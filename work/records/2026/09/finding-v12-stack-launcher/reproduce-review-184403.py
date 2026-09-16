"""Candidate review: focused regressions and owned process-boundary checks."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
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
    evidence = {"claim": 184403, "scope": "focused deterministic local tests, owned sleeper stand-ins; no deployed manager, provider, engine or v11 operation"}
    manifest = Path(__file__).with_name("EVIDENCE-184239.json")
    evidence["author_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    evidence["hashes"] = [{"path": p, "expected": h, "actual": hashlib.sha256((REPO / p).read_bytes()).hexdigest()} for p, h in json.loads(manifest.read_text())["candidates"].items()]
    assert all(r["expected"] == r["actual"] for r in evidence["hashes"])
    suite = unittest.TestSuite()
    for name, case in vars(test_stack).items():
        if isinstance(case, type) and issubclass(case, unittest.TestCase) and case.__module__ == test_stack.__name__ and name not in ("Fixture", "ValidIdleComposition"):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    output = io.StringIO()
    before = time.monotonic()
    result = unittest.TextTestRunner(stream=output).run(suite)
    evidence["stack_tests"] = {"count": result.testsRun, "success": result.wasSuccessful(), "seconds": time.monotonic() - before, "output": output.getvalue()}
    evidence["composition_not_run"] = "Two ValidIdleComposition cases need disk-backed external storage; /tmp is tmpfs and /var/tmp is outside reviewer write authority. Author evidence retained separately."
    modules = ["tests.job_manager.test_tool", "tests.job_manager.test_recovery", "tests.tools.test_job_viewer", "tests.tools.test_stage_execution_status_hardening"]
    output = io.StringIO()
    before = time.monotonic()
    result = unittest.TextTestRunner(stream=output).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
    evidence["adjacent_tests"] = {"modules": modules, "count": result.testsRun, "success": result.wasSuccessful(), "seconds": time.monotonic() - before, "output": output.getvalue()}
    children = []
    real_spawn, real_write = stack._spawn, stack.write_record
    with tempfile.TemporaryDirectory(prefix="w184403-review-") as tmp:
        root = Path(tmp)
        config = root / "deployment.json"
        config.write_text("{}")
        env = dict(os.environ, BATON_V12_JOB_STORE=str(root / "jobs"), BATON_V12_CONTROL_STORE=str(root / "control"), BATON_V12_AUTHORITY_UUID="0" * 32, BATON_V12_STAGE_EXECUTION_CONFIG=str(config))
        def sleeper(where, name):
            where.mkdir(exist_ok=True)
            record = real_spawn(where, name, [sys.executable, "-c", "import time; time.sleep(30)"], env)
            children.extend(c for c in stack._ADMITTED if c.pid == record["pid"])
            return record
        def publish(where):
            stack.snapshot_path(where).write_text(json.dumps({"schema": stack.STATUS_SCHEMA, "canonical": True, "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "jobs": []}))
        try:
            where = root / "second-record-write"
            writes = []
            def failing_write(where, name, record):
                writes.append(name)
                if len(writes) == 2:
                    raise OSError("injected incarnation record update failure")
                return real_write(where, name, record)
            output = io.StringIO()
            try:
                with mock.patch.object(stack, "_spawn", lambda where, name, argv, env: sleeper(where, name)), mock.patch.object(stack, "write_record", failing_write):
                    stack.start(where, env, stream=output, ready_seconds=0.1)
            except OSError as failure:
                record = stack.read_record(where, stack.MANAGER)
                evidence["manager_incarnation_write_failure"] = {"error": str(failure), "writes": writes, "manager_live": stack.alive(record), "record_has_incarnation": "incarnation" in record, "output": output.getvalue()}
            assert evidence["manager_incarnation_write_failure"]["manager_live"]
            for publisher_present in (True, False):
                where = root / ("both-already-live" if publisher_present else "publisher-replacement")
                manager = sleeper(where, stack.MANAGER)
                manager["incarnation"] = "admitted-but-not-initialized"
                real_write(where, stack.MANAGER, manager)
                if publisher_present:
                    sleeper(where, stack.PUBLISHER)
                publish(where)
                output = io.StringIO()
                def publisher_spawn(where, name, argv, env):
                    assert name == stack.PUBLISHER
                    record = sleeper(where, name)
                    publish(where)
                    return record
                with mock.patch.object(stack, "_spawn", publisher_spawn):
                    code = stack.start(where, env, stream=output, ready_seconds=0.1)
                evidence[where.name] = {"returncode": code, "manager_acknowledged": stack.acknowledged(manager), "serving_status": stack.observe(where, environ=env)["processes"][stack.MANAGER]["serving"], "output": output.getvalue()}
                assert code == 0 and not stack.acknowledged(manager)
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=2)
                except Exception:
                    child.kill()
                    child.wait(timeout=2)
                stack._collect(child.pid)
            evidence["all_reviewer_children_reaped"] = all(c.poll() is not None for c in children)
    evidence["total_seconds"] = time.monotonic() - began
    target = Path(__file__).with_name("REVIEW-EVIDENCE-184403.json")
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"stack": evidence["stack_tests"], "adjacent": evidence["adjacent_tests"], "seconds": evidence["total_seconds"], "evidence": str(target)}))

if __name__ == "__main__":
    run()
