"""Actual fixture owners, worker reports and custody; engine/provider are simulated.

These are joined component checks, never evidence of a live model proof.
"""
from contextlib import nullcontext
from datetime import datetime, timezone
import unittest
from unittest import mock

import accounting as a
from baton_v12.authority import Authority
from baton_v12.job_manager import status
from baton_v12.integration import reconciliation
from tests.tools import test_stage_execution as cases
from tools import stage_execution, single_worker


class JoinedJudges(unittest.TestCase):
    def pending(self):
        fixture = cases.TwoBoundJobsTraverseServingAndCorrection('test_real_B_consumer_judges_frozen_reports_and_completes_both_jobs')
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        held, deployment, result_id, result = fixture.pending_judgments()
        return fixture, held, deployment, result_id, result

    def observe(self, fixture, held, deployment, *, result_reader=None):
        config = deployment.given
        projected = status(held.job, held.composed, observed_at='2026-09-12T00:00:00.000Z')
        works = {binding['job_id'][-1]: binding['job_work_id'] for binding in config['job_bindings']}
        works.update({kind: one['deployment']['input_manifest']['work_ref']['work_id'] for kind, one in config['result_judgment_workers']['job-b'].items()})
        with Authority.open_readonly(fixture.authority_path, expected_authority_uuid=config['authority_uuid']) as owner:
            claims = a.read_claims(owner, works)
            latest = max(a.instant(event['at']) for row in claims.values() for event in row['events']) + 1
            now = datetime.fromtimestamp(latest, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            reader = a.BoundJudges(config, incarnation=projected['incarnation'], authority=owner, clock=lambda: now, control_path=fixture.control_path)
            with mock.patch.object(a.ControlStore, 'open', side_effect=AssertionError('write-capable opener')), mock.patch.object(stage_execution, 'operations_from', side_effect=AssertionError('serving factory')), mock.patch.object(a.reconciliation, 'result_of', side_effect=result_reader) if result_reader else nullcontext():
                return reader.read(projected, claims)

    def test_pending_then_three_frozen_reports_and_both_imported_without_reader_actions(self):
        fixture, held, deployment, result_id, result = self.pending()
        exclusions, observations, failed = self.observe(fixture, held, deployment)
        self.assertIsNone(failed)
        self.assertEqual(3, len(observations))
        self.assertTrue(all(one['verdict'] is None for one in observations))
        self.assertEqual(3, len(next(iter(exclusions.values()))))
        for execution in deployment.judges.values(): fixture.judgment_turn(held, execution)
        fixture.tick(held)
        exclusions, observations, failed = self.observe(fixture, held, deployment)
        self.assertIsNone(failed)
        self.assertEqual({'verification': 'accepted', 'review': 'accepted', 'approval': 'accepted'}, {one['kind']: one['verdict'] for one in observations})
        self.assertTrue(all(one['receipt_digest'] for one in observations))
        fixture.drive_job(held.job, held.composed, 'job-b', 'integration', 'completed', ticks=14)
        _, observations, failed = self.observe(fixture, held, deployment)
        self.assertIsNone(failed)
        self.assertEqual('imported', reconciliation.result_of(deployment.integration, result_id)['state'])
        self.assertEqual(4, len(deployment.authority.receipts(result['derived_proposal_id'])))
        for job in ('job-a', 'job-b'): self.assertEqual('completed', fixture.states_for(held.job, held.composed, job)['integration'])

    def test_frozen_rejection_is_primary_and_does_not_need_other_judges_to_finish(self):
        fixture, held, deployment, result_id, result = self.pending()
        execution = deployment.judges[(result_id, 'verification')]
        fixture.judgment_turn(held, execution, verdict='rejected')
        execution.poll()
        _, observations, failed = self.observe(fixture, held, deployment)
        self.assertIsNotNone(failed)
        self.assertEqual(('verification', 'rejected', 'frozen'), (failed['kind'], failed['verdict'], failed['ending']))
        self.assertEqual([], deployment.authority.receipts(result['derived_proposal_id']))
        self.assertEqual('published', reconciliation.result_of(deployment.integration, result_id)['state'])

    def test_changed_live_policy_refuses_before_credit(self):
        fixture, held, deployment, _, _ = self.pending()
        with mock.patch.object(Authority, 'policy_generation', side_effect=lambda: deployment.given['policy_generation'] + 100):
            with self.assertRaisesRegex(a.AccountingError, 'subject/result/policy'):
                self.observe(fixture, held, deployment)

    def test_bound_live_failure_and_foreign_exchange(self):
        fixture, held, deployment, _, _ = self.pending()
        # Acquisition and manager bindings remain real. Only the public exchange
        # answer is substituted to exercise the observer's closed failure mapping.
        for terminal in ({'ending': 'answered', 'disposition': 'unable'}, {'ending': 'lost'},
                         {'ending': 'faulted', 'fault_code': next(iter(a.exchange.FAULT_CODES))}):
            with self.subTest(terminal=terminal), mock.patch.object(a.exchange, 'observation', return_value={'receipt': True, 'terminal': terminal}):
                _, _, failed = self.observe(fixture, held, deployment)
                self.assertTrue(failed['failure'])
                self.assertEqual(terminal['ending'], failed['ending'])
        for bad in ('foreign', 'unreadable'):
            with self.subTest(bad=bad), mock.patch.object(a.exchange, 'observation', return_value={bad: True}):
                with self.assertRaisesRegex(a.AccountingError, 'unreadable/foreign'):
                    self.observe(fixture, held, deployment)

    def test_ordinary_import_between_result_and_policy_reads_refreshes_all_facts(self):
        fixture, held, deployment, result_id, _ = self.pending()
        for execution in deployment.judges.values(): fixture.judgment_turn(held, execution)
        original = a.reconciliation.result_of
        seen = []
        def interleaved(store, key):
            result = original(store, key)
            if not seen:
                seen.append((result['state'], deployment.authority.policy_generation()))
                fixture.drive_job(held.job, held.composed, 'job-b', 'integration', 'completed', ticks=14)
            return result
        with self.assertRaises(a.BudgetWake):
            self.observe(fixture, held, deployment, result_reader=interleaved)
        self.assertEqual('published', seen[0][0])
        self.assertGreater(deployment.authority.policy_generation(), seen[0][1])
        self.assertEqual('imported', original(deployment.integration, result_id)['state'])
        _, observations, failed = self.observe(fixture, held, deployment)
        self.assertIsNone(failed)
        self.assertEqual(3, len(observations))
        self.assertTrue(all(one['verdict'] == 'accepted' for one in observations))
        for job in ('job-a', 'job-b'): self.assertEqual('completed', fixture.states_for(held.job, held.composed, job)['integration'])

    def test_movement_during_judge_reads_refreshes_before_returning_credit(self):
        fixture, held, deployment, result_id, _ = self.pending()
        original = a.BoundJudges.judge
        moved = []
        def interleaved(reader, *args):
            observed = original(reader, *args)
            if not moved:
                moved.append(True)
                for execution in deployment.judges.values(): fixture.judgment_turn(held, execution)
                fixture.drive_job(held.job, held.composed, 'job-b', 'integration', 'completed', ticks=14)
            return observed
        # The old manager snapshot and removed launch may themselves request a
        # fresh read; either path must discard the old claims and observations.
        with mock.patch.object(a.BoundJudges, 'judge', new=interleaved):
            with self.assertRaises(a.BudgetWake): self.observe(fixture, held, deployment)
        _, observed, failed = self.observe(fixture, held, deployment)
        self.assertIsNone(failed)
        self.assertEqual(3, len(observed))
