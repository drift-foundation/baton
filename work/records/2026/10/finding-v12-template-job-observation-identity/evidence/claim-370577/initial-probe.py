"""Diagnostic only: actual context methods and launch boundary, fixture readers.
No database, engine, provider, installed deployment, or source mutation.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from tools import single_worker
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import launch, exchange

started = time.monotonic()
root = tempfile.mkdtemp(prefix='w370555-', dir='/var/tmp/baton-w257624')
limits = execution_limits.resolved({})
installed = {'input_manifest': {'manifest_digest': 'sha256:' + 'a' * 64}, 'policy_digest': 'sha256:' + 'c' * 64}
composed = dict(installed, input_manifest={'manifest_digest': 'sha256:' + 'b' * 64})

def reader(**operands):
    return dict(operands, job_input_digest='sha256:' + 'd' * 64,
                job_policy_digest='sha256:' + 'c' * 64,
                execution_limits=limits, execution_limits_digest=digest(limits))

results = []
for name, delivered in [('composed', composed), ('legacy-installed', installed)]:
    worker = object.__new__(single_worker._SingleWorker)
    worker.given = installed
    # Fixture supplies task-composition output; production _given_for and
    # both production _job_execution methods are exercised unchanged.
    worker._for_job = lambda stage: (delivered['input_manifest'], b'fixture-task')
    worker.given = dict(installed, task_bytes=b'fixture-task')
    worker.execution_context = reader
    observer = object.__new__(single_worker._Observation)
    observer.given = worker.given
    observer.execution_context = reader
    stage = {'job_id': 'job-diagnostic', 'attempt_id': 'attempt-' + name}
    served = worker._job_execution(stage)
    observed = observer._job_execution(stage)
    kwargs = dict(attempt_id=stage['attempt_id'], session='session-diagnostic',
                  contract='diagnostic contract', role='implementation',
                  transport=exchange.EXCHANGE_TRANSPORT, workspace_group=os.getgid())
    launch.materialize(root, **kwargs, job_execution=served)
    place = Path(root) / stage['attempt_id'] / 'launch.json'
    before = hashlib.sha256(place.read_bytes()).hexdigest()
    assert launch.adopt(root, **kwargs, job_execution=served) is not None
    refusal = None
    try:
        launch.adopt(root, **kwargs, job_execution=observed)
    except ContractRefusal as error:
        refusal = {'category': error.category, 'code': error.code, 'message': str(error)}
    assert (refusal is not None) == (name == 'composed')
    if refusal:
        assert refusal['category'] == 'policy' and refusal['code'] == 'denied'
    assert before == hashlib.sha256(place.read_bytes()).hexdigest()
    results.append({'case': name, 'different_context_members': [k for k in served if served[k] != observed[k]],
                    'serving_adoption': 'accepted', 'observation_adoption': refusal or 'accepted',
                    'launch_bytes_unchanged': True})
print(json.dumps({'schema':'w370555-diagnostic/1','root_retained':root,
                  'seconds':time.monotonic()-started,'results':results,
                  'limitations':'Fixture task and Job readers; no admission/store/installed-code/provider proof.'}, indent=2))
