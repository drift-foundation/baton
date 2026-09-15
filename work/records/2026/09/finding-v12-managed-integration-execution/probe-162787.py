"""Independent contract review; permissive observations are defects, not acceptance."""
import copy
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import managed_execution as managed
from baton_v12.job_manager import execution_limits
from tests.integration import test_managed_execution as contracts


class BoundaryObservations(unittest.TestCase):
    def task(self, limits):
        return contracts.TheTaskSaysWhatWasAskedFor().task(execution_limits=limits)

    def test_real_owner_generations_and_requests_are_accepted(self):
        for generation in (0, 1):
            for requested in ({}, {"verification_command_seconds": 17}):
                limits = execution_limits.resolved(requested, generation)
                self.assertEqual(self.task(limits)["execution_limits"], limits)

    def test_prior_report_bypass_is_closed(self):
        task = self.task(execution_limits.resolved({}))
        report = managed.collected_report(task, kind="measured", status=0,
            completed=[{"name": n, "status": 0} for n in task["commands"]])
        result = managed.managed_result(task, report)
        for changes in (dict(kind="unknown-kind"), dict(status=True),
                        dict(completed=[{"name": "undeclared-command", "status": True}], not_run=[]),
                        dict(kind="not-collected", status=0)):
            with self.subTest(changes=changes):
                forged = copy.deepcopy(result)
                forged["report"].update(changes)
                with self.assertRaises(ContractRefusal):
                    managed.adopt_managed_result(task, forged)

    def test_forged_preserved_defaults_are_still_accepted(self):
        for generation in (0, 1):
            original = execution_limits.resolved({}, generation)
            for changes in ({"seconds": 7200}, {"default_seconds": 7200},
                            {"seconds": 7200, "default_seconds": 7200}):
                with self.subTest(generation=generation, changes=changes):
                    forged = copy.deepcopy(original)
                    forged["boundaries"]["provider_turn"].update(changes)
                    self.assertEqual(self.task(forged)["execution_limits"], forged)
                    self.assertNotEqual(forged, original)
                    print("DEFECT OBSERVED: accepts generation", generation,
                          "provider_turn changes", changes, "against frozen default 3600")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(contracts), tests])


if __name__ == "__main__":
    unittest.main(verbosity=2)
