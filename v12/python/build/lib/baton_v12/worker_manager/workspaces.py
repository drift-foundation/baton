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

import os

# W15232: `check_content_manifest` and `validate_fragment` went with the
# acquisition half. They were how this module READ a `gitSource` or
# `directorySource` descriptor and compared a claimed manifest against a
# measured one -- both acts of interpreting an acquisition contract, and
# neither one a manager that receives an already staged directory performs.
from ..contracts import ContractRefusal, digest, digest_of_bytes
from ..contracts.errors import name_value
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
__all__ = ["MAX_ENTRIES", "MAX_BYTES", "MAX_DEPTH", "READ_ONLY_DIR",
           "READ_ONLY_FILE", "assignment_workspace", "directory_manifest",
           "discard_workspace"]

# The frozen contract's own ceilings, so a manifest this component builds is one
# `contentManifest` can hold rather than one it would refuse after the work was
# done. `maxItems` on the entry array is 100,000; the byte total is the frozen
# safe-integer bound, and this component's own limit is far below it because a
# source larger than this is a configuration mistake rather than a workload.
MAX_ENTRIES = 100_000
MAX_BYTES = 4 * 1024 * 1024 * 1024
# Depth is bounded for the same reason the canonicalizer bounds it: a walk with
# no limit is a walk somebody else decides the cost of.
MAX_DEPTH = 64

# Read-only, and OWNER-ONLY. A delivered source is evidence: the worker reads
# it and nothing writes it again, and the mode says so on disk rather than in a
# comment. The execute bit stays on directories because a directory nobody may
# traverse is a directory nobody may read either.
READ_ONLY_FILE = 0o400
READ_ONLY_DIR = 0o500


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
    """
    what = "a source directory"
    real = _real(root, what)
    entries = []
    total = 0
    for place, relative in _walk(real, what):
        content = _read_exactly(place, relative, what)
        entries.append({"path": relative,
                        "bytes": len(content),
                        "content_digest": digest_of_bytes(content)})
        total += len(content)
        if len(entries) > MAX_ENTRIES:
            _denied(f"{what} carries more than {MAX_ENTRIES} files")
        if total > MAX_BYTES:
            _denied(f"{what} carries more than {MAX_BYTES} bytes")
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


def _read_exactly(place, relative, what):
    """One file, opened once, with the descriptor deciding what it was.

    `O_NOFOLLOW` refuses a link AT the open rather than after it, and the
    identity is taken from `fstat` on the descriptor that produced the bytes.
    Anything a racing writer swaps in afterwards is a different file, and this
    never held it.

    A HARD LINK IS REFUSED HERE and not in the walk, because `st_nlink` is a
    property of the inode and the descriptor is what has one. A second name for
    the same inode is the same disclosure a symlink is, with nothing on the
    directory entry to see.
    """
    # RELATIVE TO THE DIRECTORY WE OPENED, so the file is the one that
    # directory holds rather than the one its name resolves to now.
    parent, name = place
    try:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
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
        content = _read_all(descriptor)
    finally:
        os.close(descriptor)
    return content


def _read_all(descriptor):
    pieces = []
    while True:
        piece = os.read(descriptor, 1 << 20)
        if not piece:
            return b"".join(pieces)
        pieces.append(piece)


# -- one private workspace per assignment -------------------------------------


def assignment_workspace(storage, assignment_id):
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
    boundaries.identity(assignment_id, "an assignment identity")
    root = _real(storage, "the manager's workspace storage")
    if not os.path.isdir(root):
        _refuse("the manager's workspace storage is not a directory")
    home = os.path.join(root, assignment_id)
    made = {}
    for name in ("inputs", "workspace"):
        place = os.path.join(home, name)
        os.makedirs(place, exist_ok=True)
        made[name] = _contained(place, root, f"the assignment's {name} root")
    return made


def discard_workspace(storage, assignment_id):
    """Remove ONLY what this component created, and say what it removed.

    Recoverable rather than exact: a tree already gone is the state this asks
    for, so it answers `False` instead of refusing. What it will not do is
    delete anything outside the storage root it was given -- the containment
    check runs before the removal and not after.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    root = _real(storage, "the manager's workspace storage")
    home = os.path.join(root, assignment_id)
    if not os.path.exists(home):
        return False
    _contained(home, root, "the assignment's workspace")
    _remove(home)
    return True


def _remove(place):
    """A depth-first removal that never follows a link out of the tree."""
    for current, directories, files in os.walk(place, topdown=False,
                                               followlinks=False):
        for name in files:
            os.chmod(current, 0o700)
            os.unlink(os.path.join(current, name))
        for name in directories:
            child = os.path.join(current, name)
            if os.path.islink(child):
                os.unlink(child)
                continue
            os.chmod(child, 0o700)
            os.rmdir(child)
    os.chmod(place, 0o700)
    os.rmdir(place)
