// Per-attempt runtime state: the isolated filesystem the agent sees, the
// credential staging, and the two container specs.
//
// WHAT THE PRE-CLAIM POSTURE ACTUALLY IS. An earlier version of this
// file claimed the pre-claim turn was "physically read-only" and could
// not execute anything. That was false, and review caught it: the
// container had a writable credential bind, a writable tmpfs, Docker's
// writable container layer, egress, and the same bypassPermissions ACP
// posture as the worker. The absence of a result mount was doing all
// the work, and the sentence claimed far more than that.
//
// The posture is now enforced rather than asserted, and stated at the
// strength it actually holds. A pre-claim container gets:
//
//   - the `plan` ACP permission mode, in which the agent does not
//     execute tools at all, required exactly with no fallback;
//   - a read-only root filesystem, all capabilities dropped, and no
//     new privileges;
//   - no typed input mount and no declared output mount;
//   - no Baton executable, configuration or database.
//
// Two residuals remain and are NOT claimed away. The credential bind is
// writable because the Claude SDK requires a writable config directory,
// and network egress to the model provider exists because a model turn
// needs it. So the honest property is: a pre-claim turn holds no Baton
// capability, touches no Job input or output, and cannot produce an
// accepted result or an assignment. Only a validated token can.
//
// Neither spec mounts the Baton executable, its config or its database.
// A model in either container has no coordination capability at all.

import { chmodSync, copyFileSync, existsSync, lstatSync, mkdirSync,
         readdirSync, readFileSync, realpathSync, rmSync, writeFileSync }
	from "node:fs";
import { join } from "node:path";

class RuntimeError extends Error {}

export function attemptPaths(stateDir, runtimeAttempt) {
	const root = join(stateDir, runtimeAttempt);
	return {
		root,
		credentials: join(root, "claude-config"),
		offer: join(root, "offer"),
		input: join(root, "in"),
		output: join(root, "out"),
		frozen: join(root, "frozen"),
		trace: join(root, "trace.jsonl"),
	};
}

// The refresh hazard, made explicit. The prototype hands the worker a
// COPY of the operator's OAuth credential, so a refresh inside the
// container would mint a replacement refresh token and silently
// invalidate the operator's own. The copy is therefore only staged when
// the access token still has comfortably more life than an attempt
// needs, so the container never has a reason to refresh. This is a
// prototype STOPGAP, not a design: v12 must issue a scoped, short-lived,
// worker-specific credential instead. See PROGRESS.md.
export function stageCredentials(paths, { source, minRemainingMs, now = () => Date.now() }) {
	mkdirSync(paths.credentials, { recursive: true });
	chmodSync(paths.credentials, 0o700);
	let parsed;
	try {
		parsed = JSON.parse(readFileSync(source, "utf8"));
	} catch (error) {
		throw new RuntimeError(`credential source ${source} is unreadable: ${error.message}`);
	}
	const oauth = parsed?.claudeAiOauth;
	if (!oauth || typeof oauth.expiresAt !== "number") {
		throw new RuntimeError(
			`credential source ${source} has no claudeAiOauth.expiresAt; this `
			+ `prototype refuses to stage a credential whose lifetime it cannot check`);
	}
	const remaining = oauth.expiresAt - now();
	if (remaining < minRemainingMs) {
		throw new RuntimeError(
			`the staged access token has ${Math.round(remaining / 1000)}s left, below the `
			+ `required ${Math.round(minRemainingMs / 1000)}s; refusing to launch a worker `
			+ `that would refresh and rotate the operator's own refresh token`);
	}
	copyFileSync(source, join(paths.credentials, ".credentials.json"));
	chmodSync(join(paths.credentials, ".credentials.json"), 0o600);
	// Suppress the adapter's first-run interactive prompts without
	// carrying any operator project history into the container.
	writeFileSync(join(paths.credentials, ".claude.json"),
		`${JSON.stringify({ hasCompletedOnboarding: true, projects: {} }, null, 2)}\n`);
	return { remaining_ms: remaining, expires_at: new Date(oauth.expiresAt).toISOString() };
}

const ADAPTER_TARGET = "/opt/acp";
const CONFIG_TARGET = "/run/claude-config";

function baseSpec(runtime, paths, name, workdir) {
	return {
		name, workdir,
		user: runtime.user,
		network: runtime.network,
		image: runtime.image,
		limits: [["--pids-limit", "512"], ["--memory", runtime.memory ?? "2g"]],
		env: {
			CLAUDE_CONFIG_DIR: CONFIG_TARGET,
			HOME: CONFIG_TARGET,
			// The adapter is told, in band, that it is a Baton v12
			// prototype worker. Nothing here is a capability.
			BATON_V12_POC: "0-spike",
		},
		command: ["node", join(ADAPTER_TARGET, runtime.acp_entrypoint)],
	};
}

export function preClaimSpec(runtime, paths, runtimeAttempt) {
	return {
		...baseSpec(runtime, paths, `v12poc-preclaim-${runtimeAttempt}`, "/offer"),
		readOnlyRootfs: true,
		mounts: [
			{ source: runtime.acp_adapter, target: ADAPTER_TARGET, mode: "ro" },
			{ source: paths.credentials, target: CONFIG_TARGET, mode: "rw" },
			{ source: paths.offer, target: "/offer", mode: "ro" },
		],
		tmpfs: ["/tmp:rw,size=64m"],
	};
}

export function executionSpec(runtime, paths, runtimeAttempt) {
	return {
		...baseSpec(runtime, paths, `v12poc-worker-${runtimeAttempt}`, "/out"),
		mounts: [
			{ source: runtime.acp_adapter, target: ADAPTER_TARGET, mode: "ro" },
			{ source: paths.credentials, target: CONFIG_TARGET, mode: "rw" },
			// The typed input is read-only at a stable path, and it is
			// digest-verified before and after the turn.
			{ source: paths.input, target: "/in", mode: "ro" },
			// The one writable destination, and the only place a result
			// may appear.
			{ source: paths.output, target: "/out", mode: "rw" },
		],
		tmpfs: ["/tmp:rw,size=64m"],
	};
}

// A spec is only as good as the claim that it grants nothing else. This
// is asserted rather than trusted, and it runs before every launch.
//
// Comparison is on CANONICAL paths, not on spellings. Docker resolves a
// bind source before mounting it, so a source that is merely a symlink
// to a forbidden directory passes any string comparison and then exposes
// that directory in the container — reproduced by review round 2
// against this exact function. A trusted configuration can still hold
// an accidental or later-retargeted link, and this function claims to
// enforce capability ABSENCE rather than to document today's spelling.
//
// Ambiguity is refused rather than resolved: a mount source that cannot
// be canonicalized is a mount whose real target nobody knows.
function canonical(path, what, spec) {
	try {
		return realpathSync(path);
	} catch (error) {
		throw new RuntimeError(
			`container ${spec.name} names ${what} ${path}, which cannot be resolved `
			+ `(${error.code ?? error.message}); a mount whose real target is unknown `
			+ `is refused rather than assumed safe`);
	}
}

// Returns a spec whose mount sources are the CANONICAL paths that were
// validated, not the aliases that were supplied.
//
// Round-3 review: resolving for comparison and then launching the alias
// leaves a real gap — the link can be retargeted between the check and
// `docker run`, and the comment here used to claim that case was
// covered when canonical comparison alone does not cover it. Docker
// resolves the source anyway, so handing it the resolved path changes
// nothing about what a correct configuration gets and removes the
// window entirely.
export function assertNoBatonCapability(spec, forbidden) {
	// A forbidden root that does not exist on this host cannot be
	// canonicalized, and that is not ambiguity — there is nothing there
	// to expose. Its literal spelling is still compared, so a path that
	// appears later is not silently dropped from the fence.
	const roots = forbidden.map((path) => {
		try { return { canonical: realpathSync(path), literal: path }; }
		catch { return { canonical: null, literal: path }; }
	});
	const canonicalMounts = [];
	for (const mount of spec.mounts) {
		const source = canonical(mount.source, `mount source`, spec);
		canonicalMounts.push({ ...mount, source, alias: mount.source });
		for (const root of roots) {
			for (const path of [root.canonical, root.literal]) {
				if (!path) continue;
				if (source === path || source.startsWith(`${path}/`)
						|| path.startsWith(`${source}/`)) {
					throw new RuntimeError(
						`container ${spec.name} would mount ${mount.source}`
						+ (source === mount.source ? "" : ` (really ${source})`)
						+ `, which exposes Baton state at ${root.literal}; refusing — `
						+ `no worker gets coordination capability`);
				}
			}
		}
	}
	return { ...spec, mounts: canonicalMounts };
}

// The pre-claim posture, asserted rather than described. Each clause
// corresponds to one sentence the dossier is allowed to say.
export function assertPreClaimPosture(spec, permissionMode) {
	const writable = spec.mounts.filter((mount) => mount.mode === "rw"
		&& mount.target !== CONFIG_TARGET);
	if (writable.length) {
		throw new RuntimeError(
			`the pre-claim container ${spec.name} would get writable mounts `
			+ `[${writable.map((m) => m.target).join(", ")}]; a pre-claim turn touches no `
			+ `Job input and no declared output`);
	}
	for (const forbidden of ["/in", "/out"]) {
		if (spec.mounts.some((mount) => mount.target === forbidden)) {
			throw new RuntimeError(
				`the pre-claim container ${spec.name} would mount ${forbidden}; consent is `
				+ `decided from the offer, never from the Job's data`);
		}
	}
	if (spec.readOnlyRootfs !== true) {
		throw new RuntimeError(
			`the pre-claim container ${spec.name} would get a writable root filesystem`);
	}
	if (permissionMode !== "plan") {
		throw new RuntimeError(
			`the pre-claim container ${spec.name} would run in permission mode `
			+ `'${permissionMode}'; consent is a non-executing turn, so only 'plan' is `
			+ `accepted here`);
	}
	return spec;
}

// Round-3 review: staging a copy of the operator's credential is only
// half a lifecycle, and the half that was missing is the one that
// matters. Every attempt was leaving a mode-0600 copy of the complete
// `.credentials.json` — refresh token included — under
// `run/attempts/<attempt>/claude-config/`, on the successful path as
// well as every failure path. Calling it a runtime copy does not make it
// ephemeral.
//
// So it is disposed explicitly, and ONLY once every container that
// mounts it is positively absent: removing it under a live container
// would be tidying up around a process still holding it open. If
// absence cannot be proven the secret stays and the caller reports it as
// part of the stranded condition — an undisposed credential that is
// named is recoverable, one that is quietly assumed gone is not.
//
// The bytes are overwritten before the unlink. On a copy-on-write
// filesystem that is not a guarantee of unrecoverability, and it is not
// claimed as one; it removes the plain copy from the obvious place.
export function disposeCredentials(paths) {
	const directory = paths.credentials;
	if (!existsSync(directory)) return { disposed: false, reason: "absent" };
	const removed = [];
	for (const name of readdirSync(directory)) {
		const file = join(directory, name);
		let stat;
		try { stat = lstatSync(file); } catch { continue; }
		if (stat.isFile() && stat.size > 0) {
			try { writeFileSync(file, Buffer.alloc(stat.size, 0)); }
			catch { /* the unlink below is still attempted */ }
		}
		removed.push(name);
	}
	rmSync(directory, { recursive: true, force: true });
	return { disposed: !existsSync(directory), entries: removed.length };
}

export { RuntimeError, ADAPTER_TARGET, CONFIG_TARGET };
