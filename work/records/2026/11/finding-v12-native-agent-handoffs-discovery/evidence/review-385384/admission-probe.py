import json
from pathlib import Path
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.authority import Refusal
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
        input_path=Path(self.state)/'install-inputs.json'
        config_path=Path(self.state)/'deployment.json'
        before=(input_path.read_bytes(), config_path.read_bytes())
        with self.assertRaises(ContractRefusal) as caught:
            self.created(template=self.HANDOFF,control_profile='native-handoff/1')
        self.assertIn('declares a different result contract', str(caught.exception))
        self.assertEqual((input_path.read_bytes(),config_path.read_bytes()),before)
        store,_=self.rows()
        self.assertEqual(store._connection.execute('SELECT count(*) FROM template_jobs').fetchone()[0],0)
        self.assertEqual(self.bindings(),{})
        with self.assertRaises(Refusal):
            self.authority().project_work(self.owned['authority_uuid'][:8]+'-W1')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([AdmissionProbe('test_native_job_refuses_default_workers_before_creation')]))
    raise SystemExit(not result.wasSuccessful())
