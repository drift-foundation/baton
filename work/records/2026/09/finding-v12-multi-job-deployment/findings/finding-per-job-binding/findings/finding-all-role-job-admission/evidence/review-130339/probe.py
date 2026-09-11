"""Bounded public admission controls; no direct database access or mutation."""
import json
import time
from pathlib import Path
from tests.tools.test_stage_execution import EachJobBindsItsOwnDeploymentAndLine, SECOND_WORK
from tests.job_manager import fixtures
from baton_v12.job_manager import submit, scheduler
from baton_v12.contracts import ContractRefusal

started = time.monotonic()
results = []
for label, job_id, kind in [
        ('a-implementation', 'job-a', 'implementation'),
        ('b-review', 'job-b', 'review'),
        ('a-integration', 'job-a', 'integration'),
        ('b-integration', 'job-b', 'integration'),
        ('b-wrong-input', 'job-b', 'review'),
        ('b-wrong-policy', 'job-b', 'review'),
        ('b-wrong-profile', 'job-b', 'review')]:
    f = EachJobBindsItsOwnDeploymentAndLine('runTest')
    result = {'case': label}
    try:
        f.setUp()
        store, control, composed = f.serving_two()
        work = f.work if job_id == 'job-a' else SECOND_WORK
        stage = fixtures.stage(kind, work)
        if label == 'b-wrong-profile':
            stage['profile_name'] = 'wrong-profile'
        job = fixtures.job(job_id, stages=[stage],
                           input_digest=f.manifest_for(work)['manifest_digest'],
                           policy_digest=fixtures.POLICY_DIGEST)
        if label == 'b-wrong-input':
            job['input_digest'] = f.manifest_for(f.work)['manifest_digest']
        if label == 'b-wrong-policy':
            job['policy_digest'] = 'sha256:' + 'b' * 64
        submit(store, fixtures.submission(jobs=[job]))
        stage = fixtures.JobManagerCase.attempting(f, store, job_id + '/' + kind)
        try:
            composed.admit(stage, job)
            result['admitted'] = True
        except ContractRefusal as error:
            result['refusal'] = {'category': error.category, 'code': error.code,
                                 'message': error.message}
        allocation = scheduler.allocation_of(store, stage['attempt_id'])
        result['allocation'] = None if allocation is None else {
            k: allocation[k] for k in ('worker_id', 'allocation_state')}
        operation_id = composed.canonical_operation('admit', stage['offer_id'])
        result['canonical_operation'] = operation_id
        result['canonical_receipt_exists'] = composed.receipt_of(operation_id) is not None
    finally:
        f.doCleanups()
        results.append(result)
answer = {'results': results, 'elapsed_seconds': time.monotonic() - started}
Path(__file__).with_name('verification.json').write_text(json.dumps(answer, indent=2) + '\n')
print(json.dumps(answer, indent=2))
