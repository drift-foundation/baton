// W2929 item 3, second slice: activation and runtime start.
//
// The ordering is what these cases are about. Every one of them asks the
// same question the offer slice asked: after a crash, can the next
// incarnation tell what exists? So the fixtures are about what was recorded
// BEFORE an outside call, and what the manager decides when the outside
// world answers ambiguously.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { V12Authority, V12 } from "../src/authority/index.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { activateAssignment, authorityCancelOperationId, cancelOperationId,
         observe, recordAttempt, reconcileRuntime, requestCancellation,
         requestRuntimeStart, runtimeLabels, AXES, TRANSITIONS }
	from "../src/worker_manager/attempts.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const WHO = "poc.claude";
const ATTEMPT = "attempt-1";
const ASSIGNMENT = { authorityUuid: UUID, workId: WORK, participant: WHO,
                     generation: 1 };

function storePath() {
	return join(ownedTemp("v12-manager-"), "control.sqlite3");
}

function open(path = storePath()) {
	return new ControlStore(path, { incarnation: "manager-1",
		clock: () => "2026-08-22T12:00:00.000Z" });
}

function attempt(store, extra = {}) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
	                       adapterDigest: digest("adapter"),
	                       profileDigest: digest("profile"), ...extra });
	return ATTEMPT;
}

/** The authority, scripted down to the reads and writes this slice performs.
 *
 *  `trace` is SHARED with the adapter double on purpose: the cancellation
 *  ordering is a claim about which boundary was reached first, and a
 *  per-double call list cannot express it. Final state cannot either — a
 *  manager that stopped the runtime and then fenced would leave exactly the
 *  same rows behind. */
function session({ assignment = ASSIGNMENT, participant = WHO, cancel = null,
                   trace = [] } = {}) {
	return {
		trace,
		participant,
		assignmentOf: () => assignment,
		cancel(operands) {
			trace.push(["authority.cancel", operands]);
			if (cancel !== null) return cancel(operands);
			return { ...ASSIGNMENT, phase: "block",
			         gate: `runtime-quiescence:${ASSIGNMENT.generation}`,
			         cause: "cancelled", fenced: true };
		},
	};
}

/** The AGENT, scripted. Item 4 owns the provider-neutral agent-session
 *  contract; item 3 owns where its cancellation sits in the order, which is
 *  after the authority fence and before the runtime stop. */
function agent({ cancel = null, trace = [] } = {}) {
	const calls = [];
	return {
		calls,
		trace,
		cancel(operands) {
			calls.push(["cancel", operands]);
			trace.push(["agent.cancel", operands]);
			return cancel === null ? { cancelled: "requested" } : cancel(operands);
		},
	};
}

/** The adapter, scripted. Item 4 owns what a conforming one must BE; this
 *  slice only needs something that starts, lists and stops. */
function adapter({ start = null, list = () => [], stop = null,
                   trace = [] } = {}) {
	const calls = [];
	return {
		calls,
		trace,
		start(operands) {
			calls.push(["start", operands]);
			return start === null ? { runtimeId: "runtime-1" } : start(operands);
		},
		list(operands) {
			calls.push(["list", operands]);
			return list(operands);
		},
		stop(operands) {
			calls.push(["stop", operands]);
			trace.push(["adapter.stop", operands]);
			return stop === null ? { stopped: true } : stop(operands);
		},
	};
}

/** The durable precondition activation now requires: THIS attempt's own
 *  committed claim.
 *
 *  Written straight into the offers table on purpose. The offer path — issue,
 *  accept, claim, settle — has its own suite; what this one needs is the row
 *  that path leaves behind, and driving the whole of it here would test it
 *  twice while making the activation cases harder to read.
 */
function claimed(store, { assignment = ASSIGNMENT } = {}) {
	store.db.prepare(
		"INSERT INTO offers (offer_id, work_id, authority_uuid, participant, "
		+ "runtime_attempt_id, incarnation, input_digest, policy_digest, "
		+ "profile_digest, verifier, verifier_spent, issued_at, expires_at, "
		+ "state, claim_generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, "
		+ "?, ?, 'claimed', ?)")
		.run(`offer-for-${assignment.workId}-${assignment.generation}`,
		     assignment.workId, assignment.authorityUuid,
		     assignment.participant, ATTEMPT, "manager-1", digest("input"),
		     digest("policy"), digest("profile"), "sha256:" + "0".repeat(64),
		     "2026-08-22T11:00:00.000Z", "2026-08-22T13:00:00.000Z",
		     assignment.generation);
	return assignment;
}

function activated(store, api = session()) {
	attempt(store);
	claimed(store);
	activateAssignment(store, api, { attemptId: ATTEMPT,
	                                 expect: ASSIGNMENT });
	return ATTEMPT;
}

/** Activated AND attached to a running runtime — the state a cancellation
 *  actually finds. */
function running(store, api = session()) {
	activated(store, api);
	const runtime = adapter({ list: () => [
		{ runtimeId: "runtime-1", labels: runtimeLabels(row(store)) }] });
	const decided = requestRuntimeStart(store, runtime, { attemptId: ATTEMPT });
	assert.equal(decided.decision, "attached", "the fixture did not attach");
	return ATTEMPT;
}

function row(store) {
	return store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id=?").get(ATTEMPT);
}

// -- activation --------------------------------------------------------------

test("W2929: activation fixes the assignment before anything writable runs",
	() => {
		const store = open();
		try {
			attempt(store);
			claimed(store);
			assert.equal(row(store).assignment_generation, null,
				"an attempt exists from the offer, before any assignment");
			const fixed = activateAssignment(store, session(), {
				attemptId: ATTEMPT, expect: ASSIGNMENT });
			assert.equal(fixed.alreadyFixed, false);
			const after = row(store);
			assert.equal(after.work_id, WORK);
			assert.equal(after.authority_uuid, UUID);
			assert.equal(after.assignment_generation, 1);
		} finally {
			store.close();
		}
	});

test("W2929: a stale or ended assignment is refused BEFORE the adapter", () => {
	// The point of doing this first: after one writable call the same
	// refusal would leave a runtime nobody is authorized to own.
	for (const [what, live] of [
			["ended", null],
			["a newer generation", { ...ASSIGNMENT, generation: 2 }],
			["another participant", { ...ASSIGNMENT, participant: "poc.other" }],
			["another authority", { ...ASSIGNMENT, authorityUuid: "x".repeat(32) }]]) {
		const store = open();
		try {
			attempt(store);
			claimed(store);
			assert.throws(() => activateAssignment(store, session({ assignment: live }), {
				attemptId: ATTEMPT, expect: ASSIGNMENT }),
				(error) => error instanceof ContractError
					&& error.category === "stale-assignment", what);
			assert.equal(row(store).assignment_generation, null, what);
		} finally {
			store.close();
		}
	}
});

test("W2929: the manifest is fixed ONCE", () => {
	const store = open();
	try {
		activated(store);
		// The same assignment replays.
		assert.equal(activateAssignment(store, session(), {
			attemptId: ATTEMPT, expect: ASSIGNMENT }).alreadyFixed, true);
		// A different one does not silently re-point the attempt.
		assert.throws(() => activateAssignment(store, session(), {
			attemptId: ATTEMPT,
			expect: { ...ASSIGNMENT, generation: 2 } }),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment");
		assert.equal(row(store).assignment_generation, 1);
	} finally {
		store.close();
	}
});

// -- start ordering ----------------------------------------------------------

test("W2929: start is RECORDED before the adapter is called", () => {
	// The order is the evidence. Calling first and recording afterwards
	// leaves a crash window with no durable trace that a runtime may exist,
	// and the next incarnation starts a second one.
	const store = open();
	const seen = [];
	const api = adapter({ start: () => {
		seen.push(row(store).execution_runtime);
		return { runtimeId: "runtime-1" };
	}, list: () => [{ runtimeId: "runtime-1",
	                  labels: runtimeLabels(row(store)) }] });
	try {
		activated(store);
		requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.deepEqual(seen, ["start-requested"],
			"the adapter was called before the intent was durable");
	} finally {
		store.close();
	}
});

test("W2929: an unactivated attempt cannot start anything", () => {
	const store = open();
	const api = adapter();
	try {
		attempt(store);
		assert.throws(() => requestRuntimeStart(store, api,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& /not activated/.test(error.message));
		assert.deepEqual(api.calls, [], "an unactivated attempt reached the adapter");
	} finally {
		store.close();
	}
});

// -- reconciliation ----------------------------------------------------------

test("W2929: exactly one matching runtime REATTACHES", () => {
	const store = open();
	try {
		activated(store);
		const api = adapter({ list: () => [
			{ runtimeId: "runtime-1", labels: runtimeLabels(row(store)) }] });
		const decided = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(decided.decision, "attached");
		assert.equal(decided.runtimeId, "runtime-1");
		assert.equal(row(store).runtime_id, "runtime-1");
		assert.equal(row(store).execution_runtime, "running");
	} finally {
		store.close();
	}
});

test("W2929: zero runtimes WAIT, and the retry path is CLOSED", () => {
	// The case that matters most. "The adapter sees nothing" and "nothing
	// exists" are different facts, and starting a second runtime for one
	// assignment is the failure this ordering exists to prevent.
	//
	// Review [P1]: my first version let the CALLER assert absence with a
	// boolean — the rejected `schemaProven: true` shape, where a proof the
	// caller writes is not a proof. Positive absence needs validated
	// certified-adapter evidence, which is item 4's to define, so the retry
	// path stays closed and the refusal says which slice owns it.
	const store = open();
	try {
		activated(store);
		const api = adapter({ list: () => [] });
		const waited = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(waited.decision, "uncertain");
		assert.equal(row(store).execution_runtime, "uncertain");
		assert.equal(row(store).runtime_id, null);
		// Asking again changes nothing, whatever the caller passes.
		const again = reconcileRuntime(store, api, { attemptId: ATTEMPT,
		                                             absenceProven: true });
		assert.equal(again.decision, "uncertain");
		assert.equal(row(store).execution_runtime, "uncertain");
	} finally {
		store.close();
	}
});

test("W2929: multiplicity CANCELS rather than starting another", () => {
	const store = open();
	try {
		activated(store);
		const api = adapter({ list: () => [
			{ runtimeId: "runtime-1", labels: runtimeLabels(row(store)) },
			{ runtimeId: "runtime-2", labels: runtimeLabels(row(store)) }] });
		const decided = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(decided.decision, "cancel");
		assert.deepEqual(decided.runtimes, ["runtime-1", "runtime-2"]);
		assert.equal(row(store).execution_runtime, "cancel-requested");
		assert.equal(row(store).runtime_id, null,
			"a cancelled multiplicity attached to one of them anyway");
	} finally {
		store.close();
	}
});

test("W2929: a MISMATCHED runtime cancels rather than reattaching", () => {
	const store = open();
	try {
		activated(store);
		const api = adapter({
			start: () => ({ runtimeId: "runtime-mine" }),
			list: () => [{ runtimeId: "runtime-somebody-elses",
			               labels: runtimeLabels(row(store)) }] });
		const decided = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(decided.decision, "cancel");
		assert.match(decided.why, /runtime-mine/);
		assert.equal(row(store).execution_runtime, "cancel-requested");
	} finally {
		store.close();
	}
});

test("W2929: identification is by labels, not by the adapter's id alone", () => {
	// An id the adapter minted proves only that something answers to it. A
	// runtime carrying another assignment's labels is somebody else's, and
	// attaching to it would put two managers on one runtime.
	const store = open();
	try {
		activated(store);
		const mine = runtimeLabels(row(store));
		const api = adapter({ start: () => ({}), list: () => [
			{ runtimeId: "runtime-1",
			  labels: { ...mine, generation: 7 } },
			{ runtimeId: "runtime-2",
			  labels: { ...mine, workId: "43c55d4b-W9" } },
			{ runtimeId: "runtime-3", labels: {} }] });
		const decided = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(decided.decision, "uncertain",
			"a runtime with another assignment's labels was adopted");
		assert.equal(row(store).runtime_id, null);
	} finally {
		store.close();
	}
});

// -- the axes ----------------------------------------------------------------

test("W2929: only the frozen axes and their frozen values", () => {
	const store = open();
	try {
		activated(store);
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "invented", value: "running" }),
			(error) => /frozen runtime-attempt axes/.test(error.message));
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "exploded" }),
			(error) => /not a value of execution_runtime/.test(error.message));
		// Every declared value IS reachable along the axis's OWN
		// transitions, which is the other half: a map that could not reach
		// its own members would be worse than no map. Walking the
		// vocabulary in array order is exactly what the review rejected,
		// so this walks the transitions instead.
		const reached = new Set(["not-started"]);
		let frontier = ["not-started"];
		while (frontier.length > 0) {
			const next = [];
			for (const from of frontier) {
				for (const to of TRANSITIONS.execution_runtime[from]) {
					if (reached.has(to)) continue;
					reached.add(to);
					next.push(to);
				}
			}
			frontier = next;
		}
		assert.deepEqual([...reached].sort(),
			[...AXES.execution_runtime].sort(),
			"an axis declares a value its own transitions cannot reach");
	} finally {
		store.close();
	}
});

test("W2929: UNCERTAIN never becomes destroyed", () => {
	// Destruction is a fact about the world. Inferring it from a failure to
	// look would let a manager report a cleaned-up runtime that is still
	// executing somebody's code.
	const store = open();
	try {
		activated(store);
		// Through the transition the axis actually declares: a start is
		// requested before anything is uncertain about it.
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
		                 value: "start-requested" });
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
		                 value: "uncertain" });
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "destroyed" }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "state-regression");
		assert.equal(row(store).execution_runtime, "uncertain");
		// The consent axis carries the same rule.
		observe(store, { attemptId: ATTEMPT, axis: "consent_runtime",
		                 value: "uncertain" });
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "consent_runtime", value: "destroyed" }),
			(error) => error instanceof ContractError);
	} finally {
		store.close();
	}
});

test("W2929: an axis does not go backwards, and a repeat is inert", () => {
	const store = open();
	try {
		activated(store);
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
		                 value: "start-requested" });
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
		                 value: "running" });
		const before = row(store).observation_seq;
		// A repeat changes nothing and does not advance the sequence.
		assert.equal(observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "running" }).changed, false);
		assert.equal(row(store).observation_seq, before);
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "start-requested" }),
			(error) => error instanceof ContractError
				&& error.code === "state-regression");
		// And there is NO public reset. Review [P1]: `allowReset` was an
		// exported bypass of the very rule above, and a monotonicity a
		// caller can switch off is not one.
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "not-started",
			allowReset: true }),
			(error) => error instanceof ContractError
				&& error.code === "state-regression");
	} finally {
		store.close();
	}
});

// -- independent review edges ----------------------------------------------

test("W2929 review: reactivation compares the FULL assignment", () => {
	const store = open();
	try {
		activated(store);
		assert.throws(() => activateAssignment(store, session(), {
			attemptId: ATTEMPT,
			expect: { ...ASSIGNMENT, participant: "poc.other" },
		}), (error) => error instanceof ContractError,
		"the already-fixed fast path accepted another participant");
		assert.throws(() => activateAssignment(store, session(), {
			attemptId: ATTEMPT,
			expect: { ...ASSIGNMENT, authorityUuid: "f".repeat(32) },
		}), (error) => error instanceof ContractError,
		"the already-fixed fast path accepted another authority");
	} finally {
		store.close();
	}
});

test("W2929 review: runtime labels carry the full assignment", () => {
	const store = open();
	try {
		activated(store);
		assert.equal(runtimeLabels(row(store)).participant, WHO,
			"the participant disappeared between activation and runtime identity");
	} finally {
		store.close();
	}
});

test("W2929 review: activation uses the participant-bound session", () => {
	const store = open();
	try {
		attempt(store);
		const foreign = { participant: "poc.other",
			assignmentOf: () => ASSIGNMENT };
		assert.throws(() => activateAssignment(store, foreign, {
			attemptId: ATTEMPT, expect: ASSIGNMENT,
		}), (error) => error instanceof ContractError,
		"a foreign participant's session activated this assignment");
	} finally {
		store.close();
	}
});

test("W2929 review: activation requires this attempt's recorded claim", () => {
	const store = open();
	try {
		// A live assignment somewhere in the authority is not proof that this
		// attempt's accepted offer claimed it. No offer or claim record exists.
		attempt(store);
		assert.throws(() => activateAssignment(store, session(), {
			attemptId: ATTEMPT, expect: ASSIGNMENT,
		}), (error) => error instanceof ContractError,
		"an unrelated live assignment authorized a free-standing attempt");
	} finally {
		store.close();
	}
});

test("W2929 review: attempt replay signs every durable operand", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"), profileDigest: digest("profile"),
			inputDigest: digest("input-a"), imageDigest: digest("image-a") });
		assert.throws(() => recordAttempt(store, {
			attemptId: ATTEMPT, adapterName: "different-adapter",
			adapterDigest: digest("adapter"), profileDigest: digest("profile"),
			inputDigest: digest("input-b"), imageDigest: digest("image-b"),
		}), (error) => error instanceof ContractError
			&& error.code === "operation-collision",
		"changed durable operands replayed the first attempt");
	} finally {
		store.close();
	}
});

test("W2929 review: a caller cannot self-attest runtime absence", () => {
	const store = open();
	try {
		activated(store);
		const api = adapter({ list: () => [] });
		requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		let answer = null;
		try {
			answer = reconcileRuntime(store, api, { attemptId: ATTEMPT,
				absenceProven: true });
		} catch (error) {
			assert.ok(error instanceof ContractError);
		}
		assert.notEqual(answer?.decision, "retry",
			"a bare boolean manufactured positive absence evidence");
		assert.notEqual(row(store).execution_runtime, "not-started");
	} finally {
		store.close();
	}
});

test("W2929 review: a runtime identity is fixed after attachment", () => {
	const store = open();
	try {
		activated(store);
		const labels = runtimeLabels(row(store));
		reconcileRuntime(store, adapter({ list: () => [
			{ runtimeId: "runtime-1", labels }] }), { attemptId: ATTEMPT });
		assert.equal(row(store).runtime_id, "runtime-1");
		try {
			reconcileRuntime(store, adapter({ list: () => [
				{ runtimeId: "runtime-2", labels }] }), { attemptId: ATTEMPT });
		} catch (error) {
			assert.ok(error instanceof ContractError);
		}
		assert.equal(row(store).runtime_id, "runtime-1",
			"a later inspection silently replaced the attached runtime");
	} finally {
		store.close();
	}
});

test("W2929 review: the minted runtime with wrong labels cancels", () => {
	const store = open();
	try {
		activated(store);
		const wrong = { ...runtimeLabels(row(store)), generation: 9 };
		const api = adapter({
			start: () => ({ runtimeId: "runtime-1" }),
			list: () => [{ runtimeId: "runtime-1", labels: wrong }],
		});
		const answer = requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(answer.decision, "cancel",
			"the runtime this call minted came back with another assignment's labels");
		assert.equal(row(store).execution_runtime, "cancel-requested");
	} finally {
		store.close();
	}
});

test("W2929 review: the runtime-start operation is durable before start", () => {
	const store = open();
	let operationCount = null;
	let operationId = null;
	try {
		activated(store);
		const api = adapter({ start: (operands) => {
			operationCount = store.db.prepare(
				"SELECT count(*) AS n FROM operations WHERE kind='runtime.start'")
				.get().n;
			operationId = operands.operationId ?? null;
			return { runtimeId: "runtime-1" };
		}, list: () => [{ runtimeId: "runtime-1",
			labels: runtimeLabels(row(store)) }] });
		requestRuntimeStart(store, api, { attemptId: ATTEMPT });
		assert.equal(operationCount, 1,
			"start-requested was an unjournalled axis write");
		assert.equal(typeof operationId, "string",
			"the adapter received no stable start operation identity");
		assert.ok(operationId.length > 0);
	} finally {
		store.close();
	}
});

test("W2929 review: allowReset is not a public monotonicity bypass", () => {
	const store = open();
	try {
		activated(store);
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "destroyed" });
		try {
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "running", allowReset: true });
		} catch (error) {
			assert.ok(error instanceof ContractError);
		}
		assert.equal(row(store).execution_runtime, "destroyed",
			"a caller reset positive destruction back to running");
	} finally {
		store.close();
	}
});

test("W2929 review: terminal alternatives are not an enum walk", () => {
	const store = open();
	try {
		activated(store);
		observe(store, { attemptId: ATTEMPT, axis: "worker_disposition",
			value: "completed" });
		try {
			observe(store, { attemptId: ATTEMPT, axis: "worker_disposition",
				value: "unable" });
		} catch (error) {
			assert.ok(error instanceof ContractError);
		}
		assert.equal(row(store).worker_disposition, "completed",
			"one terminal disposition was rewritten as another");
	} finally {
		store.close();
	}
});

test("W2929 review: a stale observer cannot regress a newer axis value", () => {
	const path = storePath();
	let hook = null;
	const first = new ControlStore(path, { incarnation: "manager-1",
		clock: () => {
			if (hook !== null) {
				const act = hook;
				hook = null;
				act();
			}
			return "2026-08-22T12:00:00.000Z";
		} });
	const second = new ControlStore(path, { incarnation: "manager-2",
		clock: () => "2026-08-22T12:00:01.000Z" });
	try {
		activated(first);
		observe(first, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "running" });
		hook = () => observe(second, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "quiescent" });
		try {
			observe(first, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "cancel-requested" });
		} catch (error) {
			assert.ok(error instanceof ContractError);
		}
		assert.equal(row(second).execution_runtime, "quiescent",
			"a stale read overwrote a stronger concurrent observation");
	} finally {
		first.close();
		second.close();
	}
});

test("W2929: a foreign session cannot activate a claim it does not hold", () => {
	// The review's own case for this is refused by the CLAIM guard first,
	// because its fixture has no claim at all. With the claim present, the
	// session binding is what must refuse — and it is a different rule: the
	// claim says which assignment this attempt won, the binding says who is
	// asking.
	const store = open();
	try {
		attempt(store);
		claimed(store);
		const foreign = { participant: "poc.other",
		                  assignmentOf: () => ASSIGNMENT };
		assert.throws(() => activateAssignment(store, foreign, {
			attemptId: ATTEMPT, expect: ASSIGNMENT }),
			(error) => error instanceof ContractError
				&& /acts for poc.other/.test(error.message),
			"a foreign participant activated an assignment it does not hold");
		assert.equal(row(store).assignment_generation, null);
		// And a session with NO binding at all is refused before anything
		// else is read.
		assert.throws(() => activateAssignment(store,
			{ assignmentOf: () => ASSIGNMENT },
			{ attemptId: ATTEMPT, expect: ASSIGNMENT }),
			(error) => error instanceof ContractError
				&& /names no participant/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929 re-review: one attempt cannot have two claimed offers", () => {
	// Activation asks for THIS attempt's claim. That question has no honest
	// answer if the store admits two terminal claim rows for the same attempt;
	// SELECT.get would merely choose one by an unspecified row order.
	const store = open();
	try {
		attempt(store);
		claimed(store);
		assert.throws(() => claimed(store, { assignment: {
			...ASSIGNMENT, workId: "43c55d4b-W1440", generation: 2,
		} }), /UNIQUE constraint failed/,
		"the schema admitted two different claims for one runtime attempt");
	} finally {
		store.close();
	}
});

test("W2929 re-review: an exact observation replays after the axis advances",
	() => {
		const store = open();
		try {
			activated(store);
			const first = { incarnation: "adapter-1", seq: 1 };
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "running", source: first });
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "quiescent", source: { incarnation: "adapter-1", seq: 2 } });
			const replay = observe(store, { attemptId: ATTEMPT,
				axis: "execution_runtime", value: "running", source: first });
			assert.equal(replay.replayed, true,
				"the durable duplicate was re-decided against today's axis state");
			assert.equal(row(store).execution_runtime, "quiescent");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: a conflicting duplicate refuses even at an inert value",
	() => {
		const store = open();
		try {
			activated(store);
			const source = { incarnation: "adapter-1", seq: 1 };
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "running", source });
			assert.throws(() => observe(store, { attemptId: ATTEMPT,
				axis: "consent_runtime", value: "not-started", source }),
				(error) => error instanceof ContractError
					&& error.code === "state-regression",
				"the current-value shortcut hid a different observation under one source identity");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: multiplicity discovered after uncertainty still cancels",
	() => {
		const store = open();
		try {
			activated(store);
			assert.equal(reconcileRuntime(store, adapter(), {
				attemptId: ATTEMPT }).decision, "uncertain");
			const labels = runtimeLabels(row(store));
			const answer = reconcileRuntime(store, adapter({ list: () => [
				{ runtimeId: "runtime-1", labels },
				{ runtimeId: "runtime-2", labels },
			] }), { attemptId: ATTEMPT });
			assert.equal(answer.decision, "cancel",
				"an earlier ambiguous inspection disabled later mismatch cancellation");
			assert.equal(row(store).execution_runtime, "cancel-requested");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: a concurrent different attachment enters cancellation",
	() => {
		const path = storePath();
		const first = open(path);
		const second = new ControlStore(path, { incarnation: "manager-2",
			clock: () => "2026-08-22T12:00:01.000Z" });
		try {
			activated(first);
			const labels = runtimeLabels(row(first));
			const answer = reconcileRuntime(first, adapter({ list: () => {
				reconcileRuntime(second, adapter({ list: () => [
					{ runtimeId: "runtime-2", labels },
				] }), { attemptId: ATTEMPT });
				return [{ runtimeId: "runtime-1", labels }];
			} }), { attemptId: ATTEMPT });
			assert.equal(answer.decision, "cancel",
				"the stale attachment surfaced an operation collision instead of the runtime mismatch");
			assert.equal(row(first).runtime_id, "runtime-2");
			assert.equal(row(first).execution_runtime, "cancel-requested");
		} finally {
			first.close();
			second.close();
		}
	});

test("W2929 re-review: a storage failure is not reported as a stale observation",
	() => {
		const store = open();
		try {
			activated(store);
			store.db.exec("CREATE TRIGGER observation_failure BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT, 'synthetic storage failure'); END");
			assert.throws(() => observe(store, { attemptId: ATTEMPT,
				axis: "execution_runtime", value: "running",
				source: { incarnation: "adapter-1", seq: 1 } }),
				(error) => /synthetic storage failure/.test(error.message)
					&& !(error instanceof ContractError
						&& error.category === "runtime-observation"
						&& error.code === "state-regression"),
				"a non-locking SQLite failure was rewritten as another writer's newer observation");
		} finally {
			store.close();
		}
	});

test("W2929 round-3 review: an inert observation still consumes its source id",
	() => {
		const store = open();
		try {
			activated(store);
			const source = { incarnation: "adapter-1", seq: 1 };
			observe(store, { attemptId: ATTEMPT, axis: "consent_runtime",
				value: "not-started", source });
			assert.throws(() => observe(store, { attemptId: ATTEMPT,
				axis: "execution_runtime", value: "running", source }),
				(error) => error instanceof ContractError
					&& error.code === "state-regression",
				"an accepted no-change observation left its source identity reusable");
		} finally {
			store.close();
		}
	});

test("W2929 round-3 review: multiplicity discovered while stopping still cancels",
	() => {
		const store = open();
		try {
			activated(store);
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "running" });
			observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
				value: "stopping" });
			const labels = runtimeLabels(row(store));
			const answer = reconcileRuntime(store, adapter({ list: () => [
				{ runtimeId: "runtime-1", labels },
				{ runtimeId: "runtime-2", labels },
			] }), { attemptId: ATTEMPT });
			assert.equal(answer.decision, "cancel",
				"the one omitted nonterminal state disabled mismatch cancellation");
		} finally {
			store.close();
		}
	});

test("W2929 round-3 review: the word busy is not SQLite contention", () => {
	const store = open();
	try {
		activated(store);
		store.db.exec("CREATE TRIGGER observation_busy_failure BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT, 'busy provider invariant'); END");
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "running",
			source: { incarnation: "adapter-1", seq: 1 } }),
			(error) => /busy provider invariant/.test(error.message)
				&& !(error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "state-regression"),
			"application prose containing 'busy' was classified as a database lock");
	} finally {
		store.close();
	}
});

test("W2929: attachment is decided by the DATABASE, not by the read", () => {
	// Mutation showed the JavaScript pre-check is not what decides this:
	// removing it leaves the SQL compare-and-swap refusing, which is the
	// same lesson as the offer slice's replay marker. So the case drives
	// the CAS directly — two connections, the second attaching between the
	// first's read and its write.
	const path = storePath();
	const first = open(path);
	const second = new ControlStore(path, { incarnation: "manager-2",
		clock: () => "2026-08-22T12:00:01.000Z" });
	try {
		activated(first);
		const labels = runtimeLabels(row(first));
		reconcileRuntime(first, adapter({ list: () => [
			{ runtimeId: "runtime-1", labels }] }), { attemptId: ATTEMPT });
		assert.equal(row(first).runtime_id, "runtime-1");
		// A second manager, reading the same attempt, cannot re-point it.
		const changed = second.db.prepare(
			"UPDATE attempts SET runtime_id=? WHERE runtime_attempt_id=? "
			+ "AND (runtime_id IS NULL OR runtime_id = ?)")
			.run("runtime-2", ATTEMPT, "runtime-2").changes;
		assert.equal(changed, 0,
			"the attachment CAS admitted a different runtime");
		assert.equal(row(second).runtime_id, "runtime-1");
	} finally {
		first.close();
		second.close();
	}
});

test("W2929: a store written before the index still fails CLOSED", () => {
	// The unique index makes two claimed offers per attempt impossible
	// going forward. The fail-closed read exists for a store written
	// BEFORE it — and last round I called exactly this branch
	// "unwitnessable by construction", which was wrong because the
	// construction was a property of the allocator and not of the store.
	// An invariant only the writer maintains is not one, so the reader
	// checks and this case builds the store the reader is defending
	// against.
	const store = open();
	try {
		attempt(store);
		claimed(store);
		store.db.exec("DROP INDEX offers_one_per_attempt");
		claimed(store, { assignment: { ...ASSIGNMENT,
		                               workId: "43c55d4b-W1440",
		                               generation: 2 } });
		assert.throws(() => activateAssignment(store, session(), {
			attemptId: ATTEMPT, expect: ASSIGNMENT }),
			(error) => error instanceof ContractError
				&& /2 claimed offers/.test(error.message),
			"activation chose one of two claims by row order");
		assert.equal(row(store).assignment_generation, null);
	} finally {
		store.close();
	}
});

test("W2929: attaching the SAME runtime twice is one act, not a collision", () => {
	// The other side of the attach identity. A second inspection finding
	// the runtime already attached must answer "attached", not refuse —
	// and it must not write again.
	const store = open();
	try {
		activated(store);
		const labels = runtimeLabels(row(store));
		const api = adapter({ list: () => [{ runtimeId: "runtime-1", labels }] });
		assert.equal(reconcileRuntime(store, api,
			{ attemptId: ATTEMPT }).decision, "attached");
		const seq = row(store).observation_seq;
		assert.equal(reconcileRuntime(store, api,
			{ attemptId: ATTEMPT }).decision, "attached");
		assert.equal(row(store).runtime_id, "runtime-1");
		assert.equal(row(store).observation_seq, seq,
			"a repeat attachment advanced the observation sequence");
	} finally {
		store.close();
	}
});

// -- round-3 correction: the other side of each -----------------------------

test("W2929: an inert sourced observation still replays exactly", () => {
	const store = open();
	try {
		activated(store);
		const source = { incarnation: "adapter-1", seq: 1 };
		const first = observe(store, { attemptId: ATTEMPT,
			axis: "consent_runtime", value: "not-started", source });
		assert.equal(first.changed, false);
		// Consuming the identity must not turn the repeat into a conflict:
		// the SAME observation is still the same observation.
		const again = observe(store, { attemptId: ATTEMPT,
			axis: "consent_runtime", value: "not-started", source });
		assert.equal(again.replayed, true,
			"the consumed identity refused its own exact repeat");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM observations WHERE "
			+ "runtime_attempt_id = ?").get(ATTEMPT).n, 1,
			"the replay wrote a second row for one source identity");
	} finally {
		store.close();
	}
});

test("W2929: cancelling an in-flight stop does not rewind the axis", () => {
	const store = open();
	try {
		activated(store);
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "running" });
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "stopping" });
		const seq = row(store).observation_seq;
		const labels = runtimeLabels(row(store));
		reconcileRuntime(store, adapter({ list: () => [
			{ runtimeId: "runtime-1", labels },
			{ runtimeId: "runtime-2", labels },
		] }), { attemptId: ATTEMPT });
		// The DECISION is the safety response; the axis says where the
		// runtime is, and it is further along than the request to stop it.
		assert.equal(row(store).execution_runtime, "stopping",
			"the cancellation rewrote a stopping runtime as merely requested");
		assert.equal(row(store).observation_seq, seq,
			"re-announcing an in-flight stop advanced the observation sequence");
	} finally {
		store.close();
	}
});

test("W2929: a genuinely locked database IS reported as contention", () => {
	const path = storePath();
	const store = open(path);
	const other = new ControlStore(path, { incarnation: "manager-2",
		clock: () => "2026-08-22T12:00:01.000Z" });
	try {
		activated(store);
		// A real write lock held by another connection — the one condition
		// this boundary translates, driven rather than described.
		other.db.exec("BEGIN IMMEDIATE");
		other.db.prepare("UPDATE attempts SET observed_at = ? WHERE "
			+ "runtime_attempt_id = ?").run("2026-08-22T12:00:01.000Z", ATTEMPT);
		assert.throws(() => observe(store, { attemptId: ATTEMPT,
			axis: "execution_runtime", value: "running",
			source: { incarnation: "adapter-1", seq: 1 } }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "state-regression",
			"a locked database was not translated as another writer deciding");
		other.db.exec("ROLLBACK");
	} finally {
		other.close();
		store.close();
	}
});

// -- cancellation ordering ---------------------------------------------------
//
// The whole content of these cases is WHICH BOUNDARY WAS REACHED FIRST.
// Final state cannot express it: a manager that stopped the runtime and then
// fenced the generation leaves exactly the same rows behind as one that
// fenced and then stopped. So the two doubles write into one shared trace.

test("W2929: the authority FENCES before the runtime is told to stop", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace });
		running(store, api);
		const runtime = adapter({ trace });
		const answer = requestCancellation(store, api, agent({ trace }), runtime,
			{ attemptId: ATTEMPT, reason: "operator" });
		assert.deepEqual(trace.map(([what]) => what),
			["authority.cancel", "agent.cancel", "adapter.stop"],
			"the pinned order is fence, then agent, then runtime");
		assert.equal(answer.ordered, true);
		assert.equal(answer.runtimeId, "runtime-1");
		assert.equal(row(store).execution_runtime, "cancel-requested");
	} finally {
		store.close();
	}
});

test("W2929: a refused fence stops nothing and moves no axis", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace, cancel: () => {
			throw new ContractError("stale-assignment", "ended",
				"that generation is already over");
		} });
		running(store, api);
		const runtime = adapter({ trace });
		assert.throws(() => requestCancellation(store, api, agent({ trace }), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment");
		assert.deepEqual(trace.map(([what]) => what), ["authority.cancel"],
			"the agent or the runtime was ordered although the authority "
			+ "refused to fence");
		assert.equal(row(store).execution_runtime, "running",
			"the axis announced a cancellation the authority never made");
	} finally {
		store.close();
	}
});

test("W2929: the cancellation INTENT survives an authority that never answers",
	() => {
		const path = storePath();
		const store = open(path);
		try {
			const api = session({ cancel: () => { throw new Error("transport"); } });
			running(store, api);
			const operationId = cancelOperationId(row(store));
			assert.throws(() => requestCancellation(store, api, agent(), adapter(),
				{ attemptId: ATTEMPT }), /transport/);
			// A state column would record only that somebody once intended
			// to cancel. The journal is what the next incarnation reads.
			const journalled = store.db.prepare(
				"SELECT kind, state FROM operations WHERE operation_id = ?")
				.get(operationId);
			assert.deepEqual({ ...journalled },
				{ kind: "attempt.cancel", state: "committed" },
				"nothing durable named the cancellation this manager began");
		} finally {
			store.close();
		}
	});

test("W2929: a restart submits the SAME cancellation, not a second one", () => {
	const path = storePath();
	const first = open(path);
	const second = new ControlStore(path, { incarnation: "manager-2",
		clock: () => "2026-08-22T12:00:01.000Z" });
	try {
		const trace = [];
		const api = session({ trace });
		running(first, api);
		requestCancellation(first, api, agent({ trace }), adapter({ trace }),
			{ attemptId: ATTEMPT, reason: "operator" });
		// A second incarnation, reading only the store.
		requestCancellation(second, api, agent({ trace }), adapter({ trace }),
			{ attemptId: ATTEMPT, reason: "operator" });
		const submitted = trace
			.filter(([what]) => what === "authority.cancel")
			.map(([, operands]) => operands.operationId);
		assert.equal(submitted.length, 2);
		assert.equal(submitted[0], submitted[1],
			"the restart asked the authority to fence a second time");
		assert.equal(submitted[0], authorityCancelOperationId(row(first)));
	} finally {
		first.close();
		second.close();
	}
});

test("W2929: the two journals do not share one operation identity", () => {
	const store = open();
	try {
		running(store);
		const attempt = row(store);
		// §4.2: success at one boundary does not imply success at the other.
		// One shared string would invite reading either journal's row as
		// evidence of the other's.
		assert.notEqual(cancelOperationId(attempt),
			authorityCancelOperationId(attempt));
	} finally {
		store.close();
	}
});

test("W2929: the adapter is told which act it is settling", () => {
	const store = open();
	try {
		const runtime = adapter();
		running(store);
		const operationId = cancelOperationId(row(store));
		requestCancellation(store, session(), agent(), runtime, { attemptId: ATTEMPT });
		const [, operands] = runtime.calls.find(([what]) => what === "stop");
		assert.equal(operands.operationId, operationId);
		assert.equal(operands.runtimeId, "runtime-1");
	} finally {
		store.close();
	}
});

test("W2929 review: ordering a stop is not proof the runtime stopped", () => {
	const store = open();
	try {
		running(store);
		const runtime = adapter({ stop: () => ({ stopped: false,
			why: "the runtime is still running" }) });
		const answer = requestCancellation(store, session(), agent(), runtime,
			{ attemptId: ATTEMPT });
		assert.notEqual(answer.stopped, true,
			"calling the stop boundary manufactured positive stopped evidence");
		assert.equal(row(store).execution_runtime, "cancel-requested");
	} finally {
		store.close();
	}
});

test("W2929: cancellation needs an exact generation to fence", () => {
	const store = open();
	try {
		attempt(store);
		claimed(store);
		const runtime = adapter();
		assert.throws(() => requestCancellation(store, session(), agent(), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(runtime.calls.length, 0);
	} finally {
		store.close();
	}
});

test("W2929: a foreign session cannot cancel this attempt's assignment", () => {
	const store = open();
	try {
		const trace = [];
		running(store);
		const foreign = session({ participant: "poc.other", trace });
		const runtime = adapter({ trace });
		assert.throws(() => requestCancellation(store, foreign, agent({ trace }), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "capability");
		assert.deepEqual(trace, [],
			"a session for somebody else reached the authority");
		assert.equal(row(store).execution_runtime, "running");
	} finally {
		store.close();
	}
});

test("W2929: with no runtime attached the generation is still fenced", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace });
		activated(store, api);
		const runtime = adapter({ trace });
		const answer = requestCancellation(store, api, agent({ trace }), runtime,
			{ attemptId: ATTEMPT });
		assert.equal(answer.ordered, false);
		assert.deepEqual(trace.map(([what]) => what), ["authority.cancel"]);
		assert.equal(row(store).execution_runtime, "cancel-requested",
			"a fenced assignment left its runtime axis saying not-started");
	} finally {
		store.close();
	}
});

test("W2929: a destroyed runtime is fenced with nothing left to stop", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace });
		running(store, api);
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "destroyed" });
		const runtime = adapter({ trace });
		const answer = requestCancellation(store, api, agent({ trace }), runtime,
			{ attemptId: ATTEMPT });
		assert.deepEqual(trace.map(([what]) => what), ["authority.cancel"]);
		assert.equal(answer.ordered, false);
		// The terminal axis is not rewound to announce an order nobody can
		// carry out — the round-3 rule, from the acting side.
		assert.equal(row(store).execution_runtime, "destroyed");
	} finally {
		store.close();
	}
});

test("W2929: an in-flight stop is re-ordered without rewinding the axis", () => {
	const store = open();
	try {
		const api = session();
		running(store, api);
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "stopping" });
		const seq = row(store).observation_seq;
		const runtime = adapter();
		const answer = requestCancellation(store, api, agent(), runtime,
			{ attemptId: ATTEMPT });
		assert.equal(answer.ordered, true,
			"a stop already in flight was taken as a reason not to order one");
		assert.equal(row(store).execution_runtime, "stopping");
		assert.equal(row(store).observation_seq, seq);
	} finally {
		store.close();
	}
});

test("W2929: the whole cancellation, against a real authority", () => {
	// A double can agree with an implementation about a shape neither shares
	// with the authority. This drives the real `V12Session.cancel`, so the
	// fence, the ended assignment and the typed gate are the authority's own.
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	const store = open(join(root, "control.sqlite3"));
	try {
		authority.certifyContract(V12);
		authority.addRouteHandler("impl", WHO);
		authority.createWork({ workId: WORK, route: "impl", contract: V12 });
		const api = authority.session(WHO);
		const assignment = api.claim({ workId: WORK, operationId: "claim-1" });
		attempt(store);
		claimed(store, { assignment });
		activateAssignment(store, api, { attemptId: ATTEMPT,
			expect: assignment });
		const runtime = adapter({ list: () => [
			{ runtimeId: "runtime-1", labels: runtimeLabels(row(store)) }] });
		requestRuntimeStart(store, runtime, { attemptId: ATTEMPT });
		requestCancellation(store, api, agent(), runtime,
			{ attemptId: ATTEMPT, reason: "operator" });
		const work = api.projectWork(WORK);
		assert.equal(work.handler, null, "the assignment did not end");
		assert.equal(work.phase, "block");
		assert.deepEqual({ ...work.gate }, {
			kind: "runtime-quiescence",
			detail: String(assignment.generation),
			token: `runtime-quiescence:${assignment.generation}` });
		// And the manager's own record of the same act is separate.
		assert.equal(api.operationRecord(
			authorityCancelOperationId(row(store))).state, "committed");
		assert.equal(store.db.prepare(
			"SELECT state FROM operations WHERE operation_id = ?")
			.get(cancelOperationId(row(store))).state, "committed");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: the settlements are passed through, not summarized", () => {
	const store = open();
	try {
		running(store);
		const answer = requestCancellation(store, session(),
			agent({ cancel: () => ({ cancelled: false, why: "mid-turn" }) }),
			adapter({ stop: () => ({ stopped: false, why: "still running" }) }),
			{ attemptId: ATTEMPT });
		// ORDERED is what the manager knows. What each boundary answered is
		// reported as the boundary gave it — the manager has no basis for
		// turning either into a fact about the world.
		assert.equal(answer.ordered, true);
		assert.deepEqual(answer.agentSettlement,
			{ cancelled: false, why: "mid-turn" });
		assert.deepEqual(answer.runtimeSettlement,
			{ stopped: false, why: "still running" });
		assert.equal(row(store).execution_runtime, "cancel-requested",
			"a negative settlement was folded into the axis");
	} finally {
		store.close();
	}
});

test("W2929 re-review: agent cancellation failure cannot suppress runtime stop",
	() => {
		const store = open();
		try {
			const trace = [];
			const api = session({ trace });
			running(store, api);
			const broken = agent({ trace, cancel: () => {
				throw new Error("agent transport failed");
			} });
			const runtime = adapter({ trace });
			assert.throws(() => requestCancellation(store, api, broken, runtime,
				{ attemptId: ATTEMPT }), /agent transport failed/);
			assert.deepEqual(trace.map(([what]) => what),
				["authority.cancel", "agent.cancel", "adapter.stop"],
				"an unreachable agent prevented the fenced runtime from being stopped");
			assert.equal(row(store).execution_runtime, "cancel-requested");
		} finally {
			store.close();
		}
	});

test("W2929: the agent is told which act it is settling", () => {
	const store = open();
	try {
		running(store);
		const talker = agent();
		const operationId = cancelOperationId(row(store));
		requestCancellation(store, session(), talker, adapter(),
			{ attemptId: ATTEMPT });
		const [, operands] = talker.calls.find(([what]) => what === "cancel");
		assert.equal(operands.operationId, operationId);
		assert.equal(operands.runtimeId, "runtime-1");
		assert.deepEqual(operands.assignment, ASSIGNMENT);
	} finally {
		store.close();
	}
});

test("W2929: a swapped agent and runtime refuse rather than mis-ordering", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace });
		running(store, api);
		// The parameter order IS the act order, and two adjacent injected
		// objects are easy to swap. A swap must not cancel the wrong
		// boundary first.
		assert.throws(() => requestCancellation(store, api,
			adapter({ trace }), agent({ trace }), { attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
		assert.deepEqual(trace, [], "a swapped boundary was still reached");
		assert.equal(row(store).execution_runtime, "running");
	} finally {
		store.close();
	}
});

test("W2929: a failing runtime stop does not hide a failing agent", () => {
	const store = open();
	try {
		const trace = [];
		const api = session({ trace });
		running(store, api);
		// Both post-fence boundaries fail. Neither may hide the other, and
		// choosing between them would be the manager deciding which failure
		// the caller is entitled to see.
		const broken = agent({ trace, cancel: () => {
			throw new Error("agent transport failed"); } });
		const runtime = adapter({ trace, stop: () => {
			throw new Error("runtime daemon failed"); } });
		assert.throws(() => requestCancellation(store, api, broken, runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof AggregateError
				&& error.errors.length === 2
				&& /agent transport failed/.test(error.errors[0].message)
				&& /runtime daemon failed/.test(error.errors[1].message));
		assert.deepEqual(trace.map(([what]) => what),
			["authority.cancel", "agent.cancel", "adapter.stop"]);
	} finally {
		store.close();
	}
});

test("W2929: a failed agent cancellation is re-thrown UNCHANGED, after the stop",
	() => {
	const store = open();
	try {
		running(store);
		const broken = agent({ cancel: () => {
			throw new Error("agent transport failed"); } });
		const runtime = adapter();
		// The failure is re-thrown UNCHANGED — it is the caller's to
		// classify, not this boundary's — and it is not wrapped or
		// relabelled on the way out.
		assert.throws(() => requestCancellation(store, session(), broken,
			runtime, { attemptId: ATTEMPT }),
			(error) => !(error instanceof AggregateError)
				&& !(error instanceof ContractError)
				&& error.message === "agent transport failed");
		// The stop was still ordered, under the manager's own identity.
		const [, operands] = runtime.calls.find(([what]) => what === "stop");
		assert.equal(operands.runtimeId, "runtime-1");
	} finally {
		store.close();
	}
});

test("W2929 round-3 review: a null agent failure is still a failure", () => {
	const store = open();
	try {
		running(store);
		const broken = agent({ cancel: () => { throw null; } });
		const runtime = adapter();
		const notThrown = Symbol("not thrown");
		let escaped = notThrown;
		try {
			requestCancellation(store, session(), broken, runtime,
				{ attemptId: ATTEMPT });
		} catch (failure) {
			escaped = failure;
		}
		assert.notEqual(escaped, notThrown,
			"throw null was mistaken for the no-failure sentinel");
		assert.equal(escaped, null, "the agent failure was not re-thrown unchanged");
		assert.equal(runtime.calls.some(([what]) => what === "stop"), true,
			"the null failure suppressed the runtime stop");
	} finally {
		store.close();
	}
});

test("W2929: a null agent failure is still retained beside a runtime failure",
	() => {
		const store = open();
		try {
			running(store);
			// The other half of the sentinel: a thrown `null` must survive
			// INTO the aggregate, not just out of the single-failure path.
			const broken = agent({ cancel: () => { throw null; } });
			const runtime = adapter({ stop: () => {
				throw new Error("runtime daemon failed"); } });
			assert.throws(() => requestCancellation(store, session(), broken,
				runtime, { attemptId: ATTEMPT }),
				(error) => error instanceof AggregateError
					&& error.errors.length === 2
					&& error.errors[0] === null
					&& /runtime daemon failed/.test(error.errors[1].message));
		} finally {
			store.close();
		}
	});

test("W2929: an undefined agent failure is a failure too", () => {
	const store = open();
	try {
		running(store);
		// `undefined` is the other value a boundary can throw that a
		// value-shaped sentinel would swallow, and it is what an
		// uninitialized variable already holds.
		const broken = agent({ cancel: () => { throw undefined; } });
		const runtime = adapter();
		const notThrown = Symbol("not thrown");
		let escaped = notThrown;
		try {
			requestCancellation(store, session(), broken, runtime,
				{ attemptId: ATTEMPT });
		} catch (failure) {
			escaped = failure;
		}
		assert.equal(escaped, undefined,
			"throw undefined was mistaken for no failure at all");
		assert.equal(runtime.calls.some(([what]) => what === "stop"), true,
			"the undefined failure suppressed the runtime stop");
	} finally {
		store.close();
	}
});

test("W2929: a settlement of nothing is passed through as nothing", () => {
	const store = open();
	try {
		running(store);
		// My own sweep for the round-3 shape, not a review finding: `?? null`
		// collapsed "the boundary returned nothing" into "the boundary
		// returned null", which is the same mistake one size smaller — and it
		// contradicted the comment claiming the settlements are un-summarized.
		const answer = requestCancellation(store, session(),
			agent({ cancel: () => undefined }),
			adapter({ stop: () => null }), { attemptId: ATTEMPT });
		assert.equal(answer.ordered, true);
		assert.equal(Object.hasOwn(answer, "agentSettlement"), true);
		assert.equal(answer.agentSettlement, undefined,
			"a boundary that returned nothing was reported as returning null");
		assert.equal(answer.runtimeSettlement, null,
			"a boundary that returned null was not reported verbatim");
	} finally {
		store.close();
	}
});
