"""Terminal-outcome slice: the four-outcome atomic close.

One close mechanism, outcome exactly `satisfying`, `non-satisfying`,
`rejected`, or `cancelled`, every outcome carrying a non-empty rationale
as durable review evidence. A duplicate is a rejected close whose
structured reason names the surviving Work through the explicit
non-gating `duplicate_of` relation — free text alone is insufficient.
All four outcomes share the authority, child, dependency, withdrawal,
immutability, and follow-up semantics of the ordinary close.
"""

from __future__ import annotations

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store
	store.close()


def _create(store, team="lang", member="ada", **kw):
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", classification="suspected-defect", author=member,
	                      body="born speaking", **kw)


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


def _rig(store):
	"""The full-featured provider every outcome must dismantle
	identically: an open dependent that unblocks, a second dependent
	with another live gate, a planned Next, a pending carried `@`, and a
	pending verification assignment."""
	born = _create(store)
	work, thread = born["work_id"], born["thread"]
	single = _create(store, team="push", member="sl")["work_id"]
	tr.add_dependency(store, single, work, actor_team="push", actor="sl")
	gated = _create(store, team="web", member="wren")["work_id"]
	extra = _create(store, team="push", member="sl")["work_id"]
	tr.add_dependency(store, gated, work, actor_team="web", actor="wren")
	tr.add_dependency(store, gated, extra, actor_team="web",
	                  actor="wren")
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.rsrch", phase="research",
	             comment="onward", set_next="lang.bug")
	asked = tr.post_thread(store, thread, author_team="lang",
	                           author="ada", body="push: confirm",
	                           request="push.bug", on=work)["seq"]
	assigned = tr.create_trial(store, work, actor_team="lang",
	                           actor="ada", candidate="c1",
	                           assign=["push.bug"])["assignments"][0]
	return {"work": work, "thread": thread, "single": single,
	        "gated": gated, "extra": extra, "asked": asked,
	        "assigned": assigned}


def _row(store, work_id):
	return store.conn.execute("SELECT * FROM work WHERE id=?",
	                          (work_id,)).fetchone()


# -- the four outcomes share one close ----------------------------------------

@pytest.mark.parametrize("outcome", ["satisfying", "non-satisfying",
                                     "rejected", "cancelled"])
def test_every_outcome_dismantles_the_same_machine(world, outcome):
	store = world
	rig = _rig(store)
	result = tr.close_work(store, rig["work"], actor_team="lang",
	                       actor="ada", rationale="the terminal basis",
	                       outcome=outcome)
	row = _row(store, rig["work"])
	assert row["status"] == "closed" and row["outcome"] == outcome
	assert row["rationale"] == "the terminal basis"
	assert row["current_team"] is None and row["next_team"] is None, \
		"the close did not clear Current and the planned Next"
	for seq in (rig["asked"], rig["assigned"]):
		assert store.conn.execute(
			"SELECT status FROM obligations WHERE seq=?",
			(seq,)).fetchone()["status"] == "withdrawn", \
			f"{outcome} left a pending obligation actionable"
	withdrawals = [event for event in store.events()
	               if event["kind"] == "withdraw"]
	assert len(withdrawals) == 2
	assert pj.detail(store, rig["single"], viewer_team="push",
	                 viewer_member="sl")["ready"] is True, \
		"the last-gate dependent did not unblock"
	gated = pj.detail(store, rig["gated"], viewer_team="web",
	                  viewer_member="wren")
	assert gated["ready"] is False and gated["open_blockers"] == 1, \
		"a dependent with another live gate became ready"
	closing = next(event for event in store.events()
	               if event["seq"] == result["seq"])
	assert closing["actor"] == "lang.ada"
	assert closing["payload"]["outcome"] == outcome
	assert closing["payload"]["rationale"] == "the terminal basis"
	assert closing["payload"]["trial_summary"]["candidate"] == "c1"
	# Immutable: a second close and any later carrying refuse.
	with pytest.raises(bw.WorkError, match="already closed"):
		tr.close_work(store, rig["work"], actor_team="lang", actor="ada",
		              rationale="again", outcome=outcome)
	with pytest.raises(bw.WorkError, match="refuses classification"):
		tr.classify(store, rig["work"], actor_team="lang", actor="ada",
		            classification="limitation")


def test_the_vocabulary_and_rationale_are_hard_gates(world):
	store = world
	work = _create(store)["work_id"]
	before = store.events()
	for outcome in ("satisfying", "cancelled"):
		with pytest.raises(bw.WorkError, match="rationale"):
			tr.close_work(store, work, actor_team="lang", actor="ada",
			              rationale="   ", outcome=outcome)
	for outcome in (None, "done", "duplicate", "Satisfying"):
		with pytest.raises(bw.WorkError, match="exactly one outcome"):
			tr.close_work(store, work, actor_team="lang", actor="ada",
			              rationale="words", outcome=outcome)
	assert store.events() == before, "a refused close changed the trail"
	assert _row(store, work)["status"] == "open"


@pytest.mark.parametrize("terminal_args", [
	("outcome=satisfying"),
	("rationale=complete evidence"),
])
def test_missing_cli_terminal_input_is_a_json_refusal(
		tmp_path, capsys, terminal_args):
	"""The agent surface promises JSON exit-one errors, including omission."""
	config, database = fx.build_instance(str(tmp_path))
	store = bw.Authority(database)
	work = _create(store)["work_id"]
	store.close()
	code = cli.main(["--config", config, "--participant", "lang.ada",
	                 "close", f"work={work}", *terminal_args])
	captured = capsys.readouterr()
	assert code == 1, "missing terminal input escaped through argparse exit 2"
	assert __import__("json").loads(captured.err)["error"], \
		"missing terminal input produced prose instead of the JSON contract"


def test_cancellation_holds_the_same_authority_and_child_rule(world):
	"""Cancellation is ordinary accelerated close: Current-only, no
	cascade, no child bypass."""
	store = world
	work = _create(store)["work_id"]
	for team, member in (("lang", "grace"), ("push", "sl")):
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.close_work(store, work, actor_team=team, actor=member,
			              rationale="not wanted", outcome="cancelled")
	child = tr.create_work(store, team="lang", kind="bug", title="c",
	                       origin="decomposition", classification="suspected-defect", author="ada",
	                       body="child", parent=work)["work_id"]
	with pytest.raises(bw.WorkError, match="open children"):
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="not wanted", outcome="cancelled")
	assert _row(store, child)["status"] == "open", \
		"a cancellation cascaded into a child"
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              rationale="concluded on its own", outcome="satisfying")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="no longer wanted", outcome="cancelled")
	assert _row(store, work)["outcome"] == "cancelled"


# -- the duplicate relation ----------------------------------------------------

def test_duplicate_link_rules_are_exact(world):
	store = world
	canonical = _create(store)["work_id"]
	dupe = _create(store)["work_id"]
	for outcome in ("satisfying", "non-satisfying", "cancelled"):
		with pytest.raises(bw.WorkError, match="duplicate REJECTION"):
			tr.close_work(store, dupe, actor_team="lang", actor="ada",
			              rationale="x", outcome=outcome,
			              duplicate_of=canonical)
	with pytest.raises(bw.WorkError, match="duplicate of itself"):
		tr.close_work(store, dupe, actor_team="lang", actor="ada",
		              rationale="x", outcome="rejected",
		              duplicate_of=dupe)
	with pytest.raises(bw.WorkError, match="no work"):
		tr.close_work(store, dupe, actor_team="lang", actor="ada",
		              rationale="x", outcome="rejected",
		              duplicate_of="ghost-W9")
	tr.classify(store, dupe, actor_team="lang", actor="ada",
	            classification="duplicate")
	with pytest.raises(bw.WorkError, match="free text alone"):
		tr.close_work(store, dupe, actor_team="lang", actor="ada",
		              rationale="same as the other one",
		              outcome="rejected")
	before_edges = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"]
	result = tr.close_work(store, dupe, actor_team="lang", actor="ada",
	                       rationale="folded into the canonical report",
	                       outcome="rejected", duplicate_of=canonical)
	row = _row(store, dupe)
	assert row["duplicate_of"] == canonical
	closing = next(event for event in store.events()
	               if event["seq"] == result["seq"])
	assert closing["payload"]["duplicate_of"] == canonical
	detail = pj.detail(store, dupe, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["duplicate_of"] == canonical
	assert detail["rationale"] == "folded into the canonical report"
	links = pj.links(store, dupe)
	assert links["duplicate_of"]["id"] == canonical
	assert [entry["id"] for entry in
	        pj.links(store, canonical)["duplicates"]] == [dupe], \
		"the survivor does not list what was folded into it"
	# NON-GATING: the canonical work is untouched — no edge, no
	# readiness change, no phase or Current movement.
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == \
		before_edges, "the duplicate link created a dependency edge"
	survivor = _row(store, canonical)
	assert survivor["status"] == "open" and bool(survivor["ready"]) \
		is True and survivor["current_team"] == "lang"


def test_ordinary_rejection_needs_no_link(world):
	store = world
	work = _create(store)["work_id"]
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="not reproducible on any current build",
	              outcome="rejected")
	row = _row(store, work)
	assert row["outcome"] == "rejected" and row["duplicate_of"] is None


def test_duplicate_of_must_name_the_canonical_survivor(world):
	"""A duplicate cannot be the canonical target of another duplicate."""
	store = world
	canonical = _create(store)["work_id"]
	first = _create(store)["work_id"]
	tr.classify(store, first, actor_team="lang", actor="ada",
	            classification="duplicate")
	tr.close_work(store, first, actor_team="lang", actor="ada",
	              rationale="folded once", outcome="rejected",
	              duplicate_of=canonical)
	second = _create(store)["work_id"]
	tr.classify(store, second, actor_team="lang", actor="ada",
	            classification="duplicate")
	before = store.events()
	with pytest.raises(bw.WorkError, match="canonical|surviv"):
		tr.close_work(store, second, actor_team="lang", actor="ada",
		              rationale="must name the root", outcome="rejected",
		              duplicate_of=first)
	assert store.events() == before
	assert _row(store, second)["status"] == "open"


def test_a_mid_flight_duplicate_classification_is_rechecked_in_lock(world):
	store = world
	work = _create(store)["work_id"]
	before = store.events()
	_interleave(store, lambda: tr.classify(
		store, work, actor_team="lang", actor="ada",
		classification="duplicate"))
	with pytest.raises(bw.WorkError, match="free text alone"):
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="rejecting", outcome="rejected")
	assert _row(store, work)["status"] == "open"
	assert [event for event in store.events()
	        if event["kind"] == "close_work"] == \
		[event for event in before if event["kind"] == "close_work"]


# -- races: exactly one compatible terminal history ---------------------------

def test_close_races_serialize_into_one_history(world):
	store = world

	# close vs respond: the answer lands first; the close then withdraws
	# only what is STILL pending.
	rig = _rig(store)
	_interleave(store, lambda: tr.respond_obligation(
		store, rig["asked"], team="push", member="sl", body="confirmed"))
	tr.close_work(store, rig["work"], actor_team="lang", actor="ada",
	              rationale="raced by the answer", outcome="satisfying")
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(rig["asked"],)).fetchone()["status"] == "responded"
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(rig["assigned"],)).fetchone()["status"] == "withdrawn"

	# close vs report: the report lands first and the close's audited
	# round summary counts it truthfully.
	rig = _rig(store)
	_interleave(store, lambda: tr.report(
		store, rig["assigned"], team="push", member="sl",
		observation="passed", evidence="verified"))
	result = tr.close_work(store, rig["work"], actor_team="lang",
	                       actor="ada", rationale="raced by the report",
	                       outcome="satisfying")
	summary = next(event for event in store.events()
	               if event["seq"] == result["seq"])["payload"][
	               "trial_summary"]
	assert summary["progress"] == "1/1"
	assert summary["observations"]["passed"] == 1

	# close vs close: exactly one terminal act.
	rig = _rig(store)
	_interleave(store, lambda: tr.close_work(
		store, rig["work"], actor_team="lang", actor="ada",
		rationale="first", outcome="cancelled"))
	with pytest.raises(bw.WorkError, match="already closed"):
		tr.close_work(store, rig["work"], actor_team="lang", actor="ada",
		              rationale="second", outcome="satisfying")
	assert _row(store, rig["work"])["outcome"] == "cancelled"

	# close vs pass: the pass lands first; the close commits under the
	# COMMITTED current and records it.
	rig = _rig(store)
	_interleave(store, lambda: tr.pass_work(
		store, rig["work"], actor_team="lang", actor="ada",
		to="lang.bug", phase="queued", comment="detour"))
	result = tr.close_work(store, rig["work"], actor_team="lang",
	                       actor="ada", rationale="raced by a pass",
	                       outcome="satisfying")
	closing = next(event for event in store.events()
	               if event["seq"] == result["seq"])
	assert closing["payload"]["was_current_kind"] == "bug", \
		"the close audited a pre-race Current"


# -- crash, restart, retry ------------------------------------------------------

def test_the_full_featured_close_commits_whole_or_not_at_all(world):
	store = world
	canonical = _create(store)["work_id"]
	rig = _rig(store)
	tr.classify(store, rig["work"], actor_team="lang", actor="ada",
	            classification="duplicate")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	baseline = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	baseline_events = store.events()
	statement = {"n": 0, "limit": 0}
	real_conn = store.conn

	class ExplodingConn:
		def execute(self, sql, *args):
			if sql.strip().upper().startswith(
					("UPDATE", "INSERT", "DELETE")):
				statement["n"] += 1
				if statement["n"] > statement["limit"]:
					raise Exception("injected fault")
			return real_conn.execute(sql, *args)

		def __getattr__(self, name):
			return getattr(real_conn, name)

	boundary = 0
	while True:
		boundary += 1
		statement["n"], statement["limit"] = 0, boundary
		store.conn = ExplodingConn()
		try:
			tr.close_work(store, rig["work"], actor_team="lang",
			              actor="ada", rationale="atomic duplicate fold",
			              outcome="rejected", duplicate_of=canonical)
			store.conn = real_conn
			break
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			now = hashlib.sha256(
				open(store.path, "rb").read()).hexdigest()
			assert now == baseline, \
				f"fault at write {boundary} left half a close"
			assert store.events() == baseline_events, \
				"a refused close consumed a sequence"
		assert boundary < 40, "the close never completed"
	assert _row(store, rig["work"])["duplicate_of"] == canonical


def test_restart_reconstructs_the_terminal_record_and_retry_refuses(world):
	store = world
	canonical = _create(store)["work_id"]
	dupe = _create(store)["work_id"]
	tr.close_work(store, dupe, actor_team="lang", actor="ada",
	              rationale="the canonical carries it",
	              outcome="rejected", duplicate_of=canonical)
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	row = fresh.conn.execute("SELECT * FROM work WHERE id=?",
	                         (dupe,)).fetchone()
	assert (row["status"], row["outcome"], row["rationale"],
	        row["duplicate_of"]) == \
		("closed", "rejected", "the canonical carries it", canonical)
	with pytest.raises(bw.WorkError, match="already closed"):
		tr.close_work(fresh, dupe, actor_team="lang", actor="ada",
		              rationale="retry", outcome="rejected",
		              duplicate_of=canonical)
	assert pj.detail(fresh, dupe, viewer_team="lang",
	                 viewer_member="ada")["duplicate_of"] == canonical
	fresh.close()


def test_a_mutual_duplicate_cycle_loses_its_race_in_lock(world):
	"""R74: two works folding into each other would leave no canonical
	survivor — the close that serializes second refuses in-lock."""
	store = world
	first = _create(store)["work_id"]
	second = _create(store)["work_id"]
	before = store.events()
	_interleave(store, lambda: tr.close_work(
		store, second, actor_team="lang", actor="ada",
		rationale="folding the other way", outcome="rejected",
		duplicate_of=first))
	with pytest.raises(bw.WorkError, match="canonical survivor"):
		tr.close_work(store, first, actor_team="lang", actor="ada",
		              rationale="mutual fold", outcome="rejected",
		              duplicate_of=second)
	assert _row(store, first)["status"] == "open"
	assert _row(store, second)["duplicate_of"] == first, \
		"the serialized-first fold did not stand"
	assert len([event for event in store.events()
	            if event["kind"] == "close_work"]) == \
		len([event for event in before
		     if event["kind"] == "close_work"]) + 1


def test_a_closed_canonical_target_stays_valid(world):
	"""R74 preserves the ordinary case: folding into an already CLOSED
	canonical record is legal — only duplicate targets are refused."""
	store = world
	canonical = _create(store)["work_id"]
	tr.close_work(store, canonical, actor_team="lang", actor="ada",
	              rationale="resolved on its own", outcome="satisfying")
	dupe = _create(store)["work_id"]
	tr.close_work(store, dupe, actor_team="lang", actor="ada",
	              rationale="same defect, later report",
	              outcome="rejected", duplicate_of=canonical)
	assert _row(store, dupe)["duplicate_of"] == canonical
