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
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, GOLDEN_BEARER, digest, forgetSecret, rememberSecret }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { AGENT_SESSION_SCHEMA_PATH }
	from "../src/worker_manager/agent_profile.mjs";
import { ACP_STOP_REASONS, CODEX_ERROR_INFO, CODEX_TURN_STATUSES, CONCLUSIVE,
         PERMITTED_DISPOSITIONS, TURN_ADMITTING_SESSION_STATES,
         TURN_OUTCOMES, TURN_STARTING_SESSION_STATES, allocateTurn,
         fromTerminalFact, permitsDisposition, recordTurn, selectTurnOutcome,
         turnRecordOf, turnToken }
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

// THE RELAY'S MEMORY, which is what a fixture is standing in for here.
//
// Schema 12 moved the turn identity from something derived to something the
// supervision boundary ALLOCATES, so a caller now holds a token across the
// life of one supervised turn — including across a retry of the record call.
// These cases say "the same supervised turn" by repeating a call's operands
// and "a different one" by moving the manager's window, so the fixture maps
// window -> allocated token to mean exactly that.
//
// It is scaffolding, not a contract: the window never reaches the product's
// identity, which is the ordinal `allocateTurn` claimed. Any case that wants
// two turns under ONE window, or one turn under two windows, passes its own
// `turnToken` and says so.
const _relayTokens = new Map();

function tokenFor(store, startedAt, deadlineAt) {
	let byWindow = _relayTokens.get(store);
	if (byWindow === undefined) {
		byWindow = new Map();
		_relayTokens.set(store, byWindow);
	}
	const key = `${startedAt}|${deadlineAt}`;
	if (!byWindow.has(key)) {
		byWindow.set(key, allocateTurn(store, REF).turnToken);
	}
	return byWindow.get(key);
}

/** OPEN the default supervised turn now, while the session is still ready.
 *
 *  §7.3 opens a turn only from `ready`, so a case that perturbs the session
 *  and THEN records is describing a turn that opened before the perturbation
 *  — which is exactly what a relay does: open, prompt, watch the state
 *  advance, record. Calling this first is the fixture saying so, and it keeps
 *  the perturbation being decided at the boundary the case is about. */
function openTurn(store, at = {}) {
	return tokenFor(store, at.startedAt ?? STARTED, at.deadlineAt ?? DEADLINE);
}

function ended(store, extra = {}) {
	const startedAt = "startedAt" in extra ? extra.startedAt : STARTED;
	const deadlineAt = "deadlineAt" in extra ? extra.deadlineAt : DEADLINE;
	return recordTurn(store, { sessionRef: REF, promptDigest: PROMPT,
		startedAt: STARTED, deadlineAt: DEADLINE, endedAt: ENDED,
		turnToken: tokenFor(store, startedAt, deadlineAt), ...extra });
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
			// Schema 12: four DISTINCT supervised turns, so four allocated
			// identities. They used to be told apart by their prompt bytes,
			// which is the fallback the fourth re-review removed.
			const turn = ended(store, { ...extra,
				turnToken: allocateTurn(store, REF).turnToken,
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

test("W2929: the turn identity is ALLOCATED, and carries no prompt", () => {
	// SUPERSEDED ASSERTION, on the fourth re-review's P1 ruling. This case
	// used to assert that `turnId(REF, digest("other"))` differed from
	// `turnId(REF, PROMPT)` — that the PROMPT was part of the identity. The
	// review ruled that prompt bytes belong in the effective signature and
	// cannot be the fallback deciding whether one supervised act is one turn
	// or two, so the old assertion states a contract that no longer exists.
	// The identity is the ordinal the supervision boundary claimed.
	const first = turnToken(REF, 1);
	assert.equal(turnToken({ ...REF }, 1), first, "the token is not stable");
	assert.equal(turnToken({ ...REF, sessionEpoch: 2 }, 1) === first, false);
	assert.equal(turnToken({ ...REF, posture: "consent" }, 1) === first, false);
	assert.equal(turnToken({ ...REF, runtimeAttemptId: "attempt-2" }, 1)
		=== first, false);
	assert.equal(turnToken(REF, 2) === first, false, "the ordinal is inert");
	// And nothing a caller says about the turn can reach it: there is no
	// prompt, no timestamp and no outcome in the derivation at all.
	assert.match(first, /^turn:[0-9a-f]{64}$/);
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
		// REVALIDATED against the schema-12 identity contract, as the fourth
		// re-review directed. This fixture used to mint its second turn by
		// changing the prompt under one window — the very thing that is no
		// longer an identity. Two supervised turns are two ALLOCATIONS; the
		// differing prompt is now incidental to what the case asserts, which
		// is that a body copied onto another turn's row is caught.
		const other = ended(store, {
			turnToken: allocateTurn(store, REF).turnToken,
			promptDigest: digest("other"),
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

test("W2929 re-review: repeated prompt bytes can identify a later turn", () => {
	const store = open();
	try {
		withSession(store);
		const first = ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
		const second = ended(store, {
			startedAt: "2026-08-22T12:02:00.000Z",
			deadlineAt: "2026-08-22T12:17:00.000Z",
			endedAt: "2026-08-22T12:03:00.000Z",
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
		assert.notEqual(second.turnId, first.turnId,
			"two supervised turns with identical prompt bytes were conflated");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 2);
	} finally {
		store.close();
	}
});

test("W2929 re-review: a closed session accepts no later turn", () => {
	const store = open();
	try {
		withSession(store);
		store.db.prepare(
			"UPDATE agent_sessions SET state = 'closed' WHERE "
			+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
			.run(ATTEMPT, REF.posture, REF.sessionEpoch);
		assert.throws(() => ended(store, {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 re-review: a turn binds the stored provider session identity", () => {
	const store = open();
	try {
		withSession(store);
		store.db.prepare(
			"UPDATE agent_sessions SET provider_session_id = ? WHERE "
			+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
			.run("provider-session-a", ATTEMPT, REF.posture, REF.sessionEpoch);
		assert.throws(() => ended(store, {
			sessionRef: { ...REF, providerSessionId: "provider-session-b" },
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM turns").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 re-review: malformed turn input uses the closed error taxonomy",
	() => {
		const store = open();
		try {
			withSession(store);
			assert.throws(() => ended(store, { policyFailures: null }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: malformed summary uses the closed error taxonomy",
	() => {
		const store = open();
		try {
			withSession(store);
			const turn = ended(store, {
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
			store.db.prepare(
				"UPDATE turns SET permitted = ? WHERE turn_id = ?")
				.run("not-json", turn.turnId);
			assert.throws(() => permitsDisposition(store, turn.turnId, "completed"),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: exact turn replay precedes current secret liveness", () => {
	const store = open();
	const laterBearer = "review-secret-that-was-benign-when-first-recorded";
	try {
		withSession(store);
		const operands = {
			terminalFact: { kind: "acp-stop-reason", value: "end_turn" },
			adapterDiagnostics: { "baton.relay/1": { note: laterBearer } },
		};
		const first = ended(store, operands);
		rememberSecret(laterBearer);
		assert.deepEqual(ended(store, operands), first,
			"current ephemeral registry state hid an exact committed replay");
	} finally {
		forgetSecret(laterBearer);
		store.close();
	}
});

// -- the correction's own boundaries ----------------------------------------

const SESSION_STATES = JSON.parse(
	readFileSync(AGENT_SESSION_SCHEMA_PATH).toString("utf8"))
	.$defs.sessionState.enum;

/** Put the one fixture session into an exact state. */
function sessionState(store, state) {
	store.db.prepare(
		"UPDATE agent_sessions SET state = ? WHERE runtime_attempt_id = ? "
		+ "AND posture = ? AND session_epoch = ?")
		.run(state, ATTEMPT, REF.posture, REF.sessionEpoch);
}

/** A supervision window nobody else in this file uses, keyed by minute. */
function window(minute) {
	const at = (m) => `2026-08-22T13:${String(m).padStart(2, "0")}:00.000Z`;
	return { startedAt: at(minute), deadlineAt: at(minute + 30),
	         endedAt: at(minute + 1) };
}

test("W2929 fifth review: allocation opens only the exact ready session",
	() => {
		const store = open();
		try {
			withSession(store);
			store.db.prepare(
				"UPDATE agent_sessions SET provider_session_id = ? WHERE "
				+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
				.run("provider-session-a", ATTEMPT, REF.posture,
				     REF.sessionEpoch);
			for (const state of SESSION_STATES.filter((value) => value !== "ready")) {
				sessionState(store, state);
				assert.throws(() => allocateTurn(store, {
					...REF, providerSessionId: "provider-session-a" }),
					(error) => error instanceof ContractError
						&& error.category === "refused"
						&& error.code === "precondition", state);
			}
			sessionState(store, "ready");
			assert.throws(() => allocateTurn(store, {
				...REF, providerSessionId: "provider-session-b" }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turn_allocations").get().n, 0,
				"a refused opening left a supervised-turn allocation behind");
			const opened = allocateTurn(store, {
				...REF, providerSessionId: "provider-session-a" });
			assert.equal(opened.turnOrdinal, 1);
			assert.equal(opened.agentSessionRef.providerSessionId,
				"provider-session-a");
		} finally {
			store.close();
		}
	});

test("W2929 correction: an allocation is the identity, and it is epoch-local",
	() => {
		// SUPERSEDES my round-3 case, which asserted that the manager's
		// supervision window `(startedAt, deadlineAt)` was the identity
		// component. The fourth re-review ruled that reusable operands are
		// not an allocation however manager-owned they are, and it is right:
		// nothing recorded the window, nothing bounded it, and prompt bytes
		// were still deciding whether a reuse meant one turn or two.
		const store = open();
		try {
			withSession(store);
			const first = allocateTurn(store, REF);
			const second = allocateTurn(store, REF);
			assert.equal(first.turnOrdinal, 1);
			assert.equal(second.turnOrdinal, 2, "the ordinal did not advance");
			assert.notEqual(second.turnToken, first.turnToken);
			assert.equal(first.turnToken, turnToken(REF, 1));
			// RECORDED, which is the half a derived component never had.
			assert.deepEqual(store.db.prepare(
				"SELECT turn_ordinal FROM turn_allocations WHERE "
				+ "runtime_attempt_id = ? AND posture = ? AND "
				+ "session_epoch = ? ORDER BY turn_ordinal")
				.all(ATTEMPT, REF.posture, REF.sessionEpoch)
				.map((row) => row.turn_ordinal), [1, 2]);
			// And the counter is per epoch, not per store: a second epoch
			// starts at one and its tokens are still distinct, because the
			// epoch is in the derivation.
			store.db.prepare(
				"UPDATE agent_sessions SET state = 'closed' WHERE "
				+ "runtime_attempt_id = ? AND posture = ? AND "
				+ "session_epoch = ?")
				.run(ATTEMPT, REF.posture, REF.sessionEpoch);
			store.db.prepare(
				"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
				+ "session_epoch, profile_digest, pinned_policy, work_id, "
				+ "authority_uuid, state, opened_at) "
				+ "VALUES (?, 'execution', 2, ?, ?, ?, ?, 'ready', ?)")
				.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID,
				     NOW);
			const later = allocateTurn(store, { ...REF, sessionEpoch: 2 });
			assert.equal(later.turnOrdinal, 1, "the counter is not per epoch");
			assert.notEqual(later.turnToken, first.turnToken);
		} finally {
			store.close();
		}
	});

test("W2929 correction: a changed prompt under one allocated turn COLLIDES",
	() => {
		// THE POINT OF THE FOURTH RE-REVIEW, asserted directly. Prompt bytes
		// are in the effective signature and nowhere near the identity, so
		// re-recording ONE supervised turn with different prompt bytes is
		// changed operands for one act — not a quiet second turn.
		const store = open();
		try {
			withSession(store);
			const token = allocateTurn(store, REF).turnToken;
			const fact = { kind: "acp-stop-reason", value: "end_turn" };
			const first = ended(store, { turnToken: token, terminalFact: fact });
			assert.deepEqual(ended(store, { turnToken: token,
				terminalFact: { ...fact } }), first, "the exact retry did not "
				+ "replay");
			assert.throws(() => ended(store, { turnToken: token,
				promptDigest: digest("a different prompt"),
				terminalFact: fact }),
				(error) => error instanceof ContractError
					&& error.code === "operation-collision");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turns").get().n, 1);
		} finally {
			store.close();
		}
	});

test("W2929 correction: a record is written under an allocation, or refused",
	() => {
		const store = open();
		try {
			withSession(store);
			const fact = { kind: "acp-stop-reason", value: "end_turn" };
			// A well-formed token nobody allocated is a string, not an
			// identity — the foreign key alone would only ask whether the
			// string exists somewhere.
			assert.throws(() => ended(store, { turnToken: turnToken(REF, 99),
				terminalFact: fact }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
			// And an allocation belonging to ANOTHER epoch is not this turn's
			// identity however well formed it is.
			//
			// The other epoch is the CONSENT posture, deliberately: §3.2 lets
			// both postures hold an open session under one attempt, so the
			// execution epoch stays `ready` and the refusal has to come from
			// the allocation binding. Closing this epoch to make room for a
			// second execution one would have let admission refuse first and
			// proved nothing about the binding.
			store.db.prepare(
				"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
				+ "session_epoch, profile_digest, pinned_policy, work_id, "
				+ "authority_uuid, state, opened_at) "
				+ "VALUES (?, 'consent', 1, ?, ?, ?, ?, 'ready', ?)")
				.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID,
				     NOW);
			const other = { ...REF, posture: "consent" };
			const foreign = allocateTurn(store, other);
			assert.throws(() => recordTurn(store, {
				sessionRef: REF, promptDigest: PROMPT,
				startedAt: STARTED, deadlineAt: DEADLINE, endedAt: ENDED,
				turnToken: foreign.turnToken, terminalFact: fact }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
			// A missing or malformed token is the closed schema pair, not a
			// raw property read on undefined.
			for (const [what, bad] of [["absent", undefined],
			                           ["null", null],
			                           ["empty", ""],
			                           ["a number", 7]]) {
				assert.throws(() => recordTurn(store, { sessionRef: REF,
					promptDigest: PROMPT, startedAt: STARTED,
					deadlineAt: DEADLINE, endedAt: ENDED, turnToken: bad,
					terminalFact: fact }),
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

test("W2929 correction: a re-reported end instant COLLIDES, never re-turns",
	() => {
		const store = open();
		try {
			withSession(store);
			const fact = { kind: "acp-stop-reason", value: "end_turn" };
			ended(store, { terminalFact: fact });
			// `ended_at` is what the manager OBSERVED, not what it allocated.
			// Folding it into the identity would have answered this with a
			// silent second turn document for one supervised turn.
			assert.throws(() => ended(store, { terminalFact: fact,
				endedAt: "2026-08-22T12:04:00.000Z" }),
				(error) => error instanceof ContractError
					&& error.code === "operation-collision");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turns").get().n, 1);
		} finally {
			store.close();
		}
	});

test("W2929 correction: every frozen session state admits a turn or refuses one",
	() => {
		const store = open();
		try {
			withSession(store);
			// EXHAUSTIVE over the frozen vocabulary, in BOTH directions: a
			// partition tested only on the states somebody remembered is a
			// partition a newly frozen state joins silently.
			assert.equal(SESSION_STATES.length > 0, true);
			assert.deepEqual(TURN_ADMITTING_SESSION_STATES
				.filter((state) => !SESSION_STATES.includes(state)), [],
				"an admitting state is not in the frozen vocabulary");
			// OPENED WHILE READY, every one of them, and only then does the
			// state move. Fifth re-review: allocation now admits the exact
			// `ready` session, so opening inside the loop would have refused
			// at the START boundary and stopped proving anything about the
			// SETTLE boundary this case exists for. The two are different
			// questions and this case asks the second one.
			const opened = SESSION_STATES.map((_state, index) => {
				const at = window((index + 1) * 2);
				return { at, token: openTurn(store, at) };
			});
			for (const [index, state] of SESSION_STATES.entries()) {
				const { at } = opened[index];
				sessionState(store, state);
				const before = store.db.prepare(
					"SELECT COUNT(*) AS n FROM turns").get().n;
				const token = opened[index].token;
				const record = () => recordTurn(store, { sessionRef: REF,
					promptDigest: PROMPT, ...at, turnToken: token,
					terminalFact: { kind: "acp-stop-reason",
					                value: "end_turn" } });
				if (TURN_ADMITTING_SESSION_STATES.includes(state)) {
					assert.equal(record().outcome, "completed", state);
					assert.equal(store.db.prepare(
						"SELECT COUNT(*) AS n FROM turns").get().n,
						before + 1, state);
				} else {
					assert.throws(record,
						(error) => error instanceof ContractError
							&& error.category === "refused"
							&& error.code === "precondition", state);
					assert.equal(store.db.prepare(
						"SELECT COUNT(*) AS n FROM turns").get().n,
						before, state);
				}
			}
		} finally {
			store.close();
		}
	});

test("W2929 correction: opening and settling are two sets, and START is one",
	() => {
		// The fifth re-review's structural point, held as a property rather
		// than left to the two lists staying different by habit. §7.3 draws
		// ONE edge that starts a prompt, so the start set is exactly `ready`;
		// a turn opened there may settle wherever the state has legally
		// advanced to since, so START is a strict subset of SETTLE.
		assert.deepEqual([...TURN_STARTING_SESSION_STATES], ["ready"]);
		assert.deepEqual(TURN_STARTING_SESSION_STATES
			.filter((state) => !TURN_ADMITTING_SESSION_STATES.includes(state)),
			[], "a turn may open in a state it could not settle in");
		assert.equal(
			TURN_STARTING_SESSION_STATES.length
				< TURN_ADMITTING_SESSION_STATES.length, true,
			"the two sets collapsed; opening asks the stricter question");
		// And both are drawn from the frozen vocabulary, so neither can name
		// a state the boundary does not have.
		for (const state of [...TURN_STARTING_SESSION_STATES,
		                     ...TURN_ADMITTING_SESSION_STATES]) {
			assert.equal(SESSION_STATES.includes(state), true, state);
		}
	});

test("W2929 correction: a turn opened while ready settles after the state moves",
	() => {
		// The positive direction of the split, stated on its own rather than
		// only inside the exhaustive loop: the relay opens while ready,
		// prompts, the session advances to `prompting` as §7.3 says it does,
		// and the terminal fact is recorded against that later state.
		const store = open();
		try {
			withSession(store);
			const token = openTurn(store);
			sessionState(store, "prompting");
			const turn = ended(store, { turnToken: token,
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
			assert.equal(turn.outcome, "completed");
			assert.equal(turnRecordOf(store, turn.turnId).turn_id, token);
			// And the epoch that has moved on refuses to OPEN another one.
			assert.throws(() => allocateTurn(store, REF),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
		} finally {
			store.close();
		}
	});

test("W2929 correction: a turn committed before the epoch closed still replays",
	() => {
		const store = open();
		try {
			withSession(store);
			const fact = { kind: "acp-stop-reason", value: "end_turn" };
			const first = ended(store, { terminalFact: fact });
			// Both facts are true: the turn settled legitimately, and the
			// session closed afterwards. The immutable one is the answer the
			// retry is owed, so admission never gets to reconsider it.
			sessionState(store, "closed");
			assert.deepEqual(ended(store, { terminalFact: fact }), first,
				"a later session close rewrote an already committed answer");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turns").get().n, 1);
		} finally {
			store.close();
		}
	});

test("W2929 correction: an omitted provider session is still a disagreement",
	() => {
		const store = open();
		try {
			withSession(store);
			// Opened while the epoch is ready and still unlabelled, so the
			// refusal below has to come from the SETTLE-side binding rather
			// than from the start-side one the fifth review added.
			openTurn(store);
			store.db.prepare(
				"UPDATE agent_sessions SET provider_session_id = ? WHERE "
				+ "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?")
				.run("provider-session-a", ATTEMPT, REF.posture,
				     REF.sessionEpoch);
			// Saying nothing is not agreeing. The sealed record would have
			// carried `provider_session_id: null` for an epoch that durably
			// holds one, and §3.1's reference labels evidence.
			assert.throws(() => ended(store, {
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turns").get().n, 0);
			// And the agreeing reference is sealed into the record.
			const turn = ended(store, {
				sessionRef: { ...REF, providerSessionId: "provider-session-a" },
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
			assert.equal(turnRecordOf(store, turn.turnId)
				.agent_session_ref.provider_session_id, "provider-session-a");
		} finally {
			store.close();
		}
	});

test("W2929 correction: a malformed session reference reports a closed pair",
	() => {
		// The BEHAVIOUR, not one line: measured, `turnSessionRef` is masked
		// here by the frozen record validation, which refuses the same
		// references with the same pair. What is asserted is that no shape a
		// caller can supply escapes the closed taxonomy as a raw `TypeError`.
		const store = open();
		try {
			withSession(store);
			for (const [what, ref] of [
					["absent", undefined],
					["not an object", "execution/1"],
					["no attempt", { ...REF, runtimeAttemptId: null }],
					["invented posture", { ...REF, posture: "review" }],
					["epoch zero", { ...REF, sessionEpoch: 0 }],
					["fractional epoch", { ...REF, sessionEpoch: 1.5 }],
					["provider id object", { ...REF,
						providerSessionId: { id: "a" } }]]) {
				assert.throws(() => ended(store, { sessionRef: ref,
					terminalFact: { kind: "acp-stop-reason",
					                value: "end_turn" } }),
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

test("W2929 fourth review: a non-cloneable policy failure reports a closed pair",
	() => {
		const store = open();
		try {
			withSession(store);
			assert.throws(() => ended(store, {
				policyFailures: [() => "not a frozen document"],
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM turns").get().n, 0);
		} finally {
			store.close();
		}
	});

test("W2929 fourth review: malformed sealed-record bytes use the closed taxonomy",
	() => {
		const store = open();
		try {
			withSession(store);
			const turn = ended(store, {
				terminalFact: { kind: "acp-stop-reason", value: "end_turn" } });
			store.db.prepare(
				"UPDATE turns SET body = ? WHERE turn_id = ?")
				.run("not-json", turn.turnId);
			assert.throws(() => turnRecordOf(store, turn.turnId),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
		} finally {
			store.close();
		}
	});
