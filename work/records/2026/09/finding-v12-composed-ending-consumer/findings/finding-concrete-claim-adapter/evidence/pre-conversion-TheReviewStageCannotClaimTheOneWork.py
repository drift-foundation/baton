# Retained pre-change bytes, W125032 claim125043. The exact class as it
# stood before the one conversion the approved allocation proposal names.
# Its escaping-Refusal expectation is superseded by the contained
# deferred outcome; the WRONG-ROUTE NEGATIVE ITSELF IS PRESERVED and a
# correctly routed same-Job positive belongs to W122060's routing
# provider, not here.

class TheReviewStageCannotClaimTheOneWork(ComposedOneJobCase):
    """W122060, the boundary the discharged gate uncovered, REPORTED.

    A composed Job's review stage is another assignment of the SAME Work, by
    configuration. With the gate cleared the review offer is issued and
    accepted, and the CLAIM is then refused by the Authority: `route
    'baton.impl' does not resolve to 'baton.reviewer'`. One Work carries one
    route, and nothing in this deployment's four paths moves it -- a v11 pass
    is the bootstrap ending's own handoff, and the composed implementation
    ending publishes a proposal and freezes a checkpoint instead.

    AND IT IS NOT CONTAINED. The Authority answers `authority.errors.Refusal`,
    which is not a `ContractRefusal`, so `_delegate` does not turn it into a
    deferred act -- it leaves the sweep entirely. That is a second fact worth
    separating from the first: whatever decides the routing, an uncontained
    fault out of an ordinary tick is its own defect.

    This case pins both. It is not a proof that the review stage works.
    """

    def test_the_reviewers_claim_is_refused_against_the_implementation_route(
            self):
        from baton_v12.authority import Refusal
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        held = self.implemented()
        with self.assertRaises(Refusal) as caught:
            for _ in range(4):
                tick(held.job, held.composed, now=fixtures.NOW)
        self.assertIn("does not resolve to", str(caught.exception))
        self.assertIn("baton.reviewer", str(caught.exception))


