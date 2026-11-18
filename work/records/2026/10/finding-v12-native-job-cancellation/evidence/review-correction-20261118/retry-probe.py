"""Independent deterministic probe; run with prepared interpreter from v12/python."""
import json
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts
from tests.tools.test_job_cancellation_command import InstalledCancellation

case = InstalledCancellation()
case.setUp()
try:
    case.drive(case.jobs, case.composed, 'implementation', 'waiting')
    case.cancel()
    original = attempts._order_quiescence
    def interrupted(store, agent, adapter, attempt_id, assignment, operation_id):
        with mock.patch.object(adapter, 'stop', side_effect=ContractRefusal('refused', 'precondition', 'injected transient stop refusal')):
            return original(store, agent, adapter, attempt_id, assignment, operation_id)
    with mock.patch.object(attempts, '_order_quiescence', side_effect=interrupted):
        first = case.tick()
    following = [case.tick() for _ in range(3)]
    result = {'first_cancellation': first.get('cancelled'), 'following_cancellation': [r.get('cancelled') for r in following], 'stops': len(case.stops()), 'runtime': case.axes()['execution_runtime'], 'report': case.report()}
    print(json.dumps(result, indent=2))
    assert result['stops'] == 1, result
    assert result['following_cancellation'][0][0]['outcome'] == 'ordered', result
    print('PASS: recovered stop is ordered on the next tick')
finally:
    case.tearDown()
    case.doCleanups()
