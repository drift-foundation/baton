// W2928: per-Work contract progression (ruling 3), the terminal-close
// rulings (ruling 4), and the four immutable workflow receipts.

import { test, after } from "node:test";
import assert from "node:assert/strict";

import { V11, V12 } from "../src/authority/index.mjs";
import { APPROVER, CLAUDE, CLOSER, GEMINI, INTEGRATOR, REVIEWER, UUID,
         VERIFIER, WORK, candidate, claimedV12, cleanup, deployment,
         refusalMessage } from "./authority_fixture.mjs";

after(cleanup);

test("W2928: contract progression keeps the Work and mints its first generation", () => {
	// Ruling 3. A Work keeps its identity, dossier, history, containment
	// and relationships as its contract advances; the first positive
	// generation is minted by the first claim AFTER entering the v12
	// contract, not by the transition.
	const { as, authority } = deployment();
	const v11 = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v11" });
	assert.equal(v11.generation, null);
	// Publication is refused under v11 — the contract decides the rules
	// the assignment runs under.
	assert.match(
		refusalMessage(() => as(v11.participant).publish({ expect: v11, proposalId: "p", ...candidate("v11"),
			operationId: "pub:v11" })),
		/publication requires a v12 assignment contract/);

	const advanced = as(v11.participant).advanceContract({ expect: v11, expectContract: V11, targetContract: V12,
		rationale: "M2 isolated execution", operationId: "advance:1" });
	assert.deepEqual(advanced, { contract: V12, phase: "queued", gate: null });
	// The transition ends the old assignment in the same act: it never
	// changes constraints underneath a running worker (§10.10).
	assert.equal(authority.projectWork(WORK).handler, null);
	assert.equal(authority.projectWork(WORK).workId, WORK, "the same Work");
	assert.equal(authority.projectWork(WORK).generationCounter, 0,
		"the transition itself mints nothing");
	const [event] = authority.contractEvents(WORK);
	assert.equal(event.from_contract, V11);
	assert.equal(event.to_contract, V12);
	assert.equal(event.rationale, "M2 isolated execution");

	const first = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v12" });
	assert.equal(first.generation, 1, "the first v12 claim mints generation 1");
	authority.assertInvariants(WORK);
});

test("W2928: an uncertified target contract blocks on a typed gate", () => {
	// A Work may intentionally advance to v12 before the v12 runtime is
	// deployed. It stays the SAME Work and waits visibly, rather than
	// being recreated, misclaimed under v11, or manually parked (§11).
	const { as, authority } = deployment({ certified: [V11] });
	const v11 = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v11" });
	const advanced = as(v11.participant).advanceContract({ expect: v11, expectContract: V11, targetContract: V12,
		rationale: "ahead of the runtime", operationId: "advance:1" });
	assert.deepEqual(advanced,
		{ contract: V12, phase: "block", gate: `contract-runtime:${V12}` });
	assert.equal(authority.projectWork(WORK).ready, false);
	assert.match(
		refusalMessage(() => as(CLAUDE).claim({ workId: WORK, operationId: "claim:early" })),
		/blocked by contract-runtime/);
	// The gate refuses while no certified profile exists.
	assert.match(
		refusalMessage(() => as(CLAUDE).satisfyGate({
			workId: WORK, gate: `contract-runtime:${V12}`,
			evidence: { kind: "certified-profile", profile: "oci-1" },
			operationId: "gate:early" })),
		/no certified runtime profile executes this contract/);
	// Deploying and certifying a matching environment satisfies it, and
	// the Work becomes claimable under the ALREADY SELECTED contract.
	authority.certifyContract(V12, "oci-1");
	as(CLAUDE).satisfyGate({
		workId: WORK, gate: `contract-runtime:${V12}`,
		evidence: { kind: "certified-profile", profile: "oci-1" },
		operationId: "gate:certified" });
	const work = authority.projectWork(WORK);
	assert.equal(work.contract, V12);
	assert.equal(work.ready, true);
	assert.equal(as(CLAUDE).claim({ workId: WORK, operationId: "claim:now" }).generation, 1);
});

test("W2928: a contract transition refuses stale or unpermitted operands", () => {
	const { as, authority } = deployment();
	const v11 = as(CLAUDE).claim({ workId: WORK, operationId: "claim:v11" });
	// A stale EXPECTED CONTRACT refuses even with the exact assignment.
	assert.match(
		refusalMessage(() => as(v11.participant).advanceContract({ expect: v11, expectContract: V12, targetContract: V12,
			rationale: "r", operationId: "advance:stale-contract" })),
		/contract compare-and-swap is stale/);
	// An unpermitted target refuses: an arbitrary tag edit has no authority.
	assert.match(
		refusalMessage(() => as(v11.participant).advanceContract({ expect: v11, expectContract: V11, targetContract: "v99-experimental",
			rationale: "r", operationId: "advance:unpermitted" })),
		/not permitted by policy/);
	// A stale ASSIGNMENT refuses: only the current Handler advances it.
	assert.match(
		refusalMessage(() => as(CLAUDE).advanceContract({
			expect: { ...v11, generation: 7 }, expectContract: V11,
			targetContract: V12, rationale: "r", operationId: "advance:stale-assign" })),
		/stale assignment/);
	assert.equal(authority.projectWork(WORK).contract, V11);
	assert.deepEqual(authority.contractEvents(WORK), []);
});

test("W2928: an authorized close of unclaimed Work needs no assignment", () => {
	// Ruling 4. No execution claim is manufactured merely to reach a
	// terminal state.
	const { as, authority } = deployment({ contract: V12 });
	const closed = as(CLOSER).close({
		workId: WORK, outcome: "rejected", rationale: "duplicate of W9",
		 operationId: "close:1" });
	assert.deepEqual(closed, { outcome: "rejected", actor: CLOSER, assignment: null });
	const work = authority.projectWork(WORK);
	assert.equal(work.status, "closed");
	assert.equal(work.phase, null);
	assert.equal(work.outcome, "rejected");
	authority.assertInvariants(WORK);
	// Closed Work never reopens.
	assert.match(
		refusalMessage(() => as(CLOSER).close({
			workId: WORK, outcome: "satisfying", rationale: "again",
			 operationId: "close:2" })),
		/already closed/);
});

test("W2928: a close that ends a live assignment needs the exact identity", () => {
	const { as, authority, assignment } = claimedV12();
	// Omitting it refuses.
	assert.match(
		refusalMessage(() => as(CLOSER).close({
			workId: WORK, outcome: "satisfying", rationale: "done",
			 operationId: "close:omitted" })),
		/must supply its exact assignment identity/);
	// Naming only the participant refuses.
	assert.match(
		refusalMessage(() => as(CLOSER).close({
			workId: WORK, outcome: "satisfying", rationale: "done",
			operationId: "close:participant", expect: { participant: CLAUDE } })),
		/must be the full four-part identity/);
	// A stale generation refuses.
	assert.match(
		refusalMessage(() => as(CLOSER).close({
			workId: WORK, outcome: "satisfying", rationale: "done",
			operationId: "close:stale", expect: { ...assignment, generation: 9 } })),
		/stale assignment/);
	assert.equal(authority.projectWork(WORK).status, "open");
	// The exact identity commits the terminal outcome and the centralized
	// assignment end in one act, and the event names the ended assignment.
	const closed = as(CLOSER).close({
		workId: WORK, outcome: "satisfying", rationale: "reviewed and passing",
		 operationId: "close:exact", expect: assignment });
	assert.deepEqual(closed.assignment, { ...assignment });
	const work = authority.projectWork(WORK);
	assert.equal(work.status, "closed");
	assert.equal(work.handler, null);
	assert.equal(work.phase, null);
	// Publication is invalidated: the closed generation is fenced.
	assert.deepEqual(work.fencedGenerations.map((row) => row.generation), [1]);
	const [event] = authority.assignmentEvents(WORK).slice(-1);
	assert.equal(event.cause, "close:satisfying");
	assert.equal(event.generation, 1);
	authority.assertInvariants(WORK);
});

test("W2928: a close after cancellation refuses the fenced generation", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).cancel({ expect: assignment, operationId: "cancel:1", reason: "lost" });
	assert.match(
		refusalMessage(() => as(CLOSER).close({
			workId: WORK, outcome: "cancelled", rationale: "abandoned",
			 operationId: "close:fenced", expect: assignment })),
		/fenced and ended/);
	// The operator's route is the explicit one: the Work is already
	// unclaimed, so an authorized unclaimed close works.
	const closed = as(CLOSER).close({
		workId: WORK, outcome: "cancelled", rationale: "abandoned",
		 operationId: "close:unclaimed" });
	assert.equal(closed.assignment, null);
	assert.equal(authority.projectWork(WORK).gate, null);
	authority.assertInvariants(WORK);
});

test("W2928: publication binds the exact assignment and every ruled digest", () => {
	// §10.11: the receipt binds the exact assignment AND the input, policy,
	// output, candidate-tree and target digests; §4 adds the frozen result
	// identity and its content digest. Review 2026-08-22 [P1]: one
	// undifferentiated digest bound none of that, so a published candidate
	// could not say what it had been built FROM.
	const { as, authority, assignment } = claimedV12();
	const bytes = candidate("cand-1");
	const published = as(assignment.participant).publish({ expect: assignment, proposalId: "p1", ...bytes, operationId: "pub:1" });
	assert.deepEqual(published, { proposalId: "p1", ...bytes, target: "base-1" });
	const row = authority.proposal("p1");
	assert.equal(row.participant, CLAUDE);
	assert.equal(row.generation, 1);
	assert.equal(row.result_id, bytes.resultId);
	assert.equal(row.result_digest, bytes.resultDigest);
	assert.equal(row.candidate_digest, bytes.candidateDigest);
	assert.equal(row.input_digest, bytes.inputDigest);
	assert.equal(row.policy_digest, bytes.policyDigest);

	// EVERY digest is required: a proposal missing one binds less than the
	// contract says a proposal binds.
	for (const missing of ["resultId", "resultDigest", "candidateDigest",
	                       "inputDigest", "policyDigest"]) {
		const partial = { ...candidate("cand-2") };
		delete partial[missing];
		assert.match(
			refusalMessage(() => as(assignment.participant).publish({ expect: assignment, proposalId: `p-${missing}`, ...partial,
				operationId: `pub:${missing}` })),
			new RegExp(`${missing} is missing`), missing);
	}

	// §10.11: later bytes are a NEW proposal, never the same identity — and
	// that is true of each digest, not only the candidate tree.
	for (const [field, value] of [["candidateDigest", "cand-2"],
	                              ["inputDigest", "sha256:other-input"],
	                              ["policyDigest", "sha256:other-policy"],
	                              ["resultDigest", "sha256:other-result"]]) {
		assert.match(
			refusalMessage(() => as(assignment.participant).publish({ expect: assignment, proposalId: "p1", ...bytes, [field]: value,
				operationId: `pub:${field}` })),
			/proposal identity was reused for different bytes/, field);
	}
	assert.equal(authority.proposal("p1").candidate_digest, "cand-1");
});

test("W2928: the four workflow receipts are distinct, ordered and immutable", () => {
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	// Each gate requires the previous one for the exact proposal.
	assert.match(refusalMessage(() => as(REVIEWER).review({
		proposalId: "p1", reviewId: "r1",  disposition: "accepted",
		operationId: "rev:early" })), /requires passed verification/);
	as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1", 
		observation: "passed", operationId: "ver:1" });
	assert.match(refusalMessage(() => as(APPROVER).approve({
		proposalId: "p1", approvalId: "a1",  disposition: "approved",
		operationId: "app:early", policyGeneration: 7 })), /requires accepted technical review/);
	as(REVIEWER).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "rev:1" });
	assert.match(refusalMessage(() => as(INTEGRATOR).integrate({
		proposalId: "p1", integrationId: "i1", 
		operationId: "int:early" })), /requires explicit approval/);
	as(APPROVER).approve({ proposalId: "p1", approvalId: "a1", 
		disposition: "approved", operationId: "app:1", policyGeneration: 7 });
	as(INTEGRATOR).integrate({ proposalId: "p1", integrationId: "i1",
		 operationId: "int:1" });
	assert.equal(authority.canonicalTarget(), "cand-1",
		"integration advances the canonical target");

	// Each receipt is SEPARATELY ATTRIBUTABLE: its own identity, its own
	// actor, and the candidate digest and target revision that actor saw.
	const attribution = Object.fromEntries(authority.receipts("p1")
		.map((receipt) => [receipt.kind, [receipt.receipt_id, receipt.actor]]));
	assert.deepEqual(attribution, {
		verification: ["v1", VERIFIER], review: ["r1", REVIEWER],
		approval: ["a1", APPROVER], integration: ["i1", INTEGRATOR],
	});
	for (const receipt of authority.receipts("p1")) {
		assert.equal(receipt.candidate_digest, "cand-1");
		assert.equal(receipt.target, "base-1");
	}
	assert.equal(authority.receipt("p1", "approval").policy_generation, 7);

	// A second write refuses; only a byte-identical replay of the same
	// operation id returns the committed result (§10.12).
	for (const [act, kind] of [
		[() => as(VERIFIER).verify({ proposalId: "p1", verificationId: "v2",
			 observation: "failed", operationId: "ver:2" }), "verification"],
		[() => as(REVIEWER).review({ proposalId: "p1", reviewId: "r2", 
			disposition: "rejected", operationId: "rev:2" }), "review"],
		[() => as(APPROVER).approve({ proposalId: "p1", approvalId: "a2",
			 disposition: "denied", operationId: "app:2", policyGeneration: 7 }), "approval"],
		[() => as(INTEGRATOR).integrate({ proposalId: "p1", integrationId: "i2",
			 operationId: "int:2" }), "integration"],
	]) {
		assert.match(refusalMessage(act), /receipt is immutable/, kind);
	}
	assert.equal(as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1",
		 observation: "passed", operationId: "ver:1" }).disposition,
		"passed");
	// Integration never closes the Work implicitly.
	assert.equal(authority.projectWork(WORK).status, "open");
});

test("W2928: the publisher cannot write the receipts that judge its candidate", () => {
	// Review 2026-08-22 [P1]. Without an actor and a configured capability,
	// one consumer could publish a candidate, self-verify, self-review,
	// self-approve, integrate it into the canonical target and close the
	// Work — every gate satisfied by the party the gates exist to check.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	assert.deepEqual(authority.capabilitiesOf(CLAUDE), [],
		"the claimant holds no workflow capability");
	for (const [act, capability] of [
		[() => as(CLAUDE).verify({ proposalId: "p1", verificationId: "v1",
			 observation: "passed", operationId: "ver:self" }), "verify"],
		[() => as(CLAUDE).review({ proposalId: "p1", reviewId: "r1", 
			disposition: "accepted", operationId: "rev:self" }), "review"],
		[() => as(CLAUDE).approve({ proposalId: "p1", approvalId: "a1", 
			disposition: "approved", operationId: "app:self", policyGeneration: 7 }), "approve"],
		[() => as(CLAUDE).integrate({ proposalId: "p1", integrationId: "i1",
			 operationId: "int:self" }), "integrate"],
		[() => as(CLAUDE).close({ workId: WORK, outcome: "satisfying",
			rationale: "mine",  operationId: "close:self",
			expect: assignment }), "close"],
	]) {
		assert.match(refusalMessage(act),
			new RegExp(`does not hold the ${capability} capability`), capability);
	}
	// None of them wrote anything, and each identity stays retryable.
	assert.deepEqual(authority.receipts("p1"), []);
	assert.equal(authority.operationRecord("ver:self"), null);
	assert.equal(authority.projectWork(WORK).status, "open");
	assert.equal(authority.canonicalTarget(), "base-1");
	// A caller cannot supply an actor at all: re-review 2026-08-22 [P1] found
	// that passing a configured closer's NAME was enough to act as them,
	// because the check compared a string the same caller supplied. The
	// actor now comes from the session binding, and an operand that looks
	// authoritative and is not is refused rather than ignored.
	assert.match(
		refusalMessage(() => as(CLAUDE).verify({ proposalId: "p1",
			verificationId: "v1", actor: VERIFIER, observation: "passed",
			operationId: "ver:impersonate" })),
		/takes its actor from the session it is called on/);
	// And one with no identity of its own.
	assert.match(
		refusalMessage(() => as(VERIFIER).verify({ proposalId: "p1", 
			observation: "passed", operationId: "ver:noid" })),
		/needs its own identity/);
});

test("W2928: a deployment may grant one participant several capabilities", () => {
	// §10.12 permits it explicitly — the receipts stay distinct because each
	// records who wrote it. What the authority refuses is the question going
	// UNASKED, not a deployment answering it this way.
	const { as, authority, assignment } = claimedV12();
	authority.grantCapability(GEMINI, "verify");
	authority.grantCapability(GEMINI, "review");
	as(assignment.participant).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	as(GEMINI).verify({ proposalId: "p1", verificationId: "v1", 
		observation: "passed", operationId: "ver:1" });
	as(GEMINI).review({ proposalId: "p1", reviewId: "r1", 
		disposition: "accepted", operationId: "rev:1" });
	assert.deepEqual(
		Object.fromEntries(authority.receipts("p1")
			.map((receipt) => [receipt.kind, receipt.actor])),
		{ verification: GEMINI, review: GEMINI });
	// Still not approval: that capability was not granted.
	assert.match(
		refusalMessage(() => as(GEMINI).approve({ proposalId: "p1", approvalId: "a1",
			 disposition: "approved", operationId: "app:1", policyGeneration: 7 })),
		/does not hold the approve capability/);
	authority.revokeCapability(GEMINI, "verify");
	assert.equal(authority.holdsCapability(GEMINI, "verify"), false);
	assert.deepEqual(authority.capabilitiesOf(GEMINI), ["review"]);
});

test("W2928: publication requires a LIVE assignment, not merely a past one", () => {
	// §10.3: no result or proposal capability exists once the assignment
	// is over, which is what makes a late publication from an abandoned
	// worker a refusal rather than a race.
	const { as, authority, assignment } = claimedV12();
	as(assignment.participant).end({ expect: assignment, operationId: "end:1", reason: "handed back" });
	assert.match(
		refusalMessage(() => as(assignment.participant).publish({ expect: assignment, proposalId: "p-late",
			...candidate("d"), operationId: "pub:late" })),
		/stale assignment/);
	assert.throws(() => authority.proposal("p-late"), /no such proposal/);
});

test("W2928: an approval binds its policy generation in the replay identity", () => {
	// Re-review 2026-08-22 [P1]. `policyGeneration` was optional and outside
	// the operation signature, so committing operation `app` under
	// generation 7 and resubmitting the same id under 8 REPLAYED success —
	// one identity taking two different durable meanings — and omitting it
	// entirely committed NULL while the record claimed approval binds it.
	const { as, authority, assignment } = claimedV12();
	as(CLAUDE).publish({ expect: assignment, proposalId: "p1",
		...candidate("cand-1"), operationId: "pub:1" });
	as(VERIFIER).verify({ proposalId: "p1", verificationId: "v1",
		observation: "passed", operationId: "ver:1" });
	as(REVIEWER).review({ proposalId: "p1", reviewId: "r1",
		disposition: "accepted", operationId: "rev:1" });

	// MISSING and MISTYPED are refused before anything is written.
	for (const bad of [undefined, null, "7", 0, -1, 1.5, Number.NaN]) {
		assert.match(
			refusalMessage(() => as(APPROVER).approve({ proposalId: "p1",
				approvalId: "a1", disposition: "approved", operationId: "app:bad",
				policyGeneration: bad })),
			/binds the configured policy generation/, String(bad));
	}
	assert.equal(authority.receipt("p1", "approval"), null);
	assert.equal(authority.operationRecord("app:bad"), null,
		"a refused approval journalled an operation");

	// The committed one records and RETURNS its generation.
	const approved = as(APPROVER).approve({ proposalId: "p1", approvalId: "a1",
		disposition: "approved", operationId: "app", policyGeneration: 7 });
	assert.equal(approved.policyGeneration, 7);
	assert.equal(authority.receipt("p1", "approval").policy_generation, 7);

	// The same operation id under a DIFFERENT generation is a collision, not
	// a replay. This is the exact reproduction.
	assert.match(
		refusalMessage(() => as(APPROVER).approve({ proposalId: "p1",
			approvalId: "a1", disposition: "approved", operationId: "app",
			policyGeneration: 8 })),
		/reused for different operands/);
	assert.equal(authority.receipt("p1", "approval").policy_generation, 7,
		"the stored receipt moved");

	// And the byte-identical replay still returns the committed result.
	assert.equal(as(APPROVER).approve({ proposalId: "p1", approvalId: "a1",
		disposition: "approved", operationId: "app", policyGeneration: 7 })
		.policyGeneration, 7);
	// The journal signature carries it, which is what makes the collision
	// above a collision.
	assert.match(authority.operationRecord("app").signature, /"policyGeneration":7/);
});
