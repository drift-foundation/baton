"""Independent selected-path overlap regression, claim262771.

Source-audited deterministic selector: this module's one test only. Inherits
the dossier's real-store, disk-backed, fake-engine abandonment fixture. No
live engine/provider, residue inspection or deployed operation.
"""
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody, workspaces
from test_resource_guards import TheAdoptionToUseWindowOnTheEndingPath


class AdoptionOverlap(TheAdoptionToUseWindowOnTheEndingPath):
    def test_workspace_hold_after_lookup_blocks_nested_result_submission(self):
        control, operations, worker, attempt_id, stage = self.ending("review-window-overlap")
        submissions = self.severing(after=1)
        original = workspaces.adopted_assignment_workspace
        injected = []

        def lookup(*args, **kwargs):
            roots = original(*args, **kwargs)
            if not injected:
                injected.append(True)
                opened = self.reopened("review-window-overlap-second")
                self.addCleanup(opened.close)
                adapter = worker._adapter(roots, None, None, None)
                with self.assertRaises(ContractRefusal):
                    custody.normalize_directory(opened, adapter, assignment_id=attempt_id, which="workspace")
            return roots

        with patch.object(workspaces, "adopted_assignment_workspace", lookup):
            with self.assertRaises(ContractRefusal) as caught:
                operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertEqual(injected, [True])
        self.assertIn("FROZEN", caught.exception.message)
        workspace = custody.custody_holds(control, attempt_id, "workspace")
        result = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual([(row["episode"], row["cleared"]) for row in workspace], [(0, False)])
        self.assertEqual(len(submissions), 1,
                         f"nested result helper submitted behind workspace hold; result episodes={result!r}")
        self.assertEqual(result, [], "held ancestor must block result claim and submission")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AdoptionOverlap("test_workspace_hold_after_lookup_blocks_nested_result_submission")])
