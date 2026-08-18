"""WS-2 group 2: candidate trials, exact assignments, immutable reports,
append-only assessments, consistent counters, abandon/withdraw.

Every assertion traces to the pinned rulings: a trial pins one exact
candidate and an exact selected verifier set; a report is the verifier's
immutable raw observation (passed|failed|unable) and never transitions
anything; the reviewer's assessment (accepted|rejected|inconclusive) is a
separate append-only axis; `reported/assigned` counts receipt, never
support; withdrawal is terminal and fabricates nothing.
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
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402

import json as _json


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["verify"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["verify"]},
	        "mdb": {"members": {"mo": ["dev"]}, "kinds": ["verify"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _provider(store):
	return tr.create_work(store, team="lang", kind="bug", title="LANG-42",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="the provider work")["work_id"]


def _round_view(store, work, number):
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	return next(entry for entry in detail["trials"]
	            if entry["trial"] == number)


# -- creation: candidate pinning and exact cardinality -----------------------

def test_a_round_pins_its_candidate_and_exact_selection(world):
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify"])
	assert created["trial"] == 1
	view = _round_view(store, work, 1)
	assert view["candidate"] == "driftc-A"
	assert view["status"] == "open"
	assert (view["assigned"], view["reported"], view["pending"],
	        view["withdrawn"]) == (2, 0, 2, 0)
	assert view["progress"] == "0/2"
	assert [entry["endpoint"] for entry in view["assignments"]] == \
		["push.verify", "web.verify"]
	# The assignments are actionable @ obligations for the selected routes.
	actionable = pj.obligations(store, viewer_team="push")
	assert len(actionable) == 1 and \
		actionable[0]["flavor"] == "verification"


def test_round_creation_refusals(world):
	store, _config = world
	work = _provider(store)
	with pytest.raises(bw.WorkError, match="candidate"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="  ", assign=["push.verify"])
	with pytest.raises(bw.WorkError, match="at least one"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=[])
	with pytest.raises(bw.WorkError, match="exactly one endpoint"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=["*.verify"])
	with pytest.raises(bw.WorkError, match="selected twice"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A",
		                assign=["push.verify", "push.verify"])
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.create_trial(store, work, actor_team="lang", actor="grace",
		                candidate="driftc-A", assign=["push.verify"])
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="closed"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=["push.verify"])


# -- reports: immutable raw observations -------------------------------------

def test_a_report_is_immutable_and_transitions_nothing(world):
	store, _config = world
	work = _provider(store)
	consumer = tr.create_work(store, team="push", kind="verify",
	                          title="PUSH-1", origin="external-report", classification="suspected-defect",
	                          author="sl", body="blocked")["work_id"]
	tr.add_dependency(store, consumer, work, actor_team="push", actor="sl", rationale="test dependency")
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	assignment = created["assignments"][0]
	with pytest.raises(bw.WorkError, match="observes exactly"):
		tr.report(store, assignment, team="push", member="sl",
		          observation="confirmed", evidence="e")
	with pytest.raises(bw.WorkError, match="evidence"):
		tr.report(store, assignment, team="push", member="sl",
		          observation="passed", evidence="  ")
	tr.report(store, assignment, team="push", member="sl",
	          observation="failed", evidence="crash log attached")
	view = _round_view(store, work, 1)
	assert view["progress"] == "1/1"
	entry = view["assignments"][0]
	assert entry["state"] == "reported"
	assert entry["observation"] == "failed"
	assert entry["effective_assessment"] is None, \
		"a raw report arrived pre-assessed"
	# The report transitioned NOTHING: no wake, no dependency change, no
	# provider movement — feedback never moves Work.
	assert not [e for e in store.events() if e["kind"] == "wake"]
	row = store.conn.execute("SELECT phase, ready FROM work WHERE id=?",
	                         (consumer,)).fetchone()
	assert row["phase"] == "block" and row["ready"] == 0
	provider = store.conn.execute(
		"SELECT status, phase FROM work WHERE id=?", (work,)).fetchone()
	assert provider["status"] == "open" and provider["phase"] == "queued"
	# A second report refuses; the raw evidence is immutable.
	with pytest.raises(bw.WorkError, match="already reported"):
		tr.report(store, assignment, team="push", member="sl",
		          observation="passed", evidence="changed my mind")


def test_only_the_assignment_route_handler_reports(world):
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	assignment = created["assignments"][0]
	with pytest.raises(bw.WorkError, match="ownership"):
		tr.report(store, assignment, team="web", member="wren",
		          observation="passed", evidence="not my assignment")
	# A verification assignment can never be a wake condition.
	with pytest.raises(bw.WorkError, match="never transitions"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="block", wait=assignment)
	# ...and classic verbs refuse it.
	with pytest.raises(bw.WorkError, match="completes by respond"):
		tr.report(store, fx.post(
			store, work, author_team="lang", author="ada", body="q",
			request="web.verify")["seq"], team="web", member="wren",
			observation="passed", evidence="e")


def test_verification_assignments_refuse_classic_terminal_verbs(world):
	"""The flavored @ subtype completes only through report or withdrawal;
	classic response/disposal must not create unprojectable assignment states."""
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify"])
	with pytest.raises(bw.WorkError, match="verification"):
		tr.respond_obligation(store, created["assignments"][0], team="push",
		                      member="sl", body="looks good")
	with pytest.raises(bw.WorkError, match="verification"):
		tr.dispose_obligation(store, created["assignments"][1], team="web",
		                      member="wren", disposition="not testing")
	assert _round_view(store, work, 1)["pending"] == 2


# -- assessments: the separate append-only axis ------------------------------

def test_assessment_is_append_only_and_never_rewrites_the_report(world):
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	assignment = created["assignments"][0]
	with pytest.raises(bw.WorkError, match="only a "):
		tr.assess(store, assignment, actor_team="lang", actor="ada",
		          assessment="accepted", rationale="premature")
	tr.report(store, assignment, team="push", member="sl",
	          observation="failed", evidence="crash log")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.assess(store, assignment, actor_team="push", actor="sl",
		          assessment="accepted", rationale="self-serving")
	tr.assess(store, assignment, actor_team="lang", actor="ada",
	          assessment="rejected",
	          rationale="consumer configuration error")
	entry = _round_view(store, work, 1)["assignments"][0]
	assert entry["observation"] == "failed", "assessment rewrote the report"
	assert entry["effective_assessment"]["assessment"] == "rejected"
	# Both axes visible: `failed / rejected` — receipt is not support.
	assert _round_view(store, work, 1)["progress"] == "1/1"
	# A changed mind is a SUPERSEDING act; history stays ordered.
	tr.assess(store, assignment, actor_team="lang", actor="ada",
	          assessment="accepted",
	          rationale="reproduced after all; the report was right")
	entry = _round_view(store, work, 1)["assignments"][0]
	assert entry["effective_assessment"]["assessment"] == "accepted"
	assert [act["assessment"] for act in entry["assessments"]] == \
		["rejected", "accepted"]
	assert entry["observation"] == "failed"


# -- supersession and abandon ------------------------------------------------

def test_a_new_candidate_starts_a_new_round_and_withdraws_the_old(world):
	store, _config = world
	work = _provider(store)
	first = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                        candidate="driftc-A",
	                        assign=["push.verify", "web.verify"])
	tr.report(store, first["assignments"][0], team="push", member="sl",
	          observation="failed", evidence="crash")
	second = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                         candidate="driftc-B",
	                         assign=["push.verify"])
	assert second["trial"] == 2
	old = _round_view(store, work, 1)
	assert old["status"] == "superseded"
	assert old["progress"] == "1/2" and old["withdrawn"] == 1, \
		"supersession lost the pinned report or fabricated feedback"
	assert old["candidate"] == "driftc-A"
	fresh = _round_view(store, work, 2)
	assert fresh["progress"] == "0/1", \
		"a trial-1 report carried into trial 2"
	# The withdrawn trial-1 assignment refuses late replies.
	web_assignment = first["assignments"][1]
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.report(store, web_assignment, team="web", member="wren",
		          observation="passed", evidence="late")
	withdrawals = [e for e in store.events() if e["kind"] == "withdraw"]
	assert len(withdrawals) == 1 and \
		withdrawals[0]["payload"]["endpoint"] == "web.verify"


def test_abandon_ends_the_round_but_not_the_work(world):
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify",
	                                  "mdb.verify"])
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="passed", evidence="clean run")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.abandon_trial(store, work, 1, actor_team="push", actor="sl",
		                 reason="reporters do not steer")
	tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
	                 reason="strategy changed")
	view = _round_view(store, work, 1)
	assert view["status"] == "abandoned"
	assert view["progress"] == "1/3" and view["withdrawn"] == 2
	assert store.conn.execute(
		"SELECT status FROM work WHERE id=?", (work,)).fetchone()["status"] \
		== "open", "abandoning a trial touched the work lifecycle"
	withdrawals = [e for e in store.events() if e["kind"] == "withdraw"]
	assert {e["payload"]["endpoint"] for e in withdrawals} == \
		{"web.verify", "mdb.verify"}
	with pytest.raises(bw.WorkError, match="already abandoned"):
		tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
		                 reason="twice")
	# A later candidate needs a NEW trial with NEW assignments.
	again = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                        candidate="driftc-B", assign=["push.verify"])
	assert again["trial"] == 2


def test_work_close_ends_open_rounds_and_every_assignment(world):
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify"])
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="passed", evidence="ok")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="verified in the field",
	              outcome="satisfying")
	view = _round_view(store, work, 1)
	assert view["status"] == "closed"
	assert view["progress"] == "1/2" and view["withdrawn"] == 1
	assert pj.obligations(store, viewer_team="web") == [], \
		"closure left an assignment actionable"
	with pytest.raises(bw.WorkError, match="closed"):
		tr.assess(store, created["assignments"][0], actor_team="lang",
		          actor="ada", assessment="accepted", rationale="late")


# -- authority follows the accepted configuration ----------------------------

def test_reassignment_moves_round_authority_not_history(world):
	store, config_path = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	snapshot = store.conn.execute(
		"SELECT handlers, generation FROM obligations WHERE seq=?",
		(created["assignments"][0],)).fetchone()
	assert _json.loads(snapshot["handlers"]) == ["sl"]
	assert snapshot["generation"] == 1
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
		                 reason="no longer the handler")
	tr.abandon_trial(store, work, 1, actor_team="lang", actor="grace",
	                 reason="authority follows the accepted generation")
	after = store.conn.execute(
		"SELECT handlers, generation FROM obligations WHERE seq=?",
		(created["assignments"][0],)).fetchone()
	assert _json.loads(after["handlers"]) == ["sl"], \
		"reassignment rewrote a historical resolution snapshot"
	assert after["generation"] == 1


# -- reviewer adversarial coverage: audit identity and declared actions -------

def test_report_audit_pins_the_candidate_and_evidence(world):
	"""The report act itself must preserve the evidence identity promised by
	the audit contract; reconstructing it by joining mutable implementation
	tables is not the same as recording it in the immutable act."""
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A+sha256:1234",
	                          assign=["push.verify"])
	result = tr.report(store, created["assignments"][0], team="push",
	                   member="sl", observation="passed",
	                   evidence="baton.source:proofs/push-clean.json")
	event = next(entry for entry in store.events()
	             if entry["seq"] == result["seq"])
	assert event["payload"]["candidate"] == "driftc-A+sha256:1234"
	assert event["payload"]["evidence"] == \
		"baton.source:proofs/push-clean.json"


def test_reassessment_explicitly_supersedes_the_prior_act(world):
	"""Ordered rows are history, but the ruled changed-assessment operation is
	an explicit supersession and must name the act it supersedes."""
	store, _config = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	assignment = created["assignments"][0]
	tr.report(store, assignment, team="push", member="sl",
	          observation="failed", evidence="consumer crash")
	first = tr.assess(store, assignment, actor_team="lang", actor="ada",
	                  assessment="rejected", rationale="bad consumer config")
	second = tr.assess(store, assignment, actor_team="lang", actor="ada",
	                   assessment="accepted", rationale="reproduced")
	event = next(entry for entry in store.events()
	             if entry["seq"] == second["seq"])
	assert event["payload"]["supersedes"] == first["seq"]


def test_detail_declares_the_round_actions_available_to_the_handler(world):
	"""The canonical projection is the agent API: a client must not discover
	new Group-2 operations by attempting undocumented CLI verbs."""
	store, _config = world
	work = _provider(store)
	before = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert "create_trial" in before["available_transitions"]
	assert "abandon_trial" not in before["available_transitions"]
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"])
	after = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert "create_trial" in after["available_transitions"], \
		"publishing a replacement candidate is a declared operation"
	assert "abandon_trial" in after["available_transitions"]
