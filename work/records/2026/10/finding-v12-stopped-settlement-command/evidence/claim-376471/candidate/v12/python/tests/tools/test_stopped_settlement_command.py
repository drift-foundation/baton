"""Installed selection over real stores and exchange files; synthetic OCI only."""
import copy
import io
import json
import os
from pathlib import Path
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import episodes, scheduler, submission, submit
from baton_v12.worker_manager import attempts, exchange, stopped_settlement as owner, tokens
from tools import instance, job_manager, single_worker, stopped_settlement as command
from .test_stage_execution import ServingCase
from .test_single_worker import Engine
from tests.manager.test_exchange import Home
from tests.job_manager import fixtures


class InstalledSettlement(ServingCase, Home):
    def setUp(self):
        super().setUp()
        self.places = instance.layout(self.root)
        Path(self.places['stores']).mkdir()
        os.rename(self.authority_path, self.places['authority_store'])
        self.authority_path = self.places['authority_store']
        self.config['authority_store'] = self.authority_path
        self.job_path = self.places['job_store']
        self.control_path = self.places['control_store']
        distro = Path(self.places['distro'])
        distro.mkdir(parents=True)
        Path(self.places['command']).write_text('deterministic packaged fixture')
        selector = instance.emit(self.root, authority_uuid=self.config['authority_uuid'], identity={'fixture': True}, runtime=instance.manifest(distro), now=1)
        instance.publish(self.places['instance'], selector)
        self.document = self.composed_document()
        Path(self.places['deployment']).write_text(json.dumps(self.document))
        # This fixture's scratch is outside its nominated checkout, exactly
        # as existing deployment tests arrange it. No validation is bypassed.
        self.patch_checkout = mock.patch('tools.stage_execution._checkout', return_value=self.checkout)
        self.patch_checkout.start()
        self.addCleanup(self.patch_checkout.stop)
        self.jobs, self.control = self.stores('settlement-fixture')
        submit(self.jobs, self.submission)
        self.engine = Engine()
        self.operations = self.operations(self.jobs, self.control, self.engine)
        self.addCleanup(self.operations.close)
        self.commanded(self.jobs, self.operations)
        self.stage = episodes.attempting(submission.stages_of(self.jobs, 'job-a')[0], episodes.episode_of(self.jobs, 'job-a/implementation', 1))
        # The real scheduler supplies the recorded owner that an installed
        # pooled deployment uses. The execution itself used ordinary owners.
        pool = {'schema': scheduler.POOL_SCHEMA, 'variant': 'fixture', 'separation_class': 'same-provider/same-model-fresh-context', 'workers': [
            {'worker_id': 'implementation-worker', 'lane': 'implementation', 'participant': self.config['participant'],
             'profile_name': self.config['profile_name'], 'profile_digest': self.config['profile_digest'], 'eligible_kinds': ['implementation']}]}
        scheduler.activate_pool(self.jobs, pool, {self.config['participant']: self.principal})
        scheduler.reserve(self.jobs, self.stage)
        self.delivery = single_worker.settlement_delivery(self.config, self.jobs, self.control, self.stage)
        request = exchange.observation(self.delivery)['command']
        self.ATTEMPT = self.stage['attempt_id']
        self.SESSION = single_worker._Observation._session_of(self.ATTEMPT)
        self.chain(self.delivery, request, answered=[], ending='faulted', stopped='describe', disposition=None, manifest_digest=None, fault_code='agent')
        self.engine.running = False
        self.operations.close()
        from baton_v12.worker_manager import workspaces
        workspaces.held_manager_instance(self.storage).release()
        from baton_v12.worker_manager import ControlStore
        self.control.close()
        self.control = ControlStore.open_readonly(self.control_path, incarnation="fixture-reader", clock=lambda: fixtures.NOW)
        self.addCleanup(self.control.close)
        self.engine_calls = []
        def reading(argv, *, seconds=None):
            self.engine_calls.append(argv)
            if argv[1] == 'ps':
                return Engine.answer()
            if argv[1] != 'inspect':
                raise AssertionError('settlement engine effect: ' + repr(argv))
            return self.engine(argv, seconds=seconds)
        self.runner = mock.patch.object(single_worker, 'effective_engine_run', return_value=reading)
        self.runner.start()
        self.addCleanup(self.runner.stop)

    def bound(self, document, **members):
        return {"session": self.SESSION, "attempt_id": self.ATTEMPT,
                "sequence_id": document["sequence_id"],
                "command_digest": exchange.observation(self.delivery)["command"]["command_digest"], **members}

    def call(self, verb, request=None, **selection):
        return command.execute(verb, self.places['instance'], document=request,
            clock=lambda: fixtures.NOW, **selection)

    def preview(self):
        return self.call('settlement-preview', job_id='job-a', stage_id=self.stage['stage_id'], episode=1, operation_id='operator-selection')

    def logical(self):
        return tuple(tuple(owner._connection.iterdump()) for owner in (self.jobs, self.control))

    def test_preview_settle_status_and_exact_replay(self):
        before = self.logical()
        preview = self.preview()
        self.assertEqual(preview['eligibility']['eligibility'], 'eligible')
        self.assertFalse(preview['eligibility']['reserved'])
        self.assertEqual(self.logical(), before)
        request = preview['request']
        self.assertEqual(self.call('settlement-status', request)['settlement']['state'], 'not-selected')
        before_axes = attempts.attempt_runtime_of(self.control, self.stage['attempt_id'])
        settled = self.call('settle-stopped', request)
        self.assertEqual(settled['settlement']['state'], 'settled')
        self.assertEqual(settled['settlement']['outcome']['execution_outcome'], 'failed-stopped')
        self.assertEqual(attempts.attempt_runtime_of(self.control, self.stage['attempt_id']), before_axes)
        self.assertEqual(exchange.observation(self.delivery)['state'], 'faulted')
        before = self.logical()
        with mock.patch.object(Authority, 'open_readonly', side_effect=AssertionError('replay Authority')), mock.patch.object(single_worker, 'settlement_delivery', side_effect=AssertionError('replay launch')):
            self.assertEqual(self.call('settle-stopped', request), settled)
            self.assertEqual(self.call('settlement-status', request), settled)
        self.assertEqual(self.logical(), before)

    def test_running_preview_and_settlement_hold_without_selection(self):
        self.engine.running = True
        preview = self.preview()
        self.assertEqual(preview['eligibility']['eligibility'], 'held')
        before = self.logical()
        self.assertFalse(self.call('settle-stopped', preview['request'])['settlement']['selected'])
        self.assertEqual(self.logical(), before)

    def test_foreign_selection_and_changed_request_refuse(self):
        request = self.preview()['request']
        for key, value in (('job_id', 'other'), ('stage_id', 'other'), ('episode', 2)):
            changed = copy.deepcopy(request)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ContractRefusal):
                self.call('settle-stopped', changed)
        for key, value in (('attempt_id', 'other'), ('runtime_id', 'other'), ('failure_digest', 'sha256:' + 'f' * 64)):
            changed = copy.deepcopy(request)
            changed['request'][key] = value
            with self.subTest(key=key), self.assertRaises(ContractRefusal):
                self.call('settle-stopped', changed)
        self.call('settle-stopped', request)
        changed = copy.deepcopy(request)
        changed['request']['token']['generation'] += 1
        with self.assertRaises(ContractRefusal):
            self.call('settlement-status', changed)

    def test_packaged_manager_dispatch_reads_status(self):
        from tools import stack_command
        request = self.preview()['request']
        path = Path(self.root) / 'request.json'
        path.write_text(json.dumps(request))
        output = io.StringIO()
        with mock.patch('sys.stdout', output):
            self.assertEqual(stack_command.main(['manager', 'settlement-status', '--instance', self.places['instance'], '--document', str(path)]), 0)
        self.assertEqual(json.loads(output.getvalue())['settlement']['state'], 'not-selected')

    def test_installed_argv_preview_and_settle_with_package_identity(self):
        from tools import stack_command
        output = io.StringIO()
        with mock.patch.object(stack_command, 'frozen', return_value=True), mock.patch.object(stack_command, 'executable', return_value=self.places['command']), mock.patch.object(job_manager, '_utc_clock', return_value=lambda: fixtures.NOW), mock.patch('sys.stdout', output):
            self.assertEqual(stack_command.main(['manager', 'settlement-preview', '--instance', self.places['instance'], '--job', 'job-a', '--stage', self.stage['stage_id'], '--episode', '1', '--operation-id', 'installed-argv']), 0)
            preview = json.loads(output.getvalue())
            self.assertEqual(preview['eligibility']['eligibility'], 'eligible')
            path = Path(self.root) / 'argv-request.json'
            path.write_text(json.dumps(preview['request']))
            output.seek(0)
            output.truncate()
            self.assertEqual(stack_command.main(['manager', 'settle-stopped', '--instance', self.places['instance'], '--document', str(path)]), 0)
            self.assertEqual(json.loads(output.getvalue())['settlement']['state'], 'settled')
            with mock.patch.object(stack_command, 'executable', return_value='/another/package'):
                with self.assertRaises(instance.InstanceRefusal):
                    stack_command.main(['manager', 'settlement-status', '--instance', self.places['instance'], '--document', str(path)])

    def test_stale_assignment_refuses_new_selection_but_committed_replay_survives(self):
        request = self.preview()['request']
        with mock.patch.object(command._AssignmentReader, 'assignment_of', return_value=None):
            with self.assertRaises(ContractRefusal) as refused:
                self.call('settle-stopped', request)
            self.assertEqual(refused.exception.category, 'stale-assignment')
        self.assertEqual(self.call('settlement-status', request)['settlement']['state'], 'not-selected')
        self.call('settle-stopped', request)
        with mock.patch.object(command._AssignmentReader, 'assignment_of', side_effect=AssertionError('independent disposition read')):
            self.assertEqual(self.call('settle-stopped', request)['settlement']['state'], 'settled')

    def test_readonly_surfaces_never_open_writable_handles_or_runtime_status(self):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        request = self.preview()['request']
        before = self.logical()
        with mock.patch.object(ControlStore, 'open', side_effect=AssertionError('writable control')), mock.patch.object(JobStore, 'open', side_effect=AssertionError('writable Jobs')), mock.patch.object(Authority, 'open', side_effect=AssertionError('writable Authority')):
            self.preview()
            with mock.patch.object(command, '_runtime', side_effect=AssertionError('status inspected engine')):
                self.call('settlement-status', request)
        self.assertEqual(self.logical(), before)

    def test_return_pending_recovery_and_operation_collision(self):
        request = self.preview()['request']
        with mock.patch.object(tokens.Governance, 'release', side_effect=RuntimeError('interrupted before return')):
            with self.assertRaises(RuntimeError):
                self.call('settle-stopped', request)
        self.assertEqual(self.call('settlement-status', request)['settlement']['state'], 'release-pending')
        changed = copy.deepcopy(request)
        changed['operation_id'] = 'second-selection'
        changed['request']['operation_id'] = command._operation(changed)
        with self.assertRaises(ContractRefusal):
            self.call('settle-stopped', changed)
        with mock.patch.object(Authority, 'open_readonly', side_effect=AssertionError('resumed Authority')), mock.patch.object(single_worker, 'settlement_delivery', side_effect=AssertionError('resumed launch')):
            self.assertEqual(self.call('settle-stopped', request)['settlement']['state'], 'settled')

    def test_malformed_request_and_changed_package_refuse_before_writes(self):
        from baton_v12.worker_manager import ControlStore
        request = self.preview()['request']
        changed = copy.deepcopy(request)
        del changed['request']['attempt_id']
        with mock.patch.object(ControlStore, 'open', side_effect=AssertionError('opened writable')):
            with self.assertRaises(ContractRefusal):
                self.call('settle-stopped', changed)
            Path(self.places['command']).write_text('replaced package')
            with self.assertRaises(instance.InstanceRefusal):
                self.call('settle-stopped', request)

    def test_instance_busy_refuses_and_invocation_is_exclusive(self):
        import subprocess
        import sys
        from tools.fresh_attempt_ports import InstanceOwnership
        request = self.preview()['request']
        # An actual separate process owns the product guard; no engine is run.
        script = '''import sys
from baton_v12.worker_manager import ControlStore, workspaces
with ControlStore.open_readonly(sys.argv[1], incarnation="guard-proof", clock=lambda: "2026-09-02T00:00:00.000Z") as c:
 with workspaces.hold_manager_instance(c, sys.argv[2]):
  print("held", flush=True)
  sys.stdin.readline()
'''
        child = subprocess.Popen([sys.executable, '-c', script, self.control_path, self.storage], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'held')
            with self.assertRaises(ContractRefusal):
                self.call('settle-stopped', request)
        finally:
            child.communicate('\n', timeout=10)
        ownership = InstanceOwnership.of(self.control, self.document)
        with ownership.invocation('settlement:' + request['request']['attempt_id']):
            with self.assertRaises(ContractRefusal):
                self.call('settle-stopped', request)
        self.assertEqual(self.call('settlement-status', request)['settlement']['state'], 'not-selected')

    def test_unknown_and_foreign_engine_answers_hold_exact_generation(self):
        for runtime, running in (('foreign-runtime', False), (self.engine.runtime_id, None)):
            with self.subTest(runtime=runtime, running=running):
                self.engine.runtime_id, self.engine.running = runtime, running
                preview = self.preview()
                self.assertEqual(preview['eligibility']['eligibility'], 'held')
                before = self.logical()
                result = self.call('settle-stopped', preview['request'])['settlement']
                self.assertFalse(result['selected'])
                self.assertEqual(self.logical(), before)
