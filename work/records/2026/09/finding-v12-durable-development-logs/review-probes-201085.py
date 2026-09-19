"""Synthetic local capture/restart probes; no provider, engine or store."""
import os,sys,tempfile,json,time,pathlib
from unittest.mock import patch
sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src','/home/sl/src/baton/v12/python/src/baton_v12']
import claude_agent as a
import attempt_log_format as f
from baton_v12.worker_manager import attempt_logs
start=time.monotonic()
root=pathlib.Path(tempfile.mkdtemp(prefix='w198667-review201085-'))
results={}
for initial in ['finished','partial','failed','truncated',None]:
 parent=root/str(initial);parent.mkdir()
 delivery=attempt_logs.AttemptLogs(root=str(parent),attempt_id='attempt-probe')
 pathlib.Path(delivery.log_root).mkdir()
 fd=f.open_room(delivery.log_root)
 first=a._Captured(fd,f,'provider.stdout');first.wrote(b'first-prefix');first.declare(initial)
 before=attempt_logs.follow(delivery,'provider.stdout')
 second=a._Captured(fd,f,'provider.stdout');second.wrote(b'second-whole')
 during=attempt_logs.follow(delivery,'provider.stdout')
 second.declare('finished')
 after=attempt_logs.follow(delivery,'provider.stdout')
 os.close(fd)
 results[str(initial)]={phase:{key:doc.get(key) for key in ['state','more_may_arrive','text','why']} for phase,doc in [('before',before),('during',during),('after',after)]}
parent=root/'real-short-write';parent.mkdir()
delivery=attempt_logs.AttemptLogs(root=str(parent),attempt_id='attempt-probe')
pathlib.Path(delivery.log_root).mkdir()
fd=f.open_room(delivery.log_root)
first=a._Captured(fd,f,'provider.stdout')
with patch.object(f,'write_all',side_effect=lambda handle,payload: os.write(handle,payload[:5])):
 first.wrote(b'first-MISSING-TAIL')
first.declare('finished')
before=attempt_logs.follow(delivery,'provider.stdout')
second=a._Captured(fd,f,'provider.stdout');second.wrote(b'second-whole');second.declare('finished')
after=attempt_logs.follow(delivery,'provider.stdout');os.close(fd)
results['actual_lost_write_then_success']={'before':before,'after':after,'lost_tail_not_restored':True}
results['seconds']=time.monotonic()-start;results['scratch']=str(root)
print(json.dumps(results,indent=2))
(root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
