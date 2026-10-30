"""Focused fake-engine evidence; real owner journals, no Git or live provider."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, activate_assignment, pin_boundary_identity, reconcile_runtime, request_cancellation
from baton_v12.worker_manager import attempts, tokens
from tools import authoring_enforcement as enforcement
from .test_attempts import AttemptCase, Adapter, Agent, ATTEMPT
from .test_offers import NOW


class Clock:
    def __init__(self):
        self.seconds = 0
        self.origin = datetime.fromisoformat(NOW.replace('Z', '+00:00'))

    def utc(self):
        return (self.origin + timedelta(seconds=self.seconds)).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def monotonic(self):
        return self.seconds

    def advance(self, seconds):
        self.seconds += seconds


def packet():
    return {'run_id': 'enforcement-case', 'submission': {'job_id': 'job-one'},
            'deployment': {'authority_uuid': 'authority-one'},
            'bounds': {'total_seconds': 300, 'cleanup_seconds': 60, 'implementer_invocations': 1, 'retry': False}}


class Engine:
    def __init__(self, store):
        self.store = store
        self.state = 'running'
        self.calls = []
        self.stop_ack_only = False
        self.unavailable = False
        self.wrong_identity = False

    def __call__(self, argv, *, seconds):
        assert not self.store._connection.in_transaction, 'engine I/O inside transaction'
        self.calls.append((list(argv), seconds))
        if self.unavailable:
            raise TimeoutError('fake engine unavailable')
        if argv[1] == 'stop':
            if not self.stop_ack_only:
                self.state = 'quiescent'
            return {'status': 0, 'stdout': '', 'stderr': ''}
        if argv[1] == 'rm':
            if not self.stop_ack_only:
                self.state = 'absent'
            return {'status': 0, 'stdout': '', 'stderr': ''}
        if 'inspect' in argv:
            runtime = argv[-1]
            if self.state == 'absent':
                return {'status': 1, 'stdout': '', 'stderr': 'Error: No such container: ' + runtime}
            return {'status': 0, 'stdout': json.dumps([{'Id': 'wrong-runtime' if self.wrong_identity else runtime, 'State': {'Running': self.state == 'running'}}]), 'stderr': ''}
        raise AssertionError(argv)


class LaneFixture(AttemptCase):
    def setUp(self):
        super().setUp()
        self.clock = Clock()
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation='enforcement-case', clock=self.clock.utc)
        self.addCleanup(self.store.close)
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT, expect=self.expect())
        pin_boundary_identity(self.store, attempt_id=ATTEMPT, source=(11, 111), workspace=(22, 222))
        self.runtime_adapter = Adapter('runtime-1')
        self.runtime_adapter.listing = [{'runtime_id': 'runtime-1', 'labels': attempts._runtime_labels(self.row())}]
        if getattr(self, 'attach', True):
            reconcile_runtime(self.store, self.runtime_adapter, attempt_id=ATTEMPT)
        self.governance = tokens.workspace_governance()
        self.row_value = self.row()
        self.operation = attempts._start_operation_id(self.row_value)
        self.domain = tokens.domain_of('workspace', self.governance.identity(self.row_value))
        self.token = tokens.acquire(self.store, self.domain, operation=self.operation, execution=ATTEMPT, attempt=ATTEMPT)
        tokens.journal_launch(self.store, self.token, self.operation)
        if getattr(self, 'bind', True):
            tokens.bind_container(self.store, self.token, 'runtime-1', launch=self.operation)
        self.engine = Engine(self.store)
        self.cancellations = []
        def cancel(**kwargs):
            self.cancellations.append(kwargs)
            return request_cancellation(self.store, self.port, Agent(), self.runtime_adapter, **kwargs)
        self.operations = SimpleNamespace(configuration={'workers': [{'deployment': {'engine': 'docker'}}]}, cancel_attempt=cancel)
        selection = patch.object(enforcement, 'selected_attempts', return_value=[ATTEMPT])
        selection.start()
        self.addCleanup(selection.stop)

    def lane(self, value=None):
        return enforcement.Lane(self.store, object(), self.operations, value or packet(), engine_run=self.engine, clock=self.clock.utc, monotonic=self.clock.monotonic)

    def current(self):
        return tokens.token_of(self.store, self.domain, self.token['generation'])



class OwnerLane(LaneFixture):
    def test_settled_intake_skips_redundant_fence_only_with_positive_cessation(self):
        # Boundary-negative cases complement the real intake/cleanup joined test.
        runtime = dict(attempts.attempt_runtime_of(self.store, ATTEMPT), execution_runtime='destroyed', cleanup='retained')
        token = dict(self.current(), returned=True)
        cases = [('settled', {}, {}, 'absent', {'receipt': 'present'}, False),
                 ('missing-intake', {}, {}, 'absent', None, True),
                 ('pending-cleanup', {'cleanup': 'pending'}, {}, 'absent', {'receipt': 'present'}, True),
                 ('runtime-not-ended', {'execution_runtime': 'quiescent'}, {}, 'absent', {'receipt': 'present'}, True),
                 ('outstanding-token', {}, {'returned': False}, 'absent', {'receipt': 'present'}, True),
                 ('restartable-runtime', {}, {}, 'quiescent', {'receipt': 'present'}, True),
                 ('live-runtime', {}, {}, 'running', {'receipt': 'present'}, True)]
        lane = self.lane()
        lane.stopping.set()
        for name, changed_runtime, changed_token, engine_state, receipt, cancel in cases:
            with self.subTest(name=name):
                lane.cancelled.clear()
                self.engine.state = engine_state
                with patch.object(attempts, 'attempt_runtime_of', return_value=dict(runtime, **changed_runtime)), patch.object(tokens, 'token_of', return_value=dict(token, **changed_token)), patch.object(enforcement.intake, 'intake_receipt_of', return_value=receipt), patch.object(self.operations, 'cancel_attempt') as called:
                    result = lane.tick()['attempts'][ATTEMPT]
                    self.assertEqual(result['faults'], [])
                    self.assertEqual(called.call_count, int(cancel))

    def test_expiry_reclaims_exact_runtime_without_a_serving_tick(self):
        value = packet()
        value['bounds']['total_seconds'] = 4800
        lane = self.lane(value)
        self.clock.advance(900)
        report = lane.tick()
        self.assertTrue(lane.stopping.is_set())
        self.assertTrue(self.current()['revoked'])
        self.assertTrue(self.current()['returned'])
        self.assertEqual(report['attempts'][ATTEMPT]['observation']['state'], 'absent')
        self.assertEqual(report['attempts'][ATTEMPT]['settlement']['settled'], 'returned')
        self.assertTrue(all(call[0][-1] == 'runtime-1' for call in self.engine.calls))
        calls = len(self.engine.calls)
        lane.tick()
        self.assertEqual(sum(call[0][1] == 'stop' for call in self.engine.calls), 1)
        self.assertGreaterEqual(len(self.engine.calls), calls)

    def test_acknowledgement_without_cessation_keeps_token_held(self):
        lane = self.lane()
        self.engine.stop_ack_only = True
        self.clock.advance(900)
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertTrue(self.current()['revoked'])
        self.assertFalse(self.current()['returned'])
        self.assertEqual(report['observation']['state'], 'running')
        self.assertEqual(report['settlement']['settled'], 'held')

    def test_wrong_runtime_observation_cannot_release(self):
        lane = self.lane()
        self.engine.wrong_identity = True
        self.clock.advance(900)
        self.engine.stop_ack_only = True
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertEqual(report['observation']['state'], 'uncertain')
        self.assertFalse(self.current()['returned'])

    def test_slow_or_refused_engine_retains_exact_actionable_hold(self):
        lane = self.lane()
        self.engine.unavailable = True
        self.clock.advance(900)
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertFalse(self.current()['returned'])
        self.assertEqual(report['token']['container'], 'runtime-1')
        self.assertEqual(report['observation']['state'], 'uncertain')

    def test_early_deadline_uses_cancellation_not_token_renewal_or_early_revoke(self):
        lane = self.lane()
        self.clock.advance(240)
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertEqual(len(self.cancellations), 1)
        self.assertFalse(self.current()['revoked'])
        self.assertFalse(self.current()['returned'])
        self.assertEqual(report['observation']['state'], 'running')
        lane.tick()
        self.assertEqual(len(self.cancellations), 2)
        self.assertEqual(len(self.runtime_adapter.stopped), 2)
        self.assertEqual(len({call['operation_id'] for call in self.runtime_adapter.stopped}), 1)

    def test_restart_reuses_original_envelope_and_never_grants_more_time(self):
        first = self.lane()
        self.clock.advance(30)
        second = self.lane()
        self.assertEqual(first.held, second.held)
        self.assertTrue(second.recovery)
        self.assertTrue(second.stopping.is_set())
        changed = packet()
        changed['bounds']['total_seconds'] = 4800
        with self.assertRaises(ContractRefusal):
            self.lane(changed)

    def test_regressed_wall_clock_closes_admission(self):
        lane = self.lane()
        self.clock.advance(-1)
        lane.tick()
        self.assertTrue(lane.stopping.is_set())

    def test_halt_fences_all_three_dispatch_boundaries_but_preserves_reads(self):
        raw = Mock()
        operations = enforcement.Operations(raw, self.store, 'enforcement-case')
        operations.admit('stage', 'job')
        enforcement.halt(self.store, 'enforcement-case')
        for action in ('admit', 'claim', 'launch'):
            with self.assertRaises(ContractRefusal):
                getattr(operations, action)('stage', 'job')
        operations.observe('stage')
        self.assertEqual(raw.admit.call_count, 1)
        raw.observe.assert_called_once_with('stage')
        operations.cancel_attempt(attempt_id=ATTEMPT, reason='overall-bound-exceeded')
        raw.cancel_attempt.assert_called_once_with(attempt_id=ATTEMPT, reason='authoring-enforcement')

    def test_child_admission_is_consumed_once_even_before_submission(self):
        self.lane()
        enforcement.admit_child(self.store, packet(), 100, 101)
        with self.assertRaises(ContractRefusal):
            enforcement.admit_child(self.store, packet(), 200, 201)
        with self.assertRaises(ContractRefusal):
            enforcement.admit_child(self.store, packet(), 100, 101)

    def test_multiple_engine_names_refuse_instead_of_observing_the_wrong_engine(self):
        self.operations.configuration['workers'].append({'deployment': {'engine': 'other-engine'}})
        with self.assertRaises(RuntimeError):
            self.lane()
        self.assertEqual(self.engine.calls, [])

    def test_halt_refuses_first_child_admission(self):
        self.lane()
        enforcement.halt(self.store, packet()['run_id'])
        with self.assertRaises(ContractRefusal):
            enforcement.admit_child(self.store, packet(), 100, 101)


class Child:
    def __init__(self, clock, *, returns=None, resist=False):
        self.clock, self.returns, self.resist = clock, returns, resist
        self.events = []
        self.done = False

    def poll(self):
        return self.returns if self.done else None

    def terminate(self):
        self.events.append(('terminate', self.clock.seconds))

    def kill(self):
        self.events.append(('kill', self.clock.seconds))
        self.done = not self.resist

    def wait(self, timeout):
        if not self.done:
            self.clock.advance(timeout)
            raise TimeoutError('unobserved process cessation')
        return -9


class OuterDeadline(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.guard = SimpleNamespace(envelope={'stop_at': (self.clock.origin + timedelta(seconds=240)).isoformat()},
                                     clock=self.clock.utc, recovery=False, stopping=threading.Event(), finished=threading.Event(),
                                     report={'attempts': {}}, stop=lambda **kwargs: {'state': 'held', 'faults': ['unknown runtime'], 'attempts': {}})
        self.child = Child(self.clock)
        self.launches = 0

    def launch(self):
        self.launches += 1
        return self.child

    def run_outer(self, sleep=None):
        return enforcement.supervise_process(packet(), self.guard, self.launch, clock=self.clock.monotonic, sleep=sleep or self.clock.advance)

    def test_stalled_authoring_sweep_cannot_extend_committed_deadline(self):
        report = self.run_outer()
        self.assertEqual(self.child.events, [('terminate', 240.0), ('kill', 288.0)])
        self.assertTrue(report['child_exited'])
        self.assertEqual(report['state'], 'held')
        self.assertEqual(self.launches, 1)
        self.assertEqual(packet()['bounds']['implementer_invocations'], 1)
        self.assertFalse(packet()['bounds']['retry'])

    def test_expiry_stops_child_early_even_when_enforcement_engine_never_answers(self):
        def advance(seconds):
            self.clock.advance(seconds)
            if self.clock.seconds >= 20:
                self.guard.stopping.set()
        report = self.run_outer(advance)
        self.assertEqual(self.child.events, [('terminate', 20.0), ('kill', 68.0)])
        self.assertEqual(report['state'], 'held')

    def test_failed_enforcement_never_leaves_authoring_running(self):
        self.guard.finished.set()
        report = self.run_outer()
        self.assertEqual(self.child.events, [('terminate', 0), ('kill', 48.0)])
        self.assertEqual(report['state'], 'held')

    def test_restart_launches_nothing(self):
        self.guard.recovery = True
        report = self.run_outer()
        self.assertEqual(self.launches, 0)
        self.assertEqual(report['elapsed_seconds'], 48)
        self.assertEqual(report['state'], 'held')

    def test_unknown_child_cessation_is_not_reported_as_exit(self):
        self.child.resist = True
        report = self.run_outer()
        self.assertFalse(report['child_exited'])
        self.assertIn('cessation unknown', report['faults'][0])
        self.assertEqual(report['elapsed_seconds'], 290)

    def test_engine_subprocess_timeout_is_clamped(self):
        with patch.object(enforcement.single_worker, '_engine_run', return_value={}) as run:
            enforcement.bounded_engine(['fake', 'stop'], seconds=600)
            run.assert_called_once_with(['fake', 'stop'], seconds=2)


class LateLaunch(LaneFixture):
    attach = False

    # Only these cuts belong to this fixture; inherited attached-runtime cases
    # remain selected on OwnerLane, not duplicated with changed expectations.
    def test_token_bound_before_attempt_attachment_is_stopped_but_held(self):
        lane = self.lane()
        self.clock.advance(900)
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertEqual(report['reclaim']['state'], 'absent')
        self.assertEqual(report['observation']['state'], 'absent')
        self.assertFalse(self.current()['returned'])
        self.assertTrue(self.current()['revoked'])
        self.assertIsNone(attempts.attempt_runtime_of(self.store, ATTEMPT)['runtime_id'])

    def test_late_binding_after_expiry_is_refused_and_no_new_launch_is_granted(self):
        lane = self.lane()
        tokens.admit_activation(self.store, self.token, container='runtime-1')
        self.clock.advance(900)
        lane.tick()
        self.assertTrue(self.current()['activating'])
        self.assertFalse(self.current()['returned'])
        with self.assertRaises(ContractRefusal):
            tokens.bind_container(self.store, self.token, 'late-other', launch=self.operation)


class ProcessComposition(unittest.TestCase):
    def test_real_supervisor_blocked_sweep_is_terminated_and_partial_output_retained(self):
        import os
        import sys
        import time
        from .test_offers import UUID
        root_source = Path(__file__).resolve().parents[4]
        supervisor = root_source / 'work/records/2026/09/finding-v12-single-implementation-proof'
        with tempfile.TemporaryDirectory(prefix='authoring-composition-') as temporary:
            root = Path(temporary)
            script = root / 'blocked_author.py'
            partial = root / 'partial.txt'
            script.write_text('''
import sys, time, json
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
sys.path.insert(0, sys.argv[1])
import baseline
from baton_v12.job_manager import manager
import baton_v12.job_manager as api
from baton_v12.worker_manager import attempts
root = Path(sys.argv[2])
(root/'submission.json').write_text('{}')
packet = {'schema':baseline.FRESH_PACKET_SCHEMA,'run_id':'blocked-case','work':'case','claim':1,
          'bounds':{'total_seconds':300,'cleanup_seconds':60,'turn_seconds':180,'implementer_invocations':1,'retry':False},
          'submission':{'path':str(root/'submission.json'),'job_id':'case'},'outcome_path':str(root/'outcome.json')}
class Operations:
    def cancel_attempt(self, **kwargs): return {'requested':True}
def sweep(*args, **kwargs):
    (root/'partial.txt').write_text('retained before blocked serving sweep')
    time.sleep(60)
    return {}
limits={'boundaries':{'provider_turn':{'seconds':180,'origin':'job'}}}
with ExitStack() as stack:
    for owner, name, answer in [
        (api,'read_submission',lambda value:{}),(api,'submit',lambda *args:{'submission_id':'case'}),
        (api,'sweep',sweep),(manager,'sweep',sweep),(manager,'reconcile',lambda *args,**kwargs:{}),
        (baseline,'_attempts_of',lambda *args:({'attempt':'implementation'},{'implementation':'waiting'},limits)),
        (baseline,'_cleanups',lambda *args:{'cleanup':{},'outstanding':['attempt']}),
        (baseline,'_workload_evidence',lambda *args,**kwargs:{'shortfalls':['fake provider; partial only']}),
        (attempts,'attempt_runtime_of',lambda *args:{'runtime_id':'runtime','execution_runtime':'running'})]:
        stack.enter_context(patch.object(owner,name,answer))
    baseline.supervise(object(),object(),Operations(),packet,
        surveyed={'preexisting_jobs':[],'preexisting_stages':{},'accounting_scope':'fake scheduling and provider'})
''')
            value = packet()
            value['bounds'].update(total_seconds=2, cleanup_seconds=1)
            value['deployment'].update(control_store=str(root/'control.sqlite3'), job_store=str(root/'job.sqlite3'),
                                       authority_uuid=UUID, config_path=str(root/'config.json'))
            value['code_boundary'] = str(root_source)
            (root/'config.json').write_text(json.dumps({'workers':[{'deployment':{'engine':'docker'}}]}))
            created = []
            def factory(config, job, control, **kwargs):
                created.append((threading.get_ident(), kwargs))
                return SimpleNamespace(configuration=config, close=lambda:None, cancel_attempt=Mock())
            guard = enforcement.Guard(value, factory=factory).start()
            with open(root/'child.log','wb') as output, open(root/'lock','w') as lock:
                report = enforcement.supervise_process(value, guard, lambda: enforcement.Process(
                    [sys.executable, str(script), str(supervisor), str(root)], output=output, lock_fd=lock.fileno()))
            self.assertTrue(report['child_started'], report)
            self.assertTrue(report['child_exited'], report)
            self.assertEqual(report['state'], 'held')
            self.assertLess(report['elapsed_seconds'], 5, report)
            self.assertEqual(partial.read_text(), 'retained before blocked serving sweep', (root/'child.log').read_text())
            self.assertNotEqual(created[0][0], threading.get_ident())
            self.assertIs(created[0][1]['engine_run'], enforcement.bounded_engine)
            # Restart consumes the journalled envelope without another process.
            replay = enforcement.Guard(value, factory=factory).start()
            launch = Mock(side_effect=AssertionError('no second authoring invocation'))
            again = enforcement.supervise_process(value, replay, launch)
            launch.assert_not_called()
            self.assertFalse(again['child_started'])
            self.assertEqual(replay.envelope, guard.envelope)


class UnboundLaunch(LaneFixture):
    attach = False
    bind = False

    def test_expired_unbound_launch_stays_revoked_and_has_no_invented_stop_target(self):
        lane = self.lane()
        self.clock.advance(900)
        report = lane.tick()['attempts'][ATTEMPT]
        self.assertTrue(report['token']['revoked'])
        self.assertFalse(report['token']['returned'])
        self.assertIsNone(report['token']['container'])
        self.assertIsNotNone(report['token']['launch'])
        self.assertEqual(self.engine.calls, [])
        self.assertEqual(report['reclaim']['reclaimed'], 'held')
        self.assertEqual(report['settlement']['settled'], 'held')
        with self.assertRaises(ContractRefusal):
            tokens.bind_container(self.store, self.token, 'late-runtime', launch=self.operation)
        self.assertEqual(self.current()['renewals'], 0)


class SelectedJob(unittest.TestCase):
    def test_attempt_selection_uses_real_job_episodes_and_excludes_siblings(self):
        from baton_v12.job_manager import JobStore, submit
        from tests.job_manager.fixtures import UUID, submission
        with tempfile.TemporaryDirectory() as root:
            with JobStore.open(str(Path(root)/'jobs.sqlite3'), authority_uuid=UUID, incarnation='selection', clock=lambda:NOW) as job:
                submit(job, submission())
                selected = enforcement.selected_attempts(job, 'job-a')
                foreign = enforcement.selected_attempts(job, 'job-b')
                self.assertEqual(len(selected), 2)
                self.assertEqual(len(foreign), 1)
                self.assertFalse(set(selected) & set(foreign))
                self.assertEqual(enforcement.selected_attempts(job, 'missing-job'), [])


class ControllerInputs(unittest.TestCase):
    def test_unpinned_controller_refuses_before_execution(self):
        import hashlib
        source = Path(enforcement.__file__).resolve()
        value = {'manager_source': {'path': str(source.parent.parent), 'files': {}}}
        with self.assertRaises(RuntimeError):
            enforcement.verify_controller(value)
        value['manager_source']['files']['tools/authoring_enforcement.py'] = hashlib.sha256(source.read_bytes()).hexdigest()
        with self.assertRaises(RuntimeError):
            enforcement.verify_controller(value)
        value['manager_source']['files']['tools/authoring_shutdown.py'] = hashlib.sha256(source.with_name('authoring_shutdown.py').read_bytes()).hexdigest()
        enforcement.verify_controller(value)
        value['manager_source']['files']['tools/authoring_enforcement.py'] = '0'*64
        with self.assertRaises(RuntimeError):
            enforcement.verify_controller(value)

    def test_exhausted_engine_allowance_starts_no_process(self):
        with patch.object(enforcement.single_worker, '_engine_run') as run:
            with self.assertRaises(ContractRefusal):
                enforcement.bounded_engine(['docker','stop','exact'], seconds=0)
            run.assert_not_called()


class CancellationFixture(LaneFixture):
    attach = False

    def setUp(self):
        super().setUp()
        from tools import single_worker, stage_execution
        # Use the production pooled routing and worker cancellation composition.
        # The workspace and OCI adapter are the controlled external boundaries;
        # assignment, token, cancellation intent and AuthorityPort remain real.
        worker = single_worker._SingleWorker.__new__(single_worker._SingleWorker)
        worker.control, worker.port, worker.group = self.store, self.port, self.group
        worker.given = {'workspace_storage': self.storage, 'participant': self.port.participant}
        worker._adapter = lambda *args: self.runtime_adapter
        native_stop = self.runtime_adapter.stop
        def stop(command):
            self.assertFalse(self.store._connection.in_transaction)
            self.assertTrue([call for call in self.session.calls if call[0] == 'cancel'], 'stop preceded Authority fence')
            self.assertEqual(command['runtime_id'], 'runtime-1')
            native_stop(command)
            return self.engine(['docker', 'stop', command['runtime_id']], seconds=2)
        self.runtime_adapter.stop = stop
        self.operations = stage_execution.StageExecution(SimpleNamespace(store=object()), authority=None, integration=None,
            workers=[{'worker_id':'selected-owner','operations':worker}], given={'workers':[{'deployment':{'engine':'docker'}}]})
        for patcher in (patch.object(stage_execution, 'allocation_of', return_value={'worker_id':'selected-owner'}),
                        patch.object(single_worker.workspaces, 'assignment_workspace', return_value={'test':'external roots seam'})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def held_before_expiry(self, report):
        self.assertFalse(self.current()['revoked'])
        self.assertFalse(self.current()['returned'])
        self.assertEqual(self.current()['renewals'], 0)
        self.assertIsNone(attempts.attempt_runtime_of(self.store, ATTEMPT)['runtime_id'])
        self.assertEqual(report['observation']['state'], 'quiescent')
        self.assertEqual(self.runtime_adapter.started, [])
        self.assertEqual({command['runtime_id'] for command in self.runtime_adapter.stopped}, {'runtime-1'})


class BeforeAttachmentCancellation(CancellationFixture):
    def cancel_for(self, cause):
        lane = self.lane()
        if cause == 'deadline':
            self.clock.advance(240)
        elif cause == 'operator':
            lane.stopping.set()
        else:
            lane = self.lane()
        return lane, lane.tick()['attempts'][ATTEMPT]

    def test_deadline_stops_token_bound_writer_through_production_cancellation(self):
        lane, report = self.cancel_for('deadline')
        self.held_before_expiry(report)
        lane.tick()
        self.assertEqual(len(self.runtime_adapter.stopped), 1, 'positive cessation must not repeat stop')

    def test_operator_cancellation_stops_token_bound_writer(self):
        _, report = self.cancel_for('operator')
        self.held_before_expiry(report)

    def test_recovery_stops_token_bound_writer_without_renewed_time(self):
        lane, report = self.cancel_for('recovery')
        self.assertTrue(lane.recovery)
        self.held_before_expiry(report)

    def test_unknown_engine_stop_preserves_fence_and_hold_then_retries(self):
        self.engine.unavailable = True
        lane, report = self.cancel_for('deadline')
        self.assertTrue(report['faults'])
        self.assertFalse(self.current()['returned'])
        self.assertFalse(self.current()['revoked'])
        self.engine.unavailable = False
        self.held_before_expiry(lane.tick()['attempts'][ATTEMPT])
        self.assertEqual(len({command['operation_id'] for command in self.runtime_adapter.stopped}), 1)

    def test_refused_authority_fence_never_stops_a_runtime(self):
        self.session.fence_answer = ContractRefusal('refused', 'precondition', 'fake Authority refused exact fence')
        _, report = self.cancel_for('deadline')
        self.assertTrue(report['faults'])
        self.assertEqual(self.runtime_adapter.stopped, [])
        self.assertFalse(self.current()['returned'])

    def test_refused_runtime_stop_remains_held_after_authority_fence(self):
        self.runtime_adapter.stop_failure = ContractRefusal('runtime-observation', 'quiescence-unknown', 'fake engine refused stop')
        _, report = self.cancel_for('deadline')
        self.assertTrue(report['faults'])
        self.assertTrue([call for call in self.session.calls if call[0] == 'cancel'])
        self.assertFalse(self.current()['returned'])
        self.assertFalse(self.current()['revoked'])
        self.assertEqual(self.engine.state, 'running')

    def test_cancellation_owner_refuses_token_and_attachment_identity_disagreement(self):
        self.runtime_adapter.runtime_id = 'foreign-runtime'
        self.runtime_adapter.listing = [{'runtime_id': 'foreign-runtime', 'labels': attempts._runtime_labels(self.row())}]
        reconcile_runtime(self.store, self.runtime_adapter, attempt_id=ATTEMPT)
        with self.assertRaises(ContractRefusal) as refused:
            self.operations.cancel_attempt(attempt_id=ATTEMPT, reason='authoring-enforcement')
        self.assertEqual(refused.exception.code, 'identity-mismatch')
        self.assertEqual(self.runtime_adapter.stopped, [])
        self.assertFalse(self.current()['returned'])

    def test_acknowledged_stop_is_retried_if_writer_still_runs(self):
        self.engine.stop_ack_only = True
        lane, report = self.cancel_for('deadline')
        self.assertEqual(report['observation']['state'], 'running')
        self.engine.stop_ack_only = False
        self.held_before_expiry(lane.tick()['attempts'][ATTEMPT])
        self.assertEqual(len(self.runtime_adapter.stopped), 2)
        self.assertEqual(len({command['operation_id'] for command in self.runtime_adapter.stopped}), 1)


class LateBindingCancellation(CancellationFixture):
    bind = False

    def test_late_bind_and_later_activation_are_stopped_under_the_original_fence(self):
        lane = self.lane()
        self.clock.advance(240)
        lane.tick()
        self.assertEqual(self.runtime_adapter.stopped, [])
        self.assertTrue([call for call in self.session.calls if call[0]=='cancel'])
        tokens.bind_container(self.store, self.token, 'runtime-1', launch=self.operation)
        tokens.admit_activation(self.store, self.token, container='runtime-1')
        self.held_before_expiry(lane.tick()['attempts'][ATTEMPT])
        self.assertTrue(self.current()['activating'])
        # A start already admitted before cancellation may complete after the
        # first stop. Re-observation must trigger the same stop intent again.
        self.engine.state = 'running'
        self.held_before_expiry(lane.tick()['attempts'][ATTEMPT])
        self.assertEqual(len(self.runtime_adapter.stopped), 2)
        self.assertEqual(len({command['operation_id'] for command in self.runtime_adapter.stopped}), 1)
        self.assertEqual(len({call[1]['operation_id'] for call in self.session.calls if call[0]=='cancel'}), 1)
