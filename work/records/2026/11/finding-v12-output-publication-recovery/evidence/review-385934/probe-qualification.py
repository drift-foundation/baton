import sys,os,json,tempfile,subprocess,unittest
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tools import instance
out=Path(__file__).parent;packet=out.parent/'correction-K-385929';script=(packet/'qualify-w385695.sh').read_text()
class Preparation(unittest.TestCase):
 def test_authority_locator_is_the_installed_layout(self):
  expected=instance.layout('/fixture/instance')['authority_store']
  self.assertIn('("AUTHORITY", d + "/stores/authority.sqlite3")',script)
  actual='/fixture/instance/stores/authority.sqlite3'
  print('AUTHORITY_LAYOUT',json.dumps({'actual':actual,'expected':expected}))
  self.assertEqual(actual,expected)
 def test_cleanup_recovers_pause_ack_before_parent_assigns_variable(self):
  # Exact finish function, stopped at the reachable cut after the watcher wrote
  # PREFIX.paused but before the parent copied it into PAUSED. Only a fake eng.
  body=script.split('finish() {',1)[1].split('\ntrap finish EXIT',1)[0]
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   pre=Path(d)/'deadline';Path(str(pre)+'.paused').write_text('selected-container\n')
   setup='set -euo pipefail\nEVIDENCE='+repr(d)+'\nPREFIX='+repr(str(pre))+'\nPAUSED=""; ENDING=""; MANAGER_STARTED=""; phase=deadline; OWNED_PIDS=()\n'
   fake='say() { echo "$*"; }; eng() { echo "$*" >> "$EVIDENCE/engine-calls"; if [ "$1" = inspect ]; then echo true; fi; }; ended() { return 0; }\n'
   text=setup+fake+'finish() {'+body+'\ntrap finish EXIT\nexit 143\n'
   p=subprocess.run(['bash','-c',text],capture_output=True,text=True,timeout=10)
   calls=(Path(d)/'engine-calls').read_text() if (Path(d)/'engine-calls').exists() else ''
   print('PAUSE_CUT',json.dumps({'exit':p.returncode,'engine_calls':calls,'output':p.stdout}))
   self.assertIn('unpause selected-container',calls)
if __name__=='__main__':unittest.main(verbosity=2)
