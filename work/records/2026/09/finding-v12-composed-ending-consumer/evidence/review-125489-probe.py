"""Budget4s: integration refusal, one correction cycle, lost discharge answer."""
import hashlib
import json
import pathlib
import time
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import sweep
from baton_v12.worker_manager import gate_discharge_of
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import (
    TheComposedJobTraversesReviewAndAcceptance as Lifecycle,
    TheComposedEndingIsOrderedAndSettledFromItsOwnRecord as Ending)
from tools import stage_execution

started = time.monotonic()
results = {}
for correction in (False, True):
    case = Lifecycle()
    label = 'correction_then_acceptance' if correction else 'accepted_integration'
    record = {}
    try:
        case.setUp()
        held = case.reviewed('changes-requested' if correction else 'accepted')
        if correction:
            case.drive(held.job, held.composed, 'implementation', 'waiting', ticks=12)
            second = case.only_attempt_of(held.composed, 'implementation', exclude=held.attempt_id)
            record['correction_started'] = True
            record['correction_turn'] = case.turn(held.control, 'implementation', second, case.mounted(held.composed, 'implementation', second), edits={'harness.py': "print('second correction')\n"})
            case.drive(held.job, held.composed, 'review', 'waiting', ticks=12)
            review = case.only_attempt_of(held.composed, 'review', exclude=held.review)
            record['second_review_started'] = True
            record['second_review_turn'] = case.turn(held.control, 'review', review, case.mounted(held.composed, 'review', review), edits={'review-report.json': json.dumps(case.REPORT)})
        case.drive(held.job, held.composed, 'integration', 'claimed', ticks=12)
        record['integrator_claimed'] = True
        port = case.integration_port(held)
        composed = stage_execution.operations_from(case.composed_document(line_declared_base=case.base), held.job, held.control, engine_run=case.engine, credential_provider=lambda *_: case.secret, clock=lambda: fixtures.NOW, checkout=case.checkout, integration_port=port)
        case.addCleanup(composed.close)
        case._composed = composed
        held.composed = composed
        record['reports'] = [sweep(held.job, composed, now=fixtures.NOW) for _ in range(2)]
        record['states'] = case.states(held.job, composed)
    except Exception as failure:
        record['failure'] = {'type': type(failure).__name__, 'message': str(failure)}
    finally:
        case.doCleanups()
    results[label] = record

case = Ending()
try:
    case.setUp()
    held = case.cleaned_up()
    worker = case.worker_of(held.composed, 'implementation')
    original = worker.port.satisfy_gate
    def lost_answer(*args, **kwargs):
        original(*args, **kwargs)
        raise ContractRefusal('ambiguous', 'operation', 'review probe: remote answer lost')
    with mock.patch.object(worker.port, 'satisfy_gate', side_effect=lost_answer):
        sweep(held.job, held.composed, now=fixtures.NOW)
    worker.stage._prepared.clear()
    sweep(held.job, held.composed, now=fixtures.NOW)
    receipt = gate_discharge_of(held.control, held.attempt_id)
    settlement = case.ending_records(held)['settlement']
    results['discharge_recovery'] = {'receipt_present': receipt is not None, 'settlement': settlement}
finally:
    case.doCleanups()
results['elapsed_seconds'] = time.monotonic() - started
root = pathlib.Path('/home/sl/src/baton/v12/python')
evidence = pathlib.Path(__file__).parent
manifest = json.loads((evidence / 'consumer-125449.json').read_text())
results['hashes'] = {name: {'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest(), 'matches': hashlib.sha256((root / name).read_bytes()).hexdigest() == item['sha256']} for name, item in manifest['paths'].items()}
(evidence / 'review-125489-probe.json').write_text(json.dumps(results, indent=2, default=str) + '\n')
for label in ('accepted_integration', 'correction_then_acceptance'):
    record = dict(results[label])
    if 'reports' in record:
        record['reports'] = [report.get('started') for report in record['reports']]
    print(label, json.dumps(record, default=str))
print('discharge_recovery', json.dumps(results['discharge_recovery'], default=str))
print('elapsed_seconds', results['elapsed_seconds'])
print('hashes', json.dumps(results['hashes']))
