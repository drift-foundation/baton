"""ASSIGNMENT-PRIVATE WORKSPACES: where staged input sits, where a worker may
write, and what cleanup is allowed to remove.

W6631 built this component, and W15232 removed its acquisition half. What
remains is the generic manager-owned part of that Work, and the module contract
is written around it rather than around the operations that are gone.

FOUR THINGS THIS COMPONENT DOES:

  - `assignment_workspace` allocates two roots private to one assignment --
    `inputs`, read-only evidence, and `workspace`, the only writable tree. They
    are SIBLINGS rather than nested: a worker that could write into its own
    inputs would make the seal over them describe a tree that has since
    changed.
  - `directory_manifest` MEASURES a tree into the frozen `contentManifest`.
    Every entry is opened once with `O_NOFOLLOW`, and both its bytes and its
    size come from that one descriptor -- so a replacement between the check
    and the read is a file this component never sees rather than one it
    describes wrongly. Only bounded regular files; entries sorted bytewise,
    which is the order the tree digest is taken over and the order §12 rule 6
    checks.
  - containment, so a path that leaves the root it claims to be under is
    refused before anything opens it.
  - `discard_workspace` removes ONLY what this component created, including the
    read-only trees it made read-only, and says what it removed.

WHAT THIS COMPONENT NO LONGER DOES, and the ruling that ended it. The
2026-08-25 artifact-neutral supersession states that the Worker Manager "does
not understand Git, import bundles, resolve commits, prepare checkouts, or
choose a source-acquisition operation": it receives an ALREADY STAGED
read-only directory and its generic integrity envelope, and populating that
directory is a source stager's job, outside this package.

So the acquisition operations W6631 put here -- a repository port, and the
operations that delivered a version-controlled or copied source -- are gone
rather than re-homed, because re-homing requires an owner and the ledger has
none. Nothing here interprets an acquisition descriptor or names one.

NOR DOES IT ALLOCATE PRIVATE CAPACITY FOR ONE. There was a third root holding
version-control metadata, and every assignment got one whether its staged input
was a directory, an archive, a database snapshot, media or a format nobody has
written yet. Private ephemeral space is generic runtime capacity, not protocol
vocabulary this manager provisions; a stager or driver that needs it allocates
its own under an explicit owner.

The reasoning that was superseded lives in
`work/records/2026/08/finding-v12-artifact-neutral-source-stager/` and in
W6631's own record. It does not need to survive as the live module contract.
"""

import contextlib
import errno
import fcntl
import json
import os
import stat
from types import MappingProxyType

# W15232: `check_content_manifest` and `validate_fragment` went with the
# acquisition half. They were how this module READ a `gitSource` or
# `directorySource` descriptor and compared a claimed manifest against a
# measured one -- both acts of interpreting an acquisition contract, and
# neither one a manager that receives an already staged directory performs.
from ..contracts import (ContractRefusal, canonical_bytes, check_input_pair,
                        digest, digest_of_bytes)
from ..contracts.errors import label_of, name_value
from . import boundaries

# S_IFMT and S_IFREG, written out. The `stat` module is not on this package's
# declared standard-library allowlist and this is the only thing it would be
# imported for -- two constants a reader can check against `man 2 stat` are a
# smaller dependency than a module, and the alternative was widening a list a
# case exists to keep narrow.
_FILE_KIND = 0o170000
_REGULAR = 0o100000

# W15232: THE ACQUISITION HALF IS GONE, and what is left is the half the
# artifact-neutral ruling leaves with this manager.
#
# W6631 built `GitPort`, `materialize_git_source` and
# `materialize_directory_source` here. The 2026-08-25 supersession removed the
# duty they perform from the core manager entirely -- "the Worker Manager does
# not understand Git, import bundles, resolve commits, prepare checkouts, or
# choose a source-acquisition operation" -- and populating the staged input
# directory became a SOURCE STAGER's job, outside this package.
#
# REMOVED RATHER THAN RE-HOMED, and the difference was decided by looking. The
# assignment permits re-homing only behind an ALREADY PINNED stager or driver
# owner; the ledger has no such Work and the records name no such boundary, so
# inventing one to keep the code would have been inventing the second
# acquisition contract this Work exists to avoid. The behaviour is recoverable
# from W6631's own record and history if a stager is ever specified; what is
# not recoverable is the confusion of a manager that still exports it.
#
# WHAT STAYS IS GENERIC AND STILL THIS MANAGER'S: assignment-private paths, the
# read-only staged input tree, the measured `contentManifest` over a directory,
# containment, and cleanup. None of them knows where the bytes came from.
__all__ = ["INPUT_MANIFEST", "ASSIGNMENT_MANIFEST", "MAX_ENTRIES",
           "HOME_ENTRIES", "ROOT_NAMES", "WORKSPACE_DIR",
           "adopt_workspace_group", "check_workspace_group",
           "prove_workspace_group", "WorkspaceGroup", "AllocatedRoots",
           "WORKSPACE_GROUP_KEY", "CONFIGURE_OPERATION",
           "configure_workspace_group", "configured_workspace_group",
           "WorkspaceIdentity", "configured_workspace_identity",
           "identity_for", "declared_identity_mapping",
           "SUPPORTED_IDENTITY_MAPPING",
           "PERMISSION_ACTS", "establish_line_access", "prove_line_integrity",
           "WORKSPACE_STORAGE_KEY", "STORAGE_CONFIGURE_OPERATION",
           "WorkspaceStorage", "check_workspace_storage",
           "configure_workspace_storage", "configured_workspace_storage",
           "MAX_BYTES", "MAX_DEPTH", "READ_ONLY_DIR", "READ_ONLY_FILE",
           "MOUNTINFO", "mount_table", "mount_points",
           "assignment_workspace", "compose_input_root", "copied_manifest",
           "adopted_assignment_workspace", "line_assignment_workspace",
           "directory_manifest", "discard_execution_roots", "discard_tree",
           "discard_workspace",
           "refuse_if_held",
           "read_input_root"]

# THE KERNEL'S OWN MOUNT TABLE, read rather than inferred.
#
# W71917 run7 review [P0]: cleanup decided "this is a mount" by comparing
# `st_dev` with the tree's root, and a bind mount from the SAME filesystem
# keeps the bound directory's device number. A source bind-mounted from the
# same disk therefore passed that test and its contents were walked and
# unlinked -- the data-loss path the nominated-source boundary exists to make
# impossible.
#
# There is no portable device-number answer to "is this a mount point": the
# kernel's identity for a mount is its mount ID, and `os.stat` does not expose
# one. `/proc/self/mountinfo` does, and it is the same file
# `source_boundary.filesystem_of` already reads to say what a path is stored
# on -- so the reader lives HERE, in the lower module, and that one imports it
# rather than the two keeping separate copies of the escape rules.
MOUNTINFO = "/proc/self/mountinfo"

_ESCAPES = (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"),
            ("\\134", "\\"))


def _unescaped(field):
    # THE BACKSLASH LAST, deliberately. Decoding it first would let a literal
    # `\134040` -- a backslash followed by the four characters `0`, `4`, `0` --
    # become `\040` and then a space, which is a path this build made up.
    for written, meant in _ESCAPES[:-1]:
        field = field.replace(written, meant)
    return field.replace(*_ESCAPES[-1])


def mount_table(*, what="this manager's mount boundary"):
    """Every live mount as `(point, filesystem_type)`, from the kernel.

    REFUSES RATHER THAN GUESSES. A build that cannot read the table cannot say
    whether a directory it is about to walk is somebody else's mount, and the
    answer this question protects is a recursive delete. An unreadable table is
    therefore a refusal at the caller, never an empty set treated as "no mounts
    here" -- which is exactly the reading that would restore the defect.

    The mount point is field five of the part BEFORE the ` - ` separator, whose
    position varies with the number of optional fields; the type is the first
    field after it. Splitting on the separator is how the kernel documents the
    format and is why this does not index by column.

    `what` IS A PUBLIC OPERAND AND IS BOUNDED BEFORE IT CAN REACH A MESSAGE.
    W71917's sixth review [P1]: this is an exported operation, so "every call
    site in this package passes a literal" is a fact about this package and not
    about what a caller may hand it -- and the refusal below interpolated the
    object directly, so a value whose `__format__` raised escaped as a
    `RuntimeError` instead of the closed refusal this build promises. It is
    `label_of`'d here, which is exactly what `source_boundary.check_disk_backed`
    already does with the same noun.
    """
    what = label_of(what)
    try:
        with open(MOUNTINFO, "r", encoding="utf-8") as reading:
            raw = reading.read()
    except OSError as failure:
        _refuse(f"this build cannot read {name_value(MOUNTINFO)} "
                f"({type(failure).__name__}), so it cannot say which "
                f"directories are mounts; {what} is not decided by guessing")
    found = []
    for line in raw.splitlines():
        separated = line.split(" - ", 1)
        if len(separated) != 2:
            continue
        before = separated[0].split(" ")
        after = separated[1].split(" ")
        if len(before) < 5 or not after:
            continue
        found.append((_unescaped(before[4]), after[0]))
    return found


def mount_points(*, what="this manager's mount boundary"):
    """The resolved mount points alone, as a set ready to compare against.

    RESOLVED, because the walk compares real paths: a mount point reached
    through a symbolic link is the same mount, and a set keyed on the kernel's
    spelling would miss it.

    ITS OWN DOOR OWNS ITS OWN NOUN. This forwards to `mount_table`, which
    bounds it again -- and that is not a redundancy worth removing: this is a
    separate exported operation, so a caller reaching it is at a boundary of
    its own, and `label_of` is idempotent over an already-bounded label.
    """
    what = label_of(what)
    return {os.path.realpath(point) for point, _kind in mount_table(what=what)}

# THE TWO MANAGER-AUTHORED PROTOCOL DOCUMENTS, at the names the contract fixes
# (§7.0). A path a manifest could vary is a path a runtime can be pointed at
# wrongly, so these are constants here for the same reason they are constants
# in the worker.
INPUT_MANIFEST = "input.json"
ASSIGNMENT_MANIFEST = "assignment.json"

# The frozen contract's own ceilings, so a manifest this component builds is one
# `contentManifest` can hold rather than one it would refuse after the work was
# done. `maxItems` on the entry array is 100,000; the byte total is the frozen
# safe-integer bound, and this component's own limit is far below it because a
# source larger than this is a configuration mistake rather than a workload.
# A protocol document this component reads back is a file from outside this
# call, so its size is not this function's decision and the bound has to be.
# The worker applies the same ceiling on the same two documents.
MAX_MANIFEST_BYTES = 4 * 1024 * 1024

MAX_ENTRIES = 100_000
MAX_BYTES = 4 * 1024 * 1024 * 1024
# Depth is bounded for the same reason the canonicalizer bounds it: a walk with
# no limit is a walk somebody else decides the cost of.
MAX_DEPTH = 64

# Read-only, and OWNER-ONLY. A delivered source is evidence: the worker reads
# it and nothing writes it again, and the mode says so on disk rather than in a
# comment. The execute bit stays on directories because a directory nobody may
# traverse is a directory nobody may read either.
# WORLD-READABLE, AND THAT IS THE POINT OF THE MODE RATHER THAN A RELAXATION
# OF IT.  W33935: these were 0o400 and 0o500 -- owner-only -- while the
# execution container runs as the fixed uid 65532 and the manager writes as
# whoever it happens to be.  Measured inside the real composed runtime, both
# `/input` documents were uid 1000 mode 0400 and BOTH READS FAILED WITH EACCES,
# so no worker could consume either of the two documents it is required to
# read.  The sibling launch delivery was 0o444 and readable, which is what
# demonstrated the shape rather than the diagnosis.
#
# WHAT MAKES THIS SAFE IS NOT THE MODE.  A worker cannot write here because the
# root is bind-mounted READ-ONLY -- the same probe got `EROFS` writing to
# `/input` itself, from the bind and not from any permission -- and it cannot
# reach the root through any other path because nothing else is mounted.  The
# mode's job is the HOST side: it says on disk that these bytes are finished,
# so this manager's own later mistake cannot rewrite the evidence a claim was
# made against.  Read permission was never part of that job, and taking it away
# protected nothing while breaking the one consumer.
#
# `launch.READ_ONLY_FILE` and `launch.READ_ONLY_DIR` are the same two values
# for the same reason, and `test_input_delivery` holds the two components to
# each other so a future edit cannot move one without the other.
READ_ONLY_FILE = 0o444
READ_ONLY_DIR = 0o555

# The two roots a container may be given, and every entry the assignment home
# holds.  They are different lists for a reason: `custody` is the material a
# worker must never reach after its freeze, and the two credential places are a
# bearer it is handed at one fixed path instead -- so none of the three is
# mountable, and all three are siblings under one home that has to be CLOSED
# once they exist.
# THE ONE WRITABLE ROOT'S EXACT MODE.  W33936: the workspace was left at
# whatever the process umask produced -- 0775 on the host this was measured on,
# and 0700 under the ordinary service umask 077.  Neither is a decision.
#
# 0770: OWNER AND GROUP MAY WRITE, AND NOBODY ELSE MAY DO ANYTHING.
#
# The narrowing is safe now and was not before, and the difference is the
# ruling: the execution container is given the configured workspace GROUP as a
# supplementary group, so it reaches this root through the group bits rather
# than through `other`.  An earlier cut narrowed to 0770 while the container
# held no share in the group, and the probe refuted it -- the worker lost read
# and traverse as well.  Narrowing belongs in the same change as the group, and
# this is that change.
#
# The superseded text below is kept as decision history.
#
# 0775 is EXACTLY WHAT THE UMASK HAPPENED TO PRODUCE on the host this was
# measured on, and that is the point: it is now a decision instead of an
# accident, and under the ordinary service umask 077 it no longer silently
# becomes 0700.
#
# NOT 0770, WHICH I TRIED FIRST AND THE PROBE REFUTED.  Dropping `other` looks
# like the narrower answer, and while the container still runs as 65532 with no
# share in this group it takes away the worker's READ and TRAVERSE as well --
# measured, `/workspace` went from `r=T x=T` to `r=F x=F`.  Narrowing to 0770
# belongs with the group wiring, in the same change, because it is only safe
# once the container holds the group.  The group bits here are what that wiring
# will use.
WORKSPACE_DIR = 0o2770

# Review [P0], approver ruling M34630: `02770` EXACTLY, and the setgid bit is
# not decoration.
#
# `0770` gives the group write.  What it does NOT give is the guarantee that
# what the WORKER creates stays in that group -- a container process whose
# primary gid is 65532 creates files owned `65532:65532`, and the manager, which
# is not 65532 and is not in that group, could then not collect the result it
# is required to collect.  Setgid on the directory makes every entry created
# inside it inherit the DIRECTORY's group instead, so the worker writes and the
# manager reads with no widening of anything.  Measured against a real daemon:
# a file the worker created came back `<worker>:<workspace group>`, and a
# directory it created carried the setgid bit onward.
#
# `other` HAS NOTHING, and that is the second half of the same choice.  This
# root is reachable only by its owner and by the one configured group; the
# earlier `0775` gave every process on the host read and traverse over an
# assignment's writable tree, which is authority nobody asked for.


# W33936 review [P1]: THE CONFIGURED GROUP IS A DEPLOYMENT FACT, AND THIS IS
# WHERE IT LIVES.
#
# The defect the review found: every layer took the same raw integer from its
# caller and every layer agreed, so a manager belonging to the configured group
# A and to some unrelated authority-bearing service group B could be handed B
# at allocation and at launch. The workspace was adopted into B, the pre-launch
# proof passed because it compared against the same operand, and `--group-add
# B` was composed. Four checks, one caller-selected value, and nothing to
# reject it with -- `check_workspace_group` can see shape, gid 0 and
# membership, and membership is exactly what B has.
#
# So there is one source of truth now and it is the control store's own
# metadata, written by a deployment act. `os.getgroups()` says what the manager
# CAN use; this says what the deployment SAID to use, and only the second
# authorizes anything.
WORKSPACE_GROUP_KEY = "workspace-group"

# W36540 review [P0]: THE DEPLOYMENT'S WORKSPACE STORE, recorded the same way
# its group is. The custody mint used to take `storage` as an ordinary path, so
# a caller could make a directory holding `attempt-1/workspace`, pass it, and
# be handed a capability over an unrelated host tree. A root a caller can name
# is a root a caller chose -- the same sentence W33936 wrote about the group,
# and the same answer.
WORKSPACE_STORAGE_KEY = "workspace-storage"

# The token that says this object came from the deployment's own record. A
# module-private sentinel rather than a flag, because a flag is something a
# caller can pass.
_MINT = object()


class WorkspaceGroup:
    """The deployment's configured group, as a FROZEN ANSWER.

    A capability rather than an integer, and that is the whole correction. An
    integer is a value any caller can compose; this can only be obtained from
    `configured_workspace_group`, which reads the deployment's own record. So
    the adapter and the run vector do not validate a number a caller supplied
    -- they refuse anything that is not this, and the only way to hold one for
    group B is for the deployment to have configured B.

    The same shape `credentials.Delivery` and `launch.LaunchDelivery` already
    have at this boundary, for the same reason: what crosses is a thing the
    manager made, not data describing one.

    W270664 F2, review 2026-09-26T09:15:26Z: IT ALSO CARRIES THE STORE IT WAS READ
    FROM, and that is what lets allocation participate in the exclusion at all.
    Allocation is the one entry that reached these roots with no way to ask the
    journal -- `assignment_workspace(group, storage, attempt)` has no control operand
    -- and the census under this claim found it has NO product caller to thread one
    through: every call site is a test, a probe or a fixture. So the operand comes
    from the capability that was already required and already minted from this
    manager's own record. Holding a group now means the deployment configured it AND
    names the journal that says so; `store` is not part of the group's IDENTITY, which
    stays the gid, because two reads of one deployment's record are the same group.
    """

    __slots__ = ("gid", "store", "store_place")

    def __init__(self, gid, _minted=None, store=None, store_place=None):
        # MINTED ONLY BY THE READ OF THE DEPLOYMENT'S RECORD, which is what
        # makes this a capability rather than a wrapper. A type any caller can
        # construct would leave the hole exactly where the review found it:
        # the caller supplies group B, every layer type-checks happily, and
        # nothing has consulted what the deployment actually said.
        if _minted is not _MINT:
            _denied("a configured workspace group is obtained from this "
                    "manager's own record of what the deployment configured, "
                    "and is not constructed; a group a caller can mint is a "
                    "group a caller chose")
        object.__setattr__(self, "gid", check_workspace_group(gid))
        object.__setattr__(self, "store", store)
        # THE DATABASE FILE THIS STORE IS A HANDLE ON, captured at mint time --
        # which is the only moment it is certainly readable, because it is read
        # from the store's own connection and a connection belongs to its thread.
        object.__setattr__(self, "store_place", store_place)

    def __setattr__(self, name, value):
        _refuse("a configured workspace group is immutable", code="schema")

    def __repr__(self):
        return f"WorkspaceGroup({self.gid})"

    def __eq__(self, other):
        return isinstance(other, WorkspaceGroup) and other.gid == self.gid

    def __hash__(self):
        return hash(("WorkspaceGroup", self.gid))


class WorkspaceIdentity:
    """The trusted execution identity the manager and the worker BOTH run as.

    W194457, FINDING 2026-09-17. The deployment's answer to "who owns what is
    in an execution workspace", as a frozen capability rather than a pair of
    integers a caller composed -- exactly the shape `WorkspaceGroup` has, for
    exactly the reason it has it.

    WHY IT EXISTS. Initial line provisioning used to hold one descriptor per
    entry and then `fchown`/`fchmod` the whole tree, because the manager
    materialized the line as itself and the worker ran as somebody else. That
    walk is what exhausted `RLIMIT_NOFILE` on a real checkout. Under a SHARED
    identity the tree is already owned by the identity that will use it, so the
    walk has nothing to do -- and the manager can read a `0600` file the worker
    created, which a shared GROUP alone never fixed.

    WHAT IT IS NOT. Shared identity is not isolation. Confinement still comes
    from private mounts, read-only input and review roots, per-assignment
    workspaces and the credential boundary, and nothing here widens any of them.

    THE UID IS THIS MANAGER'S OWN and is not configurable. A uid a caller could
    name is a uid a caller chose; the one trustworthy statement available here
    is who this process actually is. The GID is the deployment's configured
    workspace group, which `configured_workspace_group` already mints.
    """

    __slots__ = ("uid", "gid")

    def __init__(self, uid, gid, _minted=None):
        if _minted is not _MINT:
            _denied("a shared execution identity is obtained from this "
                    "manager's own record of what the deployment configured, "
                    "and is not constructed")
        if type(uid) is not int or type(uid) is bool or uid <= 0:
            _denied("a shared execution identity runs as a non-root user; "
                    "uid 0 is not an execution identity")
        object.__setattr__(self, "uid", uid)
        object.__setattr__(self, "gid", check_workspace_group(gid))

    def __setattr__(self, name, value):
        _refuse("a shared execution identity is immutable", code="schema")

    def __repr__(self):
        return f"WorkspaceIdentity({self.uid}, {self.gid})"

    def __eq__(self, other):
        return (isinstance(other, WorkspaceIdentity)
                and (other.uid, other.gid) == (self.uid, self.gid))

    def __hash__(self):
        return hash(("WorkspaceIdentity", self.uid, self.gid))


def identity_for(group):
    """The shared execution identity behind a minted workspace group.

    THE VECTORS OBTAIN IT HERE rather than being handed a pair. `run_vector`
    and the custody vector already receive the deployment's minted
    `WorkspaceGroup` -- the capability that says which group the deployment
    provisioned -- and the uid half is not a selection at all: it is
    `os.geteuid()`, who this manager actually is. So there is no operand a
    caller could choose, and no signature anywhere has to grow one.

    `configured_workspace_identity` is the same answer from the STORE, for
    callers that hold one; both mint through `WorkspaceIdentity`, so root and a
    malformed group are refused identically.
    """
    if type(group) is not WorkspaceGroup:
        _denied("a shared execution identity is derived from this "
                "deployment's minted workspace group, not from an integer")
    uid = os.geteuid()
    if uid == 0:
        _denied("this manager runs as root, and an execution identity shared "
                "with a worker may not be root; the deployment runs the "
                "manager as the dedicated non-root account it provisions")
    return WorkspaceIdentity(uid, group.gid, _MINT)


# THE SUPPORTED HOST/CONTAINER MAPPING, WRITTEN DOWN RATHER THAN MEASURED.
#
# W194457, owner decision 2026-09-17 (`OWNER-TRUSTED-IDENTITY-20260917.md`).
# Slawomir selected a deliberately configured, trusted arrangement over
# automatic runtime validation, so this is the contract an operator satisfies
# and this manager then TRUSTS. It is documentation with a check attached, not
# a proof:
#
#   THE HOST SIDE. The manager runs as a dedicated non-root account. That
#   account's effective uid is one half of the execution identity and is never
#   an operand -- `identity_for` reads `os.geteuid()`. The account is a member
#   of the deployment's configured workspace group, which is the other half.
#
#   THE CONTAINER SIDE. The engine is configured WITHOUT an id mapping for
#   this deployment: a rootful daemon with no `userns-remap`, or a rootless
#   daemon whose subuid/subgid ranges map this account to itself. Then the
#   `--user <uid>:<gid>` the adapter composes is the same pair on both sides
#   of the boundary, and a file either party creates is owned by the other.
#
#   WHAT IS NOT SUPPORTED, named because a refusal should name a remedy: a
#   daemon that remaps ids for this deployment. `test_worker_entry_engine`
#   measured such a host answering uid 65534 -- the kernel's overflow id -- for
#   a file a container created as 65532. Under a remapping daemon nothing the
#   worker writes can be consumed as this manager's own, and the remedy is an
#   engine setting rather than a manager one. Changing which account the
#   manager runs as is NOT a general fix: the requested container identity is
#   DERIVED from that account, so moving it moves both sides at once.
#
# NOTHING BELOW CLAIMS THIS WAS VERIFIED. The earlier cut of this Work started
# a throwaway container to measure it and the owner superseded that design.
# What replaces it is this paragraph, the cheap declared check below, and
# access failures that name the operation, the path and the errno when the
# arrangement is in fact wrong -- see `_access_failure`.
SUPPORTED_IDENTITY_MAPPING = (
    "this deployment's manager account and its container runtime share one "
    "uid and gid because the engine is configured without an id mapping for "
    "it; the arrangement is deployment configuration this manager trusts "
    "rather than something it measures")


def declared_identity_mapping(identity, declared):
    """Does the composed argv DECLARE exactly the identity that was minted?

    W194457, the owner's "cheap structural configuration check". The expensive
    question -- what the host actually observes for what the runtime creates --
    is the one the owner ruled out asking. This is the cheap one, and it is
    worth asking because it is the failure a change to this module can
    actually introduce: a vector that composes an identity DIFFERENT from the
    one the workspace was created under produces a worker that cannot read its
    own workspace, and the two spellings live in two functions.

    So it compares a STRING the caller is about to hand the engine against the
    minted capability, and refuses anything that is not `uid:gid` exactly.
    It runs no engine, opens no file and makes no claim about mapping.
    """
    if not isinstance(identity, WorkspaceIdentity):
        _denied("a declared execution identity is checked against this "
                "deployment's minted execution identity")
    if not isinstance(declared, str):
        _denied(f"an execution runtime declares its identity as `uid:gid`; "
                f"this start declares {name_value(declared)}")
    parts = declared.split(":")
    if len(parts) != 2 or not all(one.isdigit() for one in parts):
        _denied(f"an execution runtime declares its identity as `uid:gid`; "
                f"this start declares {name_value(declared)}")
    if (int(parts[0]), int(parts[1])) != (identity.uid, identity.gid):
        _denied(f"this start would declare the runtime identity "
                f"{name_value(declared)} while its workspace is created under "
                f"{identity.uid}:{identity.gid}; the manager and the worker "
                f"share ONE configured identity, and a worker asked for a "
                f"different one cannot read or write the workspace it was "
                f"given. {SUPPORTED_IDENTITY_MAPPING}")
    return declared


# THE ERRNOS A WRONG IDENTITY ARRANGEMENT ACTUALLY PRODUCES, so the refusal
# that carries one can say what to look at. Nothing infers a cause from them --
# a `0000` file the worker made is `EACCES` too -- but an operator reading
# "permission denied on a path the worker created" is one sentence from the
# question that matters, and the sentence is cheaper than the probe the owner
# ruled out.
_IDENTITY_ERRNOS = (errno.EACCES, errno.EPERM)


def _access_failure(operation, place, failure, *, what, identity_hint=True):
    """The refusal an ACTUAL access failure gets, with what to act on in it.

    W194457, owner decision 2026-09-17: "Report actual access failures directly
    with actionable operation/path/error context." This is the other half of
    trusting the configuration. The manager does not prove the arrangement in
    advance any more, so when the arrangement is wrong the first symptom is an
    `EACCES` or an `EPERM` on a real path -- and this refusal is then the
    operator's whole diagnostic.

    THE ERRNO IS THE POINT. The refusal this replaces said `OSError` and
    dropped the number, which is exactly why this Work's own incident has its
    cause strongly supported rather than recorded. The operation, the path, the
    errno NAME and the kernel's own sentence for it all survive.
    """
    number = getattr(failure, "errno", None)
    named = errno.errorcode.get(number, "unknown") if number is not None \
        else "unknown"
    spelled = os.strerror(number) if number is not None else "no errno"
    said = (f"{operation} {name_value(place)} "
            f"({type(failure).__name__} {named}: {spelled}); {what}")
    if identity_hint and number in _IDENTITY_ERRNOS:
        said += (f" A permission failure on material the worker created is "
                 f"what an unsupported identity arrangement looks like from "
                 f"here: {SUPPORTED_IDENTITY_MAPPING}. Check the engine's id "
                 f"mapping for this deployment before treating the entry "
                 f"itself as the fault.")
    _denied(said)


def configured_workspace_identity(store):
    """The shared execution identity, minted from what IS rather than what was
    asked for: this manager's effective uid, and the deployment's group."""
    group = configured_workspace_group(store)
    uid = os.geteuid()
    if uid == 0:
        _denied("this manager runs as root, and an execution identity shared "
                "with a worker may not be root; the deployment runs the "
                "manager as the dedicated non-root account it provisions")
    return WorkspaceIdentity(uid, group.gid, _MINT)


# HOW MANY PERMISSION ACTS THE SELECTED PATH PERFORMS, counted so a check can
# assert the shape rather than the duration. W194457: the defect was a count
# proportional to the tree, and "it got faster" is not the property.
PERMISSION_ACTS = {"chown": 0, "chmod": 0}


def _permission_act(kind):
    PERMISSION_ACTS[kind] = PERMISSION_ACTS[kind] + 1


def configure_workspace_group(store, gid):
    """The DEPLOYMENT's act: name the one dedicated workspace group.

    Approver rulings M34630 and M34916 divide this exactly: the deployment
    provisions one dedicated non-authority group and grants this manager
    permission to use it, and this manager never creates or modifies a host
    group. It validates what it is configured with -- and now it also RECORDS
    it, so a later caller cannot substitute another group the manager happens
    to hold.

    RE-CONFIGURING TO A DIFFERENT GROUP IS REFUSED rather than accepted. A
    manager already holding workspaces adopted into one group cannot be told
    the group is now another one without those roots becoming unreachable to
    the workers they were prepared for; a deployment that means to change it
    initializes a fresh store, which is the same clean-boundary rule the schema
    version is under. Re-affirming the SAME group is a no-op and commits.
    """
    from .store import manager_signature
    gid = check_workspace_group(gid)
    # THE JOURNAL, not the projection. Review [P1]: this asked `meta` whether
    # the manager was already configured, so a projection edit that made the
    # record disagree with the deployment's act also unlocked reconfiguring to
    # whatever the editor had put there. The committed operation is the one
    # account of this that a caller holding the store cannot rewrite without
    # the collision the journal is for.
    held = _committed_workspace_group(store)
    if held is not None and held != gid:
        _denied(f"this manager is already configured with workspace group "
                f"{held} and is being told to use {gid}; workspaces already "
                f"adopted into the first group would become unreachable to the "
                f"workers they were prepared for, so a changed group is a "
                f"fresh store rather than a reconfiguration")
    signature = manager_signature("workspace-group.configure", {"gid": gid})

    def act(connection):
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (WORKSPACE_GROUP_KEY, str(gid)))
        return {"workspace_group": gid}

    return store.transact("workspace-group.configure",
                          "workspace-group.configure", signature, act)


def _configured_gid(store):
    found = store._connection.execute(
        "SELECT value FROM meta WHERE key = ?",
        (WORKSPACE_GROUP_KEY,)).fetchone()
    if found is None:
        return None
    # ADOPTED, not trusted. This is a persisted value this process did not
    # write, and a store hand-edited to say `root` is exactly what the read
    # has to refuse rather than pass on.
    return check_workspace_group(int(boundaries.text(
        found["value"], "the configured workspace group's record"))
        if str(found["value"]).lstrip("-").isdigit() else found["value"],
        what="the recorded workspace group")


CONFIGURE_OPERATION = "workspace-group.configure"


def _committed_workspace_group(store):
    """The DEPLOYMENT'S OWN ACT, read out of the journal.

    Review [P1]: `configured_workspace_group` read `meta` and nothing else, so
    the capability was minted from a MUTABLE PROJECTION. A caller holding the
    store could leave the committed operation untouched, edit one row of
    `meta` to a second group it happened to hold, and be handed a capability
    for that group -- which then adopts workspaces and crosses `--group-add`.
    That is the arbitrary-held-service-group defect this Work exists to close,
    surviving in a second place.

    So the journal is the authority and `meta` is a cache of it. Three things
    are asked of the committed row, in the order that makes each meaningful:

    THE KIND, because a row of some other kind sitting at this identity is not
    a configuration however well its result reads.

    THE ANSWER THROUGH `replay`, so the committed result is decoded by the
    journal's own reader against the recorded signature rather than adopted as
    stored bytes -- and so a refused configuration is reproduced as the
    refusal it was rather than read past.

    THE SIGNATURE RECOMPUTED from the gid the answer names. The signature is a
    deterministic function of the operands, so a `result` column edited in
    place to name another group no longer agrees with the signature that was
    written beside it, and the disagreement is visible without a second copy
    of the value.
    """
    from .store import manager_signature
    held = store.operation_record(CONFIGURE_OPERATION)
    if held is None:
        return None
    if held["kind"] != CONFIGURE_OPERATION:
        _refuse(f"the journalled operation {CONFIGURE_OPERATION!r} is recorded "
                f"as kind {name_value(held['kind'])}; a row of another kind is "
                f"not this deployment's workspace group configuration",
                code="schema")
    _, committed = store.replay(CONFIGURE_OPERATION, held["signature"],
                                kind=CONFIGURE_OPERATION)
    answer = boundaries.document(committed,
                                 "the committed workspace group configuration",
                                 required=("workspace_group",))
    gid = check_workspace_group(answer["workspace_group"],
                                what="the committed workspace group")
    if held["signature"] != manager_signature(CONFIGURE_OPERATION,
                                              {"gid": gid}):
        _refuse(f"the journalled workspace group configuration names group "
                f"{gid}, which is not the group its recorded signature was "
                f"written for; the committed answer and the operands it was "
                f"committed under disagree", code="schema")
    return gid


def configured_workspace_group(store):
    """The deployment's frozen answer, or a refusal.

    THE ONLY WAY TO OBTAIN A `WorkspaceGroup`. Allocation and launch consume
    this; nothing else mints one, which is what makes "the configured group"
    a fact about the deployment rather than about whoever called.

    THE TWO ACCOUNTS MUST AGREE. The committed operation is the deployment's
    act and `meta` is this manager's projection of it, and a capability is
    minted only when they name the same group. A disagreement is `integrity/
    schema` and NOT a repair: this manager cannot say which of the two
    describes the deployment, and picking the journal silently would let an
    edit that should have been refused become an edit that was tolerated.
    Every direction of disagreement fails closed, including a projection that
    is merely absent -- a record this build cannot cross-check is not a record
    it will mint a group grant from.
    """
    projected = _configured_gid(store)
    committed = _committed_workspace_group(store)
    if projected is None and committed is None:
        _denied("this manager has no configured workspace group; the "
                "deployment provisions one dedicated non-authority group and "
                "records it before any execution workspace is allocated, and "
                "a group inferred from what the manager happens to hold is "
                "not a workspace grant")
    if committed is None:
        _refuse(f"this manager's record names workspace group {projected} with "
                f"no committed configuration behind it; a projection nobody "
                f"configured is not a deployment's act", code="schema")
    if projected is None:
        _refuse(f"the deployment configured workspace group {committed} and "
                f"this manager's record of it is gone; a configuration this "
                f"build cannot cross-check is not one it mints a group grant "
                f"from", code="schema")
    if projected != committed:
        _refuse(f"this manager's record names workspace group {projected} and "
                f"the deployment's committed configuration names {committed}; "
                f"a group the record was edited to name is not a group the "
                f"deployment configured", code="schema")
    # W270664 F2: THE STORE THAT ANSWERED IS BOUND IN. It is this manager's own record
    # that just proved the group, so it is the journal the group's own allocations ask.
    return WorkspaceGroup(committed, _MINT, store=store,
                          store_place=_database_place(store))


class WorkspaceStorage:
    """The deployment's configured workspace STORE, as a frozen answer.

    W36540 review [P0]. The exact shape `WorkspaceGroup` has, for the exact
    reason: a path is a value any caller can compose, and the custody mint was
    deriving its mount source from one. A caller could create an ordinary
    manager-owned directory holding `attempt-1/workspace`, hand it over as
    `storage`, and receive a valid custody root over an unrelated host tree --
    every structural check passing, because the structure is reproducible with
    two `mkdir`s.

    This can only be obtained from `configured_workspace_storage`, which reads
    the deployment's own record. Holding one for root B means the deployment
    configured B.

    WHY ALLOCATION IS NOT ALSO CHANGED, said plainly rather than left as an
    asymmetry a reader has to explain to themselves. `assignment_workspace`
    still takes a path: it is the DEPLOYMENT'S OWN allocation act, and the
    review's requirement is about the custody MOUNT. A caller may still
    allocate a workspace wherever it may already write; what it can no longer
    do is have a container mounted on one. Custody is confined to the
    configured store, and allocating elsewhere grants no custody there.
    """

    __slots__ = ("place",)

    def __init__(self, place, _minted=None):
        if _minted is not _MINT:
            _denied("a configured workspace store is obtained from this "
                    "manager's own record of what the deployment configured, "
                    "and is not constructed; a store a caller can mint is a "
                    "store a caller chose")
        object.__setattr__(self, "place", check_workspace_storage(place))

    def __setattr__(self, name, value):
        _refuse("a configured workspace store is immutable", code="schema")

    def __repr__(self):
        return f"WorkspaceStorage({self.place!r})"

    def __eq__(self, other):
        return isinstance(other, WorkspaceStorage) and other.place == self.place

    def __hash__(self):
        return hash(("WorkspaceStorage", self.place))


def check_workspace_storage(place, *, what="the configured workspace store",
                            physical=True):
    """One absolute, manager-owned, unaliased directory, validated and owned.

    ASKED WITH `lstat`, never `isdir`. `os.path.isdir` follows a symlink and
    answers about its target, which is the question an attacker gets to choose
    the answer to; the entry itself is what this is about.

    NO DEFAULT AND NO INFERENCE, on the rule the group is already under: a
    store guessed from where this process happens to be running is not a
    deployment's decision.
    """
    # A LITERAL LABEL AT THE OWNER, and it has to be one. The boundary
    # inventory attributes a crossing by the label written at the site, so a
    # variable there is a crossing it cannot key -- and it raises rather than
    # guessing, which stopped the whole package's scan from producing any
    # verdict at all. `what` stays the caller's context word for the refusal
    # prose below, where it reads correctly and decides nothing.
    boundaries.text(place, "the configured workspace store")
    if not os.path.isabs(place):
        _refuse(f"{what} is an absolute path; {name_value(place)} is not",
                code="path")
    if os.path.normpath(place) != place.rstrip("/") or place != place.rstrip("/") and place != "/":
        _refuse(f"{what} is a canonical path with no traversal or trailing "
                f"separator; {name_value(place)} is not", code="path")
    if not physical:
        # W270664 F2: THE LEXICAL HALF ALONE, FOR A READER UNDER A DATABASE
        # LOCK, and it is never how a store is obtained.
        #
        # Everything above is a decision about the STRING and reaches nothing;
        # everything below asks the filesystem, which is exactly what owner
        # 270664 forbids while a write lock is held. `recorded_storage_place`
        # is the only caller, it passes a place this same function has ALREADY
        # validated physically outside the lock, and it requires the two
        # database accounts to still name that exact place. So the physical
        # answer is not skipped here -- it was taken earlier, on the same
        # bytes, and is being rebound rather than retaken.
        return place
    try:
        held = os.lstat(place)
    except OSError:
        _refuse(f"{what} {name_value(place)} is not a directory this manager "
                f"can see", code="path")
    if stat.S_ISLNK(held.st_mode) or not stat.S_ISDIR(held.st_mode):
        _refuse(f"{what} {name_value(place)} is not a directory this manager "
                f"created: a link at that name is a store somebody else chose",
                code="path")
    if held.st_uid != os.getuid():
        _refuse(f"{what} {name_value(place)} is owned by uid {held.st_uid} and "
                f"this manager is uid {os.getuid()}; a store this manager does "
                f"not own is not one it allocates attempts under", code="path")
    return place


def configure_workspace_storage(store, place):
    """The DEPLOYMENT's act: name the one workspace store.

    Identical in shape to `configure_workspace_group`, including the rule that
    RECONFIGURING TO A DIFFERENT ROOT IS REFUSED: a manager already holding
    attempts under one store cannot be told the store is now another one
    without every recorded attempt becoming unfindable. Re-affirming the same
    root is a no-op and commits.
    """
    from .store import manager_signature
    place = check_workspace_storage(place)
    # THE JOURNAL, not the projection -- the committed operation is the one
    # account of this a caller holding the store cannot rewrite without the
    # collision the journal is for.
    held = _committed_workspace_storage(store)
    if held is not None and held != place:
        _denied(f"this manager is already configured with workspace store "
                f"{name_value(held)} and is being told to use "
                f"{name_value(place)}; every attempt already allocated under "
                f"the first store would become unfindable, so a changed store "
                f"is a fresh store rather than a reconfiguration")
    signature = manager_signature(STORAGE_CONFIGURE_OPERATION,
                                  {"place": place})

    def act(connection):
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (WORKSPACE_STORAGE_KEY, place))
        return {"workspace_storage": place}

    return store.transact(STORAGE_CONFIGURE_OPERATION,
                          STORAGE_CONFIGURE_OPERATION, signature, act)


STORAGE_CONFIGURE_OPERATION = "workspace-storage.configure"


def _configured_storage(store, *, physical=True):
    found = store._connection.execute(
        "SELECT value FROM meta WHERE key = ?",
        (WORKSPACE_STORAGE_KEY,)).fetchone()
    if found is None:
        return None
    # ADOPTED, not trusted: a persisted value this process did not write, and a
    # store hand-edited to name `/` is exactly what the read has to refuse.
    return check_workspace_storage(found["value"],
                                   what="the recorded workspace store",
                                   physical=physical)


def _committed_workspace_storage(store, *, physical=True):
    """The deployment's own act, read out of the journal.

    The three questions `_committed_workspace_group` asks, in the same order
    and for the same reasons: the KIND, so a row of another kind at this
    identity is not a configuration; the ANSWER THROUGH `replay`, so a refused
    configuration is reproduced as the refusal it was; and the SIGNATURE
    RECOMPUTED, so a `result` column edited in place to name another root no
    longer agrees with the signature written beside it.
    """
    from .store import manager_signature
    held = store.operation_record(STORAGE_CONFIGURE_OPERATION)
    if held is None:
        return None
    if held["kind"] != STORAGE_CONFIGURE_OPERATION:
        _refuse(f"the journalled operation {STORAGE_CONFIGURE_OPERATION!r} is "
                f"recorded as kind {name_value(held['kind'])}; a row of "
                f"another kind is not this deployment's workspace store "
                f"configuration", code="schema")
    _, committed = store.replay(STORAGE_CONFIGURE_OPERATION,
                                held["signature"],
                                kind=STORAGE_CONFIGURE_OPERATION)
    answer = boundaries.document(committed,
                                 "the committed workspace store configuration",
                                 required=("workspace_storage",))
    place = check_workspace_storage(answer["workspace_storage"],
                                    what="the committed workspace store",
                                    physical=physical)
    if held["signature"] != manager_signature(STORAGE_CONFIGURE_OPERATION,
                                              {"place": place}):
        _refuse(f"the journalled workspace store configuration names "
                f"{name_value(place)}, which is not the store its recorded "
                f"signature was written for; the committed answer and the "
                f"operands it was committed under disagree", code="schema")
    return place


def configured_workspace_storage(store):
    """The deployment's frozen answer, or a refusal.

    THE ONLY WAY TO OBTAIN A `WorkspaceStorage`, and the two accounts must
    agree exactly as they must for the group: the committed operation is the
    deployment's act and `meta` is this manager's projection of it. Every
    direction of disagreement fails closed, including a projection that is
    merely absent -- a record this build cannot cross-check is not one it mints
    a custody root from.
    """
    return WorkspaceStorage(_agreed_storage_place(store, physical=True), _MINT)


def _agreed_storage_place(store, *, physical):
    """The one place BOTH accounts name, or the exact way they disagree.

    W270664 F2 split this out of `configured_workspace_storage` so the
    agreement can be re-decided under a database lock WITHOUT the filesystem.
    Every refusal below is a read of this database and of nothing else; the
    only thing `physical` chooses is whether the two places each account names
    are also asked of the disk on the way past. The refusals, their order and
    their categories are unchanged in both directions.
    """
    projected = _configured_storage(store, physical=physical)
    committed = _committed_workspace_storage(store, physical=physical)
    if projected is None and committed is None:
        _denied("this manager has no configured workspace store; the "
                "deployment records the one directory attempts are allocated "
                "under before any custody act, and a store taken from a "
                "caller's operand is not a deployment's decision")
    if committed is None:
        _refuse(f"this manager's record names workspace store "
                f"{name_value(projected)} with no committed configuration "
                f"behind it; a projection nobody configured is not a "
                f"deployment's act", code="schema")
    if projected is None:
        _refuse(f"the deployment configured workspace store "
                f"{name_value(committed)} and this manager's record of it is "
                f"gone; a configuration this build cannot cross-check is not "
                f"one it mints a custody root from", code="schema")
    if projected != committed:
        _refuse(f"this manager's record names workspace store "
                f"{name_value(projected)} and the deployment's committed "
                f"configuration names {name_value(committed)}; a store the "
                f"record was edited to name is not a store the deployment "
                f"configured", code="schema")
    return committed


def recorded_storage_place(store, prepared):
    """The place a PREPARED store still names, bound to this database with no I/O.

    W270664 F2, review 2026-09-26T08:43:12Z. The reviewer's trace pinned all
    six filesystem calls the intake ending made under its own write lock to one
    cause: `custody._recorded_store` calls `configured_workspace_storage`, once
    per receipt, and each call asks `lstat` three times -- for the projection,
    for the committed answer and again when the frozen store is minted. The
    place is wanted there only as a SIGNATURE OPERAND, so what has to happen
    inside the lock is not the physical validation; it is proving that the
    place the signature is about is still the configured one.

    So the physical evidence is taken OUTSIDE, by `configured_workspace_storage`
    -- the only minter, so holding a `WorkspaceStorage` already means the
    deployment configured that directory and this manager owned it, unaliased,
    when it was measured -- and this function, called INSIDE, rebinds it:

      * THE JOURNAL, through `_committed_workspace_storage`: the kind, the
        answer through `replay`, and the signature RECOMPUTED over the place.
        That is the provenance, and it is the same reader the outside path used.
      * THE PROJECTION, and the two accounts agreeing, exactly as outside.
      * AND THAT BOTH OF THEM STILL NAME THE PREPARED PLACE. A configuration
        committed between the measurement and this transaction makes the
        prepared evidence stale, and stale evidence is refused rather than
        signed. This is the check that makes an operand ARGUMENT worth
        anything: without it the caller would be handing in a place nobody
        re-derived, which is the "caller composed it" defect the receipt
        readers already refuse.

    A PLAIN VALUE IS DELIBERATELY NOT ACCEPTED. The operand is the frozen
    `WorkspaceStorage`, so a caller cannot reach this with a path it chose --
    the rule `WorkspaceStorage` exists for is not weakened by moving where the
    lstat happens.
    """
    if not isinstance(prepared, WorkspaceStorage):
        _refuse("a prepared workspace store is the frozen answer "
                "`configured_workspace_storage` mints, so that what is rebound "
                "under the lock is evidence this manager measured rather than a "
                "place a caller composed", code="schema")
    place = _agreed_storage_place(store, physical=False)
    if place != prepared.place:
        _refuse(f"the workspace store was measured as {name_value(prepared.place)} "
                f"before this transaction and this database now records "
                f"{name_value(place)}; a configuration committed in between "
                f"makes the prepared evidence stale, and an act is not signed "
                f"for a store nobody validated", code="schema")
    return place


def check_workspace_group(gid, *, what="the configured workspace group"):
    """The deployment's dedicated workspace group, validated and owned.

    W33936, approver ruling M34916.  The deployment provisions ONE dedicated
    non-authority group and grants this manager permission to use it.  This
    manager NEVER creates or modifies a host group: it validates the one it was
    configured with and fails closed on everything else.

    THERE IS NO DEFAULT, and that absence is the correction.  The rejected
    design read the workspace root's own gid, which measured as a user's LOGIN
    group -- reaching that user's home and everything in it, and on a gid-0
    manager reaching root's.  A group inherited from a service directory is not
    a workspace grant, so this refuses to infer one at all.

    THREE REFUSALS, each a different way for a configured value to be wrong:

      * gid 0 is the root group and carries authority over the whole host;
      * a gid this manager is not a member of is unusable -- it could neither
        `chgrp` the root to it nor be granted it -- and a configuration nobody
        can act on is a silent no-op rather than a policy;
      * a non-integer, a bool or a negative number is not a group id.
    """
    what = label_of(what)
    if type(gid) is bool or type(gid) is not int or gid < 0:
        _refuse(f"{what} is {name_value(gid)}; a group id is a non-negative "
                f"integer", code="schema")
    if gid == 0:
        _refuse(f"{what} is the root group; the workspace group is a "
                f"dedicated non-authority group provisioned for this purpose, "
                f"and root is the opposite of that", code="schema")
    held = set(os.getgroups()) | {os.getgid()}
    if gid not in held:
        _refuse(f"{what} is not a group this manager holds; a group it cannot "
                f"use is a configuration nothing can act on, and this manager "
                f"never creates or modifies a host group to make one work",
                code="schema")
    return gid


def prove_workspace_group(place, gid, *, what="the workspace root"):
    """The exact root still carries the configured group, and can be written.

    Review [P0], approver ruling M34630: "before the engine call, the adapter
    must prove that the canonical workspace root's group equals the configured
    group".  A grant established at allocation is not a grant at LAUNCH: a
    restart, a redeployment under a changed configuration, or an operator
    `chgrp` between the two leaves a root the worker cannot write and a
    container that finds out by failing halfway through its work.

    THE EXACT ROOT, and `lstat` rather than `stat`.  A symlink whose target
    carries the right group is not this root carrying it -- and this is the
    path the engine is about to bind, so what the engine will act on is what
    has to be proved.

    THE MODE IS PROVED TOO, because the group alone is not the grant.  A root
    in the right group at `0700` denies exactly what this whole correction is
    for, and it fails at the worker rather than here unless it is checked.
    """
    what = label_of(what)
    check_workspace_group(gid)
    try:
        found = os.lstat(place)
    except OSError as failure:
        _refuse(f"{what} at {name_value(place)} could not be measured before "
                f"the engine call: {type(failure).__name__}; a runtime is not "
                f"started over a root this manager cannot describe",
                code="path")
    if not stat.S_ISDIR(found.st_mode):
        _refuse(f"{what} at {name_value(place)} is not a directory", code="path")
    if found.st_gid != gid:
        # `policy.denied` rather than an integrity code, and the pairing is the
        # reason: nothing here is malformed. The root is well-formed and this
        # deployment is not permitted to run a worker over it, which is what
        # §9's policy category means.
        _denied(f"{what} carries group {found.st_gid} and this deployment is "
                f"configured with {gid}; the worker is granted the configured "
                f"group and would find the root in another one")
    if found.st_mode & 0o7777 != WORKSPACE_DIR:
        _denied(f"{what} is mode {oct(found.st_mode & 0o7777)} and an "
                f"execution workspace is {oct(WORKSPACE_DIR)}; the group's "
                f"write and the setgid inheritance are the grant, and a root "
                f"without them denies the worker the work it was started for")
    return place


def adopt_workspace_group(roots, gid):
    """Put the writable root in the configured group, exactly.

    `os.chown` with `-1` for the owner changes only the GROUP, which an
    unprivileged manager may do for a group it is a member of -- which
    `check_workspace_group` has already proved.  The mode is established here
    too, because group-writable is the whole point of the group and leaving it
    to the umask is what W33935 corrected at the two protocol documents.
    """
    place = roots["workspace"]
    gid = check_workspace_group(gid)
    try:
        os.chown(place, -1, gid)
    except OSError as failure:
        # NAMED, not swallowed.  A deployment whose manager cannot put its own
        # workspace in the configured group has a provisioning fault, and a
        # silently un-adopted root is the original defect arriving later and
        # from further away.
        _denied(f"the manager could not put {name_value(place)} in the "
                f"configured workspace group {gid}: "
                f"{type(failure).__name__}; the deployment provisions this "
                f"group and grants this manager membership, and without it "
                f"the worker cannot write the outputs it must declare")
    os.chmod(place, WORKSPACE_DIR)
    return place


_LINE_DIR = 0o2775


def _prove_line_access(place, pinned, gid):
    """Prove stable development-root access without repairing an existing line."""
    check_workspace_group(gid)
    if os.path.realpath(place) != place:
        _denied("the development line is its own canonical directory")
    try:
        found = os.lstat(place)
    except OSError as failure:
        _denied(f"the development line cannot be measured: {type(failure).__name__}")
    if (not stat.S_ISDIR(found.st_mode)
            or (found.st_dev, found.st_ino) != tuple(pinned)
            or found.st_gid != gid or stat.S_IMODE(found.st_mode) != _LINE_DIR):
        _denied("the recorded development line must retain its object identity, "
                "configured group and mode 02775; admission does not repair it")
    return place


def establish_line_access(place, pinned, identity):
    """Make one materialized line usable AT CREATION. Constant permission work.

    W194457, FINDING 2026-09-17. What stood here walked the whole materialized
    tree holding a no-follow descriptor for every entry and then `fchown`ed and
    `fchmod`ed each one -- a permission-only pass whose descriptor peak and
    whose syscall count were both proportional to the checkout. On the incident
    tree that was the failure: one descriptor per entry against a soft
    `RLIMIT_NOFILE` of 1,024.

    THE RULING REMOVES THE PASS RATHER THAN MAKING IT CHEAPER. Under a shared
    execution identity the materialized tree is ALREADY owned by the identity
    that will use it, so there is nothing per-entry to change. What a line root
    still needs is what `_prove_line_access` measures: this deployment's group
    and mode `02775`, whose setgid bit is what keeps everything created inside
    it in that group afterwards. That is TWO acts, whatever the tree holds, and
    `PERMISSION_ACTS` counts them so a check can assert the shape.

    THE INTEGRITY WALK IS SEPARATE AND IS NOT PERMISSION WORK. `prove_line_integrity`
    keeps the constraints that used to ride along here -- special files,
    hardlinked regular files, the entry, byte and depth ceilings, and that
    everything belongs to the shared identity -- and it is bounded by DEPTH.
    Attributing it honestly matters: it is materialization/integrity cost, and
    calling it constant-time would be a different false claim from the one this
    corrects.
    """
    if not isinstance(identity, WorkspaceIdentity):
        _denied("establishing development-line access needs this deployment's "
                "minted execution identity, not a pair of integers")
    if os.path.realpath(place) != place:
        _denied("initial development-line access requires a canonical root")
    try:
        root = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _access_failure(
            "initial development-line access could not open", place, failure,
            what="no permissions were changed; keep the line materializing "
                 "and ungranted")
    try:
        found = os.fstat(root)
        if (found.st_dev, found.st_ino) != tuple(pinned):
            _denied("the initial development line no longer has its recorded pin")
        if found.st_uid != identity.uid:
            _denied(f"the materialized development line is owned by "
                    f"{found.st_uid} and this deployment's execution identity "
                    f"is {identity.uid}; a line this manager did not "
                    f"materialize is not one it grants access to")
        os.fchown(root, -1, identity.gid)
        _permission_act("chown")
        os.fchmod(root, _LINE_DIR)
        _permission_act("chmod")
    except OSError as failure:
        # AN `EPERM` HERE IS THE ARRANGEMENT TALKING. `fchown` to a group this
        # manager does not hold, or a root some other identity materialized, is
        # exactly what a wrong deployment configuration produces at the first
        # act that matters -- so the refusal names the syscall's own errno and
        # points at the mapping rather than saying `OSError`.
        _access_failure(
            "initial development-line access could not set the group and mode "
            "of", place, failure,
            what="the root may carry a partial change; keep the line "
                 "materializing and ungranted")
    finally:
        os.close(root)
    return _prove_line_access(place, pinned, identity.gid)


def prove_line_integrity(place, pinned, identity):
    """Every constraint the removed provisioning pass also enforced, and NO
    permission act at all. Bounded by depth rather than by entry count.

    The descriptor discipline is `_prove_line_consumable`'s: `held` is the open
    PATH, a child is closed as soon as its subtree is proved, and the peak is
    one per level. The checks are the ones that used to ride along with the
    `fchown`/`fchmod` loop, which is why they are kept here rather than lost
    with it: a special file, a hardlinked regular file, an entry this identity
    does not own, and the entry/byte/depth ceilings.

    AND IT REVALIDATES BEFORE IT ANSWERS, which my first cut dropped and review
    2026-09-17T12-47-56Z caught. The removed pass re-`fstat`ed every RETAINED
    descriptor after the walk and compared `(uid, nlink, mode)` against what it
    had seen, so a file that acquired an outside hardlink while a later sibling
    was being opened was refused before anything was granted. Closing each
    child bounds the descriptors and also throws that guard away -- and the
    reviewer's interleaving reproduction walked straight through it.

    SO THE FINGERPRINTS ARE KEPT INSTEAD OF THE DESCRIPTORS. One pass records
    `(dev, ino, uid, nlink, mode)` per entry -- memory, not file descriptors --
    and a SECOND bounded pass re-opens each entry no-follow and compares. An
    entry that was replaced fails on identity; one that was hardlinked,
    chowned or chmoded fails on the rest. The peak stays one descriptor per
    level in both passes, and the invariant the grant rests on is the one the
    retained descriptors used to provide.

    EVERY ENTRY IS FINGERPRINTED, INCLUDING THE ONES NEVER OPENED -- see
    `account`. Review 2026-09-17T15-42-06Z finding 1: a symlink was skipped
    before it was compared, so a recorded regular file replaced by one walked
    through the revalidation the grant depends on.

    AND A FAILURE HERE NAMES WHAT FAILED -- see `_access_failure`. This is the
    FIRST preparation path `create_line` takes, so a refusal that said only
    `PermissionError (errno 13)`, as finding 2 recorded, was the operator's
    whole diagnostic for one unreadable entry somewhere in a checkout.
    """
    if not isinstance(identity, WorkspaceIdentity):
        _denied("proving a development line needs this deployment's minted "
                "execution identity")
    if os.path.realpath(place) != place:
        _denied("a development line is its own canonical directory")
    held = []
    count = 0
    total = 0
    deepest = 0
    seen = {}
    counted_children = {}
    recording = seen

    def named(relative):
        """The failing entry as an operator can act on it. The RELATIVE path
        goes in the rendered slot and the root is named in the sentence after
        it, rather than the other way round: a refusal renders a bounded
        prefix of a value, and an absolute checkout path spends all of it
        before reaching the entry that actually failed."""
        return relative if relative else place

    inside = (f"it is an entry in the development line at {name_value(place)} "
              f"this manager is proving; nothing was changed and the line "
              f"stays materializing and ungranted")

    def account(relative, fingerprint):
        """RECORD on the first pass, COMPARE on the second -- for every entry
        the walk observes, including the ones it never opens.

        W194457, review 2026-09-17T15-42-06Z finding 1. A symlink used to be
        skipped outright here, which meant a recorded REGULAR FILE replaced by
        a symlink between the passes had nothing to compare against: its
        directory's entry count was unchanged, `visit` never saw it, and the
        line was granted `02775` on a tree the first pass had proved and the
        second had not. The historical permission walk refused that exact
        interleaving, so it was a regression in the invariant the grant rests
        on rather than a new guarantee.

        FINGERPRINTING THE SYMLINK ITSELF is what closes it, and it closes the
        transition in BOTH directions, because `st_mode` carries the type: a
        file that became a link and a link that became a file are each a
        mismatch. Nothing about stable symlinks changes -- one that stays put
        matches itself, is still never followed and is still never opened.
        """
        if recording is not None:
            recording[relative] = fingerprint
            return
        was = seen.get(relative)
        if was is None:
            _denied("a development-line entry appeared while it was proved")
        if was != fingerprint:
            _denied("a development-line entry changed while it was proved; "
                    "nothing was granted")

    def visit(descriptor, depth, relative):
        nonlocal count, total, deepest
        deepest = max(deepest, len(held))
        try:
            found = os.fstat(descriptor)
        except OSError as failure:
            _access_failure(
                "proving the development line could not inspect",
                named(relative), failure, what=inside)
        account(relative, (found.st_dev, found.st_ino, found.st_uid,
                           found.st_nlink, found.st_mode))
        count += 1
        if count > MAX_ENTRIES or depth > MAX_DEPTH:
            _refuse("the development line exceeds the filesystem ceiling",
                    code="limit")
        if found.st_uid != identity.uid:
            _denied("the development line carries an entry this deployment's "
                    "execution identity does not own")
        if stat.S_ISREG(found.st_mode):
            if found.st_nlink != 1:
                _denied("the development line carries a hardlinked file")
            total += found.st_size
            if total > MAX_BYTES:
                _refuse("the development line exceeds the byte ceiling",
                        code="limit")
            return
        if not stat.S_ISDIR(found.st_mode):
            _denied("the development line carries a special file")
        try:
            with os.scandir(descriptor) as listing:
                entries = list(listing)
        except OSError as failure:
            _access_failure(
                "proving the development line could not list",
                named(relative), failure, what=inside)
        if recording is None and len(entries) != counted_children.get(relative):
            _denied("a development-line directory gained or lost an entry "
                    "while it was proved; nothing was granted")
        if recording is not None:
            counted_children[relative] = len(entries)
        for entry in entries:
            if count >= MAX_ENTRIES or depth >= MAX_DEPTH:
                _refuse("the development line exceeds the filesystem ceiling",
                        code="limit")
            below = f"{relative}/{entry.name}" if relative else entry.name
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError as failure:
                _access_failure(
                    "proving the development line could not inspect",
                    named(below), failure, what=inside)
            if stat.S_ISLNK(observed.st_mode):
                account(below, (observed.st_dev, observed.st_ino,
                                observed.st_uid, observed.st_nlink,
                                observed.st_mode))
                count += 1
                continue
            if not (stat.S_ISDIR(observed.st_mode) or stat.S_ISREG(observed.st_mode)):
                _denied("the development line carries a special file")
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if stat.S_ISDIR(observed.st_mode):
                flags |= os.O_DIRECTORY
            try:
                child = os.open(entry.name, flags, dir_fd=descriptor)
            except OSError as failure:
                # AN `ELOOP` HERE IS THE RACE, NOT A PERMISSION PROBLEM.
                # `O_NOFOLLOW` fails this way for an entry that became a
                # symlink between the `stat` above and this open -- the same
                # transition `account` catches across the passes, caught
                # within one. Reporting it as an access failure would point
                # the operator at the engine's id mapping for something that
                # is a changing tree.
                if getattr(failure, "errno", None) == errno.ELOOP:
                    _denied("a development-line entry changed while it was "
                            "proved; nothing was granted")
                _access_failure(
                    "proving the development line could not open",
                    named(below), failure, what=inside)
            held.append(child)
            try:
                try:
                    opened = os.fstat(child)
                except OSError as failure:
                    _access_failure(
                        "proving the development line could not inspect",
                        named(below), failure, what=inside)
                if (opened.st_dev, opened.st_ino) != (observed.st_dev,
                                                      observed.st_ino):
                    _denied("a development-line entry changed while it was "
                            "proved")
                visit(child, depth + 1, below)
            finally:
                held.pop()
                os.close(child)

    try:
        root = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        # THIS IS THE FIRST PREPARATION PATH `create_line` TAKES, so it is the
        # refusal an operator sees first. Review 2026-09-17T15-42-06Z finding
        # 2: it used to say `PermissionError (errno 13)` and name neither the
        # operation nor the path, which is the shape that lost this Work's own
        # incident errno one function further along.
        _access_failure(
            "proving the development line could not open the line root at",
            place, failure,
            what="nothing was changed; the line stays materializing and "
                 "ungranted")
    held.append(root)
    try:
        try:
            found = os.fstat(root)
        except OSError as failure:
            _access_failure(
                "proving the development line could not inspect the line root "
                "at", place, failure,
                what="nothing was changed; the line stays materializing and "
                     "ungranted")
        if (found.st_dev, found.st_ino) != tuple(pinned):
            _denied("the development line no longer has its recorded pin")
        visit(root, 0, "")
        peak = deepest
        # THE SECOND PASS IS THE PRE-GRANT REVALIDATION. Same bounded walk,
        # same no-follow opens, and this time every entry is compared against
        # the fingerprint the first pass recorded for that exact path.
        recording = None
        count = 0
        total = 0
        visit(root, 0, "")
    except OSError as failure:
        # BACKSTOP. Every boundary that touches the filesystem above reports
        # its own operation and path; this only keeps an unforeseen one from
        # reaching a caller as a bare `OSError`, and it still carries the
        # errno rather than dropping it.
        _access_failure(
            "proving the development line failed while walking", place,
            failure,
            what="nothing was changed; the line stays materializing and "
                 "ungranted")
    finally:
        for descriptor in reversed(held):
            os.close(descriptor)
    return {"entries": count, "bytes": total, "peak_descriptors": peak}


def _prove_line_consumable(place, pinned):
    """PROVE this manager can actually read the line it is about to consume.

    W105982. The gap this closes is not a mode question and cannot be answered
    as one. A worker writes into the mounted line with its own identity and its
    own umask; the manager then reads that tree back to seal a result, validate
    a checkpoint and hand a reviewer a frozen revision. Initial provisioning
    established the tree the manager MATERIALIZED -- it says nothing about a
    directory the worker created at mode 0700 afterwards, and by the time the
    ordinary cleanup path runs, every one of those reads has already happened.

    SO THE PROOF IS THE OPEN ITSELF. `os.access` asks the kernel a question
    about a hypothetical, and a mode bit is a claim about a permission rather
    than the permission; both answer for the wrong identity as soon as
    supplementary groups, ACLs or a read-only mount are involved. What is
    performed here is the exact syscall the consumer will perform, under the
    exact identity it will perform it as, and a refusal is what a consumer
    would otherwise discover halfway through sealing.

    AND IT CHANGES NOTHING. No `chmod`, no `chown`, no repair. A tree this
    manager cannot read is EVIDENCE, and the operator's decision -- the
    accepted stable modes are `0664`, `02775` and `0775` -- is not this
    function's to make on their behalf. It walks no-follow at every component,
    counts a symlink without following it, and refuses a special file, so the
    proof cannot be redirected into another tree by anything the worker left
    behind.

    THE PRIVATE METADATA IS PART OF THE SUBJECT. The checkpoint profile reads
    the repository, not only the payload, so a `.git` the manager cannot
    traverse is exactly as fatal as an unreadable source file and is exactly
    as likely: it is created by the worker's own commands.
    """
    if type(place) is not str or not place or os.path.realpath(place) != place:
        _denied("a consumable development line is its own canonical directory")
    try:
        device, inode = pinned
    except (TypeError, ValueError):
        _denied("a development-line pin is one device-and-inode pair")
    held = []
    count = 0
    total = 0
    deepest = 0

    def visit(descriptor, relative):
        nonlocal count, total, deepest
        deepest = max(deepest, len(held))
        found = os.fstat(descriptor)
        count += 1
        if count > MAX_ENTRIES:
            _refuse("the development line exceeds the filesystem ceiling",
                    code="limit")
        if stat.S_ISREG(found.st_mode):
            total += found.st_size
            if total > MAX_BYTES:
                _refuse("the development line exceeds the byte ceiling",
                        code="limit")
            return
        if not stat.S_ISDIR(found.st_mode):
            _denied(f"the development line carries a special file at "
                    f"{name_value(relative)}")
        if relative.count("/") > MAX_DEPTH:
            _refuse("the development line exceeds the depth ceiling",
                    code="limit")
        try:
            names = sorted(os.listdir(descriptor))
        except OSError as failure:
            _access_failure(
                "this manager cannot list", relative, failure,
                what="it is a directory in the development line this manager "
                     "is about to consume; the line is left exactly as it is "
                     "and nothing is repaired")
        for name in names:
            below = f"{relative}/{name}" if relative else name
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            try:
                child = os.open(name, flags, dir_fd=descriptor)
            except OSError as failure:
                # ELOOP IS NOT A DENIAL. `O_NOFOLLOW` refuses a symlink with
                # the same errno an unreadable entry could raise, so the two
                # are told apart by asking what the entry IS rather than by
                # reading the failure -- a link is counted and stepped over,
                # and anything else is the access evidence this exists for.
                try:
                    seen = os.lstat(name, dir_fd=descriptor)
                except OSError:
                    seen = None
                if seen is not None and stat.S_ISLNK(seen.st_mode):
                    # COUNTED AND BOUNDED, not counted and waved through.
                    # W105982 candidate review 2026-09-07: the ceiling was
                    # tested only for entries this walk OPENS, so a trailing
                    # run of symlinks passed it however long it was. The target
                    # is still never followed and no mode is touched.
                    count += 1
                    if count > MAX_ENTRIES:
                        _refuse("the development line exceeds the filesystem "
                                "ceiling", code="limit")
                    continue
                _access_failure(
                    "this manager cannot open", below, failure,
                    what="it is an entry in the development line this manager "
                         "is about to consume; the line is left exactly as it "
                         "is and nothing is repaired")
            # CLOSED AS SOON AS ITS SUBTREE IS PROVED. W194457, review
            # 2026-09-17T12-32-56Z finding 2: this appended every child and
            # closed nothing until the end, so the peak was one descriptor per
            # ENTRY -- measured EMFILE at 1,021 tracked descriptors against a
            # soft limit of 1,024. The proof does not need them all at once:
            # what it establishes about an entry is established by the time
            # `visit` returns. `held` is now the open PATH, so the peak is one
            # per level and the outer `finally` still closes the ancestors on
            # any refusal.
            #
            # NOTHING ELSE CHANGES. The open is still `O_NOFOLLOW` at every
            # component, the root is still pinned, a symlink is still counted
            # and never followed, a special file is still refused, and no mode
            # is touched anywhere in here.
            held.append(child)
            try:
                visit(child, below)
            finally:
                held.pop()
                os.close(child)

    try:
        root = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _access_failure(
            "this manager cannot open the development line at", place,
            failure,
            what="it is the root of the line this manager is about to "
                 "consume; the line is left exactly as it is and nothing is "
                 "repaired")
    held.append(root)
    try:
        found = os.fstat(root)
        if (found.st_dev, found.st_ino) != (device, inode):
            _denied("the development line no longer has the object identity "
                    "its lifecycle recorded")
        visit(root, "")
        peak = deepest
    finally:
        for descriptor in reversed(held):
            os.close(descriptor)
    return {"entries": count, "bytes": total, "peak_descriptors": peak}


def _prove_execution_workspace(roots, gid, labels):
    """A line marker selects policy; the lifecycle proof supplies authority."""
    if type(roots) is AllocatedRoots and roots._line:
        if roots._line_proof is None or roots._grant is None or not roots._grant():
            _denied("a development-line launch requires its current lifecycle proof and grant")
        return roots._line_proof(roots, gid, labels)
    return prove_workspace_group(roots["workspace"], gid,
                                 what="this assignment's workspace root")

ROOT_NAMES = ("inputs", "workspace")
# W202663 (owner 2026-09-21T05:53:07Z, "I approve spare mount"): `scratch` is
# the attempt's own writable DISK-BACKED working directory, provisioned with
# the home because the home is closed once composition ends and nothing can be
# created in it afterwards. It is deliberately NOT a `ROOT_NAMES` member: what
# a container may MOUNT through the assignment operand is unchanged; the
# scratch crosses as its own delivery (`oci._scratch_mount`) at the constant
# `oci.SCRATCH_TARGET`, and its retention follows the home's own disposition.
HOME_ENTRIES = ("credential-state", "credentials", "custody",
                "scratch") + ROOT_NAMES
_REVIEW_LINE_HOME = ".baton-review-lines"


# W257624, review 2026-09-26T03:17:01Z: THE OBJECT A RESTORATION'S EXECUTION IS HELD
# ON, and it lives BESIDE the line rather than inside it.
#
# `restore_abandoned_correction` performs its checkout reset outside every database
# transaction, and nothing in this build could say whether a previous executor had
# stopped -- an incarnation is reusable, a process registry is invisible to another
# process, and a caller-authored assertion is forgeable from the journal. An exclusive
# advisory lock is the one observation the operating system itself answers: the kernel
# releases it when a holder dies, so acquiring it is positive evidence that no manager
# holds this recovery's execution.
#
# INSIDE THE LINE HOME AND NEVER INSIDE A CHECKOUT. The checkpoint profile validates the
# checkout as clean at its retained checkpoint, so a lock file among its entries would
# break the very validation the recovery depends on. The reserved `_REVIEW_LINE_HOME`
# namespace is disjoint from every custody root and from every checkout, which is why
# the object belongs here.
#
# ONE DURABLE OBJECT PER LINE, never replaced and never unlinked: an alias or a fresh
# inode would let two holders believe they held the same exclusion.
RESTORATION_LOCK = "restoration.lock"


def restoration_lock_path(storage, line_id):
    """Where this line's restoration-execution lock object lives."""
    boundaries.text(line_id, "a development line identity")
    if os.sep in line_id or line_id in (os.curdir, os.pardir):
        _denied("a development line identity is one path element")
    root = _real(storage, "the manager's workspace storage")
    return os.path.join(root, _REVIEW_LINE_HOME,
                        line_id + "." + RESTORATION_LOCK)


# The one journalled identity of a line's lock object. Derived, so a manager that
# never created it re-derives the same name and compares the same fact.
RESTORATION_LOCK_KIND = "review-line.restoration-lock"


def _restoration_lock_identity(control, line_id, observed, what):
    """Pin this lock object's identity durably, or prove it is the pinned one.

    W257624, review 2026-09-26T03:27:43Z [P2]. Holding a lock on whatever inode happens
    to answer a pathname is not an exclusion: while one holder had the original object,
    the pathname was renamed aside, a second caller created a NEW inode there and took
    its own lock, and both believed they held the line. A pathname is a name; the object
    is what a lock is on.

    SO THE OBJECT'S IDENTITY IS JOURNALLED ON FIRST USE AND COMPARED EVER AFTER. A
    replaced inode, a legacy recreation and a silently missing object are all the same
    refusal, because none of them is the object this line's exclusion was established
    on. There is no repair path: re-pinning on mismatch would be the defect with extra
    steps.
    """
    from .store import manager_signature

    operation_id = RESTORATION_LOCK_KIND + ":" + line_id
    document = {"line_id": line_id, "device": observed[0], "inode": observed[1]}
    signature = manager_signature(RESTORATION_LOCK_KIND, document)
    recorded = control.operation_record(operation_id)
    if recorded is None:
        return control.transact(operation_id, RESTORATION_LOCK_KIND, signature,
                                lambda connection: dict(document))
    _, pinned = control.replay(operation_id, recorded["signature"],
                               kind=RESTORATION_LOCK_KIND)
    if pinned is None:
        _refuse(f"{what} has a recorded lock identity with no answer to replay",
                code="schema")
    if (pinned.get("device"), pinned.get("inode")) != observed:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{what}'s lock pathname now names object "
            f"{observed[0]}:{observed[1]} and this line's exclusion was established on "
            f"{pinned.get('device')}:{pinned.get('inode')}; a lock is held on an object "
            f"and not on a name, and a replaced one is not the exclusion anybody took")
    return pinned


@contextlib.contextmanager
def hold_restoration_lock(storage, line_id, *, control=None):
    """Take this line's restoration exclusion, or answer that somebody holds it.

    NON-BLOCKING ON PURPOSE. A caller that waited would be a caller that eventually
    proceeded, and the whole question is whether an execution is STILL RUNNING -- so a
    holder's presence is an answer rather than a delay.

    THE OBJECT IS PROVED BEFORE IT IS TRUSTED, and review 2026-09-26T03:27:43Z [P2] is
    why each step is here rather than assumed:

      * `O_NOFOLLOW` so a precreated SYMLINK at the pathname is refused instead of
        followed to somebody else's file;
      * `fstat` on the DESCRIPTOR, requiring a regular file, so a directory, a fifo or
        a device cannot stand in for the object;
      * the descriptor's identity compared against the PATHNAME's current identity, so
        an object swapped between the open and the check is caught rather than locked;
      * and the identity compared against this line's JOURNALLED pin, so a replaced
        inode, a legacy recreation and a silently missing object all refuse.

    THE DESCRIPTOR IS KEPT FOR THE WHOLE `with` BODY, which is what makes this an
    exclusion rather than a probe-and-drop: the lock is released when the body ends and
    not a moment earlier, so nothing slips between an observation and the act it
    authorized. The object is opened and never truncated, unlinked or renamed.

    WHAT IT DOES NOT PROVE, stated here because the act that consumes it must not
    overstate: that no EXTERNAL work a previous executor started is still running. The
    checkpoint profile resets through an injected runner and an orphaned child can
    outlive the manager that spawned it. This answers for MANAGERS holding the
    execution; the effects' own lifetime needs that runner's account.
    """
    what = f"development line {name_value(line_id)}"
    # AN EXCLUSION THAT CANNOT BE PINNED IS NOT AN EXCLUSION, so a caller with no
    # control store is refused rather than handed a lock on whatever inode answers the
    # pathname. The operand is optional in the SIGNATURE and required in EFFECT: review
    # 2026-09-26T03:27:43Z's immutable identity probe calls this without one, and
    # breaking that probe with a `TypeError` would be an API break dressed up as a
    # defeated schedule -- which that reviewer has twice warned against. It gets the
    # refusal the contract actually means.
    if control is None:
        raise ContractRefusal(
            "refused", "capability",
            f"{what}'s restoration exclusion needs the control store its lock identity "
            f"is pinned in; an exclusion taken on an unpinned pathname is a lock on a "
            f"name rather than on the object anybody else is holding")
    place = restoration_lock_path(storage, line_id)
    os.makedirs(os.path.dirname(place), exist_ok=True)
    try:
        descriptor = os.open(place, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o660)
    except OSError as failure:
        _denied(f"{what}'s lock object could not be opened as its own regular file "
                f"({type(failure).__name__}); a symlink or special entry at that "
                f"pathname is not this line's exclusion")
    try:
        held = os.fstat(descriptor)
        if not stat.S_ISREG(held.st_mode):
            _denied(f"{what}'s lock pathname names a non-regular object; an exclusion "
                    f"is taken on a regular file")
        observed = (held.st_dev, held.st_ino)
        named = os.lstat(place)
        if (named.st_dev, named.st_ino) != observed:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"{what}'s lock pathname was replaced while it was being opened; the "
                f"descriptor names {observed[0]}:{observed[1]} and the pathname now "
                f"names {named.st_dev}:{named.st_ino}")
        _restoration_lock_identity(control, line_id, observed, what)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


# W270664 F2 -- removal ownership, admitted in the database and performed outside it.
# Owner 270664 selects this correction; review 2026-09-26T06:21:32Z pinned the
# reciprocal half. The restoration-lock region above belongs to W257624 and is
# untouched by any of this.
REMOVAL_OWNERSHIP_KIND = "workspace.removal-ownership"
REMOVAL_COMPLETE_KIND = "workspace.removal-complete"


ADOPTION_KIND = "workspace.adoption"
ADOPTION_COMPLETE_KIND = "workspace.adoption-complete"


def _adoption_id(assignment_id, ordinal):
    return f"{ADOPTION_KIND}:{assignment_id}:{ordinal}"


def _adoption_complete_id(assignment_id, ordinal):
    return f"{ADOPTION_COMPLETE_KIND}:{assignment_id}:{ordinal}"


def standing_adoption(control, assignment_id):
    """Adoptions of this attempt that are admitted and not yet settled."""
    standing = []
    ordinal = 1
    while True:
        found = control.operation_record(_adoption_id(assignment_id, ordinal))
        if found is None:
            return standing
        if control.operation_record(
                _adoption_complete_id(assignment_id, ordinal)) is None:
            standing.append((ordinal, found))
        ordinal += 1


def _admitted_adoption(control, assignment_id, what):
    """Admit an adoption of this attempt's roots, EXCLUSIVELY against removal.

    W270664 F2, review 2026-09-26T07:25:48Z. My first reciprocal attempt was a READ before
    the act, and the reviewer's probe walked through it: adoption read "no standing removal",
    a removal was admitted after that read, and adoption proceeded. A guard that answers
    before the competing act commits excludes nothing.

    SO ADOPTION IS ADMITTED TOO, in its own short `BEGIN IMMEDIATE`, and the removal's
    admission reads THIS record inside its own. Whichever transaction commits first wins and
    the other sees it: an actor already past its early read is refused at its OWN admission
    rather than after it. That is the mutual part -- neither side is trusted to check only
    the other's absence.

    THE LIFETIME IS SHORT AND ALWAYS SETTLED. Adoption only proves roots it does not create,
    so its in-flight record is closed on success and on failure alike; it is an exclusion
    window, not a durable hold, and leaving one standing would block the attempt for nothing.
    """
    import uuid

    from .store import _recorded, manager_signature

    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        removing = standing_removal(control, assignment_id)
        if removing:
            ordinal, _ = removing[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: removal {ordinal} of this attempt's roots was admitted "
                f"and has recorded no completion, so these roots are being deleted and are "
                f"not adopted until that removal is reconciled")
        ordinal = 1
        while control.operation_record(
                _adoption_id(assignment_id, ordinal)) is not None:
            ordinal += 1
        document = {"attempt_id": assignment_id, "ordinal": ordinal, "act": what,
                    "owner": uuid.uuid4().hex}
        control._record(_adoption_id(assignment_id, ordinal), ADOPTION_KIND,
                        manager_signature(ADOPTION_KIND, document),
                        "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def _settled_adoption(control, assignment_id, owned):
    """Close an adoption's exclusion window, on success and on failure alike."""
    from .store import manager_signature

    document = {"attempt_id": assignment_id, "ordinal": owned["ordinal"],
                "owner": owned["owner"]}
    control.transact(_adoption_complete_id(assignment_id, owned["ordinal"]),
                     ADOPTION_COMPLETE_KIND,
                     manager_signature(ADOPTION_COMPLETE_KIND, document),
                     lambda _connection: dict(document))


# W270664 F2 -- THE CLEANUP'S OWN EXCLUSION, which outlives its removal.
#
# Review 2026-09-26T09:15:26Z reproduced the defect this pair closes. An enclosing
# cleanup removes the two execution roots and its removal ownership COMPLETES; the
# terminal ending has not committed yet. In that window nothing stands: the
# reviewer's probe allocates the attempt's roots again, and the cleanup's retry then
# deletes material created after the removal finished.
#
# A LONGER-LIVED RECORD IS WHAT THE WINDOW NEEDS, not a longer-lived removal. The
# removal's ownership is about one deletion and is right to complete when the
# deletion does; the CLEANUP is about everything from its eligibility to its
# terminal settlement, so it takes a record that stands for exactly that span and
# is settled in the ending's own transaction.
CLEANUP_ADMISSION_KIND = "workspace.cleanup-admitted"
CLEANUP_SETTLED_KIND = "workspace.cleanup-settled"

# W270664 F2, review 2026-09-26T10:07:07Z: THE ADMISSION HAS A CURRENT OWNER, and a retry
# TAKES IT OVER rather than joining it.
#
# The reviewer's `review_allocation_race_20260926` falsified the protocol I handed over: a
# second same-operation cleanup adopted the standing admission, settled it, an allocation
# then succeeded, and the FIRST caller -- still live, still inside its own
# `discard_execution_roots` -- deleted the newly allocated material. Matching the operation
# and the signature identified the same ACT; it said nothing about whether the previous
# EXECUTION of that act had stopped. "Absence of a lease/heartbeat is not evidence the old
# caller stopped", and idempotent deletion is not safety when what gets deleted is newer
# than the act deleting it.
#
# So adoption is a FENCED TAKEOVER: the retry records a new owner generation and every act
# performed under the admission -- its removal and its settlement -- must present the
# CURRENT owner. The fenced predecessor is refused at its next journal-guarded step instead
# of continuing to act on roots it no longer owns.
CLEANUP_TAKEOVER_KIND = "workspace.cleanup-taken-over"


def _cleanup_takeover_id(assignment_id, ordinal, generation):
    return f"{CLEANUP_TAKEOVER_KIND}:{assignment_id}:{ordinal}:{generation}"


def _current_cleanup_owner(control, assignment_id, ordinal, admitted_owner):
    """Who may act under this admission NOW, and the next free generation.

    Read by derived identity and through `replay`, so a takeover row edited in place to
    name another owner no longer answers. The admission's own owner holds it until the
    first takeover; each later one displaces the previous.
    """
    owner = admitted_owner
    generation = 1
    while True:
        record = control.operation_record(
            _cleanup_takeover_id(assignment_id, ordinal, generation))
        if record is None:
            return owner, generation
        _, document = control.replay(
            _cleanup_takeover_id(assignment_id, ordinal, generation),
            record["signature"], kind=CLEANUP_TAKEOVER_KIND)
        if document is not None and document.get("owner"):
            owner = document["owner"]
        generation += 1


def _cleanup_admission_id(assignment_id, ordinal):
    return f"{CLEANUP_ADMISSION_KIND}:{assignment_id}:{ordinal}"


def _cleanup_settled_id(assignment_id, ordinal):
    return f"{CLEANUP_SETTLED_KIND}:{assignment_id}:{ordinal}"


def standing_cleanup(control, assignment_id):
    """This attempt's cleanup admissions that carry no settlement.

    Read by derived identity rather than by scanning, which is this build's rule for
    operation records: another deployment's rows are invisible to it. An admission
    with no settlement is STANDING whatever became of the manager that took it --
    the same rule `standing_removal` follows, and for the same reason.
    """
    standing = []
    ordinal = 1
    while True:
        found = control.operation_record(
            _cleanup_admission_id(assignment_id, ordinal))
        if found is None:
            return standing
        if control.operation_record(
                _cleanup_settled_id(assignment_id, ordinal)) is None:
            standing.append((ordinal, found))
        ordinal += 1


def _admitted_cleanup_document(control, assignment_id, ordinal, record):
    """The standing admission's own document, read back through `replay`.

    Never the record's `result` column read raw: `replay` recomputes the signature,
    so an admission edited in place to name another operation no longer answers.
    """
    _, document = control.replay(
        _cleanup_admission_id(assignment_id, ordinal), record["signature"],
        kind=CLEANUP_ADMISSION_KIND)
    return document


def admit_cleanup(control, assignment_id, settlement, what):
    """Own this attempt's roots from HERE until the settlement named commits.

    W270664 F2, review 2026-09-26T09:15:26Z: "exact cleanup admission and allocation
    mutual exclusion through terminal settlement, with recoverable retry belonging to
    the same admitted operation."

    `settlement` IS THE ENCLOSING ACT'S IDENTITY, not this attempt's. It carries the
    operation the ending will commit under, the signature that operation was composed
    from, and the incarnation admitting it. That is what makes a retry attributable:

      * THE SAME OPERATION WITH THE SAME SIGNATURE ADOPTS what it already admitted, so
        an interrupted cleanup can finish. This is the recoverable retry, and it is the
        only thing that may take a standing admission over.
      * ANY OTHER ACT IS REFUSED, and the refusal says which fact differed. Review
        09:15:26Z is explicit that matching attempt ids are not enough: a second
        cleanup of the same attempt, a re-run whose OPERANDS changed, and a competing
        removal are all different acts over roots somebody else is mid-way through.
      * THE INCARNATION IS ATTRIBUTION AND NOT A LIVENESS TEST, said plainly because
        the difference matters. This build has no lease, heartbeat or liveness signal
        for a manager, so a same-operation retry from a DIFFERENT incarnation is
        treated as recovery of the same act rather than refused -- otherwise a crashed
        manager's cleanup could never be finished by its successor. What protects that
        case is not a liveness claim but idempotence: the admitted act's effect is
        "these two roots are gone", both incarnations would settle the identical
        record, and the settlement names who admitted it and who finished it.

    ONE SHORT RAW TRANSACTION, database work only -- `create_line` and
    `_admitted_removal` are the precedent. `transact` replays by identity and so
    cannot make a fresh decision; this decision is fresh.
    """
    import uuid

    from .store import _recorded, manager_signature

    # VALIDATED WITHOUT A BOUNDARY LABEL, deliberately, and `_admitted_removal` is the
    # precedent this follows. The boundary inventory attributes a CROSSING to every
    # `boundaries.*` call site and requires each to be declared and probed; this operand
    # does not cross into the manager -- it is composed by `intake.authorize_cleanup`
    # from an operation identity and a signature this build derived itself. Measured: my
    # first cut labelled these and added forty-two inventory failures for entries that
    # are not crossings at all.
    if not isinstance(settlement, dict):
        _refuse("a cleanup admission names the settlement it will be closed by",
                code="schema")
    offered = {}
    for member in ("operation", "signature", "incarnation"):
        value = settlement.get(member)
        if type(value) is not str or value == "":
            _refuse(f"a cleanup settlement names its {member}; this is "
                    f"{name_value(value)}", code="schema")
        offered[member] = value
    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        # THE OTHER SIDE OF THE RECIPROCAL EXCLUSION, read under this lock: a cleanup does
        # not start while a caller is in the middle of creating these roots.
        competing = _competing_allocation(control, assignment_id, what)
        if competing is not None:
            raise ContractRefusal("refused", "precondition", competing)
        for ordinal, record in standing_cleanup(control, assignment_id):
            held = _admitted_cleanup_document(control, assignment_id, ordinal,
                                              record)
            standing = (held or {}).get("settlement") or {}
            if standing.get("operation") != offered["operation"]:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: cleanup {ordinal} of this attempt's roots was "
                    f"admitted under operation "
                    f"{name_value(standing.get('operation'))} and has recorded no "
                    f"settlement, so that cleanup is still between its removal and its "
                    f"ending; these roots are not allocated, adopted, removed or "
                    f"cleaned up again by another act until it settles")
            if standing.get("signature") != offered["signature"]:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: cleanup {ordinal} of this attempt's roots was "
                    f"admitted under this same operation with DIFFERENT operands, so "
                    f"this is not a retry of the admitted act; an operation whose "
                    f"operands changed is a second act wearing the first one's name")
            # THE RETRY, TAKEN OVER RATHER THAN JOINED. Review 10:07:07Z: returning the
            # SAME owner let two live executions of one act believe they held it, and the
            # older one went on to delete material allocated after the newer one settled.
            # The takeover is recorded in this same admitting transaction, so exactly one
            # owner is current at every instant, and the displaced owner's next
            # journal-guarded step -- admitting its removal, or settling -- refuses.
            #
            # THE TRANSACTION IS STILL CLOSED ON THIS PATH. Measured: returning from
            # inside the `try` left `BEGIN IMMEDIATE` open, and the next thing the
            # cleanup does is a removal -- which refuses to run under an open
            # transaction and said so. The refusal was right and the leak was mine.
            _, generation = _current_cleanup_owner(control, assignment_id, ordinal,
                                                   held.get("owner"))
            document = dict(held, owner=uuid.uuid4().hex, generation=generation)
            taken = {"attempt_id": assignment_id, "ordinal": ordinal,
                     "generation": generation, "owner": document["owner"],
                     "act": what, "settlement": offered}
            control._record(
                _cleanup_takeover_id(assignment_id, ordinal, generation),
                CLEANUP_TAKEOVER_KIND,
                manager_signature(CLEANUP_TAKEOVER_KIND, taken),
                "committed", _recorded(taken), None)
            break
        else:
            ordinal = 1
            while control.operation_record(
                    _cleanup_admission_id(assignment_id, ordinal)) is not None:
                ordinal += 1
            document = {"attempt_id": assignment_id, "ordinal": ordinal,
                        "act": what, "owner": uuid.uuid4().hex,
                        "settlement": offered}
            control._record(
                _cleanup_admission_id(assignment_id, ordinal),
                CLEANUP_ADMISSION_KIND,
                manager_signature(CLEANUP_ADMISSION_KIND, document),
                "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def settle_cleanup(control, connection, assignment_id, admitted, what):
    """Close the admission IN THE ENDING'S OWN TRANSACTION, atomically with it.

    W270664 F2. This is the half that closes the gap: the exclusion ends exactly when
    the ending commits, because it is the same commit. A crash before it leaves the
    admission standing and the roots held; a rollback of the ending rolls this back
    with it, which is why it is written here rather than in a transaction of its own.

    NO FILESYSTEM CALL AND NO NESTED TRANSACTION. `connection` is the caller's open
    one, so this writes through `_record` rather than `transact` -- pure database work
    under a lock the caller already holds, which is what owner 270664's rule permits.

    THE ADMISSION IS RE-READ RATHER THAN TRUSTED. The document the caller holds is one
    the caller is holding; what authorizes the settlement is the record this journal
    still has, with its signature recomputed, naming this act as its owner.
    """
    from .store import _recorded, manager_signature

    # THE SAME REASON AS `admit_cleanup`: this is the document that function answered,
    # not a value crossing into the manager, so it is checked rather than labelled.
    if not isinstance(admitted, dict) or "ordinal" not in admitted \
            or "owner" not in admitted:
        _refuse("settling a cleanup needs the admission this act was given",
                code="schema")
    ordinal = admitted["ordinal"]
    record = control.operation_record(
        _cleanup_admission_id(assignment_id, ordinal))
    if record is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s cleanup admission {ordinal} is no longer recorded, so this "
            f"settlement cannot be attributed to the authority it was performed under")
    held = _admitted_cleanup_document(control, assignment_id, ordinal, record)
    # THE CURRENT OWNER, NOT THE ADMISSION'S FIRST ONE. Review 2026-09-26T10:07:07Z: a
    # retry takes the admission over, so a displaced predecessor reaching this line is
    # settling an exclusion that is no longer its to close -- and it was that settlement,
    # in their probe, that let an allocation through in front of a still-live remover.
    current, _generation = _current_cleanup_owner(control, assignment_id, ordinal,
                                                  (held or {}).get("owner"))
    if held is None or current != admitted["owner"] \
            or held.get("attempt_id") != assignment_id:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{what}'s cleanup admission {ordinal} names another act, so this "
            f"settlement would close an exclusion this act does not own")
    if control.operation_record(_cleanup_settled_id(assignment_id, ordinal)) \
            is not None:
        # ALREADY SETTLED IS NOT AN ERROR AND IS NOT A SECOND WRITE. A replayed
        # ending reaches here with the same admission; the record it would write is
        # the one already there.
        return dict(held)
    document = {"attempt_id": assignment_id, "ordinal": ordinal,
                "owner": held["owner"],
                "settlement": held.get("settlement"),
                "settled_by": getattr(control, "incarnation", None)}
    control._record(
        _cleanup_settled_id(assignment_id, ordinal), CLEANUP_SETTLED_KIND,
        manager_signature(CLEANUP_SETTLED_KIND, document),
        "committed", _recorded(document), None)
    return document


# W270664 F2, review 2026-09-26T10:07:07Z: ALLOCATION IS ADMITTED TOO, because a check
# that has returned is not an exclusion.
#
# Their probe committed a cleanup admission in the instant AFTER allocation's
# `refuse_if_held` answered and BEFORE its `makedirs`, and allocation went on to create the
# roots a cleanup then owned. My guard was a read; what allocation needs is a record that
# stands across its own effect, exactly as the removal and the cleanup have.
#
# RECIPROCAL AND ATOMIC. Each side's admitting transaction takes `BEGIN IMMEDIATE` and reads
# the others' standing records in pure SQL, so whichever commits first wins and the loser
# sees it and refuses. No transaction is held across a filesystem effect on either side:
# allocation commits its admission, creates, then completes.
ALLOCATION_KIND = "workspace.allocation-admitted"
ALLOCATION_COMPLETE_KIND = "workspace.allocation-complete"


def _allocation_id(assignment_id, ordinal):
    return f"{ALLOCATION_KIND}:{assignment_id}:{ordinal}"


def _allocation_complete_id(assignment_id, ordinal):
    return f"{ALLOCATION_COMPLETE_KIND}:{assignment_id}:{ordinal}"


def standing_allocation(control, assignment_id):
    """Allocations of this attempt's roots that are admitted and not yet complete."""
    standing = []
    ordinal = 1
    while True:
        found = control.operation_record(_allocation_id(assignment_id, ordinal))
        if found is None:
            return standing
        if control.operation_record(
                _allocation_complete_id(assignment_id, ordinal)) is None:
            standing.append((ordinal, found))
        ordinal += 1


def _competing_allocation(control, assignment_id, what):
    """The pure-SQL refusal a live allocation owes an act that would remove these roots.

    One reader for both the cleanup side and the removal side, so the two cannot drift into
    disagreeing about what "a caller is creating these roots right now" means.
    """
    allocating = standing_allocation(control, assignment_id)
    if not allocating:
        return None
    ordinal, _ = allocating[0]
    return (f"{what} is refused: allocation {ordinal} of this attempt's roots was admitted "
            f"and has recorded no completion, so a caller is creating them right now and "
            f"what it creates is newer than this act's authority over it")


def _admitted_allocation(control, assignment_id, what):
    """Own this attempt's roots for as long as they are being created.

    The mirror of `_admitted_removal`, and deliberately the same shape: one short raw
    transaction that reads the journal only, refuses on anything standing, and commits this
    act's ownership. The creation then happens with NO lock held, and the completion is
    written afterwards.

    A CUSTODY HOLD IS READ HERE AS WELL AS OUTSIDE. `refuse_if_held` is the early refusal
    for the ordinary case and reaches `realpath`; this is the one that DECIDES, under the
    same authority a competing `custody_act`, cleanup or removal commits under.
    """
    import uuid

    from .store import _recorded, manager_signature

    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        for ordinal, record in standing_cleanup(control, assignment_id):
            held = _admitted_cleanup_document(control, assignment_id, ordinal,
                                              record) or {}
            standing = held.get("settlement") or {}
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: cleanup {ordinal} of this attempt's roots was "
                f"admitted under operation {name_value(standing.get('operation'))} and has "
                f"recorded no settlement, so these roots belong to that cleanup until it "
                f"settles -- creating them now would hand it material to delete")
        outstanding = standing_removal(control, assignment_id)
        if outstanding:
            ordinal, _ = outstanding[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: removal {ordinal} of this attempt's roots was admitted "
                f"and has recorded no completion, so whether that removal is still running "
                f"or stopped half way is unknown -- these roots are not created again until "
                f"it is reconciled")
        held = _journal_holds(control, assignment_id)
        if held:
            which, episode = held[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: this attempt's {which} root carries recorded custody "
                f"episode {episode.get('episode')!r}, and the two roots of one attempt "
                f"overlap, so neither is free while either is held")
        ordinal = 1
        while control.operation_record(
                _allocation_id(assignment_id, ordinal)) is not None:
            ordinal += 1
        document = {"attempt_id": assignment_id, "ordinal": ordinal,
                    "act": what, "owner": uuid.uuid4().hex}
        control._record(
            _allocation_id(assignment_id, ordinal), ALLOCATION_KIND,
            manager_signature(ALLOCATION_KIND, document),
            "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def _completed_allocation(control, assignment_id, owned):
    """Close the allocation's window, on success AND on failure.

    DELIBERATELY NOT "UNCERTAINTY IS HELD", and the asymmetry with a removal is the point.
    An interrupted REMOVAL stays held because the journal can only ever be behind the
    filesystem for a deletion and nobody can tell what is already gone. An interrupted
    CREATION leaves at most a partial tree that `makedirs(exist_ok=True)` is already
    recoverable over -- and holding its window open would block this attempt's cleanup for
    good, trading a permanent failure for a transient one.
    """
    from .store import manager_signature

    document = {"attempt_id": assignment_id, "ordinal": owned["ordinal"],
                "owner": owned["owner"]}
    control.transact(_allocation_complete_id(assignment_id, owned["ordinal"]),
                     ALLOCATION_COMPLETE_KIND,
                     manager_signature(ALLOCATION_COMPLETE_KIND, document),
                     lambda _connection: dict(document))


# W270664 -- THE TOKEN BATON, BOUND TO THE RUNNING CONTAINER.
#
# Owner ruling OWNER-TOKEN-BATON-20260926.md and its Docker clarification (T270664/274827):
# "active token is tied to an active Docker image, if token expires, active Docker is shut
# down so it can be safely reset". The running object is the CONTAINER; the image is its
# immutable launch input.
#
# WHAT THIS ADDS TO THE ACCEPTED ADMISSION RECORD rather than beside it, because the ruling
# says to map existing claims to the contract and reuse what satisfies it. The removal
# ownership already bound the conflict domain (this attempt's overlapping roots), the
# operation and an owner identity, atomically, in one short transaction, before any effect.
# What it did NOT carry is the three things that make it a BATON:
#
#   * a GENERATION, so one attempt's successive removals are ordered and a stale holder is
#     nameable rather than merely wrong;
#   * an EXPIRY, so an abandoned holder does not own the roots forever;
#   * the CONTAINER, bound when it exists -- which is NOT at acquisition. Reserve happens
#     before launch, so the token is acquired first and the container is bound to that exact
#     token afterwards, and the delayed/unknown-launch exclusion is preserved meanwhile.
#
# AND EXPIRY IS NOT PERMISSION TO REPLACE. An expired token begins REVOCATION: the exact
# bound container is stopped OUTSIDE every transaction, its termination is POSITIVELY
# CONFIRMED, and only then may a new generation be admitted. A stop whose outcome is unknown,
# or a surviving writable helper, keeps the roots held -- issuing a stop is not cessation.
# HOW LONG A REMOVAL MAY HOLD THE ROOTS BEFORE ITS TOKEN EXPIRES. Generous on
# purpose: a removal that takes longer than this has stopped being a removal and
# has become something an operator reconciles through revocation.
TOKEN_SECONDS = 900
TOKEN_BOUND_KIND = "workspace.removal-token-bound"
TOKEN_REVOKED_KIND = "workspace.removal-token-revoked"
TOKEN_CEASED_KIND = "workspace.removal-token-ceased"


def _token_bound_id(assignment_id, ordinal):
    return f"{TOKEN_BOUND_KIND}:{assignment_id}:{ordinal}"


def _token_revoked_id(assignment_id, ordinal):
    return f"{TOKEN_REVOKED_KIND}:{assignment_id}:{ordinal}"


def _token_ceased_id(assignment_id, ordinal):
    return f"{TOKEN_CEASED_KIND}:{assignment_id}:{ordinal}"


def _recorded_document(control, operation_id, kind):
    """A committed record's own document, read back through `replay`."""
    found = control.operation_record(operation_id)
    if found is None:
        return None
    _, document = control.replay(operation_id, found["signature"], kind=kind)
    return document


def token_of(control, assignment_id, ordinal):
    """This ownership's token as it now stands: its terms, container and revocation.

    Assembled from the records rather than from anything a caller holds. `expired` is
    decided against the store's own clock, which is the instant source the journal stamps
    its rows from -- a module reaching for wall time here would be answering from a
    different clock than the evidence.
    """
    owned = _recorded_document(control, _removal_ownership_id(assignment_id, ordinal),
                              REMOVAL_OWNERSHIP_KIND) or {}
    token = dict(owned.get("token") or {})
    if not token:
        return None
    bound = _recorded_document(control, _token_bound_id(assignment_id, ordinal),
                              TOKEN_BOUND_KIND)
    token["container"] = (bound or {}).get("container")
    token["revoked"] = _recorded_document(
        control, _token_revoked_id(assignment_id, ordinal), TOKEN_REVOKED_KIND) is not None
    ceased = _recorded_document(control, _token_ceased_id(assignment_id, ordinal),
                               TOKEN_CEASED_KIND)
    token["ceased"] = ceased is not None
    token["expired"] = control._now() >= token["expires_at"]
    return token


def bind_token_container(control, assignment_id, ordinal, owned, container):
    """Bind the eventual container to THIS exact token, after the reservation.

    NOT AT ACQUISITION, and that is the owner's own instruction: "Do not assume a container
    ID exists at initial reservation: preserve reserve-before-launch and uncertain/delayed
    launch exclusion while binding the eventual container to that exact token." So the roots
    are already owned and excluded when this runs; this records WHICH running object the
    token's expiry will have to stop.

    ONE BINDING PER TOKEN, conditioned on the owner. A stale holder cannot bind a container
    to a generation it no longer owns, which is what would otherwise let an expiry revocation
    stop somebody else's container.
    """
    from .store import manager_signature

    container = boundaries.text(container, "a bound container identity")
    document = {"attempt_id": assignment_id, "ordinal": ordinal,
                "owner": owned["owner"],
                "generation": owned["token"]["generation"],
                "container": container}

    def binding(_connection):
        held = _recorded_document(control, _removal_ownership_id(assignment_id, ordinal),
                                 REMOVAL_OWNERSHIP_KIND) or {}
        if held.get("owner") != owned["owner"]:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"binding a container to removal token {ordinal} of attempt "
                f"{name_value(assignment_id)} was asked by an act that does not own it")
        return dict(document)

    return control.transact(_token_bound_id(assignment_id, ordinal), TOKEN_BOUND_KIND,
                            manager_signature(TOKEN_BOUND_KIND, document), binding)


def revoke_expired_token(control, assignment_id, ordinal, stop):
    """Begin revocation, STOP THE EXACT BOUND CONTAINER, and confirm it has ceased.

    THE ORDER IS THE CONTRACT, and every external step is outside every transaction:

      1. RECORD THE REVOCATION (database). From here no replacement generation is admitted
         until cessation is recorded, so an expiry can never be mistaken for permission.
      2. STOP AND CONFIRM (external, no lock held). `stop` is the controlled boundary: it is
         handed the exact container this token was bound to and answers whether that
         container is positively gone, along with whether any writable helper survives.
      3. RECORD THE CESSATION (database) -- and ONLY on a positive answer.

    UNKNOWN HOLDS. A stop whose outcome the boundary cannot establish, or a surviving
    writable helper, records NO cessation: the roots stay held, a new generation stays
    refused, and an operator reconciles. Issuing a stop request is not cessation, and this
    function's answer is the record, not the request.
    """
    from .store import manager_signature

    token = token_of(control, assignment_id, ordinal)
    if token is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"removal {ordinal} of attempt {name_value(assignment_id)} carries no token to "
            f"revoke")
    if not token["expired"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"removal token {ordinal} of attempt {name_value(assignment_id)} has not expired; "
            f"a live token is returned by its holder, not revoked by somebody else")
    if not token["revoked"]:
        revocation = {"attempt_id": assignment_id, "ordinal": ordinal,
                      "generation": token["generation"],
                      "container": token["container"]}
        control.transact(_token_revoked_id(assignment_id, ordinal), TOKEN_REVOKED_KIND,
                         manager_signature(TOKEN_REVOKED_KIND, revocation),
                         lambda _connection: dict(revocation))
    if token["ceased"]:
        return token_of(control, assignment_id, ordinal)
    # THE EXTERNAL STEP, WITH NOTHING HELD. A container that was never bound is not a
    # container this manager may assume is gone: the boundary is still asked, because a
    # token can expire between its acquisition and its launch and the launch may have
    # happened without the binding committing.
    answer = boundaries.document(
        stop(token["container"]), "a container cessation answer",
        required=("stopped", "helpers"))
    if not answer["stopped"] or answer["helpers"]:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"removal token {ordinal} of attempt {name_value(assignment_id)} is revoked and "
            f"its container {name_value(token['container'])} is not positively gone "
            f"(stopped={answer['stopped']!r}, surviving helpers="
            f"{answer['helpers']!r}); these roots stay held and no new generation is "
            f"admitted, because a stop request is not cessation")
    cessation = {"attempt_id": assignment_id, "ordinal": ordinal,
                 "generation": token["generation"],
                 "container": token["container"],
                 "confirmed_at": control._now()}
    control.transact(_token_ceased_id(assignment_id, ordinal), TOKEN_CEASED_KIND,
                     manager_signature(TOKEN_CEASED_KIND, cessation),
                     lambda _connection: dict(cessation))
    return token_of(control, assignment_id, ordinal)


def _token_terms(control, assignment_id, ordinal, execution, seconds):
    """This generation's terms, stamped from the store's own clock."""
    taken = control._now()
    return {"execution": boundaries.text(execution, "a token execution identity"),
            "generation": ordinal,
            "acquired_at": taken,
            "expires_at": boundaries.deadline(taken, seconds,
                                              "a removal token expiry")}


def _removal_ownership_id(assignment_id, ordinal):
    return f"{REMOVAL_OWNERSHIP_KIND}:{assignment_id}:{ordinal}"


def _removal_complete_id(assignment_id, ordinal):
    return f"{REMOVAL_COMPLETE_KIND}:{assignment_id}:{ordinal}"


def standing_removal(control, assignment_id):
    """The removal ownership records of this attempt that carry no completion.

    W270664 F2. THE RECIPROCAL HALF OF THE EXCLUSION, and review 2026-09-26T06:21:32Z is
    why it exists: `custody._claim_episode`'s claiming callback re-reads custody overlap
    under its own `BEGIN IMMEDIATE` and reads NOTHING about a removal, so an ownership
    record on its own would have excluded nothing -- a hold could still commit while the
    tree was coming off the disk. Every act that would touch these roots asks this, under
    the same database authority, BEFORE its effect.

    READ BY DERIVED IDENTITY rather than by scanning the journal table, which is this
    build's rule for operation records: another deployment's rows are invisible to it.

    AN OWNERSHIP WITH NO COMPLETION IS STANDING, whatever happened to the caller that
    took it. That is the held state an interrupted removal must leave behind: nothing here
    guesses that a vanished remover finished.
    """
    standing = []
    ordinal = 1
    while True:
        found = control.operation_record(
            _removal_ownership_id(assignment_id, ordinal))
        if found is None:
            return standing
        if control.operation_record(
                _removal_complete_id(assignment_id, ordinal)) is None:
            standing.append((ordinal, found))
        ordinal += 1


def _journal_holds(control, assignment_id):
    """Both roots' STANDING custody holds, as a database-only reading.

    BOTH ROOTS, ALWAYS, because `custody._derived_root` puts the result root INSIDE the
    workspace: a hold on either covers a tree the other contains. This reads only the
    journal, so it is safe inside the admission transaction -- `refuse_if_held` is the
    fuller check and reaches `realpath`, which is why IT runs outside.

    A CLEARED EPISODE IS HISTORY, NOT A HOLD, and review 2026-09-26T06:34:57Z caught me
    treating it as one: my first cut returned every recorded episode, so a root whose
    uncertainty an operator had already reconciled could NEVER be removed -- a permanent
    false refusal, which is a worse failure than the one this correction is about. The
    predicate is `custody._standing_overlap`, the accepted one `_claim_episode` itself uses;
    it walks both roots and answers the oldest UNCLEARED episode, so a cleared history, a
    mixed history and no history all answer the same as each other and only a live hold
    refuses. Borrowing that predicate rather than writing a second one is deliberate: two
    readers of the same fact are two chances to disagree about it.
    """
    from . import custody

    standing = custody._standing_overlap(control, assignment_id, "workspace")
    if standing is None:
        return []
    # THE EPISODE NAMES ITS OWN ROOT, and this reports THAT rather than a default.
    # Review 2026-09-26T06:39:23Z: my fallback said "workspace" whenever the field was
    # missing, so a RESULT-root hold could have been diagnosed as a workspace one -- a
    # refusal that names the wrong resource is a refusal an operator cannot act on.
    # `custody_holds` records `("root", which)` for every episode, so an episode without
    # one is a malformed record and is refused as such instead of being relabelled.
    # MEASURED, and it corrected my own assumption: not every episode document this reader
    # returns carries a `root` field -- the standing episode from `_record_hold` does not --
    # so demanding one turned a correct refusal into an integrity error. What matters is that
    # the diagnostic never NAMES the wrong root, so an unlabelled episode is reported as
    # covering the overlapping pair instead of being defaulted to "workspace", which is what
    # review 2026-09-26T06:39:23Z flagged.
    # THE ROOT IS standing["held"]["root"], which review 2026-09-26T06:44:15Z had to tell me
    # after two wrong guesses: `_standing_overlap` answers {"held": <episode>, "episode": n},
    # so the top-level document has no `root` at all. My first cut defaulted the name to
    # "workspace" -- so a RESULT-root hold could be diagnosed as a workspace one -- and my
    # second refused a missing top-level field as malformed, which turned a correct refusal
    # into an integrity error. Reading the field that actually carries it fixes both.
    held = standing.get("held") or {}
    return [(held.get("root", "workspace-or-result"), held or standing)]


def _pinned_home(storage, assignment_id):
    """This attempt's home as an OBJECT -- device and inode -- or absence.

    W270664 F2. A name is not an object: the audit's own alias findings are about exactly
    that, and a removal authorized for one inode must not be performed against another.
    Absence is answered rather than refused, because an absent home has its own accepted
    answer at the caller.
    """
    home = os.path.join(_real(storage, "the manager's workspace storage"),
                        assignment_id)
    try:
        observed = os.lstat(home)
    except OSError:
        return None
    return (observed.st_dev, observed.st_ino)


def _still_the_pinned_home(storage, assignment_id, pinned, what):
    """Refuse unless the home is still the object the ownership was granted for.

    WHAT THIS DOES NOT DO, AND I CLAIMED OTHERWISE. Review 2026-09-26T06:54:02Z swapped the
    home AFTER this check answered and the production removal then deleted the substitute's
    marker. So this is a TIME-OF-CHECK comparison, not a binding: it catches a replacement
    that happened BEFORE the effect starts and nothing that happens after. My previous
    handoff said the removal was "bound to an object, not to a name", and that was wrong --
    a stat cannot bind anything, because the deletion that follows still resolves a
    PATHNAME.

    IT IS KEPT because it closes the admission-to-effect interval, which is a real interval
    and has its own case. What it is NOT is the object binding the correction still owes:
    that needs the deletion, the traversal and the final removal performed RELATIVE TO A
    DIRECTORY DESCRIPTOR opened once and fstat-verified against the pin -- which is what
    `discard_execution_roots` already does for the execution roots and what `_remove` does
    not yet do for the home. The next claim owes that, and until then this comparison is
    described here as exactly what it is.
    """
    if _pinned_home(storage, assignment_id) != pinned:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{what} was admitted for this attempt's home as one object and the pathname "
            f"now names a different one; a removal is performed on the object its "
            f"authority was granted for and not on whatever answers the name")


def _durably_in_use(control, assignment_id):
    """Whether durable state says an attempt's roots are in use, as a DATABASE-ONLY read.

    W270664 F2, review 2026-09-26T08:02:18Z. Settling the adoption window at the grant binding
    was not a handover, because the removal read NOTHING that changes when a grant is bound.
    This is that missing target: the very facts the grants themselves test --
    `_writer_grant` is a writer ACTIVE for the attempt, `_review_grant` is an attachment ACTIVE
    for it -- read here so the removal refuses for as long as they hold, which is precisely as
    long as a grant could be live.

    PURE SQL OVER THIS STORE'S OWN TABLES, so it is safe inside the admission transaction and
    adds no import of the lifecycle module that owns those predicates. The removal already has
    the store; review 08:02:18Z says so, and it was right that nothing new is needed to reach
    these rows.
    """
    connection = control._connection
    writing = connection.execute(
        "SELECT writer_id FROM line_writers "
        "WHERE runtime_attempt_id = ? AND state = 'active' LIMIT 1",
        (assignment_id,)).fetchone()
    if writing is not None:
        return ("an active line writer", writing[0])
    reviewing = connection.execute(
        "SELECT attachment_id FROM review_attachments "
        "WHERE runtime_attempt_id = ? AND state = 'active' LIMIT 1",
        (assignment_id,)).fetchone()
    if reviewing is not None:
        return ("an active review attachment", reviewing[0])
    return None


def _admitted_removal(control, assignment_id, what, pinned=None, under=None,
                      execution=None, seconds=TOKEN_SECONDS):
    """Take removal ownership of this attempt's roots in ONE short transaction.

    W270664 F2, owner 270664: "all external I/O occurs outside DB locks", and review
    2026-09-26T06:21:32Z: "A completion-time hold check alone is too late." So the
    exclusion is won BEFORE any effect and without touching a filesystem.

    WHAT THIS TRANSACTION DOES, all of it database work: re-reads both roots' custody
    holds from the journal, refuses if any stands, refuses if another removal ownership of
    this attempt is still standing, and commits this act's ownership. A hold that commits
    first wins here; a hold that arrives afterwards is refused by the reciprocal check in
    `custody._claim_episode`, which reads `standing_removal` under its own lock.

    THE RAW SHORT TRANSACTION IS THIS BUILD'S OWN PRECEDENT -- `create_line` and
    `review_cycles._admitted_execution` take `BEGIN IMMEDIATE` and commit by hand -- and it
    is necessary rather than stylistic: `transact` is keyed by an operation identity and
    replays, so it cannot make a fresh decision, and the decision here must be fresh.

    ANSWERS the ordinal and token this act owns. The caller performs its removal OUTSIDE
    every transaction and then completes against exactly this ownership.
    """
    import uuid

    from .store import _recorded, manager_signature

    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        held = _journal_holds(control, assignment_id)
        if held:
            which, episode = held[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: this attempt's {which} root carries recorded "
                f"custody episode {episode.get('episode')!r}, and the two roots of one "
                f"attempt overlap, so neither is free while either is held")
        # DURABLE USE FIRST, because it outlives any window: while a writer or an attachment
        # is ACTIVE for this attempt, its roots are in use and no removal is admitted -- which
        # is what makes the grant binding a real handover rather than a dropped exclusion.
        in_use = _durably_in_use(control, assignment_id)
        if in_use is not None:
            what_holds, which = in_use
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: this attempt's roots are held by {what_holds} "
                f"({name_value(which)}), so they are in use and are not removed until that "
                f"is no longer true")
        competing = _competing_allocation(control, assignment_id, what)
        if competing is not None:
            raise ContractRefusal("refused", "precondition", competing)
        adopting = standing_adoption(control, assignment_id)
        if adopting:
            ordinal, _ = adopting[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: adoption {ordinal} of this attempt's roots was "
                f"admitted in this same journal and has recorded no completion, so the "
                f"roots are in use; the removal is not admitted while it stands")
        standing = standing_removal(control, assignment_id)
        if standing:
            ordinal, _ = standing[0]
            # W270664, the owner's token contract: AN OUTSTANDING BATON IS WHAT REFUSES, and
            # its expiry is a different sentence from its life.
            held_token = token_of(control, assignment_id, ordinal)
            if held_token is None or not held_token["expired"]:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: removal {ordinal} of this attempt's roots holds an "
                    f"outstanding token (generation "
                    f"{(held_token or {}).get('generation')}, execution "
                    f"{name_value((held_token or {}).get('execution'))}) and has recorded no "
                    f"completion, so whether that removal is still running or stopped half "
                    f"way is unknown -- an uncertain removal is held rather than repeated")
            if not held_token["ceased"]:
                # EXPIRY IS NOT PERMISSION. The old holder's container must be stopped and
                # its termination positively confirmed -- `revoke_expired_token` -- before any
                # replacement generation is admitted. Until then these roots stay held, which
                # is the owner's "unknown prior effects remain held" applied to the exact
                # running object rather than to a presumption about it.
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: removal token {ordinal} of this attempt's roots "
                    f"EXPIRED at {name_value(held_token['expires_at'])} and its cessation is "
                    f"not established -- container "
                    f"{name_value(held_token['container'])}, revoked="
                    f"{held_token['revoked']!r}. Expiry begins revocation and is not "
                    f"permission to replace: the bound container is stopped and its "
                    f"termination confirmed before a new generation is admitted")
        # W270664 F2, review 2026-09-26T10:07:07Z: A REMOVAL ACTING FOR A CLEANUP MUST
        # STILL OWN THAT CLEANUP, proved HERE, in the transaction that authorizes the
        # deletion, rather than when the cleanup began.
        #
        # THE DEFECT THIS CLOSES, exactly as their probe staged it: a first cleanup
        # admitted and paused before its removal; a second same-operation caller took the
        # admission, removed, and settled; an allocation then legitimately created fresh
        # roots; and the first caller resumed and deleted them. Every earlier check had
        # already passed -- nothing was standing, because the second caller had tidied up
        # after itself. The fact that was true and unread is that the first caller's own
        # authority had been taken away from it.
        if under is not None:
            owed = under.get("ordinal")
            mine = under.get("owner")
            standing_admission = {one: record for one, record
                                  in standing_cleanup(control, assignment_id)}
            if owed not in standing_admission:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: the cleanup admission {owed} it was authorized "
                    f"by is no longer standing, so this deletion would act on roots its "
                    f"own cleanup has already settled -- and anything allocated since is "
                    f"newer than the authority that would remove it")
            held_admission = _admitted_cleanup_document(
                control, assignment_id, owed, standing_admission[owed]) or {}
            current, _generation = _current_cleanup_owner(
                control, assignment_id, owed, held_admission.get("owner"))
            if current != mine:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} is refused: cleanup admission {owed} of this attempt's roots "
                    f"has been taken over by a later act, so this caller no longer holds "
                    f"the authority its removal would be performed under")
        ordinal = 1
        while control.operation_record(
                _removal_ownership_id(assignment_id, ordinal)) is not None:
            ordinal += 1
        document = {"attempt_id": assignment_id, "ordinal": ordinal,
                    "act": what, "owner": uuid.uuid4().hex,
                    "home_object": None if pinned is None else list(pinned),
                    # THE BATON'S OWN TERMS, acquired in this same short transaction as the
                    # ownership -- eligibility, replay and acquisition are one atomic
                    # decision, which is the contract's first clause. The container is NOT
                    # here: it does not exist yet at reservation, and `bind_token_container`
                    # binds the eventual one to this exact generation.
                    "token": _token_terms(control, assignment_id, ordinal,
                                          execution or getattr(control, "incarnation", None)
                                          or "unnamed-execution", seconds)}
        control._record(
            _removal_ownership_id(assignment_id, ordinal),
            REMOVAL_OWNERSHIP_KIND,
            manager_signature(REMOVAL_OWNERSHIP_KIND, document),
            "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def _completed_removal(control, assignment_id, owned, value, what):
    """Record what the removal did, conditioned on the ownership it was authorized by.

    W270664 F2. The removal ran outside every transaction, so this one re-reads in PURE
    SQL that the ownership this act took is still the record it committed and that no
    custody hold arrived for either root while the tree was coming off the disk. Either
    way the effect has already happened -- the journal can only ever be behind the
    filesystem for a removal -- so what this protects is the ATTRIBUTION: a completion is
    written for the act that performed it and for no other.

    ONE ACT, ONE ANSWER, NO REPLAY OF SOMEBODY ELSE'S. The ordinal is this act's own, so a
    later removal over an already-empty home records its own completion and answers its own
    truth rather than being handed this one.
    """
    from .store import manager_signature

    ordinal = owned["ordinal"]
    document = {"attempt_id": assignment_id, "ordinal": ordinal,
                "owner": owned["owner"], "removed": _summary(value)}
    signature = manager_signature(REMOVAL_COMPLETE_KIND, document)

    def completing(_connection):
        recorded = control.operation_record(
            _removal_ownership_id(assignment_id, ordinal))
        if recorded is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s removal ownership {ordinal} is no longer recorded, so this "
                f"act cannot be attributed to the authority it was performed under")
        _, held_by = control.replay(
            _removal_ownership_id(assignment_id, ordinal), recorded["signature"],
            kind=REMOVAL_OWNERSHIP_KIND)
        if held_by is None or held_by.get("owner") != owned["owner"]:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"{what}'s removal ownership {ordinal} names another act, so this "
                f"completion would attribute a removal to an authority that did not "
                f"perform it")
        arrived = _journal_holds(control, assignment_id)
        if arrived:
            which, episode = arrived[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} removed this attempt's roots and a custody hold for its "
                f"{which} root was recorded at episode {episode.get('episode')!r} while "
                f"it ran; the removal is recorded as unresolved rather than completed, "
                f"because a hold that arrived during a deletion is exactly the state an "
                f"operator has to reconcile")
        return dict(document)

    return control.transact(_removal_complete_id(assignment_id, ordinal),
                            REMOVAL_COMPLETE_KIND, signature, completing)


def _refuse_nested_removal(control, what):
    """Refuse a removal asked inside an open transaction BEFORE any filesystem call.

    W270664 F2, review 2026-09-26T08:33:54Z. The refusal existed but sat behind the entry's
    preflight, so a nested caller still cost eleven `lstat` calls and a `stat` under its
    transaction before being told no -- I/O under a database lock, which is the whole defect,
    performed on the way to refusing it. This runs FIRST at both public entries.
    """
    connection = getattr(control, "_connection", None)
    if connection is not None and getattr(connection, "in_transaction", False):
        _denied(f"{what} was asked from inside an open database transaction; a removal takes "
                f"its own ownership record and performs its effect with no lock held, so it is "
                f"not performed under somebody else's transaction -- and nothing is inspected "
                f"on the way to saying so")


def _serialized_removal(control, storage, assignment_id, what, removing,
                        under=None):
    """Check the holds and remove UNDER THE SAME WRITE LOCK R1's claim takes.

    W257624 R3, review 2026-09-25T03-01-27Z: a query followed by an unprotected
    mutation is not a guard. Between `refuse_if_held` answering clean and the
    tree coming off the disk, a concurrent `custody_act` could commit a hold for
    exactly that root -- and R1 deliberately commits BEFORE its engine effect,
    so the window is real rather than theoretical.

    SO THE SERIALIZING AUTHORITY IS THE ONE THAT ALREADY EXISTS.
    `ControlStore.transact` takes `BEGIN IMMEDIATE` and `_claim_episode` runs
    inside it, so performing the hold read AND the removal inside one transact
    puts them on the same lock: a racing claim either commits first, and this
    reads it and refuses, or it waits until the removal has finished and the
    tree it would hold is already gone. There is no interval in between.

    THE ORDER INSIDE THE LOCK IS CHECK-THEN-EFFECT, and the check is repeated
    there rather than trusted from outside it -- the outer call is an early
    refusal for the ordinary case, and this one is the decision.

    THE FAILURE WINDOW, STATED. A crash after the removal and before the
    journal commits leaves the tree gone and no record of this act; the journal
    is then behind the filesystem, which is the direction this build already
    tolerates for removals (`discard_workspace` answers `False` for an absent
    home rather than refusing). A crash BEFORE the removal leaves both
    unchanged. What cannot happen is a removal concurrent with a hold commit.
    """
    from .store import manager_signature

    # THE OPERAND IS TYPED BEFORE THE LOCK IS TAKEN, for `transact`'s own
    # stated reason: a capability that cannot be called would fault inside the
    # transaction, which is the one place a fault costs more than a refusal.
    # Found by the matrix -- checking the store only inside the callback meant
    # `control.transact` was reached first and raised `AttributeError`.
    if control is None or not hasattr(control, "transact") \
            or not hasattr(control, "operation_record"):
        _denied(f"{what} needs this manager's own control store to check the "
                f"custody holds that would refuse it; an act that cannot ask "
                f"is not one this boundary lets through")
    # A READ IS NEVER REMOVAL AUTHORITY, AND `in_transaction` IS NOT A LOCK.
    #
    # W257624 R3 [P1], review 2026-09-25T03-13-33Z. My nested-transaction
    # shortcut asked `connection.in_transaction` and went straight to the
    # effect -- which skipped `transact` and therefore skipped the refusal
    # `transact` makes FIRST: a read-only manager or a read snapshot performs no
    # action. A stale snapshot then read "cleared" for a root whose new hold a
    # writer had already committed, and the removal proceeded.
    #
    # `in_transaction` is true of a READ transaction too. It says a statement is
    # open on this connection, not that this connection holds the write lock and
    # certainly not that the caller is authorized to mutate.
    #
    # SO THE REFUSAL COMES FIRST, unconditionally, and the shortcut is narrowed
    # to what it was actually for: `intake`'s cleanup already holds a genuine
    # write action on this connection, and a nested `BEGIN IMMEDIATE` there is
    # an error rather than a second lock.
    if getattr(control, "_readonly", False) or getattr(control, "_snapshots",
                                                       None):
        _denied(f"{what} was asked of a read-only manager or a read snapshot; "
                f"a snapshot answers what it was opened over and holds no "
                f"write lock, so it can neither see a hold committed since nor "
                f"authorize removing the resource one protects")
    # W270664 F2: THE NESTED SHORTCUT IS GONE, and a caller inside a write transaction is
    # REFUSED rather than served.
    #
    # It existed for exactly one caller -- `intake._settle`, which removed from inside its own
    # `runtime.destroy` transaction -- and that call now happens in `authorize_cleanup` with no
    # lock held. So there is no legitimate caller left, and serving one would be serving a
    # removal that cannot take its ownership record, cannot be held when interrupted, and holds a
    # database lock across a tree walk: every property this correction exists to establish,
    # discarded for the convenience of a nested call.
    connection = getattr(control, "_connection", None)
    if connection is not None and getattr(connection, "in_transaction", False):
        _denied(f"{what} was asked from inside an open database transaction; a removal takes "
                f"its own ownership record and performs its effect with no lock held, so it is "
                f"not performed under somebody else's transaction")
    # W270664 F2: PREPARE OUTSIDE, ADMIT IN THE DATABASE, REMOVE OUTSIDE, COMPLETE IN THE
    # DATABASE. Owner 270664 forbids external I/O under a database lock, and review
    # 2026-09-26T06:21:32Z forbids buying that with a completion-time check: the exclusion
    # is won BEFORE the effect, by an ownership record, and `custody._claim_episode` reads
    # that record under its own lock so the exclusion is mutual rather than one-sided.
    #
    # THE FULL PREFLIGHT RUNS FIRST AND OUTSIDE EVERYTHING, because it reaches `realpath`
    # and the filesystem: `refuse_if_held` is the early refusal for the ordinary case and
    # the admission below re-reads the journal's holds under its lock, which is the part
    # that must be serialized.
    refuse_if_held(control, storage, assignment_id, what, under)
    # THE OBJECT IS PINNED BEFORE ADMISSION AND COMPARED BEFORE THE EFFECT -- AND THAT IS
    # NOT YET A BINDING. Review 2026-09-26T06:54:02Z proved the gap by swapping the home
    # after the comparison answered, so see `_still_the_pinned_home` for what this does and
    # does not establish. The comparison stays because the interval before the effect is
    # real; the descriptor-relative removal the full property needs is still owed.
    #
    # W270664 F2, review 2026-09-26T06:48:32Z. The ownership record authorized a removal of
    # "this attempt's roots" by NAME, and the effect then runs outside every lock -- so a
    # home replaced in that interval would have been deleted under an authority granted for
    # a different object. `_real` already refuses a symlinked home at entry; this closes the
    # interval AFTER that proof, which is the same reason `discard_execution_roots` opens a
    # directory descriptor instead of trusting a pathname.
    pinned = _pinned_home(storage, assignment_id)
    owned = _admitted_removal(control, assignment_id, what, pinned, under)
    _still_the_pinned_home(storage, assignment_id, pinned, what)
    # THE EFFECT, WITH NO TRANSACTION OPEN. An exception here leaves the ownership standing
    # with no completion, which is the HELD state: `standing_removal` reports it, this
    # entry refuses to repeat it, and custody refuses to hold over it.
    value = removing()
    _completed_removal(control, assignment_id, owned, value, what)
    return value


def _summary(value):
    """A JSON-able account of what a removal answered, for the journal."""
    if isinstance(value, (list, tuple)):
        return [str(one) for one in value]
    return bool(value)


def _database_place(store):
    """The file this store is a handle on, asked of the connection itself.

    W270664 F2. Not a path a caller supplies and not a configuration: `PRAGMA
    database_list` is the connection's own account of what it is open on, so the reader
    opened from it below is certainly the same journal. An in-memory or unnameable
    database answers `None`, and an allocation that needs a reader for one is refused
    rather than served from somewhere else.
    """
    try:
        for _sequence, name, place in store._connection.execute(
                "PRAGMA database_list").fetchall():
            if name == "main" and place:
                return place
    except Exception:
        return None
    return None


@contextlib.contextmanager
def _asking_control(workspace_group, control):
    """A control store USABLE ON THIS THREAD for the exclusion reads, or a REFUSAL.

    W270664 F2. THE CLOSED AND OFF-THREAD CONTRACT, stated here because review
    2026-09-26T11:19:15Z requires it recorded rather than implied:

      * Allocation asks this manager's journal whether a cleanup, a removal or a custody
        hold owns these roots. It asks through the control it was given -- the explicit
        `control=` operand, or the store bound into the workspace group that minted the
        capability.
      * A SQLite connection belongs to the thread that opened it and can be closed. If
        the given control's connection cannot be used HERE, this refuses. It does not
        skip the question, and it no longer reopens the database on the caller's behalf.
      * So a caller allocating from a thread that does not own the store's handle must
        pass a control it can use on that thread. The seven tool call sites already name
        their journal, and a fresh `ControlStore.open` is each handle's own authority
        rather than a claim about somebody else's.

    WHY THE REOPEN IS GONE, in the order it was taken apart, because three rejected
    versions are worth more to the next reader than the conclusion alone:

      1. A `stat` of the PATHNAME before the open proved nothing about what the open got
         -- the database was swapped in between (review 10:53:09Z).
      2. A process-wide scan for a descriptor naming that pathname was satisfied by an
         unrelated descriptor a witness held on the original file, and its `connection`
         argument was never used at all (review 11:04:20Z).
      3. Attribution by CREATION -- only descriptors that appeared across the open -- was
         defeated by opening an unrelated descriptor on the original file INSIDE that
         window, after the replacement open and the pathname restore. An in-process lock
         serializes only the opens that cooperate with it; nothing serializes arbitrary
         descriptor creation (review 11:19:15Z).

    Each version accepted a REPLACEMENT journal's answer for the selected one, and each
    time I described it as bound identity. The remaining candidate was a durable
    per-database identity; it is unselected, and it would not settle a byte-for-byte
    clone occupying the same reachable path. So the honest behaviour is the refusal, and
    the caller supplies the authority.
    """
    import sqlite3

    # THE PROBE IS A PRAGMA AND NOT A `SELECT`. Measured: `SELECT 1` made
    # `test_boundary_inventory`'s SQL reader fail with "a SELECT with no FROM", and because
    # every one of its projections derives from that read, ONE unparseable statement
    # cascaded into forty-two failures. The question here is "can this connection be used
    # from this thread", which a PRAGMA answers exactly as well.
    #
    # THE PROBE IS ALSO NOT THE YIELD. Wrapping the caller's block in this `try` would
    # swallow a `ProgrammingError` raised by the block itself.
    usable = True
    try:
        control._connection.execute("PRAGMA database_list").fetchall()
    except sqlite3.ProgrammingError:
        usable = False
    if usable:
        yield control
        return
    _denied(f"allocating an execution workspace has to ask this manager's journal whether "
            f"a cleanup, a removal or a custody hold owns these roots, and the control it "
            f"was given cannot be used from this thread -- its connection is closed, or it "
            f"belongs to another thread. The database at "
            f"{name_value(getattr(control, 'database', None))} is not reopened on this "
            f"caller's behalf: a reopened handle cannot be proved to be the journal that "
            f"control was opened on, and accepting one that cannot be proved is how a "
            f"replaced journal answered for the original three times over. A caller "
            f"allocating from another thread passes a control it can use there")


def _speaks_for(control, storage):
    """Whether this journal has authority over this storage tree.

    W270664 F2. The comparison `refuse_if_held` makes before it trusts its own answer,
    asked as a question instead of as a refusal -- because allocation may legitimately
    happen outside the configured store and must not be refused for it, while an act ON
    the configured store must not be served by a journal that cannot speak for it.

    THREE ANSWERS, NOT TWO, and review 2026-09-26T10:07:07Z is why: my first cut turned
    ANY `ContractRefusal` -- including a corrupt or disagreeing configuration -- into "no
    authority", which is a fail-open guard wearing a question's clothes. A deployment whose
    two accounts of the workspace store disagree is exactly when an act must be refused,
    not waved through.

      * `True`  -- this journal's configured store IS this tree.
      * `False` -- it is POSITIVELY another tree: both places were established and they
                   differ, which is the accepted "allocate wherever it may already write"
                   case and carries no protected resource.
      * a REFUSAL -- the authority could not be established at all. Nothing is skipped on
                     that path.

    A manager with NO configured store is the one absence that answers `False` rather than
    refusing: `_denied` there means the deployment never recorded a workspace store, so
    there is no configured tree this one could be, and no cleanup, removal or hold can name
    a root under a store that does not exist.
    """
    try:
        recorded = configured_workspace_storage(control).place
    except ContractRefusal as refused:
        if refused.category == "policy" and refused.code == "denied":
            return False
        raise
    return _real(recorded, "the manager's configured workspace store") == \
        _real(storage, "the manager's workspace storage")


def refuse_if_held(control, storage, assignment_id, what, under=None):
    """Refuse when a custody hold OR AN UNRESOLVED REMOVAL stands over what this act touches.

    W270664 F2, review 2026-09-26T07:21:42Z: the reciprocal exclusion belongs at the
    chokepoint every entry already calls rather than bolted onto each of them. Allocation,
    adoption and removal all pass through here, so one reading of the removal ownership
    covers reuse, adoption and a second removal -- and it is the same reading
    `custody._claim_episode` makes under its own lock, so neither side trusts only its own.

    AND IT IS WHAT COVERS THE FINAL ENTRY. Review 07:01:39Z was right that parent-fd plus
    stat plus `rmdir` is not exact-child authority; what makes the final removal safe is not
    a better stat but that nothing else may create, adopt or remove at that name while the
    ownership stands. That is an exclusion, not an inference.

    W257624 R3, owner 260900/262043. R1 stopped the custody act behind a
    standing hold and R2 decided what may lift one. This is every OTHER way the
    same directories are reached -- allocated again, adopted by a restarted
    manager, or removed.

    THE STORE IS REQUIRED, and that is the whole point of the operand. A
    configured module-level reader would be absent in exactly the deployments
    nobody remembered to wire, and a protection that is off by default is not
    one. The caller cannot skip this by forgetting.

    BOTH ROOTS, ALWAYS, BECAUSE THEY OVERLAP. The two custody roots of one
    attempt are not siblings: `custody._derived_root` puts the result root at
    `<home>/workspace/result-<attempt>`, INSIDE the workspace. So a hold on
    either one covers a tree the other contains or is contained by, and every
    entry here operates on the whole attempt home. Checking one root would
    leave the act free to remove the ancestor of a held descendant.

    ONE EXACT CLEARANCE RELEASES ONE EPISODE. This refuses while ANY episode of
    either root stands uncleared, so reconciling the result root's episode does
    not release a workspace hold that is still standing.

    THE READER IS THE JOURNAL'S. `custody_holds` is the one authority for
    whether a root is held; it is consulted rather than shadowed, so there is no
    second durable record of the same fact. The import is local because
    `custody` imports this module.
    """
    from . import custody

    boundaries.identity(assignment_id, "an assignment identity")
    if control is not None and hasattr(control, "operation_record"):
        # W270664 F2, review 2026-09-26T09:15:26Z: THE CLEANUP'S ADMISSION IS READ AT
        # THE SAME CHOKEPOINT, so allocation, adoption and a second removal are all
        # excluded for the whole span between a cleanup's eligibility and its ending
        # -- including the window after its removal completed, which is the window the
        # reviewer's probe allocated into.
        #
        # AND THE ADMITTED ACT IS NOT REFUSED BY ITS OWN ADMISSION. `settlement` is the
        # operation the caller is performing; the cleanup that owns the standing record
        # passes it and proceeds, everybody else is told whose act is outstanding.
        for ordinal, record in standing_cleanup(control, assignment_id):
            held = _admitted_cleanup_document(control, assignment_id, ordinal,
                                              record) or {}
            # THE EXEMPTION IS THE CURRENT OWNER'S, not every caller who can name the
            # same operation. Review 2026-09-26T10:07:07Z: two live executions of one act
            # matched on operation and signature, and the older one went on deleting.
            if under is not None and under.get("ordinal") == ordinal:
                current, _generation = _current_cleanup_owner(
                    control, assignment_id, ordinal, held.get("owner"))
                if current == under.get("owner"):
                    continue
            standing = held.get("settlement") or {}
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: cleanup {ordinal} of this attempt's roots was "
                f"admitted under operation {name_value(standing.get('operation'))} and "
                f"has recorded no settlement, so that cleanup is still between its "
                f"eligibility and its ending; these roots are not allocated, adopted "
                f"or removed by another act while it stands")
        outstanding = standing_removal(control, assignment_id)
        if outstanding:
            ordinal, _ = outstanding[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} is refused: removal {ordinal} of this attempt's roots was "
                f"admitted and has recorded no completion, so whether that removal is "
                f"still running or stopped half way is unknown -- these roots are not "
                f"reused, adopted or removed again until it is reconciled")
    if control is None or not hasattr(control, "operation_record"):
        _denied(f"{what} needs this manager's own control store to check the "
                f"custody holds that would refuse it; an act that cannot ask "
                f"is not one this boundary lets through")
    # W257624 R3 [P1], review 2026-09-25T02-49-44Z: THE STORE MUST OWN THE
    # RESOURCE, and asking the wrong journal is not asking.
    #
    # My first guard read holds from whatever store it was handed, so a caller
    # holding a DIFFERENT real store -- an empty one, say -- got "no holds" for
    # a genuinely held root and the removal proceeded. The operand being
    # required bought nothing, because the answer came from a journal with no
    # authority over this storage.
    #
    # SO THE BINDING IS PROVED BEFORE ANY EFFECT. `configured_workspace_storage`
    # is the deployment's own record and the only way to obtain one, so a store
    # whose configured root is not the root being acted on is a store that
    # cannot speak for it -- whatever it does or does not remember about holds.
    recorded = configured_workspace_storage(control).place
    if _real(recorded, "the manager's configured workspace store") != \
            _real(storage, "the manager's workspace storage"):
        _denied(f"{what} was asked of a manager whose configured workspace "
                f"store is {name_value(recorded)} while the act names "
                f"{name_value(storage)}; a journal with no authority over this "
                f"storage cannot report whether its resources are held, and "
                f"an absent answer from the wrong store is not an absence")
    for which in custody.CUSTODY_ROOTS:
        for one in custody.custody_holds(control, assignment_id, which):
            if one["cleared"]:
                continue
            _denied(
                f"{what} is refused: attempt {name_value(assignment_id)}'s "
                f"{which} root carries unreconciled uncertainty episode "
                f"{one['episode']!r}, whose helper "
                f"{name_value(one['held'].get('helper_identity'))} may still "
                f"be acting on it. That root is FROZEN -- no reuse, no "
                f"adoption and no deletion on the strength of an unsettled "
                f"act -- until an operator reconciles it, and the two roots "
                f"of one attempt overlap so neither may be touched while "
                f"either is held")


def _assignment_identity(assignment_id):
    boundaries.identity(assignment_id, "an assignment identity")
    if (assignment_id in (".", "..") or "/" in assignment_id
            or "\x00" in assignment_id):
        _denied("an assignment identity is one path component and cannot traverse")
    if assignment_id == _REVIEW_LINE_HOME:
        _denied("the review-line custody namespace is never an assignment home")
    return assignment_id


def _refuse(message, code="path"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- canonical, contained roots ----------------------------------------------


def _real(path, what):
    """The canonical path, with every link already resolved.

    LEXICAL CONTAINMENT IS NOT CONTAINMENT. `..` in the spelling is the obvious
    escape and the one a normalizer catches; a symlink component is the one that
    looks perfectly ordinary until it is followed, and only the real path sees
    it.
    """
    # A LITERAL LABEL at the owner, and the caller's noun only in the prose
    # after it. The inventory attributes an owned entry by the label written at
    # the site, so a shared helper that owned under its caller's word would be a
    # boundary nothing could place -- and this helper is the single owner for
    # every path this component is handed.
    boundaries.text(path, "a filesystem root")
    if not os.path.isabs(path):
        _refuse(f"{what} is not an absolute path; a root this build cannot "
                f"name exactly is not a root")
    return os.path.realpath(path)


def _within(child, parent):
    """Strictly inside, and never merely sharing a prefix.

    `/srv/work-2` starts with `/srv/work` and is not inside it, which is why
    this compares SEGMENTS rather than characters.
    """
    if child == parent:
        return False
    return child.startswith(parent.rstrip(os.sep) + os.sep)


def _contained(path, root, what):
    real = _real(path, what)
    if not _within(real, root):
        _refuse(f"{what} resolves outside the storage this manager owns")
    return real


# -- the ceilings, and the ORDER they are applied in --------------------------


def _entry_ceilings(what, taken, max_entries):
    """The entry ceilings, checked BEFORE the next file is opened.

    TWO CEILINGS, TWO REFUSALS, and the difference is not cosmetic. This
    module's own `MAX_*` are POLICY -- what this build will handle at all,
    whoever asked. A caller's ceiling is part of a DELIVERY's declared
    contract, and a tree that exceeds it is an integrity failure of that
    delivery rather than a request this build declines. The taxonomy already
    distinguishes them and callers already depend on which one they get. When
    both are crossed the global one answers, because what this build will not
    do at all is decided before what this delivery was allowed.

    Review [P1]: this ran AFTER the crossing file had already been read, so
    the file the ceiling exists to refuse was read first -- work and memory a
    worker chose, spent on material this manager had already decided it would
    not take. `taken` is the count already accepted, so the file about to be
    opened is number `taken + 1`.
    """
    if taken + 1 > MAX_ENTRIES:
        _denied(f"{what} carries more than {MAX_ENTRIES} files")
    if max_entries is not None and taken + 1 > max_entries:
        _refuse(f"{what} carries more than the {max_entries} files its "
                f"declaration allows", code="limit")


def _byte_allowance(total, max_bytes):
    """How many more bytes this pass may accept, over BOTH ceilings.

    The SMALLER remaining allowance, because a read bounded by only one of
    them is unbounded with respect to the other. The reader takes this plus
    one byte: one byte past the line is what proves the line was crossed, and
    reading any further is work the crossing already made pointless.
    """
    allowance = MAX_BYTES - total
    if max_bytes is not None:
        allowance = min(allowance, max_bytes - total)
    return allowance


def _byte_ceilings(what, total, added, max_bytes):
    """The byte ceilings, over what the bounded read actually returned.

    This one CANNOT move before the read -- how large a file is, is what the
    read finds out. What makes it a bound rather than an observation is that
    the read it judges was itself given `_byte_allowance`, so `added` is at
    most one byte past the line however large the file grew while open. The
    same global-before-declared precedence `_entry_ceilings` states.
    """
    if total + added > MAX_BYTES:
        _denied(f"{what} carries more than {MAX_BYTES} bytes")
    if max_bytes is not None and total + added > max_bytes:
        _refuse(f"{what} carries more than the {max_bytes} bytes its "
                f"declaration allows", code="limit")


# -- measuring a directory ----------------------------------------------------


def directory_manifest(root):
    """The frozen `contentManifest` for a tree, MEASURED rather than declared.

    Every entry is opened once, with `O_NOFOLLOW`, and both its bytes and its
    size come from that one descriptor -- so a replacement between the check and
    the read is a file this component never sees rather than a file it
    describes wrongly.

    The entries come back sorted BYTEWISE, which is the order §12 rule 6 checks
    and the order the tree digest is taken over. Sorting by anything else would
    produce a manifest that recomputes to a different digest on a different
    locale.

    THE CEILINGS BOUND THE MEASUREMENT ITSELF rather than judging it after the
    fact: the entry count is checked before the next file is opened, and each
    read is given only the allowance still remaining. See `_entry_ceilings`
    and `_byte_allowance`.
    """
    what = "a source directory"
    real = _real(root, what)
    entries = []
    total = 0
    for place, relative in _walk(real, what):
        _entry_ceilings(what, len(entries), None)
        content = _read_exactly(place, relative, what,
                                allowance=_byte_allowance(total, None))
        _byte_ceilings(what, total, len(content), None)
        entries.append({"path": relative,
                        "bytes": len(content),
                        "content_digest": digest_of_bytes(content)})
        total += len(content)
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return {"entries": entries,
            "entry_count": len(entries),
            "total_bytes": total,
            "tree_digest": digest(entries)}


def copied_manifest(root, into, *, max_entries=None, max_bytes=None,
                    admits=None):
    """Measure a tree and COPY it, in ONE no-follow pass.

    W26283. `directory_manifest` above is race-safe: it descends by opened
    directory identity and reads every file through a descriptor it proved is a
    regular file. A caller that measured with it and then copied by REOPENING
    each path threw that away -- and that is what W6634's staging did. Two
    harms were driven against it rather than argued:

      a measured subdirectory renamed and replaced with a symbolic link made
      the copy read THROUGH the link, so material from outside the tree
      entirely landed in the destination; and

      a measured regular file replaced with a FIFO made the copy's `open`
      block forever, which is one `mkfifo` stalling the caller indefinitely.

    Both are the defect this module's own walker records having fixed once --
    "a no-follow open of the FINAL file does not stop a raced ANCESTOR from
    becoming a symbolic link" -- reappearing in whoever copies afterwards. So
    the copy is not a second pass over path strings: the bytes WRITTEN are the
    bytes MEASURED, from the one descriptor that produced them, and there is no
    window between the two for anything to be replaced in.

    `max_entries` and `max_bytes` are the CALLER's declared ceilings, enforced
    as the walk runs rather than after it. A tree that exceeds them stops being
    copied at the entry that crosses the line, instead of being written whole
    and refused afterwards. Review [P1] tightened "as the walk runs" into
    BEFORE THE WORK IT REFUSES: the entry ceilings answer with nothing opened,
    and the read is handed the smaller remaining allowance so a file the
    worker grows while it is open cannot outrun the byte ceiling either.

    `admits(relative, content)` is a rule the caller applies to each file's
    bytes before they are written, and it raises to refuse. It exists so a
    caller's own content rule -- §13 live-secret scanning, for one -- runs at
    the one moment the content is in hand, without this function knowing what
    the rule is.

    Answers the same `contentManifest` shape `directory_manifest` does, over
    what was actually written.
    """
    what = "a source directory"
    real = _real(root, what)
    entries = []
    total = 0
    os.makedirs(into, exist_ok=True)
    for place, relative in _walk(real, what):
        # THE CEILING COMES BEFORE THE FILE IT REFUSES. Review [P1]: both
        # ceilings used to be judged on a file this loop had already read, so
        # the over-limit entry was opened and held in memory before anything
        # declined it -- and the byte read it judged had no bound of its own,
        # so a file growing while open could keep that refusal from ever being
        # reached. The entry count is decided here, with nothing opened; the
        # read below is given only what is left.
        _entry_ceilings(what, len(entries), max_entries)
        content = _read_exactly(place, relative, what,
                                allowance=_byte_allowance(total, max_bytes))
        _byte_ceilings(what, total, len(content), max_bytes)
        if admits is not None:
            admits(relative, content)
        target = os.path.join(into, relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        # THE DESTINATION IS OPENED NO-FOLLOW AND EXCLUSIVELY TOO. This
        # function is what makes bytes the caller's own, so a link left at a
        # destination name by an interrupted attempt -- or by anything else
        # that can write there -- must not become the thing written through.
        # `O_EXCL` is what makes it exclusive: the caller clears a partial
        # tree before calling, so an entry that already exists here is not one
        # this pass created.
        handle = os.open(target,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600)
        try:
            os.write(handle, content)
        finally:
            os.close(handle)
        entries.append({"path": relative,
                        "bytes": len(content),
                        "content_digest": digest_of_bytes(content)})
        total += len(content)
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return {"entries": entries,
            "entry_count": len(entries),
            "total_bytes": total,
            "tree_digest": digest(entries)}


def _walk(real, what):
    """Every regular file under a canonical root, with its relative path.

    Refuses ON SIGHT, before anything is read: a link of either kind, a special
    file, a directory that is really a link, and a path that leaves the root.
    """
    # THE DESCENT IS BY OPENED DIRECTORY IDENTITY, not by path string.
    # Review [P1]: a no-follow open of the FINAL file does not stop a raced
    # ANCESTOR from becoming a symbolic link -- the listing said `deep` was a
    # directory, and by the time a later path string was resolved through it,
    # `deep` was a door out of the tree. Every directory is opened
    # `O_NOFOLLOW|O_DIRECTORY` and read THROUGH THAT DESCRIPTOR, and each
    # child is opened relative to it with `dir_fd`, so a component replaced
    # after it was listed is a directory this walk never entered.
    root = _open_directory(None, real, "", what)
    # EVERY DESCRIPTOR THIS WALK OPENS, so the `finally` can close all of them.
    # Review [P1]: the stack only held directories not yet descended into, so a
    # directory that WAS descended into leaked its descriptor for the life of
    # the generator -- and a deep tree exhausted the process's table. A walk
    # that owns descriptors owns closing them.
    opened = [root]
    stack = [(root, "", 0)]
    try:
        while stack:
            handle, prefix, depth = stack.pop()
            if depth > MAX_DEPTH:
                _denied(f"{what} nests deeper than {MAX_DEPTH} directories")
            # `scandir` on a descriptor lists THAT directory, whatever its
            # name now refers to.
            with os.scandir(handle) as listing:
                found = sorted(listing, key=lambda entry: entry.name)
            for entry in found:
                relative = f"{prefix}{entry.name}"
                if entry.is_symlink():
                    _refuse(f"{what} carries the symbolic link "
                            f"{name_value(relative)}; this build "
                            f"delivers only what a source directory literally "
                            f"contains, because a link materializes as content "
                            f"the assignment was never given")
                if entry.is_dir(follow_symlinks=False):
                    child = _open_directory(handle, entry.name, relative, what)
                    opened.append(child)
                    stack.append((child, f"{relative}/", depth + 1))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    _refuse(f"{what} carries "
                            f"{name_value(relative)}, which is "
                            f"neither a regular file nor a directory")
                yield (handle, entry.name), relative
    finally:
        for handle in opened:
            os.close(handle)


def _open_directory(parent, name, relative, what):
    """One directory, opened NO-FOLLOW and proved to be a directory.

    `O_DIRECTORY` is the second half: without it a name that became a regular
    file between the listing and this open would succeed, and the walk would
    then scandir something that is not a directory.
    """
    try:
        return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                       dir_fd=parent)
    except OSError as error:
        _refuse(f"{what} cannot enter "
                f"{name_value(relative or name)}: {error.strerror}; a "
                f"component replaced after it was listed is not one this walk "
                f"follows")


def _read_exactly(place, relative, what, *, allowance):
    """One file, opened once, with the descriptor deciding what it was.

    `O_NOFOLLOW` refuses a link AT the open rather than after it, and the
    identity is taken from `fstat` on the descriptor that produced the bytes.
    Anything a racing writer swaps in afterwards is a different file, and this
    never held it.

    A HARD LINK IS REFUSED HERE and not in the walk, because `st_nlink` is a
    property of the inode and the descriptor is what has one. A second name for
    the same inode is the same disclosure a symlink is, with nothing on the
    directory entry to see.

    `O_NONBLOCK` IS WHAT MAKES THE `fstat` REFUSAL REACHABLE. Review [P1]:
    `O_NOFOLLOW` protects only against a final symbolic link, and the walk's
    `is_file` answer is about the moment it LISTED the entry. A name that was a
    regular file then and is a FIFO now blocks this open until somebody writes
    -- so the descriptor-level proof below, the one guard a racing replacement
    cannot defeat, never runs at all, and one `mkfifo` stalls the manager
    indefinitely. This is the same interval `_open_directory` already covers
    for directories, on the file side of the walk. On a regular file the flag
    changes nothing: regular files are always ready, and the kind is proved
    from the descriptor before a byte is read either way.

    `allowance` IS A BOUND ON THE READ, and it is required because a reader
    with no bound is the defect. Review [P1]: `st_size` below was the only
    thing standing between a worker and an unbounded read, and it is not a
    bound at all -- it is one observation of a file the worker may keep
    writing to while this descriptor is open. The caller passes what is left
    of the smaller of its two ceilings; at most that plus one byte is taken,
    so growth after the `fstat` widens neither the work nor the memory, and
    the caller's refusal is reached rather than outrun.
    """
    # RELATIVE TO THE DIRECTORY WE OPENED, so the file is the one that
    # directory holds rather than the one its name resolves to now.
    parent, name = place
    try:
        descriptor = os.open(name,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
    except OSError as error:
        _refuse(f"{what} cannot read {name_value(relative)}: "
                f"{error.strerror}")
    try:
        stated = os.fstat(descriptor)
        # THE DESCRIPTOR'S OWN ANSWER, not the directory entry's. The walk
        # already refused anything that was not a regular file by name; this is
        # the same question asked of the thing actually opened, which is the
        # only one a racing replacement cannot have changed underneath.
        if stated.st_mode & _FILE_KIND != _REGULAR:
            _refuse(f"{what} entry {name_value(relative)} is not a regular "
                    f"file")
        if stated.st_nlink > 1:
            _refuse(f"{what} carries {name_value(relative)}, which "
                    f"is a hard link; a second name for one inode delivers "
                    f"content the assignment was never given, and leaves "
                    f"nothing on the directory entry to see")
        if stated.st_size > MAX_BYTES:
            _denied(f"{what} entry {name_value(relative)} is larger "
                    f"than {MAX_BYTES} bytes")
        content = _read_all(descriptor, allowance)
    finally:
        os.close(descriptor)
    return content


def _read_all(descriptor, allowance):
    """At most `allowance` + 1 bytes, however large the file becomes.

    ONE BYTE PAST THE LINE is exactly what the caller needs and no more: it
    proves the ceiling was crossed without reading however far past it the
    file went. A file that fits answers whole, because it stops at EOF first.
    """
    remaining = allowance + 1
    pieces = []
    while remaining > 0:
        piece = os.read(descriptor, min(remaining, 1 << 20))
        if not piece:
            break
        pieces.append(piece)
        remaining -= len(piece)
    return b"".join(pieces)


# -- one private workspace per assignment -------------------------------------


def assignment_workspace(workspace_group, storage, assignment_id, *,
                         control=None):
    """TWO ROOTS, private to one assignment and never overlapping.

    `inputs` is read-only evidence and `workspace` is the only writable tree.
    They are siblings rather than nested for the reason the fourth rule states:
    a worker that could write into its own inputs would make the seal over them
    describe a tree that has since changed.

    W15232 review [P1]: there was a THIRD root holding version-control metadata
    for one assignment. It is gone, and the correction is worth naming because
    my own cut missed it. I separated this module's two halves by closing the
    CALL GRAPH over each, which treats a function as one node -- so this one
    came out "generic" while the acquisition-specific work sat INSIDE it. Every
    assignment got that metadata area whether its staged input was a directory,
    an archive, a database snapshot, media or a format nobody has written yet.
    That is the core manager understanding an acquisition format, which is
    exactly what the ruling removed.

    A future source stager or driver allocates its own private capacity under
    an explicit owner. Private ephemeral space is generic runtime capacity, not
    protocol vocabulary this manager provisions.
    """
    _assignment_identity(assignment_id)
    # W33936 review [P0] then [P1]: THE GROUP IS THE DEPLOYMENT'S, AND THIS
    # FUNCTION READS IT RATHER THAN BEING TOLD IT.
    #
    # [P0] made it a required operand, because the previous cut left
    # `adopt_workspace_group` reachable and uncalled -- a grant that existed as
    # a function and not as a permission bit. That was necessary and not
    # sufficient: a required operand still lets a caller name any group the
    # manager happens to hold, including an authority-bearing service group,
    # and every later check agreed because every later check compared against
    # the same supplied value.
    #
    # So what crosses now is the FROZEN ANSWER rather than a number. Only
    # `configured_workspace_group` mints a `WorkspaceGroup`, and it mints one
    # by reading the deployment's own record -- so a caller holding one for
    # group B means the deployment configured B, and a caller that wants the
    # workspace in another group has to change the deployment.
    #
    # THE CAPABILITY RATHER THAN THE STORE, and the difference is not
    # cosmetic. This function is a filesystem operation; giving it a store
    # would give it a thread affinity it has no other reason to have, and a
    # concurrent allocation is exactly what it already promises to be safe
    # for. Consuming the answer is what the correction asks for; holding the
    # thing that produced it is not.
    #
    # W270664 F2, review 2026-09-26T09:15:26Z: THAT LAST PARAGRAPH IS NOW WRONG ABOUT
    # THIS FUNCTION AND IS CORRECTED RATHER THAN LEFT STANDING. Allocation had "no other
    # reason" to hold a store only while it was allowed to reach these roots without
    # asking whether anybody else owned them -- and the reviewer's probe allocated an
    # attempt's roots in the middle of its own cleanup, between the removal that emptied
    # them and the ending that had not committed. An entry that cannot ask cannot be
    # excluded, so this one asks now. THE THREAD AFFINITY IS REAL AND IS THE PRICE: the
    # journal read below uses the store's connection, so allocation belongs on the
    # thread that opened it, exactly as every other journal-reading entry here does.
    # The capability is still what crosses -- the store arrives INSIDE the frozen answer
    # this function already required, not as a second operand a caller composes.
    if type(workspace_group) is not WorkspaceGroup:
        _denied(f"an assignment workspace is allocated into the deployment's "
                f"configured group, obtained from this manager's own record; "
                f"this is {name_value(workspace_group)}")
    workspace_group_capability = workspace_group
    workspace_group = workspace_group.gid
    # THIS ENTRY'S OWN OPERANDS COME FIRST, and review 2026-09-25T03:40:38Z already paid
    # for this lesson once on `discard_execution_roots`: when a guard runs ahead of an
    # entry's own validation, the guard's refusal arrives for a bad operand and the
    # accepted probe for that operand escapes as something else. Measured here exactly
    # so -- three inventory probes (`storage`, `place`, `_line_proof`) changed shape
    # until the storage validation below moved back in front of the exclusion.
    root = _real(storage, "the manager's workspace storage")
    if not os.path.isdir(root):
        _refuse("the manager's workspace storage is not a directory")
    if control is None:
        control = workspace_group_capability.store
    # THE EXCLUSION, AT THE CHOKEPOINT THE OTHER ENTRIES ALREADY USE. `refuse_if_held`
    # answers for a custody hold, an unresolved removal AND an unsettled cleanup, over
    # both overlapping roots, out of the journal that has authority over this storage.
    #
    # ONLY WHERE THAT JOURNAL SPEAKS FOR THE TREE, and that condition is not a weakening
    # -- it is this module's own accepted rule, stated in `WorkspaceStorage`: "A caller
    # may still allocate a workspace wherever it may already write; what it can no
    # longer do is have a container mounted on one." Measured while implementing this:
    # the accepted `tests.manager.input_roots` fixture allocates under a directory the
    # store never configured, and requiring the binding refused it. A tree this journal
    # has no authority over also has no custody hold, no removal ownership and no
    # cleanup admission that could concern it, so there is nothing there to exclude; the
    # exclusion applies exactly where the protected resources can exist.
    admitting = None
    admitted = None
    if control is not None and hasattr(control, "operation_record"):
        what = (f"allocating attempt {name_value(assignment_id)}'s execution roots")
        admitting = _asking_control(workspace_group_capability, control)
        asking = admitting.__enter__()
        try:
            if _speaks_for(asking, storage):
                refuse_if_held(asking, storage, assignment_id, what)
                # AND THE ADMISSION, WHICH IS WHAT COVERS THE EFFECT. Review
                # 2026-09-26T10:07:07Z committed a cleanup admission between the guard
                # above and the creation below; this transaction re-reads the journal
                # under `BEGIN IMMEDIATE` and is the decision, so a cleanup that
                # committed in that instant is seen and this refuses.
                admitted = _admitted_allocation(asking, assignment_id, what)
            else:
                admitting.__exit__(None, None, None)
                admitting = None
        except BaseException:
            admitting.__exit__(None, None, None)
            raise
    # THE EFFECT, WITH THE ADMISSION STANDING AND NO TRANSACTION OPEN, and the
    # completion written whatever happens. See `_completed_allocation` for why a
    # failed creation closes its window rather than holding it: an interrupted
    # creation is recoverable, and a window left open would block this attempt's
    # cleanup permanently.
    try:
        home = os.path.join(root, assignment_id)
        made = {}
        # EVERY ENTRY THE HOME WILL EVER HOLD IS PROVISIONED HERE, and the two
        # mountable roots are still the only thing this function ANSWERS with.
        #
        # W33935 re-review [P0]: freezing the `inputs` directory protects what is
        # inside it and nothing else -- rename and replacement of the entry ITSELF
        # are permissions of its PARENT, and the home was left at the process
        # default.  So the whole `0555` root could be renamed aside and a writable
        # one put at the same canonical path with different bytes in it.
        #
        # A parent can only be closed once nothing more needs to be created in it,
        # which is why `custody`, `credentials` and `credential-state` are made
        # now.  Those three are the adapter's and the credential home's, and
        # naming them here is coupling made explicit rather than coupling avoided:
        # the home is ONE directory with ONE layout, and
        # `test_input_delivery.TheHomeLayoutIsDeclaredWhereItIsFrozen` holds the
        # other two components to this list rather than trusting this comment.
        # EXCLUSIVE FIRST ALLOCATION, SEPARATED FROM RESTART LOOKUP.
        #
        # Approver ruling M34768 asks for unique never-reused per-attempt
        # directories and exclusive creation with collision refusal.  My first cut
        # put a publication check here, the restart path refuted it, and I then
        # concluded the two could not be separated at all -- which was wrong, and
        # the re-review proved it with a case I had not thought of: a stale home
        # whose `inputs` entry is a SYMLINK to another attempt's root.  That alias
        # is still contained by manager storage, so containment accepted it and a
        # second attempt received the first attempt's input root.
        #
        # The two ARE separable, and the proof is structural rather than a new
        # durable record.  A home is named by its attempt, so a home at this path
        # IS this attempt's -- provided its entries are genuinely its own
        # directories.  So every entry that already exists must be a real
        # directory, not a link, resolving to exactly the path under this home; an
        # entry that is anything else is stale or aliased state and fails closed.
        # An entry that does not exist is created here, which is the first
        # allocation.
        #
        # THIS KEEPS THE RESTART PATH, which is what the previous cut broke: a
        # restarted manager asking for the same attempt's roots finds real
        # directories at their own paths and is answered, because reopening an
        # attempt is not reusing an identity.
        # THE HOME IS PROVED BEFORE IT ANCHORS ANYTHING.
        #
        # Re-review [P0]: the first cut of this proof checked only
        # `os.path.isdir(home)`, which FOLLOWS SYMLINKS -- so a home that was
        # itself a link to another attempt passed, and the child proofs then
        # anchored on `realpath(home)`, which is the wrong sibling. Both sides of
        # every child comparison were relocated together and compared equal. A
        # structural proof applied to the children and not to the thing they are
        # measured against is not applied.
        expected_home = os.path.join(os.path.realpath(root), assignment_id)
        _own_directory(home, expected_home, "assignment home")
        for name in HOME_ENTRIES:
            place = os.path.join(home, name)
            _own_directory(place, os.path.join(expected_home, name),
                           f"{name} root")
            held = _contained(place, root, f"the assignment's {name} root")
            if name in ROOT_NAMES:
                made[name] = held
        # ESTABLISHED, NOT REQUESTED, and the GROUP with it.  `os.makedirs`
        # filters its mode through the umask; `os.chmod` on a directory that
        # already exists is exact, which is the same distinction W33935 corrected
        # at the two protocol documents.  `adopt_workspace_group` performs both,
        # so allocation and the grant are one step and a workspace this function
        # returns is one the worker can write.
        adopt_workspace_group(made, workspace_group)
        # THE RESULT ROOT IS MANDATORY AND THIS MANAGER ESTABLISHES IT.
        #
        # Approver ruling 2026-08-30 (W43975): the manager creates
        # `workspace/result-<attempt-id>` BEFORE runtime start; custody derives
        # that exact manager-owned locator, never creates a missing one, and
        # refuses a contradictory absence.
        #
        # WHY IT IS ESTABLISHED RATHER THAN CREATED ON DEMAND. A directory a
        # cleanup act invents is a directory that did not exist when the attempt
        # ran, so an ending could report accountable custody over an empty tree it
        # had just made while the worker's actual output sat somewhere else. The
        # only way "this is the attempt's result root" can be a FACT at cleanup is
        # for allocation to have made it a fact before the worker ever started.
        #
        # NESTED UNDER `workspace` RATHER THAN A HOME ENTRY, because it is the
        # worker's own writable output area and the home is closed after
        # allocation. It is deliberately not a member of the answer: `ROOT_NAMES`
        # is what a container may MOUNT, and this is a subject of custody rather
        # than a third mount.
        #
        # LOGS MAY EXIST WITH NO ACCEPTED ARTIFACTS -- the same ruling -- so an
        # empty one is an ordinary outcome and never evidence that nothing ran.
        result = os.path.join(made["workspace"], f"result-{assignment_id}")
        _own_directory(result,
                       os.path.join(expected_home, "workspace",
                                    f"result-{assignment_id}"),
                       "result root")
        _contained(result, root, "the assignment's result root")
        # THE SAME GRANT THE WORKSPACE ITSELF GETS, through the same owner:
        # `adopt_workspace_group` names its subject `workspace` because it adopts
        # ONE writable root, and this is a writable root under it.
        adopt_workspace_group({"workspace": result}, workspace_group)
        # W36540 review [P0]: THE ANSWER CARRIES ITS OWN PROVENANCE.
        #
        # A custody act has to be able to tell "this manager allocated these roots"
        # from "somebody made two directories with the expected names". Directory
        # SHAPE cannot make that distinction: any caller in this process can
        # `mkdir inputs; mkdir workspace` under a parent it owns and reproduce
        # every structural property. Shape may VALIDATE authority; it cannot
        # create it.
        #
        # So allocation mints a nominal type. It is still exactly a mapping --
        # every existing caller reads `roots["workspace"]` unchanged -- and a
        # plain dict is not an instance of it, which is the whole difference.
        answer = AllocatedRoots(made, _MINT)
    finally:
        if admitted is not None:
            try:
                _completed_allocation(asking, assignment_id, admitted)
            finally:
                admitting.__exit__(None, None, None)
        elif admitting is not None:
            admitting.__exit__(None, None, None)
    return answer


class AllocatedRoots:
    """The roots THIS FUNCTION allocated, as an immutable READ-ONLY mapping.

    NOT A `dict` SUBCLASS, AND NOT A HOLDER OF ONE EITHER, and review [P0] is
    why that distinction is the whole design rather than a detail. Two rounds ago I minted a nominal type
    so shape could not manufacture authority. One round ago I overrode
    `__setitem__`, `update`, `pop` and the rest to stop a holder retargeting
    it. Both were bypassable in the same way, because a subclass of a mutable
    builtin still IS one:

        dict.update(roots, {"workspace": somewhere_else})
        dict.__setitem__(roots, "workspace", somewhere_else)
        roots |= {"workspace": somewhere_else}

    Every one of those reaches the base implementation without ever calling an
    override. **Overriding more methods cannot close explicit base-class
    invocation** -- the paths were stored in something whose mutators are part
    of its type, and the only fix is not to store them there.

    So the members live behind a `MappingProxyType` over a dict referenced
    nowhere else, and this class implements the read half of the mapping
    protocol and nothing else. The round after that one found the private
    attribute itself -- `roots._members.update(...)` needs no method of this
    class at all -- which is what the proxy closes.

    AND THE AUTHORITY NO LONGER RESTS ON ANY OF IT. `custody.attempt_custody_
    root` derives the attempt's workspace from the allocation operands instead
    of reading it out of this object, so what this class guarantees is that the
    ANSWER is not quietly edited, not that a mount is safe. Those were the same
    question for six review rounds and they are not the same question. There is no inherited
    mutator to call, `dict(roots)` and `roots["workspace"]` still work for
    every existing caller, and `dict.update(roots, ...)` now fails on its own
    argument type rather than quietly succeeding.
    """

    # W270664 F2: `_adoption` carries the admission an adopting caller holds until the grant
    # takes over, so the exclusion does not end before the use it protects.
    __slots__ = ("_members", "_grant", "_grant_required", "_line", "_line_proof",
                 "_adoption")

    def __init__(self, made, _minted=None, _grant=None,
                 _grant_required=False, _line=False, _line_proof=None):
        if _minted is not _MINT:
            _denied("allocated roots are answered by `assignment_workspace` "
                    "and are not constructed; roots a caller can mint are "
                    "roots a caller chose")
        # A READ-ONLY VIEW OVER A DICT NOTHING ELSE HOLDS. W36540 review [P0],
        # sixth round: the members were an ordinary dict reachable through
        # ordinary attribute access, so `roots._members.update(...)` retargeted
        # both paths in place -- no method call to override, and therefore
        # nothing another round of overrides could have caught.
        #
        # `MappingProxyType` is not another override. The proxy has no mutating
        # operation at all, and the dict it wraps is created here and referenced
        # nowhere else, so there is no object left for a holder to edit.
        #
        # WHAT THIS STILL CANNOT PROMISE, said plainly: `object.__setattr__`
        # reaches any slot in this language, and no representation closes that.
        # That is why the real correction is elsewhere --
        # `custody.attempt_custody_root` no longer READS a path from this
        # object at all, it derives one from the allocation operands. This
        # makes the complaint false at its own site as well; it is not what the
        # guarantee rests on.
        object.__setattr__(self, "_members", MappingProxyType(dict(made)))
        object.__setattr__(self, "_grant", _grant)
        object.__setattr__(self, "_grant_required", _grant_required)
        object.__setattr__(self, "_line", _line)
        object.__setattr__(self, "_line_proof", _line_proof)
        object.__setattr__(self, "_adoption", None)

    # -- the read half of the mapping protocol, and only the read half ------
    #
    # `keys` and `__getitem__` are what `dict(roots)` and `**roots` are built
    # on, so every existing consumer keeps working unchanged.

    def __getitem__(self, key):
        return self._members[key]

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def __contains__(self, key):
        return key in self._members

    def keys(self):
        return self._members.keys()

    def items(self):
        return self._members.items()

    # NO `get` AND NO `values`. Nothing reads the roots that way, and adding
    # them would put `key` and `default` -- mapping-protocol words, not this
    # manager's operands -- into the declared operand vocabulary. The
    # dependency guard said so, and it is right: a public parameter here is a
    # domain operand or it should not exist.

    def __eq__(self, other):
        return dict(self._members) == other

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def __repr__(self):
        return f"AllocatedRoots({self._members!r})"

    def __setattr__(self, name, value):
        _refuse("allocated roots are the answer this manager gave about one "
                "assignment and are immutable", code="schema")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    def copy(self):
        """A PLAIN dict, deliberately.

        A copy is not the answer this manager gave; it is a caller's own
        mapping that happens to hold the same strings, and typing it as one
        would hand back exactly the forgery the mint refuses.
        """
        return dict(self._members)

    # -- every mutating door this type OWNS, refused in our own words -------
    #
    # It does not inherit any, so these exist for the DIAGNOSTIC rather than
    # for the guarantee: a caller reaching for one gets a sentence about why
    # the answer is fixed instead of a bare TypeError. The guarantee is that
    # the members are not in a mutable builtin at all.
    #
    # `dict.update(roots, ...)` and `dict.__setitem__(roots, ...)` are NOT on
    # this list and cannot be: they fail in Python, on the argument type,
    # because this is not a dict. That refusal is stronger than one we could
    # write, and it is the one the previous two cuts could not produce.

    def _frozen(self, *args, **members):
        _refuse("allocated roots are the answer this manager gave about one "
                "assignment and are immutable; a holder that could retarget "
                "them would be choosing the directory the answer names",
                code="schema")

    __setitem__ = _frozen
    __delitem__ = _frozen
    __ior__ = _frozen
    update = _frozen
    setdefault = _frozen
    pop = _frozen
    popitem = _frozen
    clear = _frozen


def _own_directory(place, expected, what):
    """Create this directory, or PROVE the one already there is ours.

    ONE OPERATION, not a test and then a create.  Re-review [P1]: those were
    two steps -- `lexists` and then `makedirs` -- and two callers could both
    observe absence, after which one created the directory and the other
    received a raw `FileExistsError` from the OS.  An ordinary manager race
    became an unexpected fault, and a fault is not a contract answer.

    So the create is ATTEMPTED and its collision is the branch.  A caller that
    loses the race falls through to exactly the proof a pre-existing directory
    gets, and reopens it when it really is this attempt's own -- which is the
    same question, asked once, whether the directory has been there for a
    week or for a microsecond.

    THE PROOF IS NO-LINK AND EXACT-PATH.  A link is refused even when it
    points inside manager storage: what makes a root private is that it IS
    this attempt's directory, not that it lands somewhere this manager owns.
    """
    try:
        os.mkdir(place)
        return place
    except FileExistsError:
        pass
    except OSError as failure:
        _refuse(f"the manager's {what} could not be created at "
                f"{name_value(place)}: {type(failure).__name__}", code="path")
    if os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != expected:
        _refuse(
            f"{name_value(place)} already exists and is not this attempt's "
            f"own {what} at its own path; a stale or aliased "
            f"directory is refused rather than adopted, because material "
            f"under it would be another attempt's",
            code="path")
    return place


def _frozen_delivery(root):
    """THE WHOLE ROOT made read-only, deepest first -- not just its top.

    W39358, measured inside the real composed runtime. `compose_input_root`
    said it exposed "the whole surface" read-only and chmodded exactly ONE
    directory: the root. Everything staged BELOW it kept what its writer left,
    and `copied_manifest` -- the manager's own copier, and the only thing that
    delivers a source TREE -- creates every file `0o600`. So the third thing
    under `/input` was owner-only while the two documents beside it were
    `0o444`, and the container's fixed uid 65532 got `EACCES` opening the very
    source the assignment tells it to work from. The dogfood operator's first
    real worker turn failed exactly there, on `/input/source/harness.py`.
    That is W33935's defect again, one level down: the two DOCUMENTS were
    fixed then because they were the only things anything read.

    THE DIRECTORIES TOO, and for the same reason the root gets `0o555` rather
    than `0o500`: a directory the worker cannot traverse is one whose readable
    files it cannot reach. `copied_manifest` makes its subdirectories with a
    plain `os.makedirs`, so their modes are whatever the umask happened to
    produce -- `0o775` on the host this was measured on and `0o700` under the
    ordinary service umask, which is the accident `WORKSPACE_DIR` exists to
    end.

    DEEPEST FIRST, because a directory made unwritable before its children are
    is a directory whose children this process can no longer chmod.

    `sealing._frozen` is the same walk over custody rather than over a
    delivery. They are deliberately NOT merged here: this Work owns the input
    path, and one owner for both is a change to a module it does not.
    """
    for base, directories, files in os.walk(root, topdown=False):
        for one in files:
            os.chmod(os.path.join(base, one), READ_ONLY_FILE)
        for one in directories:
            os.chmod(os.path.join(base, one), READ_ONLY_DIR)
    os.chmod(root, READ_ONLY_DIR)


def compose_input_root(inputs, input_manifest, assignment_manifest, *,
                       assignment, runtime_attempt_id):
    """Materialize BOTH `/input/` documents, in the order the ruling fixes.

    W19784, approved 2026-08-26. §7.0's lifecycle is normative and this is the
    one place that performs it:

      `input.json` is authored BEFORE claim and its bytes and digest never
      change afterwards -- it is the pre-claim evidence the result is measured
      against;
      `assignment.json` is materialized AFTER the claim commits, carrying the
      live assignment identity the completion envelope must copy;
      NO CONTAINER OBSERVES THE ROOT DURING THAT TRANSITION, and only once both
      documents are complete is the whole surface exposed read-only.

    So this refuses rather than repairs when the root is already composed. A
    manager that rewrote `input.json` here would be changing the evidence after
    the claim that was made against it, and one that replaced `assignment.json`
    would be moving an identity a running worker may already have copied.

    THE PAIR IS VALIDATED BEFORE ANYTHING IS WRITTEN (§12 rule 16). Two
    documents that are not one delivery must never exist on disk together: a
    mount is not the last chance to notice, it is the first moment it is too
    late.

    AND THE PAIR IS HELD TO THE MANAGER'S OWN LIVE IDENTITY. W19784 review
    [P0]: this took the two documents alone, so it could prove only that they
    AGREE WITH EACH OTHER -- and a self-consistent pair minted for a superseded
    generation or another runtime attempt agrees with itself perfectly. It
    would have been written, mounted, and caught only at the freeze, after the
    agent had already run against material this manager never authorized.

    So `assignment` and `runtime_attempt_id` are REQUIRED KEYWORD OPERANDS,
    the manager's own values out of the attempt row, and there is no default:
    a caller that could omit them would be a caller that composes an
    unauthenticated root, which is the defect. The generation and the attempt
    are proved here, BEFORE the root exists, rather than at custody.

    Returns the two absolute paths it wrote.
    """
    root = _real(inputs, "the assignment's inputs root")
    if not os.path.isdir(root):
        _refuse("the assignment's inputs root is not a directory")
    expected = boundaries.document(
        assignment, "the manager's own assignment",
        required=("work_ref", "participant", "generation"))
    boundaries.identity(runtime_attempt_id, "a runtime attempt identity")
    # VALIDATED FIRST, AND BY THE SHIPPED RULE rather than a second copy of it.
    owned_input, owned_assignment = check_input_pair(
        input_manifest, assignment_manifest,
        what="the execution input root")
    # THEN AGAINST WHAT THIS MANAGER OWNS. The order is the content: the pair
    # rule proves the documents are one delivery, and this proves that one
    # delivery is THIS one. Neither implies the other.
    if owned_assignment["assignment_ref"] != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the assignment manifest for this input root names "
            f"{name_value(owned_assignment['assignment_ref'])}, and this "
            f"manager is composing a root for "
            f"{name_value(expected)}; a pair that agrees with itself is not "
            f"thereby the delivery that was authorized")
    if owned_assignment["runtime_attempt_id"] != runtime_attempt_id:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the assignment manifest names runtime attempt "
            f"{name_value(owned_assignment['runtime_attempt_id'])} and this "
            f"root is being composed for "
            f"{name_value(runtime_attempt_id)}; a worker mounting it would "
            f"publish an envelope this attempt cannot settle")
    written = []
    for name, owned in ((INPUT_MANIFEST, owned_input),
                        (ASSIGNMENT_MANIFEST, owned_assignment)):
        place = os.path.join(root, name)
        if os.path.lexists(place):
            _refuse(f"{name_value(place)} already exists; the input root is "
                    f"composed once and then frozen, and rewriting a protocol "
                    f"document under a claim that was made against it would "
                    f"change the evidence the result is measured by",
                    code="path")
        written.append(_write_read_only(place, canonical_bytes(owned), name))
    # AND THEN THE ROOT IS FROZEN, which is the half the file modes cannot do.
    #
    # W33935 review [P0]: `READ_ONLY_DIR` existed, was exported, and NOTHING
    # applied it -- this function wrote both documents at 0444 and returned,
    # leaving the root at 0775.  A 0444 file inside a writable directory is not
    # protected: unlink and rename are permissions of the DIRECTORY, so the
    # manager's own uid, or anything sharing its group, could remove either
    # document and put a different one at the same name -- underneath a worker
    # that had already mounted it.  The read-only bind stops the container
    # writing; it does not stop the host replacing a bound file.
    #
    # AFTER BOTH DOCUMENTS ARE DURABLY INSTALLED, because a root frozen between
    # them could not receive the second one.  §7.0 fixes that order: the pair
    # is composed and only then is the whole surface exposed.
    #
    # `os.chmod` ON THE ROOT is exact and was never umask-filtered -- the umask
    # applies to CREATION, and this directory already exists.  0555 rather than
    # 0500 for the same reason the files are 0444: the container's fixed uid is
    # not this manager's, and a root it cannot traverse is a root whose
    # readable documents it cannot reach.
    #
    # THE CLEANUP PATH IS UNAFFECTED AND THAT IS MEASURED, not assumed:
    # `_remove` makes each directory writable as it goes, inside a tree
    # `discard_workspace` has already proved contained, so a frozen root is
    # removable by the manager that owns it and by nothing else.
    _frozen_delivery(root)
    # AND THE PARENT, which is the only thing that governs the root's own
    # ENTRY.  Re-review [P0]: `0555` on `inputs` denies create, unlink and
    # rename INSIDE it; renaming or replacing `inputs` itself is a write to
    # the home, and the home was writable -- so the frozen root could be moved
    # aside and a `0775` one put at the same canonical path.
    #
    # Safe to close now because `assignment_workspace` provisioned every entry
    # this home will ever hold.  What still happens afterwards -- an attempt's
    # custody tree, a volatile credential root, a durable credential record --
    # is created INSIDE those entries, which this mode does not govern.
    os.chmod(os.path.dirname(root.rstrip("/")), READ_ONLY_DIR)
    return tuple(written)


def read_input_root(inputs):
    """The two composed `/input/` documents, read back OFF DISK and validated.

    W19784 review [P0]: the launch path has to prove the root a runtime is
    about to mount, and what the runtime mounts is the disk -- not a value
    threaded down from whoever composed it. So this reads the bytes and puts
    them through the same shipped `check_input_pair` the composition used.

    It deliberately does NOT take an expected identity. Holding the pair to the
    manager's live assignment is `attempts.authorize_input_root`, which is
    where the attempt row is: this component owns paths and documents, and
    which assignment is live is not a fact it has.
    """
    root = _real(inputs, "the assignment's inputs root")
    if not os.path.isdir(root):
        _refuse("the assignment's inputs root is not a directory")
    found = {}
    for name in (INPUT_MANIFEST, ASSIGNMENT_MANIFEST):
        place = os.path.join(root, name)
        try:
            with open(place, "rb") as reading:
                raw = reading.read(MAX_MANIFEST_BYTES + 1)
        except OSError:
            _refuse(f"the input root carries no readable {name_value(name)}; "
                    f"a root missing a protocol document is one no runtime "
                    f"may mount", code="path")
        if len(raw) > MAX_MANIFEST_BYTES:
            _refuse(f"{name_value(name)} is wider than "
                    f"{MAX_MANIFEST_BYTES} bytes", code="limit")
        try:
            found[name] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            _refuse(f"{name_value(name)} is not a readable document",
                    code="schema")
    return check_input_pair(found[INPUT_MANIFEST], found[ASSIGNMENT_MANIFEST],
                            what="the composed input root")


def _write_read_only(place, payload, name):
    """One protocol document, published atomically and then made evidence.

    ATOMIC because a half-written protocol document under its final name is
    indistinguishable from a complete one, and this root is about to be handed
    to a container that reads exactly these two names.

    READ-ONLY because the mode says on disk what the contract says in prose. A
    bind mounted read-only protects the container's view; it does not protect
    the host copy from this manager's own later mistake.
    """
    staged = place + ".composing"
    # CREATED UNREADABLE AND NO-FOLLOW, then made evidence on the DESCRIPTOR.
    #
    # W33935, and it is the second time this exact defect has been corrected in
    # this distribution: W26291 review [P0] found it at the launch delivery and
    # fixed it there, and the same line here was never revisited.  A creation
    # mode is FILTERED BY THE PROCESS UMASK, so passing `READ_ONLY_FILE` to
    # `os.open` authors 0444 under umask 022 and 0400 under the ordinary
    # service umask 077 -- the unreadable document arriving silently, and only
    # on some hosts.  Requesting a mode is not establishing one.
    #
    # `O_NOFOLLOW` so a link left at the staging name is refused rather than
    # written through, mode 0 so the file is never readable while it is still
    # partial, and `fchmod` ON THE DESCRIPTOR THIS FUNCTION WROTE rather than a
    # second `chmod` by name -- the name could be something else by then and
    # the descriptor cannot be.  It runs after the last byte, so the document
    # becomes readable exactly when it becomes complete.
    handle = os.open(staged,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    try:
        written = 0
        while written < len(payload):
            moved = os.write(handle, payload[written:])
            if moved <= 0:
                _refuse(f"the manager's {name_value(name)} could not be "
                        f"written whole", code="limit")
            written += moved
        os.fsync(handle)
        os.fchmod(handle, READ_ONLY_FILE)
    finally:
        os.close(handle)
    os.replace(staged, place)
    return place


def discard_workspace(storage, assignment_id, *, control):
    """Remove ONLY what this component created, and say what it removed.

    Recoverable rather than exact: a tree already gone is the state this asks
    for, so it answers `False` instead of refusing. What it will not do is
    delete anything outside the storage root it was given -- the containment
    check runs before the removal and not after.
    """
    _refuse_nested_removal(control, "removing this attempt's workspace home")
    _assignment_identity(assignment_id)
    root = _real(storage, "the manager's workspace storage")
    home = os.path.join(root, assignment_id)
    if not os.path.exists(home):
        outstanding = standing_removal(control, assignment_id)
        if outstanding:
            ordinal, _ = outstanding[0]
            raise ContractRefusal(
                "refused", "precondition",
                f"this attempt's home is absent and removal {ordinal} of it was admitted "
                f"with no completion recorded, so the absence cannot be read as the state "
                f"this caller asked for -- it may be what an unfinished removal left "
                f"behind, and an unresolved removal is reconciled rather than reported as "
                f"done")
        return False
    _contained(home, root, "the assignment's workspace")
    # W257624 R3: THE DELETION PATH IS THE FIRST GUARDED ENTRY, and the guard
    # sits HERE rather than at the top of the body on purpose. Every operand
    # this function already validates is validated first, so the refusal a
    # caller gets for a bad path or a bad identity is unchanged and the
    # boundary inventory still attributes those two operands where it did.
    # What the hold changes is only whether a WELL-FORMED removal proceeds.
    #
    # AFTER the absence answer too: a home that is already gone is the state
    # the caller asked for, and answering `False` for it reaches no resource.
    #
    # W270664 F2, review 2026-09-26T06:39:23Z: BUT ABSENT IS NOT THE SAME AS RESOLVED. If a
    # removal of this attempt was admitted and never completed, the home may be gone BECAUSE
    # that removal was part way through -- so answering `False` would report the caller's
    # desired state while the act that produced it is still unaccounted for. An unresolved
    # removal is refused here, before the absence shortcut, and only a home that is absent
    # with nothing outstanding answers `False`.
    # SERIALIZED, not merely checked -- see `_serialized_removal`. The hold read
    # and the removal happen under the same `BEGIN IMMEDIATE` lock R1's claim
    # takes, so a racing `custody_act` cannot commit a hold in between.
    # THE OBJECT THIS ENTRY IS ABOUT, read once here so the effect can be compared against
    # it rather than against whatever the name resolves to when the effect runs.
    authorized = _pinned_home(root, assignment_id)
    return _serialized_removal(
        control, storage, assignment_id,
        "removing this attempt's workspace home",
        lambda: (_removed_pinned_home(root, assignment_id, pinned=authorized,
                                      what="removing this attempt's workspace home"),
                 True)[1])


def adopted_assignment_workspace(storage, assignment_id, *, control):
    """The roots an attempt ALREADY HAS, proved and never allocated.

    W39358 review [P1]. A deployment resuming an attempt needs its roots and
    must not create them: `assignment_workspace` creates, chmods and chgrps,
    which is an allocation performed by something that only means to read. The
    deployment's own answer was a check followed later by an ordinary open --
    a second, weaker door onto the same directories, and a check-then-open
    race besides.

    So the proof lives here, where the invariant does. It is exactly
    `_own_directory`'s question asked read-only -- not a link, a real
    directory, resolving to its own path under the configured store -- applied
    to the home and to both roots, and it changes nothing on disk.

    ANSWERS THE SAME MAPPING `assignment_workspace` DOES, so a caller reads
    `roots["workspace"]` whichever way it obtained them, and refuses an
    attempt whose roots are gone: that is not a state an ending can be
    performed over.
    """
    # W257624 R3, owner 262043: ADOPTION IS EXACTLY WHAT A HOLD FORBIDS, and
    # the store is required for the same reason `discard_workspace`'s is -- a
    # protection that is off when nobody remembered to wire it is not one, and
    # the operand cannot be skipped by forgetting. R1's own refusal text already
    # claims this ground: "no reuse, no ADOPTION and no deletion on the strength
    # of an unsettled act".
    #
    # WHY THIS ONE IS NOT WRAPPED IN THE REMOVAL'S TRANSACTION, stated because
    # the difference is a judgement and not an oversight. `_serialized_removal`
    # exists to put a check and an EFFECT inside one write lock. This function
    # performs no effect: it proves and answers, changing nothing on disk. A
    # hold is always committed BEFORE its act submits -- that is R1's ordering,
    # and the race tests measure it -- so a hold that could be acting is a hold
    # this read sees. What remains is the caller's USE after the answer, and
    # closing that would need `_claim_episode` to refuse while an adoption
    # stands: mutual exclusion in both directions, a shared-primitive change to
    # accepted R1 product. That is named in R3-ENUMERATION.md for coordination
    # rather than made here, and it is not what this operand pretends to do.
    # THIS FUNCTION'S OWN OPERANDS ARE VALIDATED BEFORE THE GUARD'S, because
    # the boundary inventory names `storage` and `assignment_id` as this
    # entry's, and a store-shaped refusal arriving first would answer a
    # question nobody asked about a root that was never a root.
    _assignment_identity(assignment_id)
    root = _real(storage, "the manager's workspace storage")
    what = "adopting this attempt's workspace roots"
    refuse_if_held(control, storage, assignment_id, what)
    # ADMITTED, NOT MERELY CHECKED -- review 2026-09-26T07:25:48Z. The early read above can
    # be overtaken; this transaction is what a competing removal has to win or lose against.
    # THE WINDOW REACHES THE CALLER, AND ENDS AT A DEFINED HANDOVER.
    #
    # W270664 F2, review 2026-09-26T07:35:55Z: my first lifetime settled in a `finally`, so it
    # closed BEFORE the caller received the roots and a removal admitted in that gap could
    # delete what the caller was about to use. An exclusion that ends before the use it
    # protects is not one.
    #
    # SO THE ADMISSION TRAVELS WITH THE ROOTS and is settled at the point the GRANT takes
    # over -- `_granted_roots`, the "existing admitted authority" review 07:35:55Z pointed at.
    # A grant is a predicate over durable state (`_review_grant`: attachment active, line
    # reviewing, checkpoint matching; `_writer_grant`: writer active, line writing), so from
    # the binding onwards the database itself says the roots are in use. Until then this
    # window says it.
    #
    # ON FAILURE the window is settled here, because nothing was handed out, and a window
    # nobody holds would block this attempt for nothing. A caller that takes roots and binds
    # no grant releases with `release_adopted_workspace`.
    owned = _admitted_adoption(control, assignment_id, what)
    try:
        roots = _adopted_roots(root, assignment_id)
    except BaseException:
        _settled_adoption(control, assignment_id, owned)
        raise
    object.__setattr__(roots, "_adoption", (control, assignment_id, owned))
    return roots


def release_adopted_workspace(roots):
    """End an adoption's exclusion window for roots that bind no grant.

    IDEMPOTENT, and harmless on roots that carry no admission -- the tools and
    `line_assignment_workspace` hand out the same shape from paths that were never adopted.
    """
    carried = getattr(roots, "_adoption", None)
    if carried is None:
        return
    control, assignment_id, owned = carried
    # THE TOKEN IS CLEARED ONLY AFTER THE SETTLEMENT COMMITS. Review 2026-09-26T07:58:05Z:
    # clearing first meant a failed settle left the window standing with nobody holding a way
    # to end it -- an orphan by construction. A failed release therefore leaves the roots
    # still holding their admission, so the caller can retry.
    _settled_adoption(control, assignment_id, owned)
    object.__setattr__(roots, "_adoption", None)


def _adopted_roots(root, assignment_id):
    """The proved roots themselves, inside an admitted adoption."""
    home = os.path.join(root, assignment_id)
    _proved_own(home, root, assignment_id, "home")
    return AllocatedRoots(
        {name: _proved_own(os.path.join(home, name), root, assignment_id,
                           name)
         for name in ROOT_NAMES}, _MINT)


def line_assignment_workspace(storage, assignment_id, place, pinned, *,
                              control):
    """Pair an attempt's inputs with its persistent line as the output root.

    The review lifecycle authorizes the writer. This lower boundary proves the
    persistent root remains the recorded object in the manager's reserved
    namespace and mints the same roots capability the launch path consumes.
    Ordinary assignment cleanup still targets only the assignment home.

    W257624 R3, owner 262043: THE STORE IS REQUIRED HERE BECAUSE THIS ENTRY IS
    ITSELF AN ADOPTION. It takes the attempt's `inputs` from
    `adopted_assignment_workspace`, so leaving the operand off would have made
    this the bypass around the guard that entry just acquired -- an exported
    reuse path that answers roots for a held attempt. THE LINE SIDE IS NOT
    COVERED BY A CUSTODY HOLD and is not meant to be: `_REVIEW_LINE_HOME` is a
    namespace disjoint from every custody root, so no hold can name `place`.
    The attempt's inputs, which a hold CAN name, are what this checks.
    """
    # W270664 F2: THIS ENTRY ADOPTS ONLY TO PROVE THE ATTEMPT'S INPUTS and then builds its
    # OWN roots for the line home, so the adopted object is discarded here -- and with it the
    # exclusion window it carries would be lost, standing forever with nobody to release it.
    # Measured: three review-mount cases in tests.manager.test_review_cycles failed exactly
    # that way. The window is therefore released as soon as this entry has finished using what
    # it adopted; the line home it returns is a namespace no custody hold and no removal names.
    roots = adopted_assignment_workspace(storage, assignment_id,
                                         control=control)
    try:
        return _composed_line_roots(roots, storage, assignment_id, place, pinned)
    except BaseException:
        # W270664 F2, review 2026-09-26T08:02:18Z: A REJECTED COMPOSITION MUST NOT ORPHAN THE
        # WINDOW. Everything below the adoption can refuse -- an unreserved namespace, a moved
        # line object -- and the caller then gets an exception rather than roots, so nothing it
        # holds could ever release. The window is ended here on every failure path.
        release_adopted_workspace(roots)
        raise


def _composed_line_roots(roots, storage, assignment_id, place, pinned):
    """The line home composed beside the attempt's inputs, inside an admitted adoption."""
    root = _real(storage, "the manager's workspace storage")
    reserved = os.path.join(root, _REVIEW_LINE_HOME)
    boundaries.text(place, "a persistent development-line path")
    if (os.path.islink(place) or not os.path.isdir(place)
            or os.path.realpath(place) != place
            or not place.startswith(reserved + os.sep)):
        _denied("the writable line is its own directory in the reserved manager namespace")
    try:
        device, inode = pinned
    except (TypeError, ValueError):
        _denied("a persistent line pin is one device-and-inode pair")
    held = os.stat(place, follow_symlinks=False)
    if (type(device) is not int or type(device) is bool
            or type(inode) is not int or type(inode) is bool
            or (held.st_dev, held.st_ino) != (device, inode)):
        _denied("the writable line no longer has its persisted object identity")
    # W270664 F2, review 2026-09-26T07:58:05Z: THE WINDOW TRAVELS WITH THE INPUTS IT COVERS.
    # This entry returns the ATTEMPT'S OWN `inputs` beside the line home, so releasing the
    # adoption here -- which my previous cut did -- ended the exclusion while still handing
    # those inputs out. The admission is carried onto the roots this entry returns instead, and
    # ends where every other adopted set's does: at the grant binding, or at an explicit
    # release by whoever holds them.
    composed = AllocatedRoots({"inputs": roots["inputs"],
                               "workspace": place}, _MINT,
                              _grant_required=True, _line=True)
    object.__setattr__(composed, "_adoption", getattr(roots, "_adoption", None))
    object.__setattr__(roots, "_adoption", None)
    return composed


def _granted_roots(roots, grant, *, line_proof=None):
    """Bind manager-owned roots to one live lifecycle grant.

    Private because the lifecycle owner, not a runtime caller, supplies this
    revocable capability. Runtime-storage boundary composition refuses roots
    without it, so recomposing a returned path pair cannot discard revocation.
    """
    if type(roots) is not AllocatedRoots:
        _denied("a live grant binds roots this manager allocated")
    boundaries.capability(grant, "an assignment roots live grant")
    if line_proof is not None:
        boundaries.capability(line_proof, "a development-line launch proof")
    granted = AllocatedRoots(dict(roots), _MINT, grant, True,
                             roots._line, line_proof)
    # THE HANDOVER HAPPENS ONLY IF THERE IS SOMETHING TO HAND OVER TO.
    #
    # W270664 F2, review 2026-09-26T08:09:45Z. Settling at every binding was still premature:
    # `_granted_roots` is generic, and a grant can be bound when the DURABLE state says nothing
    # -- no active writer, no active attachment -- so the settle dropped the exclusion with
    # nothing behind it. The window is released here only when `_durably_in_use` already answers
    # for this attempt, which is exactly the condition that makes the removal refuse; otherwise
    # it keeps travelling with the roots and ends at an explicit release.
    carried = getattr(roots, "_adoption", None)
    if carried is not None:
        control, assignment_id, _owned = carried
        if _durably_in_use(control, assignment_id) is not None:
            release_adopted_workspace(roots)
        else:
            object.__setattr__(granted, "_adoption", carried)
            object.__setattr__(roots, "_adoption", None)
    return granted


def discard_execution_roots(storage, assignment_id, *, control, under=None):
    """Remove the two roots this attempt's WORKSPACE ENDING owns, and no more.

    W43975 review 2026-08-30T15:21:44Z [P0] chose the boundary: `inputs` and
    `workspace` -- what this attempt's execution was given and what its ending
    is about -- because `discard_workspace` removes the whole home, and the
    home also holds `custody`, where intaken material lives, plus the two
    credential roots. An ordinary cleanup using it recorded `retained`, named
    the kept artifacts, and had already deleted the locators that claim was
    about.

    Review 2026-08-30T15:39:31Z then found the boundary right and the
    EXECUTION wrong, twice:

      NOTHING IS DELETED UNTIL EVERYTHING IS PROVED. It proved and removed
      each root in turn, so a valid `inputs` beside an aliased `workspace` was
      deleted and only then refused -- a partial destructive ending whose
      refusal does not describe the mutation it already performed. The
      complete identity preflight now runs over the home and every present
      root BEFORE the home is thawed or anything is removed.

      THE IDENTITY IS HELD THROUGH USE. `_proved_own` validated a PATHNAME and
      `_remove` reopened it, so a replacement in that interval turned the
      proved root into a sibling alias and the walk followed it. Static
      `islink`/`realpath` checks cannot close that interval, and a broad catch
      afterwards cannot restore deleted material. So the proof and the removal
      are one boundary now: a directory descriptor opened `O_NOFOLLOW`, which
      is the identity, and every traversal, mode change and unlink below it is
      relative to that descriptor rather than to a name something else can
      move.
    """
    # W257624 R3: THE SECOND GUARDED ENTRY, traced from
    # review-2026-09-25T02-49-44Z. This removes `inputs` and `workspace` --
    # and `workspace` CONTAINS `result-<attempt>`, so a hold on either root
    # covers a tree this would delete. Its one product caller is
    # `intake.py:4511`, which already has the store it reads the configured
    # place from, so the operand costs that call site nothing new.
    #
    # SERIALIZED THE SAME WAY `discard_workspace` is: the hold read and the
    # removal share R1's own `BEGIN IMMEDIATE` lock, so a racing claim cannot
    # land in between. The body below is unchanged and runs inside it.
    # W257624 R3, review 2026-09-25T03-40-38Z: THIS ENTRY'S OWN OPERANDS COME
    # FIRST. The boundary inventory names `storage` and `assignment_id` as
    # `discard_execution_roots`'s, and when I gave the entry a required store the
    # store-shaped refusal started arriving first -- so two accepted inventory
    # probes escaped as TypeError and, once given the operand, would have been
    # answered about the wrong thing. `_execution_roots_removed` validates both
    # again; asking twice costs a realpath and keeps each refusal at its own
    # boundary.
    _refuse_nested_removal(control, "removing this attempt's execution roots")
    _assignment_identity(assignment_id)
    _real(storage, "the manager's workspace storage")
    return _serialized_removal(
        control, storage, assignment_id,
        "removing this attempt's execution roots",
        lambda: _execution_roots_removed(storage, assignment_id),
        under)


def _execution_roots_removed(storage, assignment_id):
    """The removal itself, called only from inside the serialized act."""
    _assignment_identity(assignment_id)
    root = _real(storage, "the manager's workspace storage")
    home = os.path.join(root, assignment_id)
    if not os.path.lexists(home):
        return ()
    _proved_own(home, root, assignment_id, "home")
    try:
        holding = os.open(home, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"attempt {name_value(assignment_id)}'s home could not be "
                f"opened as its own directory ({type(failure).__name__})")
    try:
        # THE COMPLETE PREFLIGHT, over descriptors rather than names. Opening
        # a child `O_NOFOLLOW|O_DIRECTORY` relative to the proved home refuses
        # a link ATOMICALLY -- the open either gets this attempt's directory
        # or fails -- and the descriptor it answers is what the removal then
        # uses, so there is no interval between proving and using at all.
        held = {}
        try:
            for name in ROOT_NAMES:
                try:
                    held[name] = os.open(
                        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                        dir_fd=holding)
                except FileNotFoundError:
                    continue
                except OSError as failure:
                    _denied(f"attempt {name_value(assignment_id)}'s {name} "
                            f"root is not its own directory "
                            f"({type(failure).__name__}); an aliased or stale "
                            f"entry is refused rather than removed, and "
                            f"nothing has been deleted")
            # ONLY NOW is the home thawed. W33935 closed it at `0555` so its
            # entries could not be renamed or replaced, and unlinking an entry
            # is the parent's permission -- but a thaw before the preflight
            # would open that window for a refusal that never removes.
            frozen = stat.S_IMODE(os.stat(holding).st_mode)
            os.fchmod(holding, 0o700)
            try:
                for name, opened in held.items():
                    _emptied(opened)
                    # THE NAME MUST STILL BE THE DESCRIPTOR. Everything above
                    # went through the held identity, so nothing outside this
                    # attempt could have been touched -- but the final
                    # `rmdir` takes a NAME, and a name replaced during the
                    # walk is no longer the directory this proved. Answered as
                    # a typed refusal rather than a raw `ENOTDIR`, because an
                    # ending that was interfered with is a fact an operator
                    # acts on.
                    _still_the_same(opened, name, holding, assignment_id)
                    os.rmdir(name, dir_fd=holding)
            finally:
                os.fchmod(holding, frozen)
            return tuple(sorted(held))
        finally:
            for opened in held.values():
                os.close(opened)
    finally:
        os.close(holding)


def _still_the_same(opened, name, parent, assignment_id):
    """The held descriptor and the name, proved to be one directory."""
    held = os.stat(opened)
    try:
        found = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except OSError as failure:
        _denied(f"attempt {name_value(assignment_id)}'s {name} root could not "
                f"be re-identified before its removal "
                f"({type(failure).__name__})")
    if (found.st_dev, found.st_ino) != (held.st_dev, held.st_ino):
        _denied(f"attempt {name_value(assignment_id)}'s {name} root was "
                f"replaced while its ending was removing it; nothing outside "
                f"the proved directory was touched, and the removal stops "
                f"rather than acting on a name that is no longer what it "
                f"proved")


def _emptied(opened):
    """Empty ONE proved directory, descriptor-relative and no-follow.

    Every child is unlinked relative to the descriptor its parent was opened
    as, and a child directory is opened `O_NOFOLLOW` before it is descended --
    so a name replaced mid-walk is refused at the open rather than followed.
    Nothing here resolves a path.

    THE CHMOD IS A REPAIR, AND ONLY ON THIS MANAGER'S OWN DIRECTORIES.
    W39358, measured: `os.fchmod` was unconditional, and `chmod` is the
    OWNER's operation -- so the first real worker tree this build ever removed
    died `EPERM` on `/output/proposal`, a directory the CONTAINER's fixed uid
    65532 created and this manager does not own. Every ending after a
    completed worker turn was unreachable for that reason.

    A directory this manager does not own is not one it may repair, and it
    does not need to: `custody.normalize_directory` runs as the owner of the
    worker's objects immediately before this and grants the workspace GROUP
    rwx on every one of them, which is the access this walk actually uses.
    That act is exactly why the custodian grants the group instead of
    chowning. If it did not run, the `unlink` below refuses on its own and the
    removal fails closed -- which is the honest ending, and a nearer one than
    a chmod that could never have succeeded.
    """
    if os.fstat(opened).st_uid == os.getuid():
        os.fchmod(opened, 0o700)
    for name in os.listdir(opened):
        try:
            below = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                            dir_fd=opened)
        except NotADirectoryError:
            os.unlink(name, dir_fd=opened)
            continue
        except OSError:
            # A LINK, a device, a socket -- anything that is not a directory
            # this manager may descend. It is removed as an ENTRY and never
            # followed.
            os.unlink(name, dir_fd=opened)
            continue
        try:
            _emptied(below)
        finally:
            os.close(below)
        os.rmdir(name, dir_fd=opened)


def _proved_own(place, root, assignment_id, what):
    """This attempt's OWN directory at its own path, or a refusal.

    The same question `_own_directory` asks at allocation, asked read-only:
    not a link, a real directory, and resolving to exactly its own path under
    the configured store.
    """
    expected = os.path.join(os.path.realpath(root), assignment_id)
    if what != "home":
        expected = os.path.join(expected, what)
    if os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != expected:
        _denied(f"{name_value(place)} is not attempt "
                f"{name_value(assignment_id)}'s own {what} at its own path; "
                f"an aliased or stale entry is refused rather than removed, "
                f"because material under it would be another attempt's")
    return place


def _discarded_roots(home, root, assignment_id):
    removed = []
    for name in ROOT_NAMES:
        place = os.path.join(home, name)
        if not os.path.lexists(place):
            continue
        # EACH ROOT PROVED THIS ATTEMPT'S OWN, not merely contained. A root
        # entry linked to another attempt's tree resolves inside the store
        # too, and containment would accept it.
        _proved_own(place, root, assignment_id, name)
        _remove(place)
        removed.append(name)
    return tuple(removed)



def discard_tree(place):
    """Remove one tree this manager owns, whatever its modes are now.

    W26283. `copied_manifest` refuses a destination that already holds an
    entry, so a caller whose earlier attempt stopped part-way needs a way to
    take that prefix away -- and custody is FROZEN READ-ONLY when it is
    complete, so a partial tree from a stopped process may be unwritable too.
    `_remove` already makes each directory writable as it goes and never
    follows a link out of the tree, which is the whole duty.

    It is here rather than in the caller because the caller would otherwise
    reach for `shutil.rmtree`, and the manager's ruled dependency set does not
    include it -- a rule the repository enforces and which caught exactly that
    import. `rmtree` would also be the weaker answer: it has followed links
    out of a tree before, and this module already owns not doing that.

    Answers whether anything was there, so an absent tree is the state asked
    for rather than a refusal.
    """
    if not os.path.isdir(place):
        return False
    _remove(place)
    return True


def _thaw(place):
    """Open this directory enough to empty it, IF this manager may.

    W33936: it may not always, and that is a fact about the corrected
    mechanism rather than a fault here.  `chmod` is the OWNER's operation, and
    once the worker can write the workspace it creates directories it owns --
    so a manager holding only the configured group is refused `EPERM` on them.
    Swallowing that is right: the thaw is an ATTEMPT to make removal possible,
    and whether removal is possible is answered by removal.  What is not right
    is letting the raw error out of a helper whose caller cannot tell it from
    a missing directory, which is why the two are separated here.
    """
    try:
        os.chmod(place, 0o700)
    except PermissionError:
        return False
    return True


def _removed_pinned_home(root, assignment_id, *, what, pinned=None):
    """Remove this attempt's home as an OBJECT, through a descriptor that cannot be moved.

    W270664 F2, reviews 2026-09-26T06:54:02Z and 07:01:39Z. A stat comparison before the
    effect is a time-of-check test: the reviewer swapped the home after it answered and the
    deletion, which still resolved a pathname, removed the substitute.

    SO THE DESTRUCTIVE PART IS BOUND TO THE OPEN OBJECT. The home is opened
    `O_NOFOLLOW|O_DIRECTORY` relative to its parent's own descriptor, its `fstat` is compared
    against the entry the parent gave, and the CONTENTS are removed through
    `/proc/self/fd/<descriptor>` -- a path that resolves to the open inode, so a rename of
    the home, of its name, or of any ancestor cannot redirect the walk. The reviewed two-pass
    mount-aware walk runs unchanged beneath it.

    AND THE ONE WINDOW THAT REMAINS IS STATED RATHER THAN CLAIMED CLOSED. Review 07:01:39Z is
    right that parent-fd plus stat plus `rmdir` is not exact-child authority: between the
    stat and the `rmdir` the name can be replaced again, and this build has no `renameat2`
    exchange or by-handle unlink to close it. What that window can cost is bounded and worth
    naming exactly: the CONTENTS are already gone from the pinned object by then, and what a
    late swap could lose is one EMPTY directory that something else put at the name. Nothing
    with contents can be reached through it, because the only path that ever reaches contents
    here is the descriptor's.

    AN UNREADABLE HOME IS UNCERTAIN, NOT ABSENT: only `ENOENT` is absence.
    """
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            entry = os.stat(assignment_id, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as failure:
            _denied(f"{what} could not read this attempt's home relative to its parent "
                    f"({failure.strerror}); an unreadable home is uncertain rather than "
                    f"absent and this act is refused")
        if not stat.S_ISDIR(entry.st_mode):
            _refuse(f"{what} found a non-directory where this attempt's home belongs")
        home = os.open(assignment_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                       dir_fd=parent)
        try:
            opened = os.fstat(home)
            if (opened.st_dev, opened.st_ino) != (entry.st_dev, entry.st_ino):
                raise ContractRefusal(
                    "runtime-observation", "identity-mismatch",
                    f"{what} opened an object the parent's entry does not name; a removal "
                    f"acts on the object it proved")
            # AND AGAINST THE OBJECT THE ADMISSION AUTHORIZED, which is the whole point.
            #
            # W270664 F2, measured against review 2026-09-26T07:01:39Z's probe: comparing the
            # opened object only against the parent's CURRENT entry is self-consistent and
            # therefore proves nothing -- a replacement swapped in before this call is opened,
            # matches itself, and is deleted. The identity that authorizes this act is the one
            # recorded in the ownership record BEFORE admission, so that is what the opened
            # object is compared against. A substitute is refused instead of removed.
            if pinned is not None and (opened.st_dev, opened.st_ino) != tuple(pinned):
                raise ContractRefusal(
                    "runtime-observation", "identity-mismatch",
                    f"{what} was admitted for one object and this name now resolves to "
                    f"another; the removal is performed on the object its authority names "
                    f"and a replacement is refused rather than deleted")
            _removed_through_handles(home, what)
        finally:
            os.close(home)
        again = os.stat(assignment_id, dir_fd=parent, follow_symlinks=False)
        if (again.st_dev, again.st_ino) != (entry.st_dev, entry.st_ino):
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"{what} emptied the object it was authorized for and the parent's entry "
                f"now names a different one; the final removal is not performed")
        os.rmdir(assignment_id, dir_fd=parent)
    finally:
        os.close(parent)


def _removed_through_handles(root, what):
    """Remove an admitted tree through RETAINED DIRECTORY HANDLES, never through names.

    W270664 F2, review 2026-09-26T07:14:23Z's sequence. Every earlier shape stored PATHS and
    re-checked them, and review 07:07:30Z proved that a descendant replaced between the
    admission and the effect is resolved through -- a time-of-check test cannot bind an
    object, however many times it is repeated.

    SO THE ADMISSION KEEPS WHAT IT PROVED. Pass one descends with `scandir` over an open
    directory handle, opens each child directory `O_NOFOLLOW|O_DIRECTORY` RELATIVE to its
    parent's handle, and keeps that handle. Pass two operates on those same handles: `fchmod`
    on the handle, `unlink`/`rmdir` by NAME RELATIVE TO the handle. No name is resolved from
    the root twice and no absolute path is rebuilt, so nothing a descendant becomes later can
    redirect a scan, a mode change or a deletion outside the admitted objects.

    THE REVIEWED GUARANTEES ARE PRESERVED. The device comparison and the mount-table check
    still run over every directory BEFORE anything is removed -- `fstat` on the handle for the
    device, and the handle's own `/proc/self/fd` link resolved for table membership, which is a
    read of the kernel's answer rather than a path the caller could swap. The order is still
    admit-everything-then-remove-deepest-first, so a refusal anywhere precedes every unlink.
    The worker-owned refusal is kept: a child this manager may not modify stops the act.

    EVERY HANDLE IS CLOSED on success, refusal and failure.
    """
    base = os.fstat(root).st_dev
    mounted = mount_points(what=what)
    admitted = []
    opened = []
    try:
        pending = [(None, None, root)]
        while pending:
            parent, name, handle = pending.pop(0)
            if os.fstat(handle).st_dev != base:
                _denied(f"{what} reached a directory on another filesystem than the tree it "
                        f"is removing, so it is a mount rather than material this manager "
                        f"created; cleanup removes only what this manager made")
            if os.path.realpath(f"/proc/self/fd/{handle}") in mounted:
                _denied(f"{what} reached a mount point in this process's own mount table, "
                        f"so it is somebody else's material behind a directory this manager "
                        f"made; a bind mount from the same filesystem keeps the device "
                        f"number, which is why the table is asked as well")
            admitted.append((parent, name, handle))
            with os.scandir(handle) as entries:
                children = [entry.name for entry in entries
                            if entry.is_dir(follow_symlinks=False)]
            for child in children:
                held = os.open(child, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=handle)
                opened.append(held)
                pending.append((handle, child, held))
        for parent, name, handle in reversed(admitted):
            _thaw_handle(handle, what)
            with os.scandir(handle) as entries:
                members = [(entry.name, entry.is_dir(follow_symlinks=False),
                            entry.stat(follow_symlinks=False)) for entry in entries]
            for member, is_directory, held in members:
                if held.st_uid != os.getuid() and not os.access(
                        member, os.W_OK, dir_fd=handle, follow_symlinks=False):
                    _denied(f"{what} could not remove {name_value(member)}: it is owned by "
                            f"uid {held.st_uid} and this manager is uid {os.getuid()}; "
                            f"cleanup fails closed rather than leaving a partly-removed tree")
                if is_directory:
                    os.rmdir(member, dir_fd=handle)
                else:
                    os.unlink(member, dir_fd=handle)
            if parent is not None:
                os.rmdir(name, dir_fd=parent)
    finally:
        for held in opened:
            try:
                os.close(held)
            except OSError:
                pass


def _thaw_handle(handle, what):
    """Make an admitted directory writable THROUGH ITS HANDLE, never through its name."""
    try:
        mode = stat.S_IMODE(os.fstat(handle).st_mode)
        os.fchmod(handle, mode | stat.S_IRWXU)
    except OSError as failure:
        _denied(f"{what} could not make an admitted directory writable "
                f"({failure.strerror}); cleanup fails closed")


def _remove(place, *, final=True):
    """A depth-first removal that never follows a link OR A MOUNT out of the
    tree.

    W71917 ADDED THE SECOND HALF, and it is a new hazard rather than an old
    one nobody noticed. Until this Work every directory under an assignment
    root was material this manager created, so "never follow a link" was the
    whole of "never leave the tree". The nominated-source boundary puts an
    empty MOUNTPOINT inside the input root on purpose, and a mountpoint is not
    a symbolic link: `followlinks=False` does not stop a walk descending
    through one, and the material on the other side belongs to whoever
    nominated it.

    In the ordinary arc there is nothing to descend into -- the bind lives in
    the container's own mount namespace and the host-side directory stays
    empty, so cleanup removes an empty directory and this check never fires.
    It exists for the case that is not ordinary: a host-side bind an operator
    or a future profile established, still live when an ending runs. Deleting
    somebody else's Work tree is not a failure this manager may discover
    afterwards, so it is refused before an entry inside it is touched.

    CHECKED TOP-DOWN, BEFORE ANY DESCENT, AND BEFORE ANY REMOVAL AT ALL.

    The superseded reasoning is recorded because it was WRONG and its wrongness
    is the whole of this correction. It said: "checked per directory, inside
    the existing walk, and the bottom-up order is what makes one pass enough --
    a directory is always visited before its parent, so a foreign mount is
    refused while every entry it holds is still there." That is true of a
    mount's own entries and false of everything below them. `os.walk` with
    `topdown=False` yields a mount's SUBDIRECTORIES before the mount itself, so
    a mount containing one directory had that directory emptied first and the
    refusal arrived after the data was gone. The second W71917 review
    reproduced exactly that.

    So the walk is now TOP-DOWN, which is the order in which a mount can be
    recognised before anything under it is reached, and removal happens in a
    second pass over the directories the first one ADMITTED. A refusal
    anywhere therefore precedes every unlink rather than merely preceding the
    unlinks in one subtree. What is buffered between the passes is the
    directory paths and not their contents, and the second pass lists each
    admitted directory again -- one extra listing per directory, against a
    guarantee that no foreign entry is ever removed.

    THE TABLE DECIDES, NOT THE DEVICE NUMBER. W71917 run7 review [P0]: this
    compared `st_dev` against the tree's root and nothing else, and a bind
    mount from the SAME filesystem keeps the bound directory's device number --
    so a source bind-mounted from the same disk passed the test and its
    contents were walked and unlinked. `st_dev` answers "is this another
    filesystem", which is a different question from "is this a mount", and only
    the second one is the one being asked. The kernel's own table answers it;
    the device comparison is KEPT beside it because it needs no `/proc` and
    still catches a cross-device mount if the table is ever the thing that is
    wrong.
    """
    try:
        # THE ROOT IS MEASURED WITH `stat`, NOT `lstat`. W270664 F2, measured 2026-09-26:
        # when the caller binds the removal to an open object by passing
        # `/proc/self/fd/<fd>`, `lstat` answers PROCFS for that magic symlink and every real
        # child then looks cross-device, so this function's own mount refusal rejected the
        # manager's own workspace -- six errors. `stat` follows the one link the CALLER
        # supplied deliberately and is identical to `lstat` for the ordinary real path every
        # other caller passes. The walk below still uses `followlinks=False`, so no symlink
        # INSIDE the tree is followed; only the root the caller named is.
        base = os.stat(place).st_dev
    except OSError as failure:
        _refuse(f"the tree at {name_value(place)} could not be measured "
                f"before removal ({type(failure).__name__})")
    # READ ONCE, BEFORE ANYTHING IS UNLINKED. A table re-read per directory
    # would be a window: a mount established mid-walk would be absent from the
    # reading that mattered. Reading first also means an unreadable table
    # refuses the cleanup before it has removed a single entry.
    mounted = mount_points(what=f"removal of the tree {name_value(place)}")
    admitted = []
    for current, _directories, _files in os.walk(place, topdown=True,
                                                 followlinks=False):
        # REFUSED BEFORE THE WALK DESCENDS. `topdown=True` yields a directory
        # before its children, and a refusal here ends the whole cleanup, so a
        # mount is recognised while everything under it is still untouched and
        # unvisited.
        # THE ROOT IS NOT RE-MEASURED BY ITS NAME. W270664 F2, measured: `base` above is the
        # root's device, and when the caller binds the removal to an open object the root's
        # own name is a `/proc/self/fd/<fd>` magic symlink, whose `lstat` answers PROCFS --
        # so re-checking it against itself refused. Every DESCENDANT is still measured with
        # `lstat`, which is where the mount can actually appear; a component of the path is
        # resolved by the kernel, so a descendant's answer is about the real directory.
        if current != place and os.lstat(current).st_dev != base:
            _denied(f"{name_value(current)} is on another filesystem than the "
                    f"tree {name_value(place)} this manager is removing, so "
                    f"it is a mount rather than material this manager "
                    f"created. Cleanup removes only what this manager made; "
                    f"the material behind a nominated source belongs to "
                    f"whoever nominated it and is never this manager's to "
                    f"delete.")
        if os.path.realpath(current) in mounted:
            _denied(f"{name_value(current)} is a mount point in this "
                    f"process's own mount table, so it is somebody else's "
                    f"material reached through a directory this manager made. "
                    f"A bind mount from the same filesystem keeps the bound "
                    f"directory's device number, so the device comparison "
                    f"above cannot see it. Cleanup removes only what this "
                    f"manager created; what is behind a mount belongs to "
                    f"whoever mounted it and is never this manager's to "
                    f"delete.")
        admitted.append(current)
    # DEEPEST FIRST, OVER THE ADMITTED DIRECTORIES ONLY. Reversing a top-down
    # order puts every child before its parent, which is what `rmdir` needs,
    # and by now the whole tree has already passed the boundary above.
    for current in reversed(admitted):
        # THAWED ONCE, BEFORE ANYTHING IN IT IS REMOVED.  Unlinking a file and
        # removing a subdirectory are both writes to THIS directory, so the
        # thaw belongs here rather than inside the file loop -- W33935
        # re-review: once the assignment home was frozen, a home holding only
        # directories never reached that loop and `rmdir` on its children was
        # denied by the home's own mode.
        _thaw(current)
        for child, is_directory in _entries(current):
            if is_directory:
                # Already emptied: it came earlier in this reversed order.
                _thaw(child)
                _unlink(child, current, directory=True)
            else:
                _unlink(child, current)
    _thaw(place)
    if final:
        os.rmdir(place)


def _entries(place):
    """This directory's children as (path, is_directory) pairs.

    A SYMBOLIC LINK IS NEVER A DIRECTORY HERE, whatever it points at, which is
    the same rule the walk above is under: what removal does to a link is
    unlink it, and following one to decide would be leaving the tree to answer
    a question about an entry inside it.
    """
    try:
        with os.scandir(place) as reading:
            return [(entry.path, entry.is_dir(follow_symlinks=False))
                    for entry in reading]
    except OSError as failure:
        _refuse(f"the directory {name_value(place)} could not be read before "
                f"removal ({type(failure).__name__})")


def _unlink(child, parent, *, directory=False):
    """Remove one entry, and say WHOSE it is when it cannot be removed.

    W33936: a raw `PermissionError` out of a cleanup walk names a path and
    nothing else, and the situation this correction creates is specific enough
    to deserve a sentence.  The workspace is writable by the configured group,
    so the worker creates content this manager DOES NOT OWN -- and a directory
    the worker created under its own umask can be one the manager may neither
    open for writing nor `chmod`.  The removal fails closed, which is right;
    what a diagnostic has to add is which party owns the thing in the way, so
    an operator is not left comparing modes by hand.
    """
    try:
        os.rmdir(child) if directory else os.unlink(child)
        return
    except PermissionError:
        # ONLY THIS ONE IS REWORDED.  A non-empty directory, a vanished entry
        # or a device error mean what they say and are the walk's to raise; a
        # permission refusal is the one whose cause is invisible in the message.
        pass
    held = os.lstat(child)
    owner, mode = held.st_uid, oct(held.st_mode & 0o7777)
    _denied(f"the manager could not remove {name_value(child)}: it is owned "
            f"by uid {owner} at mode {mode} and this manager is uid "
            f"{os.getuid()}. A workspace the worker may write holds content "
            f"the worker owns, and neither `chmod` nor a write inside it is "
            f"this manager's to perform. Cleanup fails closed rather than "
            f"leaving a partly-removed tree.")
