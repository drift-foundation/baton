"""W8 formatting under the W14 index/reader layout.

Each message still renders as a compact borderless block — metadata
header (#seq author ts) with the personal new marker, wrapped indented
body, references under a separate Refs section — but the block now
paints in the READER for exactly ONE selected message, chosen in the
compact Message index (`M<seq>` labels over the existing stable
sequence). Wide terminals split index|reader; narrow terminals stack
them — never a merged flat stream. Explicit `s` advances the thread
cursor through the SELECTED message and no later one.
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
	document["roots"] = {"pushcoin": {"display": "PushCoin", "base": "/srv/checkouts/pushcoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="format target", origin="external-report", classification="suspected-defect",
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


def test_the_reader_renders_the_block_with_metadata_and_references(world):
	"""The selected message paints as the SAME canonical block: header
	with seq/author/ts, indented wrapped body, each reference on its own
	line under Refs (narrow stack, so the block starts at column 0)."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		(b"\x17j", 0.4),              # Ctrl-W j: the Message index
		(b"j", 0.5),                  # select the LONG message (last)
		(b"qy", 0.4),
	], columns=44, lines=24)
	screen = ptyharness.replay(steps[2], columns=44, lines=24)
	header = next((line for line in screen
	               if re.match(r"^#3 lang\.ada \d{4}-\d{2}-\d{2}", line)),
	              None)
	assert header is not None, \
		f"no metadata header with a timestamp: {screen[:12]}"
	assert "  Refs:" in screen, "the Refs section heading is missing"
	rebuilt_ref = "".join(
		line.strip() for line in screen
		if line.startswith("    "))
	assert "[pushcoin:docs/evidence.md]" in rebuilt_ref, \
		"the reference does not render whole under Refs"
	body = " ".join(line.strip() for line in screen
	                if line.startswith("  ")
	                and not line.startswith(("    ", "  Refs:")))
	assert LONG_BODY in body, "wrapping lost body text"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_index_shows_stable_seqs_and_the_personal_new_state(world):
	"""The index labels rows `M<seq>` over the EXISTING stable message
	sequence with the viewer's personal new/seen state; the new-first
	autoselect opens the first personal-new message — and ONLY the
	selected body paints (the flat stream is gone)."""
	store = bw.Authority(world["database"])
	opener_seq = world["born"]["seq"]
	tr.seen_thread(store, world["born"]["thread"], team="lang",
	               member="grace", up_to_seq=opener_seq)
	store.close()
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"\r", 0.6),
		(b"qy", 0.4),
	])
	screen = ptyharness.replay(steps[0])
	flat = "\n".join(screen)
	opener_row = next(line for line in screen
	                  if line.startswith(f"M{opener_seq} "))
	later_row = next(line for line in screen if line.startswith("M3 "))
	assert " seen" in opener_row, "the seen opener is not marked seen"
	assert " new" in later_row, "the unseen message lost its new state"
	# the autoselected reader shows the personal-new message, with the
	# personal marker on its metadata header
	assert "#3 lang.ada" in flat and "• new" in flat
	assert "short opener" not in flat, \
		"the unselected body painted — the flat stream came back"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_new_first_autoselect_reaches_a_later_message_page(tmp_path):
	"""W14's new-first promise is Thread-wide, not first-page-only.
	When every message on page one is seen and the first unseen message is
	on a later bounded page, opening details must page to and select that
	message rather than opening an old seen body."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="paged new", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="message 0")
	seqs = [born["seq"]]
	for index in range(1, 10):
		posted = tr.post_thread(store, born["thread"],
		                        author_team="lang", author="ada",
		                        body=f"message {index}")
		seqs.append(posted["seq"])
	# At 14 rows the first index page is bounded below this cursor; the
	# first personal-new Message therefore lives on a later page.
	tr.seen_thread(store, born["thread"], team="lang", member="grace",
	               up_to_seq=seqs[5])
	first_new = seqs[6]
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.grace", [
		(b"\r", 0.8),
		(b"qy", 0.4),
	], columns=44, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	opened = "\n".join(ptyharness.replay(steps[0], columns=44, lines=14))
	assert f"M{first_new} " in opened and f"#{first_new} lang.ada" in opened, \
		("opening the Thread did not seek to its first personal-new "
		 f"Message M{first_new}: {opened}")


def test_all_seen_autoselect_opens_the_thread_newest_message(tmp_path):
	"""When no personal-new Message exists anywhere in the Thread, the
	ruled fallback is its newest Message — not the oldest Message on the
	first bounded page."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="all seen", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="message 0")
	seqs = [born["seq"]]
	for index in range(1, 10):
		posted = tr.post_thread(store, born["thread"],
		                        author_team="lang", author="ada",
		                        body=f"message {index}")
		seqs.append(posted["seq"])
	tr.seen_thread(store, born["thread"], team="lang", member="grace",
	               up_to_seq=seqs[-1])
	newest = seqs[-1]
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.grace", [
		(b"\r", 0.8),
		(b"qy", 0.4),
	], columns=44, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	opened = "\n".join(ptyharness.replay(steps[0], columns=44, lines=14))
	assert f"M{newest} " in opened and f"#{newest} lang.ada" in opened, \
		("an all-seen Thread reopened its oldest page instead of newest "
		 f"Message M{newest}: {opened}")


def test_seen_advances_through_the_selected_message_and_no_later(world):
	"""W14 seen semantics: `s` moves the per-participant cursor through
	the SELECTED message exactly — a later unseen message stays New
	until it is itself selected and marked."""
	store = bw.Authority(world["database"])
	assert pj.thread(store, world["born"]["thread"], viewer_team="lang",
	                 viewer_member="grace")["new"] == 2
	store.close()
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"\r", 0.6),
		(b"\x17j", 0.4),              # the index
		(b"k", 0.4),                  # up to the OPENER (M2)
		(b"s", 0.5),                  # seen through M2 only
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	marked = "\n".join(ptyharness.replay(steps[3]))
	assert "seen through M2" in marked, marked[-300:]
	store = bw.Authority(world["database"])
	view = pj.thread(store, world["born"]["thread"], viewer_team="lang",
	                 viewer_member="grace")
	store.close()
	assert view["new"] == 1, \
		"s did not stop at the selected message"
	# selecting the later message and marking clears the rest
	text, status, steps = ptyharness.drive(world["config"], "lang.grace", [
		(b"\r", 0.6), (b"\x17j", 0.4), (b"j", 0.4), (b"s", 0.5),
		(b"qy", 0.4),
	])
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	store = bw.Authority(world["database"])
	remaining = pj.thread(store, world["born"]["thread"],
	                      viewer_team="lang",
	                      viewer_member="grace")["new"]
	store.close()
	assert remaining == 0


def test_the_reader_scrolls_an_oversized_message(tmp_path):
	"""A body taller than the reader is not a dead-end: `j` scrolls the
	block line by line with an honest `M<seq> (cont.)` tag, the whole
	tail is reachable, and nothing is merged with other messages."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	sentence = " ".join(f"giant-line-{index:02d}" for index in range(60))
	tr.create_work(store, team="lang", kind="bug",
	               title="oversized", origin="external-report", classification="suspected-defect",
	               author="ada", body=sentence)
	store.close()
	text, status, steps = ptyharness.drive(config_path, "lang.grace", [
		(b"\r", 0.8),                              # reader page one
		(b"\x17j\x17j", 0.5),                      # focus the reader
		(b"j" * 40, 1.2),                          # scroll to the tail
		(b"qy", 0.4),
	], columns=44, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	first = "\n".join(ptyharness.replay(steps[0], columns=44, lines=14))
	assert "giant-line-00" in first
	assert "giant-line-59" not in first, "the viewport fit everything"
	assert "reader: j scrolls" in first, \
		"a clipped reader did not disclose its scroll control"
	tail = "\n".join(ptyharness.replay(steps[2], columns=44, lines=14))
	assert "(cont.)" in tail, "the continuation lost its message tag"
	assert "giant-line-59" in tail, "the body tail is unreachable"
	assert "giant-line-00" not in tail, "scrolling did not advance"


def test_the_index_pages_are_bounded_with_next(tmp_path):
	"""Bounded paging survives the redesign: a thread longer than one
	index page discloses `(n: more)`; `n` advances the window to later
	seqs and `p` returns to the first page."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	born = tr.create_work(store, team="lang", kind="bug", title="paged",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="opener")
	for index in range(30):
		tr.post_thread(store, born["thread"], author_team="lang",
		               author="ada", body=f"entry {index:02d}")
	store.close()
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.7),
		(b"\x17j", 0.4),              # the index
		(b"n", 0.6),                  # the next bounded page
		(b"p", 0.6),                  # back to the first page
		(b"qy", 0.4),
	], columns=44, lines=14)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	first = ptyharness.replay(steps[1], columns=44, lines=14)
	assert any("(n: more)" in line for line in first), first[:6]
	assert any(line.startswith("M2 ") for line in first)
	paged = ptyharness.replay(steps[2], columns=44, lines=14)
	assert not any(line.startswith("M2 ") for line in paged), \
		"n did not advance the index window"
	assert any(re.match(r"^M\d+ ", line) for line in paged)
	back = ptyharness.replay(steps[3], columns=44, lines=14)
	assert any(line.startswith("M2 ") for line in back), \
		"p did not return to the first page"


def test_the_narrow_stack_keeps_two_regions_never_a_flat_stream(world):
	"""Narrow fallback: the SAME two regions stack — index above,
	reader below. Exactly one metadata header paints (one selected
	body), while the index still lists every page row."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		(b"qy", 0.4),
	], columns=44, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0], columns=44, lines=24)
	index_rows = [line for line in screen if re.match(r"^M\d+ ", line)]
	assert len(index_rows) == 2, screen
	headers = [line for line in screen
	           if re.match(r"^#\d+ lang\.", line)]
	assert len(headers) == 1, \
		f"narrow width merged bodies back into a stream: {headers}"


def test_the_wide_split_puts_the_index_left_of_the_reader(world):
	"""At usable width the index column sits left, the reader right of
	it — on the SAME rows, not stacked."""
	text, status, steps = ptyharness.drive(world["config"], "lang.ada", [
		(b"\r", 0.6),
		(b"qy", 0.4),
	], columns=110, lines=32)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[0])
	paired = [line for line in screen
	          if re.match(r"^M\d+ ", line) and len(line) > 36
	          and line[36:].strip()]
	assert paired, \
		"no row carries index (left) and reader (right) together"
	header = next(line for line in screen if "#2 lang.ada" in line
	              or "#3 lang.ada" in line)
	assert header.index("#") >= 36, \
		f"the reader did not start right of the index: {header!r}"


def test_selection_is_stable_and_the_scroll_is_width_bound(tmp_path):
	"""The selection is keyed by the STABLE seq: it survives a repaint
	and a resize while the message remains present. The reader scroll
	is a line cursor into ONE wrapping — a different width resets it,
	so content can repeat but never be omitted."""
	from baton_work.tui.app import Console
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	sentence = " ".join(f"pane-word-{index:02d}" for index in range(40))
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="pane target", origin="external-report", classification="suspected-defect",
	                      author="ada", body=sentence)
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="the follow-up")

	class Screen:
		def addnstr(self, *_args):
			pass

	console = Console(store, "lang", "ada")
	rows = console.rows()
	console.detail_work = rows[0]["id"]
	console.disc_cursor = None
	console.mode = "detail"
	console._render_detail(Screen(), 14, 44)
	chosen = console.msg_cursor
	assert chosen is not None
	# a repaint at the same width keeps the selection
	console._render_detail(Screen(), 14, 44)
	assert console.msg_cursor == chosen, "a repaint moved the selection"
	# scroll the (clipped) reader, then resize: the width-bound scroll
	# resets, the seq-bound selection survives
	console.focus = "reader"
	assert console.reader_clipped, "the narrow reader fit everything"
	console.handle(ord("j"))
	console.handle(ord("j"))
	assert console.reader_skip == 2
	console._render_detail(Screen(), 14, 100)
	assert console.reader_skip == 0, \
		"a width-bound scroll survived into a different wrapping"
	assert console.msg_cursor == chosen, "the resize moved the selection"
	store.close()


def test_a_long_reference_wraps_and_loses_nothing(tmp_path):
	"""A reference longer than a narrow reader wraps with a deeper
	indent; the full canonical value is reconstructable from the
	screen."""
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	document["roots"] = {"pushcoin": {"display": "PushCoin", "base": "/srv/checkouts/pushcoin"}}
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc_init(config_path)
	store = bw.Authority(result["database"])
	long_path = ("docs/evidence/very/deep/directory/holding/the/"
	             "reproduction/trace-2026-08-16-with-a-long-name.md")
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="long ref", origin="external-report", classification="suspected-defect",
	                      author="ada", body="see the trace",
	                      binding=None)
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="attached",
	               refs=[f"pushcoin:{long_path}"])
	store.close()

	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.6),
		(b"\x17j", 0.4),              # the index
		(b"j", 0.5),                  # the reference-carrying message
		(b"qy", 0.4),
	], columns=44, lines=20)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
	screen = ptyharness.replay(steps[2], columns=44, lines=20)
	rebuilt = "".join(line.strip() for line in screen
	                  if line.startswith("    "))
	assert f"[pushcoin:{long_path}]" in rebuilt, \
		f"the wrapped reference lost its tail: {screen}"
