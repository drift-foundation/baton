"""A second execution on the same attempt while real staging remains active."""
import unittest
from unittest import mock
from tests.tools.test_single_worker import SingleWorkerCase, Engine, submit
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal

class SameAttemptReentry(SingleWorkerCase):
    def test_attempt_identity_does_not_prove_staging_writer_has_stopped(self):
        engine = Engine()
        job, control = self.stores('same-attempt-reentry')
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        original = workspaces.compose_input_root
        observed = []
        def paused(*args, **kwargs):
            attempt = kwargs['runtime_attempt_id']
            try:
                workspaces.admit_preparation(control, attempt, 'second execution while first writer paused', attempt)
            except ContractRefusal:
                observed.append('refused')
            else:
                observed.append('admitted')
            return original(*args, **kwargs)
        with mock.patch.object(workspaces, 'compose_input_root', side_effect=paused):
            self.commanded(job, operations)
        self.assertEqual(observed, ['refused'], 'same attempt identity grants a second execution while its first writer can still complete')

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        SameAttemptReentry('test_attempt_identity_does_not_prove_staging_writer_has_stopped')]))
    raise SystemExit(not result.wasSuccessful())
