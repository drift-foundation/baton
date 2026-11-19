"""W385222: real Authority/offer/Job stores retire admissions, never invent claims."""
import json
from pathlib import Path
from unittest import mock

from baton_v12.authority import Authority, claim_signature
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (cancellation, episodes_of, reconcile,
                                   receipts_of, status, submit, sweep)
from baton_v12.worker_manager import AuthorityPort, accept_offer, outstanding_offers, settle_claim
from tools.single_worker import _ManagerClaimSession
from tests.job_manager.fixtures import JobManagerCase, UUID, WORK_A, WHO, ROUTE
from tests.job_manager.test_job_control import at, controlled
from tests.job_manager import test_scheduling as scheduling
from baton_v12.job_manager import scheduler


class AcceptedOfferRetirement(JobManagerCase):
    def setUp(self):
        super().setUp()
        self.authority = Authority.create(str(Path(self.root) / 'authority.sqlite3'), authority_uuid=UUID, clock=self.clock)
        self.addCleanup(self.authority.dispose)
        self.authority.principal_of(WHO)
        self.authority.create_work(WORK_A, ROUTE, contract='v12-assignment-1', operation_id='create-retirement')
        self.session = _ManagerClaimSession(self.authority.session(WHO))
        self.port = AuthorityPort(self.session, claim_signature)
        self.jobs = self.store()
        self.control_store = self.control()
        self.launches = []
        self.acts = self.operations(control=self.control_store, port=self.port, start_runtime=lambda *args: self.launches.append(args))
        submit(self.jobs, controlled())
        self.tick(0)
        self.stage = self.attempting(self.jobs)
        accept_offer(self.control_store, self.port, offer_id=self.stage['offer_id'], decision='accept', bearer=self.delivered[-1]['bearer'], now=at(1), runtime_attempt_id=self.stage['attempt_id'], work_ref={'authority_uuid': UUID, 'work_id': WORK_A})
        self.instants.append(at(1))

    def tick(self, seconds):
        self.instants.append(at(seconds))
        return sweep(self.jobs, self.acts, now=at(seconds))

    def row(self):
        return self.control_store.operation_record('offer.settle:' + self.stage['offer_id'])

    def cancel(self, seconds=2):
        self.instants.append(at(seconds))
        return cancellation.request(self.jobs, job_id='job-a', reason='bounded cancellation')

    def entry(self):
        return status(self.jobs, self.acts, observed_at=self.clock())['jobs'][0]

    def assert_ended(self, state):
        self.assertEqual([(r['episode'], r['ended_state']) for r in episodes_of(self.jobs, self.stage['stage_id'])], [(1, state)])
        self.assertEqual(self.launches, [])

    def test_positive_route_refusal_retires_once_and_never_becomes_a_claim(self):
        answer = self.tick(5)
        self.assertEqual([(r['act'], r['outcome']) for r in answer['acts']], [('claim', 'refused')])
        self.assert_ended('claim-refused')
        self.assertEqual(self.entry()['stages'][0]['state'], 'exceptional')
        self.assertEqual(receipts_of(self.jobs, self.stage['stage_id'], 1)['claim']['state'], 'refused')
        recorded = self.row()
        for seconds in [10, 130, 5000]:
            self.assertEqual(self.tick(seconds)['acts'], [])
            self.assertEqual(self.row(), recorded)
        self.authority.add_route_handler(ROUTE, WHO)
        offer = self.control_store.operation_record('offer.accept:' + self.stage['offer_id'])
        accepted = json.loads(offer['result'])
        with self.assertRaises(ContractRefusal):
            self.session.claim({'work_id': WORK_A, 'operation_id': accepted['claim_operation_id']})

    def test_fenced_accepted_offer_waits_for_settlement_then_completes_and_replays(self):
        self.cancel()
        self.tick(3)
        self.assertIsNone(self.row())
        self.assertEqual(self.entry()['cancellation']['targets'][0]['state'], 'awaiting-offer-lapse')
        result = self.tick(62)
        self.assertEqual(result['acts'], [])
        self.assertEqual(result['started'], [])
        self.assert_ended('settlement-expired')
        self.assertEqual(self.entry()['cancellation']['shutdown'], 'complete')
        recorded = self.row()
        self.tick(100)
        self.assertEqual(self.row(), recorded)
        self.jobs.close()
        self.jobs = self.store(incarnation='jobs-2')
        self.acts = self.operations(control=self.control(incarnation='manager-2'), port=self.port)
        report = reconcile(self.jobs, self.acts, now=at(101))
        self.assertEqual(report['acts'], [])
        self.assertEqual(report['started'], [])
        self.assertEqual(self.entry()['cancellation']['shutdown'], 'complete')

    def test_lost_committed_claim_is_adopted_under_fence_not_retired_or_launched(self):
        self.authority.add_route_handler(ROUTE, WHO)
        original = self.session.claim
        def lost(*args):
            original(*args)
            raise ContractRefusal('ambiguous', 'operation', 'reply lost')
        with mock.patch.object(_ManagerClaimSession, 'claim', side_effect=lost):
            self.tick(2)
        self.assertIsNone(self.row())
        self.cancel(3)
        report = self.tick(62)
        self.assertEqual(json.loads(self.row()['result'])['state'], 'claimed')
        self.assertEqual([(r['act'], r['outcome']) for r in report['acts']], [('claim', 'adopted')])
        self.assertEqual(self.launches, [])
        self.assertNotEqual(self.entry()['cancellation']['shutdown'], 'complete')
        self.assertEqual(episodes_of(self.jobs, self.stage['stage_id'])[0]['ended_state'], None)

    def test_unknown_claim_answer_keeps_identity_open_before_deadline(self):
        refusal = ContractRefusal('ambiguous', 'operation', 'uncertain reply')
        with mock.patch.object(_ManagerClaimSession, 'claim', side_effect=refusal):
            self.tick(2)
            self.tick(20)
        self.assertIsNone(self.row())
        self.assertEqual(outstanding_offers(self.control_store)[0]['state'], 'accepted')
        self.cancel(21)
        self.tick(62)
        self.assert_ended('settlement-expired')

    def test_terminal_settlement_with_dropped_event_cannot_be_adopted_as_success(self):
        settle_claim(self.control_store, self.port, offer_id=self.stage['offer_id'], now=at(2), refused_evidence='positive refusal')
        # Lose republication for one tick, exposing the canonical receipt race.
        with mock.patch.object(type(self.acts), 'attach', return_value=[]):
            report = self.tick(3)
        self.assertEqual([(r['act'], r['outcome']) for r in report['acts']], [('claim', 'refused')])
        self.assertEqual(self.launches, [])
        self.assertEqual(receipts_of(self.jobs, self.stage['stage_id'], 1)['claim']['state'], 'refused')
        self.tick(4)
        self.assert_ended('claim-refused')

    def test_settlement_unavailable_retains_offer_and_cancellation_then_retries(self):
        self.cancel()
        with mock.patch.object(type(self.session), 'settle_operation', side_effect=ContractRefusal('ambiguous', 'operation', 'authority unavailable')):
            self.tick(62)
        self.assertIsNone(self.row())
        self.assertNotEqual(self.entry()['cancellation']['shutdown'], 'complete')
        self.tick(63)
        self.assert_ended('settlement-expired')
        self.assertEqual(self.entry()['cancellation']['shutdown'], 'complete')

    def test_external_authority_calls_never_hold_job_or_control_transaction(self):
        original = self.session.settle_operation
        def checked(*args):
            self.assertFalse(self.jobs._connection.in_transaction)
            self.assertFalse(self.control_store._connection.in_transaction)
            return original(*args)
        self.cancel()
        with mock.patch.object(type(self.session), 'settle_operation', side_effect=checked):
            self.tick(62)
        self.assert_ended('settlement-expired')

    def test_positive_refusal_reconciles_a_claim_that_won_before_retirement(self):
        self.authority.add_route_handler(ROUTE, WHO)
        original = self.session.claim
        def competing_claim(*args):
            original(*args)
            raise ContractRefusal('refused', 'precondition', 'another submitter saw refusal')
        # Call only the claim boundary to inspect the committed assignment.
        with mock.patch.object(_ManagerClaimSession, 'claim', side_effect=competing_claim):
            answer = self.acts.claim(self.stage)
        self.assertEqual(answer['state'], 'claimed')
        self.cancel(3)
        self.tick(4)
        self.assertEqual(receipts_of(self.jobs, self.stage['stage_id'], 1)['claim']['state'], 'adopted')
        self.assertEqual(self.launches, [])
        self.assertNotEqual(self.entry()['cancellation']['shutdown'], 'complete')

    def test_transport_failure_does_not_retire_and_later_settlement_adopts_commit(self):
        self.authority.add_route_handler(ROUTE, WHO)
        original = self.session.claim
        def lost(*args):
            original(*args)
            raise OSError('transport lost')
        with mock.patch.object(_ManagerClaimSession, 'claim', side_effect=lost):
            with self.assertRaises(OSError):
                self.tick(2)
        self.assertIsNone(self.row())
        self.cancel(3)
        self.tick(62)
        self.assertEqual(json.loads(self.row()['result'])['state'], 'claimed')
        self.assertEqual(self.launches, [])
        self.assertNotEqual(self.entry()['cancellation']['shutdown'], 'complete')

    def pooled(self):
        document = scheduling.pool(workers=[scheduling.worker('impl', 'implementation', WHO, ['implementation'])])
        principals = {WHO: self.authority.principal_of(WHO)}
        scheduler.activate_pool(self.jobs, document, principals)
        scheduler.reserve(self.jobs, self.stage)
        return scheduler.PooledManagerOperations(self.jobs, {(1, 'impl'): self.acts}, resolved_principals=principals)

    def test_deadline_fence_settles_through_selected_pool_and_releases_capacity(self):
        self.acts = self.pooled()
        report = self.tick(4800)
        self.assertEqual(report['expired'][0]['trigger'], 'stage-deadline')
        self.assert_ended('settlement-expired')
        self.assertEqual(self.entry()['cancellation']['shutdown'], 'complete')
        self.assertEqual(scheduler.allocation_of(self.jobs, self.stage['attempt_id'])['allocation_state'], 'released')

    def test_pool_settlement_preserves_canonical_principal_guard(self):
        pooled = self.pooled()
        with mock.patch.object(type(self.acts), 'settle_offer', return_value={'state': 'claimed', 'decision': {'principal': 'principal:other'}}):
            with self.assertRaises(ContractRefusal) as caught:
                pooled.settle_offer(self.stage, now=at(62))
        self.assertEqual(caught.exception.code, 'identity-mismatch')
        self.assertEqual(scheduler.allocation_of(self.jobs, self.stage['attempt_id'])['allocation_state'], 'recovery-required')
        self.assertEqual(self.launches, [])
