"""Reviewer271716: selected deterministic disposable-store account schedules.

Production observer test uses finite local child; remaining cases use labelled fake
launcher. No engine/provider/Git/deployed store. Historical reviewer probes unchanged.
"""
import unittest
from unittest import mock

import test_restore_outside_the_lock as author
from baton_v12.contracts import ContractRefusal
from tools.stage_execution import restoration_launcher, restoration_cessation


class AccountGuards(author.RestoreOutsideTheLock):
    def test_observer_outside_transaction(self):
        self.abandoned()
        observed = []
        probe = restoration_cessation()
        def observe(record):
            observed.append(self.store._connection.in_transaction)
            return probe(record)
        answer = self.restore(launcher=restoration_launcher, cessation=observe)
        self.assertEqual(answer["state"], "correction-ready")
        self.assertTrue(observed)
        self.assertFalse(any(observed))

    def test_missing_boundary_refuses_before_profile(self):
        self.abandoned()
        with mock.patch.object(self.profile, "restore_checkpoint") as profile:
            with self.assertRaises(ContractRefusal):
                self.restore(launcher=None, cessation=None)
            profile.assert_not_called()

    def test_new_launch_after_observation_refuses_release(self):
        self.abandoned()
        boundary = self.accounted()
        run = []
        def launcher(record):
            launch = boundary["launcher"](record)
            run.append(launch)
            return launch
        fired = []
        def observe(record):
            result = boundary["cessation"](record)
            if not fired:
                fired.append(True)
                run[0](("synthetic-review-extra-command",))
            return result
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(launcher=launcher, cessation=observe)
        self.assertIn("recorded a launch after", caught.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_recreated_recorder_refuses_reused_intent(self):
        self.abandoned()
        cycles = author.review_cycles
        recovery = cycles._restore_operation_id(author.RESTORE_KIND, author.ABANDONED, 2)
        first = cycles._launch_recorder(self.store, recovery, 1)
        first("intent", None)
        first("group", {"group": 900001, "leader": 900001, "started": 1})
        again = cycles._launch_recorder(self.store, recovery, 1)
        with self.assertRaises(ContractRefusal):
            again("intent", None)


def load_tests(loader, standard, pattern):
    names = [name for name in AccountGuards.__dict__ if name.startswith("test_")]
    return unittest.TestSuite(AccountGuards(name) for name in names)
