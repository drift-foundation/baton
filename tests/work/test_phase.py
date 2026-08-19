"""WS-1: public classification and operational phase — the authorized matrix.

Every assertion here traces to the confirmed rulings: never-null canonical
classification, the closed FOUR-state scheduler axis (W38: queued, active,
waiting, parked, with compact values kept presentation-only), Route-handler
transition authority, the special rules (parked, waiting/wake, closed),
typed wake conditions with the atomic single `wake`, and the always-visible
parked count.

W38 note: `active` is not reachable through the phase verb — it means a
handler holds the Work, which only `claim` establishes — and every phase
this verb CAN reach is an unclaimed state, so each one releases.
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


@pytest.fixture
def world(tmp_path):
	# W73: a handoff derives its phase from the destination ROUTE. The
	# generic `main` route stays exactly as it was for every other case
	# here; only lang's `rev` kind gains a reviewer route so that a
	# review handoff still means review.
	spec = {"lang": {"members": {"ada": ["dev", "rview"],
	                             "grace": ["dev", "rview"]},
	                 "kinds": ["bug", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	document = fx.config_document(spec)
	lang = document["teams"]["lang"]
	lang["routes"]["review"] = {"role": "rview",
	                            "handlers": ["ada", "grace"]}
	lang["kinds"]["rev"]["route"] = "review"
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(
		config_path, participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _create(store, team="lang", member="ada", **kw):
	kw.setdefault("classification", "suspected-defect")
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", author=member,
	                      body="b", **kw)["work_id"]


def _row(store, work):
	return store.conn.execute("SELECT * FROM work WHERE id=?",
	                          (work,)).fetchone()


# -- defaults and creation ---------------------------------------------------

def test_creation_defaults_and_explicit_initial_phase(world):
	store, _config = world
	work = _create(store)
	row = _row(store, work)
	assert row["classification"] == "suspected-defect", \
		"the submitted classification is stored verbatim"
	assert row["phase"] == "queued"
	# W38: creation has no phase operand at all. A new Work is open,
	# unclaimed and ungated, so `queued` is the only state it can
	# honestly be in — there is no initial choice left to preserve.
	chosen = _create(store, classification="suspected-defect")
	row = _row(store, chosen)
	assert (row["phase"], row["classification"]) == \
		("queued", "suspected-defect")


def test_creation_refuses_blocked_parked_and_compact_values(world):
	store, _config = world
	# W78: a creation has no live gate, so `block` refuses naming that
	# — the older wording said "wake condition", which was the same
	# refusal under the retired vocabulary.
	for phase, message in (("block", "live gate"),
	                       ("parked", "reason")):
		with pytest.raises(bw.WorkError, match=message):
			_create(store, phase=phase)
	# Compact display vocabulary is NOT a protocol identity.
	with pytest.raises(bw.WorkError, match="presentation"):
		_create(store, phase="queue")
	with pytest.raises(bw.WorkError, match="not one of"):
		_create(store, classification="unkwn")


# -- authorization -----------------------------------------------------------

def test_only_a_resolved_current_handler_may_transition(world):
	"""ada is the route's handler; grace and push.sl hold membership,
	visibility, even @ input — none of which is mutation authority."""
	store, _config = world
	work = _create(store)
	for team, member in (("lang", "grace"), ("push", "sl")):
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.set_phase(store, work, actor_team=team, actor=member,
			             phase="parked", reason="not mine to move")
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.classify(store, work, actor_team=team, actor=member,
			            classification="confirmed-defect")
	assert _row(store, work)["phase"] == "queued", "a refusal mutated"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.classify(store, work, actor_team="lang", actor="ada",
	            classification="confirmed-defect")
	row = _row(store, work)
	assert (row["phase"], row["classification"]) == \
		("active", "confirmed-defect")
	assert row["origin"] == "external-report", "classify touched origin"


def test_reassignment_moves_transition_authority(world):
	"""Accepted handler reassignment changes WHO may perform the next
	transition — the authority follows the live resolution."""
	store, config_path = world
	work = _create(store)
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.claim_work(store, work, actor_team="lang", actor="grace")
	assert _row(store, work)["phase"] == "active"


# -- round-trips and transitions ---------------------------------------------

def test_every_canonical_value_round_trips_and_rework_cycles(world):
	store, _config = world
	work = _create(store)
	# W38: the round trip is the SCHEDULER axis. `active` is absent by
	# construction — it arrives with a claim, not with this verb — and
	# the old research/review rework cycle is a Route concern now.
	trail = ["parked", "queued"]
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="deferring")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued")
	events = [event for event in store.events()
	          if event["kind"] == "set_phase"]
	assert [event["payload"]["to"] for event in events] == trail
	assert [event["payload"]["from"] for event in events] == \
		["queued", "parked"]
	for event in events:
		assert event["payload"]["resolution"]["handlers"] == ["ada"], \
			"a phase change audited without its authorization snapshot"
	for value in ("confirmed-defect", "limitation",
	              "duplicate", "design-choice", "rejection", "unknown"):
		tr.classify(store, work, actor_team="lang", actor="ada",
		            classification=value)
	audited = [event["payload"]["to"] for event in store.events()
	           if event["kind"] == "classify"]
	assert audited[-1] == "unknown", "unknown is an ordinary value"


def test_a_pass_records_the_destination_phase_and_closed_refuses(world):
	# finding-active-work-claim ("Current and phase move together"): the
	# pass atomically records the destination phase — here the explicit
	# review handoff — and never carries the sender's phase.
	store, _config = world
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	fx.post(store, work, author_team="lang", author="ada",
	                body="over to review", pass_to="lang.rev")
	row = _row(store, work)
	assert row["phase"] == "queued", \
		"the pass did not record its stated destination phase"
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="refuses phase"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="parked", reason="w38")
	with pytest.raises(bw.WorkError, match="refuses classification"):
		tr.classify(store, work, actor_team="lang", actor="ada",
		            classification="duplicate")


# -- waiting: typed conditions and the atomic wake ---------------------------

def test_gates_waiting_wakes_only_at_the_last_gate(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	inner = tr.create_work(store, team="lang", kind="bug", title="c",
	                       origin="decomposition", classification="suspected-defect", author="ada", body="b",
	                       parent=work)["work_id"]
	assert _row(store, work)["gate_kind"] == "work"

	tr.close_work(store, inner, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _row(store, work)["phase"] == "block", \
		"satisfying only SOME gates woke the work"
	assert not [e for e in store.events() if e["kind"] == "wake"]

	closing = tr.close_work(store, blocker, actor_team="push", actor="sl",
	                        rationale="done", outcome="satisfying")
	row = _row(store, work)
	assert row["phase"] == "queued" and row["gate_kind"] is None
	wakes = [e for e in store.events() if e["kind"] == "wake"]
	assert len(wakes) == 1, "the wake was lost or duplicated"
	assert wakes[0]["seq"] == closing["seq"] + 1, \
		"the wake is not atomic with the satisfying close"
	assert wakes[0]["payload"] == {
		"work": work, "from": "block", "to": "queued",
		# W47: the resulting scheduler phase, stated rather than
		# inferred from the from/to pair beside it.
		"phase_now": [{"work": work, "phase": "queued"}],
		# W78: the gate episode ends here too, and the gate that
		# cleared is named rather than described as a condition type.
		"gate_now": [{"work": work, "kind": None, "gate_work": None,
		              "obligation": None}],
		"cleared_gate": {"kind": "work", "work": blocker,
		                 "obligation": None}}


def test_waiting_with_no_open_gate_is_refused(world):
	store, _config = world
	work = _create(store)
	with pytest.raises(bw.WorkError, match="already-satisfied"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait="gates")


def test_obligation_waiting_wakes_once_and_grants_nothing(world):
	store, _config = world
	work = _create(store)
	asked = fx.post(store, work, author_team="lang", author="ada",
	                        body="push: confirm?", request="push.bug")["seq"]
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="block", wait=asked)
	# The respondent's input does NOT grant mutation authority...
	with pytest.raises(bw.WorkError,
	                   match="blocked on its displayed|cannot be claimed"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
	responded = tr.respond_obligation(store, asked, team="push",
	                                  member="sl", body="confirmed")
	row = _row(store, work)
	assert row["phase"] == "queued" and row["gate_obligation"] is None
	wakes = [e for e in store.events() if e["kind"] == "wake"]
	assert len(wakes) == 1 and wakes[0]["seq"] == responded["seq"] + 1
	assert wakes[0]["payload"]["cleared_gate"] == \
		{"kind": "message", "work": None, "obligation": asked}
	# ...and having supplied it, push STILL cannot mutate the work.
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.claim_work(store, work, actor_team="push", actor="sl")


def test_obligation_waiting_refuses_wrong_or_completed_obligations(world):
	store, _config = world
	work = _create(store)
	other = _create(store)
	answered = fx.post(store, work, author_team="lang",
	                           author="ada", body="?",
	                           request="push.bug")["seq"]
	tr.respond_obligation(store, answered, team="push", member="sl",
	                      body="done already")
	with pytest.raises(bw.WorkError, match="already-satisfied|already"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait=answered)
	elsewhere = fx.post(store, other, author_team="lang",
	                            author="ada", body="?",
	                            request="push.bug")["seq"]
	with pytest.raises(bw.WorkError, match="its OWN"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait=elsewhere)
	with pytest.raises(bw.WorkError, match="no obligation"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait=99999)


def test_the_wake_race_neither_loses_nor_duplicates(world):
	"""The last two gates close in two racing transactions: the one that
	commits second satisfies the condition and carries the ONE wake."""
	store, _config = world
	work = _create(store)
	first = _create(store, team="push", member="sl")
	second = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, first, actor_team="lang", actor="ada", rationale="test dependency")
	tr.add_dependency(store, work, second, actor_team="lang", actor="ada", rationale="test dependency")

	other = bw.Authority(store.path)
	original = store._write

	def close_second_first(kind, actor, payload, mutate, **kw):
		store._write = original
		tr.close_work(other, second, actor_team="push", actor="sl",
		              rationale="raced in first", outcome="satisfying")
		return original(kind, actor, payload, mutate, **kw)

	store._write = close_second_first
	tr.close_work(store, first, actor_team="push", actor="sl",
	              rationale="the last gate", outcome="satisfying")
	wakes = [e for e in store.events() if e["kind"] == "wake"]
	assert len(wakes) == 1, "the racing closes lost or duplicated the wake"
	assert _row(store, work)["phase"] == "queued"
	other.close()


def test_entering_waiting_races_the_satisfying_close(world):
	"""In-lock refusal: the last gate closes between set_phase's optimistic
	check and its lock — committing `waiting` then would be the loose end
	the ruling forbids."""
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")

	other = bw.Authority(store.path)
	original = store._write

	def satisfy_between(kind, actor, payload, mutate, **kw):
		store._write = original
		tr.close_work(other, blocker, actor_team="push", actor="sl",
		              rationale="gate shut mid-flight", outcome="satisfying")
		return original(kind, actor, payload, mutate, **kw)

	store._write = satisfy_between
	with pytest.raises(bw.WorkError, match="already-satisfied"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait="gates")
	assert _row(store, work)["phase"] == "queued"
	other.close()


# -- parking -----------------------------------------------------------------

def test_parking_needs_a_reason_keeps_current_and_never_wakes(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	with pytest.raises(bw.WorkError, match="reason"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="parked")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="strategy review pending")
	# W38 R1: a gate arriving UNDER a park does not revoke the deferral.
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	assert _row(store, work)["phase"] == "parked"
	row = _row(store, work)
	assert row["phase"] == "parked"
	assert (row["route_team"], row["route_kind"]) == ("lang", "bug"), \
		"parking dropped the one accountable Current"
	# Closing every gate wakes NOTHING parked — no condition, no promise.
	tr.close_work(store, blocker, actor_team="push", actor="sl",
	              rationale="done", outcome="satisfying")
	assert _row(store, work)["phase"] == "parked"
	assert not [e for e in store.events() if e["kind"] == "wake"]
	# parked leaves ONLY to queued, explicitly.
	with pytest.raises(bw.WorkError, match="parked"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued")
	assert _row(store, work)["phase"] == "queued"


def test_the_parked_count_is_always_visible_in_the_summary(world):
	store, _config = world
	work = _create(store)
	assert pj.team_summary(store, viewer_team="lang")["parked"] == 0
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="waiting on budget")
	summary = pj.team_summary(store, viewer_team="lang")
	assert summary["parked"] == 1 and summary["open"] == 1
	assert pj.team_summary(store, viewer_team="push")["parked"] == 0
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["phase"] == "parked" and detail["gate"] is None


def test_waiting_condition_is_visible_in_the_projection(world):
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	# W38 R1: the gate itself commits the waiting state and its
	# condition — no separate phase act is needed or accepted.
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert detail["phase"] == "block"
	assert detail["gate"]["kind"] == "work"


def test_at_input_never_grants_pass_or_close_authority(world):
	"""The delegation ruling is one ownership rule, not a phase-only gate.

	An @ destination participates so it can read and contribute, but Current
	stays with the requester. Participation therefore cannot authorize that
	respondent to pass or terminally close the requester's Work.
	"""
	store, _config = world
	for operation in ("pass", "close"):
		work = _create(store)
		fx.post(store, work, author_team="lang", author="ada",
		                body="input requested", request="push.bug")
		before = store.events()
		with pytest.raises(bw.WorkError, match="never grant|Current"):
			if operation == "pass":
				fx.post(store, work, author_team="push", author="sl",
				                body="taking it", pass_to="push.bug")
			else:
				tr.close_work(store, work, actor_team="push", actor="sl",
				              rationale="not mine to close", outcome="satisfying")
		assert store.events() == before, \
			f"an @ respondent committed an unauthorized {operation}"


def test_detail_declares_handler_phase_and_classification_authority(world):
	"""The JSON projection tells agents what they can do; trying commands is
	not discovery. Authority follows => and is absent for mere participants."""
	store, _config = world
	work = _create(store)
	owned = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert {"classify", "set_phase"} <= set(owned["available_transitions"])
	not_owned = pj.detail(store, work, viewer_team="push", viewer_member="sl")
	assert not {"classify", "set_phase"} & \
		set(not_owned["available_transitions"])
	fx.post(store, work, author_team="lang", author="ada",
	                body="delegated", pass_to="push.bug")
	former = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	delegated = pj.detail(store, work, viewer_team="push", viewer_member="sl")
	assert not {"classify", "set_phase"} & \
		set(former["available_transitions"])
	assert {"classify", "set_phase"} <= \
		set(delegated["available_transitions"])


# -- the complete R1 authority matrix and R5 vocabulary (ruled 2026-08-14) ----

def test_the_full_authority_matrix_gates_every_workflow_decision(world):
	"""Every workflow decision — @ creation, dependency changes, child
	attachment, reopen — belongs to the live Route handler; participation,
	+ attention, and @ input never substitute for ownership."""
	store, _config = world
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	                body="fyi", include="push.bug")
	for team, member in (("lang", "grace"), ("push", "sl")):
		with pytest.raises(bw.WorkError, match="never grant"):
			fx.post(store, work, author_team=team, author=member,
			                body="asking", request="push.bug")
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.add_dependency(store, work, _create(store, team="push",
			                                       member="sl"),
			                  actor_team=team, actor=member, rationale="test dependency")
	# Attaching a child needs the PARENT's handler — a teammate who merely
	# participates is refused (cross-team authors never even reach the
	# gate: authoring for another team refuses first).
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.create_work(store, team="lang", kind="bug", title="child",
		               origin="decomposition", classification="suspected-defect", author="grace", body="b",
		               parent=work)
	# The handler does all of it.
	fx.post(store, work, author_team="lang", author="ada",
	                body="asking", request="push.bug")
	tr.add_dependency(store, work, _create(store, team="push", member="sl"),
	                  actor_team="lang", actor="ada", rationale="test dependency")
	child = tr.create_work(store, team="lang", kind="bug", title="child",
	                       origin="decomposition", classification="suspected-defect", author="ada", body="b",
	                       parent=work)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	# WS-2: closure is immutable — nothing may mutate the closed child;
	# the live continuation is follow-up work.
	with pytest.raises(bw.WorkError, match="terminal|immutable"):
		tr.classify(store, child, actor_team="lang", actor="ada",
		            classification="duplicate")
	assert _row(store, child)["status"] == "closed"


def test_any_configured_participant_may_chip_in_without_work_ownership(world):
	"""Open browsing has no contribution barrier: a configured member who
	drills into another team's Work may post an ordinary message or add `+`
	attention. Neither operation grants workflow ownership."""
	store, _config = world
	work = _create(store)
	assert store.conn.execute(
		"SELECT 1 FROM thread_participants JOIN threads "
		"ON threads.id = thread_participants.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=? AND thread_participants.team='push'",
		(work,)).fetchone() is None, "the outsider was already participating"
	# R69 supersession: contribution is DISCUSSION-addressed after the
	# Slice B bridge removal — detail advertises no Work-addressed
	# posting/seen alias; the open contribution right itself is proven by
	# the successful post below, not by an advertisement.
	available = pj.detail(store, work, viewer_team="push",
	                      viewer_member="sl")["available_transitions"]
	assert not {"post_message", "mark_seen"} & set(available), \
		"detail advertises a removed Work-addressed bridge"
	fx.post(store, work, author_team="push", author="sl",
	                body="I found related evidence", include="push.bug")
	assert store.conn.execute(
		"SELECT 1 FROM messages JOIN threads "
		"ON threads.id = messages.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=? AND messages.author_team='push' "
		"AND messages.author='sl'", (work,)).fetchone(), \
		"a configured participant's contribution was not recorded"
	# Chipping in is not an ownership transfer.
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.close_work(store, work, actor_team="push", actor="sl",
		              rationale="not mine", outcome="satisfying")


def test_obligation_answering_belongs_to_the_named_routes_handler(world):
	"""A resolved handler of the route the @ names may respond or dispose —
	and nobody else, teammate or not."""
	store, _config = world
	push_work = _create(store, team="push", member="sl")
	asked = fx.post(store, push_work, author_team="push",
	                        author="sl", body="lang: yours?",
	                        request="lang.bug")["seq"]
	with pytest.raises(bw.WorkError, match="ownership"):
		tr.respond_obligation(store, asked, team="lang", member="grace",
		                      body="grace is not the intake handler")
	with pytest.raises(bw.WorkError, match="ownership"):
		tr.dispose_obligation(store, asked, team="lang", member="grace",
		                      disposition="not hers to dispose")
	still = store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?", (asked,)).fetchone()
	assert still["status"] == "pending", "an unauthorized answer committed"
	tr.respond_obligation(store, asked, team="lang", member="ada",
	                      body="ours; tracked")


def test_available_transitions_mirror_the_full_matrix(world):
	store, _config = world
	work = _create(store)
	owner = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert {"request", "pass", "add_dependency", "create_child",
	        "classify", "set_phase", "close"} <= \
		set(owner["available_transitions"])
	teammate = pj.detail(store, work, viewer_team="lang",
	                     viewer_member="grace")
	# W3: priority is OWNING-team authority — every configured member
	# of the owning team is offered prioritize, handler or not; no
	# OTHER ownership operation leaks into participation.
	# W128 adds the second one by ruling: correcting where UNCLAIMED
	# Work is offered is owning-team authority too, because an operator
	# routing around a runner cannot be made to depend on that runner.
	# It is offered only while nobody holds the Work, which is why the
	# claimed case below still sees neither.
	assert set(teammate["available_transitions"]) <= \
		{"post_message", "mark_seen", "prioritize", "reroute"}, \
		"participation leaked an ownership operation into the projection"
	assert "prioritize" in teammate["available_transitions"], \
		"the owning-team member lost the ruled priority authority"
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	for viewer in ("ada", "grace"):
		assert pj.detail(store, work, viewer_team="lang",
		                 viewer_member=viewer)["available_transitions"] \
			== [], "closure is immutable (WS-2); nothing is offered"


def test_available_transitions_offer_close_over_an_open_blocker(world):
	"""An open dependency affects readiness but does not prevent an honest
	close; the machine surface must not make agents discover that by trying."""
	store, _config = world
	work = _create(store)
	blocker = _create(store, team="push", member="sl")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	assert "close" in pj.detail(
		store, work, viewer_team="lang",
		viewer_member="ada")["available_transitions"], \
		"projection hid a close the authority permits over an open blocker"


def test_the_compact_vocabulary_is_closed_and_complete(world):
	"""R5: every canonical value has its RULED five-cell label; anything
	unmapped fails visibly — a label is never invented by truncation."""
	del world
	from baton_work.tui import app
	assert {value: app.compact_phase(value) for value in tr.PHASES} == {
		"queued": "queue", "block": "block",
		"active": "actve", "parked": "park"}
	assert {value: app.compact_classification(value)
	        for value in tr.CLASSIFICATIONS} == {
		"unknown": "unkwn", "suspected-defect": "suspt",
		"confirmed-defect": "defct", "limitation": "limit",
		"duplicate": "dupe", "design-choice": "desgn",
		"rejection": "rejct"}
	with pytest.raises(ValueError, match="no ruled compact"):
		app.compact_classification("postponement")
	with pytest.raises(ValueError, match="no ruled compact"):
		app.compact_phase("dormant")
