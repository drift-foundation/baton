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

import unittest

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
