"""W103525 claim157344: WHICH Job's line cannot be materialized, and why."""
import sys, traceback
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from tools import stage_execution

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_four_jobs_on_two_repositories_code_in_parallel")
case.setUp()
case.four_works()
given = case.four_jobs(own_workers=True)
job, control, composed = case.case.serving_two(**given)
deployment = case.case.deployment_of(composed)
for binding in given["job_bindings"]:
    print("BINDING", binding["job_id"], binding["source_worker_id"],
          binding["line_declared_base"][:12], binding["canonical_target_id"],
          binding.get("job_work_id"))
for one in given["workers"]:
    print("WORKER", one["worker_id"], one["role"],
          one["deployment"].get("participant"),
          str(one["deployment"].get("nominated_source"))[-10:],
          str(one["deployment"].get("task_document"))[-22:])
for job_id in ("job-a", "job-b", "job-c", "job-d"):
    try:
        held = deployment.line_for(job_id)
        print("LINE", job_id, held["line_id"][:16])
    except Exception as failed:
        print("LINE", job_id, "REFUSED", type(failed).__name__,
              str(failed)[:200])
