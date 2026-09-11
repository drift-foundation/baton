"""One bounded deterministic coverage run; retain its exact command/result."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

evidence = Path(__file__).resolve().parent
repository = next(parent for parent in evidence.parents if (parent / "v12/python").is_dir())
paths = ["v12/python/tools/stage_execution.py", "v12/python/tools/single_worker.py",
         "v12/python/tests/tools/test_stage_execution.py", "v12/python/tools/parallel_test.py",
         "v12/python/tests/tools/test_stage_execution_hardening.py"]
def snapshot():
    return {path: {"sha256": hashlib.sha256((repository / path).read_bytes()).hexdigest(),
                   "mode": oct((repository / path).stat().st_mode & 0o777)} for path in paths}

before = snapshot()
command = [sys.executable, "-m", "unittest", "-v", "tests.tools.test_stage_execution_hardening"]
environment = dict(os.environ, PYTHONPATH="src:.")
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=repository / "v12/python", env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
    output, code = result.stdout, result.returncode
except subprocess.TimeoutExpired as error:
    output = error.stdout or b""
    output = output.decode() if isinstance(output, bytes) else output
    code = "timeout"
elapsed = time.monotonic() - start
(evidence / "verification.log").write_text(output)
document = {"command": command, "cwd": str(repository / "v12/python"),
            "environment_override": {"PYTHONPATH": "src:."}, "timeout_seconds": 10,
            "elapsed_seconds": elapsed, "exit_code": code,
            "before": before, "after": snapshot()}
(evidence / "verification.json").write_text(json.dumps(document, indent=2) + "\n")
print(output)
print(json.dumps({"elapsed_seconds": elapsed, "exit_code": code,
                  "tracked_files_unchanged": before == document["after"]}))
