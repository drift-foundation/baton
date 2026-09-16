"""Bounded reviewer checks: disposable files, owned sleepers, invalid config only."""
import concurrent.futures
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from unittest import mock

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "v12/python"))
from tools import stack

def run():
    began = time.monotonic()
    evidence = {"claim": 183958, "scope": "focused deterministic verification; no live providers, engines, or v11 operations"}
    manifest_path = Path(__file__).with_name("EVIDENCE-183891.json")
    evidence["author_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    evidence["candidate_checks"] = [{**one, "actual": hashlib.sha256((REPO / one["path"]).read_bytes()).hexdigest()} for one in json.loads(manifest_path.read_text())["files"]]
    assert all(one["sha256"] == one["actual"] for one in evidence["candidate_checks"])
    start = time.monotonic()
    tests = subprocess.run([sys.executable, "-m", "unittest", "tests.tools.test_stack"], cwd=REPO / "v12/python", capture_output=True, text=True, timeout=30)
    evidence["author_tests"] = {"returncode": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr, "seconds": time.monotonic() - start}
    children = []
    original_popen = subprocess.Popen
    lock = threading.Lock()
    with tempfile.TemporaryDirectory(prefix="w183958-review-") as tmp:
        root = Path(tmp)
        config = root / "deployment.json"
        config.write_text("{}")
        env = dict(os.environ, BATON_V12_JOB_STORE=str(root / "jobs.sqlite"), BATON_V12_CONTROL_STORE=str(root / "control.sqlite"), BATON_V12_AUTHORITY_UUID="0" * 32, BATON_V12_STAGE_EXECUTION_CONFIG=str(config))
        def sleeper():
            child = original_popen([sys.executable, "-c", "import time; time.sleep(30)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(child)
            return child
        def fake_spawn(where, name, argv, environ):
            with lock:
                child = sleeper()
                record = {"schema": stack.SCHEMA, "name": name, "pid": child.pid, "started_at": stack.started_at(child.pid)}
                stack.write_record(where, name, record)
                return record
        def reap():
            for child in children:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
        try:
            concurrent_root = root / "concurrent"
            barrier = threading.Barrier(2, timeout=3)
            spawned_names = []
            def racing_spawn(where, name, argv, environ):
                if name == stack.MANAGER:
                    barrier.wait()
                result = fake_spawn(where, name, argv, environ)
                spawned_names.append(name)
                return result
            with mock.patch.object(stack, "_spawn", racing_spawn):
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(stack.start, concurrent_root, env, stream=io.StringIO()) for _ in range(2)]
                    codes = [future.result(timeout=5) for future in futures]
            evidence["concurrent_start"] = {"returncodes": codes, "spawned_names": sorted(spawned_names), "live_children": sum(c.poll() is None for c in children), "retained_records": len(list(concurrent_root.glob("*.json")))}
            assert sorted(spawned_names) == ["manager", "manager", "publisher", "publisher"]
            reap()
            unknown_root = root / "unknown"
            unknown_root.mkdir()
            original = sleeper()
            (unknown_root / "manager.json").write_text("{ unreadable")
            output = io.StringIO()
            with mock.patch.object(stack, "_spawn", fake_spawn):
                code = stack.start(unknown_root, env, stream=output)
            evidence["unreadable_record_start"] = {"returncode": code, "original_process_still_alive": original.poll() is None, "replacement_pid": stack.read_record(unknown_root, "manager")["pid"], "original_pid": original.pid, "output": output.getvalue()}
            assert original.poll() is None and stack.read_record(unknown_root, "manager")["pid"] != original.pid
            reap()
            invalid_root = root / "invalid"
            def tracked_popen(*args, **kwargs):
                child = original_popen(*args, **kwargs)
                children.append(child)
                return child
            output = io.StringIO()
            with mock.patch.object(subprocess, "Popen", tracked_popen):
                code = stack.start(invalid_root, env, stream=output)
            deadline = time.monotonic() + 5
            while stack.alive(stack.read_record(invalid_root, "manager")) and time.monotonic() < deadline:
                time.sleep(0.02)
            evidence["invalid_configuration_start"] = {"returncode": code, "output": output.getvalue(), "status": stack.observe(invalid_root, environ=env), "manager_log": (invalid_root / "manager.log").read_text()}
            assert not stack.alive(stack.read_record(invalid_root, "manager"))
            stop_out = io.StringIO()
            evidence["invalid_configuration_stop_code"] = stack.stop(invalid_root, stream=stop_out, grace=0.2)
            evidence["invalid_configuration_stop_output"] = stop_out.getvalue()
        finally:
            reap()
            evidence["all_owned_children_reaped"] = all(c.poll() is not None for c in children)
    evidence["total_seconds"] = time.monotonic() - began
    target = Path(__file__).with_name("REVIEW-EVIDENCE-183958.json")
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"evidence": str(target), "seconds": evidence["total_seconds"], "tests": tests.returncode, "children_reaped": evidence["all_owned_children_reaped"]}))

if __name__ == "__main__":
    run()
