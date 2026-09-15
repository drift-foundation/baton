"""W103525 claim159520: the composed-owner artifact set, with ALL FOUR JOBS
CODED AND REVIEWED.

Run from `v12/python` with `PYTHONPATH=src:tools:.`; refuses to overwrite.

Two corrections and one advance since claim159444.

THE COMBINED NEGATIVE NOW BINDS WHAT IT DESCRIBES. Review 2026-09-13T09:44:04Z
[P2]: `two_repository_bindings` set each worker's nominated source and each
binding's base and target and left `source_worker_id` alone, so the case
described `job-d` on the second repository while binding it to the first
repository's producer. The helper moves every operand that selects a repository
now, and both combined cases assert the mapping the deployment HOLDS -- source
worker, that worker's repository, the declared base and the bound target --
before reading any outcome.

AND JOB B TAKES ITS OWN TURNS. Its configured task names `feature_check.py` and
asserts `feature.py`'s value, so a turn writing the base fixture's harness
produces no completed frozen result -- measured in probe-159520-terminal.py,
where the conclusion deferred with exactly that cause. With its own output, all
four Jobs code and are reviewed, and the single configured integrator then has
ALL FOUR contending: one integrating, three queued.

WHAT IS SIMULATED, NAMED. The worker entry, the workload, the Job and Worker
Manager owners, the Authority and the review cycles are the real ones; the
container engine is a scripted seam and the provider is a deterministic child
process, not a live model.

KEYED BY SCENARIO NAME, not by method. The alternate-order case builds TWO traces
in one run -- that is the whole point of it -- so an exporter that kept only the
last artifact per method would have dropped one of them.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-159520-composed.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 159520, "work": "W103525",
            "schema": "baton.v12.scheduler-trace-set/2",
            "note": "composed fixture: real Authority, producers, reviewers, "
                    "review cycles and agent sessions. The engine seam and the "
                    "provider session ids are scripted and disclosed; every "
                    "outcome is an owner's own answer. Offer, claim, "
                    "completion, session and correction are read from the "
                    "owners' own rows and receipts, never from an allocation "
                    "release.",
            "schedules": []}

    for method in (
            "test_the_producer_and_the_reviewer_hold_their_own_sessions",
            "test_a_lost_transport_ends_the_epoch_and_never_resumes",
            "test_a_same_line_correction_keeps_its_worker_and_not_its_session",
            "test_the_composed_deployment_reopens_and_continues",
            "test_both_jobs_reach_a_real_imported_integration",
            "test_both_jobs_traverse_and_one_integrator_serializes_them",
            "test_the_two_bound_jobs_complete_in_either_order",
            "test_an_accepted_review_is_a_real_authorized_transition",
            "test_a_correction_opens_a_second_episode_on_the_same_line",
            "test_two_independent_repository_bindings_are_configured",
            "test_a_wrong_repository_binding_is_refused_by_its_own_owner",
            "test_a_second_team_is_authorized_by_scope_not_by_membership",
            "test_real_authorization_receipts_bind_actor_scope_and_subject",
            # W103525 PLAN item 6, started under owner ruling157085.
            "test_the_four_job_contention_exports_a_clean_artifact",
            # Claim159520: the two bounded schedules, actually driven.
            "test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens",
            "test_the_alternate_schedule_reaches_the_same_completions",
            "test_the_opened_edge_and_one_integrator_serialize_four_jobs"):
        case = suite.TheComposedOwnersSupplyAuthorizedTransitions(method)
        case.setUp()
        try:
            captured = {}
            original = scheduler_trace.Trace.artifact

            def keeping(self, sources=()):
                answer = original(self, sources)
                captured[answer["scenario"]["name"]] = answer
                return answer

            scheduler_trace.Trace.artifact = keeping
            try:
                getattr(case, method)()
            finally:
                scheduler_trace.Trace.artifact = original
            for name in sorted(captured):
                artifact = captured[name]
                held["schedules"].append({
                    "name": name, "method": method, "artifact": artifact,
                    "violations": scheduler_trace.validate(artifact)})
        finally:
            case.doCleanups()

    with open(OUT, "w") as writing:
        json.dump(held, writing, indent=1, sort_keys=True)
    print(f"wrote {OUT}")
    for one in held["schedules"]:
        artifact = one["artifact"]
        sessions = sorted({record["session_id"]
                           for record in artifact["records"]
                           if record["session_id"]})
        print(one["name"], "violations:", len(one["violations"]),
              "records:", len(artifact["records"]),
              "acts:", sorted({record["act"] for record in
                               artifact["records"]}),
              "sessions:", len(sessions),
              "gaps:", [gap["name"] for gap in artifact["gaps"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
