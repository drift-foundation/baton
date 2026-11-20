import json, time, sys
from pathlib import Path
from tests.tools.test_connected_creation import CreateTimeWorkLabelsThroughTheRealCommand as Case
start=time.monotonic(); results=[]
for job_id in ['job-short', 'j'*130, 'job/segment']:
 for labelled in [False,True]:
  case=Case();case.setUp()
  try:
   case.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1')
   argv=case.labelled(*(['v12'] if labelled else []),job_id=job_id)
   try:
    answer=case.made(argv); refusal=None
   except Exception as exc:
    refusal=type(exc).__name__+': '+str(exc)
   authority=case.authority()
   results.append({'job_id':job_id,'labelled':labelled,'refusal':refusal,'work_creation':authority.work_creation(case.work),'rows':[dict(x) for x in case.rows()[1].created_job_rows(case.rows()[0])]})
  finally:case.doCleanups()
output={'seconds':time.monotonic()-start,'cases':results}
Path(sys.argv[1]).write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'seconds':output['seconds'],'cases':[{'job_length':len(x['job_id']),'job_prefix':x['job_id'][:12],'labelled':x['labelled'],'work_minted':x['work_creation'] is not None,'refusal':x['refusal']} for x in results]},indent=2))
