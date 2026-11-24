#!/usr/bin/python3
"""The REAL provider CLI against a scripted endpoint, with the command supervisor as its shell prefix.

W385695 C5 (review 2026-11-24T03-03-48Z, item 5). One program, run where the CLI is: inside the provider
image by `qualify-w385695.sh cli-in-image` (no network; the endpoint is on the container's own loopback), or on
a host against a named CLI binary. It starts `stub.py`, runs ONE print turn of the CLI over six scripted
shell-tool commands, and answers a single JSON document with what it observed and a verdict.

No model, no credential, no instance. The key it passes is a placeholder the scripted endpoint never reads.
Standard library only.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

COMMANDS = [
    {"command": "echo ordinary; exit 3", "description": "ordinary exit status"},
    {"command": "sleep 300; echo never", "description": "over the bound", "timeout": 600000},
    {"command": "setsid nohup sleep 301 >/dev/null 2>&1 & echo started-detached", "description": "detached descendant"},
    {"command": "sleep 302", "description": "background task", "run_in_background": True},
    {"command": "sleep 303", "description": "moved to the background by the CLI's own window", "timeout": 2000},
    {"command": "sleep 8; echo observed", "description": "outlast every earlier bound"},
]
BOUND = 4


def survivors():
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            argv = open(f"/proc/{name}/cmdline", "rb").read().split(b"\0")
        except OSError:
            continue
        if argv[:1] == [b"sleep"] and argv[1:2] and argv[1].startswith(b"30"):
            found.append(int(name))
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stub", required=True)
    parser.add_argument("--supervisor", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--claude", default="claude")
    taken = parser.parse_args()
    work = os.path.abspath(taken.work)
    # THE PREFIX IS ONE ABSOLUTE EXECUTABLE PATH. The CLI runs it from its own working directory, and a prefix
    # it cannot execute makes every command fail -- which this check then reports as a failure, as it should.
    taken.supervisor = os.path.abspath(taken.supervisor)
    for name in ("home", "cwd", "tmp", "ledger"):
        os.makedirs(os.path.join(work, name))
    script = os.path.join(work, "script.json")
    json.dump(COMMANDS, open(script, "w"))
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    api = os.path.join(work, "api.log")
    stub = subprocess.Popen([sys.executable, taken.stub, str(port), script, api],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    answer = {"verdict": "fail", "why": []}
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                socket.create_connection(("127.0.0.1", port), timeout=1).close()
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise RuntimeError("the scripted endpoint did not start")
                time.sleep(0.1)
        base = {"HOME": os.path.join(work, "home"), "PATH": "/usr/local/bin:/usr/bin:/bin",
                "TMPDIR": os.path.join(work, "tmp")}
        version = subprocess.run([taken.claude, "--version"], env=base, capture_output=True, text=True, timeout=60)
        answer["cli_version"] = version.stdout.split()[0] if version.stdout.split() else None
        answer["supervisor_sha256"] = hashlib.sha256(open(taken.supervisor, "rb").read()).hexdigest()
        ran = subprocess.run(
            [taken.claude, "--print", "--dangerously-skip-permissions", "--output-format", "json",
             "run the scripted commands"],
            cwd=os.path.join(work, "cwd"), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240,
            env=dict(base, ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}", ANTHROPIC_API_KEY="stub-not-a-credential",
                     CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", DISABLE_AUTOUPDATER="1",
                     CLAUDE_CODE_SHELL_PREFIX=taken.supervisor, BATON_COMMAND_SECONDS=str(BOUND),
                     BATON_COMMAND_DEADLINE=repr(time.monotonic() + 600),
                     BATON_COMMAND_LEDGER=os.path.join(work, "ledger"),
                     BASH_DEFAULT_TIMEOUT_MS=str(BOUND * 1000), BASH_MAX_TIMEOUT_MS="900000"))
        answer["cli_exit"] = ran.returncode
        results = []
        for line in open(api):
            entry = json.loads(line)
            if "results" in entry:
                results = entry["results"]
        answer["tool_results"] = [one[:160] for one in results]
        names = os.listdir(os.path.join(work, "ledger"))
        records = [json.load(open(os.path.join(work, "ledger", one))) for one in sorted(names) if one.endswith(".json")]
        answer["ledger"] = {"started": len([one for one in names if one.endswith(".started")]), "finished": len(records),
                            "timed_out": len([one for one in records if one["outcome"] == "timed-out"]),
                            "descendants_gone": all(one["descendants_gone"] is True for one in records),
                            "bounds": sorted({one["seconds_bound"] for one in records})}
        time.sleep(1)
        answer["survivors"] = survivors()
        checks = {
            "the CLI ended its turn cleanly": ran.returncode == 0,
            "every scripted command was answered": len(results) == len(COMMANDS),
            "every command went through the supervisor, start and finish": answer["ledger"]["started"] == answer["ledger"]["finished"] == len(COMMANDS),
            "an ordinary command kept its own status": len(results) > 0 and "Exit code 3" in results[0],
            "a command over the bound was ended at it": len(results) > 1 and "Exit code 124" in results[1] and f"ended at its {BOUND}s bound" in results[1],
            "a detached descendant's command still answered": len(results) > 2 and "started-detached" in results[2],
            "at least the over-bound and the background command timed out": answer["ledger"]["timed_out"] >= 2,
            "every supervisor saw its descendants gone": answer["ledger"]["descendants_gone"],
            "the selected bound is the one each supervisor used": answer["ledger"]["bounds"] == [BOUND],
            "no scripted process survived": answer["survivors"] == [],
        }
        answer["checks"] = checks
        answer["why"] = [name for name, held in checks.items() if not held]
        answer["verdict"] = "pass" if not answer["why"] else "fail"
    except Exception as failed:                                   # noqa: BLE001 -- reported, never swallowed
        answer["why"].append(f"{type(failed).__name__}: {failed}")
    finally:
        stub.kill()
        stub.wait()
        for pid in survivors():
            try:
                os.kill(pid, 9)
            except OSError:
                pass
    print(json.dumps(answer, indent=1, sort_keys=True))
    return 0 if answer["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
