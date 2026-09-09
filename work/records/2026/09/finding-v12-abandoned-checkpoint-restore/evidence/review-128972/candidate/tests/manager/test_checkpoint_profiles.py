import os
import subprocess
import tempfile
import unittest

from baton_v12.checkpoint_profiles import (GitCheckpointProfile, checkpoint_ref,
                                           clean_vector, diff_vector,
                                           reset_vector, status_vector,
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


class RestoringOneCheckoutToItsRetainedCheckpoint(unittest.TestCase):
    """W128692: `restore_checkpoint`, over a REAL disposable repository.

    A recorded runner proves which argv crossed; it cannot prove that the
    scratch is gone and the tree is the checkpoint's, which is the whole claim.
    So this builds an actual Git repository, dirties it the three ways an
    abandoned worker really does -- a modified tracked file, an untracked file
    and an ignored one -- and then asks whether the checkout came back.
    """

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = os.path.join(self.temporary.name, "line")
        os.mkdir(self.repository)
        self.environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                            "HOME": self.temporary.name,
                            "GIT_CONFIG_GLOBAL": os.devnull,
                            "GIT_CONFIG_SYSTEM": os.devnull,
                            "GIT_TERMINAL_PROMPT": "0",
                            "GIT_AUTHOR_NAME": "Baton Test",
                            "GIT_AUTHOR_EMAIL": "test@baton.invalid",
                            "GIT_COMMITTER_NAME": "Baton Test",
                            "GIT_COMMITTER_EMAIL": "test@baton.invalid"}
        self.git("init", "-q", "-b", "main")
        self.write("kept.txt", "the reviewed candidate\n")
        self.write(".gitignore", "ignored/\n")
        self.git("add", "--all")
        self.git("commit", "-q", "--message", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.write("kept.txt", "the corrected candidate\n")
        self.git("add", "--all")
        self.git("commit", "-q", "--message", "checkpoint")
        self.profile = GitCheckpointProfile(self.runner)
        self.evidence = self.profile.freeze(
            self.repository, line_id="line-1", revision=1,
            declared_base=self.base)

    def tearDown(self):
        self.temporary.cleanup()

    def runner(self, argv):
        """The deployment's command seam. NOT named `run`: that is
        `TestCase.run`, and shadowing it makes the case call itself."""
        answer = subprocess.run(list(argv), capture_output=True, text=True,
                                env=self.environment, timeout=30)
        return {"returncode": answer.returncode, "stdout": answer.stdout,
                "stderr": answer.stderr}

    def git(self, *arguments):
        answer = subprocess.run(["git", "-C", self.repository, *arguments],
                                capture_output=True, text=True,
                                env=self.environment, timeout=30)
        self.assertEqual(answer.returncode, 0, answer.stderr)
        return answer.stdout

    def write(self, name, body):
        place = os.path.join(self.repository, name)
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def dirty(self):
        """The three kinds of scratch an abandoned worker really leaves."""
        self.write("kept.txt", "the abandoned round never finished this\n")
        self.write("scratch.txt", "untracked\n")
        self.write("ignored/build.log", "ignored\n")

    def test_a_dirty_checkout_comes_back_to_the_exact_checkpoint(self):
        head = self.git("rev-parse", "HEAD").strip()
        tree = self.git("rev-parse", "HEAD^{tree}").strip()
        body = open(os.path.join(self.repository, "kept.txt")).read()
        self.dirty()
        self.assertNotEqual(self.git("status", "--porcelain"), "")

        answered = self.profile.restore_checkpoint(self.repository,
                                                   self.evidence)

        self.assertEqual(answered, self.evidence)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), head)
        self.assertEqual(self.git("rev-parse", "HEAD^{tree}").strip(), tree)
        self.assertEqual(open(os.path.join(self.repository,
                                           "kept.txt")).read(), body)
        # THE SCRATCH IS GONE, tracked, untracked and ignored alike.
        self.assertEqual(self.git("status", "--porcelain",
                                  "--untracked-files=all"), "")
        self.assertFalse(os.path.exists(os.path.join(self.repository,
                                                     "scratch.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.repository,
                                                     "ignored")))

    def test_the_retained_checkpoint_and_its_objects_survive_the_restore(self):
        """A restore that had to destroy the thing it restores to would be no
        recovery at all."""
        reference = self.evidence["reference"]
        self.dirty()
        self.profile.restore_checkpoint(self.repository, self.evidence)
        self.assertEqual(
            self.git("rev-parse", "--verify", reference + "^{commit}").strip(),
            self.evidence["head"])
        self.assertEqual(
            self.git("rev-parse", "--verify", reference + "^{tree}").strip(),
            self.evidence["tree"])
        # AND THE BASE OBJECT IS STILL REACHABLE, so nothing was pruned.
        self.assertEqual(
            self.git("rev-parse", "--verify",
                     self.evidence["base"] + "^{commit}").strip(),
            self.evidence["base"])
        # THE VALIDATION IS THE PROFILE'S OWN, run again from scratch.
        self.assertEqual(
            self.profile.validate(self.repository, self.evidence,
                                  current=True),
            self.evidence)

    def test_nothing_outside_the_nominated_checkout_is_named(self):
        """Every argv is `-C` this repository and option-terminated, so there
        is no operand through which another tree could be reached."""
        sibling = os.path.join(self.temporary.name, "custody")
        os.mkdir(sibling)
        with open(os.path.join(sibling, "retained.txt"), "w") as handle:
            handle.write("immutable sibling custody\n")
        seen = []
        real = self.runner

        def recording(argv):
            seen.append(tuple(argv))
            return real(argv)

        self.profile = GitCheckpointProfile(recording)
        self.dirty()
        self.profile.restore_checkpoint(self.repository, self.evidence)
        self.assertTrue(seen)
        for argv in seen:
            self.assertEqual(argv[:3], ("git", "-C", self.repository), argv)
            self.assertNotIn(sibling, argv)
        self.assertIn(tuple(reset_vector(self.repository,
                                         self.evidence["head"])), seen)
        self.assertIn(tuple(clean_vector(self.repository)), seen)
        self.assertEqual(
            open(os.path.join(sibling, "retained.txt")).read(),
            "immutable sibling custody\n")

    def test_a_moved_checkpoint_reference_refuses_before_any_write(self):
        """THE ORDERING IS THE CONTRACT. A restore that discovered its target
        was wrong AFTER discarding the scratch would have destroyed the only
        copy of the thing it cannot replace."""
        self.dirty()
        before = self.git("status", "--porcelain", "--untracked-files=all")
        self.git("update-ref", self.evidence["reference"], self.base)
        with self.assertRaises(ProfileRefusal):
            self.profile.restore_checkpoint(self.repository, self.evidence)
        self.assertEqual(
            self.git("status", "--porcelain", "--untracked-files=all"), before)

    def test_foreign_or_malformed_evidence_refuses_and_writes_nothing(self):
        self.dirty()
        before = self.git("status", "--porcelain", "--untracked-files=all")
        for spoiled in (dict(self.evidence, profile="not-git"),
                        {"profile": "git"},
                        dict(self.evidence, head="z" * 40)):
            with self.assertRaises(ProfileRefusal):
                self.profile.restore_checkpoint(self.repository, spoiled)
        self.assertEqual(
            self.git("status", "--porcelain", "--untracked-files=all"), before)

    def test_an_unsafe_repository_path_is_refused_by_the_vectors(self):
        for place in ("relative/line", "/tmp/../etc", "/tmp/a:b", ""):
            with self.assertRaises(ProfileRefusal):
                reset_vector(place, self.evidence["head"])
            with self.assertRaises(ProfileRefusal):
                clean_vector(place)

    def test_a_head_that_is_not_one_object_name_is_refused(self):
        """`reset --hard` takes one full object name and nothing else -- not a
        revision expression, not a ref, not a leading dash."""
        for head in ("HEAD~1", "refs/heads/main", "-f", "a" * 39, "A" * 40):
            with self.assertRaises(ProfileRefusal):
                reset_vector(self.repository, head)
