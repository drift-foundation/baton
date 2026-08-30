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
from types import MappingProxyType

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries

# W36540 review [P0], round nine: `CustodyRoot` and `attempt_custody_root` are
# GONE from the surface rather than hardened again. Both were path-bearing
# objects a caller held between the authenticated lookup and the use, and every
# defence over nine rounds was a defence on the wrong side of that interval.
# There is no interval now: `custody_act` reads the durable record, composes
# the argv and runs it in one act.
#
# W36540 review [P0], round ten: `custody_vector` is GONE from the surface for
# the same reason `CustodyRoot` was. Returning the composed argv put the
# authenticated bind source in a caller-held mutable list between the durable
# lookup and the engine use -- the same interval, one layer further out, and a
# frozen argv would not have closed it either, because a caller holding a path
# can compose its own vector. `custody_act` performs the act: it looks up,
# composes, RUNS and answers, and what comes back is an answer rather than a
# capability.
__all__ = ["CUSTODY_OPERATIONS", "CUSTODY_ROOT", "CUSTODY_PROGRAM",
           "CUSTODY_ROOTS", "CustodyAnswer", "check_custody_operation",
           "custody_act"]


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


# THE TWO DIRECTORIES A CUSTODY ACT MAY TOUCH, and they are the two the
# acceptance names: the attempt's exact workspace and its result directory.
# Never their parent, which is the assignment home and holds the deliveries.
CUSTODY_ROOTS = ("workspace", "result")


def _derived_root(store, assignment_id, which):
    """The one directory this act may mount, RE-OPENED from durable state.

    EIGHT REVIEW ROUNDS ENDED HERE, and the last two are one lesson. Rounds
    one to six closed doors onto a caller-held object the mint re-read -- a
    plain mapping, one with the expected basenames, the nominal
    `AllocatedRoots` type, that type with its `dict` mutators overridden, with
    `dict` removed from its bases, and with its members behind a private
    attribute. Round seven replaced the object with a derivation from
    `storage`, and found that deriving below a CALLER'S root is still caller
    path selection. Round eight made the store a configured record and handed
    it over as a `WorkspaceStorage`, and round nine found the same defect one
    layer out: `object.__setattr__` replaces a slotted member, so a capability
    minted from durable state and then HELD is a path a caller can still
    change before it is read.

    THE RULE THAT FINALLY FOLLOWS: the operation that selects the mount reads
    the durable record ITSELF, in the same act, and hands no path-bearing
    object to anybody. There is no interval between the authenticated lookup
    and the use, because they are one operation -- so there is nothing to
    retarget, no slot to overwrite and no later re-read to poison. This is
    why the function is private and why `_custody_vector` calls it rather than
    receiving its answer.

    THE STORE IS THE AUTHORITY, and it is not a path-bearing value object: it
    is this manager's own durable handle, and reading the deployment's
    configured store and group out of it is exactly the act the review asks
    for.
    """
    from .workspaces import (configured_workspace_group,
                             configured_workspace_storage, _real, _within)
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
    # outside the configured store before any containment check could see it.
    if os.sep in assignment_id or (os.altsep and os.altsep in assignment_id) \
            or assignment_id in (os.curdir, os.pardir):
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(assignment_id)} is not an assignment identity; an "
            f"attempt is NAMED and a name that carries a path separator is a "
            f"way to compose a home this manager never allocated")
    # READ HERE, USED HERE. The capability objects never leave this frame.
    group = configured_workspace_group(store)
    root = _real(configured_workspace_storage(store).place,
                 "the manager's workspace storage")
    home = os.path.join(root, assignment_id)
    workspace = os.path.join(home, "workspace")
    # EVERY EXISTING PARENT IS PROVED BEFORE ANYTHING IS CREATED. Review [P1],
    # round eight: this used to `os.makedirs` the result root FIRST, so a home
    # entry that was a symlink to another manager-owned directory had
    # `workspace/result` created inside the TARGET and only then raised. A
    # refusal that has already written through the alias has not preserved the
    # boundary it refused for.
    _no_link(home, what="the attempt home")
    _no_link(workspace, what="the attempt's workspace")
    if which == "workspace":
        place = workspace
    else:
        # DERIVED FROM THE PROVED REAL WORKSPACE, so the creation below cannot
        # traverse a link even if one appears at the home between the proof
        # and the write: the path being created no longer contains the
        # component that was proved.
        place = os.path.join(_real(workspace, "the attempt's workspace"),
                             "result")
        if not _no_link(place, missing_ok=True):
            os.makedirs(place, exist_ok=True)
        _no_link(place, what="the attempt's result directory")
    resolved = _real(place, f"the attempt's {which} root")
    if not _within(resolved, root):
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(resolved)} resolves outside this deployment's "
            f"configured workspace store; a custody act is performed on an "
            f"attempt directory this manager allocated")
    return resolved, group.gid


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


def _custody_vector(engine, *, image_digest, name, store, assignment_id,
                    operation, which="workspace"):
    """The closed argv that performs ONE custody act, restrictions and all.

    PRIVATE, and review [P0] round ten is why. It used to be the public
    surface, so the authenticated bind source came back in an ordinary list
    that its holder could rewrite before anything executed it. It is composed
    and consumed inside `custody_act` now, and it is reachable only by the
    engine port that runs it -- which is the party that executes every other
    vector this manager composes.

    IT SELECTS ITS OWN MOUNT, and review [P0] round nine is why that is the
    signature rather than an implementation detail. This used to take a minted
    `CustodyRoot` and a `WorkspaceGroup`, and read `.place` and `.gid` off
    them -- so a caller holding either could replace a slotted member with
    `object.__setattr__` after a valid mint and have the replacement land
    verbatim in `--mount source=...`. Nine rounds of setters, private slots
    and type checks were all on the wrong side of that interval.

    So there is no interval. What crosses is this manager's own durable STORE
    and the attempt's NAME; the configured store and group are read here, the
    root is derived and proved here, and the argv is composed here, in one
    act with nothing path-bearing handed to anybody.

    IT IS NOT A RUNTIME AND DOES NOT REUSE `run_vector`. The two compose
    different things: a runtime is given inputs, a launch document and
    credentials and is expected to run somebody's assignment; a custodian is
    given one directory and a verb. Sharing a composer would mean every
    restriction this needs is one an execution vector could later relax.

    `--rm` AND FOREGROUND, WHICH IS NOT YET A LIFETIME GUARANTEE. Review
    [P1], round ten: this docstring used to say a crash leaks no capability a
    later manager would have to reclaim, and that contradicts this dossier's
    own confirmed first-review finding. What `--rm` actually buys is
    reclamation on the engine's NORMAL removal path: the container goes when
    the act ends. A manager or client that dies mid-act leaves a helper the
    engine never reclaims and this build never looks for.

    `CUSTODY_NAME` exists so a restarted manager COULD find one, and nothing
    reads it yet. Bounded, derivable and restart-reclaimable helper lifetime
    is an owed outcome of this Work and is open in `PLAN.md`; it is named here
    so the code and the record say the same thing.
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
    # THE ONE MOUNT AND THE ONE GROUP, both read from durable state in this
    # same act. There is no host path operand and no path-bearing object at
    # all, so a repository, a credential root or an unrelated sibling cannot
    # be selected -- there is nothing to select them WITH.
    source, gid = _derived_root(store, assignment_id, which)
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
    # group a caller can name is a group a caller chose -- and it is read from
    # the store above rather than handed in, for the same reason the mount is.
    argv += ["--group-add", str(gid)]
    argv += ["--mount",
             f"type=bind,source={source},target={CUSTODY_ROOT},readonly=false"]
    argv += ["--entrypoint", "python3", image_digest,
             "-c", CUSTODY_PROGRAM, operation]
    return argv


class CustodyAnswer:
    """WHAT ONE CUSTODY ACT ANSWERED, and it is deliberately not a capability.

    Review [P0] round ten. The old shape handed back an executable argv
    carrying an authenticated host path; this carries the verb, the engine's
    exit status, the custodian's own document and a bounded diagnostic. There
    is no host path in it -- the program answers paths RELATIVE to its mount,
    which is the only namespace it knows -- and no command vector, so a holder
    has nothing to retarget and nothing to re-execute.

    Immutable for the ordinary reason every answer in this package is: an
    answer somebody can edit is an account of what happened that disagrees
    with what happened.

    NO PUBLIC CONSTRUCTOR, and it is the same rule the capabilities in this
    package are under rather than a shape chosen for tidiness: an answer is
    what one act REPORTED, so a caller that could mint one could report an act
    that never happened. `_answered` below is the only way to make one, and it
    is called in exactly one place -- at the end of the act it describes.
    """

    __slots__ = ("_operation", "_status", "_answer", "_diagnostic")

    def __setattr__(self, name, value):
        raise AttributeError(
            f"a custody answer records what one act did; {name_value(name)} "
            f"is not something a holder revises afterwards")

    __delattr__ = __setattr__

    @property
    def operation(self):
        """The verb this act performed, from the closed vocabulary."""
        return self._operation

    @property
    def status(self):
        """The engine's exit status for the act."""
        return self._status

    @property
    def answer(self):
        """The custodian's own document, read-only, or `None`.

        `None` means the act did not produce one this manager could read --
        which is a fact about the act and never a reason to guess at what it
        did.
        """
        return self._answer

    @property
    def diagnostic(self):
        """A bounded window of what the act wrote to stderr."""
        return self._diagnostic

    @property
    def ok(self):
        """The act ended cleanly AND said what it did.

        Both halves, because a zero exit with no readable answer is an act
        this manager cannot account for, and custody that cannot be accounted
        for is not custody.
        """
        return self._status == 0 and self._answer is not None

    def __repr__(self):
        return (f"CustodyAnswer(operation={self._operation!r}, "
                f"status={self._status!r}, ok={self.ok!r})")


def _answered(operation, status, answer, diagnostic):
    """Mint the one answer for one act. Private, and called in one place."""
    made = object.__new__(CustodyAnswer)
    object.__setattr__(made, "_operation", operation)
    object.__setattr__(made, "_status", status)
    object.__setattr__(made, "_answer",
                       None if answer is None else MappingProxyType(answer))
    object.__setattr__(made, "_diagnostic", diagnostic)
    return made


def custody_act(engine, run, *, image_digest, name, store, assignment_id,
                operation, which="workspace"):
    """ONE CUSTODY ACT, PERFORMED -- lookup, composition, execution, answer.

    Review [P0] round ten, and it is the last interval this Work had left. The
    previous shape authenticated the bind source, composed it into `--mount`
    and RETURNED the list; every production ending would then have executed
    that list separately, so between the durable lookup and the engine use
    there was an ordinary mutable object in somebody else's hands. Nine
    earlier rounds closed that interval around progressively smaller objects.
    This one removes the interval instead: there is no return value a caller
    can execute, because the execution already happened here.

    `run` IS THE ENGINE PORT, the same one every other vector this manager
    composes goes through, and handing the argv to it is not a handoff -- it
    is the invocation. It is the boundary of the process rather than a party
    inside it, and routing custody through it also puts the act under the §13
    sweep `EnginePort` owns.

    WHAT COMES BACK IS AN ANSWER. `CustodyAnswer` carries the verb, the exit
    status, the custodian's document and a bounded diagnostic; it carries no
    host path and no command vector, so nothing a caller holds afterwards can
    select a directory or run anything.
    """
    from .oci import EnginePort

    port = run if type(run) is EnginePort else EnginePort(run)
    argv = _custody_vector(engine, image_digest=image_digest, name=name,
                           store=store, assignment_id=assignment_id,
                           operation=operation, which=which)
    answered = port(argv)
    return _answered(operation, answered["status"],
                     _custodian_document(answered["stdout"]),
                     answered["stderr"][-MAX_DIAGNOSTIC:])


def _custodian_document(stdout):
    """The custodian's one JSON line, or `None`.

    THE LAST NON-EMPTY LINE, because an engine may write its own prose to the
    same stream -- a pull, a warning -- and the custodian's answer is the last
    thing printed by the program this module owns. It is read rather than
    trusted: a document that does not parse, or that is not one JSON object,
    is no document at all, and this answers `None` rather than a partial
    reading of it.
    """
    import json

    for line in reversed((stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            document = json.loads(line)
        except ValueError:
            return None
        return document if type(document) is dict else None
    return None


# How much of a failing act's stderr is kept. The diagnostic explains an
# ending; it is not a transcript, and an unbounded one is a custodian's output
# stored verbatim in this manager's own account of it.
MAX_DIAGNOSTIC = 4096


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
