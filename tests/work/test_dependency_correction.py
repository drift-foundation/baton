"""A mistaken live dependency is correctable without falsifying either Work."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	config, database = fx.build_instance(str(tmp_path), spec)
	with bw.Authority(database) as store:
		yield store, config


def _create(store, team="lang", member="ada", title="work"):
	return tr.create_work(store, team=team, kind="bug", title=title,
	                      origin="self-initiated",
	                      classification="design-choice", author=member,
	                      body="contract")["work_id"]


def _ready(store, work):
	return store.conn.execute(
		"SELECT ready FROM work WHERE id=?", (work,)).fetchone()["ready"]


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


def test_current_handler_corrects_one_live_edge_and_audit_retains_both(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl", title="not required")
	added = tr.add_dependency(store, work, blocker,
	                          actor_team="lang", actor="ada",
	                          rationale="the provider must finish first")
	assert _ready(store, work) == 0
	assert "remove_dependency" in pj.detail(
		store, work, viewer_team="lang",
		viewer_member="ada")["available_transitions"]
	assert not [action for action in pj.participant_actions(
		store, viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "work" and action["work"] == work]

	removed = tr.remove_dependency(
		store, work, blocker, actor_team="lang", actor="ada",
		rationale="acceptance boundary corrected")
	assert _ready(store, work) == 1
	assert "remove_dependency" not in pj.detail(
		store, work, viewer_team="lang",
		viewer_member="ada")["available_transitions"]
	assert len([action for action in pj.participant_actions(
		store, viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "work" and action["work"] == work]) == 1
	assert store.conn.execute(
		"SELECT 1 FROM edges WHERE work=? AND blocker=?",
		(work, blocker)).fetchone() is None
	events = {entry["seq"]: entry for entry in store.events()}
	assert events[added["seq"]]["kind"] == "add_dependency"
	assert events[added["seq"]]["payload"]["rationale"] == \
		"the provider must finish first"
	assert events[removed["seq"]]["kind"] == "remove_dependency"
	assert events[removed["seq"]]["payload"]["created_seq"] == added["seq"]
	assert events[removed["seq"]]["payload"]["rationale"] == \
		"acceptance boundary corrected"


def test_removing_one_of_two_live_gates_does_not_make_work_ready(world):
	store, _config = world
	work = _create(store)
	first = _create(store, team="push", member="sl", title="first")
	second = _create(store, team="push", member="sl", title="second")
	tr.add_dependency(store, work, first, actor_team="lang", actor="ada",
	                  rationale="first gate")
	tr.add_dependency(store, work, second, actor_team="lang", actor="ada",
	                  rationale="second gate")
	tr.remove_dependency(store, work, first, actor_team="lang", actor="ada",
	                     rationale="first edge was mistaken")
	assert _ready(store, work) == 0
	assert store.conn.execute(
		"SELECT blocker FROM edges WHERE work=?", (work,)).fetchone()["blocker"] \
		== second


def test_correcting_the_last_gate_wakes_blocked_work_in_the_same_transaction(
		world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl", title="mistaken gate")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="suspected provider dependency")

	removed = tr.remove_dependency(
		store, work, blocker, actor_team="lang", actor="ada",
		rationale="evidence proves this edge was mistaken")
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["ready"] is True
	assert detail["phase"] == "queued" and detail["gate"] is None
	wakes = [event for event in store.events()
	         if event["kind"] == "wake" and
	         event["payload"]["work"] == work]
	assert len(wakes) == 1
	assert wakes[0]["seq"] == removed["seq"] + 1, \
		"the correction and its wake did not commit together"
	assert wakes[0]["actor"] == "lang.ada"
	# W78: the wake names the gate that CLEARED, typed and located,
	# rather than the condition kind that used to stand in for it.
	assert wakes[0]["payload"]["cleared_gate"] == {
		"kind": "work", "work": blocker, "obligation": None}
	actions = pj.participant_actions(
		store, viewer_team="lang", viewer_member="ada")["actions"]
	assert len([action for action in actions
	            if action["kind"] == "work" and
	            action["work"] == work]) == 1, \
		"the same-transaction wake minted no actionable episode"


def test_correcting_a_nonfinal_gate_leaves_blocked_work_asleep(world):
	store, _config = world
	work = _create(store)
	first = _create(store, team="push", member="sl", title="mistaken")
	second = _create(store, team="push", member="sl", title="still required")
	tr.add_dependency(store, work, first, actor_team="lang", actor="ada",
	                  rationale="first gate")
	tr.add_dependency(store, work, second, actor_team="lang", actor="ada",
	                  rationale="second gate")

	tr.remove_dependency(store, work, first, actor_team="lang", actor="ada",
	                     rationale="only the first edge was mistaken")
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["ready"] is False
	assert detail["phase"] == "block"
	assert detail["gate"]["kind"] == "work"
	assert not [event for event in store.events()
	            if event["kind"] == "wake" and
	            event["payload"]["work"] == work]


def test_wrong_handler_empty_reason_and_absent_or_historical_edges_refuse(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	with pytest.raises(bw.WorkError, match="rationale cannot be empty"):
		tr.add_dependency(store, work, blocker, actor_team="lang",
		                  actor="ada", rationale="  ")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="the gate")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="resolved handler"):
		tr.remove_dependency(store, work, blocker,
		                     actor_team="push", actor="sl", rationale="wrong")
	with pytest.raises(bw.WorkError, match="cannot be empty"):
		tr.remove_dependency(store, work, blocker,
		                     actor_team="lang", actor="ada", rationale="  ")
	assert store.last_seq() == before

	missing = _create(store, team="push", member="sl", title="missing")
	with pytest.raises(bw.WorkError, match="no live dependency"):
		tr.remove_dependency(store, work, missing,
		                     actor_team="lang", actor="ada", rationale="wrong")
	tr.close_work(store, blocker, actor_team="push", actor="sl",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="historical"):
		tr.remove_dependency(store, work, blocker,
		                     actor_team="lang", actor="ada", rationale="late")


def test_exact_retry_replays_and_conflicting_retry_refuses(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="the gate")
	first = tr.remove_dependency(
		store, work, blocker, actor_team="lang", actor="ada",
		rationale="not part of this gate", op_id="edge-correction-1")
	again = tr.remove_dependency(
		store, work, blocker, actor_team="lang", actor="ada",
		rationale="not part of this gate", op_id="edge-correction-1")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"
	with pytest.raises(bw.WorkError, match="conflicting reuse"):
		tr.remove_dependency(
			store, work, blocker, actor_team="lang", actor="ada",
			rationale="different", op_id="edge-correction-1")


def test_stale_correction_loses_to_another_correction_inside_transaction(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="the gate")
	_interleave(store, lambda: tr.remove_dependency(
		store, work, blocker, actor_team="lang", actor="ada",
		rationale="winner"))
	with pytest.raises(bw.WorkError, match="no live dependency"):
		tr.remove_dependency(store, work, blocker,
		                     actor_team="lang", actor="ada",
		                     rationale="stale loser")
	assert [event["kind"] for event in store.events()].count(
		"remove_dependency") == 1


def test_cli_exposes_short_selectors_and_required_rationale(world, capsys):
	store, config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="the gate")
	assert cli.main(["--config", config, "--participant", "lang.ada",
	                 "unblock", f"work=W{work.rsplit('W', 1)[1]}",
	                 f"on=W{blocker.rsplit('W', 1)[1]}",
	                 "rationale=wrong gate", "op-id=cli-unblock-1"]) == 0
	result = json.loads(capsys.readouterr().out)["result"]
	assert result["kind"] == "remove_dependency"
	assert _ready(store, work) == 1
	assert "rationale=" in cli.render_help("unblock")


def test_cli_refuses_block_and_unblock_without_rationale_before_dispatch(
		world, capsys):
	_store, config = world
	for verb in ("block", "unblock"):
		assert cli.main(["--config", config, "--participant", "lang.ada",
		                 verb, "work=W1", "on=W2"]) == 1
		assert "missing required rationale=" in \
			json.loads(capsys.readouterr().err)["error"]
