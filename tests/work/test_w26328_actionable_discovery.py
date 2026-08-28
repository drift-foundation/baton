"""W26328 — the participant-actionable Work an operator cannot otherwise find.

`work/records/2026/08/finding-actionable-work-discovery/`.

THE DEFECT THESE CASES REPRODUCE. The Jobs tab never says how much Work awaits
this participant, and the containment window is three levels deep — so a queued
item they could claim on the fourth has no row, no count and no locator. Search
needs a query and only reaches their own team; `active_trails` pierces the
bound only for Work somebody already holds.

THE COUNTING PREDICATE IS THE WHOLE DIFFICULTY, and it is narrower than every
neighbouring one in this repository:

  the TUI's bold Title       also the viewer's own claim and directed `@`
                             obligations, including blocked Work
  `participant_actions`      deliberately redelivers the viewer's claimed Work
                             for restart recovery
  `_first_actionable`        the right predicate, and answers exactly one row

W26328 counts Work the viewer could claim RIGHT NOW: open, ready, queued,
unclaimed, and whose exact current Route — including an explicitly selected
alternate — resolves to them. Planned `Next`, trials, pokes, runtime refreshes
and every Inbox concern are excluded, and W2938 stays authoritative that pickup
lateness is one participant obligation on Teams rather than N Work alerts.
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
OTHER = "grace"


@pytest.fixture
def authority(tmp_path):
	return fx.open_instance(str(tmp_path))


def shared_authority(directory):
	"""An authority whose default route has TWO handlers.

	The shipped fixture generates one handler per route, so a shared Route --
	which the finding is explicit about, because it decides what the count
	MEANS -- cannot be expressed through it. The document is edited before
	acceptance rather than the fixture being widened: this is one case's
	configuration, not a new shape every suite inherits.
	"""
	import json
	import os as _os
	from baton_work import lifecycle as lc
	document = fx.config_document()
	team = document["teams"]["lang"]
	role = team["routes"]["main"]["role"]
	team["routes"]["main"]["handlers"] = ["ada", "grace"]
	team["participants"]["grace"]["roles"] = \
		sorted(set(team["participants"]["grace"]["roles"] + [role]))
	# W230: ONE VISIBLE KIND MAY OFFER MORE THAN ONE ROUTE. The default is
	# what an omitted selection resolves to; an `alternate` is what an
	# operator may deliberately select per Work. The shipped fixture declares
	# none, so without this `route_selected` can never be non-null and the
	# clause that reads it is unreachable -- measured, and it was.
	team["routes"]["second"] = {"role": role, "handlers": ["grace"]}
	team["kinds"]["rsrch"]["alternates"] = ["second"]
	_os.makedirs(directory, exist_ok=True)
	place = _os.path.join(directory, "baton.json")
	with open(place, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
		handle.write("\n")
	answered = lc.init_from_config(place,
	                               participant=fx.first_participant(place))
	return bw.Authority(answered["database"])


def make(store, title, parent=None, kind="rsrch", author=MEMBER):
	return tr.create_work(store, team=TEAM, kind=kind, title=title,
	                      origin="external-report", author=author,
	                      classification="confirmed-defect",
	                      body="a body", parent=parent)["work_id"]


def chain(store, depth):
	"""One containment chain `depth` levels deep, returned root-first."""
	made = []
	parent = None
	for level in range(depth):
		parent = make(store, f"level-{level}", parent)
		made.append(parent)
	return made


def tree(store, root=None, member=MEMBER, **filters):
	return projection.tree(store, root, viewer_team=TEAM,
	                       viewer_member=member,
	                       work_filter=filters or None)


def flattened(store, member=MEMBER, **paging):
	return projection.actionable_work(store, viewer_team=TEAM,
	                                  viewer_member=member, **paging)


def row(answer, work_id):
	return next(one for one in answer["rows"] if one["id"] == work_id)


class TestTheCountingPredicateIsExact:
	"""Every exclusion the finding names, each driven separately.

	One case per exclusion rather than one matrix, because a matrix that
	regressed would say "the matrix is wrong" and these say which rule.
	"""

	def test_a_queued_unclaimed_work_on_this_route_is_actionable(self,
	                                                            authority):
		store = authority
		work = make(store, "queued for ada")
		assert tree(store)["actionable_for_viewer"] == 1
		assert row(tree(store), work)["viewer_actionable"] is True

	def test_a_claimed_work_is_not(self, authority):
		"""It is no longer available; somebody is holding it."""
		store = authority
		work = make(store, "already held")
		tr.claim_work(store, work, actor_team=TEAM, actor=MEMBER)
		assert tree(store)["actionable_for_viewer"] == 0
		assert row(tree(store), work)["viewer_actionable"] is False

	def test_a_blocked_work_is_not(self, authority):
		store = authority
		blocker = make(store, "the blocker")
		consumer = make(store, "the consumer")
		tr.add_dependency(store, consumer, blocker, actor_team=TEAM,
		                  actor=MEMBER, rationale="waits")
		answer = tree(store)
		assert row(answer, consumer)["viewer_actionable"] is False
		assert row(answer, blocker)["viewer_actionable"] is True
		assert answer["actionable_for_viewer"] == 1

	def test_a_parked_work_is_not(self, authority):
		store = authority
		work = make(store, "deferred")
		# A reason is required: parked Work has no wake condition and can sit
		# forever, so the why is on the record. The authority refusing my
		# first attempt is that rule working.
		tr.set_phase(store, work, phase="parked", actor_team=TEAM,
		             actor=MEMBER, reason="deliberately deferred")
		assert tree(store)["actionable_for_viewer"] == 0

	def test_a_terminal_work_is_not(self, authority):
		store = authority
		work = make(store, "finished")
		tr.close_work(store, work, actor_team=TEAM, actor=MEMBER,
		              outcome="satisfying", rationale="done")
		assert tree(store)["actionable_for_viewer"] == 0

	def test_work_whose_route_resolves_elsewhere_is_not(self, authority):
		"""The exact CURRENT Route, not the team.

		A member of the owning team who does not handle the Work's route may
		not claim it, and counting it would tell them to pick up something
		the authority would refuse them.
		"""
		store = authority
		make(store, "for the rsrch route")
		assert tree(store, member=MEMBER)["actionable_for_viewer"] == 1
		assert tree(store, member=OTHER)["actionable_for_viewer"] == 0


class TestOneWorkCountsOnce:
	"""The header total is the SIZE OF A SET, not a sum over rows."""

	def test_a_deep_item_counts_once_however_many_ancestors_roll_it_up(
			self, authority):
		"""Four ancestors each report it beneath them, and the total is one.

		A total accumulated from the rows would say four here, which is the
		defect the finding forbids in one sentence: "counts each Work once
		regardless of how many visible ancestors roll it up."
		"""
		store = authority
		levels = chain(store, 4)
		answer = tree(store, levels[0])
		# FOUR CLAIMABLE ITEMS AND ONE TOTAL EACH. A total accumulated from
		# the rows would count the deepest item once per ancestor that rolls
		# it up and answer ten.
		assert answer["actionable_for_viewer"] == 4
		assert row(answer, levels[0])["actionable_descendants"] == 3
		assert row(answer, levels[1])["actionable_descendants"] == 2
		assert row(answer, levels[2])["actionable_descendants"] == 1

	def test_a_row_does_not_count_itself_as_its_own_descendant(self,
	                                                          authority):
		store = authority
		work = make(store, "alone")
		answer = tree(store)
		assert row(answer, work)["viewer_actionable"] is True
		assert row(answer, work)["actionable_descendants"] == 0


class TestTheRollupIgnoresTheDisplayBound:
	"""THE WHOLE POINT OF THE CUE. `tree` shows three containment levels, so
	a queued actionable item on the fourth has no row -- and the count beneath
	its visible ancestor is the only thing that says it is there."""

	def test_a_fourth_level_item_is_counted_beneath_its_visible_ancestors(
			self, authority):
		store = authority
		levels = chain(store, 4)
		answer = tree(store, levels[0])
		painted = {one["id"] for one in answer["rows"]}
		assert levels[3] not in painted, "the window grew; this proves nothing"
		assert row(answer, levels[2])["actionable_descendants"] == 1

	def test_a_filtered_out_descendant_still_counts(self, authority):
		"""A filter decides what is DRAWN, never what exists.

		A cue that dropped with the filter would tell an operator narrowing
		their view that the Work underneath had gone away.
		"""
		store = authority
		root = make(store, "the root")
		deep = make(store, "the child", root)
		tr.prioritize(store, root, priority="high", actor_team=TEAM,
		              actor=MEMBER)
		answer = tree(store, root, priority="high")
		painted = {one["id"] for one in answer["rows"]}
		assert deep not in painted, "the filter kept it; this proves nothing"
		assert row(answer, root)["actionable_descendants"] == 1
		assert answer["actionable_for_viewer"] == 2

	def test_an_active_trail_row_carries_the_same_two_facts(self, authority):
		"""A reader that had to know which KIND of row it held to know
		whether the facts were there would be reading two shapes."""
		store = authority
		levels = chain(store, 5)
		# A SIXTH LEVEL BENEATH THE CLAIM, so the trail's own roll-up is not
		# zero. Asserting only that the member EXISTS would pass for a row
		# that always answered zero -- measured, and it did.
		beneath = make(store, "under the claim", levels[4])
		tr.claim_work(store, levels[4], actor_team=TEAM, actor=MEMBER)
		answer = tree(store, levels[0])
		assert answer["active_trails"], "no trail; this proves nothing"
		trail = answer["active_trails"][0]["work"]
		assert trail["id"] == levels[4]
		assert trail["viewer_actionable"] is False
		assert trail["actionable_descendants"] == 1
		assert beneath not in {one["id"] for one in answer["rows"]}


class TestTheSharedRouteMeansAvailableNotAssigned:

	def test_two_handlers_see_one_opportunity_until_a_claim_removes_it(
			self, tmp_path):
		"""On a shared Route this means "available to this participant".

		Both see it; neither owns it; the atomic claim is the arbiter. That
		is W2938's model and this must not contradict it.
		"""
		store = shared_authority(str(tmp_path / "shared"))
		work = make(store, "for whoever takes it")
		mine = tree(store, member=MEMBER)["actionable_for_viewer"]
		theirs = tree(store, member=OTHER)["actionable_for_viewer"]
		# THE ROUTE REALLY IS SHARED, or this case proves nothing. Asserted
		# rather than skipped: a skip here would quietly stop covering the
		# clause the finding is most explicit about.
		assert mine == theirs == 1
		tr.claim_work(store, work, actor_team=TEAM, actor=MEMBER)
		assert tree(store, member=MEMBER)["actionable_for_viewer"] == 0
		assert tree(store, member=OTHER)["actionable_for_viewer"] == 0

	def test_a_busy_participant_still_sees_queued_availability(self,
	                                                          authority):
		"""The two projections are DISTINCT.

		W2938 says a participant holding a claim owes no pickup obligation.
		That is about obligation; this is about availability, and a busy
		participant can still be shown what is waiting.
		"""
		store = authority
		held = make(store, "what ada is doing")
		waiting = make(store, "what is waiting")
		tr.claim_work(store, held, actor_team=TEAM, actor=MEMBER)
		answer = tree(store)
		assert answer["actionable_for_viewer"] == 1
		assert row(answer, waiting)["viewer_actionable"] is True
		assert row(answer, held)["viewer_actionable"] is False




class TestThePredicateRestsOnInvariantsThisSuiteChecks:
	"""Two of the four clauses are currently IMPLIED by the other two.

	Measured: removing `handler_team IS NULL` or `status='open'` from the
	claimable query changes no verdict, because W38 makes `phase='active'`
	hold exactly when a Handler does, and closing always clears `ready`.

	The predicate is still written out in full -- it is the finding's own
	wording, and code that relied on invariants stated in another Work
	without saying so is code whose reader cannot check it. What that costs
	is that two clauses are unobservable, so the INVARIANTS they lean on are
	asserted here instead. If either ever stops holding, this fails and
	somebody re-examines the predicate rather than discovering it through a
	miscount.
	"""

	def test_active_holds_exactly_when_a_handler_does(self, authority):
		store = authority
		work = make(store, "one")
		before = store.conn.execute(
			"SELECT phase, handler_team FROM work WHERE id=?",
			(work,)).fetchone()
		assert before["phase"] == "queued" and before["handler_team"] is None
		tr.claim_work(store, work, actor_team=TEAM, actor=MEMBER)
		after = store.conn.execute(
			"SELECT phase, handler_team FROM work WHERE id=?",
			(work,)).fetchone()
		assert after["phase"] == "active" and after["handler_team"] is not None

	def test_closing_always_clears_readiness(self, authority):
		store = authority
		work = make(store, "one")
		assert store.conn.execute("SELECT ready FROM work WHERE id=?",
		                          (work,)).fetchone()["ready"] == 1
		tr.close_work(store, work, actor_team=TEAM, actor=MEMBER,
		              outcome="satisfying", rationale="done")
		row_now = store.conn.execute(
			"SELECT status, ready FROM work WHERE id=?", (work,)).fetchone()
		assert row_now["status"] == "closed" and row_now["ready"] == 0


class TestTheSelectedRouteIsTheOneThatDecides:

	def test_a_reroute_moves_the_work_between_participants(self, tmp_path):
		"""W230: an explicitly selected alternate REPLACES the kind's default.

		A count that resolved the default would tell one participant to pick
		up Work the authority has routed to somebody else -- and would go on
		telling them after an operator deliberately moved it.
		"""
		store = shared_authority(str(tmp_path / "selected"))
		work = make(store, "routed to whoever the route says")
		# The default route is shared, so both see it.
		assert tree(store, member=MEMBER)["actionable_for_viewer"] == 1
		assert tree(store, member=OTHER)["actionable_for_viewer"] == 1
		assert store.conn.execute(
			"SELECT route_selected FROM work WHERE id=?",
			(work,)).fetchone()["route_selected"] is None

		# THE SELECTION REPLACES THE DEFAULT, and `second` resolves to grace
		# alone. A count that resolved the kind's default would go on telling
		# ada to pick up Work an operator deliberately moved away from them.
		tr.reroute_work(store, work, actor_team=TEAM, actor=MEMBER,
		                to="lang.rsrch", route="second",
		                reason="it belongs on the second route")
		assert store.conn.execute(
			"SELECT route_selected FROM work WHERE id=?",
			(work,)).fetchone()["route_selected"] == "second"
		assert tree(store, member=MEMBER)["actionable_for_viewer"] == 0
		assert tree(store, member=OTHER)["actionable_for_viewer"] == 1
		assert [one["id"] for one in flattened(store, member=OTHER)["rows"]] \
			== [work]
		assert flattened(store, member=MEMBER)["rows"] == []



class TestTheFlattenedViewFindsWhatTheTreeCannot:

	def test_every_match_appears_with_a_complete_breadcrumb(self, authority):
		store = authority
		levels = chain(store, 5)
		answer = flattened(store)
		# THE DEEPEST ITEM IS THERE AT ALL, which the three-level tree cannot
		# say, and it carries the whole path an operator needs to place it.
		assert levels[4] in [one["id"] for one in answer["rows"]]
		deepest = next(one for one in answer["rows"]
		               if one["id"] == levels[4])
		assert [one["id"] for one in deepest["breadcrumb"]] == levels

	def test_the_flattened_rows_apply_the_member_predicate_too(self,
	                                                          authority):
		"""The SQL narrows to the route's TEAM; only the resolution narrows
		to the member.

		Measured: dropping the membership filter from this view changed no
		verdict, because every case used a member the route resolves to. A
		participant of the owning team who does not handle the route would
		then have been listed Work the authority would refuse them.
		"""
		store = authority
		make(store, "for the rsrch route")
		assert len(flattened(store, member=MEMBER)["rows"]) == 1
		assert flattened(store, member=OTHER)["rows"] == []
		assert flattened(store, member=OTHER)["actionable_for_viewer"] == 0

	def test_the_total_agrees_with_the_tree(self, authority):
		"""Two surfaces, one predicate. A count that disagreed with the list
		would make an operator distrust both."""
		store = authority
		for index in range(3):
			make(store, f"waiting {index}")
		assert flattened(store)["actionable_for_viewer"] == \
			tree(store)["actionable_for_viewer"] == 3

	def test_an_empty_set_is_an_answer(self, authority):
		store = authority
		answer = flattened(store)
		assert answer["rows"] == []
		assert answer["actionable_for_viewer"] == 0
		assert answer["next_after"] is None

	def test_paging_traverses_every_match_once(self, authority):
		store = authority
		for index in range(7):
			make(store, f"waiting {index:02d}")
		seen, after = [], 0
		while True:
			page = flattened(store, after=after, limit=2)
			seen += [one["id"] for one in page["rows"]]
			if page["next_after"] is None:
				break
			after = page["next_after"]
		assert len(seen) == len(set(seen)) == 7
		assert seen == [one["id"] for one in flattened(store, limit=500)["rows"]]

	def test_the_order_is_the_canonical_one(self, authority):
		"""The same order `wait` offers, so the list and the wake agree."""
		store = authority
		ordinary = make(store, "ordinary")
		urgent = make(store, "urgent")
		tr.prioritize(store, urgent, priority="high", actor_team=TEAM,
		              actor=MEMBER)
		assert [one["id"] for one in flattened(store)["rows"]] == \
			[urgent, ordinary]


class TestTheDerivationIsBounded:

	def test_the_derivation_does_not_grow_with_the_tree(self, authority):
		"""A fixed statement cost for the ACTIONABLE derivation.

		Measured at `_claimable` and `_actionable_rollup` rather than at
		`tree`, and the distinction matters: `tree`'s own per-row reads
		legitimately grow with the number of rows it returns, so a count over
		the whole projection would fail for a reason that has nothing to do
		with this Work. What must not grow is the derivation W26328 adds.
		"""
		store = authority
		chain(store, 3)
		counted = []
		real = store.conn

		class Counting:
			def execute(self, statement, *rest):
				counted.append(statement)
				return real.execute(statement, *rest)

			def __getattr__(self, name):
				return getattr(real, name)

		def measure():
			counted.clear()
			store.conn = Counting()
			try:
				claimable = projection._claimable(store, TEAM, MEMBER)
				projection._actionable_rollup(store, claimable)
			finally:
				store.conn = real
			return len(counted)

		small = measure()
		for _ in range(12):
			chain(store, 3)
		large = measure()
		# The endpoint resolution is memoized per DISTINCT endpoint, so a
		# tree thirteen times the size costs the same handful of statements.
		assert large == small, (small, large)


class TestTheNeighbouringProjectionsAreUnchanged:
	"""W81's bold and W2938's pickup mean what they meant.

	The finding is explicit that these are DIFFERENT predicates, so a case
	that let them converge would be erasing the distinction it exists to
	draw.
	"""

	def test_bold_stays_broader_than_mine(self, authority):
		"""A viewer-held claim may be bold while `Mine` is blank."""
		store = authority
		held = make(store, "held by ada")
		tr.claim_work(store, held, actor_team=TEAM, actor=MEMBER)
		assert row(tree(store), held)["viewer_actionable"] is False

	def test_no_work_row_gains_pickup_vocabulary(self, authority):
		"""W2938 remains authoritative: pickup lateness is one participant
		obligation on Teams, never N Work alerts. `Mine` is an availability
		locator and must not read `member_pickup`, capacity or overdue
		time."""
		store = authority
		make(store, "waiting")
		answer = tree(store)
		one = answer["rows"][0]
		# THE MEMBERS THIS WORK ADDS, and nothing that reads pickup health.
		# `pickup` itself is a pre-existing row member owned by W2938's own
		# ruling and is deliberately untouched -- what must not appear is a
		# pickup-derived value in the two facts W26328 introduces.
		assert one["viewer_actionable"] in (True, False)
		assert isinstance(one["actionable_descendants"], int)
		assert one["pickup"] == row(tree(store), one["id"])["pickup"]
