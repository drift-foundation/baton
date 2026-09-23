"""The successor manager-source snapshot, and the replay driven against it.

Review 2026-09-22T23:53:34Z R1: `OPERATOR-FAILURE-242687.md` bound the W236087
snapshot, which holds the PRE-CORRECTION `review_driver.py` and
`stage_execution.py`, so "executing the documented command imports the old
unconditional publication and context-held ending logic". Owner reroute 242903:
"prepare a separate successor manager-source snapshot containing accepted
bytes... Exercise the composed expired-credential replay against that exact
snapshot."

This file is that exercise, and it has three parts because the claim has three
halves that can each be wrong on their own:

  1. THE SNAPSHOT CARRIES THE ACCEPTED BYTES, and the preserved one still
     carries the superseded ones. Both are asserted against the files on disk,
     not against the manifest that describes them -- a manifest agreeing with
     itself proves nothing.
  2. THE SNAPSHOT IS IMPORTABLE AS THE COMMAND IMPORTS IT. The composer runs
     as a CHILD PROCESS with `PYTHONPATH` set to the snapshot and nothing
     else, exactly as `OPERATOR-FAILURE-242687.md` prints it, and the child
     reports which file its own `review_driver` resolved from. A snapshot that
     hashes correctly but cannot be imported flat would still fail the
     operator.
  3. THE REPLAY SETTLES AGAINST A PACKET BOUND TO IT. The expired-credential
     bytes are driven through a packet whose `manager_source` and
     `code_boundary` are the snapshot, at the 120/30 bounds the owner
     selected.

WHAT PART 3 DOES NOT CLAIM, stated because it is the honest limit. This process
imports `baton_v12` and `tools` from the CHECKOUT, so the code it executes is
the checkout's -- which is byte-identical to the snapshot for the two files
that matter, and part 1 is what establishes that. `verify_imported_sources`
would refuse a packet bound to the snapshot in this process for exactly that
reason, correctly, and part 2 is the half that exercises the snapshot's own
bytes in their own interpreter.

No store belonging to any deployed instance is opened, no container starts, no
credential is read and no live provider is called.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests.job_manager import fixtures

import baseline
from test_baseline_bindings import VECTORS
from test_failure_path import ExpiredCredentialCase

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MANAGER-SOURCE-242687.json"
SNAPSHOT = Path("/home/sl/baton-runs/single-implementation-242687"
                "/manager-source")
PRESERVED = Path("/home/sl/baton-runs/managed-correction-236087"
                 "/manager-source")

ACCEPTED = {
    "baton_v12/job_manager/review_driver.py":
        "9a8a4a8193ff7b1c709c184dee3ba43a1b1e16e60891dcf31277279d2c220ae4",
    "tools/stage_execution.py":
        "ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896",
}
SUPERSEDED = {
    "baton_v12/job_manager/review_driver.py":
        "b5b22535ef105f786aa74f61ff894614a1e91bb8e2739f1051151fb893ebe10c",
    "tools/stage_execution.py":
        "33c780916a115890767bb79cc3a2dcedc6ec588fb1da08e95490cd7897cd6e81",
}
# The bounds owner reroute 242903 selected for the failure path.
FAILURE_BOUNDS = {"turn_seconds": 180, "total_seconds": 120,
                  "cleanup_seconds": 30, "implementer_invocations": 1,
                  "retry": False}


def digest_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(SNAPSHOT.is_dir(),
                     "the successor snapshot is built by snapshot_242687.py")
class TheSuccessorSnapshotCarriesTheAcceptedBytes(unittest.TestCase):
    """Part one. Asserted against the files, not against the manifest."""

    def test_the_two_corrected_modules_are_the_accepted_ones(self):
        for name, expected in sorted(ACCEPTED.items()):
            with self.subTest(module=name):
                self.assertEqual(digest_of(SNAPSHOT / name), expected)

    def test_the_preserved_snapshot_still_holds_the_superseded_bytes(self):
        """R1's remedy is a SECOND snapshot, not an overwrite. W236087's own
        packet is bound to these bytes."""
        for name, expected in sorted(SUPERSEDED.items()):
            with self.subTest(module=name):
                self.assertEqual(digest_of(PRESERVED / name), expected)

    def test_the_two_snapshots_really_differ_at_those_modules(self):
        """The check that makes the other two mean something: if the accepted
        and superseded digests were equal, both would pass while proving
        nothing about the correction being present."""
        for name in sorted(ACCEPTED):
            with self.subTest(module=name):
                self.assertNotEqual(ACCEPTED[name], SUPERSEDED[name])
                self.assertNotEqual(digest_of(SNAPSHOT / name),
                                    digest_of(PRESERVED / name))

    def test_the_layout_is_flat_so_one_import_path_is_enough(self):
        self.assertTrue((SNAPSHOT / "baton_v12" / "__init__.py").is_file())
        self.assertTrue((SNAPSHOT / "tools" / "stage_execution.py").is_file())

    def test_the_manifest_describes_the_snapshot_on_disk(self):
        held = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(held["path"], str(SNAPSHOT))
        self.assertEqual(held["accepted_product_bytes"], ACCEPTED)
        self.assertEqual(held["supersedes"]["files"], SUPERSEDED)
        self.assertIs(held["supersedes"]["preserved"], True)
        self.assertEqual(held["file_count"], len(held["files"]))
        for name, expected in sorted(held["files"].items()):
            with self.subTest(file=name):
                self.assertEqual(digest_of(SNAPSHOT / name), expected)


@unittest.skipUnless(SNAPSHOT.is_dir(),
                     "the successor snapshot is built by snapshot_242687.py")
class TheSnapshotIsImportableAsTheCommandImportsIt(unittest.TestCase):
    """Part two. A child process, with the documented PYTHONPATH and nothing
    inherited."""

    def child(self, script, *, bind=SNAPSHOT):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        if bind is not None:
            environment["PYTHONPATH"] = str(bind)
        return subprocess.run([sys.executable, "-c", script],
                              capture_output=True, text=True, timeout=300,
                              env=environment, cwd=os.sep)

    def test_a_child_bound_to_it_imports_the_corrected_driver(self):
        """The whole of R1 in one check: what does the command's interpreter
        actually load, and does that file carry the correction?"""
        answer = self.child(
            "import json, hashlib\n"
            "from baton_v12.job_manager import review_driver\n"
            "from tools import stage_execution\n"
            "print(json.dumps({\n"
            "  'driver': review_driver.__file__,\n"
            "  'driver_sha': hashlib.sha256(open(review_driver.__file__,'rb')"
            ".read()).hexdigest(),\n"
            "  'stage_sha': hashlib.sha256(open(stage_execution.__file__,'rb')"
            ".read()).hexdigest(),\n"
            "  'publishable': list(review_driver.PUBLISHABLE)}))\n")
        self.assertEqual(answer.returncode, 0, answer.stderr)
        held = json.loads(answer.stdout)
        self.assertTrue(held["driver"].startswith(str(SNAPSHOT)), held)
        self.assertEqual(held["driver_sha"],
                         ACCEPTED["baton_v12/job_manager/review_driver.py"])
        self.assertEqual(held["stage_sha"],
                         ACCEPTED["tools/stage_execution.py"])
        # AND THE CORRECTION IS PRESENT BY NAME, not only by digest.
        self.assertEqual(held["publishable"], ["completed"])

    def test_the_preserved_snapshot_does_not_carry_the_correction(self):
        """The counterexample the reviewer reproduced, kept as a regression:
        the command's PREVIOUS binding imports a driver with no publication
        guard at all."""
        answer = self.child(
            "from baton_v12.job_manager import review_driver\n"
            "print(hasattr(review_driver, 'PUBLISHABLE'))\n",
            bind=PRESERVED)
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertEqual(answer.stdout.strip(), "False")

    def test_without_the_binding_the_child_cannot_import_at_all(self):
        answer = self.child(
            "from baton_v12.job_manager import review_driver\n", bind=None)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("No module named 'baton_v12'", answer.stderr)


@unittest.skipUnless(VECTORS.exists() and SNAPSHOT.is_dir(),
                     "the composition's real operands")
class TheReplaySettlesAgainstAPacketBoundToTheSnapshot(ExpiredCredentialCase):
    """Part three. The expired-credential bytes, at the selected bounds,
    through a packet whose bound source IS the successor snapshot."""

    def bound_packet(self):
        """This case's packet, rebound to the snapshot at the owner's bounds.

        `manager_source` is manifested file by file from the snapshot, exactly
        as `baseline_bindings.compose` would, so `held_packet` pins the real
        tree rather than a description of it.
        """
        held = json.loads(MANIFEST.read_text(encoding="utf-8"))
        packet = dict(
            self.packet,
            manager_source={"path": str(SNAPSHOT),
                            "packages": list(held["packages"]),
                            "file_count": held["file_count"],
                            "files": dict(held["files"])},
            code_boundary=str(SNAPSHOT),
            bounds=dict(FAILURE_BOUNDS),
            outcome_path=str(self.packet_root / "successor-outcome.json"))
        place = self.packet_root / "SUCCESSOR-PACKET.json"
        place.write_text(json.dumps(packet, sort_keys=True, indent=2),
                         encoding="utf-8")
        self.successor_packet_path = str(place)
        return packet

    def test_the_packet_bound_to_the_snapshot_is_held_whole(self):
        packet = self.bound_packet()
        held = baseline.held_packet(self.successor_packet_path)
        self.assertEqual(held["manager_source"]["path"], str(SNAPSHOT))
        self.assertEqual(held["bounds"]["total_seconds"], 120)
        self.assertEqual(held["bounds"]["cleanup_seconds"], 30)
        self.assertEqual(held["bounds"]["implementer_invocations"], 1)
        del packet

    def test_the_expired_credential_replay_fails_promptly_and_cleans_up(self):
        outcome, _job, _control, _composed = self.supervised_failure(
            manager_source=self.bound_packet()["manager_source"],
            code_boundary=str(SNAPSHOT), bounds=dict(FAILURE_BOUNDS),
            outcome_path=str(self.packet_root / "successor-outcome.json"))
        # PROMPT, and well inside the 120 the owner selected.
        self.assertEqual(outcome["stopped"], "exceptional")
        self.assertLess(outcome["served_seconds"], 30)
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "exceptional"})
        # STOPPED, AND POSITIVELY CLEANED UP.
        self.assertEqual(outcome["outstanding_cleanup"], [])
        for attempt, cleaned in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(cleaned["cleanup"], baseline.POSITIVE_CLEANUP)
                self.assertEqual(cleaned["state"], "absent")
        # NO PROPOSAL, NO FALSE SUCCESS, AND AN ACTIONABLE REPORT.
        self.assertEqual(outcome["state"], "held")
        self.assertEqual(outcome["workload"]["proposals"], [])
        self.assertEqual(
            [one["disposition"]
             for one in outcome["workload"]["dispositions"]], ["unable"])
        self.assertTrue(
            any("ended 'unable'" in one
                for one in outcome["workload"]["shortfalls"]),
            outcome["workload"]["shortfalls"])

    def test_the_run_is_bounded_by_the_selected_total(self):
        """A failure path that still burned the old 900 would be the defect
        wearing a smaller number. The bound is 120 and the run ends on the
        STAGE, not on the bound."""
        outcome, _job, _control, _composed = self.supervised_failure(
            manager_source=self.bound_packet()["manager_source"],
            code_boundary=str(SNAPSHOT), bounds=dict(FAILURE_BOUNDS),
            outcome_path=str(self.packet_root / "successor-outcome.json"))
        self.assertNotEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertLess(outcome["served_seconds"],
                        FAILURE_BOUNDS["total_seconds"])

    def test_the_provider_was_called_once_and_never_retried(self):
        self.supervised_failure(
            manager_source=self.bound_packet()["manager_source"],
            code_boundary=str(SNAPSHOT), bounds=dict(FAILURE_BOUNDS),
            outcome_path=str(self.packet_root / "successor-outcome.json"))
        self.assertEqual(
            len(self.calls.read_text().splitlines()), 1)

    def test_the_selections_name_this_snapshot_and_these_bounds(self):
        """The composed input an operator actually edits, checked against the
        packet this case proved. R2: it used to be prose."""
        selections = json.loads(
            (HERE / "SELECTIONS-FAILURE-242687.json").read_text(
                encoding="utf-8"))["compose"]
        self.assertEqual(selections["manager_source"], str(SNAPSHOT))
        self.assertEqual(selections["code_boundary"], str(SNAPSHOT))
        self.assertEqual(selections["bounds"], FAILURE_BOUNDS)
        self.assertEqual(selections["run_id"], "single-implementation-242687")
        # AND ITS STORES ARE NOT THE FIRST RUN'S, which hold unfinished work.
        for member in ("authority_store", "job_store", "control_store",
                       "integration_store"):
            with self.subTest(store=member):
                self.assertNotIn("single-implementation-239528",
                                 selections["instance"][member])
                self.assertIn("single-implementation-242687",
                              selections["instance"][member])


class ASuccessorNeverReplacesItsPredecessorsEvidence(unittest.TestCase):
    """Review 2026-09-23T00:50:59Z R2, over disposable trees only.

    `--rebuild-into` used to change the destination and still write the FIXED
    `MANAGER-SOURCE-242687.json`, so building a successor replaced the
    accepted predecessor's manifest and the default `--verify` then checked
    the old tree against the new manifest. Nothing here touches the bound
    snapshot or its manifest: every path below is a temporary directory.
    """

    def setUp(self):
        import shutil
        import tempfile
        self.root = Path(tempfile.mkdtemp(prefix="w239528-successor-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def builder(self, *arguments):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [sys.executable, str(HERE / "snapshot_242687.py"), *arguments],
            capture_output=True, text=True, timeout=600, env=environment)

    def test_a_successor_must_state_the_claim_that_created_it(self):
        """Review 2026-09-23T01:02:06Z R2 remaining. The CLI used to call the
        builder with the ORIGINAL's claim for every build, so a successor made
        under a different assignment still recorded 242906 -- a manifest
        naming the wrong episode reads as evidence somebody produced under
        review that nobody did."""
        place = self.root / "w239528-claimless-probe" / "manager-source"
        answer = self.builder("--rebuild-into", str(place))
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("must state the claim that created it",
                      answer.stdout + answer.stderr)
        self.assertFalse(place.exists(), "it refused before copying anything")

    def test_a_successor_records_its_own_creation_and_the_shared_recipe(self):
        place = self.root / "w239528-provenance-probe" / "manager-source"
        manifest = HERE / "MANAGER-SOURCE-w239528-provenance-probe.json"
        self.addCleanup(manifest.unlink, True)
        self.assertEqual(
            self.builder("--rebuild-into", str(place),
                         "--claim", "243990").returncode, 0)
        held = json.loads(manifest.read_text(encoding="utf-8"))
        # ITS OWN CREATION...
        self.assertEqual(held["claim"], 243990)
        self.assertEqual(held["created_by_claim"], 243990)
        # ...AND THE RECIPE IT SHARES, named as a different thing.
        self.assertEqual(held["recipe"]["original_claim"], 242906)
        self.assertEqual(held["recipe"]["original_path"], str(SNAPSHOT))

    def test_the_original_manifest_still_records_its_own_claim(self):
        """Not rewritten. It is history."""
        held = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(held["claim"], 242906)

    def test_the_manifest_follows_the_snapshot(self):
        import snapshot_242687 as builder

        self.assertEqual(builder.manifest_for(builder.ORIGINAL).name,
                         "MANAGER-SOURCE-242687.json")
        self.assertEqual(
            builder.manifest_for(self.root / "elsewhere" / "manager-source")
            .name, "MANAGER-SOURCE-elsewhere.json")

    def test_an_existing_tree_is_refused(self):
        answer = self.builder()
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("never replaces a snapshot", answer.stdout + answer.stderr)

    def test_the_bound_manifest_is_not_replaced_by_a_successor(self):
        """The defect itself: the accepted manifest must be byte-identical
        after a successor is built."""
        bound = HERE / "MANAGER-SOURCE-242687.json"
        before = bound.read_bytes()
        place = self.root / "w239528-successor-probe" / "manager-source"
        answer = self.builder("--rebuild-into", str(place),
                              "--claim", "243990")
        self.addCleanup(
            lambda: (HERE / "MANAGER-SOURCE-w239528-successor-probe.json")
            .unlink(missing_ok=True))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertEqual(bound.read_bytes(), before,
                         "the successor replaced its predecessor's manifest")
        # AND THE SUCCESSOR HAS ITS OWN, naming its own path.
        successor = HERE / "MANAGER-SOURCE-w239528-successor-probe.json"
        self.assertTrue(successor.exists())
        self.assertEqual(
            json.loads(successor.read_text(encoding="utf-8"))["path"],
            str(place))

    def test_verify_uses_the_selected_pair(self):
        place = self.root / "w239528-verify-probe" / "manager-source"
        self.addCleanup(
            lambda: (HERE / "MANAGER-SOURCE-w239528-verify-probe.json")
            .unlink(missing_ok=True))
        self.assertEqual(
            self.builder("--rebuild-into", str(place),
                         "--claim", "243990").returncode, 0)
        # The successor verifies against ITS manifest...
        answer = self.builder("--verify", "--rebuild-into", str(place))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertIn(str(place), answer.stdout)
        # ...and the predecessor still verifies against ITS OWN.
        answer = self.builder("--verify")
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertIn(str(SNAPSHOT), answer.stdout)

    def test_an_existing_manifest_is_refused_even_for_a_new_tree(self):
        place = self.root / "w239528-clash-probe" / "manager-source"
        self.addCleanup(
            lambda: (HERE / "MANAGER-SOURCE-w239528-clash-probe.json")
            .unlink(missing_ok=True))
        self.assertEqual(
            self.builder("--rebuild-into", str(place),
                         "--claim", "243990").returncode, 0)
        import shutil
        shutil.rmtree(place)
        answer = self.builder("--rebuild-into", str(place),
                              "--claim", "243990")
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("never replaces a manifest",
                      answer.stdout + answer.stderr)


def load_tests(loader, tests, pattern):
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (TheSuccessorSnapshotCarriesTheAcceptedBytes,
                 ASuccessorNeverReplacesItsPredecessorsEvidence,
                 TheSnapshotIsImportableAsTheCommandImportsIt,
                 TheReplaySettlesAgainstAPacketBoundToTheSnapshot):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite


del fixtures
