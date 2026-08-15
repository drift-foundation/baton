"""Append-only Work revisions: one promoted message IS the contract.

Only the resolved Current handler of open Work commits a revision; the
promoted message must live in a discussion carrying that open Work's
label; the write is compare-and-swap on the expected prior revision,
rechecked in-lock; history is append-only and immutable; JSON exposes
exactly one effective revision plus the ordered history with complete
self-contained content — no fixed contract fields, no templates.
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
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402

import json as _json


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _create(store, team="lang", member="ada", **kw):
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", author=member,
	                      body="the initial statement", **kw)


def _say(store, discussion, body, team="lang", member="ada"):
	return tr.post_discussion(store, discussion, author_team=team,
	                          author=member, body=body)["seq"]


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate)

	store._write = wrapped


# -- the record and its numbering ---------------------------------------------

def test_a_promotion_records_the_complete_contract(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "the complete revised contract: "
	                "recover the parser without dropping state",
	                member="grace")
	result = tr.revise_work(store, work, actor_team="lang", actor="ada",
	                        message_seq=proposed, expected_revision=0,
	                        rationale="agreed in review")
	assert result["revision"] == 1
	row = store.conn.execute(
		"SELECT * FROM revisions WHERE work=? AND revision=1",
		(work,)).fetchone()
	assert row["prior"] == 0 and row["seq"] == result["seq"]
	assert row["discussion"] == thread
	assert row["message_seq"] == proposed
	assert row["actor"] == "lang.ada"
	assert row["rationale"] == "agreed in review"
	assert row["content"].startswith("the complete revised contract"), \
		"the promoted content is not self-contained in the record"
	event = next(event for event in store.events()
	             if event["seq"] == result["seq"])
	assert event["kind"] == "revise_work"
	assert event["payload"]["authorization"]["handlers"] == ["ada"], \
		"the promotion audited without its Current resolution facts"
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["revision"]["revision"] == 1
	assert detail["revision"]["content"].startswith(
		"the complete revised contract")
	assert [entry["revision"] for entry in detail["revisions"]] == [1]
	# The Work record itself did not move.
	assert detail["status"] == "open" and detail["phase"] == "queued"
	assert detail["current"]["endpoint"] == "lang.bug"


def test_history_is_ordered_append_only_and_effective_is_the_last(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	for number in (1, 2, 3):
		seq = _say(store, thread, f"complete contract, take {number}")
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=seq, expected_revision=number - 1,
		               rationale=f"iteration {number}")
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert [entry["revision"] for entry in detail["revisions"]] == \
		[1, 2, 3]
	assert [entry["prior"] for entry in detail["revisions"]] == [0, 1, 2]
	assert detail["revision"]["revision"] == 3
	assert detail["revision"]["content"] == "complete contract, take 3"
	assert detail["revisions"][0]["content"] == \
		"complete contract, take 1", "an earlier revision was rewritten"


# -- authority: Current only, transferring with the baton ----------------------

def test_only_the_live_current_handler_promotes(world):
	store, config_path = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "proposed replacement contract",
	                team="push", member="sl")
	for team, member in (("push", "sl"), ("lang", "grace")):
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.revise_work(store, work, actor_team=team, actor=member,
			               message_seq=proposed, expected_revision=0,
			               rationale="not mine to commit")
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=proposed, expected_revision=0,
	               rationale="the handler agrees")
	# Reassignment moves the authority with the accepted generation.
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	follow_up = _say(store, thread, "second replacement contract",
	                 member="grace")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=follow_up, expected_revision=1,
		               rationale="former handler")
	tr.revise_work(store, work, actor_team="lang", actor="grace",
	               message_seq=follow_up, expected_revision=1,
	               rationale="the new handler commits")
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="grace")["revision"]["actor"] == \
		"lang.grace"


# -- provenance: the promoted message keeps the work's own discussion ---------

def test_provenance_must_carry_the_open_work_label(world):
	store, _config = world
	born = _create(store)
	work = born["work_id"]
	other = _create(store)
	foreign_message = _say(store, other["discussion"],
	                       "written somewhere else")
	with pytest.raises(bw.WorkError, match="does not carry"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=foreign_message, expected_revision=0,
		               rationale="wrong provenance")
	with pytest.raises(bw.WorkError, match="no discussion message"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=99999, expected_revision=0,
		               rationale="missing message")
	with pytest.raises(bw.WorkError, match="rationale"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=_say(store, born["discussion"], "ok"),
		               expected_revision=0, rationale="   ")
	# Labelling the other discussion makes its messages eligible.
	tr.label_discussion(store, other["discussion"], work,
	                    actor_team="lang", actor="ada")
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=foreign_message, expected_revision=0,
	               rationale="now in the work's own context")


def test_a_mid_flight_unlabel_refuses_the_promotion_in_lock(world):
	store, _config = world
	born = _create(store)
	work = born["work_id"]
	other = _create(store)
	tr.label_discussion(store, other["discussion"], work,
	                    actor_team="lang", actor="ada")
	proposed = _say(store, other["discussion"], "complete contract")
	before = store.events()
	_interleave(store, lambda: tr.unlabel_discussion(
		store, other["discussion"], work, actor_team="lang",
		actor="ada"))
	with pytest.raises(bw.WorkError, match="lost .* provenance|race"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="raced")
	assert [event for event in store.events()
	        if event["kind"] == "revise_work"] == \
		[event for event in before if event["kind"] == "revise_work"]


# -- compare-and-swap ----------------------------------------------------------

def test_cas_refuses_stale_and_wrong_expectations(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	first = _say(store, thread, "contract one")
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=first, expected_revision=0,
	               rationale="one")
	second = _say(store, thread, "contract two")
	for wrong in (0, 2, 7):
		with pytest.raises(bw.WorkError, match="stale|is at revision"):
			tr.revise_work(store, work, actor_team="lang", actor="ada",
			               message_seq=second, expected_revision=wrong,
			               rationale="stale expectation")
	with pytest.raises(bw.WorkError, match="expected prior revision"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=second, expected_revision=None,
		               rationale="unnamed expectation")


def test_a_concurrent_promotion_makes_the_second_writer_stale(world):
	"""Both writers name expected revision 0; exactly one becomes
	revision 1 — the loser refuses in-lock WITHOUT consuming a
	sequence."""
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	mine = _say(store, thread, "my complete contract")
	theirs = _say(store, thread, "their complete contract")
	_interleave(store, lambda: tr.revise_work(
		store, work, actor_team="lang", actor="ada",
		message_seq=theirs, expected_revision=0, rationale="first in"))
	last_before = store.last_seq() + 1  # the interleaved write's seq
	with pytest.raises(bw.WorkError, match="lost a concurrent race"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=mine, expected_revision=0,
		               rationale="second in")
	assert store.last_seq() == last_before, \
		"the stale writer consumed a sequence"
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert [entry["revision"] for entry in detail["revisions"]] == [1]
	assert detail["revision"]["content"] == "their complete contract"
	# Retry against the CURRENT state succeeds.
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=mine, expected_revision=1,
	               rationale="rebased on the winner")
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["revision"]["revision"] == 2


# -- terminal immutability -----------------------------------------------------

def test_terminal_work_refuses_revision_and_history_survives(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "the final contract")
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=proposed, expected_revision=0,
	               rationale="settled")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="delivered", outcome="satisfying")
	late = _say(store, thread, "too late") if False else proposed
	with pytest.raises(bw.WorkError, match="terminal work is immutable"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=late, expected_revision=1,
		               rationale="post-terminal")
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert [entry["revision"] for entry in detail["revisions"]] == [1]
	assert detail["revision"]["content"] == "the final contract", \
		"closing the work disturbed its committed revision history"


def test_a_mid_flight_close_refuses_the_promotion_in_lock(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "complete contract")
	_interleave(store, lambda: tr.close_work(
		store, work, actor_team="lang", actor="ada",
		rationale="closed underneath", outcome="cancelled"))
	with pytest.raises(bw.WorkError, match="terminal work is immutable"):
		tr.revise_work(store, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="raced by the close")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM revisions").fetchone()["n"] == 0


# -- child scope, purity, crash, restart ---------------------------------------

def test_child_work_revises_independently_of_its_parent(world):
	store, _config = world
	parent = _create(store)
	child = tr.create_work(store, team="lang", kind="bug",
	                       title="independent proof",
	                       origin="decomposition", author="ada",
	                       body="child contract", parent=parent["work_id"])
	proposed = _say(store, child["discussion"], "child contract v2")
	tr.revise_work(store, child["work_id"], actor_team="lang",
	               actor="ada", message_seq=proposed,
	               expected_revision=0, rationale="child only")
	assert pj.detail(store, parent["work_id"], viewer_team="lang",
	                 viewer_member="ada")["revision"] is None, \
		"a child revision leaked into the parent's contract"
	assert pj.detail(store, child["work_id"], viewer_team="lang",
	                 viewer_member="ada")["revision"]["revision"] == 1


def test_reads_stay_pure_and_the_promotion_is_whole_or_nothing(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "complete contract")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	pj.detail(store, work, viewer_team="lang", viewer_member="grace")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert hashlib.sha256(
		open(store.path, "rb").read()).hexdigest() == digest, \
		"reading the revision surface wrote a byte"

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
			tr.revise_work(store, work, actor_team="lang", actor="ada",
			               message_seq=proposed, expected_revision=0,
			               rationale="atomic promotion")
			store.conn = real_conn
			break
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			assert hashlib.sha256(
				open(store.path, "rb").read()).hexdigest() == digest, \
				f"fault at write {boundary} left half a revision"
			assert store.events() == baseline_events
		assert boundary < 20, "the promotion never completed"


def test_restart_reconstructs_history_and_retry_refuses(world):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["discussion"]
	proposed = _say(store, thread, "complete contract")
	tr.revise_work(store, work, actor_team="lang", actor="ada",
	               message_seq=proposed, expected_revision=0,
	               rationale="settled")
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	detail = pj.detail(fresh, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["revision"]["revision"] == 1
	assert detail["revision"]["content"] == "complete contract"
	with pytest.raises(bw.WorkError, match="stale|is at revision"):
		tr.revise_work(fresh, work, actor_team="lang", actor="ada",
		               message_seq=proposed, expected_revision=0,
		               rationale="replayed")
	fresh.close()
