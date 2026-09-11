"""W119405 reviewer: actual factory, public admission, and configured consumers."""
import json
import time
from pathlib import Path
from tests.tools.test_stage_execution import EachJobBindsItsOwnDeploymentAndLine
from tests.job_manager import fixtures
from baton_v12.job_manager import submit, scheduler
from baton_v12.contracts import ContractRefusal

started = time.monotonic()
result = {}
f = EachJobBindsItsOwnDeploymentAndLine('runTest')
try:
    f.setUp()
    jobs, control, composed = f.serving_two()
    deployment = f.deployment_of(composed)
    result['binding_worker_work_mismatch'] = {
        'job_b_bound_work': deployment.binding_for('job-b')['job_work_id'],
        'job_b_source_worker_manifest_work': next(
            one['deployment']['input_manifest']['work_ref']['work_id']
            for one in deployment.given['workers']
            if one['worker_id'] == 'implementation-worker-b')}
    for name, call in (
        ('integration_required_tests', composed.integrator.required_tests),
        ('integration_global_line', deployment.line),
        ('implementation_publication', lambda: deployment.publication.published_of(attempt_id='unused'))):
        try:
            call()
            result[name] = {'refused': False}
        except ContractRefusal as error:
            result[name] = {'refused': True, 'category': error.category, 'code': error.code, 'message': error.message}
    job = fixtures.job('job-unknown', stages=[fixtures.stage('implementation', f.work)],
                       input_digest=f.manifest['manifest_digest'], policy_digest=fixtures.POLICY_DIGEST)
    submit(jobs, fixtures.submission(jobs=[job]))
    stage = fixtures.JobManagerCase.attempting(f, jobs, 'job-unknown/implementation')
    try:
        composed.admit(stage, job)
        refused = None
    except ContractRefusal as error:
        refused = {'category': error.category, 'code': error.code, 'message': error.message}
    allocation = scheduler.allocation_of(jobs, stage['attempt_id'])
    receipt = composed.receipt_of(composed.canonical_operation('admit', stage['offer_id']))
    result['unknown_job_admission'] = {
        'refusal': refused, 'canonical_admit_receipt_exists': receipt is not None,
        'allocation_exists': allocation is not None,
        'allocation_state': None if allocation is None else allocation['allocation_state'],
        'stage_id': stage['stage_id']}
finally:
    f.doCleanups()
    result['elapsed_seconds'] = time.monotonic() - started
    Path(__file__).with_name('verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
