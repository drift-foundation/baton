"""Show the existing public completion binding for both real integration branches."""
import json
from baton_v12.job_manager import episodes_of
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions as Cases

case = Cases("test_both_jobs_reach_a_real_imported_integration")
case.setUp()
try:
    receipts = case.proposal_receipts
    def recording(held, trace, job_id, subject, tick):
        stage = {"job_id": job_id, "kind": "integration", "stage_id": job_id + "/integration", **episodes_of(held.job, job_id + "/integration")[-1]}
        observed = held.composed.integrator.observe(stage)
        assert observed["state"] == "completed"
        assert observed["completion"]["proposal_id"] == subject
        print(json.dumps({"job_id": job_id, "stage_id": observed["stage_id"], "episode": observed["episode"], "attempt_id": observed["attempt_id"], "offer_id": observed["offer_id"], "completion": observed["completion"]}, sort_keys=True), flush=True)
        return receipts(held, trace, job_id, subject, tick)
    case.proposal_receipts = recording
    case.test_both_jobs_reach_a_real_imported_integration()
finally:
    case.doCleanups()
