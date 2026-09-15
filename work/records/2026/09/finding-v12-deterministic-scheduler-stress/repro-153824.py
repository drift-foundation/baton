"""Independent review probes; synthetic invalid inputs are not execution evidence.

Run from v12/python with PYTHONPATH=src:tools:.; writes no product files.
"""

import json

from baton_v12.job_manager import allocation_rows
from baton_v12.job_manager.projection import stage_states
from tests.tools import scheduler_trace as trace
from tests.tools.test_scheduler_trace import TraceCase


def record(act, attempt="a", worker="w1", principal="p1", **changed):
    held = dict.fromkeys(trace.RECORD_MEMBERS)
    held.update(tick=1, act=act, outcome="performed", attempt_id=attempt,
                worker_id=worker, principal=principal, job_id="job-a",
                stage_id="job-a/implementation", episode=1,
                operation_id=f"{act}:{attempt}", evidence="synthetic-invalid")
    held.update(changed)
    return held


def validate(records):
    held = trace.Trace(trace.Scenario(name="synthetic-invalid-review-probe", jobs=[], workers=[]))
    held.records = records
    return trace.validate(held.artifact())


answers = {"synthetic_invalid_traces": {}}
for name, records in {
    "claim_and_completion_without_reservation_or_offer": [record("claim"), record("complete")],
    "two_live_workers_share_one_effective_principal": [record("reserve"), record("reserve", "b", "w2")],
    "reopen_incorrectly_frees_live_capacity": [record("reserve"), record("reopen"), record("reserve", "b")],
    "regressing_logical_time": [record("reserve", tick=9), record("offer", tick=2), record("claim", tick=1), record("complete", tick=0)],
}.items():
    answers["synthetic_invalid_traces"][name] = {"records": records, "violations": validate(records)}

case = TraceCase()
case.setUp()
try:
    held = case.driven(["job-c/implementation"], ticks=1)
    # Preserve only the durable state a restarted driver can actually recover.
    case.jobs_store = case.store(incarnation="review-reopened")
    case._reserved = set()
    case.tick(held, 2, ["job-c/implementation"])
    answers["restart_with_fresh_driver_bookkeeping"] = {
        "durable_allocation_count": len(allocation_rows(case.jobs_store)),
        "violations": trace.validate(held.artifact()),
        "records": held.records,
    }
finally:
    case.doCleanups()

case = TraceCase()
case.setUp()
try:
    held = case.driven(["job-a/implementation"], ticks=1,
                       completing={1: ["job-a/implementation"]})
    answers["driver_calls_release_completion"] = {
        "stage_states": {key: value["state"] for key, value in stage_states(case.jobs_store, case.operations()).items()},
        "allocations": allocation_rows(case.jobs_store),
        "records": held.records,
        "violations": trace.validate(held.artifact()),
    }
finally:
    case.doCleanups()

print(json.dumps(answers, indent=2))
