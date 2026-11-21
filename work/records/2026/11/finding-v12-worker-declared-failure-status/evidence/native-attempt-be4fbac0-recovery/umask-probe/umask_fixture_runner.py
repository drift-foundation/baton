"""Exactly the two owner-approved compatibility cases, under a chosen umask, with the
real posture check observed. No changed assertions; no product edit: the posture seam
is wrapped in this harness only, to RETAIN what the product saw and said."""
import os,sys,json,pathlib,traceback,unittest
from unittest import mock
os.umask(int(os.environ['PROBE_UMASK'],8))
from tests.tools.test_job_viewer import TheRealObservationReaderReachesTheView as Cases
import baton_worker
from tests.manager import disk_roots
from baton_v12.integration import oci_delivery
ROOT=pathlib.Path(os.environ['RUN_ROOT']);LOG=ROOT/'diagnostics.jsonl';POSTURE=ROOT/'posture.jsonl'
def record(value,where=LOG):
 with where.open('a') as out:out.write(json.dumps(value)+'\n')
original_root=disk_roots.disk_backed_under;original_fault=baton_worker._faulted;original_posture=oci_delivery.prove_target_posture
def root(case):
 answer=original_root(case);record({'case':case.id(),'fixture_root':answer,'umask':oct(os.umask(0)) if False else os.environ['PROBE_UMASK']});return answer
def fault(*args,**kwargs):
 record({'event':'worker-fault','args':list(args),'kwargs':kwargs,'traceback':traceback.format_exc()});return original_fault(*args,**kwargs)
def posture(boundary,workspace_group):
 seen={'event':'prove_target_posture','umask':os.environ['PROBE_UMASK']}
 try:
  held=oci_delivery.compatible_target(boundary);seen['target']={'place':held['place'],'gid':held['gid'],'mode':oct(held['mode'])}
 except Exception as error:seen['target_error']=str(error)
 try:
  answer=original_posture(boundary,workspace_group);seen['outcome']='accepted';record(seen,POSTURE);return answer
 except Exception as error:
  seen['outcome']='refused';seen['refusal']=str(error);seen['type']=type(error).__name__;record(seen,POSTURE);raise
names=('test_a_foreign_job_still_refuses_against_the_real_reader','test_the_view_renders_the_real_model_free_completion')
with mock.patch.object(disk_roots,'disk_backed_under',root),mock.patch.object(baton_worker,'_faulted',fault),mock.patch.object(oci_delivery,'prove_target_posture',posture):
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Cases(name) for name in names))
record({'event':'result','umask':os.environ['PROBE_UMASK'],'tests':result.testsRun,'failures':[t.id() for t,_ in result.failures],'errors':[t.id() for t,_ in result.errors]})
raise SystemExit(not result.wasSuccessful())
