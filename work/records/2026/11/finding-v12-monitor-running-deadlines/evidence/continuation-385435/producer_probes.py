"""No Git, model, engine or pipeline fixture execution. Real producer methods,
recording Popen seam and real atomic exchange publication into disposable files.
"""
import sys,pathlib,tempfile,unittest,subprocess,json,datetime
from unittest import mock
ROOT=pathlib.Path('/home/sl/src/baton/work/scratch/w385427/candidate')
sys.path[:0]=[str(ROOT/'v12/worker'),str(ROOT/'v12/python/src/baton_v12')]
import claude_agent,baton_worker
class Producer(unittest.TestCase):
 def setUp(self):
  self.agent=claude_agent.ClaudeAgent()
  self.temp=tempfile.TemporaryDirectory(dir='/home/sl/src/baton/work/scratch');self.addCleanup(self.temp.cleanup);self.root=pathlib.Path(self.temp.name)
 def process(self,timeout=False):
  agent=self.agent;owner=self
  class Child:
   returncode=None
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def communicate(self,timeout):
    held=agent.observed_invocation();owner.assertIsNotNone(held);owner.assertIsNone(held['ended_at']);owner.assertEqual(held['scope'],'provider-process')
    start=datetime.datetime.fromisoformat(held['started_at'].replace('Z','+00:00'));deadline=datetime.datetime.fromisoformat(held['deadline_at'].replace('Z','+00:00'));owner.assertEqual((deadline-start).total_seconds(),12)
    pub=baton_worker._ActivityPublisher(str(owner.root),{'attempt_id':'a','operation':'work'},lambda:None,invocation=agent.observed_invocation);pub._tick();owner.assertTrue((owner.root/'invocation.json').exists());owner.assertFalse((owner.root/'activity.json').exists())
    if timeout_flag:raise subprocess.TimeoutExpired('fixture-provider',timeout)
    self.returncode=0;return None,None
   def poll(self):return self.returncode
   def kill(self):self.returncode=-9
   def wait(self):return self.returncode
  timeout_flag=timeout
  return Child()
 def test_real_start_deadline_end_and_quiet_publication(self):
  self.assertIsNone(self.agent.observed_invocation())
  with mock.patch.object(subprocess,'Popen',return_value=self.process()):
   result=self.agent._run_provider(['fixture-provider'],timeout=12)
  self.assertEqual(result.returncode,0);self.assertIsNotNone(self.agent.observed_invocation()['ended_at'])
  pub=baton_worker._ActivityPublisher(str(self.root),{'attempt_id':'a','operation':'work'},lambda:None,invocation=self.agent.observed_invocation);pub._tick();self.assertIsNotNone(json.loads((self.root/'invocation.json').read_text())['ended_at'])
 def test_timeout_records_direct_child_end_and_preserves_exception(self):
  with mock.patch.object(subprocess,'Popen',return_value=self.process(True)):
   with self.assertRaises(subprocess.TimeoutExpired):self.agent._run_provider(['fixture-provider'],timeout=12)
  self.assertIsNotNone(self.agent.observed_invocation()['ended_at'])
 def test_no_creation_no_invented_origin(self):
  with mock.patch.object(subprocess,'Popen',side_effect=FileNotFoundError):
   with self.assertRaises(FileNotFoundError):self.agent._run_provider(['missing'],timeout=12)
  self.assertIsNone(self.agent.observed_invocation())
 def test_injected_runner_is_not_process_start_evidence(self):
  agent=claude_agent.ClaudeAgent(run=lambda *a,**kw:subprocess.CompletedProcess(a,0));agent._run_provider(['fake'],timeout=12);self.assertIsNone(agent.observed_invocation())
 def test_publication_failure_does_not_change_provider_outcome(self):
  pub=baton_worker._ActivityPublisher(str(self.root),{},lambda:None,invocation=lambda:(_ for _ in ()).throw(ValueError('fixture')));pub._tick();self.assertEqual(list(self.root.iterdir()),[])
if __name__=='__main__':unittest.main(verbosity=2)
