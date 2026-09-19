"""Reviewer synthetic checks with installed-deployment access blocked."""
import sys,copy,json,io,time,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT/'v12/python'),str(ROOT/'v12/python/src'),str(Path(__file__).parent/'instance-200564')]
import compose_lifecycle as c
from baton_v12.authority import Authority
from tests.manager import test_w197661_verifier as t
case=t.VerifierCase();case.setUp();v=case.verify
results={}
class Fake:
 def policy_generation(self):return 23
 def dispose(self):pass
with patch.object(Authority,'open',side_effect=AssertionError('writable Authority forbidden')) as w,patch.object(Authority,'open_readonly',return_value=Fake()) as r:
 results['pin']=c.check_policy_pin(pin=23)
 results['open_calls']={'writable':w.call_count,'readonly':r.call_count}
for kind in ['missing_provenance','missing_attempts','boolean_provenance','missing_verdict_checkpoint']:
 obs=copy.deepcopy(case.observed)
 if kind=='missing_provenance':obs.update(expected={'unrelated':True},measured={})
 if kind=='missing_attempts':
  for stage in obs['status']['jobs'][0]['stages']:stage.pop('attempt_id')
  obs['records']['verdict'].pop('attempt_id');obs['line'].pop('custody')
 if kind=='boolean_provenance':
  for key in obs['expected']:obs['expected'][key]=False;obs['measured'][key]=False
 if kind=='missing_verdict_checkpoint':obs['records']['verdict'].pop('checkpoint_id')
 results[kind]={'failed':v.judge(obs).failed}
# Demonstrate the test's unexpected dependency without touching its deployment.
suite=unittest.defaultTestLoader.loadTestsFromName('TheEVIDENCEOfAPreviousRunIsNeverOverwritten.test_a_COLLIDING_run_is_REFUSED_and_the_bytes_survive',t)
out=io.StringIO()
with patch.object(c,'check_policy_pin',side_effect=AssertionError('unexpected installed deployment read')) as dep:
 run=unittest.TextTestRunner(stream=out).run(suite)
results['collision_test_external_dependency']={'calls':dep.call_count,'errors':len(run.errors),'text':out.getvalue()}
# Exercise suite logic with an explicitly isolated policy boundary.
out=io.StringIO();started=time.monotonic()
with patch.object(c,'check_policy_pin',return_value={'equal':True,'configured_pin':23,'authority_generation':23}):
 run=unittest.TextTestRunner(stream=out).run(unittest.defaultTestLoader.loadTestsFromModule(t))
results['isolated_suite']={'count':run.testsRun,'success':run.wasSuccessful(),'wall_seconds':time.monotonic()-started,'text':out.getvalue()}
print(json.dumps(results,indent=2))
