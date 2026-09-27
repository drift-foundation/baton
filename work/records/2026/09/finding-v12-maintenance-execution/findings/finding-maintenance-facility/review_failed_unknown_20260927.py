"""Known failed exit does not establish the state of partially changed resources."""
import unittest
from tests.manager.test_maintenance import MaintenanceCase, Engine
from baton_v12.worker_manager import maintenance, tokens

class FailedUnknown(MaintenanceCase):
    def test_failed_exit_with_lost_effect_account_keeps_resource_held(self):
        class Failed(Engine):
            def starting(engine, argv):
                result = super().starting(argv)
                engine.stdout = 'unreadable result\n'
                return result
            def __call__(engine, argv, *, seconds=None):
                result = super().__call__(argv, seconds=seconds)
                if argv[1] == 'wait':
                    result['stdout'] = '17\n'
                return result
        answer = self.prepared(Failed(self))
        self.assertFalse(answer.ok)
        self.assertEqual(self.engine.ran, 1)
        self.assertFalse(answer.returned, 'known exit but unknown effects released the resource')
        self.assertTrue(tokens.outstanding(self.store, self.domain()))
        self.assertTrue(maintenance.standing_maintenance(self.store, 'attempt-1', 'workspace'))

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(FailedUnknown)).wasSuccessful())
