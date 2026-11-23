import hashlib, json, os, sys, subprocess
pkt, repo, base, cand = sys.argv[1:5]
m = json.load(open(os.path.join(pkt, "candidate-manifest.json")))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
bad = 0
for p, e in m["files"].items():
    g = subprocess.run(["git", "-C", repo, "show", f"{m['base']}:{p}"], capture_output=True)
    for name, got, want in (("base-git", hashlib.sha256(g.stdout).hexdigest() if g.returncode == 0 else None, e["base_sha256"]),
                            ("base-copy", h(os.path.join(pkt, "base", p)), e["base_sha256"]),
                            ("cand-copy", h(os.path.join(pkt, "candidate", p)), e["candidate_sha256"]),
                            ("cand-tree", h(os.path.join(cand, p)), e["candidate_sha256"])):
        if got != want: bad += 1; print("MISMATCH", p, name, got, want)
print("patch", h(os.path.join(pkt, "candidate.patch")) == m["patch_sha256"])
print("paths==files", sorted(m["paths"]) == sorted(m["files"]))
print("mismatches", bad, "files", len(m["files"]))
