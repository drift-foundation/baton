"""Focused review checks; only owned local sleepers and temporary files."""
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(REPO / "v12/python"), str(REPO / "v12/python/src")]
from tools import stack
from tests.tools import test_stack

def run():
    began = time.monotonic()
    evidence = {"claim": 184197, "scope": "deterministic local process checks; no live models, engines, Jobs or v11 operations"}
    manifest = Path(__file__).with_name("EVIDENCE-183998.json")
    evidence["author_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    evidence["hashes"] = [{"path": name, "expected": value, "actual": hashlib.sha256((REPO / name).read_bytes()).hexdigest()} for name, value in json.loads(manifest.read_text())["candidates"].items()]
    assert all(row["actual"] == row["expected"] for row in evidence["hashes"])
    suite = unittest.TestSuite()
    classes = [test_stack.Identity, test_stack.Configuration, test_stack.Lifecycle,
               test_stack.SpawnedArgv, test_stack.Status, test_stack.Publication,
               test_stack.Boundary, test_stack.Admission, test_stack.UnknownOwnership,
               test_stack.Readiness, test_stack.RuntimeBoundary]
    for case in classes:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    output = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    evidence["focused_tests"] = {"run": result.testsRun, "success": result.wasSuccessful(), "seconds": time.monotonic() - started, "output": output.getvalue()}
    evidence["composition_not_run"] = "The two ValidIdleComposition cases require disk-backed storage outside checkout. /tmp is tmpfs; /var/tmp and ~/.cache are outside this managed reviewer's writable roots. Author evidence retained; no permission workaround or escalation attempted."
    children = []
    with tempfile.TemporaryDirectory(prefix="w184197-review-") as tmp:
        root = Path(tmp)
        config = root / "deployment.json"
        config.write_text("{}")
        env = dict(os.environ, BATON_V12_JOB_STORE=str(root / "jobs.sqlite"), BATON_V12_CONTROL_STORE=str(root / "control.sqlite"), BATON_V12_AUTHORITY_UUID="0" * 32, BATON_V12_STAGE_EXECUTION_CONFIG=str(config))
        def owned_record(where):
            where.mkdir()
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(child)
            record = {"schema": stack.SCHEMA, "name": "manager", "pid": child.pid, "started_at": stack.started_at(child.pid)}
            stack.write_record(where, "manager", record)
            return child, record
        try:
            for action in ("stop", "unwind"):
                where = root / action
                child, record = owned_record(where)
                real_proc = stack._proc
                after_signal = [False]
                def lose_visibility(held, number):
                    after_signal[0] = True
                    return True
                def proc(pid):
                    return ("unknown", None) if after_signal[0] and pid == child.pid else real_proc(pid)
                output = io.StringIO()
                with mock.patch.object(stack, "_signal", lose_visibility), mock.patch.object(stack, "_proc", proc):
                    code = stack.stop(where, stream=output, grace=0.01) if action == "stop" else stack._unwind(where, [record], output)
                evidence[action + "_live_to_unknown"] = {"returncode": code, "child_alive": child.poll() is None, "record_retained": stack.read_record(where, "manager") is not None, "output": output.getvalue()}
                assert child.poll() is None and stack.read_record(where, "manager") is None
            where = root / "partial"
            real_spawn = stack._spawn
            def partial_spawn(root, name, argv, environ):
                if name == stack.PUBLISHER:
                    raise OSError("injected publisher spawn failure")
                record = real_spawn(root, name, [sys.executable, "-c", "import time; time.sleep(30)"], environ)
                children.extend(c for c in stack._ADMITTED if c.pid == record["pid"])
                return record
            output = io.StringIO()
            try:
                with mock.patch.object(stack, "_spawn", partial_spawn):
                    stack.start(where, env, stream=output, ready_seconds=0.1)
            except OSError as failure:
                evidence["partial_spawn_oserror"] = {"exception": str(failure), "manager_still_live": stack.alive(stack.read_record(where, "manager")), "publisher_record": stack.read_record(where, "publisher"), "output": output.getvalue()}
            assert evidence["partial_spawn_oserror"]["manager_still_live"]
            where = root / "malformed"
            where.mkdir()
            stack.snapshot_path(where).write_text(json.dumps({"jobs": [None]}))
            try:
                stack.runtime_boundary(where)
            except Exception as failure:
                evidence["malformed_snapshot"] = {"exception": type(failure).__name__, "detail": str(failure)}
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
                stack._collect(child.pid)
            evidence["all_reviewer_children_reaped"] = all(c.poll() is not None for c in children)
    evidence["total_seconds"] = time.monotonic() - began
    target = Path(__file__).with_name("REVIEW-EVIDENCE-184197.json")
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tests": evidence["focused_tests"], "seconds": evidence["total_seconds"], "evidence": str(target)}))

if __name__ == "__main__":
    run()
