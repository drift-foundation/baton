"""W187 (finding-wait-column-label): the blocker-summary column says
`Wait` and renders arrowless `Wn` / `Wn+N`.

Acceptance: wide and narrow Work tables use `Wait` (never `Blk`) with
no blocker arrow anywhere; zero, one and multiple open blockers render
empty, `Wn`, and `Wn+N` without hiding the exact count; deterministic
selection and the `↳` containment marker stay distinct facts.
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
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import (Console, blocker_cue,         # noqa: E402
                                cue_column_width)
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title="w"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]


class Screen:
	def __init__(self):
		self.painted = []

	def addnstr(self, _y, _x, text, *_rest):
		self.painted.append(str(text))


def _paint(world, width):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	screen = Screen()
	console._render_table(screen, 24, width, console.rows())
	return screen.painted


def test_zero_one_and_many_render_empty_wn_and_wn_plus_n(world):
	free = make(world, title="free row")
	single = make(world, title="single gated")
	multi = make(world, title="multi gated")
	gate_a = make(world, title="gate a")
	gate_b = make(world, title="gate b")
	gate_c = make(world, title="gate c")
	tr.add_dependency(world["store"], single, gate_a,
	                  actor_team="lang", actor="ada")
	for gate in (gate_a, gate_b, gate_c):
		tr.add_dependency(world["store"], multi, gate,
		                  actor_team="lang", actor="ada")
	rows = {row["id"]: row for row in __import__("baton_work").projection.tree(
		world["store"], viewer_team="lang",
		viewer_member="ada")["rows"]}
	a_local = gate_a.rsplit("-", 1)[1]
	assert blocker_cue(rows[free]) == ""
	assert blocker_cue(rows[single]) == a_local
	assert blocker_cue(rows[multi]) == f"{a_local}+2", \
		"the exact remaining count is hidden"
	painted = _paint(world, 110)
	header = next(text for text in painted if "Title" in text)
	assert "Wait" in header and "Blk" not in header
	assert not any("←" in text for text in painted), \
		"a blocker arrow survived W187"
	multi_row = next(text for text in painted if "multi gated" in text)
	assert f"{a_local}+2" in multi_row


def test_narrow_tables_keep_wait_or_omit_it_whole(world):
	gated = make(world, title="gated row")
	gate = make(world, title="the gate")
	tr.add_dependency(world["store"], gated, gate,
	                  actor_team="lang", actor="ada")
	local = gate.rsplit("-", 1)[1]
	# A width where the cue still fits: Wait heading, arrowless cell.
	for width in (110, 96):
		painted = _paint(world, width)
		header = next(text for text in painted if "Title" in text)
		if "Wait" in header:
			assert "Blk" not in header
			row = next(text for text in painted
			           if "gated row" in text)
			assert local in row and "←" not in row
		else:
			# Omitted WHOLE: no fragment of the cue anywhere.
			assert not any("gated row" in text and local in text
			               for text in painted)


def test_the_wait_heading_fits_the_allocated_cue_column(world):
	"""A short `W2` cue must not allocate two cells then paint the
	four-cell `Wait` heading across the next column. The responsive fit
	judgment and every following cell use this same width."""
	gated = make(world, title="short cue")
	gate = make(world, title="gate")
	tr.add_dependency(world["store"], gated, gate,
	                  actor_team="lang", actor="ada")
	rows = __import__("baton_work").projection.tree(
		world["store"], viewer_team="lang",
		viewer_member="ada")["rows"]
	assert blocker_cue(next(row for row in rows
	                        if row["id"] == gated)) == \
		gate.rsplit("-", 1)[1]
	assert cue_column_width(rows) >= len("Wait"), \
		"the Wait heading is wider than its allocated column"
