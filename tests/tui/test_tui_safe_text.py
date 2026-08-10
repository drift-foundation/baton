"""Hostile-input corpus for console rendering.

Written BEFORE the renderer so the renderer is built to pass it rather than
retrofitted. Baton renders nothing, so every one of these attacks lands
entirely on the console: message bodies and subjects come from other
participants and a terminal executes what it is handed.
"""

from __future__ import annotations

import pytest

from baton_tui.safe_text import display_width, fit, sanitize_block, sanitize_line

ESC = "\x1b"

# Each entry is a real terminal capability a sender could otherwise reach.
HOSTILE = {
	"clear_screen":        f"before{ESC}[2Jafter",
	"cursor_home":         f"{ESC}[Hoverwritten",
	"cursor_up":           f"line{ESC}[5Aclimb",
	"scroll_region":       f"{ESC}[1;5r",
	"set_window_title":    f"{ESC}]0;pwned\x07",
	"clipboard_osc52":     f"{ESC}]52;c;cHduZWQ=\x07",
	"alt_screen":          f"{ESC}[?1049h",
	"bracketed_paste":     f"{ESC}[?2004h",
	"device_status_query": f"{ESC}[6n",
	"reset_terminal":      f"{ESC}c",
	"colour_injection":    f"{ESC}[31mred{ESC}[0m",
	"eight_bit_csi":       "\x9b31m",
	"eight_bit_osc":       "\x9d0;title\x9c",
	"carriage_overwrite":  "real text\rFAKE TEXT",
	"backspace_overwrite": "safe\x08\x08\x08\x08evil",
	"bell_spam":           "ding\x07\x07\x07",
	"nul_byte":            "before\x00after",
	"bidi_override":       "trusted‮detsurtnu",
	"bidi_isolate":        "a⁦b⁩c",
	"zero_width_space":    "ad​min",
	"soft_hyphen":         "ad­min",
	"unassigned":          "x￾y",
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_no_escape_or_control_survives_sanitizing(name):
	"""The load-bearing assertion: after sanitizing, nothing in the string can
	be interpreted by a terminal as an instruction."""
	for sanitize in (sanitize_line, sanitize_block):
		out = sanitize(HOSTILE[name])
		for char in out:
			code = ord(char)
			assert code not in (0x1B, 0x9B, 0x9D, 0x07, 0x08, 0x00, 0x0D), (
				f"{name}: {sanitize.__name__} left {char!r} (U+{code:04X})")
			assert not (0x00 <= code < 0x20 and char not in "\n"), f"{name}: C0 survived"
			assert not (0x80 <= code < 0xA0), f"{name}: C1 survived"


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_hostile_text_is_neutralized_not_deleted(name):
	"""Escapes are made visible rather than removed. A silently stripped
	control hides that the sender put it there, and shifts every offset after
	it -- so a human comparing what they see against what was delivered would
	be comparing two different things."""
	out = sanitize_line(HOSTILE[name])
	assert out, f"{name}: sanitizing produced nothing"
	# The surrounding legible text is preserved.
	for fragment in ("before", "after", "real text", "trusted", "admin", "safe"):
		if fragment in HOSTILE[name]:
			assert fragment in out or fragment.replace("\x00", "") in out


def test_a_subject_cannot_forge_extra_inbox_rows():
	"""An inbox row is ONE line. If a newline survived in a subject, a sender
	could draw rows that look like other people's messages."""
	forged = "Real subject\nFAKE  hq.lead  Approved and merged"
	out = sanitize_line(forged)
	assert "\n" not in out
	assert "FAKE" in out          # visible as part of the one real subject


def test_detail_pane_keeps_real_newlines():
	"""Structure survives where structure is meaningful -- otherwise a
	Markdown body becomes one unreadable line."""
	out = sanitize_block("# Title\n\nBody line\n")
	assert out.count("\n") == 3
	assert "<" not in out         # nothing was neutralized in clean text


def test_clean_text_passes_through_untouched():
	"""The neutralizer must not damage ordinary content, or people will paste
	around it."""
	for clean in ("plain ascii", "# Markdown **bold**", "accents: éüñ",
	              "日本語のテキスト", "emoji: 🚀", "code: a[i] = b->c;"):
		assert sanitize_line(clean) == clean.replace("\n", " ")


# -- width, where a miscount becomes an overflow --------------------------

def test_width_counts_cells_not_characters():
	assert display_width("abc") == 3
	assert display_width("日本") == 4          # wide: two cells each
	assert display_width("é") == 1       # combining mark takes none
	assert display_width("") == 0


@pytest.mark.parametrize("text,columns", [
	("日本語テキスト", 8), ("abcdefghij", 5), ("é" * 20, 6),
	("áb́ć", 2), ("🚀🚀🚀🚀", 5), ("short", 40),
])
def test_fit_never_exceeds_its_column_budget(text, columns):
	"""Truncation is by measured width, never character count: one wide
	character must not overflow the cell it was allotted, because a pane that
	overflows corrupts the layout the human is reading."""
	assert display_width(fit(text, columns)) <= columns


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_fit_is_safe_on_hostile_input_at_every_width(name):
	"""Truncation must not be able to slice a neutralized escape back into a
	live one."""
	for columns in range(0, 25):
		out = fit(HOSTILE[name], columns)
		assert display_width(out) <= columns
		assert ESC not in out and "\x9b" not in out and "\r" not in out


def test_enormous_single_line_part_is_bounded():
	"""A 10 MB part with no newline must not be handed to a terminal whole."""
	out = fit("x" * (10 * 1024 * 1024), 80)
	assert display_width(out) <= 80


# -- wrapping: nothing may disappear past the pane edge -------------------

WRAP_CASES = {
	"prose":            "a fairly ordinary sentence of prose that will not fit",
	"one_long_token":   "x" * 200,
	"long_url":         "https://example.com/" + "segment/" * 20,
	"cjk":              "日本語のテキストがここにあり折り返しが必要です" * 3,
	"combining":        "é" * 80,
	"hostile":          "before\x1b[2Jafter\rOVERWRITE" * 5,
	"blank_lines":      "first\n\n\nlast",
	"mixed":            "short\n" + "y" * 120 + "\n日本語 mixed with latin text",
	"trailing_spaces":  "words   " * 30,
}


@pytest.mark.parametrize("name", sorted(WRAP_CASES))
@pytest.mark.parametrize("columns", [1, 5, 12, 20, 40, 79])
def test_every_wrapped_line_fits_the_pane(name, columns):
	"""Clipping and wrapping are not interchangeable: once a tail is cut it
	cannot be scrolled to. Every visual row must fit, at every width."""
	from baton_tui.safe_text import display_width, wrap
	for line in wrap(WRAP_CASES[name], columns):
		# A single character wider than the entire pane overflows by one cell
		# rather than being deleted -- a stated limit that only arises below
		# MIN_COLUMNS, where the console refuses to draw panes anyway.
		assert display_width(line) <= max(columns, 2), f"{name} @{columns}: {line!r}"


@pytest.mark.parametrize("name", sorted(WRAP_CASES))
@pytest.mark.parametrize("columns", [12, 20, 40, 79])
def test_wrapped_lines_fit_exactly_at_usable_widths(name, columns):
	"""At any width the console will actually draw, the promise is exact."""
	from baton_tui.safe_text import display_width, wrap
	for line in wrap(WRAP_CASES[name], columns):
		assert display_width(line) <= columns, f"{name} @{columns}: {line!r}"


WHITESPACE_CASES = {
	"leading_indent":   "   indented text that continues past the pane edge",
	"code_indent":      "    def handler(request):  # aligned trailing comment",
	"trailing_spaces":  "trailing   ",
	"internal_runs":    "columns    aligned    by    spaces",
	"only_spaces":      "     ",
	"tabs":             "\tafter a tab",
	"markdown_list":    "- item one\n  - nested item\n    continued line here",
}


@pytest.mark.parametrize("name", sorted({**WRAP_CASES, **WHITESPACE_CASES}))
@pytest.mark.parametrize("columns", [4, 8, 17, 40, 79])
def test_wrapping_reconstructs_the_text_exactly(name, columns):
	"""EXACT reconstruction, whitespace included.

	The previous version of this test stripped whitespace from both sides
	before comparing, so it could not see that wrapping discarded leading
	indentation and trailing spaces -- it asserted the very thing it needed to
	catch. Markdown is displayed as source, so an indent IS content, and
	silently reformatting a sender's text while claiming losslessness is worse
	than not wrapping at all."""
	from baton_tui.safe_text import sanitize_block, wrap
	source = {**WRAP_CASES, **WHITESPACE_CASES}[name]
	sanitized = sanitize_block(source)
	rebuilt = "\n".join("".join(wrap(paragraph, columns))
	                    for paragraph in sanitized.split("\n"))
	assert rebuilt == sanitized, f"{name} @{columns}: text was altered"


def test_indentation_stays_with_its_line():
	"""Breaking inside a leading indent is lossless but reads as broken."""
	from baton_tui.safe_text import wrap
	assert wrap("   indented code", 8)[0].startswith("   ")
	assert wrap("    def f():", 20) == ["    def f():"]


def test_explicit_blank_lines_survive_wrapping():
	from baton_tui.safe_text import wrap
	assert wrap("first\n\nlast", 40) == ["first", "", "last"]


def test_wrapping_never_emits_a_control_character():
	from baton_tui.safe_text import wrap
	for line in wrap(HOSTILE["clear_screen"] + "\n" + HOSTILE["carriage_overwrite"], 15):
		for char in line:
			assert ord(char) >= 0x20 and ord(char) != 0x7F


def test_a_token_wider_than_the_pane_is_broken_not_dropped():
	from baton_tui.safe_text import display_width, wrap
	token = "z" * 100
	lines = wrap(token, 10)
	assert "".join(lines) == token
	assert all(display_width(line) <= 10 for line in lines)


# -- split_cells: the seam where two terminal attributes meet ---------------

@pytest.mark.parametrize("text", [
	"plain ascii text",
	"\u5e83\u3044\u6587\u5b57 mixed with ascii",
	"\u5e83" * 12,
	"",
	"a",
])
@pytest.mark.parametrize("columns", [0, 1, 2, 3, 7, 12, 40, 400])
def test_split_cells_loses_nothing_and_never_overflows(text, columns):
	from baton_tui.safe_text import display_width, split_cells
	head, tail = split_cells(text, columns)
	assert head + tail == text                      # nothing lost, nothing added
	assert display_width(head) <= max(0, columns)   # the head fits its budget


def test_a_wide_character_straddling_the_boundary_goes_to_the_tail():
	"""Putting it in the head would make the head one cell too wide -- the
	exact fault that pushed the divider off its column."""
	from baton_tui.safe_text import display_width, split_cells
	head, tail = split_cells("a\u5e83b", 2)
	assert head == "a"
	assert tail == "\u5e83b"
	assert display_width(head) == 1                 # under budget, not over


def test_split_cells_is_exact_when_the_boundary_falls_between_characters():
	from baton_tui.safe_text import split_cells
	assert split_cells("abcdef", 3) == ("abc", "def")
	assert split_cells("\u5e83\u5e83x", 4) == ("\u5e83\u5e83", "x")


# -- re-review R3: overlong unbroken content is elided, not fractured -------

@pytest.mark.parametrize("columns", [10, 20, 30, 40, 59, 80])
def test_a_token_wider_than_the_pane_is_elided_not_fractured(columns):
	"""Slawomir's ruling. A 200-character token split across four rows is not
	four rows of a token: it is unreadable, uncopyable, and it pushes the rest
	of the message off the pane."""
	from baton_tui.safe_text import ELLIPSIS, display_width, wrap_display
	text = "x" * (columns * 4)
	rows = wrap_display(text, columns)
	assert len(rows) == 1, "the oversized token was fractured across rows"
	assert rows[0].endswith(ELLIPSIS), "nothing marks the hidden remainder"
	assert display_width(rows[0]) <= columns


def test_wrapping_resumes_after_an_elided_token():
	"""Only the oversized token is hidden; the rest of the paragraph is not
	collateral damage."""
	from baton_tui.safe_text import ELLIPSIS, wrap_display
	rows = wrap_display("see " + "x" * 200 + " and then more words here", 30)
	assert any(row.endswith(ELLIPSIS) for row in rows)
	assert "and then more words here" in " ".join(rows)


@pytest.mark.parametrize("columns", [10, 20, 40, 80])
def test_ordinary_text_wraps_identically_either_way(columns):
	"""The ellipsis rule must not change text that never needed it, or the
	read-only and editable panes would disagree about ordinary paragraphs."""
	from baton_tui.safe_text import wrap, wrap_display
	for text in ("the quick brown fox jumps over the lazy dog " * 4,
	             "line one\nline two\n\nline four",
	             "  indented continues here and wraps eventually as well"):
		assert wrap(text, columns) == wrap_display(text, columns)


def test_the_ellipsis_fits_by_display_cells_not_characters():
	"""Trimming one CHARACTER overflows by a cell when the last one is wide --
	the fault that moved the divider in round 2."""
	from baton_tui.safe_text import display_width, wrap_display
	rows = wrap_display("\u5e83" * 40, 11)
	assert display_width(rows[0]) <= 11


def test_lossless_wrap_still_fractures_and_loses_nothing():
	"""`wrap` is the editable-text contract and must NOT have acquired the
	ellipsis: hiding characters someone is typing is a worse fault than
	hiding characters they are reading."""
	from baton_tui.safe_text import ELLIPSIS, wrap
	text = "y" * 100
	rows = wrap(text, 20)
	assert "".join(rows) == text
	assert not any(ELLIPSIS in row for row in rows)
