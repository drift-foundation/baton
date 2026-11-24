import sys,json,unittest
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.worker_manager import review_cycles
from baton_v12.contracts import ContractRefusal
class Fence(cases.TheConnectedRecoveryFromARealPooledProducer):
 def test_committed_recovery_fence_must_bind_its_checkpoint_row(self):
  self.failed_at_publication()
  held=review_cycles.freeze_unreleased_recovered_checkpoint(self.control,**self.recovery_operands())
  old=held['checkpoint_id'];changed='checkpoint-review-transplant'
  # Fault injection into disposable fixture store only: real committed fence untouched.
  self.control._connection.execute('UPDATE line_checkpoints SET checkpoint_id = ? WHERE checkpoint_id = ?',(changed,old))
  with self.assertRaises(ContractRefusal):
   found=review_cycles.checkpoint_of(self.control,changed)
   print('TRANSPLANTED_FENCE',json.dumps({'row_checkpoint':found['checkpoint_id'],'fence_checkpoint':found['fence']['intent']['checkpoint_id'],'row_writer':found['writer_id'],'fence_writer':found['fence']['intent']['writer_id']},default=str))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Fence('test_committed_recovery_fence_must_bind_its_checkpoint_row')]))
 sys.exit(not result.wasSuccessful())
