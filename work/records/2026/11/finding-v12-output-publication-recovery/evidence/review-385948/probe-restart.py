import os,sys,tempfile,subprocess,unittest,json
from pathlib import Path
P=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/correction-K-385944')
class Restart(unittest.TestCase):
 def retained_intent(self,name):
  s=(P/name).read_text();func=s[s.index('op_alive() {'):s.index('\ntrap finish EXIT')]
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   r=Path(d);pre=r/'phase';Path(str(pre)+'.stack-start-intent').write_text('retained-start-token\n')
   # The forked operation has not yet written its op record. Model that exact retained cut;
   # release it only after the rerun finishes reconciliation. No stack or engine is invoked.
   childcode='import sys,os,pathlib;print("ready",flush=True);sys.stdin.readline();p=pathlib.Path(sys.argv[1]);p.with_suffix(".stack-start-op").write_text(str(os.getpid())+" 1\\n");p.with_suffix(".late-start-effect").write_text("effect")'
   c=subprocess.Popen([sys.executable,'-c',childcode,str(pre)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
   try:
    self.assertEqual(c.stdout.readline().strip(),'ready')
    body=f'PREFIX={str(pre)!r}; UNRESOLVED=""\nsay() {{ echo "$*"; }}\nstack_live() {{ return 0; }}\n'+func+'\nreconcile_stack\necho "unresolved=[$UNRESOLVED]"\n'
    done=subprocess.run(['bash','-c',body],capture_output=True,text=True,timeout=10)
    retained=Path(str(pre)+'.stack-start-intent').exists();reconciled=Path(str(pre)+'.stack-start-reconciled').exists()
    c.communicate('\n',timeout=5)
    effect=Path(str(pre)+'.late-start-effect').exists()
    print('MISSING_OP_RESTART',json.dumps({'script':name,'exit':done.returncode,'retained':retained,'marked_reconciled':reconciled,'late_effect':effect,'stdout':done.stdout}))
    self.assertTrue(retained,'missing operation receipt was treated as cessation; retained intent cleared before late effect')
    self.assertIn('UNRESOLVED',done.stdout)
   finally:
    if c.poll() is None:c.kill()
    c.wait()
 def test_qualification_retained_start_without_operation_receipt_stays_unresolved(self):self.retained_intent('qualify-w385695.sh')
 def test_setup_retained_start_without_operation_receipt_stays_unresolved(self):self.retained_intent('option-a-setup.sh')
 def test_image_remove_failure_cannot_report_success(self):
  s=(P/'qualify-w385695.sh').read_text();cleanup=s[s.index('cleanup() {'):s.index('\ncase "$phase" in',s.index('cleanup() {'))]
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
   r=Path(d);(r/'images.owned').write_text('fixture owned-tag sha256:owned\n')
   body=f'EVIDENCE={d!r};PREFIX="$EVIDENCE/cleanup";UNRESOLVED=""\n'+'''say() { echo "$*"; };run_id() { echo run; }
eng() { if [ "$2" = inspect ]; then echo sha256:owned;return 0;fi;return 1; }
'''+cleanup+'\ncleanup\nif [ -n "$UNRESOLVED" ];then exit 1;fi\n'
   done=subprocess.run(['bash','-c',body],capture_output=True,text=True,timeout=5)
   print('IMAGE_REMOVE_FAILURE',json.dumps({'exit':done.returncode,'stdout':done.stdout}))
   self.assertNotEqual(done.returncode,0,'failed removal prints UNRESOLVED but never marks the phase unresolved')
if __name__=='__main__':unittest.main(verbosity=2)
