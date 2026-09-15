"""Independent W103525 review: labelled offline mutations and public verdict reads.

Run from v12/python with PYTHONPATH=src:tools:.; no live providers or raw store access.
"""
import copy
import json
from pathlib import Path

from tests.tools import scheduler_trace as oracle
from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection
from baton_v12.job_manager import ending, review_driver
from baton_v12.worker_manager import assignment_of, review_cycles


def main():
    source = Path(__file__).with_name("trace-155666-composed.json")
    schedules = {one["name"]: one["artifact"] for one in json.loads(source.read_text())["schedules"]}
    results = {"label": "Synthetic mutations of retained real artifacts; owners unchanged", "checks": {}}

    def check(name, artifact):
        results["checks"][name] = oracle.validate(artifact)

    sessions = schedules["composed-role-sessions"]
    check("session_original", sessions)
    altered = copy.deepcopy(sessions)
    row = next(one for one in altered["records"] if one.get("session_id"))
    row["session_id"] = row["session_id"].rsplit("/", 1)[0] + "/foreign-provider-id"
    check("session_reference_foreign_provider_component", altered)
    altered = copy.deepcopy(sessions)
    row = next(one for one in altered["records"] if one.get("session_id") and one["stage_id"].endswith("/review"))
    row["participant"] = "other.unassigned"
    check("review_session_foreign_assignment_participant", altered)
    correction = schedules["composed-correction"]
    check("correction_original", correction)
    altered = copy.deepcopy(correction)
    altered["records"] = [one for one in altered["records"] if not (one.get("stage_id") or "").endswith("/review") or one["act"] == "reserve"]
    check("correction_review_reservation_only", altered)
    print(json.dumps(results, indent=2, sort_keys=True), flush=True)

    case = TwoBoundJobsTraverseServingAndCorrection("test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding()
        case.produced(held, "job-a", held.first, "print('answered')\n")
        case.drive_job(held.job, held.composed, "job-a", "review", "waiting")
        reviewed = case.one_attempt_of(held.composed, "review-worker")
        case.review_turn(held, "job-a", reviewed, "changes-requested")
        case.drive_job(held.job, held.composed, "job-a", "implementation", "waiting")
        settlement = ending.settlement_of(held.job, "job-a/review", 1)
        evidence = settlement["evidence"]
        verdict = review_cycles.verdict_of(held.control, evidence["verdict_id"])
        assignment = assignment_of(held.control, reviewed)
        attachment = review_cycles.review_for_attempt(held.control, attempt_id=reviewed, generation=assignment["generation"])
        frozen_claim = review_driver.review_verdict_from_result(held.control, attachment_id=attachment["attachment_id"])
        assert verdict["disposition"] == "changes-requested", verdict
        assert frozen_claim["verdict"] == "changes-requested", frozen_claim
        assert verdict["attachment_id"] == attachment["attachment_id"], verdict
        print(json.dumps({"label": "Real composed owners, scripted engine; public reads only", "ending_settlement": settlement, "verdict": verdict, "frozen_review_claim": frozen_claim}, indent=2, sort_keys=True), flush=True)
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
