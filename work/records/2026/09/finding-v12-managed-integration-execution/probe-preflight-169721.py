"""Historical review diagnostic: exit zero confirms late validation, not acceptance."""
import sys
import unittest

from tests.tools import test_managed_preparation, test_stage_execution
from tools import stage_execution


class StaticPreflightDiagnostic(unittest.TestCase):
    def test_invalid_selection_survives_static_configuration(self):
        fixture = test_stage_execution.StageCase()
        try:
            fixture.setUp()
            for value in ("false", "true", 1, 0, "", None, "yes"):
                with self.subTest(value=value):
                    held = fixture.held(integration_preparation=value)
                    self.assertEqual(held["integration_preparation"], value)
                    self.assertIs(type(held["integration_preparation"]), type(value))
                    with self.assertRaises(stage_execution.ContractRefusal):
                        stage_execution._prepares(held)
                    print(f"OBSERVED static preflight accepted {value!r}; constructor selection rejects it", flush=True)
        finally:
            fixture.doCleanups()


suite = unittest.TestSuite()
for name in (
    "test_an_unselected_deployment_composes_no_preparation",
    "test_a_selection_this_build_cannot_place_refuses",
    "test_a_selected_deployment_with_no_integrator_refuses",
    "test_a_refusal_while_constructing_releases_what_it_built",
):
    suite.addTest(test_managed_preparation.TheResolverCallsItsOwnersCorrectly(name))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(StaticPreflightDiagnostic))
sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
