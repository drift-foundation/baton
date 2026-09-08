"""Offline turn-boundary and redaction regressions; no live runtime inputs."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

import live_controller_diagnostic as host
import live_supervisor_diagnostic as worker

SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CANARY = "PRIVATE-PROMPT-PROVIDER-CREDENTIAL-CANARY"


class DiagnosticsTests(unittest.TestCase):
    def fixture(self, root):
        value = host.Fixture.__new__(host.Fixture)
        value.directory = root
        value.events = []
        value.arm = "restored-first"
        value.resume = False
        value.active_turn = 0
        value.operation = "start"
        value.live_stage = "created"
        value.last_failure = None
        value.outer_operation = "start"
        value.session = SESSION
        value.deadline = time.monotonic() + 30
        value.link = SimpleNamespace(stdin=io.BytesIO())
        value.identity = mock.Mock()
        value.quiescent = mock.Mock()
        value.reader = mock.Mock()
        value.reader.next.side_effect = lambda *_: self.response()
        return value

    def response(self):
        return dict(event="complete", session=SESSION, actual_model=worker.ACTUAL_MODEL,
                    cli_version=worker.VERSION, cli_pid=13, cli_start="123", completed_ns=time.monotonic_ns(),
                    num_turns=2, reported_cost_usd=0.01)

    def stages(self, fixture):
        return [event["stage"] for event in fixture.events if event["action"] == "turn-boundary"]

    def test_failure_before_write_has_intent_but_no_write_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.identity.side_effect = worker.Refusal("container-not-current")
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertIn("turn-intent", self.stages(fixture))
            self.assertNotIn("command-write-completed", self.stages(fixture))
            self.assertEqual(fixture.last_failure["refusal_code"], "container-not-current")
            self.assertNotIn(CANARY, json.dumps(fixture.events))

    def test_partial_host_write_never_becomes_completed_write(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.link.stdin = mock.Mock()
            fixture.link.stdin.write.return_value = 1
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertIn("command-write-intent", self.stages(fixture))
            self.assertNotIn("command-write-completed", self.stages(fixture))
            self.assertEqual(fixture.last_failure["refusal_code"], "host-write-incomplete")

    def test_failure_after_write_has_no_response_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.reader.next.side_effect = worker.Refusal("stream-timeout")
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertIn("command-write-completed", self.stages(fixture))
            self.assertNotIn("response-observed", self.stages(fixture))
            self.assertEqual(fixture.last_failure["refusal_code"], "stream-timeout")

    def test_untrusted_response_observed_before_shape_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.reader.next.side_effect = lambda *_: dict(self.response(), arbitrary=CANARY)
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertIn("response-observed", self.stages(fixture))
            self.assertNotIn("post-response-validation", self.stages(fixture))
            self.assertNotIn(CANARY, json.dumps(fixture.events))

    def test_failure_after_response_preserves_boundary_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.reader.next.side_effect = lambda *_: dict(self.response(), session=str(uuid.uuid4()))
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertIn("response-observed", self.stages(fixture))
            self.assertEqual(fixture.last_failure["stage"], "post-response-validation")
            self.assertEqual(fixture.last_failure["refusal_code"], "turn-runtime-identity")
            self.assertNotIn("turn-complete", [e["action"] for e in fixture.events])

    def test_post_turn_quiescence_failure_does_not_hide_response(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.quiescent.side_effect = [None, worker.Refusal("unexpected-idle-process-tree")]
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertEqual(fixture.last_failure["stage"], "post-turn-quiescence")
            self.assertIn("response-observed", self.stages(fixture))
            milestones = host.observed_milestones([fixture], {"outcome": "failed-or-inconclusive"})
            self.assertEqual(milestones["host_turn_writes_observed"], 1)
            self.assertEqual(milestones["validated_turn_completions"], 0)
            self.assertFalse(milestones["matched_pair_verified"])

    def test_successful_turn_records_actual_model_and_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.turn(CANARY)
            milestones = host.observed_milestones([fixture], {"outcome": "failed-or-inconclusive"})
            self.assertEqual(milestones["validated_turn_completions"], 1)
            self.assertEqual(milestones["actual_models"], [worker.ACTUAL_MODEL])
            text = json.dumps(host.runtime_limitations(milestones))
            self.assertNotIn("Preparation only", text)
            self.assertIn("No matched comparison", text)

    def supervisor(self, frames):
        value = worker.Supervisor()
        value.arm = "restored-first"
        value.operation = "turn"
        value.session = SESSION
        value.limit = 2
        value.deadline = time.monotonic() + 30
        value.identity = mock.Mock(return_value=dict(cli_pid=13, cli_start="123", session=SESSION,
                    actual_model=worker.ACTUAL_MODEL, cli_version=worker.VERSION))
        value.process = SimpleNamespace(stdin=io.BytesIO())
        value.lines = mock.Mock(buffer=b"")
        value.lines.next.side_effect = frames
        return value

    def test_supervisor_partial_write_and_after_write_failure(self):
        for partial in (True, False):
            supervisor = self.supervisor(worker.Refusal("stream-timeout"))
            if partial:
                supervisor.process.stdin = mock.Mock()
                supervisor.process.stdin.write.return_value = 1
            output = io.StringIO()
            with contextlib.redirect_stdout(output), self.assertRaises(worker.Refusal):
                supervisor.turn(dict(prompt=CANARY))
            stages = [json.loads(line)["stage"] for line in output.getvalue().splitlines()]
            self.assertIn("provider-write-intent", stages)
            self.assertEqual("provider-write-completed" in stages, not partial)
            self.assertNotIn("provider-response-observed", stages)
            self.assertNotIn(CANARY, output.getvalue())

    def test_provider_failed_result_is_observed_before_refusal(self):
        supervisor = self.supervisor([dict(type="assistant", message=CANARY),
            dict(type="result", subtype="success", is_error=True, session_id=SESSION, result=CANARY)])
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(worker.Refusal) as failure:
            supervisor.turn(dict(prompt=CANARY))
        stages = [json.loads(line)["stage"] for line in output.getvalue().splitlines()]
        self.assertEqual(stages[-2:], ["provider-response-observed", "provider-result-validation"])
        self.assertEqual(worker.refusal_projection(failure.exception)["refusal_code"], "provider-result-failed")
        self.assertNotIn(CANARY, output.getvalue())

    def test_supervisor_refusal_before_turn_increment_is_correlated(self):
        frame = dict(event="refused", arm="restored-first", operation="turn", turn=0,
                     stage="command-validation", refusal_code="cli-exited", exception_kind="fixture-refusal", errno=None)
        self.assertEqual(host.diagnostic_frame(frame, "restored-first", "turn", 1), frame)
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.reader.next.side_effect = [frame]
            with self.assertRaises(worker.Refusal):
                fixture.turn(CANARY)
            self.assertEqual(next(e for e in fixture.events if e["action"] == "supervisor-observation")["refusal_code"], "cli-exited")

    def test_duplicate_or_out_of_order_provider_milestones_refuse(self):
        for stages in (("provider-response-observed",), ("provider-write-intent", "provider-write-intent")):
            with self.subTest(stages=stages), tempfile.TemporaryDirectory() as directory:
                fixture = self.fixture(Path(directory))
                fixture.reader.next.side_effect = [dict(event="diagnostic", arm=fixture.arm, operation="turn", turn=1,
                    stage=stage, monotonic_ns=time.monotonic_ns()) for stage in stages]
                with self.assertRaises(worker.Refusal):
                    fixture.turn(CANARY)
                self.assertEqual(fixture.last_failure["refusal_code"], "diagnostic-frame-invalid")

    def test_correlated_provider_milestones_reach_validated_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            stages = ("provider-write-intent", "provider-write-completed", "provider-response-observed", "provider-result-validation")
            frames = [dict(event="diagnostic", arm=fixture.arm, operation="turn", turn=1,
                           stage=stage, monotonic_ns=time.monotonic_ns()) for stage in stages]
            fixture.reader.next.side_effect = lambda *_: frames.pop(0) if frames else self.response()
            fixture.turn(CANARY)
            result = host.observed_milestones([fixture], {"outcome": "failed-or-inconclusive"})
            self.assertEqual(result["provider_turn_writes_observed"], 1)
            self.assertEqual(result["provider_results_observed"], 1)
            self.assertEqual(result["validated_turn_completions"], 1)

    def test_unknown_diagnostic_fields_codes_and_cross_arm_frames_are_rejected(self):
        frame = dict(event="refused", arm="restored-first", operation="turn", turn=1,
                     stage="command-validation", refusal_code="cli-exited", exception_kind="fixture-refusal", errno=None)
        for invalid in (dict(frame, extra=CANARY), dict(frame, refusal_code=CANARY), dict(frame, arm="retained-first")):
            with self.assertRaises(worker.Refusal):
                host.diagnostic_frame(invalid, "restored-first", "turn", 1)
        class Evil(Exception):
            def __str__(self): raise AssertionError("must not stringify")
        for error in (Evil(CANARY), worker.Refusal(CANARY)):
            self.assertEqual(worker.refusal_projection(error)["refusal_code"], "unclassified")
            self.assertNotIn(CANARY, json.dumps(worker.refusal_projection(error)))

    def test_partial_summary_preserves_retained_success_without_comparison(self):
        events = json.loads((host.HERE / "live-partial-export-2026-09-07/retained-first/events.json").read_text())
        fixture = SimpleNamespace(events=events, arm="retained-first", resume=False)
        result = host.observed_milestones([fixture], {"outcome": "failed-or-inconclusive"})
        self.assertTrue(result["retained_correction_verified"])
        self.assertFalse(result["restored_correction_verified"])
        self.assertFalse(result["matched_pair_verified"])
        self.assertEqual(result["validated_turn_completions"], 2)
        self.assertEqual(result["verified_consumptions"], 2)
        self.assertEqual(result["provider_turn_writes_observed"], 0)  # Older protocol did not record it.
        self.assertIn("missing observations do not prove", host.runtime_limitations(result)[0])

    def test_unconfirmed_shutdown_still_retains_delivery_with_closed_context(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.container = "a" * 64
            fixture.pidfd = None
            fixture.credentials = mock.Mock()
            fixture.inspect = mock.Mock(return_value={"State": {"Running": True, "Pid": 123}})
            with mock.patch.object(host, "docker"), self.assertRaises(worker.Refusal):
                fixture.shutdown()
            fixture.credentials.release.assert_not_called()
            self.assertEqual(fixture.last_failure["outer_operation"], "shutdown")
            self.assertEqual(fixture.last_failure["refusal_code"], "shutdown-unconfirmed")

    def test_consume_still_requires_exact_receipt_before_artifact_read(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.fixture(Path(directory))
            fixture.gate = host.base.Gate(Path(directory) / "gate.json", {"container": "pinned"})
            with mock.patch.object(host, "read_artifacts") as read, self.assertRaises(RuntimeError):
                fixture.consume(None, "a" * 32, True)
            read.assert_not_called()
            self.assertEqual(fixture.last_failure["outer_operation"], "consume")


if __name__ == "__main__":
    unittest.main(verbosity=2)
