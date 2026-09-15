"""Independent public close retry and post-import scratch lifecycle."""
import copy,json,os,shutil
from unittest.mock import patch
from tests.tools.test_execution_limits import TheComposedHostVerificationUsesTheJobsCeiling as Case
from tools import stage_execution
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore,queue,reconciliation
from tests.job_manager import fixtures
for branch in ('causal-retry','post-import-timeout','post-import-start-failed'):
    case=Case('test_a_scratch_that_survives_disposal_is_the_deployments_to_release');case.setUp()
    try:
        if branch=='causal-retry':
            with patch.object(shutil,'rmtree',lambda *a,**kw:None):
                held,deployment,result_id=case._blocked_result()
                registry=stage_execution._host_scratch(deployment)
                assert len(registry)==1,registry
                where=next(iter(registry))
                try:held.composed.close()
                except ContractRefusal as error:assert where in str(error),str(error)
                else:raise AssertionError('broken disposal was accepted')
                assert os.path.isdir(where) and where in registry
            held.composed.close()
            assert not os.path.exists(where) and registry=={}
            print(json.dumps({'branch':branch,'second_public_close':'passed','host_calls':len(case.seen),'materializations':case.materialized}))
        else:
            held,deployment,result_id,_=case._judged()
            argv=json.loads(case.case.shared_task_bytes)['verification']
            options={'failing':True} if branch.endswith('timeout') else {'error':FileNotFoundError('reviewer injected start failure')}
            case._watching(argv=argv,home=deployment.integration_root,**options)
            real=shutil.rmtree
            def refuse_host(where,*args,**kwargs):
                if os.path.dirname(os.path.realpath(where))==os.path.realpath(deployment.integration_root):return None
                return real(where,*args,**kwargs)
            with patch.object(shutil,'rmtree',refuse_host):
                for _ in range(4):case.case.tick(held)
            registry=stage_execution._host_scratch(deployment)
            assert len(registry)==1,registry
            where=next(iter(registry));assert os.path.isdir(where)
            retained=copy.deepcopy(stage_execution._host_retention(deployment))
            row=copy.deepcopy(reconciliation.result_of(deployment.integration,result_id))
            target=copy.deepcopy(queue.target_of(deployment.integration,row['canonical_target_id']))
            assert row['state']=='authorized' and target['state']=='blocked'
            assert where in target['blocked_account']['detail']['verification']['detail']
            store_path=deployment.given['integration_store'];incarnation=stage_execution._incarnation(held.control)
            held.composed.close()
            assert not os.path.exists(where) and registry=={}
            assert stage_execution._host_retention(deployment)==retained
            with IntegrationStore.open_readonly(store_path,incarnation=incarnation,clock=lambda:fixtures.NOW) as reader:
                assert reconciliation.result_of(reader,result_id)==row
                assert queue.target_of(reader,row['canonical_target_id'])==target
            assert (len(case.seen),case.materialized)==(1,1)
            print(json.dumps({'branch':branch,'public_close':'passed','durable_result_and_target_unchanged':True,'host_calls':len(case.seen),'materializations':case.materialized}))
    finally:case.doCleanups()
