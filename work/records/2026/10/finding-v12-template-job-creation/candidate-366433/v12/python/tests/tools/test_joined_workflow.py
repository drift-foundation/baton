"""W361912 — ONE CREATED JOB, ALL THE WAY ROUND, AND HOW LONG THE START TOOK.

This Work's children each proved one leg. The resolver resolves; the delivery
child proved a created Job's own task reaches a started implementation AND
review runtime; the retry child proved a fresh attempt keeps that task through
both runtimes; the package child proved the frozen command creates and replays
ordinary Jobs. What none of them reached is the WORKFLOW: a technical review
that decides something, the correction round that decision calls for, and a
result that is held rather than accepted -- and the one measurement DESIGN
OBS-0 asks for, taken on that same path.

WHAT IS REAL HERE. The Job store, the control store and the Authority; the real
`creation.create_template_job`; the pool composed by
`stage_execution.operations_from` with its own `reconcile`/`sweep` loop; two
real in-image worker turns per round through `baton_worker.serve_exchange`; the
real ending -- seal, intake, retention, `retain_proposal`, `publish_candidate`,
`freeze_checkpoint` -- the real review attachment, the real
`review_verdict_from_result`, and the real `open_correction` reached through
the loop's own `routed`. No offer, claim, activation, preparation, launch,
verdict or correction round is written by this file.

WHY NOT `ComposedOneJobCase`, which already drives a lifecycle. That harness
initializes a repository and commits into it. An agent may not perform a
mutating version-control operation, and that rule is not scoped to the working
tree, so this suite uses the composition this Work's own children established
instead: `test_review_driver.Profile` -- the deployment-configured checkpoint
profile with no VCS behind it -- plus process runners that refuse any
version-control invocation. Every case here would fail loudly rather than
quietly spawn one.

THE THREE DETERMINISTIC SEAMS, NAMED. The ENGINE is `_ConcurrentEngine`, the
repository's own multi-container model. The CHECKPOINT PROFILE is the one
above. The WORKER is `scripted_agent.ScriptedAgent` with the two additions
each role needs: the producer writes a synthetic object transport and a
`baton.git-proposal/1` claim, and the reviewer writes a `report.json` and a
`baton.checkpoint-review/1` claim. Those bytes are not a patch anybody could
apply and not a judgment anybody formed; what they are is the operand shape the
publication and the verdict reader VALIDATE, and both of them do -- the
publication refuses a claim whose transport is not in the frozen tree, and
`review_verdict_from_result` refuses a claim whose base, head and tree are not
the checkpoint's own.

WHAT THE TIMING IS AND IS NOT. `TheRoutineStartupInterval` below measures the
whole routine path OBS-0 names, with its endpoints and its exclusions written
down in that class rather than implied. It is a SIMULATED interval: the
container engine and the provider are the seams above, so it is not evidence
about image pull, container start, provider authentication or model latency.
It is evidence about everything this product does between an operator's words
and the agent's first substantive act.
"""
import json
import os
import time
import unittest

from baton_v12.contracts import digest
from baton_v12.job_manager import creation, reconcile, review_driver, sweep
from baton_v12.worker_manager import attempts, review_cycles

from tools import single_worker, stage_execution

from tests.job_manager import fixtures
# THE MODULES AND NOT THEIR CLASSES. Binding another suite's case class at
# module level makes unittest collect it here too, so its assertions re-run
# under this file's name -- noise at best, and a second place the same failure
# is reported. The two fixtures below are reached through their modules; only
# `ServingCase` is bound, because this suite's own base derives from it.
from tests.tools import test_job_task_delivery as _delivery
from tests.tools import test_stage_execution as _execution
from tests.tools.test_stage_execution import ServingCase


class JoinedWorkflowCase(ServingCase):
    """One created Job, a producer, an independent reviewer, and the loop.

    THE HELPERS ARE BORROWED AND THE CASES ARE NOT. `reviewing` is the accepted
    delivery suite that carries a created Job to a started review runtime; what
    this class adds is the reviewer's own turn, which is where a verdict comes
    from, and the rounds that follow it.
    """

    # BOUND IN THE CLASS BODY, where they become class attributes rather than
    # module ones -- `test_job_task_delivery` does the same for the same
    # reason. A module-level name is what unittest collects.
    reviewing = _delivery.TheReviewStageRunsThroughThePoolServingLoop
    ComposedOneJobCase = _execution.ComposedOneJobCase

    BASE = reviewing.BASE
    HEAD = reviewing.HEAD
    PROPOSAL_OUTPUTS = reviewing.PROPOSAL_OUTPUTS

    no_version_control = reviewing.no_version_control
    identity_for = reviewing.identity_for
    creation_ports = reviewing.creation_ports
    create = reviewing.create
    driven = reviewing.driven
    stages = reviewing.stages
    stage_of = reviewing.stage_of
    published = reviewing.published
    worker_of = reviewing.worker_of
    proposal_manifest = reviewing.proposal_manifest
    proposing_workers = reviewing.proposing_workers
    turn = reviewing.turn
    quiescing = ComposedOneJobCase.quiescing

    # WHAT THE OPERATOR SELECTED, in one place, because four cases compare the
    # delivered task against it.
    TASK = "joined-a"
    STATEMENT = "Carry one created Job through review and its correction."

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()
        self.produced = []
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.BASE)
        finally:
            authority.dispose()

    # -- the two workers, each with the one addition its role needs ---------

    def producing_agent(self, disposition="completed"):
        """The producer: a synthetic candidate, or an honest `unable`.

        `disposition` is this fixture's one switch and it is the whole of the
        held-result case: a worker that ANSWERS it could not do the task is an
        ending the product settles itself, and the material it produced is
        taken into custody rather than discarded.
        """
        import scripted_agent

        base, head, held = self.BASE, self.HEAD, disposition
        produced = self.produced

        class Producing(scripted_agent.ScriptedAgent):
            def work(self, seen, declared):
                produced.append(time.monotonic())
                answered = super().work(seen, declared)
                kinds = {one["name"]: one["type"] for one in declared}
                paths = {one["name"]: one["path"] for one in declared}
                for name, kind in kinds.items():
                    if kind != "git-change-proposal":
                        continue
                    with open(os.path.join(scripted_agent.OUTPUT_ROOT,
                                           paths[name], "objects.bundle"),
                              "wb") as writing:
                        writing.write(b"a synthetic object transport\n")
                outputs = []
                for one in answered["outputs"]:
                    if kinds[one["name"]] == "git-change-proposal":
                        if held == "unable":
                            # AN `unable` ANSWER WITHHOLDS THE PROPOSAL, which
                            # is what `unable` means. The other outputs are
                            # still produced, because "a retention decision
                            # names at least one artifact".
                            one = dict(one, status="missing-optional")
                        else:
                            one = dict(one, result_metadata={
                                "baton.git-proposal/1": {
                                    "base": base, "head": head,
                                    "transport": "objects.bundle",
                                    "recap": "a synthetic candidate"}})
                    outputs.append(one)
                if held == "unable":
                    return {"disposition": "unable", "outputs": outputs,
                            "recap": "the scripted producer could not do it"}
                return dict(answered, outputs=outputs)

        return Producing()

    def reviewing_agent(self, evidence, verdict):
        """The reviewer: a report, and a claim about THIS checkpoint.

        `review_verdict_from_result` cross-binds the claim against the
        checkpoint's own recorded base, head and tree, so the evidence is read
        from the checkpoint rather than composed here -- a fixture that made
        up three objects would be proving that refusal instead of this path.
        """
        import scripted_agent

        report = {"schema": "baton.review-report/1", "verdict": verdict,
                  "findings": "the scripted reviewer read the frozen line"}
        said = dict(verdict=verdict, base=evidence["base"],
                    head=evidence["head"], tree=evidence["tree"])

        class Judging(scripted_agent.ScriptedAgent):
            def work(self, seen, declared):
                answered = super().work(seen, declared)
                paths = {one["name"]: one["path"] for one in declared}
                with open(os.path.join(scripted_agent.OUTPUT_ROOT,
                                       paths["findings"], "report.json"),
                          "w") as writing:
                    json.dump(report, writing, sort_keys=True)
                outputs = []
                for one in answered["outputs"]:
                    if one["name"] == "findings":
                        one = dict(one, result_metadata={
                            "baton.checkpoint-review/1": dict(said)})
                    outputs.append(one)
                return dict(answered, outputs=outputs)

        return Judging()

    def agent(self):
        """Whichever role is turning, decided by the case."""
        return self._agent()

    # -- the deployment, and the Job the operator asked for -----------------

    def pool(self, name):
        """The deployment, already composed and serving. ONE TIME.

        This is `just start`'s half: the stores exist, the configuration is
        validated, the profile is certified, the session is minted and the pool
        is activated. `TheRoutineStartupInterval` excludes exactly this and
        says so.
        """
        jobs, control = self.stores(name)
        workers = self.proposing_workers()
        self.engine = self.quiescing()
        composed = stage_execution.operations_from(
            self.composed_document(
                checkpoint_profile=self.config["profile_name"],
                line_declared_base=self.BASE, workers=workers),
            jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        return {"jobs": jobs, "control": control, "composed": composed,
                "workers": workers}

    def requested(self, held, task=None, statement=None):
        """One ordinary creation, through the real operation."""
        installed = single_worker._held(held["workers"][0]["deployment"])
        answered = self.create(held["jobs"], installed,
                               task_id=task or self.TASK,
                               statement=statement or self.STATEMENT)
        self.job_id = answered["job_id"]
        held["installed"] = installed
        held["created"] = answered
        return answered

    def ticked(self, held, rounds=16):
        seen = []
        for _ in range(rounds):
            seen.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            seen.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        return seen

    def implemented(self, held, *, disposition="completed"):
        """Round one: the producer's own turn, and the ending that follows."""
        self.driven(held["jobs"], held["composed"], self.job_id)
        stage = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self._agent = lambda: self.producing_agent(disposition)
        self.assertEqual(
            self.turn(held["jobs"], held["control"], held["composed"],
                      "implementation", stage["attempt_id"]), 0)
        held.setdefault("implementation", []).append(stage["attempt_id"])
        self.ticked(held)
        return stage["attempt_id"]

    def attachment_of(self, held, attempt_id):
        worker = self.worker_of(held["composed"], "review")
        return review_cycles.review_for_attempt(
            held["control"], attempt_id=attempt_id,
            generation=worker.stage.deployment.generation_of(attempt_id))

    def judged(self, held, verdict):
        """The reviewer's own turn, over the checkpoint round one froze."""
        review = self.stage_of(held["jobs"], held["composed"], self.job_id,
                               kind="review")
        self.assertEqual(review["state"], "waiting")
        attachment = self.attachment_of(held, review["attempt_id"])
        checkpoint = review_cycles.checkpoint_of(held["control"],
                                                 attachment["checkpoint_id"])
        self._agent = lambda: self.reviewing_agent(checkpoint["evidence"],
                                                   verdict)
        self.assertEqual(
            self.turn(held["jobs"], held["control"], held["composed"],
                      "review", review["attempt_id"]), 0)
        held["review"] = review["attempt_id"]
        held["attachment"] = attachment
        held["checkpoint"] = checkpoint
        self.ticked(held)
        return review["attempt_id"]

    def reviewed(self, verdict, name=None):
        """One created Job through round one and one recorded verdict."""
        held = self.pool(name or ("joined-" + verdict))
        self.requested(held)
        self.implemented(held)
        self.judged(held, verdict)
        return held

    # -- what the stores hold afterwards ------------------------------------

    def rows(self, held, statement):
        return [dict(one) for one in
                held["control"]._connection.execute(statement).fetchall()]

    def task_of(self, held):
        return creation.job_task_of(held["jobs"], self.job_id)

    def verdict_rows(self, held):
        return self.rows(held, "SELECT verdict_id, disposition, "
                               "reviewer_participant, revision, "
                               "head_object FROM checkpoint_verdicts")

    def nothing_was_owner_accepted(self, held):
        """THE BOUNDARY THE FINDING DRAWS, asked of three owners.

        A technical verdict is not an owner decision and not an integration.
        What would show otherwise is a receipt against this Job's proposal, a
        canonical target that moved, or an integration stage that became
        eligible -- so all three are read rather than assumed.
        """
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            self.assertEqual(authority.canonical_target(), self.BASE)
        finally:
            authority.dispose()
        # NO INTEGRATION STAGE EXISTS AT ALL for this template: the resolved
        # workflow is implementation then independent review, which is
        # SCH-1a's "start with implementation followed by independent review".
        self.assertEqual(
            sorted(self.stages(held["jobs"], held["composed"], self.job_id)),
            ["implementation", "review"])
        # AND NO ATTEMPT RAN FOR THE CONFIGURED INTEGRATION WORKER.
        self.assertEqual(
            [one for one in self.rows(held, "SELECT assignment_participant "
                                            "FROM attempts")
             if one["assignment_participant"] == "baton.integrator"], [])


class TheCreatedJobIsReviewedAndCorrected(JoinedWorkflowCase):
    """THE MILESTONE: implementation, independent review, correction round."""

    def test_the_reviewers_verdict_is_read_from_its_own_frozen_output(self):
        """NOBODY IN THIS DEPLOYMENT DECIDED IT.

        The container wrote a report and a claim; the manager read them back
        out of accepted custody and cross-bound them against the checkpoint
        the reviewer was attached to. A fixture that recorded the verdict
        itself would be the deployment reviewing its own Job.
        """
        held = self.reviewed("changes-requested")
        said = review_driver.review_verdict_from_result(
            held["control"], attachment_id=held["attachment"]["attachment_id"])
        self.assertEqual(said["verdict"], "changes-requested")
        self.assertEqual(said["checkpoint_id"],
                         held["checkpoint"]["checkpoint_id"])
        # THE THREE OBJECTS ARE THE CHECKPOINT'S OWN, which is what makes the
        # claim a verdict about this candidate rather than four members
        # somebody wrote.
        for member in ("base", "head", "tree"):
            self.assertEqual(said[member], held["checkpoint"]["evidence"][
                member], member)
        # AND IT IS DURABLE, recorded once, naming the reviewer.
        rows = self.verdict_rows(held)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["disposition"], "changes-requested")
        self.assertEqual(rows[0]["reviewer_participant"], "baton.reviewer")
        self.assertEqual(rows[0]["revision"], 1)

    def test_the_review_was_independent_of_the_round_it_judged(self):
        """INDEPENDENCE, read from the two assignments rather than asserted.

        A different participant, a different attempt, a different container --
        and the reviewer mounted the FROZEN CHECKPOINT rather than the line the
        producer was granted a writer on.
        """
        held = self.reviewed("changes-requested")
        first = held["implementation"][0]
        rows = {one["runtime_attempt_id"]: one for one in
                self.rows(held, "SELECT runtime_attempt_id, "
                                "assignment_participant, runtime_id FROM "
                                "attempts")}
        self.assertNotEqual(first, held["review"])
        self.assertEqual(rows[first]["assignment_participant"], "baton.claude")
        self.assertEqual(rows[held["review"]]["assignment_participant"],
                         "baton.reviewer")
        # TWO CONTAINERS, and they are not the same one reused.
        self.assertNotEqual(rows[first]["runtime_id"],
                            rows[held["review"]]["runtime_id"])
        # THE MOUNT IS THE CHECKPOINT, not the writable line.
        worker = self.worker_of(held["composed"], "review")
        prepared = worker.stage._prepared[held["review"]]
        self.assertEqual(prepared["checkpoint_id"],
                         held["checkpoint"]["checkpoint_id"])
        self.assertIn("checkout", str(prepared["boundary"]["boundary"].source))
        # AND THE ATTACHMENT NAMES THE REVIEWER, over that checkpoint.
        self.assertEqual(held["attachment"]["reviewer_participant"],
                         "baton.reviewer")
        self.assertEqual(held["attachment"]["checkpoint_id"],
                         held["checkpoint"]["checkpoint_id"])

    def test_the_correction_round_is_opened_by_the_loop_and_runs(self):
        """THE ROUND THE VERDICT CALLS FOR, performed by the product.

        `open_correction` is reached through the composition's own `routed`,
        which opens the next round in the Job store from the recorded verdict.
        Nothing here calls it: the ticks after the review turn do, and what
        this reads is a SECOND implementation attempt with a running runtime.
        """
        held = self.reviewed("changes-requested")
        second = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self.assertEqual(second["state"], "waiting")
        self.assertNotEqual(second["attempt_id"], held["implementation"][0])
        self.assertEqual(self.stages(held["jobs"], held["composed"],
                                     self.job_id),
                         {"implementation": "waiting", "review": "blocked"})
        running = {one["runtime_attempt_id"]: one["execution_runtime"]
                   for one in self.rows(held, "SELECT runtime_attempt_id, "
                                              "execution_runtime FROM "
                                              "attempts")}
        self.assertEqual(running[second["attempt_id"]], "running")
        # THE FIRST ROUND AND THE REVIEW ARE BOTH OVER AND BOTH KEPT.
        self.assertEqual(running[held["implementation"][0]], "destroyed")
        self.assertEqual(running[held["review"]], "destroyed")
        # THE LINE IS WRITING AGAIN, on the SAME line, with the reviewed
        # checkpoint still frozen and the attachment ended.
        lines = self.rows(held, "SELECT line_id, state, revision, "
                                "current_checkpoint_id FROM review_lines")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["state"], "writing")
        self.assertEqual(lines[0]["current_checkpoint_id"],
                         held["checkpoint"]["checkpoint_id"])
        self.assertEqual([one["state"] for one in
                          self.rows(held, "SELECT state FROM "
                                          "line_checkpoints")], ["frozen"])
        self.assertEqual([one["state"] for one in
                          self.rows(held, "SELECT state FROM "
                                          "review_attachments")], ["ended"])

    def test_the_correction_round_is_served_the_requested_task(self):
        """THE WHOLE POINT OF THE JOINED PROOF.

        Round two is a new attempt, a new container and a new input root -- and
        the task in it is still the one the operator asked for, read off disk
        rather than from a helper. A correction that silently delivered the
        installed task would be the W363066 defect returning one round later,
        where no earlier case looks.
        """
        held = self.reviewed("changes-requested")
        second = self.stage_of(held["jobs"], held["composed"], self.job_id)
        requested = self.task_of(held)
        self.assertEqual(
            self.published(second["attempt_id"]).decode("utf-8"), requested)
        self.assertNotEqual(self.published(second["attempt_id"]),
                            held["installed"]["task_bytes"])
        # THE STATEMENT, THE ACCEPTANCE AND THE SCOPE the creation recorded.
        resolution = creation.resolution_of(held["jobs"], self.job_id)
        document = json.loads(self.published(second["attempt_id"]))
        self.assertEqual(document["task_id"], self.job_id)
        self.assertIn(resolution["task"]["statement"],
                      document["instructions"])
        for one in resolution["acceptance"]:
            self.assertIn(one, document["instructions"])
        for one in resolution["scope"]["work"]:
            self.assertIn(one, document["instructions"])
        # AND THE DURABLE IDENTITY ROUND TWO WAS CLAIMED AGAINST is the Job's
        # own, not the installed document's.
        worker = self.worker_of(held["composed"], "implementation")
        served = worker._given_for(dict(second, job_id=self.job_id))
        self.assertEqual(
            attempts.recorded_input_of(held["control"],
                                       second["attempt_id"]),
            served["input_manifest"]["manifest_digest"])
        self.assertNotEqual(served["input_manifest"]["manifest_digest"],
                            worker.given["input_manifest"]["manifest_digest"])

    def test_round_ones_evidence_survives_the_correction(self):
        """WHAT THE CORRECTION DID NOT DO.

        The reviewed round's attempt, its retained material, its sealed output
        and its own input root are all still exactly where its ending left
        them -- which is what makes the verdict about it re-readable.
        """
        held = self.reviewed("changes-requested")
        first, review = held["implementation"][0], held["review"]
        rows = {one["runtime_attempt_id"]: one for one in
                self.rows(held, "SELECT runtime_attempt_id, "
                                "worker_disposition, output, cleanup FROM "
                                "attempts")}
        for one in (first, review):
            self.assertEqual(rows[one]["worker_disposition"], "completed", one)
            self.assertEqual(rows[one]["output"], "sealed", one)
            self.assertEqual(rows[one]["cleanup"], "retained", one)
            self.assertIsNotNone(
                attempts.recorded_input_of(held["control"], one), one)
            self.assertEqual(self.published(one).decode("utf-8"),
                             self.task_of(held), one)
        # AND THE VERDICT IS STILL READABLE FROM ITS OWN EVIDENCE.
        self.assertEqual(
            review_driver.review_verdict_from_result(
                held["control"],
                attachment_id=held["attachment"]["attachment_id"])["verdict"],
            "changes-requested")

    def test_a_technical_verdict_is_not_an_owner_decision(self):
        held = self.reviewed("changes-requested")
        self.nothing_was_owner_accepted(held)


class TheRejectedReviewStopsWithoutAcceptingAnything(JoinedWorkflowCase):
    """A rejection is a technical outcome, and it opens no round."""

    def test_a_rejected_verdict_is_recorded_and_opens_no_correction(self):
        held = self.reviewed("rejected")
        rows = self.verdict_rows(held)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["disposition"], "rejected")
        self.assertEqual(rows[0]["reviewer_participant"], "baton.reviewer")
        # THE LINE SAYS SO, and it is not writing again.
        lines = self.rows(held, "SELECT state, revision FROM review_lines")
        self.assertEqual(lines, [{"state": "rejected", "revision": 1}])
        # NO SECOND IMPLEMENTATION ATTEMPT WAS EVER MADE.
        self.assertEqual(
            len(self.rows(held, "SELECT runtime_attempt_id FROM attempts")), 2)
        self.assertEqual(
            self.stage_of(held["jobs"], held["composed"],
                          self.job_id)["attempt_id"],
            held["implementation"][0])

    def test_a_rejection_accepts_and_integrates_nothing(self):
        held = self.reviewed("rejected")
        self.nothing_was_owner_accepted(held)
        # AND THE PRODUCER'S MATERIAL IS STILL IN CUSTODY, which is what makes
        # a rejection reviewable rather than a deletion.
        rows = {one["runtime_attempt_id"]: one for one in
                self.rows(held, "SELECT runtime_attempt_id, cleanup, output "
                                "FROM attempts")}
        self.assertEqual(rows[held["implementation"][0]]["cleanup"],
                         "retained")
        self.assertEqual(rows[held["implementation"][0]]["output"], "sealed")


class TheHeldResultIsAttributedTruthfully(JoinedWorkflowCase):
    """A producer that answers `unable`: held, kept, and nobody's success."""

    def held(self):
        held = self.pool("joined-held")
        self.requested(held, task="joined-held",
                       statement="A task the producer cannot do.")
        self.implemented(held, disposition="unable")
        return held

    def test_the_held_round_is_exceptional_and_names_its_worker(self):
        held = self.held()
        self.assertEqual(self.stages(held["jobs"], held["composed"],
                                     self.job_id),
                         {"implementation": "exceptional", "review":
                          "blocked"})
        rows = self.rows(held, "SELECT runtime_attempt_id, "
                               "execution_runtime, worker_disposition, "
                               "output, cleanup, assignment_participant FROM "
                               "attempts")
        self.assertEqual(len(rows), 1)
        one = rows[0]
        self.assertEqual(one["runtime_attempt_id"],
                         held["implementation"][0])
        # THE DISPOSITION IS THE WORKER'S OWN ANSWER, not a manager's guess,
        # and it is attributed to the participant that ran.
        self.assertEqual(one["worker_disposition"], "unable")
        self.assertEqual(one["assignment_participant"], "baton.claude")
        # ITS MATERIAL IS RETAINED, which is what report-and-hold means.
        self.assertEqual(one["cleanup"], "retained")
        self.assertEqual(one["output"], "sealed")
        self.assertEqual(one["execution_runtime"], "destroyed")

    def test_a_held_result_froze_no_checkpoint_and_was_reviewed_by_nobody(
            self):
        """THE FAILURE MODE THIS CASE EXISTS FOR.

        A held round must not look like a reviewable one. Nothing was frozen,
        no reviewer was attached, no verdict exists, and the line never left
        `idle` -- so there is nothing an operator or a later round could
        mistake for an accepted candidate.
        """
        held = self.held()
        self.assertEqual(self.rows(held, "SELECT state FROM line_checkpoints"),
                         [])
        self.assertEqual(
            self.rows(held, "SELECT state FROM review_attachments"), [])
        self.assertEqual(self.verdict_rows(held), [])
        lines = self.rows(held, "SELECT state, revision, "
                                "current_checkpoint_id FROM review_lines")
        self.assertEqual(lines, [{"state": "idle", "revision": 0,
                                  "current_checkpoint_id": None}])
        self.nothing_was_owner_accepted(held)

    def test_the_held_rounds_own_input_is_still_the_requested_task(self):
        """EVIDENCE PRESERVED means the task it was given, too."""
        held = self.held()
        self.assertEqual(
            self.published(held["implementation"][0]).decode("utf-8"),
            self.task_of(held))
        self.assertIsNotNone(
            attempts.recorded_input_of(held["control"],
                                       held["implementation"][0]))
        document = json.loads(self.published(held["implementation"][0]))
        self.assertIn("A task the producer cannot do.",
                      document["instructions"])


class TheRoutineStartupInterval(JoinedWorkflowCase):
    """DESIGN OBS-0, measured on this path, with its endpoints written down.

    THE INTERVAL. It opens at the instant the operator's selection arrives --
    a task name, a statement, acceptance criteria and a selected work scope,
    and nothing else -- and it closes when the assigned agent ENTERS
    `work()` inside its own runtime, which is the first substantive act of the
    task. The producing agent stamps `time.monotonic()` there itself, so the
    endpoint is the agent's own and not this fixture's guess about it.

    WHAT IS INSIDE, all of it, because OBS-0 says "the whole routine path,
    including input handling, configuration, validation and launch":

      * reading this deployment's installed worker configuration and proving
        it (`single_worker._held`, the static preflight);
      * the whole creation -- template resolution, the full-resolution digest,
        the identity reservation, the Work authorization, the deployment
        binding published and prepared, the per-Job task composed and the
        submission admitted;
      * every scheduler tick that follows: the offer, the claim, the principal
        allocation, the writer grant on the line, the input root composed and
        frozen, the launch document written, the credential delivered and the
        runtime started;
      * the in-image startup: the launch adoption, the exchange, and the
        worker's own preflight up to its first substantive act.

    WHAT IS OUTSIDE, and OBS-0a is why: the ONE-TIME install and the
    deployment's own start. `pool()` opens the stores, validates the
    configuration, certifies the checkpoint profile, mints the session and
    activates the pool -- that is `just start`, performed once per deployment
    and not per task, and SCH-2's scheduler is persistent by design. Nothing
    per-run is outside: there is no packet to engineer, no script to author and
    no manifest to write, which is the clause OBS-0 adds about not excluding
    per-run engineering by calling it task work.

    WHAT THIS IS NOT. The container engine and the provider are this suite's
    declared seams, so the figure contains NO image pull, NO container start,
    NO provider authentication and NO model latency. It is the product's own
    routine path and is reported as exactly that. The supported environment is
    the one this suite runs in: a prepared local deployment on one host, local
    SQLite stores, the deployment-configured checkpoint profile with no version
    control behind it, and no network.

    AND THE SUITE'S OWN DURATION IS NOT THE MEASURE. The figure below is one
    monotonic interval around one task's routine path; `unittest`'s wall clock
    for this file is not reported as a startup figure anywhere.
    """

    BOUND = 60.0

    def measured(self, task, statement):
        """One routine start, clocked from the operator's words."""
        held = self.pool("joined-obs0-" + task)
        # ---- THE INTERVAL OPENS HERE ----------------------------------
        opened = time.monotonic()
        installed = single_worker._held(held["workers"][0]["deployment"])
        answered = self.create(held["jobs"], installed, task_id=task,
                               statement=statement)
        self.job_id = answered["job_id"]
        held["installed"] = installed
        held["created"] = answered
        created = time.monotonic()
        self.driven(held["jobs"], held["composed"], self.job_id)
        launched = time.monotonic()
        stage = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self._agent = lambda: self.producing_agent()
        self.assertEqual(
            self.turn(held["jobs"], held["control"], held["composed"],
                      "implementation", stage["attempt_id"]), 0)
        # ---- AND IT CLOSED WHEN THE AGENT STAMPED ITS OWN ENTRY -------
        self.assertEqual(len(self.produced), 1, self.produced)
        held["interval"] = {
            "whole_seconds": self.produced[0] - opened,
            "creation_seconds": created - opened,
            "scheduling_seconds": launched - created,
            "launch_to_work_seconds": self.produced[0] - launched,
            "attempt_id": stage["attempt_id"]}
        held["implementation"] = [stage["attempt_id"]]
        return held

    def test_the_routine_start_is_within_the_obs0_bound(self):
        held = self.measured("obs0-first", "Measure the routine start.")
        interval = held["interval"]
        # THE AGENT REALLY STARTED, and it is serving the requested task --
        # a figure for a start that delivered the installed document would be
        # measuring the wrong path quickly.
        self.assertEqual(
            self.published(interval["attempt_id"]).decode("utf-8"),
            self.task_of(held))
        self.assertLess(interval["whole_seconds"], self.BOUND,
                        json.dumps(interval, default=str))
        # AND EVERY PART OF IT IS ACCOUNTED FOR: the three legs sum to the
        # whole, so nothing was measured outside what is reported.
        self.assertAlmostEqual(
            interval["creation_seconds"] + interval["scheduling_seconds"]
            + interval["launch_to_work_seconds"],
            interval["whole_seconds"], places=6)

    def test_the_correction_rounds_start_is_within_the_bound_too(self):
        """A CORRECTION IS A ROUTINE START, so it is measured as one.

        OBS-0a: "routine starts, failures and retries MUST NOT require
        operator-authored shell/Python procedures". The correction round is
        the retry case the product performs itself, and the clock here opens
        at the recorded verdict -- the moment this round's input is settled --
        and closes at the second agent's own `work()` entry.
        """
        held = self.pool("joined-obs0-correction")
        self.requested(held, task="obs0-correction",
                       statement="Measure the correction round's start.")
        self.implemented(held)
        self.judged(held, "changes-requested")
        self.assertEqual(len(self.produced), 1)
        # ---- THE SECOND INTERVAL OPENS AT THE RECORDED VERDICT --------
        opened = time.monotonic()
        second = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self.assertNotEqual(second["attempt_id"], held["implementation"][0])
        self._agent = lambda: self.producing_agent()
        self.assertEqual(
            self.turn(held["jobs"], held["control"], held["composed"],
                      "implementation", second["attempt_id"]), 0)
        self.assertEqual(len(self.produced), 2)
        elapsed = self.produced[1] - opened
        self.assertLess(elapsed, self.BOUND, elapsed)
        # AND THE ROUND IT STARTED IS SERVING THE REQUESTED TASK.
        self.assertEqual(
            self.published(second["attempt_id"]).decode("utf-8"),
            self.task_of(held))

    def test_the_measured_path_required_no_authored_procedure(self):
        """OBS-0's OTHER HALF, asserted rather than asserted ABOUT.

        "The routine path MUST NOT require script authoring, test writing or
        bespoke execution-packet engineering." What the operator supplied is
        the four selections below and nothing else: no manifest, no digest, no
        submission document, no launch packet and no path. That is a property
        of the creation request's own shape, so it is read off the recorded
        request rather than described in prose.
        """
        held = self.measured("obs0-shape", "Measure what the caller supplied.")
        resolution = creation.resolution_of(held["jobs"], self.job_id)
        # WHAT THE CALLER SELECTED, as the resolution records it: a statement,
        # acceptance criteria and two scopes. The identities beside the
        # statement are DERIVED and are here as provenance.
        self.assertEqual(sorted(resolution["task"]),
                         ["job_id", "statement", "submission_id", "work_id"])
        self.assertEqual(resolution["task"]["statement"],
                         "Measure what the caller supplied.")
        self.assertEqual(sorted(resolution["scope"]), ["tests", "work"])
        self.assertTrue(resolution["acceptance"])
        # AND NO SELECTION CARRIED A DIGEST, A MANIFEST OR A DOCUMENT. The
        # caller's half of the resolution is these four members; everything
        # the Job needed beyond them the deployment derived.
        for member in ("task", "acceptance", "scope", "overrides"):
            rendered = json.dumps(resolution[member])
            for forbidden in ("sha256:", "input_manifest", "manifest_digest",
                              "launch", "workspace"):
                self.assertNotIn(forbidden, rendered,
                                 "%s names %s" % (member, forbidden))
        # THE DERIVED HALF IS THE DEPLOYMENT'S OWN, and it is what the answer
        # reported back rather than anything the caller stated.
        self.assertTrue(
            resolution["source"]["input_digest"].startswith("sha256:"))
        self.assertEqual(held["created"]["source"]["input_digest"],
                         resolution["source"]["input_digest"])
        self.assertEqual(sorted(resolution["submission"]),
                         ["jobs", "schema", "submission_id"])
        # AND THE IMMUTABLE CALLER INTENT A REPLAY IS KEYED ON names the three
        # identities and a digest of the request -- never a derived fact.
        request = json.loads(
            [one for one in creation.created_job_rows(held["jobs"])
             if one["job_id"] == self.job_id][0]["request"])
        self.assertEqual(sorted(request),
                         ["job_id", "request_digest", "submission_id"])

    def test_the_interval_is_reported_with_its_endpoints(self):
        """The figure, written where a reader can see what it covers."""
        held = self.measured("obs0-report", "Measure and report the start.")
        interval = held["interval"]
        report = {
            "bound_seconds": self.BOUND,
            "opens_at": "the operator's selection arrives (task id, "
                        "statement, acceptance criteria, selected work scope)",
            "closes_at": "the assigned agent enters work() in its own runtime",
            "inside": ["installed worker configuration read and proved",
                       "template resolution, reservation, Work authorization, "
                       "deployment binding published and prepared, per-Job "
                       "task composed, submission admitted",
                       "offer, claim, allocation, writer grant, input root "
                       "composed and frozen, launch document, credential "
                       "delivery, runtime start",
                       "launch adoption, exchange, worker preflight"],
            "outside": ["one-time install and the deployment's own start "
                        "(stores, configuration validation, profile "
                        "certification, session mint, pool activation)"],
            "seams": ["container engine", "provider inside the workload"],
            "measured": interval}
        # THE REPORT IS WRITTEN WHERE THE EVIDENCE DIRECTORY CAN COLLECT IT.
        named = os.environ.get("BATON_V12_OBS0_REPORT")
        if named:
            with open(named, "w") as writing:
                json.dump(report, writing, indent=1, sort_keys=True)
                writing.write("\n")
        self.assertLess(interval["whole_seconds"], self.BOUND)
        self.assertGreater(interval["whole_seconds"], 0.0)


if __name__ == "__main__":
    unittest.main()
