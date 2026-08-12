"""`M` — save the whole message to a file the human names.

Everything here is driven through the REAL KEY, never the model method. `m`
shipped fixed in the model and still broken through the key, twice; the method
is not the affordance.
"""

from __future__ import annotations

import json
import os

import pytest

from baton_tui import keys as K
from baton_tui.state import MODE_BROWSE, MODE_COMPOSE, MODE_SAVE_PATH

from test_tui_driver import _press, _ready, _select, _settle, env, _instance  # noqa: F401


def _saved(path):
	with open(path, "rb") as handle:
		return json.loads(handle.read().decode("utf-8"))


def _outbox(tmp_path):
	out = tmp_path / "keep"
	out.mkdir(exist_ok=True)
	return out


# -- the key opens a path editor, and only from browse ---------------------

def test_M_opens_a_destination_editor_on_an_opened_message(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Keep me",
	           body=b"body\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF)             # claim and open
	_press(state, store, ord("M"))
	assert state.mode == MODE_SAVE_PATH
	assert state.save_path_draft.endswith(".baton.json")
	assert state.save_path_draft.startswith(state.projection_dir + os.sep)


def test_M_refuses_a_message_that_has_not_been_opened(env, tmp_path):
	"""The preview boundary, unchanged. Writing a whole message to disk is
	reading it in the most durable form there is."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Unopened",
	           body=b"secret\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, ord("M"))
	assert state.mode == MODE_BROWSE
	assert "unopened" in state.status
	assert not list(pathlib_iter(state.projection_dir))


def pathlib_iter(directory):
	return sorted(os.listdir(directory))


def test_M_does_nothing_from_a_compose_mode(env, tmp_path):
	"""While a message is being written, `M` is the letter M — the box would
	otherwise swallow the keystrokes of the draft."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, ord("n"))               # compose: recipient picker
	before = state.mode
	_press(state, store, ord("M"))
	assert state.mode == before != MODE_SAVE_PATH


def test_M_needs_no_selected_part(env, tmp_path):
	"""Unlike `m`. A subject-only message exports perfectly well — its
	subject IS the message — so requiring a part would refuse the one case
	where the export is the only way to keep it."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Nothing but a subject")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF)
	assert state.selected_part is None
	_press(state, store, ord("M"))
	assert state.mode == MODE_SAVE_PATH
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	written = pathlib_iter(state.projection_dir)
	assert len(written) == 1
	document = _saved(os.path.join(state.projection_dir, written[0]))
	assert document["message"]["subject"] == "Nothing but a subject"
	# `null` for a subject-only message -- the core's rule, asserted here so
	# the console cannot quietly acquire a different one.
	assert document["message"]["content"] is None


def test_M_is_offered_without_a_projection_directory_and_opens_an_empty_box(env):
	"""`m` needs one because it invents a filename. `M` does not: the human
	types the path. What it must NOT do is propose the working directory."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	assert state.projection_dir == ""
	_press(state, store, K.ENTER_LF)
	assert state.affordances()["save_message"] is True
	_press(state, store, ord("M"))
	assert state.mode == MODE_SAVE_PATH
	assert state.save_path_draft == ""


# -- typing in the box -----------------------------------------------------

def test_every_command_letter_is_text_inside_the_box(env, tmp_path):
	"""No browse command may fire from behind a text box — the same rule the
	pickers and confirmations follow."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("M"))
	_press(state, store, ord("q"), ord("c"), ord("n"), ord("D"), ord("/"))
	assert state.mode == MODE_SAVE_PATH
	assert state.save_path_draft == "qcnD/"


def test_backspace_and_ctrl_u_edit_the_box(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF, ord("M"))
	assert state.save_path_draft
	_press(state, store, K.CTRL_U)
	assert state.save_path_draft == ""
	_press(state, store, ord("a"), ord("b"), K.BACKSPACE_KEY)
	assert state.save_path_draft == "a"


def test_esc_cancels_and_writes_nothing(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF, ord("M"))
	_press(state, store, K.ESC)
	assert state.mode == MODE_BROWSE
	assert state.save_target is None
	assert pathlib_iter(state.projection_dir) == []


def test_an_empty_box_refuses_rather_than_guessing(env):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("M"))
	assert state.save_path_draft == ""
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_SAVE_PATH, "an empty path left the box"
	# The REFUSAL, distinguishable from the box's own empty prompt -- which
	# also mentions an absolute path, so asserting on that alone would pass
	# against an Enter that did nothing at all.
	assert "nothing typed" in state.status


# -- writing ---------------------------------------------------------------

def test_enter_writes_the_whole_message_at_the_typed_path(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Whole",
	           parts=[{"content_type": "text/plain; charset=utf-8", "body": b"one\n"},
	                  {"content_type": "text/plain; charset=utf-8", "body": b"two\n"}])
	state = _ready(store)
	out = _outbox(tmp_path) / "chosen.baton.json"
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	assert str(out) in state.status
	document = _saved(out)
	assert document["format"] == "baton.whole-message"
	assert [part["text"] for part in document["message"]["content"]["parts"]] == \
		["one\n", "two\n"]


def test_a_refusal_keeps_the_box_and_the_target(env, tmp_path):
	"""Every refusal here is about the PATH, and every one of those is fixed
	by editing the text already typed. Dropping to the list would make the
	human press `M` on the right row again to get their own words back."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Whole",
	           body=b"x\n")
	state = _ready(store)
	out = _outbox(tmp_path) / "chosen.baton.json"
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in "relative.baton.json"])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_SAVE_PATH
	assert state.save_target is not None
	assert state.save_path_draft == "relative.baton.json"
	assert "failed" in state.status
	# And the same box, corrected, writes.
	_press(state, store, K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	assert _saved(out)["message"]["subject"] == "Whole"


def test_the_target_is_the_row_M_was_pressed_on_not_whatever_moved_under_it(env, tmp_path):
	"""The two-second poll refreshes the list under a human who is typing a
	path. Re-resolving the selection at Enter is how a save lands on the
	wrong message.

	Driven in the SENT view, where a row is readable WITHOUT being opened --
	so there is no `opened` identity holding the target still and the
	selection is the only thing naming it. That is the state the poll can
	actually move under a human, and the one a re-resolving accept gets
	wrong."""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="First",
	           body=b"first\n")
	state = _ready(store)
	_press(state, store, ord("o"))               # the SENT view
	assert state.opened is None
	target = state._action_row()["id"]
	out = _outbox(tmp_path) / "chosen.baton.json"
	_press(state, store, ord("M"), K.CTRL_U)
	assert state.save_target[1] == target
	# A second message is sent, and the list moves under the open box.
	#
	# The cursor is moved DIRECTLY rather than by a keystroke, and that is the
	# only honest way to write this: the box swallows every movement key, and
	# the poll deliberately carries the cursor by identity, so today nothing a
	# human can do would move it. Both of those are properties of code that
	# could change; the guarantee under test is that accept never consults the
	# list at all, which is what makes it survive them changing.
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Second",
	           body=b"second\n")
	state.refresh(store)
	state.sent_cursor = 1 - state.sent_cursor
	assert state._action_row()["id"] != target, (
		"the list did not move; this test proves nothing")
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	assert _saved(out)["message"]["subject"] == "First"


def test_enter_writes_the_EXACT_path_typed_including_a_trailing_space(env, tmp_path):
	"""A filename may lawfully end in a space. Quietly writing a different
	name than the one on screen is the failure this box exists to prevent —
	an earlier version applied `strip()` and did exactly that."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Exact",
	           body=b"x\n")
	state = _ready(store)
	spaced = _outbox(tmp_path) / "trailing "
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(spaced)])
	assert state.save_path_draft.endswith(" ")
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	# THE TYPED NAME, not its stripped sibling.
	assert pathlib_iter(str(spaced.parent)) == ["trailing "]
	assert _saved(spaced)["message"]["subject"] == "Exact"


def test_a_whitespace_only_path_is_refused_by_the_core_not_silently_emptied(env):
	"""The other side of the same rule: `strip()` would have turned this into
	the empty box's own refusal, which says something different and true of a
	different situation."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, ord(" "), ord(" "))
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_SAVE_PATH
	assert state.save_path_draft == "  "
	assert "nothing typed" not in state.status
	assert "failed" in state.status


def test_the_model_refuses_unreceived_content_even_if_dispatch_lets_it_through(env):
	"""ONE rule asked in TWO places, on purpose. The dispatch gate and the
	model check are both real: a boundary that lives only in the affordance
	table is one refactor away from not existing, and `m` has already been
	fixed in one of the two places while staying broken in the other."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Unopened",
	           body=b"secret\n")
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	shapes = set()
	for index in range(len(state.rows)):
		state.cursor = index
		state.preview(store)
		row = state._action_row()
		shapes.add(row.get("row_type"))
		assert state.affordances()["save_message"] is False
		# The model's own refusal, reached past the gate that would have
		# stopped the key.
		assert state.begin_save_message() is False
		assert state.mode == MODE_BROWSE
		assert state.save_target is None
		# ROW-KIND-CORRECT wording. Telling someone their unseen NOTICE is an
		# "unopened message" sends them looking for a step that does not
		# apply to it -- and the direct guard used to say exactly that while
		# dispatch said the right thing.
		if row.get("row_type") == "notice":
			assert "notice" in state.status and "seen" in state.status
		else:
			assert "unopened" in state.status
	assert shapes == {"message", "notice"}, "both unreceived shapes must be swept"


def test_saving_twice_to_the_same_path_is_accepted_as_a_resume(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="Twice",
	           body=b"x\n")
	state = _ready(store)
	out = _outbox(tmp_path) / "chosen.baton.json"
	for _ in range(2):
		_press(state, store, ord("M"), K.CTRL_U)
		_press(state, store, *[ord(ch) for ch in str(out)])
		_press(state, store, K.ENTER_LF)
		assert state.mode == MODE_BROWSE, state.status
	assert pathlib_iter(str(out.parent)) == ["chosen.baton.json"]


def test_an_existing_unrelated_file_is_never_overwritten(env, tmp_path):
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	out = _outbox(tmp_path) / "precious.txt"
	out.write_bytes(b"do not lose me\n")
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_SAVE_PATH, "a clobbering save left the box"
	assert out.read_bytes() == b"do not lose me\n"


# -- notices ---------------------------------------------------------------

def test_a_seen_notice_saves_and_an_unseen_one_refuses(env, tmp_path):
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	out = _outbox(tmp_path) / "notice.baton.json"
	_press(state, store, ord("M"))
	assert state.mode == MODE_BROWSE
	assert "seen" in state.status
	# Enter marks it seen, which is what delivers its content.
	_press(state, store, K.ENTER_LF)
	_press(state, store, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	document = _saved(out)
	assert document["notice"]["subject"] == "Cast"
	assert document["notice"]["audience_kind"] == "global"


def test_the_seeded_name_says_which_kind_it_is(env, tmp_path):
	store = env
	store.send_notice("hq.lead", kind="announcement", subject="Cast", body=b"n\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF, ord("M"))
	assert os.path.basename(state.save_path_draft).startswith("notice-")
	assert state.save_path_draft.endswith(".baton.json")


def test_the_seeded_name_is_the_ruled_spelling_with_the_fields_untransformed(env, tmp_path):
	"""`<kind>-<created>-<id>.baton.json`, with both fields exactly as the
	authority holds them.

	An earlier version rewrote every non-alphanumeric character against a
	hypothetical future id scheme. That was a policy nobody ruled, it did not
	match the alphabet its own comment claimed, and it made the seeded name
	disagree with the id it names — so a human could not find the message from
	the file."""
	store = env
	mid = store.send("acme.reviewer", "acme.implementer", kind="q", subject="S",
	                 body=b"x\n")
	state = _ready(store)
	state.projection_dir = str(_outbox(tmp_path))
	_press(state, store, K.ENTER_LF, ord("M"))
	row = state._action_row()
	assert state.save_path_draft == os.path.join(
		state.projection_dir,
		f"message-{row['created_ts']}-{mid}.baton.json")
	# The id is READABLE in the name, which is the point of putting it there.
	assert mid in state.save_path_draft
	# And it stays one path component: nothing in the seed reaches a
	# directory the human did not choose.
	assert os.path.dirname(state.save_path_draft) == state.projection_dir


# -- sent mail -------------------------------------------------------------

def test_a_sent_message_saves(env, tmp_path):
	"""Anything viewable in full is saveable — the ruling `m` already
	follows. A sent row carries no `row_type`, which is the shape that made
	the search filter and the `m` boundary both wrong once."""
	store = env
	store.send("acme.implementer", "acme.reviewer", kind="q", subject="Mine",
	           body=b"outbound\n")
	state = _ready(store)
	state.refresh(store)
	_press(state, store, ord("o"))               # the SENT view
	out = _outbox(tmp_path) / "sent.baton.json"
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	assert state.mode == MODE_SAVE_PATH, state.status
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	assert _saved(out)["message"]["subject"] == "Mine"


# -- help ------------------------------------------------------------------

def test_the_help_screen_documents_M():
	from baton_tui.keys import HELP_SECTIONS
	rows = [row for _title, entries in HELP_SECTIONS for row in entries]
	assert any(row[0] == "M" for row in rows), "M is undocumented"


# -- the box is readable ---------------------------------------------------

def test_the_path_being_typed_is_on_screen(env, tmp_path):
	"""A text box the human cannot read is not a box. The packaged console
	found this: `M` opened, the prompt said "Enter writes it", and the path
	appeared nowhere — so the only way to learn where the file would land was
	to press Enter and see."""
	from baton_tui.render import render
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in "/keep/mine.baton.json"])
	assert "/keep/mine.baton.json" in "\n".join(render(state, 100, 24))
	# And backspacing is visible too, not just typing.
	_press(state, store, K.BACKSPACE_KEY)
	screen = "\n".join(render(state, 100, 24))
	assert "/keep/mine.baton.jso" in screen
	assert "/keep/mine.baton.json" not in screen


def test_a_path_too_long_for_the_row_keeps_its_END_on_screen(env):
	"""Head-anchored truncation would hide exactly the characters being
	typed, so a long destination would look frozen under the caret."""
	from baton_tui.render import render
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q", subject="S", body=b"x\n")
	state = _ready(store)
	_press(state, store, K.ENTER_LF, ord("M"), K.CTRL_U)
	long_path = "/" + "directory/" * 12 + "kept.baton.json"
	_press(state, store, *[ord(ch) for ch in long_path])
	screen = "\n".join(render(state, 60, 24))
	assert "kept.baton.json" in screen, screen
	assert "…" in screen, "a clipped row must say so"
	assert long_path.endswith(screen.splitlines()[-1].lstrip("…")[-15:])
	# `columns - 1`: the driver writes at most that many cells to avoid the
	# curses bottom-right wrap, so a row filled to the full width loses its
	# LAST cell -- which on a tail-anchored row is the character just typed.
	assert all(len(line) <= 59 for line in render(state, 60, 24)
	           if "baton.json" in line)


# -- every row shape -------------------------------------------------------

def test_an_answered_and_a_closed_inbound_row_both_save(env, tmp_path):
	"""The ruling `m` already follows: anything viewable in full is saveable.
	A resolved row has no claim left, and requiring one is exactly the defect
	that sent a human to the CLI for their own mail."""
	store = env
	answered = store.send("acme.reviewer", "acme.implementer", kind="q",
	                      subject="Answered", body=b"a\n")
	closed = store.send("acme.reviewer", "acme.implementer", kind="q",
	                    subject="Closed", body=b"c\n")
	claim = store.claim("acme.implementer", message_id=answered)
	store.reply(claim["claim_id"], participant="acme.implementer", kind="a",
	            body=b"done\n")
	shut = store.claim("acme.implementer", message_id=closed)
	store.close_claim(shut["claim_id"], participant="acme.implementer",
	                  outcome="done")
	state = _ready(store)
	state.refresh(store)

	for subject in ("Answered", "Closed"):
		index = next(i for i, row in enumerate(state.rows)
		             if row.get("subject") == subject)
		state.cursor = index
		state.preview(store)
		assert state.affordances()["save_message"] is True, subject
		out = _outbox(tmp_path) / f"{subject}.baton.json"
		_press(state, store, ord("M"), K.CTRL_U)
		assert state.mode == MODE_SAVE_PATH, (subject, state.status)
		_press(state, store, *[ord(ch) for ch in str(out)])
		_press(state, store, K.ENTER_LF)
		assert state.mode == MODE_BROWSE, (subject, state.status)
		assert _saved(out)["message"]["subject"] == subject


def test_a_notice_this_participant_AUTHORED_saves_without_being_seen(env, tmp_path):
	"""An author never gets a seen receipt for their own broadcast — nothing
	delivered it to them. The core authorizes them as the sender, and the
	console must not invent a receipt requirement the authority does not
	have."""
	store = env
	store.send_notice("acme.implementer", kind="announcement",
	                  subject="Mine to publish", body=b"n\n")
	state = _ready(store)
	state.refresh(store)
	_press(state, store, ord("o"))               # the SENT view
	index = next(i for i, row in enumerate(state.view_rows)
	             if row.get("subject") == "Mine to publish")
	state.sent_cursor = index
	state.preview(store)
	out = _outbox(tmp_path) / "authored.baton.json"
	_press(state, store, ord("M"), K.CTRL_U)
	assert state.mode == MODE_SAVE_PATH, state.status
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_BROWSE, state.status
	assert _saved(out)["notice"]["subject"] == "Mine to publish"


def test_a_transient_row_offers_M_and_the_core_refuses_it(env, tmp_path):
	"""The console does NOT duplicate the retention rule. It is the sender's
	contract, enforced where the contract lives; a second copy in the front
	end is one refactor from disagreeing with the first — and the refusal is
	visible either way."""
	store = env
	store.send("acme.reviewer", "acme.implementer", kind="q",
	           subject="Ephemeral", body=b"gone soon\n", retention="transient")
	state = _ready(store)
	out = _outbox(tmp_path) / "transient.baton.json"
	_press(state, store, K.ENTER_LF)             # claim and open
	assert state.affordances()["save_message"] is True
	_press(state, store, ord("M"), K.CTRL_U)
	_press(state, store, *[ord(ch) for ch in str(out)])
	_press(state, store, K.ENTER_LF)
	assert state.mode == MODE_SAVE_PATH, "the refusal must keep the box"
	assert "transient" in state.status
	assert not out.exists()
