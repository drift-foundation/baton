"""Independent deterministic review: focused tests and a pre-grant hardlink race.

Only disposable local filesystem fixtures; no engine/provider/production store.
Writes a new claim-specific result, never the earlier review evidence.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest import mock

from baton_v12.worker_manager import workspaces as w

started = time.monotonic()
record = Path(__file__).parent
results = {"source_sha256": hashlib.sha256(Path(w.__file__).read_bytes()).hexdigest()}
run = subprocess.run(
    [sys.executable, "-B", "-m", "unittest", "tests.manager.test_workspaces",
     "tests.manager.test_review_cycles"], capture_output=True, text=True, timeout=60)
results["focused_tests"] = {"returncode": run.returncode, "stdout": run.stdout,
                            "stderr": run.stderr, "seconds": time.monotonic() - started}

# Read the previous implementation from history without changing Git state.
old_source = subprocess.run(
    ["git", "show", "HEAD:v12/python/src/baton_v12/worker_manager/workspaces.py"],
    capture_output=True, text=True, check=True, timeout=15).stdout
definition = next(n for n in ast.parse(old_source).body
                  if isinstance(n, ast.FunctionDef) and n.name == "_provision_line_access")
namespace = dict(vars(w))
exec(compile(ast.Module(body=[definition], type_ignores=[]), "historical-provision", "exec"), namespace)
old_provision = namespace["_provision_line_access"]

fixture = Path(tempfile.mkdtemp(prefix="w194457-review194592-"))
results["fixture"] = str(fixture)
results["race"] = {}
gid = next(g for g in sorted(set(os.getgroups()) | {os.getgid()}) if g > 0)
identity = w.WorkspaceIdentity(os.geteuid(), gid, w._MINT)
for case in ("historical", "candidate"):
    root = fixture / case
    root.mkdir(mode=0o700)
    for name in ("first", "second"):
        (root / name).write_bytes(b"fixture")
    pin = (root.stat().st_dev, root.stat().st_ino)
    real_open = os.open
    visited = []
    def interleaved_open(path, flags, *args, **kwargs):
        if kwargs.get("dir_fd") is not None:
            if len(visited) == 1:
                # A previously proved regular file acquires an outside alias
                # while the walk opens the next sibling, before any grant.
                os.link(root / visited[0], fixture / (case + "-outside-link"))
            visited.append(path)
        return real_open(path, flags, *args, **kwargs)
    with mock.patch.object(w.os, "open", side_effect=interleaved_open):
        try:
            if case == "historical":
                old_provision(str(root), pin, gid)
            else:
                w.prove_line_integrity(str(root), pin, identity)
                w.establish_line_access(str(root), pin, identity)
            outcome = {"outcome": "returned"}
        except Exception as exc:
            outcome = {"outcome": type(exc).__name__, "message": str(exc)}
    outcome.update(visited=visited, final_link_count=(root / visited[0]).stat().st_nlink,
                   final_root_mode=oct(root.stat().st_mode & 0o7777))
    results["race"][case] = outcome
results["total_seconds"] = time.monotonic() - started
target = record / "REVIEW-EVIDENCE-194592.json"
with target.open("x") as stream:
    json.dump(results, stream, indent=2)
    stream.write("\n")
print(json.dumps(results, indent=2))
