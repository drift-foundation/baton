"""The two research witnesses, CONVERTED to regressions. No engine, provider or stores.

WHAT THESE USED TO ASSERT, and why they no longer do. The research claim (tuner 306616)
wrote these to localise two defects, and `FINDING.md` says plainly that a later correction
"must replace them with regressions". This is that replacement, in place, so the record of
what was wrong stays next to the check that it is not wrong any more:

  `test_terminal_failure_reports_do_not_end_serving_early` asserted that a run whose two
  Jobs had BOTH failed kept sleeping to its serving bound -- `sleeps == [1] * 4`, four
  sweeps, and no `authentication_failed` anywhere in the outcome. It now asserts the
  opposite ending, and the original witness's own fixture is kept: the real supervisor,
  the real `serve` loop, mocked sweeps and a simulated clock. The ONE thing added is a
  readable status projection, because the defect was precisely that nothing read one.

  `test_main_leaks_retained_interruption_and_closes_handles` asserted that
  `SupervisorInterrupted` escaped `main`, that stdout was EMPTY and that the handles were
  closed anyway. It now asserts the concise presentation and exit 130, and it still
  asserts the two things that were always correct: the outcome is on disk and every
  handle is closed.

`test_correction.py` holds the rest of the acceptance matrix. These remain deterministic
localisation-grade fixtures, not connected live acceptance.
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
    def test_terminal_failure_reports_END_serving_promptly(self):
        now = [0]
        sleeps = []
        reports = []
        # THE SWEEP REPORT THE WITNESS USED, unchanged: this is what `serve` sees, and the
        # point of the original finding is that the supervisor's predicate never looked at
        # it or at anything else about the Jobs.
        failure = {'jobs':[{'job_id':name,'stages':[{'state':'exceptional','failure':{'category':'authentication_failed','message':'OAuth session expired and could not be refreshed'}},{'state':'blocked'}]} for name in ('job-a','job-b')]}
        # AND THE CANONICAL STATUS PROJECTION, which is what the correction reads. Stage
        # `kind` and `state` are the vocabulary `_attempts_of`/`_terminal` already use.
        projection = {'jobs':[{'job_id':name,'execution_limits':{},'stages':[{'kind':'implementation','state':'exceptional','attempt_id':f'attempt-{name}','episodes':[]},{'kind':'review','state':'blocked','episodes':[]}]} for name in ('job-a','job-b')]}
        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds
        with tempfile.TemporaryDirectory(prefix='w306614-') as root, contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(manager, 'reconcile', return_value=failure))
            sweep = stack.enter_context(mock.patch.object(manager, 'sweep', return_value=failure))
            stack.enter_context(mock.patch.object(jobs, 'status', return_value=projection))
            stack.enter_context(mock.patch.object(subject, 'generations_from', return_value={}))
            stack.enter_context(mock.patch.object(subject, 'verdicts_of', return_value={}))
            stack.enter_context(mock.patch.object(subject.baseline, '_cancel_active', return_value={}))
            stack.enter_context(mock.patch.object(subject.baseline, '_cleanups', return_value={'cleanup':{},'outstanding':[]}))
            stack.enter_context(mock.patch.object(subject.baseline, '_retention_of', return_value='sha256:'+'a'*64))
            result = subject.supervise(object(),object(),mock.Mock(),job_ids=['job-a','job-b'],bounds={'total_seconds':6,'cleanup_seconds':2},outcome_path=str(Path(root)/'outcome.json'),deployment_path='not-opened.json',clock=lambda:'2026-09-29T00:00:00.000Z',sleep=sleep,monotonic=lambda:now[0],termination=Termination(),report=reports.append)
            # WAS: 'serving-bound-exceeded', sleeps [1,1,1,1], four sweeps.
            self.assertEqual(result['stopped'],'pipelines-terminal')
            self.assertEqual(sleeps,[])
            # AND NOT ONE SWEEP, which I had guessed wrong and measured right: `serve`
            # asks the predicate BEFORE its first sweep, so a run whose Jobs are already
            # terminal when serving opens ends without sweeping at all. In a real run the
            # first tick finds queued stages, `_terminal` answers None, and serving
            # proceeds normally -- this fixture starts at the end on purpose.
            self.assertEqual(sweep.call_count,0)
            # WAS: no report at all until the run was over.
            self.assertEqual(len(reports),2)
            for name in ('job-a','job-b'):
                self.assertTrue(any(f'Job {name} FAILED' in one for one in reports),reports)
                self.assertEqual(result['pipelines'][name]['reached'],'exceptional')
            self.assertEqual(result['state'],'held')

    def test_main_PRESENTS_the_retained_interruption_and_closes_handles(self):
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
            # WAS: assertRaises(SupervisorInterrupted) out of `main`, with empty stdout.
            status=subject.main(['--deployment',str(root/'deployment.json'),'--submission',str(root/'submission.json'),'--job-store','unused','--control-store','unused','--incarnation','repro','--outcome',str(retained)],stream=said)
            self.assertEqual(status,130)
            self.assertIn('interrupted: signal 2',said.getvalue())
            self.assertIn(str(retained),said.getvalue())
            # UNCHANGED AND STILL REQUIRED: the outcome is on disk and every handle closed.
            self.assertEqual(json.loads(retained.read_text()),outcome)
            for handle in handles:
                handle.close.assert_called_once()


if __name__=='__main__':
    unittest.main()
