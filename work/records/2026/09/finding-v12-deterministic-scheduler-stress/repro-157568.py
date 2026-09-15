"""Read retained current traces; distinguish executed acts from policy prose."""
import json,pathlib
from tests.tools import scheduler_trace
record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-157538-composed.json').read_text())['schedules']
for exported in exports:
    if exported['name'] not in ('four-jobs-a-before-c','four-jobs-c-before-a','four-jobs-continued-to-integration'):
        continue
    artifact=exported['artifact']
    assert scheduler_trace.validate(artifact)==[]
    performed=[one for one in artifact['records'] if one['outcome']=='performed']
    completed=[one['stage_id'] for one in performed if one['act']=='complete']
    assert all(job+'/'+kind in completed for job in ('job-a','job-c','job-d') for kind in ('implementation','review'))
    print(json.dumps({'schedule':exported['name'],'complete':completed,
        'submissions':[one for one in performed if one['act']=='submit'],
        'integration_starts':[one for one in performed if one['act']=='start' and (one.get('stage_id') or '').endswith('/integration')],
        'gaps':artifact['gaps']},indent=2),flush=True)
