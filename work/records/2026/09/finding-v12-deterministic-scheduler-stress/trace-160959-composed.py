"""W103525 claim160959: the composed-owner artifact set, with ALL FOUR
TERMINAL INTEGRATIONS OBSERVED AND AUTHORIZED IN BOTH BOUNDED ORDERS.

Owner ruling M160956 is what pays for this export. The change since
claim159644 is that each bounded schedule now carries every Job to a terminal
import rather than two: one direct import and THREE reconciled continuations,
each selecting the judges of ITS OWN result and each recording its own receipt
chain, with the earlier chains read before the later ones at the final tick.

Run from `v12/python` with `PYTHONPATH=src:tools:.`; refuses to overwrite.

Claim159582 left the terminal ticks OUT of the trace because observing the
completion alone produced `unauthorized-integration`. That was correct about the
oracle and wrong about what to do: it is a reason to record the chain, not a
reason to stop observing. Review 2026-09-13T10:00:30Z proved the exact seam, and
it is used here -- this deployment's own line, the integration checkpoint on it,
the proposal that checkpoint published, and the Authority's own receipts for that
proposal, through the `proposal_receipts` the accepted two-Job artifact already
uses. Nothing is invented and no source is extended.

AND BOTH ORDERS REACH IT. B's turns and the terminal integration are one helper
now, called from A-before-C and from C-before-A alike: a schedule that only ever
drove B in one order would be half a certification. The helper waits for B's own
container first, because the edge opens on A's review -- which is LAST in the
alternate order, where the first form assumed the other order's timing and
failed with "no configured worker prepared".

WHAT IS SIMULATED, NAMED. The worker entry, the workload, the Job and Worker
Manager owners, the Authority and the review cycles are the real ones; the
container engine is a scripted seam and the provider is a deterministic child
process, not a live model. The engine's `stopped` flag is deployment-wide and
proves nothing about future health; B's turns run before it for that reason.

KEYED BY SCENARIO NAME, not by method. The alternate-order case builds TWO traces
in one run -- that is the whole point of it -- so an exporter that kept only the
last artifact per method would have dropped one of them.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-160959-composed.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 160959, "work": "W103525",
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
            # Claim159644: the two bounded schedules, actually driven; claim160959
            # carries all four terminal outcomes in each of them.
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
