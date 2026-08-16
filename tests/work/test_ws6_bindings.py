"""WS-6 Slice A: configured roots, permanent dossier bindings, and
ordered typed asset references.

Roots keep the v10 grammar and never-reuse discipline; a binding is the
exact canonical `work/records/YYYY/MM/<stable-record>` locator with
Current-only CAS revision authority that freezes at terminal close;
references ride every mutation's act — independent (live root) or
dossier-relative (bound Work, effective revision pinned, no label gate,
valid after root retirement) — validating protocol facts only, never
the filesystem.
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


def _spec():
	return {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}


def _with_roots(config_path):
	document = _json.loads(open(config_path).read())
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo"},
	                     "drift": {"display": "Drift checkout"}}
	document["generation"] = document.get("generation", 1)
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	return document


@pytest.fixture
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	document = fx.config_document(_spec())
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo"},
	                     "drift": {"display": "Drift checkout"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	yield store, config_path
	store.close()


PATH = "work/records/2026/08/finding-portable"


def _create(store, team="lang", member="ada", **kw):
	return tr.create_work(store, team=team, kind="bug", title="w",
	                      origin="external-report", author=member,
	                      body="born speaking", **kw)


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


def _retire_root(config_path, root):
	document = _json.loads(open(config_path).read())
	document["generation"] += 1
	del document["roots"][root]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")


# -- the catalog ---------------------------------------------------------------

def test_the_catalog_uses_the_v10_grammar_and_never_reuses(world, tmp_path):
	store, config_path = world
	rows = {row["root"]: row["removed"] for row in store.conn.execute(
		"SELECT root, removed FROM roots")}
	assert rows == {"pushcoin": 0, "drift": 0}
	# v10 grammar refusals at validation time.
	for bad in ("Push", "push-coin", "a" * 65, "push..coin", ".push", ""):
		document = _json.loads(open(config_path).read())
		document["generation"] += 1
		document["roots"][bad] = {"display": "X"}
		with open(config_path, "w") as handle:
			_json.dump(document, handle, indent=2, sort_keys=True)
		with pytest.raises(bw.WorkError, match="root ident|unknown"):
			lc.accept_config(config_path, actor="lang.ada")
	# Retirement projects removed=1; reintroduction refuses.
	document = fx.config_document(_spec())
	document["roots"] = {"pushcoin": {"display": "PushCoin monorepo"}}
	document["generation"] = 2
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")
	assert store.conn.execute(
		"SELECT removed FROM roots WHERE root='drift'").fetchone()[
		"removed"] == 1
	document["generation"] = 3
	document["roots"]["drift"] = {"display": "Back again"}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="never silently reused"):
		lc.accept_config(config_path, actor="lang.ada")


# -- bindings: shape, atomic creation, authority, CAS -------------------------

def test_the_binding_locator_shape_is_exact(world):
	store, _config = world
	work = _create(store)["work_id"]
	for bad in ("work/records/2026/13/x", "work/records/26/08/x",
	            "work/open/2026/08/x", "work/records/2026/08/a/b",
	            "work/records/2026/08/", "records/2026/08/x",
	            "work/records/2026/08/..", "/work/records/2026/08/x"):
		with pytest.raises(bw.WorkError,
		                   match="canonical permanent record|contained|"
		                         "component"):
			tr.bind_work(store, work, actor_team="lang", actor="ada",
			             root="pushcoin", path=bad, expected_revision=0,
			             rationale="bad shape")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM bindings").fetchone()["n"] == 0


def test_creation_binds_atomically_and_needs_a_live_root(world):
	store, _config = world
	born = _create(store, binding=f"pushcoin:{PATH}")
	row = store.conn.execute(
		"SELECT * FROM bindings WHERE work=?",
		(born["work_id"],)).fetchone()
	assert (row["revision"], row["prior"], row["root"], row["path"]) == \
		(1, 0, "pushcoin", PATH)
	assert row["seq"] == born["seq"] and row["rationale"] is None
	with pytest.raises(bw.WorkError, match="not a live configured root"):
		_create(store, binding=f"ghost:{PATH}")
	detail = pj.detail(store, born["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	assert detail["binding"]["root"] == "pushcoin"
	assert detail["binding_count"] == 1
	assert detail["bindings_truncated"] is False


def test_binding_authority_is_current_only_with_cas(world):
	store, config_path = world
	work = _create(store)["work_id"]
	for team, member in (("lang", "grace"), ("push", "sl")):
		with pytest.raises(bw.WorkError, match="never grant"):
			tr.bind_work(store, work, actor_team=team, actor=member,
			             root="pushcoin", path=PATH,
			             expected_revision=0, rationale="not mine")
	tr.bind_work(store, work, actor_team="lang", actor="ada",
	             root="pushcoin", path=PATH, expected_revision=0,
	             rationale="attaching the record")
	for wrong in (0, 2):
		with pytest.raises(bw.WorkError, match="is at revision"):
			tr.bind_work(store, work, actor_team="lang", actor="ada",
			             root="drift",
			             path="work/records/2026/08/f2",
			             expected_revision=wrong, rationale="stale")
	with pytest.raises(bw.WorkError, match="rationale"):
		tr.bind_work(store, work, actor_team="lang", actor="ada",
		             root="drift", path="work/records/2026/08/f2",
		             expected_revision=1, rationale="  ")
	# Transfer moves the authority; the new handler corrects under CAS.
	fx.post(store, work, author_team="lang", author="ada",
	        body="over to push", pass_to="push.bug")
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.bind_work(store, work, actor_team="lang", actor="ada",
		             root="drift", path="work/records/2026/08/f2",
		             expected_revision=1, rationale="former handler")
	corrected = tr.bind_work(store, work, actor_team="push", actor="sl",
	                         root="drift",
	                         path="work/records/2026/08/f2",
	                         expected_revision=1,
	                         rationale="corrected locator")
	assert corrected["revision"] == 2
	history = pj.bindings(store, work)
	assert [entry["revision"] for entry in history["rows"]] == [1, 2]


def test_terminal_close_freezes_binding_history(world):
	store, _config = world
	work = _create(store, binding=f"pushcoin:{PATH}")["work_id"]
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="delivered", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="freezes its binding"):
		tr.bind_work(store, work, actor_team="lang", actor="ada",
		             root="drift", path="work/records/2026/08/f2",
		             expected_revision=1, rationale="post-terminal")
	assert pj.detail(store, work, viewer_team="lang",
	                 viewer_member="ada")["binding"]["revision"] == 1


def test_a_mid_flight_close_or_second_binding_refuses_in_lock(world):
	store, _config = world
	work = _create(store)["work_id"]
	other = bw.Authority(store.path)
	other.clock = store.clock
	_interleave(store, lambda: tr.bind_work(
		other, work, actor_team="lang", actor="ada", root="pushcoin",
		path=PATH, expected_revision=0, rationale="first in"))
	with pytest.raises(bw.WorkError, match="lost a concurrent race"):
		tr.bind_work(store, work, actor_team="lang", actor="ada",
		             root="drift", path="work/records/2026/08/f2",
		             expected_revision=0, rationale="second in")
	second = _create(store)["work_id"]
	_interleave(store, lambda: tr.close_work(
		store, second, actor_team="lang", actor="ada",
		rationale="closed under it", outcome="cancelled"))
	with pytest.raises(bw.WorkError, match="freezes its binding"):
		tr.bind_work(store, second, actor_team="lang", actor="ada",
		             root="pushcoin", path=PATH, expected_revision=0,
		             rationale="raced by the close")
	other.close()


# -- references: forms, anchoring, retirement, ordering, placement ------------

def test_references_ride_the_act_in_order(world):
	store, _config = world
	bound = _create(store, binding=f"pushcoin:{PATH}")
	target = _create(store, team="push", member="sl")
	result = tr.post_thread(
		store, target["thread"], author_team="push", author="sl",
		body="evidence attached",
		refs=[f"drift:docs/notes.md", f"{bound['work_id']}:repro/run.sh"])
	rows = store.conn.execute(
		"SELECT * FROM act_references WHERE seq=? ORDER BY ordinal",
		(result["seq"],)).fetchall()
	assert [(row["ordinal"], row["kind"]) for row in rows] == \
		[(1, "independent"), (2, "dossier")]
	assert rows[0]["root"] == "drift" and rows[0]["work"] is None
	assert (rows[1]["work"], rows[1]["binding_revision"],
	        rows[1]["root"]) == (bound["work_id"], 1, "pushcoin")
	# No label gate (M2): bound work is NOT labelled on the thread,
	# and the citation added no label, edge, or participation for lang.
	labels = pj.thread(store, target["thread"], viewer_team="push",
	                   viewer_member="sl")["labels"]
	assert [entry["work"] for entry in labels] == [target["work_id"]]
	message = pj.thread(store, target["thread"], viewer_team="push",
	                    viewer_member="sl")["messages"][-1]
	assert [ref["kind"] for ref in message["references"]] == \
		["independent", "dossier"]
	event = next(entry for entry in store.events()
	             if entry["seq"] == result["seq"])
	assert [ref["ordinal"] for ref in event["references"]] == [1, 2]


def test_reference_refusals_are_exact(world):
	store, _config = world
	born = _create(store)
	unbound = _create(store)["work_id"]
	for token, needle in (
			("ghost:docs/x", "not a live configured root"),
			(f"{unbound}:repro/x", "no dossier binding to anchor"),
			("drift:/abs/path", "contained relative"),
			("drift:a/../b", "component"),
			("drift:", "non-empty relative"),
			("noseparator", "not LEFT:relative/path")):
		with pytest.raises(bw.WorkError):
			tr.post_thread(store, born["thread"],
			                   author_team="lang", author="ada",
			                   body="x", refs=[token])
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM act_references").fetchone()["n"] == 0


def test_dossier_citations_survive_root_retirement(world):
	"""M5: new bindings and independent refs need a LIVE root; a dossier
	citation pins an existing immutable revision and stays valid."""
	store, config_path = world
	bound = _create(store, binding=f"drift:{PATH}")
	reader = _create(store, team="push", member="sl")
	_retire_root(config_path, "drift")
	# Independent reference to the retired root refuses.
	with pytest.raises(bw.WorkError, match="not a live configured root"):
		tr.post_thread(store, reader["thread"],
		                   author_team="push", author="sl", body="x",
		                   refs=["drift:docs/x.md"])
	# The dossier citation of the committed revision still publishes.
	cited = tr.post_thread(store, reader["thread"],
	                           author_team="push", author="sl",
	                           body="still anchored",
	                           refs=[f"{bound['work_id']}:proof/p.txt"])
	row = store.conn.execute(
		"SELECT root, binding_revision FROM act_references WHERE seq=?",
		(cited["seq"],)).fetchone()
	assert (row["root"], row["binding_revision"]) == ("drift", 1)
	# A NEW binding revision cannot name the retired root; correcting to
	# a live root works.
	with pytest.raises(bw.WorkError, match="not a live configured root"):
		tr.bind_work(store, bound["work_id"], actor_team="lang",
		             actor="ada", root="drift",
		             path="work/records/2026/08/f2",
		             expected_revision=1, rationale="still drift")
	tr.bind_work(store, bound["work_id"], actor_team="lang", actor="ada",
	             root="pushcoin", path="work/records/2026/08/f2",
	             expected_revision=1, rationale="moved to a live root")


def test_a_reference_pins_the_effective_revision_under_the_commit(world):
	"""A binding correction racing the publication: the reference pins
	the revision that was effective when the message COMMITTED."""
	store, _config = world
	bound = _create(store, binding=f"pushcoin:{PATH}")
	reader = _create(store, team="push", member="sl")
	_interleave(store, lambda: tr.bind_work(
		store, bound["work_id"], actor_team="lang", actor="ada",
		root="drift", path="work/records/2026/08/f2",
		expected_revision=1, rationale="corrected mid-flight"))
	result = tr.post_thread(store, reader["thread"],
	                            author_team="push", author="sl",
	                            body="anchored to what committed",
	                            refs=[f"{bound['work_id']}:repro/r.sh"])
	row = store.conn.execute(
		"SELECT binding_revision, root FROM act_references WHERE seq=?",
		(result["seq"],)).fetchone()
	assert (row["binding_revision"], row["root"]) == (2, "drift"), \
		"the reference pinned a stale revision instead of the committed one"


def test_compound_placement_is_explicit(world):
	store, _config = world
	consumer = _create(store, team="push", member="sl",
	                   binding=f"pushcoin:{PATH}")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug")["seq"]
	result = tr.accept_obligation(
		store, asked, actor_team="lang", actor="ada", body="ours",
		create={"kind": "rsrch", "title": "t"},
		refs=["pushcoin:docs/decision.md"],
		answer_refs=[f"{consumer['work_id']}:report/summary.md"])
	on_accept = store.conn.execute(
		"SELECT kind FROM act_references WHERE seq=? ORDER BY ordinal",
		(result["seq"],)).fetchall()
	assert [row["kind"] for row in on_accept] == ["independent"]
	answer_seq = result["seq"] + 1
	on_answer = store.conn.execute(
		"SELECT kind, work FROM act_references WHERE seq=?",
		(answer_seq,)).fetchall()
	assert [(row["kind"], row["work"]) for row in on_answer] == \
		[("dossier", consumer["work_id"])], \
		"the answer placement was guessed or dropped"


def test_a_reference_bearing_no_op_refuses_whole(world):
	store, _config = world
	born = _create(store, binding=f"pushcoin:{PATH}")
	top = store.last_seq()
	tr.seen_thread(store, born["thread"], team="lang",
	                   member="grace", up_to_seq=top)
	before = store.events()
	with pytest.raises(bw.WorkError, match="commits no act"):
		tr.seen_thread(store, born["thread"], team="lang",
		                   member="grace", up_to_seq=top,
		                   refs=["pushcoin:notes.md"])
	assert store.events() == before
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM act_references").fetchone()["n"] == 0


def test_config_family_references_are_independent_only(world, tmp_path):
	store, config_path = world
	document = _json.loads(open(config_path).read())
	document["generation"] += 1
	document["teams"]["push"]["participants"]["wren"] = \
		{"display": "Wren", "roles": ["dev"]}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.accept_config(config_path, actor="lang.ada",
	                          refs=["pushcoin:docs/generation-note.md"])
	rows = store.conn.execute(
		"SELECT kind, root FROM act_references WHERE seq=?",
		(result["seq"],)).fetchall()
	assert [(row["kind"], row["root"]) for row in rows] == \
		[("independent", "pushcoin")]
	with pytest.raises(bw.WorkError, match="not in the root catalog"):
		lc.accept_config(config_path, actor="lang.ada",
		                 refs=["ghost:docs/x.md"])


def test_regen_may_cite_an_existing_bound_dossier(world):
	"""The every-mutation ruling does not make regen an independent-only
	island. Fresh activation has no Work yet, but regen runs against an
	existing authority and may cite an immutable binding revision."""
	store, config_path = world
	bound = _create(store, binding=f"drift:{PATH}")
	document = _json.loads(open(config_path).read())
	document["generation"] += 1
	document["teams"]["push"]["participants"]["wren"] = \
		{"display": "Wren", "roles": ["dev"]}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.accept_config(
		config_path, actor="lang.ada",
		refs=[f"{bound['work_id']}:proof/config-change.md"])
	row = store.conn.execute(
		"SELECT kind, work, binding_revision, root, path "
		"FROM act_references WHERE seq=?", (result["seq"],)).fetchone()
	assert dict(row) == {
		"kind": "dossier", "work": bound["work_id"],
		"binding_revision": 1, "root": "drift",
		"path": "proof/config-change.md"}


def test_config_references_share_the_normalized_posix_path_grammar(world):
	"""Configuration acts use the same reference type, not a weaker parser
	that accepts a Windows separator ordinary mutations refuse."""
	_store, config_path = world
	document = _json.loads(open(config_path).read())
	document["generation"] += 1
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	with pytest.raises(bw.WorkError, match="contained relative POSIX path"):
		lc.accept_config(config_path, actor="lang.ada",
		                 refs=[r"drift:proof\config-change.md"])


# -- WS-5 composition, crash, restart, purity ---------------------------------

def test_protected_binding_and_reference_acts_retry_exactly(world):
	store, _config = world
	work = _create(store)["work_id"]
	first = tr.bind_work(store, work, actor_team="lang", actor="ada",
	                     root="pushcoin", path=PATH,
	                     expected_revision=0, rationale="attach",
	                     op_id="bind-1")
	again = tr.bind_work(store, work, actor_team="lang", actor="ada",
	                     root="pushcoin", path=PATH,
	                     expected_revision=0, rationale="attach",
	                     op_id="bind-1")
	assert again["operation"]["state"] == "replayed"
	assert again["seq"] == first["seq"]
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM bindings").fetchone()["n"] == 1
	with pytest.raises(bw.WorkError, match="different request"):
		tr.bind_work(store, work, actor_team="lang", actor="ada",
		             root="drift", path=PATH, expected_revision=0,
		             rationale="attach", op_id="bind-1")


def test_the_reference_bearing_commit_is_whole_or_nothing(world):
	store, _config = world
	bound = _create(store, binding=f"pushcoin:{PATH}")
	reader = _create(store, team="push", member="sl")
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
			tr.post_thread(
				store, reader["thread"], author_team="push",
				author="sl", body="evidence",
				refs=["drift:docs/a.md",
				      f"{bound['work_id']}:repro/b.sh"],
				op_id="post-1")
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
		assert boundary < 40, "the post never completed"


def test_restart_and_read_purity(world):
	store, _config = world
	bound = _create(store, binding=f"pushcoin:{PATH}")
	tr.post_thread(store, bound["thread"], author_team="lang",
	                   author="ada", body="anchored",
	                   refs=[f"{bound['work_id']}:notes.md"])
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	detail = pj.detail(fresh, bound["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	assert detail["binding"]["path"] == PATH
	fresh.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = hashlib.sha256(open(fresh.path, "rb").read()).hexdigest()
	pj.bindings(fresh, bound["work_id"])
	pj.thread(fresh, bound["thread"], viewer_team="lang",
	          viewer_member="grace")
	fresh.events()
	fresh.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert hashlib.sha256(
		open(fresh.path, "rb").read()).hexdigest() == digest, \
		"a binding/reference read wrote a byte"
	for kwargs in ({"after": -1}, {"limit": 0}, {"limit": 501}):
		with pytest.raises(bw.WorkError,
		                   match="pagination cursor|page limit"):
			pj.bindings(fresh, bound["work_id"], **kwargs)
	fresh.close()


def test_a_mid_flight_root_retirement_refuses_the_reference(world):
	"""The retirement committing between the optimistic parse and the
	write: the in-lock liveness check refuses the independent reference
	whole."""
	store, config_path = world
	born = _create(store)
	_interleave(store, lambda: _retire_root(config_path, "drift"))
	posts_before = len([event for event in store.events()
	                    if event["kind"] == "post_message"])
	with pytest.raises(bw.WorkError, match="not a live configured root"):
		tr.post_thread(store, born["thread"], author_team="lang",
		                   author="ada", body="raced by retirement",
		                   refs=["drift:docs/x.md"])
	assert len([event for event in store.events()
	            if event["kind"] == "post_message"]) == posts_before, \
		"the raced reference-bearing post still committed"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM act_references").fetchone()["n"] == 0


def test_regen_dossier_peek_respects_the_capability_boundary(world):
	"""R89: the store-touching dossier lookup runs only after the
	identity/capability gate — an actor the acceptance refuses learns
	nothing about which Work is bound."""
	store, config_path = world
	bound = _create(store, binding=f"drift:{PATH}")
	unbound = _create(store)["work_id"]
	document = _json.loads(open(config_path).read())
	document["generation"] += 1
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	# grace holds no config capability: the refusal is the CAPABILITY
	# one even though the cited work has no binding — the binding
	# lookup never ran for the refused identity.
	with pytest.raises(bw.WorkError, match="config capability"):
		lc.accept_config(config_path, actor="lang.grace",
		                 refs=[f"{unbound}:proof/x.md"])
	del bound
