// W2929 item 4, third slice: the turn and its outcome.
//
// The contract spends a whole section on what an outcome is NOT derived from
// — silence, transport closure, an empty update stream, a tool call's own
// status, agent prose, reachability at any layer — so most of these cases are
// about refusing to name one, and the tables are driven EXHAUSTIVELY rather
// than sampled: a closed vocabulary tested at three of eight points is a
// closed vocabulary nobody has checked.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, GOLDEN_BEARER, digest }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { ACP_STOP_REASONS, CODEX_ERROR_INFO, CODEX_TURN_STATUSES, CONCLUSIVE,
         PERMITTED_DISPOSITIONS, TURN_OUTCOMES, fromTerminalFact,
         permitsDisposition, recordTurn, selectTurnOutcome, turnId,
         turnRecordOf }
	from "../src/worker_manager/agent_turn.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const STARTED = "2026-08-22T12:00:00.000Z";
const DEADLINE = "2026-08-22T12:15:00.000Z";
const ENDED = "2026-08-22T12:01:00.000Z";
const REF = { runtimeAttemptId: ATTEMPT, posture: "execution",
              sessionEpoch: 1 };
const PROMPT = digest("prompt");

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

/** An attempt with one open execution session — written directly, because the
 *  opening path has its own suite and driving it here would test it twice. */
function withSession(store) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile") });
	store.db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, state, opened_at) "
		+ "VALUES (?, 'execution', 1, ?, ?, ?, ?, 'ready', ?)")
		.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID, NOW);
	return REF;
}

function ended(store, extra = {}) {
	return recordTurn(store, { sessionRef: REF, promptDigest: PROMPT,
		startedAt: STARTED, deadlineAt: DEADLINE, endedAt: ENDED, ...extra });
}

// -- the closed vocabulary and its two tables -------------------------------

test("W2929: every outcome has a gate and a conclusiveness, and only those", () => {
	assert.deepEqual(Object.keys(PERMITTED_DISPOSITIONS).sort(),
		[...TURN_OUTCOMES].sort(), "an outcome has no permitted set");
	assert.deepEqual(Object.keys(CONCLUSIVE).sort(), [...TURN_OUTCOMES].sort(),
		"an outcome has no conclusiveness");
	// The acceptance table, verbatim, all eight rows.
	assert.deepEqual(PERMITTED_DISPOSITIONS, {
		completed: ["completed", "unable", "plan-rejected"],
		refused: ["unable"],
		truncated: ["unable"],
		"agent-failed": ["unable"],
		cancelled: [],
		"policy-failed": [],
		timeout: [],
		"transport-lost": [],
	});
	// The two honest ones say the relay does not know.
	assert.deepEqual(TURN_OUTCOMES.filter((o) => !CONCLUSIVE[o]),
		["timeout", "transport-lost"]);
});

test("W2929: ACP stop reasons map EXACTLY, and nothing else maps", () => {
	assert.deepEqual(ACP_STOP_REASONS, {
		end_turn: "completed", refusal: "refused", max_tokens: "truncated",
		max_turn_requests: "truncated", cancelled: "cancelled",
	});
	for (const [reason, outcome] of Object.entries(ACP_STOP_REASONS)) {
		assert.equal(selectTurnOutcome({
			terminalFact: { kind: "acp-stop-reason", value: reason } }),
			outcome, reason);
	}
	for (const unknown of ["end-turn", "END_TURN", "stopped", ""]) {
		assert.throws(() => selectTurnOutcome({
			terminalFact: { kind: "acp-stop-reason", value: unknown } }),
			(error) => error instanceof ContractError, unknown);
	}
});

test("W2929: the THREE codex statuses map exactly, and nothing else", () => {
	// Review [P1]: I had two and asserted that `failed` must be REFUSED,
	// contradicting a table the boundary had already frozen. A vocabulary I
	// shortened is not a stricter vocabulary; it is a different one, and the
	// difference was invisible because I also wrote the test.
	assert.deepEqual(CODEX_TURN_STATUSES, { completed: "completed",
		interrupted: "cancelled", failed: "agent-failed" });
	for (const [status, outcome] of Object.entries(CODEX_TURN_STATUSES)) {
		assert.equal(selectTurnOutcome({
			terminalFact: { kind: "codex-turn-status", value: status } }),
			outcome, status);
	}
	for (const unknown of ["errored", "FAILED", ""]) {
		assert.throws(() => selectTurnOutcome({
			terminalFact: { kind: "codex-turn-status", value: unknown } }),
			(error) => error instanceof ContractError, unknown);
	}
});

test("W2929: §10.6 maps every certified codexErrorInfo, EXHAUSTIVELY", () => {
	// Eleven rows, each with an outcome AND a closed error pair. Sampling
	// three of eleven would leave eight untested and the table looking driven.
	assert.deepEqual(Object.fromEntries(Object.entries(CODEX_ERROR_INFO)
		.map(([value, row]) => [value, row.outcome])), {
		ContextWindowExceeded: "truncated",
		UsageLimitExceeded: "agent-failed",
		HttpConnectionFailed: "agent-failed",
		ResponseStreamConnectionFailed: "agent-failed",
		ResponseStreamDisconnected: "agent-failed",
		ResponseTooManyFailedAttempts: "agent-failed",
		Unauthorized: "agent-failed",
		SandboxError: "agent-failed",
		BadRequest: "agent-failed",
		InternalServerError: "agent-failed",
		Other: "agent-failed",
	});
	for (const [value, row] of Object.entries(CODEX_ERROR_INFO)) {
		const seen = fromTerminalFact({ kind: "codex-error-info", value });
		assert.equal(seen.outcome, row.outcome, value);
		assert.deepEqual(seen.reported, row.reported, value);
	}
	// The transport rows report differently from the provider rows, which is
	// the whole reason the table carries a pair rather than an outcome.
	assert.deepEqual(CODEX_ERROR_INFO.Unauthorized.reported,
		{ category: "policy", code: "denied" });
	assert.deepEqual(CODEX_ERROR_INFO.HttpConnectionFailed.reported,
		{ category: "unavailable", code: "transport" });
});

test("W2929 review: a failed Codex turn is an agent failure", () => {
	assert.equal(selectTurnOutcome({
		terminalFact: { kind: "codex-turn-status", value: "failed" } }),
		"agent-failed");
});

test("W2929 review: Codex error info refines the failed outcome exactly", () => {
	assert.equal(selectTurnOutcome({
		terminalFact: { kind: "codex-error-info",
			value: "ContextWindowExceeded" } }), "truncated");
	assert.equal(selectTurnOutcome({
		terminalFact: { kind: "codex-error-info",
			value: "UsageLimitExceeded" } }), "agent-failed");
	// THE ONE PLACE I HAVE NOT DONE WHAT THIS CASE ASKED. §10.6 ends: "the
	// raw `codexErrorInfo` string is retained as untrusted diagnostics; it
	// selects nothing beyond this table, and AN UNRECOGNIZED VALUE TAKES THE
	// LAST ROW." Refusing would be stricter and would contradict a decision
	// the boundary already froze, so the implementation follows the frozen
	// sentence and the disagreement is raised on the handoff instead.
	assert.deepEqual(fromTerminalFact({ kind: "codex-error-info",
		value: "boom" }), { outcome: "agent-failed",
		reported: { category: "unavailable", code: "source-provider" } });
});

// -- never inferred ---------------------------------------------------------

test("W2929: with no evidence at all, NO OUTCOME IS NAMED", () => {
	// Silence is not completion. An empty update stream is not completion.
	// Neither is agent prose, a tool call's own status, or reachability.
	assert.throws(() => selectTurnOutcome({}),
		(error) => error instanceof ContractError
			&& error.category === "integrity" && error.code === "schema");
	assert.throws(() => selectTurnOutcome({
		terminalFact: { kind: "none", value: null }, eventCount: 400 }),
		(error) => error instanceof ContractError);
});

test("W2929: a turn ending BEFORE its deadline with nothing is refused", () => {
	const store = open();
	try {
		withSession(store);
		assert.throws(() => ended(store),
			(error) => error instanceof ContractError);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: the deadline, transport death and a policy failure each name one",
	() => {
		assert.equal(selectTurnOutcome({ deadlineElapsed: true }), "timeout");
		assert.equal(selectTurnOutcome({ transportLost: true }),
			"transport-lost");
		assert.equal(selectTurnOutcome({ policyFailures: [
			{ condition: "unexpected-approval", granted: false }] }),
			"policy-failed");
		// The selector counts; `recordTurn` is where each one must BE a frozen
		// policyFailure, because that is where it becomes durable.
	});

test("W2929: the ORDER of precedence is the argument", () => {
	// A policy failure ends the turn where it happens, so it outranks
	// anything that arrives afterwards — including a terminal fact.
	assert.equal(selectTurnOutcome({
		terminalFact: { kind: "acp-stop-reason", value: "end_turn" },
		policyFailures: [{ condition: "unexpected-approval", granted: false }],
		transportLost: true, deadlineElapsed: true }), "policy-failed");
	// A terminal fact ARRIVED, so it outranks a deadline that also elapsed.
	assert.equal(selectTurnOutcome({
		terminalFact: { kind: "acp-stop-reason", value: "end_turn" },
		deadlineElapsed: true }), "completed");
	// The epoch being gone is more than "nothing has come back yet".
	assert.equal(selectTurnOutcome({ transportLost: true,
		deadlineElapsed: true }), "transport-lost");
});

// -- gates, never chooses ---------------------------------------------------

test("W2929: the outcome GATES the disposition and never chooses it", () => {
	const store = open();
	try {
		withSession(store);
		const turn = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "refusal" } });
		assert.equal(turn.outcome, "refused");
		// A refusal accepts only `unable` — and it does not DECLARE `unable`.
		assert.deepEqual(turn.permittedDispositions, ["unable"]);
		assert.equal(permitsDisposition(store, turn.turnId, "unable"), true);
		assert.equal(permitsDisposition(store, turn.turnId, "completed"), false);
		assert.equal(permitsDisposition(store, turn.turnId, "plan-rejected"),
			false);
	} finally {
		store.close();
	}
});

test("W2929: the ambiguous and ended outcomes permit NOTHING", () => {
	const store = open();
	try {
		withSession(store);
		for (const [what, extra] of [
				["timeout", { endedAt: "2026-08-22T12:20:00.000Z" }],
				["transport-lost", { transportLost: true }],
				["cancelled", { terminalFact: { kind: "acp-stop-reason",
				                                value: "cancelled" } }],
				["policy-failed", { policyFailures: [{
					condition: "unexpected-approval",
					error: { category: "policy", code: "denied" },
					observed_at: ENDED, granted: false }] }]]) {
			const turn = ended(store, { ...extra,
				promptDigest: digest(what) });
			assert.equal(turn.outcome, what);
			assert.deepEqual(turn.permittedDispositions, [], what);
			for (const d of ["completed", "unable", "plan-rejected"]) {
				assert.equal(permitsDisposition(store, turn.turnId, d), false,
					`${what}/${d}`);
			}
		}
	} finally {
		store.close();
	}
});

test("W2929: a stored gate is what a later reader sees", () => {
	const store = open();
	try {
		withSession(store);
		const turn = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
		assert.equal(store.db.prepare(
			"SELECT permitted FROM turns WHERE turn_id = ?")
			.get(turn.turnId).permitted,
			JSON.stringify(["completed", "unable", "plan-rejected"]),
			"the gate applied was not recorded beside the turn");
		assert.equal(store.db.prepare(
			"SELECT conclusive FROM turns WHERE turn_id = ?")
			.get(turn.turnId).conclusive, 1);
	} finally {
		store.close();
	}
});

// -- every turn has a deadline ----------------------------------------------

test("W2929: EVERY turn has a manager deadline", () => {
	const store = open();
	try {
		withSession(store);
		for (const missing of ["startedAt", "deadlineAt", "endedAt"]) {
			assert.throws(() => recordTurn(store, {
				sessionRef: REF, promptDigest: PROMPT, startedAt: STARTED,
				deadlineAt: DEADLINE, endedAt: ENDED, [missing]: null,
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError
					&& error.category === "integrity", missing);
		}
	} finally {
		store.close();
	}
});

test("W2929 review: a durable turn passes the frozen record shape", () => {
	const store = open();
	try {
		withSession(store);
		assert.throws(() => recordTurn(store, {
			sessionRef: REF, promptDigest: "not-a-digest",
			startedAt: STARTED, deadlineAt: "not-a-timestamp", endedAt: ENDED,
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: recording a turn is replay-safe and collision-safe", () => {
	const store = open();
	try {
		withSession(store);
		const terminalFact = { kind: "acp-stop-reason", value: "end_turn" };
		const first = ended(store, { terminalFact });
		assert.deepEqual(ended(store, { terminalFact }), first,
			"an exact retry did not replay the committed turn");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 1);
		assert.throws(() => ended(store, { terminalFact:
			{ kind: "acp-stop-reason", value: "refusal" } }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "operation-collision");
	} finally {
		store.close();
	}
});

test("W2929 review: the first turn answer is not the caller's alias", () => {
	const store = open();
	try {
		withSession(store);
		const terminalFact = { kind: "acp-stop-reason", value: "end_turn" };
		const answer = ended(store, { terminalFact });
		terminalFact.kind = "relay-policy";
		terminalFact.value = "unexpected-approval";
		assert.deepEqual(answer.terminalFact,
			{ kind: "acp-stop-reason", value: "end_turn" });
	} finally {
		store.close();
	}
});

test("W2929 review: a policy-failed turn retains the exact failure", () => {
	const store = open();
	try {
		withSession(store);
		const failure = { condition: "unexpected-approval",
			error: { category: "policy", code: "denied" },
			observed_at: ENDED, granted: false };
		ended(store, { policyFailures: [failure] });
		const row = store.db.prepare("SELECT * FROM turns").get();
		assert.deepEqual(JSON.parse(row.policy_failures), [failure],
			"the durable turn lost the policy evidence that selected its outcome");
	} finally {
		store.close();
	}
});

test("W2929: a turn happens INSIDE a session", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.throws(() => ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

test("W2929: the turn identity is derived from its epoch and prompt", () => {
	const first = turnId(REF, PROMPT);
	assert.equal(turnId({ ...REF, sessionEpoch: 2 }, PROMPT) === first, false);
	assert.equal(turnId({ ...REF, posture: "consent" }, PROMPT) === first,
		false);
	assert.equal(turnId(REF, digest("other")) === first, false);
	assert.equal(turnId({ ...REF }, PROMPT), first);
});

// -- the record is the record ------------------------------------------------

test("W2929: a malformed timestamp or digest is refused by the SHAPE", () => {
	const store = open();
	try {
		withSession(store);
		for (const [what, extra] of [
				["deadline", { deadlineAt: "not-a-timestamp" }],
				["started", { startedAt: "tomorrow" }],
				["prompt", { promptDigest: "not-a-digest" }]]) {
			assert.throws(() => ended(store, { ...extra,
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: a malformed policy failure decides nothing", () => {
	const store = open();
	try {
		withSession(store);
		for (const [what, failure] of [
				["no error pair", { condition: "unexpected-approval",
					observed_at: ENDED, granted: false }],
				["granted", { condition: "unexpected-approval",
					error: { category: "policy", code: "denied" },
					observed_at: ENDED, granted: true }],
				["unknown condition", { condition: "invented",
					error: { category: "policy", code: "denied" },
					observed_at: ENDED, granted: false }],
				["cross-category code", { condition: "unexpected-approval",
					error: { category: "policy", code: "schema" },
					observed_at: ENDED, granted: false }]]) {
			assert.throws(() => ended(store, { policyFailures: [failure] }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: negative counts are refused", () => {
	const store = open();
	try {
		withSession(store);
		for (const field of ["eventCount", "lateEventCount",
		                     "droppedEventCount", "droppedEventBytes"]) {
			assert.throws(() => ended(store, { [field]: -1,
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError, field);
		}
	} finally {
		store.close();
	}
});

test("W2929: an exact repeat REPLAYS and a changed one COLLIDES", () => {
	const store = open();
	try {
		withSession(store);
		const fact = { kind: "acp-stop-reason", value: "end_turn" };
		const first = ended(store, { terminalFact: fact });
		// The identity is deterministic, so a plain insert would have answered
		// a repeat with a raw UNIQUE violation instead of the committed result.
		assert.deepEqual(ended(store, { terminalFact: { ...fact } }), first,
			"the repeat was re-derived rather than replayed");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 1);
		assert.throws(() => ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "refusal" } }),
			(error) => error instanceof ContractError
				&& error.code === "operation-collision");
		assert.equal(store.db.prepare(
			"SELECT outcome FROM turns").get().outcome, "completed");
	} finally {
		store.close();
	}
});

test("W2929: the answer is the JOURNAL'S, not a view on the caller", () => {
	const store = open();
	try {
		withSession(store);
		const fact = { kind: "acp-stop-reason", value: "end_turn" };
		const answer = ended(store, { terminalFact: fact });
		// Mutating the caller's object afterwards must not rewrite an answer
		// that has already been given.
		fact.kind = "relay-policy";
		fact.value = "unexpected-approval";
		assert.deepEqual(answer.terminalFact,
			{ kind: "acp-stop-reason", value: "end_turn" });
		assert.deepEqual(turnRecordOf(store, answer.turnId).terminal_fact,
			{ kind: "acp-stop-reason", value: "end_turn" });
	} finally {
		store.close();
	}
});

test("W2929: the sealed turn survives, byte for byte, and re-binds", () => {
	const store = open();
	try {
		withSession(store);
		const answer = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" },
			evidence: [], adapterDiagnostics: { "baton.relay/1": { note: "x" } },
			droppedEventBytes: 12 });
		const record = turnRecordOf(store, answer.turnId);
		assert.equal(record.document_digest, answer.documentDigest);
		assert.deepEqual(record.adapter_diagnostics,
			{ "baton.relay/1": { note: "x" } });
		assert.equal(record.dropped_event_bytes, 12);
		// And a hand edit is caught on the way out, as it is for profiles and
		// manifests.
		store.db.prepare("UPDATE turns SET body = ? WHERE turn_id = ?")
			.run(JSON.stringify({ ...record, event_count: 99 }), answer.turnId);
		assert.throws(() => turnRecordOf(store, answer.turnId),
			(error) => error instanceof ContractError
				&& error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929 re-review: the stored gate cannot bypass the sealed turn", () => {
	const store = open();
	try {
		withSession(store);
		const turn = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "refusal" } });
		// The frozen body permits only `unable`. The query summary is useful,
		// but it is not independently trusted: changing it must never make a
		// disposition the sealed record forbids become acceptable.
		store.db.prepare("UPDATE turns SET permitted = ? WHERE turn_id = ?")
			.run(JSON.stringify(["completed", "unable"]), turn.turnId);
		assert.throws(() => permitsDisposition(store, turn.turnId, "completed"),
			(error) => error instanceof ContractError
				&& error.category === "integrity",
			"the disposition gate trusted an unsealed summary column");
	} finally {
		store.close();
	}
});

test("W2929 re-review: a turn record cannot retain a live bearer", () => {
	const store = open();
	try {
		withSession(store);
		assert.throws(() => ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" },
			adapterDiagnostics: { "baton.relay/1": {
				diagnostic: `provider said ${GOLDEN_BEARER}` } } }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "secret-leak");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
		// Scoped to THIS turn's operation. The table is not empty — the
		// fixture's `recordAttempt` journals `attempt.record:attempt-1`
		// before any turn exists — and the claim being made is that the
		// refused turn journalled nothing, not that nothing ever did.
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM operations WHERE kind = 'agent.turn'")
			.get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: a bearer ANYWHERE in the turn is refused", () => {
	const store = open();
	try {
		withSession(store);
		// The review drove a diagnostic. These drive the other members the
		// journal's summary also omits — because the finding is that a scan
		// over a projection is a scan over the projection, and `evidence` is
		// as absent from that projection as diagnostics were.
		for (const [what, extra] of [
				["evidence locator", { evidence: [{ purpose: "log",
					artifact: { artifact_id: "a1",
						media_type: "text/plain", bytes: 4,
						content_digest: digest("a"),
						locator: `artifact://store/${GOLDEN_BEARER}` } }] }],
				["a diagnostic key's value", { adapterDiagnostics: {
					"baton.relay/1": { nested: { deep: GOLDEN_BEARER } } } }]]) {
			assert.throws(() => ended(store, { ...extra,
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError
					&& error.code === "secret-leak", what);
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: the SUMMARY and the sealed record must agree", () => {
	const store = open();
	try {
		withSession(store);
		const turn = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
		// A drifted query column is an integrity failure wherever it is
		// found, not something to quietly prefer the sealed side of: the next
		// reader may be one that only has the column. Driven on each of the
		// three members the gate compares.
		for (const [column, value] of [["outcome", "refused"],
		                               ["conclusive", 0],
		                               ["permitted", '["completed"]']]) {
			const before = store.db.prepare(
				`SELECT ${column} AS v FROM turns WHERE turn_id = ?`)
				.get(turn.turnId).v;
			store.db.prepare(
				`UPDATE turns SET ${column} = ? WHERE turn_id = ?`)
				.run(value, turn.turnId);
			assert.throws(() => permitsDisposition(store, turn.turnId,
				"completed"),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest", column);
			store.db.prepare(
				`UPDATE turns SET ${column} = ? WHERE turn_id = ?`)
				.run(before, turn.turnId);
		}
		// And restored, the gate answers again.
		assert.equal(permitsDisposition(store, turn.turnId, "completed"), true);
	} finally {
		store.close();
	}
});

test("W2929: a record filed under another turn's identity is refused", () => {
	const store = open();
	try {
		withSession(store);
		const first = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
		const other = ended(store, { promptDigest: digest("other"),
			terminalFact: { kind: "acp-stop-reason", value: "refusal" } });
		const body = store.db.prepare(
			"SELECT body, document_digest FROM turns WHERE turn_id = ?")
			.get(other.turnId);
		// Both halves moved together, so every digest still agrees — only the
		// identity the caller ASKED FOR does not.
		store.db.prepare(
			"UPDATE turns SET body = ?, document_digest = ? WHERE turn_id = ?")
			.run(body.body, body.document_digest, first.turnId);
		assert.throws(() => turnRecordOf(store, first.turnId),
			(error) => error instanceof ContractError
				&& error.code === "digest"
				&& /calls itself/.test(error.message));
	} finally {
		store.close();
	}
});
