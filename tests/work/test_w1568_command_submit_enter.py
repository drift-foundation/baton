"""W1568: an Enter that submits a `:` command stays in command mode.

`work/records/2026/08/finding-command-submit-opens-next-job/`. From the
Jobs table with a Job selected, opening the one-line bar with `:`,
typing any command and pressing Enter executed the command AND opened
Work detail on the selected row. The operator submitted a command; they
never issued the Jobs-view Enter action.

`Console.handle()`/`_command_key()` were never wrong: they consume the
submission and close the bar. The crossover is one layer below them.
A terminal in NEW LINE mode (LNM) transmits `CR LF` for ONE Return, and
ncurses' default `nl()` sets the tty's ICRNL, so the `CR` becomes an
`LF` before the console reads it. What arrived was two IDENTICAL Enter
keys — byte-identical to two deliberate Returns — the first submitting
the command and the second falling straight through to Jobs navigation.

That is why every unit test passed: injecting one `curses.KEY_ENTER`
into `handle` cannot fail for this defect, and under `nl()` no handler
could have told the two cases apart in the first place. The correction
selects `nonl()` so `CR` survives as `13`, and decodes the `CR LF` pair
back into the one keystroke the operator made.

The decode is not a debounce, and these prove the difference: two
deliberate Returns arrive as `13 13` and stay two Enters, so a later
intentional Enter still opens the selected Job.
"""

from __future__ import annotations

import json
import os
import pty as _pty
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui import app as tui                         # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__))))
DEPLOYER = os.path.join(REPO, "tools", "deploy_work.py")

WIDTH, HEIGHT = 100, 20

# What a terminal sends for one Return. `CR` is the ordinary spelling;
# `CR LF` is what a terminal in NEW LINE mode sends for the SAME single
# keypress, and it is the spelling this Work exists to decode.
CR = b"\r"
LF = b"\n"
CRLF = b"\r\n"


# -- the terminal-level evidence --------------------------------------------

def _env():
	return {key: value for key, value in os.environ.items()
	        if key != "PYTHONPATH"}


@pytest.fixture(scope="module")
def executable(tmp_path_factory):
	"""The PACKAGED artifact, following W25: the defect is a property of
	the shipped runner's input boundary, so the evidence drives what an
	operator actually launches."""
	target = os.path.join(str(tmp_path_factory.mktemp("w1568dist")),
	                      "baton-r1")
	done = subprocess.run([sys.executable, DEPLOYER, target],
	                      capture_output=True, text=True, timeout=180)
	assert done.returncode == 0, done.stderr
	return json.loads(done.stdout)["executable"]


@pytest.fixture(scope="module")
def world(executable, tmp_path_factory):
	"""Two open Jobs through the INSTALLED product, so "the selected
	Job" and "some other Job" are distinguishable rows."""
	home = str(tmp_path_factory.mktemp("w1568home"))
	done = subprocess.run([executable, "init", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr
	config_path = os.path.join(home, "baton.json")
	with open(config_path, encoding="utf-8") as handle:
		document = json.load(handle)
	document["teams"] = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})["teams"]
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	done = subprocess.run([executable, "--participant", "lang.ada",
	                       "activate", f"directory={home}"],
	                      capture_output=True, text=True, timeout=120,
	                      env=_env())
	assert done.returncode == 0, done.stderr
	jobs = {}
	for title in ("alpha job", "bravo job"):
		done = subprocess.run(
			[executable, "--config", config_path, "--participant",
			 "lang.ada", "create", "team=lang", "kind=bug",
			 f"title={title}", "origin=self-initiated",
			 "classification=suspected-defect", "body=b"],
			capture_output=True, text=True, timeout=120, env=_env())
		assert done.returncode == 0, done.stderr
		jobs[title] = json.loads(done.stdout)["result"]["work_id"]
	return {"config": config_path, "jobs": jobs}


def _steps(executable, config_path, script, leave=b""):
	"""`leave` is whatever the script's own mode needs before `q` means
	quit again: `q` reaches the console only from a navigation mode, so
	a script ending in the command bar sends Esc first, and one ending
	in a batch buffer that still holds text answers its discard prompt
	too."""
	tail = [(leave, 0.4)] if leave else []
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", list(script) + tail + [(b"qy", 0.5)],
		columns=WIDTH, lines=HEIGHT,
		command=[sys.executable, executable])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-600:]
	return [ptyharness.replay(step, columns=WIDTH, lines=HEIGHT)
	        for step in steps]


def _in_detail(screen):
	"""Work detail is unmistakable: it is the only view that paints the
	Messages/Events tab bar."""
	return any("[Messages]" in line for line in screen)


def _detail_header(screen):
	for line in screen:
		if "(W" in line and "[open" in line:
			return line.strip()
	return None


def _bottom(screen):
	rows = [line for line in screen if line.strip()]
	return rows[-1] if rows else ""


pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.mark.serial
@pytest.mark.parametrize("command,kind,expected", [
	("summary", "read-only", "ok"),
	("claim work={alpha}", "mutation", "ok"),
	("bogusverb", "refused", "unknown command"),
	("filter phase=queued", "local", "filter:"),
])
def test_submitting_a_command_never_leaves_the_jobs_view(
		executable, world, command, kind, expected):
	"""The one property the defect broke, across every shape of command
	the acceptance boundary names: a submission is not a Jobs Enter.

	The command must still RUN — a fix that swallowed the submission
	itself would pass a bare "we are still in Jobs" assertion — so the
	brief or refusal is asserted beside the view."""
	command = command.format(alpha=world["jobs"]["alpha job"])
	steps = _steps(executable, world["config"],
	               [(b":", 0.4), (command.encode(), 0.4), (CRLF, 1.2)])
	after = steps[2]
	assert not _in_detail(after), \
		f"the {kind} submission opened Work detail:\n" + "\n".join(after)
	assert expected in _bottom(after), _bottom(after)


@pytest.mark.serial
def test_the_submission_survives_the_refresh_it_causes(executable, world):
	"""A command that changes the projection legitimately refreshes and
	may move the selected row. That refresh must not finish the job the
	stray Enter started — so this waits past the 2s timer deadline with
	no further input at all."""
	bravo = world["jobs"]["bravo job"]
	steps = _steps(executable, world["config"],
	               [(b":", 0.4),
	                (f"classify work={bravo} as=confirmed-defect".encode(),
	                 0.4),
	                (CRLF, 3.0)])
	assert not _in_detail(steps[2]), "\n".join(steps[2])
	assert any("bravo job" in line for line in steps[2]), "\n".join(steps[2])


@pytest.mark.serial
def test_a_later_deliberate_enter_still_opens_the_selected_job(
		executable, world):
	"""The correction must not cost the operator the Jobs Enter action.

	Submitted, then moved, then Enter — and the row that opens is the
	one the cursor is on, not the one that was selected when the command
	ran."""
	steps = _steps(executable, world["config"],
	               [(b":", 0.4), (b"summary", 0.4), (CRLF, 1.0),
	                (b"j", 0.4), (CRLF, 1.0)])
	assert not _in_detail(steps[2]), "the submission opened detail"
	opened = steps[4]
	assert _in_detail(opened), \
		"a deliberate Enter after a command no longer opens the Job:\n" \
		+ "\n".join(opened)
	assert world["jobs"]["bravo job"] in (_detail_header(opened) or ""), \
		_detail_header(opened)


@pytest.mark.serial
@pytest.mark.parametrize("submit", [CR, LF, CRLF])
def test_every_return_spelling_submits_exactly_once(executable, world,
                                                    submit):
	"""The three spellings a terminal may use for one Return all mean
	one Return. The bare forms were already right; `CR LF` is the one
	that was read as two."""
	steps = _steps(executable, world["config"],
	               [(b":", 0.4), (b"summary", 0.4), (submit, 1.2)])
	assert not _in_detail(steps[2]), "\n".join(steps[2])
	assert "ok" in _bottom(steps[2]), _bottom(steps[2])


@pytest.mark.serial
def test_two_deliberate_returns_are_still_two_returns(executable, world):
	"""The decode is a PAIR decode, not a suppression — the distinction
	the required behaviour turns on.

	The batch buffer counts Returns out loud: each one opens a new line,
	so `CR LF` inserting ONE line and `CR CR` inserting TWO says exactly
	that a doubled gesture collapses while a doubled INTENT does not."""
	one = _steps(executable, world["config"],
	             [(b"::a", 0.4), (CRLF, 0.4), (b"b", 0.5)],
	             leave=b"\x1by")[2]
	two = _steps(executable, world["config"],
	             [(b"::a", 0.4), (CR + CR, 0.4), (b"b", 0.5)],
	             leave=b"\x1by")[2]
	assert _batch_gap(one) == 1, "\n".join(one)
	assert _batch_gap(two) == 2, "\n".join(two)


def _batch_gap(screen):
	"""How many buffer lines the Returns opened between `a` and `b`.

	Batch lines paint a three-cell state mark and then their text, and
	an EMPTY line paints nothing at all — so the lines are counted by
	the distance between the two that carry text, which an empty row
	cannot hide."""
	rows = {}
	for number, line in enumerate(screen):
		if len(line) > 3 and line[:3] == "   " and line[3] in "ab":
			rows[line[3]] = number
	assert set(rows) == {"a", "b"}, "\n".join(screen)
	return rows["b"] - rows["a"]


@pytest.mark.serial
def test_bare_escape_still_cancels_the_bar_promptly(executable, world):
	"""`nonl()` moves the tty's ICRNL bit, which is on the same termios
	word the escape peek depends on. W25's contract is re-proved here so
	this Work cannot quietly cost it."""
	steps = _steps(executable, world["config"],
	               [(b":", 0.4), (b"summary", 0.4), (b"\x1b", 0.6)])
	assert not _in_detail(steps[2]), "\n".join(steps[2])
	assert ":summary" not in "\n".join(steps[2]), \
		"Esc no longer cancels the command bar:\n" + "\n".join(steps[2])


# -- the decode itself, with the console's own state -------------------------

class Terminal:
	"""The post-`nonl()` byte stream, as `_read_key` reads it.

	`nonl()` is what keeps `CR` at 13, so a queue of 13s and 10s is
	exactly what the real screen hands back. `curses.ungetch` is the
	terminal's own pushback FIFO, so the fake owns it too — a test that
	let it reach an uninitialized ncurses would prove nothing about
	where a pushed-back key goes."""

	def __init__(self, keys):
		self.keys = list(keys)
		self.timeouts = []

	def timeout(self, milliseconds):
		self.timeouts.append(milliseconds)

	def getch(self):
		return self.keys.pop(0) if self.keys else -1

	def ungetch(self, key):
		self.keys.insert(0, key)


def _decode(monkeypatch, keys):
	"""Every logical keystroke `_read_key` finds in one byte stream."""
	terminal = Terminal(keys)
	monkeypatch.setattr(tui.curses, "ungetch", terminal.ungetch)
	decoded = []
	while terminal.keys:
		decoded.append(tui._read_key(terminal))
	return decoded


ENTER = 10
RETURN = 13


def test_a_cr_lf_pair_decodes_to_one_enter(monkeypatch):
	assert _decode(monkeypatch, [RETURN, 10]) == [RETURN]


def test_two_returns_decode_to_two_enters(monkeypatch):
	assert _decode(monkeypatch, [RETURN, RETURN]) == [RETURN, RETURN]


def test_a_bare_line_feed_is_still_one_enter(monkeypatch):
	assert _decode(monkeypatch, [ENTER, ENTER]) == [ENTER, ENTER]


def test_whatever_follows_a_return_is_handed_on_untouched(monkeypatch):
	"""The peek pushes back anything that is not the paired `LF`, so
	typing straight through a Return loses nothing."""
	assert _decode(monkeypatch, [RETURN, ord("j")]) == [RETURN, ord("j")]
	assert _decode(monkeypatch, [RETURN, 27]) == [RETURN, 27]


def test_the_escape_decode_still_reaches_read_key(monkeypatch):
	import curses
	assert _decode(monkeypatch, [27, ord("["), ord("B")]) == [curses.KEY_DOWN]


@pytest.fixture()
def console(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	jobs = {}
	for title in ("alpha job", "bravo job"):
		jobs[title] = tr.create_work(
			store, team="lang", kind="bug", title=title,
			origin="external-report", classification="suspected-defect",
			author="ada", body="the opener")["work_id"]
	console = Console(store, "lang", "ada", config_path=config_path)
	console.jobs = jobs
	yield console
	store.close()


def _submit(monkeypatch, console, command, submit):
	"""Type a command into the bar and submit it through the REAL
	decode — the same function the runner's loop calls."""
	console.handle(ord(":"))
	for character in command:
		console.handle(ord(character))
	for key in _decode(monkeypatch, submit):
		console.handle(key)


@pytest.mark.parametrize("command", ["summary", "claim work={alpha}",
                                     "bogusverb"])
def test_the_console_state_stays_in_jobs_across_the_pair(monkeypatch,
                                                         console, command):
	"""Acceptance 2 and 3 in the console's own terms: `mode` and
	`detail_work` after a success, a mutation and a refusal."""
	command = command.format(alpha=console.jobs["alpha job"])
	_submit(monkeypatch, console, command, [RETURN, 10])
	assert console.command is None, "the bar did not close"
	assert console.mode == "table", console.mode
	assert console.detail_work is None, console.detail_work
	assert console.status, "the command did not report an outcome"


def test_the_undecoded_pair_is_the_defect_the_reader_now_prevents(console):
	"""The defect itself, stated as a property rather than trusted from
	the report — and the argument for where the fix belongs.

	This feeds what `nl()` used to deliver for one Return in NEW LINE
	mode: two bare `10`s. The first submits, the second is a Jobs Enter
	and opens Work detail. Note that no `monkeypatch` and no decode is
	involved, because there is nothing here to decide with: by the time
	`handle` sees them the two keys are LITERALLY EQUAL, which is why
	the correction has to be at the reader and cannot be in any
	handler."""
	console.handle(ord(":"))
	for character in "summary":
		console.handle(ord(character))
	console.handle(ENTER)
	assert console.mode == "table", "the submission itself left Jobs"
	console.handle(ENTER)
	assert console.mode == "detail"
	assert console.detail_work is not None


def test_a_later_deliberate_enter_opens_exactly_the_selected_job(
		monkeypatch, console):
	_submit(monkeypatch, console, "summary", [RETURN, 10])
	console.handle(ord("j"))
	rows, _hidden = console.visible_rows(console.rows())
	selected = rows[console.cursor]["id"]
	for key in _decode(monkeypatch, [RETURN, 10]):
		console.handle(key)
	assert console.mode == "detail"
	assert console.detail_work == selected
