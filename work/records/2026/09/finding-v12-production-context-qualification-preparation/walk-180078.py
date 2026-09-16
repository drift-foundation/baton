#!/usr/bin/env python3
"""W177936 bounded metadata-only home walk for the consumed 180078 tree.

Selected by owner180411 from review-2026-09-15T18-36-00Z.md, after the
fixed-path result showed private-layout.json and every use-2 operand absent --
so the stopped run was inside first inventory or subset selection, and the
descendants the fixed paths could not reach are where a nested unreadable file
would be. RUN THIS ON THE ORIGINAL OPERATOR HOST: a managed sandbox's mount and
PID view is not the operator's, so its identity answer would describe the wrong
process and its read/search classification would be meaningless.

WHAT IT REPORTS: the operator's numeric identity, and for each home an AGGREGATE
only -- counts grouped by type, uid, gid, mode, and whether POSIX mode bits
permit that identity to read and to search. Plus honest coverage: entries seen,
truncation, depth limiting, timeout, and traversal errors by closed category.

WHAT IT NEVER DOES, by construction rather than by intention:
  * opens a regular file, or reads any content;
  * follows a symlink, or calls readlink -- links are counted where they are
    found and never resolved;
  * descends into or opens a credential-shaped entry;
  * writes, creates, removes, chmods or chowns anything;
  * resolves user or group names -- identity is numbers only;
  * emits any discovered name, path, path hash, size, mtime, exception string
    or traceback.

AGGREGATES, NOT ENTRIES. A per-entry list would be a directory listing of a
private tree wearing a different hat. Grouping by (type, uid, gid, mode,
readable, searchable) answers the question that was asked -- is anything in here
unreadable to the collector -- without exporting what is in here.

NO COMPONENT IS FOLLOWED. Directories are opened O_NOFOLLOW|O_DIRECTORY from
their parent's descriptor, so a symlinked component is refused rather than
silently resolved, and a race that swaps a directory for a link cannot redirect
the walk.

BOUNDS ARE THE POINT, NOT A FORMALITY: 1024 entries per home, depth 8, 20s wall
time. Reaching one is reported, never silently absorbed -- a truncated walk that
looked complete would be worse than no walk.

This inspects metadata of a stopped attempt. It cannot recover that attempt's
original error, which was never retained. POSIX mode bits do not account for
ACLs, namespaces or other policy, so "permitted" is not proof of readability and
"denied" is not proof of the failure. Identity 180078 is consumed and stays
consumed; this script repairs nothing.
"""
import errno
import json
import os
import re
import stat
import sys
import time

SCHEMA = "baton.w177936.bounded-home-walk/1"
ROOT = "/tmp/baton-w177936-qualification-180078"
RUN_IDENTITY = "180078"
HOMES = ("use-1/home", "use-2/home")

MAX_ENTRIES = 1024
MAX_DEPTH = 8
WALL_SECONDS = 20

# The fixture's own credential shape, so this walk stops exactly where the
# collector stops rather than inventing a second rule.
CREDENTIAL = re.compile(r"credential|oauth|auth[-_.]?token|api[-_.]?key", re.I)

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

_OPEN_DIR = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY


def category(number):
    return CATEGORIES.get(number, "other")


def kind(mode):
    for predicate, name in TYPES:
        if predicate(mode):
            return name
    return "other"


def identity():
    """Numbers only. Resolving names would export arbitrary strings."""
    return {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(),
            "egid": os.getegid(), "groups": sorted(set(os.getgroups()))}


def permission_bits(info, who):
    """The POSIX bits that apply to `who` for this object.

    Owner, then group, then other -- the kernel's order, not the most
    permissive match.
    """
    mode = info.st_mode
    if info.st_uid == who["euid"]:
        return (mode >> 6) & 7
    if info.st_gid == who["egid"] or info.st_gid in who["groups"]:
        return (mode >> 3) & 7
    return mode & 7


def classify(info, who):
    bits = permission_bits(info, who)
    return {"type": kind(info.st_mode), "uid": info.st_uid, "gid": info.st_gid,
            "mode": oct(stat.S_IMODE(info.st_mode)),
            "readable": bool(bits & 4), "searchable": bool(bits & 1)}


def open_component_path(root, relative):
    """A no-follow directory descriptor for root/relative. Raises OSError."""
    fd = os.open(root, _OPEN_DIR)
    try:
        for piece in [p for p in relative.split("/") if p]:
            inner = os.open(piece, _OPEN_DIR, dir_fd=fd)
            os.close(fd)
            fd = inner
        return fd
    except BaseException:
        os.close(fd)
        raise


class Budget:
    """Entry, depth and wall-clock limits, each reported when reached."""

    def __init__(self):
        self.deadline = time.monotonic() + WALL_SECONDS
        self.entries = 0
        self.truncated = False
        self.timed_out = False
        self.depth_limited = False
        self.deepest = 0

    def spend(self):
        if time.monotonic() > self.deadline:
            self.timed_out = True
            return False
        if self.entries >= MAX_ENTRIES:
            self.truncated = True
            return False
        self.entries += 1
        return True

    def exhausted(self):
        return self.truncated or self.timed_out


def walk_home(root, relative, who):
    budget = Budget()
    groups = {}
    errors = {}
    links = 0
    credentials = 0

    def note_error(operation, failure):
        key = operation + ":" + category(failure.errno)
        errors[key] = errors.get(key, 0) + 1

    def count(row):
        key = (row["type"], row["uid"], row["gid"], row["mode"], row["readable"], row["searchable"])
        groups[key] = groups.get(key, 0) + 1

    try:
        top = open_component_path(root, relative)
    except OSError as failure:
        name = category(failure.errno)
        return {"home": relative, "state": "absent" if name == "ENOENT" else "error",
                "errno": name, "entries": 0, "groups": [], "errors": {},
                "links_not_followed": 0, "credential_shaped_skipped": 0,
                "coverage": {"complete": False, "reason": "home not opened",
                             "truncated": False, "timed_out": False,
                             "depth_limited": False, "max_depth_reached": 0}}

    stack = [(top, 0)]
    try:
        while stack:
            fd, depth = stack.pop()
            budget.deepest = max(budget.deepest, depth)
            try:
                if budget.exhausted():
                    continue
                with os.scandir(fd) as entries:
                    for entry in entries:
                        if not budget.spend():
                            break
                        try:
                            info = entry.stat(follow_symlinks=False)
                        except OSError as failure:
                            note_error("stat", failure)
                            continue
                        row = classify(info, who)
                        count(row)
                        # Links are counted where found and never resolved.
                        if stat.S_ISLNK(info.st_mode):
                            links += 1
                            continue
                        # The collector stops at these; so does this.
                        if CREDENTIAL.search(entry.name):
                            credentials += 1
                            continue
                        if not stat.S_ISDIR(info.st_mode):
                            continue
                        if depth + 1 > MAX_DEPTH:
                            budget.depth_limited = True
                            continue
                        try:
                            stack.append((os.open(entry.name, _OPEN_DIR, dir_fd=fd), depth + 1))
                        except OSError as failure:
                            note_error("opendir", failure)
            except OSError as failure:
                note_error("scandir", failure)
            finally:
                os.close(fd)
    finally:
        for fd, _ in stack:
            try:
                os.close(fd)
            except OSError:
                pass

    complete = not (budget.truncated or budget.timed_out or budget.depth_limited or errors)
    return {
        "home": relative, "state": "present", "errno": None,
        "entries": budget.entries,
        "groups": [dict(zip(("type", "uid", "gid", "mode", "readable", "searchable"), key),
                        **{"count": value})
                   for key, value in sorted(groups.items(), key=lambda item: str(item[0]))],
        "errors": dict(sorted(errors.items())),
        "links_not_followed": links,
        "credential_shaped_skipped": credentials,
        "coverage": {"complete": complete,
                     "reason": None if complete else "bounds reached or entries unreadable",
                     "truncated": budget.truncated, "timed_out": budget.timed_out,
                     "depth_limited": budget.depth_limited,
                     "max_depth_reached": budget.deepest},
    }


def report(root):
    who = identity()
    return {"schema": SCHEMA, "work": "W177936", "run_identity": RUN_IDENTITY,
            "root": root, "operator": who,
            "bounds": {"max_entries_per_home": MAX_ENTRIES, "max_depth": MAX_DEPTH,
                       "wall_seconds": WALL_SECONDS},
            "homes": [walk_home(root, relative, who) for relative in HOMES],
            "method": ("no-follow directory descriptors; aggregate counts only; no regular-file "
                       "open, no readlink, no writes, no name resolution, no names exported"),
            "limits": ("POSIX mode bits do not account for ACLs, namespaces or other policy, so "
                       "permitted is not proof of readability and denied is not proof of the "
                       "failure; this cannot recover the stopped attempt's original error")}


def main():
    # No operands at all: a path operand would make this a general-purpose
    # private-tree lister.
    if len(sys.argv) != 1:
        print(json.dumps({"schema": SCHEMA, "refused": "this walk takes no arguments"}))
        return 2
    print(json.dumps(report(ROOT), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
