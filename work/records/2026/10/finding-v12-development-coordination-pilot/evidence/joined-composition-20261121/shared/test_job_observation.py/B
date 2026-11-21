"""W385263: the same facts and clocks reach both operator surfaces."""
import copy
import datetime
import io
import json
import os
import re
from pathlib import Path
import tempfile
import unittest

from tools import job_observation as model, job_viewer, stack, worker_visibility


NOW = "2026-11-19T18:00:00.000Z"
EPOCH = datetime.datetime.fromisoformat(NOW.replace("Z", "+00:00")).timestamp()


def document():
    return {"schema": stack.STATUS_SCHEMA, "observed_at": NOW,
            "canonical": True, "incarnation": "publisher",
            "jobs": [{"job_id": "job-a", "submission_id": "submission-a",
                      "stages": [{"stage_id": "implementation", "kind": "implementation",
                                  "state": "running", "attempt_id": "attempt-a",
                                  "runtime": {"activity": {"attempt_id": "attempt-a", "bytes_observed": 0,
                                                           "observed_at": "2026-11-19T17:59:00.000Z"}},
                                  "exchange": {"states": [{"operation": "work", "state": "dispatched"}]}}]}]}


def views(doc):
    output = io.StringIO()
    stack._print_job_outcomes({"state": "fresh", "canonical": True, "document": doc}, output)
    snapshot = job_viewer.read_snapshot(doc, received_at=0)
    return output.getvalue(), "\n".join(job_viewer.render_list(snapshot, now=0, wall_now=EPOCH)), "\n".join(job_viewer.render_detail(snapshot, "job-a", now=0, wall_now=EPOCH))


class SharedObservation(unittest.TestCase):
    def test_shared_outcomes_gates_and_typed_failure(self):
        for state, outcome in (("running", "IN PROGRESS"), ("completed", "COMPLETED"), ("queued", "QUEUED"), ("changes-requested", "CHANGES REQUESTED"), ("exceptional", "FAILED"), ("blocked", "BLOCKED"), ("unrecognized", "UNKNOWN")):
            doc = document()
            stage = doc["jobs"][0]["stages"][0]
            stage["state"] = state
            stage["exchange"]["terminal"] = {"ending": "faulted", "fault_code": "agent", "adapter_failure": {"component": "role-adapter", "code": "role-output-missing"}}
            if state == "blocked":
                stage["gates"] = [{"open": False, "stage_id": "dependency", "state": "exceptional"}]
            for rendered in views(doc):
                with self.subTest(state=state):
                    self.assertIn(outcome, rendered)
                    if state == "exceptional":
                        self.assertIn("agent fault; role-output-missing", rendered)
                    if state == "blocked":
                        self.assertIn("waiting on dependency (exceptional)", rendered)

    def test_activity_zero_missing_foreign_and_old_in_fresh_snapshot(self):
        for attempt, count, expected in (("attempt-a", 0, "0 B"), ("attempt-a", None, "unknown"), ("retired-attempt", 500, "unknown")):
            doc = document()
            activity = doc["jobs"][0]["stages"][0]["runtime"]["activity"]
            activity.update(attempt_id=attempt, bytes_observed=count)
            before = copy.deepcopy(doc)
            for rendered in views(doc):
                self.assertRegex(rendered, r"activity\s+" + re.escape(expected))
                if count == 0:
                    self.assertIn("observed 1m00s ago", rendered)
                self.assertIn("work dispatched (reported; attempt association unverified)", rendered)
                self.assertNotIn("STALE", rendered)
            self.assertEqual(doc, before)

    def test_terminal_activity_keeps_original_absolute_time(self):
        doc = document()
        stage = doc["jobs"][0]["stages"][0]
        stage["state"] = "completed"
        for rendered in views(doc):
            self.assertIn("last at 2026-11-19T17:59:00.000Z", rendered)
            self.assertNotIn("observed 1m00s ago", rendered)

    def test_publication_and_observation_ages_share_exact_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "status.json"
            for observed_age, published_age in ((14.999, 0), (15, 0), (0, 15), (0, 14.999), (60, 0)):
                doc = document()
                doc["observed_at"] = datetime.datetime.fromtimestamp(EPOCH - observed_age, datetime.timezone.utc).isoformat()
                path.write_text(json.dumps(doc))
                os.utime(path, (EPOCH - published_age, EPOCH - published_age))
                read = stack.snapshot(root, EPOCH)
                viewer = job_viewer.JobViewer(job_viewer._source_from(path), clock=lambda: 0, wall=lambda: EPOCH)
                viewer.refresh()
                expected = max(observed_age, published_age) >= 15
                self.assertEqual(read["state"] == "stale", expected)
                self.assertEqual(viewer.snapshot.stale(0, wall_now=EPOCH), expected)
                viewer.refresh()
                self.assertEqual(viewer.snapshot.stale(0, wall_now=EPOCH), expected)

    def test_schema_and_visibility_contract_remain_unchanged(self):
        doc = document()
        before = copy.deepcopy(doc)
        views(doc)
        visibility = worker_visibility.visibility(doc)
        self.assertEqual(doc, before)
        self.assertEqual(doc["schema"], "baton.v12.job-status/9")
        self.assertEqual(stack.SCHEMA, "baton.v12.stack/1")
        self.assertEqual(visibility["schema"], "baton.v12.worker-visibility/1")
        self.assertEqual(visibility["freshness"]["state"], "unknown")

    def test_shared_model_has_no_io_dependencies(self):
        import ast
        source = ast.parse(Path(model.__file__).read_text())
        imports = {alias.name for node in ast.walk(source) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {"datetime", "json", "math"})
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(source)))
        calls = {node.func.id for node in ast.walk(source) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue(calls.isdisjoint({"open", "exec", "eval", "__import__"}))

    def test_unrecognized_operations_are_not_relayed(self):
        doc = document()
        stage = doc["jobs"][0]["stages"][0]
        stage["exchange"]["states"] = [{"operation": "private-command", "state": "dispatched"}]
        self.assertEqual(model.stage_view(stage, NOW)["operation"], "unknown")
        for rendered in views(doc):
            self.assertNotIn("private-command", rendered)


class TheWorkerDeclaredEndingReachesBothSurfaces(unittest.TestCase):
    """W385424 -- an ending the worker declared, said in both views.

    THE MEASURED DEFECT: `just status` and `view` both printed "failed: stage
    ended exceptionally; cause unknown" for an ending whose sealed result
    named a provider timeout, a 3600-second bound and a verification that was
    never attempted -- and printed the same sentence for an earlier ending
    whose cause was a FAILED VERIFICATION. Distinct, host-known endings
    reported as one unknown.

    EVERY CASE RENDERS THROUGH `views`, so what is asserted is the two
    operator surfaces rather than the helper between them.
    """

    TIMEOUT = {"disposition": "unable", "declared_ending": "provider-failed",
               "failure_reason": "timeout", "seconds_bound": 3600,
               "seconds_bound_source": "job-default",
               "verification_attempted": False}
    FAILED = {"disposition": "unable",
              "declared_ending": "verification-failed",
              "verification_attempted": True, "verification_status": 1}

    @staticmethod
    def wrapped(members):
        return {name: ({"known": False, "value": None, "why": "fixture"}
                       if value is None else
                       {"known": True, "value": value, "source": "fixture"})
                for name, value in members.items()}

    def failing(self, declaration=None, **stage):
        doc = document()
        held = doc["jobs"][0]["stages"][0]
        held["state"] = "exceptional"
        held.update(stage)
        if declaration is not None:
            held["attempt_diagnostics"] = {
                "schema": "baton.v12.attempt-failure-cause/1",
                "attempt_id": held["attempt_id"],
                "worker_declaration": self.wrapped(declaration)}
        return doc

    def test_a_PROVIDER_TIMEOUT_is_attributable_in_BOTH_views(self):
        doc = self.failing(self.TIMEOUT)
        for rendered in views(doc):
            self.assertIn("worker declared unable: the provider did not "
                          "finish (provider timed out)", rendered)
            self.assertIn("1h00m provider bound (job-default)", rendered)
            self.assertIn("verification not attempted", rendered)
            self.assertNotIn("cause unknown", rendered)

    def test_an_UNKNOWN_verification_axis_renders_as_UNKNOWN_not_NOT_ATTEMPTED(self):
        """Review 2026-11-21T12-34-16Z [R2]: a result with no verification
        member reaches the views as an unknown axis, and the sentence says
        so rather than claiming nothing was attempted."""
        doc = self.failing(dict(self.TIMEOUT, verification_attempted=None,
                                verification_status=None))
        for rendered in views(doc):
            self.assertIn("whether verification ran is unknown", rendered)
            self.assertNotIn("verification not attempted", rendered)
            self.assertNotIn("cause unknown", rendered)

    def test_a_FAILED_VERIFICATION_reads_DIFFERENTLY_from_a_timeout(self):
        timeout = views(self.failing(self.TIMEOUT))
        failed = views(self.failing(self.FAILED))
        for rendered in failed:
            self.assertIn("worker declared unable: its own verification "
                          "command failed", rendered)
            self.assertIn("verification ended 1", rendered)
            self.assertNotIn("cause unknown", rendered)
            self.assertNotIn("provider timed out", rendered)
        self.assertNotEqual(timeout, failed)

    def test_NO_DECLARATION_keeps_the_HONEST_cause_unknown(self):
        for declaration in (None, {}, {"disposition": None}):
            for rendered in views(self.failing(declaration)):
                self.assertIn("cause unknown", rendered)
                self.assertNotIn("worker declared", rendered)

    def test_a_MANAGER_CANCELLED_or_COMPLETED_seal_SAYS_NOTHING_here(self):
        """A cancellation is the manager's own act and its facts are reported
        by the cancellation axis; this view does not speak for it."""
        for disposition in ("cancelled", "completed", "plan-rejected"):
            doc = self.failing(dict(self.TIMEOUT, disposition=disposition))
            for rendered in views(doc):
                self.assertIn("cause unknown", rendered)
                self.assertNotIn("worker declared", rendered)

    def test_an_UNKNOWN_DECLARED_ENDING_is_still_more_than_cause_unknown(self):
        doc = self.failing({"disposition": "unable", "declared_ending": None})
        for rendered in views(doc):
            self.assertIn("worker declared unable; its declared ending is "
                          "unknown", rendered)
            self.assertNotIn("cause unknown", rendered)

    def test_an_UNOWNED_WORD_or_a_SECRET_never_reaches_a_LINE(self):
        canary = "canary-" + "q" * 32
        doc = self.failing({"disposition": "unable",
                            "declared_ending": canary,
                            "failure_reason": canary,
                            "seconds_bound": canary,
                            "seconds_bound_source": canary,
                            "verification_attempted": canary,
                            "verification_status": canary})
        for rendered in views(doc):
            self.assertNotIn(canary, rendered)
            self.assertIn("its declared ending is unknown", rendered)

    def test_an_OUT_OF_RANGE_BOUND_or_STATUS_is_simply_not_rendered(self):
        doc = self.failing(dict(self.TIMEOUT, seconds_bound=10 ** 400))
        for rendered in views(doc):
            self.assertIn("provider timed out", rendered)
            self.assertNotIn("provider bound", rendered)

    def test_an_EXCHANGE_FAULT_KEEPS_ITS_PLACE_beside_the_declaration(self):
        doc = self.failing(self.TIMEOUT)
        doc["jobs"][0]["stages"][0]["exchange"]["terminal"] = {
            "ending": "faulted", "fault_code": "agent",
            "adapter_failure": {"component": "role-adapter",
                                "code": "role-output-missing"}}
        for rendered in views(doc):
            self.assertIn("agent fault; role-output-missing", rendered)
            self.assertIn("worker declared unable", rendered)

    def test_a_SUCCESSFUL_or_UNRELATED_STAGE_reads_EXACTLY_as_before(self):
        for state in ("running", "completed", "queued", "changes-requested"):
            plain = views(self.failing(None, state=state))
            declared = views(self.failing(self.TIMEOUT, state=state))
            self.assertEqual(plain, declared)
            for rendered in declared:
                self.assertNotIn("worker declared", rendered)

    def test_REPEATED_RENDERING_mutates_NOTHING(self):
        doc = self.failing(self.TIMEOUT)
        before = copy.deepcopy(doc)
        first, second = views(doc), views(doc)
        self.assertEqual(first, second)
        self.assertEqual(doc, before)

    def test_the_MIRRORED_DECLARATION_VOCABULARY_does_not_drift(self):
        from baton_v12.worker_manager import failure_cause
        from baton_v12.worker_manager import schema as manager_schema

        self.assertEqual(sorted(model._DECLARED_ENDINGS),
                         sorted(failure_cause.DECLARED_ENDINGS))
        self.assertEqual(sorted(model._DECLARED_FAILURE_REASONS),
                         sorted(failure_cause.DECLARED_FAILURE_REASONS))
        self.assertEqual(sorted(model._DECLARED_BOUND_SOURCES),
                         sorted(failure_cause.DECLARED_BOUND_SOURCES))
        self.assertIn(model._DECLARED_UNABLE, manager_schema.DISPOSITIONS)
        self.assertEqual(model._DECLARATION_MEMBER, "worker_declaration")


if __name__ == "__main__":
    unittest.main()
