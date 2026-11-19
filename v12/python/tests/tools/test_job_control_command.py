"""W383217 — the finite Job control over the installed serving composition.

The same disposable installed instance and REAL composed stage deployment
the cancellation commands are proved over, with the Job admitted under the
first documentation profile and a clock the case moves. The serving sweep
derives the deadlines from the stores' own instants, journals the first one
reached as the fence and orders cessation through the accepted owners; the
installed `cancel-status` reports the control and the fence read-only.
"""
import json
import os
from pathlib import Path
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, cancellation, documents,
                                   job_control, review_driver, scheduler,
                                   submit, sweep)
from baton_v12.worker_manager import ControlStore, oci
from baton_v12.worker_manager.failure_cause import attempt_cessation_outcome_of
from tools import instance, stack_command, stage_execution
from tools import job_cancellation as command
from tests.job_manager import fixtures
from tests.job_manager.test_job_control import PROFILE, at
from tests.tools import test_job_cancellation_command as cancel_tests
from tests.tools import test_stage_execution as composed_tests

STAGE_SECONDS = 4800
JOB_SECONDS = 9960


class InstalledControl(cancel_tests.InstalledCancellation):
    """The installed cancellation fixture, with a movable clock and a Job
    admitted under the profile."""

    def setUp(self):
        composed_tests.ComposedOneJobCase.setUp(self)
        self.now = fixtures.NOW
        self.places = instance.layout(self.root)
        Path(self.places["stores"]).mkdir()
        os.rename(self.authority_path, self.places["authority_store"])
        self.authority_path = self.places["authority_store"]
        self.config["authority_store"] = self.authority_path
        self.job_path = self.places["job_store"]
        self.control_path = self.places["control_store"]
        distro = Path(self.places["distro"])
        distro.mkdir(parents=True)
        Path(self.places["command"]).write_text("deterministic packaged fixture")
        selector = instance.emit(self.root,
                                 authority_uuid=self.config["authority_uuid"],
                                 identity={"fixture": True},
                                 runtime=instance.manifest(distro), now=1)
        instance.publish(self.places["instance"], selector)
        self.deployment_document = self.composed_document(line_declared_base=self.base)
        Path(self.places["deployment"]).write_text(json.dumps(self.deployment_document))
        self.patch_checkout = mock.patch("tools.stage_execution._checkout",
                                         return_value=self.checkout)
        self.patch_checkout.start()
        self.addCleanup(self.patch_checkout.stop)
        self.submission["schema"] = documents.SUBMISSION_CONTROL_SCHEMA
        self.submission["jobs"][0]["control"] = {"profile": PROFILE}
        self.jobs, self.control, self.composed = self.serving()
        submit(self.jobs, self.submission)
        self.stage_id = "job-a/implementation"

    def stores(self, incarnation):
        from tests.tools.test_single_worker import AUTHORITY_UUID
        job = JobStore.open(self.job_path, authority_uuid=AUTHORITY_UUID,
                            incarnation=incarnation, clock=lambda: self.now)
        control = ControlStore.open(self.control_path,
                                    incarnation=incarnation,
                                    clock=lambda: self.now)
        self.addCleanup(job.close)
        self.addCleanup(control.close)
        return job, control

    def serving(self, **members):
        self.engine = self.quiescing()
        job, control = self.stores("stage-composed")
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **members),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: self.now, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return job, control, composed

    def tick(self, seconds=None):
        if seconds is not None:
            self.now = at(seconds)
        return sweep(self.jobs, self.composed, now=self.now)

    def drive(self, job, composed, kind, want, ticks=10):
        for _ in range(ticks):
            sweep(job, composed, now=self.now)
            held = self.states(job, composed)
            if held.get(kind) == want:
                return held
        self.fail(f"the {kind} stage never reached {want!r}: "
                  f"{self.states(job, composed)}")

    def call(self, verb, reason=None, job_id="job-a", at=None):
        return command.execute(verb, self.places["instance"], job_id=job_id,
                               reason=reason,
                               clock=lambda: self.now if at is None else at)

    def control_report(self, **named):
        return self.call("cancel-status", **named)["control"]

    def refusing_stop(self, count=1):
        """The adapter's stop refuses `count` times at the real boundary."""
        original = oci.OciAdapter.stop
        remaining = [count]

        def stop(adapter, request):
            if remaining[0] > 0:
                remaining[0] -= 1
                raise ContractRefusal("refused", "precondition",
                                      "injected transient stop refusal")
            return original(adapter, request)

        held = mock.patch.object(oci.OciAdapter, "stop", stop)
        held.start()
        self.addCleanup(held.stop)

    def deployment(self, role="review"):
        """The role's composed `StageDeployment`, which owns `routed`."""
        return self.worker_of(self.composed, role).stage.deployment

    def expiries(self):
        return self.jobs._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = 'job.expire'"
        ).fetchone()[0]


class TheDeadlineWhileServing(InstalledControl):

    def test_a_running_stage_is_stopped_at_its_stage_deadline_through_the_composition(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        starts = len(self.engine.starts)
        self.assertEqual(starts, 1)
        held = self.control_report()
        # THE ORIGIN IS THE OWNER'S OFFER INSTANT, read back from the admit
        # receipt, and the Job's is the submission's accepted instant.
        offer = self.control._connection.execute(
            "SELECT settled_at FROM operations WHERE kind = 'offer.issue'"
        ).fetchone()["settled_at"]
        self.assertEqual(held["stages"][0]["origin"], offer)
        self.assertEqual(held["job"]["origin"], fixtures.NOW)
        self.assertEqual(held["timing"], "trusted")
        self.assertIsNone(held["fence"])
        self.assertIsNone(self.report())
        # ONE SECOND BEFORE: nothing.
        report = self.tick(STAGE_SECONDS - 1)
        self.assertNotIn("expired", report)
        self.assertEqual(self.stops(), [])
        # AT THE DEADLINE: fenced, and the exact runtime ordered to cease
        # through the accepted owner -- one stop, one journalled intent.
        report = self.tick(STAGE_SECONDS)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "fenced",
                           "trigger": "stage-deadline",
                           "stage_id": self.stage_id,
                           "deadline_at": at(STAGE_SECONDS)}])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        status = self.report()
        self.assertEqual(status["trigger"], "stage-deadline")
        self.assertEqual(status["requested_at"], at(STAGE_SECONDS))
        self.assertEqual(status["observed_at"], at(STAGE_SECONDS))
        self.assertEqual(status["targets"][0]["state"], "ordered")
        self.assertEqual(self.control_report()["fence"]["trigger"],
                         "stage-deadline")
        self.assertEqual(self.report(at=at(STAGE_SECONDS + 30))["shutdown"],
                         "within-bound")
        self.assertEqual(self.report(at=at(STAGE_SECONDS + 121))["shutdown"],
                         "unresolved")
        # LATER TICKS: one record, no second order, nothing started again.
        for seconds in (STAGE_SECONDS + 1, STAGE_SECONDS + 2):
            later = self.tick(seconds)
            self.assertNotIn("expired", later)
            self.assertNotIn("cancelled", later)
        self.assertEqual(self.expiries(), 1)
        self.assertEqual(len(self.stops()), 1)
        self.assertEqual(len(self.engine.starts), starts)

    def test_a_claimed_stage_is_fenced_and_never_started_after_the_deadline(self):
        unready = self.claimed()
        report = self.tick(STAGE_SECONDS)
        self.assertEqual(report["expired"][0]["outcome"], "fenced")
        self.assertEqual([one["outcome"] for one in report["started"]],
                         ["deferred"])
        self.assertIn("expired", report["started"][0]["detail"]["message"])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("fence-unstarted", "ordered")])
        self.assertEqual(self.engine.starts, [])
        self.assertEqual(self.journalled("attempt.abandon"), 1)
        # A LATE LAUNCH CANNOT REOPEN IT at the Authority either.
        unready.stop()
        from baton_v12.job_manager import job_of
        with self.assertRaises(ContractRefusal):
            self.composed.launch(self.attempting(self.jobs, self.stage_id),
                                 job_of(self.jobs, "job-a"))
        self.tick(STAGE_SECONDS + 5)
        self.assertEqual(self.engine.starts, [])
        self.assertEqual(self.report()["targets"][0]["state"],
                         "fenced-unstarted")

    def test_a_queued_job_is_retired_at_the_job_deadline_and_reserves_nothing(self):
        report = self.tick(JOB_SECONDS)
        self.assertEqual(report["expired"][0]["trigger"], "job-deadline")
        self.assertEqual(report["acts"], [])
        for _ in range(2):
            self.tick(JOB_SECONDS + 1)
        self.assertEqual(self.engine.starts, [])
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])
        status = self.report()
        self.assertEqual(status["targets"][0]["state"],
                         "retired-before-admission")
        self.assertEqual(status["shutdown"], "complete")
        self.assertEqual(status["trigger"], "job-deadline")

    def test_the_fence_and_the_elapsed_time_survive_a_restart(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.tick(STAGE_SECONDS)
        self.assertEqual(len(self.stops()), 1)
        self.composed.close()
        self.jobs, self.control, self.composed = self.serving()
        report = self.tick(STAGE_SECONDS + 5)
        self.assertNotIn("expired", report)
        self.assertEqual(self.expiries(), 1)
        self.assertEqual(self.journalled("attempt.cancel"), 1)
        held = self.control_report()
        self.assertEqual(held["stages"][0]["elapsed_seconds"],
                         STAGE_SECONDS + 5)
        self.assertEqual(held["fence"]["requested_at"], at(STAGE_SECONDS))
        self.assertEqual(held["watermark"], at(STAGE_SECONDS + 5))
        self.assertEqual(self.report()["requested_at"], at(STAGE_SECONDS))

    def test_a_clock_rollback_holds_admission_and_is_reported(self):
        self.now = at(300)
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        report = self.tick(100)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "held",
                           "detail": {"category": "uncertain",
                                      "code": "timing",
                                      "watermark": at(300),
                                      "observed_at": at(100)}}])
        held = self.control_report()
        self.assertEqual(held["timing"], "uncertain")
        self.assertEqual(held["watermark"], at(300))
        self.assertEqual(held["stages"][0]["elapsed_seconds"], 0)
        self.assertIsNone(held["fence"])
        self.assertEqual(self.stops(), [])
        report = self.tick(400)
        self.assertNotIn("expired", report)
        self.assertEqual(self.control_report()["timing"], "trusted")

    def test_an_unresolved_shutdown_retains_the_hold_and_keeps_asking(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.refusing_stop(2)
        report = self.tick(STAGE_SECONDS)
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "deferred")])
        self.assertEqual(self.stops(), [])
        self.assertEqual(self.report()["targets"][0]["state"], "order-failed")
        report = self.tick(STAGE_SECONDS + 121)
        self.assertEqual(report["cancelled"][0]["outcome"], "deferred")
        status = self.report()
        self.assertEqual(status["shutdown"], "unresolved")
        self.assertEqual(status["targets"][0]["state"], "order-failed")
        # THE HOLD STANDS: the allocation is still reserved, nothing freed.
        self.assertEqual([one["allocation_state"]
                          for one in scheduler.allocation_rows(self.jobs)],
                         ["reserved"])
        report = self.tick(STAGE_SECONDS + 122)
        self.assertEqual(report["cancelled"][0]["outcome"], "ordered")
        self.assertEqual(len(self.stops()), 1)
        recorded = attempt_cessation_outcome_of(self.control, self.attempt_id(),
                                                "cancellation")
        self.assertEqual(recorded["outcome"], "ordered")
        self.assertEqual(self.report()["shutdown"], "unresolved")

    def test_an_operator_request_before_the_deadline_is_the_fence(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        self.now = at(10)
        self.cancel()
        report = self.tick(STAGE_SECONDS)
        self.assertNotIn("expired", report)
        self.assertEqual(self.expiries(), 0)
        status = self.report()
        self.assertEqual(status["trigger"], "operator")
        self.assertEqual(status["requested_at"], at(10))
        self.assertEqual(self.control_report()["fence"]["trigger"], "operator")


class TheCorrectionAndTheCommand(InstalledControl):

    def test_a_changes_requested_verdict_opens_no_round_under_the_profile(self):
        stage = self.attempting(self.jobs, self.stage_id)
        answered = {"outcome": "correction", "line_id": "line-1",
                    "checkpoint_id": "checkpoint-1", "verdict_id": "verdict-1"}
        with mock.patch.object(review_driver, "open_correction",
                               side_effect=AssertionError("opened")):
            held = self.deployment().routed(stage, answered)
        self.assertIsNone(held["correction"])
        declined = held["correction_declined"]
        self.assertEqual(declined["policy"], "job-control")
        self.assertEqual(declined["profile"], PROFILE)
        self.assertEqual((declined["allowance"], declined["used"]), (0, 0))
        # A JOB UNDER NO PROFILE still follows the deployment's own policy.
        other = dict(stage, job_id="job-nobody")
        with mock.patch.object(review_driver, "open_correction",
                               return_value={"opened": True}) as opened:
            held = self.deployment().routed(other, answered)
        self.assertEqual(held["correction"], {"opened": True})
        self.assertEqual(opened.call_count, 1)

    def test_cancel_status_reports_the_control_read_only_and_the_dispatch_carries_it(self):
        self.drive(self.jobs, self.composed, "implementation", "waiting")
        before = self.logical()
        with mock.patch.object(JobStore, "open",
                               side_effect=AssertionError("writable Jobs")), \
                mock.patch.object(ControlStore, "open",
                                  side_effect=AssertionError("writable control")):
            answer = self.call("cancel-status")
        self.assertEqual(answer["schema"], command.SCHEMA)
        self.assertEqual(answer["control"]["profile"], PROFILE)
        self.assertEqual(answer["control"]["resolved"]["stage_seconds"],
                         STAGE_SECONDS)
        self.assertEqual(self.logical(), before)
        import io
        from tools import job_manager
        output = io.StringIO()
        with mock.patch.object(job_manager, "_utc_clock",
                               return_value=lambda: self.now), \
                mock.patch("sys.stdout", output):
            self.assertEqual(stack_command.main(
                ["manager", "cancel-status", "--instance",
                 self.places["instance"], "--job", "job-a"]), 0)
        self.assertEqual(json.loads(output.getvalue())["control"]["profile"],
                         PROFILE)

    def test_a_stale_profile_is_refused_at_submit_and_nothing_is_recorded(self):
        stale = json.loads(json.dumps(self.submission))
        stale["submission_id"] = "sub-stale"
        stale["jobs"][0]["job_id"] = "job-stale"
        stale["jobs"][0]["control"] = {"profile": "documentation/9"}
        before = self.logical()
        with self.assertRaises(ContractRefusal):
            submit(self.jobs, stale)
        self.assertEqual(self.logical(), before)
        self.assertIsNone(job_control.control_of(self.jobs, "job-stale"))
