"""WS-4 Slice B: public thread-addressed carrying operators.

`@`, `=>`, and planned Next act on exactly ONE currently labelled,
eligible open Work (D2/R55/D9): explicit `--on` must name a current
label; omitted, it resolves only at eligible-cardinality one, recorded
and echoed. `+` stays the only fan-out and changes nothing but recorded
attention. Obligations bind to their originating thread (R59);
acceptance labels it collision-safely (D5); the gate stays the edge.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
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


def _event(store, seq):
	return next(event for event in store.events() if event["seq"] == seq)


# -- selection: explicit --on, omitted resolution, eligibility ----------------

def test_omitted_on_resolves_the_single_eligible_and_echoes(world):
	"""R55: eligibility counts labels passing the operation's Work gate —
	a foreign label the actor cannot act on creates no false ambiguity."""
	store = world
	mine = _create(store)
	foreign = _create(store, team="push", member="sl")
	tr.label_thread(store, mine["thread"], foreign["work_id"],
	                    actor_team="push", actor="sl")
	result = tr.post_thread(store, mine["thread"],
	                            author_team="lang", author="ada",
	                            body="push: confirm", request="push.bug", wait=False)
	assert result["kind"] == "request" and result["work"] == mine["work_id"]
	payload = _event(store, result["seq"])["payload"]
	assert payload["work"] == mine["work_id"]
	assert payload["on_resolved"] is True, \
		"the omitted selection was not recorded as resolved"
	obligation = store.conn.execute(
		"SELECT work FROM obligations WHERE seq=?",
		(result["seq"],)).fetchone()
	assert obligation["work"] == mine["work_id"], \
		"a request in a thread obligated another work"


def test_two_eligible_refuse_and_explicit_on_selects(world):
	store = world
	first = _create(store)
	second = _create(store)
	tr.label_thread(store, first["thread"], second["work_id"],
	                    actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="exactly one labelled work"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="whose?",
		                   request="push.bug", wait=False)
	result = tr.post_thread(store, first["thread"],
	                            author_team="lang", author="ada",
	                            body="push: confirm on the second",
	                            request="push.bug", wait=False, on=second["work_id"])
	obligation = store.conn.execute(
		"SELECT work, thread FROM obligations WHERE seq=?",
		(result["seq"],)).fetchone()
	assert obligation["work"] == second["work_id"]
	assert obligation["thread"] == first["thread"], \
		"the obligation does not name its originating thread"
	payload = _event(store, result["seq"])["payload"]
	assert payload["on"] == second["work_id"]
	assert payload["on_resolved"] is False


def test_selection_refusals_are_exact(world):
	store = world
	first = _create(store)
	stranger = _create(store)
	with pytest.raises(bw.WorkError, match="not among"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False,
		                   on=stranger["work_id"])
	with pytest.raises(bw.WorkError, match="carries none"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", on=first["work_id"])
	with pytest.raises(bw.WorkError, match="exactly one endpoint"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="*.bug", wait=False,
		                   on=first["work_id"])
	# W171: the posting surface carries NO pass vocabulary at all — a
	# baton transfer through a message is a type error, not a refusal.
	with pytest.raises(TypeError):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False,
		                   pass_to="lang.rsrch", on=first["work_id"])
	with pytest.raises(TypeError):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x",
		                   set_next="lang.rsrch", on=first["work_id"])
	# The unauthorized actor has ZERO eligible works, not an error about
	# someone else's authority.
	with pytest.raises(bw.WorkError, match="has 0"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="grace", body="x", request="push.bug", wait=False)


def test_closed_context_refuses_carrying_but_welcomes_commentary(world):
	"""D3 restated: closed Work refuses CARRYING activity; commentary in
	a thread that still has open context flows freely."""
	store = world
	live = _create(store)
	done = _create(store)
	tr.label_thread(store, live["thread"], done["work_id"],
	                    actor_team="lang", actor="ada")
	tr.close_work(store, done["work_id"], actor_team="lang", actor="ada",
	              rationale="finished", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="closed work refuses carrying"):
		tr.post_thread(store, live["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False,
		                   on=done["work_id"])
	# Omitted --on: the closed label is simply not eligible; the open one
	# resolves.
	result = tr.post_thread(store, live["thread"],
	                            author_team="lang", author="ada",
	                            body="push: confirm", request="push.bug", wait=False)
	assert store.conn.execute(
		"SELECT work FROM obligations WHERE seq=?",
		(result["seq"],)).fetchone()["work"] == live["work_id"]
	plain = tr.post_thread(store, live["thread"],
	                           author_team="lang", author="ada",
	                           body="context note about the closed leg")
	assert plain["kind"] == "post_message"


# -- + include: the only fan-out, attention only ------------------------------

def test_include_records_expansion_and_changes_nothing_else(world):
	store = world
	mine = _create(store)
	before = {
		"work": [dict(row) for row in store.conn.execute(
			"SELECT * FROM work ORDER BY id")],
		"edges": store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges").fetchone()["n"],
		"obligations": store.conn.execute(
			"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"],
	}
	result = tr.post_thread(store, mine["thread"],
	                            author_team="lang", author="ada",
	                            body="fyi", include="*.bug")
	assert result["included"] == ["lang.bug", "push.bug"]
	recorded = _event(store, result["seq"])["payload"]["include"]
	assert [entry["endpoint"] for entry in recorded] == \
		["lang.bug", "push.bug"]
	after = [dict(row) for row in store.conn.execute(
		"SELECT * FROM work ORDER BY id")]
	assert after == before["work"], "+ touched a work row"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == \
		before["edges"]
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == \
		before["obligations"]
	view = pj.thread(store, mine["thread"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["participants"] == ["lang", "push"]
	# Once: a second include does not duplicate the participation row.
	tr.post_thread(store, mine["thread"], author_team="lang",
	                   author="ada", body="again", include="push.bug")
	assert pj.thread(store, mine["thread"], viewer_team="lang",
	                 viewer_member="ada")["participants"] == \
		["lang", "push"]


# -- obligation binding and the response's return path ------------------------

def test_respond_returns_to_the_originating_thread(world):
	"""R59: the answer lands where the @ was raised, even when the
	consumer label has since been removed — removal never cancels the
	obligation, and participation persists after it terminates."""
	store = world
	first = _create(store)
	second = _create(store)
	tr.label_thread(store, first["thread"], second["work_id"],
	                    actor_team="lang", actor="ada")
	asked = tr.post_thread(store, first["thread"],
	                           author_team="lang", author="ada",
	                           body="push: confirm", request="push.bug", wait=False,
	                           on=second["work_id"])["seq"]
	tr.unlabel_thread(store, first["thread"], second["work_id"],
	                      actor_team="lang", actor="ada")
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(asked,)).fetchone()["status"] == "pending", \
		"removing the label cancelled the obligation"
	pending = pj.obligations(store, viewer_team="push")
	assert pending[0]["thread"] == first["thread"], \
		"public obligation state does not name the thread"
	result = tr.respond_obligation(store, asked, team="push", member="sl",
	                               body="confirmed")
	landed = store.conn.execute(
		"SELECT thread FROM messages WHERE seq=?",
		(result["seq"],)).fetchone()
	assert landed["thread"] == first["thread"], \
		"the answer did not return to the originating thread"
	view = pj.thread(store, first["thread"], viewer_team="push",
	                 viewer_member="sl")
	assert "push" in view["participants"], \
		"participation did not persist past the obligation"
	detail = pj.detail(store, second["work_id"], viewer_team="lang",
	                   viewer_member="ada")
	assert detail["obligations"][0]["thread"] == first["thread"]


# -- acceptance: originating label, collision-safe ----------------------------

def test_accept_labels_the_originating_thread(world):
	store = world
	consumer = _create(store, team="push", member="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug", wait=False)["seq"]
	provider = _create(store)
	result = tr.accept_obligation(store, asked, actor_team="lang",
	                              actor="ada", body="ours; tracked",
	                              into=provider["work_id"])
	payload = _event(store, result["seq"])["payload"]
	assert payload["provider_label"] == "added"
	assert payload["thread"] == consumer["thread"]
	view = pj.thread(store, consumer["thread"], viewer_team="push",
	                 viewer_member="sl")
	assert {entry["work"] for entry in view["labels"]} == \
		{consumer["work_id"], provider["work_id"]}, \
		"the acceptance did not label the originating thread"
	assert view["messages"][-1]["body"] == "ours; tracked"
	assert "lang" in view["participants"]
	assert store.conn.execute(
		"SELECT via_obligation FROM edges WHERE work=? AND blocker=?",
		(consumer["work_id"], provider["work_id"])).fetchone()[
		"via_obligation"] == asked


def test_accept_tolerates_the_preexisting_label_as_existing(world):
	store = world
	consumer = _create(store, team="push", member="sl")
	provider = _create(store)
	tr.label_thread(store, consumer["thread"],
	                    provider["work_id"], actor_team="lang",
	                    actor="ada")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug", wait=False)["seq"]
	result = tr.accept_obligation(store, asked, actor_team="lang",
	                              actor="ada", body="already in context",
	                              into=provider["work_id"])
	assert _event(store, result["seq"])["payload"][
		"provider_label"] == "existing"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM thread_labels WHERE thread=? "
		"AND work=?", (consumer["thread"],
		               provider["work_id"])).fetchone()["n"] == 1, \
		"the collision-safe acceptance duplicated the label"


def test_the_gate_is_the_edge_never_the_label(world):
	"""Drop the label — gating unchanged; the association test and the
	readiness predicate live on different records by construction."""
	store = world
	consumer = _create(store, team="push", member="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug", wait=False)["seq"]
	provider = _create(store)
	tr.accept_obligation(store, asked, actor_team="lang", actor="ada",
	                     body="ours", into=provider["work_id"])
	assert pj.detail(store, consumer["work_id"], viewer_team="push",
	                 viewer_member="sl")["ready"] is False
	tr.unlabel_thread(store, consumer["thread"],
	                      provider["work_id"], actor_team="lang",
	                      actor="ada")
	after = pj.detail(store, consumer["work_id"], viewer_team="push",
	                  viewer_member="sl")
	assert after["ready"] is False and after["open_blockers"] == 1, \
		"removing the inert label changed the gate"
	tr.close_work(store, provider["work_id"], actor_team="lang",
	              actor="ada", rationale="done", outcome="satisfying")
	assert pj.detail(store, consumer["work_id"], viewer_team="push",
	                 viewer_member="sl")["ready"] is True


def test_accept_create_labels_the_originating_thread_too(world):
	store = world
	consumer = _create(store, team="push", member="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug", wait=False)["seq"]
	result = tr.accept_obligation(store, asked, actor_team="lang",
	                              actor="ada", body="new provider work",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	payload = _event(store, result["seq"])["payload"]
	assert payload["provider_label"] == "added"
	view = pj.thread(store, consumer["thread"], viewer_team="push",
	                 viewer_member="sl")
	assert result["provider"] in \
		{entry["work"] for entry in view["labels"]}
	# The provider's own born thread exists separately and speaks.
	born = pj.work_threads(store, result["provider"],
	                           viewer_team="lang", viewer_member="ada")
	ids = [row["id"] for row in born["rows"]]
	assert consumer["thread"] in ids and len(ids) == 2


# -- races: both orders across every new decision ------------------------------

def test_a_mid_flight_unlabel_refuses_the_explicit_selection(world):
	store = world
	first = _create(store)
	second = _create(store)
	tr.label_thread(store, first["thread"], second["work_id"],
	                    actor_team="lang", actor="ada")
	messages_before = store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
	_interleave(store, lambda: tr.unlabel_thread(
		store, first["thread"], second["work_id"],
		actor_team="lang", actor="ada"))
	with pytest.raises(bw.WorkError, match="not among"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False,
		                   on=second["work_id"])
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == \
		messages_before, "the refused carrying message still landed"


def test_a_mid_flight_close_refuses_the_carrying_operation(world):
	store = world
	first = _create(store)
	_interleave(store, lambda: tr.close_work(
		store, first["work_id"], actor_team="lang", actor="ada",
		rationale="closed underneath", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="has 0|closed work refuses"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False)
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == 0


def test_a_mid_flight_second_eligible_makes_the_omission_ambiguous(world):
	store = world
	first = _create(store)
	second = _create(store)
	_interleave(store, lambda: tr.label_thread(
		store, first["thread"], second["work_id"],
		actor_team="lang", actor="ada"))
	with pytest.raises(bw.WorkError,
	                   match="exactly one labelled work|lost a concurrent"):
		tr.post_thread(store, first["thread"], author_team="lang",
		                   author="ada", body="x", request="push.bug", wait=False)
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == 0, \
		"an ambiguous resolution still committed an obligation"


def test_accept_survives_a_racing_consumer_unlabel(world):
	"""Removing the consumer's own label never cancels the obligation;
	the acceptance commits whole against the raced state."""
	store = world
	consumer = _create(store, team="push", member="sl")
	sibling = _create(store, team="push", member="sl")
	tr.label_thread(store, consumer["thread"],
	                    sibling["work_id"], actor_team="push", actor="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?", request="lang.bug", wait=False,
	                           on=consumer["work_id"])["seq"]
	provider = _create(store)
	_interleave(store, lambda: tr.unlabel_thread(
		store, consumer["thread"], consumer["work_id"],
		actor_team="push", actor="sl"))
	result = tr.accept_obligation(store, asked, actor_team="lang",
	                              actor="ada", body="ours",
	                              into=provider["work_id"])
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(asked,)).fetchone()["status"] == "accepted"
	assert _event(store, result["seq"])["payload"][
		"provider_label"] == "added"


def test_the_reverse_orders_commit_cleanly(world):
	"""Carrying first, then unlabel/close: legal serials, both commit."""
	store = world
	first = _create(store)
	second = _create(store)
	tr.label_thread(store, first["thread"], second["work_id"],
	                    actor_team="lang", actor="ada")
	asked = tr.post_thread(store, first["thread"],
	                           author_team="lang", author="ada",
	                           body="push: confirm", request="push.bug", wait=False,
	                           on=second["work_id"])["seq"]
	tr.unlabel_thread(store, first["thread"], second["work_id"],
	                      actor_team="lang", actor="ada")
	tr.close_work(store, second["work_id"], actor_team="lang",
	              actor="ada", rationale="done", outcome="satisfying")
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(asked,)).fetchone()["status"] == "withdrawn", \
		"the close did not withdraw the pending @ (WS-2 discipline)"


# -- crash, restart, retry -----------------------------------------------------

def _exploding_sweep(store, act, limit=40):
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
			act()
			store.conn = real_conn
			return
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			now = hashlib.sha256(
				open(store.path, "rb").read()).hexdigest()
			assert now == baseline, \
				f"fault at write {boundary} left a partial commit"
			assert store.events() == baseline_events
		assert boundary < limit, "the act never completed"


def test_a_carrying_post_commits_whole_or_not_at_all(world):
	store = world
	first = _create(store)
	_exploding_sweep(store, lambda: tr.post_thread(
		store, first["thread"], author_team="lang", author="ada",
		body="push: confirm", request="push.bug", wait=False))


def test_the_labelling_acceptance_commits_whole_or_not_at_all(world):
	store = world
	consumer = _create(store, team="push", member="sl")
	asked = tr.post_thread(store, consumer["thread"],
	                           author_team="push", author="sl",
	                           body="lang: yours?",
	                           request="lang.bug", wait=False)["seq"]
	provider = _create(store)
	_exploding_sweep(store, lambda: tr.accept_obligation(
		store, asked, actor_team="lang", actor="ada", body="ours",
		into=provider["work_id"]))


def test_restart_reconstructs_the_binding_and_retry_refuses(world):
	store = world
	first = _create(store)
	asked = tr.post_thread(store, first["thread"],
	                           author_team="lang", author="ada",
	                           body="push: confirm",
	                           request="push.bug", wait=False)["seq"]
	tr.respond_obligation(store, asked, team="push", member="sl",
	                      body="confirmed")
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	row = fresh.conn.execute(
		"SELECT thread, status FROM obligations WHERE seq=?",
		(asked,)).fetchone()
	assert row["thread"] == first["thread"]
	assert row["status"] == "responded"
	with pytest.raises(bw.WorkError, match="already responded"):
		tr.respond_obligation(fresh, asked, team="push", member="sl",
		                      body="again")
	fresh.close()


# -- R69/R70/R71 additive coverage --------------------------------------------

def test_every_wildcard_shape_that_lands_nowhere_refuses_whole(world):
	"""R71: exact, team-wildcard, and kind-wildcard selectors all obey
	the landing rule; the refusal leaves message, event, and sequence
	untouched."""
	store = world
	mine = _create(store)
	before_events = store.events()
	before_messages = store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
	for selector in ("ghost.bug", "ghost.*", "*.ghost",
	                 "push.bug,ghost.*"):
		with pytest.raises(bw.WorkError, match="matches no live endpoint"):
			tr.post_thread(store, mine["thread"],
			                   author_team="lang", author="ada",
			                   body="nobody", include=selector)
	assert store.events() == before_events
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == \
		before_messages, "a landing-nowhere include still published"


@pytest.fixture
def raced(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def test_a_config_race_that_empties_a_selector_refuses_in_lock(raced):
	"""R71: the optimistic expansion reaches lang.rsrch; the committing
	generation retires it — the whole publication refuses rather than
	publishing to nobody."""
	import json as _json
	from baton_work import lifecycle as lc
	store, config_path = raced
	mine = _create(store)
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	del document["teams"]["lang"]["kinds"]["rsrch"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	before = store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
	_interleave(store, lambda: lc.accept_config(config_path,
	                                            actor="lang.ada"))
	with pytest.raises(bw.WorkError, match="matches no live endpoint"):
		tr.post_thread(store, mine["thread"], author_team="lang",
		                   author="ada", body="raced", include="*.rsrch")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == before, \
		"the raced empty include still published"


def test_the_console_thread_view_is_pure(world):
	"""R70 companion: painting the thread view writes no byte —
	viewing stays pure; only the explicit bounded mark writes."""
	import hashlib as _hashlib
	from baton_work.tui.app import Console
	store = world
	mine = _create(store)

	class Screen:
		def addnstr(self, *_args):
			pass

	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	digest = _hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	console = Console(store, "lang", "grace")
	console.detail_work = mine["work_id"]
	console.disc_cursor = None
	console.mode = "detail"
	console.focus = "msgs"
	console._render_detail(Screen(), 24, 100)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	assert _hashlib.sha256(
		open(store.path, "rb").read()).hexdigest() == digest, \
		"painting the thread view wrote to the authority"
	console.handle(ord("s"))
	view = pj.thread(store, mine["thread"], viewer_team="lang",
	                 viewer_member="grace")
	assert view["new"] == 0 and view["last_seq"] == mine["seq"], \
		"the bounded mark did not clear exactly the painted snapshot"
