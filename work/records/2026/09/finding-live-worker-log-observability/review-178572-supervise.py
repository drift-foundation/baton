"""Independent bounded W61599 focused acceptance; no discovery or live provider."""
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[4]
packet = record / "correction-178427"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = json.loads((packet / "candidate.json").read_text())
assert sha(packet / "candidate.json") == "acabca2d229f984a647626d6feb5244d4d1d0bea95c80b025f802ca9194138b3"
checked = []
for row in manifest["files"]:
    path = root / row["path"].removeprefix("baton:")
    assert not path.is_symlink() and stat.S_ISREG(path.stat().st_mode)
    assert sha(path) == sha(root / row["candidate_path"]) == row["candidate_sha256"]
    assert sha(root / row["base_path"]) == row["base_sha256"]
    assert oct(stat.S_IMODE(path.stat().st_mode)) == row["candidate_mode"]
    checked.append({"path": row["path"], "sha256": sha(path), "mode": row["candidate_mode"]})
evidence = json.loads((record / "EVIDENCE-178427.json").read_text())
for row in evidence:
    assert sha(root / row["path"]) == row["sha256"], row["path"]
assert sha(record / "HANDOFF-178427.md") == "f403e933156422bd018f7315a38250e1ae8dde952aca30317a7e0e2533bd1a55"
assert sha(record / "EVIDENCE-178427.json") == "98a2d59c412c64d2ba22959ac37d69c15eb1d16593fffe7ce0eb34da4c0eeba9"

command = [sys.executable, str(packet / "run-focused.py"), "focused"]
receipt = {"work": "W61599", "review_claim": 178572, "candidate_manifest_sha256": sha(packet / "candidate.json"),
           "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": command,
           "python": sys.version, "dependencies": {p: importlib.metadata.version(p) for p in ("jsonschema", "referencing", "jsonschema-specifications", "attrs", "rpds-py")},
           "files_before": checked, "verified_evidence_files": len(evidence), "timeout_seconds": 60, "termination_signals": []}
log_path = record / "review-178572-focused.log"
started = time.monotonic()
with log_path.open("x") as log:
    process = subprocess.Popen(command, cwd=root / "v12/python", stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt["pgid"] = process.pid
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            receipt["termination_signals"].append(sig.name)
            os.killpg(process.pid, sig)
            try:
                process.wait(timeout=5)
                break
            except subprocess.TimeoutExpired:
                continue
    receipt["exit_code"] = process.returncode
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        receipt["process_group_absent"] = True
    else:
        receipt["process_group_absent"] = False
        os.killpg(process.pid, signal.SIGTERM)
        receipt["termination_signals"].append("SIGTERM-surviving-group")
receipt["elapsed_seconds"] = time.monotonic() - started
receipt["log_sha256"] = sha(log_path)
receipt["files_after_match"] = all(sha(root / row["path"].removeprefix("baton:")) == row["sha256"] for row in checked)
try:
    receipt["test_receipt"] = json.loads(log_path.read_text().splitlines()[-1])
except (ValueError, IndexError):
    receipt["test_receipt"] = None
(record / "review-178572-focused.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({k: v for k, v in receipt.items() if k != "files_before"}, indent=2))
raise SystemExit(0 if receipt["exit_code"] == 0 and receipt["process_group_absent"] and receipt["files_after_match"] and receipt["test_receipt"] and not receipt["test_receipt"]["live_threads"] else 1)
