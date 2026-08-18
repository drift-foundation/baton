"""W226 (finding-tui-held-duration): Held plus structured
handoff/pickup facts, on W55's MM:SS timer.

Responsibility begins at the committed handoff: canonical JSON exposes
`handoff_at` and the structured `pickup` state (claimed | pending |
overdue | null) — never display glyphs — while the TUI renders the
state-dependent Held field.

W65 marked every open unclaimed row `>MM:SS` here and prefixed Phase to
match. W15 SUPERSEDED that presentation: projection 8 makes `Current`
the exact claimant, blank when nobody holds the Work, so the marker
repeated a fact the row already stated. Held is now a bare timer —
`MM:SS` from `claimed_at` while claimed, from the handoff while
unclaimed, `-` with no origin, the cap otherwise — and `Current` is
what distinguishes the two intervals.

The timer ORIGINS below are unchanged by that supersession, and are the
substance of this suite. No timer, marker, or elapsed value has ever
mutated workflow authority.
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
from baton_work.tui.app import held_field                    # noqa: E402
import fixtures as fx                                         # noqa: E402


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


def make(world):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title="handed", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def row_of(world, work_id):
	rows = pj.home(world["store"], viewer_team="rev",
	               viewer_member="bee")["rows"]
	mine = pj.home(world["store"], viewer_team="lang",
	               viewer_member="ada")["rows"]
	for row in list(rows) + list(mine):
		if row["id"] == work_id:
			return row
	raise AssertionError(f"{work_id} not visible")


def epoch(ts):
	return _dt.datetime.fromisoformat(
		ts.replace("Z", "+00:00").replace(" ", "T")).timestamp()


def test_json_exposes_structured_handoff_facts_without_glyphs(world):
	store = world["store"]
	work = make(world)
	row = row_of(world, work)
	# born, never passed, unclaimed: no handoff responsibility yet
	assert row["handoff_at"] is None and row["pickup"] is None
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	row = row_of(world, work)
	assert row["handoff_at"] is not None
	assert row["pickup"] == "pending"
	# facts, never glyphs
	assert ">" not in _json.dumps({k: row[k] for k in
	                               ("handoff_at", "pickup")})
	# six minutes later the SNAPSHOT states overdue
	store.clock = lambda: _dt.datetime.fromtimestamp(
		epoch(row["handoff_at"]) + 361,
		tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
	assert row_of(world, work)["pickup"] == "overdue"


def test_the_held_field_walks_the_ruled_states(world):
	"""W78 supersedes the handoff origin walked here before.

	Held now measures the two intervals that are real operational time,
	and each is explainable from its own row: `active` since the claim,
	with `Handler` naming who holds it; `block` since the displayed
	gate's episode started, with `Wait` naming that gate. Everything
	else is `-`.

	The retired rule ran a clock on an unclaimed handoff, which is the
	defect this Work exists to remove: two unclaimed rows in the same
	phase ran different clocks because one happened to carry a
	historical `handoff_at`, and nothing on either row explained the
	difference."""
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	row = row_of(world, work)
	handed = epoch(row["handoff_at"])
	# queued after a handoff: no timer at all, however old the handoff
	assert row["phase"] == "queued"
	assert held_field(row, handed + 90) == "-", \
		"an unclaimed handoff started a clock the row cannot explain"
	assert held_field(row, handed + 36000) == "-"
	# and the handoff instant is still projected — it is history, not
	# a timer origin
	assert row["handoff_at"] is not None and row["pickup"] == "pending"

	# claim: MM:SS since claimed_at
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	row = row_of(world, work)
	assert row["pickup"] == "claimed"
	claimed = epoch(row["claimed_at"])
	assert held_field(row, claimed + 30) == "00:30"
	# W65: silence is not failure and never reaches the display
	assert held_field(row, claimed + 361) == "06:01"
	# falsifiable at any handoff-claim distance: a claim two hours after
	# the handoff shows the claim interval, never the handoff one
	synthetic = {"claimed_at": "2026-08-17T12:00:00Z",
	             "handoff_at": "2026-08-17T10:00:00Z",
	             "heartbeat_at": None}
	at = epoch("2026-08-17T12:00:30Z")
	assert held_field(synthetic, at) == "00:30", \
		"claim did not reset the displayed interval to claimed_at"

	# block: MM:SS since the DISPLAYED gate's episode start
	blocker = make(world)
	tr.add_dependency(store, work, blocker, actor_team="rev", actor="bee",
	                  rationale="needs the gate first")
	blocked = row_of(world, work)
	assert blocked["phase"] == "block"
	started = epoch(blocked["gate"]["started_at"])
	assert held_field(blocked, started + 45) == "00:45"
	assert blocked["claimed_at"] is None, \
		"the late gate did not release the claim"

	# parked: no timer
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	tr.set_phase(store, work, actor_team="rev", actor="bee",
	             phase="parked", reason="deferred by the operator")
	parked = row_of(world, work)
	assert parked["phase"] == "parked"
	assert held_field(parked, epoch(parked["last_changed_at"]) + 90) == "-"


def test_the_overflow_value_composes_like_any_other_base():
	"""W55: the overflow is an ordinary base value, not a special-cased
	cell. Under W15 it composes with nothing at all — claimed and
	unclaimed rows both render it bare, which is the supersession's
	point. Padding is presentation only."""
	at = epoch("2026-08-17T11:40:00Z")          # 100 minutes past 10:00
	silent = {"claimed_at": "2026-08-17T10:00:00Z", "handoff_at": None,
	          "heartbeat_at": "2026-08-17T10:00:00Z"}
	assert held_field(silent, at) == "∞", \
		"protocol silence still decorated the overflow value"
	beating = dict(silent, heartbeat_at="2026-08-17T11:39:30Z")
	assert held_field(beating, at) == "∞", \
		"a fresh beat rendered differently from a silent one"
	# a BLOCKED row old enough to overflow renders the SAME bare
	# overflow as a claimed one: W65 removed the elapsed-time
	# escalation, W15 removed the marker, and W78 made the blocked
	# interval a first-class one — so `∞` is the one spelling, and
	# `Handler`/`Wait` say which kind of interval it is.
	# (An unclaimed handoff no longer runs a clock at all; that case is
	# walked in the ruled-states test above.)
	blocked = {"claimed_at": None, "heartbeat_at": None,
	           "handoff_at": "2026-08-17T09:00:00Z", "status": "open",
	           "gate": {"kind": "work", "selector": "W4",
	                    "started_at": "2026-08-17T10:00:00Z"}}
	assert held_field(blocked, at) == "∞"
	# and the whole field still fits the six-cell budget it shares with
	# every ordinary value
	assert all(len(held_field(row, at)) <= 6
	           for row in (silent, beating, blocked))


def test_terminal_work_and_authority_are_untouched(world):
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	before = store.last_seq()
	# elapsed time and projections mutate NOTHING
	store.clock = lambda: "2099-01-01T00:00:00Z"
	row = row_of(world, work)
	assert row["pickup"] == "overdue"
	assert store.last_seq() == before, \
		"an overdue pickup wrote to the authority"
	detail = pj.detail(store, work, viewer_team="rev",
	                   viewer_member="bee")
	assert detail["route"]["endpoint"] == "rev.bug"
	assert detail["handler"] is None
	# closed Work renders dash and no prefix regardless of history
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	tr.close_work(store, work, actor_team="rev", actor="bee",
	              rationale="done", outcome="satisfying")
	closed = pj.detail(store, work, viewer_team="rev",
	                   viewer_member="bee")
	assert held_field(closed, 0) == "-"


def test_tree_handoff_reads_stay_constant_as_the_window_grows(world):
	"""W226 R1: the tree batches _handoffs once per window — the
	handoff-query count must not grow with the visible Work set —
	and derives every row against ONE sampled instant."""
	store = world["store"]
	def tree_pass_queries():
		counted = {"n": 0}
		def trace(statement):
			if "kind IN ('pass', 'return')" in statement:
				counted["n"] += 1
		store.conn.set_trace_callback(trace)
		try:
			pj.tree(store, viewer_team="lang", viewer_member="ada")
		finally:
			store.conn.set_trace_callback(None)
		return counted["n"]
	make(world)
	small = tree_pass_queries()
	for _ in range(6):
		make(world)
	large = tree_pass_queries()
	assert small == large == 1, \
		f"handoff reads grew with the window: {small} -> {large}"


def test_terminal_work_projects_no_pickup_alarm(world):
	"""W226 R2: closing handed-off Work retires the pickup obligation —
	pickup is None in detail AND window projections even far past the
	six-minute threshold — while handoff_at remains history."""
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	tr.close_work(store, work, actor_team="rev", actor="bee",
	              rationale="done", outcome="satisfying")
	store.clock = lambda: "2099-01-01T00:00:00Z"
	detail = pj.detail(store, work, viewer_team="rev",
	                   viewer_member="bee")
	assert detail["pickup"] is None, detail["pickup"]
	assert detail["handoff_at"] is not None, "history was deleted"
	rows = pj.home(store, viewer_team="lang", viewer_member="ada",
	               work_filter={"status": "closed"})["rows"]
	closed_row = next(row for row in rows if row["id"] == work)
	assert closed_row["pickup"] is None
	assert closed_row["handoff_at"] is not None
