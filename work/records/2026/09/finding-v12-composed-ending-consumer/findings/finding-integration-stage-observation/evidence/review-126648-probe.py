"""Independent public-status probes for OBSERVATION.md revision1."""
import json
from pathlib import Path

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
            answers[name] = case.projected("completed", runtime=case.runtime("destroyed"), completion=case.completion())
        elif name == "completed_after_uncertain_refresh":
            answers[name] = case.projected("completed", runtime=case.runtime("uncertain"), completion=case.completion())
        else:
            answers[name] = case.projected("held", output={"disposition": "completed"})
    finally:
        case.doCleanups()
Path(__file__).with_suffix(".json").write_text(json.dumps(answers, indent=2) + "\n")
print(json.dumps(answers))
