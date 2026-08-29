"""W26331: breadcrumbs are focusable navigation, not decorative prose."""

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
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import (Console, _cells, breadcrumb_window)  # noqa: E402
import fixtures as fx                                         # noqa: E402


class Screen:
	def __init__(self, height=24, width=100):
		self.height, self.width = height, width
		self.calls = []
		self.attrs = []

	def erase(self):
		self.calls = []
		self.attrs = []

	def getmaxyx(self):
		return self.height, self.width

	def addnstr(self, y, x, text, *_rest):
		self.calls.append((y, x, str(text)))
		self.attrs.append((y, x, str(text), _rest[1] if len(_rest) > 1 else 0))

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def row(self, y):
		cells = [" "] * self.width
		for at_y, x, text in self.calls:
			if at_y != y:
				continue
			for offset, character in enumerate(text):
				if x + offset < self.width:
					cells[x + offset] = character
		return "".join(cells).rstrip()


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	root = tr.create_work(store, team="lang", kind="bug", title="root title",
	                      origin="external-report", author="ada",
	                      classification="suspected-defect", body="root")
	child = tr.create_work(store, team="lang", kind="bug", title="child title",
	                       origin="decomposition", author="ada",
	                       classification="suspected-defect", body="child",
	                       parent=root["work_id"])
	grand = tr.create_work(store, team="lang", kind="bug", title="grand title",
	                       origin="decomposition", author="ada",
	                       classification="suspected-defect", body="grand",
	                       parent=child["work_id"])
	yield {"config": config, "store": store, "root": root,
	       "child": child, "grand": grand}
	store.close()


def console(world):
	return Console(world["store"], "lang", "ada",
	               config_path=world["config"])


def select_crumb(view, key):
	view._enter_breadcrumb()
	view.crumb_key = key


def work_crumb(view, work_id, occurrence=0):
	return [item for item in view.breadcrumb_items()
	        if item["kind"] == "work" and item["work"] == work_id][occurrence]


def test_focus_starts_at_the_deepest_crumb_and_horizontal_keys_hold(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	view.handle(9)
	view.handle(9)
	assert view.crumb_focus
	assert view.crumb_key == work_crumb(view, world["grand"]["work_id"])["key"]
	view.handle(ord("h"))
	assert view.crumb_key == work_crumb(view, world["child"]["work_id"])["key"]
	for _ in range(20):
		view.handle(curses.KEY_LEFT)
	assert view.crumb_key == "top:jobs"
	for _ in range(20):
		view.handle(curses.KEY_RIGHT)
	assert view.crumb_key == work_crumb(view, world["grand"]["work_id"])["key"]


def test_direct_ancestor_jump_is_one_action_and_one_back(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, work_crumb(view, world["child"]["work_id"])["key"])
	before = len(view.nav)
	view.handle(13)
	assert len(view.nav) == before + 1
	assert view.detail_work == world["child"]["work_id"]
	assert view.nav_segments() == ["Jobs", "root title", "child title"]
	view.handle(27)
	assert view.detail_work == world["grand"]["work_id"]
	assert view.nav_segments() == ["Jobs", "root title", "child title",
	                               "grand title"]
	assert view.crumb_focus
	assert view.crumb_key == work_crumb(view, world["child"]["work_id"])["key"]


@pytest.mark.parametrize("tab", ["jobs", "messages", "events"])
def test_work_to_work_jump_preserves_the_local_tab(world, tab):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	if tab == "jobs":
		view._switch_tab(-1)
	elif tab == "events":
		view._switch_tab(1)
	assert view.context_tab() == tab
	select_crumb(view, work_crumb(view, world["child"]["work_id"])["key"])
	view.handle(13)
	assert view.context_tab() == tab
	assert view.context_work() == world["child"]["work_id"]


def test_enter_on_the_current_crumb_is_a_pure_noop(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, work_crumb(view, world["grand"]["work_id"])["key"])
	before = (len(view.nav), view._nav_capture())
	view.handle(13)
	assert (len(view.nav), view._nav_capture()) == before


def test_jobs_jump_keeps_the_deep_page_for_one_back(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, "top:jobs")
	view.handle(13)
	assert view.location == [] and view.mode == "table"
	view.handle(27)
	assert view.detail_work == world["grand"]["work_id"]
	assert view.crumb_focus and view.crumb_key == "top:jobs"


def test_a_search_crumb_restores_its_exact_page_state(world):
	view = console(world)
	view.search_input = "grand"
	view._search_entry_key(13)
	view.search_after = 17
	view.search_page = 4
	view.cursor = 2
	view.selected_id = world["grand"]["work_id"]
	view._enter_detail(world["grand"]["work_id"], came_from="search")
	search = next(item for item in view.breadcrumb_items()
	              if item["kind"] == "search")
	select_crumb(view, search["key"])
	view.handle(13)
	assert (view.mode, view.search_query, view.search_after,
	        view.search_page, view.cursor, view.selected_id) == (
		"search", "grand", 17, 4, 2, world["grand"]["work_id"])
	view.handle(27)
	assert view.mode == "detail" and view.detail_work == world["grand"]["work_id"]


def test_graph_recenter_repeated_work_crumbs_have_unique_navigation(world):
	root = world["root"]["work_id"]
	alpha = tr.create_work(
		world["store"], team="lang", kind="bug", title="alpha",
		origin="self-initiated", author="ada",
		classification="suspected-defect", body="alpha")["work_id"]
	beta = tr.create_work(
		world["store"], team="lang", kind="bug", title="beta",
		origin="self-initiated", author="ada",
		classification="suspected-defect", body="beta")["work_id"]
	for consumer in (alpha, beta):
		tr.add_dependency(world["store"], consumer, root, actor_team="lang",
		                  actor="ada", rationale="shared graph ancestor")
	view = console(world)
	view._open_graph(root)
	view.graph_anchor = alpha
	view.handle(13)
	view.graph_anchor = root
	view.handle(13)
	view.graph_anchor = beta
	view.handle(13)
	items = view.breadcrumb_items()
	roots = [item for item in items
	         if item["kind"] == "work" and item.get("work") == root]
	assert len(roots) == 2 and roots[0]["key"] != roots[1]["key"]
	assert view.nav_segments() == ["Jobs", "root title", "deps", "alpha",
	                               "deps", "root title", "deps", "beta",
	                               "deps"]

	view._enter_breadcrumb()
	keys = [item["key"] for item in items]
	for expected in reversed(keys[:-1]):
		view.handle(ord("h"))
		assert view.crumb_key == expected
	select_crumb(view, roots[1]["key"])
	screen = Screen()
	view.render(screen)
	selected = [text for y, _x, text, attr in screen.attrs
	            if y == 0 and attr & curses.A_REVERSE]
	assert selected == ["root title"]

	deep_location = view.nav_segments()
	for occurrence in (1, 0):
		root_item = work_crumb(view, root, occurrence)
		before = len(view.nav)
		select_crumb(view, root_item["key"])
		view.handle(13)
		assert len(view.nav) == before + 1
		view.handle(27)
		assert view.nav_segments() == deep_location
		assert view.crumb_key == root_item["key"]


@pytest.mark.parametrize("key", [curses.KEY_UP, ord("k")], ids=["Up", "k"])
@pytest.mark.parametrize("page", ["jobs", "search", "links", "pokes", "mine"])
def test_focused_up_is_a_noop_on_every_single_body_page(world, page, key):
	view = console(world)
	if page == "jobs":
		view._open_root(world["root"]["work_id"])
		rows, _hidden = view.table_rows()
		view.cursor = 1
		view.selected_id = rows[1]["id"]
		capture = lambda: (view.cursor, view.selected_id)
	elif page == "search":
		view.search_input = "title"
		view._search_entry_key(13)
		rows, _hidden = view.visible_rows(view.search_rows())
		view.cursor = 1
		view.selected_id = rows[1]["id"]
		capture = lambda: (view.cursor, view.selected_id)
	elif page == "links":
		neighbour = tr.create_work(
			world["store"], team="lang", kind="bug", title="neighbour",
			origin="self-initiated", author="ada",
			classification="suspected-defect", body="neighbour")["work_id"]
		tr.add_dependency(world["store"], world["grand"]["work_id"],
		                  neighbour, actor_team="lang",
		                  actor="ada", rationale="graph body selection")
		view._open_graph(world["grand"]["work_id"])
		keys = view._graph_keys(view._graph_row_set())
		view.graph_anchor = keys[-1]
		capture = lambda: (view.graph_anchor, view.links_cursor)
	elif page == "pokes":
		tr.poke(world["store"], actor_team="lang", actor="grace",
		        target="lang.ada", request="first")
		tr.poke(world["store"], actor_team="lang", actor="ada",
		        target="lang.ada", request="second")
		view._open_pokes()
		rows, _older = view.poke_rows()
		view.poke_cursor = 1
		view.poke_seq = rows[1]["poke"]
		capture = lambda: (view.poke_cursor, view.poke_seq)
	else:
		view._open_mine()
		rows = view.mine_rows()
		view.cursor = 1
		view.selected_id = rows[1]["id"]
		capture = lambda: (view.cursor, view.selected_id)
	view._enter_breadcrumb()
	before = capture()
	view.handle(key)
	assert view.crumb_focus
	assert capture() == before


def test_single_body_tab_and_down_cycle_through_the_breadcrumb(world):
	view = console(world)
	view._open_root(world["root"]["work_id"])
	view.handle(9)
	assert view.crumb_focus
	view.handle(curses.KEY_DOWN)
	assert not view.crumb_focus
	view.handle(curses.KEY_UP)
	assert view.crumb_focus, "Up at the first body row did not reach the crumb"


def test_ctrl_w_connects_the_top_detail_pane_to_the_breadcrumb(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	view.focus = "threads"
	view.handle(23)
	view.handle(ord("k"))
	assert view.crumb_focus
	view.handle(23)
	view.handle(ord("j"))
	assert not view.crumb_focus and view.focus == "threads"


def test_focus_movement_executes_no_authority_statement(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	view.breadcrumb_items()  # warm the same cached ancestry the header paints
	statements = []
	world["store"].conn.set_trace_callback(statements.append)
	select_crumb(view, work_crumb(view, world["grand"]["work_id"])["key"])
	view.handle(ord("h"))
	view.handle(ord("l"))
	view.handle(curses.KEY_DOWN)
	world["store"].conn.set_trace_callback(None)
	assert statements == []


def test_viewport_uses_whole_selectors_and_both_omission_markers():
	items = [{"key": f"k{index}", "label": "very long title " + str(index),
	          "compact": f"W{index}"} for index in range(5)]
	window = breadcrumb_window(items, "k2", _cells("… > W2 > …"))
	assert [piece["text"] for piece in window] == ["…", "W2", "…"]
	assert all(piece["text"] != "very long tit" for piece in window)


def test_viewport_measures_wide_and_combining_labels_in_terminal_cells():
	wide = [{"key": "wide", "label": "界" * 6, "compact": "W2"}]
	assert [piece["text"] for piece in breadcrumb_window(wide, "wide", 10)] \
		== ["W2"]
	combining = "e\N{COMBINING ACUTE ACCENT}" * 4
	combined = [{"key": "combined", "label": combining, "compact": "W3"}]
	assert _cells(combining) == 4
	assert [piece["text"] for piece in breadcrumb_window(
		combined, "combined", 4)] == [combining]


def test_wide_selected_title_falls_back_without_covering_right_edge(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	view._work_ancestry = lambda work_id: [
		{"id": work_id, "title": "界" * 20}]
	view.work_filter = {"priority": "normal"}
	view._dispatch_tag = lambda: "Dispatch:PAUSED"
	view._enter_breadcrumb()
	screen = Screen(width=60)
	view.render(screen)
	header = [text for y, _x, text in screen.calls if y == 0]
	assert "界" * 20 not in header
	assert world["grand"]["work_id"].rsplit("-", 1)[-1] in header
	assert "Dispatch:PAUSED" in header
	assert "Filter:1" in header
	assert "lang.ada" in header


def test_focused_footer_names_ordinal_and_exact_selector(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, work_crumb(view, world["child"]["work_id"])["key"])
	screen = Screen(width=90)
	view.render(screen)
	assert screen.row(screen.height - 2).startswith("breadcrumb 3/4: W3"), \
		screen.row(screen.height - 2)
