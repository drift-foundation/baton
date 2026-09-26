"""Settlement must not turn caller assertions into execution absence.

Real disposable stores, supported APIs, controlled file writes; no real Git reset,
engine/provider call or journal mutation. The first case deliberately supplies an
unsubstantiated ending document while the named executor is demonstrably live.
"""
from pathlib import Path
import unittest

import test_restore_outside_the_lock as author


class SettlementEvidence(author.RestoreOutsideTheLock):
    def test_live_executor_cannot_be_settled_by_an_unverified_document(self):
        self.abandoned()
        other = author.ControlStore.open(self.control_path,
            incarnation=self.store.incarnation, clock=lambda: author.NOW)
        self.addCleanup(other.close)
        marker = Path(self.line_path) / 'review-settlement-successor.txt'
        marker.write_text('abandoned scratch')
        original = self.profile.restore_checkpoint
        crossings = []
        completed = []

        def restoring(repository, evidence):
            crossings.append(repository)
            if len(crossings) == 1:
                recovery = author.review_cycles._restore_operation_id(
                    author.RESTORE_KIND, author.ABANDONED, 2)
                claim = author.review_cycles._claimed_episodes(other, recovery)[0]
                _, owner = other.replay(
                    author.review_cycles._execution_id(recovery, 1),
                    claim['signature'], kind=author.review_cycles.RESTORE_EXECUTION_KIND)
                # A is on this very call stack; no one observed its absence.
                author.review_cycles.settle_restoration_execution(other,
                    attempt_id=author.ABANDONED, generation=2,
                    ended={'kind': 'executor-absent', 'executor': owner['executor'],
                           'observed_by': 'nobody-observed-the-executor'},
                    profile=self.profile)
                completed.append(self.restore(store=other))
                granted = self.granted(self.line_id, 3,
                    based=self.checkpoint['checkpoint_id'])
                self.assertEqual(granted['state'], 'active')
                marker.write_text('successor work must survive')
            answer = original(repository, evidence)
            marker.write_text('restored checkpoint')
            return answer

        self.profile.restore_checkpoint = restoring
        answer = self.restore()
        self.assertEqual(answer, completed[0])
        self.assertEqual(len(crossings), 2, 'unsafe candidate observation')
        self.assertEqual(marker.read_text(), 'successor work must survive')

    def test_changed_settlement_observer_must_not_replay_as_exact(self):
        self.abandoned()
        _, executor = self.interrupted()
        self.settle(ended=self.attested(executor, observer='first-observer'))
        with self.assertRaises(author.ContractRefusal):
            self.settle(ended=self.attested(executor, observer='different-observer'))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(SettlementEvidence(name) for name in (
        'test_live_executor_cannot_be_settled_by_an_unverified_document',
        'test_changed_settlement_observer_must_not_replay_as_exact'))
