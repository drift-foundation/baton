"""Bounded review probes using disposable Git/store fixtures only."""
import json
import os
from pathlib import Path
import shutil
import unittest
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from tests.manager.test_checkpoint_profiles import RestoringOneCheckoutToItsRetainedCheckpoint as GitCase
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.worker_manager.store import manager_signature
from baton_v12.checkpoint_profiles import GitCheckpointProfile

results = {}
for use_object_reference in (False, True):
    case = GitCase()
    case.setUp()
    fd = None
    try:
        case.dirty()
        original = Path(case.repository)
        foreign = original.with_name('foreign-repository')
        moved = original.with_name('held-original')
        shutil.copytree(original, foreign)
        (foreign/'kept.txt').write_text('foreign tracked scratch must survive\n')
        fd = os.open(original, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        real = case.runner
        switched = False
        def redirect(argv):
            global switched
            argv = list(argv)
            if argv[3] == 'reset' and not switched:
                original.rename(moved)
                original.symlink_to(foreign, target_is_directory=True)
                switched = True
            # Research-only alternative: an external command resolves the
            # live parent descriptor reference, never readlink's pathname.
            if use_object_reference:
                argv[2] = f'/proc/{os.getpid()}/fd/{fd}'
            return real(argv)
        try:
            answer = GitCheckpointProfile(redirect).restore_checkpoint(case.repository,case.evidence)
            outcome = 'accepted'
        except Exception as ex:
            outcome = type(ex).__name__
        results['descriptor_reference_proposal' if use_object_reference else 'candidate_path_gap'] = {
            'outcome': outcome,
            'foreign_tracked_after': (foreign/'kept.txt').read_text(),
            'foreign_scratch_preserved': (foreign/'scratch.txt').exists(),
            'original_tracked_after': (moved/'kept.txt').read_text()}
    finally:
        if fd is not None:
            os.close(fd)
        case.tearDown()

case = Case()
case.setUp()
try:
    case.abandoned()
    answer = case.restore()
    op = answer['operation_id']
    record = case.store.operation_record(op)
    result = json.loads(record['result'])
    signed = json.loads(record['signature'])
    result['runtime_id'] = 'foreign-runtime'
    signed['operands']['runtime_id'] = 'foreign-runtime'
    case.store._connection.execute('UPDATE operations SET result = ?, signature = ? WHERE operation_id = ?',
        (json.dumps(result), manager_signature(signed['kind'],signed['operands']),op))
    read = cycles.abandoned_correction_of(case.store,attempt_id=case.abandoned_attempt,generation=2)
    replay = case.restore()
    results['foreign_runtime_receipt'] = {'original_runtime': answer['runtime_id'],
        'reader_runtime': read['runtime_id'], 'replay_runtime': replay['runtime_id']}
finally:
    case.tearDown()

Path(__file__).with_suffix('.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
suite=unittest.TestSuite([Case('test_an_in_flight_duplicate_cannot_reach_a_second_effect'),
    Case('test_an_unfinished_retry_re_proves_its_provenance_first'),
    Case('test_a_transient_profile_failure_stays_retryable'),
    Case('test_the_reader_still_follows_its_owners_after_a_later_round')])
result=unittest.TextTestRunner().run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
