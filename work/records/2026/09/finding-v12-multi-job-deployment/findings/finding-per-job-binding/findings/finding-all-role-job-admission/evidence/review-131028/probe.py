"""Public all-role admission, mismatch and reconstruction controls."""
import json
import unittest
from tests.tools.test_stage_execution import EachJobBindsItsOwnDeploymentAndLine, EveryJobRoleIsValidatedBeforeAllocation, SECOND_WORK
from tests.job_manager import fixtures
from baton_v12.job_manager import submit, scheduler, submission
from baton_v12.contracts import ContractRefusal

results = []
cases = [(j + '-' + k, j, k, None)
         for j in ('job-a', 'job-b')
         for k in ('implementation', 'review', 'integration')]
cases += [('b-integration-' + bad, 'job-b', 'integration', bad)
          for bad in ('input', 'policy', 'profile', 'profile_digest', 'work')]
cases += [('unknown-integration', 'job-unknown', 'integration', None)]
for label, job_id, kind, bad in cases:
    f = EachJobBindsItsOwnDeploymentAndLine('runTest')
    try:
        f.setUp()
        store, control, composed = f.serving_two()
        work = f.work if job_id == 'job-a' else SECOND_WORK
        stage_doc = fixtures.stage(kind, work)
        if bad == 'profile':
            stage_doc['profile_name'] = 'wrong-profile'
        if bad == 'profile_digest':
            stage_doc['profile_digest'] = 'sha256:' + 'f' * 64
        if bad == 'work':
            stage_doc['work_id'] = f.work
        job = fixtures.job(job_id, stages=[stage_doc],
                           input_digest=f.manifest_for(work)['manifest_digest'],
                           policy_digest=fixtures.POLICY_DIGEST)
        if bad == 'input':
            job['input_digest'] = f.manifest_for(f.work)['manifest_digest']
        if bad == 'policy':
            job['policy_digest'] = 'sha256:' + 'b' * 64
        submit(store, fixtures.submission(jobs=[job]))
        stage = fixtures.JobManagerCase.attempting(f, store, job_id + '/' + kind)
        refusal = None
        try:
            composed.admit(stage, submission.job_of(store, job_id))
        except ContractRefusal as error:
            refusal = {'category': error.category, 'code': error.code,
                       'message': error.message}
        allocation = scheduler.allocation_of(store, stage['attempt_id'])
        op = composed.canonical_operation('admit', stage['offer_id'])
        receipt = composed.receipt_of(op)
        expected = bad is None and job_id != 'job-unknown'
        assert (refusal is None) == expected, (label, refusal)
        assert (allocation is not None) == expected, (label, allocation)
        assert (receipt is not None) == expected, (label, receipt)
        if expected:
            worker = kind + '-worker' + ('-b' if job_id == 'job-b' and kind != 'integration' else '')
            assert allocation['worker_id'] == worker, (label, allocation)
        results.append({'case': label, 'refusal': refusal,
                        'allocation_worker': None if allocation is None else allocation['worker_id'],
                        'canonical_receipt_exists': receipt is not None})
    finally:
        f.doCleanups()

selected = [
    'test_one_integrator_serves_two_jobs_serially_and_says_so',
    'test_an_incompatible_stage_does_not_consume_capacity_a_job_needs',
    'test_a_recorded_allocation_that_cannot_serve_the_job_is_not_admitted']
suite = unittest.TestSuite(EveryJobRoleIsValidatedBeforeAllocation(name) for name in selected)
answer = unittest.TextTestRunner(verbosity=2).run(suite)
assert answer.wasSuccessful()
print(json.dumps({'public_admission_controls': results, 'focused_regressions': selected}, indent=2))
