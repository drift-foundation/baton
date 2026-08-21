// Prototype configuration. Everything is explicit: no path, image,
// participant, adapter or credential location is ever inferred. v11's
// configuration module makes the same argument and it holds here for the
// same reason — an inferred path is an unreviewable one.

import { accessSync, constants, statSync } from "node:fs";

// PLACEMENT (finding-v12-in-repository-migration) has ONE authority, and
// it is not this module. `placement.mjs` decides where the prototype's
// disposable state may live and which paths its recipes may create and
// remove; every shell entry point runs the same check before its first
// mutation. Round-1 review found the first version of this check split
// between here and three scripts, each with its own idea of what was
// safe, so there is now exactly one.
import { CHECKOUT_ROOT, POC_ROOT, planPlacement } from "./placement.mjs";

function fail(message) { throw new Error(`v12-poc configuration: ${message}`); }

export { CHECKOUT_ROOT, POC_ROOT };

function requiredString(object, key, where) {
	const value = object?.[key];
	if (typeof value !== "string" || !value.trim()) {
		fail(`${where}.${key} must be a non-empty string`);
	}
	return value;
}

function requiredDir(path, what) {
	let stat;
	try { stat = statSync(path); } catch (error) { fail(`${what} ${path}: ${error.message}`); }
	if (!stat.isDirectory()) fail(`${what} ${path} is not a directory`);
	return path;
}

export function validateConfig(raw) {
	if (!raw || typeof raw !== "object") fail("the document must be a JSON object");

	const baton = raw.baton ?? fail("baton section missing");
	requiredString(baton, "binary", "baton");
	requiredString(baton, "config", "baton");
	const participant = requiredString(baton, "participant", "baton");
	if (!/^[^.\s]+\.[^.\s]+$/.test(participant)) {
		fail("baton.participant must be team.member");
	}
	try { accessSync(baton.binary, constants.X_OK); }
	catch (error) { fail(`baton.binary ${baton.binary} is not executable: ${error.message}`); }
	const waitTimeout = baton.waitTimeoutSeconds ?? 30;
	if (!Number.isSafeInteger(waitTimeout) || waitTimeout < 0) {
		fail("baton.waitTimeoutSeconds must be a non-negative integer");
	}

	requiredString(raw, "review_endpoint", "");
	requiredString(raw, "record_root", "");
	requiredString(raw, "record_path", "");
	// `record_base` is REQUIRED. It used to be optional and fall back to
	// the prototype root, which was harmless while that root was
	// external and is exactly the relocation hazard now: the fallback
	// would silently write every Job record into the Baton checkout.
	requiredString(raw, "record_base", "");
	requiredString(raw, "state_root", "");

	const runtime = raw.runtime ?? fail("runtime section missing");
	for (const key of ["image", "user", "network", "acp_adapter",
	                   "acp_entrypoint", "credential_source",
	                   "preclaim_permission_mode", "execution_permission_mode",
	                   "state_dir"]) {
		requiredString(runtime, key, "runtime");
	}
	// Consent and execution are different acts and get different
	// postures. Naming one mode for both is what let the pre-claim turn
	// quietly run with full tool access.
	if (runtime.preclaim_permission_mode !== "plan") {
		fail("runtime.preclaim_permission_mode must be 'plan': a consent turn does not "
			+ "execute tools");
	}
	if (runtime.preclaim_permission_mode === runtime.execution_permission_mode) {
		fail("runtime.preclaim_permission_mode and runtime.execution_permission_mode must "
			+ "differ; consent and execution are not the same posture");
	}
	requiredDir(runtime.acp_adapter, "runtime.acp_adapter");
	// A credential that cannot be read is a launch-time refusal, not a
	// mid-attempt surprise after a container is already running.
	try { accessSync(runtime.credential_source, constants.R_OK); }
	catch (error) {
		fail(`runtime.credential_source ${runtime.credential_source} is unreadable: ${error.message}`);
	}
	if (!/^\d+:\d+$/.test(runtime.user)) {
		fail("runtime.user must be uid:gid — the container never runs as root, "
			+ "because root disables the permission mode this proof requires");
	}
	const minRemaining = runtime.credential_min_remaining_ms ?? 900000;
	if (!Number.isSafeInteger(minRemaining) || minRemaining < 0) {
		fail("runtime.credential_min_remaining_ms must be a non-negative integer");
	}
	// Both turn deadlines are REQUIRED and explicit. An unsupervised
	// turn can hold the canonical Handler for as long as the agent
	// stays silent, so there is no default to fall back to.
	const timeouts = {};
	for (const key of ["preclaim_turn_timeout_ms", "execution_turn_timeout_ms"]) {
		const value = runtime[key];
		if (!Number.isSafeInteger(value) || value < 1) {
			fail(`runtime.${key} must be a positive integer; a turn with no `
				+ `manager deadline can hold a claim indefinitely`);
		}
		timeouts[key] = value;
	}

	// Every disposable path names the same explicit external root, and
	// every one of them is a strict descendant of it.
	const { stateRoot } = planPlacement(raw);

	const token = raw.token ?? {};
	const ttl = token.ttl_ms ?? 120000;
	if (!Number.isSafeInteger(ttl) || ttl < 1) fail("token.ttl_ms must be a positive integer");

	return {
		...raw,
		state_root: stateRoot,
		baton: { ...baton, waitTimeoutSeconds: waitTimeout },
		runtime: { ...runtime, credential_min_remaining_ms: minRemaining,
		           ...timeouts },
		token: { ...token, ttl_ms: ttl },
	};
}
