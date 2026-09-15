"""Inspect retained continuation evidence without regenerating schedules."""
import json,pathlib
from collections import Counter
from tests.tools import scheduler_trace
record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-159520-composed.json').read_text())['schedules']
assert len(exports)==18
by_name={one['name']:one['artifact'] for one in exports}
for name,artifact in by_name.items():
    assert scheduler_trace.validate(artifact)==[],name
    assert not [one for one in artifact['records'] if one['act']=='submit'],name
continued=by_name['four-jobs-continued-to-integration']
done=Counter(one['stage_id'] for one in continued['records'] if one['act']=='complete')
expected={f'job-{job}/{kind}' for job in 'abcd' for kind in ('implementation','review')}
assert set(done)==expected,done
assert set(done.values())=={1},done
assert max(one['tick'] for one in continued['records']) <= 100
alternate=by_name['four-jobs-c-before-a']
alt_done=Counter(one['stage_id'] for one in alternate['records'] if one['act']=='complete')
assert 'job-b/implementation' not in alt_done and 'job-b/review' not in alt_done
print(json.dumps({'validated_exports':len(exports),'continued_completions':done,
    'alternate_completions':alt_done,'max_continued_tick':max(one['tick'] for one in continued['records']),
    'integration_completions':0},indent=2))
