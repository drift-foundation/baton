import os,sys,unittest,tempfile,subprocess,json
from pathlib import Path
packet=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/correction-K-385937')
q=(packet/'qualify-w385695.sh').read_text();s=(packet/'option-a-setup.sh').read_text()
class Cleanup(unittest.TestCase):
 def start_cut(self,script,setup):
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   root=Path(d)
   # Exact production functions. Only the external stack/engine operations are doubles.
   finish=script[script.index('finish() {'):script.index('\ntrap finish EXIT')]
   if setup:
    target=script[script.index('failures() {'):script.index('\ncase "$phase" in',script.index('failures() {'))]; entry='failures'
   else:
    target=script[script.index('serve() {'):script.index('\nuntil_status() {')];entry='serve'
   fake='''
say() { echo "$*"; }
fail() { say "FAIL: $*"; exit 1; }
stack_live() { if [ -f "$EVIDENCE/started" ]; then echo "manager $$"; fi; }
reconcile_pause() { :; }
# Real signal at the start completion boundary, before caller records ownership.
timeout() {
 case "$*" in
  *' start') touch "$EVIDENCE/started"; kill -TERM "$$"; return 0;;
  *' stop') echo stopped >> "$EVIDENCE/stops"; return 0;;
  *) echo unexpected >&2; return 99;;
 esac
}
'''
   head=f'set -euo pipefail\nEVIDENCE={str(root)!r}; PREFIX="$EVIDENCE/deadline"; DEST="$EVIDENCE"; OWNER=owner; phase=deadline; ENDING=""; MANAGER_STARTED=""; PAUSED=""; OWNED_PIDS=()\n'
   body=head+fake+finish+'\ntrap finish EXIT\ntrap \'exit 143\' TERM\n'+target+'\n'+entry+'\n'
   done=subprocess.run(['bash','-c',body],capture_output=True,text=True,timeout=10)
   stopped=(root/'stops').exists();created=(root/'started').exists()
   print('START_CUT',json.dumps({'script':'setup' if setup else 'qualify','exit':done.returncode,'created':created,'stopped':stopped,'stdout':done.stdout}))
   self.assertEqual(done.returncode,143);self.assertTrue(created)
   self.assertTrue(stopped,'start effect occurred but signal cleanup did not reconcile ownership or stop it')
 def test_qualification_signal_after_start_effect_is_cleaned(self):self.start_cut(q,False)
 def test_setup_signal_after_start_effect_is_cleaned(self):self.start_cut(s,True)
 def test_failed_inspection_is_reported_as_unresolved(self):
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   root=Path(d);(root/'deadline.pause-intent').write_text('selected-container\n')
   body=q[q.index('reconcile_pause() {'):q.index('\nfinish() {')]
   head=f'EVIDENCE={str(root)!r}; PREFIX="$EVIDENCE/deadline"; PAUSED=""\n'
   # A transport failure is not positive container absence.
   fake='say() { echo "$*"; }; eng() { echo "daemon unavailable" >&2; return 125; }\n'
   done=subprocess.run(['bash','-c',head+fake+body+'\nreconcile_pause\n'],capture_output=True,text=True,timeout=10)
   print('UNKNOWN_INSPECT',json.dumps({'exit':done.returncode,'stdout':done.stdout}))
   self.assertIn('UNRESOLVED',done.stdout,'failed inspect was collapsed into absent/nothing to release')
if __name__=='__main__':unittest.main(verbosity=2)
