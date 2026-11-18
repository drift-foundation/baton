"""W383215 — explicit Job cancellation: the request, the fence, the pass.

DESIGN LIM-5. A cancellation is ONE journalled request per Job, committed
before any effect, and a FENCE every admission owner of the Job store reads
inside its own write transaction. The serving sweep carries it out through
the existing owners and reports what it ordered; cessation stays the owners'
own fact. These cases drive the Job store half against real disposable stores
and `test_status`'s strict fake operations, extended with recording stand-ins
for the two owner capabilities the pass reaches.
"""

import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, STATUS_SCHEMA, cancellation,
                                   episodes, fresh_attempt, scheduler,
                                   status, submit, sweep)
from baton_v12.job_manager.episodes import end_episode, live_of, open_next
from baton_v12.job_manager.projection import owed_acts, stage_states

from tests.job_manager import test_fresh_attempt as fresh
from tests.job_manager import test_scheduling as scheduling

if __package__:
    from .fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase,
                           job, stage, submission)
else:
    from fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase,
                          job, stage, submission)

REASON = "operator stops this Job before its deadline"
SOON = "2026-09-02T00:00:30.000Z"            # NOW + 30 s
MUCH_LATER = "2026-09-02T00:02:01.000Z"      # NOW + 121 s
EARLIER = "2026-09-01T23:59:00.000Z"


class Cancelling(FakeOperations):
    """The strict fake, plus the two capabilities the cancellation pass asks.

    Each records what it was asked and answers the shape the real owners
    answer: an intent naming the Authority operation and the fence the
    Authority returned. Neither claims cessation, exactly as the real ones.
    """

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.cancelled = []
        self.fenced_unstarted = []
        # Refusals the next calls raise, consumed one per call: a transient
        # engine failure is one entry, a persistent one is many.
        self.refusing = []

    def stage_of(self, attempt_id):
        for stage_id, held in self.observations.items():
            runtime = held.get("runtime")
            if runtime is not None and runtime["attempt_id"] == attempt_id:
                return stage_id
        raise AssertionError(attempt_id)

    def cessation(self, attempt_id, outcome, runtime_id=None):
        """What the real owner journals: the cancellation component's
        outcome for the runtime that is attached, which `observe` reads."""
        stage_id = self.stage_of(attempt_id)
        held = self.observations[stage_id]
        held["cessation"] = {
            "outcome": outcome, "effects": ["agent-cancel", "stop"]
            if outcome == "ordered" else ["agent-cancel"],
            "runtime_id": (held["runtime"]["runtime_id"] if runtime_id is None
                           else runtime_id)}

    def cancel_attempt(self, *, attempt_id, reason):
        self.cancelled.append((attempt_id, reason))
        if self.refusing:
            # The real owner records `stop-failed` before it re-raises.
            self.cessation(attempt_id, "stop-failed")
            raise self.refusing.pop(0)
        self.cessation(attempt_id, "ordered")
        return {"intent": {"attempt_id": attempt_id,
                           "authority_operation_id": "authority.attempt.cancel:x",
                           "assignment": {"generation": 1}, "reason": reason},
                "fenced": {"cause": "cancelled", "phase": "block",
                           "gate": "runtime-quiescence:1", "fenced": True,
                           "assignment": {"generation": 1}},
                "session_quiescence": None,
                "quiescence": {"ordered": True, "runtime_id": "runtime-1",
                               "agent_settlement": None,
                               "runtime_settlement": None}}

    def fence_unstarted_attempt(self, stage, *, reason):
        if self.refusing:
            raise self.refusing.pop(0)
        self.fenced_unstarted.append((stage["attempt_id"], reason))
        return {"intent": {"authority_operation_id": "authority.attempt.abandon:x",
                           "assignment": {"generation": 1}, "reason": reason},
                "fenced": {"cause": "cancelled", "phase": "block",
                           "gate": None, "fenced": True}}


class CancellationCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = Cancelling()

    def submit(self, document=None):
        return submit(self.jobs, document if document is not None
                      else submission(jobs=[job("job-a", stages=[
                          stage("implementation")])]))

    def cancel(self, job_id="job-a", reason=REASON):
        return cancellation.request(self.jobs, job_id=job_id, reason=reason)

    def projected(self, job_id="job-a", at=LATER):
        document = status(self.jobs, self.acts, observed_at=at)
        self.assertEqual(document["schema"], STATUS_SCHEMA)
        for entry in document["jobs"]:
            if entry["job_id"] == job_id:
                return entry
        raise AssertionError(job_id)

    def target(self, stage_id="job-a/implementation", **named):
        report = self.projected(**named)["cancellation"]
        self.assertIsNotNone(report)
        for one in report["targets"]:
            if one["stage_id"] == stage_id:
                return report, one
        raise AssertionError(stage_id)

    def running(self, stage_id="job-a/implementation"):
        """Admit, claim and start one stage through ordinary ticks."""
        self.acts.starts(stage_id, attaches=True)
        for _ in range(4):
            sweep(self.jobs, self.acts, now=NOW)
        held = self.projected()["stages"][0]
        self.assertIn(held["state"], ("starting", "waiting", "running"), held)
        return held


class TheRequest(CancellationCase):

    def test_one_request_is_journalled_once_and_replays_exactly(self):
        self.submit()
        first = self.cancel()
        self.assertEqual(first["job_id"], "job-a")
        self.assertEqual(first["reason"], REASON)
        self.assertEqual(first["requested_at"], NOW)
        self.assertEqual(first["observed"],
                         [{"stage_id": "job-a/implementation",
                           "kind": "implementation", "episode": 1,
                           "attempt_id": first["observed"][0]["attempt_id"],
                           "episodes": 1}])
        self.instants.append(LATER)
        self.assertEqual(self.cancel(), first)
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a"), first)

    def test_a_changed_reason_collides_rather_than_rewriting(self):
        self.submit()
        first = self.cancel()
        with self.assertRaises(ContractRefusal) as caught:
            self.cancel(reason="another account entirely")
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual(cancellation.fence_of(self.jobs, "job-a"), first)

    def test_an_unknown_job_and_a_blank_reason_refuse_without_a_fence(self):
        self.submit()
        with self.assertRaises(ContractRefusal):
            self.cancel(job_id="job-nobody")
        with self.assertRaises(ContractRefusal):
            self.cancel(reason="   ")
        self.assertIsNone(cancellation.fence_of(self.jobs, "job-a"))
        self.assertIsNone(cancellation.fence_of(self.jobs, "job-nobody"))

    def test_the_fence_survives_a_restart_of_the_manager(self):
        self.submit()
        first = self.cancel()
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2", clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(cancellation.fence_of(reopened, "job-a"), first)
        self.assertEqual(owed_acts(reopened, self.acts), [])
        self.assertEqual(cancellation.request(reopened, job_id="job-a",
                                              reason=REASON), first)

    def test_a_job_nobody_cancelled_reports_null(self):
        self.submit()
        self.assertIsNone(self.projected()["cancellation"])


class QueuedAndOfferedTargets(CancellationCase):

    def test_a_queued_stage_is_retired_before_admission(self):
        self.submit()
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(report["acts"], [])
        self.assertNotIn("cancelled", report)
        self.assertEqual([one for one in self.acts.calls
                          if one[0] in ("admit", "claim")], [])
        report, target = self.target()
        self.assertEqual(target["state"], "retired-before-admission")
        self.assertEqual(report["shutdown"], "complete")
        self.assertEqual(report["trigger_at"], NOW)
        self.assertEqual(report["shutdown_bound_seconds"], 120)
        # The stage keeps its ordinary vocabulary: no new state was invented.
        self.assertEqual(self.projected()["stages"][0]["state"], "queued")

    def test_an_offered_stage_is_never_claimed_and_waits_for_the_lapse(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.cancel()
        for _ in range(3):
            sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one for one in self.acts.calls if one[0] == "claim"],
                         [])
        report, target = self.target(at=SOON)
        self.assertEqual(target["state"], "awaiting-offer-lapse")
        self.assertEqual(report["shutdown"], "within-bound")
        self.assertEqual(report["elapsed_seconds"], 30)
        report, _ = self.target()
        self.assertEqual(report["shutdown"], "unresolved")
        self.assertEqual(report["elapsed_seconds"], 300)

    def test_the_bound_runs_from_the_request_and_never_resets(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.cancel()
        report, _ = self.target(at=MUCH_LATER)
        self.assertEqual(report["shutdown"], "unresolved")
        self.assertEqual(report["elapsed_seconds"], 121)
        # A replayed request, a restart and more ticks move nothing.
        self.instants.append(MUCH_LATER)
        self.cancel()
        sweep(self.jobs, self.acts, now=MUCH_LATER)
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-2", clock=self.clock)
        self.addCleanup(reopened.close)
        entry = [one for one in status(reopened, self.acts,
                                       observed_at=MUCH_LATER)["jobs"]][0]
        self.assertEqual(entry["cancellation"]["requested_at"], NOW)
        self.assertEqual(entry["cancellation"]["shutdown"], "unresolved")
        # And an instant this reader cannot order after the request is
        # reported as unknown time, not as time that has not passed.
        report, _ = self.target(at=EARLIER)
        self.assertEqual(report["shutdown"], "unknown-time")
        self.assertIsNone(report["elapsed_seconds"])


class ClaimedAndRunningTargets(CancellationCase):

    def test_a_claimed_stage_is_fenced_instead_of_launched(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(self.projected()["stages"][0]["state"], "claimed")
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one["outcome"] for one in report["started"]],
                         ["deferred"])
        self.assertEqual(self.acts.fenced_unstarted,
                         [(report["cancelled"][0]["attempt_id"], REASON)])
        self.assertEqual(report["cancelled"][0]["effect"], "fence-unstarted")
        self.assertEqual(report["cancelled"][0]["outcome"], "ordered")
        self.assertEqual(self.acts.cancelled, [])
        _, target = self.target()
        self.assertEqual(target["state"], "fenced-unstarted")
        self.assertEqual([one["effect"] for one in target["orders"]],
                         ["fence-unstarted"])

    def test_a_running_stage_is_ordered_to_cease_and_reported_ordered(self):
        self.submit()
        held = self.running()
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(self.acts.cancelled, [(held["attempt_id"], REASON)])
        self.assertEqual(report["cancelled"][0]["effect"], "order-cessation")
        report, target = self.target(at=SOON)
        self.assertEqual(target["state"], "ordered")
        self.assertEqual(report["shutdown"], "within-bound")
        # ORDERED IS NOT CEASED: the owner's own axes say when it is over.
        self.acts.frozen("job-a/implementation", "cancelled",
                         execution_runtime="destroyed", cleanup="complete")
        report, target = self.target()
        self.assertEqual(target["state"], "ceased")
        self.assertEqual(report["shutdown"], "complete")

    def test_the_order_is_decided_by_the_owners_record_not_the_axis(self):
        self.submit()
        held = self.running()
        self.cancel()
        sweep(self.jobs, self.acts, now=LATER)
        sweep(self.jobs, self.acts, now=LATER)
        sweep(self.jobs, self.acts, now=LATER)
        # The owner recorded `ordered` for the attached runtime, so it is
        # not asked again, and this store holds ONE order.
        self.assertEqual(len(self.acts.cancelled), 1)
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)
        _, target = self.target()
        self.assertEqual(target["state"], "ordered")
        self.assertEqual(target["cessation"]["outcome"], "ordered")
        # THE AXIS ALONE IS NOT AN ORDER. The owner moves the axis to
        # `cancel-requested` BEFORE it asks the engine; with the owner's
        # record saying the stop failed, the axis does not suppress a retry.
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"attempt_id": held["attempt_id"],
                                    "runtime_id": "runtime-1",
                                    "execution_runtime": "cancel-requested",
                                    "cleanup": "pending", "assignment": None})
        self.acts.cessation(held["attempt_id"], "stop-failed")
        _, target = self.target()
        self.assertEqual(target["state"], "order-failed")
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.cancelled), 2)
        _, target = self.target()
        self.assertEqual(target["state"], "ordered")
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)

    def test_a_transient_stop_refusal_is_retried_on_the_next_tick(self):
        """Review 2026-11-18T19-56-12Z P1: one failed stop, removed
        thereafter, must not leave the runtime un-ordered forever."""
        self.submit()
        held = self.running()
        self.cancel()
        self.acts.refusing.append(ContractRefusal(
            "refused", "precondition", "injected transient stop refusal"))
        first = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(first["cancelled"][0]["outcome"], "deferred")
        self.assertEqual(cancellation.targets_of(self.jobs, "job-a"), [])
        _, target = self.target()
        self.assertEqual(target["state"], "order-failed")
        self.assertEqual(target["orders"], [])
        second = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(second["cancelled"][0]["outcome"], "ordered")
        self.assertEqual([one[0] for one in self.acts.cancelled],
                         [held["attempt_id"]] * 2)
        self.assertEqual(len(cancellation.targets_of(self.jobs, "job-a")), 1)
        _, target = self.target()
        self.assertEqual(target["state"], "ordered")
        third = sweep(self.jobs, self.acts, now=LATER)
        self.assertNotIn("cancelled", third)

    def test_an_order_for_another_runtime_identity_does_not_cover_this_one(self):
        self.submit()
        held = self.running()
        self.cancel()
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.cancelled), 1)
        # A later generation attached under another identity: the recorded
        # outcome names the old runtime and this one is ordered afresh.
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"attempt_id": held["attempt_id"],
                                    "runtime_id": "runtime-2",
                                    "execution_runtime": "running",
                                    "cleanup": "pending", "assignment": None})
        self.acts.cessation(held["attempt_id"], "ordered",
                            runtime_id="runtime-1")
        _, target = self.target()
        self.assertEqual(target["state"], "pending")
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.cancelled), 2)

    def test_an_in_flight_start_is_ordered_not_fenced(self):
        """Review 2026-11-18T20-12-59Z P1: `start-requested` with nothing
        attached is a start whose reply may be lost, which the stop owner
        resolves through the token; only `not-started` is never-started."""
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)
        attempt = self.attempting(self.jobs, "job-a/implementation")
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"attempt_id": attempt["attempt_id"],
                                    "runtime_id": None,
                                    "execution_runtime": "start-requested",
                                    "cleanup": "pending", "assignment": None})
        self.cancel()
        _, target = self.target()
        self.assertEqual(target["state"], "pending")
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([(one["effect"], one["outcome"])
                          for one in report["cancelled"]],
                         [("order-cessation", "ordered")])
        self.assertEqual(self.acts.fenced_unstarted, [])
        # The fake owner, like the real one, names the token-bound identity.
        self.acts.observations["job-a/implementation"]["cessation"][
            "runtime_id"] = "runtime-bound-1"
        _, target = self.target()
        self.assertEqual(target["state"], "ordered")
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.cancelled), 1)
        # A late attachment of that same identity still replays.
        self.acts.observations["job-a/implementation"]["runtime"][
            "runtime_id"] = "runtime-bound-1"
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.cancelled), 1)
        _, target = self.target()
        self.assertEqual(target["state"], "ordered")
        # Whereas a positively never-started attempt is fenced, not stopped.
        self.acts.observations["job-a/implementation"]["runtime"] = {
            "attempt_id": attempt["attempt_id"], "runtime_id": None,
            "execution_runtime": "not-started", "cleanup": "pending",
            "assignment": None}
        self.acts.observations["job-a/implementation"]["cessation"] = None
        sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(len(self.acts.fenced_unstarted), 1)

    def test_an_answered_attempt_is_left_to_its_ending_owners(self):
        self.submit()
        self.running()
        self.acts.frozen("job-a/implementation", "completed",
                         execution_runtime="running", cleanup="pending")
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertNotIn("cancelled", report)
        self.assertEqual(self.acts.cancelled, [])
        _, target = self.target()
        self.assertEqual(target["state"], "ending-in-progress")

    def test_a_terminal_label_does_not_suppress_a_live_unanswered_runtime(self):
        self.submit()
        held = self.running()
        # A durable refusal makes the stage `exceptional` while the runtime
        # the manager attached is still running and nothing answered.
        self.acts.refusals[("job-a/implementation", "claim")] = ContractRefusal(
            "refused", "precondition", "already exceptional", durable=True)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"attempt_id": held["attempt_id"],
                                    "runtime_id": "runtime-1",
                                    "execution_runtime": "running",
                                    "cleanup": "pending", "assignment": None})
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual([one["outcome"] for one in report.get("cancelled", [])],
                         ["ordered"])
        self.assertEqual(len(self.acts.cancelled), 1)

    def test_an_owner_refusal_is_contained_reported_and_leaves_pending(self):
        self.submit()
        self.running()
        self.cancel()
        self.acts.refusing.append(ContractRefusal(
            "refused", "precondition", "the session is for somebody else"))
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(report["cancelled"][0]["outcome"], "deferred")
        self.assertEqual(report["cancelled"][0]["detail"]["code"],
                         "precondition")
        self.assertEqual(cancellation.targets_of(self.jobs, "job-a"), [])
        # The owner recorded that its stop did not cross; the report says so
        # and the next tick asks again rather than treating it as ordered.
        _, target = self.target()
        self.assertEqual(target["state"], "order-failed")

    def test_a_deployment_without_the_capability_is_reported_not_guessed(self):
        self.submit()
        plain = FakeOperations()
        self.acts = plain
        self.running()
        self.cancel()
        report = sweep(self.jobs, plain, now=LATER)
        self.assertEqual(report["cancelled"][0]["outcome"], "refused")
        self.assertEqual(report["cancelled"][0]["detail"]["code"],
                         "capability")

    def test_an_ended_job_keeps_its_outcome_and_nothing_is_ordered(self):
        self.submit()
        self.running()
        self.acts.frozen("job-a/implementation", "completed")
        for _ in range(3):
            sweep(self.jobs, self.acts, now=NOW)
        before = self.projected()
        self.assertEqual(before["stages"][0]["state"], "completed")
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertNotIn("cancelled", report)
        self.assertEqual(self.acts.cancelled, [])
        after = self.projected()
        self.assertEqual(after["stages"][0], before["stages"][0])
        report, target = self.target()
        self.assertEqual(target["state"], "ended-before-request")
        self.assertEqual(report["shutdown"], "complete")


class TheWriteSideFences(CancellationCase):

    def test_no_replacement_episode_opens_for_a_cancelled_job(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        live = live_of(self.jobs, "job-a/implementation")
        ended = end_episode(self.jobs, live, "abandoned-after-restart", 1)
        self.cancel()
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(report["replaced"], [])
        self.assertIsNone(live_of(self.jobs, "job-a/implementation"))
        with self.assertRaises(ContractRefusal) as caught:
            open_next(self.jobs, "job-a/implementation", ended)
        self.assertIn("cancelled", caught.exception.message)
        self.assertFalse(caught.exception.durable)
        self.assertIsNone(live_of(self.jobs, "job-a/implementation"))
        _, target = self.target()
        self.assertEqual(target["state"], "ceased")

    def test_the_reservation_refuses_under_the_lock(self):
        scheduler.activate_pool(self.jobs, scheduling.pool(),
                                scheduling.principals(scheduling.pool()))
        self.submit(submission(jobs=[
            job("job-a", stages=[stage("implementation", "work:race")])]))
        attempt = self.attempting(self.jobs, "job-a/implementation")
        self.cancel()
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.reserve(self.jobs, attempt)
        self.assertIn("cancelled", caught.exception.message)
        self.assertEqual(scheduler.allocation_rows(self.jobs), [])

    def test_the_claim_re_reads_the_fence_before_the_authority_is_asked(self):
        self.submit()
        attempt = self.attempting(self.jobs, "job-a/implementation")
        self.cancel()
        asked = []
        pooled = SimpleNamespace(store=self.jobs,
                                 _allocation=lambda stage: asked.append(stage))
        with self.assertRaises(ContractRefusal):
            scheduler.PooledManagerOperations.claim(pooled, attempt)
        self.assertEqual(asked, [])

    def test_a_cancel_racing_a_reservation_leaves_a_consistent_store(self):
        """Whichever commits first, the other sees it: never both admitted
        and unfenced, and a reservation that won is found by the pass."""
        scheduler.activate_pool(self.jobs, scheduling.pool(),
                                scheduling.principals(scheduling.pool()))
        self.submit(submission(jobs=[
            job("job-a", stages=[stage("implementation", "work:race")])]))
        barrier = threading.Barrier(2)
        outcomes = {}

        def reserving():
            store = JobStore.open(self.job_path, authority_uuid=UUID,
                                  incarnation="jobs-r", clock=self.clock)
            try:
                local = self.attempting(store, "job-a/implementation")
                barrier.wait()
                try:
                    scheduler.reserve(store, local)
                    outcomes["reserve"] = "reserved"
                except ContractRefusal:
                    outcomes["reserve"] = "refused"
            finally:
                store.close()

        def cancelling():
            store = JobStore.open(self.job_path, authority_uuid=UUID,
                                  incarnation="jobs-c", clock=self.clock)
            try:
                barrier.wait()
                cancellation.request(store, job_id="job-a", reason=REASON)
                outcomes["cancel"] = "fenced"
            finally:
                store.close()

        threads = [threading.Thread(target=reserving),
                   threading.Thread(target=cancelling)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(outcomes["cancel"], "fenced")
        allocated = scheduler.allocation_rows(self.jobs)
        if outcomes["reserve"] == "refused":
            self.assertEqual(allocated, [])
        else:
            self.assertEqual(len(allocated), 1)
        # Either way the Job owes nothing further and projects its fence.
        self.assertEqual(owed_acts(self.jobs, self.acts), [])
        self.assertIsNotNone(self.projected()["cancellation"])

    def test_a_correction_round_refuses_inside_its_transaction(self):
        self.submit(submission(jobs=[job("job-a", stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])])]))
        self.cancel()
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
        self.assertIn("cancelled", caught.exception.message)
        self.assertEqual(live_of(self.jobs, "job-a/implementation")["episode"],
                         1)
        self.assertEqual(live_of(self.jobs, "job-a/review")["episode"], 1)


class NoSuccessorThroughAFreshAttempt(fresh.FreshAttemptCase):
    """Review 5: a cancelled worker attempt projects `exceptional`, which is
    exactly the state a fresh attempt repeats. The fence must close it."""

    def test_a_cancelled_failed_job_cannot_be_retried(self):
        self.prior()
        cancellation.request(self.jobs, job_id=fresh.PRIOR, reason=REASON)
        refusal = self.refused()
        self.assertIn("cancelled", refusal.message)
        self.assertIsNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))
        self.assertEqual(fresh.successors_of(self.jobs, fresh.PRIOR), [])

    def test_a_cancel_landing_after_the_preflight_still_refuses_under_the_lock(self):
        self.prior()
        original = fresh_attempt._prior

        def then_cancel(store, prior_job_id):
            held = original(store, prior_job_id)
            cancellation.request(self.jobs, job_id=prior_job_id,
                                 reason=REASON)
            return held

        with mock.patch.object(fresh_attempt, "_prior", then_cancel):
            refusal = self.refused()
        self.assertIn("cancelled", refusal.message)
        self.assertIsNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))
        self.assertEqual(self.authorization.created, [])

    def test_a_fresh_attempt_admitted_before_the_request_is_left_intact(self):
        self.prior()
        first = self.admitted()
        cancellation.request(self.jobs, job_id=fresh.PRIOR, reason=REASON)
        self.assertEqual(self.admitted(), first)
        self.assertIsNotNone(fresh.fresh_attempt_of(self.jobs, fresh.FRESH))


if __name__ == "__main__":
    unittest.main()
