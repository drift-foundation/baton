"""W4303: a claim orphaned by a failed managed turn is recoverable.

`work/records/2026/08/finding-managed-turn-failure-orphans-claim/`.

The incident: the managed dispatcher delivered W2907 to `baton.codex`,
the agent claimed it atomically, and the turn terminated as `failed` one
second later without passing or releasing it. Five hours on, canonical
state still read `active` with that Handler while the runtime projection
reported the same context idle, and the participant's one claim slot
deadlocked — later review Work could not be claimed at all.

Recovery was then refused twice over. `release` resolved authority from
the Work's Route, and the Route's only handler WAS the failed
participant, so no configured operator could reach it. And `expect=`
compared a participant string, which is not a fence: the same
participant releasing and re-taking the Work leaves `expect=` matching
while the claim underneath is a different one.

Two ruled corrections, confirmed 2026-08-22 through obligation 4379:

  - a narrow accepted-configuration member capability, `recover`,
    separate from `config` and from Route-handler authority; and
  - a mandatory `episode=` compare-and-swap on EVERY release, so the
    exact (work, assignment episode, claimant) triple decides, and the
    authorization branch taken is journaled by name.
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
from baton_work import config as cf                           # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


def _document():
	"""THE incident's shape: one route whose ONLY handler is the managed
	participant that fails, plus an operator who is deliberately not on
	it, plus a bystander holding nothing."""
	document = fx.config_document(
		{"baton": {"members": {"codex": ["impl"], "slaw": ["approv"],
		                       "prompt": ["approv"]},
		           "kinds": ["bug"]},
		 "push": {"members": {"sl": ["impl"]}, "kinds": ["bug"]}})
	team = document["teams"]["baton"]
	team["routes"] = {"impl": {"role": "impl", "handlers": ["codex"]}}
	team["kinds"] = {"bug": {"display": "Bug", "route": "impl"}}
	# The recovery operator holds `recover` and NOT `config`; the
	# fixture's default grant is exactly what must not be load-bearing
	# here, since the ruling separates the two powers.
	team["participants"]["slaw"]["capabilities"] = ["recover"]
	team["participants"]["prompt"].pop("capabilities", None)
	return document


@pytest.fixture
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(_document(), handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="push.sl")
	store = bw.Authority(result["database"])
	yield store, config_path
	store.close()


def _orphaned(store):
	"""One Work claimed by the participant whose turn then died."""
	work = tr.create_work(store, team="baton", kind="bug",
	                      title="reconcile the orphan",
	                      origin="self-initiated",
	                      classification="confirmed-defect",
	                      author="codex", body="the managed turn failed"
	                      )["work_id"]
	tr.claim_work(store, work, actor_team="baton", actor="codex")
	return work, fx.episode_of(store, work)


# -- the capability itself ---------------------------------------------------

def test_recover_is_an_accepted_capability_separate_from_config():
	assert "recover" in cf.CAPABILITIES
	assert "config" in cf.CAPABILITIES, \
		"the narrow recovery capability must not have replaced config"


def test_an_unknown_capability_still_refuses(tmp_path):
	document = _document()
	document["teams"]["baton"]["participants"]["slaw"]["capabilities"] = \
		["release-anything"]
	path = os.path.join(str(tmp_path), "baton.json")
	with open(path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="release-anything"):
		lc.init_from_config(path, participant="push.sl")


# -- the recovery branch -----------------------------------------------------

def test_the_configured_operator_recovers_what_the_route_cannot(world):
	"""THE incident. The only handler of the endpoint is the participant
	that died holding the claim, so the ordinary branch has nobody left;
	the operator recovers it without joining the route."""
	store, _config = world
	work, episode = _orphaned(store)
	result = tr.release_claim(store, work, actor_team="baton",
	                          actor="slaw", expect="baton.codex",
	                          episode=episode,
	                          reason="the managed turn failed one second "
	                          "after claiming and never released it")
	assert result["released_claimant"] == "baton.codex"
	assert result["authorization"] == "recover"
	assert result["episode"] == episode
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work,)).fetchone()
	assert row["handler_team"] is None and row["phase"] == "queued"


def test_recovery_does_not_make_the_operator_a_handler(world):
	"""The capability authorizes ONE act. It is not a back door into the
	endpoint's ordinary workflow authority, which is the whole reason it
	is not implemented by adding the operator to the route."""
	store, _config = world
	work, episode = _orphaned(store)
	tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                 expect="baton.codex", episode=episode,
	                 reason="recovering the orphan")
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.classify(store, work, actor_team="baton", actor="slaw",
		            classification="limitation")
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.claim_work(store, work, actor_team="baton", actor="slaw")


def test_a_member_without_the_capability_is_refused_by_name(world):
	"""And the refusal names BOTH paths, so an operator reading it knows
	which one their deployment is missing."""
	store, _config = world
	work, episode = _orphaned(store)
	with pytest.raises(bw.WorkError) as refused:
		tr.release_claim(store, work, actor_team="baton", actor="prompt",
		                 expect="baton.codex", episode=episode,
		                 reason="trying without authority")
	message = str(refused.value)
	assert "neither a resolved handler" in message
	assert "`recover` capability" in message
	assert store.conn.execute(
		"SELECT handler_member FROM work WHERE id=?",
		(work,)).fetchone()["handler_member"] == "codex"


def test_the_capability_does_not_cross_team_ownership(world):
	"""A capability says what KIND of act a member may perform; it never
	makes another team's Work theirs. Same boundary `reroute` draws."""
	store, config_path = world
	document = _json.loads(open(config_path).read())
	document["teams"]["push"]["participants"]["sl"]["capabilities"] = \
		["config", "recover"]
	document["generation"] = 2
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="push.sl")
	work, episode = _orphaned(store)
	with pytest.raises(bw.WorkError, match="a member of baton holding"):
		tr.release_claim(store, work, actor_team="push", actor="sl",
		                 expect="baton.codex", episode=episode,
		                 reason="another team's claim")


def test_the_handler_branch_is_unchanged_and_journals_itself(world):
	"""Self-release still works exactly as it did, and says so."""
	store, _config = world
	work, episode = _orphaned(store)
	result = tr.release_claim(store, work, actor_team="baton",
	                          actor="codex", expect="baton.codex",
	                          episode=episode, reason="stepping away")
	assert result["authorization"] == "handler"
	journaled = store.conn.execute(
		"SELECT payload FROM events WHERE kind='release' "
		"ORDER BY seq DESC LIMIT 1").fetchone()["payload"]
	assert _json.loads(journaled)["authorization"] == "handler"


def test_the_recovery_branch_is_journaled_by_name(world):
	"""'A handler released its own claim' and 'an operator recovered
	somebody else's' are different operational events, and reading the
	branch back out of the participant string would be a guess."""
	store, _config = world
	work, episode = _orphaned(store)
	tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                 expect="baton.codex", episode=episode,
	                 reason="recovering the orphan")
	journaled = _json.loads(store.conn.execute(
		"SELECT payload FROM events WHERE kind='release' "
		"ORDER BY seq DESC LIMIT 1").fetchone()["payload"])
	assert journaled["authorization"] == "recover"
	assert journaled["episode"] == episode
	assert journaled["expect"] == "baton.codex"


# -- the episode fence -------------------------------------------------------

def test_every_release_names_its_episode_including_self_release(world):
	store, _config = world
	work, _episode = _orphaned(store)
	for actor in ("codex", "slaw"):
		with pytest.raises(TypeError):
			tr.release_claim(store, work, actor_team="baton", actor=actor,
			                 expect="baton.codex", reason="no fence")


@pytest.mark.parametrize("episode", [None, "4", 4.0, True, -1])
def test_a_non_episode_refuses_before_anything_commits(world, episode):
	store, _config = world
	work, _live = _orphaned(store)
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="assignment episode"):
		tr.release_claim(store, work, actor_team="baton", actor="codex",
		                 expect="baton.codex", episode=episode,
		                 reason="malformed fence")
	assert store.last_seq() == before


def test_a_stale_request_cannot_release_a_later_claim_by_the_same_participant(world):
	"""THE reason the claimant string alone was not a fence. A dispatcher
	retrying a failed-turn settlement, or an operator re-running a line
	from scrollback, must not abort execution nobody asked to
	interrupt."""
	store, _config = world
	work, first = _orphaned(store)
	tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                 expect="baton.codex", episode=first,
	                 reason="recovering the orphan")
	tr.claim_work(store, work, actor_team="baton", actor="codex")
	second = fx.episode_of(store, work)
	assert second != first, "release must mint a new assignment episode"
	with pytest.raises(bw.WorkError, match="never ends a later one"):
		tr.release_claim(store, work, actor_team="baton", actor="slaw",
		                 expect="baton.codex", episode=first,
		                 reason="the stale retry")
	assert store.conn.execute(
		"SELECT handler_member FROM work WHERE id=?",
		(work,)).fetchone()["handler_member"] == "codex"


def test_the_wrong_claimant_still_refuses_first(world):
	store, _config = world
	work, episode = _orphaned(store)
	with pytest.raises(bw.WorkError, match="claimed by baton.codex, not"):
		tr.release_claim(store, work, actor_team="baton", actor="slaw",
		                 expect="baton.prompt", episode=episode,
		                 reason="guessing whose execution this is")


def test_unclaimed_and_terminal_work_both_fail_closed(world):
	store, _config = world
	work, episode = _orphaned(store)
	tr.release_claim(store, work, actor_team="baton", actor="codex",
	                 expect="baton.codex", episode=episode,
	                 reason="stepping away")
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.release_claim(store, work, actor_team="baton", actor="slaw",
		                 expect="baton.codex",
		                 episode=fx.episode_of(store, work),
		                 reason="nothing to release")
	tr.claim_work(store, work, actor_team="baton", actor="codex")
	closed = fx.episode_of(store, work)
	tr.close_work(store, work, actor_team="baton", actor="codex",
	              outcome="satisfying", rationale="done after all")
	with pytest.raises(bw.WorkError, match="carries no claim to release"):
		tr.release_claim(store, work, actor_team="baton", actor="slaw",
		                 expect="baton.codex", episode=closed,
		                 reason="terminal")


def test_an_exact_retry_replays_and_a_changed_operand_refuses(world):
	"""Effectively-once still holds across the new operand: the SAME
	request replays its one committed result, and a request that differs
	only in the episode is a different request."""
	store, _config = world
	work, episode = _orphaned(store)
	first = tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                         expect="baton.codex", episode=episode,
	                         reason="recovering the orphan",
	                         op_id="w4303-recover-1")
	replay = tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                          expect="baton.codex", episode=episode,
	                          reason="recovering the orphan",
	                          op_id="w4303-recover-1")
	assert replay["seq"] == first["seq"]
	assert replay["released_claimant"] == "baton.codex"
	tr.claim_work(store, work, actor_team="baton", actor="codex")
	with pytest.raises(bw.WorkError, match="conflicting reuse|different request"):
		tr.release_claim(store, work, actor_team="baton", actor="slaw",
		                 expect="baton.codex",
		                 episode=fx.episode_of(store, work),
		                 reason="recovering the orphan",
		                 op_id="w4303-recover-1")


# -- discovery ---------------------------------------------------------------

def test_detail_publishes_the_episode_the_release_needs(world):
	"""An operand nothing publishes cannot be supplied. The recovery
	operator is deliberately NOT a route handler, so it never sees the
	readiness projection that carries the episode for the claimant."""
	store, _config = world
	work, episode = _orphaned(store)
	view = pj.detail(store, work, viewer_team="baton",
	                 viewer_member="slaw")
	assert view["episode_seq"] == episode
	tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                 expect=view["handler"]["participant"],
	                 episode=view["episode_seq"],
	                 reason="recovered from exactly what detail published")


def test_release_is_advertised_to_the_operator_who_can_perform_it(world):
	"""Discovery, not discovery-by-attempt: the projection offers the
	transition to the recovery operator exactly when the writer would
	grant it, and withholds it from a member holding neither authority."""
	store, _config = world
	work, episode = _orphaned(store)

	def offered(member):
		return pj.detail(store, work, viewer_team="baton",
		                 viewer_member=member)["available_transitions"]

	assert "release" in offered("slaw")
	assert "release" in offered("codex")
	assert "release" not in offered("prompt")
	tr.release_claim(store, work, actor_team="baton", actor="slaw",
	                 expect="baton.codex", episode=episode,
	                 reason="recovering the orphan")
	assert "release" not in offered("slaw"), \
		"an unclaimed Work advertised a claim to release"
