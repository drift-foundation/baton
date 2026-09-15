"""Independent lifecycle baseline plus the author's focused capacity cases.

The two observation assertions below record remaining defects, not acceptance.
"""
import unittest

from baton_v12.job_manager import integration_capacity as capacity
from baton_v12.worker_manager.output import frozen_output_of
from tests.job_manager import test_managed_integration_capacity as candidate


class RemainingBindings(candidate.CapacityCase):
    def test_foreign_parent_apply_is_admitted(self):
        store, stage, _allocation, registered = self.registered()
        apply = next(one for one in registered["members"] if one["phase"] == "apply")
        self.assertNotEqual(apply["execution_work_id"], stage["work_id"])
        self.assertNotEqual(apply["execution_attempt_id"], stage["attempt_id"])
        self.assertNotEqual(apply["execution_offer_id"], stage["offer_id"])
        self.prepared(store)
        answer = self.admit("apply", "apply-attempt-1", "apply-offer-1", store)
        apply = next(one for one in answer["members"] if one["phase"] == "apply")
        self.assertEqual(apply["state"], "admitted")
        print("DEFECT OBSERVED: apply admitted with Work/attempt/offer different from actual parent episode")

    def test_uncollected_digest_is_accepted_as_successful_preparation(self):
        store, _stage, _allocation, _registered = self.registered()
        self.admit("prepare", "prepare-attempt-1", "prepare-offer-1", store)
        self.destroyed("prepare-attempt-1")
        self.assertIsNone(frozen_output_of(self._control, "prepare-attempt-1"))
        answer = capacity.end_integration_execution(
            store, self._control, execution_attempt_id="prepare-attempt-1",
            outcome="succeeded", exclusion="runtime-destroyed",
            collected_digest=self.COLLECTED)
        preparation = next(one for one in answer["members"] if one["phase"] == "prepare")
        self.assertEqual(preparation["collected_digest"], self.COLLECTED)
        self.assertEqual(preparation["outcome"], "succeeded")
        self.assertIsNone(frozen_output_of(self._control, "prepare-attempt-1"))
        print("DEFECT OBSERVED: caller digest became successful preparation content with no frozen/collected artifact")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(candidate), tests])


if __name__ == "__main__":
    unittest.main(verbosity=2)
