import sys,os,json,unittest,tempfile,signal
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd().parent/'worker'))
import bounded_command as b
class Late(unittest.TestCase):
 def test_child_exits_only_after_the_absolute_deadline(self):
  clock=[0.0];real=os.waitpid;once=[True]
  handlers={n:signal.getsignal(n) for n in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   release=Path(d)/'release'
   def wait(pid,flags):
    if pid>0 and once[0]:
     once[0]=False;clock[0]=2.0;release.write_text('released after bound');return real(pid,0)
    return real(pid,flags)
   child=f'import pathlib,time\np=pathlib.Path({str(release)!r})\nwhile not p.exists(): time.sleep(0.001)\n'
   try:
    with patch.object(b.time,'monotonic',side_effect=lambda:clock[0]),patch.object(b.os,'waitpid',side_effect=wait):
     status=b.supervise([sys.executable,'-c',child],label='check',seconds=1,deadline=1,ledger=d)
    record=next(iter(b.account(d).values()));print(json.dumps({'exit':status,'record':record,'release_at':2,'deadline':1}))
    self.assertEqual(status,b.TIMED_OUT)
   finally:
    for n,h in handlers.items():signal.signal(n,h)
if __name__=='__main__':unittest.main(verbosity=2)
