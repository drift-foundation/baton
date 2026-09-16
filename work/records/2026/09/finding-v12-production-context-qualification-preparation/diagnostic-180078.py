#!/usr/bin/env python3
"""W177936 fixed-path metadata diagnostic for the consumed 180078 tree.

Selected by owner180325 from review-2026-09-15T18-36-00Z.md. RUN THIS ON THE
ORIGINAL OPERATOR HOST: a managed sandbox's mount and PID view is not the
operator's, so its identity answer would describe the wrong process.

WHAT IT DOES: reports the operator's numeric identity, and for eleven fixed
operands under the consumed run root reports state, type, uid, gid, numeric
mode, link count and a closed errno category.

WHAT IT NEVER DOES, by construction rather than by intention:
  * opens a regular file, or reads any content;
  * lists or traverses a directory;
  * calls readlink, so no link target is learned or exported;
  * writes, creates, removes, chmods or chowns anything;
  * resolves user or group names -- account names are arbitrary strings, so
    identity is reported as numbers only;
  * emits an exception string, a traceback, a hash, a size, an mtime, or any
    name discovered from the filesystem.

Every operand label below is a constant in this source. Nothing the tree
contains can become a label, so there is no path by which a private name
reaches the output.

NO COMPONENT IS FOLLOWED, NOT JUST THE LAST ONE. `os.lstat(path)` protects only
the final component: if `use-1/home` were a symlink, an lstat of
`use-1/home/.claude` would silently describe a different location and look like
a clean answer. Each operand is walked component by component through
O_PATH|O_NOFOLLOW|O_DIRECTORY descriptors, so a symlinked intermediate is
REFUSED instead of resolved. The refusal arrives as ENOTDIR on Linux, where
O_DIRECTORY is consulted before O_NOFOLLOW, and as ELOOP elsewhere; both are
inside the closed enum below, so either way you see a refusal rather than
metadata for the wrong location.

This inspects metadata of a stopped attempt. It cannot recover that attempt's
original error, and it cannot convert a failed qualification into a success.
Identity 180078 is consumed and stays consumed; this script repairs nothing.
"""
import errno
import json
import os
import stat
import sys

SCHEMA = "baton.w177936.fixed-path-metadata/1"
ROOT = "/tmp/baton-w177936-qualification-180078"
RUN_IDENTITY = "180078"

# The eleven fixed operands from the review, relative to ROOT. "" is the root.
OPERANDS = (
    "",
    "use-1",
    "use-1/home",
    "use-1/home/.claude",
    "use-1/home/.claude/projects",
    "private-layout.json",
    "private-layout.json.tmp",
    "use-2",
    "use-2/home",
    "use-2/home/.claude",
    "use-2/home/.claude/projects",
)

# The review's closed errno enum. Anything else reports "other" rather than a
# platform-specific name.
_NAMED = ("EACCES", "EPERM", "ENOENT", "ENOTDIR", "ELOOP", "ENOSPC", "EDQUOT", "EIO")
CATEGORIES = {getattr(errno, name): name for name in _NAMED if hasattr(errno, name)}

TYPES = (
    (stat.S_ISDIR, "directory"),
    (stat.S_ISREG, "regular"),
    (stat.S_ISLNK, "symlink"),
    (stat.S_ISFIFO, "fifo"),
    (stat.S_ISSOCK, "socket"),
    (stat.S_ISBLK, "block-device"),
    (stat.S_ISCHR, "char-device"),
)

_NOFOLLOW_DIR = os.O_NOFOLLOW | os.O_DIRECTORY | getattr(os, "O_PATH", 0)


def category(number):
    return CATEGORIES.get(number, "other")


def kind(mode):
    for predicate, name in TYPES:
        if predicate(mode):
            return name
    return "other"


def stat_nofollow(root, relative):
    """Metadata for one operand with NO component followed.

    Raises OSError; the caller classifies it and discards everything else.
    """
    parts = [piece for piece in relative.split("/") if piece]
    fd = os.open(root, _NOFOLLOW_DIR)
    try:
        for piece in parts[:-1]:
            inner = os.open(piece, _NOFOLLOW_DIR, dir_fd=fd)
            os.close(fd)
            fd = inner
        if not parts:
            return os.stat(fd)
        return os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
    finally:
        os.close(fd)


def row(root, relative):
    label = relative or "<root>"
    try:
        info = stat_nofollow(root, relative)
    except OSError as failure:
        # Only the closed category crosses. Never failure.strerror, never
        # failure.filename -- the latter can carry a path we did not choose.
        name = category(failure.errno)
        return {"operand": label, "state": "absent" if name == "ENOENT" else "error",
                "errno": name, "type": None, "uid": None, "gid": None,
                "mode": None, "links": None}
    return {"operand": label, "state": "present", "errno": None,
            "type": kind(info.st_mode), "uid": info.st_uid, "gid": info.st_gid,
            "mode": oct(stat.S_IMODE(info.st_mode)), "links": info.st_nlink}


def identity():
    """Numbers only. Resolving names would export arbitrary strings."""
    return {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(),
            "egid": os.getegid(), "groups": sorted(set(os.getgroups()))}


def report(root):
    return {"schema": SCHEMA, "work": "W177936", "run_identity": RUN_IDENTITY,
            "root": root, "operator": identity(),
            "paths": [row(root, relative) for relative in OPERANDS],
            "method": ("no-follow lstat of fixed operands only; no traversal, no open, "
                       "no readlink, no writes, no name resolution"),
            "limits": ("POSIX mode bits do not account for ACLs, namespaces or other policy "
                       "and are not proof of actual readability; this cannot recover the "
                       "stopped attempt's original error")}


def main():
    # No operands at all: the paths are fixed, and accepting one would make this
    # a general-purpose private-tree reader.
    if len(sys.argv) != 1:
        print(json.dumps({"schema": SCHEMA, "refused": "this diagnostic takes no arguments"}))
        return 2
    print(json.dumps(report(ROOT), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
