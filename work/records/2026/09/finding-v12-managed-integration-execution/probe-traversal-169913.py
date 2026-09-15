"""Selected composition over existing deterministic worker fixtures; diagnostic only."""
import sys
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import TheComposedJobTraversesReviewAndAcceptance
from tools import integration_worker


class SelectedTraversal(TheComposedJobTraversesReviewAndAcceptance):
    def serving(self, **members):
        return super().serving(integration_preparation=True, **members)

    def runTest(self):
        held = self.reviewed()
        preparation = held.composed.deployment._integration_operations._preparation
        with mock.patch.object(integration_worker.PreparationExecution, "prepare", side_effect=AssertionError("prepare was invoked")) as called:
            with self.assertRaises(KeyError) as stopped:
                for index in range(10):
                    sweep(held.job, held.composed, now=fixtures.NOW)
            self.assertEqual(stopped.exception.args, ("accept",))
            called.assert_not_called()
        self.assertEqual(preparation.started, [])
        print(f"OBSERVED managed admission after upstream review, sweep {index}: KeyError accept BEFORE PreparationExecution.prepare invocation", flush=True)
        with self.assertRaises(ContractRefusal) as retry:
            sweep(held.job, held.composed, now=fixtures.NOW)
        print("OBSERVED next sweep: " + str(retry.exception), flush=True)


result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([SelectedTraversal()]))
sys.exit(not result.wasSuccessful())
