// The ONE Baton boundary in this prototype. Everything that touches
// coordination state goes through the deployed v11 executable as a
// documented CLI/JSON client: no SQLite handle is ever opened here, and
// no protocol state is reconstructed by hand. See PROVENANCE.md — the
// `wait` argv shape and the readiness-is-an-edge rule are v11's.
//
// This module is TRUSTED-MANAGER-ONLY. The binary, the config path and
// the participant identity never reach a worker container.

import { execFile } from "node:child_process";
import { existsSync, realpathSync } from "node:fs";
import { dirname, resolve as resolvePath } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

class BatonError extends Error {
	constructor(message, { stderr = "", argv = [] } = {}) {
		super(message);
		this.stderr = stderr;
		this.argv = argv;
	}
}

// The production coordination state this prototype must never attach to.
//
// Round-3 review found the previous version of this guard accepted
// `/home/sl/baton-v11/baton.json` — the LIVE symlink, and the path the
// deployment is conventionally addressed by — because the pattern
// required a dot after `baton-v11`. It was also purely lexical, so any
// symlink resolving into a production home walked past it.
//
// The finding makes production coordination state a STOP CONDITION, not
// a naming convention, so the comparison is on REAL paths: the
// configured authority is resolved, each forbidden root is resolved,
// and containment decides. That catches the live alias, a `/tmp` link,
// and a prototype-root link with one rule instead of three patterns.
const PRODUCTION_ROOTS = [
	"/home/sl/baton-v11",              // the live symlink
	"/home/sl/.config/baton",
];
// Deployments are versioned as `baton-v11.<commit>`, so the family is
// matched lexically too — a home that does not exist yet cannot be
// resolved, and must still be refused.
const PRODUCTION_PATTERNS = [/^\/home\/sl\/baton-v11(\.|\/|$)/,
                             /^\/home\/sl\/\.config\/baton(\/|$)/];

// The nearest existing ancestor, so a path that has not been created yet
// is still judged by where it would really live.
function realAncestor(path) {
	let current = resolvePath(path);
	for (;;) {
		if (existsSync(current)) {
			try { return realpathSync(current); } catch { return current; }
		}
		const parent = dirname(current);
		if (parent === current) return current;
		current = parent;
	}
}

export function isProductionAuthority(config) {
	const resolved = resolvePath(config);
	if (PRODUCTION_PATTERNS.some((pattern) => pattern.test(resolved))) return true;
	const real = realAncestor(resolved);
	for (const root of PRODUCTION_ROOTS) {
		if (PRODUCTION_PATTERNS.some((pattern) => pattern.test(real))) return true;
		if (!existsSync(root)) continue;
		let realRoot;
		try { realRoot = realpathSync(root); } catch { continue; }
		if (real === realRoot || real.startsWith(`${realRoot}/`)) return true;
	}
	return false;
}

export class BatonClient {
	constructor({ binary, config, participant }) {
		if (!binary || !config || !participant) {
			throw new BatonError("BatonClient needs binary, config and participant");
		}
		if (isProductionAuthority(config)) {
			throw new BatonError(
				`${config} resolves into a production coordination home; this `
				+ `prototype refuses to attach to it — pass a disposable authority`);
		}
		this.binary = binary;
		this.config = config;
		this.participant = participant;
	}

	async run(verb, operands = [], { participant, timeoutMs = 120000 } = {}) {
		const argv = ["--config", this.config,
		              "--participant", participant ?? this.participant,
		              verb, ...operands];
		let stdout;
		try {
			({ stdout } = await execFileAsync(this.binary, argv, {
				encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
				timeout: timeoutMs,
			}));
		} catch (error) {
			// A refusal is a RESULT, not a crash: v11 prints its reason as
			// JSON on the error path and the manager must be able to read
			// it (that is the whole negative-proof surface).
			// v11 prints its refusal as a JSON document; which stream it
			// lands on is not something to guess at, so both are read.
			for (const stream of [error.stderr, error.stdout]) {
				const text = `${stream ?? ""}`.trim();
				if (!text.startsWith("{")) continue;
				let payload;
				try { payload = JSON.parse(text); } catch { continue; }
				if (payload.error) {
					throw new BatonError(payload.error, { argv, stderr: `${error.stderr ?? ""}` });
				}
			}
			throw new BatonError(
				`baton ${verb} failed: ${error.message}`,
				{ argv, stderr: `${error.stderr ?? ""}` });
		}
		let payload;
		try {
			payload = JSON.parse(stdout);
		} catch (error) {
			throw new BatonError(`baton ${verb} did not print JSON: ${error.message}`, { argv });
		}
		if (payload.error) throw new BatonError(payload.error, { argv });
		return payload;
	}

	// Read-only participant-relative readiness. Claims nothing.
	async wait(timeoutSeconds) {
		const payload = await this.run("wait", [`timeout=${timeoutSeconds}`],
			{ timeoutMs: (timeoutSeconds + 30) * 1000 });
		return validateReadiness(payload, this.participant);
	}

	async detail(work) { return this.run("detail", [`work=${work}`]); }

	// Read-only. Used to settle an ambiguous recap: the authority knows
	// whether the message is there, and this manager's memory of sending
	// it does not.
	async thread(thread) { return this.run("thread", [`thread=${thread}`]); }

	// v11's W49 rule, reused: an actionable line is an edge to
	// re-evaluate, never authority. This narrows the window before an
	// expensive agent turn; the atomic claim is still the arbiter.
	async episodeStillLive(actionKey) {
		const envelope = await this.wait(0);
		return envelope.result.actionable.some((live) => live.action_key === actionKey);
	}

	async claim(work, opId) {
		const operands = [`work=${work}`];
		if (opId) operands.push(`op-id=${opId}`);
		return this.run("claim", operands);
	}

	// W76 round 4: the recap `say` is a manager mutation too. A committed
	// message whose result was lost would otherwise be re-sent by a later
	// attempt, duplicating the recap a human reads.
	async say(thread, body, extra = [], opId) {
		const operands = [`thread=${thread}`, `body=${body}`, ...extra];
		if (opId) operands.push(`op-id=${opId}`);
		return this.run("say", operands);
	}

	// W76 round 3: `pass` carries an operation id like every other
	// manager mutation, so a lost result can replay instead of becoming
	// an unanswerable question about whether the Job reached review.
	async pass(work, to, comment, opId) {
		const operands = [`work=${work}`, `to=${to}`, `comment=${comment}`];
		if (opId) operands.push(`op-id=${opId}`);
		return this.run("pass", operands);
	}

	// Recovery, compare-and-swapped against the recorded claimant AND the
	// exact assignment episode that claim was offered under. The manager
	// uses this only to undo a claim it committed itself.
	//
	// v11 W4303 made `episode=` mandatory on every release. The claimant
	// string alone is not a fence here either: this manager releases and
	// re-offers the same Job under the same participant, so a compensation
	// whose result was lost and is retried later would otherwise abort a
	// SUCCESSOR attempt that is legitimately running. The episode is the
	// one the readiness action carried, because a claim does not mint a
	// new one.
	async release(work, expect, episode, reason, opId) {
		if (!Number.isSafeInteger(episode)) {
			throw new BatonError(
				`release needs the assignment episode it is ending; `
				+ `${JSON.stringify(episode)} is not one`);
		}
		const operands = [`work=${work}`, `expect=${expect}`,
		                  `episode=${episode}`, `reason=${reason}`];
		if (opId) operands.push(`op-id=${opId}`);
		return this.run("release", operands);
	}

	async bind(work, root, path, expect, rationale) {
		return this.run("bind", [`work=${work}`, `root=${root}`, `path=${path}`,
		                         `expect=${expect}`, `rationale=${rationale}`]);
	}

	async create(operands) { return this.run("create", operands); }
}

// The projection-12.3 readiness envelope, revalidated locally rather
// than imported from the live v11 checkout (see PROVENANCE.md). Same
// field names, same fail-closed intent.
export function validateReadiness(payload, participant) {
	const fail = (message) => { throw new BatonError(`readiness envelope: ${message}`); };
	if (!payload || typeof payload !== "object") fail("not a JSON object");
	if (payload.protocol_version !== 11) {
		fail(`protocol_version ${JSON.stringify(payload.protocol_version)} is not 11`);
	}
	if (payload.participant !== participant) {
		fail(`is for ${JSON.stringify(payload.participant)}, not ${participant}`);
	}
	if (typeof payload.authority_uuid !== "string" || !payload.authority_uuid) {
		fail("has no authority_uuid");
	}
	const result = payload.result;
	if (!result || typeof result !== "object") fail("has no result object");
	if (!Array.isArray(result.actionable)) fail("result.actionable is not an array");
	for (const action of result.actionable) {
		if (typeof action.action_key !== "string" || !action.action_key) {
			fail("an actionable entry has no action_key");
		}
		if (typeof action.kind !== "string") fail("an actionable entry has no kind");
		// v11 W4303: a Work action's assignment episode is now load-bearing
		// here — the manager fences its compensating release on it — so an
		// envelope that omits it is refused rather than producing a Job the
		// manager could claim and then not be able to release exactly.
		if (action.kind === "work"
		    && !Number.isSafeInteger(action.episode_seq)) {
			fail(`work action ${action.action_key} has no episode_seq`);
		}
	}
	return payload;
}

export { BatonError };

// Appended: the binding resolver. A Job's typed input is not carried in
// a wake prompt or a message body — it lives in the repository at the
// Work's bound record path, and the manager resolves that through the
// public CLI like any other participant would.
BatonClient.prototype.resolve = function resolve(locator) {
	return this.run("resolve", [`locator=${locator}`]);
};

// v11 projects `handler` as an OBJECT ({team, member, participant}) or
// null, never a bare string. Reading it as a string silently yields
// "[object Object]" in evidence, which is how this was found: an
// assertion comparing the Handler to `poc.claude` failed against a
// snapshot that looked populated. One accessor, used everywhere.
export function handlerAddress(detail) {
	return detail?.handler?.participant ?? null;
}
