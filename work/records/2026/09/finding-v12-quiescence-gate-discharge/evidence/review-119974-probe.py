"""Adopted receipt checks in disposable manager fixtures, not coordination SQL."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python/src"), str(root / "v12/python")]
from tests.manager.test_intake import ATTEMPT, TheQuiescenceGateIsDischargedFromTheCommittedCleanup as Case
from baton_v12.worker_manager import gate_discharge_of

results = []
spoils = [{"assignment": None}, {"assignment": {}},
          {"attempt_id": "another-attempt"}, {"gate": "runtime-quiescence:99"},
          {"operation_id": "some-other-operation"}, {"runtime_id": "foreign-runtime"}]
for members in spoils:
    case = Case("test_a_settled_cleanup_discharges_the_gate_and_frees_the_work")
    case.setUp()
    try:
        case.settled()
        case.gated()
        original = case.discharge()
        spoiled = dict(original, **members)
        case.store._connection.execute(
            "UPDATE operations SET result=? WHERE operation_id=?",
            (json.dumps(spoiled), original["operation_id"]))
        outcomes = {}
        for name, call in [("discovery", lambda: gate_discharge_of(case.store, ATTEMPT)),
                           ("replay", case.discharge)]:
            try:
                answer = call()
                outcomes[name] = {"returned": answer}
            except Exception as error:
                outcomes[name] = {"exception": type(error).__name__, "message": str(error)}
        results.append({"spoiled": members, "outcomes": outcomes})
    finally:
        case.tearDown()
        case.doCleanups()
paths = ["src/baton_v12/worker_manager/authority_port.py", "src/baton_v12/worker_manager/intake.py",
         "src/baton_v12/worker_manager/__init__.py", "tests/manager/test_intake.py",
         "tests/manager/test_offers.py", "tests/manager/test_secrets.py"]
report = {"claim": 119974, "sha256": {p: hashlib.sha256((root / "v12/python" / p).read_bytes()).hexdigest() for p in paths}, "results": results}
(Path(__file__).parent / "review-119974-probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"sha256": report["sha256"], "outcomes": [{"spoiled": r["spoiled"], "outcomes": {k: v.get("exception", "returned-unrelated-receipt") for k,v in r["outcomes"].items()}} for r in results]}, indent=2))
