"""W106673 disposable operator-run experiment. Preparation is not execution.

Only --run invokes Docker/mount operations. --self-test invokes neither.
No install, service, arbitrary target, runtime command or recovery CLI.
Linux/glibc >=2.36; local rootful Docker without user-namespace remapping.
All generated evidence/resources remain under the printed private /tmp root.
"""

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import uuid

HERE = Path(__file__).resolve().parent
IMAGE = "sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0"
GID = 65532
LABEL = "baton.experiment=W106673"
TARGET = "/output"
TIMEOUT = 30


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def save(path, value):
    temporary = path.with_suffix(".next")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def pin(path):
    found = os.stat(path, follow_symlinks=False)
    return [found.st_dev, found.st_ino]


def namespace_pin(pid, name="mnt"):
    # Follow the proc magic link: its own symlink inode is not the namespace.
    found = os.stat(f"/proc/{pid}/ns/{name}")
    return [found.st_dev, found.st_ino]


def process_start(pid):
    # comm may contain spaces and parentheses; field 22 follows its last ')'.
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


def mounts(pid):
    result = []
    for line in Path(f"/proc/{pid}/mountinfo").read_text().splitlines():
        left, right = line.split(" - ", 1)
        fields = left.split()
        result.append(dict(id=fields[0], device=fields[2], root=fields[3],
                           target=fields[4], options=fields[5].split(","),
                           propagation=fields[6:], filesystem=right.split()[0]))
    return result


class Gate:
    """Durable fixture gate. Loading state ALWAYS discards prior permission."""

    def __init__(self, path, identity=None):
        self.path = path
        if identity is None:
            self.value = json.loads(path.read_text())
            self.value.update(phase="uncertain", receipt=None)
        else:
            self.value = dict(identity=identity, generation=1, phase="attached",
                              receipt=None, consumed=0, admissions=1)
        self.persist()

    def persist(self):
        save(self.path, self.value)

    def intent(self):
        require(self.value["phase"] == "attached", "detach needs current attachment")
        self.value.update(phase="uncertain", receipt=None)
        self.persist()

    def revoked(self, observation):
        require(self.value["phase"] == "uncertain", "revocation needs a pending intent")
        self.value.update(phase="revoked", receipt=dict(
            identity=self.value["identity"], generation=self.value["generation"],
            operation=uuid.uuid4().hex, observation=observation))
        self.persist()
        return dict(self.value["receipt"])

    def stopped(self, observation):
        self.value.update(phase="shutdown", receipt=dict(
            identity=self.value["identity"], generation=self.value["generation"],
            operation=uuid.uuid4().hex, observation=observation))
        self.persist()
        return dict(self.value["receipt"])

    def consume(self, receipt):
        require(self.value["phase"] in ("revoked", "shutdown"), "consumption denied")
        require(receipt is not None and receipt == self.value["receipt"], "stale receipt")
        self.value.update(phase="reviewed", receipt=None,
                          consumed=self.value["consumed"] + 1)
        self.persist()

    def admit(self):
        require(self.value["phase"] == "reviewed", "new writer denied")
        self.value.update(phase="attached", generation=self.value["generation"] + 1,
                          admissions=self.value["admissions"] + 1, receipt=None)
        self.persist()


def docker(*args):
    # Fixed daemon; no inherited DOCKER_HOST, context, config, credentials or SSH.
    result = subprocess.run(
        ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock", *args],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "DOCKER_CONFIG": "/nonexistent"})
    require(result.returncode == 0, "Docker refused: " + result.stderr[:500])
    return result.stdout.strip()


def libc_calls():
    libc = ctypes.CDLL(None, use_errno=True)
    for name, args in (
        ("setns", [ctypes.c_int, ctypes.c_int]),
        ("open_tree", [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]),
        ("move_mount", [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]),
        ("mount_setattr", [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_size_t]),
        ("umount2", [ctypes.c_char_p, ctypes.c_int]),
    ):
        function = getattr(libc, name)  # Missing wrapper is a preflight refusal.
        function.argtypes = args
        function.restype = ctypes.c_int
    return libc


def checked(result):
    if result == -1:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))
    return result


class MountAttr(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("attr_set", "attr_clr", "propagation", "userns_fd")]


def namespace_operation(fixture, action, crash=None):
    """Fork a short-lived privileged controller; worker receives no descriptor.

    Reattach uses a detached bind created with open_tree and fixed /output.
    Only revocation is umount2(flags=0); no lazy/forced unmount path exists.
    """
    require(action in ("attach", "detach"), "closed mount operation")
    fixture.identity()
    fds = []
    child = None
    read_end, write_end = os.pipe()
    try:
        namespace = os.open(f"/proc/{fixture.pid}/ns/mnt", os.O_RDONLY)
        root = os.open(f"/proc/{fixture.pid}/root", os.O_RDONLY | os.O_DIRECTORY)
        fds.extend((namespace, root))
        require([os.fstat(namespace).st_dev, os.fstat(namespace).st_ino] == fixture.ns_pin,
                "opened namespace changed")
        fixture.identity()
        child = os.fork()
        if child == 0:
            os.close(read_end)
            try:
                libc = libc_calls()
                tree = None
                if action == "attach":
                    source = os.open(fixture.workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                    require([os.fstat(source).st_dev, os.fstat(source).st_ino] == fixture.workspace_pin,
                            "source descriptor identity changed")
                    # AT_EMPTY_PATH | OPEN_TREE_CLONE | OPEN_TREE_CLOEXEC.
                    tree = checked(libc.open_tree(source, b"", 0x1000 | 1 | os.O_CLOEXEC))
                    os.close(source)
                    # NOSUID|NODEV, private propagation, detached clone only.
                    attributes = MountAttr(2 | 4, 0, 1 << 18, 0)
                    checked(libc.mount_setattr(tree, b"", 0x1000,
                                              ctypes.byref(attributes), ctypes.sizeof(attributes)))
                checked(libc.setns(namespace, 0x00020000))  # CLONE_NEWNS.
                os.fchdir(root)
                os.chroot(".")
                os.chdir("/")
                os.close(root)
                os.close(namespace)
                signal.alarm(TIMEOUT)
                if crash == "before":
                    os._exit(71)
                if action == "detach":
                    checked(libc.umount2(b"/output", 0))
                else:
                    checked(libc.move_mount(tree, b"", -100, b"/output", 4))
                    os.close(tree)
                if crash == "after":
                    os._exit(72)
                answer = {"ok": True}
            except BaseException as error:
                answer = {"ok": False, "error": type(error).__name__,
                          "errno": getattr(error, "errno", None), "reason": str(error)[:300]}
            os.write(write_end, json.dumps(answer).encode())
            os._exit(0)
        os.close(write_end)
        write_end = None
        # No controller keeps a target/source descriptor through ordinary unmount.
        for descriptor in fds:
            os.close(descriptor)
        fds.clear()
        ready, _, _ = select.select([read_end], [], [], TIMEOUT + 2)
        require(ready, "namespace controller timed out; revocation uncertain")
        raw = os.read(read_end, 4096)
        _, status = os.waitpid(child, 0)
        child = None
        require(raw and os.waitstatus_to_exitcode(status) == 0,
                "namespace controller interrupted; revocation uncertain")
        return json.loads(raw)
    finally:
        if child is not None:
            # Only the exact child this runner just forked; no arbitrary PID.
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        os.close(read_end)
        if write_end is not None:
            os.close(write_end)
        for descriptor in fds:
            os.close(descriptor)


class Fixture:
    def __init__(self, root, name, workspace=None):
        self.directory = root / name
        self.directory.mkdir(mode=0o700)
        self.workspace = workspace or self.directory / "workspace"
        if workspace is None:
            self.workspace.mkdir()
            os.chown(self.workspace, 0, GID)
            os.chmod(self.workspace, 0o2775)
        self.workspace_pin = pin(self.workspace)
        self.nonce = uuid.uuid4().hex
        self.container = None
        self.pid = None
        self.link = None
        self.pidfd = None
        self.gate = None
        self.events = []

    def event(self, action, **facts):
        self.events.append(dict(action=action, monotonic_ns=time.monotonic_ns(), **facts))
        save(self.directory / "events.json", self.events)

    def inspect(self):
        found = json.loads(docker("inspect", "--type", "container", self.container))[0]
        require(found["Id"] == self.container and found["Image"] == IMAGE, "container/image mismatch")
        require(found["Config"]["Labels"].get("baton.experiment") == "W106673"
                and found["Config"]["Labels"].get("baton.run") == self.nonce, "label mismatch")
        return found

    def identity(self):
        found = self.inspect()
        require(found["State"]["Running"] and found["State"]["Pid"] == self.pid, "runtime not current")
        require(not select.select([self.pidfd], [], [], 0)[0], "original process exited")
        require(process_start(self.pid) == self.start_time, "PID reused")
        require(namespace_pin(self.pid) == self.ns_pin, "mount namespace changed")
        require(pin(self.workspace) == self.workspace_pin, "workspace replaced")
        host = found["HostConfig"]
        require(not host["Privileged"] and host["ReadonlyRootfs"]
                and host["NetworkMode"] == "none" and host["CapDrop"] == ["ALL"]
                and not host["PidMode"]
                and "no-new-privileges" in host["SecurityOpt"], "container restrictions changed")
        pids = docker("top", self.container, "-eo", "pid").splitlines()[1:]
        require([int(p.strip()) for p in pids] == [self.pid], "unexpected runtime processes")
        return found

    def topology(self, attached):
        self.identity()
        table = mounts(self.pid)
        root = [m for m in table if m["target"] == "/"]
        require(len(root) == 1 and "ro" in root[0]["options"]
                and not root[0]["propagation"], "container root is not private/read-only")
        output = [m for m in table if m["target"] == TARGET]
        require(len(output) == int(attached), "unexpected output mount count")
        for entry in table:
            if entry["device"] != self.source_mount["device"]:
                continue
            a, b = entry["root"].rstrip("/"), self.source_mount["root"].rstrip("/")
            overlap = a == b or a.startswith(b + "/") or b.startswith(a + "/")
            if overlap:
                require(attached and entry["target"] == TARGET
                        and entry["root"] == self.source_mount["root"],
                        "alternate mount exposes workspace")
        if attached:
            require("rw" in output[0]["options"] and not output[0]["propagation"],
                    "workspace mount is not private writable")
            require(pin(f"/proc/{self.pid}/root/output") == self.workspace_pin,
                    "mounted workspace identity differs")
        self.event("topology", attached=attached, mounts=table)
        return output

    def reply(self):
        ready, _, _ = select.select([self.link.stdout], [], [], TIMEOUT)
        require(ready, "resident response timeout")
        raw = self.link.stdout.readline()
        require(raw, "resident exited without a reply")
        answer = json.loads(raw)
        require(answer.get("event") != "fixture-refusal", "resident refused: " + raw[:300])
        self.event("resident", answer=answer)
        return answer

    def command(self, command):
        self.identity()
        self.link.stdin.write(command + "\n")
        self.link.stdin.flush()
        answer = self.reply()
        require(answer["session_nonce"] == self.session_nonce and answer["pid"] == 1,
                "resident session/process changed")
        return answer

    def start(self):
        # Stage reviewed script as a regular read-only file in operator-owned root.
        script = self.directory / "resident.py"
        script.write_bytes((HERE / "resident.py").read_bytes())
        os.chmod(script, 0o444)
        self.event("create-intent", nonce=self.nonce, image=IMAGE,
                   workspace=str(self.workspace), workspace_pin=self.workspace_pin)
        self.container = docker(
            "create", "--pull=never", "--interactive", "--network=none",
            "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--user=65532:65532", "--group-add=65532", "--pids-limit=16",
            "--memory=128m", "--cpus=1", "--label", LABEL, "--label", "baton.run=" + self.nonce,
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777",
            "--mount", f"type=bind,src={self.workspace},dst=/output,bind-propagation=rprivate",
            "--mount", f"type=bind,src={script},dst=/resident.py,readonly",
            "--workdir=/tmp", "--entrypoint=python3", IMAGE, "-u", "/resident.py")
        require(len(self.container) == 64 and all(c in "0123456789abcdef" for c in self.container),
                "unrecognized created container ID; inspect experiment labels manually")
        self.event("created", container=self.container, nonce=self.nonce, image=IMAGE,
                   workspace=str(self.workspace), workspace_pin=self.workspace_pin)
        self.stderr = (self.directory / "docker-attach.stderr").open("w")
        self.link = subprocess.Popen(
            ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock",
             "start", "--attach", "--interactive", self.container],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "DOCKER_CONFIG": "/nonexistent"})
        first = self.reply()
        require(first["event"] == "ready" and first["pid"] == 1
                and first["uid"] == 65532 and first["gid"] == GID, "wrong resident identity")
        self.session_nonce = first["session_nonce"]
        found = self.inspect()
        self.pid = found["State"]["Pid"]
        self.pidfd = os.pidfd_open(self.pid)
        self.start_time = process_start(self.pid)
        self.ns_pin = namespace_pin(self.pid)
        self.gate = Gate(self.directory / "gate.json", dict(
            container=self.container, pid=self.pid, start=self.start_time,
            mount_namespace=self.ns_pin, workspace=self.workspace_pin, session=self.session_nonce))
        self.event("registered", identity=self.gate.value["identity"])
        require(namespace_pin(self.pid, "user") == namespace_pin("self", "user"),
                "rootless/remapped user namespaces are outside this fixture")
        require(self.ns_pin != namespace_pin("self"), "worker shares host mount namespace")
        configured = found["Mounts"]
        require(len(configured) == 2 and
                {(m["Destination"], m["RW"]) for m in configured} ==
                {("/output", True), ("/resident.py", False)}, "unexpected bind mount")
        output = [m for m in mounts(self.pid) if m["target"] == TARGET]
        require(len(output) == 1, "missing initial workspace mount")
        self.source_mount = output[0]
        self.topology(True)
        posture = self.command("security-probe")
        require(posture["mount_errno"] == errno.EPERM and posture["unshare_errno"] == errno.EPERM,
                "worker mount/namespace prohibition unproved")
        require(posture["caps_zero"] and posture["no_new_privs"] == "1"
                and posture["seccomp"] == "2", "worker privilege posture differs")

    def detach(self, crash=None):
        self.topology(True)
        self.gate.intent()  # Durable denial precedes the syscall or injected loss.
        answer = namespace_operation(self, "detach", crash)
        self.event("detach-result", answer=answer)
        if not answer["ok"]:
            raise OSError(answer.get("errno") or errno.EIO, "ordinary detach failed")
        self.topology(False)
        probe = self.command("probe")
        require(not probe["writable"] and probe["errno"] in (errno.ENOENT, errno.EROFS),
                "detached resident can still access content")
        return self.gate.revoked(dict(mount_absent=True, access=probe))

    def consume(self, receipt):
        self.gate.consume(receipt)
        # The only consumer-read site is strictly after the checked gate.
        content = (self.workspace / "rounds.txt").read_text()
        self.event("consumed", content=content)
        return content

    def attach(self):
        require(self.gate.value["phase"] == "reviewed", "reattach before review denied")
        self.topology(False)
        # Close gates before a potentially uncertain attachment.
        self.gate.value.update(phase="uncertain", receipt=None)
        self.gate.persist()
        answer = namespace_operation(self, "attach")
        require(answer["ok"], "reattach failed; shutdown required")
        self.topology(True)
        require(self.command("probe")["writable"], "reattached workspace unavailable")
        self.gate.value["phase"] = "reviewed"
        self.gate.admit()

    def shutdown(self):
        found = self.inspect()
        if found["State"]["Running"]:
            # Identity failure refuses even cleanup of a running process.
            self.identity()
            docker("stop", "--time", "3", self.container)
        found = self.inspect()
        require(not found["State"]["Running"] and found["State"]["Pid"] == 0,
                "container stop unconfirmed")
        require(select.select([self.pidfd], [], [], TIMEOUT)[0], "init exit unconfirmed")
        # Search all host-visible processes for a survivor of this namespace.
        # Any unreadable namespace other than a concurrently vanished task refuses.
        survivors = []
        for proc in Path("/proc").iterdir():
            if not proc.name.isdecimal():
                continue
            try:
                if namespace_pin(proc.name) == self.ns_pin:
                    survivors.append(proc.name)
            except FileNotFoundError:
                pass
        require(not survivors, "experiment namespace still has a process")
        self.event("shutdown-confirmed")
        return self.gate.stopped(dict(container_stopped=True, init_exited=True, survivors=[]))

    def finish(self):
        # No rm/rmdir or recursive cleanup: preserve stopped containers and files.
        if self.link is not None:
            self.link.stdin.close()
            self.link.wait(timeout=TIMEOUT)
            self.link.stdout.close()
            self.stderr.close()
        if self.pidfd is not None:
            os.close(self.pidfd)
            self.pidfd = None


def denied(fixture, receipt=None):
    before = fixture.gate.value.copy()
    for operation in (lambda: fixture.gate.consume(receipt), fixture.gate.admit):
        try:
            operation()
        except RuntimeError:
            continue
        raise AssertionError("uncertain gate admitted an operation")
    require(fixture.gate.value == before, "denial changed gate counters")
    fixture.event("both-gates-denied")


def experiment():
    require(os.geteuid() == 0, "--run requires the separately approved operator command")
    require(sys.platform == "linux", "Linux required")
    libc_calls()
    os.umask(0o077)
    image = json.loads(docker("image", "inspect", IMAGE))[0]
    require(image["Id"] == IMAGE and not image["Config"].get("Volumes"), "image changed/has volumes")
    root = Path(tempfile.mkdtemp(prefix="baton-w106673-", dir="/tmp"))
    print(root, flush=True)
    save(root / "runner.json", dict(image=IMAGE, gid=GID, created=time.time(),
         scripts={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(__file__).resolve(), HERE / "resident.py")}))
    results = {}
    fixtures = []
    try:
        happy = Fixture(root, "happy")
        fixtures.append(happy)
        happy.start()
        happy.command("write-1")
        happy.command("complete")
        began = time.monotonic_ns()
        old = happy.detach()
        require(happy.consume(old) == "round 1\n", "round one bytes differ")
        results["detach_to_consumer_ns"] = time.monotonic_ns() - began
        began = time.monotonic_ns()
        happy.attach()
        # A prior receipt cannot authorize this new attachment.
        denied(happy, old)
        happy.command("write-2")
        results["reattach_to_write_ns"] = time.monotonic_ns() - began
        happy.command("complete")
        require(happy.consume(happy.detach()) == "round 1\nround 2\n", "round two bytes differ")
        happy.shutdown()
        happy.finish()
        for name in ("open-file", "cwd", "omitted", "before", "after"):
            fixture = Fixture(root, name)
            fixtures.append(fixture)
            fixture.start()
            fixture.command("write-1")
            fixture.command({"open-file": "declare-with-open-file",
                             "cwd": "declare-with-workspace-cwd"}.get(name, "complete"))
            if name == "omitted":
                denied(fixture)
            else:
                try:
                    fixture.detach(crash=name if name in ("before", "after") else None)
                except OSError as error:
                    require(name in ("open-file", "cwd") and error.errno == errno.EBUSY,
                            "unexpected detach syscall failure")
                    fixture.event("protocol-violation-busy")
                except RuntimeError as error:
                    require(name in ("before", "after") and "interrupted" in str(error),
                            "unexpected controller failure")
                    fixture.event("controller-interrupted", point=name)
                    # Observe the real kernel state while keeping the lost-
                    # acknowledgment gate closed. This is no new receipt.
                    fixture.topology(name == "before")
                else:
                    raise AssertionError("negative detach unexpectedly succeeded")
                denied(fixture)
            # Reload persisted gate, simulating manager policy reconstruction.
            # Actual helper death occurred in before/after; no production manager runs.
            fixture.gate = Gate(fixture.directory / "gate.json")
            denied(fixture)
            require(fixture.consume(fixture.shutdown()) == "round 1\n", "fallback bytes differ")
            fixture.finish()
        baseline = Fixture(root, "stop-start-one")
        fixtures.append(baseline)
        baseline.start()
        baseline.command("write-1")
        baseline.command("complete")
        began = time.monotonic_ns()
        baseline.consume(baseline.shutdown())
        results["stop_to_consumer_ns"] = time.monotonic_ns() - began
        baseline.finish()
        began = time.monotonic_ns()
        require(baseline.gate.value["phase"] == "reviewed",
                "replacement writer requires reviewed confirmed-stop result")
        next_one = Fixture(root, "stop-start-two", baseline.workspace)
        fixtures.append(next_one)
        next_one.start()
        next_one.command("write-1")
        results["restart_to_write_ns"] = time.monotonic_ns() - began
        next_one.shutdown()
        next_one.finish()
        save(root / "result.json", dict(outcome="deterministic-proof-passed",
             timings=results, real_agent_session="not attempted",
             limitation="helper crash and fixture gate reload; not production-manager recovery"))
    except BaseException as error:
        save(root / "result.json", dict(outcome="failed-or-blocked", error=type(error).__name__,
             reason=str(error)[:1000], timings=results, consumption_and_admission="denied"))
        for fixture in fixtures:
            if fixture.pidfd is not None and fixture.gate is not None:
                try:
                    fixture.gate.value.update(phase="uncertain", receipt=None)
                    fixture.gate.persist()
                    fixture.shutdown()
                    fixture.finish()
                except BaseException as cleanup:
                    fixture.event("cleanup-unconfirmed", reason=str(cleanup)[:500])
        raise
    return root


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "gate.json"
        self.gate = Gate(self.path, {"container": "fixture"})

    def tearDown(self):
        self.temporary.cleanup()

    def test_omitted_detach_denies_both(self):
        with self.assertRaises(RuntimeError):
            self.gate.consume(None)
        with self.assertRaises(RuntimeError):
            self.gate.admit()

    def test_namespace_pin_is_the_opened_namespace(self):
        descriptor = os.open("/proc/self/ns/mnt", os.O_RDONLY)
        try:
            held = os.fstat(descriptor)
            self.assertEqual(namespace_pin("self"), [held.st_dev, held.st_ino])
        finally:
            os.close(descriptor)

    def test_loss_and_restart_discard_current_permission(self):
        self.gate.intent()
        receipt = self.gate.revoked({"fixture": True})
        recovered = Gate(self.path)
        with self.assertRaises(RuntimeError):
            recovered.consume(receipt)
        with self.assertRaises(RuntimeError):
            recovered.admit()
        recovered.consume(recovered.stopped({"fixture_stop": True}))

    def test_consumer_does_not_open_content_while_denied(self):
        fixture = object.__new__(Fixture)
        fixture.gate = self.gate
        fixture.workspace = Path(self.temporary.name)
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("consumer opened content")):
            with self.assertRaises(RuntimeError):
                fixture.consume(None)

    def test_partial_attachment_keeps_both_gates_closed(self):
        self.gate.intent()
        self.gate.consume(self.gate.revoked({"fixture": True}))
        self.gate.value["phase"] = "uncertain"
        self.gate.persist()
        with self.assertRaises(RuntimeError):
            self.gate.admit()
        with self.assertRaises(RuntimeError):
            self.gate.consume(None)

    def test_old_and_duplicate_receipts_do_not_authorize_next_generation(self):
        self.gate.intent()
        old = self.gate.revoked({"fixture": True})
        self.gate.consume(old)
        with self.assertRaises(RuntimeError):
            self.gate.consume(old)
        self.gate.admit()
        self.gate.intent()
        new = self.gate.revoked({"fixture": True})
        with self.assertRaises(RuntimeError):
            self.gate.consume(old)
        self.gate.consume(new)
        self.assertEqual(self.gate.value["consumed"], 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--self-test", action="store_true")
    choice.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    experiment()
    return 0


if __name__ == "__main__":
    sys.exit(main())
