"""The documented preparation, driven through supported interfaces. R1.

Review 2026-09-23T03:30:58Z: "OPERATOR244216 links step5a exactly but that
Python block hardcodes 243284 SEL and asserts 243284 store; selecting new
244216 file still raises AssertionError before Authority.open. Supply
self-contained or parameterized new-instance preparation and test actual new
selections through preparation/composition." Owner reroute 244290: "Test the
documented preparation and composition through disposable supported
interfaces, not only JSON/prose comparisons."

WHAT IS REAL HERE. `prepare_instance.prepare` against a DISPOSABLE Authority
made with `Authority.create`, performing the actual `create_work`,
`add_route_handler`, `grant_capability` and `set_policy` acts and reading them
back through the Authority's own public readers. Then the same selections go
through `baseline_bindings.compose`, so preparation and composition are
exercised over ONE document rather than compared as prose.

WHAT IS SUBSTITUTED. Only the members `SELECTIONS-SUCCESSOR-244216.json` marks
`<OWNER>`, and only with this case's own disposable identities. The bound
members -- the image reference and digest, the worker-file digests, the
snapshot, the bounds, the run identity -- travel verbatim.

NO DEPLOYED INSTANCE IS TOUCHED. Every Authority here is created in a
temporary directory and disposed; no Job or control store is opened, no
container starts, no credential is read and no provider runs.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import baton_v12
from baton_v12.authority import Authority

import baseline_bindings
import prepare_instance
from test_baseline_bindings import (NETWORK, VECTORS,
                                    TheGeneratedPacketDrivesOneImplementation)

HERE = Path(__file__).resolve().parent
SELECTIONS = HERE / "SELECTIONS-SUCCESSOR-244216.json"
DOCUMENT = HERE / "OPERATOR-SUCCESSOR-244216.md"
RUN_ID = "single-implementation-244216"
BASE = "a" * 40


def delivered():
    return dict(json.loads(SELECTIONS.read_text(encoding="utf-8"))["compose"])


class TheFreshnessCheckIsDerivedNotHardcoded(unittest.TestCase):
    """The defect one release later, refused.

    The old block asserted a literal `single-implementation-243284`. This
    derives the marker from the selections' own `run_id`, so it moves with the
    packet instead of having to be rewritten for each one.
    """

    def test_the_delivered_selections_are_fresh_for_their_own_run(self):
        self.assertEqual(prepare_instance.fresh(delivered()), RUN_ID)

    def test_a_store_that_does_not_name_this_run_is_refused(self):
        chosen = delivered()
        chosen["instance"] = dict(chosen["instance"],
                                  job_store="/tmp/somewhere/jobs.sqlite3")
        with self.assertRaises(prepare_instance.PreparationRefusal) as caught:
            prepare_instance.fresh(chosen)
        self.assertIn("does not name this run", str(caught.exception))

    def test_a_store_naming_a_consumed_instance_is_refused_by_name(self):
        """The accepted isolation boundary: every earlier root holds other
        work and is preserved evidence."""
        for older in prepare_instance.CONSUMED:
            with self.subTest(older=older):
                chosen = delivered()
                chosen["instance"] = dict(
                    chosen["instance"],
                    # The run IS named, as a component, so this reaches the
                    # consumed-root refusal rather than the marker one.
                    control_store=f"/home/sl/baton-runs/{older}/"
                                  f"{RUN_ID}/control.sqlite3")
                with self.assertRaises(
                        prepare_instance.PreparationRefusal) as caught:
                    prepare_instance.fresh(chosen)
                self.assertIn("preserved evidence", str(caught.exception))

    def test_the_predecessors_selections_are_fresh_for_THEIR_run(self):
        """The check the old block could not make: it is not that 243284 is
        wrong, it is that a literal cannot answer for two packets."""
        older = json.loads(
            (HERE / "SELECTIONS-SUCCESSOR-243284.json").read_text(
                encoding="utf-8"))["compose"]
        self.assertEqual(prepare_instance.fresh(older),
                         "single-implementation-243284")

    def test_unresolved_owner_operands_are_named(self):
        still = prepare_instance.unresolved(delivered())
        self.assertTrue(still, "the delivered file should still have some")
        self.assertIn("provider_network", still)
        for one in still:
            with self.subTest(member=one):
                self.assertNotIn(" ", one)


class ThePreparationActsRunAgainstADisposableAuthority(unittest.TestCase):
    """The acts themselves, read back through the Authority's own readers."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="w239528-preparation-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.uuid = "0000024400000000000000000000244e"
        self.store = str(self.root / "authority.sqlite3")
        Authority.create(self.store, authority_uuid=self.uuid).dispose()

    def resolved(self):
        """The delivered selections with ONLY their `<OWNER>` members filled."""
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"], authority_store=self.store,
            authority_uuid=self.uuid,
            job_store=str(self.root / f"{RUN_ID}-jobs.sqlite3"),
            control_store=str(self.root / f"{RUN_ID}-control.sqlite3"),
            integration_store=str(self.root / f"{RUN_ID}-integration.sqlite3"),
            integration_profile={"profile_kind": "git", "profile_version": 1,
                                 "integrator_participant": "baton.integrator",
                                 "instructions_digest": "sha256:" + "e" * 64},
            retention_policy_digest="sha256:" + "c" * 64)
        chosen["participants"] = dict(
            chosen["participants"], work_id="00000244-W1",
            implementation="baton.impl", implementation_principal="impl-one",
            review="baton.reviewer", review_principal="review-one",
            receipts={"verification": "baton.verifier",
                      "review": "baton.approver-review",
                      "approval": "baton.approver"},
            fixture_files={"harness.py": "0" * 64})
        chosen["credential_profile"] = {"api": {"provider": "fixture",
                                                "reference": "fixture/one"}}
        chosen["evidence_digest"] = "sha256:" + "d" * 64
        chosen["provider_network"] = NETWORK
        chosen["source_root"] = str(self.root / "fixture-source")
        return chosen

    def prepared(self, chosen=None):
        chosen = self.resolved() if chosen is None else chosen
        authority = Authority.open(self.store,
                                   expected_authority_uuid=self.uuid)
        try:
            return prepare_instance.prepare(
                authority, chosen, base=BASE,
                operation_id="w239528-preparation-probe")
        finally:
            authority.dispose()

    def test_it_creates_the_selected_work_and_sets_the_canonical_target(self):
        held = self.prepared()
        self.assertEqual(held["work_id"], "00000244-W1")
        self.assertEqual(held["canonical_target"], BASE)
        authority = Authority.open(self.store,
                                   expected_authority_uuid=self.uuid)
        try:
            projected = authority.project_work("00000244-W1")
            self.assertEqual(projected["scope"], held["scope"])
            self.assertEqual(authority.policy("canonical_target"), BASE)
        finally:
            authority.dispose()

    def test_every_receipt_participant_holds_its_capability(self):
        held = self.prepared()
        authority = Authority.open(self.store,
                                   expected_authority_uuid=self.uuid)
        try:
            for one in held["granted"]:
                with self.subTest(**one):
                    self.assertIn(
                        one["capability"],
                        authority.capabilities_of(one["participant"]) or [])
        finally:
            authority.dispose()

    def test_the_route_handlers_named_are_the_selections_own(self):
        chosen = self.resolved()
        held = self.prepared(chosen)
        self.assertEqual(held["route_handlers"]["impl"],
                         chosen["participants"]["implementation"])
        self.assertEqual(
            held["route_handlers"]["integration"],
            chosen["instance"]["integration_profile"]["integrator_participant"])

    def test_a_repeat_replays_the_same_act(self):
        """MEASURED, and it corrected a claim rather than confirming one.

        The helper's first draft said in its own docstring that a second run
        would refuse. It does not: `create_work` is journalled under an
        operation identity derived from the run, so the repeat replays and
        answers the same Work and scope. Both the helper and the operator
        document now say that, and this is what holds them to it.
        """
        first = self.prepared()
        again = self.prepared()
        self.assertEqual(again["work_id"], first["work_id"])
        self.assertEqual(again["scope"], first["scope"])
        self.assertEqual(again["canonical_target"], first["canonical_target"])


@unittest.skipUnless(VECTORS.exists(), "the composition's real operand")
class ThePreparedSelectionsAlsoCompose(
        TheGeneratedPacketDrivesOneImplementation):
    """Preparation and composition over ONE document, not two comparisons."""

    def selections(self):
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"],
            authority_store=self.authority_path,
            authority_uuid=self.config["authority_uuid"],
            integration_store=self.integration_store,
            job_store=os.path.join(self.root, f"{RUN_ID}-jobs.sqlite3"),
            control_store=os.path.join(self.root, f"{RUN_ID}-control.sqlite3"),
            integration_profile={"profile_kind": "git", "profile_version": 1,
                                 "integrator_participant": "baton.integrator",
                                 "instructions_digest": "sha256:" + "e" * 64},
            retention_policy_digest=self.config["retention_policy_digest"],
            runtime_path=self.written_runtime_root())
        chosen["participants"] = dict(
            chosen["participants"], work_id=self.work,
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
        chosen["manager_source"] = self.written_manager_source()
        chosen["code_boundary"] = chosen["manager_source"]
        return chosen

    def test_the_244216_selections_compose_the_bound_image(self):
        documents, places = self.generate()
        packet = json.loads(
            Path(places["PACKET.json"]).read_text(encoding="utf-8"))
        artifact = json.loads(
            (HERE / "IMAGE-ARTIFACT-244216.json").read_text(encoding="utf-8"))
        self.assertEqual(packet["worker_image"]["reference"],
                         artifact["reference"])
        self.assertEqual(packet["worker_image"]["config_digest"],
                         artifact["image_config_digest"])
        self.assertEqual(
            packet["worker_image"]["worker_files"]["opt/baton/claude_agent.py"],
            artifact["accepted_adapter"]["sha256"])
        self.assertEqual(packet["bounds"]["total_seconds"], 300)
        self.assertEqual(packet["bounds"]["cleanup_seconds"], 60)
        self.assertEqual(packet["bounds"]["turn_seconds"], 180)
        self.assertEqual(packet["submission"]["job_id"], "job-" + RUN_ID)
        del documents

    def test_the_same_document_passes_the_freshness_check(self):
        """One document, both gates -- which is the whole point of R1."""
        chosen = self.selections()
        # This case relocates the stores for isolation, so the marker it
        # validates is the relocated one; what matters is that the SAME
        # function answers for both packets without being edited.
        chosen["instance"] = dict(
            chosen["instance"],
            authority_store=f"/tmp/{RUN_ID}/db/authority.sqlite3",
            job_store=f"/tmp/{RUN_ID}/db/jobs.sqlite3",
            control_store=f"/tmp/{RUN_ID}/db/control.sqlite3",
            integration_store=f"/tmp/{RUN_ID}/db/integration.sqlite3")
        self.assertEqual(prepare_instance.fresh(chosen), RUN_ID)


class TheDocumentPointsAtTheHelperAndQualifiesItsDiagnoses(unittest.TestCase):
    """Owner reroute 244290: "Qualify outcome diagnoses using actual
    evidence" -- the document may not assert a cause it has not observed."""

    def setUp(self):
        self.said = DOCUMENT.read_text(encoding="utf-8")

    def test_it_references_the_parameterized_helper(self):
        self.assertIn("prepare_instance.py", self.said)
        self.assertIn("--selections", self.said)
        self.assertIn("--base", self.said)

    def test_it_does_not_reprint_the_hardcoded_block(self):
        self.assertNotIn('assert "single-implementation-243284" in store',
                         self.said)
        self.assertNotIn("single-implementation-243284/selections.json",
                         self.said)

    def test_a_no_progress_outcome_is_not_diagnosed_as_a_cause(self):
        """It used to say the CLI "did something a mask cannot govern". That
        is one hypothesis; the outcome names a state, not a cause."""
        block = self.said.split("## What each outcome means", 1)[1]
        self.assertIn("read", block.lower())
        for asserted in ("The CLI did something a mask cannot govern",
                         "Either would be a regression"):
            with self.subTest(phrase=asserted):
                self.assertNotIn(asserted, block)

    def test_the_inspection_limit_is_disclosed(self):
        """The reviewer could not read inside the image -- its container was
        denied Docker API access -- so the byte claims are the author's,
        corroborated at the metadata level. The page has to say so."""
        said = " ".join(self.said.split())
        self.assertIn("author evidence", said.lower())
        self.assertIn("denied Docker API access", said)
        self.assertIn("not independently re-read from inside the image", said)


class AConsumedIdentityIsRefusedHoweverItIsSpelled(unittest.TestCase):
    """Review 2026-09-23T03:42:19Z R2.

    The first version exempted a consumed root when its name EQUALLED
    `run_id`, so naming the run after a consumed instance let every one of its
    stores through -- the exemption defeated the check it was written into.
    """

    def under(self, root, run):
        chosen = delivered()
        chosen["run_id"] = run
        chosen["instance"] = dict(
            chosen["instance"],
            authority_store=f"/home/sl/baton-runs/{root}/db/authority.sqlite3",
            job_store=f"/home/sl/baton-runs/{root}/db/jobs.sqlite3",
            control_store=f"/home/sl/baton-runs/{root}/db/control.sqlite3",
            integration_store=f"/home/sl/baton-runs/{root}/db/int.sqlite3")
        return chosen

    def test_naming_the_run_after_a_consumed_instance_is_refused(self):
        """The exact hole: run_id == the consumed root."""
        for root in prepare_instance.CONSUMED:
            with self.subTest(root=root):
                with self.assertRaises(
                        prepare_instance.PreparationRefusal) as caught:
                    prepare_instance.fresh(self.under(root, root))
                self.assertIn("CONSUMED", str(caught.exception))

    def test_a_consumed_root_under_a_new_run_name_is_still_refused(self):
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"],
            job_store=f"/home/sl/baton-runs/managed-correction-236087/"
                      f"{RUN_ID}/jobs.sqlite3")
        with self.assertRaises(prepare_instance.PreparationRefusal) as caught:
            prepare_instance.fresh(chosen)
        self.assertIn("preserved evidence", str(caught.exception))

    def test_a_traversal_that_lands_in_a_consumed_root_is_refused(self):
        """Normalized locations: a raw substring test answers the wrong
        question for `/a/b/../<consumed>`."""
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"],
            control_store=f"/home/sl/baton-runs/{RUN_ID}/../"
                          f"single-implementation-239528/{RUN_ID}/c.sqlite3")
        with self.assertRaises(prepare_instance.PreparationRefusal) as caught:
            prepare_instance.fresh(chosen)
        self.assertIn("preserved evidence", str(caught.exception))

    def test_the_run_must_name_a_component_not_a_substring(self):
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"],
            job_store=f"/home/sl/baton-runs/{RUN_ID}-elsewhere/jobs.sqlite3")
        with self.assertRaises(prepare_instance.PreparationRefusal) as caught:
            prepare_instance.fresh(chosen)
        self.assertIn("does not name this run", str(caught.exception))

    def test_a_valid_new_instance_still_passes(self):
        """The check must not become one nothing can satisfy."""
        self.assertEqual(prepare_instance.fresh(delivered()), RUN_ID)


class TheDocumentedEntrypointRunsThroughComposition(
        TheGeneratedPacketDrivesOneImplementation):
    """ONE resolved document, the documented command, then composition.

    Owner reroute 244386: "Add a disposable supported-interface test executing
    the actual documented entrypoint through composition using the same
    resolved successor document." The earlier cases called `prepare` and
    `compose` from separate fixtures; this writes one selections file, runs
    `prepare_instance.py` AS THE PAGE PRINTS IT -- a child process with
    `PYTHONPATH` bound to the manager source -- and then composes the very
    same file.
    """

    def successor_work(self):
        """A Work this instance has NOT yet been given.

        The fixture's own Work already exists, and `create_work` refuses a
        name that exists under a different operation identity -- correctly:
        preparing a successor must not quietly adopt somebody else's Work.
        The name still has to carry this Authority's prefix, so it is derived
        from the fixture's rather than written as a literal.
        """
        return self.work.rsplit("-W", 1)[0] + "-W900"

    def instance_root(self):
        """A directory NAMED for the run, holding all four of its stores.

        The freshness check requires exactly that, and it is right to: a
        successor's stores are its own. The fixture's Authority and
        integration stores live under its temporary root rather than under a
        run directory, so they are COPIED here -- disposable files, opened
        with the same uuid, carrying the same Work and principals. Pointing
        the document at the originals would have the check refuse, which is
        the check working rather than a reason to weaken it.
        """
        place = Path(self.root) / RUN_ID
        place.mkdir(exist_ok=True)
        authority = place / "authority.sqlite3"
        if not authority.exists():
            shutil.copy2(self.authority_path, authority)
            integration = Path(self.integration_store)
            if integration.exists():
                shutil.copy2(integration, place / "integration.sqlite3")
        return place

    def resolved_document(self):
        """The delivered successor selections, fully resolved, written once."""
        root = self.instance_root()
        chosen = delivered()
        chosen["instance"] = dict(
            chosen["instance"],
            authority_store=str(root / "authority.sqlite3"),
            authority_uuid=self.config["authority_uuid"],
            integration_store=str(root / "integration.sqlite3"),
            job_store=str(root / "jobs.sqlite3"),
            control_store=str(root / "control.sqlite3"),
            integration_profile={"profile_kind": "git", "profile_version": 1,
                                 "integrator_participant": "baton.integrator",
                                 "instructions_digest": "sha256:" + "e" * 64},
            retention_policy_digest=self.config["retention_policy_digest"],
            runtime_path=self.written_runtime_root())
        chosen["participants"] = dict(
            chosen["participants"], work_id=self.successor_work(),
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
        chosen["manager_source"] = self.written_manager_source()
        chosen["code_boundary"] = chosen["manager_source"]
        place = Path(self.root) / "resolved-successor.json"
        place.write_text(json.dumps({"compose": chosen}, indent=2,
                                    sort_keys=True), encoding="utf-8")
        return place, chosen

    def selections(self):
        return self.resolved_document()[1]

    def bound_source(self):
        """Where `baton_v12` actually is -- what `$BOUND` names in production.

        NOT `chosen["manager_source"]`: that is the fixture's deliberately
        tiny `boundpkg` tree, so binding it would answer ModuleNotFoundError
        just as an unbound shell does and would prove nothing about the step.
        The successor packet binds a manager-source snapshot whose root holds
        `baton_v12`; the standing equivalent is the root this process
        imported it from.
        """
        return str(Path(baton_v12.__file__).resolve().parent.parent)

    def documented_preparation(self, place, chosen, *, bind=True):
        """The command exactly as the page prints it."""
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        if bind:
            environment["PYTHONPATH"] = self.bound_source()
        return subprocess.run(
            [sys.executable, "-B", str(HERE / "prepare_instance.py"),
             "--selections", str(place), "--base", self.base],
            capture_output=True, text=True, timeout=300, env=environment,
            cwd=os.sep)

    def test_the_documented_command_prepares_then_composes(self):
        place, chosen = self.resolved_document()
        answer = self.documented_preparation(place, chosen)
        self.assertEqual(answer.returncode, 0,
                         f"stdout={answer.stdout}\nstderr={answer.stderr}")
        prepared = json.loads(answer.stdout)
        self.assertEqual(prepared["work_id"], self.successor_work())
        self.assertEqual(prepared["canonical_target"], self.base)
        self.assertEqual(prepared["run_id"], RUN_ID)

        # THE SAME DOCUMENT, COMPOSED. Not a second fixture: this is the file
        # the preparation just read.
        documents, places = self.generate()
        packet = json.loads(
            Path(places["PACKET.json"]).read_text(encoding="utf-8"))
        self.assertEqual(packet["bounds"], baseline_bindings.BOUNDS)
        self.assertEqual(packet["submission"]["job_id"], "job-" + RUN_ID)
        artifact = json.loads(
            (HERE / "IMAGE-ARTIFACT-244216.json").read_text(encoding="utf-8"))
        self.assertEqual(packet["worker_image"]["config_digest"],
                         artifact["image_config_digest"])
        self.assertEqual(documents["task.json"]["declared_base"], self.base)

        # AND THE AUTHORITY REALLY CARRIES WHAT THE COMMAND SAID IT DID.
        # The one the document named, which is the copy the command opened.
        authority = Authority.open(
            chosen["instance"]["authority_store"],
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            self.assertEqual(authority.policy("canonical_target"), self.base)
            self.assertEqual(
                authority.project_work(self.successor_work())["scope"],
                prepared["scope"])
        finally:
            authority.dispose()

    def test_the_command_without_the_bound_source_fails_as_reported(self):
        """R1's reproduction, kept: the page used to print it unbound."""
        place, chosen = self.resolved_document()
        answer = self.documented_preparation(place, chosen, bind=False)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("No module named 'baton_v12'", answer.stderr)

    def test_the_page_binds_the_import_path_for_this_step(self):
        said = DOCUMENT.read_text(encoding="utf-8")
        block = said.split("## Step 5a", 1)[1].split("```sh", 1)[1]
        block = block.split("```", 1)[0]
        self.assertIn('PYTHONPATH="$BOUND"', block)
        self.assertIn("prepare_instance.py", block)
        self.assertIn('--selections "$SEL"', block)
        self.assertIn('--base "$BASE"', block)


def load_tests(loader, tests, pattern):
    """THIS FILE'S OWN CHECKS, and not the ones it inherits.

    `ThePreparedSelectionsAlsoCompose` extends the generated-packet case to
    reuse its composition, which also inherits every test method that class
    and its own bases define. Running those again here would re-attribute
    other files' measured evidence to this one -- and several of them are
    about a submission this case deliberately replaces.
    """
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (TheFreshnessCheckIsDerivedNotHardcoded,
                 AConsumedIdentityIsRefusedHoweverItIsSpelled,
                 TheDocumentedEntrypointRunsThroughComposition,
                 ThePreparationActsRunAgainstADisposableAuthority,
                 ThePreparedSelectionsAlsoCompose,
                 TheDocumentPointsAtTheHelperAndQualifiesItsDiagnoses):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite
