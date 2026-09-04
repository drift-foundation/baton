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

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, owed_acts, receipt_rows,
                                   receipts_of, sweep,
                                   submit)
from baton_v12.job_manager.episodes import identities

if __package__:
    from .fixtures import (LATER, NOW, FakeOperations, JobManagerCase, job,
                           stage, submission)
else:
    from fixtures import (LATER, NOW, FakeOperations, JobManagerCase, job,
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
                         "offer.issue:" + identities(
                             "job-a/implementation", 1)[0])
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
        resumed = JobStore.open(self.job_path, incarnation="jobs-2",
                                clock=self.clock)
        self.addCleanup(resumed.close)
        self.assertEqual([one["act"] for one in owed_acts(resumed, self.acts)],
                         ["admit", "admit"])
        self.assertEqual([one["operation_id"]
                          for one in owed_acts(resumed, self.acts)],
                         ["offer.issue:" + identities(
                             "job-a/implementation", 1)[0],
                          "offer.issue:" + identities(
                              "job-b/implementation", 1)[0]])


if __name__ == "__main__":
    unittest.main()
