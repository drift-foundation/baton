import json
from unittest import mock
from tests.tools.test_retry_task_lineage import TheRetriedJobReachesItsOwnRuntimes
from baton_v12.worker_manager import review_cycles
c=TheRetriedJobReachesItsOwnRuntimes();c.setUp();results=[]
class StopProbe(BaseException):pass
def intercept(store, *,writer_id,generation,profile,port):
 w=review_cycles.writer_of(store,writer_id)
 a=store._connection.execute('SELECT worker_disposition FROM attempts WHERE runtime_attempt_id=?',(w['runtime_attempt_id'],)).fetchone()
 result={'disposition':a[0]}
 try:
  result['released']=review_cycles.release_writer(store,writer_id=writer_id,generation=generation,port=port,reason='implementation produced no candidate to review')
 except Exception as e:result['refusal']=str(e)
 result['line_state_after']=review_cycles.line_of(store,w['line_id'])['state'];results.append(result)
 raise StopProbe()
try:
 with mock.patch.object(review_cycles,'freeze_checkpoint',intercept):
  try:c.completed_retry()
  except StopProbe:pass
 print(json.dumps(results,default=str))
finally:c.doCleanups()
