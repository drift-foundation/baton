"""W71875 — the read-only status projection.

WHAT AN OPERATOR HAS TO BE ABLE TO READ WITHOUT OPENING A CONTAINER: which
stage is in which state, which gate is holding a blocked one, which runtime
identity and safe locators exist for a running one, and which acts this
control plane recorded. That is the acceptance bullet, and these cases drive
it state by state.

AND WHAT IT MUST NOT DO: the projection is derived, so nothing here writes,
and a status assembled without the manager's control store says so rather than
reporting an empty pipeline as a quiet one.
"""

import copy
import unittest

from baton_v12.contracts import ContractRefusal

from baton_v12.job_manager import (STAGE_STATES, STATUS_SCHEMA, Unobserved,
                                   receipt_rows, status, submit, sweep)
from baton_v12.job_manager.episodes import identities

if __package__:
    from .fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase, job,
                           stage, submission)
else:
    from fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase, job,
                          stage, submission)


class StatusCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()

    def states(self, document):
        return {one["stage_id"]: one["state"]
                for entry in document["jobs"] for one in entry["stages"]}

    def stage_of(self, document, stage_id):
        for entry in document["jobs"]:
            for one in entry["stages"]:
                if one["stage_id"] == stage_id:
                    return one
        raise AssertionError(stage_id)


class Shape(StatusCase):

    def test_the_document_names_its_schema_and_what_it_observed(self):
        submit(self.jobs, submission())
        document = status(self.jobs, self.acts, observed_at=NOW)
        self.assertEqual(document["schema"], STATUS_SCHEMA)
        self.assertEqual(document["observed_at"], NOW)
        self.assertEqual(document["incarnation"], "jobs-1")
        self.assertTrue(document["canonical"])

    def test_a_projection_with_no_control_store_says_nobody_looked(self):
        submit(self.jobs, submission())
        document = status(self.jobs, Unobserved(), observed_at=NOW)
        self.assertFalse(document["canonical"])
        # It still reports what was submitted, which is the whole reason the
        # read-only surface exists.
        self.assertEqual(sorted(self.states(document)),
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])

    def test_the_job_carries_its_immutable_identities_and_bounded_scope(self):
        submit(self.jobs, submission())
        first = status(self.jobs, self.acts, observed_at=NOW)["jobs"][0]
        self.assertEqual(first["job_id"], "job-a")
        self.assertEqual(first["submission_id"], "sub-1")
        self.assertEqual(first["input_digest"], "sha256:" + "1" * 64)
        self.assertEqual(first["test_scope"], ["v12/python/tests/job_manager"])
        self.assertEqual(first["terminal_policy"], "report-and-hold")

    def test_an_empty_store_projects_an_empty_pipeline(self):
        self.assertEqual(status(self.jobs, self.acts,
                                observed_at=NOW)["jobs"], [])

    def test_reading_a_status_writes_nothing(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        before = receipt_rows(self.jobs)
        for _ in range(3):
            status(self.jobs, self.acts, observed_at=LATER)
        self.assertEqual(receipt_rows(self.jobs), before)


class States(StatusCase):

    def test_a_submitted_pipeline_is_queued_and_blocked(self):
        submit(self.jobs, submission())
        self.assertEqual(self.states(status(self.jobs, self.acts,
                                            observed_at=NOW)),
                         {"job-a/implementation": "queued",
                          "job-a/review": "blocked",
                          "job-b/implementation": "queued"})

    def test_a_blocked_stage_names_the_gate_holding_it(self):
        submit(self.jobs, submission())
        review = self.stage_of(status(self.jobs, self.acts, observed_at=NOW),
                               "job-a/review")
        self.assertEqual(review["gates"],
                         [{"stage_id": "job-a/implementation",
                           "state": "queued", "open": False}])

    def test_an_admitted_stage_is_offered(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/implementation"],
            "offered")

    def test_a_claimed_stage_with_no_runtime_is_claimed(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts.observed("job-a/implementation", claimed_by=True)
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/implementation"],
            "claimed")

    def test_each_kind_names_its_own_running_state(self):
        submit(self.jobs, submission(jobs=[job("job-a", stages=[
            stage("implementation"), stage("review"),
            stage("integration")])]))
        for stage_id in ("job-a/implementation", "job-a/review",
                         "job-a/integration"):
            _offer_id, attempt_id = identities(UUID, stage_id, 1)
            self.acts.observed(stage_id, claimed_by=True,
                               runtime={"attempt_id": attempt_id,
                                        "runtime_id": "runtime-1",
                                        "execution_runtime": "running",
                                        "cleanup": None, "assignment": None},
                               activity={"attempt_id": attempt_id,
                                         "bytes_observed": 12,
                                         "observed_at": NOW})
            # W81857: THE ACTIVE WORD IS EARNED BY THE WORKER'S RECEIPT, not
            # by the runtime identity. The negative half of this rule is
            # `test_a_started_container_nobody_commanded_is_not_running`.
            self.acts.commanded(stage_id, state="working")
        self.assertEqual(self.states(status(self.jobs, self.acts,
                                            observed_at=NOW)),
                         {"job-a/implementation": "running",
                          "job-a/review": "reviewing",
                          "job-a/integration": "integrating"})

    def test_an_uncertain_runtime_is_exceptional_and_never_running(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        _offer_id, attempt_id = identities(UUID, "job-a/implementation", 1)
        self.acts.observed(
            "job-a/implementation", claimed_by=True,
            runtime={"attempt_id": attempt_id, "runtime_id": "runtime-1",
                     "execution_runtime": "uncertain", "cleanup": None,
                     "assignment": None})
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/implementation"],
            "exceptional")

    def test_a_completed_stage_opens_its_successor_s_gate(self):
        submit(self.jobs, submission())
        self.acts.frozen("job-a/implementation", "completed")
        document = status(self.jobs, self.acts, observed_at=NOW)
        self.assertEqual(self.states(document)["job-a/implementation"],
                         "completed")
        self.assertEqual(self.states(document)["job-a/review"], "queued")
        self.assertEqual(self.stage_of(document, "job-a/review")["gates"],
                         [{"stage_id": "job-a/implementation",
                           "state": "completed", "open": True}])

    def test_a_rejected_review_is_changes_requested(self):
        submit(self.jobs, submission(jobs=[job("job-a",
                                               stages=[stage("review")])]))
        self.acts.frozen("job-a/review", "plan-rejected")
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/review"],
            "changes-requested")

    def test_a_rejection_on_a_stage_that_is_not_a_review_is_exceptional(self):
        # `plan-rejected` is a REVIEW's verdict. The same disposition anywhere
        # else is an ending nobody planned for, and rounding it to the nearest
        # happy state would hide it.
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts.frozen("job-a/implementation", "plan-rejected")
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/implementation"],
            "exceptional")

    def test_a_cancelled_or_unable_ending_is_exceptional(self):
        # ONE STORE, ONE JOB PER DISPOSITION: both endings are reported side
        # by side rather than one test being two, and neither can pass because
        # the other set the state.
        submit(self.jobs, submission(jobs=[job("job-unable"),
                                           job("job-cancelled")]))
        self.acts.frozen("job-unable/implementation", "unable")
        self.acts.frozen("job-cancelled/implementation", "cancelled")
        self.assertEqual(self.states(status(self.jobs, self.acts,
                                            observed_at=NOW)),
                         {"job-unable/implementation": "exceptional",
                          "job-cancelled/implementation": "exceptional"})

    def test_a_disposition_this_build_does_not_know_is_not_read_as_benign(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts.frozen("job-a/implementation", "something-new")
        self.assertEqual(
            self.states(status(self.jobs, self.acts,
                               observed_at=NOW))["job-a/implementation"],
            "exceptional")

    def test_every_projected_state_is_in_the_closed_vocabulary(self):
        submit(self.jobs, submission())
        self.acts.frozen("job-a/implementation", "completed")
        for state in self.states(status(self.jobs, self.acts,
                                        observed_at=NOW)).values():
            self.assertIn(state, STAGE_STATES)


class Locators(StatusCase):

    def test_a_running_stage_reports_its_runtime_identity_and_activity(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        _offer_id, attempt_id = identities(UUID, "job-a/implementation", 1)
        self.acts.observed(
            "job-a/implementation", claimed_by=True,
            runtime={"attempt_id": attempt_id,
                     "runtime_id": "runtime-1",
                     "execution_runtime": "running", "cleanup": None,
                     "assignment": {"work_ref": {"work_id": "0000000a-W1"},
                                    "participant": "baton.claude",
                                    "generation": 1}},
            activity={"attempt_id": attempt_id,
                      "bytes_observed": 4096, "observed_at": NOW})
        found = self.stage_of(status(self.jobs, self.acts, observed_at=NOW),
                              "job-a/implementation")
        self.assertEqual(found["runtime"]["runtime_id"], "runtime-1")
        self.assertEqual(found["runtime"]["assignment"]["generation"], 1)
        self.assertEqual(found["runtime"]["activity"]["bytes_observed"], 4096)
        self.assertEqual(found["attempt_id"], attempt_id)

    def test_a_frozen_result_reports_the_managers_own_artifact_locators(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts.frozen("job-a/implementation", "completed", artifacts=[
            {"output_name": "proposal", "artifact_id": "artifact-1",
             "media_type": "application/x-patch", "bytes": 1024,
             "content_digest": "sha256:" + "d" * 64,
             "locator": "outputs/proposal.patch"}])
        found = self.stage_of(status(self.jobs, self.acts, observed_at=NOW),
                              "job-a/implementation")
        self.assertEqual(found["artifacts"][0]["locator"],
                         "outputs/proposal.patch")

    def test_a_stage_with_no_runtime_reports_absence_rather_than_zero(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        found = self.stage_of(status(self.jobs, self.acts, observed_at=NOW),
                              "job-a/implementation")
        self.assertIsNone(found["runtime"])
        self.assertIsNone(found["artifacts"])

    def test_the_recorded_receipts_travel_with_the_stage(self):
        submit(self.jobs, submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        found = self.stage_of(status(self.jobs, self.acts, observed_at=LATER),
                              "job-a/implementation")
        self.assertEqual([one["act"] for one in found["receipts"]], ["admit"])
        self.assertEqual(found["receipts"][0]["operation_id"],
                         "offer.issue:" + identities(UUID, "job-a/implementation", 1)[0])
        self.assertEqual(found["receipts"][0]["detail"]["canonical_state"],
                         "committed")


if __name__ == "__main__":
    unittest.main()


class AnIntegrationStageIsProjectedFromItsOwnObservation(StatusCase):
    """W126558, `OBSERVATION.md` revision 1.

    THE DEFECT THIS CLASS IS. An integration attempt writes no worker exchange
    and freezes no output, so every member the canonical observation carried
    was honestly absent for it -- and absence there is `starting`, which owes
    `dispatch`, which is a worker exchange act nothing on this path can
    perform. The stage sat at `starting` forever while the sweep asked for a
    dispatch nobody could answer.

    EARLIER FAILURE RECORDS KEEP THEIR PRECEDENCE. A supplied document takes
    its own path only after the durable refusal, the failed start, the failed
    preparation and the uncertain runtime have had theirs.
    """

    STAGE = "job-a/integration"
    ASSIGNMENT = {"work_ref": {"authority_uuid": UUID,
                               "work_id": "0000000a-W1"},
                  "participant": "baton.integrator", "generation": 5}

    def submitted(self):
        submit(self.jobs, submission(jobs=[job("job-a", stages=[
            stage("integration")])]))

    def runtime(self, execution_runtime="running", runtime_id="runtime-1"):
        return {"attempt_id": "attempt-1", "runtime_id": runtime_id,
                "execution_runtime": execution_runtime,
                "assignment": copy.deepcopy(self.ASSIGNMENT)}

    def document(self, state="pending", completion=None):
        from baton_v12.job_manager import episodes

        offer_id, attempt_id = episodes.identities(UUID, self.STAGE, 1)[:2]
        del attempt_id
        return {"schema": ("baton.v12.integration-stage-observation/1"),
                "stage_id": self.STAGE, "episode": 1,
                "attempt_id": episodes.identities(UUID, self.STAGE, 1)[1],
                "offer_id": offer_id,
                "assignment": copy.deepcopy(self.ASSIGNMENT),
                "state": state, "completion": completion}

    def completion(self):
        return {"proposal_id": "proposal-1",
                "integration_receipt_id": "receipt-1", "entry_id": "entry-1",
                "lease_id": "lease-1", "fence": 2,
                "handoff_operation_id": "pass:attempt-1",
                "to_route": "rview", "runtime_id": "runtime-1",
                "execution_runtime": "destroyed"}

    def projected(self, state="pending", runtime=None, completion=None,
                  **members):
        self.submitted()
        held = self.runtime() if runtime is None else runtime
        attempt = self.document(state, completion)
        attempt["attempt_id"] = held["attempt_id"] = attempt["attempt_id"]
        self.acts.observed(self.STAGE, claimed_by=True, runtime=held,
                           integration=attempt, **members)
        # THE FIXTURE'S OWN OFFER IDENTITY, so the document is bound to the
        # claim rather than to a spelling this case invented.
        self.acts.observations[self.STAGE]["integration"]["offer_id"] = (
            self.acts.observations[self.STAGE]["claimed_by"])
        return self.states(status(self.jobs, self.acts,
                                  observed_at=NOW))[self.STAGE]

    # -- the states OBSERVATION.md pins --------------------------------------

    def test_pending_with_a_running_runtime_is_integrating(self):
        self.assertEqual(self.projected("pending"), "integrating")

    def test_pending_with_a_quiet_runtime_is_answering(self):
        """So `conclude` reaches the driver and the DRIVER decides what a
        missing or lost result means."""
        for axis in ("quiescent", "destroyed"):
            with self.subTest(axis=axis):
                self.setUp()
                self.assertEqual(
                    self.projected("pending", runtime=self.runtime(axis)),
                    "answering")

    def test_answered_is_answering_whatever_the_runtime_is_doing(self):
        """Concluding changes no Job state by itself; the next observation is
        what proves the result."""
        for axis in ("running", "quiescent", "destroyed"):
            with self.subTest(axis=axis):
                self.setUp()
                self.assertEqual(
                    self.projected("answered", runtime=self.runtime(axis)),
                    "answering")

    def test_completed_is_completed(self):
        self.assertEqual(
            self.projected("completed", runtime=self.runtime("destroyed"),
                           completion=self.completion()), "completed")

    def test_held_is_a_visible_exceptional_stage(self):
        self.assertEqual(self.projected("held"), "exceptional")

    def test_unstarted_is_claimed_and_still_owes_its_launch(self):
        self.assertEqual(
            self.projected("unstarted",
                           runtime={"attempt_id": "attempt-1",
                                    "runtime_id": None,
                                    "execution_runtime": "not-started",
                                    "assignment": copy.deepcopy(
                                        self.ASSIGNMENT)}),
            "claimed")

    # -- and what fails closed ------------------------------------------------

    def test_unstarted_beside_a_started_runtime_fails_closed(self):
        self.assertEqual(self.projected("unstarted"), "exceptional")

    def test_pending_or_answered_without_a_runtime_fails_closed(self):
        for state in ("pending", "answered"):
            with self.subTest(state=state):
                self.setUp()
                self.assertEqual(
                    self.projected(state,
                                   runtime={"attempt_id": "attempt-1",
                                            "runtime_id": None,
                                            "execution_runtime":
                                                "not-started",
                                            "assignment": copy.deepcopy(
                                                self.ASSIGNMENT)}),
                    "exceptional")

    def test_an_uncertain_runtime_holds_the_three_that_earn_an_act(self):
        """No automatic conclude follows an uncertain runtime.

        OBSERVATION.md restricts that suppression to the three states that
        would otherwise earn an act; review 2026-09-09T09:13Z [2] is right
        that including `completed` here was wrong, and the case below is its
        correction.
        """
        for state in ("unstarted", "pending", "answered"):
            with self.subTest(state=state):
                self.setUp()
                self.assertEqual(
                    self.projected(state, runtime=self.runtime("uncertain")),
                    "exceptional")

    def test_a_completed_account_survives_a_later_uncertain_refresh(self):
        """[2]. A completed integration is HISTORICAL evidence about the fixed
        assignment, proved by the consumer before it was written. A mutable
        axis read afterwards is not a fact about it, and projecting
        `exceptional` there would let a refresh unmake a committed proof.
        """
        self.assertEqual(
            self.projected("completed", runtime=self.runtime("uncertain"),
                           completion=self.completion()), "completed")

    def test_a_held_document_is_not_turned_into_an_owed_ending(self):
        """[3]. The generic rules answered first about evidence that was never
        an integration attempt's: a `held` document beside a frozen output
        projected `answering` and owed a conclude the pinned held outcome does
        not."""
        self.assertEqual(
            self.projected("held", runtime=self.runtime("destroyed"),
                           output={"disposition": "completed",
                                   "manifest_digest": "sha256:" + "1" * 64}),
            "exceptional")

    def test_a_foreign_frozen_output_cannot_complete_an_integration(self):
        """The same rule the other way: an integration still working is not
        completed because some output exists."""
        self.assertEqual(
            self.projected("pending", output={"disposition": "completed",
                                              "manifest_digest":
                                                  "sha256:" + "1" * 64}),
            "integrating")

    def test_a_foreign_exchange_cannot_move_an_integration(self):
        """An integration attempt writes no worker exchange, so one that
        somehow appears beside it decides nothing."""
        self.assertEqual(
            self.projected("pending",
                           exchange={"transport": "baton.worker-exchange/1",
                                     "sequence_id": "sequence-x",
                                     "state": "answered"}),
            "integrating")

    def test_a_supplied_document_for_another_kind_refuses_at_the_status(self):
        """[1], through the public projection rather than the binding alone."""
        submit(self.jobs, submission(jobs=[job("job-b", stages=[
            stage("implementation")])]))
        offer_id, attempt_id = identities(UUID, "job-b/implementation", 1)[:2]
        self.acts.observed(
            "job-b/implementation", claimed_by=True,
            runtime={"attempt_id": attempt_id, "runtime_id": "runtime-1",
                     "execution_runtime": "destroyed",
                     "assignment": copy.deepcopy(self.ASSIGNMENT)},
            integration={
                "schema": "baton.v12.integration-stage-observation/1",
                "stage_id": "job-b/implementation", "episode": 1,
                "attempt_id": attempt_id, "offer_id": offer_id,
                "assignment": copy.deepcopy(self.ASSIGNMENT),
                "state": "completed", "completion": self.completion()})
        with self.assertRaises(ContractRefusal) as caught:
            status(self.jobs, self.acts, observed_at=NOW)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_failed_start_still_answers_first(self):
        self.assertEqual(
            self.projected("completed", runtime=self.runtime("destroyed"),
                           completion=self.completion(),
                           start_failure={"reason": "no image"}),
            "exceptional")
