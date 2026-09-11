"""Bounded review of candidate136712; isolated fixtures, no deployment store.

The two custom cases demonstrate defects in this candidate, so their passing
assertions describe the observed defect, not accepted product expectations.
"""
import json
import unittest
from unittest import mock

from baton_v12.integration import driver, execution
from baton_v12.integration.queue import enqueue
from tests.integration import test_reconciliation as fixture
from tests.integration.test_execution import TheAuthorizedResultIsImportedAndSettled


class Review(fixture.ResultCase):
    def test_import_records_success_without_post_import_test_execution(self):
        held = self.through_authorization()
        with mock.patch.object(fixture, "_run", wraps=fixture._run) as commands:
            answer = driver.admit_authorized_result(
                self.store, self.profile, fixture.runner, self.manager,
                self.jobs, self.authority, self.session,
                result_id=held["result_id"], attempt_id="review-import")
        calls = [list(call.args[0]) for call in commands.call_args_list]
        self.assertEqual(answer["outcome"], "integrated")
        self.assertTrue(calls)
        self.assertTrue(all(call[0] == "git" for call in calls))
        print(json.dumps({"observation": "terminal success with only Git commands after authorization",
                          "commands": calls, "settlement": answer["settlement"]}))

    def test_import_uses_a_grant_for_a_different_admitted_proposal(self):
        held = self.through_authorization()
        _, eligibility = driver.authorized_result_eligibility(
            self.store, self.profile, self.manager, self.jobs, self.authority,
            result_id=held["result_id"])
        # A different proposal is deliberately supplied at the trusted queue
        # boundary. The importer must compare its fresh account with the
        # admitted entry before using that entry's mutation grant.
        eligibility["proposal_id"] = "proposal-b1"
        entry_id = "review-other-proposal"
        enqueue(self.store, canonical_target_id=fixture.TARGET,
                entry_id=entry_id, eligibility=eligibility)
        before = self.git(self.target, "rev-parse", fixture.REFERENCE)
        answer = execution.import_authorized_result(
            self.store, self.profile, fixture.runner, self.manager,
            self.jobs, self.authority, canonical_target_id=fixture.TARGET,
            entry_id=entry_id, lease_id="review-other-lease",
            integrator_participant=fixture.INTEGRATOR,
            attempt_id="review-other-attempt", result_id=held["result_id"])
        after = self.git(self.target, "rev-parse", fixture.REFERENCE)
        self.assertEqual(answer["outcome"], "integrated")
        self.assertNotEqual(before, after)
        print(json.dumps({"observation": "target advanced under entry admitted for a different proposal",
                          "admitted_proposal": eligibility["proposal_id"],
                          "imported_proposal": held["derived_proposal_id"],
                          "before": before, "after": after,
                          "outcome": answer["outcome"]}))


if __name__ == "__main__":
    suite = unittest.TestSuite([
        TheAuthorizedResultIsImportedAndSettled("test_both_jobs_changes_land_on_the_target_and_it_settles"),
        Review("test_import_records_success_without_post_import_test_execution"),
        Review("test_import_uses_a_grant_for_a_different_admitted_proposal"),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
