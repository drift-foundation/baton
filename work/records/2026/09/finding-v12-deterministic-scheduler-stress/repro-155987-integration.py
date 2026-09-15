"""Follow-up to reviewer's allocation-key error; public live episode supplies attempt."""
import json
from baton_v12.job_manager import live_of
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases

case = Cases("test_both_jobs_traverse_and_one_integrator_serializes_them")
case.setUp()
try:
    captured = {}
    allocation = case.integration_allocation
    def remember(held):
        captured["held"] = held
        return allocation(held)
    case.integration_allocation = remember
    case.test_both_jobs_traverse_and_one_integrator_serializes_them()
    held = captured["held"]
    attempt = live_of(held.job, "job-a/integration")["attempt_id"]
    code = case.case.integration_turn(held, attempt)
    print(json.dumps({"existing_integration_turn_exit": code}), flush=True)
    assert code == 0
    case.case.engine.stopped = True
    states = case.case.drive_job(held.job, held.composed, "job-a", "integration", "completed", ticks=4)
    assert states["integration"] == "completed"
    print(json.dumps({"continued_job_a": states, "job_b": case.case.states_for(held.job, held.composed, "job-b")}, sort_keys=True), flush=True)
finally:
    case.doCleanups()
