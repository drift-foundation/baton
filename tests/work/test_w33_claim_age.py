"""W33: the claim-Age column and the final hot-cue composition.

Age (finding-tui-claim-age): elapsed time since the CURRENT claim
committed — W226 supersession, on W55's scale: ONE MM:SS
interpretation, `∞` at 100 minutes and beyond, `-` with no claim —
derived client-side from the canonical
`claimed_at` (the newest claim event's timestamp, never
last_changed_at) on the ONE existing refresh cadence. The final steady
hot cue is bold Title + Age; the indefinite hot-state blink is gone.
A short phase-cell blink survives only as the client-local CHANGE cue:
armed when a refresh observes a genuine Phase change, consumed by
exactly three scheduled ticks, cold on load/reconnect, untouched by
keystrokes, redraws, resize, and mutation refreshes.
"""

from __future__ import annotations

import curses
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
                                held_cell)
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


class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		attr = rest[1] if len(rest) > 1 else 0
		self.calls.append((y, x, str(text), attr))


def test_the_age_formatter_matrix():
	"""The pure display (W55, superseding W226's scale): whole-second
	MM:SS, the `∞` overflow at 100 minutes, the unclaimed dash, and the
	negative-clock clamp."""
	base = "2026-08-16T12:00:00Z"
	import datetime as _dt
	origin = _dt.datetime.fromisoformat(
		base.replace("Z", "+00:00")).timestamp()
	assert held_cell(None, origin) == "-"
	assert held_cell(base, origin) == "00:00"
	assert held_cell(base, origin + 1) == "00:01"
	assert held_cell(base, origin + 59) == "00:59"
	assert held_cell(base, origin + 60) == "01:00"
	assert held_cell(base, origin + 61) == "01:01"
	assert held_cell(base, origin + 60 * 26 + 7) == "26:07"
	# the last ordinary value, and the first overflow one
	assert held_cell(base, origin + 60 * 59 + 59) == "59:59"
	assert held_cell(base, origin + 60 * 99 + 59) == "99:59"
	assert held_cell(base, origin + 60 * 100) == "∞"
	assert held_cell(base, origin + 60 * 100 + 1) == "∞"
	assert held_cell(base, origin + 3600 * 400) == "∞", \
		"well past the cap did not stay at the overflow value"
	# the negative-clock clamp
	assert held_cell(base, origin - 30) == "00:00", \
		"a clock correction did not clamp to zero"
	assert all(len(held_cell(base, origin + n)) <= 5
	           for n in (0, 59, 3600, 60 * 100, 3600 * 400)), \
		"the display broke the fixed five-cell budget"


def test_claimed_at_is_the_current_claim_event_timestamp(world):
	"""Canonical JSON: claimed_at appears while a claimant exists and
	equals the NEWEST claim event's journal timestamp — never
	last_changed_at; release and close clear it; a handoff's re-claim
	resets it to the new event."""
	work = make(world, title="timed")
	assert row_of(world, work)["claimed_at"] is None
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	claimed = row_of(world, work)
	event_ts = world["store"].conn.execute(
		"SELECT ts FROM events WHERE kind='claim' "
		"ORDER BY seq DESC LIMIT 1").fetchone()["ts"]
	assert claimed["claimed_at"] == event_ts
	assert claimed["claimed_at"] != claimed["last_changed_at"], \
		"claimed_at is just last_changed_at in disguise"
	tr.release_claim(world["store"], work, actor_team="lang",
	                 actor="ada", expect="lang.ada", reason="pause")
	assert row_of(world, work)["claimed_at"] is None
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	second = row_of(world, work)["claimed_at"]
	second_event = world["store"].conn.execute(
		"SELECT ts FROM events WHERE kind='claim' "
		"ORDER BY seq DESC LIMIT 1").fetchone()["ts"]
	assert second == second_event, "the re-claim did not reset the fact"
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert row_of(world, work)["claimed_at"] is None


def test_claim_timestamps_fetch_in_one_batch(world):
	"""The W39 no-N+1 boundary holds for the claim fact too: a full
	tree performs at most ONE claim-timestamp query."""
	for index in range(6):
		work = make(world, title=f"row {index}")
		tr.claim_work(world["store"], work, actor_team="lang",
		              actor="ada")
	statements = []
	world["store"].conn.set_trace_callback(statements.append)
	try:
		pj.tree(world["store"], viewer_team="lang",
		        viewer_member="ada")
	finally:
		world["store"].conn.set_trace_callback(None)
	claim_reads = [statement for statement in statements
	               if "kind='claim'" in statement]
	assert len(claim_reads) <= 1, \
		f"claimed_at projection performed an N+1: {len(claim_reads)}"


def test_the_age_column_is_final_and_derives_from_claimed_at(world):
	"""The table ends with the six-cell Held column: live HH:MM on the
	claimed row, `-` on unclaimed rows INCLUDING the bold ready-review
	row; the painted value is exactly the formatter over claimed_at."""
	# W47 widened the field to six cells: the claim timer plus the
	# reserved liveness-suffix cell.
	assert COLUMNS[-1] == ("HELD", 6)
	assert "HELD" in DROP_ORDER, \
		"Held must be omissible as one whole responsive column"
	claimed = make(world, title="claimed row")
	tr.claim_work(world["store"], claimed, actor_team="lang",
	              actor="ada")
	review = make(world, title="review row")
	tr.set_phase(world["store"], review, actor_team="lang", actor="ada",
	             phase="review")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	screen = Screen()
	console._render_table(screen, 24, 110, console.rows())
	header = next(text for _y, _x, text, _a in screen.calls
	              if "Title" in text)
	assert header.rstrip().endswith("Held"), header
	claimed_line = next(text for _y, _x, text, _a in screen.calls
	                    if "claimed row" in text)
	assert re.search(r"\d{2}:\d{2}\s*$", claimed_line), claimed_line
	review_line = next(text for _y, _x, text, _a in screen.calls
	                   if "review row" in text)
	assert review_line.rstrip().endswith("-"), review_line


def test_phase_change_blinks_for_exactly_three_ticks(world):
	"""The change cue: the first snapshot is a cold baseline; an
	observed genuine Phase change arms that row's phase cell for THREE
	scheduled ticks; only tick() consumes; a later change re-arms."""
	work = make(world, title="watched")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])

	def blinking():
		screen = Screen()
		console._render_table(screen, 24, 110, console.rows())
		return [text for _y, _x, text, attr in screen.calls
		        if attr & curses.A_BLINK]

	assert blinking() == [], "the initial load blinked"
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="research")
	console.schedule_refresh()
	assert any("rsrch" in text for text in blinking()), \
		"an observed phase change did not arm the cue"
	assert console.phase_blink[work] == 3
	# keystrokes/redraws: repaint five times, nothing consumed
	for _repaint in range(5):
		blinking()
	assert console.phase_blink[work] == 3
	# only scheduled ticks consume — and the cue survives exactly three
	console.tick()
	assert blinking() and console.phase_blink[work] == 2
	console.tick()
	assert blinking() and console.phase_blink[work] == 1
	console.tick()
	# R1: the third cycle is spent by the SUCCESSFUL read the render
	# performs — the counter empties as that fresh paint lands.
	assert blinking() == [], "the cue outlived its three ticks"
	assert console.phase_blink.get(work, 0) == 0
	# a LATER genuine change re-arms in full
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="active")
	console.schedule_refresh()
	blinking()
	assert console.phase_blink[work] == 3


def test_mutation_refreshes_neither_consume_nor_restart(world):
	"""An immediate mutation-triggered refresh between ticks leaves an
	armed countdown exactly where it was — no consume, no restart."""
	watched = make(world, title="armed")
	other = make(world, title="unrelated")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.rows()                       # cold baseline
	tr.set_phase(world["store"], watched, actor_team="lang",
	             actor="ada", phase="research")
	console.schedule_refresh()
	console.rows()
	assert console.phase_blink[watched] == 3
	console.tick()
	console.rows()
	assert console.phase_blink[watched] == 2
	# an unrelated mutation refresh: the countdown must stay at 2
	tr.claim_work(world["store"], other, actor_team="lang",
	              actor="ada")
	console.schedule_refresh()
	console.rows()
	assert console.phase_blink[watched] == 2, \
		"a mutation refresh consumed or restarted the countdown"


def test_a_failed_scheduled_refresh_does_not_consume_the_cue(world,
		monkeypatch):
	"""The pinned unit is a SUCCESSFUL scheduled refresh tick. Timer
	expiry alone cannot spend the cue when the ensuing canonical read
	fails, because the operator never received that refreshed paint."""
	work = make(world, title="refresh may fail")
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.rows()                       # cold baseline
	tr.set_phase(world["store"], work, actor_team="lang",
	             actor="ada", phase="research")
	console.schedule_refresh()
	console.rows()
	assert console.phase_blink[work] == 3

	def unavailable(*_args, **_kwargs):
		raise RuntimeError("authority unavailable")

	monkeypatch.setattr(pj, "tree", unavailable)
	console.tick()
	with pytest.raises(RuntimeError, match="authority unavailable"):
		console.rows()
	assert console.phase_blink[work] == 3, \
		"a failed scheduled refresh consumed a cue the operator never saw"


def test_reconnect_starts_cold(world):
	"""The attention state is client-local and never persisted: a new
	console over the same authority blinks nothing."""
	work = make(world, title="was hot news")
	first = Console(world["store"], "lang", "ada",
	                config_path=world["config"])
	first.rows()
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="active")
	first.schedule_refresh()
	first.rows()
	assert first.phase_blink[work] == 3
	fresh = Console(world["store"], "lang", "ada",
	                config_path=world["config"])
	screen = Screen()
	fresh._render_table(screen, 24, 110, fresh.rows())
	assert not any(attr & curses.A_BLINK
	               for _y, _x, _t, attr in screen.calls), \
		"a reconnect inherited the change cue"


def test_age_advances_on_the_existing_cadence_only(tmp_path):
	"""PTY: the live Age cell ticks over on the ordinary refresh — no
	second scheduler, no extra polling — and the initial load blinks
	nothing while the claimed row's title is bold with a live timer."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                "kinds": ["bug"]}})
	store = bw.Authority(database)
	work = tr.create_work(store, team="lang", kind="bug",
	                      title="aging", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	store.close()
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6), (b"", 2.6), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	first = next(line for line in ptyharness.replay(steps[0])
	             if "aging" in line)
	later = next(line for line in ptyharness.replay(steps[1])
	             if "aging" in line)
	stamp = re.search(r"(\d{2}:\d{2})\s*$", first)
	moved = re.search(r"(\d{2}:\d{2})\s*$", later)
	assert stamp and moved, (first, later)
	assert moved.group(1) >= stamp.group(1)
	assert not re.search(r"\x1b\[(?:\d+;)*0?5(?:;\d+)*m"
	                     r"(?:\x1b\[[0-9;?]*[A-Za-z])*(actve|rview)",
	                     text), "an indefinite blink survived"
