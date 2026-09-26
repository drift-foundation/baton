"""Exercise mount refusal at the current retained-handle observation boundary."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from test_removal_outside_the_lock import RemovalOutsideTheLock


class HandleMounts(RemovalOutsideTheLock):
    def prepared(self):
        roots = self.attempt_roots()
        home = os.path.dirname(roots["inputs"])
        nested = os.path.join(home, "foreign")
        os.mkdir(nested)
        marker = os.path.join(nested, "keep")
        with open(marker, "w") as stream:
            stream.write("foreign material")
        return home, nested, marker

    def refused_without_effects(self, marker):
        with mock.patch.object(workspaces, "_thaw_handle") as thaw:
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertEqual(caught.exception.category, "policy")
        thaw.assert_not_called()
        self.assertTrue(os.path.isfile(marker))

    def test_descendant_cross_device_refuses_before_effects(self):
        home, nested, marker = self.prepared()
        foreign = os.stat(nested)
        honest = os.fstat
        observed = []

        def foreign_device(handle):
            value = honest(handle)
            if (value.st_dev, value.st_ino) == (foreign.st_dev, foreign.st_ino):
                observed.append(handle)
                return os.stat_result(tuple(value)[:2] + (value.st_dev + 1,) + tuple(value)[3:])
            return value

        with mock.patch.object(os, "fstat", side_effect=foreign_device):
            self.refused_without_effects(marker)
        self.assertTrue(observed)

    def test_root_mount_table_refuses_before_effects(self):
        home, nested, marker = self.prepared()
        with mock.patch.object(workspaces, "mount_points", return_value={home}):
            self.refused_without_effects(marker)

    def test_descendant_same_device_mount_refuses_before_effects(self):
        home, nested, marker = self.prepared()
        with mock.patch.object(workspaces, "mount_points", return_value={nested}):
            self.refused_without_effects(marker)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(HandleMounts(name) for name in (
        "test_descendant_cross_device_refuses_before_effects",
        "test_root_mount_table_refuses_before_effects",
        "test_descendant_same_device_mount_refuses_before_effects"))
