"""W49 (finding-acp-same-key-redelivery-loss): assignment episodes.

The live defect: W27 was delivered to `baton.claude`, reviewed, and
returned to the SAME participant between two bridge polls. Delivery was
keyed on Work identity alone and forgotten only when a poll observed the
key absent — and absence happened wholly between polls, so the return was
suppressed indefinitely and the agent was never woken.

An assignment episode is therefore its own identity: it mints when Work
becomes newly actionable for whoever its Current resolves, and NOT when
something merely changes about the Work. `last_change_seq` cannot serve,
because a claim, heartbeat, phase move, priority or classification edit
would each redeliver work nobody reassigned.
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
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		          "kinds": ["bug"]},
		 "rev": {"members": {"cass": ["rview"]}, "kinds": ["bug"]}})
	# TWO resolved handlers: a release must wake the whole endpoint,
	# not only the member who let go of the claim.
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title="w", team="lang", author="ada"):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b")


def key(world, work, member="ada", team="lang"):
	"""The episode locator this participant would be woken with, or None."""
	for action in pj.participant_actions(
			world["store"], viewer_team=team,
			viewer_member=member)["actions"]:
		if action["kind"] == "work" and action["work"] == work:
			return action["action_key"]
	return None


def test_pass_away_and_back_between_reads_is_a_new_episode(world):
	"""THE observed defect, reproduced end to end. ada holds Work, hands
	it to review, the reviewer hands it straight back — and a consumer
	that polled only before and after must still see two DIFFERENT
	episodes, because it never observed the key absent."""
	store = world["store"]
	work = make(world, "round trip")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before = key(world, work)
	assert before is not None
	# away to review and straight back, with no read in between
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="please review")
	tr.pass_work(store, work, actor_team="rev", actor="cass",
	             to="lang.bug", comment="changes please")
	after = key(world, work)
	assert after is not None, "the returned handoff never became actionable"
	assert after != before, \
		"a Work handed away and back between two polls kept its old " \
		"episode: this is exactly the suppression that lost W27"


def test_the_named_non_minting_mutations_never_redeliver(world):
	"""The other half of the contract, and the reason `last_change_seq`
	could not be reused: these all touch the Work row and MUST NOT wake
	anybody — least of all prompt a claimant because of their own claim."""
	store = world["store"]
	work = make(world, "steady")["work_id"]
	born = key(world, work)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert key(world, work) == born, "a claim minted an episode"
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	assert key(world, work) == born, "a heartbeat minted an episode"
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="research", reason=None)
	assert key(world, work) == born, "an ordinary phase move minted"
	tr.prioritize(store, work, actor_team="lang", actor="ada",
	              priority="high")
	assert key(world, work) == born, "a priority revision minted"
	tr.classify(store, work, actor_team="lang", actor="ada",
	            classification="confirmed-defect")
	assert key(world, work) == born, "a classification revision minted"
	# and the row's ordinary change identity DID move for all of them,
	# which is precisely why it cannot stand in for an episode
	row = store.conn.execute(
		"SELECT last_change_seq, episode_seq FROM work WHERE id=?",
		(work,)).fetchone()
	assert row["last_change_seq"] > row["episode_seq"], \
		"last_change_seq did not move; the contrast this test rests on " \
		"is not being exercised"


def test_release_mints_so_the_endpoint_is_woken_again(world):
	store = world["store"]
	work = make(world, "recovered")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	held = key(world, work)
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="handing back")
	freed = key(world, work)
	assert freed is not None and freed != held, \
		"an explicit release did not open a new assignment episode"
	# every eligible handler, not just the releaser
	assert key(world, work, member="bee") == freed


def test_dependency_and_child_unblock_mint(world):
	"""A false-to-true readiness flip is a wake nobody passed."""
	store = world["store"]
	work = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada")
	assert key(world, work) is None, "a blocked Work stayed actionable"
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	unblocked = key(world, work)
	assert unblocked is not None, "the unblock never became actionable"
	child = tr.create_work(store, team="lang", kind="bug",
	                       title="child", origin="decomposition",
	                       classification="suspected-defect",
	                       author="ada", body="b",
	                       parent=work)["work_id"]
	assert key(world, work) is None, "an open child left the parent ready"
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	after_child = key(world, work)
	assert after_child is not None and after_child != unblocked, \
		"the child-gate unblock did not mint a new episode"


def test_parked_resume_mints_but_parking_does_not(world):
	store = world["store"]
	work = make(world, "resting")["work_id"]
	born = key(world, work)
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert key(world, work) is None, "parked Work stayed actionable"
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued", reason=None)
	resumed = key(world, work)
	assert resumed is not None and resumed != born, \
		"the parked-to-queued resume did not mint a new episode"


def test_the_episode_is_authority_derived_and_survives_restart(world):
	"""Not a local poll counter: two independent clients — and the same
	client across a restart — must agree on the episode identity."""
	store = world["store"]
	work = make(world, "shared")["work_id"]
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="rev.bug", comment="over")
	tr.pass_work(store, work, actor_team="rev", actor="cass",
	             to="lang.bug", comment="back")
	live = key(world, work)
	fresh = bw.Authority(world["database"])
	try:
		reread = [action["action_key"] for action in
		          pj.participant_actions(fresh, viewer_team="lang",
		                                 viewer_member="ada")["actions"]
		          if action["kind"] == "work"]
		assert live in reread, \
			"a restarted client disagreed about the episode identity"
	finally:
		fresh.close()


def test_the_key_agrees_with_its_structured_fields(world):
	"""Consumers never parse the key to recover identity, and the
	external bridge validators refuse a key that disagrees — so the
	authority must emit them consistently."""
	world_work = make(world, "shaped")["work_id"]
	action = next(a for a in pj.participant_actions(
		world["store"], viewer_team="lang",
		viewer_member="ada")["actions"] if a["kind"] == "work")
	assert action["work"] == world_work
	assert action["action_key"] == (
		f"work:{action['work']}:{action['episode_seq']}"
		f":g{action['config_generation']}")
	assert isinstance(action["episode_seq"], int)
	assert isinstance(action["config_generation"], int)
