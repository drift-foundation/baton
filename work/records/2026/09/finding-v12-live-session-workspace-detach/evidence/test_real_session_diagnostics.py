"""Additive offline checks for W106673 diagnostic transport; no Docker/Claude."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import real_session_preflight_diagnostic as probe


class DiagnosticsTests(unittest.TestCase):
    def test_identity_failure_reaches_inside_output(self):
        with mock.patch.object(probe.os, "geteuid", return_value=1000):
            answer, code = probe.inside_result()
        self.assertEqual(code, 1)
        self.assertEqual(answer, dict(outcome="offline-transport-preflight-failed",
            stage="identity", reason="wrong-probe-identity", child_exit_code=None, os_errno=None))

    def test_missing_executable_reports_stage_errno_without_filename(self):
        error = FileNotFoundError(2, "secret diagnostic", "/secret/provider-path")
        with mock.patch.object(probe.os, "geteuid", return_value=65532), \
             mock.patch.object(probe.os, "getpid", return_value=1), \
             mock.patch.object(probe.Path, "mkdir"), \
             mock.patch.object(probe.subprocess, "Popen", side_effect=error):
            answer, code = probe.inside_result()
        self.assertEqual(code, 1)
        self.assertEqual(answer["stage"], "version-command")
        self.assertEqual(answer["reason"], "path-not-found")
        self.assertEqual(answer["os_errno"], 2)
        self.assertNotIn("secret", json.dumps(answer))

    def test_version_and_flag_checks_remain_failures(self):
        for values, stage, reason in (
                ([b"wrong version\n"], "version-check", "wrong-cli-version"),
                ([(probe.VERSION + "\n").encode(), b"--print\n"], "help-check", "required-flag-absent")):
            with self.subTest(stage=stage), \
                 mock.patch.object(probe.os, "geteuid", return_value=65532), \
                 mock.patch.object(probe.os, "getpid", return_value=1), \
                 mock.patch.object(probe.Path, "mkdir"), \
                 mock.patch.object(probe, "captured", side_effect=values):
                answer, code = probe.inside_result()
            self.assertEqual(code, 1)
            self.assertEqual((answer["stage"], answer["reason"]), (stage, reason))

    def test_child_nonzero_exit_survives_command_failure(self):
        child = mock.Mock()
        child.stdout.fileno.return_value = 123
        child.wait.return_value = 7
        child.poll.return_value = 7
        diagnostics = {"stage": "version-command"}
        with mock.patch.object(probe.subprocess, "Popen", return_value=child), \
             mock.patch.object(probe.select, "select", return_value=([child.stdout], [], [])), \
             mock.patch.object(probe.os, "read", side_effect=[b"secret stdout", b""]):
            with self.assertRaises(probe.ProbeFailure) as caught:
                probe.captured([probe.CLI, "--version"], diagnostics)
        answer = probe.failure(caught.exception, diagnostics)
        self.assertEqual(answer["reason"], "command-failed")
        self.assertEqual(answer["child_exit_code"], 7)
        self.assertNotIn("secret", json.dumps(answer))
        child.kill.assert_not_called()

    def test_exception_messages_and_timeout_output_are_never_exported(self):
        for error, reason in (
                (RuntimeError("secret arbitrary exception"), "unexpected-error"),
                (PermissionError(13, "secret", "/credential"), "permission-denied"),
                (subprocess.TimeoutExpired(["secret command"], 1, output=b"secret output",
                                           stderr=b"secret stderr"), "timeout")):
            with self.subTest(reason=reason):
                answer = probe.failure(error, {"stage": "stream-start"})
                self.assertEqual(answer["reason"], reason)
                self.assertNotIn("secret", json.dumps(answer))
                self.assertNotIn("credential", json.dumps(answer))

    def test_partial_malformed_and_wrong_correlation_are_distinguishable(self):
        for callable_, reason in (
            (lambda: probe.Frames().feed(b'{"secret":broken}\n'), "invalid-json"),
            (lambda: probe.initialized({"type": "control_response", "response": {
                "request_id": "wrong", "subtype": "success", "secret": "hidden"}}, "pin"),
             "wrong-control-correlation"),
            (lambda: probe.initialized({"type": "control_response", "response": {
                "request_id": "pin", "subtype": "error", "error": "secret"}}, "pin"),
             "initialization-refused")):
            with self.subTest(reason=reason):
                with self.assertRaises(probe.ProbeFailure) as caught:
                    callable_()
                answer = probe.failure(caught.exception, {"stage": "initialize-read"})
                self.assertEqual(answer["reason"], reason)
                self.assertNotIn("secret", json.dumps(answer))

    def test_failure_projection_refuses_untrusted_text_and_non_numeric_status(self):
        valid = probe.failure(probe.ProbeFailure("command-failed"), {
            "stage": "version-command", "child_exit_code": 7})
        self.assertEqual(probe.checked_failure(valid), valid)
        for changes in ({"reason": "secret"}, {"stage": "secret"}, {"child_exit_code": "secret"},
                        {"os_errno": True}, {"unexpected": "secret"}):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(probe.ProbeFailure, "invalid-probe-diagnostic"):
                    probe.checked_failure(dict(valid, **changes))

    def test_docker_start_nonzero_retains_only_bounded_bytes_for_projection(self):
        completed = subprocess.CompletedProcess(["docker"], 1, b'{"inside":"secret"}')
        with mock.patch.object(probe.subprocess, "run", return_value=completed):
            self.assertEqual(probe.docker("start", "--attach", "id", allow_exit=True),
                             (completed.stdout, 1))
            with self.assertRaises(probe.ProbeFailure) as caught:
                probe.docker("inspect", "id")
        self.assertEqual(probe.failure(caught.exception, {"stage": "image-check"})["child_exit_code"], 1)
        self.assertNotIn("secret", str(caught.exception))

    def run_operator(self, answer, *, exit_code=1, cleanup_error=None):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            container = "a" * 64
            def fake_docker(*args, **kwargs):
                calls.append((args, kwargs))
                if args[:2] == ("image", "inspect"):
                    return json.dumps([{"Id": probe.IMAGE, "Config": {}}]).encode()
                if args[0] == "create":
                    return container.encode()
                if args[0] == "start":
                    self.assertTrue(kwargs["allow_exit"])
                    return json.dumps(answer).encode(), exit_code
                raise AssertionError("unexpected Docker operation")
            found = {"State": {"Running": False, "Pid": 0, "ExitCode": exit_code}}
            checks = [found, cleanup_error or found, found]
            with mock.patch.object(probe.tempfile, "mkdtemp", return_value=directory), \
                 mock.patch.object(probe.os, "umask"), \
                 mock.patch.object(probe, "docker", side_effect=fake_docker), \
                 mock.patch.object(probe, "checked_container", side_effect=checks), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                code = probe.operator()
            result = json.loads((Path(directory)/"result.json").read_text())
            self.assertNotIn("secret", output.getvalue())
            self.assertFalse(any(args[0] in ("rm", "run") for args, kwargs in calls))
            return result, code

    def test_inside_failure_survives_nonzero_docker_exit_and_host_cleanup(self):
        inner = probe.failure(probe.ProbeFailure("command-failed"), {
            "stage": "help-command", "child_exit_code": 9})
        result, code = self.run_operator(inner)
        self.assertEqual(code, 1)
        self.assertEqual(result["probe"], inner)
        self.assertEqual(result["docker_exit_code"], 1)
        self.assertEqual(result["container_exit_code"], 1)
        self.assertEqual(result["failure"]["reason"], "inside-probe-failed")
        self.assertEqual(result["cleanup"], "confirmed-stopped-retained")

    def test_host_rejects_malformed_diagnostic_without_echo(self):
        result, code = self.run_operator({"outcome": "offline-transport-preflight-failed",
                                        "reason": "secret"})
        self.assertEqual(code, 1)
        self.assertNotIn("probe", result)
        self.assertEqual(result["failure"]["reason"], "invalid-probe-diagnostic")
        self.assertNotIn("secret", json.dumps(result))

    def test_cleanup_failure_does_not_overwrite_original_inside_failure(self):
        inner = probe.failure(probe.ProbeFailure("wrong-probe-identity"), {"stage": "identity"})
        result, code = self.run_operator(inner, cleanup_error=RuntimeError("secret cleanup"))
        self.assertEqual(code, 1)
        self.assertEqual(result["probe"], inner)
        self.assertEqual(result["failure"]["reason"], "inside-probe-failed")
        self.assertEqual(result["cleanup_failure"]["reason"], "unexpected-error")
        self.assertEqual(result["cleanup"], "unconfirmed-operator-inspection-required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
