"""W49: the Message index is a table, not a sentence.

`M<seq>`, the author, the time and the personal state were concatenated
into one string, so every row's time and state began wherever that row's
author handle happened to end. Nothing could be scanned down a column,
which is the only thing an index is for.

The fields now have fixed allocations, one compact header names them,
and each cell is clipped inside its own width so no overflow can move a
later field. Width pressure removes whole fields in reverse priority —
`Time` first, because the viewer's own new/seen fact outranks the clock —
and `Id` never goes, since a row whose selector is gone cannot be acted
on.

W228's viewer-relative action cue is deliberately absent. This Work
leaves the seam: the column set is data, so adding one is an entry in a
tuple.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import Console                        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		                        "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="the opener")
	yield {"store": store, "config": config_path, "work": born["work_id"],
	       "thread": born["thread"]}
	store.close()


def _say(world, count, author="grace"):
	for index in range(count):
		tr.post_thread(world["store"], world["thread"], author_team="lang",
		               author=author, body=f"reply {index}")


def _page(world, viewer="ada", limit=50):
	return pj.thread(world["store"], world["thread"], viewer_team="lang",
	                 viewer_member=viewer, newest=True,
	                 limit=limit)["messages"]


class Screen:
	def __init__(self):
		self.rows = {}
		self.attributes = {}

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]
		if rest:
			self.attributes[y] = rest[0]

	def lines(self):
		return [self.rows[key] for key in sorted(self.rows)]


def _index(world, cell_width=34, rows=10, viewer="ada", cursor=None,
           messages=None):
	console = Console(world["store"], "lang", viewer,
	                  config_path=world["config"])
	page = messages if messages is not None else _page(world, viewer)
	console.msg_cursor = cursor if cursor is not None else (
		page[-1]["seq"] if page else 0)
	screen = Screen()
	console._paint_index(screen, 0, rows, 0, cell_width, page)
	return screen


def _columns_of(header):
	"""Where each heading starts in the painted header row."""
	return {name: header.index(name)
	        for name in ("Id", "Do", "From", "Time", "St")
	        if name in header}


# -- the header and the offsets ---------------------------------------------

def test_one_header_names_the_fields(world):
	_say(world, 3)
	header = _index(world).lines()[0]
	assert header.startswith("Id "), header
	for name in ("From", "Time", "St"):
		assert name in header, header


def test_every_row_uses_the_same_offsets(world):
	"""The defect, directly: handles of different lengths must not move
	the later fields."""
	_say(world, 2, author="ada")        # lang.ada — short
	_say(world, 2, author="grace")      # lang.grace — longer
	painted = _index(world).lines()
	header, rows = painted[0], painted[1:]
	at = _columns_of(header)
	assert len({len(row) for row in rows}) == 1, "rows have unequal widths"
	for row in rows:
		assert row[at["From"]] != " ", f"the From cell is empty: {row!r}"
		assert row[at["Time"]:at["Time"] + 5].strip(), \
			f"the Time cell is not under its heading: {row!r}"
		state = row[at["St"]:at["St"] + 4].strip()
		assert state in ("new", "seen"), f"St is misaligned: {row!r}"


def test_a_long_handle_cannot_push_a_later_field(tmp_path):
	"""The maximum configured address is six cells per handle, so the
	`From` allocation is exactly thirteen. A cell at that limit still
	does not move the clock."""
	home = tmp_path / "widest"
	home.mkdir()
	config_path, database = fx.build_instance(
		str(home),
		{"engng": {"members": {"alexfz": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="engng", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="alexfz",
	                      body="b")
	tr.post_thread(store, born["thread"], author_team="engng",
	               author="alexfz", body="second")
	console = Console(store, "engng", "alexfz", config_path=config_path)
	page = pj.thread(store, born["thread"], viewer_team="engng",
	                 viewer_member="alexfz", newest=True,
	                 limit=10)["messages"]
	console.msg_cursor = page[-1]["seq"]
	screen = Screen()
	console._paint_index(screen, 0, 8, 0, 34, page)
	painted = screen.lines()
	store.close()
	at = _columns_of(painted[0])
	assert "engng.alexfz" in painted[1], painted[1]
	assert len("engng.alexfz") == 12, "the fixture is not at the limit"
	for row in painted[1:]:
		assert row[at["Time"]:at["Time"] + 5].strip(), \
			f"a maximum-width handle moved the clock: {row!r}"
		assert row[at["St"]:at["St"] + 4].strip() in ("new", "seen"), row


# -- the Id allocation -------------------------------------------------------

def test_the_id_column_never_clips_the_selector(world):
	"""'never clips that local selector merely because its sequence
	crossed a decimal boundary'. The selector is what every operation is
	typed from, so it widens the column instead."""
	_say(world, 12)
	page = _page(world)
	longest = max(len(f"M{message['seq']}") for message in page)
	assert longest >= 3, "the fixture did not cross a decimal boundary"
	painted = _index(world).lines()
	for row, message in zip(painted[1:], reversed(page)):
		selector = f"M{message['seq']}"
		assert row.startswith(selector), \
			f"{selector} was clipped or shifted: {row!r}"


def test_the_id_allocation_is_shared_by_every_row_on_the_page(world):
	"""'All rows on that paint use the same allocations.' A two-digit
	row on a page containing a three-digit one is padded, not narrowed."""
	_say(world, 12)
	painted = _index(world).lines()
	# read the offset from the HEADER, not from each row's first space:
	# `M9` is shorter than `M14`, so the first space legitimately moves
	# while the allocation — and therefore the next column — does not.
	at = _columns_of(painted[0])["From"]
	widths = {len(f"M{seq}") for seq in
	          (message["seq"] for message in _page(world))}
	assert len(widths) > 1, "the fixture did not mix selector widths"
	for row in painted[1:]:
		assert row[at] != " ", \
			f"a row disagrees about the Id allocation: {row!r}"
		assert row[:at].rstrip() == row[:at].rstrip().rstrip(), row


def test_the_id_column_is_at_least_its_own_heading(world):
	page = _page(world)
	assert Console.message_id_width(page) >= len("Id")
	assert Console.message_id_width([]) == len("Id")


# -- responsive omission -----------------------------------------------------

@pytest.mark.parametrize("cell_width,expected", [
	(40, ["Id", "Do", "From", "Time", "St"]),
	(34, ["Id", "Do", "From", "Time", "St"]),
	(30, ["Id", "Do", "From", "St"]),
	(26, ["Id", "Do", "From", "St"]),
	(22, ["Id", "Do", "From"]),
	(20, ["Id", "Do"]),
	(12, ["Id", "Do"]),
	(6, ["Id"]),
])
def test_width_pressure_drops_whole_fields_in_reverse_priority(
		world, cell_width, expected):
	"""Priority is Id, Do, From, St, Time — the CLOCK goes before the
	viewer's own new/seen fact, and `Do` outlives every other optional
	field. Only `Id` is unconditional: below the width that fits even
	the cue, the selector is what survives, because a row you cannot
	name is a row you cannot act on.

	W228 took the seam this Work left and inserted `Do` — the
	viewer-relative owed-action cue — second in the visual order and
	last in the drop order. That is the composition W49 was designed
	for: one entry in the column tuple and one drop-order position, no
	change to the painter. The widths here moved because the row is
	genuinely wider now, not because the rule changed."""
	_say(world, 3)
	header = _index(world, cell_width=cell_width).lines()[0]
	present = [name for name in ("Id", "Do", "From", "Time", "St")
	           if name in header]
	assert present == expected, header


def test_a_dropped_field_is_dropped_whole(world):
	"""Never a clipped heading or a half-width cell — the omission is of
	the FIELD, so nothing partial appears where it used to be."""
	_say(world, 3)
	painted = _index(world, cell_width=30).lines()
	assert "Time" not in painted[0]
	for fragment in ("Tim", "Ti", "T "):
		assert fragment not in painted[0].replace("St", ""), painted[0]
	at = _columns_of(painted[0])
	for row in painted[1:]:
		assert row[at["St"]:at["St"] + 4].strip() in ("new", "seen"), row


def test_the_selection_survives_the_narrowest_layout(world):
	"""'Id and the selection cue always survive.'"""
	_say(world, 3)
	page = _page(world)
	chosen = page[-1]["seq"]
	screen = _index(world, cell_width=6, cursor=chosen)
	painted = screen.lines()
	assert any(row.startswith(f"M{chosen}") for row in painted[1:]), painted
	import curses
	rows = [key for key in sorted(screen.rows) if key > 0]
	marked = [key for key in rows
	          if screen.attributes.get(key, 0) & curses.A_REVERSE]
	assert marked, "the selected row lost its cue at the narrowest width"


# -- pages -------------------------------------------------------------------

def test_an_empty_page_says_so_and_paints_no_header(world):
	screen = _index(world, messages=[])
	assert screen.lines() == ["(no messages on this page)"]


def test_a_page_exactly_filling_the_region(world):
	"""The header comes out of the region, so a region of N shows N-1
	messages and the last one is not silently dropped."""
	_say(world, 5)
	painted = _index(world, rows=4).lines()
	assert len(painted) == 4, painted
	assert painted[0].startswith("Id ")
	assert len(painted[1:]) == 3


def test_a_region_with_only_room_for_the_header(world):
	_say(world, 3)
	painted = _index(world, rows=1).lines()
	assert len(painted) == 1 and painted[0].startswith("Id ")


def test_an_overflowing_page_scrolls_to_keep_the_selection(world):
	"""Newest-first, and the selected row must be painted — an
	off-screen selection would make `s` act invisibly."""
	_say(world, 20)
	page = _page(world)
	oldest = page[0]["seq"]
	painted = _index(world, rows=5, cursor=oldest).lines()
	assert any(row.startswith(f"M{oldest}") for row in painted[1:]), painted


def test_the_newest_message_paints_first(world):
	_say(world, 4)
	page = _page(world)
	painted = _index(world).lines()
	assert painted[1].startswith(f"M{page[-1]['seq']}"), painted[:3]


# -- the facts the columns carry --------------------------------------------

def test_the_state_column_is_the_viewers_own(world):
	"""`St` is personal: two viewers of the same page disagree, and that
	is the point of the column."""
	_say(world, 2)
	page = _page(world, viewer="grace")
	view = pj.thread(world["store"], world["thread"], viewer_team="lang",
	                 viewer_member="ada", newest=True, limit=50)
	tr.seen_thread(world["store"], world["thread"], team="lang",
	               member="ada", up_to_seq=view["last_seq"])
	ada = _index(world, viewer="ada").lines()[1:]
	grace = _index(world, viewer="grace", messages=page).lines()[1:]
	assert all("seen" in row for row in ada), ada
	assert any("new" in row for row in grace), grace


def test_the_time_column_is_the_event_time(world):
	_say(world, 1)
	page = _page(world)
	painted = _index(world).lines()
	at = _columns_of(painted[0])
	stamp = (page[-1].get("ts") or "")[11:16]
	assert painted[1][at["Time"]:at["Time"] + 5] == stamp


def test_new_rows_are_bold_and_the_selection_is_reversed(world):
	import curses
	_say(world, 3)
	page = _page(world)
	screen = _index(world, cursor=page[-1]["seq"])
	rows = [key for key in sorted(screen.rows) if key > 0]
	assert screen.attributes[rows[0]] & curses.A_REVERSE, \
		"the selected row is not reversed"
	assert any(screen.attributes[key] & curses.A_BOLD for key in rows[1:]), \
		"no unseen row is bold"


# -- the seam W228 will use --------------------------------------------------

def test_the_column_set_is_data_not_a_format_string(world):
	"""W49 'must leave a clean column-layout seam for its future
	viewer-relative action cue'. That means adding a column is an entry
	in a tuple and a drop-order position — provable by adding one here
	and seeing it laid out and dropped without touching the painter."""
	# W228 has since taken this seam: `Do` was added as one entry and
	# one drop-order position, with no change to the painter — which is
	# what the seam was for.
	assert Console.MESSAGE_COLUMNS == (
		("Do", 4), ("From", 13), ("Time", 5), ("St", 4))
	assert Console.MESSAGE_DROP_ORDER == ("Time", "St", "From", "Do")
	kept = [name for name, _width in
	        Console.message_columns(cell_width=40, id_width=3)]
	assert kept == ["Do", "From", "Time", "St"]

	# and the seam still works for the NEXT column, proved the same way
	class WithAnother(Console):
		MESSAGE_COLUMNS = Console.MESSAGE_COLUMNS + (("Age", 3),)
		MESSAGE_DROP_ORDER = ("Age",) + Console.MESSAGE_DROP_ORDER

	wide = [name for name, _w in WithAnother.message_columns(46, 3)]
	assert wide == ["Do", "From", "Time", "St", "Age"], \
		"a new column was not laid out from the declaration alone"
	tight = [name for name, _w in WithAnother.message_columns(34, 3)]
	assert "Age" not in tight and "Time" in tight, \
		"the new column did not take its declared drop-order position"


def test_the_cue_is_absent_when_nothing_is_owed(world):
	"""W49 originally asserted that this Work ships NO obligation cue —
	a scope boundary, true until W228 took the seam. The boundary that
	survives is the one that still means something: the column is empty
	unless the viewer actually owes an action on that Message, so
	`Do` never becomes decoration.

	W228 owns the positive cases; this holds the negative one from the
	layout side, where a column that always painted something would be
	indistinguishable from one that painted the truth."""
	_say(world, 3)
	painted = _index(world).lines()
	at = _columns_of(painted[0])["Do"]
	for row in painted[1:]:
		assert row[at:at + 4].strip() == "", \
			f"a Message nobody owes an action on carries a cue: {row!r}"


# -- a real terminal ---------------------------------------------------------

@pytest.mark.serial
def test_the_columns_align_on_a_real_terminal_and_survive_a_resize(world):
	_say(world, 3, author="grace")
	_say(world, 2, author="ada")
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"\r", 0.8), ("resize", (60, 24), 0.9), (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	for label, columns, step in (("wide", 110, steps[0]),
	                             ("narrow", 60, steps[1])):
		screen = ptyharness.replay(step, columns=columns, lines=24)
		header = next((line for line in screen
		               if line.lstrip().startswith("Id ")), None)
		assert header is not None, f"{label}: no index header: {screen[:8]}"
		offset = len(header) - len(header.lstrip())
		body = [line for line in screen
		        if line[offset:offset + 1] == "M" and line.strip()]
		assert body, f"{label}: no index rows"
		at = header.index("From")
		for row in body:
			assert row[at] != " ", \
				f"{label}: a From cell is not under its heading: {row!r}"


def test_an_oversized_cell_is_clipped_rather_than_shifting_the_row(world):
	"""'clipped inside its own allocation; it never pushes time or state
	sideways.'

	Unreachable through the configured grammar — a handle is capped at
	six display cells, so `team.member` is at most the thirteen the
	`From` allocation gives it. The painter is handed a message here
	that breaks that promise anyway, because the alignment must be a
	property of the LAYOUT rather than of an upstream limit: if the
	handle cap ever moves, or a projection grows the field, the index
	must lose characters from one cell instead of losing its columns."""
	page = list(_page(world))
	page[-1] = dict(page[-1], author_team="engineering",
	                author="alexandra-fitzgerald")
	painted = _index(world, messages=page).lines()
	at = _columns_of(painted[0])
	row = painted[1]
	assert row[at["From"]:at["From"] + 13] == "engineering.a", row
	assert row[at["Time"]:at["Time"] + 5].strip(), \
		f"an oversized handle pushed the clock sideways: {row!r}"
	assert row[at["St"]:at["St"] + 4].strip() in ("new", "seen"), row
	# and every row on the page still ends at the same column
	assert len({len(line) for line in painted}) == 1, painted
