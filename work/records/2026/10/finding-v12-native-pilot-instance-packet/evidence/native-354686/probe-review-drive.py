import sys, json
from unittest import TestLoader, TextTestRunner, TestCase
sys.argv=[sys.argv[0]]
from tests.tools.test_stage_execution import ServingCase
from tests.job_manager import fixtures
from baton_v12.contracts import job_input_identity
from baton_v12.job_manager import submit, status, reconcile
from baton_v12.worker_manager import tokens
from tools import stage_execution

class Probe(ServingCase):
    def runTest(self): pass

c = Probe('runTest'); c.setUp()
try:
    job, control, composed = c.serving()
    roles = {one['role']: one for one in composed.workers}
    print('roles composed:', sorted(roles))
    rev = roles['review']['operations']
    print('review worker launch_role:', rev._worker.given.get('launch_role'))
    print('composed has launch:', hasattr(composed, 'launch'))
    # try submitting a review-kind stage job into this store
    sub = fixtures.submission(jobs=[fixtures.job(
        input_digest=job_input_identity(rev._worker.given['input_manifest']),
        policy_digest=rev._worker.given['policy_digest'],
        stages=[fixtures.stage(kind='review', work_id=c.work,
                               profile_name=rev._worker.given['profile_name'],
                               profile_digest=rev._worker.given['profile_digest'])])])
    sub['schema']='baton.v12.job-submission/2'
    sub['jobs'][0]['execution_limits']={'provider_turn_seconds':3600,'verification_command_seconds':900}
    submit(job, sub)
    print('submitted review-stage job')
    for i in range(4):
        report = reconcile(job, rev, now=fixtures.NOW)
        acts = report.get('acts') if isinstance(report, dict) else None
        print(' tick', i, 'acts:', json.dumps(acts)[:700] if acts else report)
        p = status(job, rev, observed_at=fixtures.NOW)
        st = p['jobs'][0]['stages'][0]
        print('      state', st['state'])
        if st['state']=='waiting': break
    rows=list(control._connection.execute('SELECT runtime_attempt_id, workspace_device, workspace_inode FROM attempts'))
    print('attempt rows:', len(rows))
    for r in rows:
        r=dict(r)
        dom=tokens.domain_of('workspace', tokens.workspace_identity(r))
        t=tokens.token_of(control, dom, 1)
        print('  token seconds:', t and t.get('seconds'))
finally:
    c.doCleanups()
