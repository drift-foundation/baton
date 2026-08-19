"""W15: the DEPLOYED console paints no unclaimed marker.

W65 marked every open unclaimed row with `>` in Phase and Held. W15
superseded that — projection 8's `Current` is the exact claimant and is
blank when nobody holds the Work, so the marker restated something the
row already said.

The formatting and parity suites prove the helpers and the source-tree
render. They cannot prove what the shipped executable paints, and this
marker lives entirely in presentation: a regression here would reach an
operator's screen without failing a single unit test. So this drives the
built artifact on a real PTY and reads the row a human would see.
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

WIDTH, HEIGHT = 110, 14


def _env():
	return {key: value for key, value in os.environ.items()
	        if key != "PYTHONPATH"}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
	"""A deployed executable and an instance built THROUGH it, holding
	one handed-off unclaimed Work and one claimed Work — the two rows
	whose Held renderings used to differ by the marker."""
	target = os.path.join(str(tmp_path_factory.mktemp("w15dist")),
	                      "baton-r1")
	built = subprocess.run([sys.executable, DEPLOYER, target],
	                       capture_output=True, text=True, timeout=180)
	assert built.returncode == 0, built.stderr
	executable = json.loads(built.stdout)["executable"]

	home = str(tmp_path_factory.mktemp("w15home"))
	done = subprocess.run([executable, "init", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr
	config_path = os.path.join(home, "baton.json")
	with open(config_path, encoding="utf-8") as handle:
		document = json.load(handle)
	document["teams"] = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
		 "rev": {"members": {"bee": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	done = subprocess.run([executable, "--participant", "lang.ada",
	                       "activate", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr

	def run(viewer, *argv):
		out = subprocess.run(
			[executable, "--config", config_path,
			 "--participant", viewer] + list(argv),
			capture_output=True, text=True, timeout=120, env=_env())
		assert out.returncode == 0, out.stderr
		return json.loads(out.stdout)["result"]

	handed = run("lang.ada", "create", "team=lang", "kind=bug",
	             "title=handed off", "origin=self-initiated",
	             "classification=suspected-defect", "body=b")["work_id"]
	run("lang.ada", "claim", f"work={handed}")
	run("lang.ada", "pass", f"work={handed}", "to=rev.bug",
	    "comment=over to review")

	held = run("lang.ada", "create", "team=lang", "kind=bug",
	           "title=being worked", "origin=self-initiated",
	           "classification=suspected-defect", "body=b")["work_id"]
	run("lang.ada", "claim", f"work={held}")
	return executable, config_path


def _rows(executable, config_path, viewer="lang.ada"):
	text, status, steps = ptyharness.drive(
		config_path, viewer, [(b"", 0.6), (b"qy", 0.5)],
		columns=WIDTH, lines=HEIGHT,
		command=[sys.executable, executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-500:]
	return ptyharness.replay(steps[0], columns=WIDTH, lines=HEIGHT)


def _row(screen, title):
	for line in screen:
		if title in line:
			return line
	return None


def test_the_packaged_console_paints_no_marker_on_unclaimed_work(world):
	"""The handed-off row is open, unclaimed and timing since its
	handoff — exactly the state that used to read `>MM:SS` in Held and
	carry `>` before the phase. Both must be plain now."""
	executable, config_path = world
	screen = _rows(executable, config_path)
	unclaimed = _row(screen, "handed off")
	assert unclaimed is not None, screen
	assert ">" not in unclaimed, \
		f"the deployed console still marks unclaimed Work: {unclaimed!r}"
	# ...and it is genuinely the unclaimed row: Current is blank, which
	# is the fact that replaced the marker. Guarding this keeps the
	# check from passing vacuously against a row that got claimed.
	claimed = _row(screen, "being worked")
	assert claimed is not None, screen
	assert "lang.ada" in claimed, \
		f"the claimed row does not name its claimant: {claimed!r}"
	assert "lang.ada" not in unclaimed, \
		f"the unclaimed row names a claimant: {unclaimed!r}"


def test_the_packaged_console_paints_no_marker_anywhere(world):
	"""Whole-screen, because the marker lived in two cells and a
	regression could restore either one."""
	executable, config_path = world
	screen = _rows(executable, config_path)
	# W73: rows no longer carry the word `open` — the default table
	# holds nothing else — so the titles alone select them.
	table = [line for line in screen
	         if "handed off" in line or "being worked" in line]
	assert len(table) == 2, screen
	for line in table:
		assert ">" not in line and "!" not in line, \
			f"a retired marker reached the deployed screen: {line!r}"


def test_drawing_the_packaged_screen_writes_nothing(world):
	"""Presentation-only, proven against the artifact: opening the
	console and drawing these rows advances no authority state."""
	executable, config_path = world

	def latest():
		out = subprocess.run(
			[sys.executable, executable, "--config", config_path,
			 "--participant", "lang.ada", "events", "limit=1"],
			capture_output=True, text=True, timeout=120, env=_env())
		assert out.returncode == 0, out.stderr
		return json.loads(out.stdout)["result"]

	before = latest()
	_rows(executable, config_path)
	assert latest() == before, "drawing the console wrote to the authority"
