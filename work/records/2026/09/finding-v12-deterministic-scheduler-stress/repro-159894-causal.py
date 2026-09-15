"""Independent second-integration deferral readout; deterministic providers only."""
import json
from tests.tools import test_scheduler_trace as T
from tools import stage_execution
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = T.TheComposedOwnersSupplyAuthorizedTransitions('test_the_alternate_schedule_reaches_the_same_completions')
case.setUp()
original_observe = stage_execution._CausalObserver.observe
def inspect_observation(owner, basis):
    answer = original_observe(owner, basis)
    print('CAUSAL-ANSWER', json.dumps(answer, sort_keys=True, default=str))
    return answer
stage_execution._CausalObserver.observe = inspect_observation
original = case.b_and_terminal
def inspect_next(held, trace):
    original(held, trace)
    case.case.engine.stopped = False
    original_launch = held.composed.launch
    def observed_launch(stage, job):
        answer = original_launch(stage, job)
        if stage.get('kind') == 'integration':
            print('INTEGRATION-ANSWER', stage['stage_id'], json.dumps(answer, sort_keys=True, default=str))
        return answer
    held.composed.launch = observed_launch
    for tick in range(4):
        report = sweep(held.job, held.composed, now=fixtures.NOW)
        print('SWEEP', tick, json.dumps(report, sort_keys=True, default=str))
        print('STATES', json.dumps({one: case.case.states_for(held.job, held.composed, one) for one in case.FOUR}, sort_keys=True))
case.b_and_terminal = inspect_next
try:
    case.test_the_alternate_schedule_reaches_the_same_completions()
finally:
    stage_execution._CausalObserver.observe = original_observe
    case.doCleanups()
