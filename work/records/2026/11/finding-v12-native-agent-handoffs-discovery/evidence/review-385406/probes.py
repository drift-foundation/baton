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
  identity={'head':SHA,'changed':[],'inputs':list(inputs),'content_digest':'b'*64,'consumed_count':len(inputs)};idp=self.root/'identity.json';idp.write_text(json.dumps(identity));args=['--repo',str(self.root),'--sha',SHA,'--identity',str(idp)]
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
if __name__=='__main__':unittest.main(verbosity=2)
