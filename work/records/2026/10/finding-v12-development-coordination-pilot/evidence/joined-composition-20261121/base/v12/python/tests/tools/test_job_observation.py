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


if __name__ == "__main__":
    unittest.main()
