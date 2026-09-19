"""Independent deterministic review. No engine, provider, or installed store."""
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
record = Path(__file__).resolve().parent
repo = record.parents[4]
python = repo / "v12/python"
scratch = Path(tempfile.mkdtemp(prefix="w194457-review195787-"))
result = {"claim": 195787, "scratch": str(scratch), "engine": "none; local filesystem only"}
author = json.loads((record / "EVIDENCE-195725.json").read_text())
result["candidate_sha256"] = {
    path: hashlib.sha256((python / path).read_bytes()).hexdigest()
    for path in author["candidate_sha256"]
}
result["author_hashes_match"] = result["candidate_sha256"] == author["candidate_sha256"]
for path in ("tests/manager/test_custody.py", "tests/manager/test_oci.py",
             "tests/manager/test_lifecycle_composition.py"):
    result["candidate_sha256"][path] = hashlib.sha256((python / path).read_bytes()).hexdigest()

source_path = "v12/python/src/baton_v12/worker_manager/workspaces.py"
historical_source = subprocess.run(["git", "show", "HEAD:" + source_path],
    cwd=repo, check=True, capture_output=True, text=True, timeout=10).stdout
result["historical_source_sha256"] = hashlib.sha256(historical_source.encode()).hexdigest()
node = next(node for node in ast.parse(historical_source).body
            if isinstance(node, ast.FunctionDef) and node.name == "_provision_line_access")
namespace = dict(vars(w))
exec(compile(ast.Module(body=[node], type_ignores=[]), "historical-workspaces", "exec"), namespace)
historical = namespace["_provision_line_access"]

def replacement(case, old=False):
    base = scratch / (case + ("-historical" if old else "-candidate"))
    base.mkdir()
    line = base / "checkout"
    line.mkdir(mode=0o700)
    for name in ("one", "two"):
        (line / name).write_text("original")
    outside = base / "outside"
    outside.write_text("outside sentinel")
    pin = (line.stat().st_dev, line.stat().st_ino)
    identity = w.identity_for(w.WorkspaceGroup(os.getgid(), w._MINT))
    original_open = os.open
    opened = []
    fired = []

    def interleave(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if kwargs.get("dir_fd") is not None and path in ("one", "two"):
            opened.append(path)
            if len(opened) == 2 and case != "control":
                first = line / opened[0]
                first.unlink()
                first.symlink_to(outside)
                fired.append(str(first))
        return descriptor

    try:
        with mock.patch.object(w.os, "open", side_effect=interleave):
            if old:
                historical(str(line), pin, os.getgid())
            else:
                w.prove_line_integrity(str(line), pin, identity)
                w.establish_line_access(str(line), pin, identity)
        outcome = {"returned": True}
    except Exception as failure:
        outcome = {"returned": False, "error": type(failure).__name__, "message": str(failure)}
    return {**outcome, "interleaving": fired, "root_mode": oct(line.stat().st_mode & 0o7777),
            "outside_unchanged": outside.read_text() == "outside sentinel"}

result["replacement"] = {"candidate": replacement("file-to-symlink"),
                         "historical": replacement("file-to-symlink", True),
                         "control": replacement("control")}

line = scratch / "unreadable-checkout"
line.mkdir(mode=0o700)
blocked = line / "blocked-entry"
blocked.write_text("retained")
blocked.chmod(0)
try:
    try:
        w.prove_line_integrity(str(line), (line.stat().st_dev, line.stat().st_ino),
                              w.identity_for(w.WorkspaceGroup(os.getgid(), w._MINT)))
        result["integrity_access_error"] = {"returned": True}
    except Exception as failure:
        result["integrity_access_error"] = {"returned": False, "error": type(failure).__name__,
            "message": str(failure), "root_mode": oct(line.stat().st_mode & 0o7777),
            "names_failed_path": "blocked-entry" in str(failure)}
finally:
    blocked.chmod(0o600)

selection = [
    "tests.manager.test_workspaces.InitialStableLineAccess",
    "tests.manager.test_review_cycles.StableLineLifecycle.test_establishing_access_is_serialized_before_idle_and_never_repeated",
    "tests.manager.test_review_cycles.StableLineLifecycle.test_creating_a_line_PROVES_its_integrity_before_granting_access",
    "tests.manager.test_review_cycles.StableLineLifecycle.test_a_failure_while_establishing_keeps_materializing_and_retry_finishes",
]
env = dict(os.environ, PYTHONPATH=str(python / "src") + os.pathsep + str(python),
           BATON_V12_STACK_TEST_ROOT="/tmp", PYTHONDONTWRITEBYTECODE="1")
env.pop("BATON_V12_ALLOW_LIVE_ENGINE", None)
test_started = time.monotonic()
done = subprocess.run([sys.executable, "-B", "-m", "unittest", *selection],
    cwd=python, env=env, text=True, capture_output=True, timeout=60)
result["tests"] = {"selection": selection, "returncode": done.returncode,
    "stdout": done.stdout, "stderr": done.stderr, "seconds": time.monotonic() - test_started}
result["total_seconds"] = time.monotonic() - started
with (record / "REVIEW-EVIDENCE-195787.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
