"""Joined owner proof; engine/provider/Git/privileged host are explicit fakes.

No successful Job, attempt, result, cleanup, or enforcement receipt is fabricated.
The provider writes real task-dependent source; the real adapter verifies it.
"""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from tools import next_run_managed as managed
from . import test_next_run_managed as fixture_module


class JoinedFlow(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.ManagedAllocation()
        original = fixture_module.FixtureHost.account
        install = managed.install
        def account(host, name):
            result = original(host, name)
            result['gid'] = os.getgid()  # Simulate setgid without host group changes.
            return result
        def capacity(inputs, **kw):
            return install(dict(inputs, capacity=4), **kw)
        from tests.manager import disk_roots
        disk = disk_roots.disk_backed_root()
        temporary = fixture_module.fixture_module.tempfile.TemporaryDirectory
        with patch.object(fixture_module.fixture_module.tempfile, 'TemporaryDirectory', lambda **kw: temporary(dir=disk, **kw)), patch.object(fixture_module.FixtureHost, 'account', account), patch.object(managed, 'install', capacity):
            self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.host = self.fixture.host
        self.broker = self.fixture.broker
        self.trace = self.fixture.root / 'flow-trace.jsonl'
        self.results = []
        self.host.dispatch = self.dispatch
        self.host.recovery_evidence = self.recovery
        self.fail_start = False
        self.deny_line = False

    def request(self, **data):
        return managed.execute_request(self.broker, managed.read_request(io.BytesIO(json.dumps(data).encode())))

    def invoke(self, record, packet, root, args):
        helper = Path(__file__).with_name('next_run_flow_fixture.py')
        result = subprocess.run([sys.executable, '-I', '-B', str(helper), str(root / 'code'), str(Path(__file__).resolve().parents[2]), str(self.trace), *args], env=managed.dispatch_environment(record, packet, root), cwd=root / 'code', capture_output=True, text=True, timeout=25, umask=0o077)
        # Model uid attribution for files created by this simulated dropped-uid
        # child. Modes remain the real modes created under the production umask.
        for path in Path(record['storage']).rglob('*'):
            self.host.owners.setdefault(str(path), record['uid'])
        return result

    def recovery(self, record, packet, root):
        result = self.invoke(record, packet, root, ['--fixture-recover', str(root / 'runs' / record['run_id'] / 'PACKET.json')])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.recovery_receipt = json.loads(result.stdout)
        return self.recovery_receipt

    def dispatch(self, record, packet, root):
        args = ['--packet', str(root / 'runs' / record['run_id'] / 'PACKET.json')]
        if self.fail_start: args.append('--fixture-fail-start')
        if self.deny_line: args.append('--fixture-deny-line')
        result = self.invoke(record, packet, root, args)
        logs = {p.name: p.read_text() for p in (Path(record['storage']) / 'packet').glob('*') if p.is_file()}
        from baton_v12.worker_manager import ControlStore, attempts
        outcome = json.loads(logs.get('outcome.json', '{}'))
        inventory = None  # No owner store yet is not a fabricated empty receipt.
        if Path(packet['deployment']['control_store']).exists():
            with ControlStore.open_readonly(packet['deployment']['control_store'], incarnation='flow-evidence', clock=managed.enforcement.utc) as control:
                inventory = attempts.runtime_recovery_inventory(control)
        sources = {c['attempt_id']: (Path(c['attribution']['line_path'])/'subject.py').read_text() for c in outcome.get('workload', {}).get('candidates', []) if c.get('attribution')}
        self.results.append(dict(run_id=record['run_id'], returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, logs=logs, trace=self.trace.read_text() if self.trace.exists() else '', packet=packet, inventory=inventory, outcome=outcome, sources=sources))
        return result.returncode

    def task(self, name):
        task = self.fixture.fixture.task(name)
        task['limits'] = dict(provider=3, verification=2, total=12, cleanup=4)
        return task

    def start(self, name):
        with patch.object(managed.baseline, 'verify_worker_image'):
            return self.request(action='start', run=name)

    def completed(self, name, received, task_name=None):
        task_name = name if task_name is None else task_name
        self.assertEqual(self.start(name), 0, json.dumps(self.results, indent=2))
        result = self.results[-1]
        outcome = result['outcome']
        self.assertEqual(outcome['state'], 'settled')
        self.assertEqual(outcome['stage_states'], {'implementation': 'completed'})
        self.assertEqual(outcome['held_because'], [])
        self.assertEqual(outcome['outstanding_cleanup'], [])
        outer = json.loads(result['stdout'])
        self.assertEqual(outer['state'], 'completed')
        self.assertEqual(outer['child_status'], 0)
        self.assertEqual(len(outcome['admitted_attempts']), 1)
        self.assertEqual(len(outcome['workload']['candidates']), 1)
        candidate = outcome['workload']['candidates'][0]
        self.assertEqual(candidate['state'], 'valid')
        self.assertEqual(candidate['verification'], 'passed')
        self.assertEqual(candidate['acceptance'], 'unobserved')  # Independent review remains separate.
        self.assertEqual(result['sources'][candidate['attempt_id']], 'print(' + repr('implemented ' + task_name) + ')\n')
        for item in result['inventory']:
            self.assertTrue(item['token']['returned'])
            self.assertEqual(item['runtime']['execution_runtime'], 'destroyed')
        starts = [json.loads(line)['value'] for line in result['trace'].splitlines() if json.loads(line)['kind'] == 'substantive-work' and json.loads(line)['value']['task'] == task_name]
        self.assertEqual(len(starts), 1)
        elapsed = starts[0]['monotonic'] - received
        self.assertGreater(elapsed, 0)
        self.assertLessEqual(elapsed, 60)
        result['input_receipt_monotonic'] = received
        result['receipt_including_assembly_to_work_seconds'] = elapsed

    def test_two_tasks_and_failed_start_recovery_after_one_installation(self):
        installation = (self.fixture.install / 'installation.json').read_bytes()
        code = {str(p.relative_to(self.fixture.install)): p.read_bytes() for p in (self.fixture.install/'code').rglob('*') if p.is_file()}
        receipts = []
        for name in ('first', 'second'):
            received = time.monotonic()  # Before task input assembly and preparation.
            receipt = self.request(action='prepare', task=self.task(name))
            receipts.append(receipt)
            self.completed(name, received)
        received = time.monotonic()  # Includes failed attempt plus recovery assembly.
        failed = self.request(action='prepare', task=self.task('failed'))
        self.fail_start = True
        self.assertNotEqual(self.start('failed'), 0)
        self.fail_start = False
        self.assertIsNone(self.results[-1]['inventory'])
        state = self.fixture.install/'state'
        preserved = {p.name: p.read_bytes() for p in state.glob('failed.*')}
        with self.assertRaises(managed.nr.Refusal): self.start('failed')
        recovery_task = self.task('recovered')
        recovered = self.request(action='recover', run='failed', task=recovery_task)
        self.assertEqual(self.request(action='recover', run='failed', task=recovery_task), recovered)
        self.assertEqual(self.recovery_receipt['state'], 'ceased')
        self.assertEqual(self.recovery_receipt['attempts'], [])
        for name, data in preserved.items(): self.assertEqual((state/name).read_bytes(), data)
        self.assertEqual(recovered['recovery_from'], 'failed')
        self.completed('recovered', received)
        receipts.extend([failed, recovered])
        self.assertEqual(len({r['uid'] for r in receipts}), 4)
        self.assertEqual(len({r['authority_uuid'] for r in receipts}), 4)
        self.assertEqual(len(self.host.accounts), 4)
        self.assertEqual(len(self.host.admissions), 1)
        self.assertEqual((self.fixture.install/'installation.json').read_bytes(), installation)
        for path, data in code.items(): self.assertEqual((self.fixture.install/path).read_bytes(), data)
        target = os.environ.get('BATON_NEXT_RUN_FLOW_EVIDENCE')
        if target:
            with open(target, 'x') as out:
                json.dump(dict(kind='deterministic joined owner proof', simulated=['host privileges and process uid exclusion', 'engine', 'provider', 'Git command backend'], installed_once=True, receipts=receipts, recovery=self.recovery_receipt, runs=self.results), out, indent=2)
                out.write('\n')

    def test_a_pre_runtime_source_refusal_is_accounted_and_not_cleaned(self):
        """W339626: the live C failure's own shape, through real accounting.

        Run w339626-live-345599 refused BEFORE any runtime with
        `ProfileRefusal: Git line materialization failed: fatal: could not open
        '/dev/null' for reading and writing: Permission denied` -- 125
        characters, recorded in operator-error-347682/diagnostic.json. The
        denial is injected at the Git boundary and answered by the REAL product
        profile code and the REAL owner accounting; neither the refusal nor the
        accounting is stubbed.

        The assertions are the states that run actually recorded, read from
        operator-diagnostics-347468/reports.json: runtime `not-started`,
        cancellation requested with `state` None, `cleanup` None with the
        attempt still in `outstanding_cleanup`, `retry` False, and a held
        outcome carrying the actionable cause. Cleanup must NOT read as
        complete and cessation must NOT be claimed.
        """
        self.request(action='prepare', task=self.task('denied'))
        self.deny_line = True
        try:
            self.assertNotEqual(self.start('denied'), 0)
        finally:
            self.deny_line = False
        result = self.results[-1]
        outcome = result['outcome']

        # 1. THE ORIGINAL ACTIONABLE CAUSE SURVIVES, in the owner's own report.
        failure = outcome.get('serving_failure') or ''
        self.assertIn('Permission denied', failure)
        self.assertIn('could not open', failure)
        self.assertNotEqual(outcome.get('state'), 'settled')
        self.assertNotEqual(outcome.get('stage_states'),
                            {'implementation': 'completed'})
        self.assertTrue(outcome.get('held_because'))
        self.assertEqual(outcome.get('workload', {}).get('candidates', []), [])

        # 2. CLEANUP IS NOT REPORTED COMPLETE and cessation is not claimed.
        self.assertTrue(outcome.get('outstanding_cleanup'),
                        'a pre-runtime refusal must leave cleanup outstanding')
        for held in (outcome.get('cleanup') or {}).values():
            self.assertIsNone(held.get('cleanup'),
                              'no committed cleanup may be claimed')
        for held in (outcome.get('cancellation') or {}).values():
            self.assertEqual(held.get('execution_runtime'), 'not-started')
            self.assertIsNone(held.get('state'),
                              'an unobserved runtime state is not absence')

        # 3. CONSUMPTION AND NO-RETRY ARE PRESERVED.
        self.assertIs(outcome.get('retry'), False)
        with self.assertRaises(managed.nr.Refusal):
            self.start('denied')

        # 4. No fabricated runtime receipt for a runtime that never started.
        for item in result['inventory'] or []:
            self.assertIsNone(item['runtime'].get('runtime_id'))

        # 5. THE LANE STILL WORKS AFTERWARDS. A consumed failure must not
        #    poison the installation; that is what makes this a bounded failure
        #    path rather than a dead one.
        received = time.monotonic()
        self.request(action='prepare', task=self.task('after'))
        self.completed('after', received)

    def test_initial_partial_preparation_continues_to_real_work(self):
        received = time.monotonic()
        task = self.task('first')
        original = managed.bindings._write
        def interrupted(*args, **kw):
            original(*args, **kw)
            raise OSError('simulated packet publication interruption')
        with patch.object(managed.bindings, '_write', interrupted):
            with self.assertRaises(OSError): self.request(action='prepare', task=task)
        receipt = self.request(action='prepare', task=task)
        self.assertEqual(receipt['continuation_of'], 'first')
        self.assertIsNone(receipt['recovery_from'])
        self.assertNotEqual(receipt['run_id'], 'first')
        self.assertEqual(self.request(action='prepare', task=task), receipt)
        self.completed(receipt['run_id'], received, task_name='first')
        with self.assertRaises(managed.nr.Refusal): self.start('first')
        self.assertEqual(len(self.host.admissions), 1)
        target = os.environ.get('BATON_NEXT_RUN_FLOW_EVIDENCE')
        if target:
            with open(target + '.initial.json', 'x') as out:
                json.dump(dict(receipt=receipt, runs=self.results), out, indent=2)
                out.write('\n')
