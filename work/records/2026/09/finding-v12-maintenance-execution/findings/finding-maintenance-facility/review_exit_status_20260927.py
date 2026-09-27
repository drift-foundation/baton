"""A successful engine wait command can report a failed container."""
import unittest
from tests.manager.test_maintenance import MaintenanceCase, Engine
from baton_v12.worker_manager import maintenance

class ContainerExit(MaintenanceCase):
    def test_nonzero_container_exit_is_not_successful_preparation(self):
        class FailedContainer(Engine):
            def __call__(engine, argv, *, seconds=None):
                answer = super().__call__(argv, seconds=seconds)
                if argv[1] == 'wait':
                    answer['stdout'] = '17\n'
                return answer
        answer = self.prepared(FailedContainer(self))
        self.assertFalse(answer.ok, 'container exit17 accepted because docker wait/logs exited0')
        receipt = maintenance.maintenance_settlement(self.store, 'attempt-1', 'workspace')
        self.assertTrue(receipt is None or receipt.get('disposition') != maintenance.SETTLED_PREPARED)

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(ContainerExit)).wasSuccessful())
