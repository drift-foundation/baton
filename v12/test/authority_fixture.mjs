// Shared scaffolding for the v12 assignment-authority regressions.
//
// Every suite builds a REAL authority on a real file. There is no
// in-memory double: the contract is about what survives a restart and
// what two callers see of one durable store, and a fake would answer
// both questions by construction.

import { join } from "node:path";

import { V12Authority, V11, V12 } from "../src/authority/index.mjs";
import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";

// W2907: this fixture had its own private root list, which was the right
// SHAPE and a second copy of it. One registry for the whole suite means
// one place where "which paths may this suite remove" is answered.
export const scratch = () => ownedTemp("v12-authority-");
export const cleanup = removeOwnedRoots;

export const UUID = "authority-uuid";
export const WORK = "full-W1";
export const OTHER = "full-W2";
export const CLAUDE = "poc.claude";
export const GEMINI = "poc.gemini";

// The four workflow actors and the closer, each holding ONE configured
// capability. Separate identities by default because §10.12 makes the
// receipts separately attributable: a deployment may grant one participant
// several, and the cases that care about that grant them explicitly.
export const VERIFIER = "poc.verifier";
export const REVIEWER = "poc.reviewer";
export const APPROVER = "poc.approver";
export const INTEGRATOR = "poc.integrator";
export const CLOSER = "poc.closer";
export const GRANTS = [
	[VERIFIER, "verify"], [REVIEWER, "review"], [APPROVER, "approve"],
	[INTEGRATOR, "integrate"], [CLOSER, "close"],
];

// The digest tuple §10.11 requires a proposal receipt to bind. Written out
// once so a case that does not care about the digests still supplies real
// ones rather than a placeholder that would hide a missing binding.
export function candidate(name = "cand-1") {
	return {
		resultId: `result:${name}`,
		resultDigest: `sha256:result-${name}`,
		candidateDigest: name,
		inputDigest: `sha256:input-${name}`,
		policyDigest: `sha256:policy-${name}`,
	};
}

// One deployment, opened on a path the caller keeps so it can be reopened
// as a RESTART rather than as a second authority.
export function deployment({
	dir = scratch(),
	contract = V11,
	certified = [V11, V12],
	works = [[WORK, "impl"]],
	handlers = [["impl", CLAUDE], ["impl", GEMINI], ["rview", GEMINI]],
	grants = GRANTS,
} = {}) {
	const path = join(dir, "authority.sqlite3");
	const authority = V12Authority.create(path, { authorityUuid: UUID });
	for (const name of certified) authority.certifyContract(name);
	authority.permitContractTransition(V11, V12);
	for (const [route, participant] of handlers) {
		authority.addRouteHandler(route, participant);
	}
	for (const [participant, capability] of grants) {
		authority.grantCapability(participant, capability);
	}
	for (const [workId, route] of works) {
		authority.createWork({ workId, route, contract });
	}
	return { authority, as: sessionsOf(authority), path, dir };
}

// Sessions, cached per participant.
//
// Re-review 2026-08-22 [P1]: the transitions moved off the trusted
// authority onto a per-participant session, so a test that wants to act AS
// somebody says so — which is also how the production consumer says it.
export function sessionsOf(authority) {
	const cache = new Map();
	return (participant) => {
		if (!cache.has(participant)) cache.set(participant, authority.session(participant));
		return cache.get(participant);
	};
}

// Reopen the same durable authority. This is what a manager restart looks
// like from the store's side: a new process, the same file, no memory.
export function restart(authority, path) {
	authority.dispose();
	const reopened = V12Authority.open(path, { authorityUuid: UUID });
	reopened.as = sessionsOf(reopened);
	return reopened;
}

// A v12 Work with its first assignment already minted, which most
// scenarios need before they can say anything interesting.
export function claimedV12({ participant = CLAUDE, workId = WORK, ...options } = {}) {
	const built = deployment({ contract: V12, ...options });
	const assignment = built.as(participant).claim({
		workId, operationId: `claim:offer-${workId}`,
	});
	return { ...built, assignment, session: built.as(participant) };
}

export function refusalMessage(fn) {
	try {
		fn();
	} catch (error) {
		return error.message;
	}
	throw new Error("expected a refusal, and the call succeeded");
}
