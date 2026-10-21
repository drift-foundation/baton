"""Offline preparation/consumption evidence; no provider, engine or Git writes.

The composer, manifest validator, packet reader and controller binding are real.
Dispatch tests replace the enforcement invocation and image inspection only;
these are launcher-boundary tests, not substantive-agent startup evidence.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from tools import next_run as nr
from tools import authoring_baseline as baseline

ROOT = Path(__file__).resolve().parents[4]
VECTORS = ROOT / 'work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json'


class NextRun(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='next-run-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'subject.py').write_text('print("before")\n')
        self.runtime = self.root / 'runtime'
        self.runtime.mkdir()
        (self.runtime / 'baton-v12-stack').write_text('fixture runtime bytes; never executed')
        self.installation = self.root / 'installation'
        self.inputs = {'schema': nr.SCHEMA, 'slots': {name: self.slot(index) for index, name in enumerate(['one', 'two'], 1)}}
        nr.install(self.installation, self.inputs)

    def slot(self, index):
        store = self.root / ('slot-' + str(index))
        store.mkdir(mode=0o700)
        return {'base': 'a' * 40, 'compose': {
            'instance': {'authority_store': str(store / 'authority.sqlite3'), 'authority_uuid': '0'*31+'a', 'integration_store': str(store / 'integration.sqlite3'), 'job_store': str(store / 'jobs.sqlite3'), 'control_store': str(store / 'control.sqlite3'), 'integration_profile': {'profile_kind': 'git', 'profile_version': 1, 'integrator_participant': 'baton.integrator', 'instructions_digest': 'sha256:'+'e'*64}, 'retention_policy_digest': 'sha256:'+'5'*64, 'runtime_path': str(self.runtime), 'build_commit': 'b'*40},
            'source_root': str(self.source), 'image_reference': 'fixture:never-executed', 'image_digest': 'sha256:'+'a'*64, 'cli_build': 'fixture', 'manager_source': str(ROOT / 'v12/python'), 'supervisor_path': str(Path(baseline.__file__).resolve()), 'vectors': str(VECTORS), 'credential_sources': None, 'credential_profile': {'api': {'provider': 'fixture', 'reference': 'fixture/one'}}, 'evidence_digest': 'sha256:'+'e'*64, 'provider_network': 'fixture-egress', 'code_boundary': str(ROOT / 'v12/python'), 'work': 'fixture-work', 'claim': 1, 'note': 'offline fixture; no provisioned Authority claimed',
            'participants': {'work_id': '00000000-W'+str(index), 'implementation': 'baton.impl', 'implementation_principal': 'principal:impl', 'review': 'baton.reviewer', 'review_principal': 'principal:review', 'receipts': {'verification': 'baton.verifier', 'review': 'baton.approver-review', 'approval': 'baton.approver'}, 'worker_files': {'opt/baton/claude_agent.py': '0'*64}, 'fixture_files': {}}}}

    def task(self, name='first'):
        return {'schema': nr.TASK, 'run_id': name, 'instructions': 'Change subject.py: '+name, 'files': ['subject.py'], 'base': 'a'*40, 'verification': ['python3', 'subject.py'], 'limits': {'provider': 180, 'verification': 45, 'total': 300, 'cleanup': 60}}

    def prepare(self, slot='one', name='first'):
        return nr.prepare(self.installation, slot, self.task(name))

    def dispatch(self, name='first', controller=None):
        with patch.object(baseline, 'verify_worker_image', return_value={}), patch.object(nr.enforcement, 'main', side_effect=controller or (lambda argv: 0)) as called:
            answer = nr.start(self.installation, name)
            return answer, called

    def test_two_input_only_preparations_bind_distinct_tasks_and_enforced_commands(self):
        started = time.monotonic()
        first = self.prepare()
        second = self.prepare('two', 'second')
        self.assertNotEqual(first['input_sha256'], second['input_sha256'])
        for name in ['first', 'second']:
            run = self.installation / 'runs' / name
            commands = nr.document(run / 'commands.json')
            self.assertIn('tools.next_run', commands['start'])
            self.assertIn('tools.authoring_enforcement', commands['controller'])
            policy = nr.document(run / 'policy.json')
            submission = nr.document(run / 'submission.json')
            self.assertEqual(policy['verification_command_seconds'], 45)
            self.assertEqual(submission['jobs'][0]['execution_limits']['verification_command_seconds'], 45)
            self.assertFalse((run / 'consumed.json').exists())
            answer, called = self.dispatch(name)
            self.assertEqual(answer, 0)
            self.assertEqual(called.call_args.args[0], ['--packet', str(run / 'PACKET.json')])
            self.assertEqual(nr.status(self.installation, name)['work_start'], 'unknown')
        # Deliberately no <=60s product assertion: mocked controller dispatch is
        # not substantive agent work. Retain only a local measurement.
        self.assertGreater(time.monotonic() - started, 0)

    def test_invalid_prerequisite_does_not_consume_then_supported_start_recovers(self):
        self.prepare()
        run = self.installation / 'runs/first'
        with patch.object(baseline, 'verify_worker_image', side_effect=RuntimeError('engine unavailable')), patch.object(nr.enforcement, 'main') as called:
            with self.assertRaisesRegex(RuntimeError, 'engine unavailable'):
                nr.start(self.installation, 'first')
            called.assert_not_called()
        self.assertFalse((run / 'consumed.json').exists())
        self.assertEqual(nr.status(self.installation, 'first')['state'], 'prepared')
        self.dispatch()
        self.assertTrue((run / 'consumed.json').exists())

    def test_unknown_dispatch_is_retained_and_never_replayed(self):
        self.prepare()
        def fail(argv):
            raise RuntimeError('uncertain controller effect')
        with self.assertRaisesRegex(RuntimeError, 'uncertain'):
            self.dispatch(controller=fail)
        self.assertEqual(nr.status(self.installation, 'first')['state'], 'consumed-held')
        with self.assertRaisesRegex(nr.Refusal, 'consumed'):
            self.dispatch()

    def test_stale_task_and_base_refuse_before_slot_reservation(self):
        task = self.task(); task['base'] = 'b'*40
        with self.assertRaisesRegex(nr.Refusal, 'base'):
            nr.prepare(self.installation, 'one', task)
        self.assertFalse((self.installation / 'one.assigned.json').exists())
        self.prepare()
        (self.source / 'subject.py').write_text('changed')
        with self.assertRaises(baseline.SupervisorRefusal):
            self.dispatch()
        self.assertFalse((self.installation / 'runs/first/consumed.json').exists())

    def test_source_links_and_missing_inputs_refuse(self):
        task = self.task(); task['files'] = ['absent']
        with self.assertRaises(FileNotFoundError): nr.prepare(self.installation, 'one', task)
        (self.source / 'linked').symlink_to(self.source / 'subject.py')
        task['files'] = ['linked']
        with self.assertRaises(OSError): nr.prepare(self.installation, 'one', task)
        self.assertFalse((self.installation / 'one.assigned.json').exists())

    def test_collision_and_partial_preparation_never_dispatch(self):
        with patch.object(nr.bindings, 'write', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError): self.prepare()
        self.assertEqual(nr.status(self.installation, 'first')['state'], 'partial')
        with self.assertRaisesRegex(nr.Refusal, 'assigned'): self.prepare()
        with self.assertRaises(FileNotFoundError): self.dispatch()

    def test_partial_recovery_reuses_installation_without_erasing_evidence(self):
        with patch.object(nr.bindings, 'write', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError): self.prepare()
        recovered = nr.recover(self.installation, 'first')
        self.assertEqual(recovered['state'], 'unconsumed-released')
        self.assertTrue((self.installation / 'one.released-first.json').exists())
        self.prepare(name='replacement')
        self.dispatch('replacement')
        self.assertEqual(nr.recover(self.installation, 'replacement')['state'], 'consumed-held')
        self.assertTrue((self.installation / 'one.assigned.json').exists())

    def test_runtime_and_foreign_import_refusal(self):
        (self.runtime / 'baton-v12-stack').write_text('drift')
        with self.assertRaisesRegex(nr.Refusal, 'inventory'): self.prepare()
        self.assertFalse((self.installation / 'one.assigned.json').exists())
        # Real imported-package verifier, unrelated path cannot supply tools.
        packet = {'manager_source': {'path': str(self.root), 'packages': ['tools']}}
        with self.assertRaisesRegex(baseline.SupervisorRefusal, 'outside'):
            baseline.verify_imported_sources(packet)

    def test_missing_output_parent_is_prepared_before_consumption(self):
        self.prepare()
        run = self.installation / 'runs/first'
        packet = nr.document(run / 'PACKET.json')
        # This tests preflight on a selected packet, without amending readiness.
        packet['outcome_path'] = str(run / 'new-output' / 'result.json')
        nr.prerequisites(packet)
        self.assertTrue((run / 'new-output').is_dir())
        self.assertFalse((run / 'consumed.json').exists())
        (run / 'bad-output').symlink_to(self.root)
        packet['outcome_path'] = str(run / 'bad-output' / 'result.json')
        with self.assertRaisesRegex(nr.Refusal, 'link'):
            nr.prerequisites(packet)

    def test_helper_is_required_by_actual_controller_binding(self):
        self.prepare()
        packet = nr.document(self.installation / 'runs/first/PACKET.json')
        del packet['manager_source']['files']['tools/authoring_shutdown.py']
        with self.assertRaisesRegex(RuntimeError, 'helper'):
            nr.enforcement.verify_controller(packet)

    def test_status_does_not_create_missing_run_or_stores(self):
        answer = nr.status(self.installation, 'not-prepared')
        self.assertEqual(answer['state'], 'partial')
        self.assertFalse((self.installation / 'runs/not-prepared').exists())
        self.assertFalse((self.root / 'slot-1/jobs.sqlite3').exists())
