"""Closed result evidence through actual supervisor/host methods; offline only."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import live_controller_rebound_112609 as host
import test_restore_constructor as constructors
import test_live_package as package

worker = host.wire
prior = constructors.restoration.prior
prior.host = host
prior.worker = worker
constructors.candidate = host
constructors.restoration.candidate = host
package.wire = worker
SESSION = prior.SESSION
CANARY = prior.CANARY


class ResultDiagnosticsTests(unittest.TestCase):
    def good(self):
        return dict(type="result", subtype="success", is_error=False, session_id=SESSION,
                    num_turns=2, total_cost_usd=0.01, result=CANARY, errors=[CANARY])

    def transport(self, result):
        supervisor = prior.DiagnosticsTests().supervisor([result])
        supervisor.model = worker.ACTUAL_MODEL
        supervisor.limit = 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                answer = supervisor.turn(dict(prompt=CANARY))
            except worker.Refusal as error:
                answer = dict(event="refused", arm=supervisor.arm, operation=supervisor.operation,
                              turn=supervisor.turns, stage=supervisor.stage, **worker.refusal_projection(error))
        frames = [json.loads(line) for line in output.getvalue().splitlines()]
        return supervisor, frames + [answer]

    def summary(self, frames):
        return next(frame["result_fields"] for frame in frames if "result_fields" in frame)

    def test_all_field_shapes_are_independent_and_closed(self):
        absent = object()
        subtypes = [(absent, "missing", None), (None, "wrong-type", None), (False, "wrong-type", None),
                    (0, "wrong-type", None), ([CANARY], "wrong-type", None), ({CANARY: CANARY}, "wrong-type", None),
                    ("success", "success", None), ("", "unknown", None), (CANARY, "unknown", None)]
        subtypes += [(name, "known-nonsuccess", name) for name in worker.KNOWN_RESULT_SUBTYPES]
        flags = [(absent, "missing"), (False, "false"), (True, "true"), (None, "wrong-type"),
                 (0, "wrong-type"), (1, "wrong-type"), (CANARY, "wrong-type"), ([CANARY], "wrong-type")]
        for subtype, shape, known in subtypes:
            for flag, error_shape in flags:
                with self.subTest(subtype_shape=shape, flag_shape=error_shape):
                    value = {"result": CANARY, "errors": [CANARY], CANARY: CANARY}
                    if subtype is not absent:
                        value["subtype"] = subtype
                    if flag is not absent:
                        value["is_error"] = flag
                    projection = worker.result_fields(value)
                    self.assertEqual(projection, dict(subtype=shape, known_subtype=known, is_error=error_shape))
                    self.assertEqual(worker.validate_result_fields(projection), projection)
                    self.assertNotIn(CANARY, json.dumps(projection))

    def test_actual_failed_turns_preserve_fields_before_unchanged_refusal(self):
        cases = [dict(self.good(), is_error=True), dict(self.good(), subtype="error_max_turns"),
                 {key: value for key, value in self.good().items() if key != "subtype"},
                 {key: value for key, value in self.good().items() if key != "is_error"},
                 dict(self.good(), subtype=CANARY, is_error=CANARY)]
        for value in cases:
            supervisor, frames = self.transport(value)
            self.assertEqual(self.summary(frames), worker.result_fields(value))
            self.assertEqual(frames[-1]["refusal_code"], "provider-result-failed")
            self.assertEqual(frames[-2]["stage"], "provider-result-validation")
            self.assertEqual(frames[-1]["stage"], "provider-result-validation")
            self.assertNotIn(CANARY, json.dumps(frames))
            with self.assertRaisesRegex(worker.Refusal, "^user-turn-limit$"):
                supervisor.turn(dict(prompt="second turn forbidden"))
            with tempfile.TemporaryDirectory() as directory:
                fixture = prior.DiagnosticsTests().fixture(Path(directory))
                fixture.reader.next.side_effect = frames
                with self.assertRaisesRegex(worker.Refusal, "^supervisor-refused$"):
                    fixture.turn(CANARY)
                saved = json.loads((Path(directory) / "events.json").read_text())
                self.assertEqual(self.summary(saved), worker.result_fields(value))
                milestones = host.observed_milestones([fixture], {"outcome": "failed-or-inconclusive"})
                self.assertEqual(milestones["provider_results_observed"], 1)
                self.assertEqual(milestones["validated_turn_completions"], 0)
                self.assertEqual(milestones["verified_consumptions"], 0)
                self.assertFalse(milestones["restoration_verified"])
                self.assertNotIn(CANARY, json.dumps(saved))

    def test_actual_success_transport_keeps_summary_and_validated_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = prior.DiagnosticsTests().fixture(Path(directory))
            frames = []
            def next_frame(*_):
                if not frames:
                    frames.extend(self.transport(self.good())[1])
                return frames.pop(0)
            fixture.reader.next.side_effect = next_frame
            fixture.turn(CANARY)
            self.assertEqual(self.summary(fixture.events), dict(subtype="success", known_subtype=None, is_error="false"))
            self.assertEqual(host.observed_milestones([fixture], {})["validated_turn_completions"], 1)
            self.assertNotIn(CANARY, json.dumps(fixture.events))

    def test_success_fields_do_not_waive_session_turn_cost_or_model_checks(self):
        cases = [(dict(self.good(), session_id="wrong"), "result-session-changed"),
                 (dict(self.good(), num_turns=True), "provider-turn-limit"),
                 (dict(self.good(), num_turns=9), "provider-turn-limit"),
                 (dict(self.good(), total_cost_usd=1.01), "reported-cost-limit"),
                 (dict(self.good(), total_cost_usd=float("nan")), "reported-cost-limit")]
        for value, code in cases:
            _, frames = self.transport(value)
            self.assertEqual(self.summary(frames), dict(subtype="success", known_subtype=None, is_error="false"))
            self.assertEqual(frames[-1]["refusal_code"], code)
        supervisor = prior.DiagnosticsTests().supervisor([self.good()])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(worker.Refusal, "^actual-model-unobserved$"):
            supervisor.turn(dict(prompt=CANARY))

    def test_summary_requires_exact_keys_closed_values_and_consistent_known_label(self):
        good = worker.result_fields(self.good())
        invalid = [None, [], dict(good, extra=CANARY), {"subtype": "success"},
                   dict(good, subtype=CANARY), dict(good, is_error=False), dict(good, is_error=CANARY),
                   dict(good, known_subtype=CANARY), dict(good, subtype="known-nonsuccess"),
                   dict(good, subtype="known-nonsuccess", known_subtype=CANARY), dict(good, subtype=[CANARY])]
        frame = self.transport(self.good())[1][-2]
        for value in invalid:
            with self.assertRaisesRegex(worker.Refusal, "^diagnostic-frame-invalid$"):
                host.diagnostic_frame(dict(frame, result_fields=value), "restored-first", "turn", 1)

    def test_summary_cannot_cross_arm_operation_turn_stage_or_order(self):
        frames = self.transport(self.good())[1]
        summary = frames[-2]
        for change in (dict(arm="restored-second"), dict(operation="identity"), dict(turn=0), dict(turn=2),
                       dict(stage="provider-response-observed"), dict(extra=CANARY), dict(monotonic_ns=True)):
            with self.subTest(change=change), self.assertRaises(worker.Refusal):
                host.diagnostic_frame(dict(summary, **change), "restored-first", "turn", 1)
        for malformed in ([summary], frames[:3] + [summary, summary], frames[:2] + [summary]):
            with tempfile.TemporaryDirectory() as directory:
                fixture = prior.DiagnosticsTests().fixture(Path(directory))
                fixture.reader.next.side_effect = malformed
                with self.assertRaisesRegex(worker.Refusal, "^diagnostic-frame-invalid$"):
                    fixture.turn(CANARY)
                self.assertNotIn("turn-complete", [event["action"] for event in fixture.events])

    def test_no_summary_for_assistant_text_or_missing_result(self):
        supervisor = prior.DiagnosticsTests().supervisor([dict(type="assistant", subtype=CANARY, message=CANARY)])
        supervisor.lines.next.side_effect = [dict(type="assistant", message=CANARY), worker.Refusal("stream-eof")]
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(worker.Refusal, "^stream-eof$"):
            supervisor.turn(dict(prompt=CANARY))
        self.assertNotIn("result_fields", output.getvalue())
        self.assertNotIn(CANARY, output.getvalue())

    def test_legacy_diagnostics_remain_readable_without_fabricated_summary(self):
        frames = self.transport(self.good())[1]
        old = dict(frames[-2])
        del old["result_fields"]
        self.assertEqual(host.diagnostic_frame(old, "restored-first", "turn", 1), old)
        self.assertNotIn("result_fields", old)


class SnapshotTests(unittest.TestCase):
    def test_actual_new_manifest_imports_without_runtime_or_source_construction(self):
        manifest = json.loads(host.MANIFEST.read_text())
        program = """import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import live_controller_rebound_112609 as c
setup=c.Setup(Path(sys.argv[3]))
apis=c.runtime_apis(Path(sys.argv[2]),setup)
print(json.dumps(dict(api_count=len(apis),review_driver_imported='baton_v12.job_manager.review_driver' in sys.modules,
                     resources=setup.value['resources'])))
"""
        with tempfile.TemporaryDirectory(prefix="baton-w106673-result-import-") as directory:
            runtime = host.snapshot_runtime(Path(directory), manifest)
            result = subprocess.run(["/usr/bin/python3", "-B", "-s", "-c", program, str(host.HERE), str(runtime), directory],
                cwd=directory, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            observed = json.loads(result.stdout)
            self.assertEqual(observed["api_count"], 4)
            self.assertEqual(observed["resources"], dict(credential_home="not-started", source_registry="not-started", fixture_store="not-started"))
            self.assertFalse(observed["review_driver_imported"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--broad"]:
        classes = (prior.DiagnosticsTests, constructors.restoration.RestorationTests,
                   constructors.ConstructorTests, package.StreamTests, SnapshotTests)
    else:
        if sys.argv[1:]:
            raise SystemExit("Only --broad or no operand is supported")
        classes = (ResultDiagnosticsTests,)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in classes)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
