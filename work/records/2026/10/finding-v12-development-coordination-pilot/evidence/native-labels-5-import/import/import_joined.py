#!/usr/bin/env python3
"""Exact-byte filesystem import of the reviewed joined candidate (K, M385328).

Runs the reviewed read-only preflight (same manifest, host, candidate) in this
process first and refuses on any verdict other than ok. Then, for each of the
manifest's paths, IMMEDIATELY before writing: re-checks that every ancestor
beneath the checkout is a real directory, that an existing target is still a
regular non-symlink owner-writable file whose bytes equal the reviewed base
sha256, and that a new target is still absent; re-hashes the candidate bytes
against the manifest's `joined` sha256. Any mismatch refuses the WHOLE import
before the first write. Writes are ordinary: an existing file is truncated and
rewritten in place (same inode, mode untouched -- no chmod, no install, no
rename-over); a new file is created O_EXCL with mode 0644. Nothing touches Git.
Afterwards every final sha256 and mode is recorded.
"""
import hashlib, importlib.util, json, os, stat, sys
from pathlib import Path

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(manifest, host, candidate, preflight, out):
    spec = importlib.util.spec_from_file_location("import_preflight", preflight)
    pf = importlib.util.module_from_spec(spec); spec.loader.exec_module(pf)
    if pf.main(["--manifest", manifest, "--host", host, "--candidate", candidate]) != 0:
        print("refused: preflight did not pass; nothing written"); return 2
    m = json.loads(Path(manifest).read_text()); host = Path(host).resolve(); cand = Path(candidate)
    plan = []
    for e in m["paths"]:
        target = host / e["path"]; src = cand / e["path"]
        for anc in target.parents:
            if anc == host: break
            st = os.lstat(anc)
            if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
                print(f"refused: ancestor {anc} is not a real directory; nothing written"); return 2
        data = src.read_bytes()
        if hashlib.sha256(data).hexdigest() != e["joined"]:
            print(f"refused: candidate {e['path']} != manifest joined sha256; nothing written"); return 2
        row = {"path": e["path"], "new": e["new"], "joined": e["joined"]}
        if e["new"]:
            try: os.lstat(target); print(f"refused: {e['path']} marked new but exists; nothing written"); return 2
            except FileNotFoundError: pass
        else:
            st = os.lstat(target)
            if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode) or not (st.st_mode & stat.S_IWUSR):
                print(f"refused: {e['path']} type/mode {oct(st.st_mode)}; nothing written"); return 2
            if sha256(target) != e["host_86c1c22b"]:
                print(f"refused: {e['path']} host bytes drifted from reviewed base; nothing written"); return 2
            row["mode_before"] = oct(stat.S_IMODE(st.st_mode)); row["inode_before"] = st.st_ino
        plan.append((row, target, data))
    # EVERY CHECK PASSED FOR EVERY PATH; only now does anything change.
    rows = []
    for row, target, data in plan:
        if row["new"]:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "wb") as f: f.write(data)
        else:
            with open(target, "r+b") as f: f.truncate(0); f.write(data)
        st = os.lstat(target)
        row.update(mode_after=oct(stat.S_IMODE(st.st_mode)), inode_after=st.st_ino,
                   final_sha256=sha256(target), regular=stat.S_ISREG(st.st_mode), symlink=stat.S_ISLNK(st.st_mode))
        row["final_matches_joined"] = row["final_sha256"] == row["joined"]
        rows.append(row)
    ok = all(r["final_matches_joined"] and r["regular"] and not r["symlink"] for r in rows)
    ok = ok and all(r["new"] or r["mode_after"] == r["mode_before"] and r["inode_after"] == r["inode_before"] for r in rows)
    ok = ok and all((not r["new"]) or r["mode_after"] == "0o644" for r in rows)
    report = {"verdict": "imported" if ok else "IMPORTED-WITH-VERIFICATION-FAILURE", "host": str(host), "checkpoint": m["checkpoint"],
              "manifest": manifest, "manifest_sha256": sha256(manifest), "written": len(rows), "paths": rows}
    Path(out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"verdict": report["verdict"], "written": len(rows)}, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
