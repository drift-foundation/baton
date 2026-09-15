"""Bounded public-sweep diagnosis of the four-Job review settlement gap."""
import json
from tests.tools import test_scheduler_trace as cases
from baton_v12.job_manager import sweep
from baton_v12.job_manager.projection import stage_states
from tests.job_manager import fixtures

case=cases.TheComposedOwnersSupplyAuthorizedTransitions('test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens')
try:
    case.setUp()
    held=case.four_job_deployment(own_workers=True,ticks=7)
    trace=case.blank()
    case.four_job_schedule(trace,held,order=('job-a','job-c','job-d'))
    for tick in range(4):
        report=sweep(held.job,held.composed,now=fixtures.NOW)
        print(json.dumps({'extra_tick':tick+1,'report':report},default=str),flush=True)
    states=stage_states(held.job,held.composed)
    print(json.dumps({'fixture_policy':case.case.fixture_policy,
        'current_policy':case.case.deployment_of(held.composed).authority.policy_generation(),
        'reviews':{key:value for key,value in states.items() if key.endswith('/review')}},default=str),flush=True)
finally:
    case.doCleanups()
