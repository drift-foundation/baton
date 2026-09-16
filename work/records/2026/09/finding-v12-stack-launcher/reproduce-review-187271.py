"""Review W183883 without real lifecycle/Git/Job operations.

Product hashes/bundles are read; lifecycle subprocesses and /proc reads are
simulated around the actual retained harness, using ordinary scratch files.
The author packet proof runs its own stubbed Git boundary and temporary dirs.
"""
import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
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
from baton_v12.worker_manager import source_boundary


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def lifecycle_case(scratch, mode):
    spec = importlib.util.spec_from_file_location("retained", D / "LIFECYCLE-HARNESS-187223.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.LIVE = scratch / mode
    h.A, h.B = h.LIVE / "deployment", h.LIVE / "deployment-b"
    h.INJECT = None
    for root in (h.A, h.B):
        (root / "db").mkdir(parents=True)
        (root / "instance.json").write_text("{}")
    library = h.B / "distro/_internal/libpython3.13.so.1.0"
    library.parent.mkdir(parents=True)
    original = b"ordinary fixture bytes, never mapped as a library"
    library.write_bytes(original)
    calls, tamper, timeouts = [], [], []
    pidsets = {h.A: [810001, 810002], h.B: [810003, 810004]}
    live = {pid: mode == "already-running" for group in pidsets.values() for pid in group}
    original_open = builtins.open

    def fake_open(file, *args, **kwargs):
        path = str(file)
        if path.startswith("/proc/") and path.endswith("/stat"):
            pid = int(path.split("/")[2])
            if mode == "proc-unreadable":
                raise PermissionError("injected process identity read failure")
            if not live.get(pid, False):
                raise FileNotFoundError(path)
            return io.BytesIO((str(pid) + " (mock-worker) S 0 0 0\n").encode())
        return original_open(file, *args, **kwargs)

    def fake_run(argv, **kwargs):
        args = [str(a) for a in argv]
        calls.append(args)
        verb = args[1]
        root = h.B if args[0].startswith(str(h.B)) else h.A
        if library.read_bytes() != original:
            tamper.append({"verb": verb, "live_pids": [p for p, islive in live.items() if islive]})
        if verb == "identity":
            return subprocess.CompletedProcess(args, 0, "{}", "")
        bad_runtime = root == h.B and library.read_bytes() != original
        cross = root == h.A and str(h.B / "instance.json") in args
        corrupt = (root / "instance.json").read_bytes() == b"{ not a document"
        if verb == "bootstrap":
            if mode == "preservation-failure":
                (h.A / "instance.json").write_text('{"changed":true}')
            return subprocess.CompletedProcess(args, 2, "refused", "")
        if cross or corrupt or bad_runtime:
            return subprocess.CompletedProcess(args, 2, "refused", "")
        if verb == "start":
            for pid in pidsets[root]:
                live[pid] = True
            prefix = "already running" if mode == "already-running" else "started"
            output = "\n".join(f"{prefix}: {name} pid {pid}" for name, pid in zip(("manager", "publisher"), pidsets[root]))
            if mode == "start-timeout":
                raise subprocess.TimeoutExpired(args, 300, output=output.encode())
            return subprocess.CompletedProcess(args, 0, output, "")
        if verb == "stop":
            if mode == "stop-oserror":
                raise FileNotFoundError("injected stop unavailable")
            if mode in ("already-running", "start-timeout", "proc-unreadable"):
                return subprocess.CompletedProcess(args, 2, "stop failed", "")
            for pid in pidsets[root]:
                live[pid] = False
        if verb == "status" and mode == "status-timeout" and not timeouts:
            timeouts.append(True)
            raise subprocess.TimeoutExpired(args, 300)
        return subprocess.CompletedProcess(args, 0, "mock output", "")

    stream = io.StringIO()
    with mock.patch.object(h.subprocess, "run", side_effect=fake_run), mock.patch.object(h.time, "sleep"), mock.patch("builtins.open", side_effect=fake_open), contextlib.redirect_stdout(stream):
        result = h.main()
    return {"exit": result, "output": json.loads(stream.getvalue()), "calls": calls,
            "tamper": tamper, "simulated_live_at_end": [p for p, islive in live.items() if islive],
            "library_restored": library.read_bytes() == original}


def main():
    started = time.monotonic()
    author = json.loads((D / "EVIDENCE-187223.json").read_text())
    prior = json.loads((D / "EVIDENCE-187142.json").read_text())
    manifest = json.loads((D / "ARTIFACT-MANIFEST-187142.json").read_text())
    result = {"claim": 187271, "candidate_hashes": {}, "artifact_source_hashes": {}, "bundles": {}}
    assert author["candidates"] == prior["candidates"]
    for name, table in (("candidate_hashes", author["candidates"]), ("artifact_source_hashes", manifest["source"])):
        for path, digest in table.items():
            result[name][path] = sha(ROOT / path)
            assert result[name][path] == digest, path
    for path in [PYTHON / "build/out/distro"] + [Path(p) / "distro" for p in manifest["retained"]["destinations"]]:
        held = instance.manifest(path)
        assert held["digest"] == prior["the_artifact"]["digest"]
        result["bundles"][str(path)] = {k: held[k] for k in ("files", "digest")}
    scratch = Path(tempfile.mkdtemp(prefix="w183883-review187271-", dir="/tmp"))
    argv = [sys.executable, str(D / "PACKET-CHECK-PROOF-187223.py")]
    packet = subprocess.run(argv, text=True, capture_output=True, timeout=30,
                            env=dict(os.environ, TMPDIR=str(scratch), PYTHONDONTWRITEBYTECODE="1"))
    result["packet_proof"] = {"argv": argv, "exit": packet.returncode, "stderr": packet.stderr,
                              "result": json.loads(packet.stdout)}
    assert packet.returncode == 0
    assert result["packet_proof"]["result"]["every_bad_case_refuses"]
    result["harness_cases"] = {mode: lifecycle_case(scratch, mode) for mode in (
        "positive", "status-timeout", "stop-oserror", "already-running", "start-timeout", "proc-unreadable", "preservation-failure")}
    try:
        source_boundary.nominate_source(str(scratch / "unprepared-source"))
    except Exception as error:
        result["source_before_clone"] = {"type": type(error).__name__, "message": str(error)}
    else:
        raise AssertionError("absent source accepted")
    lifecycle = json.loads((D / "LIFECYCLE-187223.json").read_text())
    pids = sorted(lifecycle["record"]["cleanup"]["owned_pids"])
    checked = subprocess.run(["ps", "-o", "pid=,stat=,args=", "-p", ",".join(pids)], text=True, capture_output=True, timeout=10)
    result["reported_pid_check"] = {"pids": pids, "exit": checked.returncode, "stdout": checked.stdout, "stderr": checked.stderr}
    result["scratch_retained"] = str(scratch)
    result["seconds_including_audit"] = time.monotonic() - started
    (D / "REVIEW-EVIDENCE-187271.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"seconds": result["seconds_including_audit"], "scratch": str(scratch),
        "packet_good": result["packet_proof"]["result"]["the_good_case_passes"], "packet_bad_refused": result["packet_proof"]["result"]["every_bad_case_refuses"],
        "harness": {m: {"exit": v["exit"], "verdict": v["output"]["record"]["verdict"], "owned_pids": v["output"]["record"]["cleanup"].get("owned_pids"), "tampered_while_simulated_live": any(t["live_pids"] for t in v["tamper"])} for m, v in result["harness_cases"].items()},
        "source_before_clone": result["source_before_clone"], "pid_check": result["reported_pid_check"]}, indent=2))
    assert result["harness_cases"]["positive"]["exit"] == 0
    assert result["harness_cases"]["status-timeout"]["exit"] == 2
    assert result["harness_cases"]["stop-oserror"]["exit"] == 2
    assert result["harness_cases"]["preservation-failure"]["exit"] == 0


if __name__ == "__main__":
    main()
