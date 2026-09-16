"""Independent W183883 review. Run with python3; no deployment mutation.

Reads retained bundles, runs focused tests in /tmp, and mocks lifecycle commands
to check the retained harness's exceptional cleanup. Does not run that harness
against an actual stack. No Git operation, store read, provider, or Job.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest import mock

D = Path(__file__).resolve().parent
ROOT = D.parents[4]
PYTHON = ROOT / "v12/python"
sys.dont_write_bytecode = True
sys.path[:0] = [str(PYTHON), str(PYTHON / "src")]
from tools import instance


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    author = json.loads((D / "EVIDENCE-187015.json").read_text())
    artifact = json.loads((D / "ARTIFACT-MANIFEST-187015.json").read_text())
    result = {"claim": 187086, "candidate_hashes": {}, "artifact_source_mismatches": {}}
    for path, expected in author["candidates"].items():
        actual = sha(ROOT / path)
        result["candidate_hashes"][path] = actual
        assert actual == expected, path
    for path, expected in artifact["source"].items():
        actual = sha(ROOT / path)
        if actual != expected:
            result["artifact_source_mismatches"][path] = {"recorded": expected, "current": actual}
    result["bundles"] = {}
    paths = [PYTHON / "build/out/distro"] + [Path(x) / "distro" for x in artifact["retained"]["destinations"]]
    for path in paths:
        found = instance.manifest(path)
        assert found["digest"] == author["the_artifact"]["digest"], str(path)
        result["bundles"][str(path)] = {k: found[k] for k in ("files", "digest")}
    result["build_log_sha256"] = sha(D / artifact["build"]["log"])
    assert result["build_log_sha256"] == artifact["build"]["log_sha256"]
    scratch = Path(tempfile.mkdtemp(prefix="w183883-review187086-", dir="/tmp"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="src:.",
               TMPDIR=str(scratch), XDG_RUNTIME_DIR=str(scratch),
               BATON_V12_STACK_DISTRO=str(paths[0]), BATON_V12_STACK_PACKAGING_REQUIRED="1")
    argv = [sys.executable, "-m", "unittest", "tests.tools.test_instance",
            "tests.tools.test_environment", "tests.tools.test_packaging",
            "tests.tools.test_stack.WhatTheRepositoryIS"]
    began = time.monotonic()
    tests = subprocess.run(argv, cwd=PYTHON, env=env, text=True, capture_output=True, timeout=120)
    result["focused_tests"] = {"argv": argv, "cwd": str(PYTHON), "timeout_seconds": 120,
        "environment_overrides": {k: env[k] for k in ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "TMPDIR", "XDG_RUNTIME_DIR", "BATON_V12_STACK_DISTRO", "BATON_V12_STACK_PACKAGING_REQUIRED")},
        "returncode": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr,
        "seconds": time.monotonic() - began}
    # Fail at the first status after both mock starts. Nothing real is launched.
    spec = importlib.util.spec_from_file_location("retained_lifecycle", D / "LIFECYCLE-HARNESS-187015.py")
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    calls = []
    def fake_stack(root, verb, *args):
        calls.append([str(root), verb])
        if verb == "status":
            raise subprocess.TimeoutExpired(["mock-stack", verb], 300)
        return {"exit": 0, "stdout": []}
    with mock.patch.object(harness, "run", return_value={"stdout": ["{}"], "exit": 0}), mock.patch.object(harness, "stack", side_effect=fake_stack):
        try:
            harness.main()
        except subprocess.TimeoutExpired:
            result["mock_lifecycle_timeout"] = {"timeout_escaped": True, "calls": calls,
                "stop_calls": sum(call[1] == "stop" for call in calls),
                "actual_stack_started": False}
        else:
            raise AssertionError("expected injected timeout")
    assert result["mock_lifecycle_timeout"]["stop_calls"] == 0
    pids = ["3899018", "3899019", "3899023", "3899024"]
    check = subprocess.run(["ps", "-o", "pid=,stat=,args=", "-p", ",".join(pids)], text=True, capture_output=True, timeout=10)
    result["author_reported_pid_check"] = {"pids": pids, "returncode": check.returncode, "stdout": check.stdout, "stderr": check.stderr}
    result["scratch_retained"] = str(scratch)
    result["seconds_including_hash_audit"] = time.monotonic() - started
    result["limits"] = "No rebuild, actual installed lifecycle rerun, credential/store read, provider/engine/Job, Git mutation, product/test edit or external-root write. Mock timeout proves missing cleanup invocation, not an observed live process leak."
    (D / "REVIEW-EVIDENCE-187086.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tests_returncode": tests.returncode, "test_summary": tests.stderr.splitlines()[-4:], "artifact_source_mismatches": result["artifact_source_mismatches"], "mock_timeout": result["mock_lifecycle_timeout"], "pid_check": result["author_reported_pid_check"], "seconds": result["seconds_including_hash_audit"], "scratch": str(scratch)}, indent=2))
    assert tests.returncode == 0


if __name__ == "__main__":
    main()
