#!/usr/bin/env python3
"""Read-only import preflight for the joined labels+observation candidate.

Checks, for every path in the joined manifest, against a host checkout:
  * an existing target is a regular, non-symlink file whose bytes equal the
    manifest's `host_86c1c22b` sha256 (the reviewed base bytes), and whose mode
    is owner-writable; custody read-only modes are reported as a refusal, never
    changed, and never treated as checkout mode instructions;
  * a path the manifest marks `new` is ABSENT on the host (no symlink, no file,
    no directory);
  * the host HEAD is the manifest's `checkpoint` and the path set is clean in
    `git status` (read-only).
It never writes, never mutates Git, and exits 0 only when every check passes;
otherwise it prints each refusal and exits 2 BEFORE any import would start.
With --apply-plan it additionally prints the exact file copies an import would
perform (still without performing them).

Usage: import_preflight.py --manifest <joined manifest.json> --host <checkout>
       [--candidate <packet candidate dir>] [--json <out.json>] [--apply-plan]
"""
import argparse, hashlib, json, os, stat, subprocess, sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(host, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    return subprocess.run(["git", "-C", str(host), *args], capture_output=True, text=True, env=env, check=True).stdout


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--host", required=True)
    ap.add_argument("--candidate"); ap.add_argument("--json"); ap.add_argument("--apply-plan", action="store_true")
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text()); host = Path(a.host).resolve()
    refusals, rows = [], []
    head = git(host, "rev-parse", "HEAD").strip()
    if head != manifest["checkpoint"]:
        refusals.append(f"host HEAD {head} is not the manifest checkpoint {manifest['checkpoint']}")
    paths = [e["path"] for e in manifest["paths"]]
    status = git(host, "status", "--porcelain", "--", *paths).strip()
    if status:
        refusals.append("path set not clean in git status: " + status.replace("\n", "; "))
    for e in manifest["paths"]:
        target = host / e["path"]; row = {"path": e["path"], "new": e["new"]}
        try:
            st = os.lstat(target); present = True
        except FileNotFoundError:
            present = False
        row["present"] = present
        if e["new"]:
            if present:
                refusals.append(f"{e['path']}: marked new but something exists on the host"); row["refused"] = "exists"
            else:
                row["check"] = "absent as expected"
        else:
            if not present:
                refusals.append(f"{e['path']}: expected base bytes but the path is absent"); row["refused"] = "absent"; rows.append(row); continue
            if stat.S_ISLNK(st.st_mode):
                refusals.append(f"{e['path']}: is a symlink"); row["refused"] = "symlink"; rows.append(row); continue
            if not stat.S_ISREG(st.st_mode):
                refusals.append(f"{e['path']}: not a regular file"); row["refused"] = "not-regular"; rows.append(row); continue
            row["mode"] = oct(stat.S_IMODE(st.st_mode))
            if not (st.st_mode & stat.S_IWUSR):
                refusals.append(f"{e['path']}: not owner-writable (mode {row['mode']}); custody modes are never changed by an import, repair is the custody owner's"); row["refused"] = "read-only"
            row["host_sha256"] = sha256(target)
            if row["host_sha256"] != e["host_86c1c22b"]:
                refusals.append(f"{e['path']}: host bytes {row['host_sha256'][:12]} differ from the reviewed base {e['host_86c1c22b'][:12]} (drift)"); row["refused"] = "drift"
            else:
                row["check"] = "base bytes match"
        if a.candidate:
            cand = Path(a.candidate) / e["path"]
            row["candidate_sha256"] = sha256(cand) if cand.is_file() else None
            if row["candidate_sha256"] != e["joined"]:
                refusals.append(f"{e['path']}: candidate bytes do not match the manifest's joined sha256"); row["refused"] = "candidate-mismatch"
        rows.append(row)
    verdict = "ok" if not refusals else "refused"
    out = {"verdict": verdict, "host": str(host), "head": head, "checkpoint": manifest["checkpoint"], "manifest": a.manifest, "refusals": refusals, "paths": rows}
    if a.apply_plan and not refusals and a.candidate:
        out["apply_plan"] = [f"copy bytes {Path(a.candidate)/e['path']} -> {host/e['path']} (ordinary mode 0644 for a new file; existing mode kept; no chmod, no install)" for e in manifest["paths"]]
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "head": head, "refusals": refusals, "checked": len(rows)}, indent=2))
    return 0 if verdict == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
