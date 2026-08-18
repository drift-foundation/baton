"""W23: bold hot Work Titles — the reliable steady hot-zone cue.

The superseding ruling (finding-tui-hot-cue-live-visibility): terminal
blink is not reliable enough to carry the hot signal alone. Every row
the canonical `hot_work` predicate selects renders its Title cell BOLD —
only the Title cell — while the phase-cell blink is retained as the
intermediate animated cue (until W33 lands claim Age). Cold rows stay
steady; the selection attribute composes with the bold rather than
erasing it; terminals that ignore blink still present hot rows clearly.
(W81 later narrowed the bold to VIEWER-personal actionability — these
pins were revised with it: the non-bold rows here are non-actionable
for the viewer, and test_w81_personal_bold carries the full matrix.)
"""

from __future__ import annotations

import curses
import hashlib
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console, hot_work              # noqa: E402
import fixtures as fx                                         # noqa: E402

# SGR whose parameter list contains a standalone 1 (bold), tolerating
# composition and cursor movement before the text lands.
BOLD_BEFORE = (r"\x1b\[(?:\d+;)*0?1(?:;\d+)*m"
               r"(?:\x1b\[[0-9;?]*[A-Za-z])*")


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
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
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		attr = rest[1] if len(rest) > 1 else 0
		self.calls.append((y, x, str(text), attr))


def test_only_hot_titles_render_bold_and_selection_composes(world):
	"""The Title-cell overdraw exists exactly for hot rows, carries
	A_BOLD, touches ONLY the title region, and composes with the
	selection attribute instead of erasing it."""
	hot = make(world, title="hot executing")
	tr.claim_work(world["store"], hot, actor_team="lang", actor="ada")
	# W81: the non-bold contrast row is one the VIEWER cannot act on —
	# dependency-blocked (ready=false), so ada sees the arrow, not bold.
	cold = make(world, title="cold queued")
	tr.add_dependency(world["store"], cold, hot, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	rows = console.rows()
	from baton_work.tui.app import actionable_work
	assert [actionable_work(row, "lang", "ada")
	        for row in rows].count(True) == 1
	screen = Screen()
	console._render_table(screen, 24, 110, rows)
	bold_titles = [(x, text, attr) for _y, x, text, attr in screen.calls
	               if attr & curses.A_BOLD and "hot executing" in text]
	assert len(bold_titles) == 1, screen.calls
	x, text, attr = bold_titles[0]
	assert x > 0, "the bold overdraw started at the Id column"
	assert "cold" not in text and "W" != text[:1], \
		"the bold overdraw spilled past the Title cell"
	assert not any(attr & curses.A_BOLD
	               for _y, _x, text, attr in screen.calls
	               if "cold queued" in text), \
		"a cold row's title went bold"
	# the SELECTED hot row: reverse AND bold together
	console.cursor = next(index for index, row in enumerate(rows)
	                      if row["id"] == hot)
	console.selected_id = hot
	composed = Screen()
	console._render_table(composed, 24, 110, rows)
	selected = next((attr for _y, x, text, attr in composed.calls
	                 if "hot executing" in text
	                 and attr & curses.A_BOLD), None)
	assert selected is not None
	assert selected & curses.A_REVERSE, \
		"selection erased the bold instead of composing with it"


def test_the_cue_is_presentation_only(world):
	"""Painting hot rows with the bold cue changes no authority byte."""
	work = make(world, title="pure")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console._render_table(Screen(), 24, 110, console.rows())
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before


def test_hot_titles_are_bold_on_the_real_terminal(tmp_path):
	"""PTY: the bold SGR lands immediately before the hot Title text —
	for BOTH hot forms (claimed, ready review) — and never before a
	cold title; the retained phase-cell blink still animates."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	claimed = tr.create_work(store, team="lang", kind="bug",
	                         title="claimed-title",
	                         origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")["work_id"]
	tr.claim_work(store, claimed, actor_team="lang", actor="ada")
	review = tr.create_work(store, team="lang", kind="bug",
	                        title="review-title",
	                        origin="external-report",
	                        classification="suspected-defect",
	                        author="ada", body="b")["work_id"]
	# W38: bold is personal actionability. A second claimed row is the
	# hot case now — an unclaimed row of any role is nobody executing.
	tr.claim_work(store, review, actor_team="lang", actor="ada")
	cold = tr.create_work(store, team="lang", kind="bug",
	                      title="cold-title",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	# W81: dependency-blocked — not actionable, so never bold; the
	# viewer reads the arrow and the counters instead.
	tr.add_dependency(store, cold, claimed, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	for title in ("claimed-title", "review-title"):
		assert re.search(BOLD_BEFORE + re.escape(title), steps[0]), \
			f"no bold attribute before the hot title {title!r}"
	assert not re.search(BOLD_BEFORE + "cold-title", steps[0]), \
		"a cold title rendered bold"
	# W33 removed the indefinite hot-state blink: a fresh load blinks
	# NOTHING — bold Title (+ Age) is the steady cue.
	assert not re.search(r"\x1b\[(?:\d+;)*0?5(?:;\d+)*m"
	                     r"(?:\x1b\[[0-9;?]*[A-Za-z])*(actve|rview)",
	                     steps[0]), "an indefinite hot blink survived W33"


def test_the_reliable_cue_survives_narrow_widths(tmp_path):
	"""At a width where the PHASE column (the blink carrier) is dropped,
	the bold Title remains — the reliable cue is never responsive-
	omitted, because the Title never is."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	from baton_work.tui.app import visible_columns
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	work = tr.create_work(store, team="lang", kind="bug",
	                      title="narrow-hot", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	store.close()
	width = 46
	assert "PHASE" not in [name for name, _w in visible_columns(width)]
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6), (b"qy", 0.4)], columns=width, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	assert re.search(BOLD_BEFORE + "narrow-hot", steps[0]), \
		"the bold cue vanished with the dropped blink carrier"
