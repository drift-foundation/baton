"""Additive mocked tests for help observation versus actual initialization."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import real_session_preflight_help as probe


class HelpTests(unittest.TestCase):
    def flags(self):
        return {flag: flag not in ("--max-turns", "--max-budget-usd") for flag in probe.FLAGS}

    def test_exact_map_and_missing_names_survive_failure(self):
        flags = self.flags()
        answer = probe.failure(probe.ProbeFailure("initialization-timeout"),
                               {"stage": "initialize-read", "flags": flags})
        self.assertEqual(answer["flags"], flags)
        self.assertEqual(answer["missing_help_flags"], ["--max-turns", "--max-budget-usd"])
        self.assertEqual(answer["unexercised_flags"], list(probe.UNEXERCISED_FLAGS))
        self.assertEqual(probe.checked_failure(answer), answer)

    def test_pre_help_failure_distinguishes_unobserved_from_missing(self):
        answer = probe.failure(FileNotFoundError(2, "secret"), {"stage": "version-command"})
        self.assertIsNone(answer["flags"])
        self.assertIsNone(answer["missing_help_flags"])
        self.assertNotIn("secret", json.dumps(answer))

    def test_unknown_names_types_and_inconsistent_missing_list_refuse(self):
        valid = probe.failure(probe.ProbeFailure("command-failed"), {
            "stage": "initialize-read", "flags": self.flags()})
        for changes in (
                {"flags": dict(self.flags(), secret=True)},
                {"flags": dict(self.flags(), **{"--print": 1})},
                {"missing_help_flags": ["secret"]},
                {"missing_help_flags": []},
                {"unexercised_flags": []}):
            with self.subTest(changes=changes), self.assertRaises(probe.ProbeFailure):
                probe.checked_failure(dict(valid, **changes))

    def inside_fixture(self, successful):
        # Missing help names here are synthetic test input, never a claim about
        # the installed image. All provider/process operations are mocked.
        help_text = "\n".join(flag for flag, seen in self.flags().items() if seen).encode()
        child = mock.Mock()
        child.pid = 123
        child.stdout.fileno.return_value = 17
        child.poll.return_value = None
        child.wait.return_value = -15
        # process stat has twenty suffix fields; process start is index19.
        stat = "123 (claude) " + " ".join(["S"] + ["0"] * 18 + ["12345"])
        diagnostics = {}
        record = {"type": "control_response", "response": {
            "request_id": "pin", "subtype": "success"}}
        with mock.patch.object(probe.os, "geteuid", return_value=65532), \
             mock.patch.object(probe.os, "getpid", return_value=1), \
             mock.patch.object(probe.Path, "mkdir"), \
             mock.patch.object(probe, "captured", side_effect=[
                 (probe.VERSION + "\n").encode(), help_text]), \
             mock.patch.object(probe.subprocess, "Popen", return_value=child) as spawn, \
             mock.patch.object(probe.os, "pidfd_open", return_value=23), \
             mock.patch.object(probe.os, "close"), \
             mock.patch.object(probe.Path, "read_text", return_value=stat), \
             mock.patch.object(probe.uuid, "uuid4", return_value=mock.Mock(hex="pin")), \
             mock.patch.object(probe.select, "select", side_effect=[
                 ([child.stdout], [], []), ([], [], [])]), \
             mock.patch.object(probe.os, "read", return_value=(
                 (json.dumps(record)+"\n").encode() if successful else b"")):
            if successful:
                result = probe.inside(diagnostics)
            else:
                with self.assertRaises(probe.ProbeFailure) as caught:
                    probe.inside(diagnostics)
                result = probe.failure(caught.exception, diagnostics)
        self.assertEqual(spawn.call_count, 1)
        self.assertIn("--input-format", spawn.call_args.args[0])
        return result

    def test_help_omission_does_not_prevent_real_initialize_path(self):
        result = self.inside_fixture(True)
        self.assertEqual(result["outcome"], "offline-transport-preflight-passed")
        self.assertTrue(result["initialized"])
        self.assertEqual(result["missing_help_flags"], ["--max-turns", "--max-budget-usd"])
        self.assertEqual(result["unexercised_flags"], list(probe.UNEXERCISED_FLAGS))
        self.assertEqual(result["session_continuity"], "unproved")
        self.assertEqual(result["restore"], "unproved")
        self.assertEqual(result["real_turns"], 0)

    def test_help_omission_never_converts_initialize_failure_to_success(self):
        result = self.inside_fixture(False)
        self.assertEqual(result["outcome"], "offline-transport-preflight-failed")
        self.assertEqual(result["reason"], "cli-exited-before-initialization")
        self.assertEqual(result["stage"], "initialize-read")
        self.assertEqual(result["missing_help_flags"], ["--max-turns", "--max-budget-usd"])

    def test_failed_per_flag_observations_survive_host_exit1(self):
        inner = probe.failure(probe.ProbeFailure("initialization-timeout"),
                              {"stage": "initialize-read", "flags": self.flags()})
        with tempfile.TemporaryDirectory() as root:
            def docker(*args, **kwargs):
                if args[:2] == ("image", "inspect"):
                    return json.dumps([{"Id": probe.IMAGE, "Config": {}}]).encode()
                if args[0] == "create":
                    return ("a"*64).encode()
                if args[0] == "start":
                    return json.dumps(inner).encode(), 1
                raise AssertionError("unexpected runtime call")
            with mock.patch.object(probe, "docker", side_effect=docker), \
                 mock.patch.object(probe, "checked_container", return_value={
                     "State": {"Running": False, "Pid": 0, "ExitCode": 1}}), \
                 mock.patch.object(probe.tempfile, "mkdtemp", return_value=root), \
                 mock.patch.object(probe.os, "umask"), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.operator(), 1)
            result = json.loads((Path(root)/"result.json").read_text())
        self.assertEqual(result["probe"], inner)
        self.assertEqual(result["docker_exit_code"], 1)
        self.assertEqual(result["container_exit_code"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
