"""Reviewer271632: focused fake-profile/real disposable store checks, no live engine.

Selected with author restoration suite; one finite local Python child for launch account.
"""
import sys
import unittest

import test_restore_outside_the_lock as author
from baton_v12.contracts import ContractRefusal
from tools.stage_execution import restoration_launcher, restoration_cessation


class CessationBoundary(author.RestoreOutsideTheLock):
    def test_cessation_observation_runs_outside_database_transaction(self):
        self.abandoned()
        honest = self.profile.restore_checkpoint
        def restoring(repository, evidence, *, runner=None):
            runner((sys.executable, "-c", "pass"))
            return honest(repository, evidence)
        self.profile.restore_checkpoint = restoring
        observed = []
        probe = restoration_cessation()
        def observe(record):
            observed.append(self.store._connection.in_transaction)
            return probe(record)
        self.restore(launcher=restoration_launcher, cessation=observe)
        self.assertTrue(observed)
        self.assertEqual(observed, [False], "kernel/process probe called under DB transaction")

    def test_missing_effect_boundary_does_not_complete(self):
        self.abandoned()
        with self.assertRaises(ContractRefusal):
            self.restore()


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(CessationBoundary(name) for name in (
        "test_cessation_observation_runs_outside_database_transaction",
        "test_missing_effect_boundary_does_not_complete"))
