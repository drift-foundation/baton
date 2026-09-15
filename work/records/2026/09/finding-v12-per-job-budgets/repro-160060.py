"""Direct blocked-result judgment gate through the actual composed deployment."""
import copy,json,os
from unittest.mock import patch
from tests.tools.test_execution_limits import TheComposedHostVerificationUsesTheJobsCeiling
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import reconciliation
from tools import single_worker
case=TheComposedHostVerificationUsesTheJobsCeiling('test_a_blocked_failure_can_never_be_published_or_authorized')
case.setUp()
try:
    held,deployment,result_id=case._blocked_result()
    before=copy.deepcopy(reconciliation.result_of(deployment.integration,result_id))
    home=os.path.join(deployment.given['state_root'],'result-judgments')
    paths_before=sorted(os.listdir(home)) if os.path.isdir(home) else None
    counts=(len(case.seen),case.materialized)
    assert counts==(1,1),counts
    refusals=[]
    with patch.object(single_worker,'JudgmentExecution',wraps=single_worker.JudgmentExecution) as judges, patch.object(deployment,'_engine_run',wraps=deployment._engine_run) as engine:
        for name in ('judgment_subject','judge_result'):
            try:
                getattr(deployment,name)(result_id)
            except ContractRefusal as error:
                assert 'blocked' in str(error),str(error)
                refusals.append({'owner':name,'code':error.code,'detail':str(error)})
            else:
                raise AssertionError(name+' accepted a blocked result')
        assert judges.call_count==0,judges.call_count
        assert engine.call_count==0,engine.call_count
    assert reconciliation.result_of(deployment.integration,result_id)==before
    assert (len(case.seen),case.materialized)==counts
    assert deployment.judges=={}
    assert (sorted(os.listdir(home)) if os.path.isdir(home) else None)==paths_before
    print(json.dumps({'refusals':refusals,'host_commands':len(case.seen),'materializations':case.materialized,'judgment_constructions':judges.call_count,'engine_calls':engine.call_count,'result_unchanged':True,'dispatch_paths_unchanged':True}))
finally:
    case.doCleanups()
