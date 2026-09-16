"""Independent focused verification within the managed reviewer's writable roots."""
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

REPO = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(REPO / "v12/python"), str(REPO / "v12/python/src")]
from tools import stack
from tests.tools import test_stack

began = time.monotonic()
manifest = Path(__file__).with_name("EVIDENCE-184442.json")
evidence = {"claim": 184537, "author_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}
evidence["hashes"] = [{"path": p, "expected": h, "actual": hashlib.sha256((REPO / p).read_bytes()).hexdigest()} for p, h in json.loads(manifest.read_text())["candidates"].items()]
assert all(row["expected"] == row["actual"] for row in evidence["hashes"])
suite = unittest.TestSuite()
for name, case in vars(test_stack).items():
    if isinstance(case, type) and issubclass(case, unittest.TestCase) and case.__module__ == test_stack.__name__ and name not in ("Fixture", "ValidIdleComposition"):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
output = io.StringIO()
start = time.monotonic()
try:
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
finally:
    # The real-spawn write-count case terminates its owned child in cleanup;
    # collect retained Popen handles as well, and account for every one.
    reaped = []
    for child in list(stack._ADMITTED):
        try:
            child.wait(timeout=2)
        except Exception:
            child.terminate()
            try:
                child.wait(timeout=2)
            except Exception:
                child.kill()
                child.wait(timeout=2)
        reaped.append({"pid": child.pid, "returncode": child.returncode})
        stack._collect(child.pid)
evidence["focused_tests"] = {"count": result.testsRun, "success": result.wasSuccessful(), "seconds_including_handle_collection": time.monotonic() - start, "output": output.getvalue()}
evidence["collected_spawn_handles"] = reaped
evidence["remaining_admitted_handles"] = len(stack._ADMITTED)
evidence["composition_not_run"] = "Two ValidIdleComposition cases require disk-backed storage outside checkout. Reviewer writable /tmp is tmpfs; /var/tmp is outside authority. Author evidence remains separate."
evidence["adjacent_evidence_reused"] = {"artifact": "REVIEW-EVIDENCE-184403.json", "tests": 168, "reason": "job_manager.py remains digest-identical to the independently verified candidate; no new adjacent code delta"}
evidence["scope"] = "focused deterministic tests only; no live provider, engine run, v11 operation or Git mutation"
evidence["total_seconds"] = time.monotonic() - began
target = Path(__file__).with_name("REVIEW-EVIDENCE-184537.json")
target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
print(json.dumps({"count": result.testsRun, "success": result.wasSuccessful(), "seconds": evidence["total_seconds"], "remaining_admitted_handles": len(stack._ADMITTED), "evidence": str(target)}))
