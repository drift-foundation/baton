"""Review probe: pass the actual checkpoint reader's answer to the resolver."""
import unittest

from tests.tools import test_integration_bundle as owner_fixture
from baton_v12.worker_manager import review_cycles
from baton_v12.job_manager import execution_limits
from tools import integration_worker


class ActualCheckpoint(owner_fixture.ProducerCase):
    def test_actual_owner_answer_is_consumable(self):
        accepted = review_cycles.integration_checkpoint(
            self.world.manager, self.world.line_id)
        print("actual checkpoint keys:", sorted(accepted), flush=True)
        print("actual evidence keys:", sorted(accepted["evidence"]), flush=True)
        # No bundle is exported here. These are inert downstream placeholders;
        # the actual owner-shape crossing fails before bundle comparison.
        with self.assertRaises(Exception) as caught:
            integration_worker.preparation_operands(
                orchestration_id="review-orch", execution_work_id="review-child",
                execution_route="integration-preparation", participant="actor",
                accepted=accepted, proposal_id=self.world.proposal_id,
                canonical_target_id=self.world.target, job_id="job-a",
                line_id=self.world.line_id,
                target_revision=accepted["evidence"]["base"],
                harness_digest="sha256:" + "a" * 64,
                profile_digest="sha256:" + "b" * 64,
                policy_digest="sha256:" + "c" * 64, profile_name="reference",
                apply_task_digest="sha256:" + "d" * 64,
                limits=execution_limits.resolved({}, 1),
                published={"input_digest": "sha256:" + "e" * 64,
                           "request": {}})
        self.assertNotIsInstance(
            caught.exception, KeyError,
            "resolver requires a field absent from its actual owner answer: "
            + repr(caught.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
