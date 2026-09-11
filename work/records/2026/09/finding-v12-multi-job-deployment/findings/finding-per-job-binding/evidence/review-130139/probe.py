"""Public admission and configured read-only status, on disposable real stores."""
import json,time
from pathlib import Path
from tests.tools.test_stage_execution import EachJobBindsItsOwnDeploymentAndLine, SECOND_WORK
from tests.tools.test_stage_execution_status_hardening import HeldIntegrationStatus
from tests.job_manager import fixtures
from baton_v12.job_manager import submit,scheduler
from baton_v12.contracts import ContractRefusal
from tools import stage_execution
started=time.monotonic()
result={}
def refusal(error):
    return {'category':error.category,'code':error.code,'message':error.message}
f=EachJobBindsItsOwnDeploymentAndLine('runTest')
try:
    f.setUp()
    jobs,control,composed=f.serving_two()
    for job_id,kind,work in [('job-unknown','implementation',f.work),('job-b','review',SECOND_WORK)]:
        job=fixtures.job(job_id, stages=[fixtures.stage(kind,work)], input_digest=f.manifest['manifest_digest'],policy_digest=fixtures.POLICY_DIGEST)
        submit(jobs,fixtures.submission(submission_id='sub-'+job_id,jobs=[job]))
        stage=fixtures.JobManagerCase.attempting(f,jobs,job_id+'/'+kind)
        failed=None
        try: composed.admit(stage,job)
        except ContractRefusal as error: failed=refusal(error)
        allocation=scheduler.allocation_of(jobs,stage['attempt_id'])
        receipt=composed.receipt_of(composed.canonical_operation('admit',stage['offer_id']))
        result[job_id+'/'+kind]={'refusal':failed,'allocation':None if allocation is None else {k:allocation[k] for k in ('worker_id','allocation_state')},'admit_receipt_exists':receipt is not None}
finally:
    f.doCleanups()
g=HeldIntegrationStatus('runTest')
try:
    g.setUp()
    doc=g.document
    target=doc['canonical_target_id']
    doc['schema']=stage_execution.MULTI_CONFIG_SCHEMA
    doc['job_bindings']=[{'job_id':g.held.integration_stage['job_id'], 'job_work_id':g.fixture.work,'review_work_id':g.fixture.work,'line_declared_base':g.fixture.base,'canonical_target_id':target,'source_worker_id':'implementation-worker'}]
    g.configuration.write_text(json.dumps(doc))
    positive=g.read_status()
    result['readonly_matching_global']={'job_id':positive['jobs'][0]['job_id'],'succeeded':True}
    doc['canonical_target_id']='unrelated-global-target'
    g.configuration.write_text(json.dumps(doc))
    try:
        g.read_status()
        result['readonly_per_job_target']={'succeeded':True}
    except ContractRefusal as error:
        result['readonly_per_job_target']={'succeeded':False,'refusal':refusal(error)}
    g.assert_preserved()
    result['readonly_owners_and_databases_preserved']=True
finally:
    g.doCleanups()
    result['elapsed_seconds']=time.monotonic()-started
    Path(__file__).with_name('verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
