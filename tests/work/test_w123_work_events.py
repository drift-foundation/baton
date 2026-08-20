"""W123 (finding-work-events-tab): the Work Events play-by-play.

The global `events` read is not Work-relative, does not say WHY an event
belongs to a Work, and has no claim intervals. `work-events work=WORK`
supplies all three over the SAME immutable ledger — no schema change.

Association is an EXPLICIT per-kind contract. That matters: a heuristic
"does this payload contain a Work-shaped string" would manufacture
events on any Work whose id happens to be quoted in someone's rationale.
"""

from __future__ import annotations

import curses
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


class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		# W110: the attribute is recorded because the ACTIVE tab is now
		# distinguished by weight rather than by brackets — brackets
		# say "this is a tab" at both view levels.
		self.calls.append((y, x, str(text),
		                   rest[1] if len(rest) > 1 else 0))

	def lines(self):
		return [text for _y, _x, text, _attr in self.calls]

	def attr_of(self, label):
		return next((attr for _y, _x, text, attr in self.calls
		             if text == label), None)


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl", "rview"],
		                      "bee": ["impl", "rview"]},
		          "kinds": ["bug"]},
		 # a real second team: the accept flow needs a cross-team
		 # provider, which is the convergence model the finding names
		 "push": {"members": {"sl": ["impl"]}, "kinds": ["bug"]}})
	lang = document["teams"]["lang"]
	lang["routes"] = {"build": {"role": "impl", "handlers": ["ada", "bee"]},
	                  "review": {"role": "rview", "handlers": ["ada"]}}
	lang["kinds"] = {"bug": {"display": "Bug", "route": "build"},
	                 "rev": {"display": "Rev", "route": "review"}}
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "store": store}
	store.close()


def make(world, title="subject", **kw):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b", **kw)


def kinds(page):
	return [entry["kind"] for entry in page["events"]]


def read(world, work, **kw):
	kw.setdefault("newest", True)
	kw.setdefault("limit", 100)
	return pj.work_events(world["store"], work, **kw)


# -- the association matrix --------------------------------------------------

def test_the_subject_matrix_attaches_by_typed_contract(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	tr.classify(store, work, actor_team="lang", actor="ada",
	            classification="confirmed-defect")
	tr.prioritize(store, work, actor_team="lang", actor="ada",
	              priority="high")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="w38")
	page = read(world, work)
	assert kinds(page) == ["create_work", "claim", "heartbeat",
	                       "classify", "prioritize", "set_phase"]
	assert all(entry["roles"] == ["subject"] for entry in page["events"])
	# creation joins on the Work's own created_seq — the created id is
	# the act's RESULT, never one of its inputs
	assert page["events"][0]["seq"] == born["seq"]


def test_pure_discussion_and_seen_movement_stay_out(world):
	"""Conversation and personal cursor movement stay in Messages.

	The behavioural half of this is NOT sufficient on its own and the
	structural half is not redundant: a plain post and a seen mark both
	record `payload.work = None`, so the association predicate would
	exclude them even if the kinds were wrongly listed as Work events.
	Asserting the exclusion list directly is what actually holds the
	line — verified by removing it, which reds this test."""
	from baton_work.projection import _EVENT_SUBJECT_KINDS
	for kind in ("post_message", "mark_seen", "create_thread",
	             "accept_config"):
		assert kind not in _EVENT_SUBJECT_KINDS, \
			f"{kind} was admitted to the operational journal"
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="just talking")
	tr.seen_thread(store, born["thread"], team="lang", member="ada",
	               up_to_seq=born["seq"])
	page = read(world, work)
	assert "post_message" not in kinds(page), \
		"conversation flooded the operational journal"
	assert "mark_seen" not in kinds(page), \
		"a personal cursor movement became a Work event"


def test_workflow_bearing_message_acts_stay_in_without_bodies(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	asked = tr.post_thread(store, born["thread"], author_team="lang",
	                       author="ada", body="lang: confirm this?",
	                       request="lang.rev", wait=False, on=work)
	tr.respond_obligation(store, asked["seq"], team="lang",
	                      member="ada", body="confirmed, proceeding")
	page = read(world, work)
	assert "request" in kinds(page) and "respond" in kinds(page)
	blob = _json.dumps(page)
	assert "confirm this?" not in blob and "proceeding" not in blob, \
		"an event duplicated a message body"


def test_a_dependency_appears_in_both_works_with_direction(world):
	"""ONE authoritative event, read from both ends with opposite roles
	— the finding's 'storage is not duplicated'."""
	store = world["store"]
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada", rationale="needs it first")
	tr.remove_dependency(store, consumer, blocker, actor_team="lang",
	                     actor="ada", rationale="added by mistake")
	from_consumer = [e for e in read(world, consumer)["events"]
	                 if e["kind"].endswith("dependency")]
	from_blocker = [e for e in read(world, blocker)["events"]
	                if e["kind"].endswith("dependency")]
	assert [e["seq"] for e in from_consumer] == \
		[e["seq"] for e in from_blocker], \
		"the two Works saw different events for one act"
	assert [e["roles"] for e in from_consumer] == \
		[["consumer"], ["consumer"]]
	assert [e["roles"] for e in from_blocker] == \
		[["blocker"], ["blocker"]]
	assert from_consumer[0]["related"] == \
		[{"work": blocker, "role": "blocker"}]
	assert from_blocker[0]["related"] == \
		[{"work": consumer, "role": "consumer"}]
	# the rationale that makes the correction reviewable travels with it
	assert from_blocker[1]["payload"]["rationale"] == "added by mistake"


def test_creation_names_its_parent_and_predecessor(world):
	store = world["store"]
	parent = make(world, "parent")["work_id"]
	child = make(world, "child", parent=parent)["work_id"]
	from_child = read(world, child)["events"][0]
	assert from_child["related"] == [{"work": parent, "role": "parent"}]
	from_parent = [e for e in read(world, parent)["events"]
	               if e["kind"] == "create_work"]
	# the parent sees the child's creation, in its parent role
	assert any("parent" in e["roles"] for e in from_parent), \
		[e["roles"] for e in from_parent]


def test_association_is_typed_not_a_string_search(world):
	"""A rationale that merely QUOTES another Work's id must not
	manufacture an event on that Work."""
	store = world["store"]
	subject = make(world, "subject")["work_id"]
	bystander = make(world, "bystander")["work_id"]
	tr.claim_work(store, subject, actor_team="lang", actor="ada")
	tr.release_claim(store, subject, actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 reason=f"handing back, see {bystander} for context")
	seqs = [e["seq"] for e in read(world, bystander)["events"]]
	release = [e for e in read(world, subject)["events"]
	           if e["kind"] == "release"]
	assert release, "the release did not attach to its own Work"
	assert release[0]["seq"] not in seqs, \
		"a quoted id manufactured an event on an unrelated Work"


# -- round one: the reverse and terminal relations ---------------------------

def test_a_parent_sees_which_child_was_born(world):
	"""W123 R1. The created id is the act's RESULT, so a parent reading
	its child's birth has to be TOLD which child — resolved through the
	typed creation relation (the Work row whose `created_seq` is this
	event), never a guessed payload key."""
	parent = make(world, "parent")["work_id"]
	child = make(world, "child", parent=parent)["work_id"]
	entry = next(e for e in read(world, parent)["events"]
	             if e["kind"] == "create_work" and "parent" in e["roles"])
	assert entry["related"] == [{"work": child, "role": "subject"}]
	# and the child's own view still reads the other direction
	from_child = read(world, child)["events"][0]
	assert from_child["roles"] == ["subject"]
	assert from_child["related"] == [{"work": parent, "role": "parent"}]


def test_a_predecessor_sees_which_follow_up_was_born(world):
	store = world["store"]
	first = make(world, "the original")["work_id"]
	tr.close_work(store, first, actor_team="lang", actor="ada",
	              rationale="superseded", outcome="satisfying")
	later = tr.create_work(store, team="lang", kind="bug",
	                       title="the follow-up",
	                       origin="external-report",
	                       classification="suspected-defect",
	                       author="ada", body="b",
	                       follow_up_of=first)["work_id"]
	entry = next(e for e in read(world, first)["events"]
	             if e["kind"] == "create_work"
	             and "predecessor" in e["roles"])
	assert entry["related"] == [{"work": later, "role": "subject"}]


def test_the_survivor_sees_which_work_was_closed_as_its_duplicate(world):
	"""W123 R2. Without this the canonical survivor's journal never
	mentioned the act that named it."""
	store = world["store"]
	survivor = make(world, "survivor")["work_id"]
	duplicate = make(world, "duplicate")["work_id"]
	closed = tr.close_work(store, duplicate, actor_team="lang",
	                       actor="ada", rationale="same as the survivor",
	                       outcome="rejected", duplicate_of=survivor)
	entry = next((e for e in read(world, survivor)["events"]
	              if e["seq"] == closed["seq"]), None)
	assert entry is not None, \
		"the survivor cannot see the Work rejected as its duplicate"
	assert "duplicate_target" in entry["roles"]
	# direction: the survivor is told WHICH Work was the duplicate
	assert entry["related"] == [{"work": duplicate, "role": "duplicate"}]
	# the closed Work still reads it as its own terminal disposition
	from_dupe = next(e for e in read(world, duplicate)["events"]
	                 if e["seq"] == closed["seq"])
	assert from_dupe["roles"] == ["subject"]
	assert from_dupe["payload"]["outcome"] == "rejected"
	# and the other direction names the survivor it was folded into
	assert from_dupe["related"] == \
		[{"work": survivor, "role": "duplicate_target"}]


def test_an_accept_created_provider_reaches_its_parent(world):
	"""W123 R4. The parent link lives on the provider's Work ROW, not in
	the accept payload, so it is resolved as a typed relation."""
	store = world["store"]
	consumer = make(world, "consumer")["work_id"]
	parent = tr.create_work(store, team="push", kind="bug",
	                        title="provider parent",
	                        origin="external-report",
	                        classification="suspected-defect",
	                        author="sl", body="b")["work_id"]
	thread = pj.work_threads(store, consumer, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	asked = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: please provide",
	                       request="push.bug", wait=False, on=consumer)
	accepted = tr.accept_obligation(
		store, asked["seq"], actor_team="push", actor="sl",
		body="creating the provider",
		create={"kind": "bug", "title": "the provider",
		        "classification": "suspected-defect", "parent": parent})
	provider = accepted["provider"]
	entry = next((e for e in read(world, parent)["events"]
	              if e["seq"] == accepted["seq"]), None)
	assert entry is not None, \
		"the parent never saw its provider being accepted into being"
	assert "parent" in entry["roles"]
	assert {"work": provider, "role": "provider"} in entry["related"]
	# the consumer still reads the same authoritative event its own way
	from_consumer = next(e for e in read(world, consumer)["events"]
	                     if e["seq"] == accepted["seq"])
	assert from_consumer["roles"] == ["consumer"]


def test_accepting_into_an_existing_provider_fabricates_no_parent(world):
	"""The negative half of R4: `into=` creates nothing, so no parent
	relation may be invented."""
	store = world["store"]
	consumer = make(world, "consumer")["work_id"]
	parent = tr.create_work(store, team="push", kind="bug",
	                        title="an unrelated parent",
	                        origin="external-report",
	                        classification="suspected-defect",
	                        author="sl", body="b")["work_id"]
	existing = tr.create_work(store, team="push", kind="bug",
	                          title="the existing provider",
	                          origin="external-report",
	                          classification="suspected-defect",
	                          author="sl", body="b",
	                          parent=parent)["work_id"]
	thread = pj.work_threads(store, consumer, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	asked = tr.post_thread(store, thread, author_team="lang",
	                       author="ada", body="push: please provide",
	                       request="push.bug", wait=False, on=consumer)
	accepted = tr.accept_obligation(
		store, asked["seq"], actor_team="push", actor="sl",
		body="the existing one already covers it", into=existing)
	assert any(e["seq"] == accepted["seq"]
	           for e in read(world, existing)["events"]), \
		"the accepted provider did not see its own acceptance"
	assert not any(e["seq"] == accepted["seq"]
	               for e in read(world, parent)["events"]), \
		"accepting into an EXISTING provider invented a parent relation"


def test_an_open_claim_carries_its_ongoing_duration(world):
	"""W123 R3. `started_at` stays fixed and heartbeats change nothing;
	the duration grows because time passed, not because anything was
	recorded."""
	store = world["store"]
	work = make(world, "held")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	interval = next(e["claim_interval"] for e in read(world, work)["events"]
	                if e["kind"] == "claim")
	assert interval["end_seq"] is None, "the claim is not open"
	assert isinstance(interval["elapsed_seconds"], int)
	assert interval["elapsed_seconds"] >= 0, \
		"an open claim reports no ongoing Held duration"
	started, first = interval["started_at"], interval["elapsed_seconds"]

	# a heartbeat neither restarts the interval nor invents work time
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	after = next(e["claim_interval"] for e in read(world, work)["events"]
	             if e["kind"] == "claim")
	assert after["started_at"] == started, "a heartbeat moved the start"
	assert after["claim_seq"] == interval["claim_seq"]
	assert after["end_seq"] is None
	assert after["elapsed_seconds"] >= first

	# the clock advancing is what moves it
	store.clock = lambda: "2099-01-01T00:00:00Z"
	later = next(e["claim_interval"] for e in read(world, work)["events"]
	             if e["kind"] == "claim")
	assert later["elapsed_seconds"] > first, \
		"the ongoing duration does not follow the read's instant"
	assert later["started_at"] == started


# -- claim intervals ---------------------------------------------------------

def test_a_completed_claim_interval_rides_both_boundaries(world):
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="cycling")
	events = {e["kind"]: e for e in read(world, work)["events"]}
	start = events["claim"]["claim_interval"]
	end = events["release"]["claim_interval"]
	assert start == end, \
		"the same interval facts are not reachable from both ends"
	assert start["claimant"] == "lang.ada"
	assert start["end_kind"] == "release"
	assert start["elapsed_seconds"] is not None
	# the heartbeat sits INSIDE the interval and starts nothing
	assert "claim_interval" not in events["heartbeat"] or \
		events["heartbeat"].get("claim_interval") is None


def test_a_heartbeat_never_restarts_or_extends_the_interval(world):
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	claim_seq = [e["seq"] for e in read(world, work)["events"]
	             if e["kind"] == "claim"][0]
	for _ in range(3):
		tr.heartbeat(store, work, actor_team="lang", actor="ada")
	page = read(world, work)
	intervals = [e["claim_interval"] for e in page["events"]
	             if e.get("claim_interval")]
	assert len({i["claim_seq"] for i in intervals}) == 1, \
		"a heartbeat opened a second interval"
	assert intervals[0]["claim_seq"] == claim_seq
	assert intervals[0]["end_seq"] is None, "an open claim was closed"


def test_a_pass_and_a_close_each_end_the_interval(world):
	store = world["store"]
	passed = make(world, "passed")["work_id"]
	tr.claim_work(store, passed, actor_team="lang", actor="ada")
	tr.pass_work(store, passed, actor_team="lang", actor="ada",
	             to="lang.rev", comment="over")
	interval = next(e["claim_interval"] for e in read(world, passed)["events"]
	                if e["kind"] == "claim")
	assert interval["end_kind"] in ("pass", "return")

	closed = make(world, "closed")["work_id"]
	tr.claim_work(store, closed, actor_team="lang", actor="ada")
	tr.close_work(store, closed, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	interval = next(e["claim_interval"] for e in read(world, closed)["events"]
	                if e["kind"] == "claim")
	assert interval["end_kind"] == "close_work"


def test_parking_and_waiting_both_end_the_interval(world):
	"""Entry into either non-executing phase ends the work-time
	interval: the claim is released, so the elapsed time stops."""
	store = world["store"]
	parked = make(world, "parked")["work_id"]
	tr.claim_work(store, parked, actor_team="lang", actor="ada")
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	interval = next(e["claim_interval"]
	                for e in read(world, parked)["events"]
	                if e["kind"] == "claim")
	assert interval["end_kind"] == "set_phase", \
		"parking did not end the work-time interval"

	born = make(world, "block")
	waiting = born["work_id"]
	asked = tr.post_thread(store, born["thread"], author_team="lang",
	                       author="ada", body="blocking question",
	                       request="lang.rev", wait=False, on=waiting)
	tr.claim_work(store, waiting, actor_team="lang", actor="ada")
	tr.set_phase(store, waiting, actor_team="lang", actor="ada",
	             phase="block", wait=asked["seq"])
	interval = next(e["claim_interval"]
	                for e in read(world, waiting)["events"]
	                if e["kind"] == "claim")
	assert interval["end_kind"] == "set_phase", \
		"entering waiting did not end the work-time interval"
	assert interval["elapsed_seconds"] is not None


def test_an_invalidating_gate_ends_the_interval(world):
	"""A late-arriving blocker releases the claimant (recorded typed in
	`released_claims`), so the interval ends there rather than running
	on through time nobody was working."""
	store = world["store"]
	work = make(world, "gated")["work_id"]
	blocker = make(world, "late gate")["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.add_dependency(store, work, blocker, actor_team="lang",
	                  actor="ada", rationale="arrived later")
	interval = next(e["claim_interval"]
	                for e in read(world, work)["events"]
	                if e["kind"] == "claim")
	assert interval["end_seq"] is not None, \
		"an invalidating gate left the work-time interval open"
	assert interval["end_kind"] == "add_dependency"


# -- pagination (the W76 contract, reused) -----------------------------------

def test_pagination_is_bounded_in_both_directions_with_a_proof_row(world):
	store = world["store"]
	work = make(world)["work_id"]
	for _ in range(9):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="cycling")
	total = len(read(world, work)["events"])
	assert total == 19, total
	page = read(world, work, limit=5)
	assert len(page["events"]) == 5
	assert page["next_before"] is not None
	visited = list(page["events"])
	while page["next_before"] is not None:
		page = read(world, work, newest=False,
		            before=page["next_before"], limit=5)
		assert page["events"], "an older cursor opened an EMPTY page"
		visited = list(page["events"]) + visited
	assert [e["seq"] for e in visited] == \
		sorted(e["seq"] for e in visited)
	assert len(visited) == total, "the walk lost or repeated events"


def test_an_exactly_full_page_does_not_invent_a_continuation(world):
	work = make(world)["work_id"]
	page = read(world, work, limit=1)
	assert len(page["events"]) == 1
	assert page["next_before"] is None, \
		"an exact-limit page advertised an empty older continuation"


def test_the_json_page_is_canonical_ascending(world):
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	page = read(world, work)
	seqs = [e["seq"] for e in page["events"]]
	assert seqs == sorted(seqs), "the JSON page left ascending order"


# -- the TUI tabs ------------------------------------------------------------

def console_at(world, height=24, width=100):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.detail_work = console.rows()[0]["id"]
	console.mode = "detail"
	console._render_detail(Screen(), height, width)
	return console


def painted(console, height=24, width=100):
	screen = Screen()
	console._render_detail(screen, height, width)
	return screen.lines()


def test_the_tab_bar_is_always_visible_and_messages_is_default(world):
	make(world)
	console = console_at(world)
	assert console.detail_tab == "messages"
	screen = Screen()
	console._render_detail(screen, 24, 100)
	lines = screen.lines()
	# W110: BOTH tabs are bracketed — the brackets identify a tab, at
	# this level and at the top level alike — and the active one is
	# highlighted instead.
	assert "[Messages]" in lines and "[Events]" in lines, lines
	assert screen.attr_of("[Messages]") & curses.A_REVERSE, \
		"the active tab is not distinguished"
	assert not screen.attr_of("[Events]") & curses.A_REVERSE, \
		"the inactive tab was highlighted too"
	assert any("[/] tabs" in line for line in lines), \
		"the footer does not advertise tab navigation"


@pytest.mark.parametrize("key,expected", [
	(ord("]"), "events"),
	(ord("["), "events"),
])
def test_both_bracket_keys_reach_events_from_messages(world, key,
                                                      expected):
	make(world)
	console = console_at(world)
	console.handle(key)
	assert console.detail_tab == expected
	screen = Screen()
	console._render_detail(screen, 24, 100)
	assert "[Events]" in screen.lines() and "[Messages]" in screen.lines()
	assert screen.attr_of("[Events]") & curses.A_REVERSE
	assert not screen.attr_of("[Messages]") & curses.A_REVERSE


def test_tab_switching_works_from_every_pane(world):
	make(world)
	console = console_at(world)
	for pane in ("threads", "index", "reader"):
		console.detail_tab = "messages"
		console.focus = pane
		console.handle(ord("]"))
		assert console.detail_tab == "events", \
			f"] did not switch from the {pane} pane"


def test_each_tab_preserves_its_own_state(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	for index in range(6):
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body=f"message {index}")
	for _ in range(4):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="cycling")
	console = console_at(world)
	console.focus = "reader"
	console.handle(ord("j"))            # move the Messages selection
	painted(console)
	messages_pane, messages_pick = console.focus, console.msg_cursor

	console.handle(ord("]"))
	painted(console)
	console.event_focus = "index"
	console.handle(ord("j"))            # move the Events selection
	painted(console)
	events_pane, events_pick = console.event_focus, console.event_cursor

	console.handle(ord("["))            # back to Messages
	painted(console)
	assert console.focus == messages_pane, "Messages lost its pane focus"
	assert console.msg_cursor == messages_pick, \
		"Messages lost its selection"
	console.handle(ord("]"))            # and back to Events
	painted(console)
	assert console.event_focus == events_pane, "Events lost its pane focus"
	assert console.event_cursor == events_pick, \
		"Events lost its selection"


def test_ctrl_w_stays_pane_local_to_the_active_tab(world):
	make(world)
	console = console_at(world)
	console.handle(ord("]"))
	painted(console)
	before_messages_focus = console.focus
	console.handle(23)
	console.handle(ord("j"))
	assert console.event_focus == "reader"
	assert console.focus == before_messages_focus, \
		"Ctrl-W in Events moved the Messages tab's focus"
	console.handle(23)
	console.handle(ord("k"))
	assert console.event_focus == "index"


def test_events_ctrl_w_accepts_cursor_keys_too(world):
	"""Events has the same cursor/vi pane contract as Messages."""
	make(world)
	console = console_at(world)
	console.handle(ord("]"))
	painted(console)
	console.handle(23)
	console.handle(curses.KEY_RIGHT)
	assert console.event_focus == "reader"
	console.handle(23)
	console.handle(curses.KEY_LEFT)
	assert console.event_focus == "index"


def test_events_open_newest_first_with_stable_identifiers(world):
	store = world["store"]
	work = make(world)["work_id"]
	for _ in range(3):
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="cycling")
	console = console_at(world)
	console.handle(ord("]"))
	lines = painted(console)
	rows = [line.split()[0] for line in lines
	        if line.startswith("E") and line[1:2].isdigit()]
	assert rows, "no event rows painted"
	numbers = [int(label[1:]) for label in rows]
	assert numbers == sorted(numbers, reverse=True), \
		f"the Events index is not newest-first: {rows}"
	assert console.event_cursor == max(numbers)


def test_the_reader_shows_roles_related_and_the_whole_payload(world):
	store = world["store"]
	consumer = make(world, "consumer")["work_id"]
	blocker = make(world, "blocker")["work_id"]
	tr.add_dependency(store, consumer, blocker, actor_team="lang",
	                  actor="ada",
	                  rationale="the reviewed prerequisite")
	console = Console(store, "lang", "ada", config_path=world["config"])
	console.detail_work = consumer
	console.mode = "detail"
	console.detail_tab = "events"
	lines = painted(console)
	flat = "\n".join(lines)
	# W1217 (finding-event-relation-display) renamed this row and
	# retired the redundant one. `consumer` is a MEANINGFUL relation —
	# it says why an Event about the blocker appears in the consumer's
	# history — and W123's point was always that the typed
	# relationship is readable, not that it was spelled `roles:`.
	assert "relation: consumer" in flat, flat[-400:]
	assert f"related: {blocker} (blocker)" in flat
	assert "the reviewed prerequisite" in flat, \
		"the rationale is not readable in the Events reader"
	assert "payload:" in flat, "the complete payload is not exposed"


def test_events_navigation_writes_nothing(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	before_seq = store.last_seq()
	before_new = pj.thread(store, born["thread"], viewer_team="lang",
	                       viewer_member="ada")["new"]
	console = console_at(world)
	for key in (ord("]"), ord("j"), ord("k"), ord("n"), ord("p"),
	            23, ord("j"), ord("j"), ord("["), ord("]")):
		console.handle(key)
		painted(console)
	assert store.last_seq() == before_seq, \
		"browsing Events wrote to the authority"
	assert pj.thread(store, born["thread"], viewer_team="lang",
	                 viewer_member="ada")["new"] == before_new, \
		"browsing Events advanced a seen cursor"


def test_conversational_counts_are_untouched_by_events(world):
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	before = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.prioritize(store, work, actor_team="lang", actor="ada",
	              priority="high")
	after = pj.detail(store, work, viewer_team="lang",
	                  viewer_member="ada")
	for field in ("message_count", "new", "thread_count"):
		assert after[field] == before[field], \
			f"workflow transitions inflated the conversational {field}"


def test_the_narrow_layout_keeps_both_event_panes(world):
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	console = console_at(world)
	console.handle(ord("]"))
	lines = painted(console, height=24, width=44)
	assert any(line.lstrip().startswith("Events (") or
	           line.lstrip().startswith("»Events (") for line in lines), \
		"the narrow Events index heading is missing"
	assert any("Event E" in line for line in lines), \
		"the narrow Events reader heading is missing"
