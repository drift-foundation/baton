"""W383217 — the persisted finite control of a Job: profile, clocks, fences.

DESIGN LIM-5. A Job admitted under a control profile carries its correction
allowance and its stage/Job wall deadlines in this store's journal, inside
the submission that admitted it. The deadlines are derived from durable
origins -- the submission's accepted instant and the Worker Manager's own
instant of each stage's admission -- against a trusted clock that persists
its watermark, and the first one reached is journalled as the Job's fence,
which the accepted cancellation owners carry out. These cases drive the Job
store half against real disposable stores and the strict fake operations.
"""

import json
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, STATUS_SCHEMA, cancellation,
                                   documents, episodes, fresh_attempt,
                                   job_control, scheduler, status, submit,
                                   sweep)
from baton_v12.job_manager.episodes import end_episode, live_of, open_next
from baton_v12.job_manager.projection import owed_acts

from tests.job_manager import test_fresh_attempt as fresh
from tests.job_manager import test_job_cancellation as cancelling
from tests.job_manager import test_scheduling as scheduling

if __package__:
    from .fixtures import (NOW, UUID, JobManagerCase, job, signature_of,
                           stage, submission)
else:
    from fixtures import (NOW, UUID, JobManagerCase, job, signature_of,
                          stage, submission)

PROFILE = "documentation/1"
STAGE_SECONDS = 4800
JOB_SECONDS = 9960
REASON = "operator stops this Job before its deadline"


def at(seconds):
    """NOW plus `seconds`, in the store's frozen instant grammar."""
    origin = datetime.strptime(NOW, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc)
    moment = origin + timedelta(seconds=seconds)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def controlled(job_id="job-a", stages=None, profile=PROFILE, limits=None,
               submission_id="sub-1"):
    """A /3 submission of one Job admitted under `profile`."""
    held = job(job_id, stages=stages if stages is not None
               else [stage("implementation")])
    held["control"] = {"profile": profile}
    if limits is not None:
        held["execution_limits"] = limits
    document = submission(submission_id=submission_id, jobs=[held])
    document["schema"] = documents.SUBMISSION_CONTROL_SCHEMA
    return document


class Controlling(cancelling.Cancelling):
    """The cancellation fake, whose journal stamps the OWNER'S instant.

    The real Worker Manager stamps `settled_at` on the `offer.issue` it
    commits; this store reads that instant back out of its admit receipt as
    the stage's origin. The fixture's constant `NOW` stamp hid the difference
    between the owner's instant and the local receipt time, which is the
    whole of review 2026-11-18T22-37-33Z's first correction.
    """

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.settled = NOW

    def committed(self, act, offer_id, result=None, intent=None):
        from baton_v12.job_manager import canonical_operation

        operation_id = canonical_operation(act, offer_id)
        self.journal[operation_id] = {
            "operation_id": operation_id, "kind": f"offer.{act}",
            "signature": signature_of(act, intent), "state": "committed",
            "result": json.dumps(result if result is not None
                                 else {"offer_id": offer_id}),
            "refusal": None, "settled_at": self.settled}
        return operation_id


class ControlCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = Controlling()

    def submit(self, document=None):
        return submit(self.jobs, document if document is not None
                      else controlled())

    def tick(self, seconds=0):
        """One sweep at NOW + seconds, with the store's clock there too."""
        self.instants.append(at(seconds))
        return sweep(self.jobs, self.acts, now=at(seconds))

    def projected(self, job_id="job-a", seconds=None):
        if seconds is not None:
            self.instants.append(at(seconds))
        document = status(self.jobs, self.acts, observed_at=self.clock())
        self.assertEqual(document["schema"], STATUS_SCHEMA)
        for entry in document["jobs"]:
            if entry["job_id"] == job_id:
                return entry
        raise AssertionError(job_id)

    def evaluation(self, job_id="job-a", seconds=None):
        now = at(seconds) if seconds is not None else self.clock()
        return job_control.evaluate(self.jobs._connection, job_id, now)

    def operations(self, kind):
        return self.jobs._connection.execute(
            "SELECT count(*) FROM operations WHERE kind = ?",
            (kind,)).fetchone()[0]

    def running(self, stage_id="job-a/implementation", seconds=0):
        self.acts.starts(stage_id, attaches=True)
        for _ in range(4):
            self.tick(seconds)
        held = self.projected()["stages"][0]
        self.assertIn(held["state"], ("starting", "waiting", "running"), held)
        return held


class TheSelection(unittest.TestCase):

    def test_the_first_profile_is_exactly_the_owner_ruling(self):
        held = job_control.resolved(PROFILE)
        self.assertEqual(held, {"profile": PROFILE, "units": "seconds",
                                "correction_rounds": 0,
                                "stage_seconds": 4800, "job_seconds": 9960,
                                "provider_turn_seconds": 3600,
                                "verification_command_seconds": 900})

    def test_a_profile_this_build_does_not_hold_is_a_stale_selection(self):
        for value in ({"profile": "documentation/2"}, {"profile": ""},
                      {"profile": None}, {}, {"profile": PROFILE, "x": 1},
                      None, PROFILE):
            with self.assertRaises(ContractRefusal, msg=value):
                job_control.owned_control(value)

    def test_only_a_version_three_submission_carries_a_control(self):
        document = controlled()
        self.assertEqual(documents.owned_submission(document)["jobs"][0]
                         ["control"], {"profile": PROFILE})
        for schema in documents.SUBMISSION_SCHEMAS[:2]:
            older = controlled()
            older["schema"] = schema
            with self.assertRaises(ContractRefusal):
                documents.owned_submission(older)
        without = controlled()
        del without["jobs"][0]["control"]
        self.assertNotIn("control",
                         documents.owned_submission(without)["jobs"][0])
        null = controlled()
        null["jobs"][0]["control"] = None
        with self.assertRaises(ContractRefusal):
            documents.owned_submission(null)

    def test_a_job_whose_ceilings_disagree_with_the_profile_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            documents.owned_submission(controlled(
                limits={"provider_turn_seconds": 7200}))
        self.assertIn("pins provider_turn_seconds at 3600",
                      caught.exception.message)
        agreeing = documents.owned_submission(controlled(
            limits={"provider_turn_seconds": 3600,
                    "verification_command_seconds": 900}))
        self.assertEqual(agreeing["jobs"][0]["control"], {"profile": PROFILE})


class TheAdmission(ControlCase):

    def test_the_control_is_journalled_inside_the_submission(self):
        recorded = self.submit()
        held = job_control.control_of(self.jobs, "job-a")
        self.assertEqual(held["profile"], PROFILE)
        self.assertEqual(held["resolved"]["stage_seconds"], STAGE_SECONDS)
        self.assertEqual(held["resolved"]["job_seconds"], JOB_SECONDS)
        self.assertEqual(held["admitted_at"], recorded["recorded_at"])
        self.assertEqual(held["operation_id"], "job.control:job-a")
        self.assertEqual(self.operations("job.control"), 1)
        # THE SAME ACT: the journal row settled with the submission.
        row = self.jobs.operation_record("job.control:job-a")
        self.assertEqual(row["settled_at"], NOW)

    def test_an_exact_replay_writes_nothing_and_a_changed_control_collides(self):
        first = self.submit()
        self.instants.append(at(10))
        self.assertEqual(self.submit(), first)
        self.assertEqual(self.operations("job.control"), 1)
        changed = controlled()
        del changed["jobs"][0]["control"]
        with self.assertRaises(ContractRefusal) as caught:
            self.submit(changed)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual(job_control.control_of(self.jobs, "job-a")
                         ["profile"], PROFILE)

    def test_the_control_survives_a_restart_and_a_job_without_one_is_null(self):
        self.submit()
        self.submit(submission(submission_id="sub-2", jobs=[
            job("job-b", stages=[stage("implementation", "0000000a-W3")])]))
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2", clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(job_control.control_of(reopened, "job-a")["profile"],
                         PROFILE)
        self.assertIsNone(job_control.control_of(reopened, "job-b"))
        self.assertIsNone(self.projected("job-b")["control"])
        held = self.projected("job-a")["control"]
        self.assertEqual(held["profile"], PROFILE)
        self.assertEqual(held["timing"], "trusted")
        self.assertIsNone(held["fence"])
        self.assertEqual(held["corrections"], {"allowance": 0, "used": 0})

    def test_the_resolution_a_submission_carries_cannot_disagree_at_submit(self):
        document = controlled(limits={"provider_turn_seconds": 3600})
        with mock.patch.object(job_control, "PROFILES", {
                PROFILE: dict(job_control.PROFILES[PROFILE],
                              provider_turn_seconds=1800)}):
            with self.assertRaises(ContractRefusal):
                self.submit(document)
        self.assertEqual(self.operations("job.control"), 0)
        self.assertIsNone(self.jobs.operation_record("job.control:job-a"))


class TheClocks(ControlCase):

    def test_the_job_clock_starts_at_accepted_creation_and_counts_queue_time(self):
        self.submit()
        held = self.evaluation(seconds=100)
        self.assertEqual(held["job"]["origin"], NOW)
        self.assertEqual(held["job"]["deadline_at"], at(JOB_SECONDS))
        self.assertEqual(held["job"]["elapsed_seconds"], 100)
        self.assertFalse(held["job"]["reached"])
        # NOT ADMITTED YET: no stage origin, no stage deadline.
        #
        # W385695 added `sub_bound` to every stage view, and `None` is what an
        # ordinary profile answers: only the publication recovery's profile
        # bounds a stage KIND any further than `stage_seconds`, so a stage of
        # any other Job carries the member and no narrower ceiling.
        self.assertEqual(held["stages"], [{"stage_id": "job-a/implementation",
                                          "origin": None, "deadline_at": None,
                                          "stage_wall_at": None,
                                          "sub_bound": None,
                                          "elapsed_seconds": None,
                                          "reached": False}])
        self.assertIsNone(held["first"])

    def test_the_stage_clock_starts_at_the_owners_admission_instant(self):
        """The owner stamped the offer at +100; this store learned of it
        at +500. The origin is the owner's."""
        self.submit()
        self.acts.settled = at(100)
        self.tick(500)
        receipt = self.projected()["stages"][0]["receipts"][0]
        self.assertEqual(receipt["act"], "admit")
        self.assertEqual(receipt["recorded_at"], at(500))
        self.assertEqual(receipt["detail"]["settled_at"], at(100))
        held = self.evaluation(seconds=500)
        self.assertEqual(held["stages"][0]["origin"], at(100))
        self.assertEqual(held["stages"][0]["deadline_at"],
                         at(100 + STAGE_SECONDS))
        self.assertEqual(held["stages"][0]["elapsed_seconds"], 400)

    def test_a_delayed_adoption_keeps_the_owners_instant(self):
        """The owner committed the offer at +100 and the reply was lost; a
        later incarnation adopts it at +900 and the origin does not move."""
        self.submit()
        attempt = self.attempting(self.jobs)
        self.acts.settled = at(100)
        from baton_v12.job_manager import stage_intent
        from baton_v12.job_manager import job_of
        self.acts.committed("admit", attempt["offer_id"],
                            intent=stage_intent(attempt,
                                                job_of(self.jobs, "job-a")))
        report = self.tick(900)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]][0],
                         ("admit", "adopted"))
        held = self.evaluation(seconds=900)
        self.assertEqual(held["stages"][0]["origin"], at(100))
        self.assertEqual(held["stages"][0]["elapsed_seconds"], 800)

    def test_a_replacement_episode_never_resets_the_stage_origin(self):
        self.submit()
        self.acts.settled = at(100)
        self.tick(100)
        live = live_of(self.jobs, "job-a/implementation")
        end_episode(self.jobs, live, "abandoned-after-restart", 1)
        self.acts.settled = at(3000)
        report = self.tick(3000)
        self.assertEqual(len(report["replaced"]), 1)
        self.assertEqual(live_of(self.jobs, "job-a/implementation")
                         ["episode"], 2)
        held = self.evaluation(seconds=3000)
        self.assertEqual(held["stages"][0]["origin"], at(100))
        self.assertEqual(held["stages"][0]["deadline_at"],
                         at(100 + STAGE_SECONDS))

    def test_the_first_deadline_is_the_stage_or_the_job_by_the_instants(self):
        self.submit()
        self.acts.settled = at(100)
        self.tick(100)
        held = self.evaluation(seconds=100 + STAGE_SECONDS)
        self.assertEqual(held["first"], {"trigger": "stage-deadline",
                                         "stage_id": "job-a/implementation",
                                         "deadline_at":
                                             at(100 + STAGE_SECONDS)})
        self.assertFalse(held["job"]["reached"])
        # A STAGE ADMITTED LATE: its deadline falls after the Job's.
        self.setUp()
        self.submit()
        self.acts.settled = at(6000)
        self.tick(6000)
        held = self.evaluation(seconds=JOB_SECONDS)
        self.assertEqual(held["first"], {"trigger": "job-deadline",
                                         "stage_id": None,
                                         "deadline_at": at(JOB_SECONDS)})
        self.assertTrue(held["stages"][0]["deadline_at"] > at(JOB_SECONDS))

    def test_a_receipt_without_the_owners_instant_is_uncertain(self):
        self.submit()
        self.tick(0)
        self.jobs._connection.execute(
            "UPDATE receipts SET detail = ? WHERE act = 'admit'",
            (json.dumps({"canonical_state": "committed", "result": None,
                         "refusal": None}),))
        held = self.evaluation(seconds=10)
        self.assertEqual(held["timing"], "uncertain")
        self.assertIsNone(held["stages"][0]["origin"])


class TheTrustedClock(ControlCase):

    def test_the_watermark_persists_and_a_rollback_holds_admission(self):
        self.submit()
        self.assertIsNone(job_control.watermark_in(self.jobs._connection))
        self.tick(200)
        self.assertEqual(job_control.watermark_in(self.jobs._connection),
                         at(200))
        # THE REVIEWER'S EXAMPLE: origin+200 observed, then origin+100.
        held = self.evaluation(seconds=100)
        self.assertEqual(held["timing"], "uncertain")
        self.assertEqual(held["job"]["elapsed_seconds"], 200)
        self.assertEqual(held["watermark"], at(200))
        report = self.tick(100)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "held",
                           "detail": {"category": "uncertain",
                                      "code": "timing",
                                      "watermark": at(200),
                                      "observed_at": at(100)}}])
        self.assertEqual(job_control.watermark_in(self.jobs._connection),
                         at(200))
        self.assertEqual(self.projected()["control"]["timing"], "uncertain")
        # Nothing new was admitted: the stage was offered at +200 and the
        # claim is not owed while the clock is untrusted.
        self.acts.canonical_state(self.attempting(self.jobs)["offer_id"],
                                  self.attempting(self.jobs)["attempt_id"],
                                  "claimed")
        self.assertEqual(owed_acts(self.jobs, self.acts), [])
        # TRUSTED AGAIN once the clock passes the watermark.
        held = self.evaluation(seconds=300)
        self.assertEqual(held["timing"], "trusted")
        self.assertEqual(held["job"]["elapsed_seconds"], 300)
        self.instants.append(at(300))
        self.assertEqual([one["act"] for one in
                          owed_acts(self.jobs, self.acts)], ["claim"])

    def test_a_restart_on_an_earlier_clock_is_uncertain_until_it_catches_up(self):
        self.submit()
        self.tick(500)
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2",
                                 clock=lambda: at(50))
        self.addCleanup(reopened.close)
        held = job_control.evaluate(reopened._connection, "job-a", at(50))
        self.assertEqual(held["timing"], "uncertain")
        self.assertEqual(held["job"]["elapsed_seconds"], 500)
        held = job_control.evaluate(reopened._connection, "job-a", at(600))
        self.assertEqual(held["timing"], "trusted")
        self.assertEqual(held["job"]["elapsed_seconds"], 600)

    def test_a_rollback_never_unreaches_a_deadline_or_lifts_the_fence(self):
        self.submit()
        self.tick(JOB_SECONDS)
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["trigger"], "job-deadline")
        held = self.evaluation(seconds=10)
        self.assertEqual(held["timing"], "uncertain")
        self.assertTrue(held["job"]["reached"])
        self.assertEqual(held["first"]["trigger"], "job-deadline")
        self.tick(10)
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a"), fence)
        self.assertEqual(self.operations("job.expire"), 1)
        self.assertEqual(owed_acts(self.jobs, self.acts), [])

    def test_the_guards_advance_the_watermark_under_their_own_lock(self):
        self.submit()
        attempt = self.attempting(self.jobs)
        scheduler.activate_pool(self.jobs, scheduling.pool(),
                                scheduling.principals(scheduling.pool()))
        self.instants.append(at(700))
        scheduler.reserve(self.jobs, attempt)
        self.assertEqual(job_control.watermark_in(self.jobs._connection),
                         at(700))


class TheExpiryFence(ControlCase):

    def test_a_running_stage_past_its_deadline_is_fenced_and_ordered_to_cease(self):
        self.submit()
        self.running(seconds=0)
        self.assertEqual(self.acts.cancelled, [])
        report = self.tick(STAGE_SECONDS)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "fenced",
                           "trigger": "stage-deadline",
                           "stage_id": "job-a/implementation",
                           "deadline_at": at(STAGE_SECONDS)}])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(len(self.acts.cancelled), 1)
        self.assertIn("stage-deadline reached", self.acts.cancelled[0][1])
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["trigger"], "stage-deadline")
        self.assertEqual(fence["requested_at"], at(STAGE_SECONDS))
        self.assertEqual(fence["observed_at"], at(STAGE_SECONDS))
        held = self.projected()
        self.assertEqual(held["cancellation"]["trigger"], "stage-deadline")
        self.assertEqual(held["cancellation"]["trigger_at"],
                         at(STAGE_SECONDS))
        self.assertEqual(held["cancellation"]["targets"][0]["state"],
                         "ordered")
        self.assertEqual(held["control"]["fence"]["trigger"],
                         "stage-deadline")
        # THE BOUND RUNS FROM THE DEADLINE: within it at +30, unresolved at
        # +121 while nothing proves cessation.
        self.assertEqual(self.projected(seconds=STAGE_SECONDS + 30)
                         ["cancellation"]["shutdown"], "within-bound")
        self.assertEqual(self.projected(seconds=STAGE_SECONDS + 121)
                         ["cancellation"]["shutdown"], "unresolved")
        # ONE RECORD, HOWEVER MANY TICKS OBSERVE IT.
        for seconds in (STAGE_SECONDS + 1, STAGE_SECONDS + 2):
            later = self.tick(seconds)
            self.assertNotIn("expired", later)
        self.assertEqual(self.operations("job.expire"), 1)
        self.assertEqual(len(self.acts.cancelled), 1)

    def test_a_late_observation_reports_the_gap_not_a_new_trigger(self):
        """The manager was not serving when the deadline passed. The trigger
        is still the deadline; the observation is reported beside it and the
        bound is already exhausted, honestly."""
        self.submit()
        self.running(seconds=0)
        report = self.tick(STAGE_SECONDS + 500)
        self.assertEqual(report["expired"][0]["outcome"], "fenced")
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["requested_at"], at(STAGE_SECONDS))
        self.assertEqual(fence["observed_at"], at(STAGE_SECONDS + 500))
        held = self.projected()["cancellation"]
        self.assertEqual(held["trigger_at"], at(STAGE_SECONDS))
        self.assertEqual(held["observed_at"], at(STAGE_SECONDS + 500))
        self.assertEqual(held["shutdown"], "unresolved")
        self.assertEqual(held["elapsed_seconds"], 500)

    def test_a_queued_job_past_its_job_deadline_is_retired_before_admission(self):
        self.submit()
        report = self.tick(JOB_SECONDS)
        self.assertEqual(report["expired"][0]["trigger"], "job-deadline")
        self.assertEqual(report["acts"], [])
        self.assertEqual(self.acts.calls, [])
        held = self.projected()
        self.assertEqual(held["stages"][0]["state"], "queued")
        self.assertEqual(held["cancellation"]["targets"][0]["state"],
                         "retired-before-admission")
        self.assertEqual(held["cancellation"]["shutdown"], "complete")

    def test_a_claimed_stage_is_not_launched_after_the_deadline(self):
        self.submit()
        self.acts.starts("job-a/implementation", attaches=True)
        self.tick(0)
        attempt = self.attempting(self.jobs)
        self.acts.canonical_state(attempt["offer_id"], attempt["attempt_id"],
                                  "claimed")
        # THE CLAIM IS TAKEN BEFORE THE DEADLINE; the launch is asked after.
        self.instants.append(at(10))
        self.acts.refusals[("job-a/implementation", "launch")] = None
        with mock.patch.object(type(self.acts), "launch",
                               side_effect=ContractRefusal(
                                   "refused", "precondition", "not yet")):
            self.tick(10)
        self.assertEqual(self.projected()["stages"][0]["state"], "claimed")
        report = self.tick(STAGE_SECONDS)
        self.assertEqual(report["expired"][0]["outcome"], "fenced")
        self.assertEqual([(one["outcome"], one["detail"]["message"][:19])
                          for one in report["started"]],
                         [("deferred", "the Job was expired")])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("fence-unstarted", "ordered")])
        self.assertEqual([call for call in self.acts.calls
                          if call[0] == "launch"], [])

    def test_an_answered_attempt_is_left_to_its_ending_owners(self):
        """The expiry-versus-success race: the worker answered before the
        deadline tick. Nothing is ordered and the output stands."""
        self.submit()
        self.running(seconds=0)
        self.acts.frozen("job-a/implementation", "completed",
                         execution_runtime="running", cleanup=None)
        report = self.tick(STAGE_SECONDS)
        self.assertEqual(report["expired"][0]["outcome"], "fenced")
        self.assertNotIn("cancelled", report)
        self.assertEqual(self.acts.cancelled, [])
        held = self.projected()
        self.assertEqual(held["stages"][0]["state"], "answering")
        self.assertEqual(held["cancellation"]["targets"][0]["state"],
                         "ending-in-progress")

    def test_a_completed_job_is_never_fenced_by_a_deadline_that_passes_later(self):
        self.submit()
        self.running(seconds=0)
        self.acts.frozen("job-a/implementation", "completed")
        self.assertEqual(self.projected()["stages"][0]["state"], "completed")
        for seconds in (STAGE_SECONDS, JOB_SECONDS, JOB_SECONDS + 5000):
            report = self.tick(seconds)
            self.assertNotIn("expired", report)
            self.assertNotIn("cancelled", report)
        self.assertEqual(self.operations("job.expire"), 0)
        held = self.projected()
        self.assertEqual(held["stages"][0]["state"], "completed")
        self.assertIsNone(held["cancellation"])
        self.assertIsNone(held["control"]["fence"])
        self.assertTrue(held["control"]["job"]["reached"])
        self.assertEqual(self.acts.cancelled, [])

    def test_the_job_deadline_fences_the_successor_of_a_completed_stage(self):
        self.submit(controlled(stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])]))
        self.running(seconds=0)
        self.acts.frozen("job-a/implementation", "completed")
        self.instants.append(at(JOB_SECONDS))
        report = self.tick(JOB_SECONDS)
        self.assertEqual(report["expired"][0]["trigger"], "job-deadline")
        self.assertEqual(report["acts"], [])
        held = {one["kind"]: one["state"]
                for one in self.projected()["stages"]}
        self.assertEqual(held, {"implementation": "completed",
                                "review": "queued"})
        self.assertEqual(owed_acts(self.jobs, self.acts), [])

    def test_a_stage_that_finished_in_time_does_not_close_its_successor(self):
        """The implementation's 4800 s pass after it completed; the review
        is still admitted until the JOB deadline."""
        self.submit(controlled(stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])]))
        self.running(seconds=0)
        self.acts.frozen("job-a/implementation", "completed")
        self.acts.settled = at(STAGE_SECONDS + 10)
        report = self.tick(STAGE_SECONDS + 10)
        self.assertNotIn("expired", report)
        self.assertEqual([(one["stage_id"], one["act"], one["outcome"])
                          for one in report["acts"]],
                         [("job-a/review", "admit", "performed")])
        held = self.projected()["control"]
        self.assertTrue(held["stages"][0]["reached"])
        self.assertFalse(held["stages"][1]["reached"])
        self.assertIsNone(held["fence"])

    def test_an_explicit_cancel_after_the_expiry_is_recorded_beside_the_fence(self):
        self.submit()
        self.running(seconds=0)
        self.tick(STAGE_SECONDS)
        self.instants.append(at(STAGE_SECONDS + 10))
        request = cancellation.request(self.jobs, job_id="job-a",
                                       reason=REASON)
        self.assertEqual(request["trigger"], "operator")
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["trigger"], "stage-deadline")
        self.assertEqual(cancellation.requests_of(self.jobs)["job-a"], request)
        self.assertEqual(self.projected()["cancellation"]["trigger"],
                         "stage-deadline")
        # AND THE OTHER WAY ROUND: a request before the deadline is the fence
        # and the control pass leaves the Job to the cancellation pass.
        self.setUp()
        self.submit()
        self.running(seconds=0)
        self.instants.append(at(10))
        request = cancellation.request(self.jobs, job_id="job-a",
                                       reason=REASON)
        report = self.tick(STAGE_SECONDS)
        self.assertNotIn("expired", report)
        self.assertEqual(self.operations("job.expire"), 0)
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a"), request)

    def test_the_fence_and_the_elapsed_time_survive_a_restart(self):
        self.submit()
        self.running(seconds=0)
        self.tick(STAGE_SECONDS)
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2",
                                 clock=lambda: at(STAGE_SECONDS + 5))
        self.addCleanup(reopened.close)
        fence = cancellation.fence_of(reopened, "job-a")
        self.assertEqual(fence["trigger"], "stage-deadline")
        self.assertEqual(fence["requested_at"], at(STAGE_SECONDS))
        held = job_control.report(reopened, "job-a",
                                  now=at(STAGE_SECONDS + 5))
        self.assertEqual(held["stages"][0]["elapsed_seconds"],
                         STAGE_SECONDS + 5)
        self.assertEqual(held["fence"]["trigger"], "stage-deadline")
        later = sweep(reopened, self.acts, now=at(STAGE_SECONDS + 5))
        self.assertNotIn("expired", later)
        self.assertEqual(self.operations("job.expire"), 1)


class TheOwnersEvidence(ControlCase):
    """Review 2026-11-19T00-20-37Z: the three boundary reproductions, each
    reproduced here first and then closed. `over` is the owners' evidence of
    cessation, never a label; the earliest reached trigger is the fence
    whatever arrived first; a clock behind the durable origins is uncertain
    before any watermark exists."""

    def test_an_uncertain_runtime_past_the_deadline_is_fenced_and_ordered(self):
        """P1, the reviewer's probe: runtime `uncertain`, cleanup pending,
        exact identity retained, no output. The stage projects `exceptional`
        -- and that is not cessation, so the deadline fences the Job and the
        cancellation pass orders the exact runtime to cease."""
        self.submit()
        held = self.running(seconds=0)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"attempt_id": held["attempt_id"],
                                    "runtime_id": "runtime-1",
                                    "execution_runtime": "uncertain",
                                    "cleanup": "pending", "assignment": None})
        self.assertEqual(self.projected()["stages"][0]["state"], "exceptional")
        report = self.tick(10000)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "fenced",
                           "trigger": "stage-deadline",
                           "stage_id": "job-a/implementation",
                           "deadline_at": at(STAGE_SECONDS)}])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual([one[0] for one in self.acts.cancelled],
                         [held["attempt_id"]])
        self.assertEqual(self.operations("job.expire"), 1)
        held = self.projected()
        self.assertEqual(held["stages"][0]["state"], "exceptional")
        self.assertEqual(held["cancellation"]["trigger"], "stage-deadline")
        self.assertEqual(held["cancellation"]["targets"][0]["state"],
                         "held-unknown")
        self.assertEqual(held["cancellation"]["shutdown"], "unresolved")
        # ONE ORDER: the owner recorded it for this exact runtime.
        self.assertNotIn("cancelled", self.tick(10001))
        self.assertEqual(len(self.acts.cancelled), 1)

    def test_a_failed_start_past_the_deadline_is_fenced_with_nothing_to_stop(self):
        """A start the manager journalled as failed is `exceptional` with no
        runtime attached. The deadline still fences the Job -- no correction
        or replacement is admitted after it -- and the owners are asked for
        nothing, because nothing of it ever ran."""
        self.submit()
        self.acts.fails("job-a/implementation", OSError("no such image"))
        for _ in range(3):
            self.tick(0)
        self.assertEqual(self.projected()["stages"][0]["state"], "exceptional")
        report = self.tick(10000)
        self.assertEqual(report["expired"][0]["outcome"], "fenced")
        self.assertEqual(report["expired"][0]["trigger"], "stage-deadline")
        self.assertNotIn("cancelled", report)
        self.assertEqual(self.acts.cancelled, [])
        self.assertEqual(self.acts.fenced_unstarted, [])
        self.assertEqual(self.projected()["stages"][0]["state"], "exceptional")
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a")["trigger"],
                         "stage-deadline")

    def test_over_is_the_owners_evidence_not_the_projected_label(self):
        """The two halves side by side on real entries: a `completed` stage
        whose axes say ceased is over; an `exceptional` stage over an
        uncertain runtime is not; a queued stage is not."""
        self.submit(controlled(stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])]))
        from baton_v12.job_manager.projection import stage_states

        self.running(seconds=0)
        entries = stage_states(self.jobs, self.acts)
        self.assertFalse(cancellation.over(entries["job-a/implementation"]))
        self.assertFalse(cancellation.over(entries["job-a/review"]))
        self.acts.frozen("job-a/implementation", "completed")
        entries = stage_states(self.jobs, self.acts)
        self.assertEqual(entries["job-a/implementation"]["state"], "completed")
        self.assertTrue(cancellation.over(entries["job-a/implementation"]))
        self.acts.frozen("job-a/implementation", "completed",
                         execution_runtime="running", cleanup=None)
        entries = stage_states(self.jobs, self.acts)
        self.assertFalse(cancellation.over(entries["job-a/implementation"]))

    def test_an_operator_request_after_a_missed_deadline_keeps_the_earlier_trigger(self):
        """P2, the reviewer's probe: no sweep saw the 4800 s deadline; the
        operator cancels at 5000 and a sweep follows. The deadline is the
        earlier trigger, so it is journalled and is the fence; the request
        stands beside it; the bound has already run 200 s."""
        self.submit()
        held = self.running(seconds=0)
        self.instants.append(at(5000))
        request = cancellation.request(self.jobs, job_id="job-a",
                                       reason=REASON)
        self.assertEqual(request["requested_at"], at(5000))
        report = self.tick(5000)
        self.assertEqual(report["expired"],
                         [{"job_id": "job-a", "outcome": "fenced",
                           "trigger": "stage-deadline",
                           "stage_id": "job-a/implementation",
                           "deadline_at": at(STAGE_SECONDS)}])
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual([one[0] for one in self.acts.cancelled],
                         [held["attempt_id"]])
        self.assertIn("stage-deadline reached", self.acts.cancelled[0][1])
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["trigger"], "stage-deadline")
        self.assertEqual(fence["requested_at"], at(STAGE_SECONDS))
        self.assertEqual(cancellation.requests_of(self.jobs)["job-a"], request)
        held = self.projected()["cancellation"]
        self.assertEqual(held["trigger"], "stage-deadline")
        self.assertEqual(held["trigger_at"], at(STAGE_SECONDS))
        self.assertEqual(held["observed_at"], at(5000))
        self.assertEqual(held["elapsed_seconds"], 200)
        self.assertEqual(held["shutdown"], "unresolved")
        self.assertEqual(held["targets"][0]["state"], "ordered")
        # A RESTART DERIVES THE SAME FENCE and journals nothing new.
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2",
                                 clock=lambda: at(5100))
        self.addCleanup(reopened.close)
        later = sweep(reopened, self.acts, now=at(5100))
        self.assertNotIn("expired", later)
        self.assertNotIn("cancelled", later)
        self.assertEqual(cancellation.fence_of(reopened, "job-a"), fence)
        self.assertEqual(self.operations("job.expire"), 1)
        self.assertEqual(self.operations("job.cancel.reason"), 1)

    def test_a_rediscovered_deadline_never_rewords_an_order_already_placed(self):
        """The stop owner's operation is one per attempt and signed over its
        reason. A sweep on a rolled-back clock carried the operator's request
        out first and the stop failed; when the clock catches up the earlier
        deadline becomes the fence, and the retry still uses the wording the
        owner was first given -- journalled once, replayed, no collision."""
        self.submit()
        held = self.running(seconds=0)
        self.instants.append(at(5000))
        cancellation.request(self.jobs, job_id="job-a", reason=REASON)
        self.acts.refusing.append(ContractRefusal(
            "refused", "precondition", "injected transient stop refusal"))
        first = self.tick(4000)
        self.assertNotIn("expired", first)
        self.assertEqual(first["cancelled"][0]["outcome"], "deferred")
        self.assertEqual(self.acts.cancelled, [(held["attempt_id"], REASON)])
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a")["trigger"],
                         "operator")
        second = self.tick(5100)
        self.assertEqual(second["expired"][0]["trigger"], "stage-deadline")
        self.assertEqual(second["cancelled"][0]["outcome"], "ordered")
        self.assertEqual(self.acts.cancelled,
                         [(held["attempt_id"], REASON)] * 2)
        fence = cancellation.fence_of(self.jobs, "job-a")
        self.assertEqual(fence["trigger"], "stage-deadline")
        self.assertEqual(fence["requested_at"], at(STAGE_SECONDS))
        held = self.projected()["cancellation"]
        self.assertEqual(held["trigger"], "stage-deadline")
        self.assertEqual(held["targets"][0]["state"], "ordered")
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)
        self.assertEqual(self.operations("job.cancel.reason"), 1)
        self.assertNotIn("cancelled", self.tick(5101))

    def test_a_rollback_before_the_first_watermark_holds_admission(self):
        """P3, the reviewer's probe: submitted at the origin, first sweep
        100 s before it. The origin is durable evidence the clock is behind,
        so timing is uncertain, elapsed is what the rows prove (0, never
        -100) and nothing is admitted until the clock catches up."""
        self.submit()
        self.assertIsNone(job_control.watermark_in(self.jobs._connection))
        held = self.evaluation(seconds=-100)
        self.assertEqual(held["timing"], "uncertain")
        self.assertEqual(held["job"]["elapsed_seconds"], 0)
        self.assertFalse(held["job"]["reached"])
        report = self.tick(-100)
        self.assertEqual(report["acts"], [])
        self.assertEqual(self.acts.calls, [])
        self.assertEqual([one["outcome"] for one in report["expired"]],
                         ["held"])
        self.assertEqual(self.projected()["control"]["timing"], "uncertain")
        self.assertEqual(self.projected()["stages"][0]["state"], "queued")
        # THE GUARD UNDER THE LOCK SAYS THE SAME before any sweep ran.
        self.setUp()
        self.submit()
        scheduler.activate_pool(self.jobs, scheduling.pool(),
                                scheduling.principals(scheduling.pool()))
        attempt = self.attempting(self.jobs)
        self.instants.append(at(-100))
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.reserve(self.jobs, attempt)
        self.assertIn("uncertain", caught.exception.message)
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])
        # AND A RESTART BEHIND THE ORIGIN, with no watermark to compare to.
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2",
                                 clock=lambda: at(-100))
        self.addCleanup(reopened.close)
        self.assertEqual(job_control.report(reopened, "job-a",
                                            now=at(-100))["timing"],
                         "uncertain")
        # TRUSTED AGAIN AT THE ORIGIN: the first tick at +0 admits.
        report = self.tick(0)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]],
                         [("admit", "performed")])
        self.assertEqual(self.evaluation(seconds=0)["timing"], "trusted")


class TheWriteSideGuards(ControlCase):

    def test_the_reservation_refuses_after_the_deadline_under_the_lock(self):
        scheduler.activate_pool(self.jobs, scheduling.pool(),
                                scheduling.principals(scheduling.pool()))
        self.submit(controlled(stages=[stage("implementation", "work:race")]))
        attempt = self.attempting(self.jobs, "job-a/implementation")
        self.instants.append(at(JOB_SECONDS))
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.reserve(self.jobs, attempt)
        self.assertIn("job-deadline", caught.exception.message)
        self.assertFalse(caught.exception.durable)
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])
        # AND UNDER UNCERTAIN TIMING, by the same guard. A refused act rolls
        # its watermark back with its transaction; the sweep's own stands.
        job_control.observe(self.jobs, at(700))
        self.instants.append(at(5))
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.reserve(self.jobs, attempt)
        self.assertIn("uncertain", caught.exception.message)
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])

    def test_the_claim_re_reads_the_deadline_before_the_authority_is_asked(self):
        self.submit()
        attempt = self.attempting(self.jobs, "job-a/implementation")
        self.instants.append(at(JOB_SECONDS))
        asked = []
        pooled = SimpleNamespace(store=self.jobs,
                                 _allocation=lambda stage: asked.append(stage))
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.PooledManagerOperations.claim(pooled, attempt)
        self.assertIn("job-deadline", caught.exception.message)
        self.assertEqual(asked, [])

    def test_no_replacement_episode_opens_after_the_deadline(self):
        self.submit()
        self.tick(0)
        live = live_of(self.jobs, "job-a/implementation")
        ended = end_episode(self.jobs, live, "abandoned-after-restart", 1)
        report = self.tick(JOB_SECONDS)
        self.assertEqual(report["replaced"], [])
        self.assertIsNone(live_of(self.jobs, "job-a/implementation"))
        with self.assertRaises(ContractRefusal) as caught:
            open_next(self.jobs, "job-a/implementation", ended)
        self.assertIn("expired", caught.exception.message)
        self.assertIsNone(live_of(self.jobs, "job-a/implementation"))

    def correction(self):
        proved = {"verdict_id": "verdict-1", "attachment_id": "attach-1"}
        with mock.patch.object(episodes, "_proved_verdict",
                               return_value=proved), \
                mock.patch.object(episodes, "_corrected_line"), \
                mock.patch.object(episodes, "_unheld"), \
                mock.patch.object(episodes, "_live_episode",
                                  side_effect=lambda store, stage, what:
                                  live_of(store, stage["stage_id"])):
            with self.assertRaises(ContractRefusal) as caught:
                episodes.advance_correction(
                    self.jobs, object(), job_id="job-a", line_id="line-1",
                    checkpoint_id="checkpoint-1", verdict_id="verdict-1")
        self.assertEqual(live_of(self.jobs, "job-a/implementation")["episode"],
                         1)
        self.assertEqual(live_of(self.jobs, "job-a/review")["episode"], 1)
        return caught.exception

    def test_a_correction_round_is_refused_by_the_allowance_in_its_transaction(self):
        self.submit(controlled(stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])]))
        refusal = self.correction()
        self.assertIn("permits 0 correction round(s) and 0 were used",
                      refusal.message)
        self.assertFalse(refusal.durable)
        # The verdict stands: nothing of the Job's rows moved.
        self.assertEqual(self.operations("episode.correct"), 0)
        # AND AFTER THE DEADLINE, BY THE DEADLINE FIRST.
        self.instants.append(at(JOB_SECONDS))
        self.assertIn("job-deadline", self.correction().message)

    def test_rounds_are_counted_as_correction_operations_not_endings(self):
        self.submit(controlled(stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])]))
        self.assertEqual(job_control.rounds_used_in(self.jobs._connection,
                                                    "job-a"), 0)
        # One committed round of ANOTHER Job and one of this Job, each the
        # one `episode.correct` record a round writes.
        for job_id in ("job-z", "job-a"):
            self.jobs.transact(
                episodes.correction_operation_id(job_id, "cp-1"),
                episodes.CORRECT_KIND,
                __import__("baton_v12.job_manager.store",
                           fromlist=["job_signature"]).job_signature(
                    episodes.CORRECT_KIND, {"job_id": job_id}),
                lambda connection, job_id=job_id: {"job_id": job_id})
        self.assertEqual(job_control.rounds_used_in(self.jobs._connection,
                                                    "job-a"), 1)
        self.assertEqual(self.projected()["control"]["corrections"],
                         {"allowance": 0, "used": 1})


class NoSuccessorThroughAFreshAttempt(fresh.FreshAttemptCase):

    def controlled_prior(self):
        """The failed prior Job, admitted under the profile."""
        held = self.prior()
        self.jobs.transact(
            job_control.control_operation_id(fresh.PRIOR), "job.control",
            __import__("baton_v12.job_manager.store",
                       fromlist=["job_signature"]).job_signature(
                "job.control", {"job_id": fresh.PRIOR}),
            lambda connection: documents.job_control_record(
                operation_id=job_control.control_operation_id(fresh.PRIOR),
                job_id=fresh.PRIOR, profile=PROFILE,
                resolved=job_control.resolved(PROFILE), admitted_at=NOW,
                incarnation="jobs-1"))
        return held

    def test_an_expired_prior_job_cannot_be_retried(self):
        self.controlled_prior()
        job_control.expire(self.jobs, job_id=fresh.PRIOR,
                           trigger="job-deadline", stage_id=None,
                           deadline_at=at(JOB_SECONDS),
                           observed_at=at(JOB_SECONDS))
        refusal = self.refused()
        self.assertIn("expired", refusal.message)
        self.assertIsNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))

    def test_a_prior_job_that_failed_before_its_deadline_may_be_retried_after_it(self):
        self.controlled_prior()
        self.instants.append(at(JOB_SECONDS + 100))
        admitted = self.admitted()
        self.assertIsNotNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))
        # THE FRESH JOB CARRIES ITS OWN CONTROL AND ITS OWN ORIGINS when the
        # prior document did; this prior's document stated none.
        self.assertIsNone(job_control.control_of(self.jobs, admitted["job_id"]))

    def test_uncertain_timing_holds_the_fresh_attempt(self):
        self.controlled_prior()
        job_control.observe(self.jobs, at(500))
        self.instants.append(at(100))
        refusal = self.refused()
        self.assertIn("uncertain", refusal.message)
        self.assertIsNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))


if __name__ == "__main__":
    unittest.main()


class TheTemplatePath(unittest.TestCase):
    """The selection travels visibly: request, resolution, /3 submission."""

    def test_a_request_may_select_a_profile_and_the_resolution_records_it(self):
        from baton_v12.job_manager import templates
        from tests.job_manager import test_templates as t

        held = templates.resolve(t.request(control={"profile": PROFILE}),
                                 configuration=t.configuration())
        self.assertEqual(held["control"], {"profile": PROFILE,
                                           "resolved": job_control.resolved(PROFILE)})
        self.assertEqual(held["submission"]["schema"],
                         documents.SUBMISSION_CONTROL_SCHEMA)
        self.assertEqual(held["submission"]["jobs"][0]["control"],
                         {"profile": PROFILE})
        # ROUND TRIP: the resolution is still spendable, as its own request.
        spent = templates.submission_for_admission(held)
        self.assertEqual(spent, held["submission"])
        # AN EDITED SELECTION IS NOT SPENDABLE.
        edited = json.loads(json.dumps(held))
        del edited["control"]
        with self.assertRaises(ContractRefusal):
            templates.submission_for_admission(edited)
        # AND NO SELECTION IS EXACTLY THE DOCUMENT IT ALWAYS WAS.
        plain = templates.resolve(t.request(), configuration=t.configuration())
        self.assertNotIn("control", plain)
        self.assertEqual(plain["submission"]["schema"],
                         documents.SUBMISSION_SCHEMAS[0])
        with self.assertRaises(ContractRefusal):
            templates.resolve(t.request(control={"profile": "documentation/9"}),
                              configuration=t.configuration())
        with self.assertRaises(ContractRefusal):
            templates.resolve(t.request(control=None),
                              configuration=t.configuration())


class TheCreationPath(unittest.TestCase):

    def test_an_installed_creation_admits_the_job_under_the_profile(self):
        from tests.job_manager import test_creation as c

        case = c.CreationCase("setUp")
        case.setUp()
        try:
            held = case.created(request=c.request(control={"profile": PROFILE}))
            self.assertEqual(held["control"]["profile"], PROFILE)
            recorded = job_control.control_of(case.jobs, held["job_id"])
            self.assertEqual(recorded["profile"], PROFILE)
            self.assertEqual(recorded["admitted_at"], held["recorded_at"])
            # THE SAME REQUEST REPLAYS; another selection is another intent.
            self.assertEqual(case.created(request=c.request(
                control={"profile": PROFILE})), held)
            with self.assertRaises(ContractRefusal):
                case.created(request=c.request())
            plain = case.created(request=c.request(task={
                "task_id": "another-task", "statement": "another statement"}))
            self.assertNotIn("control", plain)
            self.assertIsNone(job_control.control_of(case.jobs, plain["job_id"]))
        finally:
            case.doCleanups()

    def test_the_cli_states_the_profile_on_the_request(self):
        from types import SimpleNamespace

        from tools import job_manager as cli

        taken = SimpleNamespace(
            task="task-1", statement="do it", source="installed",
            work_scope=["v12/python/src"], test_scope=[], acceptance=["ok"],
            template=None, job_id=None, submission_id=None,
            provider_turn_seconds=None, verification_command_seconds=None,
            control_profile=PROFILE)
        self.assertEqual(cli._creation_request(taken)["control"],
                         {"profile": PROFILE})
        taken.control_profile = None
        self.assertNotIn("control", cli._creation_request(taken))


class TheHeavyNativeProfile(ControlCase):
    """The separately approved profile uses existing admission and fences."""

    def heavy(self):
        return controlled(profile="native-handoff-heavy/1", limits={"provider_turn_seconds": 7200})

    def test_exact_selection_and_old_profile_bytes_remain_unchanged(self):
        expected = {"correction_rounds": 0, "stage_seconds": 4800, "job_seconds": 9960,
                    "provider_turn_seconds": 3600, "verification_command_seconds": 900}
        for profile in ("documentation/1", "native-handoff/1"):
            self.assertEqual(job_control.resolved(profile), dict(expected, profile=profile, units="seconds"))
        self.assertEqual(job_control.resolved("native-handoff-heavy/1"), dict(expected,
            profile="native-handoff-heavy/1", units="seconds", stage_seconds=9000,
            job_seconds=21600, provider_turn_seconds=7200))
        self.assertEqual(job_control.continuation_allowance("native-handoff-heavy/1"), 1)
        self.assertEqual(job_control.continuation_allowance("native-handoff/1"), 1)
        self.assertEqual(job_control.continuation_allowance("documentation/1"), 0)

    def test_missing_or_mismatched_override_refuses_before_admission(self):
        for limits in (None, {"provider_turn_seconds": 3600},
                       {"provider_turn_seconds": 7200, "verification_command_seconds": 901}):
            with self.subTest(limits=limits), self.assertRaises(ContractRefusal):
                self.submit(controlled(profile="native-handoff-heavy/1", limits=limits))
        self.assertEqual(self.operations("job.control"), 0)
        with self.assertRaises(ContractRefusal):
            self.submit(controlled(profile="native-handoff/1", limits={"provider_turn_seconds": 7200}))
        self.submit(self.heavy())

    def test_replay_restart_and_old_admission_keep_their_own_clocks(self):
        self.submit(controlled(job_id="old", profile="native-handoff/1", submission_id="old-sub"))
        old = job_control.control_of(self.jobs, "old")
        self.instants.append(at(100))
        first = self.submit(self.heavy())
        self.instants.append(at(200))
        self.assertEqual(self.submit(self.heavy()), first)
        reopened = JobStore.open(self.job_path, authority_uuid=UUID, incarnation="heavy-restart", clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(job_control.control_of(reopened, "old"), old)
        self.assertEqual(job_control.evaluate(reopened._connection, "job-a", at(300))["job"]["deadline_at"], at(21700))
        self.assertEqual(job_control.evaluate(reopened._connection, "old", at(300))["job"]["deadline_at"], at(9960))
        with self.assertRaises(ContractRefusal):
            self.submit(controlled(profile="native-handoff/1"))
        with self.assertRaises(ContractRefusal):
            job_control.refuse_round(reopened._connection, "job-a")

    def test_queued_heavy_job_expires_without_admitting_work(self):
        self.submit(self.heavy())
        report = self.tick(21600)
        self.assertEqual(report["expired"][0]["trigger"], "job-deadline")
        self.assertEqual(report["acts"], [])
        self.assertEqual(self.acts.calls, [])

    def test_stage_expiry_uses_owner_origin_and_unchanged_shutdown(self):
        self.submit(self.heavy())
        self.acts.settled = at(100)
        self.running(seconds=500)
        self.assertEqual(self.evaluation(seconds=500)["stages"][0]["deadline_at"], at(9100))
        report = self.tick(9100)
        self.assertEqual(report["expired"][0]["trigger"], "stage-deadline")
        self.assertEqual(len(self.acts.cancelled), 1)
        self.assertEqual(self.projected(seconds=9130)["cancellation"]["shutdown"], "within-bound")
        self.assertEqual(self.projected(seconds=9221)["cancellation"]["shutdown"], "unresolved")

    def test_real_creation_delivers_heavy_limits_to_both_worker_roles(self):
        from tests.job_manager import test_creation as c
        from tests.tools import test_execution_limits as worker
        from tools import single_worker
        from baton_v12.worker_manager import launch

        case = c.CreationCase("setUp")
        case.setUp()
        self.addCleanup(case.doCleanups)
        request = c.request(control={"profile": "native-handoff-heavy/1"},
                            overrides={"execution_limits": {"provider_turn_seconds": 7200}})
        created = case.created(request=request)
        self.assertEqual(case.created(request=request), created)
        self.assertEqual(created["control"]["resolved"]["job_seconds"], 21600)
        given = {"input_manifest": {"manifest_digest": "sha256:" + "3" * 64},
                 "policy_digest": "sha256:" + "2" * 64}
        reader = SimpleNamespace(execution_context=single_worker.job_execution_reader(case.jobs),
                                 given=given, _given_for=lambda stage: given)
        adapter = worker.TheAdapterHandsTheCommandWhatWasConfigured()
        for role in ("implementation", "review"):
            with self.subTest(role=role):
                context = single_worker._SingleWorker._job_execution(reader,
                    {"job_id": created["job_id"], "attempt_id": "attempt-" + role})
                limits = context["execution_limits"]["boundaries"]
                self.assertEqual([limits[x]["seconds"] for x in
                    ("provider_turn", "ordinary_verification", "integration_verification", "host_verification")],
                    [7200, 900, 1800, 300])
                delivery = launch.launch_document(session="heavy-" + role, contract="heavy-task",
                                                  role=role, transport=None, job_execution=context)
                seen = worker.baton_worker.launched(delivery, place="/run/baton/launch.json")
                agent, captured = adapter.production(seen)
                agent._provider({"verification": ["fake-verification"]}, "/unused", "/unused", {}, prompt="fixed fake prompt")
                agent._verify({"verification": ["fake-verification"]}, "/unused", {}, ())
                self.assertEqual(captured, [7200, 900])

    def test_heavy_profile_preserves_one_real_resolved_continuation(self):
        from tests.job_manager import test_native_handoffs as handoffs

        for method in ("test_ONE_continuation_and_the_second_is_refused",
                       "test_a_continuation_spends_NO_CORRECTION_ROUND",
                       "test_the_original_deadlines_are_PRESERVED_by_a_continuation"):
            with self.subTest(method=method):
                case = handoffs.TheContinuationIsTheSameAdmittedTask(method)
                original = case.submission
                def heavy_submission():
                    held = original(profile="native-handoff-heavy/1")
                    held["jobs"][0]["execution_limits"] = {"provider_turn_seconds": 7200}
                    return held
                case.submission = heavy_submission
                try:
                    case.setUp()
                    if method == "test_the_original_deadlines_are_PRESERVED_by_a_continuation":
                        before = job_control.evaluate(case.jobs._connection, "job-a", handoffs.NOW)
                        case.resumed()
                        after = job_control.evaluate(case.jobs._connection, "job-a", handoffs.NOW)
                        self.assertEqual(after["profile"], "native-handoff-heavy/1")
                        self.assertEqual(after["job"], before["job"])
                        self.assertEqual(after["continuations"], {"allowance": 1, "used": 1})
                    else:
                        getattr(case, method)()
                finally:
                    case.doCleanups()
