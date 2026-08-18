"""W105: the phase-change pulse covers the whole visible Work row.

The cue was right and nearly invisible. It blinked one cell — Phase —
so it was easy to miss while scanning Titles, and at narrow widths the
responsive layout drops PHASE entirely, which removed the cue exactly
where a row is hardest to read.

Composing `A_BLINK` into the row's base attribute rather than
overpainting one cell is what makes it survive column omission and
compose with selection and the actionable-Title bold instead of
replacing either.

Nothing about WHEN it arms changes: one cold baseline, a genuine phase
change arms it, and three successful scheduled reads drain it. Those are
W33/W336's rules and this Work does not touch them.
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
	yield {"store": store, "config": config_path}
	store.close()


def _make(world, title="w", parent=None):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b", parent=parent)["work_id"]


class Screen:
	"""Every painted fragment with the attribute it was painted with."""

	def __init__(self):
		self.painted = []

	def addnstr(self, y, x, text, n, *rest):
		self.painted.append({"y": y, "x": x, "text": str(text)[:n],
		                     "attribute": rest[0] if rest else 0})

	def fragments(self, y):
		return [entry for entry in self.painted if entry["y"] == y]


def _rows(world, viewer="ada"):
	return pj.tree(world["store"], viewer_team="lang",
	               viewer_member=viewer)["rows"]


def _paint(world, blink=(), width=110, viewer="ada", cursor=0,
           work_filter=None):
	console = Console(world["store"], "lang", viewer,
	                  config_path=world["config"], work_filter=work_filter)
	console.phase_blink = {work: 3 for work in blink}
	console.cursor = cursor
	screen = Screen()
	console._render_table(screen, 24, width, _rows(world, viewer))
	return screen


def _row_line(screen, local_id):
	"""The y of the painted row whose Id cell names this Work."""
	for entry in screen.painted:
		if entry["x"] == 0 and entry["text"].startswith(f"{local_id} "):
			return entry["y"]
	raise AssertionError(f"no painted row for {local_id}: {screen.painted}")


def _local(work):
	return work.rsplit("-", 1)[1]


# -- the whole row, not one cell --------------------------------------------

def test_every_painted_fragment_of_the_changed_row_blinks(world):
	"""'Model rendering proves every painted fragment of the changed
	Work row carries blink, including Id, Title, dependency cue, and
	every retained column.'"""
	changed, blocker = _make(world, "the changed one"), _make(world, "gate")
	tr.add_dependency(world["store"], changed, blocker, actor_team="lang",
	                  actor="ada", rationale="so the row carries a cue")
	screen = _paint(world, blink=[changed])
	line = _row_line(screen, _local(changed))
	fragments = screen.fragments(line)
	assert fragments, "the changed row painted nothing"
	for entry in fragments:
		assert entry["attribute"] & curses.A_BLINK, \
			f"a fragment of the changed row does not blink: {entry}"
	# and the row it painted really is the whole row, cue included
	whole = "".join(entry["text"] for entry in fragments)
	assert _local(blocker) in whole, \
		f"the dependency cue is not on the painted row: {whole!r}"


def test_no_neighbouring_row_header_or_footer_blinks(world):
	"""'no neighboring row, header, or footer does.'"""
	changed, other = _make(world, "changed"), _make(world, "untouched")
	screen = _paint(world, blink=[changed])
	changed_line = _row_line(screen, _local(changed))
	for entry in screen.painted:
		if entry["y"] == changed_line:
			continue
		assert not entry["attribute"] & curses.A_BLINK, \
			f"something outside the changed row blinks: {entry}"
	assert any(_local(other) in entry["text"] for entry in screen.painted), \
		"the untouched row was not painted at all"


def test_an_unarmed_table_blinks_nothing(world):
	_make(world, "one")
	_make(world, "two")
	screen = _paint(world)
	assert not any(entry["attribute"] & curses.A_BLINK
	               for entry in screen.painted)


# -- composition -------------------------------------------------------------

def test_a_selected_changed_row_composes_reverse_and_blink(world):
	"""'A selected changed row composes reverse+blink.'"""
	changed = _make(world, "changed")
	screen = _paint(world, blink=[changed], cursor=0)
	line = _row_line(screen, _local(changed))
	for entry in screen.fragments(line):
		assert entry["attribute"] & curses.A_REVERSE, entry
		assert entry["attribute"] & curses.A_BLINK, entry


def test_an_actionable_title_composes_bold_blink_and_selection(world):
	"""'actionable Title composes reverse when selected plus bold+blink
	without losing any attribute.'

	The Title is painted twice — once as part of the row, once as the
	W81 actionable overpaint — and the second paint must INHERIT the
	composed attribute rather than replacing it. Overpainting with bold
	alone would erase the pulse from the one cell the eye goes to."""
	from baton_work.tui.app import actionable_work
	changed = _make(world, "changed")
	row = next(entry for entry in _rows(world) if entry["id"] == changed)
	assert actionable_work(row, "lang", "ada"), \
		"the fixture row is not actionable, so the overpaint never runs"
	screen = _paint(world, blink=[changed], cursor=0)
	line = _row_line(screen, _local(changed))
	overpaints = [entry for entry in screen.fragments(line)
	              if entry["attribute"] & curses.A_BOLD]
	assert overpaints, "the actionable Title was never overpainted"
	for entry in overpaints:
		assert entry["attribute"] & curses.A_BLINK, \
			f"the bold Title overpaint dropped the pulse: {entry}"
		assert entry["attribute"] & curses.A_REVERSE, \
			f"the bold Title overpaint dropped the selection: {entry}"


def test_an_unarmed_actionable_title_is_bold_without_blink(world):
	"""The composition must not leak the pulse into ordinary bold."""
	work = _make(world, "actionable")
	screen = _paint(world, cursor=0)
	line = _row_line(screen, _local(work))
	bolds = [entry for entry in screen.fragments(line)
	         if entry["attribute"] & curses.A_BOLD]
	assert bolds
	for entry in bolds:
		assert not entry["attribute"] & curses.A_BLINK, entry


# -- responsive layouts ------------------------------------------------------

@pytest.mark.parametrize("width", [110, 92, 80, 72, 64, 56, 48, 44])
def test_the_complete_visible_row_blinks_at_every_width(world, width):
	"""'A phase change blinks every visible cell belonging to that Work
	row, including layouts where the Phase column is dropped.'"""
	changed = _make(world, "changed")
	screen = _paint(world, blink=[changed], width=width)
	line = _row_line(screen, _local(changed))
	fragments = screen.fragments(line)
	assert fragments, f"nothing painted at width {width}"
	for entry in fragments:
		assert entry["attribute"] & curses.A_BLINK, \
			f"width {width}: {entry}"


def test_the_cue_survives_a_layout_that_drops_phase(world):
	"""The defect's sharpest case: the old cell-only pulse disappeared
	entirely at widths where PHASE is omitted — the cue was absent
	exactly where the row is hardest to read."""
	from baton_work.tui.app import visible_columns
	changed = _make(world, "changed")
	narrow = 56
	assert "PHASE" not in [name for name, _w in visible_columns(narrow, 3)], \
		"the fixture width still keeps PHASE; it proves nothing"
	screen = _paint(world, blink=[changed], width=narrow)
	line = _row_line(screen, _local(changed))
	assert all(entry["attribute"] & curses.A_BLINK
	           for entry in screen.fragments(line))


def test_the_scope_is_the_clipped_visible_row(world):
	"""'keeps the clipped visible row, not off-screen columns, as the
	exact painted scope.' Nothing is painted past the terminal, so
	nothing off-screen is animated."""
	changed = _make(world, "a title long enough to be truncated outright")
	width = 60
	screen = _paint(world, blink=[changed], width=width)
	line = _row_line(screen, _local(changed))
	for entry in screen.fragments(line):
		assert entry["x"] + len(entry["text"]) <= width, entry


# -- filtered and re-rooted windows -----------------------------------------

def test_a_filtered_window_blinks_the_same_row(world):
	changed = _make(world, "changed")
	screen = _paint(world, blink=[changed],
	                work_filter={"category": "suspected-defect"})
	line = _row_line(screen, _local(changed))
	assert all(entry["attribute"] & curses.A_BLINK
	           for entry in screen.fragments(line))


def test_a_child_row_blinks_whole(world):
	"""Containment children are painted with the same row path, so the
	cue must cover an indented row exactly as it covers a root."""
	root = _make(world, "root")
	child = _make(world, "child", parent=root)
	screen = _paint(world, blink=[child])
	line = _row_line(screen, _local(child))
	fragments = screen.fragments(line)
	assert fragments
	assert any("↳" in entry["text"] for entry in fragments), \
		"the painted row is not the containment child"
	for entry in fragments:
		assert entry["attribute"] & curses.A_BLINK, entry


# -- arming is unchanged -----------------------------------------------------

def test_a_cold_baseline_arms_nothing(world):
	"""'The initial load … does not arm or prolong the cue.'"""
	work = _make(world)
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._observe_phases(_rows(world))
	assert console.phase_blink == {}, console.phase_blink
	assert work


def test_a_genuine_phase_change_arms_three_cycles(world):
	work = _make(world)
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._observe_phases(_rows(world))
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	console._observe_phases(_rows(world))
	assert console.phase_blink.get(work) == 3


def test_a_heartbeat_arms_nothing(world):
	"""'heartbeat-only changes … do not arm or prolong the cue.'"""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._observe_phases(_rows(world))
	tr.heartbeat(world["store"], work, actor_team="lang", actor="ada")
	console._observe_phases(_rows(world))
	assert console.phase_blink == {}


def test_a_steady_refresh_arms_nothing(world):
	work = _make(world)
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	for _repeat in range(4):
		console._observe_phases(_rows(world))
	assert console.phase_blink == {}
	assert work


def test_repainting_never_drains_the_countdown(world):
	"""Only a successful SCHEDULED read spends a cycle. Painting the
	table — for a keystroke, a resize, a cached redraw — must not, or
	the pulse would drain at whatever rate the operator typed."""
	changed = _make(world, "changed")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.phase_blink = {changed: 3}
	for _repeat in range(5):
		console._render_table(Screen(), 24, 110, _rows(world))
	assert console.phase_blink == {changed: 3}, \
		"painting the table spent the countdown"


def test_the_countdown_drains_on_scheduled_cycles(world):
	changed = _make(world, "changed")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.phase_blink = {changed: 3}
	# only a SUCCESSFUL scheduled read spends a cycle, which is what
	# `owed` witnesses — an unowed call must leave the countdown alone.
	console._spend_owed_cycle(False)
	assert console.phase_blink.get(changed) == 3, \
		"an unowed cycle drained the countdown"
	for expected in (2, 1):
		console._spend_owed_cycle(True)
		assert console.phase_blink.get(changed) == expected
	console._spend_owed_cycle(True)
	assert changed not in console.phase_blink
	screen = _paint(world, blink=[])
	assert not any(entry["attribute"] & curses.A_BLINK
	               for entry in screen.painted)
