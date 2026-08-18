"""W25: cursor keys must work on a REAL terminal, not just in tests.

Every cursor alias in the console was written and unit-tested by
injecting `curses.KEY_UP` and friends straight into `Console.handle`.
A real terminal never sends those.

The finding first diagnosed this as the runner failing to enable keypad
translation. The implementation DISPROVED that: `curses.wrapper` calls
`stdscr.keypad(1)` before `run()` executes, so translation was on all
along. The measured cause is one layer down — `keypad(1)` emits `smkx`,
asking the terminal for APPLICATION cursor mode, and xterm's terminfo
then expects `ESC O B` for Down. A terminal left in NORMAL cursor mode
sends `ESC [ B`, which ncurses hands through as a bare 27 plus two
ordinary characters because it asked for the other spelling.

So the aliases were reachable from one kind of terminal and invisible
from the other, vi keys kept working throughout, and tests injecting
`curses.KEY_*` could not see the gap at all. See the dated amendment in
the bound FINDING.md.

These drive RAW ANSI sequences through a real PTY against the PACKAGED
artifact, in BOTH spellings. A test that calls `handle(curses.KEY_DOWN)`
cannot fail for this defect; only a terminal can.
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

WIDTH, HEIGHT = 100, 14

# The two spellings a terminal may send. `smkx` asks for the APPLICATION
# forms and xterm's terminfo decodes those; a terminal left in NORMAL
# cursor mode sends the CSI forms, which is the half that was broken.
UP, DOWN, RIGHT, LEFT = b"\x1b[A", b"\x1b[B", b"\x1b[C", b"\x1b[D"
SS3_UP, SS3_DOWN = b"\x1bOA", b"\x1bOB"


def _env():
	return {key: value for key, value in os.environ.items()
	        if key != "PYTHONPATH"}


@pytest.fixture(scope="module")
def executable(tmp_path_factory):
	target = os.path.join(str(tmp_path_factory.mktemp("w25dist")),
	                      "baton-r1")
	done = subprocess.run([sys.executable, DEPLOYER, target],
	                      capture_output=True, text=True, timeout=180)
	assert done.returncode == 0, done.stderr
	return json.loads(done.stdout)["executable"]


@pytest.fixture(scope="module")
def world(executable, tmp_path_factory):
	"""Created through the INSTALLED product, then populated with a
	parent and enough siblings for movement to be visible."""
	home = str(tmp_path_factory.mktemp("w25home"))
	done = subprocess.run([executable, "init", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr
	config_path = os.path.join(home, "baton.json")
	with open(config_path, encoding="utf-8") as handle:
		document = json.load(handle)
	document["teams"] = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	done = subprocess.run([executable, "--participant", "lang.ada",
	                       "activate", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr

	def create(title, parent=None):
		argv = [executable, "--config", config_path,
		        "--participant", "lang.ada", "create", "team=lang",
		        "kind=bug", f"title={title}", "origin=self-initiated",
		        "classification=suspected-defect", "body=b"]
		if parent:
			argv.append(f"parent={parent}")
		out = subprocess.run(argv, capture_output=True, text=True,
		                     timeout=120, env=_env())
		assert out.returncode == 0, out.stderr
		return json.loads(out.stdout)["result"]["work_id"]

	root = create("alpha root")
	create("alpha child", parent=root)
	for name in ("bravo", "charlie", "delta"):
		create(name)
	return config_path


def _steps(executable, config_path, script, quit_from_bar=False):
	"""Every intermediate screen, so a test can assert on the state a
	keystroke produced rather than only on the last one.

	The quit is deliberate: `q` reaches the console only from a
	navigation mode, so a script that ends inside the command bar sends
	Esc first — otherwise `qy` is typed as bar text and the console
	never exits."""
	tail = [(b"\x1b", 0.4)] if quit_from_bar else []
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", list(script) + tail + [(b"qy", 0.5)],
		columns=WIDTH, lines=HEIGHT,
		command=[sys.executable, executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-600:]
	return [ptyharness.replay(step, columns=WIDTH, lines=HEIGHT)
	        for step in steps]


def _screen(executable, config_path, script, quit_from_bar=False):
	"""The screen produced by the last SCRIPTED keystroke.

	Indexed from the front, not the back: the quit tail can itself
	change the view — the Esc that leaves the command bar also closes a
	detail pane — so counting back from the end would silently return
	the screen after the teardown rather than the one under test."""
	steps = _steps(executable, config_path, script,
	               quit_from_bar=quit_from_bar)
	return steps[len(script) - 1] if script else steps[0]


def _header(screen):
	"""The detail header names the EXACT selected Work, so it is the
	unambiguous way to say which row the cursor was on."""
	for line in screen:
		if "(W" in line and "[open" in line:
			return line.strip()
	return None


# -- the property the unit tests could not reach ----------------------------

@pytest.mark.serial
@pytest.mark.parametrize("vi,raw", [
	(b"j", DOWN), (b"k", UP),          # normal mode (DECCKM off)
	(b"j", SS3_DOWN), (b"k", SS3_UP),  # application mode (what smkx asks for)
])
def test_raw_cursor_sequences_move_the_selection_like_vi(executable, world,
                                                         vi, raw):
	"""Same starting screen, same number of presses, same visible
	landing row — proven by opening detail, which names the exact Work."""
	by_vi = _header(_screen(executable, world,
	                        [(b"j", 0.4), (vi, 0.4), (b"\r", 0.6)],
	                        quit_from_bar=True))
	by_raw = _header(_screen(executable, world,
	                         [(b"j", 0.4), (raw, 0.4), (b"\r", 0.6)],
	                         quit_from_bar=True))
	assert by_vi is not None, "the vi run never opened a detail header"
	assert by_raw == by_vi, \
		f"cursor key landed elsewhere than {vi!r}: {by_raw!r} vs {by_vi!r}"


@pytest.mark.serial
def test_a_raw_left_sequence_returns_from_a_drill(executable, world):
	"""The left/right boundary: `u` re-roots the window on the selected
	Work and LEFT pops back out, the same as Esc. If the sequence were
	not decoded, the console would stay drilled."""
	drilled = _screen(executable, world, [(b"u", 0.6)])
	returned = _screen(executable, world, [(b"u", 0.6), (LEFT, 0.6)])
	top = _screen(executable, world, [])
	assert drilled != top, "`u` did not visibly re-root the window"
	assert returned == top, \
		"a raw LEFT sequence did not return from the drill"


@pytest.mark.serial
def test_bare_escape_still_cancels_promptly(executable, world):
	"""Keypad translation makes ncurses wait after a bare ESC to see
	whether a sequence follows. With the default one-second delay that
	would make cancelling feel broken, so the runner shortens it — and
	Esc must still leave the command bar."""
	# ONE session, so the two screens differ only by the Esc between
	# them — and Esc is timed, which is the delay this test guards.
	steps = _steps(executable, world,
	               [(b":", 0.5), (b"help", 0.4), (b"\x1b", 0.5)])
	opened = "\n".join(steps[1])
	cancelled = "\n".join(steps[2])
	assert ":help" in opened, f"the command bar did not take input: {opened}"
	assert ":help" not in cancelled, \
		f"bare Esc did not cancel the command bar: {cancelled}"


@pytest.mark.serial
def test_cursor_input_advances_no_authority_state(executable, world):
	"""Navigation is observation-only: moving with the cursor keys must
	not claim, mark seen, or otherwise write."""
	def events():
		out = subprocess.run(
			[sys.executable, executable, "--config", world,
			 "--participant", "lang.ada", "events", "limit=1"],
			capture_output=True, text=True, timeout=120, env=_env())
		assert out.returncode == 0, out.stderr
		return json.loads(out.stdout)["result"]

	before = events()
	_screen(executable, world,
	        [(DOWN, 0.3), (DOWN, 0.3), (UP, 0.3), (RIGHT, 0.3), (LEFT, 0.3)])
	assert events() == before, "cursor navigation wrote to the authority"


# -- the refresh deadline, under the new escape path ------------------------

@pytest.mark.serial
def test_the_refresh_survives_a_stream_of_raw_cursor_sequences(executable,
                                                               world):
	"""Acceptance item 3, exercised through the path the fix added.

	Every raw cursor sequence now costs a short blocking peek for the
	byte after ESC. The refresh deadline is wall-clock, so a stream of
	them must neither postpone nor starve it — and the existing
	continuous-input test uses `j`/`k`, which never enters the peek at
	all.

	An external participant commits a Work mid-session; it must appear
	on schedule while the cursor keys keep arriving."""
	import threading

	def external():
		done = subprocess.run(
			[sys.executable, executable, "--config", world,
			 "--participant", "lang.ada", "create", "team=lang",
			 "kind=bug", "title=surprise",
			 "origin=external-report",
			 "classification=suspected-defect", "body=b"],
			capture_output=True, text=True, timeout=120, env=_env())
		assert done.returncode == 0, done.stderr

	# late enough that several peeked keystrokes precede it, so the
	# opening screen genuinely predates the external commit
	timer = threading.Timer(2.0, external)
	timer.start()
	try:
		# A cursor sequence every 0.3s across a 0.5s refresh window:
		# several deadlines fall between keystrokes, and each keystroke
		# passes through the ESC peek.
		script = [(DOWN, 0.3), (UP, 0.3), (DOWN, 0.3), (UP, 0.3),
		          (DOWN, 0.3), (UP, 0.3), (DOWN, 0.3), (UP, 0.3),
		          (DOWN, 0.3), (UP, 0.6), (b"qy", 0.5)]
		# drive() appends `--config … --participant … tui` itself, so a
		# faster refresh has to be appended AFTER that verb — the same
		# argv-tail trick the auto-refresh suite uses, aimed at the
		# packaged artifact rather than the source tree.
		helper = ("import sys,runpy;"
		          f"sys.argv = [{executable!r}] + sys.argv[1:] "
		          "+ ['refresh=0.5'];"
		          f"runpy.run_path({executable!r}, run_name='__main__')")
		text, status, steps = ptyharness.drive(
			world, "lang.ada", script, columns=WIDTH, lines=HEIGHT,
			command=[sys.executable, "-c", helper], settle=0.6)
	finally:
		timer.join()
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-500:]
	# It must APPEAR, not merely be present: absent from the first
	# painted screen (the external commit lands a second later) and on
	# screen by the end. Without the first half this would pass even if
	# the refresh never ran.
	first = ptyharness.replay(steps[0], columns=WIDTH, lines=HEIGHT)
	final = ptyharness.replay(steps[-2], columns=WIDTH, lines=HEIGHT)
	assert not any("surprise" in line for line in first), \
		f"the external Work was already on the opening screen: {first}"
	assert any("surprise" in line for line in final), \
		("the externally created Work never appeared while raw cursor "
		 f"sequences were arriving: {final}")
