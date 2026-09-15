"""Independent desired contracts; deterministic local fixtures, no child workloads."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.manager.test_reconciliation_task import task, _request
from baton_v12.integration import managed_execution
from baton_v12.contracts import ContractRefusal


class RequiredContracts(unittest.TestCase):
    def read(self, value):
        with tempfile.TemporaryDirectory(prefix="w166235-request-") as root:
            (Path(root) / task.REQUEST_NAME).write_text(json.dumps(value))
            return task.read_request(root)

    def test_missing_request_identity_refuses_in_both(self):
        value = _request()
        del value["job_id"]
        with self.assertRaises(ContractRefusal):
            managed_execution.adopt_preparation_request(value)
        with self.assertRaises(task.PreparationRefusal):
            self.read(value)

    def test_resolved_limits_agree_with_manager(self):
        for change in ("units", "generation", "seconds"):
            with self.subTest(change=change):
                value = _request()
                limits = value["execution_limits"]
                if change == "units":
                    limits["units"] = "minutes"
                elif change == "generation":
                    limits["compatibility_generation"] = 999
                else:
                    name = sorted(limits["boundaries"])[0]
                    limits["boundaries"][name]["seconds"] += 1
                with self.assertRaises(ContractRefusal):
                    managed_execution.adopt_preparation_request(value)
                with self.assertRaises(task.PreparationRefusal):
                    self.read(value)

    def test_measure_refuses_symlink_entry(self):
        with tempfile.TemporaryDirectory(prefix="w166235-tree-") as root:
            (Path(root) / "data").write_text("candidate")
            (Path(root) / "link").symlink_to("data")
            with self.assertRaises(task.PreparationRefusal):
                task.measure(root)

    def test_no_follow_request_rejects_symlink_root(self):
        with tempfile.TemporaryDirectory(prefix="w166235-root-") as root:
            real = Path(root) / "real"
            real.mkdir()
            (real / task.REQUEST_NAME).write_text(json.dumps(_request()))
            link = Path(root) / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(task.PreparationRefusal):
                task.read_request(str(link))

    def test_no_follow_measure_rejects_symlink_root(self):
        with tempfile.TemporaryDirectory(prefix="w166235-root-") as root:
            real = Path(root) / "real"
            real.mkdir()
            (real / "data").write_text("candidate")
            link = Path(root) / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(task.PreparationRefusal):
                task.measure(str(link))

    def test_failed_phase_is_separate_from_not_run_suffix(self):
        with tempfile.TemporaryDirectory(prefix="w166235-sequence-") as root:
            states = {}
            for name in task.CAUSAL_ORDER:
                place = Path(root) / name
                place.mkdir()
                (place / task.HARNESS_NAME).write_text("pass\n")
                states[name] = {"path": str(place), "revision": "a" * 40}
            with patch.object(task, "run_bounded", side_effect=[
                {"status": 0, "tag": None, "output": ""},
                {"status": None, "tag": "timeout", "output": "timed out"},
            ]):
                completed, not_run, tag, phase, measured = task.observe(_request(), states, 1)
            self.assertEqual([row["name"] for row in completed], ["combined"])
            self.assertEqual((tag, phase, not_run), ("timeout", "base", ["isolated"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
