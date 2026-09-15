"""W103525 claim157712: the composed-owner artifact set, with NO ACT LABEL THIS
DEPLOYMENT DID NOT PERFORM.

Run from `v12/python` with `PYTHONPATH=src:tools:.`; refuses to overwrite.

Review 2026-09-13T04:38:33Z [P1] audited the whole export and found four more
records carrying a `submit` label for something that is not a Job submission:
`composed-second-team-matrix`'s two composition REFUSALS and its composing
positive -- which is `serving_two`/`operations_from` plus a capability and a
principal read -- and `composed-wrong-repository`'s `line_for`/`create_line`
refusal.

All four facts are PRESERVED and none of them is a record any more. They are
named configuration evidence in their own scenario notes: what was asked, which
owner answered, and the owner's own refusal sentence. The proof is unchanged --
the cases still drive the real owners and still assert the real refusals -- and
the artifacts no longer claim acts nobody performed.

`submitted()` is the one place that emits `submit`, and it emits it because it
has just called the public `submit`. That stays.

The driven four-Job schedules are unchanged from claim157605: both bounded
orders complete all six stages and open the cross-Job edge, and the continuation
reaches one integrator serializing the three of four Jobs eligible at that point.

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
OUT = os.path.join(HERE, "trace-157712-composed.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 157712, "work": "W103525",
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
            # Claim157712: the two bounded schedules, actually driven.
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
