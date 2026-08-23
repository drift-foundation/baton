"""W230: one visible endpoint, one default route, explicit alternates.

`baton.impl` stays the endpoint an operator names. Behind it, `impl`
remains the deterministic default handled by Claude, and `impl2` is a
backup handled by Gemini that is selected per Work or not at all. Baton
never fails over, never races both, and never shows every candidate on a
Work row.

The three facts that make that safe, and that this file exists to hold:
the selection is DURABLE (the endpoint's route is otherwise re-resolved
on every read, so a choice would last one transaction); it is the only
route projected for that Work; and authorization follows it, or the
agent actually holding the Work could not act on it.
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
from baton_work import config                                 # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


def _document(alternates=("main2",)):
	"""`lang.bug` with a default route to `ada` and a backup to `gem` —
	the shape of `impl`/`impl2` without hard-coding the deployment's own
	handles into a protocol test."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "gem": ["dev"]},
		          "kinds": ["bug"]}})
	lang = document["teams"]["lang"]
	lang["routes"]["main2"] = {"role": "dev", "handlers": ["gem"]}
	if alternates:
		lang["kinds"]["bug"]["alternates"] = list(alternates)
	return document


@pytest.fixture()
def world(tmp_path):
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(_document(), indent=2), encoding="utf-8")
	result = lc.init_from_config(str(path), participant="lang.ada")
	store = bw.Authority(result["database"])
	yield {"store": store, "config": str(path)}
	store.close()


def _make(world, title="t"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")["work_id"]


def _route(world, work, viewer="ada"):
	return pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member=viewer)["route"]


# -- configuration -----------------------------------------------------------

def test_a_kind_may_declare_selectable_alternates():
	document = config.loads(json.dumps(_document()))
	assert document["teams"]["lang"]["kinds"]["bug"]["alternates"] == ["main2"]


def test_a_kind_without_alternates_is_unchanged():
	"""Every existing configuration stays valid: the field is optional
	and its absence means exactly one route, as before."""
	document = config.loads(json.dumps(_document(alternates=())))
	assert "alternates" not in document["teams"]["lang"]["kinds"]["bug"]


def test_an_undeclared_alternate_refuses():
	document = _document(alternates=("nowhere",))
	with pytest.raises(bw.WorkError, match="does not declare"):
		config.loads(json.dumps(document))


def test_an_alternate_carrying_a_different_role_refuses():
	"""'an unconfigured or role-incompatible route refuses atomically'.

	The endpoint's MEANING must not change with the route. An alternate
	with another role would make one visible endpoint mean
	implementation or review depending on a per-Work choice, which is
	the confusion a visible endpoint exists to prevent."""
	document = _document(alternates=("other",))
	lang = document["teams"]["lang"]
	lang["roles"]["rev"] = {"display": "Review", "instructions": "Review."}
	# gem must HOLD the role, or an earlier rule refuses first and this
	# test would pass for somebody else's reason.
	lang["participants"]["gem"]["roles"] = ["dev", "rev"]
	lang["routes"]["other"] = {"role": "rev", "handlers": ["gem"]}
	with pytest.raises(bw.WorkError, match="not the endpoint's"):
		config.loads(json.dumps(document))


def test_a_kind_may_not_list_its_own_default():
	document = _document(alternates=("main",))
	with pytest.raises(bw.WorkError, match="its own default route"):
		config.loads(json.dumps(document))


def test_a_repeated_alternate_refuses():
	document = _document(alternates=("main2", "main2"))
	with pytest.raises(bw.WorkError, match="more than once"):
		config.loads(json.dumps(document))


# -- the default is not one candidate among equals --------------------------

def test_work_is_born_on_the_default_route(world):
	work = _make(world)
	assert _route(world, work)["route"] == "main"
	assert _route(world, work)["handlers"] == ["ada"]


def test_a_handoff_with_no_selection_resolves_to_the_default(world):
	"""'Handoff with no route selects `impl`.'"""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	assert _route(world, work)["route"] == "main2"
	fx.hand_off(world["store"], work, actor_team="lang", actor="gem",
	             to="lang.bug", comment="back")
	assert _route(world, work)["route"] == "main", \
		"an omitted selection did not return to the deterministic default"


def test_nothing_ever_selects_an_alternate_on_its_own(world):
	"""Baton never fails over. Even with the default route's handler
	removed from every other consideration, an unselected Work stays on
	the default rather than drifting to a backup that could serve it."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.release_claim(world["store"], work, actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 episode=fx.episode_of(world["store"], work),
	                 reason="stepping away")
	assert _route(world, work)["route"] == "main"


# -- the selection is durable, and the only one projected -------------------

def test_the_selection_survives_later_reads(world):
	"""The endpoint's route is re-resolved on every read, so without a
	stored selection the operator's choice would last exactly one
	transaction and the next read would show — and route to — the
	default."""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="to the backup", route="main2")
	for _repeat in range(3):
		assert _route(world, work)["route"] == "main2"
	assert world["store"].conn.execute(
		"SELECT route_selected FROM work WHERE id=?",
		(work,)).fetchone()["route_selected"] == "main2"


def test_the_selected_route_is_the_only_one_projected(world):
	"""'The selected route is … the only route projected for that
	Work.' No list of candidates on the row."""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	route = _route(world, work)
	assert route["route"] == "main2"
	assert route["handlers"] == ["gem"]
	assert "alternates" not in route and "candidates" not in route
	assert "main" not in json.dumps(route).replace("main2", "")


def test_the_event_records_the_selection(world):
	"""'The selected route is recorded in authoritative Events.'"""
	work = _make(world)
	passed = fx.hand_off(world["store"], work, actor_team="lang",
	                      actor="ada", to="lang.bug", comment="over",
	                      route="main2")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == passed["seq"])
	assert event["payload"]["route_selected"] == "main2"
	assert event["payload"]["pass_resolution"]["route"] == "main2"
	assert event["payload"]["pass_resolution"]["handlers"] == ["gem"]


def test_an_unselected_handoff_records_no_selection(world):
	work = _make(world)
	# a handoff has to MOVE the baton, so reach the alternate first and
	# come back with no selection — which is the case under test.
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="out", route="main2")
	passed = fx.hand_off(world["store"], work, actor_team="lang",
	                      actor="gem", to="lang.bug", comment="back")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == passed["seq"])
	assert event["payload"]["route_selected"] is None
	assert event["payload"]["pass_resolution"]["route"] == "main"


# -- authorization follows the selection ------------------------------------

def test_the_selected_route_s_handler_can_act(world):
	"""The bug this catches is total: resolve authorization through the
	endpoint's DEFAULT and the agent actually holding the Work is not a
	handler, so a Work sent to an alternate can never be claimed,
	passed, or closed. The selection would strand it."""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	tr.claim_work(world["store"], work, actor_team="lang", actor="gem")
	assert _route(world, work, viewer="gem")["handlers"] == ["gem"]
	fx.hand_off(world["store"], work, actor_team="lang", actor="gem",
	             to="lang.bug", comment="back")
	assert _route(world, work)["route"] == "main"


def test_the_default_route_s_handler_cannot_act_on_a_selected_work(world):
	"""The other side of the same rule: eligibility follows the Work's
	own route, so the default's handler is not eligible while it sits on
	an alternate."""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.claim_work(world["store"], work, actor_team="lang", actor="ada")


# -- refusals ----------------------------------------------------------------

def test_an_unconfigured_route_refuses_atomically(world):
	work = _make(world)
	# W2571: the claim is part of the SETUP, so it is taken before the
	# baseline — what this test measures is that the refused pass wrote
	# nothing, not that a claim did.
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	before = world["store"].last_seq()
	with pytest.raises(bw.WorkError, match="does not offer route"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.bug", comment="over", route="nowhere")
	assert world["store"].last_seq() == before, "the refusal wrote an event"
	assert _route(world, work)["route"] == "main"


def test_a_pass_that_moves_nothing_still_refuses(world):
	"""The guard that a pass must MOVE the baton now compares the route,
	not only the visible endpoint — otherwise selecting an alternate on
	the same endpoint would have been refused as a non-move, which is
	the very operation this Work adds."""
	work = _make(world)
	with pytest.raises(bw.WorkError, match="already at"):
		fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.bug", comment="nowhere")
	# but the same endpoint on a DIFFERENT route is a real move
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	assert _route(world, work)["route"] == "main2"
	# and repeating THAT is a non-move again
	with pytest.raises(bw.WorkError, match="already at"):
		fx.hand_off(world["store"], work, actor_team="lang", actor="gem",
		             to="lang.bug", comment="again", route="main2")


def test_claimed_work_never_moves_underneath_its_handler(world):
	"""'Claimed Work never moves underneath its Handler. It must first
	be released or passed, then rerouted and claimed normally.'"""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	# a second eligible handler cannot reroute it out from under ada
	document = json.loads(open(world["config"], encoding="utf-8").read())
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["ada", "gem"]
	document["generation"] = 2
	open(world["config"], "w", encoding="utf-8").write(json.dumps(document))
	lc.accept_config(world["config"], actor="lang.ada")
	with pytest.raises(bw.WorkError, match="actively claimed"):
		fx.hand_off(world["store"], work, actor_team="lang", actor="gem",
		             to="lang.bug", comment="mine now", route="main2")
	# the claimant's own pass releases and reroutes in one act
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="handing over", route="main2")
	assert _route(world, work)["route"] == "main2"
	assert pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["handler"] is None


# -- configuration change ----------------------------------------------------

def test_regeneration_carries_the_alternates(world):
	"""`regen` reloads the whole configuration, so the selectable set
	must be rebuilt with it rather than surviving as stale rows."""
	document = json.loads(open(world["config"], encoding="utf-8").read())
	del document["teams"]["lang"]["kinds"]["bug"]["alternates"]
	document["generation"] = 2
	open(world["config"], "w", encoding="utf-8").write(json.dumps(document))
	lc.accept_config(world["config"], actor="lang.ada")
	work = _make(world)
	with pytest.raises(bw.WorkError, match="does not offer route"):
		fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.bug", comment="over", route="main2")


def test_a_work_on_a_withdrawn_alternate_projects_unresolved(world):
	"""A selection the accepted configuration no longer offers reports
	explicitly unresolved — the same way any stale endpoint does —
	rather than silently reverting to the default and sending the
	operator to a different agent than the record says."""
	work = _make(world)
	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.bug", comment="over", route="main2")
	document = json.loads(open(world["config"], encoding="utf-8").read())
	del document["teams"]["lang"]["kinds"]["bug"]["alternates"]
	document["generation"] = 2
	open(world["config"], "w", encoding="utf-8").write(json.dumps(document))
	lc.accept_config(world["config"], actor="lang.ada")
	route = _route(world, work)
	assert route["route"] is None and route["handlers"] == [], route
	assert route["endpoint"] == "lang.bug"


# -- existing behaviour ------------------------------------------------------

def test_an_endpoint_without_alternates_behaves_exactly_as_before(tmp_path):
	"""'Existing Claude `impl` assignments and default behavior remain
	intact.'"""
	path = tmp_path / "baton.json"
	path.write_text(json.dumps(_document(alternates=()), indent=2),
	                encoding="utf-8")
	store = bw.Authority(
		lc.init_from_config(str(path), participant="lang.ada")["database"])
	try:
		work = tr.create_work(store, team="lang", kind="bug", title="t",
		                      origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="b")["work_id"]
		assert pj.detail(store, work, viewer_team="lang",
		                 viewer_member="ada")["route"]["route"] == "main"
		with pytest.raises(bw.WorkError, match="does not offer route"):
			fx.hand_off(store, work, actor_team="lang", actor="ada",
			             to="lang.bug", comment="over", route="main2")
	finally:
		store.close()


def test_the_recorded_deployment_block_is_acceptable_configuration():
	"""W230 step 2 records the exact `teams.baton` additions the next
	generation must carry. Applying them is the approver's act, so this
	proves the material is valid BEFORE that — a deployment step is a
	poor place to discover a malformed route."""
	import re
	here = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	path = os.path.join(here, "work", "records", "2026", "08",
	                    "finding-gemini-acp-impl2", "DEPLOYMENT.md")
	with open(path, encoding="utf-8") as handle:
		found = re.search(r"```json\n(.*?)```", handle.read(), re.S)
	assert found, "the recorded configuration block is missing"
	block = json.loads(found.group(1))
	assert block["kinds"]["impl"]["route"] == "impl", \
		"the default route is not the existing one"
	assert block["kinds"]["impl"]["alternates"] == ["impl2"]
	assert block["routes"]["impl2"]["handlers"] == ["gemini"], \
		"impl2 is not handled solely by Gemini"
	assert block["routes"]["impl2"]["role"] == "impl", \
		"Gemini does not hold the existing impl role"

	document = fx.config_document(
		{"baton": {"members": {"claude": ["impl"]}, "kinds": ["impl"]}})
	team = document["teams"]["baton"]
	team["roles"]["impl"] = {"display": "Implementer",
	                         "instructions": "Implement what is routed."}
	team["routes"]["impl"] = {"role": "impl", "handlers": ["claude"]}
	team["routes"].update(block["routes"])
	team["participants"].update(block["participants"])
	team["kinds"].update(block["kinds"])
	accepted = config.loads(json.dumps(document))
	kind = accepted["teams"]["baton"]["kinds"]["impl"]
	assert kind["route"] == "impl" and kind["alternates"] == ["impl2"]
