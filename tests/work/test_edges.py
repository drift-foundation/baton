"""A3: dependency edges and the convergence model.

The centerpiece is the finding's own LANG-42 scenario: three teams converge
on one provider Work, and its terminal close satisfies every qualifying edge
through level-triggered recomputation. (WS-2: closure is immutable; the
former reopen legs became follow-up-work rules, tested here.)
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402,F401
from baton_work import transitions as tr                      # noqa: E402


import fixtures as fx


@pytest.fixture
def store(tmp_path):
	spec = {team: {"members": {member: ["dev"]}, "kinds": ["bug"]}
	        for team, member in (("lang", "ada"), ("push", "sl"),
	                             ("web", "wren"), ("mdb", "mo"))}
	with fx.open_instance(str(tmp_path), spec) as authority:
		yield authority


def _create(store, team, member, title, parent=None):
	return tr.create_work(store, team=team, kind="bug", title=title,
	                      origin="external-report", classification="suspected-defect", author=member,
	                      body=f"report: {title}", parent=parent)["work_id"]


def _ready(store, work_id):
	return store.conn.execute("SELECT ready FROM work WHERE id=?",
	                          (work_id,)).fetchone()["ready"]


def _block(store, work, blocker, team="push", member="sl"):
	return tr.add_dependency(store, work, blocker,
	                         actor_team=team, actor=member)


# -- the convergence scenario ------------------------------------------------

def test_lang_42_three_consumers_one_close_fans_out(store):
	"""The finding's canonical case, executed: Pushcoin, Web and MariaDB each
	independently blocked by one Lang record; its close unblocks each
	INDEPENDENTLY — the one with a second blocker stays blocked."""
	lang42 = _create(store, "lang", "ada", "parser recovery")
	pushcoin = _create(store, "push", "sl", "checkout fails")
	web = _create(store, "web", "wren", "render crash")
	mariadb = _create(store, "mdb", "mo", "driver hang")
	other = _create(store, "mdb", "mo", "schema review")

	_block(store, pushcoin, lang42)
	_block(store, web, lang42, team="web", member="wren")
	_block(store, mariadb, lang42, team="mdb", member="mo")
	_block(store, mariadb, other, team="mdb", member="mo")

	assert [_ready(store, w) for w in (pushcoin, web, mariadb)] == [0, 0, 0]

	tr.close_work(store, lang42, actor_team="lang", actor="ada",
	              rationale="fixed and verified", outcome="satisfying")

	assert _ready(store, pushcoin) == 1
	assert _ready(store, web) == 1
	assert _ready(store, mariadb) == 0, \
		"a dependent with another open blocker became ready"
	assert _ready(store, other) == 1

	# The provider sees the fan-in; that is the whole point of dedup.
	incoming = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges WHERE blocker=?",
		(lang42,)).fetchone()["n"]
	assert incoming == 3


def test_closure_is_immutable_and_late_evidence_becomes_follow_up(store):
	"""WS-2: no reopen exists. A later contradiction creates follow-up
	work; prior consumers are never silently re-blocked — each affected one
	gains its own NEW explicit edge."""
	lang42 = _create(store, "lang", "ada", "parser recovery")
	pushcoin = _create(store, "push", "sl", "checkout fails")
	web = _create(store, "web", "wren", "render crash")
	_block(store, pushcoin, lang42)
	_block(store, web, lang42, team="web", member="wren")
	tr.close_work(store, lang42, actor_team="lang", actor="ada",
	              rationale="fixed", outcome="satisfying")
	assert (_ready(store, pushcoin), _ready(store, web)) == (1, 1)

	follow = tr.create_work(store, team="lang", kind="bug",
	                        title="regression follow-up",
	                        origin="external-report", classification="suspected-defect", author="ada",
	                        body="push contradicts the fix",
	                        follow_up_of=lang42)["work_id"]
	_block(store, pushcoin, follow)
	assert _ready(store, pushcoin) == 0, "the new explicit edge did not gate"
	assert _ready(store, web) == 1, \
		"a prior consumer was silently re-blocked"


def test_a_new_blocker_may_target_only_open_work(store):
	"""WS-2: a dependency on finished work gates nothing and is refused;
	the live relationship belongs to follow-up work."""
	lang42 = _create(store, "lang", "ada", "parser recovery")
	tr.close_work(store, lang42, actor_team="lang", actor="ada",
	              rationale="fixed", outcome="satisfying")
	pushcoin = _create(store, "push", "sl", "checkout fails")
	with pytest.raises(bw.WorkError, match="only open Work"):
		_block(store, pushcoin, lang42)
	assert _ready(store, pushcoin) == 1


# -- cycle refusal over the union --------------------------------------------

def test_a_dependency_cycle_is_refused_with_the_loop_named(store):
	a = _create(store, "lang", "ada", "a")
	b = _create(store, "push", "sl", "b")
	c = _create(store, "web", "wren", "c")
	_block(store, a, b, team="lang", member="ada")
	_block(store, b, c)
	with pytest.raises(bw.WorkError, match="closes a loop"):
		_block(store, c, a, team="web", member="wren")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 2


def test_a_cycle_through_containment_and_dependency_together_is_refused(store):
	"""The union case: each graph alone is acyclic, the union is not. Parent
	waits on child (containment); child's blocker waiting on the parent
	closes the loop."""
	parent = _create(store, "lang", "ada", "epic")
	child = _create(store, "lang", "ada", "step", parent=parent)
	external = _create(store, "push", "sl", "external need")
	_block(store, external, parent)
	with pytest.raises(bw.WorkError, match="closes a loop"):
		_block(store, child, external, team="lang", member="ada")


def test_self_and_duplicate_edges_are_refused(store):
	a = _create(store, "lang", "ada", "a")
	b = _create(store, "push", "sl", "b")
	with pytest.raises(bw.WorkError, match="cannot block itself"):
		_block(store, a, a, team="lang", member="ada")
	_block(store, a, b, team="lang", member="ada")
	with pytest.raises(bw.WorkError, match="already blocked"):
		_block(store, a, b, team="lang", member="ada")


def test_a_closed_work_takes_no_new_blockers(store):
	a = _create(store, "lang", "ada", "a")
	b = _create(store, "push", "sl", "b")
	tr.close_work(store, a, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="takes\\s+no new blockers|no new blockers"):
		_block(store, a, b, team="lang", member="ada")


# -- blockers and children gate together -------------------------------------

def test_readiness_is_the_conjunction_of_children_and_blockers(store):
	parent = _create(store, "lang", "ada", "epic")
	child = _create(store, "lang", "ada", "step", parent=parent)
	external = _create(store, "push", "sl", "provider fix")
	_block(store, parent, external, team="lang", member="ada")

	assert _ready(store, parent) == 0
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _ready(store, parent) == 0, "an open blocker stopped gating"
	tr.close_work(store, external, actor_team="push", actor="sl",
	              rationale="done", outcome="satisfying")
	assert _ready(store, parent) == 1
