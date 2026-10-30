"""THE SOURCE/WORKSPACE BOUNDARY: a nominated tree the manager mounts and
never reads, and a workspace the manager creates and keeps custody of.

W71917, the leaf `job_manager` names as "read-only source mounts and
disk-backed workspaces". It replaces the bootstrap's ordinary COPIED source
with a delivery this manager can perform without ever looking inside the
material it delivers.

WHAT THE ORDINARY LOCAL PATH DOES NOW, and the whole of it:

  - it VALIDATES one nominated source directory -- absolute, canonical, its own
    unaliased directory, outside this manager's own storage -- and pins the
    (device, inode) that validation saw;
  - it establishes an empty MOUNTPOINT for it inside the assignment's frozen
    input root, so the engine lands the read-only bind at `/input/source`;
  - it proves the assignment's writable root is DISK-BACKED and that its
    filesystem currently holds the DECLARED CAPACITY;
  - and it composes the two mounts.

WHAT IT DELIBERATELY DOES NOT DO, because every one of these was what the
copied bootstrap did: it does not walk, copy, snapshot, enumerate, hash or
digest the nominated source, and it opens no file under it. A directory is
opened once with `O_DIRECTORY | O_NOFOLLOW` to fix its identity, and a
descriptor that is never read is not an enumeration. `workspaces.
directory_manifest` and `workspaces.copied_manifest` are not reachable from
anything here.

THE MANAGER IS GIT-AGNOSTIC AND THIS MODULE IS WHERE THAT IS STRUCTURAL. The
source descriptor's `consumption` extension carries three words. Two of them
are THIS manager's -- how the material is delivered, and what the workspace is
backed by -- and both are closed vocabularies validated here. The third is the
PROFILE, and it is bounded opaque text this manager never reads, compares
against a list, or infers: a version-control profile is a property of the
worker that consumes the mount, and the party that mounts a directory has no
business deciding what is in it. `baton_v12.source_profiles` is where that
word means something, it is outside this package, and nothing here imports it.

A NOMINATED SOURCE IS NOT A STAGED SOURCE, and the input manifest says which
it is rather than leaving a reader to infer it. A staged source carries a
`contentManifest` this manager MEASURED; a nominated one carries the manifest
of the empty mountpoint this manager created, because that -- and not the
material behind the bind -- is what it staged. Declaring the boundary in
`consumption` is what makes the empty manifest an honest statement instead of
a silent one.

TMPFS IS SCRATCH AND IS BOUNDED, AND NOTHING THE ASSIGNMENT OWES RELIES ON IT.
The runtime's private `/tmp` and `/dev/shm` are small, non-executable and
memory-backed; a checkout, a build cache, test artifacts, the declared output
and the logs are none of those things. `NON_SCRATCH_USES` names them, the
declared capacity's floor is strictly above the whole scratch bound, and
`check_disk_backed` refuses a workspace on a memory filesystem before a
runtime starts rather than after a worker has filled one.

THE WORKSPACE BOUND IS AN ADMISSION PROOF AND NOT A LIVE CEILING, and W71917
rules that it says so in its own names. Scratch is bounded by the kernel: the
tmpfs mounts above carry a size and a worker that fills one is stopped by the
filesystem. The workspace is an ordinary writable bind, and a hard byte bound
over one needs project quotas, a per-attempt loopback image or a storage
driver option -- every one of which needs privilege or host configuration this
rootless launch was deliberately built without. So `WorkspaceCapacity` is
exactly what it can be proved to be: what the deployment DECLARES one
assignment needs, held to this build's floor and ceiling at admission, and
proved against the filesystem's currently available bytes before a runtime
starts. IT IS NEITHER A RESERVATION NOR A RUNNING LIMIT. Nothing allocates
those bytes, nothing measures the workspace while a turn is in flight, and a
worker CAN therefore fill the backing filesystem after admission. That is a
named MVP exposure rather than a gap left implied, and it is why no member
here carries an entry ceiling: a number this component never applies would be
a limit's name over no mechanism, which is the state the run7 review found.
Live byte and entry ceilings are separate v12 hardening because they change
the storage or privilege model.
"""

import hashlib
import json
import os
import stat

from ..contracts import ContractRefusal
from ..contracts.errors import label_of, name_value
from . import boundaries, workspaces

__all__ = ["SOURCE_NAME", "SOURCE_TARGET", "WORKSPACE_TARGET",
           "SCRATCH_TARGET", "SCRATCH_BYTES", "SHARED_MEMORY_TARGET",
           "SHARED_MEMORY_BYTES", "SCRATCH_MOUNTS", "NON_SCRATCH_USES",
           "MEMORY_FILESYSTEMS", "MOUNTINFO",
           "CONSUMPTION_KEY", "CONSUMPTION_MEMBERS", "DELIVERY", "BACKING",
           "MAX_PROFILE", "MIN_WORKSPACE_BYTES", "MAX_WORKSPACE_BYTES",
           "SCRATCH_AGGREGATE_BYTES", "SELECTED_SCRATCH_MOUNTS",
           "VERIFIER_SCRATCH_BYTES", "VERIFIER_PARENT", "VERIFIER_ROOTS",
           "VERIFIER_FILESYSTEM", "VERIFIER_OPTIONS", "VERIFIER_MODE",
           "LAYOUT_SCHEMA", "LAYOUT_TARGET", "LAYOUT_MEMBERS",
           "MARKER_TARGET", "MARKER_SCHEMA", "MARKER_MEMBERS",
           "LAYOUT_NAME", "MAX_LAYOUT_BYTES",
           "layout_topology", "layout_digest", "compose_verifier_layout",
           "image_layout_marker", "layout_bytes", "LayoutDelivery",
           "materialize_verifier_layout",
           "NominatedSource", "WorkspaceCapacity", "SourceBoundary",
           "adopt_source_boundary", "boundary_mounts", "check_disk_backed",
           "compose_runtime_storage_boundary", "compose_source_boundary",
           "declared_profile", "filesystem_of",
           "nominate_source", "source_consumption", "source_mountpoint",
           "workspace_capacity"]

# THE WORKER'S FIXED PATHS, as constants of the contract rather than operands.
# The same rule `oci.INPUT_TARGET` and `launch.LAUNCH_TARGET` are under: a path
# a plan could vary is a path a runtime can be pointed at wrongly, and this one
# decides which directory an agent believes is the Work it was given.
SOURCE_NAME = "source"
SOURCE_TARGET = "/input/source"
WORKSPACE_TARGET = "/output"

# THE BOUNDED PRIVATE SCRATCH, declared here and composed by `oci` from these
# values rather than spelled a second time there. Two spellings of one bound
# agree until they don't, and this one is load-bearing twice: it is what the
# runtime actually gets, and it is the floor a declared capacity must clear.
SCRATCH_TARGET = "/tmp"
SCRATCH_BYTES = 64 * 1024 * 1024
SHARED_MEMORY_TARGET = "/dev/shm"
SHARED_MEMORY_BYTES = 16 * 1024 * 1024

# W325695: THE VERIFIER'S OWN PRIVATE ROOTS, one bounded tmpfs each.
#
# The defect this answers: the verifier's roots were handed to it as
# `/proc/self/fd/<n>` descriptor paths, which a CHILD cannot resolve -- a
# descriptor is per-process, so an ordinary `git` or a nested adapter in a
# grandchild found nothing at the only name it was given. The remedy is
# ordinary stable pathnames whose non-replaceability comes from the mount
# rather than from a held descriptor.
#
# WHY A SEPARATE MOUNT PER ROOT and not four directories in one: a private
# mount is the thing a process sharing this uid cannot rename, and per-root
# mounts are also what makes the per-root byte bound real. One shared mount
# would let a filled cache take the home root's room with it.
#
# THE PARENT IS NOT A MOUNT. `preparation-325908/TASK.md` selects "ordinary
# root-owned 0755 image directories in read-only rootfs, outside all writable
# mounts; no mutable ancestor" -- so `/run` and `/run/baton-verifier` are
# image scaffolding, and the worker proves that rather than trusting it.
VERIFIER_PARENT = "/run/baton-verifier"
# name -> (target, bytes). The NAME is the verifier environment's own
# vocabulary, so the manager and the worker cannot disagree about which root
# is which; `claude_agent` reads these names and never invents one.
VERIFIER_ROOTS = (
    ("HOME", f"{VERIFIER_PARENT}/home", 4 * 1024 * 1024),
    ("TMPDIR", f"{VERIFIER_PARENT}/tmp", 16 * 1024 * 1024),
    ("XDG_CACHE_HOME", f"{VERIFIER_PARENT}/cache", 4 * 1024 * 1024),
    ("PYTHONPYCACHEPREFIX", f"{VERIFIER_PARENT}/pycache", 8 * 1024 * 1024),
)
VERIFIER_FILESYSTEM = "tmpfs"
# The options every scratch mount already carries, named here because the
# worker PROVES this exact set and a second spelling would drift from it.
VERIFIER_OPTIONS = ("rw", "noexec", "nosuid", "nodev")
VERIFIER_MODE = 0o700

# THE LEGACY TABLE, AND IT IS EXACTLY WHAT IT ALWAYS WAS.
#
# W325695 review 2026-10-28T17-58-14Z [3]: the first cut reduced `/tmp` to
# 32 MiB and put the four verifier roots in here, and `oci.RESTRICTIONS`
# applies this table to EVERY run -- so an unselected runtime got the new
# roots and the smaller `/tmp` with no marker, no document and no selection
# anywhere. "This contradicts preserved legacy topology/capacity." It did, and
# the correction is that the redistribution is now a property of the SELECTED
# PROFILE below rather than of this module's one global table.
SCRATCH_MOUNTS = (
    (SCRATCH_TARGET, SCRATCH_BYTES),
    (SHARED_MEMORY_TARGET, SHARED_MEMORY_BYTES),
)

# AND THE SELECTED TABLE, which only a runtime holding a layout delivery gets.
#
# `/tmp` GIVES UP EXACTLY WHAT THE ROOTS TAKE. TASK.md: "This redistributes
# old shared /tmp 64MiB, not extra capacity." So the selected `/tmp` is the
# legacy 64 MiB minus the four roots' 32 MiB, computed here rather than
# written down, because a second literal is how the two would stop adding up.
VERIFIER_SCRATCH_BYTES = SCRATCH_BYTES - sum(
    size for _name, _target, size in VERIFIER_ROOTS)
SELECTED_SCRATCH_MOUNTS = (
    (SCRATCH_TARGET, VERIFIER_SCRATCH_BYTES),
    (SHARED_MEMORY_TARGET, SHARED_MEMORY_BYTES),
) + tuple((target, size) for _name, target, size in VERIFIER_ROOTS)

# THE AGGREGATE IS THE SAME ON BOTH PATHS, AND THAT IS THE POINT -- so the
# workspace floor derived from it is one number whether or not a layout was
# selected, and a deployment does not acquire or lose room by selecting the
# new topology. The existing 16 MiB legacy log decoy still accounts separately
# for a 96 MiB total. ASSERTED rather than described, because a later edit
# that moved one number and left this comment would grow the bound silently.
SCRATCH_AGGREGATE_BYTES = sum(size for _target, size in SCRATCH_MOUNTS)
assert SCRATCH_AGGREGATE_BYTES == 80 * 1024 * 1024, SCRATCH_AGGREGATE_BYTES
assert sum(size for _target, size in SELECTED_SCRATCH_MOUNTS) == (
    SCRATCH_AGGREGATE_BYTES)
assert VERIFIER_SCRATCH_BYTES == 32 * 1024 * 1024, VERIFIER_SCRATCH_BYTES
# No two roots may name one directory. The review's own counterexample: a
# parser that checks four canonical strings accepts the SAME mounted
# directory named for all four roles, which would put the cache and the home
# root in one another's room and defeat the per-root bound above.
assert len({target for _name, target, _size in VERIFIER_ROOTS}) == len(
    VERIFIER_ROOTS)
assert len({name for name, _target, _size in VERIFIER_ROOTS}) == len(
    VERIFIER_ROOTS)

# WHAT MAY NOT RELY ON SCRATCH, written out because "not tmpfs" is a rule about
# these five things and a reader should not have to reconstruct which. Every
# one of them either outlives the turn that produced it or is unbounded by
# nature, and both are the wrong shape for a small memory filesystem that
# vanishes with the container.
NON_SCRATCH_USES = ("checkout", "build-cache", "test-artifacts", "output",
                    "logs")

# The kernel's memory-backed filesystems, by the name `mountinfo` prints. A
# denylist is the right shape HERE and not elsewhere: the question is not "is
# this one of ours" -- there is no set of ours, a deployment may put its
# storage on any real filesystem it likes -- it is "is this one of the ones
# that is not storage at all", and that set is small, kernel-defined and
# nameable.
MEMORY_FILESYSTEMS = ("tmpfs", "ramfs", "devtmpfs")

MOUNTINFO = "/proc/self/mountinfo"

# The manifest extension this boundary is declared in. `sourceDescriptor.
# consumption` is the frozen schema's own open extension point -- its property
# names are `<namespace>/<version>` and its values are the consuming party's --
# so declaring here needs no schema change and cannot collide with another
# extension's word.
CONSUMPTION_KEY = "baton.source-boundary/1"
CONSUMPTION_MEMBERS = ("delivery", "workspace", "profile")

# THIS MANAGER'S TWO WORDS, and they are constants rather than vocabularies.
#
# A closed set with one member is a set; a CONSTANT is a statement that there
# is no choice here. There is no choice here: this component performs exactly
# one delivery -- a read-only bind of a directory it did not read -- onto
# exactly one kind of workspace, and a second word would be a second mechanism
# that does not exist. When one is built it brings its own extension version
# with it, which is what the `/1` is for.
DELIVERY = "nominated-mount"
BACKING = "disk"

# The profile word's ceiling, and the ONLY thing this manager decides about it.
# Bounded because it is text that reaches a durable document; opaque because
# what it means is the worker's, and a manager that compared it against a list
# would have taken the decision the list encodes.
MAX_PROFILE = 64

# THE DECLARED CAPACITY'S FLOOR IS THE WHOLE SCRATCH BOUND, and this is the
# deterministic form of "the ruled uses must not rely on tmpfs".
#
# A workspace declared no larger than the private scratch it sits beside is a
# workspace whose entire contents would have fitted in that scratch -- so
# nothing about the delivery would have distinguished a disk-backed checkout
# from one that happened to live in memory, and the rule would hold by
# accident rather than by construction. Strictly greater is what makes the
# distinction provable: at the floor plus one byte, `/tmp` cannot hold the
# workspace even in principle.
#
# It is a FLOOR ON THE DECLARATION and not a reservation. Nothing allocates
# these bytes; `check_disk_backed` proves the filesystem is real storage and
# the capacity proof below asks whether it currently holds what was declared.
# W325695: derived from the scratch aggregate rather than from two names, and
# the two tables above are asserted to have the SAME aggregate -- so the floor
# is one number on the legacy and the selected path alike. It is the same
# 80 MiB it has always been.
MIN_WORKSPACE_BYTES = SCRATCH_AGGREGATE_BYTES

# And this component's own ceiling, which is the manager's existing policy
# bound on any one delivery. A declared capacity above it is a configuration
# mistake rather than a workload.
MAX_WORKSPACE_BYTES = workspaces.MAX_BYTES

# The token that says an answer came from this module's own proof. The same
# `_MINT` discipline `workspaces.WorkspaceGroup` is under, and for the same
# reason: a capability a caller can construct is a capability a caller chose.
_MINT = object()


def _refuse(message, code="path"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- what a path is actually sitting on ---------------------------------------


def filesystem_of(place):
    """The filesystem TYPE the kernel says this path is on.

    READ FROM `mountinfo`, because `statvfs` cannot answer it. `os.statvfs`
    reports how much room a filesystem has and says nothing about what kind it
    is, and "how much room" is exactly the question a memory filesystem
    answers reassuringly: a 64 MiB tmpfs reports 64 MiB free and a worker
    fills it with a checkout that then disappears with the container.

    THE LONGEST MOUNT POINT THAT CONTAINS THE RESOLVED PATH, which is what the
    kernel itself resolves to. Prefix order is not enough on its own --
    `/output` and `/out` share four characters and are two filesystems -- so
    containment is compared by SEGMENTS, and the longest match wins because a
    later mount over an earlier one is the one a path actually reaches.

    `mountinfo` ESCAPES ITS OWN SEPARATORS, and a reader that ignored that
    would mis-key any mount point holding a space -- so `\\040` and its three
    siblings are decoded before anything is compared. The filesystem type
    lives after the ` - ` separator, whose position varies with the number of
    optional fields; splitting on the separator is how the kernel documents
    it and is why this does not index by column.
    """
    # A LITERAL LABEL AT THE OWNER, and this is the owner: `filesystem_of` is
    # public and takes a caller's path, so the crossing happens here rather
    # than wherever the answer is later compared. The same rule
    # `workspaces._real` and `oci.canonical_source` are written under, and for
    # the same reason -- the inventory attributes an owned entry by the label
    # written at the site, so a computed one is a boundary it cannot place.
    boundaries.text(place, "a filesystem path")
    real = os.path.realpath(place)
    # ONE READER FOR ONE FILE. W71917 run7 review [P0] gave cleanup its own
    # need for this table, and two modules parsing `mountinfo` with two copies
    # of the escape rules is the drift that ends with them disagreeing about
    # which directory a mount point is. The reader is `workspaces.mount_table`
    # -- the lower module, so this one imports it rather than the reverse --
    # and it refuses an unreadable table for the same reason this did.
    found = None
    for point, kind in workspaces.mount_table(
            what=f"the filesystem {name_value(place)} is stored on"):
        if not (real == point or real.startswith(point.rstrip("/") + "/")):
            continue
        if found is None or len(point) > len(found[0]):
            found = (point, kind)
    if found is None:
        _refuse(f"no mount in {name_value(MOUNTINFO)} contains "
                f"{name_value(real)}; a path this build cannot place on a "
                f"filesystem is not one it can say is disk-backed")
    return found[1]


def check_disk_backed(place, *, what="the assignment's writable workspace"):
    """Refuse a path that is on a memory filesystem, and say which.

    THE FIVE USES ARE WHY. A checkout, a build cache, test artifacts, the
    declared output and the logs all either outlive the turn that made them or
    have no bound of their own; a memory filesystem gives them a ceiling
    nobody declared and takes them away when the container ends. The runtime
    gets bounded scratch for the things that ARE scratch, and this is the
    boundary that keeps the two apart.
    """
    what = label_of(what)
    boundaries.text(place, "a workspace path")
    kind = filesystem_of(place)
    if kind in MEMORY_FILESYSTEMS:
        _denied(f"{what} {name_value(place)} is on a {kind} filesystem, which "
                f"is memory rather than storage; "
                f"{', '.join(NON_SCRATCH_USES)} do not rely on scratch, and "
                f"the runtime's own bounded scratch is what scratch is for")
    return kind


# -- the nominated source -----------------------------------------------------


class NominatedSource:
    """One validated source directory, as a FROZEN ANSWER with its identity.

    A PATH IS NOT A CAPABILITY and that is the whole reason this is a type.
    The material behind this path is the only thing in the delivery this
    manager did not create, so "which directory" must be a fact it established
    rather than a string it was handed at the moment of use. Minted only by
    `nominate_source`, which is the proof.

    IT CARRIES THE DEVICE AND INODE THE PROOF SAW. That is what makes a
    REPLACEMENT detectable: a path re-pointed at another tree between
    validation and runtime start resolves to the same characters and a
    different inode, and `adopt_source_boundary` compares the second against
    the first. Nothing here is a content identity -- this manager measures no
    content -- it is an identity of the DIRECTORY, which is what a mount
    source is.
    """

    __slots__ = ("place", "device", "inode")

    def __init__(self, place, device, inode, _minted=None):
        if _minted is not _MINT:
            _denied("a nominated source is answered by `nominate_source`, "
                    "which proves the directory; a source a caller can mint "
                    "is a source a caller chose")
        object.__setattr__(self, "place", place)
        object.__setattr__(self, "device", device)
        object.__setattr__(self, "inode", inode)

    def __setattr__(self, name, value):
        _refuse("a nominated source is the answer this manager gave about one "
                "directory and is immutable", code="schema")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    def __repr__(self):
        return f"NominatedSource({self.place!r})"

    def __eq__(self, other):
        return (isinstance(other, NominatedSource)
                and other.place == self.place
                and other.device == self.device
                and other.inode == self.inode)

    def __hash__(self):
        return hash(("NominatedSource", self.place, self.device, self.inode))


def nominate_source(place):
    """Prove one source directory WITHOUT READING IT, and pin its identity.

    EVERY QUESTION HERE IS ABOUT THE DIRECTORY ENTRY AND NONE IS ABOUT ITS
    CONTENTS. It is asked with `lstat` and then with one `O_DIRECTORY |
    O_NOFOLLOW` open, and the descriptor is closed without a single directory
    read: a `fstat` establishes which inode the engine will bind and nothing
    else. There is no walk, no `listdir`, no `scandir`, no open of anything
    beneath it, no digest and no version-control probe -- the whole point of
    the ruling is that a nominated source costs the manager one `stat`
    whatever is inside it, so a repository with a million objects and an empty
    directory are the same act.

    NO-FOLLOW AT THE FINAL COMPONENT AND CANONICAL ABOVE IT, which are two
    different escapes. A symlink at the name is a directory somebody else
    chose; a symlink at an ANCESTOR looks perfectly ordinary and is only
    visible in the resolved path, so the spelling this manager was given must
    already be the one the kernel resolves to. Accepting the resolved path
    instead would silently mount a tree nobody nominated.

    THE COLON IS REFUSED FOR THE ENGINE'S SAKE, exactly as `oci.
    canonical_source` refuses it: it is the engine's own separator, and a path
    carrying one is a mount argument that means something else by the time the
    engine has parsed it.
    """
    boundaries.text(place, "a nominated source directory")
    if not os.path.isabs(place):
        _refuse(f"a nominated source is an absolute path; "
                f"{name_value(place)} is not")
    if ".." in place.split("/"):
        _refuse(f"a nominated source is canonical; {name_value(place)} "
                f"traverses with `..`, which asks this manager to compute a "
                f"path rather than name one")
    if ":" in place:
        _refuse(f"a nominated source carries a colon, which is the engine's "
                f"own separator; {name_value(place)} is a mount argument "
                f"rather than a path")
    if os.path.normpath(place) != place:
        _refuse(f"a nominated source is a canonical path with no redundant "
                f"separator and no trailing one; {name_value(place)} is not")
    try:
        held = os.lstat(place)
    except OSError as failure:
        _refuse(f"the nominated source {name_value(place)} is not a directory "
                f"this manager can see ({type(failure).__name__})")
    if stat.S_ISLNK(held.st_mode):
        _refuse(f"the nominated source {name_value(place)} is a symbolic "
                f"link; a link at that name is a source somebody else chose, "
                f"and this manager mounts the directory it was given rather "
                f"than the one it resolves to")
    if not stat.S_ISDIR(held.st_mode):
        _refuse(f"the nominated source {name_value(place)} is not a "
                f"directory", code="file-type")
    if os.path.realpath(place) != place:
        _refuse(f"the nominated source {name_value(place)} resolves to "
                f"{name_value(os.path.realpath(place))}; an ancestor of a "
                f"nominated source is a link, so the tree the engine would "
                f"bind is not the tree this deployment named")
    # THE IDENTITY, FROM A DESCRIPTOR AND NOT FROM THE PATH AGAIN. `lstat`
    # above answered about a name; this answers about the OBJECT, and the two
    # are the same object only because the open is no-follow and the resolved
    # spelling was already proved equal to the given one.
    try:
        handle = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                         | os.O_CLOEXEC)
    except OSError as failure:
        _refuse(f"the nominated source {name_value(place)} could not be "
                f"opened as a directory ({type(failure).__name__})")
    try:
        # READ NOTHING. This descriptor exists for `fstat` and is closed
        # immediately; `os.listdir(handle)` would work here and is exactly
        # what this boundary promises not to do.
        found = os.fstat(handle)
    finally:
        os.close(handle)
    return NominatedSource(place, found.st_dev, found.st_ino, _MINT)


def _object_of(place, what):
    """The `(device, inode)` of a directory this manager already owns.

    `nominate_source`'s last step, for the OTHER root. That function proves a
    caller's spelling before it opens anything, because a nominated source is
    somebody else's path; the workspace is this manager's own answer from
    `assignment_workspace`, already proved to be this attempt's real directory
    at its own path, so what is left to learn is which OBJECT it is.

    NO-FOLLOW, AND NEVER READ. The same discipline and the same reason: a
    descriptor fixes the identity, and one that is never listed is not an
    enumeration.
    """
    try:
        handle = os.open(place, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as failure:
        _refuse(f"{what} {name_value(place)} could not be opened as a "
                f"directory of its own ({type(failure).__name__})")
    try:
        found = os.fstat(handle)
    finally:
        os.close(handle)
    return (found.st_dev, found.st_ino)


# -- the declared workspace capacity ------------------------------------------


class WorkspaceCapacity:
    """What one assignment DECLARES its writable workspace needs.

    Explicit and without a default, on the rule the workspace group and store
    are already under: a value inherited from whatever the host happened to
    have is not a deployment's decision, and one nobody stated is one no
    refusal can name.

    IT IS NOT A CEILING AND THE NAME NO LONGER SAYS IT IS. W71917's run7
    review found this type called a quota while the mechanism behind it was an
    admission-time check: `workspace_capacity` holds the declaration to this
    build's floor and ceiling, `_capacity` proves the filesystem currently has
    that many bytes free, and OCI then supplies an ordinary writable bind that
    bounds nothing. The ruling is to say what the mechanism does. It carries
    ONE number for the same reason -- the entry count this type used to hold
    reached no mount, no runtime and no sweep, so it was a limit's name over
    no mechanism.
    """

    __slots__ = ("max_bytes",)

    def __init__(self, max_bytes, _minted=None):
        if _minted is not _MINT:
            _denied("a declared workspace capacity is answered by "
                    "`workspace_capacity`, which holds it to this build's own "
                    "floor and ceiling")
        object.__setattr__(self, "max_bytes", max_bytes)

    def __setattr__(self, name, value):
        _refuse("a declared workspace capacity is immutable", code="schema")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    def __repr__(self):
        return f"WorkspaceCapacity(max_bytes={self.max_bytes})"

    def __eq__(self, other):
        return (isinstance(other, WorkspaceCapacity)
                and other.max_bytes == self.max_bytes)

    def __hash__(self):
        return hash(("WorkspaceCapacity", self.max_bytes))


def workspace_capacity(max_bytes):
    """The declared workspace capacity, held to this build's floor and bound.

    THE FLOOR IS THE SCRATCH BOUND AND THE REASON IS IN `MIN_WORKSPACE_BYTES`:
    a workspace that would have fitted in the runtime's private scratch proves
    nothing about the five uses that must not rely on scratch.

    THE CEILING IS AN ADMISSION BOUND ON WHAT A DEPLOYMENT MAY ASK FOR, not a
    bound on what a worker may write. Both refusals below happen before any
    runtime exists, which is the whole of what this value decides.
    """
    if type(max_bytes) is not int or type(max_bytes) is bool or max_bytes <= 0:
        _refuse(f"a declared workspace capacity's max_bytes is one positive "
                f"whole number; this is {name_value(max_bytes)}", code="schema")
    if max_bytes <= MIN_WORKSPACE_BYTES:
        _denied(f"a declared workspace capacity of {max_bytes} bytes is no "
                f"larger than the {MIN_WORKSPACE_BYTES} bytes of bounded "
                f"scratch the runtime already has; "
                f"{', '.join(NON_SCRATCH_USES)} must not rely on scratch, and "
                f"a workspace that would have fitted in it does not establish "
                f"that they do not")
    if max_bytes > MAX_WORKSPACE_BYTES:
        _denied(f"a declared workspace capacity of {max_bytes} bytes is above "
                f"this build's own {MAX_WORKSPACE_BYTES}-byte bound on one "
                f"delivery")
    return WorkspaceCapacity(max_bytes, _MINT)


# -- the composed boundary ----------------------------------------------------


class SourceBoundary:
    """The two roots one runtime receives, PROVED TOGETHER.

    Together rather than separately, because the properties that matter are
    relations: the source must not be inside the workspace, the mountpoint
    must be inside the input root, and the workspace must be real storage
    currently holding what was declared over it. A caller holding two
    validated paths holds none of that.
    """

    __slots__ = ("source", "workspace", "mountpoint", "capacity", "device",
                 "inode", "workspace_device", "workspace_inode", "_guard")

    def __init__(self, source, workspace, mountpoint, capacity, device, inode,
                 workspace_device, workspace_inode, guard=None, _minted=None):
        if _minted is not _MINT:
            _denied("a source boundary is answered by "
                    "a manager composition or adoption boundary; a "
                    "boundary a caller can mint is a topology a caller chose")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "workspace", workspace)
        object.__setattr__(self, "mountpoint", mountpoint)
        object.__setattr__(self, "capacity", capacity)
        object.__setattr__(self, "device", device)
        object.__setattr__(self, "inode", inode)
        # W71917 THIRD REVIEW [P1]: BOTH ROOTS ARE OBJECTS, NOT ONE OBJECT AND
        # ONE NAME. The source carried a proved identity and the workspace
        # carried only its pathname, so a real directory put at that pathname
        # between composition and adoption was accepted -- and that half is
        # the WRITABLE one, where the worker's answer is collected from.
        object.__setattr__(self, "workspace_device", workspace_device)
        object.__setattr__(self, "workspace_inode", workspace_inode)
        object.__setattr__(self, "_guard", guard)

    def __setattr__(self, name, value):
        _refuse("a composed source boundary is immutable", code="schema")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    def __repr__(self):
        return (f"SourceBoundary(source={self.source.place!r}, "
                f"workspace={self.workspace!r})")


def source_mountpoint(inputs):
    """The empty directory the read-only source bind lands on.

    ESTABLISHED BY THIS MANAGER, INSIDE THE INPUT ROOT, AND EMPTY. A bind
    needs somewhere to land; the ordinary bootstrap filled that directory with
    a copy of the source, and this creates it and leaves it alone. The
    manifest's `contentManifest` for this destination therefore describes an
    empty tree, which is the honest statement: an empty tree IS what this
    manager staged.

    `workspaces._own_directory`'s question, asked through the public component
    rather than reimplemented: created here, or already this attempt's own
    real directory at its own path. It is deliberately NOT proved empty on
    adoption -- once the engine has bound the source over it, what a host-side
    reader sees at that path depends on the mount namespace it is looking
    from, and a proof whose answer depends on who is asking is not a proof.
    """
    boundaries.text(inputs, "an assignment inputs root")
    root = os.path.realpath(inputs)
    place = os.path.join(root, SOURCE_NAME)
    if os.path.islink(place):
        _refuse(f"the source mountpoint {name_value(place)} is a symbolic "
                f"link; the engine would bind over a directory somebody else "
                f"chose")
    try:
        os.mkdir(place)
        return place
    except FileExistsError:
        pass
    except OSError as failure:
        _refuse(f"the source mountpoint could not be created at "
                f"{name_value(place)}: {type(failure).__name__}")
    if not os.path.isdir(place) or os.path.realpath(place) != place:
        _refuse(f"{name_value(place)} already exists and is not this "
                f"attempt's own source mountpoint at its own path")
    return place


def compose_source_boundary(source, roots, capacity):
    """One nominated source and one manager-owned workspace, proved together.

    THE ROOTS MUST BE THIS MANAGER'S OWN ANSWER. `AllocatedRoots` is minted
    only by `workspaces.assignment_workspace` and
    `workspaces.adopted_assignment_workspace`, both of which prove each root
    is this attempt's own real directory at its own path under the configured
    store. A plain mapping here would let a caller name any two directories
    and receive a boundary describing them -- which is precisely the
    "manager-created, manager-custodied" half of the ruling, and it cannot
    rest on shape.

    THE SOURCE MAY NOT BE THE MANAGER'S OWN MATERIAL, in either direction. A
    nominated source inside the workspace would be a tree the worker can write
    while it is bound read-only underneath it -- two names for one directory
    with two writabilities -- and one containing the workspace would put the
    assignment's writable root inside the evidence the assignment was given.
    Both are the aliasing `oci._mounts` refuses between mount sources, asked
    one layer earlier so it is a preparation refusal rather than a start one.
    """
    if type(capacity) is not WorkspaceCapacity:
        _denied(f"a source boundary is composed under a declared workspace "
                f"capacity; this is {name_value(capacity)}")
    if type(roots) is workspaces.AllocatedRoots and roots._grant_required:
        _denied("lifecycle-granted roots cannot be recomposed without their "
                "revocable live grant")
    return _compose_boundary(source, roots, capacity)


def compose_runtime_storage_boundary(source, roots):
    """Compose the same mount custody over deployment-supplied storage.

    Persistent review lines deliberately have no predictive free-space gate.
    Their runtime environment supplies storage just as it supplies CPU and
    memory; concrete allocation, mount and write failures belong to the one
    affected attempt. Object, topology and disk-backed-storage proofs remain
    unchanged, while no point-in-time availability reading is performed.
    """
    guard = roots._grant if type(roots) is workspaces.AllocatedRoots else None
    if guard is None or not roots._grant_required:
        _denied("a runtime storage boundary requires roots carrying the "
                "lifecycle owner's live grant")
    return _compose_boundary(source, roots, None, guard)


def _compose_boundary(source, roots, capacity, guard=None):
    if type(source) is not NominatedSource:
        _denied(f"a source boundary is composed over a nominated source this "
                f"manager proved; this is {name_value(source)}")
    if type(roots) is not workspaces.AllocatedRoots:
        _denied(f"a source boundary is composed over the roots this manager "
                f"allocated for one assignment, which carry their own "
                f"provenance; this is {name_value(roots)}")
    workspace = os.path.realpath(roots["workspace"])
    inputs = os.path.realpath(roots["inputs"])
    for name, held in (("workspace", workspace), ("inputs", inputs)):
        if source.place == held or _within(source.place, held) \
                or _within(held, source.place):
            _denied(f"the nominated source {name_value(source.place)} and "
                    f"this assignment's {name} root {name_value(held)} "
                    f"contain one another; a source that is also the "
                    f"manager's own material has two names and two "
                    f"writabilities, and neither this manager nor the engine "
                    f"says which one a path inside the container reaches")
    check_disk_backed(workspace)
    if capacity is not None:
        _capacity(workspace, capacity)
    held = _object_of(workspace, "this assignment's writable workspace")
    return SourceBoundary(source, workspace, source_mountpoint(inputs),
                          capacity, source.device, source.inode,
                          held[0], held[1], guard, _MINT)


def adopt_source_boundary(boundary, roots, *, pinned=None):
    """RE-PROVE a composed boundary against what is on disk right now.

    THIS IS THE PRE-START GATE AND THE RESTART GATE, and it is one function
    because they are one question: is the topology this manager composed still
    the topology it is about to start a runtime over? A source path re-pointed
    at another tree, a workspace replaced with a link, a mountpoint moved
    aside -- each of them is a container reading or writing something nobody
    authorized, and each is cheap to detect and impossible to undo afterwards.

    THE SOURCE IS COMPARED BY INODE, which is what makes REPLACEMENT rather
    than merely absence detectable: a directory unlinked and recreated at the
    same path passes every question about its spelling and is a different
    tree. `nominate_source` runs again -- so a path that has since become a
    link, or acquired a linked ancestor, is refused by the same rules that
    admitted it -- and then the identity it answers is held against the one
    the composition pinned.

    BOTH ROOTS, AND THE SECOND ONE IS W71917's THIRD REVIEW [P1]. The source
    was compared as an OBJECT and the workspace only as a PATHNAME, so a real
    directory created at that pathname after composition passed every question
    asked here -- it resolves to the same spelling, it is a directory of its
    own, and it is on real storage. The acceptance clause says a replaced
    source OR WORKSPACE refuses before a runtime starts, and the writable half
    is the one an assignment's answer is collected out of.

    `pinned` IS WHAT MAKES A RESTART MEAN ANYTHING. W71917 run7 review [P1]:
    the boundary handed in here is recomposed from CONFIGURATION after a
    process restart, so comparing the re-nominated source against it compared
    a fresh reading with itself -- a directory replaced while the manager was
    down was re-nominated and accepted. A caller that holds a durable record of
    what an earlier incarnation proved passes it here as the two
    `(device, inode)` pairs, source first, and the comparison is then against
    evidence rather than against a recomputation of the same guess.

    IT IS NOT OPTIONAL BECAUSE IT IS ABSENT-ABLE. `None` means the caller has
    nothing pinned YET -- the first composition, before the identity has been
    recorded -- and the in-memory comparison below still runs. A caller that
    has a pinned identity and does not pass it gets a weaker gate, which is why
    the deployment reads it unconditionally.

    WHAT THIS DOES NOT CLAIM, said plainly rather than left to be assumed. It
    proves nothing about the source's CONTENTS, before or after, because this
    manager measures no contents; a worker that needs to know which revision
    it received verifies that itself, against the base its own profile
    declares. The pinned value is an OBJECT identity -- which object a path
    named -- and the finding pins that distinction: recording a CONTENT
    identity would still be this manager holding something it is ruled not to
    take, and nothing here reads inside either tree.
    """
    if type(boundary) is not SourceBoundary:
        _denied(f"an adopted boundary is one this manager composed; this is "
                f"{name_value(boundary)}")
    _live_guard(boundary)
    if type(roots) is not workspaces.AllocatedRoots:
        _denied(f"a source boundary is adopted against the roots this manager "
                f"allocated for one assignment; this is {name_value(roots)}")
    source = nominate_source(boundary.source.place)
    if (source.device, source.inode) != (boundary.device, boundary.inode):
        _refuse(f"the nominated source {name_value(source.place)} is not the "
                f"directory this manager proved; the path now names another "
                f"tree, and a runtime started over it would read material "
                f"nobody nominated")
    if pinned is not None:
        # THE COMPARISON THAT SURVIVES A RESTART. The check above compares a
        # fresh reading with a boundary this same process composed, which after
        # a restart is another fresh reading; this one compares it with what an
        # earlier incarnation durably recorded.
        pinned_source, _pinned_workspace = _pinned_pairs(pinned)
        if pinned_source != (source.device, source.inode):
            _refuse(f"the nominated source {name_value(source.place)} is "
                    f"device {source.device} inode {source.inode} and an "
                    f"earlier incarnation of this manager proved this "
                    f"attempt's source as device {pinned_source[0]} inode "
                    f"{pinned_source[1]}; the directory was replaced while no "
                    f"manager was watching, and a runtime started over it "
                    f"would read material nobody nominated")
    workspace = os.path.realpath(roots["workspace"])
    if workspace != boundary.workspace:
        _refuse(f"this attempt's writable root is now {name_value(workspace)} "
                f"and the composed boundary names {name_value(boundary.workspace)}; "
                f"a workspace that moved between composition and start is not "
                f"the one this manager holds custody of")
    if os.path.islink(roots["workspace"]) or not os.path.isdir(workspace):
        _refuse(f"this attempt's writable root {name_value(workspace)} is no "
                f"longer a directory of its own")
    held = _object_of(workspace, "this attempt's writable workspace")
    if held != (boundary.workspace_device, boundary.workspace_inode):
        _refuse(f"this attempt's writable workspace {name_value(workspace)} "
                f"is device {held[0]} inode {held[1]} and this manager proved "
                f"device {boundary.workspace_device} inode "
                f"{boundary.workspace_inode}; the path now names another "
                f"directory, and a runtime started over it would write its "
                f"answer into material this manager has no custody of")
    if pinned is not None:
        _pinned_source, pinned_workspace = _pinned_pairs(pinned)
        if pinned_workspace != held:
            _refuse(f"this attempt's writable workspace "
                    f"{name_value(workspace)} is device {held[0]} inode "
                    f"{held[1]} and an earlier incarnation of this manager "
                    f"proved device {pinned_workspace[0]} inode "
                    f"{pinned_workspace[1]}; the directory was replaced while "
                    f"no manager was watching, and this manager's custody of "
                    f"it is what the whole delivery rests on")
    check_disk_backed(workspace)
    if boundary.capacity is not None:
        _capacity(workspace, boundary.capacity)
    inputs = os.path.realpath(roots["inputs"])
    place = os.path.join(inputs, SOURCE_NAME)
    if place != boundary.mountpoint:
        _refuse(f"the source mountpoint is now {name_value(place)} and the "
                f"composed boundary names {name_value(boundary.mountpoint)}")
    if os.path.islink(place) or not os.path.isdir(place):
        _refuse(f"the source mountpoint {name_value(place)} is not a "
                f"directory of its own; the engine would bind the nominated "
                f"source over something this manager did not establish")
    _live_guard(boundary)
    return SourceBoundary(source, workspace, place, boundary.capacity,
                          source.device, source.inode, held[0], held[1],
                          boundary._guard, _MINT)


def boundary_mounts(boundary):
    """The two binds one execution runtime receives, as (source, target,
    writable) triples.

    READ-ONLY IS NOT A PARAMETER on the source half. The nominated tree is
    somebody else's material and the whole delivery rests on the worker not
    being able to change it: a writable bind would let a turn rewrite the Work
    it was given and then answer about the rewrite. The workspace half is
    writable for the mirror-image reason -- it is the only place a worker may
    write, and one that could not be written is a runtime that cannot answer.

    THE OBJECT IS RE-PROVED HERE, AT THE LAST MOMENT THIS MANAGER OWNS.
    W71917's second review [P1]: adoption proves `(device, inode)` and then the
    argv is composed from a NAME, which the adapter resolves again and the
    engine resolves once more -- so a directory replaced after adoption is
    bound with nothing comparing it against the identity that was proved. This
    is the only place left where a comparison can happen at all, because after
    it the manager holds nothing but a string, so the proof happens here rather
    than at the earlier gate that could not reach this far.

    WHAT THIS DOES NOT CLAIM, and it is stated because it was once stated
    absolutely. The interval between this proof and the engine's own resolution
    of the same pathname is NOT closed, for either bind source, and cannot be
    with a path-based engine API: `docker` and `podman` take a source pathname
    and resolve it themselves. Closing it needs the engine to bind an object
    this manager hands it, which is a different delivery contract.

    RULED 2026-09-05: that residual interval is ACCEPTED for both roots on a
    trusted host, and this manager proves both objects at every boundary it
    owns instead. A descriptor-derived mount source, a daemon-namespace
    coupling or a restart-model change is explicitly out of scope here, so a
    later reader finding this comment does not have to re-derive why the
    obvious closure was not taken. `FINDING.md` carries the decision and the
    costs it weighed.
    """
    if type(boundary) is not SourceBoundary:
        _denied(f"the runtime binds are derived from a boundary this manager "
                f"composed; this is {name_value(boundary)}")
    _live_guard(boundary)
    proved = nominate_source(boundary.source.place)
    if (proved.device, proved.inode) != (boundary.device, boundary.inode):
        _refuse(f"the nominated source {name_value(boundary.source.place)} is "
                f"device {proved.device} inode {proved.inode} and this "
                f"manager proved device {boundary.device} inode "
                f"{boundary.inode}; the path was re-pointed after the boundary "
                f"was adopted, and the runtime binds are composed from the "
                f"object this manager proved rather than from whatever the "
                f"name reaches now")
    held = _object_of(boundary.workspace, "this attempt's writable workspace")
    if held != (boundary.workspace_device, boundary.workspace_inode):
        _refuse(f"this attempt's writable workspace "
                f"{name_value(boundary.workspace)} is device {held[0]} inode "
                f"{held[1]} and this manager proved device "
                f"{boundary.workspace_device} inode "
                f"{boundary.workspace_inode}; the path was re-pointed after "
                f"the boundary was adopted, and a worker would answer into a "
                f"directory this manager never took custody of")
    _live_guard(boundary)
    return ((boundary.source.place, SOURCE_TARGET, False),
            (boundary.workspace, WORKSPACE_TARGET, True))


def _live_guard(boundary):
    if boundary._guard is not None and boundary._guard() is not True:
        _denied("the runtime storage boundary's live grant was revoked")


def _pinned_pairs(pinned):
    """The durable evidence, as `(source, workspace)` object identities.

    ONE SHAPE READ IN ONE PLACE, because two readers of a nested tuple is how
    the source pair and the workspace pair end up compared against each other.
    A caller that holds a record of what an earlier incarnation proved passes
    both, source first, and half of one is refused rather than silently
    treated as absent -- an identity that compares against nothing is the
    defect this evidence exists to catch.
    """
    try:
        source, workspace = pinned
        source = (int(source[0]), int(source[1]))
        workspace = (int(workspace[0]), int(workspace[1]))
    except (TypeError, ValueError, IndexError, KeyError):
        _denied(f"a pinned boundary identity is the source and workspace "
                f"`(device, inode)` pairs an earlier incarnation proved; this "
                f"is {name_value(pinned)}")
    return source, workspace


def _capacity(place, capacity):
    """Whether the workspace's filesystem currently holds the declaration.

    A DECLARATION NOTHING CAN MEET IS NOT A DECLARATION. The capacity says what
    the assignment needs; this asks the filesystem whether that is even
    possible, before a runtime starts, so a deployment learns about it here
    rather than from a turn that failed halfway through writing an output.

    IT IS A PROOF ABOUT AN INSTANT AND NOT A RESERVATION, which is why W71917
    rules that neither the type nor this refusal may call it a limit. It reads
    what is free now; it takes none of it, and two assignments admitted
    against the same filesystem each prove the whole declaration separately.
    Nothing re-asks the question once a runtime is running, so a worker can
    fill the backing filesystem after admission -- an accepted MVP exposure
    with its own parked hardening Work, not something this proof prevents.

    `f_bavail` RATHER THAN `f_bfree`, because the unprivileged worker is who
    has to write: the reserved blocks `f_bfree` counts are the superuser's and
    the container's fixed uid will never see them.
    """
    try:
        held = os.statvfs(place)
    except OSError as failure:
        _refuse(f"the assignment's writable workspace {name_value(place)} "
                f"could not be measured ({type(failure).__name__})")
    available = held.f_bavail * held.f_frsize
    if available < capacity.max_bytes:
        _refuse(f"the assignment's writable workspace {name_value(place)} has "
                f"{available} bytes available and its declared capacity is "
                f"{capacity.max_bytes}; a capacity the storage cannot "
                f"currently meet is a declaration this deployment could not "
                f"have honoured", code="limit")
    return available


def _within(child, parent):
    """Strictly inside, and never merely sharing a prefix.

    `workspaces._within`'s rule, and it is compared by segments for the same
    reason: `/srv/work-2` starts with `/srv/work` and is not in it.
    """
    if child == parent:
        return False
    return child.startswith(parent.rstrip("/") + "/")


# -- what the manifest declares about all of this -----------------------------


def source_consumption(profile):
    """The `consumption` extension a nominated-mount source descriptor carries.

    THREE WORDS, TWO OF THEM THIS MANAGER'S. `delivery` says the material
    arrives as a read-only bind of a directory nobody measured, so a reader of
    the manifest can tell an empty `contentManifest` from a claim that the
    source was empty. `workspace` says the writable root is real storage. Both
    are constants of this component.

    AND `profile` IS THE WORKER'S, PASSED THROUGH. This manager bounds it as
    text and stops: a version-control profile is a fact about the party that
    consumes the mount, and the ruling that made this manager Git-agnostic is
    the same ruling that says the party mounting a directory does not decide
    what is in it.
    """
    return {CONSUMPTION_KEY: {"delivery": DELIVERY, "workspace": BACKING,
                              "profile": _profile(profile)}}


def declared_profile(source):
    """Read a source descriptor's boundary declaration; answer its profile.

    REFUSES A DESCRIPTOR THAT DOES NOT DECLARE THIS BOUNDARY, rather than
    treating absence as the ordinary case. The delivery a manifest describes
    is the delivery a worker is entitled to expect: a descriptor with no
    declaration is a STAGED source, whose `contentManifest` this manager
    measured, and mounting over one would deliver material the manifest does
    not describe.
    """
    if type(source) is not dict:
        _refuse(f"a source descriptor is one object; this is "
                f"{name_value(source)}", code="schema")
    consumption = source.get("consumption")
    if type(consumption) is not dict or CONSUMPTION_KEY not in consumption:
        _refuse(f"this source descriptor does not declare "
                f"{name_value(CONSUMPTION_KEY)}; a descriptor with no "
                f"boundary declaration is a staged source whose content this "
                f"manager measured, and a nominated mount would deliver "
                f"material its manifest does not describe", code="schema")
    declared = boundaries.document(consumption[CONSUMPTION_KEY],
                                   "a source boundary declaration",
                                   required=CONSUMPTION_MEMBERS)
    if declared["delivery"] != DELIVERY:
        _denied(f"a source boundary declaration says it is delivered "
                f"{name_value(declared['delivery'])}; this manager performs "
                f"exactly {name_value(DELIVERY)}")
    if declared["workspace"] != BACKING:
        _denied(f"a source boundary declaration says its workspace is "
                f"{name_value(declared['workspace'])}; this manager composes "
                f"exactly {name_value(BACKING)}, because "
                f"{', '.join(NON_SCRATCH_USES)} do not rely on scratch")
    return _profile(declared["profile"])


def _profile(profile):
    """The worker's profile word, BOUNDED AND NOT INTERPRETED.

    Every rule here is about the text being safely carryable -- non-empty,
    encodable, within a stated width. There is deliberately no membership
    test: the moment this compared the word against a list, this manager would
    be deciding which consumers exist, and a Git-aware profile would be a word
    it recognises. It recognises none of them.
    """
    held = boundaries.text(profile, "a source consumption profile")
    if len(held) > MAX_PROFILE:
        _refuse(f"a source consumption profile is at most {MAX_PROFILE} "
                f"characters; this is {len(held)}", code="limit")
    return held


# W325695: THE TRUSTED RUNTIME-LAYOUT SELECTION, composed here because this
# module already owns the topology above and a second owner would be a second
# spelling of it.
#
# A NEW SCHEMA AND A NEW NAME. `preparation-325908/TASK.md` forbids appending
# members to the frozen task /2, result or worker-launch documents, so the new
# semantics arrive as their own document rather than as extra members on one
# that other readers already parse.
LAYOUT_SCHEMA = "baton.v12.verifier-layout/1"
LAYOUT_TARGET = "/run/baton/verifier-layout.json"
# What the IMAGE declares, as its own file in the read-only rootfs beside the
# scaffolding it describes. This is the trusted expectation the delivered
# document is compared against -- the review's point that "source agreement is
# not established by carrying claims" is exactly this: the document alone is
# the manager's say-so, the marker alone is the image's, and only agreement
# between two independently-produced statements proves the pair was selected
# together.
MARKER_TARGET = "/opt/baton/verifier-layout-marker.json"
MARKER_SCHEMA = "baton.v12.verifier-layout-marker/1"
LAYOUT_MEMBERS = ("schema", "layout_digest", "roots", "filesystem", "options",
                  "mode", "uid", "gid", "image_digest", "profile_digest",
                  "policy_digest", "adapter_digest")
# The document's name under the delivery root, and the ceiling the worker
# reads to. `claude_agent` reads at most this many bytes, so a document wider
# than this is one it would never see whole -- refused here rather than
# delivered for the worker to reject.
LAYOUT_NAME = "verifier-layout.json"
MAX_LAYOUT_BYTES = 64 * 1024
MARKER_MEMBERS = ("schema", "layout_digest", "roots", "filesystem", "options",
                  "mode")


def layout_topology():
    """The selected topology, in the one canonical form both sides digest.

    SORTED AND FULLY SPELLED, because this is the preimage of an identity: two
    composers that agree on the topology and disagree on how to write it down
    would produce two digests for one selection and refuse each other.
    """
    return {"schema": LAYOUT_SCHEMA,
            "roots": {name: target for name, target, _size in VERIFIER_ROOTS},
            "sizes": {name: size for name, _target, size in VERIFIER_ROOTS},
            "filesystem": VERIFIER_FILESYSTEM,
            "options": sorted(VERIFIER_OPTIONS),
            "mode": VERIFIER_MODE}


def layout_digest():
    """The identity of the selected topology, and of nothing else.

    DELIBERATELY NOT OVER THE IDENTITIES. The uid/gid and the image, adapter
    and policy digests are per-deployment selections; folding them in would
    mean every deployment had a different topology identity and the image
    could never declare one. What this digest answers is the question the
    image CAN answer: "are these the roots, the filesystem, the options and
    the mode I was built with".
    """
    return hashlib.sha256(
        json.dumps(layout_topology(), sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def compose_verifier_layout(*, marker, identity, image_digest, profile_digest,
                            policy_digest, adapter_digest):
    """The document ONE runtime receives, or a refusal naming the mismatch.

    THE MANAGER-SIDE INCOMPATIBILITY REFUSAL, which the review asked for by
    name: "An old worker cannot be made to reject a document it does not read
    merely by adding a schema check to the new worker; prove manager-side
    incompatibility refusal too." An old image carries no marker, so `marker`
    is `None`, and this refuses to compose a selection for it -- BEFORE any
    runtime starts, rather than by hoping a worker that never reads the
    document will somehow decline it. The other direction is the worker's, and
    it has to be: only the worker can see that its image's marker arrived with
    no document beside it.

    `marker` is an OPERAND and is not discovered here. This module composes;
    what an image declares is read from that image's own record by the caller
    that owns image identity. Inferring it would make the refusal a guess.

    THE EXECUTION IDENTITY IS A CAPABILITY AND NOT A PAIR OF INTEGERS, and
    that is the review's correction rather than a style choice: "Bind selected
    topology and effective UID/GID through the actual owner composition, not
    self-assertion in an arbitrary document." The owner composition is
    `workspaces.identity_for`, which derives the uid from `os.geteuid()`
    behind the deployment's own minted workspace group -- the SAME object
    `oci.run_vector` turns into this runtime's `--user` flag. So the document
    cannot name an identity the container will not run as, and a caller cannot
    choose one: two integers would have been exactly the self-assertion that
    was refused, and a `WorkspaceIdentity` is a thing only the manager's own
    provisioning can mint.

    THE FOUR DIGESTS ARE THE WHOLE RESOLVED IDENTITY, `oci.RESOLVED_IDENTITY`
    member for member, for the same reason: `OciAdapter` holds one resolved
    identity at construction and refuses a layout document that disagrees with
    it, so the pair the worker proves is the pair the adapter started. A
    three-member subset would have left `profile_digest` -- the runtime
    profile that selects the posture the roots live under -- unbound.
    """
    if marker is None:
        _denied(f"this image declares no verifier-layout marker, so the "
                f"selected private verifier topology cannot be composed for "
                f"it; an image built before {name_value(LAYOUT_SCHEMA)} has "
                f"no {name_value(VERIFIER_PARENT)} scaffolding and no "
                f"per-root mounts, and composing a document it cannot honour "
                f"would start a runtime whose verifier roots do not exist")
    held = boundaries.document(marker, "a verifier-layout marker",
                               required=MARKER_MEMBERS)
    if held["schema"] != MARKER_SCHEMA:
        _denied(f"a verifier-layout marker says it is "
                f"{name_value(held['schema'])}; this manager composes against "
                f"exactly {name_value(MARKER_SCHEMA)}")
    mine = layout_digest()
    if held["layout_digest"] != mine:
        _denied(f"this image declares verifier topology "
                f"{name_value(held['layout_digest'])} and this manager "
                f"composes {name_value(mine)}; the image's fixed root "
                f"scaffolding and this manager's mounts were selected from "
                f"different topologies, and the pair refuses before the "
                f"provider rather than after a verifier cannot find a root")
    # THE TRUSTED EXECUTION IDENTITY, MINTED AND NOT NAMED. TASK.md: "not
    # hardcoded 65532, not ambient login group". `WorkspaceIdentity` is both:
    # it is never 65532, because its uid is this manager's own effective uid,
    # and it is never an ambient group, because its gid is the deployment's
    # minted `WorkspaceGroup`. A caller holding only integers cannot get here.
    if type(identity) is not workspaces.WorkspaceIdentity:
        _denied(f"a verifier layout is composed under this deployment's "
                f"minted execution identity, which is the same capability "
                f"the runtime's own `--user` flag is composed from; this is "
                f"{name_value(identity)}")
    for name, value in (("image_digest", image_digest),
                        ("profile_digest", profile_digest),
                        ("policy_digest", policy_digest),
                        ("adapter_digest", adapter_digest)):
        boundaries.text(value, f"a verifier layout's {name}")
    topology = layout_topology()
    return {"schema": LAYOUT_SCHEMA,
            "layout_digest": mine,
            "roots": topology["roots"],
            "filesystem": topology["filesystem"],
            "options": topology["options"],
            "mode": topology["mode"],
            "uid": identity.uid, "gid": identity.gid,
            "image_digest": image_digest,
            "profile_digest": profile_digest,
            "policy_digest": policy_digest,
            "adapter_digest": adapter_digest}


def image_layout_marker():
    """The marker an image build writes beside its own root scaffolding.

    Composed from the same `layout_topology` the document is, so an image
    recipe cannot declare a topology this manager does not compose. The recipe
    writes this file; `MARKER_TARGET` is where the worker reads it.
    """
    topology = layout_topology()
    return {"schema": MARKER_SCHEMA,
            "layout_digest": layout_digest(),
            "roots": topology["roots"],
            "filesystem": topology["filesystem"],
            "options": topology["options"],
            "mode": topology["mode"]}


def layout_bytes(document):
    """The canonical bytes of one layout document, bounded.

    ONE SPELLING, because these bytes are compared: `materialize_verifier_layout`
    adopts an existing document only when it is byte-identical to what this
    composition would write, and two spellings of one selection would make a
    deployment refuse its own delivery.
    """
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_LAYOUT_BYTES:
        _denied(f"this verifier-layout document is {len(payload)} bytes and "
                f"the worker reads at most {MAX_LAYOUT_BYTES}; a document the "
                f"worker would refuse is not one this manager writes")
    return payload


class LayoutDelivery:
    """The TYPED capability the adapter receives, and the only one.

    THE SAME RULE `launch.LaunchDelivery` IS UNDER, and it is the review's
    "protect document delivery, type, ownership and immutability": what
    crosses to the adapter is a delivery this manager materialized, not a path
    a caller chose. A path operand would be a caller-selected locator for the
    one document the verifier's roots are proved against -- which is exactly
    what the fixed target exists to take away.

    IT CARRIES THE DOCUMENT, not just the place, because the adapter has a
    proof to make about it: `OciAdapter` refuses a delivery whose resolved
    identity is not the one it was constructed under, and `oci.run_vector`
    refuses one whose uid/gid is not the identity it is composing into
    `--user`. Neither check is possible against bytes on disk alone.
    """

    def __init__(self, *, root, place, document):
        self.root = root
        self.place = place
        self.document = document

    def mount(self):
        """The ONE read-only bind this delivery authorizes.

        A pair rather than a mount document: `readonly` is not a parameter,
        and a delivery that could ask to be writable would be a layout
        document the worker could rewrite between proving its roots against it
        and being asked about them.
        """
        return (self.place, LAYOUT_TARGET)


def materialize_verifier_layout(storage, *, document):
    """Put one composed layout selection on disk as this manager's own.

    `storage` is the manager's own layout storage and NOT an assignment root,
    for the reason `launch.materialize` states: a document mounted out of
    `inputs` is one the input digest describes, and one mounted out of
    `workspace` is one the worker may WRITE -- so the worker could rewrite the
    document its own verifier roots are proved against.

    AN EXISTING DOCUMENT IS ADOPTED ONLY IF IT IS THIS ONE, byte for byte.
    `launch.materialize` refuses any existing root outright and is right to:
    its document is per-attempt, so an existing one is a live delivery or an
    orphan. THIS document is a per-deployment selection -- a pure function of
    the topology above, the image's marker and the resolved identity -- so a
    second start of the same deployment composes the same bytes, and refusing
    them would mean a deployment could serve exactly one runtime. Different
    bytes at the name still REFUSE: that is a selection that changed under a
    deployment whose live runtimes were started against the old one.
    """
    home = boundaries.text(storage, "the manager's verifier-layout storage")
    if not os.path.isabs(home):
        _refuse(f"the manager's verifier-layout storage is not an absolute "
                f"path; a root this build cannot name exactly is not a root",
                code="path")
    held = boundaries.document(document, "a verifier-layout document",
                               required=LAYOUT_MEMBERS)
    if held["schema"] != LAYOUT_SCHEMA:
        _denied(f"a verifier-layout delivery carries "
                f"{name_value(held['schema'])}; this manager delivers exactly "
                f"{name_value(LAYOUT_SCHEMA)}")
    payload = layout_bytes(held)
    root = os.path.join(os.path.realpath(home), "verifier-layout")
    place = os.path.join(root, LAYOUT_NAME)
    os.makedirs(root, mode=0o700, exist_ok=True)
    # THE EXISTING DOCUMENT IS COMPARED THROUGH A DESCRIPTOR, never by a
    # second lookup of a name that could be something else by then -- the rule
    # `launch.adopt` states. `O_NOFOLLOW` so a link left at the name refuses
    # rather than being read through, and the type comes from the descriptor
    # this function is holding.
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        handle = None
    except OSError as failure:
        _refuse(f"the verifier-layout document at {place} cannot be opened "
                f"({type(failure).__name__}); a link or special file at the "
                f"name is refused rather than read through", code="path")
    if handle is not None:
        try:
            found = os.fstat(handle)
            if not stat.S_ISREG(found.st_mode):
                _refuse(f"the verifier-layout document at {place} is not an "
                        f"ordinary file", code="path")
            if found.st_size > MAX_LAYOUT_BYTES:
                _refuse(f"the verifier-layout document at {place} is "
                        f"{found.st_size} bytes and this manager writes at "
                        f"most {MAX_LAYOUT_BYTES}", code="limit")
            if os.read(handle, MAX_LAYOUT_BYTES + 1) != payload:
                _denied(f"a different verifier-layout selection is already "
                        f"delivered at {place}; this deployment's selection "
                        f"changed while runtimes may have been started "
                        f"against the one on disk, and replacing those bytes "
                        f"would leave a live worker proving its roots against "
                        f"a selection nothing recorded")
        finally:
            os.close(handle)
        return LayoutDelivery(root=root, place=place, document=held)
    # EXCLUSIVE CREATION, NO-FOLLOW, AND CREATED UNREADABLE, then made
    # readable on the DESCRIPTOR this function wrote -- `launch.materialize`'s
    # rule and its reason: a creation mode is filtered by the umask, so a
    # manager under the ordinary service umask 077 would author a document the
    # container's execution identity cannot read, and `fchmod` after the last
    # byte means the document becomes readable exactly when it becomes whole.
    handle = os.open(place,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    try:
        written = 0
        while written < len(payload):
            step = os.write(handle, payload[written:])
            if type(step) is not int or step <= 0:
                _refuse(f"writing the verifier-layout document made no "
                        f"progress after {written} of {len(payload)} bytes; a "
                        f"partly written document is one the worker refuses "
                        f"and this manager believes it delivered")
            written += step
        os.fchmod(handle, 0o444)
    except BaseException:
        os.close(handle)
        os.unlink(place)
        raise
    os.close(handle)
    return LayoutDelivery(root=root, place=place, document=held)
