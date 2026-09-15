"""W103525 claim157442: can the four-Job scenario's producers actually take a
REAL TURN and complete? Reviewer: continue actual producer/reviewer turns."""
import sys, traceback
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_four_jobs_two_teams_claim_three_producers_at_once")
case.setUp()
held = case.four_job_deployment(own_workers=True, ticks=7)
producers = case.producers_of(held)
print("PRODUCERS", producers)
for job_id in ("job-a", "job-c", "job-d"):
    stage = job_id + "/implementation"
    attempt = case.attempt_of(held, stage)
    try:
        states = case.case.produced(
            held, job_id, attempt,
            f"print('the {job_id} producer answered')\n")
        print("PRODUCED", job_id, states)
    except Exception as failed:
        print("PRODUCED", job_id, "REFUSED", type(failed).__name__,
              str(failed)[:260])
for job_id in ("job-a", "job-b", "job-c", "job-d"):
    print("STATES", job_id, case.case.states_for(held.job, held.composed, job_id))

# THE REVIEWS, one at a time, with the ordinary ticks between them.
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
for round_ in range(3):
    for job_id in ("job-a", "job-c", "job-d"):
        stage = job_id + "/review"
        state = case.case.states_for(held.job, held.composed, job_id).get("review")
        if state != "waiting":
            continue
        attempt = case.attempt_of(held, stage)
        try:
            case.case.review_turn(held, job_id, attempt, "accepted")
            print("REVIEWED", job_id, attempt[:20])
        except Exception as failed:
            print("REVIEWED", job_id, "REFUSED", type(failed).__name__,
                  str(failed)[:200])
    for _ in range(14):
        sweep(held.job, held.composed, now=fixtures.NOW)
for job_id in ("job-a", "job-b", "job-c", "job-d"):
    print("AFTER", job_id, case.case.states_for(held.job, held.composed, job_id))

# WHY THE REVIEWS STAY `answering`: the projection's own reason.
import json as _json
from baton_v12.job_manager.projection import stage_states
states = stage_states(held.job, held.composed)
one = states.get("job-a/review") or {}
for name in ("state", "reason", "detail", "why", "runtime", "ending"):
    if name in one:
        print("A/REVIEW", name, _json.dumps(one[name], default=str)[:400])
print("A/REVIEW KEYS", sorted(one))
held_ending = one.get("ending") or {}
for name in sorted(held_ending):
    if name != "intent":
        print("A/ENDING", name, _json.dumps(held_ending[name], default=str)[:300])
