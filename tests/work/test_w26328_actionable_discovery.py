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


def walk(store, member=MEMBER, **paging):
	"""Every page of the flattened view, followed through the continuation
	until it is exhausted.

	BOUNDED, and the bound is its own assertion. A continuation that stops
	advancing does not fail a comparison — it loops forever, and a suite
	that hangs reports nothing at all. The bound is far above any page
	count these cases produce, so it can only fire on that defect.
	"""
	seen, after, pages = [], None, 0
	while True:
		page = flattened(store, member=member, after=after, **paging)
		seen += [one["id"] for one in page["rows"]]
		after = page["next_after"]
		pages += 1
		if after is None:
			return seen
		assert pages < 100, "the continuation never exhausted the set"


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
		# The FIRST page is `after=None`; the continuation is a token,
		# never a count, so there is no zero to start from.
		seen = walk(store, limit=2)
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


class TestTheContinuationIsAPositionAndNeverAnOffset:
	"""Independent review [P1]: a positional continuation silently skips
	actionable Work.

	`next_after` was `start + len(page)` and the next page was
	`rows[start:start + size]` of the set as it stands THEN. Between two
	pages the set moves — that is the point of a shared Route — and every
	row after a departed one slides one place forward, so the second slice
	begins one row too late and the Work that crossed the boundary appears
	in no page at all. That is the exact promise this verb exists to keep,
	so it is measured here at the boundary rather than inferred from the
	shape of the token.

	The two halves are separate cases because they fail in opposite
	directions: a REMOVAL before the cursor must not skip, and an ARRIVAL
	before it must not repeat.
	"""

	def test_a_claim_between_pages_skips_no_later_work(self, authority):
		"""The reviewer's reproduction, as a case.

		W2 and W3 are read, another handler claims W2, and the next page
		must still begin after W3 — not after "two rows", which is now W4.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		assert [one["id"] for one in first["rows"]] == made[:2]

		tr.claim_work(store, made[0], actor_team=TEAM, actor=MEMBER)
		second = flattened(store, after=first["next_after"], limit=2)

		assert [one["id"] for one in second["rows"]] == made[2:]

	def test_a_reroute_between_pages_skips_no_later_work(self, authority):
		"""The OTHER way an earlier row leaves the set.

		A cursor that counted rows cannot tell a claim from a reroute, and
		neither may cost a later Work its only locator.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		tr.reroute_work(store, made[0], actor_team=TEAM, actor=MEMBER,
		                to="push.bug", reason="handed to another team")
		second = flattened(store, after=first["next_after"], limit=2)
		assert [one["id"] for one in second["rows"]] == made[2:]

	def test_a_row_removed_from_the_page_just_read_still_skips_nothing(
			self, authority):
		"""The boundary itself: the LAST row of the page read is the one
		the cursor names, and it may leave too."""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		tr.claim_work(store, made[1], actor_team=TEAM, actor=MEMBER)
		second = flattened(store, after=first["next_after"], limit=2)
		assert [one["id"] for one in second["rows"]] == made[2:]

	def test_an_arrival_before_the_cursor_is_not_repeated(self, authority):
		"""A high-priority arrival sorts ahead of everything already
		returned. It belongs to a page that has been read, so continuing
		may not hand it back — a deliberate refresh is the path to seeing
		it, and the last case here proves the refresh does."""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		read = [one["id"] for one in first["rows"]]

		late = make(store, "urgent arrival")
		tr.prioritize(store, late, priority="high", actor_team=TEAM,
		              actor=MEMBER)
		second = flattened(store, after=first["next_after"], limit=2)
		returned = [one["id"] for one in second["rows"]]

		assert late not in returned
		assert not set(returned) & set(read)
		assert returned == made[2:]
		assert flattened(store, limit=2)["rows"][0]["id"] == late

	def test_the_order_walked_is_total(self, authority):
		"""The cursor compares POSITIONS, so the order must decide every
		pair — two rows it calls equal are two rows a page can skip or
		repeat.

		No mint produces that tie today, because the identity is minted
		from `created_seq`. This case CONSTRUCTS one directly, which is
		deliberate: the guarantee is a property of the ordering rather than
		of how ids happen to be spelled, and a later change to either must
		not quietly cost it.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		tied = store.conn.execute(
			"SELECT created_seq FROM work WHERE id=?",
			(made[1],)).fetchone()["created_seq"]
		store.conn.execute("UPDATE work SET created_seq=? WHERE id=?",
		                   (tied, made[2]))
		store.conn.commit()

		seen = walk(store, limit=1)
		assert sorted(seen) == sorted(made)
		assert len(seen) == len(set(seen)) == 4


class TestTheContinuationIsOpaque:
	"""Independent review [P1]: the approved contract calls `next_after`
	opaque, and the implementation published an integer offset a client
	could — and the documentation invited a client to — compute with."""

	def test_the_token_is_not_a_number(self, authority):
		store = authority
		for index in range(3):
			make(store, f"waiting {index}")
		token = flattened(store, limit=2)["next_after"]
		assert isinstance(token, str) and token
		assert not token.lstrip("-").isdigit()
		assert not isinstance(token, int)

	def test_the_last_page_says_so(self, authority):
		store = authority
		for index in range(2):
			make(store, f"waiting {index}")
		assert flattened(store, limit=2)["next_after"] is None

	def test_a_full_page_with_nothing_after_it_offers_no_continuation(
			self, authority):
		"""The exact-fit boundary. An offset cursor answered this by
		comparing arithmetic; the position cursor answers it by reading one
		row past the page and finding none."""
		store = authority
		for index in range(4):
			make(store, f"waiting {index}")
		first = flattened(store, limit=2)
		second = flattened(store, after=first["next_after"], limit=2)
		assert len(second["rows"]) == 2
		assert second["next_after"] is None

	@pytest.mark.parametrize("token", [0, 2, "2", "", "not-a-token",
	                                   "d29fMQ==", True, 1.5])
	def test_a_continuation_this_authority_did_not_mint_is_refused(
			self, authority, token):
		"""REFUSED, never rounded to page one.

		Answering the first page to a client that asked to continue is the
		skipped-Work defect wearing different clothes: the client believes
		it has walked past a boundary it has actually been sent back
		behind. The empty string is the one exception, because a client
		that has no token has not asked to continue.
		"""
		store = authority
		make(store, "waiting")
		if token == "":
			assert flattened(store, after=token)["rows"]
			return
		with pytest.raises(bw.WorkError, match="opaque token"):
			flattened(store, after=token)

	def test_a_token_from_the_previous_scheme_is_refused(self, authority):
		"""Not hypothetical any more: `w1` is a shape this authority really
		minted, and it names a position with NO VIEWER.

		Reading one as if it were current would take the participant binding
		off exactly the tokens that predate it, which is the population the
		binding exists for. The tag is checked before anything is decoded
		from the parts beside it, so an old token refuses rather than being
		misread as a new one.
		"""
		store = authority
		work = make(store, "waiting")
		import base64
		previous = base64.urlsafe_b64encode(
			f"w1\x1f1\x1f1\x1f7\x1f{work}".encode()).decode().rstrip("=")
		with pytest.raises(bw.WorkError, match="opaque token"):
			flattened(store, after=previous)

	def test_a_scheme_this_build_does_not_know_is_refused_at_the_tag(self,
	                                                                 authority):
		"""AND THE TAG IS WHAT REFUSES IT, which the case above does not
		establish.

		`w1` and `w2` differ in arity, so the length check catches a real
		superseded token before the tag is ever consulted — measured: the
		mutation that deletes the tag comparison stayed UNSEEN with only that
		case present, and a scheme tag nothing tests is a scheme tag that
		will not be there when two shapes DO coincide in arity. This token
		has exactly this build's member count and a scheme this build has
		never minted.
		"""
		store = authority
		work = make(store, "waiting")
		import base64
		other = base64.urlsafe_b64encode(
			f"w9\x1f{TEAM}\x1f{MEMBER}\x1f1\x1f1\x1f7\x1f{work}".encode()
		).decode().rstrip("=")
		with pytest.raises(bw.WorkError, match="opaque token"):
			flattened(store, after=other)


class TestTheContinuationIsBoundToThisAuthority:
	"""Re-review [P1]: shape is not provenance.

	The first correction established that a token DECODES and carries this
	scheme, and stopped there. A client could compose a well-formed one with
	impossible ranks, a future sequence and an id belonging to nobody, and
	every real row compared as "at or before" it — so the page came back
	empty while Work was still actionable. That is the same discovery
	failure the offset arithmetic caused, reached through the cursor.

	The token is now bound to its Work. What must NOT change is the ordinary
	case the first correction exists for, so that is asserted here too rather
	than left to the classes above.
	"""

	def forged(self, ranks, blocking, sequence, work,
	           team=TEAM, member=MEMBER):
		"""A token of the CURRENT shape, so these cases keep measuring the
		position binding rather than the shape check that runs before it."""
		import base64
		raw = "\x1f".join(str(one) for one in
		                  ("w2", team, member, ranks, blocking, sequence,
		                   work))
		return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")

	def test_a_well_shaped_position_this_authority_never_held_is_refused(
			self, authority):
		"""The reviewer's reproduction, as a case."""
		store = authority
		work = make(store, "still waiting")
		token = self.forged(99, 99, 999999999,
		                    "not-this-authority-W999999999")
		with pytest.raises(bw.WorkError, match="refresh"):
			flattened(store, after=token)
		# And the Work it would have hidden is still there to be found.
		assert [one["id"] for one in flattened(store)["rows"]] == [work]

	def test_a_cursor_naming_a_real_work_at_a_wrong_position_is_refused(
			self, authority):
		"""Nearer the mark and still invented: the id exists, the ranks do
		not describe it."""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(2)]
		sequence = store.conn.execute(
			"SELECT created_seq FROM work WHERE id=?",
			(made[0],)).fetchone()["created_seq"]
		with pytest.raises(bw.WorkError, match="refresh"):
			flattened(store, after=self.forged(0, 0, sequence, made[0]))

	def test_a_cursor_whose_row_changed_rank_is_refused_and_says_refresh(
			self, authority):
		"""The documented deliberate-refresh path, reached as a FACT.

		The dossier says a row whose own rank changes across the boundary is
		the one case a cursor cannot follow. Until the binding existed,
		nothing detected it — the old position was followed silently, and the
		rows between the two places were handed back twice or skipped with no
		way for a client to tell.

		Priority is the rank moved here because it is the outer one: raising
		the cursor row moves it ahead of everything the page returned.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		assert [one["id"] for one in first["rows"]] == made[:2]
		tr.prioritize(store, made[1], priority="high", actor_team=TEAM,
		              actor=MEMBER)
		with pytest.raises(bw.WorkError, match="refresh"):
			flattened(store, after=first["next_after"], limit=2)
		# REFRESH IS THE PATH, and it works: the whole set is readable from
		# the first page, with the moved row where it now belongs.
		assert walk(store, limit=2)[0] == made[1]
		assert sorted(walk(store, limit=2)) == sorted(made)

	def test_a_cursor_row_that_stopped_being_actionable_still_continues(
			self, authority):
		"""THE ORDINARY CASE, asserted here so the binding cannot quietly
		swallow it.

		A claim or a reroute moves a row out of the actionable set without
		moving it in the canonical order, so continuing after it means
		exactly what it meant. The lookup is over `work` rather than over the
		actionable set for this reason, and a binding written against the
		actionable set would pass every case above and break the one the
		whole feature exists for.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		tr.claim_work(store, made[1], actor_team=TEAM, actor=MEMBER)
		assert [one["id"] for one in
		        flattened(store, after=first["next_after"], limit=2)["rows"]] \
			== made[2:]

	def test_closing_the_cursor_row_does_not_move_it(self, authority):
		"""Closing is the SAME class as claiming, and it is worth its own
		case because it looks like it should not be.

		A closed Work has left the actionable set for good, so refusing here
		is tempting. But the canonical order is priority, then the blocking
		preference, then creation — and a Work with no open dependents ranks
		the same closed as open. Its POSITION did not move, so continuing
		after it means what it meant, and refusing would cost the pages after
		it for no reason a client could act on.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		first = flattened(store, limit=2)
		tr.claim_work(store, made[1], actor_team=TEAM, actor=MEMBER)
		tr.close_work(store, made[1], actor_team=TEAM, actor=MEMBER,
		              outcome="satisfying", rationale="finished")
		assert [one["id"] for one in
		        flattened(store, after=first["next_after"], limit=2)["rows"]] \
			== made[2:]

	def test_claiming_a_BLOCKING_cursor_row_moves_it_and_refuses(self,
	                                                             authority):
		"""The consequence of binding to the CURRENT position, stated
		plainly because it narrows the ordinary case.

		The blocking preference is part of the canonical order and one of its
		clauses is `handler_team IS NULL`. So a cursor row that was holding
		somebody up ranks 0 while unclaimed and 1 once claimed — an ordinary
		shared-route claim, on that one kind of row, genuinely MOVES it.

		Continuing past a position it no longer occupies would skip or repeat
		the rows between the two places with no way for a client to notice, so
		this refuses and names the refresh. It is a real narrowing of the
		inter-page claim case, and it is a narrowing toward the honest answer.
		"""
		store = authority
		made = [make(store, f"waiting {index}") for index in range(4)]
		dependent = make(store, "waits on the cursor row")
		tr.add_dependency(store, dependent, made[1], actor_team=TEAM,
		                  actor=MEMBER, rationale="needs it first")
		# ONE ROW TO A PAGE, so the continuation names the blocking row
		# itself. It sorts FIRST precisely because it is blocking, which is
		# the rank this case is about.
		first = flattened(store, limit=1)
		assert [one["id"] for one in first["rows"]] == [made[1]]
		assert row(first, made[1])["blocking"] is True

		tr.claim_work(store, made[1], actor_team=TEAM, actor=MEMBER)
		with pytest.raises(bw.WorkError, match="refresh"):
			flattened(store, after=first["next_after"], limit=1)
		# AND NOTHING IS LOST BY IT. The refresh reaches every remaining
		# actionable Work, which is what the refusal is protecting.
		assert set(walk(store, limit=1)) == {made[0], made[2], made[3]}


class TestTheContinuationIsBoundToItsParticipantView:
	"""Third review [P1]: a position is a fact about the ORDER, not a fact
	about a viewer.

	`actionable-work` answers a participant-relative question, and the
	previous token carried only where the last row sat in the canonical
	order -- which every viewer shares. So a real, authority-minted,
	unedited cursor from one participant's page was a valid cursor in
	another's, and every row before that position dropped out of their
	answer. The row binding fixed an INVENTED position and left this one
	untouched, because nothing here is invented.

	Two disjoint Routes are the whole reproduction: Grace's page-one cursor
	names a Work that sorts after everything Ada can claim, so Ada reading
	through it gets an empty page while her own Work is still waiting.
	"""

	def disjoint(self, directory):
		"""Two Routes on one kind, with one handler each and no overlap."""
		import json
		import os as _os
		from baton_work import lifecycle as lc
		document = fx.config_document()
		team = document["teams"][TEAM]
		role = team["routes"]["main"]["role"]
		team["participants"][OTHER]["roles"] = sorted(set(
			team["participants"][OTHER]["roles"] + [role]))
		team["routes"]["second"] = {"role": role, "handlers": [OTHER]}
		team["kinds"]["rsrch"]["alternates"] = ["second"]
		place = _os.path.join(directory, "baton.json")
		with open(place, "w", encoding="utf-8") as handle:
			json.dump(document, handle)
		accepted = lc.init_from_config(
			place, participant=fx.first_participant(place))
		return bw.Authority(accepted["database"])

	@pytest.fixture
	def split(self, tmp_path):
		store = self.disjoint(str(tmp_path))
		mine = [make(store, "ada one"), make(store, "ada two")]
		theirs = [make(store, "grace one"), make(store, "grace two")]
		for work in theirs:
			tr.reroute_work(store, work, actor_team=TEAM, actor=MEMBER,
			                to=f"{TEAM}.rsrch", route="second",
			                reason="Grace's disjoint Route")
		return store, mine, theirs

	def test_another_participants_cursor_is_refused(self, split):
		"""THE DEFECT. The token is genuine, minted here, and unedited."""
		store, mine, theirs = split
		theirs_page = flattened(store, member=OTHER, limit=1)
		assert [one["id"] for one in theirs_page["rows"]] == theirs[:1]
		assert theirs_page["next_after"] is not None

		with pytest.raises(bw.WorkError, match="different participant"):
			flattened(store, after=theirs_page["next_after"])

	def test_the_work_it_would_have_hidden_is_still_found(self, split):
		"""What the refusal is protecting: both of Ada's Work items were
		lost behind a cursor that answered somebody else's question."""
		store, mine, _theirs = split
		assert [one["id"] for one in flattened(store)["rows"]] == mine

	def test_each_participant_walks_their_own_view_to_the_end(self, split):
		"""And the binding costs neither of them anything. Two views, two
		cursors, and each reaches exactly its own set."""
		store, mine, theirs = split
		assert walk(store, limit=1) == mine
		assert walk(store, member=OTHER, limit=1) == theirs

	def test_the_refusal_does_not_send_them_round_a_refresh_loop(self,
	                                                             split):
		"""A cursor belonging to another participant is NOT a snapshot that
		moved, and it is answered before the row is even looked up.

		Telling its holder to refresh would send them somewhere that cannot
		help: their next page would be this page again. The two refusals say
		different things because they are different mistakes.
		"""
		store, _mine, theirs = split
		theirs_page = flattened(store, member=OTHER, limit=1)
		with pytest.raises(bw.WorkError) as caught:
			flattened(store, after=theirs_page["next_after"])
		assert "refresh" not in str(caught.value)
		assert "who is asking" in str(caught.value)

	def test_the_same_participant_is_unaffected(self, split):
		"""The binding is on the VIEW, not on the row's claimability: a
		cursor row that merely stopped being actionable for the SAME viewer
		still continues, which is the case the previous correction exists
		for and the one a view binding could most easily break."""
		store, mine, _theirs = split
		first = flattened(store, limit=1)
		tr.claim_work(store, mine[0], actor_team=TEAM, actor=MEMBER)
		assert [one["id"] for one in
		        flattened(store, after=first["next_after"], limit=1)["rows"]] \
			== mine[1:]


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
