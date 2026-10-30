"""W384870 review R2 — the content-bound source identity, over a disposable repository.

The property under test is the one the review showed missing: two candidates
with IDENTICAL `git status` text and different bytes must have different
identities, untracked files must count, ignored files must not, and the
boundary must be stated.

The R2 remainder: inputs OUTSIDE the scope that the run consumes are declared
and hashed whether or not git considers them changed, an absent declared input
refuses, and the real tree's declared inputs (`tools.parallel_test`) all exist.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import source_identity  # noqa: E402
from tools.parallel_test import SUPERVISED_MODULES, consumed_inputs  # noqa: E402

REPOSITORY = pathlib.Path(__file__).resolve().parents[4]


class DisposableRepository(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="v12-source-identity-")
        self.addCleanup(self.home.cleanup)
        self.repo = self.home.name
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@x", "HOME": self.repo}
        self.env = env
        self.git("init", "-q")
        os.makedirs(os.path.join(self.repo, "scope", "build"))
        self.write("scope/tracked.py", "one\n")
        self.write("records/gate/engine-gate.py", "supervisor\n")
        self.write("records/context/worker/agent.py", "captured\n")
        self.write(".gitignore", "/scope/build/\n__pycache__/\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")

    def git(self, *argv):
        subprocess.run(["git", "-C", self.repo, *argv], check=True, capture_output=True, env=self.env)

    def write(self, relative, text):
        path = os.path.join(self.repo, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def status_text(self):
        return subprocess.run(["git", "-C", self.repo, "status", "--porcelain"], check=True,
                              capture_output=True, env=self.env).stdout

    def identity(self, *inputs):
        return source_identity.identity(self.repo, ["scope"], inputs)

    def cli(self, *argv):
        return subprocess.run([sys.executable, "-m", "tools.source_identity", "--repo", self.repo, *argv, "scope"],
                              capture_output=True, text=True, cwd=str(pathlib.Path(__file__).resolve().parents[2]))

    def test_a_clean_tree_is_head_alone(self):
        found = self.identity()
        self.assertEqual(found["changed"], [])
        self.assertEqual(len(found["head"]), 40)
        self.assertIn("gitignored paths excluded", found["boundary"])

    def test_same_status_different_bytes_is_a_different_identity(self):
        self.write("scope/tracked.py", "candidate A\n")
        first, status_first = self.identity(), self.status_text()
        self.write("scope/tracked.py", "candidate B\n")
        second, status_second = self.identity(), self.status_text()
        self.assertEqual(status_first, status_second, "the status text must not have changed")
        self.assertNotEqual(first["content_digest"], second["content_digest"])
        self.assertEqual([one["path"] for one in second["changed"]], ["scope/tracked.py"])
        self.assertEqual(second["changed"][0]["status"], "M")

    def test_untracked_counts_and_ignored_does_not(self):
        self.write("scope/new_untracked.py", "fresh\n")
        self.write("scope/build/base_library.zip", "generated\n")
        found = self.identity()
        self.assertEqual([(one["status"], one["path"]) for one in found["changed"]],
                         [("??", "scope/new_untracked.py")])
        self.write("scope/new_untracked.py", "fresh but different\n")
        self.assertNotEqual(found["content_digest"], self.identity()["content_digest"])

    def test_outside_the_scope_is_outside_the_identity(self):
        self.write("elsewhere/evidence.log", "a run's own output\n")
        self.assertEqual(self.identity()["changed"], [])

    def test_a_deleted_file_is_recorded_as_absent(self):
        os.remove(os.path.join(self.repo, "scope", "tracked.py"))
        found = self.identity()
        self.assertEqual(found["changed"], [{"status": "D", "path": "scope/tracked.py", "sha256": "absent"}])

    def test_the_command_line_prints_the_same_document(self):
        self.write("scope/tracked.py", "cli\n")
        answer = self.cli()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertEqual(json.loads(answer.stdout)["content_digest"], self.identity()["content_digest"])

    # -- declared consumed inputs outside the scope (R2 remainder) --

    def test_a_declared_input_is_identified_although_git_sees_no_change(self):
        found = self.identity("records/gate/engine-gate.py")
        self.assertEqual(found["changed"], [], "nothing under the scope changed")
        self.assertEqual(found["consumed"], [{"input": "records/gate/engine-gate.py", "git": "tracked",
                                              "path": "records/gate/engine-gate.py",
                                              "sha256": source_identity.digest_file(os.path.join(self.repo, "records/gate/engine-gate.py"))}])
        self.assertNotEqual(found["content_digest"], self.identity()["content_digest"])
        self.assertIn("an absent declared input refuses", found["boundary"])

    def test_editing_a_declared_input_outside_the_scope_changes_the_identity(self):
        before = self.identity("records/gate/engine-gate.py")
        self.write("records/gate/engine-gate.py", "an edited supervisor\n")
        after = self.identity("records/gate/engine-gate.py")
        self.assertEqual(before["changed"], after["changed"], "the scope is untouched either way")
        self.assertNotEqual(before["content_digest"], after["content_digest"])
        self.assertEqual(self.identity()["changed"], [], "without the declaration the edit is invisible: that was the defect")

    def test_a_declared_directory_lists_untracked_files_and_not_ignored_ones(self):
        self.write("records/context/worker/fresh.py", "untracked\n")
        self.write("records/context/worker/__pycache__/agent.cpython-313.pyc", "generated\n")
        found = self.identity("records/context/worker")
        self.assertEqual([(one["git"], one["path"]) for one in found["consumed"]],
                         [("tracked", "records/context/worker/agent.py"), ("untracked", "records/context/worker/fresh.py")])
        self.write("records/context/worker/fresh.py", "untracked, edited\n")
        self.assertNotEqual(found["content_digest"], self.identity("records/context/worker")["content_digest"])

    def test_an_absent_declared_input_refuses(self):
        with self.assertRaises(source_identity.MissingInput) as caught:
            self.identity("records/gate/engine-gate.py", "records/missing/vectors.json")
        self.assertIn("records/missing/vectors.json", str(caught.exception))
        answer = self.cli("--input", "records/missing/vectors.json")
        self.assertEqual(answer.returncode, 2)
        self.assertEqual(answer.stdout, "", "a refused identity prints no document to mistake for one")
        self.assertIn("source identity refused", answer.stderr)
        self.assertIn("records/missing/vectors.json", answer.stderr)

    def test_a_wholly_ignored_declared_input_refuses(self):
        self.write("records/context/worker/__pycache__/only.pyc", "generated\n")
        with self.assertRaises(source_identity.MissingInput):
            self.identity("records/context/worker/__pycache__")

    def test_a_deleted_tracked_input_refuses(self):
        os.remove(os.path.join(self.repo, "records", "gate", "engine-gate.py"))
        with self.assertRaises(source_identity.MissingInput) as caught:
            self.identity("records/gate/engine-gate.py")
        self.assertIn("tracked but absent", str(caught.exception))

    def test_the_command_line_takes_each_input_and_prints_them(self):
        answer = self.cli("--input", "records/gate/engine-gate.py", "--input", "records/context/worker")
        self.assertEqual(answer.returncode, 0, answer.stderr)
        document = json.loads(answer.stdout)
        self.assertEqual(document["inputs"], ["records/context/worker", "records/gate/engine-gate.py"])
        self.assertEqual(document["consumed_count"], 2)
        self.assertEqual(document["content_digest"],
                         self.identity("records/gate/engine-gate.py", "records/context/worker")["content_digest"])


class TheRealTreesDeclaredInputsExist(unittest.TestCase):
    """The declaration in `tools.parallel_test` names this checkout's actual inputs.

    A declared input that is absent would refuse every `test-all`; this is the
    cheap check that says so before one is selected. It hashes the real
    declared inputs (a few dozen small files) and the changed files under
    `v12/`; it runs no test and needs no engine.
    """

    def test_every_declared_input_is_present_and_outside_the_scope(self):
        declared = consumed_inputs()
        found = source_identity.identity(str(REPOSITORY), ["v12"], declared)
        self.assertEqual(found["inputs"], declared)
        self.assertEqual(sorted({one["input"] for one in found["consumed"]}), declared, "each declared input yielded a file")
        for one in found["consumed"]:
            self.assertTrue(one["path"].startswith("work/records/"), one["path"])
            self.assertNotIn("__pycache__", one["path"])
            self.assertEqual(len(one["sha256"]), 64, one)
        self.assertGreaterEqual(found["consumed_count"], len(declared))

    def test_the_supervisor_is_derived_from_the_supervised_registry(self):
        for entry in SUPERVISED_MODULES:
            self.assertIn(entry["supervisor"].partition(":")[2], consumed_inputs())

    def test_the_declared_command_line_agrees_with_the_library(self):
        answer = subprocess.run([sys.executable, "-m", "tools.source_identity", "--repo", str(REPOSITORY), "--declared", "v12"],
                                capture_output=True, text=True, cwd=str(pathlib.Path(__file__).resolve().parents[2]))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        document = json.loads(answer.stdout)
        self.assertEqual(document["inputs"], consumed_inputs())
        self.assertEqual(document["content_digest"],
                         source_identity.identity(str(REPOSITORY), ["v12"], consumed_inputs())["content_digest"])


if __name__ == "__main__":
    unittest.main()
