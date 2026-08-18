"""W73, SUPERSEDED by W38 (finding-phase-is-scheduler-state).

W73 ruled that a handoff derives its phase from the destination route's
stage role: implementation handoffs landed `active`, review handoffs
`review`. That made the word active mean "routed to implementers"
rather than "somebody is working on it" — three Works read `active`
with one real claimant between them, which is the observation that
produced W38.

Phase is now a closed SCHEDULER axis. A handoff hands over
responsibility, not activity, so every destination role lands the same
way: `queued` when runnable, `waiting` when a gate is unsatisfied. What
kind of work it is stays in the Route's role; who is doing it is the
Handler; `active` arrives only with a claim.

W73's surviving half is intact and still asserted here: `pass` takes no
`phase=` operand, and the destination state is derived under the same
lock that moves the Route.
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
	row = world["store"].conn.execute(
		"SELECT phase FROM work WHERE id=?", (work,)).fetchone()
	return row["phase"]


ROLE_KINDS = ("impl", "rev", "sign", "dev", "short", "odd")


@pytest.mark.parametrize("kind", ROLE_KINDS)
def test_every_destination_role_lands_queued(world, kind):
	"""W38 acceptance 2. Implementation, review, research, approval and
	the stageless route all produce the SAME scheduler state, because
	none of them says anybody has started."""
	work = make(world)
	result = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="ada", to=f"lang.{kind}",
	                      comment="over")
	assert result["destination_phase"] == "queued", result
	assert phase_of(world, work) == "queued"


def test_a_stageless_role_no_longer_refuses(world):
	"""Under W73 a role outside the stage map refused the handoff. With
	phase no longer derived from the role, there is nothing left to
	refuse for: `ops` routes like any other."""
	work = make(world)
	result = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="ada", to="lang.odd", comment="over")
	assert result["destination_phase"] == "queued"
	assert result["to"] == "lang.odd"


def test_a_gated_handoff_lands_waiting(world):
	"""The other half of the derivation: the destination state comes
	from the committed gates, so a blocked Work cannot land in a
	runnable-looking phase nobody can claim."""
	work = make(world)
	blocker = make(world)
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	result = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="ada", to="lang.impl", comment="over")
	assert result["destination_phase"] == "waiting"
	assert phase_of(world, work) == "waiting"


def test_pass_still_takes_no_phase_operand(world):
	"""W73's surviving half: the caller never supplies a destination
	phase, so the handoff cannot advertise a state nobody is in."""
	assert "phase" not in {
		key["name"] for key in work_cli.GRAMMAR["pass"]["keys"]}


def test_claiming_after_the_handoff_is_what_makes_it_active(world):
	"""The whole point of the supersession, in one sequence."""
	work = make(world)
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.impl", comment="over")
	assert phase_of(world, work) == "queued"
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert phase_of(world, work) == "active"
