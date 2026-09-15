"""W103525 claim155914 probe: what a lost transport does to a composed session,
and what the NEXT session in that posture is.

PLAN item 5 keeps session continuity open. The contract's own words are that a
lost transport ENDS the epoch and the relay never resumes -- so "continuity" here
is the worker continuing while the session does NOT. This asks the owners what
they actually answer before a test asserts anything.

Run from `v12/python` with `PYTHONPATH=src:tools:.`.
"""
import json
import sys


def main():
    import tests.tools.test_stage_execution as composed_fixture
    from baton_v12.worker_manager import (adopt_provider_session,
                                          agent_sessions_of,
                                          certify_agent_session_profile,
                                          handle_transport_loss,
                                          open_agent_session, posture_slot,
                                          release_slot)
    from tests.manager.test_handshake import acp_profile

    case = composed_fixture.TwoBoundJobsTraverseServingAndCorrection(
        "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
    case.setUp()
    try:
        held = case.coding()
        profile = acp_profile()
        certify_agent_session_profile(held.control, profile)
        digest = profile["document_digest"]
        worker_id, _ = case.preparing(held.composed, held.first)
        port = {w["worker_id"]: w
                for w in held.composed.workers}[worker_id]["operations"]._worker.port
        first = open_agent_session(held.control, port, attempt_id=held.first,
                                   posture="execution", profile_digest=digest,
                                   intent="serve-implementation-1")
        ref = first["agent_session_ref"]
        adopt_provider_session(held.control, attempt_id=held.first,
                               posture="execution",
                               session_epoch=ref["session_epoch"],
                               provider_session_id="provider-session-1")
        live = dict(ref, provider_session_id="provider-session-1")
        lost = handle_transport_loss(held.control, live, turn_in_flight=True)
        print("transport loss", json.dumps(lost, sort_keys=True, default=str))
        print("slot", json.dumps(posture_slot(held.control, held.first,
                                              "execution"),
                                 sort_keys=True, default=str))
        # A SECOND OPENING BEFORE RECOVERY.
        try:
            open_agent_session(held.control, port, attempt_id=held.first,
                               posture="execution", profile_digest=digest,
                               intent="serve-implementation-2")
            print("SECOND OPENING ACCEPTED BEFORE RECOVERY")
        except Exception as failure:
            print("second opening refused",
                  f"{type(failure).__name__}: {failure}")
        released = release_slot(held.control, attempt_id=held.first,
                                posture="execution",
                                session_epoch=ref["session_epoch"],
                                evidence="session-absent",
                                observed_identity="provider-session-1",
                                reason="the transport died and the provider "
                                       "session was observed absent")
        print("released", json.dumps(released, sort_keys=True, default=str))
        second = open_agent_session(held.control, port, attempt_id=held.first,
                                    posture="execution",
                                    profile_digest=digest,
                                    intent="serve-implementation-2")
        print("second session",
              json.dumps(second["agent_session_ref"], sort_keys=True))
        print("sessions", json.dumps(
            [{k: one[k] for k in ("posture", "session_epoch", "participant",
                                  "provider_session_id", "state")}
             for one in agent_sessions_of(held.control, held.first)],
            sort_keys=True))
    finally:
        case.doCleanups()
    return 0


if __name__ == "__main__":
    sys.exit(main())
