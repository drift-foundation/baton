import json
import unittest
from tests.tools import test_joined_workflow as suite

original_ports = suite.JoinedWorkflowCase.creation_ports
original_judged = suite.JoinedWorkflowCase.judged

def ports(self, *args, **kwargs):
    answer = original_ports(self, *args, **kwargs)
    print("CREATION_PORTS", json.dumps({k: type(v).__module__ + "." + type(v).__name__ for k, v in answer.items()}), flush=True)
    return answer

def judged(self, held, verdict):
    answer = original_judged(self, held, verdict)
    stage = self.stage_of(held["jobs"], held["composed"], self.job_id)
    rows = self.rows(held, "SELECT runtime_attempt_id, execution_runtime FROM attempts")
    print("BEFORE_CORRECTION_TIMER", json.dumps({"stage_state": stage["state"], "second_attempt": stage["attempt_id"], "runtimes": rows}), flush=True)
    return answer

suite.JoinedWorkflowCase.creation_ports = ports
suite.JoinedWorkflowCase.judged = judged
names = ["test_the_routine_start_is_within_the_obs0_bound", "test_the_correction_rounds_start_is_within_the_bound_too"]
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite.TheRoutineStartupInterval(n) for n in names))
raise SystemExit(not result.wasSuccessful())
