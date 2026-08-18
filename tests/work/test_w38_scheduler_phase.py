"""W38: Phase is a closed SCHEDULER axis, and `active` means claimed.

W4 was claimed and genuinely executing while W15 and W25 had only been
routed to `baton.impl`. All three read `active`, so three concurrent
implementations appeared where there was one. The authority was encoding
the destination ROLE into the phase — an implementation handoff became
`active` before pickup, a review handoff became `review` — which
duplicated the Route and made the ordinary word active mean something
other than active work.

    queued   open, runnable, unclaimed
    active   open and CLAIMED
    waiting  open, unclaimed, gated
    parked   open, unclaimed, deliberately deferred
    terminal no phase at all

Route says what KIND of work it is. Handler says WHO is doing it. Phase
says only whether it can run and whether it is running.
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
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def store(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl", "rview"],
		                      "bee": ["impl"]},
		          "kinds": ["bug"]}})
	team = document["teams"]["lang"]
	team["routes"] = {"build": {"role": "impl", "handlers": ["ada", "bee"]},
	                  "review": {"role": "rview", "handlers": ["ada"]}}
	team["kinds"] = {"bug": {"display": "Bug", "route": "build"},
	                 "rev": {"display": "Rev", "route": "review"}}
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	with bw.Authority(result["database"]) as authority:
		yield authority


def _create(store, title="w"):
	return tr.create_work(store, team="lang", kind="bug", title=title,
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")["work_id"]


def _row(store, work):
	return store.conn.execute(
		"SELECT phase, handler_team, handler_member, wait_type "
		"FROM work WHERE id=?", (work,)).fetchone()


def _invariant(store):
	"""active if and only if a handler holds it — checked over EVERY
	open row, so no path can leave a contradiction behind."""
	for row in store.conn.execute(
			"SELECT id, phase, handler_team FROM work "
			"WHERE status='open'").fetchall():
		claimed = row["handler_team"] is not None
		assert (row["phase"] == "active") == claimed, \
			f"{row['id']}: phase={row['phase']} handler={row['handler_team']}"


# -- the closed vocabulary --------------------------------------------------

def test_the_axis_holds_exactly_the_four_scheduler_states():
	assert tr.PHASES == ("queued", "active", "waiting", "parked")
	assert "research" not in tr.PHASES and "review" not in tr.PHASES


def test_active_is_not_settable(store):
	"""It is a fact about who is executing, not a stage to announce."""
	work = _create(store)
	with pytest.raises(bw.WorkError, match="only `claim` establishes"):
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase="active")
	assert _row(store, work)["phase"] == "queued"


def test_the_public_grammar_offers_only_the_settable_states():
	"""Filtering FOR active work is an ordinary question; asking for it
	as a destination is not."""
	settable = dict(work_cli.GRAMMAR["phase"]["keys"][1].items())
	assert "active" not in settable["values"]
	assert set(settable["values"]) == {"queued", "waiting", "parked"}
	home = {key["name"]: key for key in work_cli.GRAMMAR["home"]["keys"]}
	assert "active" in home["phase"]["values"], \
		"an operator cannot ask which Work is running"


def test_creation_takes_no_phase_operand():
	"""A creation is open, unclaimed and ungated, so `queued` is the
	only honest landing state."""
	assert "phase" not in {key["name"]
	                       for key in work_cli.GRAMMAR["create"]["keys"]}


# -- the invariant, through every path --------------------------------------

def test_claiming_and_releasing_move_phase_with_the_handler(store):
	work = _create(store)
	assert _row(store, work)["phase"] == "queued"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert _row(store, work)["phase"] == "active"
	_invariant(store)
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="stepping away")
	assert _row(store, work)["phase"] == "queued"
	_invariant(store)


def test_a_pass_lands_queued_whatever_the_destination_role(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	result = tr.pass_work(store, work, actor_team="lang", actor="ada",
	                      to="lang.rev", comment="over to review")
	assert result["destination_phase"] == "queued"
	assert _row(store, work)["handler_team"] is None
	_invariant(store)


def test_a_gated_pass_lands_waiting_and_can_still_wake(store):
	"""The bug this nearly shipped: deriving `waiting` without also
	recording the wake condition produces Work that is gated forever,
	because the sweep only reconsiders rows whose condition it can
	evaluate."""
	work = _create(store)
	blocker = _create(store, "gate")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over while gated")
	row = _row(store, work)
	assert row["phase"] == "waiting"
	assert row["wait_type"] == "gates", \
		"a derived wait recorded no condition, so nothing can wake it"
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _row(store, work)["phase"] == "queued", \
		"closing the last gate did not wake the Work"
	_invariant(store)


def test_a_late_gate_on_claimed_work_releases_into_waiting(store):
	"""The other bug: this path releases the claim WITHOUT being asked
	to, so forgetting the phase here leaves `active` with nobody on it."""
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	blocker = _create(store, "late gate")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="late")
	row = _row(store, work)
	assert (row["phase"], row["handler_team"]) == ("waiting", None)
	_invariant(store)


def test_a_gate_on_unclaimed_queued_work_moves_it_to_waiting(store):
	"""Queued means runnable, not merely unclaimed. A dependency arriving
	before pickup must therefore move the scheduler state even though there
	is no Handler to release."""
	work = _create(store)
	blocker = _create(store, "gate before pickup")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="late gate")
	row = _row(store, work)
	assert (row["phase"], row["handler_team"], row["wait_type"]) == \
	       ("waiting", None, "gates")
	_invariant(store)


def test_unparking_gated_work_reveals_waiting_not_queued(store):
	"""Removing the deliberate deferral does not make open gates vanish.
	The resulting scheduler state is derived from those gates."""
	work = _create(store)
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	blocker = _create(store, "gate while parked")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="still gated")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued")
	row = _row(store, work)
	assert (row["phase"], row["handler_team"], row["wait_type"]) == \
	       ("waiting", None, "gates")
	_invariant(store)


def test_resolving_one_wait_condition_does_not_ignore_an_open_gate(store):
	"""A wake is level-triggered over the whole scheduler condition.
	Resolving the obligation that originally parked this Work must retarget
	the wait to its still-open dependency, not advertise it as runnable."""
	work = _create(store)
	thread = store.conn.execute(
		"SELECT thread FROM thread_labels WHERE work=?", (work,)).fetchone()[0]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	request = tr.post_thread(store, thread, author_team="lang", author="ada",
	                         body="please verify", request="lang.rev", on=work)
	assert _row(store, work)["wait_type"] == "obligation"
	blocker = _create(store, "independent gate")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="also required")
	tr.respond_obligation(store, request["seq"], team="lang", member="ada",
	                      body="verification complete")
	row = _row(store, work)
	assert (row["phase"], row["handler_team"], row["wait_type"]) == \
	       ("waiting", None, "gates")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _row(store, work)["phase"] == "queued"
	_invariant(store)


def test_every_settable_phase_releases_the_claim(store):
	for phase, kwargs in (("parked", {"reason": "later"}),
	                      ("queued", {})):
		work = _create(store, f"to-{phase}")
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		tr.set_phase(store, work, actor_team="lang", actor="ada",
		             phase=phase, **kwargs)
		assert _row(store, work)["handler_team"] is None, phase
	_invariant(store)


def test_a_terminal_close_clears_both(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["phase"] is None and view["handler"] is None
	_invariant(store)


def test_a_losing_claim_race_leaves_one_active_row(store):
	work = _create(store)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="already claimed"):
		tr.claim_work(store, work, actor_team="lang", actor="bee")
	assert store.last_seq() == before
	assert _row(store, work)["handler_member"] == "ada"
	_invariant(store)


# -- the projection ---------------------------------------------------------

def test_the_projection_publishes_route_handler_and_next(store):
	work = _create(store)
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["route"]["endpoint"] == "lang.bug"
	assert view["handler"] is None
	assert "current" not in view, "the retired `current` key survives"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	view = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	assert view["handler"]["participant"] == "lang.ada"
	assert view["phase"] == "active"


def test_the_handler_filter_selects_the_exact_claimant(store):
	mine = _create(store, "mine")
	theirs = _create(store, "theirs")
	tr.claim_work(store, mine, actor_team="lang", actor="ada")
	tr.claim_work(store, theirs, actor_team="lang", actor="bee")
	rows = pj.home(store, viewer_team="lang", viewer_member="ada",
	               work_filter={"handler": "me"})["rows"]
	assert [row["id"] for row in rows] == [mine]
	rows = pj.home(store, viewer_team="lang", viewer_member="ada",
	               work_filter={"phase": "active"})["rows"]
	assert sorted(row["id"] for row in rows) == sorted([mine, theirs])


# -- the prose is a specification too --------------------------------------

_ACTIVE_DOCS = ("docs/EFFECTIVE-BATON.md", "docs/BATON-WORK.md",
                "docs/AGENTS-MAILBOX-PROTO.md")

# The two load-bearing false models W38 removed. Each is composed rather
# than written out, so this file can be scanned alongside the others
# without matching itself — the same discipline the W245 vocabulary guard
# uses, and for the same reason: an exclusion stops protecting the one
# file most likely to discuss the boundary.
_DECIDES = " decides the phase"
_ROLE_DERIVES_PHASE = (
	"role" + _DECIDES,
	"derives the phase from the " + "route",
	"stage role" + " decides",
	"roles" + " map to",
	"DESTINATION ROUTE" + _DECIDES,
)
_PHASE_IS_A_STAGE = (
	"phase is still " + "`queued`",
	"claim answers" + " *who is executing*, never",
	"six-phase" + " enum",
	"`" + "research`, `active` and `review`",
)
# Retired phase spellings, as canonical VALUES rather than English words.
_RETIRED_PHASES = ('phase="research"', "phase='research'",
                   'phase="review"', "phase='review'",
                   "to=research", "to=review")


def _repo_text(relative):
	root = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	with open(os.path.join(root, relative), encoding="utf-8") as handle:
		return handle.read()


@pytest.mark.parametrize("relative", _ACTIVE_DOCS)
def test_no_active_document_teaches_role_derived_phase(relative):
	"""The first false model: that a handoff's destination ROLE decides
	its phase. W38 removed it from the authority; a document that still
	teaches it sends an operator to a prediction the product refuses."""
	flat = " ".join(_repo_text(relative).split())
	for phrase in _ROLE_DERIVES_PHASE:
		assert phrase not in flat, f"{relative} still teaches: {phrase!r}"


@pytest.mark.parametrize("relative", _ACTIVE_DOCS)
def test_no_active_document_teaches_phase_as_a_work_stage(relative):
	"""The second: that phase names what KIND of work is happening, and
	that claiming leaves it alone. Both are now false in the same
	sentence — claiming IS what makes Work active."""
	flat = " ".join(_repo_text(relative).split())
	for phrase in _PHASE_IS_A_STAGE:
		assert " ".join(phrase.split()) not in flat, \
			f"{relative} still teaches: {phrase!r}"
	for value in _RETIRED_PHASES:
		assert value not in flat, \
			f"{relative} still shows the retired phase value {value!r}"


def test_the_guide_states_the_invariant_in_the_straight_through_path():
	"""Positive half: a scan for absent phrases passes on an empty file.
	The guide must actually SAY that claiming makes Work active, in the
	path a reader meets first."""
	flat = " ".join(_repo_text("docs/EFFECTIVE-BATON.md").split())
	assert "the phase becomes `active` in the same transaction" in flat
	assert "Handler and phase are one fact seen twice" in flat


def test_the_executable_specifications_do_not_teach_it_either():
	"""The suites are durable maintenance evidence: a docstring naming
	the superseded rule teaches the next maintainer just as effectively
	as the operator guide does."""
	root = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	offenders = []
	for base, _dirs, files in os.walk(os.path.join(root, "tests", "work")):
		for name in sorted(files):
			if not name.endswith(".py"):
				continue
			path = os.path.join(base, name)
			with open(path, encoding="utf-8") as handle:
				flat = " ".join(handle.read().split())
			for phrase in _ROLE_DERIVES_PHASE + _PHASE_IS_A_STAGE:
				if " ".join(phrase.split()) in flat:
					offenders.append(f"{name}: {phrase!r}")
	assert not offenders, ("executable specifications still teach the "
	                       "superseded model:\n  " + "\n  ".join(offenders))
