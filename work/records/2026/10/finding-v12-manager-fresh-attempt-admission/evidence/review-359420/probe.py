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
CANDIDATE = DOSSIER / 'candidate-359299'
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

# Independently repeat the bounded author suite using the pinned overlay.
with (Path(__file__).parent / 'FOCUSED.txt').open('w') as stream:
    suite = unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt')
    suite_start = time.monotonic()
    run = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    results['focused'] = {'run': run.testsRun, 'failures': len(run.failures),
        'errors': len(run.errors), 'seconds': time.monotonic() - suite_start}

# Identical requests replay the intent but both continue to external bind.
case = FreshAttemptCase()
case.setUp()
try:
    case.prior()
    rendezvous = threading.Barrier(2)
    class RacingBinding(FakeBinding):
        def binding_of(self, job_id):
            found = super().binding_of(job_id)
            rendezvous.wait(timeout=10)
            return found
    shared = RacingBinding()
    def run_same(ordinal):
        with JobStore.open(case.job_path, authority_uuid=UUID, incarnation=f'review-{ordinal}', clock=case.clock) as store:
            try:
                value = fresh_attempt.admit(store, case.acts, prior_job_id=PRIOR,
                    exclusion=FakeExclusion(), authorization=FakeAuthorization(), binding=shared)
                return {'outcome': 'admitted', 'job_id': value['job_id']}
            except Exception as exc:
                return {'outcome': 'refused', 'type': type(exc).__name__, 'message': str(exc)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results['same_request_race'] = list(pool.map(run_same, (1, 2)))
    results['same_request_bind_effects'] = shared.added
finally:
    case.doCleanups()

# An ordinary submit can occupy an already-reserved fresh Job identity.
from baton_v12.job_manager import submission as submission_api
from tests.job_manager.fixtures import submission, job, stage, WORK_A
case = FreshAttemptCase()
case.setUp()
try:
    case.prior()
    class CompetingSubmission(FakeBinding):
        def bind(self, job_id, *, like, work_id):
            with JobStore.open(case.job_path, authority_uuid=UUID, incarnation='ordinary', clock=case.clock) as store:
                self.ordinary_result = submission_api.submit(store, submission(
                    submission_id='ordinary-competitor', jobs=[job(job_id,
                        stages=[stage('implementation', WORK_A)])]))
            return super().bind(job_id, like=like, work_id=work_id)
    binding = CompetingSubmission()
    try:
        case.admitted(binding=binding)
        outcome = 'admitted'
    except Exception as exc:
        outcome = str(exc)
    results['ordinary_collision_after_reserve'] = {'retry_outcome': outcome,
        'ordinary_submission': binding.ordinary_result,
        'binding_effects': binding.added,
        'intents': [{k: row[k] for k in ('job_id', 'state')} for row in fresh_attempt.fresh_attempt_rows(case.jobs)]}
finally:
    case.doCleanups()

results['seconds'] = time.monotonic() - started
(Path(__file__).parent / 'PROBE.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))

