"""W73 (finding-route-derived-handoff-phase): the route decides.

The live defect: W49 was passed to `baton.impl` with `phase=queued`.
Claude claimed it atomically and began editing and testing, while the
canonical Work projected BOTH `active=baton.claude` and `phase=queued`.
The claim stayed exclusive, so nothing was lost — but the operational
view was false, and as more agents share a route that produces noisy
acquisition attempts and bad scheduling.

The correction is authority enforcement, not documentation: `pass`
has no `phase=` operand at all, and the destination route's stage role
decides the phase atomically with Current. The false state is
unrepresentable through the public handoff.
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
from baton_work import transitions as tr                      # noqa: E402
from baton_work.transitions import STAGE_PHASES               # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	"""One team with a route per stage role, plus a stageless one."""
	document = fx.config_document(
		{"lang": {"members": {"ada": ["rsrch", "impl", "rview",
		                              "approv", "dev", "rev", "ops"]},
		          "kinds": ["bug"]}})
	team = document["teams"]["lang"]
	team["routes"] = {
		"intake": {"role": "rsrch", "handlers": ["ada"]},
		"build": {"role": "impl", "handlers": ["ada"]},
		"review": {"role": "rview", "handlers": ["ada"]},
		"sign": {"role": "approv", "handlers": ["ada"]},
		"devrt": {"role": "dev", "handlers": ["ada"]},
		"revrt": {"role": "rev", "handlers": ["ada"]},
		"misc": {"role": "ops", "handlers": ["ada"]},
	}
	team["kinds"] = {
		"bug": {"display": "Bug", "route": "intake"},
		"impl": {"display": "Impl", "route": "build"},
		"rev": {"display": "Rev", "route": "review"},
		"sign": {"display": "Sign", "route": "sign"},
		"dev": {"display": "Dev", "route": "devrt"},
		"short": {"display": "Short", "route": "revrt"},
		"odd": {"display": "Odd", "route": "misc"},
	}
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def make(world, kind="bug"):
	return tr.create_work(world["store"], team="lang", kind=kind,
	                      title="w", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]


def phase_of(world, work):
	return world["store"].conn.execute(
		"SELECT phase FROM work WHERE id=?", (work,)).fetchone()["phase"]


@pytest.mark.parametrize("kind,expected", [
	("impl", "active"),
	("rev", "review"),
	("sign", "review"),
	("bug", "research"),
	("dev", "active"),
	("short", "review"),
])
def test_every_stage_role_derives_its_phase(world, kind, expected):
	"""Handoffs to every mapped stage role derive the expected phase
	with no caller input — approver included."""
	work = make(world, "impl" if kind != "impl" else "rev")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to=f"lang.{kind}", comment="onward")
	assert phase_of(world, work) == expected


def test_a_handoff_never_produces_queued(world):
	"""The exact W49 shape: the sender cannot hand Work over as
	`queued` and then have it worked under a false stage."""
	assert "queued" not in STAGE_PHASES.values(), \
		"a stage role maps to queued; a route transfer could recreate " \
		"the false view W73 exists to remove"
	work = make(world)
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.impl", comment="please implement")
	assert phase_of(world, work) == "active"
	# and the claim that follows finds an honest stage
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert phase_of(world, work) == "active"


def test_the_operand_is_gone_from_every_surface(world):
	"""`phase=` is an unknown key on the public grammar and not a
	parameter of the authority call — the false state is
	unrepresentable, not merely discouraged."""
	work = make(world)
	with pytest.raises(TypeError):
		tr.pass_work(world["store"], work, actor_team="lang",
		             actor="ada", to="lang.rev", comment="x",
		             phase="queued")
	import contextlib
	import io
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", "lang.ada", "pass",
		                      f"work={work}", "to=lang.rev",
		                      "comment=x", "phase=review"])
	assert code != 0
	assert "unknown key 'phase'" in (out.getvalue() + err.getvalue())
	assert phase_of(world, work) == "queued", \
		"the refused handoff changed a byte"


def test_an_unmapped_destination_refuses_inside_the_transaction(world):
	work = make(world)
	store = world["store"]
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="names no work stage"):
		tr.pass_work(store, work, actor_team="lang", actor="ada",
		             to="lang.odd", comment="over to ops")
	assert store.last_seq() == before, "the refusal burned an event"
	row = store.conn.execute(
		"SELECT phase, route_kind FROM work WHERE id=?",
		(work,)).fetchone()
	assert row["phase"] == "queued" and row["route_kind"] == "bug", \
		"the refused handoff moved Current or phase"


def test_the_derived_phase_commits_with_everything_else(world):
	"""Current, phase, claim release, planned Next and the W49 episode
	are ONE atomic event — the whole point of deriving under the lock."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before_episode = store.conn.execute(
		"SELECT episode_seq FROM work WHERE id=?", (work,)).fetchone()[0]
	result = tr.pass_work(store, work, actor_team="lang", actor="ada",
	                      to="lang.impl", set_next="lang.rev",
	                      comment="onward")
	row = store.conn.execute(
		"SELECT phase, route_kind, next_kind, current_team, episode_seq "
		"FROM work WHERE id=?", (work,)).fetchone()
	assert row["phase"] == "active"
	assert row["route_kind"] == "impl"
	assert row["next_kind"] == "rev"
	assert row["current_team"] is None, "the sender's claim survived"
	assert row["episode_seq"] > before_episode, "no new episode minted"
	assert result["destination_phase"] == "active"
	# one event carried all of it
	events = [e for e in store.events() if e["seq"] == result["seq"]]
	assert len(events) == 1 and events[0]["kind"] == "pass"
	assert events[0]["payload"]["destination_phase"] == "active"


def test_same_route_phase_changes_remain_authorized_separately(world):
	"""W73 removes the handoff override, not `set_phase`."""
	store = world["store"]
	work = make(world)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.impl", comment="onward")
	assert phase_of(world, work) == "active"
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="review")
	assert phase_of(world, work) == "review", \
		"the separately authorized same-route stage change was lost"
