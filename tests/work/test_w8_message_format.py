"""W8: readable formatted Thread messages (same-schema iteration).

Each message renders as a compact borderless block: a metadata header
(#seq author ts) carrying the viewer's personal new marker, the body
wrapped to the pane width under an indent, and each reference on its own
line. Formatting is presentation only — canonical projection, pagination,
and explicit page-bounded seen semantics unchanged; a clipped block never
counts as seen.
"""

from __future__ import annotations

import json as _json
import os
import pty as _pty
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui import app                                # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")

LONG_BODY = ("the parser dies on any nested escape sequence longer than "
             "four bytes and the crash reproduces on every consumer "
             "checkout we tried this week")


@pytest.fixture()
def world(tmp_path):
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="format target", origin="external-report",
	                      author="ada", body="short opener")
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body=LONG_BODY,
	               refs=["pushcoin:docs/evidence.md"])
	cast = {"config": config_path, "born": born,
	        "database": result["database"]}
	store.close()
	return cast


def lc_init(config_path):
	from baton_work import lifecycle as lc
	return lc.init_from_config(config_path, participant="lang.ada")


def test_messages_render_as_blocks_with_metadata_and_references(world):
	"""Header with seq/author/ts, indented wrapped body, reference on
	its own line — in the focused Msgs view."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5),
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[2])
	flat = "\n".join(screen)
	header = next((line for line in screen
	               if re.match(r"^#3 lang\.ada \d{4}-\d{2}-\d{2}", line)),
	              None)
	assert header is not None, \
		f"no metadata header with a timestamp: {screen[:8]}"
	assert "  [pushcoin:docs/evidence.md]" in screen, \
		"the reference does not render on its own readable line"
	# The wrapped body: indented continuation lines, nothing clipped.
	body_lines = [line for line in screen
	              if line.startswith("  ") and "nested escape" in line
	              or line.startswith("  ") and "checkout we tried" in line]
	assert len(body_lines) >= 2, "the long body did not wrap"
	rebuilt = " ".join(line.strip() for line in screen
	                   if line.startswith("  ")
	                   and not line.startswith("  ["))
	assert LONG_BODY in rebuilt, "wrapping lost body text"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_new_marker_is_personal_and_from_the_projection(world):
	"""grace has seen the opener only: the later message carries the
	new marker, the opener does not — exactly the projection's
	per-message fact."""
	store = bw.Authority(world["database"])
	opener_seq = world["born"]["seq"]
	tr.seen_thread(store, world["born"]["thread"], team="lang",
	               member="grace", up_to_seq=opener_seq)
	view = pj.thread(store, world["born"]["thread"], viewer_team="lang",
	                 viewer_member="grace")
	flags = {m["seq"]: m["new"] for m in view["messages"]}
	store.close()
	assert flags[opener_seq] is False and any(flags.values())

	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5),
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[2])
	opener = next(line for line in screen
	              if line.startswith(f"#{opener_seq} "))
	later = next(line for line in screen if line.startswith("#3 "))
	assert "• new" not in opener, "a seen message carries the new marker"
	assert "• new" in later, "an unseen message lost its new marker"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_clipped_block_never_counts_as_seen(world):
	"""The page-bounded seen bound is the last message painted IN FULL:
	with a viewport too short for the second (wrapped) block, s marks
	only the opener — the long message stays New."""
	store = bw.Authority(world["database"])
	before = pj.thread(store, world["born"]["thread"], viewer_team="lang",
	                   viewer_member="grace")["new"]
	assert before == 2
	store.close()
	# lines=9: msgs budget = 6 lines; opener block (2) fits, the long
	# wrapped block does not fit in the remainder at width 40.
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5),
		(b"s", 0.5),
		(b"q", 0.4),
	], columns=40, lines=9)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	store = bw.Authority(world["database"])
	view = pj.thread(store, world["born"]["thread"], viewer_team="lang",
	                 viewer_member="grace")
	store.close()
	assert view["new"] == 1, \
		"a clipped block was counted as seen (or nothing was marked)"


def test_the_split_preview_uses_the_same_blocks(world):
	"""The bottom pane paints the SAME formatted blocks — metadata
	header, indented body, reference line."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"", 0.5),
		(b"q", 0.4),
	])
	screen = ptyharness.replay(steps[0])
	flat = "\n".join(screen)
	assert re.search(r"^#2 lang\.ada \d{4}-\d{2}-\d{2}", flat,
	                 re.M), "the preview lost the metadata header"
	assert "  short opener" in screen, \
		"the preview body is not an indented block"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_an_oversized_message_is_readable_via_continuation(tmp_path):
	"""R1: a FIRST message taller than the viewport is not a dead-end —
	n continues through its body page by page, the (cont.) header names
	the same message, and s counts it only once its final line has
	painted."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	sentence = " ".join(f"giant-line-{index:02d}" for index in range(60))
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="oversized", origin="external-report",
	                      author="ada", body=sentence)
	store.close()

	# lines=9, width=40: the wrapped block is far taller than the page.
	text, status, steps = ptyharness.drive(config_path, "lang.grace", [
		(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5),   # page one of the body
		(b"s", 0.5),                               # must NOT count it
		(b"n", 0.5),                               # continue the body
		(b"q", 0.4),
	], columns=40, lines=9)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	first = "\n".join(ptyharness.replay(steps[2], columns=40, lines=9))
	assert "giant-line-00" in first
	assert "giant-line-59" not in first, "the viewport fit everything"
	continued = "\n".join(ptyharness.replay(steps[4], columns=40,
	                                        lines=9))
	assert "(cont.)" in continued, "the continuation lost its header"
	assert "giant-line-00" not in continued, "n did not advance the body"
	store = bw.Authority(result["database"])
	still_new = pj.thread(store, born["thread"], viewer_team="lang",
	                      viewer_member="grace")["new"]
	store.close()
	assert still_new == 1, \
		"s counted a message whose final line never painted"

	# Walk to the end: the 31-line block (whole-token wrapping: two
	# words per 37-cell line) pages 6+5+5+5+5+5 — five continuations
	# land the tail, where s may finally count the message.
	script = [(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5)]
	script += [(b"n", 0.4)] * 5
	script += [(b"s", 0.5), (b"q", 0.4)]
	text, status, steps = ptyharness.drive(config_path, "lang.grace",
	                                       script, columns=40, lines=9)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	tail = "\n".join(ptyharness.replay(steps[-2], columns=40, lines=9))
	assert "giant-line-59" in tail, "the body tail is unreachable"
	store = bw.Authority(result["database"])
	remaining = pj.thread(store, born["thread"], viewer_team="lang",
	                      viewer_member="grace")["new"]
	store.close()
	assert remaining == 0, \
		"the fully displayed message could not be marked seen"


def test_the_preview_seen_bound_excludes_the_status_row(tmp_path):
	"""R2: the bottom terminal row belongs to the command/status line.
	The preview budget stops above it — an oversized block fills the
	pane to the LAST PREVIEW row and never paints the reserved row,
	so s cannot count a line the final composition replaced."""
	from baton_work.tui.app import MIN_SPLIT_HEIGHT
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	tall = " ".join(f"boundary-word-{index:02d}" for index in range(40))
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="boundary", origin="external-report",
	                      author="ada", body=tall)
	store.close()

	lines = MIN_SPLIT_HEIGHT
	text, status, steps = ptyharness.drive(config_path, "lang.grace", [
		(b"", 0.6),
		(b"\t", 0.4),
		(b"s", 0.5),
		(b"q", 0.4),
	], columns=40, lines=lines)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	before = ptyharness.replay(steps[0], columns=40, lines=lines)
	assert any("boundary-word" in line for line in before), \
		"the oversized block did not paint at all"
	assert before[lines - 1] == "", \
		f"a preview line reached the reserved status row: " \
		f"{before[lines - 1]!r}"
	store = bw.Authority(result["database"])
	still_new = pj.thread(store, born["thread"], viewer_team="lang",
	                      viewer_member="grace")["new"]
	store.close()
	assert still_new == 1, \
		"s counted a block the status row composition clipped"


def test_a_long_reference_wraps_and_loses_nothing(tmp_path):
	"""R3: a reference longer than a narrow pane wraps with a deeper
	indent; the full canonical value is reconstructable from the
	screen."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	long_path = ("docs/evidence/very/deep/directory/holding/the/"
	             "reproduction/trace-2026-08-16-with-a-long-name.md")
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="long ref", origin="external-report",
	                      author="ada", body="see the trace",
	                      binding=None)
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="attached",
	               refs=[f"pushcoin:{long_path}"])
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.5), (b"o", 0.5), (b"\r", 0.5),
		(b"q", 0.4),
	], columns=40, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[2], columns=40, lines=14)
	rebuilt = "".join(
		line.strip() for line in screen
		if line.strip().startswith("[pushcoin") or
		(line.startswith("  ") and not line.strip().startswith("#") and
		 ("/" in line or line.strip().endswith("]"))))
	assert f"[pushcoin:{long_path}]" in rebuilt.replace("attached", ""), \
		f"the wrapped reference lost its tail: {screen}"


def test_continuation_survives_a_terminal_resize(tmp_path):
	"""R4: the skip cursor is bound to the width it was computed at.
	After a resize the continuation resets (repetition is acceptable),
	content is never omitted, and s stays unavailable until the actual
	tail has been shown at the NEW width — in the focused Msgs view."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	sentence = " ".join(f"resize-word-{index:02d}" for index in range(40))
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="resize target", origin="external-report",
	                      author="ada", body=sentence)
	store.close()

	# Narrow start, one continuation, then a WIDER resize to 60
	# columns (the block still overflows the page), an immediate s
	# (must be inert: the re-wrapped block restarts and is not fully
	# painted), then the tail and the real mark.
	script = [
		(b"\r", 0.7), (b"o", 0.7), (b"\r", 0.7),   # page one at 44 cols
		(b"n", 0.6),                               # continuation at 44
		("resize", (60, 12), 0.9),                 # rewrap at 60 cols
		(b"s", 0.6),                               # premature: inert
		(b"n", 0.6),                               # the tail at 60
		(b"s", 0.6),                               # the real mark
		(b"q", 0.5),
	]
	text, status, steps = ptyharness.drive(
		config_path, "lang.grace", script, columns=44, lines=12,
		dynamic_size=True, settle=1.2)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

	first = "\n".join(ptyharness.replay(steps[2], columns=44, lines=12))
	assert "resize-word-00" in first, first[:400]
	assert "resize-word-39" not in first, "the narrow viewport fit all"

	# After the resize the pages at 60 columns must jointly cover the
	# WHOLE body (reset-and-repeat, no omission)...
	wide = "\n".join(
		"\n".join(ptyharness.replay(step, columns=60, lines=12))
		for step in steps[4:7])
	for index in range(40):
		assert f"resize-word-{index:02d}" in wide, \
			f"resize omitted word {index:02d}"

	# ...the premature s marked nothing (no confirmation painted, and
	# the block restarts unfinished at the new width)...
	premature = "\n".join(ptyharness.replay(steps[5], columns=60,
	                                        lines=12))
	assert "seen up to" not in premature, \
		"s counted a block the resize re-wrapped mid-continuation"
	# ...and the final s cleared the message after the tail painted.
	final = "\n".join(ptyharness.replay(steps[7], columns=60,
	                                     lines=12))
	assert "seen up to" in final, final[:400]
	store = bw.Authority(result["database"])
	remaining = pj.thread(store, born["thread"], viewer_team="lang",
	                      viewer_member="grace")["new"]
	store.close()
	assert remaining == 0, \
		"the message could not be marked after the full walk"


def test_the_preview_skip_resets_when_the_width_changes(tmp_path):
	"""R4, the shared preview path: a stub-screen check that a skip
	advanced at one width resets on the next paint at another — the
	painter never sees a cursor from a different wrapping."""
	from baton_work.tui.app import Console
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	sentence = " ".join(f"pane-word-{index:02d}" for index in range(40))
	tr.create_work(store, team="lang", kind="bug", title="pane target",
	               origin="external-report", author="ada", body=sentence)

	class Screen:
		def addnstr(self, *_args):
			pass

	console = Console(store, "lang", "ada")
	console.render_probe = None
	console._render_table(Screen(), 8, 44, console.rows())
	console._render_preview(Screen(), 8, 6, 44, console.rows())
	assert console.preview_next_skip, "the narrow pane fit everything"
	console.focus = "msgs"
	console.split_active = True
	console.handle(ord("n"))
	assert console.preview_skip > 0
	# The next paint arrives at a DIFFERENT width: the skip must reset
	# before the painter applies it.
	console._render_preview(Screen(), 8, 6, 100, console.rows())
	assert console.preview_skip == 0, \
		"a width-bound skip survived into a different wrapping"
	store.close()
