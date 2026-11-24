import sys,json,unittest,copy
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from tests.tools import test_stage_execution as stage_cases
from tools import stage_execution,pool
from baton_v12.contracts.manifest import job_input_identity

class Deadline(cases.PublicationExecutionCase):
    def test_measurement_crossing_deadline_cannot_publish(self):
        import baton_worker
        self.ready();self.launched()
        real=baton_worker.measured
        def late(*a,**kw):
            self.instants.append(cases.LATE)
            return real(*a,**kw)
        with patch.object(baton_worker,'measured',late):
            rc=self.turn()
        terminal=self.exchange_view()['terminal']
        print('POST_COPY_DEADLINE',json.dumps({'rc':rc,'clock':self.clock(),'terminal':terminal}))
        self.assertNotEqual(terminal['ending'],'answered')

class Production(stage_cases.APublicationWorkerIsAConfiguredRoleInItsOwnLane):
    def test_installer_accepts_publication_role(self):
        worker=self.publication()
        value={'worker_id':worker['worker_id'],'role':worker['role'],'participant':worker['deployment']['participant'],'deployment':worker['deployment']}
        pool.held_worker(value)

    def test_one_installed_publisher_can_serve_second_work(self):
        given=self.with_publisher();worker=given['workers'][-1];d=worker['deployment'];m=d['input_manifest']
        binding={'job_id':'recovery-other','job_work_id':'0000000a-W999','source_worker_id':'implementation-worker'}
        stage={'job_id':binding['job_id'],'kind':'publication','profile_name':d['profile_name'],'profile_digest':d['profile_digest']}
        job={'input_digest':job_input_identity(m),'policy_digest':d['policy_digest']}
        disagreement=stage_execution._disagreements(stage_execution._served_deployment(given,worker,binding),stage,job,binding)
        print('SECOND_WORK',json.dumps(disagreement))
        self.assertNotIn('the Work',disagreement)

if __name__=='__main__':
    suite=unittest.TestSuite([Deadline('test_measurement_crossing_deadline_cannot_publish'),Production('test_installer_accepts_publication_role'),Production('test_one_installed_publisher_can_serve_second_work')])
    result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
