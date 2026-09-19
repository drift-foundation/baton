"""W71875 — deriving the next act from persisted state, and delegating it once.

WHAT ORDINARY SUCCESS LOOKS LIKE: an operator submits, and every act after
that is derived. These cases drive `sweep` and assert which acts it decided
were owed, that each was delegated exactly once, and that a receipt naming the
canonical operation was written for it.

WHAT IT MUST NOT DO IS AS IMPORTANT. A blocked stage is not admitted; a
claimed stage owes nothing further here; a stage whose predecessor ended in
changes-requested or exceptional stays blocked rather than being pushed
through; and an ordinary refusal leaves the act owed instead of recording one.
"""

import json
import subprocess
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, RefreshUnavailable, owed_acts,
                                   receipt_rows, receipts_of, status, sweep,
                                   submit)
from baton_v12.job_manager import episodes, manager, projection
from baton_v12.job_manager.episodes import identities

if __package__:
    from .fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase, job,
                           stage, submission)
else:
    from fixtures import (LATER, NOW, UUID, FakeOperations, JobManagerCase, job,
                          stage, submission)


class SweepCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        self.acts = FakeOperations()

    def submit(self, document=None):
        return submit(self.jobs, document if document is not None
                      else submission())

    def outcomes(self, report):
        return [(one["stage_id"], one["act"], one["outcome"])
                for one in report["acts"]]

    @staticmethod
    def gated_job():
        """One Job whose review stage gates on its implementation.

        A case about ONE gate uses one Job, so a second Job's ordinary
        progress cannot be mistaken for the gate opening.
        """
        return job("job-a", stages=[
            stage("implementation"),
            stage("review", depends_on=[{"job_id": "job-a",
                                         "kind": "implementation"}])])


class Eligibility(SweepCase):

    def test_only_ungated_stages_are_admitted_on_the_first_sweep(self):
        self.submit()
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(
            self.outcomes(report),
            [("job-a/implementation", "admit", "performed"),
             ("job-b/implementation", "admit", "performed")])
        # THE REVIEW STAGE IS GATED and is not offered. A scheduler that
        # admitted it would authorize a reviewer for a checkpoint that does
        # not exist yet.
        self.assertNotIn("job-a/review", [one[0] for one in self.acts.calls])

    def test_two_independent_jobs_are_admitted_from_one_submission(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(sorted(self.acts.calls),
                         [("admit", "job-a/implementation"),
                          ("admit", "job-b/implementation")])

    def test_a_gate_opens_only_on_a_completed_predecessor(self):
        self.submit(submission(jobs=[self.gated_job()]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.frozen("job-a/implementation", "completed")
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(self.outcomes(report),
                         [("job-a/review", "admit", "performed")])

    def test_a_changes_requested_predecessor_leaves_its_successor_blocked(self):
        # The same-line correction cycle is W71918's. This leaf reports the
        # gate as closed rather than reopening it or pretending it opened.
        document = submission(jobs=[job("job-a", stages=[
            stage("review"),
            stage("integration", depends_on=[{"job_id": "job-a",
                                              "kind": "review"}])])])
        submit(self.jobs, document)
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.frozen("job-a/review", "plan-rejected")
        self.assertEqual(sweep(self.jobs, self.acts, now=LATER)["acts"], [])

    def test_an_unable_predecessor_leaves_its_successor_blocked(self):
        self.submit(submission(jobs=[self.gated_job()]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.frozen("job-a/implementation", "unable")
        self.assertEqual(sweep(self.jobs, self.acts, now=LATER)["acts"], [])

    def test_an_empty_store_owes_nothing(self):
        self.assertEqual(sweep(self.jobs, self.acts, now=NOW)["acts"], [])
        self.assertEqual(owed_acts(self.jobs, self.acts), [])


class Delegation(SweepCase):

    def test_an_admitted_stage_owes_its_claim_next(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        # The fake's journal now holds the admit, so the next sweep derives
        # the claim from the receipt rather than from anything remembered.
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(
            self.outcomes(report),
            [("job-a/implementation", "claim", "performed"),
             ("job-b/implementation", "claim", "performed")])

    def test_a_claimed_stage_owes_nothing_further_from_this_leaf(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=LATER)
        self.acts.observed("job-a/implementation", claimed_by=True)
        self.acts.observed("job-b/implementation", claimed_by=True)
        self.assertEqual(sweep(self.jobs, self.acts, now=LATER)["acts"], [])

    def test_the_receipt_names_the_canonical_operation(self):
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        held = receipts_of(self.jobs, "job-a/implementation", 1)
        self.assertEqual(sorted(held), ["admit"])
        self.assertEqual(held["admit"]["operation_id"],
                         "offer.issue:" + identities(UUID, "job-a/implementation", 1)[0])
        self.assertEqual(held["admit"]["state"], "performed")
        self.assertEqual(held["admit"]["incarnation"], "jobs-1")

    def test_one_act_is_delegated_once_however_often_the_loop_ticks(self):
        self.submit()
        for _ in range(4):
            sweep(self.jobs, self.acts, now=NOW)
        # THE JOURNALLED ACTS, once each. W76207 added a third call to this
        # surface, so the assertion names the two acts this leaf keeps
        # RECEIPTS for rather than every call the fake saw -- the receipt is
        # what makes them once-only, and it is what this case is about.
        self.assertEqual(
            sorted(one for one in self.acts.calls
                   if one[0] in ("admit", "claim")),
            [("admit", "job-a/implementation"),
             ("admit", "job-b/implementation"),
             ("claim", "job-a/implementation"),
             ("claim", "job-b/implementation")])

    def test_the_launch_is_asked_every_tick_and_never_receipted(self):
        """W76207: the third call is LEVEL-TRIGGERED, and that is the point.

        `admit` and `claim` happen once because a receipt says they did. A
        launch has no receipt here -- the Worker Manager journals the start
        under its own derived identity -- so this leaf asks again on every
        tick until canonical state says the runtime is up. That is what makes
        the first tick after a restart behave exactly like any other, which is
        the crash window the whole seam exists for.
        """
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)
        # Both stages are claimed by now, so both are asked, every tick.
        for _ in range(3):
            before = len([one for one in self.acts.calls
                          if one[0] == "launch"])
            sweep(self.jobs, self.acts, now=NOW)
            after = len([one for one in self.acts.calls
                         if one[0] == "launch"])
            self.assertEqual(after - before, 2)
        # AND NOTHING WAS RECEIPTED FOR IT. The two acts this leaf owns are
        # still the only rows in its store.
        self.assertEqual(sorted({row["act"] for row in
                                 receipt_rows(self.jobs)}),
                         ["admit", "claim"])


class Refusals(SweepCase):

    def test_an_ordinary_refusal_defers_the_act_and_records_nothing(self):
        # `submit_claim` refuses an offer the worker has not accepted yet.
        # That is the honest state of the world, not a failure to record.
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim",
                         ContractRefusal("refused", "precondition",
                                         "offer job-a is not accepted"))
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(self.outcomes(report),
                         [("job-a/implementation", "claim", "deferred")])
        self.assertEqual(report["acts"][0]["detail"]["code"], "precondition")
        self.assertEqual(sorted(receipts_of(self.jobs,
                                            "job-a/implementation", 1)),
                         ["admit"])
        # AND IT IS STILL OWED. The next tick asks again.
        self.assertEqual(self.outcomes(sweep(self.jobs, self.acts, now=LATER)),
                         [("job-a/implementation", "claim", "performed")])

    def test_a_durable_refusal_is_recorded_and_makes_the_stage_exceptional(self):
        self.submit(submission(jobs=[job("job-a")]))
        self.acts.refuse("job-a/implementation", "admit",
                         ContractRefusal("policy", "profile-uncertified",
                                         "nothing certifies it", durable=True))
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(self.outcomes(report),
                         [("job-a/implementation", "admit", "refused")])
        held = receipts_of(self.jobs, "job-a/implementation", 1)
        self.assertEqual(held["admit"]["state"], "refused")
        # AND THE STAGE STOPS. A settled refusal is a condition an operator
        # sees rather than something to keep sweeping past.
        self.assertEqual(sweep(self.jobs, self.acts, now=LATER)["acts"], [])

    def test_an_act_the_manager_journals_under_no_derived_identity_refuses(self):
        # If the manager ever changed how it spells its operation identity,
        # every sweep would repeat a committed act. Refusing here is the only
        # answer that does not silently start re-issuing offers.
        class Silent(FakeOperations):
            def admit(self, stage, job):
                self.calls.append(("admit", stage["stage_id"]))
                return None

        self.submit(submission(jobs=[job("job-a")]))
        with self.assertRaises(ContractRefusal) as caught:
            sweep(self.jobs, Silent(), now=NOW)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))


class ADeferredActSaysWHYAndForWHICHAttempt(SweepCase):
    """W197661, owner ruling seq199199's visibility half.

    THE DEFECT THIS CLOSES. `Refusals.test_an_ordinary_refusal_defers_the_act
    _and_records_nothing` above is still correct about receipts: a deferral is
    NOT one. But "records nothing" was also literally true of the REASON, and
    that is what an operator needed. A real deployment sat at `answering` for a
    whole incident with a healthy manager, a fresh snapshot and one observed
    Job, and the only account of why was a reconcile report nobody had kept.

    AND IT IS NOT TERMINAL. `projection` reads a durably REFUSED receipt as
    `exceptional`; a deferral is re-enterable and must never be read that way,
    which is why it is its own relation rather than a widened receipt.
    """

    REASON = ContractRefusal("refused", "precondition",
                             "offer job-a is not accepted")

    LATEST = "2026-09-02T00:10:00.000Z"

    def at(self, instant):
        """The STORE's clock, which is what stamps a durable write. `now=` is
        the sweep's own operand and does not decide when a row was recorded."""
        self.instants.append(instant)

    def deferring(self, act="claim"):
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", act, self.REASON)
        self.at(LATER)
        return sweep(self.jobs, self.acts, now=LATER)

    def held(self):
        """Every outstanding reason for this stage, whichever episode owed it."""
        return projection.deferral_of(self.jobs, "job-a/implementation")

    def test_the_reason_and_the_exact_attempt_are_DURABLE(self):
        self.deferring()
        found = self.held()
        self.assertEqual(len(found), 1)
        one = found[0]
        self.assertEqual(one["act"], "claim")
        self.assertEqual(one["category"], "refused")
        self.assertEqual(one["code"], "precondition")
        self.assertIn("is not accepted", one["message"])
        # THE HALF THE OWNER ASKED FOR BY NAME: a reason without a subject is
        # not actionable.
        self.assertEqual(
            one["attempt_id"],
            projection.stage_states(self.jobs, self.acts)
            ["job-a/implementation"]["episode"]["attempt_id"])

    def test_it_is_NOT_a_receipt(self):
        self.deferring()
        self.assertEqual(sorted(receipts_of(self.jobs,
                                            "job-a/implementation", 1)),
                         ["admit"])

    def test_the_stage_is_NOT_made_exceptional_by_it(self):
        """The whole reason this is not a widened receipt."""
        self.deferring()
        held = projection.stage_states(self.jobs, self.acts)
        self.assertNotEqual(held["job-a/implementation"]["state"],
                            "exceptional")

    def test_repeating_keeps_ONE_row_and_advances_only_what_it_observed(self):
        """A deferral repeats on every tick. A row per occurrence would be an
        unbounded durable write driven by a condition that is not changing."""
        self.deferring()
        first = self.held()[0]
        self.at(self.LATEST)
        for _ in range(3):
            # RE-ARMED EACH TICK, because the fake refuses once and the
            # condition this is about is one that keeps recurring. A loop that
            # let it succeed would be measuring resolution, not repetition.
            self.acts.refuse("job-a/implementation", "claim", self.REASON)
            sweep(self.jobs, self.acts, now=self.LATEST)
        found = self.held()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["since"], first["since"])
        self.assertEqual(found[0]["observed"], self.LATEST)
        self.assertNotEqual(found[0]["observed"], found[0]["since"])

    def test_a_SETTLED_act_leaves_no_outstanding_reason(self):
        """A reason left behind after its act succeeded would be worse than
        none: an operator would be reading a live explanation of something
        that is over."""
        self.deferring()
        self.assertIsNotNone(self.held())
        self.assertEqual(self.outcomes(sweep(self.jobs, self.acts, now=LATER)),
                         [("job-a/implementation", "claim", "performed")])
        self.assertIsNone(self.held())

    def test_it_SURVIVES_a_restart_of_the_manager(self):
        """The reason has to outlive the process that observed it, or an
        operator arriving after a crash is exactly where they were before."""
        self.deferring()
        before = self.held()
        self.jobs.close()
        self.jobs = JobStore.open(self.job_path, authority_uuid=UUID,
                                  incarnation="jobs-after-restart",
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.assertEqual(self.held(), before)

    def test_the_status_document_carries_it_beside_the_state(self):
        """The acceptance in the review's own words: the reason and the exact
        attempt, without direct store or Docker inspection."""
        self.deferring()
        document = projection.status(self.jobs, self.acts,
                                     observed_at=self.LATEST)
        stage = [one for one in document["jobs"][0]["stages"]
                 if one["stage_id"] == "job-a/implementation"][0]
        self.assertEqual(len(stage["deferral"]), 1)
        self.assertEqual(stage["deferral"][0]["code"], "precondition")
        self.assertEqual(stage["deferral"][0]["attempt_id"],
                         stage["attempt_id"])
        self.assertNotEqual(stage["state"], "exceptional")

    def test_a_stage_with_nothing_outstanding_says_NULL(self):
        """Which is a different answer from a stage nobody has asked to do
        anything, and both are different from an empty list."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        document = projection.status(self.jobs, self.acts, observed_at=NOW)
        for one in document["jobs"][0]["stages"]:
            self.assertIsNone(one["deferral"])

    def test_a_DURABLE_refusal_records_a_receipt_and_no_deferral(self):
        """The two are different answers and must not be conflated: one is
        settled and terminal, the other is outstanding and re-enterable."""
        self.submit(submission(jobs=[job("job-a")]))
        self.acts.refuse("job-a/implementation", "admit",
                         ContractRefusal("policy", "profile-uncertified",
                                         "nothing certifies it", durable=True))
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(
            receipts_of(self.jobs, "job-a/implementation", 1)["admit"]
            ["state"], "refused")
        self.assertIsNone(self.held())


class ADeferredFINALIZATIONIsVisibleToo(SweepCase):
    """W197661 review 2026-09-18T02-59-56Z [R1], and it is the defect this
    whole visibility was selected FOR.

    I wired `_defer` into `_delegate`, whose acts are `admit` and `claim`. The
    owner selected this for a deferred `conclude` -- which goes through
    `_converse` and `_recover_endings` -- so the reviewer's probe still found
    `answering` with `deferral: null` for the exact attempt whose finalization
    was blocked, and my "R2a DONE" was wrong about the half that mattered.
    """

    REASON = ContractRefusal("refused", "precondition",
                             "synthetic finalization blocked after intake")

    def answering(self):
        """One stage whose worker answered and whose ending is owed."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"runtime_id": "runtime-1",
                                    "execution_runtime": "quiescent"},
                           exchange={"state": "answered"})
        return "job-a/implementation"

    def held(self):
        return projection.deferral_of(self.jobs, "job-a/implementation")

    def stage(self, observed_at=NOW):
        document = projection.status(self.jobs, self.acts,
                                     observed_at=observed_at)
        return [one for one in document["jobs"][0]["stages"]
                if one["stage_id"] == "job-a/implementation"][0]

    def test_a_deferred_CONCLUDE_is_recorded_with_its_exact_attempt(self):
        stage_id = self.answering()
        self.acts.refuse(stage_id, "conclude", self.REASON)
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertIn(("conclude", "deferred"),
                      [(one["act"], one["outcome"])
                       for one in report.get("spoken", [])])
        found = self.held()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["act"], "conclude")
        # THE FAKE'S OWN REFUSAL, whatever it says: what this case is about
              # is that the PATH records one, not which prose it carries.
        self.assertTrue(found[0]["message"])
        self.assertIsNone(found[0]["operation_id"])

    def test_the_STATUS_SURFACE_no_longer_says_answering_with_nothing(self):
        """The reviewer's probe, asserted: `answering` with `deferral: null`
        for the exact attempt whose finalization was blocked."""
        stage_id = self.answering()
        self.acts.refuse(stage_id, "conclude", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        found = self.stage(observed_at=LATER)
        self.assertEqual(found["state"], "answering")
        self.assertIsNotNone(found["deferral"])
        self.assertEqual(found["deferral"][0]["act"], "conclude")
        self.assertEqual(found["deferral"][0]["attempt_id"],
                         found["attempt_id"])
        # AND IT IS STILL NOT TERMINAL. A re-enterable condition reported as
        # `exceptional` would be a worse falsehood than the silence.
        self.assertNotEqual(found["state"], "exceptional")

    def test_a_SUCCEEDING_conclude_clears_the_reason(self):
        stage_id = self.answering()
        self.acts.refuse(stage_id, "conclude", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        self.assertIsNotNone(self.held())
        # THE FAKE IS GIVEN AN ENDING, so the next tick's conclude SUCCEEDS.
        # Its default is a refusal, which is honest -- a deployment given no
        # conclude cannot end anything -- and would have made this case
        # measure the refusal path twice.
        self.acts.endings[stage_id] = {"ended": True}
        sweep(self.jobs, self.acts, now=LATER)
        self.assertIsNone(self.held())
        self.assertIsNone(self.stage(observed_at=LATER)["deferral"])

    def test_a_REPEATED_refusal_keeps_one_row_and_advances_observed(self):
        stage_id = self.answering()
        self.acts.refuse(stage_id, "conclude", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        first = self.held()[0]
        self.instants.append(self.LATEST)
        for _ in range(3):
            self.acts.refuse(stage_id, "conclude", self.REASON)
            sweep(self.jobs, self.acts, now=self.LATEST)
        found = self.held()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["since"], first["since"])
        self.assertEqual(found[0]["observed"], self.LATEST)

    def test_it_SURVIVES_a_restart(self):
        stage_id = self.answering()
        self.acts.refuse(stage_id, "conclude", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        before = self.held()
        self.jobs.close()
        self.jobs = JobStore.open(self.job_path, authority_uuid=UUID,
                                  incarnation="jobs-after-restart",
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.assertEqual(self.held(), before)

    LATEST = "2026-09-02T00:10:00.000Z"


class AFailureToRecordTheREASONIsNotASuccess(SweepCase):
    """Review [R2]: blanket exception swallowing made failed persistence
    indistinguishable from success -- an evidence surface that silently has no
    evidence, which is the class of defect this Work exists to remove."""

    REASON = ContractRefusal("refused", "precondition", "offer not accepted")

    def test_a_deferral_that_could_not_be_written_SAYS_SO(self):
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim", self.REASON)
        self.jobs._connection.execute("DROP TABLE deferrals")
        report = sweep(self.jobs, self.acts, now=LATER)
        detail = report["acts"][0]["detail"]
        self.assertEqual(detail["code"], "precondition")
        self.assertFalse(detail["evidence"]["recorded"])
        self.assertIn("could not be recorded", detail["evidence"]["why"])

    def test_an_ORDINARY_deferral_adds_no_evidence_noise(self):
        """The report is about the ACT. A line saying the note was filed would
        be noise on every tick."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim", self.REASON)
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertNotIn("evidence", report["acts"][0]["detail"])

    def test_a_FAILED_CLEAR_is_reported_rather_than_left_to_mislead(self):
        """A reason left behind because the DELETE failed would present a
        settled act as outstanding."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        self.jobs._connection.execute("DROP TABLE deferrals")
        report = sweep(self.jobs, self.acts, now=LATER)
        detail = report["acts"][0]["detail"] or {}
        self.assertFalse(detail["evidence"]["cleared"])
        self.assertIn("may still be reported as outstanding",
                      detail["evidence"]["why"])

    def test_the_STAGE_is_unaffected_by_an_evidence_failure(self):
        """Evidence failure is kept separate from execution state."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim", self.REASON)
        self.jobs._connection.execute("DROP TABLE deferrals")
        sweep(self.jobs, self.acts, now=LATER)
        held = projection.stage_states(self.jobs, self.acts)
        self.assertNotEqual(held["job-a/implementation"]["state"],
                            "exceptional")


class ARETAINEDReasonIsNotAnOUTSTANDINGOne(SweepCase):
    """Review 2026-09-18T03-18-24Z [3], and my previous case did not prove it.

    `_resolve` deletes the row when the act settles. A DELETE that FAILED left
    it behind, and the status reader called every stored row outstanding -- so
    a settled act's retained reason was presented as a live condition. My
    earlier case dropped the TABLE, which proves the reconcile report says so
    and proves nothing at all about the operator surface, because with the
    table gone there is no row to read.

    THE CASE THAT ACTUALLY PROVES IT leaves the row READABLE and settles the
    act, which is the state an operator would really meet.
    """

    REASON = ContractRefusal("refused", "precondition", "offer not accepted")

    def stage(self):
        document = projection.status(self.jobs, self.acts, observed_at=LATER)
        return [one for one in document["jobs"][0]["stages"]
                if one["stage_id"] == "job-a/implementation"][0]

    def test_a_settled_act_whose_row_SURVIVED_is_marked_RETAINED(self):
        from unittest import mock

        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refuse("job-a/implementation", "claim", self.REASON)
        sweep(self.jobs, self.acts, now=LATER)
        held = self.stage()["deferral"]
        self.assertTrue(held[0]["outstanding"])
        self.assertIsNone(held[0]["why_retained"])
        # THE CLEAR FAILS AND THE ROW STAYS READABLE, which is the state the
        # previous case could not produce.
        with mock.patch.object(manager, "_resolve",
                               lambda store, owed: {"cleared": False,
                                                    "why": "it did not"}):
            sweep(self.jobs, self.acts, now=LATER)
        found = self.stage()["deferral"]
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0]["outstanding"])
        self.assertIn("retained evidence rather than an outstanding",
                      found[0]["why_retained"])
        # AND THE STAGE MOVED ON, which is what makes the row stale.
        self.assertEqual(
            sorted(receipts_of(self.jobs, "job-a/implementation", 1)),
            ["admit", "claim"])

    def test_an_OLDER_pending_ending_is_reported_and_attributed(self):
        """`_recover_endings` services endings registered by a prior episode,
        and a reader bound to the live episode would hide them."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        # A DEFERRAL RECORDED FOR AN EARLIER EPISODE, the way
        # `_recover_endings` records one.
        manager._defer(
            self.jobs,
            {"stage_id": "job-a/implementation", "episode": 1,
             "act": "conclude", "attempt_id": "attempt-older"},
            {"category": "refused", "code": "precondition",
             "message": "an older ending never settled"})
        found = self.stage()["deferral"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["act"], "conclude")
        self.assertEqual(found[0]["episode"], 1)
        self.assertEqual(found[0]["attempt_id"], "attempt-older")
        # OUTSTANDING, because nothing has settled that ending.
        self.assertTrue(found[0]["outstanding"])

    def test_an_UNREGISTERED_conclude_reason_stays_OUTSTANDING(self):
        """`conclude` writes no receipt, so what settles it is a REGISTERED
        ending that is no longer pending. A first cut of that rule read
        "nothing is pending" as settlement -- which quietly calls an
        outstanding condition over whenever no ending was ever registered.
        The safe direction is this one."""
        self.submit(submission(jobs=[job("job-a")]))
        sweep(self.jobs, self.acts, now=NOW)
        manager._defer(
            self.jobs,
            {"stage_id": "job-a/implementation", "episode": 1,
             "act": "conclude", "attempt_id": "attempt-never-registered"},
            {"category": "refused", "code": "precondition",
             "message": "no ending was ever registered for this"})
        found = self.stage()["deferral"]
        self.assertTrue(found[0]["outstanding"])
        self.assertIsNone(found[0]["why_retained"])


class Containment(SweepCase):

    def test_one_job_s_durable_refusal_does_not_hold_up_another(self):
        self.submit()
        self.acts.refuse("job-a/implementation", "admit",
                         ContractRefusal("policy", "profile-uncertified",
                                         "nothing certifies it", durable=True))
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(
            self.outcomes(report),
            [("job-a/implementation", "admit", "refused"),
             ("job-b/implementation", "admit", "performed")])
        # AND THE UNRELATED JOB KEEPS MOVING on later ticks, while the failed
        # one stays contained rather than being retried or discarded.
        self.assertEqual(self.outcomes(sweep(self.jobs, self.acts, now=LATER)),
                         [("job-b/implementation", "claim", "performed")])


class TheEngineIsAskedBeforeAnythingIsProjected(SweepCase):
    """W85500: the runtime axis, refreshed on every tick.

    THE DEFECT. A start attaches a runtime and records it; every ordinary
    sweep afterwards read that recorded row, and the only other caller of the
    reconciliation is the successful ending -- which an exceptional stage
    never reaches, correctly, because it owes no act. So a worker that wrote a
    faulted terminal and exited stayed projected `running` for as long as
    anybody looked.
    """

    def live(self):
        """Which stages have an episode currently answering for them."""
        from baton_v12.job_manager import episodes, submission as rows

        return sorted(one["stage_id"] for one in rows.stage_rows(self.jobs)
                      if episodes.live_of(self.jobs, one["stage_id"])
                      is not None)

    def test_exactly_the_stages_with_a_live_episode_are_refreshed(self):
        """NOT "every stage". A stage whose episode is over has identities
        belonging to an attempt that is finished, and asking the engine about
        them would refresh somebody else's runtime into this stage's row."""
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        report = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(sorted(one["stage_id"] for one in
                                report["refreshed"]), self.live())
        self.assertEqual(len(report["refreshed"]), len(self.live()))
        # AND EACH ONE NAMES THE EPISODE AND ATTEMPT IT ASKED ABOUT, so a
        # reader can tell which attempt an answer belongs to.
        for one in report["refreshed"]:
            self.assertIsInstance(one["episode"], int)
            self.assertTrue(one["attempt_id"].startswith("attempt-"))

    def test_a_deployment_with_no_refresh_says_not_asked(self):
        """`None` is 'nobody looked', not 'the runtime is gone'."""
        self.submit()
        report = sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual({one["state"] for one in report["refreshed"]},
                         {"not-asked"})
        self.assertEqual([one for one in report["refreshed"]
                          if "detail" in one], [])

    def test_what_the_refresh_recorded_is_what_this_tick_projects(self):
        """THE ORDER IS THE POINT. The refresh runs before the first
        projection, so this tick reports this tick's runtime truth rather than
        last tick's."""
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"execution_runtime": "running",
                                    "cleanup": None})
        self.acts.refreshed("job-a/implementation", "quiescent")
        report = sweep(self.jobs, self.acts, now=LATER)
        refreshed = {one["stage_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed["job-a/implementation"]["state"],
                         "quiescent")
        projected = status(self.jobs, self.acts, observed_at=LATER)
        held = [one for job in projected["jobs"] for one in job["stages"]
                if one["stage_id"] == "job-a/implementation"][0]
        self.assertEqual(held["runtime"]["execution_runtime"], "quiescent")

    def test_one_stages_refusal_leaves_every_other_stage_refreshed(self):
        """THE ACCEPTANCE'S ISOLATION HALF. An escaping refusal would make one
        damaged attempt stop the sweep projecting anything at all -- which is
        this Work's own defect arriving by a different road."""
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refreshes["job-a/implementation"] = ContractRefusal(
            "refused", "precondition", "this engine cannot be asked")
        self.acts.refreshed("job-b/implementation", "quiescent")
        report = sweep(self.jobs, self.acts, now=LATER)
        refreshed = {one["stage_id"]: one for one in report["refreshed"]}
        self.assertEqual(refreshed["job-a/implementation"]["state"], None)
        self.assertEqual(refreshed["job-a/implementation"]["detail"],
                         {"category": "refused", "code": "precondition"})
        self.assertEqual(refreshed["job-b/implementation"]["state"],
                         "quiescent")
        # AND THE REFUSAL'S PROSE IS NOWHERE, because it is composed from
        # values this deployment read and some of those come from a worker.
        self.assertNotIn("cannot be asked", json.dumps(report))
        # AND THE REST OF THE TICK HAPPENED. The refusal contained itself; it
        # did not stop the derivation that follows it.
        self.assertEqual(self.outcomes(report),
                         [("job-a/implementation", "claim", "performed"),
                          ("job-b/implementation", "claim", "performed")])

    def test_a_malformed_refresh_answer_is_contained_not_believed(self):
        """W85500 review 2026-09-04T14-27-54Z [P1].

        The manager called `.get` on whatever came back, so a deployment
        answering a scalar aborted the WHOLE sweep with `AttributeError` before
        the first projection -- suppressing an exchange terminal that was
        readable on disk and stopping every unrelated stage.

        RE-REVIEW 2026-09-04T19:08:40Z [P1] ADDED THE LAST TWO. `isinstance`
        plus `.get` is not a closed document: an undeclared member was
        accepted and silently discarded, and a `dict` SUBCLASS ran its own
        `.get` inside the validation boundary and propagated whatever that
        raised out of it. Both are now refused as the malformed evidence they
        are.
        """

        class Hostile(dict):
            def get(self, *_args, **_kwargs):
                raise RuntimeError("a subclass method ran inside the boundary")

        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        for wrong in ("wrong", 7, ["running"],
                      {"execution_runtime": "made-up"},
                      {"something_else": "running"},
                      {"execution_runtime": "quiescent", "unexpected": 1},
                      Hostile(execution_runtime="quiescent")):
            self.acts.refreshes["job-a/implementation"] = wrong
            self.acts.refreshed("job-b/implementation", "quiescent")
            report = sweep(self.jobs, self.acts, now=LATER)
            held = {one["stage_id"]: one for one in report["refreshed"]}
            self.assertEqual(held["job-a/implementation"]["state"], None,
                             wrong)
            self.assertEqual(
                held["job-a/implementation"]["detail"],
                {"category": "integrity", "code": "schema"}, wrong)
            # AND THE OTHER STAGE STILL GOT ITS ANSWER.
            self.assertEqual(held["job-b/implementation"]["state"],
                             "quiescent", wrong)

    def test_an_engine_that_cannot_be_asked_is_uncertain_not_gone(self):
        """A deployment's own `RefreshUnavailable` is an unasked question.

        Only typed refusals were contained, so a socket, a pipe or a missing
        binary aborted the sweep before anything was projected. Nothing is
        recorded from this: the runtime axis keeps whatever it last knew, which
        is the honest difference between "gone" and "unasked".

        THE CONDITION IS THE DEPLOYMENT'S, which is re-review
        2026-09-04T19:08:40Z [P1]. The manager used to catch `OSError` and
        decide on every deployment's behalf what an unreachable engine is --
        and a `subprocess` runner that hit its deadline raises
        `TimeoutExpired`, which is the same operational fact and not an
        `OSError`. Both are translated where they are understood, and this
        pass contains what was named.
        """
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refreshes["job-a/implementation"] = RefreshUnavailable(
            OSError("the engine socket is not there"))
        self.acts.refreshed("job-b/implementation", "quiescent")
        report = sweep(self.jobs, self.acts, now=LATER)
        held = {one["stage_id"]: one for one in report["refreshed"]}
        self.assertEqual(held["job-a/implementation"]["state"], None)
        self.assertEqual(held["job-a/implementation"]["detail"],
                         {"category": "uncertain",
                          "code": "engine-unreachable", "error": "OSError"})
        self.assertEqual(held["job-b/implementation"]["state"], "quiescent")
        self.assertNotIn("socket is not there", json.dumps(report))
        # AND THE TICK FINISHED: the derivation after this pass still ran.
        self.assertEqual(self.outcomes(report),
                         [("job-a/implementation", "claim", "performed"),
                          ("job-b/implementation", "claim", "performed")])

    def test_a_timed_out_runner_is_the_same_unasked_question(self):
        """The type the blanket branch used to swallow, named by its owner.

        `subprocess.TimeoutExpired` is not an `OSError`, so under the previous
        candidate a runner that hit its deadline was reported as an
        implementation `fault` -- and on any tick but the last one, reported
        nowhere at all.
        """
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refreshes["job-a/implementation"] = RefreshUnavailable(
            subprocess.TimeoutExpired(["docker", "inspect"], 600))
        self.acts.refreshed("job-b/implementation", "quiescent")
        report = sweep(self.jobs, self.acts, now=LATER)
        held = {one["stage_id"]: one for one in report["refreshed"]}
        self.assertEqual(held["job-a/implementation"]["detail"],
                         {"category": "uncertain",
                          "code": "engine-unreachable",
                          "error": "TimeoutExpired"})
        self.assertEqual(held["job-b/implementation"]["state"], "quiescent")

    def test_an_arbitrary_defect_escapes_rather_than_becoming_report_data(
            self):
        """RE-REVIEW 2026-09-04T19:08:40Z [P1], and it reverses this
        candidate's own earlier answer.

        The previous pass caught `Exception` and turned any defect into a
        per-tick `refresh-fault` detail. That is not disclosure on the serving
        path: `serve` overwrites `report` every tick and answers only the last
        one, so a programming defect caught on an earlier tick is raised
        nowhere, recorded nowhere, and gone entirely as soon as one tick
        succeeds. Containment is for malformed evidence and for the failure a
        deployment itself named; a defect belongs to whoever is running the
        loop.
        """
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refreshes["job-a/implementation"] = RuntimeError(
            "engine transport broke")
        self.acts.refreshed("job-b/implementation", "quiescent")
        with self.assertRaises(RuntimeError) as raised:
            sweep(self.jobs, self.acts, now=LATER)
        self.assertIn("engine transport broke", str(raised.exception))

    def test_an_unreachable_engine_never_suppresses_a_readable_exchange(self):
        """The acceptance sentence this finding put at risk, directly.

        The exchange is a durable file and is read by the projection that runs
        AFTER this pass. A contained engine failure that escaped would mean
        nobody ever read it.
        """
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.observed("job-a/implementation", claimed_by=True,
                           runtime={"runtime_id": "runtime-1",
                                    "execution_runtime": "running",
                                    "cleanup": None})
        self.acts.commanded("job-a/implementation", state="faulted",
                            terminal={"ending": "faulted",
                                      "fault_code": "agent",
                                      "disposition": None,
                                      "manifest_digest": None})
        self.acts.refreshes["job-a/implementation"] = RefreshUnavailable(
            OSError("broken"))
        report = sweep(self.jobs, self.acts, now=LATER)
        del report
        projected = status(self.jobs, self.acts, observed_at=LATER)
        held = [one for job in projected["jobs"] for one in job["stages"]
                if one["stage_id"] == "job-a/implementation"][0]
        self.assertEqual(held["exchange"]["terminal"]["fault_code"], "agent")
        self.assertEqual(held["state"], "exceptional")

    def test_repeated_sweeps_ask_again_and_change_nothing_else(self):
        """LEVEL-TRIGGERED, like every other pass here: the answer is read
        from the engine each tick rather than remembered."""
        self.submit()
        sweep(self.jobs, self.acts, now=NOW)
        self.acts.refreshed("job-a/implementation", "quiescent")
        self.acts.refreshed("job-b/implementation", "quiescent")
        first = sweep(self.jobs, self.acts, now=LATER)
        self.acts.refreshed_calls.clear()
        second = sweep(self.jobs, self.acts, now=LATER)
        self.assertEqual(sorted(self.acts.refreshed_calls), self.live())
        self.assertEqual([one["state"] for one in first["refreshed"]],
                         [one["state"] for one in second["refreshed"]])
        self.assertEqual(second["acts"], [])


class OrdinarySuccess(SweepCase):
    """The headline claim: after the submission, nothing is typed per act."""

    def test_two_jobs_reach_their_terminal_states_on_repeated_ticks_alone(self):
        self.submit()
        # Tick one: both ungated implementations are admitted.
        sweep(self.jobs, self.acts, now=NOW)
        # Tick two: both claims follow from the receipts alone.
        sweep(self.jobs, self.acts, now=LATER)
        # The runtimes then do their work; freezing a result is the other
        # leaves' business and arrives here as the manager's own observation.
        self.acts.frozen("job-a/implementation", "completed")
        self.acts.frozen("job-b/implementation", "completed")
        # Tick three: the gate this opens admits the review with no operator
        # naming it.
        sweep(self.jobs, self.acts, now=LATER)
        sweep(self.jobs, self.acts, now=LATER)
        self.acts.frozen("job-a/review", "completed")
        # And then nothing more is owed.
        self.assertEqual(sweep(self.jobs, self.acts, now=LATER)["acts"], [])
        self.assertEqual(
            sorted(one for one in self.acts.calls
                   if one[0] in ("admit", "claim")),
            [("admit", "job-a/implementation"), ("admit", "job-a/review"),
             ("admit", "job-b/implementation"),
             ("claim", "job-a/implementation"), ("claim", "job-a/review"),
             ("claim", "job-b/implementation")])


class Persistence(SweepCase):

    def test_the_owed_act_survives_the_process_that_derived_it(self):
        self.submit()
        self.jobs.close()
        resumed = JobStore.open(self.job_path, authority_uuid=UUID, incarnation="jobs-2",
                                clock=self.clock)
        self.addCleanup(resumed.close)
        self.assertEqual([one["act"] for one in owed_acts(resumed, self.acts)],
                         ["admit", "admit"])
        self.assertEqual([one["operation_id"]
                          for one in owed_acts(resumed, self.acts)],
                         ["offer.issue:" + identities(UUID, "job-a/implementation", 1)[0],
                          "offer.issue:" + identities(UUID, "job-b/implementation", 1)[0]])


if __name__ == "__main__":
    unittest.main()
