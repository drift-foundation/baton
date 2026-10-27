"""Read-only-to-repository fixture probe of production pool profile injection."""
import json,subprocess
from tests.tools.test_stage_execution import ServingCase
from tests.tools.test_single_worker import Engine
from tests.job_manager.test_review_driver import Profile
from tests.job_manager import fixtures
from tools import stage_execution
original=subprocess.Popen
def guarded(argv,*args,**kwargs):
 if argv and str(argv[0]).split('/')[-1]=='git': raise AssertionError('unexpected Git process')
 return original(argv,*args,**kwargs)
subprocess.Popen=guarded
case=ServingCase(); case.setUp()
try:
 jobs,control=case.stores('review-profile-injection')
 document=case.composed_document(checkpoint_profile='reference')
 operations=stage_execution.operations_from(document,jobs,control,engine_run=Engine(),credential_provider=lambda *_:case.secret,clock=lambda:fixtures.NOW,checkout=case.checkout,checkpoint_profile=Profile())
 try: print(json.dumps({'composition_succeeded':True,'worker_count':len(operations.workers),'profile':'reference','scope':'composition only; not pool execution acceptance'}))
 finally: operations.close()
finally:
 case.doCleanups(); subprocess.Popen=original
