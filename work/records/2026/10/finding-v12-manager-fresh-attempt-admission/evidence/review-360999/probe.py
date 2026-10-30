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
CANDIDATE = DOSSIER / 'findings/finding-host-exclusion-lifetime/candidate-360912'
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
    from unittest.mock import patch
    from tests.job_manager.test_fresh_attempt import TheConnectedRetry
    from tools import job_manager as command
    from tools.fresh_attempt_ports import DeploymentBinding
    results={};start=time.monotonic()
    manifest=json.loads((CANDIDATE/'MANIFEST.json').read_text())
    results['manifest']=hashlib.sha256((CANDIDATE/'MANIFEST.json').read_bytes()).hexdigest()
    for name,entry in manifest['MEMBERS'].items():
        assert hashlib.sha256((CANDIDATE/name).read_bytes()).hexdigest()==entry['candidate']
        assert (not (ROOT/name).exists()) if entry['new_path'] else hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['canonical_base']
    case=TheConnectedRetry();case.setUp()
    try:
        case.failed();before=api.submission_of(case.jobs,'sub-job-a');config_before=case.binding.configuration()
        argv=['--store',case.places['job_store'],'--incarnation','joined-cli','--authority-uuid',case.uuid,'fresh-attempt','--prior-job','job-a','--control',case.places['control_store'],'--authority',case.places['authority_store'],'--instance',case.state]
        stream=io.StringIO()
        with patch.object(command,'_ReadOnly',return_value=case.acts), __import__('contextlib').redirect_stderr(io.StringIO()):command.main(argv,clock=case.clock,stream=stream)
        answer=json.loads(stream.getvalue())
        config_after=case.binding.configuration()
        assert before==api.submission_of(case.jobs,'sub-job-a')
        assert config_before['workers']==config_after['workers']
        doc=json.loads(api.submission_of(case.jobs,'sub-job-a-retry-2')['document'])
        assert doc['jobs'][0]['execution_limits']=={'provider_turn_seconds':3600,'verification_command_seconds':900}
        assert all(answer['binding']['serving'][role] for role in ['implementation','review'])
        with JobStore.open(case.places['job_store'],authority_uuid=case.uuid,incarnation='joined-reopened',clock=case.clock) as store:
            with patch.object(DeploymentBinding,'bind',side_effect=AssertionError('replay cannot rebind')):
                replay=case.admit(store=store)
        assert replay==answer
        results['cli_and_restart']=dict(answer=answer,prior_unchanged=True,workers_unchanged=True,reopened_replay_equal=True,limits=doc['jobs'][0]['execution_limits'])
    finally:case.doCleanups()
    case=TheConnectedRetry();case.setUp()
    try:
        case.failed();real=DeploymentBinding.bind;calls=[]
        def cut(self,*args,**kwargs):
            value=real(self,*args,**kwargs);calls.append(args[0]);raise RuntimeError('cut after actual bootstrap binding publication')
        with patch.object(DeploymentBinding,'bind',cut):
            try:case.admit()
            except RuntimeError:pass
            else:raise AssertionError('cut not reached')
        assert case.binding.binding_of('job-a-retry-2') is not None
        assert api.submission_of(case.jobs,'sub-job-a-retry-2') is None
        with JobStore.open(case.places['job_store'],authority_uuid=case.uuid,incarnation='recovery',clock=case.clock) as store:
            try:case.admit(store=store)
            except ContractRefusal as exc:results['different_incarnation_incomplete_refusal']=str(exc)
            else:raise AssertionError('different incarnation took unresolved intent')
        with JobStore.open(case.places['job_store'],authority_uuid=case.uuid,incarnation='jobs-1',clock=case.clock) as store:
            with patch.object(DeploymentBinding,'bind',side_effect=AssertionError('published binding must not repeat')):
                answer=case.admit(store=store)
                assert case.admit(store=store)==answer
        assert len(calls)==1
        results['real_binding_cut']=dict(job_id=answer['job_id'],publication_calls=len(calls),recovered=True)
    finally:case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
