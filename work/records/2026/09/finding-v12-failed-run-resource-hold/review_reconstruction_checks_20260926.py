"""Focused behavioral revalidation of reconstruction a7760cd9.

Uses existing deterministic custody/replay assertions and counts entry to the
three helpers omitted from the author's coverage selector. No tracing or product
mutation. Also revalidates the reconstructed grant and atomic restoration.
"""
from contextlib import ExitStack
import json
import unittest
from unittest import mock

from baton_v12.worker_manager import review_cycles


def main():
    names = [
        'tests.job_manager.test_review_driver.TheWorkerCompletionTraversesPublicCustody',
        'test_grant_writer_admission',
        'review_grant_writer_schedule_20260926.ScheduleProbe.test_both_proofs_finish_before_either_transaction',
        'review_grant_writer_schedule_20260926.ScheduleProbe.test_cached_writer_roots_recheck_access_before_use',
        'test_restore_outside_the_lock',
        'review_restore_atomic_admission_20260926',
    ]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    with ExitStack() as stack:
        observed = {name: stack.enter_context(mock.patch.object(
            review_cycles, name, wraps=getattr(review_cycles, name)))
            for name in ('_custodied_review', '_cleaned_review', '_committed_act')}
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        counts = {name: wrapped.call_count for name, wrapped in observed.items()}
    print(json.dumps({'helper_calls': counts, 'tests': result.testsRun,
                      'success': result.wasSuccessful()}, sort_keys=True))
    return 0 if result.wasSuccessful() and all(counts.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
