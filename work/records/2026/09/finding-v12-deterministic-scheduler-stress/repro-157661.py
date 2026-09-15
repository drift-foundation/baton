"""Read the retained export independently; do not regenerate the scenarios."""
import json,pathlib
from tests.tools import scheduler_trace
record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-157605-composed.json').read_text())['schedules']
assert len(exports)==18
for exported in exports:
    artifact=exported['artifact']
    violations=scheduler_trace.validate(artifact)
    assert violations==[], (exported['name'],violations)
    submitted=[one for one in artifact['records'] if one['act']=='submit']
    assert submitted==[], (exported['name'],submitted)
    if exported['name'] not in ('four-jobs-a-before-c','four-jobs-c-before-a','four-jobs-continued-to-integration'):
        continue
    performed=[one for one in artifact['records'] if one['outcome']=='performed']
    completed=[one['stage_id'] for one in performed if one['act']=='complete']
    assert all(job+'/'+kind in completed for job in ('job-a','job-c','job-d') for kind in ('implementation','review'))
    print(json.dumps({'schedule':exported['name'],'complete':completed,
        'submissions':submitted,'integration_starts':[one for one in performed if one['act']=='start' and (one.get('stage_id') or '').endswith('/integration')],
        'gaps':artifact['gaps']},indent=2),flush=True)
print(json.dumps({'retained_schedules_validated':len(exports),'submit_records':0}))
