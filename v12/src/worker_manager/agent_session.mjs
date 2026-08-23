// W2929 plan item 4, second slice: OPENING AN AGENT SESSION.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance:
//
//   "It opens separate consent and execution sessions, each with a fresh
//    per-posture epoch; it never resumes, forks, promotes or re-prompts after
//    transport loss. Consent has no assignment/workspace/output, execution has
//    the exact assignment and pinned workspace role, and neither receives
//    Baton capability."
//
// THE THREE RULES, and where each is decided:
//
//   1. a FRESH epoch per posture, every time — decided by the store, as the
//      next epoch for this (attempt, posture) and never a reused one;
//   2. the posture BINDINGS — consent has no assignment and no workspace and
//      no declared output; execution has the exact fixed assignment, and its
//      Work must be the session's Work, which the frozen schema's own
//      description says JSON Schema cannot express;
//   3. NO BATON CAPABILITY REACHES THE PROVIDER. Review [P1]: I kept this by
//      giving the boundary no session at all — and that CONFLATED TWO ROLES.
//      The trusted Worker Manager IS the one Baton authority client and must
//      reproject the assignment immediately before an execution session
//      exists; the untrusted agent endpoint and relay are what must never
//      receive a capability. Removing the manager's handle did not prove
//      provider isolation, it removed the liveness check the contract
//      requires. The handle is here, used for exactly one read, and kept out
//      of every returned value and every durable row.
//
// WHAT IS NOT HERE: turns and their deadlines, event normalization, and the
// adapter CONTRACTS. This slice answers what a session IS when it is opened.

import { ContractError, digest } from "./contracts.mjs";
import { certifiedAgentSessionProfile } from "./agent_profile.mjs";

export const POSTURES = Object.freeze(["consent", "execution"]);

function attemptOf(store, attemptId) {
	const row = store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id = ?").get(attemptId);
	if (row === undefined) {
		throw new ContractError("refused", "precondition",
			`no runtime attempt ${attemptId}`);
	}
	return row;
}

/** The next epoch for this attempt and posture.
 *
 *  ALWAYS THE NEXT ONE. The manager never resumes, forks or promotes a
 *  session, so there is no path that reuses an epoch — and the derivation
 *  says so rather than a comment saying so. Consent and execution count
 *  separately, because they never share a connection either. */
export function nextEpoch(store, attemptId, posture) {
	return store.db.prepare(
		"SELECT COALESCE(MAX(session_epoch), 0) + 1 AS next FROM "
		+ "agent_sessions WHERE runtime_attempt_id = ? AND posture = ?")
		.get(attemptId, posture).next;
}

/** Open one agent session in one posture, under one certified profile.
 *
 *  The `session` is the manager's own participant-bound authority handle. It
 *  is read — once, to reproject the assignment an execution session claims to
 *  belong to — and it appears in nothing this function returns or writes. */
export function openAgentSession(store, session,
                                 { attemptId, posture, profileDigest }) {
	if (!POSTURES.includes(posture)) {
		throw new ContractError("integrity", "schema",
			`${posture} is not a posture; a session is consent or execution, `
			+ `and they never share an epoch or a connection`);
	}
	const attempt = attemptOf(store, attemptId);
	// THE PROFILE MUST BE CERTIFIED, and read as the document it is. A
	// session pins a per-posture policy, and a digest cannot be read for one.
	const profile = certifiedAgentSessionProfile(store, profileDigest);
	if (profile === null) {
		throw new ContractError("policy", "profile-uncertified",
			`nothing certifies agent-session profile ${profileDigest} for `
			+ `this manager; a session pins a policy, and one nothing has `
			+ `agreed to is not a policy`);
	}
	const binding = profile.postures[posture];
	// THE POSTURE BINDINGS. The schema pins consent's `workspace` and
	// `declared_output` to false and execution's to true, so a certified
	// profile already carries the right pair — this reads them rather than
	// restating them, because a rule restated in two places is a rule that
	// can disagree with itself.
	if (attempt.work_id === null || attempt.authority_uuid === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} names no Work; a session is evidence about `
			+ `one and cannot be opened without it`);
	}
	let assignment = null;
	if (posture === "execution") {
		// THE EXACT ASSIGNMENT, and the cross-field rule the frozen schema's
		// own description says JSON Schema cannot express: this assignment's
		// Work is the session's Work.
		if (attempt.assignment_generation === null) {
			throw new ContractError("refused", "precondition",
				`attempt ${attemptId} is not activated; an execution session `
				+ `has the exact assignment, and there is none`);
		}
		if (typeof session?.assignmentOf !== "function") {
			throw new ContractError("refused", "precondition",
				`an execution session is opened against the LIVE assignment; `
				+ `the manager's authority handle is what reads it`);
		}
		// THE HANDLE'S BINDING, SNAPSHOTTED ONCE.
		//
		// Review [P1]: I checked only that the handle could answer, and
		// `assignmentOf` is WORK-SCOPED — a session minted for another
		// participant returns the same live assignment, and the four-part
		// comparison then proves the projection agrees with the attempt
		// while proving nothing about who asked. That is the activation
		// slice's own lesson, which I wrote and did not carry: the claim
		// says which assignment this attempt won, the binding says who is
		// asking, and they are two different rules.
		//
		// Read ONCE, into a local. Measured honestly: a mutation that reads
		// `session.participant` inline instead is EQUIVALENT here, because
		// the value is used exactly once on the success path and what lands
		// in the row comes from the ATTEMPT, never from the handle. The
		// local is kept so the single read stays visible — the authority's
		// own sessions snapshot for this reason, and the next edit that
		// wanted this value would otherwise reach for the getter again.
		// Named `actor` rather than `binding`: the posture binding is already
		// in scope above, and a second `binding` here would shadow it inside
		// the one block where the two are easiest to confuse.
		const actor = session.participant;
		if (actor !== attempt.assignment_participant) {
			throw new ContractError("refused", "precondition",
				`this authority session acts for ${actor} and attempt `
				+ `${attemptId} is assigned to `
				+ `${attempt.assignment_participant}`);
		}
		// THE CACHED ROW IS NOT THE LIVE ASSIGNMENT. Review [P1]: this
		// consulted only the attempt's own copy, so an execution session
		// opened cleanly against an assignment the authority had already
		// fenced and ended. The manager is the authority client; it asks.
		const live = session.assignmentOf(attempt.work_id);
		const fixed = { authorityUuid: attempt.authority_uuid,
		                workId: attempt.work_id,
		                participant: attempt.assignment_participant,
		                generation: attempt.assignment_generation };
		if (live === null) {
			throw new ContractError("stale-assignment", "ended",
				`${attempt.work_id} holds no live assignment; an execution `
				+ `session belongs to one`);
		}
		if (live.authorityUuid !== fixed.authorityUuid
				|| live.workId !== fixed.workId
				|| live.participant !== fixed.participant
				|| live.generation !== fixed.generation) {
			throw new ContractError("stale-assignment", "generation",
				`the live assignment is ${JSON.stringify(live)} and this `
				+ `attempt is fixed to ${JSON.stringify(fixed)}`);
		}
		assignment = { participant: fixed.participant,
		               generation: fixed.generation };
	}
	const epoch = nextEpoch(store, attemptId, posture);
	const pinned = digest(binding.policy);
	// ONE OPEN SESSION PER POSTURE, decided by the DATABASE. Review [P1]:
	// freshness and concurrency are two rules, and allocating the next epoch
	// answered only the first. A read of MAX followed by a separate insert is
	// not an atomic allocator across two manager connections, so the partial
	// unique index is what refuses — and its refusal is translated to the
	// frozen pair rather than surfacing as a raw constraint.
	try {
		insertSession(store, { attemptId, posture, epoch, profileDigest,
		                       pinned, attempt, assignment });
	} catch (failure) {
		if (isUniqueViolation(failure)) {
			throw new ContractError("runtime-observation", "duplicate-runtime",
				`attempt ${attemptId} already has an open ${posture} session; `
				+ `a posture holds one, and a later epoch begins after this `
				+ `one closes`);
		}
		throw failure;
	}
	return openedAnswer({ attemptId, posture, epoch, profileDigest, pinned,
	                      attempt, assignment, binding });
}

function insertSession(store, { attemptId, posture, epoch, profileDigest,
                                pinned, attempt, assignment }) {
	store.db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, participant, generation, provider_session_id, "
		+ "state, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, "
		+ "'not-started', ?)")
		.run(attemptId, posture, epoch, profileDigest, pinned,
		     attempt.work_id, attempt.authority_uuid,
		     assignment?.participant ?? null, assignment?.generation ?? null,
		     store.clock());
}

// A UNIQUE violation, and nothing else. The same narrowing the observation
// boundary already carries: a wrong diagnosis is worse than a raw error.
function isUniqueViolation(failure) {
	const errcode = failure?.errcode;
	return typeof errcode === "number" && (errcode & 0xff) === 19
		&& /UNIQUE/i.test(String(failure?.message ?? ""));
}

function openedAnswer({ attemptId, posture, epoch, profileDigest, pinned,
                        attempt, assignment, binding }) {
	return {
		// The REFERENCE, which labels evidence and authorizes nothing. Nothing
		// here is the manager's authority handle, which is the half of rule 3
		// that is actually about the provider.
		agentSessionRef: { runtimeAttemptId: attemptId, posture,
		                   sessionEpoch: epoch, providerSessionId: null },
		profileDigest, pinnedPolicy: pinned,
		workRef: { authorityUuid: attempt.authority_uuid,
		           workId: attempt.work_id },
		assignment,
		workspace: binding.workspace,
		declaredOutput: binding.declared_output,
		state: "not-started",
	};
}

/** Close one session, which is the ONLY thing that frees its posture.
 *
 *  A later epoch begins after this one closes. `unknown` does not free the
 *  posture and never will here: re-identification after transport ambiguity
 *  is a gate this slice has not built, and opening a second session while the
 *  first may still be alive is exactly what the one-open rule prevents. */
export function closeAgentSession(store, { attemptId, posture, epoch }) {
	const changed = store.db.prepare(
		"UPDATE agent_sessions SET state = 'closed' WHERE "
		+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ? "
		+ "AND state <> 'closed'").run(attemptId, posture, epoch).changes;
	return { attemptId, posture, epoch, closed: changed === 1 };
}

/** Every session opened for this attempt, oldest first. */
export function agentSessionsOf(store, attemptId) {
	return store.db.prepare(
		"SELECT * FROM agent_sessions WHERE runtime_attempt_id = ? "
		+ "ORDER BY posture, session_epoch").all(attemptId);
}
