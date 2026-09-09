"""Verify the three reviewed boundaries and focused provider controls."""
import json
from pathlib import Path
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import submit
from tests.job_manager.fixtures import job, stage, submission
from tests.job_manager.test_status import AnIntegrationStageIsProjectedFromItsOwnObservation

answers = {}
for name in ("non_integration_completion", "completed_after_uncertain_refresh", "held_with_frozen_output"):
    case = AnIntegrationStageIsProjectedFromItsOwnObservation("test_completed_is_completed")
    try:
        case.setUp()
        if name == "non_integration_completion":
            case.STAGE = "job-a/implementation"
            case.submitted = lambda: submit(case.jobs, submission(jobs=[job("job-a", stages=[stage("implementation")])]))
            try:
                case.projected("completed", runtime=case.runtime("destroyed"), completion=case.completion())
            except ContractRefusal as refused:
                answers[name] = [refused.category, refused.code]
            else:
                raise AssertionError("integration evidence completed an implementation stage")
            assert answers[name] == ["refused", "operation-collision"]
        elif name == "completed_after_uncertain_refresh":
            answers[name] = case.projected("completed", runtime=case.runtime("uncertain"), completion=case.completion())
            assert answers[name] == "completed"
        else:
            answers[name] = case.projected("held", output={"disposition": "completed"})
            assert answers[name] == "exceptional"
    finally:
        case.doCleanups()

selectors = [
    "tests.job_manager.test_delegation.TheIntegrationObservationIsBoundBeforeItIsRead",
    "tests.job_manager.test_status.AnIntegrationStageIsProjectedFromItsOwnObservation",
    "tests.job_manager.test_exchange.AnIntegrationStageOwesConcludeAndNeverDispatch",
    "tests.job_manager.test_tool.TheStatusSurfaceMayReadIntegrationAndStillActOnNothing",
]
suite = unittest.defaultTestLoader.loadTestsFromNames(selectors)
result = unittest.TextTestRunner(verbosity=1).run(suite)
answers["selectors"] = selectors
answers["tests_run"] = result.testsRun
answers["success"] = result.wasSuccessful()
Path(__file__).with_suffix(".json").write_text(json.dumps(answers, indent=2) + "\n")
print(json.dumps(answers))
raise SystemExit(0 if result.wasSuccessful() else 1)
