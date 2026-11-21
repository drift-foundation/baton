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


class Timing(unittest.TestCase):
    def job(self):
        return {"created_at": "2026-11-19T17:00:00Z", "control": {
            "timing": "trusted", "observed_at": NOW,
            "job": {"origin": "2026-11-19T17:00:00Z", "deadline_at": "2026-11-19T18:05:00Z"},
            "stages": [{"stage_id": "implementation", "origin": "2026-11-19T17:50:00Z", "deadline_at": "2026-11-19T18:01:00Z"}]}}

    def test_separate_age_unknown_runtime_and_partial_named_limit_in_all_views(self):
        doc = document(); job = doc["jobs"][0]; job.update(self.job())
        stage = job["stages"][0]; stage["episode"] = 0
        stage["episodes"] = [{"episode": 0, "opened_at": "2026-11-19T17:50:00Z"}]
        before = copy.deepcopy(doc)
        for rendered in views(doc):
            self.assertIn("Job age 1h00m", rendered)
            self.assertRegex(rendered, r"running\s+unknown")
            self.assertIn("stage timeout in 1m00s", rendered)
            self.assertIn("provider timing unknown (earliest known only)", rendered)
        self.assertEqual(doc, before)

    def test_blocked_episode_has_not_started(self):
        stage = {"state": "blocked", "stage_id": "review", "attempt_id": "future", "episode": 0,
                 "episodes": [{"episode": 0, "opened_at": "2026-11-19T17:00:00Z", "ended_at": None}]}
        view = model.stage_timing(stage, self.job(), NOW)
        self.assertEqual(view["running"], "not started")
        self.assertEqual(view["timeout"], "Job timeout in 5m00s")
        stage["episodes"][0]["ended_at"] = NOW
        self.assertEqual(model.stage_timing(stage, self.job(), NOW)["running"], "unknown")

    def test_ties_and_deadline_boundary_are_not_cessation(self):
        job = self.job(); job["control"]["job"]["deadline_at"] = "2026-11-19T18:01:00Z"
        stage = {"stage_id": "implementation", "state": "running"}
        for seconds in (59,60,61):
            observed = datetime.datetime.fromtimestamp(EPOCH+seconds, datetime.timezone.utc).isoformat()
            job["control"]["observed_at"] = observed
            view = model.stage_timing(stage, job, observed)
            self.assertEqual(view["limiting"], ["Job", "stage"])
            self.assertEqual(view["remaining_seconds"], max(0,60-seconds))
            if seconds >= 60:self.assertIn("cessation unconfirmed", view["timeout"])

    def test_unknown_future_stale_control_and_terminal(self):
        job = self.job(); stage = {"stage_id": "implementation", "state": "running"}
        for instant in ("bad", "2026-11-19T18:00:01Z", "2026-11-19T17:59:45Z"):
            job["control"]["observed_at"] = instant
            self.assertEqual(model.stage_timing(stage, job, NOW)["timeout"], "timeout unknown")
        self.assertIsNone(model._elapsed("2026-11-19T18:00:01Z", None, NOW))
        self.assertTrue(model.stale_ages(-1))
        stage["state"] = "completed"
        self.assertEqual(model.stage_timing(stage, job, NOW)["timeout"], "timeout not applicable (stage ended)")

    def test_retry_never_rebases_job_deadline_on_new_episode(self):
        job = self.job(); stage = {"state": "running", "stage_id": "implementation", "episode": 2,
                                  "episodes": [{"episode": 2, "opened_at": NOW}]}
        view = model.stage_timing(stage, job, NOW)
        self.assertEqual(view["running"], "unknown")
        self.assertEqual(view["remaining_seconds"], 60)
        self.assertEqual(view["job_age"], "1h00m")


class InvocationClocks(unittest.TestCase):
    job = Timing.job
    def stage(self):
        return {"stage_id":"implementation","state":"running","attempt_id":"new-attempt","exchange":{"command":{"sequence_id":"seq","command_digest":"digest"},"invocation":{"attempt_id":"new-attempt","operation":"work","scope":"provider-process","sequence_id":"seq","command_digest":"digest","started_at":"2026-11-19T17:59:30Z","deadline_at":"2026-11-19T18:00:30Z","ended_at":None}}}

    def test_provider_origin_and_continuation_do_not_rebase_job_limits(self):
        stage=self.stage();job=self.job();view=model.stage_timing(stage,job,NOW)
        self.assertEqual(view["running_seconds"],30);self.assertEqual(view["limiting"],["provider"]);self.assertEqual(view["remaining_seconds"],30);self.assertTrue(view["complete"])
        stage["exchange"]["invocation"].update(started_at="2026-11-19T17:59:50Z",deadline_at="2026-11-19T18:02:00Z")
        view=model.stage_timing(stage,job,NOW);self.assertEqual(view["running_seconds"],10);self.assertEqual(view["limiting"],["stage"]);self.assertEqual(view["remaining_seconds"],60)

    def test_terminal_duration_is_frozen_and_missing_end_unknown(self):
        stage=self.stage();stage["state"]="completed";fact=stage["exchange"]["invocation"]
        self.assertIsNone(model.stage_timing(stage,self.job(),NOW)["running_seconds"])
        fact["ended_at"]="2026-11-19T17:59:45Z"
        self.assertEqual(model.stage_timing(stage,self.job(),NOW)["running_seconds"],15)
        self.assertEqual(model.stage_timing(stage,self.job(),"2026-11-20T18:00:00Z")["running_seconds"],15)

    def test_wrong_attempt_future_start_and_malformed_end_are_unknown(self):
        for key,value in (("attempt_id","old-attempt"),("started_at","2026-11-19T18:00:01Z"),("ended_at","bad")):
            stage=self.stage();stage["exchange"]["invocation"][key]=value
            view=model.stage_timing(stage,self.job(),NOW);self.assertIsNone(view["running_seconds"]);self.assertIn("provider timing unknown",view["timeout"])

    def test_expired_provider_is_not_termination_and_partial_control_stays_qualified(self):
        stage=self.stage();stage["exchange"]["invocation"]["deadline_at"]=NOW
        view=model.stage_timing(stage,self.job(),NOW);self.assertEqual(view["remaining_seconds"],0);self.assertIn("cessation unconfirmed",view["timeout"])
        view=model.stage_timing(self.stage(),{},NOW);self.assertEqual(view["limiting"],["provider"]);self.assertFalse(view["complete"]);self.assertIn("Job/stage timing unknown",view["timeout"])
