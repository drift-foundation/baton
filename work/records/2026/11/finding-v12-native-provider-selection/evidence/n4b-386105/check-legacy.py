"""Compare exact pre-change and candidate Claude attribution bytes, source only."""
import json,subprocess,sys,hashlib
from pathlib import Path
repo=Path('/home/sl/src/baton/work/scratch/n4b-386105')
sys.path.insert(0,str(repo/'v12/python/src'))
from baton_v12.provider_policy import attribution
old=subprocess.check_output(['git','show','HEAD:v12/python/src/baton_v12/provider_policy/attribution.py'],cwd=repo)
ns={'__package__':'baton_v12.provider_policy'};exec(compile(old,'baseline-attribution.py','exec'),ns)
d=dict(attempt_id='attempt',home_identity=dict(job_id='job'),contract=dict(selection=dict(provider='claude',requested_model='selector',reported_identity='reported',cli_build='2.1.247'),adapter=dict(participation_sources=[dict(field='modelUsage',kind='keys')])))
cases=[None,b'',b'broken',b'{"type":"result","subtype":"success","is_error":false,"modelUsage":{"reported":{},"other":{}}}',b'{"type":"result","subtype":"success","is_error":false,"modelUsage":{"other":{}}}',b'{"type":"result","subtype":"error","is_error":true,"modelUsage":{"reported":{}}}']
results=[]
for n,raw in enumerate(cases):
 for partial in (False,True):
  kw=dict(phase='implementation',evidenced_build='2.1.247',raw=raw,partial=partial)
  a=json.dumps(ns['record'](d,**kw),sort_keys=True,separators=(',',':')).encode()
  b=json.dumps(attribution.record(d,**kw),sort_keys=True,separators=(',',':')).encode()
  assert a==b
  results.append(dict(case=n,partial=partial,sha256=hashlib.sha256(b).hexdigest()))
print(json.dumps(dict(compared=len(results),byte_identical=True,cases=results),indent=2))
