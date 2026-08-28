"""W6814 — the operator-facing half: elision lines, activation, tabs, history.

`work/records/2026/08/finding-tui-active-descendant-trail/`.

THE DEFECT. The Jobs window is three containment levels. Work claimed below
that window was invisible, so a roll-up with no Handler looked idle while
somebody was executing underneath it. `tree.active_trails` (the projection
half, covered by `test_w6814_active_trails`) reports every such claim with the
returned ancestor it belongs under. These cases are about what the console
then DOES with it, and about the two navigation rulings the same finding
made:

- a non-selectable `⋮` (`...` where the encoding cannot carry it) stands for
  the omitted levels, and the exact active Work is a real, selectable row
  beneath it;
- Enter ACTIVATES the selected Job — a Job with children becomes the
  contextual root, one without opens its detail — superseding W71's single
  meaning;
- the contextual Work page carries `[Jobs] [Messages] [Events]` scoped to its
  ROOT Work, and Back is browser history: one explicit navigation, one Esc,
  bounded at 64 with the original caller never evicted.
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
from baton_work.tui import app                                # noqa: E402
from baton_work.tui.app import Console, elision_mark, tree_stream  # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


TEAM = "lang"
ENTER, ESC = curses.KEY_ENTER, 27


class Screen:
	"""The same virtual screen the other console suites use: paint calls
	recorded, then composed in paint order so the last write at a column
	wins exactly as a terminal resolves it."""

	def __init__(self, height=24, width=110):
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

	def rows(self):
		return [self.row(y) for y in range(self._size[0])]

	def row(self, y):
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
	"""Two eligible handlers of one route, so claims can be concurrent.

	A participant holds ONE active claim at a time, so a case about
	handlers working at the same time needs two of them — which is what
	`build_crew` configures and what the default one-handler spec cannot
	express."""
	config, database = fx.build_crew(str(tmp_path), TEAM, ["ada", "bee"],
	                                 kinds=("bug",))
	store = bw.Authority(database)
	yield {"config": config, "store": store, "database": database}
	store.close()


def make(world, title, parent=None):
	return tr.create_work(
		world["store"], team=TEAM, kind="bug", title=title,
		origin="external-report" if parent is None else "decomposition",
		classification="confirmed-defect", author="ada",
		body=f"{title} opener", parent=parent)["work_id"]


def chain(world, depth, prefix="level"):
	"""One containment chain `depth` levels deep, root-first."""
	made, parent = [], None
	for level in range(depth):
		parent = make(world, f"{prefix}-{level}", parent)
		made.append(parent)
	return made


def claim(world, work_id, member="ada"):
	return tr.claim_work(world["store"], work_id, actor_team=TEAM,
	                     actor=member)


def console(world, member="ada", work_filter=None):
	return Console(world["store"], TEAM, member,
	               config_path=world["config"], work_filter=work_filter)


def painted(view, height=24, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen


def body(view, height=24, width=110):
	"""The painted rows with the blank tail removed — header row, table
	header, rows, footer."""
	return [line for line in painted(view, height, width).rows() if line]


def local(work_id):
	return work_id.rsplit("-", 1)[-1]


def row_of(view, work_id, height=24, width=110):
	"""The one painted line whose Id column is this Work's local id."""
	tag = local(work_id)
	return next((line for line in body(view, height, width)
	             if line.split(" ")[0] == tag), None)


def marker_lines(view, height=24, width=110):
	mark = view.elision_mark()
	return [line for line in body(view, height, width)
	        if line.strip() == mark]


# -- the elision and the exact active Work -----------------------------------

class TestTheWindowShowsWhatItHides:

	def test_a_hidden_claim_paints_an_elision_and_its_exact_work(self, world):
		"""The reported shape, end to end: three visible levels, one
		omitted-levels marker, and the claimed Work with its own
		identity, title and Handler."""
		levels = chain(world, 4)
		deep = levels[3]
		claim(world, deep)
		view = console(world)
		lines = body(view)
		assert row_of(view, levels[2]) is not None, lines
		assert len(marker_lines(view)) == 1, lines
		trail_row = row_of(view, deep)
		assert trail_row is not None, \
			f"the hidden claim never reached the screen: {lines}"
		assert "level-3" in trail_row and "lang.ada" in trail_row, trail_row
		# ORDER: ancestor, then the marker, then the Work it stands for.
		order = [lines.index(row_of(view, levels[2])),
		         lines.index(marker_lines(view)[0]),
		         lines.index(trail_row)]
		assert order == sorted(order), (order, lines)

	def test_the_elision_is_not_a_work_row(self, world):
		"""It carries no Id, no columns, and nothing the operator can aim
		at. A marker with a cursor on it is a Work as far as their hands
		are concerned, and Enter on one would have to mean nothing."""
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		mark = marker_lines(view)[0]
		assert mark.strip() == view.elision_mark()
		# Nothing but indent before the marker: the Id column is empty.
		assert mark.lstrip() == view.elision_mark()
		rows, _hidden = view.table_rows()
		assert all("id" in row for row in rows), \
			"a display line reached the selectable set"
		assert len(rows) == 4, [row["local_id"] for row in rows]

	def test_the_ancestor_never_borrows_the_descendants_handler(self, world):
		"""The authority is right and stays right: a parent's Handler and
		Phase are the parent's. The trail adds a row; it does not restate
		a descendant's facts on the row above."""
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		for ancestor in levels[:3]:
			line = row_of(view, ancestor)
			assert "lang.ada" not in line, \
				f"an ancestor borrowed the descendant's Handler: {line}"
		assert "lang.ada" in row_of(view, levels[3])

	def test_an_ordinarily_visible_claim_is_not_drawn_twice(self, world):
		levels = chain(world, 3)
		claim(world, levels[2])
		view = console(world)
		assert marker_lines(view) == []
		rows, _hidden = view.table_rows()
		assert [row["id"] for row in rows] == levels

	def test_several_claims_under_one_anchor_share_one_elision(self, world):
		"""Every concurrent claim is its own row — a count would recreate
		the debugging problem the feature removes — and one marker serves
		the group, because repeating it would spend a line per worker
		saying the same thing."""
		levels = chain(world, 3)
		first = make(world, "deep-a", levels[2])
		second = make(world, "deep-b", levels[2])
		claim(world, first, "ada")
		claim(world, second, "bee")
		view = console(world)
		assert len(marker_lines(view)) == 1, body(view)
		rows, _hidden = view.table_rows()
		assert [row["id"] for row in rows] == levels + [first, second], \
			"concurrent claims are not in containment order"

	def test_claims_under_different_anchors_stay_under_their_own(self, world):
		root = make(world, "root")
		left = make(world, "left", root)
		right = make(world, "right", root)
		under_left = make(world, "l-child", left)
		under_right = make(world, "r-child", right)
		deep_left = make(world, "l-deep", under_left)
		deep_right = make(world, "r-deep", under_right)
		claim(world, deep_left, "ada")
		claim(world, deep_right, "bee")
		view = console(world)
		lines = body(view)
		assert len(marker_lines(view)) == 2, lines
		positions = [lines.index(row_of(view, work)) for work in
		             (under_left, deep_left, under_right, deep_right)]
		assert positions == sorted(positions), (positions, lines)

	def test_the_trail_row_carries_the_claim_facts_of_its_own_row(self, world):
		"""Parity with the canonical row: the trail IS the active Work's
		row, not a reduced one whose Handler survived while its claim
		facts vanished."""
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		rows, _hidden = view.table_rows()
		trail = next(row for row in rows if row["id"] == levels[3])
		canonical = pj.detail(world["store"], levels[3], viewer_team=TEAM,
		                      viewer_member="ada")
		assert trail["handler"] == canonical["handler"]
		assert trail["claimed_at"] == canonical["claimed_at"]
		assert trail["phase"] == canonical["phase"] == "active"

	def test_a_run_state_reaches_the_trail_row(self, world):
		"""What the HANDLER's runner is doing, on the row that names the
		handler — never inferred from Phase, and never on the ancestor."""
		levels = chain(world, 4)
		claim(world, levels[3])
		tr.runtime_start(world["store"], actor_team=TEAM, actor="ada",
		                 incarnation="run-1", adapter="acp")
		tr.runtime_state(world["store"], actor_team=TEAM, actor="ada",
		                 incarnation="run-1", state="working")
		view = console(world)
		rows, _hidden = view.table_rows()
		trail = next(row for row in rows if row["id"] == levels[3])
		assert trail["agent"]["state"] == "working"
		assert view._row_cells(trail)["RUN"] == app.agent_cell(trail["agent"])
		# And it reaches the paint, on the row that names the handler.
		assert "work" in row_of(view, levels[3])
		assert "work" not in row_of(view, levels[2])


# -- the marker's two spellings ----------------------------------------------

class TestTheMarkerFallback:

	def test_the_unicode_marker_is_used_where_it_encodes(self):
		assert elision_mark("utf-8") == "⋮"

	def test_ascii_falls_back_rather_than_failing(self):
		assert elision_mark("ascii") == "..."
		assert elision_mark("latin-1") == "..."

	def test_an_unknown_encoding_falls_back_too(self):
		"""A locale nobody can look up is not a reason to raise on the
		render path."""
		assert elision_mark("not-a-real-encoding") == "..."

	def test_the_console_paints_whichever_its_terminal_can_encode(self, world):
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		view.encoding = "ascii"
		assert marker_lines(view) and marker_lines(view)[0].strip() == "..."
		view.encoding = "utf-8"
		assert marker_lines(view) and marker_lines(view)[0].strip() == "⋮"


# -- structure survives width, length, filters and scrolling -----------------

class TestTheStructureSurvives:

	def test_a_long_title_never_deletes_the_marker(self, world):
		levels = chain(world, 3)
		deep = make(world, "d" * 80, levels[2])   # the title cap
		claim(world, deep)
		view = console(world)
		for width in (110, 90, 76):
			marks = [line for line in body(view, width=width)
			         if line.strip() == view.elision_mark()]
			assert marks, f"the marker was truncated away at {width}"

	def test_a_narrow_terminal_keeps_the_group_or_refuses_whole(self, world):
		"""The table's existing too-narrow REFUSAL is the one honest
		answer at widths that cannot hold identities. What must never
		happen is a screen that keeps the trail row and drops the marker
		that explains it."""
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		for width in range(40, 112, 4):
			lines = body(view, width=width)
			if any("terminal too narrow" in line for line in lines):
				continue
			assert any(line.strip() == view.elision_mark()
			           for line in lines), (width, lines)
			assert row_of(view, levels[3], width=width), (width, lines)

	def test_a_resize_in_both_directions_keeps_the_shape(self, world):
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		shapes = []
		for width in (110, 80, 110):
			lines = body(view, width=width)
			shapes.append((len([line for line in lines
			                    if line.strip() == view.elision_mark()]),
			               bool(row_of(view, levels[3], width=width))))
		assert shapes == [(1, True)] * 3, shapes

	def test_a_handler_filter_paints_the_claim_the_window_hides(self, world):
		"""The counterexample from the revalidation. `handler=` used to
		leave the screen EMPTY while that handler was holding something
		below the window; the bounded ancestors are retained as context
		and the claim is painted under them."""
		levels = chain(world, 4)
		claim(world, levels[3], "bee")
		view = console(world, work_filter={"handler": "lang.bee"})
		lines = body(view)
		assert row_of(view, levels[3]) is not None, lines
		assert marker_lines(view), lines
		for ancestor in levels[:3]:
			assert row_of(view, ancestor) is not None, (ancestor, lines)

	def test_the_selected_trail_row_is_never_scrolled_off(self, world):
		"""The elision spends a PHYSICAL line, and the viewport still
		anchors on the selected Work id — so a group cannot quietly push
		the row the operator is aiming at off the drawn slice."""
		levels = chain(world, 3)
		for index in range(6):
			make(world, f"sibling-{index}", levels[1])
		deep = make(world, "the deep claim", levels[2])
		claim(world, deep)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == deep)
		view.selected_id = deep
		for height in (10, 12, 24):
			assert row_of(view, deep, height=height) is not None, \
				f"the selected trail row was scrolled off at {height}"

	def test_revealing_closed_rows_leaves_the_group_where_it_was(self, world):
		"""`z` changes which ordinary rows are drawn. The group still
		hangs from its own ancestor, and the closed row it now sits
		beside is not mistaken for one."""
		levels = chain(world, 3)
		done = make(world, "already finished", levels[1])
		tr.close_work(world["store"], done, actor_team=TEAM, actor="ada",
		              outcome="satisfying", rationale="done")
		deep = make(world, "the live one", levels[2])
		claim(world, deep)
		view = console(world)
		assert row_of(view, done) is None, "the closed row was not collapsed"
		before = body(view).index(marker_lines(view)[0]) \
			- body(view).index(row_of(view, levels[2]))
		view.handle(ord("z"))
		assert row_of(view, done) is not None, "`z` revealed nothing"
		assert len(marker_lines(view)) == 1, body(view)
		after = body(view).index(marker_lines(view)[0]) \
			- body(view).index(row_of(view, levels[2]))
		assert after == before, \
			"the group moved away from the ancestor it belongs to"
		assert row_of(view, deep) is not None

	def test_a_closed_ancestor_cannot_hide_a_live_claim(self, world):
		"""Containment forbids the shape — a parent cannot close while an
		open child remains — so a collapsed closed row can hold no active
		descendant. The stream never DROPS a trail to keep that
		assumption tidy: an unanchored group still flushes."""
		orphan = {"anchor": "no-such-work", "hidden_depth": 2,
		          "work": {"id": "x-W99", "local_id": "W99", "depth": 0}}
		stream = tree_stream([], [orphan])
		assert [entry["kind"] for entry in stream] == ["elision", "work"]


# -- activation: what Enter opens --------------------------------------------

class TestActivation:

	def test_a_job_with_children_becomes_the_contextual_root(self, world):
		levels = chain(world, 4)
		view = console(world)
		view.selected_id = levels[0]
		view.cursor = 0
		view.handle(ENTER)
		assert view.mode == "table"
		assert view.path[-1] == levels[0]
		assert view.context_work() == levels[0]

	def test_a_job_with_no_children_opens_its_detail(self, world):
		levels = chain(world, 2)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == levels[1])
		view.selected_id = levels[1]
		view.handle(ENTER)
		assert view.mode == "detail" and view.detail_work == levels[1]
		assert view.detail_tab == "messages", \
			"a leaf did not default to its Messages"

	def test_activating_a_trail_row_opens_that_exact_work(self, world):
		"""The whole point of making the row selectable."""
		levels = chain(world, 4)
		deep = levels[3]
		claim(world, deep)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == deep)
		view.selected_id = deep
		view.handle(ENTER)
		assert view.mode == "detail" and view.detail_work == deep

	def test_a_claimed_non_leaf_trail_re_roots_like_any_other(self, world):
		levels = chain(world, 5)
		held = levels[3]
		claim(world, held)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == held)
		view.selected_id = held
		view.handle(ENTER)
		assert view.mode == "table" and view.path[-1] == held

	def test_j_and_k_walk_into_the_trail_rows(self, world):
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world)
		view.handle(ord("k"))                   # settle on the first row
		seen = [view.selected_id]
		for _ in range(4):
			view.handle(ord("j"))
			seen.append(view.selected_id)
		assert levels[3] in seen, seen
		assert None not in seen, "a display line became a selection"
		# Four rows, so the fifth `j` clamps on the last one.
		assert seen == levels + [levels[-1]], \
			"j skipped a row or landed on a marker"

	def test_the_explicit_unfold_still_roots_at_a_childless_job(self, world):
		"""`u` is not superseded: activation deliberately opens a
		childless Job's detail, and `u` is the way to root at one."""
		levels = chain(world, 2)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == levels[1])
		view.selected_id = levels[1]
		view.handle(ord("u"))
		assert view.mode == "table" and view.path[-1] == levels[1]

	def test_the_window_and_its_trails_recompute_at_the_new_root(self, world):
		levels = chain(world, 6)
		deep = levels[5]
		claim(world, deep)
		view = console(world)
		assert deep not in {row["id"] for row in view.view()[0]}, \
			"a claim three levels past the window was already ordinary"
		assert marker_lines(view), body(view)

		def open_row(work_id):
			rows, _hidden = view.table_rows()
			view.cursor = next(index for index, row in enumerate(rows)
			                   if row["id"] == work_id)
			view.selected_id = work_id
			view.handle(ENTER)

		open_row(levels[2])
		assert marker_lines(view), \
			"the claim is still below the re-rooted window and lost its marker"
		open_row(levels[3])
		assert deep in {row["id"] for row in view.view()[0]}, \
			"the window did not recompute against the new root"
		assert marker_lines(view) == [], \
			"an ordinarily visible claim kept an elision above it"


# -- the contextual page's tabs ----------------------------------------------

class TestRootScopedTabs:

	def test_the_page_carries_three_tabs_scoped_to_its_root(self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		labels = [label for _name, label in view.detail_tab_segments()]
		assert labels == ["[Jobs]", "[Messages]", "[Events]"]
		assert view.context_tab() == "jobs", \
			"a Job with children did not open on Jobs"
		screen = painted(view)
		assert screen.attr_of("[Jobs]") != screen.attr_of("[Messages]")

	def test_moving_the_highlight_never_moves_which_work_owns_messages(
			self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		view.handle(ord("j"))                   # highlight the child
		assert view.selected_id == levels[1]
		view.handle(ord("]"))                   # Messages
		assert view.detail_work == levels[0], \
			"the highlighted descendant hijacked the page's Messages"

	def test_a_tab_round_trip_restores_the_row_it_left(self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		view.handle(ord("j"))
		chosen = view.selected_id
		view.handle(ord("]"))                   # Messages
		view.handle(ord("["))                   # back to Jobs
		assert view.context_tab() == "jobs"
		assert view.selected_id == chosen, \
			"the tab round trip reset the row the operator left"

	def test_a_tab_move_records_no_history(self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		depth = len(view.nav)
		for _ in range(6):
			view.handle(ord("]"))
		assert len(view.nav) == depth, \
			"local tab moves grew the Back stack"
		assert view.nav_segments() == ["Jobs", "level-0"]

	def test_a_filter_does_not_overwrite_the_contextual_tab_row(self, world):
		"""Filter disclosure and the root-local tabs are two required rows.

		The filter remains active after re-rooting, so sharing row 1 makes its
		clause text paint over `[Jobs] [Messages] [Events]` and leaves the
		contextual page with no usable local-tab disclosure.
		"""
		levels = chain(world, 3)
		view = console(world, work_filter={"status": "open"})
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		lines = painted(view).rows()
		assert any("[Jobs]  [Messages]  [Events]" in line for line in lines), \
			lines[:6]
		assert any(line.startswith("filter: status=open") for line in lines), \
			lines[:6]

	def test_the_rows_above_the_table_keep_a_stable_order(self, world):
		"""Both disclosures are required and neither is optional to the
		other, so they are allocated from one running cursor rather than
		written at literal rows. The order is breadcrumb, tabs, filter,
		then the table's own header — and the header is what proves the
		table starts BELOW both rather than under one of them."""
		levels = chain(world, 3)
		view = console(world, work_filter={"status": "open"})
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		screen = painted(view)
		rows = screen.rows()
		tabs = next(index for index, line in enumerate(rows)
		            if "[Jobs]  [Messages]  [Events]" in line)
		clauses = next(index for index, line in enumerate(rows)
		               if line.startswith("filter: status=open"))
		header = next(index for index, line in enumerate(rows)
		              if line.startswith("Id Title"))
		assert screen.row(0).startswith("Jobs > "), screen.row(0)
		assert 0 < tabs < clauses < header, (tabs, clauses, header)
		# And nothing was overpainted: the tab row is the WHOLE row.
		assert "filter:" not in rows[tabs], rows[tabs]
		assert "[" not in rows[clauses], rows[clauses]

	def test_neither_row_costs_the_table_its_rows(self, world):
		"""The viewport budget beneath them is unchanged: every Work the
		window holds is still painted, and so is its elision group."""
		levels = chain(world, 4)
		claim(world, levels[3])
		view = console(world, work_filter={"status": "open"})
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		for work in levels[:3] + [levels[3]]:
			assert row_of(view, work) is not None, body(view)
		assert marker_lines(view), body(view)

	def test_a_narrow_terminal_still_viewports_the_clause_line(self, world):
		"""W5's rule survives the extra row: the clause line is
		horizontally viewported and marked, never silently dropped."""
		levels = chain(world, 3)
		view = console(world, work_filter={"status": "open",
		                                   "priority": "normal",
		                                   "phase": "queued"})
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		for width in (110, 60, 30):
			rows = painted(view, width=width).rows()
			clauses = [line for line in rows
			           if line.startswith("filter: ")]
			assert clauses, (width, rows[:6])
			assert len(clauses[0]) <= width - 1, (width, clauses[0])
			assert any("[Jobs]" in line for line in rows), (width, rows[:6])


# -- Back history ------------------------------------------------------------

class TestBoundedHistory:

	def test_one_enter_is_one_back_however_deep_the_row(self, world):
		levels = chain(world, 3)
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == levels[2])
		view.selected_id = levels[2]
		view.handle(ENTER)
		assert len(view.nav) == 1
		# The TRAIL still names every level; only the history is one.
		assert view.nav_segments() == ["Jobs", "level-0", "level-1",
		                               "level-2"]
		view.handle(ESC)
		assert view.nav == [] and view.mode == "table"

	def test_explicit_intermediate_entries_are_their_own_back_steps(
			self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == levels[1])
		view.selected_id = levels[1]
		view.handle(ENTER)
		assert len(view.nav) == 2
		view.handle(ESC)
		assert view.path[-1] == levels[0]
		view.handle(ESC)
		assert view.nav == [] and view.path == []

	def test_the_page_you_are_already_on_is_not_recorded(self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		assert len(view.nav) == 1
		for _ in range(5):
			view.handle(ENTER)              # the root row IS the root
			view.handle(ord("u"))
		assert len(view.nav) == 1, \
			"re-opening the current page grew the history"

	def test_history_is_bounded_and_never_evicts_the_way_out(self, world):
		"""Past the bound the OLDEST ordinary entry goes. The original
		caller is kept beside the stack, so a long walk is still one Esc
		from the view it started in."""
		root = make(world, "the caller root")
		leaves = [make(world, f"leaf-{index}", root)
		          for index in range(app.NAV_HISTORY_LIMIT + 12)]
		view = console(world)
		rows, _hidden = view.table_rows()
		view.cursor = next(index for index, row in enumerate(rows)
		                   if row["id"] == root)
		view.selected_id = root
		opened_at = (view.mode, view.cursor, view.selected_id, list(view.path))
		for leaf in leaves:
			view._enter_detail(leaf, came_from="table")
		assert len(view.nav) == app.NAV_HISTORY_LIMIT, len(view.nav)
		while view.nav:
			view.handle(ESC)
		assert (view.mode, view.cursor, view.selected_id,
		        list(view.path)) == opened_at, \
			"eviction stranded the operator inside the Work view"

	def test_a_fresh_console_starts_with_no_history(self, world):
		"""Session-local: a restart begins empty, and nothing is
		persisted anywhere for it to inherit."""
		levels = chain(world, 2)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		assert view.nav
		restarted = console(world)
		assert restarted.nav == [] and restarted.nav_caller is None
		assert restarted.nav_segments() == []

	def test_row_and_filter_moves_are_not_history(self, world):
		levels = chain(world, 3)
		view = console(world)
		view.selected_id, view.cursor = levels[0], 0
		view.handle(ENTER)
		depth = len(view.nav)
		for key in (ord("j"), ord("k"), ord("z"), ord("z")):
			view.handle(key)
		assert len(view.nav) == depth


# -- the real terminal -------------------------------------------------------

def test_the_live_shape_paints_on_a_real_terminal(world):
	"""The reported W5/W6631 shape, end to end, through curses: the
	roll-up, the marker, and the exact active Work with its Handler."""
	levels = chain(world, 4, prefix="stage")
	claim(world, levels[3], "bee")
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.6),
		(b"qy", 0.4),
	])
	screen = ptyharness.replay(steps[0])
	assert any(line.strip() == "⋮" for line in screen), screen[:10]
	deep = next((line for line in screen
	             if line.split(" ")[0] == local(levels[3])), None)
	assert deep is not None, screen[:10]
	assert "stage-3" in deep and "lang.bee" in deep, deep
	ancestor = next(line for line in screen
	                if line.split(" ")[0] == local(levels[2]))
	assert "lang.bee" not in ancestor, ancestor
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]


def test_a_real_terminal_activates_the_hidden_claim_and_comes_back(world):
	"""Selecting down into the trail row and pressing Enter opens THAT
	Work, and one Esc returns to the table it was opened from."""
	levels = chain(world, 4, prefix="stage")
	claim(world, levels[3], "bee")
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"jjj", 0.6),                # onto the trail row
		(b"\r", 0.6),                 # it has no children: its detail
		(b"\x1b", 0.5),               # one action in, one Esc out
		(b"qy", 0.4),
	])
	opened = ptyharness.replay(steps[1])
	assert opened[0].startswith("Jobs > "), opened[0]
	assert "stage-3" in opened[0], opened[0]
	assert any("Threads (" in line for line in opened), opened[:12]
	back = ptyharness.replay(steps[2])
	assert back[0].startswith("[Jobs ") and "[Teams]" in back[0], back[0]
	assert any(line.strip() == "⋮" for line in back), back[:10]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]


def test_a_real_terminal_shows_the_root_scoped_tabs(world):
	"""Activation on a Job with children roots the tree at it and paints
	its three local tabs; `]` reaches that same Work's Messages."""
	levels = chain(world, 3, prefix="stage")
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		(b"]", 0.5),
		(b"qy", 0.4),
	])
	rooted = ptyharness.replay(steps[0])
	assert rooted[0].startswith("Jobs > stage-0"), rooted[0]
	assert any("[Jobs]  [Messages]  [Events]" in line for line in rooted), \
		rooted[:6]
	messages = ptyharness.replay(steps[1])
	assert messages[0] == rooted[0], "the tab move changed the location row"
	assert any("stage-0 opener" in line for line in messages), messages[:16]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]


def test_a_real_terminal_resize_keeps_the_marker(world):
	"""R4 geometry: the group survives a live SIGWINCH in both
	directions."""
	levels = chain(world, 4, prefix="stage")
	claim(world, levels[3], "bee")
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"", 0.6), ("resize", (84, 24), 0.9), (b"", 0.6),
		 ("resize", (110, 32), 0.9), (b"", 0.6), (b"qy", 0.4)],
		dynamic_size=True, columns=110, lines=32)
	for step in (steps[0], steps[2], steps[4]):
		screen = ptyharness.replay(step, columns=110, lines=32)
		assert any(line.strip() == "⋮" for line in screen), screen[:12]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
