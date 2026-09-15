"""Review diagnostic. Mocked supervisor edges; no descendant is launched."""
import contextlib
import importlib.util
import io
import itertools
import json
import pathlib
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests.tools import test_managed_preparation


class SupervisorDiagnostic(unittest.TestCase):
    def test_leader_completion_skips_kill_for_remaining_group(self):
        spec = importlib.util.spec_from_file_location("reviewed_runner", "/tmp/w166281_run.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        signals = []
        child = mock.Mock(pid=123456, returncode=-signal.SIGTERM)
        child.communicate.side_effect = [subprocess.TimeoutExpired("fixture", 3), (b"leader ended", b"")]
        clock = itertools.count()
        with tempfile.TemporaryDirectory(prefix="w161230-review-supervisor-") as directory:
            ledger = pathlib.Path(directory) / "ledger.json"
            ledger.write_text(json.dumps({"runs": []}))
            with mock.patch.object(runner, "DOSSIER", directory), mock.patch.object(runner, "LEDGER", str(ledger)), mock.patch.object(runner.subprocess, "Popen", return_value=child), mock.patch.object(runner.os, "killpg", side_effect=lambda pid, sig: signals.append(sig)), mock.patch.object(runner.time, "perf_counter", side_effect=lambda: next(clock)), mock.patch.object(runner.time, "sleep"), contextlib.redirect_stderr(io.StringIO()):
                code = runner.main(["1", "mocked-leader-first", "unused-fixture"])
            row = json.loads(ledger.read_text())["runs"][0]
        self.assertEqual(code, 1)
        self.assertTrue(row["timed_out"])
        self.assertFalse(row["group_proved_gone"])
        self.assertEqual([sig for sig in signals if sig], [signal.SIGTERM])
        self.assertNotIn(signal.SIGKILL, signals)
        print("OBSERVED mocked remaining group: TERM only, KILL skipped, group_proved_gone=False; failure recorded", flush=True)


suite = unittest.TestSuite([
    test_managed_preparation.TheResolverCallsItsOwnersCorrectly("test_a_malformed_selection_refuses_at_STATIC_PREFLIGHT"),
    SupervisorDiagnostic("test_leader_completion_skips_kill_for_remaining_group"),
])
sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
