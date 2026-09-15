"""Review terminal readback and the existing public receipt-export seam."""
import json
from unittest.mock import patch
from tests.tools import test_scheduler_trace as T
from tests.tools import scheduler_trace
from baton_v12.worker_manager import review_cycles

case = T.TheComposedOwnersSupplyAuthorizedTransitions('test_the_opened_edge_and_one_integrator_serialize_four_jobs')
case.setUp()
helds, traces = [], []
original_deployment = case.four_job_deployment
original_artifact = scheduler_trace.Trace.artifact
def deployment(**kwargs):
    held = original_deployment(**kwargs)
    helds.append(held)
    return held
def artifact(trace, *args, **kwargs):
    answer = original_artifact(trace, *args, **kwargs)
    if answer['scenario']['name'] == 'four-jobs-continued-to-integration':
        traces.append(trace)
    return answer
case.four_job_deployment = deployment
try:
    with patch.object(scheduler_trace.Trace, 'artifact', artifact):
        case.test_the_opened_edge_and_one_integrator_serialize_four_jobs()
    held, trace = helds[0], traces[-1]
    before = trace.artifact(T.SOURCES)
    assert not [r for r in before['records'] if r['act'] == 'complete' and r['stage_id'].endswith('/integration')]
    states = {job: case.case.states_for(held.job, held.composed, job) for job in case.FOUR}
    completed = [job for job in case.FOUR if states[job]['integration'] == 'completed']
    assert completed == ['job-a'], states
    trace._tick += 1
    case.observed(held, trace, trace._tick, case.FOUR, trace.__dict__.setdefault('_seen', set()))
    without_receipts = scheduler_trace.validate(trace.artifact(T.SOURCES))
    assert 'unauthorized-integration' in str(without_receipts), without_receipts
    owner = case.case.deployment_of(held.composed)
    line = owner.line_for('job-a')['line_id']
    checkpoint = review_cycles.integration_checkpoint(held.control, line)
    proposal = owner.published_proposal(checkpoint)
    receipts = case.proposal_receipts(held, trace, 'job-a', proposal, trace._tick)
    after = scheduler_trace.validate(trace.artifact(T.SOURCES))
    assert after == [], after
    print(json.dumps({'states': states, 'original_export_integration_completions': 0,
                      'observed_without_receipts': without_receipts,
                      'receipt_kinds': sorted(receipts), 'after_public_receipts': after,
                      'qualification': 'Independent final-state observation and receipt readback; omitted intervening ticks remain omitted.'}, indent=2))
finally:
    case.doCleanups()
