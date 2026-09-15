"""Independent bounded review probes; scripted providers, real owner operations."""
import copy
import json
from pathlib import Path

from tests.tools import scheduler_trace as oracle
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases


def main():
    artifacts = {s["name"]: s["artifact"] for s in json.loads(Path(__file__).with_name("trace-155914-composed.json").read_text())["schedules"]}
    checks = {}
    original = artifacts["composed-correction"]
    assert oracle.validate(original) == []
    for member, value in (("reviewer_participant", "other.unassigned"), ("reviewer_principal", "principal:other.unassigned"), ("review_assignment_generation", 999)):
        altered = copy.deepcopy(original)
        next(r for r in altered["records"] if r["act"] == "correct")["correction"][member] = value
        checks[member] = oracle.validate(altered)
        assert checks[member]
    altered = copy.deepcopy(original)
    for row in altered["records"]:
        if row.get("stage_id") == "job-a/review":
            row.update(stage_id="job-b/review", job_id="job-b")
    checks["foreign_job"] = oracle.validate(altered)
    assert checks["foreign_job"]
    print(json.dumps({"correction_mutations": checks}, sort_keys=True), flush=True)

    case = Cases("test_the_composed_deployment_reopens_and_continues")
    case.setUp()
    try:
        reopen = case.reopened
        def observed_reopen(held):
            print(json.dumps({"reopen_boundary": {
                "job_b_states": case.case.states_for(held.job, held.composed, "job-b"),
                "running_engine_records": sum(bool(r["running"]) for r in case.case.engine.records.values()),
                "engine_starts": len(case.case.engine.starts)}}, sort_keys=True), flush=True)
            return reopen(held)
        case.reopened = observed_reopen
        case.test_the_composed_deployment_reopens_and_continues()
    finally:
        case.doCleanups()

    case = Cases("test_both_jobs_traverse_and_one_integrator_serializes_them")
    case.setUp()
    try:
        captured = {}
        allocation = case.integration_allocation
        def remember(held):
            captured["held"] = held
            captured["allocation"] = allocation(held)
            return captured["allocation"]
        case.integration_allocation = remember
        case.test_both_jobs_traverse_and_one_integrator_serializes_them()
        held = captured["held"]
        attempt = captured["allocation"]["attempt_id"]
        code = case.case.integration_turn(held, attempt)
        print(json.dumps({"existing_integration_turn_exit": code}), flush=True)
        assert code == 0
        case.case.engine.stopped = True
        states = case.case.drive_job(held.job, held.composed, "job-a", "integration", "completed", ticks=4)
        assert states["integration"] == "completed"
        print(json.dumps({"continued_job_a": states, "job_b": case.case.states_for(held.job, held.composed, "job-b")}, sort_keys=True), flush=True)
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
