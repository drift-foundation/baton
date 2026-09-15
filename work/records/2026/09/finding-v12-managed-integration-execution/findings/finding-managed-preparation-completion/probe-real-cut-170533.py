"""Independent fault with the scheduler's actual recovery-required transition."""
import unittest
from unittest import mock
from tools import integration_worker
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes

class RealInterruption(OneManagedPreparationCompletes):
    def test_unexpected_pre_intent_interruption_recovers(self):
        original = integration_worker.PreparationExecution.decide
        cuts = []
        def interrupted(*args, **kwargs):
            if not cuts:
                cuts.append('publication-before-intent')
                raise RuntimeError('independent unexpected pre-intent interruption')
            return original(*args, **kwargs)
        with mock.patch.object(integration_worker.PreparationExecution, 'decide', interrupted):
            self.complete()
        self.assertEqual(cuts, ['publication-before-intent'])

if __name__ == '__main__':
    suite = unittest.TestSuite([RealInterruption('test_unexpected_pre_intent_interruption_recovers')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
