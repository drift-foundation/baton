import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.job_manager import publication_execution,cancellation
class Adoption(cases.PublicationExecutionCase):
 def test_clock_crosses_deadline_during_host_measurement(self):
  self.ready();self.launched();self.serving();self.assertEqual(self.turn(),0)
  real=publication_execution._measured_outputs
  def crossed(*args,**kwargs):
   value=real(*args,**kwargs);self.instants.append(cases.LATE);return value
  with patch.object(publication_execution,'_measured_outputs',crossed):self.tick(cases.PUBLISHED)
  result=publication_execution.result_of(self.jobs,self.recovery_job_id)
  print('HOST_COMMIT',json.dumps({'clock':self.clock(),'result':result,'fence':cancellation.fence_of(self.jobs,self.recovery_job_id)},default=str))
  self.assertIsNone(result,'new adoption must check current time after measurement, at commit')
if __name__=='__main__':unittest.main(verbosity=2)
