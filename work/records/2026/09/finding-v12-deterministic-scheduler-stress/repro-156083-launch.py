"""Read the actual integration-owner answer underneath the sweep summary."""
import json
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases

case = Cases("test_both_jobs_traverse_and_one_integrator_serializes_them")
case.setUp()
try:
    coding = case.case.coding
    observed = set()
    def recording(*args, **kwargs):
        held = coding(*args, **kwargs)
        launch = held.composed.launch
        def launched(stage, job):
            answer = launch(stage, job)
            if stage["stage_id"] == "job-b/integration":
                value = json.dumps(answer, sort_keys=True, default=str)
                if value not in observed:
                    print(value, flush=True)
                    observed.add(value)
            return answer
        held.composed.launch = launched
        return held
    case.case.coding = recording
    case.test_both_jobs_traverse_and_one_integrator_serializes_them()
finally:
    case.doCleanups()
