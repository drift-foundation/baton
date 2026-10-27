"""W364834 — A FRESH ATTEMPT AT A TEMPLATE-CREATED JOB KEEPS ITS TASK.

The parent's connected creation reported this gap and the FINDING names the
two code facts behind it: `fresh_attempt._bound` asked the selector without a
task, and `creation.job_task_of` read `template_jobs` alone -- a relation a
retry identity has no row in. A retried template Job submits the prior Job's
input digest, carried verbatim by `_composed`, which for a created Job IS its
own task's Job-scoped identity. So before this Work every reader answered the
INSTALLED task: unservable at admission, and refused as "another bootstrap
input" if it ever reached a worker.

WHAT IS REAL HERE. A real Job store and control store; the real
`creation.create_template_job`; the real pool composed by
`stage_execution.operations_from` with its own serving loop; a real engine
refusal that ends the first attempt; the real `fresh_attempt.admit` over that
store and those real manager operations; and the real lineage read. The
CHECKPOINT PROFILE is `test_review_driver.Profile` -- the
deployment-configured profile with no version control behind it -- and every
case installs process runners that refuse any version-control invocation.

WHAT STANDS IN, NAMED. The three `fresh_attempt` ports that are not this
outcome's: the host exclusion, the Work authorization and the deployment
binding, which are `test_fresh_attempt`'s own strict stand-ins. The binding
is the one that matters here and it is strict in the way that counts: it
RECORDS the task it was asked with, so a case can assert what travelled
rather than that an answer came back.
"""

import io
import json
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import creation, fresh_attempt, reconcile, sweep
from baton_v12.worker_manager import attempts

from tools import single_worker, stage_execution

from tests.job_manager import fixtures
from tests.job_manager import test_fresh_attempt as retry_fixtures
from tests.job_manager.test_fresh_attempt import (FakeAuthorization,
                                                  FakeBinding, FakeExclusion,
                                                  FakeOwnership)
from tests.tools.test_job_task_delivery import (
    TheCreatedJobRunsThroughThePoolServingLoop as pool,
    TheReviewStageRunsThroughThePoolServingLoop as reviewing)
from tests.tools.test_stage_execution import (ComposedOneJobCase,
                                              ServingCase,
                                              _ConcurrentEngine)
from tests.tools.test_single_worker import Engine


class RetryLineageCase(ServingCase):
    """One created Job, failed by the engine, and the retry at it."""

    # THE HELPERS ARE BORROWED AND THE CASES ARE NOT.
    no_version_control = pool.no_version_control
    identity_for = pool.identity_for
    creation_ports = pool.creation_ports
    create = pool.create
    driven = pool.driven
    stages = pool.stages
    stage_of = pool.stage_of
    published = pool.published

    def worker_of(self, composed, role, worker_id=None, attempt_id=None):
        """One composed worker: by exact id, by the attempt it prepared, or
        the single one of its role.

        The pool helper answers by ROLE, and a two-producer pool has two
        implementation workers -- so this takes the two other ways a case can
        mean one of them. `attempt_id` is how the borrowed `turn` resolves it:
        the worker that PREPARED an attempt is the one whose launch document
        and roots that turn is over, which is `job_execution_for`'s own rule.
        """
        lane = [one for one in composed.workers if one["role"] == role]
        if worker_id is not None:
            held = [one for one in lane if one["worker_id"] == worker_id]
        else:
            attempt = attempt_id or getattr(self, "_turning_attempt", None)
            held = [one for one in lane
                    if attempt in (getattr(
                        getattr(one["operations"]._worker, "stage", None),
                        "_prepared", None) or {})] if attempt else []
            held = held or lane
        self.assertEqual(len(held), 1,
                         [one["worker_id"] for one in held] + [role, worker_id,
                                                              attempt_id])
        return held[0]["operations"]._worker
    # THE REAL IN-IMAGE TURN, and the engine that can carry an ending.
    turn = reviewing.turn
    quiescing = ComposedOneJobCase.quiescing

    def setUp(self):
        super().setUp()
        from tests.job_manager.test_review_driver import Profile

        self.profile_seam = Profile()
        self.no_version_control()
        # THE STAND-IN PORTS ANSWER FOR THIS CASE'S OWN DISPOSABLE INSTANCE.
        # `fresh_attempt._one_instance` refuses ports that answer for another
        # deployment -- the rule a fixture declaring a fictional path would
        # break -- and `test_fresh_attempt` carries this exact device for the
        # same reason.
        held = retry_fixtures.CURRENT.get("identity")
        retry_fixtures.CURRENT["identity"] = self.identity_for()
        self.addCleanup(retry_fixtures.CURRENT.__setitem__, "identity", held)
        self.exclusion = FakeExclusion()
        self.binding = FakeBinding()

    def agent(self):
        """An in-image worker that FAULTS, which is the pilot's own shape.

        A fresh attempt replaces an execution that is OVER -- the admission
        refuses one beside a stage still owed an act, in as many words -- so
        the first attempt has to END, and a faulted turn is the ending the
        pilot measured: the container writes a terminal and the stage
        projects `exceptional`.

        IT DOES NOT RELEASE THE POOL'S CAPACITY, and an earlier version of
        this comment said it did. Review 2026-10-27T00-18-27Z corrected that:
        a faulted attempt's material is PRESERVED (DESIGN ART-7), so its
        allocation stays held and a retry bound to the same producer is
        refused for "every effective worker/principal capacity is reserved or
        recovery-required". That retention is the product working; the
        fixture that gets a retry to its own runtime is the configured SPARE
        PRODUCER in `TheRetriedJobReachesItsOwnRuntimes`, which leaves the
        first attempt's allocation and evidence exactly as they are.
        """
        import scripted_agent

        class Unable(scripted_agent.ScriptedAgent):
            """A worker that ANSWERS it could not do it.

            The pilot's own shape -- "the implementation ends `unable`" --
            and the one the recovery needs: `finalize_quiescent_assignment`
            refuses an attempt whose "worker disposition is 'none'", because
            finalization ends the assignment of a worker that has ALREADY
            answered. A turn that merely raises leaves a `faulted` terminal
            with no disposition, which is a different ending and not one an
            operator may finalize. Every declared output is answered
            `missing-optional`, which the manifest permits because none of
            them is required.
            """

            def work(self, seen, declared):
                # THE SCRIPTED TREES ARE STILL WRITTEN, because an ending
                # needs something to take into custody: "a retention
                # decision names at least one artifact", and an `unable`
                # answer with every output missing cannot be concluded at
                # all. What is withheld is the PROPOSAL -- this worker
                # produced no candidate, which is what `unable` means -- and
                # the manifest permits that because no output is required.
                answered = super().work(seen, declared)
                kinds = {one["name"]: one["type"] for one in declared}
                outputs = []
                for one in answered["outputs"]:
                    if kinds[one["name"]] == "git-change-proposal":
                        one = dict(one, status="missing-optional")
                    outputs.append(one)
                return {"disposition": "unable", "outputs": outputs,
                        "recap": "the scripted worker could not do it"}

        return Unable()

    def failing_pool(self, task_id="retry-first",
                     statement="The task a retry must keep."):
        """One created Job whose first attempt ends exceptional, for real."""
        jobs, control = self.stores("retry-lineage")
        installed = single_worker._held(
            self.worker("implementation")["deployment"])
        answered = self.create(jobs, installed, task_id=task_id,
                               statement=statement)
        self.job_id = answered["job_id"]
        self.engine = self.quiescing()
        composed = stage_execution.operations_from(
            self.composed_document(
                checkpoint_profile=self.config["profile_name"]),
            jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        self.driven(jobs, composed, self.job_id)
        self.first_attempt = self.stage_of(jobs, composed,
                                           self.job_id)["attempt_id"]
        # THE REAL TURN, which faults; then the ordinary ticks that end it.
        self.turn(jobs, control, composed, "implementation",
                  self.first_attempt)
        for _ in range(12):
            sweep(jobs, composed, now=fixtures.NOW)
            reconcile(jobs, composed, now=fixtures.NOW)
            if self.stages(jobs, composed,
                           self.job_id)["implementation"] == "exceptional":
                break
        self.assertEqual(
            self.stages(jobs, composed, self.job_id),
            {"implementation": "exceptional", "review": "blocked"})
        return {"jobs": jobs, "control": control, "composed": composed,
                "created": answered, "installed": installed}

    def retried(self, held, prior=None, **named):
        """One fresh attempt, through the real admission."""
        operands = {"prior_job_id": prior or self.job_id,
                    "exclusion": self.exclusion,
                    "authorization": FakeAuthorization(),
                    "binding": self.binding, "ownership": FakeOwnership()}
        operands.update(named)
        return fresh_attempt.admit(held["jobs"], held["composed"], **operands)

    def task_of(self, held, job_id):
        return creation.job_task_of(held["jobs"], job_id)


class TheAdmissionCarriesTheTask(RetryLineageCase):
    """What travels to the selector, which is where the retry used to die."""

    def test_the_priors_own_task_reaches_the_servability_question(self):
        held = self.failing_pool()
        self.retried(held)
        # ONE ANSWER PER STAGE, and the Job's own task in every one of them.
        self.assertEqual(len(self.binding.tasks), 2)
        self.assertEqual(set(self.binding.tasks),
                         {self.task_of(held, self.job_id)})
        # AND IT IS NOT THE INSTALLED DOCUMENT, which is what travelled before.
        self.assertNotEqual(self.binding.tasks[0],
                            held["installed"]["task_bytes"].decode("utf-8"))

    def test_the_fresh_job_answers_the_priors_task_through_the_lineage(self):
        held = self.failing_pool()
        answered = self.retried(held)
        fresh = answered["job_id"]
        self.assertNotEqual(fresh, self.job_id)
        self.assertEqual(self.task_of(held, fresh),
                         self.task_of(held, self.job_id))
        # AND THE FRESH SUBMISSION DECLARES THE PRIOR IDENTITY, which is why
        # the two have to agree at all.
        rows = {one["job_id"]: one["input_digest"] for one in
                held["jobs"]._connection.execute(
                    "SELECT job_id, input_digest FROM jobs").fetchall()}
        self.assertEqual(rows[fresh], rows[self.job_id])

    def test_nothing_copied_the_task_into_the_retrys_own_row(self):
        """One creation holds the bytes; the lineage is how they are found."""
        held = self.failing_pool()
        answered = self.retried(held)
        self.assertEqual(
            [one["job_id"] for one in
             creation.created_job_rows(held["jobs"])], [self.job_id])
        self.assertEqual(self.task_of(held, answered["job_id"]),
                         self.task_of(held, self.job_id))

    def test_the_original_creation_and_its_evidence_are_untouched(self):
        held = self.failing_pool()
        before = [dict(one) for one in
                  creation.created_job_rows(held["jobs"])]
        first_attempt = self.stage_of(held["jobs"], held["composed"],
                                      self.job_id)["attempt_id"]
        recorded = attempts.recorded_input_of(held["control"], first_attempt)
        self.retried(held)
        self.assertEqual([dict(one) for one in
                          creation.created_job_rows(held["jobs"])], before)
        self.assertEqual(
            attempts.recorded_input_of(held["control"], first_attempt),
            recorded)
        self.assertEqual(
            self.stages(held["jobs"], held["composed"],
                        self.job_id)["implementation"], "exceptional")

    def test_the_same_request_again_answers_the_same_fresh_job(self):
        held = self.failing_pool()
        first = self.retried(held)
        second = self.retried(held)
        self.assertEqual(first["job_id"], second["job_id"])
        rows = held["jobs"]._connection.execute(
            "SELECT job_id FROM fresh_attempts").fetchall()
        self.assertEqual([one["job_id"] for one in rows], [first["job_id"]])
        self.assertEqual(self.task_of(held, first["job_id"]),
                         self.task_of(held, self.job_id))


class TheRetriedJobIsServedItsOwnTask(RetryLineageCase):
    """What the serving readers and the selector answer for the retry.

    These are the composition questions; `TheRetriedJobReachesItsOwnRuntimes`
    below starts the containers. Both are kept: a reader that answers right
    and a runtime that mounts right are two facts, and this suite found the
    first one broken before the second could be asked.
    """

    def test_the_serving_readers_answer_the_inherited_task(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        # THE READER THE SERVING PATH CALLS, not the one this case prefers:
        # `stage_execution._job_workers` reads exactly this.
        reader = single_worker.job_task_reader(held["jobs"])
        self.assertEqual(reader(job_id=fresh), reader(job_id=self.job_id))
        self.assertEqual(reader(job_id=fresh),
                         self.task_of(held, self.job_id))

    def test_the_document_a_worker_would_serve_the_retry_under(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        worker = self.worker_of(held["composed"], "implementation")
        stage = dict(self.stage_of(held["jobs"], held["composed"], fresh),
                     job_id=fresh)
        served = worker._given_for(stage)
        self.assertIsNot(served, worker.given)
        self.assertEqual(served["task_bytes"].decode("utf-8"),
                         self.task_of(held, self.job_id))
        from baton_v12.contracts.manifest import job_input_identity

        rows = {one["job_id"]: one["input_digest"] for one in
                held["jobs"]._connection.execute(
                    "SELECT job_id, input_digest FROM jobs").fetchall()}
        self.assertEqual(job_input_identity(served["input_manifest"]),
                         rows[fresh])
        self.assertIsNone(worker._matches(
            stage, {"job_id": fresh, "input_digest": rows[fresh],
                    "policy_digest": worker.given["policy_digest"]}))

    def test_the_retry_is_offered_and_its_claim_waits_on_the_works_route(self):
        """WHAT THE ONE-PRODUCER POOL DOES, read out of the loop's reports.

        The prior attempt's own `unable` ending settles its assignment, so
        the retry IS offered -- and its claim is then deferred, because that
        ending also passed the Work to its `review_route`: "the authority
        refused this claim: route 'rview' does not resolve to
        'baton.claude'". The Work is somebody else's to hand back, which is
        the v11 route doing its job rather than anything about the task.

        IT IS WHY THE RUNTIME CLASS AUTHORIZES ITS SPARE PRODUCER FOR BOTH
        ROUTES, and the sequence matters: this deployment's implementation
        participant handles `impl` alone, so a Job whose Work has moved to
        review cannot be re-claimed by it at all.

        W365075 LEFT THIS CASE WHERE IT WAS. The release returns the line to
        `idle` and the ending's own discharge clears the quiescence gate -- so
        the offer this case asserts is now reached through an ungated Work
        rather than in spite of one -- and the route is what still defers the
        claim, which is the same observation over the same reports.
        """
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        said = []
        for _ in range(6):
            said.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            said.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        self.assertEqual(self.stages(held["jobs"], held["composed"],
                                     fresh)["implementation"], "offered")
        acts = [one for report in said for one in report["acts"]
                if one["stage_id"].startswith(fresh)]
        self.assertTrue(acts)
        self.assertIn("does not resolve to", json.dumps(acts, default=str))
        # AND THIS IS ALSO WHERE `_fence_operation` IS PROVED. That reader
        # answers the authority operation id the ending's handoff is fenced
        # by, and before W365075 it knew only the checkpoint and the verdict.
        # A released ending that carried none would have handed off with no
        # fence operation -- so the Work would never have moved to `rview`,
        # and this refusal, which names that route, could not exist. The
        # route the claim meets is the evidence that the handoff carried the
        # release's own fence.
        # AND THE RELEASE IS WHY THE LINE IS NOT WHAT STOPS IT.
        worker = self.worker_of(held["composed"], "implementation")
        line = worker.stage.deployment.line_for(fresh)
        self.assertEqual(line["state"], "idle")
        # AND NOTHING STARTED FOR IT.
        stage = self.stage_of(held["jobs"], held["composed"], fresh)
        self.assertIsNone(stage.get("runtime"))


class TheRetriedJobReachesItsOwnRuntimes(RetryLineageCase):
    """W364834's outcome: the retry's own containers, with the task it kept.

    THE FIXTURE'S ONE ADDITION IS SPARE CAPACITY, which review
    2026-10-27T00-18-27Z names as a supported strategy. The deployment
    configures a SECOND implementation producer and binds the retry identity
    to it, so the first attempt's retained allocation and evidence are left
    exactly as they are -- nothing is deleted, no cleanup is forged and no
    activation is handwritten. An operator who means to retry a Job on a pool
    whose producer is holding a faulted attempt's material configures
    precisely this.

    THE REST IS THE PRODUCT. The creation, the admission, the serving loop,
    the real in-image turns, the ending with its publication and frozen
    checkpoint, and the review attachment over that checkpoint. The engine
    and the checkpoint profile are the two deterministic seams, and every
    case refuses to spawn version control.
    """

    BASE = "a" * 40
    HEAD = "b" * 40
    PROPOSAL_OUTPUTS = reviewing.PROPOSAL_OUTPUTS
    proposal_manifest = reviewing.proposal_manifest
    SPARE = "implementation-worker-b"

    def quiescing(self):
        """The multi-container double, because this pool runs two attempts.

        The first attempt's container is still in the engine's account when
        the retry starts -- it ended `unable`, not removed -- and a double
        that models ONE container shows the retry that container and the
        manager refuses to adopt it: "one delivery carries one identity",
        which is correct. `_ConcurrentEngine` is the repository's own
        multi-container model and it carries the stop/absence facts an
        ending needs.
        """
        return _ConcurrentEngine()

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority

        self.proposing = True
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.BASE)
            self.spare_principal = authority.principal_of("baton.second")
            # BOTH ROUTES THIS WORK PASSES THROUGH. The first attempt's
            # ending hands the Work to its `review_route`, so by the time the
            # retry is offered the Work is on `rview` -- and a claim is
            # refused for a route that does not resolve to the claimant
            # ("route 'rview' does not resolve to 'baton.second'"). An
            # operator configuring a spare producer authorizes it for the
            # routes its Jobs will be on; this is that, and nothing else.
            for route in (fixtures.ROUTE, "rview"):
                authority.add_route_handler(route, "baton.second")
        finally:
            authority.dispose()

    def agent(self):
        """Faulting for the first attempt, proposing for the retry's.

        `self.proposing` is the fixture's one switch: the first turn has to
        FAULT so the prior execution is over, and the retry's has to publish
        a proposal so its review stage opens. Both are the same scripted
        worker with the same declared outputs.
        """
        if not self.proposing:
            return RetryLineageCase.agent(self)
        return reviewing.agent(self)

    def spare_capacity_document(self):
        """The pool, with a second producer and the retry bound to it."""
        manifest = self.proposal_manifest()
        held = {one["role"]: one
                for one in self.composed_document()["workers"]}
        for one in held.values():
            one["deployment"]["input_manifest"] = manifest
        spare = json.loads(json.dumps(held["implementation"]))
        # EXACTLY THE THREE MEMBERS A CONFIGURED WORKER CARRIES -- the
        # participant lives inside the deployment, and a wrapper member the
        # schema does not name is refused by `held_configuration`.
        spare["worker_id"] = self.SPARE
        spare["deployment"]["participant"] = "baton.second"
        spare["deployment"]["principal"] = self.spare_principal
        spare["deployment"]["launch_home"] = os.path.join(self.root,
                                                          "launch-spare")
        spare["deployment"]["credential_home"] = os.path.join(self.root,
                                                              "cred-spare")
        self.retry_id = "job-retry-first-retry-2"
        return self.composed_document(
            checkpoint_profile=self.config["profile_name"],
            line_declared_base=self.BASE,
            # AND A RETENTION DISPOSITION THAT DOES NOT KEEP THE MATERIAL.
            #
            # `retain` and `quarantine` are the two that KEEP it, and cleanup
            # then ends `retained` -- which is why a faulted attempt holds its
            # allocation and its Work. `discard-after-intake` is the third
            # configured value the product already supports: the material is
            # taken into custody, accounted for, and then let go, so the
            # attempt settles and the pool is free. Configuring it is this
            # fixture's one deployment choice; nothing is deleted by hand and
            # no cleanup is forged. An operator who means to retry rather than
            # inspect configures exactly this.
            retention_disposition="discard-after-intake",
            schema=stage_execution.MULTI_CONFIG_SCHEMA,
            workers=[held["implementation"], held["review"],
                     held["integration"], spare],
            job_bindings=[
                {"job_id": "job-retry-first", "job_work_id": self.work,
                 "review_work_id": self.work,
                 "line_declared_base": self.BASE,
                 "canonical_target_id": "target-1",
                 "source_worker_id": "implementation-worker"},
                # THE RETRY'S OWN BINDING, on the spare producer. Its
                # identity is `successor_of`'s own derivation, so the
                # deployment binds what the admission will name.
                {"job_id": self.retry_id, "job_work_id": self.work,
                 "review_work_id": self.work,
                 "line_declared_base": self.BASE,
                 "canonical_target_id": "target-1",
                 "source_worker_id": self.SPARE}])

    def failing_pool(self, task_id="retry-first",
                     statement="The task a retry must keep."):
        """One created Job whose first attempt faults, on a two-producer pool."""
        jobs, control = self.stores("retry-runtime")
        document = self.spare_capacity_document()
        installed = single_worker._held(document["workers"][0]["deployment"])
        answered = self.create(jobs, installed, task_id=task_id,
                               statement=statement)
        self.job_id = answered["job_id"]
        self.engine = self.quiescing()
        composed = stage_execution.operations_from(
            document, jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout,
            checkpoint_profile=self.profile_seam)
        self.addCleanup(composed.close)
        self.driven(jobs, composed, self.job_id)
        self.first_attempt = self.stage_of(jobs, composed,
                                           self.job_id)["attempt_id"]
        self.proposing = False
        self.turn(jobs, control, composed, "implementation",
                  self.first_attempt)
        self.proposing = True
        for _ in range(12):
            sweep(jobs, composed, now=fixtures.NOW)
            reconcile(jobs, composed, now=fixtures.NOW)
            if self.stages(jobs, composed,
                           self.job_id)["implementation"] == "exceptional":
                break
        self.assertEqual(
            self.stages(jobs, composed, self.job_id),
            {"implementation": "exceptional", "review": "blocked"})
        # AND THE PRIOR ASSIGNMENT IS ALREADY SETTLED BY THE ENDING, which
        # this fixture learned by trying to settle it itself.
        #
        # `finalize_quiescent_assignment` says "CALLING THIS IS THE
        # OPERATOR'S DECISION... nothing in this manager calls this on a
        # worker's behalf" -- but that is about a worker that has NOT
        # answered. An `unable` ANSWER is an ending, and the composed
        # ending performs it: calling it again from here was refused with
        # "operation 'attempt.finalize-quiescent:...' is already recorded
        # with a different kind or signature", which is the journal saying
        # the act had already happened. So this fixture performs no recovery
        # act at all: the first attempt ends the way the product ends it.
        #
        # A TURN THAT MERELY RAISES IS DIFFERENT, and that is why the agent
        # answers rather than raising: a `faulted` terminal carries no
        # disposition, finalization refuses it ("worker disposition is
        # 'none'"), and the Work stays claimed -- which is the state the
        # earlier claim of this Work reported as a capacity hold.
        return {"jobs": jobs, "control": control, "composed": composed,
                "created": answered, "installed": installed}

    def turn(self, jobs, control, composed, role, attempt_id, job_id=None):
        """The borrowed turn, told which worker and which Job this attempt is.

        TWO THINGS THE BORROWED HELPER TAKES FROM THE CASE. `_turning_attempt`
        selects the worker that PREPARED the attempt, because a two-producer
        pool has two of them; and `job_id` names the Job the launch document
        is for. W365075: the retry is a SECOND Job on this Work, and the
        helper read `self.job_id` -- so adopting the retry's launch document
        was refused with "not the one this manager would have written for it",
        which is `launch.adopt` correctly rejecting a document naming the
        prior Job. Rebound for the call rather than reassigned, so every other
        reader still means the original.
        """
        held = getattr(self, "_turning_attempt", None)
        owner = self.job_id
        self._turning_attempt = attempt_id
        self.job_id = job_id or owner
        try:
            return reviewing.turn(self, jobs, control, composed, role,
                                  attempt_id)
        finally:
            self._turning_attempt = held
            self.job_id = owner

    def admitted_retry(self):
        """The retry, admitted and driven as far as the product takes it."""
        held = self.failing_pool()
        answered = self.retried(held)
        fresh = answered["job_id"]
        self.assertEqual(fresh, self.retry_id)
        held["retry"] = fresh
        seen = []
        for _ in range(14):
            seen.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            seen.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        held["reports"] = seen
        held["retry_stage"] = self.stage_of(held["jobs"], held["composed"],
                                            fresh)
        return held

    def completed_retry(self):
        """The retry carried all the way to its own REVIEW runtime.

        W365075's own outcome, and no operator act anywhere in it: the
        admission, the ordinary ticks, the retry's real in-image turn, and
        then ordinary ticks again. Everything the loop does -- the offer, the
        claim, the writer grant on the released line, the container, the
        ending with its publication and frozen checkpoint, the attachment and
        the review container -- is the product's.
        """
        held = self.admitted_retry()
        fresh = held["retry"]
        # THE RETRY'S OWN IMPLEMENTATION ATTEMPT, which exists because the
        # line admitted a writer for it.
        self.driven(held["jobs"], held["composed"], fresh)
        stage = self.stage_of(held["jobs"], held["composed"], fresh)
        held["retry_attempt"] = stage["attempt_id"]
        self.assertNotEqual(held["retry_attempt"], self.first_attempt)
        self.proposing = True
        self.turn(held["jobs"], held["control"], held["composed"],
                  "implementation", held["retry_attempt"], job_id=fresh)
        for _ in range(16):
            sweep(held["jobs"], held["composed"], now=fixtures.NOW)
            reconcile(held["jobs"], held["composed"], now=fixtures.NOW)
        held["stages"] = self.stages(held["jobs"], held["composed"], fresh)
        return held

    def rows(self, held, statement):
        return [dict(one) for one in
                held["control"]._connection.execute(statement).fetchall()]

    def gate_of(self, held):
        """The Work's gate, read from the Authority's own projection."""
        from baton_v12.authority import Authority

        del held
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            return authority.project_work(self.work).get("gate")
        finally:
            authority.dispose()

    def test_the_document_the_spare_would_serve_the_retry_under(self):
        """The delivery question, which is this suite's own subject.

        W365075 released the line, so the dead end this case used to meet is
        gone and the stage this document is composed from is a LIVE one --
        the retry holds the line and its container is running. The document
        is composed from the stage either way, which is why this case did not
        have to change.
        """
        held = self.admitted_retry()
        stage = held["retry_stage"]
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id=self.SPARE)
        served = worker._given_for(dict(stage, job_id=held["retry"]))
        self.assertEqual(served["task_bytes"].decode("utf-8"),
                         self.task_of(held, self.job_id))
        self.assertIsNot(served, worker.given)

    def test_the_prior_endings_gate_is_discharged_by_the_release(self):
        """THE OBLIGATION THE RELEASE INHERITED, and discharged.

        Ending an assignment is not evidence that the container is gone, so
        the Authority installs `runtime-quiescence:<generation>` in the same
        transaction -- whichever ending performed the fence. The release
        performs the SAME fence the freeze does, so it owes the SAME
        discharge, and the ending carries the gate reference out in its
        `released` document for the composition to settle.

        W365075's own regression lives here. The first cut returned the
        release without its fence, so `_fenced_gate` found nothing to be owed,
        no discharge was ever asked for, and the Work stayed gated -- a dead
        end one step past the one this Work was created for, with the retry
        deferred on "an offer is issued only against open, queued, unclaimed,
        ungated Work".
        """
        held = self.admitted_retry()
        self.assertIsNone(self.gate_of(held))
        acts = [one for report in held["reports"] for one in report["acts"]
                if one["stage_id"].startswith(held["retry"])]
        self.assertTrue(acts)
        self.assertNotIn("ungated Work", json.dumps(acts, default=str))
        # AND IT IS THE PRIOR ENDING'S OWN COMMITTED ACT, read through the
        # owner's reader rather than inferred from the projection's absence.
        from baton_v12.worker_manager import gate_discharge_of

        discharged = gate_discharge_of(held["control"], self.first_attempt)
        self.assertIsNotNone(discharged)
        self.assertEqual(discharged["gate"], "runtime-quiescence:1")
        # THE RETRY'S OWN ATTEMPT OWES NO DISCHARGE YET: its ending has not
        # happened, which is what distinguishes "cleared" from "never asked".
        self.assertIsNone(gate_discharge_of(held["control"],
                                            held["retry_stage"]["attempt_id"]))

    def test_the_released_line_admits_the_retrys_own_writer(self):
        """ONE LINE FOR THE WORK, AND THE RETRY IS WRITING ON IT.

        `create_line`'s identity is `(authority, work)`, so a retry is a new
        Job on the SAME line -- which is exactly why the stuck state mattered.
        The release returns that line to `idle`, `grant_writer` admits it, and
        the writer the line now carries belongs to the retry's attempt and not
        to the round that produced nothing.
        """
        held = self.admitted_retry()
        worker = self.worker_of(held["composed"], "implementation",
                                worker_id="implementation-worker")
        deployment = worker.stage.deployment
        line = deployment.line_for(held["retry"])
        self.assertEqual(line["line_id"],
                         deployment.line_for(self.job_id)["line_id"])
        self.assertEqual(line["state"], "writing")
        # NOTHING WAS FROZEN BY THE ROUND THAT PRODUCED NOTHING.
        self.assertIsNone(line["current_checkpoint_id"])
        self.assertEqual(self.rows(held, "SELECT COUNT(*) AS held FROM "
                                         "line_checkpoints")[0]["held"], 0)
        # AND THE TWO WRITERS ARE THE TWO ROUNDS: the released one and the
        # live one, each naming its own attempt.
        writers = {one["revocation_reason"]: one for one in
                   self.rows(held, "SELECT runtime_attempt_id, state, "
                                   "revocation_reason FROM line_writers")}
        self.assertEqual(sorted(writers, key=lambda one: one or ""),
                         [None, "released"])
        self.assertEqual(writers["released"]["runtime_attempt_id"],
                         self.first_attempt)
        self.assertEqual(writers["released"]["state"], "revoked")
        self.assertEqual(writers[None]["state"], "active")
        self.assertNotEqual(writers[None]["runtime_attempt_id"],
                            self.first_attempt)

    def test_the_retry_reaches_its_own_implementation_runtime(self):
        """W365075'S MILESTONE, FIRST HALF: a container for the retry.

        Not a helper's answer and not a projection of intent -- the attempt
        row the manager keeps, with a running runtime attached, reached
        through the ordinary serving loop over the released line.
        """
        held = self.admitted_retry()
        stage = held["retry_stage"]
        self.assertEqual(stage["state"], "waiting")
        self.assertIsNotNone(stage["attempt_id"])
        self.assertNotEqual(stage["attempt_id"], self.first_attempt)
        self.assertEqual(stage["allocation"]["worker_id"], self.SPARE)
        running = {one["runtime_attempt_id"]: one for one in
                   self.rows(held, "SELECT runtime_attempt_id, runtime_id, "
                                   "execution_runtime FROM attempts")}
        held_row = running[stage["attempt_id"]]
        self.assertEqual(held_row["execution_runtime"], "running")
        self.assertIsNotNone(held_row["runtime_id"])
        # AND THE PRIOR ONE IS STILL WHERE ITS ENDING LEFT IT.
        self.assertEqual(running[self.first_attempt]["execution_runtime"],
                         "destroyed")

    def test_the_retry_reaches_its_own_independent_review_runtime(self):
        """W365075'S MILESTONE, SECOND HALF: review, started.

        The retry's real turn publishes a candidate, so THIS round's ending
        takes the other branch of step eight -- it freezes a checkpoint --
        and the line goes `reviewing` behind an active attachment over that
        checkpoint. The review stage then starts its own container. Every act
        is the loop's.
        """
        held = self.completed_retry()
        self.assertEqual(held["stages"],
                         {"implementation": "completed", "review": "waiting"})
        lines = self.rows(held, "SELECT line_id, state, current_checkpoint_id "
                                "FROM review_lines")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["state"], "reviewing")
        frozen = self.rows(held, "SELECT checkpoint_id, state FROM "
                                 "line_checkpoints")
        self.assertEqual([one["state"] for one in frozen], ["frozen"])
        self.assertEqual(lines[0]["current_checkpoint_id"],
                         frozen[0]["checkpoint_id"])
        attached = self.rows(held, "SELECT attachment_id, checkpoint_id, "
                                   "state FROM review_attachments")
        self.assertEqual([one["state"] for one in attached], ["active"])
        self.assertEqual(attached[0]["checkpoint_id"],
                         frozen[0]["checkpoint_id"])
        # THE REVIEW CONTAINER, AND IT IS A THIRD ATTEMPT.
        review = self.stage_of(held["jobs"], held["composed"], held["retry"],
                               kind="review")
        self.assertEqual(review["state"], "waiting")
        runtimes = {one["runtime_attempt_id"]: one["execution_runtime"]
                    for one in self.rows(held, "SELECT runtime_attempt_id, "
                                               "execution_runtime FROM "
                                               "attempts")}
        self.assertEqual(len(runtimes), 3)
        self.assertEqual(runtimes[review["attempt_id"]], "running")
        self.assertEqual(runtimes[held["retry_attempt"]], "destroyed")
        self.assertEqual(runtimes[self.first_attempt], "destroyed")

    def test_the_excluded_rounds_material_is_untouched_by_all_of_it(self):
        """WHAT THE RECOVERY DID NOT DO, after the whole lifecycle ran.

        The review's boundary: preserve the original output, the task, the
        Work identity and the attribution, and do not erase evidence. Asked
        at the END, when three runtimes have come and gone.
        """
        held = self.completed_retry()
        first = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self.assertEqual(first["attempt_id"], self.first_attempt)
        self.assertEqual(first["allocation"]["worker_id"],
                         "implementation-worker")
        rows = {one["runtime_attempt_id"]: one for one in
                self.rows(held, "SELECT runtime_attempt_id, "
                                "worker_disposition, cleanup, output, "
                                "assignment_participant FROM attempts")}
        excluded = rows[self.first_attempt]
        self.assertEqual(excluded["worker_disposition"], "unable")
        self.assertEqual(excluded["cleanup"], "retained")
        self.assertEqual(excluded["output"], "sealed")
        self.assertEqual(excluded["assignment_participant"], "baton.claude")
        # ITS OWN TASK IS STILL IN ITS OWN INPUT ROOT, and it is the one the
        # retry inherited.
        self.assertEqual(self.published(self.first_attempt).decode("utf-8"),
                         self.task_of(held, self.job_id))
        self.assertEqual(self.published(held["retry_attempt"]).decode("utf-8"),
                         self.task_of(held, self.job_id))
        # AND THE RETRY RAN FOR THE SPARE PRINCIPAL, not for the excluded
        # round's producer.
        self.assertEqual(rows[held["retry_attempt"]]["cleanup"], "retained")

    def test_the_first_attempts_evidence_survives_the_retry(self):
        held = self.admitted_retry()
        first = self.stage_of(held["jobs"], held["composed"], self.job_id)
        self.assertEqual(first["attempt_id"], self.first_attempt)
        self.assertIsNotNone(first["allocation"])
        self.assertEqual(first["allocation"]["worker_id"],
                         "implementation-worker")
        self.assertIsNotNone(
            attempts.recorded_input_of(held["control"], self.first_attempt))
        # AND ITS INPUT ROOT STILL CARRIES ITS OWN TASK.
        self.assertEqual(self.published(self.first_attempt).decode("utf-8"),
                         self.task_of(held, self.job_id))

    def test_the_same_admission_after_a_reopen_answers_the_same_retry(self):
        """REOPEN AND REPLAY, over the same durable state."""
        held = self.admitted_retry()
        from baton_v12.job_manager import JobStore

        reopened = JobStore.open(
            self.job_path, authority_uuid=self.config["authority_uuid"],
            incarnation="reopened-1", clock=lambda: fixtures.NOW)
        self.addCleanup(reopened.close)
        again = fresh_attempt.admit(
            reopened, held["composed"], prior_job_id=self.job_id,
            exclusion=self.exclusion, authorization=FakeAuthorization(),
            binding=self.binding, ownership=FakeOwnership())
        self.assertEqual(again["job_id"], held["retry"])
        self.assertEqual(creation.job_task_of(reopened, held["retry"]),
                         self.task_of(held, self.job_id))
        rows = reopened._connection.execute(
            "SELECT job_id FROM fresh_attempts").fetchall()
        self.assertEqual([one["job_id"] for one in rows], [held["retry"]])


class TheLineageRefusesWhatItCannotRead(RetryLineageCase):
    """A corrupt lineage is a refusal, not an answer and not a loop."""

    def test_a_circular_lineage_refuses(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        # NO OPERATION WRITES THIS: it is a store somebody edited.
        held["jobs"]._connection.execute(
            "UPDATE fresh_attempts SET prior_job_id = ? WHERE job_id = ?",
            (fresh, fresh))
        with self.assertRaises(ContractRefusal) as caught:
            self.task_of(held, fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("circular lineage", str(caught.exception))

    def test_a_lineage_whose_origin_was_never_created_answers_none(self):
        """The legacy path: a retry of a hand-submitted Job has no own task."""
        from baton_v12.job_manager import submit

        held = self.failing_pool()
        submit(held["jobs"], fixtures.submission(
            submission_id="sub-plain",
            jobs=[fixtures.job("job-plain", stages=[
                fixtures.stage("implementation", self.work),
                fixtures.stage("review", self.work,
                               depends_on=[{"job_id": "job-plain",
                                            "kind": "implementation"}])])]))
        self.assertIsNone(self.task_of(held, "job-plain"))
        # AND THE LINEAGE READ IS THE SAME ONE for a Job with no retry row.
        self.assertIsNone(self.task_of(held, "job-nobody-submitted"))


if __name__ == "__main__":
    unittest.main()
