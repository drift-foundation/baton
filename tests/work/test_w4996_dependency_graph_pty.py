"""W4996: the dependency graph on a REAL terminal.

`work/records/2026/08/finding-ascii-dependency-neighborhood/`, contract
approved 2026-08-22 without amendment.

The focused suite drives the projection, the pure renderer and the console's
key handling directly. That is where the boundaries live and it is where they
are asserted — but none of it proves what an operator actually SEES. curses
chooses freely among cursor-addressing spellings, a footer can be painted and
then overdrawn, and a layout that fits in a unit test can wrap on a terminal
that is one column narrower than the code believed.

So every assertion here replays the raw byte stream into a character grid and
asks what a human would have read. The contract's own PTY list is what these
cover: many-to-one, one-to-many, both sides at once, narrow and resized
screens, the footer key legend, and the containment/duplicate/follow-up text
that must NOT appear on this page.
"""

from __future__ import annotations

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
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")

WIDE, TALL = 120, 32


# THE CENTER IS SELECTED THROUGH SEARCH, not by counting table rows.
#
# The Jobs table orders by readiness and priority, so which row leads is a
# property of the fixture's dependency shape — the very thing these cases
# vary. Searching for the centre's exact title is deterministic across every
# shape, and it exercises the search entry path the contract also requires.
OPEN_CENTER = [(b"/", 0.5), (b"the center", 0.5), (b"\r", 0.7),
               (b"b", 0.8)]


def build(tmp_path, shape):
	"""One authority whose dependency shape is named by `shape`."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config, participant="lang.ada")["database"]
	store = bw.Authority(database)

	def make(title):
		return tr.create_work(store, team="lang", kind="bug", title=title,
		                      origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="opener")["work_id"]

	def depend(work, blocker):
		tr.add_dependency(store, work, blocker, actor_team="lang",
		                  actor="ada", rationale="waits on it")

	center = make("the center")
	made = {"center": center}
	if shape in ("many-to-one", "both"):
		for index in range(3):
			blocker = make(f"blocker {index}")
			made[f"blocker{index}"] = blocker
			depend(center, blocker)
	if shape in ("one-to-many", "both"):
		for index in range(3):
			consumer = make(f"consumer {index}")
			made[f"consumer{index}"] = consumer
			depend(consumer, center)
	if shape == "lonely":
		pass
	if shape == "containment":
		# A CHILD, a DUPLICATE and a FOLLOW-UP, none of which belongs on
		# this page. They exist so their absence is a measurement.
		tr.create_work(store, team="lang", kind="bug", title="the child",
		               origin="decomposition",
		               classification="suspected-defect", author="ada",
		               body="opener", parent=center)
		other = make("the duplicate")
		tr.close_work(store, other, actor_team="lang", actor="ada",
		              outcome="rejected", rationale="same as the center",
		              duplicate_of=center)
	store.close()
	return config, made


def screen(config, script, columns=WIDE, lines=TALL, dynamic=False):
	text, status, steps = ptyharness.drive(
		config, "lang.ada", OPEN_CENTER + list(script) + [(b"qy", 0.4)],
		columns=columns, lines=lines, dynamic_size=dynamic)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, status
	rendered = steps[-2] if len(steps) > 1 else text
	return ptyharness.replay(rendered, columns=columns, lines=lines)


def local(work_id):
	return work_id.rsplit("-", 1)[-1]


# -- the shapes --------------------------------------------------------------

def test_many_to_one_draws_every_blocker_reaching_the_center(tmp_path):
	config, made = build(tmp_path, "many-to-one")
	painted = "\n".join(screen(config, []))
	centre = local(made["center"])
	for index in range(3):
		blocker = local(made[f"blocker{index}"])
		assert f"[{blocker} " in painted, painted
		# DIRECTION, spelled on the row: the blocker blocks the center.
		assert any(f"[{blocker} " in line and "--blocks-->" in line
		           and f"[{centre} " in line.split("--blocks-->")[1]
		           for line in painted.split("\n")), painted


def test_one_to_many_draws_every_consumer_the_center_reaches(tmp_path):
	config, made = build(tmp_path, "one-to-many")
	painted = "\n".join(screen(config, []))
	centre = local(made["center"])
	for index in range(3):
		consumer = local(made[f"consumer{index}"])
		assert any(f"[{centre} " in line.split("--blocks-->")[0]
		           and f"[{consumer} " in line.split("--blocks-->")[1]
		           for line in painted.split("\n")
		           if "--blocks-->" in line), painted


def test_both_sides_are_drawn_around_one_center(tmp_path):
	"""The whole reason this view exists: the operator sees the Work
	BETWEEN what it waits on and what waits on it, without reconstructing
	it mentally from two flat lists."""
	config, made = build(tmp_path, "both")
	rows = screen(config, [])
	painted = "\n".join(rows)
	centre = local(made["center"])
	upstream = [line for line in rows if "--blocks-->" in line
	            and f"[{centre} " in line.split("--blocks-->")[1]]
	downstream = [line for line in rows if "--blocks-->" in line
	              and f"[{centre} " in line.split("--blocks-->")[0]]
	assert len(upstream) == 3, painted
	assert len(downstream) == 3, painted
	# Upstream reads outermost-to-centre and downstream centre-to-outermost,
	# so every blocker row precedes every dependent row.
	assert rows.index(upstream[-1]) < rows.index(downstream[0]), painted


# -- what must NOT be here ---------------------------------------------------

def test_containment_duplicates_and_follow_ups_stay_off_this_page(tmp_path):
	"""The dependency-only scope clarification, measured rather than
	assumed. Containment stays in the Jobs tree; duplicates and follow-ups
	keep their own projections."""
	config, made = build(tmp_path, "containment")
	painted = "\n".join(screen(config, []))
	for absent in ("the child", "the duplicate", "duplicate-of", "duplicate",
	               "follow-up", "↳"):
		assert absent not in painted, (absent, painted)
	# And the page really did open — an empty screen would pass the above.
	assert "depth 1/3" in painted, painted


def test_the_empty_neighbourhood_says_so(tmp_path):
	config, _made = build(tmp_path, "lonely")
	painted = "\n".join(screen(config, []))
	assert "(no blocking or dependent neighbors)" in painted, painted
	assert "--blocks-->" not in painted, painted


# -- the footer --------------------------------------------------------------

def test_the_footer_names_every_key_the_page_answers_to(tmp_path):
	config, _made = build(tmp_path, "both")
	painted = "\n".join(screen(config, []))
	for legend in ("depth 1/3", "[Enter] recenter", "[+/-] depth",
	               "[Esc] back"):
		assert legend in painted, (legend, painted)


def test_the_footer_follows_the_depth_it_reports(tmp_path):
	config, _made = build(tmp_path, "both")
	painted = "\n".join(screen(config, [(b"+", 0.6)]))
	assert "depth 2/3" in painted, painted
	assert "depth 1/3" not in painted, painted


# -- geometry ----------------------------------------------------------------

def test_a_narrow_terminal_keeps_every_relationship(tmp_path):
	"""A narrow terminal loses LAYOUT, never a relationship. An operator
	who widened the window and saw a new edge appear would have been
	looking at a lie."""
	config, made = build(tmp_path, "both")
	wide = "\n".join(screen(config, []))
	narrow = "\n".join(screen(config, [], columns=64, lines=32))
	for name, work in made.items():
		if name == "center":
			continue
		assert f"[{local(work)} " in wide, (name, wide)
		assert f"[{local(work)} " in narrow, (name, narrow)


def test_a_resize_in_both_directions_moves_nothing(tmp_path):
	"""Resize never changes centre, depth, expansion or selection — which
	is why it cannot move an ACTION to another Work."""
	config, made = build(tmp_path, "both")
	text, status, steps = ptyharness.drive(
		config, "lang.ada",
		OPEN_CENTER + [("resize", (64, 24), 0.8),
		               ("resize", (120, 32), 0.8), (b"qy", 0.4)],
		columns=WIDE, lines=TALL, dynamic_size=True)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	opened = "\n".join(ptyharness.replay(steps[3], columns=WIDE, lines=TALL))
	shrunk = "\n".join(ptyharness.replay(steps[4], columns=64, lines=24))
	grown = "\n".join(ptyharness.replay(steps[5], columns=WIDE, lines=TALL))
	assert "depth 1/3" in opened and "depth 1/3" in grown, (opened, grown)
	centre = local(made["center"])
	for painted in (opened, shrunk, grown):
		assert f"[{centre} " in painted, painted
	# Every Work survives the round trip; the layout is what changed.
	for name, work in made.items():
		assert f"[{local(work)} " in grown, (name, grown)


def test_a_narrow_terminal_reaches_the_STACKED_fallback_and_survives(tmp_path):
	"""The narrow FALLBACK, which is a different boundary from the narrow
	REFUSAL — and the one a real operator actually reaches.

	The refusal needs a terminal narrower than one complete selector, and
	the console's own table cannot start at such a width, so that boundary
	is asserted in the focused suite where it can be measured. What IS
	reachable here is the stacked form, and reaching it USED TO KILL THE
	CONSOLE: its presentation rows carry no identity by design, and the
	selection anchor assumed every row had a Work. A 30-column terminal
	exited 1 with a traceback while every focused case passed."""
	config, made = build(tmp_path, "both")
	rows = screen(config, [], columns=30, lines=24)
	painted = "\n".join(rows)
	centre = local(made["center"])
	assert f"[{centre} " in painted, painted
	# Every relationship survives the narrowest form, whichever renderer
	# drew it — the arrow may be on its own row now.
	for name, work in made.items():
		assert f"[{local(work)} " in painted, (name, painted)
	assert "--blocks-->" in painted, painted


# -- navigation --------------------------------------------------------------

def test_enter_recenters_on_a_real_terminal_and_esc_comes_back(tmp_path):
	config, made = build(tmp_path, "both")
	text, status, steps = ptyharness.drive(
		config, "lang.ada",
		OPEN_CENTER + [(b"j", 0.5), (b"\r", 0.8), (b"\x1b", 0.7),
		               (b"\x1b", 0.7), (b"qy", 0.4)],
		columns=WIDE, lines=TALL)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	recentred = "\n".join(ptyharness.replay(steps[5], columns=WIDE, lines=TALL))
	# Two graph frames in the trail, and still the graph — not the table.
	assert recentred.count("deps") >= 2, recentred
	assert "depth 1/3" in recentred, recentred
	back = "\n".join(ptyharness.replay(steps[6], columns=WIDE, lines=TALL))
	assert "depth 1/3" in back, "the first Esc left the graph entirely"
	table = "\n".join(ptyharness.replay(steps[7], columns=WIDE, lines=TALL))
	assert "Title" in table, "the last Esc did not return to the table"
