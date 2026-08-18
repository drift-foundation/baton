"""W26: the `:` bar keeps a searchable history.

After a command executed or refused, opening `:` started empty — so
changing one operand of a long operation meant retyping all of it. The
refusal case is the one that mattered most: a command the parser or the
authority rejected is exactly the one an operator wants back.

History is session-local PRESENTATION state. It is never read from or
written to the authority, two Consoles never share it, and nothing here
survives a restart — persistence needs its own ruling about where such
state lives and what it means to keep command bodies on disk.
"""

from __future__ import annotations

import curses
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work.tui.app import Console, HISTORY_LIMIT          # noqa: E402
import fixtures as fx                                          # noqa: E402

CTRL_R = 18
TAB = 9


@pytest.fixture()
def console(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield Console(store, "lang", "ada", config_path=config_path)
	store.close()


def _type(console, text):
	for character in text:
		console.handle(ord(character))


def _open(console):
	console.handle(ord(":"))


def _submit(console, text):
	_open(console)
	_type(console, text)
	console.handle(10)


# -- what enters history ---------------------------------------------------

def test_a_refused_command_is_remembered(console):
	"""The primary use case. A command the authority refuses is the one
	worth recalling, so history cannot be derived from success."""
	_submit(console, "claim work=nope")
	assert console.history == ["claim work=nope"]
	assert console.status, "the refusal was not surfaced"


def test_an_unparseable_command_is_remembered(console):
	"""Refused before the authority ever sees it — still a submission."""
	_submit(console, 'say body="unterminated')
	assert console.history == ['say body="unterminated']


def test_a_cancelled_draft_never_enters_history(console):
	_open(console)
	_type(console, "close work=W2")
	console.handle(27)
	assert console.history == []


def test_an_empty_submission_is_not_remembered(console):
	_submit(console, "")
	assert console.history == []


def test_adjacent_identical_submissions_collapse(console):
	for _ in range(3):
		_submit(console, "home")
	_submit(console, "tree")
	_submit(console, "home")
	# ...but a repeat that is NOT adjacent is a separate entry
	assert console.history == ["home", "tree", "home"]


def test_history_is_bounded_and_evicts_oldest_first(console):
	console.history = [f"home {index}" for index in range(HISTORY_LIMIT)]
	_submit(console, "the newest one")
	assert len(console.history) == HISTORY_LIMIT
	assert console.history[-1] == "the newest one"
	assert console.history[0] == "home 1", "eviction took the wrong end"


def test_two_consoles_do_not_share_history(console, tmp_path):
	_submit(console, "home")
	other = Console(console.store, "lang", "ada",
	                config_path=console.config_path)
	assert other.history == [], "history leaked between Consoles"


# -- Up/Down ---------------------------------------------------------------

def test_up_recalls_the_newest_then_walks_older(console):
	_submit(console, "first")
	_submit(console, "second")
	_open(console)
	console.handle(curses.KEY_UP)
	assert console.command == "second"
	console.handle(curses.KEY_UP)
	assert console.command == "first"


def test_up_stops_at_the_oldest_entry(console):
	_submit(console, "only")
	_open(console)
	for _ in range(5):
		console.handle(curses.KEY_UP)
	assert console.command == "only"


def test_down_past_the_newest_restores_the_exact_draft(console):
	"""Byte-exact, including trailing space — an approximate restore is
	worse than none, because the operator cannot see what changed."""
	_submit(console, "home")
	_open(console)
	_type(console, "say thread=T2 body=hal ")
	console.handle(curses.KEY_UP)
	assert console.command == "home"
	console.handle(curses.KEY_DOWN)
	assert console.command == "say thread=T2 body=hal "


def test_up_with_no_history_leaves_the_draft_alone(console):
	_open(console)
	_type(console, "partial")
	console.handle(curses.KEY_UP)
	console.handle(curses.KEY_DOWN)
	assert console.command == "partial"


def test_editing_a_recalled_entry_does_not_change_history(console):
	_submit(console, "close work=W2")
	_open(console)
	console.handle(curses.KEY_UP)
	console.handle(curses.KEY_BACKSPACE)
	_type(console, "9")
	assert console.command == "close work=W9"
	assert console.history == ["close work=W2"], \
		"editing the buffer rewrote the stored entry"


def test_reopening_the_bar_starts_a_fresh_draft_after_the_newest(console):
	_submit(console, "home")
	_open(console)
	console.handle(curses.KEY_UP)
	console.handle(27)
	_open(console)
	assert console.command == "", "the bar reopened onto a stale recall"
	console.handle(curses.KEY_UP)
	assert console.command == "home"


# -- reverse search --------------------------------------------------------

def test_ctrl_r_finds_the_newest_match_and_narrows(console):
	_submit(console, "close work=W2 outcome=satisfying")
	_submit(console, "home")
	_submit(console, "close work=W3 outcome=rejected")
	_open(console)
	console.handle(CTRL_R)
	assert console.reverse["match"] is not None
	_type(console, "W2")
	assert console.history[console.reverse["match"]].startswith(
		"close work=W2")


def test_repeated_ctrl_r_steps_to_the_next_older_match(console):
	_submit(console, "close work=W2")
	_submit(console, "close work=W3")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "close")
	assert console.history[console.reverse["match"]] == "close work=W3"
	console.handle(CTRL_R)
	assert console.history[console.reverse["match"]] == "close work=W2"


def test_ctrl_r_does_not_wrap_past_the_oldest_match(console):
	"""Wrapping hides that the search has run out."""
	_submit(console, "close work=W2")
	_submit(console, "close work=W3")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "close")
	for _ in range(6):
		console.handle(CTRL_R)
	assert console.history[console.reverse["match"]] == "close work=W2"


def test_backspace_widens_the_query(console):
	_submit(console, "close work=W2")
	_submit(console, "home")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "clo")
	assert console.history[console.reverse["match"]] == "close work=W2"
	for _ in range(3):
		console.handle(curses.KEY_BACKSPACE)
	assert console.reverse["query"] == ""
	assert console.history[console.reverse["match"]] == "home"


def test_a_query_matching_nothing_reports_no_match(console):
	_submit(console, "home")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "zzz")
	assert console.reverse["match"] is None


def test_the_search_is_case_sensitive(console):
	_submit(console, "close work=W2")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "CLOSE")
	assert console.reverse["match"] is None


def test_escape_restores_the_pre_search_draft(console):
	_submit(console, "home")
	_open(console)
	_type(console, "say thread=T2 ")
	console.handle(CTRL_R)
	_type(console, "ho")
	console.handle(27)
	assert console.reverse is None
	assert console.command == "say thread=T2 ", \
		"cancelling search did not restore the draft"


@pytest.mark.parametrize("accept", [curses.KEY_RIGHT, TAB])
def test_right_and_tab_adopt_the_match_without_executing(console, accept):
	"""Both accept the match into the ordinary buffer and neither
	executes it.

	W27 landed the completion verb this branch was reserved for, so Tab
	now adopts AND completes in one gesture — the ruling says Tab
	"first adopts the displayed history match into the normal buffer and
	then runs this same completion operation". The adopted line ends in
	a complete closed value, so completion appends that value's ruled
	delimiter and nothing else. Right adopts alone, unchanged.

	This file's comment beside the branch read it as completing on the
	NEXT Tab; W27's contract is the same gesture, and that is what is
	implemented."""
	_submit(console, "close work=W2 outcome=satisfying")
	_open(console)
	# captured AFTER opening: the `:` handler clears status, so the
	# pre-open value would make this pass for the wrong reason.
	before = console.status
	console.handle(CTRL_R)
	_type(console, "close")
	console.handle(accept)
	assert console.reverse is None
	adopted = "close work=W2 outcome=satisfying"
	expected = adopted + (" " if accept == TAB else "")
	assert console.command == expected
	assert console.status == before, "accepting the match executed it"


def test_the_adopted_match_is_an_ordinary_buffer(console):
	"""`recall, tweak, rerun`: after accepting, editing behaves exactly
	as if the text had been typed."""
	_submit(console, "close work=W2")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "close")
	console.handle(curses.KEY_RIGHT)
	console.handle(curses.KEY_BACKSPACE)
	_type(console, "9")
	assert console.command == "close work=W9"


def test_enter_submits_the_selected_match(console):
	_submit(console, "home")
	_submit(console, "tree")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "hom")
	console.handle(10)
	assert console.command is None, "the bar stayed open"
	assert console.reverse is None
	# submitting a recalled entry records it again as the newest
	assert console.history[-1] == "home"


def test_enter_with_no_selected_match_executes_nothing(console):
	"""The no-match prompt must not execute the invisible saved draft.

	The confirmed contract makes Enter submit the selected text.  When there
	is no selection, retaining search is safer than silently running text the
	operator can no longer see.
	"""
	_submit(console, "home")
	_open(console)
	_type(console, "close work=W2")
	console.handle(CTRL_R)
	_type(console, "does-not-match")
	calls = []
	console.execute = calls.append
	console.handle(10)
	assert calls == [], "Enter executed the hidden pre-search draft"
	assert console.reverse is not None, "the refused search was discarded"
	assert console.command == "close work=W2"


def test_a_search_query_never_enters_history(console):
	_submit(console, "home")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "zzz")
	console.handle(27)
	console.handle(27)
	assert console.history == ["home"]


# -- everything else is untouched ------------------------------------------

def test_table_navigation_keeps_its_own_up_and_down(console):
	"""History binds Up/Down only while the bar is OPEN."""
	rows = console.rows()
	if len(rows) > 1:
		console.handle(curses.KEY_DOWN)
		assert console.cursor == 1
		console.handle(curses.KEY_UP)
		assert console.cursor == 0
	assert console.command is None


def test_the_batch_buffer_keeps_its_line_navigation(console):
	"""`::` has its own Up/Down over staged lines; W26 does not touch
	it."""
	console.handle(ord(":"))
	console.handle(ord(":"))
	assert console.batch is not None and console.command is None
	console.handle(ord("h"))
	console.handle(10)
	console.handle(ord("t"))
	assert len(console.batch) == 2
	console.handle(curses.KEY_UP)
	assert console.batch_cursor == 0, "batch line navigation changed"


def test_navigating_history_reads_nothing_from_the_authority(console):
	"""Presentation state: recalling and searching must not query."""
	_submit(console, "home")
	_submit(console, "tree")
	from baton_work import projection as pj
	calls = {"n": 0}
	real = pj.tree

	def counting(*args, **kwargs):
		calls["n"] += 1
		return real(*args, **kwargs)

	pj.tree = counting
	try:
		_open(console)
		console.handle(curses.KEY_UP)
		console.handle(curses.KEY_UP)
		console.handle(curses.KEY_DOWN)
		console.handle(CTRL_R)
		_type(console, "ho")
		console.handle(CTRL_R)
		console.handle(curses.KEY_RIGHT)
		console.handle(27)
	finally:
		pj.tree = real
	assert calls["n"] == 0, \
		f"history navigation queried the authority {calls['n']}x"


def test_an_overwidth_reverse_query_keeps_its_live_tail_visible(console):
	"""Reverse search inherits the command bar's caret viewport rule.

	The insertion point is at the end of the query.  Moving the terminal
	caret to the right edge while painting only the query's old prefix puts
	the caret on unrelated text and hides every character the operator is
	currently typing.
	"""
	_submit(console, "home")
	_open(console)
	console.handle(CTRL_R)
	query = "prefix-" + "x" * 40 + "-live-tail"
	_type(console, query)

	class Screen:
		def __init__(self):
			self.calls = []
			self.caret = None

		def erase(self):
			pass

		def getmaxyx(self):
			return 12, 32

		def addnstr(self, y, x, text, *rest):
			self.calls.append((y, x, str(text)))

		def move(self, y, x):
			self.caret = (y, x)

		def refresh(self):
			pass

	screen = Screen()
	console.render(screen)
	bottom = "".join(text for y, _x, text in screen.calls if y == 11)
	assert query[-9:] in bottom, \
		f"the live reverse-search tail is outside its viewport: {bottom!r}"
	assert screen.caret is not None and screen.caret[0] == 11


# -- the real terminal -----------------------------------------------------

@pytest.mark.serial
def test_a_no_match_enter_changes_nothing_on_a_real_terminal(tmp_path):
	"""The painted state and the submitted command must not diverge.

	State-level checks prove `execute()` is not called; only a terminal
	shows that the row still says no-match afterwards, and that nothing
	the operator could not see reached the authority. This drives the
	real key bytes: `Ctrl-R`, a query that matches nothing, Enter.
	"""
	import os
	import ptyharness
	from baton_work import transitions as tr

	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	with bw.Authority(database) as store:
		tr.create_work(store, team="lang", kind="bug", title="alpha",
		               origin="self-initiated",
		               classification="suspected-defect", author="ada",
		               body="b")
		before = store.last_seq()

	script = [
		(b":", 0.4), (b"home\r", 0.6),          # one entry in history
		(b":", 0.4), (b"close work=W2", 0.4),   # a draft, then search
		(b"\x12", 0.4), (b"zzzz", 0.5),         # Ctrl-R, no match
		(b"\r", 0.6),                           # Enter must do nothing
		(b"\x1b", 0.3), (b"\x1b", 0.3), (b"qy", 0.5),
	]
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", script, columns=100, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]

	after_enter = "\n".join(ptyharness.replay(steps[6], columns=100,
	                                          lines=14))
	assert "reverse-i-search" in after_enter, \
		f"Enter left the no-match search: {after_enter[-300:]!r}"
	assert "close work=W2" not in after_enter, \
		"the hidden draft was painted back onto the row"

	with bw.Authority(database) as store:
		assert store.last_seq() == before, \
			"a command the operator could not see reached the authority"


@pytest.mark.serial
def test_the_draft_survives_a_no_match_search_on_a_real_terminal(tmp_path):
	"""...and Esc still returns exactly what was being typed."""
	import os
	import ptyharness
	from baton_work import transitions as tr

	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	with bw.Authority(database) as store:
		tr.create_work(store, team="lang", kind="bug", title="alpha",
		               origin="self-initiated",
		               classification="suspected-defect", author="ada",
		               body="b")

	script = [
		(b":", 0.4), (b"home\r", 0.6),
		(b":", 0.4), (b"close work=W2", 0.4),
		(b"\x12", 0.4), (b"zzzz", 0.4),
		(b"\r", 0.4),                # refused, still searching
		(b"\x1b", 0.5),              # Esc restores the draft
		(b"\x1b", 0.3), (b"qy", 0.5),
	]
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", script, columns=100, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
	restored = "\n".join(ptyharness.replay(steps[7], columns=100, lines=14))
	assert ":close work=W2" in restored, \
		f"Esc did not restore the draft: {restored[-300:]!r}"


# -- the over-width reverse-search viewport (round 2) ----------------------

class _Row:
	"""One render, reduced to the bottom row and the terminal caret."""

	def __init__(self, columns=32, lines=12):
		self.calls = []
		self.caret = None
		self._size = (lines, columns)

	def erase(self):
		pass

	def getmaxyx(self):
		return self._size

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text)))

	def move(self, y, x):
		self.caret = (y, x)

	def refresh(self):
		pass

	def bottom(self):
		row = self._size[0] - 1
		return "".join(text for y, _x, text in self.calls if y == row)


def _reverse_row(console, columns=32, lines=12):
	screen = _Row(columns, lines)
	console.render(screen)
	return screen.bottom(), screen.caret


def _open_search(console, query, history=("home",)):
	for entry in history:
		_submit(console, entry)
	_open(console)
	console.handle(CTRL_R)
	_type(console, query)


def test_the_caret_lands_on_the_last_typed_character_not_the_edge(console):
	"""The defect'S OTHER HALF. Painting the oldest prefix was one
	failure; clamping the caret to the final cell was the other, and it
	is what made the row actively misleading — the caret claimed an
	insertion point that was not where typing went."""
	query = "prefix-" + "x" * 40 + "-live-tail"
	_open_search(console, query)
	row, caret = _reverse_row(console, columns=32)
	assert caret is not None
	# the caret sits immediately after the last painted query character
	assert row[caret[1] - 1] == query[-1], \
		f"the caret is not on the insertion point: {row!r} at {caret}"
	assert caret[1] <= 31 - 1


def test_the_clip_is_disclosed_the_way_ordinary_entry_discloses_it(console):
	_open_search(console, "prefix-" + "x" * 40 + "-live-tail")
	row, _caret = _reverse_row(console, columns=32)
	assert "`<" in row, \
		f"the clipped left is not marked: {row!r}"


def test_the_identity_survives_the_clip(console):
	"""An operator who cannot see which mode they are in cannot predict
	what Enter does. The identity is ranked above the query for exactly
	that reason, and above the match twice over."""
	_open_search(console, "prefix-" + "x" * 40 + "-live-tail")
	row, _caret = _reverse_row(console, columns=32)
	assert row.startswith("(reverse-i-search)`"), row


def test_a_match_is_clipped_before_the_query_is(console):
	"""The match is the RESULT. A result that crowds out the input it
	came from is backwards, so it yields the row first."""
	long_command = "filter " + "y" * 60 + " tail-of-match"
	_open_search(console, "y" * 30, history=("home", long_command))
	row, caret = _reverse_row(console, columns=44)
	assert "y" * 20 in row, f"the live query was clipped first: {row!r}"
	assert "tail-of-match" not in row, \
		f"the match kept room the query needed: {row!r}"
	assert caret is not None and row[caret[1] - 1] == "y"


def test_a_fitting_query_and_match_both_paint_whole(console):
	"""The ordinary case is unchanged: nothing is clipped and nothing
	is marked."""
	_open_search(console, "ho", history=("home",))
	row, caret = _reverse_row(console, columns=60)
	assert row.startswith("(reverse-i-search)`ho': "), row
	assert "home" in row and "<" not in row, row
	assert caret == (11, len("(reverse-i-search)`ho"))


def test_a_wider_resize_shows_the_whole_query_again(console):
	"""The stored query is never cut — the viewport is recomputed from
	the intact value, so widening restores what narrowing hid."""
	query = "prefix-" + "x" * 20 + "-live-tail"
	_open_search(console, query)
	narrow, _ = _reverse_row(console, columns=32)
	assert query not in narrow
	wide, caret = _reverse_row(console, columns=110)
	assert query in wide, \
		f"the query did not survive the narrow render: {wide!r}"
	assert "<" not in wide
	assert caret == (11, len("(reverse-i-search)`") + len(query))


def test_a_degenerate_width_keeps_the_mode_recognizable(console):
	"""Narrower than the prompt itself. Something has to give; the
	answer is not a second, shorter spelling of the prompt, which would
	make the mode unrecognizable exactly when it is hardest to read."""
	_open_search(console, "abc")
	row, caret = _reverse_row(console, columns=12)
	assert row and "(reverse-i" in row, row
	assert caret is not None and 0 <= caret[1] <= 10, caret


def test_the_no_match_distinction_survives_the_viewport(console):
	"""DIM for no match is a rule the round-1 review established; the
	viewport must not have quietly dropped it."""
	painted = []

	class Screen(_Row):
		def addnstr(self, y, x, text, *rest):
			super().addnstr(y, x, text, *rest)
			if y == 11:
				painted.append(rest[-1] if rest else None)

	_open_search(console, "zzz-no-such-command")
	console.render(Screen(32, 12))
	assert painted and painted[-1] == curses.A_DIM, painted
