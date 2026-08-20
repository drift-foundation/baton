"""W20: mailbox-local start, stop and status own only their processes."""

from __future__ import annotations

import json
import os
import signal
import socket
import stat
import subprocess
import sys
import time

import pytest


REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
CONTROLLER = os.path.join(REPO, "tools", "infra.py")


@pytest.fixture
def fake_service(tmp_path):
	path = tmp_path / "fake_service.py"
	path.write_text(r'''
import argparse
import os
import signal
import socket
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--events", required=True)
parser.add_argument("--ready-socket")
parser.add_argument("--bind-only", action="store_true")
parser.add_argument("--crash-after", type=float)
parser.add_argument("--ignore-term", action="store_true")
parser.add_argument("--child-pid")
parser.add_argument("--grandchild-pid")
parser.add_argument("--child-ignores-term", action="store_true")
options = parser.parse_args()

def record(event):
    with open(options.events, "a", encoding="utf-8") as handle:
        handle.write(f"{event} {options.name}\n")
        handle.flush()
        os.fsync(handle.fileno())

listener = None
if options.ready_socket:
    try:
        os.unlink(options.ready_socket)
    except FileNotFoundError:
        pass
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(options.ready_socket)
    # W20: --bind-only leaves an inert socket inode at the configured
    # path and never accepts, which is what a dispatcher leaves behind
    # when its listener dies while the process lives on.
    if not options.bind_only:
        listener.listen()

if options.child_pid:
    # W20: the managed service spawns its own agent — the deployed ACP
    # bridge's shape. `--child-ignores-term` makes that agent survive
    # SIGTERM so the group cannot drain; `--grandchild-pid` nests one
    # level deeper, which the group signal covers without the
    # controller walking any parent/child chain.
    inner = "import time; time.sleep(60)"
    if options.child_ignores_term:
        inner = ("import signal, time\n"
                 "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                 "time.sleep(60)")
    if options.grandchild_pid:
        inner = ("import subprocess, sys, os, time\n"
                 "deep = subprocess.Popen([sys.executable, '-c',"
                 " 'import time; time.sleep(60)'])\n"
                 "handle = open(%r, 'w')\n"
                 "handle.write(str(deep.pid)); handle.flush()\n"
                 "os.fsync(handle.fileno()); handle.close()\n"
                 "time.sleep(60)" % options.grandchild_pid)
    child = subprocess.Popen([sys.executable, "-c", inner])
    with open(options.child_pid, "w", encoding="utf-8") as handle:
        handle.write(str(child.pid))
        handle.flush()
        os.fsync(handle.fileno())

def stop(_signum, _frame):
    if options.ignore_term:
        record("ignored")
        return
    record("term")
    if listener is not None:
        listener.close()
        try:
            os.unlink(options.ready_socket)
        except FileNotFoundError:
            pass
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
record("start")
deadline = None if options.crash_after is None else time.monotonic() + options.crash_after
while True:
    if deadline is not None and time.monotonic() >= deadline:
        record("crash")
        raise SystemExit(7)
    time.sleep(0.02)
''', encoding="utf-8")
	return str(path)


def _service(name, fake, events, *, after=(), readiness=None, extra=()):
	service = {
		"name": name,
		"command": [sys.executable, fake, "--name", name,
		            "--events", str(events), *extra],
		"after": list(after),
		"readiness": readiness or {
			"type": "process", "stableMilliseconds": 100},
		"startTimeoutSeconds": 2,
		"stopTimeoutSeconds": 2,
	}
	return service


def _mailbox(tmp_path, services, **extra):
	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	document = {
		"version": 1,
		"startTimeoutSeconds": 2,
		"stopTimeoutSeconds": 2,
		"services": services,
		**extra,
	}
	(mailbox / "infra.json").write_text(
		json.dumps(document, indent=2) + "\n", encoding="utf-8")
	return mailbox


def _run(command, mailbox):
	return subprocess.run(
		[sys.executable, CONTROLLER, command, str(mailbox)],
		capture_output=True, text=True, timeout=15)


def _json(done):
	return json.loads(done.stdout if done.stdout else done.stderr)


def _state(mailbox):
	return json.loads((mailbox / "run" / "infra-state.json").read_text(
		encoding="utf-8"))


def _alive(pid):
	try:
		body = open(f"/proc/{pid}/stat", encoding="utf-8").read()
	except FileNotFoundError:
		return False
	return body[body.rfind(")") + 2:].split()[0] != "Z"


def _wait_dead(pid, timeout=3):
	deadline = time.monotonic() + timeout
	while time.monotonic() < deadline:
		if not _alive(pid):
			return
		time.sleep(0.02)
	assert not _alive(pid), f"pid {pid} stayed alive"


def test_complete_start_status_stop_is_idempotent_private_and_ordered(
		tmp_path, fake_service):
	events = tmp_path / "events"
	ready = tmp_path / "beta.sock"
	services = [
		_service("alpha", fake_service, events),
		_service("beta", fake_service, events, after=("alpha",),
		         readiness={"type": "unix_socket", "path": str(ready)},
		         extra=("--ready-socket", str(ready))),
	]
	mailbox = _mailbox(tmp_path, services)
	try:
		started = _run("start", mailbox)
		assert started.returncode == 0, started.stderr
		assert _json(started)["healthy"] is True
		state = _state(mailbox)
		assert state["launchOrder"] == ["alpha", "beta"]
		assert not list((mailbox / "run").glob("*.tmp"))
		for directory in (mailbox / "run", mailbox / "log"):
			assert stat.S_IMODE(directory.stat().st_mode) == 0o700
		assert stat.S_IMODE(
			(mailbox / "run" / "infra-state.json").stat().st_mode) == 0o600
		for name in ("alpha", "beta"):
			log = mailbox / "log" / f"{name}.log"
			assert stat.S_IMODE(log.stat().st_mode) == 0o600
			assert '"event": "launch"' in log.read_text(encoding="utf-8")

		status = _run("status", mailbox)
		assert status.returncode == 0, status.stderr
		assert [row["state"] for row in _json(status)["services"]] == [
			"healthy", "healthy"]
		again = _run("start", mailbox)
		assert again.returncode == 0
		assert _json(again)["already_running"] is True
		assert events.read_text(encoding="utf-8").splitlines() == [
			"start alpha", "start beta"]

		stopped = _run("stop", mailbox)
		assert stopped.returncode == 0, stopped.stderr
		assert not (mailbox / "run" / "infra-state.json").exists()
		assert events.read_text(encoding="utf-8").splitlines() == [
			"start alpha", "start beta", "term beta", "term alpha"]
		again = _run("stop", mailbox)
		assert again.returncode == 0
		assert _json(again)["already_stopped"] is True
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


def test_stop_terminates_a_service_process_group(tmp_path, fake_service):
	"""A managed bridge may spawn an ACP agent process. Stopping only the
	group leader reports success while leaving that agent alive, so lifecycle
	ownership has to cover the whole session created for the service."""
	events = tmp_path / "events"
	child_pid_path = tmp_path / "child.pid"
	service = _service(
		"parent", fake_service, events,
		extra=("--child-pid", str(child_pid_path)))
	mailbox = _mailbox(tmp_path, [service])
	child_pid = None
	try:
		assert _run("start", mailbox).returncode == 0
		child_pid = int(child_pid_path.read_text(encoding="utf-8"))
		assert _alive(child_pid), "the managed service did not spawn its agent"
		stopped = _run("stop", mailbox)
		assert stopped.returncode == 0, stopped.stderr
		_wait_dead(child_pid)
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)
		if child_pid is not None and _alive(child_pid):
			os.kill(child_pid, signal.SIGKILL)
			_wait_dead(child_pid)


def test_logs_append_across_restarts(tmp_path, fake_service):
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	for _iteration in range(2):
		assert _run("start", mailbox).returncode == 0
		assert _run("stop", mailbox).returncode == 0
	log = (mailbox / "log" / "owned.log").read_text(encoding="utf-8")
	assert log.count('"event": "launch"') == 2


def test_http_readiness_is_checked(tmp_path):
	probe = socket.socket()
	probe.bind(("127.0.0.1", 0))
	port = probe.getsockname()[1]
	probe.close()
	service = {
		"name": "http-service",
		"command": [sys.executable, "-m", "http.server", str(port),
		            "--bind", "127.0.0.1"],
		"readiness": {"type": "http",
		              "url": f"http://127.0.0.1:{port}/",
		              "expectedStatus": 200},
		"startTimeoutSeconds": 3,
		"stopTimeoutSeconds": 2,
	}
	mailbox = _mailbox(tmp_path, [service])
	try:
		assert _run("start", mailbox).returncode == 0
		assert _run("status", mailbox).returncode == 0
	finally:
		assert _run("stop", mailbox).returncode == 0


def test_failed_readiness_rolls_back_only_this_invocations_children(
		tmp_path, fake_service):
	events = tmp_path / "events"
	never = tmp_path / "never.sock"
	services = [
		_service("alpha", fake_service, events),
		_service("beta", fake_service, events, after=("alpha",),
		         readiness={"type": "unix_socket", "path": str(never)},
		         extra=("--crash-after", "0.15")),
	]
	mailbox = _mailbox(tmp_path, services)
	failed = _run("start", mailbox)
	assert failed.returncode == 2
	assert "beta failed readiness" in _json(failed)["error"]
	assert "beta.log" in _json(failed)["error"]
	assert not (mailbox / "run" / "infra-state.json").exists()
	assert events.read_text(encoding="utf-8").splitlines() == [
		"start alpha", "start beta", "crash beta", "term alpha"]


def test_interrupted_start_records_then_rolls_back_its_child(
		tmp_path, fake_service):
	events = tmp_path / "events"
	never = tmp_path / "never.sock"
	service = _service(
		"owned", fake_service, events,
		readiness={"type": "unix_socket", "path": str(never)})
	mailbox = _mailbox(tmp_path, [service])
	controller = subprocess.Popen(
		[sys.executable, CONTROLLER, "start", str(mailbox)],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	deadline = time.monotonic() + 3
	while time.monotonic() < deadline and not events.exists():
		time.sleep(0.02)
	assert events.exists(), "the fake child never started"
	os.kill(controller.pid, signal.SIGTERM)
	stdout, stderr = controller.communicate(timeout=5)
	assert controller.returncode == 2
	assert not stdout
	assert "startup interrupted by signal" in json.loads(stderr)["error"]
	assert events.read_text(encoding="utf-8").splitlines() == [
		"start owned", "term owned"]
	assert not (mailbox / "run" / "infra-state.json").exists()


def test_child_crash_is_visible_and_stop_cleans_stale_state(
		tmp_path, fake_service):
	events = tmp_path / "events"
	service = _service("short", fake_service, events,
	                   extra=("--crash-after", "0.4"))
	mailbox = _mailbox(tmp_path, [service])
	assert _run("start", mailbox).returncode == 0
	pid = _state(mailbox)["services"]["short"]["pid"]
	_wait_dead(pid)
	status = _run("status", mailbox)
	assert status.returncode == 1
	assert _json(status)["services"][0]["state"] == "stopped"
	assert _run("stop", mailbox).returncode == 0
	assert not (mailbox / "run" / "infra-state.json").exists()


@pytest.mark.parametrize("field,replacement,expected", [
	("startTicks", lambda value: value + 1, "pid-reused"),
	("observedArgv", lambda value: value + ["tampered"], "argv-mismatch"),
])
def test_stop_refuses_pid_reuse_or_argv_mismatch_without_signalling(
		tmp_path, fake_service, field, replacement, expected):
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	assert _run("start", mailbox).returncode == 0
	path = mailbox / "run" / "infra-state.json"
	original = _state(mailbox)
	pid = original["services"]["owned"]["pid"]
	tampered = json.loads(json.dumps(original))
	entry = tampered["services"]["owned"]
	entry[field] = replacement(entry[field])
	path.write_text(json.dumps(tampered), encoding="utf-8")
	refused = _run("stop", mailbox)
	assert refused.returncode == 2
	assert _json(refused)["services"][0]["state"] == expected
	assert _alive(pid), "the controller signalled an unowned process"
	path.write_text(json.dumps(original), encoding="utf-8")
	assert _run("stop", mailbox).returncode == 0
	_wait_dead(pid)


def test_partial_state_refuses_start_without_adopting_or_duplicating(
		tmp_path, fake_service):
	events = tmp_path / "events"
	services = [_service("alpha", fake_service, events),
	            _service("beta", fake_service, events, after=("alpha",))]
	mailbox = _mailbox(tmp_path, services)
	assert _run("start", mailbox).returncode == 0
	path = mailbox / "run" / "infra-state.json"
	original = _state(mailbox)
	partial = json.loads(json.dumps(original))
	del partial["services"]["beta"]
	partial["launchOrder"].remove("beta")
	path.write_text(json.dumps(partial), encoding="utf-8")
	refused = _run("start", mailbox)
	assert refused.returncode == 2
	assert "refusing to adopt" in _json(refused)["error"]
	assert events.read_text(encoding="utf-8").splitlines() == [
		"start alpha", "start beta"]
	path.write_text(json.dumps(original), encoding="utf-8")
	assert _run("stop", mailbox).returncode == 0


def test_stop_uses_owned_state_even_when_manifest_becomes_malformed(
		tmp_path, fake_service):
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	assert _run("start", mailbox).returncode == 0
	pid = _state(mailbox)["services"]["owned"]["pid"]
	(mailbox / "infra.json").write_text("{broken", encoding="utf-8")
	stopped = _run("stop", mailbox)
	assert stopped.returncode == 0, stopped.stderr
	_wait_dead(pid)


def test_stop_timeout_never_escalates_to_force(tmp_path, fake_service):
	events = tmp_path / "events"
	service = _service("stubborn", fake_service, events,
	                   extra=("--ignore-term",))
	service["stopTimeoutSeconds"] = 1
	mailbox = _mailbox(tmp_path, [service])
	assert _run("start", mailbox).returncode == 0
	pid = _state(mailbox)["services"]["stubborn"]["pid"]
	try:
		refused = _run("stop", mailbox)
		assert refused.returncode == 2
		assert _json(refused)["services"][0]["state"] == "did-not-exit"
		assert _alive(pid), "the controller escalated beyond SIGTERM"
		assert "ignored stubborn" in events.read_text(encoding="utf-8")
	finally:
		if _alive(pid):
			os.kill(pid, signal.SIGKILL)
			_wait_dead(pid)
		assert _run("stop", mailbox).returncode == 0


def test_preexisting_readiness_refuses_unowned_service(
		tmp_path, fake_service):
	events = tmp_path / "events"
	ready = tmp_path / "occupied.sock"
	listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	listener.bind(str(ready))
	listener.listen()
	try:
		service = _service(
			"occupied", fake_service, events,
			readiness={"type": "unix_socket", "path": str(ready)},
			extra=("--ready-socket", str(ready)))
		mailbox = _mailbox(tmp_path, [service])
		refused = _run("start", mailbox)
		assert refused.returncode == 2
		assert "refusing to adopt" in _json(refused)["error"]
		assert not events.exists()
	finally:
		listener.close()


def test_status_refuses_a_stale_unix_socket_inode(tmp_path, fake_service):
	"""A socket pathname is not readiness. The owned process may remain
	alive while the listener disappears, and an inert socket inode can remain
	at the same path. Status must prove a connection rather than blessing the
	file type."""
	events = tmp_path / "events"
	ready = tmp_path / "service.sock"
	service = _service(
		"owned", fake_service, events,
		readiness={"type": "unix_socket", "path": str(ready)},
		extra=("--ready-socket", str(ready)))
	mailbox = _mailbox(tmp_path, [service])
	try:
		assert _run("start", mailbox).returncode == 0
		# Detach the real listener from its name, then leave a socket inode
		# at the exact configured path with no process listening on it.
		os.unlink(ready)
		stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			stale.bind(str(ready))
		finally:
			stale.close()
		status = _run("status", mailbox)
		assert status.returncode == 1, \
			"an inert socket pathname was reported healthy"
		assert _json(status)["services"][0]["state"] == "unhealthy"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


@pytest.mark.parametrize("mutate,pattern", [
	(lambda doc, _tmp: doc.update({"mystery": True}), "unknown keys"),
	(lambda doc, _tmp: doc["services"].append(dict(doc["services"][0])),
	 "duplicate service name"),
	(lambda doc, _tmp: doc["services"].append({
		"name": "other", "participant": "baton.one",
		"command": [sys.executable, "-c", "import time; time.sleep(30)"]}),
	 "participant baton.one is assigned more than once"),
	(lambda doc, _tmp: doc["services"][0].update({"after": ["one"]}),
	 "depends on itself"),
	(lambda doc, _tmp: doc["services"][0].update({
		"command": ["/definitely/missing"]}), "executable is missing"),
	(lambda doc, tmp: doc["services"][0].update({
		"requires": [str(tmp / "missing.json")]}), "required path is missing"),
])
def test_malformed_or_unsafe_manifest_refuses_before_launch(
		tmp_path, fake_service, mutate, pattern):
	events = tmp_path / "events"
	service = _service("one", fake_service, events)
	service["participant"] = "baton.one"
	mailbox = _mailbox(tmp_path, [service])
	path = mailbox / "infra.json"
	document = json.loads(path.read_text(encoding="utf-8"))
	mutate(document, tmp_path)
	path.write_text(json.dumps(document), encoding="utf-8")
	refused = _run("start", mailbox)
	assert refused.returncode == 2
	assert pattern in _json(refused)["error"]
	assert not events.exists()


def test_non_private_state_refuses_before_any_signal(tmp_path, fake_service):
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	assert _run("start", mailbox).returncode == 0
	path = mailbox / "run" / "infra-state.json"
	state = _state(mailbox)
	pid = state["services"]["owned"]["pid"]
	os.chmod(path, 0o644)
	refused = _run("stop", mailbox)
	assert refused.returncode == 2
	assert "not private" in _json(refused)["error"]
	assert _alive(pid)
	os.chmod(path, 0o600)
	assert _run("stop", mailbox).returncode == 0


@pytest.mark.parametrize("link_kind", ["symbolic", "hard"])
def test_lifecycle_lock_refuses_links_to_an_unrelated_file(tmp_path,
                                                           fake_service,
                                                           link_kind):
	"""The mailbox lock is lifecycle metadata too. Following a symbolic
	link, or accepting a hard-linked inode, makes `status`, `start` and
	`stop` take their advisory lock on somebody else's file. The target
	may be a perfectly private regular file, so mode checks alone do not
	establish mailbox ownership."""
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	run = mailbox / "run"
	run.mkdir(mode=0o700)
	victim = tmp_path / "unrelated-private-file"
	victim.write_text("must remain unrelated\n", encoding="utf-8")
	os.chmod(victim, 0o600)
	lock = run / "infra.lock"
	if link_kind == "symbolic":
		lock.symlink_to(victim)
	else:
		os.link(victim, lock)
	refused = _run("status", mailbox)
	assert refused.returncode == 2, \
		f"a {link_kind} lock was accepted: {refused.stdout}{refused.stderr}"
	assert "lock" in _json(refused)["error"]
	assert victim.read_text(encoding="utf-8") == "must remain unrelated\n"
	assert not events.exists(), "lock validation launched a service"


def test_start_refuses_a_service_log_symlink_without_touching_its_target(
		tmp_path, fake_service):
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	log_dir = mailbox / "log"
	log_dir.mkdir(mode=0o700)
	victim = tmp_path / "operator-notes"
	victim.write_text("must remain intact\n", encoding="utf-8")
	os.chmod(victim, 0o600)
	(log_dir / "owned.log").symlink_to(victim)
	try:
		refused = _run("start", mailbox)
		assert refused.returncode == 2
		assert "service log" in _json(refused)["error"]
		assert victim.read_text(encoding="utf-8") == "must remain intact\n"
		assert not events.exists(), "the controller launched after following a log symlink"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


# W459 slice 2: the example now mints its Codex Threads per start, so
# the dispatcher's configuration is RENDERED from a shipped template
# rather than maintained by hand. The controller reads that template at
# load, so exercising the example means supplying it the way an
# operator does — by replacing the placeholder path with a real one.
TEMPLATE_PLACEHOLDER = "/absolute/path/to/codex-event-bridge.template.json"
ACP_TEMPLATE_PLACEHOLDER = "/absolute/path/to/acp-bridge.template.json"


def _example_document(tmp_path):
	example = os.path.join(REPO, "conf", "infra.example.json")
	body = open(example, encoding="utf-8").read()
	for placeholder, name in (
			(TEMPLATE_PLACEHOLDER, "codex-event-bridge.template.json"),
			(ACP_TEMPLATE_PLACEHOLDER, "acp-bridge.template.json")):
		template = tmp_path / name
		template.write_text(
			open(os.path.join(REPO, "conf", name),
			     encoding="utf-8").read(), encoding="utf-8")
		body = body.replace(placeholder, str(template))
	return body


def test_checked_in_example_manifest_matches_the_controller_schema(tmp_path):
	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	(mailbox / "infra.json").write_text(_example_document(tmp_path),
	                                    encoding="utf-8")
	status = _run("status", mailbox)
	assert status.returncode == 1
	payload = _json(status)
	assert payload["healthy"] is False
	assert [row["name"] for row in payload["services"]] == [
		"codex-app-server", "codex-dispatcher", "codex-readiness",
		"codex-tuner-readiness", "claude-acp"]


def test_example_owns_one_isolated_readiness_path_per_codex_participant(
		tmp_path):
	document = json.loads(_example_document(tmp_path))
	services = {service["name"]: service for service in document["services"]}
	reviewer = services["codex-readiness"]
	tuner = services["codex-tuner-readiness"]

	def argument(service, option):
		index = service["command"].index(option)
		return service["command"][index + 1]

	assert reviewer["participant"] == argument(reviewer, "--participant") \
		== "baton.codex"
	assert tuner["participant"] == argument(tuner, "--participant") \
		== "baton.tuner"
	assert argument(reviewer, "--target") == "baton-reviewer"
	assert argument(tuner, "--target") == "baton-tuner"
	assert argument(reviewer, "--socket") == argument(tuner, "--socket")
	assert reviewer["after"] == tuner["after"] == ["codex-dispatcher"]

	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	tuner["participant"] = "baton.codex"
	(mailbox / "infra.json").write_text(
		json.dumps(document), encoding="utf-8")
	refused = _run("status", mailbox)
	assert refused.returncode == 2
	assert "participant baton.codex is assigned more than once" in \
		_json(refused)["error"]


# -- the log-containment boundary, beyond the one reviewed case -------------

def _log_case(tmp_path, fake_service, prepare):
	"""One start attempt whose log path `prepare` has arranged, with an
	unrelated private file that must come back untouched."""
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	log_dir = mailbox / "log"
	log_dir.mkdir(mode=0o700)
	victim = tmp_path / "operator-notes"
	victim.write_text("must remain intact\n", encoding="utf-8")
	os.chmod(victim, 0o600)
	prepare(log_dir / "owned.log", victim)
	try:
		refused = _run("start", mailbox)
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)
	return refused, victim, events


def test_start_refuses_a_hard_linked_service_log(tmp_path, fake_service):
	"""The reviewed defect through a different primitive. `O_NOFOLLOW`
	cannot see a hard link, and the descriptor is a private regular file
	by every other measure — it is simply also somebody else's file.

	Left open, the controller appends its launch boundary and the child's
	whole output into that file and starts the service as though nothing
	were wrong, which is exactly what the symlink case did."""
	refused, victim, events = _log_case(
		tmp_path, fake_service, lambda log, target: os.link(target, log))
	assert refused.returncode == 2, refused.stdout + refused.stderr
	assert "link" in _json(refused)["error"]
	assert victim.read_text(encoding="utf-8") == "must remain intact\n", \
		"the controller wrote through a hard link into an unrelated file"
	assert not events.exists(), "the controller launched anyway"


def test_start_refuses_a_symlinked_log_directory_target(tmp_path,
                                                        fake_service):
	refused, _victim, events = _log_case(
		tmp_path, fake_service,
		lambda log, _target: log.symlink_to(log.parent))
	assert refused.returncode == 2, refused.stdout + refused.stderr
	assert not events.exists()


def test_start_refuses_a_dangling_log_symlink(tmp_path, fake_service):
	"""A dangling link is the dangerous case in waiting: with `O_CREAT`
	and no `O_NOFOLLOW` the open CREATES the target, so the controller
	would quietly start writing wherever the link points."""
	refused, victim, events = _log_case(
		tmp_path, fake_service,
		lambda log, target: log.symlink_to(str(target) + ".not-yet"))
	assert refused.returncode == 2, refused.stdout + refused.stderr
	assert not (tmp_path / "operator-notes.not-yet").exists(), \
		"the refused open created the link's target"
	assert not events.exists()


def test_start_refuses_a_group_readable_service_log(tmp_path, fake_service):
	"""The retained descriptor check, which the reviewed case does not
	reach: a log an unrelated user can read is not private, whoever
	created it."""
	def prepare(log, _target):
		log.write_text("", encoding="utf-8")
		os.chmod(log, 0o640)

	refused, _victim, events = _log_case(tmp_path, fake_service, prepare)
	assert refused.returncode == 2, refused.stdout + refused.stderr
	assert "not a private regular file" in _json(refused)["error"]
	assert not events.exists()


def test_start_refuses_a_fifo_service_log(tmp_path, fake_service):
	"""The other half of the retained check: the file TYPE. A private
	FIFO passes the mode test and would block the first write."""
	refused, _victim, events = _log_case(
		tmp_path, fake_service,
		lambda log, _target: os.mkfifo(log, 0o600))
	assert refused.returncode == 2, refused.stdout + refused.stderr
	assert "not a private regular file" in _json(refused)["error"]
	assert not events.exists()


def test_an_ordinary_log_has_exactly_one_name_across_a_restart(tmp_path,
                                                               fake_service):
	"""The link guard must cost nothing legitimate: a real run's log is
	a single-named private regular file and stays one across a restart
	that appends to it."""
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	try:
		assert _run("start", mailbox).returncode == 0
		log_path = mailbox / "log" / "owned.log"
		first = os.stat(log_path)
		assert first.st_nlink == 1
		assert stat.S_IMODE(first.st_mode) & 0o077 == 0
		assert _run("stop", mailbox).returncode == 0
		assert _run("start", mailbox).returncode == 0
		again = os.stat(log_path)
		assert again.st_nlink == 1, "a restart gave the log a second name"
		assert again.st_size > first.st_size, "the restart did not append"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


# -- socket readiness is a connection, not an inode -------------------------

def test_start_refuses_when_the_service_binds_without_listening(tmp_path,
                                                               fake_service):
	"""'Cover both startup and status.' The reviewed regression proves
	the status half; this is the startup half, where a false positive is
	worse — it lets the invocation advance to DEPENDENT readiness
	producers behind a socket that cannot accept.

	The service binds the configured path and never listens, which is
	the shape a dispatcher leaves when its listener dies while the
	process lives. Note what this does NOT do: pre-creating the inode
	before `start` trips the separate refusal-to-adopt-pre-existing-
	readiness guard, so that construction refuses either way and proves
	nothing about the probe."""
	events = tmp_path / "events"
	ready = tmp_path / "service.sock"
	service = _service(
		"owned", fake_service, events,
		readiness={"type": "unix_socket", "path": str(ready)},
		extra=("--ready-socket", str(ready), "--bind-only"))
	mailbox = _mailbox(tmp_path, [service])
	try:
		refused = _run("start", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		error = _json(refused)["error"]
		assert "failed readiness" in error, \
			f"start refused for some other reason: {error}"
		# the service DID launch and bind — so the readiness failure is
		# about the probe, not about a service that never ran. (The
		# inode itself is gone by now: rollback stopped the service and
		# its handler unlinks the path.)
		assert "start owned" in events.read_text(encoding="utf-8"), \
			"the service never launched, so the probe was never tested"
		state = mailbox / "run" / "infra-state.json"
		assert not state.exists() or not _state(mailbox)["services"], \
			"a service that never became ready stayed recorded"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


def test_a_dependent_service_never_starts_behind_an_inert_socket(tmp_path,
                                                                fake_service):
	"""The consequence the review names. Dependency order means a false
	readiness answer does not merely mislabel one row — it launches the
	next service against a socket that cannot accept events."""
	events = tmp_path / "events"
	ready = tmp_path / "first.sock"
	first = _service(
		"first", fake_service, events,
		readiness={"type": "unix_socket", "path": str(ready)},
		extra=("--ready-socket", str(ready), "--bind-only"))
	second = _service("second", fake_service, events, after=("first",))
	mailbox = _mailbox(tmp_path, [first, second])
	try:
		refused = _run("start", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		error = _json(refused)["error"]
		assert "first" in error and "failed readiness" in error, error
		recorded = []
		if events.exists():
			recorded = [line for line in
			            events.read_text(encoding="utf-8").splitlines()
			            if "second" in line]
		assert not recorded, \
			"the dependent service started behind an unready socket"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


def test_a_live_listener_is_still_ready(tmp_path, fake_service):
	"""'retain the existing active-listener cases.' The connection probe
	must not make a genuinely listening service look unready — including
	across the repeated connect-and-close that every `status` performs."""
	events = tmp_path / "events"
	ready = tmp_path / "service.sock"
	service = _service(
		"owned", fake_service, events,
		readiness={"type": "unix_socket", "path": str(ready)},
		extra=("--ready-socket", str(ready)))
	mailbox = _mailbox(tmp_path, [service])
	try:
		assert _run("start", mailbox).returncode == 0
		for _repeat in range(4):
			done = _run("status", mailbox)
			assert done.returncode == 0, done.stdout + done.stderr
			assert _json(done)["services"][0]["state"] == "healthy"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


def test_an_unprobeable_socket_refuses_rather_than_reporting_unhealthy(
		tmp_path, fake_service):
	"""'unexpected errors should remain a clear non-ready/refusal rather
	than inode-based success.'

	An error that is not an ANSWER about the service — the controller
	unable to ask at all — must not be reported as `unhealthy`. That
	would assert a state it has not proved, which is the same defect as
	blessing an inode. It refuses by name instead, so the operator can
	tell "the service is down" from "I could not look"."""
	events = tmp_path / "events"
	# a path far longer than the AF_UNIX sun_path limit: connect cannot
	# even be attempted, and the errno is neither ENOENT nor ECONNREFUSED.
	ready = tmp_path / ("x" * 200 + ".sock")
	service = _service("owned", fake_service, events,
	                   readiness={"type": "unix_socket", "path": str(ready)})
	mailbox = _mailbox(tmp_path, [service])
	try:
		refused = _run("start", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		error = _json(refused)["error"]
		assert "cannot probe readiness socket" in error, error
		assert "errno" in error, "the refusal does not name the cause"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


# -- the same containment contract, everywhere the mailbox owns a file ------

def test_the_lifecycle_state_read_refuses_a_symlink(tmp_path, fake_service):
	"""`run/infra-state.json` decides which processes the controller
	believes it may signal, so it is the file where a substitution would
	matter most.

	This case was ALREADY closed — `_load_state` lstats the path first —
	and the test exists to keep it closed while that guard moves behind
	the shared helper. Stating that plainly matters: the sibling I swept
	for turned out to be protected, and reporting it as a fresh hole
	would have been a false claim about my own change."""
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	run_dir = mailbox / "run"
	run_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
	victim = tmp_path / "someone-elses-state.json"
	victim.write_text('{"services": []}\n', encoding="utf-8")
	os.chmod(victim, 0o600)
	(run_dir / "infra-state.json").symlink_to(victim)
	done = _run("status", mailbox)
	assert done.returncode == 2, done.stdout + done.stderr
	assert "not a real state file" in _json(done)["error"]
	assert victim.read_text(encoding="utf-8") == '{"services": []}\n'


def test_the_lifecycle_state_read_refuses_a_hard_link(tmp_path, fake_service):
	"""The half that was NOT closed. `lstat` cannot see a hard link, so
	the existing guard passed it: the descriptor is a private regular
	file that is simply also somebody else's file — the same primitive
	that defeated the log guard until it was closed there too."""
	events = tmp_path / "events"
	mailbox = _mailbox(tmp_path, [_service("owned", fake_service, events)])
	run_dir = mailbox / "run"
	run_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
	victim = tmp_path / "someone-elses-state.json"
	victim.write_text('{"services": []}\n', encoding="utf-8")
	os.chmod(victim, 0o600)
	os.link(victim, run_dir / "infra-state.json")
	done = _run("status", mailbox)
	assert done.returncode == 2, done.stdout + done.stderr
	assert "names" in _json(done)["error"] or "link" in _json(done)["error"]


@pytest.mark.parametrize("owned", ["lifecycle lock", "lifecycle state",
                                   "service log"])
def test_every_mailbox_owned_file_shares_one_containment_rule(owned):
	"""Three files, one rule, one implementation.

	The lock, the state and each log are all private lifecycle metadata,
	and this Work has now had the SAME containment defect reported
	against two of them separately. Stating the rule once is what stops
	a third report: a future mailbox-owned file gets it by calling the
	helper, not by remembering four flags."""
	import inspect
	import importlib.util
	spec = importlib.util.spec_from_file_location("infra", CONTROLLER)
	infra = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(infra)
	source = inspect.getsource(infra._open_owned)
	for guard in ("O_NOFOLLOW", "O_NONBLOCK", "S_ISREG", "st_nlink"):
		assert guard in source, \
			f"the shared containment rule lost its {guard} guard"
	# and every owner goes through it rather than opening for itself
	whole = inspect.getsource(infra)
	for site, flags in (("_open_log", "os.O_WRONLY | os.O_APPEND"),
	                    ("_read_json", "os.O_RDONLY"),
	                    ("MailboxLock", "os.O_RDWR")):
		body = whole[whole.index(f"def {site}" if site != "MailboxLock"
		                         else f"class {site}"):]
		body = body[:2000]
		assert "_open_owned(" in body, \
			f"{site} opens its file without the shared rule"
	assert owned in whole, f"no caller names {owned!r} in its refusals"


# -- the owned process group, beyond the one reviewed case ------------------

def test_a_grandchild_in_the_owned_session_is_terminated(tmp_path,
                                                         fake_service):
	"""Ownership is the SESSION the controller created, not one
	generation of it. A managed bridge that spawns an agent which spawns
	a helper is the same shape one level deeper, and signalling the
	group covers it for free — which is the point of signalling the
	group rather than walking a parent/child chain."""
	events = tmp_path / "events"
	child_pid_path = tmp_path / "child.pid"
	grandchild_pid_path = tmp_path / "grandchild.pid"
	service = _service(
		"parent", fake_service, events,
		extra=("--child-pid", str(child_pid_path),
		       "--grandchild-pid", str(grandchild_pid_path)))
	mailbox = _mailbox(tmp_path, [service])
	pids = []
	try:
		assert _run("start", mailbox).returncode == 0
		for path in (child_pid_path, grandchild_pid_path):
			deadline = time.monotonic() + 3
			while time.monotonic() < deadline and not path.exists():
				time.sleep(0.02)
			assert path.exists(), f"{path.name} was never written"
			pids.append(int(path.read_text(encoding="utf-8")))
		assert all(_alive(pid) for pid in pids), "the fixture did not nest"
		assert _run("stop", mailbox).returncode == 0
		for pid in pids:
			_wait_dead(pid)
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)
		for pid in pids:
			if _alive(pid):
				os.kill(pid, signal.SIGKILL)
				_wait_dead(pid)


def test_rollback_terminates_the_whole_group_too(tmp_path, fake_service):
	"""Rollback uses the same termination, so a child started by a
	service that then fails readiness must not survive the invocation
	that created it. This is the path where the exited leader is still
	this controller's own child — a zombie is a live group member, so
	without reaping it the group would never read as drained and a
	correct rollback would report failure."""
	events = tmp_path / "events"
	child_pid_path = tmp_path / "child.pid"
	ready = tmp_path / "never.sock"
	service = _service(
		"doomed", fake_service, events,
		readiness={"type": "unix_socket", "path": str(ready)},
		extra=("--child-pid", str(child_pid_path)))
	mailbox = _mailbox(tmp_path, [service])
	child_pid = None
	try:
		refused = _run("start", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		assert child_pid_path.exists(), "the service never spawned its child"
		child_pid = int(child_pid_path.read_text(encoding="utf-8"))
		_wait_dead(child_pid)
		state = mailbox / "run" / "infra-state.json"
		assert not state.exists() or not _state(mailbox)["services"], \
			"a rolled-back service stayed in lifecycle state"
	finally:
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)
		if child_pid is not None and _alive(child_pid):
			os.kill(child_pid, signal.SIGKILL)
			_wait_dead(child_pid)


def test_stop_stays_truthful_when_a_group_member_survives(tmp_path,
                                                          fake_service):
	"""'keep truthful state when any member remains.'

	The leader exits on SIGTERM but its child ignores it, so the group
	does not drain. Stop must NOT report success and must NOT drop the
	service from lifecycle state — the alternative is a controller that
	says it stopped something it did not, which is the defect one level
	along from the one just fixed."""
	events = tmp_path / "events"
	child_pid_path = tmp_path / "child.pid"
	service = _service(
		"stubborn", fake_service, events,
		extra=("--child-pid", str(child_pid_path), "--child-ignores-term"))
	mailbox = _mailbox(tmp_path, [service])
	child_pid = None
	try:
		assert _run("start", mailbox).returncode == 0
		deadline = time.monotonic() + 3
		while time.monotonic() < deadline and not child_pid_path.exists():
			time.sleep(0.02)
		child_pid = int(child_pid_path.read_text(encoding="utf-8"))
		assert _alive(child_pid)
		done = _run("stop", mailbox)
		# an incomplete stop is the controller's refusal exit, not a
		# quiet success with a warning
		assert done.returncode == 2, done.stdout + done.stderr
		payload = _json(done)
		assert payload["healthy"] is False
		assert payload["services"][0]["state"] == "group-did-not-exit", payload
		assert "incomplete stops" in payload["error"]
		assert _alive(child_pid), "the fixture's child did not ignore SIGTERM"
		assert "stubborn" in _state(mailbox)["services"], \
			"a service whose group survived was dropped from state"
	finally:
		if child_pid is not None and _alive(child_pid):
			os.kill(child_pid, signal.SIGKILL)
			_wait_dead(child_pid)
		if (mailbox / "run" / "infra-state.json").exists():
			_run("stop", mailbox)


def test_termination_never_signals_a_group_it_does_not_own(tmp_path,
                                                           fake_service):
	"""'It must not broaden into process discovery or signal a
	reused/unowned group.'

	Termination is reached only after the identity check passes, and the
	group is signalled only when the recorded pid is its OWN group and
	session leader. This exercises the second condition directly: a pid
	that is alive and matches nothing recorded must not be signalled at
	all — the test process is its own such case, and if termination
	broadened before checking, it would signal the suite's group."""
	import importlib.util
	spec = importlib.util.spec_from_file_location("infra", CONTROLLER)
	infra = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(infra)
	entry = {"pid": os.getpid(), "startTicks": 1, "argv": ["nonsense"],
	         "stopTimeoutSeconds": 1}
	result = infra._terminate(entry)
	assert result not in ("stopped", "group-did-not-exit"), result
	assert _alive(os.getpid()), "termination signalled the suite's own group"


def test_a_service_that_is_not_its_own_session_leader_is_not_broadened(
		tmp_path, fake_service):
	"""The guard's other half, proved by what SURVIVES termination.

	R4: the previous version of this test asserted the suite's own
	`sid`/`pgid` and called nothing. That made it environment-dependent
	(it fails outright in a runner that is its own session leader) and
	vacuous (removing or inverting the guard could not red it). Both
	faults are the reviewer's, and both are fixed by building the
	topology here instead of assuming one.

	A leader is started with `start_new_session=True` — the same thing
	the controller does — and spawns a child INSIDE that session. The
	child is therefore alive, owned, and matching, but is not its own
	group or session leader, which is exactly the condition the guard
	tests. Terminating the child must signal the child alone.

	The discriminating assertion is that the LEADER is still running
	afterwards. It sits in the group that `killpg` would have signalled,
	so it dies if the guard is removed or inverted and lives if the
	single-process path was taken. That group belongs to this test and
	was created by it, so an inverted guard damages nothing outside the
	topology under test — unlike using the runner's own group, which is
	why the earlier sweep of this branch was recorded as unsafe to run
	rather than performed."""
	import importlib.util
	spec = importlib.util.spec_from_file_location("infra", CONTROLLER)
	infra = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(infra)

	events = tmp_path / "events"
	child_path = tmp_path / "child.pid"
	leader = subprocess.Popen(
		[sys.executable, fake_service, "--name", "leader",
		 "--events", str(events), "--child-pid", str(child_path)],
		start_new_session=True)
	child = None
	try:
		deadline = time.monotonic() + 5
		while time.monotonic() < deadline and not child_path.exists():
			time.sleep(0.02)
		assert child_path.exists(), "the fixture never spawned its child"
		child = int(child_path.read_text(encoding="utf-8"))
		observed = infra._proc(child)
		assert observed is not None, "the child was not observable"

		# the precondition is CONSTRUCTED, not assumed of the runner
		assert observed["pgid"] == leader.pid, observed
		assert observed["sid"] == leader.pid, observed
		assert observed["pgid"] != child and observed["sid"] != child, \
			"the child leads its own group; this is not the guarded case"

		entry = {"pid": child, "startTicks": observed["startTicks"],
		         "observedArgv": observed["argv"], "stopTimeoutSeconds": 2}
		assert infra._identity(entry)[0] == "owned", \
			"the entry does not match the child, so termination would " \
			"refuse before reaching the guard"

		result = infra._terminate(entry)

		assert result == "stopped", result
		_wait_dead(child)
		assert _alive(leader.pid), \
			"termination broadened into a group the controller did not create"
	finally:
		if child is not None and _alive(child):
			os.kill(child, signal.SIGKILL)
		try:
			os.killpg(leader.pid, signal.SIGKILL)
		except (ProcessLookupError, PermissionError):
			pass
		leader.wait(timeout=5)
