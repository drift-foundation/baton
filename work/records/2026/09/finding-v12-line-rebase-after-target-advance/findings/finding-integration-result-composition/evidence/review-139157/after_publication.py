"""Independent real-store/Git traversal past the test-only reader error.
Uses existing disclosed fixture engine/provider. No product monkeypatch, no
changed candidate, no fabricated observation/receipt, no canonical Baton store.
"""
import json
from tests.tools import test_stage_execution as T
from baton_v12.integration import reconciliation
case=T.TwoBoundJobsTraverseServingAndCorrection("test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET")
case.setUp()
try:
    held=case.integrating()
    case.drive_job(held.job,held.composed,"job-a","integration","completed",ticks=4)
    deployment=case.deployment_of(held.composed)
    for i in range(4):
        report=case.tick(held)
        row=deployment.integration._connection.execute("SELECT result_id FROM integration_results").fetchone()
        if row is not None:
            result=reconciliation.result_of(deployment.integration,row["result_id"])
            if result["state"]=="published": break
    assert result["state"]=="published", result["state"]
    observed=result["causal_observations"]
    print("published",json.dumps({"state":result["state"],"causal_keys":list(observed),"statuses":{k:observed[k]["status"] for k in ("base","isolated","combined")}}))
    assert observed["base"]["status"]!=0
    assert observed["isolated"]["status"]==observed["combined"]["status"]==0
    assert len({observed[k]["test_digest"] for k in ("base","isolated","combined")})==1
    proposal=result["derived_proposal_id"]
    assert deployment.authority.receipts(proposal)==[]
    deployment.sessions["verification"].verify({"proposal_id":proposal,"verification_id":proposal+"-verification","observation":"passed","operation_id":proposal+"-verify"})
    deployment.sessions["review"].review({"proposal_id":proposal,"review_id":proposal+"-review","disposition":"accepted","operation_id":proposal+"-rev"})
    deployment.sessions["approval"].approve({"proposal_id":proposal,"approval_id":proposal+"-approval","disposition":"approved","policy_generation":deployment.authority.policy_generation(),"operation_id":proposal+"-appr"})
    for i in range(4):
        report=case.tick(held)
        result=reconciliation.result_of(deployment.integration,row["result_id"])
        events=[event for key in ("started","spoken","recovered") for event in report.get(key,[]) if event.get("stage_id")=="job-b/integration"]
        states=case.states_for(held.job,held.composed,"job-b")
        print("after_receipts",json.dumps({"tick":i,"result_state":result["state"],"reason":result.get("reason"),"states":states,"events":events},default=str))
        if result["state"]=="imported" or any(e.get("outcome")=="deferred" for e in events):break
    assert result["state"]=="imported", "actual import did not complete"
finally:
    case.doCleanups()
