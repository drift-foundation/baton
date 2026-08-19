"""W35: the `:` bar is a real editable line.

`work/records/2026/08/finding-command-buffer-cursor-editing/`. Up and
Down recalled submitted commands, but the recalled line had no editable
caret: printable input appended and Backspace removed only the last
character. Correcting one operand in the middle meant deleting the whole
suffix and typing it again — which defeats the recall-edit-resubmit
workflow the history feature exists for. The W26 regression named
"editing a recalled entry" only ever changed the final character, so it
could not see the gap.

The 2026-08-18 ruling, approved by Slawomir, is a NON-MODAL line editor:

- Left/Right move one character; Home/End and Ctrl-A/Ctrl-E jump to the
  ends;
- Backspace removes before the caret, Delete removes under it, printable
  input inserts at it;
- printable `h`, `l`, `i` and `a` stay literal command text — no hidden
  normal mode, no second cursor grammar;
- Esc keeps its existing visible meaning: cancel without executing.

The caret is presentation state shared by freshly typed, recalled,
reverse-search-adopted, seeded and completion-expanded drafts, and
editing never touches history or the authority before Enter.
"""

from __future__ import annotations

import curses
import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work.tui.app import Console, command_window          # noqa: E402
import fixtures as fx                                           # noqa: E402

CTRL_A = 1
CTRL_E = 5
CTRL_R = 18
TAB = 9
ESC = 27
ENTER = 10
BACKSPACE = curses.KEY_BACKSPACE
DELETE = curses.KEY_DC
LEFT = curses.KEY_LEFT
RIGHT = curses.KEY_RIGHT
HOME = curses.KEY_HOME
END = curses.KEY_END


@pytest.fixture()
def console(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	console = Console(store, "lang", "ada", config_path=config_path)
	console.database = database
	yield console
	store.close()


def _type(console, text):
	for character in text:
		console.handle(ord(character))


def _keys(console, *keys):
	for key in keys:
		console.handle(key)


def _open(console):
	console.handle(ord(":"))


def _submit(console, text):
	_open(console)
	_type(console, text)
	console.handle(ENTER)


def _state(console):
	return console.command, console.command_caret


# -- the reported defect -----------------------------------------------------

def test_a_recalled_command_is_edited_in_its_middle(console):
	"""The report, exactly. Recall a long command, walk back into an
	operand, and correct it WITHOUT deleting the suffix.

	Against the pre-W35 bar every Left is ignored and the insert lands
	at the end, so this reads `...title=oldbody=b` — which is the
	defect."""
	_submit(console, "create team=lang kind=bug title=old body=b")
	_open(console)
	console.handle(curses.KEY_UP)
	assert _state(console) == (
		"create team=lang kind=bug title=old body=b", 42)

	# walk left over ` body=b` (7) and over `old` (3) to sit after `=`
	_keys(console, *([LEFT] * 10))
	assert console.command_caret == 32
	_keys(console, DELETE, DELETE, DELETE)     # remove `old` under the caret
	_type(console, "new")
	assert _state(console) == (
		"create team=lang kind=bug title=new body=b", 35)


def test_backspace_removes_before_the_caret_not_the_last_character(console):
	"""The other half of the report: Backspace was a suffix operation.
	Here it must remove the character the caret is standing after, in
	the middle of the line."""
	_open(console)
	_type(console, "detail work=W12")
	_keys(console, LEFT, LEFT)                 # caret between `W` and `12`
	console.handle(BACKSPACE)
	assert _state(console) == ("detail work=12", 12)


def test_insertion_at_the_beginning_middle_and_end(console):
	"""The acceptance boundary names all three positions."""
	_open(console)
	_type(console, "bcd")
	_keys(console, HOME)
	_type(console, "a")
	assert _state(console) == ("abcd", 1)
	_keys(console, END)
	_type(console, "e")
	assert _state(console) == ("abcde", 5)
	_keys(console, LEFT, LEFT)
	_type(console, "X")
	assert _state(console) == ("abcXde", 4)


# -- the ruled key map -------------------------------------------------------

def test_home_end_and_the_readline_spellings_agree(console):
	_open(console)
	_type(console, "detail work=W1")
	for to_start in (HOME, CTRL_A):
		_keys(console, END)
		console.handle(to_start)
		assert console.command_caret == 0
	for to_end in (END, CTRL_E):
		_keys(console, HOME)
		console.handle(to_end)
		assert console.command_caret == len("detail work=W1")


def test_hlia_stay_literal_command_text(console):
	"""The ruling's whole reason for being non-modal: ordinary command
	entry is already an insertion context, so the vi movement letters
	must remain characters. A modal editor would have eaten these."""
	_open(console)
	_type(console, "hail")
	assert _state(console) == ("hail", 4)
	_keys(console, HOME)
	_type(console, "hlia")
	assert _state(console) == ("hliahail", 4)


def test_esc_still_cancels_without_executing(console):
	before = hashlib.sha256(
		open(console.database, "rb").read()).hexdigest()
	_open(console)
	_type(console, "close work=W1 rationale=x outcome=satisfying")
	_keys(console, HOME, RIGHT, RIGHT)
	console.handle(ESC)
	assert console.command is None and console.command_caret == 0
	assert console.history == [], "a cancelled line entered history"
	assert hashlib.sha256(
		open(console.database, "rb").read()).hexdigest() == before


def test_the_caret_stops_at_both_ends(console):
	"""Movement is clamped, and the boundary deletions are no-ops
	rather than the old suffix behaviour sneaking back in."""
	_open(console)
	_type(console, "ab")
	_keys(console, *([LEFT] * 9))
	assert console.command_caret == 0
	console.handle(BACKSPACE)
	assert _state(console) == ("ab", 0), \
		"Backspace at the start deleted something"
	_keys(console, *([RIGHT] * 9))
	assert console.command_caret == 2
	console.handle(DELETE)
	assert _state(console) == ("ab", 2), \
		"Delete at the end deleted something"


def test_an_empty_buffer_survives_every_editing_key(console):
	_open(console)
	_keys(console, LEFT, RIGHT, HOME, END, CTRL_A, CTRL_E, BACKSPACE,
	      DELETE)
	assert _state(console) == ("", 0)
	assert console.command is not None, "an editing key closed the bar"


# -- submission and history immutability -------------------------------------

def test_enter_submits_the_whole_line_not_the_part_before_the_caret(console):
	_open(console)
	_type(console, "detail work=W1")
	_keys(console, HOME)
	console.handle(ENTER)
	assert console.history == ["detail work=W1"]
	assert console.command is None and console.command_caret == 0


def test_editing_a_recalled_entry_never_mutates_history(console):
	"""The recalled line is an independent DRAFT. This is the case W26
	could not reach: an INTERIOR edit, on an entry recalled twice."""
	_submit(console, "detail work=W1")
	_submit(console, "detail work=W2")
	_open(console)
	_keys(console, curses.KEY_UP, curses.KEY_UP)
	assert console.command == "detail work=W1"
	_keys(console, LEFT)
	_type(console, "0")
	assert _state(console) == ("detail work=W01", 14)
	assert console.history == ["detail work=W1", "detail work=W2"], \
		"an interior edit reached back into history"

	# and walking away and back re-recalls the ORIGINAL, not the edit
	_keys(console, curses.KEY_DOWN, curses.KEY_DOWN, curses.KEY_UP,
	      curses.KEY_UP)
	assert console.command == "detail work=W1"


def test_down_past_the_newest_restores_the_draft_and_its_caret(console):
	"""`the draft, exactly as it was` — which after W35 includes where
	the operator had left the caret. Restoring the characters and
	throwing the caret to the end would be a different draft."""
	_submit(console, "detail work=W1")
	_open(console)
	_type(console, "say body=half-written")
	_keys(console, LEFT, LEFT, LEFT)
	assert console.command_caret == 18
	_keys(console, curses.KEY_UP)
	assert console.command == "detail work=W1"
	_keys(console, curses.KEY_DOWN)
	assert _state(console) == ("say body=half-written", 18)


# -- composition with the other bar behaviours -------------------------------

def test_completion_leaves_the_caret_after_what_it_typed(console):
	"""W27 completes by TYPING the remaining characters, so it goes
	through the caret like everything else."""
	_open(console)
	_type(console, "det")
	console.handle(TAB)
	assert console.command.startswith("detail")
	assert console.command_caret == len(console.command)


def test_completion_declines_when_the_caret_is_not_at_the_end(console):
	"""Tab completes the buffer's LAST token, which is not the token an
	interior caret is in. This caught a real defect in the first cut of
	this Work: completion types its characters through the same path
	ordinary keys use, so once that path inserted at the caret, Tab
	spliced `ail` into position 0 and produced `adet`. Declining is the
	same conservatism the function already applies to an ambiguous
	candidate — a repeated Tab never chooses for the operator, and that
	includes never choosing WHERE."""
	_open(console)
	_type(console, "det")
	_keys(console, HOME)
	console.handle(TAB)
	assert _state(console) == ("det", 0), \
		"completion rewrote a line the caret was not at the end of"
	# moving back to the end restores ordinary completion
	_keys(console, END)
	console.handle(TAB)
	assert console.command.startswith("detail")
	assert console.command_caret == len(console.command)


def test_reverse_search_adoption_lands_the_caret_at_the_end(console):
	_submit(console, "detail work=W1")
	_open(console)
	console.handle(CTRL_R)
	_type(console, "W1")
	console.handle(RIGHT)                      # adopt
	assert console.reverse is None
	assert _state(console) == ("detail work=W1", 14)
	# and the adopted line is then an ordinary editable buffer
	_keys(console, LEFT)
	_type(console, "0")
	assert _state(console) == ("detail work=W01", 14)


def test_reverse_search_cancel_restores_the_draft_and_its_caret(console):
	_submit(console, "detail work=W1")
	_open(console)
	_type(console, "say body=x")
	_keys(console, LEFT, LEFT)
	assert console.command_caret == 8
	console.handle(CTRL_R)
	_type(console, "detail")
	console.handle(ESC)
	assert console.reverse is None
	assert _state(console) == ("say body=x", 8)


def test_the_say_seed_removal_keeps_the_caret_where_it_was_looking(console):
	"""W28 removes its own `thread=` seed when the operator supplies an
	explicit one. The caret has to ride that splice: throwing it to the
	end would move the operator away from the operand they are typing."""
	work = _seed_thread(console)
	_open(console)
	_type(console, "say")
	assert console.seeded_say is not None, "the fixture never seeded"
	seeded = console.command
	_type(console, "body=hello thread=T99")
	assert console.seeded_say is None, "the seed was not reconciled away"
	assert "thread=T99" in console.command
	assert console.command.count("thread=") == 1
	# the caret is still at the end of what was just typed
	assert console.command_caret == len(console.command)
	assert seeded and work


class _Screen:
	def addnstr(self, *args):
		pass


def _seed_thread(console):
	"""Put the console where the `say` seed has a thread to name — the
	same detail-pane setup W81's own suite uses."""
	from baton_work import transitions as tr
	created = tr.create_work(console.store, team="lang", kind="bug",
	                         title="seedable", origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")
	console.detail_work = created["work_id"]
	console.mode = "detail"
	console._render_detail(_Screen(), 24, 100)
	return created["work_id"]


# -- the pure viewport -------------------------------------------------------

def test_a_fitting_line_is_drawn_whole_with_the_caret_on_the_character():
	assert command_window(":detail", 7, 40) == (":detail", 7)
	assert command_window(":detail", 0, 40) == (":detail", 0)
	assert command_window(":detail", 3, 40) == (":detail", 3)


def test_a_caret_near_the_start_of_a_long_line_stays_anchored_left():
	"""Scrolling a buffer whose beginning is being edited would move
	text for no reason. The hidden tail is NAMED instead."""
	typed = ":" + "abcdefghij" * 4
	text, column = command_window(typed, 3, 20)
	assert text.startswith(":abc") and text.endswith(">")
	assert len(text) == 20
	assert column == 3


def test_a_caret_past_the_first_screenful_scrolls_and_names_the_head():
	typed = ":" + "abcdefghij" * 4
	text, column = command_window(typed, len(typed), 20)
	assert text.startswith("<"), text
	assert text.endswith("hij"), text
	# the caret stays on screen with a free cell after it
	assert column == len(text) <= 20 - 1


def test_the_caret_is_always_visible_at_every_position_and_width():
	"""The property, swept rather than sampled: for any caret and any
	usable width the caret column lands inside the terminal, and the
	drawn text never exceeds the space it was given."""
	typed = ":create team=lang kind=bug title=a-fairly-long-title body=x"
	for avail in range(4, 80):
		for caret in range(len(typed) + 1):
			text, column = command_window(typed, caret, avail)
			assert 0 <= column <= avail, (avail, caret, column)
			assert len(text) <= avail, (avail, caret, text)


def test_a_resize_recomputes_the_window_from_the_same_buffer():
	"""The window is a PURE function of buffer, caret and width — there
	is no remembered scroll offset — so a resize cannot strand the
	caret. Narrow then wide, same inputs, and the wide one shows the
	line whole."""
	typed = ":detail work=W1 and-a-long-tail-that-overflows"
	narrow, narrow_column = command_window(typed, 10, 20)
	wide, wide_column = command_window(typed, 10, 80)
	assert wide == typed and wide_column == 10
	assert len(narrow) <= 20 and narrow_column <= 20
	# and asking again gives exactly the same answer
	assert command_window(typed, 10, 20) == (narrow, narrow_column)


# -- display cells ------------------------------------------------------------

def test_wide_characters_keep_the_caret_on_its_own_cell():
	"""A caret counted in characters and drawn in cells drifts by one
	column per wide character, and every later keystroke then lands
	somewhere the operator was not pointing."""
	typed = ":say body=" + "漢字" + "tail"
	# three characters into the buffer is `s`, `a`, `y` — still cells
	assert command_window(typed, 4, 60)[1] == 4
	# after both wide characters: 10 narrow cells + 2 wide = 14
	caret = typed.index("t", 10)
	assert command_window(typed, caret, 60)[1] == 14
	# and the whole line measures in cells, not characters
	assert command_window(typed, caret, 15)[0] != typed


def test_editing_around_wide_characters_moves_whole_characters(console):
	console.handle(ord(":"))
	console._set_command("say body=漢字tail")
	assert console.command_caret == len("say body=漢字tail")
	_keys(console, LEFT, LEFT, LEFT, LEFT)
	assert console.command_caret == len("say body=漢字")
	console.handle(BACKSPACE)
	assert _state(console) == ("say body=漢tail", 10), console.command
	console.handle(BACKSPACE)
	assert _state(console) == ("say body=tail", 9)


# -- the authority boundary ---------------------------------------------------

def test_editing_reads_and_writes_no_authority_bytes(console):
	"""Command editing is presentation state. Nothing below Enter may
	touch the store."""
	before = hashlib.sha256(
		open(console.database, "rb").read()).hexdigest()
	_submit(console, "detail work=W1")
	_open(console)
	_keys(console, curses.KEY_UP)
	_keys(console, HOME, RIGHT, RIGHT, DELETE, LEFT, CTRL_E, CTRL_A,
	      BACKSPACE, END)
	_type(console, "-edited")
	console.handle(ESC)
	assert hashlib.sha256(
		open(console.database, "rb").read()).hexdigest() == before


# -- the real terminal --------------------------------------------------------
#
# W25's finding is why these exist rather than only the pure-state tests
# above: a key that `handle()` understands can still be invisible from a
# terminal, because `keypad(1)` asks for APPLICATION cursor mode and a
# terminal left in NORMAL mode sends the other spelling. A test that
# injects `curses.KEY_LEFT` cannot fail for that; only a terminal can.

RAW_LEFT = b"\x1b[D"
RAW_RIGHT = b"\x1b[C"
RAW_HOME = b"\x1b[H"
RAW_END = b"\x1b[F"
RAW_DELETE = b"\x1b[3~"


@pytest.fixture()
def instance(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug"]}})
	return config_path, database


def _pty_or_skip():
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty")
	import ptyharness
	return ptyharness


def test_raw_cursor_sequences_edit_the_bar_on_a_real_terminal(instance):
	"""Interior editing, driven as bytes a terminal actually sends.

	The line is typed, walked back over with NORMAL-mode Left, corrected
	with a raw Delete, and the result read off the screen a human would
	see. Esc then cancels, so nothing is submitted."""
	ptyharness = _pty_or_skip()
	config, database = instance
	before = hashlib.sha256(open(database, "rb").read()).hexdigest()
	script = [(b":detail work=W12", 0.6)]
	script += [(RAW_LEFT, 0.15)] * 2               # caret between W and 12
	script += [(RAW_DELETE, 0.3), (b"9", 0.3),     # W12 -> W92
	           (b"\x1b", 0.3), (b"qy", 0.4)]
	text, status, steps = ptyharness.drive(config, "lang.ada", script)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	edited, (row, col, visible) = ptyharness.replay(steps[-3],
	                                                cursor=True)
	bar = edited[31]
	assert bar.startswith(":detail work=W92"), bar
	assert visible, "the caret is hidden during command entry"
	# the caret sits after the digit just typed, INSIDE the line
	assert (row, col) == (31, len(":detail work=W9")), (row, col, bar)
	assert hashlib.sha256(open(database, "rb").read()).hexdigest() == before


def test_raw_home_and_end_reach_the_bar_on_a_real_terminal(instance):
	"""Home and End carry exactly the application/normal-mode skew W25
	measured for the arrows, so the ruled contract needs both spellings
	decoded or two of its keys work on one terminal and not the other."""
	ptyharness = _pty_or_skip()
	config, _database = instance
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":work=W1", 0.6),
		(RAW_HOME, 0.3), (b"detail ", 0.4),        # insert at the start
		(RAW_END, 0.3), (b"!", 0.4),               # and back to the end
		(b"\x1b", 0.3), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	after_home, (_row, home_col, _v) = ptyharness.replay(steps[2],
	                                                     cursor=True)
	assert after_home[31].startswith(":detail work=W1"), after_home[31]
	assert home_col == len(":detail "), home_col
	after_end, (row, col, visible) = ptyharness.replay(steps[4],
	                                                   cursor=True)
	assert after_end[31].startswith(":detail work=W1!"), after_end[31]
	assert visible and (row, col) == (31, len(":detail work=W1!"))


def test_ctrl_a_and_ctrl_e_need_no_escape_decoding_at_all(instance):
	"""The readline spellings are plain control bytes, so they are the
	terminal-proof path to both ends however the terminal spells Home
	and End. That is why the ruling names them beside Home/End rather
	than instead of them."""
	ptyharness = _pty_or_skip()
	config, _database = instance
	text, status, steps = ptyharness.drive(config, "lang.ada", [
		(b":work=W1", 0.6),
		(b"\x01", 0.3), (b"detail ", 0.4),         # Ctrl-A
		(b"\x05", 0.3), (b"!", 0.4),               # Ctrl-E
		(b"\x1b", 0.3), (b"qy", 0.4)])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	bar = ptyharness.replay(steps[4])[31]
	assert bar.startswith(":detail work=W1!"), bar


def test_a_narrow_terminal_keeps_an_interior_caret_visible(instance):
	"""The viewport question the acceptance boundary asks: a line longer
	than the row, edited in its MIDDLE, must still show the caret. The
	pre-W35 bar could only ever anchor the end of the buffer."""
	ptyharness = _pty_or_skip()
	config, _database = instance
	line = (b":create team=lang kind=bug "
	        b"title=a-long-title-that-overflows body=still-typing")
	script = [(line, 0.9)]
	script += [(RAW_LEFT, 0.06)] * 30
	script += [(b"", 0.5), (b"\x1b", 0.3), (b"qy", 0.4)]
	text, status, steps = ptyharness.drive(
		config, "lang.ada", script, columns=44, lines=24, settle=1.2)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen, (row, col, visible) = ptyharness.replay(
		steps[-3], columns=44, lines=24, cursor=True)
	bar = screen[23]
	assert visible, "the caret is hidden while editing a scrolled line"
	assert row == 23 and 0 <= col < 44, (row, col, bar)
	# the caret is INSIDE the drawn text, not pinned to either end, and
	# the window names what it is hiding
	assert bar.startswith("<"), f"no left clip marker: {bar!r}"
	assert 0 < col < len(bar.rstrip()), (col, bar)
	# and the character the caret stands on is the one 30 back from the
	# end of what was typed
	expected = line.decode()[-30]
	assert bar[col] == expected, (bar[col], expected, bar)
