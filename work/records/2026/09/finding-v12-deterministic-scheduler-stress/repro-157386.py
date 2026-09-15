"""Independent four-Job owner checks and retained export validation."""
import json,pathlib
from tests.tools import scheduler_trace as oracle
from tests.tools import test_scheduler_trace as cases
from baton_v12.authority import Authority
from baton_v12.worker_manager.offers import claimed_offers_for
from baton_v12.job_manager.submission import stage_rows

record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-157344-composed.json').read_text())['schedules']
artifact=next(one['artifact'] for one in exports if 'four-jobs' in one['name'])
assert oracle.validate(artifact)==[]
performed=[one for one in artifact['records'] if one['outcome']=='performed']
for job in ('job-a','job-c','job-d'):
    for act in ('reserve','offer','accept','claim','start'):
        assert any(one['job_id']==job and one['act']==act for one in performed), (job,act)
assert not any(one['job_id']=='job-b' for one in performed)
assert not any(one['act']=='complete' for one in performed)
principals={one['participant']:one['principal'] for one in artifact['scenario']['workers']}
assert {one.split('.')[0] for one in principals}=={'baton','other'}, principals
print(json.dumps({'retained_records':[(one['job_id'],one['act']) for one in performed], 'principals':principals, 'gaps':artifact['gaps']},indent=2),flush=True)

case=cases.TheComposedOwnersSupplyAuthorizedTransitions('test_four_jobs_two_teams_claim_three_producers_at_once')
try:
    case.setUp()
    held=case.four_job_deployment(own_workers=True,ticks=7)
    owners=[]
    authority=Authority.open_readonly(case.case.authority_path,expected_authority_uuid=case.case.config['authority_uuid'])
    try:
        for job in ('job-a','job-c','job-d'):
            attempt=case.attempt_of(held,job+'/implementation')
            claims=claimed_offers_for(held.control,attempt)
            assert len(claims)==1, (job,claims)
            owners.append({'job_id':job,'attempt_id':attempt,'claimed_offers':claims})
        for job,actors in case.FOUR_ACTORS.items():
            assert authority.principal_of(actors['producer'])=='principal:'+actors['producer']
            assert authority.holds_capability(actors['reviewer'],'review',scope=case.case.scope)
    finally:
        authority.dispose()
    stages=stage_rows(held.job)
    assert sorted(row['job_id'] for row in stages if row['kind']=='integration')==list(case.FOUR)
    print(json.dumps({'live_owners':owners,'integration_stages':[row for row in stages if row['kind']=='integration']},indent=2,default=str),flush=True)
finally:
    case.doCleanups()
