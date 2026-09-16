"""Focused observed contract conflict; no runtime, model or engine execution."""
import copy
import unittest
from types import SimpleNamespace
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager.delegation import stage_intent
from tools import single_worker, stage_execution
from tests.manager.test_claude_agent import claude_agent, DECLARED
import baton_worker


def receipt():
    one = copy.deepcopy(DECLARED[0])
    one.update(name="provider-context-receipt", path="provider-context-receipt")
    one["constraints"].update(max_bytes=16384, max_entries=1, allowed_media_types=["application/json"])
    return one


class PacketConflict(unittest.TestCase):
    def test_ordinary_delegation_binds_both_roles_to_the_same_submitted_input(self):
        job = {"input_digest": "sha256:"+"1"*64, "policy_digest": "sha256:"+"2"*64}
        stage = {"offer_id": "offer", "work_id": "work", "attempt_id": "attempt", "profile_digest": "sha256:"+"3"*64}
        implementation = stage_intent(dict(stage, kind="implementation"), job)
        review = stage_intent(dict(stage, kind="review", offer_id="review-offer", attempt_id="review-attempt"), job)
        self.assertEqual(implementation["input_digest"], job["input_digest"])
        self.assertEqual(review["input_digest"], job["input_digest"])

    def test_removing_the_receipt_from_review_changes_the_required_input_identity(self):
        original = {"work_ref": {"work_id": "work"}, "outputs": [receipt()]}
        original["manifest_digest"] = digest(original)
        derived = {"work_ref": original["work_ref"], "outputs": []}
        derived["manifest_digest"] = digest(derived)
        self.assertNotEqual(original["manifest_digest"], derived["manifest_digest"])
        given = {"launch_role": "review", "profile_name": "profile", "profile_digest": "sha256:"+"3"*64, "policy_digest": "sha256:"+"2"*64, "input_manifest": original}
        stage = {"kind": "review", "work_id": "work", "profile_name": given["profile_name"], "profile_digest": given["profile_digest"]}
        job = {"input_digest": original["manifest_digest"], "policy_digest": given["policy_digest"]}
        single_worker._SingleWorker._matches(SimpleNamespace(given=given), stage, job)
        changed = dict(given, input_manifest=derived)
        with self.assertRaisesRegex(ContractRefusal, "another bootstrap input"):
            single_worker._SingleWorker._matches(SimpleNamespace(given=changed), stage, job)
        self.assertIn("the submitted input", stage_execution._disagreements(changed, stage, job, {"job_work_id": "work"}))

    def test_required_receipt_cannot_be_reported_missing_by_review(self):
        with self.assertRaisesRegex(baton_worker.WorkerFault, "required and is answered"):
            baton_worker.answered([receipt()], [{"name": "provider-context-receipt", "status": "missing-optional", "result_metadata": {}}])

    def test_the_shared_review_workload_has_no_context_receipt_output(self):
        declarations = []
        for name in ("proposal", "findings", "logs"):
            one = copy.deepcopy(DECLARED[0])
            one.update(name=name, path=name, required=False)
            declarations.append(one)
        produce, absent = claude_agent._selected(declarations, claude_agent.REVIEW_OUTPUTS, "review")
        self.assertEqual([one["name"] for one in produce], ["findings", "logs"])
        with self.assertRaisesRegex(claude_agent.TaskRefusal, "unrecognised"):
            claude_agent._selected(declarations+[receipt()], claude_agent.REVIEW_OUTPUTS, "review")


if __name__ == "__main__":
    unittest.main(verbosity=2)
