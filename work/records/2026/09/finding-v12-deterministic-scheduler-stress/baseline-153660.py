"""Read-only product baseline for W103525; runs disposable existing fixtures."""

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


record = Path(__file__).resolve().parent
label = sys.argv[1] if len(sys.argv) == 2 else "baseline-153660"
if not label.replace("-", "").isalnum():
    raise SystemExit("label must contain only letters, digits and hyphens")
if any((record / (label + suffix)).exists() for suffix in (".log", ".json")):
    raise SystemExit("refusing to overwrite prior run evidence; supply a new label")
repository = next(parent for parent in record.parents if (parent / "AGENTS.md").is_file())
python_root = repository / "v12/python"
selectors = [
    "tests.job_manager.test_scheduling.Capacity",
    "tests.job_manager.test_scheduling.SelectionAndSettlement",
    "tests.job_manager.test_scheduling.FourEffectiveClaimsAreLiveTogether",
    "tests.job_manager.test_scheduling.PoolComposition",
    "tests.job_manager.test_sweep.Eligibility",
    "tests.job_manager.test_sweep.Persistence",
]
command = [sys.executable, "-B", "-m", "unittest", "-v", *selectors]
environment = dict(os.environ, PYTHONPATH=str(python_root / "src") + os.pathsep + str(python_root))
paths = sorted(set(python_root.glob("src/**/*.py")) | set(python_root.glob("tools/**/*.py")) | set(python_root.glob("tests/job_manager/*.py")))
def fingerprints():
    return {str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}

before = fingerprints()
started = time.monotonic()
try:
    result = subprocess.run(command, cwd=python_root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    code, output = result.returncode, result.stdout
except subprocess.TimeoutExpired as error:
    code, output = 124, error.stdout or b""
elapsed = time.monotonic() - started
after = fingerprints()
report = {"work": "W103525", "claim": 153660, "command": command, "cwd": "v12/python", "timeout_seconds": 60,
          "elapsed_seconds": elapsed, "returncode": code, "provider": "none; existing scripted unit fixtures",
          "limits": "Scheduler/control-store baseline with fake Authority sessions and runtime callbacks; not composed multi-team certification.",
          "changed_during_run": [path for path in before if before[path] != after[path]], "source_sha256": before}
try:
    report["jsonschema_version"] = importlib.metadata.version("jsonschema")
except importlib.metadata.PackageNotFoundError:
    report["jsonschema_version"] = None
(record / (label + ".log")).write_bytes(output)
(record / (label + ".json")).write_text(json.dumps(report, indent=2) + "\n")
sys.stdout.buffer.write(output)
print(json.dumps({key: value for key, value in report.items() if key != "source_sha256"}))
sys.exit(code)
