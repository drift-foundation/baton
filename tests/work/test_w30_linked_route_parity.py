"""W30: a linked Work keeps the alternate route it was sent to.

`work/records/2026/08/finding-linked-work-alternate-route-projection/`.
The projection-12 authority routed W25 through `baton.impl` on the
explicit internal route `impl2`. `detail work=W25` said so — endpoint
`baton.impl`, route `impl2`, handlers `gemini`. Reading the SAME Work
through its dependency, from `detail work=W17`, `links.blocks` said
route `impl`, handlers `claude`.

The authority row was not ambiguous and nothing was reconfigured
between the reads. One projection sent an operator to Gemini and the
other to Claude.

The cause was one omitted argument: `links()`'s local `far()` resolved
every neighbour with `route_team` and `route_kind` and dropped
`route_selected`, so linked views fell back to the endpoint's default
while direct views honoured W230. That affects EVERY relationship
`far()` serves, which is why these tests sweep all of them rather than
the one the incident happened to expose.

The correction itself landed under W128, whose own acceptance boundary
required direct and linked views to agree; this record owns the
regressions that keep it true.
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
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402


def document(generation=1, alternates=("alt",)):
	"""`lang.impl` offers an alternate route resolving to a DIFFERENT
	member, which is the only shape in which this defect exists: with
	one route per endpoint the wrong resolution gives the right
	answer."""
	base = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "impl"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	team = base["teams"]["lang"]
	team["routes"]["main"] = {"role": "dev", "handlers": ["ada"]}
	team["routes"]["alt"] = {"role": "dev", "handlers": ["grace"]}
	team["kinds"]["impl"] = {"display": "Impl", "route": "main",
	                         "alternates": list(alternates)}
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
	yield {"store": store, "config": config_path}
	store.close()


def make(world, title="a work", kind="impl", parent=None):
	return tr.create_work(world["store"], team="lang", kind=kind,
	                      title=title, origin="self-initiated",
	                      classification="design-choice", author="ada",
	                      body="the opener", parent=parent)["work_id"]


def onto_alternate(world, work):
	"""Send one Work to the alternate route, exactly as the incident's
	W25 was."""
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.impl", route="alt",
	             comment="offered to the alternate route")
	return work


def direct(world, work):
	return pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["route"]


def links(world, work):
	return pj.links(world["store"], work)


def assert_parity(world, neighbour, seen, where):
	"""The acceptance boundary's demand: EXACT route and handler parity
	with the Work's own direct projection."""
	expected = direct(world, neighbour)
	assert seen == expected, (where, seen, expected)


# -- both sides of a dependency ----------------------------------------------

def test_the_incident_read_from_the_other_side_of_its_dependency(world):
	"""W25 seen through W17, which is the read that disagreed."""
	consumer = make(world, title="the consumer")
	blocker = make(world, title="the blocker")
	# The edge exists first and the routing happens after, exactly as
	# the incident did: W17 -> W25 predated W25's move to impl2.
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="the consumer waits on the blocker")
	onto_alternate(world, consumer)
	assert direct(world, consumer)["route"] == "alt"
	assert direct(world, consumer)["handlers"] == ["grace"]
	seen = links(world, blocker)["blocks"][0]["route"]
	assert seen["route"] == "alt", \
		"the linked view sent the operator to the default route's agent"
	assert seen["handlers"] == ["grace"]
	assert_parity(world, consumer, seen, "blocks")


def test_the_same_edge_read_from_the_consumer_side(world):
	consumer = make(world, title="the consumer")
	blocker = onto_alternate(world, make(world, title="the blocker"))
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	seen = links(world, consumer)["blocked_by"][0]["route"]
	assert seen["route"] == "alt"
	assert_parity(world, blocker, seen, "blocked_by")


# -- containment -------------------------------------------------------------

def test_a_child_on_an_alternate_keeps_it_in_the_parents_view(world):
	parent = make(world, title="the parent")
	child = onto_alternate(world, make(world, title="the child",
	                                   parent=parent))
	seen = links(world, parent)["contains"][0]["route"]
	assert seen["route"] == "alt"
	assert_parity(world, child, seen, "contains")


def test_a_parent_on_an_alternate_keeps_it_in_the_childs_view(world):
	parent = make(world, title="the parent")
	child = make(world, title="the child", parent=parent)
	onto_alternate(world, parent)
	seen = links(world, child)["parent"]["route"]
	assert seen["route"] == "alt"
	assert_parity(world, parent, seen, "parent")


# -- the non-gating relationships --------------------------------------------

def test_a_duplicate_relation_keeps_the_alternate_both_ways(world):
	"""'At least one non-gating relationship' — and this one is
	navigable from both sides, so both are asserted."""
	survivor = onto_alternate(world, make(world, title="the survivor"))
	duplicate = make(world, title="the duplicate")
	tr.claim_work(world["store"], duplicate, actor_team="lang",
	              actor="ada")
	tr.close_work(world["store"], duplicate, actor_team="lang",
	              actor="ada", outcome="rejected",
	              rationale="the same defect as the survivor",
	              duplicate_of=survivor)
	seen = links(world, duplicate)["duplicate_of"]["route"]
	assert seen["route"] == "alt"
	assert_parity(world, survivor, seen, "duplicate_of")
	folded = links(world, survivor)["duplicates"][0]
	assert folded["id"] == duplicate
	# the folded row is terminal, so it reports no live route at all —
	# eligibility is a live question, and that rule is not this one
	assert folded["route"] is None


def test_a_follow_up_relation_keeps_the_alternate_both_ways(world):
	original = make(world, title="the original")
	tr.claim_work(world["store"], original, actor_team="lang",
	              actor="ada")
	tr.close_work(world["store"], original, actor_team="lang",
	              actor="ada", outcome="satisfying", rationale="shipped")
	follow_up = onto_alternate(world, tr.create_work(
		world["store"], team="lang", kind="impl",
		title="the follow-up", origin="self-initiated",
		classification="design-choice", author="ada", body="opener",
		follow_up_of=original)["work_id"])
	seen = links(world, original)["follow_ups"][0]["route"]
	assert seen["route"] == "alt"
	assert_parity(world, follow_up, seen, "follow_ups")
	back = links(world, follow_up)["follow_up_of"]
	assert back["id"] == original


# -- the sweep ---------------------------------------------------------------

def test_every_relationship_far_serves_agrees_with_the_direct_view(world):
	"""One omitted argument broke EVERY relationship `far()` builds, so
	the regression covers all of them in one authority rather than
	trusting that a fix in one call site reached the others."""
	hub = make(world, title="the hub")
	child = make(world, title="child", parent=hub)
	blocker = make(world, title="blocker")
	consumer = make(world, title="consumer")
	# Every edge first, on the default route where `ada` is the
	# resolved handler; then every neighbour moves to the alternate.
	tr.add_dependency(world["store"], hub, blocker, actor_team="lang",
	                  actor="ada", rationale="waits on it")
	tr.add_dependency(world["store"], consumer, hub, actor_team="lang",
	                  actor="ada", rationale="waits on the hub")
	neighbours = {"contains": onto_alternate(world, child),
	              "blocked_by": onto_alternate(world, blocker),
	              "blocks": onto_alternate(world, consumer)}
	view = links(world, hub)
	for relation in ("contains", "blocked_by", "blocks"):
		entry = view[relation][0]
		assert entry["route"]["route"] == "alt", (relation, entry)
		assert_parity(world, neighbours[relation], entry["route"],
		              relation)


# -- controls ----------------------------------------------------------------

def test_a_default_routed_neighbour_is_unchanged(world):
	"""'Default-routed and endpoint-without-alternates behavior must
	remain unchanged.'"""
	consumer = make(world, title="the consumer")
	blocker = make(world, title="the blocker")
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	seen = links(world, consumer)["blocked_by"][0]["route"]
	assert seen["route"] == "main"
	assert seen["handlers"] == ["ada"]
	assert_parity(world, blocker, seen, "blocked_by")


def test_an_endpoint_without_alternates_is_unchanged(world):
	consumer = make(world, title="the consumer", kind="bug")
	blocker = make(world, title="the blocker", kind="bug")
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	seen = links(world, consumer)["blocked_by"][0]["route"]
	assert seen["endpoint"] == "lang.bug"
	assert_parity(world, blocker, seen, "blocked_by")


def test_a_withdrawn_alternate_projects_unresolved_everywhere(world):
	"""'A selected route withdrawn by a later accepted configuration
	must project unresolved everywhere; a relationship view must not
	silently substitute the new/default route.' Substituting is the
	original defect wearing a different hat — it would send the
	operator to an agent nobody chose."""
	consumer = make(world, title="the consumer")
	blocker = onto_alternate(world, make(world, title="the blocker"))
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	with open(world["config"], "w", encoding="utf-8") as handle:
		_json.dump(document(generation=2, alternates=()), handle,
		           indent=2, sort_keys=True)
	lc.accept_config(world["config"], actor="lang.ada")
	straight = direct(world, blocker)
	assert straight["route"] is None and straight["handlers"] == [], \
		"the direct view substituted a route the operator never chose"
	seen = links(world, consumer)["blocked_by"][0]["route"]
	assert seen == straight, (seen, straight)
	assert seen["route"] is None, \
		"the linked view substituted the default for a withdrawn route"


def test_a_terminal_neighbour_reports_no_route_in_either_view(world):
	consumer = make(world, title="the consumer")
	blocker = onto_alternate(world, make(world, title="the blocker"))
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	tr.claim_work(world["store"], blocker, actor_team="lang",
	              actor="grace")
	tr.close_work(world["store"], blocker, actor_team="lang",
	              actor="grace", outcome="satisfying", rationale="done")
	assert direct(world, blocker) is None
	assert links(world, consumer)["blocked_by"][0]["route"] is None


def test_the_console_neighbour_view_reads_the_corrected_route(world):
	"""The `b` view renders `links` directly, so the operator-facing
	end of this defect is covered too."""
	from baton_work.tui.app import Console
	consumer = make(world, title="the consumer")
	blocker = onto_alternate(world, make(world, title="the blocker"))
	tr.add_dependency(world["store"], consumer, blocker,
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	view = Console(world["store"], "lang", "ada",
	               config_path=world["config"])
	view.links_work = consumer
	rows = view._links_rows()
	assert rows, rows
	assert any("lang.impl" in text for _work, text in rows)
