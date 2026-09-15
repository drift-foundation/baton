"""Independent trace mutations and scripted-engine probes; no owner-state fabrication."""
import copy
import json
from pathlib import Path
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools import scheduler_trace as oracle
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases
from tests.tools.test_scheduler_trace import TheValidatorRefusesSyntheticInvalidTraces as Negatives


def main():
    artifacts = {s["name"]: s["artifact"] for s in json.loads(Path(__file__).with_name("trace-156029-composed.json").read_text())["schedules"]}
    terminal = artifacts["composed-two-jobs-one-integrator"]
    print(json.dumps({"terminal_artifact": {"violations": oracle.validate(terminal), "acts": sorted({r["act"] for r in terminal["records"]}), "authorization_references": terminal.get("authorization_references")}}, sort_keys=True), flush=True)
    n = Negatives()
    first = n.legal(acts=("reserve",), tick=1)
    second = n.legal(attempt="attempt-2", acts=("reserve",), tick=2)
    release = n.record(act="release", attempt_id="attempt-1", tick=2, worker_id="impl-one", principal="principal:one", operation_id="attempt-1:release")
    print(json.dumps({"same_tick_release": n.codes(first + second + [release])}), flush=True)
    foreign = dict(release, worker_id="foreign-worker", principal="principal:foreign")
    print(json.dumps({"foreign_release_identity": n.codes(first + second + [foreign])}), flush=True)
    second[0]["recorded_at"] = "2026-09-02T00:00:01.000Z"
    release["recorded_at"] = "2026-09-02T00:00:02.000Z"
    print(json.dumps({"release_after_reservation_owner_instants": n.codes(first + second + [release])}), flush=True)

    case = Cases("test_the_composed_deployment_reopens_and_continues")
    case.setUp()
    try:
        original = case.reopened
        def duplicate_start(held):
            second = original(held)
            vectors = [v for v in case.case.engine.starts if held.second in " ".join(v)]
            assert len(vectors) == 1, len(vectors)
            case.case.engine(vectors[0])
            print(json.dumps({"synthetic_extra_job_b_engine_start": True}), flush=True)
            return second
        case.reopened = duplicate_start
        case.test_the_composed_deployment_reopens_and_continues()
        print(json.dumps({"candidate_reopen_assertions_accept_duplicate_start": True}), flush=True)
    finally:
        case.doCleanups()

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
        for quiescent in (True, False):
            case.case.engine.stopped = quiescent
            report = sweep(held.job, held.composed, now=fixtures.NOW)
            details = {key: [r for r in rows if isinstance(r, dict) and r.get("stage_id") == "job-b/integration"] for key, rows in report.items() if isinstance(rows, list)}
            print(json.dumps({"scripted_engine_stopped": quiescent, "job_b_sweep": details}, sort_keys=True, default=str), flush=True)
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
