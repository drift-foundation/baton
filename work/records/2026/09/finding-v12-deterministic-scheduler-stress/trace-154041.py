"""W103525 claim154041 (correction of review 2026-09-12T16:35:09Z C1-C3): the corrected trace set, gap report and reopen schedule.

Run from `v12/python` with `PYTHONPATH=src:tools:.`. It refuses to overwrite an
existing result, exactly as `baseline-153660.py` and `trace-153769.py` do.

WHAT REVIEW 2026-09-12T16:18:34Z CORRECTED HERE. R5: the first exporter discarded
the executed gap documents and wrote a separate hard-coded name/locator list, so
every artifact carried `gaps=[]` and the report was a restatement rather than
evidence. The gaps are now the ones the runs actually recorded. R1: the third
schedule is the requested reopen-and-continue run, driven by a genuinely fresh
driver over the same durable files, not a second capacity miss.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-154041.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 154041, "work": "W103525",
            "schema": "baton.v12.scheduler-trace-set/2",
            "note": "exploratory: JobManagerCase fake Authority sessions and an "
                    "unpinned jsonschema resolution. Allocation reservation and "
                    "release are real; no owner-issued stage completion, claim, "
                    "correction, review or integration is driven here, and the "
                    "oracle refuses any completion lacking its claim.",
            "schedules": [], "gaps": [], "validator": {}}

    def schedule(name, order, *, reopen=False):
        case = suite.TheScriptedScenarioRunsOverRealOwners(
            "test_the_artifact_is_versioned_and_carries_its_environment") \
            if not reopen else suite.TheThirdScheduleReopensAtADurableBoundary(
                "test_reopening_retains_durable_identities")
        case.setUp()
        try:
            trace = case.driven(order, ticks=1,
                                reopen_at=1 if reopen else None)
            if reopen:
                trace.record(1, "reopen", outcome="performed",
                             operation_id="store.reopen:jobs-reopened",
                             evidence="jobs.sqlite3")
                case.fresh_driver().tick(trace, 2, order)
            artifact = trace.artifact(suite.SOURCES)
            held["schedules"].append({
                "name": name, "order": order,
                "artifact": artifact,
                "violations": scheduler_trace.validate(artifact)})
        finally:
            case.doCleanups()

    schedule("a-before-c", ["job-a/implementation", "job-c/implementation"])
    schedule("c-before-a", ["job-c/implementation", "job-a/implementation"])
    schedule("capacity-miss-with-unrelated-review",
             ["job-c/implementation", "job-d/implementation",
              "job-a/implementation", "job-d/review"])
    schedule("reopen-and-continue",
             ["job-c/implementation", "job-d/implementation"], reopen=True)

    # R5: THE GAPS ARE THE ONES THE RUNS RECORDED, taken from the cases that
    # observe them rather than restated by hand.
    for kind, method in (
            (suite.TheRetainedContractMismatchesAreRecordedAsGaps,
             "test_stage_id_order_is_not_a_priority_contract"),
            (suite.TheRetainedContractMismatchesAreRecordedAsGaps,
             "test_affinity_fallback_is_soft_and_is_recorded_as_a_gap"),
            (suite.TheRetainedContractMismatchesAreRecordedAsGaps,
             "test_composed_continuation_is_not_observable_here"),
            (suite.TheRetainedContractMismatchesAreRecordedAsGaps,
             "test_authority_teams_and_repository_bindings_are_not_established")):
        case = kind(method)
        case.setUp()
        try:
            # Re-derive the same observation the case makes, and keep ITS
            # document -- the case itself asserts the gap is present.
            captured = []
            original = scheduler_trace.Trace.gap

            def keeping(self, **members):
                answer = original(self, **members)
                captured.append(answer)
                return answer

            scheduler_trace.Trace.gap = keeping
            try:
                getattr(case, method)()
            finally:
                scheduler_trace.Trace.gap = original
            held["gaps"].extend(captured)
        finally:
            case.doCleanups()

    held["validator"] = {
        "codes": sorted({"unknown-schema", "scenario-digest-mismatch",
                         "incomplete-record", "unattributed-act",
                         "missing-prerequisite", "out-of-order",
                         "duplicate-act", "episode-mismatch", "untimed-act",
                         "regressing-time", "successor-before-prerequisite",
                         "overlapping-occupancy", "unattributed-review",
                         "review-by-producer", "duplicate-operation",
                         "uncaused-refusal"}),
        "note": "each has a synthetic invalid-trace case built by deleting or "
                "corrupting exactly one thing in an otherwise legal trace; "
                "synthetic traces are never execution evidence"}

    with open(OUT, "w") as writing:
        json.dump(held, writing, indent=1, sort_keys=True)
    print(f"wrote {OUT}")
    for one in held["schedules"]:
        print(one["name"], "violations:", len(one["violations"]),
              "records:", len(one["artifact"]["records"]),
              "digest:", one["artifact"]["scenario_digest"][:19])
    print("gaps:", [one["name"] for one in held["gaps"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
