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

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { assertNoDurableSecret, canonicalBytes, ContractError, digest }
	from "./contracts.mjs";

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
	// Review [P1]: any array-like with a nonzero `length` selected
	// `policy-failed`. A count is not a policy failure.
	if (!Array.isArray(policyFailures)) {
		throw new ContractError("integrity", "schema",
			"policy failures are a list of frozen policyFailure documents; "
			+ "a value that merely has a length is not one");
	}
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

/** The ONE turn identity, derived from the session epoch and the prompt. */
export function turnId(sessionRef, promptDigest) {
	return `turn:${digest({
		runtimeAttemptId: sessionRef.runtimeAttemptId,
		posture: sessionRef.posture, sessionEpoch: sessionRef.sessionEpoch,
		promptDigest,
	}).slice("sha256:".length)}`;
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
export function recordTurn(store, { sessionRef, promptDigest, startedAt,
                                    deadlineAt, endedAt, terminalFact = null,
                                    policyFailures = [], transportLost = false,
                                    eventCount = 0, lateEventCount = 0,
                                    droppedEventCount = 0,
                                    droppedEventBytes = 0, evidence = [],
                                    adapterDiagnostics = {} }) {
	const session = store.db.prepare(
		"SELECT state FROM agent_sessions WHERE runtime_attempt_id = ? "
		+ "AND posture = ? AND session_epoch = ?")
		.get(sessionRef?.runtimeAttemptId, sessionRef?.posture,
		     sessionRef?.sessionEpoch);
	if (session === undefined) {
		throw new ContractError("refused", "precondition",
			`no agent session ${sessionRef?.posture}/`
			+ `${sessionRef?.sessionEpoch} for attempt `
			+ `${sessionRef?.runtimeAttemptId}; a turn happens INSIDE one`);
	}
	// EVERY POLICY FAILURE IS A FROZEN DOCUMENT, validated before it decides
	// anything and RETAINED with the turn it decided.
	// Per failure, so the refusal names WHICH one. Measured: the record-level
	// validation below covers this too, so removing only this leaves the
	// malformed case still caught — both must go for it to pass. It is kept
	// for the index in the message, not counted as a guard.
	const failures = policyFailures.map((failure, at) => {
		const owned = structuredClone(failure);
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
	const id = turnId(sessionRef, promptDigest);
	const body = {
		session_family: "baton.agent-session",
		version: { major: 1, minor: 0 },
		document: "turn",
		turn_id: id,
		agent_session_ref: {
			runtime_attempt_id: sessionRef.runtimeAttemptId,
			posture: sessionRef.posture,
			session_epoch: sessionRef.sessionEpoch,
			provider_session_id: sessionRef.providerSessionId ?? null,
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
	// THE WHOLE DOCUMENT, before anything can be written. Review [P1]: the
	// journal scans the RESULT it commits, and that summary omits `evidence`
	// and `adapter_diagnostics` — so a live bearer under an innocently named
	// diagnostic landed in `turns.body` while the journal committed a clean
	// summary. A scan over a projection is a scan over the projection.
	assertNoDurableSecret(document, `turn ${id}`);
	const signature = digest({ kind: "agent.turn",
	                           operands: { turnId: id, sealed } });
	return store.transact(id, "agent.turn", signature, (db) => {
		db.prepare(
			"INSERT INTO turns (turn_id, runtime_attempt_id, posture, "
			+ "session_epoch, prompt_digest, started_at, deadline_at, "
			+ "ended_at, outcome, terminal_kind, terminal_value, conclusive, "
			+ "permitted, event_count, late_event_count, "
			+ "dropped_event_count, dropped_event_bytes, policy_failures, "
			+ "body, document_digest, recorded_at) VALUES (?, ?, ?, ?, ?, ?, "
			+ "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(id, sessionRef.runtimeAttemptId, sessionRef.posture,
			     sessionRef.sessionEpoch, promptDigest, startedAt, deadlineAt,
			     endedAt, outcome, fact.kind, fact.value,
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
	const row = store.db.prepare(
		"SELECT body, document_digest FROM turns WHERE turn_id = ?").get(id);
	if (row === undefined) return null;
	const owned = JSON.parse(row.body);
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
	const summary = { permitted: JSON.parse(row.permitted),
	                  outcome: row.outcome,
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
