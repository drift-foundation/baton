"""Targeted independent probes using the author's real-custody fixture."""
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

root = Path(__file__).resolve().parents[8]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.job_manager.test_review_driver import TheImplementationResumeReadsRealCommittedCustody as Case
from baton_v12.job_manager import review_driver

started = time.monotonic()
results = {}

def observe(call):
    try:
        return {"returned": call()}
    except Exception as error:
        return {"exception": type(error).__name__, "category": getattr(error, "category", None), "code": getattr(error, "code", None), "message": str(error)}

def run(name, procedure):
    case = Case()
    case.setUp()
    try:
        results[name] = procedure(case)
    finally:
        case.tearDown()
        case.doCleanups()

def discard(case):
    original = review_driver.end_implementation
    def ending(*args, **kwargs):
        kwargs["retention_disposition"] = "discard-after-intake"
        return original(*args, **kwargs)
    with patch.object(review_driver, "end_implementation", ending):
        held = case.implemented()
    case.reopened()
    record = json.loads(case.control._connection.execute("SELECT result FROM operations WHERE kind = 'runtime.destroy'").fetchone()[0])
    with case.no_external_act(held):
        answered = observe(lambda: case.resume(held, retention_disposition="discard-after-intake"))
    return {"ordinary_cleanup": record["cleanup"], "ordinary_kept": record["kept"], "resume": answered}

def damaged_custody(case):
    held = case.implemented()
    case.reopened()
    row = case.control._connection.execute("SELECT operation_id, result FROM operations WHERE kind = 'runtime.destroy'").fetchone()
    record = json.loads(row["result"])
    record["directory_custody"] = {key: {} for key in record["directory_custody"]}
    case.control._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?", (json.dumps(record), row["operation_id"]))
    with case.no_external_act(held):
        answered = observe(lambda: case.resume(held))
    return {"substituted_directory_custody": record["directory_custody"], "resume": answered}

run("real_discard_ending", discard)
run("empty_nested_cleanup_custody", damaged_custody)
paths = ["v12/python/src/baton_v12/job_manager/review_driver.py", "v12/python/tests/job_manager/test_review_driver.py"]
report = {"work": "W120425", "claim": 120624, "sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}, "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
