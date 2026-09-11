"""Positive reconstruction of a real Job-B integration admission."""
import json
from tests.tools.test_stage_execution import EveryJobRoleIsValidatedBeforeAllocation, SECOND_WORK
from baton_v12.job_manager import scheduler

f = EveryJobRoleIsValidatedBeforeAllocation('runTest')
try:
    f.setUp()
    jobs, control, first = f.serving_two()
    f.offered(jobs, [f.standalone('job-b', 'integration', SECOND_WORK)])
    assert f.admitting(jobs, first, 'job-b/integration') is None
    stage = f.attempted(jobs, 'job-b/integration')
    before = scheduler.allocation_of(jobs, stage['attempt_id'])
    receipt = f.receipted(jobs, first, 'job-b/integration')
    first.close()
    second = f.recomposed(jobs, control)
    refusal = f.admitting(jobs, second, 'job-b/integration')
    print(json.dumps({'admit_refusal': None if refusal is None else
                     {'category': refusal.category, 'code': refusal.code,
                      'message': refusal.message}}))
    assert scheduler.allocation_of(jobs, stage['attempt_id']) == before
    assert f.receipted(jobs, second, 'job-b/integration') == receipt
    print(json.dumps({'same_allocation': True, 'same_receipt': True,
                      'worker': before['worker_id'], 'work': stage['work_id']}))
finally:
    f.doCleanups()
