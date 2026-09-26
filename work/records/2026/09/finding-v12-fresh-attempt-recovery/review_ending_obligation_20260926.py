"""Candidate 0392e8e: settlement is recorded before its ending is complete.

Independent deterministic probe; does not modify the author module. This is a
candidate-specific observation, not a requirement to preserve the faulty state.
"""
import unittest
from unittest.mock import patch

import test_fresh_attempt_after_failure as candidate
from baton_v12.job_manager import ending, live_of
from baton_v12.worker_manager import line_of, writer_of


class EndingObservation(unittest.TestCase):
    def test_candidate_settles_with_successor_still_owning_line_and_lane(self):
        case = candidate.AGatedJobRecoversAndItsSuccessorSucceeds(
            "test_the_gated_job_recovers_and_its_successor_is_accepted")
        case.setUp()
        try:
            called = []
            original = ending.settle_ending

            def capture(*args, **kwargs):
                called.append(kwargs["evidence"])
                return original(*args, **kwargs)

            with patch.object(ending, "settle_ending", capture):
                case.test_the_gated_job_recovers_and_its_successor_is_accepted()
            fresh = live_of(case.jobs, candidate.STAGE)["attempt_id"]
            line = line_of(case.store, case.line["line_id"])
            row = case.row(fresh)
            self.assertEqual(len(called), 1)
            self.assertEqual(line["state"], "writing")
            self.assertEqual(line["current_checkpoint_id"], case.checkpoint_id)
            self.assertEqual(case.lane_holders(), [fresh])
            self.assertEqual(case.session.live_assignment["generation"], 3)
            self.assertIsNotNone(ending.settlement_of(case.jobs, candidate.STAGE, 3))
            self.assertEqual(ending.pending_endings(case.jobs), [])
            print({"line_state": line["state"], "cleanup": row["cleanup"],
                   "runtime": row["execution_runtime"], "lane": case.lane_holders(),
                   "generation": case.session.live_assignment["generation"],
                   "settlement_evidence": called[0], "pending_endings": []})
        finally:
            case.doCleanups()


if __name__ == "__main__":
    unittest.main()
