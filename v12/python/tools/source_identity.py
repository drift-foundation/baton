"""W384870 review R2 — the CONTENT-BOUND identity of the source a test run tested.

`HEAD` names the committed tree. Everything else that could be under test --
modified, added, deleted, renamed and UNTRACKED files inside the selected scope
-- is identified by the SHA-256 of its bytes, never by its path or status text:
editing a file that `git status` already lists changes no status line, and a
run whose "identity" was a hash of status lines could not tell candidate A from
candidate B. This module hashes the bytes.

THE BOUNDARY IS EXPLICIT. The scope is the path(s) given (the test entries pass
`v12`); what `.gitignore` excludes is excluded here too (so `v12/python/build/`
and other generated outputs never hash themselves), and anything outside the
scope -- the Work records where a run's own evidence lands -- is outside the
identity by construction. Say the scope in the evidence; this module prints it.

Usage: python3 -m tools.source_identity [--repo DIR] SCOPE...  -> JSON on stdout.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys


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


def digest_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(repo, scopes):
    head = _git(repo, "rev-parse", "HEAD").decode().strip()
    entries = []
    for status, path in changed_paths(repo, scopes):
        full = os.path.join(repo, path)
        if os.path.islink(full):
            content = "symlink:" + hashlib.sha256(os.readlink(full).encode()).hexdigest()
        elif os.path.isfile(full):
            content = digest_file(full)
        else:
            content = "absent"
        entries.append({"status": status, "path": path, "sha256": content})
    rolled = hashlib.sha256()
    rolled.update(head.encode())
    for one in entries:
        rolled.update(f"\n{one['status']}\t{one['path']}\t{one['sha256']}".encode("utf-8", "surrogateescape"))
    return {"head": head, "scope": list(scopes), "changed": entries, "changed_count": len(entries),
            "content_digest": rolled.hexdigest(),
            "boundary": "HEAD plus the SHA-256 of every modified, added, deleted, renamed or untracked "
                        "file under the scope; gitignored paths excluded; paths outside the scope excluded"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None, help="repository root (default: the one containing this tool)")
    parser.add_argument("scope", nargs="+", help="repository-relative paths that bound the identity")
    options = parser.parse_args(argv)
    repo = options.repo or _git(os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--show-toplevel").decode().strip()
    print(json.dumps(identity(repo, options.scope), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
