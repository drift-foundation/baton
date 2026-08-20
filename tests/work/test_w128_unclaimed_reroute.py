"""W128: unclaimed Work is the owning team's to reroute.

`work/records/2026/08/finding-unclaimed-work-reroute/`. W30 sat open,
queued and unclaimed on the `impl2` alternate while the agent that route
resolves to was not taking it. Canonical detail offered the owning-team
reviewer only `prioritize`: `pass` belongs to the resolved route handler,
so the only way to move untouched Work was to wake the very runner the
operator was trying to route around.

That is a dependency in the wrong direction. It strands Work exactly
when the runner is offline, overloaded or broken — which is when
rerouting is needed at all.

So the authority for this one correction is OWNERSHIP rather than route
eligibility: any active member of the owning team may correct where
unclaimed Work is offered. Route eligibility still decides who
EXECUTES, claimed Work is never rerouted underneath its handler, and the
race between a claim and a reroute is decided under the write lock with
the loser changing nothing.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import cli as _cli                             # noqa: E402
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402


def document(generation=1, alternates=("alt",)):
	"""`lang.impl` offers an alternate route to a DIFFERENT member, and
	`lang.rev` is a second endpoint — the three destinations the
	acceptance boundary asks about."""
	base = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "impl", "rev"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	team = base["teams"]["lang"]
	team["routes"]["main"] = {"role": "dev", "handlers": ["ada"]}
	team["routes"]["alt"] = {"role": "dev", "handlers": ["grace"]}
	team["kinds"]["impl"] = {"display": "Impl", "route": "main",
	                         "alternates": list(alternates)}
	team["kinds"]["rev"] = {"display": "Rev", "route": "alt"}
	base["generation"] = generation
	return base


@pytest.fixture()
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document(), handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def make(world, kind="impl", title="the stranded work"):
	return tr.create_work(world["store"], team="lang", kind=kind,
	                      title=title, origin="self-initiated",
	                      classification="design-choice", author="ada",
	                      body="the opener")["work_id"]


def onto_alternate(world, work):
	"""Put the Work where this record's whole premise starts: open,
	queued and UNCLAIMED on the alternate route.

	W2571 makes that arrival a claimant's handoff — ada claims it and
	passes it, and the pass releases the claim on the way out, which is
	exactly the stranded state W128 exists to correct. `fx.hand_off`
	states the claim once and says why."""
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	            to="lang.impl", route="alt",
	            comment="offered to the alternate route")


def reroute(world, work, to="lang.impl", route=None,
            reason="the alternate route's runner is not taking it",
            member="ada", team="lang", **extra):
	return tr.reroute_work(world["store"], work, actor_team=team,
	                       actor=member, to=to, route=route,
	                       reason=reason, **extra)


def route_of(world, work, member="ada", team="lang"):
	return pj.detail(world["store"], work, viewer_team=team,
	                 viewer_member=member)["route"]


def work_row(world, work):
	return dict(world["store"].conn.execute(
		"SELECT * FROM work WHERE id=?", (work,)).fetchone())


# -- the motivating case -----------------------------------------------------

def test_the_owning_team_moves_unclaimed_work_off_an_alternate(world):
	"""W30's situation exactly: unclaimed on the alternate, and the
	operator is not made to wake the runner they are routing around."""
	work = make(world)
	onto_alternate(world, work)
	assert route_of(world, work)["handlers"] == ["grace"]
	result = reroute(world, work)
	assert result["to"] == "lang.impl"
	assert result["route"] == "main"
	assert result["from"] == {"endpoint": "lang.impl", "route": "alt"}
	assert route_of(world, work)["handlers"] == ["ada"], \
		"the Work is still offered to the runner it was routed away from"


def test_the_primary_can_be_rerouted_onto_an_alternate(world):
	work = make(world)
	reroute(world, work, route="alt",
	        reason="claude is saturated; try the backup route")
	live = route_of(world, work)
	assert live["endpoint"] == "lang.impl" and live["route"] == "alt"
	assert live["handlers"] == ["grace"]


def test_a_different_endpoint_is_a_reroute_too(world):
	work = make(world)
	reroute(world, work, to="lang.rev",
	        reason="this is review work, not implementation")
	live = route_of(world, work)
	assert live["endpoint"] == "lang.rev"


def test_the_rerouted_work_keeps_everything_else(world):
	"""'Preserve the Work identity, dossier binding, messages,
	dependencies, containment, priority, classification, and planned
	Next.'

	The row comparison is the strongest form of that: every column but
	the selected route is asserted byte-identical, which covers the
	binding revision, the parent, the counters and everything a later
	column would add without this test needing to learn about it."""
	store = world["store"]
	parent = make(world, title="the parent")
	work = tr.create_work(store, team="lang", kind="impl",
	                      title="the child", origin="self-initiated",
	                      classification="suspected-defect",
	                      author="ada", body="opener",
	                      parent=parent)["work_id"]
	blocker = make(world, title="the blocker")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="needs the blocker first")
	tr.prioritize(store, work, actor_team="lang", actor="ada",
	              priority="high")
	before = work_row(world, work)
	reroute(world, work, route="alt", reason="moving it")
	after = work_row(world, work)
	for column, value in before.items():
		if column in ("route_selected", "last_change_seq",
		              "last_changed_at", "episode_seq"):
			continue
		assert after[column] == value, column
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["priority"] == "high"
	assert detail["classification"] == "suspected-defect"
	assert detail["links"]["parent"]["id"] == parent
	assert [entry["id"] for entry in detail["links"]["blocked_by"]] == \
		[blocker]


def test_a_planned_next_is_not_this_corrections_to_make(world):
	work = make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	            to="lang.impl", route="alt", set_next="lang.rev",
	            comment="over, and back to review after")
	reroute(world, work, reason="taking it back")
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["next"]["endpoint"] == "lang.rev", \
		"the reroute silently dropped the planned Next"


# -- refusals ----------------------------------------------------------------

def test_a_no_op_reroute_refuses(world):
	work = make(world)
	with pytest.raises(bw.WorkError, match="already at"):
		reroute(world, work, reason="nowhere to go")
	# and selecting the route it is already on is the same no-op
	onto_alternate(world, work)
	with pytest.raises(bw.WorkError, match="already at"):
		reroute(world, work, route="alt", reason="still nowhere")


def test_another_teams_unclaimed_work_stays_theirs(world):
	"""'Cross-team participants cannot reroute another team's Work
	merely because it is unclaimed.'"""
	work = make(world)
	onto_alternate(world, work)
	with pytest.raises(bw.WorkError, match="owned by lang"):
		reroute(world, work, member="sl", team="push",
		        reason="I would like this")
	assert route_of(world, work)["route"] == "alt", \
		"the refused reroute moved it anyway"


def test_terminal_work_has_no_route_to_correct(world):
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	with pytest.raises(bw.WorkError, match="terminal work"):
		reroute(world, work, route="alt", reason="one more move")


def test_claimed_work_is_never_rerouted_under_its_handler(world):
	work = make(world)
	onto_alternate(world, work)
	tr.claim_work(world["store"], work, actor_team="lang",
	              actor="grace")
	with pytest.raises(bw.WorkError, match="claimed by lang.grace"):
		reroute(world, work, reason="taking it back anyway")
	assert route_of(world, work)["route"] == "alt"
	# the stated alternatives both work
	tr.release_claim(world["store"], work, actor_team="lang",
	                 actor="grace", expect="lang.grace",
	                 reason="handing it back")
	reroute(world, work, reason="now that nobody holds it")
	assert route_of(world, work)["route"] == "main"


def test_a_reason_is_required(world):
	work = make(world)
	for empty in ("", "   ", None):
		with pytest.raises(bw.WorkError, match="state reason="):
			reroute(world, work, route="alt", reason=empty)


def test_a_withdrawn_route_refuses_rather_than_routing_elsewhere(world):
	"""The selection resolves INSIDE the lock, so a regen that removed
	the alternate refuses instead of quietly falling back to the
	default — which would send the Work to a different agent than the
	operator chose."""
	work = make(world)
	with open(world["config"], "w", encoding="utf-8") as handle:
		_json.dump(document(generation=2, alternates=()), handle,
		           indent=2, sort_keys=True)
	lc.accept_config(world["config"], actor="lang.ada")
	with pytest.raises(bw.WorkError, match="does not offer route"):
		reroute(world, work, route="alt", reason="to the alternate")
	assert route_of(world, work)["route"] == "main", \
		"a refused selection moved the Work anyway"


# -- the claim/reroute race --------------------------------------------------

def test_a_claim_that_commits_first_makes_the_reroute_refuse(world):
	work = make(world)
	onto_alternate(world, work)
	tr.claim_work(world["store"], work, actor_team="lang",
	              actor="grace")
	before = work_row(world, work)
	with pytest.raises(bw.WorkError, match="claimed by"):
		reroute(world, work, reason="lost the race")
	after = work_row(world, work)
	assert after == before, \
		"the losing reroute changed Route, Handler, Phase or Next"


def test_a_reroute_that_commits_first_makes_the_old_route_refuse(world):
	"""The other ordering: the reroute wins, and the claim the old
	route's handler was about to make is refused against the state that
	actually committed."""
	work = make(world)
	onto_alternate(world, work)
	reroute(world, work, reason="won the race")
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.claim_work(world["store"], work, actor_team="lang",
		              actor="grace")
	# and the route it moved TO can claim it
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["handler"]["member"] == "ada"


def test_an_exact_retry_replays_rather_than_moving_twice(world):
	work = make(world)
	first = reroute(world, work, route="alt", reason="to the alternate",
	                op_id="fix-1")
	again = reroute(world, work, route="alt", reason="to the alternate",
	                op_id="fix-1")
	assert again["operation"]["state"] == "replayed"
	assert first["seq"] == again["seq"]
	assert route_of(world, work)["route"] == "alt"


# -- the record --------------------------------------------------------------

def test_the_correction_is_a_work_event_and_not_a_message(world):
	"""'Record the correction in Work Events; it is not a discussion
	Message.'"""
	work = make(world)
	onto_alternate(world, work)
	before = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")
	reroute(world, work, reason="the runner is not taking it")
	after = pj.detail(world["store"], work, viewer_team="lang",
	                  viewer_member="ada")
	assert after["message_count"] == before["message_count"], \
		"the reroute posted a discussion message"
	assert after["thread_count"] == before["thread_count"]
	events = pj.work_events(world["store"], work)["events"]
	entry = next(row for row in events if row["kind"] == "reroute")
	assert entry["payload"]["reason"] == "the runner is not taking it"
	assert entry["payload"]["from"] == {"endpoint": "lang.impl",
	                                    "route": "alt"}
	assert entry["payload"]["resolution"]["route"] == "main"
	assert entry["payload"]["resolution"]["handlers"] == ["ada"]


def test_both_projections_agree_about_the_new_route(world):
	"""'Project the new Route consistently through direct and linked
	Work views' — the W39 lesson, asserted here rather than assumed."""
	work = make(world)
	consumer = make(world, title="the consumer")
	tr.add_dependency(world["store"], consumer, work, actor_team="lang",
	                  actor="ada", rationale="waits on it")
	reroute(world, work, route="alt", reason="to the alternate")
	direct = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")["route"]
	linked = pj.links(world["store"], consumer)["blocked_by"][0]["route"]
	assert direct["route"] == "alt"
	assert linked == direct, (linked, direct)
	rows = pj.tree(world["store"], None, viewer_team="lang",
	               viewer_member="ada")["rows"]
	row = next(entry for entry in rows if entry["id"] == work)
	assert row["route"] == direct


def test_readiness_offers_the_work_to_the_new_route(world):
	"""The reroute mints a new assignment episode, so the destination
	is woken even if this Work was delivered to them before."""
	work = make(world)
	assert any(action.get("work") == work for action in
	           pj.participant_actions(world["store"], viewer_team="lang",
	                                  viewer_member="ada")["actions"])
	reroute(world, work, route="alt", reason="to the alternate")
	assert not any(action.get("work") == work for action in
	               pj.participant_actions(
		world["store"], viewer_team="lang",
		viewer_member="ada")["actions"]), \
		"the old route is still being woken for it"
	assert any(action.get("work") == work for action in
	           pj.participant_actions(world["store"], viewer_team="lang",
	                                  viewer_member="grace")["actions"])


# -- the surface -------------------------------------------------------------

def test_detail_offers_reroute_to_the_owning_team_while_unclaimed(world):
	work = make(world)
	onto_alternate(world, work)
	mine = pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["available_transitions"]
	assert "reroute" in mine, mine
	assert "pass" not in mine, \
		"pass was advertised to somebody the route does not resolve"
	foreign = pj.detail(world["store"], work, viewer_team="push",
	                    viewer_member="sl")["available_transitions"]
	assert "reroute" not in foreign
	tr.claim_work(world["store"], work, actor_team="lang",
	              actor="grace")
	claimed = pj.detail(world["store"], work, viewer_team="lang",
	                    viewer_member="ada")["available_transitions"]
	assert "reroute" not in claimed, \
		"claimed Work still advertises a reroute it would refuse"


def test_the_verb_is_public_and_takes_a_durable_reason(world, capsys):
	spec = {key["name"]: key for key in _cli.GRAMMAR["reroute"]["keys"]}
	assert spec["reason"]["required"] and spec["reason"]["prose"]
	assert spec["work"]["required"] and spec["to"]["required"]
	assert not spec["route"]["required"]
	assert "reroute" in _cli.MUTATIONS
	work = make(world)
	code = _cli.main(["--config", world["config"], "--participant",
	                  "lang.ada", "reroute", f"work={work}",
	                  "to=lang.impl", "route=alt",
	                  "reason=the primary runner is saturated"])
	assert code == 0
	result = _json.loads(capsys.readouterr().out)["result"]
	assert result["to"] == "lang.impl" and result["route"] == "alt"


def test_the_cli_accepts_the_visible_local_work_selector(world, capsys):
	"""Every public work= operand accepts the W<n> spelling shown by the
	TUI. Reroute must resolve it before lookup and before operation-id
	identity, exactly like the existing Work verbs."""
	work = make(world)
	local = work.rsplit("-", 1)[1]
	code = _cli.main(["--config", world["config"], "--participant",
	                  "lang.ada", "reroute", f"work={local}",
	                  "to=lang.impl", "route=alt",
	                  "reason=the primary runner is saturated"])
	assert code == 0
	result = _json.loads(capsys.readouterr().out)["result"]
	assert result["work"] == work and result["route"] == "alt"
