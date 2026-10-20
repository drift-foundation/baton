"""Bounded shutdown: candidate-native composition and retained honest outcomes."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from tools.authoring_shutdown import Shutdown, bounded
from tests.manager import disk_roots, shutdown_fixture


class FastContract(unittest.TestCase):
    def test_blocking_step_is_interrupted_and_alarm_restored(self):
        handler = signal.getsignal(signal.SIGALRM)
        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, 'publication'):
            with bounded(started + .05, 'publication'):
                time.sleep(5)
        self.assertLess(time.monotonic() - started, 1)
        self.assertEqual(signal.getsignal(signal.SIGALRM), handler)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_one_deadline_reserves_each_finalization_phase_without_reset(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            packet = {'run_id': 'one', 'submission': {'job_id': 'job-one'},
                      'bounds': {'total_seconds': 100, 'cleanup_seconds': 60}}
            deadline = time.monotonic() + 3
            (path / 'request').write_text(json.dumps({'run_id': 'one', 'deadline': deadline}))
            budget = Shutdown(packet, path / 'request', path / 'progress')
            budget.begin()
            self.assertEqual(budget.deadline, deadline)
            deadlines = [budget.until(phase) for phase in ('cleanup', 'accounting', 'workload-publication', 'guard-stop', 'guard-publication')]
            self.assertEqual(deadlines, sorted(deadlines))
            self.assertLess(deadlines[-1], deadline)
            (path / 'request').write_text(json.dumps({'run_id': 'one', 'deadline': deadline + 100}))
            budget.begin()
            self.assertEqual(budget.deadline, deadline)
            self.assertEqual(packet['bounds'], {'total_seconds': 100, 'cleanup_seconds': 60})

    def test_exhausted_step_does_not_execute(self):
        calls = []
        with self.assertRaises(TimeoutError):
            with bounded(time.monotonic() - 1, 'cleanup'):
                calls.append(1)
        self.assertEqual(calls, [])


class Composition(unittest.TestCase):
    def test_real_baseline_shutdown_matrix(self):
        source = Path(__file__).resolve().parents[4]
        retained = os.environ.get('BATON_SHUTDOWN_EVIDENCE')
        if retained:
            output = Path(retained)
            output.mkdir(parents=True, exist_ok=False)
        else:
            output = Path(disk_roots.disk_backed_under(self))
        modes = ('normal', 'blocked_sweep', 'absent_cleanup', 'delayed_snapshot',
                 'snapshot_before', 'stuck_snapshot', 'stuck_workload', 'stuck_cleanup', 'stuck_accounting', 'unknown', 'pre_signal')
        results = []
        for mode in modes:
            with self.subTest(mode=mode):
                root = output / mode
                root.mkdir()
                shutdown_fixture.prepare(source, root, mode)
                started = time.monotonic()
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=os.pathsep.join([str(source / 'v12/python'), str(source / 'v12/python/src')]))
                with (root / 'outer.log').open('w') as log:
                    child = subprocess.Popen([sys.executable, '-B', str(Path(shutdown_fixture.__file__).resolve()), '--fixture', str(source), '--packet', str(root / 'packet.json')], env=env, stdout=log, stderr=subprocess.STDOUT)
                    try:
                        code = child.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=5)
                        self.fail('outer timeout; retained named manager evidence requires cleanup investigation')
                events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
                managers = [row['manager'] for row in events if row['event'] == 'manager_started']
                reaped = [row['manager'] for row in events if row['event'] == 'manager_reaped']
                self.assertTrue(managers)
                self.assertEqual(managers, reaped)
                for pid in managers:
                    with self.assertRaises(ProcessLookupError):
                        os.kill(pid, 0)
                from baton_v12.worker_manager import ControlStore, workspaces
                from tools.authoring_enforcement import utc
                packet = json.loads((root / 'packet.json').read_text())
                with ControlStore.open(packet['deployment']['control_store'], incarnation='shutdown-test-cleanup', clock=utc) as control:
                    held = workspaces.hold_manager_instance(control, str(root / 'storage'))
                    held.release()
                reports = list(root.glob('outcome.json.enforcement-*.json'))
                self.assertEqual(len(reports), 1, (root / 'outer.log').read_text())
                report = json.loads(reports[0].read_text())
                self.assertTrue(report['child_exited'])
                self.assertEqual(report['state'], 'held', 'a fake create/refused workload is never accepted')
                final = any(row['event'] == 'snapshot_replaced' and row['finished'] for row in events)
                outcome = (root / 'outcome.json').exists()
                self.assertEqual(report['original_envelope']['packet']['bounds'], packet['bounds'])
                if mode in ('normal', 'blocked_sweep', 'absent_cleanup', 'snapshot_before', 'stuck_cleanup', 'stuck_accounting', 'unknown'):
                    self.assertTrue(outcome, (root / 'outcome.json.authoring.log').read_text())
                    self.assertTrue(final, report)
                    self.assertNotEqual(report['child_status'], -9)
                    workload = json.loads((root / 'outcome.json').read_text())
                    self.assertEqual(workload['state'], 'held')
                    self.assertFalse(workload['retry'])
                    if mode in ('blocked_sweep', 'absent_cleanup'):
                        rows = list(report['enforcement']['attempts'].values())
                        self.assertTrue(rows)
                        self.assertTrue(all(row['token']['seconds'] == 2 and row['token']['renewals'] == 0 for row in rows))
                        self.assertTrue(all(row['observation']['state'] == 'absent' and row['token']['returned'] for row in rows))
                        self.assertTrue(workload['outstanding_cleanup'], 'pending output/cleanup does not prevent token settlement')
                        request = json.loads(next(root.glob('*.shutdown.json')).read_text())
                        self.assertLessEqual(report['shutdown_progress']['deadline'], request['deadline'])
                        published = [row['monotonic'] for row in events if row['event'] == 'snapshot_replaced' and row['finished']]
                        self.assertLess(max(published), request['deadline'])
                    if mode in ('stuck_cleanup', 'stuck_accounting'):
                        self.assertIn('timed out', str(workload))
                    if mode == 'absent_cleanup':
                        signals = [row for row in events if row['event'] == 'deferred_signal_returned']
                        self.assertEqual(signals[0]['received'], ['signal 15', 'signal 15'])
                    if mode == 'unknown':
                        rows = list(report['enforcement']['attempts'].values())
                        self.assertTrue(any(row.get('token') and row['token']['revoked'] and not row['token']['returned'] for row in rows))
                        self.assertTrue(any((row.get('observation') or {}).get('state') == 'uncertain' for row in rows))
                elif mode == 'pre_signal':
                    self.assertFalse(report['author_invocation_started'])
                    self.assertFalse(outcome)
                    self.assertTrue(final)
                else:
                    self.assertIsNotNone(report['shutdown_progress'])
                    self.assertTrue(report['enforcement']['faults'] or report['shutdown_progress']['faults'])
                    if mode == 'stuck_workload':
                        self.assertFalse(outcome)
                        self.assertIn('workload publication', str(report))
                    else:
                        self.assertTrue(outcome)
                        self.assertFalse(final)
                elapsed = time.monotonic() - started
                self.assertLess(elapsed, 15)
                results.append(dict(case=mode, code=code, seconds=elapsed, managers_reaped=reaped,
                                    manager_pids_absent=managers, guard_reacquired=True,
                                    outcome_present=outcome, final_snapshot=final))
                (output / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
