"""The packet bindings are held against the manager's own validator.

Review 2026-09-22T06:36:24Z asked for concrete proposed documents rather than a
general statement that they are owner selections. This drives `packet_bindings`
over the REAL installed instance's identities and the published worker-contract
conformance vector, holds the result with `stage_execution.held_configuration`
-- the same function the serving deployment and `tools.bootstrap` both run --
and then proves `supervisor.held_packet` accepts the packet it emitted.

WHAT IS NOT CLAIMED. Composing and validating a deployment document is not
running one. No store is opened, no session is minted, no credential is read, no
container starts and no Git operation is performed. The declared base is a
synthetic object name here; the real one is the operator's, from step 4.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import stage_execution

import packet_bindings
import supervisor

HERE = Path(__file__).resolve().parent
CHECKOUT = str(HERE.parents[4])
INSTALL = Path("/home/sl/baton-runs/managed-correction-236087/install")
MANAGER_SOURCE = "/home/sl/baton-runs/managed-correction-236087/manager-source"
VECTORS = (Path(CHECKOUT) / "work/records/2026/08"
           / "finding-v12-isolated-agent-workers/findings"
           / "finding-v12-worker-contract/findings"
           / "finding-worker-control-api-manifests/evidence/vectors.json")
BASE = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


RUN = Path("/home/sl/baton-runs/managed-correction-236087/run")


def inferred_boundary(relocated_tools):
    """`stage_execution._checkout`'s default, reproduced over a given layout.

    Three parents above the module's own file. Reproduced here rather than
    imported so the assertion is about the RULE and not about wherever this
    process happens to have loaded `stage_execution` from.
    """
    return os.path.realpath(os.path.join(
        os.path.dirname(os.path.abspath(
            str(Path(relocated_tools) / "stage_execution.py"))),
        "..", "..", ".."))


@unittest.skipUnless(MANAGER_SOURCE and Path(MANAGER_SOURCE).is_dir(),
                     "the relocated manager source is this check's real "
                     "operand")
class TheInferredCodeBoundaryIsWrongForARelocatedSource(unittest.TestCase):
    """The owner's refused launch, reproduced from the layout that caused it.

    `packet_bindings.write` validated with an explicit boundary and
    `supervisor._compose` let `operations_from` infer one, so a packet that
    passed preparation refused at composition -- after the owner acts had
    already committed. These assert the inference itself and then the whole
    symptom over the operator's own written deployment.
    """

    def test_the_default_answers_the_run_roots_parent(self):
        ordinary = inferred_boundary(Path(CHECKOUT) / "v12/python/tools")
        self.assertEqual(ordinary, CHECKOUT)
        relocated = inferred_boundary(Path(MANAGER_SOURCE) / "tools")
        self.assertEqual(relocated, os.path.dirname(os.path.dirname(
            os.path.realpath(MANAGER_SOURCE))))
        # WHICH IS THE PARENT OF THE RUN ROOT, so the run's own stores are
        # inside it and the copied code is protected only incidentally.
        self.assertTrue(os.path.realpath(MANAGER_SOURCE).startswith(
            relocated + os.sep))
        self.assertNotEqual(relocated, os.path.realpath(MANAGER_SOURCE))

    @unittest.skipUnless((RUN / "deployment.json").exists(),
                         "the operator's written deployment is this check's "
                         "real operand")
    def test_the_written_deployment_refuses_under_the_inferred_boundary(self):
        """The refusal the owner saw, and the boundary that avoids it.

        READ ONLY: `held_configuration` opens no store and starts nothing. The
        operator's run directory is not modified by this check.
        """
        deployment = json.loads((RUN / "deployment.json").read_text())
        relocated = inferred_boundary(Path(MANAGER_SOURCE) / "tools")
        with self.assertRaises(Exception) as caught:
            stage_execution.held_configuration(deployment, checkout=relocated)
        self.assertIn("checkout", str(getattr(caught.exception, "message",
                                              caught.exception)))
        # AND UNDER THE BOUND BOUNDARY the same bytes are accepted.
        held = stage_execution.held_configuration(deployment,
                                                  checkout=MANAGER_SOURCE)
        self.assertEqual(sorted(one["role"] for one in held["workers"]),
                         ["implementation", "review"])


@unittest.skipUnless(INSTALL.exists() and VECTORS.exists(),
                     "the isolated installation and the published worker "
                     "contract vectors are this composition's real operands")
class TheProposedBindingsAreHeldBeforeTheyAreWritten(unittest.TestCase):

    def setUp(self):
        # OUTSIDE THE CHECKOUT, because `held_configuration` refuses a
        # configured mutable root inside the working tree and `/tmp` is a
        # tmpfs on this host, which the workspace boundary refuses too.
        self.root = tempfile.mkdtemp(prefix="w236087-bindings-",
                                     dir="/var/tmp")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.run_root = os.path.join(self.root, "run")
        self.source = os.path.join(self.root, "fixture-source")
        os.makedirs(self.source)
        shutil.copy(str(HERE / "fixture" / "harness.py"),
                    os.path.join(self.source, "harness.py"))
        instance = json.loads((INSTALL / "instance.json").read_text())
        configuration = json.loads(Path(instance["deployment"]).read_text())
        self.selections = {
            "instance": {
                "authority_store": configuration["authority_store"],
                "authority_uuid": instance["authority_uuid"],
                "integration_store": configuration["integration_store"],
                "job_store": instance["job_store"],
                "control_store": instance["control_store"],
                "integration_profile": configuration["integration_profile"],
                "retention_policy_digest":
                    configuration["retention_policy_digest"],
                "runtime_path": os.path.join(INSTALL, "distro"),
                "build_commit": instance["identity"]["build_stamp"]["commit"]},
            "source_root": self.source,
            "image_reference": "baton-v12-claude-worker:w236087-236349",
            "image_digest": "sha256:2e9e84ff23319778760d5b22c70d543d4290"
                            "931510a3ab3ecf40bcdaad7456bd",
            "cli_build": "2.1.247",
            "manager_source": MANAGER_SOURCE,
            "supervisor_path": str(HERE / "supervisor.py"),
            "vectors": str(VECTORS),
            "credential_sources": os.path.join(self.root, "registry"),
            "credential_profile": {"api": {"provider": "user-registry",
                                           "reference": "claude/one"}},
            # REAL RETAINED EVIDENCE, not a sentinel: R4 refused the all-zero
            # placeholder, and the composer now refuses it too.
            "evidence_digest": "sha256:" + sha256(
                str(Path(CHECKOUT) / "work/records/2026/09"
                    / "finding-v12-production-context-qualification-preparation"
                    / "REVIEW-EVIDENCE-235998.json")),
            "provider_network": "baton-provider-egress",
            "run_id": "managed-correction-236087",
            "work": "W236087", "claim": 236529,
            "note": "one managed correction; W236087",
            "participants": {
                # THE WORK CARRIES ITS AUTHORITY'S PREFIX, which
                # `contracts.manifest._relate_work_ref` requires: a manifest
                # naming a Work from another Authority is refused before
                # anything is composed.
                "work_id": instance["authority_uuid"][:8] + "-W1",
                "implementation": "baton.implementer",
                "implementation_principal": "implementer-principal",
                "review": "baton.reviewer",
                "review_principal": "reviewer-principal",
                "receipts": {"verification": "baton.verifier",
                             "review": "baton.approver-review",
                             "approval": "baton.approver"},
                "worker_files": {
                    "opt/baton/claude_agent.py":
                        "abdf903da3c767f3fe9babf84e4499f455da968a61ee3c"
                        "975b9899988354bb4d"},
                "fixture_files": {
                    "harness.py": sha256(os.path.join(self.source,
                                                      "harness.py"))}}}

    def composed(self, **changed):
        selections = dict(self.selections)
        selections.update(changed)
        return packet_bindings.compose(base=BASE, run_root=self.run_root,
                                       **selections)

    # -- the composition itself ---------------------------------------------

    def test_the_deployment_is_accepted_by_the_managers_own_validator(self):
        documents = self.composed()
        packet_bindings.write(self.run_root, documents, checkout=CHECKOUT)
        held = stage_execution.held_configuration(documents["deployment.json"],
                                                  checkout=CHECKOUT)
        self.assertEqual(held["schema"], stage_execution.CONFIG_SCHEMA)
        self.assertEqual(sorted(one["role"] for one in held["workers"]),
                         ["implementation", "review"])

    def test_the_implementation_worker_is_the_contextual_schema(self):
        from tools import single_worker

        documents = self.composed()
        workers = {one["role"]: one["deployment"]
                   for one in documents["deployment.json"]["workers"]}
        self.assertEqual(workers["implementation"]["schema"],
                         single_worker.CONTEXT_CONFIG_SCHEMA)
        self.assertEqual(workers["implementation"]["provider_context"]["mode"],
                         "required")
        # AND THE REVIEW WORKER IS NOT. A reviewer that resumed the
        # implementer's conversation would not be an independent review.
        self.assertEqual(workers["review"]["schema"],
                         single_worker.CONFIG_SCHEMA)
        self.assertNotIn("provider_context", workers["review"])

    def test_the_context_profile_is_the_candidate_session_profile(self):
        from baton_v12.contracts import digest
        from baton_v12.worker_manager import provider_context as context

        documents = self.composed()
        profile = documents["context-profile.json"]
        # THE VALIDATOR THE CERTIFICATION USES, run on the proposed document.
        held = context._profile(profile)
        self.assertEqual(held["schema"], context.SESSION_PROFILE_SCHEMA)
        self.assertEqual(held["qualification"], "candidate")
        self.assertEqual(held["state_paths"],
                         [packet_bindings.CONTEXT_STATE_PATH])
        self.assertEqual(held["argv_policy_digest"],
                         digest(context.ARGV_POLICY))
        self.assertEqual(held["environment_policy_digest"],
                         digest(context.ENVIRONMENT_POLICY))
        workers = {one["role"]: one["deployment"]
                   for one in documents["deployment.json"]["workers"]}
        self.assertEqual(
            workers["implementation"]["provider_context"]["profile_digest"],
            digest(profile))

    def test_the_three_identities_are_digests_of_readable_documents(self):
        """An owner can read what was proposed instead of approving a hash."""
        from baton_v12.contracts import digest

        documents = self.composed()
        deployment = documents["deployment.json"]["workers"][0]["deployment"]
        self.assertEqual(deployment["profile_digest"],
                         digest(documents["runtime-profile.json"]))
        self.assertEqual(deployment["policy_digest"],
                         digest(documents["policy.json"]))
        self.assertEqual(deployment["adapter_digest"],
                         digest(documents["adapter.json"]))

    def test_the_submission_carries_the_declared_provider_turn_ceiling(self):
        documents = self.composed()
        job = documents["submission.json"]["jobs"][0]
        self.assertEqual(job["execution_limits"],
                         {"provider_turn_seconds": 180})
        self.assertEqual([one["kind"] for one in job["stages"]],
                         ["implementation", "review"])

    def test_the_manifest_declares_the_reserved_receipt_output(self):
        documents = self.composed()
        manifest = (documents["deployment.json"]["workers"][0]["deployment"]
                    ["input_manifest"])
        names = [one["name"] for one in manifest["outputs"]]
        self.assertIn("provider-context-receipt", names)
        self.assertIn("proposal", names)
        source = manifest["sources"][0]
        self.assertEqual(source["destination"], "source")
        self.assertEqual(source["content_manifest"]["entry_count"], 0)
        self.assertEqual(source["consumption"]["baton.source-boundary/1"]
                         ["profile"], "git-line")

    # -- what it refuses -----------------------------------------------------

    def test_a_network_none_provider_deployment_is_refused(self):
        """R4: the image-inspection posture is not the live provider's.

        `oci.py` passes this straight to `--network`, and the worker reaches an
        external Claude API; a container with no network could never answer the
        question the run exists to ask.
        """
        with self.assertRaisesRegex(packet_bindings.BindingRefusal,
                                    "could never answer the question"):
            self.composed(provider_network="none")
        for value in ("", None, 3):
            with self.subTest(network=value):
                with self.assertRaisesRegex(
                        packet_bindings.BindingRefusal,
                        "one non-empty engine network name"):
                    self.composed(provider_network=value)

    def test_the_selected_network_reaches_every_deployment_byte(self):
        documents = self.composed()
        self.assertEqual(documents["runtime-profile.json"]["network"],
                         "baton-provider-egress")
        self.assertEqual(documents["adapter.json"]["network"],
                         "baton-provider-egress")
        for one in documents["deployment.json"]["workers"]:
            with self.subTest(role=one["role"]):
                self.assertEqual(one["deployment"]["network"],
                                 "baton-provider-egress")

    def test_a_sentinel_evidence_digest_is_refused(self):
        """R4: an all-zero digest said `bound` and named nothing."""
        with self.assertRaisesRegex(packet_bindings.BindingRefusal,
                                    "a sentinel, not retained evidence"):
            self.composed(evidence_digest="sha256:" + "0" * 64)

    def test_the_task_states_requirements_and_not_a_review_script(self):
        """The first live run's defect, in the bytes that caused it.

        `claude_agent` composes the implementation prompt as work to do and
        the review prompt as requirements to assess, from this same string. A
        four-stage script here is a script the implementation role executes --
        which is what happened: it implemented, reviewed itself, corrected,
        reviewed again and answered "Verdict: accept". See LIVE-RUN-239365.md.
        """
        documents = self.composed()
        said = documents["task.json"]["instructions"]
        # WHAT IT MUST SAY: the requirement, and that judging is not its stage.
        self.assertIn("prints READY followed by a newline", said)
        self.assertIn("Change only harness.py", said)
        self.assertIn("python3 harness.py", said)
        self.assertIn("Do not review, assess or grade your own work", said)
        self.assertIn("do not write a verdict", said)
        self.assertIn("an independent reviewer with its own turn does that",
                      said)
        # WHAT IT MUST NOT SAY: any stage it is not, or any verdict to return.
        for forbidden in ("FIRST REVIEW", "FINAL REVIEW", "CORRECTION",
                          "changes-requested", "accept only if",
                          "Accept only if", "ACCEPTANCE.md"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, said)

    def test_the_implementation_prompt_carries_no_review_script(self):
        """The prompt the worker will really compose, from these bytes."""
        import claude_agent

        documents = self.composed()
        prompt = claude_agent._prompt(documents["task.json"])
        self.assertIn("Edit files here directly", prompt)
        self.assertIn("Do not review, assess or grade your own work", prompt)
        for forbidden in ("FIRST REVIEW", "FINAL REVIEW", "changes-requested"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, prompt)

    def test_the_review_prompt_presents_them_as_requirements(self):
        """And the reviewer gets the same requirements, framed to assess."""
        import claude_agent

        documents = self.composed()
        prompt = claude_agent._review_prompt(
            documents["task.json"], "/input/source", "review-report.json")
        self.assertIn("You are reviewing a change on a read-only source tree",
                      prompt)
        self.assertIn("The change was made to satisfy these requirements",
                      prompt)
        self.assertIn("prints READY followed by a newline", prompt)
        self.assertIn("not evidence that it passed", prompt)

    def test_the_preflight_names_every_missing_authority_preparation(self):
        """R4: a participant string is not a registered participant."""
        from baton_v12.authority import Authority

        place = os.path.join(self.root, "empty-authority.sqlite3")
        authority = Authority.create(place, authority_uuid="0" * 32)
        self.addCleanup(authority.dispose)
        documents = self.composed()
        missing = packet_bindings.preflight(
            authority, documents, self.selections["participants"])
        said = " | ".join(missing)
        self.assertIn("does not exist or is unreadable", said)
        # AND IT STOPS AT THE FIRST CONCLUSIVE GAP rather than reporting
        # capability absences for a Work that does not exist.
        self.assertEqual(len(missing), 1)

    def test_the_preflight_reports_what_it_cannot_prove(self):
        from baton_v12.authority import Authority

        participants = self.selections["participants"]
        place = os.path.join(self.root, "partial-authority.sqlite3")
        authority = Authority.create(place, authority_uuid="0" * 32)
        self.addCleanup(authority.dispose)
        authority.create_work(participants["work_id"], "impl",
                              contract="v12-assignment-1",
                              operation_id="preflight-fixture")
        documents = self.composed()
        missing = packet_bindings.preflight(authority, documents, participants)
        said = " | ".join(missing)
        self.assertIn("holds no 'verify' capability", said)
        self.assertIn("UNVERIFIABLE HERE", said)
        self.assertIn("route's handlers", said)

    def test_the_code_boundary_defaults_to_the_manager_source(self):
        documents = self.composed()
        self.assertEqual(documents["PACKET.json"]["code_boundary"],
                         MANAGER_SOURCE)

    def test_a_boundary_that_does_not_cover_the_source_refuses(self):
        with self.assertRaisesRegex(packet_bindings.BindingRefusal,
                                    "would not protect the code"):
            self.composed(code_boundary=self.root)

    def test_the_written_packet_validates_under_its_own_boundary(self):
        """No `checkout` operand: the packet's bound value is the only one.

        Passing a different one here is exactly what let preparation and
        composition disagree.
        """
        documents = self.composed()
        places = packet_bindings.write(self.run_root, documents)
        held = supervisor.held_packet(places["PACKET.json"])
        self.assertEqual(held["code_boundary"], MANAGER_SOURCE)

    def test_an_unresolved_declared_base_refuses_rather_than_placeholding(self):
        for value in ("BASE_FROM_STEP_4", "a" * 39, None, ""):
            with self.subTest(base=value):
                with self.assertRaisesRegex(
                        packet_bindings.BindingRefusal,
                        "one full lower-case object name"):
                    packet_bindings.compose(base=value,
                                            run_root=self.run_root,
                                            **self.selections)

    def test_two_roles_sharing_a_principal_are_refused_before_writing(self):
        documents = self.composed(participants=dict(
            self.selections["participants"],
            review_principal="implementer-principal"))
        with self.assertRaises(Exception):
            packet_bindings.write(self.run_root, documents, checkout=CHECKOUT)
        self.assertFalse(os.path.exists(
            os.path.join(self.run_root, "deployment.json")),
            "a composition the manager refuses must not reach the disk")

    # -- and the packet the supervisor will read -----------------------------

    def test_the_written_packet_is_accepted_by_held_packet(self):
        documents = self.composed()
        places = packet_bindings.write(self.run_root, documents,
                                       checkout=CHECKOUT)
        held = supervisor.held_packet(places["PACKET.json"])
        self.assertEqual(held["run_id"], "managed-correction-236087")
        self.assertEqual(held["bounds"]["turn_seconds"], 180)
        self.assertEqual(held["manager_source"]["path"], MANAGER_SOURCE)
        self.assertEqual(held["manager_source"]["file_count"],
                         len(held["manager_source"]["files"]))

    def test_the_written_packet_binds_the_bytes_that_were_written(self):
        documents = self.composed()
        places = packet_bindings.write(self.run_root, documents,
                                       checkout=CHECKOUT)
        packet = json.loads(Path(places["PACKET.json"]).read_text())
        self.assertEqual(packet["deployment"]["config_sha256"],
                         sha256(places["deployment.json"]))
        self.assertEqual(packet["submission"]["sha256"],
                         sha256(places["submission.json"]))
        self.assertEqual(packet["context"]["profile_sha256"],
                         sha256(places["context-profile.json"]))
        # AND A MOVED BYTE REFUSES, which is the whole point of binding them.
        Path(places["submission.json"]).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(supervisor.SupervisorRefusal,
                                    "the Job submission"):
            supervisor.held_packet(places["PACKET.json"])


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
