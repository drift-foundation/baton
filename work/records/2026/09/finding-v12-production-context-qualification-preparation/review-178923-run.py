"""Independent correction acceptance; deterministic engine/provider boundaries."""
import json
from pathlib import Path
import stat
import sys
import threading
import unittest

record = Path(__file__).resolve().parent
sys.path.insert(0, str(record / "evidence"))
import test_qualification as tests

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()
case = tests.Controller()
case.setUp()
try:
    fake, outcome = case.execute()
    state = next((case.root / "use-2/home/.claude/projects").glob("*/*.jsonl"))
    source = next((case.root / "use-1/home/.claude/projects").glob("*/*.jsonl"))
    info = state.stat()
    modes = {"restored_state": oct(stat.S_IMODE(info.st_mode)),
             "source_state": oct(stat.S_IMODE(source.stat().st_mode)),
             "request1": oct(stat.S_IMODE((case.root / "request-1.json").stat().st_mode)),
             "request2": oct(stat.S_IMODE((case.root / "request-2.json").stat().st_mode)),
             "source_copy_bytes_equal": source.read_bytes() == state.read_bytes(),
             "owner_uid": info.st_uid, "gid": info.st_gid,
             "actual_engine_execution": False}
    assert modes["restored_state"] == "0o660"
    assert modes["request1"] == modes["request2"] == "0o640"
    assert modes["source_copy_bytes_equal"] and outcome["outcome"] == "qualified"
finally:
    case.doCleanups()
receipt = {"tests": result.testsRun, "errors": len(result.errors), "failures": len(result.failures),
           "controller_metadata_recheck": modes,
           "live_threads": [t.name for t in threading.enumerate() if t is not threading.main_thread()]}
print(json.dumps(receipt), flush=True)
assert not receipt["live_threads"]
