"""W136: participant-relative readiness — the one action projection.

finding-v11-participant-readiness (first child of the messaging cutover
gate): `participant_actions` owns the wake rules — routed Work
(unclaimed wakes every resolved Route handler; the claim leaves only
the claimant, same Work action key), `@` obligations (eligible members
of the owed endpoint; identity = seq), and due verification trials
(eligible members of the Work's Current; identity includes the deadline
generation, so extension retires the alarm). `+`, plain posts, and
personal New never enter. JSON `wait` and the TUI's personal
oblig/due counters consume the same facts; the team summary stays
team-wide and separate; reads write nothing.
"""

from __future__ import annotations

import json as _json
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
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	# TWO resolved handlers (ada, bee) plus grace, a configured member
	# the route does not resolve — the eligibility contrasts every
	# rule needs. push is the cross-team counterpart.
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"],
		                      "grace": ["obs"]},
		          "kinds": ["bug"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title="w", team="lang", author="ada"):
	return tr.create_work(world["store"], team=team, kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author=author, body="b")


def actions(world, member, team="lang"):
	return pj.participant_actions(world["store"], viewer_team=team,
	                              viewer_member=member)["actions"]


def keys(world, member, team="lang"):
	return [action["action_key"] for action in actions(world, member,
	                                                   team=team)]


def work_key(world, work, member="ada", team="lang"):
	"""W49: the Work action key is an EPISODE locator, so a test that
	means "this Work's current wake" reads it from the projection
	rather than reconstructing `work:<id>`. Returns None when the Work
	is not actionable for that member."""
	for action in actions(world, member, team=team):
		# obligations and due trials also carry `work`, so the kind is
		# part of the match — an episode belongs to the Work action.
		if action["kind"] == "work" and action["work"] == work:
			return action["action_key"]
	return None


def episode(world, work, member="ada", team="lang"):
	for action in actions(world, member, team=team):
		if action["kind"] == "work" and action["work"] == work:
			return action["episode_seq"]
	return None


def test_routed_work_wakes_handlers_and_the_claim_narrows(world):
	"""Unclaimed ready routed Work wakes EVERY resolved handler under
	ONE key; the claim leaves the claimant alone and does NOT mint a
	new episode; the loser loses it; release DOES mint, restoring both
	under a fresh episode (W49); the claimant rediscovers their own
	Work after restart."""
	store = world["store"]
	work = make(world, "shared duty")["work_id"]
	born_key = work_key(world, work)
	assert born_key is not None
	assert born_key in keys(world, "ada") and born_key in keys(world, "bee")
	assert born_key not in keys(world, "grace"), \
		"an unresolved member was woken"
	assert born_key not in keys(world, "sl", team="push")
	tr.claim_work(store, work, actor_team="lang", actor="bee")
	# W49: a claim is not a handoff, so the episode must NOT move —
	# otherwise the claimant is prompted again by their own claim.
	assert work_key(world, work, member="bee") == born_key, \
		"the claim minted a new episode and would re-wake the claimant"
	assert born_key in keys(world, "bee"), "the claimant lost their wake"
	assert born_key not in keys(world, "ada"), \
		"the losing handler kept the wake"
	entry = next(action for action in actions(world, "bee")
	             if action["action_key"] == born_key)
	assert entry["claimed"] is True
	assert entry["work"] == work, \
		"the Work id must stay a structured field, not be parsed back "\
		"out of the episode locator"
	# a heartbeat is liveness, never reassignment
	tr.heartbeat(store, work, actor_team="lang", actor="bee")
	assert work_key(world, work, member="bee") == born_key, \
		"a heartbeat minted an episode"
	# restart: the claimant rediscovers their still-open Work
	fresh = bw.Authority(world["database"])
	try:
		rediscovered = pj.participant_actions(
			fresh, viewer_team="lang",
			viewer_member="bee")["actions"]
		assert born_key in [action["action_key"]
		                    for action in rediscovered]
	finally:
		fresh.close()
	tr.release_claim(store, work, actor_team="lang", actor="bee",
	                 expect="lang.bee", reason="cycling")
	# W49: release hands the Work back to the endpoint — a NEW episode,
	# so every eligible handler (the released claimant included) wakes
	# again even though the Work id never changed.
	released_key = work_key(world, work)
	assert released_key is not None and released_key != born_key, \
		"release did not mint a new assignment episode"
	assert released_key in keys(world, "ada") and \
		released_key in keys(world, "bee")
	# blocked/waiting/parked/closed leave the unclaimed wake set
	gate = make(world, "gate", team="push", author="sl")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	assert work_key(world, work) is None, "a blocked row still woke"
	tr.close_work(store, gate, actor_team="push", actor="sl",
	              rationale="done", outcome="satisfying")
	# the unblock is a false-to-true readiness flip: a new episode
	unblocked_key = work_key(world, work)
	assert unblocked_key is not None and \
		unblocked_key not in (born_key, released_key), \
		"the dependency unblock did not mint a new episode"
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	assert work_key(world, work) is None, "a parked row still woke"


def test_obligations_wake_eligible_members_and_reroute_follows(world):
	"""A pending @ wakes exactly the owed endpoint's resolved members
	under its seq identity; completion retires it; plain and + posts
	never enter the set."""
	store = world["store"]
	born = make(world, "asked", team="push", author="sl")
	asked = tr.post_thread(store, born["thread"], author_team="push",
	                       author="sl", body="lang: confirm?",
	                       request="lang.bug", wait=False, on=born["work_id"])
	key = f"obligation:{asked['seq']}"
	assert key in keys(world, "ada") and key in keys(world, "bee")
	assert key not in keys(world, "grace")
	assert key not in keys(world, "sl", team="push"), \
		"the asker woke for their own @"
	entry = next(action for action in actions(world, "ada")
	             if action["action_key"] == key)
	assert entry["flavor"] == "response"
	assert "respond" in entry["completes_by"]
	# a plain contextual post and personal New never wake anybody
	tr.post_thread(store, born["thread"], author_team="push",
	               author="sl", body="just context")
	assert keys(world, "ada").count(key) == 1
	assert all(action["kind"] != "work" or action["work"] != "plain"
	           for action in actions(world, "ada"))
	tr.respond_obligation(store, asked["seq"], team="lang",
	                      member="ada", body="confirmed")
	assert key not in keys(world, "ada") and \
		key not in keys(world, "bee"), \
		"a completed @ kept waking the team"


def test_due_trials_wake_current_handlers_per_generation(world):
	"""A due trial wakes the Work's resolved Current members under a
	generation-scoped key: extension retires the alarm and the next
	due generation is a NEW action."""
	store = world["store"]
	work = make(world, "verified")["work_id"]
	store.clock = lambda: "2026-08-16T11:00:00Z"
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="cand-A", assign=["push.bug"],
	                review_at="2026-08-16T12:00:00Z")
	store.clock = lambda: "2026-08-16T12:00:00Z"
	due = [action for action in actions(world, "ada")
	       if action["kind"] == "due_trial"]
	assert len(due) == 1
	first_key = due[0]["action_key"]
	assert first_key.endswith(":1")
	assert not any(action["kind"] == "due_trial"
	               for action in actions(world, "grace"))
	# extension retires the alarm...
	store.clock = lambda: "2026-08-16T12:30:00Z"
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at="2026-08-16T13:00:00Z")
	assert not any(action["kind"] == "due_trial"
	               for action in actions(world, "ada"))
	# ...and the later due generation is a NEW action key
	store.clock = lambda: "2026-08-16T13:00:00Z"
	due = [action for action in actions(world, "ada")
	       if action["kind"] == "due_trial"]
	assert len(due) == 1 and due[0]["action_key"] != first_key
	assert due[0]["action_key"].endswith(":2")


def test_wait_is_member_relative_and_deterministic(world):
	"""`wait` passes both identity halves: an eligible member wakes
	immediately with structured keyed actions and a snapshot token; an
	ineligible member times out quietly; the order is deterministic
	(obligations, due trials, then Work)."""
	store = world["store"]
	work = make(world, "waking")["work_id"]
	born = make(world, "asking", team="push", author="sl")
	tr.post_thread(store, born["thread"], author_team="push",
	               author="sl", body="lang: confirm?",
	               request="lang.bug", wait=False, on=born["work_id"])
	woken = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="ada",
	                           timeout_seconds=0.05)
	assert woken["timed_out"] is False
	kinds = [action["kind"] for action in woken["actionable"]]
	assert kinds == sorted(kinds, key=("obligation", "due_trial",
	                                   "work").index), \
		"the action order is not the documented deterministic one"
	assert "snapshot_seq" in woken
	quiet = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="grace",
	                           timeout_seconds=0.05)
	assert quiet == {"actionable": [], "timed_out": True,
	                 "snapshot_seq": quiet["snapshot_seq"]}


def test_the_read_creates_no_write(world):
	"""The projection and the wait are pure — authority bytes are
	identical across both."""
	import hashlib
	store = world["store"]
	make(world, "held")
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	pj.participant_actions(store, viewer_team="lang",
	                       viewer_member="ada")
	pj.wait_actionable(store, viewer_team="lang", viewer_member="ada",
	                   timeout_seconds=0.01)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before


def test_the_header_counts_are_the_viewers_not_the_teams(world):
	"""oblig/due on the header are the VIEWER'S actionable counts —
	grace shows zero while ada shows the load; the parked count stays
	the team-wide summary fact."""
	store = world["store"]
	born = make(world, "asked", team="push", author="sl")
	tr.post_thread(store, born["thread"], author_team="push",
	               author="sl", body="lang: confirm?",
	               request="lang.bug", wait=False, on=born["work_id"])
	parked = make(world, "resting")["work_id"]
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	summary = pj.team_summary(store, viewer_team="lang")

	def tabs(member):
		# W25: the personal owed count is the Inbox tab's, drawn from
		# the same participant projection. The team-wide parked fact
		# left the header by ruling and is asserted where it now
		# lives — the canonical summary — so this test still holds
		# both halves of its question.
		console = Console(store, "lang", member,
		                  config_path=world["config"])
		return console.top_tabs()

	def owed(member):
		return pj.inbox(store, viewer_team="lang",
		                viewer_member=member)["owed"]

	assert owed("ada") == 1 and owed("grace") == 0, \
		"an unresolved member's Inbox shows the team's load"
	for member in ("ada", "grace"):
		box = pj.inbox(store, viewer_team="lang", viewer_member=member)
		assert f"Inbox {box['total']}/{box['unseen']}" in tabs(member), \
			(member, tabs(member), box)
	assert summary["parked"] == 1, "the team-wide parked fact vanished"


def test_cli_wait_reaches_the_participant_projection(world):
	"""The public wait rides both identity halves through the grammar
	and returns the keyed actions."""
	import contextlib
	import io
	from baton_work import cli as work_cli
	work = make(world, "public wake")["work_id"]

	def run(viewer):
		out, err = io.StringIO(), io.StringIO()
		with contextlib.redirect_stdout(out), \
				contextlib.redirect_stderr(err):
			code = work_cli.main(["--config", world["config"],
			                      "--participant", viewer, "wait",
			                      "timeout=0.05"])
		return code, out.getvalue(), err.getvalue()

	code, out, _err = run("lang.ada")
	assert code == 0
	body = _json.loads(out)["result"]
	assert body["timed_out"] is False
	entry = next(action for action in body["actionable"]
	             if action["kind"] == "work" and action["work"] == work)
	# W49: the public surface carries the episode locator plus the
	# structured facts a consumer needs without parsing the key
	assert entry["action_key"] == \
		f"work:{work}:{entry['episode_seq']}:g{entry['config_generation']}"
	code, out, _err = run("lang.grace")
	assert code == 0
	assert _json.loads(out)["result"]["timed_out"] is True


# -- trial 2 -----------------------------------------------------------------

def test_the_projection_version_names_the_wake_contract(world):
	"""R1: the permanent wake contract is versioned — 4.3 introduced
	the participant-relative typed actions, 4.4 the threadless pass,
	and W179's direct-scope counters moved the major to 5.0 (ruled
	honest-breaking, no alias). Same-major demands succeed; a stale
	4.x demand refuses."""
	from baton_work import jsonapi
	# W5 added the fourth `poke` action kind as an additive minor, so
	# the live version moved to 11.1 while an 11.0 demand still
	# succeeds — which is what "compatible within the major" means.
	# W5: the `poke` action kind moved the MAJOR to 12. A consumer built
	# before the tolerance widening refuses an envelope carrying it, and
	# refusing is this file's documented major condition — so an 11.x
	# demand now refuses cleanly rather than reading a wake set it
	# cannot handle.
	assert jsonapi.PROJECTION_VERSION == "12.3"
	jsonapi.require_version("12.0")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("11.2")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("8.0")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("4.3")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("3.9")


def test_a_real_reroute_moves_eligibility_and_is_a_new_resolution_episode(world):
	"""R2 as superseded by W49. An ACTUAL accepted regeneration reroutes
	the endpoint: the pending @, the routed Work, and the due trial all
	move to the new handler set without rewriting history. The @ and
	trial identities are unchanged, as before.

	The WORK key deliberately changes, because endpoint eligibility is
	generation-relative: a participant removed and restored between two
	polls would otherwise stay suppressed forever under a key that never
	moved. A config acceptance is rare, and conservatively redelivering
	otherwise-unchanged actionable Work is an honest new resolution
	episode rather than a false wake. (This clause replaces the original
	"without changing their stable action keys" for Work only.)"""
	store = world["store"]
	work = make(world, "rerouted")["work_id"]
	born = make(world, "asked", team="push", author="sl")
	asked = tr.post_thread(store, born["thread"], author_team="push",
	                       author="sl", body="lang: confirm?",
	                       request="lang.bug", wait=False, on=born["work_id"])
	store.clock = lambda: "2026-08-16T11:00:00Z"
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="cand-R", assign=["push.bug"],
	                review_at="2026-08-16T12:00:00Z")
	store.clock = lambda: "2026-08-16T12:00:00Z"
	before_key = work_key(world, work)
	before_episode = episode(world, work)
	obligation_key = f"obligation:{asked['seq']}"
	before = keys(world, "ada")
	assert before_key in before and obligation_key in before
	round_key = next(k for k in before if k.startswith("trial:"))
	assert not any(k in keys(world, "grace")
	               for k in (before_key, obligation_key, round_key))
	# the REAL reroute: generation 2 resolves the route to grace alone
	document = _json.load(open(world["config"]))
	document["generation"] = 2
	document["teams"]["lang"]["roles"]["dev"] = {
		"display": "Dev", "instructions": "Own this team's work."}
	document["teams"]["lang"]["participants"]["grace"]["roles"] = \
		["dev", "obs"]
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(world["config"], "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(world["config"], actor="lang.ada")
	after_grace = keys(world, "grace")
	# unchanged identities: the @ and the trial
	for key in (obligation_key, round_key):
		assert key in after_grace, \
			f"the reroute did not carry {key} to the new handler"
	# the Work moved too, under a NEW generation-bearing episode key
	grace_key = work_key(world, work, member="grace")
	assert grace_key is not None, \
		"the reroute did not carry the Work to the new handler"
	assert grace_key != before_key, \
		"a config acceptance must be a new resolution episode"
	assert grace_key.endswith(":g2") and before_key.endswith(":g1"), \
		"the accepted configuration generation is not in the key"
	# the WORK-side episode itself is untouched: nobody passed anything
	assert episode(world, work, member="grace") == before_episode, \
		"a config acceptance minted a Work assignment episode"
	after_ada = keys(world, "ada")
	assert not any(k in after_ada
	               for k in (before_key, grace_key, obligation_key,
	                         round_key)), \
		"the old handler kept eligibility after the reroute"
	# history unwritten: the obligation row and trial generation stand
	entry = next(action for action in actions(world, "grace")
	             if action["action_key"] == obligation_key)
	assert entry["seq"] == asked["seq"]
	assert round_key.endswith(":1"), "the reroute minted a generation"


def test_the_snapshot_is_never_mixed(world, monkeypatch):
	"""R3: a claim committed BETWEEN the projection's subqueries is
	entirely invisible — the returned action set and snapshot_seq are
	wholly pre-commit; the next call is wholly post-commit."""
	store = world["store"]
	work = make(world, "raced")["work_id"]
	key = work_key(world, work)
	pre_seq = store.conn.execute(
		"SELECT MAX(seq) AS s FROM events").fetchone()["s"]
	original = pj._endpoint_struct
	fired = {"done": False}

	def interleaving(inner_store, team, kind, selected=None):
		if not fired["done"]:
			fired["done"] = True
			writer = bw.Authority(world["database"])
			try:
				tr.claim_work(writer, work, actor_team="lang",
				              actor="bee")
			finally:
				writer.close()
		return original(inner_store, team, kind, selected)

	monkeypatch.setattr(pj, "_endpoint_struct", interleaving)
	window = pj.participant_actions(store, viewer_team="lang",
	                                viewer_member="ada")
	monkeypatch.setattr(pj, "_endpoint_struct", original)
	assert fired["done"], "the interleaved writer never ran"
	assert window["snapshot_seq"] == pre_seq, \
		"the snapshot token names a mixed state"
	assert key in [action["action_key"]
	               for action in window["actions"]], \
		"the pre-commit snapshot lost the unclaimed wake"
	entry = next(action for action in window["actions"]
	             if action["action_key"] == key)
	assert entry["claimed"] is False, "the snapshot mixed two states"
	# the next read is wholly post-commit
	fresh = pj.participant_actions(store, viewer_team="lang",
	                               viewer_member="ada")
	assert key not in [action["action_key"]
	                   for action in fresh["actions"]]


def test_endpoint_resolution_is_bounded_per_snapshot(world):
	"""R4: N actions on ONE endpoint resolve it once — the endpoint
	query count does not grow with the action count."""
	store = world["store"]
	for index in range(6):
		make(world, f"same endpoint {index}")
	statements = []
	store.conn.set_trace_callback(statements.append)
	try:
		window = pj.participant_actions(store, viewer_team="lang",
		                                viewer_member="ada")
	finally:
		store.conn.set_trace_callback(None)
	assert len([a for a in window["actions"]
	            if a["kind"] == "work"]) >= 6
	kind_reads = [statement for statement in statements
	              if "FROM kinds" in statement]
	assert len(kind_reads) <= 1, \
		f"endpoint resolution grew with the actions: {len(kind_reads)}"


def test_personal_headers_on_the_real_terminal(tmp_path):
	"""R5: real PTY at comfortable AND narrow widths — the eligible
	member's header carries the personal load, the ineligible member's
	shows zero, and the team-wide parked fact is common to both."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="push", kind="bug",
	                      title="asked", origin="external-report",
	                      classification="suspected-defect",
	                      author="sl", body="b")
	tr.post_thread(store, born["thread"], author_team="push",
	               author="sl", body="lang: confirm?",
	               request="lang.bug", wait=False, on=born["work_id"])
	parked = tr.create_work(store, team="lang", kind="bug",
	                        title="resting", origin="external-report",
	                        classification="suspected-defect",
	                        author="ada", body="b")["work_id"]
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	store.close()
	for columns, lines in ((110, 32), (60, 24)):
		for viewer, oblig in (("lang.ada", 1), ("lang.grace", 0)):
			text, status, steps = ptyharness.drive(
				config, viewer, [(b"", 0.6), (b"qy", 0.4)],
				columns=columns, lines=lines)
			assert os.WIFEXITED(status) and \
				os.WEXITSTATUS(status) == 0
			header = ptyharness.replay(steps[0], columns=columns,
			                           lines=lines)[0]
			# W25: the personal count is the Inbox tab's, and the
			# team-wide parked counter is retired from the header.
			with bw.Authority(database) as store:
				box = pj.inbox(store, viewer_team="lang",
				               viewer_member=viewer.split(".")[1])
			assert box["owed"] == oblig, (viewer, box)
			assert f"Inbox {box['total']}/{box['unseen']}" in header, \
				(viewer, columns, header)
			assert "[park:" not in header, (viewer, columns, header)


def test_plus_and_new_are_attention_not_wakeups(world):
	"""R6: an ACTUAL `+` include and an isolated personal-New message
	exist, stay visible through their attention surfaces, and never
	enter the action set."""
	store = world["store"]
	born = make(world, "context", team="push", author="sl")
	work, thread = born["work_id"], born["thread"]
	# a real + fan-out naming ada, and a plain post creating New
	tr.post_thread(store, thread, author_team="push", author="sl",
	               body="fyi lang", include="lang.*")
	tr.post_thread(store, thread, author_team="push", author="sl",
	               body="just news")
	view = pj.thread(store, thread, viewer_team="lang",
	                 viewer_member="ada")
	assert view["new"] > 0, "the attention surface lost the messages"
	mine = actions(world, "ada")
	assert all(action["kind"] == "work" or
	           action.get("work") != work for action in mine), \
		"a + or plain message entered the action set"
	assert not any(action["kind"] == "obligation"
	               for action in mine), \
		"attention manufactured an obligation"
	# and the wait stays quiet for a member with only attention
	quiet = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="grace",
	                           timeout_seconds=0.05)
	assert quiet["timed_out"] is True
