"""Independent missing edges of preparation ownership; no live engine."""
import unittest
from tests.manager.test_maintenance import MaintenanceCase, IMAGE
from baton_v12.worker_manager import workspaces, custody
from baton_v12.contracts import ContractRefusal

class PreparationMatrix(MaintenanceCase):
    def test_allocation_first_excludes_preparation(self):
        workspaces._admitted_allocation(self.store, 'attempt-1', 'existing allocator')
        with self.assertRaises(ContractRefusal):
            workspaces.admit_preparation(self.store, 'attempt-1', 'competing preparation')

    def test_preparation_first_excludes_custody(self):
        workspaces.admit_preparation(self.store, 'attempt-1', 'preparing inputs')
        with self.assertRaises(ContractRefusal):
            custody._claim_episode(self.store, 'attempt-1', 'workspace', 'normalize', IMAGE,
                custody._custody_identity(self.storage, 'attempt-1', 'workspace', 'normalize'))

    def test_unfinished_preparation_is_not_blindly_adopted(self):
        workspaces.admit_preparation(self.store, 'attempt-1', 'first writer still running')
        with self.assertRaises(ContractRefusal):
            workspaces.admit_preparation(self.store, 'attempt-1', 'second execution no cessation evidence')

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PreparationMatrix))
    raise SystemExit(not result.wasSuccessful())
