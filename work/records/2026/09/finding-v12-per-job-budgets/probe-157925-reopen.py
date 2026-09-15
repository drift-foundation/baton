"""W156162 claim157925: what the REOPENED sweeps actually report once the
engine survives the client. The previous form passed on destroyed runtimes."""
import json, sys
sys.path[:0] = ["src", "tools", "."]
from unittest.mock import patch
from tests.tools import test_execution_limits as mine
from baton_v12.job_manager import episodes_of, stages_of, sweep
from tests.job_manager import fixtures

case = mine.AReopenedServingKeepsBothJobsLaunchesUntouched(
    "test_a_reopened_serving_adopts_the_same_two_deliveries")
case.setUp()
held = case.case.coding()
stages = {}
for job_id in ("job-a", "job-b"):
    row = next(one for one in stages_of(held.job, job_id)
               if one["kind"] == "implementation")
    episode = episodes_of(held.job, row["stage_id"])[-1]
    stages[job_id] = dict(row, **{k: v for k, v in episode.items()
                                  if k not in row})
document = case.case.traversing()
engine = case.case.engine
held.composed.close(); held.job.close(); held.control.close()
with patch.object(type(case.case), "quiescing", return_value=engine):
    job, control, composed = case.case.serving_two(**document)
for index in range(3):
    report = sweep(job, composed, now=fixtures.NOW)
    print("SWEEP", index, json.dumps(
        {"refreshed": report["refreshed"], "started": report["started"],
         "acts": report["acts"]}, default=str)[:600])
for job_id in stages:
    print("STATE", job_id,
          case.case.states_for(job, composed, job_id))
print("STARTS", {j: len(case.starts_naming(o["attempt_id"]))
                 for j, o in stages.items()})
