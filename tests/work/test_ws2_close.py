"""WS-2 group 1: universal terminal outcomes, immutable closure, follow-up.

The pinned rules (FINDING.md, 2026-08-14): every terminal close names
exactly `satisfying` or `non-satisfying`, universally; either outcome ends
the provider gate without touching any consumer's Current, classification,
or status; closure is immutable — no reopen exists anywhere; later evidence
is follow-up Work, non-gating, the one new reference closed Work accepts;
new blockers target only open Work.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store
	store.close()


def _create(store, team="lang", member="ada", **kw):
	kw.setdefault("classification", "suspected-defect")
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", author=member,
	                      body="b", **kw)["work_id"]


def _row(store, work):
	return store.conn.execute("SELECT * FROM work WHERE id=?",
	                          (work,)).fetchone()


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


# -- universal terminal outcomes ---------------------------------------------

def test_every_close_names_exactly_one_canonical_outcome(world):
	store = world
	work = _create(store)
	for bad in (None, "fixed", "satisfying-ish", ""):
		with pytest.raises(bw.WorkError, match="exactly one outcome"):
			tr.close_work(store, work, actor_team="lang", actor="ada",
			              rationale="done", outcome=bad)
	assert _row(store, work)["status"] == "open", "a refusal closed"
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="did not pan out", outcome="non-satisfying")
	row = _row(store, work)
	assert row["outcome"] == "non-satisfying"
	closing = next(e for e in store.events() if e["kind"] == "close_work")
	assert closing["payload"]["outcome"] == "non-satisfying"
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["outcome"] == "non-satisfying"


def test_either_outcome_ends_the_gate_and_mutates_no_consumer(world):
	"""The provider's terminal result returns the decision to each
	consumer's court: last-gate waiters wake, multi-gate waiters hold, and
	nobody's Current, classification, or status moves."""
	store = world
	for outcome in ("satisfying", "non-satisfying"):
		provider = _create(store)
		# Born 'limitation' so the explicit classify below records a real
		# change (creation now requires a concrete value, fresh schema).
		consumer = _create(store, team="push", member="sl",
		                   classification="limitation")
		other_gate = _create(store, team="push", member="sl")
		holder = _create(store, team="push", member="sl")
		tr.add_dependency(store, consumer, provider,
		                  actor_team="push", actor="sl", rationale="test dependency")
		tr.add_dependency(store, holder, provider,
		                  actor_team="push", actor="sl", rationale="test dependency")
		tr.add_dependency(store, holder, other_gate,
		                  actor_team="push", actor="sl", rationale="test dependency")
		tr.classify(store, consumer, actor_team="push", actor="sl",
		            classification="suspected-defect")
		tr.set_phase(store, consumer, actor_team="push", actor="sl",
		             phase="waiting", wait="gates")
		tr.set_phase(store, holder, actor_team="push", actor="sl",
		             phase="waiting", wait="gates")

		closing = tr.close_work(store, provider, actor_team="lang",
		                        actor="ada", rationale="terminal",
		                        outcome=outcome)
		woken = _row(store, consumer)
		assert woken["ready"] == 1 and woken["phase"] == "queued", \
			f"a {outcome} close did not end the gate"
		assert woken["status"] == "open"
		assert woken["classification"] == "suspected-defect"
		assert (woken["route_team"], woken["route_kind"]) == \
			("push", "bug"), "the provider result moved a consumer's Current"
		held = _row(store, holder)
		assert held["phase"] == "waiting" and held["ready"] == 0, \
			"a consumer with another open gate was woken"
		wakes = [e for e in store.events() if e["kind"] == "wake" and
		         e["payload"]["work"] == consumer]
		assert len(wakes) == 1 and wakes[0]["seq"] == closing["seq"] + 1
		# The consumer can SEE the result where its dependency points.
		links = pj.links(store, consumer)
		assert links["blocked_by"][0]["outcome"] == outcome
		tr.close_work(store, other_gate, actor_team="push", actor="sl",
		              rationale="cleanup", outcome="satisfying")
		tr.close_work(store, holder, actor_team="push", actor="sl",
		              rationale="cleanup", outcome="satisfying")
		tr.close_work(store, consumer, actor_team="push", actor="sl",
		              rationale="cleanup", outcome="satisfying")


# -- immutable closure -------------------------------------------------------

def test_closed_work_refuses_every_mutation_but_keeps_reads_and_seen(world):
	store = world
	work = _create(store)
	blocker = _create(store)
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	baseline = store.events()
	with pytest.raises(bw.WorkError):
		fx.post(store, work, author_team="lang", author="ada",
		                body="late words")
	with pytest.raises(bw.WorkError):
		tr.classify(store, work, actor_team="lang", actor="ada",
		            classification="duplicate")
	with pytest.raises(bw.WorkError):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="queued")
	with pytest.raises(bw.WorkError):
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="again", outcome="satisfying")
	with pytest.raises(bw.WorkError):
		tr.create_work(store, team="lang", kind="bug", title="child",
		               origin="decomposition", classification="suspected-defect", author="ada", body="b",
		               parent=work)
	with pytest.raises(bw.WorkError):
		tr.add_dependency(store, work, blocker,
		                  actor_team="lang", actor="ada", rationale="test dependency")
	assert store.events() == baseline, "a refusal mutated closed history"
	# Reads and personal seen state remain.
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["available_transitions"] == []
	pj.links(store, work)
	marked = fx.mark_all_seen(store, work, team="lang", member="grace",
	                      up_to_seq=store.last_seq())
	assert marked["kind"] == "mark_seen", \
		"closed history cannot be marked read"


def test_no_reopen_surface_remains_anywhere(world):
	store = world
	assert not hasattr(tr, "reopen_work")
	work = _create(store)
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	for team, member in (("lang", "ada"), ("lang", "grace"),
	                     ("push", "sl")):
		detail = pj.detail(store, work, viewer_team=team,
		                   viewer_member=member)
		assert "reopen" not in detail["available_transitions"]
	assert not any(event["kind"] == "reopen_work"
	               for event in store.events())


def test_terminal_close_never_leaves_a_classic_obligation_actionable(world):
	"""Closed Work refuses new carrying obligation activity. The authority
	may refuse close until a classic @ is discharged, or terminate it as part
	of close, but it must never commit closed Work with a pending obligation
	that can append a later response to immutable history."""
	store = world
	work = _create(store)
	request = fx.post(
		store, work, author_team="lang", author="ada", body="please test",
		request="push.bug")
	before = store.events()
	try:
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="concluded", outcome="non-satisfying")
	except bw.WorkError:
		assert _row(store, work)["status"] == "open"
		assert store.events() == before, "a refused close partially committed"
		return

	obligation = store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(request["seq"],)).fetchone()
	assert obligation["status"] != "pending", \
		"terminal close left an @ obligation actionable on closed Work"
	with pytest.raises(bw.WorkError):
		tr.respond_obligation(store, request["seq"], team="push", member="sl",
		                      body="late response")


# -- follow-up ---------------------------------------------------------------

def test_follow_up_targets_closed_work_only_and_gates_nothing(world):
	store = world
	work = _create(store)
	with pytest.raises(bw.WorkError, match="still open"):
		_create(store, follow_up_of=work)
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	follow = _create(store, follow_up_of=work)
	row = _row(store, follow)
	assert row["follow_up_of"] == work
	assert row["ready"] == 1, "the follow-up relationship gated"
	# Navigable from BOTH sides, and it names the closed history it keeps.
	graph = pj.links(store, follow)
	assert graph["follow_up_of"]["id"] == work
	assert graph["follow_up_of"]["outcome"] == "satisfying"
	back = pj.links(store, work)
	assert [entry["id"] for entry in back["follow_ups"]] == [follow]
	with pytest.raises(bw.WorkError, match="no work"):
		_create(store, follow_up_of="nope-W9")


def test_follow_up_open_targets_refuse_at_the_precheck(world):
	"""R2 correction: the open-target refusal fires at the PRECHECK, before
	any write path opens. Under immutable closure an observed-closed
	predecessor can never become open again, so the in-lock recheck is
	defense in depth rather than a live reverse race — its wiring is
	proven by the break-sweep that removes both layers, not by an
	interleaving this test cannot reach."""
	store = world
	target = _create(store)
	with pytest.raises(bw.WorkError, match="still open"):
		_create(store, follow_up_of=target)


def test_a_blocker_closing_mid_flight_refuses_in_the_lock(world):
	"""New blockers target only OPEN work — revalidated in the lock, where
	a concurrently-closed blocker refuses rather than recording a dead
	dependency."""
	store = world
	dependent = _create(store)
	blocker = _create(store, team="push", member="sl")
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.close_work(
		other, blocker, actor_team="push", actor="sl",
		rationale="closed mid-flight", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="only open Work"):
		tr.add_dependency(store, dependent, blocker,
		                  actor_team="lang", actor="ada", rationale="test dependency")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 0
	other.close()


# -- the group-1 correction: withdrawal at close, races, DEP -----------------

def test_close_withdraws_every_pending_obligation_with_route_visibility(
		world):
	"""One close, two pending @ obligations: both leave the actionable set
	atomically, each withdrawal audited with the recorded route
	accountability, and every late answer refuses."""
	store = world
	work = _create(store)
	first = fx.post(store, work, author_team="lang", author="ada",
	                        body="push: confirm?", request="push.bug")
	second = fx.post(store, work, author_team="lang", author="ada",
	                         body="rev: sanity?", request="lang.rev")
	assert len(pj.obligations(store, viewer_team="push")) == 1
	closing = tr.close_work(store, work, actor_team="lang", actor="ada",
	                        rationale="concluded",
	                        outcome="non-satisfying")
	assert pj.obligations(store, viewer_team="push") == []
	assert pj.obligations(store, viewer_team="lang") == []
	withdrawals = [event for event in store.events()
	               if event["kind"] == "withdraw"]
	assert len(withdrawals) == 2
	assert all(event["seq"] > closing["seq"] for event in withdrawals), \
		"a withdrawal committed outside the closing transaction"
	assert {event["payload"]["endpoint"] for event in withdrawals} == \
		{"push.bug", "lang.rev"}
	for event in withdrawals:
		assert event["payload"]["handlers"], \
			"a withdrawal lost its route accountability"
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.respond_obligation(store, first["seq"], team="push", member="sl",
		                      body="too late")
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.dispose_obligation(store, second["seq"], team="lang",
		                      member="ada", disposition="too late")


def test_withdrawn_obligation_resolves_to_its_withdraw_event(world):
	"""resolved_seq is the direct audit address of an obligation's terminal
	act. A withdrawal therefore points at its own route-visible `withdraw`
	event, not merely at the enclosing close event whose payload does not
	identify this obligation."""
	store = world
	work = _create(store)
	asked = fx.post(
		store, work, author_team="lang", author="ada", body="please test",
		request="push.bug")["seq"]
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="concluded", outcome="satisfying")
	obligation = store.conn.execute(
		"SELECT resolved_seq FROM obligations WHERE seq=?", (asked,)).fetchone()
	resolved = next(event for event in store.events()
	                if event["seq"] == obligation["resolved_seq"])
	assert resolved["kind"] == "withdraw"
	assert resolved["payload"]["obligation"] == asked


def test_the_answer_versus_close_race_serializes_both_ways(world):
	"""Exactly one legal serialization commits: a close landing between an
	answer's precheck and its lock withdraws the obligation and the answer
	refuses; an answer landing inside the close's window is kept — the
	close withdraws only what is still pending."""
	store = world
	# Serialization 1: close wins; the late respond refuses.
	work = _create(store)
	asked = fx.post(store, work, author_team="lang", author="ada",
	                        body="push?", request="push.bug")["seq"]
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.close_work(
		other, work, actor_team="lang", actor="ada",
		rationale="closed first", outcome="non-satisfying"))
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.respond_obligation(store, asked, team="push", member="sl",
		                      body="racing answer")
	messages = store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages JOIN threads "
		"ON threads.id = messages.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=?", (work,)).fetchone()["n"]
	assert messages == 2, "the losing answer appended to closed history"

	# Serialization 2: the answer wins; the close keeps it and withdraws
	# nothing.
	work2 = _create(store)
	asked2 = fx.post(store, work2, author_team="lang", author="ada",
	                         body="push?", request="push.bug")["seq"]
	_interleave(store, lambda: tr.respond_obligation(
		other, asked2, team="push", member="sl", body="answered first"))
	tr.close_work(store, work2, actor_team="lang", actor="ada",
	              rationale="closed second", outcome="satisfying")
	row = store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?", (asked2,)).fetchone()
	assert row["status"] == "responded", \
		"the close overwrote a committed answer with a withdrawal"
	assert not [event for event in store.events()
	            if event["kind"] == "withdraw" and
	            event["payload"]["work"] == work2]
	other.close()


def test_dep_counts_only_live_dependents_and_the_drill_matches(world):
	"""DEP is the provider's LIVE load: open dependents only. Closing a
	consumer removes it from the count and the drill without deciding
	anything on the provider; the journal keeps the edge acts."""
	store = world
	provider = _create(store)
	dependents = [_create(store, team="push", member="sl")
	              for _ in range(3)]
	for dependent in dependents:
		tr.add_dependency(store, dependent, provider,
		                  actor_team="push", actor="sl", rationale="test dependency")
	view = pj.detail(store, provider, viewer_team="lang",
	                 viewer_member="ada")
	assert view["open_dependents"] == 3
	assert [entry["id"] for entry in view["links"]["blocks"]] == dependents

	tr.close_work(store, dependents[1], actor_team="push", actor="sl",
	              rationale="fixed our side", outcome="satisfying")
	view = pj.detail(store, provider, viewer_team="lang",
	                 viewer_member="ada")
	assert view["open_dependents"] == 2, "a closed consumer still counts as live load"
	assert [entry["id"] for entry in view["links"]["blocks"]] == \
		[dependents[0], dependents[2]], "the drill kept a closed consumer"
	# The consumer's closure decided NOTHING on the provider...
	assert view["status"] == "open" and view["phase"] == "queued"
	assert view["classification"] == "suspected-defect"
	# ...and the journal retains every edge act for history.
	edge_acts = [event for event in store.events()
	             if event["kind"] == "add_dependency"]
	assert len(edge_acts) == 3


def test_dep_counter_and_drill_share_one_detail_snapshot(world, monkeypatch):
	"""One canonical detail response cannot say DEP=1 while drilling the
	adjacent field yields no dependent. A consumer close racing between the
	counter and list reads must appear wholly before or wholly after them."""
	store = world
	provider = _create(store)
	consumer = _create(store, team="push", member="sl")
	tr.add_dependency(store, consumer, provider,
	                  actor_team="push", actor="sl", rationale="test dependency")
	other = bw.Authority(store.path)
	original = pj._row_view
	raced = False

	def close_between_counter_and_drill(*args, **kwargs):
		nonlocal raced
		view = original(*args, **kwargs)
		if not raced and view["id"] == provider:
			raced = True
			tr.close_work(other, consumer, actor_team="push", actor="sl",
			              rationale="resolved locally",
			              outcome="satisfying")
		return view

	monkeypatch.setattr(pj, "_row_view", close_between_counter_and_drill)
	view = pj.detail(store, provider, viewer_team="lang", viewer_member="ada")
	assert view["open_dependents"] == len(view["links"]["blocks"]), \
		"one detail snapshot disagrees about its live dependents"
	other.close()
