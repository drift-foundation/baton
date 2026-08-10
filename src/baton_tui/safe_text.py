"""Rendering untrusted text safely.

Baton itself renders nothing, so the console owns this entire attack surface.
Every part body arrives from another participant and must be treated as
hostile: a message body can carry ANSI escape sequences, and a terminal
interprets them. Unfiltered, a sender could reposition the cursor, rewrite
rows the human already read, clear the screen, set the window title, or (with
OSC 52) put arbitrary data on the operator's clipboard. `\\r` alone is enough
to overwrite a line so the visible text differs from the delivered bytes.

The rule is that NOTHING a sender writes may become a terminal instruction.
Text is transformed to printable characters before it can reach a screen, and
what the human sees is what was actually delivered.

Neutralize, do not strip: a removed character changes offsets and hides that
anything was there, so escapes are made visible instead. If a message really
does contain `ESC[2J`, the human should see that it does.
"""

from __future__ import annotations

import unicodedata

# C0 controls except tab, which layout handles, and newline, which is
# structure rather than an instruction.
_C0 = {c for c in range(0x00, 0x20)} - {0x09, 0x0A}
_C0.add(0x7F)                                   # DEL
_C1 = set(range(0x80, 0xA0))                    # C1 controls, incl. 8-bit CSI/OSC

# Characters that reorder or hide text without being controls. Bidi overrides
# are how a line can render in an order the bytes do not have -- the same
# trick as the "Trojan Source" source-code attack, and an inbox showing a
# subject is exactly as vulnerable as a compiler.
_BIDI = {0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
         0x2066, 0x2067, 0x2068, 0x2069}
_INVISIBLE = {0x00AD, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}

_REPLACEMENT = "�"


def sanitize_line(text: str) -> str:
	"""One line of untrusted text, safe to place in a terminal cell run.

	Newlines are NOT structure here -- a subject or an inbox row is one line,
	and an embedded newline would let a sender forge additional rows."""
	return _sanitize(text, keep_newlines=False)


def sanitize_block(text: str) -> str:
	"""Untrusted text for the detail pane, where newlines are real structure
	but every other control is not."""
	return _sanitize(text, keep_newlines=True)


def _sanitize(text: str, *, keep_newlines: bool) -> str:
	out = []
	for char in text:
		code = ord(char)
		if char == "\n":
			out.append("\n" if keep_newlines else " ")
			continue
		if char == "\t":
			out.append("    ")
			continue
		if code in _C0 or code in _C1:
			# Visible, not deleted: the human should be able to tell that the
			# sender put a control character here.
			out.append(f"<{unicodedata.name(char, f'U+{code:04X}')[:24]}>"
			           if code not in (0x1B,) else "<ESC>")
			continue
		if code in _BIDI or code in _INVISIBLE:
			out.append(f"<U+{code:04X}>")
			continue
		if unicodedata.category(char) in ("Cs", "Co", "Cn"):
			out.append(_REPLACEMENT)
			continue
		out.append(char)
	return "".join(out)


def display_width(text: str) -> int:
	"""Terminal columns a sanitized string occupies.

	Wide characters take two cells and combining marks take none. Getting this
	wrong does not merely misalign a pane -- a sender who can make the
	measured width disagree with the drawn width can push content past a
	boundary the layout believed it had."""
	width = 0
	for char in text:
		if unicodedata.combining(char):
			continue
		width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
	return width


def fit(text: str, columns: int, *, ellipsis: str = "…") -> str:
	"""Sanitize and truncate to at most `columns` display cells.

	Truncation is by measured width, never by character count, so one wide
	character cannot overflow the cell it was allotted."""
	safe = sanitize_line(text)
	if display_width(safe) <= columns:
		return safe
	if columns <= 0:
		return ""
	budget = columns - display_width(ellipsis)
	if budget <= 0:
		return ellipsis[:columns]
	out = []
	used = 0
	for char in safe:
		step = display_width(char)
		if used + step > budget:
			break
		out.append(char)
		used += step
	return "".join(out) + ellipsis


def pad(text: str, columns: int) -> str:
	"""Pad to exactly `columns` DISPLAY CELLS.

	`f"{text:<20}"` pads by character count, so a string containing wide
	characters ends up wider than its budget and pushes everything after it
	rightwards. That is how the pane divider drifted between rows: an inbox
	row with Japanese in the subject was padded to 24 characters but occupied
	27 cells, and the divider moved with it."""
	deficit = columns - display_width(text)
	return text + " " * deficit if deficit > 0 else text


def split_cells(text: str, columns: int) -> tuple[str, str]:
	"""Split at exactly `columns` DISPLAY CELLS, losing nothing.

	Unlike `fit` this keeps the tail, and unlike ordinary slicing it counts
	cells rather than characters. A wide character straddling the boundary
	goes to the TAIL: putting it in the head would make the head one cell too
	wide, which is what pushed the divider off its column before.

	Used where two different terminal attributes meet on one row, so the seam
	lands on the same cell the renderer drew the divider in."""
	if columns <= 0:
		return ("", text)
	used = 0
	for index, char in enumerate(text):
		step = display_width(char)
		if used + step > columns:
			return (text[:index], text[index:])
		used += step
	return (text, "")


def wrap(text: str, columns: int) -> list[str]:
	"""Soft-wrap to `columns` DISPLAY CELLS, losing NOTHING.

	The contract is EXACT RECONSTRUCTION: concatenating the lines of each
	paragraph reproduces that paragraph character for character, with only
	visual line boundaries inserted.

	Whitespace is content. Indentation carries meaning in Markdown source, in
	code, and in anything a sender formatted deliberately -- and Markdown is
	currently displayed AS source, so discarding leading spaces silently
	reformats the sender's text while claiming to be lossless. An earlier
	version did exactly that, and the regression could not catch it because it
	stripped whitespace from both sides before comparing.

	Clipping and wrapping are not interchangeable: once a tail is cut it cannot
	be scrolled to. The detail pane used to clip, so the end of every long line
	simply did not exist.

	Breaks prefer the last space that fits, keeping words whole; the space
	stays on the line that ends with it, so nothing is lost. A token wider than
	the pane is broken at the cell boundary rather than allowed to overflow.

	ONE stated limit: a single character wider than the whole pane -- a 2-cell
	CJK glyph in a 1-cell column -- is emitted on its own line and overflows by
	one cell. Deleting the human's text to satisfy an arithmetic promise would
	be worse, and it only arises below the console's minimum usable width."""
	return _wrap(text, columns, elide=False)


def wrap_display(text: str, columns: int) -> list[str]:
	"""Wrap for READ-ONLY content: whitespace breaks, and a token wider than
	the whole pane is truncated with an ellipsis rather than fractured.

	Slawomir's ruling. A 200-character token split across four rows is not four
	rows of a token -- it is unreadable, uncopyable, and it pushes the rest of
	the message off the pane. A visible U+2026 says plainly that something is
	hidden, which fracturing does not. Wrapping RESUMES at the next space, so
	only the oversized token is elided and the rest of the paragraph survives.

	NEVER use this for editable text. Hiding characters a human is currently
	typing is a different and much worse fault than hiding characters they are
	reading, so `wrap` stays lossless for drafts.

	The underlying model is untouched either way: this decides presentation,
	not content."""
	return _wrap(text, columns, elide=True)


ELLIPSIS = "\u2026"


def _elided(line: str, columns: int) -> str:
	"""`line` with room made for the ellipsis, measured in DISPLAY CELLS.

	Dropping one CHARACTER would overflow the pane by a cell whenever the last
	one was wide, which is the fault that moved the divider in round 2."""
	room = columns - display_width(ELLIPSIS)
	if room <= 0:
		return ELLIPSIS
	head, _ = split_cells(line, room)
	return head + ELLIPSIS


def wrap_overflow(text: str, columns: int) -> list[str]:
	"""Wrap at whitespace, but leave an oversized token WHOLE on its own line.

	For content the human can scroll sideways. Fracturing it across rows was
	rejected as unreadable and uncopyable; eliding it discards the tail, which
	is right when nothing can reach the tail and wrong once something can. The
	line comes back longer than `columns` ON PURPOSE -- the pane windows it
	horizontally and says which side is hidden."""
	return _wrap(text, columns, elide=False, keep_oversized=True)


def _wrap(text: str, columns: int, *, elide: bool,
          keep_oversized: bool = False) -> list[str]:
	"""Shared engine. `elide` decides the fate of a token that cannot fit on a
	line of its own: fracture it (lossless) or truncate it (explicit)."""
	if columns <= 0:
		return [""]
	out: list[str] = []
	for paragraph in sanitize_block(text).split("\n"):
		if not paragraph:
			out.append("")
			continue
		line = ""
		width = 0
		break_at = 0            # index in `line` just past the last space run
		eliding = False
		for char in paragraph:
			step = display_width(char)
			if eliding:
				# Inside a token already truncated: skip the rest of it and
				# resume wrapping at the next space.
				if char == " ":
					eliding = False
					line, width, break_at = "", 0, 0
				continue
			# An oversized token with no break opportunity stays INTACT when
			# the caller asked for that: it falls through to the ordinary
			# append below, so the space that ends it still registers as the
			# next break opportunity and the rest of the paragraph wraps
			# normally. Fracturing it was rejected as unreadable; eliding it
			# discards the tail, which is right when nothing can reach the
			# tail and wrong once something can.
			oversized = keep_oversized and break_at == 0
			if line and width + step > columns and not oversized:
				if break_at > 0:
					out.append(line[:break_at])
					line = line[break_at:]
					width = display_width(line)
				elif elide and char != " ":
					# No break opportunity anywhere on this line AND the
					# character that overflowed is not itself a space: the
					# token really is wider than the pane. A space here means
					# the line ended exactly at a word boundary, which is an
					# ordinary break -- eliding it would truncate text that
					# fits, and would make read-only and editable panes
					# disagree about ordinary paragraphs.
					out.append(_elided(line, columns))
					eliding = True
					continue
				else:
					out.append(line)
					line, width = "", 0
				break_at = 0
			line += char
			width += step
			# Only a space that FOLLOWS content is a break opportunity, so
			# leading indentation is never eaten.
			if char == " " and line.strip():
				break_at = len(line)
		if line and not eliding:
			out.append(line)
	return out or [""]
