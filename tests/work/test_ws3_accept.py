"""WS-3: the atomic provider acceptance.

One transaction commits — or refuses whole — the obligation's terminal
`accepted` state, the rationale in the consumer's thread, the
provenance-carrying edge, readiness, the exact-obligation wake (R47), and
in the create form the provider Work itself, established no later than the
acceptance that names it (R48). The authority is the ruled narrow grant:
the pending exact @ authorizes its live route handler, once.
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
from baton_work import cli as work_cli                        # noqa: E402
import fixtures as fx                                         # noqa: E402

import json as _json


@pytest.fixture
def world(tmp_path):
	spec = {"drift": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                  "kinds": ["bug", "rsrch"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}}
	config_path, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _report(store, team="push", member="sl"):
	work = tr.create_work(store, team=team, kind="bug", title=f"{team} report",
	                      origin="external-report", classification="suspected-defect", author=member,
	                      body="local report")["work_id"]
	asked = fx.post(store, work, author_team=team, author=member,
	                        body="drift: yours?", request="drift.bug")["seq"]
	return work, asked


def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


# -- the create form: whole effects and truthful ordering --------------------

def test_accept_create_commits_every_half_in_one_ordered_act(world):
	store, _config = world
	push1, asked = _report(store)
	result = tr.accept_obligation(
		store, asked, actor_team="drift", actor="ada",
		body="ours; tracking as a parser regression",
		create={"kind": "rsrch", "classification": "suspected-defect", "title": "parser recovery"})
	provider = result["provider"]
	assert result["created"] is True

	# R48: the provider exists AT the acceptance's own sequence.
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (provider,)).fetchone()
	assert row["created_seq"] == result["seq"]
	assert row["origin"] == "external-report"
	assert provider.endswith(f"-W{result['seq']}")

	# The obligation is terminally ACCEPTED, addressed to this act, naming
	# the provider.
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (asked,)).fetchone()
	assert obligation["status"] == "accepted"
	assert obligation["resolved_seq"] == result["seq"]
	assert obligation["accepted_into"] == provider
	assert pj.obligations(store, viewer_team="drift") == []

	# The edge exists with provenance; readiness recomputed.
	edge = store.conn.execute(
		"SELECT * FROM edges WHERE work=? AND blocker=?",
		(push1, provider)).fetchone()
	assert edge["via_obligation"] == asked
	assert store.conn.execute("SELECT ready FROM work WHERE id=?",
	                          (push1,)).fetchone()["ready"] == 0

	# Both threads carry the rationale: the provider's first message
	# at the accept seq, the consumer's answer as the next ordered act.
	provider_first = store.conn.execute(
		"SELECT messages.* FROM messages JOIN threads "
		"ON threads.id = messages.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=?", (provider,)).fetchone()
	assert provider_first["seq"] == result["seq"]
	consumer_answer = store.conn.execute(
		"SELECT messages.* FROM messages JOIN threads "
		"ON threads.id = messages.thread "
		"JOIN work ON work.created_seq = threads.created_seq "
		"WHERE work.id=? ORDER BY messages.seq DESC LIMIT 1",
		(push1,)).fetchone()
	assert consumer_answer["seq"] == result["seq"] + 1
	assert consumer_answer["body"].startswith("ours; tracking")

	# The audit: dense, with the accept act carrying both authority and
	# creation, then the consumer message act.
	events = store.events()
	assert [event["seq"] for event in events] == \
		list(range(1, len(events) + 1))
	accept = next(event for event in events if event["kind"] == "accept")
	assert accept["seq"] == result["seq"]
	assert accept["payload"]["created"] is True
	assert accept["payload"]["provider"] == provider
	assert accept["payload"]["authorization"]["endpoint"] == "drift.bug"
	assert accept["payload"]["resolution"]["endpoint"] == "drift.rsrch"
	answered = next(event for event in events
	                if event["seq"] == result["seq"] + 1)
	assert answered["kind"] == "post_message"
	assert answered["payload"]["via_accept"] == result["seq"]

	# Projections: provenance from both sides, one snapshot.
	links = pj.links(store, push1)
	assert links["blocked_by"][0]["id"] == provider
	assert links["blocked_by"][0]["via_obligation"] == asked
	assert pj.links(store, provider)["blocks"][0]["via_obligation"] == asked
	assert pj.detail(store, provider, viewer_team="drift",
	                 viewer_member="ada")["open_dependents"] == 1


def test_accept_into_gates_an_existing_provider(world):
	store, _config = world
	provider = tr.create_work(store, team="drift", kind="rsrch",
	                          title="parser recovery",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="tracking")["work_id"]
	push1, asked = _report(store)
	web1, web_asked = _report(store, team="web", member="wren")
	tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
	                     body="same parser regression", into=provider)
	tr.accept_obligation(store, web_asked, actor_team="drift", actor="ada",
	                     body="same parser regression", into=provider)
	detail = pj.detail(store, provider, viewer_team="drift",
	                   viewer_member="ada")
	assert detail["open_dependents"] == 2
	assert {entry["via_obligation"] for entry in
	        detail["links"]["blocks"]} == {asked, web_asked}
	accept = next(event for event in store.events()
	              if event["kind"] == "accept")
	assert accept["payload"]["created"] is False
	assert accept["payload"]["provider_route"]["endpoint"] == \
		"drift.rsrch", "the provider Route evidence is missing"


def test_accept_result_exposes_the_ruled_structured_edge(world):
	store, _config = world
	consumer, asked = _report(store)
	result = tr.accept_obligation(
		store, asked, actor_team="drift", actor="ada", body="ours",
		create={"kind": "rsrch", "classification": "suspected-defect", "title": "parser recovery"})
	assert result["edge"] == {
		"work": consumer,
		"blocker": result["provider"],
		"via_obligation": asked,
	}


def test_into_form_refuses_create_only_cli_options(world, capsys):
	store, config = world
	provider = tr.create_work(store, team="drift", kind="rsrch",
	                          title="parser recovery",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="tracking")["work_id"]
	_consumer, asked = _report(store)
	before = store.events()
	code = work_cli.main([
		"--config", config, "--participant", "drift.ada", "accept",
		f"obligation={asked}", "body=ours", f"into={provider}",
		f"parent={provider}"])
	assert code == 1
	assert "parent=" in _json.loads(capsys.readouterr().err)["error"]
	assert store.events() == before


@pytest.mark.parametrize("token", [
	"kind=rsrch",
	"title=parser recovery",
	"classification=bug",
	"parent=ignored-W1",
])
def test_into_form_refuses_every_create_only_cli_option(
		world, capsys, token):
	store, config = world
	provider = tr.create_work(store, team="drift", kind="rsrch",
	                          title="parser recovery",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="tracking")["work_id"]
	_consumer, asked = _report(store)
	before = store.events()
	code = work_cli.main([
		"--config", config, "--participant", "drift.ada", "accept",
		f"obligation={asked}", "body=ours", f"into={provider}", token])
	assert code == 1
	key = token.split("=")[0] + "="
	assert key in _json.loads(capsys.readouterr().err)["error"]
	assert store.events() == before


# -- authority: the narrow grant and its boundaries --------------------------

def test_only_the_live_route_handler_holds_the_grant(world):
	store, config_path = world
	push1, asked = _report(store)
	for team, member in (("drift", "grace"), ("push", "sl")):
		with pytest.raises(bw.WorkError, match="ownership"):
			tr.accept_obligation(store, asked, actor_team=team,
			                     actor=member, body="not mine",
			                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	# Reassignment moves the grant with the accepted generation.
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["drift"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="drift.ada")
	with pytest.raises(bw.WorkError, match="ownership"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="no longer the handler",
		                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="grace", body="mine now",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	accept = next(event for event in store.events()
	              if event["kind"] == "accept")
	assert accept["payload"]["authorization"]["generation"] == 2
	assert accept["payload"]["authorization"]["handlers"] == ["grace"]
	del result


def test_into_requires_the_obligations_own_team_and_open_work(world):
	store, _config = world
	push1, asked = _report(store)
	foreign = tr.create_work(store, team="web", kind="bug", title="w",
	                         origin="external-report", classification="suspected-defect", author="wren",
	                         body="b")["work_id"]
	with pytest.raises(bw.WorkError, match="addressed to"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="wrong team", into=foreign)
	closed = tr.create_work(store, team="drift", kind="rsrch", title="c",
	                        origin="external-report", classification="suspected-defect", author="ada",
	                        body="b")["work_id"]
	tr.close_work(store, closed, actor_team="drift", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="gates nothing"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="closed target", into=closed)


def test_create_with_parent_needs_the_separate_parent_gate(world):
	store, _config = world
	epic = tr.create_work(store, team="drift", kind="rsrch", title="epic",
	                      origin="self-initiated", classification="suspected-defect", author="ada",
	                      body="the umbrella")["work_id"]
	push1, asked = _report(store)
	# grace holds the route after a gen-2 swap of the PARENT's current
	# route? Simpler: ada is both the route handler and the parent's
	# Route handler — allowed; grace is neither — already covered. The
	# separate-gate case: make ada the obligation handler but NOT the
	# parent handler by passing the parent's Current away.
	fx.post(store, epic, author_team="drift", author="ada",
	                body="park with grace's build", pass_to="drift.bug")
	# drift.bug routes main -> handlers [ada]; both gates still ada, so
	# acceptance under a parent succeeds and records BOTH authorities.
	result = tr.accept_obligation(
		store, asked, actor_team="drift", actor="ada", body="child of epic",
		create={"kind": "rsrch", "classification": "suspected-defect", "title": "step", "parent": epic})
	accept = next(event for event in store.events()
	              if event["kind"] == "accept")
	assert accept["payload"]["parent_authorization"]["endpoint"] == \
		"drift.bug"
	row = store.conn.execute("SELECT parent FROM work WHERE id=?",
	                         (result["provider"],)).fetchone()
	assert row["parent"] == epic


# -- R47: wake semantics ------------------------------------------------------

def test_accept_wakes_the_exact_obligation_waiter_but_not_ready(world):
	store, _config = world
	push1, asked = _report(store)
	tr.set_phase(store, push1, actor_team="push", actor="sl",
	             phase="waiting", wait=asked)
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	row = store.conn.execute(
		"SELECT phase, ready, wait_obligation FROM work WHERE id=?",
		(push1,)).fetchone()
	assert row["phase"] == "queued", \
		"the exact-obligation waiter did not wake"
	assert row["ready"] == 0, "the new gate did not hold readiness false"
	wakes = [event for event in store.events() if event["kind"] == "wake"]
	assert len(wakes) == 1
	assert wakes[0]["payload"]["condition"]["obligation"] == asked
	assert wakes[0]["seq"] > result["seq"]


def test_accept_never_wakes_a_gates_waiter(world):
	store, _config = world
	push1, asked = _report(store)
	other_gate = tr.create_work(store, team="web", kind="bug", title="g",
	                            origin="external-report", classification="suspected-defect", author="wren",
	                            body="b")["work_id"]
	tr.add_dependency(store, push1, other_gate, actor_team="push",
	                  actor="sl", rationale="test dependency")
	tr.set_phase(store, push1, actor_team="push", actor="sl",
	             phase="waiting", wait="gates")
	tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
	                     body="ours", create={"kind": "rsrch",
	                                          "classification": "suspected-defect",
	                                          "title": "t"})
	row = store.conn.execute("SELECT phase FROM work WHERE id=?",
	                         (push1,)).fetchone()
	assert row["phase"] == "waiting", \
		"an accept woke a gates-waiter it had just re-gated"
	assert not [event for event in store.events()
	            if event["kind"] == "wake"]


# -- refusals and races -------------------------------------------------------

def test_acceptance_refusals_commit_nothing(world):
	store, _config = world
	push1, asked = _report(store)
	baseline = store.events()
	cases = [
		dict(body="", create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"}),
		dict(body="b"),
		dict(body="b", into="x", create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"}),
		dict(body="b", create={"kind": "nope", "classification": "suspected-defect", "title": "t"}),
		dict(body="b", create={"kind": "rsrch", "classification": "suspected-defect", "title": " "}),
		dict(body="b", create={"kind": "rsrch", "classification": "suspected-defect", "title": "t",
		                       "phase": "parked"}),
		dict(body="b", create={"kind": "rsrch", "title": "t",
		                       "classification": ""}),
		dict(body="b", create={"kind": "rsrch", "classification": "suspected-defect", "title": "t",
		                       "phase": ""}),
		dict(body="b", into="none-W9"),
	]
	for kwargs in cases:
		with pytest.raises(bw.WorkError):
			tr.accept_obligation(store, asked, actor_team="drift",
			                     actor="ada", **kwargs)
	assert store.events() == baseline, "a refused acceptance left effects"
	# Verification assignments are not acceptable.
	provider = tr.create_work(store, team="drift", kind="rsrch", title="p",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="b")["work_id"]
	created = tr.create_trial(store, provider, actor_team="drift",
	                          actor="ada", candidate="c",
	                          assign=["push.bug"])
	with pytest.raises(bw.WorkError, match="verification"):
		tr.accept_obligation(store, created["assignments"][0],
		                     actor_team="push", actor="sl", body="b",
		                     into=provider)


def test_the_double_accept_race_creates_no_orphan(world):
	store, _config = world
	push1, asked = _report(store)
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.accept_obligation(
		other, asked, actor_team="drift", actor="ada",
		body="the first session's acceptance",
		create={"kind": "rsrch", "classification": "suspected-defect", "title": "first"}))
	with pytest.raises(bw.WorkError, match="already accepted"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="the second session's acceptance",
		                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "second"})
	works = [row["id"] for row in store.conn.execute(
		"SELECT id FROM work WHERE team='drift'")]
	assert len(works) == 1, "the losing accept left an orphan provider"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 1
	other.close()


def test_the_accept_versus_consumer_close_race_serializes(world):
	store, _config = world
	push1, asked = _report(store)
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.close_work(
		other, push1, actor_team="push", actor="sl",
		rationale="withdrawn locally", outcome="non-satisfying"))
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="racing", create={"kind": "rsrch",
		                                           "classification": "suspected-defect",
		                                           "title": "t"})
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM work WHERE team='drift'").fetchone(
		)["n"] == 0
	other.close()


def test_the_accept_versus_provider_close_race_serializes(world):
	store, _config = world
	provider = tr.create_work(store, team="drift", kind="rsrch", title="p",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="b")["work_id"]
	push1, asked = _report(store)
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.close_work(
		other, provider, actor_team="drift", actor="ada",
		rationale="closed mid-accept", outcome="satisfying"))
	with pytest.raises(bw.WorkError, match="gates nothing"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="racing", into=provider)
	assert store.conn.execute(
		"SELECT status FROM obligations WHERE seq=?",
		(asked,)).fetchone()["status"] == "pending", \
		"the losing accept still terminalized the obligation"
	other.close()


def test_accept_first_then_dispose_and_retry_refuse(world):
	store, _config = world
	push1, asked = _report(store)
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.accept_obligation(
		other, asked, actor_team="drift", actor="ada", body="accepted",
		create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"}))
	with pytest.raises(bw.WorkError, match="already accepted"):
		tr.dispose_obligation(store, asked, team="drift", member="ada",
		                      disposition="racing dispose")
	# The stated retry boundary: no operation ids, so a retried accept
	# refuses with zero duplicate effects.
	with pytest.raises(bw.WorkError, match="already accepted"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="accepted", create={"kind": "rsrch",
		                                              "classification": "suspected-defect",
		                                              "title": "t"})
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 1
	other.close()


def test_the_atomic_accept_rolls_back_whole_at_every_boundary(world):
	"""Fault injection at each successive write inside the accept: every
	fault leaves the authority byte-identical — neither half ever commits
	alone."""
	store, _config = world
	push1, asked = _report(store)
	tr.set_phase(store, push1, actor_team="push", actor="sl",
	             phase="waiting", wait=asked)
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
			tr.accept_obligation(store, asked, actor_team="drift",
			                     actor="ada", body="atomic",
			                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
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
				f"fault at write {boundary} left half an acceptance"
			assert store.events() == baseline_events
		assert boundary < 60, "the accept never completed"
	# Whole: provider, edge, accepted obligation, message, wake.
	obligation = store.conn.execute(
		"SELECT status, accepted_into FROM obligations WHERE seq=?",
		(asked,)).fetchone()
	assert obligation["status"] == "accepted"
	assert store.conn.execute(
		"SELECT via_obligation FROM edges WHERE work=?",
		(push1,)).fetchone()["via_obligation"] == asked
	assert store.conn.execute(
		"SELECT phase, ready FROM work WHERE id=?",
		(push1,)).fetchone()["phase"] == "queued"


def test_restart_reconstructs_the_acceptance(world):
	store, _config = world
	push1, asked = _report(store)
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	fresh = bw.Authority(store.path)
	links = pj.links(fresh, push1)
	assert links["blocked_by"][0]["id"] == result["provider"]
	assert links["blocked_by"][0]["via_obligation"] == asked
	assert fresh.conn.execute(
		"SELECT status, accepted_into FROM obligations WHERE seq=?",
		(asked,)).fetchone()["accepted_into"] == result["provider"]
	fresh.close()


# -- R52: the relations are integrity-bound ----------------------------------

def test_the_new_relations_are_schema_bound(world):
	"""via_obligation and accepted_into are foreign keys: garbage
	references refuse at the database, ordinary edges keep NULL, and a
	non-accepted obligation never acquires a provider."""
	store, _config = world
	push1, asked = _report(store)
	import sqlite3
	with pytest.raises(sqlite3.IntegrityError):
		store.conn.execute(
			"INSERT INTO edges (work, blocker, via_obligation, "
			"created_seq) VALUES (?, ?, 424242, 99)", (push1, push1))
	store.conn.execute("ROLLBACK")
	with pytest.raises(sqlite3.IntegrityError):
		store.conn.execute(
			"UPDATE obligations SET accepted_into='ghost-W9' WHERE seq=?",
			(asked,))
	store.conn.execute("ROLLBACK")
	# An ordinary block stays provenance-free; respond leaves no provider.
	other_gate = tr.create_work(store, team="web", kind="bug", title="g",
	                            origin="external-report", classification="suspected-defect", author="wren",
	                            body="b")["work_id"]
	tr.add_dependency(store, push1, other_gate, actor_team="push",
	                  actor="sl", rationale="test dependency")
	assert store.conn.execute(
		"SELECT via_obligation FROM edges WHERE work=? AND blocker=?",
		(push1, other_gate)).fetchone()["via_obligation"] is None
	tr.respond_obligation(store, asked, team="drift", member="ada",
	                      body="answered plainly")
	assert store.conn.execute(
		"SELECT accepted_into FROM obligations WHERE seq=?",
		(asked,)).fetchone()["accepted_into"] is None


# -- R53: the completed race matrix ------------------------------------------

def test_accept_first_then_consumer_close_both_commit(world):
	"""Accept-first order: the acceptance commits; the consumer's later
	close is legal, withdraws nothing acceptance-related, and the edge
	remains historical evidence."""
	store, _config = world
	push1, asked = _report(store)
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	tr.close_work(store, push1, actor_team="push", actor="sl",
	              rationale="resolved locally anyway",
	              outcome="non-satisfying")
	obligation = pj.detail(store, push1, viewer_team="push",
	                       viewer_member="sl")["obligations"][0]
	assert obligation["status"] == "accepted"
	assert obligation["accepted_into"] == result["provider"]
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 1
	assert not [e for e in store.events() if e["kind"] == "withdraw"], \
		"the close withdrew an already-terminal obligation"


def test_accept_first_then_provider_close_fans_out(world):
	store, _config = world
	push1, asked = _report(store)
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	tr.close_work(store, result["provider"], actor_team="drift",
	              actor="ada", rationale="fixed", outcome="satisfying")
	row = store.conn.execute("SELECT ready FROM work WHERE id=?",
	                         (push1,)).fetchone()
	assert row["ready"] == 1, "the provider close did not end the gate"


def test_dispose_first_makes_the_accept_refuse(world):
	store, _config = world
	push1, asked = _report(store)
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.dispose_obligation(
		other, asked, team="drift", member="ada",
		disposition="not ours after all"))
	with pytest.raises(bw.WorkError, match="already disposed"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="racing accept",
		                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM work WHERE team='drift'").fetchone(
		)["n"] == 0, "the losing accept left an orphan"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges").fetchone()["n"] == 0
	other.close()


def test_a_config_change_landing_mid_accept_decides_in_the_lock(world):
	"""Regen-first order, raced: the generation-2 acceptance commits
	between the optimistic gate and the lock — the in-lock gate decides
	under the NEW generation and the former handler refuses."""
	store, config_path = world
	push1, asked = _report(store)
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["drift"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	_interleave(store, lambda: lc.accept_config(config_path,
	                                            actor="drift.ada"))
	with pytest.raises(bw.WorkError, match="ownership"):
		tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
		                     body="stale authority",
		                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM work WHERE team='drift'").fetchone(
		)["n"] == 0


def test_accept_first_then_config_change_keeps_the_snapshot(world):
	store, config_path = world
	push1, asked = _report(store)
	tr.accept_obligation(store, asked, actor_team="drift", actor="ada",
	                     body="under generation 1",
	                     create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	document = _json.loads(open(config_path).read())
	document["generation"] = 2
	document["teams"]["drift"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="drift.ada")
	accept = next(event for event in store.events()
	              if event["kind"] == "accept")
	assert accept["payload"]["authorization"]["generation"] == 1
	assert accept["payload"]["authorization"]["handlers"] == ["ada"], \
		"the later generation rewrote the recorded authority snapshot"


def test_concurrent_accepts_of_different_obligations_both_commit(world):
	store, _config = world
	provider = tr.create_work(store, team="drift", kind="rsrch", title="p",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="b")["work_id"]
	push1, push_asked = _report(store)
	web1, web_asked = _report(store, team="web", member="wren")
	other = bw.Authority(store.path)
	_interleave(store, lambda: tr.accept_obligation(
		other, web_asked, actor_team="drift", actor="ada",
		body="web accepted first", into=provider))
	tr.accept_obligation(store, push_asked, actor_team="drift",
	                     actor="ada", body="push accepted second",
	                     into=provider)
	detail = pj.detail(store, provider, viewer_team="drift",
	                   viewer_member="ada")
	assert detail["open_dependents"] == 2
	assert {entry["via_obligation"] for entry in
	        detail["links"]["blocks"]} == {push_asked, web_asked}
	assert len([e for e in store.events()
	            if e["kind"] == "accept"]) == 2
	other.close()


def test_the_into_form_rolls_back_whole_at_every_boundary(world):
	store, _config = world
	provider = tr.create_work(store, team="drift", kind="rsrch", title="p",
	                          origin="external-report", classification="suspected-defect", author="ada",
	                          body="b")["work_id"]
	push1, asked = _report(store)
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
			tr.accept_obligation(store, asked, actor_team="drift",
			                     actor="ada", body="atomic into",
			                     into=provider)
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
				f"fault at write {boundary} left half an acceptance"
			assert store.events() == baseline_events
		assert boundary < 60, "the accept never completed"
	assert store.conn.execute(
		"SELECT accepted_into FROM obligations WHERE seq=?",
		(asked,)).fetchone()["accepted_into"] == provider


def test_restart_reconstructs_the_accepted_state_publicly(world):
	"""The accepted terminal state is read back through the PUBLIC
	projection after restart — no SQL, no audit mining."""
	store, _config = world
	push1, asked = _report(store)
	result = tr.accept_obligation(store, asked, actor_team="drift",
	                              actor="ada", body="ours",
	                              create={"kind": "rsrch", "classification": "suspected-defect", "title": "t"})
	fresh = bw.Authority(store.path)
	detail = pj.detail(fresh, push1, viewer_team="push",
	                   viewer_member="sl")
	entry = detail["obligations"][0]
	assert entry["seq"] == asked
	assert entry["status"] == "accepted"
	assert entry["accepted_into"] == result["provider"]
	assert detail["links"]["blocked_by"][0]["via_obligation"] == asked
	fresh.close()


def test_accept_create_refuses_omitted_and_unknown_classification(world):
	"""finding-active-work-claim (review 2026-08-16T09-27-05Z): the
	acceptance-creation path independently requires the submitter's
	concrete classification. Omission and explicit 'unknown' each refuse,
	and the refusal commits NOTHING — the obligation stays pending, no
	event, no provider Work, no edge, no message."""
	store, _config = world
	_push1, asked = _report(store)

	def snapshot():
		count = lambda table: store.conn.execute(
			f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
		pending = store.conn.execute(
			"SELECT status FROM obligations WHERE seq=?",
			(asked,)).fetchone()["status"]
		return (store.last_seq(), pending, count("work"), count("edges"),
		        count("messages"))

	before = snapshot()
	for create in ({"kind": "rsrch", "title": "t"},
	               {"kind": "rsrch", "title": "t",
	                "classification": "unknown"}):
		with pytest.raises(bw.WorkError, match="concrete classification"):
			tr.accept_obligation(store, asked, actor_team="drift",
			                     actor="ada", body="ours", create=create)
		assert snapshot() == before, \
			f"a refused acceptance ({create}) left effects"
	assert before[1] == "pending", "the obligation moved"
