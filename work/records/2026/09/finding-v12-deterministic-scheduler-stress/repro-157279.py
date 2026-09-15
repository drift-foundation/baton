"""Independent retained R6d mutations and bounded four-Job continuation."""
import copy,json,pathlib
from tests.tools import scheduler_trace as oracle
from tests.tools import test_scheduler_trace as cases
from baton_v12.job_manager import sweep, episodes, receipts_of
from tests.job_manager import fixtures

record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-157211-composed.json').read_text())['schedules']
original=next(item['artifact'] for item in exports if item['name']=='composed-both-jobs-imported')
assert oracle.validate(original)==[]
for name in ('foreign-source','published-owner-result'):
    changed=copy.deepcopy(original)
    if name=='foreign-source':
        row=next(one for one in changed['records'] if one['act']=='complete' and one['stage_id']=='job-b/integration')
        row['completion']['source_proposal_id']='proposal-of-another-job'
    else:
        next(iter(changed['result_references'].values()))['state']='published'
    violations=oracle.validate(changed)
    assert violations, name
    print(json.dumps({'case':name,'violations':violations}),flush=True)

artifact=next(item['artifact'] for item in exports if 'four-jobs' in item['name'])
print(json.dumps({'four_job_artifact_keys':list(artifact),'scenario':artifact['scenario'],
                  'performed':[(one['job_id'],one['act']) for one in artifact['records'] if one['outcome']=='performed'],
                  'violations':oracle.validate(artifact)},indent=2),flush=True)

case=cases.TheComposedOwnersSupplyAuthorizedTransitions('test_four_jobs_on_two_repositories_code_in_parallel')
try:
    case.setUp()
    held=case.four_job_deployment(own_workers=True)
    reports=[]
    for tick in range(4):
        reports.append(sweep(held.job,held.composed,now=fixtures.NOW))
    from baton_v12.job_manager.submission import stage_rows
    observed=[]
    for stage in stage_rows(held.job):
        if stage['job_id'] not in ('job-c','job-d') or stage['kind']!='implementation':
            continue
        live=episodes.live_of(held.job,stage['stage_id'])
        observed.append({'stage':stage,'live':live,'receipts':receipts_of(held.job,stage['stage_id'],live['episode'])})
    print(json.dumps({'continued_ticks':4,'last_report':reports[-1],'extra_job_owners':observed},indent=2,default=str),flush=True)
finally:
    case.doCleanups()
