"""W103525 claim157538: how far does the corrected four-Job schedule run?

Reviewer's own contrast reported: B implementation waiting, A integration
integrating, C/D integration queued in nine observed continuation ticks. This
asks the same question of the corrected fixture."""
import sys
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens")
case.setUp()
held = case.four_job_deployment(own_workers=True, ticks=7)
trace = case.blank()
case.four_job_schedule(trace, held, order=("job-a", "job-c", "job-d"))
for extra in range(9):
    sweep(held.job, held.composed, now=fixtures.NOW)
for job_id in case.FOUR:
    print("AFTER", job_id, case.case.states_for(held.job, held.composed, job_id))
print("PRODUCERS", case.producers_of(held))
