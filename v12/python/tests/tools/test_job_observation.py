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
        for state, outcome in (("running", "IN PROGRESS"), ("completed", "ALL PHASES COMPLETE"), ("queued", "QUEUED"), ("changes-requested", "CHANGES REQUESTED"), ("exceptional", "FAILED"), ("blocked", "BLOCKED"), ("unrecognized", "UNKNOWN")):
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
        # W385263 (owner 2026-11-26): all phases done is ALL PHASES COMPLETE, not UNKNOWN; with no
        # matching review verdict it shows none, and it still records no Job closure.
        self.check(doc, "ALL PHASES COMPLETE", "done; admission admitted", reason="No review verdict is recorded")
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

    def test_a_completed_cancellation_shutdown_is_CANCELLED_and_a_pending_one_is_still_a_request(self):
        """W386732 (M386700 after settlement): the headline follows the published report's own shutdown."""
        for state, position in (("running","in progress"), ("offered","admitted"), ("queued","ready"), ("starting","admitted")):
            with self.subTest(state=state):
                doc = document()
                job = doc["jobs"][0]
                job["stages"][0]["state"] = state
                job["cancellation"] = {"trigger":"operator", "shutdown":"complete"}
                self.check(doc, "CANCELLED", position + "; admission",
                           reason="Cancellation shutdown complete: every target has settled and nothing further is admitted.")
                for pending in ("unresolved", "within-bound", None, "", "COMPLETE", 1):
                    job["cancellation"] = {"trigger":"operator", "shutdown":pending}
                    self.check(doc, "CANCELLATION REQUESTED", position + "; admission")
                job["cancellation"] = {"trigger":"operator"}
                self.check(doc, "CANCELLATION REQUESTED", position + "; admission")

    def test_a_completed_cancellation_keeps_a_failure_and_an_owner_decision_first(self):
        """The original failure and review details stay as they were; only the cancellation line's word changes."""
        doc = document()
        job = doc["jobs"][0]
        job["cancellation"] = {"trigger":"operator", "shutdown":"complete"}
        stage = job["stages"][0]
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


DIAGNOSTIC_SCHEMA = "baton.v12.attempt-failure-cause/1"


class AFrozenReviewWithoutAReportIsBlocked(unittest.TestCase):
    """W386395, from native run M386388 on 0cb8b0de.

    THE MEASURED DEFECT: the implementation had completed and the sole
    remaining review attempt had frozen its result `unable` with the sealed
    report state `missing`. The stage still read `answering`, so every surface
    said the review was in progress and the Job IN PROGRESS, while the
    launcher, reading the same evidence, reported a terminal hold.

    THE SHAPE is the retained snapshot's (`evidence/retained-final.status.json`
    in the W386395 dossier): the members the read model consults, with the
    same states, the same attempt binding and the same declaration leaves.
    """

    REVIEW_ATTEMPT = "attempt-review"

    @staticmethod
    def declaration(**members):
        return {name: {"known": True, "value": value, "source": "fixture"} for name, value in members.items()}

    def job(self, review_declaration=None, **review):
        stages = [
            {"stage_id": "job-a/implementation", "kind": "implementation", "state": "completed",
             "attempt_id": "attempt-impl", "episode": 1, "episodes": [{"episode": 1, "attempt_id": "attempt-impl"}],
             "allocation": {"episode": 1, "assignment_id": "attempt-impl", "allocation_state": "released"},
             "attempt_diagnostics": {"schema": DIAGNOSTIC_SCHEMA, "attempt_id": "attempt-impl", "worker_declaration": self.declaration(
                 disposition="completed", frozen_at="2026-11-19T17:50:00.000Z")}},
            {"stage_id": "job-a/review", "kind": "review", "state": "answering",
             "attempt_id": self.REVIEW_ATTEMPT, "episode": 1,
             "episodes": [{"episode": 1, "attempt_id": self.REVIEW_ATTEMPT}],
             "allocation": {"episode": 1, "assignment_id": self.REVIEW_ATTEMPT, "allocation_state": "reserved"},
             "gates": [{"open": True, "stage_id": "job-a/implementation", "state": "completed"}],
             "attempt_diagnostics": {"schema": DIAGNOSTIC_SCHEMA, "attempt_id": self.REVIEW_ATTEMPT, "worker_declaration": self.declaration(
                 **(review_declaration if review_declaration is not None else
                    {"disposition": "unable", "frozen_at": "2026-11-19T17:55:00.000Z", "review_report": "missing"}))}}]
        stages[1].update(review)
        return {"schema": stack.STATUS_SCHEMA, "observed_at": NOW, "canonical": True, "incarnation": "publisher",
                "jobs": [{"job_id": "job-a", "submission_id": "submission-a", "stages": stages}]}

    def seen(self, doc):
        view = model.job_view(doc, doc["jobs"][0])
        return view, {phase["role"]: phase for phase in view["phases"]}

    def test_the_retained_run_reads_BLOCKED_with_the_report_reason_on_every_surface(self):
        doc = self.job()
        view, phases = self.seen(doc)
        self.assertEqual((view["headline"], view["headline_reason"]), ("BLOCKED", "Review held: review report missing"))
        self.assertEqual(phases["review"]["row_position"], "held")
        self.assertEqual(phases["review"]["reason"], "Review held: review report missing")
        status, listed, detail = views(doc)
        for text in (status, listed, detail):
            self.assertIn("BLOCKED", text)
            self.assertIn("Review held: review report missing", text)
            self.assertNotIn("IN PROGRESS", text)
        from tools import job_tui
        with tempfile.TemporaryDirectory(prefix="v12-w386395-") as room:
            place = os.path.join(room, "status.json")
            Path(place).write_text(json.dumps(doc))
            session = job_tui.Session(job_tui.source_from(place))
            session.read()
            painted = "\n".join(session.frame(24, 120).lines)
            session.key("open")
            opened = "\n".join(session.frame(24, 120).lines)
        for text in (painted, opened):
            self.assertIn("BLOCKED", text)
            self.assertIn("Review held: review report missing", text)
        self.assertIn("review          held", opened)

    def test_the_hold_survives_its_runtime_stopping_on_every_surface(self):
        """M386388 after expiry reclaim: the same frozen attempt, now ceased.
        The row says `stopped`; the Job stays BLOCKED with the same sentence."""
        from tools import job_tui
        stopped = {"outcome": {"known": True, "value": "ceased-absent", "source": "attempt.cessation-outcome"}}
        for label, row in (("before", "held"), ("after", "stopped")):
            with self.subTest(runtime=label):
                doc = self.job()
                if label == "after":
                    doc["jobs"][0]["stages"][1]["attempt_diagnostics"]["cause"] = stopped
                view, phases = self.seen(doc)
                self.assertEqual((view["headline"], view["headline_reason"]), ("BLOCKED", "Review held: review report missing"))
                self.assertEqual(phases["review"]["row_position"], row)
                status, listed, detail = views(doc)
                with tempfile.TemporaryDirectory(prefix="v12-w386395-") as room:
                    place = os.path.join(room, "status.json")
                    Path(place).write_text(json.dumps(doc))
                    session = job_tui.Session(job_tui.source_from(place))
                    session.read()
                    painted = "\n".join(session.frame(24, 120).lines)
                    session.key("open")
                    opened = "\n".join(session.frame(24, 120).lines)
                for text in (status, listed, detail, painted, opened):
                    self.assertIn("BLOCKED", text)
                    self.assertIn("Review held: review report missing", text)
                    self.assertNotIn("UNKNOWN", text)
                self.assertIn("review          " + row, opened)
        # A stopped review that never froze is no hold; genuine parallel work still leads.
        doc = self.job({"disposition": "unable", "review_report": "missing"})
        doc["jobs"][0]["stages"][1]["attempt_diagnostics"]["cause"] = stopped
        self.assertNotEqual(self.seen(doc)[0]["headline"], "BLOCKED")
        doc = self.job()
        doc["jobs"][0]["stages"][1]["attempt_diagnostics"]["cause"] = stopped
        doc["jobs"][0]["stages"].append({"stage_id": "job-a/integration", "kind": "integration", "state": "running",
                                         "attempt_id": "attempt-int", "episode": 1,
                                         "episodes": [{"episode": 1, "attempt_id": "attempt-int"}],
                                         "allocation": {"episode": 1, "assignment_id": "attempt-int"}})
        self.assertEqual(self.seen(doc)[0]["headline"], "IN PROGRESS")

    def test_each_classified_report_state_holds(self):
        for state, sentence in (("empty", "Review held: review report empty"),
                                ("malformed", "Review held: review report malformed"),
                                ("unclassified", "Review held: no usable report")):
            with self.subTest(state=state):
                view, _ = self.seen(self.job({"disposition": "unable", "frozen_at": "2026-11-19T17:55:00.000Z",
                                              "review_report": state}))
                self.assertEqual((view["headline"], view["headline_reason"]), ("BLOCKED", sentence))

    def test_an_answering_review_that_has_not_frozen_is_still_IN_PROGRESS(self):
        """Post-turn verification can still be running: no frozen result, no hold."""
        for declaration in ({}, {"disposition": "unable", "review_report": "missing"}, {"review_report": "not-read",
                            "disposition": "unable", "frozen_at": "2026-11-19T17:55:00.000Z"}):
            with self.subTest(declaration=sorted(declaration)):
                view, phases = self.seen(self.job(declaration))
                self.assertEqual(view["headline"], "IN PROGRESS")
                self.assertEqual(phases["review"]["row_position"], "in progress")

    def test_evidence_of_another_attempt_or_unknown_evidence_never_holds(self):
        doc = self.job()
        doc["jobs"][0]["stages"][1]["attempt_diagnostics"]["attempt_id"] = "attempt-earlier"
        self.assertEqual(self.seen(doc)[0]["headline"], "IN PROGRESS")
        doc = self.job()
        doc["jobs"][0]["stages"][1]["attempt_diagnostics"]["worker_declaration"]["review_report"] = {"known": False, "value": None}
        self.assertEqual(self.seen(doc)[0]["headline"], "IN PROGRESS")

    def test_a_genuinely_active_parallel_phase_still_reads_IN_PROGRESS(self):
        doc = self.job()
        doc["jobs"][0]["stages"].append({"stage_id": "job-a/integration", "kind": "integration", "state": "running",
                                         "attempt_id": "attempt-int", "episode": 1,
                                         "episodes": [{"episode": 1, "attempt_id": "attempt-int"}],
                                         "allocation": {"episode": 1, "assignment_id": "attempt-int"}})
        view, phases = self.seen(doc)
        self.assertEqual((view["headline"], view["headline_reason"]), ("IN PROGRESS", ""))
        self.assertEqual(phases["review"]["row_position"], "held")
        self.assertEqual(phases["integration"]["row_position"], "running")

    def test_failure_and_owner_decisions_keep_their_priority(self):
        doc = self.job()
        doc["jobs"][0]["stages"][0]["state"] = "exceptional"
        self.assertEqual(self.seen(doc)[0]["headline"], "FAILED")
        doc = self.job(runtime={"model_attribution_hold": "model-attribution-missing"})
        view, phases = self.seen(doc)
        self.assertEqual(view["headline"], "DECISION NEEDED")
        self.assertEqual(phases["review"]["row_position"], "answering — held for owner")
        self.assertEqual(phases["review"]["reason"],
                         "held: model-attribution-missing; owner action needed; Review held: review report missing")
        doc = self.job()
        doc["jobs"][0]["cancellation"] = {"requested_at": NOW}
        self.assertEqual(self.seen(doc)[0]["headline"], "CANCELLATION REQUESTED")


# Simulated provider and engine at their normal boundaries; actual worker,
# custody, manager, projection and three rendered views.
from tests.tools import test_provider_selection as report_fixtures


class ReviewReportVisibility(report_fixtures.SelectedBase):
    REPORT = {"schema": "baton.review-report/1", "verdict": "accepted", "findings": "Reviewed fixture"}
    SENTENCES = ("Review held: review report missing", "Review held: review report empty",
                 "Review held: review report malformed", "Review held: no usable report")

    def provider(self, **kwargs):
        original = super().provider(**kwargs)
        def run(argv, **options):
            answer = original(argv, **options)
            if argv[0] == "claude" and argv != ["claude", "--version"] and getattr(self, "report_link", False):
                target = Path(options["cwd"], "valid-report")
                target.write_text(json.dumps(self.REPORT))
                Path(options["cwd"], "review-report.json").symlink_to(target)
            return answer
        return run

    def review(self, body=None, *, status=0, mismatch=False, historical=False, link=False):
        from unittest import mock
        from baton_v12.job_manager import review_driver, sweep
        from tests.job_manager import fixtures
        import claude_agent
        held = self.implemented()
        from baton_v12.authority import Authority
        from baton_v12.authority.messages import ROUTING_SCHEMA
        authority = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("native_handoff_routing", {"schema": ROUTING_SCHEMA,
                "reviewer": "baton.reviewer", "decision_recipient": "baton.slaw"})
        finally:
            authority.dispose()
        self.drive(held.job, held.composed, "review", "waiting")
        held.review = self.only_attempt(held.composed, "review")
        if mismatch:
            self.reported = ["other-model"]
        self.report_link = link
        actual_write = claude_agent._written
        def historical_write(path, content, *args, **kwargs):
            if path.endswith("/logs/review.json"):
                log = json.loads(content)
                log.pop("report_state")
                content = json.dumps(log)
            return actual_write(path, content, *args, **kwargs)
        with mock.patch.object(claude_agent, "_written", side_effect=historical_write if historical else actual_write):
            self.assertEqual(self.turn(held.control, "review", held.review,
                self.mounted(held.composed, "review", held.review),
                edits={} if body is None else {"review-report.json": body}, status=status), 0)
        actual_end = review_driver.end_review_from_result
        self.conclusions = []
        def end(*args, **kwargs):
            self.end_args, self.end_kwargs = args, kwargs
            answer = actual_end(*args, **kwargs)
            self.conclusions.append(answer)
            return answer
        with mock.patch.object(review_driver, "end_review_from_result", side_effect=end):
            for _ in range(4):
                sweep(held.job, held.composed, now=fixtures.NOW)
                if self.conclusions:
                    break
        self.assertTrue(self.conclusions)
        self.held = held
        return held, self.conclusions[-1]

    def snapshot(self):
        from baton_v12.job_manager import status
        from tests.job_manager import fixtures
        doc = status(self.held.job, self.held.composed, observed_at=fixtures.NOW)
        # Observation time alone is translated to the fixed rendering clock.
        doc["observed_at"] = NOW
        return doc

    def check(self, sentence, conclusion=None, *, stale=False, attribution=False):
        doc = self.snapshot()
        stage = next(s for s in doc["jobs"][0]["stages"] if s["kind"] == "review")
        diagnostic = stage["attempt_diagnostics"]
        self.assertEqual(diagnostic["attempt_id"], self.held.review)
        if stale:
            doc["observed_at"] = "2026-11-18T18:00:00.000Z"
            output = io.StringIO()
            stack._print_job_outcomes({"state": "stale", "canonical": True, "document": doc}, output)
            snap = job_viewer.read_snapshot(doc, received_at=0)
            rendered = (output.getvalue(), "\n".join(job_viewer.render_list(snap, now=60, wall_now=EPOCH)),
                        "\n".join(job_viewer.render_detail(snap, "job-a", now=60, wall_now=EPOCH)))
        else:
            rendered = views(doc)
        for view in rendered:
            if sentence:
                self.assertIn(sentence, view)
            for other in self.SENTENCES:
                if other != sentence:
                    self.assertNotIn(other, view)
            if stale:
                self.assertIn("STALE", view.upper())
            if attribution:
                first = "held: model-attribution-conflicting; owner action needed"
                self.assertIn(first, view)
                if sentence:
                    self.assertLess(view.index(first), view.index(sentence))
        if conclusion is not None:
            if sentence:
                self.assertIn(sentence, conclusion["held_reason"])
                self.assertEqual(conclusion["outcome"], "held")
                self.assertIsNone(conclusion.get("verdict_id"))
                self.assertFalse(conclusion["cleaned_up"])
                from baton_v12.job_manager import review_uncertainty
                self.assertEqual(review_uncertainty.items_of(self.held.job), [])
                self.assertEqual(conclusion["review_report"], diagnostic["worker_declaration"]["review_report"])
            else:
                for other in self.SENTENCES:
                    self.assertNotIn(other, json.dumps(conclusion))
        return doc, stage

    def test_17_missing(self):
        held, end = self.review()
        doc, stage = self.check(self.SENTENCES[0], end)
        self.assertEqual(stage["state"], "answering")
        from baton_v12.job_manager import review_uncertainty
        self.assertEqual(review_uncertainty.items_of(held.job), [])
        self.assertIsNone(end.get("verdict"))

    def test_17_empty(self):
        held, end = self.review("")
        self.check(self.SENTENCES[1], end)

    def test_17_malformed(self):
        held, end = self.review("not JSON")
        self.check(self.SENTENCES[2], end)

    def test_18_symlink(self):
        held, end = self.review(link=True)
        self.check(self.SENTENCES[3], end)

    def test_19_historical(self):
        held, end = self.review(historical=True)
        self.check(self.SENTENCES[3], end)

    def test_20_replaced_sealed_log(self):
        from baton_v12.worker_manager import frozen_output_of
        from baton_v12.worker_manager.failure_cause import review_report_of
        from baton_v12.job_manager import review_driver
        from urllib.parse import urlsplit, unquote
        held, end = self.review()
        frozen = frozen_output_of(held.control, held.review)
        artifact = next(a for a in frozen["artifacts"] if a["output_name"] == "logs")
        path = Path(unquote(urlsplit(artifact["locator"]).path), "review.json")
        original = path.read_bytes()
        # Same byte length, different digest: no size-only trust.
        path.chmod(0o600)
        path.write_bytes(original.replace(b'"missing"', b'"garbage"'))
        reason = review_report_of(held.control, held.review)
        self.assertFalse(reason["known"])
        self.assertIn("recompute", reason["why"])
        self.assertLessEqual(len(reason["why"]), 512)
        end = review_driver.end_review_from_result(*self.end_args, **self.end_kwargs)
        self.check(None, end)

    def test_21_provider_failure(self):
        held, end = self.review(json.dumps(self.REPORT), status=1)
        self.check(None, end)
        self.assertEqual(end["review_report"]["value"], "not-read")
        for view in views(self.snapshot()):
            self.assertIn("provider failure unclassified", view)

    def test_22_uncertainty(self):
        held, end = self.review(json.dumps({"schema": "baton.review-uncertainty/1", "findings": "Cannot decide"}))
        self.check(None, end)
        self.assertIn("uncertainty", end)
        self.assertIn("owner decision", end["held_reason"])
        from baton_v12.job_manager import review_uncertainty
        [item] = review_uncertainty.items_of(held.job)
        self.assertEqual(item["destination"], "baton.slaw")
        self.assertEqual(item["evidence"]["attempt_id"], held.review)
        self.assertIsNone(item["verdict"])
        self.assertIsNone(item["automatic_retry"])

    def test_23_attribution_with_usable_report(self):
        held, end = self.review(json.dumps(self.REPORT), mismatch=True)
        self.check(None, end, attribution=True)
        self.assertEqual(end["reason"], "model-attribution-conflicting")

    def test_24_attribution_and_missing_report(self):
        held, end = self.review(mismatch=True)
        self.check(self.SENTENCES[0], end, attribution=True)
        self.assertTrue(end["held_reason"].startswith("model-attribution-conflicting"))

    def test_25_accepted(self):
        held, end = self.review(json.dumps(self.REPORT))
        self.check(None, end)
        self.assertEqual(end["outcome"], "accepted")

    def test_26_later_episode_does_not_inherit(self):
        held, end = self.review()
        doc, stage = self.check(self.SENTENCES[0], end)
        # A later correction episode snapshot retains historical evidence;
        # its live attempt association must prevent using the earlier log.
        stage["episodes"].append({"episode": 2, "attempt_id": "later-review"})
        stage.update(episode=2, attempt_id="later-review")
        stage["allocation"].update(episode=2, assignment_id="later-review")
        for view in views(doc):
            for sentence in self.SENTENCES:
                self.assertNotIn(sentence, view)

    def test_27_stale_snapshot(self):
        held, end = self.review()
        self.check(self.SENTENCES[0], end, stale=True)

    def test_28_recovered_ending_remeasures_without_duplicate_writes(self):
        from baton_v12.job_manager import review_driver
        from baton_v12.worker_manager.failure_cause import review_report_of
        held, end = self.review()
        worker = self.worker_of(held.composed, "review")
        worker.stage._prepared.clear()
        from baton_v12.worker_manager import ControlStore
        reopened = ControlStore.open(self.control_path, incarnation="report-reopen", clock=lambda: NOW)
        try:
            changes = reopened._connection.total_changes
            self.assertEqual(review_report_of(reopened, held.review), end["review_report"])
            self.assertEqual(reopened._connection.total_changes, changes)
        finally:
            reopened.close()
        starts = len(self.engine.starts)
        before = held.control._connection.total_changes
        again = review_driver.end_review_from_result(*self.end_args, **self.end_kwargs)
        self.assertEqual(again, end)
        self.assertEqual(review_report_of(held.control, held.review), end["review_report"])
        self.assertEqual(held.control._connection.total_changes, before)
        self.assertEqual(len(self.engine.starts), starts)
        self.check(self.SENTENCES[0], again)


    def test_sentence_vocabularies_agree_and_unknown_stays_silent(self):
        from baton_v12.worker_manager import review_reports
        for word in review_reports.REPORT_STATES + ("foreign-prose", None):
            for known in (True, False):
                fact = {"known": known, "value": word}
                self.assertEqual(model.review_report_sentence(fact), review_reports.review_report_sentence(fact))
                if not known or word in ("usable", "not-read", "foreign-prose", None):
                    self.assertEqual(model.review_report_sentence(fact), "")


class OwnerPacedObservation(unittest.TestCase):
    def test_phase_cancellation_binds_internal_stage_episode_and_attempt(self):
        doc = document()
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open")
        stage = job["stages"][0]
        target = {"stage_id": "exec-1/research", "episode": 1, "attempt_id": "attempt-a", "state": "ordered"}
        stage.update(stage_id="job-a/routing", kind="research", execution_job_id="exec-1",
                     execution_cancellation={"trigger": "job-deadline", "targets": [target]})
        for rendered in views(doc):
            self.assertIn("stopping (ordered)", rendered)
            self.assertNotIn("CANCELLATION REQUESTED", rendered)
        for key, foreign in (("stage_id", "exec-2/research"), ("stage_id", "job-a/routing"),
                             ("episode", 2), ("attempt_id", "foreign-attempt")):
            with self.subTest(key=key, foreign=foreign):
                stage["execution_cancellation"]["targets"] = [dict(target, **{key: foreign})]
                for rendered in views(doc):
                    self.assertNotIn("stopping (ordered)", rendered)

    def test_mixed_status_preserves_automatic_attempt_diagnostics(self):
        from tools import attempt_diagnostics
        older = document()
        mixed = copy.deepcopy(older)
        mixed.update(schema=stack.MANUAL_STATUS_SCHEMA)
        mixed["jobs"].append({"job_id": "study", "mode": "MANUAL", "lifecycle": "open", "stages": []})
        self.assertEqual(attempt_diagnostics.report(mixed)["rows"], attempt_diagnostics.report(older)["rows"])
        prior = worker_visibility.visibility(older)
        current = worker_visibility.visibility(mixed)
        self.assertEqual(current["source_schema"], stack.MANUAL_STATUS_SCHEMA)
        self.assertEqual(current["stages"], prior["stages"])
        mixed["jobs"][1]["lifecycle"] = "unexpected"
        with self.assertRaises(worker_visibility.VisibilityRefusal):
            worker_visibility.visibility(mixed)
        self.assertIsNotNone(stack._malformed(mixed))
        mixed["schema"] = "baton.v12.job-status/999"
        with self.assertRaises(worker_visibility.VisibilityRefusal):
            worker_visibility.visibility(mixed)
        with self.assertRaises(job_viewer.ViewerRefusal):
            attempt_diagnostics.report(mixed)

    def test_a_ready_unselected_assignment_preserves_a_real_hold(self):
        doc = document()
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open")
        job["stages"][0]["state"] = "answering"
        job["stages"][0]["runtime"]["model_attribution_hold"] = "model-attribution-missing"
        job["stages"].append({"kind": "research", "stage_id": "job-a/another", "state": "queued", "selected_at": None})
        for rendered in views(doc):
            self.assertIn("MANUAL OPEN   DECISION NEEDED", rendered)
            self.assertIn("model-attribution-missing", rendered)

    def test_owner_decisions_keep_worker_uncertainty_and_closed_phase_counts_on_every_surface(self):
        doc = document()
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open")
        stage = job["stages"][0]
        cause = "model-attribution-missing"
        stage["runtime"]["model_attribution_hold"] = cause
        decision = {"actor": {"participant": "baton.slaw", "principal": "owner"},
                    "outcome": "success", "recorded_at": NOW, "held_cause": cause,
                    "frozen": {"result_id": "frozen-1", "frozen_at": NOW, "manifest_digest": "manifest-1"}}
        stage.update(selected_at=NOW, state="completed", stage_id="job-a/review",
                     result={"reason": "owner-decision", "owner_decision": decision, "attempt_id": "attempt-a"})
        job["stages"].append({"state": "queued", "kind": "research", "stage_id": "job-a/unselected"})
        for rendered in views(doc):
            self.assertIn("AWAITING ASSIGNMENT", rendered)
            self.assertNotIn("owner action needed", rendered)
            self.assertIn("Worker hold at freeze: " + cause, rendered)
            self.assertIn("Owner decision: success by baton.slaw (owner)", rendered)
            self.assertIn("Frozen result: frozen-1", rendered)
        job["stages"].extend([{"state": "exceptional", "kind": "research", "stage_id": "job-a/failed", "selected_at": NOW},
                              {"state": "blocked", "kind": "research", "stage_id": "job-a/blocked"}])
        job.update(lifecycle="closed", closed_at=NOW)
        for rendered in views(doc):
            self.assertIn("MANUAL · CLOSED", rendered)
            self.assertIn("1 finished · 1 failed · 2 never selected", rendered)
            self.assertIn("job-a/failed", rendered)
            self.assertIn("job-a/blocked", rendered)
            self.assertIn("manifest-1", rendered)

    def test_idle_selected_settled_and_closed_on_every_surface(self):
        doc = document()
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        stage = {"kind": "research", "stage_id": "job-a/routing", "state": "queued", "selected_at": None}
        job.update(mode="MANUAL", lifecycle="open", stages=[stage],
                   budget={"charged_seconds": 3, "limit_seconds": 60})
        for rendered in views(doc):
            self.assertIn("MANUAL OPEN   AWAITING ASSIGNMENT", rendered)
            self.assertIn("Ready for explicit start", rendered)
            self.assertIn("3/60s charged", rendered)
        job["budget"]["expired"] = True
        for rendered in views(doc):
            self.assertIn("MANUAL OPEN   BUDGET EXHAUSTED", rendered)
            self.assertNotIn("Ready for explicit start", rendered)
        job["budget"]["expired"] = False
        stage["selected_at"] = NOW
        for rendered in views(doc):
            self.assertIn("MANUAL OPEN   QUEUED", rendered)
            self.assertIn("Selection recorded; waiting for admission", rendered)
        stage.update(state="completed", result={"attempt_id": "attempt-1", "locator": "file:///retained/findings"},
                     artifacts=[{"output_name": "findings", "locator": "file:///retained/findings"}])
        for rendered in views(doc):
            self.assertIn("MANUAL OPEN   AWAITING ASSIGNMENT", rendered)
            self.assertIn("The planned phase finished.", rendered)
            self.assertIn("Retained result for attempt attempt-1", rendered)
            self.assertIn("Retained findings: file:///retained/findings", rendered)
        auto = {"job_id": "auto-1", "stages": []}
        doc["jobs"].append(auto)
        snapshot = job_viewer.read_snapshot(doc, received_at=0)
        def todo():
            return "\n".join(job_viewer.render_list(snapshot, now=0, wall_now=EPOCH, todo=True))
        self.assertIn("job-a", todo())
        self.assertNotIn("auto-1", todo())
        job.update(lifecycle="closed", closed_at=NOW)
        self.assertNotIn("job-a", todo())
        for rendered in views(doc):
            self.assertIn("MANUAL · CLOSED", rendered)
            self.assertIn("1 finished · 0 failed · 0 never selected", rendered)
            self.assertIn("closed at " + NOW, rendered)
        self.assertIn("file:///retained/findings", views(doc)[2])


class AllPhasesCompleteShowsOnlyItsOwnVerdict(unittest.TestCase):
    """W385263, owner decision 2026-11-26, with M386415 as the regression case.

    M386415 (job-offline-status-successor-386415) finished both phases and its
    review recorded an ACCEPTED verdict on the candidate checkpoint, yet every
    surface read UNKNOWN. THE SHAPE is the retained snapshot's
    (`runs/M386415/final.status.json` on the field instance) reduced to the
    members the read model consults, with its real stage, attempt, checkpoint
    and verdict identities; `review_verdict` is the member this change's read
    publishes for the review stage (`job_manager.review_verdicts.matching`).
    """

    JOB = "job-offline-status-successor-386415"
    REVIEW_ATTEMPT = "attempt-7a47d72c3a7a73567104592b6d70341c38ff7aecb8f1e9165fea0ac3ec27ca95"
    CHECKPOINT = "checkpoint-a9affab3e5516d2c6fe715d0e4a9457c81036992019040a2c47d57f4a28e906b"
    VERDICT = {"disposition": "accepted",
               "verdict_id": "verdict-0dc0fcbf9da7bb6f41556baff503fbf2edfff1ff009bf10c63c06dc4665e8eaf",
               "attachment_id": "review-20155d4a646c9a373d67bf5658a406a7ed597b0898dd080807d5101678c2b345",
               "attempt_id": REVIEW_ATTEMPT, "checkpoint_id": CHECKPOINT,
               "line_id": "line-dbaa6202656126256eee7ffd0fc1d9b953c0ebe37c99d81aff29ea939747a2ca",
               "base_object": "6ac23589f24aa94fe8cfd9cb7d79eb57d78d061c",
               "head_object": "340f867479024e6dcffec92345a2dfc5d0263189",
               "tree_object": "35686824a2f560f9c20e80d6905873dd0c89c41e", "importable": True}
    # M386422: main commit 6540775d integrated the accepted candidate with the same tree.
    RECEIPT = {"job_id": JOB, "action": "record-integration", "operation_id": "job.integration-recorded:x",
               "recorded_at": "2026-11-26T19:00:00.000Z",
               "recorded_by": {"participant": "baton.slaw", "principal": "principal:baton.slaw"},
               "candidate": {"checkpoint_id": CHECKPOINT, "head_object": "340f867479024e6dcffec92345a2dfc5d0263189",
                             "tree_object": "35686824a2f560f9c20e80d6905873dd0c89c41e"},
               "target": {"commit": "6540775d5f29bea86f71756486c092be9d0a3ccd", "tree": "35686824a2f560f9c20e80d6905873dd0c89c41e"},
               "phases": []}

    def snapshot(self, verdict=None, publish=True):
        implementation = "attempt-9b8f859bb00bd68102a6d26908097b23322e7f44af0c1f78e67b2b3f17769a64"
        stages = [
            {"stage_id": self.JOB + "/implementation", "kind": "implementation", "state": "completed",
             "attempt_id": implementation, "episode": 1, "episodes": [{"episode": 1, "attempt_id": implementation}],
             "allocation": {"episode": 1, "assignment_id": implementation, "allocation_state": "released"},
             "runtime": {"assignment": {"generation": 1}}},
            {"stage_id": self.JOB + "/review", "kind": "review", "state": "completed",
             "attempt_id": self.REVIEW_ATTEMPT, "episode": 1,
             "episodes": [{"episode": 1, "attempt_id": self.REVIEW_ATTEMPT}],
             "allocation": {"episode": 1, "assignment_id": self.REVIEW_ATTEMPT, "allocation_state": "released"},
             "gates": [{"open": True, "stage_id": self.JOB + "/implementation", "state": "completed"}],
             "runtime": {"assignment": {"generation": 2}}}]
        if publish:
            stages[1]["review_verdict"] = verdict
        return {"schema": stack.STATUS_SCHEMA, "observed_at": NOW, "canonical": True, "incarnation": "publisher",
                "jobs": [{"job_id": self.JOB, "submission_id": "sub-" + self.JOB, "stages": stages}]}

    def surfaces(self, doc):
        from tools import job_tui
        output = io.StringIO()
        stack._print_job_outcomes({"state": "fresh", "canonical": True, "document": doc}, output)
        snapshot = job_viewer.read_snapshot(doc, received_at=0)
        texts = [output.getvalue(), "\n".join(job_viewer.render_list(snapshot, now=0, wall_now=EPOCH)),
                 "\n".join(job_viewer.render_detail(snapshot, self.JOB, now=0, wall_now=EPOCH))]
        with tempfile.TemporaryDirectory(prefix="v12-w385263-") as room:
            place = os.path.join(room, "status.json")
            Path(place).write_text(json.dumps(doc))
            session = job_tui.Session(job_tui.source_from(place))
            session.read()
            texts.append("\n".join(session.frame(24, 160).lines))
            session.key("open")
            texts.append("\n".join(session.frame(24, 160).lines))
        return texts

    def test_M386415_with_its_accepted_importable_candidate_reads_READY_FOR_INTEGRATION_everywhere(self):
        doc = self.snapshot(dict(self.VERDICT))
        before = copy.deepcopy(doc)
        view = model.job_view(doc, doc["jobs"][0])
        self.assertEqual(view["headline"], "READY FOR INTEGRATION")
        self.assertIn("340f867479024e6dcffec92345a2dfc5d0263189", view["headline_reason"])
        self.assertIn(self.CHECKPOINT, view["headline_reason"])
        self.assertEqual(view["review_verdict"], self.VERDICT)
        for text in self.surfaces(doc):
            self.assertIn("READY FOR INTEGRATION", text)
            self.assertNotIn("DONE", text)
        self.assertEqual(doc, before, "interpretation must be pure")

    def test_an_accepted_verdict_whose_candidate_is_NOT_IMPORTABLE_falls_back_to_ALL_PHASES_COMPLETE(self):
        for importable in (False, None, "yes"):
            with self.subTest(importable=importable):
                doc = self.snapshot(dict(self.VERDICT, importable=importable))
                view = model.job_view(doc, doc["jobs"][0])
                self.assertEqual(view["headline"], "ALL PHASES COMPLETE · REVIEW ACCEPTED")
                self.assertIn("Job closure has not been recorded", view["headline_reason"])
                for text in self.surfaces(doc):
                    self.assertNotIn("READY FOR INTEGRATION", text)

    def test_M386415_after_the_owner_records_6540775d_reads_DONE_everywhere_with_the_verdict_still_readable(self):
        for publish in (True, False):
            with self.subTest(verdict_published=publish):
                doc = self.snapshot(dict(self.VERDICT), publish=publish)
                doc["jobs"][0]["integration"] = copy.deepcopy(self.RECEIPT)
                view = model.job_view(doc, doc["jobs"][0])
                self.assertEqual(view["headline"], "DONE")
                self.assertIn("Integrated as 6540775d5f29bea86f71756486c092be9d0a3ccd from accepted candidate 340f8674", view["headline_reason"])
                self.assertEqual(view["review_verdict"], self.VERDICT if publish else None)
                self.assertEqual([phase["state"] for phase in view["phases"]], ["completed", "completed"])
                for text in self.surfaces(doc):
                    self.assertIn("DONE", text)
                    self.assertIn("6540775d5f29bea86f71756486c092be9d0a3ccd", text)

    # W386746 (owner ruling 2026-11-28): the owner's FINAL decision not to integrate the accepted candidate.
    DECLINED = {"job_id": JOB, "action": "decline-integration", "operation_id": "job.integration-recorded:x",
                "recorded_at": "2026-11-28T06:00:00.000Z",
                "recorded_by": {"participant": "baton.slaw", "principal": "principal:baton.slaw"},
                "candidate": {"checkpoint_id": CHECKPOINT, "head_object": "340f867479024e6dcffec92345a2dfc5d0263189",
                              "tree_object": "35686824a2f560f9c20e80d6905873dd0c89c41e", "verdict_id": "verdict-x",
                              "review_attempt_id": "attempt-review"},
                "reason": "Probe only; the owner keeps main unchanged.", "phases": []}

    def test_after_the_owner_DECLINES_it_reads_NOT_INTEGRATED_everywhere_with_the_accepted_review_and_candidate_readable(self):
        ready = self.snapshot(dict(self.VERDICT))
        doc = self.snapshot(dict(self.VERDICT))
        doc["jobs"][0]["integration_declined"] = copy.deepcopy(self.DECLINED)
        before = copy.deepcopy(doc)
        view = model.job_view(doc, doc["jobs"][0])
        self.assertEqual(view["headline"], "NOT INTEGRATED")
        self.assertEqual(view["headline_reason"],
                         'Owner declined to integrate accepted candidate 340f867479024e6dcffec92345a2dfc5d0263189; reason: '
                         '"Probe only; the owner keeps main unchanged."; checkpoint ' + self.CHECKPOINT
                         + "; recorded by baton.slaw at 2026-11-28T06:00:00.000Z.")
        self.assertEqual(view["review_verdict"], self.VERDICT)
        self.assertEqual(view["integration_declined"], self.DECLINED)
        self.assertIsNone(view["integration"])
        self.assertEqual(view["phases"], model.job_view(ready, ready["jobs"][0])["phases"], "phase rows are unchanged")
        for text in self.surfaces(doc):
            self.assertIn("NOT INTEGRATED", text)
            self.assertNotIn("READY FOR INTEGRATION", text)
            self.assertNotIn("DONE", text)
        status_text, monitor_list, detail, tui_list, tui_detail = self.surfaces(doc)
        for text in (status_text, detail, tui_list, tui_detail):
            self.assertIn("340f867479024e6dcffec92345a2dfc5d0263189", text)
            self.assertIn("Probe only; the owner keeps main unchanged.", text)
        self.assertEqual(doc, before, "interpretation must be pure")

    def test_a_DAMAGED_or_FOREIGN_decline_and_a_MANUAL_Job_never_read_NOT_INTEGRATED(self):
        for label, change in (("another Job", {"job_id": "job-other"}), ("no reason", {"reason": ""}),
                              ("no candidate", {"candidate": {}}), ("no checkpoint", {"candidate": {"head_object": "340f8674"}}),
                              ("no actor", {"recorded_by": None}), ("not a mapping", None)):
            with self.subTest(label):
                doc = self.snapshot(dict(self.VERDICT))
                doc["jobs"][0]["integration_declined"] = None if change is None else dict(self.DECLINED, **change)
                self.assertEqual(model.job_view(doc, doc["jobs"][0])["headline"], "READY FOR INTEGRATION")
        doc = self.snapshot(dict(self.VERDICT))
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open", integration_declined=copy.deepcopy(self.DECLINED))
        for stage in job["stages"]:
            stage["selected_at"] = NOW
        self.assertEqual(model.job_view(doc, job)["headline"], "AWAITING ASSIGNMENT")

    def test_a_DAMAGED_or_FOREIGN_receipt_and_a_MANUAL_Job_never_read_DONE(self):
        for label, change in (("another Job", {"job_id": "job-other"}), ("no target", {"target": {}}),
                              ("no actor", {"recorded_by": None}), ("not a mapping", None)):
            with self.subTest(label):
                doc = self.snapshot(dict(self.VERDICT))
                doc["jobs"][0]["integration"] = None if change is None else dict(self.RECEIPT, **change)
                self.assertEqual(model.job_view(doc, doc["jobs"][0])["headline"], "READY FOR INTEGRATION")
        doc = self.snapshot(dict(self.VERDICT))
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open", integration=copy.deepcopy(self.RECEIPT))
        for stage in job["stages"]:
            stage["selected_at"] = NOW
        self.assertEqual(model.job_view(doc, job)["headline"], "AWAITING ASSIGNMENT")

    def test_M386415_as_the_old_build_published_it_reads_ALL_PHASES_COMPLETE_without_a_verdict(self):
        """The retained snapshot itself carries no review_verdict member: no verdict is invented."""
        doc = self.snapshot(publish=False)
        view = model.job_view(doc, doc["jobs"][0])
        self.assertEqual(view["headline"], "ALL PHASES COMPLETE")
        self.assertIsNone(view["review_verdict"])
        for text in self.surfaces(doc):
            self.assertIn("ALL PHASES COMPLETE", text)
            self.assertNotIn("REVIEW ACCEPTED", text)

    def test_a_MISSING_FOREIGN_or_DAMAGED_verdict_never_reads_REVIEW_ACCEPTED(self):
        cases = {
            "null (read, none matches -- including a verdict on another checkpoint)": None,
            "another attempt": dict(self.VERDICT, attempt_id="attempt-other"),
            "unknown disposition": dict(self.VERDICT, disposition="approved"),
            "no checkpoint": dict(self.VERDICT, checkpoint_id=""),
            "not a mapping": "accepted",
        }
        for label, verdict in cases.items():
            with self.subTest(case=label):
                doc = self.snapshot(verdict)
                self.assertEqual(model.job_view(doc, doc["jobs"][0])["headline"], "ALL PHASES COMPLETE")
                for text in self.surfaces(doc):
                    self.assertNotIn("REVIEW ACCEPTED", text)
        doc = self.snapshot(dict(self.VERDICT))
        doc["jobs"][0]["stages"].append(dict(doc["jobs"][0]["stages"][1], stage_id=self.JOB + "/second-review"))
        self.assertEqual(model.job_view(doc, doc["jobs"][0])["headline"], "ALL PHASES COMPLETE",
                         "two review stages: no single verdict is the Job's")

    def test_a_verdict_beside_an_UNFINISHED_phase_changes_nothing(self):
        doc = self.snapshot(dict(self.VERDICT))
        doc["jobs"][0]["stages"][0]["state"] = "queued"
        self.assertNotIn("ALL PHASES COMPLETE", model.job_view(doc, doc["jobs"][0])["headline"])

    def test_MANUAL_owner_close_rules_are_unchanged(self):
        doc = self.snapshot(dict(self.VERDICT))
        doc["schema"] = stack.MANUAL_STATUS_SCHEMA
        job = doc["jobs"][0]
        job.update(mode="MANUAL", lifecycle="open")
        for stage in job["stages"]:
            stage["selected_at"] = NOW
        self.assertEqual(model.job_view(doc, job)["headline"], "AWAITING ASSIGNMENT")
        job.update(lifecycle="closed", closed_at=NOW)
        self.assertEqual(model.job_view(doc, job)["headline"], "CLOSED")


class ASettledRemovalReadsWhatTheProductRecorded(unittest.TestCase):
    """W386766 (owner ruling 2026-11-28): a settlement removal on every surface, from its published record."""

    check = JobHeadlines.check
    LEGACY = "Stopped — runtime removed by settlement. Original ending unknown."
    RETAINED = 'Stopped — agent fault after describe (no manifest). Runtime removed by settlement: "settlement: M386700".'

    def removed(self, terminal=None, cancellation=None):
        doc = document()
        job = doc["jobs"][0]
        job["stages"][0].update(state="exceptional", exchange=None,
                                removal={"attempt_id": "attempt-a", "reason": "settlement: M386700", "removed": True,
                                         "execution_runtime": "destroyed", "cleanup": "retained", "terminal": terminal})
        job["stages"][0]["runtime"]["execution_runtime"] = "destroyed"
        if cancellation:
            job["cancellation"] = {"trigger": "operator", "shutdown": cancellation, "targets": [
                {"stage_id": "implementation", "episode": 1, "attempt_id": "attempt-a", "state": "ended-before-request"}]}
        return doc

    FAULT = {"ending": "faulted", "fault_code": "agent", "answered": ["describe"], "disposition": None, "manifest_digest": None}

    def test_a_legacy_removal_says_its_ending_is_unknown_and_is_FAILED_until_cancellation_completes(self):
        self.check(self.removed(), "FAILED", "stopped; admission admitted", self.LEGACY)
        self.check(self.removed(cancellation="unresolved"), "FAILED", self.LEGACY,
                   reason="Cancellation also recorded: operator; shutdown unresolved.")
        self.check(self.removed(cancellation="complete"), "CANCELLED", "stopped; admission admitted", self.LEGACY,
                   reason="Cancellation shutdown complete")

    def test_a_retained_fault_shows_the_fault_and_the_settlement_reason_and_keeps_FAILED(self):
        self.check(self.removed(self.FAULT), "FAILED", "stopped; admission admitted", self.RETAINED)
        self.check(self.removed(self.FAULT, cancellation="complete"), "FAILED", self.RETAINED,
                   reason="Cancellation also recorded: operator; shutdown complete.")
        adapter = dict(self.FAULT, adapter_failure={"component": "role-adapter", "code": next(iter(model._STATUS_ADAPTER_CODES))})
        self.check(self.removed(adapter), "FAILED", "agent fault; " + adapter["adapter_failure"]["code"] + " after describe")

    def test_R1_a_retained_fault_keeps_FAILED_for_BOTH_cancellation_target_histories(self):
        """Review 2026-11-28T06-17-31Z R1: a `ceased` target puts a stop word on the attempt; the fault still wins."""
        for target in ("ended-before-request", "ceased"):
            with self.subTest(target=target):
                doc = self.removed(self.FAULT, cancellation="complete")
                doc["jobs"][0]["cancellation"]["targets"][0]["state"] = target
                self.check(doc, "FAILED", self.RETAINED, reason="Cancellation also recorded: operator; shutdown complete.")
                legacy = self.removed(cancellation="complete")
                legacy["jobs"][0]["cancellation"]["targets"][0]["state"] = target
                self.check(legacy, "CANCELLED", self.LEGACY, reason="Cancellation shutdown complete")

    def test_R2_a_DECLARED_removal_is_not_a_removal_until_the_runtime_record_confirms_it(self):
        """Review R2: the declaration commits before the fence and destroy; an interrupted removal shows where it stopped."""
        for runtime, cleanup, removed in (("running", "pending", False), ("quiescent", None, False),
                                          ("destroyed", "pending", False), ("destroyed", "retained", None)):
            with self.subTest(runtime=runtime, cleanup=cleanup, removed=removed):
                doc = self.removed(self.FAULT)
                stage = doc["jobs"][0]["stages"][0]
                stage["runtime"]["execution_runtime"] = runtime
                stage["removal"].update(removed=removed, execution_runtime=runtime, cleanup=cleanup)
                if runtime == "running":    # a stale removal copy never overrides the published runtime
                    stage["removal"].update(execution_runtime="destroyed")
                stage["exchange"] = {"terminal": dict(self.FAULT, fault_code="agent")}
                rendered = "".join(views(doc))
                self.assertNotIn("Runtime removed by settlement", rendered)
                self.assertIn("settlement removal declared, not confirmed: runtime " + runtime + ", cleanup "
                              + (cleanup or "unknown"), rendered)
                self.assertIn("agent fault", rendered)          # the current fault evidence stays visible
                self.assertIn("failed; admission admitted", rendered)
                self.check(doc, "FAILED")
                legacy = self.removed(cancellation="complete")
                legacy["jobs"][0]["stages"][0]["removal"].update(removed=removed, execution_runtime=runtime, cleanup=cleanup)
                legacy["jobs"][0]["stages"][0]["runtime"]["execution_runtime"] = runtime
                self.assertNotIn(self.LEGACY, "".join(views(legacy)))
        # And once the record confirms it, the same removal reads as removed.
        self.check(self.removed(self.FAULT), "FAILED", "stopped; admission admitted", self.RETAINED)

    def test_a_completed_or_genuinely_starting_attempt_is_not_read_as_removed(self):
        doc = self.removed(self.FAULT)
        doc["jobs"][0]["stages"][0]["state"] = "completed"
        self.check(doc, "ALL PHASES COMPLETE", "done; admission admitted")
        self.assertNotIn("Runtime removed by settlement", "".join(views(doc)))
        doc = document()
        doc["jobs"][0]["stages"][0].update(state="starting", exchange=None)
        self.check(doc, "ADMITTED", "admitted; admission admitted")
        self.assertNotIn("Stopped", "".join(views(doc)))

    def test_a_foreign_or_damaged_removal_record_is_ignored(self):
        for removal in ({"attempt_id": "attempt-b", "reason": "x", "terminal": None}, {"attempt_id": "attempt-a", "reason": "", "terminal": None},
                        {"attempt_id": "attempt-a", "reason": "x", "terminal": "faulted"}, "removed"):
            with self.subTest(removal=removal):
                doc = self.removed()
                doc["jobs"][0]["stages"][0]["removal"] = removal
                rendered = "".join(views(doc))
                self.assertNotIn("removed by settlement", rendered)
                self.assertIn("failed; admission admitted", rendered)
