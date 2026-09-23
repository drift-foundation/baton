from pathlib import Path
import sys,unittest,time,json,hashlib,io
from unittest.mock import patch
D=Path(__file__).resolve().parent; R=D.parents[4]; S=D.parent/'finding-v12-single-implementation-proof'
sys.path[:0]=[str(D),str(S),str(R/'v12/python/src'),str(R/'v12/python')]
import test_review_supervisor as t
import review_supervisor as s
from baton_v12.job_manager import review_driver
from baton_v12.worker_manager import boundaries
started=time.monotonic()
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(m) for m in ('test_attachment','test_review_bindings','test_review_supervisor'))
with (D/'review-tests-247222.log').open('w') as log: result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
case=t.PacketCase();case.setUp()
try:
 p=case.written(supervisor={"path":s.__file__,"sha256":hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest()})
 stream=io.StringIO()
 code=s.main(['--packet',p,'--incarnation','review-probe'],stream=stream,image_inspect=lambda ref: (_ for _ in ()).throw(AssertionError('must refuse before engine')))
 startup={"exit":code,"message":stream.getvalue()}
finally:case.doCleanups()
case=t.TheVerdictEvidenceReadsTheFrozenOutput('test_no_review_attempt_at_all_is_a_shortfall');case.setUp()
try:
 attempt=case.attached(); packet=case.packet()
 # Interface-shape probe only: mock the public reader return, not a provider receipt.
 answer={"attachment_id":"fixture","attempt_id":attempt,"checkpoint_id":case.checkpoint['checkpoint_id'],"verdict":"accepted","base":packet['subject']['base_object'],"head":packet['subject']['head_object'],"tree":packet['subject']['tree_object'],"result_id":"fixture","result_digest":"sha256:"+'a'*64}
 with patch.object(review_driver,'review_verdict_from_result',return_value=answer):
  evidence=s._verdict_evidence(case.store,packet,{attempt:'review'},{})
finally:case.tearDown();case.doCleanups()
try:boundaries.instant('now','operator clock');clock='accepted'
except Exception as exc:clock=str(exc)
output={"claim":247222,"tests":result.testsRun,"passed":result.wasSuccessful(),"startup":startup,"public_verdict_shape_probe":evidence,"operator_clock_probe":clock,"elapsed_seconds":time.monotonic()-started,"sha256":{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('review_supervisor.py','test_review_supervisor.py','review_bindings.py','OPERATOR-239533.md','SELECTIONS-239533.json')}}
(D/'review-checks-247222.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
