"""W73: the default Work list stops repeating `open` at every row.

`work/records/2026/08/finding-hide-redundant-work-state/`. The normal
table hides terminal Work, so every visible row carried `St = open` —
six cells restating a property of the VIEW rather than telling any two
rows apart, on a table whose scarcest resource is horizontal space.

Ruled 2026-08-18 and approved by Slawomir:

- `St` leaves the open-only table. Canonical `status` stays in JSON,
  filtering, detail and Events; this is presentation only.
- Where terminal Work CAN be seen — revealed with `z`, or selected by a
  closed-status filter — a compact `Out` column carries the outcome:
  `sat`, `nsat`, `rej`, `cancl`, and `-` for an open row in a mixed
  view.
- Phase is never overloaded with a terminal outcome. Phase is the open
  Work scheduler axis and terminal Work still has none.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402

OUTCOMES = ("satisfying", "non-satisfying", "rejected", "cancelled")
COMPACT = ("sat", "nsat", "rej", "cancl")


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config, participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title, *, outcome=None):
	work = tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]
	if outcome is not None:
		tr.close_work(world["store"], work, actor_team="lang", actor="ada",
		              rationale="done", outcome=outcome)
	return work


def console(world, *, show_closed=False, work_filter=None):
	made = Console(world["store"], "lang", "ada",
	               config_path=world["config"], work_filter=work_filter)
	made.show_closed = show_closed
	return made


class Screen:
	def __init__(self):
		self.lines = {}

	def addnstr(self, row, col, text, width, *rest):
		"""Paint IN PLACE. A first cut replaced the tail on every call,
		so only the last write to a row survived and every row decoded
		as id-plus-title — which made three assertions here pass for
		the wrong reason before they failed for the right one."""
		text = text[:width]
		line = self.lines.get(row, "").ljust(col)
		self.lines[row] = line[:col] + text + line[col + len(text):]

	def refresh(self):
		pass

	def move(self, *args):
		pass


def table(made, width=110, height=24):
	screen = Screen()
	made._render_table(screen, height, width, made.rows())
	return [screen.lines.get(index, "")
	        for index in range(height)]


def header_of(lines):
	return next(line for line in lines if "Title" in line)


def row_for(lines, title):
	"""The row for one Work, located by the drawn TITLE CELL.

	W2938 removed the Jobs `New` column with no replacement, which
	changed which columns the responsive layout keeps — and the Title
	is the one column it may truncate, so `title in line` stopped
	matching. This reads the cell's real bounds off the header rather
	than guessing an offset, and compares the drawn text as the prefix
	it is, so it survives the next column too."""
	header = next(line for line in lines if "Title" in line)
	start = header.index("Title")
	tail = header[start + len("Title"):]
	end = start + len("Title") + (len(tail) - len(tail.lstrip())) - 1
	for line in lines:
		if line is header or len(line) < start:
			continue
		drawn = line[start:end].rstrip()
		if drawn and title.startswith(drawn):
			return line
	raise AssertionError(f"no row drew a prefix of {title!r}: {lines}")


# -- the default view --------------------------------------------------------

def test_the_open_only_table_has_no_state_column_at_all(world):
	"""The reported redundancy, gone. Not blanked, not shortened —
	absent, so its cells return to the Title."""
	make(world, "a live row")
	make(world, "another live row")
	lines = table(console(world))
	head = header_of(lines)
	assert "St" not in head, head
	assert "Out" not in head, \
		"the terminal Outcome column appeared where nothing can be terminal"
	body = "\n".join(lines[1:])
	assert "open" not in body, \
		f"a row still repeats the view's own invariant: {body[:200]}"
	assert "ST" not in [name for name, _w in app.visible_columns(110)]


def test_a_collapsed_closed_row_does_not_summon_the_column(world):
	"""The default view HIDES terminal Work, so it cannot contain any —
	the hidden count is reported, and the column stays away."""
	make(world, "a live row")
	make(world, "finished", outcome="satisfying")
	made = console(world)
	lines = table(made)
	assert "Out" not in header_of(lines)
	assert "finished" not in "\n".join(lines)
	_visible, hidden = made.visible_rows(made.rows())
	assert hidden == 1


# -- where terminal Work can be seen -----------------------------------------

@pytest.mark.parametrize("outcome,compact", list(zip(OUTCOMES, COMPACT)))
def test_every_terminal_outcome_is_distinguishable(world, outcome, compact):
	"""The point of the column: four terminal outcomes an operator must
	be able to tell apart, none of them the word `closed`."""
	make(world, "the closed one", outcome=outcome)
	lines = table(console(world, show_closed=True))
	assert "Out" in header_of(lines)
	assert compact in row_for(lines, "the closed one").split(), \
		row_for(lines, "the closed one")


def test_the_compact_vocabulary_is_exactly_the_ruled_one(world):
	assert sorted(app.OUTCOME_COMPACT.values()) == sorted(COMPACT)
	for outcome, compact in zip(OUTCOMES, COMPACT):
		assert app.compact_outcome(outcome) == compact
	# the `c/` prefix went with the column that needed it
	assert not any(value.startswith("c/")
	               for value in app.OUTCOME_COMPACT.values())


def test_an_open_row_in_a_mixed_view_dashes_its_outcome(world):
	"""`-` is not a missing value: an open Work HAS no outcome, and
	saying so beside `rej` is what makes the mixed view readable."""
	make(world, "a live row")
	make(world, "rejected one", outcome="rejected")
	lines = table(console(world, show_closed=True))
	assert "-" in row_for(lines, "a live row").split()
	assert "rej" in row_for(lines, "rejected one").split()
	assert app.outcome_cell({"status": "open", "outcome": None}) == "-"


def test_a_closed_status_filter_also_brings_the_column(world):
	"""The ruling names two triggers, and the filter is the one that
	does not touch `z`."""
	make(world, "a live row")
	make(world, "finished", outcome="cancelled")
	made = console(world, work_filter={"status": "closed"})
	assert made.terminal_visible() is True
	lines = table(made)
	assert "Out" in header_of(lines)
	assert "cancl" in row_for(lines, "finished").split()


def test_the_column_follows_the_view_not_the_rows_that_happen_to_be_there(
		world):
	"""Deliberate: the trigger is the VIEW's question. Deriving it from
	whichever rows are on screen would make the column appear and vanish
	as ordinary Work closed underneath the operator, and a table whose
	columns move on their own is harder to read than one dash."""
	make(world, "a live row")
	made = console(world, show_closed=True)
	assert made.terminal_visible() is True
	lines = table(made)
	assert "Out" in header_of(lines), \
		"the revealed view dropped the column because nothing was closed yet"
	assert "-" in row_for(lines, "a live row").split()


# -- phase is not overloaded --------------------------------------------------

def test_phase_still_dashes_on_terminal_work(world):
	"""The ruling's explicit boundary: Phase remains the OPEN Work
	scheduler axis, and terminal Work continues to have none. The
	outcome went to its own column precisely so this stayed true."""
	work = make(world, "the closed one", outcome="non-satisfying")
	made = console(world, show_closed=True)
	row = next(entry for entry in made.rows() if entry["id"] == work)
	assert row["phase"] is None, row
	assert app.phase_cell(row["status"], row["phase"]) == "-"
	drawn = row_for(table(made), "the closed one")
	assert "nsat" in drawn.split()


def test_canonical_status_is_untouched_everywhere_it_lives(world):
	"""Presentation simplification, not a data-model change."""
	open_work = make(world, "a live row")
	closed = make(world, "finished", outcome="rejected")
	rows = {row["id"]: row for row in pj.home(
		world["store"], viewer_team="lang",
		viewer_member="ada")["rows"]}
	assert rows[open_work]["status"] == "open"
	assert rows[open_work]["outcome"] is None
	assert rows[closed]["status"] == "closed"
	assert rows[closed]["outcome"] == "rejected"
	detail = pj.detail(world["store"], closed, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["status"] == "closed"
	assert detail["outcome"] == "rejected", \
		"detail lost the full canonical spelling"


# -- the responsive budget ----------------------------------------------------

def test_the_open_only_budget_gained_the_retired_columns_cells(world):
	"""Removing six cells plus a separator is the operator-visible
	benefit, so it is asserted rather than assumed."""
	for width in (60, 80, 110):
		open_only = app.visible_columns(width)
		mixed = app.visible_columns(width, terminal=True)
		assert "OUT" not in dict(open_only)
		assert "OUT" in dict(mixed) or width < 40, (width, mixed)


def test_out_survives_longest_under_width_pressure(world):
	"""It is present only because the operator asked to see terminal
	Work; dropping it before Route and Next would make the reveal
	pointless, and those two are least interesting on a closed row."""
	assert app.DROP_ORDER[-1] == "OUT"
	# the narrowest width that still keeps Out at all
	narrow = min(width for width in range(20, 140)
	             if "OUT" in dict(app.visible_columns(width,
	                                                  terminal=True)))
	kept = dict(app.visible_columns(narrow, terminal=True))
	assert "ROUTE" not in kept and "NEXT" not in kept, kept
	# and at that same width the OPEN-only view has already spent its
	# extra cells on other columns, which is the trade being asserted
	assert "OUT" not in dict(app.visible_columns(narrow))


def test_identity_and_title_outlive_the_outcome_column(world):
	"""The acceptance boundary's drop-order rule, stated directly."""
	make(world, "a long enough title to matter", outcome="satisfying")
	made = console(world, show_closed=True)
	# the narrowest width this VIEW actually draws at — `layout_fits`
	# alone is optimistic because the leading Id column joins the
	# budget only once the rows are known
	drawn = {}
	for width in range(20, 140):
		lines = table(made, width=width)
		if any("Title" in line for line in lines):
			drawn = {"width": width, "lines": lines}
			break
	assert drawn, "the table never drew at any width"
	head = header_of(drawn["lines"])
	assert head.startswith("Id "), head
	assert "Title" in head, head
	# one cell narrower it REFUSES whole rather than truncating an
	# identity to keep a column
	refused = "\n".join(table(made, width=drawn["width"] - 1))
	assert "too narrow" in refused, refused[:200]


def test_the_budget_is_deterministic_for_every_width(world):
	"""Same width, same answer, and the mixed view never keeps MORE
	columns than the open-only one at the same width."""
	for width in range(20, 140):
		assert app.visible_columns(width) == app.visible_columns(width)
		open_only = {name for name, _w in app.visible_columns(width)}
		mixed = {name for name, _w in app.visible_columns(width,
		                                                  terminal=True)}
		assert (mixed - {"OUT"}) <= open_only, (width, mixed, open_only)
