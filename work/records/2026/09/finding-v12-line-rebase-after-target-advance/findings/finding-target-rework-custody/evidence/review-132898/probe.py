"""Independent slice-A probes; only disposable test-owned stores/repositories."""
import json
from unittest.mock import patch

from manager.test_target_rework import (TargetReworkCase, Authority, Port,
                                       TARGET, PROPOSAL)
from baton_v12.worker_manager import grant_writer, freeze_checkpoint, line_of
from baton_v12.worker_manager.target_rework import prepare_rework, rework_of, effective_base


def report(name, **result):
    print(json.dumps(dict(probe=name, **result)), flush=True)


case = TargetReworkCase()
try:
    case.setUp()
    line, checkpoint, target, held = case.prepared()
    attempt = case.attempt('writer-attempt-2', 2, 'baton.impl', 'writer')
    args = dict(line_id=line['line_id'], attempt_id=attempt, generation=2,
                worker_id='impl-worker', profile=case.profile,
                based_checkpoint_id=checkpoint['checkpoint_id'])
    writer = grant_writer(case.store, **args)
    try:
        replay = grant_writer(case.store, **args)
        report('writer_replay', equal=replay == writer)
    except Exception as error:
        report('writer_replay', error=type(error).__name__, message=str(error))
    case.completed(attempt)
    frozen = freeze_checkpoint(case.store, writer_id=writer['writer_id'],
                               generation=2, profile=case.profile, port=Port('baton.impl'))
    report('freeze_without_unowned_checkout_reset', base=frozen['evidence']['base'],
           expected_base=target, head=frozen['evidence']['head'],
           old_head=checkpoint['evidence']['head'],
           prepared_head=held['prepared']['head'],
           job_a_content=case.vcs(line['line_path'], 'show', frozen['evidence']['head'] + ':harness.py'))
    case.store._connection.execute('UPDATE target_reworks SET target_revision = ? WHERE operation_id = ?',
                                   ('e' * 40, held['operation_id']))
    case.store._connection.commit()
    report('tampered_row', read_target=rework_of(case.store, held['operation_id'])['target_revision'],
           effective_base=effective_base(case.store, line['line_id']), original_target=target)
finally:
    case.doCleanups()

case = TargetReworkCase()
try:
    case.setUp()
    line, checkpoint = case.accepted_line()
    target = case.advanced()
    settlement = case.settled()
    args = dict(line_id=line['line_id'], checkpoint_id=checkpoint['checkpoint_id'],
                target_id=TARGET, target_source=case.target_place, target_proposal_id=PROPOSAL,
                profile=case.profile, settlement_id=settlement['settlement_id'])
    with patch.object(case.profile, 'prepare_rework', side_effect=RuntimeError('injected death after committed intent')):
        try:
            prepare_rework(case.store, Authority(target), **args)
        except RuntimeError:
            pass
    with patch.object(case.profile, 'prepare_rework', wraps=case.profile.prepare_rework) as resumed:
        result = prepare_rework(case.store, Authority(target), **args)
        report('intent_cutpoint_recovery', state=result['state'], prepared=result['prepared'],
               profile_calls=resumed.call_count, line_state=line_of(case.store, line['line_id'])['state'])
finally:
    case.doCleanups()
