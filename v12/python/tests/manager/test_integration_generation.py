"""A successful integration ADVANCES the approval generation, by design.

W197661, claim202052, corroborating review202028's independent reproduction
against this tree rather than taking its word for it.

WHY THIS FILE EXISTS. W197661's verifier carried an unconditional REQUIRED
check that the deployment's configured approval pin still equalled the
Authority's current generation, and treated its failure as evidence the
retained lifecycle had not completed. It is the opposite: a gate every success
fails.

THE MECHANISM, read off `baton_v12/authority/core.py integrate`:

  1. the authorization decision is taken FIRST, through `_require_capability`;
  2. `set_policy("canonical_target", proposal["candidate_digest"])` runs;
  3. `set_policy` calls `_bump_policy_generation` UNCONDITIONALLY;
  4. the integration receipt is written carrying the decision from step 1.

So a completed integration necessarily ends with the Authority one generation
past the one its own receipt records. The product source already knows this --
`tools/stage_execution.py:3103` says `_accepted_receipts` "checks the deployment
pin against the Authority's CURRENT generation before it issues anything, so
issuing at reconciliation time -- after the first Job's integration bumped that
generation -- can only ever refuse."

WHAT THIS DOES NOT CLAIM. It does not propose a product change, and it does not
say the advance is wrong. It fixes what may be concluded FROM the advance:
historical completion is proved by the owned proposal, result, target and
receipt, and the current pin comparison is a fact about FUTURE authorization.

NO DEPLOYMENT, NO ENGINE, NO STORE PATH. One temporary Authority per case,
through the existing fixture's public helpers.

WHY IT LIVES UNDER tests/manager AND NOT tests/authority. The Authority suite is
a REGISTERED gate: `tests/authority/test_catalog.py`
`test_the_suite_is_one_gate_and_not_a_pile_of_files` enumerates its files by
name, so adding one there means editing that catalog. Review201931 was explicit
about coordinating ownership of any required test registry before editing it,
and this file is W197661's corroboration of a mechanism rather than a new
Authority obligation -- so it sits with this Work's other suites and IMPORTS the
Authority fixture instead of registering against its gate.
"""

import unittest

from ..authority.test_contract import DIGESTS, UUID, WorkflowCase


class ASuccessfulIntegrationADVANCESTheGeneration(WorkflowCase):

    def integrated(self, proposal_id="proposal-1"):
        """One whole authorized workflow, ending in `integrate`."""
        self.grant_each()
        self.published()
        self.through_approval(proposal_id)
        before = self.core.policy_generation()
        answer = self.core.integrate(
            proposal_id=proposal_id, integration_id="int-1",
            actor="baton.integrator", operation_id=self.op("integrate"))
        return before, answer, self.core.policy_generation()

    def test_the_generation_is_ONE_HIGHER_afterwards(self):
        before, _, after = self.integrated()
        self.assertEqual(after, before + 1,
                         "set_policy(canonical_target) bumps unconditionally")

    def test_the_canonical_target_became_the_PROPOSAL_S_candidate(self):
        """The advance is not incidental: it is the target moving, which is
        what the deployment asked for."""
        self.integrated()
        self.assertEqual(self.core.canonical_target(),
                         DIGESTS["candidate_digest"])

    def test_the_RECEIPT_records_the_EARLIER_generation(self):
        """The decision is taken before the bump, so the receipt is one behind
        the Authority the moment it is written. THIS is why equality cannot be
        a gate on historical completion."""
        before, _, after = self.integrated()
        receipt = self.core.receipt("proposal-1", "integration")
        self.assertEqual(receipt["decision"]["policy_generation"], before)
        self.assertNotEqual(receipt["decision"]["policy_generation"], after)

    def test_so_PIN_EQUALITY_CANNOT_HOLD_after_a_success(self):
        """Stated as its own case because it is the whole conclusion: a
        deployment pinned to the generation its integration was accepted under
        NECESSARILY differs from its Authority once that integration succeeds."""
        before, _, after = self.integrated()
        configured_pin = before
        self.assertNotEqual(configured_pin, after)
        self.assertEqual(after, configured_pin + 1)

    def test_the_receipt_is_still_a_VALID_ACCEPTED_receipt(self):
        """The advance does not un-accept anything. Historical acceptance and
        current readiness are different facts about different moments."""
        self.integrated()
        receipt = self.core.receipt("proposal-1", "integration")
        self.assertEqual(receipt["disposition"], "integrated")
        self.assertEqual(receipt["proposal_id"], "proposal-1")
        self.assertEqual(receipt["candidate_digest"],
                         DIGESTS["candidate_digest"])


class TheADVANCEIsNotAPredicateOfSUCCESS(WorkflowCase):
    """Review202028: "Do not ... infer acceptance from merely current ==
    configured + 1." The shape is necessary, not sufficient."""

    def test_an_ORDINARY_POLICY_WRITE_advances_it_just_the_same(self):
        """Nothing was integrated here at all. A verifier concluding success
        from a one-step advance would accept this."""
        before = self.core.policy_generation()
        self.core.set_policy("something-else", "a value")
        self.assertEqual(self.core.policy_generation(), before + 1)
        self.assertIsNone(self.core.receipt("proposal-1", "integration"))

    def test_and_the_canonical_target_did_NOT_move(self):
        before = self.core.canonical_target()
        self.core.set_policy("something-else", "a value")
        self.assertEqual(self.core.canonical_target(), before)


class UNOWNEDEvidenceStillFAILS(WorkflowCase):
    """Review202028: "A mismatched/unowned receipt or terminal still fails."
    Proved against the Authority itself, so the verifier's bindings are
    checking something the owner agrees is distinguishable."""

    def test_ANOTHER_proposal_has_NO_integration_receipt(self):
        self.grant_each()
        self.published()
        self.through_approval()
        self.core.integrate(proposal_id="proposal-1", integration_id="int-1",
                            actor="baton.integrator",
                            operation_id=self.op("integrate"))
        self.assertIsNotNone(self.core.receipt("proposal-1", "integration"))
        self.assertIsNone(self.core.receipt("proposal-2", "integration"))

    def test_an_integration_receipt_is_IMMUTABLE(self):
        """So a receipt cannot be re-written later to carry the generation a
        weaker verifier wanted to see."""
        self.grant_each()
        self.published()
        self.through_approval()
        self.core.integrate(proposal_id="proposal-1", integration_id="int-1",
                            actor="baton.integrator",
                            operation_id=self.op("integrate"))
        with self.assertRaises(Exception) as caught:
            self.core.integrate(proposal_id="proposal-1",
                                integration_id="int-2",
                                actor="baton.integrator",
                                operation_id=self.op("integrate"))
        self.assertIn("immutable", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
