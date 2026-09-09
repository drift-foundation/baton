import os
import subprocess
import tempfile
import unittest

from baton_v12.checkpoint_profiles import (GitCheckpointProfile, checkpoint_ref,
                                           diff_vector, status_vector,
                                           tree_vector, update_ref_vector)
from baton_v12.source_profiles import ProfileRefusal


BASE = "a" * 40
HEAD = "b" * 40
TREE = "c" * 40


class CheckpointProfile(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = os.path.join(self.temporary.name, "repository")
        os.mkdir(self.repository)
        self.commands = []

    def tearDown(self):
        self.temporary.cleanup()

    def runner(self, argv):
        self.commands.append(argv)
        if argv == tuple(status_vector(self.repository)):
            stdout = ""
        elif argv == tuple(["git", "-C", self.repository, "rev-parse",
                            "--verify", "HEAD"]):
            stdout = HEAD + "\n"
        elif argv == tuple(tree_vector(self.repository)):
            stdout = TREE + "\n"
        elif argv == tuple(diff_vector(self.repository, BASE, HEAD)):
            stdout = "a.txt\x00z.txt\x00"
        elif argv == tuple(update_ref_vector(
                self.repository, checkpoint_ref("line-1", 1), HEAD)):
            stdout = ""
        elif argv == tuple(["git", "-C", self.repository, "rev-parse",
                            "--verify",
                            checkpoint_ref("line-1", 1) + "^{commit}"]):
            stdout = HEAD + "\n"
        elif argv == tuple(tree_vector(
                self.repository, checkpoint_ref("line-1", 1))):
            stdout = TREE + "\n"
        else:
            self.fail(f"unexpected command: {argv!r}")
        return {"returncode": 0, "stdout": stdout, "stderr": ""}

    def test_freeze_retains_and_revalidates_exact_ref_tree_and_path_set(self):
        evidence = GitCheckpointProfile(self.runner).freeze(
            self.repository, line_id="line-1", revision=1,
            declared_base=BASE)
        self.assertEqual(evidence["reference"], checkpoint_ref("line-1", 1))
        self.assertEqual(evidence["head"], HEAD)
        self.assertEqual(evidence["tree"], TREE)
        self.assertEqual(evidence["paths"], ["a.txt", "z.txt"])
        self.assertIn(tuple(update_ref_vector(
            self.repository, checkpoint_ref("line-1", 1), HEAD)),
            self.commands)

    def test_checkpoint_refs_are_reserved_and_revision_vectors_are_unambiguous(self):
        reference = checkpoint_ref("line-1", 7)
        self.assertEqual(reference, "refs/baton/checkpoints/line-1/7")
        self.assertEqual(tree_vector(self.repository, reference)[-1],
                         reference + "^{tree}")
        with self.assertRaises(ProfileRefusal):
            update_ref_vector(self.repository, "refs/heads/main", HEAD)

    def test_dirty_candidate_refuses_before_ref_retention(self):
        def dirty(argv):
            if argv == tuple(status_vector(self.repository)):
                return {"returncode": 0, "stdout": "?? untracked\x00",
                        "stderr": ""}
            self.fail(f"unexpected command after dirty status: {argv!r}")
        with self.assertRaisesRegex(ProfileRefusal, "clean committed"):
            GitCheckpointProfile(dirty).freeze(
                self.repository, line_id="line-1", revision=1,
                declared_base=BASE)

    def test_runner_result_is_closed(self):
        with self.assertRaisesRegex(ProfileRefusal, "closed"):
            GitCheckpointProfile(lambda argv: {"returncode": 0}).freeze(
                self.repository, line_id="line-1", revision=1,
                declared_base=BASE)

    def test_real_git_keeps_an_old_checkpoint_after_the_line_advances(self):
        source = os.path.join(self.temporary.name, "source")
        line = os.path.join(self.temporary.name, "line")

        def git(*arguments):
            return subprocess.run(
                arguments, check=True, text=True, capture_output=True).stdout.strip()

        def runner(argv):
            completed = subprocess.run(argv, text=True, capture_output=True)
            return {"returncode": completed.returncode,
                    "stdout": completed.stdout, "stderr": completed.stderr}

        git("git", "init", "-q", source)
        git("git", "-C", source, "config", "user.name", "Baton Test")
        git("git", "-C", source, "config", "user.email", "baton@example.invalid")
        with open(os.path.join(source, "candidate.txt"), "w", encoding="utf-8") as writing:
            writing.write("base\n")
        git("git", "-C", source, "add", "candidate.txt")
        git("git", "-C", source, "commit", "-q", "-m", "base")
        base = git("git", "-C", source, "rev-parse", "HEAD")
        with open(os.path.join(source, "candidate.txt"), "w", encoding="utf-8") as writing:
            writing.write("source tip after declared base\n")
        git("git", "-C", source, "add", "candidate.txt")
        git("git", "-C", source, "commit", "-q", "-m", "later source tip")
        # Simulate a stop after clone and before the profile detached the line
        # to the declared base. Recovery adopts this checkout and clones no
        # second tree.
        git("git", "clone", "-q", source, line)
        profile = GitCheckpointProfile(runner)
        profile.materialize(source, line, base)
        self.assertEqual(git("git", "-C", line, "rev-parse", "HEAD"), base)
        git("git", "-C", line, "config", "user.name", "Baton Test")
        git("git", "-C", line, "config", "user.email", "baton@example.invalid")

        with open(os.path.join(line, "candidate.txt"), "w", encoding="utf-8") as writing:
            writing.write("first\n")
        git("git", "-C", line, "add", "candidate.txt")
        git("git", "-C", line, "commit", "-q", "-m", "first checkpoint")
        first = profile.freeze(line, line_id="line-real", revision=1,
                               declared_base=base)
        with open(os.path.join(line, "candidate.txt"), "w", encoding="utf-8") as writing:
            writing.write("second\n")
        git("git", "-C", line, "add", "candidate.txt")
        git("git", "-C", line, "commit", "-q", "-m", "second checkpoint")
        second = profile.freeze(line, line_id="line-real", revision=2,
                                declared_base=base)

        self.assertNotEqual(first["head"], second["head"])
        self.assertEqual(profile.validate(line, first, current=False), first)
        self.assertEqual(git("git", "-C", line, "rev-parse", first["reference"]),
                         first["head"])
        with self.assertRaisesRegex(ProfileRefusal, "no longer matches"):
            profile.validate(line, first, current=True)


if __name__ == "__main__":
    unittest.main()
