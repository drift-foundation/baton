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
CANDIDATE = DOSSIER / 'candidate-360435'
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
    from tests.job_manager.test_fresh_attempt import TheHostIsThisInstanceS, TheExclusionOutlivesEveryBorrower
    from tools.fresh_attempt_ports import HostExclusion
    from baton_v12.worker_manager import workspaces
    results = {}; start = time.monotonic()
    with (Path(__file__).parent/'FOCUSED.txt').open('w') as stream:
        t = time.monotonic()
        run = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt'))
        results['focused'] = dict(run=run.testsRun, failures=len(run.failures), errors=len(run.errors), seconds=time.monotonic()-t)
    case = TheHostIsThisInstanceS(); case.setUp()
    try:
        case.failed()
        other = case.other_control()
        answer = case.admit(exclusion=HostExclusion(other))
        results['unbound_real_host'] = dict(outcome=answer, supplied=other.database, installed=case.places['control_store'], published=case.binding.binding_of('job-a-retry-2'))
        assert answer['job_id']=='job-a-retry-2'
    finally: case.doCleanups()
    case = TheExclusionOutlivesEveryBorrower(); case.setUp()
    try:
        first = case.owning().held(); first.__enter__()
        observed = threading.Event(); proceed = threading.Event(); entered = threading.Event(); finish = threading.Event()
        actual = workspaces.hold_manager_instance
        answers = {}
        def paused(store, place):
            guard = actual(store, place)
            observed.set()
            assert proceed.wait(5)
            return guard
        def second():
            try:
                with case.owning().held() as guard:
                    answers['guard_descriptor'] = guard._descriptor
                    answers['borrowers'] = workspaces.borrowers_of(case.place())
                    entered.set()
                    assert finish.wait(10)
            except BaseException as exc:
                answers['error'] = repr(exc); entered.set()
        with patch.object(workspaces, 'hold_manager_instance', side_effect=paused):
            worker=threading.Thread(target=second); worker.start()
            assert observed.wait(5)
            first.__exit__(None,None,None)
            proceed.set()
            assert entered.wait(5)
            try:
                answers['contender_while_second_active'] = case.forked(case.place())
            finally:
                finish.set(); worker.join(5)
        results['concurrent_borrow_registration'] = answers
        assert answers['guard_descriptor'] is None
        assert answers['contender_while_second_active']['outcome']=='held'
    finally: case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
