"""W103525 claim155666 probe, second half: the REVIEWER's own session.

Independent roles means two different principals holding two different sessions.
This drives Job A's implementation to a real completion, reaches the reviewer's
own activated attempt, and asks the session owner for it under the REVIEWER's
own port.

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
        profile = acp_profile()
        certify_agent_session_profile(held.control, profile)
        digest = profile["document_digest"]

        def port_of(attempt_id):
            worker_id, _ = case.preparing(held.composed, attempt_id)
            one = {w["worker_id"]: w for w in held.composed.workers}[worker_id]
            return worker_id, one["operations"]._worker.port

        producer_id, producer_port = port_of(held.first)
        print("producer", producer_id, producer_port.participant)
        opened = open_agent_session(
            held.control, producer_port, attempt_id=held.first,
            posture="execution", profile_digest=digest,
            intent="serve-implementation-1")
        print("producer session",
              json.dumps(opened["agent_session_ref"], sort_keys=True))

        case.turn(held.control, "implementation", held.first,
                  case.mounted_at(held.composed, held.first),
                  edits={"harness.py": "print('answered')\n"})
        case.drive_job(held.job, held.composed, "job-a", "implementation",
                       "completed")
        case.drive_job(held.job, held.composed, "job-a", "review", "waiting")
        reviewed = case.one_attempt_of(held.composed, "review-worker")
        print("review attempt", reviewed)
        row = held.control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (reviewed,)).fetchone()
        print("review attempt activation", json.dumps(
            {k: row[k] for k in ("work_id", "authority_uuid",
                                 "assignment_participant",
                                 "assignment_generation",
                                 "assignment_principal")}, sort_keys=True))
        reviewer_id, reviewer_port = port_of(reviewed)
        print("reviewer", reviewer_id, reviewer_port.participant)
        try:
            answer = open_agent_session(
                held.control, reviewer_port, attempt_id=reviewed,
                posture="execution", profile_digest=digest,
                intent="serve-review-1")
            print("reviewer session",
                  json.dumps(answer["agent_session_ref"], sort_keys=True))
        except Exception as failure:
            print("reviewer session REFUSED",
                  f"{type(failure).__name__}: {failure}")
        # AND WHAT A FOREIGN PORT IS TOLD, which is the separation itself.
        try:
            open_agent_session(held.control, producer_port,
                               attempt_id=reviewed, posture="execution",
                               profile_digest=digest,
                               intent="serve-review-by-producer")
            print("CROSSED PORT ACCEPTED -- no separation")
        except Exception as failure:
            print("crossed port refused",
                  f"{type(failure).__name__}: {failure}")
        for attempt_id in (held.first, reviewed):
            print("sessions", attempt_id[:20],
                  json.dumps([{k: one[k] for k in
                               ("posture", "session_epoch", "participant",
                                "provider_session_id", "state", "work_id")}
                              for one in agent_sessions_of(held.control,
                                                           attempt_id)],
                             sort_keys=True))
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
