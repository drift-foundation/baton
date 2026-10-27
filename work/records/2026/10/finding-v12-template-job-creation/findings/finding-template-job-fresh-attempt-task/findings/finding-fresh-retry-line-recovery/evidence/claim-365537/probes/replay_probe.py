import json
from tests.tools.test_retry_task_lineage import TheRetriedJobReachesItsOwnRuntimes
from baton_v12.worker_manager import review_cycles
c=TheRetriedJobReachesItsOwnRuntimes();c.setUp()
try:
 h=c.completed_retry()
 writer=h['control']._connection.execute('SELECT * FROM line_writers WHERE runtime_attempt_id = ?', (c.first_attempt,)).fetchone()
 worker=c.worker_of(h['composed'],'implementation',worker_id='implementation-worker')
 result={'stages':h['stages'],'first_writer':writer['writer_id']}
 try:
  result['replay']=review_cycles.release_writer(h['control'],writer_id=writer['writer_id'],generation=writer['assignment_generation'],port=worker.port,reason='implementation produced no candidate to review')
 except Exception as e:result['refusal']=str(e)
 print(json.dumps(result,default=str))
finally:c.doCleanups()
