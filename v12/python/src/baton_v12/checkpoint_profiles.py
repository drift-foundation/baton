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

__all__ = ["GitCheckpointProfile", "checkpoint_ref", "diff_vector",
           "status_vector", "tree_vector", "update_ref_vector"]


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
