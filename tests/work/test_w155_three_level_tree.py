"""W155: the Work window shows three containment levels.

Two levels hid a common shape. A root's child sat waiting with no
Handler while ITS child was open and claimed, and nothing on screen gave
the operator a reason to re-root — the interesting Work was one
navigation step away with no sign that it existed.

The window now spans root, child and grandchild. Containment semantics
are untouched: one parent, and indentation means containment and nothing
else. A dependency is a graph edge and keeps its separate `Wait` cue.

The fourth level and below never paint, and the deepest visible row says
so with a `▸` icon in the same reserved structural space W154
established — so no title length, width, selection or filter can delete
it.
"""

from __future__ import annotations

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
from baton_work.tui.app import Console, _title_cell           # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)

	def make(title, parent=None, origin="decomposition"):
		return tr.create_work(store, team="lang", kind="bug", title=title,
		                      origin=origin,
		                      classification="suspected-defect",
		                      author="ada", body="b",
		                      parent=parent)["work_id"]

	yield {"store": store, "config": config_path, "make": make}
	store.close()


def _rows(world, root=None, viewer="ada", work_filter=None):
	return pj.tree(world["store"], root, viewer_team="lang",
	               viewer_member=viewer, work_filter=work_filter)["rows"]


def _by_id(world, **kwargs):
	return {row["id"]: row for row in _rows(world, **kwargs)}


def _chain(world, depth):
	"""A single containment chain `depth` levels deep, root first."""
	ids, parent = [], None
	for level in range(depth):
		parent = world["make"](f"level {level}", parent=parent,
		                       origin="external-report" if level == 0
		                       else "decomposition")
		ids.append(parent)
	return ids


# -- the window --------------------------------------------------------------

def test_a_three_level_chain_paints_whole(world):
	root, child, grand = _chain(world, 3)
	rows = _rows(world)
	assert [row["id"] for row in rows] == [root, child, grand]
	assert [row["depth"] for row in rows] == [0, 1, 2]
	assert not any(row["deeper"] for row in rows), \
		"a fully visible chain claims to hide something"


def test_the_fourth_level_never_paints_and_is_disclosed(world):
	"""'Fourth-level-or-deeper containment never paints in the current
	window; its visible ancestor carries the unclippable ▸ icon.'"""
	root, child, grand, great = _chain(world, 4)
	rows = _by_id(world)
	assert great not in rows, "the fourth level painted"
	assert set(rows) == {root, child, grand}
	assert rows[grand]["deeper"] is True
	assert rows[child]["deeper"] is False and rows[root]["deeper"] is False
	assert "▸" in _title_cell(rows[grand], 40)
	assert "▸" not in _title_cell(rows[child], 40)


def test_a_deeper_chain_still_stops_at_three(world):
	"""Six levels deep is the same answer as four: the cap is the cap."""
	ids = _chain(world, 6)
	rows = _rows(world)
	assert [row["id"] for row in rows] == ids[:3]
	assert rows[-1]["deeper"] is True


def test_a_leaf_root_paints_alone_and_discloses_nothing(world):
	only = world["make"]("alone", origin="external-report")
	rows = _rows(world)
	assert [row["id"] for row in rows] == [only]
	assert rows[0]["deeper"] is False
	assert "↳" not in _title_cell(rows[0], 40)
	assert "▸" not in _title_cell(rows[0], 40)


def test_siblings_order_identically_at_every_level(world):
	"""W3's priority-then-creation order applies within each sibling
	group WITHOUT a group leaving its parent."""
	root = world["make"]("root", origin="external-report")
	first = world["make"]("child one", parent=root)
	second = world["make"]("child two", parent=root)
	deep_a = world["make"]("grand a", parent=first)
	deep_b = world["make"]("grand b", parent=first)
	tr.prioritize(world["store"], second, actor_team="lang", actor="ada",
	              priority="high")
	tr.prioritize(world["store"], deep_b, actor_team="lang", actor="ada",
	              priority="high")
	order = [row["id"] for row in _rows(world)]
	# the high-priority sibling leads its own group, and the group under
	# `first` stays under `first`
	assert order == [root, second, first, deep_b, deep_a], order


def test_containment_is_the_only_thing_depth_means(world):
	"""A dependency edge must not masquerade as containment: the blocker
	keeps its own place in the tree and the consumer's depth is
	untouched."""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	blocker = world["make"]("an unrelated blocker", origin="external-report")
	tr.add_dependency(world["store"], child, blocker, actor_team="lang",
	                  actor="ada", rationale="needs it")
	rows = _by_id(world)
	assert rows[child]["depth"] == 1, "a dependency changed containment depth"
	assert rows[blocker]["depth"] == 0, "a blocker was adopted as a child"
	# the dependency shows through the Wait cue, not through indentation
	from baton_work.tui.app import blocker_cue
	assert blocker_cue(rows[child]) == blocker.rsplit("-", 1)[1]
	assert "↳" not in _title_cell(rows[blocker], 40)


# -- the disclosure is a window fact, not a depth number --------------------

def test_a_filter_that_hides_children_still_discloses_them(world):
	"""W154's ruling names filters explicitly: they must never silently
	remove the fact that a visible Work has hidden children. Defining
	the cue against the window ACTUALLY RETURNED gets this for free."""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	tr.classify(world["store"], child, actor_team="lang", actor="ada",
	            classification="design-choice")
	rows = _by_id(world, work_filter={"category": "suspected-defect"})
	assert child not in rows, "the fixture's filter did not hide the child"
	assert rows[root]["deeper"] is True, \
		"a filtered-away child stopped being disclosed"
	assert "▸" in _title_cell(rows[root], 40)


def test_a_matching_descendant_keeps_its_whole_ancestry(world):
	"""The W5 containment rule over three levels: a match keeps its
	ancestors as structural context, at their own depths, unpromoted."""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	grand = world["make"]("the needle", parent=child)
	tr.classify(world["store"], grand, actor_team="lang", actor="ada",
	            classification="design-choice")
	rows = _rows(world, work_filter={"category": "design-choice"})
	assert [row["id"] for row in rows] == [root, child, grand]
	assert [row["depth"] for row in rows] == [0, 1, 2], \
		"filtering promoted a row or changed its depth"
	assert [row["filter_match"] for row in rows] == [False, False, True]


def test_a_group_with_no_match_disappears_whole(world):
	keep = world["make"]("keeper", origin="external-report")
	world["make"]("the needle", parent=keep)
	other = world["make"]("nothing here", origin="external-report")
	world["make"]("nor here", parent=other)
	tr.classify(world["store"], keep, actor_team="lang", actor="ada",
	            classification="design-choice")
	rows = _rows(world, work_filter={"category": "design-choice"})
	assert [row["id"] for row in rows] == [keep]


# -- re-rooting --------------------------------------------------------------

def test_re_rooting_reveals_the_next_three_levels(world):
	"""'Re-rooting that row reveals the next three-level window.'"""
	ids = _chain(world, 6)
	rows = _rows(world, root=ids[2])
	assert [row["id"] for row in rows] == ids[2:5]
	assert [row["depth"] for row in rows] == [0, 1, 2]
	assert rows[-1]["deeper"] is True, \
		"the re-rooted window does not disclose what is below it"
	# and re-rooting the deepest of those reaches the rest
	last = _rows(world, root=ids[4])
	assert [row["id"] for row in last] == ids[4:6]
	assert last[-1]["deeper"] is False


def test_a_re_rooted_leaf_is_a_window_of_one(world):
	ids = _chain(world, 3)
	rows = _rows(world, root=ids[2])
	assert [row["id"] for row in rows] == [ids[2]]
	assert rows[0]["deeper"] is False


# -- one batched read --------------------------------------------------------

def test_the_window_reads_do_not_grow_with_the_tree(world):
	"""W39 R1: growing the visible tree must not grow the number of
	reads. The three-level window is bigger, so this is the moment that
	rule would quietly break.

	`_row_view` legitimately costs a fixed number of reads PER ROW, and
	that total grows with any tree — measuring it would prove nothing.
	What this measures is the WINDOW's own reads: one ordered statement
	per LEVEL plus the batched `deeper` lookup, bounded by the depth cap
	and nothing else.

	This test previously asserted `small + 1` after adding a second
	depth-1 row — blessing exactly the per-parent growth its name
	forbids. A test that accepts the defect it is named for is worse
	than no test, so it now pins the constant."""
	store = world["store"]

	class Counting:
		"""`sqlite3.Connection.execute` is read-only, so the count is
		taken around the connection rather than on it."""

		def __init__(self, real):
			self._real = real
			self.window = 0

		def execute(self, sql, *args, **kwargs):
			# the window's own statements, matched precisely: the
			# per-level sibling query (ordered, so it is not the per-row
			# child COUNT that `_row_view` legitimately makes) and the
			# batched `deeper` lookup.
			level = "WHERE parent IN" in sql and "ORDER BY CASE priority" in sql
			roots = "parent IS NULL" in sql and "ORDER BY CASE priority" in sql
			if level or roots or "SELECT DISTINCT parent" in sql:
				self.window += 1
			return self._real.execute(sql, *args, **kwargs)

		def __getattr__(self, name):
			return getattr(self._real, name)

	def window_reads():
		real = store.conn
		proxy = Counting(real)
		store.conn = proxy
		try:
			_rows(world)
		finally:
			store.conn = real
		return proxy.window

	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	world["make"]("grand", parent=child)
	# the roots query, one statement per level below it, and `deeper`
	baseline = window_reads()
	assert baseline == 4, baseline

	# now grow the tree in every direction it can grow
	for index in range(6):
		world["make"](f"another root {index}", origin="external-report")
	assert window_reads() == baseline, "more roots cost more window reads"
	for index in range(6):
		world["make"](f"another child {index}", parent=root)
	assert window_reads() == baseline, "more children cost more window reads"
	for index in range(6):
		world["make"](f"another grand {index}", parent=child)
	assert window_reads() == baseline, \
		"more grandchildren cost more window reads"


# -- the drawn table ---------------------------------------------------------

class Screen:
	def __init__(self):
		self.rows = {}

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]

	def lines(self):
		return [self.rows[key] for key in sorted(self.rows)]


def _levels(painted):
	"""The Work rows among painted lines, found by the Id column.

	Deliberately not by title text: the title is the one column that
	truncates, so matching on it would make a test about level COUNT
	fail for a reason about width.
	"""
	import re
	return [line for line in painted
	        if re.match(r"^W\d+ ", line)]


def _painted(world, width=110, height=24, root=None, work_filter=None):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"], work_filter=work_filter)
	screen = Screen()
	console._render_table(screen, height, width,
	                      _rows(world, root=root, work_filter=work_filter))
	return screen.lines()


def test_the_three_levels_are_unambiguously_indented(world):
	_chain(world, 4)
	painted = _levels(_painted(world))
	assert len(painted) == 3, painted
	root, child, grand = painted
	# each level's marker starts two cells deeper than the one above
	assert "↳" not in root
	assert child.index("↳") + 2 == grand.index("↳"), \
		f"the indents are not fixed per level: {painted}"


@pytest.mark.parametrize("width", [110, 92, 80, 72, 64, 56, 48, 44])
def test_every_supported_width_keeps_all_three_levels(world, width):
	_chain(world, 4)
	painted = _painted(world, width=width)
	assert len(_levels(painted)) == 3, \
		f"a level was dropped at width {width}: {painted}"
	assert any("▸" in line for line in painted), \
		f"the more-levels icon is gone at width {width}"


def test_a_long_title_at_the_third_level_keeps_its_icon(world):
	"""W154 and W155 composing: the deepest row is the one carrying the
	icon AND the one most likely to be indented into a narrow title."""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	grand = world["make"](
		"Rewrite public docs and architecture for v11 in full", parent=child)
	world["make"]("hidden", parent=grand)
	for width in (110, 80, 60, 50, 44):
		painted = _painted(world, width=width)
		row = next(line for line in painted if "▸" in line)
		assert "  ↳ ▸1 " in row, f"width {width}: {row!r}"


def test_the_closed_collapse_still_names_what_it_hides(world):
	"""Closed-row hiding is its own contract and stays coherent at the
	new cap."""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	tr.close_work(world["store"], child, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	painted = _painted(world)
	assert any("closed hidden" in line for line in painted), painted
	assert not any("child" in line for line in painted)


def test_the_deepest_visible_row_never_borrows_from_below(world):
	"""'does not aggregate hidden Handler, Phase, or message state onto
	the ancestor.'"""
	root = world["make"]("root", origin="external-report")
	child = world["make"]("child", parent=root)
	grand = world["make"]("grand", parent=child)
	hidden = world["make"]("hidden and claimed", parent=grand)
	tr.claim_work(world["store"], hidden, actor_team="lang", actor="ada")
	rows = _by_id(world)
	assert hidden not in rows
	assert rows[grand]["handler"] is None, \
		"the visible ancestor borrowed the hidden claimant"
	assert rows[grand]["deeper"] is True
	painted = _painted(world)
	row = next(line for line in painted if "▸" in line)
	assert "ada" not in row, row


# -- a real terminal ---------------------------------------------------------

@pytest.mark.serial
def test_a_real_terminal_paints_three_levels_and_re_roots(world):
	ids = _chain(world, 5)
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"", 0.6), (b"jj", 0.4), (b"u", 0.7), (b"\x1b", 0.6),
		 (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	opened = ptyharness.replay(steps[0], columns=110, lines=24)
	assert len(_levels(opened)) == 3, opened
	assert any("▸" in line for line in opened), "no more-levels icon"
	rooted = ptyharness.replay(steps[2], columns=110, lines=24)
	assert "level 2" in rooted[0], \
		f"the breadcrumb did not re-root: {rooted[0]!r}"
	assert any("level 4" in line for line in rooted), \
		"the re-rooted window did not reach deeper Work"
	back = ptyharness.replay(steps[3], columns=110, lines=24)
	assert any("level 0" in line for line in back), \
		"Esc did not return to the root window"


@pytest.mark.serial
def test_a_resize_keeps_the_three_levels_and_the_icon(world):
	_chain(world, 4)
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"", 0.6), ("resize", (60, 24), 0.9), (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	for label, columns, step in (("wide", 110, steps[0]),
	                             ("narrow", 60, steps[1])):
		screen = ptyharness.replay(step, columns=columns, lines=24)
		levels = _levels(screen)
		assert len(levels) == 3, f"{label}: {levels}"
		assert any("▸" in line for line in screen), \
			f"{label}: the more-levels icon is missing"
