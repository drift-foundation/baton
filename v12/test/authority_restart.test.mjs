// W2928: restart and durability.
//
// The whole reason this authority is a real store rather than process
// memory. `SPEC.md` §9 is a table of "last durable boundary -> recovery
// rule", and every row of it assumes the authority remembers what it
// committed after the process that committed it is gone. These cases
// reopen the SAME file as a new process would and ask what survived.
//
// The accepted `0-spike` kept its issued/spent map in one manager
// process (§1, §2); that is the choice being replaced here, so proving
// durability is proving the supersession.

import { test, after } from "node:test";
import assert from "node:assert/strict";

import { V12Authority, V11, V12 } from "../src/authority/index.mjs";
import { APPROVER, CLAUDE, GEMINI, INTEGRATOR, OTHER, REVIEWER, UUID,
         VERIFIER, WORK, candidate, cleanup, deployment, restart,
         refusalMessage } from "./authority_fixture.mjs";

after(cleanup);

test("W2928: restart BEFORE the claim commits the fixed operation once", () => {
	// §9: "`accepted`, claim not known — submit/retry only the fixed claim
	// operation." The manager died before it learned anything; the
	// authorization is durable and the claim commits exactly once.
	const built = deployment({ contract: V12 });
	let authority = restart(built.authority, built.path);
	assert.equal(authority.operationRecord("claim:offer-1"), null,
		"nothing was committed before the restart");
	const first = authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-1" });
	assert.equal(first.generation, 1);
	// And a second restart replaying the same fixed operation mints
	// nothing further.
	authority = restart(authority, built.path);
	assert.deepEqual(authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-1" }), { ...first });
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	authority.assertInvariants(WORK);
	authority.dispose();
});

test("W2928: restart AFTER an ambiguous claim replays the same generation", () => {
	// §9: "claim may have committed — replay/query the exact claim
	// operation. Current participant alone cannot settle it."
	const built = deployment({ contract: V12 });
	const original = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-1" });
	const authority = restart(built.authority, built.path);
	// The read-only lookup settles it without mutating anything.
	assert.deepEqual(authority.operationResult("claim:offer-1"), { ...original });
	// And the replay is byte-identical rather than a second mint.
	assert.deepEqual(authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-1" }),
		{ ...original });
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	assert.deepEqual({ ...authority.assignmentOf(WORK) }, { ...original });
	authority.dispose();
});

test("W2928: a fence, a gate and a contract survive the restart", () => {
	const built = deployment({ contract: V12 });
	const assignment = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	built.authority.session(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "runtime unreachable" });
	const authority = restart(built.authority, built.path);
	const work = authority.projectWork(WORK);
	assert.equal(work.phase, "block");
	assert.equal(work.gate.token, "runtime-quiescence:1");
	assert.equal(work.contract, V12);
	assert.deepEqual(work.fencedGenerations,
		[{ generation: 1, cause: "cancelled", reason: "runtime unreachable" }]);
	// The fence still refuses the ended generation after the restart —
	// which is the point: a worker that outlived the manager cannot come
	// back and publish.
	assert.match(
		refusalMessage(() => authority.session(assignment.participant).publish({ expect: assignment, proposalId: "p", ...candidate("late"),
			operationId: "pub:late" })),
		/fenced and ended/);
	assert.equal(authority.slotHolder(CLAUDE), null,
		"the freed claim slot stayed freed");
	authority.assertInvariants(WORK);
	authority.dispose();
});

test("W2928: a retired identity is still dead after a restart", () => {
	const built = deployment({ contract: V12 });
	built.authority.session(CLAUDE).settleOperation({
		operationId: "claim:offer-1",
		signature: V12Authority.claimSignature(WORK, CLAUDE),
		reason: "the claim-settlement deadline passed",
		disposition: "settlement-expired", mayRetire: true });
	const authority = restart(built.authority, built.path);
	assert.equal(authority.operationRecord("claim:offer-1").state, "retired");
	assert.match(
		refusalMessage(() => authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-1" })),
		/claim-settlement deadline passed/);
	// And the disposition the retirement bound is still the one a later
	// entry path replays.
	assert.equal(authority.session(CLAUDE).settleOperation({
		operationId: "claim:offer-1",
		signature: V12Authority.claimSignature(WORK, CLAUDE),
		reason: "refused", disposition: "claim-refused", mayRetire: true })
		.record.disposition, "settlement-expired");
	authority.dispose();
});

test("W2928: a durable refusal is still a refusal after a restart", () => {
	const built = deployment({ contract: V12 });
	const assignment = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	built.authority.session(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("c1"), operationId: "pub:1" });
	built.authority.session(VERIFIER).verify({ proposalId: "p1", verificationId: "v1",
		 observation: "passed", operationId: "v:1" });
	built.authority.session(REVIEWER).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "r:1" });
	built.authority.session(APPROVER).approve({ proposalId: "p1", approvalId: "a1", 
		disposition: "approved", operationId: "a:1", policyGeneration: 7 });
	built.authority.setPolicy("canonical_target", "moved");
	assert.throws(() => built.authority.session(INTEGRATOR).integrate({
		proposalId: "p1", integrationId: "i1", 
		operationId: "int:1" }));
	const authority = restart(built.authority, built.path);
	assert.equal(authority.integrationAttempts("p1").length, 1);
	assert.match(
		refusalMessage(() => authority.session(INTEGRATOR).integrate({ proposalId: "p1",
			integrationId: "i1",  operationId: "int:1" })),
		/canonical target moved/);
	assert.equal(authority.integrationAttempts("p1").length, 1,
		"the post-restart retry appended a second attempt");
	authority.dispose();
});

test("W2928: a transaction that refuses leaves nothing behind", () => {
	// Fence and end commit TOGETHER (§10.5), so a refusal partway through
	// an ending path must leave neither. `close` is the sharpest case: it
	// fences, ends, and terminalizes, and a stale identity has to undo all
	// three.
	const built = deployment({ contract: V12 });
	const assignment = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	assert.throws(() => built.authority.close({
		workId: WORK, outcome: "satisfying", rationale: "done", actor: "poc.closer",
		operationId: "close:stale", expect: { ...assignment, generation: 5 } }));
	const authority = restart(built.authority, built.path);
	const work = authority.projectWork(WORK);
	assert.equal(work.status, "open");
	assert.equal(work.handler, CLAUDE);
	assert.equal(work.phase, "active");
	assert.deepEqual(work.fencedGenerations, []);
	assert.deepEqual(authority.assignmentEvents(WORK), []);
	assert.equal(authority.operationRecord("close:stale"), null);
	authority.assertInvariants(WORK);
	authority.dispose();
});

test("W2928: the authority UUID is durable and is never reassigned", () => {
	// Every assignment identity in this store names the original UUID, so
	// a store that answered to two of them would make `assignment_ref`
	// ambiguous — the one thing §4 says it must never be.
	const built = deployment({ contract: V12 });
	built.authority.dispose();
	assert.match(
		refusalMessage(() => V12Authority.open(built.path,
			{ authorityUuid: "a-different-authority" })),
		/is authority-uuid, not a-different-authority/);
	const authority = V12Authority.open(built.path);
	assert.equal(authority.authorityUuid, UUID);
	assert.equal(authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" }).authorityUuid, UUID);
	authority.dispose();
});

test("W2928: two Works over one durable store keep separate generations", () => {
	// The counter is PER WORK. One shared store is what makes the
	// deployment-wide claim slot and the per-Work counter observably
	// different things.
	const built = deployment({
		contract: V12, works: [[WORK, "impl"], [OTHER, "impl"]] });
	const mine = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:a" });
	const theirs = built.authority.session(GEMINI).claim({ workId: OTHER, operationId: "claim:b" });
	assert.equal(mine.generation, 1);
	assert.equal(theirs.generation, 1);
	built.authority.session(mine.participant).end({ expect: mine, operationId: "end:a", reason: "r" });
	const authority = restart(built.authority, built.path);
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	assert.equal(authority.projectWork(OTHER).generationCounter, 1);
	assert.deepEqual({ ...authority.assignmentOf(OTHER) }, { ...theirs });
	assert.equal(authority.slotHolder(GEMINI), OTHER);
	assert.equal(authority.slotHolder(CLAUDE), null);
	authority.assertInvariants(WORK);
	authority.assertInvariants(OTHER);
	authority.dispose();
});

test("W2928: the whole assignment history is readable after a restart", () => {
	const built = deployment({ contract: V12 });
	const first = built.authority.session(CLAUDE).claim({ workId: WORK, operationId: "claim:1" });
	built.authority.session(first.participant).cancel({ expect: first, operationId: "cancel:1", reason: "lost" });
	built.authority.session(CLAUDE).satisfyGate({
		workId: WORK, gate: "runtime-quiescence:1",
		evidence: { kind: "runtime-absent", runtime: "container-1" },
		operationId: "gate:1" });
	const second = built.authority.session(GEMINI).claim({ workId: WORK, operationId: "claim:2" });
	built.authority.session(second.participant).pass({ expect: second, toRoute: "rview", operationId: "pass:1",
		comment: "ready for review" });
	const authority = restart(built.authority, built.path);
	assert.deepEqual(
		authority.assignmentEvents(WORK).map((row) =>
			[row.participant, row.generation, row.cause, row.fenced, row.gate]),
		[[CLAUDE, 1, "cancelled", 1, "runtime-quiescence:1"],
		 [GEMINI, 2, "pass", 0, null]]);
	assert.deepEqual(authority.gateEvidence(WORK).map((row) => row.gate),
		["runtime-quiescence:1"]);
	assert.equal(authority.projectWork(WORK).route, "rview");
	assert.equal(authority.projectWork(WORK).generationCounter, 2);
	authority.dispose();
});
