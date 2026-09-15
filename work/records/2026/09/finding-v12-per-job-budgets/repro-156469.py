"""Independent default-generation and null probes through disposable public owners."""
import json
from unittest.mock import patch
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore,submit,documents,projection
from baton_v12.job_manager import execution_limits as limits
from tests.job_manager.fixtures import JobManagerCase,NOW,UUID
from tests.job_manager.test_execution_limits import limited
case=JobManagerCase();case.setUp()
try:
    store=JobStore.open(case.job_path,authority_uuid=UUID,incarnation='review-156469',clock=case.clock);case.addCleanup(store.close)
    doc=limited(verification_command_seconds=120);first=submit(store,doc)
    def statuses(): return {j['job_id']:j['execution_limits'] for j in projection.status(store,case.operations(),observed_at=NOW)['jobs']}
    before=statuses()['job-a']; newer=max(limits.GENERATIONS)+1
    defaults=dict(limits.GENERATIONS[limits.CURRENT_GENERATION],provider_turn=7200)
    with patch.dict(limits.GENERATIONS,{newer:defaults}),patch.object(limits,'CURRENT_GENERATION',newer):
        assert submit(store,doc)==first
        new=limited();new['submission_id']='sub-new';new['jobs'][0]['job_id']='job-new';submit(store,new)
        after=statuses()
        assert after['job-a']==before
        assert after['job-new']['boundaries']['provider_turn']['seconds']==7200
    null=limited();null['jobs'][0]['execution_limits']=None
    try: documents.owned_submission(null)
    except ContractRefusal: rejected=True
    else: rejected=False
    assert rejected
    print(json.dumps({'old_job_unchanged':True,'new_job_provider_seconds':7200,'present_null_refused':rejected,'old_generation':before['compatibility_generation'],'new_generation':newer},sort_keys=True))
finally: case.doCleanups()
