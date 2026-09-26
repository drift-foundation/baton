"""Reviewer272088: deterministic persisted previous-format settlement account.

Uses ordinary recorder on disposable store, no raw SQL, live processes or providers.
"""
import unittest
import test_restore_outside_the_lock as author
from baton_v12.contracts import ContractRefusal


class PriorSettlement(author.RestoreOutsideTheLock):
    def test_previous_fixed_label_incomplete_launch_is_not_skipped(self):
        self.abandoned()
        recovery, executor = self.interrupted()
        # Exact label emitted by immediately preceding settlement implementation;
        # coverage protocol remains launch-account/1 across both implementations.
        recorder = author.review_cycles._launch_recorder(self.store, recovery, "settlement-1")
        recorder("intent", None)
        with self.assertRaises(ContractRefusal):
            self.settle(store=self.fresh_manager())


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([PriorSettlement(
        "test_previous_fixed_label_incomplete_launch_is_not_skipped")])
