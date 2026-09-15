"""W103525 claim156124: the unit-pool trace set, gap report and reopen schedule.

Run from `v12/python` with `PYTHONPATH=src:tools:.`. It refuses to overwrite an
existing result, exactly as `baseline-153660.py` and `trace-153769.py` do.

RE-EXPORTED UNDER THE CURRENT CANDIDATE BYTES. The record shape gained a
`session` context member and the environment manifest's `unobserved_fields`
became each trace's own declaration rather than a module constant, so the earlier
sets describe a shape this candidate no longer writes. The schedules, the gap
documents and the reopen boundary are the same four this claim inherited; what is
new is that each artifact now declares what ITS driver looked at, and this pool
looks at neither runtime nor session identity.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-156124.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 156124, "work": "W103525",
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
                         "uncaused-refusal", "unvalidated-act",
                         "unattributed-authorization", "unauthorized-subject",
                         "nonaccepting-authorization",
                         "mismatched-authorization",
                         "unreferenced-authorization",
                         "instants-disagree-with-order",
                         # Owner155646's slice.
                         "unattributed-session",
                         "consent-session-carries-an-assignment",
                         "session-attempt-mismatch",
                         "session-without-its-claim",
                         "review-session-by-producer",
                         "uncaused-correction", "unsuperseded-correction",
                         "unreviewed-correction",
                         "unobserved-field-recorded",
                         "undeclared-observation",
                         # Review 2026-09-12T23:32:26Z.
                         "unreferenced-session",
                         "session-contradicts-its-assignment",
                         "noncorrecting-judgment",
                         "mismatched-correction",
                         # Review 2026-09-12T23:45:06Z.
                         "misattributed-correction",
                         "unreferenced-correction",
                         # Review 2026-09-13T00:09:15Z: the same-tick handoff.
                         "unreferenced-session",
                         # Review 2026-09-13T00:24:01Z.
                         "unauthorized-integration"}),
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
