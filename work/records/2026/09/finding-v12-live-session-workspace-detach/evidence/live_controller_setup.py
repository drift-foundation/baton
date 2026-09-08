"""W106673 ONE separately approved live pair. --audit is read-only/offline.

No arbitrary image/model/credential/network/target operands, build, pull, retry,
production manager invocation or live coordination-store access. Fixture-only.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
IMAGE = "sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f"
SOURCE = "/home/sl/.claude/.credentials.json"
GID = 65532
USER = 1000
DELAY_NS = 5_000_000_000
DOCKER_ENV = dict(PATH="/usr/bin:/bin", HOME="/nonexistent", DOCKER_CONFIG="/nonexistent")
DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
MANIFEST = HERE / "live-setup-manifest.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def audit():
    given = json.loads(MANIFEST.read_text())
    for relative, expected in given["files"].items():
        path = REPO / relative
        require(path.is_file() and not path.is_symlink() and digest(path) == expected, "package-drift")
    runtime = {str(p.relative_to(REPO)) for p in (REPO / "v12/python/src/baton_v12").rglob("*.py")}
    require(runtime == {p for p in given["files"] if p.startswith("v12/python/src/baton_v12/") and p.endswith(".py")},
            "runtime-file-set-drift")
    schemas = {"v12/python/src/baton_v12/contracts/schema/" + name for name in
               ("worker-control-1.0.schema.json", "agent-session-1.0.schema.json")}
    require(schemas <= given["files"].keys(), "schema-package-incomplete")
    require(given["image"] == IMAGE, "manifest-constants")
    return given


def require(condition, code):
    if not condition:
        raise ValueError(code)


# A standalone operator/audit invocation proves the helper bytes before import.
# Unit tests import this module without running its command-line boundary.
if __name__ == "__main__":
    try:
        audit()
    except Exception:
        print('{"outcome":"package-drift-or-manifest-missing"}')
        sys.exit(1)

import host_runner as base
import live_supervisor as wire
import real_session_contract as contract
require = wire.require


def snapshot_runtime(root, manifest):
    snapshot = root / "runtime-source-private"
    snapshot.mkdir(mode=0o700)
    for relative, expected in manifest["files"].items():
        if not relative.startswith("v12/python/"):
            continue
        source = REPO / relative
        require(not source.is_symlink(), "runtime-source-symlink")
        content = source.read_bytes()
        require(hashlib.sha256(content).hexdigest() == expected, "runtime-copy-drift")
        target = snapshot / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(content)
    return snapshot / "v12/python"


def docker(*arguments):
    answer = subprocess.run([*DOCKER, *arguments], env=DOCKER_ENV, stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=30)
    require(answer.returncode == 0, "docker-refused")
    require(len(answer.stdout) <= 2 * 1024 * 1024, "docker-output-bound")
    return answer.stdout.decode().strip()


@contextmanager
def source_identity():
    original = os.geteuid()
    try:
        os.seteuid(USER)
        yield
    finally:
        os.seteuid(original)


class Credentials:
    """Existing source reader + manager materialization, confined to this run."""
    def __init__(self):
        # Retain lifecycle ownership before any fallible constructor operation.
        self.store = None
        self.deliveries = {}

    def prepare(self, root, runtime, setup):
        setup.enter("credential-imports")
        credentials, workspaces, ControlStore, sources = runtime_apis(runtime, setup)
        setup.enter("volatile-home-check")
        require(any(m["target"] == "/dev/shm" and m["filesystem"] == "tmpfs" for m in base.mounts("self")),
                "credential-home-not-volatile")
        setup.enter("credential-home-create", "credential_home")
        self.place = Path(tempfile.mkdtemp(prefix="baton-w106673-credentials-", dir="/dev/shm"))
        setup.created("credential_home", self.place)
        setup.enter("source-registry-create", "source_registry")
        self.registry_home = Path(tempfile.mkdtemp(prefix="baton-w106673-source-", dir="/dev/shm"))
        setup.created("source_registry", self.registry_home)
        registry = self.registry_home / "sources.json"
        setup.enter("source-registry-write")
        base.save(registry, dict(schema=sources.SCHEMA, sources=[dict(provider="claude", reference="w106673-owner-source", path=SOURCE)]))
        setup.enter("source-registry-permissions")
        os.chown(registry, USER, USER)
        os.chmod(registry, 0o600)
        os.chown(self.registry_home, USER, USER)
        os.chmod(self.registry_home, 0o700)
        setup.enter("source-reader-construct")
        self.reader = sources.UserCredentialSources(str(registry), max_bearer=credentials.MAX_BEARER)
        setup.enter("credential-home-construct")
        self.home = credentials.CredentialHome(str(self.place))
        setup.enter("fixture-store-open", "fixture_store")
        self.store = ControlStore.open(str(root / "fixture-control.sqlite3"), incarnation=uuid.uuid4().hex, clock=fixture_now)
        setup.created("fixture_store", root / "fixture-control.sqlite3")
        setup.enter("fixture-group-configure")
        workspaces.configure_workspace_group(self.store, GID)
        setup.enter("fixture-group-read")
        self.group = workspaces.configured_workspace_group(self.store)
        setup.enter("private-resource-record")
        base.save(root / "private-resources.json", dict(credential_home=str(self.place), source_registry_home=str(self.registry_home),
                  session_state="private arm directories; never export"))
        setup.complete()

    def provider(self, provider, reference):
        with source_identity():
            return self.reader(provider, reference)

    def materialize(self, attempt):
        delivery = self.home.materialize([dict(slot="claude", provider="claude", reference="w106673-owner-source")],
            attempt_id=attempt, workspace_group=self.group, credential_provider=self.provider)
        self.deliveries[attempt] = delivery
        require(len(delivery.mounts()) == 1 and delivery.mounts()[0][1] == "/run/baton/credentials/claude", "credential-slot-drift")
        return delivery

    def release(self, attempt, shutdown_confirmed):
        require(shutdown_confirmed is True, "credential-release-before-shutdown")
        self.home.tear_down(self.deliveries[attempt])
        del self.deliveries[attempt]


STAGES = frozenset(("created", "image-inspect", "network-inspect", "operator-groups", "runtime-snapshot",
    "credential-imports", "source-reader-import", "volatile-home-check", "credential-home-create",
    "source-registry-create", "source-registry-write", "source-registry-permissions", "source-reader-construct",
    "credential-home-construct", "fixture-store-open", "fixture-group-configure", "fixture-group-read",
    "private-resource-record", "setup-complete", "pair", "fixture-store-close"))


def safe_exception(error, stage):
    require(stage in STAGES, "unknown-diagnostic-stage")
    kinds = {FileNotFoundError: "file-not-found", PermissionError: "permission-denied",
             ModuleNotFoundError: "module-not-found", ImportError: "import-error", ValueError: "value-error",
             TypeError: "type-error", OSError: "os-error", RuntimeError: "runtime-error",
             subprocess.TimeoutExpired: "subprocess-timeout", wire.Refusal: "fixture-refusal"}
    number = error.errno if isinstance(error, OSError) else None
    if type(number) is not int or not 0 < number < 4096:
        number = None
    return dict(stage=stage, exception_kind=kinds.get(type(error), "other"), errno=number)


class Setup:
    def __init__(self, root):
        self.root = root
        self.paths = {}
        self.value = dict(stage="created", construction_complete=False, store_close="not-opened",
                          resources={name: "not-started" for name in ("credential_home", "source_registry", "fixture_store")})
        self.persist()

    def persist(self):
        base.save(self.root / "setup.json", self.value)

    def enter(self, stage, resource=None):
        require(stage in STAGES, "unknown-setup-stage")
        self.value["stage"] = stage
        if resource is not None:
            require(resource in self.value["resources"], "unknown-setup-resource")
            self.value["resources"][resource] = "attempted"
        self.persist()  # Intent survives failures before a constructor returns.

    def created(self, resource, path):
        require(resource in self.value["resources"], "unknown-setup-resource")
        self.paths[resource] = str(path)
        base.save(self.root / "setup-private.json", self.paths)
        self.value["resources"][resource] = "created"
        self.persist()

    def complete(self):
        self.value.update(stage="setup-complete", construction_complete=True)
        self.persist()


def settle_setup(credentials, setup):
    # Close only a fixture-store object we actually received. No new directory,
    # registry, source or orphan removal is introduced by this correction.
    if credentials is not None and credentials.store is not None:
        try:
            credentials.store.close()
            setup.value["store_close"] = "confirmed"
        except BaseException as error:
            setup.value["store_close"] = "unconfirmed"
            setup.value["ending_diagnostic"] = safe_exception(error, "fixture-store-close")
    resources = setup.value["resources"]
    untouched = all(state == "not-started" for state in resources.values())
    partial = not setup.value["construction_complete"] and not untouched
    store_settled = resources["fixture_store"] == "not-started" or setup.value["store_close"] == "confirmed"
    settled = not partial and store_settled
    setup.value.update(partial_setup_unresolved=partial, cleanup_accounted=settled)
    setup.persist()
    return settled


def runtime_apis(runtime, setup):
    # Frozen read-only package imports; no production manager is started.
    require(not any(name == "baton_v12" or name.startswith("baton_v12.") for name in sys.modules), "runtime-already-imported")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(runtime / "src"))
    from baton_v12.worker_manager import credentials, workspaces
    from baton_v12.worker_manager.store import ControlStore
    setup.enter("source-reader-import")
    spec = importlib.util.spec_from_file_location("fixture_user_credentials", runtime / "tools/user_credentials.py")
    sources = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sources)
    return credentials, workspaces, ControlStore, sources


def process_fact(pid):
    fields = {}
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        name, _, value = line.partition(":")
        fields[name] = value.split()
    require(fields["Uid"] == [str(GID)] * 4 and fields["Gid"] == [str(GID)] * 4, "process-user-drift")
    require(all(int(fields[name][0], 16) == 0 for name in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"))
            and fields["NoNewPrivs"] == ["1"] and fields["Seccomp"] == ["2"], "process-privilege-drift")
    cwd = os.readlink(f"/proc/{pid}/cwd")
    require(cwd != "/output" and not cwd.startswith("/output/"), "process-workspace-cwd")
    executable = os.stat(f"/proc/{pid}/exe")
    return dict(pid=pid, parent=int(fields["PPid"][0]), start=base.process_start(pid),
                namespace=base.namespace_pin(pid), inner_pid=int(fields["NSpid"][-1]),
                executable=[executable.st_dev, executable.st_ino])


def check_tree(facts, init, cli, namespace):
    require({f["pid"] for f in facts} == {init, cli} and len(facts) == 2, "unexpected-idle-process-tree")
    require(all(f["namespace"] == namespace for f in facts), "process-namespace-drift")
    require(next(f for f in facts if f["pid"] == cli)["parent"] == init, "cli-parent-drift")


def read_artifacts(workspace, expected_pin):
    descriptor = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        held = os.fstat(descriptor)
        require([held.st_dev, held.st_ino] == expected_pin, "consumer-workspace-drift")
        names = os.listdir(descriptor)
        require(set(names) <= {"solution.py", "continuity.txt"}, "artifact-path-set")
        files = {}
        for name in names:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
            try:
                found = os.fstat(fd)
                require(stat.S_ISREG(found.st_mode) and found.st_nlink == 1 and found.st_size <= 4096, "artifact-file-boundary")
                files[name] = os.read(fd, 4097)
                require(len(files[name]) <= 4096, "artifact-size-bound")
            finally:
                os.close(fd)
        return files
    finally:
        os.close(descriptor)


def export_evidence(root):
    """Copy only controller-owned projections; never walk private/session trees."""
    names = ["package.json", "network.json", "arms.json", "result.json", "setup.json"]
    names += [f"{arm}/{name}.json" for arm in ("retained-first", "restored-first", "restored-second") for name in ("events", "gate")]
    destination = Path(tempfile.mkdtemp(prefix="baton-w106673-live-export-", dir="/tmp"))
    hashes = {}
    for name in names:
        source = root / name
        if not source.exists():
            continue
        found = source.lstat()
        require(stat.S_ISREG(found.st_mode) and found.st_nlink == 1 and found.st_size <= 4 * 1024 * 1024, "export-file-boundary")
        content = source.read_bytes()
        json.loads(content)
        target = destination / name
        target.parent.mkdir(mode=0o700, exist_ok=True)
        target.write_bytes(content)
        os.chmod(target, 0o600)
        os.chown(target, USER, USER)
        if target.parent != destination:
            os.chown(target.parent, USER, USER)
        hashes[name] = hashlib.sha256(content).hexdigest()
    base.save(destination / "PROVENANCE.json", dict(original_root=str(root), files=hashes,
              scope="controller-owned projections only; session, source, delivery, workspace and fixture store excluded"))
    os.chmod(destination / "PROVENANCE.json", 0o600)
    os.chown(destination / "PROVENANCE.json", USER, USER)
    os.chown(destination, USER, USER)
    return destination


class Fixture(base.Fixture):
    def __init__(self, root, name, network, credentials, deadline, workspace=None, session_home=None, session=None, resume=False):
        super().__init__(root, name, workspace)
        self.network = network
        self.credentials = credentials
        self.deadline = deadline
        self.session_home = session_home or self.directory / "session-private"
        if session_home is None:
            self.session_home.mkdir(mode=0o700)
            os.chown(self.session_home, GID, GID)
            for name in ("work", "home", "cache"):
                place = self.session_home / name
                place.mkdir(mode=0o700)
                os.chown(place, GID, GID)
        self.session = session or str(uuid.uuid4())
        self.resume = resume
        self.cli_fd = None
        self.stopped = False
        self.delivery = None
        self.create_started = False

    def event(self, action, **facts):
        if action == "detach-result":
            answer = facts["answer"]
            facts = dict(answer=dict(ok=answer.get("ok") is True,
                         errno=answer.get("errno") if type(answer.get("errno")) is int else None))
        super().event(action, **facts)

    def inspect(self):
        found = json.loads(docker("inspect", "--type", "container", self.container))[0]
        require(found["Id"] == self.container and found["Image"] == IMAGE, "container-image-drift")
        require(found["Config"]["Labels"].get("baton.experiment") == "W106673"
                and found["Config"]["Labels"].get("baton.run") == self.nonce, "container-label-drift")
        return found

    def identity(self):
        found = self.inspect()
        require(found["State"]["Running"] and found["State"]["Pid"] == self.pid, "container-not-current")
        require(not select.select([self.pidfd], [], [], 0)[0] and base.process_start(self.pid) == self.start_time, "init-exited-or-reused")
        require(base.namespace_pin(self.pid) == self.ns_pin and base.pin(self.workspace) == self.workspace_pin, "namespace-workspace-drift")
        host = found["HostConfig"]
        require(not host["Privileged"] and host["ReadonlyRootfs"] and host["NetworkMode"] == self.network
                and host["CapDrop"] == ["ALL"] and not host["CapAdd"] and not host["PidMode"]
                and "no-new-privileges" in host["SecurityOpt"] and not host["PortBindings"]
                and not host["PublishAllPorts"] and host["Memory"] == 2 * 1024**3
                and host["PidsLimit"] == 64 and host["NanoCpus"] == 1_000_000_000,
                "runtime-posture-drift")
        require(found["Config"]["User"] == "65532:65532", "runtime-user-drift")
        expected = {("/output", True, str(self.workspace)), ("/session", True, str(self.session_home)),
                    ("/live_supervisor.py", False, str(self.directory / "live_supervisor.py")),
                    ("/run/baton/credentials/claude", False, self.delivery.mounts()[0][0])}
        require(len(found["Mounts"]) == 4 and {(m["Destination"], m["RW"], m["Source"]) for m in found["Mounts"]} == expected,
                "runtime-mount-config-drift")
        return found

    def tree(self):
        rows = docker("top", self.container, "-eo", "pid").splitlines()[1:]
        require(0 < len(rows) <= 64 and all(row.strip().isdecimal() for row in rows), "process-list-shape")
        return sorted((process_fact(int(row)) for row in rows), key=lambda f: f["pid"])

    def quiescent(self):
        self.identity()
        require(not select.select([self.cli_fd], [], [], 0)[0], "cli-pidfd-exited")
        facts = self.tree()
        check_tree(facts, self.pid, self.cli_pid, self.ns_pin)
        require(facts == self.baseline_tree, "idle-process-tree-changed")
        response = self.command("identity")
        require(response["cli_pid"] == self.cli_inner and response["cli_start"] == self.cli_start
                and response["session"] == self.session, "supervisor-cli-identity-drift")
        self.event("quiescent", processes=facts, session=self.session)

    def reply(self, seconds=30):
        answer = self.reader.next(min(self.deadline, time.monotonic() + seconds))
        require(answer.get("event") in ("ready", "initialized", "complete", "identity", "probe"), "supervisor-refused")
        return answer

    def command(self, command, **operands):
        self.identity()
        self.link.stdin.write(json.dumps(dict(op=command, **operands)).encode() + b"\n")
        self.link.stdin.flush()
        return self.reply(180 if command == "turn" else 30)

    def start(self):
        script = self.directory / "live_supervisor.py"
        script.write_bytes((HERE / "live_supervisor.py").read_bytes())
        os.chmod(script, 0o444)
        self.delivery = self.credentials.materialize(self.nonce)
        credential, target = self.delivery.mounts()[0]
        self.event("create-intent", nonce=self.nonce, image=IMAGE, network_id=self.network,
                   workspace_pin=self.workspace_pin, requested_session=self.session, resume=self.resume)
        self.create_started = True
        self.container = docker("create", "--pull=never", "--interactive", "--network=" + self.network,
            "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--user=65532:65532",
            "--group-add=65532", "--pids-limit=64", "--memory=2g", "--cpus=1",
            "--label", base.LABEL, "--label", "baton.run=" + self.nonce,
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
            "--mount", f"type=bind,src={self.workspace},dst=/output,bind-propagation=rprivate",
            "--mount", f"type=bind,src={self.session_home},dst=/session,bind-propagation=rprivate",
            "--mount", f"type=bind,src={script},dst=/live_supervisor.py,readonly",
            "--mount", f"type=bind,src={credential},dst={target},readonly",
            "--workdir=/session/work", "--entrypoint=python3", IMAGE, "-u", "/live_supervisor.py")
        require(re.fullmatch(r"[0-9a-f]{64}", self.container), "created-id-unrecognized")
        self.event("created", container=self.container)
        self.link = subprocess.Popen([*DOCKER, "start", "--attach", "--interactive", self.container],
            env=DOCKER_ENV, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        self.reader = wire.Lines(self.link.stdout.fileno())
        first = self.reply()
        require(first == dict(event="ready", pid=1, uid=GID, gid=GID), "supervisor-identity")
        found = self.inspect()
        self.pid = found["State"]["Pid"]
        self.pidfd = os.pidfd_open(self.pid)
        self.start_time = base.process_start(self.pid)
        self.ns_pin = base.namespace_pin(self.pid)
        require(base.namespace_pin(self.pid, "user") == base.namespace_pin("self", "user")
                and self.ns_pin != base.namespace_pin("self"), "unsupported-namespace-posture")
        self.gate = base.Gate(self.directory / "gate.json", dict(container=self.container, pid=self.pid,
            start=self.start_time, mount_namespace=self.ns_pin, workspace=self.workspace_pin))
        self.event("registered", identity=self.gate.value["identity"])
        output = [m for m in base.mounts(self.pid) if m["target"] == "/output"]
        require(len(output) == 1, "initial-workspace-missing")
        self.source_mount = output[0]
        self.topology(True)
        initialized = self.command("start", session=self.session, resume=self.resume, deadline=self.deadline)
        self.cli_inner, self.cli_start = initialized["cli_pid"], initialized["cli_start"]
        facts = self.tree()
        matches = [f for f in facts if f["inner_pid"] == self.cli_inner and f["start"] == self.cli_start]
        require(len(matches) == 1, "cli-host-identity-unproved")
        self.cli_pid = matches[0]["pid"]
        self.cli_fd = os.pidfd_open(self.cli_pid)
        self.baseline_tree = facts
        self.quiescent()
        self.event("initialized", **initialized)

    def turn(self, prompt):
        self.quiescent()
        began = time.monotonic_ns()
        answer = self.command("turn", prompt=prompt)
        require(answer["session"] == self.session and answer["actual_model"] == wire.ACTUAL_MODEL
                and answer["cli_version"] == wire.VERSION, "turn-runtime-identity")
        completed = answer["completed_ns"]
        require(type(completed) is int and began <= completed <= time.monotonic_ns(), "turn-clock-order")
        self.quiescent()
        self.event("turn-complete", dispatched_ns=began, **answer)
        return began, completed, answer

    def detach(self):
        self.quiescent()
        receipt = super().detach()
        self.quiescent()
        return receipt

    def consume(self, receipt, token, corrected):
        self.gate.consume(receipt)
        self.event("receipt-consumed", receipt=receipt)
        files = read_artifacts(self.workspace, self.workspace_pin)
        require(contract.verify(files, token, corrected), "artifact-verification-failed")
        self.event("consumed-and-verified", corrected=corrected,
                   files={name: hashlib.sha256(value).hexdigest() for name, value in files.items()})
        return True

    def process_identity(self):
        self.quiescent()
        return [self.container, self.cli_pid, self.cli_start, self.ns_pin]

    def shutdown(self):
        # A dead/failed CLI must not prevent stopping the exact pinned container.
        found = self.inspect()
        if found["State"]["Running"]:
            if self.pidfd is not None:
                self.identity()
            docker("stop", "--time", "3", self.container)
        found = self.inspect()
        require(not found["State"]["Running"] and found["State"]["Pid"] == 0, "shutdown-unconfirmed")
        if self.pidfd is not None:
            require(select.select([self.pidfd], [], [], 30)[0], "init-exit-unconfirmed")
            for proc in Path("/proc").iterdir():
                if proc.name.isdecimal():
                    try:
                        require(base.namespace_pin(proc.name) != self.ns_pin, "namespace-survivor")
                    except FileNotFoundError:
                        pass
        self.stopped = True
        self.event("shutdown-confirmed", container=self.container, init_exit_observed=self.pidfd is not None)
        receipt = self.gate.stopped(dict(container_stopped=True, init_exited=True, survivors=[])) if self.gate else None
        self.credentials.release(self.nonce, True)
        self.delivery = None
        return receipt

    def finish(self):
        if self.link is not None:
            self.link.stdin.close()
            self.link.wait(timeout=30)
            self.link.stdout.close()
            self.link = None
        for name in ("pidfd", "cli_fd"):
            fd = getattr(self, name)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)


def measured(fixture, action, operation):
    began = time.monotonic_ns()
    answer = operation()
    fixture.event(action, duration_ns=time.monotonic_ns() - began)
    return answer


def execute_pair(root, network, credentials, deadline, fixtures):
    token = uuid.uuid4().hex
    prompt = contract.first_prompt(token)
    common = dict(image=IMAGE, model=wire.MODEL, cli_version=wire.VERSION,
        initial_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        correction_prompt_sha256=hashlib.sha256(contract.CORRECTION.encode()).hexdigest(),
        initial_bytes_sha256=hashlib.sha256(b"").hexdigest(), review_delay_ns=DELAY_NS)
    results = {}
    for arm in ("retained", "restored"):
        first = Fixture(root, arm + "-first", network, credentials, deadline)
        fixtures.append(first)
        require(not list(first.workspace.iterdir()), "initial-workspace-not-empty")
        measured(first, "initial-runtime-start", first.start)
        before = first.process_identity()
        _, end, _ = first.turn(prompt)
        row = dict(common, process_before=before, workspace_before=first.workspace_pin,
                   session_before=first.session, end_of_work_ns=end)
        operation = first.detach if arm == "retained" else first.shutdown
        receipt = measured(first, "first-detach" if arm == "retained" else "first-stop", operation)
        row["first_artifact_verified"] = first.consume(receipt, token, False)
        row["review_ready_ns"] = time.monotonic_ns()
        require(deadline - time.monotonic() > 5, "review-deadline")
        time.sleep(DELAY_NS / 1e9)
        if arm == "retained":
            current = first
            measured(first, "reattach", first.attach)
            first.quiescent()
        else:
            require(first.stopped and first.gate.value["phase"] == "reviewed", "replacement-before-reviewed-stop")
            first.finish()
            current = Fixture(root, "restored-second", network, credentials, deadline,
                workspace=first.workspace, session_home=first.session_home, session=first.session, resume=True)
            fixtures.append(current)
            measured(current, "replacement-start-and-initialize", current.start)
            row.update(old_container_shutdown_confirmed=True, resume_requested=first.session)
        began, done, answer = current.turn(contract.CORRECTION)
        row.update(correction_dispatch_ns=began, correction_done_ns=done, session_after=answer["session"],
                   process_after=current.process_identity(), workspace_after=base.pin(current.workspace),
                   actual_model=answer["actual_model"])
        row["correction_verified"] = current.consume(measured(current, "final-detach", current.detach), token, True)
        row["verified_correction_ns"] = time.monotonic_ns()
        row["consumption_receipts_verified"] = True
        if arm == "retained":
            row["pidfd_continuously_live"] = not select.select([current.cli_fd], [], [], 0)[0]
        current.shutdown()
        current.finish()
        results[arm] = row
        base.save(root / "arms.json", results)
    return dict(outcome="live-pair-passed", arms=results, timings=contract.comparable(results["retained"], results["restored"]))


def run():
    manifest = audit()
    require(os.geteuid() == 0 and sys.platform == "linux", "separate-root-operator-approval-required")
    base.libc_calls()
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix="baton-w106673-live-", dir="/tmp"))
    print(root, flush=True)
    base.save(root / "package.json", dict(manifest_sha256=digest(MANIFEST), image=IMAGE, model=wire.MODEL))
    fixtures = []
    setup = Setup(root)
    credentials = None
    original_groups = os.getgroups()
    began = time.monotonic()
    deadline = began + 720  # Reserve the final 180 seconds of the 900s run for ending.
    overall_deadline = began + 900
    outcome = dict(outcome="failed-or-inconclusive", consumption_and_admission="denied", cleanup_confirmed=False)
    def expired(*_):
        raise wire.Refusal("overall-timeout")
    signal.signal(signal.SIGALRM, expired)
    signal.signal(signal.SIGTERM, expired)
    signal.setitimer(signal.ITIMER_REAL, 720)
    try:
        setup.enter("image-inspect")
        image = json.loads(docker("image", "inspect", IMAGE))[0]
        require(image["Id"] == IMAGE and not image["Config"].get("Volumes"), "image-missing-or-drift")
        setup.enter("network-inspect")
        network = json.loads(docker("network", "inspect", "bridge"))[0]
        require(network["Name"] == "bridge" and network["Driver"] == "bridge" and network["Scope"] == "local"
                and not network["Internal"] and network["Options"].get("com.docker.network.bridge.default_bridge") == "true"
                and re.fullmatch(r"[0-9a-f]{64}", network["Id"]), "builtin-bridge-unproved")
        base.save(root / "network.json", dict(id=network["Id"], driver="bridge", boundary="ordinary Docker outbound; not provider-only"))
        setup.enter("operator-groups")
        os.setgroups(sorted(set(original_groups) | {GID}))
        setup.enter("runtime-snapshot")
        runtime = snapshot_runtime(root, manifest)
        credentials = Credentials()
        credentials.prepare(root, runtime, setup)
        setup.enter("pair")
        outcome = execute_pair(root, network["Id"], credentials, deadline, fixtures)
    except BaseException as error:
        # Do not serialize exception messages, stderr, transcripts or credential contents.
        outcome["outcome"] = "failed-or-inconclusive"
        outcome["failure_code"] = "execution-refused"
        outcome["diagnostic"] = safe_exception(error, setup.value["stage"])
    finally:
        signal.setitimer(signal.ITIMER_REAL, max(0.001, overall_deadline - time.monotonic()))
        cleanup = []
        for fixture in fixtures:
            try:
                require(time.monotonic() < overall_deadline, "cleanup-deadline")
                if not fixture.stopped:
                    if fixture.gate:
                        fixture.gate.value.update(phase="uncertain", receipt=None)
                        fixture.gate.persist()
                    if fixture.container and re.fullmatch(r"[0-9a-f]{64}", fixture.container):
                        fixture.shutdown()
                    elif fixture.delivery and not fixture.create_started:
                        credentials.release(fixture.nonce, True)
                    elif fixture.create_started:
                        # A lost create response may hide a real container. Preserve the
                        # private credential delivery and exact label for operator repair.
                        raise wire.Refusal("create-outcome-uncertain")
                fixture.finish()
                cleanup.append(dict(nonce=fixture.nonce, confirmed=True))
            except BaseException:
                cleanup.append(dict(nonce=fixture.nonce, confirmed=False))
        signal.setitimer(signal.ITIMER_REAL, 0)
        setup_settled = settle_setup(credentials, setup)
        os.setgroups(original_groups)
        outcome["cleanup"] = cleanup
        outcome["cleanup_confirmed"] = setup_settled and all(row["confirmed"] for row in cleanup) and (credentials is None or not credentials.deliveries)
        if not outcome["cleanup_confirmed"]:
            outcome["outcome"] = "failed-or-inconclusive"
        outcome["limitations"] = manifest["limitations"]
        outcome["elapsed_seconds_before_result_export"] = time.monotonic() - began
        base.save(root / "result.json", outcome)
        print(export_evidence(root), flush=True)
    return 0 if outcome["outcome"] == "live-pair-passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    try:
        require(args.audit != args.run, "choose-one-operation")
        if args.audit:
            found = audit()
            print(json.dumps(dict(outcome="offline-hash-audit-passed", files=len(found["files"]))))
            sys.exit(0)
        sys.exit(run())
    except Exception:
        print('{"outcome":"refused-before-result"}')
        sys.exit(1)
