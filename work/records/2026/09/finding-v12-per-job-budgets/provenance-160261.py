"""Gather the W156162 candidate's provenance, READ-ONLY.

Every Git invocation below reads: `rev-parse`, `ls-tree`, `show`, `diff` with
`--numstat` and with `-U0`. Nothing writes to the index, the worktree or any
ref. The path list is the candidate's own 29 paths, taken from the previous
packet so that the two can be compared path by path rather than re-derived from
a working tree that other Works also touch."""
import hashlib
import json
import os
import subprocess

ROOT = "/home/sl/src/baton"
HERE = os.path.join(ROOT, "work/records/2026/09/finding-v12-per-job-budgets")
BEFORE = os.path.join(HERE, "provenance-159612.json")
OUT = os.path.join(HERE, "provenance-160261.json")


def git(*arguments, binary=False):
    done = subprocess.run(("git", "-C", ROOT) + arguments,
                          capture_output=True, check=False)
    if done.returncode != 0:
        return None
    return done.stdout if binary else done.stdout.decode("utf-8")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


held = json.load(open(BEFORE))
paths = [one["path"] for one in held]
answer = []
for path in paths:
    where = os.path.join(ROOT, path)
    candidate = open(where, "rb").read() if os.path.exists(where) else None
    base = git("show", f"HEAD:{path}", binary=True)
    numstat = git("diff", "--numstat", "HEAD", "--", path) or ""
    hunks = git("diff", "-U0", "HEAD", "--", path) or ""
    answer.append({
        "path": path,
        "tracked_at_head": base is not None,
        "base_bytes": None if base is None else len(base),
        "base_sha256": None if base is None else digest(base),
        "candidate_bytes": None if candidate is None else len(candidate),
        "candidate_sha256": None if candidate is None else digest(candidate),
        "numstat": numstat.strip("\n"),
        "hunk_count": len([one for one in hunks.splitlines()
                           if one.startswith("@@")])})

json.dump(answer, open(OUT, "w"), indent=1, sort_keys=True)

# WHAT MOVED SINCE THE PREVIOUS PACKET, so the difference is reported rather
# than left for a reader to diff two files by hand.
was = {one["path"]: one for one in held}
moved = [one["path"] for one in answer
         if one["candidate_sha256"] != was[one["path"]]["candidate_sha256"]]
same_head = [one["path"] for one in answer
             if one["base_sha256"] != was[one["path"]]["base_sha256"]]
print(json.dumps({
    "paths": len(answer),
    "untracked_at_head": [one["path"] for one in answer
                          if not one["tracked_at_head"]],
    "missing_from_worktree": [one["path"] for one in answer
                              if one["candidate_sha256"] is None],
    "candidate_changed_since_159612": moved,
    "base_changed_since_159612": same_head,
    "total_added": sum(int(one["numstat"].split("\t")[0])
                       for one in answer
                       if one["numstat"] and one["numstat"].split("\t")[0]
                       .isdigit()),
    "total_removed": sum(int(one["numstat"].split("\t")[1])
                         for one in answer
                         if one["numstat"] and one["numstat"].split("\t")[1]
                         .isdigit()),
    "total_hunks": sum(one["hunk_count"] for one in answer)}, indent=1))
