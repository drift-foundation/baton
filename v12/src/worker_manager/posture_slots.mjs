// W771: POSTURE OCCUPANCY, separated from the observation axis.
//
// `work/records/2026/08/finding-agent-session-close-axis-conflict/`
//
// The confirmed ruling, 2026-08-23:
//
//   "Preserve the provider-observation axis exactly as evidence. `unknown`
//    remains terminal and is never promoted to `closed` merely because the
//    manager ordered a close, lost transport, reached a deadline, or wants to
//    reuse the posture. Posture occupancy is a separate manager-owned axis:
//
//        available -> occupied -> recovery-required -> available"
//
// WHY THE TWO WERE TANGLED, since that is what the ruling untangles. The
// partial unique index made occupancy a projection of `agent_session_state`,
// so the only way to get a posture back was to write `closed` — and `closed`
// asserts that a terminal turn fact was observed for every turn the epoch
// started. A session that died before it initialized had no such facts, so
// recovering capacity meant inventing knowledge. The close path did exactly
// that, over four states §7.3 forbids.
//
// SILENCE AND ELAPSED TIME NEVER RECOVER A SLOT. Moving out of
// `recovery-required` takes positive evidence that the old provider session
// CANNOT STILL ACT. For the OCI reference runtime that is the adapter
// observing the exact assignment container stopped or absent — a request to
// stop is not proof, and the runtime-neutral contract records the observation
// rather than making Docker a protocol concept.
//
// AND RECOVERY DOES NOT REWRITE HISTORY. A durable result of
//
//     observation: unknown   runtime: stopped   slot: available
//
// is coherent and is the normal shape after transport loss. Stopping the
// container recovers execution capacity; it does not discard a filesystem,
// accept an output, or choose salvage — those stay independent disposition
// decisions this module has no opinion about.

import { ContractError, nameValue, opaqueIdFault }
	from "./contracts.mjs";

/** The three. §7.3's nine states are a different axis and stay that way. */
export const SLOT_OCCUPANCY = Object.freeze(["available", "occupied",
	"recovery-required"]);

export const POSTURES = Object.freeze(["consent", "execution"]);

/** The kinds of evidence that can positively establish absence.
 *
 *  A closed set, because "the manager believes it is gone" is not one of
 *  them. `provider-session-closed` is the normally observed end of a session;
 *  `runtime-absent` is the adapter observing the exact runtime identity
 *  stopped or no longer present. Both are OBSERVATIONS. A stop request, a
 *  deadline and a disconnect are none of them, and there is deliberately no
 *  member for any of the three. */
export const RECOVERY_EVIDENCE = Object.freeze(["provider-session-closed",
	"runtime-absent"]);

function requireEvidence(evidence, runtimeIdentity) {
	if (!RECOVERY_EVIDENCE.includes(evidence)) {
		throw new ContractError("integrity", "schema",
			`${nameValue(evidence)} is not positive absence `
			+ `evidence; a slot is recovered by `
			+ `${RECOVERY_EVIDENCE.join(" or ")}, and silence, an elapsed `
			+ `deadline or a stop REQUEST is none of them`);
	}
	if (evidence === "runtime-absent"
			&& (typeof runtimeIdentity !== "string"
				|| runtimeIdentity.length === 0)) {
		throw new ContractError("integrity", "schema",
			`runtime-absent evidence names the exact runtime identity that was `
			+ `observed stopped or absent; "the container is gone" without `
			+ `saying which container is a claim about nothing`);
	}
}

function requirePosture(posture) {
	if (!POSTURES.includes(posture)) {
		throw new ContractError("integrity", "schema",
			`${nameValue(posture)} is not a posture`);
	}
	return posture;
}

function requireAttempt(attemptId) {
	// THE SHARED FROZEN PROOF, not a third opinion. This checked "nonempty
	// string" while the axis and the two read boundaries were being taught
	// the frozen `opaqueId` rule — which would have made a string with a
	// space in it a valid attempt here and an invalid one there. That is the
	// 4al defect, and the way to not repeat it is to not have a local copy of
	// the question.
	const fault = opaqueIdFault(attemptId);
	if (fault !== null) {
		throw new ContractError("integrity", "schema",
			`a runtime attempt id ${fault}`);
	}
	return attemptId;
}

function requireEpoch(epoch) {
	if (!Number.isInteger(epoch) || epoch < 1) {
		throw new ContractError("integrity", "schema",
			`${nameValue(epoch)} is not a positive session epoch`);
	}
	return epoch;
}

function requireReason(reason) {
	if (typeof reason !== "string" || reason.trim().length === 0) {
		throw new ContractError("integrity", "schema",
			`a slot movement carries a non-empty reason; a reader who finds a `
			+ `posture unavailable needs to know why without guessing`);
	}
	return reason;
}

/** The slot as it stands, or null when the posture has never been used. */
export function postureSlot(store, attemptId, posture) {
	const row = store.db.prepare(
		"SELECT occupancy, session_epoch, reason, changed_at FROM "
		+ "posture_slots WHERE runtime_attempt_id = ? AND posture = ?")
		.get(requireAttempt(attemptId), requirePosture(posture));
	if (row === undefined) return null;
	if (!SLOT_OCCUPANCY.includes(row.occupancy)) {
		throw new ContractError("integrity", "schema",
			`the slot for ${posture} holds ${JSON.stringify(row.occupancy)}, `
			+ `which is not one of ${SLOT_OCCUPANCY.join(", ")}`);
	}
	return { attemptId, posture, occupancy: row.occupancy,
	         sessionEpoch: row.session_epoch, reason: row.reason,
	         changedAt: row.changed_at };
}

/** OCCUPY the slot for one epoch, or refuse. Atomic.
 *
 *  A never-used posture is created `available` and taken in the same
 *  statement pair, under the caller's write transaction, so the first open
 *  and the second open are decided by the database rather than by a read.
 *
 *  Called from INSIDE `openAgentSession`'s transaction, which is why it takes
 *  a `db` rather than a store: the slot and the session row are one act. A
 *  posture occupied by an epoch that never became a session would be exactly
 *  the stranding this ruling exists to remove. */
export function occupySlot(db, { attemptId, posture, sessionEpoch, at }) {
	requireAttempt(attemptId);
	requirePosture(posture);
	requireEpoch(sessionEpoch);
	// INSERT-OR-NOTHING first, so a posture nobody has used becomes an
	// `available` row without a read deciding anything.
	db.prepare(
		"INSERT OR IGNORE INTO posture_slots (runtime_attempt_id, posture, "
		+ "occupancy, session_epoch, reason, changed_at) "
		+ "VALUES (?, ?, 'available', NULL, NULL, ?)")
		.run(attemptId, posture, at);
	const taken = db.prepare(
		"UPDATE posture_slots SET occupancy = 'occupied', session_epoch = ?, "
		+ "reason = NULL, changed_at = ? WHERE runtime_attempt_id = ? "
		+ "AND posture = ? AND occupancy = 'available'")
		.run(sessionEpoch, at, attemptId, posture).changes;
	if (taken !== 1) {
		const row = db.prepare(
			"SELECT occupancy, session_epoch, reason FROM posture_slots "
			+ "WHERE runtime_attempt_id = ? AND posture = ?")
			.get(attemptId, posture);
		throw new ContractError("runtime-observation", "duplicate-runtime",
			`the ${posture} posture of ${attemptId} is ${row?.occupancy} `
			+ `(epoch ${row?.session_epoch ?? "none"}`
			+ `${row?.reason ? `: ${row.reason}` : ""}); a posture holds one `
			+ `session, and a later epoch begins only after this slot is `
			+ `recovered`);
	}
	return { attemptId, posture, occupancy: "occupied", sessionEpoch };
}

/** The slot as the write transaction sees it, with the epoch bound.
 *
 *  Review [P1]: both mutations selected by attempt and posture only, so a
 *  DELAYED report about epoch 1 moved or freed epoch 2. Evidence is about the
 *  epoch that produced it; applied to a later occupant it is not stale
 *  evidence, it is evidence about something else.
 *
 *  The comparison runs in the idempotent branches too. "Already released" is
 *  only an answer to a retry if the release being retried is the one that
 *  happened — otherwise an older epoch's evidence would be answered as though
 *  it had succeeded. */
function boundSlot(db, { attemptId, posture, sessionEpoch }) {
	const row = db.prepare(
		"SELECT occupancy, session_epoch, reason FROM posture_slots WHERE "
		+ "runtime_attempt_id = ? AND posture = ?").get(attemptId, posture);
	if (row === undefined) {
		throw new ContractError("refused", "precondition",
			`the ${posture} posture of ${attemptId} has never been occupied; `
			+ `there is nothing to recover`);
	}
	if (row.session_epoch !== sessionEpoch) {
		throw new ContractError("runtime-observation", "identity-mismatch",
			`this evidence is about ${posture}/${sessionEpoch} and the slot `
			+ `holds ${posture}/${row.session_epoch}; evidence about one `
			+ `epoch says nothing about the one that replaced it`);
	}
	return row;
}

/** Prove the durable fact an evidence NAME claims, or refuse.
 *
 *  Review [P1]: this boundary checked the SPELLING of a caller's assertion
 *  and called it positive evidence. `provider-session-closed` released a slot
 *  whose session was still `ready`, and `runtime-absent` accepted any
 *  non-empty string without ever comparing it with the runtime the attempt is
 *  durably attached to. A closed vocabulary of labels is not evidence; it is
 *  a closed vocabulary of claims.
 *
 *  `provider-session-closed` therefore requires the SAME EPOCH's observation
 *  to durably be `closed` — the axis is where that fact is established, and
 *  this reads it rather than trusting a caller who says it happened.
 *
 *  `runtime-absent` requires the exact `attempts.runtime_id`. A missing,
 *  foreign or stale identity recovers nothing, because "some container is
 *  gone" is not "the container that held this assignment is gone".
 *
 *  Neither path REWRITES the observation. Runtime evidence recovers capacity
 *  and says nothing about what the provider was seen to do. */
function proveEvidence(db, { attemptId, posture, sessionEpoch, evidence,
                             runtimeIdentity }) {
	if (evidence === "provider-session-closed") {
		const session = db.prepare(
			"SELECT state FROM agent_sessions WHERE runtime_attempt_id = ? "
			+ "AND posture = ? AND session_epoch = ?")
			.get(attemptId, posture, sessionEpoch);
		if (session === undefined) {
			throw new ContractError("refused", "precondition",
				`no agent session ${posture}/${sessionEpoch} for ${attemptId}`);
		}
		if (session.state !== "closed") {
			throw new ContractError("refused", "precondition",
				`${posture}/${sessionEpoch} is observed ${session.state}, not `
				+ `closed; a provider-close release reads the observation `
				+ `rather than trusting a caller that one happened`);
		}
		return;
	}
	const attempt = db.prepare(
		"SELECT runtime_id FROM attempts WHERE runtime_attempt_id = ?")
		.get(attemptId);
	const attached = attempt?.runtime_id ?? null;
	if (attached === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} is attached to no runtime, so no runtime `
			+ `identity can have been observed absent for it`);
	}
	if (runtimeIdentity !== attached) {
		throw new ContractError("runtime-observation", "identity-mismatch",
			`${nameValue(runtimeIdentity)} was observed absent and `
			+ `attempt ${attemptId} is attached to ${JSON.stringify(attached)}`
			+ `; some container being gone is not the one that held this `
			+ `assignment being gone`);
	}
}

/** Move the slot to `recovery-required`, or refuse.
 *
 *  This is what an ambiguous ending does. It is NOT a failure state and it is
 *  not terminal — it says the epoch that held the slot may still be able to
 *  act and nobody has established otherwise, which is the honest reading of a
 *  dead transport, an elapsed deadline or a close nobody saw complete.
 *
 *  It changes no observation. The session's own axis is wherever the provider
 *  was actually seen to be, and that is the point of the separation. */
export function requireSlotRecovery(store, { attemptId, posture,
                                             sessionEpoch, reason }) {
	requireAttempt(attemptId);
	requirePosture(posture);
	requireEpoch(sessionEpoch);
	requireReason(reason);
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	try {
		const answer = requireSlotRecoveryIn(db, store.clock(),
			{ attemptId, posture, sessionEpoch, reason });
		db.exec("COMMIT");
		return answer;
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
}

/** The same act, INSIDE a caller's transaction.
 *
 *  Review [P1]: transport loss recorded `unknown` and left the slot occupied,
 *  and composing the two through two separate transactions would leave a
 *  crash window where the observation had landed and the slot had not. One
 *  transaction or an explicitly repairable protocol — this is the first. */
export function requireSlotRecoveryIn(db, at, { attemptId, posture,
                                                sessionEpoch, reason }) {
	requireAttempt(attemptId);
	requirePosture(posture);
	requireEpoch(sessionEpoch);
	requireReason(reason);
	{
		const row = boundSlot(db, { attemptId, posture, sessionEpoch });
		if (row.occupancy === "recovery-required") {
			// Reporting the same ambiguity twice is ordinary; the FIRST
			// reason is kept, because the later report observed nothing new.
			return { attemptId, posture, occupancy: "recovery-required",
			         sessionEpoch: row.session_epoch, moved: false };
		}
		if (row.occupancy !== "occupied") {
			throw new ContractError("refused", "precondition",
				`the ${posture} posture of ${attemptId} is ${row.occupancy}; `
				+ `only an occupied slot can become ambiguous`);
		}
		db.prepare(
			"UPDATE posture_slots SET occupancy = 'recovery-required', "
			+ "reason = ?, changed_at = ? WHERE runtime_attempt_id = ? "
			+ "AND posture = ?").run(reason, at, attemptId, posture);
		return { attemptId, posture, occupancy: "recovery-required",
		         sessionEpoch: row.session_epoch, moved: true };
	}
}

/** RELEASE the slot on positive evidence, or refuse.
 *
 *  The whole ruling lives here. A slot returns to `available` only when
 *  something was OBSERVED that establishes the old provider session cannot
 *  still act — a normally observed provider-session close, or the runtime
 *  itself observed stopped or absent by its exact identity.
 *
 *  `runtime-absent` REQUIRES the identity that was observed, because "the
 *  container is gone" without saying which container is a claim about
 *  nothing. A stale identity is a stale observation and it recovers nothing.
 *
 *  It touches no session row. `observation: unknown / slot: available` is a
 *  coherent durable result and is the normal shape after transport loss. */
export function releaseSlot(store, { attemptId, posture, sessionEpoch, evidence,
                                     runtimeIdentity = null, reason }) {
	requireAttempt(attemptId);
	requirePosture(posture);
	requireEpoch(sessionEpoch);
	requireReason(reason);
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	try {
		const answer = releaseSlotIn(db, store.clock(),
			{ attemptId, posture, sessionEpoch, evidence, runtimeIdentity,
			  reason });
		db.exec("COMMIT");
		return answer;
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
}

/** The same act, INSIDE a caller's transaction — so an operation that both
 *  establishes an observation and releases on it is ONE act rather than two
 *  that a crash can separate. */
export function releaseSlotIn(db, at, { attemptId, posture, sessionEpoch, evidence,
                                        runtimeIdentity = null, reason }) {
	requireAttempt(attemptId);
	requirePosture(posture);
	requireEpoch(sessionEpoch);
	requireReason(reason);
	requireEvidence(evidence, runtimeIdentity);
	const row = boundSlot(db, { attemptId, posture, sessionEpoch });
	// THE NAMED FACT, PROVED. Before this, the slot state is irrelevant: a
	// caller whose evidence is not real must not learn whether a retry would
	// have answered.
	proveEvidence(db, { attemptId, posture, sessionEpoch, evidence,
	                    runtimeIdentity });
	if (row.occupancy === "available") {
		// Already recovered, for THIS epoch — `boundSlot` established that.
		// A retried recovery answers rather than refusing, because the
		// evidence has not changed and neither has the slot.
		return { attemptId, posture, occupancy: "available",
		         releasedEpoch: row.session_epoch, moved: false };
	}
	db.prepare(
		"UPDATE posture_slots SET occupancy = 'available', reason = ?, "
		+ "changed_at = ? WHERE runtime_attempt_id = ? AND posture = ?")
		.run(reason, at, attemptId, posture);
	return { attemptId, posture, occupancy: "available",
	         releasedEpoch: row.session_epoch, moved: true };
}
