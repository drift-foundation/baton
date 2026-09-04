"""W76207 — the post-claim launch seam, and the start failure it can report.

TWO GAPS, ONE FILE. W71875's control plane stopped at the claim: nothing drove
a claimed stage into a live worker, and nothing could see that a start had
failed. The first left `job_manager.py serve` with no production path from an
accepted claim to a runtime; the second let the projection report a stage as
`running` on the strength of a runtime id that failed-start reconciliation had
attached AFTER the manager recorded the failure.

WHY THE LAUNCH IS NOT INSIDE `claim()`. A crash after the Authority commits the
claim leaves the next incarnation ADOPTING the canonical `offer.settle` receipt
without calling `claim` again -- so a launch folded into that call is skipped
once, permanently, on the one path nobody watches. The cases below drive that
exact restart.
"""

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, ManagerOperations, Unobserved,
                                   receipt_rows, reconcile, status, submit,
                                   sweep)
from baton_v12.worker_manager import (AuthorityPort, accept_offer,
                                      attempt_preparation_failure_of,
                                      attempt_start_failure_of, record_attempt)

if __package__:
    from .fixtures import (NOW, PROFILE, SOON, UUID, WORK_A, FakeOperations,
                           JobManagerCase, fake_claim_signature, job,
                           submission)
else:
    from fixtures import (NOW, PROFILE, SOON, UUID, WORK_A, FakeOperations,
                          JobManagerCase, fake_claim_signature, job,
                          submission)

STAGE = "job-a/implementation"


class TheLaunchIsLevelTriggered(JobManagerCase):
    """Asked from canonical state, on every tick, including after a restart."""

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        self.acts.starts(STAGE)

    def claimed(self):
        """Two ticks: admit, then claim. The stage is now claimed."""
        sweep(self.jobs, self.acts, now=NOW)
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]],
                         [("claim", "performed")])
        return report

    def test_a_claimed_stage_is_launched_and_reported(self):
        self.claimed()
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([(one["stage_id"], one["outcome"], one["runtime_id"])
                          for one in report["started"]],
                         [(STAGE, "started", f"runtime-{STAGE}")])
        self.assertEqual(report["acts"], [],
                         "the two receipt acts are already done; the launch "
                         "is not one of them")

    def test_a_stage_that_is_not_claimed_is_never_launched(self):
        """Eligibility is canonical state, not a hopeful attempt.

        Before the claim the stage is queued and then offered, and neither
        owes a runtime.
        """
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual([one for one in self.acts.calls
                          if one[0] == "launch"], [])

    def test_a_running_stage_is_observed_rather_than_started_again(self):
        self.claimed()
        sweep(self.jobs, self.acts, now=SOON)
        # The manager now reports a runtime AND the exchange reports a worker
        # that accepted its command, so the stage is `running`.
        #
        # W81857 made the second half necessary. A runtime identity alone used
        # to be enough for this projection, and that is precisely the defect:
        # the container this test stands in for could be idling with no
        # command, no provider and no output, and nothing here would have
        # noticed. `test_status` owns the negative case.
        self.acts.observed(STAGE, claimed_by=True,
                           runtime={"attempt_id": f"attempt:{STAGE}",
                                    "runtime_id": "runtime-1",
                                    "execution_runtime": "running",
                                    "cleanup": None, "assignment": None})
        self.acts.commanded(STAGE, state="working")
        before = len([one for one in self.acts.calls if one[0] == "launch"])
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(report["started"], [])
        self.assertEqual(len([one for one in self.acts.calls
                              if one[0] == "launch"]), before)
        self.assertEqual(status(self.jobs, self.acts,
                                observed_at=SOON)["jobs"][0]["stages"][0]
                         ["state"], "running")

    def test_read_only_status_never_launches(self):
        self.claimed()
        before = len([one for one in self.acts.calls if one[0] == "launch"])
        status(self.jobs, self.acts, observed_at=SOON)
        status(self.jobs, Unobserved(), observed_at=SOON)
        self.assertEqual(len([one for one in self.acts.calls
                              if one[0] == "launch"]), before,
                         "status is a read; it asks nobody to start anything")


class TheLaunchSurvivesTheClaimCrashWindow(JobManagerCase):
    """The reason the seam is level-triggered rather than folded into `claim`.

    These drive the REAL operations, because the whole premise is what the
    canonical journal does when a manager dies between the Authority's commit
    and this store's receipt.
    """

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.control_store = self.control()
        self.started = []
        self.acts = self.operations(control=self.control_store)

    def operations(self, control=None, port=None):
        control = control if control is not None else self.control()
        port = port if port is not None else AuthorityPort(
            self.session, fake_claim_signature)
        return ManagerOperations(
            control, port, mint_bearer=self.mint,
            deliver_bearer=self.deliver,
            start_runtime=lambda stage, job: self.launched(stage))

    def launched(self, stage):
        self.started.append(stage["stage_id"])
        return {"runtime_id": f"runtime-{stage['stage_id']}"}

    def test_a_claim_adopted_after_a_crash_is_still_launched(self):
        """THE DEFECT THIS SEAM EXISTS FOR, driven end to end.

        The claim commits at the Authority and the process dies before its
        receipt. The next incarnation ADOPTS that canonical settlement -- it
        never calls `claim` again -- so a launch hidden inside `claim` would
        never happen for this stage, ever.
        """
        sweep(self.jobs, self.acts, now=NOW)
        stage = self.attempting(self.jobs)
        accept_offer(self.control_store, self.acts.port,
                     offer_id=stage["offer_id"], decision="accept",
                     bearer=self.delivered[-1]["bearer"], now=NOW,
                     runtime_attempt_id=stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        sweep(self.jobs, self.acts, now=NOW)
        # THE CRASH: the Authority holds the claim, this store's receipt is
        # gone, and so is anything the launch might have recorded.
        self.jobs._connection.execute(
            "DELETE FROM receipts WHERE act = 'claim'")
        self.jobs._connection.execute(
            "DELETE FROM operations WHERE operation_id LIKE '%:claim'")
        self.started.clear()
        self.session.calls.clear()
        resumed = JobStore.open(self.job_path, incarnation="jobs-2",
                                clock=self.clock)
        self.addCleanup(resumed.close)
        report = sweep(resumed, self.acts, now=SOON)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["acts"]],
                         [("claim", "adopted")],
                         "the claim is ADOPTED, not re-called")
        self.assertEqual([call for call in self.session.calls
                          if call[0] == "claim"], [])
        # AND THE LAUNCH STILL HAPPENED, which is the whole correction.
        self.assertEqual(self.started, [STAGE])
        self.assertEqual([(one["stage_id"], one["outcome"])
                          for one in report["started"]], [(STAGE, "started")])

    def test_reconcile_launches_on_the_first_tick_after_a_restart(self):
        sweep(self.jobs, self.acts, now=NOW)
        stage = self.attempting(self.jobs)
        accept_offer(self.control_store, self.acts.port,
                     offer_id=stage["offer_id"], decision="accept",
                     bearer=self.delivered[-1]["bearer"], now=NOW,
                     runtime_attempt_id=stage["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        sweep(self.jobs, self.acts, now=NOW)
        self.started.clear()
        resumed = JobStore.open(self.job_path, incarnation="jobs-3",
                                clock=self.clock)
        self.addCleanup(resumed.close)
        reconcile(resumed, self.acts, now=SOON)
        self.assertEqual(self.started, [STAGE],
                         "recovery and the ordinary tick ask the same "
                         "question, which is what level-triggered means")


class AFailedStartIsContainedAndExceptional(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a"), job(
            "job-b", stages=[{"kind": "implementation", "work_id": WORK_A,
                              "profile_name": "reference",
                              "profile_digest": PROFILE,
                              "depends_on": []}])]))
        self.acts = FakeOperations()
        self.acts.starts(STAGE)
        self.acts.starts("job-b/implementation")
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)

    def states(self):
        return {one["stage_id"]: one["state"] for job_status in
                status(self.jobs, self.acts, observed_at=SOON)["jobs"]
                for one in job_status["stages"]}

    def test_a_recorded_durable_refusal_is_contained_and_becomes_exceptional(self):
        """The acceptance, and review [P1] made it sharper.

        Reporting the refusal was never enough: the stage stayed `claimed`
        with no canonical ending, so the next tick asked again forever. What
        contains it is the Worker Manager's own failed-start record, and this
        case proves all three halves -- contained, exceptional, not retried --
        while an unrelated stage is still launched in the same sweep.
        """
        self.acts.fails(STAGE, ContractRefusal(
            "refused", "precondition", "the engine refused the image",
            durable=True))
        report = sweep(self.jobs, self.acts, now=SOON)
        outcomes = {one["stage_id"]: one["outcome"]
                    for one in report["started"]}
        self.assertEqual(outcomes[STAGE], "refused")
        self.assertEqual(outcomes["job-b/implementation"], "started",
                         "the unrelated stage was still launched")
        self.assertEqual(self.states()[STAGE], "exceptional")
        # AND IT IS NOT ASKED AGAIN. The canonical ending is what stops the
        # level-triggered loop, which is the half the earlier case missed.
        before = self.acts.calls.count(("launch", STAGE))
        again = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([one for one in again["started"]
                          if one["stage_id"] == STAGE], [])
        self.assertEqual(self.acts.calls.count(("launch", STAGE)), before,
                         "the ended stage is not asked again")
        self.assertEqual([one["stage_id"] for one in again["started"]],
                         ["job-b/implementation"],
                         "and the unrelated stage still is")

    def test_a_durable_refusal_nobody_recorded_refuses_rather_than_looping(self):
        """Review [P1]: the silent forever-retry this used to be.

        A deployment that refuses durably and journals nothing leaves this
        control plane no fact to project and no reason to stop. Reporting it
        as a stage outcome would be a retry loop with a tidy report; the
        honest answer names the deployment's omission.
        """
        self.acts.fails(STAGE, ContractRefusal(
            "refused", "precondition", "a durable ending nobody wrote down",
            durable=True), records=False)
        with self.assertRaises(ContractRefusal) as caught:
            sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("no failed-start record", caught.exception.message)

    def test_a_recorded_adapter_fault_is_contained_and_the_sweep_continues(self):
        """Review [P1]: the production fault path, which is not a refusal.

        `request_runtime_start` journals the failed start and then RE-RAISES
        the adapter's own typed fault, so a real engine error is not a
        `ContractRefusal` at all. It escaped the handler, skipped every stage
        sorted after it, and ended `serve`. The failing stage is sorted FIRST
        here on purpose, so a stage that only runs after it is the evidence.
        """
        self.assertLess(STAGE, "job-b/implementation",
                        "the failing stage must sort first for this to prove "
                        "anything")
        self.acts.fails(STAGE, OSError("no such image"))
        report = sweep(self.jobs, self.acts, now=SOON)
        outcomes = {one["stage_id"]: one["outcome"]
                    for one in report["started"]}
        self.assertEqual(outcomes[STAGE], "refused")
        self.assertEqual(outcomes["job-b/implementation"], "started",
                         "the stage sorted after the fault was still reached")
        self.assertEqual(self.states()[STAGE], "exceptional")
        # AND THE LOOP KEEPS SERVING: a later tick still runs and still
        # observes the unrelated stage.
        self.assertIsNotNone(sweep(self.jobs, self.acts, now=SOON))

    def test_an_unrecorded_fault_is_raised_rather_than_buried(self):
        """A programming error has no canonical record, and must not become a
        stage outcome that looks like a transient condition."""
        self.acts.fails(STAGE, RuntimeError("a defect, not an ending"),
                        records=False)
        with self.assertRaises(RuntimeError):
            sweep(self.jobs, self.acts, now=SOON)

    def test_an_ordinary_refusal_defers_and_the_next_tick_asks_again(self):
        self.acts.starts(STAGE, ContractRefusal(
            "refused", "precondition", "the workspace is not ready yet"))
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual({one["stage_id"]: one["outcome"]
                          for one in report["started"]}[STAGE], "deferred")
        self.acts.starts(STAGE)
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual({one["stage_id"]: one["outcome"]
                          for one in report["started"]}[STAGE], "started")

    def test_a_recorded_preparation_failure_projects_exceptional(self):
        """W76207 re-review [P1]: the manager keeps TWO ending records.

        A start act that failed is also `intake`'s authority to remove the
        container that start created; a post-claim preparation that never
        reached an adapter authorizes nothing. They are two durable facts and
        one stage state, so this projection asks for both and reads either as
        the stage being over.
        """
        self.acts.observed(
            STAGE, claimed_by=True,
            runtime={"attempt_id": f"attempt:{STAGE}", "runtime_id": None,
                     "execution_runtime": "start-requested",
                     "cleanup": None, "assignment": None},
            preparation_failure={
                "attempt_id": f"attempt:{STAGE}", "expect": None,
                "runtime_id": None, "execution_runtime": "start-requested",
                "failure": {"kind": "refusal", "category": "refused",
                            "code": "precondition",
                            "message": "this attempt cannot be recovered"}})
        held = {one["stage_id"]: one for job_status in
                status(self.jobs, self.acts, observed_at=SOON)["jobs"]
                for one in job_status["stages"]}
        self.assertEqual(held[STAGE]["state"], "exceptional")
        self.assertEqual(held["job-b/implementation"]["state"], "claimed",
                         "the other stage is still observable")
        # AND IT IS NOT ASKED TO START AGAIN.
        before = len([one for one in self.acts.calls if one[0] == "launch"])
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([one for one in report["started"]
                          if one["stage_id"] == STAGE], [])
        self.assertEqual(len([one for one in self.acts.calls
                              if one[0] == "launch"]), before + 1,
                         "only the unrelated stage was asked")

    def test_a_recorded_start_failure_projects_exceptional(self):
        """W76207's other half: the runtime id must not answer first.

        Failed-start reconciliation may ATTACH a runtime id, so an observation
        that carried only the runtime reported this stage as `running`. The
        manager's own record decides.
        """
        self.acts.observed(
            STAGE, claimed_by=True,
            runtime={"attempt_id": f"attempt:{STAGE}",
                     "runtime_id": "runtime-attached-after-the-failure",
                     "execution_runtime": "running", "cleanup": None,
                     "assignment": None},
            start_failure={"attempt_id": f"attempt:{STAGE}", "expect": None,
                           "start_operation_id": "runtime.start:abc",
                           "runtime_id": "runtime-attached-after-the-failure",
                           "execution_runtime": "running",
                           "failure": {"kind": "fault", "fault": "OSError",
                                       "message": "no such image"}})
        held = {one["stage_id"]: one for job_status in
                status(self.jobs, self.acts, observed_at=SOON)["jobs"]
                for one in job_status["stages"]}
        self.assertEqual(held[STAGE]["state"], "exceptional")
        self.assertEqual(held["job-b/implementation"]["state"], "claimed",
                         "the other stage is still observable")
        # AND IT IS NOT ASKED TO START AGAIN.
        before = len([one for one in self.acts.calls if one[0] == "launch"])
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([one for one in report["started"]
                          if one["stage_id"] == STAGE], [])
        self.assertEqual(len([one for one in self.acts.calls
                              if one[0] == "launch"]), before + 1,
                         "only the unrelated stage was asked")


class TheStartFailureRead(JobManagerCase):
    """The narrow public read this leaf added to the Worker Manager."""

    def test_an_attempt_nobody_recorded_answers_absence(self):
        control = self.control()
        self.assertIsNone(attempt_start_failure_of(control, "attempt:nobody"))

    def test_an_attempt_whose_start_never_failed_answers_absence(self):
        control = self.control()
        record_attempt(control, attempt_id="attempt-1",
                       adapter_name="reference", adapter_digest="sha256:a",
                       profile_digest=PROFILE)
        self.assertIsNone(attempt_start_failure_of(control, "attempt-1"))

    def test_the_preparation_read_answers_absence_for_the_same_two(self):
        """Its sibling, and its own read for the same two absences."""
        control = self.control()
        self.assertIsNone(
            attempt_preparation_failure_of(control, "attempt:nobody"))
        record_attempt(control, attempt_id="attempt-1",
                       adapter_name="reference", adapter_digest="sha256:a",
                       profile_digest=PROFILE)
        self.assertIsNone(
            attempt_preparation_failure_of(control, "attempt-1"))


if __name__ == "__main__":
    unittest.main()
