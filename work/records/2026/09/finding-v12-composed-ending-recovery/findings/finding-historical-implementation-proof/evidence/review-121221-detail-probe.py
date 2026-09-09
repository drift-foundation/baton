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

import signal
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("8s budget")))
signal.setitimer(signal.ITIMER_REAL, 8)
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

def cold(case):
    held = case.implemented()
    case.reopened()
    case.publication.retained.clear()
    with patch.object(case.publisher, 'canonical_target', side_effect=AssertionError('cold resume reads live canonical target')):
        result = observe(lambda: case.resume(held))
    return result

def cold_unrestricted(case):
    held = case.implemented()
    case.reopened()
    case.publication.retained.clear()
    before = case.control._connection.total_changes
    with patch.object(case.publisher, 'canonical_target', wraps=case.publisher.canonical_target) as target:
        result = observe(lambda: case.resume(held))
    return {'resume': result, 'live_target_reads': target.call_count, 'control_changes': case.control._connection.total_changes-before}

def forged_selectors(case):
    held = case.implemented()
    case.reopened()
    answer = case.publication.published_of(attempt_id=case.ATTEMPT)
    result = {}
    for name, value in [('proposal_id','proposal-elsewhere'),('proposal_manifest_digest','sha256:'+'3'*64)]:
        with patch.object(case.publication, 'published_of', return_value=dict(answer, **{name:value})):
            with case.no_external_act(held):
                result[name] = observe(lambda:case.resume(held))
    return result

def measured_detail(case):
    held = case.implemented()
    case.reopened()
    with case.no_external_act(held):
        warm = case.resume(held)
    different = [k for k in warm if warm[k] != held['ended'][k]]
    case.publication.retained.clear()
    statements=[]
    case.control._connection.set_trace_callback(statements.append)
    cold = observe(lambda:case.resume(held))
    case.control._connection.set_trace_callback(None)
    case.publication.retained.clear()
    with patch.object(case.publisher, 'canonical_target', return_value='c3'*20):
        drift = observe(lambda:case.resume(held))
    return {'ordinary_resume_different_members':different,'cold_returned':'returned' in cold,'cold_write_statements':[s for s in statements if s.startswith(('BEGIN','INSERT','UPDATE','DELETE','COMMIT'))],'later_target_drift':drift}

run('cold_transaction_and_return_contract',measured_detail)
paths = ["v12/python/src/baton_v12/job_manager/review_driver.py", "v12/python/tests/job_manager/test_review_driver.py"]
signal.setitimer(signal.ITIMER_REAL, 0)
report = {"work": "W120425", "claim": 121221, "sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}, "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
