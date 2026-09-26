"""W257624: deterministic overlapping restorers on two disposable handles.

The profile seam writes a real file as the controlled checkout-reset effect.
No engine, Git, provider or deployed store. B finishes while A has entered its
profile; B releases, a successor writes, then A's delayed effect overwrites it.
Only the local test is selected; inherited author cases are not rerun here.
"""
from pathlib import Path
import unittest

from test_restore_outside_the_lock import RestoreOutsideTheLock, ControlStore, NOW


class Overlap(RestoreOutsideTheLock):
    def test_a_delayed_restorer_cannot_overwrite_an_admitted_successor(self):
        self.abandoned()
        marker = Path(self.line_path) / 'review-successor-data.txt'
        marker.write_text('abandoned scratch')
        original = self.profile.restore_checkpoint
        crossings = []
        outcomes = []
        other = ControlStore.open(self.control_path, incarnation='second-restorer',
                                  clock=lambda: NOW)
        self.addCleanup(other.close)

        def restoring(repository, evidence):
            crossings.append(repository)
            if len(crossings) == 1:
                # A is in external restoration; B adopts its unfinished intent.
                outcomes.append(self.restore(store=other))
                successor = self.granted(self.line_id, 3,
                                          based=self.checkpoint['checkpoint_id'])
                self.assertEqual(successor['state'], 'active')
                marker.write_text('successor work must survive')
            answer = original(repository, evidence)
            # Model the destructive profile effect on real disposable bytes.
            marker.write_text('restored checkpoint')
            return answer

        self.profile.restore_checkpoint = restoring
        answered = self.restore()
        self.assertEqual(len(crossings), 2)
        self.assertEqual(answered, outcomes[0])
        self.assertEqual(self.line_row()['state'], 'writing')
        self.assertEqual(marker.read_text(), 'successor work must survive')


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([Overlap(
        'test_a_delayed_restorer_cannot_overwrite_an_admitted_successor')])
