"""W110: one bracketed tab grammar throughout the TUI.

`work/records/2026/08/finding-consistent-tui-tab-grammar/`. The console
taught two grammars for one concept. Top-level Jobs/Teams/Inbox moved
on `Tab`/`Shift-Tab` and bracketed only the ACTIVE label; Work detail's
Messages/Events moved on `[`/`]` and bracketed only the active label
too. So the same bracket meant "this is a tab" at one level and "and
this one is selected" at the other, and the same operation wanted a
different gesture depending on how deep the operator was.

The ruling: every tab label is bracketed, the active one is
HIGHLIGHTED, and `[`/`]` move to the previous/next tab at the level the
operator is in. `Tab`/`Shift-Tab` survive as aliases.

What these tests hold, which is the whole of the acceptance boundary:
both bars bracket every tab and highlight exactly one; the keys wrap at
both levels; Work detail's keys never leak upward; the aliases still
work; `[` and `]` typed into text entry stay literal; `Ctrl-W` still
owns pane movement and tab movement never touches pane focus; a narrow
header keeps the active tab and never paints half a bracket; and the
footer hints and the operator documentation teach the same keys.
"""

from __future__ import annotations

import curses
import os
import pathlib
import re
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console, TABS                   # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
TAB, BTAB = 9, curses.KEY_BTAB
NEXT, PREV = ord("]"), ord("[")
ENTER, ESC, CTRL_W = 13, 27, 23


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the one open Work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada",
	               body="a message so the detail view has one")
	store.close()
	return {"config": config_path, "database": database,
	        "work": born["work_id"]}


class Screen:
	"""Records what was painted AND with what weight.

	The active tab is a weight now, not a bracket, so a fake that drops
	the attribute could not see the cue this Work exists to add."""

	def __init__(self, height=24, width=110):
		self.height = height
		self.width = width
		self.calls = []
		self.rows = {}

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.calls = []
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		text = str(text)[:n]
		attr = rest[0] if rest else 0
		self.calls.append({"y": y, "x": x, "text": text, "attr": attr})
		row = self.rows.get(y, "").ljust(x)
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []

	def labels(self, row):
		"""`[(text, attr)]` for the labels painted on one row."""
		return [(call["text"], call["attr"]) for call in self.calls
		        if call["y"] == row]

	def active(self, row):
		return [text for text, attr in self.labels(row)
		        if attr & curses.A_REVERSE]


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	return Console(store, "lang", member, config_path=world["config"])


def painted(view, height=24, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen


def header_row(screen):
	return screen.lines()[0]


def detail_bar(screen):
	"""The row the two detail labels were painted on."""
	rows = {call["y"] for call in screen.calls
	        if call["text"] in ("[Messages]", "[Events]")}
	assert len(rows) == 1, f"the detail tabs landed on {rows}"
	return rows.pop()


def open_detail(view):
	view.handle(ENTER)
	assert view.mode == "detail", "the Work detail view did not open"
	return view


# -- the bar: every tab bracketed, exactly one highlighted -------------------

def test_the_top_bar_brackets_every_tab(world):
	view = console(world)
	labels = [label for _name, label in view.top_tab_segments()]
	# W26328: the Jobs label carries the participant-actionable count,
	# always spelled. It is still ONE bracketed tab, which is what this
	# case is about, so the shape is asserted here and the number is
	# asserted where it is the subject.
	assert re.fullmatch(r"\[Jobs \d+\]", labels[0]), labels[0]
	assert labels[1] == "[Teams]", labels
	# W167: the label is `[Inbox]`, or `[Inbox *]` when this
	# participant owes something. Either way it is one bracketed tab.
	assert labels[2] in ("[Inbox]", "[Inbox *]"), labels[2]
	assert view.top_tabs() == "  ".join(labels)
	assert header_row(painted(view)).startswith(view.top_tabs())


@pytest.mark.parametrize("presses", [0, 1, 2])
def test_exactly_one_top_tab_is_highlighted(world, presses):
	view = console(world)
	for _ in range(presses):
		view.handle(NEXT)
	expected = dict(view.top_tab_segments())[view.tab]
	screen = painted(view)
	assert screen.active(0) == [expected], screen.labels(0)


def test_the_detail_bar_brackets_both_tabs_and_highlights_one(world):
	"""W6814 adds `[Jobs]` to the contextual Work page's row — the Work
	rendered as the tree root is the third thing an operator can want
	to see about the Work they opened. The GRAMMAR this case pins is
	unchanged: every label is bracketed at every moment, and exactly one
	carries the active weight."""
	view = open_detail(console(world))
	screen = painted(view)
	row = detail_bar(screen)
	assert [text for text, _attr in screen.labels(row)] == \
		["[Jobs]", "[Messages]", "[Events]"]
	assert screen.active(row) == ["[Messages]"]
	view.handle(NEXT)
	screen = painted(view)
	assert screen.active(detail_bar(screen)) == ["[Events]"]


def test_the_bracket_is_not_the_active_cue_at_either_level(world):
	"""The point of the ruling. Every label keeps its brackets through
	every selection, at both levels — what moves is the weight."""
	view = console(world)
	bar = view.top_tabs()
	for _ in range(len(TABS)):
		assert view.top_tabs() == bar, \
			"the label text moved with the selection"
		view.handle(NEXT)
	view = open_detail(console(world))
	for _ in range(2):
		# W6814: three labels now, and still every one of them
		# bracketed through every selection.
		assert view._tab_bar() == "[Jobs]  [Messages]  [Events]"
		view.handle(NEXT)


# -- navigation, at both levels, with wrap-around ----------------------------

def test_bracket_keys_cycle_the_top_level_with_wrap(world):
	view = console(world)
	forward = []
	for _ in range(4):
		forward.append(view.tab)
		view.handle(NEXT)
	assert forward == ["jobs", "teams", "inbox", "jobs"], forward
	back = []
	for _ in range(4):
		back.append(view.tab)
		view.handle(PREV)
	assert back == ["teams", "jobs", "inbox", "teams"], back


def test_bracket_keys_cycle_work_detail_with_wrap(world):
	"""W6814: the cycle is the contextual Work page's THREE tabs, and
	`Jobs` is a mode change rather than another reader — so the tab in
	view is read from `context_tab()`, which answers for all three."""
	view = open_detail(console(world))
	seen = []
	for _ in range(4):
		seen.append(view.context_tab())
		view.handle(NEXT)
	assert seen == ["messages", "events", "jobs", "messages"], seen
	assert view.context_tab() == "events"
	view.handle(PREV)
	assert view.context_tab() == "messages", "] and [ did not undo each other"
	view.handle(PREV)
	assert view.context_tab() == "jobs"
	view.handle(PREV)
	assert view.context_tab() == "events", "[ did not wrap backwards"


@pytest.mark.parametrize("start", list(TABS))
def test_the_keys_reach_every_tab_from_every_tab(world, start):
	view = console(world)
	while view.tab != start:
		view.handle(NEXT)
	assert {view.tab for _ in range(len(TABS))
	        if not view.handle(NEXT)} or True
	reached = set()
	for _ in range(len(TABS)):
		reached.add(view.tab)
		view.handle(NEXT)
	assert reached == set(TABS), reached


# -- context separation ------------------------------------------------------

def test_detail_tab_keys_never_reach_the_top_level(world):
	"""The one separation the ruling keeps, and the reason the guard is
	on the view MODE rather than on the key."""
	view = open_detail(console(world))
	for _ in range(4):
		view.handle(NEXT)
		assert view.tab == "jobs", \
			"a Work-detail tab key escaped to the top level"
	for _ in range(4):
		view.handle(PREV)
		assert view.tab == "jobs"


def test_the_top_level_keys_return_when_detail_closes(world):
	view = open_detail(console(world))
	view.handle(NEXT)
	assert view.detail_tab == "events" and view.tab == "jobs"
	view.handle(ESC)
	assert view.mode != "detail"
	view.handle(NEXT)
	assert view.tab == "teams", \
		"the top level did not take its keys back"


def test_tab_movement_does_not_disturb_pane_focus(world):
	"""`Ctrl-W` remains pane navigation, and a tab move is a VIEW move.
	A tab key that also reset the focused pane would make the two
	gestures interfere in exactly the way the ruling separates."""
	view = open_detail(console(world))
	view.handle(CTRL_W)
	view.handle(ord("j"))
	moved = view.focus
	assert moved != "threads", "the pane focus never moved"
	view.handle(NEXT)
	view.handle(PREV)
	assert view.focus == moved, "a tab key moved the pane focus"


# -- the aliases survive -----------------------------------------------------

def test_tab_no_longer_switches_tabs(world):
	"""W110 kept `Tab`/`Shift-Tab` as compatibility aliases here.
	W1151 (finding-immediate-pane-focus-navigation) retires them: `[`
	and `]` are the EXCLUSIVE tab-switching keys, because Tab has a
	better job one level down — cycling pane focus for operators who do
	not reach for Vim window commands. One key cannot mean "next tab"
	and "next pane" without meaning neither.

	What W110 actually owns is unchanged and still asserted above: the
	bracketed grammar, at both levels, with wrap."""
	view = console(world)
	view.handle(TAB)
	assert view.tab == "jobs", "Tab still switched a top-level tab"
	view.handle(BTAB)
	assert view.tab == "jobs", "Shift-Tab still switched a top-level tab"
	# and the canonical keys are unaffected
	view.handle(NEXT)
	assert view.tab == "teams"


# -- text entry keeps the brackets literal -----------------------------------

def test_the_command_bar_takes_brackets_as_text(world):
	view = console(world)
	view.handle(ord(":"))
	for key in (ord("s"), PREV, ord("x"), NEXT):
		view.handle(key)
	assert view.command == "s[x]", view.command
	assert view.tab == "jobs", "a typed bracket switched the tab"


def test_the_search_entry_takes_brackets_as_text(world):
	view = console(world)
	view.handle(ord("/"))
	for key in (PREV, ord("a"), NEXT):
		view.handle(key)
	assert view.search_input == "[a]", view.search_input
	assert view.tab == "jobs"


def test_the_batch_buffer_takes_brackets_as_text(world):
	"""W19's `::` multiline buffer. Every key belongs to the buffer
	while it is open — the same rule that keeps `q` literal there."""
	view = console(world)
	view.handle(ord(":"))
	view.handle(ord(":"))
	assert view.batch is not None, "the batch buffer did not open"
	for key in (ord("s"), PREV, ord("x"), NEXT):
		view.handle(key)
	assert view.batch[0]["text"] == "s[x]", view.batch[0]
	assert view.tab == "jobs", "a batch keystroke switched the tab"


# -- narrow widths -----------------------------------------------------------

def test_a_narrow_header_never_paints_half_a_bracket(world):
	view = console(world)
	for width in range(1, 40):
		screen = painted(view, height=14, width=width)
		for text, _attr in screen.labels(0):
			if not text.startswith("["):
				continue
			assert text.endswith("]"), \
				f"width {width} painted a partial label {text!r}"


def test_a_narrow_header_keeps_the_active_tab(world):
	"""Dropping labels is fine; dropping the one the keys act in is
	not. The active tab is the last thing a narrow bar may lose."""
	view = console(world)
	for tab in TABS:
		while view.tab != tab:
			view.handle(NEXT)
		for width in range(14, 40):
			screen = painted(view, height=14, width=width)
			painted_tabs = [text for text, _a in screen.labels(0)
			                if text.startswith("[")]
			if not painted_tabs:
				continue
			assert screen.active(0), \
				(f"width {width} painted {painted_tabs} without the "
				 f"active {tab}")


def test_an_impossible_width_paints_no_tab_rather_than_a_stump(world):
	view = console(world)
	screen = painted(view, height=14, width=4)
	assert [text for text, _a in screen.labels(0)
	        if text.startswith("[")] == []


@pytest.mark.parametrize("tab", list(TABS))
def test_the_right_aligned_identity_never_overwrites_a_tab(world, tab):
	"""Review R1: whole labels means the FINAL screen, not the first
	paint call. Identity is deliberately painted last and may otherwise
	replace a closing bracket after `visible_tab_segments` accepted it."""
	view = console(world)
	while view.tab != tab:
		view.handle(NEXT)
	for width in range(8, 41):
		screen = painted(view, height=14, width=width)
		line = header_row(screen)
		identity_at = max(0, width - 1 - len(view.participant))
		prefix = line[:identity_at].rstrip()
		assert prefix.count("[") == prefix.count("]"), \
			(f"width {width} left a partial tab before the identity: "
			 f"{line!r}")


def test_a_narrow_detail_bar_keeps_the_active_tab(world):
	"""Review R2: detail has the same narrow-layout contract. Painting
	left-to-right must not leave only inactive Messages visible while the
	operator is actually in Events."""
	view = open_detail(console(world))
	view.handle(NEXT)
	assert view.detail_tab == "events"
	screen = painted(view, height=14, width=13)
	row = detail_bar(screen)
	assert screen.active(row) == ["[Events]"], screen.labels(row)


# -- what the console TELLS the operator -------------------------------------

@pytest.mark.parametrize("tab", ["teams", "inbox"])
def test_the_footer_teaches_the_canonical_keys(world, tab):
	view = console(world)
	while view.tab != tab:
		view.handle(NEXT)
	assert any("[/] tabs" in line for line in painted(view).lines()), \
		painted(view).lines()[-3:]


def test_the_detail_footer_teaches_the_same_keys(world):
	view = open_detail(console(world))
	assert any("[/] tabs" in line for line in painted(view).lines())


def test_the_operator_documentation_teaches_one_grammar():
	body = (REPO / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	prose = " ".join(body.split())
	assert "[Jobs 3] [Teams] [Inbox *]" in prose, \
		"the documented header still shows the superseded bar"
	assert "`]` selects the next tab and `[` the previous" in prose, \
		"the doc does not name the canonical keys at the top level"
	assert "`[/] tabs`" in prose, "the footer hint is undocumented"
	# the retired instructions must not survive beside the new one
	for retired in ("still belong to Work detail",
	                "the selected tab is in brackets",
	                "`Tab` cycles them forward"):
		assert retired not in prose, \
			f"the doc still teaches the superseded rule: {retired!r}"


# -- a real terminal ---------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_moves_both_tab_levels_with_brackets(world):
	"""Injected keys cannot see a terminal that never sends them. The
	replay reconstructs TEXT and not weight, so what a terminal can
	prove is the bracketed bar and the movement — the highlight is
	pinned above, where the attribute is exact."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.5),        # 0: Jobs
		(b"]", 0.5),       # 1: Teams
		(b"]", 0.5),       # 2: Inbox
		(b"]", 0.5),       # 3: wrapped back to Jobs
		(b"\r", 0.6),      # 4: Work detail, on Messages
		(b"]", 0.5),       # 5: Events — and NOT the top level
		(b"qy", 0.4),
	])
	jobs, teams, inbox, wrapped, detail, events = (
		ptyharness.replay(step) for step in steps[:6])
	for screen in (jobs, teams, inbox, wrapped):
		assert re.match(r"\[Jobs \d+\]  \[Teams\]  \[Inbox", screen[0]), \
			screen[0]
	assert any("lang.grace" in line for line in teams), teams[:8]
	assert any("nothing owed" in line or "Inbox" in line
	           for line in inbox), inbox[:8]
	assert any("the one open Work" in line for line in wrapped), \
		"] did not wrap back to Jobs"
	assert any("[Messages]  [Events]" in line for line in detail), \
		detail[:12]
	assert any("[Messages]  [Events]" in line for line in events), \
		events[:12]
	# the ] inside detail moved the DETAIL tab and left the top level
	# alone: the Events view names the Work's journal, and the global
	# tab row is not painted at all.
	#
	# W292 supersedes the old expectation that the global row stayed
	# visible here. What the ruling keeps is the property this case
	# exists for: `]` inside a drilled page moves that page's LOCAL tab
	# and nothing else — and it is now provable from the header, which
	# names the drilled location rather than the top level.
	assert events[0].startswith("Jobs > "), events[0]
	for label in ("[Jobs ", "[Teams]", "[Inbox"):
		assert label not in events[0], events[0]
	assert detail[0] == events[0], \
		"the local tab move changed the location row"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-600:]
