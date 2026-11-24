import sys,os,json,unittest,subprocess,signal,time
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
class Timing(cases.TheReviewersRequiredVerificationIsSupervisedAndBounded):
 def test_copy_time_reduces_remaining_command_allowance(self):
  clock=[0.0]; real_copy=self.module.shutil.copytree; real_popen=subprocess.Popen; timeouts=[]
  def copy(*a,**kw):
   result=real_copy(*a,**kw);clock[0]+=10;return result
  def popen(*a,**kw):
   child=real_popen(*a,**kw); wait=child.wait
   def watched(timeout=None):
    if timeout is not None:timeouts.append(timeout)
    return wait(timeout=timeout)
   child.wait=watched;return child
  with patch.object(self.module.shutil,'copytree',side_effect=copy),patch.object(self.module.time,'monotonic',side_effect=lambda:clock[0]),patch.object(self.module.subprocess,'Popen',side_effect=popen):
   seen=self.checked('pass',invocation=1)
  print('COPY_DEADLINE',json.dumps({'elapsed_copy':10,'invocation':1,'timeouts':timeouts,'record':seen}))
  self.assertNotEqual(seen['outcome'],'passed','check launched after invocation elapsed during copy')
 def test_detached_descendant_is_not_proved_gone_by_group_gone(self):
  marker=Path(self.root)/'escaped.pid';ready=Path(self.root)/'escaped.ready'
  childcode=f'import os,time;open({str(ready)!r},"w").write(str(os.getpid()));time.sleep(60)'
  program=f'import subprocess,sys,time,pathlib\nc=subprocess.Popen([sys.executable,"-c",{childcode!r}],start_new_session=True)\npathlib.Path({str(marker)!r}).write_text(str(c.pid))\nwhile not pathlib.Path({str(ready)!r}).exists(): time.sleep(0.01)\n'
  try:
   seen=self.checked(program,command=2);pid=int(marker.read_text());os.kill(pid,0)
   print('DETACHED_DESCENDANT',json.dumps({'alive':True,'record':seen}))
   self.assertFalse(seen['outcome']=='passed' and seen['group_gone'] is True,'empty group does not prove all verification descendants ended')
  finally:
   if marker.exists():
    try:os.kill(int(marker.read_text()),signal.SIGKILL)
    except ProcessLookupError:pass
class Replay(cases.TheConnectedRecoveryFromARealPooledProducer):
 def test_removal_success_can_replay(self):
  original=self.removed
  def twice(selector,job,stage,reason):
   first=original(selector,job,stage,reason)
   print('FIRST_REMOVAL',json.dumps(first,default=str))
   second=original(selector,job,stage,reason)
   self.assertTrue(second['removed']);return first
  self.removed=twice
  self.test_a_stopped_original_is_held_then_removed_recovered_and_reviewed()
if __name__=='__main__':
 suite=unittest.TestSuite([Timing('test_copy_time_reduces_remaining_command_allowance'),Timing('test_detached_descendant_is_not_proved_gone_by_group_gone'),Replay('test_removal_success_can_replay')])
 result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
