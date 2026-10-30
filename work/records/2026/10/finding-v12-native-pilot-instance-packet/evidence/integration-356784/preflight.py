"""Whole-path integration preflight for the accepted 34-path delta.

Read-only. Per AGENTS.md's integrator rules every existing target must be a
non-symlink REGULAR file, already OWNER-WRITABLE, and matching the REVIEWED
BASE bytes; every planned addition must not already exist. Per the owner's
approval the whole target set is checked BEFORE any import and divergence stops
it.
"""
import hashlib, json, os, stat, subprocess

REPO = "/home/sl/src/baton"
BASE = "d6881d8adbd567b6e92a4a2a1d0cb68ee781f70a"
DELTA = json.load(open("/home/sl/src/baton/work/records/2026/10/"
                       "finding-v12-native-pilot-instance-packet/evidence/"
                       "combined-355012/DELTA.json"))["delta"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def at_rev(rev, path):
    done = subprocess.run(["git", "-C", REPO, "cat-file", "-p", f"{rev}:{path}"],
                          capture_output=True)
    return sha(done.stdout) if done.returncode == 0 else None


rows, buckets = {}, {}
for path, facts in sorted(DELTA.items()):
    accepted = facts["candidate"]
    reviewed_base = facts["base"]          # None for a planned addition
    full = os.path.join(REPO, path)
    link = os.path.islink(full)
    there = os.path.exists(full) and not link
    info = {"accepted": accepted, "reviewed_base": reviewed_base,
            "at_base_commit": at_rev(BASE, path), "at_head": at_rev("HEAD", path),
            "exists": there, "is_symlink": link}
    if there:
        st = os.stat(full)
        with open(full, "rb") as handle:
            info["worktree"] = sha(handle.read())
        info["mode"] = oct(stat.S_IMODE(st.st_mode))
        info["owner_writable"] = bool(st.st_mode & stat.S_IWUSR)
        info["regular"] = stat.S_ISREG(st.st_mode)
    else:
        info["worktree"] = None

    if info["worktree"] == accepted:
        verdict = "ALREADY-AT-ACCEPTED"
    elif reviewed_base is None and there:
        verdict = "OVERLAP: planned addition already exists"
    elif reviewed_base is None:
        verdict = "READY: addition, target absent"
    elif info["worktree"] == reviewed_base:
        verdict = "READY: target matches reviewed base"
    elif info["worktree"] is None:
        verdict = "DIVERGED: existing target is missing"
    else:
        verdict = "DIVERGED: target is neither reviewed base nor accepted"
    info["verdict"] = verdict
    rows[path] = info
    buckets[verdict.split(":")[0]] = buckets.get(verdict.split(":")[0], 0) + 1

print(json.dumps(buckets, indent=1))
print()
for path, info in rows.items():
    if not info["verdict"].startswith("ALREADY"):
        print(info["verdict"], path)
        print("   worktree", str(info["worktree"])[:16], "| reviewed_base",
              str(info["reviewed_base"])[:16], "| HEAD", str(info["at_head"])[:16],
              "| accepted", info["accepted"][:16])
bad = [p for p, i in rows.items()
       if i["exists"] and not (i.get("owner_writable") and i.get("regular"))]
print()
print("NON-REGULAR OR NOT OWNER-WRITABLE:", bad)
print("SYMLINKS:", [p for p, i in rows.items() if i["is_symlink"]])
modes = sorted({i["mode"] for i in rows.values() if i.get("mode")})
print("MODES PRESENT:", modes)
json.dump(rows, open("/tmp/preflight.json", "w"), indent=1, sort_keys=True)
