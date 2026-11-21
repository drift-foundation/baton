import contextlib,importlib.util,io,json,os,pathlib,subprocess,tempfile,unittest
from unittest import mock
R=pathlib.Path('/home/sl/src/baton');P=pathlib.Path('work/records/2026/10/finding-v12-development-coordination-pilot');C=R/P/'config'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
tree=module('treeguard',C/'native-handoffs-2-tree.py');stampmod=module('stamp',R/'v12/python/tools/build_stamp.py');SHA='a'*40
class Guards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=R/'work/scratch',prefix='codxpc-guard406-');self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
 def assess(self,lines,stamp=None,inputs=()):
  identity={'head':SHA,'changed':[],'inputs':list(inputs),'content_digest':'b'*64,'consumed_count':len(inputs)};idp=self.root/'identity.json';idp.write_text(json.dumps(identity));capture=self.root/'capture.json';capture.write_text(json.dumps({'commit':SHA}));args=['--capture',str(capture),'--repo',str(self.root),'--sha',SHA,'--identity',str(idp)]
  if stamp is not None:
   p=self.root/'stamp.json';p.write_text(json.dumps(stamp));args+=['--stamp',str(p)]
  with mock.patch.object(tree,'observe',return_value=lines),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   try:return tree.main(args)
   except SystemExit as e:return e.code
 def test_generated_records_with_real_capture_are_accepted(self):
  lines=['?? '+str(P/'config/native-bound-2.json')];stamp=stampmod.capture(source=self.root,runner=lambda argv,cwd:SHA+'\n' if 'rev-parse' in argv else '\n'.join(lines)+'\n');self.assertTrue(stamp['dirty']);self.assertEqual(self.assess(lines,stamp),0)
 def test_unrelated_review_evidence_does_not_require_new_checkpoint(self):
  self.assertEqual(self.assess(['?? work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-385406/']),0)
 def test_capture_excused_build_outputs_are_not_counted_as_source_drift(self):
  lines=['?? '+str(P/'config/native-bound-2.json'),'?? v12/python/build/out/'];stamp=stampmod.capture(source=self.root,runner=lambda argv,cwd:SHA+'\n' if 'rev-parse' in argv else '\n'.join(lines)+'\n');self.assertEqual(stamp['changed_entries'],1);self.assertEqual(stamp['excused_build_output'],1);self.assertEqual(self.assess(lines,stamp),0)
 def test_recorded_stamp_not_rewritten_by_later_generated_evidence(self):
  before=['?? '+str(P/'config/native-bound-2.json')];stamp=stampmod.capture(source=self.root,runner=lambda argv,cwd:SHA+'\n' if 'rev-parse' in argv else '\n'.join(before)+'\n');after=before+['?? '+str(P/('evidence/checkpoint-'+SHA[:8]+'-packaging/'))];self.assertEqual(self.assess(after,stamp),0)
 def install(self,different_stamp=False):
  cfg=self.root/'cfg';cfg.mkdir();dest=self.root/'dest';dest.mkdir();ev=self.root/'ev';g=ev/('checkpoint-'+SHA[:8]+'-packaging');g.mkdir(parents=True);stamp={'commit':SHA,'dirty':True,'changed_entries':4};(g/'build-stamp.json').write_text(json.dumps(stamp));(g/'bundle-identity.json').write_text(json.dumps({'sha256':'verified-bundle','build_stamp':stamp}));(dest/'authority-identity.json').write_text('{}')
  changed=dict(stamp,dirty=False) if different_stamp else stamp
  identity={'authority_uuid':'fixture','identity':{'build_stamp':changed,'sha256':'different-unverified-bundle'}};binp=self.root/'bin';binp.mkdir();just=binp/'just';just.write_text('#!/bin/bash\nif [[ "$*" == *bootstrap* ]]; then\ncat > "'+str(dest/'instance.json')+'" <<\'EOF\'\n'+json.dumps(identity)+'\nEOF\nfi\n');just.chmod(0o755)
  block=(C/'native-handoffs-2-qualify.sh').read_text().split('\ninstall)\n',1)[1].split('\n    ;;',1)[0]
  script='set -euo pipefail\ncheck(){ :; }\n'+block
  env=dict(os.environ,PATH=str(binp)+':'+os.environ['PATH'],SHA=SHA,SHORT=SHA[:8],DEST=str(dest),CFG=str(cfg),EV=str(ev));out=subprocess.run(['bash','-c',script],env=env,capture_output=True,text=True);return out,dest
 def test_different_stamp_refuses_before_install_effects(self):
  out,dest=self.install(True);self.assertNotEqual(out.returncode,0);self.assertFalse((dest/'instance.json').exists(),'bootstrap already created the destination before stamp refusal')
 def test_same_stamp_different_bundle_is_not_accepted(self):
  out,dest=self.install(False);self.assertNotEqual(out.returncode,0,'unverified bundle accepted solely because its stamp matches: '+out.stdout)
# Round 6 API adaptation: required --capture added above; old assertions retained.
import hashlib,shutil
instance=module("runtime_instance",R/"v12/python/tools/instance.py")
class Round6(Guards):
 def install(self,different_stamp=False,mode=None):
  cfg=self.root/'cfg';cfg.mkdir();dest=self.root/'dest';dest.mkdir();ev=self.root/'ev';g=ev/('checkpoint-'+SHA[:8]+'-packaging');g.mkdir(parents=True);tmp=self.root/'tmp';tmp.mkdir();stamp={'commit':SHA,'dirty':True,'changed_entries':4}
  d=self.root/'v12/python/build/out/distro';d.mkdir(parents=True);dep=d/'_internal/library.so';dep.parent.mkdir();dep.write_bytes(b'qualified-library')
  bundle=d/'baton-v12-stack';identity={'sha256':'fixture-executable-identity','build_stamp':stamp}
  bundle.write_text('#!/bin/sh\necho invoked > '+str(self.root/'bundle-invoked')+'\ncat <<\'EOF\'\n'+json.dumps(identity)+'\nEOF\n');bundle.chmod(0o755)
  (g/'build-stamp.json').write_text(json.dumps(stamp));(g/'bundle-identity.json').write_text(json.dumps(identity));(g/'distro-sha256.txt').write_text(hashlib.sha256(bundle.read_bytes()).hexdigest()+'  '+str(bundle)+'\n')
  runtime=instance.manifest(d);(g/'runtime-manifest.json').write_text(json.dumps(runtime));toolsdir=self.root/'v12/python/tools';toolsdir.mkdir();shutil.copyfile(R/'v12/python/tools/instance.py',toolsdir/'instance.py')
  if different_stamp:
   changed=dict(stamp,dirty=False);(g/'build-stamp.json').write_text(json.dumps(changed))
  elif mode is None:bundle.write_text(bundle.read_text()+'# other executable, same reported stamp\n')
  if mode=='missing':(g/'distro-sha256.txt').unlink()
  if mode=='dependency':dep.write_bytes(b'changed-unqualified-library')
  if mode=='add':(dep.parent/'added.so').write_bytes(b'added')
  if mode=='remove':dep.unlink()
  if mode=='external-link':dep.unlink();dep.symlink_to('/etc/hosts')
  if mode=='internal-link':dep.unlink();dep.symlink_to('../baton-v12-stack')
  if mode=='runtime-mismatch':runtime=dict(runtime,digest='other')
  binp=self.root/'bin';binp.mkdir();just=binp/'just';installed=dict(identity)
  if mode=='installed-mismatch':installed['sha256']='other'
  just.write_text('#!/bin/bash\nif [[ "$*" == *bootstrap* ]]; then\ncat > "'+str(dest/'instance.json')+'" <<\'EOF\'\n'+json.dumps({'authority_uuid':'fixture','identity':installed,'runtime':runtime})+'\nEOF\necho {} > "'+str(dest/'authority-identity.json')+'"\nfi\n');just.chmod(0o755)
  block=(C/'native-handoffs-2-qualify.sh').read_text().split('\ninstall)\n',1)[1].split('\n    ;;',1)[0]
  env=dict(os.environ,PATH=str(binp)+':'+os.environ['PATH'],SHA=SHA,SHORT=SHA[:8],DEST=str(dest),CFG=str(cfg),EV=str(ev),TMP=str(tmp),PYTHON=str(R/'.venv/bin/python'))
  out=subprocess.run(['bash','-c','set -euo pipefail\ncheck(){ :; }\n'+block],cwd=self.root,env=env,capture_output=True,text=True);return out,dest
 def test_missing_evidence_refuses_before_bootstrap(self):
  out,dest=self.install(mode='missing');self.assertNotEqual(out.returncode,0);self.assertFalse((dest/'instance.json').exists())
 def test_matching_artifact_passes(self):
  out,dest=self.install(mode='matching');self.assertEqual(out.returncode,0,out.stderr);self.assertTrue((dest/'instance.json').exists())
 def test_installed_mismatch_refuses(self):
  out,dest=self.install(mode='installed-mismatch');self.assertNotEqual(out.returncode,0);self.assertTrue((dest/'instance.json').exists())
 def test_changed_dependency_refuses_before_bootstrap(self):
  out,dest=self.install(mode='dependency');self.assertNotEqual(out.returncode,0,'changed dependency accepted: '+out.stdout);self.assertFalse((dest/'instance.json').exists())
 def test_full_clean_guard_allows_capture_excused_output(self):
  bindir=self.root/'bin';bindir.mkdir();git=bindir/'git';git.write_text('#!/bin/sh\nprintf "?? v12/python/build/out/\\n"\n');git.chmod(0o755)
  source=(C/'native-handoffs-2-qualify.sh').read_text();block=source.split('clean_tree() {',1)[1].split('\n}',1)[0]
  out=subprocess.run(['bash','-c','set -euo pipefail\nclean_tree(){\n'+block+'\n}\nclean_tree'],env=dict(os.environ,PATH=str(bindir)+':'+os.environ['PATH']),capture_output=True,text=True)
  self.assertEqual(out.returncode,0,out.stderr)
 def test_stable_inputs_survive_evidence_then_refuse_content_drift(self):
  ident=self.root/'identity.json';capture=self.root/'capture.json';stable=self.root/'stable.json'
  d={'head':SHA,'changed':[],'inputs':['fixtures/input'],'content_digest':'b'*64,'consumed_count':1};ident.write_text(json.dumps(d));capture.write_text(json.dumps({'commit':SHA}))
  args=['--repo',str(self.root),'--sha',SHA,'--identity',str(ident),'--capture',str(capture),'--stable',str(stable)]
  with mock.patch.object(tree,'dirty_inputs',return_value=[]),mock.patch.object(tree,'observe',return_value=['?? arbitrary/review/']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   self.assertEqual(tree.main(args),0);before=stable.read_bytes();self.assertEqual(tree.main(args),0);self.assertEqual(stable.read_bytes(),before)
   d['content_digest']='c'*64;ident.write_text(json.dumps(d))
   with self.assertRaises(SystemExit) as raised:tree.main(args)
   self.assertEqual(raised.exception.code,2);self.assertEqual(stable.read_bytes(),before)
 def test_add_remove_links_refuse_before_execution(self):
  for mode in ('add','remove','external-link','internal-link'):
   with self.subTest(mode=mode):
    self.setUp();out,dest=self.install(mode=mode);self.assertNotEqual(out.returncode,0,out.stdout);self.assertFalse((dest/'instance.json').exists());self.assertFalse((self.root/'bundle-invoked').exists())
 def test_installed_runtime_mismatch_refuses(self):
  out,dest=self.install(mode='runtime-mismatch');self.assertNotEqual(out.returncode,0);self.assertTrue((dest/'instance.json').exists());self.assertIn('installed runtime',out.stderr)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Round6);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
