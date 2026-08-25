"""W96: the dependency view opens with `d`, and `b` opens nothing.

`work/records/2026/08/finding-tui-dependency-key-d/`, confirmed and
reviewer-revalidated 2026-08-23.

The key was `b`, inherited from the earlier blocker/link presentation. Since
W4996 the page has shown BOTH what a Work waits on and what waits on it, so
`b` named half of what it opened; the action is `[d] deps` now.

`b` is REMOVED — not aliased, not deprecated, not hidden. The positive cases
for `d` live beside the entries they belong to (W4996 for table and Search
entry, W17 for the advertised label, W292 for the breadcrumb segment). What
this file owns is the half a rename cannot prove by deleting the old cases:
that pressing `b` now does NOTHING, in both entry contexts and on a real
terminal. An alias would keep every renamed case green.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))), "src"))

import curses                                                 # noqa: E402
import pty as _pty                                            # noqa: E402

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)

	def make(title):
		return tr.create_work(store, team="lang", kind="bug", title=title,
		                      origin="self-initiated",
		                      classification="design-choice",
		                      author="ada", body="x")["work_id"]

	consumer = make("the consumer")
	blocker = make("the blocker")
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="the consumer waits on it")
	yield {"store": store, "config": config,
	       "consumer": consumer, "blocker": blocker}
	store.close()


def console(world, tmp_path):
	return Console(world["store"], "lang", "ada",
	               config_path=str(tmp_path / "console.json"))


def select(view, work):
	ids = [row["id"] for row in view.rows()]
	view.cursor = ids.index(work)
	view.selected_id = work


def state(view):
	"""Everything the operator would notice moving."""
	return (view.mode, list(view.path), view.cursor, view.selected_id,
	        list(view.nav_segments()), getattr(view, "graph_center", None))


# -- the table entry ---------------------------------------------------------

def test_b_does_nothing_in_the_work_table(world, tmp_path):
	"""The removal, asserted rather than inferred from a deleted case.

	Deleting the old positive case proves only that nobody tests `b` any
	more. This proves the key is UNBOUND: mode, breadcrumb trail, cursor,
	selection and graph centre all come out exactly as they went in, and
	no graph was opened."""
	view = console(world, tmp_path)
	select(view, world["consumer"])
	before = state(view)
	view.handle(ord("b"))
	assert view.mode == "table", "`b` still opened something"
	assert view.graph_center is None, "`b` opened a dependency graph"
	assert state(view) == before, "`b` moved the table underneath the operator"
	# And the replacement works from the state `b` left behind, so the
	# removal did not cost the action its entry point.
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.graph_center == world["consumer"]


def test_b_does_nothing_in_search_results(world, tmp_path):
	"""Search dispatches before the table branch, so it is its own
	binding and its own removal."""
	view = console(world, tmp_path)
	view.handle(ord("/"))
	for char in "the consumer":
		view.handle(ord(char))
	view.handle(curses.KEY_ENTER)
	assert view.mode == "search"
	rows, _hidden = view.visible_rows(view.search_rows())
	assert [row["id"] for row in rows] == [world["consumer"]], rows
	before = (view.mode, view.search_query, view.cursor, view.selected_id,
	          view.search_page, view.graph_center)
	view.handle(ord("b"))
	assert view.mode == "search", "`b` left the search results"
	assert view.graph_center is None, "`b` opened a dependency graph"
	assert (view.mode, view.search_query, view.cursor, view.selected_id,
	        view.search_page, view.graph_center) == before, \
		"`b` disturbed the search state"
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.graph_center == world["consumer"]


# -- and on a real terminal --------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_b_leaves_the_table_on_a_real_terminal(world):
	"""What an operator actually sees.

	An in-process case reads the console's own state; this reads the
	bytes curses painted. A stray alias, a duplicated branch, or a
	binding reintroduced further down the dispatcher would show up here
	as the graph appearing one keystroke early."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.6),
		(b"b", 0.6),                  # unbound: the table must stay
		(b"d", 0.6),                  # the ruled key opens the graph
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text
	after_b = "\n".join(ptyharness.replay(steps[1]))
	assert "[d] deps" in after_b, \
		"`b` left the Work table; the footer is gone"
	assert "--blocks-->" not in after_b, \
		"`b` opened the dependency graph — it is still bound"
	after_d = "\n".join(ptyharness.replay(steps[2]))
	assert "--blocks-->" in after_d, after_d
