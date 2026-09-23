"""The ACTUAL successor selections and documented entrypoint. W239528 R3.

Review 2026-09-23T01:02:06Z: "The 121 tests still compose generic fixture
selections or SELECTIONS-FAILURE; none references SELECTIONS-SUCCESSOR-243284
or its operator document. Exercise this actual successor selection and
documented entrypoint deterministically, substituting only explicit owner
operands, and assert the fresh authority/store, base, run/Job, revised
supervisor digest and 180/300/60 bindings."

WHAT IS SUBSTITUTED AND WHAT IS NOT. Only the members the selections file marks
`<OWNER>` are replaced, and only with this case's own disposable identities --
the Authority and participants the fixture registered, the fixture repository
it created, a fixture credential reference. Every member the dossier BINDS
travels verbatim: the successor snapshot, the code boundary, the image and
adapter digests, the installed runtime, the vectors, the run identity and the
bounds. If the delivered file drifts from what the operator document promises,
these fail.

WHAT THIS IS NOT. It is not successful-baseline readiness and it authorizes no
execution. The custody-mode blocker is unresolved and
`TheDocumentSaysWhatItIsNotReadyFor` asserts the document still says so.

No deployed store is opened, no container starts, no credential is read and no
live provider is called.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import baseline
import baseline_bindings
from test_baseline_bindings import (NETWORK, VECTORS,
                                    TheGeneratedPacketDrivesOneImplementation)

HERE = Path(__file__).resolve().parent
SELECTIONS = HERE / "SELECTIONS-SUCCESSOR-243284.json"
DOCUMENT = HERE / "OPERATOR-SUCCESSOR-243284.md"
SNAPSHOT = Path("/home/sl/baton-runs/single-implementation-242687"
                "/manager-source")
RUN_ID = "single-implementation-243284"
BOUNDS = {"turn_seconds": 180, "total_seconds": 300, "cleanup_seconds": 60,
          "implementer_invocations": 1, "retry": False}


def owner_operand(value):
    """Is this member still an unresolved owner choice?"""
    return isinstance(value, str) and value.startswith("<OWNER")


class TheDeliveredSelectionsSayWhatTheDocumentPromises(unittest.TestCase):
    """Read as delivered. No composition, no substitution."""

    def setUp(self):
        self.chosen = json.loads(
            SELECTIONS.read_text(encoding="utf-8"))["compose"]

    def test_the_bounds_are_the_selected_ones(self):
        self.assertEqual(self.chosen["bounds"], BOUNDS)

    def test_the_bound_source_is_the_verified_successor_snapshot(self):
        self.assertEqual(self.chosen["manager_source"], str(SNAPSHOT))
        self.assertEqual(self.chosen["code_boundary"], str(SNAPSHOT))

    def test_every_store_is_the_successors_own(self):
        """The accepted isolation boundary: every earlier instance now holds
        other work, and none of them may appear here."""
        for member in ("authority_store", "job_store", "control_store",
                       "integration_store"):
            with self.subTest(store=member):
                held = self.chosen["instance"][member]
                self.assertIn("/single-implementation-243284/", held)
                for older in ("single-implementation-239528",
                              "single-implementation-success-239528",
                              "single-implementation-242687",
                              "managed-correction-236087"):
                    self.assertNotIn(older, held)

    def test_the_run_identity_is_new(self):
        self.assertEqual(self.chosen["run_id"], RUN_ID)

    def test_the_supervisor_is_this_dossiers_current_one(self):
        self.assertEqual(self.chosen["supervisor_path"],
                         str(HERE / "baseline.py"))

    def test_the_unresolved_operands_are_marked_and_bounded(self):
        """What is still the owner's is NAMED, and nothing else is."""
        bound = ("cli_build", "code_boundary", "image_digest",
                 "image_reference", "manager_source", "run_id",
                 "supervisor_path", "vectors", "work", "claim", "note",
                 "bounds", "credential_sources")
        for member in bound:
            with self.subTest(member=member):
                self.assertFalse(owner_operand(self.chosen.get(member)),
                                 f"{member} should be bound, not an operand")
        instance = self.chosen["instance"]
        for member in ("authority_store", "job_store", "control_store",
                       "integration_store", "runtime_path", "build_commit"):
            with self.subTest(member=member):
                self.assertFalse(owner_operand(instance[member]))

    def test_the_blocker_travels_with_the_selections(self):
        held = json.loads(SELECTIONS.read_text(encoding="utf-8"))
        self.assertIn("_unresolved_blocker", held)
        self.assertIn("custody", held["_unresolved_blocker"]["what"].lower())
        self.assertIn("NOT successful-baseline ready", held["_status"])


class TheDocumentSaysWhatItIsNotReadyFor(unittest.TestCase):
    """R3's last point, and owner reroute 243281's standing instruction."""

    def setUp(self):
        self.said = DOCUMENT.read_text(encoding="utf-8")

    def test_it_opens_with_the_unresolved_blocker(self):
        head = self.said.split("## Step 0", 1)[0]
        self.assertIn("NOT successful-baseline ready", head)
        self.assertIn("custody-mode failure is unresolved", head)

    def test_the_base_is_bound_rather_than_assumed(self):
        """It used to invoke the composer with an unassigned `$BASE`."""
        self.assertIn('SOURCE="$ROOT/fixture-source"', self.said)
        self.assertIn('BASE="$(', self.said)
        self.assertIn('--base "$BASE"', self.said)

    def test_the_preparation_block_is_the_successors_own(self):
        """It used to link a step 5a that opens the 239528 Authority store."""
        block = self.said.split("## Step 5a", 1)[1].split("## Steps", 1)[0]
        self.assertIn("single-implementation-243284", block)
        self.assertIn('assert "single-implementation-243284" in store', block)
        self.assertNotIn(
            "/home/sl/baton-runs/single-implementation-239528/db/", block)

    def test_the_accepted_failure_packet_is_not_misattributed(self):
        """It used to credit the REFUSED draft's 900-second bound and
        pre-correction snapshot to the ACCEPTED failure packet."""
        table = self.said.split("## What changed", 1)[1].split("### Why", 1)[0]
        self.assertIn("was ACCEPTED and already carries the corrected", table)
        self.assertIn("120 / 30", table)
        self.assertIn("refused draft", table)

    def test_it_names_the_bounds_it_selects(self):
        self.assertIn("300 / 60", self.said)
        self.assertIn("`turn_seconds` = 180", self.said)


@unittest.skipUnless(VECTORS.exists() and SNAPSHOT.is_dir(),
                     "the composition's real operands")
class TheSuccessorSelectionsCompose(TheGeneratedPacketDrivesOneImplementation):
    """The delivered file, composed with ONLY its `<OWNER>` members filled."""

    def selections(self):
        chosen = dict(json.loads(
            SELECTIONS.read_text(encoding="utf-8"))["compose"])
        # ONLY THE OWNER OPERANDS, and only with this case's own identities.
        chosen["instance"] = dict(
            chosen["instance"],
            authority_store=self.authority_path,
            authority_uuid=self.config["authority_uuid"],
            integration_store=self.integration_store,
            job_store=os.path.join(self.root, "jobs.sqlite3"),
            control_store=os.path.join(self.root, "control.sqlite3"),
            integration_profile={"profile_kind": "git", "profile_version": 1,
                                 "integrator_participant": "baton.integrator",
                                 "instructions_digest": "sha256:" + "e" * 64},
            retention_policy_digest=self.config["retention_policy_digest"],
            runtime_path=self.written_runtime_root())
        chosen["participants"] = dict(
            chosen["participants"],
            work_id=self.work,
            implementation=self.config["participant"],
            implementation_principal=self.config["principal"],
            review="baton.reviewer",
            review_principal=self.principals["baton.reviewer"],
            receipts={"verification": "baton.verifier",
                      "review": "baton.approver-review",
                      "approval": "baton.approver"},
            fixture_files={"harness.py": self.digest_of(
                os.path.join(self.source, "harness.py"))})
        chosen["credential_profile"] = {"api": {"provider": "fixture",
                                                "reference": "fixture/one"}}
        chosen["evidence_digest"] = "sha256:" + "d" * 64
        chosen["provider_network"] = NETWORK
        chosen["source_root"] = self.source
        # `manager_source` and `code_boundary` travel VERBATIM: they are the
        # delivered bindings and substituting them would test a tree nobody
        # ships. The composer hashes the real 106-file successor snapshot, and
        # the documented child imports from it.
        return chosen

    def test_the_delivered_selections_compose_and_hold(self):
        documents, places = self.generate()
        packet = json.loads(
            Path(places["PACKET.json"]).read_text(encoding="utf-8"))
        self.assertEqual(packet["bounds"], BOUNDS)
        self.assertEqual(packet["run_id"], RUN_ID)
        self.assertEqual(packet["submission"]["job_id"], "job-" + RUN_ID)
        self.assertEqual(packet["context"]["job_id"], "job-" + RUN_ID)
        # THE SUPERVISOR DIGEST IS THIS DOSSIER'S CURRENT baseline.py, which
        # carries the interruption and no-progress corrections.
        self.assertEqual(packet["supervisor"]["path"],
                         str(HERE / "baseline.py"))
        self.assertEqual(packet["supervisor"]["sha256"],
                         self.digest_of(str(HERE / "baseline.py")))
        # AND THE DECLARED BASE IS THE FIXTURE'S OWN HEAD.
        self.assertEqual(documents["task.json"]["declared_base"], self.base)
        self.assertEqual(
            documents["deployment.json"]["line_declared_base"], self.base)
        held = baseline.held_packet(places["PACKET.json"])
        self.assertEqual(held["bounds"]["total_seconds"], 300)
        self.assertEqual(held["bounds"]["cleanup_seconds"], 60)

    def test_the_documented_composer_command_runs_over_them(self):
        """The entrypoint as the document prints it: an explicit interpreter,
        `PYTHONPATH` bound to the source and nothing inherited, absolute
        paths, and `--base` supplied."""
        run_root = os.path.join(self.root, "successor-run")
        place = Path(self.root) / "successor-selections.json"
        place.write_text(json.dumps({"compose": self.selections()}, indent=2,
                                    sort_keys=True), encoding="utf-8")
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        environment["PYTHONPATH"] = str(SNAPSHOT)
        answer = subprocess.run(
            [sys.executable, str(HERE / "baseline_bindings.py"),
             "--selections", str(place), "--base", self.base,
             "--run-root", run_root],
            capture_output=True, text=True, timeout=300, env=environment,
            cwd=os.sep)
        self.assertEqual(answer.returncode, 0,
                         f"stdout={answer.stdout}\nstderr={answer.stderr}")
        printed = json.loads(answer.stdout)
        self.assertIn("PACKET.json", printed)
        packet = json.loads(
            Path(run_root, "PACKET.json").read_text(encoding="utf-8"))
        self.assertEqual(packet["bounds"], BOUNDS)
        self.assertEqual(packet["submission"]["job_id"], "job-" + RUN_ID)

    def test_an_unbound_base_is_refused_by_name(self):
        """What the document's old unassigned `$BASE` would have expanded to."""
        with self.assertRaises(baseline_bindings.BindingRefusal) as caught:
            baseline_bindings.compose(base="", run_root=self.root,
                                      **self.selections())
        self.assertIn("one full lower-case object name", str(caught.exception))


ARTIFACT = HERE / "IMAGE-ARTIFACT-244216.json"
CORRECTED = HERE / "SELECTIONS-SUCCESSOR-244216.json"
CORRECTED_DOCUMENT = HERE / "OPERATOR-SUCCESSOR-244216.md"
ACCEPTED_ADAPTER = (
    "18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d")
SUPERSEDED_ADAPTER = (
    "abdf903da3c767f3fe9babf84e4499f455da968a61ee3c975b9899988354bb4d")
PRESERVED_IMAGE_DIGEST = (
    "sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd")


class TheCorrectedImageIsWhatThePacketBinds(unittest.TestCase):
    """Owner reroute 244214: "bind actual image and worker digests".

    Read as delivered. The artefact record is the one `image_244216.py` wrote
    from a container started FROM the image; these assert the SELECTIONS agree
    with it, because a packet that named a different digest than the one that
    was verified would bind an image nobody checked.
    """

    def setUp(self):
        self.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.chosen = json.loads(
            CORRECTED.read_text(encoding="utf-8"))["compose"]

    def test_the_packet_binds_the_artefact_that_was_verified(self):
        self.assertEqual(self.chosen["image_reference"],
                         self.artifact["reference"])
        self.assertEqual(self.chosen["image_digest"],
                         self.artifact["image_config_digest"])

    def test_it_binds_the_accepted_adapter_and_not_the_superseded_one(self):
        held = self.chosen["participants"]["worker_files"]
        self.assertEqual(held["opt/baton/claude_agent.py"], ACCEPTED_ADAPTER)
        self.assertNotEqual(held["opt/baton/claude_agent.py"],
                            SUPERSEDED_ADAPTER)
        self.assertEqual(
            self.artifact["accepted_adapter"]["sha256"], ACCEPTED_ADAPTER)
        self.assertEqual(
            self.artifact["accepted_adapter"]["provider_umask"], "0o77")

    def test_every_bound_worker_file_is_one_the_image_carries(self):
        inside = self.artifact["all_worker_files"]
        for name, digest in sorted(
                self.chosen["participants"]["worker_files"].items()):
            with self.subTest(file=name):
                self.assertEqual(inside.get(name), digest)

    def test_the_new_image_is_distinct_from_the_preserved_one(self):
        self.assertNotEqual(self.artifact["image_config_digest"],
                            PRESERVED_IMAGE_DIGEST)
        self.assertEqual(self.artifact["supersedes"]["image_config_digest"],
                         PRESERVED_IMAGE_DIGEST)
        self.assertIs(self.artifact["supersedes"]["preserved"], True)
        self.assertEqual(self.artifact["supersedes"]["claude_agent_sha256"],
                         SUPERSEDED_ADAPTER)

    def test_the_bounds_and_identities_are_the_selected_ones(self):
        self.assertEqual(self.chosen["bounds"], BOUNDS)
        self.assertEqual(self.chosen["run_id"], "single-implementation-244216")
        for member in ("authority_store", "job_store", "control_store",
                       "integration_store"):
            with self.subTest(store=member):
                self.assertIn("/single-implementation-244216/",
                              self.chosen["instance"][member])

    def test_the_artefact_was_verified_from_inside_the_image(self):
        """Not from the build context. The recipe makes this point about
        itself and the record has to be able to say which it did."""
        self.assertIn("started FROM the image",
                      self.artifact["verified_how"])
        self.assertIn("no provider ran", self.artifact["verified_how"])

    def test_the_document_says_what_the_run_can_and_cannot_answer(self):
        said = CORRECTED_DOCUMENT.read_text(encoding="utf-8")
        self.assertIn("sha256:c862c055", said)
        self.assertIn("If it is `sha256:2e9e84ff", said)
        self.assertIn("Cannot", said)
        self.assertIn("new finding, not a failure of this packet", said)
        self.assertIn("180 / 300 / 60", said.replace("180 / 300 / 60",
                                                     "180 / 300 / 60"))

    def test_what_it_cannot_establish_travels_with_the_selections(self):
        held = json.loads(CORRECTED.read_text(encoding="utf-8"))
        self.assertIn("_what_this_can_answer", held)
        self.assertIn("explicit chmod",
                      held["_what_this_can_answer"]["cannot"])
        self.assertIn("not_authorized_here", held["_what_this_can_answer"])


def load_tests(loader, tests, pattern):
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (TheDeliveredSelectionsSayWhatTheDocumentPromises,
                 TheCorrectedImageIsWhatThePacketBinds,
                 TheDocumentSaysWhatItIsNotReadyFor,
                 TheSuccessorSelectionsCompose):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite
