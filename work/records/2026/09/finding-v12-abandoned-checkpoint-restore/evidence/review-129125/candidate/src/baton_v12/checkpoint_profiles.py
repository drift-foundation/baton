"""Profile-owned immutable review checkpoints.

W71918 keeps Git out of the generic review-cycle manager.  This module owns
the exact Git commands and turns their bounded answers into opaque checkpoint
evidence.  A deployment supplies the command runner; the manager sees only
``materialize``, ``freeze`` and ``validate`` capabilities and never an argv.

The first checkout is the one materialization of a development line.  Later
correction rounds reuse it.  A checkpoint is a retained ref to the exact commit
and tree, not a copy of the worktree and not the mutable checkout pathname.
"""

import os

from .contracts import digest
from .source_profiles.checkout import (GIT_PROFILE, ProfileRefusal,
                                       check_declared_base, clone_vector,
                                       detach_vector, verify_vector)

__all__ = ["GitCheckpointProfile", "checkpoint_ref", "clean_vector",
           "diff_vector", "reset_vector", "status_vector", "tree_vector",
           "update_ref_vector"]


def _path(place, what):
    if type(place) is not str or not place or not os.path.isabs(place):
        raise ProfileRefusal(f"{what} is an absolute non-empty path")
    if "\x00" in place or ".." in place.split("/") or ":" in place:
        raise ProfileRefusal(f"{what} is a canonical engine-safe path")
    if os.path.normpath(place) != place:
        raise ProfileRefusal(f"{what} has one canonical spelling")
    return place


def _identity(value, what):
    if type(value) is not str or not value or "/" in value or "\x00" in value:
        raise ProfileRefusal(f"{what} is non-empty opaque text without a slash")
    return value


def _reference(value):
    if (type(value) is not str or not value.startswith("refs/baton/checkpoints/")
            or "\x00" in value or ".." in value.split("/")
            or value.endswith("/") or value.startswith("-")):
        raise ProfileRefusal("a checkpoint reference is in the reserved Baton namespace")
    return value


def _revision(value, what):
    if (type(value) is not str or not value or "\x00" in value
            or value.startswith("-") or value.endswith("^{tree}")
            or value.endswith("^{commit}")):
        raise ProfileRefusal(f"{what} is one unambiguous Git revision")
    return value


def checkpoint_ref(line_id, revision):
    _identity(line_id, "a development line identity")
    if type(revision) is not int or type(revision) is bool or revision < 1:
        raise ProfileRefusal("a checkpoint revision is a positive integer")
    return f"refs/baton/checkpoints/{line_id}/{revision}"


def status_vector(repository):
    return ["git", "-C", _path(repository, "a private line repository"),
            "status", "--porcelain=v1", "-z", "--untracked-files=all"]


def tree_vector(repository, commit="HEAD"):
    return ["git", "-C", _path(repository, "a private line repository"),
            "rev-parse", "--verify", f"{_revision(commit, 'a commit')}^{{tree}}"]


def diff_vector(repository, base, head):
    return ["git", "-C", _path(repository, "a private line repository"),
            "diff", "--name-only", "-z", "--no-renames",
            f"{check_declared_base(base)}..{check_declared_base(head)}"]


def update_ref_vector(repository, reference, head):
    return ["git", "-C", _path(repository, "a private line repository"),
            "update-ref", _reference(reference),
            check_declared_base(head)]


def reset_vector(repository, head):
    """Put the tracked worktree and index back on one exact commit.

    W128692. `--hard` IS THE POINT AND IS ALSO THE WHOLE DANGER, so the operand
    is not a caller's string: `check_declared_base` admits one full object name
    and nothing else, which is what stops a revision expression, a ref name, a
    pathspec or a leading dash arriving here. The repository is the same
    `_path` every other vector in this module takes.

    IT WRITES NO OBJECT AND MOVES NO REF THIS MODULE RETAINS. `reset --hard`
    moves HEAD and the index; the checkpoint refs live under
    `refs/baton/checkpoints/` and are not HEAD, and no object is deleted --
    which is what makes a restore reversible in the only sense that matters
    here, that the checkpoint it restores to is still there afterwards.
    """
    return ["git", "-C", _path(repository, "a private line repository"),
            "reset", "--hard", check_declared_base(head), "--"]


def clean_vector(repository):
    """Remove the untracked scratch `reset --hard` deliberately leaves.

    `-x` INCLUDES IGNORED FILES, and that is the decision rather than an
    oversight: an abandoned worker's build output, virtualenv or editor state
    is exactly the uncommitted scratch this restore exists to discard, and a
    checkout that still carried it would not be the retained checkpoint's tree.

    `--` ENDS THE OPTIONS AND NO PATHSPEC FOLLOWS, so this is the whole
    nominated checkout and never a caller-chosen subtree. Git never removes
    `.git` itself, so the repository's objects and the retained checkpoint refs
    survive this by the tool's own rule rather than by one stated here.
    """
    return ["git", "-C", _path(repository, "a private line repository"),
            "clean", "-f", "-d", "-x", "--"]


class _HeldCheckout:
    """One nominated checkout, HELD AS AN OBJECT for as long as it is written.

    W128692 review 2026-09-09T16:04Z, and it is right that my previous cut was
    the same gap one boundary further along. Comparing `lstat` before and after
    the command is still a PATHNAME comparison: the interval between the check
    and the child's own resolution belongs to whoever can rename the directory,
    and the reviewer's runner replaced it in exactly that interval.

    SO THE OBJECT IS OPENED, NOT NAMED. An `O_DIRECTORY | O_NOFOLLOW` descriptor
    IS the checkout -- a rename cannot redirect it and a symlink cannot become
    it -- and the path handed to each command is derived FROM that descriptor
    immediately before the command runs. Substituting the original name no
    longer substitutes the target: the commands follow the object this profile
    was nominated over, wherever that object has been moved to.

    THE RUNNER CONTRACT IS UNCHANGED. It receives argv and nothing else, so the
    descriptor cannot cross into the child; what crosses is a path this process
    derives from the descriptor at the last possible moment and proves is still
    that same object. `/proc/self/fd` is what makes that derivation possible,
    and a platform without it is told exactly which capability is missing
    rather than quietly getting the weaker pathname behaviour.
    """

    def __init__(self, repository):
        if os.path.islink(repository):
            raise ProfileRefusal(
                "the private line repository is a directory of its own and "
                "not a link to one")
        try:
            self._fd = os.open(repository,
                               os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError:
            raise ProfileRefusal(
                "the private line repository is a real directory this "
                "restore can hold open") from None
        try:
            status = os.fstat(self._fd)
        except OSError:
            os.close(self._fd)
            raise ProfileRefusal(
                "the private line repository could not be identified") from None
        self._identity = (status.st_dev, status.st_ino)

    def __enter__(self):
        return self

    def __exit__(self, *ended):
        os.close(self._fd)
        return False

    def place(self):
        """Where the HELD object is right now, proved to still be it."""
        link = f"/proc/self/fd/{self._fd}"
        if not os.path.lexists(link):
            raise ProfileRefusal(
                "this deployment cannot resolve an open directory descriptor "
                "to a path, so a restore cannot bind its commands to the "
                "checkout it holds rather than to a name")
        try:
            place = os.readlink(link)
        except OSError:
            raise ProfileRefusal(
                "the held private line repository could not be located") from None
        if place.endswith(" (deleted)"):
            raise ProfileRefusal(
                "the held private line repository has been removed; a restore "
                "writes the exact checkout it was nominated over")
        place = _path(place, "a private line repository")
        try:
            status = os.stat(place)
        except OSError:
            raise ProfileRefusal(
                "the held private line repository could not be located") from None
        if (status.st_dev, status.st_ino) != self._identity:
            raise ProfileRefusal(
                "the held private line repository now resolves to another "
                "object; a restore writes the exact checkout it was nominated "
                "over")
        return place


class GitCheckpointProfile:
    """The Git profile as injected, bounded command capabilities.

    ``runner`` receives one tuple argv and returns exactly ``returncode``,
    ``stdout`` and ``stderr``.  stderr is used only in a local refusal and is
    never returned as checkpoint evidence.
    """

    name = GIT_PROFILE

    def __init__(self, runner):
        if not callable(runner):
            raise ProfileRefusal("a Git checkpoint profile needs a command runner")
        self._runner = runner

    def _run(self, argv, what):
        answer = self._runner(tuple(argv))
        if type(answer) is not dict or set(answer) != {
                "returncode", "stdout", "stderr"}:
            raise ProfileRefusal(
                f"the Git runner's {what} answer has the closed command-result shape")
        if type(answer["returncode"]) is not int or type(answer["returncode"]) is bool:
            raise ProfileRefusal(f"the Git runner's {what} status is an integer")
        if type(answer["stdout"]) is not str or type(answer["stderr"]) is not str:
            raise ProfileRefusal(f"the Git runner's {what} streams are text")
        if answer["returncode"] != 0:
            detail = answer["stderr"].strip()[:240]
            raise ProfileRefusal(f"Git {what} failed" +
                                 (f": {detail}" if detail else ""))
        return answer["stdout"]

    def _head(self, repository):
        found = self._run(verify_vector(repository), "HEAD verification").strip()
        return check_declared_base(found)

    def _clean(self, repository):
        if self._run(status_vector(repository), "clean-worktree check") != "":
            raise ProfileRefusal(
                "a checkpoint freezes a clean committed candidate; the private "
                "line still has tracked or untracked worktree changes")

    def materialize(self, source, repository, declared_base):
        source = _path(source, "a nominated source")
        repository = _path(repository, "a private line repository")
        base = check_declared_base(declared_base)
        if not os.path.lexists(repository):
            self._run(clone_vector(source, repository), "line materialization")
        elif not os.path.isdir(repository) or os.path.islink(repository):
            raise ProfileRefusal(
                "the private line repository is not a directory of its own")
        # Also run on recovery. A process may have completed the clone and
        # stopped before detaching its worktree to the declared base; the one
        # existing checkout is resumed, never cloned or copied again.
        self._run(detach_vector(repository, declared=base),
                  "declared-base checkout")
        head = self._head(repository)
        if head != base:
            raise ProfileRefusal(
                f"the private line is at {head!r}, not declared base {base!r}")
        self._clean(repository)
        return {"profile": GIT_PROFILE, "base": base, "head": head}

    def freeze(self, repository, *, line_id, revision, declared_base):
        repository = _path(repository, "a private line repository")
        base = check_declared_base(declared_base)
        self._clean(repository)
        head = self._head(repository)
        tree = check_declared_base(
            self._run(tree_vector(repository), "tree verification").strip())
        paths_text = self._run(diff_vector(repository, base, head),
                               "reviewed-path inventory")
        paths = paths_text.split("\x00")
        if paths and paths[-1] == "":
            paths.pop()
        if any(not path or path.startswith("/") or ".." in path.split("/")
               for path in paths) or len(set(paths)) != len(paths):
            raise ProfileRefusal("Git returned a non-canonical reviewed path set")
        paths.sort()
        reference = checkpoint_ref(line_id, revision)
        self._run(update_ref_vector(repository, reference, head),
                  "checkpoint-reference retention")
        evidence = {"profile": GIT_PROFILE, "base": base, "head": head,
                    "tree": tree, "paths": paths,
                    "path_set_digest": digest(paths), "reference": reference}
        self.validate(repository, evidence, current=True)
        return evidence

    def restore_checkpoint(self, repository, evidence):
        """Discard this private checkout's scratch back to a retained
        checkpoint.

        W128692, `work/records/2026/09/finding-v12-abandoned-checkpoint-
        restore/`. A declared abandoned correction leaves a dirty checkout and
        an active writer, and `grant_writer` admits nobody while the line is
        `writing` -- but simply moving those rows would hand the next writer a
        tree full of somebody else's unfinished work, and
        `validate(current=True)` would refuse it anyway. This is the missing
        act: put the checkout back exactly on the checkpoint the correction was
        based on.

        THE CHECKPOINT IS VERIFIED BEFORE ANY WRITE, and that ordering is the
        contract rather than a preference. `validate` re-reads the retained
        reference, its commit and its tree, and re-derives the reviewed path
        set -- so a moved reference, a changed tree, a foreign profile or
        evidence that is not this profile's shape all refuse while the
        worktree is still untouched. A restore that discovered its target was
        wrong AFTER discarding the scratch would have destroyed the only copy
        of the thing it could not replace.

        AND SO IS THE OBJECT, which two rounds of review are about. Validating
        the PATHNAME and the checkpoint CONTENTS let a rename plus a symlink at
        the old name point the destructive commands at a tree outside the line;
        and comparing that pathname's identity before and after the commands
        was the same gap one boundary along, because the interval between the
        check and the child's own resolution belongs to whoever can rename the
        directory.

        SO THE CHECKOUT IS HELD AS AN OBJECT, by an `O_DIRECTORY | O_NOFOLLOW`
        descriptor, and every command's path is derived from that descriptor
        immediately before it runs. A rename cannot redirect a descriptor and a
        symlink cannot become one, so the commands follow the checkout this
        profile was nominated over rather than whatever its old name now
        points at.

        WHAT IS WRITTEN IS THE NOMINATED CHECKOUT AND NOTHING ELSE. Two
        commands, both `-C` this repository, both option-terminated with no
        pathspec: `reset --hard <head>` for tracked state and `clean -fdx` for
        untracked. No object is deleted, no ref this module retains is moved,
        and nothing outside the repository is named at all -- so the immutable
        sibling custody beside a line, and every path outside it, are untouched
        because they are never operands.

        AND THE ANSWER IS EARNED RATHER THAN ASSERTED. The same evidence comes
        back only after `validate(current=True)` succeeds, which is the
        profile's own proof that the checkout is now CLEAN and at the
        checkpoint's exact head. A restore that returned before proving that
        would be reporting an intention.
        """
        repository = _path(repository, "a private line repository")
        with _HeldCheckout(repository) as checkout:
            # BEFORE THE FIRST WRITE. `validate` owns the evidence shape, the
            # profile, the retained reference, its commit and tree, and the
            # reviewed path set -- and it is asked over the HELD object, so it
            # verifies the same checkout the writes will reach.
            held = self.validate(checkout.place(), evidence)
            head = check_declared_base(held["head"])
            self._run(reset_vector(checkout.place(), head),
                      "checkpoint restoration")
            self._run(clean_vector(checkout.place()), "scratch removal")
            return self.validate(checkout.place(), held, current=True)

    def validate(self, repository, evidence, *, current=False):
        repository = _path(repository, "a private line repository")
        if type(evidence) is not dict or set(evidence) != {
                "profile", "base", "head", "tree", "paths",
                "path_set_digest", "reference"}:
            raise ProfileRefusal("Git checkpoint evidence has its closed shape")
        if evidence["profile"] != GIT_PROFILE:
            raise ProfileRefusal("Git validates only Git checkpoint evidence")
        base = check_declared_base(evidence["base"])
        head = check_declared_base(evidence["head"])
        tree = check_declared_base(evidence["tree"])
        reference = _reference(evidence["reference"])
        held = self._run(["git", "-C", repository, "rev-parse", "--verify",
                          f"{reference}^{{commit}}"],
                         "checkpoint-reference verification").strip()
        if check_declared_base(held) != head:
            raise ProfileRefusal("the retained checkpoint reference moved")
        held_tree = self._run(tree_vector(repository, reference),
                              "checkpoint-tree verification").strip()
        if check_declared_base(held_tree) != tree:
            raise ProfileRefusal("the retained checkpoint tree changed")
        paths_text = self._run(diff_vector(repository, base, head),
                               "checkpoint-path verification")
        paths = sorted(path for path in paths_text.split("\x00") if path)
        if evidence["paths"] != paths or evidence["path_set_digest"] != digest(paths):
            raise ProfileRefusal("the checkpoint's reviewed path set changed")
        if current:
            self._clean(repository)
            if self._head(repository) != head:
                raise ProfileRefusal(
                    "the mutable line no longer matches the checkpoint requested "
                    "for current read-only review")
        return dict(evidence)
