import json,time
from pathlib import Path
from tests.job_manager.test_serving_renewal import ServingPermission
from baton_v12.worker_manager import tokens
start=time.monotonic();case=ServingPermission();case.setUp()
try:
 case.clock.seconds=120;token=case.acquire();rows=[]
 for second in (901,1800,3600,3720,4740,4800):
  case.clock.seconds=second;report=case.lane.tick()
  rows.append({'envelope_elapsed_seconds':second,'engine_state':case.engine.state,'token':case.current(token),'report':report})
 result={'simulation':'controlled clock and fake external engine; real token/preparation/enforcement owners','acquired':token,'job_context':case.context,'observations':rows}
finally:case.doCleanups()
result['seconds']=time.monotonic()-start
Path('/tmp/baton-serving-envelope-347778/evidence/effective-policy.json').write_text(json.dumps(result,indent=2)+'\n')
print('seconds',result['seconds'])
