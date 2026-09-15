"""W103525 claim155666 probe: can the composed path open a REAL agent session?

Owner155646 authorized "demonstrate nonempty sessions and independent roles
first". This asks the question before any test is written, so that a refusal is
reported as the owner's own sentence rather than guessed at.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.worker_manager import (agent_sessions_of,
                                          certify_agent_session_profile,
                                          open_agent_session)
    from tests.manager.test_handshake import acp_profile

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding()
        print("attempts", held.first, held.second)
        # THE ATTEMPT ROW, as the session owner will read it.
        row = held.control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (held.first,)).fetchone()
        print("attempt columns", list(row.keys()) if row else None)
        if row is not None:
            print("attempt", json.dumps({k: row[k] for k in row.keys()
                                         if k in ("runtime_attempt_id", "work_id",
                                                  "authority_uuid",
                                                  "assignment_participant",
                                                  "assignment_generation")},
                                        sort_keys=True))
        worker_id, _prepared = case.preparing(held.composed, held.first)
        print("prepared by", worker_id)
        one = {w["worker_id"]: w for w in held.composed.workers}[worker_id]
        inner = one["operations"]._worker
        print("worker port participant", getattr(
            getattr(inner, "port", None), "participant", None))
        profile = acp_profile()
        certified = certify_agent_session_profile(held.control, profile)
        print("certified", json.dumps(certified, sort_keys=True))
        for posture in ("consent", "execution"):
            try:
                answer = open_agent_session(
                    held.control, inner.port, attempt_id=held.first,
                    posture=posture, profile_digest=profile["document_digest"],
                    intent=f"probe-{posture}-1")
                print(posture, "opened",
                      json.dumps(answer["agent_session_ref"], sort_keys=True))
            except Exception as failure:
                print(posture, "REFUSED",
                      f"{type(failure).__name__}: {failure}")
        print("sessions", json.dumps(agent_sessions_of(held.control,
                                                       held.first),
                                     sort_keys=True, default=str))
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
