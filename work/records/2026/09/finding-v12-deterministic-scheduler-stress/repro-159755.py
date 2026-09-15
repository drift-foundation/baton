"""Independent second-integration deferral readout; deterministic providers only."""
import json
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = T.TheComposedOwnersSupplyAuthorizedTransitions('test_the_opened_edge_and_one_integrator_serialize_four_jobs')
case.setUp()
original = case.b_and_terminal
def inspect_next(held, trace):
    original(held, trace)
    case.case.engine.stopped = False
    for tick in range(4):
        report = sweep(held.job, held.composed, now=fixtures.NOW)
        print('SWEEP', tick, json.dumps(report, sort_keys=True, default=str))
        print('STATES', json.dumps({one: case.case.states_for(held.job, held.composed, one) for one in case.FOUR}, sort_keys=True))
case.b_and_terminal = inspect_next
try:
    case.test_the_opened_edge_and_one_integrator_serialize_four_jobs()
finally:
    case.doCleanups()
