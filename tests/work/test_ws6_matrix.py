"""WS-6 Slice A R91: the complete reference/race matrix.

One successful reference-bearing act through EVERY public mutation
family (fresh activation and dossier-capable regen included), asserting
event placement and WS-5 exact-retry replay; whole-or-nothing fault
injection through the compound accept carrying both placements; and the
named both-order races — where both orders legitimately succeed, the
committed revision/order is asserted rather than an invented refusal.
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

PATH = "work/records/2026/08/finding-matrix"
REF = "pushcoin:evidence/note.md"


def _document():
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo", "base": "/srv/checkouts/pushcoin"},
	                     "drift": {"display": "Drift checkout", "base": "/srv/checkouts/drift"}}
	return document


@pytest.fixture
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		_json.dump(_document(), handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
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


def _refs_on(store, seq):
	return [dict(row) for row in store.conn.execute(
		"SELECT kind, root, path FROM act_references WHERE seq=? "
		"ORDER BY ordinal", (seq,))]


# -- every public mutation family carries a reference and retries exactly ------

FAMILIES = [
	"create", "close", "classify", "phase", "block", "revise",
	"discuss", "say", "label", "unlabel", "mark-seen", "respond",
	"dispose", "accept", "try", "report", "assess", "abandon",
	"extend", "bind",
]


@pytest.mark.parametrize("family", FAMILIES)
def test_every_family_carries_ordered_references_and_replays(world, family):
	store, _config = world
	born = _create(store)
	work, thread = born["work_id"], born["thread"]
	kwargs = dict(op_id=f"fam-{family}", refs=[REF])

	if family == "create":
		act = lambda **kw: _create(store, **kw)
	elif family == "close":
		act = lambda **kw: tr.close_work(
			store, work, actor_team="lang", actor="ada",
			rationale="done", outcome="satisfying", **kw)
	elif family == "classify":
		act = lambda **kw: tr.classify(
			store, work, actor_team="lang", actor="ada",
			classification="confirmed-defect", **kw)
	elif family == "phase":
		act = lambda **kw: tr.set_phase(
			store, work, actor_team="lang", actor="ada",
			phase="active", **kw)
	elif family == "block":
		other = _create(store, team="push", member="sl")["work_id"]
		act = lambda **kw: tr.add_dependency(
			store, work, other, actor_team="lang", actor="ada", **kw, rationale="test dependency")
	elif family == "revise":
		# W288: promotion is the claimant's act.
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		proposed = tr.post_thread(
			store, thread, author_team="lang", author="ada",
			body="the contract")["seq"]
		act = lambda **kw: tr.revise_work(
			store, work, actor_team="lang", actor="ada",
			message_seq=proposed, expected_revision=0,
			rationale="promote", **kw)
	elif family == "discuss":
		act = lambda **kw: tr.create_thread(
			store, actor_team="lang", actor="ada", body="ctx",
			labels=[work], subject="trial subject", **kw)
	elif family == "say":
		act = lambda **kw: tr.post_thread(
			store, thread, author_team="lang", author="ada",
			body="spoken", **kw)
	elif family == "label":
		other = _create(store)
		act = lambda **kw: tr.label_thread(
			store, thread, other["work_id"], actor_team="lang",
			actor="ada", **kw)
	elif family == "unlabel":
		other = _create(store)
		tr.label_thread(store, thread, other["work_id"],
		                    actor_team="lang", actor="ada")
		act = lambda **kw: tr.unlabel_thread(
			store, thread, other["work_id"], actor_team="lang",
			actor="ada", **kw)
	elif family == "mark-seen":
		top = store.last_seq()
		act = lambda **kw: tr.seen_thread(
			store, thread, team="lang", member="grace", up_to_seq=top,
			**kw)
	elif family == "respond":
		asked = tr.post_thread(
			store, thread, author_team="lang", author="ada",
			body="push: confirm", request="push.bug", wait=False, on=work)["seq"]
		act = lambda **kw: tr.respond_obligation(
			store, asked, team="push", member="sl", body="confirmed",
			**kw)
	elif family == "dispose":
		asked = tr.post_thread(
			store, thread, author_team="lang", author="ada",
			body="push: confirm", request="push.bug", wait=False, on=work)["seq"]
		act = lambda **kw: tr.dispose_obligation(
			store, asked, team="push", member="sl",
			disposition="no action needed", **kw)
	elif family == "accept":
		consumer = _create(store, team="push", member="sl")
		asked = tr.post_thread(
			store, consumer["thread"], author_team="push",
			author="sl", body="lang: yours?", request="lang.bug", wait=False)["seq"]
		act = lambda **kw: tr.accept_obligation(
			store, asked, actor_team="lang", actor="ada", body="ours",
			into=work, **kw)
	elif family == "try":
		act = lambda **kw: tr.create_trial(
			store, work, actor_team="lang", actor="ada",
			candidate="c1", assign=["push.bug"], **kw)
	elif family == "report":
		assigned = tr.create_trial(
			store, work, actor_team="lang", actor="ada",
			candidate="c1", assign=["push.bug"])["assignments"][0]
		act = lambda **kw: tr.report(
			store, assigned, team="push", member="sl",
			observation="passed", evidence="clean", **kw)
	elif family == "assess":
		assigned = tr.create_trial(
			store, work, actor_team="lang", actor="ada",
			candidate="c1", assign=["push.bug"])["assignments"][0]
		tr.report(store, assigned, team="push", member="sl",
		          observation="passed", evidence="clean")
		act = lambda **kw: tr.assess(
			store, assigned, actor_team="lang", actor="ada",
			assessment="accepted", rationale="verified", **kw)
	elif family == "abandon":
		created = tr.create_trial(
			store, work, actor_team="lang", actor="ada",
			candidate="c1", assign=["push.bug"])
		act = lambda **kw: tr.abandon_trial(
			store, work, created["trial"], actor_team="lang",
			actor="ada", reason="withdrawn", **kw)
	elif family == "extend":
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="c1", assign=["push.bug"],
		                review_at="2027-01-01T00:00:00Z")
		act = lambda **kw: tr.extend_trial(
			store, work, 1, actor_team="lang", actor="ada",
			review_at="2027-06-01T00:00:00Z", **kw)
	elif family == "bind":
		act = lambda **kw: tr.bind_work(
			store, work, actor_team="lang", actor="ada",
			root="pushcoin", path=PATH, expected_revision=0,
			rationale="attach", **kw)

	first = act(**kwargs)
	assert _refs_on(store, first["seq"]) == \
		[{"kind": "independent", "root": "pushcoin",
		  "path": "evidence/note.md"}], \
		f"{family}: the reference did not ride the act's event"
	assert first["operation"] == {"id": f"fam-{family}",
	                              "state": "committed"}
	again = act(**kwargs)
	assert again["operation"]["state"] == "replayed", family
	assert again["seq"] == first["seq"], \
		f"{family}: the protected retry performed a second effect"


def test_fresh_activation_and_dossier_regen_carry_references(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w") as handle:
		_json.dump(_document(), handle, indent=2, sort_keys=True)
	activated = lc.init_from_config(
		config_path, participant="lang.ada", op_id="act-1",
		refs=["pushcoin:docs/charter.md"])
	store = bw.Authority(activated["database"])
	assert _refs_on(store, activated["seq"]) == \
		[{"kind": "independent", "root": "pushcoin",
		  "path": "docs/charter.md"}]
	replay = lc.init_from_config(
		config_path, participant="lang.ada", op_id="act-1",
		refs=["pushcoin:docs/charter.md"])
	assert replay["operation"]["state"] == "replayed"
	# Regen cites an existing bound dossier and retries exactly.
	bound = _create(store, binding=f"drift:{PATH}")
	document = _document()
	document["generation"] = 2
	document["teams"]["push"]["participants"]["wren"] = \
		{"display": "Wren", "roles": ["dev"]}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	accepted = lc.accept_config(
		config_path, actor="lang.ada", op_id="regen-1",
		refs=[f"{bound['work_id']}:proof/change.md"])
	row = store.conn.execute(
		"SELECT kind, work, binding_revision FROM act_references "
		"WHERE seq=?", (accepted["seq"],)).fetchone()
	assert (row["kind"], row["work"], row["binding_revision"]) == \
		("dossier", bound["work_id"], 1)
	again = lc.accept_config(
		config_path, actor="lang.ada", op_id="regen-1",
		refs=[f"{bound['work_id']}:proof/change.md"])
	assert again["operation"]["state"] == "replayed"
	store.close()


# -- fault injection through the compound accept -------------------------------

def test_the_compound_accept_with_both_placements_is_whole_or_nothing(world):
	store, _config = world
	provider_target = _create(store)
	consumer = _create(store, team="push", member="sl",
	                   binding=f"pushcoin:{PATH}")
	asked = tr.post_thread(
		store, consumer["thread"], author_team="push", author="sl",
		body="lang: yours?", request="lang.bug", wait=False)["seq"]
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
			result = tr.accept_obligation(
				store, asked, actor_team="lang", actor="ada",
				body="ours", into=provider_target["work_id"],
				refs=["pushcoin:docs/decision.md"],
				answer_refs=[f"{consumer['work_id']}:report/sum.md"],
				op_id="accept-both")
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
				f"fault at write {boundary} left partial reference rows"
			assert store.events() == baseline_events
		assert boundary < 50, "the accept never completed"
	assert [row["kind"] for row in _refs_on(store, result["seq"])] == \
		["independent"]
	assert [row["kind"] for row in
	        _refs_on(store, result["seq"] + 1)] == ["dossier"], \
		"the completed accept lost one of its placements"


# -- the named both-order races -----------------------------------------------

def _retire_root(config_path, root):
	document = _json.loads(open(config_path).read())
	document["generation"] = document.get("generation", 1) + 1
	del document["roots"][root]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")


def test_binding_races_in_both_orders(world):
	store, config_path = world

	# binding vs binding — sequential order commits [1, 2]; the raced
	# order is the mid-flight regression in test_ws6_bindings.
	work = _create(store)["work_id"]
	tr.bind_work(store, work, actor_team="lang", actor="ada",
	             root="pushcoin", path=PATH, expected_revision=0,
	             rationale="first")
	tr.bind_work(store, work, actor_team="lang", actor="ada",
	             root="drift", path="work/records/2026/08/f2",
	             expected_revision=1, rationale="second")
	assert [entry["revision"] for entry in
	        pj.bindings(store, work)["rows"]] == [1, 2]

	# binding vs transfer — transfer first: the former handler refuses
	# in-lock; bind first then transfer: both stand.
	raced = _create(store)["work_id"]
	_interleave(store, lambda: tr.pass_work(
		store, raced, actor_team="lang", actor="ada",
		to="push.bug", comment="handing over"))
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.bind_work(store, raced, actor_team="lang", actor="ada",
		             root="pushcoin", path=PATH, expected_revision=0,
		             rationale="raced by the transfer")
	ordered = _create(store)["work_id"]
	tr.bind_work(store, ordered, actor_team="lang", actor="ada",
	             root="pushcoin", path=PATH, expected_revision=0,
	             rationale="bound before the transfer")
	fx.post(store, ordered, author_team="lang", author="ada",
	        body="now handing over", pass_to="push.bug")
	assert pj.detail(store, ordered, viewer_team="push",
	                 viewer_member="sl")["binding"]["revision"] == 1

	# binding vs close — bind first then close: history [1] freezes (the
	# close-first order is the mid-flight regression in the focused
	# suite).
	closing = _create(store, binding=f"pushcoin:{PATH}")["work_id"]
	tr.close_work(store, closing, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert pj.detail(store, closing, viewer_team="lang",
	                 viewer_member="ada")["binding"]["revision"] == 1

	# binding vs retirement — bind first then retire: the binding
	# stands; the NEXT revision needs a live root (retire-first is the
	# in-lock liveness path).
	survivor = _create(store, binding=f"drift:{PATH}")["work_id"]
	_retire_root(config_path, "drift")
	assert pj.detail(store, survivor, viewer_team="lang",
	                 viewer_member="ada")["binding"]["root"] == "drift"
	with pytest.raises(bw.WorkError, match="not a live configured root"):
		tr.bind_work(store, survivor, actor_team="lang", actor="ada",
		             root="drift", path="work/records/2026/08/f3",
		             expected_revision=1, rationale="retired root")


def test_reference_races_in_both_orders(world):
	store, config_path = world

	# reference vs binding correction — cite FIRST, correct after: the
	# committed citation stays pinned to revision 1 (correction-first is
	# the pin-under-commit regression in the focused suite).
	bound = _create(store, binding=f"pushcoin:{PATH}")
	reader = _create(store, team="push", member="sl")
	cited = tr.post_thread(
		store, reader["thread"], author_team="push", author="sl",
		body="anchored", refs=[f"{bound['work_id']}:repro/r.sh"])
	tr.bind_work(store, bound["work_id"], actor_team="lang",
	             actor="ada", root="drift",
	             path="work/records/2026/08/f2", expected_revision=1,
	             rationale="corrected after the citation")
	row = store.conn.execute(
		"SELECT binding_revision, root FROM act_references WHERE seq=?",
		(cited["seq"],)).fetchone()
	assert (row["binding_revision"], row["root"]) == (1, "pushcoin"), \
		"the correction reinterpreted the committed citation"

	# reference vs work close — BOTH orders succeed: a bound Work stays
	# citable after (and even while) closing; the citation pins the
	# frozen revision.
	closing = _create(store, binding=f"pushcoin:{PATH}")
	_interleave(store, lambda: tr.close_work(
		store, closing["work_id"], actor_team="lang", actor="ada",
		rationale="closing mid-citation", outcome="satisfying"))
	mid = tr.post_thread(
		store, reader["thread"], author_team="push", author="sl",
		body="cites the closing work",
		refs=[f"{closing['work_id']}:notes.md"])
	assert store.conn.execute(
		"SELECT binding_revision FROM act_references WHERE seq=?",
		(mid["seq"],)).fetchone()["binding_revision"] == 1
	after = tr.post_thread(
		store, reader["thread"], author_team="push", author="sl",
		body="cites the closed work",
		refs=[f"{closing['work_id']}:more.md"])
	assert store.conn.execute(
		"SELECT binding_revision FROM act_references WHERE seq=?",
		(after["seq"],)).fetchone()["binding_revision"] == 1

	# reference vs root retirement — cite first, retire after: the
	# committed independent row stands (retire-first is the in-lock
	# refusal regression in the focused suite).
	early = tr.post_thread(
		store, reader["thread"], author_team="push", author="sl",
		body="early evidence", refs=["drift:docs/early.md"])
	_retire_root(config_path, "drift")
	assert store.conn.execute(
		"SELECT root FROM act_references WHERE seq=?",
		(early["seq"],)).fetchone()["root"] == "drift"
