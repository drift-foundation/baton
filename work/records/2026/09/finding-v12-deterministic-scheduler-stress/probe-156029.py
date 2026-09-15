"""W103525 claim156029 probe: after Job A integrates, what happens to Job B?

Review 2026-09-13T00:09:15Z showed `integration_turn` plus ordinary owner ticks
completes Job A in this exact contention case, and warned that B may face
stale-target or candidate rules after A changes their common target: "report its
exact owner result rather than assuming success". This asks.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    from baton_v12.job_manager import live_of, sweep
    from tests.job_manager import fixtures
    from tests.tools.test_scheduler_trace import (
        TheComposedOwnersSupplyAuthorizedTransitions as Cases)

    case = Cases("test_both_jobs_traverse_and_one_integrator_serializes_them")
    case.setUp()
    try:
        captured = {}
        original = case.integration_allocation

        def remember(held):
            captured["held"] = held
            return original(held)

        case.integration_allocation = remember
        case.test_both_jobs_traverse_and_one_integrator_serializes_them()
        held = captured["held"]
        attempt = live_of(held.job, "job-a/integration")["attempt_id"]
        print("integration_turn exit",
              case.case.integration_turn(held, attempt))
        case.case.engine.stopped = True
        states = case.case.drive_job(held.job, held.composed, "job-a",
                                     "integration", "completed", ticks=4)
        print("job-a", json.dumps(states, sort_keys=True))
        # AND NOW THE CAPACITY HANDOFF. Ordinary ticks only.
        for index in range(12):
            report = sweep(held.job, held.composed, now=fixtures.NOW)
            acts = [one for one in report["acts"]
                    if one["stage_id"].startswith("job-b")]
            if acts:
                print("tick", index + 1, "job-b acts",
                      json.dumps(acts, sort_keys=True, default=str)[:900])
            held_states = case.case.states_for(held.job, held.composed,
                                               "job-b")
            if held_states["integration"] not in ("queued",):
                print("tick", index + 1, "job-b", json.dumps(held_states,
                                                             sort_keys=True))
        print("job-b final", json.dumps(
            case.case.states_for(held.job, held.composed, "job-b"),
            sort_keys=True))
        print("job-b allocated",
              case.case.allocated(held.job, "job-b/integration"))
        live = live_of(held.job, "job-b/integration")
        print("job-b live", json.dumps(live, sort_keys=True, default=str)[:400])
    finally:
        case.doCleanups()
    return 0


def _both():
    main()
    print("--- second question ---")
    second_question()
    return 0


def second_question():
    """And if B's own integrator turn is driven too, what does the owner say?

    A and B publish into ONE canonical target at one revision. A has just
    integrated, so B's proposal was built on a revision the target no longer
    holds -- which is where `integration.driver`'s "a proposal is offered against
    the revision it was built from" rule decides. This asks for the answer rather
    than assuming either outcome.
    """
    import json
    from baton_v12.contracts import ContractRefusal
    from baton_v12.job_manager import live_of, sweep
    from tests.job_manager import fixtures
    from tests.tools.test_scheduler_trace import (
        TheComposedOwnersSupplyAuthorizedTransitions as Cases)

    case = Cases("test_both_jobs_traverse_and_one_integrator_serializes_them")
    case.setUp()
    try:
        captured = {}
        original = case.integration_allocation

        def remember(held):
            captured["held"] = held
            return original(held)

        case.integration_allocation = remember
        case.test_both_jobs_traverse_and_one_integrator_serializes_them()
        held = captured["held"]
        first = live_of(held.job, "job-a/integration")["attempt_id"]
        case.case.integration_turn(held, first)
        case.case.engine.stopped = True
        case.case.drive_job(held.job, held.composed, "job-a", "integration",
                            "completed", ticks=4)
        # THE HANDOFF, then B's own turn.
        case.case.engine.stopped = False
        for _ in range(6):
            sweep(held.job, held.composed, now=fixtures.NOW)
        states = case.case.states_for(held.job, held.composed, "job-b")
        print("job-b before its turn", json.dumps(states, sort_keys=True))
        second = live_of(held.job, "job-b/integration")["attempt_id"]
        try:
            print("job-b integration_turn exit",
                  case.case.integration_turn(held, second))
        except ContractRefusal as failure:
            print("job-b integration_turn refused",
                  f"{failure.category}/{failure.code}: {failure.message}")
        except Exception as failure:
            print("job-b integration_turn",
                  f"{type(failure).__name__}: {failure}")
        case.case.engine.stopped = True
        for index in range(8):
            report = sweep(held.job, held.composed, now=fixtures.NOW)
            acts = [one for one in report["acts"]
                    if one["stage_id"].startswith("job-b")]
            if acts:
                print("tick", index + 1, json.dumps(acts, sort_keys=True,
                                                    default=str)[:700])
        print("job-b final", json.dumps(
            case.case.states_for(held.job, held.composed, "job-b"),
            sort_keys=True))
    finally:
        case.doCleanups()


if __name__ == "__main__":
    sys.exit(_both())
