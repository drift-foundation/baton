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


def ordinary_identity(row):
    """The workspace resource identity the ordinary governance uses."""
    return tokens.workspace_identity(row)
from tests.manager.test_authoring_enforcement import Clock, Engine


def native_limits(provider=3600, verification=900):
    return execution_limits.resolved(
        {'provider_turn_seconds': provider,
         'verification_command_seconds': verification})


class NativeAcquisitionCase(AttemptCase):
    """The REAL prepared acquisition fixture, through `reserve`, on a fake clock.

    Separated from the cases below so a second subject can reuse the fixture
    WITHOUT re-running this one's cases under its own class name -- a duplicate
    that reports a failure against a subject it is not about.
    """

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


class NativeAcquisition(NativeAcquisitionCase):
    """The native lifetime reaching a real acquired token, and staying bounded."""

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


class ARevokedGenerationPermitsNoEffects(NativeAcquisitionCase):
    """W354630 review354690: the omission, and why revocation is not expiry.

    `effects_permitted` asked four questions -- current, unreturned, unexpired,
    container bound -- and NOT revocation. So a REVOKED generation whose expiry
    judgement no longer reads true answered True and would have been handed the
    governed resource again. The reviewer reproduced it after a failed expiry
    cleanup, a restart and a clock rollback; this is that sequence at the
    acquisition boundary, through the real owner APIs.

    REVOCATION IS THE DURABLE FACT AND EXPIRY IS A CLOCK READING, which is the
    whole point: a rollback can un-expire a token but cannot un-revoke it.
    """

    def revoked_generation(self):
        """Acquire, bind, expire, revoke -- all through the real owner."""
        seconds = self.policy()(self.store, self.stage, self.context)
        _token, domain, generation = self.acquire_through_reserve(seconds)
        row = self.row()
        operation = attempts._start_operation_id(row)
        held = tokens.token_of(self.store, domain, generation)
        tokens.bind_container(self.store, held, 'runtime-1', launch=operation)
        # EXPIRY FIRST, because only an expired generation may be revoked.
        self.clock.advance(seconds + 1)
        tokens.revoke(self.store, ordinary_identity(row), 'workspace',
                      execution=row['runtime_attempt_id'], operation=operation)
        return domain, generation, seconds

    def test_a_bound_live_generation_DOES_permit_effects(self):
        """The control: without revocation the gate answers True."""
        seconds = self.policy()(self.store, self.stage, self.context)
        _token, domain, generation = self.acquire_through_reserve(seconds)
        row = self.row()
        operation = attempts._start_operation_id(row)
        held = tokens.token_of(self.store, domain, generation)
        tokens.bind_container(self.store, held, 'runtime-1', launch=operation)
        held = tokens.token_of(self.store, domain, generation)
        self.assertTrue(tokens.effects_permitted(self.store, held))

    def test_a_REVOKED_generation_permits_no_effects_even_when_expiry_reads_false(self):
        domain, generation, seconds = self.revoked_generation()
        held = tokens.token_of(self.store, domain, generation)
        self.assertTrue(held['revoked'])
        self.assertTrue(held['expired'])
        self.assertFalse(tokens.effects_permitted(self.store, held))
        # THE ROLLBACK. The clock goes backwards -- a restart against a store
        # whose host clock regressed -- so `expired` reads False again.
        self.clock.seconds = 0
        held = tokens.token_of(self.store, domain, generation)
        self.assertFalse(held['expired'],
                         'the rollback must really un-expire it, or this case '
                         'is not the one the reviewer reproduced')
        self.assertTrue(held['revoked'], 'revocation is durable')
        self.assertFalse(held['returned'], 'and it is not released')
        # THE DEFECT: this answered True before the correction.
        self.assertFalse(
            tokens.effects_permitted(self.store, held),
            'a revoked generation may not be handed the resource again')


from tests.tools.test_stage_execution import ComposedOneJobCase
from tools import job_manager as job_manager_tool


class NativeComposedCase(ComposedOneJobCase):
    """FIXTURE ONLY: the real composed deployment, carrying the native policy.

    Separated from the subjects below so each reuses this composition without
    re-running the others' cases under its own class name.

    THE LAST HALF OF THE TWO-STAGE PROOF, which these subjects are about. `NativeProductionLaunch` above proves
    the implementation stage reaches a real acquired token at the Job's composed
    lifetime; `NativeStageComposition` proves the factory hands one policy to
    both stage workers. Neither reaches the REVIEW stage's own acquisition, and
    the review stage is a second assignment of the SAME Work -- so a reviewer
    cannot claim until the implementation ending has moved that Work onto its
    configured review route.

    Two earlier shapes were refused by the product and are not retried here.
    `single_worker`'s deployment is implementation-only (`_held`: "this
    deployment launches implementation and this configuration names 'review'"),
    and submitting a bare review stage into a `ServingCase` store leaves the
    claim refused ("route 'baton.impl' does not resolve to 'baton.reviewer'").
    Both refusals are the authorization boundary working. THE ROUTE IS MOVED BY
    THE REAL `route_fenced` ENDING, which `ComposedOneJobCase` already drives,
    so this case weakens no check and moves no Work by hand.

    What it adds to that traversal is the one operand it does not carry: the
    REAL native lifetime policy, injected into the real composer rather than
    into the token, and then the two acquired tokens are read out of the store
    the serving pass wrote.
    """

    SELECTED = {'provider_turn_seconds': 3600,
                'verification_command_seconds': 900}

    def setUp(self):
        super().setUp()
        self.submission['schema'] = 'baton.v12.job-submission/2'
        self.submission['jobs'][0]['execution_limits'] = self.SELECTED

    def serving(self, **members):
        """The fixture's own composition, plus the native lifetime policy.

        Wrapping the composer rather than reimplementing `serving` keeps the
        whole real fixture -- engine, credentials, clock, checkout -- and adds
        exactly one operand, resolved from the configuration the deployment is
        actually composed with.
        """
        actual = stage_execution.operations_from

        def compose(configuration, job_store, control_store, **named):
            named['lifetime_policy'] = stage_execution.native_lifetime_policy(
                configuration)
            return actual(configuration, job_store, control_store, **named)

        with patch.object(stage_execution, 'operations_from',
                          side_effect=compose):
            return super().serving(**members)

    def token_of_attempt(self, control, attempt_id):
        """One attempt's own workspace token, through the real reader."""
        # THE WHOLE ROW, because the start operation identity is derived from
        # the attempt's own assignment and a narrowed SELECT hides that.
        [row] = [dict(one) for one in control._connection.execute(
            'SELECT * FROM attempts WHERE runtime_attempt_id = ?',
            (attempt_id,))]
        domain = tokens.domain_of('workspace', tokens.workspace_identity(row))
        generation = tokens.generation_of(
            control, domain, execution=attempt_id,
            operation=attempts._start_operation_id(row))
        return domain, generation, tokens.token_of(control, domain, generation)


class NativeTwoStageAcquisition(NativeComposedCase):
    """BOTH stages reaching their OWN acquired token, through the real ending."""

    def test_BOTH_stages_acquire_their_OWN_token_at_the_composed_lifetime(self):
        held = self.implemented()
        self.drive(held.job, held.composed, 'review', 'waiting')
        review_attempt = self.only_attempt(held.composed, 'review')
        self.assertNotEqual(review_attempt, held.attempt_id,
                            'the review stage is its own attempt')

        expected = execution_limits.task_token_seconds(
            execution_limits.resolved(self.SELECTED))
        seen = {}
        for role, attempt_id in (('implementation', held.attempt_id),
                                 ('review', review_attempt)):
            domain, generation, token = self.token_of_attempt(
                held.control, attempt_id)
            self.assertIsNotNone(token, f'the {role} stage acquired no token')
            seen[role] = (domain, generation, token)
            # THE WHOLE POINT: the value the policy composed reached THIS
            # stage's acquisition. Unwire any middle link and it is 900.
            self.assertEqual(token['seconds'], expected,
                             f'the {role} token must carry the composed '
                             f'lifetime')
            self.assertGreater(token['seconds'], 900,
                               f'the {role} token must outlive the per-'
                               f'invocation ceiling')
            self.assertNotEqual(token['seconds'], tokens.LIFETIME_SECONDS)
            # A LIFETIME, NOT AN ENVELOPE -- nothing native enforces a stop_at.
            self.assertIsNone(token.get('permission'))

        # ITS OWN GENERATION, NOT THE IMPLEMENTATION'S. Two stages of one Work
        # on one resource family would otherwise be one token read twice.
        self.assertNotEqual(seen['implementation'][0], seen['review'][0],
                            'each stage governs its own workspace resource')

    def test_the_review_stage_is_reached_because_the_ENDING_moved_the_route(self):
        """The precondition, asserted rather than assumed.

        If this ever regresses, the acquisition case above would fail for a
        reason that has nothing to do with the lifetime.
        """
        held = self.implemented()
        self.assertEqual(self.projected()['route'],
                         self.config['review_route'])
        del held

    def projected(self):
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config['authority_uuid'])
        try:
            return authority.project_work(self.work)
        finally:
            authority.dispose()


class TheDisconnectedTwoStageComposition(NativeComposedCase):
    """THE NEGATIVE ARM, so the case above cannot pass for the wrong reason.

    Same real fixture, same real ending, same two stages -- and NO lifetime
    policy. If both tokens still read the composed 7320 here, the assertion
    above would be measuring something other than the forwarding, because the
    value would be arriving from somewhere this deployment did not choose.
    """

    def serving(self, **members):
        # Deliberately NOT wrapping the composer: the grandparent's plain
        # composition, which supplies no lifetime policy at all.
        return ComposedOneJobCase.serving(self, **members)

    def test_NEITHER_stage_reaches_the_composed_lifetime_without_the_policy(self):
        """The same two stages, and both tokens must fall back to 900."""
        held = self.implemented()
        self.drive(held.job, held.composed, 'review', 'waiting')
        review_attempt = self.only_attempt(held.composed, 'review')
        for role, attempt_id in (('implementation', held.attempt_id),
                                 ('review', review_attempt)):
            _domain, _generation, token = self.token_of_attempt(
                held.control, attempt_id)
            self.assertEqual(token['seconds'], tokens.LIFETIME_SECONDS,
                             f'the disconnected {role} stage must fall back')
            self.assertEqual(token['seconds'], 900)


class _SettableClock:
    """THE FIXTURE'S OWN UTC CLOCK, advanced deliberately and never by wall time.

    `tests.manager.test_authoring_enforcement.Clock` answers `utc` for the
    worker-manager cases above; the composed deployment and its two stores want
    a plain callable, so this is that shape over the same fixed origin.
    """

    def __init__(self, at=None):
        from tests.job_manager import fixtures

        self.at = fixtures.NOW if at is None else at

    def __call__(self):
        return self.at

    def advance(self, seconds):
        import datetime

        held = datetime.datetime.strptime(
            self.at, '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                tzinfo=datetime.timezone.utc)
        held = held + datetime.timedelta(seconds=seconds)
        self.at = (held.strftime('%Y-%m-%dT%H:%M:%S.')
                   + f'{held.microsecond // 1000:03d}Z')
        return self.at


class TheOwnerFailureReachesTheReportThroughStatus(NativeComposedCase):
    """THE JOINED PROOF: owner cause -> durable capture -> `/7` -> report.

    THE FAILURE THIS IS ABOUT IS THE OWNER'S OWN. On 2026-10-19 the recovered
    pilot's implementation died because its workspace token expired at 900s
    with zero renewals while the Job allowed 3600s of provider execution
    (`OWNER-FAILURE-EVIDENCE-20261019.md`). Two things had to become true: the
    token must carry the Job's COMPOSED lifetime instead of 900, and when a
    deadline does end a runtime the ORDINARY status must say so with an
    actionable cause rather than leaving an operator guessing.

    So this drives the real composed native deployment to a started container,
    advances the clock past that composed deadline, runs THE OWNER'S OWN
    RECLAIM PASS -- `tools/job_manager._reclaiming`, the production one -- and
    then reads the cause back out through `status` and
    `attempt_diagnostics.report`. Nothing here writes a cause, a status
    document or a report row.

    WHY THE RECLAIM IS DRIVEN EXPLICITLY AND IS NOT A FIXTURE SHORTCUT:
    `manager.serve` takes `reclaim=` as its own optional pass
    (`manager.py:833`, *"a run that cannot reclaim must not begin"*), and
    `sweep` alone never reclaims. A fixture that only swept would advance the
    clock past every deadline and prove nothing, which is exactly what the
    first attempt at this case did.
    """

    def running(self):
        """One real composed attempt with its container started, no turn run."""
        from baton_v12.job_manager import submit as submit_jobs

        job, control, composed = self.serving()
        submit_jobs(job, self.submission)
        self.drive(job, composed, 'implementation', 'waiting')
        attempt_id = self.only_attempt(composed, 'implementation')
        return SimpleNamespace(job=job, control=control, composed=composed,
                               attempt_id=attempt_id)

    def serving(self, **members):
        """The native composition on a clock THE STORES ALSO READ.

        `SingleWorkerCase.stores` pins both stores to `fixtures.NOW`, and a
        token's expiry is judged against the control store's own clock -- so
        advancing only the serving clock leaves every deadline in the future
        and no reclaim is ever eligible. Measured, not assumed: the first
        attempt advanced the serving clock alone and the pass found nothing.
        """
        self.clock = _SettableClock()
        return super().serving(**members)

    def stores(self, incarnation):
        from baton_v12.job_manager import JobStore
        from tests.tools.test_single_worker import AUTHORITY_UUID

        job = JobStore.open(self.job_path, authority_uuid=AUTHORITY_UUID,
                            incarnation=incarnation, clock=self.clock)
        control = ControlStore.open(self.control_path,
                                    incarnation=incarnation, clock=self.clock)
        self.addCleanup(job.close)
        self.addCleanup(control.close)
        return job, control

    def reported(self, held, *, observed_at):
        """The ORDINARY status document, projected by the ORDINARY report."""
        import json as _json

        from baton_v12.job_manager import status as projected
        from tools import attempt_diagnostics

        document = projected(held.job, held.composed, observed_at=observed_at)
        self.assertEqual(document['schema'], 'baton.v12.job-status/7')
        report = attempt_diagnostics.report(
            _json.dumps(document).encode('utf-8'))
        row = [one for one in report['rows']
               if one['stage']['kind']['value'] == 'implementation'][0]
        return report, row

    def test_a_MISSING_cause_is_an_explicit_unknown_and_not_an_invention(self):
        """The arm that has to come first: before the reclaim there IS none.

        A report that only ever ran against a failed attempt could be printing
        a cause it made up. This proves the absence is stated.
        """
        held = self.running()
        _report, row = self.reported(held, observed_at=self.clock())
        self.assertIsNone(row['cause'])
        self.assertEqual(row['unknown_why'],
                         'no durable cause was established for this attempt')
        # AND WHICH CARRIERS IT LOOKED FOR, so "unknown" is checkable.
        self.assertTrue(any('expiry-reclaim' in one
                            for one in row['absent_records']))
        self.assertFalse(row['diagnostic_degradation']['known'])

    def test_the_OWNERS_expiry_reclaim_reaches_the_report_with_its_cause(self):
        held = self.running()
        # THE DEADLINE IS THE COMPOSED ONE, which is the owner's first failure
        # answered: the pilot died on 900 with no renewal.
        expected = execution_limits.task_token_seconds(
            execution_limits.resolved(self.SELECTED))
        _domain, _generation, token = self.token_of_attempt(
            held.control, held.attempt_id)
        self.assertEqual(token['seconds'], expected)
        self.assertEqual(token['renewals'], 0)

        later = self.clock.advance(expected + 60)
        # THE OWNER'S OWN PASS, composed exactly as the deployment composes it.
        reclaim = job_manager_tool._reclaiming(
            held.control, self.config['engine'], self.engine)
        answer = reclaim(now=later)
        self.assertEqual(answer['refused'], [])
        [reclaimed] = answer['reclaimed']
        self.assertEqual(reclaimed['attempt_id'], held.attempt_id)

        report, row = self.reported(held, observed_at=later)
        self.assertEqual(report['schema'], 'baton.v12.attempt-diagnostics/1')
        self.assertEqual(report['is_acceptance'], False)
        cause = row['cause']
        self.assertIsNotNone(cause, 'the reclaim established no durable cause')
        # THE CAUSE, NAMED -- not a generic failure.
        self.assertEqual(cause['component']['value'], 'expiry-reclaim')
        # EXACT OPERATION AND CORRELATION, which is what makes it actionable.
        for member in ('operation_id', 'correlation_id', 'outcome',
                       'cessation'):
            self.assertTrue(cause[member]['known'],
                            f'the cause must carry a known {member}')
        self.assertEqual(cause['runtime_id']['value'],
                         row['execution']['runtime_id']['value'])
        # AND WHAT IT ACTUALLY DID, so an operator is not guessing.
        self.assertIn('revoke', cause['effects']['value'])

        # CORRELATED TO THE ADMITTED LIMITS, read from the status document.
        requested = row['execution_limits']['requested']
        self.assertEqual(requested['provider_turn_seconds']['value'],
                         self.SELECTED['provider_turn_seconds'])
        self.assertEqual(requested['verification_command_seconds']['value'],
                         self.SELECTED['verification_command_seconds'])

        # SAFE LOCATORS: the attempt is named, and the workspace object says
        # in the artifact itself that it is not a path and resolves nothing.
        self.assertTrue(row['locators']['attempt_id']['known'])
        self.assertFalse(row['locators']['workspace_object']['is_a_path'])
        self.assertFalse(row['locators']['workspace_object']['is_a_locator'])

    def test_the_packaged_report_discloses_NO_secret(self):
        """The report is published to an operator, so this is not optional."""
        import json as _json

        held = self.running()
        later = self.clock.advance(
            execution_limits.task_token_seconds(
                execution_limits.resolved(self.SELECTED)) + 60)
        job_manager_tool._reclaiming(
            held.control, self.config['engine'], self.engine)(now=later)
        report, _row = self.reported(held, observed_at=later)
        packaged = _json.dumps(report)
        self.assertNotIn(self.secret, packaged)
        # AND NO WORKFLOW MUTATION: the report opens no store at all.
        self.assertTrue(report['opens_no_store'])
