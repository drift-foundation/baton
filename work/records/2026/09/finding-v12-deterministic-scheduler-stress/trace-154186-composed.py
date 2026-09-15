"""W103525 claim154186 (correction of review 2026-09-12T16:35:09Z C1-C3): the composed-owner authorized-transition artifact.

Run from `v12/python` with `PYTHONPATH=src:tools:.`; refuses to overwrite.

R1, review 2026-09-12T16:18:34Z: the scheduler-level schedules record real
reservations and releases but no owner-issued offer, claim, completion, review or
correction. This exports the composed fixture's OWN authorized transitions --
real Authority, real producers and reviewers, real review cycles, scripted engine
seam -- read back out of durable owner evidence.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trace-154186-composed.json")


def main():
    if os.path.exists(OUT):
        sys.stderr.write(f"refusing to overwrite {OUT}\n")
        return 2

    import tests.tools.test_scheduler_trace as suite
    from tests.tools import scheduler_trace

    held = {"claim": 154186, "work": "W103525",
            "schema": "baton.v12.scheduler-trace-set/2",
            "note": "composed fixture: real Authority, producers, reviewers and "
                    "review cycles; the engine seam is scripted and disclosed. "
                    "Offer, claim and completion are read from the manager's own "
                    "receipts and the projection's own state, never from an "
                    "allocation release.",
            "schedules": []}

    for name, method in (
            ("composed-accepted-review",
             "test_an_accepted_review_is_a_real_authorized_transition"),
            ("composed-correction",
             "test_a_correction_opens_a_second_episode_on_the_same_line"),
            ("composed-two-repository-bindings",
             "test_two_independent_repository_bindings_are_configured"),
            ("composed-wrong-repository-refusal",
             "test_a_wrong_repository_binding_is_refused_by_its_own_owner"),
            ("composed-second-team-matrix",
             "test_a_second_team_is_authorized_by_scope_not_by_membership")):
        case = suite.TheComposedOwnersSupplyAuthorizedTransitions(method)
        case.setUp()
        try:
            captured = {}
            original = scheduler_trace.Trace.artifact

            def keeping(self, sources=()):
                answer = original(self, sources)
                captured["artifact"] = answer
                return answer

            scheduler_trace.Trace.artifact = keeping
            try:
                getattr(case, method)()
            finally:
                scheduler_trace.Trace.artifact = original
            artifact = captured["artifact"]
            held["schedules"].append({
                "name": name, "artifact": artifact,
                "violations": scheduler_trace.validate(artifact)})
        finally:
            case.doCleanups()

    with open(OUT, "w") as writing:
        json.dump(held, writing, indent=1, sort_keys=True)
    print(f"wrote {OUT}")
    for one in held["schedules"]:
        acts = sorted({(record["stage_id"], record["act"])
                       for record in one["artifact"]["records"]})
        print(one["name"], "violations:", len(one["violations"]),
              "acts:", acts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
