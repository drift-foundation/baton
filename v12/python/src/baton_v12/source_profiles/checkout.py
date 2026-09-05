"""Turning a read-only mount into somewhere the worker may work.

W71917. Two profiles, one boundary, and no inference in either of them.

THE COPY-SAFETY RULE, because it is the whole of why the Git plan is three
arguments longer than the obvious one. `git clone` from a path on the same
filesystem takes its "local" shortcut and HARDLINKS the object files instead of
copying them -- which is fast, and which makes the workspace's objects the very
same inodes as the read-only mount's. Two names for one object where one name
is somebody else's material is precisely the aliasing the read-only bind exists
to prevent: a worker that later repacked, pruned or gc'd its clone would be
operating on inodes inside the nominated source.

`--no-hardlinks` is the whole fix and it is not optional here, so it is
composed rather than accepted as an operand. `--no-local` is composed beside it
for the case the shortcut is taken by a different route -- a `file://` spelling
disables the shortcut, a bare path takes it, and a plan that depended on which
spelling a caller used would be a plan that is copy-safe by accident.

THE DECLARED BASE IS CHECKED OUT AND THEN CONFIRMED, NOT MERELY LOOKED UP.
The assignment declares an object name; the plan puts the worktree AT that
commit and then asks the worktree which commit it is on.

That is a correction, and the shape it replaces is worth stating because it
looked right. W71917 run7 review [P1]: the plan was `clone` followed by
`rev-parse --verify <base>^{commit}`, and neither of those checks anything out
-- `clone` takes the SOURCE'S CURRENT HEAD, and `rev-parse` proves only that
the object is PRESENT. A source whose HEAD had moved on while still containing
the declared commit satisfied both, and the worker edited the wrong revision
with nothing in the plan able to notice. `checkout --detach` makes the worktree
the commit; `rev-parse --verify HEAD` reports which commit that turned out to
be, and the plan carries the value it must equal.

Nothing here decides what to DO about a failed step; that is a disposition, and
a plan composer that took dispositions would be the second decision-maker this
separation exists to avoid. The plan says what to run and what the answer must
be, and the party that runs it owns the failure.

AND NOTHING HERE READS THE MOUNT. A plan is composed from the profile word and
the declared base, both of which arrive in the assignment. This module never
looks for a repository, never probes for version-control metadata, and cannot
be asked to: `checkout_plan` is given the profile rather than discovering it,
because discovering it is the inference the ruling removed from the manager and
re-adding it one package over would put it straight back.
"""

import re

__all__ = ["BASE_KINDS", "CHECKOUT_NAME", "GENERIC_PROFILE", "GIT_PROFILE",
           "PROFILES", "checkout_plan", "check_declared_base", "clone_vector",
           "detach_vector", "verify_vector"]

# THE TWO PROFILE WORDS, and they live HERE rather than in the manager. The
# manager carries this word through the manifest as bounded opaque text and
# compares it against nothing; this is the party that consumes it, so this is
# the party that may know what the values are.
GENERIC_PROFILE = "generic"
GIT_PROFILE = "git"
PROFILES = (GENERIC_PROFILE, GIT_PROFILE)

# Where a Git profile's clone lands INSIDE the writable workspace. A fixed name
# for the reason every other fixed path in this delivery is fixed: a checkout
# whose location a caller could vary is a checkout the rest of the turn has to
# be told about, and a directory beside the attempt's result root is somewhere
# the worker already may write.
CHECKOUT_NAME = "checkout"

# The two object-name widths Git actually has. Both are accepted and NEITHER is
# converted into the other: a sha1 name under a sha256 repository is a
# different object namespace rather than a shorter digest, and a composer that
# padded or truncated would produce a verification that passes against the
# wrong object.
BASE_KINDS = {40: "sha1", 64: "sha256"}

_OBJECT = re.compile(r"\A[0-9a-f]+\Z")


class ProfileRefusal(Exception):
    """This package's own refusal.

    NOT `ContractRefusal`, deliberately. That type belongs to the manager's
    contracts layer, and importing it here would make the profile package
    depend on the very slice the separation exists to keep it out of. A caller
    that wants one vocabulary catches this and raises its own; a caller that
    imported the manager to catch a profile error would have imported the
    manager.
    """


def check_declared_base(declared):
    """The base revision the assignment DECLARED, as a name and nothing more.

    LOWER-CASE HEX AT ONE OF THE TWO REAL WIDTHS. An abbreviated name is
    refused rather than expanded: abbreviation is resolved against a
    repository, so accepting one here would make this composer ask the mount a
    question -- and the answer would decide which object gets verified, which
    is the verification deciding its own subject.

    UPPER CASE IS REFUSED FOR THE REASON `oci` REFUSES IT IN AN IMAGE DIGEST:
    it is the same object and a different string, so two spellings of one base
    are two bases to every comparison downstream.
    """
    if type(declared) is not str or not declared:
        raise ProfileRefusal(
            f"a declared base revision is non-empty text; this is "
            f"{type(declared).__name__}")
    if not _OBJECT.match(declared):
        raise ProfileRefusal(
            f"a declared base revision is lower-case hexadecimal; "
            f"{declared!r} is not")
    if len(declared) not in BASE_KINDS:
        raise ProfileRefusal(
            f"a declared base revision is a full object name -- "
            f"{' or '.join(str(one) for one in sorted(BASE_KINDS))} "
            f"characters -- because an abbreviation is resolved against a "
            f"repository rather than named; this is {len(declared)}")
    return declared


def clone_vector(place, into):
    """The closed argv that clones a read-only mount into the workspace.

    `--no-hardlinks` AND `--no-local`, both composed and neither an operand.
    See the module note: the local shortcut hardlinks objects, and a hardlink
    into the nominated source is the aliasing the read-only bind exists to
    prevent.

    `--no-checkout` is NOT composed. A profile that cloned without a working
    tree would hand the worker a repository it has to check out itself, which
    is the same act one step later and with the copy-safety rule no longer
    applied to it.
    """
    return ["git", "clone", "--no-hardlinks", "--no-local",
            _path(place, "a mounted source"), _path(into, "a checkout")]


def detach_vector(into, *, declared):
    """The closed argv that makes the worktree BE the declared base.

    W71917 run7 review [P1] is why this step exists at all. The plan used to be
    clone-then-`rev-parse`, and neither of those checks out anything: `clone`
    checks out the SOURCE'S CURRENT HEAD, and `rev-parse --verify` proves only
    that the named object is present in the repository. A source whose HEAD had
    moved on -- or sat on another branch -- while still containing the declared
    commit satisfied both commands, and the worker then edited the wrong
    revision with nothing in the plan able to notice.

    `--detach` RATHER THAN A BRANCH. The worker is not continuing anyone's
    line of development; it is being placed at one exact commit, and a branch
    name would be a second thing that could move. A detached HEAD is the
    honest spelling of "this worktree is this commit".

    `^{commit}` IS KEPT HERE TOO, for `verify_vector`'s old reason: it makes a
    tag or a tree of the same name a failure rather than a checkout of
    something that is not the declared commit.
    """
    return ["git", "-C", _path(into, "a checkout"), "checkout", "--detach",
            f"{check_declared_base(declared)}^{{commit}}"]


def verify_vector(into):
    """The closed argv that asks a clone WHICH COMMIT IT IS ACTUALLY ON.

    THE SUBJECT CHANGED WITH THE DEFECT. This used to ask whether the declared
    base was present, which a repository can answer yes to while its worktree
    is at some other commit entirely. It now asks for the ACTIVE HEAD, and the
    plan carries the value that answer has to equal -- so the check is an
    equality against what the assignment declared rather than an existence
    question that a superset satisfies.

    `--verify` keeps absence a non-zero status rather than an empty line on
    standard output; a detached HEAD is still a resolvable ref, so the vector
    is unchanged in shape.

    `-C` RATHER THAN A WORKING DIRECTORY. The clone's location is part of the
    question, so it is in the vector where a reader can see it, instead of in
    process state a caller sets separately and this composer cannot check.
    """
    return ["git", "-C", _path(into, "a checkout"), "rev-parse", "--verify",
            "HEAD"]


def checkout_plan(place, into, *, profile, declared=None):
    """The whole plan for one profile: what to run, in order, and why.

    ONE FUNCTION FOR BOTH PROFILES, because the boundary is the same one. The
    generic profile's plan is empty and its source root is the MOUNT ITSELF;
    the Git profile's plan is two vectors and its source root is the checkout
    inside the workspace. Neither profile inspects the mount to decide which
    it is -- the assignment said.

    A DECLARED BASE IS REQUIRED FOR THE GIT PROFILE AND REFUSED FOR THE
    GENERIC ONE, and the second half matters as much as the first. A generic
    profile carrying a base revision is an assignment that meant to ask for a
    version-controlled checkout and did not say so; accepting it would deliver
    the generic boundary while its author believed a base had been verified.
    """
    if profile not in PROFILES:
        raise ProfileRefusal(
            f"{profile!r} is not a source profile; this package consumes "
            f"{' and '.join(PROFILES)}")
    place = _path(place, "a mounted source")
    into = _path(into, "a workspace")
    if profile == GENERIC_PROFILE:
        if declared is not None:
            raise ProfileRefusal(
                "a generic profile declares no base revision; a base is a "
                "version-control fact, and an assignment that names one while "
                "asking for the generic boundary would believe a verification "
                "had happened that this profile never performs")
        # THE MOUNT IS THE SOURCE ROOT. Nothing is copied into the workspace,
        # which is the generic boundary's whole content: the worker reads the
        # read-only mount in place and writes only what it produces.
        return {"profile": GENERIC_PROFILE, "source_root": place,
                "workspace": into, "steps": ()}
    if declared is None:
        raise ProfileRefusal(
            "a git profile verifies the base revision the assignment "
            "declared, and this one declares none; a checkout nobody can "
            "check against a base is a copy of whatever the mount happened "
            "to hold")
    checkout = f"{into.rstrip('/')}/{CHECKOUT_NAME}"
    base = check_declared_base(declared)
    return {"profile": GIT_PROFILE, "source_root": checkout,
            "workspace": into,
            "base": base,
            "base_kind": BASE_KINDS[len(declared)],
            # THE ORDER IS THE CONTENT. Cloning before checking out is what
            # makes both later acts questions about the worker's OWN copy
            # rather than about the mount; either one against the mount would
            # be this package reading the read-only tree, which is the thing
            # the boundary took away from the manager and did not hand to
            # anybody else.
            #
            # A STEP IS AN ARGV AND WHAT ITS OUTPUT MUST BE. W71917 run7
            # review [P1]: exit status alone cannot express "the worktree is at
            # this exact commit", because the command that answers which commit
            # that is succeeds whatever the answer. The expectation travels
            # with the step so the party that runs it compares rather than
            # interprets, and a step with nothing to compare says so with
            # `None` instead of leaving the reader to infer it.
            "steps": ({"argv": tuple(clone_vector(place, checkout)),
                       "expect_stdout": None},
                      {"argv": tuple(detach_vector(checkout,
                                                   declared=base)),
                       "expect_stdout": None},
                      {"argv": tuple(verify_vector(checkout)),
                       "expect_stdout": base})}


def _path(place, what):
    """One absolute, canonical path, with no separator the tool would eat.

    A leading `-` IS REFUSED, and it is not paranoia: every vector here is a
    command line, and a path beginning with a dash is read as an option by the
    program that receives it. The check belongs at the composer because the
    composer is what puts the value in argument position.
    """
    if type(place) is not str or not place:
        raise ProfileRefusal(f"{what} is non-empty text; this is "
                             f"{type(place).__name__}")
    if "\x00" in place:
        raise ProfileRefusal(f"{what} carries a NUL byte")
    if not place.startswith("/"):
        raise ProfileRefusal(f"{what} is an absolute path; {place!r} is not")
    if ".." in place.split("/"):
        raise ProfileRefusal(
            f"{what} is canonical; {place!r} traverses with `..`, which asks "
            f"this composer to compute a path rather than name one")
    if place != "/" and place.endswith("/"):
        raise ProfileRefusal(
            f"{what} carries a trailing separator; {place!r} is one spelling "
            f"of a path this plan names in two places")
    return place
