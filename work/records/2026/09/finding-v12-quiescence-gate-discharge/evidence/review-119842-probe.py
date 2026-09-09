"""Offline receiving-boundary probes; uses only disposable manager fixtures."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[6]
sys.path[:0] = [str(ROOT / "v12/python/src"), str(ROOT / "v12/python")]
from tests.manager.test_intake import (ATTEMPT,
    TheQuiescenceGateIsDischargedFromTheCommittedCleanup as Case)
from baton_v12.worker_manager import gate_discharge_of

results = []
for scenario in ("changed-runtime", "wrong-answer", "foreign-authority"):
    case = Case("test_a_settled_cleanup_discharges_the_gate_and_frees_the_work")
    case.setUp()
    try:
        original = case.settled()
        original_runtime = case.attempt_row()["runtime_id"]
        case.gated()
        if scenario == "changed-runtime":
            case.store._connection.execute(
                "UPDATE attempts SET runtime_id=? WHERE runtime_attempt_id=?",
                ("runtime-never-observed-absent", ATTEMPT))
        elif scenario == "wrong-answer":
            case.session.satisfy_gate = lambda operands: {
                "gate": "runtime-quiescence:99", "kind": [], "phase": "block"}
        else:
            case.session._work["authority_uuid"] = "9" * 32
        try:
            answer = case.discharge()
            outcome = {"accepted": answer}
        except Exception as error:
            outcome = {"refused_or_faulted": type(error).__name__, "message": str(error)}
        results.append({"scenario": scenario, "original_runtime": original_runtime,
                        "cleanup_operation": original["operation"],
                        "outcome": outcome, "gate_remaining": case.session._work["gate"],
                        "evidence": case.session.gate_evidence,
                        "discoverable": gate_discharge_of(case.store, ATTEMPT)})
    finally:
        case.tearDown()
        case.doCleanups()
print(json.dumps(results, indent=2))
