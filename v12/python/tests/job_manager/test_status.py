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

from baton_v12.job_manager import (JobStore, STAGE_STATES, STATUS_SCHEMA,
                                   Unobserved,
                                   receipt_rows, status, submit, sweep)
from baton_v12.job_manager import delegation, projection
from baton_v12.job_manager import submission as submission_reads
from baton_v12.job_manager.episodes import (end_episode, identities, live_of,
                                            open_next)
from baton_v12.job_manager.projection import receipts_of

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
        # PRE-EXISTING AND FOUND IN PASSING (W197661 claim199391): this
        # fixture omitted `source_proposal_id` and `result_id`, which
        # `delegation.INTEGRATION_COMPLETION_MEMBERS` requires, so three cases
        # errored on a completion account the product would never accept. The
        # fixture lagged the contract; the contract is right.
        return {"proposal_id": "proposal-1",
                "source_proposal_id": "proposal-0",
                # NULL, and that is the statement: a reconciliation result id
                # means a reconciled import, which "starts no runtime" -- and
                # this fixture's integration ran a container and destroyed it.
                "result_id": None,
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


class ConcurrentSubmission(StatusCase):
    """W319114 — one status describes ONE moment of the Job store.

    THE MEASURED DEFECT. `status` derived the stage states, and only then read
    the Job rows and each Job's stage rows. A public `submit` committing in
    between put a stage in the second read that the first had no entry for, and
    the composed document raised `KeyError` on `held[row["stage_id"]]` --
    reported to an operator as an unexplained crash of the read-only surface,
    on a store that was behaving exactly as designed.

    THESE USE TWO REAL CONNECTIONS, which is what makes them about the
    boundary. `self.jobs` is the serving manager's write-capable handle and
    `self.reader` is the read-only one a monitor opens, both over one store
    file. The interleaving is DETERMINISTIC: the writer's act runs inside a
    wedge placed at the exact seam, so nothing here depends on thread timing.

    WHAT THE FIX IS. `projection.materialized` reads every Job-owned row under
    one read view of this database and releases it; the canonical observations
    are acquired afterwards. So the document reports an earlier coherent
    moment -- never a Job without its stages, a stage without its Job, or an
    episode beside the receipts of the one that replaced it -- and no
    observation is ever attempted while a Job-store transaction is open.
    """

    def setUp(self):
        super().setUp()
        self.reader = JobStore.open_readonly(
            self.job_path, authority_uuid=UUID, incarnation="jobs-monitor",
            clock=self.clock)
        self.addCleanup(self.reader.close)

    # -- the deterministic interleaving ---------------------------------------

    def wedge(self, holder, name, act):
        """Run `act` ONCE, immediately after `holder.name` has answered.

        Returns the list the wedge appends to, so a case can prove the
        interleaving actually happened rather than passing because it did not.
        """
        real = getattr(holder, name)
        fired = []

        def wedged(*operands, **supplied):
            answer = real(*operands, **supplied)
            if not fired:
                fired.append(True)
                act()
            return answer

        setattr(holder, name, wedged)
        self.addCleanup(setattr, holder, name, real)
        return fired

    def dump(self):
        """Every row of every table, as the WRITER sees it.

        The projection must change nothing, and a read-only connection cannot
        be trusted to prove that about itself.
        """
        tables = [row[0] for row in self.jobs._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "ORDER BY name")]
        return {name: [tuple(row) for row in self.jobs._connection.execute(
            f"SELECT * FROM {name}").fetchall()] for name in tables}

    # -- the original race ----------------------------------------------------

    def test_a_submission_committed_between_the_two_reads_no_longer_raises(self):
        """The minimal baseline from the finding, end to end.

        An empty store, the state derivation answering its real empty result, a
        public `submit` on the writer, and then the rest of `status`. This is
        the case that raised `KeyError: 'job-a/implementation'`.
        """
        fired = self.wedge(projection, "stage_states",
                           lambda: submit(self.jobs, submission()))
        document = status(self.reader, self.acts, observed_at=NOW)
        self.assertEqual(fired, [True])
        # THE EARLIER MOMENT, WHOLE. The submission is absent with its Jobs
        # AND its stages rather than half-present.
        self.assertEqual(document["jobs"], [])
        self.assertEqual(document["observed_at"], NOW)

    def test_a_submission_committed_INSIDE_the_materialization_is_coherent(self):
        """The same race one layer in: the writer commits between the stage
        read and the Job read, which is where the two moments actually met."""
        fired = self.wedge(submission_reads, "stage_rows",
                           lambda: submit(self.jobs, submission()))
        document = status(self.reader, self.acts, observed_at=NOW)
        self.assertEqual(fired, [True])
        self.assertEqual(document["jobs"], [])

    def test_the_new_stages_are_reported_by_the_NEXT_read_and_not_lost(self):
        """An earlier coherent moment is not a silent omission. The submission
        the racing status could not include is in the one after it, in full."""
        self.wedge(projection, "stage_states",
                   lambda: submit(self.jobs, submission()))
        self.assertEqual(status(self.reader, self.acts,
                                observed_at=NOW)["jobs"], [])
        self.assertEqual(
            sorted(self.states(status(self.reader, self.acts,
                                      observed_at=LATER))),
            ["job-a/implementation", "job-a/review", "job-b/implementation"])

    def test_every_reported_stage_has_its_Job_and_every_Job_its_stages(self):
        """The invariant the `KeyError` was the symptom of, asserted directly
        under the same interleaving."""
        self.wedge(projection, "stage_states",
                   lambda: submit(self.jobs, submission(
                       submission_id="sub-2",
                       jobs=[job("job-late")])))
        submit(self.jobs, submission())
        document = status(self.reader, self.acts, observed_at=NOW)
        for entry in document["jobs"]:
            self.assertTrue(entry["stages"], entry["job_id"])
            for one in entry["stages"]:
                self.assertEqual(one["job_id"], entry["job_id"])
        self.assertEqual(sorted(one["job_id"] for one in document["jobs"]),
                         ["job-a", "job-b"])

    # -- a concurrent ADVANCEMENT, which is the other half of the rule --------

    def test_an_episode_advancing_mid_status_is_not_mixed_with_the_next_one(self):
        """A stage whose live episode ends and is replaced WHILE the status is
        composing its observations is reported as the moment it materialized:
        episode one, unended, with episode one's receipts. A pass that read the
        episode early and the rest late would name episode two beside the
        receipts of the episode it replaced.
        """
        submit(self.jobs, submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        before = receipts_of(self.jobs, "job-a/implementation", 1)
        self.assertIn("admit", before)

        def advance():
            live = live_of(self.jobs, "job-a/implementation")
            ended = end_episode(self.jobs, live, "abandoned-after-restart", 1)
            open_next(self.jobs, "job-a/implementation", ended)

        fired = self.wedge(delegation, "observation_of", advance)
        one = self.stage_of(status(self.reader, self.acts, observed_at=LATER),
                            "job-a/implementation")
        self.assertEqual(fired, [True])
        self.assertEqual(one["episode"], 1)
        self.assertEqual([record["episode"] for record in one["episodes"]], [1])
        self.assertIsNone(one["episodes"][0]["ended_state"])
        self.assertEqual(sorted(record["episode"]
                                for record in one["receipts"]), [1])
        # AND THE ADVANCEMENT IS NOT LOST EITHER -- the next read has it.
        after = self.stage_of(status(self.reader, self.acts, observed_at=LATER),
                             "job-a/implementation")
        self.assertEqual(after["episode"], 2)
        self.assertEqual([record["episode"] for record in after["episodes"]],
                         [1, 2])

    def test_a_concurrent_advancement_leaves_the_derivation_coherent_too(self):
        """`stage_states` on its own -- the pass the sweep and the owed-act
        derivation both come through -- holds the same line."""
        submit(self.jobs, submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)

        def advance():
            live = live_of(self.jobs, "job-a/implementation")
            ended = end_episode(self.jobs, live, "abandoned-after-restart", 1)
            open_next(self.jobs, "job-a/implementation", ended)

        fired = self.wedge(delegation, "observation_of", advance)
        entry = projection.stage_states(
            self.reader, self.acts)["job-a/implementation"]
        self.assertEqual(fired, [True])
        self.assertEqual(entry["episode"]["episode"], 1)
        self.assertEqual([record["episode"] for record in entry["history"]],
                         [1])
        self.assertEqual(entry["attempt"]["attempt_id"],
                         entry["episode"]["attempt_id"])

    # -- DB-1 and DB-4: nothing external happens under this store's boundary --

    def test_the_other_store_is_read_with_no_Job_transaction_open(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        seen = []
        real = delegation.observation_of

        def watched(operations, stage, held):
            seen.append((self.reader._connection.in_transaction,
                         self.jobs._connection.in_transaction))
            return real(operations, stage, held)

        delegation.observation_of = watched
        self.addCleanup(setattr, delegation, "observation_of", real)
        status(self.reader, self.acts, observed_at=LATER)
        self.assertTrue(seen)
        self.assertEqual(set(seen), {(False, False)})

    def test_a_FAILING_observation_also_leaves_no_boundary_behind(self):
        """DB-1 is not satisfied by the happy path. An observation that raises
        must do so with the read view already released, or the refusal would
        propagate out of a store still holding a transaction."""
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        broken = ContractRefusal("unavailable", "transport",
                                 "the canonical store could not be read")

        real = delegation.observation_of
        seen = []

        def failing(operations, stage, held):
            seen.append(self.reader._connection.in_transaction)
            raise broken

        delegation.observation_of = failing
        self.addCleanup(setattr, delegation, "observation_of", real)
        with self.assertRaises(ContractRefusal) as caught:
            status(self.reader, self.acts, observed_at=LATER)
        self.assertEqual(caught.exception.code, "transport")
        self.assertEqual(seen, [False])
        self.assertFalse(self.reader._connection.in_transaction)
        # AND THE READER IS STILL USABLE afterwards, which a leaked boundary
        # on a `mode=ro` connection would not leave it.
        self.assertFalse(self.jobs._connection.in_transaction)

    def test_the_materialization_cannot_reach_another_store_at_all(self):
        """The enforcement is structural rather than a comment: the function
        that holds the read view is handed no `operations`."""
        import inspect

        self.assertEqual(
            list(inspect.signature(projection.materialized).parameters),
            ["store", "stages"])

    def test_the_read_view_is_released_even_when_the_body_raises(self):
        submit(self.jobs, submission())
        with self.assertRaises(KeyError):
            with self.reader.read_snapshot():
                self.assertTrue(self.reader._connection.in_transaction)
                raise KeyError("the body's own failure")
        self.assertFalse(self.reader._connection.in_transaction)

    def test_a_caller_s_own_boundary_is_neither_nested_nor_ended(self):
        """SQLite has no nested transactions, and ending one here would commit
        or discard a decision this read had nothing to do with."""
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.addCleanup(lambda: self.jobs._connection.in_transaction
                        and self.jobs._connection.execute("ROLLBACK"))
        with self.jobs.read_snapshot():
            self.assertTrue(self.jobs._connection.in_transaction)
        self.assertTrue(self.jobs._connection.in_transaction)

    # -- and the ordinary readings, unchanged ---------------------------------

    def test_an_empty_store_still_reads_empty_through_the_reader(self):
        self.assertEqual(status(self.reader, self.acts,
                                observed_at=NOW)["jobs"], [])

    def test_a_populated_store_reads_the_same_through_both_handles(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        # EVERY MEMBER BUT THE INCARNATION, which names the handle that did
        # the reading and is legitimately different.
        self.assertEqual(status(self.reader, self.acts,
                                observed_at=LATER)["jobs"],
                         status(self.jobs, self.acts,
                                observed_at=LATER)["jobs"])
        self.assertEqual(self.states(status(self.reader, self.acts,
                                            observed_at=LATER)),
                         {"job-a/implementation": "offered",
                          "job-a/review": "blocked",
                          "job-b/implementation": "offered"})

    def test_reading_through_the_read_only_handle_changes_no_row(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        before = self.dump()
        for _ in range(3):
            status(self.reader, self.acts, observed_at=LATER)
            projection.stage_states(self.reader, self.acts)
        self.assertEqual(self.dump(), before)

    def test_the_whole_status_shape_survives_the_new_boundary(self):
        """The document's contract is closed, so the composition is compared
        member by member against the one the serving handle produces."""
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)
        document = status(self.reader, self.acts, observed_at=LATER)
        self.assertEqual(document["schema"], STATUS_SCHEMA)
        one = self.stage_of(document, "job-a/implementation")
        self.assertEqual(
            sorted(one),
            sorted(self.stage_of(status(self.jobs, self.acts,
                                        observed_at=LATER),
                                 "job-a/implementation")))
        self.assertEqual(one["allocations"], [])
        self.assertIsNone(one["allocation"])
        self.assertEqual([record["act"] for record in one["receipts"]],
                         ["admit"])

    def test_the_authority_and_schema_checks_still_guard_the_reader(self):
        """The new boundary is not a way around the opener's proofs."""
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open_readonly(self.job_path, authority_uuid="f" * 32,
                                   incarnation="jobs-monitor",
                                   clock=self.clock)
        self.assertEqual(caught.exception.category, "refused")


class ObservingInsideACallersBoundary(StatusCase):
    """W319114 (correction) -- a derivation that would OBSERVE refuses.

    WHAT THE FIRST PASS LEFT OPEN. `materialized` takes one read view of this
    database and releases it before a single observation, which is the whole
    two-phase shape -- for a caller that owns no transaction of its own.
    `read_snapshot` deliberately does NOT touch a caller's existing boundary:
    SQLite has no nested transactions and ending somebody else's would commit
    or discard a decision this read had nothing to do with. So inside

        with store.read_snapshot():
            projection.status(store, operations, observed_at=NOW)

    the view is the caller's, it is still open when `materialized` returns,
    and `stage_states` then asked the Worker Manager for an observation per
    live stage with a Job-store transaction HELD. Measured: three external
    observations with `in_transaction` true, through the public API, with no
    raw SQL and no hostile store. DB-1 forbids external I/O under a
    transaction and DB-4 forbids calling another store while retaining this
    one's, so that is the accepted outcome violated from the one direction
    the boundary could not close by itself.

    WHAT THESE CASES ESTABLISH, AND WHY THEY RECORD STATES. A case that only
    asserts "a refusal was raised" would pass just as well against a build
    that observed three times and then refused, which is the thing being
    excluded. So each one wraps `delegation.observation_of`, records
    `in_transaction` AT EVERY CALL, and asserts the recorded list contains no
    `True` -- the exclusion itself, not a proxy for it.

    AND THE CALLER'S TRANSACTION IS NOT THE PRICE. Refusing by committing or
    rolling back somebody else's boundary would be the same defect with a
    tidier symptom: their work would be decided by a read-only derivation
    that was never asked to decide it. It is left exactly as it was found,
    open and pending.
    """

    def setUp(self):
        super().setUp()
        self.reader = JobStore.open_readonly(
            self.job_path, authority_uuid=UUID, incarnation="jobs-monitor",
            clock=self.clock)
        self.addCleanup(self.reader.close)

    def watched(self, store):
        """Record `in_transaction` at EVERY observation, and keep observing.

        The real `observation_of` still runs, so a build that does not refuse
        reaches its ordinary answer and the recorded states are what it
        actually did rather than what a stub made it do.
        """
        seen = []
        real = delegation.observation_of

        def recording(operations, stage, held):
            seen.append(store._connection.in_transaction)
            return real(operations, stage, held)

        delegation.observation_of = recording
        self.addCleanup(setattr, delegation, "observation_of", real)
        return seen

    def populated(self):
        submit(self.jobs, submission())
        sweep(self.jobs, self.acts, now=NOW)

    def held(self, store):
        """Open the caller's OWN boundary and guarantee it is ended here."""
        self.addCleanup(lambda: store._connection.in_transaction
                        and store._connection.execute("ROLLBACK"))

    # -- 1. the behavioural exclusion -----------------------------------------

    def test_a_status_inside_the_callers_own_read_view_observes_NOTHING(self):
        """The measured case, asserted by what the other store was asked."""
        self.populated()
        seen = self.watched(self.reader)
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                status(self.reader, self.acts, observed_at=LATER)
            # AND THE CALLER'S VIEW IS UNTOUCHED, still open around the
            # refusal that was raised inside it.
            self.assertTrue(self.reader._connection.in_transaction)
        # NO OBSERVATION RAN AT ALL, and none ran under a transaction. The
        # second assertion is the rule; the first is how this build keeps it.
        self.assertEqual(seen, [])
        self.assertNotIn(True, seen)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))

    def test_the_refusal_names_what_was_done_and_what_to_do_instead(self):
        self.populated()
        self.held(self.jobs)
        with self.jobs.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                status(self.jobs, self.acts, observed_at=LATER)
        said = str(caught.exception)
        self.assertIn("a status document", said)
        self.assertIn("still holds that store's own transaction", said)
        self.assertIn("'jobs-1'", said)
        self.assertIn("DB-1", said)
        self.assertIn("DB-4", said)
        self.assertIn("read_snapshot", said)
        self.assertIn("projection.materialized", said)
        self.assertIn("No observation was attempted", said)
        self.assertIn("nothing was changed", said)

    def test_the_SAME_status_succeeds_once_the_boundary_is_released(self):
        """The refusal is about WHEN it was asked, and says so by being
        transient: the identical call one line later answers in full."""
        self.populated()
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal):
                status(self.reader, self.acts, observed_at=LATER)
        seen = self.watched(self.reader)
        document = status(self.reader, self.acts, observed_at=LATER)
        self.assertEqual(self.states(document),
                         {"job-a/implementation": "offered",
                          "job-a/review": "blocked",
                          "job-b/implementation": "offered"})
        self.assertNotIn(True, seen)
        self.assertEqual(set(seen), {False})

    # -- 2. the caller's work survives ----------------------------------------

    def test_the_callers_transaction_is_still_open_and_still_PENDING(self):
        """Neither committed nor discarded. The refusal decides nothing about
        a boundary it did not open."""
        self.populated()
        seen = self.watched(self.jobs)
        self.held(self.jobs)
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.jobs._connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("w319114-pending", "the caller's own uncommitted change"))
        with self.assertRaises(ContractRefusal):
            status(self.jobs, self.acts, observed_at=LATER)
        self.assertEqual(seen, [])
        # STILL OPEN.
        self.assertTrue(self.jobs._connection.in_transaction)
        # STILL PENDING, WHICH IS TWO FACTS. The caller's own connection can
        # still see its change -- so nothing discarded it -- and no other
        # connection can -- so nothing committed it.
        self.assertEqual(self.pending_rows(self.jobs), 1)
        self.assertEqual(self.pending_rows(self.reader), 0)
        # AND THE CALLER STILL DECIDES. Rolling back is the caller's act, and
        # it leaves the store exactly as a discarded change should.
        self.jobs._connection.execute("ROLLBACK")
        self.assertEqual(self.pending_rows(self.jobs), 0)

    def test_the_callers_transaction_can_still_be_COMMITTED_afterwards(self):
        """The other half: a caller that meant to keep its change keeps it."""
        self.held(self.jobs)
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.jobs._connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("w319114-pending", "kept"))
        with self.assertRaises(ContractRefusal):
            status(self.jobs, self.acts, observed_at=LATER)
        self.jobs._connection.execute("COMMIT")
        self.assertEqual(self.pending_rows(self.reader), 1)

    def pending_rows(self, store):
        return store._connection.execute(
            "SELECT count(*) FROM meta WHERE key = ?",
            ("w319114-pending",)).fetchone()[0]

    # -- 3. the standalone derivation holds the same line ---------------------

    def test_stage_states_called_from_inside_a_boundary_refuses_too(self):
        """`stage_states` is the pass the sweep and the owed-act derivation
        come through, and it observes whether or not a status asked it to."""
        self.populated()
        seen = self.watched(self.reader)
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                projection.stage_states(self.reader, self.acts)
            # STILL INSIDE THE CALLER'S OWN BOUNDARY: the refusal did not end
            # the read view it was raised under.
            self.assertTrue(self.reader._connection.in_transaction)
        self.assertEqual(seen, [])
        self.assertNotIn(True, seen)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("a stage-state derivation", str(caught.exception))
        self.assertFalse(self.reader._connection.in_transaction)

    def test_stage_states_leaves_the_writers_pending_change_alone_too(self):
        self.populated()
        self.held(self.jobs)
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.jobs._connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("w319114-pending", "the caller's own uncommitted change"))
        with self.assertRaises(ContractRefusal):
            projection.stage_states(self.jobs, self.acts)
        self.assertTrue(self.jobs._connection.in_transaction)
        self.assertEqual(self.pending_rows(self.jobs), 1)
        self.assertEqual(self.pending_rows(self.reader), 0)

    # -- 4. the failure paths -------------------------------------------------

    def test_an_EMPTY_store_refuses_identically(self):
        """Nothing to observe is not the same as nothing to refuse. A check
        placed inside the per-stage loop would pass this case by doing
        nothing, and the next populated caller would observe under the
        boundary again."""
        seen = self.watched(self.reader)
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                status(self.reader, self.acts, observed_at=NOW)
            with self.assertRaises(ContractRefusal):
                projection.stage_states(self.reader, self.acts)
        self.assertEqual(seen, [])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))

    def test_an_observation_that_would_itself_FAIL_is_never_attempted(self):
        """The point is not which refusal wins. It is that the external read
        does not happen: a build that observed and then reported the
        observation's own failure would have performed exactly the I/O DB-1
        forbids, and would look like a transport problem while doing it."""
        self.populated()
        attempts = []
        real = delegation.observation_of

        def exploding(operations, stage, held):
            attempts.append(self.reader._connection.in_transaction)
            raise ContractRefusal("unavailable", "transport",
                                  "the canonical store could not be read")

        delegation.observation_of = exploding
        self.addCleanup(setattr, delegation, "observation_of", real)
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                status(self.reader, self.acts, observed_at=LATER)
        self.assertEqual(attempts, [])
        self.assertEqual(caught.exception.code, "precondition")
        self.assertNotIn("could not be read", str(caught.exception))

    def test_an_UNOBSERVED_derivation_refuses_on_the_same_rule(self):
        """`Unobserved` performs no I/O, so this one is about the rule rather
        than the measured harm: the derivation refuses on WHAT IT WOULD DO,
        decided before the handle it would do it through is consulted. A
        check that asked the operations handle first would be a second place
        for the boundary rule to be got wrong."""
        self.populated()
        self.held(self.reader)
        with self.reader.read_snapshot():
            with self.assertRaises(ContractRefusal) as caught:
                status(self.reader, Unobserved(), observed_at=LATER)
        self.assertEqual(caught.exception.code, "precondition")

    # -- what stays legitimate inside a caller's boundary ----------------------

    def test_materialized_is_STILL_served_inside_the_callers_boundary(self):
        """The refusal is scoped to the passes that go on to observe.
        `materialized` reads only this store's own rows and takes no
        `operations` handle, which is exactly what DB-1 permits under a
        transaction -- so narrowing it here too would have cost a legitimate
        read to fix an illegitimate one."""
        self.populated()
        self.held(self.reader)
        with self.reader.read_snapshot():
            snapshot = projection.materialized(self.reader)
        self.assertEqual(sorted(snapshot["owned"]),
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        self.assertEqual(sorted(one["job_id"] for one in snapshot["jobs"]),
                         ["job-a", "job-b"])

    def test_the_question_itself_is_the_stores_own_and_is_public(self):
        """`holds_transaction` is asked of the owner rather than read off its
        connection: DB-6 makes the public owner API the boundary, and a
        reader reaching into `_connection` would be a second account of a
        fact this store already owns."""
        self.assertFalse(self.jobs.holds_transaction())
        self.held(self.jobs)
        self.jobs._connection.execute("BEGIN IMMEDIATE")
        self.assertTrue(self.jobs.holds_transaction())
        self.jobs._connection.execute("ROLLBACK")
        self.assertFalse(self.jobs.holds_transaction())
        # AND A READ TRANSACTION COUNTS, which is the case DB-1 says is not an
        # escape from the rule.
        with self.reader.read_snapshot():
            self.assertTrue(self.reader.holds_transaction())
        self.assertFalse(self.reader.holds_transaction())

    # -- the bounded secondary item -------------------------------------------

    def test_a_CLOSED_handle_reports_this_distributions_refusal(self):
        """`read_snapshot` asked `in_transaction` ahead of its own `try`, so a
        closed handle raised a raw `sqlite3.ProgrammingError` and a caller got
        the driver's vocabulary for a condition DB-6 names a typed refusal.
        The same guard that asks the boundary question answers this one."""
        closed = JobStore.open_readonly(
            self.job_path, authority_uuid=UUID, incarnation="jobs-closed",
            clock=self.clock)
        closed.close()
        with self.assertRaises(ContractRefusal) as caught:
            with closed.read_snapshot():
                raise AssertionError("the body must not run")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("'jobs-closed'", str(caught.exception))
        self.assertIn("is closed", str(caught.exception))
        self.assertIn("nothing was changed", str(caught.exception))
