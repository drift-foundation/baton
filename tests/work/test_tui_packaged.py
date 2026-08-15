"""B3: the ruled scenario through the DEPLOYED artifact, on a real PTY.

The console under test is the installed `bin/baton-work` produced by the
v11-only deployer — PYTHONPATH deliberately absent, so the distribution
stands alone — and the JSON side of every claim runs through the SAME
installed executable as a separate process. The scenario is the ruled
workflow story, not a read/seen smoke test: create, include fan-out, a
request obligation, its response, a pass with a planned return, a
dependency edge, and the terminal close that unblocks the consumer — every
mutation typed into the packaged console's `:` command bar, which routes
through the one public CLI surface.
"""

from __future__ import annotations

import json
import os
import pty as _pty
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
DEPLOYER = os.path.join(REPO, "tools", "deploy_work.py")

WIDTH, HEIGHT = 110, 32


def _env():
	return {key: value for key, value in os.environ.items()
	        if key != "PYTHONPATH"}


@pytest.fixture(scope="module")
def executable(tmp_path_factory):
	target = os.path.join(str(tmp_path_factory.mktemp("b3dist")),
	                      "baton-work-r1")
	proc = subprocess.run([sys.executable, DEPLOYER, target],
	                      capture_output=True, text=True, timeout=120)
	assert proc.returncode == 0, proc.stderr
	return json.loads(proc.stdout)["executable"]


@pytest.fixture(scope="module")
def world(executable, tmp_path_factory):
	"""The instance itself is created THROUGH the installed product:
	init → edit → activate."""
	home = str(tmp_path_factory.mktemp("b3home"))
	proc = subprocess.run([executable, "init", home],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert proc.returncode == 0, proc.stderr
	config_path = os.path.join(home, "baton.json")
	with open(config_path, encoding="utf-8") as handle:
		document = json.load(handle)
	document["teams"] = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	proc = subprocess.run([executable, "--participant", "lang.ada",
	                       "activate", home], capture_output=True,
	                      text=True, timeout=120, env=_env())
	assert proc.returncode == 0, proc.stderr
	return config_path


def _json_read(executable, path, *argv, viewer):
	proc = subprocess.run(
		[executable, "--config", path, "--participant", viewer]
		+ list(argv),
		capture_output=True, text=True, timeout=120, env=_env())
	assert proc.returncode == 0, proc.stderr
	return json.loads(proc.stdout)["result"]


def _console(executable, path, viewer, commands):
	"""One packaged-console session: each command typed into the `:`
	bar; the last screen before quit is returned."""
	script = [(b"", 0.5)]
	for command in commands:
		script.append((b":" + command.encode() + b"\n", 0.9))
	script.append((b"q", 0.4))
	text, status, steps = ptyharness.drive(
		path, viewer, script, columns=WIDTH, lines=HEIGHT,
		command=[executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, \
		text[-400:]
	return [ptyharness.replay(step, columns=WIDTH, lines=HEIGHT)
	        for step in steps]


def test_the_ruled_scenario_through_the_deployed_console(executable,
		world):
	path = world

	# 1. ada CREATES the provider epic through the console command bar.
	screens = _console(executable, path, "lang.ada", [
		'create --team lang --kind bug --title "parser recovery" '
		'--origin external-report --body "crash reported"'])
	assert any("ok work_id=" in line
	           for screen in screens for line in screen), \
		"the command bar did not report the created work"
	epic = _json_read(executable, path, "home",
	                  viewer="lang.ada")["rows"][0]["id"]

	# 2. sl creates the CONSUMER work and the dependency edge; the
	# consumer is not ready while the provider is open.
	_console(executable, path, "push.sl", [
		'create --team push --kind bug --title "checkout fails" '
		'--origin external-report --body "500 at checkout"'])
	consumer = _json_read(executable, path, "home",
	                      viewer="push.sl")["rows"][0]["id"]
	_console(executable, path, "push.sl",
	         [f"block {consumer} --on {epic}"])
	detail = _json_read(executable, path, "detail", consumer,
	                    viewer="push.sl")
	assert detail["ready"] is False, "the edge did not gate readiness"

	# 3. ada fans out an INCLUDE, then a REQUEST at push's route — the
	# obligation the JSON side must see as pending.
	born = _json_read(executable, path, "work-discussions", epic,
	                  "--limit", "1", viewer="lang.ada")["rows"][0]["id"]
	_console(executable, path, "lang.ada", [
		f'say {born} --body "tracking the reports" --include "*.bug"',
		f'say {born} --body "push: can you retest?" '
		f'--request push.bug --on {epic}'])
	obligations = _json_read(executable, path, "obligations",
	                         viewer="push.sl")
	assert len(obligations) == 1
	request_seq = obligations[0]["seq"]

	# 4. sl RESPONDS through the console; the obligation clears.
	_console(executable, path, "push.sl",
	         [f'respond {request_seq} --body "retested; still crashing"'])
	assert _json_read(executable, path, "obligations",
	                  viewer="push.sl") == []

	# 5. ada PASSES the epic to push with a planned return; sl then
	# performs the CONSUMING return — Current comes back to Lang and
	# the planned Next is consumed, and the audit distinguishes the
	# outbound pass (pass + planted next) from the consuming return
	# (pass, no new next).
	_console(executable, path, "lang.ada", [
		f'say {born} --body "handing over" --on {epic} '
		f'--pass-to push.bug --set-next lang.bug'])
	detail = _json_read(executable, path, "detail", epic,
	                    viewer="lang.ada")
	assert detail["current"]["endpoint"] == "push.bug"
	assert detail["next"]["endpoint"] == "lang.bug"
	_console(executable, path, "push.sl", [
		f'say {born} --body "returning with results" --on {epic} '
		f'--pass-to lang.bug'])
	detail = _json_read(executable, path, "detail", epic,
	                    viewer="lang.ada")
	assert detail["current"]["endpoint"] == "lang.bug", \
		"the return did not bring Current back"
	assert detail["next"] is None, \
		"the consuming return did not consume the planned Next"
	events = _json_read(executable, path, "events", viewer="lang.ada")
	passes = [entry["payload"] for entry in events
	          if entry["payload"].get("pass")]
	assert [(p["pass"], p.get("set_next"), p["consumed_next"])
	        for p in passes] == \
		[("push.bug", "lang.bug", False), ("lang.bug", None, True)], \
		"the audit does not distinguish outbound pass from return"
	# The include act reached its audience: the audit records the
	# resolved endpoints the `*.bug` selector fanned out to.
	included = [entry["payload"]["include"] for entry in events
	            if entry["payload"].get("include")]
	assert {member["endpoint"] for member in included[0]} == \
		{"lang.bug", "push.bug"}, \
		"the include fan-out did not reach the expected audience"

	# 6. ada (Current again) CLOSES the epic satisfying; the consumer
	# UNBLOCKS. The closed provider renders its outcome in the console.
	_console(executable, path, "lang.ada", [
		f'close {epic} --rationale "delivered and verified" '
		f'--outcome satisfying'])
	assert _json_read(executable, path, "detail", consumer,
	                  viewer="push.sl")["ready"] is True, \
		"the terminal close did not unblock the consumer"
	screens = _console(executable, path, "lang.ada", [])
	flat = "\n".join(line for screen in screens for line in screen)
	assert "c/sat" not in flat, \
		"a closed row leaked into the default collapsed table"
	text, status, steps = ptyharness.drive(
		path, "lang.ada", [(b"z", 0.5), (b"q", 0.4)],
		columns=WIDTH, lines=HEIGHT, command=[executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	revealed = "\n".join(ptyharness.replay(steps[0], columns=WIDTH,
	                                       lines=HEIGHT))
	assert "c/sat" in revealed, \
		"the revealed closed provider does not show its outcome"

	# 7. A refused command surfaces the PUBLIC refusal in the console.
	screens = _console(executable, path, "push.sl", [
		f'close {consumer} --outcome satisfying'])
	flat = "\n".join(line for screen in screens for line in screen)
	assert "rationale" in flat, \
		"the public refusal did not reach the console status line"


def test_the_packaged_console_refuses_before_curses(executable, world):
	path = world
	text, status, _steps = ptyharness.drive(
		path, "ghost.gone", [(b"", 0.3)], command=[executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 1
	assert "not a participant" in text, text[-300:]
	assert "\x1b[?1049h" not in text, \
		"curses claimed the screen before the refusal"
