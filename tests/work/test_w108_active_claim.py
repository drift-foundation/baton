"""W108 (finding-active-work-claim): the ATOMIC, PHASE-ORTHOGONAL claim.

`active_team`/`active_member` answer WHO is executing; `phase` answers WHAT
stage is happening — claiming never rewrites phase, ordinary phase changes
never release, and a pass atomically records the destination Current AND
the destination phase (explicit, or derived from the destination route's
stage role) while releasing the sender's claim and never claiming for the
recipient. Blocked Work keeps its honest stage phase but cannot be claimed;
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


def test_an_explicit_destination_phase_wins(store):
	work = _create(store)
	fx.post(store, work, author_team="lang", author="ada",
	        body="triage first", pass_to="lang.rev",
	        pass_phase="research")
	assert _row(store, work)["phase"] == "research"


def test_a_stageless_destination_role_demands_the_phase(store):
	work = _create(store)
	with pytest.raises(bw.WorkError, match="names no work stage"):
		fx.post(store, work, author_team="lang", author="ada",
		        body="over to ops", pass_to="lang.odd")
	fx.post(store, work, author_team="lang", author="ada",
	        body="over to ops", pass_to="lang.odd", pass_phase="queued")
	assert _row(store, work)["phase"] == "queued"


def test_waiting_and_parked_are_never_a_pass_destination(store):
	work = _create(store)
	with pytest.raises(bw.WorkError, match="never a pass destination"):
		fx.post(store, work, author_team="lang", author="ada",
		        body="x", pass_to="lang.rev", pass_phase="waiting")


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


def test_the_pass_retry_identity_includes_the_destination_phase(store):
	"""R1: the destination phase is typed semantic input — the exact same
	pass replays its one event, while the same operation id with only the
	phase changed refuses as an operation conflict and changes nothing."""
	work = _create(store)
	first = fx.post(store, work, author_team="lang", author="ada",
	                body="over", pass_to="lang.rev", pass_phase="review",
	                op_id="pass-p")
	same = fx.post(store, work, author_team="lang", author="ada",
	               body="over", pass_to="lang.rev", pass_phase="review",
	               op_id="pass-p")
	assert same["seq"] == first["seq"]
	assert same["operation"]["state"] == "replayed"
	before = (store.last_seq(), _row(store, work)["phase"])
	with pytest.raises(bw.WorkError):
		fx.post(store, work, author_team="lang", author="ada",
		        body="over", pass_to="lang.rev", pass_phase="research",
		        op_id="pass-p")
	assert (store.last_seq(), _row(store, work)["phase"]) == before, \
		"a conflicting phase retry replayed or committed"


def test_claim_is_advertised_exactly_when_the_writer_grants_it(store):
	"""R2: canonical discovery — `claim` appears in available_transitions
	precisely for the resolved Current handler of open, ready,
	non-waiting/non-parked, unclaimed Work; every other state hides it."""
	def offered(work, viewer="ada"):
		view = pj.detail(store, work, viewer_team="lang",
		                 viewer_member=viewer)
		return "claim" in view["available_transitions"]

	ready = _create(store, "offer-ready")
	assert offered(ready), "an eligible ready handler is not offered claim"
	assert offered(ready, viewer="bee"), "the second handler is eligible too"

	blocked = _create(store, "offer-blocked")
	gate = _create(store, "offer-gate")
	tr.add_dependency(store, blocked, gate, actor_team="lang", actor="ada")
	assert not offered(blocked), "blocked work advertised claim"

	claimed = _create(store, "offer-claimed")
	tr.claim_work(store, claimed, actor_team="lang", actor="ada")
	assert not offered(claimed, viewer="bee"), \
		"already-claimed work advertised claim"

	parked = _create(store, "offer-parked")
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert not offered(parked), "parked work advertised claim"

	reviewing = _create(store, "offer-outsider", kind="rev")
	assert not offered(reviewing, viewer="bee"), \
		"a non-handler of the review route was offered claim"
	assert offered(reviewing), "the review-route handler is eligible"

	closed = _create(store, "offer-closed")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	view = pj.detail(store, closed, viewer_team="lang",
	                 viewer_member="ada")
	assert view["available_transitions"] == [], \
		"closed work advertised operations"


def test_the_public_claim_verb_reaches_the_transition(store, capsys):
	"""R2 (CLI proof): the advertised operation and the public verb are
	the same surface — `claim WORK` through cli.main commits the claim
	the projection then shows."""
	import json as _j
	from baton_work import cli
	work = _create(store, "cli-claimed")
	code = cli.main(["--config", store.test_config_path,
	                 "--participant", "lang.bee", "claim", f"work={work}"])
	out = capsys.readouterr().out
	assert code == 0, out
	result = _j.loads(out)
	assert result["result"]["claimant"] == "lang.bee"
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["active"] == {"team": "lang", "member": "bee"}


def test_release_recovers_the_claim_and_nothing_else(store):
	"""Ruled recovery: self-release and forced recovery are the same
	honest operation — claimant-only mutation with durable reason."""
	work = _create(store, "recover-me")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="research")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = store.conn.execute(
		"SELECT phase, ready, current_team, current_kind, next_team "
		"FROM work WHERE id=?", (work,)).fetchone()
	# Forced recovery by the OTHER resolved handler.
	result = tr.release_claim(store, work, actor_team="lang", actor="bee",
	                          expect="lang.ada",
	                          reason="claimant stopped responding")
	assert result["released_claimant"] == "lang.ada"
	row = _row(store, work)
	assert row["active_team"] is None
	after = store.conn.execute(
		"SELECT phase, ready, current_team, current_kind, next_team "
		"FROM work WHERE id=?", (work,)).fetchone()
	assert tuple(after) == tuple(before), \
		"release mutated something beyond the claimant"
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["kind"] == "release"
	assert event["payload"]["released_claimant"] == "lang.ada"
	assert event["payload"]["reason"] == "claimant stopped responding"
	# Self-release uses the SAME operation.
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	tr.release_claim(store, work, actor_team="lang", actor="bee",
	                 expect="lang.bee", reason="yielding to ada")
	assert _row(store, work)["active_team"] is None


def test_release_compare_and_swap_refuses_in_the_transaction(store):
	work = _create(store, "cas")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="claimed by lang.ada, not"):
		tr.release_claim(store, work, actor_team="lang", actor="bee",
		                 expect="lang.bee", reason="stale observation")
	assert store.last_seq() == before
	assert _row(store, work)["active_member"] == "ada", \
		"a mismatched CAS release mutated the claim"

	unclaimed = _create(store, "cas-empty")
	with pytest.raises(bw.WorkError, match="unclaimed"):
		tr.release_claim(store, unclaimed, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="nothing there")
	with pytest.raises(bw.WorkError, match="non-empty durable reason"):
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="   ")


def test_release_authority_is_the_live_current_endpoint(store):
	"""bee handles the build route but NOT the review route: on a
	review-kind Work bee's release refuses even with an exact expect."""
	work = _create(store, "review-owned", kind="rev")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError):
		tr.release_claim(store, work, actor_team="lang", actor="bee",
		                 expect="lang.ada", reason="not mine to take")
	assert _row(store, work)["active_member"] == "ada"


def test_release_retry_replays_and_conflicts_honestly(store):
	work = _create(store, "release-retry")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	first = tr.release_claim(store, work, actor_team="lang", actor="ada",
	                         expect="lang.ada", reason="pausing",
	                         op_id="rel-1")
	again = tr.release_claim(store, work, actor_team="lang", actor="ada",
	                         expect="lang.ada", reason="pausing",
	                         op_id="rel-1")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"
	with pytest.raises(bw.WorkError):
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="different words",
		                 op_id="rel-1")


def test_release_is_advertised_only_while_claimed(store):
	def offered(work, viewer="ada"):
		view = pj.detail(store, work, viewer_team="lang",
		                 viewer_member=viewer)
		return "release" in view["available_transitions"]

	work = _create(store, "offer-release")
	assert not offered(work), "unclaimed work advertised release"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert offered(work), "the claimant is not offered self-release"
	assert offered(work, viewer="bee"), \
		"the other resolved handler is not offered recovery"
	reviewing = _create(store, "offer-release-outsider", kind="rev")
	tr.claim_work(store, reviewing, actor_team="lang", actor="ada")
	assert not offered(reviewing, viewer="bee"), \
		"a non-handler was offered release"


def test_the_public_release_verb_reaches_the_transition(store, capsys):
	import json as _j
	from baton_work import cli
	work = _create(store, "cli-released")
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	code = cli.main(["--config", store.test_config_path,
	                 "--participant", "lang.ada", "release", f"work={work}",
	                 "expect=lang.bee",
	                 "reason=bee's runner died"])
	out = capsys.readouterr().out
	assert code == 0, out
	assert _j.loads(out)["result"]["released_claimant"] == "lang.bee"
	assert _row(store, work)["active_team"] is None
