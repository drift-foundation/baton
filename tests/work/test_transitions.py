"""A2: Work + containment — atomic creation, closure roll-up, reopen.

The property under test throughout is LEVEL-TRIGGERED readiness: every
assertion about `ready` is an assertion about recomputation from current
state, and the reopen tests exist precisely because an event-forwarding
implementation passes the close tests and fails these.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402


@pytest.fixture
def store(tmp_path):
	with bw.Authority.init(str(tmp_path / "work.sqlite3")) as authority:
		authority.register_team("lang", "Language")
		authority.register_member("lang", "slaw", "Slawomir")
		authority.register_kind("lang", "bug", "Bug intake")
		authority.register_kind("lang", "rsrch", "Research")
		authority.register_kind("lang", "old", "Retired road")
		authority.retire_kind("lang", "old")
		yield authority


def _ready(store, work_id):
	return store.conn.execute("SELECT ready FROM work WHERE id=?",
	                          (work_id,)).fetchone()["ready"]


def _create(store, title="Parser crash", parent=None, kind="bug"):
	return tr.create_work(store, team="lang", kind=kind, title=title,
	                      origin="external-report", author="slaw",
	                      body=f"report: {title}", parent=parent)


# -- creation ----------------------------------------------------------------

def test_create_is_work_plus_first_message_in_one_event(store):
	result = _create(store)
	work_id = result["work_id"]
	assert work_id.endswith(f"-W{result['seq']}")
	assert work_id.startswith(store.meta()["authority_uuid"][:8]), \
		"the id does not carry the authority qualifier"
	message = store.conn.execute("SELECT * FROM messages WHERE work=?",
	                             (work_id,)).fetchone()
	assert message["seq"] == result["seq"], \
		"the first message is a separate event from its work"
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work_id,)).fetchone()
	assert (row["origin"], row["classification"], row["status"]) == \
		("external-report", None, "open")
	assert (row["current_team"], row["current_kind"]) == ("lang", "bug")
	assert _ready(store, work_id) == 1, "a fresh leaf is ready"


def test_a_failure_after_the_work_insert_leaves_neither_row(store):
	"""The A2 crash-injection: die between the two inserts and NOTHING is
	observable — no work, no message, no burned sequence number."""
	prefix = store.meta()["authority_uuid"][:8]

	def half_then_boom(conn, seq):
		conn.execute(
			"INSERT INTO work (id, team, title, origin, status, "
			"current_team, current_kind, ready, created_seq) "
			"VALUES (?, 'lang', 'orphan', 'external-report', 'open', "
			"'lang', 'bug', 0, ?)", (f"{prefix}-W{seq}", seq))
		raise RuntimeError("crash between work and first message")

	with pytest.raises(RuntimeError):
		store._write("create_work", "lang.slaw", {}, half_then_boom)
	assert store.conn.execute("SELECT COUNT(*) AS n FROM work").fetchone()["n"] == 0
	assert store.conn.execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == 0
	follow = _create(store)
	assert follow["seq"] == store.last_seq(), "the crash burned a number"


@pytest.mark.parametrize("kwargs,fragment", [
	(dict(title="  "), "non-empty"),
	(dict(origin="made-up"), "not one of"),
	(dict(body=""), "non-empty"),
	(dict(kind="nosuch"), "not a registered endpoint"),
	(dict(kind="old"), "retired"),
	(dict(author="ghost"), "not a registered member"),
])
def test_creation_refuses_bad_inputs_before_writing(store, kwargs, fragment):
	base = dict(team="lang", kind="bug", title="t", origin="external-report",
	            author="slaw", body="b")
	base.update(kwargs)
	with pytest.raises(bw.WorkError, match=fragment):
		tr.create_work(store, **base)
	assert store.conn.execute("SELECT COUNT(*) AS n FROM work").fetchone()["n"] == 0


def test_a_child_of_a_closed_parent_is_refused(store):
	parent = _create(store)["work_id"]
	tr.close_work(store, parent, actor_team="lang", actor="slaw",
	              disposition="fixed")
	with pytest.raises(bw.WorkError, match="does not grow new children"):
		_create(store, title="late child", parent=parent)


# -- closure roll-up ---------------------------------------------------------

def test_children_gate_the_parent_level_triggered(store):
	parent = _create(store, "epic")["work_id"]
	child_a = _create(store, "step a", parent=parent)["work_id"]
	child_b = _create(store, "step b", parent=parent)["work_id"]
	assert _ready(store, parent) == 0, "open children left the parent ready"

	tr.close_work(store, child_a, actor_team="lang", actor="slaw",
	              disposition="done")
	assert _ready(store, parent) == 0, "one open child still gates"
	tr.close_work(store, child_b, actor_team="lang", actor="slaw",
	              disposition="done")
	assert _ready(store, parent) == 1, "all children closed; parent not ready"


def test_closing_over_open_children_is_refused_by_name(store):
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	with pytest.raises(bw.WorkError, match=child):
		tr.close_work(store, parent, actor_team="lang", actor="slaw",
		              disposition="premature")
	assert store.conn.execute("SELECT status FROM work WHERE id=?",
	                          (parent,)).fetchone()["status"] == "open"


def test_close_clears_current_and_next_terminally(store):
	work = _create(store)["work_id"]
	tr.close_work(store, work, actor_team="lang", actor="slaw",
	              disposition="fixed and verified")
	row = store.conn.execute("SELECT * FROM work WHERE id=?", (work,)).fetchone()
	assert row["status"] == "closed"
	assert row["current_team"] is None and row["current_kind"] is None
	assert row["next_team"] is None and row["next_kind"] is None
	assert row["ready"] == 0
	assert row["closed_seq"] is not None


def test_close_requires_a_disposition(store):
	work = _create(store)["work_id"]
	with pytest.raises(bw.WorkError, match="disposition"):
		tr.close_work(store, work, actor_team="lang", actor="slaw",
		              disposition="  ")


# -- reopen ------------------------------------------------------------------

def test_reopen_visibly_reopens_the_ancestor_gate(store):
	"""The confirmed behavior verbatim: adding or reopening a required
	descendant visibly reopens the ancestor gate — and it must happen through
	recomputation, which the A3 break-sweep will hold in place."""
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="slaw",
	              disposition="done")
	assert _ready(store, parent) == 1

	tr.reopen_work(store, child, actor_team="lang", actor="slaw",
	               reason="the fix regressed")
	assert _ready(store, parent) == 0, "the ancestor gate did not reopen"
	assert store.conn.execute("SELECT status FROM work WHERE id=?",
	                          (child,)).fetchone()["status"] == "open"
	assert _ready(store, child) == 1


def test_reopen_under_a_closed_parent_is_refused_top_down(store):
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="slaw",
	              disposition="done")
	tr.close_work(store, parent, actor_team="lang", actor="slaw",
	              disposition="shipped")
	with pytest.raises(bw.WorkError, match="reopen the ancestry first"):
		tr.reopen_work(store, child, actor_team="lang", actor="slaw",
		               reason="regressed")


def test_reopen_requires_a_reason_and_a_closed_work(store):
	work = _create(store)["work_id"]
	with pytest.raises(bw.WorkError, match="not closed"):
		tr.reopen_work(store, work, actor_team="lang", actor="slaw",
		               reason="r")
	tr.close_work(store, work, actor_team="lang", actor="slaw",
	              disposition="done")
	with pytest.raises(bw.WorkError, match="reason"):
		tr.reopen_work(store, work, actor_team="lang", actor="slaw",
		               reason=" ")


# -- audit -------------------------------------------------------------------

def test_every_transition_is_one_audited_event(store):
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="slaw",
	              disposition="done")
	tr.reopen_work(store, child, actor_team="lang", actor="slaw",
	               reason="regressed")
	kinds = [event["kind"] for event in store.events()]
	assert kinds == ["register_team", "register_member", "register_kind",
	                 "register_kind", "register_kind", "retire_kind",
	                 "create_work", "create_work", "close_work",
	                 "reopen_work"]
	seqs = [event["seq"] for event in store.events()]
	assert seqs == list(range(1, len(kinds) + 1))


def test_reopen_restores_the_endpoint_the_close_cleared(store):
	"""No open work without a responsible endpoint — RULED, and the easy
	defect is exactly the one this pins: close nulls `Current`, so a reopen
	that 'restores' from the live row restores NULL and quietly creates
	ownerless open work."""
	work = _create(store, kind="rsrch")["work_id"]
	tr.close_work(store, work, actor_team="lang", actor="slaw",
	              disposition="done")
	tr.reopen_work(store, work, actor_team="lang", actor="slaw",
	               reason="regressed")
	row = store.conn.execute("SELECT * FROM work WHERE id=?", (work,)).fetchone()
	assert row["status"] == "open"
	assert (row["current_team"], row["current_kind"]) == ("lang", "rsrch"), \
		f"reopened work has no responsible endpoint: {dict(row)}"
