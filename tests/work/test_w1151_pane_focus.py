"""W1151: Tab is the discoverable pane-focus gesture.

`work/records/2026/08/finding-immediate-pane-focus-navigation/`. The
geometric `Ctrl-W` map works — the mandatory gate in that dossier drove
a real pty and could not reproduce the reported pause, and the approver
then dropped the timing half from this Work entirely. What remains is
the confirmed secondary method: in view mode `Tab` cycles pane focus
forward and `Shift-Tab` backward, while `[`/`]` stay the EXCLUSIVE
tab-switching keys.

That last word is the change with teeth. W110 kept `Tab`/`Shift-Tab` as
compatibility aliases for top-level tab movement; they are retired
here, because one key cannot mean "next tab" and "next pane" without
meaning neither.

What these tests hold: the cycle in both directions with wrap, over the
panes each detail tab actually paints; the aliases gone; `[`/`]`
untouched at both levels; text entry keeping its own Tab contracts; the
move being read-only; and the footer naming both gestures without
spending a row on it.
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

import baton_work as bw                                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console                          # noqa: E402
import fixtures as fx                                          # noqa: E402

TAB, BTAB = 9, curses.KEY_BTAB
NEXT_TAB, PREV_TAB = ord("]"), ord("[")
ENTER, ESC, CTRL_W = 13, 27, 23


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the focus subject",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	for index in range(3):
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body=f"message {index}")
	store.close()
	return {"config": config_path, "database": database,
	        "work": born["work_id"]}


class Screen:
	def __init__(self, height=30, width=120):
		self.height = height
		self.width = width
		self.rows = {}

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "").ljust(x)
		text = str(text)[:n]
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def console(world):
	store = bw.Authority(world["database"])
	return Console(store, "lang", "ada", config_path=world["config"])


def painted(view, height=30, width=120):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


def detail(world):
	view = console(world)
	view.handle(ENTER)
	assert view.mode == "detail", "the detail view did not open"
	return view


# -- the cycle ---------------------------------------------------------------

def test_tab_cycles_the_message_panes_forward(world):
	view = detail(world)
	seen = []
	for _ in range(4):
		seen.append(view.focus)
		view.handle(TAB)
	assert seen == ["threads", "index", "reader", "threads"], seen


def test_shift_tab_cycles_them_backward(world):
	view = detail(world)
	seen = []
	for _ in range(4):
		seen.append(view.focus)
		view.handle(BTAB)
	assert seen == ["threads", "reader", "index", "threads"], seen


def test_the_two_directions_are_inverses(world):
	view = detail(world)
	for _ in range(len(("threads", "index", "reader")) * 2):
		before = view.focus
		view.handle(TAB)
		view.handle(BTAB)
		assert view.focus == before, before


def test_events_cycles_the_panes_it_actually_paints(world):
	"""Two panes there, not three: the Threads list is a Messages-tab
	region and Tab must not invent a stop that is not on screen."""
	view = detail(world)
	view.handle(NEXT_TAB)
	assert view.detail_tab == "events"
	seen = []
	for _ in range(3):
		seen.append(view.event_focus)
		view.handle(TAB)
	assert seen == ["index", "reader", "index"], seen
	# three forward steps from `index` land on `reader`; one back
	# returns to `index`
	assert view.event_focus == "reader"
	view.handle(BTAB)
	assert view.event_focus == "index"


def test_tab_and_the_chord_reach_the_same_states(world):
	"""The two gestures are alternatives, not two different models."""
	by_tab, by_chord = detail(world), detail(world)
	by_tab.handle(TAB)
	by_chord.handle(CTRL_W)
	by_chord.handle(ord("j"))
	assert by_tab.focus == by_chord.focus == "index"
	by_tab.handle(TAB)
	by_chord.handle(CTRL_W)
	by_chord.handle(ord("l"))
	assert by_tab.focus == by_chord.focus == "reader"


@pytest.mark.parametrize("pane_key", [TAB, BTAB])
def test_a_pane_key_consumes_a_pending_ctrl_w_prefix(world, pane_key):
	"""The two gestures are alternatives, so using one cannot leave the
	other half-entered. Otherwise Ctrl-W, Tab, j makes that later j finish
	the OLD chord instead of acting in the pane Tab selected."""
	view = detail(world)
	view.handle(CTRL_W)
	assert view.ctrl_w_pending
	view.handle(pane_key)
	assert not view.ctrl_w_pending, \
		"Tab moved focus but left the prior Ctrl-W prefix armed"


# -- the aliases are retired --------------------------------------------------

def test_tab_no_longer_switches_top_level_tabs(world):
	view = console(world)
	for key in (TAB, BTAB, TAB):
		view.handle(key)
		assert view.tab == "jobs", "Tab still moved a top-level tab"


def test_the_bracket_keys_still_switch_both_levels(world):
	view = console(world)
	view.handle(NEXT_TAB)
	assert view.tab == "teams"
	view.handle(PREV_TAB)
	assert view.tab == "jobs"
	inner = detail(world)
	inner.handle(NEXT_TAB)
	assert inner.detail_tab == "events"
	inner.handle(PREV_TAB)
	assert inner.detail_tab == "messages"


def test_a_detail_tab_key_never_moves_pane_focus(world):
	view = detail(world)
	view.handle(TAB)
	moved = view.focus
	view.handle(NEXT_TAB)
	view.handle(PREV_TAB)
	assert view.focus == moved, "a tab key disturbed the pane focus"


def test_a_pane_key_never_moves_a_tab(world):
	view = detail(world)
	for _ in range(4):
		view.handle(TAB)
		assert view.detail_tab == "messages"
		assert view.tab == "jobs"


# -- text entry keeps its own Tab ---------------------------------------------

def test_the_command_bar_keeps_its_completion_tab(world):
	"""W27's contract: Tab completes in the command bar. Pane cycling
	must not reach a surface where somebody is typing."""
	view = console(world)
	view.handle(ord(":"))
	for character in "clo":
		view.handle(ord(character))
	view.handle(TAB)
	assert view.command and view.command.startswith("clos"), view.command
	assert view.focus == "threads", "a completion moved the pane focus"


def test_the_search_entry_is_not_pane_navigation(world):
	view = console(world)
	view.handle(ord("/"))
	view.handle(TAB)
	assert view.search_input is not None, "Tab closed the search entry"
	assert view.tab == "jobs"


def test_the_batch_buffer_is_not_pane_navigation(world):
	view = console(world)
	view.handle(ord(":"))
	view.handle(ord(":"))
	assert view.batch is not None
	view.handle(TAB)
	assert view.batch is not None, "Tab left the batch buffer"


# -- the move is a view move --------------------------------------------------

def test_cycling_reads_nothing_and_changes_nothing(world):
	"""Focus is presentation: no selection, no seen state, no
	authority write."""
	view = detail(world)
	store = bw.Authority(world["database"])
	try:
		before = store.last_seq()
		selection = (view.disc_cursor, view.thread_before)
		for _ in range(6):
			view.handle(TAB)
		for _ in range(6):
			view.handle(BTAB)
		assert (view.disc_cursor, view.thread_before) == selection
		assert store.last_seq() == before, "focus movement wrote something"
	finally:
		store.close()


@pytest.mark.parametrize("width", [120, 90, 60, 40])
def test_the_focus_states_are_the_same_at_every_width(world, width):
	"""Wide puts the index beside the reader and narrow stacks them;
	the logical regions are the same either way."""
	view = detail(world)
	seen = []
	for _ in range(3):
		painted(view, width=width)
		seen.append(view.focus)
		view.handle(TAB)
	assert seen == ["threads", "index", "reader"], (width, seen)


# -- what the console tells the operator --------------------------------------

def test_the_footer_names_both_gestures_in_one_cell(world):
	view = detail(world)
	lines = painted(view)
	footer = next(line for line in lines if "panes" in line)
	assert "Tab/Ctrl-W panes" in footer, footer
	# and it did not cost a row: the tab hint is still on the same line
	assert "[/] tabs" in footer, footer


def test_the_operator_documentation_teaches_the_alternative():
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	prose = " ".join((repo / "docs" / "BATON-WORK.md")
	                 .read_text(encoding="utf-8").split())
	assert "Tab" in prose and "pane" in prose
	assert "Tab/Ctrl-W panes" in prose or \
		"`Tab` cycles pane focus" in prose, \
		"the guide does not teach Tab as a pane gesture"


# -- a real terminal ----------------------------------------------------------

@pytest.mark.skipif(not hasattr(__import__("pty"), "fork"),
                    reason="no pty support")
def test_a_real_terminal_moves_the_focus_marker_with_tab(world):
	"""Injected keys cannot see a terminal that never sends them. The
	focus marker `»` is TEXT, so a replay that keeps no attributes can
	still say which pane has it."""
	import ptyharness
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.9),      # 0: detail, focus on Threads
		(b"\t", 0.6),      # 1: Tab -> the message index
		(b"\t", 0.6),      # 2: Tab -> the reader
		(b"\x1b[Z", 0.6),  # 3: Shift-Tab (CSI Z) -> back to the index
		(b"qy", 0.4),
	], columns=120, lines=32)

	def marker(screen):
		"""(row, column) of the `»` focus cue.

		Read as a POSITION rather than as the heading text beside it:
		the index and the reader share one composed row at this width,
		so their headings do not tell the two apart — where the marker
		sits does."""
		for row, line in enumerate(screen):
			if "»" in line:
				return (row, line.index("»"))
		return None

	seen = [marker(ptyharness.replay(step, columns=120, lines=32))
	        for step in steps[:4]]
	assert all(seen), seen
	threads, index, reader, back = seen
	assert threads != index, ("Tab did not leave Threads", seen)
	assert index != reader, ("the second Tab did not move", seen)
	assert threads != reader, seen
	assert back == index, ("Shift-Tab did not step back", seen)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
