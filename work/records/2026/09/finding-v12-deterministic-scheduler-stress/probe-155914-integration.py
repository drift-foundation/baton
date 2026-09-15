"""W103525 claim155914 probe: both whole Jobs to terminal integration.

PLAN item 5 keeps "both whole Jobs reaching terminal integration" open. This asks
the composed owners how far the accepted two-Job traversal actually goes, and what
the SECOND Job is told while the first holds the one integrator.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.job_manager import live_of, projection
    from baton_v12.job_manager.scheduler import allocation_of
    from tests.job_manager import fixtures

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.both_accepted()
        for job_id in ("job-a", "job-b"):
            print(job_id, "after acceptance", json.dumps(
                case.states_for(held.job, held.composed, job_id),
                sort_keys=True))
        case.drive_job(held.job, held.composed, "job-a", "integration",
                       "integrating")
        for job_id in ("job-a", "job-b"):
            print(job_id, "at integration", json.dumps(
                case.states_for(held.job, held.composed, job_id),
                sort_keys=True),
                "allocated:", case.allocated(held.job,
                                             f"{job_id}/integration"))
        owed = projection.owed_acts(held.job, held.composed)
        print("owed", json.dumps(owed, sort_keys=True, default=str)[:2000])
        # HOW FAR DOES AN ORDINARY SWEEP CARRY IT?
        from baton_v12.job_manager import sweep as tick
        for _ in range(20):
            tick(held.job, held.composed, now=fixtures.NOW)
        for job_id in ("job-a", "job-b"):
            print(job_id, "after 20 more ticks", json.dumps(
                case.states_for(held.job, held.composed, job_id),
                sort_keys=True),
                "allocated:", case.allocated(held.job,
                                             f"{job_id}/integration"))
        for job_id in ("job-a", "job-b"):
            live = live_of(held.job, f"{job_id}/integration")
            print(job_id, "live integration episode",
                  json.dumps(live, sort_keys=True, default=str)[:500])
            if live and live.get("attempt_id"):
                print("  allocation",
                      json.dumps(allocation_of(held.job, live["attempt_id"]),
                                 sort_keys=True, default=str))
    finally:
        case.doCleanups()
    return 0


def _both():
    main()
    second_question()
    return 0


def second_question():
    """And what does the SCHEDULER itself say about job-b's integration while
    the one integrator is held? The absence of an allocation is not a cause."""
    import json
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.contracts import ContractRefusal
    from baton_v12.job_manager import live_of, projection
    from baton_v12.job_manager.scheduler import reserve
    from tests.job_manager import fixtures

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.both_accepted()
        case.drive_job(held.job, held.composed, "job-a", "integration",
                       "integrating")
        [owed] = projection.owed_acts(held.job, held.composed)
        print("owed act", owed["act"], owed["stage_id"])
        live = live_of(held.job, "job-b/integration")
        try:
            answer = reserve(held.job, dict(owed, pool=held.composed))
            print("RESERVE ANSWERED", json.dumps(answer, sort_keys=True,
                                                 default=str)[:600])
        except ContractRefusal as failure:
            print("reserve refused",
                  f"{failure.category}/{failure.code}: {failure.message}")
        except TypeError as failure:
            print("signature", failure)
            try:
                answer = reserve(held.job, owed)
                print("RESERVE(owed) ANSWERED",
                      json.dumps(answer, sort_keys=True, default=str)[:600])
            except Exception as other:
                print("reserve(owed)", f"{type(other).__name__}: {other}")
    finally:
        case.doCleanups()


if __name__ == "__main__":
    sys.exit(_both())
