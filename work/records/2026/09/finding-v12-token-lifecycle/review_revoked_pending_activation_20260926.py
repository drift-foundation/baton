"""Normalization must not precede exclusion of an admitted unresolved activation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import intake, tokens

class PendingActivation(unittest.TestCase):
    def test_unsettled_activation_holds_before_normalization(self):
        spec = importlib.util.spec_from_file_location('expiry_cases', Path(__file__).with_name('test_expiry_reclaim.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        f = module.TheRevokedResourceHasItsOwnEnding()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.addCleanup(f.tearDown)
        # Model activation admitted, submission unresolved: do not record its return.
        with patch.object(tokens.Reservation, 'settle', return_value=None):
            governance, domain = f.revoked()
        self.assertTrue(tokens.token_of(f.store, domain, 1)['activating'])
        with patch.object(intake, '_normalized', wraps=intake._normalized) as normalize:
            try:
                f.settled(governance)
            except ContractRefusal:
                pass
            self.assertEqual(normalize.call_count, 0, 'normalization began before unresolved activation was excluded')
        self.assertEqual(len(tokens.outstanding(f.store, domain)), 1)

if __name__ == '__main__':
    unittest.main()
