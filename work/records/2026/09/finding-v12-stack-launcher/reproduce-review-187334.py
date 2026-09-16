"""Focused W183883 mixed-ownership review. No real stack or Git operation."""
import contextlib
import hashlib
import importlib.util
import io
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
sys.dont_write_bytecode = True


def run_case(scratch, mode):
    spec = importlib.util.spec_from_file_location("retained", D / "LIFECYCLE-HARNESS-187303.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.LIVE = scratch / mode
    h.A, h.B = h.LIVE / "deployment", h.LIVE / "deployment-b"
    h.INJECT = None
    for root in (h.A, h.B):
        (root / "db").mkdir(parents=True)
        (root / "instance.json").write_text("{}")
    states = {h.A: "absent", h.B: "absent"}
    if mode in ("a-running", "both-running"):
        states[h.A] = "running"
    if mode in ("b-running", "both-running"):
        states[h.B] = "running"
    if mode == "b-unknown":
        states[h.B] = "unknown"
    pids = {h.A: (810001, 810002), h.B: (810003, 810004)}
    calls, corrupted = [], []

    def fake_run(argv, **kwargs):
        args = [str(a) for a in argv]
        verb = args[1]
        root = h.B if args[0].startswith(str(h.B)) else h.A
        calls.append({"root": str(root), "verb": verb, "argv": args})
        if verb == "identity":
            return subprocess.CompletedProcess(args, 0, "{}", "")
        if verb == "bootstrap":
            if mode == "preservation":
                (h.A / "instance.json").write_text('{"changed":true}')
            return subprocess.CompletedProcess(args, 2, "refused", "")
        if root == h.A and str(h.B / "instance.json") in args:
            return subprocess.CompletedProcess(args, 2, "refused", "")
        if (root / "instance.json").read_bytes() == b"{ not a document":
            corrupted.append(str(root))
            return subprocess.CompletedProcess(args, 2, "refused", "")
        if verb == "status":
            output = "\n".join(name + " " + states[root] + (" pid " + str(pid) if states[root] == "running" else "") for name, pid in zip(("manager", "publisher"), pids[root]))
            return subprocess.CompletedProcess(args, 0, output, "")
        if verb == "start":
            states[root] = "running"
            if mode == "b-start-timeout" and root == h.B:
                raise subprocess.TimeoutExpired(args, 300)
            output = "\n".join(f"started: {name} pid {pid}" for name, pid in zip(("manager", "publisher"), pids[root]))
            return subprocess.CompletedProcess(args, 0, output, "")
        if verb == "stop":
            states[root] = "absent"
        return subprocess.CompletedProcess(args, 0, "mock output", "")

    out = io.StringIO()
    with mock.patch.object(h.subprocess, "run", side_effect=fake_run), mock.patch.object(h.time, "sleep"), contextlib.redirect_stdout(out):
        code = h.main()
    output = json.loads(out.getvalue())
    return {"exit": code, "output": output, "calls": calls, "corrupted_selectors_seen": corrupted,
            "stop_calls": [c["root"] for c in calls if c["verb"] == "stop"]}


def main():
    began = time.monotonic()
    author = json.loads((D / "EVIDENCE-187303.json").read_text())
    previous = json.loads((D / "EVIDENCE-187223.json").read_text())
    assert author["candidates"] == previous["candidates"]
    hashes = {}
    for path, wanted in author["candidates"].items():
        hashes[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert hashes[path] == wanted, path
    scratch = Path(tempfile.mkdtemp(prefix="w183883-review187334-", dir="/tmp"))
    cases = {mode: run_case(scratch, mode) for mode in ("positive", "both-running", "preservation", "a-running", "b-running", "b-unknown", "b-start-timeout")}
    lifecycle = json.loads((D / "LIFECYCLE-187303.json").read_text())
    pids = [str(pid) for group in lifecycle["record"]["cleanup"]["owned_pids"].values() for pid in group.values()]
    checked = subprocess.run(["ps", "-o", "pid=,stat=,args=", "-p", ",".join(pids)], capture_output=True, text=True, timeout=10)
    result = {"claim": 187334, "candidate_hashes": hashes, "cases": cases, "scratch_retained": str(scratch),
              "seconds": time.monotonic() - began, "reported_pid_check": {"pids": pids, "exit": checked.returncode, "stdout": checked.stdout, "stderr": checked.stderr},
              "limits": "Actual retained harness with simulated subprocess results and ordinary local files; no real stack, Git, provider, engine or Job. Unchanged product/packaging acceptance reused."}
    (D / "REVIEW-EVIDENCE-187334.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"seconds": result["seconds"], "scratch": str(scratch), "pid_check": result["reported_pid_check"], "cases": {m: {"exit": c["exit"], "claimed": c["output"]["record"]["cleanup"]["claimed"], "stops": c["stop_calls"], "corruptions": c["corrupted_selectors_seen"]} for m, c in cases.items()}}, indent=2))
    assert cases["positive"]["exit"] == 0
    assert cases["preservation"]["exit"] == 2
    assert cases["both-running"]["stop_calls"] == []
    assert any(x.endswith("deployment-b") for x in cases["b-running"]["stop_calls"])
    assert any(x.endswith("deployment-b") for x in cases["b-running"]["corrupted_selectors_seen"])


if __name__ == "__main__":
    main()
