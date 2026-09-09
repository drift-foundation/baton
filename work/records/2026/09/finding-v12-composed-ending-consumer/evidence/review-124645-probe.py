"""Independent two-cutpoint probe; execute from v12/python with PYTHONPATH=.:src:tests.

Only disposable existing test fixtures are changed. No live coordination store.
"""
import json
import time
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import review_driver, submit, sweep
from baton_v12.worker_manager import attempt_runtime_of, gate_discharge_of
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import TheComposedEndingIsOrderedAndSettledFromItsOwnRecord as Case


def probe():
    results = {}
    case = Case()
    case.setUp()
    try:
        held = case.cleaned_up()
        results["receipt_before"] = gate_discharge_of(held.control, held.attempt_id)
        case.worker_of(held.composed, "implementation").stage._prepared.clear()
        results["retry"] = sweep(held.job, held.composed, now=fixtures.NOW)
        results["receipt_after"] = gate_discharge_of(held.control, held.attempt_id)
        results["settlement"] = case.ending_records(held)["settlement"]
    finally:
        case.doCleanups()

    case = Case()
    case.setUp()
    try:
        job, control, composed = case.serving()
        submit(job, case.submission)
        case.drive(job, composed, "implementation", "waiting")
        attempt_id = case.only_attempt(composed, "implementation")
        roots = case.mounted(composed, "implementation", attempt_id)
        assert case.turn(control, "implementation", attempt_id, roots,
                         edits={"harness.py": "print('the corrected harness')\n"}) == 0
        held = SimpleNamespace(job=job, control=control, composed=composed,
                               attempt_id=attempt_id, roots=roots)
        with mock.patch.object(review_driver, "authorize_cleanup", side_effect=ContractRefusal("refused", "precondition", "review probe: cleanup temporarily unavailable")):
            results["cleanup_cut"] = sweep(job, composed, now=fixtures.NOW)
        results["runtime_after_freeze"] = attempt_runtime_of(control, attempt_id)
        worker = case.worker_of(composed, "implementation")
        worker.stage._prepared.clear()
        results["freeze_retry"] = sweep(job, composed, now=fixtures.NOW)
        results["freeze_ending"] = case.ending_records(held)
    finally:
        case.doCleanups()
    return results


started = time.monotonic()
results = probe()
results["elapsed_seconds"] = time.monotonic() - started
print(json.dumps(results, indent=2, default=str))
