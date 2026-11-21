import importlib.util,json,pathlib,unittest
P=pathlib.Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-385390/probes.py')
spec=importlib.util.spec_from_file_location('old_probes',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Create(m.Helpers):
 def setup_create(self,missing=False,wrong=False,exit_code=0):
  self.tree_bound();self.git_stub();self.stub('just','echo just >> "$CALLS"\nexit 0')
  dest=self.root/'dest';(dest/'distro').mkdir(parents=True);(dest/'authority-identity.json').write_text(json.dumps({'authority_uuid':'a'*32}))
  routing={'reviewer':'baton.reviewer-native','decision_recipient':'baton.slaw'}
  (self.cfg/('native-instance-2-'+m.SHA[:8]+'.json')).write_text(json.dumps({'native_handoff_routing':routing}))
  work='aaaaaaaa-W1';held={'work_id':work,'template':{'version':'baton.v12.job-template.implementation-review/3'},'control':{'profile':'native-handoff/1'}}
  lines=['routing%-14s reviewer %s, decisions to %s'%('',routing['reviewer'],routing['decision_recipient']),'work  %-14s already exists; left alone'%(work if not wrong else 'aaaaaaaa-W2'),'grant %-14s approve/review/verify/integrate in its own scope'%work,'answer%-14s answer-handoff to %s in its own scope; no review grant'%('',routing['reviewer'])]
  if missing:lines.pop()
  exe=dest/'distro/baton-v12-stack';exe.write_text('#!/usr/bin/python3\nimport sys\nprint('+repr(json.dumps(held))+')\nprint('+repr('\n'.join(lines))+',file=sys.stderr)\nraise SystemExit('+str(exit_code)+')\n');exe.chmod(0o755)
  stmt=self.root/'stmt';stmt.write_text('bounded task');return {'JOB':'review-fixture','STMT':str(stmt)}
 def test_success_captures_both_streams_without_store(self):
  env=self.setup_create();x=self.step('create',env);self.assertEqual(x.returncode,0,x.stderr);self.assertIn('reported by the command',x.stdout)
  q=self.repo/m.P/'evidence/native-handoffs-2-qualification';self.assertEqual(json.loads((q/'create-review-fixture.json').read_text())['work_id'],'aaaaaaaa-W1');self.assertIn('answer-handoff',(q/'create-review-fixture.report.log').read_text());self.assertFalse((self.root/'dest/db').exists())
 def test_missing_grant_report_fails(self):
  env=self.setup_create(missing=True);x=self.step('create',env);self.assertNotEqual(x.returncode,0);self.assertIn('lacks the line',x.stderr)
 def test_foreign_work_report_fails(self):
  env=self.setup_create(wrong=True);x=self.step('create',env);self.assertNotEqual(x.returncode,0);self.assertIn('aaaaaaaa-W1',x.stderr)
 def test_failed_create_preserves_status_and_evidence(self):
  env=self.setup_create(exit_code=9);x=self.step('create',env);self.assertEqual(x.returncode,9);self.assertNotIn('reported by the command',x.stdout);q=self.repo/m.P/'evidence/native-handoffs-2-qualification';self.assertTrue((q/'create-review-fixture.report.log').exists());self.assertTrue((q/'create-review-fixture.json').exists())
if __name__=='__main__':
 names=['test_success_captures_both_streams_without_store','test_missing_grant_report_fails','test_foreign_work_report_fails','test_failed_create_preserves_status_and_evidence'];out=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Create(n) for n in names));raise SystemExit(not out.wasSuccessful())
