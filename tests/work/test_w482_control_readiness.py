"""W482: readiness may ASK a service, not only reach it.

`work/records/2026/08/finding-dispatcher-target-readiness/`. During the
975af64 cutover the controller reported the Codex dispatcher healthy
while its configured tuner target could not resume at all:
`no rollout found for thread id …`. The readiness producer went on
forwarding W321 into a queue nothing would drain, and W321 stayed
queued and overdue. The failure was in `codex-dispatcher.log`, not in
`just status`.

A connection was never the whole contract for that service: the
dispatcher begins listening before its targets resume and keeps
listening when one is `notLoaded`. It already exposes the stronger fact
through the same socket — `{"control":"status"}` answers `ready` only
when every configured target is connected and loaded — and nothing
asked it.

The ruling: `unix_socket` readiness gains optional `request`/`expect`,
both together or neither; `expect` matches required top-level reply
fields and grows no expression language; every way a reply can fail to
arrive or fail to match is "not ready yet", decided by the timeouts
that already exist.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
CONTROLLER = os.path.join(REPO, "tools", "infra.py")

pytestmark = pytest.mark.skipif(not os.path.isdir("/proc"),
                                reason="needs /proc")


def _fake_dispatcher(path):
	"""A service in the dispatcher's shape: it listens immediately and
	answers `{"control":"status"}` — with what, and after how long, is
	the test's business."""
	path.write_text('''
import argparse, json, os, signal, socket, sys, threading, time
parser = argparse.ArgumentParser()
parser.add_argument("--socket", required=True)
parser.add_argument("--ready-after", type=float, default=0.0)
parser.add_argument("--reply", default="status")
parser.add_argument("--flip-at", type=float, default=None)
options = parser.parse_args()

started = time.monotonic()

def snapshot():
    elapsed = time.monotonic() - started
    ready = elapsed >= options.ready_after
    if options.flip_at is not None and elapsed >= options.flip_at:
        ready = False
    return {"ready": ready, "targets": {"baton-tuner": {"loaded": ready}},
            "globalQueueDepth": 0}

listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(options.socket)
listener.listen()

def serve():
    while True:
        try:
            client, _ = listener.accept()
        except OSError:
            return
        try:
            client.settimeout(2)
            client.recv(65536)
            if options.reply == "status":
                client.sendall((json.dumps(snapshot()) + "\\n").encode())
            elif options.reply == "garbage":
                client.sendall(b"not json at all\\n")
            elif options.reply == "array":
                client.sendall(b"[1, 2, 3]\\n")
            elif options.reply == "truncated":
                client.sendall(b'{"ready": tr')
            elif options.reply == "huge":
                client.sendall(b'{"ready": true, "pad": "' + b"x" * 200000)
            elif options.reply == "silent":
                time.sleep(5)
            elif options.reply == "close":
                pass
            elif options.reply == "numeric":
                client.sendall(b'{"ready": 1}\\n')
            elif options.reply == "drip":
                for byte in b'{"ready": true}\\n':
                    client.sendall(bytes([byte]))
                    time.sleep(0.2)
        except OSError:
            pass
        finally:
            try:
                client.close()
            except OSError:
                pass

threading.Thread(target=serve, daemon=True).start()

def stop(*_args):
    try:
        os.unlink(options.socket)
    except FileNotFoundError:
        pass
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
while True:
    time.sleep(0.02)
''', encoding="utf-8")
	return str(path)


@pytest.fixture()
def rig(tmp_path):
	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	return {"mailbox": mailbox,
	        "service": _fake_dispatcher(tmp_path / "dispatcher.py"),
	        "socket": str(tmp_path / "events.sock"),
	        "tmp": tmp_path}


def _manifest(rig, *, readiness=None, extra=(), timeout=4):
	return {
		"version": 1,
		"startTimeoutSeconds": timeout,
		"stopTimeoutSeconds": 2,
		"services": [{
			"name": "dispatcher",
			"command": [sys.executable, rig["service"],
			            "--socket", rig["socket"], *extra],
			"readiness": readiness if readiness is not None else {
				"type": "unix_socket", "path": rig["socket"],
				"request": {"control": "status"},
				"expect": {"ready": True}},
			"startTimeoutSeconds": timeout,
			"stopTimeoutSeconds": 2,
		}],
	}


def _write(rig, document):
	(rig["mailbox"] / "infra.json").write_text(
		json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _run(command, rig, timeout=30):
	return subprocess.run(
		[sys.executable, CONTROLLER, command, str(rig["mailbox"])],
		capture_output=True, text=True, timeout=timeout)


def _json(done):
	return json.loads(done.stdout if done.stdout else done.stderr)


# -- the healthy path ---------------------------------------------------------

def test_a_dispatcher_that_answers_ready_starts(rig):
	_write(rig, _manifest(rig))
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		assert _json(done)["healthy"] is True
		status = _run("status", rig)
		assert status.returncode == 0
		assert _json(status)["services"][0]["state"] == "healthy"
	finally:
		_run("stop", rig)


def test_a_slow_target_holds_startup_and_then_succeeds(rig):
	"""Ruling 3: a target slow to resume holds startup unready for the
	existing service timeout, and loading inside that window succeeds."""
	_write(rig, _manifest(rig, extra=["--ready-after", "1.0"], timeout=6))
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		assert _json(done)["healthy"] is True
	finally:
		_run("stop", rig)


# -- the defect this Work exists for -----------------------------------------

def test_a_listening_dispatcher_with_an_unloaded_target_is_not_ready(rig):
	"""The cutover, reproduced: the socket accepts from the first
	instant and the target never loads."""
	_write(rig, _manifest(rig, extra=["--ready-after", "3600"], timeout=2))
	done = _run("start", rig)
	assert done.returncode != 0, done.stdout
	assert "failed readiness" in (done.stdout + done.stderr)
	assert not (rig["mailbox"] / "run" / "infra-state.json").exists(), \
		"a dispatcher that never loaded its target was left running"


def test_connection_only_readiness_would_have_called_it_healthy(rig):
	"""The same service, the same instant, the OLD contract — kept as a
	live comparison so the difference this Work makes stays visible."""
	_write(rig, _manifest(
		rig, extra=["--ready-after", "3600"],
		readiness={"type": "unix_socket", "path": rig["socket"]}))
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		assert _json(done)["healthy"] is True, \
			"connection-only readiness stopped accepting a listening socket"
	finally:
		_run("stop", rig)


def test_a_target_lost_after_startup_makes_status_unhealthy(rig):
	"""Ruling 3's second half: later `status` repeats the query, and a
	target that becomes unloadable makes the stack unhealthy without
	Baton killing or restarting anything."""
	_write(rig, _manifest(rig, extra=["--flip-at", "0.5"], timeout=4))
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
		import time as _time
		_time.sleep(0.8)
		status = _run("status", rig)
		assert status.returncode != 0
		payload = _json(status)
		assert payload["healthy"] is False
		assert payload["services"][0]["state"] == "unhealthy"
		# and the process is still exactly where it was
		assert payload["services"][0]["pid"] > 0
		assert os.path.exists(f"/proc/{payload['services'][0]['pid']}")
	finally:
		_run("stop", rig)


# -- every way a reply can fail ----------------------------------------------

@pytest.mark.parametrize("reply", ["garbage", "array", "truncated", "huge",
                                   "silent", "close"])
def test_a_reply_that_is_not_an_answer_fails_closed(rig, reply):
	_write(rig, _manifest(rig, extra=["--reply", reply], timeout=2))
	done = _run("start", rig)
	assert done.returncode != 0, (reply, done.stdout)
	assert "failed readiness" in (done.stdout + done.stderr), reply


def test_a_mismatched_field_fails_closed(rig):
	_write(rig, _manifest(rig, extra=["--ready-after", "3600"], timeout=2))
	document = json.loads(
		(rig["mailbox"] / "infra.json").read_text(encoding="utf-8"))
	document["services"][0]["readiness"]["expect"] = {"ready": False}
	_write(rig, document)
	# the service answers ready:false, so THIS expectation matches
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
	finally:
		_run("stop", rig)


def test_a_field_the_reply_does_not_carry_fails_closed(rig):
	document = _manifest(rig, timeout=2)
	document["services"][0]["readiness"]["expect"] = {"absent": True}
	_write(rig, document)
	done = _run("start", rig)
	assert done.returncode != 0
	assert "failed readiness" in (done.stdout + done.stderr)


def test_a_boolean_expectation_does_not_accept_a_number(rig):
	"""JSON booleans and numbers are different types even though Python
	compares `True == 1`. A numeric readiness value is a mismatch, not a
	successful boolean assertion."""
	_write(rig, _manifest(rig, extra=["--reply", "numeric"], timeout=1))
	done = _run("start", rig)
	assert done.returncode != 0, done.stdout + done.stderr
	assert "failed readiness" in (done.stdout + done.stderr)


def test_a_slow_drip_cannot_outlive_the_probe_deadline(rig):
	"""A socket inactivity timeout is not a bounded exchange: one byte
	inside every timeout window can otherwise hold `_ready` beyond the
	service's complete startup deadline and then report success."""
	_write(rig, _manifest(rig, extra=["--reply", "drip"], timeout=1))
	started = time.monotonic()
	done = _run("start", rig, timeout=8)
	elapsed = time.monotonic() - started
	assert done.returncode != 0, done.stdout + done.stderr
	assert elapsed < 2.5, f"one readiness exchange held startup for {elapsed:.2f}s"
	assert "failed readiness" in (done.stdout + done.stderr)


def test_extra_diagnostic_fields_are_welcome(rig):
	"""The reply carries `targets` and `globalQueueDepth` beside
	`ready`; matching required TOP-LEVEL fields must not mean matching
	the whole document."""
	_write(rig, _manifest(rig))
	done = _run("start", rig)
	try:
		assert done.returncode == 0, done.stdout + done.stderr
	finally:
		_run("stop", rig)


# -- the manifest surface -----------------------------------------------------

def test_request_and_expect_are_configured_together(rig):
	for partial in ({"request": {"control": "status"}},
	                {"expect": {"ready": True}}):
		document = _manifest(rig)
		document["services"][0]["readiness"] = {
			"type": "unix_socket", "path": rig["socket"], **partial}
		_write(rig, document)
		done = _run("status", rig)
		assert done.returncode == 2, partial
		assert "together or not at all" in _json(done)["error"], partial


def test_an_empty_expectation_refuses(rig):
	document = _manifest(rig)
	document["services"][0]["readiness"]["expect"] = {}
	_write(rig, document)
	done = _run("status", rig)
	assert done.returncode == 2
	assert "at least one field" in _json(done)["error"]


def test_a_nested_expectation_refuses(rig):
	"""This version matches top-level fields and deliberately grows no
	expression language."""
	document = _manifest(rig)
	document["services"][0]["readiness"]["expect"] = {
		"targets": {"baton-tuner": {"loaded": True}}}
	_write(rig, document)
	done = _run("status", rig)
	assert done.returncode == 2
	assert "must be a string, number, boolean or null" in _json(done)["error"]


def test_connection_only_remains_a_valid_form(rig):
	document = _manifest(rig, readiness={"type": "unix_socket",
	                                     "path": rig["socket"]})
	_write(rig, document)
	done = _run("status", rig)
	assert done.returncode == 1, done.stdout + done.stderr
	assert _json(done)["services"][0]["state"] == "stopped"


def test_the_example_dispatcher_asks_for_ready():
	example = json.loads(open(os.path.join(REPO, "conf",
	                                       "infra.example.json"),
	                          encoding="utf-8").read())
	dispatcher = next(service for service in example["services"]
	                  if service["name"] == "codex-dispatcher")
	assert dispatcher["readiness"]["request"] == {"control": "status"}
	assert dispatcher["readiness"]["expect"] == {"ready": True}


def test_stop_ownership_does_not_depend_on_readiness(rig):
	"""Ruling: stop stays process/argv based. A service whose readiness
	answer has gone wrong is still owned and still stoppable."""
	_write(rig, _manifest(rig, extra=["--flip-at", "0.3"], timeout=4))
	assert _run("start", rig).returncode == 0
	state = json.loads((rig["mailbox"] / "run" / "infra-state.json")
	                   .read_text(encoding="utf-8"))
	pid = state["services"]["dispatcher"]["pid"]
	import time as _time
	_time.sleep(0.5)
	done = _run("stop", rig)
	assert done.returncode == 0, done.stdout + done.stderr
	assert not os.path.exists(f"/proc/{pid}")


def test_the_setup_guide_documents_the_control_form():
	import pathlib
	prose = " ".join((pathlib.Path(REPO) / "docs" / "BATON-SETUP.md")
	                 .read_text(encoding="utf-8").split())
	assert '"request"' in prose and '"expect"' in prose
	assert "EVERY configured target" in prose
