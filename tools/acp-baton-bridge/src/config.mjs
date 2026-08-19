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
	// (initialize, session new/load, set_mode). Turns have no
	// arbitrary work deadline; they race agent death instead.
	const setupTimeoutMs = raw.setupTimeoutMs ?? 10000;
	if (!Number.isSafeInteger(setupTimeoutMs) || setupTimeoutMs < 1) {
		fail("setupTimeoutMs must be a positive integer");
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
			env: agent.env ?? {},
			cwd: agent.cwd,
		},
		session: { mode: session.mode, cwd: session.cwd },
		permissionMode: raw.permissionMode,
		policyResources: policy,
		stateDir: raw.stateDir,
		retryMs,
		setupTimeoutMs,
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
