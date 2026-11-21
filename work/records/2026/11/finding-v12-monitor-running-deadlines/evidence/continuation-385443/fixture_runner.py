"""Exactly the two owner-approved compatibility cases. No changed assertions."""
import os,sys,json,pathlib,traceback,unittest
from unittest import mock
from tests.tools.test_job_viewer import TheRealObservationReaderReachesTheView as Cases
import baton_worker
from tests.manager import disk_roots
ROOT=pathlib.Path(os.environ['RUN_ROOT']);LOG=ROOT/'diagnostics.jsonl'
def record(value):
 with LOG.open('a') as out:out.write(json.dumps(value)+'\n')
original_root=disk_roots.disk_backed_under
original_fault=baton_worker._faulted

def root(case):
 answer=original_root(case);record({'case':case.id(),'fixture_root':answer});return answer

def fault(*args,**kwargs):
 record({'event':'worker-fault','args':list(args),'kwargs':kwargs,'traceback':traceback.format_exc()})
 return original_fault(*args,**kwargs)
names=('test_a_foreign_job_still_refuses_against_the_real_reader','test_the_view_renders_the_real_model_free_completion')
with mock.patch.object(disk_roots,'disk_backed_under',root),mock.patch.object(baton_worker,'_faulted',fault):
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Cases(name) for name in names))
raise SystemExit(not result.wasSuccessful())
