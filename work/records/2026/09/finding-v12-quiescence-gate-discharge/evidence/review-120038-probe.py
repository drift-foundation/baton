"""Present-record refusal checks in disposable Worker Manager fixtures only."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python/src"), str(root / "v12/python")]
from tests.manager.test_intake import ATTEMPT, TheQuiescenceGateIsDischargedFromTheCommittedCleanup as Case
from baton_v12.worker_manager import gate_discharge_of

results = []
for scenario in ("sql-null", "json-null", "foreign-kind", "list-result"):
    case = Case("test_a_settled_cleanup_discharges_the_gate_and_frees_the_work")
    case.setUp()
    try:
        case.settled()
        case.gated()
        receipt = case.discharge()
        column = "kind" if scenario == "foreign-kind" else "result"
        value = {"sql-null": None, "json-null": "null", "foreign-kind": "unrelated.operation", "list-result": "[]"}[scenario]
        try:
            case.store._connection.execute(
                "UPDATE operations SET " + column + "=? WHERE operation_id=?",
                (value, receipt["operation_id"]))
        except Exception as error:
            results.append({"scenario": scenario, "fixture_write_refused": type(error).__name__})
            continue
        outcomes = {}
        for name, call in [("discovery", lambda: gate_discharge_of(case.store, ATTEMPT)), ("replay", case.discharge)]:
            try:
                outcomes[name] = {"returned": call()}
            except Exception as error:
                outcomes[name] = {"exception": type(error).__name__, "category": getattr(error, "category", None), "code": getattr(error, "code", None)}
        results.append({"scenario": scenario, "outcomes": outcomes})
    finally:
        case.tearDown()
        case.doCleanups()
paths = ["src/baton_v12/worker_manager/authority_port.py", "src/baton_v12/worker_manager/intake.py", "src/baton_v12/worker_manager/__init__.py", "tests/manager/test_intake.py", "tests/manager/test_offers.py", "tests/manager/test_secrets.py"]
report = {"claim": 120038, "sha256": {p: hashlib.sha256((root / "v12/python" / p).read_bytes()).hexdigest() for p in paths}, "results": results}
with (Path(__file__).parent / "review-120038-probe.json").open("x") as out:
    out.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
