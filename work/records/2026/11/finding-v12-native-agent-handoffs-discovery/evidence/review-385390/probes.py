import hashlib, json, os, pathlib, shutil, subprocess, tempfile, unittest
R=pathlib.Path('/home/sl/src/baton')
P=pathlib.Path('work/records/2026/10/finding-v12-development-coordination-pilot')
C=R/P/'config'; E=R/P/'evidence'
SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()

class Helpers(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=R/'work/scratch',prefix='codxpc-c3-');self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir();self.cfg=self.repo/P/'config';self.cfg.mkdir(parents=True);self.bound=self.cfg/'native-bound-2.json'
  for n in ('native-handoffs-2-bind.py','native-handoffs-2-qualify.sh','native-instance-handoffs-2.unbound.json','native-installed-task-handoffs-2.unbound.json'):shutil.copyfile(C/n,self.cfg/n)
  self.man=[]
  for name in ('native-handoffs-composer','native-handoffs-1-correction-2'):
   dst=self.repo/P/'evidence'/name;dst.mkdir(parents=True);shutil.copyfile(E/name/'manifest.json',dst/'manifest.json');self.man.append(str(dst/'manifest.json'))
  for name in ('native-handoffs-1-correction-2','native-handoffs-composer'):
   for x in json.loads((E/name/'manifest.json').read_text())['paths']:
    dst=self.repo/x['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(E/name/'candidate'/x['path'],dst)
  self.bin=self.root/'bin';self.bin.mkdir();self.calls=self.root/'calls';self.env=dict(os.environ,QUALIFY_REPO=str(self.repo),QUALIFY_DEST=str(self.root/'dest'),QUALIFY_TMP=str(self.root/'tmp'),QUALIFY_PACKAGING_ROOT=str(self.root/'packaging'),PATH=str(self.bin)+':'+os.environ['PATH'],QUALIFY_PYTHON='/home/sl/src/baton/.venv/bin/python')
  self.stub('just','echo just >> "$CALLS"\nexit 7');self.stub('docker','echo docker >> "$CALLS"\nexit 3');self.env['CALLS']=str(self.calls)
 def stub(self,name,body):
  f=self.bin/name;f.write_text('#!/bin/bash\n'+body+'\n');f.chmod(0o755)
 def git_stub(self,actual=False,dirty=False,moved=False):
  # Stand-in ONLY; no Git initialization/index/commit operation.
  show='exec /usr/bin/git -C /home/sl/src/baton show "$2"' if actual else 'cat "'+str(self.repo)+'/${2#*:}"'
  self.stub('git','case "$1" in status) '+('echo " M v12/STACK.md"' if dirty else ':')+';; rev-parse) echo '+('a'*40 if moved else SHA)+';; show) '+show+';; -C) shift 2; '+show+';; *) exit 91;; esac')
 def bind(self,*args):
  return subprocess.run(['python3','-I',str(self.cfg/'native-handoffs-2-bind.py'),'--repo',str(R),'--sha',SHA,'--manifests',*self.man,*args],capture_output=True,text=True)
 def tree_bound(self):
  x=self.bind('--tree',str(self.repo),'--out',str(self.bound));self.assertEqual(x.returncode,0,x.stderr)
 def step(self,step,env=None):
  return subprocess.run(['bash',str(self.cfg/'native-handoffs-2-qualify.sh'),step],env=dict(self.env,**(env or {})),capture_output=True,text=True,timeout=20)
 def test_joined_map_and_tree_recheck(self):
  self.tree_bound();b=json.loads(self.bound.read_text());self.assertEqual(len(b['paths']),43);self.assertEqual(len(b['overlap']),5)
  for path in b['overlap']:self.assertEqual(b['paths'][path]['owner'],'native-handoffs-composer')
  x=self.bind('--tree',str(self.repo),'--check',str(self.bound));self.assertEqual(x.returncode,0,x.stderr)
 def test_manifest_pin_and_byte_drift_refuse_without_binding(self):
  path=self.repo/'v12/STACK.md';path.write_text('drift');x=self.bind('--tree',str(self.repo),'--out',str(self.bound));self.assertEqual(x.returncode,2);self.assertFalse(self.bound.exists())
  pathlib.Path(self.man[0]).write_text('{}');x=self.bind('--tree',str(self.repo),'--out',str(self.bound));self.assertEqual(x.returncode,2);self.assertIn('not the reviewed manifest',x.stderr);self.assertFalse(self.bound.exists())
 def test_tree_binding_cannot_bypass_actual_committed_provenance(self):
  self.tree_bound();self.git_stub(actual=True)
  for step in ('bundle','image','install','compose','repeat','create','start'):
   x=self.step(step);self.assertEqual(x.returncode,2,(step,x.stdout,x.stderr));self.assertIn('does not carry the accepted bytes',x.stderr)
  self.assertFalse(self.calls.exists())
 def test_dirty_and_moved_head_stop_all_actions(self):
  self.tree_bound()
  for mode in ({'dirty':True},{'moved':True}):
   self.git_stub(**mode)
   for step in ('bundle','image','install','compose','repeat','create','start'):
    x=self.step(step);self.assertEqual(x.returncode,2,(step,x.stderr))
  self.assertFalse(self.calls.exists())
 def test_pipeline_failure_preserves_exit_and_stops_later_calls(self):
  self.tree_bound();self.git_stub()
  x=self.step('bundle');self.assertEqual(x.returncode,7,x.stderr);self.assertEqual(self.calls.read_text(),'just\n')
  self.assertFalse((self.repo/P/'evidence'/('checkpoint-'+SHA[:8]+'-packaging')/'build-stamp.json').exists())
  x=self.step('image');self.assertEqual(x.returncode,3,x.stderr);self.assertEqual(self.calls.read_text(),'just\ndocker\n')
 def test_missing_selections_refuse_before_commands(self):
  self.tree_bound();self.git_stub();x=self.step('create',{'JOB':'','STMT':''});self.assertEqual(x.returncode,2,x.stderr);self.assertIn('pending selection',x.stderr);self.assertFalse(self.calls.exists())

if __name__=='__main__':unittest.main(verbosity=2)
