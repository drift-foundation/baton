import json,os,time
from pathlib import Path
from tests.tools.test_job_task_delivery import ObservationReproducesTheDeliveredIdentity as Case
start=time.monotonic();c=Case('test_the_observation_adopts_the_materialized_launch');c.setUp()
try:
 h=c.running('review-strengthened');ob=c.observing(h);stage=h['stage'];path=Path(c.config['launch_home'])/h['attempt']/'launch.json'
 original=path.read_bytes();mode=path.stat().st_mode & 0o7777
 before=[h[x]._connection.total_changes for x in ('job','control')]
 good=ob.observe_exchange(stage)
 assert good is not None and good['state']!='unreadable',good
 assert before==[h[x]._connection.total_changes for x in ('job','control')]
 assert path.read_bytes()==original
 doc=json.loads(original);doc['role']='review';os.chmod(path,0o644);path.write_bytes(json.dumps(doc,sort_keys=True,separators=(',',':')).encode());os.chmod(path,mode)
 bad=ob.observe_exchange(stage)
 assert bad is not None and bad['state']=='unreadable',bad
 assert bad['unreadable']=={'category':'policy','code':'denied'},bad
 print(json.dumps({'valid_exchange':good['state'],'read_calls_changed_no_job_or_control_rows':True,'valid_read_preserved_launch':True,'tampered_mode_restored':oct(mode),'tampered_exchange':bad,'seconds':time.monotonic()-start,'limits':'existing deterministic serving harness and task-reader substitution; no live engine/provider or real template admission'},indent=2))
finally:c.doCleanups()
