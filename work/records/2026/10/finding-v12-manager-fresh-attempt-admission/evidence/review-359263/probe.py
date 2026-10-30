"""Independent deterministic probes; candidate imports over unchanged source.

No retained instance, live engine/provider, Git, or production database access.
"""
import concurrent.futures
import hashlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import threading
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[7]
DOSSIER = Path(__file__).resolve().parents[2]
CANDIDATE = DOSSIER / 'candidate-358995'
PYTHON = ROOT / 'v12/python'
sys.path[:0] = [str(PYTHON), str(PYTHON / 'src')]
os.environ['BATON_V12_STACK_TEST_ROOT'] = '/var/tmp/baton-w257624'
os.environ['BATON_V12_DISK_ROOT'] = '/var/tmp/baton-w257624'
sys.dont_write_bytecode = True

class Overlay(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        prefix = 'v12/python/src/' if fullname.startswith('baton_v12') else 'v12/python/'
        rel = prefix + fullname.replace('.', '/')
        file = CANDIDATE / (rel + '.py')
        if file.exists():
            return importlib.util.spec_from_file_location(fullname, file)
        file = CANDIDATE / rel / '__init__.py'
        if file.exists():
            return importlib.util.spec_from_file_location(fullname, file,
                submodule_search_locations=[str(file.parent), str(ROOT / rel)])

sys.meta_path.insert(0, Overlay())
from tests.job_manager.test_fresh_attempt import FreshAttemptCase, FakeAuthorization, FakeBinding, FakeExclusion, PRIOR
from baton_v12.job_manager import JobStore, fresh_attempt
from tests.job_manager.fixtures import UUID
from tools.fresh_attempt_ports import DeploymentBinding
from tests.tools.test_bootstrap import ValidFixture
from tools import bootstrap
from tools import stage_execution
from tests.job_manager.test_fresh_attempt import TheDeploymentRule

results = {}
started = time.monotonic()
manifest_path = CANDIDATE / 'MANIFEST.json'
manifest = json.loads(manifest_path.read_text())
results['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
results['pins'] = {rel: hashlib.sha256((CANDIDATE / rel).read_bytes()).hexdigest() == member['candidate']
                   for rel, member in manifest['MEMBERS'].items()}
assert all(results['pins'].values())

fixture = ValidFixture()
fixture.setUp()
try:
    document = fixture.document()
    prepared = bootstrap.prepare(document, stream=io.StringIO())
    (Path(fixture.state) / 'install-inputs.json').write_text(json.dumps(document))
    port = DeploymentBinding(fixture.state, stream=io.StringIO())
    try:
        answer = port.bind('job-a-retry-2', like='job-a', work_id=fixture.work)
        results['real_binding'] = {'outcome': 'returned', 'answer': answer}
    except Exception as exc:
        results['real_binding'] = {'outcome': 'refused', 'type': type(exc).__name__, 'message': str(exc)}
finally:
    fixture.doCleanups()

case = FreshAttemptCase()
case.setUp()
try:
    case.prior()
    barrier = threading.Barrier(2)
    class RacingAuthorization(FakeAuthorization):
        def work_of(self, work_id):
            answer = super().work_of(work_id)
            barrier.wait(timeout=10)
            return answer
    def run(job_id):
        with JobStore.open(case.job_path, authority_uuid=UUID, incarnation=job_id, clock=case.clock) as store:
            try:
                answer = fresh_attempt.admit(store, case.acts, prior_job_id=PRIOR,
                    exclusion=FakeExclusion(), authorization=RacingAuthorization(),
                    binding=FakeBinding(), job_id=job_id)
                return {'outcome': 'admitted', 'job_id': answer['job_id']}
            except Exception as exc:
                return {'outcome': 'refused', 'type': type(exc).__name__, 'message': str(exc)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results['same_prior_race'] = list(pool.map(run, ['retry-left', 'retry-right']))
    results['successors'] = [r['job_id'] for r in fresh_attempt.successors_of(case.jobs, PRIOR)]
finally:
    case.doCleanups()

case = FreshAttemptCase()
case.setUp()
try:
    case.prior()
    case.binding = FakeBinding(serving=())
    try:
        case.admitted()
    except Exception as exc:
        results['binding_refusal'] = {'type': type(exc).__name__, 'message': str(exc),
            'intents': [{k: r[k] for k in ('job_id', 'state')} for r in fresh_attempt.fresh_attempt_rows(case.jobs)],
            'binding_effects': case.binding.added}
    changed = FakeAuthorization(known=False)
    try:
        case.admitted(work_id='0000000a-W77', authorization=changed)
    except Exception as exc:
        results['changed_partial_request'] = {'type': type(exc).__name__, 'message': str(exc),
            'created_work_before_collision': changed.created}
finally:
    case.doCleanups()

case = TheDeploymentRule()
case.setUp()
try:
    given = case.given()
    binding = case.binding(given)
    given['job_bindings'] = [binding]
    stage = case.staged(given)
    wrong_job = dict(case.job_of(given), input_digest='sha256:' + 'f' * 64)
    with tempfile.TemporaryDirectory(prefix='w358969-binding-') as root:
        config_path = Path(bootstrap.layout(root)['configuration'])
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(given))
        reported = DeploymentBinding(root).serving(PRIOR, 'implementation')
        try:
            stage_execution.servable_workers(given, binding, stage, wrong_job)
            actual = 'accepted'
        except Exception as exc:
            actual = str(exc)
        results['actual_input_mismatch'] = {'adapter_reports': reported,
            'actual_submitted_input': wrong_job['input_digest'], 'real_selector': actual}
finally:
    case.doCleanups()

results['seconds'] = time.monotonic() - started
(Path(__file__).parent / 'PROBE.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
