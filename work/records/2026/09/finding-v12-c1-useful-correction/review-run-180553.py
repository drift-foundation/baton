"""Independent bounded C1 verification over the exact reviewed candidate."""
import ctypes
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(HERE / "CANDIDATE-180423.json") == "2e7107ecbfc133374e1811e33e99e3764924c20f90ceb22ab71683a00d834499"
candidate = json.loads((HERE / "CANDIDATE-180423.json").read_bytes())
checks = []
def check(path, expected, mode=None):
    actual = sha(path)
    info = path.lstat()
    good = actual == expected and stat.S_ISREG(info.st_mode) and (mode is None or oct(stat.S_IMODE(info.st_mode)) == mode)
    checks.append({"path": str(path.relative_to(ROOT)), "sha256": actual, "matches": good})
    assert good, str(path)

for row in candidate["files"]:
    check(ROOT / row["path"], row["sha256"], row["target_mode"])
    check(ROOT / row["snapshot"], row["sha256"], row["custody_mode"])
    check(ROOT / row["base_snapshot"], row["base_sha256"])
for row in candidate["unchanged_selected"] + candidate["read_only_inputs"]:
    check(ROOT / row["path"], row["sha256"], row["mode"])
    if "snapshot" in row:
        check(ROOT / row["snapshot"], row["sha256"])
check(ROOT / candidate["patch"]["path"], candidate["patch"]["sha256"])
check(HERE / "HANDOFF-180423.md", "fb7002066020b014bee958a3dbd55107b464060f0f4bb340625a2486428e4357")
check(HERE / "EVIDENCE-180423.json", "7ebf7dcf65b6e2242cb8ced6d200da7f6f94486c259b6e9f6f92d5a7a3932659")
author = json.loads((HERE / "EVIDENCE-180423.json").read_bytes())
for row in author["artifacts"] + [part for run in author["runs"] for part in (run["receipt"], run["log"])]:
    check(ROOT / row["path"], row["sha256"])
groups = {
    "positive": ["tests.tools.test_correction_restart.UsefulCorrection"],
    "negative": ["tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence"],
    "focused": ["tests.integration.test_managed_storage.PreparedEligibilityUsesCandidateMeasurements", "tests.tools.test_single_worker.OptionalIntegrationContextDeclaration", "tests.tools.test_managed_apply.ContextFreeIntegrationReceiptBoundary", "tests.manager.test_claude_context.ServingBinding", "tests.manager.test_claude_context.WorkerInvocation", "tests.manager.test_claude_context.RestoredCorrectionBoundary"],
}
name = sys.argv[1]
selectors = groups[name]
before = {row["path"]: sha(ROOT / row["path"]) for row in candidate["files"] + candidate["unchanged_selected"] + candidate["read_only_inputs"]}
assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
env = dict(os.environ, PYTHONPATH="src:tools:.", PYTHONDONTWRITEBYTECODE="1", BATON_C_EVIDENCE=str(HERE / ("review-trace-180553-" + name + ".json")))
command = [sys.executable, "-B", "-m", "unittest", "-v", *selectors]
start = time.monotonic()
timed_out = False
signals = []
reaped = []
with (HERE / ("review-run-180553-" + name + ".log")).open("x") as log:
    process = subprocess.Popen(command, cwd=ROOT / "v12/python", env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        status = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        signals.append("TERM-timeout")
        try:
            status = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            signals.append("KILL-timeout")
            status = process.wait(timeout=5)
for sig in (signal.SIGTERM, signal.SIGKILL):
    try:
        os.killpg(process.pid, sig)
        signals.append(sig.name)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            pid, code = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if pid:
            reaped.append([pid, code])
        else:
            time.sleep(0.02)
try:
    os.killpg(process.pid, 0)
    gone = False
except ProcessLookupError:
    gone = True
seconds = time.monotonic() - start
after = {path: sha(ROOT / path) for path in before}
record = {"claim": 180553, "selector_group": name, "command": command, "status": status, "seconds": seconds, "timeout": timed_out, "group_gone": gone, "subreaper": True, "signals": signals, "reaped": reaped, "checks": checks, "before": before, "after": after, "python": sys.version, "dependencies": {n: importlib.metadata.version(n) for n in ("jsonschema", "jsonschema-specifications", "referencing", "attrs", "rpds-py")}}
with (HERE / ("review-run-180553-" + name + ".json")).open("x") as output:
    output.write(json.dumps(record, indent=2) + "\n")
print(json.dumps({k: record[k] for k in ("status", "seconds", "timeout", "group_gone", "signals")}))
assert status == 0 and not timed_out and gone and before == after
