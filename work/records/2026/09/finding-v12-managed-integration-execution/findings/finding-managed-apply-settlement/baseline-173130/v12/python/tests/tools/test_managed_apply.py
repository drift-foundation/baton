"""Selected W170385 managed apply and settlement evidence.

Git mutations in these cases are confined to disposable fixture repositories.
The local receipt cases are component evidence, not complete managed execution.
"""
import os
import tempfile
import unittest
import json
from pathlib import Path

from baton_v12.integration.git_profile import GitIntegrationProfile, IntegrationProfileRefusal
from tools.stage_execution import _git_run
from tests.tools.test_managed_preparation import RealLine


class ThePreparationHandoffNeedsItsGitObjects(unittest.TestCase):
    def test_the_current_output_omits_the_derived_commit_and_executable_mode(self):
        """Observed scope blocker, not a passing managed-apply acceptance case."""
        from tests.tools.test_managed_preparation import OnePreparationRunsThroughTheOrdinaryWorker

        class ExecutableCandidate(OnePreparationRunsThroughTheOrdinaryWorker):
            def history(self, conflicting=False):
                revisions = super().history(conflicting)
                self.line.run(["checkout", "--quiet", "-b", "executable-candidate", revisions["candidate"]])
                self.line.write("tool.sh", "#!/bin/sh\nexit 0\n")
                os.chmod(os.path.join(self.line.place, "tool.sh"), 0o755)
                revisions["candidate"] = self.line.commit("candidate includes an executable")
                return revisions

        case = ExecutableCandidate("run")
        self.addCleanup(case.doCleanups)
        case.setUp()
        answer = case.agent().work(case.launch(), case.declared())
        self.assertEqual(answer["disposition"], "completed")
        report = case.report()
        derived = report["derived_candidate"]
        objects = os.path.join(case.scratch, "objects")
        tree_entry = _git_run(["git", "-C", objects, "ls-tree", derived["revision"], "--", "tool.sh"])
        self.assertEqual(tree_entry["returncode"], 0)
        self.assertTrue(tree_entry["stdout"].startswith("100755 blob "))
        emitted = Path(case.output, "candidate", "tool.sh")
        self.assertEqual(emitted.read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual(emitted.stat().st_mode & 0o111, 0)
        self.assertFalse(any(path.name in (".git", "objects.bundle") for path in Path(case.output).rglob("*")))
        measured = next(one for one in report["states"]["combined"]["content"]["entries"] if one["path"] == "tool.sh")
        self.assertEqual(set(measured), {"path", "content_digest", "bytes"})
        portable = os.path.join(case.root.name, "input-objects-only")
        self.assertEqual(_git_run(["git", "init", "--quiet", "--bare", portable])["returncode"], 0)
        fetched = _git_run(["git", "-C", portable, "fetch", "--quiet", os.path.join(case.input, "source", "objects.bundle"), "refs/*:refs/input/*"])
        self.assertEqual(fetched["returncode"], 0)
        missing = _git_run(["git", "-C", portable, "cat-file", "-e", derived["revision"] + "^{commit}"])
        self.assertNotEqual(missing["returncode"], 0)
        print(json.dumps({"proof": "preparation-handoff-scope-blocker", "derived_revision": derived["revision"],
                          "derived_tree": derived["tree"], "git_mode": "100755", "output_executable": False,
                          "derived_commit_in_input_bundle": False, "output_paths": sorted(str(path.relative_to(case.output)) for path in Path(case.output).rglob("*") if path.is_file())}, sort_keys=True))


class TheTargetEffectAndReceiptAreOneTransaction(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="v12-managed-apply-")
        self.addCleanup(self.home.cleanup)
        self.line = RealLine(os.path.join(self.home.name, "target"))
        self.line.write("feature.py", "VALUE = 1\n")
        self.old = self.line.commit("base")
        self.line.write("feature.py", "VALUE = 2\n")
        self.new = self.line.commit("approved")
        self.reference = "refs/baton/targets/local"
        self.line.run(["update-ref", self.reference, self.old])
        self.profile = GitIntegrationProfile(_git_run)
        self.receipt = {"publication": "publication-a", "old": self.old, "new": self.new}
        self.checks = []

    def publish(self, **changed):
        operands = dict(reference=self.reference, imported=self.new, reviewed=self.old,
                        publication_id="publication-a", receipt=self.receipt,
                        before_commit=lambda: self.checks.append("grant"))
        operands.update(changed)
        return self.profile.publish_with_receipt(self.line.place, **operands)

    def test_target_and_exact_receipt_survive_a_new_owner(self):
        before = self.profile.publication_receipt(self.line.place, publication_id="publication-a")
        self.assertIsNone(before)
        receipt = self.publish()
        self.assertEqual(self.checks, ["grant"])
        self.assertEqual(self.line.run(["show", self.reference + ":feature.py"]), "VALUE = 2")
        reopened = GitIntegrationProfile(_git_run)
        self.assertEqual(reopened.publication_receipt(self.line.place, publication_id="publication-a"), receipt)
        self.assertEqual(receipt["document"], self.receipt)

    def test_stale_target_cas_creates_no_receipt(self):
        self.line.run(["update-ref", self.reference, self.new, self.old])
        with self.assertRaises(IntegrationProfileRefusal):
            self.publish()
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.new)
        self.assertIsNone(self.profile.publication_receipt(self.line.place, publication_id="publication-a"))


    def test_receipt_collision_does_not_advance_the_target(self):
        reference = self.profile.publication_reference("publication-a")
        self.line.run(["update-ref", reference, self.old])
        with self.assertRaises(IntegrationProfileRefusal):
            self.publish()
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.old)
        self.assertEqual(self.line.run(["rev-parse", reference]), self.old)

    def test_lost_transaction_reply_recovers_without_another_effect(self):
        calls = []

        def lost(argv, **options):
            answer = _git_run(argv, **options)
            if "update-ref" in argv and "--stdin" in argv:
                calls.append(tuple(argv))
                raise RuntimeError("reply lost after transaction")
            return answer

        self.profile = GitIntegrationProfile(lost)
        with self.assertRaisesRegex(RuntimeError, "reply lost"):
            self.publish()
        recovered = GitIntegrationProfile(_git_run).publication_receipt(self.line.place, publication_id="publication-a")
        self.assertEqual(recovered["document"], self.receipt)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.new)

    def test_grant_is_checked_after_receipt_object_work_before_transaction(self):
        seen = []

        def run(argv, **options):
            seen.append(tuple(argv))
            return _git_run(argv, **options)

        def revoked():
            self.assertTrue(any("hash-object" in argv for argv in seen))
            self.assertFalse(any("update-ref" in argv for argv in seen))
            raise RuntimeError("grant revoked")

        self.profile = GitIntegrationProfile(run)
        with self.assertRaisesRegex(RuntimeError, "grant revoked"):
            self.publish(before_commit=revoked)
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.old)
        self.assertIsNone(self.profile.publication_receipt(self.line.place, publication_id="publication-a"))


class TheLocalReceiptOwnerComposesWithPlacement(unittest.TestCase):
    """Real target receipt; surrounding authorization/exclusion remain fixtures."""

    def setUp(self):
        from tests.tools.test_managed_integration import PlacementCase
        self.case = PlacementCase("run")
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.case.custody()
        self.case.stopped()
        self.configure(_git_run)

    def configure(self, runner):
        from integration_placement import LocalGitTargetOwner
        from tests.tools.test_managed_integration import ORCHESTRATION
        case = self.case
        case.profile = GitIntegrationProfile(runner)
        case.target_owner = LocalGitTargetOwner(
            coordinator=case.coordinator, manager=case.store, profile=case.profile,
            execution_owner=case.execution_owner, authorization=case.authorization,
            repository=case.repository, reference=case.reference, managed_result_id=ORCHESTRATION)

    def test_real_receipt_publication_and_historical_replay(self):
        first = self.case.publish()
        self.assertEqual(first["outcome"], "published")
        self.assertEqual(self.case.standing(), self.case.candidate)
        self.configure(_git_run)
        replayed = self.case.publish()
        self.assertEqual(replayed["outcome"], "replayed")
        self.assertEqual(replayed["imported_revision"], first["imported_revision"])

    def test_lost_reply_is_settled_from_the_real_receipt(self):
        calls = []

        def lost(argv, **options):
            answer = _git_run(argv, **options)
            if "update-ref" in argv and "--stdin" in argv:
                calls.append(tuple(argv))
                raise RuntimeError("target reply lost")
            return answer

        self.configure(lost)
        with self.assertRaisesRegex(RuntimeError, "target reply lost"):
            self.case.publish()
        self.configure(_git_run)
        self.assertEqual(self.case.publish()["outcome"], "resumed")
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.case.standing(), self.case.candidate)

