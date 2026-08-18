"""W29: `Messages (total/unseen)` describes the Thread, not the page.

The heading formatted `len(messages)` — the loaded page. So a Thread
holding forty Messages rendered `Messages (10)` whenever the page size
was ten, and an operator could not reconcile the heading with the
conversation in front of them or see how much remained unseen.

Both numbers are whole-Thread facts read from the same canonical
snapshot. The paging continuation beside them answers a different
question and is unchanged.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="the first message")
	yield {"store": store, "config": config_path,
	       "work": born["work_id"], "thread": born["thread"]}
	store.close()


def _say(world, count, author="ada"):
	for index in range(count):
		tr.post_thread(world["store"], world["thread"],
		               author_team="lang", author=author,
		               body=f"message {index}")


def _read(world, viewer="ada", **kwargs):
	return pj.thread(world["store"], world["thread"], viewer_team="lang",
	                 viewer_member=viewer, **kwargs)


def _mark_all_seen(world, viewer="ada"):
	view = _read(world, viewer=viewer, newest=True)
	tr.seen_thread(world["store"], world["thread"], team="lang",
	               member=viewer, up_to_seq=view["last_seq"])


# -- the projection --------------------------------------------------------

def test_total_counts_the_whole_thread_not_the_page(world):
	"""The defect, directly: a page smaller than the Thread."""
	_say(world, 24)
	view = _read(world, limit=5)
	assert len(view["messages"]) == 5, "the fixture did not page"
	assert view["total"] == 25, "total reported the page"


def test_total_is_stable_across_pages_and_directions(world):
	"""Paging is navigation, not content. Neither number may move."""
	_say(world, 24)
	first = _read(world, limit=5, newest=True)
	older = _read(world, limit=5, before=first["messages"][0]["seq"])
	forward = _read(world, limit=5, after=0)
	assert first["total"] == older["total"] == forward["total"] == 25
	assert first["new"] == older["new"] == forward["new"]


def test_a_one_message_thread_reads_one(world):
	"""The born Thread before anything is added: the smallest case the
	heading has to get right."""
	view = _read(world, viewer="bee")
	assert view["total"] == 1 and view["new"] == 1


def test_marking_seen_moves_only_the_unseen_count(world):
	_say(world, 9)
	before = _read(world, viewer="bee")
	assert (before["total"], before["new"]) == (10, 10)
	_mark_all_seen(world, viewer="bee")
	after = _read(world, viewer="bee")
	assert after["total"] == 10, "marking seen changed the total"
	assert after["new"] == 0


def test_a_new_message_moves_total_and_may_move_unseen(world):
	_mark_all_seen(world, viewer="bee")
	seen = _read(world, viewer="bee")
	assert (seen["total"], seen["new"]) == (1, 0)
	_say(world, 1)
	after = _read(world, viewer="bee")
	assert (after["total"], after["new"]) == (2, 1)


def test_the_counts_are_viewer_relative_only_in_unseen(world):
	"""Two participants disagree about unseen and never about total."""
	_say(world, 5)
	_mark_all_seen(world, viewer="ada")
	ada, bee = _read(world, viewer="ada"), _read(world, viewer="bee")
	assert ada["total"] == bee["total"] == 6
	assert ada["new"] == 0 and bee["new"] == 6


def test_a_page_exactly_the_limit_still_reports_the_thread(world):
	"""The case where page length and total coincide by accident —
	which is how a page-derived heading looks correct in testing."""
	_say(world, 4)
	view = _read(world, limit=5)
	assert len(view["messages"]) == view["total"] == 5
	assert view["next_after"] is None and view["next_before"] is None


# -- the heading -----------------------------------------------------------

class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		self.calls.append(str(text))

	def lines(self):
		return list(self.calls)


def _console(world, viewer="ada"):
	console = Console(world["store"], "lang", viewer,
	                  config_path=world["config"])
	console.detail_work = world["work"]
	console.mode = "detail"
	return console


def _heading(world, width=110, height=30, viewer="ada", console=None):
	console = console or _console(world, viewer)
	screen = Screen()
	console._render_detail(screen, height, width)
	return next((line for line in screen.lines()
	             if "Messages (" in line), None)


def test_the_heading_shows_the_pair(world):
	_say(world, 5)
	line = _heading(world, viewer="bee")
	assert line is not None, "no Messages heading was painted"
	assert "Messages (6/6)" in line, line


def test_the_heading_reports_zero_unseen_once_seen(world):
	_say(world, 5)
	_mark_all_seen(world, viewer="bee")
	line = _heading(world, viewer="bee")
	assert "Messages (6/0)" in line, line


def test_the_heading_does_not_shrink_to_the_page(world):
	"""The regression proper: a Thread larger than one page."""
	_say(world, 40)
	line = _heading(world)
	assert "Messages (41/" in line, \
		f"the heading reported the painted page: {line!r}"


def test_the_paging_continuation_survives_beside_the_counts(world):
	"""`(n: older)` answers a different question and stays."""
	_say(world, 40)
	line = _heading(world)
	assert "(n: older)" in line, line


def test_a_narrow_terminal_keeps_both_numbers(world):
	"""The counts are the point of the heading; they may not be the
	first thing a narrow layout drops."""
	_say(world, 40)
	line = _heading(world, width=60, height=20)
	assert line is not None and "Messages (41/" in line, line


def test_paging_the_pane_changes_neither_number(world):
	"""Navigation is not mutation: reading further back must not move
	a count the operator is using to judge the conversation."""
	_say(world, 40)
	import re

	def counts(line):
		# the COUNTS only: the focus marker beside them legitimately
		# moves with the pane focus, and is a different fact.
		return re.search(r"Messages \((\d+)/(\d+)\)", line).groups()

	console = _console(world)
	console.focus = "index"
	before = _heading(world, console=console)
	console.handle(ord("n"))
	after = _heading(world, console=console)
	assert counts(after) == counts(before), \
		f"paging moved the counts: {before!r} -> {after!r}"
	assert "(n: older)" in before
