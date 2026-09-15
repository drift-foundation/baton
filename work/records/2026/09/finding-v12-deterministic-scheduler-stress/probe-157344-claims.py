"""W103525 claim157344: do C and D CLAIM now that their routes are configured?
Reviewer [P1]: four further ordinary sweeps reported route baton.impl does not
resolve to baton.third/baton.fourth. This asks the same question again."""
import sys
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_four_jobs_on_two_repositories_code_in_parallel")
case.setUp()
held = case.four_job_deployment(own_workers=True)
for extra in range(4):
    sweep(held.job, held.composed, now=fixtures.NOW)
for job_id in ("job-a", "job-b", "job-c", "job-d"):
    print("STATES", job_id,
          case.case.states_for(held.job, held.composed, job_id))
print("PRODUCERS", case.producers_of(held))
from baton_v12.worker_manager.offers import claimed_offers_for
from baton_v12.job_manager import episodes
from baton_v12.job_manager.submission import stage_rows
for row in stage_rows(held.job):
    live = episodes.live_of(held.job, row["stage_id"])
    if not live:
        continue
    attempt = episodes.attempting(row, live)["attempt_id"]
    print("CLAIMED", row["stage_id"],
          len(claimed_offers_for(held.control, attempt)))
