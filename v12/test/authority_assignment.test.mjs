// W2928: assignment identity, generation allocation, capacity, the ONE
// assignment-ending helper, cancellation and the typed gates.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-assignment-authority`,
// implementing `SPEC.md` version `1-ruled`.
//
// These run against the REAL authority through its public boundary. The
// W151 evidence model proves the design is coherent; these prove this
// implementation is the thing the design describes.

import { test, after } from "node:test";
import assert from "node:assert/strict";

import { V11, V12 } from "../src/authority/index.mjs";
import { CLAUDE, CLOSER, GEMINI, OTHER, UUID, WORK, candidate, claimedV12,
         cleanup, deployment, refusalMessage } from "./authority_fixture.mjs";

after(cleanup);

test("W2928: a v12 claim returns the full four-part assignment identity", () => {
	const { as, authority, assignment } = claimedV12();
	// §4: exactly (authority UUID, full Work ID, participant, positive
	// generation). Not a local selector, and not a participant alone.
	assert.deepEqual({ ...assignment }, {
		authorityUuid: UUID, workId: WORK, participant: CLAUDE, generation: 1,
	});
	assert.equal(typeof assignment.generation, "number");
	assert.ok(assignment.generation > 0);
	const projected = authority.projectWork(WORK);
	assert.deepEqual({ ...projected.assignment }, { ...assignment });
	assert.equal(projected.phase, "active");
	assert.equal(projected.handler, CLAUDE);
	authority.assertInvariants(WORK);
});

test("W2928: a v11 claim mints NO generation", () => {
	// Ruling 3 narrowed the parent generation ruling: minting is
	// contract-conditional. The consequence is explicit and is not an
	// oversight — under v11 two consecutive claims by one participant are
	// indistinguishable, which is the defect contract progression fixes.
	const { as, authority } = deployment();
	const assignment = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v11" });
	assert.equal(assignment.generation, null);
	assert.equal(authority.projectWork(WORK).generationCounter, 0);
	authority.assertInvariants(WORK);
});

test("W2928: the generation counter is monotonic and never reused", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).end({ expect: assignment, operationId: "end:1", reason: "handed back" });
	const second = as(CLAUDE).claim({ workId: WORK, operationId: "claim:2" });
	assert.equal(second.generation, 2);
	as(second.participant).end({ expect: second, operationId: "end:2", reason: "again" });
	const third = as(GEMINI).claim({ workId: WORK, operationId: "claim:3" });
	assert.equal(third.generation, 3);
	// Ending an assignment invalidates it WITHOUT resetting, decrementing
	// or reusing its generation (§10.1, §10.6).
	assert.equal(authority.projectWork(WORK).generationCounter, 3);
	authority.assertInvariants(WORK);
});

test("W2928: a participant holds ONE live claim across the whole deployment", () => {
	// §10.2. Capacity is deployment-wide, not per Work, and it is checked
	// inside the claim write transaction.
	const { as, authority } = deployment({
		contract: V12, works: [[WORK, "impl"], [OTHER, "impl"]] });
	as(CLAUDE).claim({ workId: WORK, operationId: "claim:a" });
	assert.match(
		refusalMessage(() => as(CLAUDE).claim({ workId: OTHER, operationId: "claim:b" })),
		/already holds full-W1; a participant holds ONE active claim/);
	// A DIFFERENT participant is unaffected: capacity is per participant.
	const other = as(GEMINI).claim({ workId: OTHER, operationId: "claim:c" });
	assert.equal(other.generation, 1, "each Work counts its own generations");
	authority.assertInvariants(WORK);
	authority.assertInvariants(OTHER);
});

test("W2928: a competing claim loses atomically and the winner is unaffected", () => {
	const { as, authority } = deployment({ contract: V12 });
	const won = as(CLAUDE).claim({ workId: WORK, operationId: "claim:winner" });
	assert.match(
		refusalMessage(() => as(GEMINI).claim({ workId: WORK, operationId: "claim:loser" })),
		/Work is already claimed/);
	// The loser minted nothing: the counter is the winner's generation and
	// no second slot was taken.
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	assert.deepEqual({ ...authority.assignmentOf(WORK) }, { ...won });
	assert.equal(authority.slotHolder(GEMINI), null);
	// An ordinary refusal writes NOTHING and stays retryable, so the loser
	// may try again once the Work is free — with the same operation id.
	as(won.participant).end({ expect: won, operationId: "end:winner", reason: "done" });
	const later = as(GEMINI).claim({ workId: WORK, operationId: "claim:loser" });
	assert.equal(later.generation, 2);
});

test("W2928: the route decides who may claim, not the caller", () => {
	const { as, authority } = deployment({ contract: V12 });
	assert.match(
		refusalMessage(() => as("poc.stranger").claim({ workId: WORK, operationId: "claim:x" })),
		/route impl does not resolve to poc\.stranger/);
	authority.assertInvariants(WORK);
});

test("W2928: every assignment-owned act compare-and-swaps the FULL identity", () => {
	const { as, authority, assignment } = claimedV12();
	// §8: participant equality is insufficient. Each of these differs from
	// the live assignment in exactly one part.
	const wrong = [
		["generation", { ...assignment, generation: 2 }],
		["participant", { ...assignment, participant: GEMINI }],
		["work", { ...assignment, workId: OTHER }],
		["authority", { ...assignment, authorityUuid: "another-authority" }],
	];
	for (const [part, expect] of wrong) {
		assert.throws(
			() => as(CLAUDE).activity({ expect, key: `k-${part}` }),
			// The session refuses a wrong PARTICIPANT before the authority sees
			// it — a session acts only on its own assignments — and the
			// authority refuses the other three.
			(error) => /stale assignment|another-authority|no such Work|this session acts for/
				.test(error.message),
			`a wrong ${part} was accepted`);
	}
	// And a participant alone is refused as an identity at all, rather than
	// being completed from current state.
	assert.match(
		refusalMessage(() => as(CLAUDE).activity({
			expect: { participant: CLAUDE }, key: "k" })),
		/must be the full four-part identity/);
	assert.deepEqual(authority.activities(WORK), []);
	assert.deepEqual({ ...as(assignment.participant).activity({ expect: assignment, key: "k" }) }.action_key, "k");
});

test("W2928: an ended generation can never act again, even for the same participant", () => {
	// The immediate-successor race: the same participant releases
	// generation 1 and claims generation 2, so `handler == participant`
	// still matches while the stale act must not.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).end({ expect: assignment, operationId: "end:1", reason: "handed back" });
	const successor = as(CLAUDE).claim({ workId: WORK, operationId: "claim:2" });
	assert.equal(authority.projectWork(WORK).handler, CLAUDE, "same participant");
	assert.match(
		refusalMessage(() => as(assignment.participant).activity({ expect: assignment, key: "late" })),
		/stale assignment/);
	assert.match(
		refusalMessage(() => as(assignment.participant).publish({ expect: assignment, proposalId: "p-late", ...candidate("late"),
			operationId: "pub:late" })),
		/stale assignment/);
	// The successor works normally.
	as(successor.participant).activity({ expect: successor, key: "fresh" });
	assert.equal(authority.activities(WORK).length, 1);
});

test("W2928: cancellation fences the generation and ends the assignment together", () => {
	// Ruling 1. There is no observable window between the two facts: the
	// Work is `block` behind a typed gate with NO Handler, never `active`
	// while nobody may execute it.
	const { as, authority, assignment } = claimedV12();
	const result = as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "runtime lost" });
	assert.equal(result.fenced, true);
	assert.equal(result.gate, "runtime-quiescence:1");
	const work = authority.projectWork(WORK);
	assert.equal(work.phase, "block");
	assert.equal(work.handler, null);
	assert.equal(work.assignment, null);
	assert.equal(work.gate.kind, "runtime-quiescence");
	assert.deepEqual(work.fencedGenerations,
		[{ generation: 1, cause: "cancelled", reason: "runtime lost" }]);
	// Every capability of that generation is dead, and the refusal says
	// FENCED rather than merely stale — the assignment is gone for good.
	for (const act of [
		() => as(assignment.participant).activity({ expect: assignment, key: "late" }),
		() => as(assignment.participant).publish({ expect: assignment, proposalId: "p",
			...candidate("d"), operationId: "pub:late" }),
		() => as(assignment.participant).end({ expect: assignment, operationId: "end:late" }),
	]) {
		assert.match(refusalMessage(act), /fenced and ended/);
	}
	authority.assertInvariants(WORK);
});

test("W2928: cancellation frees the participant's one global claim slot", () => {
	// The whole point of ending the assignment rather than retaining
	// Handler: the participant is not taken offline for every other Route
	// while one Work waits for its runtime to be proven gone.
	const { as, authority, assignment } = claimedV12({
		works: [[WORK, "impl"], [OTHER, "impl"]] });
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	assert.equal(authority.slotHolder(CLAUDE), null);
	const elsewhere = as(CLAUDE).claim({ workId: OTHER, operationId: "claim:other" });
	assert.equal(elsewhere.participant, CLAUDE);
	// …while the cancelled Work stays gated.
	assert.equal(authority.projectWork(WORK).gate.token, "runtime-quiescence:1");
	assert.equal(authority.projectWork(WORK).ready, false);
});

test("W2928: no successor claims while the quiescence gate holds", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	assert.match(
		refusalMessage(() => as(GEMINI).claim({ workId: WORK, operationId: "claim:successor" })),
		/blocked by runtime-quiescence:1/);
	assert.equal(authority.projectWork(WORK).generationCounter, 1,
		"a refused claim mints nothing");
});

test("W2928: an unreachable runtime is not a dead one", () => {
	// §10.8. `quiescent` and `uncertain` are observations; only positive
	// absence — or an explicitly pinned certified-isolation clause —
	// releases the replacement.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	const gate = "runtime-quiescence:1";
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate, evidence: { kind: "runtime-uncertain" },
			operationId: "gate:guess" })),
		/replacement is not permitted/);
	// The pinned clause is not pinned yet.
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate,
			evidence: { kind: "certified-isolation-policy", policy: "iso-1" },
			operationId: "gate:policy" })),
		/replacement is not permitted/);
	authority.setPolicy("isolation_certified", true);
	const satisfied = as(CLAUDE).satisfyGate({
		workId: WORK, gate,
		evidence: { kind: "certified-isolation-policy", policy: "iso-1" },
		operationId: "gate:policy-2" });
	assert.equal(satisfied.kind, "certified-isolation-policy");
	// The policy decision and its evidence are journalled BEFORE a
	// successor receives a fresh generation.
	assert.deepEqual(authority.gateEvidence(WORK).map((row) => row.evidence),
		[{ kind: "certified-isolation-policy", policy: "iso-1" }]);
	const successor = as(GEMINI).claim({ workId: WORK, operationId: "claim:successor" });
	assert.equal(successor.generation, 2);
	authority.assertInvariants(WORK);
});

test("W2928: positive absence satisfies the gate and must name the runtime", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate: "runtime-quiescence:1",
			evidence: { kind: "runtime-absent" }, operationId: "gate:vague" })),
		/must name the exact runtime it observed/);
	as(CLAUDE).satisfyGate({
		workId: WORK, gate: "runtime-quiescence:1",
		evidence: { kind: "runtime-absent", runtime: "container-9" },
		operationId: "gate:absent" });
	assert.equal(authority.projectWork(WORK).ready, true);
	assert.equal(as(GEMINI).claim({ workId: WORK, operationId: "claim:successor" }).generation, 2);
});

test("W2928: only the gate actually holding the Work can be satisfied", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate: "runtime-quiescence:99",
			evidence: { kind: "runtime-absent", runtime: "c" }, operationId: "gate:wrong" })),
		/that gate is not the one holding this Work/);
});

test("W2928: a plan rejection installs its gate atomically with the end", () => {
	// §11: the unchanged plan cannot be reoffered, because the gate is
	// installed in the same transaction that ends the assignment.
	const { as, authority, assignment } = claimedV12();
	const result = as(assignment.participant).rejectPlan({ expect: assignment, operationId: "plan:1", planDigest: "plan-a",
		reason: "the plan skips the regression" });
	assert.equal(result.gate, "plan-revision:plan-a");
	assert.equal(authority.projectWork(WORK).phase, "block");
	assert.equal(authority.projectWork(WORK).handler, null);
	// Rejection is not cancellation: no generation is fenced, because the
	// worker did nothing that must be invalidated.
	assert.deepEqual(authority.fencedGenerations(WORK), []);
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate: "plan-revision:plan-a",
			evidence: { kind: "revised-plan", plan_digest: "plan-a" },
			operationId: "gate:same" })),
		/cannot be satisfied by reoffering the rejected plan/);
	as(CLAUDE).satisfyGate({
		workId: WORK, gate: "plan-revision:plan-a",
		evidence: { kind: "revised-plan", plan_digest: "plan-b" },
		operationId: "gate:revised" });
	assert.equal(authority.projectWork(WORK).ready, true);
});

test("W2928: EVERY Handler-clear path goes through the one ending helper", () => {
	// §7's closing rule, and the reason it exists: v11 clears Handler in
	// six different places, so a fence added to `release` alone leaves five
	// doors open. Each path below is exercised on its own Work and must
	// leave the same three facts true.
	const paths = {
		release: ({ as }, assignment) =>
			as(CLAUDE).end({ expect: assignment, operationId: "op", reason: "r" }),
		pass: ({ as }, assignment) =>
			as(CLAUDE).pass({ expect: assignment, toRoute: "rview", operationId: "op",
				comment: "ready for review" }),
		cancel: ({ as }, assignment) =>
			as(CLAUDE).cancel({ expect: assignment, operationId: "op", reason: "r" }),
		"gate arrival": ({ as }, assignment) =>
			as(CLAUDE).installGate({ workId: WORK, gate: "runtime-quiescence:1",
				reason: "r", operationId: "op", expect: assignment }),
		"plan rejection": ({ as }, assignment) =>
			as(CLAUDE).rejectPlan({ expect: assignment, operationId: "op",
				planDigest: "p", reason: "r" }),
		"contract advance": ({ as }, assignment) =>
			as(CLAUDE).advanceContract({ expect: assignment, expectContract: V12,
				targetContract: V12, rationale: "r", operationId: "op" }),
		close: ({ as }, assignment) =>
			as(CLOSER).close({ workId: WORK, outcome: "satisfying", rationale: "r",
				operationId: "op", expect: assignment }),
	};
	for (const [name, act] of Object.entries(paths)) {
		const built = claimedV12();
		const { authority, assignment } = built;
		if (name === "contract advance") authority.permitContractTransition(V12, V12);
		act(built, assignment);
		const work = authority.projectWork(WORK);
		assert.equal(work.handler, null, `${name} left a Handler behind`);
		assert.equal(work.liveGeneration, null, `${name} left a live generation`);
		assert.equal(authority.slotHolder(CLAUDE), null,
			`${name} did not free the participant's claim slot`);
		assert.notEqual(work.phase, "active", `${name} left the Work active`);
		// The event names the ended assignment, so the journal answers "who
		// lost the Work and why" without inference.
		const [event] = authority.assignmentEvents(WORK).slice(-1);
		assert.equal(event.participant, CLAUDE, name);
		assert.equal(event.generation, 1, name);
		assert.ok(event.cause, name);
		authority.assertInvariants(WORK);
	}
});

test("W2928: a gate arrival on claimed Work needs the exact assignment", () => {
	const { as, authority, assignment } = claimedV12();
	assert.match(
		refusalMessage(() => as(CLAUDE).installGate({
			workId: WORK, gate: "runtime-quiescence:1", reason: "r",
			operationId: "gate-arrival:silent" })),
		/must supply the exact assignment identity/);
	// Unclaimed Work needs none: there is no assignment to end.
	as(assignment.participant).end({ expect: assignment, operationId: "end:1", reason: "r" });
	const installed = as(CLAUDE).installGate({
		workId: WORK, gate: "contract-runtime:v12-assignment-1", reason: "r",
		operationId: "gate-arrival:unclaimed" });
	assert.equal(installed.assignment, null);
	assert.equal(authority.projectWork(WORK).phase, "block");
});

test("W2928: Work phase carries only scheduler meaning", () => {
	// §10.7. Cancellation, quiescence and output are not phases; they
	// become at most ONE displayed typed gate, which is v11's `block`
	// mechanism rather than a new axis.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	const work = authority.projectWork(WORK);
	assert.ok(["queued", "active", "block", "parked"].includes(work.phase));
	assert.equal(work.phase, "block");
	assert.equal(work.gate.token, "runtime-quiescence:1");
	assert.equal(Object.keys(work).includes("runtime"), false,
		"the authority does not project a runtime state it is not authoritative for");
	assert.equal(Object.keys(work).includes("output"), false);
});

test("W2928: a public transition cannot commit an impossible scheduler state", () => {
	// Review 2026-08-22 [P1]. `createWork` accepted `phase="active"` and
	// `end` accepted a caller-supplied phase, so both committed
	// Handler-null/active rows through the public boundary and
	// `assertInvariants` reported it only after the corruption was durable.
	// Invariants are a backstop; the transition is where an impossible
	// state is refused.
	const { as, authority } = deployment({ contract: V12 });

	// Creation mints an UNCLAIMED Work, so `active` is not reachable: it
	// means exactly "a Handler holds it", and only `claim` reaches it.
	assert.match(
		refusalMessage(() => authority.createWork({
			workId: "full-W9", route: "impl", phase: "active" })),
		/a Work is created unclaimed/);
	assert.throws(() => authority.projectWork("full-W9"), /no such Work/,
		"the refused creation wrote a row anyway");

	// A gate is a REASON the Work cannot run, so the two halves must agree.
	assert.match(
		refusalMessage(() => authority.createWork({
			workId: "full-W9", route: "impl", phase: "block" })),
		/must name the one gate holding it/);
	assert.match(
		refusalMessage(() => authority.createWork({
			workId: "full-W9", route: "impl", gate: "runtime-quiescence:1" })),
		/cannot be installed with phase queued/);
	// And the token has to be a typed one with a detail, or nothing could
	// ever satisfy it: `satisfyGate` has no kind to check evidence against.
	for (const bad of ["nonsense", "nonsense:1", "runtime-quiescence:",
	                   "runtime-quiescence"]) {
		assert.match(
			refusalMessage(() => authority.createWork({
				workId: "full-W9", route: "impl", phase: "block", gate: bad })),
			/is not a typed gate token/, bad);
	}
	// The valid shapes still work.
	authority.createWork({ workId: "full-W9", route: "impl", phase: "block",
		gate: "contract-runtime:v12-assignment-1" });
	assert.equal(authority.projectWork("full-W9").phase, "block");
	authority.assertInvariants("full-W9");
	authority.createWork({ workId: "full-W10", route: "impl", phase: "parked" });
	authority.assertInvariants("full-W10");
});

test("W2928: `end` derives its outcome instead of accepting one", () => {
	// The other half of the same [P1]: `end({..., phase: "active"})` used to
	// commit a Handler-null active row. §7 gives every transition a DERIVED
	// scheduler outcome, and a caller that wants a gate uses the transition
	// that installs one.
	const { as, authority, assignment } = claimedV12();
	const released = as(assignment.participant).end({ expect: assignment, operationId: "end:1", reason: "handed back" });
	assert.equal(released.phase, "queued");
	assert.equal(released.gate, null);
	const work = authority.projectWork(WORK);
	assert.equal(work.phase, "queued");
	assert.equal(work.gate, null);
	authority.assertInvariants(WORK);

	// Strict operands: a caller that supplies `phase` and has it ignored
	// believes it chose the outcome, and that belief is what the corrected
	// transition removes.
	const supplied = claimedV12();
	assert.match(
		refusalMessage(() => supplied.as(supplied.assignment.participant).end({ expect: supplied.assignment, operationId: "end:p", phase: "active" })),
		/end does not take phase/);
	assert.equal(supplied.authority.projectWork(WORK).phase, "active");
	assert.equal(supplied.authority.operationRecord("end:p"), null);
	assert.match(
		refusalMessage(() => supplied.authority.createWork({
			workId: "full-W8", route: "impl", handler: CLAUDE })),
		/createWork does not take handler/);

	// A disposition that belongs to another transition is refused rather
	// than quietly producing that transition's name with this one's effect.
	const second = claimedV12();
	assert.match(
		refusalMessage(() => second.as(second.assignment.participant).end({ expect: second.assignment, operationId: "end:x",
			disposition: "cancelled", reason: "r" })),
		/is not a release disposition/);
	assert.equal(second.authority.projectWork(WORK).phase, "active");
	assert.equal(second.authority.operationRecord("end:x"), null,
		"the refusal journalled an operation");
	assert.deepEqual(second.authority.assignmentEvents(WORK), []);
});

test("W2928: a gate arrival validates its token before it writes", () => {
	const { as, authority, assignment } = claimedV12();
	assert.match(
		refusalMessage(() => as(CLAUDE).installGate({
			workId: WORK, gate: "made-up:1", reason: "r", operationId: "gate:bad",
			expect: assignment })),
		/is not a typed gate token/);
	// Nothing moved and nothing was journalled, so the identity is still
	// free for the correct call.
	const work = authority.projectWork(WORK);
	assert.equal(work.phase, "active");
	assert.equal(work.gate, null);
	assert.equal(authority.operationRecord("gate:bad"), null);
	as(CLAUDE).installGate({ workId: WORK, gate: "runtime-quiescence:1",
		reason: "r", operationId: "gate:bad", expect: assignment });
	assert.equal(authority.projectWork(WORK).gate.token, "runtime-quiescence:1");
	authority.assertInvariants(WORK);
});
