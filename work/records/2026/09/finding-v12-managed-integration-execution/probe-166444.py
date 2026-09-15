"""Desired strict limits contract and group-observation checks, no real signals."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from tests.manager.test_reconciliation_task import task, _request, _owned
from baton_v12.integration import managed_execution
from baton_v12.contracts import ContractRefusal

class Contracts(unittest.TestCase):
    def test_equal_numeric_values_do_not_replace_integer_types(self):
        for field in ("compatibility_generation", "seconds", "default_seconds"):
            with self.subTest(field=field):
                value = _request()
                limits = value["execution_limits"]
                if field == "compatibility_generation":
                    limits[field] = float(limits[field])
                else:
                    boundary = limits["boundaries"][sorted(limits["boundaries"])[0]]
                    boundary[field] = float(boundary[field])
                with self.assertRaises(ContractRefusal):
                    managed_execution.adopt_preparation_request(value)
                with tempfile.TemporaryDirectory(prefix="w166444-types-") as root:
                    (Path(root) / task.REQUEST_NAME).write_text(json.dumps(value))
                    with self.assertRaises(task.PreparationRefusal):
                        task.read_request(root, owned=_owned())

    def test_reaped_leader_still_requires_group_observation(self):
        child = Mock(pid=765432)
        child.poll.return_value = 0
        with patch.object(task.os, "killpg") as signal_group, \
             patch.object(task, "_group_is_gone", side_effect=[False, True]) as gone, \
             patch.object(task.time, "sleep"):
            task._exclude(child, 765432, "not excluded")
        self.assertEqual(gone.call_count, 2)
        signal_group.assert_called_with(765432, task.signal.SIGTERM)

if __name__ == "__main__":
    unittest.main(verbosity=2)
