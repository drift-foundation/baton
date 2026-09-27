"""Real ordinary staging interleaved with removal admission; fake engine only."""
import unittest
from unittest import mock
from tests.tools.test_single_worker import SingleWorkerCase, Engine, submit
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal

class StagingExclusion(SingleWorkerCase):
    def test_removal_cannot_enter_during_input_publication(self):
        engine = Engine()
        job, control = self.stores('staging-exclusion')
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        original = workspaces.compose_input_root
        observed = []
        def paused(*args, **kwargs):
            attempt = kwargs['runtime_attempt_id']
            try:
                workspaces._admitted_removal(control, attempt, 'review competing with input publication')
            except ContractRefusal:
                observed.append('refused')
            else:
                observed.append('admitted')
            return original(*args, **kwargs)
        with mock.patch.object(workspaces, 'compose_input_root', side_effect=paused):
            try:
                self.commanded(job, operations)
            except AssertionError:
                if observed != ['admitted']:
                    raise
        self.assertEqual(observed, ['refused'], 'removal acquired ownership while ordinary host staging could still write')

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        StagingExclusion('test_removal_cannot_enter_during_input_publication')]))
    raise SystemExit(not result.wasSuccessful())
