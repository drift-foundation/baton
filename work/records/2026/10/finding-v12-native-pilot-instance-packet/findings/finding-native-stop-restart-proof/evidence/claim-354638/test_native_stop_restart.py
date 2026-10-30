"""Native lifetime cessation/recovery: real owner stores, deterministic engine only."""
from pathlib import Path

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import (ControlStore, activate_assignment,
    pin_boundary_identity, reconcile_runtime, request_cancellation,
    request_runtime_start)
from baton_v12.worker_manager import attempts, tokens, workspaces
from tools import job_manager, stage_execution
from tests.manager.test_attempts import AttemptCase, Adapter, Agent, ATTEMPT
from tests.manager.test_authoring_enforcement import Clock, Engine


class NativeStopRestart(AttemptCase):
    def setUp(self):
        super().setUp()
        self.clock = Clock()
        self.store._clock = self.clock.utc
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT, expect=self.expect())
        roots = workspaces.assignment_workspace(self.group, self.storage, ATTEMPT)
        found = Path(roots['workspace']).stat()
        pin_boundary_identity(self.store, attempt_id=ATTEMPT, source=(11, 111), workspace=(found.st_dev, found.st_ino))
        workspaces.record_preparation(self.store, ATTEMPT, roots, [])
        self.adapter = Adapter('runtime-1')
        self.adapter.listing = [{'runtime_id': 'runtime-1', 'labels': attempts._runtime_labels(self.row())}]
        reconcile_runtime(self.store, self.adapter, attempt_id=ATTEMPT)
        self.engine = Engine(self.store)
        self.stage = {'job_id': 'job-one', 'attempt_id': ATTEMPT}
        self.context = dict(self.stage, execution_limits=execution_limits.resolved({'provider_turn_seconds': 3600, 'verification_command_seconds': 900}))
        self.seconds = stage_execution.native_lifetime_policy({})(self.store, self.stage, self.context)
        self.govern = workspaces.prepared_workspace_governance(self.store, ATTEMPT, seconds=self.seconds)
        self.operation = attempts._start_operation_id(self.row())
        reservation = self.govern.reserve(self.store, self.row(), operation=self.operation)
        reservation.bind('runtime-1')()
        reservation.settle('runtime-1')
        self.domain = tokens.domain_of('workspace', self.govern.identity(self.row()))
        self.token = tokens.token_of(self.store, self.domain, 1)

    def current(self):
        return tokens.token_of(self.store, self.domain, self.token['generation'])

    def sweep(self):
        return job_manager._reclaiming(self.store, 'docker', self.engine)(now=self.clock.utc())

    def reopen(self):
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation='native-restarted', clock=self.clock.utc)
        self.addCleanup(self.store.close)
        self.engine.store = self.store
        self.govern = workspaces.prepared_workspace_governance(self.store, ATTEMPT, seconds=self.seconds)

    def assert_held(self):
        self.assertFalse(self.current()['returned'])
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, self.domain, operation='competitor', execution='other')

    def assert_no_new_start(self):
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, govern=self.govern)
        self.assertEqual(self.adapter.started, [])
        self.assertFalse(any(call[0][1] in ('run', 'start', 'exec') for call in self.engine.calls))

    def test_native_deadline_drives_exact_runtime_stop_and_cleanup(self):
        self.assertEqual(self.seconds, 7320)
        self.clock.advance(901)
        self.assertEqual(self.sweep()['reclaimed'], [])
        self.assertTrue(tokens.effects_permitted(self.store, self.token))
        self.assertEqual(self.engine.calls, [])
        self.clock.seconds = self.seconds
        result = self.sweep()
        self.assertEqual(result['refused'], [])
        self.assertEqual(result['reclaimed'][0]['ending']['settled'], 'returned')
        self.assertEqual([call[0][1] for call in self.engine.calls], ['stop', 'rm', 'inspect', 'inspect'])
        self.assertTrue(all(call[0][-1] == 'runtime-1' for call in self.engine.calls))
        self.assertEqual(self.engine.state, 'absent')
        self.assertTrue(self.current()['returned'])
        self.assertTrue(self.current()['revoked'])
        self.assertFalse(tokens.effects_permitted(self.store, self.token))
        self.assertEqual(result['reclaimed'][0]['ending']['state'], 'absent')
        self.assertTrue((Path(self.storage) / ATTEMPT / 'workspace').is_dir())
        calls = list(self.engine.calls)
        self.reopen()
        self.assertEqual(self.sweep()['reclaimed'], [])
        self.assertEqual(self.engine.calls, calls)
        self.assertEqual(self.current()['expires_at'], self.token['expires_at'])
        self.assert_no_new_start()

    def test_stop_acknowledgement_without_cessation_holds_until_confirmed(self):
        self.engine.stop_ack_only = True
        self.clock.seconds = self.seconds
        self.sweep()
        self.assertEqual(self.engine.state, 'running')
        self.assertTrue(self.current()['revoked'])
        self.assert_held()
        self.reopen()
        self.assert_held()
        self.engine.stop_ack_only = False
        self.sweep()
        self.assertEqual(self.engine.state, 'absent')
        self.assertTrue(self.current()['returned'])

    def test_unavailable_engine_holds_across_restart_then_retries_exact_runtime(self):
        self.engine.unavailable = True
        self.clock.seconds = self.seconds
        self.sweep()
        self.assert_held()
        self.assertFalse(tokens.effects_permitted(self.store, self.token))
        self.reopen()
        self.assert_held()
        self.engine.unavailable = False
        self.sweep()
        self.assertTrue(self.current()['returned'])
        self.assertTrue(all(call[0][-1] == 'runtime-1' for call in self.engine.calls))
        self.assert_no_new_start()

    def test_wrong_runtime_observation_never_releases(self):
        self.engine.wrong_identity = True
        self.engine.stop_ack_only = True
        self.clock.seconds = self.seconds
        self.sweep()
        self.assert_held()
        self.assert_no_new_start()

    def test_reopened_store_preserves_deadline_and_generation_without_revival(self):
        self.clock.advance(1000)
        self.reopen()
        self.govern.reserve(self.store, self.row(), operation=self.operation)
        for field in ('acquired_at', 'expires_at', 'generation', 'owner', 'container'):
            self.assertEqual(self.current()[field], self.token[field])
        self.assertTrue(tokens.effects_permitted(self.store, self.token))
        self.assert_no_new_start()
        self.clock.seconds = self.seconds
        self.engine.unavailable = True
        self.sweep()
        self.reopen()
        self.govern.reserve(self.store, self.row(), operation=self.operation)
        self.assertEqual(self.current()['expires_at'], self.token['expires_at'])
        self.assertEqual(self.current()['generation'], self.token['generation'])
        self.assertFalse(tokens.effects_permitted(self.store, self.token))
        self.assertTrue(self.current()['revoked'])
        self.clock.seconds = 100
        with self.assertRaises(ContractRefusal):
            tokens.renew(self.store, self.token, execution=ATTEMPT, operation=self.operation, expected_revision=0)
        self.assertFalse(tokens.effects_permitted(self.store, self.token), self.current())
        self.assert_held()
        self.assert_no_new_start()

    def test_cancellation_stops_exact_runtime_before_expiry_without_releasing_hold(self):
        native_stop = self.adapter.stop
        def stop(command):
            native_stop(command)
            return self.engine(['docker', 'stop', command['runtime_id']], seconds=2)
        self.adapter.stop = stop
        request_cancellation(self.store, self.port, Agent(), self.adapter, attempt_id=ATTEMPT, reason='native-test-cancel')
        self.assertEqual(self.engine.state, 'quiescent')
        self.assertEqual(self.adapter.stopped[0]['runtime_id'], 'runtime-1')
        self.assertFalse(self.current()['expired'])
        self.assert_held()
        self.reopen()
        self.assert_held()
        self.assert_no_new_start()
        self.clock.seconds = self.seconds
        self.sweep()
        self.assertEqual(self.engine.state, 'absent')
        self.assertTrue(self.current()['returned'])
