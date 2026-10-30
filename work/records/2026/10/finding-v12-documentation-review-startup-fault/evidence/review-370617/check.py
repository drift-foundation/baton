import copy,hashlib,json,time
from pathlib import Path
import claude_agent
started=time.monotonic()
p=Path('work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/claim-370562')
b=json.loads((p/'BINDING.json').read_text());d=json.loads((p/'DIAGNOSIS.json').read_text())
assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in b['evidence'].items())
actual=Path(d['evidence_this_rests_on']['input_json'])
assert hashlib.sha256(actual.read_bytes()).hexdigest()==d['evidence_this_rests_on']['input_json_sha256']
manifest=json.loads(actual.read_text()); declared=manifest['outputs']
assert declared==d['evidence_this_rests_on']['review_declared_outputs']
rows=[]
def check(name,value,role,want):
    try:
        produced,absent=claude_agent._selected(value,claude_agent.IMPLEMENTATION_OUTPUTS if role=='implementation' else claude_agent.REVIEW_OUTPUTS,role)
        outcome={'accepted':True,'produced':[x['name'] for x in produced],'absent':[x['name'] for x in absent]}
    except claude_agent.TaskRefusal as e:
        outcome={'accepted':False,'refusal':str(e)}
    assert outcome['accepted']==want
    rows.append(dict(case=name,role=role,**outcome))
check('retained',declared,'implementation',True)
check('retained',declared,'review',False)
shared=copy.deepcopy(declared)
for name in ['findings','logs']:
    item=copy.deepcopy(declared[0]);item.update(name=name,path=name,type='directory-result',required=False);shared.append(item)
check('union-but-proposal-required',shared,'review',False)
shared[0]['required']=False
check('proposed-optional-union',shared,'implementation',True)
check('proposed-optional-union',shared,'review',True)
print(json.dumps({'checked_evidence_files':len(b['evidence']),'retained_input_hash_matches':True,'source_sha256':hashlib.sha256(Path('v12/worker/claude_agent.py').read_bytes()).hexdigest(),'results':rows,'seconds':time.monotonic()-started,'limits':'Source selector only; no image-byte equivalence, provider, deployment correction, output validation or cleanup proof.'},indent=2))
