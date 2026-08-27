"""Daemon-free regressions for W17110's independent spike review."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[6]
TRIAL = ROOT / "v12" / "spike" / "ping-pong" / "trial.py"
SPEC = importlib.util.spec_from_file_location("w17110_trial", TRIAL)
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)
PREFLIGHT = ROOT / "v12" / "spike" / "ping-pong" / "preflight.py"
PREFLIGHT_SPEC = importlib.util.spec_from_file_location(
    "w17110_preflight", PREFLIGHT)
preflight = importlib.util.module_from_spec(PREFLIGHT_SPEC)
PREFLIGHT_SPEC.loader.exec_module(preflight)


class FakeEngine:
    def __init__(self, *, exit_status=0, remove_status=0,
                 result="pong", reported_pong=True, extra_result=False,
                 ps_status=0, image_list_status=0, overrides=None,
                 image_survives_by_id=False, identity_query_status=None):
        self.exit_status = exit_status
        self.remove_status = remove_status
        self.result = result
        self.reported_pong = reported_pong
        self.extra_result = extra_result
        self.ps_status = ps_status
        self.image_list_status = image_list_status
        self.overrides = overrides or {}
        self.image_survives_by_id = image_survives_by_id
        self.identity_query_status = identity_query_status

    def __call__(self, *arguments, **_ignored):
        if arguments[0] == "run":
            mounts = [arguments[index + 1]
                      for index, value in enumerate(arguments)
                      if value == "--mount"]
            sources = {}
            for mount in mounts:
                fields = dict(field.split("=", 1) for field in mount.split(",")
                              if "=" in field)
                sources[fields["target"]] = fields["source"]
            with open(os.path.join(sources["/input"], "input.json"),
                      encoding="utf-8") as reading:
                correlation = json.load(reading)["correlation_id"]
            with open(os.path.join(sources["/output"], "output.json"), "w",
                      encoding="utf-8") as writing:
                document = {
                    "spike": "w17110-ping-pong",
                    "provider": "claude",
                    "correlation_id": correlation,
                    "started_at": "2026-08-27T00:00:00.000Z",
                    "finished_at": "2026-08-27T00:00:01.000Z",
                    "exit_status": self.exit_status,
                    "result_digest": "sha256:" + hashlib.sha256(
                        self.result.encode("utf-8")).hexdigest(),
                    "result_bytes": len(self.result.encode("utf-8")),
                    "stderr_bytes": 0,
                }
                if self.exit_status != 0:
                    document["failure_category"] = "unrecognized"
                document.update(self.overrides)
                if self.extra_result:
                    document["result"] = self.result
                    document["pong"] = self.reported_pong
                json.dump(document, writing)
            return subprocess.CompletedProcess(arguments, self.exit_status,
                                               b"", b"")
        if arguments[0] == "ps":
            return subprocess.CompletedProcess(arguments, self.ps_status,
                                               b"", b"query refused")
        if arguments[:2] == ("image", "rm"):
            return subprocess.CompletedProcess(arguments, self.remove_status,
                                               b"", b"refused")
        if arguments[:2] == ("image", "ls"):
            return subprocess.CompletedProcess(
                arguments, self.image_list_status, b"", b"query refused")
        if arguments[:2] == ("image", "inspect"):
            status = self.identity_query_status
            if status is None:
                status = 0 if self.image_survives_by_id else 1
                diagnostic = (b"" if status == 0
                              else b"Error: No such image")
            else:
                diagnostic = b"permission denied while connecting to daemon"
            return subprocess.CompletedProcess(
                arguments, status, b"", diagnostic)
        return subprocess.CompletedProcess(arguments, 0, b"", b"")


class TheHostProvesTheTrialRatherThanTrustingIt(unittest.TestCase):
    def run_trial(self, fake, *, remove_staged=True):
        with tempfile.TemporaryDirectory(prefix="w17110-review-") as root:
            credential = os.path.join(root, "credential.json")
            with open(credential, "w", encoding="utf-8") as writing:
                writing.write("review-secret-with-no-recognized-prefix")
            home = os.path.join(root, "staged")
            os.makedirs(home)
            output = io.StringIO()
            cleanup = trial.shutil.rmtree if remove_staged else lambda *_a, **_k: None
            with patch.object(trial, "built", return_value="sha256:image"), \
                    patch.object(trial, "engine", fake), \
                    patch.object(trial.tempfile, "mkdtemp", return_value=home), \
                    patch.object(trial.shutil, "rmtree", cleanup), \
                    contextlib.redirect_stdout(output):
                status = trial.main(["claude", "--credentials", credential])
            return status, json.loads(output.getvalue())

    def test_nonzero_malformed_output_cannot_be_a_satisfying_pong(self):
        status, report = self.run_trial(
            FakeEngine(exit_status=9, result="not pong", reported_pong=True))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["satisfying"])

    def test_arbitrary_agent_output_is_not_copied_to_the_host_report(self):
        secret = "review-secret-with-no-recognized-prefix"
        status, report = self.run_trial(
            FakeEngine(exit_status=1, result=secret, reported_pong=False,
                       extra_result=True))
        self.assertNotIn(secret, json.dumps(report))

    def test_an_unexpected_published_member_refuses_the_result_shape(self):
        status, report = self.run_trial(FakeEngine(extra_result=True))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["satisfying"])

    def test_a_success_shape_cannot_carry_a_failure_category(self):
        status, report = self.run_trial(FakeEngine(overrides={
            "failure_category": "authentication"}))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["verdict"]["closed_result_shape"])

    def test_a_closed_shape_also_holds_its_fact_types(self):
        status, report = self.run_trial(FakeEngine(overrides={
            "result_bytes": "four"}))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["verdict"]["closed_result_shape"])

    def test_an_unhashable_provider_value_is_refused_not_raised(self):
        with self.subTest(value=[]):
            self.assertFalse(trial._closed_shape(
                self.valid_document(provider=[])))

    def valid_document(self, **overrides):
        document = {
            "spike": "w17110-ping-pong",
            "provider": "claude",
            "correlation_id": "w17110-review",
            "started_at": "2026-08-27T00:00:00Z",
            "finished_at": "2026-08-27T00:00:01Z",
            "exit_status": 0,
            "result_digest": trial.EXPECTED_DIGEST,
            "result_bytes": 4,
            "stderr_bytes": 0,
        }
        document.update(overrides)
        return document

    def test_a_staged_root_that_survives_prevents_clean_success(self):
        status, report = self.run_trial(FakeEngine(), remove_staged=False)
        self.assertFalse(report["staged_root_removed"])
        self.assertNotEqual(status, 0)
        self.assertFalse(report["clean"])

    def test_a_refused_image_removal_prevents_clean_success(self):
        status, report = self.run_trial(FakeEngine(remove_status=1))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["clean"])

    def test_a_successful_untag_does_not_prove_image_identity_absent(self):
        status, report = self.run_trial(FakeEngine(
            image_survives_by_id=True))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["clean"])
        self.assertIn("sha256:image", report["images_surviving"])

    def test_a_failed_identity_query_does_not_prove_image_absence(self):
        status, report = self.run_trial(FakeEngine(
            identity_query_status=125))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["image_identity_query_ok"])
        self.assertFalse(report["clean"])

    def test_identity_query_status_one_is_not_uniquely_image_absent(self):
        status, report = self.run_trial(FakeEngine(
            identity_query_status=1))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["image_identity_query_ok"])
        self.assertFalse(report["clean"])

    def test_a_failed_container_cleanup_query_prevents_clean_success(self):
        status, report = self.run_trial(FakeEngine(ps_status=1))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["clean"])

    def test_a_failed_image_cleanup_query_prevents_clean_success(self):
        status, report = self.run_trial(FakeEngine(image_list_status=1))
        self.assertNotEqual(status, 0)
        self.assertFalse(report["clean"])


class PreflightProvesUsabilityRatherThanPresence(unittest.TestCase):
    def test_an_unreadable_nominated_provider_is_not_ready(self):
        with tempfile.TemporaryDirectory(prefix="w17110-preflight-") as root:
            credential = os.path.join(root, "credential.json")
            with open(credential, "w", encoding="utf-8") as writing:
                writing.write("not-opened")
            os.chmod(credential, 0o600)
            output, error = io.StringIO(), io.StringIO()
            with patch.object(preflight, "NOMINATED", credential), \
                    patch.object(preflight, "KNOWN", {}), \
                    patch.object(preflight, "_engine", return_value={
                        "present": True, "client": "docker"}), \
                    patch.object(preflight, "_reachable", return_value={}), \
                    patch.object(preflight, "_observed_readable",
                                 return_value={"probed": True,
                                               "readable": False}), \
                    contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(error):
                status = preflight.main()
            report = json.loads(output.getvalue())
            self.assertFalse(report["credential_providers"]["nominated"]
                             ["readable_by_container_uid"])
            self.assertNotEqual(status, 0)

    def test_observed_file_readability_does_not_override_ancestor_traversal(self):
        with tempfile.TemporaryDirectory(prefix="w17110-preflight-") as root:
            for name in ("claude", "codex"):
                credential = os.path.join(root, name)
                with open(credential, "w", encoding="utf-8") as writing:
                    writing.write("not-opened")
                os.chmod(credential, 0o644)
            os.chmod(root, 0o700)
            output, error = io.StringIO(), io.StringIO()
            with patch.object(preflight, "NOMINATED", root), \
                    patch.object(preflight, "KNOWN", {}), \
                    patch.object(preflight, "_engine", return_value={
                        "present": True, "client": "docker"}), \
                    patch.object(preflight, "_reachable", return_value={}), \
                    patch.object(preflight, "_observed_readable",
                                 return_value={"probed": True,
                                               "readable": True}), \
                    contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(error):
                status = preflight.main()
            report = json.loads(output.getvalue())
            self.assertFalse(report["credential_providers"]["nominated"]
                             ["readable_by_container_uid"])
            self.assertTrue(all(report["credential_providers"]
                                ["usable_per_provider"].values()))
            self.assertNotEqual(status, 0)

    def test_a_probe_that_did_not_run_cannot_fall_back_to_ready(self):
        with tempfile.TemporaryDirectory(prefix="w17110-preflight-") as root:
            for name in ("claude", "codex"):
                credential = os.path.join(root, name)
                with open(credential, "w", encoding="utf-8") as writing:
                    writing.write("not-opened")
                os.chmod(credential, 0o644)
            os.chmod(root, 0o755)
            output, error = io.StringIO(), io.StringIO()
            with patch.object(preflight, "NOMINATED", root), \
                    patch.object(preflight, "KNOWN", {}), \
                    patch.object(preflight, "_engine", return_value={
                        "present": True, "client": "docker"}), \
                    patch.object(preflight, "_reachable", return_value={}), \
                    patch.object(preflight, "_observed_readable",
                                 return_value={"probed": False,
                                               "why": "probe failed"}), \
                    contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(error):
                status = preflight.main()
            report = json.loads(output.getvalue())
            self.assertTrue(all(report["credential_providers"]
                               ["nominated_per_provider"][name]
                               ["readable_by_container_uid"]
                               for name in ("claude", "codex")))
            self.assertNotEqual(status, 0)

    def test_a_provider_directory_needs_traversal_permission(self):
        with tempfile.TemporaryDirectory(prefix="w17110-preflight-") as root:
            provider = os.path.join(root, "provider")
            os.makedirs(provider)
            os.chmod(root, 0o755)
            os.chmod(provider, 0o444)
            self.assertFalse(preflight._readable_by_container(provider))

    def test_a_readable_root_with_unusable_provider_paths_is_not_ready(self):
        with tempfile.TemporaryDirectory(prefix="w17110-preflight-") as root:
            os.chmod(root, 0o755)
            output, error = io.StringIO(), io.StringIO()
            with patch.object(preflight, "NOMINATED", root), \
                    patch.object(preflight, "KNOWN", {}), \
                    patch.object(preflight, "_engine", return_value={
                        "present": True, "client": "docker"}), \
                    patch.object(preflight, "_reachable", return_value={}), \
                    contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(error):
                status = preflight.main()
            report = json.loads(output.getvalue())
            self.assertTrue(report["credential_providers"]["nominated"]
                            ["readable_by_container_uid"])
            self.assertEqual(
                set(report["credential_providers"]["nominated_per_provider"]),
                {"claude", "codex"})
            self.assertNotEqual(status, 0)


if __name__ == "__main__":
    unittest.main()
