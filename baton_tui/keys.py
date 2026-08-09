"""Key -> model event mapping, decided outside curses.

The curses loop must contain nothing worth testing. Everything that could be
wrong -- which key does what, whether a keystroke is destructive, what typing
does in reply mode -- is decided here, on plain integers, and is therefore
assertable without a terminal.
"""

from __future__ import annotations

from .state import (MODE_BROWSE, MODE_COMPOSE, MODE_CONFIRM_QUIT,
                    MODE_CONFIRM_SEND, MODE_HELP, MODE_NOTICE,
                    MODE_PICK_RECIPIENT, MODE_PICK_ROOT, MODE_REPLY)

# Events the driver may raise on the model. Names, not behaviour: the model
# owns what each one does.
QUIT = "quit"
UP = "up"
DOWN = "down"
PAGE_UP = "page_up"
PAGE_DOWN = "page_down"
SCROLL_UP = "scroll_up"
SCROLL_DOWN = "scroll_down"
OPEN = "open"
REPLY = "reply"
CLOSE = "close"
MATERIALIZE = "materialize"
READ_PART = "read_part"
REFRESH = "refresh"
SEND = "send"
CANCEL = "cancel"
TYPE = "type"
BACKSPACE = "backspace"
COMPOSE = "compose"
COMPOSE_NOTICE = "compose_notice"
NEXT_FIELD = "next_field"
PREV_FIELD = "prev_field"
PART_UP = "part_up"
PART_DOWN = "part_down"
CONFIRM = "confirm"
CONFIRM_SEND = "confirm_send"
DECLINE_SEND = "decline_send"
DECLINE = "decline"
FIRST = "first"
LAST = "last"
PREFIX_G = "prefix_g"
PICK = "pick"
PICK_PAGE = "pick_page"
VIEW_INBOX_KEY = "view_inbox"
VIEW_SENT_KEY = "view_sent"
EDIT_BODY = "edit_body"
CARET_LEFT = "caret_left"
CARET_RIGHT = "caret_right"
CARET_HOME = "caret_home"
CARET_END = "caret_end"
DELETE_FORWARD = "delete_forward"
KILL_TO_START = "kill_to_start"
TOGGLE_FOCUS = "toggle_focus"
HSCROLL_LEFT = "hscroll_left"
HSCROLL_RIGHT = "hscroll_right"
OPEN_HELP = "open_help"
CLOSE_HELP = "close_help"
IGNORE = "ignore"

KEY_UP, KEY_DOWN, KEY_NPAGE, KEY_PPAGE, KEY_RESIZE = 259, 258, 338, 339, 410
# curses names for the editing keys, plus the raw sequences a terminal sends
# when the terminfo database is not consulted -- the same lesson the arrow
# keys taught in round two.
KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_DC = 260, 261, 262, 360, 330
ESC, ENTER_LF, ENTER_CR, BACKSPACE_KEY, DELETE_KEY = 27, 10, 13, 263, 127
TAB, SHIFT_TAB = 9, 353
CTRL_U, CTRL_D, CTRL_E = 21, 4, 5
CTRL_R = 18

# Escape-sequence tails for the keys we care about, decoded HERE rather than
# relying on curses keypad translation.
#
# Trial defect: on the deployment terminal `getch()` returned the raw bytes
# 27, 91, 66 for Down instead of KEY_DOWN, so arrow keys did nothing at all --
# `curses.wrapper` enables keypad, but the translation still did not happen
# (missing or mismatched terminfo will do it). Depending on the terminal
# database to make arrows work is a dependency the console does not need:
# these sequences are fixed by ANSI, so decoding them costs a lookup table and
# removes the failure mode entirely.
ESCAPE_SEQUENCES = {
	"[A": KEY_UP, "OA": KEY_UP,
	"[B": KEY_DOWN, "OB": KEY_DOWN,
	"[5~": KEY_PPAGE, "[6~": KEY_NPAGE,
	"[Z": SHIFT_TAB,
	"[H": KEY_PPAGE, "[F": KEY_NPAGE,          # Home/End page the inbox
}


def decode_escape(tail: str) -> int | None:
	"""Translate the bytes AFTER an ESC into a key code, or None if this is
	not a sequence we handle. A bare ESC (empty tail) stays ESC, which is what
	cancels a draft -- so the decoder must never swallow it."""
	return ESCAPE_SEQUENCES.get(tail)

_BROWSE = {
	ord("q"): QUIT, ord("k"): UP, ord("j"): DOWN,
	KEY_UP: UP, KEY_DOWN: DOWN, KEY_PPAGE: PAGE_UP, KEY_NPAGE: PAGE_DOWN,
	CTRL_U: PAGE_UP, CTRL_D: PAGE_DOWN,
	# `J`/`K` are GONE. Detail scrolling is `j`/`k` under DETAIL focus now,
	# and two competing navigation models is one more than a console should
	# have. Removed rather than aliased: a hidden spelling is a key only its
	# author can press.
	TAB: TOGGLE_FOCUS, SHIFT_TAB: TOGGLE_FOCUS,
	ENTER_LF: OPEN, ENTER_CR: OPEN,
	# `r` OPENS THE EDITOR. Slawomir's trial finding, and it supersedes the
	# earlier pairing: the reply people actually write is a body in their
	# editor, and the subject-only quick reply is the rare one. The easier key
	# serves the common action, so lowercase `r` is the full reply and shifted
	# `R` is the quick subject line -- the reverse of what shipped before.
	ord("r"): EDIT_BODY, ord("c"): CLOSE, ord("m"): MATERIALIZE,
	# `v` READS an external part into the pane. Verified unbound before taking
	# it. Distinct from `m`: `m` writes a projection and the core refuses to
	# for an external part, because it is already a file -- so without `v`
	# there was no key at all for the one thing a human wants to do with it.
	ord("v"): READ_PART,
	# `?` opens the modal shortcut list. Verified unbound; it is not a letter
	# anyone types as a command, and it is what people already press.
	ord("?"): OPEN_HELP,
	# `R` is the QUICK reply: the subject line is the message, no editor. It
	# took the browse `e` binding, which is REMOVED rather than kept as an
	# undiscoverable alias: a second spelling nobody is told about is a key
	# that only its author can press. `Ctrl-E` still promotes a quick draft
	# to the editor from inside it.
	ord("R"): REPLY,
	# `g` is the `gg` prefix, so manual refresh cannot live there. It is
	# Ctrl+r, because `R` is a reply key. A prefix key must do NOTHING on its
	# own -- a `g` that refreshed would make every abandoned `gg` a side
	# effect.
	ord("g"): PREFIX_G, ord("G"): LAST, CTRL_R: REFRESH,
	ord("n"): COMPOSE, ord("N"): COMPOSE_NOTICE,
	ord("i"): VIEW_INBOX_KEY,
	ord("o"): VIEW_SENT_KEY,
	# `[`/`]` are the ONLY part navigation now. `h`/`l` scroll the focused
	# DETAIL pane sideways, because once DETAIL focus exists Vim `h`/`l` not
	# moving within it is a visible contradiction in the model. `H`/`L` are
	# removed rather than aliased -- a spelling nobody is told about is a key
	# only its author can press.
	ord("["): PART_UP, ord("]"): PART_DOWN,
	ord("h"): HSCROLL_LEFT, ord("l"): HSCROLL_RIGHT,
	KEY_LEFT: HSCROLL_LEFT, KEY_RIGHT: HSCROLL_RIGHT,
}

# The help screen's content, and the ONE place the shortcut list lives.
#
# Written as data beside the table it describes, so a binding cannot be added
# without a visible gap here -- a test asserts every browse EVENT appears. A
# help screen maintained separately from the key map is a help screen that is
# wrong within a month, and wrong help is worse than none: it is believed.
HELP_SECTIONS = (
	("Browse the list", (
		("Tab", "focus the list or the detail pane; navigation follows it",
		 (TOGGLE_FOCUS,)),
		("j / k, arrows", "LIST focus: select — a directed message is CLAIMED "
		                  "and opened; DETAIL focus: scroll one line", (UP, DOWN)),
		("gg / G", "LIST: first / last row; DETAIL: top / bottom",
		 (PREFIX_G, FIRST, LAST)),
		("Ctrl+u / Ctrl+d, PgUp/PgDn", "page the focused pane",
		 (PAGE_UP, PAGE_DOWN)),
		("i / o", "MESSAGES / Sent filter", (VIEW_INBOX_KEY, VIEW_SENT_KEY)),
		("Ctrl+r", "refresh now (it also polls every 2s)", (REFRESH,)),
		("?", "this screen; q or Esc closes it", (OPEN_HELP, CLOSE_HELP)),
		("q", "quit (asks if a claim is unresolved)", (QUIT,)),
	)),
	("Read a message", (
		# What Enter is still FOR. A directed row was claimed and opened when
		# it was selected, so describing Enter as the thing that claims sends
		# the human looking for a step that has already happened.
		("Enter", "mark an unseen notice seen and read it", (OPEN,)),
		("", "! is an unseen notice; ✓ one you have seen — its "
		     "content is not redelivered", ()),
		("[ / ]", "previous / next part", (PART_UP, PART_DOWN)),
		("h / l, arrows", "DETAIL focus: scroll sideways, for content too long "
		                  "to wrap", (HSCROLL_LEFT, HSCROLL_RIGHT)),
		("v", "read an external part's file — only from a claim you hold", (READ_PART,)),
		("m", "materialize the selected part — not an external one, it is already a file", (MATERIALIZE,)),
	)),
	("Reply and compose", (
		("r", "reply, or follow up on an answered row — straight into your "
		      "external editor", (EDIT_BODY,)),
		("R", "the same, but a quick one: the subject line IS the message",
		 (REPLY,)),
		("n", "new message: pick a recipient, then subject/attach", (COMPOSE,)),
		("Enter", "on an EMPTY attach field: choose a configured root, then "
		          "type the path INSIDE it — never root:path", ()),
		("N", "publish a notice", (COMPOSE_NOTICE,)),
		("Enter then y", "review, then send — from ANY field, and a subject "
		                 "alone is enough", (SEND, CONFIRM_SEND)),
		("Esc", "cancel a draft", (CANCEL, DECLINE_SEND)),
	)),
	("While typing", (
		("Ctrl+e", "edit the body in your external editor", ()),
		("Ctrl+u", "delete back to the start of the line", (KILL_TO_START,)),
		("Ctrl+a / End, arrows", "move the caret", (CARET_HOME, CARET_END,
		                                        CARET_LEFT, CARET_RIGHT)),
		("Tab", "next compose field", (NEXT_FIELD, PREV_FIELD)),
		("Backspace / Del", "delete either side of the caret",
		 (BACKSPACE, DELETE_FORWARD)),
		("a-z", "pick a recipient; Tab pages the picker", (PICK, PICK_PAGE)),
	)),
	# Help OWNS the lifecycle now. The detail pane used to end every preview
	# with `Enter: claim and open (takes ownership)` and its two siblings, and
	# every Sent row with the badge glossary. Those were removed as repeated
	# reference in the work area, so what they said has to be complete HERE --
	# removing an explanation is only safe if its one owner carries it.
	("Lifecycle", (
		("selecting", "a pending directed message is CLAIMED and opened: "
		              "ownership is taken and a reply or close is then owed", ()),
		("Enter", "on an unseen notice: records the receipt and opens it, "
		          "at-most-once — the content is not redelivered", ()),
		("Enter", "on a message already yours: reopens it; the reply or "
		          "close is still owed", ()),
		("r / R", "on a claim: resolves it", ()),
		("r / R", "on an answered or sent row: a follow-up, in reference to "
		          "it — a new message, never a second disposition", ()),
		("c", "close: a terminal disposition — only while you hold the claim", (CLOSE,)),
		("Y", "confirm quitting with a claim still owed", (CONFIRM, DECLINE)),
	)),
	# The one-cell status column, spelled out. It used to sit under every Sent
	# row as a permanent glossary; it is reference, so it lives here and in
	# the README.
	# The status column answers ONE question: does someone wait on me, and if
	# so have I read it and answered? Slawomir's trial ruling -- people think
	# in todo lists, not in store state machines. The exact protocol state is
	# still in the detail pane for diagnosis; this is how the LIST reads.
	# The status column answers who owns the next action while an item is
	# LIVE, and what became of it once it is TERMINAL. Direction shapes the
	# live marks and is deliberately absent from the terminal ones: the party
	# column already says who acted.
	("List notation — while it is live", (
		("•", "addressed to you and not yet opened", ()),
		("○", "opened and yours: a reply or close is still owed", ()),
		("▷", "you sent it; the recipient has not picked it up", ()),
		("▶", "they picked it up: the next action is owed by them", ()),
		("!", "a notice you have not seen", ()),
	)),
	("List notation — once it is done", (
		("✓", "nothing is owed: replied, closed, or a notice you have seen — "
		      "whichever side acted", ()),
		("", "which of those it was is in the detail pane, exactly", ()),
		("E / X", "expired / quarantined", ()),
		("N", "a notice you authored", ()),
		("x", "content withheld: its parts failed their pins", ()),
		("?", "a state this console does not understand — report it", ()),
	)),
)

# HUMAN-FACING KEY NOTATION, ruled during the trial and applied throughout the
# tables above and below:
#
#   Ctrl chords take a LOWER-case letter -- `Ctrl+e`, `Ctrl+u`, `Ctrl+r` --
#   because Shift is not part of the gesture and a capital implies it is.
#   A plain letter is upper-case only where Shift really is the difference:
#   `R`, `N`, `G`. Case alone says so; `Shift+r` is never written.
#   Named keys keep their conventional spelling: Enter, Esc, Tab, PgUp, PgDn.
#
# `^E` and `Ctrl-E` are gone from anything a human reads. The CONSTANTS are
# still `CTRL_E` and comments still say Ctrl-E, deliberately: churning code to
# match a presentation rule is how a rename turns into a diff nobody can
# review.
#
# What each NON-BROWSE mode actually offers, as `(label, keys)`.
#
# Beside the tables that decide it, and carrying the KEY CODES so a test can
# assert every advertised chord really dispatches in that mode. The browse
# footer used to be drawn in every mode, advertising `n new` and `^R refresh`
# in the help screen and open/reply/close from the row hidden behind the
# recipient picker -- keys the mode tables deliberately swallow.
# Each entry is `(label, keys, condition)`. `condition` is None for a control
# that is always meaningful here, or the name of a state-dependent affordance.
#
# "Legal AND meaningful", not merely mapped: `Tab` is a live key in a
# one-field notice and a one-page picker and changes nothing in either, so
# advertising it promises a change the key cannot make.
MODE_LEGENDS = {
	MODE_HELP: (
		("j/k scroll", (ord("j"), ord("k")), None),
		# "dismiss", not "close": `Esc close` reads as the `c close` action to
		# a human skimming the row, and it is not one -- help closes nothing.
		("? q Esc dismiss", (ord("?"), ord("q"), ESC), None),
	),
	MODE_PICK_RECIPIENT: (
		("a-z choose a recipient", (ord("a"), ord("z")), None),
		("Tab next page", (TAB,), "picker_paging"),
		("Esc cancel", (ESC,), None),
	),
	MODE_PICK_ROOT: (
		("a-z choose an attachment root", (ord("a"), ord("z")), None),
		("Tab next page", (TAB,), "picker_paging"),
		("Esc cancel", (ESC,), None),
	),
	MODE_REPLY: (
		("type to edit the subject line", (ord("a"),), None),
		("Ctrl+u kill to start", (CTRL_U,), None),
		("Ctrl+e editor", (CTRL_E,), None),
		("Enter reviews the send", (ENTER_LF,), None),
		("Esc cancel", (ESC,), None),
	),
	MODE_COMPOSE: (
		("type to edit", (ord("a"),), None),
		("Tab next field", (TAB,), "more_fields"),
		("Ctrl+u kill to start", (CTRL_U,), None),
		("Ctrl+e editor", (CTRL_E,), None),
		("Enter reviews the send", (ENTER_LF,), None),
		("Esc cancel", (ESC,), None),
	),
	MODE_NOTICE: (
		("type to edit", (ord("a"),), None),
		("Tab next field", (TAB,), "more_fields"),
		("Ctrl+u kill to start", (CTRL_U,), None),
		("Ctrl+e editor", (CTRL_E,), None),
		("Enter reviews the send", (ENTER_LF,), None),
		("Esc cancel", (ESC,), None),
	),
}

# Modes where every printable key is TEXT, not a command. Listed explicitly so
# adding a mode forces a decision about it rather than defaulting to
# "keystrokes are commands", which is the dangerous default.
_TEXT_MODES = (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE)


def map_key(key: int, mode: str) -> tuple[str, str | None]:
	"""(event, payload) for one keypress in one mode.

	Reply mode is deliberately a SEPARATE table rather than a set of
	exceptions: while typing, `q` is the letter q and `c` is the letter c. A
	shared table with guards is how a draft ends up quitting the application
	or closing a claim mid-sentence."""
	if mode == MODE_HELP:
		# A modal VIEW. Only closing it and scrolling it are live; nothing
		# else may fire from behind a screen the human is reading, which is
		# the same rule the recipient picker follows.
		if key in (ord("?"), ord("q"), ESC):
			return CLOSE_HELP, None
		if key in (ord("j"), KEY_DOWN, CTRL_D, KEY_NPAGE):
			return SCROLL_DOWN, None
		if key in (ord("k"), KEY_UP, CTRL_U, KEY_PPAGE):
			return SCROLL_UP, None
		return IGNORE, None
	if mode in (MODE_PICK_RECIPIENT, MODE_PICK_ROOT):
		# Letters SELECT here. No browse or compose command may fire from a
		# picker: the human is choosing who receives a message, or which trust
		# anchor an attachment is named against, and a stray `c` or `q`
		# reaching its browse meaning would be acting on the inbox behind the
		# dialogue.
		#
		# ONE table for both, deliberately: the root picker reuses the
		# recipient picker's conventions -- letters select, Tab pages, Esc
		# cancels -- and two tables would let them drift apart for no reason
		# the human could see.
		if key == ESC:
			return CANCEL, None
		if key == TAB:
			return PICK_PAGE, None
		if ord("a") <= key <= ord("z"):
			return PICK, chr(key)
		return IGNORE, None
	if mode == MODE_CONFIRM_SEND:
		# `Send? Y/n` -- conventional shell semantics, YES as the default, so
		# Enter answers it. The fast path is Enter, Enter.
		#
		# Everything that is NOT an answer is still swallowed: printable
		# characters must not reach the draft they are no longer editing, and
		# no browse command may fire from behind the question.
		if key in (ord("y"), ord("Y"), ENTER_LF, ENTER_CR):
			return CONFIRM_SEND, None
		if key in (ord("n"), ord("N"), ESC):
			return DECLINE_SEND, None
		return IGNORE, None
	if mode == MODE_CONFIRM_QUIT:
		# Only an explicit Y confirms. Everything else -- including Enter,
		# which a human hits reflexively -- means stay.
		return (CONFIRM if key in (ord("y"), ord("Y")) else DECLINE), None
	if mode in _TEXT_MODES:
		if key in (ESC,):
			return CANCEL, None
		if key in (ENTER_LF, ENTER_CR):
			return SEND, None
		# NOTE on `e`: it is bound to the editor in BROWSE only, and the text
		# modes are a separate table -- so inside the quick-reply subject
		# editor `e` is already just a letter, and needs no special case here.
		# One was written and removed: deleting it changed no test, which is
		# the definition of dead code that looks load-bearing.
		if key in (KEY_LEFT,):
			return CARET_LEFT, None
		if key in (KEY_RIGHT,):
			return CARET_RIGHT, None
		if key in (KEY_HOME, 1):          # 1 = Ctrl-A, the readline spelling
			return CARET_HOME, None
		if key == KEY_END:
			# Ctrl-E is the body editor here, so End has no control-key
			# spelling. Ctrl-A stays as Home because nothing else claims it.
			return CARET_END, None
		if key == KEY_DC:
			return DELETE_FORWARD, None
		if key == CTRL_U:
			# Kill to the start of the line, the readline spelling. In BROWSE
			# the same chord pages the list; these are separate tables, so
			# neither needs a guard against the other.
			return KILL_TO_START, None
		if key == CTRL_E:
			# A CONTROL key on purpose: every printable character in these
			# modes is text, so stealing one would make a letter unusable in
			# a message.
			return EDIT_BODY, None
		if key in (BACKSPACE_KEY, DELETE_KEY, 8):
			return BACKSPACE, None
		if key == TAB:
			return NEXT_FIELD, None
		if key == SHIFT_TAB:
			return PREV_FIELD, None
		if key == KEY_RESIZE:
			return REFRESH, None
		# Printable characters only. A control character in a draft would be
		# sent to another participant and rendered on THEIR terminal, so it is
		# refused at the keyboard as well as at the renderer.
		if 32 <= key < 127 or key > 159:
			try:
				return TYPE, chr(key)
			except ValueError:
				return IGNORE, None
		return IGNORE, None
	if key == KEY_RESIZE:
		return REFRESH, None
	return _BROWSE.get(key, IGNORE), None


# Events with an effect outside the console: they take ownership, consume a
# broadcast, publish, or write to the filesystem. MATERIALIZE belongs here --
# it writes a file, and a key sweep that treated it as observation would be
# asserting the wrong safety property.
EFFECTFUL = (OPEN, SEND, CLOSE, MATERIALIZE)


def is_destructive(event: str) -> bool:
	"""Events that change something outside the model. Keeps the mapping
	honest: exactly these, and nothing that merely moves or looks."""
	return event in EFFECTFUL
