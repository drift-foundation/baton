"""W81857 — the level-triggered exchange pass, and the status that stopped lying.

`work/records/2026/09/finding-v12-production-runtime-conversation/`.

TWO DEFECTS, ONE FILE. W76207's control plane stopped at the launch: nothing
commanded a started container, and the projection reported a stage as `running`
on the strength of a runtime identity the start had attached. The live W71917
submission reached a healthy container whose only process was an idle PID 1,
and the board said work was in progress for as long as anybody cared to look.

WHY THE COMMAND IS NOT INSIDE `launch()`. Every reason `_launch` is not inside
`claim()` applies one layer down: a crash between the engine's answer and
anything recording it leaves the next incarnation observing an attached runtime
without calling `launch` again, so a command folded into that call would be
skipped once, permanently, on the path nobody watches. The cases below drive
that exact restart.
"""

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (Unobserved, reconcile, status, submit,
                                   sweep)

if __package__:
    from .fixtures import (NOW, SOON, FakeOperations, JobManagerCase, job,
                           stage, submission)
else:
    from fixtures import (NOW, SOON, FakeOperations, JobManagerCase, job,
                          stage, submission)

STAGE = "job-a/implementation"


class ExchangeCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()
        submit(self.jobs, submission(jobs=[job("job-a")]))
        self.acts = FakeOperations()
        self.acts.starts(STAGE, attaches=True)

    def started(self):
        """Two ticks: admit, then claim-launch-and-command.

        The second tick does three things because every pass after the claim
        reacquires canonical state: the claim commits, the launch sees a
        claimed stage with no runtime, and the exchange pass sees the runtime
        the launch just attached. That is what level-triggered buys -- a fresh
        container does not wait a whole tick for something to do.
        """
        sweep(self.jobs, self.acts, now=NOW)
        return sweep(self.jobs, self.acts, now=SOON)

    def state(self, stage_id=STAGE):
        return self.projected()[stage_id]

    def projected(self, store=None, acts=None):
        return {one["stage_id"]: one for job_status in
                status(store if store is not None else self.jobs,
                       acts if acts is not None else self.acts,
                       observed_at=SOON)["jobs"]
                for one in job_status["stages"]}

    def spoke(self):
        return [one for one in self.acts.calls
                if one[0] in ("dispatch", "conclude")]

    def answered(self):
        """A started, commanded stage whose worker has answered."""
        self.acts.commands[STAGE] = {"published": True}
        self.started()
        self.acts.commanded(STAGE, state="answered")


class AStartedContainerIsNotWorkInProgress(ExchangeCase):
    """The defect, stated as the property that now holds.

    A runtime identity says a container exists. It does not say a command
    reached it, that a provider was spawned, or that anything is being written
    -- and elapsed time and process health cannot tell the difference either,
    which is why the projection had no way to be wrong loudly.
    """

    def test_a_started_container_nobody_commanded_is_not_running(self):
        self.started()
        held = self.state()
        self.assertEqual(held["state"], "starting")
        self.assertIsNone(held["exchange"])
        self.assertEqual(held["runtime"]["runtime_id"], f"runtime-{STAGE}")

    def test_a_deployment_with_no_exchange_read_says_nobody_looked(self):
        self.started()
        # `starting` AND `exchange: null` ARE ONE ANSWER, and it is honest:
        # this control plane holds no exchange read at all, which is not the
        # same claim as an exchange that has been read and is empty.
        self.assertIsNone(self.state()["exchange"])
        self.assertEqual(self.state()["state"], "starting")

    def test_a_commanded_but_unaccepted_worker_is_waiting(self):
        self.started()
        self.acts.commanded(STAGE)
        held = self.state()
        self.assertEqual(held["state"], "waiting")
        self.assertEqual(held["exchange"]["state"], "waiting")

    def test_the_active_word_is_earned_by_the_workers_receipt(self):
        self.started()
        self.acts.commanded(STAGE, state="working")
        self.assertEqual(self.state()["state"], "running")

    def test_each_kind_names_its_own_active_word_only_once_working(self):
        submit(self.jobs, submission(submission_id="sub-kinds", jobs=[
            job("job-k", stages=[stage("implementation"), stage("review"),
                                 stage("integration")])]))
        for stage_id, expected in (("job-k/implementation", "running"),
                                   ("job-k/review", "reviewing"),
                                   ("job-k/integration", "integrating")):
            with self.subTest(stage=stage_id):
                self.acts.observed(
                    stage_id, claimed_by=True,
                    runtime={"attempt_id": f"attempt:{stage_id}",
                             "runtime_id": "runtime-1",
                             "execution_runtime": "running",
                             "cleanup": None, "assignment": None})
                self.acts.commanded(stage_id, state="working")
                self.assertEqual(self.state(stage_id)["state"], expected)

    def test_an_answered_worker_is_ending_rather_than_completed(self):
        self.started()
        self.acts.commanded(STAGE, state="answered")
        # NOT `completed`. Nothing has frozen the output, taken custody of it
        # or handed the Work on, and reporting a result nobody holds is the
        # same class of claim this Work exists to remove.
        self.assertEqual(self.state()["state"], "answering")

    def test_a_faulted_or_lost_exchange_is_exceptional_and_contained(self):
        self.started()
        for held in ("faulted", "lost", "unreadable"):
            with self.subTest(state=held):
                self.acts.commanded(STAGE, state=held)
                self.assertEqual(self.state()["state"], "exceptional")

    def test_a_receipted_turn_whose_runtime_stopped_is_not_working(self):
        """W81857 review 2026-09-04T03-43-45Z [P1], and the whole cross-product.

        A receipt is durable and a process is not. `working` says the worker
        published its pre-dispatch receipt; it cannot say the worker is still
        there. Only `uncertain` used to be treated as exceptional and every
        other axis value was handed to the exchange mapping alone, so a
        container that died mid-turn kept reporting the active word -- silence
        read as progress, which is the original defect one layer down.
        """
        self.started()
        for axis in ("not-started", "start-requested", "cancel-requested",
                     "stopping", "quiescent", "uncertain", "destroyed"):
            with self.subTest(execution_runtime=axis):
                self.acts.observations[STAGE]["runtime"][
                    "execution_runtime"] = axis
                self.acts.commanded(STAGE, state="working")
                self.assertEqual(self.state()["state"], "exceptional")

    def test_only_an_actually_running_runtime_earns_the_active_word(self):
        self.started()
        self.acts.observations[STAGE]["runtime"]["execution_runtime"] = \
            "running"
        self.acts.commanded(STAGE, state="working")
        self.assertEqual(self.state()["state"], "running")

    def test_a_pre_command_stage_whose_runtime_stopped_is_not_starting(self):
        """The same rule before the command, where it is equally true.

        A container that is not running cannot be commanded and cannot accept
        one, so reporting it as a stage that is about to be given work would be
        the same false patience in an earlier state.
        """
        self.started()
        for state in ("not-requested", "waiting"):
            for axis in ("quiescent", "destroyed", "uncertain"):
                with self.subTest(exchange=state, execution_runtime=axis):
                    self.acts.observations[STAGE]["runtime"][
                        "execution_runtime"] = axis
                    self.acts.commanded(STAGE, state=state)
                    self.assertEqual(self.state()["state"], "exceptional")

    def test_an_answered_terminal_does_not_need_a_live_runtime(self):
        """The one state whose correctness does not depend on the container.

        The ending quiesces the runtime on purpose, so requiring `running`
        here would make a correct mid-ending stage look broken and stop the
        very acts that finish it.
        """
        self.acts.commands[STAGE] = {"published": True}
        self.started()
        self.acts.commanded(STAGE, state="answered")
        for axis in ("running", "stopping", "quiescent", "destroyed"):
            with self.subTest(execution_runtime=axis):
                self.acts.observations[STAGE]["runtime"][
                    "execution_runtime"] = axis
                self.assertEqual(self.state()["state"], "answering")

    def test_a_stopped_runtime_authorizes_no_replay_of_the_turn(self):
        """Reported and contained, never re-commanded.

        Turning an incomplete turn into an ending needs positive evidence and
        a named recovery act; this control plane has neither, so what it does
        is say so and stop asking rather than send a second command.
        """
        self.started()
        self.acts.observations[STAGE]["runtime"]["execution_runtime"] = \
            "quiescent"
        self.acts.commanded(STAGE, state="working")
        before = len(self.spoke())
        sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(len(self.spoke()), before)
        self.assertEqual(self.state()["state"], "exceptional")

    def test_an_exchange_state_this_build_cannot_name_is_not_the_calmest(self):
        self.started()
        self.acts.commanded(STAGE, state="probably-fine")
        self.assertEqual(self.state()["state"], "exceptional")

    def test_the_status_schema_says_the_vocabulary_moved(self):
        self.assertEqual(status(self.jobs, self.acts,
                                observed_at=NOW)["schema"],
                         "baton.v12.job-status/3")


class AReaderWithNoExchangeStillTellsTheTruth(ExchangeCase):
    """W81857 review 2026-09-04T07-00-54Z [P1]: the read-only surface.

    `job_manager status` is given no deployment factory, so it holds no
    exchange read and honestly answers `exchange: null`. That used to mean it
    skipped the ending-owed rule entirely -- and a stage whose output was
    frozen and whose cleanup had not settled read back `completed` there while
    a serving manager called it `answering`. Same durable state, two answers,
    and the reassuring one belonged to the reader that could see less.

    `exchange: null` reports that nobody looked. It does not make a false
    terminal state truthful, and a dependent gate must not open on one.
    """

    def blind(self):
        """The same store, read through a surface with no exchange reader."""
        acts = FakeOperations()
        acts.observations = {stage_id: dict(held, exchange=None)
                             for stage_id, held
                             in self.acts.observations.items()}
        return acts

    def test_a_frozen_output_with_an_unsettled_cleanup_is_not_completed(self):
        self.answered()
        for cleanup in (None, "pending", "blocked-on-intake"):
            with self.subTest(cleanup=cleanup):
                self.acts.frozen(STAGE, "completed",
                                 execution_runtime="quiescent",
                                 cleanup=cleanup)
                self.assertEqual(self.state()["state"], "answering")
                # AND THE SAME ANSWER WITH THE EXCHANGE TAKEN AWAY. The
                # evidence the reader still has -- the manager's own frozen
                # output and its own cleanup axis -- is enough, which is the
                # whole correction.
                blind = self.blind()
                held = self.projected(acts=blind)[STAGE]
                self.assertEqual(held["state"], "answering")
                self.assertIsNone(held["exchange"])

    def test_a_settled_cleanup_still_projects_the_frozen_disposition(self):
        self.answered()
        for cleanup in ("complete", "retained", "failed"):
            with self.subTest(cleanup=cleanup):
                self.acts.frozen(STAGE, "completed",
                                 execution_runtime="destroyed",
                                 cleanup=cleanup)
                self.assertEqual(self.state()["state"], "completed")
                self.assertEqual(
                    self.projected(acts=self.blind())[STAGE]["state"],
                    "completed")

    def test_no_exchange_read_before_any_answer_is_still_starting(self):
        """The positive control the correction must not break.

        A container that is up and has answered nothing has no frozen output
        either, so the new rule has nothing to fire on and the honest answer
        is unchanged: the container is up and this reader cannot see a turn.
        """
        self.started()
        held = self.projected(acts=self.blind())[STAGE]
        self.assertEqual(held["state"], "starting")
        self.assertIsNone(held["exchange"])

    def test_an_unfinished_ending_opens_no_dependent_gate(self):
        """The consequence that matters most, asserted as its own fact.

        Gates open on `completed` and nothing else, so a stage that is only
        `answering` must leave its successor blocked -- and the reader with no
        exchange must agree, or a dependent stage starts on the strength of a
        result nobody has taken custody of.
        """
        submit(self.jobs, submission(submission_id="sub-gate", jobs=[
            job("job-g", stages=[
                stage("implementation"),
                stage("review", depends_on=[{"job_id": "job-g",
                                             "kind": "implementation"}])])]))
        first, second = "job-g/implementation", "job-g/review"
        self.acts.observed(first, claimed_by=True,
                           runtime={"attempt_id": f"attempt:{first}",
                                    "runtime_id": "runtime-1",
                                    "execution_runtime": "quiescent",
                                    "cleanup": None, "assignment": None})
        self.acts.commanded(first, state="answered")
        self.acts.frozen(first, "completed", execution_runtime="quiescent",
                         cleanup="pending")
        for acts in (self.acts, self.blind()):
            held = self.projected(acts=acts)
            self.assertEqual(held[first]["state"], "answering")
            self.assertEqual(held[second]["state"], "blocked")
            self.assertEqual([one["open"] for one in held[second]["gates"]],
                             [False])
        # AND IT OPENS ONCE THE ENDING ACTUALLY FINISHES.
        self.acts.frozen(first, "completed", execution_runtime="destroyed",
                         cleanup="complete")
        held = self.projected()
        self.assertEqual(held[first]["state"], "completed")
        self.assertEqual(held[second]["state"], "queued")


class TheCommandIsLevelTriggered(ExchangeCase):

    def test_a_started_stage_is_commanded_and_reported(self):
        self.acts.commands[STAGE] = {"published": True}
        report = self.started()
        self.assertEqual([(one["stage_id"], one["outcome"])
                          for one in report["started"]],
                         [(STAGE, "started")])
        self.assertEqual([(one["stage_id"], one["act"], one["outcome"])
                          for one in report["spoken"]],
                         [(STAGE, "dispatch", "performed")])

    def test_the_command_and_the_launch_happen_in_one_tick(self):
        """The stage this tick started is the stage this tick commands.

        The exchange pass reacquires canonical state after the launch, so a
        container that came up a millisecond ago does not wait a whole tick
        for the sequence that gives it something to do.
        """
        self.acts.commands[STAGE] = {"published": True}
        report = self.started()
        self.assertEqual([one[0] for one in self.acts.calls
                          if one[0] in ("launch", "dispatch")],
                         ["launch", "dispatch"])
        self.assertEqual(len(report["spoken"]), 1)

    def test_an_unstarted_stage_is_never_commanded(self):
        """Eligibility is canonical state, not a hopeful attempt.

        Before the launch the stage is queued, then offered, then claimed, and
        none of those has a container to command.
        """
        self.acts.launches.pop(STAGE, None)
        self.acts.commands[STAGE] = {"published": True}
        sweep(self.jobs, self.acts, now=NOW)
        sweep(self.jobs, self.acts, now=NOW)
        self.assertEqual(self.spoke(), [])

    def test_a_commanded_stage_is_not_commanded_again(self):
        self.acts.commands[STAGE] = {"published": True}
        self.started()
        before = len(self.spoke())
        sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(len(self.spoke()), before)

    def test_a_working_worker_is_never_interrupted(self):
        self.acts.commands[STAGE] = {"published": True}
        self.started()
        self.acts.commanded(STAGE, state="working")
        before = len(self.spoke())
        sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(len(self.spoke()), before)

    def test_a_restart_before_the_command_publishes_it_once(self):
        """The crash window this pass exists for, driven from both sides.

        A manager that died between the engine's answer and anything recording
        it leaves an attached runtime and no command. The next incarnation
        derives the same act from the same canonical state -- which is what
        level-triggered means -- and the publisher's own derived name is what
        makes a duplicate an adoption rather than a second sequence.
        """
        self.acts.commands[STAGE] = {"published": True}
        self.started()
        resumed = reconcile(self.jobs, self.acts, now=SOON)
        self.assertEqual(resumed["spoken"], [])
        self.assertEqual(len([one for one in self.spoke()
                              if one[0] == "dispatch"]), 1)

    def test_a_deployment_with_no_dispatch_defers_rather_than_pretending(self):
        report = self.started()
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["spoken"]],
                         [("dispatch", "deferred")])
        self.assertEqual(report["spoken"][0]["detail"]["code"], "capability")

    def test_a_refused_command_leaves_the_next_tick_asking_again(self):
        self.acts.commands[STAGE] = ContractRefusal(
            "refused", "precondition", "the delivery is not ready")
        self.started()
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(report["spoken"][0]["outcome"], "deferred")
        self.assertEqual(len([one for one in self.spoke()
                              if one[0] == "dispatch"]), 2)


class TheEndingIsLevelTriggeredToo(ExchangeCase):

    def test_an_answered_stage_is_concluded_and_reported(self):
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["spoken"]],
                         [("conclude", "performed")])

    def test_a_crash_after_the_freeze_still_owes_the_rest_of_the_ending(self):
        """W81857 review 2026-09-04T03-43-45Z [P1], and the case it replaces.

        `test_a_frozen_output_ends_the_asking` asserted the unsafe inverse: it
        required the control plane to STOP asking as soon as an output was
        frozen. The freeze is the third of seven steps, so a process death
        after it left intake, retention, the exact-generation Authority pass
        and cleanup owed forever while every later sweep reported the Work
        `completed` -- finished, on a board, with its assignment still live and
        its result never handed to review.

        This is the same durable state and the opposite expectation.
        """
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        # EXACTLY WHAT `request_freeze` COMMITTED AND NOTHING AFTER IT: the
        # cleanup axis is the last step's own, and it has not moved.
        self.acts.frozen(STAGE, "completed", execution_runtime="quiescent",
                         cleanup="pending")
        before = len(self.spoke())
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(self.state()["state"], "answering")
        self.assertEqual([(one["act"], one["outcome"])
                          for one in report["spoken"]],
                         [("conclude", "performed")])
        self.assertEqual(len(self.spoke()), before + 1)

    def test_every_unsettled_cleanup_state_keeps_the_ending_owed(self):
        """Each boundary a crash can land on, between the freeze and the end.

        `blocked-on-intake` is the manager's own answer when cleanup was asked
        for and intake had not happened, and `pending` is where it starts.
        Neither is an ending, so both keep the act owed -- which is what makes
        the whole composition replayable rather than only its first half.
        """
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        for cleanup in (None, "pending", "blocked-on-intake"):
            with self.subTest(cleanup=cleanup):
                self.acts.frozen(STAGE, "completed",
                                 execution_runtime="quiescent",
                                 cleanup=cleanup)
                before = len(self.spoke())
                sweep(self.jobs, self.acts, now=SOON)
                self.assertEqual(self.state()["state"], "answering")
                self.assertEqual(len(self.spoke()), before + 1)

    def test_a_settled_cleanup_is_what_ends_the_asking(self):
        """And only then does the frozen disposition decide the stage.

        `complete`, `retained` and `failed` are the cleanup axis's terminal
        values -- the last substep reached its own ending -- so there is
        nothing left to replay and the stage is what its frozen result says.
        """
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        for cleanup in ("complete", "retained", "failed"):
            with self.subTest(cleanup=cleanup):
                self.acts.frozen(STAGE, "completed",
                                 execution_runtime="destroyed",
                                 cleanup=cleanup)
                before = len(self.spoke())
                sweep(self.jobs, self.acts, now=SOON)
                self.assertEqual(self.state()["state"], "completed")
                self.assertEqual(len(self.spoke()), before)

    def test_a_restart_in_the_middle_of_the_ending_replays_it(self):
        """The window from the other side: a resumed manager, not a next tick.

        Nothing is carried across the restart. The act is derived from the
        same canonical state -- an answered exchange whose cleanup axis has not
        settled -- so `reconcile` owes exactly what a running manager would.
        """
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        self.acts.frozen(STAGE, "completed", execution_runtime="quiescent",
                         cleanup="blocked-on-intake")
        mark = len(self.spoke())
        resumed = reconcile(self.jobs, self.acts, now=SOON)
        self.assertEqual([one["act"] for one in resumed["spoken"]],
                         ["conclude"])
        self.assertEqual([one[0] for one in self.spoke()[mark:]], ["conclude"])

    def test_an_unfinished_ending_is_never_reported_completed(self):
        """The projection half, stated on its own.

        A frozen output no longer outranks an owed ending, whatever its
        disposition says, because the disposition describes the worker's
        answer and not what became of it.
        """
        self.answered()
        for disposition in ("completed", "unable", "cancelled"):
            with self.subTest(disposition=disposition):
                self.acts.frozen(STAGE, disposition,
                                 execution_runtime="quiescent",
                                 cleanup="pending")
                self.assertEqual(self.state()["state"], "answering")

    def test_a_restart_after_the_answer_resumes_only_the_owed_ending(self):
        """No second command, ever, on the path a restart takes.

        The command is already on disk and the worker has already answered it;
        what a resumed manager owes is the ending, and asking for a turn again
        would be a second provider invocation on the one path nobody watches.
        """
        self.answered()
        self.acts.endings[STAGE] = {"disposition": "completed"}
        mark = len(self.spoke())
        reconcile(self.jobs, self.acts, now=SOON)
        self.assertEqual([one[0] for one in self.spoke()[mark:]],
                         ["conclude"])

    def test_a_refused_ending_is_contained_and_asked_again(self):
        self.answered()
        self.acts.endings[STAGE] = ContractRefusal(
            "refused", "precondition", "the runtime is not quiescent")
        report = sweep(self.jobs, self.acts, now=SOON)
        self.assertEqual(report["spoken"][0]["outcome"], "deferred")
        self.assertEqual(self.state()["state"], "answering")

    def test_one_stages_refusal_leaves_another_stage_observable(self):
        submit(self.jobs, submission(submission_id="sub-two",
                                     jobs=[job("job-c"), job("job-d")]))
        for stage_id in ("job-c/implementation", "job-d/implementation"):
            self.acts.observed(
                stage_id, claimed_by=True,
                runtime={"attempt_id": f"attempt:{stage_id}",
                         "runtime_id": "runtime-1",
                         "execution_runtime": "running",
                         "cleanup": None, "assignment": None})
            self.acts.commanded(stage_id, state="answered")
        self.acts.endings["job-c/implementation"] = ContractRefusal(
            "refused", "precondition", "not quiescent")
        self.acts.endings["job-d/implementation"] = {"disposition": "completed"}
        report = sweep(self.jobs, self.acts, now=SOON)
        spoken = {one["stage_id"]: one["outcome"] for one in report["spoken"]}
        self.assertEqual(spoken["job-c/implementation"], "deferred")
        self.assertEqual(spoken["job-d/implementation"], "performed")
        self.assertEqual(self.projected()["job-d/implementation"]["state"],
                         "answering")

    def test_a_read_only_status_surface_never_commands_or_concludes(self):
        self.answered()
        before = len(self.spoke())
        status(self.jobs, self.acts, observed_at=SOON)
        status(self.jobs, Unobserved(), observed_at=SOON)
        self.assertEqual(len(self.spoke()), before,
                         "status is a read; it asks nobody to do anything")
