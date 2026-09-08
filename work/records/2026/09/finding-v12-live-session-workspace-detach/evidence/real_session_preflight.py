"""Prepared W106673 offline exact-image transport probe; operator execution only.

--self-test has no Docker/provider side effects. --operator creates ONE offline
container and retains it stopped. No workspace, credential, mount syscall,
provider user message, model call, image acquisition or existing container use.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import uuid

IMAGE = "sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f"
VERSION = "2.1.247 (Claude Code)"
CLI = "/usr/local/bin/claude"
LIMIT = 262144
FLAGS = ("--input-format", "--output-format", "--verbose", "--print",
         "--resume", "--session-id", "--setting-sources", "--strict-mcp-config",
         "--mcp-config", "--tools", "--max-turns", "--max-budget-usd", "--model",
         "--dangerously-skip-permissions")
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/probe-home",
       "TMPDIR": "/tmp", "XDG_CACHE_HOME": "/tmp/probe-cache",
       "PYTHONDONTWRITEBYTECODE": "1"}


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


class Frames:
    """Bound retained and total bytes; errors never quote provider output."""
    def __init__(self):
        self.pending = b""
        self.total = 0

    def feed(self, chunk):
        self.total += len(chunk)
        require(self.total <= LIMIT, "output-limit")
        self.pending += chunk
        records = []
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                raise RuntimeError("invalid-json") from None
            require(isinstance(record, dict), "invalid-record")
            records.append(record)
        return records


def captured(argv):
    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             cwd="/tmp", env=ENV)
    data = bytearray()
    deadline = time.monotonic() + 15
    try:
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "command-timeout")
            require(select.select([child.stdout], [], [], remaining)[0], "command-timeout")
            chunk = os.read(child.stdout.fileno(), 8192)
            if not chunk:
                break
            data.extend(chunk)
            require(len(data) <= LIMIT, "output-limit")
        require(child.wait(timeout=max(.01, deadline-time.monotonic())) == 0, "command-failed")
        return bytes(data)
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stdout.close()


def initialized(record, request_id):
    # Project only an exact correlation and success bit, never response contents.
    if record.get("type") != "control_response":
        return False
    response = record.get("response")
    require(isinstance(response, dict), "invalid-control-response")
    require(response.get("request_id") == request_id, "wrong-control-correlation")
    require(response.get("subtype") == "success", "initialization-refused")
    return True


def inside():
    require(os.geteuid() == 65532 and os.getpid() == 1, "wrong-probe-identity")
    Path(ENV["HOME"]).mkdir(mode=0o700)
    version = captured([CLI, "--version"])
    require(version.decode().strip() == VERSION, "wrong-cli-version")
    help_bytes = captured([CLI, "--help"])
    help_text = help_bytes.decode()
    flags = {flag: flag in help_text for flag in FLAGS}
    require(all(flags.values()), "required-flag-absent")
    # No user frame is ever sent. No credential and network=none enforce the
    # offline boundary even if initialization attempts background traffic.
    argv = [CLI, "--print", "--input-format", "stream-json", "--output-format",
            "stream-json", "--verbose", "--tools", "", "--setting-sources=",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, cwd="/tmp", env=ENV)
    pidfd = os.pidfd_open(child.pid)
    start = Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    request_id = uuid.uuid4().hex
    decoder = Frames()
    accepted = False
    begun = time.monotonic_ns()
    try:
        child.stdin.write((json.dumps({"type": "control_request", "request_id": request_id,
                                      "request": {"subtype": "initialize", "hooks": None}}) + "\n").encode())
        child.stdin.flush()
        deadline = time.monotonic() + 15
        while not accepted:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "initialization-timeout")
            require(select.select([child.stdout], [], [], remaining)[0], "initialization-timeout")
            chunk = os.read(child.stdout.fileno(), 8192)
            require(chunk, "cli-exited-before-initialization")
            for record in decoder.feed(chunk):
                accepted = initialized(record, request_id) or accepted
        elapsed = time.monotonic_ns() - begun
        # This proves only an idle initialized process, never a Claude turn/session.
        require(not select.select([pidfd], [], [], 1)[0], "initialized-cli-exited")
        require(Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
                == start, "cli-process-changed")
        return dict(outcome="offline-transport-preflight-passed", version=VERSION,
                    help_sha256=hashlib.sha256(help_bytes).hexdigest(), flags=flags,
                    initialized=True, idle_process_survived=True, pid=child.pid,
                    start=start, initialization_ns=elapsed,
                    real_turns=0, session_continuity="unproved", restore="unproved")
    finally:
        child.stdin.close()
        if child.poll() is None:
            child.terminate()
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=3)
        child.stdout.close()
        os.close(pidfd)


def docker(*args):
    result = subprocess.run(["/usr/bin/docker", "--host", "unix:///var/run/docker.sock", *args],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=60,
                            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
                                 "DOCKER_CONFIG": "/nonexistent"})
    require(result.returncode == 0, "docker-refused")
    require(len(result.stdout) <= LIMIT, "docker-output-limit")
    return result.stdout


def checked_container(container, nonce):
    found = json.loads(docker("inspect", "--type=container", container))[0]
    require(found["Id"] == container and found["Image"] == IMAGE, "container-image-mismatch")
    require(found["Config"]["Labels"].get("baton.run") == nonce
            and found["Config"]["Labels"].get("baton.experiment") == "W106673-offline-session",
            "container-label-mismatch")
    host = found["HostConfig"]
    require(host["NetworkMode"] == "none" and not host["Privileged"]
            and host["ReadonlyRootfs"] and host["CapDrop"] == ["ALL"]
            and "no-new-privileges" in host["SecurityOpt"], "wrong-container-posture")
    require(found["Config"]["User"] == "65532:65532", "wrong-container-user")
    require(len(found["Mounts"]) == 1 and found["Mounts"][0]["Destination"] == "/probe.py"
            and not found["Mounts"][0]["RW"], "unexpected-bind")
    return found


def operator():
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix="baton-w106673-session-preflight-", dir="/tmp"))
    print(root, flush=True)
    script = root / "probe.py"
    script.write_bytes(Path(__file__).read_bytes())
    script.chmod(0o444)
    nonce = uuid.uuid4().hex
    result = dict(outcome="failed-or-blocked", image=IMAGE, run=nonce,
                  script_sha256=hashlib.sha256(script.read_bytes()).hexdigest())
    container = None
    try:
        result["stage"] = "image-check"
        image = json.loads(docker("image", "inspect", IMAGE))[0]
        require(image["Id"] == IMAGE and not image["Config"].get("Volumes"), "wrong-image")
        require(not any(one.split("=", 1)[0].startswith(("ANTHROPIC_", "CLAUDE_"))
                        for one in image["Config"].get("Env", [])), "provider-image-environment")
        result["stage"] = "container-create"
        container = docker("create", "--pull=never", "--network=none", "--read-only",
                           "--cap-drop=ALL", "--security-opt=no-new-privileges",
                           "--user=65532:65532", "--pids-limit=64", "--memory=1g", "--cpus=1",
                           "--label=baton.experiment=W106673-offline-session",
                           "--label=baton.run=" + nonce,
                           "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
                           "--mount", f"type=bind,src={script},dst=/probe.py,readonly",
                           "--workdir=/tmp", "--entrypoint=/usr/bin/python3",
                           IMAGE, "-B", "/probe.py", "--inside").decode().strip()
        require(len(container) == 64 and all(c in "0123456789abcdef" for c in container),
                "invalid-created-id")
        result["container"] = container
        (root / "registration.json").write_text(json.dumps(result, indent=2) + "\n")
        checked_container(container, nonce)
        result["stage"] = "offline-initialization"
        answer = json.loads(docker("start", "--attach", container))
        require(isinstance(answer, dict) and answer.get("outcome") == "offline-transport-preflight-passed",
                "inside-probe-failed")
        result["probe"] = answer
        result["outcome"] = "offline-transport-preflight-passed"
        result["stage"] = "done"
    except Exception:
        # No raw runtime exception or child output is published.
        result["outcome"] = "failed-or-blocked"
    finally:
        if container is not None:
            try:
                found = checked_container(container, nonce)
                if found["State"]["Running"]:
                    docker("stop", "--time=3", container)
                found = checked_container(container, nonce)
                require(not found["State"]["Running"] and found["State"]["Pid"] == 0,
                        "stop-unconfirmed")
                result["cleanup"] = "confirmed-stopped-retained"
                result["container_exit_code"] = found["State"]["ExitCode"]
                if result["container_exit_code"] != 0:
                    result["outcome"] = "failed-or-blocked"
            except Exception:
                result["cleanup"] = "unconfirmed-operator-inspection-required"
                result["outcome"] = "failed-or-blocked"
        (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] == "offline-transport-preflight-passed" else 1


class LocalTests(unittest.TestCase):
    def test_cleanup_identity_check_refuses_a_different_container(self):
        with mock.patch(__name__ + ".docker", return_value=json.dumps([
                {"Id": "other", "Image": IMAGE}]).encode()):
            with self.assertRaisesRegex(RuntimeError, "container-image-mismatch"):
                checked_container("expected", "nonce")

    def test_fragmented_records(self):
        frames = Frames()
        self.assertEqual(frames.feed(b'{"type":"control_'), [])
        self.assertEqual(frames.feed(b'response"}\n'), [{"type": "control_response"}])

    def test_malformed_and_oversized_are_closed(self):
        for raw in (b'{secret}\n', b'[]\n', b'x' * (LIMIT + 1)):
            with self.subTest(size=len(raw)):
                with self.assertRaises(RuntimeError) as error:
                    Frames().feed(raw)
                self.assertNotIn("secret", str(error.exception))

    def test_control_response_requires_exact_success(self):
        good = {"type": "control_response", "response": {"request_id": "pin", "subtype": "success"}}
        self.assertTrue(initialized(good, "pin"))
        self.assertFalse(initialized({"type": "result", "result": "secret"}, "pin"))
        for response in ({"request_id": "old", "subtype": "success"},
                         {"request_id": "pin", "subtype": "error", "error": "secret"}):
            with self.assertRaises(RuntimeError) as error:
                initialized({"type": "control_response", "response": response}, "pin")
            self.assertNotIn("secret", str(error.exception))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--operator", action="store_true")
    group.add_argument("--inside", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LocalTests))
        return 0 if result.wasSuccessful() else 1
    if args.inside:
        try:
            print(json.dumps(inside(), sort_keys=True))
            return 0
        except Exception:
            print('{"outcome":"offline-transport-preflight-failed"}')
            return 1
    return operator()


if __name__ == "__main__":
    sys.exit(main())
