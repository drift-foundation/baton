"""W325959: the NATIVE task-token lifetime, through the real composition.

THE RECORDED FAILURE THESE CASES CLOSE. The native pilot's implementation
attempt had its workspace token expire at 900 seconds with zero renewals while
its Job allowed a 3600-second provider turn
(`OWNER-FAILURE-EVIDENCE-20261019.md`). `PreparedGovernance.reserve` acquired
with neither `seconds` nor a permission, so `tokens.acquire` took its
`LIFETIME_SECONDS` default.

WHY A LIFETIME AND NOT AN ENVELOPE. The native stop owner is the serving
loop's reclaim pass: `tokens.Governance.overdue` answers only for an EXPIRED
token and `tools/job_manager._reclaiming` acts on what it answers. Nothing
native reads an envelope's `stop_at`, so an envelope would record an execution
deadline no native party enforces.

A DISCONNECTED FORWARDING PATH MUST FAIL THESE CASES, which is review
2026-10-22T19-32-18Z's requirement and the defect in my previous revision:
those cases built a governance and then called `tokens.acquire` directly, so
unwiring `factory`, the callback or `reserve` would not have been noticed.
Every case below goes through the REAL act -- `reserve` for the acquisition,
`stage_execution.operations_from` for the composition, and
`stage_execution.factory` for the entry point -- so each link is load-bearing.

THE POLICY INPUTS ARE SELECTED, NOT DERIVED FROM A UNIVERSAL CLAIM. The three
checkout steps, the 900-second per-step allowance and the 120-second cleanup
reserve are NATIVE POLICY INPUTS chosen from this build's own constants and
the pilot's own `policy.json`. They are NOT a proof about every possible
elapsed runtime, and nothing here asserts one.

DETERMINISTIC: a real `ControlStore` on a controlled clock, a fake engine and
adapter. No provider, no container and no process is created or signalled.

FIXTURE REQUIREMENT, stated because an independent reviewer met it the hard
way at claim354590: the real-composition cases below inherit
`SingleWorkerCase`/`ServingCase`, which take a DISK-BACKED root through
`tests.manager.disk_roots`. On a host whose `/tmp` is a tmpfs that helper
REFUSES BY NAME rather than falling back, and the fix is its own variable --
`BATON_V12_DISK_ROOT=<a real-storage directory>`. That refusal is the helper
working as designed (a workspace on scratch is what `source_boundary` exists
to reject), so nothing here changes it; it is recorded so the next runner
reads the refusal as an environment operand rather than as a failure of this
subject.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import (ControlStore, activate_assignment,
                                      pin_boundary_identity,
                                      reconcile_runtime)
from baton_v12.worker_manager import attempts, tokens, workspaces
from tools import single_worker, stage_execution
from tests.manager.test_attempts import AttemptCase, Adapter, ATTEMPT
from tests.manager.test_authoring_enforcement import Clock, Engine


def native_limits(provider=3600, verification=900):
    return execution_limits.resolved(
        {'provider_turn_seconds': provider,
         'verification_command_seconds': verification})


class NativeAcquisition(AttemptCase):
    """The REAL prepared acquisition, through `reserve`, on a fake clock."""

    def setUp(self):
        super().setUp()
        self.clock = Clock()
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation='native-case',
                                       clock=self.clock.utc)
        self.addCleanup(self.store.close)
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        home = Path(self.storage) / ATTEMPT
        home.mkdir()
        roots = {name: str(home / name) for name in ('workspace', 'inputs')}
        for name in roots.values():
            Path(name).mkdir()
        found = Path(roots['workspace']).stat()
        pin_boundary_identity(self.store, attempt_id=ATTEMPT, source=(11, 111),
                              workspace=(found.st_dev, found.st_ino))
        workspaces.record_preparation(self.store, ATTEMPT, roots, [])
        self.adapter = Adapter('runtime-1')
        self.adapter.listing = [{'runtime_id': 'runtime-1',
                                 'labels': attempts._runtime_labels(self.row())}]
        reconcile_runtime(self.store, self.adapter, attempt_id=ATTEMPT)
        self.engine = Engine(self.store)
        self.stage = {'job_id': 'job-one', 'attempt_id': ATTEMPT}
        self.context = {'job_id': 'job-one', 'attempt_id': ATTEMPT,
                        'execution_limits': native_limits()}

    def policy(self):
        """THE REAL native policy, from the module under test."""
        return stage_execution.native_lifetime_policy({})

    def acquire_through_reserve(self, seconds):
        """THE REAL ACT. `reserve` is what the pilot path actually calls."""
        governance = workspaces.prepared_workspace_governance(
            self.store, ATTEMPT, seconds=seconds)
        row = self.row()
        operation = attempts._start_operation_id(row)
        governance.reserve(self.store, row, operation=operation)
        domain = tokens.domain_of('workspace', governance.identity(row))
        generation = tokens.generation_of(self.store, domain,
                                          execution=ATTEMPT,
                                          operation=operation)
        return tokens.token_of(self.store, domain, generation), domain, generation

    def current(self, domain, generation):
        return tokens.token_of(self.store, domain, generation)

    # -- the connection itself ------------------------------------------------

    def test_the_REAL_policy_feeds_the_REAL_reserve_and_the_token_takes_it(self):
        """The whole chain: policy -> reserve -> acquire -> stored token."""
        seconds = self.policy()(self.store, self.stage, self.context)
        self.assertEqual(seconds,
                         execution_limits.task_token_seconds(native_limits()))
        token, domain, generation = self.acquire_through_reserve(seconds)
        # THE STORED TOKEN carries it -- not a value this case computed.
        self.assertEqual(token['seconds'], seconds)
        self.assertGreater(token['seconds'], tokens.LIFETIME_SECONDS)

    def test_WITHOUT_the_policy_the_REAL_reserve_still_takes_900(self):
        """The defect, reproduced through the same real act. A disconnected
        forwarding path lands here, which is why this case exists."""
        token, _domain, _generation = self.acquire_through_reserve(None)
        self.assertEqual(token['seconds'], tokens.LIFETIME_SECONDS)
        self.assertEqual(token['seconds'], 900)

    def test_the_acquired_token_SURVIVES_PAST_900_and_is_still_bounded(self):
        seconds = self.policy()(self.store, self.stage, self.context)
        _token, domain, generation = self.acquire_through_reserve(seconds)
        self.assertFalse(self.current(domain, generation)['expired'])
        self.clock.advance(901)
        held = self.current(domain, generation)
        self.assertFalse(held['expired'],
                         'a native token must outlive the old 900 default')
        self.clock.advance(seconds)
        held = self.current(domain, generation)
        self.assertTrue(held['expired'], 'the lifetime is still a bound')
        # EXPIRY IS NOT RELEASE.
        self.assertFalse(held['returned'])

    def test_expiry_makes_it_RECLAIMABLE_through_the_real_overdue_owner(self):
        """The native stop trigger, asked of the owner that enforces it."""
        seconds = self.policy()(self.store, self.stage, self.context)
        self.acquire_through_reserve(seconds)
        governance = tokens.workspace_governance()
        row = self.row()
        operation = attempts._start_operation_id(row)
        self.assertIsNone(governance.overdue(self.store, row,
                                             operation=operation),
                          'not overdue while the lifetime stands')
        self.clock.advance(seconds + 1)
        overdue = governance.overdue(self.store, row, operation=operation)
        self.assertIsNotNone(overdue, 'expiry is what _reclaiming acts on')
        self.assertFalse(overdue['returned'],
                         'the resource stays held: expiry is not release')

    def test_REPLAY_of_the_same_acquisition_does_not_extend_or_duplicate(self):
        """Durable original timing; a replayed start is not a new permission."""
        seconds = self.policy()(self.store, self.stage, self.context)
        first, domain, generation = self.acquire_through_reserve(seconds)
        self.clock.advance(500)
        again, domain_again, generation_again = self.acquire_through_reserve(
            seconds)
        self.assertEqual((domain_again, generation_again),
                         (domain, generation),
                         'a replay is the same generation, not a new one')
        self.assertEqual(again['expires_at'], first['expires_at'],
                         'the deadline is durable and is not reset')

    def test_the_per_invocation_ceilings_are_UNCHANGED_by_the_lifetime(self):
        limits = native_limits()
        seconds = self.policy()(self.store, self.stage, self.context)
        self.assertGreater(seconds, 0)
        after = self.context['execution_limits']
        self.assertEqual(after, limits)
        self.assertEqual(after['boundaries']['provider_turn']['seconds'], 3600)
        self.assertEqual(
            after['boundaries']['ordinary_verification']['seconds'], 900)

    def test_a_lifetime_BESIDE_a_permission_is_refused_by_the_acquisition(self):
        envelope = {'started_at': self.clock.utc(),
                    'stop_at': '2099-01-01T00:00:00.000Z',
                    'expires_at': '2099-01-01T01:00:00.000Z',
                    'policy': {'run': 'r', 'job': 'job-one'}}
        governance = workspaces.prepared_workspace_governance(
            self.store, ATTEMPT, permission=envelope, seconds=7320)
        with self.assertRaises(ContractRefusal) as caught:
            governance.reserve(self.store, self.row(),
                               operation=attempts._start_operation_id(self.row()))
        self.assertIn('not both', str(caught.exception))

    def test_the_policy_REFUSES_a_resolution_its_owner_would_not_produce(self):
        tampered = dict(native_limits())
        tampered['boundaries'] = dict(tampered['boundaries'])
        tampered['boundaries']['provider_turn'] = dict(
            tampered['boundaries']['provider_turn'], seconds=7200)
        with self.assertRaises(ContractRefusal):
            self.policy()(self.store, self.stage,
                          dict(self.context, execution_limits=tampered))

    def test_the_policy_answers_NONE_when_there_is_nothing_to_resolve(self):
        """No Job context leaves the acquisition default exactly where it was."""
        select = self.policy()
        self.assertIsNone(select(self.store, self.stage,
                                 {'attempt_id': 'another'}))
        self.assertIsNone(select(self.store, self.stage,
                                 {'attempt_id': ATTEMPT}))


# -- THE MIDDLE FORWARDING, OBSERVED ON ACTUAL ACQUIRED TOKENS ---------------
#
# W325959 review 2026-10-22T19-38-15Z: my previous revision proved the middle
# with `inspect.signature`/`getsource` and mocked `operations_from` inside the
# factory case. Both are SURROGATES -- a source-text assertion passes while the
# value is dropped at runtime, and a mocked composer never composes. The review
# is right, and it asks for the only thing that actually settles it: OBSERVE THE
# ACQUIRED TOKEN after driving the real composition. A middle link that stops
# forwarding leaves the token at `LIFETIME_SECONDS`, which the assertions below
# catch.

from tests.tools.test_single_worker import SingleWorkerCase
from tests.tools.test_stage_execution import ServingCase
from tests.job_manager.test_serving_renewal import LaunchEngine


class NativeProductionLaunch(SingleWorkerCase):
    """The REAL composition, driven to a REAL acquisition, token observed."""

    def test_native_serving_reaches_the_acquisition_with_the_selected_lifetime(self):
        from baton_v12.job_manager import submit
        from tests.job_manager import fixtures

        job, control = self.stores('native-lifetime-launch')
        self.submission['schema'] = 'baton.v12.job-submission/2'
        selected = {'provider_turn_seconds': 3600,
                    'verification_command_seconds': 900}
        self.submission['jobs'][0]['execution_limits'] = selected
        submit(job, self.submission)
        engine = LaunchEngine()
        # THE REAL COMPOSER, NOT A MOCK, carrying the REAL native policy.
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW,
            lifetime_policy=stage_execution.native_lifetime_policy(self.config))
        self.addCleanup(operations.close)
        self.commanded(job, operations)
        self.assertEqual(len(engine.starts), 1)

        # THE ACQUIRED TOKEN, read out of the store the serving pass wrote.
        rows = list(control._connection.execute(
            'SELECT runtime_attempt_id, workspace_device, workspace_inode '
            'FROM attempts'))
        self.assertEqual(len(rows), 1)
        row = dict(rows[0])
        domain = tokens.domain_of('workspace', tokens.workspace_identity(row))
        token = tokens.token_of(control, domain, 1)

        expected = execution_limits.task_token_seconds(
            execution_limits.resolved(selected))
        # THIS IS THE WHOLE POINT: the value the policy composed reached the
        # acquisition through every intermediate link. Unwire any one of them
        # and this is LIFETIME_SECONDS instead.
        self.assertEqual(token['seconds'], expected)
        self.assertNotEqual(token['seconds'], tokens.LIFETIME_SECONDS)
        self.assertGreater(token['seconds'], 900)
        # AND IT IS A LIFETIME, NOT AN ENVELOPE -- nothing native enforces a
        # stop_at, so none is recorded.
        self.assertIsNone(token.get('permission'))
        self.assertEqual(token['container'], engine.runtime_id)

    def test_WITHOUT_the_policy_the_same_real_serving_acquires_900(self):
        """The disconnected composition, through the same real path."""
        from baton_v12.job_manager import submit
        from tests.job_manager import fixtures

        job, control = self.stores('native-lifetime-absent')
        self.submission['schema'] = 'baton.v12.job-submission/2'
        self.submission['jobs'][0]['execution_limits'] = {
            'provider_turn_seconds': 3600,
            'verification_command_seconds': 900}
        submit(job, self.submission)
        engine = LaunchEngine()
        operations = single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW)
        self.addCleanup(operations.close)
        self.commanded(job, operations)
        rows = list(control._connection.execute(
            'SELECT runtime_attempt_id, workspace_device, workspace_inode '
            'FROM attempts'))
        row = dict(rows[0])
        domain = tokens.domain_of('workspace', tokens.workspace_identity(row))
        token = tokens.token_of(control, domain, 1)
        self.assertEqual(token['seconds'], tokens.LIFETIME_SECONDS)
        self.assertEqual(token['seconds'], 900)


class NativeStageComposition(ServingCase):
    """BOTH real stage workers must carry the policy -- object, not source."""

    def test_the_native_factory_delivers_the_policy_to_both_stage_workers(self):
        import json

        job, control = self.stores('native-stage-composition')
        document = self.composed_document()
        config = Path(self.root) / 'native-config.json'
        config.write_text(json.dumps(document))
        actual = stage_execution.operations_from

        def compose(configuration, job_store, control_store, **named):
            # External provider/engine injection only. The lifetime policy must
            # arrive from `factory` itself, which is what this proves.
            named['engine_run'] = LaunchEngine()
            return actual(configuration, job_store, control_store,
                          credential_provider=lambda provider, reference:
                          self.secret, **named)

        with patch.object(stage_execution, '_configuration',
                          return_value=document), \
                patch.object(stage_execution, 'operations_from',
                             side_effect=compose):
            composed = stage_execution.factory(job, control)
        self.addCleanup(composed.close)
        workers = [one['operations']._worker for one in composed.workers
                   if one['role'] in ('implementation', 'review')]
        self.assertEqual(len(workers), 2,
                         'the native pilot has an implementation and a review')
        self.assertTrue(all(callable(worker.lifetime_policy)
                            for worker in workers),
                        'both stage workers must carry the lifetime policy')
        self.assertIs(workers[0].lifetime_policy, workers[1].lifetime_policy,
                      'one policy, delivered to both stages')
