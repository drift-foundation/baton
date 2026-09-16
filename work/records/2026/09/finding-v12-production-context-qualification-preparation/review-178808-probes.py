"""Independent offline review; only synthetic state and temporary owned paths."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

record = Path(__file__).resolve().parent
sys.path.insert(0, str(record / "evidence"))
import test_qualification as tests
f, c = tests.fixture, tests.c
began = time.monotonic()
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()

case = tests.Controller()
case.setUp()
try:
    fake, outcome = case.execute()
    session_file = next((case.root / "use-2/home/.claude/projects").glob("*/*.jsonl"))
    info = session_file.stat()
    permissions = {"owner_uid": info.st_uid, "gid": info.st_gid, "mode": oct(stat.S_IMODE(info.st_mode)),
                   "selected_runtime_uid": 65532, "runtime_is_owner": info.st_uid == 65532,
                   "group_read": bool(info.st_mode & stat.S_IRGRP), "group_write": bool(info.st_mode & stat.S_IWGRP),
                   "other_write": bool(info.st_mode & stat.S_IWOTH), "fake_controller_outcome": outcome["outcome"],
                   "qualification": "metadata proof; fake uses current UID/GID, not real Docker identities"}
    assert not permissions["runtime_is_owner"]
    assert permissions["mode"] == "0o640" and not permissions["group_write"] and not permissions["other_write"]
finally:
    case.doCleanups()

with tempfile.TemporaryDirectory(prefix="w177936-review-preflight-") as temporary:
    parent = Path(temporary)
    run_root, volatile = parent / "run", parent / "volatile"
    export = parent / "run-export"
    export.mkdir()
    reached = []

    def selected_process(*args, **kwargs):
        reached.append("controller-process-construction")
        raise RuntimeError("offline boundary: no controller or engine started")

    with mock.patch.object(f, "ROOT", run_root), mock.patch.object(f, "VOLATILE", volatile), \
            mock.patch.object(f, "audit", return_value="synthetic-reviewed-manifest"), \
            mock.patch.object(os, "getuid", return_value=1000), mock.patch.object(os, "getgroups", return_value=[c.GROUP]), \
            mock.patch.object(f.grp, "getgrnam", return_value=type("Group", (), {"gr_gid": c.GROUP})()), \
            mock.patch.object(f.multiprocessing, "Process", selected_process), \
            mock.patch.object(f, "engine", side_effect=AssertionError("engine prohibited")), \
            mock.patch.object(f, "credential", side_effect=AssertionError("credential prohibited")):
        try:
            f.run("synthetic-reviewed-manifest")
        except RuntimeError:
            pass
    assert reached == ["controller-process-construction"]
    preflight = {"export_existed_before_admission": True, "reached": reached,
                 "created_run_marker": run_root.exists(), "created_volatile_marker": volatile.exists(),
                 "actual_controller_engine_provider_calls": 0}

receipt = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "permission_probe": permissions, "export_preflight_probe": preflight,
           "live_threads": [t.name for t in threading.enumerate() if t is not threading.main_thread()],
           "elapsed_seconds": time.monotonic() - began}
print(json.dumps(receipt, sort_keys=True), flush=True)
assert not receipt["live_threads"]
