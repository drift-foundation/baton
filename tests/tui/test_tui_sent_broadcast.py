"""The scenario the ruling names: publish a scoped broadcast, then see it in
your own Sent view — in the SAME running console.

WHY THIS FILE EXISTS. On 2026-08-13, after the legacy 1.1.0 relocation,
`human.slawomir` published notice `433d58e6…` to scope `baton.*` and reported
that the legacy console did not show it. Slawomir ruled that legacy 1.1.0
exists only to reconnect participants through the new topology, so it is not
to be patched; the SUCCESSOR must be exercised with the same scenario before
its cutover, and this is that exercise.

WHAT "WITHOUT RESTARTING" MEANS HERE, precisely. Every check below runs
against the `InboxState` that published the notice. No second state object is
constructed, no store is reopened, and no test calls `refresh` on the state's
behalf — if the row is on screen it is because the console put it there.
Constructing a fresh state would test a restart, which is the one thing the
acceptance boundary excludes.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import baton_core as core                                       # noqa: E402
from baton_tui import keys as K                                 # noqa: E402
from baton_tui.driver import step                               # noqa: E402
from baton_tui.render import layout_for, render                 # noqa: E402
from baton_tui.state import (MODE_BROWSE, VIEW_SENT, InboxState)  # noqa: E402


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "sent-broadcast"},
			"participants": {
				"baton.implementer": {}, "baton.reviewer": {},
				"web.lead": {}, "human.slawomir": {},
			},
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path


@pytest.fixture
def env(tmp_path):
	path = _instance(tmp_path)
	with core.open_instance(path) as store:
		yield store, path


def _ready(store, participant="human.slawomir"):
	state = InboxState(participant)
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	state.preview(store)
	return state


def _press(state, store, *pressed):
	for key in pressed:
		step(state, store, key, 100, 24)
	return state


def _type(state, store, text):
	for char in text:
		_press(state, store, ord(char))


def _screen(state, columns=100, lines=24):
	return "\n".join(render(state, columns, lines))


def _broadcast(state, store, scope, subject):
	"""`N`, choose the audience, type the subject, send, confirm."""
	_press(state, store, ord("N"))
	if scope is not None:
		_type(state, store, scope)
	_press(state, store, K.ENTER_LF)
	_type(state, store, subject)
	_press(state, store, K.ENTER_LF, ord("y"))
	assert state.mode == MODE_BROWSE, \
		f"the composer did not close, so nothing was published: {state.status}"


def _sent_notices(state):
	return [row for row in state.sent_rows if row.get("row_kind") == "notice"]


# -- the acceptance boundary, clause by clause ------------------------------

def test_a_scoped_broadcast_is_in_the_senders_sent_view_without_a_restart(env):
	"""Acceptance clause 1. The console that published it shows it, with no
	restart and no refresh performed on its behalf by this test."""
	store, path = env
	state = _ready(store)
	_broadcast(state, store, "baton.*", "testing broadcast reply each")

	published = core.dump(path)["notices"]
	assert len(published) == 1, f"nothing was published: {state.status}"

	rows = _sent_notices(state)
	assert len(rows) == 1, \
		f"the notice is in the authority but not in Sent: {state.sent_rows}"
	assert rows[0]["id"] == published[0]["id"]
	assert state.sent_rows_fresh, "the Sent list is showing a stale cache"


def test_the_sent_row_is_accurate_about_kind_subject_and_receipts(env):
	"""Acceptance clause 2. Present is not the same as correct: a row that
	appeared but described the wrong thing would satisfy clause 1 and fail the
	human reading it."""
	store, path = env
	state = _ready(store)
	_broadcast(state, store, "baton.*", "testing broadcast reply each")
	row = _sent_notices(state)[0]

	assert row["subject"] == "testing broadcast reply each"
	assert row["kind"] == "announcement"
	# A notice has no recipient and must not borrow a directed message's
	# vocabulary to pretend otherwise.
	assert row["to_participant"] is None
	assert "state" not in row, \
		"a notice has no claim, so a directed state here would be invented"
	# Receipts, which is what a notice HAS in place of a claim. Nobody has
	# seen it yet.
	assert row["seen_count"] == 0
	assert row["expires_ts"] > row["created_ts"]

	# And the receipt count is live, not frozen at publication: a recipient
	# seeing it moves the number in the sender's view on the next poll.
	audience = {entry["participant"] for entry in core.dump(path)["notice_audience"]
	            if entry["notice_id"] == row["id"]}
	assert audience == {"baton.implementer", "baton.reviewer"}, audience
	store.see("baton.reviewer")
	state.refresh(store)
	assert _sent_notices(state)[0]["seen_count"] == 1


def test_the_broadcast_is_drawn_on_the_sent_screen(env):
	"""Acceptance clause 1, at the SCREEN rather than at the model. `o`
	switches to Sent; the subject and the notice glyph must be on it.

	The model check above would pass while the renderer dropped every notice
	row, which is exactly the shape of the reported symptom."""
	store, _ = env
	state = _ready(store)
	_broadcast(state, store, "baton.*", "testing broadcast reply each")
	_press(state, store, ord("o"))
	assert state.view == VIEW_SENT

	screen = _screen(state)
	assert "testing broadcast reply each" in screen, screen
	line = [row for row in screen.splitlines()
	        if "testing broadcast reply each" in row][0]
	assert "N" in line, f"the notice glyph is missing from the row: {line!r}"


def test_a_global_broadcast_is_shown_the_same_way(env):
	"""The reported case was scoped, but a global notice takes the other
	branch at the one place the TUI spelling becomes the protocol's
	(`scope=None`). A fix that read the scope to decide what to list would
	pass the scoped case and fail here."""
	store, path = env
	state = _ready(store)
	_broadcast(state, store, None, "for all of us")

	rows = _sent_notices(state)
	assert len(rows) == 1, f"a global notice is missing from Sent: {state.status}"
	assert rows[0]["subject"] == "for all of us"
	audience = {entry["participant"] for entry in core.dump(path)["notice_audience"]
	            if entry["notice_id"] == rows[0]["id"]}
	assert audience == {"baton.implementer", "baton.reviewer", "web.lead",
	                    "human.slawomir"}


def test_the_broadcast_does_not_land_in_the_senders_inbox_instead(env):
	"""The symptom's near neighbour, and the reason "it is somewhere" is not
	the same as "it is in Sent". A global notice's audience includes its
	author, so an implementation could satisfy a naive search of the screen
	while putting the sender's own broadcast in the wrong pane."""
	store, _ = env
	state = _ready(store)
	_broadcast(state, store, None, "for all of us")

	assert state.view != VIEW_SENT, "this test is about the INBOX view"
	inbox = [row for row in state.rows
	         if row.get("subject") == "for all of us"
	         and row.get("row_type") != "notice"]
	assert not inbox, f"the sender's own broadcast entered the inbox: {inbox}"
	assert _sent_notices(state), "and it is not in Sent either"


def test_several_broadcasts_stay_newest_first(env):
	"""Ordering is part of "accurate": the one you just sent is the one you
	are looking for, and it belongs at the top.

	ONLY ACROSS A SECOND BOUNDARY, which is why this test waits. `list_sent`
	orders by `(created_ts, id)` and `created_ts` has one-second resolution,
	so two broadcasts published inside the same second are ordered by a
	`token_hex` id — arbitrarily. Written without the wait, this test asserted
	`third, second, first` and got `third, first, second`. Reported to review
	rather than papered over: the wait makes this test measure the ordering
	rule, and the same-second case is measured for what it actually
	guarantees below."""
	import time

	store, _ = env
	state = _ready(store)
	_broadcast(state, store, "baton.*", "first broadcast")
	time.sleep(1.05)
	_broadcast(state, store, None, "second broadcast")

	subjects = [row["subject"] for row in _sent_notices(state)]
	assert subjects == ["second broadcast", "first broadcast"], subjects


def test_broadcasts_published_within_one_second_are_all_present(env):
	"""What the same-second case DOES guarantee, stated so a future reader
	does not mistake the silence above for a promise.

	Order among them is the id's, not the sender's. Completeness is not
	negotiable either way: a tie must not drop a row."""
	store, _ = env
	state = _ready(store)
	_broadcast(state, store, "baton.*", "one")
	_broadcast(state, store, "baton.*", "two")
	_broadcast(state, store, None, "three")

	rows = _sent_notices(state)
	assert {row["subject"] for row in rows} == {"one", "two", "three"}
	assert len({row["id"] for row in rows}) == 3, "a tie collapsed two rows"
