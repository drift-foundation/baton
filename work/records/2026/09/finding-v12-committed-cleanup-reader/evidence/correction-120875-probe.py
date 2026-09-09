"""The review's seven reopened-fixture probes, re-run unchanged.

W120762, claim 120875. Same fixture entry points and the same seven damaged
states as `review-120847-probe.py`; only the expectation changed.
"""
import hashlib
import json
import time
from pathlib import Path

from tests.manager import test_intake as t
from baton_v12.contracts import ContractRefusal

evidence = Path(__file__).resolve().parent
start = time.monotonic()
results = {}


def run(name, disposition="retain", change=None, sql=None, failed=False):
    case = t.TheCommittedCleanupIsReadableWithoutActing("run")
    case.setUp()
    try:
        kwargs = {}
        if failed:
            kwargs["destroyed"] = {
                "state": "running", "why": "survived",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "not-delivered"}}
        settled = case.settled(disposition, **kwargs)
        case.reopened()
        operation = settled["operation"]["operation_id"]
        statement, values = sql if sql else (
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(dict(settled, **change)), operation))
        if sql and values == "operation":
            values = (operation,)
        with case.damaged(statement, values), case.no_act():
            try:
                result = {"returned": case.read()}
            except ContractRefusal as exc:
                result = {"refused": [exc.category, exc.code, exc.message]}
        results[name] = {"ordinary_ending": settled["cleanup"],
                         "result": result,
                         "no_external_calls_or_writes": True}
    finally:
        case.doCleanups()


run("retained_material_reported_complete", change={"cleanup": "complete"})
run("discard_reported_retained", disposition="discard-after-intake",
    change={"cleanup": "retained"})
run("uncertain_runtime_reported_settled_failed", failed=True,
    change={"state": "uncertain"})
run("unknown_runtime_reported_settled_failed", failed=True,
    change={"state": "invented"})
run("foreign_signature_with_unchanged_receipt",
    sql=("UPDATE operations SET signature = '{}' WHERE operation_id = ?",
         "operation"))
run("discard_with_missing_retention_decisions",
    disposition="discard-after-intake",
    sql=("DELETE FROM retentions WHERE runtime_attempt_id = ?", (t.ATTEMPT,)))
run("unowned_optional_kind", change={"kind": ["foreign", "ending"]})

paths = ("src/baton_v12/worker_manager/intake.py",
         "src/baton_v12/worker_manager/__init__.py",
         "tests/manager/test_intake.py",
         "tests/manager/test_secrets.py")
report = {"work": "W120762", "claim": 120875,
          "sha256": {path: hashlib.sha256(
              (Path("v12/python") / path).read_bytes()).hexdigest()
              for path in paths},
          "results": results, "seconds": time.monotonic() - start}
(evidence / "correction-120875-probe.json").write_text(
    json.dumps(report, indent=2) + "\n")
print(json.dumps({"seconds": report["seconds"], "results": {
    name: {"accepted": "returned" in held["result"],
           "refusal": held["result"].get("refused", [None, None, ""])[:2]}
    for name, held in results.items()}}, indent=2))
