"""W39: inline dependency arrows in Work lists; Ready removed.

The ruled cue (finding-tui-inline-dependency-cue): `← Wn` on a row means
that Work is blocked by the named OPEN Work — the deterministic first
open blocker's authority-local selector, `+N` for the rest. A row with
no open blocker has no cue; satisfied historical edges leave the live
cue. `↳` containment and `[b] deps` stay untouched; narrow layouts omit
the cue as ONE whole responsive field, never clipping or relabeling it.
The boolean Ready column is gone — the arrow explains what must finish.
"""

from __future__ import annotations

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import (COLUMNS, DROP_ORDER, Console,  # noqa: E402
                                blocker_cue, cue_column_width)
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


def row_of(world, work_id):
	rows = pj.tree(world["store"], viewer_team="lang",
	               viewer_member="ada")["rows"]
	return next(row for row in rows if row["id"] == work_id)


def block(world, work, on):
	tr.add_dependency(world["store"], work, on, actor_team="lang",
	                  actor="ada")


class Screen:
	def __init__(self):
		self.painted = []

	def addnstr(self, _y, _x, text, *_rest):
		self.painted.append(str(text))


def test_the_projection_names_the_deterministic_first_blocker(world):
	"""`first_open_blocker` is the OLDEST open blocker's local selector
	from the one snapshot — no client inference, no N+1; closing the
	first promotes the next; closing all clears the cue and the
	satisfied edges never return to it."""
	consumer = make(world, title="gated")
	first = make(world, title="gate one")
	second = make(world, title="gate two")
	third = make(world, title="gate three")
	for blocker in (second, first, third):   # insertion order shuffled
		block(world, consumer, blocker)
	row = row_of(world, consumer)
	assert row["first_open_blocker"] == first.rsplit("-", 1)[1], \
		"the cue is not the oldest open blocker"
	assert row["open_blockers"] == 3
	assert blocker_cue(row) == f"← {first.rsplit('-', 1)[1]} +2"
	tr.close_work(world["store"], first, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	row = row_of(world, consumer)
	assert row["first_open_blocker"] == second.rsplit("-", 1)[1]
	assert blocker_cue(row) == f"← {second.rsplit('-', 1)[1]} +1"
	for blocker in (second, third):
		tr.close_work(world["store"], blocker, actor_team="lang",
		              actor="ada", rationale="done",
		              outcome="satisfying")
	row = row_of(world, consumer)
	assert row["first_open_blocker"] is None
	assert row["open_blockers"] == 0
	assert blocker_cue(row) == "", \
		"a satisfied historical edge stayed in the live cue"


def test_the_tree_fetches_blocker_selectors_in_one_batch(world):
	"""The finding explicitly refuses one extra authority read per Work.
	Growing the visible tree must not grow first-blocker SELECTs: the
	projection fetches the whole window's summaries in at most one batch."""
	for index in range(8):
		consumer = make(world, title=f"consumer {index}")
		block(world, consumer, make(world, title=f"gate {index}"))
	statements = []
	world["store"].conn.set_trace_callback(statements.append)
	try:
		pj.tree(world["store"], viewer_team="lang", viewer_member="ada")
	finally:
		world["store"].conn.set_trace_callback(None)
	selector_reads = [statement for statement in statements
	                  if "SELECT work.id FROM edges JOIN work" in statement
	                  and "ORDER BY work.created_seq LIMIT 1" in statement]
	assert len(selector_reads) <= 1, \
		f"first-open-blocker projection performed an N+1: {len(selector_reads)} reads"


def test_one_blocker_renders_without_a_count(world):
	consumer = make(world, title="single gate")
	gate = make(world, title="the gate")
	block(world, consumer, gate)
	assert blocker_cue(row_of(world, consumer)) == \
		f"← {gate.rsplit('-', 1)[1]}"
	assert blocker_cue(row_of(world, gate)) == "", \
		"the provider side grew a cue"


def test_ready_is_gone_and_the_cue_column_renders(world):
	"""The painted table: no Ready header, the Blk field carries
	`← Wn +N` on the blocked row and stays empty on others."""
	assert "READY" not in dict(COLUMNS)
	assert "READY" not in DROP_ORDER
	consumer = make(world, title="blocked row")
	for title in ("g1", "g2"):
		block(world, consumer, make(world, title=title))
	screen = Screen()
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(screen, 24, 110, console.rows())
	header = next(text for text in screen.painted if "Title" in text)
	assert "Ready" not in header, header
	assert "Blk" in header, header
	blocked = next(text for text in screen.painted
	               if "blocked row" in text)
	assert re.search(r"← W\d+ \+1", blocked), blocked
	unblocked = next(text for text in screen.painted if "g1" in text)
	assert "←" not in unblocked


def test_containment_and_dependency_stay_distinct(world):
	"""A row can be BOTH a containment child (`↳` in the title) and
	blocked (`← Wn` in the cue field) — two facts, two markers, never
	conflated."""
	parent = make(world, title="the parent")
	child = tr.create_work(world["store"], team="lang", kind="bug",
	                       title="the child", origin="external-report",
	                       classification="suspected-defect",
	                       author="ada", body="b",
	                       parent=parent)["work_id"]
	gate = make(world, title="the gate")
	block(world, child, gate)
	screen = Screen()
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(screen, 24, 110, console.rows())
	child_row = next(text for text in screen.painted
	                 if "the child" in text)
	assert "↳ the child" in child_row, child_row
	assert f"← {gate.rsplit('-', 1)[1]}" in child_row, child_row
	gate_row = next(text for text in screen.painted
	                if "the gate" in text)
	assert "↳" not in gate_row and "←" not in gate_row


def test_narrow_widths_omit_the_cue_whole_never_clip_it(world):
	"""When the cue field alone breaks the fit it disappears entirely —
	no `←` fragment survives — while the table itself still paints and
	`[b] deps` remains the full view."""
	consumer = make(world, title="tight")
	block(world, consumer, make(world, title="gate"))
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	wide = Screen()
	console._render_table(wide, 24, 110, console.rows())
	assert any("←" in text for text in wide.painted)
	# find a width where the table fits WITHOUT the cue but not with it
	from baton_work.tui.app import id_column_width, layout_fits
	rows = console.rows()
	visible, _hidden = console.visible_rows(rows)
	id_width = id_column_width(visible)
	cue = cue_column_width(visible)
	narrow = next(w for w in range(120, 30, -1)
	              if layout_fits(w, id_width)
	              and not layout_fits(w, id_width + 1 + cue))
	tight = Screen()
	console._render_table(tight, 24, narrow, rows)
	assert not any("←" in text for text in tight.painted), \
		"the cue was clipped instead of omitted whole"
	assert not any("Blk" in text for text in tight.painted)
	assert any("tight" in text for text in tight.painted), \
		"the table stopped painting instead of omitting the cue"
	# the full dependency view stays reachable
	links = pj.links(world["store"], consumer)
	assert links["blocked_by"], "the [b] deps view lost the edge"


def test_the_cue_follows_refresh(world):
	"""Closing the gate through the public CLI removes the cue on the
	next painted rows — canonical data in, no stale arrow out."""
	consumer = make(world, title="refreshed")
	gate = make(world, title="short gate")
	block(world, consumer, gate)
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	before = Screen()
	console._render_table(before, 24, 110, console.rows())
	assert any("←" in text for text in before.painted)
	console.execute(f"close work={gate.rsplit('-', 1)[1]} "
	                f"rationale=done outcome=satisfying")
	assert console.status.startswith("ok"), console.status
	after = Screen()
	console._render_table(after, 24, 110, console.rows())
	blocked_row = next(text for text in after.painted
	                   if "refreshed" in text)
	assert "←" not in blocked_row, \
		"a satisfied edge kept its live cue"


def test_json_and_tui_agree_on_the_cue(world):
	"""Parity: the painted cue is exactly the canonical
	first_open_blocker + open_blockers rendering — nothing invented by
	the terminal."""
	consumer = make(world, title="parity row")
	for title in ("p1", "p2", "p3"):
		block(world, consumer, make(world, title=title))
	row = row_of(world, consumer)
	expected = f"← {row['first_open_blocker']} +{row['open_blockers'] - 1}"
	assert blocker_cue(row) == expected
	screen = Screen()
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(screen, 24, 110, console.rows())
	painted = next(text for text in screen.painted
	               if "parity row" in text)
	assert expected in painted, (expected, painted)
