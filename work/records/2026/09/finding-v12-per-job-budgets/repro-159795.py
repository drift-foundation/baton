"""Independent actual materialization census and blocked public owner refusals."""
import copy
import json
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
from baton_v12.integration import reconciliation

case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
calls, snapshots, retained = [], [], []
materialize = stage_execution._materialize
read_failure = reconciliation.failed_host_verification
scratch_count = case._scratch_count
def watched_materialize(*args, **kwargs):
    calls.append(str(args[2]))
    return materialize(*args, **kwargs)
def counted(held):
    snapshots.append(len(calls))
    return scratch_count(held)
def read(store, result_id):
    answer = read_failure(store, result_id)
    retained.append((store, result_id))
    return answer
try:
    case.setUp()
    case._scratch_count = counted
    with patch.object(stage_execution, '_materialize', watched_materialize), patch.object(reconciliation, 'failed_host_verification', read):
        case.test_resumed_serving_after_a_reopen_runs_no_command()
    assert len(snapshots) == 2 and snapshots[0] == snapshots[1] and snapshots[0] > 0, snapshots
    store, result_id = retained[-1]
    deployment = case.case.deployment_of(case.case._composed)
    before = copy.deepcopy(reconciliation.result_of(store, result_id))
    refusals = []
    operations = [
        ('publish_result', lambda: reconciliation.publish_result(store, deployment.sessions['integrator'], result_id=result_id, input_digest='sha256:'+'1'*64, policy_digest='sha256:'+'2'*64)),
        ('record_result_evidence', lambda: reconciliation.record_result_evidence(store, deployment.authority, deployment.sessions['verification'], deployment.sessions['review'], deployment.sessions['approval'], result_id=result_id)),
        ('record_imported', lambda: reconciliation.record_imported(store, deployment.authority, result_id=result_id, entry_id='never-admitted')),
    ]
    for name, operation in operations:
        try:
            operation()
        except Exception as refusal:
            assert 'blocked' in str(refusal), (name, type(refusal).__name__, str(refusal))
            refusals.append({'operation': name, 'type': type(refusal).__name__, 'category': getattr(refusal, 'category', None), 'code': getattr(refusal, 'code', None), 'message': str(refusal)})
        else:
            raise AssertionError(name+' accepted a blocked result')
        assert reconciliation.result_of(store, result_id) == before
    print(json.dumps({'materialization_counts_before_after': snapshots, 'host_calls': case.seen, 'state': before['state'], 'refusals': refusals}, indent=2))
finally:
    case.doCleanups()
