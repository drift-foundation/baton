"""W30: the Message reader has no heading of its own.

The wide split painted `Message M20` on its own row while the reversed
index row already showed the selection and the metadata directly beneath
already said `#20`. Three statements of one fact, one of them costing a
body line.

The reader now starts with its canonical metadata in that row. Focus
rides the metadata, marked in the same `»` column the index heading uses
— bold alone would not do, because unseen metadata is already bold.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(__import__("pty"), "fork"),
                                reason="no pty support")


def _world(tmp_path, messages=3, body="the body", team=None, member=None):
	teams = {"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}}
	if member:
		teams[team] = {"members": {member: ["dev"]}, "kinds": ["bug"]}
	config_path, database = fx.build_instance(str(tmp_path), teams)
	with bw.Authority(database) as store:
		born = tr.create_work(store, team="lang", kind="bug",
		                      title="w", origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="the opener")
		for index in range(messages - 1):
			tr.post_thread(store, born["thread"], author_team="lang",
			               author="ada", body=f"{body} {index}")
	return config_path


def _screens(config_path, script, columns=110, lines=24):
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada", list(script) + [(b"qy", 0.4)],
		columns=columns, lines=lines)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
	return [ptyharness.replay(step, columns=columns, lines=lines)
	        for step in steps]


# -- the heading is gone ---------------------------------------------------

@pytest.mark.serial
@pytest.mark.parametrize("columns", [110, 60])
def test_no_reader_heading_at_any_width(tmp_path, columns):
	"""Wide split and narrow stack alike."""
	config_path = _world(tmp_path)
	rows = _screens(config_path, [(b"\r", 0.7)], columns=columns)[0]
	flat = "\n".join(rows)
	assert "Messages (" in flat, flat[:400]
	assert "Message M" not in flat, \
		f"the reader heading survived at {columns} columns"


@pytest.mark.serial
def test_the_metadata_sits_on_the_row_the_heading_used(tmp_path):
	"""Wide: the Message-index heading and the reader's first metadata
	line share one row."""
	config_path = _world(tmp_path)
	rows = _screens(config_path, [(b"\r", 0.7)])[0]
	heading = next(line for line in rows if "Messages (" in line)
	assert "#" in heading, \
		f"the reader metadata is not on the index heading row: {heading!r}"
	assert "lang.ada" in heading


@pytest.mark.serial
@pytest.mark.parametrize("columns,lines", [(110, 24), (110, 14),
                                           (60, 24), (60, 14)])
def test_the_reader_fills_the_row_the_heading_occupied(tmp_path, columns,
                                                       lines):
	"""The point of the change: one more line of CONTENT. Pinned by
	geometry rather than by a sample line, so it survives a fixture
	edit — with a body longer than the pane, the reader paints every
	row from the shared heading row through the last row above the
	footer, and its body lines number one less than that span (the
	metadata row).

	Give the row back to a label and the bottom reader row goes blank,
	which is exactly what this asserts against."""
	config_path = _world(tmp_path, messages=1)
	with bw.Authority(os.path.join(os.path.dirname(config_path),
	                               "work.sqlite3")) as store:
		thread = store.conn.execute(
			"SELECT thread FROM thread_labels LIMIT 1").fetchone()[0]
		tr.post_thread(store, thread, author_team="lang", author="ada",
		               body="\n".join(f"line {n}" for n in range(80)))
	rows = _screens(config_path, [(b"\r", 0.8)], columns=columns,
	                lines=lines)[0]
	from baton_work.tui.app import Console
	# wide: the reader is the right-hand cell and starts on the shared
	# row. narrow: it is the full width, stacked directly under the
	# index with no label row between them.
	wide = columns - 1 - Console.INDEX_WIDTH - 2 >= Console.MIN_READER
	reader_x = Console.INDEX_WIDTH + 2 if wide else 0
	start = next(index for index, line in enumerate(rows)
	             if line[reader_x:].strip().lstrip("»").startswith("#"))
	if wide:
		assert "Messages (" in rows[start], \
			"the wide reader did not start on the shared heading row"
	else:
		# no label row survives between the index and the reader: every
		# row from the heading down to the reader carries index content.
		heading = next(index for index, line in enumerate(rows)
		               if "Messages (" in line)
		between = [rows[index] for index in range(heading + 1, start)]
		assert between and all(line.strip() for line in between), \
			f"a blank or label row sits between index and reader: {between!r}"
	footer = lines - 2
	painted = [index for index in range(start, footer)
	           if rows[index][reader_x:].strip()]
	assert painted == list(range(start, footer)), \
		f"the reader left rows {sorted(set(range(start, footer)) - set(painted))} " \
		f"blank; it should reach the footer at {footer}"
	bodies = [rows[index][reader_x:].strip()
	          for index in range(start + 1, footer)]
	assert all(text.startswith("line ") for text in bodies), bodies
	assert len(bodies) == footer - start - 1
	# and the clipped tail is disclosed rather than dropped
	assert "reader: j scrolls" in "\n".join(rows), rows[footer]


# -- focus ------------------------------------------------------------------

@pytest.mark.serial
def test_focus_moves_onto_the_metadata_row(tmp_path):
	"""Ctrl-W j walks Threads -> index -> reader. The reader marker has
	to move with it, because the row it used to live on is gone.

	Both markers now share one row, so they are distinguished by
	COLUMN: the index owns column 0, the reader owns the column before
	its metadata."""
	config_path = _world(tmp_path)
	# W2597: entry now lands in the INDEX, so the walk starts by going
	# up to the Threads list; the three focus states this test compares
	# are the same three, reached in the same order.
	steps = _screens(config_path, [(b"\r\x17k", 0.7), (b"\x17j", 0.5),
	                               (b"\x17j", 0.6)])
	shared = [next(line for line in rows if "Messages (" in line)
	          for rows in steps]
	assert shared[0].startswith(" ") and "»" not in shared[0], \
		f"the Threads list has focus but a Message pane is marked: {shared[0]!r}"
	assert shared[1].startswith("»Messages ("), \
		f"the index has focus and no marker: {shared[1]!r}"
	assert "»#" not in shared[1], \
		f"the index has focus and the reader is marked too: {shared[1]!r}"
	assert shared[2].startswith(" Messages ("), \
		f"the reader has focus and the index kept its marker: {shared[2]!r}"
	assert "»#" in shared[2], \
		f"the reader has focus and no marker: {shared[2]!r}"


@pytest.mark.serial
def test_the_marker_column_does_not_eat_content(tmp_path):
	"""The marker is an inset, not an overwrite: every byte of metadata
	visible unfocused is still visible focused, and it does not shift
	the index heading beside it."""
	config_path = _world(tmp_path)
	steps = _screens(config_path, [(b"\r\x17k", 0.7), (b"\x17j", 0.5),
	                               (b"\x17j", 0.6)])

	def reader(rows):
		line = next(l for l in rows if "Messages (" in l)
		column = line.index("#")
		head, _, tail = line.partition("#")
		return head.strip("» "), "#" + tail, column

	index_head, unfocused, unfocused_at = reader(steps[1])
	reader_head, focused, focused_at = reader(steps[2])
	assert unfocused == focused, \
		f"the marker displaced metadata: {unfocused!r} vs {focused!r}"
	assert unfocused_at == focused_at, \
		f"the marker shifted the metadata column: {unfocused_at} -> " \
		f"{focused_at}"
	assert index_head == reader_head, \
		"the marker moved the heading beside it"


@pytest.mark.serial
def test_an_empty_reader_keeps_its_explicit_text(tmp_path):
	"""With nothing selected the row says so, rather than going blank
	now that no heading names the pane."""
	from baton_work.tui.app import Console

	config_path = _world(tmp_path)
	database = os.path.join(os.path.dirname(config_path), "work.sqlite3")
	painted = []

	class Screen:
		def addnstr(self, y, x, text, *_rest):
			painted.append(str(text))

	with bw.Authority(database) as store:
		thread = store.conn.execute(
			"SELECT thread FROM thread_labels LIMIT 1").fetchone()[0]
		console = Console(store, "lang", "ada", config_path=config_path)
		console._cached = lambda _key, _read: {
			"messages": [], "next_after": None, "next_before": None,
			"total": 0, "new": 0, "subject": "s"}
		console._render_message_region(Screen(), 5, 24, 110,
		                               {"id": thread})
	flat = "\n".join(painted)
	assert "(no message selected)" in flat
	assert "Message M" not in flat


@pytest.mark.serial
@pytest.mark.parametrize("focused", [False, True])
def test_the_reader_never_bleeds_past_its_cell(tmp_path, focused):
	"""The reader now shares a row with the index heading, so a row that
	overruns its cell no longer runs into blank space — it runs into
	another pane's label. Checked with the longest metadata the handle
	grammar permits (6 cells of team, 6 of member) and an unbroken body
	token, in both focus states."""
	config_path = _world(tmp_path, messages=1, team="engng",
	                     member="alexfz")
	with bw.Authority(os.path.join(os.path.dirname(config_path),
	                               "work.sqlite3")) as store:
		thread = store.conn.execute(
			"SELECT thread FROM thread_labels LIMIT 1").fetchone()[0]
		tr.post_thread(store, thread, author_team="engng",
		               author="alexfz", body="x" * 300)
	script = [(b"\r", 0.8)]
	if focused:
		script += [(b"", 0.4), (b"\x17j", 0.6)]
	rows = _screens(config_path, script, columns=110, lines=24)[-1]
	from baton_work.tui.app import Console
	reader_x = Console.INDEX_WIDTH + 2
	cell = 110 - 1 - reader_x
	for line in rows:
		painted = line[reader_x:].rstrip()
		assert len(painted) <= cell, \
			f"the reader bled past its cell: {painted!r}"
	shared = next(line for line in rows if "Messages (" in line)
	assert shared[reader_x] in ("»", " "), repr(shared[reader_x:reader_x + 4])
	assert shared[reader_x + 1:].lstrip().startswith("#"), \
		repr(shared[reader_x:reader_x + 12])
	# the index heading beside it is intact, not overwritten
	assert "Messages (" in shared[:reader_x]


@pytest.mark.serial
def test_the_scroll_tag_also_respects_the_reserved_column(tmp_path):
	"""`(cont.)` replaces the metadata row when scrolled, on the same
	row and under the same reservation."""
	config_path = _world(tmp_path, messages=1)
	with bw.Authority(os.path.join(os.path.dirname(config_path),
	                               "work.sqlite3")) as store:
		thread = store.conn.execute(
			"SELECT thread FROM thread_labels LIMIT 1").fetchone()[0]
		tr.post_thread(store, thread, author_team="lang", author="ada",
		               body="\n".join(f"line {n}" for n in range(60)))
	rows = _screens(config_path, [(b"\r", 0.8), (b"", 0.4),
	                              (b"\x17j", 0.4), (b"jjj", 0.6)])[-1]
	from baton_work.tui.app import Console
	reader_x = Console.INDEX_WIDTH + 2
	shared = next(line for line in rows if "Messages (" in line)
	painted = shared[reader_x:]
	assert "(cont.)" in painted, \
		f"scrolling did not disclose the hidden head: {painted!r}"
	assert painted[0] == "»", f"the scrolled reader lost its marker: {painted!r}"


# -- everything else is untouched ------------------------------------------

@pytest.mark.serial
def test_the_index_heading_and_selection_cue_survive(tmp_path):
	"""W30 removes ONE heading. The Message-index heading and its
	counts stay, and the reversed index row remains the selection
	cue."""
	config_path = _world(tmp_path)
	rows = _screens(config_path, [(b"\r", 0.7)])[0]
	flat = "\n".join(rows)
	assert "Messages (3/" in flat, flat[:400]
	assert any(line.lstrip().startswith("M") and "lang.ada" in line
	           for line in rows), "the index rows are gone"


@pytest.mark.serial
def test_selection_still_moves_the_reader(tmp_path):
	config_path = _world(tmp_path, body="reply number")
	steps = _screens(config_path, [(b"\r", 0.7), (b"", 0.4),
	                               (b"j", 0.6)])

	def selected(rows):
		line = next(l for l in rows if "#" in l and "lang.ada" in l)
		return line.split("#")[1].split()[0]

	assert selected(steps[0]) != selected(steps[2]), \
		"the reader did not follow the selection"


@pytest.mark.serial
def test_a_resize_keeps_the_reader_headingless(tmp_path):
	config_path = _world(tmp_path)
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada",
		[(b"\r", 0.7), ("resize", (60, 24), 0.8), (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	after = "\n".join(ptyharness.replay(steps[1], columns=60, lines=24))
	assert "Messages (" in after, after[:300]
	assert "Message M" not in after, "a resize brought the heading back"
