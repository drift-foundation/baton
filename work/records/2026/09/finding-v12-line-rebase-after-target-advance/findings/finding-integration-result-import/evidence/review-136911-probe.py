"""R1/R2 correction checks and the existing post-execution grant cutpoint.

The custom case records the candidate's defect; its assertions are evidence,
not accepted product expectations. All owners operate on disposable fixtures.
"""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import abandon_lease, block_target
from tests.integration.test_execution import (
    PostImportVerifier, TheAuthorizedResultIsImportedAndSettled)
from tests.integration.test_reconciliation import TARGET, REFERENCE


class Review(TheAuthorizedResultIsImportedAndSettled):
    def test_grant_ended_during_verification_still_advances_reference(self):
        held = self.through_authorization()
        case = self

        class Ended(PostImportVerifier):
            def verify_imported(self, basis):
                answer = super().verify_imported(basis)
                lease = case.store._connection.execute(
                    "SELECT * FROM leases WHERE state = 'live'").fetchone()
                block_target(case.store, canonical_target_id=TARGET,
                             entry_id=lease["entry_id"],
                             lease_id=lease["lease_id"], fence=lease["fence"],
                             reason="integrity",
                             detail={"observed": "review: holder recovered while verification finished"})
                abandon_lease(case.store, lease_id=lease["lease_id"],
                              fence=lease["fence"], recovery={
                                  "attempt_id": lease["attempt_id"],
                                  "evidence": "review: execution stopped before return"})
                return answer

        before = self.git(self.target, "rev-parse", REFERENCE)
        with self.assertRaises(ContractRefusal) as caught:
            self.tick(held, verifier=Ended(self))
        after = self.git(self.target, "rev-parse", REFERENCE)
        receipt = self.authority.receipt(held["derived_proposal_id"], "integration")
        self.assertNotEqual(before, after)
        self.assertIsNotNone(receipt)
        print(json.dumps({"observation": "reference and Authority advanced after grant abandoned during verification",
                          "before": before, "after": after,
                          "receipt": receipt, "late_refusal": str(caught.exception)}))


if __name__ == "__main__":
    names = ["test_the_required_post_import_tests_ACTUALLY_RUN",
             "test_a_FAILED_post_import_test_holds_and_never_advances",
             "test_a_GRANT_FOR_ANOTHER_PROPOSAL_writes_nothing"]
    suite = unittest.TestSuite([TheAuthorizedResultIsImportedAndSettled(name)
                               for name in names])
    suite.addTest(Review("test_grant_ended_during_verification_still_advances_reference"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
