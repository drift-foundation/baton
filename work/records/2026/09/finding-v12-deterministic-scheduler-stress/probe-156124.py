"""W103525 claim156124 probe: Job B's REAL gate, and the judgment path to it.

Review 2026-09-13T00:24:01Z measured that Job B is on the `reconciled` branch
awaiting verification receipts on its derived proposal -- not blocked by the
deployment-wide quiescence flag, and not waiting for a direct integration turn.
This asks whether the fixture's own judgment path can be driven with the
observer in the loop, which is what an exportable trace needs.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.integration import reconciliation
    from baton_v12.job_manager import live_of

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding(
            result_judgment_workers=case.judgment_workers())
        print("coding accepted the judgment workers")
        for job_id, attempt_id, reviewer_id, edits in (
                ("job-a", held.first, "review-worker",
                 {"harness.py": "print('the first job answered')\n"}),
                ("job-b", held.second, "review-worker-b",
                 {"feature.py": case.B_FEATURE,
                  "feature_check.py": case.B_CHECK})):
            case.turn(held.control, "implementation", attempt_id,
                      case.mounted_at(held.composed, attempt_id), edits=edits)
            case.drive_job(held.job, held.composed, job_id, "implementation",
                           "completed")
            case.drive_job(held.job, held.composed, job_id, "review",
                           "waiting")
            reviewed = case.one_attempt_of(held.composed, reviewer_id)
            case.review_turn(held, job_id, reviewed, "accepted")
            case.drive_job(held.job, held.composed, job_id, "review",
                           "completed")
        print("both accepted")
        case.drive_job(held.job, held.composed, "job-a", "integration",
                       "integrating")
        first = live_of(held.job, "job-a/integration")["attempt_id"]
        print("job-a integration_turn", case.integration_turn(held, first))
        case.engine.stopped = True
        case.drive_job(held.job, held.composed, "job-a", "integration",
                       "completed", ticks=4)
        deployment = case.deployment_of(held.composed)
        reports = []
        for _ in range(14):
            reports.append(case.tick(held))
            if len(deployment.judges) == 3:
                break
        print("judges", len(deployment.judges))
        if len(deployment.judges) != 3:
            print("last report", json.dumps(reports[-1], sort_keys=True,
                                            default=str)[:1200])
            return 1
        result_id = next(iter(deployment.judges))[0]
        result = reconciliation.result_of(deployment.integration, result_id)
        print("derived result", result["state"],
              result.get("derived_proposal_id"))
        print("receipts before judgments",
              deployment.authority.receipts(result["derived_proposal_id"]))
        for _key, execution in deployment.judges.items():
            case.judgment_turn(held, execution)
        case.tick(held)
        for execution in deployment.judges.values():
            execution.result()
        states = case.drive_job(held.job, held.composed, "job-b",
                                "integration", "completed", ticks=14)
        print("job-b", json.dumps(states, sort_keys=True))
        settled = reconciliation.result_of(deployment.integration, result_id)
        print("derived result after", settled["state"])
        print("receipts after",
              len(deployment.authority.receipts(result["derived_proposal_id"])))
        for job_id in ("job-a", "job-b"):
            print(job_id, json.dumps(
                case.states_for(held.job, held.composed, job_id),
                sort_keys=True))
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
