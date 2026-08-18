"""W288: the Work contract is promoted by whoever is EXECUTING the Work.

Found while proving W104's post-W245 documentation: two participants
resolved through one route, `ada` held the claim, and `bee` — eligible
but executing nothing — replaced the live contract underneath her. Route
eligibility says who MAY claim; it never said who is accountable right
now, so gating promotion on it alone let one worker rewrite assigned
scope beneath another and defeated the claim's single-executor boundary.

The authority now requires the exact current claimant AND live route
eligibility, both decided in the transaction that commits the revision.
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
	"""Two handlers on ONE route — the exact shape that produced the
	defect — plus an outsider team."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "bee": ["impl"]},
		          "kinds": ["bug"]},
		 "push": {"members": {"sl": ["impl"]}, "kinds": ["bug"]}})
	lang = document["teams"]["lang"]
	lang["routes"] = {"build": {"role": "impl", "handlers": ["ada", "bee"]},
	                  "queue": {"role": "impl", "handlers": ["ada", "bee"]}}
	lang["kinds"] = {"bug": {"display": "Bug", "route": "build"},
	                 "task": {"display": "Task", "route": "queue"}}
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield store, config_path
	store.close()


def _setup(store, claim_by="ada"):
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="the initial statement")
	work, thread = born["work_id"], born["thread"]
	proposed = tr.post_thread(store, thread, author_team="lang",
	                          author="bee",
	                          body="proposed replacement contract")["seq"]
	if claim_by:
		tr.claim_work(store, work, actor_team="lang", actor=claim_by)
	return work, thread, proposed


def _state(store, work):
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	return (view["revision"], view["route"]["endpoint"], view["handler"],
	        view["phase"])


# -- the boundary -----------------------------------------------------------

def test_the_exact_claimant_promotes(world):
	store, _config = world
	work, _thread, proposed = _setup(store)
	result = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                        message_seq=proposed, expected_revision=0,
	                        rationale="agreed in discussion")
	assert result["revision"] == 1
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["revision"]["message_seq"] == proposed
	assert view["revision"]["actor"] == "lang.ada"


def test_an_eligible_route_peer_refuses_and_changes_nothing(world):
	"""The defect, as a regression: bee resolves through the same route
	and may propose all day, but ada is the one executing."""
	store, _config = world
	work, _thread, proposed = _setup(store, claim_by="ada")
	before = _state(store, work)
	before_seq = store.last_seq()
	with pytest.raises(bw.WorkError, match="claimed by lang.ada"):
		tr.revise_work(store, work, actor_team="lang", actor="bee",
		               message_seq=proposed, expected_revision=0,
		               rationale="not mine to commit")
	assert store.last_seq() == before_seq, "a refused revision burned a seq"
	assert _state(store, work) == before
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["revision"] is None


def test_unclaimed_work_refuses_and_discussion_stays_open(world):
	store, config = world
	work, thread, proposed = _setup(store, claim_by=None)
	before_seq = store.last_seq()
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="nobody executing")
	assert store.last_seq() == before_seq
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["revision"] is None
	# proposing is still fine — the refusal is about PROMOTION only
	again = tr.post_thread(store, thread, author_team="lang", author="bee",
	                       body="another proposal")["seq"]
	assert again > proposed


def test_an_outsider_refuses_on_eligibility_before_the_claim(world):
	"""Order matters for the message: a foreign team is not eligible at
	all, so it should hear that rather than a claim-ownership fact it
	could not act on anyway."""
	store, _config = world
	work, _thread, proposed = _setup(store)
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.revise_work(store, work, actor_team="push", actor="sl",
		               message_seq=proposed, expected_revision=0,
		               rationale="outsider")


# -- losing the claim mid-flight --------------------------------------------

def test_releasing_the_claim_ends_the_authority(world):
	store, _config = world
	work, _thread, proposed = _setup(store)
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="stepping away")
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="after release")


def test_passing_the_work_ends_the_authority(world):
	"""A pass clears current (W245), so the sender stops being able to
	rewrite the contract the moment the baton moves."""
	store, _config = world
	work, _thread, proposed = _setup(store)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.task", comment="over to the queue")
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="after pass")


def test_forced_recovery_moves_the_authority_to_the_recoverer(world):
	store, _config = world
	work, _thread, proposed = _setup(store)
	tr.release_claim(store, work, actor_team="lang", actor="bee",
	                 expect="lang.ada", reason="ada's runner died")
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	with pytest.raises(bw.WorkError, match="claimed by lang.bee"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="former claimant")
	assert tr.revise_work(store, work, actor_team="lang", actor="bee",
	                      message_seq=proposed, expected_revision=0,
	                      rationale="recovered and executing")["revision"] == 1


def test_a_claim_lost_inside_the_transaction_fails_closed(world):
	"""The check runs in the committing lock, so a release that lands
	between the caller's read and the write refuses rather than racing."""
	store, _config = world
	work, _thread, proposed = _setup(store)
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="raced away")
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="raced")
	store._write = original
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["revision"] is None


# -- effectively-once -------------------------------------------------------

def test_an_exact_retry_replays_the_one_revision(world):
	store, _config = world
	work, _thread, proposed = _setup(store)
	first = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                       message_seq=proposed, expected_revision=0,
	                       rationale="agreed", op_id="rev-1")
	again = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                       message_seq=proposed, expected_revision=0,
	                       rationale="agreed", op_id="rev-1")
	assert again["operation"]["state"] == "replayed"
	assert again["revision"] == first["revision"] == 1
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["revision_count"] == 1, "the retry minted a second revision"


def test_a_retry_after_losing_the_claim_replays_and_authorizes_nothing_new(world):
	"""The stored result is replayed, so a retry cannot become a fresh
	authorization for a participant who is no longer executing."""
	store, _config = world
	work, thread, proposed = _setup(store)
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=proposed, expected_revision=0,
	               rationale="agreed", op_id="rev-1")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="handing over")
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	replay = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                        message_seq=proposed, expected_revision=0,
	                        rationale="agreed", op_id="rev-1")
	assert replay["operation"]["state"] == "replayed"
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["revision_count"] == 1
	# and a genuinely NEW request from the former claimant still refuses
	follow_up = tr.post_thread(store, thread, author_team="lang",
	                           author="ada", body="third contract")["seq"]
	with pytest.raises(bw.WorkError, match="claimed by lang.bee"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=follow_up, expected_revision=1,
		               rationale="former claimant", op_id="rev-2")


def test_the_authorization_snapshot_records_the_claimant(world):
	store, _config = world
	work, _thread, proposed = _setup(store)
	result = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                        message_seq=proposed, expected_revision=0,
	                        rationale="agreed")
	event = [e for e in store.events() if e["seq"] == result["seq"]][0]
	assert event["payload"]["authorization"]["claimant"] == "lang.ada", \
		"the revision evidence does not record who was executing"


# -- the operator has to be able to discover the precondition ---------------

def test_the_public_help_states_the_claimant_precondition():
	"""An operator reading `--help revise` must learn that being an
	eligible route handler is not enough. Without this the only way to
	discover the rule is to be refused by it."""
	from baton_work import cli
	entry = cli.GRAMMAR["revise"]
	blurb = entry["help"]
	assert "exact current claimant" in blurb, blurb
	assert "route" in blurb, blurb
	assert "unclaimed" in blurb, blurb
	work_key = next(key for key in entry["keys"] if key["name"] == "work")
	assert "claim" in work_key["help"], work_key


def test_the_help_and_the_authority_cannot_drift_apart(world):
	"""The help makes three claims; each is asserted against the live
	authority here, so a future edit that softens one without changing
	the other reds instead of quietly misleading operators."""
	store, _config = world
	work, _thread, proposed = _setup(store, claim_by=None)
	blurb = __import__("baton_work.cli", fromlist=["cli"]).GRAMMAR["revise"]["help"]

	# "unclaimed Work refuses"
	assert "unclaimed" in blurb
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="probe")
	# "only the exact current claimant"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="claimed by lang.ada"):
		tr.revise_work(store, work, actor_team="lang", actor="bee",
		               message_seq=proposed, expected_revision=0,
		               rationale="probe")
	# "still eligible through the Work's route"
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.revise_work(store, work, actor_team="push", actor="sl",
		               message_seq=proposed, expected_revision=0,
		               rationale="probe")
	assert tr.revise_work(store, work, actor_team="lang", actor="ada",
	                      message_seq=proposed, expected_revision=0,
	                      rationale="the claimant")["revision"] == 1
