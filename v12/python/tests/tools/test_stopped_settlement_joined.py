"""W375446: real worker exchange, installed argv, synthetic OCI cessation."""
import io
import json
import os
from pathlib import Path
from unittest import mock

from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, attempts, exchange, launch, tokens, sessions, custody
from baton_v12.worker_manager import stopped_settlement as settlement
from tools import job_manager, stack_command, stopped_settlement as command
from tests.job_manager import fixtures
from tests.manager import test_worker_image  # installs the ordinary worker import path
# W384870: through the module, so the sibling TestCase is not collected twice.
from . import test_stopped_settlement_command as settlement_command
import baton_worker


class JoinedSettlement(settlement_command.InstalledSettlement):
    def chain(self, delivery, document, **unused):
        # The accepted parent fixture calls this before any worker response.
        # Here the production exchange loop writes every event itself.
        self.provider_calls = []
        calls = self.provider_calls
        class FailedAgent:
            def work(self, seen, declared):
                calls.append('work')
                raise RuntimeError('deterministic provider failure; no model invoked')
            def consider(self, seen, request):
                raise AssertionError('unexpected provider operation')
        seen = {'schema': launch.EXCHANGE_SCHEMA, 'session': self.SESSION,
                'contract': 'v12-assignment-1', 'role': 'implementation',
                'transport': exchange.EXCHANGE_TRANSPORT}
        roots = Path(self.storage) / self.ATTEMPT
        with mock.patch.object(baton_worker, 'INPUT_ROOT', str(roots / 'inputs')), mock.patch.object(baton_worker, 'OUTPUT_ROOT', str(roots / 'workspace')):
            self.assertEqual(baton_worker.serve_exchange(FailedAgent(), seen, self.SESSION, delivery.command_root, delivery.event_root), 1)
        self.assertEqual(self.provider_calls, ['work'])
        view = exchange.observation(delivery)
        self.assertEqual(view['state'], 'faulted')
        self.assertIsNone(view['terminal']['manifest_digest'])
        self.assertIsNone(view['terminal']['disposition'])
        return view

    def argv(self, verb, request):
        path = Path(self.root) / 'joined-request.json'
        path.write_text(json.dumps(request))
        output = io.StringIO()
        with mock.patch.object(stack_command, 'frozen', return_value=True), mock.patch.object(stack_command, 'executable', return_value=self.places['command']), mock.patch.object(job_manager, '_utc_clock', return_value=lambda: fixtures.NOW), mock.patch('sys.stdout', output):
            self.assertEqual(stack_command.main(['manager', verb, '--instance', self.places['instance'], '--document', str(path)]), 0)
        return json.loads(output.getvalue())['settlement']

    def test_real_fault_preserves_files_authority_and_no_verdict(self):
        request = self.preview()['request']
        roots = Path(self.storage) / self.stage['attempt_id']
        retained = roots / 'workspace' / 'partial-output'
        retained.write_bytes(b'partial failed execution')
        def files():
            return {str(p.relative_to(roots)): p.read_bytes() for p in roots.rglob('*') if p.is_file()}
        before_files = files()
        with Authority.open_readonly(self.authority_path, expected_authority_uuid=self.config['authority_uuid']) as authority:
            before_work = authority.project_work(self.work)
        before_runtime = attempts.attempt_runtime_of(self.control, self.stage['attempt_id'])
        with mock.patch.object(job_manager._ReclaimAdapter, 'stop_expired', side_effect=AssertionError('stop')), mock.patch.object(custody, 'normalize_directory', side_effect=AssertionError('normalize')), mock.patch.object(sessions, 'close_agent_session', side_effect=AssertionError('native close')):
            result = self.argv('settle-stopped', request)
        self.assertEqual(result['state'], 'settled')
        self.assertEqual(result['receipt']['result_consumption'], 'unresolved')
        self.assertEqual(files(), before_files)
        self.assertEqual(attempts.attempt_runtime_of(self.control, self.stage['attempt_id']), before_runtime)
        with Authority.open_readonly(self.authority_path, expected_authority_uuid=self.config['authority_uuid']) as authority:
            self.assertEqual(authority.project_work(self.work), before_work)
        self.assertEqual(self.provider_calls, ['work'])
        self.assertEqual(exchange.observation(self.delivery)['state'], 'faulted')
        self.assertTrue(all(call[1] in ('inspect', 'ps') for call in self.engine_calls))
        self.assertEqual(self.argv('settlement-status', request), result)

    def crash_cut(self, cut):
        request = self.preview()['request']
        real = ControlStore.transact
        def interrupt(store, operation, kind, signature, action):
            result = real(store, operation, kind, signature, action)
            if kind == cut:
                raise RuntimeError('lost reply after ' + cut)
            return result
        with mock.patch.object(ControlStore, 'transact', interrupt):
            with self.assertRaises(RuntimeError):
                self.argv('settle-stopped', request)
        state = self.argv('settlement-status', request)['state']
        self.assertEqual(state, {settlement.INTENT: 'held', settlement.OUTCOME: 'release-pending', tokens.RETURNED_KIND: 'returned-receipt-pending', settlement.RECEIPT: 'settled'}[cut])
        if cut in (tokens.RETURNED_KIND, settlement.RECEIPT):
            with mock.patch.object(tokens.Governance, 'release', side_effect=AssertionError('duplicate return')), mock.patch('tools.stopped_settlement._runtime', side_effect=lambda _: object()):
                self.assertEqual(self.argv('settle-stopped', request)['state'], 'settled')
        else:
            self.assertEqual(self.argv('settle-stopped', request)['state'], 'settled')
        self.assertEqual(self.provider_calls, ['work'])

    def test_crash_after_intent(self):
        self.crash_cut(settlement.INTENT)

    def test_crash_after_outcome(self):
        self.crash_cut(settlement.OUTCOME)

    def test_crash_after_return(self):
        self.crash_cut(tokens.RETURNED_KIND)

    def test_crash_after_receipt(self):
        self.crash_cut(settlement.RECEIPT)

    def test_joined_fence_rejects_acting_operations(self):
        request = self.preview()['request']
        core = request['request']
        real = ControlStore.transact
        checked = []
        def interleave(store, operation, kind, signature, action):
            result = real(store, operation, kind, signature, action)
            if kind == settlement.INTENT:
                token = core['token']
                self.assertFalse(tokens.effects_permitted(store, token))
                for acting in (
                    lambda: tokens.renew(store, token, execution=core['attempt_id'], operation=core['start_operation_id'], expected_revision=0),
                    lambda: tokens.admit_activation(store, token, container=core['runtime_id']),
                    lambda: tokens.journal_launch(store, token, core['start_operation_id']),
                    lambda: tokens.bind_container(store, token, core['runtime_id'], launch=core['start_operation_id'])):
                    with self.assertRaises(ContractRefusal):
                        acting()
                    checked.append(True)
            return result
        with mock.patch.object(ControlStore, 'transact', interleave):
            self.assertEqual(self.argv('settle-stopped', request)['state'], 'settled')
        self.assertEqual(len(checked), 4)

    def test_inaccessible_output_needs_no_scan_or_normalization(self):
        request = self.preview()['request']
        workspace = Path(self.storage) / self.ATTEMPT / 'workspace'
        mode = workspace.stat().st_mode & 0o777
        os.chmod(workspace, 0)
        try:
            with mock.patch('os.scandir', side_effect=PermissionError('unreadable output')), mock.patch.object(custody, 'normalize_directory', side_effect=AssertionError('normalize')):
                self.assertEqual(self.argv('settle-stopped', request)['state'], 'settled')
        finally:
            os.chmod(workspace, mode)

    def test_unsettled_start_and_helpers_hold(self):
        request = self.preview()['request']
        before = self.logical()
        with mock.patch.object(attempts, 'start_submission_returned', return_value=False):
            with self.assertRaises(ContractRefusal):
                self.argv('settle-stopped', request)
        self.assertEqual(self.logical(), before)
        runtime = command._runtime
        for helpers in (None, [{'helper_identity': 'uncertain-writer'}]):
            def observe(deployment):
                adapter = runtime(deployment)
                adapter.surviving_helpers = lambda: helpers
                return adapter
            with mock.patch.object(command, '_runtime', side_effect=observe):
                self.assertEqual(self.argv('settle-stopped', request)['state'], 'held')
            self.assertEqual(self.logical(), before)
