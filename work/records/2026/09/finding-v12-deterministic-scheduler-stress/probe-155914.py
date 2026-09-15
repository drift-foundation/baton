"""W103525 claim155914 probe: can the COMPOSED deployment be reopened at a
durable boundary and continue?

Owner155911 raised the caps and asked for the remaining R1 correction and then
the accepted composed continuation. Composed reopen has been open since the first
slice and was explicitly not attempted last claim. This asks the question before
any test asserts it.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from tests.job_manager import fixtures
    from tools import stage_execution
    from baton_v12.job_manager import allocation_of, episodes_of, stage_rows

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding()
        case.turn(held.control, "implementation", held.first,
                  case.mounted_at(held.composed, held.first),
                  edits={"harness.py": "print('answered')\n"})
        case.drive_job(held.job, held.composed, "job-a", "implementation",
                       "completed")
        print("before", json.dumps(
            case.states_for(held.job, held.composed, "job-a"), sort_keys=True))
        before = {}
        for row in stage_rows(held.job):
            for episode in episodes_of(held.job, row["stage_id"]):
                allocation = allocation_of(held.job, episode["attempt_id"])
                if allocation is not None:
                    before[episode["attempt_id"]] = (
                        row["stage_id"], allocation["worker_id"],
                        allocation["allocation_state"])
        print("allocations before", json.dumps(before, sort_keys=True))

        # THE REOPEN: a fresh deployment over the SAME durable files, under its
        # own incarnation, with its own handles. Nothing of the first
        # deployment's Python state crosses the boundary.
        document = case.two_jobs(**case.traversing())
        job2, control2 = case.stores("stage-reopened")
        second = stage_execution.operations_from(
            case.composed_document(line_declared_base=case.base, **document),
            job2, control2, engine_run=case.engine,
            credential_provider=lambda provider, reference: case.secret,
            clock=lambda: fixtures.NOW, checkout=case.checkout)
        try:
            print("reopened ok")
            states = case.drive_job(job2, second, "job-a", "review", "waiting")
            print("after reopen", json.dumps(states, sort_keys=True))
            after = {}
            for row in stage_rows(job2):
                for episode in episodes_of(job2, row["stage_id"]):
                    allocation = allocation_of(job2, episode["attempt_id"])
                    if allocation is not None:
                        after[episode["attempt_id"]] = (
                            row["stage_id"], allocation["worker_id"],
                            allocation["allocation_state"])
            print("allocations after", json.dumps(after, sort_keys=True))
            print("same attempts kept:",
                  set(before) <= set(after))
            reviewed = case.one_attempt_of(second, "review-worker")
            print("review attempt", reviewed)
        finally:
            second.close()
            job2.close()
            control2.close()
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
