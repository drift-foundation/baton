import hashlib, json, subprocess, sys, os
pkt = sys.argv[1]; repo = sys.argv[2]
m = json.load(open(os.path.join(pkt, "candidate-manifest.json")))
def blob(rev, p):
    r = subprocess.run(["git", "-C", repo, "show", f"{rev}:{p}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
def f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
bad = 0
for p, e in m["files"].items():
    checks = [("base-git", blob(m["base_checkpoint"], p), e["base_sha256"]),
              ("retained-git", blob(m["retained_candidate"], p), e["retained_sha256"]),
              ("cand-copy", f(os.path.join(pkt, "candidate", p)), e["candidate_sha256"]),
              ("base-copy", f(os.path.join(pkt, "base", p)), e["base_sha256"]),
              ("ret-copy", f(os.path.join(pkt, "retained", p)), e["retained_sha256"])]
    for name, got, want in checks:
        if got != want:
            bad += 1; print("MISMATCH", p, name, got, want)
# delta set = paths where candidate != retained
delta = sorted(p for p, e in m["files"].items() if e["candidate_sha256"] != e["retained_sha256"])
print("delta==declared", delta == sorted(m["delta_paths"]))
# cumulative set vs git diff product paths
r = subprocess.run(["git","-C",repo,"diff","--name-only",m["base_checkpoint"],m["retained_candidate"],"--","v12"],capture_output=True,text=True).stdout.split()
print("retained v12 paths", len(r), "manifest-has-all", set(r) <= set(m["files"]), "extra", sorted(set(m["files"]) - set(r)))
print("mismatches", bad, "files", len(m["files"]))
