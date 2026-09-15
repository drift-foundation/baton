"""Additional derived result using existing public fixture setup, no fixture edit.
W156162 research; reuse W103525 scenario helpers, not its verification allowance.
"""
import json,hashlib
from pathlib import Path
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep
from baton_v12.integration import reconciliation
from tests.job_manager import fixtures
case=T.TheComposedOwnersSupplyAuthorizedTransitions('test_the_opened_edge_and_one_integrator_serialize_four_jobs');case.setUp()
saved={};original=case.b_and_terminal
def capture(held,trace):
    answer=original(held,trace);saved['held']=held;return answer
case.b_and_terminal=capture
try:
    case.test_the_opened_edge_and_one_integrator_serialize_four_jobs()
    held=saved['held'];deployment=case.case.deployment_of(held.composed)
    first={key[0] for key in deployment.judges}
    assert len(first)==1,first
    for _ in range(16):
        sweep(held.job,held.composed,now=fixtures.NOW)
        result_ids={key[0] for key in deployment.judges}
        if len(result_ids)>=2:break
    assert len(result_ids)==2,result_ids
    rows=[reconciliation.result_of(deployment.integration,result_id) for result_id in sorted(result_ids)]
    assert len({row['job_id'] for row in rows})==2
    assert {row['state'] for row in rows}=={'imported','published'},rows
    for row in rows:
        assert row['causal_observations']['base']['harness_added'] is True
        assert row['causal_observations']['base']['status']!=0
        assert row['causal_observations']['isolated']['status']==0
        assert row['causal_observations']['combined']['status']==0
    print(json.dumps({'results':[{'job_id':r['job_id'],'result_id':r['result_id'],'state':r['state'],'task':r['causal_observations']['combined']['test_identity'],'harness_digest':r['causal_observations']['combined']['test_digest']} for r in rows],'public_setup_helpers':['four_works','current_policy','four_jobs','four_submission','four_job_deployment'],'scope':'two genuine derived results; successful causal evidence, not the missing failure-isolation matrix','fixtures':{str(Path(T.__file__).resolve()):hashlib.sha256(Path(T.__file__).read_bytes()).hexdigest()}},indent=2))
finally:case.doCleanups()
