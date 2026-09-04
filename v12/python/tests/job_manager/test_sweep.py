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
