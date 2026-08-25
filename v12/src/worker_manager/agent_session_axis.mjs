// W2929 plan item 4, sixth slice: THE AGENT-SESSION OBSERVATION AXIS.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance, frozen §7.3:
//
//   "`agent_session_state` moves monotonically and never regresses."
//
//   not-started -> initializing -> ready -> prompting -> turn-ended -> closed
//                                             |
//                                             +-> cancel-requested
//                                             |     -> agent-quiescent
//                                             |     -> unknown
//                                             +-> unknown
//
// THE TABLE IS THE RULE, and it is transcribed from the frozen design model
// rather than re-derived from the diagram — the diagram shows the spine and
// the model carries the exact successor sets, including the edges the spine
// does not draw (`ready -> cancel-requested`, `turn-ended -> prompting` for a
// second supervised turn in one epoch, and the `-> closed` edges).
//
// `unknown` IS TERMINAL AND STAYS THERE. §3.3 and §7.3 both say so, and the
// reason is the whole point of the axis: `unknown` means no terminal fact was
// observed. Promoting it to `closed` would record knowledge that was never
// acquired — a session record asserting that every turn the epoch started has
// a terminal fact, when the honest answer is that nobody saw the ending.
//
// AND A FINISHED CONVERSATION IS NOT AN ABSENT RUNTIME. §7.4's rule has one
// implementation here and it always answers false: no agent-session state
// satisfies `runtime-quiescence`, because the gate is about whether the
// runtime holding the generation is gone and every state on this axis is
// about what an agent said.

import { ContractError, nameValue, opaqueIdFault, withinFrozenLength }
	from "./contracts.mjs";

/** The frozen `$defs.providerSessionId` upper bound. */
const PROVIDER_SESSION_ID_LIMIT = 512;

/** The nine. §7.3, and the schema's `sessionState` enum is the same nine. */
export const SESSION_STATES = Object.freeze(["not-started", "initializing",
	"ready", "prompting", "turn-ended", "cancel-requested", "agent-quiescent",
	"unknown", "closed"]);

/** Which state may follow which. Transcribed from the frozen model.
 *
 *  Two rows are worth reading twice. `turn-ended -> prompting` is how one
 *  epoch runs a second supervised turn, which is the fact the turn slice's
 *  identity allocation exists for. And `unknown` and `closed` have EMPTY
 *  successor sets: both are terminal, and `unknown` is terminal in the
 *  direction that matters — it never becomes `closed`, because that would be
 *  claiming an observation nobody made. */
export const ALLOWED_SESSION_SUCCESSORS = Object.freeze({
	"not-started": Object.freeze(["initializing", "unknown"]),
	initializing: Object.freeze(["ready", "unknown", "closed"]),
	ready: Object.freeze(["prompting", "cancel-requested", "unknown",
		"closed"]),
	prompting: Object.freeze(["turn-ended", "cancel-requested", "unknown"]),
	"turn-ended": Object.freeze(["prompting", "cancel-requested", "unknown",
		"closed"]),
	"cancel-requested": Object.freeze(["agent-quiescent", "unknown"]),
	"agent-quiescent": Object.freeze(["closed"]),
	unknown: Object.freeze([]),
	closed: Object.freeze([]),
});

/** The states with no successor at all. */
export const TERMINAL_SESSION_STATES = Object.freeze(SESSION_STATES.filter(
	(state) => ALLOWED_SESSION_SUCCESSORS[state].length === 0));

function knownState(state, where) {
	if (!SESSION_STATES.includes(state)) {
		throw new ContractError("integrity", "schema",
			`${nameValue(state)} is not one of the nine agent `
			+ `session states (${where})`);
	}
	return state;
}

/** Whether `to` may follow `from`. Pure, and the one place the table is read. */
export function permitsSessionTransition(from, to) {
	knownState(from, "from");
	knownState(to, "to");
	// AN OBSERVATION OF THE SAME STATE IS NOT A MOVE. The axis is what the
	// relay has OBSERVED, and observing the same thing twice is ordinary —
	// the model returns the current state rather than refusing, and refusing
	// would make a duplicate frame look like a regression.
	if (from === to) return true;
	return ALLOWED_SESSION_SUCCESSORS[from].includes(to);
}

/** The caller's session reference, PROVEN before it reaches any query.
 *
 *  Review [P1]: the axis built its reference from three components and
 *  dropped `provider_session_id` entirely, so a label naming provider session
 *  B moved the row durably held for provider session A — and a malformed
 *  reference reached SQLite as a raw binding error rather than a closed pair.
 *
 *  This is the THIRD boundary in this Work to need the same sentence: §3.1
 *  makes the provider id the fourth component of the reference that labels
 *  evidence, the turn and event boundaries already bind it, and I wrote a new
 *  one that did not — two rounds after the event reader was corrected for
 *  binding three quarters of exactly this.
 *
 *  EXPORTED, so a caller that also has to REPORT the reference can take one
 *  snapshot and hand the same object to this boundary. Reading a caller's
 *  property twice — once to validate and once to report — is how a getter
 *  answers A to the check and B to the record. */
export function normalizeAgentSessionRef(sessionRef) {
	const runtimeAttemptId = sessionRef?.runtimeAttemptId;
	const posture = sessionRef?.posture;
	const sessionEpoch = sessionRef?.sessionEpoch;
	const providerSessionId = sessionRef?.providerSessionId ?? null;
	// Review [P1], and the frozen schema rather than a ruling: §3.1 types
	// `runtime_attempt_id` as `$ref: opaqueId` and `provider_session_id` as
	// `$ref: providerSessionId`, and neither bound was enforced. A malformed
	// attempt id reached the event reader's query and came back as ABSENCE.
	// The opaque-id proof is the shared one, so this boundary and the two
	// read boundaries cannot reach different conclusions about one string.
	//
	// THE CONTAINER QUESTION IS UNTOUCHED. This proves the MEMBERS the frozen
	// schema types; whether the reference must itself be an exact inert
	// record is item 4ah and is still open.
	if (opaqueIdFault(runtimeAttemptId) !== null
			|| (posture !== "consent" && posture !== "execution")
			|| !Number.isInteger(sessionEpoch) || sessionEpoch < 1
			|| (providerSessionId !== null
				&& (typeof providerSessionId !== "string"
					|| providerSessionId.length === 0
					|| !withinFrozenLength(providerSessionId,
						PROVIDER_SESSION_ID_LIMIT)))) {
		throw new ContractError("integrity", "schema",
			`${nameValue(sessionRef)} is not an agent session `
			+ `reference; §3.1 is an attempt, a posture, a positive epoch and `
			+ `a nonempty opaque provider session id or none`);
	}
	return { runtimeAttemptId, posture, sessionEpoch, providerSessionId };
}

/** Move one durable session's axis, or refuse.
 *
 *  Returns `{ state, moved }` — the state that now holds, and whether this
 *  observation changed it. Re-observing the current state is a no-op that
 *  answers rather than refuses, so a retransmitted observation is harmless.
 *
 *  DECIDED INSIDE THE WRITE TRANSACTION, for the reason the runtime
 *  observations already carry: a read of the current state followed by a
 *  separate write is not a monotone axis across two manager connections. Two
 *  managers both pass any read, and only the transaction decides. */
export function observeAgentSessionState(store, sessionRef, state) {
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	try {
		const answer = observeAgentSessionStateIn(db, sessionRef, state);
		db.exec("COMMIT");
		return answer;
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
}

/** The same observation, INSIDE a caller's transaction.
 *
 *  Exposed so an act that both observes and moves a posture slot is ONE
 *  transaction rather than two a crash can separate. The proof and the
 *  binding are identical; only who owns the transaction differs. */
export function observeAgentSessionStateIn(db, sessionRef, state) {
	const ref = normalizeAgentSessionRef(sessionRef);
	knownState(state, "observed");
	{
		const row = db.prepare(
			"SELECT state, provider_session_id FROM agent_sessions WHERE "
			+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
			.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch);
		if (row === undefined) {
			throw new ContractError("refused", "precondition",
				`no agent session ${ref.posture}/${ref.sessionEpoch} for `
				+ `attempt ${ref.runtimeAttemptId}; an axis belongs to a `
				+ `session`);
		}
		// THE LABEL IS BOUND BEFORE EITHER ANSWER. A no-op is still an
		// observation: affirming that provider session B's axis reads
		// `prompting` is a claim about B, and answering it from A's row is
		// the same mistake as moving A's row — so the binding precedes the
		// self-observation shortcut rather than sitting after it.
		const stored = row.provider_session_id ?? null;
		if (stored !== ref.providerSessionId) {
			throw new ContractError("runtime-observation", "identity-mismatch",
				`this observation names provider session `
				+ `${JSON.stringify(ref.providerSessionId)} and epoch `
				+ `${ref.posture}/${ref.sessionEpoch} durably names `
				+ `${JSON.stringify(stored)}; the reference labels evidence `
				+ `and must be the one the session actually holds`);
		}
		// The stored value is proved to be one of the nine before it decides
		// anything: a row edited to carry a state this contract never had
		// would otherwise index into the table and read `undefined`.
		knownState(row.state, "stored");
		if (row.state === state) {
			return { state, moved: false };
		}
		if (!permitsSessionTransition(row.state, state)) {
			throw new ContractError("runtime-observation", "state-regression",
				`agent session ${ref.posture}/${ref.sessionEpoch} is `
				+ `${row.state} and cannot move to ${state}; §7.3 permits `
				+ `${ALLOWED_SESSION_SUCCESSORS[row.state].join(", ") || "no "
				+ "successor at all"}`);
		}
		db.prepare(
			"UPDATE agent_sessions SET state = ? WHERE runtime_attempt_id = ? "
			+ "AND posture = ? AND session_epoch = ?")
			.run(state, ref.runtimeAttemptId, ref.posture, ref.sessionEpoch);
		return { state, moved: true };
	}
}

/** §7.4 — the one function here that always answers false.
 *
 *  A finished conversation says nothing about whether the runtime that held
 *  the generation is absent. The gate is satisfied only by worker-control
 *  §6.3 runtime inspection reaching positive absence, or by W151's pinned
 *  certified-isolation clause. Neither is an agent-session fact, and
 *  `agent-quiescent` is the state most likely to be mistaken for one —
 *  §7.4's title is "agent quiescence is not runtime quiescence" for exactly
 *  that reason.
 *
 *  It takes a state and validates it rather than ignoring its argument,
 *  because a caller passing a state this contract does not have is asking a
 *  malformed question, and answering `false` to a malformed question is how
 *  a caller concludes it asked a good one. */
export function satisfiesRuntimeQuiescenceGate(state) {
	knownState(state, "observed");
	return false;
}
