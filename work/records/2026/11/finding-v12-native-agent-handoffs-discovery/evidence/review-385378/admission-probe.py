import json
from pathlib import Path
import unittest
from tests.tools.test_connected_creation import TheReusableInstanceComposesHandoffCapableWorkers

class AdmissionProbe(TheReusableInstanceComposesHandoffCapableWorkers):
    def test_native_job_refuses_default_workers_before_creation(self):
        issued=[]
        self.installed_with_repositories(issued,native_handoff_routing=dict(self.ROUTING))
        workers=[]
        for worker_id,role,participant in (('impl-a','implementation','baton.impl-a'),('review-a','review','baton.reviewer')):
            code,said,into=self.composed_by_command(worker_id,role,participant)
            self.assertEqual(code,0,said)
            worker=json.loads(Path(into).read_text())
            self.assertEqual([o['name'] for o in worker['deployment']['input_manifest']['outputs']],['proposal'])
            workers.append(worker)
        code,said=self.repeated(issued,workers,self.ROUTING)
        self.assertEqual(code,0,said)
        code,said=self.created(template=self.HANDOFF,control_profile='native-handoff/1')
        self.assertNotEqual(code,0,'Unsupported /3 Job admitted against default /1 workers: '+said)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([AdmissionProbe('test_native_job_refuses_default_workers_before_creation')]))
    raise SystemExit(not result.wasSuccessful())
