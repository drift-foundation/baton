"""W384870 review R2 — the content-bound source identity, over a disposable repository.

The property under test is the one the review showed missing: two candidates
with IDENTICAL `git status` text and different bytes must have different
identities, untracked files must count, ignored files must not, and the
boundary must be stated.
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
        self.write(".gitignore", "/scope/build/\n")
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

    def identity(self):
        return source_identity.identity(self.repo, ["scope"])

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
        answer = subprocess.run([sys.executable, "-m", "tools.source_identity", "--repo", self.repo, "scope"],
                                check=True, capture_output=True, text=True,
                                cwd=str(pathlib.Path(__file__).resolve().parents[2]))
        self.assertEqual(json.loads(answer.stdout)["content_digest"], self.identity()["content_digest"])


if __name__ == "__main__":
    unittest.main()
