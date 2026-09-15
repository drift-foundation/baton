"""Read-only artifact audit, no scenario execution or generated receipts."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from tests.tools import scheduler_trace

record = Path(__file__).resolve().parent
path = record / 'trace-160959-composed.json'
assert hashlib.sha256(path.read_bytes()).hexdigest() == '5a3ead46c46b5586cbd3a74d7454b402fd04dfbe34414e33a061ac9e90fb9303'
bundle = json.loads(path.read_text())
assert len(bundle['schedules']) == len({s['name'] for s in bundle['schedules']}) == 18
summary = []
for s in bundle['schedules']:
    a = s['artifact']
    errors = scheduler_trace.validate(a)
    assert not errors, (s['name'], errors)
    summary.append(dict(name=s['name'], records=len(a['records']), max_tick=max((r['tick'] for r in a['records']), default=0), acts=dict(Counter(r['act'] for r in a['records'])), completions=[r['stage_id'] for r in a['records'] if r['act']=='complete' and r['outcome']=='performed'], sessions=sorted({r['session_id'] for r in a['records'] if r['session_id']}), gaps=a['gaps'], note=a['scenario'].get('note'), source_manifest=a.get('source_manifest'), environment=a.get('environment')))
fresh = {}
for order in ['a_before_c', 'c_before_a']:
    a = json.loads((record / f'review-161114-{order}.json').read_text())
    fresh[order] = dict(sha256=hashlib.sha256((record / f'review-161114-{order}.json').read_bytes()).hexdigest(), scenario=a['scenario'], acts=dict(Counter(r['act'] for r in a['records'])), corrections=[r for r in a['records'] if r['act']=='correct'], imports=[r for r in a['records'] if r['act']=='integrate'], causal=json.loads((record / f'review-161114-{order}-causal.json').read_text()))
answer = dict(export_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), schedules=summary, fresh=fresh)
out = record / 'audit-161114.json'
assert not out.exists()
out.write_text(json.dumps(answer, indent=2, default=str)+'\n')
print(json.dumps(summary, indent=2))
print(json.dumps({'fresh': {k: {'acts': v['acts'], 'corrections': len(v['corrections']), 'imports': len(v['imports']), 'causal_answers':len(v['causal'])} for k,v in fresh.items()}}, indent=2))
