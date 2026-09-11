"""Independent final Q controls, using only disposable component fixtures."""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import abandon_lease, block_target
from tests.integration.test_execution import (
    PostImportVerifier, TheAuthorizedResultIsImportedAndSettled)
from tests.integration.test_reconciliation import TARGET, REFERENCE


class Review(TheAuthorizedResultIsImportedAndSettled):
    def test_grant_ended_during_verification_advances_neither_owner(self):
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
        verifier = Ended(self)
        with self.assertRaises(ContractRefusal) as caught:
            self.tick(held, verifier=verifier)
        after = self.git(self.target, "rev-parse", REFERENCE)
        receipt = self.authority.receipt(held["derived_proposal_id"], "integration")
        self.assertEqual(before, after)
        self.assertIsNone(receipt)
        self.assertEqual(len(verifier.asked), 1)
        self.assertEqual(self.authority.canonical_target(), before)
        print(json.dumps({"observation": "reference and Authority unchanged after grant abandoned during verification",
                          "before": before, "after": after,
                          "receipt": receipt, "refusal": str(caught.exception)}))


if __name__ == "__main__":
    names = ["test_both_jobs_changes_land_on_the_target_and_it_settles",
             "test_the_required_post_import_tests_ACTUALLY_RUN",
             "test_a_FAILED_post_import_test_holds_and_never_advances",
             "test_a_GRANT_FOR_ANOTHER_PROPOSAL_writes_nothing"]
    suite = unittest.TestSuite([TheAuthorizedResultIsImportedAndSettled(name)
                               for name in names])
    suite.addTest(Review("test_grant_ended_during_verification_advances_neither_owner"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
