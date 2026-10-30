"""Complete combined base/candidate manifest and retained delta for W325959.

BASE is the COMMITTED baseline tree, read out of the object store rather than
the dirty shared working tree -- the composition evidence pinned that choice at
claim354165 and this manifest keeps it. CANDIDATE is the isolated candidate as
it now stands. Every path that differs is enumerated with both digests.
"""
import hashlib, json, os, subprocess, sys

REPO = "/home/sl/src/baton"
CAND = "/tmp/w325959-354165/candidate"
BASE_COMMIT = "d6881d8adbd567b6e92a4a2a1d0cb68ee781f70a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def committed(path):
    """That path's COMMITTED bytes, or None when the baseline has no such file."""
    done = subprocess.run(["git", "-C", REPO, "cat-file", "-p",
                           f"{BASE_COMMIT}:{path}"],
                          capture_output=True)
    return done.stdout if done.returncode == 0 else None


candidate, delta, absent = {}, {}, []
for root, dirs, files in os.walk(CAND):
    dirs[:] = [one for one in dirs if one != "__pycache__"]
    for name in sorted(files):
        full = os.path.join(root, name)
        rel = os.path.relpath(full, CAND)
        with open(full, "rb") as handle:
            bytes_now = handle.read()
        here = sha(bytes_now)
        candidate[rel] = here
        base_bytes = committed(rel)
        if base_bytes is None:
            absent.append(rel)
            delta[rel] = {"base": None, "candidate": here,
                          "kind": "added-by-this-work"}
        elif sha(base_bytes) != here:
            delta[rel] = {"base": sha(base_bytes), "candidate": here,
                          "kind": "changed-from-baseline"}

print(json.dumps({"candidate_files": len(candidate),
                  "changed_or_added": len(delta),
                  "added": len(absent),
                  "delta": delta}, indent=1, sort_keys=True))
json.dump({"schema": "baton.w325959-combined-manifest/1",
           "base_commit": BASE_COMMIT,
           "candidate_root": CAND,
           "candidate_file_count": len(candidate),
           "candidate": candidate},
          open("/tmp/w325959-355012-CANDIDATE-MANIFEST.json", "w"),
          indent=1, sort_keys=True)
