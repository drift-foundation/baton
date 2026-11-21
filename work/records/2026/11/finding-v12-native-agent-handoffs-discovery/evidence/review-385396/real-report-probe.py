import contextlib,io,json,pathlib,subprocess,sys,unittest
from tests.tools.test_connected_creation import TheReusableInstanceComposesHandoffCapableWorkers
E=pathlib.Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-agent-handoffs-discovery/evidence/review-385396')
HELPER=pathlib.Path('/home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/native-handoffs-2-qualify.sh')
class Report(TheReusableInstanceComposesHandoffCapableWorkers):
 def test_supported_composition_real_create_and_exact_helper_validator(self):
  issued=[];self.installed_with_repositories(issued,native_handoff_routing=dict(self.ROUTING));workers=[]
  for wid,role,who in [('impl-a','implementation','baton.impl-a'),('review-a','review','baton.reviewer')]:
   code,said,into=self.composed_by_command(wid,role,who,'--template',self.HANDOFF);self.assertEqual(code,0,said);workers.append(json.loads(pathlib.Path(into).read_text()))
  code,said=self.repeated(issued,workers,self.ROUTING);self.assertEqual(code,0,said)
  report=io.StringIO()
  with contextlib.redirect_stderr(report):code,said=self.created(template=self.HANDOFF,control_profile='native-handoff/1')
  self.assertEqual(code,0,said)
  (E/'real-create.stdout.json').write_text(said);(E/'real-create.stderr.log').write_text(report.getvalue())
  cfg=pathlib.Path(self.root)/'bound-config';cfg.mkdir();(cfg/('native-instance-2-'+self.BASE[:8]+'.json')).write_text(json.dumps({'native_handoff_routing':self.ROUTING}))
  branch=HELPER.read_text().split('create)\n',1)[1].split('\nstart)',1)[0];validator=branch.split("<<'PY'\n",1)[1].split('\nPY',1)[0]
  out=subprocess.run([sys.executable,'-I','-',self.BASE,str(cfg),str(E/'real-create.stdout.json'),str(E/'real-create.stderr.log')],input=validator,capture_output=True,text=True)
  (E/'real-validator.log').write_text(out.stdout+out.stderr);self.assertEqual(out.returncode,0,out.stderr);self.assertIn('reported by the command',out.stdout)
if __name__=='__main__':
 out=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Report('test_supported_composition_real_create_and_exact_helper_validator')]));raise SystemExit(not out.wasSuccessful())
