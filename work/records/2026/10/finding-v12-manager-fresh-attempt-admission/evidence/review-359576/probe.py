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
CANDIDATE = DOSSIER / 'candidate-359459'
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
from tests.job_manager.test_fresh_attempt import FreshAttemptCase, FakeBinding, FakeOwnership, FakeExclusion, FakeAuthorization, TheRealInstanceGuard, PRIOR, FRESH
from baton_v12.job_manager import JobStore, fresh_attempt
from baton_v12.job_manager import submission as api
from tests.job_manager.fixtures import UUID, submission, job
from baton_v12.worker_manager import workspaces
from tools.fresh_attempt_ports import InstanceOwnership

def main():
    results = {}
    started = time.monotonic()
    manifest_path = CANDIDATE / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    results['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    results['pins'] = {rel: hashlib.sha256((CANDIDATE/rel).read_bytes()).hexdigest() == member['candidate'] for rel, member in manifest['MEMBERS'].items()}
    results['bases'] = {rel: (not (ROOT/rel).exists()) if member['new'] else hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() == member['base'] for rel, member in manifest['MEMBERS'].items()}
    assert all(results['pins'].values()) and all(results['bases'].values())
    with (Path(__file__).parent/'FOCUSED.txt').open('w') as stream:
        start = time.monotonic()
        run = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt'))
        results['focused'] = dict(run=run.testsRun, failures=len(run.failures), errors=len(run.errors), seconds=time.monotonic()-start)
    case = FreshAttemptCase()
    case.setUp()
    try:
        case.prior()
        gate = threading.Barrier(2, timeout=5)
        class Racing(FakeBinding):
            def binding_of(self, job_id):
                found = super().binding_of(job_id)
                gate.wait()
                return found
        shared = Racing()
        def racing(_):
            with JobStore.open(case.job_path, authority_uuid=UUID, incarnation='same-incarnation', clock=case.clock) as store:
                try:
                    return fresh_attempt.admit(store, case.acts, prior_job_id=PRIOR, exclusion=FakeExclusion(), authorization=FakeAuthorization(), binding=shared, ownership=FakeOwnership())['job_id']
                except Exception as exc:
                    return str(exc)
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results['same_incarnation'] = list(pool.map(racing, [1,2]))
        results['same_incarnation_bind_effects'] = shared.added
    finally:
        case.doCleanups()
    case = FreshAttemptCase()
    case.setUp()
    try:
        case.prior()
        class Taking(FakeBinding):
            def bind(self, job_id, *, like, work_id):
                with JobStore.open(case.job_path, authority_uuid=UUID, incarnation='ordinary', clock=case.clock) as store:
                    self.submitted = api.submit(store, submission(submission_id='sub-'+job_id, jobs=[job(job_id)]))
                return super().bind(job_id, like=like, work_id=work_id)
        binding = Taking()
        try:
            result = case.admitted(binding=binding)
        except Exception as exc:
            result = str(exc)
        results['same_submission_name'] = dict(ordinary=binding.submitted, retry=result, binding_effects=binding.added, persisted=api.job_of(case.jobs,FRESH))
    finally:
        case.doCleanups()
    case = TheRealInstanceGuard()
    case.setUp()
    try:
        place=case.configuration['workers'][0]['deployment']['workspace_storage']
        serving=workspaces.hold_manager_instance(case.control_store,place)
        try:
            before=case.forked(place)
            with InstanceOwnership.of(case.control_store,case.configuration).held() as borrowed:
                same = borrowed is serving
            after=case.forked(place)
            results['borrowed_guard'] = dict(same_object=same, before=before, after=after)
        finally:
            serving.release()
    finally:
        case.doCleanups()
    results['seconds']=time.monotonic()-started
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__ == '__main__':
    main()
