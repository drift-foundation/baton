"""W292: one breadcrumb-scoped navigation model for the whole console.

`work/records/2026/08/finding-work-detail-breadcrumb-navigation/`.

The console used to paint the global `[Jobs] [Teams] [Inbox]` row and a
drilled page's own `[Messages] [Events]` row at the same time. Two tab
rows on one screen imply two peer navigation surfaces, when one of them
is a drill-down INSIDE the other — so the operator could not tell where
they were or what Back would do.

The confirmed model is universal, not Work-specific: a top-level page
shows its tabs; entering anything replaces that row with the breadcrumb
for the whole path plus that page's own local tabs; Back/Esc pops
exactly one segment and restores the level it reveals. These cases pin
the model itself and the two drillable surfaces that exist today — Work
detail and the Jobs table re-root — plus the search and Inbox entry
paths, which must reach the same model without losing what they already
promised.
"""

from __future__ import annotations

import curses
import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


class Screen:
	def __init__(self, height=24, width=100):
		self.calls = []
		self._size = (height, width)

	def erase(self):
		self.calls = []

	def getmaxyx(self):
		return self._size

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def clrtoeol(self):
		pass

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text),
		                   rest[1] if len(rest) > 1 else 0))

	def lines(self):
		return [text for _y, _x, text, _attr in self.calls]

	def row(self, y):
		"""One painted row, composed in paint order — the header
		overdraws, so the last write at a column wins, exactly as a real
		terminal resolves it."""
		width = self._size[1]
		cells = [" "] * width
		for at_y, x, text, _attr in self.calls:
			if at_y != y:
				continue
			for offset, char in enumerate(text):
				if 0 <= x + offset < width:
					cells[x + offset] = char
		return "".join(cells).rstrip()

	def attr_of(self, label):
		return next((attr for _y, _x, text, attr in self.calls
		             if text == label), None)


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	root = tr.create_work(store, team="lang", kind="bug", title="the root",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="root opener")
	child = tr.create_work(store, team="lang", kind="bug", title="the child",
	                       origin="decomposition",
	                       classification="suspected-defect", author="ada",
	                       body="child opener", parent=root["work_id"])
	grand = tr.create_work(store, team="lang", kind="bug",
	                       title="the grandchild", origin="decomposition",
	                       classification="suspected-defect", author="ada",
	                       body="grand opener", parent=child["work_id"])
	other = tr.create_work(store, team="lang", kind="bug",
	                       title="a second root", origin="external-report",
	                       classification="suspected-defect", author="ada",
	                       body="second opener")
	# A dependency reaching INTO the deep tree, so the neighbour view has
	# a far Work whose real ancestry is more than one level.
	tr.add_dependency(store, other["work_id"], grand["work_id"],
	                  actor_team="lang", actor="ada",
	                  rationale="the second root waits on the grandchild")
	yield {"config": config, "store": store, "root": root, "child": child,
	       "grand": grand, "other": other}
	store.close()


def console(world, work_filter=None):
	return Console(world["store"], "lang", "ada",
	               config_path=world["config"], work_filter=work_filter)


def header(view, height=24, width=100):
	screen = Screen(height, width)
	view.render(screen)
	return screen.row(0)


def painted(view, height=24, width=100):
	screen = Screen(height, width)
	view.render(screen)
	return screen


def local(id_):
	return id_.rsplit("-", 1)[-1]


# -- the model -----------------------------------------------------------

def test_the_global_tab_row_is_the_top_level_only(world):
	view = console(world)
	assert view.nav == [] and view.nav_segments() == []
	assert header(view).startswith("[Jobs 3]  [Teams]  [Inbox")

	view.handle(curses.KEY_ENTER)
	row = header(view)
	assert view.nav, "entering a Work page recorded no navigation path"
	for label in ("[Jobs 3]  [Teams]", "[Teams]", "[Inbox"):
		assert label not in row, row
	assert row.startswith("Jobs > "), row
	# The drilled page's OWN tabs are still there, and exactly one is
	# active — the local row is not what this ruling removed. W6814
	# makes them three, all scoped to the Work this page is about.
	labels = [label for _name, label in view.detail_tab_segments()]
	assert labels == ["[Jobs]", "[Messages]", "[Events]"], labels
	# The painter writes each label at its own column so exactly one can
	# carry the active weight, so the labels are separate calls.
	drawn = painted(view).lines()
	for label in labels:
		assert label in drawn, (label, drawn[:8])
	screen = painted(view)
	assert screen.attr_of("[Jobs]") != screen.attr_of("[Messages]"), \
		"the local row does not distinguish its active tab"


def test_the_trail_names_the_whole_path_and_ends_where_it_is(world):
	view = console(world)
	view.handle(curses.KEY_ENTER)              # the root's detail
	assert view.nav_segments() == ["Jobs", "the root"]
	assert view.nav_text() == "Jobs > the root"
	# Identity keeps the right edge whatever the location says.
	assert header(view).rstrip().endswith("lang.ada")


def test_direct_grandchild_entry_is_one_action_and_one_back(world):
	"""W6814 SUPERSEDES W292's rule that the trail and the Back stack
	are the same list.

	W292 read "do not paint ancestry that one Back skips" as a reason to
	make every painted ancestor its own Back step. That charged the
	operator two extra Escs — through two Work pages they never asked to
	open — for one Enter into a row the screen was already showing.

	The trail is structural and still names the whole containment path;
	the stack is explicit navigation ACTIONS, and one entry is one Back.
	Both halves are asserted here so neither can drift back into the
	other."""
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	assert view.nav_segments() == ["Jobs", "the root", "the child",
	                               "the grandchild"], view.nav_segments()
	assert view.detail_work == world["grand"]["work_id"]
	assert len(view.nav) == 1, \
		"one navigation action recorded more than one Back step"

	view.handle(27)
	assert view.nav == [] and view.mode == "table"
	assert header(view).startswith("[Jobs "), "the last Back left the top level"

	# Explicitly opening the intermediate parent first IS two actions,
	# and is therefore two Back steps — the other half of the ruling.
	view._enter_detail(world["child"]["work_id"], came_from="table")
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	assert len(view.nav) == 2
	view.handle(27)
	assert view.detail_work == world["child"]["work_id"], \
		"Back skipped a level the operator had explicitly opened"
	view.handle(27)
	assert view.nav == [] and view.mode == "table"


def test_back_from_detail_restores_the_caller_selection(world):
	"""W6814: activation opens a childless Job's detail, so the walk
	aims at the grandchild. What the case pins is unchanged — Back
	returns the caller's exact row and cursor."""
	view = console(world)
	rows, _hidden = view.table_rows()
	assert len(rows) > 2
	view.handle(ord("j"))
	view.handle(ord("j"))
	chosen = view.selected_id
	assert chosen == world["grand"]["work_id"], chosen
	view.handle(curses.KEY_ENTER)
	assert view.mode == "detail", "a childless Job did not open its detail"
	while view.nav:
		view.handle(27)
	assert view.mode == "table"
	assert view.selected_id == chosen, \
		"Back reset the caller's stable selection"
	assert view.cursor == 2


def test_table_re_root_is_a_drill_that_restores_its_opener(world):
	view = console(world)
	view.handle(ord("j"))
	opened_at = (view.cursor, view.selected_id)
	view.handle(ord("u"))
	assert view.nav_segments()[0] == "Jobs"
	assert view.nav_segments()[-1] in ("the child", "a second root",
	                                   "the root")
	assert "[Jobs " not in header(view)
	while view.nav:
		view.handle(27)
	assert (view.cursor, view.selected_id) == opened_at, \
		"the re-root Back did not restore the row that opened it"
	assert view.path == []
	assert header(view).startswith("[Jobs ")


def select(view, title):
	"""Put the table cursor on the row with this title, by identity."""
	rows, _hidden = view.visible_rows(view.rows())
	view.cursor = next(index for index, row in enumerate(rows)
	                   if row["title"] == title)
	view.selected_id = rows[view.cursor]["id"]
	return rows[view.cursor]["id"]


def test_a_nested_re_root_appends_one_segment_not_the_whole_ancestry(world):
	"""Round-1 review, [P1].

	`u` on a Work and then `u` on its child used to seed the FULL
	ancestry both times, producing `Jobs > root > root > child` — a
	duplicated segment that is not a containment level, and two Backs
	that revealed visually identical scopes."""
	view = console(world)
	select(view, "the root")
	view.handle(ord("u"))
	assert view.nav_segments() == ["Jobs", "the root"]

	select(view, "the child")
	view.handle(ord("u"))
	assert view.nav_segments() == ["Jobs", "the root", "the child"], \
		"the nested re-root repeated ancestry the stack already had"
	assert view.path == [world["root"]["work_id"], world["child"]["work_id"]]

	view.handle(27)
	assert view.nav_segments() == ["Jobs", "the root"], \
		"one Back did not reveal exactly one level"
	assert view.path == [world["root"]["work_id"]]

	view.handle(27)
	assert view.nav == [] and view.mode == "table"
	assert view.path == [], "the last Back did not reach the Jobs root"
	assert header(view).startswith("[Jobs ")


def test_a_works_own_pages_are_tabs_of_one_level_not_two_levels(world):
	"""W6814 SUPERSEDES W292's `the root · detail` second segment.

	A re-rooted subtree and that Work's Messages are two pages of ONE
	Work, and the confirmed model makes them two TABS of one contextual
	page rather than two levels of a path. So the trail does not grow,
	the tab move records no history, and one Esc still leaves the Work
	the operator actually opened."""
	view = console(world)
	select(view, "the root")
	view.handle(ord("u"))
	assert view.nav_segments() == ["Jobs", "the root"]
	depth = len(view.nav)
	view.handle(ord("]"))
	assert view.mode == "detail" and view.detail_tab == "messages"
	assert view.detail_work == world["root"]["work_id"], \
		"the local tab moved to a Work other than the page's root"
	assert view.nav_segments() == ["Jobs", "the root"], view.nav_segments()
	assert len(view.nav) == depth, "a local tab move recorded history"
	view.handle(27)
	assert view.nav == [] and view.mode == "table"


def select_neighbour(view):
	"""Move the graph selection onto the first row that is not the center.

	BOUNDED and direction-agnostic. The center sits BETWEEN the upstream
	and downstream layers, so which key reaches a neighbour depends on the
	fixture's shape — and a `while` that assumed one direction spins
	forever on a Work whose only edges are on the other side."""
	rows = view._graph_row_set()
	assert any(row["work"] != view.graph_center for row in rows), rows
	for key in (ord("k"), ord("j")):
		for _step in range(len(rows)):
			if view.graph_anchor != view.graph_center:
				return
			view.handle(key)
	assert view.graph_anchor != view.graph_center, "no neighbour was reachable"


def test_a_linked_drill_through_rebuilds_the_far_works_own_ancestry(world):
	"""Round-1 review, [P1] — restated for the view that replaced it.

	W4996's approved contract changed what Enter DOES here: the `[b]`
	page is the dependency neighbourhood graph, and Enter RECENTERS it on
	the selected Work, pushing one navigation frame. It no longer unwinds
	the stack and re-roots the Jobs tree at the far Work.

	The property this case has always protected survives that change and
	is what is asserted: a drill from this page pushes its own frames, the
	trail names where the operator actually is, and each Back reveals
	exactly one level — ending at the table they left. What is gone is the
	cross-TREE jump, which the contract removed deliberately; that removal
	is recorded in the dossier rather than absorbed here."""
	view = console(world)
	select(view, "a second root")
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.nav_segments() == ["Jobs", "a second root", "deps"], \
		view.nav_segments()
	center = view.graph_center

	# Recenter on the neighbour: one more frame, still in the graph.
	# Selection starts at the CENTER, which sits between the upstream and
	# downstream layers — so the neighbour is reached with `k` here, and
	# the case moves onto it deliberately rather than assuming a direction.
	select_neighbour(view)
	view.handle(curses.KEY_ENTER)
	assert view.mode == "links", "Enter left the dependency view"
	assert view.graph_center != center, "Enter did not recenter"
	assert view.nav_segments()[-1] == "deps", view.nav_segments()
	assert "the grandchild" in view.nav_segments(), view.nav_segments()

	# Back reveals exactly one level, and the first Back off the page
	# returns to the caller's table.
	view.handle(27)
	assert view.mode == "links" and view.graph_center == center
	assert view.nav_segments() == ["Jobs", "a second root", "deps"]
	view.handle(27)
	assert view.nav == [] and view.mode == "table"
	assert header(view).startswith("[Jobs ")


def test_a_drill_through_from_a_re_rooted_caller_carries_no_caller_ancestry(
		world):
	"""The same question under W4996's contract: what does the caller get
	back?

	The dependency page no longer re-roots the Jobs tree, so a caller's
	ancestry can no longer prefix an unrelated Work. What must still hold
	— and is the part that would actually hurt an operator — is that Back
	returns the RE-ROOTED caller exactly as it was, path included."""
	view = console(world)
	select(view, "the root")
	view.handle(ord("u"))
	rooted = list(view.path)
	# The re-rooted window shows the root's subtree; open the neighbour
	# view of the grandchild, whose dependent is outside that subtree.
	select(view, "the grandchild")
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view._graph_view()["edges"], \
		"the fixture dependency did not reach the neighbour view"
	select_neighbour(view)
	view.handle(curses.KEY_ENTER)
	assert view.mode == "links", "the dependency page re-rooted the tree"
	assert view.path == rooted, \
		"recentering the graph moved the caller's table underneath it"
	view.handle(27)
	view.handle(27)
	assert view.mode == "table" and view.path == rooted, \
		"Back did not restore the re-rooted caller"


def test_local_tab_keys_never_reach_the_global_row(world):
	view = console(world)
	view.handle(curses.KEY_ENTER)
	before = (view.tab, view.focus, view.selected_id, view.nav_segments())
	last = view.store.last_seq()
	for key in (ord("]"), ord("]"), ord("["), ord("[")):
		view.handle(key)
		assert view.tab == "jobs", "a local tab key moved the global tab"
	assert view.detail_tab in ("messages", "events")
	assert (view.tab, view.focus, view.selected_id, view.nav_segments()) \
		== before, "a local tab key disturbed the level around it"
	assert view.store.last_seq() == last, "tab movement wrote to the authority"


def test_brackets_still_move_the_global_tabs_at_the_top_level(world):
	"""W110's grammar is refined, not retired."""
	view = console(world)
	view.handle(ord("]"))
	assert view.tab == "teams"
	view.handle(ord("]"))
	assert view.tab == "inbox"
	view.handle(ord("["))
	assert view.tab == "teams"
	assert header(view).startswith("[Jobs 3]  [Teams]  [Inbox")


# -- the other entry paths ------------------------------------------------

def test_search_is_a_segment_and_keeps_its_exact_restoration(world):
	view = console(world)
	view.handle(ord("j"))
	table_at = (view.cursor, view.selected_id)
	view.handle(ord("/"))
	for char in "root":
		view.handle(ord(char))
	view.handle(10)
	assert view.mode == "search"
	assert view.nav_segments() == ["Jobs", "search: root"], view.nav_segments()
	assert "[Jobs " not in header(view)

	rows, _hidden = view.visible_rows(view.search_rows())
	assert rows, "the fixture search matched nothing"
	view.handle(curses.KEY_ENTER)
	assert view.mode == "detail"
	assert view.nav_segments()[:2] == ["Jobs", "search: root"], \
		"the Work scope did not nest under the search that opened it"

	while view.mode == "detail":
		view.handle(27)
	assert view.mode == "search", \
		"Back from a search result skipped the results page"
	view.handle(27)
	assert view.mode == "table" and view.nav == []
	assert (view.cursor, view.selected_id) == table_at, \
		"search lost its exact prior-table restoration"


def test_a_replacement_query_relabels_one_segment(world):
	view = console(world)
	view.handle(ord("/"))
	for char in "root":
		view.handle(ord(char))
	view.handle(10)
	view.handle(ord("/"))
	for char in "child":
		view.handle(ord(char))
	view.handle(10)
	assert view.nav_segments() == ["Jobs", "search: child"], \
		"a replacement query nested a second search inside the first"
	view.handle(27)
	assert view.nav == [] and view.mode == "table"


def test_the_inbox_handoff_lands_in_jobs_and_backs_out_there(world):
	"""The ruled exception, stated: an Inbox row LINKS into Jobs. Back
	returns to Jobs, which is where the operator now is — not to the
	Inbox they were handed over from."""
	view = console(world)
	view.tab = "inbox"
	view._enter_detail(world["root"]["work_id"], came_from="table")
	view.tab = "jobs"
	assert view.nav_segments() == ["Jobs", "the root"]
	view.handle(27)
	assert view.nav == [] and view.tab == "jobs" and view.mode == "table"
	assert header(view).startswith("[Jobs ")


def test_the_links_page_is_a_segment_too(world):
	view = console(world)
	view.handle(ord("d"))
	assert view.mode == "links"
	assert view.nav_segments()[0] == "Jobs"
	# W17 ruled the label reads "deps"; W4996 made the page the
	# dependency neighbourhood graph. The segment is still a segment.
	assert "deps" in view.nav_segments()[-1]
	assert "[Jobs " not in header(view)
	view.handle(27)
	assert view.mode == "table" and view.nav == []


# -- the active-filter disclosure -----------------------------------------

def test_a_drilled_header_still_discloses_an_active_filter(world):
	"""Round-2 review, [P1].

	W292 supersedes the global TAB ROW inside a drill. It does not
	supersede W5's ruling that an active filter is always disclosed in
	the header — and search results are themselves narrowed by that
	filter, so a drilled page with no disclosure would show a reduced
	result set with nothing saying why."""
	active = {"status": "open"}
	tag = f"Filter:{len(active)}"

	# Top level: unchanged, and the baseline for the rest.
	view = console(world, work_filter=active)
	assert tag in header(view), header(view)

	# Direct Work detail.
	view = console(world, work_filter=active)
	view.handle(curses.KEY_ENTER)
	row = header(view)
	assert row.startswith("Jobs > "), row
	assert tag in row, f"the drilled header dropped the filter tag: {row!r}"
	assert row.rstrip().endswith("lang.ada"), row
	for label in ("[Jobs ", "[Teams]", "[Inbox"):
		assert label not in row, row

	# A re-rooted table keeps BOTH the header tag and the separately
	# ruled normalized-clause line.
	view = console(world, work_filter=active)
	select(view, "the root")
	view.handle(ord("u"))
	row = header(view)
	assert tag in row and row.rstrip().endswith("lang.ada"), row
	drawn = painted(view).lines()
	assert any(line.startswith("filter: ") for line in drawn), drawn[:6]

	# Search results, the case the review called out by name.
	view = console(world, work_filter=active)
	view.handle(ord("/"))
	for char in "root":
		view.handle(ord(char))
	view.handle(10)
	assert view.mode == "search"
	row = header(view)
	assert row.startswith("Jobs > search: root"), row
	assert tag in row, f"a filtered search hid its filter: {row!r}"
	assert row.rstrip().endswith("lang.ada"), row


def test_the_drilled_filter_tag_and_identity_survive_a_narrow_header(world):
	"""Both right-edge units are reserved where the trail's room is
	decided, so neither can be half-erased by the other."""
	active = {"status": "open", "priority": "high"}
	tag = f"Filter:{len(active)}"
	view = console(world, work_filter=active)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	for width in (100, 72, 56, 44):
		row = header(view, width=width)
		assert row.rstrip().endswith("lang.ada"), (width, row)
		assert tag in row, (width, row)
		# The trail is shortened around them rather than overrunning
		# them, and a shortened trail says so.
		location = row[:row.index(tag)].rstrip()
		assert location, (width, row)
		if not location.startswith("Jobs > "):
			assert location.startswith("…"), (width, row)
		for label in ("[Jobs ", "[Teams]", "[Inbox"):
			assert label not in row, (width, row)


def test_no_filter_means_no_tag_on_a_drilled_header(world):
	"""The disclosure is a fact about the filter, not decoration."""
	view = console(world)
	view.handle(curses.KEY_ENTER)
	row = header(view)
	assert "Filter:" not in row, row
	assert row.startswith("Jobs > ") and row.rstrip().endswith("lang.ada")


# -- narrow and resized ---------------------------------------------------

def test_a_narrow_header_keeps_where_you_are_and_who_you_are(world):
	view = console(world)
	view._enter_detail(world["grand"]["work_id"], came_from="table")
	for width in (100, 60, 44, 32):
		row = header(view, width=width)
		assert row.rstrip().endswith("lang.ada"), (width, row)
		if width < 60:
			# W26331 uses exact compact selectors when they let the whole
			# path fit; an ellipsis appears only when a side is omitted.
			assert "W4" in row and "grand tit" not in row, (width, row)
		else:
			assert "the grandchild" in row, (width, row)
		for label in ("[Jobs ", "[Teams]", "[Inbox"):
			assert label not in row, (width, row)
	# The local tab row survives every one of those widths, and the
	# active tab is still exactly one.
	for width in (100, 60, 44, 32):
		drawn = painted(view, width=width).lines()
		assert any("[Messages]" in line for line in drawn), (width, drawn[:6])


def test_resizing_does_not_move_the_operator(world):
	view = console(world)
	view._enter_detail(world["child"]["work_id"], came_from="table")
	view.handle(ord("]"))
	before = (view.nav_segments(), view.detail_tab, view.detail_work)
	for width in (100, 40, 120, 52):
		header(view, width=width)
	assert (view.nav_segments(), view.detail_tab, view.detail_work) == before


# -- a real terminal ------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_walks_in_and_out_one_segment_at_a_time(world):
	"""Bare Esc and the decoded Left key are the same Back, and the whole
	walk is read-only."""
	before = world["store"].last_seq()
	# W6814: activation re-roots a Job that has children, so the second
	# segment is opening `the child` from inside `the root` — one
	# explicit action, one segment, one Back.
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.5),                # 0: the top level
		(b"u", 0.5),               # 1: re-root — a drilled page
		(b"j\r", 0.6),             # 2: open the child — another segment
		(b"]", 0.5),               # 3: local tab move, same location
		(b"\x1b", 0.5),            # 4: one segment out
		(b"\x1b[D", 0.5),          # 5: decoded Left, one more
		(b"qy", 0.4),
	])
	top, rooted, deeper, messages, out_one, out_two = (
		ptyharness.replay(step) for step in steps[:6])
	assert top[0].startswith("[Jobs 3]  [Teams]  [Inbox"), top[0]
	for screen in (rooted, deeper, messages, out_one):
		for label in ("[Jobs 3]  [Teams]", "[Teams]", "[Inbox"):
			assert label not in screen[0], screen[0]
		assert screen[0].startswith("Jobs > "), screen[0]
		assert screen[0].rstrip().endswith("lang.ada"), screen[0]
	assert deeper[0] == messages[0], \
		"the local tab move changed the location row"
	assert any("[Messages]  [Events]" in line for line in messages), \
		messages[:12]
	assert out_two[0].startswith("[Jobs 3]  [Teams]  [Inbox"), out_two[0]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-600:]
	assert world["store"].last_seq() == before, \
		"the navigation walk wrote to the authority"
