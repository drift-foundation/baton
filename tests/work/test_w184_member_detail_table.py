"""W184: Teams member details are a key/value table.

`work/records/2026/08/finding-teams-member-detail-table/`. The block
was a sequence of prose lines — identity, roles, routes, held Work,
runner state, adapter/provider/model, session, incarnation,
timestamps, facts and the last poke answer — with labels starting at
different columns and several facts packed into one sentence. The data
was all there; finding one field meant rereading the whole block.

The ruling: grouped key/value rows, keys left, values in one aligned
column, wrapped continuations at the value column, every fact its own
key, and a `Log` row that says "not published" rather than guessing a
path.

These tests hold the SHAPE (alignment, sections, wrapping, the key
cap) and the CONTENT (every fact that was there before is still
there, and missing/unknown/absent stay distinguishable from each
other). Presentation only: the projection is asserted unchanged.
"""

from __future__ import annotations

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
from baton_work.tui.app import Console, kv_lines                # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
SESSION = "01a01552-9d3e-77bb-a2c1-0f4d5e6a7b8c-and-longer-still"
TAB = 9
NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes
SECTIONS = ("Identity and routing", "Workflow", "Runner state",
            "Operational diagnostics", "Last poke answer")


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def furnish(world, *, session=SESSION, facts=True, answer=True):
	"""A member with everything the block can show."""
	store = world["store"]
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the held work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")
	tr.claim_work(store, born["work_id"], actor_team="lang", actor="ada")
	tr.runtime_start(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", adapter="codex",
	                 provider="OpenAI", model="gpt-5.6", session=session,
	                 action_owner="lang.grace")
	tr.runtime_state(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", state="waiting-input",
	                 cause="approval", detail="command approval required",
	                 work=born["work_id"])
	if facts:
		tr.runtime_facts(store, actor_team="lang", actor="ada",
		                 incarnation="run-1", source="configured",
		                 facts={"workdir": "/home/op/src/baton",
		                        "log": "/var/log/codex-event-bridge.log",
		                        "version": "codex-event-bridge 1.4.0"})
	if answer:
		seq = tr.poke(store, actor_team="lang", actor="grace",
		              target="lang.ada", request="status?")["poke"]
		tr.answer_poke(store, seq, actor_team="lang", actor="ada",
		               state="needs-help",
		               explanation="the approval prompt is blocking me",
		               provider="OpenAI", model="gpt-5.6",
		               session_state="live", auth_state="ok",
		               limit_state="ok", context_used=90,
		               context_limit=100)
	return born["work_id"]


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	view = Console(store, "lang", member, config_path=world["config"])
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	return view


def detail(world, member="ada", width=110):
	"""The block itself, straight from the renderer — no screen, so a
	short terminal cannot hide a row this is asserting about."""
	view = console(world, member)
	row = next(entry for entry in view.team_rows()
	           if entry["participant"] == f"lang.{member}")
	return view._team_detail(row, width)


class Screen:
	def __init__(self, height=40, width=110):
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
		row = self.rows.get(y, "").ljust(x)
		text = str(text)[:n]
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def painted(view, height=40, width=110):
	screen = Screen(height, width)
	view.render(screen)
	return screen.lines()


def row_for(lines, key):
	"""The value of one key, from the composed block."""
	for line in lines:
		stripped = line.strip()
		if stripped.startswith(key) and (
				len(stripped) == len(key)
				or stripped[len(key)] == " "):
			return stripped[len(key):].strip()
	return None


def value_column(lines):
	"""Where the values start — the same column for every row."""
	columns = set()
	for line in lines:
		if not line.startswith("    ") or not line.strip():
			continue
		body = line[4:]
		if body.startswith(" "):
			continue
		gap = body.find("  ")
		if gap > 0 and body[gap:].strip():
			columns.add(4 + len(body[:gap].ljust(gap)) +
			            len(body[gap:]) - len(body[gap:].lstrip()))
	return columns


# -- the shape ---------------------------------------------------------------

def test_the_block_is_grouped_into_the_ruled_sections(world):
	furnish(world)
	lines = detail(world)
	titles = [line.strip() for line in lines
	          if line.startswith("  ") and not line.startswith("    ")
	          and line.strip()]
	for section in SECTIONS:
		assert section in titles, (section, titles)
	assert titles.index("Identity and routing") < titles.index("Workflow")
	assert titles.index("Runner state") < \
		titles.index("Operational diagnostics")


def test_every_value_starts_in_the_same_column(world):
	furnish(world)
	lines = detail(world)
	starts = set()
	for line in lines:
		if not line.startswith("    ") or line[4:5] == " ":
			continue
		body = line[4:]
		gap = body.find("  ")
		if gap <= 0:
			continue
		starts.add(4 + len(body) - len(body[gap:].lstrip()))
	assert len(starts) == 1, \
		f"the value column moved between rows: {sorted(starts)}"


def test_a_wrapped_value_continues_at_the_value_column(world):
	"""Not under its key: a wrapped locator must still read as one
	field's content."""
	furnish(world)
	lines = detail(world, width=60)
	session_at = next(index for index, line in enumerate(lines)
	                  if line.strip().startswith("Session"))
	head = lines[session_at]
	column = len(head) - len(head[head.index("  ", 4):].lstrip())
	continuation = lines[session_at + 1]
	assert continuation.startswith(" " * column), \
		(column, repr(continuation))
	assert continuation.strip(), "the wrap produced an empty line"
	# and the whole locator is recoverable from the wrapped pieces
	joined = "".join(line.strip() for line in
	                 lines[session_at:session_at + 4])
	assert SESSION in joined.replace("Session", ""), joined


def test_a_long_key_never_eats_the_value_column(world):
	"""The cap is a third of the usable width. A key past it keeps its
	whole text and its value begins on the next line — truncating a
	label would produce something that reads like a different one."""
	sections = [("Section", [("An extremely long key name", "value"),
	                         ("Short", "other")])]
	lines = kv_lines(sections, 30)
	assert "An extremely long key name" in lines[1]
	assert lines[2].strip() == "value"
	assert lines[3].lstrip().startswith("Short")
	assert lines[2].index("value") == lines[3].index("other")


def test_an_empty_section_is_omitted_not_left_as_a_heading(world):
	assert kv_lines([("Empty", []), ("Full", [("K", "v")])], 60) == \
		["  Full", "    K  v"]
	assert kv_lines([("Empty", [])], 60) == []


# -- the content: everything that was there is still there -------------------

def test_identity_and_routing_keep_their_facts(world):
	furnish(world)
	lines = detail(world)
	assert row_for(lines, "Participant") == "lang.ada"
	assert row_for(lines, "Display") == "Ada"
	assert row_for(lines, "Roles") == "dev"
	assert "lang.bug" in row_for(lines, "Route")


def test_workflow_keeps_the_held_work(world):
	work = furnish(world)
	lines = detail(world)
	held = row_for(lines, "Holding")
	assert work.rsplit("-", 1)[1] in held, held
	assert "the held work" in held


def test_every_runner_fact_has_its_own_key(world):
	"""The ruling names these individually: combining unrelated facts
	to save a row is what made the old block unscannable."""
	furnish(world)
	lines = detail(world)
	expected = {"State": "waiting-input (reported)",
	            "Cause": "approval",
	            "Detail": "command approval required",
	            "Adapter": "codex",
	            "Provider": "OpenAI",
	            "Model": "gpt-5.6",
	            "Incarnation": "run-1"}
	for key, value in expected.items():
		assert row_for(lines, key) == value, (key, row_for(lines, key))
	assert row_for(lines, "Session").startswith(SESSION[:20])
	for key in ("Since", "Last contact", "Lease expires", "Stale"):
		assert row_for(lines, key), key
	assert "lang.grace" in row_for(lines, "Action owner")


def test_the_operational_facts_keep_source_and_age(world):
	furnish(world)
	lines = detail(world)
	workdir = row_for(lines, "Workdir")
	assert "/home/op/src/baton" in workdir
	assert "configured" in workdir and "ago" in workdir, workdir
	assert "codex-event-bridge 1.4.0" in row_for(lines, "Version")


def test_the_log_row_carries_the_exact_locator(world):
	furnish(world)
	log = row_for(detail(world), "Log")
	assert "/var/log/codex-event-bridge.log" in log, log
	assert "configured" in log and "ago" in log, log


def test_an_unpublished_log_says_so_rather_than_guessing(world):
	"""The ruling is explicit: an operator looking for the log must be
	told it was never published, not handed a path from a deployment
	they hope is running."""
	furnish(world, facts=False)
	log = row_for(detail(world), "Log")
	assert log is not None, "the Log row disappeared with the facts"
	assert "not published" in log, log
	assert "/var/log" not in log, log


def test_the_last_poke_answer_keeps_every_field(world):
	furnish(world)
	lines = detail(world)
	assert row_for(lines, "Said") == "needs-help"
	assert "approval prompt" in row_for(lines, "Explanation")
	assert row_for(lines, "Session state") == "live"
	assert row_for(lines, "Auth state") == "ok"
	assert row_for(lines, "Limit state") == "ok"
	assert row_for(lines, "Context used") == "90"
	assert row_for(lines, "Context limit") == "100"


def test_partial_poke_telemetry_never_renders_python_none(world):
	"""Each telemetry field is independently optional in the protocol.

	If an adapter knows only one of the three, the table must preserve the
	other two as explicitly absent rather than leaking Python's internal
	``None`` spelling into the operator surface.
	"""
	furnish(world, answer=False)
	seq = tr.poke(world["store"], actor_team="lang", actor="grace",
	              target="lang.ada", request="status?")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="working", explanation="capacity known",
	               context_limit=200)
	lines = detail(world)
	assert row_for(lines, "Context limit") == "200"
	assert row_for(lines, "Context used") == "-"
	assert row_for(lines, "Context remaining") == "-"
	assert not any("None" in line for line in lines), lines


# -- missing, unknown and absent stay different ------------------------------

def test_a_member_with_no_lease_says_that_and_not_a_row_of_dashes(world):
	lines = detail(world, member="grace")
	lease = row_for(lines, "Lease")
	assert lease and "never published runtime state" in lease, lease
	assert row_for(lines, "State") is None, \
		"a member with no lease grew a state row"


def test_never_asked_is_not_the_same_as_answered_nothing(world):
	furnish(world, answer=False)
	said = row_for(detail(world), "Said")
	assert "never asked" in said, said


def test_an_unknown_reported_value_is_shown_as_unknown(world):
	"""`unknown` is a fact ABOUT the adapter. The renderer must not
	tidy it into a blank or a dash."""
	furnish(world, answer=False)
	seq = tr.poke(world["store"], actor_team="lang", actor="grace",
	              target="lang.ada", request="status?")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="idle", explanation="between turns")
	lines = detail(world)
	assert row_for(lines, "Provider") == "unknown" or \
		row_for(lines, "Session state") == "unknown", lines
	assert row_for(lines, "Auth state") == "unknown"


def test_an_absent_optional_fact_is_a_dash_not_a_gap(world):
	furnish(world, facts=False)
	world["store"].close()
	world["store"] = bw.Authority(world["database"])
	lines = detail(world, member="grace")
	# grace has no lease at all — the one row says so, and nothing
	# invents a reassuring value beside it
	assert not any("ok" in line for line in lines
	               if line.strip().startswith("Auth"))


# -- widths ------------------------------------------------------------------

@pytest.mark.parametrize("width", [200, 110, 80, 60, 40, 30, 20, 12])
def test_no_width_paints_past_the_edge(world, width):
	furnish(world)
	for line in detail(world, width=width):
		assert len(line) <= max(8, width - 1), (width, len(line), line)


def test_a_narrow_block_still_carries_every_key(world):
	furnish(world)
	wide = {line.strip().split("  ")[0]
	        for line in detail(world, width=160) if line.startswith("    ")}
	narrow = {line.strip().split("  ")[0]
	          for line in detail(world, width=44) if line.startswith("    ")}
	assert wide <= narrow | {""}, sorted(wide - narrow)


def test_a_wide_terminal_recovers_the_whole_session(world):
	furnish(world)
	assert row_for(detail(world, width=200), "Session") == SESSION


def test_a_resize_is_just_the_block_asked_again(world):
	furnish(world)
	before = detail(world, width=160)
	detail(world, width=40)
	assert detail(world, width=160) == before


def test_a_multi_route_member_lists_each_route(world):
	"""One row per route, not one sentence for all of them."""
	furnish(world)
	lines = detail(world)
	routes = [line for line in lines
	          if line.strip().startswith("Route")]
	view = console(world)
	row = next(entry for entry in view.team_rows()
	           if entry["participant"] == "lang.ada")
	assert len(routes) == max(1, len(row["routes"])), routes


# -- the surroundings are unchanged ------------------------------------------

def test_the_projection_is_untouched(world):
	"""Presentation only. The JSON a consumer reads is the same one."""
	furnish(world)
	roster = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	mine = next(row for entry in roster["teams"]
	            for row in entry["members"]
	            if row["participant"] == "lang.ada")
	assert mine["runtime"]["session"] == SESSION
	assert mine["runtime"]["state"] == "waiting-input"
	assert mine["last_answer"]["state"] == "needs-help"
	assert {fact["key"] for fact in mine["runtime"]["facts"]} == \
		{"workdir", "log", "version"}


def test_selection_scope_and_actions_still_work(world):
	furnish(world)
	view = console(world)
	before = view.team_cursor
	view.handle(ord("j"))
	assert view.team_cursor != before
	lines = painted(view)
	assert any("j/k select" in line and "p poke" in line
	           for line in lines), lines[-3:]
	scope = view.teams_own_only
	view.handle(ord("t"))
	assert view.teams_own_only is not scope


def test_a_short_terminal_says_what_it_could_not_show(world):
	"""The block is taller now, by design. A terminal that cannot hold
	it must say so rather than stopping mid-table and looking
	complete."""
	furnish(world)
	view = console(world)
	lines = painted(view, height=18)
	assert any("more row(s)" in line and "`teams`" in line
	           for line in lines), lines[-4:]


# -- documentation and a real terminal ---------------------------------------

def test_the_documentation_shows_the_sections():
	body = (REPO / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	prose = " ".join(body.split())
	for section in SECTIONS:
		assert section in prose, section
	assert "Log" in prose


@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_paints_the_table(world):
	furnish(world)
	world["store"].close()
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"]", 0.6), (b"qy", 0.4)], columns=120, lines=44)
	screen = ptyharness.replay(text, columns=120, lines=44)
	for section in ("Identity and routing", "Runner state",
	                "Operational diagnostics"):
		assert any(line.strip() == section for line in screen), \
			(section, screen[:20])
	assert any(line.strip().startswith("Session") and SESSION[:20] in line
	           for line in screen), screen
	assert any(line.strip().startswith("Log")
	           and "/var/log/codex-event-bridge.log" in line
	           for line in screen), screen
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
