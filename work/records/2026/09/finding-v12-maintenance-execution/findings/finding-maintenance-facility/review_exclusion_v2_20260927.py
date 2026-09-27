"""Deterministic exclusion schedules; no live engine or product mutation."""
import unittest
from unittest.mock import patch
from tests.manager.test_maintenance import MaintenanceCase, Engine, IMAGE
from baton_v12.worker_manager import custody, workspaces, maintenance
from baton_v12.contracts import ContractRefusal

class Exclusion(MaintenanceCase):
    def test_interposed_custody_claim_is_refused_before_effect(self):
        honest = custody._reconciled
        reached = []
        def racing(*args, **kwargs):
            answer = honest(*args, **kwargs)
            reached.append(True)
            custody._claim_episode(self.store, 'attempt-1', 'workspace', 'normalize', IMAGE,
                custody._custody_identity(self.storage, 'attempt-1', 'workspace', 'normalize'))
            return answer
        with patch.object(custody, '_reconciled', racing):
            with self.assertRaises(ContractRefusal):
                self.prepared()
        self.assertEqual(reached, [True])
        self.assertEqual(self.engine.ran, 0)
        self.assertIsNone(custody._standing_overlap(self.store, 'attempt-1', 'workspace'))

    def test_live_maintenance_excludes_workspace_entry(self):
        case = self
        refused = []
        class Concurrent(Engine):
            def starting(engine, argv):
                case.assertTrue(maintenance.standing_maintenance(case.store, 'attempt-1', 'workspace'))
                try:
                    workspaces.refuse_if_held(case.store, case.storage, 'attempt-1', 'review allocation')
                except ContractRefusal:
                    refused.append(True)
                return super().starting(argv)
        self.prepared(Concurrent(self))
        self.assertEqual(refused, [True], "conflicting entry admitted while maintenance active")

    def test_live_maintenance_excludes_removal_admission(self):
        case = self
        refused = []
        class Concurrent(Engine):
            def starting(engine, argv):
                case.assertTrue(maintenance.standing_maintenance(case.store, 'attempt-1', 'workspace'))
                try:
                    workspaces._admitted_removal(case.store, 'attempt-1', 'review removal')
                except ContractRefusal:
                    refused.append(True)
                return super().starting(argv)
        self.prepared(Concurrent(self))
        self.assertEqual(refused, [True], "conflicting entry admitted while maintenance active")

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(Exclusion)).wasSuccessful())
