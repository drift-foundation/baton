"""Run from v12/python with PYTHONPATH=src:.; stores are test-owned only.

Capture actual owner records at the W110772 production refusal, without
patching the owner's return values or manufacturing a successful verdict.
"""
import json
from unittest import mock

from baton_v12.worker_manager import frozen_output_of, intake_receipt_of, load_manifest, retentions_of
from baton_v12.worker_manager.attempts import attempt_runtime_of
from baton_v12.worker_manager.workspaces import directory_manifest
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody


def capture(cut):
    case = TheWorkerCompletionTraversesPublicCustody("test_actual_completion_reaches_first_verdict_and_public_custody")
    try:
        case.setUp()
        held = case.produced()
        attempt = held["attempt_id"]
        initial_frozen = None
        before = []
        if cut:
            with case.public_ending(interrupt_after_freeze=True) as before:
                with case.assertRaises(case.after_freeze):
                    case.end(held)
            initial_frozen = frozen_output_of(case.control, attempt)
            case.assertIsNotNone(initial_frozen)
            case.assertIsNone(intake_receipt_of(case.control, attempt))
            case.assertEqual(retentions_of(case.control, attempt), ())
            case.assertEqual(case.verdicts(held), 0)
        with case.public_ending() as order, mock.patch.object(case, "turn", side_effect=AssertionError("no repeated worker invocation")):
            ended = case.end(held)
        frozen = frozen_output_of(case.control, attempt)
        result = load_manifest(case.control, frozen["manifest_digest"], "resultManifest")
        receipt = intake_receipt_of(case.control, attempt)
        retained = retentions_of(case.control, attempt)
        case.assertEqual(result["completion_manifest_digest"], held["terminal"]["manifest_digest"])
        case.assertEqual(result["assignment_ref"], held["terminal"]["assignment_ref"])
        case.assertEqual(receipt["result_id"], frozen["result_id"])
        case.assertEqual(receipt["custody"], "accepted")
        case.assertEqual(receipt["receipt_digest"], ended["receipt_digest"])
        case.assertEqual({one["artifact_id"] for one in retained}, set(ended["artifacts"]))
        case.assertTrue(all(one["disposition"] == "retain" for one in retained))
        measured = {one["name"]: one for one in held["measured"]}
        for output in result["outputs"]:
            case.assertEqual(output["content_manifest"], measured[output["name"]]["content_manifest"])
            case.assertEqual(output["result_metadata"], measured[output["name"]]["result_metadata"])
        checked = []
        for artifact in receipt["artifacts"]:
            actual = directory_manifest(artifact["custody_locator"].removeprefix("file://"))["tree_digest"]
            case.assertEqual(actual, artifact["content_digest"])
            checked.append({"artifact_id": artifact["artifact_id"], "actual_tree_digest": actual})
        case.assertEqual(ended["verdict"], "accepted")
        case.assertEqual(ended["outcome"], "held")
        case.assertIn("a review verdict requires frozen output and passed verification", ended["held_reason"])
        case.assertEqual(case.verdicts(held), 0)
        case.assertFalse(ended["cleaned_up"])
        case.assertEqual(held["adapter"].destroyed_with, [])
        case.assertEqual(case.worker_turns, 1)
        if cut:
            case.assertEqual(initial_frozen, frozen)
            case.assertEqual(len(held["adapter"].seals), 2)
        return {"after_freeze_cut": cut, "before_order": before, "ending_order": order,
                "worker_turns": case.worker_turns, "completion": held["terminal"],
                "frozen": frozen, "result": result, "intake": receipt, "retentions": retained,
                "recomputed_custody_trees": checked, "ending": ended,
                "runtime": attempt_runtime_of(case.control, attempt),
                "verdict_count": case.verdicts(held), "destroy_calls": held["adapter"].destroyed_with}
    finally:
        case.doCleanups()


if __name__ == "__main__":
    print(json.dumps({"observed": [capture(False), capture(True)]}, indent=2, sort_keys=True))
