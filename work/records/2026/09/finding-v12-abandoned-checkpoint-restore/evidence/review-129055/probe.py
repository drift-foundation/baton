"""Only disposable fixtures; measure effects independently of reported success."""
import json
from pathlib import Path
import unittest
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from tests.manager.test_checkpoint_profiles import RestoringOneCheckoutToItsRetainedCheckpoint as GitCase
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.checkpoint_profiles import GitCheckpointProfile
from baton_v12.contracts import ContractRefusal

results = {}
case = Case()
case.setUp()
try:
    case.abandoned()
    original = case.profile.restore_checkpoint
    seen = []
    def paused(repository, evidence):
        if not seen:
            seen.append('A paused')
            case.restore()
            case.admit()
            case.profile.current_revision = 999
            seen.append('B completed; successor admitted; scratch999')
        return original(repository, evidence)
    case.profile.restore_checkpoint = paused
    try:
        case.restore()
        outcome = 'accepted'
    except ContractRefusal as ex:
        outcome = [ex.category, ex.code]
    results['duplicate'] = {'outcome': outcome, 'events': seen,
                            'successor_scratch_after': case.profile.current_revision,
                            'line': cycles.line_of(case.store, case.line_id)['state']}
finally:
    case.tearDown()

case = Case()
case.setUp()
try:
    case.abandoned()
    case.profile.restore_refusal = ContractRefusal('refused', 'precondition', 'interrupted')
    try:
        case.restore()
    except ContractRefusal:
        pass
    case.profile.restore_refusal = None
    case.store._connection.execute(
        "UPDATE checkpoint_verdicts SET reviewer_principal = 'foreign-principal' WHERE checkpoint_id = ?",
        (case.checkpoint['checkpoint_id'],))
    calls = len(case.profile.restore_calls)
    answer = case.restore()
    try:
        cycles.abandoned_correction_of(case.store, attempt_id=case.abandoned_attempt, generation=2)
        reader = 'accepted'
    except ContractRefusal as ex:
        reader = [ex.category, ex.code]
    results['retry_skips_verdict'] = {'restore': answer['state'],
        'profile_effects_on_retry': len(case.profile.restore_calls)-calls,
        'completed_reader': reader}
finally:
    case.tearDown()

case = GitCase()
case.setUp()
try:
    case.dirty()
    original_path = Path(case.repository)
    outside = original_path.with_name('outside-after-check')
    before = (original_path/'kept.txt').read_text()
    real = case.runner
    def replace_before_effect(argv):
        if argv[3] == 'reset':
            original_path.rename(outside)
            original_path.symlink_to(outside, target_is_directory=True)
        return real(argv)
    try:
        GitCheckpointProfile(replace_before_effect).restore_checkpoint(case.repository, case.evidence)
        outcome = 'accepted'
    except Exception as ex:
        outcome = type(ex).__name__
    results['path_check_effect_gap'] = {'outcome': outcome,
        'outside_tracked_before': before,
        'outside_tracked_after': (outside/'kept.txt').read_text()}
finally:
    case.tearDown()

Path(__file__).with_suffix('.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
suite=unittest.TestSuite([
    Case('test_the_line_comes_back_correction_ready_at_the_same_checkpoint'),
    Case('test_the_reader_still_follows_its_owners_after_a_later_round'),
    GitCase('test_a_dirty_checkout_comes_back_to_the_exact_checkpoint')])
answer=unittest.TextTestRunner().run(suite)
raise SystemExit(0 if answer.wasSuccessful() else 1)
