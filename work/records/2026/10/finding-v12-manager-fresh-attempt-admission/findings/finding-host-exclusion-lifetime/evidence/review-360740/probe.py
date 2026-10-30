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
CANDIDATE = DOSSIER / 'candidate-360582'
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
    from tests.job_manager.test_fresh_attempt import TheHostIsThisInstanceS, TheExclusionOutlivesEveryBorrower
    from baton_v12.worker_manager import workspaces
    import select, signal
    results={}; start=time.monotonic()
    results['focused_evidence']='FOCUSED.txt from preceding run; no rerun'
    a=TheHostIsThisInstanceS(); a.setUp()
    b=TheHostIsThisInstanceS(); b.setUp()
    try:
        a.failed()
        answer=a.admit(exclusion=b.exclusion,authorization=b.authorization,binding=b.binding,ownership=b.ownership)
        results['different_job_store']=dict(job_store=a.places['job_store'],declared_job_store=b.bound['job_store'],authority_equal=a.uuid==b.uuid,answer=answer,published_in_other=b.binding.binding_of('job-a-retry-2'))
        assert answer['job_id']=='job-a-retry-2'
    finally: b.doCleanups(); a.doCleanups()
    case=TheExclusionOutlivesEveryBorrower();case.setUp()
    try:
        context=case.owning().held();guard=context.__enter__()
        serving=workspaces.hold_manager_instance(case.control_store,case.place())
        context.__exit__(None,None,None)
        results['serving_acquired_during_borrow']=dict(same_guard=serving is guard,descriptor=serving._descriptor,contender=case.forked(case.place()))
        serving.release()
        locked=threading.Event();release=threading.Event()
        def locker():
            with workspaces._BORROWING:
                locked.set();release.wait(10)
        thread=threading.Thread(target=locker);thread.start();assert locked.wait(5)
        read,write=os.pipe();pid=os.fork()
        if pid==0:
            os.close(read)
            signal.signal(signal.SIGALRM,lambda *_: os._exit(77));signal.alarm(2)
            with case.owning().held():os.write(write,b'acquired')
            os._exit(0)
        os.close(write)
        release.set();thread.join(5)
        _,status=os.waitpid(pid,0)
        data=os.read(read,100);os.close(read)
        results['fork_during_bookkeeping']=dict(child_exit=os.waitstatus_to_exitcode(status),message=data.decode())
        assert os.waitstatus_to_exitcode(status)==77
    finally:case.doCleanups()
    results['seconds']=time.monotonic()-start
    (Path(__file__).parent/'PROBE.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
