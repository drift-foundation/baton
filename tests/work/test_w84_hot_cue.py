"""W84: the hot-zone attention cue — a slow terminal blink on ONLY the
phase/status cell of operationally hot Work. (W33 later REMOVED the
indefinite hot-state blink — the surviving pins here are the canonical
hot predicate, presentation purity, and the no-blink guarantees; the
final cue suite lives in test_w23_bold_title / test_w33_claim_age.)

The ruled hot zone (finding-tui-recent-work-cue, superseding rule +
presentation clarification): any open Work with a non-null active
claimant, and any open ready review Work awaiting its reviewer's claim.
Blocked (ready=false) review, waiting, parked, and terminal Work stay
steady. Derived from canonical row state alone — no recency clock, no
timestamps, no authority write; phase, readiness, Current, and claimant
remain the authoritative textual facts for terminals that ignore blink.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

from baton_work.authority import Authority                    # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import hot_work                       # noqa: E402
import fixtures as fx                                         # noqa: E402

# ncurses spells blink as an SGR parameter list containing a standalone
# 5 (xterm: \\E[5m), possibly composed with other attributes and cursor
# movement before the cell text lands.
BLINK_BEFORE = (r"\x1b\[(?:\d+;)*0?5(?:;\d+)*m"
                r"(?:\x1b\[[0-9;?]*[A-Za-z])*")


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "bee": ["rview"]},
		                "kinds": ["bug"]}})
	store = Authority(database)
	yield store, config, database
	store.close()


def make(store, title="w"):
	return tr.create_work(store, team="lang", kind="bug", title=title,
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def row_of(store, work_id):
	rows = pj.tree(store, viewer_team="lang",
	               viewer_member="ada")["rows"]
	return next(row for row in rows if row["id"] == work_id)


def test_hot_zone_state_matrix(world):
	"""The focused matrix, canonical state only: claimed Work in any
	operational phase is hot; ready unclaimed review is hot; blocked
	review, waiting, parked, unclaimed non-review, and terminal Work
	are cold — and the ruled state changes flip the cue exactly."""
	store, _config, _database = world
	work = make(store)
	# open queued, unclaimed: cold
	assert not hot_work(row_of(store, work))
	# claimed (phase untouched by the orthogonal claim): hot
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert hot_work(row_of(store, work))
	# claimed research and active: hot in every executing phase
	for phase in ("research", "active"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase=phase)
		claimed = row_of(store, work)
		assert claimed["current"] is not None
		assert hot_work(claimed), phase
	# released: cold again
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="handing back")
	assert not hot_work(row_of(store, work))
	# ready unclaimed review: hot — the interval before the reviewer
	# claims is exactly the zone the cue exists for
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="review")
	review = row_of(store, work)
	assert review["current"] is None and review["ready"]
	assert hot_work(review)
	# claimed review: still hot
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert hot_work(row_of(store, work))
	# BLOCKED review is cold: the blocker gates readiness
	blocker = make(store, title="gate")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="blocked below")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	blocked = row_of(store, work)
	assert not blocked["ready"] and blocked["phase"] == "review"
	assert not hot_work(blocked)
	# the blocker itself: open queued unclaimed — cold
	assert not hot_work(row_of(store, blocker))
	# closing the blocker restores readiness: hot again with NO edit
	# to the review row itself
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert hot_work(row_of(store, work))
	# parked is cold — and leaving the park restores the review cue
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert not hot_work(row_of(store, work))
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="review")
	assert hot_work(row_of(store, work))
	# waiting is cold (waiting-on-gates needs an OPEN blocker, and the
	# waiting row is honestly not ready)
	second_gate = make(store, title="second-gate")
	tr.add_dependency(store, work, second_gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="waiting", wait="gates")
	waiting = row_of(store, work)
	assert waiting["current"] is None
	assert not hot_work(waiting)
	# terminal: cold, and the closed blocker already proved it
	closed = row_of(store, blocker)
	assert closed["status"] == "closed" and not hot_work(closed)


def test_the_cue_reads_no_clock_and_writes_nothing(world):
	"""Presentation-only, by construction and by bytes: deriving the
	cue for every row mutates nothing, and it needs no timestamp —
	hot_work is a pure function of the canonical row dict."""
	store, _config, database = world
	work = make(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(database, "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	rows = pj.tree(store, viewer_team="lang",
	               viewer_member="ada")["rows"]
	verdicts = [hot_work(row) for row in rows]
	assert verdicts == [True]
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(database, "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before, \
			"deriving the cue touched the authority"
	minimal = {"status": "open", "current": None, "phase": "review",
	           "ready": True}
	assert hot_work(minimal), \
		"the cue needed more than canonical row state"


def test_cold_tables_never_emit_blink(tmp_path):
	"""PTY: a table of only cold rows (queued unclaimed, blocked
	review, closed) emits NO blink SGR at all — the steady-state
	proof a grid replay cannot give."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = Authority(database)
	blocked = make(store, title="blocked-review")
	gate = make(store, title="gate")
	tr.set_phase(store, blocked, actor_team="lang", actor="ada",
	             phase="review")
	tr.add_dependency(store, blocked, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	done = make(store, title="finished")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"z", 0.6), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0])
	assert any("blocked-review" in line for line in screen)
	assert not re.search(BLINK_BEFORE + r"[a-z-]+", text), \
		"a cold table emitted a blink attribute"


def test_narrow_width_drops_the_cell_not_the_console(tmp_path):
	"""PTY: at a width where the PHASE column is dropped there is no
	cell to animate — the hot row renders steadily and nothing
	crashes; the refusal/collapse contract is untouched."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	from baton_work.tui.app import visible_columns
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = Authority(database)
	work = make(store, title="hot-and-narrow")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	store.close()
	width = 46
	dropped = [name for name, _w in visible_columns(width)]
	assert "PHASE" not in dropped, \
		"pick a width that actually drops the PHASE column"
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6), (b"qy", 0.4)], columns=width, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0], columns=width, lines=24)
	assert any("hot-and-narrow" in line for line in screen), screen[:6]
	assert not re.search(BLINK_BEFORE + r"[a-z-]+", text), \
		"blink emitted with no phase cell on screen"
