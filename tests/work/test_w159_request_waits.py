"""W159 (finding-request-waits-by-default): a directed request blocks.

`request=` created an obligation; suspending the asking Work was a
SECOND command. So the common case — "I cannot go on until you answer"
— was unsafe by default: the Work stayed active and claimed while no
honest progress was possible, and an interruption between the two
commits left the workflow state lying.

The blocking form is now one transaction: publish, create the
obligation, enter the exact-obligation wait, release the claim.
`wait=false` is the deliberate asynchronous override.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"], "bee": ["impl"]},
		          "kinds": ["bug"]},
		 "push": {"members": {"sl": ["impl"]}, "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def asking(world, claim="ada"):
	"""A claimed Work with its born thread, ready to ask."""
	store = world["store"]
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the asker", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="opener")
	work = born["work_id"]
	thread = pj.work_threads(store, work, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	if claim:
		tr.claim_work(store, work, actor_team="lang", actor=claim)
	return work, thread


def state(world, work):
	return dict(world["store"].conn.execute(
		"SELECT phase, wait_type, wait_obligation, handler_team, "
		"handler_member, route_team, route_kind FROM work WHERE id=?",
		(work,)).fetchone())


# -- the blocking default ----------------------------------------------------

@pytest.mark.parametrize("spelling", [None, True])
def test_a_directed_request_blocks_atomically(world, spelling):
	"""Omitted and explicit true are the SAME effective operation."""
	store = world["store"]
	work, thread = asking(world)
	before = state(world, work)
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: please advise",
	                        request="push.bug", on=work, wait=spelling)
	after = state(world, work)
	assert after["phase"] == "waiting"
	assert after["wait_type"] == "obligation"
	assert after["wait_obligation"] == posted["seq"], \
		"the wait names some other obligation than the one just created"
	assert after["handler_team"] is None, "the claim was not released"
	# Current does NOT move: the answer is owed TO the handler
	assert (after["route_team"], after["route_kind"]) == \
		(before["route_team"], before["route_kind"])
	# and the obligation is real and actionable for the asked endpoint
	owed = pj.participant_actions(store, viewer_team="push",
	                              viewer_member="sl")["actions"]
	assert any(action["kind"] == "obligation"
	           and action["seq"] == posted["seq"] for action in owed)


def test_the_whole_thing_is_one_event(world):
	store = world["store"]
	work, thread = asking(world)
	before = store.last_seq()
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: advise",
	                        request="push.bug", on=work)
	assert posted["seq"] == before + 1, \
		"the blocking request consumed more than one sequence"
	event = [e for e in store.events() if e["seq"] == posted["seq"]][0]
	assert event["kind"] == "request"
	assert event["payload"]["wait"] is True, \
		"the effective waiting choice is not in the event evidence"
	assert event["payload"]["released_claimant"] == "lang.ada"


def test_the_exact_waiter_wakes_once_on_every_resolution(world):
	"""respond, dispose and accept each wake the one waiter."""
	store = world["store"]
	for resolve in ("respond", "dispose", "accept"):
		work, thread = asking(world)
		posted = tr.post_thread(store, thread, author_team="lang",
		                        author="ada", body="push: advise",
		                        request="push.bug", on=work)
		assert state(world, work)["phase"] == "waiting"
		if resolve == "respond":
			tr.respond_obligation(store, posted["seq"], team="push",
			                      member="sl", body="here you are")
		elif resolve == "dispose":
			tr.dispose_obligation(store, posted["seq"], team="push",
			                      member="sl", disposition="not ours")
		else:
			provider = tr.create_work(
				store, team="push", kind="bug", title="provider",
				origin="external-report",
				classification="suspected-defect", author="sl",
				body="b")["work_id"]
			tr.accept_obligation(store, posted["seq"], actor_team="push",
			                     actor="sl", body="gated on this",
			                     into=provider)
		after = state(world, work)
		# W38 R3: `accept` gates the waiter on the provider it just
		# named, so that resolution RETARGETS rather than waking.
		if resolve == "accept":
			assert after["phase"] == "waiting", \
				"accept advertised a gated waiter as runnable"
			assert after["wait_type"] == "gates"
		else:
			assert after["phase"] == "queued", \
				f"{resolve} did not wake the exact waiter"
			assert after["wait_type"] is None
		wakes = [e for e in store.events()
		         if e["kind"] == "wake"
		         and e["payload"]["work"] == work]
		expected = 0 if resolve == "accept" else 1
		assert len(wakes) == expected, \
			f"{resolve} woke the waiter {len(wakes)}x, expected {expected}"


def test_an_unrelated_obligation_does_not_wake_the_waiter(world):
	store = world["store"]
	work, thread = asking(world)
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: advise",
	                        request="push.bug", on=work)
	# a second, unrelated Work asks its own question and gets an answer
	other, other_thread = asking(world, claim="bee")
	other_posted = tr.post_thread(store, other_thread, author_team="lang",
	                              author="bee", body="push: and this?",
	                              request="push.bug", on=other)
	tr.respond_obligation(store, other_posted["seq"], team="push",
	                      member="sl", body="that one")
	assert state(world, work)["phase"] == "waiting", \
		"an unrelated resolution woke the wrong waiter"
	assert state(world, other)["phase"] == "queued"
	tr.respond_obligation(store, posted["seq"], team="push",
	                      member="sl", body="and this one")
	assert state(world, work)["phase"] == "queued"


# -- the explicit asynchronous override --------------------------------------

def test_wait_false_creates_the_obligation_and_changes_nothing_else(world):
	store = world["store"]
	work, thread = asking(world)
	before = state(world, work)
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: when you can",
	                        request="push.bug", on=work, wait=False)
	after = state(world, work)
	assert after == before, \
		"wait=false changed phase, claim, Current or wait condition"
	owed = pj.participant_actions(store, viewer_team="push",
	                              viewer_member="sl")["actions"]
	assert any(action["kind"] == "obligation"
	           and action["seq"] == posted["seq"] for action in owed), \
		"wait=false did not create an actionable obligation"
	event = [e for e in store.events() if e["seq"] == posted["seq"]][0]
	assert event["payload"]["wait"] is False


# -- refusals, all before mutation -------------------------------------------

def refuses(world, message, **kw):
	store = world["store"]
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match=message):
		tr.post_thread(store, **kw)
	assert store.last_seq() == before, "a refusal still committed"


def test_wait_without_a_request_refuses(world):
	_work, thread = asking(world)
	refuses(world, "carries no request", thread_id=thread,
	        author_team="lang", author="ada", body="x", wait=True)
	refuses(world, "carries no request", thread_id=thread,
	        author_team="lang", author="ada", body="x", wait=False)


def test_wait_without_a_request_cannot_replay_a_valid_plain_post(world):
	"""Validation precedes replay: an invalid spelling is never an exact
	retry merely because its effective request-wait value collapses to false."""
	store = world["store"]
	_work, thread = asking(world)
	tr.post_thread(store, thread, author_team="lang", author="ada",
	               body="plain context", op_id="plain-then-invalid")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="carries no request"):
		tr.post_thread(store, thread, author_team="lang", author="ada",
		               body="plain context", wait=True,
		               op_id="plain-then-invalid")
	assert store.last_seq() == before


def test_a_malformed_boolean_refuses_in_the_grammar(world):
	work, thread = asking(world)
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", "lang.ada", "say",
		                      f"thread={thread}", "body=x",
		                      "request=push.bug", f"on={work}",
		                      "wait=maybe"])
	assert code != 0
	assert "true" in (out.getvalue() + err.getvalue())


def test_an_unclaimed_work_cannot_be_blocked(world):
	work, thread = asking(world, claim=None)
	refuses(world, "unclaimed", thread_id=thread, author_team="lang",
	        author="ada", body="push: advise", request="push.bug",
	        on=work)
	# but the asynchronous form is still available
	tr.post_thread(world["store"], thread, author_team="lang",
	               author="ada", body="push: advise",
	               request="push.bug", on=work, wait=False)


def test_somebody_elses_claim_cannot_be_blocked(world):
	"""Route eligibility is not permission to park another participant's
	execution."""
	work, thread = asking(world, claim="bee")
	refuses(world, "claimed by lang.bee", thread_id=thread,
	        author_team="lang", author="ada", body="push: advise",
	        request="push.bug", on=work)


def test_a_second_blocking_request_cannot_stack(world):
	"""A Work already waiting is, by construction, unclaimed — entering
	waiting released the claim — so the claim gate is what refuses. No
	separate phase test is needed, and adding one would be unreachable
	code."""
	store = world["store"]
	work, thread = asking(world)
	tr.post_thread(store, thread, author_team="lang", author="ada",
	               body="push: advise", request="push.bug", on=work)
	suspended = state(world, work)
	assert suspended["phase"] == "waiting"
	assert suspended["handler_team"] is None
	refuses(world, "unclaimed", thread_id=thread, author_team="lang",
	        author="ada", body="push: again", request="push.bug",
	        on=work)


# -- effectively-once identity uses the EFFECTIVE value ----------------------

def test_an_exact_retry_may_spell_the_default_explicitly(world):
	store = world["store"]
	work, thread = asking(world)
	first = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: advise",
	                       request="push.bug", on=work, op_id="ask-1")
	again = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: advise",
	                       request="push.bug", on=work, wait=True,
	                       op_id="ask-1")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"


def test_flipping_the_effective_value_fails_closed(world):
	store = world["store"]
	work, thread = asking(world)
	tr.post_thread(store, thread, author_team="lang", author="ada",
	               body="push: advise", request="push.bug", on=work,
	               op_id="ask-2")
	before = (store.last_seq(), state(world, work))
	with pytest.raises(bw.WorkError):
		tr.post_thread(store, thread, author_team="lang", author="ada",
		               body="push: advise", request="push.bug",
		               on=work, wait=False, op_id="ask-2")
	assert (store.last_seq(), state(world, work)) == before, \
		"a conflicting wait= retry replayed or committed"


# -- R3: the compound transition is whole or nothing -------------------------

def test_every_injected_boundary_leaves_the_authority_byte_identical(world):
	"""The blocking form commits five things at once — message,
	obligation, wait fields, claim release, operation receipt. A partial
	commit is exactly the state W159 exists to make impossible, so every
	write boundary is faulted in turn."""
	store = world["store"]
	work, thread = asking(world)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	baseline = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	baseline_events = store.events()
	baseline_state = state(world, work)
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

	boundary, faulted = 0, 0
	while True:
		boundary += 1
		statement["n"], statement["limit"] = 0, boundary
		store.conn = ExplodingConn()
		try:
			tr.post_thread(store, thread, author_team="lang",
			               author="ada", body="push: please advise",
			               request="push.bug", on=work, op_id="ask-x")
			store.conn = real_conn
			break
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			faulted += 1
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			assert hashlib.sha256(
				open(store.path, "rb").read()).hexdigest() == baseline, \
				f"fault at write {boundary} left a partial blocking request"
			assert store.events() == baseline_events
			assert state(world, work) == baseline_state, \
				f"fault at write {boundary} moved phase, wait or claim"
			assert store.conn.execute(
				"SELECT COUNT(*) AS n FROM operations").fetchone()[
				"n"] == 0, "a crashed attempt recorded a false success"
		assert boundary < 40, "the blocking request never completed"
	assert faulted >= 3, \
		f"only {faulted} write boundaries were exercised; the compound " \
		f"transition should have several"
	# and the committed act replays across a restart
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	replay = tr.post_thread(fresh, thread, author_team="lang",
	                        author="ada", body="push: please advise",
	                        request="push.bug", on=work, op_id="ask-x")
	assert replay["operation"]["state"] == "replayed"
	fresh.close()
	after = state(world, work)
	assert after["phase"] == "waiting" and after["handler_team"] is None


def test_the_blocking_request_serializes_against_a_claim_release(world):
	"""Exactly one compatible history commits. The request needs the
	claim it is about to release, so a release that wins first must make
	the request refuse — never strand a waiter on a claim nobody held."""
	store = world["store"]
	work, thread = asking(world)
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="stepping away")
	before = store.last_seq()
	with pytest.raises(bw.WorkError, match="unclaimed"):
		tr.post_thread(store, thread, author_team="lang", author="ada",
		               body="push: advise", request="push.bug", on=work)
	assert store.last_seq() == before
	assert state(world, work)["phase"] != "waiting", \
		"a refused blocking request stranded the Work in waiting"


def test_only_one_resolution_wakes_the_waiter(world):
	"""Competing response/dispose against one obligation: the first
	commits, the rest refuse, and the waiter wakes exactly once."""
	store = world["store"]
	work, thread = asking(world)
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: advise",
	                        request="push.bug", on=work)
	tr.respond_obligation(store, posted["seq"], team="push",
	                      member="sl", body="the answer")
	for second in (
			lambda: tr.respond_obligation(store, posted["seq"],
			                              team="push", member="sl",
			                              body="again"),
			lambda: tr.dispose_obligation(store, posted["seq"],
			                              team="push", member="sl",
			                              disposition="never mind")):
		with pytest.raises(bw.WorkError):
			second()
	wakes = [e for e in store.events()
	         if e["kind"] == "wake" and e["payload"]["work"] == work]
	assert len(wakes) == 1, f"the waiter woke {len(wakes)} times"
	messages = [e for e in store.events()
	            if e["kind"] == "request"
	            and e["payload"].get("work") == work]
	assert len(messages) == 1, "a duplicate request Message committed"
	episodes = {e["seq"] for e in store.events() if e["kind"] == "wake"}
	assert len(episodes) == 1


# -- R4: the user-facing surfaces ---------------------------------------------

def test_command_assistance_offers_wait_only_with_a_request(world):
	"""The shared analyzer, not a second description of the grammar."""
	from baton_work.tui.app import assist_text
	plain = assist_text("say thread=T2 body=x ")
	assert "wait=" not in plain, \
		f"assistance offered wait= without a request: {plain}"
	carrying = assist_text("say thread=T2 body=x request=push.bug ")
	assert "wait=" in carrying, \
		f"assistance hid the waiting choice: {carrying}"
	values = assist_text("say thread=T2 body=x request=push.bug wait=")
	assert "true" in values and "false" in values, values


def test_the_console_command_path_produces_the_same_facts(world):
	"""The acceptance item is that the USER-FACING mutation path agrees
	with canonical JSON, not that both happen to share a parser."""
	from baton_work.tui.app import Console
	store = world["store"]
	work, thread = asking(world)

	class Screen:
		def addnstr(self, *args):
			pass

	console = Console(store, "lang", "ada", config_path=world["config"])
	console.detail_work = work
	console.mode = "detail"
	console.command = ""
	for character in (f"say thread={thread.rsplit('-', 1)[1]} "
	                  f"body=advise request=push.bug on={work}"):
		console.handle(ord(character))
	console.handle(10)                       # Enter executes
	assert "error" not in (console.status or "").lower(), console.status
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["phase"] == "waiting"
	assert detail["handler"] is None
	assert detail["waiting_on"]["type"] == "obligation"
	# the Events journal shows the same effective choice
	entry = next(e for e in pj.work_events(store, work, newest=True,
	                                       limit=50)["events"]
	             if e["kind"] == "request")
	assert entry["payload"]["wait"] is True
	assert entry["payload"]["released_claimant"] == "lang.ada"
	assert detail["waiting_on"]["obligation"] == entry["seq"]


# -- R5: the immediate result reports which form committed -------------------

@pytest.mark.parametrize("spelling,expected", [
	(None, True), (True, True), (False, False),
])
def test_the_say_result_echoes_the_effective_choice(world, spelling,
                                                    expected):
	"""Both forms otherwise returned the same shape, so an operator had
	to read Events back to learn whether their Work was now suspended —
	inference from omission, which the acceptance boundary names
	separately from the Events evidence."""
	store = world["store"]
	work, thread = asking(world)
	result = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: advise",
	                        request="push.bug", on=work, wait=spelling)
	assert result["wait"] is expected
	# and it agrees with what actually happened
	assert (state(world, work)["phase"] == "waiting") is expected


def test_a_plain_message_invents_no_waiting_choice(world):
	"""Omission, deliberately: a message with no request has nothing to
	wait on, so the key is ABSENT rather than a misleading false."""
	store = world["store"]
	_work, thread = asking(world)
	result = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="just context")
	assert "wait" not in result, \
		f"a plain message reported a waiting choice: {result}"
	assert "work" not in result


@pytest.mark.parametrize("spelling,expected", [(None, True), (False, False)])
def test_the_replayed_result_is_identical(world, spelling, expected):
	"""A protected retry replays the STORED result, so the echoed choice
	must survive the round trip rather than being recomputed."""
	store = world["store"]
	work, thread = asking(world)
	first = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: advise",
	                       request="push.bug", on=work, wait=spelling,
	                       op_id="echo-1")
	again = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: advise",
	                       request="push.bug", on=work, wait=spelling,
	                       op_id="echo-1")
	assert again["operation"]["state"] == "replayed"
	assert again["wait"] is expected
	assert {k: v for k, v in again.items() if k != "operation"} == \
		{k: v for k, v in first.items() if k != "operation"}, \
		"the replayed result differs from the committed one"


# -- projection and evidence -------------------------------------------------

def test_json_shows_the_waiting_condition_and_the_effective_choice(world):
	store = world["store"]
	work, thread = asking(world)
	posted = tr.post_thread(store, thread, author_team="lang",
	                        author="ada", body="push: advise",
	                        request="push.bug", on=work)
	detail = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["phase"] == "waiting"
	assert detail["handler"] is None
	assert detail["waiting_on"] == {"type": "obligation",
	                                "obligation": posted["seq"]}
	entry = next(e for e in pj.work_events(store, work, newest=True,
	                                       limit=50)["events"]
	             if e["seq"] == posted["seq"])
	assert entry["payload"]["wait"] is True, \
		"the Events journal does not show the waiting choice"
	assert entry["payload"]["released_claimant"] == "lang.ada"


def test_the_grammar_advertises_the_choice(world):
	"""The acceptance boundary asks that the choice not require
	inference from omission."""
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		work_cli.main(["--help", "say"])
	text = out.getvalue() + err.getvalue()
	assert "wait=" in text
	assert "true, false" in text
	assert "default true with request=" in text
