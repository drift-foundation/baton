import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.job_manager import publication_execution,cancellation
from baton_v12.worker_manager import attempt_runtime_of
class Window(cases.PublicationExecutionCase):
 def test_expiry_after_final_gate_before_terminal(self):
  import baton_worker
  self.ready();self.launched();self.serving()
  original=baton_worker._publish
  def crossing(root,name,body,*args,**kwargs):
   if name=='state-work.json' and body.get('state')=='answered':self.instants.append(cases.LATE)
   return original(root,name,body,*args,**kwargs)
  with patch.object(baton_worker,'_publish',crossing):rc=self.turn()
  terminal=self.exchange_view()['terminal']
  for _ in range(3):self.tick(cases.LATE)
  observed={'worker_rc':rc,'terminal':terminal,'fence':cancellation.fence_of(self.jobs,self.recovery_job_id),'result':publication_execution.result_of(self.jobs,self.recovery_job_id),'runtime':attempt_runtime_of(self.control,self.publication_attempt),'readiness':publication_execution.publication_readiness(self.jobs,'D1')}
  print('WINDOW',json.dumps(observed,default=str))
  self.assertIsNone(observed['result'],'expired publication must not acquire new adoption result')
if __name__=='__main__':unittest.main(verbosity=2)
