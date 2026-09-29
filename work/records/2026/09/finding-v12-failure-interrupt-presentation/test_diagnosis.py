"""Research witnesses of current defects; no engine/provider or deployed stores.

The real two-Job supervisor and manager serving loop run with simulated sweep
reports/time and mocked lifecycle boundaries. These tests assert observed bugs,
not desired acceptance; a later correction must replace them with regressions.
"""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'finding-v12-real-jobs-adoption-gate'))
import two_job_supervisor as subject
import baton_v12.job_manager as jobs
from baton_v12.job_manager import manager
from tools import stage_execution
from baton_v12.worker_manager import ControlStore


class Termination:
    def install(self): pass
    def defer(self): return []
    def restore(self): pass


class Diagnosis(unittest.TestCase):
    def test_terminal_failure_reports_do_not_end_serving_early(self):
        now = [0]
        sleeps = []
        failure = {'jobs':[{'job_id':name,'stages':[{'state':'exceptional','failure':{'category':'authentication_failed','message':'OAuth session expired and could not be refreshed'}},{'state':'blocked'}]} for name in ('job-a','job-b')]}
        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds
        with tempfile.TemporaryDirectory(prefix='w306614-') as root, contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(manager, 'reconcile', return_value=failure))
            sweep = stack.enter_context(mock.patch.object(manager, 'sweep', return_value=failure))
            stack.enter_context(mock.patch.object(subject, 'generations_from', return_value={}))
            stack.enter_context(mock.patch.object(subject, 'verdicts_of', return_value={}))
            stack.enter_context(mock.patch.object(subject.baseline, '_cancel_active', return_value={}))
            stack.enter_context(mock.patch.object(subject.baseline, '_cleanups', return_value={'cleanup':{},'outstanding':[]}))
            stack.enter_context(mock.patch.object(subject.baseline, '_retention_of', return_value='sha256:'+'a'*64))
            result = subject.supervise(object(),object(),mock.Mock(),job_ids=['job-a','job-b'],bounds={'total_seconds':6,'cleanup_seconds':2},outcome_path=str(Path(root)/'outcome.json'),deployment_path='not-opened.json',clock=lambda:'2026-09-29T00:00:00.000Z',sleep=sleep,monotonic=lambda:now[0],termination=Termination())
            self.assertEqual(result['stopped'],'serving-bound-exceeded')
            self.assertEqual(sleeps,[1]*4)
            self.assertEqual(sweep.call_count,4)
            self.assertNotIn('authentication_failed',json.dumps(result))
            self.assertEqual(result['state'],'held')

    def test_main_leaks_retained_interruption_and_closes_handles(self):
        outcome={'state':'held','stopped':'interrupted','held_because':['provider authentication_failed'],'outstanding_cleanup':[]}
        handles=[mock.Mock(),mock.Mock(),mock.Mock()]
        said=io.StringIO()
        with tempfile.TemporaryDirectory(prefix='w306614-main-') as root, contextlib.ExitStack() as stack:
            root=Path(root)
            (root/'deployment.json').write_text(json.dumps({'authority_uuid':'a'*32,'job_bindings':[{'job_id':'job-a'},{'job_id':'job-b'}]}))
            (root/'submission.json').write_text('{}')
            retained=root/'outcome.json'
            def interrupted(*args,**kwargs):
                subject.baseline._publish(str(retained),outcome)
                raise subject.baseline.SupervisorInterrupted('signal 2',outcome)
            stack.enter_context(mock.patch.object(jobs.JobStore,'open',return_value=handles[0]))
            stack.enter_context(mock.patch.object(ControlStore,'open',return_value=handles[1]))
            stack.enter_context(mock.patch.object(stage_execution,'operations_from',return_value=handles[2]))
            stack.enter_context(mock.patch.object(jobs,'submit'))
            stack.enter_context(mock.patch.object(subject,'supervise',side_effect=interrupted))
            with self.assertRaises(subject.baseline.SupervisorInterrupted) as raised:
                subject.main(['--deployment',str(root/'deployment.json'),'--submission',str(root/'submission.json'),'--job-store','unused','--control-store','unused','--incarnation','repro','--outcome',str(retained)],stream=said)
            self.assertEqual(raised.exception.outcome,outcome)
            self.assertEqual(json.loads(retained.read_text()),outcome)
            self.assertEqual(said.getvalue(),'')
            for handle in handles:
                handle.close.assert_called_once()


if __name__=='__main__':
    unittest.main()
