"""Reviewer deterministic shutdown counterexamples; engine/provider simulated."""
import sys,time,json,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
import supervisor
from test_supervisor import SupervisedCase
from tests.job_manager import fixtures

class ShutdownCounterexamples(SupervisedCase):
    def test_refresh_failure_is_silently_settled(self):
        original=supervisor._attempts_of
        faults=[]
        def fail_after_stop(job,operations,job_id):
            if isinstance(operations,supervisor.AdmissionGate) and operations.stopped:
                faults.append(True)
                raise RuntimeError('canonical history unavailable after stop')
            return original(job,operations,job_id)
        with mock.patch.object(supervisor,'_attempts_of',side_effect=fail_after_stop):
            _,outcome,_,_=self.supervised()
        self.assertTrue(faults)
        self.assertEqual(outcome['state'],'settled')
        self.assertEqual(outcome['held_because'],[])

    def test_overall_timeout_does_not_stop_waiting_runtime(self):
        job,control,composed=self.serving()
        ticks=iter(range(10000))
        packet=dict(self.packet,bounds=dict(self.packet['bounds'],total_seconds=8,cleanup_seconds=3))
        outcome=supervisor.supervise(job,control,composed,packet,clock=lambda:fixtures.NOW,sleep=lambda seconds:None,monotonic=lambda:float(next(ticks)))
        self.assertEqual(outcome['stopped'],'overall-bound-exceeded')
        self.assertTrue(outcome['admitted_attempts'])
        self.assertTrue(outcome['outstanding_cleanup'])
        commands=[argv[1] for argv in self.engine.vectors]
        self.assertIn('run',commands)
        self.assertNotIn('stop',commands)
        self.assertNotIn('kill',commands)
        self.assertNotIn('rm',commands)
        self.assertEqual(outcome['stage_states']['implementation'],'waiting')

if __name__=='__main__':
    suite=unittest.TestSuite(ShutdownCounterexamples(n) for n in ShutdownCounterexamples.__dict__ if n.startswith('test_'))
    start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'confirmed_counterexamples':result.wasSuccessful(),'seconds':time.monotonic()-start}))
    sys.exit(not result.wasSuccessful())
