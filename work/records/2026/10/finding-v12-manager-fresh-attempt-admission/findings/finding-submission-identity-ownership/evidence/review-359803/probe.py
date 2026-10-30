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

ROOT = Path(__file__).resolve().parents[9]
DOSSIER = Path(__file__).resolve().parents[2]
CANDIDATE = DOSSIER / 'candidate-359749'
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
from tests.job_manager.test_fresh_attempt import FreshAttemptCase, FakeExclusion, FakeAuthorization, FakeBinding, FakeOwnership, PRIOR, FRESH
from baton_v12.job_manager import JobStore, fresh_attempt
from baton_v12.job_manager import submission as api
from tests.job_manager.fixtures import UUID, submission, job
from baton_v12.contracts import ContractRefusal

def main():
    results={};start=time.monotonic()
    mp=CANDIDATE/'MANIFEST.json';manifest=json.loads(mp.read_text())
    results['manifest_sha256']=hashlib.sha256(mp.read_bytes()).hexdigest()
    results['pins']={rel:hashlib.sha256((CANDIDATE/rel).read_bytes()).hexdigest()==m['candidate'] for rel,m in manifest['MEMBERS'].items()}
    results['bases']={rel:(not (ROOT/rel).exists()) if m['new_path'] else hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==m['canonical_base'] for rel,m in manifest['MEMBERS'].items()}
    parent=DOSSIER.parents[1]/'candidate-359603'
    results['changed_from_parent']=[rel for rel in manifest['MEMBERS'] if (CANDIDATE/rel).read_bytes()!=(parent/rel).read_bytes()]
    assert all(results['pins'].values()) and all(results['bases'].values())
    with (Path(__file__).parent/'FOCUSED.txt').open('w') as stream:
        t=time.monotonic()
        run=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt'))
        results['focused']=dict(run=run.testsRun,failures=len(run.failures),errors=len(run.errors),seconds=time.monotonic()-t)
    case=FreshAttemptCase();case.setUp()
    try:
        case.prior()
        try: api.submit(case.jobs,submission(submission_id='sub-'+FRESH,jobs=[job(PRIOR)]))
        except ContractRefusal as exc: results['earlier_refusal']=dict(message=str(exc),durable=exc.durable)
        results['earlier_submission_row']=api.submission_of(case.jobs,'sub-'+FRESH)
        try: results['retry']=case.admitted()
        except Exception as exc: results['retry']=str(exc)
        results['effects_after_prior_refusal']=case.binding.added
        results['intent_after_prior_refusal']=fresh_attempt.fresh_attempt_of(case.jobs,FRESH)
    finally:case.doCleanups()
    case=FreshAttemptCase();case.setUp()
    try:
        case.prior();case.prior(job_id='quickstart-x')
        gate=threading.Barrier(2,timeout=5)
        class Synchronized(FakeExclusion):
            def evidence_of(self,ids):
                answer=super().evidence_of(ids)
                if len(self.asked)==1:gate.wait()
                return answer
        def racing(prior):
            with JobStore.open(case.job_path,authority_uuid=UUID,incarnation=prior,clock=case.clock) as store:
                binding=FakeBinding()
                try:
                    value=fresh_attempt.admit(store,case.acts,prior_job_id=prior,submission_id='same-submission',exclusion=Synchronized(),authorization=FakeAuthorization(),binding=binding,ownership=FakeOwnership())
                    outcome='admitted'
                except Exception as exc:outcome=str(exc)
                return dict(prior=prior,outcome=outcome,effects=binding.added)
        with concurrent.futures.ThreadPoolExecutor(2) as pool:results['concurrent_retry_names']=list(pool.map(racing,[PRIOR,'quickstart-x']))
    finally:case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
