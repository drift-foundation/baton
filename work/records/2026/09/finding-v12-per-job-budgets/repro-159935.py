"""Actual observation-operation replay/conflict using retained measured custody."""
import copy
import json
from types import SimpleNamespace
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from baton_v12.integration import reconciliation
from baton_v12.contracts import ContractRefusal

case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp()
    held, deployment, result_id = case._blocked_result()
    store = deployment.integration
    before = copy.deepcopy(reconciliation.result_of(store, result_id))
    counts = (len(case.seen), case.materialized)
    observed = copy.deepcopy(before['causal_observations'])
    answers, replay_calls, write_calls = [], [], []
    def observe(basis):
        answers.append(copy.deepcopy(basis))
        return dict(basis, execution=observed['execution'], observations=copy.deepcopy(observed))
    observer = SimpleNamespace(participant=before['observed_by'], observe=observe)
    replay, transact = store.replay, store.transact
    def replays(*args, **kwargs):
        replay_calls.append(args[0])
        return replay(*args, **kwargs)
    def writes(*args, **kwargs):
        write_calls.append(args[0])
        return transact(*args, **kwargs)
    with patch.object(store, 'replay', replays), patch.object(store, 'transact', writes):
        identical = reconciliation.record_causal_observations(store, observer, result_id=result_id)
        assert identical == before
        assert len(replay_calls) == 1 and not write_calls, (replay_calls, write_calls)
        # A changed valid diagnostic is a different observation signature;
        # this does not fabricate success or modify retained custody.
        observed['detail'] += ' [different replay attestation]'
        try:
            reconciliation.record_causal_observations(store, observer, result_id=result_id)
        except ContractRefusal as refused:
            assert refused.code == 'operation-collision', (refused.code, str(refused))
            conflict = {'category': refused.category, 'code': refused.code, 'message': str(refused)}
        else:
            raise AssertionError('conflicting observation replay accepted')
    assert reconciliation.result_of(store, result_id) == before
    assert (len(case.seen), case.materialized) == counts == (1, 1)
    assert not write_calls and len(replay_calls) == 1
    print(json.dumps({'result_id': result_id, 'state': before['state'], 'actual_journal_replay_calls': replay_calls, 'transact_calls': write_calls, 'replay_observer_calls': len(answers), 'command_materialization_counts': counts, 'conflict': conflict}, indent=2))
finally:
    case.doCleanups()
