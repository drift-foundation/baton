"""W103525 claim155666 probe, third half: the correction's OWN causal evidence,
and whether both Jobs can be driven in either order.

Owner155646 asked for composed alternate-order/reopen/correction evidence. This
asks the public owners what they will actually answer before a test asserts it.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.worker_manager import review_cycles

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding()
        # JOB B FIRST, which is the alternate order.
        case.turn(held.control, "implementation", held.second,
                  case.mounted_at(held.composed, held.second),
                  edits={"feature.py": case.B_FEATURE,
                         "feature_check.py": case.B_CHECK})
        case.drive_job(held.job, held.composed, "job-b", "implementation",
                       "completed")
        print("job-b first ok")
        case.turn(held.control, "implementation", held.first,
                  case.mounted_at(held.composed, held.first),
                  edits={"harness.py": "print('answered')\n"})
        case.drive_job(held.job, held.composed, "job-a", "implementation",
                       "completed")
        print("job-a second ok")
        case.drive_job(held.job, held.composed, "job-a", "review", "waiting")
        reviewed = case.one_attempt_of(held.composed, "review-worker")
        case.review_turn(held, "job-a", reviewed, "changes-requested")
        case.drive_job(held.job, held.composed, "job-a", "implementation",
                       "waiting")
        row = held.control._connection.execute(
            "SELECT assignment_generation FROM attempts "
            "WHERE runtime_attempt_id = ?", (reviewed,)).fetchone()
        generation = row["assignment_generation"]
        print("review generation", generation)
        attachment = review_cycles.review_for_attempt(
            held.control, attempt_id=reviewed, generation=generation)
        print("attachment", json.dumps(attachment, sort_keys=True,
                                       default=str))
        line = case.line_of(held.composed, "job-a")
        print("line", json.dumps(line, sort_keys=True, default=str))
        status = review_cycles.line_status(held.control, line["line_id"])
        print("line_status", json.dumps(status, sort_keys=True, default=str))
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
