import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.worker_manager import tokens,attempt_runtime_of
from baton_v12.job_manager import publication_execution,recovery_owner_items_of
class Failure(cases.PublicationExecutionCase):
 def test_expired_worker_releases_token_without_relaunch(self):
  import baton_worker
  self.ready();self.launched();self.serving()
  place=Path(self.storage)/self.publication_attempt/'workspace';s=place.stat()
  domain=tokens.domain_of('workspace',f'{s.st_dev}:{s.st_ino}');generation=tokens.outstanding(self.control,domain)[0]['generation']
  real=baton_worker.measured
  def late(*a,**kw):
   self.instants.append(cases.LATE);return real(*a,**kw)
  with patch.object(baton_worker,'measured',late):self.assertEqual(self.turn(),1)
  for _ in range(4):self.tick(cases.LATE)
  state=tokens.token_of(self.control,domain,generation)
  print('EXPIRED',json.dumps({'token':state,'runtime':attempt_runtime_of(self.control,self.publication_attempt),'readiness':publication_execution.publication_readiness(self.jobs,'D1'),'owner_items':recovery_owner_items_of(self.jobs)},default=str))
  self.assertTrue(state['returned'])
  self.assertEqual(self.review_offers(),[])
if __name__=='__main__':unittest.main(verbosity=2)
