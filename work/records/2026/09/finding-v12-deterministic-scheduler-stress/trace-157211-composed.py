"""W103525 claim157211: the composed-owner artifact set, now with FOUR JOBS.

Run from `v12/python` with `PYTHONPATH=src:tools:.`; refuses to overwrite.

TWO THINGS ARE NEW HERE. R6d, from review 2026-09-13T01:18:16Z: the owner result
reference already carried `source_proposal_id` and `state` and the validator
compared neither, so a reconciled completion could name a source its own
referenced result never derived from, and a `published` snapshot could be
presented as terminal proof of an import. Both are compared now and both
mutations are retained in the suite.

And owner ruling157085 raised the implementation allowance to 600 cumulative
seconds so the FOUR-JOB composition could be started. It is started: four Works
on the real Authority, four Jobs from one submission across two repositories,
one cross-Job dependency edge A->B and independent C/D, and three producers
allocated at one instant. The PLAN's "two implementation slots" is NOT what runs
-- a configured worker carries one Work and a Work belongs to one Job's stage --
and the artifact carries that as a recorded gap with the measured contrast
behind it rather than as an argument.

KEYED BY SCENARIO NAME, not by method. The alternate-order case builds TWO traces
in one run -- that is the whole point of it -- so an exporter that kept only the
last artifact per method would have dropped one of them.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-157211-composed.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 157211, "work": "W103525",
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
            "test_the_four_job_contention_exports_a_clean_artifact"):
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
