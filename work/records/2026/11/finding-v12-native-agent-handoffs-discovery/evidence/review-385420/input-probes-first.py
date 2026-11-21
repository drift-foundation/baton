import contextlib,io,json,pathlib,hashlib,unittest
from unittest import mock
import probes as base
source=base.module('source_identity',base.R/'v12/python/tools/source_identity.py')
class Inputs(base.Guards):
 def real_identity(self,changed):
  with mock.patch.object(source,'_git',return_value=(base.SHA+'\n').encode()),mock.patch.object(source,'changed_paths',return_value=changed),mock.patch.object(source,'input_files',return_value=[('tracked','fixtures/input')]),mock.patch.object(source,'_content',side_effect=lambda p:hashlib.sha256(p.encode()).hexdigest()):
   return source.identity(str(self.root),['v12'],['fixtures/input'])
 def invoke(self,d,transition=None,dirty=()):
  identity=self.root/'identity.json';identity.write_text(json.dumps(d));cap=self.root/'capture.json';cap.write_text(json.dumps({'commit':base.SHA}));sums=self.root/'sums';
  if not sums.exists():sums.write_text('old')
  args=['--repo',str(self.root),'--sha',base.SHA,'--identity',str(identity),'--capture',str(cap),'--stable',str(self.root/'stable.json'),'--helper-sums',str(sums)]
  if transition:args+=['--helper-transition',transition]
  with mock.patch.object(base.tree,'observe',return_value=[]),mock.patch.object(base.tree,'dirty_inputs',return_value=list(dirty)),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   try:return base.tree.main(args)
   except SystemExit as e:return e.code
 def test_real_digest_reconciliation_and_output_stability(self):
  clean=self.real_identity([]);self.assertEqual(base.tree.inputs_digest(clean,[]),clean['content_digest']);self.assertEqual(self.invoke(clean),0)
  changed=self.real_identity([('??','v12/python/build/out/a.so'),('??','v12/python/build/work/cache'),('??','v12/python/packaging/build-stamp.json')]);self.assertEqual(base.tree.inputs_digest(changed,changed['changed']),clean['content_digest']);self.assertEqual(self.invoke(changed),0)
 def test_tracked_and_nearby_paths_refuse(self):
  for status,path in [(' M','v12/python/build/out/a.so'),('??','v12/python/build/outside/a'),('??','v12/python/packaging/build-stamp.json.extra'),('??','v12/python/src/new.py')]:
   with self.subTest(path=path):self.assertEqual(self.invoke(self.real_identity([(status,path)])),2)
 def test_transition_keeps_prior_and_refuses_source_or_declared_drift(self):
  clean=self.real_identity([]);self.assertEqual(self.invoke(clean),0);stable=self.root/'stable.json';prior=stable.read_bytes();old=json.loads(prior)['helper_sums_sha256'];(self.root/'sums').write_text('new')
  self.assertEqual(self.invoke(clean),2);self.assertEqual(self.invoke(clean,'wrong'),2);self.assertEqual(stable.read_bytes(),prior)
  drift=dict(clean,content_digest='drift');self.assertEqual(self.invoke(drift,old),2);self.assertEqual(self.invoke(clean,old,['?? fixtures/input/new']),2);self.assertEqual(stable.read_bytes(),prior)
  self.assertEqual(self.invoke(clean,old),0);held=json.loads(stable.read_bytes());saved=self.root/held['transitions'][0]['prior_record_kept_as'];self.assertEqual(saved.read_bytes(),prior);self.assertEqual(held['inputs_digest'],clean['content_digest']);self.assertEqual(self.invoke(clean),0)
if __name__=='__main__':
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName('Inputs.'+name,module=__import__(__name__)) for name in ('test_real_digest_reconciliation_and_output_stability','test_tracked_and_nearby_paths_refuse','test_transition_keeps_prior_and_refuses_source_or_declared_drift'));result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
