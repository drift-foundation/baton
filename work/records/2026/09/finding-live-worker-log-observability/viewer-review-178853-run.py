"""Focused viewer review, with deterministic renderer boundary probes."""
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest import mock

root = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.tools import test_job_viewer as tests

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()
case = tests.TheTrustedActivityCountIsShownAndNeverEmbellished()
case.setUp()
try:
    doc = case.observed(state="completed")
    snapshot = tests.read_snapshot(doc, received_at=case.now)
    line = next(line for line in tests.render_list(snapshot, now=case.now) if "activity" in line)
    stage = doc["jobs"][0]["stages"][0]
    instant = stage["runtime"]["activity"]["observed_at"]
    clipping = {"line": line, "width": 100, "full_instant_visible": instant in line,
                "stage_id_visible": stage["stage_id"] in line, "instant": instant}
    bad = case.observed(count=10 ** 400)
    # Exercise the ordinary JSON file-input parser, not just a Python object.
    raw = json.dumps(bad).encode()
    malformed = tests.read_snapshot(raw, received_at=case.now)
    try:
        tests.render_list(malformed, now=case.now)
    except Exception as error:
        count_probe = {"snapshot_accepted": True, "bytes": len(raw), "error": type(error).__name__}
    else:
        count_probe = {"snapshot_accepted": True, "bytes": len(raw), "error": None}
    with mock.patch.object(tests.job_viewer, "_activity", return_value=tests.job_viewer.UNKNOWN):
        old_behavior = tests.render_list(malformed, now=case.now)
    count_probe["old_constant_activity_renders"] = bool(old_behavior)
finally:
    case.doCleanups()

receipt = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "clipping_probe": clipping, "oversized_integer_probe": count_probe,
           "live_threads": [t.name for t in threading.enumerate() if t is not threading.main_thread()]}
print(json.dumps(receipt), flush=True)
assert not receipt["live_threads"]
