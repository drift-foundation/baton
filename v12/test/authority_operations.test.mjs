// W2928: the operation journal — effectively-once, collisions, durable
// refusals, retirement and settlement.
//
// This is the half of `SPEC.md` that four focused reviews kept returning
// to, so the cases are written to the distinctions those reviews drew:
//
//   - an operation IDENTITY is durably UNSUBMITTED, COMMITTED, REFUSED
//     (only when the refusal wrote something) or RETIRED (§4);
//   - reading is how a submitter LEARNS an outcome; it is never how one
//     is DECIDED (§8);
//   - an id is not the operands, so a record under that id with different
//     operands is a collision that fails closed (§10.16);
//   - a retirement binds the DISPOSITION it caused, because the authority
//     act and a manager's control row are separate durability boundaries
//     (§10.17).

import { test, after } from "node:test";
import assert from "node:assert/strict";

import { V12Authority, V12 } from "../src/authority/index.mjs";
import { APPROVER, CLAUDE, CLOSER, GEMINI, INTEGRATOR, OTHER, REVIEWER,
         VERIFIER, WORK, candidate, claimedV12, cleanup, deployment,
         refusalMessage } from "./authority_fixture.mjs";

after(cleanup);

const claimOp = "claim:offer-1";
const signature = () => V12Authority.claimSignature(WORK, CLAUDE);

test("W2928: an exact replay returns the committed result and mints nothing", () => {
	const { as, authority, assignment } = claimedV12();
	const replayed = as(CLAUDE).claim({
		workId: WORK, operationId: `claim:offer-${WORK}` });
	assert.deepEqual(replayed, { ...assignment });
	// §10.13: retry can repeat an operation RESULT but never a generation
	// mint. The counter did not move.
	assert.equal(authority.projectWork(WORK).generationCounter, 1);
	authority.assertInvariants(WORK);
});

test("W2928: one operation id with different operands is refused, not replayed", () => {
	const { as, authority } = deployment({ contract: V12 });
	as(CLAUDE).claim({ workId: WORK, operationId: claimOp });
	assert.match(
		refusalMessage(() => as(GEMINI).claim({ workId: WORK, operationId: claimOp })),
		/operation id was reused for different operands/);
	assert.equal(authority.projectWork(WORK).handler, CLAUDE);
});

test("W2928: every durable operand rides the signature, including the prose", () => {
	// §7. A reason or rationale is written into the authoritative event or
	// the terminal outcome. Outside the signature, reusing one id with
	// different prose would silently return the first result and commit
	// text nobody asked for.
	const built = claimedV12();
	built.as(built.assignment.participant).end({ expect: built.assignment, operationId: "end:1", reason: "handed back" });
	assert.match(
		refusalMessage(() => built.as(built.assignment.participant).end({ expect: built.assignment, operationId: "end:1", reason: "something else" })),
		/reused for different operands/);

	const cancelled = claimedV12();
	cancelled.as(cancelled.assignment.participant).cancel({ expect: cancelled.assignment, operationId: "cancel:1", reason: "runtime lost" });
	assert.match(
		refusalMessage(() => cancelled.as(cancelled.assignment.participant).cancel({ expect: cancelled.assignment, operationId: "cancel:1", reason: "other" })),
		/reused for different operands/);

	const closed = claimedV12();
	closed.as(CLOSER).close({ workId: WORK, outcome: "satisfying",
		rationale: "reviewed",  operationId: "close:1",
		expect: closed.assignment });
	assert.match(
		refusalMessage(() => closed.as(CLOSER).close({
			workId: WORK, outcome: "satisfying", rationale: "different words",
			 operationId: "close:1", expect: closed.assignment })),
		/reused for different operands/);
});

test("W2928: an ordinary refusal writes nothing and stays retryable", () => {
	const { as, authority } = deployment({ contract: V12 });
	as(CLAUDE).claim({ workId: WORK, operationId: "claim:winner" });
	const attempt = () => as(GEMINI).claim({ workId: WORK, operationId: "claim:loser" });
	assert.match(refusalMessage(attempt), /already claimed/);
	// Nothing was journalled: the identity is still UNSUBMITTED, which is
	// what makes the retry a first attempt rather than a replay.
	assert.equal(authority.operationRecord("claim:loser"), null);
	assert.equal(authority.operationResult("claim:loser"), null);
});

test("W2928: a refusal that WROTE something replays that refusal", () => {
	// §7's second replay rule and the one transition that has it: the
	// stale-target integration journals its attempt before refusing, so
	// the retry must replay the refusal rather than append a second
	// attempt or take a different outcome under one identity.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1", 
		observation: "passed", operationId: "ver:1" });
	as(REVIEWER).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "rev:1" });
	as(APPROVER).approve({ proposalId: "p1", approvalId: "a1", 
		disposition: "approved", operationId: "app:1", policyGeneration: 7 });
	// The canonical target moves underneath the approved proposal.
	authority.setPolicy("canonical_target", "moved-1");
	assert.match(refusalMessage(() => as(INTEGRATOR).integrate({
		proposalId: "p1", integrationId: "i1", 
		operationId: "int:1" })), /canonical target moved/);
	assert.equal(authority.integrationAttempts("p1").length, 1);
	assert.equal(authority.operationRecord("int:1").state, "refused");

	// The retry replays the same refusal and journals no second attempt —
	// even though the target has since moved BACK, which without the
	// durable refusal would let one identity take two different outcomes.
	authority.setPolicy("canonical_target", "base-1");
	assert.match(refusalMessage(() => as(INTEGRATOR).integrate({
		proposalId: "p1", integrationId: "i1", 
		operationId: "int:1" })), /canonical target moved/);
	assert.equal(authority.integrationAttempts("p1").length, 1,
		"the retry appended a second attempt");
	assert.equal(authority.receipt("p1", "integration"), null);

	// A NEW operation identity is free to evaluate the world as it now
	// stands, and it succeeds.
	assert.equal(as(INTEGRATOR).integrate({ proposalId: "p1", integrationId: "i1",
		 operationId: "int:2" }).disposition, "integrated");
	assert.equal(authority.canonicalTarget(), "cand-1");
});

test("W2928: a refusal that wrote NOTHING leaves the identity unsubmitted", () => {
	// Review 2026-08-22 [P1]. `integrate` used to mark every refusal
	// durable, so a pre-approval integration — which writes no attempt row —
	// was recorded REFUSED and permanently closed. An ordinary refusal
	// writes nothing and stays retryable; REFUSED exists only when the
	// refusal itself is a committed outcome.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	assert.match(refusalMessage(() => as(INTEGRATOR).integrate({
		proposalId: "p1", integrationId: "i1", 
		operationId: "int:early" })), /requires passed verification/);
	assert.equal(authority.integrationAttempts("p1").length, 0,
		"the refusal wrote an attempt row it should not have");
	assert.equal(authority.operationRecord("int:early"), null,
		"a no-write refusal was journalled as durable");

	// So the SAME operation identity still works once the workflow catches
	// up, which is what "stays retryable" means.
	as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1", 
		observation: "passed", operationId: "ver:1" });
	as(REVIEWER).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "rev:1" });
	as(APPROVER).approve({ proposalId: "p1", approvalId: "a1", 
		disposition: "approved", operationId: "app:1", policyGeneration: 7 });
	assert.equal(as(INTEGRATOR).integrate({ proposalId: "p1", integrationId: "i1",
		 operationId: "int:early" }).disposition, "integrated");
});

test("W2928: settlement without explicit authority to retire does not retire", () => {
	// Review 2026-08-22 [P1]: `mayRetire` defaulted to true, so omitting the
	// operand retired an unsubmitted claim on the spot. Settlement authority
	// is something a caller asserts, never something it inherits by saying
	// nothing.
	const { as, authority } = deployment({ contract: V12 });
	const observed = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(),
		reason: "no authority supplied", disposition: "settlement-expired" });
	assert.deepEqual(observed, { kind: "live", record: null });
	assert.equal(authority.operationRecord(claimOp), null);
	// The fixed claim is still authorized and still commits.
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: claimOp }).generation, 1);
});

test("W2928: an unanswerable lookup settles nothing", () => {
	// §8: "I could not ask" must never be read as "it did not commit".
	const { as, authority } = deployment({ contract: V12 });
	authority.setLookupAvailable(false);
	assert.match(refusalMessage(() => authority.operationResult(claimOp)),
		/lookup is unavailable/);
	assert.match(
		refusalMessage(() => as(CLAUDE).settleOperation({
			operationId: claimOp, signature: signature(), reason: "timed out",
			disposition: "settlement-expired" })),
		/lookup is unavailable/);
	// The identity is untouched, so the fixed claim is still live.
	authority.setLookupAvailable(true);
	assert.equal(authority.operationRecord(claimOp), null);
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: claimOp }).generation, 1);
});

test("W2928: settlement without authority to retire may only observe", () => {
	// §10.15. A caller with no positive evidence that the operation is
	// over — a timeout before its deadline — observes and reports `live`.
	const { as, authority } = deployment({ contract: V12 });
	const observed = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(), reason: "too early",
		disposition: "settlement-expired", mayRetire: false });
	assert.deepEqual(observed, { kind: "live", record: null });
	assert.equal(authority.operationRecord(claimOp), null);
	// So the fixed claim still commits afterwards, which is the whole
	// point: retiring it early would have stranded an authorized claim.
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: claimOp }).generation, 1);
});

test("W2928: a committed claim WINS a settlement, whatever the caller intended", () => {
	// The settlement timeout's central hazard: the authority committed the
	// claim and the manager lost the result. Terminalizing on the caller's
	// intent would strand a live assignment holding the participant's one
	// slot while every later claim refuses.
	const { as, authority, assignment } = claimedV12();
	const settled = as(CLAUDE).settleOperation({
		operationId: `claim:offer-${WORK}`, signature: signature(),
		reason: "deadline passed", disposition: "settlement-expired",
		mayRetire: true });
	assert.equal(settled.kind, "committed");
	assert.deepEqual(settled.result, { ...assignment });
	// And the identity is NOT retired: a committed operation is already
	// terminal, so reconciling it is not a retirement.
	assert.equal(authority.operationRecord(`claim:offer-${WORK}`).state, "committed");
});

test("W2928: a settlement cannot race a claim that commits after its lookup", () => {
	// The read proves only its own instant. The settlement re-reads INSIDE
	// the act, so a claim that commits between the two is found rather
	// than overwritten.
	const { as, authority } = deployment({ contract: V12 });
	assert.equal(authority.operationResult(claimOp), null, "nothing committed yet");
	// …and now the submitter, which had already passed its preconditions,
	// commits.
	const assignment = as(CLAUDE).claim({ workId: WORK, operationId: claimOp });
	const settled = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(), reason: "deadline passed",
		disposition: "settlement-expired", mayRetire: true });
	assert.equal(settled.kind, "committed");
	assert.deepEqual(settled.result, { ...assignment });
	assert.equal(authority.projectWork(WORK).handler, CLAUDE);
});

test("W2928: a retired identity stays dead for every later submitter", () => {
	// Retirement is a property of the IDENTITY, not of one request's
	// operands, so it closes the identity to the original submitter, to a
	// stale one, and to one asking for something else entirely.
	const { as, authority } = deployment({ contract: V12 });
	const retired = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(),
		reason: "the claim-settlement deadline passed with no committed claim",
		disposition: "settlement-expired", mayRetire: true });
	assert.equal(retired.kind, "retired");
	assert.deepEqual(retired.record, {
		reason: "the claim-settlement deadline passed with no committed claim",
		disposition: "settlement-expired",
	});
	// The original fixed claim is dead even though the Work is free.
	assert.equal(authority.projectWork(WORK).ready, true);
	assert.match(
		refusalMessage(() => as(CLAUDE).claim({ workId: WORK, operationId: claimOp })),
		/claim-settlement deadline passed/);
	// Retirement is answered BEFORE the signature: a stale submitter with
	// different operands learns the identity is dead, not that its operands
	// disagree. Those are different facts and only one of them is true.
	assert.match(
		refusalMessage(() => as(GEMINI).claim({ workId: WORK, operationId: claimOp })),
		/claim-settlement deadline passed/);
	// A fresh offer with a fresh identity claims normally.
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: "claim:offer-2" }).generation, 1);
});

test("W2928: the retirement decides the disposition; a later path replays it", () => {
	// §10.17. The authority record and a manager's control row are
	// separate durability boundaries, so a manager can retire and die
	// before writing its row. Whoever arrives next arrives on whatever
	// entry path it happens to be on, and must not relabel the outcome.
	const { as, authority } = deployment({ contract: V12 });
	as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(),
		reason: "the claim was submitted and refused", disposition: "claim-refused",
		mayRetire: true });
	// A settlement timeout meets that retirement and proposes its own
	// disposition. It gets the bound one back.
	const met = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(),
		reason: "the deadline passed", disposition: "settlement-expired",
		mayRetire: true });
	assert.deepEqual(met.record, {
		reason: "the claim was submitted and refused", disposition: "claim-refused" });
	// And in the other direction.
	const other = deployment({ contract: V12, works: [[OTHER, "impl"]] });
	const otherSignature = V12Authority.claimSignature(OTHER, CLAUDE);
	other.as(CLAUDE).settleOperation({
		operationId: "claim:o", signature: otherSignature,
		reason: "the deadline passed", disposition: "settlement-expired",
		mayRetire: true });
	assert.equal(other.as(CLAUDE).settleOperation({
		operationId: "claim:o", signature: otherSignature,
		reason: "refused", disposition: "claim-refused", mayRetire: true })
		.record.disposition, "settlement-expired");
});

test("W2928: a replayed retirement reports the reason its identity died of", () => {
	const { as, authority } = deployment({ contract: V12 });
	as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(),
		reason: "the operator abandoned a stuck handoff",
		disposition: "settlement-expired", mayRetire: true });
	// Every submitter learns the real reason rather than a message invented
	// by whoever noticed afterwards.
	assert.match(
		refusalMessage(() => as(CLAUDE).claim({ workId: WORK, operationId: claimOp })),
		/the operator abandoned a stuck handoff/);
	const record = authority.operationRecord(claimOp);
	assert.equal(record.state, "retired");
	assert.equal(record.detail.reason, "the operator abandoned a stuck handoff");
	// The retirement BINDS the operands it settled, so the journal says
	// which operation died.
	assert.equal(record.signature, signature());
});

test("W2928: a colliding operation identity fails closed and changes no record", () => {
	// §10.16. An id proves only that SOMETHING committed under it. A
	// settlement whose expected operands disagree must neither adopt the
	// other operation's result nor overwrite its record — binding another
	// participant's assignment to this offer is exactly the failure.
	const { as, authority } = deployment({
		contract: V12, works: [[WORK, "impl"], [OTHER, "impl"]] });
	const mine = as(CLAUDE).claim({ workId: WORK, operationId: "claim:shared" });
	assert.match(
		refusalMessage(() => as(CLAUDE).settleOperation({
			operationId: "claim:shared",
			signature: V12Authority.claimSignature(OTHER, GEMINI),
			reason: "timed out", disposition: "settlement-expired", mayRetire: true })),
		/reused for different operands/);
	const record = authority.operationRecord("claim:shared");
	assert.equal(record.state, "committed", "the collision retired the other record");
	assert.deepEqual(record.result, { ...mine });
	assert.equal(authority.projectWork(OTHER).handler, null);
});

test("W2928: settlement compares operands even when it may retire", () => {
	// The collision check applies to an UNSUBMITTED identity too, in the
	// sense that the retirement it writes binds this caller's operands —
	// so a later settlement with different ones is refused rather than
	// silently reading somebody else's retirement as its own.
	const { as, authority } = deployment({ contract: V12 });
	as(CLAUDE).settleOperation({
		operationId: claimOp, signature: signature(), reason: "gone",
		disposition: "settlement-expired", mayRetire: true });
	// A DIFFERENT expected signature still meets the retirement first,
	// because retirement is a property of the identity (§4) — and the
	// record it reads names the operands that actually died.
	const met = as(CLAUDE).settleOperation({
		operationId: claimOp, signature: V12Authority.claimSignature(OTHER, GEMINI),
		reason: "mine", disposition: "claim-refused", mayRetire: true });
	assert.equal(met.kind, "retired");
	assert.equal(authority.operationRecord(claimOp).signature, signature());
});

test("W2928: the journal distinguishes all four operation states", () => {
	const { as, authority, assignment } = claimedV12();
	// UNSUBMITTED
	assert.equal(authority.operationRecord("never"), null);
	// COMMITTED
	assert.equal(authority.operationRecord(`claim:offer-${WORK}`).state, "committed");
	// REFUSED, only where the refusal wrote something durable.
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("c1"), operationId: "pub:1" });
	as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1", 
		observation: "passed", operationId: "ver:1" });
	as(REVIEWER).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "rev:1" });
	as(APPROVER).approve({ proposalId: "p1", approvalId: "a1", 
		disposition: "approved", operationId: "app:1", policyGeneration: 7 });
	authority.setPolicy("canonical_target", "moved");
	assert.throws(() => as(INTEGRATOR).integrate({ proposalId: "p1",
		integrationId: "i1",  operationId: "int:1" }));
	assert.equal(authority.operationRecord("int:1").state, "refused");
	// RETIRED
	as(CLAUDE).settleOperation({ operationId: "retire-me", signature: "sig",
		reason: "dead", disposition: "settlement-expired", mayRetire: true });
	assert.equal(authority.operationRecord("retire-me").state, "retired");
	// And `operationResult` answers only for a COMMITTED one.
	assert.equal(authority.operationResult("int:1"), null);
	assert.equal(authority.operationResult("retire-me"), null);
	assert.deepEqual(authority.operationResult(`claim:offer-${WORK}`), { ...assignment });
});

test("W2928: a mutating operation without an operation id is refused", () => {
	const { as, authority } = deployment({ contract: V12 });
	assert.match(
		refusalMessage(() => as(CLAUDE).claim({ workId: WORK, operationId: "" })),
		/needs an operation id/);
	assert.equal(authority.projectWork(WORK).handler, null);
});
