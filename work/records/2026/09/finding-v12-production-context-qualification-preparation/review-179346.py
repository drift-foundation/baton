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
assert sha(record / "EVIDENCE-179295.json") == "d51199114b8ca4705d38745803d747e4bbcd0a0b206081dd1387c1c53e515d13"
evidence = json.loads((record / "EVIDENCE-179295.json").read_bytes())
checks = []
for row in evidence["files"]:
    path = record / row["path"]
    info = path.lstat()
    checks.append({"path": row["path"], "kind": "current", "sha256": sha(path), "match": stat.S_ISREG(info.st_mode) and sha(path) == row["candidate_sha256"] and oct(stat.S_IMODE(info.st_mode)) == row["mode"]})
    if row["retained_copy"]:
        checks.append({"path": row["retained_copy"], "kind": "candidate", "match": sha(record / row["retained_copy"]) == row["candidate_sha256"]})
        base = record / "candidate-179146" / path.name
        checks.append({"path": str(base.relative_to(record)), "kind": "accepted-base", "match": sha(base) == row["base_sha256"]})
assert all(row["match"] for row in checks)
before = {row["path"]: sha(record / row["path"]) for row in evidence["files"]}
log_path = record / "review-179346.log"
began = time.monotonic()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX="/tmp/w177936-review-179346-bytecode")
with log_path.open("xb") as log:
    process = subprocess.Popen([sys.executable, "-B", str(record / "review-179346-run.py")], stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=env)
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
report = {"work": "W177936", "claim": 179346, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "manifest_sha256": evidence["manifest_sha256"], "evidence_sha256": sha(record / "EVIDENCE-179295.json"), "checks": checks, "before": before, "after": after, "unchanged": before == after, "python": sys.version, "seconds": seconds, "timeout": timeout, "exit_code": status, "process_group_absent": gone, "log_sha256": sha(log_path), "run_script_sha256": sha(record / "review-179346-run.py"), "supervisor_sha256": sha(Path(__file__)), "execution": "60 selected offline tests; projection parity matrix; malformed model-record observations through real controller/fake engine; no live engine/model/credentials/private roots"}
with (record / "review-evidence-179346.json").open("x") as stream:
    json.dump(report, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: report[k] for k in ("seconds", "timeout", "exit_code", "process_group_absent", "unchanged")}))
raise SystemExit(0 if status == 0 and gone and not timeout and before == after else 1)
