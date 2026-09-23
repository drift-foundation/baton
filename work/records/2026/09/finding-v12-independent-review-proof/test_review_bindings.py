"""The review composition, driven over a real line rather than a description.

WHAT IS REAL HERE. Every case composes against a real `ControlStore` holding a
real line, a real writer and a real frozen checkpoint, produced through the
supported `review_cycles` API by the same fixture `test_attachment` uses. So
"the composer reads the subject" is measured against a store that actually has
one, and "the composer refuses" is measured against the state that actually
causes the refusal.

AND THE WHOLE CHAIN IS DRIVEN. `TheDocumentedCommandProducesAnAcceptedPacket`
runs the command the operator page prints, as a subprocess, which composes,
holds the deployment against `stage_execution.held_configuration` -- the same
validator the serving deployment and `tools.bootstrap` run -- writes
`PACKET.json`, and then hands those exact bytes to
`review_supervisor.held_packet`. Preparation, composition and the supervisor's
own packet validation are one path here rather than three claims.

WHAT IS NOT PROVED HERE, stated rather than left to be assumed: no container,
image, provider, network or credential is involved, and no run is served. A
packet a validator accepts is not a run that happened.
"""

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from tests.manager.test_review_cycles import AUTHORITY, WORK

import attachment
import review_bindings
from test_attachment import REVIEWER, AttachmentCase

SIBLING = os.path.join(os.path.dirname(HERE),
                       "finding-v12-single-implementation-proof")
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(HERE)))))
VECTORS = os.path.join(
    CHECKOUT, "work/records/2026/08",
    "finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract",
    "findings/finding-worker-control-api-manifests/evidence/vectors.json")


class ComposingCase(AttachmentCase):
    """The attachment fixture, plus the operands a composition needs.

    The manager source and runtime root are this checkout's real ones: the
    composer hashes them, and hashing a tree that does not exist is not a
    proof of anything.
    """

    def setUp(self):
        super().setUp()
        self.run_root = os.path.join(self.temporary.name, "review-run")
        self.runtime_root = os.path.join(self.temporary.name, "runtime")
        os.makedirs(self.runtime_root)
        with open(os.path.join(self.runtime_root, "baton-v12-stack"), "w",
                  encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        self.manager_source = os.path.join(self.temporary.name, "src")
        os.makedirs(os.path.join(self.manager_source, "boundpkg"))
        with open(os.path.join(self.manager_source, "boundpkg",
                               "__init__.py"), "w", encoding="utf-8") as h:
            h.write("VERSION = 'bound'\n")

    def producer(self, **overrides):
        held = {"control_store": self.control_path,
                "line_id": self.line_id,
                "authority_uuid": AUTHORITY,
                "work_id": WORK,
                "checkpoint_id": self.checkpoint["checkpoint_id"],
                "workspace_storage": self.storage,
                "profile_name": self.profile.name,
                "run_root": os.path.dirname(self.control_path)}
        held.update(overrides)
        return held

    def operands(self, **overrides):
        held = {
            "instance": {
                "authority_store": os.path.join(self.temporary.name, "a.db"),
                "integration_store": os.path.join(self.temporary.name,
                                                  "i.db"),
                "job_store": os.path.join(self.temporary.name, "j.db"),
                "integration_profile": {
                    "profile_kind": "git", "profile_version": 1,
                    "integrator_participant": "baton.merge",
                    "instructions_digest": "sha256:" + "f" * 64},
                "retention_policy_digest": "sha256:" + "0f" * 32,
                "runtime_path": self.runtime_root,
                "build_commit": "c" * 40},
            "run_root": self.run_root,
            "image_reference": "baton-v12-claude-worker:w239533",
            "image_digest": "sha256:" + "c8" * 32,
            "cli_build": "claude-code/2.0.0",
            "manager_source": self.manager_source,
            "supervisor_path": os.path.join(HERE, "attachment.py"),
            "vectors": VECTORS,
            "participants": {
                "work_id": WORK,
                "implementation": "baton.impl",
                "implementation_principal": "principal:baton.impl",
                "review": REVIEWER["reviewer_participant"],
                "review_principal": REVIEWER["reviewer_principal"],
                "receipts": {"verification": "baton.verifier",
                             "review": "baton.approver-review",
                             "approval": "baton.approver"},
                "worker_files": {"opt/baton/claude_agent.py": "18c3" * 16}},
            "credential_sources": None,
            "credential_profile": {"api": {"provider": "fixture",
                                           "reference": "fixture/one"}},
            "evidence_digest": "sha256:" + "d" * 64,
            "provider_network": "baton-provider-egress",
            "run_id": "independent-review-239533",
            "work": "W239533", "claim": 244629, "note": "composition proof",
            "producer": self.producer()}
        held.update(overrides)
        return held

    def written_selections(self, **overrides):
        operands = self.operands(**overrides)
        operands.pop("run_root")
        place = os.path.join(self.temporary.name, "selections.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump({"compose": operands}, handle, indent=2, sort_keys=True)
        return place

    def bound_environment(self):
        """The import path the operator page binds, as the page binds it."""
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment["PYTHONPATH"] = os.pathsep.join(
            [os.path.join(CHECKOUT, "v12/python/src"),
             os.path.join(CHECKOUT, "v12/python"), HERE, SIBLING])
        return environment

    def documented(self, place, *extra):
        return subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "review_bindings.py"),
             "--selections", place, "--run-root", self.run_root, *extra],
            capture_output=True, text=True, timeout=300,
            env=self.bound_environment(), cwd=os.sep)

    def composed(self, **overrides):
        return review_bindings.compose(**self.operands(**overrides))

    def refusal(self, **overrides):
        shared = review_bindings._reuse()
        with self.assertRaises(shared.BindingRefusal) as caught:
            self.composed(**overrides)
        return str(caught.exception)


@unittest.skipUnless(os.path.exists(VECTORS),
                     "the published worker-contract conformance vector is "
                     "this composition's real operand")
class TheSubjectIsReadFromTheProducersOwnRecords(ComposingCase):
    def test_the_declared_base_comes_from_the_checkpoint_not_an_operand(self):
        documents = self.composed()
        held = self.held_subject()
        self.assertEqual(documents["deployment.json"]["line_declared_base"],
                         held["declared_base"])
        self.assertEqual(documents["task.json"]["declared_base"],
                         held["declared_base"])
        # AND THERE IS NO OPERAND TO GET WRONG. `compose` takes no `base`.
        import inspect
        self.assertNotIn(
            "base", inspect.signature(review_bindings.compose).parameters)

    def test_the_v12_work_is_the_producers_so_the_line_is_recovered(self):
        documents = self.composed()
        deployment = documents["deployment.json"]
        self.assertEqual(deployment["job_work_id"], WORK)
        self.assertEqual(deployment["review_work_id"], WORK)
        self.assertEqual(
            documents["submission.json"]["jobs"][0]["stages"][0]["work_id"],
            WORK)

    def test_the_source_and_workspace_storage_are_the_producers(self):
        documents = self.composed()
        for one in documents["deployment.json"]["workers"]:
            self.assertEqual(one["deployment"]["nominated_source"],
                             self.source)
            self.assertEqual(one["deployment"]["workspace_storage"],
                             self.storage)

    def test_the_packet_carries_the_exact_subject_it_composed_against(self):
        packet = self.composed()["PACKET.json"]
        self.assertEqual(packet["subject"]["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertEqual(packet["subject"]["head_object"],
                         self.held_subject()["head_object"])
        self.assertEqual(packet["subject"]["producer"]["participant"],
                         self.PRODUCER_PARTICIPANT)


@unittest.skipUnless(os.path.exists(VECTORS), "conformance vector required")
class AnUnattachableProposalIsNotComposedAtAll(ComposingCase):
    """The preflight is wired into composition, not printed beside it."""

    def test_a_wrong_checkpoint_refuses_before_any_document_exists(self):
        said = self.refusal(
            producer=self.producer(checkpoint_id="checkpoint-" + "0" * 8))
        self.assertIn("cannot be reviewed by this deployment", said)
        self.assertIn("WRONG:", said)
        self.assertFalse(os.path.exists(self.run_root))

    def test_a_reviewer_that_is_the_producer_refuses(self):
        operands = self.operands()
        operands["participants"] = dict(
            operands["participants"],
            review=self.PRODUCER_PARTICIPANT,
            review_principal=self.PRODUCER_PRINCIPAL)
        shared = review_bindings._reuse()
        with self.assertRaises(shared.BindingRefusal) as caught:
            review_bindings.compose(**operands)
        self.assertIn("NOT INDEPENDENT AT:", str(caught.exception))

    def test_a_foreign_v12_work_refuses_with_what_the_line_carries(self):
        """And it is `attachment`'s refusal, not the composer's.

        Worth keeping distinct: the named line's own Authority and Work are a
        fact about the SUBJECT, answered before the composer has an opinion,
        and the message names what that line really carries so an operator can
        see what they meant to review.
        """
        with self.assertRaises(attachment.AttachmentRefusal) as caught:
            self.composed(producer=self.producer(work_id=WORK + "-other"))
        said = str(caught.exception)
        self.assertIn("the same line", said)
        self.assertIn(WORK, said)


@unittest.skipUnless(os.path.exists(VECTORS), "conformance vector required")
class TheCompositionCarriesOnlyThisJobsWorkload(ComposingCase):
    def test_one_review_stage_and_no_dependency(self):
        jobs = self.composed()["submission.json"]["jobs"]
        self.assertEqual(len(jobs), 1)
        stages = jobs[0]["stages"]
        self.assertEqual([one["kind"] for one in stages], ["review"])
        self.assertEqual(stages[0]["depends_on"], [])

    def test_the_manifest_requires_findings_and_logs_and_no_proposal(self):
        outputs = self.composed()["deployment.json"]["workers"][0][
            "deployment"]["input_manifest"]["outputs"]
        named = {one["name"]: one for one in outputs}
        self.assertEqual(sorted(named), ["findings", "logs"])
        for one in outputs:
            self.assertTrue(one["required"], one)

    def test_an_implementation_worker_is_configured_and_never_submitted(self):
        documents = self.composed()
        roles = [one["role"] for one in documents["deployment.json"]["workers"]]
        self.assertEqual(sorted(roles), ["implementation", "review"])
        kinds = {one["kind"] for one in
                 documents["submission.json"]["jobs"][0]["stages"]}
        self.assertEqual(kinds, {"review"})

    def test_the_two_roles_share_no_participant_or_principal(self):
        workers = self.composed()["deployment.json"]["workers"]
        seen = {one["deployment"]["participant"] for one in workers}
        held = {one["deployment"]["principal"] for one in workers}
        self.assertEqual(len(seen), 2)
        self.assertEqual(len(held), 2)

    def test_implementation_and_correction_bounds_are_refused_by_name(self):
        for member in review_bindings.FOREIGN_BOUNDS:
            with self.subTest(member=member):
                said = self.refusal(bounds=dict(review_bindings.BOUNDS,
                                                **{member: 1}))
                self.assertIn(member, said)
                self.assertIn("W239533 drives one REVIEW container", said)

    def test_a_second_review_invocation_is_refused(self):
        said = self.refusal(bounds=dict(review_bindings.BOUNDS,
                                        review_invocations=2))
        self.assertIn("ONE review container", said)


@unittest.skipUnless(os.path.exists(VECTORS), "conformance vector required")
class TheCriteriaAskForAJudgmentRatherThanSupplyingOne(ComposingCase):
    """W236087's live failure was a task document that carried its answer."""

    def test_the_criteria_name_no_verdict_for_this_change(self):
        said = self.composed()["task.json"]["instructions"]
        for banned in ("Verdict: accept", "the change is correct",
                       "this change is correct", "you should accept"):
            self.assertNotIn(banned.lower(), said.lower())

    def test_all_three_verdicts_are_offered_as_valid_results(self):
        said = self.composed()["task.json"]["instructions"]
        for one in ("accepted", "changes-requested", "rejected"):
            self.assertIn(one, said)
        self.assertIn("valid review result", said)

    def test_the_reviewer_is_told_it_has_no_correction_stage(self):
        said = self.composed()["task.json"]["instructions"]
        self.assertIn("read-only", said)
        self.assertIn("NOT THE IMPLEMENTER", said)

    def test_the_criteria_are_sealed_at_their_own_byte_length(self):
        documents = self.composed()
        contract = documents["deployment.json"]["workers"][0]["deployment"][
            "input_manifest"]["human_contract"]
        body = json.dumps(documents["task.json"], sort_keys=True).encode()
        self.assertEqual(contract["bytes"], len(body))
        self.assertEqual(documents["PACKET.json"]["criteria"]["content_digest"],
                         contract["content_digest"])


@unittest.skipUnless(os.path.exists(VECTORS), "conformance vector required")
class TheDocumentedEntrypointComposesFromASelectionsDocument(ComposingCase):
    """`review_bindings.py --selections ... --run-root ...`, run as a command.

    The refusal path is what is driven end to end here: it reaches
    `compose`, opens the producer's real control store read-only, and answers
    the exact refusal on stderr with a non-zero status. The accepting path
    continues into `write`, which needs a disposable Authority this case does
    not yet build -- `PROGRESS.md` records that as outstanding rather than
    letting a skipped assertion imply it passed.
    """

    def test_the_command_refuses_a_wrong_checkpoint_with_its_own_words(self):
        place = self.written_selections(
            producer=self.producer(checkpoint_id="checkpoint-" + "0" * 8))
        answer = self.documented(place)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("WRONG:", answer.stdout + answer.stderr)

    def test_the_command_takes_no_base_operand(self):
        """A review reads the base its subject was produced against.

        Exercised through the SAME bound environment as the accepting path, so
        an argparse refusal cannot be confused with an import failure -- which
        is what an earlier version of this case actually measured.
        """
        place = self.written_selections()
        answer = self.documented(place, "--base", "a" * 40)
        self.assertEqual(answer.returncode, 2,
                         f"stdout={answer.stdout}\nstderr={answer.stderr}")
        self.assertIn("unrecognized arguments", answer.stderr)


@unittest.skipUnless(os.path.exists(VECTORS), "conformance vector required")
class TheDocumentedCommandProducesAnAcceptedPacket(ComposingCase):
    """Preparation through composition through the supervisor's validator.

    This is the proof owner reroute 247154 asks for: "actual CLI-through-
    write/held_configuration proof". Nothing is called in-process except the
    reading of what the command wrote.
    """

    def test_the_command_writes_a_packet_the_supervisor_accepts(self):
        import review_supervisor

        place = self.written_selections()
        answer = self.documented(place)
        self.assertEqual(answer.returncode, 0,
                         f"stdout={answer.stdout}\nstderr={answer.stderr}")
        # IT PRINTED A DIGEST FOR EVERY DOCUMENT IT WROTE.
        digests = json.loads(answer.stdout)
        self.assertEqual(
            sorted(digests),
            ["PACKET.json", "adapter.json", "deployment.json", "policy.json",
             "runtime-profile.json", "submission.json", "task.json"])
        for name, held in digests.items():
            with self.subTest(document=name):
                self.assertEqual(len(held), 64)
                self.assertTrue(
                    os.path.exists(os.path.join(self.run_root, name)))

        # AND THE SUPERVISOR HOLDS THE BYTES THE COMMAND WROTE. `held_packet`
        # re-pins the deployment, the submission and the criteria from disk
        # and compares the sealed content digest, so this is the packet
        # validation the run itself would perform, over the packet the
        # documented command actually produced.
        packet = review_supervisor.held_packet(
            os.path.join(self.run_root, "PACKET.json"))
        self.assertEqual(packet["schema"], review_supervisor.PACKET_SCHEMA)
        self.assertEqual(packet["bounds"]["review_invocations"], 1)
        self.assertIs(packet["bounds"]["retry"], False)
        self.assertEqual(packet["subject"]["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertEqual(packet["deployment"]["control_store"],
                         self.control_path)

    def test_the_deployment_it_wrote_passes_the_managers_own_validator(self):
        """Not a second opinion -- the same function, over the written bytes.

        `write` holds the composition before publishing it, so a command that
        exited zero has already been through this. Running it again here over
        what landed on disk is what distinguishes "the composer validated an
        object it had in memory" from "the file an operator will point the
        manager at is one the manager accepts".
        """
        from tools import stage_execution

        answer = self.documented(self.written_selections())
        self.assertEqual(answer.returncode, 0, answer.stderr)
        with open(os.path.join(self.run_root, "deployment.json"),
                  encoding="utf-8") as handle:
            written = json.load(handle)
        with open(os.path.join(self.run_root, "PACKET.json"),
                  encoding="utf-8") as handle:
            packet = json.load(handle)
        # THE PACKET'S OWN BOUND BOUNDARY, not one derived here. Deriving it
        # from the state root put the deployment's mutable state inside the
        # checkout and the validator said so -- which is the disagreement
        # W239528's composer carries a bound `code_boundary` to avoid, and
        # reproducing it in a test would have been testing the test.
        held = stage_execution.held_configuration(
            written, checkout=packet["code_boundary"])
        self.assertIsNotNone(held)

    def test_a_malformed_correction_policy_is_refused_by_the_validator(self):
        """Owned where every other deployment member is owned.

        Review 2026-09-23T12:20:24Z asked for the validator itself to be
        exercised, not just the two accepted values. An unreadable policy
        would otherwise be discovered by `routed`, which runs after a verdict
        has been recorded -- the wrong moment to learn that a deployment
        cannot say what it meant.
        """
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution

        documents = self.composed()
        for policy in ("Decline", "off", "", None, 1):
            with self.subTest(policy=policy):
                written = dict(documents["deployment.json"],
                               correction_policy=policy)
                with self.assertRaises(ContractRefusal) as caught:
                    stage_execution.held_configuration(
                        written, checkout=documents["PACKET.json"][
                            "code_boundary"])
                self.assertIn("correction policy", str(caught.exception))

    def test_the_composed_deployment_declines_the_correction_round(self):
        from tools import stage_execution

        documents = self.composed()
        self.assertEqual(documents["deployment.json"]["correction_policy"],
                         stage_execution.DECLINE_CORRECTION)

    def test_a_refused_composition_writes_no_packet_at_all(self):
        """The refusal path leaves nothing half-written for an operator."""
        place = self.written_selections(
            producer=self.producer(checkpoint_id="checkpoint-" + "0" * 8))
        answer = self.documented(place)
        self.assertNotEqual(answer.returncode, 0)
        self.assertFalse(os.path.exists(
            os.path.join(self.run_root, "PACKET.json")))


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if isinstance(value, type) and issubclass(value, unittest.TestCase) \
                and value.__module__ == __name__ \
                and name not in ("ComposingCase",):
            suite.addTests(loader.loadTestsFromTestCase(value))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
