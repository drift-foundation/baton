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
                                  "state": "running", "attempt_id": "attempt-a", "episode": 1,
                                  "episodes": [{"episode": 1, "attempt_id": "attempt-a"}],
                                  "allocation": {"episode": 1, "assignment_id": "attempt-a"},
                                  "runtime": {"activity": {"attempt_id": "attempt-a", "bytes_observed": 0,
                                                           "observed_at": "2026-11-19T17:59:00.000Z"}},
                                  "exchange": {"states": [{"operation": "work", "state": "dispatched"}]}}]}]}


def views(doc):
    output = io.StringIO()
    stack._print_job_outcomes({"state": "fresh", "canonical": True, "document": doc}, output)
    snapshot = job_viewer.read_snapshot(doc, received_at=0)
    return output.getvalue(), "\n".join(job_viewer.render_list(snapshot, now=0, wall_now=EPOCH)), "\n".join(job_viewer.render_detail(snapshot, "job-a", now=0, wall_now=EPOCH))


class SharedObservation(unittest.TestCase):
    def test_attribution_holds_name_typed_cause_and_owner_action_on_all_views(self):
        for cause in ("model-attribution-missing", "model-attribution-conflicting", "model-attribution-invalid"):
            doc = document()
            stage = doc["jobs"][0]["stages"][0]
            stage["state"] = "answering"
            stage["runtime"]["model_attribution_hold"] = cause
            for rendered in views(doc):
                self.assertIn(cause + "; owner action needed", rendered)
    def test_shared_outcomes_gates_and_typed_failure(self):
        for state, outcome in (("running", "IN PROGRESS"), ("completed", "UNKNOWN"), ("queued", "QUEUED"), ("changes-requested", "CHANGES REQUESTED"), ("exceptional", "FAILED"), ("blocked", "BLOCKED"), ("unrecognized", "UNKNOWN")):
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
            self.assertRegex(rendered, r"duration\s+unknown")
            self.assertIn("stage timeout in 1m00s", rendered)
            self.assertNotIn("provider", rendered)
        self.assertEqual(doc, before)

    def test_blocked_episode_has_unknown_start(self):
        stage = {"state": "blocked", "stage_id": "review", "attempt_id": "future", "episode": 0,
                 "episodes": [{"episode": 0, "opened_at": "2026-11-19T17:00:00Z", "ended_at": None}]}
        view = model.stage_timing(stage, self.job(), NOW)
        self.assertEqual(view["running"], "unknown")
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


class TheFailureCauseAndTimingShareOneStageLine(unittest.TestCase):
    """Joined composition (W385427 + W385424 over 7ac02c7f): one stage line
    carries BOTH the worker-declared ending and the attributed invocation
    timing on every shared surface, each in its own words, neither displacing
    the other."""

    def test_a_declared_timeout_and_its_frozen_invocation_render_together(self):
        declared = TheWorkerDeclaredEndingReachesBothSurfaces(
            "test_a_PROVIDER_TIMEOUT_is_attributable_in_BOTH_views")
        doc = declared.failing(declared.TIMEOUT)
        job = doc["jobs"][0]; job.update(Timing.job(None))
        stage = job["stages"][0]
        fact = InvocationClocks.stage(None)
        stage["attempt_id"] = fact["attempt_id"]
        stage["episodes"][0]["attempt_id"] = fact["attempt_id"]
        stage["allocation"]["assignment_id"] = fact["attempt_id"]
        if stage.get("attempt_diagnostics"):
            stage["attempt_diagnostics"]["attempt_id"] = fact["attempt_id"]
        stage.setdefault("exchange", {}).update(fact["exchange"])
        stage["exchange"]["invocation"]["ended_at"] = "2026-11-19T17:59:45Z"
        before = copy.deepcopy(doc)
        for rendered in views(doc):
            self.assertIn("worker declared unable: the provider did not finish (provider timed out)", rendered)
            self.assertIn("verification not attempted", rendered)
            self.assertNotIn("cause unknown", rendered)
            # W385431: the frozen figure, labelled for what it is. The
            # invocation recorded an ending, so no surface says `running`.
            self.assertIn("provider ran 15s", rendered)
            self.assertNotRegex(rendered, r"running\s+15s")
            self.assertIn("timeout not applicable (stage ended)", rendered)
            self.assertIn("Job age 1h00m", rendered)
        self.assertEqual(doc, before)

    def test_an_unknown_declaration_and_unknown_timing_stay_two_unknowns(self):
        declared = TheWorkerDeclaredEndingReachesBothSurfaces(
            "test_a_PROVIDER_TIMEOUT_is_attributable_in_BOTH_views")
        doc = declared.failing(dict(declared.TIMEOUT, verification_attempted=None,
                                    verification_status=None))
        doc["jobs"][0].update(Timing.job(None))
        for rendered in views(doc):
            self.assertIn("whether verification ran is unknown", rendered)
            self.assertRegex(rendered, r"duration\s+unknown")
            self.assertIn("timeout not applicable (stage ended)", rendered)


class AnEndedInvocationIsNotARunningOne(unittest.TestCase):
    """W385431 -- the frozen provider duration, labelled for what it is.

    THE DEFECT, on all three shared surfaces at once. The worker records the
    provider PROCESS's own `ended_at` when that process exits and THEN runs
    its verification command, so between those two facts the invocation
    duration has stopped moving while the stage is genuinely still open --
    and `just status`, the viewer list and the viewer detail all printed
    `running 15s`. The figure was frozen, the word said live, and the pair got
    more convincing with time, exactly as a relative activity age beside a
    terminal stage does.

    WHAT IS ASSERTED IS THE SURFACES. Every case renders through `views`, so
    the subject is the two operator surfaces and their shared viewer rather
    than the helper between them, and each case asserts the word that was
    WRONG is absent rather than merely leaving it unasserted.

    AND AN HONEST LABEL IS NOT AN OUTCOME. `provider ran 15s` says a process
    ended; it does not say the stage or the Job ended, completed, succeeded or
    was accepted, and the state, timeout, reason and activity axes beside it
    keep reporting exactly what they did.
    """

    ENDED = "2026-11-19T17:59:45Z"
    OPEN_NOTE = ("provider invocation ended after 15s; "
                 "this stage has not ended")

    def staged(self, *, state="running", invocation=True, **spoiled):
        """One Job whose stage carries an attributed provider invocation.

        The fixtures are the ones the existing cases use: `Timing.job`'s
        admitted Job/stage deadlines and `InvocationClocks.stage`'s attributed
        provider process, which starts 30s before this observation.
        """
        doc = document()
        job = doc["jobs"][0]
        job.update(Timing.job(None))
        stage = job["stages"][0]
        fact = InvocationClocks.stage(None)
        stage["state"] = state
        stage["attempt_id"] = fact["attempt_id"]
        stage["episodes"][0]["attempt_id"] = fact["attempt_id"]
        stage["allocation"]["assignment_id"] = fact["attempt_id"]
        if stage.get("attempt_diagnostics"):
            stage["attempt_diagnostics"]["attempt_id"] = fact["attempt_id"]
        stage["exchange"].update(fact["exchange"])
        if invocation:
            stage["exchange"]["invocation"].update(spoiled)
        else:
            stage["exchange"]["invocation"] = None
        return doc, stage, job

    # -- an ACTIVE invocation, unchanged -----------------------------------

    def test_an_ACTIVE_invocation_keeps_RUNNING_and_a_FIGURE_THAT_MOVES(self):
        doc, stage, job = self.staged()
        view = model.stage_timing(stage, job, NOW)
        self.assertEqual(view["invocation"], "active")
        self.assertEqual(view["running_seconds"], 30)
        self.assertEqual(view["duration"], "running 30s")
        self.assertIsNone(view["duration_note"])
        before = copy.deepcopy(doc)
        for rendered in views(doc):
            self.assertRegex(rendered, r"running\s+30s")
            self.assertNotIn("provider ran", rendered)
            self.assertNotIn("has not ended", rendered)
            # THE PROVIDER'S OWN DEADLINE STILL LIMITS A LIVE PROCESS.
            self.assertIn("provider timeout in 30s", rendered)
            self.assertIn("Job age 1h00m", rendered)
        self.assertEqual(doc, before)
        # AND IT MOVES, because nothing has frozen it: ten seconds later on the
        # manager's own clock the figure is ten seconds larger. That is the
        # property the ended case must NOT have.
        later = model.stage_timing(stage, job, "2026-11-19T18:00:10.000Z")
        self.assertEqual(later["duration"], "running 40s")

    # -- an ENDED invocation under a stage that has NOT ended --------------

    def test_an_ENDED_invocation_under_an_OPEN_stage_SAYS_SO_everywhere(self):
        """The measured defect, across the states a stage is in while the
        worker's own verification is still running."""
        for state in ("running", "reviewing", "integrating", "answering"):
            with self.subTest(state=state):
                doc, stage, job = self.staged(state=state, ended_at=self.ENDED)
                view = model.stage_timing(stage, job, NOW)
                self.assertEqual(view["invocation"], "ended")
                self.assertEqual(view["running_seconds"], 15)
                self.assertEqual(view["duration"], "provider ran 15s")
                self.assertEqual(view["duration_note"], self.OPEN_NOTE)
                for rendered in views(doc):
                    self.assertIn("provider ran 15s", rendered)
                    self.assertIn(self.OPEN_NOTE, rendered)
                    # THE WORD THAT WAS WRONG.
                    self.assertNotRegex(rendered, r"running\s+15s")
                    # AND NOTHING HERE PROMOTES IT TO AN OUTCOME: the Job is
                    # still in progress, the stage is still under its own
                    # deadline, and no acceptance is claimed.
                    self.assertIn("IN PROGRESS", rendered)
                    self.assertIn("stage timeout in 1m00s", rendered)
                    self.assertNotIn("COMPLETED", rendered)
                    self.assertNotIn("timeout not applicable", rendered)
                    self.assertNotIn("accepted", rendered)

    def test_the_FROZEN_figure_does_not_grow_while_nothing_runs(self):
        """The reason the word mattered. An ended invocation's figure is the
        same an hour later; a label saying `running` beside it would have been
        getting steadily more wrong."""
        doc, stage, job = self.staged(ended_at=self.ENDED)
        for observed in (NOW, "2026-11-19T18:05:00.000Z",
                         "2026-11-20T18:00:00.000Z"):
            with self.subTest(observed=observed):
                view = model.stage_timing(stage, job, observed)
                self.assertEqual(view["running_seconds"], 15)
                self.assertEqual(view["duration"], "provider ran 15s")
                self.assertEqual(view["ended_at"], self.ENDED)
        # AND A CONTROL READING NOBODY REFRESHED IS STILL UNKNOWN TIMING, by
        # the same 15-second rule: an honest duration label does not make a
        # stale deadline current.
        stale = model.stage_timing(stage, job, "2026-11-19T18:05:00.000Z")
        self.assertEqual(stale["timeout"], "timeout unknown")
        self.assertEqual(stale["deadlines"], [])

    def test_the_ENDED_PROVIDER_DEADLINE_no_longer_limits_the_stage(self):
        """An ended process cannot time out, and the stage's own admitted
        deadline is what remains."""
        doc, stage, job = self.staged(ended_at=self.ENDED)
        view = model.stage_timing(stage, job, NOW)
        self.assertEqual(view["limiting"], ["stage"])
        self.assertTrue(view["complete"])
        self.assertEqual(view["timeout"], "stage timeout in 1m00s")
        for rendered in views(doc):
            self.assertNotIn("provider timeout", rendered)
            self.assertNotIn("provider timing unknown", rendered)

    # -- a TERMINAL stage --------------------------------------------------

    def test_a_TERMINAL_stage_keeps_its_frozen_duration_and_owes_no_NOTE(self):
        """The stage state and `timeout not applicable (stage ended)` already
        say the stage ended, so the open-stage sentence would be false."""
        for state in ("completed", "exceptional", "changes-requested"):
            with self.subTest(state=state):
                doc, stage, job = self.staged(state=state, ended_at=self.ENDED)
                view = model.stage_timing(stage, job, NOW)
                self.assertEqual(view["invocation"], "ended")
                self.assertEqual(view["duration"], "provider ran 15s")
                self.assertIsNone(view["duration_note"])
                self.assertEqual(view["timeout"],
                                 "timeout not applicable (stage ended)")
                for rendered in views(doc):
                    self.assertIn("provider ran 15s", rendered)
                    self.assertNotRegex(rendered, r"running\s+15s")
                    self.assertNotIn("has not ended", rendered)

    def test_a_TERMINAL_stage_with_NO_RECORDED_END_stays_unknown(self):
        """A terminal stage whose invocation never recorded an ending has no
        duration to report, and an invented one is the thing this view
        refuses everywhere else."""
        doc, stage, job = self.staged(state="completed")
        view = model.stage_timing(stage, job, NOW)
        self.assertIsNone(view["invocation"])
        self.assertIsNone(view["running_seconds"])
        self.assertEqual(view["duration"], "duration unknown")
        self.assertIsNone(view["duration_note"])
        for rendered in views(doc):
            self.assertRegex(rendered, r"duration\s+unknown")
            self.assertNotIn("provider ran", rendered)

    # -- missing and unqualified timing ------------------------------------

    def test_MISSING_FOREIGN_FUTURE_and_MALFORMED_timing_gain_NO_label(self):
        """Every qualification that already answered `unknown` still answers
        `unknown`, and none of them acquires a past tense."""
        spoiled = {"no invocation at all": {"invocation": False},
                   "a foreign attempt": {"attempt_id": "retired-attempt"},
                   "a start in the future": {"started_at": "2026-11-19T18:00:01Z"},
                   "a malformed ending": {"ended_at": "bad"},
                   "an ending before its start": {"ended_at": "2026-11-19T17:59:00Z"},
                   "an ending after the observation": {"ended_at": "2026-11-19T18:00:01Z"},
                   "another scope": {"scope": "dispatch"},
                   "another operation": {"operation": "describe"},
                   "another command": {"command_digest": "sha256:" + "a" * 64},
                   "another sequence": {"sequence_id": "other-sequence"}}
        for why, members in spoiled.items():
            with self.subTest(why=why):
                doc, stage, job = self.staged(**members)
                view = model.stage_timing(stage, job, NOW)
                self.assertIsNone(view["invocation"])
                self.assertIsNone(view["running_seconds"])
                self.assertEqual(view["running"], "unknown")
                self.assertEqual(view["duration"], "duration unknown")
                self.assertIsNone(view["duration_note"])
                if members.get("invocation") is False:
                    self.assertNotIn("provider", view["timeout"])
                else:
                    self.assertIn("provider timing unknown (earliest known only)", view["timeout"])
                for rendered in views(doc):
                    self.assertRegex(rendered, r"duration\s+unknown")
                    self.assertNotIn("provider ran", rendered)
                    self.assertNotIn("has not ended", rendered)

    def test_a_planned_stage_has_UNKNOWN_start(self):
        doc = document()
        job = doc["jobs"][0]
        job.update(Timing.job(None))
        job["stages"] = [{"stage_id": "implementation",
                          "kind": "implementation", "state": "queued"}]
        view = model.stage_timing(job["stages"][0], job, NOW)
        self.assertIsNone(view["invocation"])
        self.assertEqual(view["duration"], "duration unknown")
        self.assertIsNone(view["duration_note"])
        for rendered in views(doc):
            self.assertIn("duration unknown", rendered)
            self.assertNotIn("not started", rendered)
            self.assertNotIn("provider ran", rendered)
            self.assertNotRegex(rendered, r"running\s+\d")

    # -- the three surfaces, word for word ---------------------------------

    def test_STATUS_MONITOR_and_VIEWER_agree_WORD_FOR_WORD(self):
        """One interpretation and no second wording. A surface that composed
        its own label is a surface that can disagree with the other two on the
        day it matters."""
        for state, members, expected in (
                ("running", {}, "running 30s"),
                ("running", {"ended_at": self.ENDED}, "provider ran 15s"),
                ("completed", {"ended_at": self.ENDED}, "provider ran 15s"),
                ("running", {"ended_at": "bad"}, "duration unknown")):
            with self.subTest(expected=expected, state=state):
                doc, stage, job = self.staged(state=state, **members)
                self.assertEqual(model.stage_timing(stage, job, NOW)["duration"],
                                 expected)
                for rendered in views(doc):
                    self.assertIn(expected, rendered)
                    for other in ("running 30s", "provider ran 15s",
                                  "duration unknown"):
                        if other != expected:
                            self.assertNotIn(other, rendered)

    def test_the_LIST_COLUMNS_keep_the_STAGE_ID_and_the_BANNER_its_AGE(self):
        """Review R1's rule, held for the sentence this correction adds: the
        variable-width fact goes on a continuation line, the fixed columns
        keep the identity an operator opened the list to copy, and the
        15-second freshness rule is untouched."""
        doc, stage, job = self.staged(ended_at=self.ENDED)
        status_text, listed, detail = views(doc)
        for rendered in (status_text, listed, detail):
            self.assertEqual(rendered.count("provider ran 15s"), 1)
            self.assertIn(self.OPEN_NOTE, rendered)
            self.assertNotIn("STALE", rendered)
        row = next(one for one in listed.splitlines()
                   if one.startswith("  implementation"))
        self.assertLessEqual(len(row), 100)
        self.assertTrue(row.endswith("implementation"))
        self.assertIn("duration     provider ran 15s", detail)
        # THE SAME DOCUMENT, UNREFRESHED, IS STILL CONSPICUOUSLY STALE.
        snapshot = job_viewer.read_snapshot(doc, received_at=0)
        stale = "\n".join(job_viewer.render_list(
            snapshot, now=0, wall_now=EPOCH + model.STALE_SECONDS))
        self.assertIn("!! STALE", stale)
        self.assertIn("provider ran 15s", stale)
        self.assertIn(self.OPEN_NOTE, stale)

    def test_the_WORKER_DECLARED_CAUSE_still_reaches_an_OPEN_stage_line(self):
        """The axes do not displace each other. A stage whose provider
        invocation ended and whose diagnostics carry a declaration renders
        both, and neither becomes the other's explanation."""
        declared = TheWorkerDeclaredEndingReachesBothSurfaces(
            "test_a_PROVIDER_TIMEOUT_is_attributable_in_BOTH_views")
        doc, stage, job = self.staged(state="exceptional",
                                      ended_at=self.ENDED)
        stage["attempt_diagnostics"] = {
            "schema": "baton.v12.attempt-failure-cause/1",
            "attempt_id": stage["attempt_id"],
            "worker_declaration": declared.wrapped(declared.FAILED)}
        for rendered in views(doc):
            self.assertIn("provider ran 15s", rendered)
            self.assertIn("worker declared unable: its own verification "
                          "command failed", rendered)
            self.assertIn("verification ended 1", rendered)
            self.assertNotIn("cause unknown", rendered)
            self.assertNotRegex(rendered, r"running\s+15s")



class A1Contract(unittest.TestCase):
    """§6's numbered behaviours on status, monitor list and monitor detail.

    Synthetic documents model published evidence, never owner receipts from a
    live run. The four byte-identical retained documents have a local manifest.
    """

    def fixture(self, state="running", admitted=True):
        doc = document()
        stage = doc["jobs"][0]["stages"][0]
        stage.update(state=state, runtime=None, exchange=None, receipts=[],
                     offer_id="reserved-offer", artifacts=[])
        if admitted:
            stage["allocation"].update(worker_id="worker-a", participant="participant-a",
                                       allocation_state="reserved", release_reason=None)
        else:
            stage.pop("allocation")
        return doc, stage

    def check(self, doc, present=(), absent=()):
        before = copy.deepcopy(doc)
        rendered = views(doc)
        for index, text in enumerate(rendered):
            with self.subTest(surface=("status", "list", "detail")[index]):
                for word in present:
                    self.assertIn(word, text)
                for word in absent:
                    self.assertNotIn(word, text)
        self.assertEqual(doc, before, "interpretation must be pure")
        return rendered

    def receipt(self, act, state="performed", result=None, **detail):
        return {"episode": 1, "act": act, "state": state,
                "detail": {"result": result, **detail}}

    def cancel(self, doc, state, attempt="attempt-a", episode=1):
        target = {"stage_id": "implementation", "episode": episode,
                  "attempt_id": attempt, "state": state}
        doc["jobs"][0]["cancellation"] = {"trigger": "operator", "shutdown": "unresolved",
                                         "targets": [target]}
        return target

    def invocation(self, stage):
        stage["exchange"] = copy.deepcopy(InvocationClocks.stage(None)["exchange"])
        stage["exchange"]["invocation"]["attempt_id"] = "attempt-a"
        return stage["exchange"]["invocation"]

    def diagnostic(self, stage, **members):
        stage["attempt_diagnostics"] = {"schema": "baton.v12.attempt-failure-cause/1",
                                        "attempt_id": "attempt-a", **members}
        return stage["attempt_diagnostics"]

    def test_01_allocation_admits_exact_episode_and_attempt(self):
        doc, stage = self.fixture()
        self.check(doc, ("admission admitted", "attempt 1 attempt-a", "reserved on worker-a"))
        for key, value in (("episode", 2), ("episode", True), ("assignment_id", "foreign"), ("assignment_id", None)):
            changed = copy.deepcopy(doc)
            changed["jobs"][0]["stages"][0]["allocation"][key] = value
            self.check(changed, ("admission unknown",), ("attempt 1 attempt-a", "reserved on worker-a"))

    def test_02_only_committed_live_admission_receipt_admits(self):
        for state in ("performed", "adopted"):
            doc, stage = self.fixture(admitted=False)
            stage["receipts"] = [self.receipt("admit", state, canonical_state="committed")]
            self.check(doc, ("admission admitted", "attempt 1 attempt-a", "offered"))
            for key, value in (("episode", 2), ("episode", None), ("detail", {"canonical_state": "pending"})):
                changed = copy.deepcopy(doc)
                changed["jobs"][0]["stages"][0]["receipts"][0][key] = value
                self.check(changed, ("admission unknown",), ("attempt 1 attempt-a", "offered"))

    def test_03_claimed_receipt_alone_admits(self):
        doc, stage = self.fixture(admitted=False)
        stage["receipts"] = [self.receipt("claim", result={"state": "claimed"})]
        self.check(doc, ("admission admitted", "attempt 1 attempt-a", "claimed"), ("reserved on",))

    def test_04_ending_is_not_admission(self):
        doc, stage = self.fixture("completed", admitted=False)
        stage["episodes"][0].update(ended_state="completed", ended_at=NOW)
        text = self.check(doc, ("admission unknown",), ("attempt 1 attempt-a",))
        self.assertIn("reserved identity — admission unknown", text[2])

    def test_05_refused_offer_is_a_fact_not_admission(self):
        doc, stage = self.fixture(admitted=False)
        stage["receipts"] = [self.receipt("admit", "refused")]
        self.check(doc, ("offer refused", "admission unknown"), ("attempt 1 attempt-a", "admission not admitted"))

    def test_06_claim_ending_does_not_admit(self):
        for ending in ("declined", "expired", "abandoned-after-restart", "claim-refused", "settlement-expired"):
            doc, stage = self.fixture(admitted=False)
            stage["receipts"] = [self.receipt("claim", result={"state": ending})]
            self.check(doc, ("claim not obtained: " + ending, "admission unknown"), ("attempt 1 attempt-a",))

    def test_07_blocked_is_planned_with_unknown_admission(self):
        doc, stage = self.fixture("blocked", admitted=False)
        stage["gates"] = [{"open": False, "stage_id": "dependency", "state": "running"}]
        output = self.check(doc, ("planned — waiting on dependency", "admission unknown", "duration unknown"),
                            ("attempt-a", "reserved-offer", "never admitted", "not started"))
        self.assertNotIn("reserved identity", output[0])
        self.assertNotIn("reserved identity", output[1])
        self.assertIn("reserved identity — admission unknown", output[2])

    def test_08_queued_is_ready_not_running(self):
        doc, stage = self.fixture("queued", admitted=False)
        self.check(doc, ("ready; admission unknown", "duration unknown"), ("running", "attempt-a", "not started", "no attempt in progress"))

    def test_09_noncanonical_does_not_change_evidence(self):
        doc, stage = self.fixture("blocked", admitted=False)
        doc["canonical"] = False
        outputs = self.check(doc, ("planned — waiting on unknown; admission unknown",), ("attempt-a", "not started"))
        for text in outputs[1:]:
            self.assertIn("manager was NOT read", text)
        self.assertEqual(model.job_view(doc, doc["jobs"][0]), model.job_view(dict(doc, canonical=True), doc["jobs"][0]))

    def test_10_retired_target_is_positive_nonadmission(self):
        doc, stage = self.fixture("blocked", admitted=False)
        target = self.cancel(doc, "retired-before-admission")
        self.check(doc, ("admission not admitted",), ("stopped", "stopping", "attempt 1 attempt-a"))
        for key in ("attempt_id", "episode", "stage_id"):
            changed = copy.deepcopy(doc)
            changed["jobs"][0]["cancellation"]["targets"][0][key] = None
            self.check(changed, ("admission unknown",), ("admission not admitted",))

    def test_11_all_execution_states_require_admission(self):
        for state in ("offered", "claimed", "starting", "waiting", "running", "reviewing", "integrating", "answering", "awaiting-answer", "answered", "changes-requested", "completed", "exceptional"):
            doc, stage = self.fixture(state, admitted=False)
            self.check(doc, ("unknown (reported state: " + state + ")",), ("attempt 1 attempt-a",))

    def test_12_done_requires_admission(self):
        doc, stage = self.fixture("completed")
        self.check(doc, ("done; admission admitted",))
        stage.pop("allocation")
        self.check(doc, ("unknown (reported state: completed)",), ("done;",))

    def test_13_live_facts_are_independent(self):
        cases = [({"runtime": {"runtime_id": "runtime-a"}}, "runtime recorded: runtime-a"),
                 ({"runtime": {"execution_runtime": "active"}}, "runtime recorded: active"),
                 ({"receipts": [self.receipt("admit", canonical_state="committed")]}, "offered"),
                 ({"receipts": [self.receipt("claim", result={"state": "claimed"})]}, "claimed"),
                 ({"receipts": [self.receipt("admit", "refused")]}, "offer refused"),
                 ({"receipts": [self.receipt("claim", result={"state": "expired"})]}, "claim not obtained: expired"),
                 ({"exchange": {"receipt": {"accepted_at": NOW}}}, "command accepted (reported)"),
                 ({"exchange": {"states": [{"operation": "work", "state": "answered"}]}}, "work answered (reported; attempt association unverified)")]
        for members, expected in cases:
            doc, stage = self.fixture()
            stage.update(members)
            others = [word for _, word in cases if word != expected and word != "offered"]
            self.check(doc, (expected,), tuple(others) + ("execution started", "provider started"))

    def test_14_runtime_is_recorded_not_started(self):
        doc, stage = self.fixture()
        stage["runtime"] = {"runtime_id": "runtime-a"}
        self.check(doc, ("runtime recorded: runtime-a",), ("started", "running"))

    def test_15_recorded_failed_start(self):
        doc, stage = self.fixture()
        stage["runtime"] = {"runtime_id": "runtime-a"}
        self.diagnostic(stage, start_failure_recorded={"known": True, "value": True})
        self.check(doc, ("runtime start failed", "runtime recorded: runtime-a"), ("execution started",))

    def test_16_acceptance_is_not_start(self):
        doc, stage = self.fixture()
        stage["exchange"] = {"receipt": {"accepted_at": NOW}}
        self.check(doc, ("command accepted (reported) at " + NOW, "duration unknown"), ("started", "running", "provider"))

    def test_17_dispatch_is_reported_not_start(self):
        doc, stage = self.fixture()
        stage["exchange"] = {"receipt": {"accepted_at": NOW}, "states": [{"operation": "work", "state": "dispatched"}]}
        self.check(doc, ("command accepted (reported)", "work dispatched (reported; attempt association unverified)"), ("execution started", "provider started"))

    def test_18_nonprovider_integration_has_no_start_fact(self):
        doc, stage = self.fixture("integrating")
        stage.update(kind="integration", artifacts=[{"output_name": "integration-result", "locator": "file:///result"}],
                     exchange={"receipt": {"accepted_at": NOW}, "states": [{"operation": "work", "state": "answered"}]})
        self.check(doc, ("command accepted (reported)", "work answered (reported; attempt association unverified)", "result recorded: integration-result", "duration unknown"),
                   ("execution started", "provider", "not started"))

    def test_19_valid_invocation_proves_both_starts(self):
        doc, stage = self.fixture()
        invocation = self.invocation(stage)
        self.check(doc, ("execution started", "provider started", "running 30s"), ("command accepted",))
        stage["state"] = "completed"
        self.check(doc, ("execution started", "provider started", "duration unknown"))
        stage["state"] = "running"
        invocation["ended_at"] = "2026-11-19T17:59:45Z"
        self.check(doc, ("execution started", "provider started", "provider ran 15s"), ("running 15s",))

    def test_20_each_invalid_binding_keeps_acceptance_independent(self):
        for key, value in (("attempt_id", "foreign"), ("attempt_id", None), ("scope", "other"), ("operation", "describe"),
                           ("command_digest", "foreign"), ("command_digest", None), ("sequence_id", "foreign"), ("sequence_id", None), ("started_at", "bad"),
                           ("started_at", "2026-11-19T18:00:01Z"), ("deadline_at", "2026-11-19T17:00:00Z"),
                           ("ended_at", "bad"), ("ended_at", "2026-11-19T17:00:00Z"), ("ended_at", "2026-11-19T18:00:01Z")):
            doc, stage = self.fixture()
            self.invocation(stage)[key] = value
            stage["exchange"]["receipt"] = {"accepted_at": NOW}
            self.check(doc, ("command accepted (reported)", "execution start unknown", "duration unknown"), ("execution started", "provider started"))

    def test_21_observations_are_not_provider_evidence(self):
        doc, stage = self.fixture()
        stage.update(runtime={"activity": {"attempt_id": "attempt-a", "bytes_observed": 12, "observed_at": NOW}},
                     artifacts=[{"output_name": "candidate"}])
        self.check(doc, ("12 B", "result recorded: candidate"), ("provider", "model ran", "execution started"))

    def test_22_every_stop_target_word(self):
        for state, word in (("pending", "stopping (pending)"), ("awaiting-offer-lapse", "stopping (awaiting-offer-lapse)"),
                            ("ordered", "stopping (ordered)"), ("order-failed", "stopping (order-failed)"),
                            ("ending-in-progress", "stopping (ending-in-progress)"), ("held-unknown", "stopping (held-unknown)"),
                            ("ceased", "stopped"), ("fenced-unstarted", "cancelled before start")):
            doc, stage = self.fixture("exceptional")
            self.cancel(doc, state)
            self.check(doc, (word,), ("failed; admission", "failed — stopping"))
        doc, stage = self.fixture("completed")
        self.cancel(doc, "ended-before-request")
        self.check(doc, ("done; admission admitted",), ("stopped", "stopping", "cancelled before start"))

    def test_23_running_order_is_in_progress_stopping(self):
        doc, stage = self.fixture()
        self.cancel(doc, "ordered")
        self.check(doc, ("in progress — stopping (ordered)",), ("stopped",))

    def test_24_exceptional_has_unchanged_reason(self):
        doc, stage = self.fixture("exceptional")
        stage["exchange"] = {"terminal": {"ending": "faulted", "fault_code": "agent", "adapter_failure": {"component": "role-adapter", "code": "role-output-missing"}}}
        self.check(doc, ("failed; admission admitted", "agent fault; role-output-missing"), ("stopped",))

    def test_25_earlier_stop_never_labels_live_attempt(self):
        doc, stage = self.fixture()
        stage["episode"] = 2
        stage["episodes"][0]["episode"] = 2
        stage["allocation"]["episode"] = 2
        stage["episodes"].insert(0, {"episode": 1, "attempt_id": "older", "ended_state": "exceptional", "ended_at": NOW})
        stage["allocations"] = [{"episode": 1, "assignment_id": "older"}]
        self.cancel(doc, "ceased", "older", 1)
        outputs = self.check(doc, ("in progress; admission admitted", "attempt 1 older — stopped", "attempt 2 attempt-a"))
        for output in outputs:
            live = next(line for line in output.splitlines() if "attempt 2 attempt-a" in line)
            self.assertNotIn("stopped", live)

    def test_26_diagnostics_must_name_this_attempt(self):
        for identity in ("foreign", None):
            doc, stage = self.fixture("exceptional")
            diagnostic = self.diagnostic(stage, start_failure_recorded={"known": True, "value": True},
                                         cause={"outcome": {"known": True, "value": "ceased-absent"}},
                                         worker_declaration={"disposition": {"known": True, "value": "unable"}})
            diagnostic["attempt_id"] = identity
            self.check(doc, ("failed; admission admitted", "cause unknown"), ("stopped", "runtime start failed", "worker declared"))
        doc, stage = self.fixture("exceptional")
        self.diagnostic(stage, cause={"outcome": {"known": True, "value": "ceased-quiescent"}})
        self.check(doc, ("stopped; admission admitted",))

    def test_27_no_cessation_from_elapsed_time_or_order(self):
        for state in ("running", "exceptional", "completed"):
            doc, stage = self.fixture(state)
            self.cancel(doc, "ordered")
            doc["jobs"][0]["cancellation"].update(shutdown_bound_seconds=120, elapsed_seconds=999, shutdown="unresolved")
            self.diagnostic(stage, cause={"outcome": {"known": True, "value": "ordered"}})
            self.check(doc, ("stopping (ordered)",), ("stopped",))

    def test_28_cancelled_before_start_is_on_attempt_not_job(self):
        doc, stage = self.fixture("exceptional")
        self.cancel(doc, "fenced-unstarted")
        outputs = self.check(doc, ("attempt 1 attempt-a — cancelled before start",))
        self.assertIn("Cancellation: operator; shutdown unresolved", outputs[0])
        self.assertNotIn("Job job-a: cancelled before start", outputs[0])

    def test_29_answer_positions_and_job_outcomes_are_known(self):
        for state, words, outcome in (("awaiting-answer", "waiting for an answer", "WAITING FOR AN ANSWER"), ("answered", "answered — held", "ANSWERED — HELD")):
            doc, stage = self.fixture(state)
            self.check(doc, (words + "; admission admitted", outcome), ("UNKNOWN",))

    def test_30_history_shows_only_published_historical_facts(self):
        doc, stage = self.fixture()
        stage["episode"] = 4
        stage["episodes"][0]["episode"] = 4
        stage["allocation"]["episode"] = 4
        stage["episodes"][:0] = [{"episode": 1, "attempt_id": "old-a", "ended_state": "changes-requested", "ended_at": NOW},
                                 {"episode": 2, "attempt_id": "old-b"}, {"episode": 3, "attempt_id": "reserved-old"}]
        stage["allocations"] = [{"episode": n, "assignment_id": identity, "worker_id": "old-worker", "participant": "old-participant", "allocation_state": "released", "release_reason": "cleanup-retained"} for n, identity in ((1, "old-a"), (2, "old-b"))]
        outputs = self.check(doc, ("attempt 1 old-a", "attempt 2 old-b", "worker old-worker; participant old-participant", "allocation released; release reason cleanup-retained", "ending changes-requested at " + NOW, "no ending recorded", "other facts unknown"), ("reserved-old",))
        self.assertIn("3 admitted attempt(s)", outputs[1])
        self.assertIn("reserved identity — admission unknown", outputs[2])

    def test_31_summary_counts_admitted_nonterminal_attempts(self):
        for state, admitted, expected in (("completed", True, 0), ("blocked", False, 0), ("running", True, 1)):
            doc, stage = self.fixture(state, admitted)
            self.check(doc, (str(expected) + " admitted attempt(s) in nonterminal phases",))
            answer = stack.runtime_boundary(Path("unused"), held={"state": "fresh", "canonical": True, "document": doc,
                                            "observed_age_seconds": 0, "published_age_seconds": 0})
            self.assertEqual(answer["open_episodes"], expected)

    def test_32_four_retained_snapshots(self):
        import hashlib
        root = Path(__file__).parent / "fixtures" / "a1"
        manifest = json.loads((root / "manifest.json").read_text())
        self.assertEqual(len(manifest), 4)
        found = 0
        for record in manifest:
            raw = (root / record["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
            doc = json.loads(raw)
            snapshot = job_viewer.read_snapshot(doc, received_at=0)
            output = io.StringIO()
            stack._print_job_outcomes({"state": "fresh", "canonical": doc["canonical"], "document": doc}, output)
            listed = "\n".join(job_viewer.render_list(snapshot, now=0))
            for job in doc["jobs"]:
                detail = "\n".join(job_viewer.render_detail(snapshot, job["job_id"], now=0))
                for stage in job["stages"]:
                    if stage["kind"] == "review" and stage["state"] == "blocked":
                        found += 1
                        for text in (output.getvalue(), listed, detail):
                            self.assertNotIn(stage["attempt_id"], text)
                            self.assertNotIn(stage["offer_id"], text)
                            self.assertIn("admission not admitted" if record["file"] == "retained-3.json" else "admission unknown", text)
        self.assertEqual(found, 2, "two retained snapshots contain blocked reviews; the other two completed")

    def test_33_partial_and_damaged_fields_degrade(self):
        for key in ("runtime", "exchange", "attempt_diagnostics", "allocation", "allocations", "receipts"):
            for value in (None, [], "broken", {"unknown": True}):
                doc, stage = self.fixture(admitted=False)
                stage[key] = value
                self.check(doc, ("admission unknown", "duration unknown"), ("execution started", "provider started"))
        doc, stage = self.fixture(admitted=False)
        stage.update(state=[], stage_id=None, kind={}, episodes=[{"episode": [], "attempt_id": {}}])
        self.check(doc, ("unknown",))

    def test_34_option_a_freshness_and_activity_remain_independent(self):
        doc, stage = self.fixture()
        for count, identity, expected in ((0, "attempt-a", "0 B"), (42, "attempt-a", "42 B"), (42, "other", "unknown"), (None, "attempt-a", "unknown")):
            stage["runtime"] = {"activity": {"attempt_id": identity, "bytes_observed": count, "observed_at": "2026-11-19T17:59:00.000Z"}}
            for text in self.check(doc, absent=("provider started",)):
                self.assertRegex(text, r"activity\s+" + re.escape(expected))
        stage["runtime"]["activity"].update(attempt_id="attempt-a", bytes_observed=0)
        self.check(doc, ("observed 1m00s ago",), ("STALE",))
        stage["state"] = "completed"
        self.check(doc, ("last at 2026-11-19T17:59:00.000Z",), ("observed 1m00s ago",))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "status.json"
            path.write_text(json.dumps(doc))
            os.utime(path, (EPOCH, EPOCH))
            for age, stale in ((14.999, False), (15, True)):
                answer = stack.snapshot(Path(root), EPOCH + age)
                self.assertEqual(answer["state"] == "stale", stale)
                output = io.StringIO()
                stack._print_job_outcomes(answer, output)
                self.assertEqual("Jobs (stale" in output.getvalue(), stale)
                snapshot = job_viewer.read_snapshot(doc, received_at=0)
                for renderer in (lambda: job_viewer.render_list(snapshot, now=0, wall_now=EPOCH + age),
                                 lambda: job_viewer.render_detail(snapshot, "job-a", now=0, wall_now=EPOCH + age)):
                    self.assertEqual("!! STALE" in "\n".join(renderer()), stale)

    def test_35_documentation_names_rules_and_approved_words(self):
        documentation = (Path(__file__).parents[2] / "JOB-VIEWER.md").read_text()
        for words in ("admitted", "not admitted", "unknown", "episode", "assignment id", "attempt id", "Command accepted", "Execution started", "provider started", "planned", "ready", "in progress", "waiting for an answer", "answered — held", "changes requested", "done", "Failed", "stopping", "stopped", "cancelled before start"):
            self.assertIn(words, documentation)
        for state, expected in (("offered", "admitted"), ("claimed", "admitted"), ("starting", "admitted"), ("waiting", "admitted"), ("reviewing", "in progress"), ("answering", "in progress"), ("changes-requested", "changes requested")):
            doc, stage = self.fixture(state)
            self.check(doc, (expected + "; admission admitted",))

class JobHeadlines(unittest.TestCase):
    def check(self, doc, headline, *row_words, reason=None):
        original = copy.deepcopy(doc)
        for rendered in views(doc):
            lines = rendered.splitlines()
            idx = next(i for i, line in enumerate(lines) if line.startswith(("Job job-a:", "JOB job-a ")))
            self.assertTrue(lines[idx].endswith(headline), lines[idx])
            if reason:
                self.assertIn(reason, lines[idx + 1])
            for word in row_words:
                self.assertIn(word, rendered)
        self.assertEqual(doc, original)

    def test_mixed_priority_preserves_rows(self):
        doc = document()
        stages = doc["jobs"][0]["stages"]
        running = copy.deepcopy(stages[0])
        running.update(kind="review", stage_id="review")
        stages.append(running)
        stages[0]["state"] = "answering"
        stages[0]["runtime"]["model_attribution_hold"] = "model-attribution-missing"
        self.check(doc, "DECISION NEEDED", "answering — held for owner", "in progress; admission admitted",
                   reason="implementation: model-attribution-missing")
        stages.append({"stage_id":"failure","kind":"integration","state":"exceptional"})
        self.check(doc, "FAILED", "model-attribution-missing", "in progress; admission admitted")

    def test_waiting_rows_require_named_external_dependencies(self):
        doc = document()
        stages = doc["jobs"][0]["stages"]
        stages.append({"kind":"review","stage_id":"review","state":"blocked",
                       "gates":[{"open":False,"stage_id":"implementation","state":"queued"}]})
        self.check(doc, "IN PROGRESS", "waiting on implementation")
        stages[0]["state"] = "queued"
        self.check(doc, "QUEUED", "waiting on implementation")
        stages[0].update(state="blocked", gates=[{"open":False,"stage_id":"external-a","state":"waiting"}])
        self.check(doc, "BLOCKED", "waiting on external-a", "waiting on implementation")
        stages[1]["gates"][0]["stage_id"] = "external-b"
        self.check(doc, "BLOCKED", "waiting on external-a", "waiting on external-b")
        stages[1]["gates"] = []
        self.check(doc, "UNKNOWN", "blocker unknown")

    def test_completion_without_job_result_and_stop_without_decision(self):
        doc = document()
        job = doc["jobs"][0]
        stage = job["stages"][0]
        stage["state"] = "completed"
        self.check(doc, "UNKNOWN", "done; admission admitted", reason="final Job outcome has not been recorded")
        stage["state"] = "exceptional"
        job["cancellation"] = {"targets":[{"stage_id":"implementation","episode":1,"attempt_id":"attempt-a","state":"ceased"}]}
        self.check(doc, "CANCELLATION REQUESTED", "attempt 1 attempt-a — stopped")
        stage["runtime"]["model_attribution_hold"] = "model-attribution-missing"
        self.check(doc, "DECISION NEEDED", "attempt 1 attempt-a — stopped", reason="model-attribution-missing")

    def test_admission_priority_requires_published_admission(self):
        for state in ("offered", "claimed", "starting", "waiting"):
            with self.subTest(state=state):
                doc = document()
                stages = doc["jobs"][0]["stages"]
                stages[0]["state"] = state
                self.check(doc, "ADMITTED", "admitted; admission admitted", "reported phase state: " + state)
                stages.append({"stage_id":"review", "kind":"review", "state":"blocked",
                               "gates":[{"open":False, "stage_id":"implementation", "state":state}]})
                self.check(doc, "ADMITTED", "waiting on implementation (" + state + ")")
                stages.append({"stage_id":"another", "kind":"research", "state":"queued"})
                self.check(doc, "ADMITTED", "ready; admission unknown")
                stages.append(dict(document()["jobs"][0]["stages"][0], stage_id="active"))
                self.check(doc, "IN PROGRESS", "in progress; admission admitted")
                del stages[1:]
                stages[0].pop("allocation")
                self.check(doc, "UNKNOWN", "admission unknown")

    def test_cancellation_priority_keeps_phase_positions(self):
        for state, position in (("running","in progress"), ("offered","admitted"), ("queued","ready")):
            with self.subTest(state=state):
                doc = document()
                job = doc["jobs"][0]
                job["cancellation"] = {"trigger":"operator", "shutdown":"unresolved"}
                stage = job["stages"][0]
                stage["state"] = state
                self.check(doc, "CANCELLATION REQUESTED", position + "; admission")
                stage["state"] = "answering"
                stage["runtime"]["model_attribution_hold"] = "model-attribution-missing"
                self.check(doc, "DECISION NEEDED", reason="model-attribution-missing")
                job["stages"].append({"stage_id":"failed","state":"exceptional"})
                self.check(doc, "FAILED", "model-attribution-missing")

    def test_dependency_chain_is_order_independent_and_needs_external_evidence(self):
        doc = document()
        def waiting(name, dependency):
            return {"kind":name, "stage_id":name, "state":"blocked",
                    "gates":[{"stage_id":dependency, "open":False, "state":"blocked"}]}
        stages = [waiting("integration","review"), waiting("review","implementation"),
                  waiting("implementation","external-fix")]
        doc["jobs"][0]["stages"] = stages
        self.check(doc, "BLOCKED", "waiting on external-fix", "waiting on implementation", "waiting on review")
        stages[-1]["gates"][0]["open"] = True
        self.check(doc, "UNKNOWN")
        stages[-1]["gates"] = waiting("implementation","review")["gates"]
        self.check(doc, "UNKNOWN", "waiting on review")
