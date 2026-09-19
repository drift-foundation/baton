"""Synthetic capture persistence probes; no deployment or provider access."""
import sys,os,json,pathlib,tempfile,time
from unittest.mock import patch
sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src','/home/sl/src/baton/v12/python/src/baton_v12']
import claude_agent as a
import attempt_log_format as f
from baton_v12.worker_manager import attempt_logs
start=time.monotonic();root=pathlib.Path(tempfile.mkdtemp(prefix='w198667-review201212-'));results={}
def setup(name):
 parent=root/name;parent.mkdir();d=attempt_logs.AttemptLogs(root=str(parent),attempt_id='attempt-probe');pathlib.Path(d.log_root).mkdir();return d,f.open_room(d.log_root)
def writer(fd,data,state):
 c=a._Captured(fd,f,'provider.stdout');c.wrote(data);c.declare(state)
def read(d):
 found=attempt_logs.follow(d,'provider.stdout');return {key:found[key] for key in ['state','text','more_may_arrive','why']}
for state in ['finished','failed','partial','truncated',None]:
 d,fd=setup(str(state));writer(fd,b'first-prefix',state);writer(fd,b'second-whole','finished');results[str(state)]=read(d);os.close(fd)
d,fd=setup('persist-failure');writer(fd,b'first-prefix','failed')
with patch.object(f,'_write_carried',return_value=False):
 second=a._Captured(fd,f,'provider.stdout');second.wrote(b'second-prefix');second.declare(None)
results['failed_persistence_before_third']={'declaration':f.read_declaration(fd,'provider.stdout'),'carried':f.read_carried(fd,'provider.stdout')}
writer(fd,b'third-whole','finished');results['failed_persistence_after_third']=read(d);os.close(fd)
d,fd=setup('unreadable-carry');writer(fd,b'first-prefix','failed')
second=a._Captured(fd,f,'provider.stdout');second.wrote(b'second-prefix');second.declare(None)
real_open=f.os.open
def unreadable(path,*args,**kwargs):
 if path==f.carried_name('provider.stdout'):raise PermissionError('injected cumulative-record read denial')
 return real_open(path,*args,**kwargs)
with patch.object(f.os,'open',side_effect=unreadable):writer(fd,b'third-whole','finished')
results['unreadable_carry_after_third']=read(d);os.close(fd)
results['seconds']=time.monotonic()-start;results['scratch']=str(root)
(root/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
