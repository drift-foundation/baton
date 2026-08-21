// Isolated worker containers. Every mount, every environment variable
// and the network posture are named explicitly here, because "what did
// the worker actually have access to" is one of the questions this
// proof exists to answer, and an implicit default is not an answer.
//
// Containers are deliberately NOT run with `--rm`: the exit code, the
// image identity and the start/finish instants are termination evidence
// the trace has to carry, and `--rm` destroys them at exactly the
// moment they become interesting. Removal is an explicit later step.

import { execFile, spawn } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

class ContainerError extends Error {}

// `mounts` entries are {source, target, mode: "ro"|"rw"} — no shorthand,
// so a writable mount can never be a typo away from a read-only one.
export function runArgv(spec) {
	const argv = ["run", "--interactive", "--name", spec.name,
	              "--user", spec.user,
	              "--network", spec.network,
	              "--workdir", spec.workdir,
	              // Capabilities and privilege escalation are dropped on
	              // every container this prototype starts. Neither turn
	              // has any use for them, and "the worker had no reason
	              // to need it" is not the same as "the worker could not
	              // have it".
	              "--cap-drop", "ALL", "--security-opt", "no-new-privileges"];
	if (spec.readOnlyRootfs) argv.push("--read-only");
	for (const limit of spec.limits ?? []) argv.push(...limit);
	for (const mount of spec.mounts) {
		if (mount.mode !== "ro" && mount.mode !== "rw") {
			throw new ContainerError(
				`mount ${mount.target} must declare mode 'ro' or 'rw', got ${JSON.stringify(mount.mode)}`);
		}
		argv.push("--mount",
			`type=bind,source=${mount.source},target=${mount.target}`
			+ (mount.mode === "ro" ? ",readonly" : ""));
	}
	for (const tmpfs of spec.tmpfs ?? []) argv.push("--tmpfs", tmpfs);
	for (const [key, value] of Object.entries(spec.env ?? {})) {
		argv.push("--env", `${key}=${value}`);
	}
	argv.push(spec.image, ...spec.command);
	return argv;
}

export function spawnContainer(spec) {
	const argv = runArgv(spec);
	const child = spawn("docker", argv, { stdio: ["pipe", "pipe", "pipe"] });
	const stderr = [];
	child.stderr.on("data", (chunk) => {
		stderr.push(chunk.toString("utf8"));
		if (stderr.length > 400) stderr.splice(0, stderr.length - 400);
	});
	return { child, argv, stderrChunks: stderr };
}

export async function inspect(name) {
	const { stdout } = await execFileAsync("docker",
		["inspect", name], { encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
	const [record] = JSON.parse(stdout);
	if (!record) throw new ContainerError(`docker inspect ${name} returned nothing`);
	return {
		id: record.Id,
		image: record.Image,
		image_ref: record.Config?.Image ?? null,
		running: record.State?.Running ?? null,
		exit_code: record.State?.ExitCode ?? null,
		oom_killed: record.State?.OOMKilled ?? null,
		started_at: record.State?.StartedAt ?? null,
		finished_at: record.State?.FinishedAt ?? null,
		mounts: (record.Mounts ?? []).map((mount) => ({
			source: mount.Source, target: mount.Destination, rw: mount.RW,
		})),
		network_mode: record.HostConfig?.NetworkMode ?? null,
		user: record.Config?.User ?? null,
		// The hardening posture, read back from the runtime rather than
		// taken from the spec we asked for. A container is removed at the
		// end of an attempt, so if this is not captured while it exists
		// the evidence cannot answer the question later.
		readonly_rootfs: record.HostConfig?.ReadonlyRootfs ?? null,
		cap_drop: record.HostConfig?.CapDrop ?? null,
		security_opt: record.HostConfig?.SecurityOpt ?? null,
		tmpfs: record.HostConfig?.Tmpfs ?? null,
	};
}

// Quiescence is a CHECKED fact, not an assumption that closing stdin was
// enough. A container that will not stop on its own is stopped, and the
// trace says which of the two happened.
export async function awaitQuiescence(name, { timeoutMs = 30000, pollMs = 250 } = {}) {
	const deadline = Date.now() + timeoutMs;
	for (;;) {
		const state = await inspect(name);
		if (!state.running) return { ...state, stopped_by: "self" };
		if (Date.now() >= deadline) {
			await execFileAsync("docker", ["stop", "--timeout", "5", name]);
			return { ...(await inspect(name)), stopped_by: "manager" };
		}
		await new Promise((resolve) => setTimeout(resolve, pollMs));
	}
}

// Recording a failed fence is not the same as establishing one. Every
// boundary this prototype claims to cross only after a container stopped
// is guarded by THIS function, and it refuses everything that is not an
// unambiguous clean self-termination:
//
//   - an inspection error means quiescence is unknown, not acceptable;
//   - `running` true means the container is still there;
//   - a manager-forced stop cannot be distinguished from a kill in the
//     middle of a write, so it is refused rather than interpreted;
//   - a non-zero exit means the agent process did not finish normally.
//
// The caller treats a refusal as terminal for the attempt.
export function assertQuiesced(state, what) {
	if (!state || state.error) {
		throw new ContainerError(
			`${what} could not be proven quiescent (${state?.error ?? "no inspection"}); `
			+ `refusing to cross a boundary that assumes it stopped`);
	}
	if (state.running !== false) {
		throw new ContainerError(`${what} is still running; refusing to proceed`);
	}
	if (state.stopped_by !== "self") {
		throw new ContainerError(
			`${what} had to be stopped by the manager (exit ${state.exit_code}); a forced `
			+ `stop is indistinguishable from a kill mid-write, so the attempt is refused`);
	}
	if (state.exit_code !== 0) {
		throw new ContainerError(
			`${what} exited ${state.exit_code}${state.oom_killed ? " (OOM-killed)" : ""}; `
			+ `refusing to accept work from a container that did not finish normally`);
	}
	return state;
}

export async function remove(name) {
	try {
		await execFileAsync("docker", ["rm", "--force", name]);
	} catch { /* already gone is the desired end state */ }
}

// Removal, then PROOF of removal.
//
// `remove()` swallows every error, which is right for tidying up after
// a success and wrong for deciding anything. Before the manager tells
// Baton a Job is available again it has to establish that the previous
// execution container is GONE — not that a removal command was issued.
// A docker daemon that cannot answer is not evidence of absence, so an
// unanswerable inspection reports `gone: false` and the caller fails
// closed rather than advertising Work whose old worker may still run.
export async function removeAndVerify(name) {
	let removal = null;
	try {
		await execFileAsync("docker", ["rm", "--force", name]);
	} catch (error) {
		removal = error.stderr?.toString().trim() || error.message;
	}
	try {
		const state = await inspect(name);
		return { name, gone: false, removal,
		         reason: `docker still resolves ${name} `
		                 + `(running=${state.running})` };
	} catch (error) {
		const text = `${error.stderr ?? ""}${error.message ?? ""}`;
		// Only "there is no such container" proves absence. Anything
		// else — a daemon that is down, a permission error, a timeout —
		// is an unanswered question.
		if (/no such object|no such container/i.test(text)) {
			return { name, gone: true, removal };
		}
		return { name, gone: false, removal,
		         reason: `could not establish that ${name} is gone: `
		                 + `${text.trim().slice(0, 200)}` };
	}
}

export { ContainerError };
