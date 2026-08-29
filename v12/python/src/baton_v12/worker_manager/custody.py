"""W36540 — unconditional manager custody over an ended attempt's directories.

THE DEFECT THIS EXISTS TO REMOVE, measured on a real daemon under W33936's
corrected mechanism with the container proved absent: a directory the worker
created WITH CONTENT IN IT cannot be removed by the manager. Its mode comes
from the worker's umask -- measured `drwxr-sr-x`, so the group has no write --
and the manager owns neither the directory nor a way to `chmod` it. `os.chmod`
is EPERM and unlinking inside it is EACCES. Any real worker creates populated
subdirectories, so this leaves trees the manager cannot remove.

That is a CONSEQUENCE of the approved mechanism rather than a defect in it.
The configured group grants write on the workspace ROOT; what the worker
creates inside is the worker's, and W33936 correctly made the failure honest
rather than widening anything to get past it.

APPROVER RULING M36166 fixes both what is required and what may not be used.

THE REQUIRED INVARIANT is UNCONDITIONAL: after fencing and proving the exact
worker container absent, this manager must be able to inspect, read, hash,
archive, normalize and recursively delete EVERY object in that attempt's exact
workspace and result directories, REGARDLESS OF WORKER-SELECTED MODES.

EXPLICITLY NOT THE MECHANISM: a worker umask of `002`. It may improve the
cooperative path and it cannot be custody, because custody may not depend on
the worker having cooperated. A worker that sets its own umask back, or writes
one directory `0700` on purpose, defeats it -- and a custody property that an
uncooperative worker can switch off is not a property.

THE MECHANISM IS A SHORT-LIVED CUSTODY HELPER, and the whole of its design is
in three constraints:

ONE MOUNT, THE EXACT ATTEMPT DIRECTORY. Not the storage root, not the inputs,
not the launch or credential roots, not the repository. Absent rather than
denied: a path that is not mounted cannot be reached by any means, which is a
stronger statement than a permission check and one that survives a bug in the
program it is running.

THE OWNING WORKER IDENTITY. This is the part that makes the custody
unconditional, and it is worth stating plainly: the helper runs as the SAME
uid the worker ran as, so it OWNS every object the worker created. An owner
may always `chmod` its own objects, whatever mode they currently carry -- so
there is no mode a worker can choose that locks the custodian out. The manager
never acquires that ownership itself and never needs to.

TYPED MANAGER-OWNED OPERATIONS ONLY. The vocabulary below is closed and the
program that runs inside is a constant of this module. There is no operand
through which a worker or a caller names a command, a path outside the attempt
directory, or a second mount -- because there is no command operand at all,
only a verb this module recognises.

WHAT THE HELPER IS NOT TRUSTED TO DO. It normalizes; the MANAGER removes. The
containment rules, the "remove only what this component created" rule and the
storage-root check stay exactly where they are, on this side, because those
are the rules that make a deletion safe and they are not the helper's to
re-derive.
"""

import os
import re
import stat

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries

__all__ = ["CUSTODY_OPERATIONS", "CUSTODY_ROOT", "CUSTODY_PROGRAM",
           "CustodyRoot", "attempt_custody_root", "check_custody_operation",
           "custody_vector"]


# THE CLOSED VOCABULARY, exactly M36166's six.
#
# `normalize` and `discard` are the two this build composes into an ending;
# the other four are the custody the ruling requires the manager to BE ABLE to
# perform over the same directory, and they are named here rather than added
# later because a vocabulary that grows one verb at a time is not closed.
CUSTODY_OPERATIONS = ("inspect", "read", "hash", "archive", "normalize",
                      "discard")

# WHERE THE ONE MOUNT LANDS. Fixed rather than composed, because a container
# path a caller could choose is an operand that decides what the program walks.
CUSTODY_ROOT = "/custody"

# A NAME THIS MANAGER CAN RECOGNISE AFTERWARDS, and the reason it is a prefix
# rather than a label: a custody helper that outlives its act has to be
# findable by a restarted manager that never saw it start.
CUSTODY_NAME = "baton-custody"

_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,60}")


def check_custody_operation(operation):
    """One verb from the closed vocabulary, or a refusal.

    THE RECEIVING END OF THE RULING'S "no worker-supplied command". A verb is
    not a command: it selects among programs this module owns, and a value
    that is not one of the six selects nothing at all.
    """
    boundaries.text(operation, "a custody operation")
    if operation not in CUSTODY_OPERATIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(operation)} is not a custody operation; the six "
            f"this manager owns are {', '.join(CUSTODY_OPERATIONS)}, and a "
            f"custody act is chosen from that vocabulary rather than "
            f"described by its caller")
    return operation


# THE PROGRAM, AND IT IS A CONSTANT OF THIS MODULE.
#
# It takes ONE argument -- the verb -- and validates it against its own copy of
# the vocabulary, so the closed set is enforced at both ends of the crossing
# rather than only on the composing side. It walks nothing but its own mount.
#
# `normalize` is the act that removes the defect: running as the owner of the
# worker's objects, it restores group access on every directory and file under
# the mount, so the MANAGER's own removal walk can then proceed under its own
# containment rules. It does not delete, and it does not touch anything above
# its mount because there is nothing above its mount to touch.
CUSTODY_PROGRAM = r'''
import base64, hashlib, json, os, sys

ROOT = "/custody"
VERBS = ("inspect", "read", "hash", "archive", "normalize", "discard")

# How much of a file is read at once. Constant memory is the whole point: a
# worker file larger than this container's memory bound must not be able to
# end the custody act.
CHUNK = 1 << 20

# How many bytes of one file `read` carries back in its answer. Bounded
# because the answer is one JSON document on a pipe, and stated in the answer
# itself through `complete` so a partial carry is never mistaken for the file.
MAX_CARRIED = 1 << 16

verb = sys.argv[1] if len(sys.argv) > 1 else ""
if verb not in VERBS:
    print(json.dumps({"custody": "refused", "why": "unknown operation"}))
    raise SystemExit(2)

MINE = os.getuid()


def owned(place):
    held = os.lstat(place)
    return held.st_uid == MINE, held


def openable(place):
    """Make one OWNED directory traversable BEFORE anything descends into it.

    Review [P0]: the first cut walked bottom-up, so `os.walk` had to enter a
    directory before the pass that would have made it enterable -- and a
    mode-zero directory inside a mode-zero directory was silently omitted
    from the walk entirely. Only the outer one was ever changed, and the
    subtree below it stayed outside custody while the act reported success.

    Top-down, and each owned directory is opened on the way IN. That is the
    order that makes the property unconditional at any depth.
    """
    mine, held = owned(place)
    if mine and not held.st_mode & 0o100:
        os.chmod(place, (held.st_mode & 0o7777) | 0o700)


def walk():
    """Every entry under the mount, top-down, never following a link out.

    A SYMLINKED DIRECTORY IS EXCLUDED FROM DESCENT AND NOT FROM THE WALK.
    Review [P1]: the first correction dropped links out of `directories`
    before the yield, which stopped traversal -- correctly -- and also made
    the link OBJECT invisible. `inspect` answered an empty list for a root
    holding one directory symlink, and `discard` reported success while
    leaving it there. "Every object" includes the link itself: it stays
    observable and removable, and its target stays untouched.
    """
    for current, directories, files in os.walk(ROOT, topdown=True):
        descend, links = [], []
        for name in directories:
            place = os.path.join(current, name)
            if os.path.islink(place):
                links.append(name)
                continue
            openable(place)
            descend.append(name)
        directories[:] = descend
        # The links ride with the FILES, which is what they are to every act
        # here: one entry to report and one entry to unlink, never a way in.
        yield current, descend, files + links


def relative(place):
    return os.path.relpath(place, ROOT)


def every():
    for current, directories, files in walk():
        for name in files + directories:
            yield os.path.join(current, name)


if verb == "normalize":
    changed, skipped = 0, 0
    for place in every():
        if os.path.islink(place):
            continue
        mine, held = owned(place)
        if not mine:
            skipped += 1
            continue
        grant = 0o070 if os.path.isdir(place) else 0o060
        os.chmod(place, (held.st_mode & 0o7777) | grant)
        changed += 1
    print(json.dumps({"custody": "normalize", "entries": changed,
                      "not_ours": skipped, "running_as": [MINE, os.getgid()]}))
    raise SystemExit(0)

if verb == "inspect":
    entries = []
    for place in every():
        held = os.lstat(place)
        entries.append({"path": relative(place),
                        "mode": oct(held.st_mode & 0o7777),
                        "uid": held.st_uid, "gid": held.st_gid,
                        "kind": ("link" if os.path.islink(place)
                                 else "directory" if os.path.isdir(place)
                                 else "file")})
    print(json.dumps({"custody": "inspect", "entries": sorted(
        entries, key=lambda one: one["path"]),
        "running_as": [MINE, os.getgid()]}))
    raise SystemExit(0)

if verb in ("read", "hash", "archive"):
    # THE THREE READING ACTS SHARE ONE WALK and differ only in what they
    # answer about each file. A file this custodian cannot open after
    # `openable` has run is reported as unreadable rather than skipped: an
    # act that silently omitted an entry would be the same defect the
    # traversal correction removes.
    #
    # STREAMED, NEVER SLURPED. Review [P1]: every branch did
    # `handle.read()` into one bytes object before hashing it, so a worker
    # file larger than this container's 512 MiB terminated the custody act --
    # and an act a worker can end by writing a big file is not unconditional.
    # The digest is now computed over CHUNK reads at constant memory, so file
    # size decides how long the act takes and nothing else.
    #
    # AND THE HEAD IS BASE64 AND EXPLICITLY PARTIAL. It used to be
    # `body[:4096].decode("utf-8", "replace")`, which is lossy TWICE: it
    # stops at 4096 bytes without saying so, and it replaces every byte that
    # is not UTF-8 with U+FFFD -- so what came back was neither the file nor
    # a recoverable prefix of it. `complete` now says whether the carried
    # bytes ARE the file, and the bytes are carried unmangled.
    entries, total = [], 0
    for place in every():
        if os.path.islink(place) or os.path.isdir(place):
            continue
        mine, held = owned(place)
        if mine and not held.st_mode & 0o400:
            os.chmod(place, (held.st_mode & 0o7777) | 0o400)
        one = {"path": relative(place), "bytes": held.st_size}
        digest = hashlib.sha256()
        carried, measured = bytearray(), 0
        try:
            with open(place, "rb") as handle:
                while True:
                    chunk = handle.read(CHUNK)
                    if not chunk:
                        break
                    digest.update(chunk)
                    measured += len(chunk)
                    if verb == "read" and len(carried) < MAX_CARRIED:
                        carried += chunk[:MAX_CARRIED - len(carried)]
        except OSError as failure:
            one["unreadable"] = type(failure).__name__
            entries.append(one)
            continue
        total += measured
        # THE MEASURED SIZE, not the one `lstat` reported. A file that grew
        # or shrank between the two is a file whose recorded byte count would
        # otherwise disagree with its own digest.
        one["bytes"] = measured
        one["sha256"] = "sha256:" + digest.hexdigest()
        if verb == "read":
            one["content_base64"] = base64.b64encode(bytes(carried)).decode(
                "ascii")
            one["complete"] = measured <= MAX_CARRIED
        entries.append(one)
    answer = {"custody": verb, "entries": sorted(
        entries, key=lambda one: one["path"]), "total_bytes": total,
        "running_as": [MINE, os.getgid()]}
    if verb == "archive":
        # THE ARCHIVE IS A MANIFEST AND SAYS SO. What custody needs from this
        # act is a durable description of what was there; the bytes stay
        # where they are, and after `normalize` the manager reads them
        # directly under its own containment rules.
        #
        # WHETHER THAT SATISFIES "archive" IS AN OPEN RULING and is recorded
        # as one in the finding rather than decided here. Returning content
        # through this channel needs somewhere to put it, and M36166 fixes
        # ONE mount which is the custody subject itself -- writing an archive
        # into the tree under custody would change the thing being described.
        answer["content"] = "manifest-only"
        answer["tree_digest"] = "sha256:" + hashlib.sha256(json.dumps(
            [(one["path"], one.get("sha256"), one["bytes"])
             for one in answer["entries"]],
            sort_keys=True).encode("utf-8")).hexdigest()
    print(json.dumps(answer))
    raise SystemExit(0)

if verb == "discard":
    # RECURSIVE DELETE, bottom-up over a tree already made traversable on the
    # way down. Only what this custodian owns is removed; anything else is
    # counted and left, and the caller is told.
    removed, kept = 0, 0
    order = []
    for current, directories, files in walk():
        order.append((current, list(directories), list(files)))
    for current, directories, files in reversed(order):
        for name in files:
            place = os.path.join(current, name)
            mine, _held = owned(place)
            if not mine:
                kept += 1
                continue
            # A LINK IS UNLINKED, never followed: the entry goes and whatever
            # it pointed at is none of this act's business.
            os.unlink(place)
            removed += 1
        for name in directories:
            place = os.path.join(current, name)
            mine, _held = owned(place)
            if not mine:
                kept += 1
                continue
            try:
                os.rmdir(place)
                removed += 1
            except OSError:
                kept += 1
    print(json.dumps({"custody": "discard", "removed": removed, "kept": kept,
                      "running_as": [MINE, os.getgid()]}))
    raise SystemExit(0)
'''


_MINT = object()


class CustodyRoot:
    """ONE directory a custody act may be performed on, as a CAPABILITY.

    Review [P0]: the vector took a raw absolute host path and applied only
    `realpath`. Every caller supplied the whole assignment HOME, whose
    siblings are `credentials`, `credential-state`, `inputs` and the launch
    root -- and my own probe transcript listed those four in the helper's
    `inspect` answer. Skipping what the helper does not own is NOT absence: a
    different typed operation, or a bug in this program, still reads whatever
    the mount exposes, and the pinned boundary is that they are unreachable.

    So a custody root is MINTED from the assignment layout this manager
    established, never named by a caller. There is no constructor a caller can
    reach -- the same rule W33936's `WorkspaceGroup` is under, for the same
    reason: a path a caller can name is a path a caller chose.
    """

    __slots__ = ("place", "which")

    def __init__(self, place, which, _minted=None):
        if _minted is not _MINT:
            raise ContractRefusal(
                "policy", "denied",
                "a custody root is minted from this manager's own assignment "
                "layout and is not constructed; a root a caller can mint is a "
                "root a caller chose")
        object.__setattr__(self, "place", place)
        object.__setattr__(self, "which", which)

    def __setattr__(self, name, value):
        raise ContractRefusal("integrity", "schema",
                              "a custody root is immutable")

    def __repr__(self):
        return f"CustodyRoot({self.which}={self.place!r})"


# THE ONLY TWO DIRECTORIES A CUSTODY ACT MAY TOUCH, and they are the two the
# acceptance names: the attempt's exact workspace and its result directory.
# Never their parent, which is the assignment home and holds the deliveries.
CUSTODY_ROOTS = ("workspace", "result")


def attempt_custody_root(workspace_group, storage, assignment_id,
                         which="workspace"):
    """Mint the capability for ONE of this attempt's own directories, by
    DERIVING it from the allocation rather than reading it off anything.

    SIX REVIEW ROUNDS ENDED HERE, and they were all one defect wearing
    different clothes. The mount source was READ from an object the caller
    held: first a plain mapping, then a mapping with the expected basenames,
    then the nominal type `assignment_workspace` answers with, then that type
    with its `dict` mutators overridden, then that type with `dict` removed
    from its bases, then that type with its members in a private attribute.
    Each round closed one door onto the same room:

        roots["workspace"] = elsewhere
        dict.update(roots, {"workspace": elsewhere})
        roots |= {"workspace": elsewhere}
        roots._members.update({"workspace": elsewhere})

    The last one is the whole lesson. `_members` is private by NAME and its
    value is an ordinary mutable dict, so a holder reads it through ordinary
    attribute access and edits it in place -- and no amount of further
    overriding reaches that, because there is no method call to override. The
    same would be true of the next representation and the one after it: in
    this language a holder of an object can reach what the object holds, so
    an authority carried in caller-held process state and re-read later is an
    authority the caller can change in between.

    SO THE PATH IS NOT AN INPUT AT ALL ANY MORE. There is nothing here to
    forge, retarget or launder, because nothing here is read: this function
    RE-DERIVES `<storage>/<assignment>/workspace` by exactly the rule
    `assignment_workspace` allocates it by, from exactly the operands
    `assignment_workspace` allocates it from -- the deployment's configured
    group capability, the manager's storage root and the attempt identity.
    An `AllocatedRoots` object is no longer accepted, so mutating one cannot
    influence this and neither can constructing one.

    WHAT AUTHORITY THIS THEREFORE CARRIES, said exactly. It carries the
    ALLOCATION's, and not one bit more: any directory this can mount is one
    `assignment_workspace` would have allocated for the same operands, and a
    caller that can name those operands can already call that function. What
    is now impossible -- and was the finding -- is selecting something that is
    NOT an attempt workspace. The composed source is always the `workspace`
    entry of a home directly under the storage root, so the assignment home,
    its `inputs`, `credentials`, `credential-state` and `custody` siblings, the
    repository and every unrelated host path are unreachable rather than
    merely refused. There is no operand from which any of them could be built.

    AND EVERY COMPONENT IS `lstat`ed, never `isdir`ed. The workspace is
    worker-writable, so `result` is a name an ended worker can leave as a
    symlink to any host path the engine can resolve -- and `os.path.isdir`
    follows it while `_real` resolves it, which between them turned a
    worker-controlled alias into a mount. A link is refused wherever it sits.
    """
    from .workspaces import WorkspaceGroup, _real, _within
    # THE GROUP CAPABILITY, FIRST AND AS PROVENANCE. `assignment_workspace`
    # requires it to allocate, so requiring it to derive is what makes this
    # the same act: a caller that cannot obtain the deployment's configured
    # group never allocated the root this would name. It is the deployment's
    # own record rather than a number, on W33936's rule -- a group a caller
    # can name is a group a caller chose.
    if type(workspace_group) is not WorkspaceGroup:
        raise ContractRefusal(
            "policy", "denied",
            f"a custody root is derived with this deployment's CONFIGURED "
            f"workspace group, obtained from this manager's own record; this "
            f"is {name_value(workspace_group)}")
    boundaries.text(which, "a custody root name")
    if which not in CUSTODY_ROOTS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(which)} is not a custody root; the two an attempt "
            f"has are {', '.join(CUSTODY_ROOTS)}, and their parent holds the "
            f"deliveries and is never mounted")
    boundaries.identity(assignment_id, "an assignment identity")
    # AN IDENTITY IS A NAME AND NEVER A PATH. `boundaries.identity` is
    # `boundaries.text` -- it owns durable text and says nothing about path
    # syntax -- so an attempt called `../../etc` would otherwise compose a home
    # outside the storage root before any containment check could see it. This
    # is the same rule `assignment_workspace` gets from comparing against its
    # own `expected_home`, stated directly because this function derives rather
    # than creates.
    if os.sep in assignment_id or (os.altsep and os.altsep in assignment_id) \
            or assignment_id in (os.curdir, os.pardir):
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(assignment_id)} is not an assignment identity; an "
            f"attempt is NAMED and a name that carries a path separator is a "
            f"way to compose a home this manager never allocated")
    root = _real(storage, "the manager's workspace storage")
    if not os.path.isdir(root):
        raise ContractRefusal(
            "integrity", "path",
            "the manager's workspace storage is not a directory")
    # THE SAME LAYOUT `assignment_workspace` ESTABLISHES, composed rather than
    # looked up: one home per attempt directly under the storage root, and
    # `workspace` inside it.
    home = os.path.join(root, assignment_id)
    place = (os.path.join(home, "workspace") if which == "workspace"
             else os.path.join(home, "workspace", "result"))
    if which == "result" and not _no_link(place, missing_ok=True):
        os.makedirs(place, exist_ok=True)
    # EVERY COMPONENT, from the home down: a link anywhere on the way is a
    # different directory than the one this manager created, and an entry this
    # manager does not own is not one it allocated.
    _no_link(home, what="the attempt home")
    _no_link(os.path.join(home, "workspace"), what="the attempt's workspace")
    if which == "result":
        _no_link(place, what="the attempt's result directory")
    resolved = _real(place, f"the attempt's {which} root")
    # AND THE RESOLVED SOURCE IS STILL UNDER THE STORAGE ROOT. Redundant given
    # the link proofs above and kept anyway: containment is the property the
    # mount actually depends on, and a proof that holds it directly does not
    # stop holding it when somebody changes how the components are checked.
    if not _within(resolved, root):
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(resolved)} resolves outside this manager's "
            f"workspace storage; a custody act is performed on an attempt "
            f"directory this manager allocated")
    return CustodyRoot(resolved, which, _MINT)


def _no_link(place, *, what=None, missing_ok=False):
    """One EXACT directory this manager owns, asked with `lstat`.

    `os.path.isdir` follows a symlink and answers about its target, which is
    the question a worker gets to choose the answer to. `lstat` answers about
    the entry.
    """
    try:
        held = os.lstat(place)
    except FileNotFoundError:
        if missing_ok:
            return False
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(place)} does not exist; a custody root is a "
            f"directory this manager created")
    if not stat.S_ISDIR(held.st_mode) or stat.S_ISLNK(held.st_mode):
        raise ContractRefusal(
            "policy", "denied",
            f"{what or name_value(place)} is not a directory this manager "
            f"created: it is {'a symbolic link' if stat.S_ISLNK(held.st_mode)
                              else 'not a directory'}. The workspace is "
            f"worker-writable, so a name inside it is a name an ended worker "
            f"can point wherever the engine can resolve -- and a resolved "
            f"alias is not a capability")
    if held.st_uid != os.getuid():
        raise ContractRefusal(
            "policy", "denied",
            f"{what or name_value(place)} is owned by uid {held.st_uid} and "
            f"this manager is uid {os.getuid()}; a custody root is one this "
            f"manager created")
    return True


def custody_vector(engine, *, image_digest, name, custody, operation,
                   workspace_group):
    """The closed argv that performs ONE custody act, restrictions and all.

    IT IS NOT A RUNTIME AND DOES NOT REUSE `run_vector`. The two compose
    different things: a runtime is given inputs, a launch document and
    credentials and is expected to run somebody's assignment; a custodian is
    given one directory and a verb. Sharing a composer would mean every
    restriction this needs is one an execution vector could later relax.

    `--rm` AND FOREGROUND, which is what "short-lived" means mechanically: the
    engine removes the container when the act ends, so nothing it creates
    outlives the act and a crash between start and ending leaks no capability
    a later manager would have to find and reclaim.
    """
    from .oci import _engine, _IMAGE, _refuse
    engine = _engine(engine)
    boundaries.text(image_digest, "an image digest")
    if not _IMAGE.match(image_digest):
        _refuse(f"{name_value(image_digest)} is not a sha256 image digest; a "
                f"custody act runs the image this manager can name exactly",
                code="digest")
    boundaries.identity(name, "a custody act name")
    if not _NAME.fullmatch(name):
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(name)} is not a runtime name this build composes")
    operation = check_custody_operation(operation)
    # THE ONE MOUNT, and it is the capability's own path. There is no host
    # path operand at all now, so an arbitrary absolute directory -- a
    # repository, a credential root, an unrelated sibling -- cannot be
    # selected: it is not a custody root and nothing can make it one.
    if type(custody) is not CustodyRoot:
        raise ContractRefusal(
            "policy", "denied",
            f"a custody act is performed on a root minted from this manager's "
            f"own assignment layout; this is {name_value(custody)}")
    source = custody.place
    argv = [engine, "run", "--rm", "--name", name]
    for flag, value in _CUSTODY_RESTRICTIONS:
        argv.append(flag)
        if value is not None:
            argv.append(value)
    # THE CONFIGURED WORKSPACE GROUP, FOR THE SAME REASON THE WORKER GETS IT.
    #
    # Measured rather than reasoned: the first cut composed no group, and the
    # custodian could not so much as ENTER the workspace. The root is `02770`
    # and manager-owned, so uid 65532 without the group has no `x` on it --
    # the helper listed the attempt home and stopped there, reporting five
    # entries that were none of its business and never reaching the worker's.
    #
    # It is W33936's capability rather than a gid, on that Work's rule: a
    # group a caller can name is a group a caller chose.
    from .workspaces import WorkspaceGroup
    if type(workspace_group) is not WorkspaceGroup:
        raise ContractRefusal(
            "policy", "denied",
            f"a custody act is composed with this deployment's CONFIGURED "
            f"workspace group, obtained from this manager's own record; this "
            f"is {name_value(workspace_group)}")
    argv += ["--group-add", str(workspace_group.gid)]
    argv += ["--mount",
             f"type=bind,source={source},target={CUSTODY_ROOT},readonly=false"]
    argv += ["--entrypoint", "python3", image_digest,
             "-c", CUSTODY_PROGRAM, operation]
    return argv


# THE SAME UNCONDITIONAL POSTURE THE RUNTIME IS UNDER, minus what a custodian
# has no use for. It is written out rather than imported from `RESTRICTIONS`
# because two of the entries differ for reasons that have to be visible:
#
#   * `--read-only` stays: the one writable place is the mount.
#   * `--network none` stays: a custodian has nothing to talk to, and a helper
#     that could reach a network is a helper that could carry the material it
#     is holding somewhere.
#   * `--user 65532:65532` is the WORKER's identity on purpose, and it is the
#     whole mechanism. As the owner of what the worker created, the custodian
#     may `chmod` it whatever mode the worker chose.
_CUSTODY_RESTRICTIONS = (
    ("--cap-drop", "ALL"),
    ("--security-opt", "no-new-privileges"),
    ("--security-opt", "label=disable"),
    ("--user", "65532:65532"),
    ("--read-only", None),
    ("--network", "none"),
    ("--pids-limit", "128"),
    ("--memory", "512m"),
    ("--cpus", "1"),
    ("--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m"),
)
