"""Read the isolation test's actual returned phase and result/Job pairing."""
import json
from tests.tools.test_execution_limits import TheComposedHostVerificationUsesTheJobsCeiling as Case
from baton_v12.integration import reconciliation
from baton_v12.contracts import ContractRefusal
case=Case('test_one_retained_failure_never_speaks_for_another_execution');case.setUp()
original=case._isolation_owner
records=[]
def observed(deployment,*,scope,seconds):
    owner=original(deployment,scope=scope,seconds=seconds)
    run=owner._run
    try:
        row=reconciliation.result_of(deployment.integration,scope[1]);row_job=row['job_id']
    except ContractRefusal as failure:row_job='REFUSED: '+str(failure)
    def call(*args,**kwargs):
        result=run(*args,**kwargs)
        records.append({'scope':scope,'actual_result_job':row_job,'seconds':seconds,'returned_phase':result['phase'],'input_commit_equals_tree':result['input_commit']==result['input_tree'],'answer':result})
        return result
    owner._run=call
    return owner
case._isolation_owner=observed
try:
    case.test_one_retained_failure_never_speaks_for_another_execution()
    print(json.dumps(records,indent=2))
finally:case.doCleanups()
