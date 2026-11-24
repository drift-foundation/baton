import sys,os,json,unittest,subprocess,signal,time,importlib.util,tempfile
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src'),str(root.parent/'worker')]
from tests.job_manager import test_publication_recovery_execution as cases
import bounded_command
class Corrected(cases.TheReviewersRequiredVerificationIsSupervisedAndBounded):
 def test_detached_child_is_absent_after_pass(self):
  marker=Path(self.root)/'escaped.pid';ready=Path(self.root)/'escaped.ready'
  childcode=f'import os,time;open({str(ready)!r},"w").write(str(os.getpid()));time.sleep(60)'
  program=f'import subprocess,sys,time,pathlib\nc=subprocess.Popen([sys.executable,"-c",{childcode!r}],start_new_session=True)\npathlib.Path({str(marker)!r}).write_text(str(c.pid))\nwhile not pathlib.Path({str(ready)!r}).exists(): time.sleep(0.01)\n'
  try:
   seen=self.checked(program,command=2);pid=int(marker.read_text())
   self.assertEqual(seen['outcome'],'passed');self.assertIs(seen['descendants_gone'],True)
   with self.assertRaises(ProcessLookupError):os.kill(pid,0)
   print('DETACHED_CORRECTED',json.dumps(seen))
  finally:
   if marker.exists():
    try:os.kill(int(marker.read_text()),signal.SIGKILL)
    except ProcessLookupError:pass
 def test_copy_crossing_remaining_deadline_runs_nothing(self):
  clock=[time.monotonic()];real=self.module.shutil.copytree
  def copy(*a,**kw):
   result=real(*a,**kw);clock[0]+=60;return result
  marker=Path(self.root)/'should-not-run'
  with patch.object(self.module.shutil,'copytree',side_effect=copy),patch.object(self.module.time,'monotonic',side_effect=lambda:clock[0]):
   seen=self.checked(f'open({str(marker)!r},"w")',invocation=30)
  self.assertEqual(seen['outcome'],'not-run');self.assertFalse(marker.exists());print('COPY_CORRECTED',json.dumps(seen))
class Deadline(unittest.TestCase):
 def test_completion_observed_after_deadline_does_not_report_success(self):
  # Actual child/wait; controlled clock crosses absolute bound at completion observation.
  clock=[0.0];wait=os.waitpid;first=[True]
  def waited(pid,flags):
   if pid>0 and first[0]:
    first[0]=False;answer=wait(pid,0);clock[0]=2.0;return answer
   return wait(pid,flags)
  old={n:signal.getsignal(n) for n in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as ledger:
   try:
    with patch.object(bounded_command.time,'monotonic',side_effect=lambda:clock[0]),patch.object(bounded_command.os,'waitpid',side_effect=waited):
     status=bounded_command.supervise([sys.executable,'-c','pass'],label='check',seconds=1,deadline=1.0,ledger=ledger)
    record=next(iter(bounded_command.account(ledger).values()));print('LATE_COMPLETION',json.dumps({'exit':status,'record':record}))
    self.assertNotEqual(status,0,'completion observed after absolute bound was recorded as success')
   finally:
    for n,h in old.items():signal.signal(n,h)
class Removal(cases.TheConnectedRecoveryFromARealPooledProducer):
 def test_removal_exact_replay_remains_eligible(self):
  real=self.removed
  def twice(selector,job,stage,reason):
   one=real(selector,job,stage,reason);two=real(selector,job,stage,reason)
   self.assertTrue(one['removed']);self.assertTrue(two['removed']);self.assertTrue(two['replayed']);return one
  self.removed=twice;self.test_a_stopped_original_is_held_then_removed_recovered_and_reviewed()
if __name__=='__main__':
 suite=unittest.TestSuite([Corrected('test_detached_child_is_absent_after_pass'),Corrected('test_copy_crossing_remaining_deadline_runs_nothing'),Deadline('test_completion_observed_after_deadline_does_not_report_success'),Removal('test_removal_exact_replay_remains_eligible')]);result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
