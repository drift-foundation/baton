// W2929 plan item 4, third slice: THE TURN AND ITS OUTCOME.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance:
//
//   "Every turn has a manager deadline. Turn outcome is selected only from the
//    closed eight-value vocabulary and only from a terminal provider fact,
//    policy failure, deadline or transport death. It gates but never chooses
//    worker disposition."
//
// SELECTED, NEVER INFERRED. The ACP boundary's §5.4 lists what an outcome is
// NOT derived from: silence, transport closure, an empty update stream, a
// tool call's own status, agent prose, and reachability at any layer. So this
// module takes the evidence a relay actually holds and REFUSES when none of
// it names an outcome — the alternative to refusing is guessing, and every
// item on that list is a guess somebody could defend.
//
// GATES, NEVER CHOOSES. The worker declares its disposition; the outcome only
// decides whether such a declaration may be accepted at all.
//
// AND THE RECORD IS THE RECORD. Review [P1], four findings converging: the
// durable turn bypassed its frozen shape and seal, the policy fact that
// SELECTED the outcome was discarded, the act was neither replay- nor
// collision-safe, and the first answer aliased the caller's object. They have
// one correction between them — build the complete frozen `turnRecord`,
// validate it against the placed schema BEFORE reading semantic members, seal
// it, and commit it through the manager's own operation journal, whose
// byte-stable result is what the first caller and every later one receive.
//
// AND AN IDENTITY IS ALLOCATED, NEVER DERIVED FROM OPERANDS. Fourth
// re-review [P1]: I answered "give every supervised turn a stable identity
// independent of prompt content" by hashing the caller's `started_at` and
// `deadline_at` and keeping `prompt_digest` to tell two reuses apart. That is
// reusable DATA that happens to differ, not an identity — nothing allocated
// it, nothing recorded the allocation, no constraint made it unique in the
// epoch, and prompt bytes were still the fallback deciding whether one
// supervised act was one turn or two. The supervision boundary MINTS the
// identity now (`allocateTurn`), the database enforces one per epoch ordinal,
// the record REFERENCES its allocation, and the prompt lives where the review
// put it: in the effective signature, so a changed prompt under one allocated
// turn COLLIDES instead of quietly becoming a second turn.
//
// AND AN IMMUTABLE ANSWER IS RESOLVED BEFORE TODAY'S STATE. Third re-review
// [P1 x3, P2]: the identity was derived from prompt bytes alone, so a second
// legitimate turn that happened to send the same prompt reached the FIRST
// turn's operation id; admission proved a session row existed and then read
// nothing out of it; and both the durable-secret liveness scan and that
// admission ran BEFORE the journal could answer, so mutable current state
// could hide an answer already committed. One shape holds all three: the
// turn's identity carries the manager-owned supervision window that §5.1
// mints per supervised turn, and every check that depends on state as it is
// NOW moved inside the write transaction, which the journal resolves first.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { assertNoDurableSecret, canonicalBytes, ContractError, digest,
         nameValue, opaqueIdFault } from "./contracts.mjs";
import { normalizeAgentSessionRef }
	from "./agent_session_axis.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const AGENT_SESSION_SCHEMA = JSON.parse(readFileSync(
	join(HERE, "schema", "agent-session-1.0.schema.json")).toString("utf8"));

const _ajv = new Ajv2020({ strict: false, validateFormats: false,
                           allErrors: false });
// Two definitions out of ONE document, so the shared `$id` is dropped: Ajv
// keys compiled schemas by it and refuses a second registration under the
// same one. The definitions are unchanged; only the registration key is.
function definitionOf(name) {
	const { $id: _id, oneOf: _oneOf, ...rest } = AGENT_SESSION_SCHEMA;
	return { ...rest, $ref: `#/$defs/${name}` };
}

const _validateTurn = _ajv.compile(definitionOf("turnRecord"));
const _validatePolicyFailure = _ajv.compile(definitionOf("policyFailure"));

/** The closed eight. Every turn ends in exactly one of these. */
export const TURN_OUTCOMES = Object.freeze(["completed", "refused",
	"truncated", "cancelled", "agent-failed", "policy-failed", "timeout",
	"transport-lost"]);

/** ACP `stopReason` maps EXACTLY, and nothing else maps at all. */
export const ACP_STOP_REASONS = Object.freeze({
	end_turn: "completed",
	refusal: "refused",
	max_tokens: "truncated",
	max_turn_requests: "truncated",
	cancelled: "cancelled",
});

/** Codex app-server's THREE terminal statuses (§10.3).
 *
 *  Review [P1]: I had two, and my own case asserted that `failed` must be
 *  REFUSED — contradicting a table the boundary had already frozen. A
 *  vocabulary I shortened is not a stricter vocabulary; it is a different
 *  one, and the difference was invisible because I also wrote the test. */
export const CODEX_TURN_STATUSES = Object.freeze({
	completed: "completed",
	interrupted: "cancelled",
	failed: "agent-failed",
});

/** §10.6, verbatim: `codexErrorInfo` into the CLOSED taxonomy.
 *
 *  `ContextWindowExceeded` is the one case where the provider reports budget
 *  exhaustion structurally, which is why §10.3 defers here rather than
 *  calling every failure `agent-failed`. Nothing new is minted; the raw
 *  string is untrusted diagnostics and selects nothing beyond this table. */
export const CODEX_ERROR_INFO = Object.freeze({
	ContextWindowExceeded: Object.freeze({ outcome: "truncated",
		reported: Object.freeze({ category: "unavailable",
		                          code: "source-provider" }) }),
	UsageLimitExceeded: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "source-provider" }) }),
	HttpConnectionFailed: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "transport" }) }),
	ResponseStreamConnectionFailed: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "transport" }) }),
	ResponseStreamDisconnected: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "transport" }) }),
	ResponseTooManyFailedAttempts: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "transport" }) }),
	Unauthorized: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "policy", code: "denied" }) }),
	SandboxError: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "policy", code: "denied" }) }),
	BadRequest: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "source-provider" }) }),
	InternalServerError: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "source-provider" }) }),
	Other: Object.freeze({ outcome: "agent-failed",
		reported: Object.freeze({ category: "unavailable",
		                          code: "source-provider" }) }),
});

// "The raw `codexErrorInfo` string is retained as untrusted diagnostics; it
// selects nothing beyond this table, and AN UNRECOGNIZED VALUE TAKES THE LAST
// ROW." — §10.6, quoted because the review asked for a refusal instead.
// Refusing would be stricter and would contradict a decision the boundary
// already froze, and the honest place for that disagreement is the handoff
// rather than a silent divergence in either direction.
const CODEX_ERROR_UNRECOGNIZED = CODEX_ERROR_INFO.Other;

/** WHICH DISPOSITIONS AN OUTCOME PERMITS — the acceptance table, verbatim. */
export const PERMITTED_DISPOSITIONS = Object.freeze({
	completed: Object.freeze(["completed", "unable", "plan-rejected"]),
	refused: Object.freeze(["unable"]),
	truncated: Object.freeze(["unable"]),
	"agent-failed": Object.freeze(["unable"]),
	cancelled: Object.freeze([]),
	"policy-failed": Object.freeze([]),
	timeout: Object.freeze([]),
	"transport-lost": Object.freeze([]),
});

/** Whether the TURN conclusively ended. Never a statement about the runtime. */
export const CONCLUSIVE = Object.freeze({
	completed: true, refused: true, truncated: true, cancelled: true,
	"agent-failed": true, "policy-failed": true,
	timeout: false, "transport-lost": false,
});

const TERMINAL_KINDS = Object.freeze(["acp-stop-reason", "codex-turn-status",
	"codex-error-info", "relay-policy", "relay-deadline", "none"]);

/** Select the outcome from the evidence, or refuse.
 *
 *  THE ORDER IS THE ARGUMENT. A §4 violation ends the turn where it happens,
 *  so it outranks anything that arrives afterwards. A terminal provider fact
 *  outranks a deadline, because the fact ARRIVED. Transport death outranks the
 *  deadline for the same reason it is a different outcome: the epoch is gone,
 *  which is more than "nothing has come back yet".
 *
 *  And with none of them, this REFUSES. */
export function selectTurnOutcome({ terminalFact = null,
                                    policyFailures = [],
                                    transportLost = false,
                                    deadlineElapsed = false } = {}) {
	requirePolicyFailureList(policyFailures);
	if (policyFailures.length > 0) return "policy-failed";
	if (terminalFact !== null && terminalFact.kind !== "none") {
		return fromTerminalFact(terminalFact).outcome;
	}
	if (transportLost) return "transport-lost";
	if (deadlineElapsed) return "timeout";
	throw new ContractError("integrity", "schema",
		"this turn carries no terminal fact, no policy failure, no transport "
		+ "death and no elapsed deadline; silence, an empty update stream, a "
		+ "tool call's own status and agent prose are none of them an outcome");
}

/** Prove the COLLECTION before anything iterates or counts it.
 *
 *  Review [P1]: any array-like with a nonzero `length` selected
 *  `policy-failed`. A count is not a policy failure. Third re-review [P2]:
 *  and `recordTurn` reached `.map` on the same value before this ran at all,
 *  so `policyFailures: null` left as a raw `TypeError` — the frozen rule is
 *  that every reported failure is one closed category/code pair, and an
 *  interpreter-authored error is not one however accurate it is. */
function requirePolicyFailureList(policyFailures) {
	if (!Array.isArray(policyFailures)) {
		throw new ContractError("integrity", "schema",
			"policy failures are a list of frozen policyFailure documents; "
			+ "a value that merely has a length is not one");
	}
	return policyFailures;
}

/** The outcome AND the closed error pair a terminal fact reports as. */
export function fromTerminalFact(fact) {
	if (!TERMINAL_KINDS.includes(fact?.kind)) {
		throw new ContractError("integrity", "schema",
			`${fact?.kind} is not a terminal fact kind`);
	}
	if (fact.kind === "acp-stop-reason") {
		const mapped = ACP_STOP_REASONS[fact.value];
		if (mapped === undefined) {
			throw new ContractError("integrity", "schema",
				`${fact.value} is not an ACP stop reason; the mapping is `
				+ `exact and an unknown one is not a turn outcome`);
		}
		return { outcome: mapped, reported: null };
	}
	if (fact.kind === "codex-turn-status") {
		const mapped = CODEX_TURN_STATUSES[fact.value];
		if (mapped === undefined) {
			throw new ContractError("integrity", "schema",
				`${fact.value} is not one of the three codex turn statuses`);
		}
		return { outcome: mapped, reported: null };
	}
	if (fact.kind === "codex-error-info") {
		const row = CODEX_ERROR_INFO[fact.value] ?? CODEX_ERROR_UNRECOGNIZED;
		return { outcome: row.outcome, reported: row.reported };
	}
	if (fact.kind === "relay-policy") {
		return { outcome: "policy-failed", reported: null };
	}
	if (fact.kind === "relay-deadline") {
		return { outcome: "timeout", reported: null };
	}
	throw new ContractError("integrity", "schema",
		`a terminal fact of kind ${fact.kind} names no outcome`);
}

/** The states in which a supervised turn may legitimately SETTLE.
 *
 *  A closed set, named positively rather than by excluding today's two bad
 *  ones: the question an admission asks is "may a turn end here", and a list
 *  of the states where it may not is a list that a new state joins silently
 *  and wrongly.
 *
 *  `not-started` and `initializing` are out because no prompt has been issued
 *  yet. `unknown` and `closed` are out because they are TERMINAL — §3.3 says
 *  a session reaches `closed` only once a terminal turn fact was observed for
 *  every turn the epoch started, and `unknown` is the honest end of an epoch
 *  whose ending nobody observed. A turn arriving after either one is evidence
 *  about a settled epoch, and settling it anyway would make the session
 *  record say something it never knew. */
export const TURN_ADMITTING_SESSION_STATES = Object.freeze(["ready",
	"prompting", "turn-ended", "cancel-requested", "agent-quiescent"]);

/** The states in which a supervised turn may be OPENED. Exactly one.
 *
 *  Fifth re-review [P1]: allocation checked only that the epoch existed, and
 *  I argued that opening asks a different question from settling. It does —
 *  but the different question has a stricter answer, not a weaker one. §7.3
 *  draws exactly one edge that starts a prompt, `ready -> prompting`, so
 *  every other state either has not reached a prompt yet or is past one.
 *  `agent-quiescent` says the conversation is over; §3.3 makes `unknown` and
 *  `closed` terminal, and `closed` asserts that a terminal fact was observed
 *  for EVERY turn the epoch started — so opening one afterwards makes a
 *  durable assertion false the moment the row lands.
 *
 *  The two sets are therefore deliberately different and both are needed. A
 *  turn OPENS only from `ready` and may SETTLE anywhere the epoch has legally
 *  advanced to since, because the state moves while the agent is working and
 *  a terminal fact arriving in `cancel-requested` is exactly what §7.3
 *  describes. What I had wrong was not the distinction; it was deferring the
 *  open-time question to settle time, which is after the external prompt the
 *  check exists to protect. */
export const TURN_STARTING_SESSION_STATES = Object.freeze(["ready"]);

/** The token an allocated turn ordinal is named by.
 *
 *  Derived from the epoch and the ORDINAL the allocator claimed — never from
 *  a prompt, a timestamp, or anything the agent said. Exported so a reader
 *  can name an allocation without opening the table, not so a caller can mint
 *  one: minting is `allocateTurn`, because a token nobody allocated is a
 *  string and not an identity. */
export function turnToken(sessionRef, ordinal) {
	return `turn:${digest({
		runtimeAttemptId: sessionRef.runtimeAttemptId,
		posture: sessionRef.posture, sessionEpoch: sessionRef.sessionEpoch,
		turnOrdinal: ordinal,
	}).slice("sha256:".length)}`;
}

/** The caller's session reference, stated at the boundary that consumes it.
 *
 *  MEASURED AS MASKED, and said rather than implied: removing this leaves
 *  every malformed-reference case still refusing with the same closed pair,
 *  because the reference is a member of the frozen `turnRecord` and the
 *  record-level validation below rejects it. It is kept because the reference
 *  now reaches the IDENTITY digest and the durable body before any row is
 *  read, and a boundary whose one input shape is only implied by a schema
 *  check further down is a boundary the next reader has to reconstruct. It is
 *  not counted as a guard. */
function turnSessionRef(sessionRef) {
	// W2929 composition, 2026-08-23: THIS WAS THE SECOND COPY OF §3.1 AND IT
	// HAD ALREADY DIVERGED ONCE — it accepted an empty `providerSessionId`
	// the axis refused, so the same reference was valid here and invalid
	// there. Item 4al aligned the two texts; alignment is a state, and two
	// implementations kept in step by a regression drift again the first time
	// only one of them is edited.
	//
	// There is one now. The axis owns §3.1 because the axis is where a
	// reference is proved against the durable session, and this boundary
	// asks the same question about the same document.
	return normalizeAgentSessionRef(sessionRef);
}

/** Admit this turn into the epoch it names — the FULL durable reference, and
 *  a state a turn may still settle in.
 *
 *  Third re-review [P1]: the admission selected `state` and then used the row
 *  only for presence. A `closed` epoch accepted a new turn and sealed it, and
 *  a caller naming `provider-session-b` was sealed as accepted evidence while
 *  the durable row named `provider-session-a` — §3.1 says the reference
 *  LABELS EVIDENCE, and a label that disagrees with the record it labels is
 *  worse than none.
 *
 *  Inside the write transaction, and only for a genuinely new record. State
 *  as it is NOW cannot be allowed to decide an answer the journal already
 *  committed: a turn that settled legitimately and a session that closed
 *  afterwards are both true, and the retry is owed the first one. */
function sessionRow(db, ref) {
	const session = db.prepare(
		"SELECT state, provider_session_id FROM agent_sessions WHERE "
		+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
		.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch);
	if (session === undefined) {
		throw new ContractError("refused", "precondition",
			`no agent session ${ref.posture}/${ref.sessionEpoch} for attempt `
			+ `${ref.runtimeAttemptId}; a turn happens INSIDE one`);
	}
	return session;
}

function bindProviderSession(session, ref) {
	const stored = session.provider_session_id ?? null;
	if (stored !== ref.providerSessionId) {
		throw new ContractError("refused", "precondition",
			`this turn names provider session `
			+ `${JSON.stringify(ref.providerSessionId)} and epoch `
			+ `${ref.posture}/${ref.sessionEpoch} durably names `
			+ `${JSON.stringify(stored)}; the reference labels evidence and `
			+ `must be the one the session actually holds`);
	}
}

/** OPEN a turn here, or refuse. The exact `ready` session, and no other. */
function admitTurnStart(db, ref) {
	const session = sessionRow(db, ref);
	if (!TURN_STARTING_SESSION_STATES.includes(session.state)) {
		throw new ContractError("refused", "precondition",
			`agent session ${ref.posture}/${ref.sessionEpoch} is `
			+ `${session.state}; a turn OPENS only from `
			+ `${TURN_STARTING_SESSION_STATES.join(", ")}, because §7.3 draws `
			+ `one edge that starts a prompt and every other state is either `
			+ `before it or past it`);
	}
	bindProviderSession(session, ref);
}

/** SETTLE a turn here, or refuse. */
function admitTurnSettlement(db, ref) {
	const session = sessionRow(db, ref);
	if (!TURN_ADMITTING_SESSION_STATES.includes(session.state)) {
		throw new ContractError("refused", "precondition",
			`agent session ${ref.posture}/${ref.sessionEpoch} is `
			+ `${session.state}; a turn settles only in `
			+ `${TURN_ADMITTING_SESSION_STATES.join(", ")}, and a terminal or `
			+ `ambiguous epoch has already said what it knows`);
	}
	bindProviderSession(session, ref);
}

/** MINT one supervised turn's identity inside a session epoch.
 *
 *  This is the supervision boundary §5.1 already describes: the manager opens
 *  a turn, gives it a deadline, and only then issues the prompt. So this is
 *  where the identity belongs — before any prompt content exists to derive it
 *  from, and before anything the agent says or the manager later observes can
 *  reach it.
 *
 *  ALLOCATED, AND THE ALLOCATION IS RECORDED. Fourth re-review [P1]: a
 *  "stable identity component" that nothing allocates and no constraint
 *  bounds is data the caller may repeat. The ordinal is claimed under the
 *  write lock and the UNIQUE constraint is the backstop, exactly as the one
 *  open session per posture is decided — two managers racing on separate
 *  connections both pass any read, and only the database refuses the second.
 *
 *  It is deliberately NOT journalled. An operation journal replays an act by
 *  its identity, and allocating is how an identity comes to exist; keying it
 *  under an invented id would be inventing the thing allocation produces. A
 *  retried allocation therefore mints a fresh ordinal and the abandoned one
 *  is a GAP — visible, harmless, and honest about a turn the relay opened and
 *  did not finish. What must survive a retry is the RECORD, and it does,
 *  because the relay holds the token it was given.
 *
 *  IT ADMITS THE SESSION IT IS ABOUT TO OPEN A TURN IN. Fifth re-review
 *  [P1]: this checked only that the epoch existed, on my argument that
 *  opening and settling ask different questions and the settle question
 *  belongs at settle time. The distinction was right and the conclusion was
 *  backwards — opening asks the STRICTER question, and asking it late is
 *  asking it after the external prompt it exists to protect. §7.3 draws one
 *  edge that starts a prompt; §3.3's `closed` asserts a terminal fact for
 *  every turn the epoch started, so an allocation landing afterwards makes a
 *  durable assertion false rather than leaving a harmless gap.
 *
 *  `recordTurn` keeps its own SETTLE-state and provider checks, because the
 *  two are genuinely different: a turn opens while `ready` and settles
 *  wherever §7.3 has legally advanced to since, and an exact committed record
 *  must still replay after the session later closes. */
export function allocateTurn(store, sessionRef) {
	const ref = turnSessionRef(sessionRef);
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	try {
		// UNDER THE SAME WRITE LOCK that claims the ordinal, and BEFORE the
		// insert: a refused opening leaves nothing behind, and the state it
		// was refused on cannot move between the check and the row.
		admitTurnStart(db, ref);
		const ordinal = db.prepare(
			"SELECT COALESCE(MAX(turn_ordinal), 0) + 1 AS next FROM "
			+ "turn_allocations WHERE runtime_attempt_id = ? AND posture = ? "
			+ "AND session_epoch = ?")
			.get(ref.runtimeAttemptId, ref.posture, ref.sessionEpoch).next;
		const token = turnToken(ref, ordinal);
		db.prepare(
			"INSERT INTO turn_allocations (turn_token, runtime_attempt_id, "
			+ "posture, session_epoch, turn_ordinal, allocated_at) "
			+ "VALUES (?, ?, ?, ?, ?, ?)")
			.run(token, ref.runtimeAttemptId, ref.posture, ref.sessionEpoch,
			     ordinal, store.clock());
		db.exec("COMMIT");
		return { turnToken: token, turnOrdinal: ordinal, agentSessionRef: ref };
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
}

/** The allocation this record is being written under, or a refusal.
 *
 *  The record REFERENCES its allocation, so the token has to name one and
 *  that one has to belong to the epoch the turn claims. A token allocated in
 *  another epoch is not this turn's identity however well formed it is, and
 *  the foreign key alone would only say the string exists somewhere. */
function bindAllocation(db, ref, token) {
	const row = db.prepare(
		"SELECT runtime_attempt_id, posture, session_epoch, turn_ordinal "
		+ "FROM turn_allocations WHERE turn_token = ?").get(token);
	if (row === undefined) {
		throw new ContractError("refused", "precondition",
			`${token} names no allocated turn; the supervision boundary mints `
			+ `a turn identity and a record is written under one`);
	}
	if (row.runtime_attempt_id !== ref.runtimeAttemptId
			|| row.posture !== ref.posture
			|| row.session_epoch !== ref.sessionEpoch) {
		throw new ContractError("refused", "precondition",
			`${token} is allocated to ${row.posture}/${row.session_epoch} of `
			+ `attempt ${row.runtime_attempt_id} and this turn claims `
			+ `${ref.posture}/${ref.sessionEpoch} of ${ref.runtimeAttemptId}`);
	}
	return row;
}

/** Record one turn: build the frozen document, validate it, seal it, and
 *  commit it through the manager's operation journal.
 *
 *  SHAPE BEFORE SEMANTICS, because three nonempty strings are not a timestamp
 *  and a digest, and later semantic code cannot stand in for shape proof.
 *  THE DECIDING EVIDENCE IS RETAINED, because a durable outcome whose policy
 *  failure vanished is not the record that outcome came from. THE ACT IS
 *  JOURNALLED, because a deterministic identity with a plain insert answers a
 *  repeat with a raw UNIQUE violation instead of the committed result. And
 *  THE ANSWER IS THE JOURNAL'S, so the first caller and every retry receive
 *  the same owned bytes rather than a view onto the caller's own object. */
export function recordTurn(store, { turnToken: token, sessionRef,
                                    promptDigest, startedAt,
                                    deadlineAt, endedAt, terminalFact = null,
                                    policyFailures = [], transportLost = false,
                                    eventCount = 0, lateEventCount = 0,
                                    droppedEventCount = 0,
                                    droppedEventBytes = 0, evidence = [],
                                    adapterDiagnostics = {} }) {
	const ref = turnSessionRef(sessionRef);
	if (typeof token !== "string" || token.length === 0) {
		throw new ContractError("integrity", "schema",
			`${nameValue(token)} is not a turn token; a record `
			+ `is written under an identity the supervision boundary minted`);
	}
	// EVERY POLICY FAILURE IS A FROZEN DOCUMENT, validated before it decides
	// anything and RETAINED with the turn it decided.
	// Per failure, so the refusal names WHICH one. Measured: the record-level
	// validation below covers this too, so removing only this leaves the
	// malformed case still caught — both must go for it to pass. It is kept
	// for the index in the message, not counted as a guard.
	requirePolicyFailureList(policyFailures);
	const failures = policyFailures.map((failure, at) => {
		// SHAPE BEFORE THE COPY. Fourth re-review [P2]: `structuredClone`
		// ran first and a function element left as a raw `DataCloneError`.
		// A frozen policyFailure is a JSON object, and asking that BEFORE
		// copying costs one `typeof` and closes the whole class — the clone
		// is here to stop a caller mutating what was validated, not to
		// discover what kind of value it was handed.
		if (typeof failure !== "object" || failure === null
				|| Array.isArray(failure)) {
			throw new ContractError("integrity", "schema",
				`policy failure ${at} is ${failure === null ? "null"
					: Array.isArray(failure) ? "an array" : typeof failure}; `
				+ `a frozen policyFailure is a document`);
		}
		// And the residue: a plain object may still carry an interior no
		// structured clone can own. That is the same closed pair, not
		// whichever error the algorithm reached.
		let owned;
		try {
			owned = structuredClone(failure);
		} catch (unclonable) {
			throw new ContractError("integrity", "schema",
				`policy failure ${at} cannot be owned by this boundary `
				+ `(${unclonable.message}); a frozen policyFailure carries `
				+ `only durable JSON members`);
		}
		if (!_validatePolicyFailure(owned)) {
			const first = _validatePolicyFailure.errors?.[0];
			throw new ContractError("integrity", "schema",
				`policy failure ${at} is not a frozen policyFailure: `
				+ `${first?.instancePath || "/"} `
				+ `${first?.message ?? "refused"}`);
		}
		return owned;
	});
	// Copied — and MEASURED as equivalent, which is worth saying rather than
	// implying: `store.transact` returns the byte-stable JSON it committed,
	// so the answer is already owned, and the row is written from these
	// members inside the transaction before any caller could touch them. The
	// clone is kept because a boundary that reads a caller's object twice is
	// how a check and an act come to disagree, but THE JOURNAL is what makes
	// the answer owned, not this line.
	const fact = terminalFact === null
		? { kind: "none", value: null } : structuredClone(terminalFact);
	const outcome = selectTurnOutcome({ terminalFact: fact,
		policyFailures: failures, transportLost,
		deadlineElapsed: endedAt >= deadlineAt });
	// THE IDENTITY IS THE ALLOCATION. Nothing is derived here any more.
	const id = token;
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "turn",
		turn_id: id,
		agent_session_ref: {
			runtime_attempt_id: ref.runtimeAttemptId,
			posture: ref.posture,
			session_epoch: ref.sessionEpoch,
			provider_session_id: ref.providerSessionId,
		},
		started_at: startedAt,
		ended_at: endedAt,
		deadline_at: deadlineAt,
		prompt_digest: promptDigest,
		outcome,
		terminal_fact: fact,
		conclusive: CONCLUSIVE[outcome],
		permitted_dispositions: [...PERMITTED_DISPOSITIONS[outcome]],
		event_count: eventCount,
		late_event_count: lateEventCount,
		dropped_event_count: droppedEventCount,
		dropped_event_bytes: droppedEventBytes,
		policy_failures: failures,
		evidence: structuredClone(evidence),
		adapter_diagnostics: structuredClone(adapterDiagnostics),
	};
	const sealed = digest(body);
	const document = { ...body, document_digest: sealed };
	if (!_validateTurn(document)) {
		const first = _validateTurn.errors?.[0];
		throw new ContractError("integrity", "schema",
			`this turn is not a valid baton.agent-session 1.0 turn record: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	const signature = digest({ kind: "agent.turn",
	                           operands: { turnId: id, sealed } });
	// FIXED IDENTITY AND SIGNATURE FIRST, then everything that reads state as
	// it is NOW. `store.transact` resolves the journal before it runs this,
	// so an exact retry replays and a changed one collides without either
	// check below being consulted — which is the point of both moves.
	return store.transact(id, "agent.turn", signature, (db) => {
		// THE ALLOCATION IS THE IDENTITY, so it is bound before anything
		// else: an unallocated or foreign token is not this turn.
		bindAllocation(db, ref, id);
		admitTurnSettlement(db, ref);
		// THE WHOLE DOCUMENT, before anything can be written. Review [P1]: the
		// journal scans the RESULT it commits, and that summary omits
		// `evidence` and `adapter_diagnostics` — so a live bearer under an
		// innocently named diagnostic landed in `turns.body` while the journal
		// committed a clean summary. A scan over a projection is a scan over
		// the projection.
		//
		// Third re-review [P1]: and the scan is over the EPHEMERAL registry as
		// it stands right now, so it belongs to a new write and to nothing
		// else. Run before the journal, it let ordinary durable text that was
		// benign when committed become a bearer later and start refusing an
		// exact replay — writing nothing, returning no bearer-bearing field,
		// and hiding an immutable answer whose bytes had not changed. A new
		// write still refuses.
		assertNoDurableSecret(document, `turn ${id}`);
		db.prepare(
			"INSERT INTO turns (turn_id, runtime_attempt_id, posture, "
			+ "session_epoch, prompt_digest, started_at, deadline_at, "
			+ "ended_at, outcome, terminal_kind, terminal_value, conclusive, "
			+ "permitted, event_count, late_event_count, "
			+ "dropped_event_count, dropped_event_bytes, policy_failures, "
			+ "body, document_digest, recorded_at) VALUES (?, ?, ?, ?, ?, ?, "
			+ "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(id, ref.runtimeAttemptId, ref.posture, ref.sessionEpoch,
			     promptDigest, startedAt, deadlineAt, endedAt, outcome,
			     fact.kind, fact.value,
			     CONCLUSIVE[outcome] ? 1 : 0,
			     JSON.stringify(PERMITTED_DISPOSITIONS[outcome]), eventCount,
			     lateEventCount, droppedEventCount, droppedEventBytes,
			     JSON.stringify(failures),
			     canonicalBytes(document).toString("utf8"), sealed,
			     store.clock());
		return { turnId: id, outcome, conclusive: CONCLUSIVE[outcome],
		         permittedDispositions: [...PERMITTED_DISPOSITIONS[outcome]],
		         terminalFact: fact, policyFailures: failures,
		         documentDigest: sealed };
	});
}

/** The retained turn document for an identity, or null.
 *
 *  Parsed fresh and re-bound to the digest it was sealed under — the rule the
 *  retained profiles and manifests already carry, applied here rather than
 *  waited for. */
export function turnRecordOf(store, id) {
	// W2929 composition revalidation: THE IDENTIFIER IS PROVED BEFORE IT
	// REACHES THE STATEMENT. Measured — an unproved id bound straight into
	// the query, so an object operand left as SQLite's own binding error and
	// a trapping Proxy left as an arbitrary Error of the caller's choosing.
	// A well-formed token naming no turn still answers null: absence and
	// refusal are different answers to different questions.
	// Review [P1]: this proved "nonempty string", which is one third of the
	// frozen rule. `$defs.turnRecord.turn_id` is `$ref: opaqueId`, so a
	// string with a space in it or a 161-character one is not a turn token —
	// and answering `null` to it reported ABSENCE for a question that was
	// never asked, which is the very separation item 4ak claimed to make.
	const fault = opaqueIdFault(id);
	if (fault !== null) {
		throw new ContractError("integrity", "schema",
			`a turn token ${fault}; an operand is proved before it reaches `
			+ `the store, and a malformed identity is not an absence`);
	}
	const row = store.db.prepare(
		"SELECT body, document_digest FROM turns WHERE turn_id = ?").get(id);
	if (row === undefined) return null;
	// Fourth re-review [P2]: this parsed outside any integrity wrapper, so
	// unparsable retained bytes left as a raw `SyntaxError` while malformed
	// bytes in the SUMMARY of the same safety path already reported the
	// closed pair. Retained record bytes that cannot be parsed have failed
	// the seal as surely as bytes that parse and disagree with it.
	let owned;
	try {
		owned = JSON.parse(row.body);
	} catch (failure) {
		throw new ContractError("integrity", "digest",
			`the retained turn under ${id} is not parsable `
			+ `(${failure.message}); bytes that cannot be read cannot be `
			+ `bound to the digest they were sealed under`);
	}
	// SHAPE, THEN THE FOUR WITNESSES. The declared digest, the recomputed
	// canonical digest, the stored digest and the identity the caller ASKED
	// FOR are one fact — the profile and manifest loaders already bind the
	// first three, and a record answering to somebody else's turn id is the
	// fourth way the same question can be got wrong.
	//
	// MEASURED: the shape check here is INERT given the write-side validation
	// and the seal — bytes that changed would fail the digest first, and a
	// malformed record could never have been written. It is kept because a
	// loader that trusts what it parses is the shape this Work has corrected
	// twice, and it is not counted as a guard.
	if (!_validateTurn(owned)) {
		const first = _validateTurn.errors?.[0];
		throw new ContractError("integrity", "schema",
			`the retained turn under ${id} is not a valid turn record: `
			+ `${first?.instancePath || "/"} ${first?.message ?? "refused"}`);
	}
	const { document_digest: declared, ...rest } = owned;
	const recomputed = digest(rest);
	if (recomputed !== row.document_digest
			|| declared !== row.document_digest) {
		throw new ContractError("integrity", "digest",
			`turn ${id} is sealed under ${row.document_digest}, declares `
			+ `${declared} and recomputes to ${recomputed}`);
	}
	if (owned.turn_id !== id) {
		throw new ContractError("integrity", "digest",
			`the record filed under ${id} calls itself ${owned.turn_id}`);
	}
	return owned;
}

/** Whether this turn's outcome permits the worker's declared disposition.
 *
 *  GATES, NEVER CHOOSES. */
export function permitsDisposition(store, id, disposition) {
	// THE SAFETY DECISION READS THE SEALED RECORD. Review [P1]: this read the
	// unsealed `permitted` summary column, so editing that one column made
	// the manager accept `completed` from a refused turn while the retained
	// record still forbade it. A seal that the consumer it exists for does
	// not consult protects nobody.
	const record = turnRecordOf(store, id);
	if (record === null) {
		throw new ContractError("refused", "precondition",
			`no turn ${id}; a disposition is gated by the turn that preceded `
			+ `it`);
	}
	// AND THE SUMMARY MUST AGREE WITH IT. A query column that has drifted
	// from the canonical record is an integrity failure wherever it is found,
	// not something to quietly prefer the sealed side of: the next reader may
	// be one that only has the column.
	const row = store.db.prepare(
		"SELECT permitted, outcome, conclusive FROM turns WHERE turn_id = ?")
		.get(id);
	// Third re-review [P2]: the summary was parsed OUTSIDE any integrity
	// wrapper, so retained bytes that are not JSON at all left as a raw
	// `SyntaxError`. A summary that cannot even be compared with the sealed
	// record has already diverged from it, which is the same integrity
	// failure a comparable-but-different summary reports — so it reports as
	// that, and not as whichever error the parser reached first.
	let permitted;
	try {
		permitted = JSON.parse(row.permitted);
	} catch (failure) {
		throw new ContractError("integrity", "digest",
			`turn ${id} retains a gate summary that is not JSON `
			+ `(${failure.message}); it cannot be compared with the sealed `
			+ `record, and a summary that cannot be compared has already `
			+ `drifted from it`);
	}
	const summary = { permitted, outcome: row.outcome,
	                  conclusive: row.conclusive === 1 };
	const sealed = { permitted: record.permitted_dispositions,
	                 outcome: record.outcome, conclusive: record.conclusive };
	if (digest(summary) !== digest(sealed)) {
		throw new ContractError("integrity", "digest",
			`turn ${id} summarizes ${JSON.stringify(summary)} and its sealed `
			+ `record says ${JSON.stringify(sealed)}`);
	}
	// From the SEALED record. Measured: with the comparison above passing,
	// reading the column instead is equivalent — the comparison is what
	// decides, and this line only makes the source of the answer obvious.
	return record.permitted_dispositions.includes(disposition);
}
