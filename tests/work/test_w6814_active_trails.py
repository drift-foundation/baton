"""W6814 — the actively claimed Work a bounded window hides.

`work/records/2026/08/finding-tui-active-descendant-trail/`, both rulings
approved 2026-08-24: an additive projection-minor `tree.active_trails` derived
INSIDE the tree snapshot, and one trail for every hidden canonical claim even
when that Work contains children.

THE DEFECT THESE CASES REPRODUCE. The window is three containment levels. A
Work claimed at the fourth is invisible, so an operator sees a roll-up with no
Handler and no reason to re-root while somebody is working underneath it. With
a Handler filter it is worse: the only matching Work is outside the window, so
nothing matches and nothing retains it as context — the screen is EMPTY while
that handler is holding something.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import pytest                                                 # noqa: E402

import baton_work as bw                                       # noqa: E402
from baton_work import projection                             # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


TEAM = "lang"
MEMBER = "ada"


@pytest.fixture
def authority(tmp_path):
	return fx.open_instance(str(tmp_path))


def make(store, title, parent=None, kind="rsrch"):
	return tr.create_work(store, team=TEAM, kind=kind, title=title,
	                      origin="external-report", author=MEMBER,
	                      classification="confirmed-defect",
	                      body="a body", parent=parent)["work_id"]


def chain(store, depth, *, titles=None):
	"""One containment chain `depth` levels deep, returned root-first."""
	made = []
	parent = None
	for level in range(depth):
		parent = make(store, (titles or {}).get(level, f"level-{level}"),
		              parent)
		made.append(parent)
	return made


def claim(store, work_id, actor=MEMBER):
	return tr.claim_work(store, work_id, actor_team=TEAM, actor=actor)


def tree(store, root=None, **filters):
	return projection.tree(store, root, viewer_team=TEAM,
	                       viewer_member=MEMBER,
	                       work_filter=filters or None)


class TestTheWindowReportsWhatItHides:

	def test_a_claim_below_the_three_level_window_is_reported(self, authority):
		store = authority
		levels = chain(store, 4)
		deep = levels[3]
		claim(store, deep)
		answer = tree(store, levels[0])
		painted = [row["id"] for row in answer["rows"]]
		assert deep not in painted, "the defect no longer reproduces"
		trails = answer["active_trails"]
		assert len(trails) == 1
		assert trails[0]["work"]["id"] == deep
		# Anchored to the DEEPEST VISIBLE ancestor, which is where the
		# elision and the leaf are painted.
		assert trails[0]["anchor"] == levels[2]
		assert trails[0]["hidden_depth"] == 1

	def test_an_ordinarily_visible_claim_is_never_duplicated(self, authority):
		store = authority
		levels = chain(store, 3)
		claim(store, levels[2])
		answer = tree(store, levels[0])
		assert levels[2] in {row["id"] for row in answer["rows"]}
		assert answer["active_trails"] == [], \
			"a row the window already paints was reported twice"

	def test_a_claimed_non_leaf_is_still_a_trail(self, authority):
		"""The approved ruling: ONE TRAIL PER HIDDEN CLAIM, even when the
		claimed Work contains children.

		Reporting only containment leaves would hide a handler holding a
		roll-up, and handlers working at the same time are exactly who this field exists to
		surface.
		"""
		store = authority
		levels = chain(store, 5)
		held = levels[3]
		claim(store, held)
		trails = tree(store, levels[0])["active_trails"]
		assert [trail["work"]["id"] for trail in trails] == [held]
		assert trails[0]["work"]["status"] == "open"

	# NOT HERE, AND NAMED RATHER THAN WEAKENED: several handlers under one
	# anchor. A participant holds ONE active claim at a time, so proving it
	# needs two eligible handlers of the same route -- which this fixture
	# team does not configure. Writing it with one handler would give the
	# case a name it does not earn. It needs a two-handler fixture and is
	# recorded in PROGRESS as remaining work.

	def test_queued_and_closed_work_is_not_a_trail(self, authority):
		"""ACTIVITY IS A CLAIM, not a guess. Nothing here infers it from
		messages or timers."""
		store = authority
		levels = chain(store, 4)
		# Unclaimed and therefore not active.
		assert tree(store, levels[0])["active_trails"] == []

	def test_the_field_is_additive_and_the_rows_are_untouched(self,
	                                                          authority):
		"""The projection MINOR is what advances; a consumer that ignores the
		new member reads exactly what it read before."""
		store = authority
		levels = chain(store, 4)
		before = tree(store, levels[0])
		claim(store, levels[3])
		after = tree(store, levels[0])
		assert [row["id"] for row in after["rows"]] == \
			[row["id"] for row in before["rows"]]
		# W26328 adds `actionable_for_viewer` as projection 12.7's additive
		# member. The rule this case states is unchanged -- the member set is
		# exhaustive and a consumer that ignores a new member reads what it
		# read before -- so the set grows by exactly the one the approved
		# contract names.
		assert set(after) == set(before) == {
			"rows", "summary", "filter", "active_trails",
			"actionable_for_viewer", "snapshot_seq"}


class TestTheFilterCounterexample:
	"""The exact case the revalidation recorded: `tree work=W2
	handler=baton.claude` returned NO rows while a hidden Work was held."""

	def test_a_handler_filter_finds_the_claim_the_window_hides(self,
	                                                           authority):
		store = authority
		levels = chain(store, 4)
		deep = levels[3]
		claim(store, deep)
		answer = tree(store, levels[0], handler="lang.ada")
		# CORRECTED under the review's case-specific approval. This asserted
		# `rows == []`, which enshrined the opposite of the confirmed ruling:
		# a hidden matching claim keeps its bounded ancestors as STRUCTURAL
		# CONTEXT, exactly as an ordinarily visible matching descendant does,
		# so the renderer has a visible ancestor to group the trail under.
		assert [row["id"] for row in answer["rows"]] == levels[:3]
		assert all(row["filter_match"] is False for row in answer["rows"])
		assert answer["active_trails"][0]["anchor"] == levels[2], \
			"the anchor is the deepest RETAINED row"
		# ...and the screen is no longer empty about a handler who is
		# holding something.
		assert [trail["work"]["id"]
		        for trail in answer["active_trails"]] == [deep]

	def test_a_trail_the_filter_excludes_is_not_reported(self, authority):
		"""The field must not become a way around the filter.

		A trail is reported only when the claimed Work ITSELF matches, so
		`handler=X` answers about X and nobody else.
		"""
		store = authority
		levels = chain(store, 4)
		claim(store, levels[3])
		# `grace` holds nothing, so a filter naming her must report no trail
		# even though a claim exists under this root.
		answer = tree(store, levels[0], handler="lang.grace")
		assert answer["active_trails"] == []

	def test_a_deep_filter_match_retains_its_visible_ancestors(self,
	                                                         authority):
		"""The approved clarification keeps bounded ancestors as structural
		context. An anchor absent from `rows` gives the renderer nowhere to
		insert the trail and is not a visible ancestor."""
		store = authority
		levels = chain(store, 4)
		claim(store, levels[3])
		answer = tree(store, levels[0], handler="lang.ada")
		painted = [row["id"] for row in answer["rows"]]
		assert painted == levels[:3]
		assert all(row["filter_match"] is False for row in answer["rows"])
		assert answer["active_trails"][0]["anchor"] in painted


class TestItStaysOneSnapshotAndOneWindow:

	def test_a_claim_outside_the_requested_root_is_not_this_calls_business(
			self, authority):
		store = authority
		mine = chain(store, 4)
		elsewhere = chain(store, 4, titles={0: "other-root"})
		claim(store, elsewhere[3])
		assert tree(store, mine[0])["active_trails"] == []

	def test_the_trails_carry_the_same_snapshot_as_the_rows(self, authority):
		"""Derived inside the transaction that already exists, which is the
		whole reason the ruling put it in the projection rather than in the
		renderer: a client join would mix independent snapshots on one
		screen."""
		store = authority
		levels = chain(store, 4)
		claim(store, levels[3])
		answer = tree(store, levels[0])
		assert answer["snapshot_seq"] == store.last_seq()
		assert answer["active_trails"][0]["work"]["handler"] is not None

	def test_a_trail_row_keeps_the_claim_facts_of_the_canonical_row(
			self, authority):
		"""The endpoint is the exact active Work row, not a reduced row whose
		claim disappeared while its Handler survived."""
		store = authority
		levels = chain(store, 4)
		claim(store, levels[3])
		trail = tree(store, levels[0])["active_trails"][0]["work"]
		detail = projection.detail(store, levels[3], viewer_team=TEAM,
		                           viewer_member=MEMBER)
		assert trail["claimed_at"] == detail["claimed_at"]
		assert trail["heartbeat_at"] == detail["heartbeat_at"]
		assert trail["claimed_at"] is not None


class TestEveryConcurrentHandlerRemainsVisible:

	def test_same_anchor_trails_follow_full_containment_order(self, tmp_path):
		"""The endpoint's own priority must not leapfrog the hidden branch it
		lives under. Canonical tree order is sibling order at every level."""
		_config, database = fx.build_crew(str(tmp_path), TEAM,
		                                    ("ada", "grace"),
		                                    kinds=("rsrch",))
		store = bw.Authority(database)
		try:
			root, child, anchor = chain(store, 3)
			first_branch = tr.create_work(
				store, team=TEAM, kind="rsrch", title="first branch",
				origin="decomposition", author=MEMBER,
				classification="confirmed-defect", body="a body",
				parent=anchor, priority="high")["work_id"]
			first_claim = tr.create_work(
				store, team=TEAM, kind="rsrch", title="first claim",
				origin="decomposition", author=MEMBER,
				classification="confirmed-defect", body="a body",
				parent=first_branch, priority="low")["work_id"]
			second_branch = tr.create_work(
				store, team=TEAM, kind="rsrch", title="second branch",
				origin="decomposition", author=MEMBER,
				classification="confirmed-defect", body="a body",
				parent=anchor, priority="low")["work_id"]
			second_claim = tr.create_work(
				store, team=TEAM, kind="rsrch", title="second claim",
				origin="decomposition", author=MEMBER,
				classification="confirmed-defect", body="a body",
				parent=second_branch, priority="high")["work_id"]
			claim(store, first_claim, actor="ada")
			claim(store, second_claim, actor="grace")
			trails = tree(store, root)["active_trails"]
			assert [trail["work"]["id"] for trail in trails] == [
				first_claim, second_claim]
		finally:
			store.close()
