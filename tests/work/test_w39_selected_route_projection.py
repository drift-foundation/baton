"""W39: every Work-relative projection follows its selected Route.

The visible endpoint stays stable while one Work may select an alternate
Route.  Readiness, detail authority and due-trial responsibility must all
resolve that same selection.  A directed obligation is different: it names
its own endpoint and must not inherit the surrounding Work's selection.
"""

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
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document({
		"lang": {"members": {"ada": ["dev"], "gem": ["dev"]},
		         "kinds": ["bug"]},
		"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	})
	lang = document["teams"]["lang"]
	lang["routes"]["main2"] = {"role": "dev", "handlers": ["gem"]}
	lang["kinds"]["bug"]["alternates"] = ["main2"]
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(document, indent=2), encoding="utf-8")
	database = lc.init_from_config(str(path),
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": str(path)}
	store.close()


def _make(world, title="selected"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")


def _select_alternate(world, work):
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="use the alternate", route="main2")


def _work_actions(world, member):
	return [entry for entry in pj.participant_actions(
		world["store"], viewer_team="lang", viewer_member=member)["actions"]
		if entry["kind"] == "work"]


def _due_actions(world, member):
	return [entry for entry in pj.participant_actions(
		world["store"], viewer_team="lang", viewer_member=member)["actions"]
		if entry["kind"] == "due_trial"]


def test_selected_route_controls_work_readiness_detail_and_claim_recovery(world):
	born = _make(world)
	work = born["work_id"]
	_select_alternate(world, work)
	assert not _work_actions(world, "ada"), \
		"the default handler was woken for alternate-routed Work"
	assert [entry["work"] for entry in _work_actions(world, "gem")] == [work]
	assert "claim" not in pj.detail(
		world["store"], work, viewer_team="lang",
		viewer_member="ada")["available_transitions"]
	assert "claim" in pj.detail(
		world["store"], work, viewer_team="lang",
		viewer_member="gem")["available_transitions"]

	tr.claim_work(world["store"], work, actor_team="lang", actor="gem")
	assert not _work_actions(world, "ada")
	claimed = _work_actions(world, "gem")
	assert len(claimed) == 1 and claimed[0]["claimed"] is True


def test_directed_obligation_keeps_its_own_endpoint_resolution(world):
	born = _make(world)
	work = born["work_id"]
	_select_alternate(world, work)
	posted = tr.post_thread(
		world["store"], born["thread"], author_team="lang", author="gem",
		body="lang: answer independently", request="lang.bug", on=work,
		wait=False)
	key = f"obligation:{posted['seq']}"
	ada = pj.participant_actions(world["store"], viewer_team="lang",
	                             viewer_member="ada")["actions"]
	gem = pj.participant_actions(world["store"], viewer_team="lang",
	                             viewer_member="gem")["actions"]
	assert key in [entry["action_key"] for entry in ada], \
		"the endpoint's default handler lost its directed obligation"
	assert key not in [entry["action_key"] for entry in gem], \
		"the Work's alternate Route leaked into an independent obligation"


def test_selected_route_controls_due_trial_actions_and_owed_by(world):
	store = world["store"]
	work = _make(world)["work_id"]
	_select_alternate(world, work)
	store.clock = lambda: "2026-08-19T11:00:00Z"
	tr.create_trial(store, work, actor_team="lang", actor="gem",
	                candidate="candidate", assign=["push.bug"],
	                review_at="2026-08-19T12:00:00Z")
	store.clock = lambda: "2026-08-19T12:00:00Z"
	assert not _due_actions(world, "ada"), \
		"the default handler was woken for an alternate-routed trial"
	due = _due_actions(world, "gem")
	assert len(due) == 1
	assert due[0]["responsible"]["route"] == "main2"
	assert due[0]["responsible"]["handlers"] == ["gem"]
	derived = [entry for entry in pj.obligations(
		store, viewer_team="lang") if entry["flavor"] == "due_trial"]
	assert len(derived) == 1
	assert derived[0]["owed_by"]["route"] == "main2"
	assert derived[0]["owed_by"]["handlers"] == ["gem"]


def test_withdrawn_selected_route_fails_closed_in_every_action_view(world):
	work = _make(world)["work_id"]
	_select_alternate(world, work)
	document = json.loads(open(world["config"], encoding="utf-8").read())
	del document["teams"]["lang"]["kinds"]["bug"]["alternates"]
	document["generation"] = 2
	open(world["config"], "w", encoding="utf-8").write(
		json.dumps(document, indent=2))
	lc.accept_config(world["config"], actor="lang.ada")
	assert not _work_actions(world, "ada")
	assert not _work_actions(world, "gem")
	for member in ("ada", "gem"):
		available = pj.detail(world["store"], work, viewer_team="lang",
		                      viewer_member=member)["available_transitions"]
		assert "claim" not in available


def test_config_generation_redelivers_selected_route_deterministically(world):
	work = _make(world)["work_id"]
	_select_alternate(world, work)
	first = _work_actions(world, "gem")[0]
	document = json.loads(open(world["config"], encoding="utf-8").read())
	document["generation"] = 2
	open(world["config"], "w", encoding="utf-8").write(
		json.dumps(document, indent=2))
	lc.accept_config(world["config"], actor="lang.ada")
	second = _work_actions(world, "gem")[0]
	assert first["work"] == second["work"] == work
	assert first["episode_seq"] == second["episode_seq"]
	assert first["config_generation"] == 1
	assert second["config_generation"] == 2
	assert first["action_key"] != second["action_key"]
