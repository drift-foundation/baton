"""Swap disposable homes after the last identity check, before removal uses the name."""
import os
import unittest
from unittest import mock
from test_removal_outside_the_lock import RemovalOutsideTheLock
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal


class AfterPinSwap(RemovalOutsideTheLock):
    def test_substitute_survives_after_last_identity_check(self):
        self.attempt_roots()
        home = os.path.join(self.storage, "assignment-1")
        replacement = os.path.join(self.temporary_root(), "review-substitute")
        os.mkdir(replacement)
        marker = os.path.join(replacement, "unrelated.txt")
        with open(marker, "w") as stream:
            stream.write("preserve substitute")
        honest = workspaces._still_the_pinned_home

        def checked(*args, **kwargs):
            answer = honest(*args, **kwargs)
            os.rename(home, home + ".review-original")
            os.rename(replacement, home)
            return answer

        with mock.patch.object(workspaces, "_still_the_pinned_home", side_effect=checked):
            try:
                workspaces.discard_workspace(self.storage, "assignment-1", control=self.store)
            except ContractRefusal:
                pass
        self.assertTrue(os.path.isfile(os.path.join(home, "unrelated.txt")),
                        "replacement was deleted after the identity check")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AfterPinSwap("test_substitute_survives_after_last_identity_check")])
