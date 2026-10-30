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


class IntendedScenarioGuard(unittest.TestCase):
    """W384870 C7: a journal that did not reach the mode's scenario cannot pass."""
    ENVELOPE_REFUSAL = 'ContractRefusal: selected envelope cannot support the populated provider and verification limits'

    def journal(self, mode, *, engine=('ps', 'create', 'start', 'ps', 'inspect', 'stop'), acquire=True, refusals=(), injections=True, extra=()):
        rows = [dict(event='manager_started', manager=1)]
        if acquire:
            rows.append(dict(event='token_acquire', operands=['attempt', 'eligible', 'execution', 'operation', 'permission'], permission=True))
        rows += [dict(event='fake_engine', argv=['docker', step, 'runtime-single-1']) for step in engine]
        rows += [dict(event='start_refused', refusal=refusal) for refusal in refusals]
        if injections and mode in shutdown_fixture.INJECTIONS:
            rows.append(dict(event=shutdown_fixture.INJECTIONS[mode]))
        return rows + list(extra)

    def test_every_mode_passes_its_own_intended_journal(self):
        for mode in shutdown_fixture.RUNTIME_MODES:
            self.assertEqual(shutdown_fixture.unreached(mode, self.journal(mode)), [], mode)
        for mode in shutdown_fixture.CREATE_REFUSAL_MODES:
            scripted = "ContractRefusal: the engine refused to start this runtime: '" + shutdown_fixture.SCRIPTED_CREATE_REFUSAL + "; normal baseline return control'"
            self.assertEqual(shutdown_fixture.unreached(mode, self.journal(mode, engine=('ps', 'create', 'ps'), refusals=[scripted])), [], mode)
        self.assertEqual(shutdown_fixture.unreached('pre_signal', self.journal('pre_signal', engine=(), acquire=False)), [])

    def test_an_early_start_refusal_cannot_pass_an_engine_reaching_mode(self):
        # The eight-day vacuous journal: no create, no start, an envelope refusal.
        vacuous = self.journal('blocked_sweep', engine=('ps',), refusals=[self.ENVELOPE_REFUSAL], injections=False)
        missing = shutdown_fixture.unreached('blocked_sweep', vacuous)
        self.assertTrue(any('never created' in fact for fact in missing), missing)
        self.assertTrue(any('never started' in fact for fact in missing), missing)
        self.assertTrue(any(self.ENVELOPE_REFUSAL in fact for fact in missing), missing)
        self.assertTrue(any('blocked_serving_sweep' in fact for fact in missing), missing)
        # A refused ACQUISITION (the remaining-window refusal) is named too.
        refused = self.journal('unknown', engine=('ps',), injections=False, extra=[dict(event='token_acquire_refused', refusal='ContractRefusal: remaining execution envelope cannot support the populated invocation limits')])
        self.assertTrue(any('remaining execution envelope' in fact for fact in shutdown_fixture.unreached('unknown', refused)))

    def test_an_unscripted_refusal_cannot_pass_a_create_refusal_mode(self):
        # The same vacuous journal satisfied the old `normal` branch: held outcome, final snapshot.
        vacuous = self.journal('normal', engine=('ps',), refusals=[self.ENVELOPE_REFUSAL])
        missing = shutdown_fixture.unreached('normal', vacuous)
        self.assertTrue(any('scripted create refusal never reached' in fact for fact in missing), missing)
        self.assertTrue(any('unscripted refusal' in fact and self.ENVELOPE_REFUSAL in fact for fact in missing), missing)
        started = self.journal('stuck_workload', refusals=["ContractRefusal: the engine refused to start this runtime: '" + shutdown_fixture.SCRIPTED_CREATE_REFUSAL + "'"])
        self.assertTrue(any('started although create was scripted to refuse' in fact for fact in shutdown_fixture.unreached('stuck_workload', started)))

    def test_a_missing_selected_injection_is_detected(self):
        for mode, injection in shutdown_fixture.INJECTIONS.items():
            journal = self.journal(mode, injections=False, **({'engine': ('ps', 'create', 'ps'), 'refusals': ["x: '" + shutdown_fixture.SCRIPTED_CREATE_REFUSAL + "'"]} if mode in shutdown_fixture.CREATE_REFUSAL_MODES else {'engine': (), 'acquire': False} if mode == 'pre_signal' else {}))
            self.assertIn('selected injection ' + injection + ' never happened', shutdown_fixture.unreached(mode, journal), mode)

    def test_a_pre_invocation_signal_mode_must_invoke_nothing(self):
        invoked = self.journal('pre_signal', engine=('ps', 'create'), acquire=True)
        missing = shutdown_fixture.unreached('pre_signal', invoked)
        self.assertIn('pre-invocation signal mode expected no token acquisition', missing)
        self.assertIn('pre-invocation signal mode expected no engine create', missing)

    def test_every_matrix_mode_declares_a_scenario(self):
        modes = ('normal', 'blocked_sweep', 'absent_cleanup', 'delayed_snapshot', 'snapshot_before', 'stuck_snapshot', 'stuck_workload', 'stuck_cleanup', 'stuck_accounting', 'unknown', 'pre_signal')
        self.assertEqual(sorted(modes), sorted(shutdown_fixture.RUNTIME_MODES + shutdown_fixture.CREATE_REFUSAL_MODES + ('pre_signal',)))
        self.assertEqual(shutdown_fixture.unreached('unlisted', self.journal('unlisted')), ['mode unlisted declares no intended scenario'])


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
                # W384870 C7 review 17:17:47Z: the mode must reach ITS scenario; an early
                # start refusal, a missing injection or an unstarted runtime fails it.
                self.assertEqual(shutdown_fixture.unreached(mode, events), [])
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
                        # W384870 C7: the token's lifetime is the controller's permission
                        # envelope (no bare duration, no renewals), not an injected 2 s.
                        for row in rows:
                            policy = row['token']['permission']['policy']
                            self.assertEqual((policy['run'], policy['total_seconds'], policy['cleanup_seconds']), (packet['run_id'], packet['bounds']['total_seconds'], packet['bounds']['cleanup_seconds']))
                            self.assertIsNone(row['token']['seconds'])
                            self.assertEqual((row['token']['renewals'], row['token']['renewals_remaining']), (0, 0))
                        # W384870 C7: the envelope's stop_at is enforced through PRODUCTION
                        # CANCELLATION, not an early expiry reclaim (the controller's own
                        # `held_before_expiry` contract, test_authoring_enforcement): the exact
                        # runtime is stopped despite the blocked/absent serving side, and the
                        # token stays held -- neither returned nor revoked -- for the
                        # stopped-execution settlement owner. Before 30245386 this matrix
                        # injected a 2 s token so expiry reclaim settled it inside the run.
                        for row in rows:
                            self.assertEqual((row['observation']['runtime_id'], row['observation']['state']), ('runtime-single-1', 'quiescent'))
                            self.assertEqual((row['token']['container'], row['token']['returned'], row['token']['revoked']), ('runtime-single-1', False, False))
                            self.assertEqual(row['faults'], [])
                        stops = [row['argv'][-1] for row in events if row['event'] == 'fake_engine' and row['argv'][1] == 'stop']
                        self.assertEqual(set(stops), {'runtime-single-1'}, 'the exact runtime is stopped despite the blocked serving side')
                        self.assertTrue(workload['outstanding_cleanup'], 'pending output/cleanup is retained as an actionable hold')
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
                        # W384870 C7: an engine that cannot be asked preserves the fence and the
                        # hold (`test_unknown_engine_stop_preserves_fence_and_hold_then_retries`):
                        # the token is neither returned nor revoked and the fault is carried.
                        self.assertTrue(any(row.get('token') and row['token']['container'] == 'runtime-single-1' and not row['token']['returned'] and not row['token']['revoked'] for row in rows))
                        self.assertTrue(any((row.get('observation') or {}).get('state') == 'uncertain' for row in rows))
                        self.assertTrue(any('selected fake engine uncertainty' in fault for row in rows for fault in row['faults']))
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
