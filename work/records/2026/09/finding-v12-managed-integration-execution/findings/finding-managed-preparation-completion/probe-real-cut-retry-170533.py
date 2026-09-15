"""Retry the ordinary sweep after the unexpected publication-before-intent fault."""
import unittest
from unittest import mock
from tools import integration_worker
from baton_v12 import job_manager
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes

class RealInterruption(OneManagedPreparationCompletes):
    def test_unexpected_pre_intent_interruption_recovers(self):
        original = integration_worker.PreparationExecution.decide
        tick = job_manager.sweep
        cuts = []; caught = []
        def interrupted(*args, **kwargs):
            if not cuts:
                cuts.append('publication-before-intent')
                raise RuntimeError('independent unexpected pre-intent interruption')
            return original(*args, **kwargs)
        def retryable_tick(*args, **kwargs):
            try:
                return tick(*args, **kwargs)
            except RuntimeError as error:
                if str(error) != 'independent unexpected pre-intent interruption':
                    raise
                caught.append(str(error))
                return {'interruption': str(error)}
        with mock.patch.object(integration_worker.PreparationExecution, 'decide', interrupted), mock.patch.object(job_manager, 'sweep', retryable_tick):
            self.complete()
        self.assertEqual(cuts, ['publication-before-intent'])
        self.assertEqual(len(caught), 1)

if __name__ == '__main__':
    suite = unittest.TestSuite([RealInterruption('test_unexpected_pre_intent_interruption_recovers')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
