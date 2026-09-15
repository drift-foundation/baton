"""W103525 claim157211: WHAT the four-Job artifact actually contains. A trace
with no records validates clean vacuously, and this Work has already been caught
once by an assertion that could not fail."""
import collections, json, sys, unittest
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from tests.tools import scheduler_trace

case = T.TheComposedOwnersSupplyAuthorizedTransitions(
    "test_the_four_job_contention_exports_a_clean_artifact")
case.setUp()
held = case.four_job_deployment(own_workers=True)
trace = case.blank()
case.observing(held, trace, "job-a", "implementation", "waiting",
               job_ids=case.FOUR, ticks=6)
jobs, workers, bindings = case.scenario_from(held, case.FOUR)
trace.scenario = scheduler_trace.Scenario(
    name="four-jobs", jobs=jobs, workers=workers, ticks=100,
    order=["job-a/implementation"],
    resolved_principals={one["participant"]: one["principal"]
                         for one in workers})
artifact = trace.artifact(T.SOURCES)
print("RECORDS", len(artifact["records"]))
for key, count in sorted(collections.Counter(
        (one["stage_id"], one["act"], one["outcome"])
        for one in artifact["records"]).items()):
    print("  ", key, count)
print("VIOLATIONS", scheduler_trace.validate(artifact))
