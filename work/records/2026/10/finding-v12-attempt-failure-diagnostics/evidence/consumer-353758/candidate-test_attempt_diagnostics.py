"""W333486 -- the read-only diagnostic report, and what it refuses to do.

A PURE PROJECTION over one status document: no store, no clock, no engine, no
provider, no subprocess. These cases drive the real module and prove the
allowlist, the per-fact provenance, the bounded unknown reasons, the
incomplete-final-result verdict, the safe-locator emission, and that
`tools/stack_command.COMMANDS` both SERVES and DISPATCHES the subcommand in
source -- with the rebuilt-bundle obligation stated rather than assumed away.

BOUNDED SLICE, stated: the locator ROUND TRIP against a real retained
delivery is not driven here. What is proved is that the report emits the
supported invocation shape, names the one operand only an operator can
supply, and resolves no delivery root itself.
"""

import io
import json
import unittest

from tools import attempt_diagnostics, stack_command

SECRET = "canary-" + "z" * 32


def document(**stage):
    held = {"stage_id": "stage-1", "job_id": "job-1", "kind": "implementation",
            "state": "running", "attempt_id": "attempt-1"}
    diagnostic = stage.get("attempt_diagnostics")
    if isinstance(diagnostic, dict):
        diagnostic = dict(diagnostic, schema=attempt_diagnostics.SOURCE_DIAGNOSTIC_SCHEMA, attempt_id="attempt-1")
        for axis in ("cause", "workspace_object"):
            if isinstance(diagnostic.get(axis), dict):
                diagnostic[axis] = {key: {"known": True, "value": value, "source": "fixture"} for key, value in diagnostic[axis].items()}
        stage["attempt_diagnostics"] = diagnostic
    held.update(stage)
    return {"schema": "baton.v12.job-status/7",
            "jobs": [{"job_id": "job-1", "stages": [held]}]}


class TheReportIsAPureProjection(unittest.TestCase):

    def test_it_reads_one_document_and_opens_NOTHING(self):
        held = attempt_diagnostics.report(json.dumps(document()).encode())
        self.assertEqual(held["schema"], attempt_diagnostics.SCHEMA)
        self.assertIs(held["opens_no_store"], True)
        self.assertEqual(len(held["rows"]), 1)

    def test_it_states_NO_FRESHNESS_VERDICT_because_none_was_selected(self):
        held = attempt_diagnostics.report(json.dumps(document()).encode())
        self.assertIsNone(held["freshness_verdict"])
        self.assertIn("no freshness policy", held["freshness_why"])

    def test_a_DIAGNOSTIC_CAUSE_IS_NOT_AN_ACCEPTANCE(self):
        held = attempt_diagnostics.report(json.dumps(document(
            attempt_diagnostics={"cause": {
                "component": "expiry-reclaim", "operation_id": "op-1",
                "correlation_id": "c-1", "outcome": "ceased-absent",
                "cessation": "absent", "runtime_id": "container-1",
                "category": None, "code": None}})).encode())
        row = held["rows"][0]
        self.assertIs(held["is_acceptance"], False)
        self.assertIs(row["completeness"]["is_acceptance"], False)
        self.assertIs(row["completeness"]["proves_cessation"], False)
        self.assertEqual(row["completeness"]["state"], "incomplete")
        self.assertEqual(row["cause"]["cessation"]["value"], "absent")

    def test_an_ABSENT_diagnostic_means_NOBODY_LOOKED(self):
        row = attempt_diagnostics.report(
            json.dumps(document()).encode())["rows"][0]
        self.assertIsNone(row["cause"])
        self.assertEqual(row["completeness"]["state"], "absent")
        self.assertIn("nobody looked", row["completeness"]["why"])

    def test_an_INCOMPLETE_final_result_is_INCOMPLETE_and_nothing_more(self):
        # The facts are partial the way a deadline-bounded publication
        # failure leaves them. That is neither a cessation nor an acceptance,
        # and WHY it is partial is unknown.
        row = attempt_diagnostics.report(json.dumps(document(
            attempt_diagnostics={"cause": {"component": "cancellation",
                                           "operation_id": "op-1"}}
        )).encode())["rows"][0]
        self.assertEqual(row["completeness"]["state"], "incomplete")
        self.assertIn("outcome", row["completeness"]["missing"])
        self.assertIs(row["completeness"]["proves_cessation"], False)
        self.assertIn("unknown", row["completeness"]["why"])

    def test_EVERY_member_is_known_with_a_source_or_unknown_with_a_reason(self):
        row = attempt_diagnostics.report(
            json.dumps(document()).encode())["rows"][0]
        for member in row["stage"].values():
            if member["known"]:
                self.assertTrue(member["source"])
            else:
                self.assertTrue(member["why"])
                self.assertIsNone(member["value"])

    def test_the_ALLOWLIST_IS_POSITIVE_and_an_unknown_member_is_NAMED_only(self):
        row = attempt_diagnostics.report(json.dumps(document(
            attempt_diagnostics={"cause": {
                "component": "expiry-reclaim", "operation_id": "op-1",
                "correlation_id": "c-1", "outcome": "ceased-absent",
                "cessation": "absent", "runtime_id": "container-1",
                "category": None, "code": None,
                "private_transcript": SECRET}})).encode())
        self.assertEqual(row["rows"][0]["unrecognised"], ("undeclared members omitted",))
        self.assertNotIn(SECRET, json.dumps(row, default=list))

    def test_a_NESTED_OBJECT_is_NOT_forwarded_wholesale(self):
        row = attempt_diagnostics.report(json.dumps(document(
            attempt_diagnostics={"cause": {
                "component": {"leaked": SECRET}, "operation_id": "op-1",
                "correlation_id": "c-1", "outcome": "ceased-absent",
                "cessation": "absent", "runtime_id": None,
                "category": None, "code": None}})).encode())
        self.assertNotIn(SECRET, json.dumps(row, default=list))
        self.assertFalse(row["rows"][0]["cause"]["component"]["known"])

    def test_DEVICE_AND_INODE_travel_labelled_and_are_NOT_a_locator(self):
        row = attempt_diagnostics.report(json.dumps(document(
            attempt_diagnostics={"workspace_object": {"device": 7,
                                                      "inode": 9}}
        )).encode())["rows"][0]
        workspace = row["locators"]["workspace_object"]
        self.assertEqual(workspace["device"]["value"], 7)
        self.assertIs(workspace["is_a_path"], False)
        self.assertIs(workspace["is_a_locator"], False)

    def test_the_SUPPORTED_READ_names_the_one_operand_it_cannot_supply(self):
        row = attempt_diagnostics.report(
            json.dumps(document()).encode())["rows"][0]
        supported = row["locators"]["supported_read"]
        self.assertIn("baton-v12-stack logs", supported["command"])
        self.assertEqual(supported["operator_must_supply"], "<launch-home>")
        self.assertIn("deployment fact", supported["why"])

    def test_it_carries_the_MANAGERS_OWN_recorded_artifacts_by_name(self):
        row = attempt_diagnostics.report(json.dumps(document(
            artifacts=[{"name": "result/answer.txt"}])).encode())["rows"][0]
        self.assertEqual(tuple(row["locators"]["recorded_artifacts"]["value"]),
                         ("result/answer.txt",))


class TheCommandTableServesAndDispatchesIt(unittest.TestCase):

    def test_COMMANDS_carries_the_subcommand_in_SOURCE(self):
        self.assertIn("attempt-diagnostics", stack_command.COMMANDS)

    def test_the_entry_DISPATCHES_to_this_module(self):
        called = []
        original = attempt_diagnostics.main
        attempt_diagnostics.main = lambda operands: called.append(operands) or 0
        try:
            answer = stack_command.COMMANDS["attempt-diagnostics"](["a.json"])
        finally:
            attempt_diagnostics.main = original
        self.assertEqual(answer, 0)
        self.assertEqual(called, [["a.json"]])

    def test_the_REBUILT_BUNDLE_obligation_is_stated_in_the_artifact(self):
        held = attempt_diagnostics.report(json.dumps(document()).encode())
        self.assertIn("rebuilt", held["deployment_obligation"])
        self.assertIn("stack_command.COMMANDS",
                      held["deployment_obligation"])
        self.assertIn("rebuilt bundle",
                      (attempt_diagnostics.__doc__ or "").lower())

    def test_the_COMMAND_refuses_an_operand_set_it_does_not_serve(self):
        stream = io.StringIO()
        import contextlib
        stack = contextlib.redirect_stderr(io.StringIO())
        stack.__enter__()
        self.addCleanup(stack.__exit__, None, None, None)
        self.assertEqual(attempt_diagnostics.main([], stream=stream), 2)
        self.assertEqual(attempt_diagnostics.main(["a", "b"], stream=stream), 2)


from unittest.mock import patch
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import status, submit
from baton_v12.job_manager import delegation
from baton_v12.worker_manager import accept_offer, record_attempt, failure_cause
from tests.job_manager.fixtures import JobManagerCase, NOW, UUID, WORK_A, PROFILE, job, submission


class RealStatusReportSeam(JobManagerCase):
    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.control_store = self.control()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.stage = self.attempting(self.jobs)
        self.acts = self.operations(control=self.control_store)
        self.job = {"input_digest": "sha256:" + "1" * 64, "policy_digest": "sha256:" + "2" * 64}
        self.acts.admit(self.stage, self.job)
        accept_offer(self.control_store, self.acts.port, offer_id=self.stage["offer_id"],
                     decision="accept", bearer=self.delivered[-1]["bearer"], now=NOW,
                     runtime_attempt_id=self.stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        self.acts.claim(self.stage)
        record_attempt(self.control_store, attempt_id=self.stage["attempt_id"],
                       adapter_name="acp", adapter_digest="sha256:" + "a" * 64,
                       profile_digest=PROFILE, policy_digest="sha256:" + "2" * 64)

    def snapshot(self, operations=None):
        return status(self.jobs, operations or self.acts, observed_at=NOW)

    def row(self, snapshot=None):
        return attempt_diagnostics.report(json.dumps(snapshot or self.snapshot()).encode())["rows"][0]

    def outcome(self, outcome="ceased-absent", **extra):
        return failure_cause.record_and_raise_cessation_outcome(
            self.control_store, self.stage["attempt_id"], component="expiry-reclaim",
            generation=None, runtime_id="container-1", correlation_id="resource.reclaim:abc",
            effects=("revoke", "stop", "remove"), outcome=outcome, **extra)

    def test_real_durable_expiry_reaches_status_and_report_unchanged(self):
        self.outcome()
        before = (self.jobs._connection.total_changes, self.control_store._connection.total_changes,
                  list(self.session.calls))
        snapshot = self.snapshot()
        row = self.row(snapshot)
        cause = snapshot["jobs"][0]["stages"][0]["attempt_diagnostics"]["cause"]
        for name in ("component", "operation_id", "correlation_id", "runtime_id", "outcome", "cessation", "effects"):
            self.assertEqual(row["cause"][name]["value"], failure_cause.decode(cause[name])[1])
            self.assertTrue(row["cause"][name]["known"])
        self.assertEqual(row["stage"]["episode"]["value"], 1)
        self.assertEqual(row["axes"]["renewal_limit"]["value"], failure_cause.tokens.RENEWAL_LIMIT)
        self.assertEqual(before, (self.jobs._connection.total_changes, self.control_store._connection.total_changes,
                                  list(self.session.calls)))
        self.assertFalse(row["completeness"]["is_acceptance"])

    def test_typed_engine_failure_is_known_while_cessation_remains_unknown(self):
        self.outcome("engine-timeout", category="runtime-observation", code="engine-timeout")
        row = self.row()
        self.assertEqual(row["cause"]["outcome"]["value"], "engine-timeout")
        self.assertEqual(row["cause"]["cessation"]["value"], "unknown")
        self.assertEqual(row["cause"]["code"]["value"], "engine-timeout")

    def test_historical_unknown_is_not_an_empty_success(self):
        row = self.row()
        self.assertIsNone(row["cause"])
        self.assertIn("no durable cause", row["unknown_why"])
        self.assertIn("attempt.cessation-*:expiry-reclaim", row["absent_records"])
        self.assertEqual(row["completeness"]["state"], "incomplete")

    def test_unreadable_diagnostic_does_not_erase_independent_status(self):
        expected = self.snapshot()["jobs"][0]["stages"][0]["state"]
        for error in (PermissionError(SECRET), ValueError(SECRET), ContractRefusal("integrity", "schema", SECRET)):
            with self.subTest(error=type(error).__name__), patch.object(delegation, "attempt_failure_cause_of", side_effect=error):
                snapshot = self.snapshot()
                self.assertEqual(snapshot["jobs"][0]["stages"][0]["state"], expected)
                row = self.row(snapshot)
                self.assertEqual(row["completeness"]["state"], "unavailable")
                self.assertNotIn(SECRET, json.dumps(snapshot))
                self.assertNotIn(SECRET, json.dumps(row))

    def test_other_episode_and_runtime_evidence_cannot_be_reported_as_current(self):
        self.outcome()
        snapshot = self.snapshot()
        stage = snapshot["jobs"][0]["stages"][0]
        diagnostic = stage["attempt_diagnostics"]
        diagnostic["attempt_id"] = "other-episode-attempt"
        self.assertEqual(self.row(snapshot)["completeness"]["state"], "unavailable")
        diagnostic["attempt_id"] = stage["attempt_id"]
        diagnostic["execution"]["runtime_id"] = {"known": True, "value": "other-runtime", "source": "attempts"}
        self.assertEqual(self.row(snapshot)["completeness"]["state"], "unavailable")

    def test_stale_snapshot_preserves_recorded_time_without_inventing_freshness(self):
        snapshot = self.snapshot()
        diagnostic = snapshot["jobs"][0]["stages"][0]["attempt_diagnostics"]
        diagnostic["execution"]["observed_at"] = {"known": True, "value": NOW, "source": "attempts"}
        result = attempt_diagnostics.report(json.dumps(snapshot).encode())
        self.assertEqual(result["rows"][0]["execution"]["observed_at"]["value"], NOW)
        self.assertIsNone(result["freshness_verdict"])

    def test_returned_and_exception_carriers_are_reported_without_private_text(self):
        for raises in (False, True):
            with self.subTest(raises=raises):
                original = ContractRefusal("runtime-observation", "identity-mismatch", SECRET)
                setattr(original, failure_cause.DEGRADATION_MEMBER, SECRET)
                def call(stage, job):
                    if raises:
                        raise original
                    return {failure_cause.DEGRADATION_MEMBER: SECRET}
                acts = self.operations(control=self.control_store, conclude_attempt=call)
                if raises:
                    with self.assertRaises(ContractRefusal) as caught:
                        acts.conclude(self.stage, self.job)
                    self.assertIs(caught.exception, original)
                else:
                    acts.conclude(self.stage, self.job)
                snapshot = self.snapshot(acts)
                row = self.row(snapshot)
                self.assertEqual(row["diagnostic_degradation"]["value"], True)
                self.assertIn("process-local", row["diagnostic_degradation"]["source"])
                self.assertNotIn(SECRET, json.dumps(snapshot))
                self.assertNotIn(SECRET, json.dumps(row))
                # A cold reader has no carrier evidence; it cannot assert success.
                self.assertFalse(self.row()["diagnostic_degradation"]["known"])

    def test_private_keys_provenance_and_unknown_reasons_are_not_forwarded(self):
        self.outcome()
        snapshot = self.snapshot()
        diagnostic = snapshot["jobs"][0]["stages"][0]["attempt_diagnostics"]
        diagnostic["cause"][SECRET] = SECRET
        diagnostic["cause"]["category"] = {"known": False, "value": None, "why": SECRET}
        diagnostic["cause"]["component"]["source"] = SECRET
        diagnostic["unknown"] = {"why": SECRET}
        diagnostic["absent_records"] = [SECRET]
        self.assertNotIn(SECRET, json.dumps(self.row(snapshot)))

    def test_EVERY_absent_record_the_PRODUCER_composes_reaches_the_report(self):
        """W333486 claim353758: the report's names held against the producer's.

        THE DEFECT THIS CATCHES, measured through this very seam: the reader
        allowlisted `attempt.start-failed`, `attempt.preparation-failed` and a
        bare `resource.revoked`, while `failure_cause` emits
        `runtime.start-failed`, `runtime.preparation-failed` and
        `resource-token.revoked` (bare OR suffixed with its domain and
        generation). THREE OF THE FIVE names a real composed expiry carried
        were dropped SILENTLY, which is the failure mode
        `failure_cause._compose` warns about in terms: a reader that discards a
        record quietly hides that the producer moved.

        The expectation is not a list typed here. It is `absent_of` over the
        SAME document the report read, so a producer rename fails this case
        instead of emptying the report.
        """
        self.outcome()
        snapshot = self.snapshot()
        diagnostic = snapshot["jobs"][0]["stages"][0]["attempt_diagnostics"]
        produced = failure_cause.absent_of(diagnostic)
        self.assertTrue(produced, "this composition must name absent records")
        row = self.row(snapshot)
        self.assertEqual(tuple(row["absent_records"] or ()), tuple(produced))

    def test_an_absent_record_the_report_does_NOT_own_is_still_dropped(self):
        """The allowlist stays POSITIVE: recognition widened, not removed."""
        snapshot = self.snapshot()
        self.outcome()
        snapshot = self.snapshot()
        diagnostic = snapshot["jobs"][0]["stages"][0]["attempt_diagnostics"]
        diagnostic["absent_records"] = list(diagnostic["absent_records"]) + [
            SECRET, "resource-token.revokedNOTASEPARATOR", "attempt.start-failed"]
        row = self.row(snapshot)
        reported = tuple(row["absent_records"] or ())
        self.assertNotIn(SECRET, json.dumps(row))
        self.assertNotIn("resource-token.revokedNOTASEPARATOR", reported)
        # The producer's OLD spelling is not owned by this build either.
        self.assertNotIn("attempt.start-failed", reported)

    def test_owned_source_schema_does_not_drift(self):
        self.assertEqual(attempt_diagnostics.SOURCE_DIAGNOSTIC_SCHEMA, failure_cause.DIAGNOSTIC_SCHEMA)

    def test_cli_missing_denied_and_malformed_input_never_creates_a_store(self):
        import contextlib
        from pathlib import Path
        missing = Path(self.root) / "never-created.sqlite3"
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(attempt_diagnostics.main([str(missing)], stream=io.StringIO()), 2)
            self.assertFalse(missing.exists())
            with patch("builtins.open", side_effect=PermissionError(SECRET)):
                self.assertEqual(attempt_diagnostics.main([str(missing)], stream=io.StringIO()), 2)
            missing.write_text(SECRET)
            before = missing.read_bytes()
            self.assertEqual(attempt_diagnostics.main([str(missing)], stream=io.StringIO()), 2)
            self.assertEqual(missing.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
