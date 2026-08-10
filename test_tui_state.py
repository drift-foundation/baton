"""Screen-model tests: the interaction, without a terminal.

The state model is a pure function of previous state plus one keystroke, so
the safety properties are checkable here. The most important of them -- THE
POLL never claims, and a broadcast is never consumed by being looked at -- is
asserted by COUNTING rows in the authority, not by inspecting what the model
returned.

Selection is deliberately NOT in that list any more: highlighting an inbound
directed message claims and opens it (FINDING §16). "Observation never claims"
was the property when selection counted as observation; it does not now, and
naming it that way here would be a test file asserting the opposite of the
code it tests.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core
from baton_tui import REQUIRES_CORE_API, check_core_compatibility
from baton_tui.state import (MODE_BROWSE, MODE_COMPOSE, MODE_REPLY, MODE_NOTICE,
                             InboxState)


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	root = home / "root"
	root.mkdir()
	(root / "EVIDENCE.md").write_bytes(b"pinned evidence\n")
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 9, "generation": 1,
			"mailbox": {"name": "console"},
			"participants": {"acme.reviewer": {}, "acme.implementer": {},
			                 "hq.lead": {"capabilities": ["recovery", "config"]}},
			"roots": {"src": str(root)}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path, root


@pytest.fixture
def env(tmp_path):
	path, root = _instance(tmp_path)
	with core.open_instance(path) as store:
		yield store, root


def _counts(store):
	return (store.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0],
	        store.conn.execute("SELECT COUNT(*) FROM notice_seen").fetchone()[0])


# -- the property the whole design exists for ------------------------------

def test_browsing_claims_directed_rows_but_never_a_broadcast(env):
	"""SUPERSEDED and replaced. This asserted that browsing the whole inbox
	produced zero claims and zero receipts, and that nothing content-bearing
	ever reached the pane -- the OBSERVE/COMMIT split the console was built
	around.

	Slawomir reversed it for DIRECTED messages: highlighting one claims and
	opens it, because scrolling to a row and then pressing Enter is one
	ceremony too many. The accepted consequence is exactly what this test now
	pins -- moving across pending rows accumulates unresolved claims.

	What did NOT change is the half that still matters: a BROADCAST is never
	consumed by looking at it. Zero notice receipts, however much browsing
	happens, and repeated passes claim nothing new because the rows are
	already claimed by this participant."""
	store, _ = env
	for i in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Question {i}", body=b"body\n")
	store.send_notice("hq.lead", kind="announcement", subject="All hands", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert len(state.rows) == 5
	for _ in range(6):
		for _ in range(len(state.rows)):
			state.move(1, store)
		for _ in range(len(state.rows)):
			state.move(-1, store)
		state.refresh(store)
	claims, receipts = _counts(store)
	assert receipts == 0, "looking at a broadcast consumed it"
	# One claim per DIRECTED row, and not one more however many passes: a
	# row already claimed by us is REOPENED, never claimed again.
	assert claims == 4, f"expected one claim per directed row, got {claims}"
	assert state.unresolved_count() == 4


def test_preview_shows_shape_but_never_content(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Shaped",
	           parts=[{"content_type": "text/markdown; charset=utf-8", "body": b"# secret\n"},
	                  {"content_type": "text/markdown; charset=utf-8",
	                   "disposition": "attachment", "attach": "src:EVIDENCE.md"}])
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	preview = state.detail["preview"]
	assert preview["subject"] == "Shaped"
	assert [p["storage"] for p in preview["parts"]] == ["inline", "external"]
	blob = json.dumps(preview)
	assert "secret" not in blob and "base64" not in blob


# -- selecting a directed row takes ownership of THAT row -------------------

def test_selection_claims_exactly_the_row_landed_on_not_the_oldest(env):
	"""Authority delivery is FIFO; human selection is not restricted by it.
	Whatever row the human lands on is what gets claimed -- `wait` could only
	ever have taken the oldest pending message, and MESSAGES is presented
	newest-first, so the head of the list is not even that one.

	**This pin had gone vacuous** and review caught it. It moved the cursor
	and THEN called `open_selected`, asserting the claim afterwards -- but the
	move now does the claiming, so the `open_selected` call proved nothing
	while the name still said it did. It brackets the selection transition
	itself now."""
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Q{i}", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_row(store)                       # the head, deliberately
	head = state.selected["id"]
	before = {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()}
	assert before == {head}

	state.move(2, store)                          # the transition under test
	chosen = state.selected
	assert chosen["id"] != head, "the fixture did not move"
	after = {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()}
	# EXACTLY the row landed on was added -- not the one passed over, and not
	# the oldest.
	assert after - before == {chosen["id"]}, f"selection claimed {after - before}"
	assert state.detail["delivery"]["message"]["subject"] == chosen["subject"]
	assert state.opened["id"] == chosen["id"]

	# And a subsequent Enter on the open row does NOT claim again: it is a
	# reopen at most, which is why it stops being advertised.
	state.open_selected(store)
	assert {r[0] for r in store.conn.execute(
		"SELECT message_id FROM claims").fetchall()} == after
	assert state.unresolved_count() == 2


def test_opening_loads_content_only_after_claiming(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"# real content\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	assert "delivery" not in state.detail
	assert _counts(store) == (0, 0)
	state.open_selected(store)
	body = state.detail["delivery"]["message"]["content"]["parts"][0]["text"]
	assert body == "# real content\n"
	assert _counts(store)[0] == 1
	assert "owed" in state.status


def test_claimed_row_reopens_without_a_second_claim(env):
	"""Restart with an active claim: the console must recover the readable
	delivery, and must not claim again to do it."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Held", body=b"x\n")
	first = InboxState("acme.implementer")
	first.refresh(store)
	first.open_selected(store)
	before = _counts(store)
	# A brand-new state object: nothing carried in memory.
	second = InboxState("acme.implementer")
	second.refresh(store)
	second.preview(store)
	assert second.selected["state"] == "claimed"
	second.open_selected(store)
	assert second.detail["delivery"]["message"]["subject"] == "Held"
	assert _counts(store) == before
	assert second.unresolved_count() == 1


def test_notice_opens_once_and_is_not_redelivered(env):
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Once", body=b"body\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	assert _counts(store)[1] == 0
	state.open_selected(store)
	# Through the delivery envelope now, so the renderer can actually show it:
	# the raw rows carry `body` bytes and the renderer speaks `text`, which is
	# why every notice used to draw as "(no retained bytes)".
	assert state.detail["notice"]["content"]["parts"][0]["text"] == "body\n"
	assert _counts(store)[1] == 1
	# It STAYS in the list as history, with its state changed to seen.
	#
	# SUPERSEDED, recorded so it is not resurrected: this asserted
	# `all(r["row_type"] != "notice" ...)` -- that the row disappeared. It was
	# the unseen-queue behaviour, and Slawomir rejected it from the live
	# console: a human watched an announcement vanish while reading it. The
	# property that survives is the one that matters -- exactly one receipt,
	# and no redelivery.
	state.refresh(store)
	kept = [r for r in state.rows if r["row_type"] == "notice"]
	assert len(kept) == 1 and kept[0]["state"] == "seen"
	assert _counts(store)[1] == 1, "a second receipt was written"


# -- inline reply ----------------------------------------------------------

def test_a_quick_reply_edits_the_subject_line_and_sends_it_as_the_content(env):
	"""The quick path: `r`, edit one line, send. The subject line IS the
	reply, through the same subject-only shorthand compose uses.

	SUPERSEDED MODEL, recorded so it is not resurrected: this test used to
	set `state.draft` as an inline BODY and assert the subject was inherited
	unchanged. There is no inline body editor any more -- printable text never
	accumulates in a body buffer -- and the subject convention is now a
	single `Re: ` prefix."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Needs an ack", body=b"?\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert state.begin_reply() is True
	assert state.mode == MODE_REPLY
	# Seeded, and the caret edits THIS line.
	assert state.draft == "Needs an ack"
	state.draft = "Needs an ack — still working, give me more time"
	result = state.send_reply(store)
	assert result["already_committed"] is False
	assert state.mode == MODE_BROWSE
	response = store.get_message(result["response_message_id"])
	assert response["subject"] == "Needs an ack — still working, give me more time"
	assert response["parts"][0]["content_type"] == "text/markdown; charset=utf-8"
	# The same words as the content part -- never a zero-byte placeholder.
	assert response["parts"][0]["body"] == (
		b"Needs an ack \xe2\x80\x94 still working, give me more time")
	assert state.unresolved_count() == 0


def test_the_reply_subject_is_preserved_exactly(env):
	"""Slawomir's ruling: NO automatic prefix, ever. `R` in SENT already
	exposes replied state and `responds_to`/`thread_id` carry the actual
	relationship, so a `Re:` would be decorative redundancy -- and subject
	churn in a long thread, where the same words drift by one prefix per hop.

	SUPERSEDED, recorded so it is not resurrected: an earlier rule seeded
	`Re: ` exactly once, case-insensitively, and this test asserted that. The
	semantic assertion it existed for -- that a thread's subject does not
	accumulate noise -- is unchanged and now absolute."""
	store, _ = env
	for original in ("Deploy plan", "Re: already prefixed", "RE: shouting",
	                 "re: lowercase", "  padded  ", ""):
		# EXACTLY, including surrounding whitespace. This asserted
		# `original.strip()` until review caught it: the core rejects a padded
		# subject deliberately, so trimming here would hide a refusal the
		# human is entitled to see and send something they did not type.
		assert InboxState.reply_subject(original) == original
	assert InboxState.reply_subject(None) == ""
	# Specifically: nothing is ever ADDED, to anything.
	assert not InboxState.reply_subject("Deploy plan").startswith("Re:")


def test_reply_is_refused_when_nothing_is_claimed(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert state.begin_reply() is False
	assert state.mode == MODE_BROWSE
	assert "claim the message first" in state.status


def test_escape_cancels_a_draft_without_sending(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "half-written thought"
	state.cancel_reply()
	assert state.mode == MODE_BROWSE and state.draft == ""
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
	assert state.unresolved_count() == 1      # still owed, still visible


# -- ordering and the FIFO warning -----------------------------------------

def test_messages_is_the_exact_reverse_of_what_claim_would_deliver(env):
	"""MESSAGES is NEWEST FIRST (Slawomir's ruling), and delivery is still
	FIFO. The invariant that survives -- and the one worth pinning -- is that
	they are the SAME total order, inverted.

	`created_ts` is second-resolution, so messages sent within one second tie
	and core breaks the tie on id. If the console tie-broke differently the
	two orders would not be reverses of each other, and "the newest message"
	and "the message `claim` takes last" would be different rows.

	(This test used to assert the list order EQUALLED delivery order, when
	MESSAGES was oldest-first. That presentation is superseded; the ordering
	agreement it was really about is unchanged and is asserted here.)"""
	store, _ = env
	for i in range(6):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"m{i}", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	listed = [r["id"] for r in state.rows]
	delivery_order = []
	while True:
		try:
			claim = store.claim("acme.implementer")
		except core.BatonError:
			break
		delivery_order.append(claim["message_id"])
		store.close_claim(claim["claim_id"], participant="acme.implementer")
	assert listed == list(reversed(delivery_order))
	# ...and the newest is at the TOP, which is the point of the ruling.
	assert listed[0] == delivery_order[-1]


def test_skipping_a_senders_earlier_message_warns_but_allows(env):
	"""Warns rather than forbids: the human may have a reason, and a console
	that refuses teaches people to work around it.

	Newest-first means the row that SKIPS something is now the head of the
	list rather than the row below it. The warning compares by
	`(created_ts, id)` rather than by position for exactly that reason, so
	this pins both directions: the newer row warns, the older one does not."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="a", body=b"a\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="b", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	later = state.selected                          # newest is at the top now
	assert "earlier message" in state.warning
	state.move(1, store)                            # down to the older one
	assert state.warning == "", "the oldest pending message skips nothing"
	state.move(-1, store)
	state.open_selected(store)                      # allowed anyway
	assert state.detail["delivery"]["message"]["subject"] == later["subject"]


def test_no_warning_across_different_senders(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="theirs", body=b"a\n")
	store.send("hq.lead", "acme.implementer", kind="q", subject="mine", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.move(1, store)
	assert state.warning == ""


# -- unresolved work stays visible ----------------------------------------

def test_unresolved_claims_remain_visible_until_disposed(env):
	"""The failure this console exists to prevent: walking away from a claim
	nobody else can take."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert state.unresolved_count() == 1
	for _ in range(3):
		state.refresh(store)
		assert state.unresolved_count() == 1
	state.close_selected(store, outcome="noted")
	assert state.unresolved_count() == 0


def test_console_declares_the_core_api_it_needs():
	check_core_compatibility(core)
	assert core.core_versions()["core_api_version"] >= REQUIRES_CORE_API


# -- displayed item and action target must be incapable of diverging -------

def test_reply_cannot_land_on_a_claim_the_human_is_not_looking_at(env):
	"""Reported by baton.reviewer, reproduced before fixing.

	Opening a notice removes it from the list, so `refresh` shifted the cursor
	onto an unrelated claimed message while the detail pane still showed the
	notice. `r` then bound to the CURSOR -- so a reply typed while reading a
	notice was delivered to a different sender entirely. Not merely a wrong
	disposition: the human's own words to the wrong recipient."""
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="A notice", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Unrelated work", body=b"q\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	# Claim the message so an actionable claim exists to be hit by accident.
	for index, row in enumerate(state.rows):
		if row["row_type"] == "message":
			state.cursor = index
			state.open_selected(store)
			break
	state.refresh(store)
	for index, row in enumerate(state.rows):
		if row["row_type"] == "notice":
			state.cursor = index
			break
	state.preview(store)
	state.open_selected(store)
	assert "notice" in state.detail

	before = store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]
	# `r` on a notice now composes a directed message to its AUTHOR. The
	# safety property this test exists for is unchanged and is what matters:
	# it must never bind to the unrelated claim under the cursor.
	assert state.begin_reply() is True
	assert state.compose["to"] == "hq.lead", "the reply bound to the wrong party"
	assert state.compose["to"] != "acme.reviewer"
	state.draft = "meant for the notice"
	assert state.send_reply(store) is None       # no claim is answerable here
	assert state.close_selected(store) is None
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == before
	# The unrelated claim is untouched and still owed.
	assert state.unresolved_count() == 1


def test_navigating_away_moves_the_action_target_to_the_new_row(env):
	"""Moving must change the action target deliberately, never leave a stale
	one armed behind the new view.

	The DIRECTION changed with claim-on-highlight: it used to be dropped and
	left at None, because selection was observational. Now the new row is
	claimed and opened, so the target FOLLOWS the selection. The property that
	survives -- and it is the one the wrong-recipient bug was about -- is that
	the target and the displayed row can never be different rows."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="First", body=b"a\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Second", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert state.opened is not None
	opened_id = state.opened["id"]
	state.move(1, store)
	assert state.selected["id"] != opened_id
	assert state.opened is not None, "the new row was not opened"
	assert state.opened["id"] == state.selected["id"], (
		"the action target is not the row on screen")
	# The earlier claim survives and is still owed: nothing is auto-closed.
	assert state.unresolved_count() == 2


def test_a_draft_does_not_follow_the_cursor(env):
	"""A half-typed reply belongs to the item it was started for. Carrying it
	to the next row is how the wrong thing gets sent confidently."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="First", body=b"a\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Second", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "half-written"
	state.move(1, store)
	assert state.mode == MODE_BROWSE and state.draft == ""


def test_public_refresh_keeps_display_and_target_together(env):
	"""PUBLIC refresh must hold the invariant by itself.

	The earlier version of this test called a private `_recentre_on_opened`
	afterwards, so the test was supplying the behaviour and the model was not.
	The polling loop calls public `refresh`, so a test that repairs the state
	by hand proves only that the repair works."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Working on", body=b"a\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	target = state.opened["claim_id"]
	opened_id = state.opened["id"]
	# Mail keeps arriving and the list reorders underneath, repeatedly.
	for i in range(3):
		store.send("hq.lead", "acme.implementer", kind="q",
		           subject=f"Newer {i}", body=b"b\n")
		state.refresh(store)                     # public API only
	assert state.opened["claim_id"] == target
	assert state.opened["id"] == opened_id
	assert state.selected["id"] == opened_id     # cursor re-aimed at what is shown
	state.begin_reply()
	# The draft is the SUBJECT line now; the point of this test is WHICH
	# claim the reply lands on, which is unchanged.
	state.draft = "Working on"
	result = state.send_reply(store)
	response = store.get_message(result["response_message_id"])
	assert response["subject"] == "Working on"


def test_refresh_invalidates_a_target_that_disappeared(env):
	"""If the opened claim stops being ours, refresh must drop the target and
	SAY so. Stale actionable state left armed behind the current view is how
	the next keystroke goes somewhere unexpected."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Mine", body=b"a\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	claim_id = state.opened["claim_id"]
	# Someone with the recovery capability takes the claim back.
	store.recover_claim(claim_id, participant="hq.lead", reason="abandoned")
	state.refresh(store)                          # public API only
	assert state.opened is None
	assert state.detail is None
	assert "no longer" in state.status
	# Nothing is actionable, and no disposition can be produced by accident.
	before = store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]
	assert state.send_reply(store) is None
	assert state.close_selected(store) is None
	assert store.conn.execute(
		"SELECT COUNT(*) FROM dispositions").fetchone()[0] == before


def test_refresh_discards_a_draft_for_a_lost_claim(env):
	"""A reply half-typed for a claim that is no longer ours must not survive
	to be sent at whatever comes next."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Mine", body=b"a\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "most of a careful answer"
	store.recover_claim(state.opened["claim_id"], participant="hq.lead", reason="taken")
	state.refresh(store)
	assert state.mode == MODE_BROWSE and state.draft == ""
	assert "draft discarded" in state.status


def test_the_actionable_item_is_visible_to_the_renderer(env):
	"""Keeping the invariant in code is not enough if the human cannot see
	which item their next keystroke applies to."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"a\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	# SUPERSEDED IN LOCATION. `action_target_description` composed the
	# footer's `acting on ...` clause and is removed with the footer. What the
	# human must still be able to see is the OBLIGATION, and the two facts
	# that carry it are the affordance query and the header's count.
	assert not hasattr(state, "action_target_description"), \
		"the removed clause is back"
	assert state.affordances()["close"] is False
	assert state.unresolved_count() == 0
	state.open_selected(store)
	assert state.affordances()["close"] is True
	assert state.unresolved_count() == 1
	state.close_selected(store, outcome="noted")
	assert state.affordances()["close"] is False
	assert state.unresolved_count() == 0


def test_tests_do_not_prop_up_the_model_with_private_calls():
	"""A guard on the guards.

	One of these tests used to call a private repair method after `refresh`,
	so it passed while the model itself did not hold the invariant -- the test
	was supplying the behaviour the polling loop would not have. Any test that
	reaches past the public API can hide that same class of gap, so the whole
	file is scanned for it."""
	import ast
	import pathlib

	tree = ast.parse(pathlib.Path(__file__).read_text())
	offenders = []
	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef) and node.name == THIS_TEST:
			continue
		if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
			if isinstance(node.value, ast.Name) and node.value.id in STATE_NAMES:
				offenders.append(f"{node.value.id}.{node.attr} (line {node.lineno})")
	assert not offenders, f"tests call private state internals: {offenders}"


THIS_TEST = "test_tests_do_not_prop_up_the_model_with_private_calls"
STATE_NAMES = {"state", "first", "second"}


# -- pre-commit defect: an attachment IS content ---------------------------

def _composing(store, root, *, body="", attach="", subject="Subject"):
	"""`attach` is still written here as `root:path` because that is what the
	CORE call takes, and these tests are about what reaches the wire.

	SUPERSEDED AS UI: the human never types that form. They choose a root from
	a picker and type a path relative to it, and the console builds the
	locator at the boundary. The split is set up directly here so these
	pre-commit content tests keep asking their own question."""
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(recipient="acme.reviewer")
	state.compose["subject"] = subject
	state.compose["body"] = body
	if attach:
		root_id, _, relative = attach.partition(":")
		state.compose["attach_root"] = root_id
		state.compose["attach_path"] = relative
		state.known_roots = [{"root_id": root_id, "path": str(root)}]
	return state


def _message_count(store):
	return store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]


def test_an_attachment_with_no_body_is_a_valid_message(env):
	"""Protocol 9 requires content, and an external attachment IS a content
	leaf. Refusing this made the console disagree with the authority it is a
	front end for."""
	store, root = env
	state = _composing(store, root, attach="src:EVIDENCE.md")
	result = state.send_compose(store)
	assert result is not None, f"attachment-only send refused: {state.status}"

	leaves = store.conn.execute(
		"SELECT storage, content_type FROM parts "
		"WHERE owner_kind = 'message' AND owner_id = ? AND storage != 'none' "
		"ORDER BY ordinal", (result,)).fetchall()
	# EXACTLY ONE leaf, and it is the external one. Adding an empty inline
	# text part to satisfy a content check would put a part on the wire that
	# the sender never wrote.
	assert len(leaves) == 1, f"expected one leaf, got {leaves}"
	assert leaves[0][0] == "external"


def test_a_truly_empty_compose_is_refused(env):
	"""Nothing at all -- no subject, no body, no attachment. A message needs
	SOMETHING to say.

	(A subject alone used to be refused too. Slawomir superseded that with the
	one-line shorthand below, so this test now pins the narrower rule that
	survived rather than the one it replaced.)"""
	store, root = env
	before = _message_count(store)
	state = _composing(store, root, subject="")
	assert state.send_compose(store) is None
	assert _message_count(store) == before, "a refused send still wrote"
	assert state.mode == MODE_COMPOSE
	assert "nothing to send" in state.status


def test_a_whitespace_only_body_is_content(env):
	"""The store accepts those bytes. A console that silently refuses them is
	inventing a rule the protocol does not have -- and indentation and blank
	lines are content in Markdown, which is what this body is declared as."""
	store, root = env
	state = _composing(store, root, body="   \n\t\n")
	result = state.send_compose(store)
	assert result is not None, f"whitespace-only body refused: {state.status}"
	stored = store.conn.execute(
		"SELECT c.body FROM parts p JOIN contents c ON c.content_id = p.content_id "
		"WHERE p.owner_kind = 'message' AND p.owner_id = ? AND p.storage = 'inline'",
		(result,)).fetchone()
	assert stored[0] == b"   \n\t\n", "the whitespace was altered on the way out"


def test_a_padded_reply_subject_is_trimmed_by_the_console_at_send(env):
	"""SUPERSEDED, twice, and the second reversal was ruled.

	This test first set a whitespace-only BODY and asserted it was accepted,
	which was right when the draft was a body. It then asserted the console
	passed a padded SUBJECT through untouched so the core's refusal surfaced.

	Slawomir ruled the split: the shared core and the agent CLI keep refusing
	edge whitespace -- an agent sending `"  S  "` has a bug worth hearing
	about, and accepting it would change retry identity -- while the TUI trims
	at send. A human typing into a field trails a space the way they do in
	every other text box on their machine, and answering that with a refusal
	is the console failing to be a console.

	Interior whitespace is still untouched, and the core is still the only
	validator. The console does not pre-empt any OTHER refusal."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"y\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(10, 10)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "  padded  "
	assert state.send_reply(store) is not None
	assert state.unresolved_count() == 0        # the claim resolved
	sent = store.list_messages("acme.reviewer")
	assert [m["subject"] for m in sent if m["from_participant"]
	        == "acme.implementer"] == ["padded"]


def test_the_console_trims_only_the_edges_of_a_subject(env):
	"""The narrow half of the ruling. Interior whitespace is unambiguous and
	is part of what the human wrote."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"y\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(10, 10)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "  two   words  "
	assert state.send_reply(store) is not None
	sent = [m for m in store.list_messages("acme.reviewer")
	        if m["from_participant"] == "acme.implementer"]
	assert sent[0]["subject"] == "two   words"


def test_compose_buffers_survive_every_failed_send(env):
	"""Retyping a message because the console threw it away is the kind of
	small betrayal that stops people using a tool."""
	store, root = env
	# No recipient.
	state = _composing(store, root, body="text")
	state.compose["to"] = ""
	assert state.send_compose(store) is None
	assert state.compose.get("body") == "text"
	# No content at all, not even a subject.
	state = _composing(store, root, subject="")
	state.compose["body"] = ""
	assert state.send_compose(store) is None
	assert state.compose.get("body") == ""
	# Rejected by the STORE -- an attachment path that does not exist.
	state = _composing(store, root, body="text", attach="src:missing.md")
	assert state.send_compose(store) is None
	assert state.compose.get("body") == "text"
	assert state.mode == MODE_COMPOSE


def test_a_notice_uses_the_subject_shorthand_too(env):
	"""Slawomir approved the one-line shorthand for notices as well, for
	consistency with directed compose. A subject alone becomes the content
	part; a zero-byte part is still never published.

	(This test previously asserted the opposite -- that a notice always needs
	a body -- which was the rule before that decision.)"""
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(notice=True)
	state.compose["subject"] = "Maintenance at 14:00"
	state.compose["body"] = ""
	notice_id = state.send_compose(store)
	assert notice_id is not None
	stored = store.conn.execute(
		"SELECT c.body FROM parts p JOIN contents c ON c.content_id = p.content_id "
		"WHERE p.owner_kind = 'notice' AND p.owner_id = ?", (notice_id,)).fetchone()
	assert stored[0] == b"Maintenance at 14:00"


def test_a_notice_with_neither_subject_nor_body_is_refused(env):
	"""Truly empty is still refused, and nothing is written."""
	store, _ = env
	before = store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(notice=True)
	assert state.send_compose(store) is None
	assert store.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == before
	assert "nothing to send" in state.status


# -- addendum: the one-line subject shorthand ------------------------------

def test_a_subject_alone_sends_as_a_one_line_message(env):
	"""A quick message should not cost a Tab and a retype. The subject line
	becomes the content part as well as the subject -- the same words either
	way."""
	store, root = env
	state = _composing(store, root, subject="deploy is green")
	result = state.send_compose(store)
	assert result is not None, f"subject-only send refused: {state.status}"

	row = store.conn.execute(
		"SELECT subject FROM messages WHERE id = ?", (result,)).fetchone()
	assert row[0] == "deploy is green"

	leaves = store.conn.execute(
		"SELECT p.storage, p.content_type, c.body FROM parts p "
		"LEFT JOIN contents c ON c.content_id = p.content_id "
		"WHERE p.owner_kind = 'message' AND p.owner_id = ? AND p.storage != 'none' "
		"ORDER BY p.ordinal", (result,)).fetchall()
	assert len(leaves) == 1, f"expected one leaf, got {leaves}"
	assert leaves[0][0] == "inline"
	assert leaves[0][1].startswith("text/markdown")
	# The SUBJECT TEXT, not a zero-byte placeholder. An empty leaf would make
	# the message unreadable to anything that renders content, not headers.
	assert leaves[0][2] == b"deploy is green"


def test_the_shorthand_does_not_fire_when_there_is_a_body(env):
	"""An explicit body is what the sender wrote; the subject is a summary of
	it. Substituting one for the other would silently discard the message."""
	store, root = env
	state = _composing(store, root, subject="summary", body="the actual text")
	result = state.send_compose(store)
	assert result is not None
	bodies = [row[0] for row in store.conn.execute(
		"SELECT c.body FROM parts p JOIN contents c ON c.content_id = p.content_id "
		"WHERE p.owner_kind = 'message' AND p.owner_id = ?", (result,)).fetchall()]
	assert bodies == [b"the actual text"]


def test_the_shorthand_does_not_fire_when_there_is_an_attachment(env):
	"""Subject plus attachment stays attachment-only. Synthesizing an inline
	duplicate of the subject would put a second leaf on the wire that the
	sender did not write."""
	store, root = env
	state = _composing(store, root, subject="the evidence",
	                   attach="src:EVIDENCE.md")
	result = state.send_compose(store)
	assert result is not None, f"refused: {state.status}"
	leaves = store.conn.execute(
		"SELECT storage FROM parts WHERE owner_kind = 'message' AND owner_id = ? "
		"AND storage != 'none' ORDER BY ordinal", (result,)).fetchall()
	assert [row[0] for row in leaves] == ["external"]


def test_the_compose_prompt_says_enter_sends_from_any_field(env):
	"""The shorthand is only a keystroke saver if the human knows it exists,
	and it is invisible: nothing on screen otherwise suggests Enter works
	before you have reached the body.

	SUPERSEDED IN LOCATION. This required the sentence in the detail pane AND
	again in the status bar -- the same instruction in two layers, which is
	exactly what the one-owner ruling removes. The shorthand still has to be
	discoverable, so `?` help owns it, and the panes must be clear of it."""
	from baton_tui.render import layout_for, render
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(recipient="acme.reviewer")
	state.set_viewport(**layout_for(100, 24))
	screen = render(state, 100, 24)

	# The COMPOSE PROMPT itself, in the detail pane -- not merely somewhere on
	# screen. The status bar carries the same words, so a whole-screen search
	# passed even with the prompt hint deleted. Checked by removing it.
	from baton_tui.render import DIVIDER

	def flat(lines):
		# Whitespace-insensitive: the hint WRAPS at this pane width, so a
		# phrase is split across rows and a naive substring search reports it
		# missing. `render` also rstrips each row, so the wrap point loses its
		# space entirely.
		return " ".join(" ".join(lines).split())

	# STACKED: the detail pane is the rows BELOW the one-row rule and above the
	# two-row footer, where it used to be the columns right of the divider.
	rule = [index for index, line in enumerate(screen)
	        if DIVIDER * 8 in line][0]
	detail = flat(screen[rule + 1:-1])
	assert "any field" not in detail, "tutorial prose is back in the work area"
	assert "subject alone" not in detail
	assert "new message" not in detail, "the removed heading is back"
	# The fields themselves are still there -- removal of explanation, never
	# of the state the human needs to act.
	assert "to:" in detail and "subject:" in detail

	# Status reports the event, not the key list.
	status = flat(screen[-1:])
	assert "composing a message" in status
	assert "any field" not in status, "status is restating the footer again"

	# ...and `?` help, the owner, carries the shorthand in full.
	from baton_tui.keys import HELP_SECTIONS
	help_text = " ".join(f"{key} {text}" for _title, rows in HELP_SECTIONS
	                     for key, text, *_ in rows)
	assert "ANY field" in help_text
	assert "subject alone is enough" in help_text


def test_compose_opens_focused_on_the_subject(env):
	"""The shorthand costs zero Tabs only if the caret starts where the one
	line gets typed."""
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(recipient="acme.reviewer")
	assert state.compose_fields[state.compose_field] == "subject"


# -- C3: MESSAGES is newest-first, and an arrival must not move the target --

def test_messages_is_newest_first_by_a_total_order(env):
	"""Ruled by Slawomir: new at top. Pinned as a TOTAL order over
	`(created_ts, id)` descending, with ties present -- Baton stamps to the
	second, so a test that relied on send order inside one second would be
	asserting whatever SQLite happened to return."""
	store, _ = env
	ids = [store.send("acme.reviewer", "acme.implementer", kind="q",
	                  subject=f"m{index}", body=b"b\n") for index in range(8)]
	state = InboxState("acme.implementer")
	state.refresh(store)
	stamps = {mid: store.get_message(mid)["created_ts"] for mid in ids}
	assert len(set(stamps.values())) < len(ids), (
		"the fixture did not produce tied timestamps, so the tiebreak is untested")
	listed = [(row["created_ts"], row["id"]) for row in state.rows]
	assert listed == sorted(listed, reverse=True)


def test_a_notice_sorts_into_the_same_newest_first_order(env):
	"""Notices share the list, so they share the order. A row that sorted by a
	different rule would appear in a position nothing else explains."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="first", body=b"b\n")
	store.send_notice("hq.lead", kind="announcement", subject="broadcast", body=b"n\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	listed = [(row["created_ts"], row["id"]) for row in state.rows]
	assert listed == sorted(listed, reverse=True)


def test_new_mail_arrives_at_the_top_without_moving_the_selection(env):
	"""The reason identity matters more under newest-first than it did under
	oldest-first: an arrival inserts at index 0 and shifts every row down, so
	a numeric cursor would silently point at a different message and the next
	Enter would claim something the human never chose."""
	store, _ = env
	for index in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"old{index}", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.move(2, store)
	chosen = state.selected["id"]
	position = state.cursor
	# A real second later, so the arrival is unambiguously newer rather than
	# tied with the others and ordered by id. The point of the pin is that a
	# row inserted ABOVE the selection does not take the selection with it,
	# and a tie would sometimes place it below and prove nothing.
	import time
	time.sleep(1.1)
	new_id = store.send("hq.lead", "acme.implementer", kind="q",
	                    subject="arrival", body=b"b\n")
	before_poll = state.status
	state.refresh(store)
	assert state.rows[0]["id"] == new_id, "the arrival is not at the top"
	assert state.selected["id"] == chosen, "the selection followed the index, not the row"
	assert state.cursor == position + 1, "the cursor did not move down with its row"
	# And the poll says NOTHING about it. The arrival is at the top of the
	# list and counted in the header; a status line repeating that was a third
	# copy, written over whatever the human's last action had reported --
	# which here is the claim `move` took, the most important thing on screen.
	assert state.status == before_poll, \
		"the poll overwrote a real outcome with mailbox state"
	assert "claimed" in state.status, "the outcome that mattered was lost"


def test_the_sent_filter_keeps_its_row_when_something_is_sent(env):
	"""Same rule, same reason: `list_sent` is newest-first, so publishing puts
	a row above whatever the human had selected."""
	from baton_tui.state import VIEW_SENT
	store, _ = env
	for index in range(3):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=f"out{index}", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_view(VIEW_SENT)
	state.move(1, store)
	chosen = state.selected_sent["id"]
	# A real second later, so it certainly sorts ABOVE the selected row rather
	# than tying and landing below it, where the pin would prove nothing.
	import time
	time.sleep(1.1)
	newest = store.send("acme.implementer", "hq.lead", kind="q",
	                    subject="newer", body=b"b\n")
	state.refresh(store)
	assert state.sent_rows[0]["id"] == newest
	assert state.selected_sent["id"] == chosen


def test_first_and_last_still_reach_the_ends_under_newest_first(env):
	"""`gg` lands on the newest and `G` on the oldest. Both are still reachable
	and neither is the same row it used to be."""
	store, _ = env
	for index in range(6):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"m{index}", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	newest, oldest = state.rows[0]["id"], state.rows[-1]["id"]
	state.jump_to(len(state.rows) - 1, store)
	assert state.selected["id"] == oldest
	state.jump_to(0, store)
	assert state.selected["id"] == newest


def test_handled_and_outbound_rows_keep_their_place_in_the_new_order(env):
	"""Answering changes the badge, not the position -- under newest-first as
	it did under oldest-first."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="in", body=b"b\n")
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="out", body=b"b\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	before = [row["id"] for row in state.rows]
	inbound = next(index for index, row in enumerate(state.rows)
	               if row.get("direction") == "in")
	state.cursor = inbound
	state.preview(store)
	state.open_selected(store)
	state.close_selected(store, outcome="noted")
	assert [row["id"] for row in state.rows] == before
	assert state.rows[inbound]["state"] == "closed"


# -- RULED: a reply is an indented child of what it answers -----------------

def _answered(store, subject="Question"):
	"""A received message and the outbound reply that resolved it."""
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject=subject, body=b"?\n")
	claim = store.claim("acme.implementer", message_id=mid)
	result = store.reply(claim["claim_id"], participant="acme.implementer",
	                     kind="response", subject=subject, body=b"answered\n")
	return mid, result["response_message_id"]


def test_a_reply_is_an_indented_child_of_the_message_it_answers(env):
	"""Slawomir's ruling. Newest-first put the reply immediately ABOVE its own
	parent, where it reads as two unrelated messages that happen to share a
	subject -- and the row a human looks at to see whether something was
	answered is the row of the thing they answered."""
	store, _ = env
	parent, reply = _answered(store)
	state = InboxState("acme.implementer")
	state.refresh(store)
	order = [row["id"] for row in state.rows]
	assert order.index(reply) == order.index(parent) + 1, "the reply is not under its parent"
	depths = {row["id"]: row["depth"] for row in state.rows}
	assert depths[parent] == 0 and depths[reply] == 1


def test_the_reply_marker_is_drawn_on_the_child_row(env):
	"""The relationship must be VISIBLE, not inferred from adjacency: two rows
	next to each other say nothing on their own."""
	from baton_tui.render import THREAD_MARKER, layout_for, render
	store, _ = env
	_answered(store, "Needs an answer")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	rows = [line for line in render(state, 100, 24)[1:] if "Needs an answer" in line]
	assert len(rows) == 2
	parent, child = rows
	assert THREAD_MARKER not in parent
	assert THREAD_MARKER in child
	# Indented, and the badge/date columns are untouched by it.
	assert child.index(THREAD_MARKER) > parent.index("Needs an answer")
	assert child.index("08-") == parent.index("08-")


def test_a_reply_keeps_its_own_badge_and_direction(env):
	"""Threading is presentation. The child is still an outbound message with
	its own lifecycle, and the parent's badge still changes when it is
	answered.

	SUPERSEDED SPELLING: the answered INBOUND parent reads `✓` -- I replied,
	nothing is owed -- rather than the store's `R`. The outbound child keeps
	`Q`, because what matters about a message you sent is whether the other
	side has picked it up. The two notations answering different questions on
	adjacent rows is the point of the ruling, not a wrinkle in it."""
	from baton_tui.render import COMPLETED, layout_for, render
	store, _ = env
	parent, reply = _answered(store, "Badged")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	by_id = {row["id"]: row for row in state.rows}
	assert by_id[parent]["state"] == "completed"
	assert by_id[reply]["direction"] == "out"
	rows = [line for line in render(state, 100, 24)[1:] if "Badged" in line]
	assert COMPLETED in rows[0], rows[0]       # I answered it
	from baton_tui.render import QUEUED
	assert QUEUED in rows[1], rows[1]         # the reply, queued for them


def test_answering_brings_the_thread_back_to_the_top(env):
	"""Threads sort by their NEWEST member. By the root's own timestamp a reply
	you just sent would appear near the bottom -- the "I sent it and it
	vanished" failure that unified MESSAGES exists to fix."""
	import time
	store, _ = env
	old = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Old thread", body=b"?\n")
	time.sleep(1.1)
	store.send("hq.lead", "acme.implementer", kind="q", subject="Newer", body=b"?\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert state.rows[0]["subject"] == "Newer"
	time.sleep(1.1)
	claim = store.claim("acme.implementer", message_id=old)
	store.reply(claim["claim_id"], participant="acme.implementer",
	            kind="response", subject="Old thread", body=b"answered\n")
	state.refresh(store)
	assert state.rows[0]["id"] == old, "the answered thread did not come back up"
	assert state.rows[1]["depth"] == 1
	assert state.rows[2]["subject"] == "Newer"


def test_an_orphaned_reply_is_a_root_not_an_indent_under_nothing(env):
	"""`responds_to` is followed only within the VISIBLE set. A reply whose
	parent has been collected must stand on its own rather than claim a depth
	it cannot show a parent for."""
	from baton_tui.state import thread_rows
	rows = [{"row_type": "message", "id": "b", "created_ts": "2026-08-08T10:00:01Z",
	         "responds_to": "a-which-is-gone"}]
	threaded = thread_rows(rows)
	assert [row["depth"] for row in threaded] == [0]


def test_a_row_that_answers_itself_cannot_loop(env):
	"""Defensive: the schema should never produce it, but a self-reference
	would hang the walk rather than fail visibly."""
	from baton_tui.state import thread_rows
	rows = [{"row_type": "message", "id": "a", "created_ts": "2026-08-08T10:00:00Z",
	         "responds_to": "a"}]
	assert [row["depth"] for row in thread_rows(rows)] == [0]


# -- R10: an external part must be reachable AND readable -------------------
#
# Trial failure, reported by Slawomir against a real message: "cannot see the
# license part.. I can only view part[0]". Both headers were reachable; the
# external one rendered as "(no retained bytes)" and offered nothing, so the
# human correctly concluded there was nothing to see.

def _licensed(store, tmp_root, body=b"MIT License\n\nPermission is granted.\n"):
	(tmp_root / "LICENSE").write_bytes(body)
	return store.send("acme.reviewer", "acme.implementer", kind="q",
	                  subject="Queue sample — multipart with stable license",
	                  parts=[
		{"content_type": "text/markdown; charset=utf-8",
		 "body": b"# Note\n\nSee the licence beside this.\n"},
		{"content_type": "text/plain; charset=utf-8", "disposition": "attachment",
		 "attach": "src:LICENSE", "filename": "LICENSE"}])


def _opened_licensed(store, root):
	from baton_tui.render import layout_for
	_licensed(store, root)
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 40))
	state.open_selected(store)
	return state


def test_both_part_headers_are_reachable_and_the_mark_moves(env):
	"""The required regression: an inline Markdown leaf plus an external
	LICENSE leaf, both reachable with `[`/`]`, the selected header visibly
	changing."""
	from baton_tui.driver import step
	from baton_tui.render import STYLE_PART_HEADER, layout_for, render_styled
	store, root = env
	state = _opened_licensed(store, root)
	assert [part["address"] for part in state.visible_parts()] == ["0", "1"]

	def marked():
		layout = layout_for(100, 40)
		state.set_viewport(**layout)
		return [text for text, style in render_styled(state, 100, 40)
		        if STYLE_PART_HEADER in style]

	first = marked()
	assert first and "[0]" in first[0]
	step(state, store, ord("]"), 100, 40)
	assert state.selected_part["address"] == "1"
	second = marked()
	assert second and "[1]" in second[0], "the external header is not marked"
	assert second != first, "the selected header did not visibly change"
	step(state, store, ord("["), 100, 40)
	assert state.selected_part["address"] == "0"


def test_an_external_part_is_not_described_as_empty(env):
	"""The actual defect. `(no retained bytes)` belongs to a SCRUBBED
	transient body, where the manifest outlived the payload. An external leaf
	has bytes -- in a configured root, hash-pinned and verified at claim
	time -- and describing it as empty is why the trial concluded the part
	could not be viewed."""
	from baton_tui.render import layout_for, render
	store, root = env
	state = _opened_licensed(store, root)
	state.set_viewport(**layout_for(100, 40))
	rows = render(state, 100, 40)
	screen = "\n".join(rows)
	assert "no retained bytes" not in screen
	# Whitespace-insensitive: the header WRAPS at this width, so a phrase is
	# split across rows and a naive substring search reports it missing.
	flat = " ".join(" ".join(rows).split())
	assert "external file src:LICENSE" in flat
	assert "pin verified" in flat


def test_v_reads_the_external_part_into_the_pane(env):
	"""The fix. `m` cannot help -- the core refuses to copy an external part
	into a projection, because it is already a file -- so without this there
	was no key at all for the one thing a human wants to do with a licence."""
	from baton_tui.driver import step
	from baton_tui.render import layout_for, render
	store, root = env
	state = _opened_licensed(store, root)
	step(state, store, ord("]"), 100, 40)
	before = "\n".join(render(state, 100, 40))
	assert "Permission is granted" not in before
	step(state, store, ord("v"), 100, 40)
	state.set_viewport(**layout_for(100, 40))
	after = "\n".join(render(state, 100, 40))
	assert "MIT License" in after
	assert "Permission is granted" in after
	assert state.status_severity == "success"


def test_reading_an_external_part_writes_nothing(env):
	"""It returns delivered content, so it is owner-checked and claim-gated --
	but it creates no claim, no receipt, no transition and no projection."""
	from baton_tui.driver import step
	store, root = env
	state = _opened_licensed(store, root)
	before = (_counts(store),
	          store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0],
	          store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0])
	step(state, store, ord("]"), 100, 40)
	step(state, store, ord("v"), 100, 40)
	assert (_counts(store),
	        store.conn.execute("SELECT COUNT(*) FROM transitions").fetchone()[0],
	        store.conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]) == before


def test_reading_an_external_part_fails_closed_on_a_broken_pin(env):
	"""The bytes are shown only while they are the bytes that were sent.
	Editing the file after publication invalidates the pin, and a console that
	displayed the new contents would be showing something the sender never
	sent."""
	from baton_tui.driver import step
	store, root = env
	state = _opened_licensed(store, root)
	step(state, store, ord("]"), 100, 40)
	(root / "LICENSE").write_bytes(b"a different licence entirely\n")
	step(state, store, ord("v"), 100, 40)
	assert state.status_severity == "error"
	assert state.external_text == {}


def test_materialize_still_targets_the_selected_external_part(env):
	"""`m` acts on the SELECTED part, and for an external one the core refuses
	by design -- it is already a file, and copying it would duplicate the
	thing the pin exists to avoid. What matters is that the refusal names the
	part the human chose, not that it silently wrote part 0."""
	from baton_tui.driver import step
	store, root = env
	state = _opened_licensed(store, root)
	state.projection_dir = str(root)
	step(state, store, ord("]"), 100, 40)
	assert state.materialize_selected_part(store) is None
	assert "'1'" in state.status, state.status
	assert "externally stored at src:LICENSE" in state.status


def test_bytes_read_for_one_message_are_never_drawn_under_another(env):
	"""They are cached for display only, and a cache keyed by manifest address
	would happily redraw message A's licence under message B's part 1."""
	from baton_tui.driver import step
	store, root = env
	state = _opened_licensed(store, root)
	step(state, store, ord("]"), 100, 40)
	step(state, store, ord("v"), 100, 40)
	assert state.external_text
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Other",
	           body=b"unrelated\n")
	state.refresh(store)
	state.move(1, store)
	assert state.external_text == {}, "the cached file survived the move"


# -- RULED: an answered conversation is never a dead end -------------------

def _answered_pair(store):
	"""A received message, claimed and answered. The claim is resolved, so
	nothing is owed -- and the conversation is still open."""
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="The question", body=b"?\n")
	claim = store.claim("acme.implementer", message_id=mid)
	store.reply(claim["claim_id"], participant="acme.implementer",
	            kind="response", subject="The question", body=b"answered\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.cursor = next(index for index, row in enumerate(state.rows)
	                    if row["id"] == mid)
	state.preview(store)
	state.open_selected(store)
	return state, mid


def _counts_full(store, message_id=None):
	"""Claims, dispositions and receipts overall, plus the transitions of ONE
	message.

	Not total transitions: publishing ANY message writes one, so a follow-up
	moves that number legitimately. What must not move is anything about the
	ORIGINAL -- so the transition count is scoped to it, which is the actual
	claim being made."""
	one = lambda sql, *a: store.conn.execute(sql, a).fetchone()[0]
	return (one("SELECT COUNT(*) FROM claims"),
	        one("SELECT COUNT(*) FROM dispositions"),
	        one("SELECT COUNT(*) FROM notice_seen"),
	        one("SELECT COUNT(*) FROM transitions WHERE entity_id = ?",
	            message_id) if message_id else 0)


def test_a_handled_inbound_row_offers_a_follow_up_not_a_dead_end(env):
	"""Slawomir's ruling. `R` stays, the body stays immutable, nothing is
	owed -- and the screen says what can still be done."""
	from baton_tui.render import layout_for, render
	from baton_tui.state import FOLLOW_UP_ANSWERED
	store, _ = env
	state, mid = _answered_pair(store)
	assert state.opened["claim_id"] is None, "a resolved row offered a disposition"
	assert state.follow_up_context["to"] == "acme.reviewer"
	state.set_viewport(**layout_for(100, 40))
	screen = "\n".join(render(state, 100, 40))
	assert FOLLOW_UP_ANSWERED in screen
	assert "read only" not in screen.lower()
	# SUPERSEDED: an answered INBOUND row now reads `✓` -- I replied, nothing
	# is owed -- rather than `R`, which was the store's word for the
	# disposition it recorded.
	from baton_tui.render import COMPLETED
	assert COMPLETED in screen, "the handled row lost its badge"


def test_a_follow_up_is_a_new_linked_message_and_not_a_disposition(env):
	"""The whole shape: a new id, `responds_to` naming the selected message,
	`kind=follow_up`, and NOTHING moved on the original."""
	from baton_tui.state import KIND_FOLLOW_UP
	store, _ = env
	state, mid = _answered_pair(store)
	before = _counts_full(store, mid)
	messages = store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
	assert state.begin_reply() is True
	state.compose["subject"] = "one more thing"
	result = state.send_compose(store)
	assert result is not None, state.status
	# One new message, and not one claim, disposition, transition or receipt.
	assert store.conn.execute(
		"SELECT COUNT(*) FROM messages").fetchone()[0] == messages + 1
	assert _counts_full(store, mid) == before
	child = store.get_message(result)
	assert child["responds_to"] == mid
	assert child["kind"] == KIND_FOLLOW_UP
	assert child["to_participant"] == "acme.reviewer"
	assert child["from_participant"] == "acme.implementer"
	# The original is untouched: same state, same disposition.
	assert store.get_message(mid)["state"] == "completed"


def test_a_follow_up_inherits_the_thread_when_there_is_one(env):
	"""`thread_id` is inherited when the selected message has one, and is not
	invented when it does not."""
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Threaded", body=b"?\n", thread_id="t-42")
	claim = store.claim("acme.implementer", message_id=mid)
	store.reply(claim["claim_id"], participant="acme.implementer",
	            kind="response", subject="Threaded", body=b"a\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == mid)
	state.preview(store)
	state.open_selected(store)
	state.begin_reply()
	state.compose["subject"] = "still about this"
	result = state.send_compose(store)
	assert store.get_message(result)["thread_id"] == "t-42"


def test_an_ordinary_new_message_is_never_linked(env):
	"""`n` must not acquire a linkage from whatever was last open -- the same
	fault that once quoted an unrelated message into a fresh compose."""
	store, _ = env
	state, mid = _answered_pair(store)
	state.begin_compose(recipient="acme.reviewer")
	assert state.follow_up_to is None
	state.compose["subject"] = "unrelated"
	result = state.send_compose(store)
	child = store.get_message(result)
	assert child["responds_to"] is None
	assert child["kind"] != "follow_up"


def test_following_up_twice_creates_siblings(env):
	"""Two follow-ups on the same parent are siblings at one level, not a
	staircase: they are both in reference to the same message."""
	store, _ = env
	state, mid = _answered_pair(store)
	for text in ("first", "second"):
		state.open_selected(store)
		state.begin_reply()
		state.compose["subject"] = text
		assert state.send_compose(store) is not None, state.status
		state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == mid)
		state.preview(store)
	kids = [row for row in state.rows if row.get("responds_to") == mid]
	assert len(kids) == 3, "expected the reply plus two follow-ups"
	assert {row["depth"] for row in kids} == {1}, "siblings were nested"


def test_following_up_on_a_child_nests_one_level_deeper(env):
	"""Following up on a follow-up is the next level, subject to the cap."""
	store, _ = env
	state, mid = _answered_pair(store)
	state.begin_reply()
	state.compose["subject"] = "first"
	first = state.send_compose(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == first)
	state.preview(store)
	state.open_selected(store)
	assert state.follow_up_context["to"] == "acme.reviewer"
	state.begin_reply()
	state.compose["subject"] = "deeper"
	second = state.send_compose(store)
	rows = {row["id"]: row for row in state.rows}
	assert rows[second]["responds_to"] == first
	assert rows[second]["depth"] == rows[first]["depth"] + 1


def test_a_follow_up_from_an_outbound_row_goes_to_its_recipient(env):
	"""The other party, taken from the row: the AUTHOR for inbound, the
	RECIPIENT for outbound. Getting this backwards would send your follow-up
	to yourself."""
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Delegated",
	           body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	state.open_selected(store)
	assert state.follow_up_context["to"] == "acme.reviewer"
	state.begin_reply()
	state.compose["subject"] = "any progress?"
	result = state.send_compose(store)
	child = store.get_message(result)
	assert child["to_participant"] == "acme.reviewer"
	assert child["from_participant"] == "acme.implementer"


def test_the_original_body_is_never_what_the_console_writes_to(env):
	"""A follow-up is a new message. The authority's original bytes are
	immutable and must come back identical afterwards."""
	store, _ = env
	state, mid = _answered_pair(store)
	before = store.get_message(mid)
	state.begin_reply()
	state.compose["subject"] = "more"
	state.send_compose(store)
	after = store.get_message(mid)
	assert after["manifest_sha256"] == before["manifest_sha256"]
	assert after["subject"] == before["subject"]
	assert after["state"] == before["state"]


def test_the_detail_pane_says_in_reference_to(env):
	"""Human-facing prose for `responds_to`. The wire field is unchanged; the
	relation is broader than the one claim-resolving reply, so the label is."""
	from baton_tui.render import layout_for, render
	from baton_tui.state import IN_REFERENCE_TO
	store, _ = env
	state, mid = _answered_pair(store)
	state.begin_reply()
	state.compose["subject"] = "follow-up"
	child = state.send_compose(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == child)
	state.preview(store)
	state.open_selected(store)
	state.set_viewport(**layout_for(120, 40))
	screen = "\n".join(render(state, 120, 40))
	assert IN_REFERENCE_TO in screen
	assert mid in screen


# -- RULED: a seen notice stays in MESSAGES as history ---------------------

def _seen_notice(store, participant="acme.implementer", subject="Broadcast"):
	notice_id = store.send_notice("hq.lead", kind="announcement",
	                              subject=subject, body=b"the announcement\n")
	state = InboxState(participant)
	state.refresh(store)
	state.cursor = next(i for i, r in enumerate(state.rows)
	                    if r["row_type"] == "notice")
	state.preview(store)
	state.open_selected(store)
	return state, notice_id


def test_a_seen_notice_is_retained_with_the_seen_badge(env):
	"""Slawomir's ruling, and the badge he settled on: `✓`, because `N`
	reads as New — the opposite state — and `S` is the fallback spelling.

	(The bracketed spelling is SUPERSEDED by the one-cell status column; which
	glyph means what is unchanged.)"""
	from baton_tui.render import layout_for, render
	store, _ = env
	state, notice_id = _seen_notice(store)
	state.refresh(store)
	state.set_viewport(**layout_for(120, 24))
	row = next(r for r in state.rows if r["id"] == notice_id)
	assert row["state"] == "seen"
	listed = [line for line in render(state, 120, 24) if "Broadcast" in line][0]
	assert "✓" in listed, listed
	assert "!" not in listed, "a seen notice still demands attention"


def test_an_unseen_notice_keeps_the_attention_marker(env):
	"""The two states must not look alike; `!` is the one that asks for
	something."""
	from baton_tui.render import layout_for, render
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Fresh", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(120, 24))
	listed = [line for line in render(state, 120, 24) if "Fresh" in line][0]
	assert "!" in listed and "✓" not in listed


def test_opening_a_seen_notice_writes_nothing_and_says_no_redelivery(env):
	"""Not a content path. The absence of a write is not enough on its own: a
	reader has to be TOLD the bytes are not coming back, or the row looks one
	keystroke away from the announcement."""
	from baton_tui.render import layout_for, render
	store, _ = env
	state, notice_id = _seen_notice(store)
	state.refresh(store)
	before = _counts(store)
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == notice_id)
	state.preview(store)
	state.open_selected(store)
	assert _counts(store) == before, "reopening a seen notice wrote"
	state.set_viewport(**layout_for(120, 24))
	screen = "\n".join(render(state, 120, 24))
	assert "not redelivered" in screen or "not redelivered" in state.status


def test_the_body_read_this_session_stays_on_screen(env):
	"""It is already in memory. Blanking it because the poll ran would take
	away something the human is reading."""
	from baton_tui.render import layout_for, render
	store, _ = env
	state, notice_id = _seen_notice(store)
	state.set_viewport(**layout_for(120, 24))
	assert "the announcement" in "\n".join(render(state, 120, 24))
	state.refresh(store)
	assert "the announcement" in "\n".join(render(state, 120, 24)), \
		"the poll took the body away"


def test_after_a_restart_the_metadata_remains_and_the_body_does_not(env):
	"""What at-most-once MEANS: the row records that something was said, and
	is not a second copy of it."""
	from baton_tui.render import layout_for, render
	store, _ = env
	_, notice_id = _seen_notice(store)
	fresh = InboxState("acme.implementer")           # a new process
	fresh.refresh(store)
	row = next(r for r in fresh.rows if r["id"] == notice_id)
	assert row["state"] == "seen" and row["subject"] == "Broadcast"
	fresh.cursor = fresh.rows.index(row)
	fresh.preview(store)
	fresh.open_selected(store)
	fresh.set_viewport(**layout_for(120, 24))
	screen = "\n".join(render(fresh, 120, 24))
	assert "Broadcast" in screen
	assert "the announcement" not in screen, "the body came back after a restart"


def test_seen_state_is_per_participant(env):
	"""One receipt per participant. Seeing it must not mark it seen for
	anyone else."""
	store, _ = env
	_, notice_id = _seen_notice(store, "acme.implementer")
	other = InboxState("acme.reviewer")
	other.refresh(store)
	row = next(r for r in other.rows if r["id"] == notice_id)
	assert row["state"] == "unseen"


def test_a_seen_notice_sorts_by_the_same_newest_first_rule(env):
	"""It is an ordinary row now, so it obeys the ordinary order."""
	import time
	store, _ = env
	_seen_notice(store)
	time.sleep(1.1)
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Newer",
	           body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	listed = [(r["created_ts"], r["id"]) for r in state.rows]
	assert listed == sorted(listed, reverse=True)
	assert state.rows[0]["subject"] == "Newer"


def test_an_expired_notice_leaves_the_list(env):
	"""TTL and gc remain the ONLY reason a history row disappears."""
	store, _ = env
	notice_id = store.send_notice("hq.lead", kind="announcement",
	                              subject="Brief", body=b"x\n", ttl_seconds=1)
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert any(r["id"] == notice_id for r in state.rows)
	store.expire("hq.lead", notice_id=notice_id)
	state.refresh(store)
	assert not any(r["id"] == notice_id for r in state.rows)


def test_a_response_can_still_be_started_from_a_seen_row(env):
	"""`r`/`R` still reach the author from the retained metadata alone."""
	store, _ = env
	_, notice_id = _seen_notice(store)
	# A NEW process: the point is that the metadata alone is enough.
	fresh = InboxState("acme.implementer")
	fresh.refresh(store)
	fresh.cursor = next(i for i, r in enumerate(fresh.rows) if r["id"] == notice_id)
	fresh.preview(store)
	fresh.open_selected(store)
	assert fresh.begin_reply() is True
	assert fresh.compose["to"] == "hq.lead"


def test_refreshing_over_a_seen_notice_writes_nothing(env):
	"""Observation only: the activity query is a LEFT JOIN with no receipt and
	no write lock."""
	store, _ = env
	state, _ = _seen_notice(store)
	before = _counts(store)
	for _ in range(5):
		state.refresh(store)
	assert _counts(store) == before


# -- review R6: `v` is offered only when it could show something -----------

def _external(store, root, content_type, name="EVIDENCE.md"):
	(root / name).write_bytes(b"pinned evidence\n")
	return store.send("acme.reviewer", "acme.implementer", kind="q",
	                  subject=f"With {content_type}", parts=[
		{"content_type": "text/markdown; charset=utf-8", "body": b"# Note\n"},
		{"content_type": content_type, "disposition": "attachment",
		 "attach": f"src:{name}", "filename": name}])


def _opened_with_external(store, root, content_type):
	from baton_tui.render import layout_for
	mid = _external(store, root, content_type)
	state = InboxState("acme.implementer")
	state.projection_dir = str(root)
	state.refresh(store)
	state.set_viewport(**layout_for(120, 40))
	# BY ID. Same-second sends tie and order by id, so "the newest" is not
	# reliably at the top -- selecting positionally opened an earlier
	# message's part and compared it against this call's expectation.
	state.cursor = next(i for i, r in enumerate(state.rows) if r["id"] == mid)
	state.preview(store)
	state.open_selected(store)
	state.move_part(1)                                # onto the external leaf
	assert state.selected_part["storage"] == "external"
	return state


def test_an_external_text_part_offers_v_and_it_works(env):
	store, root = env
	state = _opened_with_external(store, root, "text/plain; charset=utf-8")
	assert state.affordances()["read_part"] is True
	assert state.read_selected_external_part(store) is not None
	assert state.status_severity == "success"


@pytest.mark.parametrize("content_type", ["image/png", "application/pdf",
                                          "application/octet-stream"])
def test_a_binary_external_part_never_offers_v(env, content_type):
	"""R6. The declared type is on the part, so this is decidable without
	touching the file — advertising `v` meant reading and HASHING a PNG only
	to report that it is not text."""
	from baton_tui.driver import _allowed
	import baton_tui.keys as K
	store, root = env
	state = _opened_with_external(store, root, content_type)
	assert state.affordances()["read_part"] is False
	assert not _allowed(state, K.READ_PART)
	reason = state.unavailable_reason("read_part")
	assert "not displayable" in reason
	assert "src:EVIDENCE.md" in reason, "the refusal does not say where the file is"


def test_the_binary_external_state_is_in_the_footer_matrix(env):
	"""It belongs in the swept matrix, not only in its own test."""
	from baton_tui.render import render
	store, root = env
	state = _opened_with_external(store, root, "image/png")
	legend = "\n".join(render(state, 200, 40)[-1:])
	assert "v read" not in legend, legend
	# The part is still reachable and still materializable — only `v` is not
	# offered, because only `v` could not show anything.
	assert state.affordances()["part_nav"] is True


def test_the_offer_and_the_action_use_one_rule(env):
	"""They must not disagree: the offer is made from the manifest and the
	action re-checks what came back, under the same predicate."""
	from baton_tui.state import _is_displayable_text
	store, root = env
	for content_type, expected in (("text/plain; charset=utf-8", True),
	                               ("text/html; charset=utf-8", True),
	                               ("image/png", False),
	                               ("application/pdf", False)):
		state = _opened_with_external(store, root, content_type)
		assert _is_displayable_text(state.selected_part) is expected
		assert state.affordances()["read_part"] is expected
