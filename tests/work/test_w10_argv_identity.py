"""W10: the recorded identity is certified at readiness, not guessed.

A shebang or `/usr/bin/env` launch rewrites argv IN PLACE. The live
four-service start recorded `/usr/bin/env node …` and `/usr/bin/env bash
…` and then compared them against the `node …` those had become — same
pid, same session, same start ticks — so every freshly created service
was classified `argv-mismatch` by the controller that had just made it.

The first correction waited 250 ms for the argv to stop changing. The
live smoke disproved it: `codex-readiness` stayed in its launcher argv
past that interval and was certified as the launcher. No interval can
know an exec chain is finished, and a longer one only moves the race.

So the launch is recorded PROVISIONALLY — owned by pid and start ticks
from the first instant, certified by nothing — and the observed argv is
captured at configured readiness, which is the manifest's own statement
that startup completed. Both sides of that boundary are pinned below: a
chain that arrives before readiness is accepted however long it takes,
and a process that rewrites its identity after readiness is refused.

Nothing here special-cases node, bash, `env`, or a command shape.
"""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import time

import pytest


REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
CONTROLLER = os.path.join(REPO, "tools", "infra.py")

# The interval the live smoke disproved. A launcher that outlives it is
# the exact shape that failed, so the regression for it is built from
# this number rather than from a number that merely looks large.
DISPROVED_SETTLE_SECONDS = 0.25


def _load_controller():
	spec = importlib.util.spec_from_file_location("infra", CONTROLLER)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


@pytest.fixture
def chain(tmp_path):
	"""A real shebang chain: `env` → `sh` → the service's interpreter.

	Three argv snapshots for one pid, which is the live shape rather
	than an imitation of it. `delay` is how long the pid sits in its
	launcher argv before the final exec — the variable the disproved
	mechanism was sensitive to and this one must not be."""
	service = tmp_path / "chain_service.py"
	service.write_text(r'''
import argparse
import os
import signal
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--events", required=True)
parser.add_argument("--exec-after", type=float)
options = parser.parse_args()

with open(options.events, "a", encoding="utf-8") as handle:
    handle.write(f"start {options.name}\n")
    handle.flush()
    os.fsync(handle.fileno())

def stop(_signum, _frame):
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
deadline = None if options.exec_after is None else time.monotonic() + options.exec_after
while True:
    if deadline is not None and time.monotonic() >= deadline:
        # A REAL later substitution: same pid, same start ticks, an argv
        # the controller never recorded.
        os.execv(sys.executable,
                 [sys.executable, "-c", "import time; time.sleep(60)"])
    time.sleep(0.02)
''', encoding="utf-8")

	def build(name, *, delay=0.05, crash=False):
		launcher = tmp_path / f"{name}-launcher"
		tail = "exit 3\n" if crash \
			else f'exec {sys.executable} {service} "$@"\n'
		launcher.write_text(
			"#!/usr/bin/env sh\n" f"sleep {delay}\n" + tail,
			encoding="utf-8")
		launcher.chmod(0o700)
		return str(launcher)

	return build


def _service(name, launcher, events, *, extra=(), stable=300, timeout=10):
	return {
		"name": name,
		"command": [launcher, "--name", name, "--events", str(events),
		            *extra],
		"after": [],
		"readiness": {"type": "process", "stableMilliseconds": stable},
		"startTimeoutSeconds": timeout,
		"stopTimeoutSeconds": 3,
	}


def _mailbox(tmp_path, services):
	mailbox = tmp_path / "mailbox"
	mailbox.mkdir(mode=0o700)
	(mailbox / "infra.json").write_text(json.dumps({
		"version": 1,
		"startTimeoutSeconds": 10,
		"stopTimeoutSeconds": 3,
		"services": services,
	}, indent=2) + "\n", encoding="utf-8")
	return mailbox


def _run(command, mailbox):
	return subprocess.run(
		[sys.executable, CONTROLLER, command, str(mailbox)],
		capture_output=True, text=True, timeout=60)


def _json(result):
	return json.loads(result.stdout)


def _state(mailbox):
	return json.loads(
		(mailbox / "run" / "infra-state.json").read_text(encoding="utf-8"))


def _alive(pid):
	return os.path.exists(f"/proc/{pid}")


def _wait_dead(pid, timeout=5):
	deadline = time.monotonic() + timeout
	while time.monotonic() < deadline and _alive(pid):
		time.sleep(0.02)
	return not _alive(pid)


def _stop(mailbox):
	if (mailbox / "run" / "infra-state.json").exists():
		_run("stop", mailbox)


def test_a_launcher_outliving_the_disproved_interval_is_still_healthy(
		tmp_path, chain):
	"""The live smoke reduced to one service, and the whole point of the
	second correction.

	This launcher holds its own argv for more than twice the interval the
	first implementation waited for, which is exactly what `codex-
	readiness` did in the field. A mechanism that certifies argv on a
	timer records the launcher here and reports `argv-mismatch`; one that
	certifies at readiness records the program that arrived."""
	delay = DISPROVED_SETTLE_SECONDS * 3
	mailbox = _mailbox(tmp_path, [
		_service("slow", chain("slow", delay=delay), tmp_path / "events",
		         stable=1500)])
	try:
		started = _run("start", mailbox)
		assert started.returncode == 0, started.stdout + started.stderr
		assert _json(started)["healthy"] is True, started.stdout

		entry = _state(mailbox)["services"]["slow"]
		assert entry["argvIdentity"] == "final", entry
		assert entry["observedArgv"][0] == sys.executable, entry
		assert entry["observedArgv"][1].endswith("chain_service.py"), entry

		checked = _run("status", mailbox)
		assert checked.returncode == 0, checked.stdout + checked.stderr
		assert _json(checked)["services"][0]["state"] == "healthy", \
			checked.stdout
	finally:
		_stop(mailbox)


def test_readiness_finalizes_the_recorded_identity(tmp_path, chain):
	"""What was recorded, not merely that it agreed with itself.

	A test that only asserted `healthy` would pass if the controller
	recorded the launcher AND compared against the launcher. The stored
	snapshot must be the program the service actually became, and it must
	say that it was certified."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained"), tmp_path / "events")])
	try:
		assert _run("start", mailbox).returncode == 0
		entry = _state(mailbox)["services"]["chained"]
		assert entry["argvIdentity"] == "final", entry
		assert entry["observedArgv"][0] == sys.executable, entry
		# the transient stages are exactly what must NOT survive
		assert "env" not in os.path.basename(entry["observedArgv"][0])
		assert not entry["observedArgv"][0].endswith("sh"), entry
		assert entry["observedArgv"] != entry["configuredArgv"], \
			"the chain never moved; this fixture proves nothing"
		# ownership is still recorded against the process the controller
		# created, not re-derived from whatever it became
		assert entry["configuredArgv"][0].endswith("chained-launcher")
		assert _state(mailbox)["version"] == 2
	finally:
		_stop(mailbox)


def test_every_configured_service_is_finalized_not_just_the_first(
		tmp_path, chain):
	"""The live failure was all four services at once, so one certified
	service is not the property. Ordered starts share one controller
	pass, and a finalization that only ran for the last launch would
	still leave the earlier ones mismatched."""
	events = tmp_path / "events"
	services = [_service(f"chained{index}", chain(f"chained{index}"), events)
	            for index in range(4)]
	mailbox = _mailbox(tmp_path, services)
	try:
		started = _run("start", mailbox)
		assert started.returncode == 0, started.stdout + started.stderr
		payload = _json(started)
		assert payload["healthy"] is True, payload
		assert len(payload["services"]) == 4, payload
		for row in payload["services"]:
			assert row["state"] == "healthy", row
		recorded = _state(mailbox)["services"]
		for index in range(4):
			entry = recorded[f"chained{index}"]
			assert entry["argvIdentity"] == "final", entry
			assert entry["observedArgv"][0] == sys.executable, entry
	finally:
		_stop(mailbox)


def test_a_post_readiness_argv_substitution_is_still_refused(tmp_path, chain):
	"""The other side of the boundary, and the reason certifying at
	readiness is not the same as 'stop checking'.

	This service reaches its configured program, is recorded healthy, and
	only then execs something else with the same pid and start ticks.
	That is a substituted identity, not a chain still arriving, and it
	must fail closed exactly as it did before this Work."""
	mailbox = _mailbox(tmp_path, [
		_service("substituted", chain("substituted"), tmp_path / "events",
		         extra=("--exec-after", "1.5"))])
	try:
		started = _run("start", mailbox)
		assert started.returncode == 0, started.stdout + started.stderr
		assert _json(started)["healthy"] is True, started.stdout
		recorded = _state(mailbox)["services"]["substituted"]
		assert recorded["argvIdentity"] == "final", recorded
		assert recorded["observedArgv"][1].endswith("chain_service.py")

		deadline = time.monotonic() + 10
		while time.monotonic() < deadline:
			payload = _json(_run("status", mailbox))
			if payload["services"][0]["state"] != "healthy":
				break
			time.sleep(0.1)
		assert payload["services"][0]["state"] == "argv-mismatch", payload
		assert payload["healthy"] is False, payload
	finally:
		_stop(mailbox)


def test_the_launch_is_owned_and_provisional_before_readiness(tmp_path, chain):
	"""Certifying at readiness opens an interval in which the process
	exists and its identity is not yet established, and a controller
	interrupted inside it must not leave an orphan.

	Observed rather than asserted about the source: `start` runs as a
	subprocess and the state file is watched while it is STILL RUNNING.
	What the file says the FIRST time it names the service is the
	discriminating fact — an owned entry that admits it is provisional,
	carrying an argv that is not yet the program that will arrive."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained", delay=0.05),
		         tmp_path / "events", stable=2000)])
	state_path = mailbox / "run" / "infra-state.json"
	running = subprocess.Popen(
		[sys.executable, CONTROLLER, "start", str(mailbox)],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	try:
		first_seen = None
		deadline = time.monotonic() + 20
		while time.monotonic() < deadline and running.poll() is None:
			try:
				document = json.loads(state_path.read_text(encoding="utf-8"))
			except (FileNotFoundError, ValueError):
				time.sleep(0.005)
				continue
			entry = document.get("services", {}).get("chained")
			if entry is not None:
				first_seen = entry
				break
			time.sleep(0.005)
		assert first_seen is not None, "the service was never recorded"
		assert first_seen["argvIdentity"] == "provisional", first_seen
		assert first_seen["pid"] > 0 and first_seen["startTicks"] > 0, \
			"the ownership record was incomplete while the launch arrived"
		assert first_seen["observedArgv"][0] != sys.executable, (
			"the first record already held the arrived program, so the "
			"controller waited before owning the process it created")
		running.wait(timeout=30)
		assert running.returncode == 0, running.stderr.read()
		assert _state(mailbox)["services"]["chained"]["argvIdentity"] \
			== "final"
	finally:
		if running.poll() is None:
			running.wait(timeout=30)
		_stop(mailbox)


def test_a_provisional_launch_survives_a_killed_controller_and_rolls_back(
		tmp_path, chain):
	"""Interruption while provisional, end to end.

	The controller is SIGKILLed mid-launch, which is the case a
	provisional record exists for. The service is still running and still
	owned, so: it is never reported healthy, `start` refuses to adopt it,
	and `stop` rolls it back on the pid and start ticks the interrupted
	controller recorded — without ever having certified its argv."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained", delay=0.05),
		         tmp_path / "events", stable=3000)])
	state_path = mailbox / "run" / "infra-state.json"
	running = subprocess.Popen(
		[sys.executable, CONTROLLER, "start", str(mailbox)],
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	pid = None
	try:
		deadline = time.monotonic() + 20
		while time.monotonic() < deadline:
			try:
				document = json.loads(state_path.read_text(encoding="utf-8"))
			except (FileNotFoundError, ValueError):
				time.sleep(0.005)
				continue
			entry = document.get("services", {}).get("chained")
			if entry is not None and entry["argvIdentity"] == "provisional":
				pid = entry["pid"]
				break
			time.sleep(0.005)
		assert pid is not None, "no provisional launch was ever recorded"
		running.kill()
		running.wait(timeout=10)
		assert _alive(pid), "the fixture lost its service before the check"

		# never adopted, never healthy
		checked = _run("status", mailbox)
		assert checked.returncode == 1, checked.stdout + checked.stderr
		row = _json(checked)["services"][0]
		assert row["state"] == "provisional", row
		assert row["healthy"] is False, row

		refused = _run("start", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		assert "refusing to adopt" in _json(refused)["error"]
		assert _alive(pid), "a refused start killed the process it refused"

		# rolled back on ownership alone
		done = _run("stop", mailbox)
		assert done.returncode == 0, done.stdout + done.stderr
		assert _json(done)["services"][0]["state"] == "stopped", done.stdout
		assert _wait_dead(pid), "the provisional service survived stop"
		assert not state_path.exists()
	finally:
		if running.poll() is None:
			running.kill()
			running.wait(timeout=10)
		if pid is not None and _alive(pid):
			os.kill(pid, signal.SIGKILL)
		_stop(mailbox)


def test_provisional_rollback_still_refuses_a_reused_pid(tmp_path, chain):
	"""Provisional rollback drops the argv requirement, so it must not
	quietly drop the reuse guard with it. Same interrupted launch, one
	tampered start-ticks field: `stop` refuses and signals nothing."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained", delay=0.05),
		         tmp_path / "events", stable=3000)])
	state_path = mailbox / "run" / "infra-state.json"
	running = subprocess.Popen(
		[sys.executable, CONTROLLER, "start", str(mailbox)],
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	pid = None
	try:
		deadline = time.monotonic() + 20
		while time.monotonic() < deadline:
			try:
				document = json.loads(state_path.read_text(encoding="utf-8"))
			except (FileNotFoundError, ValueError):
				time.sleep(0.005)
				continue
			entry = document.get("services", {}).get("chained")
			if entry is not None and entry["argvIdentity"] == "provisional":
				pid = entry["pid"]
				break
			time.sleep(0.005)
		assert pid is not None, "no provisional launch was ever recorded"
		running.kill()
		running.wait(timeout=10)

		document["services"]["chained"]["startTicks"] += 1
		state_path.write_text(json.dumps(document), encoding="utf-8")
		refused = _run("stop", mailbox)
		assert refused.returncode == 2, refused.stdout + refused.stderr
		assert _json(refused)["services"][0]["state"] == "pid-reused"
		assert _alive(pid), "the controller signalled an unowned process"
	finally:
		if running.poll() is None:
			running.kill()
			running.wait(timeout=10)
		if pid is not None and _alive(pid):
			os.kill(pid, signal.SIGKILL)
			_wait_dead(pid)


def test_a_launch_that_dies_before_readiness_keeps_the_readiness_diagnosis(
		tmp_path, chain):
	"""A crash while provisional is a readiness failure and is reported
	in the words readiness has always used.

	The first implementation of this Work grew a second failure vocabulary
	for the interval before certification, and a service that merely
	crashed was reported as one whose argv never stabilised. Inventing a
	second story about one failure takes a truthful diagnosis away from
	the operator reading it, which is the defect class this Work exists
	to remove."""
	mailbox = _mailbox(tmp_path, [
		_service("doomed", chain("doomed", delay=0.2, crash=True),
		         tmp_path / "events", stable=1000, timeout=5)])
	failed = _run("start", mailbox)
	assert failed.returncode == 2, failed.stdout + failed.stderr
	error = json.loads(failed.stderr)["error"]
	assert "failed readiness" in error, error
	assert "argv" not in error, error
	assert "rollback refused" not in error, error
	assert not (mailbox / "run" / "infra-state.json").exists()


def test_stop_still_owns_a_finalized_service(tmp_path, chain):
	"""Certification changes what is recorded, so it could quietly change
	what `stop` can prove it owns. The whole smoke has to close."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained"), tmp_path / "events")])
	assert _run("start", mailbox).returncode == 0
	entry = _state(mailbox)["services"]["chained"]
	assert entry["argvIdentity"] == "final", entry
	done = _run("stop", mailbox)
	assert done.returncode == 0, done.stdout + done.stderr
	assert _json(done)["healthy"] is True, done.stdout
	assert _wait_dead(entry["pid"]), "the finalized service survived stop"


def test_pid_reuse_is_still_fail_closed_after_finalization(tmp_path, chain):
	"""Start ticks remain the reuse guard. Finalization re-reads /proc,
	so this proves the re-read did not overwrite the recorded ticks with
	a fresh sample and bless a reused pid."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained"), tmp_path / "events")])
	try:
		assert _run("start", mailbox).returncode == 0
		state_path = mailbox / "run" / "infra-state.json"
		document = json.loads(state_path.read_text(encoding="utf-8"))
		document["services"]["chained"]["startTicks"] += 1
		state_path.write_text(json.dumps(document), encoding="utf-8")
		payload = _json(_run("status", mailbox))
		assert payload["services"][0]["state"] == "pid-reused", payload
	finally:
		_stop(mailbox)


def test_finalization_refuses_an_exited_or_reused_process(tmp_path):
	"""The two guards on the certifying read itself, which no timing
	fixture can construct reliably. Both must refuse rather than record
	an argv belonging to nothing, or to something else."""
	infra = _load_controller()
	victim = subprocess.Popen([sys.executable, "-c", "pass"])
	victim.wait()
	entry = {"name": "gone", "pid": victim.pid, "startTicks": 1,
	         "observedArgv": ["x"], "argvIdentity": "provisional"}
	with pytest.raises(infra.InfraError) as exited:
		infra._finalize_identity(str(tmp_path), {}, entry, "/tmp/log")
	assert "exited as its identity was recorded" in str(exited.value)

	alive = {"name": "self", "pid": os.getpid(), "startTicks": 999999,
	         "observedArgv": ["x"], "argvIdentity": "provisional"}
	with pytest.raises(infra.InfraError) as reused:
		infra._finalize_identity(str(tmp_path), {}, alive, "/tmp/log")
	assert "was reused" in str(reused.value)
	assert alive["argvIdentity"] == "provisional", \
		"a refused finalization still marked the entry certified"


def test_a_version_one_document_is_read_as_provisional(tmp_path, chain):
	"""The deployed lifecycle state written before this Work.

	Its `observedArgv` was recorded from the first readable cmdline, so
	it is precisely an uncertified snapshot — reading it as `final` would
	certify the one value this Work proved was never verified. It is
	read as what it is, which also gives the operator a controller path
	to recover the partial live set instead of a hand-rolled kill."""
	mailbox = _mailbox(tmp_path, [
		_service("chained", chain("chained"), tmp_path / "events")])
	pid = None
	try:
		assert _run("start", mailbox).returncode == 0
		state_path = mailbox / "run" / "infra-state.json"
		document = json.loads(state_path.read_text(encoding="utf-8"))
		pid = document["services"]["chained"]["pid"]
		# exactly what the old controller wrote: version 1, no identity
		document["version"] = 1
		del document["services"]["chained"]["argvIdentity"]
		state_path.write_text(json.dumps(document), encoding="utf-8")

		checked = _run("status", mailbox)
		assert checked.returncode == 1, checked.stdout + checked.stderr
		assert _json(checked)["services"][0]["state"] == "provisional", \
			checked.stdout

		done = _run("stop", mailbox)
		assert done.returncode == 0, done.stdout + done.stderr
		assert _wait_dead(pid), "the version 1 service survived stop"
	finally:
		if pid is not None and _alive(pid):
			os.kill(pid, signal.SIGKILL)
		_stop(mailbox)
