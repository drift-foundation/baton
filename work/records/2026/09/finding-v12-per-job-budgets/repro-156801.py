"""Proposed main pooled fixture setup; unchanged assertions, fake providers."""
import difflib, hashlib, json, pathlib, sys, types, unittest
from baton_v12.job_manager import submission
record = pathlib.Path(__file__).parent
source = pathlib.Path('/home/sl/src/baton/v12/python/tests/tools/test_stage_execution.py')
original = source.read_text()
anchor = ('            transport=exchange.EXCHANGE_TRANSPORT,\n'
          '            workspace_group=single_worker.configured_workspace_group(control))')
assert original.count(anchor) == 1
changed = original.replace(anchor, '            transport=exchange.EXCHANGE_TRANSPORT,\n'
    '            job_execution=_review_context(self, role, attempt_id),\n'
    '            workspace_group=single_worker.configured_workspace_group(control))')
def context(case, role, attempt_id):
    composed = case.composed_for(role)
    workers = [one['operations']._worker for one in composed.workers
               if attempt_id in (getattr(getattr(one['operations']._worker, 'stage', None), '_prepared', None) or {})]
    assert len(workers) == 1
    worker = workers[0]
    jobs = worker.stage.deployment.jobs
    stages = [stage for stage in submission.stage_rows(jobs) if stage['attempt_id'] == attempt_id]
    assert len(stages) == 1
    return submission.job_execution_context(jobs, stages[0]['job_id'], attempt_id=attempt_id,
        runtime_input_digest=worker.given['input_manifest']['manifest_digest'],
        runtime_policy_digest=worker.given['policy_digest'])
(record / 'fixture-156801.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True), changed.splitlines(keepends=True), fromfile=str(source), tofile='isolated-copy-with-_review_context-from-repro-156801.py')))
print(json.dumps({'source_sha256': hashlib.sha256(original.encode()).hexdigest(), 'proposed_source_sha256': hashlib.sha256(changed.encode()).hexdigest(), 'helper': 'context in repro-156801.py', 'changed_adopt_sites': 1}), flush=True)
module = types.ModuleType('tests.tools._w156162_review')
module.__file__ = str(source)
module.__package__ = 'tests.tools'
module._review_context = context
sys.modules[module.__name__] = module
exec(compile(changed, str(source), 'exec'), module.__dict__)
selectors = ['TheComposedImplementationHalfRunsOnOrdinaryTicks.test_one_submitted_job_reaches_a_completed_implementation_stage', 'TheComposedJobTraversesReviewAndAcceptance.test_the_reviewers_own_verdict_completes_the_review_stage', 'TwoBoundJobsTraverseServingAndCorrection.test_the_second_job_reaches_its_own_reviewer_and_verdict']
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name, module) for name in selectors)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
