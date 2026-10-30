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


class NativeComposition(AttemptCase):
    """`factory` and `operations_from` must DELIVER the policy, or fail here."""

    def test_factory_supplies_a_lifetime_policy_at_the_native_entry_point(self):
        """The caller that did not exist. Unwire it and this case fails."""
        seen = {}

        def record(configuration, job_store, control_store, **named):
            seen.update(named)
            return SimpleNamespace(configuration=configuration)

        with patch.object(stage_execution, 'operations_from', record), \
                patch.object(stage_execution, '_configuration',
                             return_value={'workers': []}):
            stage_execution.factory(object(), object())
        self.assertIn('lifetime_policy', seen)
        self.assertTrue(callable(seen['lifetime_policy']),
                        'factory must supply a callable native lifetime policy')

    def test_worker_operations_carries_it_to_the_real_composition(self):
        """The forwarding single_worker performs, asserted on the object."""
        import inspect

        # THE WORKER COMPOSITION ACCEPTS AND RETAINS IT. _SingleWorker is what
        # `worker_operations` builds and what reaches the acquisition.
        self.assertIn('lifetime_policy', inspect.signature(
            single_worker._SingleWorker.__init__).parameters)
        source = inspect.getsource(single_worker._SingleWorker.__init__)
        self.assertIn('self.lifetime_policy = lifetime_policy', source,
                      'the composition must retain the policy it was handed')
        # AND THE SIGNATURE ACCEPTS IT ALL THE WAY DOWN, so a rename breaks here
        # rather than silently dropping the policy.
        for owner in (single_worker.operations_from,
                      single_worker.worker_operations,
                      stage_execution.operations_from):
            with self.subTest(owner=owner.__name__):
                self.assertIn('lifetime_policy',
                              inspect.signature(owner).parameters)
        self.assertIn('seconds', inspect.signature(
            workspaces.prepared_workspace_governance).parameters)
