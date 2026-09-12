"""Offline owner-time fixtures. No live engine, credential or database operation."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import accounting as a

HERE = Path(__file__).resolve().parent
REC = HERE.parent
LIMITS = {'impl': 240, 'original-review': 180, 'integrator': 120, 'verification': 180, 'review': 180, 'approval': 180}


def at(number):
    return datetime.fromtimestamp(number, timezone.utc).isoformat()


def history(name, start, end=None):
    fixed = {'work_ref': {'authority_uuid': 'unit', 'work_id': name}, 'participant': name, 'generation': 1}
    events = [{'cause': 'claimed', 'assignment_ref': fixed, 'at': at(start)}]
    if end is not None:
        events.append({'cause': 'pass', 'assignment_ref': fixed, 'at': at(end)})
    return {'current': fixed if end is None else None, 'events': events}


class AccountingTests(unittest.TestCase):
    def choose(self, rows, now, *, elapsed=300, credited=True):
        excludes = {}
        if credited and 'integrator' in rows:
            excludes[a.key(rows['integrator']['events'][0]['assignment_ref'])] = [row['events'][0]['assignment_ref'] for name, row in rows.items() if name in ('verification', 'review', 'approval')]
        return a.evaluate(rows, excludes, now=now, elapsed=elapsed, limits=LIMITS)

    def integration(self, decision):
        return next(c for c in decision['clocks'] if c['kind'] == 'integration')

    def test_run9_replay_preserves_unspent_judge_allowance(self):
        claims = json.loads((REC / 'evidence/run9-budget-150384/authority-assignments.json').read_text())
        deadline = a.instant('2026-09-12T05:59:52.183Z')
        for row in claims.values():
            row['events'] = [e for e in row['events'] if a.instant(e['at']) <= deadline]
            row['current'] = row['events'][-1]['assignment_ref'] if row['events'][-1]['cause'] == 'claimed' else None
        fixed = claims['b']['current']
        excludes = {a.key(fixed): [claims[n]['events'][0]['assignment_ref'] for n in ('verification', 'review', 'approval')]}
        limits = {e['assignment_ref']['participant']: 240 if 'impl-' in e['assignment_ref']['participant'] else 120 if 'integrator' in e['assignment_ref']['participant'] else 180 for row in claims.values() for e in row['events']}
        decision = a.evaluate(claims, excludes, now=deadline, elapsed=405.787504, limits=limits)
        self.assertAlmostEqual(.158, self.integration(decision)['charged'], places=5)
        self.assertAlmostEqual(60.158, decision['remaining'], places=5)
        self.assertTrue(self.integration(decision)['paused'])
        json.dumps(decision, allow_nan=False)

    def test_direct_integration_has_no_credit(self):
        with self.assertRaises(a.BudgetExpired) as caught:
            self.choose({'integrator': history('integrator', 0)}, 120)
        self.assertEqual(0, caught.exception.clock['excluded'])

    def test_overlapping_judges_are_union_not_sum(self):
        rows = {'integrator': history('integrator', 0), 'verification': history('verification', 10, 70), 'review': history('review', 20, 80), 'approval': history('approval', 30, 60)}
        clock = self.integration(self.choose(rows, 100))
        self.assertEqual((70, 30, 90, False), (clock['excluded'], clock['charged'], clock['remaining'], clock['paused']))

    def test_gaps_preparation_and_post_judgment_are_charged(self):
        rows = {'integrator': history('integrator', 0), 'verification': history('verification', 10, 30), 'review': history('review', 40, 60)}
        self.assertEqual(60, self.integration(self.choose(rows, 100))['charged'])
        with self.assertRaises(a.BudgetExpired): self.choose(rows, 160)

    def test_judge180_stays_armed_while_integration_paused(self):
        rows = {'integrator': history('integrator', 0), 'verification': history('verification', 10)}
        decision = self.choose(rows, 150)
        self.assertEqual(40, decision['remaining'])
        with self.assertRaises(a.BudgetExpired) as caught: self.choose(rows, 190)
        self.assertEqual('verification', caught.exception.clock['assignment']['participant'])

    def test_completed_intervals_between_polls_cannot_hide_overrun(self):
        rows = {'integrator': history('integrator', 0, 200), 'verification': history('verification', 10, 70)}
        with self.assertRaises(a.BudgetExpired): self.choose(rows, 210)
        rows['integrator'] = history('integrator', 0, 180)
        self.choose(rows, 210)  # exactly120 charged ended on time

    def test_exclusions_clipped_to_integration_interval(self):
        rows = {'integrator': history('integrator', 20), 'verification': history('verification', 10, 30)}
        self.assertEqual(10, self.integration(self.choose(rows, 50))['excluded'])

    def test_repeated_poll_never_resets_integration_balance(self):
        rows = {'integrator': history('integrator', 0), 'verification': history('verification', 20, 80)}
        self.assertEqual(40, self.integration(self.choose(rows, 100))['charged'])
        self.assertEqual(60, self.integration(self.choose(rows, 120))['charged'])

    def test_no_credit_without_bound_result(self):
        rows = {'integrator': history('integrator', 0), 'verification': history('verification', 10)}
        with self.assertRaises(a.BudgetExpired): self.choose(rows, 120, credited=False)

    def test_foreign_or_unclaimed_exclusion_refuses(self):
        row = history('integrator', 0)
        with self.assertRaises(a.AccountingError):
            a.evaluate({'integrator': row}, {a.key(row['current']): [history('review', 1)['current']]}, now=50, elapsed=50, limits=LIMITS)

    def test_future_missing_and_duplicate_claims_refuse(self):
        for row in (history('integrator', 60), {'current': history('integrator', 0)['current'], 'events': []}):
            with self.assertRaises(a.AccountingError): self.choose({'integrator': row}, 50, credited=False)
        row = history('integrator', 0); row['events'] *= 2
        with self.assertRaises(a.AccountingError): self.choose({'integrator': row}, 50, credited=False)

    def test_whole1200_wins_even_when_judges_pause_integration(self):
        with self.assertRaises(a.BudgetExpired) as caught:
            self.choose({'integrator': history('integrator', 0), 'verification': history('verification', 10)}, 20, elapsed=1200)
        self.assertEqual('whole-run', caught.exception.clock['kind'])

    def test_final_tests_require_positive_remainder_and_cap30(self):
        self.assertEqual(30, a.final_timeout(1100))
        self.assertEqual(.5, a.final_timeout(1199.5))
        for value in (1200, 1201):
            with self.assertRaises(a.BudgetExpired): a.final_timeout(value)

    def test_stale_alarm_wakes_for_fresh_owners_but_whole_expiry_is_fatal(self):
        clock = [120]; calls = []; record = {}
        alarm = a.Alarm(started=0, monotonic=lambda: clock[0], set_timer=lambda seconds: calls.append(('arm', seconds)), record=record, persist=lambda value: calls.append(('persist', value)))
        alarm.arm({'winner': {'kind': 'integration'}, 'remaining': 1})
        self.assertEqual('persist', calls[0][0])
        with self.assertRaises(a.BudgetWake): alarm(None, None)
        self.assertEqual(('arm', 1080), calls[-1])
        clock[0] = 1200
        with self.assertRaises(a.BudgetExpired): alarm(None, None)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='w71879-150501-binding-'))
        self.config = json.loads((REC / 'prepared-150007/frozen-config/stage-execution.json').read_text())
        self.config['state_root'] = str(self.root)
        self.subject = json.loads((REC / 'evidence/run9-budget-150384/subject.json').read_text())
        home = self.root / 'result-judgments' / a.digest(self.subject['result_id'])[7:]
        home.mkdir(parents=True)
        self.subject_path = home / 'subject.json'; self.subject_path.write_text(json.dumps(self.subject))
        self.status = json.loads((REC / 'evidence/run9-budget-150384/last-status.json').read_text())
        self.claims = json.loads((REC / 'evidence/run9-budget-150384/authority-assignments.json').read_text())
        self.held = dict(self.subject, state='published', authority_uuid=self.config['authority_uuid'],
                         integration_assignment=self.claims['b']['current'], integration_attempt_id=self.status['jobs'][1]['stages'][-1]['attempt_id'],
                         work_id=self.claims['b']['current']['work_ref']['work_id'], prepared={'head': self.subject['candidate'], 'tree': self.subject['tree']})
        self.authority = mock.Mock(); self.authority.policy_generation.return_value = 25
        self.control_path = self.root / 'control.sqlite3'
        self.manager = a.ControlStore.open(str(self.control_path), incarnation='w71879-run9', clock=lambda: '2026-09-12T06:01:00.000Z')
        self.addCleanup(self.manager.close)
        from baton_v12.worker_manager.workspaces import configure_workspace_group
        configure_workspace_group(self.manager, os.getgid())
        self.reader = a.BoundJudges(self.config, incarnation='w71879-run9', authority=self.authority, clock=lambda: '2026-09-12T06:01:00.000Z', control_path=self.control_path)
        # All exchange/output paths in this test are private fixture paths.
        for kind, one in self.config['result_judgment_workers']['job-b'].items():
            one['deployment']['workspace_storage'] = str(self.root / 'storage' / kind)
            one['deployment']['launch_home'] = str(self.root / 'launch' / kind)

    def read(self):
        with mock.patch.object(a.IntegrationStore, 'open_readonly') as opened, mock.patch.object(a.reconciliation, 'result_of', return_value=self.held):
            answer = self.reader.read(self.status, self.claims)
            opened.assert_called_once()
            return answer

    def test_ended_judge_without_activated_owner_binding_refuses(self):
        with self.assertRaisesRegex(a.AccountingError, 'ended judge has no activated'): self.read()

    def test_wrong_result_assignment_stage_policy_and_work_refuse_before_credit(self):
        original = deepcopy(self.held)
        for field, value in (('authority_uuid', 'foreign'), ('integration_attempt_id', 'foreign'), ('work_id', 'foreign'), ('canonical_target_id', 'foreign'), ('source_base', 'foreign')):
            self.held = deepcopy(original); self.held[field] = value
            with self.subTest(field=field), self.assertRaises(a.AccountingError): self.read()
        self.held = original; self.authority.policy_generation.return_value = 26
        with self.assertRaises(a.AccountingError): self.read()

    def test_absent_subject_grants_no_credit(self):
        self.config['state_root'] = str(self.root / 'not-created')
        self.assertEqual(({}, [], None), self.reader.read(self.status, self.claims))

    def test_required_public_owner_refusal_propagates(self):
        with mock.patch.object(a.IntegrationStore, 'open_readonly', side_effect=a.AccountingError('read-only owner refused')):
            with self.assertRaisesRegex(a.AccountingError, 'owner refused'): self.reader.read(self.status, self.claims)

    def test_no_serving_factory_or_private_store_access_in_helper(self):
        source = (HERE / 'accounting.py').read_text()
        for forbidden in ('._connection', 'sqlite3', 'operations_from(', 'StageDeployment(', 'ControlStore.open('):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
