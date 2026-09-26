"""Reviewer272008: selected deterministic settlement-validation retry schedule.

Fake accounted runner/profile and real disposable store, no external process or engine.
"""
import unittest
import test_restore_outside_the_lock as author


class SettlementRetry(author.RestoreOutsideTheLock):
    def test_settlement_can_retry_after_its_validation_stops(self):
        self.abandoned()
        self.interrupted()
        honest = self.profile.validate
        calls = []
        def validate(repository, evidence, **kwargs):
            result = honest(repository, evidence, **kwargs)
            calls.append(True)
            if len(calls) == 1:
                raise RuntimeError("settlement validation interrupted after accounted command")
            return result
        self.profile.validate = validate
        with self.assertRaisesRegex(RuntimeError, "settlement validation interrupted"):
            self.settle()
        settled = self.settle(store=self.fresh_manager())
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(self.line_row()["state"], "writing")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([SettlementRetry(
        "test_settlement_can_retry_after_its_validation_stops")])
