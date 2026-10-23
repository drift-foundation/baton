"""W333485: prospective fixed-envelope permission, fake engine/controlled time."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import copy

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import ControlStore, activate_assignment, pin_boundary_identity, reconcile_runtime, request_cancellation
from baton_v12.worker_manager import attempts, tokens, workspaces
from tools import authoring_enforcement as enforcement, stage_execution
from tests.manager.test_attempts import AttemptCase, Adapter, Agent, ATTEMPT
from tests.manager.test_authoring_enforcement import Clock, Engine, packet


class ServingPermission(AttemptCase):
    def setUp(self):
        super().setUp()
        self.clock = Clock()
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation='permission-case', clock=self.clock.utc)
        self.addCleanup(self.store.close)
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT, expect=self.expect())
        home = Path(self.storage) / ATTEMPT
        home.mkdir()
        roots = {name: str(home / name) for name in ('workspace', 'inputs')}
        for name in roots.values():
            Path(name).mkdir()
        found = Path(roots["workspace"]).stat()
        pin_boundary_identity(self.store, attempt_id=ATTEMPT, source=(11, 111), workspace=(found.st_dev, found.st_ino))
        workspaces.record_preparation(self.store, ATTEMPT, roots, [])
        self.value = packet()
        self.value['bounds']['total_seconds'] = 4800
        self.context = {'job_id': 'job-one', 'attempt_id': ATTEMPT, 'execution_limits': execution_limits.resolved({'provider_turn_seconds': 3600, 'verification_command_seconds': 30})}
        self.stage = {'job_id': 'job-one', 'attempt_id': ATTEMPT}
        self.adapter = Adapter('runtime-1')
        self.adapter.listing = [{'runtime_id': 'runtime-1', 'labels': attempts._runtime_labels(self.row())}]
        reconcile_runtime(self.store, self.adapter, attempt_id=ATTEMPT)
        self.engine = Engine(self.store)
        native_stop = self.adapter.stop
        def stop(command):
            native_stop(command)
            self.engine(['docker', 'stop', command['runtime_id']], seconds=2)
            return {'stopped': True}
        self.adapter.stop = stop
        self.adapter.observe = lambda runtime: {'state': self.engine.state, 'why': 'controlled external engine', 'mounts': None}
        self.cancelled = []
        def cancel(**kwargs):
            self.cancelled.append(kwargs)
            return request_cancellation(self.store, self.port, Agent(), self.adapter, **kwargs)
        self.operations = SimpleNamespace(configuration={'workers': [{'deployment': {'engine': 'docker'}}]}, cancel_attempt=cancel)
        selected = patch.object(enforcement, 'selected_attempts', return_value=[ATTEMPT])
        selected.start()
        self.addCleanup(selected.stop)
        self.lane = enforcement.Lane(self.store, object(), self.operations, self.value, engine_run=self.engine, clock=self.clock.utc, monotonic=self.clock.monotonic)

    def selection(self):
        return enforcement.permission_policy(self.value)(self.store, self.stage, self.context)

    def acquire(self):
        permission, eligible = self.selection()
        governance = workspaces.prepared_workspace_governance(self.store, ATTEMPT, permission=permission, permission_eligible=eligible)
        row = self.row()
        operation = attempts._start_operation_id(row)
        governance.reserve(self.store, row, operation=operation)
        domain = tokens.domain_of('workspace', governance.identity(row))
        token = tokens.token_of(self.store, domain, tokens.generation_of(self.store, domain, execution=ATTEMPT, operation=operation))
        tokens.bind_container(self.store, token, 'runtime-1', launch=operation)
        return token

    def current(self, token):
        return tokens.token_of(self.store, token['domain'], token['generation'])

    def test_real_acquisition_and_enforcement_support_3600_then_cleanup(self):
        before = copy.deepcopy(self.context)
        self.clock.advance(120)  # preparation/startup is charged to the original envelope
        token = self.acquire()
        self.assertEqual(token['permission']['policy']['cleanup_seconds'], 60)
        self.assertEqual(token['expires_at'], token['permission']['expires_at'])
        self.assertEqual((enforcement.instant(token['expires_at']) - enforcement.instant(token['acquired_at'])).total_seconds(), 4680)
        for seconds in (901, 1800, 3600, 3720):
            self.clock.seconds = seconds
            report = self.lane.tick()
            self.assertFalse(self.lane.stopping.is_set(), report)
            self.assertFalse(self.current(token)['expired'])
            self.assertEqual(self.engine.state, 'running')
        self.clock.seconds = 4740
        report = self.lane.tick()
        self.assertTrue(self.lane.stopping.is_set())
        self.assertEqual(self.engine.state, 'quiescent', report)
        self.assertFalse(self.current(token)['returned'])
        self.clock.seconds = 4800
        report = self.lane.tick()
        self.assertEqual(self.engine.state, 'absent', report)
        self.assertTrue(self.current(token)['returned'])
        self.assertEqual(self.context, before)
        self.assertEqual(self.current(token)['permission'], token['permission'])

    def test_replay_and_restart_never_reset_the_deadline(self):
        token = self.acquire()
        self.clock.advance(1000)
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation='restarted', clock=self.clock.utc)
        self.addCleanup(self.store.close)
        replay = self.acquire()
        self.assertEqual(replay['acquired_at'], token['acquired_at'])
        self.assertEqual(replay['expires_at'], token['expires_at'])
        self.assertEqual(replay['owner'], token['owner'])
        self.assertEqual(replay['generation'], token['generation'])
        recovered = enforcement.Lane(self.store, object(), self.operations, self.value, engine_run=self.engine, clock=self.clock.utc, monotonic=self.clock.monotonic)
        self.assertTrue(recovered.recovery)
        self.assertTrue(recovered.stopping.is_set())

    def test_malformed_permission_reaches_its_token_validator_without_acquiring(self):
        permission, eligible = self.selection()
        for changed in ({'expires_at': 'tomorrow'}, {'stop_at': permission['started_at']}, {'extra': True}):
            with self.subTest(changed=changed):
                governance = workspaces.prepared_workspace_governance(self.store, ATTEMPT, permission=dict(permission, **changed), permission_eligible=eligible)
                with self.assertRaises(ContractRefusal):
                    governance.reserve(self.store, self.row(), operation='invalid')
                self.assertEqual(tokens.outstanding(self.store, tokens.domain_of('workspace', governance.identity(self.row()))), [])
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, 'workspace:legacy', operation='invalid-duration', execution=ATTEMPT, seconds=None)

    def test_cancellation_before_acquisition_refuses_new_permission(self):
        request_cancellation(self.store, self.port, Agent(), self.adapter, attempt_id=ATTEMPT, reason='test-cancel')
        with self.assertRaisesRegex(ContractRefusal, 'ending or cancelled'):
            self.acquire()

    def test_foreign_prepared_assignment_cannot_use_the_policy(self):
        permission, eligible = self.selection()
        governance = workspaces.prepared_workspace_governance(self.store, ATTEMPT, permission=permission, permission_eligible=eligible)
        with self.assertRaisesRegex(ContractRefusal, 'another prepared assignment'):
            governance.reserve(self.store, dict(self.row(), runtime_attempt_id='foreign'), operation='foreign')

    def test_closed_admission_competes_inside_acquisition(self):
        permission, eligible = self.selection()
        enforcement.halt(self.store, self.value['run_id'])
        govern = workspaces.prepared_workspace_governance(self.store, ATTEMPT, permission=permission, permission_eligible=eligible)
        with self.assertRaisesRegex(ContractRefusal, 'admission is closed'):
            govern.reserve(self.store, self.row(), operation='new-start')
        self.assertEqual(tokens.outstanding(self.store, tokens.domain_of('workspace', govern.identity(self.row()))), [])

    def test_exhausted_or_regressed_clock_cannot_acquire(self):
        for instant in (-1, 4740, 4800):
            with self.subTest(instant=instant):
                self.clock.seconds = instant
                with self.assertRaisesRegex(ContractRefusal, 'exhausted or its clock is ambiguous'):
                    self.acquire()

    def test_expiry_is_not_revival_or_reuse_and_unknown_cessation_holds(self):
        token = self.acquire()
        self.engine.unavailable = True
        self.clock.seconds = 4800
        report = self.lane.tick()
        self.assertTrue(self.lane.stopping.is_set())
        self.assertFalse(self.current(token)['returned'], report)
        replay = self.acquire()
        self.assertEqual(replay['expires_at'], token['expires_at'])
        self.assertTrue(self.current(token)['expired'])
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, token['domain'], operation='competitor', execution='other')
        self.clock.seconds = 100
        with self.assertRaises(ContractRefusal):
            tokens.renew(self.store, token, execution=ATTEMPT, operation=token['operation'], expected_revision=0)
        self.assertFalse(self.current(token)['returned'])

    def test_startup_cannot_consume_the_required_invocation_and_cleanup_reserve(self):
        self.clock.seconds = 1111  # 4740 - 3630 is the latest full invocation start.
        with self.assertRaisesRegex(ContractRefusal, 'remaining execution envelope'):
            self.acquire()

    def test_fixed_envelope_cannot_be_renewed_or_rebound(self):
        token = self.acquire()
        with self.assertRaisesRegex(ContractRefusal, 'fixed terminal deadline'):
            tokens.renew(self.store, token, execution=ATTEMPT, operation=token['operation'], expected_revision=0)
        changed = copy.deepcopy(token['permission'])
        changed['policy']['cleanup_seconds'] = 61
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, token['domain'], operation=token['operation'], execution=ATTEMPT, attempt=ATTEMPT, permission=changed)
        self.assertEqual(self.current(token)['permission'], token['permission'])

    def test_missing_invalid_foreign_and_oversized_limits_refuse(self):
        original = copy.deepcopy(self.context)
        for limits in (None, {}, dict(original['execution_limits'], scope='unlimited'), execution_limits.resolved({'provider_turn_seconds': 4800})):
            with self.subTest(limits=limits):
                self.context['execution_limits'] = limits
                with self.assertRaises(ContractRefusal):
                    self.selection()
        self.context = original
        self.stage['job_id'] = 'unrelated'
        with self.assertRaises(ContractRefusal):
            self.selection()

    def test_shorter_populated_limits_and_envelope_are_not_a_new_constant(self):
        self.value['run_id'] = 'shorter'
        self.value['bounds'] = dict(self.value['bounds'], total_seconds=600, cleanup_seconds=40)
        enforcement.envelope(self.store, self.value)
        self.context['execution_limits'] = execution_limits.resolved({'provider_turn_seconds': 400, 'verification_command_seconds': 20})
        permission, _ = self.selection()
        self.assertEqual((enforcement.instant(permission['expires_at']) - enforcement.instant(permission['started_at'])).total_seconds(), 600)
        self.assertEqual((enforcement.instant(permission['expires_at']) - enforcement.instant(permission['stop_at'])).total_seconds(), 40)


from tests.tools.test_single_worker import SingleWorkerCase, Engine as LaunchEngine


class ProductionLaunch(SingleWorkerCase):
    def test_job_serving_reaches_envelope_acquisition_and_dispatch(self):
        from baton_v12.job_manager import submit
        from tests.job_manager import fixtures
        from tools import single_worker
        job, control = self.stores('envelope-launch')
        self.submission['schema'] = 'baton.v12.job-submission/2'
        self.submission['jobs'][0]['execution_limits'] = {'provider_turn_seconds': 3600, 'verification_command_seconds': 30}
        submit(job, self.submission)
        value = packet()
        value['submission']['job_id'] = 'job-a'
        value['bounds']['total_seconds'] = 4800
        value['deployment']['authority_uuid'] = job.authority_uuid
        held, _ = enforcement.envelope(control, value)
        engine = LaunchEngine()
        operations = single_worker.operations_from(self.config, job, control, engine_run=engine,
            credential_provider=lambda provider, reference: self.secret, clock=lambda: fixtures.NOW,
            permission_policy=enforcement.permission_policy(value))
        self.addCleanup(operations.close)
        self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)
        self.assertTrue(engine.running)
        rows = list(control._connection.execute('SELECT runtime_attempt_id, workspace_device, workspace_inode FROM attempts'))
        self.assertEqual(len(rows), 1)
        row = dict(rows[0])
        domain = tokens.domain_of('workspace', tokens.workspace_identity(row))
        token = tokens.token_of(control, domain, 1)
        self.assertIsNotNone(token.get('permission'))
        self.assertEqual(token['container'], engine.runtime_id)
        self.assertEqual(token['permission']['started_at'], held['started_at'])
        self.assertEqual(token['permission']['policy']['execution_limits']['requested'], self.submission['jobs'][0]['execution_limits'])
        self.assertTrue(tokens.effects_permitted(control, token))
        clock = Clock()
        clock.origin = enforcement.instant(held['started_at'])
        control._clock = clock.utc
        for seconds in (901, 1800, 3600):
            clock.seconds = seconds
            self.assertTrue(tokens.effects_permitted(control, token))
            self.assertTrue(engine.running)
        self.assertEqual(tokens.token_of(control, domain, 1)['expires_at'], token['expires_at'])


from tests.tools.test_stage_execution import ServingCase


class AuthoringComposition(ServingCase):
    def test_child_composition_delivers_policy_to_real_stage_workers(self):
        import json
        job, control = self.stores('authoring-envelope-composition')
        document = self.composed_document()
        config = Path(self.root) / 'envelope-config.json'
        config.write_text(json.dumps(document))
        value = packet()
        value['code_boundary'] = self.checkout
        value['deployment']['config_path'] = str(config)
        actual = stage_execution.operations_from
        def compose(config, job, control, **named):
            # External provider/engine injection only; the actual stage factory
            # and its returned workers consume the policy from child_compose.
            named['engine_run'] = LaunchEngine()
            return actual(config, job, control, credential_provider=lambda provider, reference: self.secret, **named)
        with patch.object(stage_execution, 'operations_from', side_effect=compose):
            composed = enforcement.child_compose(value, job, control, None)
        self.addCleanup(composed.close)
        workers = [one['operations']._worker for one in composed.workers if one['role'] in ('implementation', 'review')]
        self.assertEqual(len(workers), 2)
        self.assertTrue(all(callable(worker.permission_policy) for worker in workers))
        self.assertIs(workers[0].permission_policy, workers[1].permission_policy)
