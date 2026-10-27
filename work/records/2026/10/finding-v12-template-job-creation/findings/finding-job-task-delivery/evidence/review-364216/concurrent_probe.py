"""Reuse existing multi-container engine at the candidate's normal engine seam."""
import json
from pathlib import Path
from baton_v12.job_manager.creation import job_task_of
from tests.tools.test_job_task_delivery import TwoCreatedJobsRunThroughOnePoolServingLoop
from tests.tools.test_stage_execution import _ConcurrentEngine
c=TwoCreatedJobsRunThroughOnePoolServingLoop(); c.setUp()
try:
 c.quiescing=lambda: _ConcurrentEngine()
 held=c.both()
 answer={'states':{j:c.stages(held['jobs'],held['composed'],j)['implementation'] for j in held['created']},'starts':len(c.engine.starts),'runtimes':{j:s['runtime']['runtime_id'] for j,s in held['stages'].items()}}
 deliveries={}
 for j,stage in held['stages'].items():
  raw=(Path(c.storage)/stage['attempt_id']/'inputs/task.json').read_bytes()
  assert raw==job_task_of(held['jobs'],j).encode('utf-8')
  deliveries[j]=json.loads(raw)['instructions']
 assert deliveries['job-pool-first']!=deliveries['job-pool-second']
 answer['each_published_task_matches_own_created_job']=True
 print(json.dumps(answer,indent=2))
finally: c.doCleanups()
