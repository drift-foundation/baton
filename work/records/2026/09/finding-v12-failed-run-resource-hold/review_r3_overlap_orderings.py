"""Source-audited fake-engine proofs of both stale overlap-read orderings.

Reviewer264559. Only the two explicitly listed cases run; real independent
ControlStore handles and the existing fake-engine abandonment fixture.
"""
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody
from test_resource_guards import AHeldResourceIsNotRemoved


class OverlapOrderings(AHeldResourceIsNotRemoved):
    def ordering(self, winner, loser):
        control, composed, attempt = self.unresolved_custody("review-overlap-" + winner)
        other = self.reopened("review-overlap-winner")
        self.addCleanup(other.close)
        original = custody._standing_overlap
        stale = []
        before = self.engine_effects()

        def admission(store, assignment_id, which):
            answer = original(store, assignment_id, which)
            if store is control and not stale:
                self.assertIsNone(answer)
                stale.append(True)
                with self.assertRaises(ContractRefusal) as held:
                    custody.normalize_directory(other, composed, assignment_id=attempt, which=winner)
                self.assertIn("did not answer accountably", held.exception.message)
            return answer

        with patch.object(custody, "_standing_overlap", admission):
            with self.assertRaises(ContractRefusal) as refused:
                custody.normalize_directory(control, composed, assignment_id=attempt, which=loser)
        self.assertEqual(stale, [True])
        self.assertIn("nothing was submitted", refused.exception.message)
        self.assertIn("overlapping " + loser, refused.exception.message)
        self.assertEqual(custody.custody_holds(control, attempt, loser), [])
        self.assertEqual([(row["episode"], row["cleared"]) for row in custody.custody_holds(control, attempt, winner)], [(0, False)])
        self.assertEqual(len(self.engine_effects()) - len(before), 1)
        control.close()
        reopened = self.reopened("review-overlap-restart")
        self.addCleanup(reopened.close)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(reopened, composed, assignment_id=attempt, which=loser)
        self.assertEqual(len(self.engine_effects()) - len(before), 1)

    def test_workspace_wins_after_result_read(self):
        self.ordering("workspace", "result")

    def test_result_wins_after_workspace_read(self):
        self.ordering("result", "workspace")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(OverlapOrderings(name) for name in
        ("test_workspace_wins_after_result_read", "test_result_wins_after_workspace_read"))
