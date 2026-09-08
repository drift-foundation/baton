"""Restoration-only offline orchestration checks; no real runtime or source."""
import io
import json
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest import mock
import uuid

import live_controller_restore as candidate
import test_live_diagnostics as prior


class RestorationTests(unittest.TestCase):
    def experiment(self, root, failure=None):
        instances = []
        sessions = {}
        class Fixture:
            def __init__(self, root, name, network, credentials, deadline, workspace=None, session_home=None, session=None, resume=False):
                assert name in ("restored-first", "restored-second")
                assert len(instances) < 2
                if instances:
                    assert instances[0].stopped and instances[0].gate.value["phase"] == "reviewed"
                    assert workspace == instances[0].workspace and session_home == instances[0].session_home
                    assert session == instances[0].session and resume is True
                self.arm = name
                self.resume = resume
                self.session = session or str(uuid.uuid4())
                self.workspace = workspace or root / "workspace"
                if workspace is None:
                    self.workspace.mkdir()
                self.workspace_pin = candidate.base.pin(self.workspace)
                self.session_home = session_home or root / "private-session"
                self.gate = candidate.base.Gate(root / (name + "-gate.json"), dict(arm=name))
                self.stopped = False
                self.turns = []
                self.events = []
                instances.append(self)
            def start(self):
                assert self.resume == (self.arm == "restored-second")
            def event(self, action, **facts): self.events.append(dict(action=action, **facts))
            def process_identity(self): return [self.arm, len(instances), "pinned-start", [1, 2]]
            def turn(self, prompt):
                assert not self.turns
                self.turns.append(prompt)
                assert self.gate.value["phase"] == "attached"
                if failure == self.arm + "-turn":
                    raise candidate.wire.Refusal("provider-result-failed")
                began = time.monotonic_ns()
                if not self.resume:
                    sessions[self.session] = re.search(r"correction: ([0-9a-f]{32})", prompt).group(1)
                    (self.workspace / "solution.py").write_bytes(b"incorrect" if failure == "initial-bytes" else candidate.contract.INITIAL)
                else:
                    assert prompt == candidate.contract.CORRECTION
                    assert sessions[self.session] not in prompt
                    (self.workspace / "solution.py").write_bytes(candidate.contract.CORRECTED)
                    (self.workspace / "continuity.txt").write_text(sessions[self.session] + "\n")
                return began, time.monotonic_ns(), dict(session=self.session, actual_model=candidate.wire.ACTUAL_MODEL)
            def shutdown(self):
                if failure == "first-stop" and not self.resume:
                    raise candidate.wire.Refusal("shutdown-unconfirmed")
                self.stopped = True
                return self.gate.stopped(dict(container_stopped=True))
            def detach(self):
                assert self.resume  # Initial result must use confirmed-stop custody.
                self.gate.intent()
                return self.gate.revoked(dict(mount_absent=True))
            def consume(self, receipt, token, corrected):
                self.gate.consume(receipt)
                files = candidate.read_artifacts(self.workspace, self.workspace_pin)
                candidate.require(candidate.contract.verify(files, token, corrected), "artifact-verification-failed")
                return True
            def finish(self): pass
        with mock.patch.object(candidate, "Fixture", Fixture), mock.patch.object(candidate.time, "sleep"), \
                mock.patch.object(candidate.contract, "comparable", side_effect=AssertionError("No matched pair is permitted")):
            result = candidate.execute_restoration(root, "network", object(), time.monotonic() + 420, instances_for_cleanup := [])
        self.assertEqual(instances_for_cleanup, instances)
        return result, instances

    def test_two_turn_restoration_with_real_fixed_byte_verifier_and_no_retained_arm(self):
        with tempfile.TemporaryDirectory() as directory:
            result, fixtures = self.experiment(Path(directory))
            self.assertEqual([f.arm for f in fixtures], ["restored-first", "restored-second"])
            self.assertEqual([len(f.turns) for f in fixtures], [1, 1])
            self.assertTrue(all(f.stopped for f in fixtures))
            self.assertEqual(result["outcome"], "restored-only-passed")
            self.assertFalse(result["matched_comparison"])
            self.assertEqual(set(result["arms"]), {"restored"})
            self.assertIn("end_to_verified_correction_ns", result["restoration_timings"])
            self.assertNotIn("timings", result)

    def test_first_turn_stop_or_artifact_failure_prevents_replacement(self):
        for failure in ("restored-first-turn", "first-stop", "initial-bytes"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(candidate.wire.Refusal):
                    self.experiment(root, failure)
                self.assertFalse((root / "restored-second-gate.json").exists())

    def test_restored_turn_failure_preserves_first_verified_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(candidate.wire.Refusal):
                self.experiment(root, "restored-second-turn")
            row = json.loads((root / "arms.json").read_text())["restored"]
            self.assertTrue(row["first_artifact_verified"])
            self.assertTrue(row["old_container_shutdown_confirmed"])
            self.assertNotIn("correction_verified", row)

    def test_restoration_acceptance_rejects_missing_identity_custody_or_clock_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result, _ = self.experiment(Path(directory))
        row = result["arms"]["restored"]
        changes = (("first_artifact_verified", False), ("correction_verified", False),
            ("consumption_receipts_verified", False), ("old_container_shutdown_confirmed", False),
            ("final_shutdown_confirmed", False), ("workspace_after", [0, 0]),
            ("session_after", str(uuid.uuid4())), ("resume_requested", str(uuid.uuid4())),
            ("process_after", row["process_before"]), ("actual_model", "different"),
            ("review_ready_ns", row["verified_correction_ns"] + 1))
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(candidate.wire.Refusal):
                candidate.verify_restoration(dict(row, **{key: value}))

    def test_host_and_initialized_supervisor_refuse_second_turn(self):
        helper = prior.DiagnosticsTests()
        with tempfile.TemporaryDirectory() as directory:
            fixture = helper.fixture(Path(directory))
            fixture.turn("one")
            before = fixture.link.stdin.getvalue()
            with self.assertRaisesRegex(candidate.wire.Refusal, "user-turn-limit"):
                fixture.turn("two")
            self.assertEqual(fixture.link.stdin.getvalue(), before)
        supervisor = candidate.wire.Supervisor()
        # Exercise actual initialization through its budget binding, stopping at
        # deadline validation before filesystem, credential or process activity.
        with self.assertRaisesRegex(candidate.wire.Refusal, "overall-deadline"):
            supervisor.initialize(dict(arm="restored-first", session=prior.SESSION, resume=False, deadline=float("inf")))
        self.assertEqual(supervisor.limit, 1)
        supervisor.identity = mock.Mock()
        supervisor.turns = 1
        supervisor.send = mock.Mock()
        with self.assertRaisesRegex(candidate.wire.Refusal, "user-turn-limit"):
            supervisor.turn(dict(prompt="two"))
        supervisor.send.assert_not_called()


if __name__ == "__main__":
    # Preserve prior assertions; exercise the signed-off diagnostic expectations
    # unchanged against the runnable restored-only sources.
    prior.host = candidate
    prior.worker = candidate.wire
    suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromModule(prior),
                               unittest.defaultTestLoader.loadTestsFromTestCase(RestorationTests)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
