import sys,os,pathlib,tempfile,json,subprocess,time
sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src','/home/sl/src/baton/v12/python/src/baton_v12']
import claude_agent as a
import attempt_log_format as f
from baton_v12.worker_manager import attempt_logs
root=pathlib.Path(tempfile.mkdtemp(prefix='w198667-review200927-'));results={};t=time.monotonic()
p=root/'fifo';p.mkdir();os.mkfifo(p/'provider.stdout.log')
code="import sys,os;sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src/baton_v12'];import claude_agent as a,attempt_log_format as f;fd=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY);a._Captured(fd,f,'provider.stdout')"
try:
 r=subprocess.run([sys.executable,'-c',code,str(p)],timeout=2,capture_output=True,text=True);results['fifo']={'returncode':r.returncode,'stderr':r.stderr}
except subprocess.TimeoutExpired:results['fifo']={'timed_out_seconds':2,'child':'killed and reaped by subprocess.run'}
p=root/'alias';p.mkdir();outside=root/'sibling.log';outside.write_bytes(b'');os.link(outside,p/'provider.stdout.log');fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
c=a._Captured(fd,f,'provider.stdout');c.wrote(b'raw provider bytes');c.declare('finished');os.close(fd);results['alias']={'outside':outside.read_text()}
p=root/'restart';p.mkdir();fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
c=a._Captured(fd,f,'provider.stdout');c.wrote(b'first');c.declare('finished')
c=a._Captured(fd,f,'provider.stdout');c.wrote(b'second')
results['restart']={'declaration_while_second_writer_is_open':f.read_declaration(fd,'provider.stdout'),'raw':(p/'provider.stdout.log').read_text()}
c.declare(None);os.close(fd)
results['restart']['declaration_after_unfinished_capture']=json.loads((p/'provider.stdout.status.json').read_text())
results['seconds']=time.monotonic()-t;results['root']=str(root)
(root/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
