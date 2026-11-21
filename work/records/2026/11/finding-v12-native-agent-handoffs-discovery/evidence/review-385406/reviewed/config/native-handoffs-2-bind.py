"""Bind ONE owner checkpoint to the exact bytes two accepted candidates fixed.

W385331 qualification, review 2026-11-21T00-55-22Z C3.1. Two accepted packets
describe the source this qualification runs on: the first-slice candidate
(36 paths, manifest `4925897d…`) and the composer correction (12 paths,
manifest `fa01b73d…`). Five paths are in both, and for those the LATER review
accepted the composer bytes -- so the joined path map takes the composer's
digest on every overlap and the slice's digest only where the composer did not
touch the path. Both manifests are themselves pinned by their SHA256 before
their contents are believed.

    python3 -I native-handoffs-2-bind.py --repo DIR --sha SHA --manifests A B
                                          --out bound.json [--tree DIR]

Reads: each path's bytes at `SHA` through `git -C REPO show SHA:path`, or, with
`--tree`, out of a directory (how the checks exercise it on disposable trees).
Writes: the bound file, and ONLY when every path agrees. Any disagreement names
every disagreeing path and exits 2 with nothing written. `--check bound.json`
re-verifies an existing binding against `SHA` (the consuming blocks' guard).
Read-only on Git.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

SCHEMA = "k.native-handoffs-2-binding/2"
# THE ACCEPTED MANIFESTS, pinned by their own bytes: the composer correction
# (review 2026-11-21T00-55-22Z: C1/C2 resolved) and the first slice (review
# 2026-11-20T21-32-47Z). Order matters: the later candidate takes precedence
# on every path both describe.
PINNED = (("native-handoffs-composer",
           "fa01b73d811ffabee510d333f18a97153ab197a21bf16ea32f92736be8ce1e77"),
          ("native-handoffs-1-correction-2",
           "4925897d2bdf6e343d6eac229544b7c2c308f31fbf59ce01ec8b70b9c2aafd24"))
# THE OVERLAP THE REVIEW ENUMERATED (qualification-conflicts.json); computed
# again below and held to this list so a changed manifest cannot widen it
# silently.
OVERLAP = ("v12/STACK.md",
           "v12/python/src/baton_v12/job_manager/role_capability.py",
           "v12/python/tests/tools/test_connected_creation.py",
           "v12/python/tests/tools/test_native_handoffs.py",
           "v12/python/tools/stage_execution.py")


def sha256_bytes(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def refuse(message):
    print("refused: " + message, file=sys.stderr)
    raise SystemExit(2)


def pinned_manifests(places):
    """Each manifest's document, admitted only at its pinned SHA256."""
    held = []
    for (name, digest), place in zip(PINNED, places):
        raw = open(place, "rb").read()
        found = hashlib.sha256(raw).hexdigest()
        if found != digest:
            refuse(f"{place} digests to {found}; the accepted {name} manifest "
                   f"is {digest}. This is not the reviewed manifest and "
                   f"nothing is bound to it")
        held.append((name, digest, json.loads(raw)))
    return held


def joined_map(manifests):
    """`{path: (digest, owner)}` with the later candidate first in precedence."""
    (newer_name, _n, newer), (older_name, _o, older) = manifests
    newer_paths = {one["path"]: one["candidate"] for one in newer["paths"]}
    older_paths = {one["path"]: one["candidate"] for one in older["paths"]}
    overlap = tuple(sorted(set(newer_paths) & set(older_paths)))
    if overlap != tuple(sorted(OVERLAP)):
        refuse(f"the two manifests overlap on {list(overlap)} and the review "
               f"enumerated {list(OVERLAP)}; a changed overlap is not bound "
               f"by precedence nobody reviewed")
    joined = {path: (digest, newer_name) for path, digest in newer_paths.items()}
    for path, digest in older_paths.items():
        joined.setdefault(path, (digest, older_name))
    return joined, overlap


def committed(repo, sha, path):
    out = subprocess.run(["git", "-C", repo, "show", f"{sha}:{path}"],
                         capture_output=True,
                         env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if out.returncode != 0:
        return None
    return sha256_bytes(out.stdout)


def in_tree(tree, path):
    place = os.path.join(tree, path)
    if not os.path.isfile(place) or os.path.islink(place):
        return None
    with open(place, "rb") as reading:
        return sha256_bytes(reading.read())


def verify(joined, read):
    """Every disagreeing path, with what was found."""
    bad = []
    for path in sorted(joined):
        wanted, owner = joined[path]
        found = read(path)
        if found != wanted:
            bad.append({"path": path, "expected": wanted, "owner": owner,
                        "found": found})
    return bad


def main(argv=None):
    parser = argparse.ArgumentParser(prog="native-handoffs-2-bind")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--manifests", nargs=2, required=True,
                        metavar=("COMPOSER", "SLICE"))
    parser.add_argument("--out", default=None)
    parser.add_argument("--tree", default=None,
                        help="read the bytes out of this directory instead of "
                             "git show SHA:path (checks only)")
    parser.add_argument("--check", default=None,
                        help="an existing bound file to re-verify instead of "
                             "writing one")
    taken = parser.parse_args(argv)
    if (taken.out is None) == (taken.check is None):
        refuse("name exactly one of --out and --check")
    if len(taken.sha) != 40 or any(c not in "0123456789abcdef"
                                   for c in taken.sha):
        refuse(f"{taken.sha!r} is not a full lower-case commit identity")
    manifests = pinned_manifests(taken.manifests)
    joined, overlap = joined_map(manifests)
    if taken.tree is not None:
        read = lambda path: in_tree(taken.tree, path)   # noqa: E731
    else:
        read = lambda path: committed(taken.repo, taken.sha, path)  # noqa: E731
    bad = verify(joined, read)
    if bad:
        for one in bad:
            print(f"  {one['path']}: found {one['found']}, accepted "
                  f"{one['expected']} ({one['owner']})", file=sys.stderr)
        refuse(f"{taken.sha} does not carry the accepted bytes of "
               f"{len(bad)} path(s) above; this is not the accepted "
               f"checkpoint and nothing was bound")
    bound = {"schema": SCHEMA, "sha": taken.sha,
             "manifests": {name: digest for name, digest, _ in manifests},
             "overlap_precedence": manifests[0][0],
             "overlap": list(overlap),
             "paths": {path: {"digest": digest, "owner": owner}
                       for path, (digest, owner) in sorted(joined.items())}}
    if taken.check is not None:
        held = json.load(open(taken.check))
        if held != bound:
            refuse(f"the bound file {taken.check} does not describe "
                   f"{taken.sha} with these manifests; re-bind rather than "
                   f"consuming a stale binding")
        print(f"bound {taken.sha} verified: {len(joined)} paths, "
              f"{len(overlap)} overlap paths at {manifests[0][0]} bytes")
        return 0
    with open(taken.out, "x", encoding="utf-8") as writing:
        json.dump(bound, writing, indent=2, sort_keys=True)
        writing.write("\n")
    print(f"bound {taken.sha}: {len(joined)} paths "
          f"({len(manifests[0][2]['paths'])} composer incl. {len(overlap)} "
          f"overlap at composer bytes, "
          f"{len(joined) - len(manifests[0][2]['paths'])} slice-only) -> "
          f"{taken.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
