"""Candidate 1c233d6b: stale caller before outer lock, controlled file reset.

No product mutation or actual Git/engine operation. Two real store handles,
real restoration and successor admission; wrapper only schedules the pause.
"""
from pathlib import Path
import unittest
from unittest import mock

import test_restore_outside_the_lock as author


class AtomicAdmission(author.RestoreOutsideTheLock):
    def test_completed_competitor_before_claim_preserves_successor(self):
        self.abandoned()
        marker = Path(self.line_path) / 'review-episode-successor.txt'
        marker.write_text('abandoned scratch')
        other = author.ControlStore.open(self.control_path,
            incarnation=self.store.incarnation, clock=lambda: author.NOW)
        self.addCleanup(other.close)
        original_claim = author.review_cycles.workspaces.hold_restoration_lock
        original_restore = self.profile.restore_checkpoint
        paused = []
        crossings = []
        results = []

        def restoring(repository, evidence):
            crossings.append(repository)
            answer = original_restore(repository, evidence)
            marker.write_text('restored checkpoint')
            return answer

        def delayed(*args, **kwargs):
            if not paused:
                paused.append(True)
                # A passed initial replay/eligibility reads, before outer lock acquisition.
                results.append(self.restore(store=other))
                granted = self.granted(self.line_id, 3,
                    based=self.checkpoint['checkpoint_id'])
                self.assertEqual(granted['state'], 'active')
                marker.write_text('successor work must survive')
            return original_claim(*args, **kwargs)

        self.profile.restore_checkpoint = restoring
        with mock.patch.object(author.review_cycles.workspaces, 'hold_restoration_lock', delayed):
            answer = self.restore()
        self.assertEqual(answer, results[0])
        self.assertEqual(len(crossings), 1, 'stale caller must not enter profile')
        self.assertEqual(marker.read_text(), 'successor work must survive')


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AtomicAdmission(
        'test_completed_competitor_before_claim_preserves_successor')])
