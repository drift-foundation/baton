import sys,json,time
from pathlib import Path
root=Path.cwd()
sys.path[:0]=[str(root/'v12/python'),str(root/'v12/python/src')]
from tests.job_manager.test_role_capability import TheOwnedDataBoundaryIsComplete
from baton_v12.job_manager import role_capability
from baton_v12 import source_profiles
f=TheOwnedDataBoundaryIsComplete(); results={}; start=time.monotonic()
for name,base in [('valid','0'*40),('missing_base',None)]:
    installed=f.installed_task(declared_base=base)
    lanes={r:f.candidate(r,installed_task=installed) for r in ['implementation','review']}
    try:
        admitted=role_capability.admissible_roles(f.contract(),candidates=lanes)
    except Exception as e:
        admitted={'exception':type(e).__name__,'message':str(e)}
    task=json.loads(lanes['implementation']['task_document'])
    try:
        source_profiles.checkout_plan('/synthetic/source','/synthetic/workspace',profile=task['source_profile'],declared=task['declared_base'])
        owner='accepted'
    except Exception as e:
        owner={'exception':type(e).__name__,'message':str(e)}
    results[name]={'profile':task['source_profile'],'declared_base':base,'admission':admitted,'source_profile_owner':owner}
print(json.dumps({'seconds':time.monotonic()-start,'results':results},indent=2))
