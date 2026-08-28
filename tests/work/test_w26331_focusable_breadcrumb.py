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
from baton_work.tui.app import (Console, breadcrumb_window)   # noqa: E402
import fixtures as fx                                         # noqa: E402


class Screen:
	def __init__(self, height=24, width=100):
		self.height, self.width = height, width
		self.calls = []

	def erase(self):
		self.calls = []

	def getmaxyx(self):
		return self.height, self.width

	def addnstr(self, y, x, text, *_rest):
		self.calls.append((y, x, str(text)))

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
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
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


def test_focus_starts_at_the_deepest_crumb_and_horizontal_keys_hold(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	view.handle(9)
	view.handle(9)
	assert view.crumb_focus
	assert view.crumb_key == f"work:{world['grand']['work_id']}"
	view.handle(ord("h"))
	assert view.crumb_key == f"work:{world['child']['work_id']}"
	for _ in range(20):
		view.handle(curses.KEY_LEFT)
	assert view.crumb_key == "top:jobs"
	for _ in range(20):
		view.handle(curses.KEY_RIGHT)
	assert view.crumb_key == f"work:{world['grand']['work_id']}"


def test_direct_ancestor_jump_is_one_action_and_one_back(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, f"work:{world['child']['work_id']}")
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
	assert view.crumb_key == f"work:{world['child']['work_id']}"


@pytest.mark.parametrize("tab", ["jobs", "messages", "events"])
def test_work_to_work_jump_preserves_the_local_tab(world, tab):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	if tab == "jobs":
		view._switch_tab(-1)
	elif tab == "events":
		view._switch_tab(1)
	assert view.context_tab() == tab
	select_crumb(view, f"work:{world['child']['work_id']}")
	view.handle(13)
	assert view.context_tab() == tab
	assert view.context_work() == world["child"]["work_id"]


def test_enter_on_the_current_crumb_is_a_pure_noop(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, f"work:{world['grand']['work_id']}")
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
	select_crumb(view, f"work:{world['grand']['work_id']}")
	view.handle(ord("h"))
	view.handle(ord("l"))
	view.handle(curses.KEY_DOWN)
	world["store"].conn.set_trace_callback(None)
	assert statements == []


def test_viewport_uses_whole_selectors_and_both_omission_markers():
	items = [{"key": f"k{index}", "label": "very long title " + str(index),
	          "compact": f"W{index}"} for index in range(5)]
	window = breadcrumb_window(items, "k2", len("… > W2 > …"))
	assert [piece["text"] for piece in window] == ["…", "W2", "…"]
	assert all(piece["text"] != "very long tit" for piece in window)


def test_focused_footer_names_ordinal_and_exact_selector(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	select_crumb(view, f"work:{world['child']['work_id']}")
	screen = Screen(width=90)
	view.render(screen)
	assert screen.row(screen.height - 2).startswith("breadcrumb 3/4: W3"), \
		screen.row(screen.height - 2)
