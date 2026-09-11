"""Standalone Git primitives for preparing and importing an integration result.

W131409 replacement slice P, INTEGRATION-CONTRACT-v1 sections 2 and 6.

WHAT THIS IS FOR. An eligible submission is the producer's ORIGINAL candidate,
built on the base its line was declared at. An integration result is a
DIFFERENT immutable candidate: that submission's net change reconciled with one
exact current target snapshot. This module owns the mechanics of producing and
proving that second object, and nothing else.

IT IS STANDALONE ON PURPOSE. It imports no manager, no Authority, no store and
no coordinator capability -- only the standard library and its own refusal --
so the same primitives can be copied into an integration worker image without
carrying a control-plane capability across that boundary. Every command is
composed here as an argv and handed to an injected runner; this module opens no
process itself.

WHERE IT MAY WRITE, and it is two places only. Objects and preparation
references live in the NOMINATED PRIVATE STORAGE the integration role was given.
The dedicated target repository is written at exactly one explicitly configured
reference, and only through a compare-and-swap from the revision the result was
reviewed against. No human repository index, branch or history is ever an
operand: `merge-tree` and `commit-tree` read and write objects, and the one ref
write names its own reserved reference and its expected old value.

WHAT IT DOES NOT DECIDE. A clean textual merge establishes prepared CONTENT and
nothing more -- not correctness, not eligibility, not authorization. A conflict
is an ANSWER carrying its paths, not a failure, because resolving one
automatically is outside this first capability by explicit decision.
"""

import os

__all__ = ["GitIntegrationProfile", "IntegrationProfileRefusal",
           "PREPARED_NAMESPACE", "PROFILE_NAME", "PROFILE_VERSION",
           "advance_ref_vector", "commit_tree_vector", "import_vector",
           "merge_tree_vector", "prepared_ref", "read_ref_vector",
           "tree_entries_vector", "verify_vector"]

PROFILE_NAME = "git-integration"
PROFILE_VERSION = 1

# THE RESERVED NAMESPACE PREPARATION RETAINS UNDER. A prepared result is not a
# checkpoint and not a branch: nobody has reviewed it yet, it is not any line's
# revision, and the act that produces it must be unable to name a checkpoint
# reference at all. A separate namespace makes that a property of the name
# check rather than of the caller's care.
PREPARED_NAMESPACE = "refs/baton/integration/prepared/"

# The identity a prepared commit is recorded under. It is the INTEGRATION
# ROLE's and deliberately not the producing worker's: nobody authored these
# bytes -- they are the recorded three-way result of a reviewed submission and
# a target snapshot -- and borrowing a human's name for them would assert an
# authorship that did not happen.
AUTHOR_NAME = "Baton integration"
AUTHOR_EMAIL = "integration@baton.invalid"

_OBJECT = 40


class IntegrationProfileRefusal(Exception):
    """This profile's own refusal, so the module needs no contracts import."""


def _refuse(message):
    raise IntegrationProfileRefusal(message)


def _object_name(value, what):
    """One full object name, and nothing a revision expression could be.

    Forty lowercase hex characters or a refusal. A ref name, a `HEAD~2`, a
    pathspec or a leading dash never reaches a command from here.
    """
    if type(value) is not str or len(value) != _OBJECT \
            or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lowercase object name")
    return value


def _path(place, what):
    if type(place) is not str or not place or not os.path.isabs(place):
        _refuse(f"{what} is an absolute non-empty path")
    if "\x00" in place or ".." in place.split("/") or ":" in place:
        _refuse(f"{what} is a canonical engine-safe path")
    if os.path.normpath(place) != place:
        _refuse(f"{what} has one canonical spelling")
    return place


def _reference(value, namespace):
    if (type(value) is not str or not value.startswith(namespace)
            or "\x00" in value or ".." in value.split("/")
            or value.endswith("/") or value.startswith("-")):
        _refuse(f"a reference in this act is under {namespace}")
    return value


def _configured_reference(value):
    """The dedicated target's own configured revision reference.

    IT IS CONFIGURATION AND NOT A CALLER'S CHOICE, which is why the only rule
    here is the shape one: it must be a real `refs/` name, it may not be a
    symbolic name like `HEAD`, and it may not be spelled so that Git could read
    it as an option. WHICH reference is the deployment's decision, proved by
    the caller having been configured with it.
    """
    if (type(value) is not str or not value.startswith("refs/")
            or "\x00" in value or ".." in value.split("/")
            or value.endswith("/") or value.startswith("-")):
        _refuse("a configured target revision reference is a refs/ name")
    return value


def prepared_ref(result_id):
    """The reserved name one prepared integration result is retained under."""
    if type(result_id) is not str or not result_id or "/" in result_id \
            or "\x00" in result_id or result_id.startswith("-"):
        _refuse("a result identity is non-empty opaque text without a slash")
    return PREPARED_NAMESPACE + result_id


def import_vector(repository, source, revision):
    """Bring ONE named object into the private preparation storage.

    `fetch` writes objects and moves no branch, no tag and no reference this
    module retains. The source is named as a PATH rather than a URL, so no
    transport is configured by this act.
    """
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "fetch", "--no-tags", "--no-write-fetch-head",
            _path(source, "a nominated source repository"),
            _object_name(revision, "an imported revision")]


def verify_vector(repository, revision):
    """Resolve one revision to its commit, proving the store really holds it."""
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "rev-parse", "--verify",
            f"{_object_name(revision, 'a revision')}^{{commit}}"]


def tree_of_vector(repository, revision):
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "rev-parse", "--verify",
            f"{_object_name(revision, 'a revision')}^{{tree}}"]


def merge_tree_vector(repository, base, target, candidate):
    """The three-way reconciliation, computed entirely in the object store.

    THIS IS WHY THE ACT IS CONTAINABLE. `merge-tree --write-tree` reads three
    commits and writes the merged TREE; it touches no index, no worktree, no
    HEAD and no reference, so the producer's line is not an operand and cannot
    be. What it answers is the submission's net change -- `base..candidate` --
    replayed onto `target`, which is the reconciliation this result owes rather
    than a checkout at the target.
    """
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "merge-tree", "--write-tree", "-z", "--name-only",
            f"--merge-base={_object_name(base, 'the submission base')}",
            _object_name(target, "the target snapshot"),
            _object_name(candidate, "the submitted candidate")]


def commit_tree_vector(repository, tree, parent, message):
    """Record one merged tree as a commit whose only parent is the target.

    ONE PARENT AND NOT TWO. A two-parent merge commit would say these bytes are
    the meeting of two histories; what actually happened is that a reviewed
    submission was re-expressed on top of one target snapshot, and the result is
    reviewed and imported as its own candidate. The identity is supplied on the
    command line so this act needs no ambient configuration and cannot inherit
    a human's.
    """
    if type(message) is not str or not message or "\x00" in message:
        _refuse("a prepared result's message is non-empty text")
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "-c", f"user.name={AUTHOR_NAME}",
            "-c", f"user.email={AUTHOR_EMAIL}",
            "commit-tree", _object_name(tree, "the merged tree"),
            "-p", _object_name(parent, "the target snapshot"), "-m", message]


def retain_vector(repository, reference, commit):
    """Retain a prepared result, in the prepared namespace and nowhere else."""
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "update-ref", _reference(reference, PREPARED_NAMESPACE),
            _object_name(commit, "a prepared result")]


def read_ref_vector(repository, reference):
    """Read the dedicated target's configured revision reference."""
    return ["git", "-C", _path(repository, "the dedicated target repository"),
            "rev-parse", "--verify",
            f"{_configured_reference(reference)}^{{commit}}"]


def advance_ref_vector(repository, reference, new, expected):
    """Advance the configured reference, COMPARE-AND-SWAP on its old value.

    The third operand is what makes this safe against a second writer: Git
    refuses the update unless the reference still holds exactly the revision
    the result was reviewed against. An advance that merely set the new value
    would be a last-writer-wins target.
    """
    return ["git", "-C", _path(repository, "the dedicated target repository"),
            "update-ref", _configured_reference(reference),
            _object_name(new, "the imported result"),
            _object_name(expected, "the reviewed target revision")]


def tree_entries_vector(repository, revision):
    """Every path and mode one revision's tree carries, recursively.

    `-z` and full recursion, so the answer is the complete target-relative
    path/mode set rather than a summary of it. Submodules and symlinks come
    back with their own modes and are refused by the reader rather than
    silently flattened.
    """
    return ["git", "-C", _path(repository, "a private preparation repository"),
            "ls-tree", "-r", "-z", "--full-tree",
            _object_name(revision, "a revision")]


# The four file modes a result may carry. A gitlink (160000) is a submodule
# and a symlink (120000) is a pointer whose target this import does not own;
# both refuse rather than being imported as though they were content.
_CONTENT_MODES = frozenset({"100644", "100755"})
_NAMED_MODES = {"120000": "a symbolic link", "160000": "a submodule"}


class GitIntegrationProfile:
    """The bounded command capabilities an integration result is made with.

    `runner` receives one tuple argv and answers exactly `returncode`,
    `stdout` and `stderr`. stderr is used only in a local refusal and is never
    returned as evidence.
    """

    name = PROFILE_NAME
    version = PROFILE_VERSION

    def __init__(self, runner):
        if not callable(runner):
            _refuse("a Git integration profile needs a command runner")
        self._runner = runner

    def _answer(self, argv, what):
        answer = self._runner(tuple(argv))
        if type(answer) is not dict or set(answer) != {
                "returncode", "stdout", "stderr"}:
            _refuse(f"the Git runner's {what} answer has the closed "
                    f"command-result shape")
        if type(answer["returncode"]) is not int \
                or type(answer["returncode"]) is bool:
            _refuse(f"the Git runner's {what} status is an integer")
        if type(answer["stdout"]) is not str or type(answer["stderr"]) is not str:
            _refuse(f"the Git runner's {what} streams are text")
        return answer

    def _run(self, argv, what):
        answer = self._answer(argv, what)
        if answer["returncode"] != 0:
            detail = answer["stderr"].strip()[:240]
            _refuse(f"Git {what} failed" + (f": {detail}" if detail else ""))
        return answer["stdout"]

    # -- reading what a repository really holds ------------------------------

    def held(self, repository, revision, what="a revision"):
        """This repository really holds that exact commit AND its tree.

        A digest this role was told about is not content. What makes it content
        is that the store resolves it to a commit and that commit to a tree.
        """
        commit = self._run(verify_vector(repository, revision),
                           f"{what} verification").strip()
        if _object_name(commit, what) != revision:
            _refuse(f"{what} does not resolve to itself")
        return {"commit": revision,
                "tree": _object_name(
                    self._run(tree_of_vector(repository, revision),
                              f"{what} tree verification").strip(),
                    f"{what}'s tree")}

    def content(self, repository, revision):
        """The complete target-relative path and mode set of one revision.

        UNSUPPORTED KINDS REFUSE HERE rather than at the import. A symlink or a
        submodule in a prepared result is a path whose meaning this import does
        not own, and discovering that while writing the target would be one
        boundary too late.
        """
        text = self._run(tree_entries_vector(repository, revision),
                         "result content inventory")
        held = {}
        for record in text.split("\x00"):
            if not record:
                continue
            meta, _, path = record.partition("\t")
            fields = meta.split()
            if len(fields) != 3 or not path:
                _refuse("Git returned a tree entry this profile cannot read")
            mode, kind, _oid = fields
            if mode in _NAMED_MODES:
                _refuse(f"the prepared result carries {_NAMED_MODES[mode]} at "
                        f"{path!r}; this import owns ordinary file content and "
                        f"refuses a path kind it cannot apply")
            if kind != "blob" or mode not in _CONTENT_MODES:
                _refuse(f"the prepared result carries an unsupported entry at "
                        f"{path!r}")
            if path.startswith("/") or ".." in path.split("/") or path in held:
                _refuse("Git returned a non-canonical result path set")
            held[path] = mode
        return held

    # -- preparing one result ------------------------------------------------

    def prepare(self, repository, *, result_id, base, candidate, target,
                candidate_source, target_source):
        """Reconcile one submission with one target snapshot, or hold.

        THE ORDER IS THE CONTRACT. Both objects are imported and PROVED to be
        real content before anything is merged, the merge writes only a tree,
        and the retained reference is written last -- so a death anywhere
        leaves either nothing or a reference this profile can validate and
        reuse instead of merging twice.

        A CONFLICT IS AN ANSWER. It comes back held with its paths, and the
        submission's own objects and the target are exactly as they were,
        because neither was ever written.
        """
        repository = _path(repository, "a private preparation repository")
        base = _object_name(base, "the submission base")
        candidate = _object_name(candidate, "the submitted candidate")
        target = _object_name(target, "the target snapshot")
        reference = prepared_ref(result_id)
        self._run(import_vector(repository, candidate_source, candidate),
                  "submission import")
        self._run(import_vector(repository, candidate_source, base),
                  "submission base import")
        self._run(import_vector(repository, target_source, target),
                  "target snapshot import")
        held = {"base": self.held(repository, base, "the submission base"),
                "candidate": self.held(repository, candidate,
                                       "the submitted candidate"),
                "target": self.held(repository, target,
                                    "the target snapshot")}
        prepared = self._retained(repository, reference)
        if prepared is not None:
            # ALREADY PREPARED, VALIDATED RATHER THAN REDONE. Applying the
            # reconciliation twice would write a second commit for one
            # committed intent, which is exactly what a replay must not do.
            return {"state": "prepared", "sources": held,
                    "prepared": self.validate(repository, prepared,
                                              target=target)}
        merged = self._answer(
            merge_tree_vector(repository, base, target, candidate),
            "result reconciliation")
        if merged["returncode"] != 0:
            return {"state": "held", "sources": held,
                    "reason": "the submission's change does not reconcile "
                              "cleanly with this target snapshot",
                    "conflicts": _conflicted(merged["stdout"])}
        tree = _object_name(merged["stdout"].split("\x00")[0].strip(),
                            "the merged tree")
        commit = _object_name(self._run(
            commit_tree_vector(repository, tree, target,
                               f"baton integration result {result_id}"),
            "prepared result commit").strip(), "the prepared result")
        self._run(retain_vector(repository, reference, commit),
                  "prepared result retention")
        return {"state": "prepared", "sources": held,
                "prepared": self.validate(
                    repository,
                    {"profile": PROFILE_NAME, "version": PROFILE_VERSION,
                     "base": target, "head": commit, "tree": tree,
                     "reference": reference,
                     "content": self.content(repository, commit)},
                    target=target)}

    def _retained(self, repository, reference):
        """The prepared result this reference already names, or absence."""
        found = self._answer(
            ["git", "-C", repository, "rev-parse", "--verify",
             f"{_reference(reference, PREPARED_NAMESPACE)}^{{commit}}"],
            "prepared reference lookup")
        if found["returncode"] != 0:
            return None
        commit = _object_name(found["stdout"].strip(), "a prepared result")
        return {"profile": PROFILE_NAME, "version": PROFILE_VERSION,
                "base": _object_name(
                    self._run(["git", "-C", repository, "rev-parse",
                               "--verify", f"{reference}^^{{commit}}"],
                              "prepared parent verification").strip(),
                    "the prepared result's parent"),
                "head": commit,
                "tree": self.held(repository, commit,
                                  "the prepared result")["tree"],
                "reference": reference,
                "content": self.content(repository, commit)}

    def validate(self, repository, prepared, *, target=None):
        """Prove one prepared result against the repository itself."""
        repository = _path(repository, "a private preparation repository")
        if type(prepared) is not dict or set(prepared) != {
                "profile", "version", "base", "head", "tree", "reference",
                "content"}:
            _refuse("prepared result evidence has its closed shape")
        if prepared["profile"] != PROFILE_NAME \
                or prepared["version"] != PROFILE_VERSION:
            _refuse("this profile validates only its own prepared evidence")
        base = _object_name(prepared["base"], "the prepared result's base")
        head = _object_name(prepared["head"], "the prepared result")
        tree = _object_name(prepared["tree"], "the prepared result's tree")
        reference = _reference(prepared["reference"], PREPARED_NAMESPACE)
        if target is not None and base != _object_name(target, "a target"):
            _refuse("the prepared result names another target snapshot")
        named = self._run(["git", "-C", repository, "rev-parse", "--verify",
                           f"{reference}^{{commit}}"],
                          "prepared reference verification").strip()
        if _object_name(named, "the retained result") != head:
            _refuse("the retained prepared reference moved")
        if self.held(repository, head, "the prepared result")["tree"] != tree:
            _refuse("the retained prepared tree changed")
        parent = self._run(["git", "-C", repository, "rev-parse", "--verify",
                            f"{reference}^^{{commit}}"],
                           "prepared parent verification").strip()
        if _object_name(parent, "the prepared result's parent") != base:
            _refuse("the prepared result is not based on the target it names")
        if self.content(repository, head) != prepared["content"]:
            _refuse("the prepared result's path and mode set changed")
        return dict(prepared, content=dict(prepared["content"]))

    # -- advancing the dedicated target --------------------------------------

    def revision(self, repository, reference):
        """What the dedicated target's configured reference holds NOW."""
        return _object_name(
            self._run(read_ref_vector(repository, reference),
                      "target revision read").strip(),
            "the dedicated target's revision")

    def advance(self, repository, *, reference, imported, reviewed):
        """Move the configured reference from the reviewed revision, or refuse.

        THE EXPECTED OLD VALUE IS THE WHOLE SAFETY. A second writer that
        advanced the target between the review and this act loses the swap
        rather than being overwritten, and the refusal is Git's own.
        """
        repository = _path(repository, "the dedicated target repository")
        self._run(advance_ref_vector(repository, reference, imported, reviewed),
                  "target revision advance")
        held = self.revision(repository, reference)
        if held != _object_name(imported, "the imported result"):
            _refuse("the dedicated target's reference did not take the "
                    "imported result")
        return held


def _conflicted(stdout):
    """The conflicted paths the reconciliation reported, as a sorted set.

    ITS OWN SECTIONS, READ AS SECTIONS. The `-z` answer is the merged tree,
    then the conflicted-file records, then an EMPTY field, then informational
    messages -- so the paths are everything between the tree and that
    separator, and `--name-only` is what makes those records the bare paths.
    Reading past the separator would collect the tool's prose as a path.
    """
    held = set()
    for one in stdout.split("\x00")[1:]:
        if one == "":
            break
        candidate = one.strip()
        if candidate and not candidate.startswith("/") \
                and ".." not in candidate.split("/"):
            held.add(candidate)
    return sorted(held)
