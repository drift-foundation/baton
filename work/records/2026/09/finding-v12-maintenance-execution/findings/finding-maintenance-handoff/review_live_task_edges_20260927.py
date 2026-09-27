"""Remaining task-first admissions on the composed ordinary path; fake engine."""
import unittest
from tests.tools.test_single_worker import SingleWorkerCase, Engine, submit
from baton_v12.worker_manager import workspaces, custody
from baton_v12.contracts import ContractRefusal

class LiveTaskEdges(SingleWorkerCase):
    def running(self, label):
        engine = Engine()
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        self.addCleanup(operations.close)
        state = self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        return control, state['jobs'][0]['stages'][0]['attempt_id']

    def test_live_task_excludes_custody_writer(self):
        control, attempt = self.running('live-task-custody')
        with self.assertRaises(ContractRefusal):
            custody._claim_episode(control, attempt, 'workspace', 'normalize', 'sha256:'+'c'*64,
                custody._custody_identity(self.storage, attempt, 'workspace', 'normalize'))

    def test_live_task_excludes_mutating_allocation_admission(self):
        control, attempt = self.running('live-task-allocation')
        with self.assertRaises(ContractRefusal):
            workspaces._admitted_allocation(control, attempt, 'new mutating allocation alongside live task')

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveTaskEdges))
    raise SystemExit(not result.wasSuccessful())
