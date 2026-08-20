"""W137: the runtime-state tables are clear and responsive.

`work/records/2026/08/finding-responsive-teams-runtime-table/`. Two
presentation choices from W93 were wrong in opposite directions:

- the Jobs column beside `Handler` was headed `Agent` but never held
  one. `Handler` names the participant; those cells say what that
  participant's RUNNER is doing (`work`, `input`, `retry`, `off`). It
  is `Run` now — presentation only, and Teams keeps its own `Agent`
  column, which really does name the adapter family;
- the Teams Members table measured its content, computed a `used`
  width, and then threw it away, so it stayed as narrow as its floors
  no matter how much terminal it had. `Session` was additionally cut
  to twelve characters INSIDE the cell builder, before the layout
  could know whether it had eighty columns or two hundred, so a wide
  terminal could not recover a locator the record held all along.

What these tests hold: the rename with its JSON parity, and the layout
as a function of width — wide, exact fit, narrow, resize, no session,
and a long identity — asserted on the composed row and never on the
paint calls that produced it.
"""

from __future__ import annotations

import curses
import os
import pathlib
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import (Console, TEAM_COLUMNS,          # noqa: E402
                                TEAM_DROP_ORDER, team_layout)
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
SESSION = "01a01552-9d3e-77bb-a2c1-0f4d5e6a7b8c"
TAB = 9
NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the held work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")
	tr.claim_work(store, born["work_id"], actor_team="lang", actor="ada")
	tr.runtime_start(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", adapter="codex",
	                 provider="OpenAI", model="gpt-5.6", session=SESSION)
	tr.runtime_state(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", state="working",
	                 work=born["work_id"])
	store.close()
	return {"config": config_path, "database": database,
	        "work": born["work_id"]}


class Screen:
	def __init__(self, height=26, width=110):
		self.height = height
		self.width = width
		self.rows = {}

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "")
		text = str(text)[:n]
		row = row.ljust(x)
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def console(world, member="ada", tab=None):
	store = bw.Authority(world["database"])
	view = Console(store, "lang", member, config_path=world["config"])
	while tab is not None and view.tab != tab:
		view.handle(NEXT_TAB)
	return view


def painted(view, height=26, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


def teams_rows(view, width=110, height=26):
	"""The header row and the member rows, composed."""
	lines = painted(view, height=height, width=width)
	header = next((line for line in lines
	               if line.startswith("Participant")), "")
	members = [line for line in lines if line.startswith("lang.")]
	return header, members


def natural_for(view):
	rows = view.team_rows()
	cells = {row["participant"]: view._team_cells(row) for row in rows}
	return {name: max([len(name)] + [len(cells[row["participant"]][name])
	                                 for row in rows])
	        for name, _floor, _cap in TEAM_COLUMNS}


# -- Jobs: the column is named for what it holds ----------------------------

def test_jobs_heads_the_runtime_column_run(world):
	header = next(line for line in painted(console(world))
	              if "Handler" in line)
	assert "Run" in header, header
	assert "Agent" not in header, \
		"the superseded header survived in Jobs"
	assert header.index("Handler") < header.index("Run")


def test_the_run_cells_are_the_same_canonical_states(world):
	"""A rename, and nothing else. The cells, the projection field they
	read and the JSON beside them are untouched."""
	lines = painted(console(world))
	row = next(line for line in lines
	           if line.startswith(world["work"].rsplit("-", 1)[1] + " "))
	assert "lang.ada" in row and "work" in row, row
	store = bw.Authority(world["database"])
	try:
		entry = next(item for item in pj.tree(
			store, None, viewer_team="lang",
			viewer_member="ada")["rows"]
			if item["id"] == world["work"])
	finally:
		store.close()
	assert entry["agent"]["state"] == "working", \
		"the projection field moved with the header"
	assert app.agent_cell(entry["agent"]) == "work"


def test_the_column_key_and_the_drop_order_agree(world):
	names = [name for name, _w in app.COLUMNS]
	assert "RUN" in names and "AGENT" not in names, names
	assert set(app.DROP_ORDER) <= set(names), \
		"a drop-order entry names no column"
	assert "RUN" in app.DROP_ORDER


def test_teams_keeps_its_own_agent_column(world):
	"""The two columns are not the same column. In Teams `Agent` names
	the adapter FAMILY and `State` says what it is doing; the finding
	keeps both, and only Jobs was misnamed."""
	header, members = teams_rows(console(world, tab="teams"))
	assert "Agent" in header and "State" in header, header
	mine = next(line for line in members if line.startswith("lang.ada"))
	assert "codex" in mine and "work" in mine, mine


# -- the layout, as a function of width --------------------------------------

def test_a_wide_terminal_shows_the_whole_session(world):
	header, members = teams_rows(console(world, tab="teams"), width=160)
	assert "Session" in header
	mine = next(line for line in members if line.startswith("lang.ada"))
	assert SESSION in mine, mine
	assert "…" not in mine, "a wide terminal still abbreviated"


def test_the_wide_row_never_paints_past_the_edge(world):
	for width in (60, 80, 110, 160, 200):
		_header, members = teams_rows(console(world, tab="teams"),
		                              width=width)
		for line in members:
			assert len(line) <= width - 1, (width, len(line), line)


def test_an_exact_fit_shows_everything_and_nothing_more(world):
	view = console(world, tab="teams")
	natural = natural_for(view)
	id_natural = max(len(row["participant"])
	                 for row in view.team_rows())
	id_width, columns = team_layout(10_000, id_natural, natural)
	need = id_width + sum(size + 1 for _name, size in columns)
	# at exactly the width the full table needs, nothing is dropped
	exact, exact_columns = team_layout(need + 1, id_natural, natural)
	assert [name for name, _s in exact_columns] == \
		[name for name, _s in columns]
	assert dict(exact_columns) == dict(columns)
	assert exact == id_width
	# one column narrower, and the FIRST optional field gives way
	_id, tighter = team_layout(need, id_natural, natural)
	assert dict(tighter)["Session"] < dict(columns)["Session"], tighter


@pytest.mark.parametrize("width", list(range(6, 200, 1)))
def test_no_width_ever_overflows_or_reorders(world, width):
	"""The layout is a total function: every width produces a table
	that fits, in the declared column order."""
	view = console(world, tab="teams")
	natural = natural_for(view)
	id_width, columns = team_layout(width, 12, natural)
	assert id_width + sum(size + 1 for _n, size in columns) \
		<= max(0, width - 1), (width, id_width, columns)
	order = [name for name, _floor, _cap in TEAM_COLUMNS]
	assert [name for name, _s in columns] == \
		[name for name in order if name in dict(columns)]


def test_narrow_widths_drop_whole_columns_in_the_ruled_order(world):
	"""Deterministic, and in the order the record states: the session
	locator first, because the member detail block below carries it in
	full, so it is the one column whose loss costs an operator nothing
	they cannot recover with one keystroke."""
	view = console(world, tab="teams")
	natural = natural_for(view)
	dropped = []
	previous = {name for name, _s in team_layout(400, 12, natural)[1]}
	for width in range(400, 5, -1):
		present = {name for name, _s in team_layout(width, 12, natural)[1]}
		for name in sorted(previous - present):
			dropped.append(name)
		assert present <= previous, \
			f"width {width} brought a column back as the screen shrank"
		previous = present
	assert dropped == list(TEAM_DROP_ORDER) + ["State"], dropped


def test_the_identity_and_the_state_survive_longest(world):
	view = console(world, tab="teams")
	natural = natural_for(view)
	for width in range(20, 60):
		id_width, columns = team_layout(width, 12, natural)
		assert id_width >= app.TEAM_ID_FLOOR, (width, id_width)
		assert "State" in dict(columns), (width, columns)


def test_a_truncated_value_says_that_it_is_truncated(world):
	"""Never split an identifier ambiguously: a silently cut locator
	reads as a different, shorter locator."""
	view = console(world, tab="teams")
	_header, members = teams_rows(view, width=70)
	mine = next(line for line in members if line.startswith("lang.ada"))
	assert SESSION not in mine, "70 columns should not fit this locator"
	assert "…" in mine, mine
	assert SESSION[:10] in mine, mine


def test_a_resize_is_just_the_layout_asked_again(world):
	"""Selection, member detail and everything else survive; only the
	widths move."""
	view = console(world, tab="teams")
	wide, wide_rows = teams_rows(view, width=160)
	narrow, narrow_rows = teams_rows(view, width=70)
	back, back_rows = teams_rows(view, width=160)
	assert wide == back and wide_rows == back_rows, \
		"the table did not come back from a resize"
	assert SESSION in wide_rows[0] and SESSION not in narrow_rows[0]
	assert view.team_cursor == 0


def test_a_member_with_no_session_is_a_dash_not_a_gap(world):
	"""`-` means the authority holds no such fact. It must not become
	an empty cell that reads as "fine"."""
	view = console(world, member="grace", tab="teams")
	_header, members = teams_rows(view, width=160)
	other = next(line for line in members
	             if line.startswith("lang.grace"))
	assert " - " in other, other
	assert SESSION not in other


def test_a_long_identity_is_not_silently_shortened(world):
	view = console(world, tab="teams")
	natural = natural_for(view)
	long_id = len("lang.a-very-long-participant-identity")
	id_width, _columns = team_layout(200, long_id, natural)
	assert id_width == long_id, id_width
	# and when it truly cannot fit, the cut is VISIBLE
	assert app._fit("lang.a-very-long-participant", 10) == "lang.a-ve…"


def test_the_session_is_no_longer_cut_before_the_layout_runs(world):
	"""The defect, named. `_team_cells` must hand the layout the WHOLE
	value; deciding a width inside the cell builder is what made a wide
	terminal unable to recover it."""
	view = console(world, tab="teams")
	row = next(entry for entry in view.team_rows()
	           if entry["participant"] == "lang.ada")
	assert view._team_cells(row)["Session"] == SESSION


# -- selection and detail are unchanged --------------------------------------

def test_selection_and_member_detail_still_behave(world):
	view = console(world, tab="teams")
	lines = painted(view, width=160)
	assert any(SESSION in line and line.startswith("  ") or
	           SESSION in line for line in lines)
	# W184: `Provider` is its own key/value row.
	assert any(line.strip().startswith("Provider") and "OpenAI" in line
	           for line in lines), lines
	before = view.team_cursor
	view.handle(ord("j"))
	assert view.team_cursor != before, "j stopped selecting"
	assert any("t own/all teams" in line
	           for line in painted(view, width=160))


def test_the_own_member_emphasis_and_selection_still_paint(world):
	"""Both weights are still asked of the row, not of the layout."""
	class Attr(Screen):
		def __init__(self, height=26, width=160):
			super().__init__(height, width)
			self.calls = []

		def addnstr(self, y, x, text, n, *rest):
			super().addnstr(y, x, text, n, *rest)
			self.calls.append((str(text)[:n], rest[0] if rest else 0))

	view = console(world, tab="teams")
	screen = Attr()
	view.render(screen)
	selected = [text for text, attr in screen.calls
	            if attr & curses.A_REVERSE and text.startswith("lang.")]
	assert selected and selected[0].startswith("lang.ada"), selected


# -- the operator documentation ----------------------------------------------

def test_the_documentation_uses_the_same_column_vocabulary():
	body = (REPO / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	prose = " ".join(body.split())
	assert "`Run`" in prose, "the Jobs column is undocumented"
	assert "`Agent`" in prose and "`State`" in prose, \
		"the Teams columns are undocumented"


# -- a real terminal ---------------------------------------------------------

@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_uses_the_width_it_has(world):
	"""Two real terminals, one wide and one narrow, from the same
	authority: the wide one shows the whole locator and the narrow one
	says it abbreviated rather than pretending."""
	wide_text, wide_status, _steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"]", 0.6), (b"qy", 0.4)], columns=180, lines=26)
	wide = ptyharness.replay(wide_text, columns=180, lines=26)
	assert any(SESSION in line for line in wide), \
		[line for line in wide if "lang.ada" in line]
	assert os.WIFEXITED(wide_status) and os.WEXITSTATUS(wide_status) == 0

	narrow_text, narrow_status, _steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"]", 0.6), (b"qy", 0.4)], columns=72, lines=26)
	narrow = ptyharness.replay(narrow_text, columns=72, lines=26)
	member = next(line for line in narrow
	              if line.startswith("lang.ada"))
	assert SESSION not in member, member
	assert "…" in member, member
	for line in narrow:
		assert len(line.rstrip()) <= 72, line
	assert os.WIFEXITED(narrow_status) \
		and os.WEXITSTATUS(narrow_status) == 0
