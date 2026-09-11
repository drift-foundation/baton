"""Run only the allocated pair, carrying a 20-second cumulative ceiling."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

evidence = Path(__file__).resolve().parent
repository = next(parent for parent in evidence.parents if (parent / "v12/python").is_dir())
history_path = evidence / "verification.json"
history = json.loads(history_path.read_text()) if history_path.exists() else []
used = sum(one["elapsed_seconds"] for one in history)
remaining = 20 - used
if remaining <= 0:
    raise SystemExit("20-second execution budget exhausted")
run = evidence / ("run-" + str(len(history) + 1))
run.mkdir()

def snapshot():
    return {str(path.relative_to(repository)): {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": oct(path.stat().st_mode & 0o777)}
        for path in sorted((repository / "v12").rglob("*.py")) if path.is_file()}

before = snapshot()
command = [sys.executable, "-m", "unittest", "-v", "tests.tools.test_stage_execution_status_hardening"]
overrides = {"PYTHONPATH": "src:.", "BATON_STATUS_HARDENING_EVIDENCE": str(run)}
start = time.monotonic()
try:
    completed = subprocess.run(command, cwd=repository / "v12/python", env=dict(os.environ, **overrides),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=remaining)
    output, code = completed.stdout, completed.returncode
except subprocess.TimeoutExpired as error:
    output = error.stdout or b""
    output = output.decode() if isinstance(output, bytes) else output
    code = "timeout"
elapsed = time.monotonic() - start
after = snapshot()
(run / "verification.log").write_text(output)
(run / "candidate-hashes.json").write_text(json.dumps({"before": before, "after": after}, indent=2) + "\n")
changed = [path for path in before.keys() | after.keys() if before.get(path) != after.get(path)]
history.append({"command": command, "cwd": str(repository / "v12/python"), "environment_override": overrides,
                "timeout_seconds": remaining, "elapsed_seconds": elapsed, "exit_code": code,
                "changed_paths": sorted(changed), "evidence": run.name})
history_path.write_text(json.dumps(history, indent=2) + "\n")
print(output)
print(json.dumps({"exit_code": code, "elapsed_seconds": elapsed,
                  "cumulative_seconds": used + elapsed, "remaining_seconds": 20 - used - elapsed,
                  "changed_paths": sorted(changed)}))
