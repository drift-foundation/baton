"""Readback payload and optional-preload probes against disposable JobStores."""
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[8]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.job_manager.test_ending import EndingCase, STAGE, REVIEW, WORK_B, assignment, evidence, TERMINAL, RETENTION_POLICY
from baton_v12.job_manager import ending
from baton_v12.job_manager.store import job_signature

started = time.monotonic()
results = {}

def observe(call):
    try:
        return {"returned": call()}
    except Exception as error:
        return {"exception": type(error).__name__, "category": getattr(error, "category", None), "code": getattr(error, "code", None), "message": str(error)}

def document(case):
    attempt = case.attempting(case.jobs)
    return dict({key: attempt[key] for key in ending.SELECTORS}, assignment=assignment(), disposition="completed", terminal_manifest_digest=TERMINAL, retention_disposition="retain", retention_policy_digest=RETENTION_POLICY)

def settlement(intent, proof=None):
    return dict({key: intent[key] for key in ending.SELECTORS}, assignment=intent["assignment"], intent=ending.intent_operation_id(STAGE, 1), evidence=evidence() if proof is None else proof)

def write(case, kind, value):
    return case.jobs.transact(f"{kind}:{STAGE}:1", kind, job_signature(kind, value), lambda connection: value)

def decisions(case):
    return {"read": observe(lambda: ending.ending_of(case.jobs, STAGE, 1)), "pending": observe(lambda: [one["stage_id"] for one in ending.pending_endings(case.jobs)]), "states": observe(lambda: {key: value["state"] for key, value in case.projected().items()})}

def with_case(name, run):
    case = EndingCase()
    case.setUp()
    try:
        results[name] = run(case)
    finally:
        case.tearDown()
        case.doCleanups()

def malformed_evidence(case, proof):
    intent = case.register()
    case.cleaned_up()
    write(case, ending.SETTLED_KIND, settlement(intent, proof))
    return decisions(case)

for name, proof in (("null_references_on_read", evidence(result_id=None, manifest_digest=None, receipt_digest=None)), ("non_document_evidence", []), ("unknown_evidence_member", evidence(unowned=True))):
    with_case(name, lambda case, proof=proof: malformed_evidence(case, proof))

def malformed_intent(case):
    intent = document(case)
    intent.update(disposition=[], terminal_manifest_digest=None, retention_disposition={}, retention_policy_digest=False)
    write(case, ending.INTENT_KIND, intent)
    write(case, ending.SETTLED_KIND, settlement(intent))
    case.cleaned_up()
    return decisions(case)

with_case("malformed_intent_payload", malformed_intent)

def supplied_intent(case):
    intent = document(case)
    write(case, ending.SETTLED_KIND, settlement(intent))
    return {"ordinary": observe(lambda: ending.settlement_of(case.jobs, STAGE, 1)), "supplied": observe(lambda: ending.settlement_of(case.jobs, STAGE, 1, intent=intent)), "stored_intent": ending.intent_of(case.jobs, STAGE, 1)}

with_case("caller_intent_bypasses_orphan_refusal", supplied_intent)

def supplied_stage(case):
    intent = document(case)
    intent["work_id"] = WORK_B
    intent["assignment"] = assignment(work_id=WORK_B)
    write(case, ending.INTENT_KIND, intent)
    stage = dict(case.attempting(case.jobs), work_id=WORK_B)
    return {"ordinary": observe(lambda: ending.intent_of(case.jobs, STAGE, 1)), "supplied": observe(lambda: ending.intent_of(case.jobs, STAGE, 1, stage=stage))}

with_case("caller_stage_bypasses_stored_work_binding", supplied_stage)
paths = ["src/baton_v12/job_manager/ending.py", "src/baton_v12/job_manager/projection.py", "src/baton_v12/job_manager/manager.py", "tests/job_manager/test_ending.py"]
report = {"work": "W120424", "claim": 120507, "sha256": {p: hashlib.sha256((root / "v12/python" / p).read_bytes()).hexdigest() for p in paths}, "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps({"sha256": report["sha256"], "seconds": report["seconds"], "results": {name: {key: ("returned" if "returned" in value else value.get("exception")) if isinstance(value, dict) and ("returned" in value or "exception" in value) else value for key, value in result.items()} for name, result in results.items()}}, indent=2))
