"""Independent mutations of current retained authorization artifact; no owner writes."""
import copy,json
from pathlib import Path
from tests.tools.scheduler_trace import validate
raw=json.loads((Path(__file__).parent/'trace-154323-composed.json').read_text())
original=next(x['artifact'] for x in raw['schedules'] if x['name']=='composed-authorization-receipts')
answers={}
for name in ('original','foreign_scope','missing_generation','wrong_role','missing_reference','foreign_scope_without_reference'):
    a=copy.deepcopy(original)
    r=next(r for r in a['records'] if r['act']=='review')
    if name.startswith('foreign_scope'):r['authorization']['effective_scope']='scope:elsewhere'
    if name=='missing_generation':r['authorization']['policy_generation']=None
    if name=='wrong_role':r['authorization']['role']='integrate'
    if name in ('missing_reference','foreign_scope_without_reference'):a.pop('authorization_references',None)
    answers[name]=validate(a)
print(json.dumps(answers,indent=2))
assert answers['original']==[]
assert answers['foreign_scope'] and answers['missing_generation'] and answers['wrong_role']
