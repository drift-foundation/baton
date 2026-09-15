"""Independent supervisor interruption observations; all process/Docker boundaries fake."""
import signal
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tests.manager import test_runtime_deadline_engine_budget as candidate

gate = candidate.gate


class Observations(candidate.EngineBudget):
    def test_leader_reap_does_not_prove_owned_session_stopped(self):
        class Leader:
            pid = 12345
            terminated = False
            descendant_alive = True

            def wait(inner, timeout):
                if inner.terminated:
                    return -15
                self.clock.now += timeout
                raise subprocess.TimeoutExpired("leader", timeout)

        leader = Leader()

        def killpg(pid, sig):
            self.assertEqual(pid, leader.pid)
            leader.terminated = True
            if sig == signal.SIGKILL:
                leader.descendant_alive = False

        with mock.patch.object(gate.subprocess, "Popen", return_value=leader), mock.patch.object(gate.os, "killpg", side_effect=killpg) as signals:
            self.process = gate.OwnedProcess(["fake-child"])
            result = self.run_gate()
        self.assertEqual([call.args[1] for call in signals.call_args_list], [signal.SIGTERM])
        self.assertTrue(leader.descendant_alive)
        self.assertEqual(set(result["cleanup"]["resolved"]), set(self.names))
        self.assertEqual(result["reap_errors"], [])
        print("OBSERVED: leader wait returned after TERM; surviving owned descendant was not stopped, yet container cleanup ran")

    def test_partial_call_record_prevents_all_cleanup_despite_valid_names(self):
        def factory(command, **kwargs):
            process = self.factory(command, **kwargs)
            (self.root / "child-call-1.json").write_text("{")
            process.code = 1
            return process

        result = self.run_gate(factory)
        self.assertFalse(result["ok"])
        self.assertEqual(set(self.inventory.names()), set(self.names))
        self.assertIsNone(result["cleanup"]["unresolved"])
        self.assertIn("JSONDecodeError", result["cleanup"]["errors"][0])
        self.assertFalse(any(command[1] == "rm" for command, _, _ in self.docker.commands))
        self.assertTrue(set(self.names).issubset(self.docker.live))
        print("OBSERVED: interrupted in-place call-record rewrite disables every cleanup attempt despite valid durable inventory")

    def test_last_accounting_write_can_overrun_and_still_report_success(self):
        original = gate.durable

        def durable(path, value, **kwargs):
            original(path, value, **kwargs)
            if Path(path).name == "result.json" and not kwargs.get("exclusive"):
                self.clock.now += 181

        with mock.patch.object(gate, "durable", side_effect=durable):
            result = self.run_gate()
        self.assertTrue(result["ok"])
        self.assertGreater(self.clock() - 1000, 180)
        self.assertLess(result["elapsed"], 180)
        print("OBSERVED: final durable write time is omitted; returned success exceeds absolute180s")


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromModule(candidate)
    for name in sorted(Observations.__dict__):
        if name.startswith("test_"):
            suite.addTest(Observations(name))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
