"""W65 (finding-unclaimed-work-cue): unclaimed is the primary cue.

The live defect: W2 painted an overdue `!` while sitting in review.
Canonical detail said it was unclaimed, dependency-blocked and not
ready — adding its blockers had correctly released the reviewer's
claim — yet the pickup projection went on aging the old handoff and
escalating, even though authority rules made a new claim impossible.

The ruling: the operational signal is whether open Work has a
claimant, because unclaimed means nobody is executing it. `>` states
that fact independently of elapsed time; readiness, wait and park are
separate structured facts explaining why unclaimed Work may not be
claimable. Both six-minute `!` escalations are gone — a claimed agent
can be alive and busy inside one model turn with no chance to beat.
"""

from __future__ import annotations

import datetime as _dt
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import held_field, pickup_prefix      # noqa: E402
import fixtures as fx                                         # noqa: E402

SIX_MINUTES = 360


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "grace": ["impl"]},
		          "kinds": ["bug"]},
		 "rev": {"members": {"bee": ["rview"]}, "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "grace"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield {"config": config, "store": store}
	store.close()


def make(world, title="handed"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def row_of(world, work_id):
	for row in pj.home(world["store"], viewer_team="lang",
	                   viewer_member="ada")["rows"]:
		if row["id"] == work_id:
			return row
	for row in pj.home(world["store"], viewer_team="rev",
	                   viewer_member="bee")["rows"]:
		if row["id"] == work_id:
			return row
	raise AssertionError(f"{work_id} not visible")


def epoch(ts):
	return _dt.datetime.fromisoformat(
		ts.replace("Z", "+00:00").replace(" ", "T")).timestamp()


def test_every_open_unclaimed_state_carries_the_marker(world):
	"""The full ruled matrix. Each row proves the marker from its OWN
	state, not from how long it has been in it."""
	store = world["store"]
	now = epoch("2026-08-17T12:00:00Z")

	# ready / unclaimed / never passed — no timer origin, still unclaimed
	fresh = row_of(world, make(world, "ready"))
	assert pickup_prefix(fresh, now) == ">"
	assert held_field(fresh, now) == ">-", \
		"a born unclaimed Work hid the fact behind a missing timer"

	# passed / unclaimed
	passed_id = make(world, "passed")
	tr.pass_work(store, passed_id, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	passed = row_of(world, passed_id)
	handed = epoch(passed["handoff_at"])
	assert pickup_prefix(passed, handed + 5) == ">"
	assert held_field(passed, handed + 5) == ">00:05"

	# blocked / unclaimed — the exact W2 shape
	blocked_id = make(world, "blocked")
	blocker = make(world, "blocker")
	tr.pass_work(store, blocked_id, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	tr.add_dependency(store, blocked_id, blocker, actor_team="rev",
	                  actor="bee", rationale="test dependency")
	blocked = row_of(world, blocked_id)
	assert blocked["ready"] is False
	assert pickup_prefix(blocked, now) == ">", \
		"dependency-blocked Work stopped stating that it is unclaimed"

	# waiting and parked stay unclaimed too
	waiting_id = make(world, "waiting")
	waiting_blocker = make(world, "waiting blocker")
	tr.pass_work(store, waiting_id, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	tr.add_dependency(store, waiting_id, waiting_blocker,
	                  actor_team="rev", actor="bee", rationale="test dependency")
	tr.set_phase(store, waiting_id, actor_team="rev", actor="bee",
	             phase="waiting", wait="gates")
	waiting = row_of(world, waiting_id)
	assert waiting["phase"] == "waiting" and waiting["ready"] is False
	assert pickup_prefix(waiting, now) == ">"
	assert waiting["pickup"] == "pending", \
		"waiting Work with a real handoff claimed an overdue pickup"
	parked_id = make(world, "parked")
	tr.set_phase(store, parked_id, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert pickup_prefix(row_of(world, parked_id), now) == ">"

	# claimed loses the marker; released regains it
	claimed_id = make(world, "claimed")
	tr.claim_work(store, claimed_id, actor_team="lang", actor="ada")
	claimed = row_of(world, claimed_id)
	assert pickup_prefix(claimed, now) == " "
	assert held_field(claimed, epoch(claimed["claimed_at"]) + 5) == "00:05 "
	tr.release_claim(store, claimed_id, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="cycling")
	assert pickup_prefix(row_of(world, claimed_id), now) == ">", \
		"a released claim did not restore the unclaimed marker"

	# terminal Work has no execution claim and no marker
	done = make(world, "done")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	closed = row_of(world, done)
	assert pickup_prefix(closed, now) == " "
	assert held_field(closed, now) == "-"


def test_crossing_six_minutes_changes_nothing(world):
	"""The escalation is gone in BOTH directions: an unclaimed row keeps
	its plain marker, and a claimed row keeps its blank suffix."""
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	row = row_of(world, work)
	handed = epoch(row["handoff_at"])
	for offset in (0, SIX_MINUTES - 1, SIX_MINUTES, SIX_MINUTES * 100):
		assert pickup_prefix(row, handed + offset) == ">", \
			f"the unclaimed marker changed at +{offset}s"
		assert "!" not in held_field(row, handed + offset), \
			f"an alert appeared at +{offset}s"
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	held = row_of(world, work)
	claimed = epoch(held["claimed_at"])
	for offset in (0, SIX_MINUTES - 1, SIX_MINUTES, SIX_MINUTES * 100):
		cell = held_field(held, claimed + offset)
		assert cell.endswith(" ") and "!" not in cell, \
			f"a claimed row alerted at +{offset}s: {cell!r}"


def test_overdue_never_describes_unclaimable_work(world):
	"""The projection half of the ruling. `overdue` asserts somebody
	owes a pickup, so it may only describe Work a pickup is possible
	on — the W2 defect was aging a handoff the authority had already
	made unclaimable."""
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	handed = epoch(row_of(world, work)["handoff_at"])

	def at(seconds):
		store.clock = lambda: _dt.datetime.fromtimestamp(
			handed + seconds,
			tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
		return row_of(world, work)

	assert at(5)["pickup"] == "pending"
	# a genuine ready unclaimed pickup DOES go overdue
	assert at(SIX_MINUTES + 1)["pickup"] == "overdue"
	# now block it: the claim becomes impossible, so the obligation ends
	blocker = make(world, "blocker")
	tr.add_dependency(store, work, blocker, actor_team="rev",
	                  actor="bee", rationale="test dependency")
	blocked = at(SIX_MINUTES * 10)
	assert blocked["ready"] is False
	assert blocked["pickup"] == "pending", \
		"dependency-blocked Work still claimed an overdue pickup " \
		"obligation nobody could discharge"
	# and it recovers once the blocker closes
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert at(SIX_MINUTES * 10)["pickup"] == "overdue"
	# parked and waiting are unclaimable for the same reason
	tr.set_phase(store, work, actor_team="rev", actor="bee",
	             phase="parked", reason="later")
	assert at(SIX_MINUTES * 10)["pickup"] == "pending"


def test_json_carries_facts_and_no_glyph(world):
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	row = row_of(world, work)
	blob = _json.dumps(row)
	assert ">" not in blob and "!" not in blob, \
		"a display glyph reached canonical JSON"
	for field in ("pickup", "handoff_at", "ready", "phase", "current"):
		assert field in row, f"{field} stopped being a structured fact"
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	tr.heartbeat(store, work, actor_team="rev", actor="bee")
	held = row_of(world, work)
	assert held["heartbeat_at"] is not None, \
		"heartbeat diagnostics were removed along with the glyph"
	assert held["pickup"] == "claimed"
