"""Bounded deterministic review counterexamples; no engine/provider access."""
import json, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
import supervisor
from test_supervisor import SupervisedCase
from baton_v12 import job_manager

class RealComposedCounterexamples(SupervisedCase):
    def test_declared_one_each_still_runs_two_each_and_settles(self):
        packet=self.written_packet(bounds=dict(self.packet['bounds'],implementer_invocations=1,review_invocations=1,turn_seconds=1))
        supervisor.held_packet(self.packet_path)
        _,outcome,_,_=self.supervised(packet=packet)
        self.assertEqual(outcome['state'],'settled')
        self.assertEqual(len(outcome['admitted_attempts']),4)
        self.assertEqual(self.calls_count(),2)

    def test_accepting_first_review_settles_without_restore(self):
        def accept_first(job,control,composed,**unused):
            attempt=self.pending(composed,'review')
            if attempt is None:return
            self.turned.add(attempt)
            return self.turn(control,'review',attempt,self.mounted(composed,'review',attempt),edits={'review-report.json':json.dumps({'schema':'baton.review-report/1','verdict':'accepted','findings':'accepted initial proposal'})})
        self.run_review=accept_first
        _,outcome,_,_=self.supervised()
        self.assertEqual(outcome['state'],'settled')
        self.assertEqual(self.calls_count(),1)
        self.assertEqual(len(outcome['admitted_attempts']),2)

class FailureBoundaryCounterexamples(unittest.TestCase):
    def run_case(self, *, late_failure=False):
        with tempfile.TemporaryDirectory(prefix='w236087-review-') as root:
            p=Path(root); (p/'submission').write_text('{}')
            packet={'bounds':{'total_seconds':2,'cleanup_seconds':3},'submission':{'path':str(p/'submission'),'job_id':'job-a'},'outcome_path':str(p/'outcome'),'run_id':'review-synthetic','work':'W236087','claim':236474}
            seen={}; counts={'sweeps':0}; queries=[]
            def attempts(*args):return dict(seen),{'implementation':'waiting'},{}
            def serve(*args,should_continue,**kwargs):
                if not late_failure:seen['a']='implementation'
                should_continue()
                if late_failure:
                    seen['late']='implementation'
                    raise RuntimeError('fault after admission before next predicate')
            def clean(control,packet,admitted):
                queries.append(sorted(admitted))
                return {'cleanup':{a:{'cleanup':None} for a in admitted},'outstanding':list(admitted)}
            def sweep(*args,**kwargs):
                counts['sweeps']+=1
                seen['new-after-stop']='review'
            ticks=iter(range(100))
            with mock.patch.object(job_manager,'submit',return_value={'submission_id':'s'}),mock.patch.object(job_manager,'read_submission',return_value={}),mock.patch.object(job_manager,'serve',side_effect=serve),mock.patch.object(job_manager,'sweep',side_effect=sweep),mock.patch.object(supervisor,'_attempts_of',side_effect=attempts),mock.patch.object(supervisor,'_cleanups',side_effect=clean):
                outcome=supervisor.supervise(None,None,None,packet,clock=lambda:'2026-09-22T00:00:00Z',sleep=lambda n:None,monotonic=lambda:next(ticks))
            return outcome,queries,counts
    def test_cleanup_sweep_admits_then_omits_intruder_from_cleanup(self):
        outcome,queries,counts=self.run_case()
        self.assertEqual(counts['sweeps'],1)
        self.assertEqual(outcome['unexpected_attempts'],['new-after-stop'])
        self.assertNotIn('new-after-stop',outcome['cleanup'])
        self.assertTrue(all('new-after-stop' not in q for q in queries))
    def test_admission_before_serving_exception_missing_from_accounting(self):
        outcome,queries,counts=self.run_case(late_failure=True)
        self.assertEqual(outcome['admitted_attempts'],[])
        self.assertEqual(outcome['cleanup'],{})
        self.assertEqual(counts['sweeps'],0)

if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in (RealComposedCounterexamples,FailureBoundaryCounterexamples):
        for name in cls.__dict__:
            if name.startswith('test_'):suite.addTest(cls(name))
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'confirmed_counterexamples':result.wasSuccessful(),'seconds':time.monotonic()-started}))
    sys.exit(not result.wasSuccessful())
