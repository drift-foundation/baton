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
from tools import job_manager, single_worker, stack_command, stopped_settlement as command
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

    # W386766 (owner ruling 2026-11-28), on the real exchange and the composition's own removal. The M386700
    # shape: a real agent fault after `describe`, settled stopped, then `settlement-remove`. Before the removal
    # takes the exchange its terminal is retained; afterwards the episode is over -- status, the sweep and the
    # display all agree with the durable evidence, across a restart, and nothing is dispatched again.

    def removing_engine(self):
        """The fixture engine, except that `rm` removes and a removed identity then inspects absent."""
        engine, real = self.engine, type(self.engine).__call__

        class Removing(type(engine)):
            def __call__(inner, argv, *, seconds=None):
                if argv[1] == "rm":
                    engine.vectors.append(list(argv))
                    engine.runtime_id = None
                    return engine.answer()
                if argv[1] == "inspect" and engine.runtime_id is None:
                    engine.vectors.append(list(argv))
                    return engine.answer(status=1, stderr="Error response from daemon: No such container: " + argv[-1])
                return real(engine, argv, seconds=seconds)
        removing = Removing.__new__(Removing)
        removing.__dict__ = engine.__dict__
        return removing

    def composed(self, incarnation):
        from baton_v12.worker_manager import workspaces
        jobs, control = self.stores(incarnation)
        operations = type(self).operations(self, jobs, control, self.engine)

        def close():
            operations.close()
            workspaces.held_manager_instance(self.storage).release()
            jobs.close()
            control.close()
        return jobs, control, operations, close

    def test_a_removal_retains_the_fault_and_the_settled_episode_never_dispatches_again(self):
        from baton_v12.job_manager import status, sweep
        from baton_v12.worker_manager import intake
        from tools import job_observation
        self.assertEqual(self.argv('settle-stopped', self.preview()['request'])['state'], 'settled')
        self.runner.stop()
        self.addCleanup(self.runner.start)
        self.engine = self.removing_engine()
        with mock.patch.object(single_worker, 'effective_engine_run', return_value=self.engine):
            jobs, control, operations, close = self.composed('w386766-quiesce')
            self.assertEqual(operations.refresh_runtime(self.stage)['execution_runtime'], 'quiescent')
            close()
            remove = lambda: command.remove(self.places['instance'], job_id='job-a', stage_id=self.stage['stage_id'],
                                            episode=1, reason='settlement: M386700 shape', clock=lambda: fixtures.NOW,
                                            compose=lambda configuration, j, c: type(self).operations(self, j, c, self.engine))
            # Review 2026-11-28T06-17-31Z R2: THE DECLARATION COMMITS BEFORE THE FENCE AND DESTROY. Cut there, the
            # removal is declared and NOT done: status must show the recorded runtime and the live fault, never
            # "Runtime removed by settlement".
            real = ControlStore.transact

            def cut(store, operation, kind, signature, action):
                answered = real(store, operation, kind, signature, action)
                if kind == 'attempt.abandon':
                    raise RuntimeError('lost reply after the abandonment declaration')
                return answered
            with mock.patch.object(ControlStore, 'transact', cut):
                with self.assertRaises(RuntimeError):
                    remove()
            jobs, control, operations, close = self.composed('w386766-interrupted')
            try:
                document = status(jobs, operations, observed_at=fixtures.SOON)
            finally:
                close()
            job = next(one for one in document['jobs'] if one['job_id'] == 'job-a')
            stage = next(one for one in job['stages'] if one['stage_id'] == self.stage['stage_id'])
            self.assertIs(stage['removal']['removed'], False)
            self.assertEqual(stage['removal']['execution_runtime'], 'quiescent')
            view = job_observation.job_view(document, job)
            phase = next(one for one in view['phases'] if one['stage_id'] == self.stage['stage_id'])
            self.assertNotIn('Runtime removed by settlement', phase['reason'])
            self.assertIn('settlement removal declared, not confirmed: runtime quiescent', phase['reason'])
            self.assertIn('agent fault', phase['reason'])       # the exchange is still there, and so is its fault
            self.assertEqual(stage['state'], 'exceptional')
            self.assertNotEqual(phase['row_position'].split(';')[0], 'stopped')
            # The repeated removal replays the committed declaration and finishes it.
            removed = remove()
            self.assertTrue(removed['removed'])
            self.assertEqual(removed['after'], {'execution_runtime': 'destroyed', 'cleanup': 'retained'})
            retained = intake.removal_terminal_of(self.control, attempt_id=self.ATTEMPT)
            self.assertEqual((retained['ending'], retained['fault_code'], retained['answered'], retained['manifest_digest']),
                             ('faulted', 'agent', ['describe'], None))
            self.assertEqual(retained['sequence_id'], exchange.sequence_of(self.ATTEMPT))
            for incarnation in ('w386766-serving-1', 'w386766-serving-2'):     # a restart between the two
                jobs, control, operations, close = self.composed(incarnation)
                try:
                    with mock.patch.object(type(operations), 'dispatch', side_effect=AssertionError('redispatch')) as dispatch:
                        for _ in range(3):
                            sweep(jobs, operations, now=fixtures.SOON)
                    self.assertEqual(dispatch.call_count, 0)
                    document = status(jobs, operations, observed_at=fixtures.SOON)
                finally:
                    close()
                job = next(one for one in document['jobs'] if one['job_id'] == 'job-a')
                stage = next(one for one in job['stages'] if one['stage_id'] == self.stage['stage_id'])
                self.assertEqual(stage['state'], 'exceptional')
                self.assertEqual(stage['removal']['terminal'], retained)
                self.assertEqual(stage['removal']['reason'], 'settlement: M386700 shape')
                view = job_observation.job_view(document, job)
                phase = next(one for one in view['phases'] if one['stage_id'] == self.stage['stage_id'])
                self.assertEqual(view['headline'], 'FAILED')
                self.assertEqual(phase['row_position'].split(';')[0], 'stopped')
                self.assertEqual(phase['reason'], 'Stopped — agent fault after describe (no manifest). '
                                                  'Runtime removed by settlement: "settlement: M386700 shape".')
