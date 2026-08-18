"""W48: the Event payload is JSON the eye can follow.

The reader appended `payload: ` plus one `json.dumps(..., sort_keys=True)`
line. Nested objects and arrays arrived as a single long line and the
generic wrapper then folded it at whatever column the pane happened to
be — obscuring precisely the structure an operator opens a payload to
read.

The payload is now a section: `payload:` alone, then the value at two
spaces per nesting level, one logical line at a time, before any
terminal-width handling. Two smaller defects fall out of the same code
and are fixed with it: a present falsy payload was rendered as `{}`, and
a wrapped line lost its structural depth to a fixed four-space
continuation.

Nothing here reads or writes the authority beyond the one projection
read the reader already made.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console, soft_wrap             # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                        "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


def _console(world):
	return Console(world["store"], "lang", "ada",
	               config_path=world["config"])


def _entry(payload, **extra):
	"""One Event entry in the projection's shape, with a chosen payload
	— so the payload's TYPE can be varied independently of whatever
	transitions happen to emit."""
	entry = {"seq": 7, "kind": "request", "actor": "lang.ada",
	         "ts": "2026-08-18T15:00:00Z", "roles": ["consumer"],
	         "related": [], "references": [], "claim_interval": None}
	entry.update(extra)
	if payload is not _MISSING:
		entry["payload"] = payload
	return entry


_MISSING = object()


def _payload_block(lines):
	"""The logical lines from `payload:` onward, label excluded."""
	start = lines.index("  payload:")
	return lines[start + 1:]


def _reassemble(lines):
	"""The payload block parsed back to a value — the parity check the
	acceptance boundary asks for."""
	return json.loads("\n".join(line[2:] for line in _payload_block(lines)))


# -- the block itself --------------------------------------------------------

def test_the_label_stands_alone_and_the_json_begins_beneath_it(world):
	lines = _console(world)._event_lines(_entry({"work": "W2"}))
	assert "  payload:" in lines, lines
	block = _payload_block(lines)
	assert block[0] == "  {", block
	assert block[-1] == "  }", block


def test_nesting_is_two_spaces_per_level(world):
	payload = {"outer": {"inner": {"leaf": 1}}}
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	assert block == [
		"  {",
		'    "outer": {',
		'      "inner": {',
		'        "leaf": 1',
		"      }",
		"    }",
		"  }",
	], block


def test_arrays_keep_their_json_spelling(world):
	payload = {"items": [1, "two", None, True, {"k": []}]}
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	assert block == [
		"  {",
		'    "items": [',
		"      1,",
		'      "two",',
		"      null,",
		"      true,",
		"      {",
		'        "k": []',
		"      }",
		"    ]",
		"  }",
	], block


def test_keys_are_deterministic(world):
	payload = {"zebra": 1, "alpha": 2, "middle": 3}
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	assert [line.strip() for line in block[1:-1]] == \
		['"alpha": 2,', '"middle": 3,', '"zebra": 1']
	# and the same payload built in another key order renders identically
	other = {"middle": 3, "zebra": 1, "alpha": 2}
	assert _payload_block(
		_console(world)._event_lines(_entry(other))) == block


def test_unicode_stays_readable(world):
	payload = {"naïve": "ça va — 日本語", "emoji": "✅"}
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	joined = "\n".join(block)
	assert "naïve" in joined and "ça va — 日本語" in joined
	assert "✅" in joined
	assert "\\u" not in joined, "Unicode was escaped instead of shown"


def test_escaped_strings_keep_their_json_escapes(world):
	payload = {"quoted": 'he said "no"', "path": "a\\b",
	           "line": "one\ntwo", "tab": "a\tb"}
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	joined = "\n".join(block)
	assert '\\"no\\"' in joined
	assert "a\\\\b" in joined
	assert "one\\ntwo" in joined, "a newline escape became a real break"
	assert "a\\tb" in joined
	# every logical line stays one line — an escape never splits the block
	assert len(block) == 6, block


# -- absent is not falsy -----------------------------------------------------

def test_an_absent_payload_renders_the_empty_object(world):
	lines = _console(world)._event_lines(_entry(_MISSING))
	assert _payload_block(lines) == ["  {}"]


@pytest.mark.parametrize("payload,expected", [
	({}, "{}"),
	(None, "null"),
	(False, "false"),
	(0, "0"),
	("", '""'),
	([], "[]"),
	(0.0, "0.0"),
])
def test_a_present_falsy_payload_keeps_its_own_type(world, payload, expected):
	"""The defect the ruling names: `entry.get("payload") or {}` turned
	every falsy JSON value into `{}`, so the reader asserted an empty
	object where the ledger holds `null`, `false`, `0`, `""` or `[]`."""
	block = _payload_block(_console(world)._event_lines(_entry(payload)))
	assert block == [f"  {expected}"], block


@pytest.mark.parametrize("payload", [
	None, False, 0, "", [], [1, 2], "a string", 42,
])
def test_a_non_object_payload_does_not_crash_the_typed_labels(world, payload):
	"""The typed labels read the payload's own fields, which only an
	object has. Reaching `.get` on a list or scalar would raise while
	painting."""
	lines = _console(world)._event_lines(_entry(payload))
	assert lines[0].startswith("#7 request")
	assert "  payload:" in lines


def test_the_block_reassembles_to_the_projected_value(world):
	"""JSON output and TUI rendering are views of the SAME complete
	payload — reassembling the unwrapped block parses back to it."""
	payload = {"a": [1, {"b": None}], "c": "ünicode", "d": {"e": True},
	           "f": "", "g": 0}
	lines = _console(world)._event_lines(_entry(payload))
	assert _reassemble(lines) == payload


def test_the_block_reassembles_for_a_real_transition(world):
	"""The same parity against a payload the authority actually wrote,
	rather than one this test invented."""
	store = world["store"]
	work = tr.create_work(store, team="lang", kind="bug", title="t",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")["work_id"]
	blocker = tr.create_work(store, team="lang", kind="bug", title="b",
	                         origin="external-report",
	                         classification="suspected-defect",
	                         author="ada", body="b")["work_id"]
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="needs it")
	entry = pj.work_events(store, work)["events"][-1]
	lines = _console(world)._event_lines(entry)
	assert _reassemble(lines) == entry["payload"]
	# nested structure is visible rather than folded onto one line
	assert any(line.startswith('      "') for line in _payload_block(lines)), \
		"nothing reached the second nesting level"


def test_nothing_is_folded_summarized_or_clipped(world):
	"""'the complete payload is never folded, summarized, or silently
	clipped' — every leaf value appears somewhere in the block."""
	payload = {"deep": {"deeper": {"deepest": ["needle-one", "needle-two"]}},
	           "flat": "needle-three"}
	block = "\n".join(_payload_block(
		_console(world)._event_lines(_entry(payload))))
	for needle in ("needle-one", "needle-two", "needle-three"):
		assert needle in block, f"{needle} was folded away"
	assert "..." not in block and "…" not in block


# -- the soft wrap -----------------------------------------------------------

def test_a_wrapped_line_keeps_its_structural_indentation():
	"""The second defect the ruling names: the old wrapper gave every
	indented line one fixed four-space continuation, so a deeply nested
	scalar wrapped to a depth it does not occupy."""
	line = '        "key": "' + "x" * 60 + '"'
	out = soft_wrap(line, 30)
	assert len(out) > 1, "the fixture did not wrap"
	assert out[0].startswith('        "key"')
	for continuation in out[1:]:
		leading = len(continuation) - len(continuation.lstrip(" "))
		assert leading == 10, \
			f"continuation sits at {leading}, not the line's 8 + 2"


@pytest.mark.parametrize("indent", [0, 2, 4, 6, 8, 12])
def test_the_continuation_is_always_two_cells_deeper(indent):
	line = " " * indent + "token " + "y" * 80
	out = soft_wrap(line, 32)
	assert len(out) > 1
	for continuation in out[1:]:
		leading = len(continuation) - len(continuation.lstrip(" "))
		assert leading == indent + 2


def test_the_wrap_generalizes_the_old_label_behavior():
	"""The rule is a generalization, not a replacement: a top-level line
	still continues at two cells and a two-space fact line at four,
	which is exactly what the fixed-indent wrapper produced."""
	top = "#7 request lang.ada " + "z" * 60
	fact = "  rationale: " + "z" * 60
	assert all(line.startswith("  ") and not line.startswith("   ")
	           for line in soft_wrap(top, 30)[1:])
	assert all(line.startswith("    ") and not line.startswith("     ")
	           for line in soft_wrap(fact, 30)[1:])


@pytest.mark.parametrize("width", list(range(8, 41)))
def test_the_wrap_drops_no_character_at_any_width(width):
	"""Presentation only: wrapping adds the continuation indent and
	nothing else changes, so stripping that indent reassembles the
	logical line BYTE for byte.

	This assertion was briefly weakened to ignore spaces while the wrap
	consumed the one it broke at. That was accommodating a defect
	rather than finding it: a space inside a JSON string is data, and
	`"alpha   beta"` must not come back as `"alphabeta"`."""
	# A shallow line, so every width in this range is a pane that can
	# actually hold its indentation. A pane NARROWER than the line's own
	# indent is a different, degenerate case with its own test below —
	# there the continuation is clamped and the output is mostly
	# whitespace, which proves termination rather than fidelity.
	line = '  "k": "' + "abcdefghij" * 8 + '"'
	out = soft_wrap(line, width)
	assert out[0] + "".join(part[4:] for part in out[1:]) == line, \
		"stripping the continuation indent did not reassemble the line"
	assert all(len(part) <= max(8, width) for part in out)


def test_wrapping_preserves_spaces_inside_a_json_string():
	"""Structural continuation indentation is presentation; spaces in
	the serialized JSON are data and must survive byte-for-byte."""
	line = '  "value": "alpha   beta gamma delta"'
	out = soft_wrap(line, 20)
	continuation_indent = " " * 4
	reassembled = out[0] + "".join(
		part[len(continuation_indent):] for part in out[1:])
	assert reassembled == line


def test_an_unbreakable_token_is_shown_whole_across_lines():
	"""A long JSON token has no spaces to break at. It must still be
	shown — hard-broken across lines, never truncated."""
	token = "q" * 90
	out = soft_wrap(f'    "id": "{token}"', 24)
	assert token in "".join(part.strip() for part in out)


def test_a_short_line_is_returned_untouched():
	assert soft_wrap("  payload:", 40) == ["  payload:"]
	assert soft_wrap("", 40) == [""]
	assert soft_wrap("  {", 40) == ["  {"]


def test_a_pathologically_narrow_pane_still_terminates():
	"""The continuation indent is clamped so a deeply indented line
	cannot consume the whole pane and stall."""
	line = " " * 20 + "value " + "w" * 40
	out = soft_wrap(line, 10)
	assert out and all(len(part) <= 10 for part in out)
	assert len(out) < 200, "the wrap did not make progress"


# -- the reader on a real terminal ------------------------------------------

class Screen:
	def __init__(self, columns=110):
		self.rows = {}
		self.columns = columns

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]

	def lines(self):
		return [self.rows[key] for key in sorted(self.rows)]


def _painted(world, entry, cell_width=70, rows=40, skip=0):
	console = _console(world)
	console.event_skip = skip
	screen = Screen()
	console._paint_event_reader(screen, 0, rows, 0, cell_width, entry)
	return console, screen.lines()


def test_the_reader_paints_the_structure(world):
	payload = {"outer": {"inner": ["a", "b"]}}
	_console_, painted = _painted(world, _entry(payload))
	assert "  payload:" in painted
	assert "  {" in painted
	assert '    "outer": {' in painted
	assert '      "inner": [' in painted


def test_a_narrow_pane_keeps_depth_and_discloses_the_tail(world):
	payload = {"outer": {"inner": {"leaf": "y" * 120}}}
	entry = _entry(payload)
	# tall enough to reach the leaf: the depth claim is about the
	# CONTINUATIONS, not about clipping.
	_deep_console, painted = _painted(world, entry, cell_width=28, rows=40)
	deep = [line for line in painted if line.strip().startswith("y")]
	assert deep, painted
	for line in deep:
		leading = len(line) - len(line.lstrip(" "))
		assert leading == 10, \
			f"a continuation lost its nesting depth: {line!r}"
	# and a pane too short for the block discloses the clipped tail
	short_console, _short = _painted(world, entry, cell_width=28, rows=6)
	assert short_console.event_clipped is True, \
		"a payload longer than the pane was not disclosed as clipped"


def test_scrolling_reveals_the_rest_and_marks_the_continuation(world):
	payload = {"k%d" % index: "v" * 20 for index in range(30)}
	first_console, first = _painted(world, _entry(payload), rows=8)
	assert first_console.event_clipped is True
	later_console, later = _painted(world, _entry(payload), rows=8, skip=12)
	assert any("(cont.)" in line for line in later), later
	assert first != later, "scrolling painted the same rows"


def test_a_resize_repaints_from_the_same_logical_lines(world):
	"""Wrapping is derived from the logical lines each paint, so a
	narrow render never truncates state a wider one needs."""
	payload = {"outer": {"inner": {"leaf": "z" * 90}}}
	entry = _entry(payload)
	_narrow_console, narrow = _painted(world, entry, cell_width=26, rows=40)
	_wide_console, wide = _painted(world, entry, cell_width=100, rows=40)
	def content(lines):
		return "".join(line.strip() for line in lines)
	assert "z" * 90 in content(wide), "the wide render lost the value"
	assert content(narrow).count("z") == content(wide).count("z"), \
		"the narrow render dropped payload characters"


def test_an_empty_reader_is_unchanged(world):
	console = _console(world)
	screen = Screen()
	console._paint_event_reader(screen, 0, 10, 0, 70, None)
	assert screen.lines() == ["(no event selected)"]
	assert console.event_clipped is False


def test_the_common_labels_still_precede_the_payload(world):
	"""'The common typed labels above the payload remain concise' — they
	are unchanged and still come first."""
	payload = {"rationale": "because", "from": "queued", "to": "block",
	           "work": "W2"}
	lines = _console(world)._event_lines(_entry(payload))
	label_rows = [line for line in lines[:lines.index("  payload:")]]
	assert "  rationale: because" in label_rows
	assert "  from: queued" in label_rows and "  to: block" in label_rows
	# and the same facts are still in the payload block below, whole
	assert _reassemble(lines) == payload


def test_references_and_related_survive(world):
	entry = _entry({"work": "W2"},
	               related=[{"work": "W9", "role": "blocker"}],
	               references=[{"root": "baton", "path": "docs/x.md"}])
	lines = _console(world)._event_lines(entry)
	assert "  related: W9 (blocker)" in lines
	assert "  ref: baton:docs/x.md" in lines


def test_painting_writes_nothing_to_the_authority(world):
	"""'Reading, wrapping, scrolling, and resizing write nothing.'"""
	store = world["store"]
	work = tr.create_work(store, team="lang", kind="bug", title="t",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="b")["work_id"]
	entry = pj.work_events(store, work)["events"][-1]
	before = store.last_seq()
	for width in (24, 40, 70, 120):
		for skip in (0, 3, 9):
			_painted(world, entry, cell_width=width, rows=6, skip=skip)
	assert store.last_seq() == before, "painting mutated the authority"


# -- the wrap is lossless, as a property ------------------------------------

def _continuation_width(line, cell_width):
	"""The continuation indent `soft_wrap` uses: the line's OWN leading
	run plus two, clamped so a pane narrower than that still makes
	progress.

	Stated here rather than measured from the output, because a fragment
	whose content begins with spaces is indistinguishable from indent —
	measuring it is how a check of this property quietly starts passing
	for the wrong reason."""
	cell = max(8, cell_width)
	indent = len(line) - len(line.lstrip(" "))
	return min(indent + 2, max(0, cell - 1))


@pytest.mark.parametrize("line", [
	'  "value": "alpha   beta gamma delta"',
	'      "trailing": "ends with a space "',
	'    "leading": "   starts with spaces"',
	'        "only": "     "',
	'  "mixed": "a  b   c    d     e"',
	'          "deep": "one two three four five six seven"',
	'  "escaped": "quote \\" backslash \\\\ newline \\n tab \\t"',
	'  "unicode": "naïve ça 日本語 ✅ é"',
	'  "unbroken": "' + "q" * 80 + '"',
	'  "runs": "' + " " * 12 + 'after a long run"',
])
@pytest.mark.parametrize("width", [8, 9, 12, 16, 20, 24, 31, 40, 64])
def test_the_wrap_reassembles_byte_for_byte(line, width):
	"""The property the review pinned: every source character survives,
	and the ONLY thing the wrapper adds is the continuation prefix.

	Checked across the shapes that break naive wrappers — repeated
	spaces at a break, leading and trailing spaces inside a string,
	all-space values, escapes, Unicode, and a token with no space at
	all."""
	out = soft_wrap(line, width)
	cell = max(8, width)
	assert all(len(part) <= cell for part in out), \
		[len(part) for part in out]
	cont = _continuation_width(line, width)
	rebuilt = out[0] + "".join(part[cont:] for part in out[1:])
	assert rebuilt == line, \
		f"the wrap altered the line at width {width}: {out!r}"


def test_the_wrap_is_lossless_across_a_broad_sweep():
	"""The same property over a deterministic sweep of awkward inputs.

	Not a random fuzz: a fixed generator, so a failure is reproducible
	and the test cannot pass or fail differently between runs. It exists
	because the review's single case and my hand-written ones are the
	shapes I thought to try, and this defect had already survived one
	round of tests I wrote myself."""
	pieces = ("a", " ", "  ", '"', "\\", "é", "x", ":", ",")
	failures = []
	for seed in range(600):
		body = "".join(pieces[(seed * 7 + index * 11) % len(pieces)]
		               for index in range(1 + seed % 40))
		line = " " * (2 * (seed % 6)) + body
		for width in (8, 11, 14, 19, 26, 33, 44):
			out = soft_wrap(line, width)
			cell = max(8, width)
			if any(len(part) > cell for part in out):
				failures.append(("overflows the cell", line, width, out))
				continue
			cont = _continuation_width(line, width)
			rebuilt = out[0] + "".join(part[cont:] for part in out[1:])
			if rebuilt != line:
				failures.append(("altered the line", line, width, out))
	assert not failures, \
		f"{len(failures)} of 4200 wraps were lossy; first: {failures[0]!r}"
