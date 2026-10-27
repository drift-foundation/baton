"""W361912 — the deployment derivation, against a REAL deployment document.

WHY THIS SUITE EXISTS SEPARATELY FROM `test_creation`. Those cases drive the
operation with a stand-in derivation, which proves the operation. This one
proves the DERIVATION: that the four facts an operator must not be asked for
can really be read off a document `stage_execution.held_configuration` owns,
and -- the part that matters -- that a Job resolved from them is one the
scheduler's own rule says the configured workers can serve.

THAT ROUND TRIP IS THE WHOLE CLAIM. `_disagreements` compares a worker's
`launch_role`, its manifest Work, its profile name and digest, the Job-scoped
projection of its input manifest and its policy digest against the stage and
the Job. A derivation that got any one of them wrong would produce a
configuration that validates cleanly and whose stages no worker can ever be
selected for, which is the failure the pilot recorded. So the cases below
derive, resolve, and then ask `servable_workers` -- the scheduler's function,
not a restatement of it.

The fixture is `tests.tools.test_stage_execution.StageCase`'s own document,
reused rather than rebuilt for the reason that suite gives: the launch
document's rules have one owner, and a test that hand-rolled a second valid
document would be asserting against its own idea of one.
"""

import json
import unittest

from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import templates

from tools import stage_execution
from tools.creation_ports import BindingRefusal, DeploymentDerivation

from tests.tools.test_stage_execution import StageCase

TASK_WORK_SCOPE = ("v12/python/src/baton_v12/job_manager/creation.py",)


class _Derivation(DeploymentDerivation):
    """The real port over a document this case holds rather than a file.

    EVERYTHING BELOW `configuration` IS THE PRODUCT'S. `held` still runs
    `stage_execution.held_configuration`, and `derived` still reads only what
    that owner answered -- so what is substituted here is where the bytes come
    from and nothing about how they are proved.
    """

    def __init__(self, document, *, checkout=None, **named):
        super().__init__("/unused", **named)
        self._document = document
        self._checkout = checkout

    def configuration(self):
        return self._document

    def held(self):
        return stage_execution.held_configuration(self._document,
                                                  checkout=self._checkout)


class DerivationCase(StageCase):

    def derivation(self, document=None, **named):
        return _Derivation(self.document() if document is None else document,
                           checkout=self.checkout, **named)

    def refused(self, document=None, **named):
        with self.assertRaises(BindingRefusal) as caught:
            self.derivation(document, **named).derived()
        return str(caught.exception)


class TheFourDerivedFacts(DerivationCase):

    def test_each_one_is_the_configured_workers_own(self):
        held = self.derivation().derived()
        given = stage_execution.held_configuration(self.document(),
                                                   checkout=self.checkout)
        producer = next(one for one in given["workers"]
                        if one["role"] == "implementation")
        self.assertEqual(
            held["work_id"],
            producer["deployment"]["input_manifest"]["work_ref"]["work_id"])
        self.assertEqual(
            held["input_digest"],
            job_input_identity(producer["deployment"]["input_manifest"],
                               what="a configured worker's input"))
        self.assertEqual(held["policy_digest"],
                         producer["deployment"]["policy_digest"])
        self.assertEqual(sorted(held["profiles"]),
                         ["implementation", "review"])
        for kind in ("implementation", "review"):
            worker = next(one for one in given["workers"]
                          if one["role"] == kind)
            self.assertEqual(
                held["profiles"][kind],
                {"profile_name": worker["deployment"]["profile_name"],
                 "profile_digest": worker["deployment"]["profile_digest"]})

    def test_the_integration_role_is_not_derived_for_a_two_stage_template(
            self):
        """ONLY THE LANES THIS CREATION NEEDS.

        This deployment configures an integration worker too. A port that
        derived every configured role would have to agree with it about a
        stage the implementation-review template does not carry.
        """
        held = self.derivation().derived()
        self.assertNotIn("integration", held["profiles"])

    def test_a_malformed_deployment_document_refuses_through_its_owner(self):
        """THE OWNER'S REFUSAL, not a second validator here.

        `held_configuration` is what proves a deployment document, and a port
        that pre-checked it would be a copy of that rule.
        """
        from baton_v12.contracts import ContractRefusal

        document = self.document()
        del document["workers"]
        with self.assertRaises(ContractRefusal):
            self.derivation(document).derived()


class TheOwnerRefusesIncoherenceBeforeThePortSeesIt(DerivationCase):
    """WHERE THE DISAGREEMENT REFUSALS ACTUALLY LIVE, measured.

    I wrote the port's `_agreed` check expecting to drive it with a document
    whose review worker disagreed about the policy or the Work. It cannot be
    driven that way, and the reason is better than the test I meant to write:
    `stage_execution.held_configuration` ALREADY refuses such a document, so a
    port reading its answer never sees one. These cases record that, because
    an unreachable refusal somebody believes is load-bearing is worse than one
    whose owner is named.
    """

    def owner_refuses(self, document):
        from baton_v12.contracts import ContractRefusal

        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.held_configuration(document,
                                               checkout=self.checkout)
        return caught.exception.message

    def test_a_worker_whose_policy_disagrees_with_its_manifest_is_refused(
            self):
        document = self.document()
        for one in document["workers"]:
            if one["role"] == "review":
                one["deployment"]["policy_digest"] = "sha256:" + "9" * 64
        self.assertIn("another policy", self.owner_refuses(document))

    def test_a_worker_whose_manifest_was_edited_is_refused(self):
        document = self.document()
        for one in document["workers"]:
            if one["role"] == "review":
                one["deployment"]["input_manifest"]["work_ref"]["work_id"] = \
                    "0000000a-W9"
        self.assertIn("does not identify itself",
                      self.owner_refuses(document))

    def test_a_deployment_missing_a_role_is_refused(self):
        document = self.document()
        document["workers"] = [one for one in document["workers"]
                               if one["role"] != "review"]
        self.owner_refuses(document)


class TheDerivationsOwnRefusals(DerivationCase):
    """And the port's checks, driven against what an owner may answer.

    `held_configuration` refuses the document-level incoherence above, and it
    does NOT decide that two workers of one role must carry one profile -- so
    that is the port's own rule and this is where it is driven.

    EVERY WORKER HERE IS A REAL OWNED ONE with one member moved. A hand-made
    minimal manifest does not survive `job_input_identity`, which validates
    against the frozen schema -- so these start from the fixture's own owned
    document and change exactly the fact under test.
    """

    def owned(self):
        return stage_execution.held_configuration(self.document(),
                                                  checkout=self.checkout)

    def port(self, workers, **named):
        class _Answered(DeploymentDerivation):
            def held(self):
                return {"workers": workers}

        return _Answered("/unused", **named)

    def of(self, role, **moved):
        worker = next(one for one in self.owned()["workers"]
                      if one["role"] == role)
        return {"worker_id": worker["worker_id"], "role": role,
                "deployment": dict(worker["deployment"], **moved)}

    def refused(self, workers, **named):
        with self.assertRaises(BindingRefusal) as caught:
            self.port(workers, **named).derived()
        return str(caught.exception)

    def test_two_workers_of_one_role_with_two_profiles_refuse(self):
        second = self.of("review", profile_digest="sha256:" + "7" * 64)
        second["worker_id"] = "review-worker-2"
        message = self.refused([self.of("implementation"),
                                self.of("review"), second])
        self.assertIn("different runtime profiles", message)
        self.assertIn("will not choose", message)

    def test_lanes_disagreeing_about_the_policy_refuse(self):
        message = self.refused([
            self.of("implementation"),
            self.of("review", policy_digest="sha256:" + "9" * 64)])
        self.assertIn("the submitted policy", message)
        self.assertIn("will not choose", message)

    def test_a_missing_lane_refuses_naming_it(self):
        message = self.refused([self.of("implementation")])
        self.assertIn("'review'", message)
        self.assertIn("would never run", message)

    def test_only_the_requested_lanes_have_to_agree(self):
        """AN INTEGRATION WORKER ON ANOTHER PROFILE IS NOT A DISAGREEMENT.

        The template says which stages a Job owes, so a role this creation
        does not need is not asked to agree about anything.
        """
        held = self.port([
            self.of("implementation"), self.of("review"),
            self.of("integration", policy_digest="sha256:" + "8" * 64,
                    profile_digest="sha256:" + "4" * 64)]).derived()
        self.assertEqual(sorted(held["profiles"]),
                         ["implementation", "review"])
        self.assertEqual(
            held["policy_digest"],
            self.of("implementation")["deployment"]["policy_digest"])

    def test_the_lanes_a_port_derives_are_an_operand(self):
        held = self.port([self.of("implementation")],
                         kinds=("implementation",)).derived()
        self.assertEqual(sorted(held["profiles"]), ["implementation"])


class TheDerivedJobIsServable(DerivationCase):
    """The round trip: derive, resolve, and ask the scheduler's own rule."""

    def resolved(self, held):
        return templates.resolve(
            {"schema": templates.REQUEST_SCHEMA,
             "task": {"job_id": "job-w361912-servable",
                      "work_id": held["work_id"],
                      "statement": "one bounded creation"},
             "source": {"input_digest": held["input_digest"],
                        "policy_digest": held["policy_digest"]},
             "scope": {"work": list(TASK_WORK_SCOPE), "tests": []},
             "acceptance": ["the derived Job is servable"]},
            configuration={"schema": templates.CONFIGURATION_SCHEMA,
                           "profiles": held["profiles"]})

    def binding_for(self, job_id, held, document):
        """The binding this deployment would publish for a created Job.

        Composed here the way `bootstrap._compose` emits one, because what is
        being tested is the DERIVATION against the selector -- installing an
        instance to obtain the same five members would be testing `bootstrap`.
        """
        producer = next(one for one in document["workers"]
                        if one["role"] == "implementation")
        return {"job_id": job_id, "job_work_id": held["work_id"],
                "review_work_id": held["work_id"],
                "line_declared_base": document["line_declared_base"],
                "canonical_target_id": document["canonical_target_id"],
                "source_worker_id": producer["worker_id"]}

    def test_every_resolved_stage_is_servable_by_a_configured_worker(self):
        document = self.document()
        held = self.derivation(document).derived()
        resolution = self.resolved(held)
        entry = resolution["submission"]["jobs"][0]
        given = stage_execution.held_configuration(document,
                                                   checkout=self.checkout)
        binding = self.binding_for(entry["job_id"], held, document)
        for stage in entry["stages"]:
            with self.subTest(kind=stage["kind"]):
                compatible = stage_execution.servable_workers(
                    given, binding, dict(stage, job_id=entry["job_id"]),
                    entry)
                self.assertTrue(compatible)
                self.assertEqual(
                    [one["role"] for one in compatible], [stage["kind"]],
                    "a stage is served by a worker of its own lane")

    def test_one_wrong_derived_digest_makes_every_stage_unservable(self):
        """THE CONTROL CASE, so the pass above is not a coincidence.

        This is the pilot's failure in one assertion: a Job whose input
        digest an operator typed differently from the installed worker's
        validates cleanly and can never be selected.
        """
        document = self.document()
        held = dict(self.derivation(document).derived(),
                    input_digest="sha256:" + "0" * 64)
        resolution = self.resolved(held)
        entry = resolution["submission"]["jobs"][0]
        given = stage_execution.held_configuration(document,
                                                   checkout=self.checkout)
        binding = self.binding_for(entry["job_id"], held, document)
        from baton_v12.contracts import ContractRefusal

        for stage in entry["stages"]:
            with self.subTest(kind=stage["kind"]):
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution.servable_workers(
                        given, binding, dict(stage, job_id=entry["job_id"]),
                        entry)
                self.assertIn("the submitted input",
                              caught.exception.message)

    def test_a_wrong_derived_profile_makes_that_stage_unservable(self):
        document = self.document()
        held = self.derivation(document).derived()
        held["profiles"]["review"] = dict(held["profiles"]["review"],
                                          profile_digest="sha256:" + "6" * 64)
        resolution = self.resolved(held)
        entry = resolution["submission"]["jobs"][0]
        given = stage_execution.held_configuration(document,
                                                   checkout=self.checkout)
        binding = self.binding_for(entry["job_id"], held, document)
        from baton_v12.contracts import ContractRefusal

        review = next(one for one in entry["stages"]
                      if one["kind"] == "review")
        with self.assertRaises(ContractRefusal) as caught:
            stage_execution.servable_workers(
                given, binding, dict(review, job_id=entry["job_id"]), entry)
        self.assertIn("the workload profile digest", caught.exception.message)
        # AND THE IMPLEMENTATION STAGE IS UNAFFECTED, which is what makes the
        # per-stage derivation worth having.
        implementation = next(one for one in entry["stages"]
                              if one["kind"] == "implementation")
        self.assertTrue(stage_execution.servable_workers(
            given, binding, dict(implementation, job_id=entry["job_id"]),
            entry))


class TheRequestedTaskDoesNotReachTheWorker(DerivationCase):
    """R3, REPRODUCED. The reviewer's inference is correct and it is load-
    bearing: a created Job executes the task the DEPLOYMENT installed, not
    the one the request stated.

    review-2026-10-26T19-22-51Z: "selecting a new task may still execute the
    previously installed task. No execution reproduction of that inference is
    claimed." These cases claim it, from the owning code, and name why it is
    a specification gap rather than a bug in this candidate.

    THE MECHANISM, IN THREE OWNED FACTS.

      1. `single_worker._task_bytes(given["task_document"],
         manifest["human_contract"])` reads the task from the DEPLOYMENT's
         configured `task_document` path, at static preflight, and holds it as
         immutable bytes -- "a change to the configured path afterwards cannot
         change what a later composition publishes".
      2. `stage_execution._Stage.prepare_context` delivers exactly
         `worker.given["task_bytes"]` to the provider.
      3. `contracts.manifest` classifies `human_contract` as JOB INTENT --
         "which task, by content digest" -- so it is INSIDE
         `job_input_identity`, which is what `_disagreements` compares
         against the Job's `input_digest`.

    (1) and (2) mean the worker runs the installed task. (3) means the gap
    cannot be closed by deriving a different `input_digest`: a Job whose
    input identity named the REQUESTED task would be unservable by every
    installed worker. Both halves are asserted below.
    """

    def with_another_task(self, manifest):
        """One real manifest naming a DIFFERENT task, and still a manifest.

        The `human_contract` artifact moves and `manifest_digest` is
        RECOMPUTED by §12's own rule -- the digest over the document without
        that member -- because `job_input_identity` verifies it. Leaving the
        declared digest behind would make these cases about a malformed
        manifest rather than about a different task.
        """
        from baton_v12.contracts import digest as canonical_digest

        held = json.loads(json.dumps(manifest))
        held["human_contract"] = dict(held["human_contract"],
                                      content_digest="sha256:" + "3" * 64)
        held["manifest_digest"] = canonical_digest(
            {name: value for name, value in held.items()
             if name != "manifest_digest"})
        return held

    def test_the_task_bytes_come_from_the_deployment_not_from_any_job(self):
        """FACT 1, from the owner's own signature and docstring."""
        import inspect

        from tools import single_worker

        source = inspect.getsource(single_worker)
        self.assertIn('given["task_bytes"] = _task_bytes('
                      'given["task_document"],', source)
        self.assertIn('manifest["human_contract"])', source)
        # AND NOTHING ABOUT A JOB REACHES THAT READ. `_task_bytes` takes a
        # configured path and a manifest artifact; there is no Job operand.
        held = inspect.signature(single_worker._task_bytes)
        self.assertEqual(list(held.parameters), ["place", "contract"])

    def test_the_provider_is_handed_those_same_bytes(self):
        """FACT 2."""
        import inspect

        source = inspect.getsource(stage_execution)
        self.assertIn('task_bytes=worker.given["task_bytes"]', source)

    def test_the_task_is_inside_the_job_input_identity(self):
        """FACT 3, and this is what makes it a specification gap.

        `human_contract` is deliberately NOT projected out: the contracts
        layer classifies it as "which task, by content digest". So a Job
        carrying a different task has a different Job input identity.
        """
        from baton_v12.contracts.manifest import JOB_INPUT_EXCLUDED

        self.assertNotIn("human_contract", JOB_INPUT_EXCLUDED)
        given = stage_execution.held_configuration(self.document(),
                                                   checkout=self.checkout)
        producer = next(one for one in given["workers"]
                        if one["role"] == "implementation")
        manifest = producer["deployment"]["input_manifest"]
        self.assertIn("human_contract", manifest)
        before = job_input_identity(manifest,
                                    what="a configured worker's input")
        moved = self.with_another_task(manifest)
        self.assertNotEqual(
            job_input_identity(moved, what="a configured worker's input"),
            before,
            "a different task is a different Job input identity")

    def test_a_job_naming_the_requested_task_is_unservable(self):
        """THE CONSEQUENCE, driven through the scheduler's own rule.

        If a creation derived an input identity that reflected the REQUESTED
        task rather than the installed one, every configured worker would
        disagree about "the submitted input" -- so the Job would be admitted,
        bound, and selectable by nobody. That is the same failure mode the
        pilot recorded, reached from the opposite direction.
        """
        from baton_v12.contracts import ContractRefusal

        document = self.document()
        held = self.derivation(document).derived()
        given = stage_execution.held_configuration(document,
                                                   checkout=self.checkout)
        producer = next(one for one in given["workers"]
                        if one["role"] == "implementation")
        moved = self.with_another_task(
            producer["deployment"]["input_manifest"])
        requested = job_input_identity(
            moved, what="a configured worker's input")
        self.assertNotEqual(requested, held["input_digest"])
        resolution = templates.resolve(
            {"schema": templates.REQUEST_SCHEMA,
             "task": {"job_id": "job-w361912-requested-task",
                      "work_id": held["work_id"],
                      "statement": "a task nobody installed"},
             "source": {"input_digest": requested,
                        "policy_digest": held["policy_digest"]},
             "scope": {"work": list(TASK_WORK_SCOPE), "tests": []},
             "acceptance": ["the requested task reaches the worker"]},
            configuration={"schema": templates.CONFIGURATION_SCHEMA,
                           "profiles": held["profiles"]})
        entry = resolution["submission"]["jobs"][0]
        binding = {"job_id": entry["job_id"],
                   "job_work_id": held["work_id"],
                   "review_work_id": held["work_id"],
                   "line_declared_base": document["line_declared_base"],
                   "canonical_target_id": document["canonical_target_id"],
                   "source_worker_id": producer["worker_id"]}
        for one in entry["stages"]:
            with self.subTest(kind=one["kind"]):
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution.servable_workers(
                        given, binding,
                        dict(one, job_id=entry["job_id"]), entry)
                self.assertIn("the submitted input",
                              caught.exception.message)

    def test_what_the_creation_actually_derives_is_the_installed_task(self):
        """AND SO THE CREATED JOB RUNS THE INSTALLED TASK.

        This is the finding stated as an assertion rather than as prose: the
        input identity a creation derives is the one whose `human_contract`
        is the deployment's configured task document, whatever the request
        said. The statement, the acceptance criteria and the selected work
        scope are retained as provenance in `template_jobs` and reach no
        worker.
        """
        document = self.document()
        held = self.derivation(document).derived()
        given = stage_execution.held_configuration(document,
                                                   checkout=self.checkout)
        producer = next(one for one in given["workers"]
                        if one["role"] == "implementation")
        self.assertEqual(
            held["input_digest"],
            job_input_identity(producer["deployment"]["input_manifest"],
                               what="a configured worker's input"))
        self.assertEqual(
            producer["deployment"]["input_manifest"]["human_contract"],
            next(one for one in given["workers"]
                 if one["role"] == "review")["deployment"]["input_manifest"]
            ["human_contract"],
            "both installed lanes carry the one installed task")


if __name__ == "__main__":
    unittest.main()
