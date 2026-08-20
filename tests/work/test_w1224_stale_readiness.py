"""W1224: readiness never addresses the wrong participant.

`work/records/2026/08/finding-readiness-wrong-participant-after-pass/`.
Live v11 use produced three canonical contradictions in a row: after
`baton.codex` passed Work to `baton.impl`, the Codex readiness path
emitted "ready and unclaimed for baton.codex" while canonical `detail`
showed the Work queued at `baton.impl` with no handler and no reviewer
claim. The claim then failed authorization — the boundary doing its
job — but the wake was a lie somebody had to chase.

This file is the AUTHORITY half of locating that defect, and it clears
the projection: `participant_actions` moves the Work off the old
participant and onto the new endpoint under a new episode key in the
same transaction as the pass. Nothing about routing is inferred and
nothing lingers.

The window is downstream, in the Codex dispatcher's queue, where an
event can wait behind a running turn and drain after the pass. That
half is `tools/codex-event-bridge/test/stale_episode.test.mjs`.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import lifecycle as lc                          # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402


@pytest.fixture()
def world(tmp_path):
	"""Two endpoints with DIFFERENT handlers, which is what the live
	deployment has and what a single-route fixture cannot show: `impl`
	resolves to ada, `rview` to bee."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "bee": ["rview"]},
		          "kinds": ["bug", "rev"]}})
	lang = document["teams"]["lang"]
	lang["routes"] = {"build": {"role": "impl", "handlers": ["ada"]},
	                  "review": {"role": "rview", "handlers": ["bee"]}}
	lang["kinds"] = {"bug": {"display": "Bug", "route": "build"},
	                 "rev": {"display": "Rev", "route": "review"}}
	config_path = str(tmp_path / "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


def make_work(world, title="the passed work"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


def keys(world, member):
	return [action["action_key"] for action in pj.participant_actions(
		world["store"], viewer_team="lang",
		viewer_member=member)["actions"] if action["kind"] == "work"]


def claimed(world, member):
	return {action["action_key"]: action["claimed"]
	        for action in pj.participant_actions(
		        world["store"], viewer_team="lang",
		        viewer_member=member)["actions"]
	        if action["kind"] == "work"}


def state(world, work):
	view = pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")
	return (view["route"]["endpoint"],
	        (view["handler"] or {}).get("participant"), view["phase"])


# -- the reported sequence ----------------------------------------------------

def test_a_pass_moves_the_wake_in_the_same_transaction(world):
	"""The exact reported shape: a reviewer passes to the implementer's
	endpoint, and the reviewer must stop being woken for it."""
	born = make_work(world)
	work = born["work_id"]
	assert keys(world, "ada") and not keys(world, "bee")

	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over to review")

	assert state(world, work) == ("lang.rev", None, "queued")
	assert keys(world, "ada") == [], \
		"the previous participant is still woken for passed Work"
	assert len(keys(world, "bee")) == 1


def test_the_new_participant_gets_a_new_episode(world):
	"""Not the old key handed on: a pass is a new assignment episode,
	so delivery memory anywhere downstream cannot confuse the two."""
	born = make_work(world)
	work = born["work_id"]
	before = keys(world, "ada")[0]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over to review")
	after = keys(world, "bee")[0]
	assert after != before, (before, after)
	assert after.startswith("work:")


def test_held_work_is_never_unclaimed_to_anybody_else(world):
	"""The second contradiction in the report: `active`, Handler
	`baton.claude`, and another participant told it was ready AND
	unclaimed."""
	born = make_work(world)
	work = born["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert state(world, work)[1] == "lang.ada"
	assert claimed(world, "ada") == {keys(world, "ada")[0]: True}
	assert keys(world, "bee") == [], \
		"a claimed Work was offered to another participant"


def test_the_holder_sees_its_own_work_as_claimed(world):
	"""The claimant-continuation half of `wait` still works — the fix
	for the wrong participant must not cost the right one its own
	assignment after a restart."""
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	assert list(claimed(world, "ada").values()) == [True]


def test_a_pass_back_wakes_the_implementer_exactly_once(world):
	"""The legitimate direction, and the one that must keep working."""
	born = make_work(world)
	work = born["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="review please")
	tr.claim_work(world["store"], work, actor_team="lang", actor="bee")
	tr.pass_work(world["store"], work, actor_team="lang", actor="bee",
	             to="lang.bug", comment="changes requested")
	assert keys(world, "bee") == []
	assert len(keys(world, "ada")) == 1


def test_a_pass_claim_pass_race_leaks_nothing_backwards(world):
	"""Rapid pass/claim/pass, asserted after every step rather than at
	the end: an earlier episode must never be visible to the wrong
	participant at any point in the sequence."""
	born = make_work(world)
	work = born["work_id"]
	seen = []
	for step in range(3):
		tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
		seen.append((keys(world, "ada"), keys(world, "bee")))
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment=f"round {step}")
		seen.append((keys(world, "ada"), keys(world, "bee")))
		tr.claim_work(world["store"], work, actor_team="lang", actor="bee")
		seen.append((keys(world, "ada"), keys(world, "bee")))
		tr.pass_work(world["store"], work, actor_team="lang", actor="bee",
		             to="lang.bug", comment=f"back {step}")
		seen.append((keys(world, "ada"), keys(world, "bee")))
	for ada, bee in seen:
		assert not (ada and bee), \
			f"both participants were woken for one Work: {ada} {bee}"
	# every key ever offered to either side is distinct per episode
	offered = [key for ada, bee in seen for key in ada + bee]
	assert len(set(offered)) >= 4, offered


def test_readiness_stays_read_only_through_all_of_it(world):
	born = make_work(world)
	work = born["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over")
	before = world["store"].last_seq()
	for member in ("ada", "bee"):
		for _ in range(3):
			pj.participant_actions(world["store"], viewer_team="lang",
			                       viewer_member=member)
	assert world["store"].last_seq() == before, "a readiness read wrote"


def test_the_cli_refusal_remains_the_final_boundary(world):
	"""This Work removes a misleading wake; it does not weaken the
	authority behind it. A claim by the wrong participant still fails
	closed, naming the endpoint that may act."""
	born = make_work(world)
	work = born["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over")
	with pytest.raises(bw.WorkError) as refusal:
		tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert "lang.rev" in str(refusal.value), str(refusal.value)
