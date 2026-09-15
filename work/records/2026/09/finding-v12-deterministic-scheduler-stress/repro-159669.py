"""Validate retained both-order completions and receipt chains; no regeneration."""
import json,pathlib
from collections import Counter
from tests.tools import scheduler_trace
record=pathlib.Path(__file__).parent
schedules=json.loads((record/'trace-159644-composed.json').read_text())['schedules']
assert len(schedules)==18
assert len({one['name'] for one in schedules})==18
for one in schedules:
    assert scheduler_trace.validate(one['artifact'])==[],one['name']
results=[]
for name in ('four-jobs-continued-to-integration','four-jobs-c-before-a'):
    artifact=next(one['artifact'] for one in schedules if one['name']==name)
    records=artifact['records']
    completed=Counter(one['stage_id'] for one in records if one['act']=='complete')
    for job in 'abcd':
        for kind in ('implementation','review'):
            assert completed[f'job-{job}/{kind}']==1,completed
    terminal=[one for one in records if one['act']=='complete' and one['stage_id'].endswith('/integration')]
    assert len(terminal)==1
    acts={one['act'] for one in records}
    assert {'verify','review','approve','integrate'} <= acts, acts
    assert len(records)==66
    assert max(one['tick'] for one in records)<=100
    assert terminal[0]['completion']['integration_receipt_id']
    results.append({'name':name,'records':len(records),'completions':completed,
        'terminal':terminal[0]['stage_id'],'max_tick':max(one['tick'] for one in records),
        'terminal_receipt':terminal[0]['completion']['integration_receipt_id']})
print(json.dumps({'validated_unique_schedules':18,'orders':results},indent=2))
