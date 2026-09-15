"""W103525 claim157211: what the PUBLIC configuration owner says about four
Jobs. PLAN: "The exact legal public setup must be revalidated; a fixture that
cannot bind this configuration reports the gap rather than silently reducing it
to one team." This asks, and mutates nothing durable."""
import sys, traceback
sys.path[:0] = ["src", "tools", "."]

from tests.tools import test_stage_execution as composed

case = composed.TwoBoundJobsTraverseServingAndCorrection(
    "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
case.setUp()
try:
    from baton_v12.authority import Authority
    authority = Authority.open(case.authority_path,
                               expected_authority_uuid=case.config["authority_uuid"])
    try:
        for work in ("0000000a-W1", "0000000a-W2", "0000000a-W3",
                     "0000000a-W4", "0000000a-W5"):
            try:
                held = authority.project_work(work)
                print("WORK", work, {k: held.get(k) for k in
                                     ("route", "scope", "phase", "contract")})
            except Exception as failed:
                print("WORK", work, "ABSENT:", type(failed).__name__,
                      str(failed)[:120])
        for who in ("baton.claude", "baton.second", "baton.reviewer",
                    "baton.reviewer-2", "baton.integrator", "baton.third",
                    "baton.reviewer-3"):
            try:
                print("PRINCIPAL", who, authority.principal_of(who))
            except Exception as failed:
                print("PRINCIPAL", who, "ABSENT:", str(failed)[:100])
    finally:
        authority.dispose()
except Exception:
    traceback.print_exc()
print("SOURCES:", case.source, case.second_source)
given = case.two_jobs()
print("WORKER IDS:", [(w["worker_id"], w["role"],
                       w["deployment"].get("participant")) for w in given["workers"]])
print("BINDINGS:", given["job_bindings"])
