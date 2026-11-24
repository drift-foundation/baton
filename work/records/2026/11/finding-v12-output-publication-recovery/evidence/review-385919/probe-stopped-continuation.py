import sys,json,unittest
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from tools import instance,single_worker,stopped_settlement
from baton_v12.worker_manager import workspaces,attempt_runtime_of
class Stopped(cases.TheConnectedRecoveryFromARealPooledProducer):
 def test_settle_stopped_then_inspect(self):
  job=self.failed_at_publication(settle=False)
  self.operations.close()
  workspaces.held_manager_instance(self.config['workspace_storage']).release()
  places=instance.layout(self.state)
  distro=Path(places['distro']);distro.mkdir(parents=True,exist_ok=True)
  Path(places['command']).write_text('deterministic installed selector fixture')
  selector=instance.emit(self.state,authority_uuid=self.config['authority_uuid'],identity={'fixture':True},runtime=instance.manifest(distro),now=1)
  instance.publish(places['instance'],selector)
  with patch.object(single_worker,'effective_engine_run',return_value=self.engine):
   preview=stopped_settlement.execute('settlement-preview',places['instance'],job_id=job,stage_id=self.producer_stage['stage_id'],episode=1,operation_id='review-stopped',clock=lambda:self.now)
   print('PREVIEW',json.dumps(preview,default=str))
   settled=stopped_settlement.execute('settle-stopped',places['instance'],document=preview['request'],clock=lambda:self.now)
  print('SETTLED',json.dumps(settled,default=str))
  read=self.inspected(job)
  print('INSPECT_STOPPED',json.dumps({'runtime':attempt_runtime_of(self.control,self.attempt),'eligible':read['eligible'],'holds':read['holds']},default=str))
  self.assertEqual(settled['settlement']['state'],'settled')
  self.assertFalse(read['eligible'])
  self.restarted(same_engine=True)
  removal=self.operations.abandon_attempt(attempt_id=self.attempt,stage=self.producer_stage,reason='review supported removal after stopped settlement')
  print('REMOVAL_AFTER_STOPPED',json.dumps(removal,default=str))
  again=self.inspected(job)
  print('INSPECT_AFTER_REMOVAL',json.dumps({'eligible':again['eligible'],'holds':again['holds']},default=str))
  self.assertTrue(again['eligible'])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Stopped('test_settle_stopped_then_inspect')]))
 sys.exit(not result.wasSuccessful())
