"""W38956 — WHICH DOCKER TRANSPORT CAN ACTUALLY DRIVE `baton.worker-entry/1`.

Run against the development host's own daemon on 2026-08-29; the recorded
answers are in `w38956-transport-probe.txt` beside this file.

THE QUESTION. The accepted start vector is `docker run --detach` with no
`--interactive`, so the container's stdin is `/dev/null`: the reference worker
reads EOF immediately and exits 0. A worker-entry conversation needs a stdin
that stays open, frames written to it, and an EOF at the end -- `serve` returns
0 only on a clean end of input, and a session ended by a signal is not a worker
that finished.

So three candidate transports were measured rather than argued about, and each
was measured for the four properties the conversation actually needs: frames
in, frames out, stderr told apart from stdout, and EOF propagated so the worker
ends its own session with its own exit status.

WHAT IS DELIBERATELY NOT MEASURED HERE: whether any of them is the right
BOUNDARY. That is a design decision and it is recorded in `FINDING.md`. This
file establishes only what the daemon does, because a design argued from a
guess about `docker attach` is a design nobody can check.
"""

import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

# One echoing program, used by every candidate, so the transports differ and
# the peer does not. It answers each line, then says out loud that it saw EOF
# -- which is the property `docker attach` turns out not to have.
PROGRAM = ("import sys\n"
           "for line in sys.stdin:\n"
           "    sys.stdout.write('echo:' + line); sys.stdout.flush()\n"
           "sys.stderr.write('EOF-SEEN\\n'); sys.stderr.flush()\n"
           "sys.exit(0)\n")

IMAGE = "python:3.13-slim"


def _pump(stream, sink):
    for chunk in iter(lambda: stream.read(1), b""):
        sink.append(chunk)


def drive(argv, label, *, wait=10):
    """Write one line, close stdin, and report what came back and when.

    The reader threads are what make this measure the LIVE channel rather than
    a completed process: a `subprocess.run` cannot tell "answered and then
    waited" from "answered at exit".
    """
    process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = [], []
    threading.Thread(target=_pump, args=(process.stdout, out),
                     daemon=True).start()
    threading.Thread(target=_pump, args=(process.stderr, err),
                     daemon=True).start()
    process.stdin.write(b"one\n")
    process.stdin.flush()
    time.sleep(1.5)
    answered = (b"".join(out), b"".join(err))
    process.stdin.close()
    try:
        status = process.wait(timeout=wait)
    except subprocess.TimeoutExpired:
        process.kill()
        status = "NO-EOF (still running after stdin closed)"
    print(f"{label}:")
    print(f"    answered while live: stdout={answered[0]!r} "
          f"stderr={answered[1]!r}")
    print(f"    after stdin close:   stdout={b''.join(out)!r} "
          f"stderr={b''.join(err)!r}")
    print(f"    transport status:    {status}")


def started(name, argv, program=PROGRAM):
    made = subprocess.run(
        ["docker", "run", "--detach", "--interactive", "--name", name,
         "--network", "none", "--user", "65532:65532"] + argv
        + [IMAGE, "python3", "-u", "-c", program],
        capture_output=True, timeout=600)
    assert made.returncode == 0, made.stderr.decode("utf-8", "replace")
    return made.stdout.decode("utf-8").strip()


def probe_attach():
    """`docker run --detach --interactive` + `docker attach`."""
    name = "baton-w38956-attach-" + uuid.uuid4().hex[:8]
    runtime = started(name, [])
    try:
        drive(["docker", "attach", runtime], "docker attach")
    finally:
        subprocess.run(["docker", "rm", "--force", runtime],
                       capture_output=True, timeout=180)


def probe_exec():
    """`docker run --detach --interactive` holding the container up, then
    `docker exec --interactive` for the conversation itself."""
    name = "baton-w38956-exec-" + uuid.uuid4().hex[:8]
    runtime = started(name, [], program="import sys; sys.stdin.read()")
    try:
        drive(["docker", "exec", "--interactive", runtime,
               "python3", "-u", "-c", PROGRAM], "docker exec --interactive")
    finally:
        subprocess.run(["docker", "rm", "--force", runtime],
                       capture_output=True, timeout=180)


def probe_start_attach():
    """`docker create` + `docker start --attach --interactive`."""
    name = "baton-w38956-start-" + uuid.uuid4().hex[:8]
    made = subprocess.run(
        ["docker", "create", "--interactive", "--name", name,
         "--network", "none", "--user", "65532:65532",
         IMAGE, "python3", "-u", "-c", PROGRAM],
        capture_output=True, timeout=600)
    runtime = made.stdout.decode("utf-8").strip()
    try:
        drive(["docker", "start", "--attach", "--interactive", runtime],
              "docker create + docker start --attach --interactive")
        held = subprocess.run(
            ["docker", "container", "inspect", runtime, "--format",
             "{{.State.Status}} {{.State.ExitCode}}"],
            capture_output=True, timeout=120)
        print(f"    container ending:    "
              f"{held.stdout.decode('utf-8').strip()}")
    finally:
        subprocess.run(["docker", "rm", "--force", runtime],
                       capture_output=True, timeout=180)


def probe_exec_identity():
    """THE SECOND QUESTION, and the one that decides between the two survivors.

    W33936 gives an execution container its workspace share as
    `--group-add <gid>`, which is a HostConfig property of the container. An
    exec session is a different process created through a different API, so
    whether it inherits that supplementary group is a fact about the daemon
    rather than something to assume -- and a transport whose worker cannot
    write `/output` is not a transport.
    """
    home = tempfile.mkdtemp(prefix="baton-w38956-identity-")
    workspace = os.path.join(home, "workspace")
    os.makedirs(workspace)
    os.chmod(workspace, 0o2770)
    name = "baton-w38956-identity-" + uuid.uuid4().hex[:8]
    runtime = started(
        name,
        ["--group-add", str(os.getgid()),
         "--mount", f"type=bind,source={workspace},target=/output,"
                    f"readonly=false"],
        program="import sys; sys.stdin.read()")
    try:
        asked = subprocess.run(
            ["docker", "exec", runtime, "sh", "-c",
             "id; touch /output/written-by-exec && echo WROTE || echo DENIED"],
            capture_output=True, timeout=180)
        print("docker exec identity and workspace write:")
        for line in asked.stdout.decode("utf-8", "replace").splitlines():
            print(f"    {line}")
    finally:
        subprocess.run(["docker", "rm", "--force", runtime],
                       capture_output=True, timeout=180)
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    print(subprocess.run(["docker", "version", "--format",
                          "docker server {{.Server.Version}}"],
                         capture_output=True,
                         timeout=120).stdout.decode("utf-8").strip())
    probe_attach()
    probe_exec()
    probe_start_attach()
    probe_exec_identity()
