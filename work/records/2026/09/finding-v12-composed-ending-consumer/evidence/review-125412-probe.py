"""Budget4s: ordinary accepted/correction routes and lost discharge answer."""
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
result = {}
for verdict in ('accepted', 'changes-requested'):
    case = Lifecycle()
    try:
        case.setUp()
        held = case.reviewed(verdict)
        reports = [sweep(held.job, held.composed, now=fixtures.NOW) for _ in range(4)]
        result[verdict] = {'route': case.projected()['route'], 'states': case.states(held.job, held.composed), 'reports': reports}
    except Exception as failure:
        result[verdict] = {'exception': type(failure).__name__, 'message': str(failure)}
    finally:
        case.doCleanups()

case = Ending()
try:
    case.setUp()
    held = case.cleaned_up()
    worker = case.worker_of(held.composed, 'implementation')
    original = worker.port.satisfy_gate
    def lost_answer(*args, **kwargs):
        original(*args, **kwargs)
        raise ContractRefusal('ambiguous', 'operation', 'review probe: remote discharge committed, answer lost')
    with mock.patch.object(worker.port, 'satisfy_gate', side_effect=lost_answer):
        sweep(held.job, held.composed, now=fixtures.NOW)
    before = gate_discharge_of(held.control, held.attempt_id)
    worker.stage._prepared.clear()
    retry = sweep(held.job, held.composed, now=fixtures.NOW)
    result['lost_discharge_answer'] = {'receipt_before': before, 'receipt_after': gate_discharge_of(held.control, held.attempt_id), 'ending': case.ending_records(held), 'retry': retry}
finally:
    case.doCleanups()

result['elapsed_seconds'] = time.monotonic() - started
root = pathlib.Path('/home/sl/src/baton/v12/python')
evidence = pathlib.Path(__file__).parent
manifest = json.loads((evidence / 'consumer-125334.json').read_text())
result['hashes'] = {name: {'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest(), 'matches': hashlib.sha256((root / name).read_bytes()).hexdigest() == item['sha256']} for name, item in manifest['paths'].items()}
result['integration_port_sha256'] = hashlib.sha256((root / 'tools/integration_worker.py').read_bytes()).hexdigest()
(evidence / 'review-125412-probe.json').write_text(json.dumps(result, indent=2, default=str) + '\n')
for verdict in ('accepted', 'changes-requested'):
    item = result[verdict]
    if 'reports' in item:
        item = {**item, 'reports': [[{'stage': act.get('stage_id'), 'act': act.get('act'), 'outcome': act.get('outcome'), 'detail': act.get('detail')} for act in report['acts']] for report in item['reports']]}
    print(verdict, json.dumps(item, default=str))
lost = result['lost_discharge_answer']
print('lost_discharge_answer', json.dumps({'receipt_before': lost['receipt_before'], 'receipt_after': lost['receipt_after'], 'settlement': lost['ending']['settlement']}, default=str))
print('elapsed_seconds', result['elapsed_seconds'])
print('hashes', json.dumps(result['hashes']))
print('integration_port_sha256', result['integration_port_sha256'])
