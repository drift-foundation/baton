"""W108 (finding-active-work-claim): the ATOMIC claim.

SUPERSEDED IN PART — W38, recorded here by W2780 on 2026-08-20. This
docstring described the claim as PHASE-ORTHOGONAL and said "claiming
never rewrites phase", which the suite below already contradicts: see
`test_claiming_records_the_claimant_and_makes_the_work_active`, whose
own note says phase and Handler are the same fact seen twice.

The live contract. `handler_team`/`handler_member` answer WHO is
executing, and `phase` answers whether the Work can run — a closed
SCHEDULER axis, not a stage. The claim establishes both in one
statement, because `active` means exactly that a Handler holds it; only
`claim` reaches it.

The release rule follows from that and NOT from which phase is asked
for. W38 review R2: this docstring said "ordinary phase changes never
release", which is false in the other direction too — `set_phase` cannot
reach `active`, so every phase it CAN reach (`queued`, `block`,
`parked`) is an unclaimed state, and each one releases the claim it
finds. There is no ordinary phase change that keeps a claimant. A pass
atomically records the destination Route AND the destination phase —
derived from the destination's readiness, never from the caller — while
releasing the sender's claim and never claiming for the recipient.
`block` is the phase gated Work is IN, and blocked Work cannot be
claimed. Every claim precondition is rechecked inside the write
transaction.

What the phase never said is what KIND of work this is; that is the
route's role, on its own axis.
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
def store(tmp_path):
	"""One team, stage-named routes (impl/rview) with TWO handlers on the
	implementation route, plus one route whose role names no stage."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl", "rview", "ops"],
		                      "bee": ["impl"]},
		          "kinds": ["bug"]}})
	team = document["teams"]["lang"]
	team["routes"] = {
		"build": {"role": "impl", "handlers": ["ada", "bee"]},
		"review": {"role": "rview", "handlers": ["ada"]},
		"misc": {"role": "ops", "handlers": ["ada"]},
	}
	team["kinds"] = {
		"bug": {"display": "Bug", "route": "build"},
		"rev": {"display": "Rev", "route": "review"},
		"odd": {"display": "Odd", "route": "misc"},
	}
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	with bw.Authority(result["database"]) as authority:
		authority.test_config_path = config_path
		yield authority


def _create(store, title="claimable", parent=None, kind="bug"):
	return tr.create_work(store, team="lang", kind=kind, title=title,
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b", parent=parent)["work_id"]


def _row(store, work):
	return store.conn.execute(
		"SELECT phase, ready, handler_team, handler_member, gate_kind "
		"FROM work WHERE id=?", (work,)).fetchone()


def test_claiming_records_the_claimant_and_makes_the_work_active(store):
	"""W38 supersedes W108's orthogonality here: phase and Handler are
	no longer independent, they are the SAME fact seen twice. `active`
	means somebody is executing, so the claim that establishes the
	claimant establishes the phase in the same statement."""
	work = _create(store)
	assert _row(store, work)["phase"] == "queued"
	result = tr.claim_work(store, work, actor_team="lang", actor="ada")
	row = _row(store, work)
	assert (row["handler_team"], row["handler_member"]) == ("lang", "ada")
	assert row["phase"] == "active", "the claim left the phase behind"
	assert result["phase"] == "active"
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	# W245: `participant` mirrors the route struct's `endpoint`, so the
	# composed identity is not re-derived by every consumer.
	assert view["handler"] == {"team": "lang", "member": "ada",
	                           "participant": "lang.ada"}
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["kind"] == "claim"
	assert event["payload"]["claimant"] == "lang.ada"


def test_a_competing_claim_fails_closed_naming_the_claimant(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="claimed by lang.ada"):
		tr.claim_work(store, work, actor_team="lang", actor="bee")
	assert store.last_seq() == before, "a refused claim burned an event"
	assert _row(store, work)["handler_team"] == "lang"


def test_an_exact_retry_replays_the_one_claim(store):
	work = _create(store)
	first = tr.claim_work(store, work, actor_team="lang", actor="ada",
	                      op_id="claim-1")
	again = tr.claim_work(store, work, actor_team="lang", actor="ada",
	                      op_id="claim-1")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"


def test_claim_preconditions_are_decided_in_the_transaction(store):
	# W1477: an open CHILD is not one of the preconditions. This case
	# used to open with an epic gaining a child and the claim being
	# refused; containment gates terminal closure, not execution, so
	# the parent stays claimable with its part still open.
	epic = _create(store, "epic")
	_child = _create(store, "step", parent=epic)
	tr.claim_work(store, epic, actor_team="lang", actor="ada")
	assert _row(store, epic)["phase"] == "active"

	# The advisory-observation race: ready observed true, then a
	# dependency commits, then the claim runs — and loses.
	work = _create(store, "advisory")
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["ready"] is True
	blocker = _create(store, "arrived-later")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	with pytest.raises(bw.WorkError, match="cannot be claimed"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")

	parked = _create(store, "parked")
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	with pytest.raises(bw.WorkError, match="parked"):
		tr.claim_work(store, parked, actor_team="lang", actor="ada")

	closed = _create(store, "stale")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="terminal"):
		tr.claim_work(store, closed, actor_team="lang", actor="ada")


def test_independent_work_carries_independent_claimants(store):
	"""Pipeline parallelism: two Works claimed by different members,
	one claimant each. Both read `active` now, because both are being
	worked — the Route is what says one is review and one is build."""
	reviewing = _create(store, "under review")
	tr.claim_work(store, reviewing, actor_team="lang", actor="ada")
	implementing = _create(store, "being built")
	tr.claim_work(store, implementing, actor_team="lang", actor="bee")
	rows = {work: _row(store, work)
	        for work in (reviewing, implementing)}
	assert rows[reviewing]["phase"] == "active"
	assert rows[reviewing]["handler_member"] == "ada"
	assert rows[implementing]["phase"] == "active"
	assert rows[implementing]["handler_member"] == "bee"


def test_every_reachable_phase_change_releases_the_claim(store):
	"""W38: the phase verb reaches only UNCLAIMED states, so there is no
	longer such a thing as an ordinary stage change that keeps the
	claim. Moving to queued is a release, exactly as block and parked
	already were."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="stepping away")
	assert _row(store, work)["handler_member"] is None, \
		"a phase change into an unclaimed state kept the claim"


def test_entering_block_releases_the_claim(store):
	"""The condition-bound `block` entry is its own release boundary: the
	claimant clears and the event's payload keeps the released
	claimant as recoverable evidence."""
	work = _create(store, "to-wait")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	asked = fx.post(store, work, author_team="lang", author="ada",
	                body="blocking question", request="lang.rev")
	obligation = asked["seq"]
	released = tr.set_phase(store, work, actor_team="lang", actor="ada",
	                        phase="block", wait=obligation)
	row = _row(store, work)
	assert row["phase"] == "block"
	assert row["handler_team"] is None, \
		"entering block kept the execution claim"
	event = [e for e in store.events() if e["seq"] == released["seq"]][0]
	assert event["payload"]["released_claimant"] == "lang.ada", \
		"the block release is not recoverable from the event"


def test_entering_parked_releases_the_claim(store):
	parked = _create(store, "to-park")
	tr.claim_work(store, parked, actor_team="lang", actor="ada")
	released = tr.set_phase(store, parked, actor_team="lang", actor="ada",
	                        phase="parked", reason="later")
	assert _row(store, parked)["handler_team"] is None
	event = [e for e in store.events() if e["seq"] == released["seq"]][0]
	assert event["payload"]["released_claimant"] == "lang.ada"


def test_terminal_close_releases_the_claim(store):
	closed = _create(store, "to-close")
	tr.claim_work(store, closed, actor_team="lang", actor="ada")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _row(store, closed)["handler_team"] is None, \
		"terminal close did not release the claim"


def test_a_pass_records_the_destination_phase_atomically(store):
	"""The handoff records its destination state in the SAME event; the
	sender's claim is released and the recipient stays unclaimed. W38:
	that state is `queued`, because handing over responsibility is not
	the same as somebody starting."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	result = fx.post(store, work, author_team="lang", author="bee",
	                 body="done, please review", pass_to="lang.rev")
	row = _row(store, work)
	assert row["phase"] == "queued", \
		"the pass did not record the destination stage"
	assert row["handler_team"] is None, "the sender's claim survived"
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["payload"]["destination_phase"] == "queued", \
		"the destination phase is not part of the pass event"
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["handler"] is None, "the recipient was claimed implicitly"
	# Reviewer→implementer records the implementation stage.
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	fx.post(store, work, author_team="lang", author="ada",
	        body="changes requested", pass_to="lang.bug")
	row = _row(store, work)
	assert row["phase"] == "queued" and row["handler_team"] is None


def test_the_caller_cannot_supply_a_destination_phase(store):
	"""W73 removed the caller override and W38 removed the derivation
	that replaced it. What survives both is the property that matters:
	the sender never states the destination state, so a handoff cannot
	advertise a stage nobody is in."""
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="triage first", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "queued", \
		"a routed, unclaimed handoff is not queued"
	with pytest.raises(TypeError):
		tr.pass_work(store, work, actor_team="lang", actor="ada",
		             to="lang.rsrch", comment="x", phase="queued")


def test_a_stageless_destination_role_now_routes_like_any_other(store):
	"""W73 refused a role outside its stage map, because it had no
	phase to derive. W38 derives from the gates instead, so there is
	nothing left to refuse for: an ops route is a destination like any
	other."""
	work = _create(store)
	result = fx.post(store, work, author_team="lang", author="ada",
	                 body="over to ops", pass_to="lang.odd")
	assert result is not None
	assert _row(store, work)["phase"] == "queued"


def test_parked_is_unreachable_through_a_handoff(store):
	"""Parking is a deliberate deferral with a reason, so no handoff can
	produce it. W38 does make `block` reachable — a gated handoff must
	land there, or the Work would advertise as runnable when it is
	not — which is asserted in the W38 suite."""
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="x", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "queued"


def test_a_blocked_move_lands_blocked_and_refuses_claim(store):
	"""SUPERSEDED IN PART — W2571 (`finding-pass-requires-current-claim`,
	2026-08-20). This was `test_a_blocked_handoff_lands_waiting_and
	_refuses_claim` and moved the Work with `pass`; W2780 also retired
	`waiting` from its name, since the phase is `block`. A pass now requires
	the claim, and R3 of THIS record's parent releases the claimant the
	moment a gate arrives — so gated Work has no claimant, can acquire
	none, and moves by `reroute`, which derives the same phase. Every
	assertion is the one this test always made."""
	work = _create(store, "blocked-review")
	blocker = _create(store, "the gate")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada", rationale="test dependency")
	tr.reroute_work(store, work, actor_team="lang", actor="ada",
	                to="lang.rev", reason="offered to review while gated")
	row = _row(store, work)
	assert row["phase"] == "block", \
		"a gated handoff advertised itself as runnable"
	assert row["ready"] == 0
	with pytest.raises(bw.WorkError, match="cannot be claimed"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert _row(store, work)["handler_member"] == "ada"


def test_the_tui_facts_name_the_claimant(store):
	from baton_work.tui.app import Console
	work = _create(store, "shown")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	console = Console(store, "lang", "ada")
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert any(fact == "handler: lang.ada"
	           for fact in console._facts(view)), \
		"the detail facts do not name the handler"


def test_a_late_gate_releases_the_claim_and_moves_to_block(store):
	"""R3: a dependency arriving on claimed Work invalidates execution —
	the claimant is released atomically, and the causing event's payload
	keeps the released claimant as recoverable evidence.

	W38 changes where it lands. Under the old model the stage was
	independent, so the row kept it; now `active` MEANS somebody is
	executing, and releasing without moving the phase would leave the
	exact contradiction the invariant forbids. The Work is gated, so it
	lands `block` — which is what the gate says anyway."""
	work = _create(store, "invalidated")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert _row(store, work)["phase"] == "active"
	blocker = _create(store, "late gate")
	linked = tr.add_dependency(store, work, blocker, actor_team="lang",
	                           actor="ada", rationale="test dependency")
	row = _row(store, work)
	assert row["phase"] == "block", \
		"a released, gated Work kept a phase nobody was executing"
	assert row["ready"] == 0
	assert row["handler_team"] is None, \
		"execution stayed claimed on unready work"
	event = [e for e in store.events() if e["seq"] == linked["seq"]][0]
	assert {"work": work, "claimant": "lang.ada",
	        "from_phase": "active"} in \
		event["payload"]["released_claims"], \
		"the released claimant is not recoverable from the causing event"


def test_an_exact_pass_retry_replays_the_one_handoff(store):
	"""W2571: the claim is stated ONCE and the retry states
	`claim=False`, because the retry must change nothing — including
	not re-acquiring the claim the first pass released. The replay is
	answered inside the write transaction BEFORE the claim gate runs,
	which is why an exact retry still replays from unclaimed state."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	first = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-x")
	again = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-x",
	                claim=False)
	assert again["seq"] == first["seq"], "the retry created a second pass"
	assert again["operation"]["state"] == "replayed"
	assert _row(store, work)["phase"] == "queued"


def test_the_pass_never_carries_the_senders_phase(store):
	"""Race shape: the sender flips their own stage right before the
	handoff commits — the pass still records the DESTINATION phase."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert _row(store, work)["phase"] == "active"
	fx.post(store, work, author_team="lang", author="ada",
	        body="over", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "queued", \
		"the pass carried the sender's active phase to the recipient"


def test_a_consuming_return_commits_a_newly_planted_next(store):
	"""Discovered at the live W108 handoff: a return that consumes the
	planned Next silently dropped a NEW --set-next stated on the same
	act. The new plan commits with the return."""
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="review it", pass_to="lang.rev", set_next="lang.bug")
	returned = fx.post(store, work, author_team="lang", author="ada",
	                   body="approved; plan the review return",
	                   pass_to="lang.bug", set_next="lang.rev")
	assert returned["kind"] == "return"
	row = store.conn.execute(
		"SELECT next_team, next_kind FROM work WHERE id=?",
		(work,)).fetchone()
	assert (row["next_team"], row["next_kind"]) == ("lang", "rev"), \
		"the consuming return dropped the newly planted Next"


def test_the_pass_retry_identity_is_the_destination_not_the_phase(store):
	"""W73: the phase is no longer typed input, so it is no longer part
	of the operation identity — the exact same pass replays its one
	event, and a same-id retry naming a DIFFERENT destination is still
	a conflict that changes nothing."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	first = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-p")
	# W2571: neither retry may claim — a retry that changes nothing must
	# also acquire nothing, and `before` below would otherwise record a
	# claim this test never asked for.
	same = fx.post(store, work, author_team="lang", author="ada",
	               body="over", pass_to="lang.rev", op_id="pass-p",
	               claim=False)
	assert same["seq"] == first["seq"]
	assert same["operation"]["state"] == "replayed"
	before = (store.last_seq(), _row(store, work)["phase"])
	with pytest.raises(bw.WorkError):
		fx.post(store, work, author_team="lang", author="ada",
		        body="over", pass_to="lang.rsrch", op_id="pass-p",
		        claim=False)
	assert (store.last_seq(), _row(store, work)["phase"]) == before, \
		"a conflicting destination retry replayed or committed"
