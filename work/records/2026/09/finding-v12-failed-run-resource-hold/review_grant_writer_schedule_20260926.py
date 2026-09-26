"""Independent W257624 schedule evidence; controlled disposable stores only.

The delayed entry is a valid schedule after the author's initial barrier.
Its failure demonstrates a test assumption, not duplicate product admission.
The other cases force the claimed post-proof overlap and exercise cached-root
access revalidation. Run only the three locally defined methods below.
"""
import os
import threading
import unittest
from unittest import mock

import test_grant_writer_admission as author
from baton_v12.worker_manager import assignment_of


class ScheduleProbe(author.GrantWriterAdmission):
    def test_valid_delayed_entry_breaks_author_race_expectation(self):
        original = author.grant_writer
        finished = threading.Event()

        def ordered(store, **operands):
            if operands['attempt_id'] == 'race-b':
                if not finished.wait(5):
                    raise AssertionError('first admission did not finish')
                return original(store, **operands)
            try:
                return original(store, **operands)
            finally:
                finished.set()

        with mock.patch.object(author, 'grant_writer', ordered):
            self.test_one_line_admits_exactly_one_of_two_competing_writers()

    def test_both_proofs_finish_before_either_transaction(self):
        original = author.review_cycles._proved_line_object
        proved = threading.Barrier(2, timeout=5)
        observed = []

        def together(store, line):
            pin = original(store, line)
            observed.append(store._connection.in_transaction)
            proved.wait()
            return pin

        with mock.patch.object(author.review_cycles, '_proved_line_object', together):
            self.test_one_line_admits_exactly_one_of_two_competing_writers()
        self.assertEqual(observed, [False, False])

    def test_cached_writer_roots_recheck_access_before_use(self):
        line = self.line()
        writer = self.granted(line['line_id'], 1)
        author.workspaces.assignment_workspace(
            self.group, self.storage, 'writer-attempt-1')
        roots = author.review_cycles.writer_boundary(
            self.store, writer_id=writer['writer_id'], generation=1)['roots']
        assignment = assignment_of(self.store, 'writer-attempt-1')
        gid = author.workspaces.configured_workspace_group(self.store).gid
        os.chmod(line['path'], 0o700)
        with self.assertRaises(author.ContractRefusal) as caught:
            author.workspaces._prove_execution_workspace(roots, gid, assignment)
        self.assertIn('admission does not repair it', caught.exception.message)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(ScheduleProbe(name) for name in (
        'test_valid_delayed_entry_breaks_author_race_expectation',
        'test_both_proofs_finish_before_either_transaction',
        'test_cached_writer_roots_recheck_access_before_use'))
