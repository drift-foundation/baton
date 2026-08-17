"""WS-5: effectively-once mutation retry by client operation identity.

An optional per-participant opaque id makes a mutation effectively-once:
the operation record, effect, event (when any), and complete replayable
result commit atomically; exact retry is a pure replay; conflicting
reuse refuses; refusals never consume the identity; successful no-ops
consume it without inventing a domain event; every result carries
exactly one `operation` shape (null / committed / replayed).
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
	                      origin="external-report", classification="suspected-defect", author=member,
	                      body="born speaking", **kw)


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


# -- identity grammar and scope ------------------------------------------------

def test_the_id_grammar_refuses_junk_before_anything_else(world):
	store, _config = world
	born = _create(store)
	for bad in ("", " ", "a b", "x\ty", "c\x01d", "z" * 129):
		with pytest.raises(bw.WorkError, match="1-128 bytes"):
			tr.post_thread(store, born["thread"],
			                   author_team="lang", author="ada",
			                   body="x", op_id=bad)
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM operations").fetchone()["n"] == 0


def test_scope_is_per_participant_never_global(world):
	"""The same id VALUE under two participants is two independent
	protected operations."""
	store, _config = world
	born = _create(store)
	mine = tr.post_thread(store, born["thread"],
	                          author_team="lang", author="ada",
	                          body="ada speaks", op_id="shared-uuid")
	theirs = tr.post_thread(store, born["thread"],
	                            author_team="push", author="sl",
	                            body="sl speaks", op_id="shared-uuid")
	assert mine["operation"] == {"id": "shared-uuid",
	                             "state": "committed"}
	assert theirs["operation"] == {"id": "shared-uuid",
	                               "state": "committed"}
	assert mine["seq"] != theirs["seq"], \
		"one participant's id blocked another's honest commit"


# -- the three envelope shapes -------------------------------------------------

def test_every_result_carries_exactly_one_operation_shape(world):
	store, _config = world
	born = _create(store)
	bare = tr.post_thread(store, born["thread"],
	                          author_team="lang", author="ada", body="x")
	assert bare["operation"] is None, \
		"an unprotected call did not say so"
	fresh = tr.post_thread(store, born["thread"],
	                           author_team="lang", author="ada",
	                           body="y", op_id="op-1")
	assert fresh["operation"] == {"id": "op-1", "state": "committed"}
	replay = tr.post_thread(store, born["thread"],
	                            author_team="lang", author="ada",
	                            body="y", op_id="op-1")
	assert replay["operation"] == {"id": "op-1", "state": "replayed"}
	assert replay["seq"] == fresh["seq"], \
		"the replay did not return the original committed sequence"


# -- exact retry, conflicting reuse, refusal non-poisoning ---------------------

def test_exact_retry_replays_without_a_second_effect(world):
	store, _config = world
	born = _create(store)
	first = tr.post_thread(store, born["thread"],
	                           author_team="lang", author="ada",
	                           body="push: confirm", request="push.bug",
	                           op_id="ask-1")
	events_after = store.events()
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	retry = tr.post_thread(store, born["thread"],
	                           author_team="lang", author="ada",
	                           body="push: confirm", request="push.bug",
	                           op_id="ask-1")
	assert retry["seq"] == first["seq"]
	assert retry["operation"]["state"] == "replayed"
	assert {key: value for key, value in retry.items()
	        if key != "operation"} == \
		{key: value for key, value in first.items()
		 if key != "operation"}, \
		"the replayed domain payload differs from the committed one"
	assert store.events() == events_after, "a replay consumed a sequence"
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert hashlib.sha256(
		open(store.path, "rb").read()).hexdigest() == digest, \
		"a replay wrote a byte"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == 1, \
		"the retry performed a second effect"


def test_conflicting_reuse_refuses_closed(world):
	store, _config = world
	born = _create(store)
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="ada", body="first meaning", op_id="op-x")
	before = store.events()
	with pytest.raises(bw.WorkError, match="different request"):
		tr.post_thread(store, born["thread"],
		                   author_team="lang", author="ada",
		                   body="second meaning", op_id="op-x")
	assert store.events() == before


def test_a_refusal_leaves_the_id_unconsumed_for_the_correction(world):
	store, _config = world
	work = _create(store)["work_id"]
	with pytest.raises(bw.WorkError, match="exactly one outcome"):
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="words", outcome="done", op_id="close-1")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM operations").fetchone()["n"] == 0, \
		"a refusal consumed the operation identity"
	corrected = tr.close_work(store, work, actor_team="lang",
	                          actor="ada", rationale="words",
	                          outcome="satisfying", op_id="close-1")
	assert corrected["operation"]["state"] == "committed"


# -- the fingerprint excludes dynamic resolution -------------------------------

def test_later_state_replay_returns_the_original_resolution(world):
	"""A committed protected carrying operation replays after the Work
	closed — the fingerprint names the TYPED request, and the replay is
	a read of the committed fact, not a new act."""
	store, _config = world
	born = _create(store)
	passed = tr.pass_work(store, born["work_id"],
	                      actor_team="lang", actor="ada",
	                      to="lang.rsrch", comment="onward", op_id="pass-1")
	tr.close_work(store, born["work_id"], actor_team="lang",
	              actor="ada", rationale="done", outcome="satisfying")
	replay = tr.pass_work(store, born["work_id"],
	                      actor_team="lang", actor="ada",
	                      to="lang.rsrch", comment="onward", op_id="pass-1")
	assert replay["seq"] == passed["seq"]
	assert replay["operation"]["state"] == "replayed"
	assert replay["work"] == born["work_id"]
	with pytest.raises(bw.WorkError, match="terminal work never moves"):
		tr.pass_work(store, born["work_id"],
		             actor_team="lang", actor="ada",
		             to="lang.rsrch", comment="onward again", op_id="pass-2")


def test_a_removed_identity_gets_no_replay_carve_out(world):
	store, config_path = world
	born = _create(store)
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="grace", body="before removal",
	                   op_id="grace-1")
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	with pytest.raises(bw.WorkError, match="not a registered member"):
		tr.post_thread(store, born["thread"],
		                   author_team="lang", author="grace",
		                   body="before removal", op_id="grace-1")


# -- the in-lock race algorithm ------------------------------------------------

def test_a_concurrent_identical_attempt_replays_in_lock(world):
	store, _config = world
	born = _create(store)
	other = bw.Authority(store.path)
	other.clock = store.clock
	_interleave(store, lambda: tr.post_thread(
		other, born["thread"], author_team="lang", author="ada",
		body="the one message", op_id="race-1"))
	result = tr.post_thread(store, born["thread"],
	                            author_team="lang", author="ada",
	                            body="the one message", op_id="race-1")
	assert result["operation"]["state"] == "replayed", \
		"the racing loser committed a second effect"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages WHERE body=?",
		("the one message",)).fetchone()["n"] == 1
	other.close()


def test_a_concurrent_conflicting_attempt_refuses_in_lock(world):
	store, _config = world
	born = _create(store)
	other = bw.Authority(store.path)
	other.clock = store.clock
	_interleave(store, lambda: tr.post_thread(
		other, born["thread"], author_team="lang", author="ada",
		body="their meaning", op_id="race-2"))
	with pytest.raises(bw.WorkError, match="different request"):
		tr.post_thread(store, born["thread"],
		                   author_team="lang", author="ada",
		                   body="my meaning", op_id="race-2")
	other.close()


# -- protected successful no-ops (R76) -----------------------------------------

def test_a_protected_no_op_consumes_the_id_without_an_event(world):
	store, _config = world
	born = _create(store)
	top = store.last_seq()
	tr.seen_thread(store, born["thread"], team="lang",
	                   member="grace", up_to_seq=top)
	events_before = store.events()
	losing = tr.seen_thread(store, born["thread"], team="lang",
	                            member="grace", up_to_seq=top,
	                            op_id="mark-1")
	assert losing["advanced"] is False and losing["cursor"] == top
	assert losing["operation"] == {"id": "mark-1", "state": "committed"}
	assert store.events() == events_before, \
		"a successful no-op invented a domain event"
	row = store.conn.execute(
		"SELECT seq FROM operations WHERE participant='lang.grace' AND "
		"op_id='mark-1'").fetchone()
	assert row is not None and row["seq"] is None, \
		"the no-op did not consume its identity (R76)"
	# The cursor then advances; the exact retry STILL replays the stored
	# no-op result verbatim — it names what THAT invocation did.
	tr.post_thread(store, born["thread"], author_team="lang",
	                   author="ada", body="later")
	tr.seen_thread(store, born["thread"], team="lang",
	                   member="grace", up_to_seq=store.last_seq())
	retry = tr.seen_thread(store, born["thread"], team="lang",
	                           member="grace", up_to_seq=top,
	                           op_id="mark-1")
	assert retry["advanced"] is False and retry["cursor"] == top
	assert retry["operation"]["state"] == "replayed"
	with pytest.raises(bw.WorkError, match="different request"):
		tr.seen_thread(store, born["thread"], team="lang",
		                   member="grace", up_to_seq=top - 1,
		                   op_id="mark-1")


# -- operation-log: paged, own-only, pure --------------------------------------

def test_the_operation_log_pages_on_its_own_recorded_cursor(world):
	store, _config = world
	born = _create(store)
	for index in range(5):
		tr.post_thread(store, born["thread"],
		                   author_team="lang", author="ada",
		                   body=f"m{index}", op_id=f"op-{index}")
	tr.post_thread(store, born["thread"], author_team="push",
	                   author="sl", body="other actor", op_id="op-0")
	walked, after, pages = [], 0, 0
	while True:
		page = pj.operation_log(store, "lang.ada", after=after, limit=2)
		walked += [row["op_id"] for row in page["rows"]]
		pages += 1
		if page["next_after"] is None:
			break
		after = page["next_after"]
	assert walked == [f"op-{index}" for index in range(5)], \
		"the operation log skipped, repeated, or leaked another actor"
	assert pages == 3
	for kwargs in ({"after": -1}, {"limit": 0}, {"limit": 501}):
		with pytest.raises(bw.WorkError,
		                   match="pagination cursor|page limit"):
			pj.operation_log(store, "lang.ada", **kwargs)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	pj.operation_log(store, "lang.ada")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert hashlib.sha256(
		open(store.path, "rb").read()).hexdigest() == digest


# -- crash, restart ------------------------------------------------------------

def test_the_protected_commit_is_whole_or_nothing(world):
	store, _config = world
	consumer = _create(store, team="push", member="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug")["seq"]
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
			tr.accept_obligation(store, asked, actor_team="lang",
			                     actor="ada", body="ours",
			                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"},
			                     op_id="accept-1")
			store.conn = real_conn
			break
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			assert hashlib.sha256(
				open(store.path, "rb").read()).hexdigest() == baseline, \
				f"fault at write {boundary} left a partial operation"
			assert store.events() == baseline_events
			assert store.conn.execute(
				"SELECT COUNT(*) AS n FROM operations").fetchone()[
				"n"] == 0, "a crashed attempt recorded a false success"
		assert boundary < 40, "the accept never completed"
	# The record now replays across restart.
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	replay = tr.accept_obligation(fresh, asked, actor_team="lang",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"},
	                              op_id="accept-1")
	assert replay["operation"]["state"] == "replayed"
	assert replay["provider"], "the replayed result lost its decorations"
	fresh.close()


# -- init and regen (P9a) ------------------------------------------------------

def test_protected_init_replays_and_conflicts_on_an_existing_authority(
		tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		_json.dump(fx.config_document(), handle, indent=2, sort_keys=True)
	first = lc.init_from_config(config_path, participant="lang.ada",
	                            op_id="init-1")
	assert first["operation"] == {"id": "init-1", "state": "committed"}
	assert first["generation"] == 1
	# Exact protected re-init replays the committed result.
	again = lc.init_from_config(config_path, participant="lang.ada",
	                            op_id="init-1")
	assert again["operation"]["state"] == "replayed"
	assert again["database"] == first["database"]
	# The identity gate refuses an unknown identity, learning nothing.
	with pytest.raises(bw.WorkError, match="not a registered member"):
		lc.init_from_config(config_path, participant="ghost.gone",
		                    op_id="init-1")
	# A DIFFERENT document under the same id is a conflict.
	document = fx.config_document()
	document["instance"]["name"] = "edited"
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="different request"):
		lc.init_from_config(config_path, participant="lang.ada",
		                    op_id="init-1")
	# Id-less re-init keeps today's honest refusal.
	with pytest.raises(bw.WorkError, match="already exists"):
		lc.init_from_config(config_path, participant="lang.ada")


def test_fresh_init_validates_the_proposed_participant(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		_json.dump(fx.config_document(), handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="proposed generation-1"):
		lc.init_from_config(config_path, participant="ghost.gone")


def test_protected_regen_replays_the_acceptance(world):
	store, config_path = world
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	first = lc.accept_config(config_path, actor="lang.ada",
	                         op_id="regen-1")
	assert first["operation"]["state"] == "committed"
	assert first["generation"] == 2
	again = lc.accept_config(config_path, actor="lang.ada",
	                         op_id="regen-1")
	assert again["operation"]["state"] == "replayed"
	assert again["generation"] == 2, \
		"the replayed acceptance lost its decorations"


# -- R84 both-order races on the in-lock and no-op paths ----------------------

def test_an_in_lock_removal_race_refuses_the_protected_commit(world):
	store, config_path = world
	born = _create(store)
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	_interleave(store, lambda: lc.accept_config(config_path,
	                                            actor="lang.ada"))
	with pytest.raises(bw.WorkError,
	                   match="not a registered member|currently accepted"):
		tr.post_thread(store, born["thread"], author_team="lang",
		                   author="grace", body="mid-flight",
		                   op_id="grace-inlock")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM operations WHERE "
		"participant='lang.grace'").fetchone()["n"] == 0, \
		"a removed identity still consumed an operation record"


def test_a_no_op_removal_race_refuses_in_its_own_observation(
		world, monkeypatch):
	"""The record-only no-op transaction shares the same coherent
	gate+lookup observation: a removal committing before its lookup
	refuses; the reverse order leaves the committed record intact."""
	store, config_path = world
	born = _create(store)
	top = store.last_seq()
	tr.seen_thread(store, born["thread"], team="lang",
	                   member="grace", up_to_seq=top)
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["participants"]["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	original = store._op_replay
	fired = {"done": False}

	def remove_then_lookup(conn, participant, op_id, fingerprint):
		if not fired["done"]:
			fired["done"] = True
			lc.accept_config(config_path, actor="lang.ada")
		return original(conn, participant, op_id, fingerprint)

	monkeypatch.setattr(store, "_op_replay", remove_then_lookup)
	with pytest.raises(bw.WorkError, match="not a registered member"):
		tr.seen_thread(store, born["thread"], team="lang",
		                   member="grace", up_to_seq=top,
		                   op_id="grace-noop")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM operations WHERE "
		"participant='lang.grace'").fetchone()["n"] == 0
