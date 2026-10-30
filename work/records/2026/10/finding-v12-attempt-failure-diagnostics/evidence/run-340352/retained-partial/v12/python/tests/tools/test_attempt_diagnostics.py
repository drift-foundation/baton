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
        self.assertEqual(row["completeness"]["state"], "complete")

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
        self.assertIn("private_transcript", row["rows"][0]["unrecognised"])
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


if __name__ == "__main__":
    unittest.main()
