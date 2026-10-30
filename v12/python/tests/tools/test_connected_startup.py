"""W361912 — THE ROUTINE STARTUP INTERVAL, ON THE CONNECTED OWNER PATH.

THIS SUPERSEDES `test_joined_workflow.TheRoutineStartupInterval`, which review
2026-10-27T16-27-58Z found defective in two ways, and both findings were
right:

  R1. That class borrowed `test_job_task_delivery`'s creation ports, which are
      `test_creation`'s `FakeDerivation`, `FakeAuthorization`, `FakeBinding`
      and `FakeOwnership`. So the Work authorization and the deployment
      binding publication were SIMULATED inside an interval whose report
      claimed to include them, and the supported command's own parsing and
      composition were not in it at all. A real operation called with fake
      admission owners is not the whole routine startup path.
  R2. Its correction case called a helper that ticked sixteen times before the
      timer opened, so the routing, the allocation, the preparation and the
      launch it meant to measure had already happened. The reviewer's probe
      observed the second runtime `running` before the clock started.

WHAT IS DIFFERENT HERE, and it is the whole point of the file. The instance is
INSTALLED by the real `bootstrap.main`. The Job is created by the real
`tools.job_manager.main` with the operator's own argv, so the parsing, the
request composition and the dispatch are inside the interval. Behind that
command the admission owners are the REAL adapters:
`creation_ports.DeploymentDerivation` reads this instance's own emitted
configuration, `WorkAuthorization` opens this instance's own Authority and
reuses or creates the Work on it, `NewJobBinding` publishes the Job entry into
`install-inputs.json` and calls `bootstrap.prepare` -- which revalidates the
WHOLE deployment -- and `InstanceOwnership` takes the real instance guard. Then
the pool composed from that same installed configuration serves the Job, and a
real in-image turn runs until the agent's first substantive act.

AND THE CORRECTION CLOCK OPENS BEFORE ANYTHING IT MEASURES. The review turn
returns and the timer opens IMMEDIATELY, with no reconciliation in between --
so the verdict is not yet even recorded. Everything the product then does is
inside: the ending that records the verdict, the routing back to the producer,
the correction round opened in the Job store, the allocation, the writer grant,
the input root, the launch and the second agent's own startup. Review
2026-10-27T16-27-58Z said "if opening earlier is simpler, report that
conservatively and accurately rather than backdating an observation", and this
opens earlier.

THE SEAMS, ALL OF THEM, NAMED HONESTLY AND NOT CALLED OWNERS:

  the container ENGINE is `_ConcurrentEngine`, the repository's own
    multi-container model -- so no image is pulled and no container started;
  the PROVIDER inside the workload is `scripted_agent.ScriptedAgent` with the
    one addition each role needs -- so no model is reached and no credential
    authenticated;
  the CHECKPOINT PROFILE is `test_review_driver.Profile`, the
    deployment-configured profile with no version control behind it, and every
    case installs runners that REFUSE any version-control invocation;
  the installed one-folder RUNTIME is `test_bootstrap`'s stand-in directory
    with `bootstrap._identity_of` patched exactly as that suite patches it.
    Nothing here executes it, and it is OUTSIDE every interval below: that the
    real frozen command creates and replays ordinary Jobs is W366246's own
    accepted proof (`findings/finding-packaged-template-creation`), which this
    file reuses rather than re-running.

WHAT THIS DOES NOT ESTABLISH, said here so no summary has to infer it. The
correction round is measured to the second agent's first substantive act; a
COMPLETED corrected candidate and a SECOND review are not reached. The proposal
and the verdict are synthetic deterministic content, not an applicable change
and not a live model's judgment.
"""
import json
import os
import time
import unittest

from baton_v12.contracts import digest
from baton_v12.worker_manager import launch
from baton_v12.job_manager import (JobStore, creation, reconcile,
                                   review_driver, status as projected, sweep)
from baton_v12.worker_manager import ControlStore, attempts, review_cycles

from tools import single_worker, stage_execution

from tests.job_manager import fixtures
# THE MODULES AND NOT THEIR CLASSES: a module-level name bound to a case class
# is one unittest collects, so its assertions would re-run under this file.
from tests.tools import test_bootstrap as _bootstrap
from tests.tools import test_connected_creation as _connected
from tests.tools import test_job_task_delivery as _delivery
from tests.tools import test_stage_execution as _execution


class ConnectedStartupCase(_connected.ConnectedCreationCase):
    """One really installed instance, the real command, and the real loop."""

    BASE = "a" * 40
    HEAD = "b" * 40
    PROPOSAL_OUTPUTS = _delivery.TheReviewStageRunsThroughThePoolServingLoop\
        .PROPOSAL_OUTPUTS
    BOUND = 60.0

    def setUp(self):
        super().setUp()
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()
        self.produced = []
        self._judging = None

    def no_version_control(self):
        """Refuse every version-control process for the rest of this case.

        `test_job_task_delivery`'s own guard, borrowed verbatim in behaviour:
        it RAISES rather than skipping, so a case that spawned version control
        fails instead of quietly doing it.
        """
        import subprocess

        held_run, held_popen = subprocess.run, subprocess.Popen

        def refuse(argv):
            first = str(argv[0]).split("/")[-1] if argv else ""
            if first == "git":
                raise AssertionError(
                    "this case spawned version control: "
                    + " ".join(str(one) for one in argv))

        def run(argv, *arguments, **named):
            refuse(argv)
            return held_run(argv, *arguments, **named)

        def popen(argv, *arguments, **named):
            refuse(argv)
            return held_popen(argv, *arguments, **named)

        subprocess.run, subprocess.Popen = run, popen
        self.addCleanup(setattr, subprocess, "Popen", held_popen)
        self.addCleanup(setattr, subprocess, "run", held_run)

    # -- the one-time install, and everything it configures -----------------

    def proposal_manifest(self, worker):
        """The manifest a Job whose result is PUBLISHED has to declare.

        Composed from the INSTALLED worker's own manifest rather than from a
        fixture's: three outputs, each at its own name, none required, with
        the proposal typed `git-change-proposal` -- which is what
        `publish_candidate` requires exactly one of.
        """
        import copy

        manifest = copy.deepcopy(worker["deployment"]["input_manifest"])
        held = manifest["outputs"][0]
        manifest["outputs"] = [
            dict(held, name=name, type=kind, path=name, required=False)
            for name, kind in self.PROPOSAL_OUTPUTS]
        manifest.pop("manifest_digest", None)
        manifest["manifest_digest"] = digest(manifest)
        return manifest

    def publishing_workers(self):
        """Every installed worker, carrying that one manifest."""
        held = _bootstrap.ValidFixture.workers(self)
        manifest = self.proposal_manifest(held[0])
        for one in held:
            one["deployment"]["input_manifest"] = manifest
        return held

    def deployment(self):
        """INSTALL ONCE, then serve. Everything here is outside every clock.

        OBS-0a is the authority for that: privileged provisioning, storage and
        narrow admission provisioning are ONE-TIME INSTALLATION, and routine
        starts must not repeat them. What this does is the install and
        `just start`: the installer composes the Authority, the Work, the
        routes, the grants, the storage layout and the configuration; then the
        stores are opened and the pool is activated. A deployment does this
        once and then serves every Job that arrives.
        """
        from baton_v12.authority import Authority

        self.installed(checkpoint_profile=self.profile_seam.name,
                       workers=self.publishing_workers())
        configured = self.configuration()
        # THE CANONICAL TARGET THE PUBLICATION BINDS TO, set once at install
        # time as an operator does. `retain_proposal` reads it and
        # `publish_candidate` binds to it.
        authority = Authority.open(
            self.owned["authority_store"],
            expected_authority_uuid=self.owned["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.BASE)
        finally:
            authority.dispose()
        jobs = JobStore.open(self.owned["job_store"],
                             authority_uuid=self.owned["authority_uuid"],
                             incarnation="serving-1",
                             clock=lambda: fixtures.NOW)
        self.addCleanup(jobs.close)
        control = ControlStore.open(self.owned["control_store"],
                                   incarnation="manager-serving",
                                   clock=lambda: fixtures.NOW)
        self.addCleanup(control.close)
        self.engine = _execution._ConcurrentEngine()
        composed = stage_execution.operations_from(
            configured, jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: "a-secret",
            clock=lambda: fixtures.NOW,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        return {"jobs": jobs, "control": control, "composed": composed,
                "configured": configured}

    # -- the two workers -----------------------------------------------------

    def agent(self):
        if self._judging is not None:
            return self._judging
        return self.producing_agent()

    def producing_agent(self):
        """The producer, which stamps its own first substantive act."""
        import scripted_agent

        base, head, produced = self.BASE, self.HEAD, self.produced

        class Producing(scripted_agent.ScriptedAgent):
            def work(self, seen, declared):
                # THE CLOSING ENDPOINT, TAKEN BY THE AGENT ITSELF. OBS-0's
                # endpoint is "the assigned agent starting substantive task
                # work", so the stamp belongs here rather than in a caller
                # that can only observe the turn returning.
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
                        one = dict(one, result_metadata={
                            "baton.git-proposal/1": {
                                "base": base, "head": head,
                                "transport": "objects.bundle",
                                "recap": "a synthetic candidate"}})
                    outputs.append(one)
                return dict(answered, outputs=outputs)

        return Producing()

    def reviewing_agent(self, evidence, verdict="changes-requested"):
        """The reviewer, claiming about THIS checkpoint's own three objects."""
        import scripted_agent

        report = {"schema": "baton.review-report/1", "verdict": verdict,
                  "findings": "the scripted reviewer read the frozen line"}
        said = {"verdict": verdict, "base": evidence["base"],
                "head": evidence["head"], "tree": evidence["tree"]}

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

    # -- the loop, the turn and the projection ------------------------------

    def worker_of(self, composed, role):
        held = [one for one in composed.workers if one["role"] == role]
        self.assertEqual(len(held), 1, role)
        return held[0]["operations"]._worker

    def turn(self, held, role, attempt_id, job_id):
        """One real in-image turn over the composition's own mounted roots."""
        import baton_worker
        import scripted_agent

        worker = self.worker_of(held["composed"], role)
        roots = dict(worker.stage._prepared[attempt_id]["boundary"]["roots"])
        delivered = single_worker.launch.adopt(
            worker.given["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=worker.given["launch_contract"], role=role,
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            job_execution=single_worker.job_execution_reader(held["jobs"])(
                job_id=job_id, attempt_id=attempt_id,
                runtime_input_digest=attempts.recorded_input_of(
                    held["control"], attempt_id),
                runtime_policy_digest=worker.given["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(
                held["control"]))
        kept = []
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", roots["inputs"]),
                (baton_worker, "OUTPUT_ROOT", roots["workspace"]),
                (scripted_agent, "OUTPUT_ROOT", roots["workspace"])):
            kept.append((module, name, getattr(module, name)))
            setattr(module, name, value)
        try:
            return baton_worker.serve_exchange(
                self.agent(), delivered.document,
                launch.payload_of(delivered.document)["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root)
        finally:
            for module, name, value in kept:
                setattr(module, name, value)

    def ticked(self, held, rounds=16):
        for _ in range(rounds):
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)

    def states(self, held, job_id):
        for one in projected(held["jobs"], held["composed"],
                             observed_at=fixtures.NOW)["jobs"]:
            if one["job_id"] == job_id:
                return {stage["kind"]: stage["state"]
                        for stage in one["stages"]}
        self.fail("no projected Job " + repr(job_id))

    def stage_of(self, held, job_id, kind="implementation"):
        for one in projected(held["jobs"], held["composed"],
                             observed_at=fixtures.NOW)["jobs"]:
            if one["job_id"] == job_id:
                for stage in one["stages"]:
                    if stage["kind"] == kind:
                        return stage
        self.fail("no %s stage for %r" % (kind, job_id))

    def driven(self, held, job_id, kind="implementation", want="waiting",
               rounds=14):
        for _ in range(rounds):
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
            if self.states(held, job_id).get(kind) == want:
                return self.stage_of(held, job_id, kind)
        self.fail("%s's %s never reached %r: %s"
                  % (job_id, kind, want, self.states(held, job_id)))

    def delivered_task(self, held, attempt_id):
        place = os.path.join(
            held["configured"]["workers"][0]["deployment"]
            ["workspace_storage"], attempt_id, "inputs",
            single_worker.TASK_DOCUMENT)
        with open(place, "rb") as reading:
            return reading.read().decode("utf-8")

    # -- the measurements ----------------------------------------------------

    def initial(self, task="startup-a",
                statement="Measure the whole routine start."):
        """One routine start, clocked from the operator's words.

        THE CLOCK OPENS BEFORE THE COMMAND IS EVEN PARSED. `argv` is composed
        inside the interval too, because composing the operator's own command
        line is part of what an operator does and excluding it would be the
        hidden-preparation OBS-0 forbids.
        """
        held = self.deployment()
        opened = time.monotonic()
        argv = self.argv(task=task, statement=statement)
        from tools import job_manager
        import io

        said = io.StringIO()
        self.assertEqual(job_manager.main(argv, stream=said), 0,
                         said.getvalue())
        answered = json.loads(said.getvalue())
        admitted = time.monotonic()
        stage = self.driven(held, answered["job_id"])
        launched = time.monotonic()
        self.assertEqual(
            self.turn(held, "implementation", stage["attempt_id"],
                      answered["job_id"]), 0)
        self.assertEqual(len(self.produced), 1, self.produced)
        held["job_id"] = answered["job_id"]
        held["created"] = answered
        held["first"] = stage["attempt_id"]
        held["initial"] = {
            "whole_seconds": self.produced[0] - opened,
            "command_and_admission_seconds": admitted - opened,
            "scheduling_and_launch_seconds": launched - admitted,
            "runtime_startup_seconds": self.produced[0] - launched,
            "attempt_id": stage["attempt_id"]}
        return held

    def correction(self, held):
        """The correction round, clocked from BEFORE the verdict is recorded.

        `judged` here does the review turn and NOTHING ELSE -- no tick -- so
        when the clock opens the verdict is still only bytes in a frozen
        result. R2's defect was opening it sixteen ticks later.
        """
        review = self.driven(held, held["job_id"], kind="review")
        worker = self.worker_of(held["composed"], "review")
        attachment = review_cycles.review_for_attempt(
            held["control"], attempt_id=review["attempt_id"],
            generation=worker.stage.deployment.generation_of(
                review["attempt_id"]))
        checkpoint = review_cycles.checkpoint_of(held["control"],
                                                 attachment["checkpoint_id"])
        self._judging = self.reviewing_agent(checkpoint["evidence"])
        self.assertEqual(
            self.turn(held, "review", review["attempt_id"],
                      held["job_id"]), 0)
        self._judging = None
        # ---- THE CLOCK OPENS HERE, BEFORE ANY RECONCILIATION -----------
        opened = time.monotonic()
        # NOTHING IS RECORDED YET, and this proves it rather than claiming it:
        # the verdict relation is empty at the instant the clock opens.
        self.assertEqual(
            [dict(one) for one in held["control"]._connection.execute(
                "SELECT verdict_id FROM checkpoint_verdicts").fetchall()], [])
        second = self.driven(held, held["job_id"])
        self.assertNotEqual(second["attempt_id"], held["first"])
        routed = time.monotonic()
        self.assertEqual(
            self.turn(held, "implementation", second["attempt_id"],
                      held["job_id"]), 0)
        self.assertEqual(len(self.produced), 2, self.produced)
        held["review"] = review["attempt_id"]
        held["attachment"] = attachment
        held["checkpoint"] = checkpoint
        held["second"] = second["attempt_id"]
        held["correction"] = {
            "whole_seconds": self.produced[1] - opened,
            "verdict_to_launch_seconds": routed - opened,
            "runtime_startup_seconds": self.produced[1] - routed,
            "attempt_id": second["attempt_id"]}
        return held


class TheInitialRoutineStartIsMeasured(ConnectedStartupCase):
    """The whole path, from the operator's command to the agent's first act."""

    def test_the_initial_start_is_within_the_obs0_bound(self):
        held = self.initial()
        interval = held["initial"]
        self.assertLess(interval["whole_seconds"], self.BOUND,
                        json.dumps(interval))
        # THE LEGS SUM TO THE WHOLE, so nothing was measured outside what is
        # reported and nothing reported was measured twice.
        self.assertAlmostEqual(
            interval["command_and_admission_seconds"]
            + interval["scheduling_and_launch_seconds"]
            + interval["runtime_startup_seconds"],
            interval["whole_seconds"], places=6)
        # AND THE START IT MEASURED DELIVERED THE REQUESTED TASK -- a figure
        # for a start that served the installed document would be measuring
        # the wrong path quickly.
        self.assertEqual(self.delivered_task(held, held["first"]),
                         creation.job_task_of(held["jobs"], held["job_id"]))

    def test_the_admission_inside_the_interval_was_the_real_owners(self):
        """R1'S CORRECTION, ASSERTED RATHER THAN DESCRIBED.

        The previous measurement's report claimed the Work authorization and
        the deployment binding publication were inside it while fakes stood in
        for both. So this case reads the EFFECTS those owners leave behind,
        off disk and out of the Authority, after an interval that contained
        them -- which no fake could have produced.
        """
        held = self.initial(task="startup-owners",
                            statement="Prove the owners were real.")
        job_id = held["job_id"]
        # THE DEPLOYMENT BINDING WAS PUBLISHED into this instance's own
        # emitted configuration, and additively into the install document
        # `bootstrap.prepare` consumes -- which is the publication a fake
        # records and does not perform.
        bound = self.bindings()
        self.assertIn(job_id, bound)
        self.assertEqual(bound[job_id]["job_work_id"], self.work)
        self.assertEqual([one["job_id"]
                          for one in self.install_document()["jobs"]],
                         ["job-a", job_id])
        # THE WORK IS THE INSTANCE'S OWN, on the instance's own Authority.
        from baton_v12.authority import Authority

        authority = Authority.open(
            self.owned["authority_store"],
            expected_authority_uuid=self.owned["authority_uuid"])
        try:
            self.assertEqual(
                authority.project_work(self.work)["status"], "open")
        finally:
            authority.dispose()
        # AND THE CREATION WAS RECORDED BY THE MANAGER, with the derived
        # identities the operator never supplied.
        row = [one for one in creation.created_job_rows(held["jobs"])
               if one["job_id"] == job_id]
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0]["state"], "created")
        self.assertTrue(
            held["created"]["source"]["input_digest"].startswith("sha256:"))
        self.assertEqual(held["created"]["servable"],
                         {"implementation": ["impl-a"],
                          "review": ["review-a"]})

    def test_the_measured_path_required_no_authored_procedure(self):
        """OBS-0's OTHER HALF: no script, no test, no packet.

        Read off the operator's own argv and the recorded resolution rather
        than described: the command line carries selections and store paths
        and NO digest, manifest, document or launch packet, and the resolution
        the manager recorded says the same about the caller's half.
        """
        held = self.initial(task="startup-shape",
                            statement="Prove nothing was authored.")
        argv = self.argv(task="startup-shape",
                         statement="Prove nothing was authored.")
        rendered = " ".join(argv)
        for forbidden in ("sha256:", "--input-digest", "--policy-digest",
                          "--manifest", "--submission", "--packet",
                          "--profile-digest"):
            self.assertNotIn(forbidden, rendered, forbidden)
        resolution = creation.resolution_of(held["jobs"], held["job_id"])
        for member in ("task", "acceptance", "scope", "overrides"):
            said = json.dumps(resolution[member])
            for forbidden in ("sha256:", "input_manifest", "manifest_digest",
                              "launch", "workspace"):
                self.assertNotIn(forbidden, said,
                                 "%s names %s" % (member, forbidden))
        # EVERY IDENTITY THE JOB NEEDED WAS DERIVED BY THE DEPLOYMENT.
        self.assertTrue(
            resolution["source"]["input_digest"].startswith("sha256:"))
        self.assertEqual(resolution["source"]["input_digest"],
                         held["created"]["source"]["input_digest"])


class TheCorrectionStartIsMeasured(ConnectedStartupCase):
    """R2's correction: the clock opens before the verdict is even recorded."""

    def test_the_correction_start_is_within_the_obs0_bound(self):
        held = self.correction(self.initial(
            task="startup-correction",
            statement="Measure the correction round's start."))
        interval = held["correction"]
        self.assertLess(interval["whole_seconds"], self.BOUND,
                        json.dumps(interval))
        self.assertAlmostEqual(
            interval["verdict_to_launch_seconds"]
            + interval["runtime_startup_seconds"],
            interval["whole_seconds"], places=6)
        # THE SECOND ROUND IS A SECOND ATTEMPT, and the task in its own input
        # root is still the one the operator asked for.
        self.assertNotEqual(held["second"], held["first"])
        self.assertEqual(self.delivered_task(held, held["second"]),
                         creation.job_task_of(held["jobs"], held["job_id"]))

    def test_everything_the_correction_needed_happened_inside_the_clock(self):
        """WHAT THE INTERVAL CONTAINED, read from the stores afterwards.

        The opening assertion in `correction()` establishes that the verdict
        relation was EMPTY when the clock opened. These are the effects that
        exist when it closes, so each of them happened inside it.
        """
        held = self.correction(self.initial(
            task="startup-contents",
            statement="Prove what the clock contained."))
        # THE VERDICT WAS RECORDED inside the interval.
        rows = [dict(one) for one in held["control"]._connection.execute(
            "SELECT disposition, reviewer_participant, revision FROM "
            "checkpoint_verdicts").fetchall()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["disposition"], "changes-requested")
        self.assertEqual(rows[0]["reviewer_participant"], "baton.reviewer")
        # THE CORRECTION ROUND WAS OPENED and the line writes again.
        lines = [dict(one) for one in held["control"]._connection.execute(
            "SELECT state, current_checkpoint_id FROM review_lines"
        ).fetchall()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["state"], "writing")
        self.assertEqual(lines[0]["current_checkpoint_id"],
                         held["checkpoint"]["checkpoint_id"])
        # AND THE SECOND RUNTIME WAS STARTED inside it, which is the fact R2
        # found already true before the old clock opened.
        running = {one["runtime_attempt_id"]: one["execution_runtime"]
                   for one in held["control"]._connection.execute(
                       "SELECT runtime_attempt_id, execution_runtime FROM "
                       "attempts").fetchall()}
        # ROUND TWO'S RUNTIME IS STILL RUNNING, which is exactly right: the
        # clock closed at its agent's first substantive act and nothing has
        # ticked since, so its own ending has not been driven. R2's defect was
        # that this row was already in this state BEFORE the old clock opened.
        self.assertEqual(running[held["second"]], "running")
        self.assertEqual(running[held["first"]], "destroyed")
        self.assertEqual(running[held["review"]], "destroyed")
        self.assertEqual(len(running), 3)

    def test_the_verdict_was_the_reviewers_own_on_the_connected_path(self):
        """The same independence the pool suite proves, over a real install."""
        held = self.correction(self.initial(
            task="startup-independent",
            statement="Prove the reviewer was independent here too."))
        said = review_driver.review_verdict_from_result(
            held["control"],
            attachment_id=held["attachment"]["attachment_id"])
        self.assertEqual(said["verdict"], "changes-requested")
        for member in ("base", "head", "tree"):
            self.assertEqual(said[member],
                             held["checkpoint"]["evidence"][member], member)
        rows = {one["runtime_attempt_id"]: one["assignment_participant"]
                for one in held["control"]._connection.execute(
                    "SELECT runtime_attempt_id, assignment_participant FROM "
                    "attempts").fetchall()}
        self.assertEqual(rows[held["first"]], "baton.impl-a")
        self.assertEqual(rows[held["review"]], "baton.reviewer")
        self.assertEqual(rows[held["second"]], "baton.impl-a")


class TheIntervalsAreReportedWithTheirEndpoints(ConnectedStartupCase):
    """BOTH intervals, written where the evidence directory can collect them.

    Review 2026-10-27T16-27-58Z: "Retain a durable correction interval as well
    as the initial interval; the current obs0-interval.json contains only the
    initial measured result." Both are here, in one document, each with its
    own endpoints.
    """

    SEAMS = ["container engine (_ConcurrentEngine; no image pull, no "
             "container start)",
             "provider inside the workload (scripted_agent; no model, no "
             "credential authentication)",
             "checkpoint profile with no version control behind it; every "
             "case refuses any version-control invocation",
             "the installed one-folder runtime is test_bootstrap's stand-in "
             "directory and nothing here executes it; that the real frozen "
             "command creates and replays ordinary Jobs is W366246's accepted "
             "proof, reused rather than re-run"]

    def test_both_intervals_are_within_the_bound_and_reported(self):
        held = self.correction(self.initial(
            task="startup-report",
            statement="Measure and report both starts."))
        report = {
            "schema": "baton.v12.obs0-interval-report/2",
            "supersedes": "evidence/claim-366433/obs0-interval.json, whose "
                          "single interval was measured with fake admission "
                          "owners (R1) and whose correction figure was never "
                          "recorded (R2)",
            "bound_seconds": self.BOUND,
            "supported_environment": "one host; a prepared local deployment "
                                     "installed once by the real bootstrap; "
                                     "local SQLite stores; no network",
            "one_time_and_outside_every_interval": [
                "the install: Authority, Work, routes, grants, storage "
                "layout, deployment configuration, selector",
                "the deployment's own start: stores opened, configuration "
                "validated, checkpoint profile certified, session minted, "
                "pool activated"],
            "seams": self.SEAMS,
            "initial": {
                "opens_at": "immediately before the operator's command line "
                            "is composed and tools.job_manager.main is "
                            "entered",
                "closes_at": "the assigned agent enters work() in its own "
                             "runtime, stamped by the agent",
                "inside": [
                    "command parsing, request composition and dispatch",
                    "DeploymentDerivation reading this instance's emitted "
                    "configuration",
                    "WorkAuthorization on this instance's own Authority",
                    "NewJobBinding publishing into install-inputs.json and "
                    "bootstrap.prepare revalidating the whole deployment",
                    "InstanceOwnership taking the real instance guard",
                    "create_template_job: template resolution, full "
                    "resolution digest, identity reservation, per-Job task "
                    "composed, submission admitted",
                    "every scheduler tick: offer, claim, allocation, writer "
                    "grant, input root composed and frozen, launch document, "
                    "credential delivery, runtime start",
                    "launch adoption, exchange and worker preflight"],
                "measured": held["initial"]},
            "correction": {
                "opens_at": "immediately after the review turn returns and "
                            "BEFORE any reconciliation; the verdict relation "
                            "is asserted empty at this instant, so the "
                            "verdict is not yet recorded",
                "closes_at": "the second agent enters work() in its own "
                             "runtime, stamped by the agent",
                "inside": [
                    "the review ending: seal, intake, retention, the verdict "
                    "read from frozen output and recorded",
                    "routing the Work back to the producer's own route",
                    "open_correction advancing the Job to its next round",
                    "allocation, writer grant on the released line, input "
                    "root, launch document, credential delivery, runtime "
                    "start",
                    "launch adoption, exchange and worker preflight"],
                "measured": held["correction"]},
            "not_established": [
                "a completed corrected candidate and a second review",
                "applicable version-control changes; the proposal and the "
                "verdict are synthetic deterministic content",
                "live model judgment, provider authentication or container "
                "start latency"]}
        named = os.environ.get("BATON_V12_OBS0_REPORT")
        if named:
            with open(named, "w") as writing:
                json.dump(report, writing, indent=1, sort_keys=True)
                writing.write("\n")
        for which in ("initial", "correction"):
            measured = report[which]["measured"]
            self.assertGreater(measured["whole_seconds"], 0.0, which)
            self.assertLess(measured["whole_seconds"], self.BOUND, which)


if __name__ == "__main__":
    unittest.main()
