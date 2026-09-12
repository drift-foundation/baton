"""Offline runner correction tests. No engine, model, Git or live Authority calls.

All process/owner answers are unit fixtures; only labelled /tmp evidence is written.
No real review marker or deployment state is created. Fixtures are retained.
"""
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stats_candidate_runner', HERE / 'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def completed(code=0, stdout='{"ID":"unit-container","CPUPerc":"3%"}\n', stderr=''):
    return subprocess.CompletedProcess(['unit-stats'], code, stdout, stderr)


def jobs(state):
    return {'jobs': [{'job_id': name, 'stages': [{'state': state} for _ in range(3)]} for name in ('job-a', 'job-b')]}


class StatsTests(unittest.TestCase):
    def observe(self, result, rows=None):
        with mock.patch.object(runner.subprocess, 'run', side_effect=result if isinstance(result, BaseException) else None, return_value=result) as call:
            answer = runner.stats_observation([{'Id': 'unit-container'}] if rows is None else rows)
        return answer, call

    def test_success_retains_requested_ids_raw_output_and_timing(self):
        answer, call = self.observe(completed())
        self.assertEqual('available', answer['state'])
        self.assertEqual(completed().stdout, answer['stdout'])
        self.assertEqual(['unit-container'], answer['requested_ids'])
        self.assertEqual(0, answer['exit_code'])
        self.assertGreaterEqual(answer['elapsed_seconds'], 0)
        self.assertLessEqual(answer['started_at'], answer['ended_at'])
        call.assert_called_once_with(['docker', 'stats', '--no-stream', '--format', '{{json .}}', 'unit-container'], cwd=runner.CWD, capture_output=True, text=True, timeout=10)

    def test_nonzero_retains_eof_and_partial_output_without_retry(self):
        answer, call = self.observe(completed(1, 'partial row', 'EOF\n'))
        self.assertEqual(('unavailable', 1, 'partial row', 'EOF\n'), (answer['state'], answer['exit_code'], answer['stdout'], answer['stderr']))
        self.assertEqual('nonzero-exit', answer['error']['type'])
        call.assert_called_once()

    def test_requested_empty_or_whitespace_is_unavailable(self):
        for text in ('', ' \n'):
            with self.subTest(text=text):
                answer, call = self.observe(completed(stdout=text))
                self.assertEqual('unavailable', answer['state'])
                self.assertEqual('empty-output', answer['error']['type'])
                call.assert_called_once()

    def test_no_ids_is_not_requested(self):
        answer, call = self.observe(completed(), [])
        self.assertEqual(('not-requested', [], None, ''), (answer['state'], answer['requested_ids'], answer['exit_code'], answer['stdout']))
        call.assert_not_called()

    def test_subprocess_timeout_retains_partial_bytes(self):
        answer, call = self.observe(subprocess.TimeoutExpired(['unit-stats'], 10, output=b'partial', stderr=b'EOF'))
        self.assertEqual(('unavailable', None, 'partial', 'EOF'), (answer['state'], answer['exit_code'], answer['stdout'], answer['stderr']))
        self.assertEqual({'type': 'subprocess.TimeoutExpired', 'timeout_seconds': 10}, answer['error'])
        call.assert_called_once()

    def test_bounded_output_has_explicit_truncation(self):
        answer, _ = self.observe(completed(1, 'x' * 70000, 'y' * 9000))
        self.assertEqual((65536, 8192), (len(answer['stdout']), len(answer['stderr'])))
        self.assertEqual((70000, 9000), (answer['stdout_characters'], answer['stderr_characters']))
        self.assertTrue(answer['stdout_truncated'] and answer['stderr_truncated'])

    def test_watchdog_and_nontelemetry_errors_propagate(self):
        for error in (TimeoutError('watchdog'), FileNotFoundError('engine missing'), ValueError('bug')):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(type(error)):
                    self.observe(error)

    def test_required_inspect_and_label_checks_stay_strict(self):
        with mock.patch.object(runner, 'command', side_effect=['unit-container', RuntimeError('inspect failed')]):
            with self.assertRaisesRegex(RuntimeError, 'inspect failed'):
                runner.containers()
        with mock.patch.object(runner, 'command', side_effect=['unit-container', json.dumps([{'Config': {'Labels': {'baton.v12.authority_uuid': 'foreign'}}}])]):
            with self.assertRaisesRegex(RuntimeError, 'crossed the configured Authority'):
                runner.containers()
        with mock.patch.object(runner.subprocess, 'run', return_value=completed(1, '', 'required command failed')):
            with self.assertRaisesRegex(RuntimeError, 'required command failed'):
                runner.command(['docker', 'ps'])


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained = Path(tempfile.mkdtemp(prefix='w71879-145261-unit-runner-'))
        print('Retained offline fixture root:', cls.retained, flush=True)

    def exercise(self, *, stats=None, fault=None, final_exit=0, terminal=True, current=None, events=None, claim_age=None, stop_error=None):
        root = self.retained / (self._testMethodName + '-' + str(len(list(self.retained.iterdir()))))
        (root / 'evidence').mkdir(parents=True)
        row = {'Id': 'unit-container', 'Config': {'Labels': {'baton.v12.authority_uuid': runner.UUID}},
               'HostConfig': {'NanoCpus': 2000000000, 'Memory': 2147483648, 'PidsLimit': 512}}
        approval = {'verdict': 'accepted', 'review_locator': 'UNIT-ONLY mocked read; no marker file',
                    'config_files': {'stage-execution.json': 'unit', 'submission.json': 'unit'},
                    'reviewed_files': {str(HERE / n): 'unit' for n in ('run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py')}}
        original_read = Path.read_text
        original_exists = Path.exists
        def read(path, *args, **kwargs):
            if path == runner.HERE / 'execution-review.json': return json.dumps(approval)
            if str(path) == '/proc/meminfo': return 'MemAvailable: 30000000 kB\n'
            return original_read(path, *args, **kwargs)
        def exists(path):
            if path == root / 'control.sqlite3': return True
            return original_exists(path)
        clock = SimpleNamespace(now=0)
        def sleep(seconds): clock.now += seconds
        serve = mock.Mock(pid=123456)
        serve.poll.side_effect = [None, None if terminal else 1]
        owner = mock.Mock()
        if claim_age is not None:
            current = {'participant': runner.ACTORS['impl-a']}
            events = [{'cause': 'claimed', 'assignment_ref': current, 'at': (datetime.now(timezone.utc) - timedelta(seconds=claim_age)).isoformat()}]
        owner.assignment_of.return_value = current
        owner.assignment_events.return_value = events or []
        status_calls = []
        observed_after_gap = []
        def command(argv, **kwargs):
            if 'info' in argv:
                return json.dumps({'cpus': 1 if fault == 'capacity' else 20, 'memory': 21474836480})
            if 'submit' in argv: return '{"unit_fixture":true}'
            if argv == runner.STATUS:
                if fault == 'status': raise RuntimeError('required status unavailable')
                status_calls.append(argv)
                if len(status_calls) == 2:
                    # Read through an independent descriptor before successful completion:
                    # this proves the first EOF iteration was persisted and flushed.
                    observed_after_gap.extend(json.loads(line) for line in (root / 'evidence/samples.jsonl').read_text().splitlines())
                return json.dumps(jobs('running' if len(status_calls) == 1 else 'completed'))
            if 'stop' in argv: return 'unit containment'
            raise AssertionError('unplanned command: ' + repr(argv))
        container_calls = []
        def containers():
            container_calls.append(None)
            if len(container_calls) == 1: return []
            if len(container_calls) == 2:
                if fault == 'inspect': raise RuntimeError('required inspect unavailable')
                return [row]
            return []
        def process(argv, **kwargs):
            if argv[:2] == ['docker', 'stats']:
                if stats == 'watchdog':
                    # Invoke the actual handler registered by main, not a surrogate error.
                    registered_alarm[0](None, None)
                if isinstance(stats, BaseException): raise stats
                return stats or completed(1, '', 'EOF')
            self.assertEqual([runner.PYTHON, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], argv)
            return completed(final_exit, 'UNIT final tests', '')
        registered_alarm = []
        def signal_handler(kind, callback):
            registered_alarm.append(callback)
            return 'UNIT prior alarm'
        git_answers = iter([runner.BASE + ' ' + runner.TREE, '', 'UNIT landed candidate tree', '', 'UNIT diff'])
        with ExitStack() as stack:
            def patch(obj, name, **kwargs): return stack.enter_context(mock.patch.object(obj, name, **kwargs))
            patch(runner, 'RUN', new=root)
            patch(Path, 'read_text', new=read); patch(Path, 'exists', new=exists)
            patch(runner, 'sha', return_value='unit')
            patch(runner.os, 'getgroups', return_value=[1001])
            patch(runner.os, 'statvfs', return_value=SimpleNamespace(f_bavail=1 << 30, f_frsize=4096))
            patch(runner, 'baseline', return_value={'UNIT_fixture': True})
            cmd = patch(runner, 'command', side_effect=command)
            patch(runner, 'containers', side_effect=containers)
            patch(runner, 'retained_bytes', return_value=17179869184 if fault == 'storage' else 123)
            patch(runner.Authority, 'open_readonly', return_value=owner)
            patch(runner.subprocess, 'Popen', return_value=serve)
            process_call = patch(runner.subprocess, 'run', side_effect=process)
            stopped = patch(runner, 'stop_serving', side_effect=stop_error)
            patch(runner.signal, 'signal', side_effect=signal_handler)
            timers = patch(runner.signal, 'setitimer')
            patch(runner.time, 'monotonic', side_effect=lambda: clock.now)
            patch(runner.time, 'sleep', side_effect=sleep)
            patch(runner, 'git_read', side_effect=lambda *args: next(git_answers))
            error = None
            try: runner.main()
            except BaseException as failure: error = failure
        result_path = root / 'evidence/run-result.json'
        result = json.loads(result_path.read_text()) if result_path.exists() else None
        samples_path = root / 'evidence/samples.jsonl'
        samples = [json.loads(line) for line in samples_path.read_text().splitlines()] if samples_path.exists() else []
        return SimpleNamespace(error=error, result=result, samples=samples, stopped=stopped,
                               process_call=process_call, timers=timers, command=cmd, flushed=observed_after_gap)

    def test_eof_gap_flushes_surrounding_evidence_and_continues(self):
        held = self.exercise()
        self.assertIsNone(held.error)
        self.assertEqual(2, len(held.samples))
        first = held.flushed[0]
        self.assertEqual('unavailable', first['docker_stats']['state'])
        self.assertEqual('EOF', first['docker_stats']['stderr'])
        self.assertEqual(123, first['retained_bytes'])
        self.assertTrue(first['claims'] and first['status'] and first['runtime_observations'])
        summary = held.result['stats_observations']
        self.assertEqual((1, 1, 0), (summary['unavailable'], summary['not-requested'], summary['available']))
        self.assertEqual('samples.jsonl:1', summary['gaps'][0]['sample'])
        self.assertEqual(1, sum(call.args[0][:2] == ['docker', 'stats'] for call in held.process_call.call_args_list))
        self.assertEqual([1200, 1200, 1199], [call.args[1] for call in held.timers.call_args_list if call.args[1] != 0])
        self.assertTrue(held.result['terminal_both'])
        self.assertEqual(0, held.result['final_test_exit'])

    def test_subprocess_timeout_remains_gap_and_continues(self):
        held = self.exercise(stats=subprocess.TimeoutExpired(['unit-stats'], 10, output=b'partial'))
        self.assertIsNone(held.error)
        self.assertEqual('partial', held.flushed[0]['docker_stats']['stdout'])
        self.assertEqual(1, held.result['stats_observations']['unavailable'])

    def test_actual_registered_watchdog_is_fatal_and_contains(self):
        held = self.exercise(stats='watchdog')
        self.assertIsInstance(held.error, TimeoutError)
        self.assertIn('approved proof wall/active-attempt deadline', held.result['failure'])
        self.assertFalse(held.result['terminal_both'])
        self.assertGreater(held.stopped.call_count, 0)
        self.assertEqual(0, held.result['stats_observations']['unavailable'])

    def test_required_status_inspect_storage_remain_fatal(self):
        for fault in ('status', 'inspect', 'storage'):
            with self.subTest(fault=fault):
                held = self.exercise(fault=fault)
                self.assertIsInstance(held.error, RuntimeError)
                self.assertFalse(held.result['terminal_both'])
                self.assertGreater(held.stopped.call_count, 0)
                held.process_call.assert_not_called()

    def test_host_capacity_refuses_before_submission(self):
        held = self.exercise(fault='capacity')
        self.assertIsInstance(held.error, RuntimeError)
        self.assertIn('host capacity', str(held.error))
        self.assertFalse(any('submit' in call.args[0] for call in held.command.call_args_list))

    def test_missing_claim_timestamp_remains_fatal(self):
        held = self.exercise(current={'participant': runner.ACTORS['impl-a']})
        self.assertIn('no matching claim timestamp', str(held.error))
        held.process_call.assert_not_called()
        self.assertFalse(held.result['terminal_both'])

    def test_active_attempt_deadline_remains_fatal(self):
        held = self.exercise(claim_age=241)
        self.assertIn('approved attempt deadline', str(held.error))
        held.process_call.assert_not_called()

    def test_incomplete_jobs_do_not_become_terminal_from_gap(self):
        held = self.exercise(terminal=False)
        self.assertIn('serve exited before both terminal', str(held.error))
        self.assertFalse(held.result['terminal_both'])
        self.assertEqual(1, held.result['stats_observations']['unavailable'])
        self.assertNotIn('result', held.result)

    def test_final_verification_failure_stays_fatal(self):
        held = self.exercise(final_exit=1)
        self.assertIn('whole-target final tests failed', str(held.error))
        self.assertEqual(1, held.result['final_test_exit'])
        self.assertNotIn('result', held.result)


if __name__ == '__main__':
    began = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'seconds': time.monotonic() - began, 'retained_fixture_root': str(RunnerTests.retained),
              'scope': 'offline mocked process/owner/clock answers; no real review markers, engine, model, Git or live Authority; temporary evidence is UNIT fixture data'}
    (HERE / 'evidence/focused-tests.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
