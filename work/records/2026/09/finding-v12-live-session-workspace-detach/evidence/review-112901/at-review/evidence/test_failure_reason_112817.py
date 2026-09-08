"""Focused closed status projection; no provider, private data or broad suite."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import test_result_diagnostics as prior
import live_controller_failure_reason_112817 as host

worker = host.wire
prior.host = host
prior.worker = worker
prior.prior.host = host
prior.prior.worker = worker
CANARY = prior.CANARY


class FailureReasonTests(unittest.TestCase):
    def transport(self, value):
        return prior.ResultDiagnosticsTests().transport(value)

    def good(self):
        return prior.ResultDiagnosticsTests().good()

    def test_every_documented_status_is_preserved_as_an_observation(self):
        self.assertEqual(worker.KNOWN_API_ERROR_STATUSES, {400, 401, 402, 403, 404, 409, 413, 429, 500, 504, 529})
        for code in worker.KNOWN_API_ERROR_STATUSES:
            value = dict(self.good(), is_error=True, api_error_status=code)
            projected = worker.failure_reason(value)
            self.assertEqual(projected, dict(shape="known", http_status=code))
            self.assertEqual(worker.validate_failure_reason(projected), projected)
            with self.assertRaisesRegex(worker.Refusal, '^provider-result-failed$'):
                worker.result_projection(value, prior.SESSION)

    def test_missing_null_unknown_and_malformed_values_are_closed(self):
        self.assertEqual(worker.failure_reason({}), dict(shape="missing", http_status=None))
        cases = [(None, "null"), (True, "wrong-type"), (False, "wrong-type"), (429.0, "wrong-type"),
                 ("429", "wrong-type"), (CANARY, "wrong-type"), ([429, CANARY], "wrong-type"),
                 ({"status": 429, CANARY: CANARY}, "wrong-type"), (0, "unknown"), (200, "unknown"),
                 (-1, "unknown"), (599, "unknown"), (10**200, "unknown")]
        for value, shape in cases:
            with self.subTest(shape=shape, kind=type(value).__name__):
                result = worker.failure_reason(dict(api_error_status=value, result=CANARY, errors=[CANARY]))
                self.assertEqual(result, dict(shape=shape, http_status=None))
                self.assertEqual(worker.validate_failure_reason(result), result)
                self.assertNotIn(CANARY, json.dumps(result))

    def test_actual_failed_transport_persists_status_without_acceptance(self):
        for code in (401, 429, 529, CANARY, None):
            value = dict(self.good(), is_error=True, api_error_status=code)
            supervisor, frames = self.transport(value)
            self.assertEqual(frames[-2]["failure_reason"], worker.failure_reason(value))
            self.assertEqual(frames[-1]["refusal_code"], "provider-result-failed")
            with tempfile.TemporaryDirectory() as directory:
                fixture = prior.prior.DiagnosticsTests().fixture(Path(directory))
                fixture.reader.next.side_effect = frames
                with self.assertRaisesRegex(worker.Refusal, '^supervisor-refused$'):
                    fixture.turn(CANARY)
                saved = json.loads((Path(directory) / "events.json").read_text())
                summary = next(event["failure_reason"] for event in saved if "failure_reason" in event)
                self.assertEqual(summary, worker.failure_reason(value))
                observed = host.observed_milestones([fixture], {})
                self.assertEqual(observed["validated_turn_completions"], 0)
                self.assertEqual(observed["verified_consumptions"], 0)
                self.assertFalse(observed["restoration_verified"])
                self.assertNotIn(CANARY, json.dumps(saved))
            with self.assertRaisesRegex(worker.Refusal, '^user-turn-limit$'):
                supervisor.turn(dict(prompt="not another turn"))

    def test_status_neither_grants_nor_revokes_result_acceptance(self):
        for status in (None, 429, CANARY):
            _, frames = self.transport(dict(self.good(), api_error_status=status))
            self.assertEqual(frames[-1]["event"], "complete")
        for patch, refusal in ((dict(session_id="foreign"), "result-session-changed"),
                               (dict(num_turns=True), "provider-turn-limit"),
                               (dict(total_cost_usd=2), "reported-cost-limit")):
            _, frames = self.transport(dict(self.good(), api_error_status=401, **patch))
            self.assertEqual(frames[-1]["refusal_code"], refusal)

    def test_host_refuses_malformed_summary_before_logging(self):
        frame = self.transport(dict(self.good(), is_error=True, api_error_status=429))[1][-2]
        malformed = [None, [], CANARY, {}, dict(shape="known", http_status=True),
                     dict(shape="known", http_status=599), dict(shape="known", http_status="429"),
                     dict(shape="missing", http_status=429), dict(shape=CANARY, http_status=None),
                     dict(shape=[CANARY], http_status=None), dict(shape="known", http_status={CANARY: CANARY}),
                     dict(shape="known", http_status=429, text=CANARY)]
        for value in malformed:
            bad = dict(frame, failure_reason=value)
            with self.assertRaises(worker.Refusal):
                host.diagnostic_frame(bad, "restored-first", "turn", 1)
            with tempfile.TemporaryDirectory() as directory:
                fixture = prior.prior.DiagnosticsTests().fixture(Path(directory))
                fixture.reader.next.side_effect = [bad]
                with self.assertRaises(worker.Refusal):
                    fixture.turn(CANARY)
                self.assertFalse(any("failure_reason" in event for event in fixture.events))
                self.assertNotIn(CANARY, json.dumps(fixture.events))

    def test_summary_cannot_cross_arm_operation_turn_stage_or_order(self):
        frames = self.transport(dict(self.good(), is_error=True, api_error_status=429))[1]
        frame = frames[-2]
        for patch in (dict(arm="restored-second"), dict(operation="shutdown"), dict(turn=0),
                      dict(stage="provider-write-intent"), dict(event="refused")):
            with self.assertRaises(worker.Refusal):
                host.diagnostic_frame(dict(frame, **patch), "restored-first", "turn", 1)
        for sequence in ([frames[0], frame], [*frames[:-1], frame]):
            with tempfile.TemporaryDirectory() as directory:
                fixture = prior.prior.DiagnosticsTests().fixture(Path(directory))
                fixture.reader.next.side_effect = sequence
                with self.assertRaises(worker.Refusal):
                    fixture.turn(CANARY)
                self.assertLessEqual(sum("failure_reason" in event for event in fixture.events), 1)
                self.assertEqual(host.observed_milestones([fixture], {})["validated_turn_completions"], 0)

    def test_legacy_absence_stays_unobserved_and_input_is_not_mutated(self):
        value = dict(self.good(), is_error=True, api_error_status=429, secret={CANARY: [CANARY]})
        before = copy.deepcopy(value)
        worker.failure_reason(value)
        self.assertEqual(value, before)
        frame = self.transport(value)[1][-2]
        del frame["failure_reason"]
        self.assertEqual(host.diagnostic_frame(frame, "restored-first", "turn", 1), frame)
        self.assertNotIn("failure_reason", frame)
        with self.assertRaisesRegex(worker.Refusal, '^provider-result-failed$'):
            worker.result_projection(value, prior.SESSION)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    for cls in (FailureReasonTests, prior.ResultDiagnosticsTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    for method in ("test_unconfirmed_shutdown_still_retains_delivery_with_closed_context",
                   "test_consume_still_requires_exact_receipt_before_artifact_read"):
        suite.addTest(prior.prior.DiagnosticsTests(method))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
