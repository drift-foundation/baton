"""Independent token-era R2 reader regression; disposable store only."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody
from baton_v12.worker_manager.store import manager_signature
from test_hold_clearance import OnlyExactSettlementClearsOneHold


class TokenReadback(OnlyExactSettlementClearsOneHold):
    def test_direct_receipt_for_another_submission_does_not_lift(self):
        control, _composed, attempt_id, held = self.held_episode("review-r2-direct-token")
        wrong = "0" * 32 if held["claimant"] != "0" * 32 else "1" * 32
        document = self.answered(held, submission=wrong)["document"]
        body = {"attempt_id": attempt_id, "root": "result", "episode": 0,
                "helper_identity": held["helper_identity"], "observed": "wrong submission receipt",
                "accounted": custody.CUSTODY_DIRECT_ACT, "accounted_document": document}
        identity = custody._hold_identity(custody.CUSTODY_CLEARED_KIND, attempt_id, "result", 0)
        control.transact(identity, custody.CUSTODY_CLEARED_KIND,
                         manager_signature(custody.CUSTODY_CLEARED_KIND, body), lambda _c: dict(body))
        with self.assertRaises(ContractRefusal, msg="direct receipt readback must compare the echoed token to its hold"):
            custody.custody_holds(control, attempt_id, "result")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([TokenReadback("test_direct_receipt_for_another_submission_does_not_lift")])


if __name__ == "__main__":
    unittest.main()
