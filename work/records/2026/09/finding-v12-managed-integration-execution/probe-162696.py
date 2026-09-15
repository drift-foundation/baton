"""New-contract boundary research; permissive observations are defects."""
import copy
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import managed_execution as managed
from baton_v12.job_manager.execution_limits import resolved
from tests.integration import test_managed_execution as contracts
from tests.job_manager import test_managed_integration_capacity as capacity


class BoundaryObservations(unittest.TestCase):
    def task(self, **changed):
        return contracts.TheTaskSaysWhatWasAskedFor().task(**changed)

    def test_real_resolved_job_limits_are_rejected(self):
        limits = resolved({})
        with self.assertRaises(ContractRefusal):
            self.task(execution_limits=limits)
        print("DEFECT OBSERVED: actual resolved Job limits rejected by managed_task")

    def test_invented_empty_limits_and_unknown_generation_are_accepted(self):
        task = self.task(execution_limits={"effective": {}, "generation": 999})
        self.assertEqual(task["execution_limits"], {"effective": {}, "generation": 999})
        print("DEFECT OBSERVED: empty effective limits and unknown compatibility generation accepted")

    def test_untrusted_result_adoption_bypasses_report_validation(self):
        task = self.task()
        report = managed.collected_report(
            task, kind="measured", completed=[{"name": name, "status": 0}
                                               for name in task["commands"]], status=0)
        result = managed.managed_result(task, report)
        variants = [dict(kind="unknown-kind"), dict(status=True),
                    dict(completed=[{"name": "undeclared-command", "status": True}], not_run=[]),
                    dict(kind="not-collected", status=0)]
        for changes in variants:
            with self.subTest(changes=changes):
                forged = copy.deepcopy(result)
                forged["report"].update(changes)
                adopted = managed.adopt_managed_result(task, forged)
                self.assertEqual(adopted["report"], forged["report"])
        print("DEFECT OBSERVED: adoption accepts invalid report kinds, boolean status and undeclared command accounting")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(capacity),
                               loader.loadTestsFromModule(contracts), tests])


if __name__ == "__main__":
    unittest.main(verbosity=2)
