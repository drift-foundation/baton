"""Review the reported line-materialization blocker using existing fixtures."""
import json
import os
import sys
import unittest

from baton_v12.checkpoint_profiles import ProfileRefusal
from baton_v12.job_manager import submit, sweep
from tests.job_manager import fixtures
from tests.tools import test_managed_preparation, test_stage_execution


class FixtureBoundary(unittest.TestCase):
    def fixture(self, kind):
        case = kind()
        self.addCleanup(case.doCleanups)
        case.setUp()
        return case

    def test_plain_source_fixture_reproduces_the_reported_refusal(self):
        case = self.fixture(test_stage_execution.ServingCase)
        self.assertTrue(os.path.isdir(case.source))
        self.assertFalse(os.path.exists(os.path.join(case.source, ".git")))
        document = case.composed_document(integration_preparation=True)
        self.assertEqual(document["checkpoint_profile"], "git")
        self.assertEqual(document["line_declared_base"], "a" * 40)
        self.assertEqual(json.loads(case.task_bytes)["source_profile"], "generic")
        jobs, control, composed = case.serving(integration_preparation=True)
        submit(jobs, case.submission)
        with self.assertRaises(ProfileRefusal) as caught:
            sweep(jobs, composed, now=fixtures.NOW)
        self.assertIn("line materialization", str(caught.exception))
        print("OBSERVED existing plain directory + generic workload + Git checkpoint: " + str(caught.exception), flush=True)

    def test_existing_git_fixture_passes_that_boundary_with_selection_enabled(self):
        case = self.fixture(test_stage_execution.ComposedOneJobCase)
        self.assertTrue(os.path.isdir(os.path.join(case.source, ".git")))
        jobs, control, composed = case.serving(integration_preparation=True)
        self.assertIsNotNone(composed.deployment._integration_operations._preparation)
        submit(jobs, case.submission)
        states = case.drive(jobs, composed, "implementation", "waiting")
        self.assertEqual(states["implementation"], "waiting")
        self.assertEqual(len([one for one in case.engine.starts if "--entrypoint" not in one]), 1)
        print("OBSERVED existing Git-backed fixture with managed selection: " + repr(states) + "; one simulated worker start; no worker workload executed", flush=True)


suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_managed_preparation.ASelectedDeploymentComposesTheManagedPath))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(FixtureBoundary))
sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
