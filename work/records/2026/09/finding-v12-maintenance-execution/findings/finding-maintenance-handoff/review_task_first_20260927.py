"""Task-token acquisition wins first; conflicting removal must refuse."""
import unittest
from unittest import mock
from tests.tools.test_single_worker import SingleWorkerCase, Engine, submit
from baton_v12.worker_manager import tokens, workspaces
from baton_v12.contracts import ContractRefusal

class TaskFirst(SingleWorkerCase):
    def test_removal_refuses_after_task_acquisition(self):
        engine = Engine()
        job, control = self.stores('task-first')
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        original = tokens.acquire
        observed = []
        def acquired(asking, domain, **named):
            token = original(asking, domain, **named)
            if not observed:
                try:
                    workspaces._admitted_removal(control, named['attempt'], 'competing after task acquisition')
                except ContractRefusal:
                    observed.append('refused')
                else:
                    observed.append('admitted')
            return token
        with mock.patch.object(tokens, 'acquire', side_effect=acquired):
            self.commanded(job, operations)
        self.assertEqual(observed, ['refused'], 'removal admitted after task token acquisition')

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([TaskFirst('test_removal_refuses_after_task_acquisition')]))
    raise SystemExit(not result.wasSuccessful())
