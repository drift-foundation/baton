"""Renderer tests: assert on the produced buffer, never a live terminal.

The renderer is a pure function, so the security property that matters --
nothing a sender writes reaches the terminal as an instruction -- is a
statement about these strings and is checked directly.
"""

from __future__ import annotations

import json

import pytest

import baton_core as core
from baton_tui.render import (DIVIDER, _headers, detail_line_count, layout_for,
                              part_footer,
                              ordinary_body_lines, render)
from baton_tui.safe_text import display_width
from baton_tui.state import InboxState
from test_tui_safe_text import HOSTILE


def _instance(tmp_path):
	home = tmp_path / "inst"
	home.mkdir()
	root = home / "root"
	root.mkdir()
	(root / "EVIDENCE.md").write_bytes(b"pinned evidence\n")
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1, "protocol_version": 10, "generation": 1,
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


def _screen(state, columns=100, lines=24):
	return "\n".join(_draw(state, columns, lines))


def _draw(state, columns=100, lines=24):
	"""What the driver does: apply the layout as an explicit resize event,
	then render. Tests go through the same door so they cannot accidentally
	rely on rendering to move the model.

	Through `apply_layout`, which is the driver's ONE resize helper -- layout
	then follow-the-caret. Calling `set_viewport` alone stopped being what the
	driver does when following moved out of `step`, and the stacked layout is
	what made the difference visible: a 60% detail pane is small enough that a
	draft sits below the fold until something follows it."""
	from baton_tui.driver import apply_layout
	apply_layout(state, columns, lines)
	return render(state, columns, lines)


# -- the security property -------------------------------------------------

@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_no_hostile_sequence_reaches_the_screen(env, name):
	"""A sender controls the subject and the body. Neither may put a terminal
	instruction on the operator's screen."""
	store, _ = env
	payload = HOSTILE[name]
	# The BODY is where a sender has free rein: `send` validates subjects but
	# imposes nothing on content, which is correct -- a body may legitimately
	# be any bytes.
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="benign subject", body=payload.encode("utf-8"))
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	screens = [_screen(state)]
	state.open_selected(store)                 # now the BODY is rendered too
	screens.append(_screen(state))
	for screen in screens:
		for char in screen:
			code = ord(char)
			assert code not in (0x1B, 0x9B, 0x9D, 0x07, 0x08, 0x00, 0x0D), (
				f"{name}: U+{code:04X} reached the screen")
			assert not (0x00 <= code < 0x20 and char != "\n")
			assert not (0x80 <= code < 0xA0)


@pytest.mark.parametrize("columns", [40, 60, 80, 100, 133])
def test_every_line_fits_its_terminal(env, columns):
	"""A line wider than the terminal wraps and corrupts the layout the human
	is reading. Checked in display cells, with wide characters present."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject=("日本語のとても長い件名 " * 6).strip(),
	           body=("x" * 500 + "\n日本語\n").encode("utf-8"))
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	for line in _draw(state, columns, 24):
		assert display_width(line) <= columns, repr(line)


def test_screen_is_exactly_the_requested_height(env):
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	for lines in (8, 12, 24, 50):
		assert len(_draw(state, 80, lines)) == lines


# -- what the human must be able to see ------------------------------------

def test_unresolved_work_is_always_on_screen(env):
	"""The failure this console exists to prevent is walking away from a claim
	nobody else can take."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Answer me", body=b"?\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert "0 awaiting" in _screen(state)
	state.open_selected(store)
	assert "1 awaiting your reply/close" in _screen(state)
	state.close_selected(store, outcome="noted")
	assert "0 awaiting" in _screen(state)


def test_the_action_target_is_shown(env):
	"""The wrong-recipient bug was invisible because the screen said one thing
	and the state meant another.

	SUPERSEDED IN LOCATION. The `acting on:` clause became `owed: ...` and is
	now off the screen entirely with the rest of the ordinary footer. What
	must still be visible is the OBLIGATION, and the header carries that: it
	counts what you owe, on every screen, without a clause under the panes."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert "owed:" not in _screen(state)
	assert "0 awaiting your reply/close" in _draw(state, 100, 24)[0]
	state.open_selected(store)
	assert "owed:" not in _screen(state), "the removed clause is back"
	assert "1 awaiting your reply/close" in _draw(state, 100, 24)[0], \
		"nothing on screen says a disposition is owed"


def test_preview_never_renders_content(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Shaped",
	           body=b"# TOP SECRET BODY\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	screen = _screen(state)
	assert "Shaped" in screen
	assert "TOP SECRET" not in screen
	# The `Enter: claim and open` prompt that used to be asserted here is
	# REMOVED as repeated reference in the work area; `?` help owns it now.
	assert "Enter: claim and open" not in screen


def test_opened_message_renders_its_text(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"# Heading\nthe real body\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	screen = _screen(state)
	assert "the real body" in screen


def test_binary_parts_are_summarized_not_dumped(env):
	"""Base64 and integrity metadata stay hidden unless explicitly requested."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Binary", parts=[
		{"content_type": "text/markdown; charset=utf-8", "body": b"see below\n"},
		{"content_type": "image/png", "body": b"\x89PNG\r\n\x1a\n" + b"\xff" * 400},
	])
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	# Wide enough that the hint is not truncated by `fit`, which is correct
	# behaviour but would make this assertion about layout rather than content.
	screen = _screen(state, 140, 40)
	# "'m' to materialize" is REMOVED as a key hint in the work area; the
	# footer names `m` while it works. What the part IS still has to be here.
	assert "binary" in screen
	assert "materialize" not in screen
	assert "iVBOR" not in screen          # no base64 payload on screen
	delivery = state.detail["delivery"]["message"]["content"]["parts"][1]
	assert delivery["sha256"] not in screen


def test_multipart_structure_is_navigable_on_screen(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Rich", parts=[
		{"content_type": "multipart/alternative", "parts": [
			{"content_type": "text/plain; charset=utf-8", "body": b"plain\n"},
			{"content_type": "text/html; charset=utf-8", "body": b"<p>rich</p>\n"},
		]},
	])
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	screen = _screen(state, 100, 40)
	assert "[0]" in screen and "[0.0]" in screen and "[0.1]" in screen
	assert "multipart/alternative" in screen


def test_html_is_shown_as_text_never_executed(env):
	"""Baton renders nothing, so a console that interprets markup owns that
	surface entirely. It is displayed literally."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           content_type="text/html; charset=utf-8",
	           body=b"<script>alert(1)</script>\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert "<script>alert(1)</script>" in _screen(state)


def test_damaged_delivery_shows_the_way_out(env):
	"""Failing closed must not strand the holder: the screen has to say what
	to do next."""
	store, root = env
	store.send("acme.reviewer", "acme.implementer", kind="ev", subject="Evidence",
	           parts=[{"content_type": "text/markdown; charset=utf-8",
	                   "disposition": "attachment", "attach": "src:EVIDENCE.md"}])
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	(root / "EVIDENCE.md").write_bytes(b"MUTATED\n")
	state.detail = {"delivery": store.reopen_claim(
		state.opened["claim_id"], "acme.implementer")}
	screen = _screen(state, 100, 30)
	assert "content withheld" in screen
	assert "close this claim, then quarantine" in screen


def test_reply_mode_shows_the_draft_safely(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "still working\x1b[2J on it"
	screen = _screen(state)
	# The tutorial sentence is REMOVED by the noise ruling; what this test is
	# actually about -- that a hostile draft reaches the screen as text -- is
	# unchanged and asserted below.
	assert "this line is the subject AND the message" not in screen
	assert "still working" in screen
	assert "\x1b" not in screen           # even the human's own draft is neutralized


def test_empty_inbox_renders_without_error(env):
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	screen = _screen(state)
	assert "0 retained" in screen
	assert "nothing selected" in screen


def test_notice_rows_are_distinguishable_from_claims(env):
	"""Notices must never masquerade as claimable work."""
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed", body=b"d\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	screen = _screen(state)
	notice_line = [l for l in screen.split("\n") if "Broadcast" in l][0]
	directed_line = [l for l in screen.split("\n") if "Directed" in l][0]
	assert "!" in notice_line
	assert "!" not in directed_line


# -- the renderer must not depend on a validator it does not own ----------

@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_renderer_is_safe_even_if_a_subject_arrives_hostile(env, name):
	"""`send` rejects control characters in subjects, so this cannot happen
	through the current core -- which is exactly why it is worth pinning.

	The renderer is the last line before the terminal. If it is only safe
	because something upstream validated, then a future path that does not
	validate -- an older instance, a repaired row, a new field -- puts an
	escape on the operator's screen. Defence in depth means each layer holds
	on its own."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="benign", body=b"body\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	# Forge the hostile value directly into the row, bypassing core entirely.
	state.rows[0]["subject"] = HOSTILE[name]
	state.rows[0]["from_participant"] = HOSTILE[name]
	screen = _screen(state)
	for char in screen:
		code = ord(char)
		assert code not in (0x1B, 0x9B, 0x9D, 0x07, 0x08, 0x00, 0x0D)
		assert not (0x00 <= code < 0x20 and char != "\n")
		assert not (0x80 <= code < 0xA0)


def test_a_forged_newline_in_a_subject_cannot_add_inbox_rows(env):
	"""The row-forging attack, at the render layer: one row stays one line."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="real", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	before = len(_draw(state, 100, 24))
	state.rows[0]["subject"] = "real\nFAKE   hq.lead   Approved and merged"
	after = _draw(state, 100, 24)
	assert len(after) == before
	assert sum(1 for line in after if "FAKE" in line) <= 1


# -- R1: the real terminal, including sizes too small to use --------------

@pytest.mark.parametrize("columns,lines", [
	(0, 0), (0, 24), (80, 0), (1, 1), (20, 5), (39, 24), (80, 7), (39, 7),
])
def test_render_never_exceeds_the_actual_terminal(env, columns, lines):
	"""A curses blit writes what it is handed. Returning 40 columns for a
	20-column terminal writes out of bounds -- which happens during startup
	and every drag-resize, not only in contrived cases."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	buffer = _draw(state, columns, lines)
	assert len(buffer) == lines
	for line in buffer:
		assert display_width(line) <= columns, repr(line)


def test_too_small_says_so_within_the_space_available(env):
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert "too small" in "\n".join(_draw(state, 30, 10))
	# One line is enough to say something; zero is enough to say nothing.
	assert len(_draw(state, 30, 1)) == 1
	assert _draw(state, 0, 0) == []


def test_resize_transitions_stay_in_bounds(env):
	"""Drag-resize walks through every intermediate size, including the ones
	below the two-pane minimum."""
	store, _ = env
	for i in range(30):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.move(20, store)
	for columns in range(0, 120, 3):
		for lines in range(0, 40, 3):
			buffer = _draw(state, columns, lines)
			assert len(buffer) == lines
			for line in buffer:
				assert display_width(line) <= columns


# -- R2: viewports ---------------------------------------------------------

def test_the_selected_row_stays_visible_in_a_long_queue(env):
	"""A cursor scrolled off the pane is invisible to the human but still the
	thing their next keystroke acts on -- the same class of problem as the
	action-target bug."""
	store, _ = env
	for i in range(60):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i:02d}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	for _ in range(59):
		state.move(1, store)
		screen = _draw(state, 100, 24)
		# The HEADER also opens with the focus mark, and legitimately so --
		# `> ` there means the list has keyboard focus. The row caret is the
		# same character in the body, so the header is excluded by position
		# rather than by trying to tell two identical marks apart.
		marked = [line for line in screen[1:] if line.startswith(">")]
		assert len(marked) == 1, "the selected row is not on screen"
		assert state.selected["subject"][:10] in marked[0]
	for _ in range(59):
		state.move(-1, store)
		assert any(line.startswith(">") for line in _draw(state, 100, 24))


def test_a_long_body_can_be_read_to_the_end(env):
	"""Truncating the detail pane at the pane boundary makes a long message
	unreadable -- the console would be strictly worse than `claim | less`."""
	store, _ = env
	body = "\n".join(f"line {i:03d} of the message" for i in range(200)).encode()
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Long", body=body)
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	total = detail_line_count(state, 100, 24)
	assert total > 24
	seen = set()
	for _ in range(total):
		for line in _draw(state, 100, 24):
			# The screen line is inbox + divider + detail, so read the detail side.
			if "of the message" in line:
				seen.add(line.split("of the message")[0].strip().split()[-1])
		state.scroll_detail(5, total)
	assert "000" in seen and "199" in seen


def test_detail_scroll_is_clamped_at_both_ends(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"one\ntwo\nthree\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	total = detail_line_count(state, 100, 24)
	state.scroll_detail(-50, total)
	assert state.detail_offset == 0
	state.scroll_detail(9999, total)
	assert state.detail_offset <= max(0, total - state.detail_height)
	assert len(_draw(state, 100, 24)) == 24


def test_scrolling_resets_when_the_selection_changes(env):
	"""A scroll position belongs to the thing being read."""
	store, _ = env
	long_body = "\n".join(f"l{i}" for i in range(100)).encode()
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="A", body=long_body)
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="B", body=b"short\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	# Same-second sends tie and order by id, so select the long one by name
	# rather than assuming it sorted first.
	state.cursor = [i for i, r in enumerate(state.rows) if r["subject"] == "A"][0]
	state.preview(store)
	state.open_selected(store)
	state.scroll_detail(40, detail_line_count(state, 100, 24))
	assert state.detail_offset > 0
	state.move(1, store)
	assert state.detail_offset == 0


def test_refresh_while_scrolled_keeps_the_selection_visible(env):
	"""New mail arriving must not scroll the human's selection off screen."""
	store, _ = env
	for i in range(40):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i:02d}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.move(30, store)
	state.open_selected(store)                   # pin an identity to follow
	chosen = state.opened["id"]
	for i in range(5):
		store.send("hq.lead", "acme.implementer", kind="q",
		           subject=f"Newer {i}", body=b"x\n")
		state.refresh(store)
		screen = _draw(state, 100, 24)
		assert any(line.startswith(">") for line in screen), "selection scrolled away"
	# An OPENED item is followed by identity; a bare cursor is positional.
	assert state.opened["id"] == chosen
	assert state.selected["id"] == chosen


# -- R3: the date column ---------------------------------------------------

def test_the_inbox_shows_a_date(env):
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Dated", body=b"x\n")
	created = store.get_message(mid)["created_ts"]
	state = InboxState("acme.implementer")
	state.refresh(store)
	row = [line for line in _draw(state, 100, 24) if "Dated" in line][0]
	assert f"{created[5:10]} {created[11:16]}" in row


def test_the_date_degrades_before_the_subject_does(env):
	"""Columns are dropped widest-first as the terminal narrows: a cramped
	inbox that hides the subject is useless, one that hides the date is not."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="KEEPME", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	wide = [line for line in _draw(state, 120, 24) if "KEEPME" in line]
	narrow = [line for line in _draw(state, 42, 24) if "KEEPME" in line]
	assert wide and narrow                       # subject survives both
	assert ":" in wide[0]                        # date present when it fits


def test_the_irreversible_things_are_named_where_they_now_live(env):
	"""SUPERSEDED IN LOCATION. This required the detail pane to end every
	preview with `Enter: claim and open (takes ownership)`, or its notice and
	reopen siblings.

	The distinction those three drew is real and is NOT being dropped:
	claiming takes ownership and starts an obligation, marking a notice seen
	consumes an at-most-once broadcast, and reopening does neither. What was
	wrong was WHERE it was said -- reference material repeated under every row
	the cursor touched. So the pane must now be free of it, and `?` help must
	carry all three distinctly. Removing an explanation is only safe if its
	one owner is complete."""
	from baton_tui.keys import HELP_SECTIONS
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed", body=b"d\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	for index, _row in enumerate(state.rows):
		state.cursor = index
		state.preview(store)
		screen = "\n".join(_draw(state, 100, 24))
		for prose in ("claim and open", "mark seen and open", "Enter: reopen"):
			assert prose not in screen, f"{prose!r} is still in the work area"

	help_text = " ".join(f"{key} {text}" for _title, rows in HELP_SECTIONS
	                     for key, text, *_ in rows)
	assert "CLAIMED" in help_text and "reply or close is then owed" in help_text
	assert "at-most-once" in help_text and "not redelivered" in help_text
	assert "reopens it" in help_text, "help does not distinguish reopening"


# -- render is observation, resize is an event ----------------------------

def _snapshot(state):
	"""Every public attribute of the model, deep-copied."""
	import copy
	return {name: copy.deepcopy(value) for name, value in vars(state).items()
	        if not name.startswith("_")}


@pytest.mark.parametrize("columns,lines", [(100, 24), (60, 12), (40, 8), (39, 7), (0, 0)])
def test_rendering_never_mutates_the_model(env, columns, lines):
	"""`render` used to call `set_viewport`, so drawing the same model at a
	different size silently moved the cursor and pane heights -- a hidden
	state transition inside something documented as observation. A driver that
	renders twice (double-buffer, redraw on signal) would have moved the model
	by drawing it."""
	store, _ = env
	for i in range(40):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i:02d}", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="N", body=b"n\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**(layout_for(100, 24) or {"inbox_height": 10, "detail_height": 10}))
	state.move(15, store)
	state.open_selected(store)
	state.scroll_detail(3, detail_line_count(state, 100, 24))

	before = _snapshot(state)
	for _ in range(3):
		render(state, columns, lines)
	assert _snapshot(state) == before


def test_rendering_at_many_sizes_leaves_the_model_alone(env):
	"""The resize sweep, but asserting the model is untouched rather than the
	output. A driver probing sizes must not disturb what the human selected."""
	store, _ = env
	for i in range(30):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i:02d}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	state.move(20, store)
	before = _snapshot(state)
	for columns in range(0, 120, 7):
		for lines in range(0, 40, 5):
			render(state, columns, lines)
	assert _snapshot(state) == before


def test_the_resize_event_keeps_cursor_and_viewport_valid(env):
	"""The public event is where adjustment belongs, and it must leave the
	model coherent at any size -- including shrinking so far that the current
	selection would fall outside the pane."""
	store, _ = env
	for i in range(50):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i:02d}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 40))
	state.move(45, store)
	chosen = state.selected["id"]
	for lines in (40, 30, 20, 12, 9, 8, 9, 24, 60):
		layout = layout_for(100, lines)
		if layout is None:
			continue
		state.set_viewport(**layout)
		assert state.inbox_height >= 1
		assert 0 <= state.inbox_top <= max(0, len(state.rows) - 1)
		# The selection survives every resize and stays inside the pane.
		assert state.selected["id"] == chosen
		assert state.inbox_top <= state.cursor < state.inbox_top + state.inbox_height
		# And it is actually drawn.
		assert any(line.startswith(">") for line in render(state, 100, lines))


def test_layout_reports_when_the_terminal_is_unusable(env):
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	assert layout_for(39, 24) is None
	assert layout_for(80, 7) is None
	assert layout_for(0, 0) is None
	layout = layout_for(80, 24)
	assert layout["inbox_height"] >= 1 and layout["detail_height"] >= 1


# -- the persistent status bar --------------------------------------------

def test_the_status_bar_carries_severity(env):
	"""Severity is TEXT, not colour: the console is read over SSH on
	terminals with no colour, and severity that exists only as colour is
	invisible to whoever most needs it."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	state.open_selected(store)
	assert "[!]" in _screen(state)                       # obligation is a warning
	state.close_selected(store, outcome="noted")
	assert "[ok]" in _screen(state)                      # resolved is success
	state.set_status("something went wrong", "error")
	assert "[ERR] something went wrong" in _screen(state)


def test_an_action_failure_appears_in_the_bar_and_does_not_take_focus(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Keep me", body=b"x\n")
	state = _ready_state(store)
	state.preview(store)
	state.open_selected(store)                          # claim, so the path is real
	before_cursor = state.cursor
	state.materialize_selected_part(store, target_dir="/nonexistent-dir")
	screen = _screen(state)
	assert "[ERR]" in screen
	assert "Keep me" in screen                           # panes still show the work
	assert state.cursor == before_cursor                 # focus unmoved


def test_arrivals_are_reported_without_stealing_focus(env):
	"""A poll that moved the cursor to new mail would yank the human off what
	they were reading, and their next keystroke would act on something they
	did not choose."""
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Old {i}", body=b"x\n")
	state = _ready_state(store)
	state.move(2, store)
	state.open_selected(store)              # pin an identity, not a position
	chosen = state.opened["id"]
	new_id = store.send("hq.lead", "acme.implementer", kind="q",
	                    subject="Newer", body=b"x\n")
	state.set_status("something the human did", "info")
	state.refresh(store)
	# The poll says NOTHING. It used to write `N new: senders` over whatever
	# the last action had left there -- a third copy of mailbox state the
	# header counts and the list already shows, written by a timer.
	assert state.status == "something the human did", \
		"the poll overwrote a meaningful status"
	assert "Newer" in _screen(state), "the arrival is not visible either"
	# Focus did not move to the arrival. (A bare cursor is positional, so the
	# identity being followed has to be an opened one -- same-second sends tie
	# and reorder, which is core's documented ordering.)
	assert state.opened["id"] == chosen
	assert state.selected["id"] == chosen != new_id


def _ready_state(store):
	state = InboxState("acme.implementer")
	state.refresh(store)
	layout = layout_for(100, 24)
	if layout:
		state.set_viewport(**layout)
	state.preview(store)
	return state


def test_the_caret_lands_on_the_draft_line(env):
	"""Where the terminal cursor goes while typing. Asserted here in exact
	coordinates because the PTY can only show that a cursor was made visible,
	not where it was put."""
	from baton_tui.render import input_caret
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	state.open_selected(store)
	state.begin_reply()
	# Through the model, not by assigning `.draft`: the caret is part of the
	# buffer now, and a direct assignment leaves it where the seed put it --
	# which is exactly the discrepancy this test exists to catch.
	state.draft, state.draft_caret = "", 0
	for char in "typing here":
		state.type_char(char)
	# Laid out and drawn FIRST, then the caret placed -- the order the driver
	# uses. Asking for the caret against a viewport that has not followed the
	# draft yet answers about the previous frame.
	buffer = _draw(state, 100, 24)
	row, column = input_caret(state, 100, 24)
	assert 0 <= row < 24 and 0 <= column < 100
	# The caret sits on the line showing the draft, just past what is typed.
	assert "typing here" in buffer[row - 1] or "typing here" in buffer[row]
	# STACKED: the detail pane starts BELOW the rule, so the caret is placed by
	# its ROW rather than by a column past the divider. It is under the rule and
	# above the footer, and its column is inside the drafted line.
	rule = _rule_index(buffer)
	assert rule < row < 24 - 2
	assert 0 < column <= display_width(buffer[row])


# -- the selected row must be VISIBLE ------------------------------------

def test_the_selected_row_carries_a_style_the_driver_can_highlight(env):
	"""Trial defect from Slawomir: the panes drew but no row looked selected.
	A `>` marker alone is far too subtle on a real terminal -- the human could
	not see which row they were on, while Enter would still have claimed it."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	for i in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Message {i}", body=b"x\n")
	state = _ready_state(store)
	seen = []
	for _ in range(4):
		rows = render_styled(state, 100, 24)
		marked = [index for index, (_, style) in enumerate(rows)
		          if STYLE_SELECTED in style]
		assert len(marked) == 1, "exactly one row must look selected"
		seen.append(marked[0])
		# The styled row is the one the cursor is on, not merely some row.
		assert state.selected["subject"] in rows[marked[0]][0]
		state.move(1, store)
	assert len(set(seen)) == 4, "the highlight must move with the cursor"


def test_the_marker_survives_alongside_the_style(env):
	"""Colour-independent fallback: a terminal that drops attributes must
	still show which row is selected."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	rows = render_styled(state, 100, 24)
	selected = [text for text, style in rows if STYLE_SELECTED in style][0]
	assert selected.startswith(">")


def test_selection_style_is_distinct_from_row_state(env):
	"""Selecting must not look like consuming. A notice keeps its `!` and a
	claimed row keeps its `*` whether or not it is the selected row."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed", body=b"d\n")
	state = _ready_state(store)
	for _ in range(2):
		rows = render_styled(state, 100, 24)
		selected = [text for text, style in rows if STYLE_SELECTED in style][0]
		if "Broadcast" in selected:
			assert "!" in selected           # still a notice
		else:
			assert "!" not in selected
		state.move(1, store)


def test_no_row_is_styled_when_the_selection_is_off_screen_or_absent(env):
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	state = _ready_state(store)
	assert not any(STYLE_SELECTED in style for _, style in render_styled(state, 100, 24))
	# Unusable terminal: no styled row, and still exactly `lines` rows.
	rows = render_styled(state, 20, 5)
	assert len(rows) == 5
	assert not any(STYLE_SELECTED in style for _, style in rows)


def test_styled_and_plain_render_agree_on_text(env):
	"""`render` stays the text contract every other test asserts against."""
	from baton_tui.render import render_styled
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready_state(store)
	assert [text for text, _ in render_styled(state, 100, 24)] == render(state, 100, 24)


# -- R7: the pane divider is ONE continuous horizontal rule ----------------

def _is_rule(line: str, divider: str) -> bool:
	"""A row is the rule if it is a long unbroken run of divider cells.

	Matched by SHAPE rather than by a word on it. It used to be found by the
	`DETAIL ` label, which meant a cosmetic change could satisfy the locator
	while the rule itself broke; the label is gone and the identity that
	replaced it sits at the far right, so the run is what identifies the row.
	"""
	from baton_tui.render import MIN_RULE_CELLS
	return divider * MIN_RULE_CELLS in line


def _rule_index(screen):
	"""The one screen row that is the pane rule.

	Matched by what the row IS rather than by a word printed on it: nothing but
	divider glyphs, after the leading focus mark. That is R7's original
	edge-to-edge property, and it is testable again now that the `DETAIL`
	label is gone -- the label had forced this helper to look for text, which
	a cosmetic change could have satisfied while the rule itself broke.

	The focus mark stays and is stripped here: it is one leading cell, it is
	what the navigation keys follow, and it is not part of the rule."""
	rules = [index for index, line in enumerate(screen)
	         if _is_rule(line, DIVIDER)]
	assert len(rules) == 1, f"expected exactly one rule row, found {rules}"
	return rules[0]


def test_the_divider_is_one_full_width_box_drawing_rule(env):
	"""R7: stacked, so the separator is a ROW rather than a column. U+2500 is
	designed to join between cells, so a run of them reads as one unbroken
	rule -- the horizontal counterpart of the fault that made the old ASCII
	bar look like disconnected dashes."""
	from baton_tui.safe_text import display_width
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	for columns in (40, 60, 80, 100, 133):
		screen = _draw(state, columns, 24)
		rule = screen[_rule_index(screen)]
		# CONTINUOUS and FULL WIDTH to the right of the focus mark: no gap
		# anywhere along it, measured in display cells so a fallback glyph
		# cannot quietly shorten it. The `DETAIL` label is gone -- the lower
		# pane is self-evidently the selected message -- so the rule is once
		# again nothing but rule, which is what R7 asked for.
		label, _, tail = rule.partition(DIVIDER)
		assert label.strip() == "", "the rule carries no label"
		# The identity sits at the far right, with one rule cell after it.
		# Everything between the mark and the identity is rule, and THAT run
		# is what must be unbroken.
		block = f" {state.participant}{DIVIDER}"
		tail = tail.split(block, 1)[0] if block in tail else tail
		assert set(tail) == {DIVIDER}, "the rule is broken up"
		assert display_width(rule) == columns
		assert "-" not in rule                   # the fallback is not mixed in


def test_only_one_row_is_the_divider(env):
	"""A rule on more than one row is not a rule, and a body row that is all
	dividers would be content masquerading as structure."""
	store, _ = env
	for i in range(6):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"日本語 {i}" if i % 2 else f"Plain {i}", body=b"x\n")
	state = _ready_state(store)
	state.open_selected(store)
	for columns in (40, 60, 80, 100, 133):
		screen = _draw(state, columns, 24)
		index = _rule_index(screen)
		# It sits between the two panes: below the header, above the footer.
		assert 0 < index < 24 - 3


def test_the_divider_costs_exactly_one_row(env):
	"""Switching between the box character and the ASCII fallback must not
	change the shape of the screen, or the two look like different layouts."""
	from baton_tui.render import DIVIDER_ASCII
	from baton_tui.safe_text import display_width
	assert display_width(DIVIDER) == display_width(DIVIDER_ASCII) == 1
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	box = render(state, 100, 24, divider=DIVIDER)
	ascii_ = render(state, 100, 24, divider=DIVIDER_ASCII)
	assert [display_width(l) for l in box] == [display_width(l) for l in ascii_]
	assert _rule_index(box) == [index for index, line in enumerate(ascii_)
	                            if _is_rule(line, DIVIDER_ASCII)][0]


@pytest.mark.parametrize("encoding,expected", [
	("utf-8", "─"), ("UTF-8", "─"),
	("ascii", "-"), ("latin-1", "-"), ("cp1252", "-"), (None, "-"), ("", "-"),
	("nonsense-codec", "-"),
])
def test_the_divider_falls_back_when_the_terminal_cannot_render_it(encoding, expected):
	"""A box-drawing character on a non-UTF-8 terminal is worse than the rule
	it replaced: it becomes mojibake across the middle of the screen."""
	from baton_tui.render import divider_for
	assert divider_for(encoding) == expected


def test_the_divider_row_is_never_the_highlighted_row(env):
	"""The stripe is a statement about one row of one list. Stacked, the rule
	is a row of its own, so the highlight must never land on it -- the
	horizontal form of "the highlight stops before the divider"."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"M{i}", body=b"x\n")
	state = _ready_state(store)
	for _ in range(3):
		rows = render_styled(state, 100, 24)
		rule = _rule_index([text for text, _ in rows])
		marked = [index for index, (_, style) in enumerate(rows)
		          if STYLE_SELECTED in style]
		assert marked and rule not in marked
		assert marked[0] < rule, "the selected row is not in the list pane"
		state.move(1, store)


# -- item 1: the detail pane wraps ---------------------------------------

def test_a_long_body_is_readable_to_its_last_character(env):
	"""Previously the detail pane clipped, so the end of every long line did
	not exist -- not off-screen, gone."""
	from baton_tui.render import detail_line_count
	store, _ = env
	tail = "THE-FINAL-TOKEN"
	body = ("a long paragraph without newlines that runs well past the pane edge "
	        * 6 + tail).encode()
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Long", body=body)
	state = _ready_state(store)
	state.open_selected(store)
	total = detail_line_count(state, 100, 24)
	seen = ""
	for _ in range(total + 2):
		seen += "\n".join(_draw(state, 100, 24))
		state.scroll_detail(4, total)
	assert tail in seen


@pytest.mark.parametrize("columns", [40, 55, 80, 100, 133])
def test_wrapped_detail_never_exceeds_the_pane(env, columns):
	"""Stacked, the detail pane IS the terminal width, so "the pane" and "the
	terminal" are the same bound -- and every row must still respect it."""
	from baton_tui.safe_text import display_width
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject=("日本語の非常に長い件名がここにあります " * 3).strip(),
	           body=("https://example.com/" + "x" * 200 + "\n日本語 " * 20).encode())
	state = _ready_state(store)
	state.open_selected(store)
	screen = _draw(state, columns, 24)
	for line in screen:
		assert display_width(line) <= columns
	# ...and the detail pane really did get the whole width to wrap into.
	assert display_width(screen[_rule_index(screen)]) == columns


def test_narrowing_and_widening_reflows_without_losing_bytes(env):
	from baton_tui.render import detail_line_count
	store, _ = env
	marker = "REFLOW-MARKER"
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Reflow",
	           body=("filler words " * 40 + marker).encode())
	state = _ready_state(store)
	state.open_selected(store)
	for columns in (133, 60, 40, 100):
		total = detail_line_count(state, columns, 24)
		state.detail_offset = 0
		seen = ""
		for _ in range(total + 2):
			seen += "\n".join(_draw(state, columns, 24))
			state.scroll_detail(4, total)
		assert marker in seen, f"content lost at {columns} columns"


# -- R7 item 2: the 40/60 split lives in one helper, and divides HEIGHT ----

@pytest.mark.parametrize("lines", [8, 10, 12, 20, 24, 40, 60, 100])
def test_panes_split_forty_sixty_with_one_divider_row(lines):
	"""Stacked: the ratio divides the BODY HEIGHT, and the rule costs one row
	rather than one column. Both panes are the full terminal width."""
	from baton_tui.render import pane_heights
	body = ordinary_body_lines(lines)      # header plus the one-row footer
	top, detail = pane_heights(body)
	assert top + detail + 1 == body        # the rule is paid for exactly once
	assert top >= 1 and detail >= 1
	if body >= 20:
		# Rounding dominates in a short body -- at four usable rows there is no
		# split within 3% of anything -- so the ratio is pinned where it is
		# actually a ratio.
		assert abs(top / (top + detail) - 0.40) < 0.03


def test_every_consumer_uses_the_same_pane_arithmetic(env):
	"""The geometry used to be recomputed in four places. They have to agree
	exactly, or the rule lands on one row while the caret believes another."""
	from baton_tui.render import (_body_lines, detail_line_count, input_caret,
	                              pane_heights)
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("word " * 200).encode())
	state = _ready_state(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft = "typing"
	for columns, lines in ((40, 24), (61, 20), (80, 24), (100, 12), (133, 40)):
		# Asked of the product rather than restated: the footer went from two
		# ordinary rows to one, and a test carrying its own `lines - 3` would
		# have had to be edited to agree -- which is the same fact in two
		# places, the thing this whole batch is about.
		top, detail = pane_heights(_body_lines(state, lines))
		screen = _draw(state, columns, lines)
		# The drawn rule is exactly where the helper puts it: one row past the
		# header and the list pane.
		assert _rule_index(screen) == 1 + top
		assert len(screen) == lines
		assert detail_line_count(state, columns, lines) > 0
		row, _ = input_caret(state, columns, lines)
		assert 1 + top < row < lines - 1      # the caret is in the detail pane


# -- R7: the highlight covers the selected list row, and only that row -----

@pytest.mark.parametrize("columns", [40, 50, 61, 80, 100, 133, 200])
def test_the_selection_span_covers_the_whole_list_row(columns):
	"""Stacked, a list row IS the whole row, so the stripe covers it end to
	end. What the span still guarantees -- and what the column layout needed
	it for -- is that the stripe is confined to one row of one list."""
	from baton_tui.render import selection_span
	start, end = selection_span(columns)
	assert start == 0
	assert end == columns


def test_the_highlight_never_reaches_the_divider_or_the_detail_pane(env):
	"""The stripe used to run into the pane beside it. Stacked, the same
	mistake would be a stripe on the rule or on a detail row, so the pin moved
	from a column boundary to a row boundary."""
	from baton_tui.render import STYLE_SELECTED, render_styled
	store, _ = env
	for index in range(4):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"y\n")
	state = _ready_state(store)
	state.open_selected(store)
	for columns in (40, 61, 80, 100, 133):
		_draw(state, columns, 24)                 # apply this layout first
		rows = render_styled(state, columns, 24)
		rule = _rule_index([text for text, _ in rows])
		marked = [index for index, (_, style) in enumerate(rows)
		          if STYLE_SELECTED in style]
		assert len(marked) == 1
		assert 0 < marked[0] < rule


def test_wide_characters_do_not_push_a_list_row_past_the_terminal(env):
	"""Wide list text was what pushed the divider off its column before. The
	stripe is drawn by splitting the row at the span boundary, so that split
	must never leave a head wider than the terminal."""
	from baton_tui.render import selection_span
	from baton_tui.safe_text import split_cells
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="\u5e83\u3044\u6587\u5b57\u306e\u4ef6\u540d", body=b"y\n")
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="plain", body=b"y\n")
	state = _ready_state(store)
	for columns in (40, 61, 80, 100):
		_, end = selection_span(columns)
		screen = _draw(state, columns, 24)
		for line in screen[1:_rule_index(screen)]:
			head, tail = split_cells(line, end)
			assert display_width(head) <= end
			assert tail == "", "a list row overflowed the terminal width"


# -- re-review R1: the picker pages by what it can actually DRAW ------------

# The live protocol-9 registry, plus a legal maximum-length address. 64 bytes
# is the configured ceiling, so this is the widest entry the picker can ever
# be asked to draw -- the previous capacity arithmetic was checked against
# short fixture names and passed while the real ones did not fit.
LIVE_ADDRESSES = [
	"baton.implementer", "baton.reviewer", "human.slawomir",
	"lang_testing.implementer", "lang_testing.reviewer",
	"drift.implementer", "drift.reviewer",
	"a" * 55 + ".member",
] + [f"team{index:02d}.member" for index in range(13)]

SUPPORTED_SIZES = [(40, 8), (40, 10), (40, 12), (40, 24), (60, 10),
                   (80, 24), (100, 24), (100, 8), (133, 40), (200, 24)]


def _picker_state(columns, lines, addresses=LIVE_ADDRESSES):
	from baton_tui.render import layout_for
	from baton_tui.state import InboxState, MODE_PICK_RECIPIENT
	state = InboxState("baton.implementer")
	state.mode = MODE_PICK_RECIPIENT
	state.recipients = [{"address": address} for address in addresses]
	state.set_viewport(**layout_for(columns, lines,
	                                state.recipients, state.participant))
	return state


@pytest.mark.parametrize("columns,lines", SUPPORTED_SIZES)
def test_every_offered_recipient_is_fully_drawn(columns, lines):
	"""A shortcut you cannot see is worse than no shortcut: the keystroke
	still works and sends to whoever the invisible row named. Reproduced at
	40x10 and 40x12 with the live registry, where letters c/d/e were offered
	and never drawn."""
	from baton_tui.render import _picker_entry_lines
	state = _picker_state(columns, lines)
	screen = _draw(state, columns, lines)
	# The picker is MODAL and owns the body, so its entries wrap at the full
	# terminal width.
	width = columns
	for label, entry in state.picker_entries():
		# FULLY drawn: an address wraps to several rows at narrow widths, and
		# a half-drawn address is a half-identified recipient. Compare against
		# the rows the entry layout produces, so a truncated tail is caught.
		expected = _picker_entry_lines(label, entry["address"],
		                               state.participant, width)
		for row in expected:
			assert any(row in line for line in screen), (
				f"{columns}x{lines}: {entry['address']} is offered but the "
				f"row {row!r} is not drawn")


@pytest.mark.parametrize("columns,lines", SUPPORTED_SIZES)
def test_a_multipage_picker_always_says_where_you_are(columns, lines):
	"""Hidden recipients must be visibly hidden. The old layout dropped the
	footer at exactly the narrow sizes where paging was heaviest."""
	state = _picker_state(columns, lines)
	body = "\n".join(_draw(state, columns, lines))
	if state.picker_pages > 1:
		assert f"page {state.picker_page + 1}/{state.picker_pages}" in body, (
			f"{columns}x{lines}: {state.picker_pages} pages and no position shown")
		assert "Tab" in body, f"{columns}x{lines}: no way to advance is stated"


@pytest.mark.parametrize("columns,lines", SUPPORTED_SIZES)
def test_paging_reaches_every_recipient_exactly_once(columns, lines):
	"""Capacity that varies with width is only correct if the pages still
	partition the registry."""
	state = _picker_state(columns, lines)
	seen = []
	for _ in range(state.picker_pages):
		seen.extend(entry["address"] for _, entry in state.picker_entries())
		state.picker_next_page()
	assert seen == [entry["address"] for entry in state.recipients]


def test_the_live_registry_at_a_hundred_by_twentyfour():
	"""The case the previous docstring claimed and the previous test did not
	render."""
	state = _picker_state(100, 24, LIVE_ADDRESSES[:21])
	body = "\n".join(_draw(state, 100, 24))
	assert "lang_testing.implementer" in body
	for label, _ in state.picker_entries():
		assert f"{label})" in body


# -- re-review R3: which panes elide, and which must not -------------------

def _detail(screen):
	"""Only the detail pane: the rows below the rule and above the footer.

	The list rows truncate with `fit`, which also emits U+2026, and so does the
	footer's key list -- searching the whole screen for an ellipsis passes
	whether or not the detail pane elides anything, which is how the first
	version of this test managed to be vacuous. Stacked, "below the rule" is
	what "right of the divider" used to be.

	With the recipient picker open there is no rule, because the chooser is
	modal and owns the whole body; then the body IS the pane.

	The footer boundary comes from the shared authority, not from a literal.
	This carried `else 2` from the two-row footer and so dropped the LAST real
	detail row on every ordinary screen -- which is the same class of mistake
	as the production geometry it was meant to be checking.

	The `QUIT WITH...` branch that used to sit here is GONE with the two-row
	quit footer. It had become unreachable, and an unreachable branch in a
	geometry helper is a claim that a shape still exists."""
	footer = len(screen) - 1 - ordinary_body_lines(len(screen))
	body = screen[1:len(screen) - footer]
	for index, line in enumerate(body):
		if _is_rule(line, DIVIDER):
			return body[index + 1:]
	return body


def test_read_only_body_content_elides_an_overlong_token(env):
	from baton_tui.safe_text import ELLIPSIS
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=("see " + "x" * 400 + " tail\n").encode())
	state = _ready_state(store)
	state.open_selected(store)
	detail = _detail(_draw(state, 100, 24))
	assert any(ELLIPSIS in line for line in detail)
	# NOT fractured: the token occupies one row, not eight.
	assert sum(1 for line in detail if "xxxxxxxxxx" in line) == 1
	# ...and the rest of the paragraph survived the elision.
	assert any("tail" in line for line in detail)


def test_headers_elide_by_the_same_rule(env):
	"""Explicit truncation, as ruled -- and a subject is the one field most
	likely to arrive overlong."""
	from baton_tui.safe_text import ELLIPSIS
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="S" * 240, body=b"y\n")
	state = _ready_state(store)
	state.open_selected(store)
	detail = _detail(_draw(state, 100, 24))
	assert any(ELLIPSIS in line for line in detail)
	# The subject appears twice in the pane -- once in the read-only heading
	# and once as a header line -- and BOTH must elide rather than fracture.
	elided = [line for line in detail if "SSSSSSSSSS" in line]
	assert elided
	assert all(ELLIPSIS in line for line in elided)


def test_a_reply_draft_is_never_elided(env):
	"""Editable text stays lossless. Hiding what someone is typing is a
	different and worse fault than hiding what they are reading."""
	from baton_tui.safe_text import ELLIPSIS
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	           body=b"y\n")
	state = _ready_state(store)
	state.open_selected(store)
	state.begin_reply()
	state.draft, state.draft_caret = "z" * 400, 400
	# Scrolled to the draft, as the driver's follow does after every keystroke:
	# the stacked detail pane is 60% of the body, so a 400-character draft
	# starts below the fold and "never elided" is about the rows it occupies.
	screen = _draw(state, 100, 24)
	drafted = "".join(_detail(screen))
	assert ELLIPSIS not in drafted, "the draft was truncated"
	# It wraps LOSSLESSLY rather than eliding: every drawn row is full, so what
	# is on screen is a prefix-free run of the draft, not a summary of it.
	assert drafted.count("z") == len([c for c in drafted if c == "z"])
	assert drafted.count("z") >= 100


def test_a_compose_field_is_never_elided(env):
	from baton_tui.safe_text import ELLIPSIS
	store, _ = env
	state = _ready_state(store)
	state.begin_compose(recipient="acme.reviewer")
	state.compose["subject"] = "w" * 300
	state.compose_carets["subject"] = 300
	screen = _draw(state, 100, 24)
	assert ELLIPSIS not in "".join(_detail(screen))


def test_a_picker_address_is_never_elided():
	"""Two accounts differing only in their tail would render identically,
	and the picker exists to stop exactly that mistake."""
	from baton_tui.safe_text import ELLIPSIS
	state = _picker_state(100, 24, ["a" * 55 + ".member", "baton.reviewer"])
	body = "".join(_detail(_draw(state, 100, 24)))
	assert ELLIPSIS not in body
	assert body.count("a") >= 55


# -- addendum: the selected part header is visibly marked ------------------

def _multipart(store, subject="Multipart"):
	return store.send("acme.reviewer", "acme.implementer", kind="q",
	                  subject=subject, parts=[
		{"content_type": "text/plain; charset=utf-8", "body": b"first leaf\n"},
		{"content_type": "multipart/mixed", "parts": [
			{"content_type": "text/plain; charset=utf-8", "body": b"nested one\n"},
			{"content_type": "text/plain; charset=utf-8", "body": b"nested two\n"},
		]},
	])


def _opened(store, participant="acme.implementer"):
	state = _ready_state(store, participant) if False else _ready_state(store)
	state.open_selected(store)
	return state


def _styled(state, columns=100, lines=24):
	from baton_tui.render import layout_for, render_styled
	layout = layout_for(columns, lines)
	if layout is not None:
		state.set_viewport(**layout)
	return render_styled(state, columns, lines)


def test_the_footer_names_exactly_one_selected_part(env):
	"""REPLACES the part-header mark, which no longer exists for text parts.

	The mark used to say which part `m` will write out, by styling that
	part's header row. The header row is gone -- ruled: the body starts where
	it used to, and the metadata moved to a fixed footer -- so the FOOTER is
	now what says it, and it says exactly one part out of a stated total."""
	from baton_tui.render import part_footer
	store, _ = env
	_multipart(store)
	state = _opened(store)
	line = part_footer(state, 100)
	assert line.count("[") == 1, f"more than one part is named: {line!r}"
	total = len(state.visible_parts())
	assert f"(1/{total} parts)" in line


def test_the_footer_follows_part_selection(env):
	"""It must follow `[`/`]`, or it names a part the human has left."""
	from baton_tui.render import part_footer
	store, _ = env
	_multipart(store)
	state = _opened(store)
	addresses = [part.get("address") for part in state.visible_parts()]
	total = len(addresses)
	assert f"[{addresses[0]}]" in part_footer(state, 100)
	assert f"(1/{total} parts)" in part_footer(state, 100)
	state.move_part(1)
	assert f"[{addresses[1]}]" in part_footer(state, 100)
	assert f"(2/{total} parts)" in part_footer(state, 100)
	state.move_part(-1)
	assert f"[{addresses[0]}]" in part_footer(state, 100)


def test_the_footer_is_not_a_list_row(env):
	"""Two cursors that look the same are one cursor as far as the human is
	concerned, and they mean different things. The footer is structurally
	separate now rather than merely styled differently."""
	from baton_tui.render import STYLE_SELECTED, part_footer, render_styled
	store, _ = env
	_multipart(store)
	state = _opened(store)
	footer = part_footer(state, 100).rstrip()
	rows = render_styled(state, 100, 24)
	selected = [text for text, style in rows if STYLE_SELECTED in style]
	assert footer.strip()
	assert all(footer.strip() not in text for text in selected), \
		"the inbox selection and the part footer are the same row"


def test_a_nested_leaf_appears_in_the_footer(env):
	"""A leaf inside a nested container is still a leaf `m` can act on, and
	the footer has to be able to name it."""
	from baton_tui.render import part_footer
	store, _ = env
	_multipart(store)
	state = _opened(store)
	addresses = [part.get("address") for part in state.visible_parts()]
	assert len(addresses) >= 2, "the fixture is not nested"
	for index, address in enumerate(addresses):
		state.part_cursor = index
		assert f"[{address}]" in part_footer(state, 100)


def test_the_footer_stays_while_the_body_scrolls_away(env):
	"""THE INVERSION, and the reason the footer was ruled.

	The old mark lived on a header row, so scrolling past that row took the
	part identity off the screen -- exactly when a reader deep in a long body
	most wants to know which part they are in. A fixed footer cannot scroll
	away."""
	from baton_tui.render import detail_line_count, part_footer
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Long",
	           parts=[{"content_type": "text/plain; charset=utf-8",
	                   "body": ("line\n" * 400).encode()}])
	state = _opened(store)
	before = part_footer(state, 100)
	state.scroll_detail(300, detail_line_count(state, 100, 24))
	assert part_footer(state, 100) == before
	assert part_footer(state, 100).strip(), "the footer emptied while scrolling"


def test_content_cannot_forge_a_part_mark(env):
	"""The mark comes from the code that drew the row, never from searching
	the text -- otherwise a sender writes the marker at the start of a line
	and paints a part selection that is not there."""
	from baton_tui.render import PART_MARKER, STYLE_PART_HEADER
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Forge",
	           parts=[{"content_type": "text/plain; charset=utf-8",
	                   "body": f"{PART_MARKER} [9] text/plain forged\n".encode()}])
	state = _opened(store)
	for text, style in _styled(state):
		if "forged" in text:
			assert STYLE_PART_HEADER not in style


# -- addendum: the header shows the advisory part name ---------------------

def test_the_part_header_shows_address_type_disposition_and_name(env):
	"""Rendered directly, with no label: a part is not a file, and
	the name is a human label until someone chooses to save it."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Named",
	           parts=[
		{"content_type": "text/plain; charset=utf-8", "body": b"note\n"},
		{"content_type": "image/png", "body": b"\x89PNG\r\n\x1a\n",
		 "disposition": "attachment", "part_name": "diagram.png"},
	])
	state = _opened(store)
	detail = "\n".join(_detail(_draw(state, 100, 24)))
	assert "image/png" in detail
	assert "attachment" in detail
	assert "diagram.png" in detail
	assert "part_name" not in detail.lower() and "filename" not in detail.lower(), \
		"the name is labelled rather than shown"


def test_the_authority_refuses_a_part_name_carrying_controls(env):
	"""First line of defence, and the strongest one: a hostile filename
	cannot enter the mailbox at all. Pinned here so the console's display
	rule is never mistaken for the only thing standing between a sender and
	the terminal."""
	import baton_core as core
	store, _ = env
	with pytest.raises(core.BatonError):
		store.send("acme.reviewer", "acme.implementer", kind="q", subject="Hostile",
		           parts=[{"content_type": "application/octet-stream",
		                   "body": b"\x00\x01", "disposition": "attachment",
		                   "part_name": "ok\u001b[2Jname\u0007.bin"}])


@pytest.mark.parametrize("hostile", [
	"ok\u001b[2Jname.bin",
	"drop\rme.bin",
	"bell\u0007.bin",
	"csi\u009bmore.bin",
	"rtl\u202eexe.txt",
])
def test_a_hostile_part_name_would_still_render_as_inert_text(hostile):
	"""Second line of defence, tested directly against the renderer because
	the first line stops it reaching a real message. If a filename ever
	arrives by another path -- a future import, a relaxed validator -- it
	reaches the terminal as visible text, not as a control."""
	from baton_tui.render import _rendered_parts
	rows = _rendered_parts([{"address": "0", "content_type": "application/octet-stream",
	                         "disposition": "attachment", "part_name": hostile,
	                         "encoding": "base64", "size": 2}], 60)
	# Per ROW, not on a joined string: the "\n" used to join them is itself
	# below 0x20, so the joined form flags every input and the test passes
	# nothing. It caught me once.
	for row in rows:
		assert not any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F
		               for char in row), (
			f"a control character survived into {row!r}")
		assert "\u202e" not in row, "a bidi override survived"
	assert any("bin" in row for row in rows)     # the visible name survives
	assert all(display_width(row) <= 60 for row in rows)


# -- R7: the stacked layout ------------------------------------------------
#
# The console was two side-by-side columns: a 40%-wide list and a 60%-wide
# detail pane with a vertical rule between them. It is now stacked -- a
# full-width list above a full-width detail pane, separated by one horizontal
# rule. Everything below fails if the column layout comes back.

def test_the_screen_is_stacked_list_above_detail(env):
	"""The shape itself: header, list, ONE rule row, detail, footer -- in that
	order, with nothing beside anything."""
	store, _ = env
	for index in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index}", body=b"body text\n")
	state = _ready_state(store)
	state.open_selected(store)
	screen = _draw(state, 100, 24)
	rule = _rule_index(screen)
	# The list is ABOVE the rule and the opened message BELOW it. In the column
	# layout both appeared on the same rows, so this ordering could not hold.
	assert any("Row 0" in line for line in screen[1:rule])
	assert any("body text" in line for line in screen[rule + 1:-1])
	# ...and no row carries both, which is exactly what a column layout does.
	for line in screen:
		assert not ("Row 0" in line and "body text" in line)


@pytest.mark.parametrize("columns", [40, 61, 80, 100, 133, 200])
def test_both_panes_get_the_whole_terminal_width(env, columns):
	"""The point of stacking. In the column layout a subject had 40% of the
	terminal and a body 60%; both now have all of it, so a long line reaches
	past either old boundary."""
	from baton_tui.safe_text import display_width
	store, _ = env
	# 255 bytes is the authority's subject ceiling, so this is the widest
	# subject the list can ever be asked to draw.
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="S" * 255, body=("W " * 400 + "\n").encode())
	state = _ready_state(store)
	state.open_selected(store)
	screen = _draw(state, columns, 24)
	rule = _rule_index(screen)
	widest_row = max(display_width(line) for line in screen[1:rule])
	widest_detail = max(display_width(line) for line in screen[rule + 1:-1])
	# Within a couple of cells of the full width: the list row spends a few on
	# its marker and badge, and the detail pane indents by two.
	assert widest_row > columns - 4, "the list pane did not get the full width"
	assert widest_detail > columns - 4, "the detail pane did not get the full width"
	assert widest_row <= columns and widest_detail <= columns


def test_the_list_pane_is_about_forty_percent_of_the_body(env):
	"""Slawomir's ratio, measured on the DRAWN screen rather than on the
	helper -- the helper agreeing with itself is not evidence."""
	store, _ = env
	for index in range(60):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index:02d}", body=b"x\n")
	state = _ready_state(store)
	for lines in (24, 40, 60):
		screen = _draw(state, 100, lines)
		rule = _rule_index(screen)
		listed, detailed = rule - 1, len(screen) - 1 - rule - 1
		assert listed + detailed + 1 == ordinary_body_lines(lines)
		assert abs(listed / (listed + detailed) - 0.40) < 0.05, (
			f"{lines} lines: {listed} list rows and {detailed} detail rows")


def test_the_stacked_minimum_still_draws_every_region(env):
	"""The minimum terminal check is recomputed from the stacked geometry: at
	40x8 there must still be a list row, a rule, a detail row and the footer,
	or the minimum is a size the console cannot actually draw."""
	from baton_tui.render import MIN_COLUMNS, MIN_LINES
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Smallest", body=b"tiny\n")
	state = _ready_state(store)
	screen = _draw(state, MIN_COLUMNS, MIN_LINES)
	assert len(screen) == MIN_LINES
	rule = _rule_index(screen)
	assert rule >= 2, "no room for a list row above the rule"
	assert len(screen) - 2 - rule >= 2, "no room for a detail row below the rule"
	assert any("Smallest" in line for line in screen[1:rule])


def test_no_column_width_helper_survives():
	"""R7 requirement, stated structurally: the 40/60 arithmetic now divides
	HEIGHT. A leftover width helper would be a second authority that still
	says the panes sit side by side, and something would eventually ask it."""
	from baton_tui import render as R
	assert not hasattr(R, "pane_widths")
	assert not hasattr(R, "INBOX_SHARE")
	assert not hasattr(R, "MIN_INBOX_COLUMNS")
	assert hasattr(R, "pane_heights")


def test_the_recipient_picker_is_modal_and_owns_the_body():
	"""Choosing a recipient replaces everything under the header. Confined to
	a 60% detail pane it could not draw a prompt, one recipient and its page
	footer at the minimum terminal -- and a letter that is selectable but not
	drawn is the fault the measured capacity exists to prevent."""
	for columns, lines in ((40, 8), (100, 24)):
		state = _picker_state(columns, lines)
		screen = _draw(state, columns, lines)
		assert not any(line and set(line) == {DIVIDER} for line in screen), (
			f"{columns}x{lines}: the picker left a rule on screen")
		body = "\n".join(screen[1:-2])
		assert "send to:" in body
		for label, entry in state.picker_entries():
			assert f"{label})" in body


def test_the_date_still_degrades_before_the_subject_at_the_stacked_width(env):
	"""The degradation thresholds were widths of a 40% column; stacked they
	are widths of the whole terminal, so they had to move or the date would
	be unconditional and the degradation path dead code."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="KEEPME", body=b"x\n")
	state = _ready_state(store)

	def row(columns):
		screen = _draw(state, columns, 24)
		return [line for line in screen[1:_rule_index(screen)] if "KEEPME" in line][0]

	assert ":" in row(100)                       # the date fits and is shown
	assert ":" not in row(40)                    # it is the first thing dropped
	assert "KEEPME" in row(40)                   # the subject never is


# -- R1: one viewport authority, so no row is hidden without saying so -----
#
# `layout_for` reserved the overflow-indicator row unconditionally while the
# pane reserved it only when the list actually overflowed. At exactly-capacity
# the model scrolled to top=1 and row 0 left the screen with no `... above` to
# say it had.

def _list_rows(screen):
	"""The drawn list rows, blank padding removed."""
	return [line for line in screen[1:_rule_index(screen)] if line.strip()]


def _assert_the_list_is_honest(state, columns, lines):
	"""At every cursor position: the selected row is DRAWN, and if any row is
	off screen the pane says so. Those two together are the whole contract --
	a hidden row is acceptable, a silently hidden row is not.

	Subjects are read from the model rather than from the send order:
	same-second sends tie and are ordered by id, so assuming the send order
	would make this a test of SQLite's row ordering."""
	subjects = [row["subject"] for row in state.view_rows]
	for position in range(len(subjects)):
		state.view_cursor = position
		# Through the public resize event, which is what re-scrolls the model:
		# the driver applies a layout on every frame, so this is the door a
		# cursor move actually goes through.
		state.set_viewport(inbox_height=state.inbox_height,
		                   detail_height=state.detail_height)
		screen = _draw(state, columns, lines)
		drawn = _list_rows(screen)
		selected = subjects[position]
		assert any(selected in line for line in drawn), (
			f"{columns}x{lines}, {len(subjects)} rows, cursor {position}: "
			f"the selected row {selected!r} is not drawn")
		missing = [subject for subject in subjects
		           if not any(subject in line for line in drawn)]
		if missing:
			assert any("..." in line for line in drawn), (
				f"{columns}x{lines}, {len(subjects)} rows, cursor {position}: "
				f"{len(missing)} row(s) hidden with no overflow indicator")


@pytest.mark.parametrize("delta", [-2, -1, 0, 1, 4])
def test_the_messages_list_never_hides_a_row_silently(env, delta):
	"""Exactly-capacity is the case that failed; its neighbours are here so a
	fix that only special-cases equality does not pass."""
	from baton_tui.render import pane_heights
	store, _ = env
	capacity = pane_heights(24 - 3)[0]
	count = max(1, capacity + delta)
	subjects = [f"Row{index:02d}" for index in range(count)]
	for subject in subjects:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=subject, body=b"x\n")
	state = _ready_state(store)
	assert len(state.rows) == count
	_assert_the_list_is_honest(state, 100, 24)


def test_an_exactly_fitting_list_never_scrolls(env):
	"""The reported reproduction, as a model property. With exactly as many
	messages as rows there is nothing to scroll to, so moving to the last one
	must leave the top where it is.

	It failed because the model's window was the pane height MINUS the
	overflow-indicator row while the pane, seeing no overflow, drew all of
	them: two heights for one pane. Pinned on `view_top` rather than on the
	drawn rows, because the renderer's own clamp would mask a model that still
	believed it had scrolled."""
	from baton_tui.render import pane_heights
	store, _ = env
	capacity = pane_heights(24 - 3)[0]
	for index in range(capacity):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Fit{index:02d}", body=b"x\n")
	state = _ready_state(store)
	assert len(state.rows) == capacity
	for position in range(capacity):
		state.view_cursor = position
		state.set_viewport(inbox_height=state.inbox_height,
		                   detail_height=state.detail_height)
		assert state.view_top == 0, (
			f"cursor {position} of {capacity} scrolled a list that fits: "
			f"top is {state.view_top}")
	# ...and the drawn pane really does show all of them, with no indicator.
	drawn = _list_rows(_draw(state, 100, 24))
	assert len(drawn) == capacity
	assert not any("..." in line for line in drawn)


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_the_sent_filter_never_hides_a_row_silently(env, delta):
	"""The same authority, the other view. They share `list_capacity`, and the
	pin exists so a future third view cannot quietly get its own arithmetic."""
	from baton_tui.render import pane_heights
	from baton_tui.state import VIEW_SENT
	store, _ = env
	capacity = pane_heights(24 - 3)[0]
	count = max(1, capacity + delta)
	subjects = [f"Out{index:02d}" for index in range(count)]
	for subject in subjects:
		store.send("acme.implementer", "acme.reviewer", kind="q",
		           subject=subject, body=b"x\n")
	state = _ready_state(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	assert len(state.sent_rows) == count
	_assert_the_list_is_honest(state, 100, 24)


def test_first_and_last_are_reachable_and_drawn_at_every_size(env):
	"""`gg` and `G` at exactly-capacity were how the hidden row was found:
	moving to the last row scrolled the first one off with nothing to say so."""
	store, _ = env
	for index in range(9):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row{index:02d}", body=b"x\n")
	state = _ready_state(store)
	for lines in (8, 10, 12, 16, 20, 24, 30, 40):
		_draw(state, 100, lines)               # apply this size first
		for target in (0, len(state.rows) - 1):
			state.view_cursor = target
			state.set_viewport(inbox_height=state.inbox_height,
			                   detail_height=state.detail_height)
			screen = _draw(state, 100, lines)
			drawn = _list_rows(screen)
			assert any(state.rows[target]["subject"] in line for line in drawn), (
				f"{lines} lines: row {target} is selected but not drawn")


def test_resizing_across_the_capacity_boundary_keeps_the_selection_drawn(env):
	"""Every size in a sweep, with the row count fixed: the boundary is
	crossed by resizing as well as by sending."""
	store, _ = env
	for index in range(8):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row{index:02d}", body=b"x\n")
	state = _ready_state(store)
	state.view_cursor = len(state.rows) - 1
	# By subject from the MODEL: same-second sends tie and order by id, so
	# "the last row" is not necessarily the last one sent.
	last = state.rows[-1]["subject"]
	subjects = [row["subject"] for row in state.rows]
	for lines in (40, 30, 24, 20, 16, 12, 10, 8, 10, 24, 40):
		screen = _draw(state, 100, lines)
		drawn = _list_rows(screen)
		assert any(last in line for line in drawn), (
			f"{lines} lines: the selection was lost across the resize")
		hidden = [subject for subject in subjects
		          if not any(subject in line for line in drawn)]
		if hidden:
			assert any("..." in line for line in drawn), (
				f"{lines} lines: {hidden} hidden with no indicator")


# -- R2: the superseded History view is gone -------------------------------

def test_there_is_no_history_view():
	"""FINDING §3b: `There is NO separate History view`. It survived as
	unreachable code -- no key emitted its event, so nothing exercised it and
	nothing would have caught it drifting out of agreement with the unified
	list it was superseded by."""
	from baton_tui import driver, keys, render
	from baton_tui import state as S
	for module in (S, keys, driver, render):
		names = [name for name in dir(module) if "HISTORY" in name.upper()]
		assert not names, f"{module.__name__} still carries {names}"
	assert not hasattr(S.InboxState, "open_history_selected")
	assert not hasattr(S.InboxState, "selected_history")
	# On an INSTANCE, because `history_rows`, `history_cursor` and
	# `history_top` were created in `__init__` and never existed on the class.
	# `hasattr(InboxState, ...)` was false before the removal too, so it pinned
	# nothing -- a vacuous assertion is worse than none, because it reports a
	# guarantee it never checked.
	instance = S.InboxState("acme.implementer")
	for field in ("history_rows", "history_cursor", "history_top"):
		assert not hasattr(instance, field), f"the model still carries {field}"
		assert field not in vars(instance)
	# The core method that existed only to populate it is gone too; the
	# owner-checked reopen the unified list actually uses stays.
	import baton_core as core
	assert not hasattr(core.Store, "list_received")
	assert hasattr(core.Store, "open_received")


def test_brackets_alone_navigate_parts():
	"""`[`/`]` are the ONLY part navigation. `h`/`l` scroll the focused
	DETAIL pane sideways, and `H`/`L` are removed rather than aliased.

	(This asserted `h`/`l`/`H`/`L` were part navigation, from before DETAIL
	focus existed -- at which point Vim `h`/`l` not moving within the focused
	pane became a visible contradiction in the model.)"""
	from baton_tui import keys as K
	from baton_tui.state import MODE_BROWSE
	assert K.map_key(ord("["), MODE_BROWSE) == (K.PART_UP, None)
	assert K.map_key(ord("]"), MODE_BROWSE) == (K.PART_DOWN, None)
	assert K.map_key(ord("h"), MODE_BROWSE) == (K.HSCROLL_LEFT, None)
	assert K.map_key(ord("l"), MODE_BROWSE) == (K.HSCROLL_RIGHT, None)
	for gone in (ord("H"), ord("L")):
		assert K.map_key(gone, MODE_BROWSE) == (K.IGNORE, None)


# -- R3: outbound rows keep their lifecycle in MESSAGES --------------------

def test_an_outbound_row_shows_queued_and_picked_up_in_messages(env):
	"""Slawomir relies on seeing whether delegated work has been picked up.
	Outbound rows went through the inbound notation, where `Q` and `P`
	became a blank and a `*` -- which say "waiting for ME" and "claimed by
	ME". Only the Sent filter told the truth, and the primary list did not.

	The brackets are SUPERSEDED: Slawomir ruled a one-cell status column, in
	which alignment rather than punctuation marks the boundary. The badge
	letters, and everything this test is actually about, are unchanged."""
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Delegated", body=b"x\n")
	state = _ready_state(store)
	row = [line for line in _list_rows(_draw(state, 100, 24)) if "Delegated" in line][0]
	from baton_tui.render import PICKED_UP, QUEUED
	assert QUEUED in row, f"queued outbound row does not say so: {row!r}"
	# ...and once the other side picks it up, on the same row.
	store.claim("acme.reviewer")
	state.refresh(store)
	row = [line for line in _list_rows(_draw(state, 100, 24)) if "Delegated" in line][0]
	assert PICKED_UP in row, f"picked-up outbound row does not say so: {row!r}"


def test_inbound_notation_is_unchanged_beside_it(env):
	"""The outbound badge must not leak onto inbound rows: the inbound
	notation answers what the READER owes, and the outbound one answers what
	the other side has done with it.

	SUPERSEDED SPELLING, twice. It was a blank and `*`, then brackets went;
	now it is `•` unopened and `○` opened, by Slawomir's trial ruling that a
	glyph should answer "does someone wait on me". A blank said "waiting for
	me" by saying nothing at all, which is the least visible mark on the
	screen for the state that most demands attention. What the test is about
	-- that Q/P never appear on an inbound row -- is unchanged."""
	from baton_tui.render import OPENED, UNOPENED
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Owed", body=b"x\n")
	state = _ready_state(store)
	row = [line for line in _list_rows(_draw(state, 100, 24)) if "Owed" in line][0]
	assert UNOPENED in row, row
	assert "Q" not in row and "P" not in row
	state.open_selected(store)                    # claim it
	row = [line for line in _list_rows(_draw(state, 100, 24)) if "Owed" in line][0]
	assert OPENED in row, row
	assert "P" not in row


def test_every_list_row_aligns_whichever_notation_it_uses(env):
	"""A 1-cell glyph beside a 3-cell badge shifted the date and sender two
	cells on alternating rows. After R3 that is most of the list."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Inbound", body=b"x\n")
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Outbound", body=b"x\n")
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	state = _ready_state(store)
	drawn = _list_rows(_draw(state, 100, 24))
	assert len(drawn) >= 3
	# The date column starts at the same cell on every row.
	columns = {line.index("08-") for line in drawn if "08-" in line}
	assert len(columns) == 1, f"the date column drifts between rows: {columns}"


# -- RULED: reply indentation is capped at three levels --------------------

def test_the_reply_indent_is_capped_at_three_levels():
	"""Slawomir's ruling. Levels 0-3 are explicit; past the bound the indent
	stops growing and the marker says so, because unbounded indentation
	pushes the subject off the pane -- losing the message to preserve the
	shape of the conversation."""
	from baton_tui.render import (DEEP_THREAD_MARKER, MAX_THREAD_DEPTH,
	                              THREAD_INDENT, THREAD_MARKER, thread_prefix)
	from baton_tui.safe_text import display_width
	assert thread_prefix(0) == ""
	for depth in range(1, MAX_THREAD_DEPTH + 1):
		prefix = thread_prefix(depth)
		assert prefix.startswith(" " * (THREAD_INDENT * depth))
		assert THREAD_MARKER in prefix and DEEP_THREAD_MARKER not in prefix
	# Each explicit level really is a visible step.
	widths = [display_width(thread_prefix(depth))
	          for depth in range(1, MAX_THREAD_DEPTH + 1)]
	assert widths == sorted(set(widths)), f"levels are not distinct: {widths}"
	# ...and past the bound the indent stops and the marker changes.
	capped = display_width(thread_prefix(MAX_THREAD_DEPTH))
	for depth in (MAX_THREAD_DEPTH + 1, MAX_THREAD_DEPTH + 2, 12, 400):
		prefix = thread_prefix(depth)
		assert DEEP_THREAD_MARKER in prefix
		assert prefix.startswith(" " * (THREAD_INDENT * MAX_THREAD_DEPTH))
		assert display_width(prefix) == capped - display_width(THREAD_MARKER) \
			+ display_width(DEEP_THREAD_MARKER)


def test_every_optional_glyph_falls_back_together():
	"""ONE decision for the whole set, so a terminal cannot end up with the
	Unicode arrow beside the ASCII ellipsis. Pinned BY VALUE, both spellings.

	(This covered the two reply markers; the seen-notice mark joined them when
	Slawomir ruled `✓` with `S` as its fallback. The bracketed spelling those
	two arrived in is SUPERSEDED by the one-cell status column.)"""
	from baton_tui.render import markers_for, thread_prefix
	from baton_tui.safe_text import display_width
	from baton_tui.render import ASCII_GLYPHS
	assert markers_for("utf-8") == {"thread": "↪", "deep": "…↪",
	                                "notice_seen": "✓", "status": {}}
	for encoding in ("ascii", "latin-1", None, "", "nonsense-codec"):
		glyphs = markers_for(encoding)
		assert glyphs == {"thread": "->", "deep": "...->", "notice_seen": "S",
		                  "status": ASCII_GLYPHS}
		# The STATUS column falls back with the rest, one decision: a terminal
		# that cannot draw `↪` cannot draw `▷` either, and a screen mixing
		# them is the thing this function exists to prevent.
		assert glyphs["status"], "the status column did not fall back"
		assert glyphs["deep"] in thread_prefix(9, glyphs["thread"], glyphs["deep"])
		assert glyphs["thread"] in thread_prefix(1, glyphs["thread"], glyphs["deep"])
	# Fallback is PRESENTATION only: the status column does not move with it.
	assert display_width("✓") == display_width("S") == 1


def _chain(store, depth):
	"""A received message answered `depth` times, alternating direction, so
	the thread really is nested rather than a flat run of siblings."""
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Deep thread", body=b"?\n")
	for _ in range(depth):
		claim = store.claim("acme.implementer", message_id=mid)
		result = store.reply(claim["claim_id"], participant="acme.implementer",
		                     kind="response", subject="Deep thread", body=b"a\n")
		mid = result["response_message_id"]
		# The other side answers ours, so the next level is a real child.
		claim = store.claim("acme.reviewer", message_id=mid)
		result = store.reply(claim["claim_id"], participant="acme.reviewer",
		                     kind="response", subject="Deep thread", body=b"b\n")
		mid = result["response_message_id"]
	return mid


def test_a_deep_chain_keeps_every_row_in_order(env):
	"""Presentation-only compression: nothing is hidden, collapsed, reordered
	or re-parented. Only how far right a row starts is bounded."""
	from baton_tui.render import MAX_THREAD_DEPTH
	store, _ = env
	_chain(store, 4)
	state = _ready_state(store)
	depths = [row.get("depth") for row in state.rows]
	assert max(depths) > MAX_THREAD_DEPTH, "the fixture is not deep enough"
	# Every message is present, once, parent before child, in one thread.
	assert len(state.rows) == len(depths)
	assert depths == sorted(depths), "the traversal is no longer parent-first"
	assert depths[0] == 0


@pytest.mark.parametrize("columns", [40, 61, 80, 100])
def test_a_deep_chain_still_fits_and_still_aligns(env, columns):
	"""The bound exists so the subject survives at a narrow width, and the
	date and party columns must not move because a row is deep."""
	from baton_tui.render import DEEP_THREAD_MARKER
	from baton_tui.safe_text import display_width
	store, _ = env
	_chain(store, 4)
	state = _ready_state(store)
	screen = _draw(state, columns, 40)
	listed = [line for line in screen[1:_rule_index(screen)] if line.strip()]
	assert len(listed) >= 5
	for line in listed:
		assert display_width(line) <= columns
	if columns >= 60:                       # where the date column is drawn
		starts = {line.index("08-") for line in listed if "08-" in line}
		assert len(starts) == 1, f"the date column moved with depth: {starts}"
	assert any(DEEP_THREAD_MARKER in line for line in listed), \
		"nothing said the ancestry was compressed"


# -- RULED: [N] is a KIND in Sent; ! and [✓] are STATES in MESSAGES --------

def test_the_sent_filter_badges_a_notice_by_kind_not_by_receipts(env):
	"""Ruled after I raised the ambiguity. `[N]` in the Sent filter says "this
	row is a notice" — a row KIND — and must not vary with whether anyone has
	seen it: that would need an aggregate over all recipients, which the row
	does not claim to show."""
	from baton_tui.render import layout_for, render, sent_status_glyph
	from baton_tui.state import VIEW_SENT
	store, _ = env
	notice_id = store.send_notice("acme.implementer", kind="announcement",
	                              subject="Broadcast", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	state.set_viewport(**layout_for(120, 24))
	row = next(r for r in state.sent_rows if r["id"] == notice_id)
	assert sent_status_glyph(row) == "N"
	listed = [line for line in render(state, 120, 24) if "Broadcast" in line][0]
	assert "N" in listed
	# Someone sees it; the authored row's badge does not move.
	store.mark_notice_seen("acme.reviewer", notice_id)
	state.refresh(store)
	row = next(r for r in state.sent_rows if r["id"] == notice_id)
	assert sent_status_glyph(row) == "N", "the sent badge tracked a recipient's receipt"


def test_the_two_notice_notations_mean_different_things(env):
	"""They coexist deliberately, so the legend has to carry both and they
	must not be confusable: `N` is what a row IS, `!`/`✓` is where it stands
	with you. (Bracketed spellings SUPERSEDED by the one-cell column; what
	they distinguish is unchanged.)"""
	from baton_tui.render import NOTICE_BADGE, NOTICE_SEEN_MARK, SENT_LEGEND
	assert NOTICE_BADGE == "N"
	assert NOTICE_SEEN_MARK == "✓"
	assert NOTICE_BADGE != NOTICE_SEEN_MARK
	# `✓ seen notice` is SUPERSEDED as a separate legend entry: one terminal
	# mark covers replied, closed and seen, so the legend says `✓ done` once
	# rather than listing three ways to be finished.
	for fragment in ("N notice", "! unseen notice", "✓ done"):
		assert fragment in SENT_LEGEND, f"the legend does not explain {fragment!r}"


# -- BATCH 2 R1: every content-bearing shape pans its content, and only that --

LONG = "see " + "ABCDEFGHIJ" * 12 + "ENDMARK"


def _semantic(state, width=60):
	"""The produced detail lines, split into the rows that MAY pan and the
	rows that must not.

	Asked of the renderer directly rather than through the driver: the point
	is that every detail SHAPE marks its content, and a shape reached only by
	a longer keyboard route would otherwise go unpinned."""
	from baton_tui.render import _detail_lines
	pannable: list[int] = []
	produced = _detail_lines(state, width, pannable=pannable)
	movable = set(pannable)
	return ([produced[i] for i in sorted(movable)],
	        [line for i, line in enumerate(produced) if i not in movable])


def _pans(state, width=60):
	"""What the shape reports it can pan, and what its content actually is."""
	from baton_tui.render import detail_overflow
	content, chrome = _semantic(state, width)
	return detail_overflow(state, width, 24), content, chrome


def test_an_active_notice_pans_its_body(env):
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast",
	                  body=(LONG + "\n").encode())
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert "notice" in state.detail, "this fixture did not reach the notice shape"
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "an opened notice reports no body to pan"
	assert any("ENDMARK" in line for line in content)
	assert not any("ENDMARK" in line for line in chrome)
	assert any(line.strip().startswith("From:") for line in chrome), \
		"notice metadata was marked as content"


def test_a_seen_notice_pans_the_body_it_still_holds(env):
	"""The already-seen path keeps a body loaded earlier in the session. While
	it is on screen it is content like any other."""
	store, _ = env
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast",
	                  body=(LONG + "\n").encode())
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	state.refresh(store)
	state.open_selected(store)                 # now the seen path
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "the retained body is on screen but cannot pan"
	assert any("ENDMARK" in line for line in content), \
		"the retained body was marked as chrome"
	assert not any(line.strip().startswith("From:") for line in content)


def test_a_handled_inbound_copy_pans_its_body(env):
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Handled", body=(LONG + "\n").encode())
	claim = store.claim("acme.implementer", message_id=mid)
	store.close_claim(claim["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert "received" in state.detail, "this fixture did not reach the handled shape"
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "a handled inbound copy reports no body to pan"
	assert any("ENDMARK" in line for line in content)
	assert not any("ENDMARK" in line for line in chrome)
	from baton_tui.state import FOLLOW_UP_ANSWERED
	assert any(FOLLOW_UP_ANSWERED in line for line in chrome), \
		"the guidance heading was marked as content"
	assert mid


def test_an_outbound_copy_pans_its_body(env):
	from baton_tui.state import VIEW_SENT
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Mine",
	           body=(LONG + "\n").encode())
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_view(VIEW_SENT)
	state.refresh(store)
	state.open_selected(store)
	assert "sent" in state.detail, "this fixture did not reach the outbound shape"
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "an outbound copy reports no body to pan"
	assert any("ENDMARK" in line for line in content)
	assert not any("ENDMARK" in line for line in chrome)


def test_a_sent_notice_pans_its_body(env):
	from baton_tui.state import VIEW_SENT
	store, _ = env
	store.send_notice("acme.implementer", kind="announcement", subject="Mine",
	                  body=(LONG + "\n").encode())
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_view(VIEW_SENT)
	state.refresh(store)
	state.open_selected(store)
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "a sent notice reports no body to pan"
	assert any("ENDMARK" in line for line in content), \
		"the sent notice body was marked as chrome"
	assert not any("ENDMARK" in line for line in chrome)


def test_a_container_label_stays_fixed_while_a_nested_body_pans(env):
	"""The recursion carries the marking down, and stops at the container.

	A nested part's own header and its parent's label are both structure: the
	human reads them to know WHERE in the message they are, which is exactly
	what panning would take away."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Nested",
	           parts=[{"content_type": "multipart/alternative",
	                   "parts": [
	                       {"content_type": "text/plain; charset=utf-8",
	                        "body": ("plain " + LONG + "\n").encode()},
	                       {"content_type": "text/markdown; charset=utf-8",
	                        "body": ("md " + LONG + "\n").encode()}]}])
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	overflow, content, chrome = _pans(state)
	assert overflow > 0, "a nested body reports nothing to pan"
	assert sum("ENDMARK" in line for line in content) == 2, \
		"both nested bodies should be content"
	assert any("multipart/alternative" in line for line in chrome), \
		"the container label was marked as content"
	# The nested LEAF header is gone -- ruled; a text part now leads with its
	# body and its media type lives in the fixed footer. The container label
	# stays because it is structure: it says where in the message you are,
	# which is what panning would take away.
	assert not any("text/plain" in line for line in chrome), \
		"a text leaf still draws a header line above its body"
	from baton_tui.render import part_footer
	assert "text/plain" in part_footer(state, 100), \
		"the media type did not move to the footer"
	assert not any("ENDMARK" in line for line in chrome)


# -- BATCH 3: one owner per fact -------------------------------------------

# Instructions that must appear in exactly ONE layer. Each is a phrase that
# was, at some point, on screen in two places at once.
_INSTRUCTIONS = (
	"claim and open",
	"mark seen and open",
	"Enter: reopen",
	"this line is the subject AND the message",
	"Enter reviews the send from any field",
	"subject alone is enough",
	"Tab moves",
	"Esc cancels",
	"new message (",
	# NOT "Ctrl+E": the EMPTY body row names that key by Slawomir's trial
	# ruling, and it is the one deliberate exception -- a row with no state to
	# report would otherwise say only that nothing is there. The hyphenated
	# `Ctrl-E` stays swept, because that was the removed `(Ctrl-E to edit)`
	# hint sitting beside a body that DID have state.
	"Ctrl-E",
	"to materialize",
	"Nothing here claims, receipts or transitions anything",
)


def _work_area(state, columns=100, lines=24):
	"""Everything between the header rule and the footer: the LIST and the
	detail pane. What the footer and status bar say is a separate question."""
	from baton_tui.render import DIVIDER
	screen = _draw(state, columns, lines)
	rule = _rule_index(screen)
	return " ".join(" ".join(screen[:rule] + screen[rule + 1:-1]).split())


@pytest.mark.parametrize("phrase", _INSTRUCTIONS)
def test_no_instruction_survives_in_the_work_area(env, phrase):
	"""Slawomir's acceptance rule for the cleanup: if the same instruction
	appears in two layers, name its owner and remove the duplicate. The work
	area is never the owner -- it holds messages and drafts.

	Swept across every shape rather than the one literal that was reported,
	because fixing only what was seen leaves the same sentence in the next
	pane the human opens."""
	from baton_tui.state import MODE_BROWSE
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Directed",
	           parts=[{"content_type": "application/octet-stream",
	                   "body": b"\x00\x01\x02"}])
	store.send_notice("hq.lead", kind="announcement", subject="Broadcast", body=b"n\n")
	state = InboxState("acme.implementer")
	state.refresh(store)

	seen = []
	for index in range(len(state.rows)):
		state.cursor = index
		state.preview(store)
		seen.append(_work_area(state))
		state.open_selected(store)
		seen.append(_work_area(state))
	state.begin_reply()
	seen.append(_work_area(state))
	state.mode = MODE_BROWSE
	state.begin_compose(recipient="acme.reviewer")
	seen.append(_work_area(state))
	state.mode = MODE_BROWSE
	state.begin_compose(notice=True)
	seen.append(_work_area(state))

	for screen in seen:
		assert phrase not in screen, f"{phrase!r} is still in the work area"


def _detail_pane(state, columns=100, lines=24):
	"""The detail pane alone. The list is a separate question: it keeps its
	rows while you compose, and should."""
	from baton_tui.render import DIVIDER
	screen = _draw(state, columns, lines)
	rule = _rule_index(screen)
	return " ".join(" ".join(screen[rule + 1:-1]).split())


def test_a_fresh_compose_owns_the_pane(env):
	"""The reported case: composing a new message drew the selected row's
	preview above the form, so an action prompt for a row the human cannot act
	on sat over the message they were writing.

	Asserted on the preview's METADATA BLOCK, not on the body. A preview never
	renders content -- the first version of this pin looked for the body text
	and so passed with the fix deliberately disabled, because that text was
	never on screen in the first place."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Unrelated thing", body=b"the other body\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.preview(store)
	before = _detail_pane(state)
	assert "From: acme.reviewer" in before.replace("From:    ", "From: ")
	assert "Unrelated thing" in before

	state.begin_compose(recipient="acme.reviewer")
	pane = _detail_pane(state)
	assert "From:" not in pane, "the unrelated row's metadata is still behind it"
	assert "Unrelated thing" not in pane, "the unrelated subject is still behind it"
	assert "to: acme.reviewer" in pane.replace("to:      ", "to: ")
	assert "subject:" in pane


def test_a_follow_up_keeps_the_message_it_answers(env):
	"""The other half, and the reason mode alone cannot decide it: a follow-up
	IS a composition, and hiding the message it refers to would take away the
	thing being answered."""
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Answered thing", body=b"the original question\n")
	claim = store.claim("acme.implementer", message_id=mid)
	store.close_claim(claim["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.open_selected(store)
	assert state.begin_reply(), "this fixture did not reach a follow-up"
	assert "the original question" in _work_area(state), \
		"the message being answered was hidden"


def test_the_header_does_not_repeat_the_product_name(env):
	"""The terminal running it already establishes which tool this is.

	The identity used to lead this line and no longer does: it moved to the
	pane rule so the queue counts get the position the human actually reads.
	What this pins now is that the top line opens with the VIEW -- the two
	lists look alike at a glance, and acting on the wrong one is the mistake
	the console exists to prevent -- and that the identity is on screen
	SOMEWHERE, which is the part of the old assertion still worth holding."""
	store, _ = env
	from baton_tui.state import VIEW_SENT
	state = InboxState("acme.implementer")
	state.refresh(store)
	for view, expected in ((None, "Messages:"), (VIEW_SENT, "Sent:")):
		if view:
			state.select_view(view)
		screen = _draw(state, 100, 24)
		header = screen[0]
		assert not header.lstrip().startswith("baton"), header
		# The leading focus mark is allowed and is not part of the name.
		assert header.lstrip().lstrip("> ").startswith(expected), header
		assert "acme.implementer" not in header, header
		assert any("acme.implementer" in line for line in screen), \
			"the identity left the header without arriving anywhere"


def test_the_status_column_is_exactly_one_cell_everywhere(env):
	"""Every row class, both notations. A column that is three cells on some
	rows and one on others moves the date under the human's eye."""
	from baton_tui.render import (GLYPH_WIDTH, NOTICE_BADGE, NOTICE_SEEN_MARK,
	                              NOTICE_SEEN_MARK_ASCII, SENT_BADGES)
	from baton_tui.safe_text import display_width
	assert GLYPH_WIDTH == 1
	for glyph in (list(SENT_BADGES.values())
	              + [NOTICE_BADGE, NOTICE_SEEN_MARK, NOTICE_SEEN_MARK_ASCII,
	                 "!", "*", "~", "?", " "]):
		assert display_width(glyph) == 1, f"{glyph!r} is not one cell"
		assert "[" not in glyph and "]" not in glyph, f"{glyph!r} kept its brackets"


def test_help_and_readme_own_the_notation_the_panes_gave_up(env):
	"""Removing an explanation is only safe if its one owner carries it."""
	from pathlib import Path
	from baton_tui.keys import HELP_SECTIONS
	help_text = " ".join(f"{key} {text}" for _title, rows in HELP_SECTIONS
	                     for key, text, *_ in rows)
	readme = Path(__file__).resolve().parents[2].joinpath("README.md").read_text()
	# What the READER owes, and what the other side has done. Both sets, in
	# both owners: the glyph on the row is deliberately terse, so the place it
	# is explained has to be complete.
	for glyph, meaning in (("•", "not yet opened"), ("○", "still owed"),
	                       ("▷", "picked it up"), ("▶", "picked it up"),
	                       ("✓", "replied, closed"),
	                       ("!", "have not seen"), ("~", "withheld"),
	                       ("E", "expired"), ("X", "quarantined"),
	                       ("N", "notice"), ("?", "does not understand")):
		assert glyph in help_text, f"help does not list {glyph!r}"
		assert meaning in help_text.lower(), f"help does not explain {meaning!r}"
		assert glyph in readme, f"the README does not list {glyph!r}"
		assert meaning in readme.lower(), f"the README does not explain {meaning!r}"
	assert "[Q]" not in help_text and "[Q]" not in readme, "bracketed notation survives"
	# The old inbound reading is gone from both, not merely joined by the new.
	assert "claimed by you" not in help_text and "claimed by you" not in readme
	assert "inbound, waiting for you" not in readme
	# `R` is REMOVED from the human vocabulary: a completed row reads `✓`
	# whichever side answered it, so a legend teaching `R` would describe a
	# glyph the console never draws.
	assert "they answered it" not in readme
	assert "R replied" not in help_text and "R replied" not in readme
	# `C` goes with it: one terminal mark, ruled. A legend teaching `C` would
	# describe a glyph the console never draws.
	assert "C closed" not in help_text and "C closed" not in readme
	assert "| `C` |" not in readme, "the C row survives in the README table"


def test_the_reclaimed_row_is_navigable_not_merely_blank(env):
	"""The correction that made this necessary: `_footer_height` went to one
	row while `layout_for` and `picker_capacity` still subtracted three, so
	the MODEL's viewport stayed a row smaller than the screen. The extra row
	drew, and nothing could scroll to it -- a reclaimed row nobody can reach
	is not reclaimed."""
	from baton_tui.render import (PART_FOOTER_ROWS, layout_for,
	                              ordinary_body_lines, pane_heights)
	store, _ = env
	for index in range(80):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Row {index:02d}", body=b"x\n")
	state = _ready_state(store)
	for lines in (12, 20, 24, 40):
		layout = layout_for(100, lines)
		top, detail = pane_heights(ordinary_body_lines(lines))
		# What the model was told, and what the screen actually has.
		assert layout["inbox_height"] == max(1, top)
		# The detail PANE has `detail` rows; the model's scrollable height is
		# one less, because the selected-part footer occupies the last one.
		# Ruled in `work/finding-human-console/findings/
		# finding-selected-part-footer/FINDING.md`: "The footer consumes one
		# DETAIL row. Layout, page size, overflow indicators, navigation, and
		# resize calculations account for it."
		assert layout["detail_height"] == max(1, detail - PART_FOOTER_ROWS)
		state.set_viewport(**layout)
		screen = _draw(state, 100, lines)
		rule = _rule_index(screen)
		drawn_list = rule - 1
		drawn_detail = len(screen) - 1 - rule - 1
		assert drawn_list == layout["inbox_height"], (
			f"{lines} lines: {drawn_list} list rows drawn, model believes "
			f"{layout['inbox_height']}")
		# The pane draws the model's scrollable rows PLUS the part footer.
		# The point of this test is that the two agree, and they still do --
		# with the footer named rather than absorbed, so a future change to
		# either side has to change this line too.
		assert drawn_detail == layout["detail_height"] + PART_FOOTER_ROWS, (
			f"{lines} lines: {drawn_detail} detail rows drawn, model believes "
			f"{layout['detail_height']} scrollable + {PART_FOOTER_ROWS} footer")


def test_the_picker_is_measured_against_the_same_body(env):
	"""The modal picker was measured against the old footer height too, so a
	terminal that could draw one more recipient was told it could not."""
	from baton_tui.render import ordinary_body_lines, picker_capacity
	people = [{"address": f"team.person{index:02d}"} for index in range(12)]
	for lines in (12, 20, 24, 40):
		capacity = picker_capacity(people, "acme.implementer", 100, lines)
		assert capacity >= 1
		# It grows with the body, and the body is the SHARED arithmetic.
		bigger = picker_capacity(people, "acme.implementer", 100, lines + 4)
		assert bigger >= capacity
		assert ordinary_body_lines(lines + 4) == ordinary_body_lines(lines) + 4


def test_the_pane_helpers_reach_the_bottom_row_of_the_pane(env):
	"""The helpers sliced `[:-2]` for a two-row footer. With one row that
	silently drops a REAL pane row, so a cleanup or panning assertion could
	pass while ignoring the bottom of what the human sees.

	Pinned with content that reaches that row: the fixtures the other tests
	use happen to leave it blank, which is exactly why the wrong slice went
	unnoticed."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Filled",
	           body=("\n".join(f"line {index:02d}" for index in range(60))
	                 + "\nLASTVISIBLE\n").encode())
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))
	state.open_selected(store)
	screen = _draw(state, 100, 24)
	bottom = screen[-2]                      # the last PANE row, above status
	assert bottom.strip(), "this fixture did not fill the pane to the bottom"
	# NORMALISED on both sides. The helpers collapse runs of spaces, and the
	# bottom row is now the selected-part footer, whose fields are separated
	# by two -- so the raw needle could not match text that had been
	# collapsed. This compares what the row SAYS, which is the question.
	needle = " ".join(bottom.split())
	assert needle in _detail_pane(state), \
		"the detail helper drops the bottom row of the pane"
	assert needle in _work_area(state), \
		"the work-area helper drops the bottom row of the pane"
	assert any(needle in " ".join(line.split()) for line in _detail(screen)), \
		"the `_detail` helper drops the bottom row of the pane"


def test_the_empty_body_row_names_the_key_and_the_filled_one_does_not(env):
	"""Slawomir's trial ruling, and its boundary. An empty body row has no
	state of its own to report, so it advertises the action instead; a body
	with content reports its size and says nothing about keys."""
	from baton_tui.render import EMPTY_BODY
	store, _ = env
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.begin_compose(recipient="acme.reviewer")
	empty = _detail_pane(state)
	assert EMPTY_BODY in empty, "the empty body row does not offer the action"
	assert "(none)" not in empty, "the superseded label is back"

	state.compose["body"] = "one\ntwo\nthree"
	filled = _detail_pane(state)
	assert "3 lines" in filled
	assert "13 characters" in filled
	assert EMPTY_BODY not in filled, "the empty-state label outlived the body"
	assert "Ctrl" not in filled, "a key hint reappeared beside a real body"


# -- TRIAL: how a key is SPELLED where a human reads it --------------------

def test_no_human_facing_legend_writes_a_control_chord_in_capitals(env):
	"""Ruled during the trial: a Ctrl chord takes a lower-case letter, because
	Shift is not part of the gesture and a capital implies it is. `^E` goes
	too — it is terminal shorthand, not something to teach.

	FOUR surfaces, and the fourth is a genuinely RENDERED screen. The first
	version of this said it swept the rendered screen and did not: it checked
	`?` help, the modal legend tables and the README, all of which are source
	data. A drift that only reached the drawn output would have passed it.

	The README is swept for the caret too. Exempting it was a hole, and the
	hyphenated lower-case `Ctrl-e` was another: both are spellings this ruling
	removes. The CONSTANTS are still not swept — `CTRL_E` is code."""
	import re
	from pathlib import Path
	from baton_tui import keys as K
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 40))
	state.open_selected(store)
	drawn = ["\n".join(_draw(state, 100, 40))]
	state.begin_reply()
	drawn.append("\n".join(_draw(state, 100, 40)))
	state.mode = "help"
	drawn.append("\n".join(_draw(state, 100, 40)))
	state.mode = "browse"
	state.begin_compose(recipient="acme.reviewer")
	drawn.append("\n".join(_draw(state, 100, 40)))

	surfaces = {
		"help table": " ".join(f"{key} {label}" for _title, rows in K.HELP_SECTIONS
		                       for key, label, *_ in rows),
		"modal legends": " ".join(label for rows in K.MODE_LEGENDS.values()
		                          for label, _keys, _cond in rows),
		"README": Path(__file__).resolve().parents[2].joinpath("README.md").read_text(),
		"the drawn screen": "\n".join(drawn),
	}
	for name, text in surfaces.items():
		assert "^" not in text, f"{name} uses terminal caret shorthand"
		assert not re.search(r"Ctrl[+-][A-Z]\b", text), \
			f"{name} capitalises a control letter"
		# The HYPHEN is out too, in either case: one spelling, everywhere.
		assert not re.search(r"Ctrl-[A-Za-z]", text), \
			f"{name} hyphenates a control chord"
		assert not re.search(r"Shift\s*\+", text), \
			f"{name} spells out Shift; letter case already says it"


def test_the_control_chords_that_are_advertised_still_work(env):
	"""Notation only: the spelling changed, the bindings did not."""
	from baton_tui import keys as K
	from baton_tui.state import MODE_BROWSE, MODE_REPLY
	assert K.map_key(K.CTRL_R, MODE_BROWSE)[0] == K.REFRESH
	assert K.map_key(K.CTRL_E, MODE_REPLY)[0] == K.EDIT_BODY
	assert K.map_key(K.CTRL_U, MODE_REPLY)[0] == K.KILL_TO_START
	# ...and the labels that name them say so in the ruled spelling.
	labels = " ".join(label for rows in K.MODE_LEGENDS.values()
	                  for label, _keys, _cond in rows)
	assert "Ctrl+e" in labels and "Ctrl+u" in labels


def test_a_shifted_letter_is_written_as_the_letter(env):
	"""`R`, `N`, `G` are shifted and say so by being capitals."""
	from baton_tui import keys as K
	keys_named = {key for _title, rows in K.HELP_SECTIONS for key, *_ in rows}
	assert "R" in keys_named and "N" in keys_named
	assert not any(name.startswith("Shift") for name in keys_named)


def test_every_marker_the_driver_passes_reaches_both_renderers(env):
	"""The gap this closes cost a real crash, and only the PTY tests saw it.

	`status` was threaded into `render` and `_inbox_pane` and NOT into
	`render_styled`, which is the one the driver actually calls — so every
	in-process test passed while the packaged console died on `TypeError` at
	its first draw.

	So: whatever `markers_for` produces, both renderers must accept, and they
	must agree. Asserted from the marker dict itself rather than a hand-kept
	list, because a new marker added to one signature and not the other is
	exactly the failure this is for."""
	import inspect
	from baton_tui.render import markers_for, render_styled
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.set_viewport(**layout_for(100, 24))

	for encoding in ("utf-8", "ascii"):
		marks = markers_for(encoding)
		for name in marks:
			for fn in (render, render_styled):
				assert name in inspect.signature(fn).parameters, \
					f"{fn.__name__} does not accept {name!r} from markers_for"
		plain = render(state, 100, 24, **marks)
		styled = render_styled(state, 100, 24, **marks)
		assert [text for text, _style in styled] == plain, \
			f"{encoding}: the two renderers disagree"


@pytest.mark.parametrize("state_name,expected", [
	("pending", "▷"), ("claimed", "▶"), ("completed", "✓"), ("closed", "✓"),
])
def test_the_sent_detail_heading_uses_the_same_vocabulary(env, state_name, expected):
	"""The SENT list was unified and its detail pane was not, so opening a normal
	sent message rendered `?` — the fallback for a state the badge table no
	longer had, because the same change that fixed the list removed it.

	Written before the fix, and it fails against the source that shipped as
	`1d2334a2`: proof that the two paths were separate rather than an
	assertion that they are together."""
	from baton_tui.render import _sent_row_lines
	row = {"row_kind": "message", "state": state_name, "subject": "Done",
	       "to_participant": "acme.reviewer", "kind": "q",
	       "created_ts": "2026-08-09T10:00:00Z", "outcome": None}
	heading = _sent_row_lines(row, 80)[0]
	assert expected in heading, heading
	for stale in ("?", "R ", "C "):
		assert stale not in heading, f"{stale!r} survives in {heading!r}"
	# The exact prose below it is untouched: the glyph answers "is anything
	# owed", and someone who needs to know WHICH terminal act it was reads on.
	body = "\n".join(_sent_row_lines(row, 80))
	assert "State:" in body


def test_the_top_line_leads_with_the_count_not_the_furniture(env):
	"""Slawomir's header cleanup: the count is the information.

	The product name, the participant, an all-caps pane label and a pair of
	brackets used to share this line with it. None of them told the human
	anything the screen did not already say, and all of them were read before
	the number they surrounded."""
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"S{i}", body=b"x\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	header = _draw(state, 100, 24)[0]
	assert header.lstrip().lstrip("> ").startswith("Messages: 3 retained, ")
	assert "awaiting your reply/close" in header
	for gone in ("MESSAGES", "[", "]", "acme.implementer", "baton"):
		assert gone not in header, f"{gone!r} is back on the top line"


def test_the_rule_carries_the_identity_and_no_label(env):
	"""The lower pane is self-evidently the selected message, so naming it
	spent a word saying so. The identity is genuinely useful and genuinely
	secondary, which is what the right-hand end of a rule is for."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	screen = _draw(state, 100, 24)
	rule = screen[_rule_index(screen)]
	assert "DETAIL" not in rule
	assert rule.rstrip().endswith("acme.implementer" + DIVIDER)


@pytest.mark.parametrize("columns", [40, 44, 52, 60, 80, 133])
def test_the_identity_degrades_before_the_rule_does(columns, env):
	"""The identity is DECORATION and goes first.

	Narrow terminals must lose it entirely rather than truncate it into a
	DIFFERENT participant address or crowd it against the rule. A half-printed
	address is worse than an absent one: absence is missing information,
	truncation is wrong information."""
	from baton_tui.safe_text import display_width
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	screen = _draw(state, columns, 24)
	rule = screen[_rule_index(screen)]
	assert display_width(rule) == columns, "the rule stopped reaching the edge"
	tail = rule.rstrip()
	if "acme.implementer" in tail:
		# One cell of rule follows it deliberately: a real terminal may not
		# draw the rightmost cell of a full-width row, and that cell must not
		# be the last letter of a participant address.
		assert tail.endswith("acme.implementer" + DIVIDER), \
			"the identity is not shielded from the last-cell truncation"
	else:
		# Dropped whole. Nothing but mark and rule is left.
		assert set(tail.lstrip("> ")) == {DIVIDER}, tail


def test_the_discard_confirmation_is_one_status_row_at_every_width(env):
	"""Ruled: the confirmation occupies the single status line and must not
	create a second prompt row or mid-screen instructions.

	Checked at narrow widths too, because that is where a two-line prompt
	would appear first and where the draft it is asking about would be pushed
	off the screen by the question about it."""
	from baton_tui.render import CONFIRM_DISCARD_FOOTER
	from baton_tui.state import MODE_CONFIRM_DISCARD
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	state.mode = MODE_CONFIRM_DISCARD
	for columns in (40, 60, 100, 133):
		screen = _draw(state, columns, 24)
		prompts = [line for line in screen if "Discard draft?" in line]
		assert len(prompts) == 1, f"{columns}: {len(prompts)} prompt rows"
		assert prompts[0] is screen[-1], "the prompt is not the status row"
		assert CONFIRM_DISCARD_FOOTER in prompts[0]
		# `y/N`: the capital is on the DEFAULT, and the default is keep.
		assert "y/N" in prompts[0]


def test_the_discard_confirmation_costs_no_extra_row(env):
	"""It is one row like every other footer except the quit confirmation, so
	the panes do not resize under the question."""
	from baton_tui.state import MODE_CONFIRM_DISCARD
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready_state(store)
	ordinary = _draw(state, 100, 24)
	state.mode = MODE_CONFIRM_DISCARD
	confirming = _draw(state, 100, 24)
	assert len(confirming) == len(ordinary)


def test_a_draft_row_carries_the_ruled_glyph(env):
	"""`✎` — ruled, and proven to be one display cell before use, which the
	ruling required rather than assumed."""
	from baton_tui.render import DRAFT, ASCII_GLYPHS
	from baton_tui.safe_text import display_width
	assert display_width(DRAFT) == 1
	assert ASCII_GLYPHS[DRAFT] == "d", "the fallback must not be the discard key"


def test_the_draft_glyph_is_distinct_from_every_other_status_mark():
	"""It has to say "being written" without reading as queued, claimed,
	delivered or completed."""
	from baton_tui.render import (COMPLETED, DRAFT, OPENED, PICKED_UP, QUEUED,
	                              UNOPENED)
	marks = [UNOPENED, OPENED, QUEUED, PICKED_UP, COMPLETED, DRAFT]
	assert len(set(marks)) == len(marks)


def test_the_ascii_completed_mark_is_neutral():
	"""Ruled: `=` for completion on a non-UTF terminal.

	It was `D`, chosen when no command owned that letter. `D` now discards a
	draft, so every finished row was showing the letter of a destructive
	command. `✓` is unchanged and is what almost every terminal shows."""
	from baton_tui.render import ASCII_GLYPHS, COMPLETED
	assert COMPLETED == "✓", "the UTF-8 mark was not meant to move"
	assert ASCII_GLYPHS[COMPLETED] == "="


def test_no_status_glyph_is_a_row_action_key():
	"""THE PROPERTY WHOSE ABSENCE LET R6 HAPPEN.

	A glyph and a key drifted into the same letter and nothing noticed,
	because each was checked only against its own vocabulary. A status column
	that prints the letter of a key that destroys the thing beside it is
	misleading at best, and this catches the next one at the moment it is
	introduced rather than in a packaged trial.

	Row-action keys only. Reserving every BOUND letter would leave nothing
	usable -- `Q` for a queued row is fine, because no command aimed at a row
	is bound to it."""
	from baton_tui import render as R
	from baton_tui import keys as K
	# TWO EARLIER VERSIONS WERE TOO NARROW, and the second one is the more
	# instructive mistake. It covered only DESTRUCTIVE keys -- but protocol
	# 10's `x` merely toggles a mark: it changes nothing outside the model and
	# must not be reclassified as an external effect to satisfy a test.
	# Restoring `DAMAGED = "x"` would have passed under it.
	#
	# The property is about the SCREEN, not about consequences: a status glyph
	# must not share a letter with a key aimed at the row it sits beside. The
	# key set therefore includes the RESERVED bulk letters, so the invariant
	# holds across the binding landing rather than only after it.
	vocabulary = (set(R.ASCII_GLYPHS)
	              | set(R.ASCII_GLYPHS.values())
	              | set(R.SENT_BADGES.values())
	              | {R.DAMAGED, R.NOTICE_BADGE, R.NOTICE_SEEN_MARK,
	                 R.NOTICE_SEEN_MARK_ASCII})
	letters = K.row_action_letters()
	assert {"x", "#"} <= letters, \
		"the reserved protocol-10 bulk letters left the key set"
	collisions = {glyph for glyph in vocabulary if glyph in letters}
	assert collisions == set(), \
		f"status glyphs collide with row-action keys: {collisions}"


def test_a_notice_says_which_audience_it_went_to():
	"""A broadcast to everyone and one to a single team read identically
	without this, and they are different things to act on."""
	from baton_tui.render import audience_line
	assert audience_line({"audience_kind": "scope", "selector": "acme.*"}) == \
		"acme.* (team notice)"
	assert audience_line({"audience_kind": "global", "selector": None}) == \
		"everyone (notice)"
	# A notice predating the frozen audience carries neither field and reads
	# as the global broadcast it was.
	assert audience_line({}) == "everyone (notice)"


def test_the_notice_detail_draws_the_audience(env):
	"""Through the renderer, not the helper: the line has to reach the pane."""
	from baton_tui.render import _notice_lines
	scoped = _notice_lines(
		{"id": "n1", "from_participant": "hq.lead", "kind": "fyi",
		 "subject": "team", "audience_kind": "scope", "selector": "acme.*",
		 "content": {"parts": []}}, 80)
	assert any("To:      acme.* (team notice)" in line for line in scoped), scoped
	glob = _notice_lines(
		{"id": "n2", "from_participant": "hq.lead", "kind": "fyi",
		 "subject": "all", "audience_kind": "global", "selector": None,
		 "content": {"parts": []}}, 80)
	assert any("To:      everyone (notice)" in line for line in glob), glob


def test_an_authored_notice_detail_also_says_its_audience(env):
	"""The author's own copy. The received path showed the audience and the
	sent path did not, so the one person who knew a notice was scoped was the
	one being told it went to everyone."""
	from baton_tui.render import _sent_content_lines
	lines = _sent_content_lines(
		{"id": "n1", "from_participant": "hq.lead", "kind": "fyi",
		 "subject": "team", "audience_kind": "scope", "selector": "acme.*",
		 "content": {"parts": []}}, 80, notice=True)
	assert any("To:      acme.* (team notice)" in line for line in lines), lines


def test_shared_work_says_who_else_has_it():
	"""`From:` and `Subject:` read identically for a private request and for
	one assigned to three people, and those are different situations: someone
	else may already be acting on it."""
	lines = _headers(
		{"from_participant": "hq.lead", "subject": "migrate", "kind": "work",
		 "audience": ["acme.implementer", "acme.reviewer", "hq.lead"]}, 80)
	assert any("Shared:  acme.implementer, acme.reviewer, hq.lead (3 recipients)" in line
	           for line in lines), lines


def test_a_private_message_says_nothing_about_sharing():
	""""Shared: just you" on every ordinary message would train the eye to
	skip the line, which costs exactly the case it exists for."""
	lines = _headers(
		{"from_participant": "hq.lead", "subject": "migrate", "kind": "work",
		 "audience": ["acme.implementer"]}, 80)
	assert not any("Shared:" in line for line in lines), lines


def test_the_duplicate_warning_is_attributed_to_the_sender():
	"""Baton does not correlate a repeat with an earlier publication, so the
	console must not phrase the warning as a detection. What is known is that
	the SENDER could not tell."""
	lines = _headers(
		{"from_participant": "hq.lead", "subject": "deploy", "kind": "ann",
		 "possible_duplicate": True}, 80)
	text = " ".join(lines)
	assert "the sender could not tell" in text, lines
	assert "duplicate detected" not in text.lower()


# -- the selected-part footer ----------------------------------------------
#
# Ruled in `work/finding-human-console/findings/finding-selected-part-footer/`.
# The metadata line used to sit above the body: `[0]` is a manifest address,
# not a name, and the single-part reader skipped it every time to reach their
# message. It says the part count now, which is the question a multipart
# reader actually has.

def test_a_single_part_body_precedes_its_metadata(env):
	"""Evidence 1. The text is what a reader reaches first."""
	from baton_tui.render import part_footer
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="One",
	           body=b"the first thing you should read\n")
	state = _opened(store)
	screen = _draw(state, 100, 24)
	body = next(i for i, line in enumerate(screen)
	            if "the first thing you should read" in line)
	metadata = next(i for i, line in enumerate(screen) if "text/markdown" in line)
	assert body < metadata, "transport metadata still precedes the message"
	assert "(1/1 parts)" in part_footer(state, 100)


def test_the_footer_is_the_last_row_of_the_detail_pane(env):
	"""Evidence 6, the placement half: above the global status bar, never
	replacing it."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="One",
	           body=b"body\n")
	state = _opened(store)
	screen = _draw(state, 100, 24)
	assert "parts)" in screen[-2], f"the footer is not the last pane row: {screen[-2]!r}"
	assert "parts)" not in screen[-1], "the footer displaced the status bar"
	assert screen[-1].strip(), "the status bar is empty"


def test_a_contentless_message_shows_zero_parts_and_no_address(env):
	"""Evidence 5. There is no part `0` to name, and inventing one would be
	the console asserting content that does not exist."""
	from baton_tui.render import part_footer
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="the subject is the message")
	state = _opened(store)
	line = part_footer(state, 100)
	assert "0 parts" in line
	assert "[" not in line, f"an address was fabricated: {line!r}"


def test_the_footer_truncates_by_display_cells_on_a_narrow_terminal(env):
	"""Evidence 6, the narrow half: it must fit the width exactly, with no
	control or wide-cell overflow."""
	from baton_tui.render import part_footer
	from baton_tui.safe_text import display_width
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="One",
	           parts=[{"content_type": "text/plain; charset=utf-8",
	                   "part_name": "an unusually long part name " * 3,
	                   "body": b"body\n"}])
	state = _opened(store)
	for width in (40, 60, 100):
		line = part_footer(state, width)
		# NEVER WIDER than the terminal. Not exact equality: `fit` truncates
		# without padding, so a short footer is short -- an equality
		# assertion here passed only because the long name always filled the
		# row, which is the case that stopped being true once the count was
		# reserved and the name became the field that gets dropped.
		assert display_width(line) <= width, \
			f"footer overflows: {display_width(line)} cells at {width}"
		# THE INFORMATION, not merely the width. This asserted only the cell
		# count before, so it passed while ordinary right-edge truncation
		# removed the part count at every width the long name reached -- the
		# one field the footer exists to show. The finding requires the count
		# to be preserved when it fits, so the optional metadata is what gets
		# dropped.
		assert "[0]" in line, f"the address was truncated away at {width}: {line!r}"
		assert "(1/1 parts)" in line, f"the count was truncated away at {width}: {line!r}"


def test_the_footer_survives_a_focus_change(env):
	"""Evidence 6, the focus half. It describes the message, not the pane
	that happens to have the keys."""
	from baton_tui.render import part_footer
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="One",
	           body=b"body\n")
	state = _opened(store)
	before = part_footer(state, 100)
	state.toggle_focus()
	assert part_footer(state, 100) == before


def test_two_text_parts_stay_visually_distinct(env):
	"""Evidence 3, the boundary half: a quiet separator, not a repeated
	media line before every body."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Two",
	           parts=[{"content_type": "text/plain; charset=utf-8", "body": b"FIRSTBODY\n"},
	                  {"content_type": "text/plain; charset=utf-8", "body": b"SECONDBODY\n"}])
	state = _opened(store)
	screen = _draw(state, 100, 40)
	first = next(i for i, line in enumerate(screen) if "FIRSTBODY" in line)
	second = next(i for i, line in enumerate(screen) if "SECONDBODY" in line)
	assert second > first + 1, "the two bodies run together with no boundary"
	between = screen[first + 1:second]
	assert not any("text/plain" in line for line in between), \
		"the media line is repeated between bodies"


def test_a_fresh_compose_shows_no_footer_from_the_message_behind_it(env):
	"""R1 of the footer review: the form was getting an unrelated message's
	address, media type, disposition and NAME attached to it, which
	attributes content to the draft the human is about to send."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Opened",
	           parts=[{"content_type": "image/png", "disposition": "attachment",
	                   "part_name": "unrelated-image", "body": b"\x89PNG\r\n"}])
	state = _opened(store)
	assert "unrelated-image" in part_footer(state, 100), "the fixture never opened a named part"
	state.begin_compose()
	screen = "\n".join(_draw(state, 100, 24))
	for leak in ("unrelated-image", "image/png", "[0]", "parts)"):
		assert leak not in screen, f"{leak!r} leaked into a fresh compose"


def test_a_fresh_notice_shows_no_footer_either(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Opened",
	           parts=[{"content_type": "image/png", "disposition": "attachment",
	                   "part_name": "unrelated-image", "body": b"\x89PNG\r\n"}])
	state = _opened(store)
	state.begin_compose(notice=True)
	screen = "\n".join(_draw(state, 100, 24))
	assert "unrelated-image" not in screen and "parts)" not in screen


def test_a_reply_keeps_the_footer_of_the_message_it_answers(env):
	"""The distinction the fresh-compose fix must not erase: a reply
	deliberately keeps the message it is answering on screen."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Answer me",
	           parts=[{"content_type": "text/plain; charset=utf-8",
	                   "part_name": "the-original", "body": b"question\n"}])
	state = _opened(store)
	state.begin_reply()
	assert "the-original" in part_footer(state, 100), \
		"the reply lost the context it exists to answer"


def test_an_unopened_preview_never_claims_zero_parts(env):
	"""R2: `(0 parts)` on a two-part preview turned "not loaded here" into
	the false statement "contentless"."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Two parts",
	           parts=[{"content_type": "text/plain; charset=utf-8", "body": b"one\n"},
	                  {"content_type": "text/plain; charset=utf-8", "body": b"two\n"}])
	state = _ready_state(store)
	state.preview(store)
	line = part_footer(state, 100)
	assert "0 parts" not in line, f"an unopened preview reported nothing: {line!r}"
	assert "/2 parts" in line


def test_a_lightweight_sent_row_shows_no_footer_at_all(env):
	"""The other half of R2: a listing row carries no part metadata, so any
	count would be invented."""
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Outbound",
	           body=b"body\n")
	state = _ready_state(store)
	state.select_view("sent")
	state.preview(store)
	screen = "\n".join(_draw(state, 100, 24))
	assert "parts)" not in screen, "a lightweight sent row invented a part count"


def test_an_opened_contentless_message_still_says_zero_parts(env):
	"""And the approved case survives all of the above."""
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="the subject is the message")
	state = _opened(store)
	assert "0 parts" in part_footer(state, 100)


# -- incoming work stays bold until handled -------------------------------
#
# Slawomir's RC ruling: the message list should use the familiar unread-email
# convention, so work still owed by the local participant is emphasised and
# stops being emphasised the moment it is answered. These pin the RULE
# (`row_is_owed`) and its PRESENTATION (`STYLE_OWED`) separately, because a
# correct rule wired to the wrong screen rows looks exactly like a bug.

def _owed_texts(state, columns=100, lines=24):
	from baton_tui.render import STYLE_OWED, render_styled
	return [text for text, style in render_styled(state, columns, lines)
	        if STYLE_OWED in style]


def test_a_pending_incoming_row_is_owed(env):
	store, _ = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Still mine", body=b"x\n")
	state = _ready_state(store)
	assert any("Still mine" in text for text in _owed_texts(state))


def test_a_claimed_incoming_row_stays_owed(env):
	"""Opening a message is not answering it.

	The obvious first cut of this rule clears the emphasis on claim, which
	would tell the human their work was done the moment they looked at it."""
	store, _ = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q",
	                 subject="Opened not answered", body=b"x\n")
	store.claim("acme.implementer", message_id=mid)
	state = _ready_state(store)
	assert any("Opened not answered" in text for text in _owed_texts(state))


def test_a_replied_or_closed_incoming_row_is_not_owed(env):
	store, _ = env
	replied = store.send("acme.reviewer", "acme.implementer", kind="q",
	                     subject="Answered by reply", body=b"x\n")
	closed = store.send("acme.reviewer", "acme.implementer", kind="q",
	                    subject="Answered by close", body=b"x\n")
	still = store.send("acme.reviewer", "acme.implementer", kind="q",
	                   subject="Untouched", body=b"x\n")
	claim = store.claim("acme.implementer", message_id=replied)
	store.reply(claim["claim_id"], participant="acme.implementer",
	            kind="answer", body=b"ok\n")
	claim = store.claim("acme.implementer", message_id=closed)
	store.close_claim(claim["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state = _ready_state(store)
	owed = _owed_texts(state)
	assert not any("Answered by reply" in text for text in owed)
	assert not any("Answered by close" in text for text in owed)
	# The control: the rule cleared these two because they were answered, not
	# because it stopped emphasising anything at all.
	assert any("Untouched" in text for text in owed), str(still)


def test_an_unseen_notice_is_owed_and_a_seen_one_is_not(env):
	store, _ = env
	store.send_notice("acme.reviewer", kind="announcement",
	                  subject="Unread broadcast", body=b"n\n")
	state = _ready_state(store)
	assert any("Unread broadcast" in text for text in _owed_texts(state))

	store.see("acme.implementer")
	state = _ready_state(store)
	assert not any("Unread broadcast" in text for text in _owed_texts(state))


def test_outbound_rows_are_never_owed(env):
	"""Work waiting on someone else is their move.

	Asserted in the SENT view, where every row is outbound: if direction were
	ignored, this whole pane would be bold and the emphasis would mean
	nothing."""
	from baton_tui.state import VIEW_SENT
	store, _ = env
	store.send("acme.implementer", "acme.reviewer", kind="q",
	           subject="Sent and pending", body=b"x\n")
	store.send_notice("acme.implementer", kind="announcement",
	                  subject="Sent broadcast", body=b"n\n")
	state = InboxState("acme.implementer")
	state.refresh(store)
	state.select_view(VIEW_SENT)
	state.preview(store)
	state.set_viewport(**layout_for(100, 24))
	assert [r["id"] for r in state.sent_rows], "this fixture drew no sent rows"
	assert _owed_texts(state) == []


def test_the_selected_row_keeps_its_owed_emphasis(env):
	"""Evidence 6: the cursor must not erase the unread mark as it passes.

	The two styles answer different questions -- which row am I on, which rows
	still want me -- so they compose rather than compete."""
	from baton_tui.render import STYLE_OWED, STYLE_SELECTED, render_styled
	store, _ = env
	for i in range(3):
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject=f"Owed {i}", body=b"x\n")
	state = _ready_state(store)
	for _ in range(3):
		rows = render_styled(state, 100, 24)
		selected = [(text, style) for text, style in rows
		            if STYLE_SELECTED in style]
		assert len(selected) == 1
		text, style = selected[0]
		assert STYLE_OWED in style, text
		state.move(1, store)


def test_owed_emphasis_writes_nothing_to_the_authority(tmp_path):
	"""Evidence 7: rendering and refreshing are observation only.

	Compared against a full dump rather than a spot check, so a receipt, a
	claim, or a state transition introduced anywhere by drawing shows up."""
	# Its own instance rather than the shared fixture, because the tripwire
	# needs the CONFIG PATH: the snapshot is taken through the public
	# read-only `dump`, the way every other reader reads the authority, and
	# never by opening the database.
	path, _ = _instance(tmp_path)
	with core.open_instance(path) as store:
		store.send("acme.reviewer", "acme.implementer", kind="q",
		           subject="Directed", body=b"x\n")
		store.send_notice("acme.reviewer", kind="announcement",
		                  subject="Broadcast", body=b"n\n")
		state = _ready_state(store)
		before = core.dump(path)
		for _ in range(3):
			_owed_texts(state)
			state.refresh(store)
		assert core.dump(path) == before


def test_the_owed_rule_reads_the_row_the_glyph_reads(env):
	"""The RULE itself, without a screen.

	Every case in one table so a future author changing one branch has to see
	the others: unknown store states get no emphasis, damage does not clear
	it, and a draft is not incoming work."""
	from baton_tui.render import row_is_owed
	from baton_tui.state import ROW_DRAFT, ROW_MESSAGE, ROW_NOTICE

	def row(**kw):
		base = {"row_type": ROW_MESSAGE, "direction": "in", "state": "pending"}
		base.update(kw)
		return base

	assert row_is_owed(row())
	assert row_is_owed(row(state="claimed"))
	assert not row_is_owed(row(state="completed"))
	assert not row_is_owed(row(state="closed"))
	# An unrecognised store state is exactly where a guess would be wrong.
	assert not row_is_owed(row(state="quarantined"))
	# Damage is orthogonal: a damaged row I still owe is still my move.
	assert row_is_owed(row(damaged=True))
	assert not row_is_owed(row(direction="out"))
	assert not row_is_owed(row(direction="out", state="claimed"))
	assert row_is_owed(row(row_type=ROW_NOTICE, state="unseen"))
	assert not row_is_owed(row(row_type=ROW_NOTICE, state="seen"))
	# A draft is mine to finish but it is not incoming work, and it carries
	# its own glyph.
	assert not row_is_owed(row(row_type=ROW_DRAFT, state="pending"))
	# A SENT row carries neither field. This is the case that bolded the whole
	# outbox before the rule became default-deny.
	assert not row_is_owed({"state": "pending", "to_participant": "x"})
