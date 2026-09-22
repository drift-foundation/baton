"""Focused partial-review checks; all runtime/provider work is simulated."""
import sys,json,time,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
import supervisor
from test_supervisor import TheSupervisorShutsDownWhatItStarted as Shutdown
class RemainingEdges(unittest.TestCase):
    def test_unknown_stage_still_skips_known_attempt_cancellation(self):
        ops=mock.Mock(); uncertainty=[]
        result=supervisor._cancel_active(ops,None,{}, {'known-attempt':None},{},uncertainty,reason='serving-failed')
        ops.cancel_attempt.assert_not_called()
        self.assertTrue(result['known-attempt']['requested'])
        self.assertIn('nothing of this run is executing',result['known-attempt']['why'])
    def test_interrupt_in_cancel_escapes_current_handler(self):
        ops=mock.Mock();ops.cancel_attempt.side_effect=KeyboardInterrupt('during cancel')
        with self.assertRaises(KeyboardInterrupt):
            supervisor._cancel_active(ops,None,{}, {'a':'implementation'}, {'implementation':'waiting'},[],reason='interrupted')
if __name__=='__main__':
    suite=unittest.TestSuite()
    for cls in (Shutdown,RemainingEdges):
        for name in cls.__dict__:
            if name.startswith('test_'):suite.addTest(cls(name))
    started=time.monotonic();r=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'seconds':time.monotonic()-started,'meaning':'five partial-fix checks plus two remaining-defect counterexamples'}))
    sys.exit(not r.wasSuccessful())
