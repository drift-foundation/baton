"""W226 (finding-tui-held-duration): Held plus structured
handoff/pickup facts, on W55's MM:SS timer.

Responsibility begins at the committed handoff: canonical JSON exposes
`handoff_at` and the structured `pickup` state (claimed | pending |
overdue | null) — never display glyphs — while the TUI renders the
state-dependent Held field (W65: `>MM:SS` for every open unclaimed
Work, the visible reset to claimed_at at pickup, a constant blank
suffix once claimed) and the Phase pickup prefix. No prefix, suffix,
or elapsed time mutates workflow authority.
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
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	row = row_of(world, work)
	handed = epoch(row["handoff_at"])
	# pending: >MM:SS since the committed handoff (W55 scale)
	assert held_field(row, handed + 90) == ">01:30"
	assert pickup_prefix(row, handed + 90) == ">"
	# W65: crossing six minutes changes NOTHING — unclaimed is the
	# fact, and it was already being stated
	assert held_field(row, handed + 360) == ">06:00"
	assert pickup_prefix(row, handed + 360) == ">"
	# claim: the prefix disappears and the DISPLAYED interval resets to
	# claimed_at — the pickup insight is preserved, not erased
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	row = row_of(world, work)
	assert row["pickup"] == "claimed"
	claimed = epoch(row["claimed_at"])
	assert held_field(row, claimed + 30) == "00:30 "
	assert pickup_prefix(row, claimed + 30) == " "
	# W65: the claimant suffix is a constant blank; silence is not
	# failure and never reaches the display
	assert held_field(row, claimed + 361) == "06:01 "
	# the visible reset is FALSIFIABLE at any handoff-claim distance: a
	# claim two hours after the handoff shows 30 seconds of claim-held,
	# never the handoff interval — which on this scale would be `∞`
	synthetic = {"claimed_at": "2026-08-17T12:00:00Z",
	             "handoff_at": "2026-08-17T10:00:00Z",
	             "heartbeat_at": None}
	at = epoch("2026-08-17T12:00:30Z")
	assert held_field(synthetic, at) == "00:30 ", \
		"claim did not reset the displayed interval to claimed_at"
	# repass starts a NEW pending interval for the new destination
	tr.pass_work(store, work, actor_team="rev", actor="bee",
	             to="lang.bug", comment="back")
	fresh = row_of(world, work)
	assert fresh["pickup"] == "pending"
	assert epoch(fresh["handoff_at"]) >= handed
	assert held_field(fresh, epoch(fresh["handoff_at"]) + 60) == ">01:00"


def test_the_overflow_value_composes_like_any_other_base():
	"""W55 + W65: `∞` is an ordinary base value, not a special-cased
	cell — the unclaimed marker composes with it exactly as with MM:SS,
	and the claimed suffix is the same constant blank. Padding is
	presentation only."""
	at = epoch("2026-08-17T11:40:00Z")          # 100 minutes past 10:00
	silent = {"claimed_at": "2026-08-17T10:00:00Z", "handoff_at": None,
	          "heartbeat_at": "2026-08-17T10:00:00Z"}
	assert held_field(silent, at) == "∞ ", \
		"protocol silence still decorated the overflow value"
	beating = dict(silent, heartbeat_at="2026-08-17T11:39:30Z")
	assert held_field(beating, at) == "∞ ", \
		"a fresh beat rendered differently from a silent one"
	# an unclaimed handoff old enough to overflow keeps the plain
	# unclaimed marker: W65 removed the elapsed-time escalation, so
	# `>∞` is now the reachable long-pending spelling.
	pending = {"claimed_at": None, "heartbeat_at": None,
	           "handoff_at": "2026-08-17T10:00:00Z", "status": "open"}
	assert held_field(pending, at) == ">∞"
	assert pickup_prefix(pending, at) == ">"
	# and the whole field still fits the six-cell budget it shares with
	# every ordinary value
	assert all(len(held_field(row, at)) <= 6
	           for row in (silent, beating, pending))


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
	assert detail["current"]["endpoint"] == "rev.bug"
	assert detail["active"] is None
	# closed Work renders dash and no prefix regardless of history
	tr.claim_work(store, work, actor_team="rev", actor="bee")
	tr.close_work(store, work, actor_team="rev", actor="bee",
	              rationale="done", outcome="satisfying")
	closed = pj.detail(store, work, viewer_team="rev",
	                   viewer_member="bee")
	assert held_field(closed, 0) == "-"
	assert pickup_prefix(closed, 0) == " "


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
