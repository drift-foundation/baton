"""Independent bounded observations of retained 04648e1b, not product tests."""
import json
from pathlib import Path
import time
from unittest import mock
from tests.tools.test_work_command import WorkCommandCase, WORK, SLAW
from tests.job_manager.test_creation import CreationCase, FakeAuthorization, request
from baton_v12.job_manager import creation
from baton_v12.authority.labels import MAX_LABELS

out = Path(__file__).resolve().parent
started = time.monotonic()
observed = {}

case = CreationCase()
case.setUp()
try:
    authorization = FakeAuthorization(labels=['hot', 'v12'])
    from baton_v12.contracts import ContractRefusal
    try:
        case.created(authorization=authorization, request=request(labels=['v12']))
    except ContractRefusal as exc:
        observed['preexisting_work_with_explicit_subset_labels'] = {'state':'refused','message':str(exc),'reservations':case.rows()}
    else:
        raise AssertionError('unrelated existing Work accepted')

finally:
    case.doCleanups()

case = WorkCommandCase()
case.setUp()
try:
    case.work()
    case.allow()
    first = case.run_command('label-work', participant=SLAW, work=WORK, operation_id='review-add', labels=['v12'])
    removed = case.run_command('unlabel-work', participant=SLAW, work=WORK, operation_id='review-remove', labels=['v12'])
    before = len(case.events())
    replay = case.run_command('label-work', participant=SLAW, work=WORK, operation_id='review-add', labels=['v12'])
    observed['exact_replay_after_intervening_mutation'] = {
        'exit_codes': [first[0], removed[0], replay[0]],
        'byte_identical': first == replay, 'first': json.loads(first[1]),
        'replay': json.loads(replay[1]), 'events_before_replay': before,
        'events_after_replay': len(case.events())}
finally:
    case.doCleanups()

case = WorkCommandCase()
case.setUp()
try:
    case.work(labels=[f'label-{i:02d}' for i in range(MAX_LABELS - 1)])
    case.allow()
    answer = case.run_command('label-work', participant=SLAW, work=WORK, operation_id='review-overflow', labels=['z-last-slot', 'zz-overflow'])
    observed['multi_label_overflow'] = {'exit_code': answer[0], 'stdout': answer[1], 'stderr': answer[2],
                                        'new_labels_retained': [one for one in case.live() if one.startswith('z')]}
finally:
    case.doCleanups()

with mock.patch('baton_v12.authority.labels.canonical_label_set', side_effect=RuntimeError('review sentinel')):
    try:
        creation._labels(['v12'])
    except RuntimeError:
        observed['typed_refusal_allowlist'] = 'RuntimeError escapes; not masked by new Refusal catch'
    else:
        raise AssertionError('unexpected broad exception masking')

observed['seconds'] = time.monotonic() - started
(out / 'probe-results.json').write_text(json.dumps(observed, indent=2) + '\n')
print(json.dumps({'seconds':observed['seconds'], 'reuse':observed['preexisting_work_with_explicit_subset_labels']['state'],
                  'replay_identical':observed['exact_replay_after_intervening_mutation']['byte_identical'],
                  'overflow_retained':observed['multi_label_overflow']['new_labels_retained']}))
