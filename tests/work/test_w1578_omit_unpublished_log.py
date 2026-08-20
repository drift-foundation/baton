"""W1578: an unpublished log gets no row at all.

`work/records/2026/08/finding-omit-unpublished-member-log/`. In the
deployed Teams member-detail table every configured participant painted
the same wide sentence:

    Log  not published — this runner's adapter has published no log locator

W184 put it there deliberately — an operator hunting for the log should
be told it was never published rather than left to guess a path from a
deployment they hope is running. What the live table showed is that the
row is unanimous: nobody's adapter publishes a log locator, so the
sentence costs a wide row per member and discloses nothing an absent
inventory key does not already say.

The 2026-08-20 ruling keeps the half of W184 that was load bearing and
retires the half that was not: a PUBLISHED log still appears verbatim
with its source and age, and an absent one is simply absent. Nothing
guesses a path either way — the difference is only whether Baton spends
a row saying so.

This is presentation. These assert the projection is untouched, because
"the row is gone" and "the fact is gone" are very different failures.
"""

from __future__ import annotations

import copy
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
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
NEXT_TAB = ord("]")
LOCATOR = "/var/log/codex-event-bridge.log"


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def runner(world, member, incarnation, facts=None):
	"""One member with a live lease and exactly the facts named."""
	tr.runtime_start(world["store"], actor_team="lang", actor=member,
	                 incarnation=incarnation, adapter="codex",
	                 provider="OpenAI", model="gpt-5.6",
	                 session=f"session-{member}")
	if facts:
		tr.runtime_facts(world["store"], actor_team="lang", actor=member,
		                 incarnation=incarnation, source="configured",
		                 facts=facts)


def detail(world, member="ada", width=110):
	"""The composed block straight from the renderer, so a short screen
	cannot hide a row under test."""
	store = bw.Authority(world["database"])
	try:
		view = Console(store, "lang", member, config_path=world["config"])
		while view.tab != "teams":
			view.handle(NEXT_TAB)
		row = next(entry for entry in view.team_rows()
		           if entry["participant"] == f"lang.{member}")
		return view._team_detail(row, width)
	finally:
		store.close()


def row_for(lines, key):
	for line in lines:
		stripped = line.strip()
		if stripped.startswith(key) and (
				len(stripped) == len(key) or stripped[len(key)] == " "):
			return stripped[len(key):].strip()
	return None


def titles(lines):
	return [line.strip() for line in lines
	        if line.startswith("  ") and not line.startswith("    ")
	        and line.strip()]


# -- the ruling --------------------------------------------------------------

def test_a_published_log_still_carries_its_locator_source_and_age(world):
	"""Acceptance 1 — the half of W184 that stands. A locator that
	EXISTS is exactly as visible as it was."""
	runner(world, "ada", "run-1", {"log": LOCATOR})
	log = row_for(detail(world), "Log")
	assert LOCATOR in log, log
	assert "configured" in log and "ago" in log, log


def test_an_absent_log_leaves_no_row_and_no_sentence(world):
	"""Acceptance 2 — the row is gone, and so is the prose that made it
	worth removing. Asserted against the WHOLE block rather than the
	`Log` key alone, because a sentence relocated to another key would
	cost the same row and read the same way."""
	runner(world, "ada", "run-1", {"workdir": "/home/op/src/baton"})
	lines = detail(world)
	assert row_for(lines, "Log") is None, lines
	block = "\n".join(lines)
	assert "not published" not in block, block
	assert "no log locator" not in block, block


def test_the_facts_that_were_published_are_all_still_there(world):
	"""Removing the synthetic row must not thin the real inventory: a
	member with facts but no `log` keeps its section and every fact in
	it."""
	runner(world, "ada", "run-1",
	       {"workdir": "/home/op/src/baton",
	        "version": "codex-event-bridge 1.4.0"})
	lines = detail(world)
	assert "Operational diagnostics" in titles(lines), titles(lines)
	assert "/home/op/src/baton" in row_for(lines, "Workdir")
	assert "codex-event-bridge 1.4.0" in row_for(lines, "Version")
	assert row_for(lines, "Log") is None, lines


def test_a_member_that_published_nothing_has_no_diagnostics_section(world):
	"""Acceptance 3's other half: with the synthetic row gone the
	section can now be genuinely empty, and `kv_lines` already drops an
	empty section rather than leaving a heading over nothing.

	The rest of the block is asserted present, so "the section is
	omitted" cannot pass by the details having failed to render."""
	runner(world, "ada", "run-1")
	lines = detail(world)
	assert "Operational diagnostics" not in titles(lines), titles(lines)
	for section in ("Identity and routing", "Workflow", "Runner state",
	                "Last poke answer"):
		assert section in titles(lines), (section, titles(lines))
	assert row_for(lines, "Session") == "session-ada"


def test_a_heading_is_never_left_standing_over_nothing(world):
	"""The same property from the other side: no block anywhere ends on
	a section title with no rows beneath it."""
	runner(world, "ada", "run-1")
	lines = detail(world)
	headings = [number for number, line in enumerate(lines)
	            if line.strip() in titles(lines)
	            and line.startswith("  ") and not line.startswith("    ")]
	for number in headings:
		following = lines[number + 1:number + 2]
		assert following and following[0].startswith("    "), \
			(lines[number], lines[number:number + 2])


# -- members are rendered independently --------------------------------------

def test_one_members_locator_never_reaches_another(world):
	"""Acceptance 3. The two directions are different failures — a
	shared dict would leak the locator INTO the member without one, and
	a shared filter would drop it FROM the member with one — so both
	are asserted, from one authority holding both members at once."""
	runner(world, "ada", "run-1", {"log": LOCATOR})
	runner(world, "grace", "run-2", {"workdir": "/home/op/elsewhere"})
	published = detail(world, "ada")
	silent = detail(world, "grace")
	assert LOCATOR in row_for(published, "Log"), published
	assert row_for(silent, "Log") is None, silent
	assert LOCATOR not in "\n".join(silent), silent
	assert "/home/op/elsewhere" not in "\n".join(published), published
	assert "/home/op/elsewhere" in row_for(silent, "Workdir")


def test_the_order_the_members_are_asked_in_changes_nothing(world):
	"""A leak through renderer state would show up as an answer that
	depends on who was drawn first."""
	runner(world, "ada", "run-1", {"log": LOCATOR})
	runner(world, "grace", "run-2", {"workdir": "/home/op/elsewhere"})
	first = detail(world, "grace")
	detail(world, "ada")
	assert detail(world, "grace") == first


# -- layout stays honest at every width --------------------------------------

@pytest.mark.parametrize("width", [200, 110, 80, 60, 40, 30, 20, 12])
def test_no_width_paints_past_the_edge_without_the_row(world, width):
	"""Acceptance 4. The block got shorter, not narrower — every width
	W184 pinned still holds."""
	runner(world, "ada", "run-1", {"workdir": "/home/op/src/baton"})
	for line in detail(world, width=width):
		assert len(line) <= max(8, width - 1), (width, len(line), line)


@pytest.mark.parametrize("width", [200, 110, 60, 44])
def test_the_value_column_is_still_one_column(world, width):
	"""The removed row was the LONGEST key-value pair in the section.
	Alignment is computed from the widest key, so dropping it is exactly
	the kind of change that can shift a column — this pins that every
	value still starts at one."""
	runner(world, "ada", "run-1", {"workdir": "/home/op/src/baton"})
	columns = set()
	for line in detail(world, width=width):
		if not line.startswith("    ") or line[4:5] == " ":
			continue
		body = line[4:]
		gap = body.find("  ")
		if gap > 0 and body[gap:].strip():
			columns.add(4 + len(body[:gap].ljust(gap))
			            + len(body[gap:]) - len(body[gap:].lstrip()))
	assert len(columns) == 1, (width, sorted(columns))


def test_a_narrow_block_still_carries_every_remaining_key(world):
	runner(world, "ada", "run-1",
	       {"workdir": "/home/op/src/baton", "log": LOCATOR})
	wide = {line.strip().split("  ")[0]
	        for line in detail(world, width=160) if line.startswith("    ")}
	narrow = {line.strip().split("  ")[0]
	          for line in detail(world, width=44) if line.startswith("    ")}
	assert "Log" in wide and "Log" in narrow
	assert wide <= narrow | {""}, sorted(wide - narrow)


def test_a_truncated_screen_still_says_what_it_could_not_show(world):
	"""Acceptance 4's truncated case. Dropping a row makes the block
	shorter, which is the point — but a screen that still cannot hold
	it must keep saying so instead of stopping mid-table and looking
	complete."""
	runner(world, "ada", "run-1", {"log": LOCATOR})
	store = bw.Authority(world["database"])
	try:
		view = Console(store, "lang", "ada", config_path=world["config"])
		while view.tab != "teams":
			view.handle(NEXT_TAB)
		screen = _Screen(height=14, width=110)
		view.render(screen)
		lines = screen.lines()
	finally:
		store.close()
	assert any("more row(s)" in line and "`teams`" in line
	           for line in lines), lines[-4:]


class _Screen:
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


# -- presentation only -------------------------------------------------------

def test_the_projection_still_holds_what_the_adapter_published(world):
	"""The row is a rendering decision. The authority's answer about
	who published which fact must be byte-identical either way — an
	operator asking `teams` still gets the truth the table now spends
	no row on."""
	runner(world, "ada", "run-1", {"workdir": "/home/op/src/baton"})
	runner(world, "grace", "run-2", {"log": LOCATOR})
	before = copy.deepcopy(pj.teams(world["store"], viewer_team="lang",
	                                viewer_member="ada"))
	detail(world, "ada")
	detail(world, "grace")
	assert pj.teams(world["store"], viewer_team="lang",
	                viewer_member="ada") == before
	published = {member["participant"]:
	             {fact["key"] for fact in
	              (member["runtime"] or {}).get("facts") or []}
	             for team in before["teams"] for member in team["members"]}
	assert published["lang.ada"] == {"workdir"}
	assert published["lang.grace"] == {"log"}


def test_the_documentation_states_the_superseding_rule():
	"""Both halves, and neither the retired sentence nor the claim that
	made it a contract."""
	body = (REPO / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	prose = " ".join(body.split())
	assert "A published `Log` appears verbatim with its source and age" \
		in prose, "the published-log rule lost its statement"
	assert "has no `Log` row" in prose, "the omission is undocumented"
	assert "`Log` is always present" not in prose, \
		"the doc still teaches the superseded rule"
	assert "says the adapter has published none" not in prose, \
		"the doc still teaches the superseded rule"


@pytest.mark.skipif(not hasattr(_pty, "fork"), reason="no pty support")
def test_a_real_terminal_paints_neither_row_nor_sentence(world):
	"""What an operator SEES, which is where the sentence was reported
	from — and both halves of the ruling in one session.

	`ada` publishes a workdir and no log; `j` then selects `grace`, who
	publishes a log. The first screen must carry the facts and neither
	the row nor the sentence; the second must carry the locator."""
	runner(world, "ada", "run-1", {"workdir": "/home/op/src/baton"})
	runner(world, "grace", "run-2", {"log": LOCATOR})
	world["store"].close()
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada",
		[(b"]", 0.7), (b"j", 0.7), (b"qy", 0.4)], columns=120, lines=44)
	absent, published = (ptyharness.replay(step, columns=120, lines=44)
	                     for step in steps[:2])
	assert any(line.strip() == "Operational diagnostics"
	           for line in absent), absent
	assert any("/home/op/src/baton" in line for line in absent), absent
	assert "not published" not in "\n".join(absent), absent
	assert not any(line.strip().startswith("Log") for line in absent), \
		[line for line in absent if line.strip().startswith("Log")]
	assert any(line.strip().startswith("Log") and LOCATOR in line
	           for line in published), published
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
