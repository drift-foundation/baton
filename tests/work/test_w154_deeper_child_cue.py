"""W154: a long title must not delete the fact that Work is hidden.

Live evidence: W5, `Rewrite public docs and architecture for v11`, showed
no sign that W6 existed beneath it. JSON proved W5 had one open child and
that W6 was actively claimed. `u` exposed it, so the Work was there all
along — the renderer had appended `▸1` after the complete title and then
cut the combined string to the Title column, and the title was long
enough to take the cue with it.

The cue is structure, not text. It is laid out before the title and the
title takes what is left, so width, title length, selection, filters and
the other columns can shorten the TITLE and never the disclosure.

A parent's Handler is untouched by any of this: the cue says deeper Work
exists, while Handler keeps naming only the exact claimed row.
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

# The live shape, verbatim: the title that hid its own child.
LIVE_TITLE = "Rewrite public docs and architecture for v11"


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

	# The live shape, moved one level down by W155.
	#
	# W154's own guarantee is unchanged: wherever the disclosure appears,
	# a long title must not delete it. What W155 changed is WHICH row
	# carries it — the window now shows three levels, so the cue belongs
	# to the deepest visible row whose own children are outside it. The
	# long title therefore sits at depth 2, which is where the cue is,
	# because a fixture that put it anywhere else would be asserting
	# nothing.
	epic = make("the v11 documentation epic", origin="external-report")
	mid = make("Retire v10 code and data", parent=epic)
	parent = make(LIVE_TITLE, parent=mid)                        # depth 2
	hidden = make("Rewrite the Codex documents", parent=parent)  # outside
	yield {"store": store, "config": config_path, "root": epic,
	       "epic": epic, "mid": mid, "parent": parent,
	       "hidden": hidden, "make": make}
	store.close()


def _rows(world, viewer="ada"):
	return pj.tree(world["store"], viewer_team="lang",
	               viewer_member=viewer)["rows"]


def _row(world, work):
	return next(row for row in _rows(world) if row["id"] == work)


# -- the cell, at every width ------------------------------------------------

@pytest.mark.parametrize("title_width", list(range(9, 61)))
def test_the_disclosure_survives_every_title_width(world, title_width):
	"""The defect, directly. The cue is present at every width where the
	row is painted at all — including widths far below anything the
	table will actually offer, because the guarantee is structural and
	not a happy consequence of the columns being roomy."""
	cell = _title_cell(_row(world, world["parent"]), title_width)
	assert "▸" in cell, f"the disclosure vanished at width {title_width}"
	assert cell.startswith("  ↳ ▸1 "), cell
	assert len(cell) == title_width


def test_a_long_title_loses_text_and_never_the_cue(world):
	"""What the two layouts do differently, side by side."""
	row = _row(world, world["parent"])
	narrow = _title_cell(row, 18)
	assert "▸1" in narrow
	# the title is what gives way
	assert not narrow.strip().endswith(row["title"])
	assert row["title"].startswith(narrow.split("▸1 ", 1)[1].rstrip())


def test_a_leaf_child_carries_no_disclosure(world):
	"""'Leaf rows never show the cue.'"""
	leaf = world["make"]("a childless child", parent=world["root"])
	cell = _title_cell(_row(world, leaf), 40)
	assert cell.startswith("↳ a childless child"), cell
	assert "▸" not in cell
	# and a row whose children ARE inside the window discloses nothing
	# either — there is nothing hidden to disclose.
	assert "▸" not in _title_cell(_row(world, world["mid"]), 40)


def test_a_root_row_carries_no_containment_marker(world):
	"""A root's children are painted inline beneath it, so there is
	nothing hidden to disclose."""
	cell = _title_cell(_row(world, world["root"]), 60)
	assert cell.startswith("the v11 documentation epic")
	assert "↳" not in cell and "▸" not in cell


def test_the_count_is_the_canonical_progress_total(world):
	"""The cue is projection data, not a client-side tally."""
	row = _row(world, world["parent"])
	assert row["progress"]["children"] == 1
	assert "▸1 " in _title_cell(row, 40)
	world["make"]("second hidden child", parent=world["parent"])
	assert "▸2 " in _title_cell(_row(world, world["parent"]), 40)


def test_a_wide_count_still_leaves_the_cue_visible(world):
	"""A three-digit count widens the reserved space; the title yields,
	the cue does not."""
	row = dict(_row(world, world["parent"]))
	row["progress"] = {"children": 128, "closed": 0}
	cell = _title_cell(row, 16)
	assert cell.startswith("  ↳ ▸128 "), cell


# -- Handler is not the cue --------------------------------------------------

def test_a_claimed_deeper_work_does_not_lend_its_handler_upward(world):
	"""'Do not copy a child's Handler onto its parent.' This is the live
	shape: W6 was actively claimed while W5, the row actually painted,
	was not."""
	tr.claim_work(world["store"], world["hidden"], actor_team="lang",
	              actor="ada")
	painted = {row["id"]: row for row in _rows(world)}
	assert world["hidden"] not in painted, \
		"the hidden Work is inside the window; the fixture proves nothing"
	parent = painted[world["parent"]]
	assert parent["handler"] is None, \
		"the parent borrowed its hidden child's claimant"
	# and it still says something is under there
	assert "▸1 " in _title_cell(parent, 40)


def test_a_row_shows_its_own_handler_when_it_is_claimed(world):
	"""The cue and the Handler answer different questions, so a row that
	IS claimed still names its claimant."""
	leaf = world["make"]("a claimable leaf", parent=world["root"])
	tr.claim_work(world["store"], leaf, actor_team="lang", actor="ada")
	assert _row(world, leaf)["handler"]["member"] == "ada"
	assert "▸" not in _title_cell(_row(world, leaf), 40)


# -- the drawn table ---------------------------------------------------------

class Screen:
	def __init__(self):
		self.rows = {}

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]

	def lines(self):
		return [self.rows[key] for key in sorted(self.rows)]


def _painted(world, width=110, height=24, viewer="ada"):
	console = Console(world["store"], "lang", viewer,
	                  config_path=world["config"])
	screen = Screen()
	console._render_table(screen, height, width, _rows(world))
	return screen.lines()


@pytest.mark.parametrize("width", [110, 92, 80, 72, 64, 56, 48, 44])
def test_the_drawn_row_keeps_the_cue_at_every_supported_width(world, width):
	"""'at every supported width where the Work row itself is shown'."""
	painted = _painted(world, width=width)
	rows = [line for line in painted if "↳" in line]
	assert rows, f"no containment row is painted at width {width}"
	assert any("▸1" in line for line in rows), \
		f"the disclosure is gone at width {width}: {rows}"


def test_the_live_shape_reproduces_and_is_fixed(world):
	"""The exact reported case: a long parent title, one open claimed
	child, and the operator able to see that something is under it."""
	tr.claim_work(world["store"], world["hidden"], actor_team="lang",
	              actor="ada")
	painted = _painted(world, width=110)
	# the title itself truncates, which is the point — find the row by
	# the structure that CANNOT truncate.
	row = next(line for line in painted if "▸" in line)
	assert "▸1" in row, f"the live shape still hides its deeper Work: {row}"
	assert "ada" not in row, "the row borrowed its hidden child's claimant"
	assert not any("Rewrite the Codex" in line for line in painted), \
		"the deeper Work painted at this level"


def test_selection_does_not_erase_the_cue(world):
	"""The reversed selection attribute and the actionable bold both
	repaint the Title cell; each must repaint the SAME cell."""
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	for cursor in range(0, 2):
		console.cursor = cursor
		console.selected_id = None
		screen = Screen()
		console._render_table(screen, 24, 110, _rows(world))
		child = [line for line in screen.lines() if "▸" in line]
		assert child, f"selection at {cursor} erased the disclosure"


def test_the_actionable_bold_repaint_keeps_the_cue(world):
	"""W81 repaints the Title cell in bold for the viewer's actionable
	Work. That second paint must draw the SAME cell — otherwise the row
	that most wants attention is the one that loses its disclosure.

	Reachable because `progress.children` counts ALL children: a row
	whose deeper Work is closed still discloses it (`u` still reaches
	it) while the row itself is ungated, ready and therefore
	actionable."""
	tr.close_work(world["store"], world["hidden"], actor_team="lang",
	              actor="ada", outcome="satisfying", rationale="done")
	row = _row(world, world["parent"])
	assert row["ready"] is True and row["handler"] is None
	assert row["progress"]["children"] == 1, \
		"the closed child stopped counting; the fixture proves nothing"
	from baton_work.tui.app import actionable_work
	assert actionable_work(row, "lang", "ada"), \
		"the row is not actionable, so the bold repaint never runs"
	painted = _painted(world, width=110)
	assert any("↳ ▸1 " in line for line in painted), \
		f"the bold repaint erased the disclosure: {painted}"


def test_a_filtered_view_keeps_the_cue(world):
	"""Filters change WHICH rows are shown, never whether a shown row
	tells the truth about what is under it."""
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"],
	                  work_filter={"classification": "suspected-defect"})
	screen = Screen()
	console._render_table(screen, 24, 110, _rows(world))
	assert [line for line in screen.lines() if "▸" in line], \
		"a filtered view dropped the disclosure"


# -- a real terminal ---------------------------------------------------------

@pytest.mark.serial
def test_a_real_terminal_shows_the_cue_and_survives_a_resize(world):
	"""Virtual screens can agree with a bug the terminal disagrees with,
	so the live shape is driven on a PTY — wide, then resized narrow."""
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"", 0.6), ("resize", (64, 24), 0.9), (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	wide = ptyharness.replay(steps[0], columns=110, lines=24)
	narrow = ptyharness.replay(steps[1], columns=64, lines=24)
	for label, screen in (("wide", wide), ("narrow", narrow)):
		rows = [line for line in screen if "↳" in line]
		assert rows, f"{label}: no child row painted"
		assert any("▸1" in line for line in rows), \
			f"{label}: the disclosure is missing: {rows}"


@pytest.mark.serial
def test_the_cue_precedes_the_title_on_a_real_terminal(world):
	"""Not merely present — present in the reserved position, so the
	title is what truncates."""
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada", [(b"", 0.6), (b"qy", 0.4)],
		columns=70, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	row = next(line for line in ptyharness.replay(steps[0], columns=70,
	                                              lines=24)
	           if "▸" in line)
	assert "↳ ▸1 " in row, row
	# W2938 removed the Jobs `New` column, which freed enough width for
	# `Next` to survive at 70 columns — and the Title, the one column
	# this layout may truncate, absorbed the difference. So the ordering
	# is asserted STRUCTURALLY rather than against a fixed number of
	# title characters: whatever fits after the cue must be a prefix of
	# the live title, which says the disclosure precedes it at every
	# width instead of at this one.
	drawn = row.split("↳ ▸1 ", 1)[1].split()[0]
	assert drawn and LIVE_TITLE.startswith(drawn), (drawn, row)


# -- the cue's condition, and its coupling to W155 --------------------------

def test_the_cue_is_driven_by_hidden_work_not_by_a_child_count(world):
	"""W154 reserved the cue's SPACE; W155 settled its CONDITION.

	The two are easy to confuse and were briefly wrong together: while
	W155 was in review, this Work emitted the cue for any indented row
	with a non-zero child count, which stopped meaning "has hidden Work"
	the moment a third level became visible. The cue reads the
	projection's `deeper` fact, so a row whose children are painted
	beneath it carries nothing."""
	rows = {row["id"]: row for row in _rows(world)}
	visible_children = rows[world["mid"]]
	assert visible_children["progress"]["children"] > 0, \
		"the fixture's middle row has no children; it proves nothing"
	assert visible_children["deeper"] is False
	assert "▸" not in _title_cell(visible_children, 40), \
		"a row whose children are visible still claims to hide Work"

	hidden = rows[world["parent"]]
	assert hidden["progress"]["children"] > 0 and hidden["deeper"] is True
	assert "▸" in _title_cell(hidden, 40)


def test_a_child_count_alone_never_produces_the_cue(world):
	"""Directly: the same row, differing only in `deeper`. If the cue
	ever goes back to reading the count, this is the line that says so."""
	row = dict(_row(world, world["parent"]))
	assert row["progress"]["children"] > 0
	assert "▸" in _title_cell(dict(row, deeper=True), 40)
	assert "▸" not in _title_cell(dict(row, deeper=False), 40), \
		"the cue fired on a child count with nothing hidden"


def test_the_disclosure_condition_comes_from_the_projection(world):
	"""The TUI must not re-derive it. `deeper` is a window fact — which
	rows this call returned — and only the projection knows that, so a
	client computing it from depth or counts would get the filtered and
	re-rooted cases wrong."""
	assert all("deeper" in row for row in _rows(world)), \
		"the projection stopped publishing the disclosure condition"
	import inspect
	from baton_work.tui import app
	source = inspect.getsource(app._title_cell)
	assert 'row.get("deeper")' in source
	assert "depth == 2" not in source and "depth >= 2" not in source, \
		"the cue re-derives the window's cap instead of reading it"
