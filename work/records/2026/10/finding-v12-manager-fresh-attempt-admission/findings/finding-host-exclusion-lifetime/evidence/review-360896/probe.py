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
CANDIDATE = DOSSIER / 'candidate-360765'
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
    from tests.job_manager.test_fresh_attempt import TheExclusionOutlivesEveryBorrower
    from baton_v12.worker_manager import workspaces
    from unittest.mock import patch
    results={}; start=time.monotonic()
    with (Path(__file__).parent/'FOCUSED.txt').open('w') as stream:
        t=time.monotonic();run=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromName('tests.job_manager.test_fresh_attempt'))
        results['focused']=dict(run=run.testsRun,failures=len(run.failures),errors=len(run.errors),seconds=time.monotonic()-t)
    case=TheExclusionOutlivesEveryBorrower();case.setUp()
    try:
        guard=workspaces.hold_manager_instance(case.control_store,case.place())
        paused=threading.Event();proceed=threading.Event();actual=workspaces.ManagerInstanceGuard._disown
        def delayed(self):
            if threading.current_thread().name=='releasing':
                paused.set();assert proceed.wait(5)
            return actual(self)
        with patch.object(workspaces.ManagerInstanceGuard,'_disown',delayed):
            thread=threading.Thread(target=guard.release,name='releasing');thread.start();assert paused.wait(5)
            next_guard=workspaces.hold_manager_instance(case.control_store,case.place())
            before=next_guard._descriptor
            proceed.set();thread.join(5);assert not thread.is_alive()
            results['final_release_vs_new_holder']=dict(same_guard=next_guard is guard,before_descriptor=before,after_descriptor=next_guard._descriptor,holders=workspaces.holders_of(case.place()),contender=case.forked(case.place()))
            assert next_guard._descriptor is None
            assert results['final_release_vs_new_holder']['contender']['outcome']=='held'
            next_guard.release()
    finally:case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
