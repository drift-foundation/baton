"""The parent review's three Job-journal reproductions, re-run unchanged.

W120424, claim 120461. Same disposable JobStore, same public journal API and
the same three scenarios as `../../../evidence/review-120378-probe.py`; only
the expectation changed, so what this measures is the correction rather than a
new fixture. Writes nothing outside its own temporary stores.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[8]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.job_manager.test_ending import (EndingCase, REVIEW, STAGE, WORK_B,
                                           assignment, evidence)
from baton_v12.job_manager import ending

started = time.monotonic()
results = {}


def observe(call):
    try:
        return {"returned": call()}
    except Exception as error:
        return {"exception": type(error).__name__,
                "category": getattr(error, "category", None),
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
    settled = observe(lambda: case.settle(evidence=evidence(
        result_id=None, manifest_digest=None, receipt_digest=None)))
    return {"settlement": settled,
            "implementation_state": case.projected(STAGE)["state"],
            "dependent_state": case.projected(REVIEW)["state"],
            "pending_stage_ids": [one["stage_id"] for one
                                  in ending.pending_endings(case.jobs)]}


job_case("null_required_evidence", null_references)


def foreign_settlement(case):
    case.register()
    case.cleaned_up()
    case.register(REVIEW, assignment=assignment(work_id=WORK_B))
    foreign = case.settle(REVIEW, assignment=assignment(work_id=WORK_B))
    held = case.jobs.operation_record(
        ending.settlement_operation_id(REVIEW, 1))
    case.jobs.transact(ending.settlement_operation_id(STAGE, 1),
                       ending.SETTLED_KIND, held["signature"],
                       lambda connection: foreign)
    return {"read": observe(lambda: ending.ending_of(case.jobs, STAGE, 1)),
            "discovery": observe(
                lambda: [one["stage_id"] for one
                         in ending.pending_endings(case.jobs)]),
            "implementation_state": observe(
                lambda: case.projected(STAGE)["state"]),
            "dependent_state": observe(
                lambda: case.projected(REVIEW)["state"]),
            "review_settlement_is_still_its_own": (
                ending.settlement_of(case.jobs, REVIEW, 1) == foreign)}


job_case("foreign_settlement_under_selected_identity", foreign_settlement)

paths = ["src/baton_v12/job_manager/ending.py",
         "src/baton_v12/job_manager/projection.py",
         "src/baton_v12/job_manager/manager.py",
         "tests/job_manager/test_ending.py"]
report = {"work": "W120424", "claim": 120461,
          "sha256": {path: hashlib.sha256(
              (root / "v12/python" / path).read_bytes()).hexdigest()
              for path in paths},
          "results": results, "seconds": time.monotonic() - started}
Path(__file__).with_suffix(".json").write_text(
    json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
