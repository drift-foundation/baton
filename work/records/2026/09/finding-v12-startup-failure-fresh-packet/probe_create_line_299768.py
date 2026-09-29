"""Focused reached DB-1 regression; expected to fail on the current candidate.

Uses only fresh deterministic test stores. No deployed coordination store or
live engine is opened. The transaction flag is observed on that fixture's own
connection while real filesystem calls execute; no SQL is read or written here.
"""
import json
import os
from pathlib import Path
import unittest
from unittest import mock

from baton_v12.worker_manager import review_cycles, workspaces
from test_baseline_bindings import TheFreshPacket


class ReachedLineCompletion(TheFreshPacket):
    def test_no_filesystem_call_under_create_line_transaction(self):
        observations = []
        create = review_cycles.create_line
        lstat, fchmod = workspaces.os.lstat, workspaces.os.fchmod

        def wrapped(store, **operands):
            def observed(name, operation):
                def call(*args, **kwargs):
                    observations.append({"operation": name, "operand": str(args[0]), "in_transaction": store._connection.in_transaction})
                    return operation(*args, **kwargs)
                return call
            with mock.patch.object(workspaces.os, "lstat", side_effect=observed("lstat", lstat)), mock.patch.object(workspaces.os, "fchmod", side_effect=observed("fchmod", fchmod)):
                return create(store, **operands)

        with mock.patch.object(review_cycles, "create_line", side_effect=wrapped):
            self.test_fresh_positive_one_proposal_without_context()
        locked = [row for row in observations if row["in_transaction"]]
        retained = os.environ.get("BATON_TEST_DB1_EVIDENCE")
        if retained:
            destination = Path(retained)
            if destination.exists():
                raise AssertionError("refuse evidence overwrite")
            destination.write_text(json.dumps({"observations": observations, "locked": locked, "connected_positive_completed": True}, indent=2) + "\n")
        self.assertTrue(observations, "create_line boundary was not reached")
        self.assertEqual(locked, [], "DB-1: reached filesystem calls while create_line held its transaction")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ReachedLineCompletion("test_no_filesystem_call_under_create_line_transaction")]))
    raise SystemExit(not result.wasSuccessful())
