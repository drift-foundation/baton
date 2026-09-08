"""W116014 approved catalog verification; no whole-suite dispatch."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
OUT = HERE / "final-118934"
OUT.mkdir(exist_ok=True)
paths = ("v12/python/tools/parallel_test.py", "v12/python/tests/authority/test_catalog.py", "v12/python/tests/tools/test_parallel_runner.py")
expected = ("f00fec0efebca9df1e25c025d1c9f07d350d1c79f0f0c880e673888bac884547", "14ca384916dd0c175409c9af97c338f923ce73ba789f0eec68a745385904eed6", "690241cb9f51e1405c6d3246bd8a66620a95d4f8ecf561e8d5d4553dfd736406")
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
patch = []
for index, (name, approved) in enumerate(zip(paths, expected)):
    live = ROOT / name
    assert digest(live) == approved, name
    before = HERE / "before" / name if index < 2 else HERE / "proposed-runner-before.py"
    target = OUT / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(live, target)
    patch.extend(difflib.unified_diff(before.read_text().splitlines(keepends=True), live.read_text().splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name))
(OUT / "candidate.patch").write_text("".join(patch))
env = dict(os.environ, PYTHONPATH="src")
remaining = 30.0 - 12.758
start = time.monotonic()
results = []
groups = [("focused", ["tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_the_serial_modules_are_the_ones_that_own_an_engine"]), ("modules", ["tests.tools.test_parallel_runner", "tests.authority.test_catalog"])]
for label, names in groups:
    command = [sys.executable, "-m", "unittest", "-v", *names]
    step = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT / "v12/python", env=env, capture_output=True, text=True, timeout=max(0.001, remaining - (step - start)))
        output = result.stdout + result.stderr
        code = result.returncode
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or b"") + (error.stderr or b"")
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        code = "timeout"
    elapsed = time.monotonic() - step
    (OUT / (label + ".txt")).write_text(output)
    results.append({"group": label, "command": command, "exit_code": code, "elapsed_seconds": elapsed})
    print(json.dumps(results[-1]), flush=True)
    if code != 0:
        print(output, flush=True)
        break
elapsed = time.monotonic() - start
hashes = {name: digest(ROOT / name) for name in paths}
assert tuple(hashes.values()) == expected
report = {"approval": "T116014/M118927", "claim": 118934, "hashes": hashes, "results": results, "prior_seconds": 12.758, "this_claim_seconds": elapsed, "cumulative_seconds": 12.758 + elapsed, "budget_seconds": 30, "all_passed": len(results) == 2 and all(r["exit_code"] == 0 for r in results), "registry_and_authority_catalog_unchanged_this_claim": True}
(OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
raise SystemExit(0 if report["all_passed"] else 1)
