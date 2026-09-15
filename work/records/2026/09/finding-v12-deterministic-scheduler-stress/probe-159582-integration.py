"""W103525 claim159582: can a four-Job schedule reach a TERMINAL integration?
Whatever the owners answer is retained."""
import sys
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_the_opened_edge_and_one_integrator_serialize_four_jobs")
case.setUp()
held = case.four_job_deployment(own_workers=True, ticks=7)
trace = case.blank()
case.four_job_schedule(trace, held, order=("job-a", "job-c", "job-d"))
for _ in range(9):
    sweep(held.job, held.composed, now=fixtures.NOW)
# B'S OWN TURNS FIRST, so every producer container has ended before the engine
# is told the world stopped: that flag is DEPLOYMENT-WIDE, and applying it while
# other Jobs were live reported their runtimes gone and made them `exceptional`.
attempt_b = case.attempt_of(held, "job-b/implementation")
case.case.turn(held.control, "implementation", attempt_b,
               case.case.mounted_at(held.composed, attempt_b),
               edits={"feature.py": case.case.B_FEATURE,
                      "feature_check.py": case.case.B_CHECK})
for _ in range(12):
    sweep(held.job, held.composed, now=fixtures.NOW)
case.case.review_turn(held, "job-b", case.attempt_of(held, "job-b/review"),
                      "accepted")
for _ in range(20):
    sweep(held.job, held.composed, now=fixtures.NOW)
print("AFTER-B", {one: case.case.states_for(held.job, held.composed, one)
                  for one in case.FOUR})
integrating = [one for one in case.FOUR
               if case.case.states_for(held.job, held.composed, one)
               .get("integration") == "integrating"]
print("INTEGRATING", integrating)
attempt = case.attempt_of(held, integrating[0] + "/integration")
print("ATTEMPT", attempt)
try:
    answered = case.case.integration_turn(held, attempt)
    print("TURN", answered)
    # THE CONTAINER ENDED, which the manager must OBSERVE rather than be told.
    case.case.engine.stopped = True
    for _ in range(14):
        sweep(held.job, held.composed, now=fixtures.NOW)
except Exception as failed:
    print("REFUSED", type(failed).__name__, str(failed)[:300])
for one in case.FOUR:
    print("FINAL", one, case.case.states_for(held.job, held.composed, one))
