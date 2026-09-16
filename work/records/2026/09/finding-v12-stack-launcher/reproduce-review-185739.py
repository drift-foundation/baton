"""Offline review of W183883's setup delta; no actual install or deployment."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[5]
DIST = REPO / "v12/python"
sys.path.insert(0, str(DIST))
from tools import environment

started = time.monotonic()
dossier = Path(__file__).parent
author = json.loads((dossier / "EVIDENCE-185653.json").read_text())
expected = author["delivered"]["candidates"]
hashes = {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest()
          for path in expected}
assert hashes == expected
evidence = {"claim": 185739, "candidate_hashes": hashes,
            "all_author_hashes_match": True}
test_started = time.monotonic()
tests = subprocess.run([sys.executable, "-m", "unittest", "-v",
                        "tests.tools.test_environment"], cwd=DIST,
                       capture_output=True, text=True, timeout=120)
evidence["tests"] = {"returncode": tests.returncode,
                     "seconds": time.monotonic() - test_started,
                     "stdout": tests.stdout, "stderr": tests.stderr}
dry = subprocess.run(["just", "--dry-run", "setup", "PY=/usr/bin/python3.13"],
                     cwd=REPO / "v12", capture_output=True, text=True, timeout=10)
evidence["documented_override"] = {"returncode": dry.returncode,
                                  "stdout": dry.stdout, "stderr": dry.stderr}
assert '--python "PY=/usr/bin/python3.13"' in dry.stderr + dry.stdout
with tempfile.TemporaryDirectory(prefix="w183883-review-185739-") as scratch:
    root = Path(scratch) / "env"
    calls = []
    def runner(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["-m", "venv"]:
            (root / "bin").mkdir(parents=True)
            (root / "bin/python").symlink_to(sys.executable)
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="simulated index unavailable")
    refusals = []
    for attempt in range(2):
        try:
            environment.setup(root, chosen=sys.executable, runner=runner,
                              stream=io.StringIO())
        except environment.SetupRefusal as failure:
            refusals.append(str(failure))
    evidence["failed_first_install_retry"] = {
        "refusals": refusals, "runner_calls": calls,
        "observed_state": environment.observe(root)["state"],
        "marker_exists": environment.marker_path(root).exists(),
        "directory_preserved": root.is_dir()}
    assert len(refusals) == 2 and "did not create" in refusals[1]
    assert len(calls) == 2 and environment.observe(root)["state"] == "foreign"
evidence["verification_seconds_including_cleanup"] = time.monotonic() - started
evidence["cleanup"] = "TemporaryDirectory removed owned stand-in; all subprocesses completed; no install, network, provider, engine, Job or deployment executed"
(dossier / "REVIEW-EVIDENCE-185739.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"test_returncode": tests.returncode,
                  "seconds": evidence["verification_seconds_including_cleanup"],
                  "counterexamples": ["documented override is a literal executable", "first install failure cannot retry"]}))
