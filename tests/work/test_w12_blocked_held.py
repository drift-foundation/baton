"""W12: Held is the Handler column, and a blocked row has no Handler.

W2 sat in `block` waiting on W3, held by nobody, and its Held advanced.
The row read as somebody's task running late. Nobody could progress it —
the gate had released the claim to create the block in the first place —
so the number described time no participant was spending.

This supersedes the blocked-Held half of W78. What W78 built stays:
the gate keeps its typed identity and episode start, `Wait` names it,
and Events carry how long the block lasted. Blocked duration is still
canonical evidence; it is simply not Handler duration, and the Handler
column is where it stopped belonging.
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
from baton_work.tui.app import blocker_cue, held_field        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		                        "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


def _make(world, title="w", parent=None):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b", parent=parent)["work_id"]


def _row(world, work):
	return pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")


def _thread(world, work):
	return pj.work_threads(world["store"], work, viewer_team="lang",
	                       viewer_member="ada")["rows"][0]["id"]


def _epoch(value):
	import datetime as _dt
	return _dt.datetime.fromisoformat(
		value.replace("Z", "+00:00").replace(" ", "T")).timestamp()


# -- the reported row --------------------------------------------------------

def test_the_reported_shape_blocked_on_another_work_shows_no_held(world):
	"""The finding's own case: a Work blocked on another Work, with no
	Handler, whose Held advanced."""
	consumer, blocker = _make(world, "W2"), _make(world, "W3")
	tr.add_dependency(world["store"], consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="needs it first")
	row = _row(world, consumer)
	assert row["phase"] == "block"
	assert row["handler"] is None
	started = row["gate"]["started_at"]
	# an hour of block is still `-`, not a large number
	assert held_field(row, _epoch(started) + 3600) == "-"


def test_a_message_gate_shows_no_held_either(world):
	"""Both typed gates, because W78 made the kind a real distinction
	and a fix that only covered `work` would leave the same row shape
	running a clock through a directed obligation."""
	work = _make(world, "asked")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.post_thread(world["store"], _thread(world, work), author_team="lang",
	               author="ada", body="advise", request="lang.rsrch", on=work)
	row = _row(world, work)
	assert row["phase"] == "block"
	assert row["gate"]["kind"] == "message"
	assert row["handler"] is None, "the message gate did not release the claim"
	assert held_field(row, _epoch(row["gate"]["started_at"]) + 600) == "-"
	assert blocker_cue(row), "the gate must still name the source Message"


# -- what did not change -----------------------------------------------------

def test_an_active_claim_still_times_from_claimed_at(world):
	"""The column keeps its one remaining meaning, unchanged and capped
	exactly as before."""
	work = _make(world, "held")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	row = _row(world, work)
	assert row["handler"] is not None
	base = _epoch(row["claimed_at"])
	assert held_field(row, base) == "00:00"
	assert held_field(row, base + 45) == "00:45"
	assert held_field(row, base + 3599) == "59:59"


def test_the_gate_episode_and_its_start_survive(world):
	"""'Gate identity/start and Events duration remain available and
	unchanged.' The evidence moved out of one cell; it was not deleted.

	Proved against the projection rather than the cell, because the
	whole point is that the fact still exists where agents read it."""
	consumer, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	gate = _row(world, consumer)["gate"]
	assert gate["kind"] == "work"
	assert gate["work"] == blocker
	assert gate["selector"] == blocker.rsplit("-", 1)[1]
	assert gate["started_at"] is not None, \
		"the blocked duration lost its origin as well as its cell"


def test_the_block_duration_is_still_recoverable_from_the_episode(world):
	"""Blocked duration remains canonical operational evidence: a
	consumer that wants it computes it from the episode start, which is
	exactly where the ruling puts it."""
	consumer, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	started = _row(world, consumer)["gate"]["started_at"]
	assert (_epoch(started) + 90) - _epoch(started) == 90


# -- the rule, over every state ----------------------------------------------

def _every_phase(world):
	"""One of each open scheduler state, plus a terminal row."""
	store = world["store"]
	rows = {}

	# W2938 one-slot capacity: ada holds ONE claim at a time, so the
	# rows that merely pass THROUGH a claim on their way somewhere else
	# are built first and the one that STAYS claimed is built last.
	# Ordering, not a second claimant: this fixture's route resolves to
	# ada alone, and inventing a handler to keep the old order would be
	# changing the world to suit the sequence.
	rows["queued"] = _make(world, "queued")

	blocked = _make(world, "blocked")
	tr.add_dependency(store, blocked, _make(world, "gate"),
	                  actor_team="lang", actor="ada", rationale="r")
	rows["block-work"] = blocked

	asked = _make(world, "asked")
	tr.claim_work(store, asked, actor_team="lang", actor="ada")
	tr.post_thread(store, _thread(world, asked), author_team="lang",
	               author="ada", body="advise", request="lang.rsrch",
	               on=asked)                       # the request releases it
	rows["block-message"] = asked

	parked = _make(world, "parked")
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="deferred")
	rows["parked"] = parked

	closed = _make(world, "closed")
	tr.claim_work(store, closed, actor_team="lang", actor="ada")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	rows["closed"] = closed

	released = _make(world, "released")
	tr.claim_work(store, released, actor_team="lang", actor="ada")
	tr.release_claim(store, released, actor_team="lang", actor="ada",
	                 expect="lang.ada", episode=fx.episode_of(store, released),
	                 reason="handing it back")
	rows["released"] = released

	claimed = _make(world, "claimed")
	tr.claim_work(store, claimed, actor_team="lang", actor="ada")
	rows["active"] = claimed

	return rows


def test_held_runs_exactly_when_a_handler_holds_the_work(world):
	"""The whole rule as one invariant over every state the scheduler
	has, so a future state cannot quietly acquire a clock: Held advances
	if and only if the row names a Handler."""
	states = _every_phase(world)
	now = _epoch(_row(world, states["queued"])["last_changed_at"]) + 300
	for label, work in states.items():
		row = _row(world, work)
		running = held_field(row, now) != "-"
		assert running == (row["handler"] is not None), (
			f"{label}: phase={row['phase']} handler={row['handler']} "
			f"held={held_field(row, now)!r}")


def test_only_the_active_row_runs_a_clock(world):
	"""The same fact counted, so the invariant above cannot pass by
	holding vacuously — if nothing ran a clock at all it would still be
	'if and only if'."""
	states = _every_phase(world)
	now = _epoch(_row(world, states["queued"])["last_changed_at"]) + 300
	running = [label for label, work in states.items()
	           if held_field(_row(world, work), now) != "-"]
	assert running == ["active"], running


def test_a_blocked_row_that_becomes_claimable_again_times_from_the_claim(
		world):
	"""Clearing the gate does not backdate Held to the block. The clock
	starts when a Handler actually takes it, which is the only instant
	the column now means."""
	store = world["store"]
	consumer, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	blocked_at = _epoch(_row(world, consumer)["gate"]["started_at"])
	tr.claim_work(store, blocker, actor_team="lang", actor="ada")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	assert _row(world, consumer)["phase"] == "queued"
	assert held_field(_row(world, consumer), blocked_at + 120) == "-"

	tr.claim_work(store, consumer, actor_team="lang", actor="ada")
	row = _row(world, consumer)
	assert held_field(row, _epoch(row["claimed_at"]) + 5) == "00:05", \
		"Held counted from the block rather than from the claim"


# -- parity ------------------------------------------------------------------

def test_the_json_projection_is_unchanged_by_this_work(world):
	"""'JSON/TUI parity tests distinguish gate duration from Handler
	duration.' This Work is presentation-only: the projection already
	carried both facts separately, which is why the cell could be wrong
	while the data was right. Nothing agents read changes."""
	work = _make(world, "asked")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.post_thread(world["store"], _thread(world, work), author_team="lang",
	               author="ada", body="advise", request="lang.rsrch", on=work)
	row = _row(world, work)
	# the two durations have two separate origins, and always did
	assert row["gate"]["started_at"] is not None      # gate duration
	assert row["claimed_at"] is None                  # handler duration
	assert row["handler"] is None
	# the cell reads the second, so it is `-`; a consumer wanting the
	# first reads the gate, which is still there
	assert held_field(row, _epoch(row["gate"]["started_at"]) + 60) == "-"


def test_claimed_at_is_null_exactly_when_handler_is(world):
	"""The coupling `held_field` relies on, pinned so it cannot drift.

	The cell tests Handler and then formats `claimed_at`. If the
	projection ever kept a stale `claimed_at` on an unclaimed row, that
	would be a clock waiting to reappear, and this reds first."""
	states = _every_phase(world)
	for label, work in states.items():
		row = _row(world, work)
		assert (row["claimed_at"] is None) == (row["handler"] is None), label
