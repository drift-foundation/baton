"""Unprivileged deterministic resident for the future authorized mount proof.

Runs as one process with stdio control and cwd outside /output. Commands are
fixed fixture operations, not a shell. A completion reply is deliberately NOT
a detach receipt; only the trusted controller may authorize consumption.
"""

import json
import ctypes
import os
from pathlib import Path
import sys
import time

WORKSPACE = Path("/output")
PAYLOAD = WORKSPACE / "rounds.txt"
os.chdir("/tmp")
os.umask(0o002)
session_nonce = os.urandom(16).hex()  # Fixture continuity marker, not a credential.
completed_rounds = 0
held_file = None


def facts():
    mounts = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        before, _, after = line.partition(" - ")
        fields = before.split()
        if fields[4] == str(WORKSPACE):
            mounts.append({"id": fields[0], "parent": fields[1], "device": fields[2],
                           "root": fields[3], "options": fields[5],
                           "propagation": fields[6:], "filesystem": after.split()[0]})
    return {"pid": os.getpid(), "session_nonce": session_nonce,
            "rounds": completed_rounds, "cwd": os.getcwd(), "mounts": mounts,
            "uid": os.getuid(), "gid": os.getgid(), "groups": os.getgroups(),
            "monotonic_ns": time.monotonic_ns()}


def emit(result):
    print(json.dumps({**facts(), **result}, sort_keys=True), flush=True)


emit({"event": "ready"})
for raw in sys.stdin:
    command = raw.strip()
    try:
        if command in ("write-1", "write-2"):
            requested = int(command[-1])
            if requested != completed_rounds + 1 or held_file is not None:
                raise ValueError("round order or retained handle")
            with PAYLOAD.open("a", encoding="utf-8") as handle:
                handle.write(f"round {requested}\n")
                handle.flush()
                os.fsync(handle.fileno())
            completed_rounds = requested
            emit({"event": "written", "workspace_identity": [WORKSPACE.stat().st_dev, WORKSPACE.stat().st_ino]})
        elif command == "complete":
            if held_file is not None:
                held_file.close()
                held_file = None
            os.chdir("/tmp")
            emit({"event": "completion-declared", "busy_fixture": False})
        elif command == "declare-with-open-file":
            if held_file is not None:
                raise ValueError("already holding a file")
            held_file = PAYLOAD.open("a", encoding="utf-8")
            emit({"event": "completion-declared", "busy_fixture": "open-file"})
        elif command == "declare-with-workspace-cwd":
            os.chdir(WORKSPACE)
            emit({"event": "completion-declared", "busy_fixture": "cwd"})
        elif command == "probe":
            try:
                descriptor = os.open(PAYLOAD, os.O_WRONLY | os.O_APPEND)
            except OSError as error:
                emit({"event": "access-probe", "writable": False, "errno": error.errno})
            else:
                os.close(descriptor)
                emit({"event": "access-probe", "writable": True})
        elif command == "security-probe":
            # A disposable child probes the actual cap/seccomp posture. If an
            # operation unexpectedly succeeds the host must abort and stop.
            read_end, write_end = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(read_end)
                libc = ctypes.CDLL(None, use_errno=True)
                libc.mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                                       ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p]
                libc.mount.restype = ctypes.c_int
                libc.unshare.argtypes = [ctypes.c_int]
                libc.unshare.restype = ctypes.c_int
                mounted = libc.mount(None, b"/output", None, 32 | 4096, None)
                mount_errno = ctypes.get_errno() if mounted == -1 else 0
                unshared = libc.unshare(0x10000000 | 0x00020000)
                unshare_errno = ctypes.get_errno() if unshared == -1 else 0
                os.write(write_end, json.dumps(
                    {"mount_errno": mount_errno, "unshare_errno": unshare_errno}).encode())
                os._exit(0)
            os.close(write_end)
            result = json.loads(os.read(read_end, 1024))
            os.close(read_end)
            _, status = os.waitpid(child, 0)
            if os.waitstatus_to_exitcode(status) != 0:
                raise ValueError("security probe child failed")
            posture = dict(line.split(":", 1) for line in
                           Path("/proc/self/status").read_text().splitlines() if ":" in line)
            emit({"event": "security-probe", **result,
                  "caps_zero": all(int(posture[key].strip(), 16) == 0 for key in
                                   ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")),
                  "no_new_privs": posture["NoNewPrivs"].strip(),
                  "seccomp": posture["Seccomp"].strip()})
        elif command == "quit":
            emit({"event": "exiting"})
            break
        else:
            raise ValueError("unknown fixture command")
    except (OSError, ValueError) as error:
        emit({"event": "fixture-refusal", "error": type(error).__name__, "errno": getattr(error, "errno", None)})

if held_file is not None:
    held_file.close()
