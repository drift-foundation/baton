"""Preflight and import of the JOINED candidate (W385427 + W385424 + W385454) into the host tree.

Adapted from native-handoffs-composer-integration/integrate.py for the joined manifest shape
(`paths[].sha256`/`base_sha256`, `tree_sha256`). The accepted manifest/tree digests are filled in
after the joined review binds them; until then the preflight checks the packet's own consistency.

    python3 -I integrate.py preflight <packet> <evidence-dir>
    python3 -I integrate.py import    <packet> <evidence-dir>

Preflight (read-only): the packet's manifest digests to the accepted SHA256,
`candidate.sha256` re-digests to the accepted tree, every candidate file equals
its manifest digest; HEAD is the candidate's base, `git status -- v12` is
empty, no index.lock; every modified target is a regular non-symlink,
owner-writable file whose bytes equal the manifest's base digest and whose
blob equals the manifest's base_blob and HEAD's blob. Writes PREFLIGHT.json.
Import refuses unless preflight passes NOW, then writes each target through a
sibling temporary and os.replace keeping the existing mode (no chmod/install),
and records POST-IMPORT.json, post-import.sha256, imported-paths.txt.
Git is only read.
"""
import hashlib, json, os, stat, subprocess, sys, tempfile

MANIFEST_SHA = "<set-after-review>"  # the joined manifest the review binds; checked only when not the placeholder
TREE = "<set-after-review>"
BASE = "7ac02c7f01cc59b43ade0c98b55be59ea750af41"
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0")


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, env=ENV, check=True).stdout.strip()


def blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def tree_digest(entries):
    text = "".join(f"{d.split(':', 1)[1]}  {p}\n" for p, d in sorted(entries))
    return sha(text.encode())


def preflight(packet, out):
    faults = []
    raw = open(f"{packet}/manifest.json", "rb").read()
    found = hashlib.sha256(raw).hexdigest()
    if MANIFEST_SHA != "<set-after-review>" and found != MANIFEST_SHA:
        faults.append(f"manifest digests to {found}, accepted {MANIFEST_SHA}")
    m = json.loads(raw)
    tree = "sha256:" + m["tree_sha256"]
    if m["base"] != BASE or (TREE != "<set-after-review>" and tree != TREE):
        faults.append(f"manifest base/tree {m['base']}/{tree}")
    listed = open(f"{packet}/candidate.sha256").read()
    if sha(listed.encode()) != tree:
        faults.append("candidate.sha256 does not re-digest to the manifest's tree")
    head = git("rev-parse", "HEAD")
    if head != BASE:
        faults.append(f"HEAD {head} is not the base {BASE}")
    status = git("status", "--porcelain", "--", "v12")
    if status:
        faults.append(f"v12/ not clean: {status.splitlines()}")
    if os.path.exists(".git/index.lock"):
        faults.append("index.lock present")
    rows = []
    for one in m["paths"]:
        p = one["path"]
        row = {"path": p, "state": "modified", "packet_candidate_sha256": "sha256:" + one["sha256"], "source": one["source"]}
        cand = open(f"{packet}/candidate/{p}", "rb").read()
        if sha(cand) != "sha256:" + one["sha256"]:
            faults.append(f"{p}: packet candidate bytes do not match the manifest")
        st = os.lstat(p) if os.path.lexists(p) else None
        row["host_kind"] = ("symlink" if st and stat.S_ISLNK(st.st_mode) else "file" if st and stat.S_ISREG(st.st_mode) else "absent/other")
        if row["host_kind"] != "file":
            faults.append(f"{p}: host target is {row['host_kind']}"); rows.append(row); continue
        row["host_mode"] = oct(stat.S_IMODE(st.st_mode)); row["host_owner_writable"] = bool(st.st_mode & stat.S_IWUSR) and st.st_uid == os.getuid()
        if not row["host_owner_writable"]:
            faults.append(f"{p}: not owner-writable ({row['host_mode']})")
        host = open(p, "rb").read()
        row["host_sha256"] = sha(host); row["host_blob"] = blob(host); row["head_blob"] = git("rev-parse", f"HEAD:{p}")
        if row["host_sha256"] != "sha256:" + one["base_sha256"] or row["host_blob"] != row["head_blob"]:
            faults.append(f"{p}: host bytes {row['host_sha256']} are not the reviewed base sha256:{one['base_sha256']} (blob {row['host_blob']}, HEAD blob {row['head_blob']})")
        rows.append(row)
    report = {"packet": packet, "manifest_sha256": found, "manifest_expected": MANIFEST_SHA, "tree_digest": "sha256:" + m["tree_sha256"],
              "host_head": head, "host_v12_status_lines": len(status.splitlines()), "paths": rows, "faults": faults}
    os.makedirs(out, exist_ok=True)
    json.dump(report, open(f"{out}/PREFLIGHT.json", "w"), indent=1, sort_keys=True)
    print("PREFLIGHT", "OK" if not faults else "FAULTS", len(rows), "paths;", len(faults), "faults")
    for f in faults: print("  -", f)
    return m, faults


def do_import(packet, out):
    m, faults = preflight(packet, out)
    if faults:
        print("refused: preflight faults; nothing written"); return 2
    imported, entries = [], []
    for one in m["paths"]:
        p = one["path"]; raw = open(f"{packet}/candidate/{p}", "rb").read()
        mode = stat.S_IMODE(os.stat(p).st_mode)
        fd, tmp = tempfile.mkstemp(prefix=".import-", dir=os.path.dirname(p) or ".")
        with os.fdopen(fd, "wb") as w: w.write(raw)
        os.chmod(tmp, mode); os.replace(tmp, p)
        after = open(p, "rb").read()
        assert sha(after) == "sha256:" + one["sha256"], p
        imported.append(p); entries.append((p, sha(after)))
    tree = "sha256:" + hashlib.sha256("".join(f"{d.split(':',1)[1]}  {p}\n" for p, d in entries).encode()).hexdigest()
    status = subprocess.run(["git", "status", "--porcelain", "--", "v12"], capture_output=True, text=True, env=ENV, check=True).stdout.splitlines()  # unstripped: porcelain lines begin with a space
    expected = "sha256:" + m["tree_sha256"]
    report = {"imported": imported, "tree_digest": tree, "tree_expected": expected, "tree_ok": tree == expected,
              "status_after": status, "status_exactly_imported": sorted(s[3:] for s in status) == sorted(imported) and all(s.startswith(" M ") for s in status),
              "index_lock": os.path.exists(".git/index.lock"), "head_after": git("rev-parse", "HEAD"),
              "paths": [{"path": p, "sha256": d, "mode": oct(stat.S_IMODE(os.stat(p).st_mode))} for p, d in entries]}
    json.dump(report, open(f"{out}/POST-IMPORT.json", "w"), indent=1, sort_keys=True)
    open(f"{out}/post-import.sha256", "w").write("".join(f"{d.split(':',1)[1]}  {p}\n" for p, d in entries))
    open(f"{out}/imported-paths.txt", "w").write("".join(p + "\n" for p in imported))
    print("IMPORTED", len(imported), "paths; tree", tree, "ok" if report["tree_ok"] else "MISMATCH", "; status exact:", report["status_exactly_imported"])
    return 0 if report["tree_ok"] and report["status_exactly_imported"] else 3


if __name__ == "__main__":
    mode, packet, out = sys.argv[1:4]
    raise SystemExit((2 if preflight(packet, out)[1] else 0) if mode == "preflight" else do_import(packet, out))
