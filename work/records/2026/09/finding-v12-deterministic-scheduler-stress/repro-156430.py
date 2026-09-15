"""Independent retained-artifact mutations; no owner state is edited."""
import copy
import json
from pathlib import Path
from tests.tools import scheduler_trace as oracle

original = next(s['artifact'] for s in json.loads(Path(__file__).with_name('trace-156395-composed.json').read_text())['schedules'] if s['name'] == 'composed-both-jobs-imported')
assert oracle.validate(original) == []
def check(name, change, required=False):
    artifact = copy.deepcopy(original)
    change(artifact)
    violations = oracle.validate(artifact)
    print(json.dumps({'case': name, 'violations': violations}), flush=True)
    if required:
        assert violations, name

def completion(artifact, job='job-a'):
    return next(r['completion'] for r in artifact['records'] if r['act']=='complete' and r['stage_id']==job+'/integration')
def swap(artifact):
    for r in artifact['records']:
        if r['act'] in oracle.SUBJECT_AUTHORIZATION:
            r['job_id']={'job-a':'job-b','job-b':'job-a'}[r['job_id']]
            r['stage_id']=r['job_id']+'/integration'
def drop_start(artifact):
    artifact['records']=[r for r in artifact['records'] if not (r['act']=='start' and r['stage_id']=='job-a/integration')]
check('R6a_swapped_chains', swap, True)
check('R6b_deleted_direct_start', drop_start, True)
check('foreign_direct_completion_runtime', lambda a: completion(a).update(runtime_id='runtime-of-another-attempt'), True)
check('direct_completion_claims_running_runtime', lambda a: completion(a).update(execution_runtime='running'), True)
check('foreign_reconciled_result', lambda a: completion(a, 'job-b').update(result_id='result-of-another-job'), True)
check('reconciled_without_source_proposal', lambda a: completion(a, 'job-b').update(source_proposal_id=None), True)

check('foreign_nonempty_source_proposal', lambda a: completion(a,'job-b').update(source_proposal_id='proposal-of-another-job'))
check('owner_result_still_published', lambda a: next(iter(a['result_references'].values())).update(state='published'))
print(json.dumps({'original_owner_results':original['result_references']},sort_keys=True))
