"""W2845 cut 4 — contract progression, the candidate, the four receipts, the
configured capabilities, authorized close, and the one durable refusal.

The obligations of catalog D: progression that waits visibly on a typed gate
when the target runtime is not certified; a proposal that says what it was built
FROM; four separately attributable IMMUTABLE receipts in order, each written by
the actor who holds the configured capability for that step; the policy
generation an approval binds riding the operation identity; authorized close in
both its forms; and the stale-target integration attempt -- the first real
transition in this authority whose REFUSAL is itself a committed outcome.
"""

import os
import tempfile
import unittest

from baton_v12.authority import Authority, CAPABILITIES, Refusal, V11, V12
from baton_v12.authority.core import INTAKE_OUTCOMES
from baton_v12.authority.identity import GATE_CONTRACT_RUNTIME, signature_of

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
GEMINI = "baton.gemini"
SLAW = "baton.slaw"
CODEX = "baton.codex"
ROUTE = "impl"
NOW = "2026-08-24T06:00:00.000Z"

CANDIDATE = "sha256:candidate-1"
DIGESTS = {"result_id": "result-1", "result_digest": "sha256:result-1",
           "candidate_digest": CANDIDATE, "input_digest": "sha256:input-1",
           "policy_digest": "sha256:policy-1"}


class WorkflowCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self._ops = 0

    def op(self, label="op"):
        self._ops += 1
        return f"{label}.{self._ops}"

    def work(self, work_id=WORK, *, contract=V12, handlers=(CLAUDE,)):
        self.core.create_work(work_id, ROUTE, contract=contract, operation_id=("create-" + str(work_id))[:160])
        for participant in handlers:
            self.core.add_route_handler(ROUTE, participant)
        return work_id

    def claimed(self, work_id=WORK, participant=CLAUDE, **kwargs):
        self.work(work_id, **kwargs)
        # W16823: the claim answers a closed result; this fixture's callers
        # want the four-part fence out of it.
        return self.core.claim(work_id, participant,
                               operation_id=self.op("claim"))["assignment"]

    def grant_each(self):
        """One participant per capability, which is the DEFAULT arrangement.

        §10.12 permits a deployment to grant one participant several, and the
        receipts stay distinct even then -- but distinct actors are what makes
        the separation visible, so the fixture uses them.
        """
        for participant, capability in zip(
                (GEMINI, CODEX, SLAW, "baton.integrator"), CAPABILITIES):
            self.authority.grant_capability(participant, capability)
        self.authority.grant_capability("baton.closer", "close")

    def published(self, **overrides):
        assignment = self.claimed()
        digests = {**DIGESTS, **overrides}
        answer = self.core.publish(assignment, operation_id=self.op("publish"),
                                   proposal_id="proposal-1", **digests)
        return assignment, answer

    def through_approval(self, proposal_id="proposal-1"):
        self.core.verify(proposal_id=proposal_id, verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op("verify"))
        self.core.review(proposal_id=proposal_id, review_id="rev-1",
                         actor=CODEX, disposition="accepted",
                         operation_id=self.op("review"))
        self.core.approve(proposal_id=proposal_id, approval_id="app-1",
                          actor=SLAW, disposition="approved",
                          operation_id=self.op("approve"), policy_generation=7)


class ContractProgression(WorkflowCase):

    def test_a_certified_target_advances_straight_to_the_queue(self):
        assignment = self.claimed(contract=V11)
        self.authority.permit_contract_transition(V11, V12)
        self.authority.certify_contract(V12, "reference")
        answer = self.core.advance_contract(
            assignment, operation_id=self.op(), expect_contract=V11,
            target_contract=V12, rationale="needs generations")
        self.assertEqual(answer, {"contract": V12, "phase": "queued",
                                  "gate": None})
        projected = self.core.project_work(WORK)
        self.assertEqual(projected["contract"], V12)
        self.assertIsNone(projected["handler"])
        self.assertTrue(projected["ready"])
        # The progression ENDED the assignment through the one helper, so the
        # history shows it rather than leaving a Handler behind.
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed", "contract-advanced"])
        events = self.core.contract_events(WORK)
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0]["from_contract"], events[0]["to_contract"]),
                         (V11, V12))
        self.assertEqual(events[0]["rationale"], "needs generations")
        self.core.assert_invariants(WORK)

    def test_an_uncertified_target_waits_visibly_on_a_typed_gate(self):
        # §11: a Work MAY intentionally advance to a contract whose runtime is
        # not deployed yet.  It stays THE SAME WORK and waits visibly rather
        # than being recreated or misclaimed -- which is the whole reason the
        # gate exists.
        assignment = self.claimed(contract=V11)
        self.authority.permit_contract_transition(V11, V12)
        answer = self.core.advance_contract(
            assignment, operation_id=self.op(), expect_contract=V11,
            target_contract=V12, rationale="ahead of the runtime")
        self.assertEqual(answer["phase"], "block")
        self.assertEqual(answer["gate"], f"{GATE_CONTRACT_RUNTIME}:{V12}")
        projected = self.core.project_work(WORK)
        self.assertEqual(projected["contract"], V12)
        self.assertFalse(projected["ready"])
        self.assertEqual(projected["gate"]["kind"], GATE_CONTRACT_RUNTIME)
        # And it is the SAME Work: same id, same counter, same history.  The
        # v11 claim minted no generation, so the counter is still 0 -- advancing
        # the contract does not invent one, and §10.1's counter is untouched by
        # anything but a claim.
        self.assertEqual(projected["work_id"], WORK)
        self.assertEqual(projected["generation_counter"], 0)
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed", "contract-advanced"])
        self.core.assert_invariants(WORK)
        # Certifying the runtime is what releases it, through the gate.
        self.authority.certify_contract(V12, "reference")
        self.core.satisfy_gate(WORK, operation_id=self.op(),
                               gate=answer["gate"],
                               evidence={"kind": "certified-profile",
                                         "profile": "reference"})
        self.assertTrue(self.core.project_work(WORK)["ready"])
        # And the FIRST claim under the new contract mints generation one, on
        # the same Work that was v11 a moment ago.
        self.assertEqual(
            self.core.claim(WORK, CLAUDE, operation_id=self.op()
                            )["assignment"]["generation"], 1)

    def test_the_contract_compare_and_swap_is_exact(self):
        assignment = self.claimed(contract=V11)
        self.authority.permit_contract_transition(V11, V12)
        with self.assertRaises(Refusal) as caught:
            self.core.advance_contract(
                assignment, operation_id=self.op(), expect_contract=V12,
                target_contract=V11, rationale="wrong way")
        self.assertIn("stale", str(caught.exception))
        self.assertEqual(self.core.project_work(WORK)["contract"], V11)

    def test_an_unpermitted_transition_is_refused_by_policy(self):
        assignment = self.claimed(contract=V11)
        with self.assertRaises(Refusal) as caught:
            self.core.advance_contract(
                assignment, operation_id=self.op(), expect_contract=V11,
                target_contract=V12, rationale="not permitted")
        self.assertIn("not permitted", str(caught.exception))
        self.assertEqual(self.core.project_work(WORK)["contract"], V11)
        self.assertEqual(self.core.contract_events(WORK), [])
        # And the assignment survived, because an ordinary refusal writes
        # nothing at all.
        self.assertEqual(self.core.assignment_of(WORK), assignment)


class CanonicalActivity(WorkflowCase):

    def test_an_activity_is_idempotent_under_its_own_key(self):
        assignment = self.claimed()
        first = self.core.activity(assignment, key="wrote-the-file")
        second = self.core.activity(assignment, key="wrote-the-file")
        self.assertEqual(first["seq"], second["seq"])
        self.assertEqual(len(self.core.activities(WORK)), 1)
        self.core.activity(assignment, key="ran-the-tests")
        self.assertEqual(len(self.core.activities(WORK)), 2)

    def test_an_activity_belongs_to_an_exact_assignment(self):
        assignment = self.claimed()
        self.core.end(assignment, operation_id=self.op())
        with self.assertRaises(Refusal):
            self.core.activity(assignment, key="too-late")
        self.assertEqual(self.core.activities(WORK), [])

    def test_a_v11_activity_keys_correctly_despite_a_null_generation(self):
        # SQLite treats NULLs as distinct in a unique index, so a v11
        # assignment -- which mints no generation -- would insert the same
        # activity twice and the idempotency key would silently stop working.
        assignment = self.claimed(contract=V11)
        self.assertIsNone(assignment["generation"])
        self.core.activity(assignment, key="same-key")
        self.core.activity(assignment, key="same-key")
        self.assertEqual(len(self.core.activities(WORK)), 1)


class Publication(WorkflowCase):

    def test_a_proposal_says_what_it_was_built_from(self):
        assignment, answer = self.published()
        self.assertEqual(answer["target"], "base-1")
        for name, value in DIGESTS.items():
            self.assertEqual(answer[name], value)
        proposal = self.authority.proposal("proposal-1")
        # THE FULL FOUR-PART IDENTITY, nested, like every other projection.
        # Cut 4's first draft answered in bare columns even though cut 2 had
        # already corrected `assignment_events` to do this -- so the correction
        # is a shared projector rather than four more hand-written dicts.
        self.assertEqual(proposal["assignment_ref"], assignment)
        self.assertEqual(answer["assignment_ref"], assignment)
        self.assertNotIn("participant", proposal)
        self.assertNotIn("work_id", proposal)
        for name, value in DIGESTS.items():
            self.assertEqual(proposal[name], value)

    def test_every_digest_is_required(self):
        # The frozen host took ONE undifferentiated digest, so a published
        # candidate could not say what it had been built FROM -- the input it
        # consumed, the policy it ran under, or the frozen output it came from.
        assignment = self.claimed()
        # `result_id` is an opaque IDENTITY rather than a digest, so it is
        # refused one rule earlier and by name; the four digests are covered by
        # the loop below.
        for what, value in [("absent", ""), ("not text", 7), ("none", None),
                            ("one with a space", "has a space")]:
            with self.subTest(missing="result_id", what=what):
                with self.assertRaises(Refusal) as caught:
                    self.core.publish(assignment, operation_id=self.op(),
                                      proposal_id="proposal-1",
                                      **{**DIGESTS, "result_id": value})
                self.assertIn("result id", str(caught.exception))
        for missing in ("result_digest", "candidate_digest", "input_digest",
                        "policy_digest"):
            for what, value in [("absent", ""), ("not text", 7),
                                ("none", None)]:
                with self.subTest(missing=missing, what=what):
                    digests = {**DIGESTS, missing: value}
                    with self.assertRaises(Refusal) as caught:
                        self.core.publish(assignment,
                                          operation_id=self.op(),
                                          proposal_id="proposal-1", **digests)
                    # AND IT SAYS WHICH ONE.  "a digest is missing" sends
                    # somebody to check all five; naming it is the whole value
                    # of a per-digest check over a generic text rule.
                    self.assertIn(missing, str(caught.exception))
        with self.assertRaises(Refusal):
            self.authority.proposal("proposal-1")

    def test_a_proposal_identity_reused_for_different_bytes_refuses(self):
        # LATER BYTES ARE A NEW PROPOSAL.  A candidate is immutable, so an id
        # reused for different content is a collision rather than an edit.
        assignment, _answer = self.published()
        with self.assertRaises(Refusal) as caught:
            self.core.publish(assignment, operation_id=self.op(),
                              proposal_id="proposal-1",
                              **{**DIGESTS, "candidate_digest": "sha256:other"})
        self.assertIn("different bytes", str(caught.exception))
        self.assertEqual(self.authority.proposal("proposal-1")["candidate_digest"],
                         CANDIDATE)
        # And the same bytes under a NEW operation id answer with the same
        # proposal rather than refusing.
        again = self.core.publish(assignment, operation_id=self.op(),
                                  proposal_id="proposal-1", **DIGESTS)
        self.assertEqual(again["candidate_digest"], CANDIDATE)

    def test_publication_requires_a_v12_assignment_contract(self):
        assignment = self.claimed(contract=V11)
        with self.assertRaises(Refusal) as caught:
            self.core.publish(assignment, operation_id=self.op(),
                              proposal_id="proposal-1", **DIGESTS)
        self.assertIn("v12", str(caught.exception))


class CutFourReviewFindings(WorkflowCase):
    """The three W151 contract gaps the independent cut-4 review found."""

    def test_a_result_identity_names_one_set_of_bytes(self):
        # [P1 1] `result_id` had only the text rule, so the SAME frozen result
        # identity could be published twice with CONTRADICTORY digests -- naming
        # two different things, with nothing downstream able to tell which.
        assignment = self.claimed()
        self.core.publish(assignment, operation_id=self.op(),
                          proposal_id="proposal-1", **DIGESTS)
        with self.assertRaises(Refusal) as caught:
            self.core.publish(assignment, operation_id=self.op(),
                              proposal_id="proposal-2",
                              **{**DIGESTS, "result_digest": "sha256:other"})
        self.assertIn("already bound", str(caught.exception))
        # CONSISTENT REUSE STAYS PERMITTED: one frozen result may back several
        # proposals, which is why the rule is about contradiction rather than
        # about reuse.
        second = self.core.publish(assignment, operation_id=self.op(),
                                   proposal_id="proposal-2", **DIGESTS)
        self.assertEqual(second["result_id"], DIGESTS["result_id"])
        self.assertEqual(len(self.authority.receipts("proposal-2")), 0)
        self.assertEqual(self.authority.proposal("proposal-2")["result_digest"],
                         DIGESTS["result_digest"])

    def test_a_result_identity_names_the_assignment_that_made_it(self):
        # A frozen result is produced BY an assignment.  The same identity
        # appearing under a different one is not reuse, it is a claim that two
        # producers made the same bytes -- and this boundary cannot know that.
        first = self.claimed()
        self.core.publish(first, operation_id=self.op(),
                          proposal_id="proposal-1", **DIGESTS)
        self.core.end(first, operation_id=self.op())
        second = self.core.claim(WORK, CLAUDE, operation_id=self.op())["assignment"]
        self.assertEqual(second["generation"], 2)
        with self.assertRaises(Refusal) as caught:
            self.core.publish(second, operation_id=self.op(),
                              proposal_id="proposal-2", **DIGESTS)
        self.assertIn("different assignment", str(caught.exception))
        # And a malformed one never reaches the journal at all.
        with self.assertRaises(Refusal):
            self.core.publish(second, operation_id="never-used",
                              proposal_id="proposal-3",
                              **{**DIGESTS, "result_id": "has a space"})
        self.assertIsNone(self.core.operation_record("never-used"))

    def test_the_canonical_target_is_read_semantically(self):
        # [P1 2] `policy` is deliberately generic -- any owned JSON document --
        # and this accessor handed whatever it found into a durable column.  A
        # dict reached parameter binding as a raw `ProgrammingError`; an EMPTY
        # STRING published successfully, which is worse, because the proposal was
        # then bound to no target at all.
        assignment = self.claimed()
        for what, value in [("a document", {"a": 1}), ("a list", ["a"]),
                            ("empty text", ""), ("a number", 7),
                            ("true", True), ("none", None)]:
            with self.subTest(what=what):
                self.authority.set_policy("canonical_target", value)
                with self.assertRaises(Refusal):
                    self.authority.canonical_target()
                with self.assertRaises(Refusal):
                    self.core.publish(assignment, operation_id=self.op(),
                                      proposal_id="proposal-1", **DIGESTS)
        with self.assertRaises(Refusal):
            self.authority.proposal("proposal-1")
        # The default and an ordinary value both read cleanly.
        self.authority.set_policy("canonical_target", "base-2")
        self.assertEqual(self.authority.canonical_target(), "base-2")
        self.assertEqual(
            self.core.publish(assignment, operation_id=self.op(),
                              proposal_id="proposal-1", **DIGESTS)["target"],
            "base-2")

    def test_a_malformed_target_also_stops_integration(self):
        # The other side effect the accessor guards: integration compares the
        # canonical target and then WRITES it.
        self.grant_each()
        self.published()
        self.through_approval()
        self.authority.set_policy("canonical_target", {"a": 1})
        with self.assertRaises(Refusal):
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertIsNone(self.authority.receipt("proposal-1", "integration"))
        self.assertEqual(self.authority.integration_attempts("proposal-1"), [])
        self.assertIsNone(self.core.operation_record("int-op"))

    def test_every_cut_four_projection_answers_with_the_whole_identity(self):
        # [P1 3] Cut 2 corrected `assignment_events` to answer with a nested
        # `assignment_ref`, and cut 4 then added four more projections that
        # answered in BARE COLUMNS again.  One shared projector now, and this
        # case walks all of them.
        assignment = self.claimed()
        self.core.activity(assignment, key="wrote-the-file")
        published = self.core.publish(assignment, operation_id=self.op(),
                                      proposal_id="proposal-1", **DIGESTS)
        self.authority.permit_contract_transition(V12, "v12-next")
        self.authority.certify_contract("v12-next", "reference")
        self.core.advance_contract(assignment, operation_id=self.op(),
                                   expect_contract=V12,
                                   target_contract="v12-next",
                                   rationale="onward")
        answers = {
            "activity answer": self.core.activities(WORK)[0],
            "assignment event": self.core.assignment_events(WORK)[0],
            "contract event": self.core.contract_events(WORK)[0],
            "proposal read": self.authority.proposal("proposal-1"),
            "publish answer": published,
        }
        for what, answer in answers.items():
            with self.subTest(what=what):
                self.assertEqual(answer["assignment_ref"], assignment, what)
                self.assertEqual(
                    answer["assignment_ref"]["work_ref"]["authority_uuid"],
                    UUID, what)
                # And NONE of them answers in parts any more.
                for bare in ("participant", "generation", "work_id"):
                    self.assertNotIn(bare, answer, f"{what}: {bare}")

    def test_result_identity_and_projection_survive_restart_as_fresh_data(self):
        """The corrected binding is durable, and its read is never a live row."""
        assignment = self.claimed()
        self.core.publish(assignment, operation_id=self.op(),
                          proposal_id="proposal-1", **DIGESTS)
        self.authority.dispose()
        self.authority = Authority.open(self.path,
                                        expected_authority_uuid=UUID,
                                        clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core

        projected = self.authority.proposal("proposal-1")
        self.assertEqual(projected["assignment_ref"], assignment)
        projected["assignment_ref"]["work_ref"]["authority_uuid"] = "changed"
        projected["result_digest"] = "changed"
        reread = self.authority.proposal("proposal-1")
        self.assertEqual(reread["assignment_ref"], assignment)
        self.assertEqual(reread["result_digest"], DIGESTS["result_digest"])

        refused_operation = self.op()
        with self.assertRaises(Refusal) as caught:
            self.core.publish(assignment, operation_id=refused_operation,
                              proposal_id="proposal-2",
                              **{**DIGESTS, "result_digest": "sha256:other"})
        self.assertIn("already bound", str(caught.exception))
        self.assertIsNone(self.authority.operation_record(refused_operation))


class TheFourReceipts(WorkflowCase):

    def test_four_ordered_immutable_attributable_receipts(self):
        self.grant_each()
        self.published()
        self.through_approval()
        self.core.integrate(proposal_id="proposal-1", integration_id="int-1",
                            actor="baton.integrator", operation_id=self.op())
        receipts = self.authority.receipts("proposal-1")
        self.assertEqual([row["kind"] for row in receipts],
                         ["approval", "integration", "review", "verification"])
        # EVERY receipt names its own actor and what that actor was LOOKING AT.
        for row in receipts:
            self.assertEqual(row["candidate_digest"], CANDIDATE)
            self.assertEqual(row["target"], "base-1")
            self.assertNotEqual(row["actor"], CLAUDE)
        self.assertEqual(
            {row["kind"]: row["actor"] for row in receipts},
            {"verification": GEMINI, "review": CODEX, "approval": SLAW,
             "integration": "baton.integrator"})
        # And each is IMMUTABLE: a second receipt of the same kind refuses.
        for kind, call in [
                ("verification", lambda: self.core.verify(
                    proposal_id="proposal-1", verification_id="ver-2",
                    actor=GEMINI, observation="failed",
                    operation_id=self.op())),
                ("review", lambda: self.core.review(
                    proposal_id="proposal-1", review_id="rev-2", actor=CODEX,
                    disposition="rejected", operation_id=self.op())),
                ("approval", lambda: self.core.approve(
                    proposal_id="proposal-1", approval_id="app-2", actor=SLAW,
                    disposition="denied", operation_id=self.op(),
                    policy_generation=8)),
                ("integration", lambda: self.core.integrate(
                    proposal_id="proposal-1", integration_id="int-2",
                    actor="baton.integrator", operation_id=self.op()))]:
            with self.subTest(kind=kind):
                with self.assertRaises(Refusal) as caught:
                    call()
                self.assertIn("immutable", str(caught.exception))
        self.assertEqual(len(self.authority.receipts("proposal-1")), 4)

    def test_the_order_is_enforced_and_not_merely_expected(self):
        self.grant_each()
        self.published()
        # Review before verification, approval before review, integration
        # before any of them.
        with self.assertRaises(Refusal) as caught:
            self.core.review(proposal_id="proposal-1", review_id="rev-1",
                             actor=CODEX, disposition="accepted",
                             operation_id=self.op())
        self.assertIn("passed verification", str(caught.exception))
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.core.approve(proposal_id="proposal-1", approval_id="app-1",
                              actor=SLAW, disposition="approved",
                              operation_id=self.op(), policy_generation=7)
        self.assertIn("accepted technical review", str(caught.exception))
        with self.assertRaises(Refusal) as caught:
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id=self.op())
        self.assertIn("accepted technical review", str(caught.exception))
        self.assertEqual([row["kind"] for row in
                          self.authority.receipts("proposal-1")],
                         ["verification"])

    def test_a_failed_verification_stops_the_chain(self):
        self.grant_each()
        self.published()
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="failed",
                         operation_id=self.op())
        for what, call in [
                ("review", lambda: self.core.review(
                    proposal_id="proposal-1", review_id="rev-1", actor=CODEX,
                    disposition="accepted", operation_id=self.op())),
                ("integration", lambda: self.core.integrate(
                    proposal_id="proposal-1", integration_id="int-1",
                    actor="baton.integrator", operation_id=self.op()))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()

    def test_only_the_dispositions_each_step_defines_are_accepted(self):
        self.grant_each()
        self.published()
        for what, call in [
                ("verification", lambda d: self.core.verify(
                    proposal_id="proposal-1", verification_id="ver-1",
                    actor=GEMINI, observation=d, operation_id=self.op())),
                ("review", lambda d: self.core.review(
                    proposal_id="proposal-1", review_id="rev-1", actor=CODEX,
                    disposition=d, operation_id=self.op()))]:
            for disposition in ("approved", "yes", "", None, 7, "PASSED"):
                with self.subTest(what=what, disposition=disposition):
                    with self.assertRaises(Refusal):
                        call(disposition)
        self.assertEqual(self.authority.receipts("proposal-1"), [])


class GapsIFoundByProbingMyOwnCut(WorkflowCase):
    """Probed before handing over, because the last two reviews found things a
    passing suite did not."""

    def test_a_receipt_identity_is_claimed_once(self):
        # Found by probing: a `receipt_id` reused across kinds on one proposal,
        # or across two proposals, hit the table's uniqueness and left as
        # `IntegrityError` -- a FAULT, which takes the whole transaction down
        # and journals nothing, so the caller got an unexplained crash instead
        # of "that identity is taken".  `publish` already had this rule for
        # proposal identities; the receipts did not.
        self.grant_each()
        assignment = self.claimed()
        for proposal_id in ("proposal-1", "proposal-2"):
            self.core.publish(assignment, operation_id=self.op(),
                              proposal_id=proposal_id, **DIGESTS)
        self.core.verify(proposal_id="proposal-1", verification_id="shared-id",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        for what, call in [
                ("another kind on the same proposal",
                 lambda: self.core.review(
                     proposal_id="proposal-1", review_id="shared-id",
                     actor=CODEX, disposition="accepted",
                     operation_id=self.op())),
                ("the same kind on another proposal",
                 lambda: self.core.verify(
                     proposal_id="proposal-2", verification_id="shared-id",
                     actor=GEMINI, observation="passed",
                     operation_id=self.op())),
                ("an integration receipt",
                 lambda: self.core.integrate(
                     proposal_id="proposal-2", integration_id="shared-id",
                     actor="baton.integrator", operation_id=self.op()))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                self.assertIn("already the", str(caught.exception))
        # ONE receipt exists, and the chain still works with its own ids.
        self.assertEqual(len(self.authority.receipts("proposal-1")), 1)
        self.core.review(proposal_id="proposal-1", review_id="rev-1",
                         actor=CODEX, disposition="accepted",
                         operation_id=self.op())
        self.assertEqual(len(self.authority.receipts("proposal-1")), 2)

    def test_a_receipt_id_is_a_frozen_opaque_identity(self):
        self.grant_each()
        assignment = self.claimed()
        self.core.publish(assignment, operation_id=self.op(),
                          proposal_id="proposal-1", **DIGESTS)
        for what, receipt_id in [("a megabyte", "y" * 1_000_000),
                                 ("one with a space", "ver 1"),
                                 ("an empty one", ""),
                                 ("none", None),
                                 ("unencodable text", "ver\ud800")]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.verify(proposal_id="proposal-1",
                                     verification_id=receipt_id, actor=GEMINI,
                                     observation="passed",
                                     operation_id=self.op())
        self.assertEqual(self.authority.receipts("proposal-1"), [])


class ConfiguredCapabilities(WorkflowCase):

    def test_a_receipt_is_written_by_the_configured_actor(self):
        # The frozen host stored dispositions with NO actor and no
        # authorization, so one consumer could publish a candidate,
        # self-verify, self-review, self-approve, integrate it into the
        # canonical target and close the Work.
        self.published()
        for what, call in [
                ("verification", lambda actor: self.core.verify(
                    proposal_id="proposal-1", verification_id="ver-1",
                    actor=actor, observation="passed",
                    operation_id=self.op())),
                ("review", lambda actor: self.core.review(
                    proposal_id="proposal-1", review_id="rev-1", actor=actor,
                    disposition="accepted", operation_id=self.op())),
                ("approval", lambda actor: self.core.approve(
                    proposal_id="proposal-1", approval_id="app-1", actor=actor,
                    disposition="approved", operation_id=self.op(),
                    policy_generation=7)),
                ("integration", lambda actor: self.core.integrate(
                    proposal_id="proposal-1", integration_id="int-1",
                    actor=actor, operation_id=self.op()))]:
            for who in (CLAUDE, "", None, 7, "baton.nobody"):
                with self.subTest(what=what, who=who):
                    with self.assertRaises(Refusal):
                        call(who)
        self.assertEqual(self.authority.receipts("proposal-1"), [])

    def test_a_capability_refusal_writes_nothing_and_stays_retryable(self):
        # An ORDINARY refusal, so an actor granted the capability afterwards may
        # simply retry -- with a NEW operation id, because the operand set is
        # the same and the identity was never consumed.
        self.published()
        with self.assertRaises(Refusal):
            self.core.verify(proposal_id="proposal-1",
                             verification_id="ver-1", actor=GEMINI,
                             observation="passed", operation_id="ver-op")
        self.assertIsNone(self.core.operation_record("ver-op"))
        self.authority.grant_capability(GEMINI, "verify")
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id="ver-op")
        self.assertEqual(self.core.operation_record("ver-op")["state"],
                         "committed")

    def test_one_participant_may_hold_several_and_the_receipts_stay_distinct(self):
        # §10.12 permits it.  What a deployment cannot do is leave the question
        # unasked, which is what an actorless receipt does.
        for capability in CAPABILITIES:
            self.authority.grant_capability(GEMINI, capability)
        self.published()
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        self.core.review(proposal_id="proposal-1", review_id="rev-1",
                         actor=GEMINI, disposition="accepted",
                         operation_id=self.op())
        self.core.approve(proposal_id="proposal-1", approval_id="app-1",
                          actor=GEMINI, disposition="approved",
                          operation_id=self.op(), policy_generation=7)
        self.core.integrate(proposal_id="proposal-1", integration_id="int-1",
                            actor=GEMINI, operation_id=self.op())
        receipts = self.authority.receipts("proposal-1")
        self.assertEqual(len(receipts), 4)
        self.assertEqual({row["actor"] for row in receipts}, {GEMINI})
        self.assertEqual({row["receipt_id"] for row in receipts},
                         {"ver-1", "rev-1", "app-1", "int-1"})


class PolicyGeneration(WorkflowCase):

    def test_an_approval_binds_the_generation_it_was_granted_under(self):
        self.grant_each()
        self.published()
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        self.core.review(proposal_id="proposal-1", review_id="rev-1",
                         actor=CODEX, disposition="accepted",
                         operation_id=self.op())
        for what, generation in [("absent", None), ("zero", 0),
                                 ("negative", -1), ("a float", 1.0),
                                 ("true", True), ("text", "7")]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.approve(proposal_id="proposal-1",
                                      approval_id="app-1", actor=SLAW,
                                      disposition="approved",
                                      operation_id=self.op(),
                                      policy_generation=generation)
        answer = self.core.approve(proposal_id="proposal-1",
                                   approval_id="app-1", actor=SLAW,
                                   disposition="approved",
                                   operation_id="app-op", policy_generation=7)
        self.assertEqual(answer["policy_generation"], 7)
        self.assertEqual(
            self.authority.receipt("proposal-1", "approval")["policy_generation"],
            7)

    def test_the_generation_rides_the_operation_identity(self):
        # The frozen host had it OUTSIDE the signature, so committing one
        # operation under generation 7 and resubmitting the same id under 8
        # REPLAYED success instead of colliding -- one identity taking two
        # different durable meanings.
        self.grant_each()
        self.published()
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        self.core.review(proposal_id="proposal-1", review_id="rev-1",
                         actor=CODEX, disposition="accepted",
                         operation_id=self.op())
        self.core.approve(proposal_id="proposal-1", approval_id="app-1",
                          actor=SLAW, disposition="approved",
                          operation_id="app-op", policy_generation=7)
        with self.assertRaises(Refusal) as caught:
            self.core.approve(proposal_id="proposal-1", approval_id="app-1",
                              actor=SLAW, disposition="approved",
                              operation_id="app-op", policy_generation=8)
        self.assertIn("different operands", str(caught.exception))
        self.assertNotEqual(
            signature_of("approval", {"proposal_id": "p", "receipt_id": "r",
                                      "actor": SLAW, "disposition": "approved",
                                      "policy_generation": 7}),
            signature_of("approval", {"proposal_id": "p", "receipt_id": "r",
                                      "actor": SLAW, "disposition": "approved",
                                      "policy_generation": 8}))


class Integration(WorkflowCase):

    def test_integration_moves_the_canonical_target(self):
        self.grant_each()
        self.published()
        self.through_approval()
        self.assertEqual(self.authority.canonical_target(), "base-1")
        answer = self.core.integrate(proposal_id="proposal-1",
                                     integration_id="int-1",
                                     actor="baton.integrator",
                                     operation_id=self.op())
        self.assertEqual(answer["disposition"], "integrated")
        self.assertEqual(self.authority.canonical_target(), CANDIDATE)
        self.assertEqual(self.authority.integration_attempts("proposal-1"), [])

    def test_a_stale_target_journals_its_attempt_and_refuses_DURABLY(self):
        # THE ONE TRANSITION WHOSE REFUSAL CAN WRITE SOMETHING.  The attempt is
        # journalled beside the proposal BEFORE it refuses, so the retry
        # replays that refusal instead of appending a second attempt or taking
        # a different outcome under one identity.
        self.grant_each()
        self.published()
        self.through_approval()
        # The canonical target moves under the proposal's feet.
        self.authority.set_policy("canonical_target", "sha256:somebody-else")
        with self.assertRaises(Refusal) as caught:
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertIn("canonical target moved", str(caught.exception))
        attempts = self.authority.integration_attempts("proposal-1")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["reason"], "stale-target")
        self.assertEqual(attempts[0]["target"], "sha256:somebody-else")
        # THE REFUSAL IS ITSELF A COMMITTED OUTCOME, bound to the identity.
        record = self.core.operation_record("int-op")
        self.assertEqual(record["state"], "refused")
        # And the retry REPLAYS it rather than appending a second attempt.
        with self.assertRaises(Refusal) as again:
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertEqual(str(again.exception), str(caught.exception))
        self.assertEqual(len(self.authority.integration_attempts("proposal-1")), 1)
        # No receipt was written and the target did not move.
        self.assertIsNone(self.authority.receipt("proposal-1", "integration"))
        self.assertEqual(self.authority.canonical_target(),
                         "sha256:somebody-else")

    def test_approval_is_the_gate_it_claims_to_be(self):
        # Verification passed and review accepted, and NOTHING ELSE.  Without a
        # case here, the approval check is shadowed by the review check that
        # fires before it -- so the rule "integration requires explicit
        # approval" would be untested even though three cases mention it.
        self.grant_each()
        self.published()
        self.core.verify(proposal_id="proposal-1", verification_id="ver-1",
                         actor=GEMINI, observation="passed",
                         operation_id=self.op())
        self.core.review(proposal_id="proposal-1", review_id="rev-1",
                         actor=CODEX, disposition="accepted",
                         operation_id=self.op())
        with self.assertRaises(Refusal) as caught:
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertIn("explicit approval", str(caught.exception))
        # AND THIS REFUSAL IS ORDINARY: it wrote nothing, so the identity stays
        # usable.  Only the refusal that journalled its attempt is durable, and
        # this one journalled nothing.
        self.assertIsNone(self.core.operation_record("int-op"))
        self.assertEqual(self.authority.integration_attempts("proposal-1"), [])
        self.assertEqual(self.authority.canonical_target(), "base-1")
        # A DENIED approval is not an approval either.
        self.core.approve(proposal_id="proposal-1", approval_id="app-1",
                          actor=SLAW, disposition="denied",
                          operation_id=self.op(), policy_generation=7)
        with self.assertRaises(Refusal):
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertIsNone(self.core.operation_record("int-op"))

    def test_a_pre_approval_refusal_writes_nothing_and_stays_retryable(self):
        # The frozen host had the durable flag on the CALL, so EVERY
        # integration refusal -- including a pre-approval one that wrote
        # nothing -- was recorded REFUSED and permanently closed.  Only the
        # refusal that actually journalled its attempt is durable.
        self.grant_each()
        self.published()
        with self.assertRaises(Refusal):
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-1",
                                actor="baton.integrator",
                                operation_id="int-op")
        self.assertIsNone(self.core.operation_record("int-op"))
        self.assertEqual(self.authority.integration_attempts("proposal-1"), [])
        # So the SAME identity works once the preconditions hold.
        self.through_approval()
        self.core.integrate(proposal_id="proposal-1", integration_id="int-1",
                            actor="baton.integrator", operation_id="int-op")
        self.assertEqual(self.core.operation_record("int-op")["state"],
                         "committed")


class AuthorizedClose(WorkflowCase):

    def test_an_unclaimed_close_is_authorized_and_manufactures_no_claim(self):
        # Ruling 4: no execution claim is manufactured merely to reach a
        # terminal state.
        self.grant_each()
        self.work()
        answer = self.core.close(WORK, operation_id=self.op(),
                                 outcome="satisfying", rationale="done",
                                 actor="baton.closer")
        self.assertIsNone(answer["assignment"])
        projected = self.core.project_work(WORK)
        self.assertEqual(projected["status"], "closed")
        self.assertIsNone(projected["phase"])
        self.assertEqual(projected["outcome"], "satisfying")
        self.assertEqual(self.core.assignment_events(WORK), [])
        self.core.assert_invariants(WORK)

    def test_a_close_over_a_live_assignment_must_name_it_exactly(self):
        self.grant_each()
        assignment = self.claimed()
        with self.assertRaises(Refusal) as caught:
            self.core.close(WORK, operation_id=self.op(), outcome="cancelled",
                            rationale="abandoned", actor="baton.closer")
        self.assertIn("exact assignment identity", str(caught.exception))
        self.assertEqual(self.core.assignment_of(WORK), assignment)
        # A stale identity refuses too, and the Work stays open.
        with self.assertRaises(Refusal):
            self.core.close(WORK, operation_id=self.op(), outcome="cancelled",
                            rationale="abandoned", actor="baton.closer",
                            expect={**assignment, "generation": 9})
        self.assertEqual(self.core.project_work(WORK)["status"], "open")
        # The exact identity closes it, fencing the generation on the way.
        answer = self.core.close(WORK, operation_id=self.op(),
                                 outcome="cancelled", rationale="abandoned",
                                 actor="baton.closer", expect=assignment)
        self.assertEqual(answer["assignment"], assignment)
        self.assertEqual(self.core.fenced_generations(WORK), [1])
        self.assertIsNone(self.core.slot_holder(CLAUDE))
        self.assertEqual(
            [event["cause"] for event in self.core.assignment_events(WORK)],
            ["claimed", "close:cancelled"])
        self.core.assert_invariants(WORK)

    def test_holding_the_assignment_is_not_authority_to_close(self):
        # §7 says an AUTHORIZED actor holding the configured close capability,
        # and the frozen host had neither an actor nor a check.
        assignment = self.claimed()
        with self.assertRaises(Refusal) as caught:
            self.core.close(WORK, operation_id=self.op(), outcome="cancelled",
                            rationale="mine now", actor=CLAUDE,
                            expect=assignment)
        self.assertIn("close capability", str(caught.exception))
        self.assertEqual(self.core.project_work(WORK)["status"], "open")

    def test_a_close_names_the_work_it_ends(self):
        # The cut-2 lesson, applied here before somebody has to find it: an
        # identity is compared against the Work it belongs to or not at all.
        self.grant_each()
        self.work(WORK)
        self.work(OTHER)
        self.core.add_route_handler(ROUTE, GEMINI)
        other = self.core.claim(OTHER, GEMINI, operation_id=self.op())["assignment"]
        with self.assertRaises(Refusal) as caught:
            self.core.close(WORK, operation_id=self.op(), outcome="cancelled",
                            rationale="wrong Work", actor="baton.closer",
                            expect=other)
        self.assertIn(OTHER, str(caught.exception))
        self.assertEqual(self.core.project_work(WORK)["status"], "open")
        self.assertEqual(self.core.assignment_of(OTHER), other)

    def test_a_close_needs_a_known_outcome_and_a_rationale(self):
        self.grant_each()
        self.work()
        self.assertEqual(sorted(INTAKE_OUTCOMES),
                         ["cancelled", "non-satisfying", "rejected",
                          "satisfying"])
        for what, kwargs in [
                ("an unknown outcome",
                 {"outcome": "finished", "rationale": "done"}),
                ("no rationale", {"outcome": "satisfying", "rationale": ""}),
                ("a rationale that is not text",
                 {"outcome": "satisfying", "rationale": 7})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    self.core.close(WORK, operation_id=self.op(),
                                    actor="baton.closer", **kwargs)
        self.assertEqual(self.core.project_work(WORK)["status"], "open")

    def test_a_closed_work_is_closed_once(self):
        self.grant_each()
        self.work()
        self.core.close(WORK, operation_id="close-op", outcome="satisfying",
                        rationale="done", actor="baton.closer")
        # The same operation REPLAYS.
        self.assertEqual(
            self.core.close(WORK, operation_id="close-op",
                            outcome="satisfying", rationale="done",
                            actor="baton.closer")["outcome"], "satisfying")
        # A different one refuses, because the Work is already closed.
        with self.assertRaises(Refusal) as caught:
            self.core.close(WORK, operation_id=self.op(),
                            outcome="rejected", rationale="again",
                            actor="baton.closer")
        self.assertIn("already closed", str(caught.exception))
        self.assertEqual(self.core.project_work(WORK)["outcome"], "satisfying")

    def test_a_terminal_work_admits_no_claim(self):
        self.grant_each()
        self.work()
        self.core.close(WORK, operation_id=self.op(), outcome="satisfying",
                        rationale="done", actor="baton.closer")
        with self.assertRaises(Refusal):
            self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.core.assert_invariants(WORK)


if __name__ == "__main__":
    unittest.main()
