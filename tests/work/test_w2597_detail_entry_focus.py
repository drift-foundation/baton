"""W2597: fresh Work detail opens focused on the Message index.

`work/records/2026/08/finding-default-message-pane-focus/`. Opening a
Work selected its first Thread and left the cursor in the Threads pane.
Most Work has exactly one Thread — which the autoselect had already
picked — so every reading session began by paying a `Tab` to reach the
Messages the selection was already pointing at.

The ruling moves only where the cursor STARTS. Work detail still opens
on the Messages tab, still autoselects the Thread by the New-first rule,
and the visible Thread still decides which Messages are shown. The
Threads pane keeps its job and stays one gesture away.

Two things this must not become. It must not read or write anything:
entry defers both selections to the renderer, so it cannot invent a
Message, mark one seen, or touch the authority. And it must not strand
an operator in an empty pane: Work with no Thread, and a Thread with no
Messages, stay navigable.

The three entry paths — Jobs, search results, and an Inbox row's Work
context — go through one helper, because a default that three call
sites each spell for themselves is a default that drifts.
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
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import (Console,                       # noqa: E402
                                DETAIL_ENTRY_FOCUS)
import fixtures as fx                                          # noqa: E402

TAB, BTAB = 9, curses.KEY_BTAB
ENTER, ESC, CTRL_W = 13, 27, 23
NEXT_TAB = ord("]")
# W6814 put a third tab (`Jobs`) on the contextual Work page's row, so a
# Messages→Events→Messages round trip is `]` then `[` rather than `]`
# twice. The property under test — a tab keeps its own pane focus across a
# round trip — is unchanged and is what these cases still assert.
PREV_TAB = ord("[")


@pytest.fixture()
def world(tmp_path):
	"""One Work with one Thread and several Messages — the ordinary
	shape, and the one the ruling is about."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the reading subject",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	for index in range(3):
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body=f"message {index}")
	store.close()
	return {"config": config_path, "database": database,
	        "work": born["work_id"], "thread": born["thread"]}


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


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	return Console(store, "lang", member, config_path=world["config"])


def painted(view, height=30, width=120):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


def from_jobs(world):
	view = console(world)
	view.handle(ENTER)
	assert view.mode == "detail", "the detail view did not open"
	return view


def from_search(world, query="reading"):
	view = console(world)
	view.handle(ord("/"))
	for character in query:
		view.handle(ord(character))
	view.handle(ENTER)          # run the search
	assert view.mode == "search", view.mode
	view.handle(ENTER)          # open the selected result
	assert view.mode == "detail", "the search result did not open detail"
	return view


@pytest.fixture()
def pair(tmp_path):
	"""TWO Works, because the P1 sequence needs a Work to leave and a
	DIFFERENT one to open, and Work A needs enough events to page."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	works = []
	for title in ("work A", "work B"):
		born = tr.create_work(store, team="lang", kind="bug", title=title,
		                      origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="the opener")
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body="a message")
		works.append(born["work_id"])
	for index in range(14):
		tr.prioritize(store, works[0], actor_team="lang", actor="ada",
		              priority="high" if index % 2 else "low")
	store.close()
	return {"config": config_path, "database": database,
	        "a": works[0], "b": works[1]}


def marker_row(lines, label):
	return next(line for line in lines if label in line)


# -- the default ------------------------------------------------------------

def test_a_fresh_detail_entry_focuses_the_message_index(world):
	"""The ruling, in the console's own state."""
	view = from_jobs(world)
	assert view.focus == "index"
	assert view.focus == DETAIL_ENTRY_FOCUS


def test_the_index_is_the_pane_the_screen_marks(world):
	"""State is not enough — the operator has to SEE where the cursor
	is. The Threads list keeps its selection and loses only the focus
	marker."""
	lines = painted(from_jobs(world))
	assert marker_row(lines, "Messages (").startswith("»"), \
		marker_row(lines, "Messages (")
	threads = marker_row(lines, "Threads (")
	assert not threads.startswith("»"), threads


def test_j_and_k_move_messages_with_no_preliminary_pane_switch(world):
	"""The acceptance boundary's headline: the extra `Tab` is gone."""
	view = from_jobs(world)
	painted(view)
	first = view.msg_cursor
	assert first is not None, "entry selected no Message to move from"
	view.handle(ord("j"))
	painted(view)
	assert view.msg_cursor != first, \
		"j did not move the Message selection; entry is in the wrong pane"
	view.handle(ord("k"))
	painted(view)
	assert view.msg_cursor == first, "k did not come back"


def test_the_thread_is_still_autoselected_and_still_decides_the_messages(
		world):
	"""Only the focus moved. The Thread selection rule and its effect on
	what the index shows are untouched."""
	view = from_jobs(world)
	painted(view)
	assert view.viewed_thread == world["thread"]
	assert view.disc_cursor == 0


# -- every entry path agrees -------------------------------------------------

def test_the_jobs_entry_path_uses_the_default(world):
	assert from_jobs(world).focus == DETAIL_ENTRY_FOCUS


def test_the_search_entry_path_uses_the_default(world):
	view = from_search(world)
	assert view.focus == DETAIL_ENTRY_FOCUS
	assert view.detail_return == "search", \
		"the search return path was lost with the focus change"


def test_the_inbox_entry_path_uses_the_default(tmp_path):
	"""An Inbox row hands the operator to Jobs with the right Work
	already open, so it is a fresh detail entry like the other two."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="owed work", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="confirm before the handoff",
	               request="lang.bug", on=born["work_id"], wait=False)
	store.close()
	world = {"config": config_path, "database": database,
	         "work": born["work_id"]}
	view = console(world)
	while view.tab != "inbox":
		view.handle(NEXT_TAB)
	rows = view.inbox_rows()
	assert rows, "the Inbox has no row to enter from"
	view.handle(ENTER)
	assert view.mode == "detail", "the Inbox row did not open detail"
	assert view.tab == "jobs", "the Inbox entry did not hand over to Jobs"
	assert view.focus == DETAIL_ENTRY_FOCUS
	view.store.close()


def test_the_three_paths_reach_the_same_focus(world):
	"""Asserted together, because the defect a shared default prevents
	is exactly one path drifting from the others."""
	assert len({from_jobs(world).focus, from_search(world).focus}) == 1


# -- the Threads pane is one gesture away ------------------------------------

def test_shift_tab_reaches_the_threads_pane(world):
	view = from_jobs(world)
	view.handle(BTAB)
	assert view.focus == "threads"


def test_the_geometric_chord_reaches_the_threads_pane(world):
	view = from_jobs(world)
	view.handle(CTRL_W)
	view.handle(ord("k"))
	assert view.focus == "threads"


def test_the_threads_pane_still_navigates_once_reached(world):
	"""Reaching it is not enough; it has to still work."""
	view = from_jobs(world)
	painted(view)
	view.handle(BTAB)
	view.handle(ord("j"))
	painted(view)
	assert view.focus == "threads"


# -- empty states stay safe and navigable ------------------------------------

def test_a_work_with_no_thread_opens_without_error(world, monkeypatch):
	"""The acceptance boundary asks for empty Work to stay safe.

	That state is NOT reachable through the public surface, and saying
	so is part of the answer: every Work is born with a Thread, and
	`unlabel_thread` refuses to remove a Thread's final label — "a
	thread always keeps explicit Work scope". So this drives the
	renderer's own empty branch directly rather than pretending to
	construct a state the authority forbids. What it proves is that the
	guard is real and that entry does not invent a Message to fill it."""
	view = from_jobs(world)
	monkeypatch.setattr(type(view), "thread_rows", lambda self: [])
	lines = painted(view)
	assert any("(no threads)" in line for line in lines), lines[:12]
	assert view.focus == DETAIL_ENTRY_FOCUS
	assert view.msg_cursor is None, "an empty detail invented a Message"


def test_keys_in_an_empty_message_index_do_nothing_and_do_not_trap(
		world, monkeypatch):
	"""The empty pane must not be a hole the operator falls into: the
	movement keys are inert, and focus can still leave."""
	view = from_jobs(world)
	monkeypatch.setattr(type(view), "thread_rows", lambda self: [])
	painted(view)
	for key in (ord("j"), ord("k"), ord("n"), ord("p")):
		view.handle(key)
		painted(view)
		assert view.msg_cursor is None
	view.handle(TAB)
	assert view.focus != DETAIL_ENTRY_FOCUS, \
		"focus could not leave the empty Message index"
	view.handle(ESC)
	assert view.mode == "table", "Esc could not leave an empty detail"


def test_marking_seen_with_nothing_selected_writes_nothing(world):
	"""`s` is the one writer in this view. With no Message selected it
	must do nothing at all rather than reaching for the authority —
	which is the state an empty index leaves it in."""
	view = from_jobs(world)
	painted(view)
	view.msg_cursor = None
	before = view.store.last_seq()
	view.handle(ord("s"))
	assert view.store.last_seq() == before, "an empty `s` wrote an event"


# -- entry is read-only ------------------------------------------------------

def test_entering_detail_writes_nothing_and_marks_nothing_seen(world):
	"""The ruling is explicit that defaulting to the Message index must
	not mark anything seen. Asserted on the authority sequence AND on
	the personal New count, because a seen advance is exactly the write
	that would not move a Work row."""
	store = bw.Authority(world["database"])
	before_seq = store.last_seq()
	before_new = {key: value for key, value in pj.new_count(
		store, world["work"], viewer_team="lang",
		viewer_member="ada").items() if key != "snapshot_seq"}
	store.close()
	view = from_jobs(world)
	painted(view)
	view.handle(ord("j"))
	painted(view)
	store = bw.Authority(world["database"])
	try:
		assert store.last_seq() == before_seq, "entry wrote an event"
		assert {key: value for key, value in pj.new_count(
			store, world["work"], viewer_team="lang",
			viewer_member="ada").items()
			if key != "snapshot_seq"} == before_new, \
			"entry advanced a personal seen cursor"
	finally:
		store.close()


def test_leaving_and_re_entering_re_applies_the_default(world):
	"""`Esc` returns to the table, so the next Enter is a FRESH entry —
	not a return to an open view — and gets the default again. Stated
	because the ruling distinguishes the two and this console only has
	the first."""
	view = from_jobs(world)
	view.handle(BTAB)
	assert view.focus == "threads"
	view.handle(ESC)
	assert view.mode == "table"
	view.handle(ENTER)
	assert view.focus == DETAIL_ENTRY_FOCUS


# -- a fresh entry carries nothing from the Work before it -------------------

def test_a_fresh_entry_after_leaving_from_events_opens_on_messages(pair):
	"""Review 2026-08-20T12-31-04Z, P1. `detail_tab` survived `Esc`, so
	this exact live sequence opened the NEXT Work on Events — against
	the ruling that detail opens on Messages, and against the
	documentation.

	The earlier version of this suite could not see it: it only moved
	the Message PANE focus before leaving, which the entry helper always
	reset. This leaves from the other TAB, and opens a DIFFERENT Work
	through a real entry path, which is the shape the defect needed."""
	view = console(pair)
	view.handle(ENTER)                       # Work A
	assert view.detail_tab == "messages"
	view.handle(NEXT_TAB)
	assert view.detail_tab == "events", "the tab did not switch"
	view.handle(ESC)
	assert view.mode == "table"
	view.handle(ord("j"))                    # select Work B
	view.handle(ENTER)
	assert view.detail_work == pair["b"], "the second Work did not open"
	assert view.detail_tab == "messages", \
		"a fresh entry opened on the tab the PREVIOUS Work was left on"
	assert view.focus == DETAIL_ENTRY_FOCUS


def test_re_entering_the_same_work_from_events_also_opens_on_messages(pair):
	"""The same sequence without changing Work — because "fresh entry"
	is about the ENTRY, not about which Work it lands on."""
	view = console(pair)
	view.handle(ENTER)
	view.handle(NEXT_TAB)
	view.handle(ESC)
	view.handle(ENTER)
	assert view.detail_work == pair["a"]
	assert view.detail_tab == "messages"


def test_a_fresh_entry_leaves_no_events_state_from_the_previous_work(pair):
	"""The same gap one level down, found while correcting P1: the
	Events cursor, page and pane focus survived `Esc` too, so the next
	Work's Events tab — one `]` away — opened on ANOTHER Work's page.

	`event_before` is the one that matters most: a page cursor is a
	sequence belonging to the Work it was read from, so carrying it
	across is not merely stale, it is wrong."""
	view = console(pair)
	view.handle(ENTER)
	view.handle(NEXT_TAB)
	painted(view, height=14)
	view.handle(ord("n"))                    # page to older events
	painted(view, height=14)
	view.handle(CTRL_W)
	view.handle(ord("j"))                    # focus the event reader
	assert view.event_before is not None, "the Events page did not move"
	assert view.event_focus == "reader"
	view.handle(ESC)
	view.handle(ord("j"))
	view.handle(ENTER)                       # Work B, fresh
	assert view.event_before is None, \
		"the new Work inherited the previous Work's Events page cursor"
	assert view.event_cursor is None
	assert view.event_focus == "index"
	assert view.event_skip == 0


def test_an_in_detail_tab_round_trip_still_preserves_both_sides(pair):
	"""The correction must not overreach. `[`/`]` inside ONE open detail
	view is not an entry, so each tab keeps its own focus and cursor —
	the property `_switch_tab` exists for."""
	view = console(pair)
	view.handle(ENTER)
	view.handle(BTAB)                        # Messages: choose Threads
	assert view.focus == "threads"
	view.handle(NEXT_TAB)                    # Events
	painted(view, height=14)
	view.handle(CTRL_W)
	view.handle(ord("j"))                    # Events: choose the reader
	assert view.event_focus == "reader"
	view.handle(PREV_TAB)                    # back to Messages
	assert view.detail_tab == "messages"
	assert view.focus == "threads", \
		"the round trip reset the Messages pane the operator chose"
	view.handle(NEXT_TAB)                    # and back to Events
	assert view.event_focus == "reader", \
		"the round trip reset the Events pane the operator chose"


def test_switching_tabs_inside_detail_preserves_each_tabs_own_focus(world):
	"""The other half of the same distinction: `[`/`]` moves WITHIN an
	open detail view, so it is not a fresh entry and must not reset
	anything."""
	view = from_jobs(world)
	view.handle(BTAB)
	assert view.focus == "threads"
	view.handle(NEXT_TAB)               # to Events
	assert view.detail_tab == "events"
	view.handle(PREV_TAB)               # back to Messages
	assert view.detail_tab == "messages"
	assert view.focus == "threads", \
		"a tab round trip reset the pane focus the operator chose"
