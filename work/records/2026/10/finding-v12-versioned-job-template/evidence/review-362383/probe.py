import copy,json
from unittest.mock import patch
from baton_v12.job_manager import templates,execution_limits
from baton_v12.contracts import ContractRefusal
from tests.job_manager.test_templates import request,configuration
r=templates.resolve(request(),configuration=configuration())
results={}
for field,value in [('template',None),('task',{}),('scope',{}),('stages',[None]),('stages',[{'kind':'implementation'}]),('acceptance',None),('overrides',{'execution_limits':None})]:
    bad=copy.deepcopy(r);bad[field]=value
    try:
        templates.submission_for_admission(bad);out={'accepted':True}
    except Exception as e:
        out={'type':type(e).__name__,'typed_refusal':isinstance(e,ContractRefusal),'message':str(e)}
    results[field+':'+json.dumps(value)]=out
new=dict(execution_limits.GENERATIONS[1]);new['provider_turn']=7200
with patch.dict(execution_limits.GENERATIONS,{2:new}),patch.object(execution_limits,'CURRENT_GENERATION',2):
    try: templates.submission_for_admission(r);results['stale_limit']='accepted'
    except ContractRefusal: results['stale_limit']='refused'
try: templates.template_of(templates.IMPLEMENTATION_REVIEW)['completion']['delivers']='wrong'
except TypeError: results['lookup_mutation']='refused'
results['scope']=r['scope'];results['submission_test_scope']=r['submission']['jobs'][0]['test_scope']
print(json.dumps(results,indent=2))
