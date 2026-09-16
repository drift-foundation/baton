"""Independent focused viewer review and renderer probes; no live provider."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time
import unittest

record = Path(__file__).resolve().parent
root = record.parents[4]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

if len(sys.argv) > 1 and sys.argv[1] == "child":
    sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
    from tests.tools import test_job_viewer as tests
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    probes = []
    case = tests.TheTrustedActivityCountIsShownAndNeverEmbellished()
    case.setUp()
    try:
        for state in ("running", "completed", "changes-requested", "exceptional"):
            for count in (1_468_006, (1 << 53) - 1, 10 ** 400):
                doc = case.observed(state=state, count=count)
                stage = doc["jobs"][0]["stages"][0]
                raw = json.dumps(doc).encode()
                snapshot = tests.read_snapshot(raw, received_at=case.now)
                listed = tests.render_list(snapshot, now=case.now)
                detail = tests.render_detail(snapshot, "job-a", now=case.now)
                own = tests.mine(listed)
                probes.append({"state": state, "count": str(count), "input_bytes": len(raw),
                               "stage_id": stage["stage_id"], "own_list_lines": own.splitlines(),
                               "identity_in_list": stage["stage_id"] in own,
                               "instant_in_list": stage["runtime"]["activity"]["observed_at"] in own,
                               "identity_in_detail": stage["stage_id"] in "\n".join(detail),
                               "list_max_stage_width": max(map(len, tests.rows(listed)))})
    finally:
        case.doCleanups()
    receipt = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "probes": probes, "live_threads": [t.name for t in threading.enumerate() if t is not threading.main_thread()]}
    print(json.dumps(receipt), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not receipt["live_threads"] else 1)

manifest_path = record / "viewer-candidate-178930.json"
assert sha(manifest_path) == "820c7c9b1aff17390b78d304d1d320dd8c13c3279823361f362be30b4cc314c7"
manifest = json.loads(manifest_path.read_text())
checked = []
for row in manifest["files"]:
    relative = row["path"].removeprefix("baton:")
    path = root / relative
    assert not path.is_symlink() and stat.S_ISREG(path.stat().st_mode)
    assert sha(path) == row["candidate_sha256"]
    assert oct(stat.S_IMODE(path.stat().st_mode)) == row["mode"]
    for kind, key in (("base", "accepted_viewer_base_sha256"), ("candidate", "reviewed_178853_sha256")):
        assert sha(record / "viewer-review-178853" / kind / relative) == row[key]
    copy = record / "viewer-review-179011" / "candidate" / relative
    copy.parent.mkdir(parents=True, exist_ok=True)
    with copy.open("xb") as out:
        out.write(path.read_bytes())
    checked.append(row)
command = [sys.executable, str(Path(__file__).resolve()), "child"]
receipt = {"work": "W61599", "claim": 179011, "manifest_sha256": sha(manifest_path),
           "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "python": sys.version,
           "files": checked, "command": command, "timeout_seconds": 60, "termination_signals": []}
started = time.monotonic()
log_path = record / "viewer-review-179011.log"
with log_path.open("x") as log:
    process = subprocess.Popen(command, cwd=root / "v12/python", stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt["pgid"] = process.pid
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        receipt["timed_out"] = True
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        receipt["termination_signals"].append(sig.name)
        os.killpg(process.pid, sig)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
    process.poll()
    receipt["exit_code"] = process.returncode
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        receipt["process_group_absent"] = True
    else:
        receipt["process_group_absent"] = False
receipt["elapsed_seconds"] = time.monotonic() - started
receipt["log_sha256"] = sha(log_path)
receipt["files_after_match"] = all(sha(root / row["path"].removeprefix("baton:")) == row["candidate_sha256"] for row in checked)
try:
    receipt["test_receipt"] = json.loads(log_path.read_text().splitlines()[-1])
except (ValueError, IndexError):
    receipt["test_receipt"] = None
(record / "viewer-review-179011.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt["exit_code"] == 0 and receipt["process_group_absent"] and receipt["files_after_match"] else 1)
