"""W183883 focused review: read-only bundle audit, local tests and mock failures.

No real lifecycle commands, Git operations, stores, provider, engine or Job.
The operator check uses a shell function standing in for Git's read results.
Lifecycle subprocesses are mocked; all mutated files are scratch fixtures.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
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


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def harness_case(scratch, mode):
    spec = importlib.util.spec_from_file_location("review_lifecycle", D / "LIFECYCLE-HARNESS-187142.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.LIVE = scratch / mode
    h.A, h.B = h.LIVE / "a", h.LIVE / "b"
    h.INJECT = "after-starts" if mode == "after-starts" else None
    for root in (h.A, h.B):
        (root / "db").mkdir(parents=True)
        (root / "instance.json").write_text("{}")
    library = h.B / "distro/_internal/libpython3.13.so.1.0"
    library.parent.mkdir(parents=True)
    pristine = b"ordinary review fixture, not an executable"
    library.write_bytes(pristine)
    calls, tamper_seen, timed_out = [], [], []

    def fake_run(argv, **kwargs):
        args = [str(a) for a in argv]
        if args[0] == "bash":
            return subprocess.CompletedProcess(args, 0, "777\n" if mode == "stop-failure" else "", "")
        verb = args[1]
        calls.append(args)
        if verb == "identity":
            return subprocess.CompletedProcess(args, 0, "{}", "")
        root = h.A if args[0].startswith(str(h.A)) else h.B
        if library.read_bytes() != pristine:
            tamper_seen.append(verb)
        if mode == "status-timeout" and verb == "status" and not timed_out:
            timed_out.append(True)
            raise subprocess.TimeoutExpired(args, 300)
        if mode == "stop-oserror" and verb == "stop":
            raise FileNotFoundError("injected stop executable unavailable")
        code = 0
        if verb == "bootstrap" or (root == h.A and str(h.B / "instance.json") in args):
            code = 2
        if root == h.B and ((h.B / "instance.json").read_bytes() != b"{}" or library.read_bytes() != pristine):
            code = 2
        if mode == "stop-failure" and verb == "stop":
            code = 2
        return subprocess.CompletedProcess(args, code, "mock command result", "")

    out = io.StringIO()
    escaped = None
    returned = None
    with mock.patch.object(h.subprocess, "run", side_effect=fake_run), mock.patch.object(h.time, "sleep"), contextlib.redirect_stdout(out):
        try:
            returned = h.main()
        except Exception as exc:
            escaped = type(exc).__name__ + ": " + str(exc)
    result = {"exit": returned, "escaped": escaped, "calls": calls,
              "tamper_seen_at_commands": tamper_seen,
              "library_restored": library.read_bytes() == pristine,
              "selector_restored": (h.B / "instance.json").read_bytes() == b"{}",
              "output": json.loads(out.getvalue()) if out.getvalue() else None}
    return result


def packet_case(scratch, mode):
    text = (D / "OPERATOR-INDEPENDENT-REPOSITORY.md").read_text()
    block = text.split("```sh\n#!/usr/bin/env bash\n", 1)[1].split("```", 1)[0]
    root = scratch / ("packet-" + mode)
    target, workspace, source = (root / part for part in ("target", "workspace", "source"))
    for p in (target, workspace, source):
        p.mkdir(parents=True)
    substitutions = {"TARGET": shlex.quote(str(target)), "WORKSPACE": shlex.quote(str(workspace)),
                     "BASE": "a" * 40, "REFERENCE": "refs/heads/main", "SOURCES": "(" + shlex.quote(str(source)) + ")"}
    for name, value in substitutions.items():
        block = re.sub(r"^" + name + r"=.*$", name + "=" + value, block, flags=re.M)
    # Explicit boundary simulation: these directories are not Git repositories.
    shim = '''
git () {
  case "$3" in
    rev-parse) if [ "$4" = --verify ]; then printf '%s\\n' aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; else printf '%s/.git\\n' "$2"; fi ;;
    cat-file|remote|count-objects) return 0 ;;
    *) return 99 ;;
  esac
}
'''
    if mode == "workspace-stat-error":
        shim += '''stat () { if [ "$3" = "$WORKSPACE" ]; then echo 'injected stat failure' >&2; return 7; else command stat "$@"; fi; }
'''
    if mode == "workspace-alternates":
        alternates = workspace / ".git/objects/info/alternates"
        alternates.parent.mkdir(parents=True)
        alternates.write_text("/borrowed/development/object/store\n")
    block = block.replace("identity ()", shim + "\nidentity ()", 1)
    script = root / "check.sh"
    script.write_text(block)
    done = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=10)
    return {"script": str(script), "exit": done.returncode, "stdout": done.stdout, "stderr": done.stderr,
            "git_boundary": "simulated read responses; no actual Git operation or repository creation"}


def main():
    started = time.monotonic()
    author = json.loads((D / "EVIDENCE-187142.json").read_text())
    manifest = json.loads((D / "ARTIFACT-MANIFEST-187142.json").read_text())
    result = {"claim": 187184, "candidate_hashes": {}, "artifact_source_hashes": {}, "bundles": {}}
    for key, table in (("candidate_hashes", author["candidates"]), ("artifact_source_hashes", manifest["source"])):
        for path, digest in table.items():
            result[key][path] = sha(ROOT / path)
            assert result[key][path] == digest, (key, path)
    distro = PYTHON / "build/out/distro"
    for path in [distro] + [Path(p) / "distro" for p in manifest["retained"]["destinations"]]:
        held = instance.manifest(path)
        assert held["digest"] == author["the_artifact"]["digest"]
        result["bundles"][str(path)] = {k: held[k] for k in ("files", "digest")}
    result["build_log_sha256"] = sha(D / manifest["build"]["log"])
    assert result["build_log_sha256"] == manifest["build"]["log_sha256"]
    scratch = Path(tempfile.mkdtemp(prefix="w183883-review187184-", dir="/tmp"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="src:.", TMPDIR=str(scratch),
               BATON_V12_STACK_DISTRO=str(distro), BATON_V12_STACK_PACKAGING_REQUIRED="1")
    argv = [sys.executable, "-m", "unittest", "tests.tools.test_stack.WhatTheRepositoryIS", "tests.tools.test_packaging"]
    began = time.monotonic()
    done = subprocess.run(argv, cwd=PYTHON, env=env, capture_output=True, text=True, timeout=60)
    result["tests"] = {"argv": argv, "cwd": str(PYTHON), "timeout_seconds": 60, "exit": done.returncode,
                       "stdout": done.stdout, "stderr": done.stderr, "seconds": time.monotonic() - began,
                       "environment_overrides": {k: env[k] for k in ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "TMPDIR", "BATON_V12_STACK_DISTRO", "BATON_V12_STACK_PACKAGING_REQUIRED")}}
    result["harness_cases"] = {mode: harness_case(scratch, mode) for mode in ("positive", "after-starts", "status-timeout", "stop-failure", "stop-oserror")}
    result["packet_cases"] = {mode: packet_case(scratch, mode) for mode in ("positive", "workspace-stat-error", "workspace-alternates")}
    lifecycle = json.loads((D / "LIFECYCLE-187142.json").read_text())
    proof = json.loads((D / "CLEANUP-PROOF-187142.json").read_text())
    pids = sorted(set(re.findall(r"(?:manager|publisher) pid (\d+)", json.dumps([lifecycle, proof]))))
    checked = subprocess.run(["ps", "-o", "pid=,stat=,args=", "-p", ",".join(pids)], text=True, capture_output=True, timeout=10)
    result["reported_pid_check"] = {"pids": pids, "exit": checked.returncode, "stdout": checked.stdout, "stderr": checked.stderr}
    result["seconds_including_audit"] = time.monotonic() - started
    result["scratch_retained"] = str(scratch)
    (D / "REVIEW-EVIDENCE-187184.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"tests": result["tests"], "harness_summary": {m: {k: v[k] for k in ("exit", "escaped", "library_restored", "selector_restored")} for m, v in result["harness_cases"].items()}, "packet_cases": result["packet_cases"], "pid_check": result["reported_pid_check"], "seconds": result["seconds_including_audit"], "scratch": str(scratch)}, indent=2))
    assert done.returncode == 0
    assert result["harness_cases"]["positive"]["exit"] == 0
    assert result["harness_cases"]["after-starts"]["exit"] == 2
    assert result["harness_cases"]["status-timeout"]["exit"] == 0
    assert result["harness_cases"]["stop-failure"]["exit"] == 0
    assert result["harness_cases"]["stop-oserror"]["escaped"].startswith("FileNotFoundError")
    assert all(c["exit"] == 0 for c in result["packet_cases"].values())


if __name__ == "__main__":
    main()
