"""`/` filters the message list by author and subject, and reads nothing.

Slawomir's request, scoped by his ruling on 2026-08-11: metadata only, author
and subject, no body search. The scope is not a simplification — `Store.
preview_message` returns headers only and says why, so the body of an unread
message does not exist to a reader who has not claimed it. A search that could
read one would be a search that answers mail on the human's behalf.

The rule these tests exist to defend, above all others: filtering is a VIEW.
It changes what is drawn and nothing else — not what is claimed, not what is
seen, not what the console believes the human still owes.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core
from baton_tui.render import layout_for, render
from baton_tui.state import (MODE_BROWSE, MODE_COMPOSE, MODE_SEARCH, VIEW_SENT,
                             InboxState, row_author, row_matches)


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
			"mailbox": {"name": "search"},
			"participants": {"acme.reviewer": {}, "acme.implementer": {},
			                 "ops.lead": {}},
			"roots": {}, "retention_days": 90,
		}, handle)
	core.init_instance(path)
	return path


@pytest.fixture
def env(tmp_path):
	path = _instance(tmp_path)
	with core.open_instance(path) as store:
		yield store, path


def _ready(store, participant="acme.implementer"):
	state = InboxState(participant)
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	return state


def _type(state, text):
	for char in text:
		state.search_type(char)


def _subjects(state):
	return [row.get("subject") for row in state.view_rows]


# -- the rule, without a store --------------------------------------------

def test_the_matcher_reads_author_and_subject_only():
	row = {"row_type": "message", "id": "1", "direction": "in",
	       "state": "pending", "from_participant": "ops.lead",
	       "to_participant": "acme.implementer", "subject": "Retry logic",
	       "kind": "implementation_handoff"}
	assert row_matches(row, "retry")
	assert row_matches(row, "ops.lead")
	# Case-insensitive both ways.
	assert row_matches(row, "RETRY") and row_matches(row, "OPS.LEAD")
	# Substring, not prefix.
	assert row_matches(row, "y log")
	# Fields that are NOT searched, ruled: kind, state, direction, id.
	assert not row_matches(row, "implementation_handoff")
	assert not row_matches(row, "pending")
	# An empty query matches everything rather than nothing, which is what
	# makes an empty box show the whole list instead of an empty one.
	assert row_matches(row, "")


def test_the_matcher_is_literal_not_a_pattern():
	"""Ruled: no regex. Addresses are dotted, so `.` as a wildcard would make
	`payments.` match `paymentsX` — a filter quietly returning rows the human
	did not ask for."""
	row = {"row_type": "message", "id": "1", "direction": "in",
	       "state": "pending", "from_participant": "paymentsX.bot",
	       "subject": "nothing here"}
	assert not row_matches(row, "payments.")
	# Regex metacharacters are literals, not syntax errors and not wildcards.
	starred = dict(row, subject="a * b")
	assert row_matches(starred, "*")
	assert not row_matches(row, "*")
	assert not row_matches(row, "(unclosed")


def test_the_matcher_folds_non_ascii_case():
	row = {"row_type": "message", "id": "1", "direction": "in",
	       "state": "pending", "from_participant": "münchen.ops",
	       "subject": "Straße update"}
	assert row_matches(row, "MÜNCHEN")
	assert row_matches(row, "straße")


def test_author_is_the_party_the_row_displays():
	"""Inbound shows who sent it; outbound and Sent rows show who it went to.
	Matching a field the human cannot see would look broken every time it
	hit."""
	inbound = {"row_type": "message", "id": "1", "direction": "in",
	           "from_participant": "ops.lead", "to_participant": "me.here"}
	outbound = {"row_type": "message", "id": "2", "direction": "out",
	            "from_participant": "me.here", "to_participant": "ops.lead"}
	assert row_author(inbound) == "ops.lead"
	assert row_author(outbound) == "ops.lead"
	# A SENT row carries no direction and no from_participant at all.
	assert row_author({"id": "3", "to_participant": "ops.lead"}) == "ops.lead"


# -- entering and leaving --------------------------------------------------

def test_slash_enters_search_only_from_browse(env):
	store, _ = env
	state = _ready(store)
	assert state.begin_search() is True
	assert state.mode == MODE_SEARCH
	state.cancel_search()

	# From a compose mode it must refuse: the next keystrokes belong to the
	# message being written.
	state.mode = MODE_COMPOSE
	assert state.begin_search() is False
	assert state.mode == MODE_COMPOSE


def test_the_help_screen_lists_the_binding(env):
	from baton_tui import keys as K
	store, _ = env
	state = _ready(store)
	state.open_help()
	screen = "\n".join(render(state, 100, 40))
	assert "/" in screen and "author or subject" in screen
	# From the SHARED key table, so help cannot advertise a key that is not
	# bound: `/` in browse maps to the search event.
	assert K.map_key(ord("/"), MODE_BROWSE) == (K.SEARCH, None)


def test_typing_filters_and_accepting_keeps_the_filter(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Retry logic", body=b"x\n")
	store.send("ops.lead", "acme.implementer", kind="q",
	           subject="Deploy window", body=b"x\n")
	state = _ready(store)
	assert len(state.rows) == 2

	state.begin_search()
	_type(state, "retry")
	assert _subjects(state) == ["Retry logic"]
	state.accept_search()
	assert state.mode == MODE_BROWSE
	# The filter SURVIVES: the human filtered in order to act on the result.
	assert _subjects(state) == ["Retry logic"]
	assert state.searching is True


def test_escape_clears_the_filter_entirely(env):
	"""`/` then Esc is the only way back to the whole list, so Esc must clear
	rather than restore the query the box was seeded with."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Retry logic", body=b"x\n")
	store.send("ops.lead", "acme.implementer", kind="q",
	           subject="Deploy window", body=b"x\n")
	state = _ready(store)
	state.begin_search()
	_type(state, "retry")
	state.accept_search()
	assert len(state.rows) == 1

	state.begin_search()
	assert state.search_draft == "retry", "the box edits the filter in force"
	state.cancel_search()
	assert state.mode == MODE_BROWSE
	assert state.searching is False
	assert len(state.rows) == 2


def test_backspace_and_clear_widen_the_result(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Retry logic", body=b"x\n")
	store.send("ops.lead", "acme.implementer", kind="q",
	           subject="Retry budget", body=b"x\n")
	state = _ready(store)
	state.begin_search()
	_type(state, "retry l")
	assert _subjects(state) == ["Retry logic"]
	state.search_backspace()
	state.search_backspace()
	assert sorted(_subjects(state)) == ["Retry budget", "Retry logic"]
	state.search_clear()
	assert state.search_draft == ""
	assert len(state.view_rows) == 2


def test_a_query_matching_nothing_empties_the_list_and_says_so(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Retry logic", body=b"x\n")
	state = _ready(store)
	state.begin_search()
	_type(state, "zzzz")
	assert state.view_rows == []
	assert state.selected is None, "no row may be selected out of an empty list"
	assert "no match" in state.status
	# And it is recoverable, not a dead end.
	state.cancel_search()
	assert len(state.rows) == 1


# -- the safety property ---------------------------------------------------

def test_searching_claims_nothing_and_sees_nothing(env):
	"""The whole point. Compared against a full public dump, so a claim, a
	receipt or any state transition introduced by filtering shows up."""
	store, path = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Unread and pending", body=b"x\n")
	store.send_notice("acme.reviewer", kind="ann", subject="Unseen broadcast",
	                  body=b"n\n")
	state = _ready(store)
	before = core.dump(path)

	state.begin_search()
	for text in ("u", "n", "r", "e", "a", "d"):
		state.search_type(text)
	state.search_backspace()
	state.accept_search()
	state.begin_search()
	state.cancel_search()

	assert core.dump(path) == before

	# Said again in the terms the finding uses, because a dump comparison is
	# only as clear as the reader's memory of what it covers.
	rows = {row["subject"]: row for row in state.rows}
	assert rows["Unread and pending"]["state"] == "pending"
	assert rows["Unseen broadcast"]["state"] != "seen"


def test_a_filter_never_reduces_what_you_owe(env):
	"""The most dangerous thing search could do is make an obligation
	disappear from the count a human scans for."""
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Owed and hidden", body=b"x\n")
	store.claim("acme.implementer", message_id=mid)
	state = _ready(store)
	owed = state.unresolved_count()
	assert owed == 1

	state.begin_search()
	_type(state, "zzzz")
	assert state.view_rows == [], "the owed row is filtered out of sight"
	assert state.unresolved_count() == owed, "but it is still owed"
	assert f"{owed} awaiting" in render(state, 100, 24)[0]


def test_the_header_says_a_filter_is_active(env):
	"""A filtered list that does not announce itself is indistinguishable
	from a mailbox that lost messages."""
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i}", body=b"x\n")
	state = _ready(store)
	assert "3 retained" in render(state, 100, 24)[0]

	state.begin_search()
	_type(state, "message 1")
	header = render(state, 100, 24)[0]
	assert "1 of 3" in header and "message 1" in header


def test_an_open_claim_survives_being_filtered_out_of_sight(env):
	"""Filtering hides a row; it does not answer it, and it must not make the
	console forget which claim the human is holding."""
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Opened work", body=b"x\n")
	state = _ready(store)
	state.open_selected(store)
	assert state.opened is not None and state.opened["id"] == mid

	state.begin_search()
	_type(state, "zzzz")
	state.accept_search()
	assert state.view_rows == []
	assert state.opened is not None and state.opened["id"] == mid

	# AND ACROSS THE POLL, which is where the target is actually revalidated.
	# Without this the test passes even when revalidation reads the filtered
	# list -- verified by breaking it deliberately and watching it stay green.
	# The console polls every two seconds; a human who filters and then waits
	# is the ordinary case, not a contrived one.
	state.refresh(store)
	assert state.view_rows == []
	assert state.opened is not None and state.opened["id"] == mid, \
		"a view filter must not make the console forget a claim it holds"


# -- selection, refresh, and the Sent view ---------------------------------

def test_the_selection_follows_the_row_not_the_index(env):
	store, _ = env
	for subject in ("Alpha", "Beta", "Gamma retry"):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=subject, body=b"x\n")
	state = _ready(store)
	# Newest first, so put the cursor on the one that will survive the filter.
	for index, row in enumerate(state.rows):
		if row["subject"] == "Gamma retry":
			state.cursor = index
	assert state.selected["subject"] == "Gamma retry"

	state.begin_search()
	_type(state, "retry")
	assert state.selected["subject"] == "Gamma retry", \
		"the human stays on the row they were on"


def test_a_refresh_under_a_filter_admits_only_matches(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Retry logic", body=b"x\n")
	state = _ready(store)
	state.begin_search()
	_type(state, "retry")
	state.accept_search()
	assert len(state.rows) == 1

	store.send("ops.lead", "acme.implementer", kind="q",
	           subject="Deploy window", body=b"x\n")
	store.send("ops.lead", "acme.implementer", kind="q",
	           subject="Retry budget", body=b"x\n")
	state.refresh(store)

	assert sorted(_subjects(state)) == ["Retry budget", "Retry logic"]
	# The non-matching arrival is not lost, only unshown: it is in the full
	# set and in the retained count.
	assert state.retained_count == 3
	state.cancel_search()
	assert len(state.rows) == 3


def test_the_sent_view_is_searched_too(env):
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Handoff ready", body=b"x\n")
	store.send("acme.implementer", "ops.lead", kind="q",
	           subject="Budget question", body=b"x\n")
	state = _ready(store)
	state.select_view(VIEW_SENT)
	assert len(state.sent_rows) == 2

	state.begin_search()
	_type(state, "ops.lead")
	assert _subjects(state) == ["Budget question"], \
		"author in Sent is the party the row shows: the recipient"
	state.search_clear()
	_type(state, "handoff")
	assert _subjects(state) == ["Handoff ready"]


# -- rendering -------------------------------------------------------------

@pytest.mark.parametrize("columns,lines", [(100, 24), (60, 12), (44, 10)])
def test_a_filtered_screen_stays_within_its_dimensions(env, columns, lines):
	from baton_tui.safe_text import display_width
	store, _ = env
	for i in range(6):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i} with a fairly long subject line",
		           body=b"x\n")
	state = _ready(store)
	state.set_viewport(**(layout_for(columns, lines) or
	                      {"inbox_height": 1, "detail_height": 1}))
	state.begin_search()
	_type(state, "message 3")
	screen = render(state, columns, lines)
	assert len(screen) == lines
	assert all(display_width(line) <= columns for line in screen)


# -- the Sent cursor indexes the list it is drawn against ------------------
#
# R1 from review. `sent_cursor` indexes `sent_rows` — the FILTERED view — and
# two places read it out of `_all_sent_rows` instead. Under a filter that
# captures a different row than the one on screen, so a second narrowing
# keystroke moved the selection onto a neighbour even though the original still
# matched. A later open or materialize would then act on a row the human never
# chose, which is the wrong-target class this console exists to prevent.


def _sent_row(subject, index):
	"""A Sent row as `list_sent` shapes them: no `row_type`, no `direction`.

	The recipient is `ops.lead` for a reason the reviewer had to find for me:
	`acme.reviewer` contains an `m`, and search matches the OTHER PARTY as well
	as the subject. Every row therefore matched the first keystroke, nothing
	was filtered out, and the test could not fail however it was worded — I
	rewrote it three times looking for the defect in the assertions."""
	return {"id": f"id{index}", "subject": subject, "to_participant": "ops.lead",
	        "state": "pending", "created_ts": f"2026-08-11T10:0{index}:00Z",
	        "kind": "q"}


def test_a_filtered_sent_selection_stays_on_its_row_across_keystrokes(env):
	"""The reviewer's repro exactly, built from constructed rows.

	The rows are constructed rather than sent through the store because the
	defect is in index handling and the authority's ordering is not stable for
	messages created in the same second — my first attempt at this test landed
	the target at index 0, where the filtered and full index spaces agree and
	the bug cannot appear."""
	store, _ = env
	state = _ready(store)
	state.select_view(VIEW_SENT)
	state.sent_rows = [_sent_row("a no", 0), _sent_row("b match one", 1),
	                   _sent_row("c match two", 2)]
	state.sent_cursor = 2                        # NONZERO, past a non-match
	assert state.selected_in_view["subject"] == "c match two"

	state.begin_search()
	_type(state, "m")
	# THE FILTER ACTUALLY BIT. Without this the test can pass while nothing was
	# filtered at all, which is exactly how it passed against the broken code.
	assert [row["subject"] for row in state.sent_rows] == [
		"b match one", "c match two"], "the first keystroke filtered nothing"
	for typed in ("", "a"):
		if typed:
			_type(state, typed)
		assert state.selected_in_view["subject"] == "c match two", \
			f"typing {typed!r} moved the selection to another row"
		# AFTER EVERY KEYSTROKE. The cursor going out of range is how this
		# defect actually shows: `selected_in_view` clamps when read, so the
		# subject still looks right while the renderer and the scroll logic
		# use a cursor that points past the list they draw.
		# INDEXED DIRECTLY, not read through `selected_in_view`, which clamps:
		# clamping is what let a cursor pointing past the filtered list still
		# report the right subject while the renderer drew the highlight
		# somewhere else.
		assert state.sent_cursor < len(state.sent_rows), \
			f"typing {typed!r} left the cursor outside the drawn list"
		assert state.sent_rows[state.sent_cursor]["subject"] == "c match two", \
			f"typing {typed!r} left the cursor on the wrong drawn row"


def test_a_refresh_under_a_sent_filter_keeps_the_row_and_a_legal_cursor(env):
	"""Order-independent by construction: whatever row the cursor is on before
	the poll, it is on the same row after it, with a cursor inside the list
	that is actually drawn."""
	store, _ = env
	for subject in ("c match two", "b match one", "a no"):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=subject, body=b"x\n")
	state = _ready(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	state.begin_search()
	_type(state, "match")
	state.accept_search()
	assert len(state.sent_rows) == 2, [r["subject"] for r in state.sent_rows]
	state.sent_cursor = 1                        # the second match
	target = state.selected_in_view["id"]

	# A poll arrives, and a non-matching row lands among the full set.
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="z unrelated", body=b"x\n")
	state.refresh(store)

	assert state.selected_in_view["id"] == target, \
		"the refresh moved the selection off the row under the cursor"
	assert state.sent_cursor < len(state.sent_rows), \
		"the refresh left the cursor outside the filtered list"
	drawn = "\n".join(render(state, 100, 24))
	assert "z unrelated" not in drawn, "a non-matching arrival was drawn"


def test_clearing_a_sent_filter_does_not_jump_rows(env):
	store, _ = env
	for subject in ("c match two", "b match one", "a no"):
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=subject, body=b"x\n")
	state = _ready(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	state.begin_search()
	_type(state, "match")
	state.accept_search()
	state.sent_cursor = 1
	target = state.selected_in_view["id"]

	state.begin_search()
	state.cancel_search()
	assert state.selected_in_view["id"] == target, \
		"clearing the filter landed on a different row"
	assert len(state.sent_rows) == 3
	assert state.sent_cursor < len(state.sent_rows)
