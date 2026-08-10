"""Rendering: state -> a grid of text lines. No curses, no I/O.

Kept a pure function so the whole screen is assertable. Curses draws the
buffer this produces; it decides nothing. That split is what lets the hostile
cases be tested at all -- "an escape sequence never reaches the terminal" is a
statement about strings, and only stays true if the strings are the thing
being checked.

Every value that came from another participant goes through `safe_text` on the
way in. There is exactly one place that is done -- `_cell` -- so a new field
cannot be added to a row and quietly bypass it.
"""

from __future__ import annotations

from .safe_text import (display_width, fit, sanitize_block, sanitize_line,
                        split_cells, wrap, wrap_display, wrap_overflow)


def _wrapped(text: str, width: int, indent: str = "  ") -> list[str]:
	"""Detail lines that WRAP instead of clipping.

	`_cell` truncates, which is right for a fixed-width inbox column and wrong
	for content: once the tail is cut it cannot be scrolled to, so a body
	wider than the pane was simply unreadable. Continuation lines carry the
	same indent, so a wrapped paragraph still reads as one block."""
	available = max(1, width - display_width(indent))
	return [indent + line for line in wrap_display(text, available)]


def _wrapped_content(text: str, width: int, indent: str = "  ") -> list[str]:
	"""Part CONTENT, wrapped at whitespace with an oversized token left whole.

	The line may come back WIDER than the pane. That is the point: `h`/`l`
	scroll the detail sideways, so the tail has to still be there to reach.
	Applied to content only -- headers and the structural chrome keep eliding,
	because shifting a label off screen because one body line is long would
	make the pane unreadable to fix a line."""
	available = max(1, width - display_width(indent))
	return [indent + line for line in wrap_overflow(text, available)]


def _hwindow(line: str, width: int, offset: int) -> str:
	"""One content line, windowed horizontally at `offset` display cells.

	Nothing is discarded: what is off-screen is REACHABLE, and which side is
	hidden is stated with the ellipsis convention. Split by cells, never
	characters, so a wide glyph is never cut in half and the row never exceeds
	the terminal."""
	if display_width(line) <= width and offset == 0:
		return line
	_, tail = split_cells(line, offset)
	left = offset > 0
	room = width - (display_width(ELLIPSIS) if left else 0)
	head, rest = split_cells(tail, max(0, room))
	right = display_width(rest) > 0
	if right:
		head, _ = split_cells(head, max(0, display_width(head) - display_width(ELLIPSIS)))
	return (ELLIPSIS if left else "") + head + (ELLIPSIS if right else "")


def _wrapped_lossless(text: str, width: int, indent: str = "  ") -> list[str]:
	"""The same, for text that must not lose a character: drafts, compose
	fields, and the picker's addresses.

	Read-only content elides a token wider than the pane (Slawomir's ruling);
	editable text cannot, because hiding what someone is typing is a worse
	fault than hiding what they are reading. An ADDRESS cannot elide either --
	two accounts that differ only in their tail would render identically, and
	the picker exists to stop exactly that class of mistake."""
	available = max(1, width - display_width(indent))
	return [indent + line for line in wrap(text, available)]
from .safe_text import ELLIPSIS
from .state import (PICKER_LABELS, VIEW_SENT, MODE_COMPOSE, MODE_CONFIRM_QUIT,
                    MODE_CONFIRM_SEND, MODE_NOTICE,
                    FOCUS_DETAIL, FOCUS_LIST,
                    FOLLOW_UP_ANSWERED, FOLLOW_UP_SENT, IN_REFERENCE_TO,
                    MODE_HELP, MODE_PICK_RECIPIENT, MODE_PICK_ROOT, MODE_REPLY,
                    MODE_CONFIRM_DISCARD, ROW_DRAFT, ROW_MESSAGE, ROW_NOTICE,
                    SEV_ERROR, SEV_INFO,
                    SEV_SUCCESS,
                    SEV_WARNING, list_capacity, list_top)

# Severity markers. Text, not colour: the console must be readable over SSH on
# a terminal with no colour support, and severity that only exists as colour
# is invisible to anyone who cannot see it.
_SEVERITY_MARK = {SEV_INFO: "i", SEV_SUCCESS: "ok", SEV_WARNING: "!", SEV_ERROR: "ERR"}

MIN_COLUMNS = 40
MIN_LINES = 8

# The horizontal pane divider. U+2500 BOX DRAWINGS LIGHT HORIZONTAL is designed
# to join continuously between cells, so a row of them reads as one unbroken
# rule; ASCII `-` leaves visible gaps because the glyph does not reach the cell
# edges. One display cell wide either way (U+2500 is East-Asian "Ambiguous",
# which `display_width` counts as 1), so switching between them cannot change
# how many cells the rule occupies or how wide the row is.
DIVIDER = "\u2500"
DIVIDER_ASCII = "-"

# A notice this participant has SEEN, retained in the list. `✓` says the
# receipt exists without reading as New (which is the opposite state) or as
# Sent. `S` is the fallback, `S` for seen. ONE cell either way, which is the
# status column's width: the brackets were punctuation doing a job that
# alignment already does, and they cost two cells on every row.
NOTICE_SEEN_MARK = "✓"
NOTICE_SEEN_MARK_ASCII = "S"

# Default pane split, list:detail, after the one-ROW divider. The panes are
# STACKED, so the ratio divides HEIGHT and both panes are the full terminal
# width. Named so a future setting has one place to change; deliberately NOT
# configurable yet.
LIST_SHARE = 0.40
MIN_LIST_LINES = 1


def pane_heights(body_lines: int) -> tuple[int, int]:
	"""(list, detail) heights for a body this tall, the divider row excluded.

	THE one place this arithmetic lives, for exactly the reason the pane-WIDTH
	helper it replaces existed: render, the detail line count, the caret, the
	part-header marks and the selection styling all have to agree, or the rule
	lands on one row while the caret believes another.

	There is deliberately no pane-width helper any more. Stacked, both panes
	are `columns` wide, and a surviving 40/60 column split would have been a
	second authority quietly disagreeing with the screen."""
	usable = max(0, body_lines - 1)                 # the divider takes one row
	top = max(MIN_LIST_LINES, round(usable * LIST_SHARE))
	top = min(top, usable)                          # never more than there is
	detail = usable - top
	if detail == 0 and top > 1:
		top, detail = top - 1, 1                    # always leave a detail pane
	return top, detail


def divider_for(encoding: str | None) -> str:
	"""The best divider this terminal can actually render.

	A box-drawing character written to a non-UTF-8 terminal is worse than the
	ASCII rule it replaced: it becomes a replacement glyph or mojibake across
	the middle of the screen. Falls back rather than assuming."""
	if not encoding:
		return DIVIDER_ASCII
	try:
		DIVIDER.encode(encoding)
	except (LookupError, UnicodeEncodeError):
		return DIVIDER_ASCII
	return DIVIDER


def _cell(value, width: int) -> str:
	"""The ONLY door untrusted text passes through on its way to the screen."""
	return fit("" if value is None else str(value), width)


# What an INBOUND row says about the human's own obligation.
#
# Slawomir's model, from the trial: people think in todo lists, not in store
# state machines. The glyph answers one question -- does someone wait on me,
# and if so have I read it and answered? The protocol state is unchanged and
# stays exactly as it is in the detail pane; this is a perspective-aware
# reading of it, for the one participant looking at the screen.
# DIRECTION matters while an obligation is LIVE, because the human has to know
# who owns the next action. It stops mattering once the item is terminal: the
# party column already says who acted, and repeating it in the glyph is the
# duplication this column exists to avoid. So the live states come in two
# shapes and the terminal ones are shared.
UNOPENED = "•"          # inbound, and I have not opened it
OPENED = "○"            # inbound and mine; a reply or close is still owed
QUEUED = "▷"            # outbound, waiting for the other side to pick it up
PICKED_UP = "▶"         # outbound and theirs; they own the next action
COMPLETED = "✓"         # ordinarily finished: replied, closed, or seen
# `~` for withheld content, RULED. It was `x`, which protocol 10 binds as the
# bulk MARK key -- so a damaged row would have shown the letter of the key
# that selects it, in the column beside it. The glyph moved rather than the
# key: `x` for a checkbox is muscle memory a human already has, and a status
# mark is internal vocabulary nobody has ever typed. Move the cheap side.
#
# `~` reads as "approximate, not the real thing", which is what a row whose
# parts failed their pins IS.
DAMAGED = "~"
# A retained draft: being written, and never handed to the authority. Ruled.
# It says "in progress" without implying anything was queued, claimed,
# delivered or completed, and it is distinct from every mark above -- none of
# which can describe something the store has never seen.
DRAFT = "✎"

# Non-UTF-8 terminals. `Q`/`P` are the FALLBACK spelling of `▷`/`▶` rather
# than the normal presentation, and completion falls back to one
# direction-independent mark for the same reason `✓` is shared.
#
# The two live INBOUND fallbacks were not ruled, so these are mine and are
# flagged as such in the handoff: `*` for unopened, because it is the loudest
# ASCII mark available and unopened is the state that most wants attention,
# and `o` for opened, because it is the same shape as `○`.
# Lowercase `d` for a draft, ruled, and lowercase for a stated reason:
# uppercase `D` is the DISCARD key, and a status column that shows the letter
# of the destructive command next to the thing it destroys is an invitation.
#
# `=` for completion, ruled, and for the same reason one step removed. It was
# `D`, chosen when no command owned that letter; `D` now discards a draft, so
# every finished row on a non-UTF terminal was showing the letter of a
# destructive command. Harmless in dispatch and misleading to read. `=` is
# neutral, settled, and one cell in every encoding.
#
# UTF-8 is unaffected: `✓` is unchanged and is what almost every terminal
# actually shows.
ASCII_GLYPHS = {UNOPENED: "*", OPENED: "o", QUEUED: "Q", PICKED_UP: "P",
                COMPLETED: "=", DRAFT: "d"}


def _status_glyph(row: dict, notice_seen: str = NOTICE_SEEN_MARK) -> str:
	"""One cell, from the reader's point of view.

	`•` and `○` replace the old blank and `*`. A blank said "waiting for me"
	by saying nothing at all, which is the least visible thing on a screen for
	the state that most demands attention.

	`✓` replaces the inbound `R`, the outbound one AND `C`: what the list
	answers is whether anything is still owed, and once the answer is no, the
	mark is the same. Which side acted is in the party column; whether they
	replied or closed is in the detail pane. Neither needs a second telling
	in a one-cell column.

	Direction is read from the ROW, not from the caller, so an inbound and an
	outbound row in equivalent store states cannot disagree about which
	vocabulary they belong to."""
	if row["row_type"] == ROW_DRAFT:
		# Before every other test. A draft has no store state to read, so
		# falling through would ask questions about an entity the authority
		# has never seen.
		return DRAFT
	if row["row_type"] == ROW_NOTICE:
		# `!` is ATTENTION -- an unseen broadcast. Once seen it is history,
		# and the mark says the receipt exists rather than demanding a look.
		# `N` is deliberately NOT reused here: it reads as "new", which is the
		# opposite of what a seen notice is.
		return notice_seen if row.get("state") == "seen" else "!"
	if row.get("damaged"):
		return DAMAGED
	state = row.get("state")
	outbound = row.get("direction") == "out"
	if state in ("completed", "closed"):
		# ONE terminal mark. Replied and closed are different acts, and the
		# earlier version said so with `✓` against `C` -- ruled out: the
		# question the list answers is whether anything is still owed, and
		# the answer is the same either way. Which act it was stays exact in
		# the detail pane, for anyone who needs to know.
		return COMPLETED
	if state == "pending":
		return QUEUED if outbound else UNOPENED
	if state == "claimed":
		return PICKED_UP if outbound else OPENED
	# Anything else is a store state this reading has no human meaning for;
	# the lifecycle table names it rather than inventing a symbol.
	return exceptional_badge(row)


def layout_for(columns: int, lines: int, recipients=(), participant=None) -> dict | None:
	"""Pane heights for a terminal of this size, or None if it is too small.

	The arithmetic lives here so the driver does not reimplement it, but
	APPLYING it is the driver's job: it calls `state.set_viewport(**layout)`
	on start and on resize. Rendering must not do it, because then drawing the
	same model at a different size would silently move the model -- a hidden
	state transition inside something documented as observation.

	Computed for the ordinary ONE-ROW footer and the ordinary stacked body.
	The quit confirmation takes a second row, but it is a transient state the
	model does not need a resized viewport for."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return None
	body_lines = ordinary_body_lines(lines)
	top_lines, detail_lines = pane_heights(body_lines)
	# The PANE HEIGHT, not the row budget. How many rows are actually drawn
	# depends on whether the list overflows, and `list_capacity` is the one
	# place that decides it -- subtracting the indicator row here as well gave
	# the model a second, smaller height and hid a message at exact fit.
	layout = {"inbox_height": max(1, top_lines),
	          "detail_height": max(1, detail_lines)}
	if recipients:
		# Only when there is something to measure. Returning a capacity
		# computed from an EMPTY list would let any caller that omits the
		# recipients silently reset a correct capacity to 1 -- and
		# `set_viewport` treats an absent capacity as "leave it alone",
		# which is the safe reading of "I did not measure this".
		layout["picker_capacity"] = picker_capacity(recipients, participant,
		                                            columns, lines)
	return layout


def picker_capacity(recipients, participant, columns: int, lines: int) -> int:
	"""How many recipients this terminal can actually DRAW.

	Measured, not estimated. The previous version wrapped the prompt and then
	subtracted a fixed `1 + 2`, which assumes every entry and the pagination
	footer occupy exactly one row each. At 40 columns a real address wraps to
	two rows, so the picker offered letters `c`, `d`, `e` that were never
	drawn -- and then dropped the footer that would have said so. A shortcut
	you cannot see is worse than no shortcut: the keystroke still works, and
	it sends to whoever the invisible row named.

	So the entries are laid out for real and counted until the pane is full.
	The footer is reserved only when there will BE a footer, which is decided
	by this same count -- hence the second pass.

	Measured against the MODAL body, because that is what the picker occupies:
	the full terminal width, and every body row under the header. A 60% detail
	pane cannot draw a prompt, one recipient and a page footer at the minimum
	terminal, so leaving the picker inside it would have offered a letter it
	could not draw -- the exact fault this measurement exists to prevent."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return 1
	width = columns
	body_lines = ordinary_body_lines(lines)
	addresses = [entry["address"] for entry in recipients]
	head = len(_wrapped(PICKER_PROMPT, width))
	# Worst case page numbering, so the reserve cannot be short on the last
	# page: every page shows the same total, and the widest page number is
	# the total itself.
	footer = len(_picker_footer_lines(max(1, len(addresses)),
	                                  max(1, len(addresses)), width))

	def fits(budget: int) -> int:
		used, count = 0, 0
		for index, address in enumerate(addresses):
			rows = len(_picker_entry_lines(PICKER_LABELS[index % len(PICKER_LABELS)],
			                               address, participant, width))
			if used + rows > budget:
				break
			used += rows
			count += 1
		return count

	room = body_lines - head
	# One page, no footer needed?
	if room > 0 and fits(room) >= len(addresses):
		return max(1, len(addresses))
	# Otherwise the footer is real and has to be paid for.
	count = fits(max(0, room - footer))
	# A pane too small for even one entry still must not offer letters it
	# cannot draw; `picker_entries` is clamped by what `_picker_lines` draws,
	# so returning 1 here is honest only because that clamp exists.
	return max(1, count)


# Style names a driver may act on. Deliberately abstract: the renderer says
# "this row is selected", the driver decides that means reverse video. Keeping
# curses attributes out of here is what lets the whole screen be asserted as
# data.
STYLE_SELECTED = "selected"
STYLE_PART_HEADER = "part-header"

# Marker for the selected part header. Deliberately NOT the inbox `>`: the two
# selections mean different things -- which message Enter opens, and which part
# `m` writes out -- and a human who cannot tell them apart has two cursors that
# look like one.
PART_MARKER = "\u25b8"
PART_MARKER_ASCII = ">>"

# Marker for a reply, drawn at the head of an indented child row. U+21AA
# RIGHTWARDS ARROW WITH HOOK is the conventional "in reply to" glyph; `->` is
# the fallback for a terminal that cannot encode it.
THREAD_MARKER = "\u21aa"
THREAD_MARKER_ASCII = "->"
# Marker for a reply DEEPER than the visible bound: the same arrow behind an
# ellipsis, saying that ancestry above it is visually compressed.
DEEP_THREAD_MARKER = "\u2026\u21aa"
DEEP_THREAD_MARKER_ASCII = "...->"
# Cells of indent per level of reply. Two: deep enough to read as a step, small
# enough that a nested thread does not eat the subject column.
THREAD_INDENT = 2
# Reply depths drawn explicitly. Slawomir's ruling: three. Past it every row is
# still shown, in its true position and order -- only the INDENT is clamped,
# and the marker changes so three levels and nine do not look identical.
MAX_THREAD_DEPTH = 3


def markers_for(encoding: str | None) -> dict:
	"""Every optional glyph, decided ONCE for this terminal.

	One decision, not three: a terminal that cannot encode the reply arrow
	cannot encode the check mark either, and deciding them separately is how a
	screen ends up with a Unicode arrow beside an ASCII ellipsis. Same
	reasoning as the divider -- a replacement glyph is worse than plain ASCII,
	and each of these carries meaning rather than decoration.

	Fallback changes PRESENTATION only. Every one of these is three display
	cells or fewer in both spellings, so no column moves with the choice.

	`status` maps the status-column glyphs to their fallback spelling, or is
	empty when the terminal can draw them. `Q`/`P` live in here and NOT in the
	normal presentation: the ruled UTF-8 marks are `▷`/`▶`, and the letters
	are what a terminal falls back to."""
	try:
		(DEEP_THREAD_MARKER + NOTICE_SEEN_MARK
		 + UNOPENED + OPENED + QUEUED + PICKED_UP + COMPLETED).encode(encoding or "ascii")
	except (LookupError, UnicodeEncodeError):
		return {"thread": THREAD_MARKER_ASCII, "deep": DEEP_THREAD_MARKER_ASCII,
		        "notice_seen": NOTICE_SEEN_MARK_ASCII, "status": dict(ASCII_GLYPHS)}
	return {"thread": THREAD_MARKER, "deep": DEEP_THREAD_MARKER,
	        "notice_seen": NOTICE_SEEN_MARK, "status": {}}


def thread_prefix(depth: int, marker: str = THREAD_MARKER,
                  deep: str = DEEP_THREAD_MARKER) -> str:
	"""What precedes a reply's subject at this depth, indent included.

	THE one place the bound lives. Depth is clamped for DISPLAY only: the row
	keeps its true position, order, badge, direction and actionability, and
	`responds_to` is untouched. Only how far right it starts is bounded, and
	past the bound the marker says so rather than letting three levels and
	nine look identical.

	Unbounded, a long thread pushes the subject off the right of the pane --
	which loses the message to preserve the shape of the conversation."""
	if depth <= 0:
		return ""
	shown = min(depth, MAX_THREAD_DEPTH)
	glyph = deep if depth > MAX_THREAD_DEPTH else marker
	return f"{' ' * (THREAD_INDENT * shown)}{glyph} "


def part_marker_for(encoding: str | None) -> str:
	"""U+25B8 where the terminal can encode it, `>>` where it cannot. Same
	reasoning as the divider: a replacement glyph is worse than plain ASCII."""
	try:
		PART_MARKER.encode(encoding or "ascii")
	except (LookupError, UnicodeEncodeError):
		return PART_MARKER_ASCII
	return PART_MARKER


def selection_span(columns: int) -> tuple[int, int]:
	"""Screen columns the selection highlight covers: `[start, end)`.

	The WHOLE ROW, because a stacked list row IS the whole row. The property
	the column layout needed this helper to enforce is unchanged and is now
	about rows rather than cells: the stripe covers exactly ONE ROW of ONE
	LIST. It never reaches the divider rule below it, and never the detail
	pane under that."""
	return (0, max(0, columns))


def render_styled(state, columns: int = 100, lines: int = 24, *,
                  divider: str = DIVIDER,
                  marker: str = PART_MARKER,
                  thread: str = THREAD_MARKER,
                  deep: str = DEEP_THREAD_MARKER,
                  notice_seen: str = NOTICE_SEEN_MARK,
                  status: dict | None = None) -> list[tuple[str, frozenset]]:
	"""The screen as `(text, style)` pairs.

	The selected inbox row carries `selected` so the driver can give it a
	full-row terminal attribute. A `>` marker alone proved far too subtle to
	find on a real terminal -- the human could not see which row they were on,
	while Enter would still have claimed it."""
	text_rows = render(state, columns, lines, divider=divider, marker=marker,
	                   thread=thread, deep=deep, notice_seen=notice_seen, status=status)
	selected_row = _selected_screen_row(state, columns, lines)
	header_rows = _part_header_screen_rows(state, columns, lines, marker=marker)
	out = []
	for index, text in enumerate(text_rows):
		style = set()
		if index == selected_row:
			style.add(STYLE_SELECTED)
		if index in header_rows:
			style.add(STYLE_PART_HEADER)
		out.append((text, frozenset(style)))
	return out


def _part_header_screen_rows(state, columns: int, lines: int, *,
                             marker: str = PART_MARKER) -> set:
	"""SCREEN rows carrying the selected part's header, after scrolling.

	Empty when the header has scrolled out of the pane -- a mark on a row that
	is no longer the header would point at whatever content took its place."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return set()
	_, height = _pane_geometry(state, lines)
	marks: list[int] = []
	produced = _detail_lines(state, columns, marker=marker, marks=marks)
	if not marks:
		return set()
	offset = max(0, min(state.detail_offset, max(0, len(produced) - height)))
	base = _detail_screen_top(state, lines)
	visible = set()
	for index in marks:
		row = index - offset
		if 0 <= row < height:
			# The last visible row may have been replaced by the "N more
			# lines" indicator, which is not a header.
			if len(produced) > offset + height and row == height - 1:
				continue
			visible.add(base + row)
	return visible


# Rows the ordinary footer occupies: ONE status line. Named so the model
# geometry, the picker measurement and the renderer cannot disagree about it,
# which is exactly what happened when the two-row footer became one and only
# the renderer was told.
ORDINARY_FOOTER_ROWS = 1


def ordinary_body_lines(lines: int) -> int:
	"""Rows between the header and the ordinary footer, divider included.

	The single arithmetic. `layout_for` sizes the model's viewport with it,
	`picker_capacity` measures the modal body with it, and `_body_lines` draws
	with it -- one row reclaimed from the footer has to reach all three or the
	model is smaller than the screen and the bottom row of the pane is never
	navigable."""
	return lines - 1 - ORDINARY_FOOTER_ROWS


def _footer_height(state) -> int:
	"""Rows the footer occupies. ONE for browse, reply, compose, notice, the
	picker, help and the send confirmation; TWO only for the unresolved-quit
	confirmation.

	It was two everywhere -- a shortcut catalogue above a status line.
	Slawomir ruled the ordinary key legend off the screen entirely: `?` help
	and the README own shortcuts, and the bottom row is for what the console
	DID. The reclaimed row goes to the panes.

	The quit confirmation is the one shape that still needs two, because the
	question and the reason it is being asked are different facts and the
	human is about to abandon claims. It is transient, which is why the model
	viewport and the picker measurement are sized for the ordinary one.

	Read by everything that divides the screen up, because a footer that
	changes height while the body arithmetic does not is how a row goes
	missing or gets drawn twice."""
	return 2 if state.mode == MODE_CONFIRM_QUIT else ORDINARY_FOOTER_ROWS


def _body_lines(state, lines: int) -> int:
	"""Rows between the header and the footer, divider row included."""
	return lines - 1 - _footer_height(state)


HELP_TITLE = "SHORTCUTS — ? q Esc closes; j/k scrolls"


def help_lines(state, width: int) -> list[str]:
	"""The whole shortcut map as text, from `keys.HELP_SECTIONS`.

	Built from the table beside the key map so the two cannot drift. A help
	screen maintained separately is wrong within a month, and wrong help is
	worse than none because it is believed."""
	from . import keys as K
	out = _wrapped(HELP_TITLE, width)
	for title, entries in K.HELP_SECTIONS:
		out.append("")
		out.extend(_wrapped(title, width))
		for chord, description, _ in entries:
			out.extend(_wrapped(f"{chord:<20}{description}", width, "    "))
	return out


def _help_pane(state, width: int, height: int) -> list[str]:
	"""The scrolled window onto the help. It PAGES rather than clipping: a
	shortcut the terminal was too small to draw would be a shortcut that does
	not exist, which is the fault the recipient picker taught."""
	produced = help_lines(state, width)
	offset = max(0, min(state.help_offset, max(0, len(produced) - height)))
	window = [_cell(line, width) for line in produced[offset:offset + height]]
	if len(produced) > offset + height and window:
		window[-1] = _cell(f"  ... {len(produced) - offset - height} more "
		                   f"(j/k scrolls)", width)
	while len(window) < height:
		window.append("")
	return window[:height]


def help_line_count(state, columns: int, lines: int) -> int:
	"""How many lines the help occupies at this width, for scroll clamping."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return 0
	return len(help_lines(state, columns))


def _pane_geometry(state, lines: int) -> tuple[int, int]:
	"""(list rows, detail rows) for THIS state at this height.

	The recipient picker is MODAL and owns the whole body. Two reasons, and
	the second is the load-bearing one: a human choosing a recipient is not
	reading the list behind the choice, and at the minimum terminal a 60%
	detail pane cannot draw the prompt, one recipient and the page footer --
	so a picker confined to it would offer a letter it could not draw, which
	is precisely the fault the measured capacity exists to prevent."""
	body = _body_lines(state, lines)
	if state.mode in (MODE_PICK_RECIPIENT, MODE_HELP):
		return 0, body
	return pane_heights(body)


def _detail_screen_top(state, lines: int) -> int:
	"""The first SCREEN row of the detail pane: past the header, the list and
	the divider rule -- or past the header alone while the picker is modal."""
	top_lines, _ = _pane_geometry(state, lines)
	modal = state.mode in (MODE_PICK_RECIPIENT, MODE_HELP)
	return 1 + top_lines + (0 if modal else 1)


def _selected_screen_row(state, columns: int, lines: int) -> int | None:
	"""Which SCREEN line holds the selected list row, or None when the
	terminal is unusable, the queue is empty, or no list is drawn."""
	# The ACTIVE view. This read `state.rows`/`inbox_top`/`cursor` while the
	# pane drew `sent_rows`/`sent_top`/`sent_cursor`, so in SENT the stripe
	# landed on the wrong row -- or on none at all when the inbox was empty
	# and the sent list was not.
	rows = state.view_rows
	if columns < MIN_COLUMNS or lines < MIN_LINES or not rows:
		return None
	top_lines, _ = _pane_geometry(state, lines)
	if top_lines <= 0:
		return None                      # modal chooser: no list on screen
	usable = list_capacity(len(rows), top_lines)
	top = list_top(len(rows), top_lines, state.view_top)
	offset = state.view_cursor - top
	if offset < 0 or offset >= usable:
		return None                      # scrolled out of the pane
	return 1 + offset                    # 1 = past the header


def render(state, columns: int = 100, lines: int = 24, *,
           divider: str = DIVIDER, marker: str = PART_MARKER,
           thread: str = THREAD_MARKER,
           deep: str = DEEP_THREAD_MARKER,
           notice_seen: str = NOTICE_SEEN_MARK,
           status: dict | None = None) -> list[str]:
	"""The whole screen as EXACTLY `lines` strings, each at most `columns`
	display cells wide.

	OBSERVATION ONLY: this never mutates the model. Scroll positions and pane
	heights are read from the state; the driver sets them through the public
	`set_viewport` on start and resize.

	The requested size is the ACTUAL terminal size and is never clamped
	upward. A curses blit writes what it is given, so returning 40 columns for
	a 20-column terminal would write out of bounds -- which happens during
	startup and on every drag-resize, not only in contrived cases. Below the
	two-pane minimum we render a clipped notice instead, still within the real
	dimensions."""
	columns = max(0, columns)
	lines = max(0, lines)
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return _too_small(columns, lines)

	body_lines = _body_lines(state, lines)
	out = [_header(state, columns)]
	if state.mode == MODE_HELP:
		# A modal VIEW over the whole body, with its own scroll. The ordinary
		# one-line status bar stays exactly as it was: help is a screen, not
		# status-bar prose, and the bar is where async events land.
		out.extend(_help_pane(state, columns, body_lines))
	elif state.mode == MODE_PICK_RECIPIENT:
		# Modal: the chooser owns the body. There is no list behind it to
		# separate from, so no rule is drawn.
		out.extend(_detail_pane(state, columns, body_lines, marker=marker))
	else:
		top_lines, detail_lines = _pane_geometry(state, lines)
		out.extend(_inbox_pane(state, columns, top_lines, thread=thread,
		                       deep=deep, notice_seen=notice_seen,
		                       status=status))
		# The rule carries the focus mark and the IDENTITY, not a label. The
		# lower pane is self-evidently the selected message; naming it spent a
		# word saying so. The participant is genuinely useful and genuinely
		# secondary, which is what the right-hand end of a rule is for.
		out.append(_detail_rule(state, columns, divider))
		out.extend(_detail_pane(state, columns, detail_lines, marker=marker))
	out.extend(_footer(state, columns))
	return [line.rstrip() for line in out[:lines]]


def _too_small(columns: int, lines: int) -> list[str]:
	"""Clipped to the real dimensions, including 0 and 1."""
	message = [f"terminal too small", f"need {MIN_COLUMNS}x{MIN_LINES}"]
	out = [_cell(text, columns) for text in message[:lines]]
	while len(out) < lines:
		out.append("")
	return out[:lines]


def detail_overflow(state, columns: int = 100, lines: int = 24) -> int:
	"""Display cells the widest rendered detail line runs past the pane.

	Zero when nothing overflows, which is what decides whether sideways
	movement is offered at all -- the same availability fact the footer and
	dispatch read."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return 0
	pannable: list[int] = []
	produced = _detail_lines(state, columns, pannable=pannable)
	# From the CONTENT lines only: chrome never pans, so a long header must
	# not offer sideways movement that would do nothing to it.
	widest = max((display_width(produced[index]) for index in pannable
	              if index < len(produced)), default=0)
	return max(0, widest - columns)


def detail_line_count(state, columns: int = 100, lines: int = 24) -> int:
	"""How many lines the detail pane WOULD produce at this width. The driver
	needs it to clamp scrolling, and only the renderer knows how content laid
	out at the current width."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return 0
	return len(_detail_lines(state, columns))


# Focus marker. ASCII and WIDTH-STABLE: `> ` and two spaces occupy the same
# two cells, so toggling focus cannot move anything on the row. Both labels are
# always drawn and exactly one carries the marker -- an indication that exists
# only as bold or colour is no indication on half the terminals this runs on.
FOCUS_MARK = "> "
FOCUS_BLANK = "  "


# Cells of rule that must remain to the LEFT of the identity for it to read as
# right-aligned against something rather than as a stray word near the edge.
MIN_RULE_CELLS = 8


def _detail_rule(state, columns: int, divider: str) -> str:
	"""The rule between the panes: focus mark, fill, then the identity.

	This row IS the lower pane's header, which is why the `DETAIL` label lived
	here and why the identity replaces it. The identity is not on the status
	line: an empty status is pinned to be a BLANK row, and a decoration
	printed there would quietly end that.

	One row, full width, unbroken between the mark and the identity -- R7's
	edge-to-edge property, measured the same way it always was.

	DECORATIVE, and it degrades first. On a terminal too narrow to hold it
	with a clear run of rule to its left, the rule simply goes to the edge:
	losing the participant name costs the human something they can get from
	`?` or their own shell, while letting it crowd or truncate costs them a
	name that is WRONG rather than absent.
	"""
	mark = focus_mark(state, FOCUS_DETAIL)
	# The row ends in RULE, not in the identity, and that last cell is not
	# decoration.
	#
	# A real terminal does not reliably draw the rightmost cell of a
	# full-width row -- writing it can wrap the cursor, so curses declines.
	# With the identity flush right that cost its last character, and a
	# packaged run drew `acme.implemente`: a participant address that does not
	# exist. Absent is fine; wrong is not, and a name one letter short is
	# wrong in the way that sends someone looking for the wrong mailbox.
	# Ending with rule means the cell the terminal may drop is one nobody
	# reads.
	#
	# No trailing SPACE for the same job: `render` rstrips every row, so a
	# blank there is not drawn and the rule comes up short of the edge --
	# which several tests measure, correctly, in display cells.
	identity = f" {state.participant}"
	fill = max(0, columns - display_width(mark))
	lead = fill - display_width(identity) - 1
	if lead >= MIN_RULE_CELLS:
		return _cell(mark + divider * lead + identity + divider, columns)
	return _cell(mark + divider * fill, columns)


def focus_mark(state, pane: str) -> str:
	return FOCUS_MARK if state.focus == pane else FOCUS_BLANK


def _fresh_composition(state) -> bool:
	"""A compose or notice that is NOT answering anything.

	`state.mode == MODE_COMPOSE` alone is not the question: a follow-up is
	also a composition, and it must keep the message it refers to on screen.
	The explicit reply context is what separates them, and while the send is
	armed the mode being confirmed is what counts."""
	mode = (getattr(state, "send_return_mode", None) or MODE_COMPOSE) \
		if state.mode == MODE_CONFIRM_SEND else state.mode
	if mode not in (MODE_COMPOSE, MODE_NOTICE):
		return False
	return not (getattr(state, "compose_is_reply", False)
	            or getattr(state, "follow_up_to", None))


def _header(state, columns: int) -> str:
	owed = state.unresolved_count()
	warning = f"  ⚠ {_cell(state.warning, columns // 3)}" if state.warning else ""
	mark = focus_mark(state, FOCUS_LIST)
	# THE COUNT IS THE INFORMATION. The product name, the participant, an
	# all-caps pane label and a pair of brackets used to compete with it on
	# this one line; none of them told the human anything the screen did not
	# already say. Identity moved to the lower rule, where it is available
	# without being in the way.
	#
	# Which view you are in stays, and stays first. The two lists look alike
	# at a glance and acting on the wrong one is the class of mistake this
	# console exists to prevent -- SENT cannot act on anything, but believing
	# you are in it while in MESSAGES very much can.
	#
	# The focus mark stays too. It is one leading cell, it is what the
	# navigation keys follow, and the ruling permits a subtle marker; what it
	# forbids is the label coming back.
	if state.view == VIEW_SENT:
		return _cell(f"{mark}Sent: {len(state.sent_rows)} sent, newest first "
		             f"— read only, i for messages{warning}", columns)
	return _cell(f"{mark}Messages: {len(state.rows)} retained, {owed} awaiting "
	             f"your reply/close{warning}", columns)


def _compact_date(created_ts) -> str:
	"""`2026-08-08T04:01:27Z` -> `08-08 04:01`, always UTC.

	UTC deliberately: the protocol stores UTC, agents in different places read
	the same inbox, and a local-time column would make two people describing
	"the 04:01 message" mean different rows."""
	if not created_ts or len(str(created_ts)) < 17:
		return ""
	text = str(created_ts)
	return f"{text[5:10]} {text[11:16]}"


# Compact state badges for the SENT view. Text, not colour, for the same
# reason the severity markers are: a badge that only exists as colour is
# invisible over SSH on a terminal without it.
# The lifecycle states an outbound row can be in. `pending`, `claimed`,
# `completed` and `closed` are NOT here: those are the four the human-facing
# vocabulary covers, and `_status_glyph` answers them for both views. What
# remains are the states that ARE their own answer -- an expiry or a
# quarantine is not a step in anyone's obligation.
SENT_BADGES = {
	"expired": "E",
	"quarantined": "X",
}
NOTICE_BADGE = "N"
# The glossary is REFERENCE, not message content, so it no longer appears in
# the detail pane on every selected row. `?` help and the README own it.
SENT_LEGEND = ("• unopened  ○ opened, owed  ▷ queued  ▶ picked up  "
               "✓ done  E expired  X quarantined  N notice  ! unseen notice")


def exceptional_badge(row: dict) -> str:
	"""The EXCEPTIONAL states only -- expiry, quarantine, and the authored
	notice. RENAMED from `sent_badge`, deliberately: while it was named for a
	view it kept being reached for as that view's status machine, and a second
	status machine is how MESSAGES and SENT came to disagree about one row.
	Everything a human has an obligation about goes through `_status_glyph`.

	What happened to one outbound row.

	A notice gets its OWN badge rather than borrowing a directed state. It has
	no claim, so `pending` and `claimed` would both be lies -- what it has is
	receipts and a lifetime, and those are shown beside it instead."""
	if row.get("row_kind") == "notice":
		return NOTICE_BADGE
	return SENT_BADGES.get(row.get("state"), "?")


# Column degradation thresholds for the list pane, re-derived for the STACKED
# layout: the pane is now the WHOLE terminal width, so the old width-of-a-40%-
# column numbers would have made the date unconditional and left the
# degradation path dead. Widest column goes first; the subject is last to give
# up space, because a list that hides the subject is useless and one that hides
# the date is not.
DATE_COLUMN_WIDTH = 60
WIDE_PARTY_WIDTH = 90

# Cells the status column occupies, whichever notation a row uses. Every
# glyph is now ONE cell -- `Q`, `*`, `✓`, `S`, blank -- and the column is
# padded to that width so the columns after it cannot move between rows.
GLYPH_WIDTH = 1


def _party_width(width: int) -> int:
	"""Cells for the other party's address, per available width."""
	if width >= WIDE_PARTY_WIDTH:
		return 18
	return 12 if width >= DATE_COLUMN_WIDTH else 10


def sent_status_glyph(row, notice_seen: str = NOTICE_SEEN_MARK,
                      status: dict | None = None) -> str:
	"""The status glyph for an OUTBOUND row, list or detail.

	`list_sent` rows are shaped differently from inbox rows -- `row_kind`, and
	no `direction`, because everything here is outbound by definition -- so
	they are normalised HERE and the shared glyph function is asked. One
	place, because the list and the detail heading drifting apart is exactly
	what happened: the list was unified, the heading kept calling the old
	badge table, and when the normal states left that table the heading
	started drawing `?` for every ordinary message."""
	if row.get("row_kind") == "notice":
		# An AUTHORED notice keeps `N`. It is not a receipt state: `!`/`✓` say
		# whether I have seen someone else's broadcast, and neither is a fact
		# about one I published.
		glyph = NOTICE_BADGE
	else:
		glyph = _status_glyph({**row, "row_type": ROW_MESSAGE,
		                       "direction": "out"}, notice_seen)
	return (status or {}).get(glyph, glyph)


def _sent_pane(state, width: int, height: int, *,
               notice_seen: str = NOTICE_SEEN_MARK,
               status: dict | None = None) -> list[str]:
	"""The Sent FILTER: outbound traffic, newest first, read-only."""
	rows = []
	source = state.view_rows
	usable = list_capacity(len(source), height)
	overflow = usable < height
	top = list_top(len(source), height, state.view_top)
	visible = source[top:top + usable]
	show_date = width >= DATE_COLUMN_WIDTH
	date_width = 12 if show_date else 0
	for offset, row in enumerate(visible):
		index = top + offset
		marker = ">" if index == state.view_cursor else " "
		# The SAME function the messages pane uses. Two views showing the same
		# row must not disagree about it, and while SENT had its own table
		# they did: an answered message read `✓` in one and `R` in the other.
		#
		# `list_sent` rows are shaped differently -- `row_kind`, and no
		# `direction`, because everything here is outbound by definition. So
		# they are NORMALISED at the boundary rather than teaching the glyph
		# function a second row shape.
		badge = f"{sent_status_glyph(row, notice_seen, status):<{GLYPH_WIDTH}}"
		date = f"{_compact_date(row.get('created_ts')):<11} " if show_date else ""
		if row.get("row_kind") == "notice":
			# Receipts, not a claim state: what a broadcast can actually
			# report about how it landed.
			target = f"all ({row.get('seen_count', 0)} seen)"
		else:
			target = row.get("to_participant") or ""
		target_width = _party_width(width)
		subject = row.get("subject") or f"({row.get('kind') or 'no subject'})"
		remaining = max(4, width - GLYPH_WIDTH - 2 - target_width - date_width)
		text = (f"{marker}{badge} {date}{_cell(target, target_width):<{target_width}} "
		        f"{_cell(subject, remaining)}")
		rows.append(_cell(text, width))
	remaining = len(source) - top - usable
	if overflow:
		rows.append(_cell(f"  ... {remaining} more" if remaining > 0
		                  else f"  ... {top} above", width))
	while len(rows) < height:
		rows.append("")
	return rows


def _inbox_pane(state, width: int, height: int, *,
                thread: str = THREAD_MARKER,
                deep: str = DEEP_THREAD_MARKER,
                notice_seen: str = NOTICE_SEEN_MARK,
                status: dict | None = None) -> list[str]:
	"""The visible slice, following the model's viewport so the selected row
	cannot scroll out of sight."""
	if state.view == VIEW_SENT:
		# The SAME top pane, not a split: one list at a time, at the full
		# terminal width and the full 40% of the body. Splitting it between
		# two lists would halve the rows each gets to save one keystroke.
		return _sent_pane(state, width, height, notice_seen=notice_seen,
		                  status=status)
	rows = []
	usable = list_capacity(len(state.rows), height)
	overflow = usable < height
	top = list_top(len(state.rows), height, state.inbox_top)
	visible = state.rows[top:top + usable]
	# Columns are dropped deliberately as width shrinks, widest first, so a
	# narrow terminal loses the date rather than the subject. Thresholds live
	# in `_party_width`/`DATE_COLUMN_WIDTH` and are shared with the sent pane,
	# so the two lists cannot degrade at different sizes.
	show_date = width >= DATE_COLUMN_WIDTH
	date_width = 12 if show_date else 0
	sender_width = _party_width(width)
	for offset, row in enumerate(visible):
		index = top + offset
		marker = ">" if index == state.cursor else " "
		# ONE function for every row, inbound and outbound alike. It reads
		# direction off the row itself, so a completed inbound and a completed
		# outbound cannot end up with different glyphs -- which is exactly
		# what happened while outbound had its own branch here: it reported
		# the store's word (`R`) for the same fact the inbound side called
		# `✓`. Direction still decides the LIVE states, `▷`/`▶` against
		# `•`/`○`, because there the human does need to know whose move it is.
		glyph = _status_glyph(row, notice_seen)
		glyph = (status or {}).get(glyph, glyph)
		# One column width for both notations. A 1-cell glyph beside a 3-cell
		# badge shifted the date and sender two cells on alternating rows,
		# which after this change is most of the list rather than the rare
		# terminal row it used to be.
		glyph = f"{glyph:<{GLYPH_WIDTH}}"
		date = f"{_compact_date(row.get('created_ts')):<11} " if show_date else ""
		# WHO THE OTHER PARTY IS, with the direction stated. `to x` and a bare
		# name read very differently at a glance, which is the point: work I
		# owe must not look like work I delegated.
		if row.get("direction") == "out":
			sender = _cell(f"to {row.get('to_participant') or ''}", sender_width)
		else:
			sender = _cell(row.get("from_participant"), sender_width)
		subject = row.get("subject") or f"({row.get('kind') or 'no subject'})"
		# A REPLY is an indented child of what it answers, marked so the
		# relationship is visible rather than inferred from adjacency. The
		# indent goes in the SUBJECT column and nowhere else: indenting the
		# whole row would move the date and sender on reply rows only, and
		# every list row lining up is a property pinned one round ago.
		depth = int(row.get("depth") or 0)
		subject = thread_prefix(depth, thread, deep) + subject
		remaining = max(4, width - GLYPH_WIDTH - 2 - sender_width - date_width)
		text = (f"{marker}{glyph} {date}{sender:<{sender_width}} "
		        f"{_cell(subject, remaining)}")
		rows.append(_cell(text, width))
	remaining = len(state.rows) - top - usable
	if overflow:
		# Appended on its OWN line, never over a real row.
		rows.append(_cell(f"  ... {remaining} more" if remaining > 0
		                  else f"  ... {top} above", width))
	while len(rows) < height:
		rows.append("")
	return rows


def _detail_pane(state, width: int, height: int, *,
                 marker: str = PART_MARKER) -> list[str]:
	"""The scrolled window onto the detail lines, so long content is readable
	rather than silently truncated at the pane boundary."""
	pannable: list[int] = []
	produced = _detail_lines(state, width, marker=marker, pannable=pannable)
	movable = set(pannable)
	offset = max(0, min(state.detail_offset, max(0, len(produced) - height)))
	# CONTENT pans; chrome does not. Metadata, part headers and container
	# labels stay put, so the human keeps track of which message they are in
	# and which part they are on while a long line moves underneath.
	window = [_hwindow(line, width, state.detail_hscroll)
	          if index in movable else _cell(line, width)
	          for index, line in enumerate(produced[offset:offset + height],
	                                       start=offset)]
	if len(produced) > offset + height and window:
		window[-1] = _cell(f"  ... {len(produced) - offset - height} more lines", width)
	while len(window) < height:
		window.append("")
	return window[:height]


def _detail_lines(state, width: int, *, marker: str = PART_MARKER,
                  marks=None, pannable=None,
                  notice_seen: str = NOTICE_SEEN_MARK,
                  status: dict | None = None) -> list[str]:
	"""The detail pane's lines. `marks`, when given, is filled with the
	indices of the selected part's header rows -- reported by the code that
	drew them, never rediscovered by searching the text."""
	if state.mode == MODE_PICK_ROOT:
		# Same reasoning as the recipient picker below: the chooser REPLACES
		# the pane, so `marks` is never filled from content that is not on
		# screen.
		return _root_picker_lines(state, width)
	if state.mode == MODE_PICK_RECIPIENT:
		# The picker REPLACES everything below the header: the human is
		# choosing a recipient, and message content behind the choice is noise.
		# Checked FIRST so `marks` is never filled from content that is not on
		# screen -- the part-header styling would otherwise mark whichever
		# picker row happened to land on that index.
		return _picker_lines(state, width)
	out: list[str] = []
	detail = state.detail
	chosen = state.selected_part
	selected = chosen.get("address") if chosen else None
	if _fresh_composition(state):
		# A genuinely fresh compose OWNS this pane. The selected row behind it
		# is unrelated, and drawing its preview under a new message put an
		# action prompt for a row the human cannot act on right now above the
		# form they are typing in. A REPLY or follow-up is the opposite case:
		# the original is the thing being answered, so it stays.
		detail = None
	if detail is None:
		out.extend(_wrapped("(nothing selected)", width))
	elif "preview" in detail:
		out.extend(_preview_lines(detail["preview"], width))
	elif "delivery" in detail:
		out.extend(_delivery_lines(detail["delivery"], width, selected=selected,
		                           marker=marker, marks=marks,
		                           external=getattr(state, "external_text", None),
		                           pannable=pannable))
	elif "notice" in detail:
		out.extend(_notice_lines(detail["notice"], width, selected=selected,
		                         marker=marker, marks=marks,
		                         pannable=pannable))
	elif "sent_row" in detail:
		out.extend(_sent_row_lines(detail["sent_row"], width,
		                           notice_seen=notice_seen, status=status))
	elif "received" in detail:
		out.extend(_sent_content_lines(detail["received"], width,
		                               selected=selected, marker=marker,
		                               marks=marks, heading=FOLLOW_UP_ANSWERED,
		                               pannable=pannable))
	elif "sent" in detail:
		out.extend(_sent_content_lines(detail["sent"], width, selected=selected,
		                               marker=marker, marks=marks,
		                               pannable=pannable))
	elif "sent_notice" in detail:
		out.extend(_sent_content_lines(detail["sent_notice"], width,
		                               selected=selected, marker=marker,
		                               marks=marks, notice=True,
		                               pannable=pannable))

	# While the send is armed, keep drawing the draft exactly as it was. The
	# whole point of confirming is that the human can READ what they are about
	# to publish; a confirmation over a blank pane asks them to approve
	# something they can no longer see.
	mode = (getattr(state, "send_return_mode", None) or MODE_COMPOSE) \
		if state.mode == MODE_CONFIRM_SEND else state.mode
	# NO tutorial prose in either shape. The keys are on the footer while they
	# work and in `?` help and the README for good; a sentence teaching them
	# in the middle of the work area is read once and then in the way forever.
	# Slawomir's ruling: screen density is for messages and work.
	if mode == MODE_REPLY:
		out.append("")
		out.extend(_wrapped_lossless(state.draft, width, "  > "))
		out.extend(_body_summary(getattr(state, "reply_body", ""), width))
	elif mode in (MODE_COMPOSE, MODE_NOTICE):
		out.append("")
		if mode == MODE_COMPOSE:
			# Chosen from the registry, shown but not editable -- there is no
			# keystroke path back to a typed address.
			out.extend(_wrapped_lossless(state.compose.get("to", ""), width, "    to:      "))
		for index, field in enumerate(state.compose_fields):
			marker = ">" if index == state.compose_field else " "
			value = state.compose.get(field, "")
			if field == "attach_path":
				# ROOT and PATH on separate rows, never collapsed into
				# `root:path`. The locator is a serialization the human is not
				# asked to learn, and showing it here would teach it back to
				# them. The root row is not editable -- it is chosen -- so it
				# carries no field marker.
				root = state.compose.get("attach_root", "")
				out.extend(_wrapped_lossless(root, width, "    root:    "))
				out.extend(_wrapped_lossless(value, width, f"  {marker} path:    "))
				continue
			out.extend(_wrapped_lossless(f"{field + ':':<9}{value}", width, f"  {marker} "))
		# The body is not an editable field: it is written externally or not
		# at all. Showing its STATE keeps that honest -- an empty line where a
		# body used to be typed would just look broken.
		out.extend(_body_summary(state.compose.get("body", ""), width))
	return out


# Short on purpose: the prompt is overhead that competes with the entries for
# rows, and at 40x8 a wrapping prompt left no room to draw even one recipient.
# The full hint lives in the status bar, which is always present anyway.
PICKER_PROMPT = "send to:"

# The literal confirmation footer. One row, exactly this text, clipped only by
# a narrow terminal.
CONFIRM_SEND_FOOTER = ("Send now? [Y/n]   Enter or y = send   "
                       "n or Esc = keep editing")


def _picker_entry_lines(label: str, address: str, participant, width: int) -> list[str]:
	"""One offered recipient. Shared with `picker_capacity`, which counts
	these rows -- a second copy of this layout is how the picker came to
	offer letters it never drew."""
	mine = "   (you)" if address == participant else ""
	return _wrapped_lossless(f"{address}{mine}", width, f"  {label})  ")


def _picker_footer_lines(page: int, pages: int, width: int) -> list[str]:
	"""Where you are and how to move. Shown whenever there is more than one
	page, so a hidden recipient is never silently hidden."""
	return _wrapped(f"page {page}/{pages}  Tab=next", width)


ROOT_PROMPT = "attach from:"


def _root_picker_lines(state, width: int) -> list[str]:
	"""Every configured attachment root on this page, one letter each.

	The absolute base directory is shown BESIDE the name, because the choice
	is a security boundary: `src` means nothing on its own, and a human
	deciding where a file may come from has to see where that points."""
	out = _wrapped(ROOT_PROMPT, width)
	for label, entry in state.root_entries():
		out.extend(_wrapped(f"{label})  {entry['root_id']}", width, "  "))
		out.extend(_wrapped(entry.get("path", ""), width, "      "))
	if state.root_pages > 1:
		out.extend(_picker_footer_lines(state.picker_page + 1,
		                                state.root_pages, width))
	return out


def _picker_lines(state, width: int) -> list[str]:
	"""Every configured participant on this page, one letter each."""
	# No blank separators. They cost two rows, and at 40x8 those two rows are
	# the difference between drawing one recipient with its page footer and
	# drawing a letter the human can press but cannot read. Density is a
	# smaller loss than a shortcut that lies.
	out = _wrapped(PICKER_PROMPT, width)
	for label, entry in state.picker_entries():
		out.extend(_picker_entry_lines(label, entry["address"],
		                               state.participant, width))
	if state.picker_pages > 1:
		out.extend(_picker_footer_lines(state.picker_page + 1,
		                                state.picker_pages, width))
	return out


def _headers(item: dict, width: int) -> list[str]:
	out = []
	if item.get("responds_to"):
		# "In reference to", not "In reply to": the relation is broader than
		# the one claim-resolving reply -- later follow-ups use it too. The
		# WIRE field is still `responds_to`; this is prose, not a rename.
		out.extend(_wrapped(f"{IN_REFERENCE_TO:<9}{item['responds_to']}", width))
	for label, key in (("From", "from_participant"), ("Subject", "subject"),
	                   ("Kind", "kind"), ("Date", "created_ts"), ("State", "state")):
		if item.get(key) is not None:
			# Subjects run to 255 bytes; clipping one hides the end of the
			# thing the human is deciding about.
			out.extend(_wrapped(f"{label + ':':<9}{item[key]}", width))
	return out


def _part_lines(parts, width: int, indent: str = "  ") -> list[str]:
	"""Part structure, from metadata only. A preview shows what a message IS."""
	out = []
	for part in parts or []:
		size = "" if part.get("size") is None else f"  {part['size']}B"
		name = f"  {part['filename']}" if part.get("filename") else ""
		storage = "" if part.get("storage") in (None, "inline") else f"  [{part['storage']}]"
		out.extend(_wrapped(
			f"[{part['address']}] {part['content_type']}{storage}{size}{name}",
			width, indent))
		if part.get("parts"):
			out.extend(_part_lines(part["parts"], width, indent + "    "))
	return out


def _preview_lines(preview: dict, width: int) -> list[str]:
	"""What a message IS: metadata and part shape, and nothing else.

	The three `Enter: ...` prompts that used to end this pane are REMOVED by
	Slawomir's ruling. They named the irreversible thing correctly -- claim,
	mark seen, reopen -- but they were reference, repeated under every row the
	cursor touched, and after the first use they are only in the way. `?` help
	carries the lifecycle semantics in full, and the footer says what works
	now. The blank row that existed only to separate the prompt goes with it."""
	out = _headers(preview, width)
	out.append("")
	out.extend(_part_lines(preview.get("parts"), width))
	return out


def _delivery_lines(delivery: dict, width: int, *, selected=None,
                    marker: str = PART_MARKER, marks=None,
                    external: dict | None = None, pannable=None) -> list[str]:
	message = delivery.get("message", {})
	out = _headers(message, width)
	if delivery.get("damaged"):
		out.append("")
		out.extend(_wrapped(f"! content withheld: {delivery['damaged']}", width))
		out.extend(_wrapped(f"! {delivery.get('disposition_path', '')}", width))
		return out
	content = message.get("content") or {}
	out.append("")
	out.extend(_rendered_parts(content.get("parts"), width, selected=selected,
	                           marker=marker, marks=marks, base=len(out),
	                           external=external, pannable=pannable))
	return out


def _notice_lines(notice: dict, width: int, *, selected=None,
                  marker: str = PART_MARKER, marks=None,
                  pannable=None) -> list[str]:
	out = _headers(notice, width)
	if notice.get("already_seen"):
		out.append("")
		out.extend(_wrapped("(already seen — not redelivered)", width))
		out.extend(_part_lines(notice.get("parts"), width))
		return out
	out.append("")
	# The typed envelope when the caller built one, the raw rows otherwise.
	# Only the envelope carries `text`/`encoding`; reading `parts` off the raw
	# shape is what drew every notice as "(no retained bytes)".
	parts = ((notice.get("content") or {}).get("parts")
	         if notice.get("content") else notice.get("parts"))
	out.extend(_rendered_parts(parts, width, selected=selected,
	                           marker=marker, marks=marks, base=len(out),
	                           pannable=pannable))
	return out


def _part_header(part: dict) -> str:
	"""What a leaf IS: manifest address, declared media type, disposition and
	the part NAME.

	"Part name", not "filename", by Slawomir's ruling: a part is not a file,
	and the recipient decides what to do when materializing it. The name is a
	human label that becomes an input to filesystem naming only if someone
	saves the part -- so it is rendered directly, with no `filename:` label in
	front of it. (The wire field is still `filename` at protocol 9; renaming
	it is protocol-10 work.)

	It is a LABEL, never a path. `m` keeps writing to its own generated
	destination, because a sender-supplied name is sender-controlled input and
	a console that turned it into a path would be writing wherever the sender
	chose. Displaying it is safe only because every line through `_wrapped` is
	sanitized: a name carrying ESC or CR reaches the terminal as visible text,
	not as a control."""
	bits = [f"[{part.get('address', '')}] {part.get('content_type', '')}"]
	if part.get("disposition"):
		bits.append(str(part["disposition"]))
	if part.get("filename"):
		bits.append(str(part["filename"]))
	return "  ".join(bits)


_SENT_STATE_WORDS = {
	"pending": "queued — not picked up yet",
	"claimed": "picked up — being worked on",
	"completed": "resolved by a reply",
	"closed": "closed",
	"expired": "expired",
	"quarantined": "quarantined — content withheld",
}


def _sent_row_lines(row, width: int, *,
                    notice_seen: str = NOTICE_SEEN_MARK,
                    status: dict | None = None) -> list[str]:
	"""What `list_sent` already told us. No core call is made to draw this.

	The heading takes its glyph from the SAME function the list does. It used
	to call the old badge helper, which is how opening a normal sent message
	came to draw `?`: the badge table stopped answering the ordinary states
	when the list moved off it, and nothing here noticed."""
	if row is None:
		return _wrapped("(nothing sent)", width)
	glyph = sent_status_glyph(row, notice_seen, status)
	out = _wrapped(f"{glyph} {row.get('subject') or '(no subject)'}", width)
	out.append("")
	if row.get("row_kind") == "notice":
		out.extend(_wrapped("To:      everyone (notice)", width))
		out.extend(_wrapped(f"Seen by: {row.get('seen_count', 0)}", width))
		out.extend(_wrapped(f"Expires: {row.get('expires_ts') or 'unknown'}", width))
	else:
		out.extend(_wrapped(f"To:      {row.get('to_participant') or ''}", width))
		out.extend(_wrapped(
			f"State:   {_SENT_STATE_WORDS.get(row.get('state'), row.get('state') or '')}",
			width))
		if row.get("outcome"):
			out.extend(_wrapped(f"Outcome: {row['outcome']}", width))
	out.extend(_wrapped(f"Kind:    {row.get('kind') or ''}", width))
	out.extend(_wrapped(f"Sent:    {row.get('created_ts') or ''}", width))
	# The badge glossary and the "Enter opens your own copy, read only"
	# sentence that used to close this pane are REMOVED. The SENT header
	# already says read only, the footer says what works now, and the glossary
	# is reference material that belongs in `?` help and the README -- not
	# under every row the cursor lands on. SENT_LEGEND survives as the ONE
	# definition of the notation those two surfaces quote.
	return out


def _sent_content_lines(envelope, width: int, *, selected=None,
                        marker: str = None, marks=None,
                        notice: bool = False,
                        heading: str = FOLLOW_UP_SENT,
                        pannable=None) -> list[str]:
	"""An opened copy, outbound or received. Same rendering as a delivery.

	The heading is CONTEXT-SENSITIVE GUIDANCE rather than a label. It used to
	say "ALREADY ANSWERED — read only" and "YOUR SENT COPY — read only", which
	presented a conversation as a dead end: nothing is OWED here, but plenty
	can still be said. The body itself remains immutable and no disposition
	key is offered -- what changed is that the screen no longer implies the
	thread is over."""
	out = _wrapped(heading, width)
	out.append("")
	out.extend(_headers(envelope, width))
	out.append("")
	content = envelope.get("content") or {}
	out.extend(_rendered_parts(content.get("parts"), width, selected=selected,
	                           marker=marker or PART_MARKER, marks=marks,
	                           base=len(out), pannable=pannable))
	return out


def _note_pannable(pannable, base: int, produced: list, rows: list) -> None:
	"""Record which produced lines are CONTENT, and so may pan sideways.

	Metadata, part headers and container labels are CHROME: they stay fixed.
	Panning them off the left edge because one body line is long would make
	the pane unreadable in order to fix a line -- the human would lose which
	message they are looking at and which part they are on."""
	if pannable is not None:
		pannable.extend(range(base + len(produced), base + len(produced) + len(rows)))


def _rendered_parts(parts, width: int, indent: str = "  ", *,
                    selected: str | None = None, marker: str = PART_MARKER,
                    marks: list | None = None, base: int = 0,
                    external: dict | None = None,
                    pannable: list | None = None) -> list[str]:
	"""Opened content. Text parts are shown; binary and integrity metadata are
	summarized and hidden unless explicitly materialized.

	The selected leaf's HEADER rows -- never its content -- are marked, and
	their indices are recorded in `marks` if one is given. Recording indices
	rather than letting the styling layer search for the marker matters: a
	sender can put U+25B8 at the start of a line of body text, and a console
	that styles whatever looks like a marker would let them paint a fake part
	selection. The index comes from the code that drew the row."""
	out: list[str] = []

	def mark(rows: list[str], chosen: bool) -> None:
		"""Record these rows as the SELECTED header. `chosen` is not optional:
		an earlier version recorded every leaf's header, so every part looked
		selected and the mark said nothing about which one `m` would act on."""
		if chosen and marks is not None:
			marks.extend(range(base + len(out), base + len(out) + len(rows)))

	for part in parts or []:
		address = part.get("address", "")
		chosen = selected is not None and address == selected
		head_indent = (indent[:-2] + marker + " ") if chosen and len(indent) >= 2 \
			else indent

		def headed(text: str) -> list[str]:
			"""Header rows, with the mark on the FIRST one only.

			Applying the marked indent to every wrapped row repeated the glyph
			down the left edge, so a header that wrapped looked like several
			selected parts. Same display width either way, so the continuation
			rows still line up."""
			rows = _wrapped(text, width, indent)
			if chosen and rows:
				rows[0] = head_indent + rows[0][len(indent):]
			return rows
		if part.get("parts") is not None:
			rows = _wrapped(f"[{address}] {part['content_type']}", width, indent)
			out.extend(rows)
			out.extend(_rendered_parts(part["parts"], width, indent + "  ",
			                           selected=selected, marker=marker,
			                           marks=marks, base=base + len(out),
			                           external=external, pannable=pannable))
			continue
		header = _part_header(part)
		if part.get("encoding") == "text":
			rows = headed(header)
			mark(rows, chosen)
			out.extend(rows)
			# Content is NEVER marked: the mark says which part `m` acts on,
			# and spreading it over the body would say the whole part is a
			# control.
			body = _wrapped_content(part.get("text", ""), width, indent)
			_note_pannable(pannable, base, out, body)
			out.extend(body)
		elif part.get("encoding") == "base64":
			rows = headed(f"{header}  ({part.get('size')} bytes, binary)")
			mark(rows, chosen)
			out.extend(rows)
		elif part.get("storage") == "external":
			# An EXTERNAL leaf has bytes -- in a configured root, hash-pinned
			# and verified at claim time. It just does not carry them in the
			# envelope. Saying "no retained bytes" described it as empty, and
			# a human reading a licence file reported exactly that: "I can
			# only view part 0". That message belongs to a SCRUBBED transient
			# body, where the manifest really did outlive the payload, and
			# `storage` is what tells the two apart.
			pin = part.get("attachment") or {}
			where = f"{pin.get('root_id', '?')}:{pin.get('path', '?')}"
			rows = headed(f"{header}  ({part.get('size')} bytes, external file "
			              f"{where}, pin verified)")
			mark(rows, chosen)
			out.extend(rows)
			text = (external or {}).get(str(address))
			if text is not None:
				body = _wrapped_content(text, width, indent)
				_note_pannable(pannable, base, out, body)
				out.extend(body)
			elif part.get("content_type", "").startswith("text/"):
				out.extend(_wrapped("(not read into this pane)", width, indent))
			else:
				out.extend(_wrapped("(binary — open it at the path above)",
				                    width, indent))
		else:
			rows = headed(f"{header}  (no retained bytes — a transient body "
			              f"scrubbed on delivery)")
			mark(rows, chosen)
			out.extend(rows)
	return out


def input_line_index(state, columns: int, lines: int) -> int:
	"""Index, within the detail pane's wrapped lines, of the line currently
	being typed. -1 when nothing is being typed.

	The renderer is the only thing that knows how a draft wrapped, so the
	driver asks it and then tells the model through `follow_line`. Render
	stays observation-only."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return -1
	if state.mode not in (MODE_REPLY, MODE_COMPOSE, MODE_NOTICE):
		return -1
	produced = _detail_lines(state, columns)
	for index in range(len(produced) - 1, -1, -1):
		if produced[index].strip():
			return index
	return -1


def part_header_line_index(state, columns: int, lines: int) -> int:
	"""Index, within the detail pane's wrapped lines, of the SELECTED part's
	header row. -1 when nothing is marked.

	The counterpart of `input_line_index`, and it exists for the same reason:
	only the renderer knows how the content laid out, and the driver has to
	tell the model where to scroll. Stacked, the detail pane is 60% of the
	body rather than all of it, so the later parts of a multipart message
	start below the fold -- and a mark the human cannot see is a cursor that
	does not exist as far as they are concerned."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return -1
	marks: list[int] = []
	_detail_lines(state, columns, marks=marks)
	return marks[0] if marks else -1


def input_caret(state, columns: int, lines: int) -> tuple[int, int]:
	"""Where the terminal cursor belongs while typing.

	Computed here because only the renderer knows the layout; the driver just
	moves the caret there. A cursor parked in the corner while the human types
	elsewhere is a small thing that makes a console feel broken."""
	if columns < MIN_COLUMNS or lines < MIN_LINES:
		return (0, 0)
	produced = _detail_lines(state, columns)
	offset = max(0, min(state.detail_offset, max(0, len(produced) - state.detail_height)))
	# The detail pane starts at column 0 now and at a ROW below the rule, so
	# the caret's screen row carries the whole offset the pane split produces.
	base = _detail_screen_top(state, lines)
	for index in range(len(produced) - 1, -1, -1):
		line = produced[index]
		if line.lstrip().startswith((">", "> ")) or "> " in line:
			row = index - offset + base
			if not (0 <= row < lines):
				break
			# Follow the MODEL CARET, not the end of the line. The caret used
			# to sit after the last character because insertion was the only
			# edit there was; with a real caret, parking the terminal cursor
			# at the end would show the human one position while their next
			# keystroke lands at another.
			text, caret = state._read_buffer()
			drawn = display_width(line)
			if text:
				tail = display_width(text[caret:])
				drawn = max(0, drawn - tail)
			return (row, min(columns - 1, drawn))
	return (min(lines - 1, base), 0)


# What an empty body row says. Deliberately an ACTION, not "(none)": ruled
# from the terminal trial, and the single exception to keys living only in the
# footer and `?` help -- an empty row has no state of its own to report.
EMPTY_BODY = "Ctrl+e to edit"


def _body_summary(body: str, width: int) -> list[str]:
	"""What the body IS, since it is never typed here.

	A count rather than the text: the body may be long, the editor is where it
	is read and written, and a truncated preview would invite editing the
	preview."""
	if not body:
		# The EMPTY state names the key, by Slawomir's trial ruling. It is the
		# one place a keystroke belongs in the pane: there is no body state to
		# report yet, so the row would otherwise say only that nothing is
		# there. A body with content goes back to reporting its size.
		return _wrapped(f"  body:    {EMPTY_BODY}", width)
	lines = body.count("\n") + 1
	# Plural spelled out rather than "1 lines".
	unit = "line" if lines == 1 else "lines"
	# STATE, not the key that changes it: the footer names `^E` while it works.
	return _wrapped(f"  body:    {lines} {unit}, {len(body)} characters", width)


# The contextual/global label tables and `legend_actions` that stood here are
# REMOVED. They existed to compose the footer's shortcut catalogue, and nothing
# displays one any more: `?` help and the README own shortcuts, and the bottom
# row is one status line. What they were composed FROM survives, because it was
# never presentation -- `state.affordances()` and `state.modal_affordances()`
# are the single query dispatch consults, and `keys.MODE_LEGENDS` still carries
# each modal control's key codes so a test can assert every documented chord
# really dispatches in that mode.


# One line, ruled. No second prompt row and no mid-screen instructions: the
# question is small, and the draft it is about is what the human should still
# be able to see.
CONFIRM_DISCARD_FOOTER = "Discard draft? y/N"


def _footer(state, columns: int) -> list[str]:
	from . import keys as K
	if state.mode == MODE_CONFIRM_QUIT:
		return [_cell("  QUIT WITH UNRESOLVED CLAIMS?", columns),
		        _cell(f"  {state.status}", columns)]
	if state.mode == MODE_CONFIRM_DISCARD:
		# ONE row, on the status line, exactly as ruled. `y/N` with the
		# capital on the default, which is the conventional spelling for a
		# destructive question -- and the opposite of the send confirmation
		# next door, which is `Y/n` because sending is what the human just
		# asked for.
		return [_cell(f"  {CONFIRM_DISCARD_FOOTER}", columns)]
	if state.mode == MODE_CONFIRM_SEND:
		# ONE row, and it IS the footer: no severity prefix, no separate
		# status row, no context row. Slawomir's literal target. The draft
		# gains the row the second line used to take, which is the point --
		# the question is small and what you are about to send is not.
		return [_cell(f"  {CONFIRM_SEND_FOOTER}", columns)]
	# ONE row, and it says what the console DID -- an invoked operation, a
	# confirmation, an outcome, a warning, an error. No shortcut catalogue, no
	# `acting on ...` clause: both were reference the human reads once, and
	# `?` help owns them. An empty status is a blank row, NOT a place to put a
	# reworded hint.
	mark = _SEVERITY_MARK.get(state.status_severity, "i")
	bar = f"  [{mark}] {state.status}" if state.status else ""
	return [_cell(bar, columns)]
