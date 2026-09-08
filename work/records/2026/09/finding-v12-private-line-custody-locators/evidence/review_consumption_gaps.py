"""W105982 reviewer regressions. Only disposable test stores/roots are touched.
Run from v12/python with PYTHONPATH=src:. python3 <this script>.
Assertions express the approved refusal boundaries, not today's unsafe result.
"""
import os
import tempfile
import unittest
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import review_cycles, workspaces
from tests.manager.test_review_cycles import ReviewCycles


class ConsumptionBoundaries(unittest.TestCase):
    def fixture(self):
        case = ReviewCycles('test_line_and_each_operation_replay_exactly')
        case.setUp()
        self.addCleanup(case.doCleanups)
        self.addCleanup(case.tearDown)
        line = case.line()
        writer = case.writer(line['line_id'], 1)
        case.complete('writer-attempt-1')
        return case, line, writer

    def test_symlinks_cannot_bypass_entry_ceiling(self):
        with tempfile.TemporaryDirectory(prefix='w105982-review-links-') as root:
            root = os.path.realpath(root)
            for number in range(3):
                os.symlink('missing', os.path.join(root, f'link-{number}'))
            pin = os.stat(root)
            with mock.patch.object(workspaces, 'MAX_ENTRIES', 2):
                with self.assertRaises(ContractRefusal):
                    workspaces.prove_line_consumable(root, (pin.st_dev, pin.st_ino))

    def test_changed_assignment_principal_cannot_authorize_consumption(self):
        case, line, writer = self.fixture()
        subject = review_cycles.consumption_subject(case.store, attempt_id='writer-attempt-1', generation=1)
        # Test fixture corruption, NOT a coordination store operation.
        case.store._connection.execute("UPDATE attempts SET assignment_principal = 'replacement' WHERE runtime_attempt_id = 'writer-attempt-1'")
        with self.assertRaises(ContractRefusal):
            review_cycles.consumption_subject(case.store, attempt_id='writer-attempt-1', generation=1)

    def test_checkpoint_rechecks_object_after_the_authority_fence(self):
        case, line, writer = self.fixture()
        subject = review_cycles.consumption_subject(case.store, attempt_id='writer-attempt-1', generation=1)
        workspaces.prove_line_consumable(subject['line_path'], subject['pinned'])
        port = case.port('baton.impl')
        cancel = port.cancel
        def replace_at_external_fence(*args, **kwargs):
            answer = cancel(*args, **kwargs)
            os.rename(line['path'], line['path'] + '-original')
            os.mkdir(line['path'])
            return answer
        with mock.patch.object(port, 'cancel', side_effect=replace_at_external_fence):
            with self.assertRaises(ContractRefusal):
                review_cycles.freeze_checkpoint(case.store, writer_id=writer['writer_id'], generation=1,
                                                profile=case.profile, port=port)
        self.assertEqual(case.profile.freeze_calls, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
