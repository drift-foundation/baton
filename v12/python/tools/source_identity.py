"""W384870 review R2 — the CONTENT-BOUND identity of the source a test run tested.

`HEAD` names the committed tree. Everything else that could be under test --
modified, added, deleted, renamed and UNTRACKED files inside the selected scope
-- is identified by the SHA-256 of its bytes, never by its path or status text:
editing a file that `git status` already lists changes no status line, and a
run whose "identity" was a hash of status lines could not tell candidate A from
candidate B. This module hashes the bytes.

THE BOUNDARY IS EXPLICIT, in two parts.

The SCOPE is the path(s) given (the test entries pass `v12`): under it, every
changed or untracked file is hashed; what `.gitignore` excludes is excluded
(so `v12/python/build/` and other generated outputs never hash themselves).

The CONSUMED INPUTS are files OUTSIDE the scope that the run executes, imports
or reads -- the reviewed supervisor, captured image contexts, proposed
contracts, manifest vectors -- declared by exact path (`--input`, or
`--declared` for the runner's `tools.parallel_test.CONSUMED_INPUTS`). Each is
hashed by content WHETHER OR NOT git considers it changed, because HEAD binds
only its committed version and an edited or untracked input would otherwise
change what the run tested without changing its identity. A declared input
that is absent, or has no non-ignored file, REFUSES the identity (exit 2): a
run cannot name a candidate it cannot find. Everything else outside the scope
-- the Work records where a run's own evidence lands -- stays out by
construction. Say the scope and the inputs in the evidence; this module prints
both.

Usage: python3 -m tools.source_identity [--repo DIR] [--declared] [--input PATH]... SCOPE...
-> JSON on stdout.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys


class MissingInput(Exception):
    """A declared consumed input is absent (or wholly gitignored) in this checkout."""


def _git(repo, *argv):
    return subprocess.run(["git", "-C", repo, *argv], check=True, capture_output=True).stdout


def changed_paths(repo, scopes):
    """(status, path) for every file git considers changed or untracked under the scopes.

    `--porcelain=v1 -z` is the stable, NUL-separated grammar; a rename carries
    the new path first and the old path as the next record, and both are kept.
    `--untracked-files=all` lists files, not directories, so an untracked tree
    is identified file by file. Ignored files are not listed, which is the
    documented boundary.
    """
    raw = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *scopes)
    records = raw.split(b"\0")
    found = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status, path = record[:2].decode(), record[3:].decode("utf-8", "surrogateescape")
        found.append((status.strip() or "??", path))
        if status[0] in "RC":
            found.append(("<-", records[index].decode("utf-8", "surrogateescape")))
            index += 1
    return sorted(set(found))


def _listed(repo, path, *selection):
    raw = _git(repo, "ls-files", "-z", *selection, "--", path)
    return sorted(one.decode("utf-8", "surrogateescape") for one in raw.split(b"\0") if one)


def input_files(repo, path):
    """(git, path) for every non-ignored file under a declared input, file or directory.

    `git ls-files --cached` lists the tracked files (as git knows them, so a
    deleted tracked file is listed and is then refused as absent), `--others
    --exclude-standard` the untracked files git does not ignore; `__pycache__`
    and other ignored outputs beside an input are not part of it. A declared
    input with no file at all -- absent, or only ignored content -- refuses.
    """
    tracked = _listed(repo, path, "--cached")
    untracked = [one for one in _listed(repo, path, "--others", "--exclude-standard") if one not in tracked]
    found = sorted([("tracked", one) for one in tracked] + [("untracked", one) for one in untracked], key=lambda one: one[1])
    if not found:
        raise MissingInput(f"declared consumed input {path!r} has no file in this checkout "
                           "(absent, or gitignored); the run cannot identify what it would consume")
    return found


def digest_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _content(full):
    if os.path.islink(full):
        return "symlink:" + hashlib.sha256(os.readlink(full).encode()).hexdigest()
    if os.path.isfile(full):
        return digest_file(full)
    return "absent"


def identity(repo, scopes, inputs=()):
    head = _git(repo, "rev-parse", "HEAD").decode().strip()
    entries = []
    for status, path in changed_paths(repo, scopes):
        entries.append({"status": status, "path": path, "sha256": _content(os.path.join(repo, path))})
    consumed = []
    for declared in sorted(set(inputs)):
        for git, path in input_files(repo, declared):
            content = _content(os.path.join(repo, path))
            if content == "absent":
                raise MissingInput(f"declared consumed input {declared!r}: {path!r} is tracked but absent "
                                   "from this checkout; the run cannot identify what it would consume")
            consumed.append({"input": declared, "git": git, "path": path, "sha256": content})
    rolled = hashlib.sha256()
    rolled.update(head.encode())
    for one in entries:
        rolled.update(f"\n{one['status']}\t{one['path']}\t{one['sha256']}".encode("utf-8", "surrogateescape"))
    for one in consumed:
        rolled.update(f"\ninput\t{one['path']}\t{one['sha256']}".encode("utf-8", "surrogateescape"))
    return {"head": head, "scope": list(scopes), "changed": entries, "changed_count": len(entries),
            "inputs": sorted(set(inputs)), "consumed": consumed, "consumed_count": len(consumed),
            "content_digest": rolled.hexdigest(),
            "boundary": "HEAD plus the SHA-256 of every modified, added, deleted, renamed or untracked "
                        "file under the scope, plus the SHA-256 of every non-ignored file of each declared "
                        "consumed input whether changed or not; gitignored paths excluded; other paths "
                        "outside the scope excluded; an absent declared input refuses"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None, help="repository root (default: the one containing this tool)")
    parser.add_argument("--input", action="append", default=[], metavar="PATH",
                        help="a repository-relative file or directory the run consumes outside the scope; repeatable")
    parser.add_argument("--declared", action="store_true",
                        help="also the inputs tools.parallel_test declares (CONSUMED_INPUTS and the supervisors)")
    parser.add_argument("scope", nargs="+", help="repository-relative paths that bound the identity")
    options = parser.parse_args(argv)
    repo = options.repo or _git(os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--show-toplevel").decode().strip()
    inputs = list(options.input)
    if options.declared:
        from tools import parallel_test
        inputs.extend(parallel_test.consumed_inputs())
    try:
        found = identity(repo, options.scope, inputs)
    except MissingInput as refusal:
        print(f"source identity refused: {refusal}", file=sys.stderr)
        return 2
    print(json.dumps(found, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
