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
CANDIDATE = DOSSIER / 'candidate-359603'
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
from tests.job_manager.test_fresh_attempt import FreshAttemptCase, FakeBinding, TheRealInstanceGuard, TheConnectedRetry, FRESH
from baton_v12.job_manager import JobStore
from baton_v12.job_manager import submission as api
from tests.job_manager.fixtures import UUID, submission, job
from baton_v12.worker_manager import ControlStore
from tools.fresh_attempt_ports import HostExclusion, InstanceOwnership

def main():
    results={}
    start=time.monotonic()
    mp=CANDIDATE/'MANIFEST.json'
    manifest=json.loads(mp.read_text())
    results['manifest_sha256']=hashlib.sha256(mp.read_bytes()).hexdigest()
    results['pins']={rel:hashlib.sha256((CANDIDATE/rel).read_bytes()).hexdigest()==m['candidate'] for rel,m in manifest['MEMBERS'].items()}
    results['bases']={rel:(not (ROOT/rel).exists()) if m['new'] else hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==m['base'] for rel,m in manifest['MEMBERS'].items()}
    assert all(results['pins'].values()) and all(results['bases'].values())
    with (Path(__file__).parent/'FOCUSED.txt').open('w') as stream:
        t=time.monotonic()
        run=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt'))
        results['focused']=dict(run=run.testsRun,failures=len(run.failures),errors=len(run.errors),seconds=time.monotonic()-t)
    case=FreshAttemptCase();case.setUp()
    try:
        case.prior()
        class Taking(FakeBinding):
            def bind(self,job_id,*,like,work_id):
                with JobStore.open(case.job_path,authority_uuid=UUID,incarnation='ordinary',clock=case.clock) as store:
                    self.submitted=api.submit(store,submission(submission_id='sub-'+job_id,jobs=[job('other-job')]))
                return super().bind(job_id,like=like,work_id=work_id)
        binding=Taking()
        try: value=case.admitted(binding=binding)
        except Exception as exc: value=str(exc)
        results['submission_id_collision']=dict(ordinary=binding.submitted,retry=value,effects=binding.added)
    finally:case.doCleanups()
    case=TheRealInstanceGuard();case.setUp()
    try:
        owning=InstanceOwnership.of(case.control_store,case.configuration)
        place=case.configuration['workers'][0]['deployment']['workspace_storage']
        first=owning.held();second=owning.held()
        first.__enter__()
        second.__enter__()
        try:
            before=case.forked(place)
            first.__exit__(None,None,None)
            after=case.forked(place)
            results['overlapping_guard_lifetimes']=dict(before=before,after_first_exit_while_second_active=after)
        finally:second.__exit__(None,None,None)
    finally:case.doCleanups()
    case=TheConnectedRetry();case.setUp()
    try:
        case.failed()
        other_path=str(Path(case.state)/'unrelated-control.sqlite3')
        configuration=case.binding.configuration()
        with ControlStore.open(other_path,incarnation='other-host',clock=case.clock) as other:
            # Exactly the CLI composition: expected is its independently supplied --control.
            exclusion=HostExclusion(other,expected=other_path)
            ownership=InstanceOwnership.of(other,configuration)
            value=case.admit(exclusion=exclusion,ownership=ownership)
            results['wrong_control']=dict(actual=other_path,instance_control=case.places['control_store'],job_id=value['job_id'],exclusion=value['exclusion'])
    finally:case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
