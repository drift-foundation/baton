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

THE TIMING IS NOT HERE, AND THAT IS A CORRECTION. An earlier version of this
file carried `TheRoutineStartupInterval`, and review 2026-10-27T16-27-58Z found
it defective twice over: this fixture's creation ports are `test_creation`'s
`FakeDerivation`/`FakeAuthorization`/`FakeBinding`/`FakeOwnership`, so an
interval measured here cannot contain the Work authorization or the deployment
binding publication its report claimed; and its correction case opened its
clock after a helper had already ticked the correction round into a running
runtime. Both findings were right. The measurement now lives in
`tests/tools/test_connected_startup.py`, over a really installed instance, the
real `tools.job_manager.main` and the real admission adapters, with the
correction clock opening before the verdict is even recorded.

WHAT THIS FILE STILL OWNS is the WORKFLOW: the verdict, the correction round,
the rejection and the held result, with their evidence and their attribution.
Those cases never depended on the admission owners being real -- what they
read is the loop, the ending, the attachment and the stores -- and review
2026-10-27T16-27-58Z verified all fifteen of them independently.
"""
import json
import os
import time
import unittest

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


if __name__ == "__main__":
    unittest.main()
