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
from tests.tools.test_stage_execution import ComposedOneJobCase, ServingCase
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
    worker_of = pool.worker_of
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
        refuses one beside a stage still owed an act, in as many words. So
        the first attempt has to END, and it has to end in a way that
        RELEASES the pool's capacity: a refused launch leaves the allocation
        `recovery-required` and the retry is then refused for "every
        effective worker/principal capacity is reserved or recovery-required",
        which is the recovery path's business and not this outcome's. A
        faulted turn is the ending the pilot measured: the container wrote a
        terminal, the stage projects `exceptional` and the allocation is
        released.
        """
        import scripted_agent

        class Faulting(scripted_agent.ScriptedAgent):
            def work(self, seen, declared):
                raise RuntimeError("the fixture's worker could not do it")

        return Faulting()

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
    """The delivery half: what the runtime would be served for the retry.

    WHERE THIS STOPS, AND WHY IT IS NOT THIS OUTCOME'S. A faulted attempt's
    material is PRESERVED -- DESIGN ART-7, and `AFaultedTerminalSurvivesThe
    ContainerThatWroteIt` is its case -- so its allocation stays held and the
    pool answers a retry's offer with "every effective worker/principal
    capacity is reserved or recovery-required". Releasing it is the recovery
    path's act, not an admission's and not a delivery's. Measured here rather
    than assumed: the case below reads that exact refusal out of the loop's
    own report.

    So what these cases assert is everything the runtime would use, composed
    by the objects that compose it: the Job-store reader the serving path
    calls, the selector's answer with the inherited task, and the per-stage
    document a worker would serve the retry under. The started container for
    a retried Job is the capacity release's to unblock.
    """

    def test_the_serving_readers_answer_the_inherited_task(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        # THE READER THE SERVING PATH CALLS, not the one this case prefers:
        # `stage_execution._job_workers` reads exactly this.
        reader = single_worker.job_task_reader(held["jobs"])
        self.assertEqual(reader(job_id=fresh),
                         reader(job_id=self.job_id))
        self.assertEqual(reader(job_id=fresh),
                         self.task_of(held, self.job_id))

    def test_the_document_a_worker_would_serve_the_retry_under(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        worker = self.worker_of(held["composed"], "implementation")
        stage = dict(self.stage_of(held["jobs"], held["composed"], fresh),
                     job_id=fresh)
        served = worker._given_for(stage)
        # THE PER-JOB DOCUMENT IS COMPOSED, not the installed one.
        self.assertIsNot(served, worker.given)
        self.assertEqual(served["task_bytes"].decode("utf-8"),
                         self.task_of(held, self.job_id))
        # AND ITS JOB-SCOPED IDENTITY IS WHAT THE RETRY SUBMITTED, which is
        # the agreement `_matches` enforces and the retry used to fail.
        from baton_v12.contracts.manifest import job_input_identity

        rows = {one["job_id"]: one["input_digest"] for one in
                held["jobs"]._connection.execute(
                    "SELECT job_id, input_digest FROM jobs").fetchall()}
        self.assertEqual(job_input_identity(served["input_manifest"]),
                         rows[fresh])
        self.assertIsNone(worker._matches(
            stage, {"job_id": fresh, "input_digest": rows[fresh],
                    "policy_digest": worker.given["policy_digest"]}))

    def test_the_selector_admits_the_retry_with_its_inherited_task(self):
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        deployment = self.worker_of(held["composed"],
                                    "implementation").stage.deployment
        rows = {one["job_id"]: dict(one) for one in
                held["jobs"]._connection.execute(
                    "SELECT job_id, input_digest, policy_digest "
                    "FROM jobs").fetchall()}
        job = dict(rows[fresh])
        for kind in ("implementation", "review"):
            stage = dict(self.stage_of(held["jobs"], held["composed"], fresh,
                                       kind=kind), job_id=fresh)
            binding, workers = stage_execution._job_workers(
                deployment, stage, job)
            self.assertTrue(workers, kind)
            del binding

    def test_the_retrys_offer_is_held_by_the_faulted_attempts_capacity(self):
        """THE LIMIT, read out of the loop's own report rather than assumed."""
        held = self.failing_pool()
        fresh = self.retried(held)["job_id"]
        said = []
        for _ in range(6):
            said.append(reconcile(held["jobs"], held["composed"],
                                  now=fixtures.NOW))
            said.append(sweep(held["jobs"], held["composed"],
                              now=fixtures.NOW))
        self.assertEqual(self.stages(held["jobs"], held["composed"],
                                     fresh)["implementation"], "queued")
        acts = [one for report in said for one in report["acts"]
                if one["stage_id"].startswith(fresh)]
        self.assertTrue(acts)
        self.assertIn("capacity is reserved or recovery-required",
                      json.dumps(acts, default=str))


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
