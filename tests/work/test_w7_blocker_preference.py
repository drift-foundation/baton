"""W7: Work that is holding another agent goes first in its own pool.

`work/records/2026/08/finding-blocker-effective-priority/`, the
first-cut ruling of 2026-08-18. The live stall it comes from: W5
contained W6, W6 waited on W101, and W101 was implemented, ready and
unclaimed on a single reviewer route. Its ordinary queue position held
W6, W5 and a whole documentation track, and nothing in the displayed
ordering said so.

The confirmed rule is deliberately narrow and binary:

1. explicit `high | normal | low` stays the primary pool and is NEVER
   rewritten or inherited;
2. within one pool, ready unclaimed Work that currently blocks another
   agent sorts ahead of free-standing Work;
3. binary only — no cross-pool promotion, no weighted fan-out, no
   transitive scoring, no second priority axis;
4. stable creation order tie-breaks inside each group;
5. the SAME ordering drives human Work lists and participant readiness;
6. claimed, blocked or parked Work is never preempted or made claimable.

The broader effective-priority model in the finding stays deferred, and
the tests below are written to red if any part of it leaks in early.
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

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		          "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config, participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title, *, priority=None, parent=None):
	work = tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b", parent=parent)["work_id"]
	if priority is not None:
		tr.prioritize(world["store"], work, actor_team="lang", actor="ada",
		              priority=priority)
	return work


def gate(world, consumer, blocker, rationale="the pipeline needs it"):
	tr.add_dependency(world["store"], consumer, blocker, actor_team="lang",
	                  actor="ada", rationale=rationale)


def titles(world, member="ada"):
	return [row["title"] for row in
	        pj.home(world["store"], viewer_team="lang",
	                viewer_member=member)["rows"]]


def row(world, work, member="ada"):
	return next(entry for entry in
	            pj.home(world["store"], viewer_team="lang",
	                    viewer_member=member)["rows"]
	            if entry["id"] == work)


def wake_titles(world, member="ada"):
	return [action["title"] for action in
	        pj.participant_actions(world["store"], viewer_team="lang",
	                               viewer_member=member)["actions"]
	        if action["kind"] == "work"]


# -- the rule ----------------------------------------------------------------

def test_a_blocker_sorts_ahead_of_free_standing_work_in_its_pool(world):
	"""The live stall, reduced. `free` was created first and would lead
	on creation order alone; `blocker` is holding `consumer`, so it goes
	first — which is the whole operational statement."""
	free = make(world, "free-standing")
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)

	assert titles(world) == ["the blocker", "free-standing", "consumer"]
	assert row(world, blocker)["blocking"] is True
	assert row(world, free)["blocking"] is False
	# the consumer is gated, so it is not a candidate for the preference
	# even though something depends on nothing of it
	assert row(world, consumer)["blocking"] is False


def test_explicit_priority_is_never_rewritten_or_inherited(world):
	"""Rule 1. The preference is an ORDERING, not a promotion: the
	stored priority of every row is exactly what its owner set, before
	and after the edge exists."""
	consumer = make(world, "consumer", priority="high")
	blocker = make(world, "the blocker", priority="low")
	before = dict(world["store"].conn.execute(
		"SELECT id, priority FROM work").fetchall())
	gate(world, consumer, blocker)
	assert dict(world["store"].conn.execute(
		"SELECT id, priority FROM work").fetchall()) == before
	assert row(world, blocker)["priority"] == "low"
	assert row(world, consumer)["priority"] == "high"


def test_there_is_no_cross_pool_promotion(world):
	"""Rule 3, stated as the case that would expose it. A LOW blocker
	holding a HIGH consumer must not climb out of the low pool — an
	inherited or effective priority would put it first, and the ruling
	defers exactly that."""
	consumer = make(world, "high consumer", priority="high")
	ordinary = make(world, "normal free-standing")
	blocker = make(world, "low blocker", priority="low")
	gate(world, consumer, blocker)

	assert titles(world) == ["high consumer", "normal free-standing",
	                         "low blocker"]
	# it IS a blocker; it simply sorts first within LOW
	assert row(world, blocker)["blocking"] is True
	other_low = make(world, "other low", priority="low")
	assert titles(world)[-2:] == ["low blocker", "other low"]
	assert other_low


def test_the_preference_orders_only_within_one_pool(world):
	"""Rule 2 from the other side: two blockers and two free-standing
	Works across two pools interleave pool-first, blocker-second."""
	consumer = make(world, "consumer")
	high_free = make(world, "high free", priority="high")
	high_blocker = make(world, "high blocker", priority="high")
	normal_free = make(world, "normal free")
	normal_blocker = make(world, "normal blocker")
	gate(world, consumer, high_blocker)
	gate(world, consumer, normal_blocker)

	assert titles(world) == ["high blocker", "high free", "normal blocker",
	                         "consumer", "normal free"]
	assert high_free and normal_free


def test_creation_order_tie_breaks_inside_each_group(world):
	"""Rule 4. Two blockers keep their permanent order, and so do two
	free-standing rows; the preference splits the pool into exactly two
	stable groups and nothing more."""
	consumer = make(world, "consumer")
	free_one = make(world, "free one")
	blocker_one = make(world, "blocker one")
	free_two = make(world, "free two")
	blocker_two = make(world, "blocker two")
	gate(world, consumer, blocker_one)
	gate(world, consumer, blocker_two)

	# `consumer` was created before either free-standing row, so it
	# leads the non-blocking group: the tie-break is permanent creation
	# order, not "everything the reader thinks of as free-standing".
	assert titles(world) == ["blocker one", "blocker two", "consumer",
	                         "free one", "free two"]
	assert free_one and free_two


# -- the preference appears and disappears with the edge ---------------------

def test_removing_the_edge_removes_the_preference_immediately(world):
	"""Rule 4 of the proposed model, retained by the first cut: nothing
	is rewritten, the predicate simply stops being true. No automatic
	operation touches the blocker."""
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)
	assert titles(world)[0] == "the blocker"

	tr.remove_dependency(world["store"], consumer, blocker,
	                     actor_team="lang", actor="ada",
	                     rationale="it was never a real gate")
	assert titles(world) == ["consumer", "the blocker"]
	assert row(world, blocker)["blocking"] is False
	assert row(world, blocker)["priority"] == "normal", \
		"unblocking rewrote an explicit priority"


def test_closing_the_consumer_removes_the_preference(world):
	"""It stops holding somebody the moment the consumer is terminal —
	the edge stays in the ledger, the influence does not."""
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)
	assert row(world, blocker)["blocking"] is True

	tr.close_work(world["store"], consumer, actor_team="lang", actor="ada",
	              rationale="withdrawn", outcome="cancelled")
	assert row(world, blocker)["blocking"] is False
	# the closed consumer stays in the projection (collapsing it is TUI
	# presentation) and simply stops conferring the preference, so the
	# two rows fall back to permanent creation order
	assert titles(world) == ["consumer", "the blocker"]
	# the edge itself is still history
	assert world["store"].conn.execute(
		"SELECT COUNT(*) AS n FROM edges WHERE blocker=?",
		(blocker,)).fetchone()["n"] == 1


# -- rule 6: never preempted, never made claimable ---------------------------

def test_a_claimed_blocker_takes_no_preference(world):
	"""Somebody is already on it, so advertising it first tells an idle
	agent to pick up Work it may not have."""
	consumer = make(world, "consumer")
	free = make(world, "free-standing")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)
	assert titles(world)[0] == "the blocker"

	tr.claim_work(world["store"], blocker, actor_team="lang", actor="bee")
	assert row(world, blocker)["blocking"] is False
	assert titles(world) == ["consumer", "free-standing", "the blocker"]
	assert free


def test_a_parked_blocker_takes_no_preference(world):
	"""Parking is an explicit deferral. Sorting a parked Work to the
	front would quietly re-raise a decision somebody made on purpose."""
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)
	assert row(world, blocker)["blocking"] is True

	tr.set_phase(world["store"], blocker, actor_team="lang", actor="ada",
	             phase="parked", reason="waiting on an external release")
	assert row(world, blocker)["blocking"] is False
	assert titles(world) == ["consumer", "the blocker"]


def test_a_blocker_that_is_itself_gated_takes_no_preference(world):
	"""A chain: `deep` gates `middle`, `middle` gates `consumer`. Only
	the end that can actually be picked up leads — advertising `middle`
	would point an agent at Work nothing lets it start."""
	consumer = make(world, "consumer")
	middle = make(world, "middle")
	deep = make(world, "deep")
	gate(world, consumer, middle)
	gate(world, middle, deep)

	assert row(world, middle)["blocking"] is False, \
		"a gated blocker was advertised as pickable"
	assert row(world, deep)["blocking"] is True
	assert titles(world) == ["deep", "consumer", "middle"]


def test_the_ordering_makes_nothing_claimable_that_was_not(world):
	"""The boundary stated directly: ordering is presentation and
	scheduling. Eligibility, readiness and the claim are untouched, so a
	competing claim on a sorted-forward blocker still fails closed."""
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)
	assert titles(world)[0] == "the blocker"

	# the gated consumer is still not claimable
	with pytest.raises(bw.WorkError):
		tr.claim_work(world["store"], consumer, actor_team="lang",
		              actor="bee")
	# and the blocker is claimed exactly once
	tr.claim_work(world["store"], blocker, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError):
		tr.claim_work(world["store"], blocker, actor_team="lang",
		              actor="bee")


# -- rule 5: one ordering for humans and agents ------------------------------

def test_readiness_and_the_work_lists_name_the_same_next_work(world):
	"""Rule 5, which is the whole reason the order fragment is shared
	rather than repeated. An agent polling `wait` and an operator
	reading the board must be told the same thing."""
	free = make(world, "free-standing")
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)

	board = [title for title in titles(world)]
	woken = wake_titles(world)
	assert woken[0] == "the blocker"
	# the wake set is a SUBSET of the board (gated Work never wakes),
	# and the two agree wherever they overlap
	assert woken == [title for title in board if title in set(woken)]
	assert free


def test_children_and_tree_levels_order_identically(world):
	"""Sibling groups order the same at every level without leaving
	their parent, which is what the tree window has always promised —
	the preference must not be a root-only rule."""
	parent = make(world, "parent")
	free = make(world, "child free", parent=parent)
	consumer = make(world, "child consumer", parent=parent)
	blocker = make(world, "child blocker", parent=parent)
	gate(world, consumer, blocker)

	kids = [entry["title"] for entry in pj.children(
		world["store"], parent, viewer_team="lang", viewer_member="ada")]
	assert kids == ["child blocker", "child free", "child consumer"]

	window = pj.tree(world["store"], viewer_team="lang",
	                 viewer_member="ada")["rows"]
	nested = [entry["title"] for entry in window
	          if entry["title"].startswith("child")]
	assert nested == kids, "the tree window ordered siblings differently"
	assert free


def test_search_keeps_its_creation_order_cursor_contract(world):
	"""Deliberately NOT reordered. Search answers "find this Work", not
	"what next", and its `next_after` continuation cursor rides stable
	creation order — reordering it would break paging without helping
	anyone schedule."""
	consumer = make(world, "find consumer")
	blocker = make(world, "find blocker")
	gate(world, consumer, blocker)
	found = [entry["title"] for entry in pj.search(
		world["store"], "find", viewer_team="lang",
		viewer_member="ada")["rows"]]
	assert found == ["find consumer", "find blocker"]


# -- the published fact ------------------------------------------------------

def test_the_boost_is_a_published_boolean_not_a_glyph_to_parse(world):
	"""Clients read the canonical fact. `links.blocks` already names
	exactly whom it is holding, so the reason is inspectable without a
	count — and a count is what rule 3 defers."""
	consumer = make(world, "consumer")
	blocker = make(world, "the blocker")
	gate(world, consumer, blocker)

	view = pj.detail(world["store"], blocker, viewer_team="lang",
	                 viewer_member="ada")
	assert view["blocking"] is True
	assert view["open_dependents"] == 1
	assert [link["id"] for link in
	        pj.links(world["store"], blocker)["blocks"]] == [consumer]
	# nothing resembling an effective/derived priority is published
	assert "effective_priority" not in view
	assert "priority_boost" not in view


def test_the_projection_version_names_the_ordering_contract(world):
	from baton_work import jsonapi
	# W7's ordering rode 11.2 briefly and is aggregated into the 12.0
	# candidate W5's review ordered — nothing was released between them,
	# so two majors would describe a history that never happened.
	assert jsonapi.PROJECTION_VERSION == "12.3"
	jsonapi.require_version("12.0")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("11.2")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("10.0")


def test_one_predicate_serves_every_surface(world):
	"""There is exactly ONE blocker definition. A second copy is how
	the human board and the agent's wake set start disagreeing, which
	is the failure this finding is about."""
	import inspect
	source = inspect.getsource(pj)
	assert source.count("EXISTS (SELECT 1 FROM edges JOIN work AS blocked") \
		== 1, "the blocker predicate is written more than once"
	assert source.count("WORK_ORDER = (") == 1
	# and every Work-list statement uses it rather than its own spelling
	assert "ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 " \
		"ELSE 2 END, created_seq" not in source, \
		"an ordering surface kept its own pre-W7 order fragment"


# -- the rendered board -------------------------------------------------------

def test_the_drawn_table_leads_with_the_blocker(tmp_path):
	"""`identical TUI and readiness order`, asserted on a REAL screen.

	The first cut argued this was structural — the console has no sort
	of its own, so it renders whatever order the projection returns —
	and the generic parity suite does compare drawn rows to projected
	rows one for one. Neither actually exercises a BLOCKER, and an
	argument that a surface cannot disagree is not evidence that it
	does not. The two existing TUI tests that broke when this ordering
	landed were indirect evidence; this is the direct kind.

	If the board and the wake set could ever disagree about what to do
	next, that disagreement is the whole defect this Work exists to
	remove — so it is worth one test that a human's screen is the thing
	being asserted."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness

	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	# `zeta-consumer` and `alpha-free` are both created BEFORE the
	# blocker, so creation order alone would put the blocker last. Only
	# the preference can move it to the top.
	consumer = tr.create_work(store, team="lang", kind="bug",
	                          title="zeta-consumer",
	                          origin="external-report",
	                          classification="suspected-defect",
	                          author="ada", body="b")["work_id"]
	tr.create_work(store, team="lang", kind="bug", title="alpha-free",
	               origin="external-report",
	               classification="suspected-defect",
	               author="ada", body="b")
	blocker = tr.create_work(store, team="lang", kind="bug",
	                         title="omega-blocker",
	                         origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")["work_id"]
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="the pipeline needs it")
	# the projection's own answer, to compare the screen against
	board = [row["title"] for row in pj.home(
		store, viewer_team="lang", viewer_member="ada")["rows"]]
	store.close()
	assert board == ["omega-blocker", "zeta-consumer", "alpha-free"], board

	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b"", 0.6), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0])
	drawn = [title for title in board
	         if any(title in line for line in screen)]
	assert drawn == board, \
		f"the drawn table did not carry the projected order: {drawn}"
	at = {title: next(index for index, line in enumerate(screen)
	                  if title in line) for title in board}
	assert at["omega-blocker"] < at["zeta-consumer"] < at["alpha-free"], \
		f"the blocker is not at the top of the drawn board: {at}"
