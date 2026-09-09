"""Independent deterministic interleavings and historical-owner checks.

Only disposable repository fixtures and their SQLite stores are changed.
"""
import json
from pathlib import Path
import unittest

from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from tests.manager.test_checkpoint_profiles import RestoringOneCheckoutToItsRetainedCheckpoint as GitCase
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.contracts import ContractRefusal

results = {}

case = Case()
case.setUp()
try:
    case.abandoned()
    original = case.profile.restore_checkpoint
    events = []
    first = True
    def suspended_restore(repository, evidence):
        global first
        if first:
            first = False
            # A paused before its destructive profile effect. B completes
            # the identical recovery, then an ordinary successor is admitted.
            second = case.restore()
            granted = case.admit()
            case.profile.current_revision = 999
            events.append({'second_completed': second['state'],
                           'successor': granted['writer_id'],
                           'successor_scratch_revision': 999})
        events.append({'profile_write_while_line': cycles.line_of(case.store, case.line_id)['state']})
        return original(repository, evidence)
    case.profile.restore_checkpoint = suspended_restore
    answer = case.restore()
    results['inflight_duplicate'] = {
        'events': events, 'returned': answer['state'],
        'final_line': cycles.line_of(case.store, case.line_id)['state'],
        'final_scratch_revision': case.profile.current_revision,
        'profile_restore_count': len(case.profile.restore_calls)}
finally:
    case.tearDown()

case = Case()
case.setUp()
try:
    case.abandoned()
    answer = case.restore()
    case.store._connection.execute(
        "UPDATE line_writers SET principal = 'foreign-principal' WHERE writer_id = ?",
        (case.writer_row['writer_id'],))
    try:
        cycles.writer_for_attempt(case.store, attempt_id=case.abandoned_attempt, generation=2)
        owner = 'accepted'
    except ContractRefusal as failure:
        owner = {'category': failure.category, 'code': failure.code}
    read = cycles.abandoned_correction_of(case.store, attempt_id=case.abandoned_attempt, generation=2)
    replay = case.restore()
    results['historical_writer_disagrees'] = {
        'writer_owner': owner, 'reader_accepted_original': read == answer,
        'act_replayed_original': replay == answer}
finally:
    case.tearDown()

case = GitCase()
case.setUp()
try:
    case.dirty()
    original_path = Path(case.repository)
    outside = original_path.with_name('substituted-outside-line')
    original_path.rename(outside)
    original_path.symlink_to(outside, target_is_directory=True)
    answer = case.profile.restore_checkpoint(case.repository, case.evidence)
    results['symlink_substitution'] = {
        'accepted': answer == case.evidence,
        'nominated_path_is_symlink': original_path.is_symlink(),
        'outside_scratch_removed': not (outside/'scratch.txt').exists(),
        'outside_tracked_text': (outside/'kept.txt').read_text()}
finally:
    case.tearDown()

Path(__file__).with_suffix('.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))

suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Case),
                            unittest.defaultTestLoader.loadTestsFromTestCase(GitCase)])
run = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if run.wasSuccessful() else 1)
