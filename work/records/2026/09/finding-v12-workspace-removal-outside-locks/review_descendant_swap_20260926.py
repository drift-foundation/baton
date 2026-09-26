"""A pinned root does not pin descendant names after the top-down preflight."""
import os
import unittest
from unittest import mock
from test_removal_outside_the_lock import RemovalOutsideTheLock
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal


class DescendantSwap(RemovalOutsideTheLock):
    def test_descendant_replacement_cannot_delete_outside_material(self):
        self.attempt_roots()
        child = os.path.join(self.storage, "assignment-1", "workspace")
        outside = os.path.join(self.temporary_root(), "review-outside-tree")
        os.mkdir(outside)
        marker = os.path.join(outside, "keep.txt")
        with open(marker, "w") as stream:
            stream.write("outside the authorized tree")
        original = workspaces._thaw
        swapped = []

        def thawing(place):
            if not swapped and str(place).endswith("/workspace"):
                swapped.append(True)
                os.rename(child, outside + ".saved-workspace")
                os.symlink(outside, child)
            return original(place)

        with mock.patch.object(workspaces, "_thaw", side_effect=thawing):
            try:
                workspaces.discard_workspace(self.storage, "assignment-1", control=self.store)
            except (ContractRefusal, OSError):
                pass
        self.assertEqual(swapped, [True])
        self.assertTrue(os.path.isfile(marker), "outside material deleted through replaced descendant")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([DescendantSwap("test_descendant_replacement_cannot_delete_outside_material")])
