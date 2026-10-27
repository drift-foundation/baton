"""What state does an `unable` ending leave the line in, and who can advance it?"""
import json

from tests.tools import test_retry_task_lineage as suite
from tests.job_manager import fixtures
from baton_v12.worker_manager import review_cycles


class One(suite.TheRetriedJobReachesItsOwnRuntimes):
    def runTest(self):
        pass


case = One()
case.setUp()
held = case.failing_pool()
worker = case.worker_of(held["composed"], "implementation",
                        worker_id="implementation-worker")
deployment = worker.stage.deployment
line = deployment.line_for(case.job_id)
print("line:", json.dumps({k: str(v)[:60] for k, v in line.items()}, indent=1))
checkpoint = (review_cycles.checkpoint_of(held["control"],
                                          line["current_checkpoint_id"])
              if line.get("current_checkpoint_id") else None)
print("checkpoint:", json.dumps(
    {k: str(v)[:60] for k, v in (checkpoint or {}).items()}, indent=1)[:600])

rows = held["control"]._connection.execute(
    "SELECT runtime_attempt_id, state, checkpoint_id FROM review_attachments"
).fetchall()
print("attachments:", [tuple(one) for one in rows])
print("first job stages:", case.stages(held["jobs"], held["composed"],
                                       case.job_id))
writers = held["control"]._connection.execute(
    "SELECT writer_id, runtime_attempt_id, state, generation "
    "FROM line_writers").fetchall()
print("writers:", [tuple(one) for one in writers])
case.doCleanups()
