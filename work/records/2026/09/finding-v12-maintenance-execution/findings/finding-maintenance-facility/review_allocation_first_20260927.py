"""Reverse-order exclusion: an admitted allocation must precede maintenance safely."""
import unittest
from tests.manager.test_maintenance import MaintenanceCase, Engine
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal

class AllocationFirst(MaintenanceCase):
    def test_allocation_admitted_first_excludes_maintenance(self):
        workspaces._admitted_allocation(self.store, 'attempt-1', 'review allocation')
        self.assertTrue(workspaces.standing_allocation(self.store, 'attempt-1'))
        engine = Engine(self)
        refused = False
        try:
            self.prepared(engine)
        except ContractRefusal:
            refused = True
        self.assertTrue(refused, f'maintenance proceeded under standing allocation; effects={engine.ran}')
        self.assertEqual(engine.ran, 0)

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(AllocationFirst)).wasSuccessful())
