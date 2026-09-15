"""W103525 claim153769: produce the reproducible trace set and gap report.

Run from `v12/python` with `PYTHONPATH=src:tools:.`. It drives the same fixed
scenarios the focused suite drives, through the same REAL owners, and writes one
versioned artifact per schedule plus the consolidated gap report.

IT REFUSES TO OVERWRITE an existing result, exactly as `baseline-153660.py`
does: a trace file that could be silently replaced is not durable evidence.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-153769.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 153769, "work": "W103525",
            "schema": "baton.v12.scheduler-trace-set/1",
            "note": "exploratory: fake Authority sessions and an unpinned "
                    "jsonschema resolution; not composed certification",
            "schedules": [], "gaps": [], "validator": {}}

    schedules = [
        ("a-before-c", ["job-a/implementation", "job-c/implementation"]),
        ("c-before-a", ["job-c/implementation", "job-a/implementation"]),
        ("capacity-miss", ["job-c/implementation", "job-d/implementation",
                           "job-a/implementation"]),
    ]
    for name, order in schedules:
        case = suite.TheScriptedScenarioRunsOverRealOwners(
            "test_the_artifact_is_versioned_and_carries_its_environment")
        case.setUp()
        try:
            trace = case.driven(order, ticks=1)
            artifact = trace.artifact(suite.SOURCES)
            held["schedules"].append({
                "name": name, "order": order,
                "artifact": artifact,
                "violations": scheduler_trace.validate(artifact)})
        finally:
            case.doCleanups()

    # THE GAP REPORT, produced by the same cases that record the gaps.
    for method in ("test_stage_id_order_is_not_a_priority_contract",
                   "test_affinity_fallback_is_soft_and_is_recorded_as_a_gap",
                   "test_composed_continuation_is_not_observable_here"):
        case = suite.TheRetainedContractMismatchesAreRecordedAsGaps(method)
        case.setUp()
        try:
            getattr(case, method)()
        finally:
            case.doCleanups()
    # The gaps themselves are asserted inside those cases; restate the three
    # retained mismatches here so the report stands alone.
    held["gaps"] = [
        {"name": "explicit-fallback", "state": "open",
         "locator": "FINDING.md 2026-09-12T15:54:16Z mismatch 1"},
        {"name": "priority-and-creation-order", "state": "open",
         "locator": "FINDING.md 2026-09-12T15:54:16Z mismatch 2"},
        {"name": "composed-continuation", "state": "open",
         "locator": "FINDING.md 2026-09-12T15:54:16Z mismatch 3"}]

    held["validator"] = {
        "codes": ["unknown-schema", "incomplete-record", "unattributed-act",
                  "out-of-order", "untimed-act", "unproven-completion",
                  "successor-before-prerequisite", "overlapping-occupancy",
                  "unattributed-review", "review-by-producer",
                  "duplicate-operation", "uncaused-refusal"],
        "note": "each has a synthetic invalid-trace case; synthetic traces are "
                "never execution evidence"}

    with open(OUT, "w") as writing:
        json.dump(held, writing, indent=1, sort_keys=True)
    print(f"wrote {OUT}")
    for one in held["schedules"]:
        print(one["name"], "violations:", len(one["violations"]),
              "records:", len(one["artifact"]["records"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
