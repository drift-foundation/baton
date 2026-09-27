"""Focused deterministic reviewer probes; no live engine."""
import unittest
from unittest.mock import patch
from tests.manager.test_maintenance import MaintenanceCase, Engine, IMAGE
from baton_v12.worker_manager import custody, tokens
from baton_v12.contracts import ContractRefusal

class Admission(MaintenanceCase):
    def test_custody_hold_winning_before_token_admission_prevents_effect(self):
        honest = custody._reconciled
        reached = []
        def racing(*args, **kwargs):
            answer = honest(*args, **kwargs)
            name = custody._custody_identity(self.storage, 'attempt-1', 'workspace', 'normalize')
            reached.append(custody._claim_episode(self.store, 'attempt-1', 'workspace', 'normalize', IMAGE, name))
            return answer
        with patch.object(custody, '_reconciled', racing):
            try:
                self.prepared()
            except ContractRefusal:
                pass
        self.assertEqual(len(reached), 1)
        self.assertIsNotNone(custody._standing_overlap(self.store, 'attempt-1', 'workspace'))
        self.assertEqual(self.engine.ran, 0, 'maintenance wrote despite newly committed conflicting custody hold')

    def test_expiry_during_create_reconciles_the_created_container(self):
        class Delayed(Engine):
            def creating(engine, argv):
                answer = super().creating(argv)
                engine.case.instant = '2026-09-27T00:16:00.000Z'
                return answer
        engine = Delayed(self)
        with self.assertRaises(ContractRefusal):
            self.prepared(engine)
        self.assertIsNotNone(engine.created)
        self.assertEqual(engine.ran, 0)
        self.assertTrue(any(argv[1] in ('stop', 'rm') for argv, _ in engine.seen),
                        'exact created runtime was abandoned on expired binding refusal')

    def test_expiry_after_start_enforces_shutdown_before_leaving_hold(self):
        class Slow(Engine):
            def starting(engine, argv):
                answer = super().starting(argv)
                engine.case.instant = '2026-09-27T00:16:00.000Z'
                return answer
        engine = Slow(self)
        with self.assertRaises(ContractRefusal):
            self.prepared(engine)
        self.assertEqual(engine.ran, 1)
        self.assertTrue(any(argv[1] == 'stop' for argv, _ in engine.seen),
                        'expired started maintenance was never asked to stop')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Admission)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
