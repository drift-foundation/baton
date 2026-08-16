"""A2: Work + containment — atomic creation, closure roll-up, immutability.

The property under test throughout is LEVEL-TRIGGERED readiness: every
assertion about `ready` is an assertion about recomputation from current
state. (WS-2: closure is immutable — the former reopen tests became the
follow-up rules tested here.)
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


import copy
import json as _json

import fixtures as fx
from baton_work import lifecycle as lc


@pytest.fixture
def store(tmp_path):
	spec = {"lang": {"members": {"slaw": ["dev"]},
	                 "kinds": ["bug", "rsrch", "old"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	# Retire "old" the only way the boundary allows: a generation-2
	# acceptance that drops it.
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["kinds"]["old"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.slaw")
	with bw.Authority(database) as authority:
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
	message = store.conn.execute(
		"SELECT messages.* FROM messages JOIN threads "
		"ON threads.id = messages.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=?",
	                             (work_id,)).fetchone()
	assert message["seq"] == result["seq"], \
		"the first message is a separate event from its work"
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work_id,)).fetchone()
	assert (row["origin"], row["classification"], row["status"]) == \
		("external-report", "unknown", "open"), \
		"classification is canonical `unknown`, never null (WS-1)"
	assert row["phase"] == "queued", "new work defaults to queued (WS-1)"
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
	              rationale="fixed", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="does not grow new children"):
		_create(store, title="late child", parent=parent)


# -- closure roll-up ---------------------------------------------------------

def test_children_gate_the_parent_level_triggered(store):
	parent = _create(store, "epic")["work_id"]
	child_a = _create(store, "step a", parent=parent)["work_id"]
	child_b = _create(store, "step b", parent=parent)["work_id"]
	assert _ready(store, parent) == 0, "open children left the parent ready"

	tr.close_work(store, child_a, actor_team="lang", actor="slaw",
	              rationale="done", outcome="satisfying")
	assert _ready(store, parent) == 0, "one open child still gates"
	tr.close_work(store, child_b, actor_team="lang", actor="slaw",
	              rationale="done", outcome="satisfying")
	assert _ready(store, parent) == 1, "all children closed; parent not ready"


def test_closing_over_open_children_is_refused_by_name(store):
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	with pytest.raises(bw.WorkError, match=child):
		tr.close_work(store, parent, actor_team="lang", actor="slaw",
		              rationale="premature", outcome="satisfying")
	assert store.conn.execute("SELECT status FROM work WHERE id=?",
	                          (parent,)).fetchone()["status"] == "open"


def test_close_clears_current_and_next_terminally(store):
	work = _create(store)["work_id"]
	tr.close_work(store, work, actor_team="lang", actor="slaw",
	              rationale="fixed and verified", outcome="satisfying")
	row = store.conn.execute("SELECT * FROM work WHERE id=?", (work,)).fetchone()
	assert row["status"] == "closed"
	assert row["current_team"] is None and row["current_kind"] is None
	assert row["next_team"] is None and row["next_kind"] is None
	assert row["ready"] == 0
	assert row["closed_seq"] is not None


def test_close_requires_a_rationale(store):
	work = _create(store)["work_id"]
	with pytest.raises(bw.WorkError, match="rationale"):
		tr.close_work(store, work, actor_team="lang", actor="slaw",
		              rationale="  ", outcome="satisfying")


# -- audit -------------------------------------------------------------------

def test_every_transition_is_one_audited_event(store):
	parent = _create(store, "epic")["work_id"]
	child = _create(store, "step", parent=parent)["work_id"]
	tr.close_work(store, child, actor_team="lang", actor="slaw",
	              rationale="done", outcome="satisfying")
	follow = tr.create_work(store, team="lang", kind="bug",
	                        title="follow-up", origin="external-report",
	                        author="slaw", body="late evidence",
	                        follow_up_of=child)
	kinds = [event["kind"] for event in store.events()]
	assert kinds == ["accept_config", "accept_config",
	                 "create_work", "create_work", "close_work",
	                 "create_work"]
	seqs = [event["seq"] for event in store.events()]
	assert seqs == list(range(1, len(kinds) + 1))
	assert follow["seq"] == seqs[-1]


def test_closed_work_is_terminal_and_follow_up_is_the_only_new_reference(
		store):
	"""WS-2 immutable closure: the closed record refuses every mutation;
	reading it and marking it seen remain; new work may point at it via
	follow_up_of — which must name a CLOSED work and gates nothing."""
	work = _create(store, kind="rsrch")["work_id"]
	with pytest.raises(bw.WorkError, match="still open"):
		tr.create_work(store, team="lang", kind="bug", title="early",
		               origin="external-report", author="slaw", body="b",
		               follow_up_of=work)
	tr.close_work(store, work, actor_team="lang", actor="slaw",
	              rationale="done", outcome="satisfying")
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work,)).fetchone()
	assert row["outcome"] == "satisfying"
	assert (row["current_team"], row["current_kind"]) == (None, None)
	# mark_seen mutates the VIEWER's cursor, not the record: allowed.
	fx.mark_all_seen(store, work, team="lang", member="slaw",
	             up_to_seq=store.last_seq())
	follow = tr.create_work(store, team="lang", kind="bug",
	                        title="follow-up", origin="external-report",
	                        author="slaw", body="late evidence",
	                        follow_up_of=work)["work_id"]
	assert store.conn.execute(
		"SELECT follow_up_of FROM work WHERE id=?",
		(follow,)).fetchone()["follow_up_of"] == work
	assert store.conn.execute("SELECT ready FROM work WHERE id=?",
	                          (follow,)).fetchone()["ready"] == 1, \
		"follow_up_of gated the new work"


# -- WF-09 extracted regressions: terminal competitors validate in the lock --
#
# Workflow-to-regression rule (WORKFLOW-TESTS.md): WF-09's race checkpoints
# found respond AND dispose both committing against one obligation — every
# terminal-competition check ran only BEFORE the write lock. These model the
# exact interleaving deterministically: the competing commit lands between
# the optimistic pre-read and the write transaction, through the `_write`
# seam (the same modeling the C4 review used for include expansion).

def _race_pair(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	return bw.Authority(database), bw.Authority(database)


def _interleave(store, competing):
	"""Run `competing` between store's next optimistic pre-read and its
	write transaction."""
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


def test_wf09_race1_obligation_terminal_actions_exclude_in_the_lock(tmp_path):
	"""WF-09 race 1: two members race respond/dispose on one obligation;
	exactly one commits and the loser refuses INSIDE the lock."""
	racer, other = _race_pair(tmp_path)
	work = tr.create_work(racer, team="push", kind="bug", title="w",
	                      origin="external-report", author="sl",
	                      body="b")["work_id"]
	asked = fx.post(racer, work, author_team="push", author="sl",
	                        body="yours?", request="lang.bug")["seq"]
	_interleave(racer, lambda: tr.dispose_obligation(
		other, asked, team="lang", member="ada",
		disposition="not ours after all"))
	messages_before = racer.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
	with pytest.raises(bw.WorkError, match="already disposed"):
		tr.respond_obligation(racer, asked, team="lang", member="ada",
		                      body="ours; tracked")
	row = racer.conn.execute("SELECT status FROM obligations WHERE seq=?",
	                         (asked,)).fetchone()
	assert row["status"] == "disposed"
	assert racer.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == \
		messages_before, "the losing respond still published its message"
	kinds = [event["kind"] for event in racer.events()]
	assert kinds.count("dispose") == 1 and kinds.count("respond") == 0


def test_wf09_race2_a_pass_losing_to_a_terminal_close_refuses(tmp_path):
	"""WF-09 race 2: pass and close race; if the close serializes first the
	pass must refuse in the lock, never resurrect Current on closed work."""
	racer, other = _race_pair(tmp_path)
	work = tr.create_work(racer, team="lang", kind="bug", title="w",
	                      origin="external-report", author="ada",
	                      body="b")["work_id"]
	_interleave(racer, lambda: tr.close_work(
		other, work, actor_team="lang", actor="ada",
		rationale="fixed and verified", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="closed"):
		fx.post(racer, work, author_team="lang", author="ada",
		                body="handing over", pass_to="lang.rev")
	row = racer.conn.execute(
		"SELECT status, current_team, current_kind FROM work WHERE id=?",
		(work,)).fetchone()
	assert row["status"] == "closed"
	assert row["current_team"] is None and row["current_kind"] is None, \
		"the losing pass resurrected Current on a terminal work"


def test_wf09_race2_close_records_the_current_that_committed(tmp_path):
	"""WF-09 race 2, other serialization: a pass lands between close's
	pre-read and its lock. The close event must record the endpoint that
	was REALLY live at commit — history is where cleared facts live, and
	a stale record would lie about who last held the baton."""
	racer, other = _race_pair(tmp_path)
	work = tr.create_work(racer, team="lang", kind="bug", title="w",
	                      origin="external-report", author="ada",
	                      body="b")["work_id"]
	_interleave(racer, lambda: fx.post(
		other, work, author_team="lang", author="ada",
		body="quick handoff", pass_to="lang.rev"))
	tr.close_work(racer, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	closing = next(event for event in racer.events()
	               if event["kind"] == "close_work")
	assert closing["payload"]["was_current_kind"] == "rev", \
		"the close recorded the pre-race Current"


def test_wf09_double_close_refuses_in_the_lock(tmp_path):
	racer, other = _race_pair(tmp_path)
	work = tr.create_work(racer, team="lang", kind="bug", title="w",
	                      origin="external-report", author="ada",
	                      body="b")["work_id"]
	_interleave(racer, lambda: tr.close_work(
		other, work, actor_team="lang", actor="ada",
		rationale="done first", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="already closed"):
		tr.close_work(racer, work, actor_team="lang", actor="ada",
		              rationale="done second", outcome="satisfying")
	kinds = [event["kind"] for event in racer.events()]
	assert kinds.count("close_work") == 1
