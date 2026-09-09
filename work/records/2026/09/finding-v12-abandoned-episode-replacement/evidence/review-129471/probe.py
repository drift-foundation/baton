import json
from pathlib import Path
import unittest
from tests.job_manager.test_recovery import OneAbandonedCorrectionEpisodeIsReplaced as Case
from baton_v12.job_manager import episodes
from baton_v12.worker_manager import line_of
from baton_v12.contracts import ContractRefusal

results = {}

case = Case()
case.setUp()
try:
    case.abandoned()
    original = case.jobs.transact
    moved = []
    def during_handoff(operation_id, kind, signature, action):
        if kind == episodes.RESTART_KIND and not moved:
            moved.append(case.round(3, 'accepted', based=case.checkpoint_id))
        return original(operation_id, kind, signature, action)
    case.jobs.transact = during_handoff
    try:
        answer = case.restart()
        outcome = answer['ended_state']
    except ContractRefusal as ex:
        outcome = [ex.category, ex.code]
    results['accepted_review_before_commit'] = {
        'outcome': outcome,
        'line_state': line_of(case.control, case.line['line_id'])['state'],
        'live_episode': case.live('implementation'),
    }
finally:
    case.doCleanups()

case = Case()
case.setUp()
try:
    original = case.correct
    handoff_checkpoint = []
    def later_checkpoint(first):
        handoff_checkpoint.append(first['checkpoint_id'])
        answer = original(first)
        later = case.round(3, 'changes-requested', based=first['checkpoint_id'])
        case.checkpoint_id = later['checkpoint_id']
        return answer
    case.correct = later_checkpoint
    case.abandoned()
    try:
        answer = case.restart()
        outcome = answer['ended_state']
    except ContractRefusal as ex:
        outcome = [ex.category, ex.code]
    results['different_checkpoint_than_job_handoff'] = {
        'handoff_checkpoint': handoff_checkpoint[0],
        'restored_checkpoint': case.checkpoint_id,
        'outcome': outcome,
        'live_episode': case.live('implementation'),
    }
finally:
    case.doCleanups()

case = Case()
case.setUp()
try:
    case.abandoned()
    answer = case.restart()
    spoiled = dict(answer, schema='foreign-schema', assignment=None,
                   checkpoint_id='foreign-checkpoint')
    case.jobs._connection.execute(
        'UPDATE operations SET result=? WHERE operation_id=?',
        (json.dumps(spoiled), answer['operation_id']))
    try:
        replay = case.restart()
        results['malformed_replay'] = {'returned': replay}
    except ContractRefusal as ex:
        results['malformed_replay'] = {'refusal': [ex.category, ex.code]}
finally:
    case.doCleanups()

suite = unittest.TestSuite([
    Case('test_the_abandoned_episode_ends_and_the_sweep_opens_one_successor'),
    Case('test_an_exact_replay_answers_after_the_successor_has_started'),
    Case('test_an_accepted_review_supersedes_the_correction'),
])
control = unittest.TextTestRunner(verbosity=2).run(suite)
results['controls_pass'] = control.wasSuccessful()
Path(__file__).with_suffix('.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
raise SystemExit(0 if control.wasSuccessful() else 1)
