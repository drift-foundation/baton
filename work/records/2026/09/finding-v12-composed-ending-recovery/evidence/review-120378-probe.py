"""Targeted receiving-boundary probes on disposable test stores only."""
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.job_manager.test_ending import EndingCase, STAGE, REVIEW, WORK_B, assignment, evidence
from tests.job_manager.test_review_driver import TheImplementationEndingIsReenterableAfterItsCleanup
from baton_v12.job_manager import ending

started = time.monotonic()
results = {}

def observe(call):
    try:
        return {"returned": call()}
    except Exception as error:
        return {"exception": type(error).__name__, "category": getattr(error, "category", None),
                "code": getattr(error, "code", None), "message": str(error)}

def job_case(name, run):
    case = EndingCase()
    case.setUp()
    try:
        results[name] = run(case)
    finally:
        case.tearDown()
        case.doCleanups()

job_case("foreign_authority_registration", lambda case: observe(
    lambda: case.register(assignment=assignment(authority_uuid="9" * 32))))

def null_references(case):
    case.register()
    case.cleaned_up()
    settled = case.settle(evidence=evidence(result_id=None, manifest_digest=None, receipt_digest=None))
    return {"settlement": settled, "implementation_state": case.projected(STAGE)["state"],
            "dependent_state": case.projected(REVIEW)["state"]}
job_case("null_required_evidence", null_references)

def foreign_settlement(case):
    case.register()
    case.cleaned_up()
    case.register(REVIEW, assignment=assignment(work_id=WORK_B))
    foreign = case.settle(REVIEW, assignment=assignment(work_id=WORK_B))
    held = case.jobs.operation_record(ending.settlement_operation_id(REVIEW, 1))
    # Copy an actual committed foreign document and its signature to the
    # selected identity through this disposable store's public journal API.
    case.jobs.transact(ending.settlement_operation_id(STAGE, 1), ending.SETTLED_KIND,
                       held["signature"], lambda connection: foreign)
    return {"read": ending.ending_of(case.jobs, STAGE, 1),
            "pending_stage_ids": [one["stage_id"] for one in ending.pending_endings(case.jobs)],
            "implementation_state": case.projected(STAGE)["state"],
            "dependent_state": case.projected(REVIEW)["state"]}
job_case("foreign_settlement_under_selected_identity", foreign_settlement)

def driver_case(name, publication):
    case = TheImplementationEndingIsReenterableAfterItsCleanup()
    case.setUp()
    try:
        case.gone()
        operations = case.control._connection.execute(
            "SELECT operation_id FROM operations WHERE kind='runtime.destroy'").fetchall()
        case.publication.answer = publication
        before = case.control._connection.total_changes
        with case.retained():
            answer = observe(case.resume)
        results[name] = {"cleanup_operations": [list(row) for row in operations],
                         "result": answer, "control_writes": case.control._connection.total_changes - before,
                         "fixture_limit": "retained frozen/intake/retention readers are mocked as in the added driver tests"}
    finally:
        case.tearDown()
        case.doCleanups()

driver_case("resume_without_cleanup_journal", {"proposal_id": "proposal-1", "result_id": "result-1"})
driver_case("resume_with_non_document_publication", [])
paths = ["src/baton_v12/job_manager/ending.py", "src/baton_v12/job_manager/projection.py",
         "src/baton_v12/job_manager/manager.py", "src/baton_v12/job_manager/review_driver.py",
         "tests/job_manager/test_ending.py", "tests/job_manager/test_review_driver.py"]
report = {"work": "W119733", "claim": 120378,
          "sha256": {path: hashlib.sha256((root / "v12/python" / path).read_bytes()).hexdigest() for path in paths},
          "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
