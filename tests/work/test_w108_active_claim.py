"""W108 (finding-active-work-claim): the ATOMIC, PHASE-ORTHOGONAL claim.

`active_team`/`active_member` answer WHO is executing; `phase` answers WHAT
stage is happening — claiming never rewrites phase, ordinary phase changes
never release, and a pass atomically records the destination Current AND
the destination phase (W73: derived from the destination route's stage
role, never from the caller) while releasing the sender's claim and
never claiming for the recipient. Blocked Work keeps its honest stage phase but cannot be claimed;
every claim precondition is rechecked inside the write transaction.
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
		"SELECT phase, ready, active_team, active_member, wait_type "
		"FROM work WHERE id=?", (work,)).fetchone()


def test_claiming_records_the_claimant_without_touching_phase(store):
	work = _create(store)
	before = _row(store, work)["phase"]
	result = tr.claim_work(store, work, actor_team="lang", actor="ada")
	row = _row(store, work)
	assert (row["active_team"], row["active_member"]) == ("lang", "ada")
	assert row["phase"] == before, "the claim silently rewrote phase"
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["active"] == {"team": "lang", "member": "ada"}
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
	assert _row(store, work)["active_team"] == "lang"


def test_an_exact_retry_replays_the_one_claim(store):
	work = _create(store)
	first = tr.claim_work(store, work, actor_team="lang", actor="ada",
	                      op_id="claim-1")
	again = tr.claim_work(store, work, actor_team="lang", actor="ada",
	                      op_id="claim-1")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"


def test_claim_preconditions_are_decided_in_the_transaction(store):
	epic = _create(store, "epic")
	_child = _create(store, "step", parent=epic)
	with pytest.raises(bw.WorkError, match="cannot be claimed"):
		tr.claim_work(store, epic, actor_team="lang", actor="ada")

	# The advisory-observation race: ready observed true, then a
	# dependency commits, then the claim runs — and loses.
	work = _create(store, "advisory")
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["ready"] is True
	blocker = _create(store, "arrived-later")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada")
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
	"""Pipeline parallelism: a claimed review-phase Work beside an
	independently claimed implementation Work, one claimant each."""
	reviewing = _create(store, "under review")
	tr.set_phase(store, reviewing, actor_team="lang", actor="ada",
	             phase="review")
	tr.claim_work(store, reviewing, actor_team="lang", actor="ada")
	implementing = _create(store, "being built")
	tr.set_phase(store, implementing, actor_team="lang", actor="ada",
	             phase="active")
	tr.claim_work(store, implementing, actor_team="lang", actor="bee")
	rows = {work: _row(store, work)
	        for work in (reviewing, implementing)}
	assert rows[reviewing]["phase"] == "review"
	assert rows[reviewing]["active_member"] == "ada"
	assert rows[implementing]["phase"] == "active"
	assert rows[implementing]["active_member"] == "bee"


def test_ordinary_phase_changes_keep_the_claim(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="research")
	assert _row(store, work)["active_member"] == "ada", \
		"an ordinary stage change released the claim"


def test_entering_waiting_releases_the_claim(store):
	"""The condition-bound waiting entry is its own release boundary: the
	claimant clears and the waiting event's payload keeps the released
	claimant as recoverable evidence."""
	work = _create(store, "to-wait")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	asked = fx.post(store, work, author_team="lang", author="ada",
	                body="blocking question", request="lang.rev")
	obligation = asked["seq"]
	released = tr.set_phase(store, work, actor_team="lang", actor="ada",
	                        phase="waiting", wait=obligation)
	row = _row(store, work)
	assert row["phase"] == "waiting"
	assert row["active_team"] is None, \
		"entering waiting kept the execution claim"
	event = [e for e in store.events() if e["seq"] == released["seq"]][0]
	assert event["payload"]["released_claimant"] == "lang.ada", \
		"the waiting release is not recoverable from the event"


def test_entering_parked_releases_the_claim(store):
	parked = _create(store, "to-park")
	tr.claim_work(store, parked, actor_team="lang", actor="ada")
	released = tr.set_phase(store, parked, actor_team="lang", actor="ada",
	                        phase="parked", reason="later")
	assert _row(store, parked)["active_team"] is None
	event = [e for e in store.events() if e["seq"] == released["seq"]][0]
	assert event["payload"]["released_claimant"] == "lang.ada"


def test_terminal_close_releases_the_claim(store):
	closed = _create(store, "to-close")
	tr.claim_work(store, closed, actor_team="lang", actor="ada")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _row(store, closed)["active_team"] is None, \
		"terminal close did not release the claim"


def test_a_pass_records_the_destination_phase_atomically(store):
	"""Implementer→reviewer lands phase=review in the SAME event; the
	sender's claim is released and the recipient stays unclaimed."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	tr.set_phase(store, work, actor_team="lang", actor="bee",
	             phase="active")
	result = fx.post(store, work, author_team="lang", author="bee",
	                 body="done, please review", pass_to="lang.rev")
	row = _row(store, work)
	assert row["phase"] == "review", \
		"the pass did not record the destination stage"
	assert row["active_team"] is None, "the sender's claim survived"
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["payload"]["destination_phase"] == "review", \
		"the destination phase is not part of the pass event"
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["active"] is None, "the recipient was claimed implicitly"
	# Reviewer→implementer records the implementation stage.
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	fx.post(store, work, author_team="lang", author="ada",
	        body="changes requested", pass_to="lang.bug")
	row = _row(store, work)
	assert row["phase"] == "active" and row["active_team"] is None


def test_the_route_decides_the_phase_and_the_caller_cannot(store):
	"""W73 supersedes R1's caller override. W49 was handed to
	baton.impl with phase=queued and then actively worked, so the
	projection showed a claimed Work sitting in `queued`. The
	destination route now decides, and the operand is gone from the
	grammar entirely — the false state is unrepresentable rather than
	merely discouraged."""
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="triage first", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "review", \
		"the reviewer route did not decide the destination stage"
	# a handoff never produces `queued`, whatever the sender wanted
	assert _row(store, work)["phase"] != "queued"
	with pytest.raises(TypeError):
		tr.pass_work(store, work, actor_team="lang", actor="ada",
		             to="lang.rsrch", comment="x", phase="queued")


def test_a_stageless_destination_role_refuses_the_handoff(store):
	"""W73: with no caller override left, an unmapped destination role
	has nothing to fall back on and refuses inside the transaction
	rather than guessing a stage."""
	work = _create(store)
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="names no work stage"):
		fx.post(store, work, author_team="lang", author="ada",
		        body="over to ops", pass_to="lang.odd")
	assert store.last_seq() == before, \
		"the refused handoff still committed an event"
	assert _row(store, work)["phase"] == "queued", \
		"the refused handoff moved the stage"


def test_waiting_and_parked_are_unreachable_through_a_handoff(store):
	"""They were never a pass destination, and W73 removes the operand
	that could even name them: no stage role maps to either, so a
	handoff cannot produce them by any route."""
	from baton_work.transitions import STAGE_PHASES
	assert "waiting" not in STAGE_PHASES.values()
	assert "parked" not in STAGE_PHASES.values()
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="x", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "review"


def test_blocked_review_work_keeps_review_but_refuses_claim(store):
	work = _create(store, "blocked-review")
	blocker = _create(store, "the gate")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada")
	fx.post(store, work, author_team="lang", author="ada",
	        body="review while blocked", pass_to="lang.rev")
	row = _row(store, work)
	assert row["phase"] == "review", \
		"a dependency edge silently rewrote the stage to waiting"
	assert row["ready"] == 0
	with pytest.raises(bw.WorkError, match="cannot be claimed"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert _row(store, work)["active_member"] == "ada"


def test_the_tui_facts_name_the_claimant(store):
	from baton_work.tui.app import Console
	work = _create(store, "shown")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	console = Console(store, "lang", "ada")
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert any(fact == "active: lang.ada"
	           for fact in console._facts(view)), \
		"the detail facts do not name the active participant"


def test_a_late_gate_releases_the_claim_but_keeps_the_stage(store):
	"""R3: a dependency arriving on claimed Work invalidates execution —
	the claimant is released atomically — without rewriting the honest
	work stage; the causing event's payload keeps the released claimant
	as recoverable evidence."""
	work = _create(store, "invalidated")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="review")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	blocker = _create(store, "late gate")
	linked = tr.add_dependency(store, work, blocker, actor_team="lang",
	                           actor="ada")
	row = _row(store, work)
	assert row["phase"] == "review", \
		"the late gate rewrote the honest work stage"
	assert row["ready"] == 0
	assert row["active_team"] is None, \
		"execution stayed claimed on unready work"
	event = [e for e in store.events() if e["seq"] == linked["seq"]][0]
	assert {"work": work, "claimant": "lang.ada"} in \
		event["payload"]["released_claims"], \
		"the released claimant is not recoverable from the causing event"


def test_an_exact_pass_retry_replays_the_one_handoff(store):
	work = _create(store)
	first = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-x")
	again = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-x")
	assert again["seq"] == first["seq"], "the retry created a second pass"
	assert again["operation"]["state"] == "replayed"
	assert _row(store, work)["phase"] == "review"


def test_the_pass_never_carries_the_senders_phase(store):
	"""Race shape: the sender flips their own stage right before the
	handoff commits — the pass still records the DESTINATION phase."""
	work = _create(store)
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="research")
	fx.post(store, work, author_team="lang", author="ada",
	        body="over", pass_to="lang.rev")
	assert _row(store, work)["phase"] == "review", \
		"the pass carried the sender's phase instead of the destination"


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
	first = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", op_id="pass-p")
	same = fx.post(store, work, author_team="lang", author="ada",
	               body="over", pass_to="lang.rev", op_id="pass-p")
	assert same["seq"] == first["seq"]
	assert same["operation"]["state"] == "replayed"
	before = (store.last_seq(), _row(store, work)["phase"])
	with pytest.raises(bw.WorkError):
		fx.post(store, work, author_team="lang", author="ada",
		        body="over", pass_to="lang.rsrch", op_id="pass-p")
	assert (store.last_seq(), _row(store, work)["phase"]) == before, \
		"a conflicting destination retry replayed or committed"
