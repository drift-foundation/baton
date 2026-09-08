"""Independent blocker audit; real fixture owners, no changed outcomes or axes."""
import hashlib
import json
from pathlib import Path
from unittest import mock
from baton_v12.worker_manager import review_cycles, frozen_output_of, intake_receipt_of, retentions_of
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Case

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parents[1]
REPO = next(p for p in HERE.parents if (p / "v12/python").is_dir())
candidate = json.loads((DOSSIER / "evidence/tuner-111406/candidate.json").read_text())
hashes = {}
for path, expected in candidate["sha256"].items():
    data = (REPO / path).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    hashes[path] = {"expected": expected, "actual": actual, "matches": actual == expected}
    dest = HERE / "candidate" / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
test = (REPO / "v12/python/tests/job_manager/test_review_driver.py").read_bytes()
prior = json.loads((DOSSIER / "evidence/tuner-111406/baseline.json").read_text())
prefix_hash = hashlib.sha256(test[:111559]).hexdigest()
prefix_matches = prefix_hash == prior["v12/python/tests/job_manager/test_review_driver.py"]


def capture(cut):
    case = Case("test_actual_completion_reaches_first_verdict_and_public_custody")
    try:
        case.setUp()
        held = case.produced()
        before = []
        frozen_at_cut = None
        if cut:
            with case.public_ending(interrupt_after_freeze=True) as before:
                with case.assertRaises(case.after_freeze):
                    case.end(held)
            frozen_at_cut = frozen_output_of(case.control, held["attempt_id"])
        attempts = []
        original = review_cycles._quiescent_completed
        def recording(*args, **kwargs):
            answer = original(*args, **kwargs)
            attempts.append({key: answer[key] for key in ("runtime_attempt_id", "output", "verification", "worker_disposition")})
            return answer
        with mock.patch.object(review_cycles, "_quiescent_completed", recording), case.public_ending() as order:
            ending = case.end(held)
        receipt = intake_receipt_of(case.control, held["attempt_id"])
        retained = retentions_of(case.control, held["attempt_id"])
        case.assertEqual(attempts[-1]["output"], "sealed")
        case.assertEqual(attempts[-1]["verification"], "none")
        case.assertEqual(ending["outcome"], "held")
        case.assertEqual(ending["verdict"], "accepted")
        case.assertFalse(ending["cleaned_up"])
        case.assertEqual(case.verdicts(held), 0)
        case.assertEqual(case.worker_turns, 1)
        return {"cut": cut, "before": before, "order": order, "owner_answer_at_verdict": attempts,
                "completion_digest": held["terminal"]["manifest_digest"],
                "frozen": frozen_output_of(case.control, held["attempt_id"]),
                "frozen_at_cut": frozen_at_cut, "receipt": receipt, "retentions": retained,
                "ending": ending, "worker_turns": case.worker_turns,
                "verdict_count": case.verdicts(held), "destroy_calls": held["adapter"].destroyed_with}
    finally:
        case.doCleanups()


result = {"hashes": hashes, "prior_111559_bytes_match": prefix_matches,
          "prior_prefix_sha256": prefix_hash, "observed": [capture(False), capture(True)]}
(HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
for name in ("FINDING.md", "PLAN.md", "PROGRESS.md"):
    (HERE / ("at-review-" + name)).write_bytes((DOSSIER / name).read_bytes())
print(json.dumps({"hashes_match": all(x["matches"] for x in hashes.values()),
                  "prior_prefix_matches": prefix_matches,
                  "observed": [{"cut": x["cut"], "owner_answer": x["owner_answer_at_verdict"],
                                "order": x["order"], "outcome": x["ending"]["outcome"],
                                "retentions": len(x["retentions"])} for x in result["observed"]]}, indent=2))
