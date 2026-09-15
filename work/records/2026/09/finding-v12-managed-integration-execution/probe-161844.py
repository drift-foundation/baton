"""Check that the newly consumed fence document is actually closed."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts as owner
from tests.manager.test_attempts import ATTEMPT, AttemptCase
from tests.manager.test_reconciliation_worker import TheFencedBeforeStartProof


class FenceShapeReview(AttemptCase):
    cancelled = TheFencedBeforeStartProof.cancelled
    fenced = TheFencedBeforeStartProof.fenced

    def test_unknown_fence_member_refuses(self):
        self.cancelled()
        self.session._work["fenced_generations"][0]["unrecognized"] = "value"
        with self.assertRaises(ContractRefusal):
            owner.unstarted_cancellation_of(self.store, self.port, ATTEMPT)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FenceShapeReview))
    raise SystemExit(not result.wasSuccessful())
