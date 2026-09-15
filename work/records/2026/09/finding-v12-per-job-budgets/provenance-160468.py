"""Gather the W156162 candidate's provenance, READ-ONLY, and PIN THE REVISION.

Every Git invocation reads: `rev-parse`, `show`, `diff --numstat`, `diff -U0`.
Nothing writes to the index, the worktree or any ref.

Review 2026-09-13T11:49:41Z corrected two labels in the previous packet, and
both are fixed here rather than restated: the added/removed/hunk totals are for
TRACKED MODIFIED paths only -- the generator leaves them empty for every new
file -- and equal base hashes prove equality at the enumerated paths, not that a
repository HEAD could not have moved, so the revision is pinned explicitly."""
import hashlib
import json
import os
import subprocess

ROOT = "/home/sl/src/baton"
HERE = os.path.join(ROOT, "work/records/2026/09/finding-v12-per-job-budgets")
BEFORE = os.path.join(HERE, "provenance-160341.json")
OUT = os.path.join(HERE, "provenance-160468.json")


def git(*arguments, binary=False):
    done = subprocess.run(("git", "-C", ROOT) + arguments,
                          capture_output=True, check=False)
    if done.returncode != 0:
        return None
    return done.stdout if binary else done.stdout.decode("utf-8")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


head = (git("rev-parse", "HEAD") or "").strip()
held = json.load(open(BEFORE))["paths"]
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

tracked = [one for one in answer if one["tracked_at_head"]]
modified = [one for one in tracked if one["numstat"]]
summary = {
    "head_revision": head,
    "paths": len(answer),
    "new_paths_untracked_at_head": [one["path"] for one in answer
                                    if not one["tracked_at_head"]],
    "tracked_modified_paths": len(modified),
    "tracked_unmodified_paths": [one["path"] for one in tracked
                                 if not one["numstat"]],
    "missing_from_worktree": [one["path"] for one in answer
                              if one["candidate_sha256"] is None],
    # LABELLED, because the previous packet did not say so: these cover the
    # tracked modified paths ONLY. A new file has no base to diff against, so
    # its lines are in none of these numbers.
    "tracked_modified_added_lines": sum(int(one["numstat"].split("\t")[0])
                                        for one in modified),
    "tracked_modified_removed_lines": sum(int(one["numstat"].split("\t")[1])
                                          for one in modified),
    "tracked_modified_zero_context_hunks": sum(one["hunk_count"]
                                               for one in modified),
    "new_path_bytes": sum(one["candidate_bytes"] for one in answer
                          if not one["tracked_at_head"]),
    "candidate_changed_since_160341": [
        one["path"] for one in answer
        if one["candidate_sha256"] != {
            two["path"]: two for two in held}[one["path"]]["candidate_sha256"]],
    "base_changed_since_160341": [
        one["path"] for one in answer
        if one["base_sha256"] != {
            two["path"]: two for two in held}[one["path"]]["base_sha256"]]}

json.dump({"summary": summary, "paths": answer}, open(OUT, "w"), indent=1,
          sort_keys=True)
print(json.dumps(summary, indent=1))
