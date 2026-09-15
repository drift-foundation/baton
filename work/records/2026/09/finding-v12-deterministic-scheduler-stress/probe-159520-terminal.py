"""W103525 claim159520: how far past the single integrator does the four-Job
schedule run once B is driven too? Retained whatever the answer is."""
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
for _ in range(9):
    sweep(held.job, held.composed, now=fixtures.NOW)
print("BEFORE-B", {one: case.case.states_for(held.job, held.composed, one)
                   for one in case.FOUR})
# B'S OWN TURNS, through the same helpers the other three used.
stage = "job-b/implementation"
attempt = case.attempt_of(held, stage)
print("B ATTEMPT", attempt)
try:
    case.case.turn(held.control, "implementation", attempt,
                   case.case.mounted_at(held.composed, attempt),
                   edits={"feature.py": case.case.B_FEATURE,
                          "feature_check.py": case.case.B_CHECK})
    causes = []
    for _ in range(10):
        report = sweep(held.job, held.composed, now=fixtures.NOW)
        for one in report["spoken"] + report["started"]:
            if one.get("outcome") not in (None, "performed") \
                    and "job-b" in str(one.get("stage_id")):
                causes.append(one)
    print("AFTER-B-TURN", case.case.states_for(held.job, held.composed, "job-b"))
    import json as _j
    print("B CAUSES", _j.dumps(causes[:3], default=str)[:700])
    review = case.attempt_of(held, "job-b/review")
    case.case.review_turn(held, "job-b", review, "accepted")
    for _ in range(20):
        sweep(held.job, held.composed, now=fixtures.NOW)
except Exception as failed:
    print("B REFUSED", type(failed).__name__, str(failed)[:300])
for one in case.FOUR:
    print("FINAL", one, case.case.states_for(held.job, held.composed, one))
