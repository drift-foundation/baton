import sys, json, io, time
from pathlib import Path
from unittest.mock import patch
root = Path.cwd()
sys.path[:0] = [str(root/'v12/python'), str(root/'v12/python/src'), str(root/'v12/python/src/baton_v12'), str(root/'v12/worker')]
from tests.job_manager.test_role_capability import TheOwnedDataBoundaryIsComplete
from baton_v12.job_manager import role_capability
from tools import job_task
import claude_agent
fixture = TheOwnedDataBoundaryIsComplete()
base = json.loads(fixture.candidate('implementation')['task_document'])
variants = {'valid': base, 'only_generation_and_profile': {k:base[k] for k in ('schema','source_profile')}, 'verification_string': dict(base,verification='python3 -m unittest'), 'unknown_member': dict(base,unexpected=True), 'numeric_task_id': dict(base,task_id=7)}
results = {}
start=time.monotonic()
for name, task in variants.items():
    raw=json.dumps(task,sort_keys=True,separators=(',',':')).encode()
    candidates=fixture.both()
    for lane in candidates.values():
        lane['task_document']=raw.decode()
        lane['input_manifest']=job_task.manifest_for(lane['input_manifest'],raw.decode())
    try:
        admission=role_capability.admissible_roles(fixture.contract(),candidates=candidates)
    except Exception as e:
        admission={'exception':type(e).__name__,'message':str(e)}
    try:
        with patch('builtins.open',return_value=io.BytesIO(raw)):
            claude_agent._read_task('/synthetic/task.json')
        worker='accepted'
    except Exception as e:
        worker={'exception':type(e).__name__,'message':str(e)}
    results[name]={'admission':admission,'worker_reader':worker}
print(json.dumps({'seconds':time.monotonic()-start,'results':results},indent=2))
