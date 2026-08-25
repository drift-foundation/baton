"""EXACT SOURCES, AND ONE PRIVATE WORKSPACE PER ASSIGNMENT.

W6631 (`work/records/2026/08/finding-v12-oci-source-workspace-materializer`),
the first bounded child of W5.

WHAT THIS COMPONENT IS FOR. A worker is handed material and asked to believe it
is what the manifest says. Everything downstream -- the output seal, the
proposal, the receipt -- describes a tree, and if the tree on disk is not the
tree the manifest names then every one of those descriptions is faithful about
the wrong thing. So the tree is REBUILT AND MEASURED here rather than trusted,
and a source that does not recompute to its declared content manifest is not
delivered at all.

THE FOUR RULES THAT DECIDE THE SHAPE:

  1. REGULAR FILES ONLY, and no link of any kind. The frozen host's own
     `input_source.mjs` carries the lesson in its opening comment: a symlink
     inside a record materializes as ordinary files in the worker snapshot, and
     every downstream digest then faithfully describes content the Job was
     never entitled to. A hard link is the same disclosure with no link to see.
  2. THE OPEN FILE IS THE MEASURED FILE. Checking a path and then opening it
     again is two different files whenever anything is racing -- so each entry
     is opened ONCE with `O_NOFOLLOW`, and its identity is taken from the
     descriptor rather than from the name.
  3. NOTHING PARTIAL IS EVER ACCEPTED. Materialization builds under a staging
     name this component owns and is published by one rename; a refusal removes
     the staging tree and leaves no directory a caller could mistake for a
     delivered source.
  4. PRIVATE, NON-OVERLAPPING ROOTS. Two assignments never share a writable
     workspace or Git metadata, and the read-only inputs are not inside the
     writable tree -- a worker that could write into its own inputs would make
     the seal over them describe something that has since changed.

WHAT IS DELIBERATELY NOT HERE, because the assignment says so: OCI engine
mutation, manager lifecycle composition, output acceptance, credential
delivery, provider code and authority access.

AND THE GIT TRANSPORT IS INJECTED RATHER THAN SHELLED OUT. `GitPort` types the
four questions this component asks a repository; the process that answers them
is the deployment's, exactly as the authority session is. That keeps the
VERIFICATION -- which is what W6631 owns -- provable without this package
deciding how a repository is reached, and it is the same capability shape
`AuthorityPort` already uses. The adapter that binds it to a real repository is
named in the record as the next cut rather than written blind here.
"""

import os

from ..contracts import (ContractRefusal, check_content_manifest, digest,
                         digest_of_bytes, validate_fragment)
from ..contracts.errors import name_value
from . import boundaries

# S_IFMT and S_IFREG, written out. The `stat` module is not on this package's
# declared standard-library allowlist and this is the only thing it would be
# imported for -- two constants a reader can check against `man 2 stat` are a
# smaller dependency than a module, and the alternative was widening a list a
# case exists to keep narrow.
_FILE_KIND = 0o170000
_REGULAR = 0o100000

__all__ = ["GitPort", "MAX_ENTRIES", "MAX_BYTES", "MAX_DEPTH", "READ_ONLY_DIR",
           "READ_ONLY_FILE", "assignment_workspace", "directory_manifest",
           "discard_workspace", "materialize_directory_source",
           "materialize_git_source"]

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


class GitPort:
    """The four questions this component asks a repository, TYPED.

    A capability rather than a subprocess call, for the reason `AuthorityPort`
    is one: what this component owns is the VERIFICATION -- that the base
    revision is the immutable object the manifest pins, that an advertised ref
    still names it, and that the working tree it is handed is that revision --
    and none of that should depend on this package deciding how a repository is
    reached.

    `resolve` answers the object a ref names, or None when the repository does
    not carry it. `checkout` materializes one revision into a directory this
    component created, using metadata this component created. Neither is
    allowed to be a bare string: a capability whose members are not typed at
    construction is one whose absence is discovered by a caller's fault.
    """

    MEMBERS = ("resolve", "checkout")

    def __init__(self, repository):
        # THE OPERATIONS ARE THE CAPABILITY, not the object carrying them. A
        # repository is not itself something this manager calls, so typing it
        # would refuse every well-formed one; what must exist and be callable
        # is each question this port asks, and an absent one is discovered here
        # rather than halfway through a delivery.
        self._resolve = boundaries.capability(
            getattr(repository, "resolve", None),
            "the git repository's resolve operation")
        self._checkout = boundaries.capability(
            getattr(repository, "checkout", None),
            "the git repository's checkout operation")

    def resolve(self, uri, ref):
        """The git object a ref names in this repository, or None."""
        return self._resolve(uri=uri, ref=ref)

    def checkout(self, uri, revision, *, into, git_dir):
        """One revision, into a directory and a metadata directory OURS."""
        return self._checkout(uri=uri, revision=revision, into=into,
                              git_dir=git_dir)


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
    """THREE ROOTS, private to one assignment and never overlapping.

    `inputs` is read-only evidence, `workspace` is the only writable tree, and
    `git` holds metadata that belongs to this assignment alone. They are
    siblings rather than nested for the reason the fourth rule states: a worker
    that could write into its own inputs would make the seal over them describe
    a tree that has since changed, and shared Git metadata is one assignment
    able to move another's refs.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    root = _real(storage, "the manager's workspace storage")
    if not os.path.isdir(root):
        _refuse("the manager's workspace storage is not a directory")
    home = os.path.join(root, assignment_id)
    made = {}
    for name in ("inputs", "workspace", "git"):
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


# -- delivering a source ------------------------------------------------------


def materialize_directory_source(source, *, origin, inputs):
    """Deliver one directory source, EXACT and read-only.

    The declared content manifest is not evidence about the tree; it is the
    CLAIM this checks. The tree is measured, the measurement is compared member
    for member, and only then is anything published -- so a source whose digest,
    count or byte total disagrees never becomes a directory a worker can read.

    NOTHING PARTIAL IS PUBLISHED. The copy is built under a staging name this
    component owns and moved into place by one rename; every refusal removes it.
    """
    what = "a directory source"
    # THE FROZEN CLOSED FRAGMENT FIRST, before a member is read or the
    # filesystem is touched. Review [P1]: this owned the document and then
    # checked a hand-written member list, which is a SECOND contract for a
    # shape the frozen schema already states exactly -- `directorySource`
    # closes its member set, types every one of them and carries the content
    # manifest's own rules. A manual list is the "contract that names a subset
    # of what it accepts is a floor" defect, and it also let a malformed
    # source reach a `realpath` call before anything had established it was a
    # source at all.
    declared = validate_fragment(
        boundaries.document(source, "a directory source"),
        "directorySource", what=what)
    measured = directory_manifest(origin)
    _agree(measured, declared["content_manifest"], what)
    destination = _destination(inputs, declared["destination"], what)
    return _publish(origin, destination, measured, what)


def _agree(measured, claimed, what):
    """MEMBER FOR MEMBER, and the disagreement is named.

    Comparing the tree digests alone would be enough to refuse, and would say
    only that two long strings differ. A reader of this refusal is trying to
    find out what is on disk that should not be, so the count and the byte
    total are compared first and named when they differ.
    """
    for member in ("entry_count", "total_bytes", "tree_digest"):
        if measured[member] != claimed[member]:
            _refuse(f"{what} declares {member} "
                    f"{name_value(claimed[member])} and its origin "
                    f"measures {name_value(measured[member])}",
                    code="digest")
    if measured["entries"] != claimed["entries"]:
        _refuse(f"{what} entries do not match its origin, although their "
                f"count, byte total and tree digest agree", code="digest")


def _destination(inputs, destination, what):
    """Where the source lands, INSIDE the assignment's own inputs root."""
    root = _real(inputs, "the assignment's inputs root")
    place = os.path.normpath(os.path.join(root, destination))
    if not _within(place, root):
        _refuse(f"{what} destination "
                f"{name_value(destination)} leaves the "
                f"assignment's inputs root")
    if os.path.exists(place):
        _refuse(f"{what} destination {name_value(destination)} is "
                f"already delivered; a source is materialized once")
    return place


def _publish(origin, destination, measured, what):
    """Copy under a staging name, then ONE rename.

    The staging directory is a sibling of the destination and carries a name
    this component owns, so a half-built tree is never reachable under the name
    a worker is told to read. A refusal removes it; a success is one atomic
    rename.
    """
    staging = _staging(destination, what)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    try:
        os.makedirs(staging, mode=0o700)
        for entry in measured["entries"]:
            _place(origin, staging, entry, what)
        _seal(staging)
        os.rename(staging, destination)
    except BaseException:
        if os.path.exists(staging):
            _remove(staging)
        raise
    return {"destination": destination,
            "entry_count": measured["entry_count"],
            "total_bytes": measured["total_bytes"],
            "tree_digest": measured["tree_digest"]}


def _staging(destination, what):
    """The staging name, and NOTHING MAY ALREADY BE THERE.

    Review [P1]: this removed whatever it found. A symbolic link planted at the
    staging name would have been followed by that removal -- deleting somebody
    else's tree -- and even a leftover directory is material this operation did
    not create and must not silently take over. `lstat` asks about the NAME
    rather than what it points at, so a link is seen as a link.

    A leftover from a crashed delivery is therefore an operator's decision, not
    this operation's: cleanup removes what this component created, and it can
    be asked to.
    """
    staging = destination + ".materializing"
    try:
        os.lstat(staging)
    except FileNotFoundError:
        return staging
    except OSError as error:
        _refuse(f"{what} cannot examine its staging name: {error.strerror}")
    _refuse(f"{what} already has something at its staging name; this "
            f"operation does not follow or remove material it did not create")


def _place(origin, staging, entry, what):
    """One file, re-read and RE-MEASURED as it is written.

    The manifest was measured a moment ago and this reads the origin again, so
    the two reads are compared: a file replaced in between is caught HERE rather
    than delivered under a digest taken from the version that is gone. Reading
    twice is the cost of the guarantee, and the guarantee is the point of the
    component.
    """
    relative = entry["path"]
    # THE SAME NO-FOLLOW DESCENT for the second read. Resolving the whole
    # relative path as a string would walk ancestors by name again, which is
    # the door the fd walk exists to close.
    place = _reach(origin, relative, what)
    try:
        content = _read_exactly(place, relative, what)
    finally:
        os.close(place[0])
    if digest_of_bytes(content) != entry["content_digest"]:
        _refuse(f"{what} entry {name_value(relative)} changed while "
                f"it was being delivered", code="digest")
    place = os.path.join(staging, relative)
    os.makedirs(os.path.dirname(place), mode=0o700, exist_ok=True)
    descriptor = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                         READ_ONLY_FILE)
    try:
        # A SHORT WRITE IS NOT A WRITTEN FILE. Review [P1]: `os.write` may
        # write fewer bytes than it was given and answers how many -- a
        # truncated delivery would otherwise be published under the digest of
        # the whole file, which is the seal describing the wrong tree by
        # another route.
        written = 0
        while written < len(content):
            moved = os.write(descriptor, content[written:])
            if moved <= 0:
                _refuse(f"{what} could not finish writing "
                        f"{name_value(relative)}")
            written += moved
    finally:
        os.close(descriptor)


def _reach(origin, relative, what):
    """`(directory descriptor, name)` for one relative path, opened
    component by component and never followed."""
    parts = relative.split("/")
    handle = _open_directory(None, origin, "", what)
    opened = [handle]
    try:
        for part in parts[:-1]:
            handle = _open_directory(handle, part, relative, what)
            opened.append(handle)
        # THE ANCESTORS ARE CLOSED EITHER WAY. Review [P1]: they were closed
        # only on the failing path, so every delivered file leaked one
        # descriptor per directory above it. The LAST handle is the one the
        # caller reads through and is closed by `_place`.
        for one in opened[:-1]:
            os.close(one)
        return (handle, parts[-1])
    except BaseException:
        for one in opened:
            os.close(one)
        raise


def _seal(place):
    """Read-only on disk, deepest first, so a directory is closed after its
    files are."""
    for current, directories, files in os.walk(place, topdown=False,
                                               followlinks=False):
        for name in files:
            os.chmod(os.path.join(current, name), READ_ONLY_FILE)
        for name in directories:
            os.chmod(os.path.join(current, name), READ_ONLY_DIR)
    os.chmod(place, READ_ONLY_DIR)


def materialize_git_source(source, *, git, inputs, git_metadata):
    """Deliver one Git source at its IMMUTABLE base revision.

    THE REVISION IS THE CONTRACT AND THE REF IS EVIDENCE. §12 pins
    `base_revision` as an object; a ref is a name that moved once and can move
    again. So the revision is what is checked out, and an advertised
    `source_ref` or `integration_ref` is verified to still name that object --
    a ref that has moved REFUSES rather than being followed, because a source
    delivered from where the branch is now is not the source the assignment was
    made against.

    §12 rule 7 is the contracts layer's: a sha1 revision under a sha256
    repository is a different object namespace, not a shorter digest.
    """
    what = "a git source"
    # The frozen closed fragment first, for the same reasons as the directory
    # half: `gitSource` closes the member set, types the revision as a
    # `gitObject` and bounds the ref strings.
    declared = validate_fragment(boundaries.document(source, "a git source"),
                                 "gitSource", what=what)
    # THE FROZEN FRAGMENT ALREADY OWNS IT. `_pinned` stood here and is gone:
    # measured over every malformed revision a caller could send -- absent
    # members, a wrong algorithm, a hex of the wrong length or alphabet, an
    # extra member -- the `gitSource` fragment admits NONE of them, so
    # `_pinned` could never refuse anything that reached it. Item 2's
    # correction, which put the fragment ahead of every member read, is what
    # made it unreachable. The tenth boundary this campaign has removed rather
    # than documented.
    revision = declared["base_revision"]
    if revision["algorithm"] != declared["object_format"]:
        _refuse(f"{what} declares object format "
                f"{name_value(declared['object_format'])} and a "
                f"{name_value(revision['algorithm'])} base revision "
                f"(§12 rule 7)")
    # EVERY ADVERTISED REF, and both of them are optional. `null` means the
    # manifest advertises none, which is not the same as advertising one that
    # cannot be resolved.
    for member in ("source_ref", "integration_ref"):
        advertised = declared[member]
        if advertised is None:
            continue
        _advertised(advertised)
        found = git.resolve(declared["uri"], advertised)
        if found is None:
            _denied(f"{what} advertises {member} "
                    f"{name_value(advertised)}, which this "
                    f"repository does not carry")
        found = _resolved(found)
        if (found["algorithm"], found["hex"]) \
                != (revision["algorithm"], revision["hex"]):
            _denied(f"{what} {member} {name_value(advertised)} now "
                    f"names {name_value(found['hex'])} and the "
                    f"assignment pins {name_value(revision['hex'])}; "
                    f"a ref that moved is evidence that it moved, not a new "
                    f"base revision")
    destination = _destination(inputs, declared["destination"], what)
    private = _private_metadata(git_metadata, declared["name"])
    staging = _staging(destination, what)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    try:
        os.makedirs(staging, mode=0o700)
        git.checkout(declared["uri"], revision, into=staging,
                     git_dir=private)
        # WHAT ARRIVED IS MEASURED LIKE ANY OTHER TREE. A checkout is somebody
        # else's process writing into a directory this component owns, so its
        # answer is evidence and the tree is the fact -- and the same link,
        # special-file and limit rules apply to it.
        measured = directory_manifest(staging)
        _seal(staging)
        os.rename(staging, destination)
    except BaseException:
        if os.path.exists(staging):
            _remove(staging)
        raise
    return {"destination": destination,
            "base_revision": dict(revision),
            "git_dir": private,
            "entry_count": measured["entry_count"],
            "total_bytes": measured["total_bytes"],
            "tree_digest": measured["tree_digest"]}


def _advertised(ref):
    """A ref name the manifest advertises as evidence."""
    return boundaries.text(ref, "an advertised git ref")


def _resolved(found):
    """THE REPOSITORY'S ANSWER, owned on the way in.

    It comes from a capability the deployment supplied, so it is a received
    document rather than one this build made -- indexed only after it is proved
    to have the two members it is about to be compared on.
    """
    return boundaries.document(found, "a resolved git object",
                               required=("algorithm", "hex"))


def _private_metadata(git_metadata, name):
    """Metadata for ONE source of one assignment, and nobody else's.

    Shared Git metadata is one assignment able to move another's refs, prune
    another's objects and decide what another's revision resolves to. The
    directory is created here rather than accepted from a caller so that
    "private" is a fact about what this component made.
    """
    root = _real(git_metadata, "the assignment's git metadata root")
    place = os.path.join(root, name)
    if not _within(place, root):
        _refuse(f"git metadata for {name_value(name)} leaves the "
                f"assignment's own metadata root")
    if os.path.exists(place):
        _refuse(f"git metadata for {name_value(name)} already "
                f"exists; a source's metadata is created once")
    os.makedirs(place, mode=0o700)
    return place
