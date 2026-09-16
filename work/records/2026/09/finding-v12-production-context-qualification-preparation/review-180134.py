"""Bind exact fixture bytes; supervise one focused independent offline run."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(record / "EVIDENCE-180078.json") == "3cdc5355f1a49bcbe5792f4f61396e54b7be4e3e999eefb3e9c0853afa1295ef"
evidence = json.loads((record / "EVIDENCE-180078.json").read_bytes())
checks = []
for row in evidence["files"]:
    path = record / row["path"]
    info = path.lstat()
    checks.append({"path": row["path"], "kind": "current", "sha256": sha(path), "match": stat.S_ISREG(info.st_mode) and sha(path) == row["candidate_sha256"] and oct(stat.S_IMODE(info.st_mode)) == row["mode"]})
    if row["retained_copy"]:
        checks.append({"path": row["retained_copy"], "kind": "candidate", "match": sha(record / row["retained_copy"]) == row["candidate_sha256"]})
        base = record / "candidate-179295" / path.name
        if path.name != "OPERATOR-178579.md":
            checks.append({"path": str(base.relative_to(record)), "kind": "accepted-base", "match": sha(base) == row["base_sha256"]})
assert all(row["match"] for row in checks)
def root_metadata():
    roots = [*evidence["consumed_identity"]["roots"], *[evidence["fresh_roots"][k] for k in ("private_root", "credential_copy_root", "export_root")]]
    found = {}
    for root in roots:
        try:
            info = Path(root).lstat()
            found[root] = {k: getattr(info, k) for k in ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_mtime_ns", "st_ctime_ns")}
        except FileNotFoundError:
            found[root] = None
    return found
roots_before = root_metadata()
assert all(roots_before[evidence["fresh_roots"][k]] is None for k in ("private_root", "credential_copy_root", "export_root"))
before = {row["path"]: sha(record / row["path"]) for row in evidence["files"]}
log_path = record / "review-180134.log"
began = time.monotonic()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX="/tmp/w177936-review-180134-bytecode")
with log_path.open("xb") as log:
    process = subprocess.Popen([sys.executable, "-B", str(record / "review-180134-run.py")], stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=env)
    timeout = False
    try:
        status = process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            status = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            status = process.wait(timeout=5)
    try:
        os.killpg(process.pid, 0)
        gone = False
    except ProcessLookupError:
        gone = True
seconds = time.monotonic() - began
after = {row["path"]: sha(record / row["path"]) for row in evidence["files"]}
roots_after = root_metadata()
assert roots_before == roots_after
report = {"roots_before": roots_before, "roots_after": roots_after, "work": "W177936", "claim": 180134, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "manifest_sha256": evidence["manifest_sha256"], "evidence_sha256": sha(record / "EVIDENCE-180078.json"), "checks": checks, "before": before, "after": after, "unchanged": before == after, "python": sys.version, "seconds": seconds, "timeout": timeout, "exit_code": status, "process_group_absent": gone, "log_sha256": sha(log_path), "run_script_sha256": sha(record / "review-180134-run.py"), "supervisor_sha256": sha(Path(__file__)), "execution": "67 focused offline tests, four identity mismatches despite matching manifest digest, four stale digests refused; root metadata only; no live engine/model/credentials/root reservation"}
with (record / "review-evidence-180134.json").open("x") as stream:
    json.dump(report, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: report[k] for k in ("seconds", "timeout", "exit_code", "process_group_absent", "unchanged")}))
raise SystemExit(0 if status == 0 and gone and not timeout and before == after else 1)
