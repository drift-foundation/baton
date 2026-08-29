"""W5: the conversational poke — asking a live agent "what's up?".

`work/records/2026/08/finding-conversational-agent-poke/`, slice A
(PLAN steps 3 and 4). An operator sees an apparently idle or stalled
participant and needs to ask the session what is happening. Creating a
Work dependency, a workflow transition, or a directed obligation merely
to wake that agent falsifies the coordination record; restarting the
runner is too strong when the session may be healthy but quiet.

So poke is a small PERSISTENT authority primitive that survives an
offline participant, reaches Codex and ACP agents through the same
participant-relative `wait`, and gives the operator one vendor-neutral
place to read the answer. It carries no workflow authority whatsoever,
and the tests that matter most below are the ones proving that: no Work
row, no obligation, no message, no Work event, and no claim moves
because somebody asked a question.

The 2026-08-18 dispositions this pins: self-poke is allowed; timeout is
OPTIONAL, explicit, and derived at read time with no scheduler; pending
pokes are deduplicated by keeping the NEWEST per asker and target; and
the response reports canonical Baton state separately from the agent's
own explanation so disagreement stays visible.
"""

from __future__ import annotations

import hashlib
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	"""ada and grace in one team, sl in another — an asker, a target,
	and a cross-team third party. ada and sl hold `config`; grace does
	not, which is the capability contrast cancellation needs."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["obs"]},
		          "kinds": ["bug"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config, participant="lang.ada")["database"]
	store = bw.Authority(database)
	_inject_clock(store)
	yield {"config": config, "database": database, "store": store}
	store.close()


def _inject_clock(store):
	"""`Authority` binds its clock ONCE at construction from the
	environment, so a store built before a test freezes time would keep
	reading the wall clock. This reads the injected instant at CALL
	time and falls back to real UTC — the same contract, evaluated
	later."""
	store.clock = lambda: (os.environ.get("BATON_WORK_NOW")
	                       or bw.authority._utc_now())


def make(world, title="w", author="ada"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b")["work_id"]


def actions(world, member, team="lang"):
	return pj.participant_actions(world["store"], viewer_team=team,
	                              viewer_member=member)["actions"]


def keys(world, member, team="lang"):
	return [action["action_key"]
	        for action in actions(world, member, team=team)]


def pokes(world, member="ada", team="lang", **kwargs):
	return pj.pokes(world["store"], viewer_team=team,
	                viewer_member=member, **kwargs)["pokes"]


def one(world, seq, **kwargs):
	return next(row for row in pokes(world, **kwargs) if row["poke"] == seq)


def snapshot(world):
	"""Everything a poke must never touch, in one comparable value."""
	store = world["store"]
	return {
		table: [dict(row) for row in store.conn.execute(
			f"SELECT * FROM {table}")]
		for table in ("work", "obligations", "edges", "messages",
		              "threads", "thread_labels", "trials")}


def at(now):
	os.environ["BATON_WORK_NOW"] = now


def unfreeze():
	os.environ.pop("BATON_WORK_NOW", None)


@pytest.fixture(autouse=True)
def _clock():
	yield
	unfreeze()


# -- the point of the feature ------------------------------------------------

def test_a_poke_wakes_a_participant_with_no_actionable_work_at_all(world):
	"""The whole reason this exists. grace has no Work, no obligation
	and no trial — every existing wake rule is silent for her — and a
	poke still reaches her, which is what "wake an apparently idle
	agent" means. Nothing else in the projection can do this."""
	assert keys(world, "grace") == [], "the fixture already had a wake"
	asked = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace")

	woken = actions(world, "grace")
	assert [action["kind"] for action in woken] == ["poke"]
	entry = woken[0]
	assert entry["action_key"] == f"poke:{asked['poke']}"
	assert entry["poke"] == asked["poke"] == asked["seq"]
	assert entry["asker"] == "lang.ada"
	# the friendly default, not an alarm
	assert entry["request"] == "what's up?"
	assert entry["expires_at"] is None
	# and it wakes NOBODY else, because a poke names one participant
	assert keys(world, "ada") == []
	assert keys(world, "sl", team="push") == []


def test_a_poke_moves_no_work_obligation_message_or_event(world):
	"""The invariant the primitive exists to protect: asking a question
	falsifies nothing. A dependency, a directed obligation, or a phase
	move would each have woken the agent too — and each would have left
	a lie in the coordination record."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	before = snapshot(world)
	events_before = len(pj.work_events(world["store"], work)["events"])

	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="working", explanation="reading the dossier",
	               work=[work])
	other = tr.poke(world["store"], actor_team="push", actor="sl",
	                target="lang.grace")["poke"]
	tr.cancel_poke(world["store"], other, actor_team="push", actor="sl",
	               reason="answered elsewhere")

	assert snapshot(world) == before, \
		"a poke, an answer or a cancellation changed workflow state"
	assert len(pj.work_events(world["store"], work)["events"]) \
		== events_before, \
		"a poke manufactured an event on a Work it merely mentioned"
	# and the claim is exactly where it was: naming a Work in an answer
	# is a report, never an acquisition
	row = world["store"].conn.execute(
		"SELECT handler_team, handler_member FROM work WHERE id=?",
		(work,)).fetchone()
	assert (row["handler_team"], row["handler_member"]) == ("lang", "ada")


def test_the_answer_reports_canonical_state_beside_the_agents_claim(world):
	"""The disagreement is the report. grace answers that she is working
	on a Work that ada actually holds — the single most useful thing a
	poke can surface — so the projection must state both facts and
	collapse neither."""
	work = make(world, title="held by ada")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="working", explanation="mid review", work=[work],
	               provider="acp", model="a-model", session_state="live",
	               auth_state="ok", context_limit=1000, context_used=250)

	row = one(world, seq)
	assert row["state"] == "answered"
	answer = row["answer"]
	assert answer["state"] == "working"
	assert answer["explanation"] == "mid review"
	# THE AGENT'S CLAIM, with the canonical facts about it
	claimed = answer["claimed_work"]
	assert [entry["work"] for entry in claimed] == [work]
	assert claimed[0]["handler"] == "lang.ada", claimed
	assert claimed[0]["status"] == "open" and claimed[0]["phase"] == "active"
	# THE AUTHORITY'S OWN ANSWER about the target, owed to nobody's report
	assert row["canonical"]["handled_work"] == []
	# the two layers stay separable
	assert answer["runner"] == {"provider": "acp", "model": "a-model",
	                            "session_state": "live", "auth_state": "ok",
	                            "limit_state": "unknown", "retry_at": None}
	assert answer["telemetry"] == {"context_limit": 1000,
	                               "context_used": 250,
	                               "context_remaining": None}


def test_unsupplied_diagnostics_are_explicitly_unknown_never_guessed(world):
	"""Capability-based means an adapter that cannot see a fact says so.
	`unknown` is a first-class member of each vocabulary, and an omitted
	scalar is null — never a zero standing in for a fact nobody has."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="idle", explanation="nothing assigned")
	answer = one(world, seq)["answer"]
	assert answer["runner"] == {"provider": "unknown", "model": "unknown",
	                            "session_state": "unknown",
	                            "auth_state": "unknown",
	                            "limit_state": "unknown", "retry_at": None}
	assert answer["telemetry"] == {"context_limit": None,
	                               "context_used": None,
	                               "context_remaining": None}
	assert answer["claimed_work"] == []


def test_a_runner_layer_can_explain_why_the_model_could_not_answer(world):
	"""Layer 1 exists for the case the finding names: a provider rate
	limiter or an authentication failure is why there is no useful agent
	status, and it must be reportable as such rather than inferred from
	silence."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="needs-help",
	               explanation="the provider is throttling this account",
	               provider="acp", limit_state="rate-limited",
	               auth_state="ok", retry_at="2030-01-01T00:05:00Z")
	answer = one(world, seq)["answer"]
	assert answer["state"] == "needs-help"
	assert answer["runner"]["limit_state"] == "rate-limited"
	assert answer["runner"]["retry_at"] == "2030-01-01T00:05:00Z"


# -- authorization and targeting ---------------------------------------------

def test_self_poke_is_allowed_and_travels_the_same_persistent_path(world):
	"""Ruled 2026-08-18. Its canonical purpose is the end-to-end
	diagnostic "does my wake-up bus work?", so it must exercise the very
	same delivery another asker would use — not a shortcut."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.ada")["poke"]
	assert keys(world, "ada") == [f"poke:{seq}"]
	row = one(world, seq)
	assert row["asker"] == row["target"] == "lang.ada"
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="working", explanation="bus works")
	assert one(world, seq)["state"] == "answered"


def test_any_configured_participant_may_ask_across_teams(world):
	"""Poke carries no workflow authority, so the route-eligibility gate
	that protects mutations has nothing to protect here. Requiring a
	capability would make the friendly question harder to ask than the
	acts that actually change state."""
	seq = tr.poke(world["store"], actor_team="push", actor="sl",
	              target="lang.grace")["poke"]
	assert keys(world, "grace") == [f"poke:{seq}"]
	assert one(world, seq)["asker"] == "push.sl"


@pytest.mark.parametrize("target,expected", [
	("lang", "team.member shaped"),
	(".grace", "team.member shaped"),
	("lang.", "team.member shaped"),
	("lang.*", "not a registered member"),
	("lang.ghost", "not a registered member"),
	("push.grace", "not a registered member"),
])
def test_a_poke_names_one_exact_participant_and_nothing_else(world, target,
                                                             expected):
	"""Never a route, never a wildcard. A poke that fanned out would be
	a broadcast, and a broadcast has no one answer to be terminal."""
	with pytest.raises(bw.WorkError, match=expected):
		tr.poke(world["store"], actor_team="lang", actor="ada",
		        target=target)
	assert pokes(world) == []


def test_only_the_exact_participant_asked_may_answer(world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	with pytest.raises(bw.WorkError,
	                   match="only the exact participant that was asked"):
		tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
		               state="idle", explanation="not mine to answer")
	with pytest.raises(bw.WorkError, match="only the exact participant"):
		tr.answer_poke(world["store"], seq, actor_team="push", actor="sl",
		               state="idle", explanation="not mine either")
	assert one(world, seq)["state"] == "pending"
	assert keys(world, "grace") == [f"poke:{seq}"]


def test_exactly_one_response_is_terminal(world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="idle", explanation="quiet")
	assert keys(world, "grace") == [], \
		"an answered poke stayed in the wake set"
	with pytest.raises(bw.WorkError, match="already answered"):
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="grace", state="working",
		               explanation="changed my mind")
	assert one(world, seq)["answer"]["explanation"] == "quiet"


def test_an_answer_naming_a_work_that_does_not_exist_refuses(world):
	"""A claim about a Work nobody can address is a malformed answer,
	not a disagreement — there is nothing to compare it against."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	with pytest.raises(bw.WorkError):
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="grace", state="working",
		               explanation="on it", work=["fefefefe-W999"])
	assert one(world, seq)["state"] == "pending"


@pytest.mark.parametrize("kwargs,expected", [
	({"state": "busy"}, "poke state"),
	({"session_state": "maybe"}, "session_state"),
	({"auth_state": "probably"}, "auth_state"),
	({"limit_state": "slow"}, "limit_state"),
	({"retry_at": "soon"}, "canonical UTC instant"),
	({"context_used": -1}, "non-negative integer"),
	({"context_limit": True}, "non-negative integer"),
	({"explanation": "   "}, "non-empty string"),
])
def test_every_answer_vocabulary_is_closed(world, kwargs, expected):
	"""Closed vocabularies and bounded scalars are how "no credentials,
	no unrestricted vendor payloads" is kept STRUCTURAL: there is no
	opaque column for one to arrive in, so there is nothing to sanitize
	later."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	call = {"state": "idle", "explanation": "quiet"}
	call.update(kwargs)
	with pytest.raises(bw.WorkError, match=expected):
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="grace", **call)
	assert one(world, seq)["state"] == "pending"


# -- deduplication: the newest pending poke per asker and target -------------

def test_a_new_poke_supersedes_that_askers_earlier_pending_one(world):
	"""Ruled 2026-08-18. This is what a rate limit is actually for here —
	one asker cannot pile up questions — achieved without measuring time
	or adding the authority's first background timer."""
	first = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace", request="what's up?")["poke"]
	second = tr.poke(world["store"], actor_team="lang", actor="ada",
	                 target="lang.grace",
	                 request="still there? it has been an hour")
	assert second["superseded"] == [first]

	# only the newer one is actionable, and its text is the CURRENT one
	woken = actions(world, "grace")
	assert [entry["action_key"] for entry in woken] \
		== [f"poke:{second['poke']}"]
	assert woken[0]["request"] == "still there? it has been an hour"

	# the superseded record REMAINS history rather than being rewritten
	older = one(world, first)
	assert older["state"] == "superseded"
	assert older["request"] == "what's up?"
	assert older["resolved_seq"] == second["seq"]
	# and it can no longer be answered
	with pytest.raises(bw.WorkError, match="already superseded"):
		tr.answer_poke(world["store"], first, actor_team="lang",
		               actor="grace", state="idle", explanation="late")


def test_a_superseding_poke_starts_its_own_wait_window(world):
	"""The positive half of the expiry ruling: "its optional
	`expires_at` starts the NEW wait window".

	The companion below it — an `op-id` retry NOT renewing — has been
	pinned since the first cut, but the two are different acts and only
	one of them was covered. A deliberate re-ask is a new question and
	is bounded by the deadline the asker just set; the superseded row
	keeps the deadline it was created with, because it is history."""
	at("2026-08-19T00:00:00Z")
	first = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace",
	                expires_at="2026-08-19T00:05:00Z")["poke"]
	at("2026-08-19T00:04:00Z")
	second = tr.poke(world["store"], actor_team="lang", actor="ada",
	                 target="lang.grace", request="still there?",
	                 expires_at="2026-08-19T00:30:00Z")
	assert second["superseded"] == [first]

	# past the FIRST poke's deadline the live question is still live
	at("2026-08-19T00:06:00Z")
	assert keys(world, "grace") == [f"poke:{second['poke']}"]
	assert one(world, second["poke"])["state"] == "pending"
	# and the superseded row kept its own recorded deadline
	older = one(world, first)
	assert older["state"] == "superseded"
	assert older["expires_at"] == "2026-08-19T00:05:00Z"

	# the new window ends when the NEW deadline says it does
	at("2026-08-19T00:30:00Z")
	assert keys(world, "grace") == []
	assert one(world, second["poke"])["state"] == "timed-out"


def test_a_superseding_poke_may_drop_the_deadline_entirely(world):
	"""`optional` cuts both ways: re-asking without `expires_at`
	replaces a bounded question with an unbounded one, which is what an
	asker who has given up guessing when the target will return
	actually wants."""
	at("2026-08-19T00:00:00Z")
	first = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace",
	                expires_at="2026-08-19T00:05:00Z")["poke"]
	second = tr.poke(world["store"], actor_team="lang", actor="ada",
	                 target="lang.grace")
	assert second["superseded"] == [first]
	assert one(world, second["poke"])["expires_at"] is None
	at("2027-08-19T00:00:00Z")
	assert keys(world, "grace") == [f"poke:{second['poke']}"], \
		"the replaced deadline still bounded the new question"


def test_different_askers_keep_independent_pending_pokes(world):
	"""They are different people asking, so both questions exist and
	both are delivered."""
	mine = tr.poke(world["store"], actor_team="lang", actor="ada",
	               target="lang.grace")
	theirs = tr.poke(world["store"], actor_team="push", actor="sl",
	                 target="lang.grace")
	assert mine["superseded"] == [] and theirs["superseded"] == []
	assert keys(world, "grace") == [f"poke:{mine['poke']}",
	                                f"poke:{theirs['poke']}"]


def test_supersession_is_scoped_to_one_target(world):
	"""Asking grace does not withdraw the question already put to ada."""
	to_ada = tr.poke(world["store"], actor_team="lang", actor="ada",
	                 target="lang.ada")["poke"]
	to_grace = tr.poke(world["store"], actor_team="lang", actor="ada",
	                   target="lang.grace")
	assert to_grace["superseded"] == []
	assert keys(world, "ada") == [f"poke:{to_ada}"]


# -- optional, explicit, derived expiry --------------------------------------

def test_expiry_is_derived_at_read_time_and_needs_no_scheduler(world):
	"""Ruled 2026-08-18. Nothing in this authority watches a clock, and
	this feature deliberately does not introduce the first thing that
	does. The stored row keeps saying `pending` past its deadline; every
	read agrees it is `timed-out` and stops offering it."""
	at("2026-08-19T00:00:00Z")
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace",
	              expires_at="2026-08-19T00:10:00Z")["poke"]
	assert keys(world, "grace") == [f"poke:{seq}"]
	assert one(world, seq)["state"] == "pending"

	at("2026-08-19T00:09:59Z")
	assert keys(world, "grace") == [f"poke:{seq}"], "expired one second early"

	at("2026-08-19T00:10:00Z")
	assert keys(world, "grace") == [], \
		"a timed-out poke was still offered for delivery"
	assert one(world, seq)["state"] == "timed-out"
	# the ROW was never written: nothing scheduled a transition
	stored = world["store"].conn.execute(
		"SELECT status, resolved_seq FROM pokes WHERE seq=?",
		(seq,)).fetchone()
	assert stored["status"] == "pending" and stored["resolved_seq"] is None


def test_a_timed_out_poke_can_never_later_be_answered(world):
	"""If the deadline lived only in the read path, an answer arriving
	late would quietly resurrect a poke the operator has already been
	shown as terminal."""
	at("2026-08-19T00:00:00Z")
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace",
	              expires_at="2026-08-19T00:10:00Z")["poke"]
	at("2026-08-19T00:10:01Z")
	with pytest.raises(bw.WorkError, match="timed out"):
		tr.answer_poke(world["store"], seq, actor_team="lang",
		               actor="grace", state="idle", explanation="late")
	with pytest.raises(bw.WorkError, match="timed out"):
		tr.cancel_poke(world["store"], seq, actor_team="lang", actor="ada")
	assert one(world, seq)["state"] == "timed-out"


def test_without_a_deadline_an_offline_participant_answers_on_return(world):
	"""The approved property a background expiry would have destroyed.
	A poke with no `expires_at` stays pending however long the target is
	away, and level-triggered delivery re-offers it on return."""
	at("2026-08-19T00:00:00Z")
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	at("2027-08-19T00:00:00Z")
	assert keys(world, "grace") == [f"poke:{seq}"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="idle", explanation="back after a year")
	assert one(world, seq)["state"] == "answered"


def test_an_already_expired_deadline_refuses_at_creation(world):
	at("2026-08-19T00:00:00Z")
	with pytest.raises(bw.WorkError, match="not later than now"):
		tr.poke(world["store"], actor_team="lang", actor="ada",
		        target="lang.grace", expires_at="2026-08-18T00:00:00Z")
	with pytest.raises(bw.WorkError, match="canonical UTC instant"):
		tr.poke(world["store"], actor_team="lang", actor="ada",
		        target="lang.grace", expires_at="tomorrow")
	assert pokes(world) == []


def test_supersession_leaves_an_already_timed_out_poke_alone(world):
	"""A timed-out poke is terminal by derivation. Rewriting it as
	`superseded` would change a state the operator has already read."""
	at("2026-08-19T00:00:00Z")
	stale = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace",
	                expires_at="2026-08-19T00:10:00Z")["poke"]
	at("2026-08-19T00:20:00Z")
	fresh = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace")
	assert fresh["superseded"] == []
	assert one(world, stale)["state"] == "timed-out"
	assert keys(world, "grace") == [f"poke:{fresh['poke']}"]


# -- cancellation ------------------------------------------------------------

def test_the_asker_withdraws_their_own_question(world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.cancel_poke(world["store"], seq, actor_team="lang", actor="ada",
	               reason="found out another way")
	assert keys(world, "grace") == []
	row = one(world, seq)
	assert row["state"] == "cancelled" and row["answer"] is None


def test_a_config_holder_clears_a_poke_aimed_at_a_participant_that_wont_return(
		world):
	"""The operator needs this; grace, who holds no capability and did
	not ask, does not get it."""
	seq = tr.poke(world["store"], actor_team="push", actor="sl",
	              target="lang.ada")["poke"]
	with pytest.raises(bw.WorkError, match="only that asker or a holder"):
		tr.cancel_poke(world["store"], seq, actor_team="lang",
		               actor="grace")
	assert one(world, seq)["state"] == "pending"
	tr.cancel_poke(world["store"], seq, actor_team="lang", actor="ada",
	               reason="that runner is retired")
	assert one(world, seq)["state"] == "cancelled"


def test_cancelling_an_answered_poke_refuses_rather_than_rewriting_history(
		world):
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="grace",
	               state="idle", explanation="quiet")
	with pytest.raises(bw.WorkError, match="already answered"):
		tr.cancel_poke(world["store"], seq, actor_team="lang", actor="ada")
	assert one(world, seq)["answer"]["explanation"] == "quiet"


# -- replay, restart, purity -------------------------------------------------

def test_an_exact_retry_replays_and_does_not_renew_the_wait_window(world):
	"""The established `op-id` protection, unchanged. A retry is the
	same question, not a new one, so it must not mint a second poke and
	must not restart the deadline the first one carried."""
	at("2026-08-19T00:00:00Z")
	first = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace",
	                expires_at="2026-08-19T00:10:00Z", op_id="ask-1")
	at("2026-08-19T00:05:00Z")
	again = tr.poke(world["store"], actor_team="lang", actor="ada",
	                target="lang.grace",
	                expires_at="2026-08-19T00:10:00Z", op_id="ask-1")
	assert again["poke"] == first["poke"]
	assert again["operation"]["state"] == "replayed"
	assert [row["poke"] for row in pokes(world)] == [first["poke"]]
	assert one(world, first["poke"])["expires_at"] \
		== "2026-08-19T00:10:00Z", "the retry renewed the wait window"
	# and the deadline still arrives when the FIRST poke said it would
	at("2026-08-19T00:10:00Z")
	assert keys(world, "grace") == []


def test_a_pending_poke_survives_a_restart_and_is_redelivered(world):
	"""Persistence is the reason this is authority state rather than a
	runner-control socket. A runner that restarts, reconnects, or simply
	polls again sees the question again — level-triggered, with no
	delivery counter and no acknowledgement distinct from the answer."""
	seq = tr.poke(world["store"], actor_team="lang", actor="ada",
	              target="lang.grace")["poke"]
	world["store"].close()
	reopened = bw.Authority(world["database"])
	_inject_clock(reopened)
	world["store"] = reopened
	assert keys(world, "grace") == [f"poke:{seq}"]
	assert keys(world, "grace") == [f"poke:{seq}"], \
		"delivery was consumed by reading it"


def test_reading_pokes_and_waiting_write_nothing(world):
	"""Reads are pure — the authority's bytes are identical before and
	after. A wake that recorded its own delivery would be a write on the
	`wait` path, which this projection has never had."""
	tr.poke(world["store"], actor_team="lang", actor="ada",
	        target="lang.grace")
	world["store"].conn.commit()
	before = hashlib.sha256(open(world["database"], "rb").read()).hexdigest()
	for _ in range(3):
		pokes(world)
		actions(world, "grace")
		pj.wait_actionable(world["store"], viewer_team="lang",
		                   viewer_member="grace", timeout_seconds=0)
	after = hashlib.sha256(open(world["database"], "rb").read()).hexdigest()
	assert after == before, "a read mutated the authority"


def test_pokes_come_last_so_a_question_never_displaces_the_workflow(world):
	"""Deterministic order, and the reason for it: a conversational
	question is the least authoritative thing in the wake set."""
	work = make(world, title="routed")
	tr.poke(world["store"], actor_team="push", actor="sl",
	        target="lang.ada")
	kinds = [entry["kind"] for entry in actions(world, "ada")]
	assert "work" in kinds and kinds[-1] == "poke", kinds
	assert work


# -- the public CLI surface --------------------------------------------------

def _run(capsys, config, *argv, participant="lang.ada", expect_ok=True):
	code = cli.main(["--config", config, "--participant", participant]
	                + list(argv))
	captured = capsys.readouterr()
	if expect_ok:
		assert code == 0, captured.err
		return _json.loads(captured.out)
	assert code == 1, captured.out
	return _json.loads(captured.err)


def test_the_public_grammar_carries_the_whole_conversation(world, capsys):
	"""One question and one answer, entirely through the key=value
	surface an agent actually drives."""
	config = world["config"]
	asked = _run(capsys, config, "poke", "target=lang.grace",
	             "request=what's up?")
	seq = asked["result"]["poke"]
	assert asked["result"]["target"] == "lang.grace"
	assert asked["projection_version"] == "12.8"  # the poke major

	woken = _run(capsys, config, "wait", "timeout=0",
	             participant="lang.grace")["result"]
	assert [entry["kind"] for entry in woken["actionable"]] == ["poke"]

	answered = _run(capsys, config, "poke-answer", f"poke={seq}",
	                "state=waiting", "explanation=waiting on review",
	                "session-state=live", "context-limit=1000",
	                participant="lang.grace")["result"]
	assert answered["state"] == "waiting"

	listed = _run(capsys, config, "pokes")["result"]["pokes"]
	assert len(listed) == 1 and listed[0]["state"] == "answered"
	assert listed[0]["answer"]["telemetry"]["context_limit"] == 1000
	assert listed[0]["answer"]["telemetry"]["context_used"] is None

	assert _run(capsys, config, "pokes", "target=push.sl")["result"]["pokes"] \
		== []


def test_the_grammar_refuses_a_closed_vocabulary_before_any_write(world,
                                                                  capsys):
	config = world["config"]
	seq = _run(capsys, config, "poke", "target=lang.grace")["result"]["poke"]
	error = _run(capsys, config, "poke-answer", f"poke={seq}",
	             "state=confused", "explanation=x", participant="lang.grace",
	             expect_ok=False)
	assert "state" in error["error"]
	error = _run(capsys, config, "poke", "target=lang.grace", "urgency=high",
	             expect_ok=False)
	assert "unknown key" in error["error"]
	assert _run(capsys, config, "pokes")["result"]["pokes"][0]["state"] \
		== "pending"


# -- slice B: the runners consume it ------------------------------------------

def test_the_real_envelope_satisfies_both_runner_bridges(world, tmp_path):
	"""The producer and the consumers, on ONE envelope.

	Both bridge suites test `poke` against fixtures they wrote
	themselves, which is exactly how a producer and a consumer drift
	apart while both suites stay green. This drives a REAL `wait`
	envelope out of the CLI and through the shared validator, the
	compact locator, and the ACP prompt builder — so the fields the
	authority emits and the fields a runner requires are the same
	fields or this fails."""
	import shutil
	import subprocess
	if shutil.which("node") is None:
		pytest.skip("the runner bridges need node")
	repo = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))

	tr.poke(world["store"], actor_team="push", actor="sl",
	        target="lang.grace", request="still on the review?")
	world["store"].conn.commit()

	waited = subprocess.run(
		[sys.executable, "-m", "baton_work.cli",
		 "--config", world["config"], "--participant", "lang.grace",
		 "wait", "timeout=0"],
		capture_output=True, text=True, timeout=60,
		env={**os.environ, "PYTHONPATH": os.path.join(repo, "src")})
	assert waited.returncode == 0, waited.stderr
	envelope = tmp_path / "envelope.json"
	envelope.write_text(waited.stdout, encoding="utf-8")

	harness = tmp_path / "consume.mjs"
	harness.write_text(f'''
import {{ readFileSync }} from "node:fs";
import {{ validateEnvelope, actionLocator }} from
	"{repo}/tools/codex-event-bridge/src/codex_baton_bridge.mjs";
import {{ promptText }} from
	"{repo}/tools/acp-baton-bridge/src/baton_readiness.mjs";
const payload = JSON.parse(readFileSync(process.argv[2], "utf8"));
const validated = validateEnvelope(payload, "lang.grace");
const poke = validated.result.actionable.find((a) => a.kind === "poke");
console.log(JSON.stringify({{
	kinds: validated.result.actionable.map((a) => a.kind),
	ignored: validated.result.ignored_actions,
	locator: poke ? actionLocator(poke) : null,
	prompt: poke ? promptText(validated, poke, null) : null,
}}));
''', encoding="utf-8")

	consumed = subprocess.run(
		["node", str(harness), str(envelope)],
		capture_output=True, text=True, timeout=60)
	assert consumed.returncode == 0, consumed.stderr
	seen = _json.loads(consumed.stdout)

	# the poke SURVIVED validation rather than being tolerated away —
	# which is the whole difference between the compatibility
	# prerequisite and the feature
	assert "poke" in seen["kinds"], seen
	assert seen["ignored"] == [], seen["ignored"]
	# the locator carries what `poke-answer` needs, and no Work
	assert seen["locator"]["poke"] == pokes(world)[0]["poke"]
	assert seen["locator"]["asker"] == "push.sl"
	assert seen["locator"]["request"] == "still on the review?"
	assert "work" not in seen["locator"], seen["locator"]
	# and the prompt asks the question rather than raising an alarm
	assert "push.sl asks lang.grace: still on the review?" in seen["prompt"]
	assert "poke-answer poke=" in seen["prompt"]
	for alarming in ("alert", "escalat", "unhealthy", "failure"):
		assert alarming not in seen["prompt"].lower(), seen["prompt"]


def test_the_emitted_action_carries_exactly_the_consumed_contract(world):
	"""The producer half, stated as fields, so a change here fails
	beside the bridge suites rather than silently ahead of them."""
	seq = tr.poke(world["store"], actor_team="push", actor="sl",
	              target="lang.grace", request="what's up?",
	              expires_at="2030-01-01T00:00:00Z")["poke"]
	action = actions(world, "grace")[0]
	assert set(action) == {"kind", "action_key", "poke", "asker",
	                       "request", "expires_at", "asked_at"}
	assert action["kind"] == "poke"
	assert action["action_key"] == f"poke:{seq}"
	assert action["poke"] == seq
	assert action["asker"] == "push.sl"
	assert action["request"] == "what's up?"
	assert action["expires_at"] == "2030-01-01T00:00:00Z"
	# no Work field at all: the primitive has none, and a consumer
	# refuses an envelope that invents one
	assert "work" not in action
