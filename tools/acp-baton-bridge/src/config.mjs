import { isAbsolute } from "node:path";
// acp-baton-bridge configuration (W163, finding-v11-acp-agent-bridge):
// EVERYTHING is explicit deployment configuration — agent command,
// arguments, environment, cwd, participant, session policy, permission
// mode, and required policy resources. No filesystem path, executable,
// or model identity is ever inferred, and agent-specific settings are
// opaque here: this program is ACP-generic.

import { accessSync, constants, readFileSync, statSync } from "node:fs";

function fail(message) {
	throw new Error(`acp-baton-bridge configuration: ${message}`);
}

// The largest interval a Node timer holds: `setTimeout` stores its delay as a
// signed 32-bit number of milliseconds, and anything above this is replaced
// by 1ms with a warning. Exported so the bound is a checkable fact rather
// than a number repeated in prose.
export const MAX_TURN_TIMEOUT_MS = 2147483647;

function requiredString(object, key, where) {
	const value = object?.[key];
	if (typeof value !== "string" || !value.trim()) {
		fail(`${where}.${key} must be a non-empty string`);
	}
	return value;
}

export function validateConfig(raw) {
	if (!raw || typeof raw !== "object") fail("the document must be a JSON object");

	const baton = raw.baton ?? fail("baton section missing");
	requiredString(baton, "binary", "baton");
	requiredString(baton, "config", "baton");
	// W12229: AND BOTH PATHS ARE ABSOLUTE.
	//
	// These two are this family's half of the Baton launcher contract —
	// they become `BATON_BIN` and `BATON_CONFIG` in the agent's own
	// environment — and the confirmed boundary is that a context must not
	// infer them from a repository path, a deployment symlink, or
	// filesystem context. A relative executable is resolved by whatever
	// launch context the process happens to have and a relative config is
	// read from whatever working directory it inherits, so accepting one
	// hands the agent an inferred location labelled authoritative.
	//
	// The Codex dispatcher has always required this of its own
	// `roleInstructions` paths, and review [P1] required the Codex
	// bootstrap to refuse the same shape. This is the third door into one
	// contract; it refuses for the same reason as the other two.
	for (const key of ["binary", "config"]) {
		if (!isAbsolute(baton[key])) {
			fail(`baton.${key} must be an absolute path; a relative one is `
				+ "resolved from whatever context this process happens to "
				+ "have, which is the inference the launcher contract "
				+ "exists to remove");
		}
	}
	requiredString(baton, "participant", "baton");
	if (!/^[^.\s]+\.[^.\s]+$/.test(baton.participant)) {
		fail("baton.participant must be team.member");
	}
	// W101: the launch role is ALWAYS explicit, even for a participant
	// that holds exactly one role today — a later second role must not
	// silently change this session's persona.
	if (typeof baton.role !== "string" || !baton.role.trim()) {
		fail("baton.role is required: name the held role this session launches in");
	}
	if (!/^[^.\s]+$/.test(baton.role)) {
		fail("baton.role must be one role handle without whitespace or dots");
	}
	const waitTimeout = baton.waitTimeoutSeconds ?? 60;
	if (!Number.isSafeInteger(waitTimeout) || waitTimeout < 1) {
		fail("baton.waitTimeoutSeconds must be a positive integer");
	}

	// W14828: THE SPAWNED ENVIRONMENT IS DERIVED FROM `baton`, NOT SUPPLIED
	// BESIDE IT.
	//
	// The incident: a managed restart rendered the correct executable, config,
	// participant and role into the runtime context, `agent.env` carried none
	// of them, and the fresh model went looking — found a persistent
	// participant `load.json` still pinned to a retired deployment, and made
	// its first `claim` through an executable that refused the live authority.
	// The claim failed while the authority still showed Work claimed by that
	// participant.
	//
	// So the four values have ONE source and two carriers that cannot
	// disagree: this environment, and the prompt block beside it. An operator
	// may still spell them, because existing templates do — but only to the
	// same values, and a conflict refuses BY KEY before anything is read,
	// waited on, spawned or prompted. Silently preferring either side would
	// rebuild the split this Work exists to remove.
	function launcherEnvironment(source, supplied) {
		const derived = {
			BATON_BIN: source.binary,
			BATON_CONFIG: source.config,
			BATON_PARTICIPANT: source.participant,
			BATON_ROLE: source.role,
		};
		for (const [key, value] of Object.entries(derived)) {
			if (supplied[key] !== undefined && supplied[key] !== value) {
				fail(`agent.env.${key} is ${JSON.stringify(supplied[key])} and `
					+ `the accepted baton section says ${JSON.stringify(value)}; `
					+ `the launcher contract has one source, and a second `
					+ `spelling of it is the drift this refuses rather than `
					+ `resolves`);
			}
		}
		// DERIVED LAST, so they also override whatever the PARENT process
		// happened to export: the session spawns with `{...process.env,
		// ...config.agent.env}`, and a stale inherited `BATON_BIN` is exactly
		// the ambient carrier the confirmed boundary refuses to trust.
		return { ...supplied, ...derived };
	}

	const agent = raw.agent ?? fail("agent section missing");
	requiredString(agent, "command", "agent");
	if (agent.args !== undefined && (!Array.isArray(agent.args)
			|| agent.args.some((entry) => typeof entry !== "string"))) {
		fail("agent.args must be an array of strings");
	}
	if (agent.env !== undefined) {
		if (typeof agent.env !== "object" || agent.env === null
				|| Array.isArray(agent.env)) {
			fail("agent.env must be an object of string values");
		}
		for (const [key, value] of Object.entries(agent.env)) {
			if (typeof value !== "string") {
				fail(`agent.env.${key} must be a string`);
			}
		}
	}
	requiredString(agent, "cwd", "agent");

	const session = raw.session ?? fail("session section missing");
	if (session.mode !== "new" && session.mode !== "load") {
		fail("session.mode must be exactly 'new' or 'load'");
	}
	requiredString(session, "cwd", "session");

	// The ruled permission boundary: the EXACT operator-selected mode is
	// configuration; the client requires it after new/load and fails
	// visibly rather than falling back to prompts or another mode.
	requiredString(raw, "permissionMode", "config");

	// Deployment-owned prohibitions: the client does not parse commands
	// or own the vocabulary — it validates that every configured policy
	// resource exists and is readable, and REFUSES to start otherwise.
	// R3: the list is REQUIRED and non-empty; hard denials beneath the
	// bypass mode are not optional in this deployment shape.
	const policy = raw.policyResources;
	if (!Array.isArray(policy) || policy.length === 0) {
		fail("policyResources must name at least one deployment-owned "
			+ "prohibition resource; absence refuses startup");
	}
	if (policy.some((entry) =>
			typeof entry !== "string" || !entry.trim())) {
		fail("every policyResources entry must be a non-empty path");
	}
	for (const resource of policy) {
		try {
			accessSync(resource, constants.R_OK);
			statSync(resource);
		} catch {
			fail(`required policy resource ${resource} is missing or unreadable; refusing to start`);
		}
	}

	requiredString(raw, "stateDir", "config");
	const retryMs = raw.retryMs ?? 1000;
	if (!Number.isSafeInteger(retryMs) || retryMs < 1) {
		fail("retryMs must be a positive integer");
	}
	// R4: the supervision deadline for setup-phase protocol calls
	// (initialize, session new/load, set_mode).
	const setupTimeoutMs = raw.setupTimeoutMs ?? 10000;
	if (!Number.isSafeInteger(setupTimeoutMs) || setupTimeoutMs < 1) {
		fail("setupTimeoutMs must be a positive integer");
	}
	// W28681: THE TURN DEADLINE, MANDATORY AND WITHOUT A DEFAULT.
	//
	// The incident: a managed turn published `working` for the better part of
	// an hour while five tool process groups it had left behind survived for
	// 34-36 hours, one of them burning a full core. The turn itself had no
	// deadline at all — `promptText` raced only the agent's death — so the
	// only lane this participant has stayed occupied by a turn nothing could
	// end.
	//
	// NO DEFAULT, deliberately, and this is the one place that decision can be
	// enforced. Every other timeout here has one because a wrong guess is
	// merely slow; a wrong guess HERE either kills legitimate long work or
	// leaves the defect open, and neither is a choice a repository can make on
	// a deployment's behalf. An absent value is a configuration that has not
	// decided, and a configuration that has not decided must not start.
	//
	// AND IT IS WALL-CLOCK, not an activity reset. A legitimate tool may be
	// silent for a long time while a chatty infinite one produces updates
	// forever, so streamed ACP updates are diagnostics and never extend this.
	const turnTimeoutMs = raw.turnTimeoutMs;
	if (!Number.isSafeInteger(turnTimeoutMs) || turnTimeoutMs < 1) {
		fail("turnTimeoutMs must be a positive integer number of "
			+ "milliseconds and has no default: it is the wall-clock bound on "
			+ "one delivered turn, and a deployment that has not chosen one "
			+ "has not decided how long its only delivery lane may be held");
	}
	// AND IT MUST BE A DURATION THIS RUNTIME CAN ACTUALLY WAIT.
	//
	// Review [P1]: every positive safe integer was accepted, and Node's timer
	// interval is a SIGNED 32-BIT millisecond value. `2147483648` therefore
	// validated, then `setTimeout` warned about the overflow and used ONE
	// MILLISECOND — so an operator asking for the longest deadline they could
	// express silently got the shortest one there is. A deadline that becomes
	// its own opposite without refusing is worse than no deadline, because
	// the configuration says one thing and the supervisor does another.
	//
	// REFUSED RATHER THAN CLAMPED. Clamping would substitute this
	// repository's number for the operator's, which is the whole reason this
	// operand has no default; and a long-duration timer built by chaining
	// short ones would be this program inventing a scheduler to make an
	// unreasonable value work. ~24.8 days is named in the message so the
	// ceiling is a fact the operator can act on rather than a mystery.
	if (turnTimeoutMs > MAX_TURN_TIMEOUT_MS) {
		fail(`turnTimeoutMs must be at most ${MAX_TURN_TIMEOUT_MS} `
			+ "milliseconds (about 24.8 days), which is the longest interval "
			+ "this runtime's timers can hold; a larger value is silently "
			+ "truncated to one millisecond, turning the longest deadline an "
			+ "operator can ask for into the shortest one there is");
	}

	// W93 R9: the runtime IDENTITY metadata. Teams cannot tell a Claude
	// runner from a Gemini one when every ACP lease publishes adapter
	// `acp` and nothing else — and neither may be inferred from a
	// participant name or an executable path, which is exactly how a
	// roster starts lying. It is optional, validated, and carried
	// through verbatim.
	//
	// `actionOwner` is the participant who owes this runner's
	// interactive answers. The authority already accepts it; without it
	// here, a `waiting-input` state can never become the ruled
	// actionable Inbox entry. No owner is ever guessed.
	let runtime = { provider: undefined, model: undefined,
		actionOwner: undefined };
	if (raw.runtime !== undefined) {
		const source = raw.runtime;
		if (typeof source !== "object" || source === null
				|| Array.isArray(source)) {
			fail("runtime must be an object");
		}
		for (const key of Object.keys(source)) {
			if (!["provider", "model", "actionOwner"].includes(key)) {
				fail(`runtime.${key} is not a runtime metadata field`);
			}
		}
		for (const key of ["provider", "model", "actionOwner"]) {
			if (source[key] === undefined) continue;
			if (typeof source[key] !== "string" || !source[key].trim()) {
				fail(`runtime.${key} must be a non-empty string`);
			}
			runtime[key] = source[key];
		}
		if (runtime.actionOwner !== undefined
				&& !/^[^.\s]+\.[^.\s]+$/.test(runtime.actionOwner)) {
			fail("runtime.actionOwner must be team.member");
		}
	}

	return {
		runtime,
		baton: {
			binary: baton.binary,
			config: baton.config,
			participant: baton.participant,
			role: baton.role,
			waitTimeoutSeconds: waitTimeout,
		},
		agent: {
			command: agent.command,
			args: agent.args ?? [],
			env: launcherEnvironment(baton, agent.env ?? {}),
			cwd: agent.cwd,
		},
		session: { mode: session.mode, cwd: session.cwd },
		permissionMode: raw.permissionMode,
		policyResources: policy,
		stateDir: raw.stateDir,
		retryMs,
		setupTimeoutMs,
		turnTimeoutMs,
	};
}

export function loadConfig(path) {
	let text;
	try {
		text = readFileSync(path, "utf8");
	} catch (error) {
		fail(`cannot read ${path}: ${error.message}`);
	}
	let raw;
	try {
		raw = JSON.parse(text);
	} catch (error) {
		fail(`${path} is not valid JSON: ${error.message}`);
	}
	return validateConfig(raw);
}
