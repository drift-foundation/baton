"""Independent acceptance-oracle mutations of retained owner-produced artifact."""
import copy,json,hashlib
from pathlib import Path
from tests.tools.scheduler_trace import validate
p=Path(__file__).parent
source=p/'trace-154200-composed.json'
held=json.loads(source.read_text())
original=next(x['artifact'] for x in held['schedules'] if x['name']=='composed-accepted-review')
answers={"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"original":validate(original),"synthetic_mutations":{}}
for name in ('deleted_acceptance','acceptance_after_claim'):
    artifact=copy.deepcopy(original)
    target=next(r for r in artifact['records'] if r['act']=='accept')
    if name=='deleted_acceptance': artifact['records'].remove(target)
    else: target['recorded_at']='2026-09-02T00:00:01.000Z'
    answers['synthetic_mutations'][name]=validate(artifact)
print(json.dumps(answers,indent=2))
assert answers['original']==[]
assert any(x['code']=='missing-prerequisite' for x in answers['synthetic_mutations']['deleted_acceptance'])
assert any(x['code']=='out-of-order' for x in answers['synthetic_mutations']['acceptance_after_claim'])
