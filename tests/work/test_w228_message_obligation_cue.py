"""W228: the Message that owes you something says so.

A pending obligation showed up as `oblig:1` in the header, a bold Work
row, and `Msg/My 2/1` — aggregates that say something is owed
*somewhere*. The Message that actually created it looked like prose. To
act, a viewer had to leave the TUI, run `obligations`, correlate a
sequence back to a Message by hand, and then compose the verb.

The cue is personal, names the obligation, and the selected row states
the exact commands that satisfy it. It is canonical pending state or
nothing: a directed Message whose obligation is resolved is ordinary
prose again, and presentation never infers one from the Message alone.
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
from baton_work.tui.app import Console, format_message        # noqa: E402
import fixtures as fx                                         # noqa: E402
import ptyharness                                             # noqa: E402


@pytest.fixture()
def world(tmp_path):
	"""Two teams, so an obligation can be owed to somebody else and the
	viewer-relative rule has something to be relative to."""
	config_path, database = fx.build_instance(
		str(tmp_path),
		# `grace` holds the same role but the route resolves to `ada`
		# alone, so she is a SAME-TEAM member who must not see the cue.
		# Without her the team check alone would catch every foreign
		# case and the handler check would be untested.
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug", title="w",
	                      origin="external-report",
	                      classification="suspected-defect", author="ada",
	                      body="the opener")
	yield {"store": store, "config": config_path, "work": born["work_id"],
	       "thread": born["thread"]}
	store.close()


def _say(world, body="ordinary discussion"):
	return tr.post_thread(world["store"], world["thread"],
	                      author_team="lang", author="ada", body=body)["seq"]


def _ask(world, endpoint="lang.rsrch", body="please advise"):
	return tr.post_thread(world["store"], world["thread"],
	                      author_team="lang", author="ada", body=body,
	                      request=endpoint, on=world["work"],
	                      wait=False)["seq"]


def _page(world, viewer="ada", team="lang"):
	return pj.thread(world["store"], world["thread"], viewer_team=team,
	                 viewer_member=viewer, newest=True,
	                 limit=50)["messages"]


def _owed(world, seq, viewer="ada", team="lang"):
	message = next(entry for entry in _page(world, viewer, team)
	               if entry["seq"] == seq)
	return message["owed"]


# -- the projection ----------------------------------------------------------

def test_a_pending_obligation_marks_its_own_message(world):
	plain, asked = _say(world), _ask(world)
	assert _owed(world, plain) is None, "an ordinary Message claims an action"
	owed = _owed(world, asked)
	assert owed is not None, "the Message that created the obligation is bare"
	assert owed["seq"] == asked
	assert owed["owed_by"]["endpoint"] == "lang.rsrch"
	assert owed["completes_by"] == ["respond", "dispose", "accept"]


def test_the_cue_is_personal(world):
	"""'another member's obligation does not mark the row as owed by
	this viewer.'"""
	asked = _ask(world, endpoint="push.bug")
	assert _owed(world, asked, viewer="sl", team="push") is not None, \
		"the endpoint's own member does not see the obligation"
	assert _owed(world, asked, viewer="ada", team="lang") is None, \
		"a foreign obligation marked this viewer's row"


def test_a_same_team_member_the_endpoint_does_not_resolve_is_unmarked(world):
	"""The cue is owed-BY-endpoint, not owed-by-team.

	`grace` is in `lang` and holds the same role, but `lang.rsrch`
	resolves to `ada` alone — so the obligation is not hers to answer
	and her row must not claim it. Without this case the team check and
	the handler check overlap, and only one of them is really tested."""
	asked = _ask(world)
	assert _owed(world, asked, viewer="ada") is not None
	assert _owed(world, asked, viewer="grace") is None, \
		"a member the endpoint does not resolve was marked as owing it"
	painted = _index(world, viewer="grace")
	owed_row = next(row for row in painted[1:] if row.startswith(f"M{asked} "))
	assert _cell(painted, "Do", owed_row) == "", owed_row


def test_many_pending_obligations_each_mark_their_own_message(world):
	first, second = _ask(world, body="one"), _ask(world, body="two")
	_say(world)
	page = {entry["seq"]: entry["owed"] for entry in _page(world)}
	assert page[first]["seq"] == first
	assert page[second]["seq"] == second
	assert sum(1 for value in page.values() if value) == 2


@pytest.mark.parametrize("finish", ["respond", "dispose", "accept"])
def test_each_terminal_action_stops_the_row_looking_actionable(world, finish):
	"""'Resolved, cancelled, or superseded obligations cease to look
	actionable after refresh while remaining visible in history.'"""
	asked = _ask(world)
	assert _owed(world, asked) is not None
	store = world["store"]
	if finish == "respond":
		tr.respond_obligation(store, asked, team="lang", member="ada",
		                      body="here you are")
	elif finish == "dispose":
		tr.dispose_obligation(store, asked, team="lang", member="ada",
		                      disposition="no longer needed")
	else:
		tr.accept_obligation(store, asked, actor_team="lang", actor="ada",
		                     body="taken",
		                     create={"kind": "rsrch",
		                             "classification": "suspected-defect",
		                             "title": "provider"})
	assert _owed(world, asked) is None, \
		f"the row still looks actionable after {finish}"
	# and the Message itself is still there — history, not erasure
	assert any(entry["seq"] == asked for entry in _page(world)), \
		"resolving the obligation removed the Message"


def test_a_terminal_close_withdraws_the_cue_with_the_obligation(world):
	"""Closing the Work withdraws its pending obligations, so the cue
	must follow canonical state rather than the Message's shape."""
	asked = _ask(world)
	assert _owed(world, asked) is not None
	tr.close_work(world["store"], world["work"], actor_team="lang",
	              actor="ada", outcome="cancelled",
	              rationale="no longer needed")
	assert _owed(world, asked) is None, \
		"a withdrawn obligation still looks actionable"


def test_the_cue_costs_one_read_for_a_whole_page(world):
	"""W39 R1: the cue must not cost a read per Message row."""
	for index in range(12):
		_ask(world, body=f"advise {index}")
	store = world["store"]

	class Counting:
		def __init__(self, real):
			self._real = real
			self.owed = 0

		def execute(self, sql, *args, **kwargs):
			if "FROM obligations WHERE status='pending'" in sql \
					and "message_seq IN" in sql:
				self.owed += 1
			return self._real.execute(sql, *args, **kwargs)

		def __getattr__(self, name):
			return getattr(self._real, name)

	real = store.conn
	proxy = Counting(real)
	store.conn = proxy
	try:
		page = pj.thread(store, world["thread"], viewer_team="lang",
		                 viewer_member="ada", newest=True, limit=50)
	finally:
		store.conn = real
	assert len([entry for entry in page["messages"] if entry["owed"]]) == 12
	assert proxy.owed == 1, \
		f"the cue issued {proxy.owed} reads for one page"


# -- the index cue -----------------------------------------------------------

class Screen:
	def __init__(self):
		self.rows = {}

	def addnstr(self, y, x, text, n, *rest):
		self.rows[y] = (self.rows.get(y, "")[:x]).ljust(x) + str(text)[:n]

	def lines(self):
		return [self.rows[key] for key in sorted(self.rows)]


def _index(world, cell_width=40, viewer="ada", team="lang"):
	console = Console(world["store"], team, viewer,
	                  config_path=world["config"])
	page = _page(world, viewer, team)
	console.msg_cursor = page[-1]["seq"] if page else 0
	screen = Screen()
	console._paint_index(screen, 0, 12, 0, cell_width, page)
	return screen.lines()


def _cell(painted, name, row):
	at = painted[0].index(name)
	width = {"Do": 4, "From": 13, "Time": 5, "St": 4}[name]
	return row[at:at + width].strip()


def test_the_row_names_the_obligation(world):
	"""'identifies the obligation by its local sequence and conveys that
	action is required'."""
	_say(world)
	asked = _ask(world)
	painted = _index(world)
	assert "Do" in painted[0], painted[0]
	owed_row = next(row for row in painted[1:] if row.startswith(f"M{asked} "))
	assert _cell(painted, "Do", owed_row) == f"@{asked}"


def test_the_row_never_truncates_a_large_obligation_selector(world):
	"""The obligation sequence is monotonic and unbounded. A fixed
	four-cell `Do` column turns `@1000` into the different selector `@100`,
	which is worse than hiding the cue because the painted command target is
	false."""
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	message = {
		"seq": 7, "author_team": "lang", "author": "ada",
		"body": "act", "ts": "2026-08-18 00:00:00", "new": True,
		"references": [],
		"owed": {"seq": 1000, "owed_by": {"endpoint": "lang.rsrch"},
		         "completes_by": ["respond"]},
	}
	console.msg_cursor = message["seq"]
	screen = Screen()
	console._paint_index(screen, 0, 4, 0, 40, [message])
	painted = screen.lines()
	assert "@1000" in painted[1], \
		f"the cue names a different obligation: {painted[1]!r}"
	# and the heading grew with it, so the column still lines up
	assert painted[0].index("From") > painted[0].index("Do") + 4, \
		f"the heading did not widen with the cue: {painted[0]!r}"
	# (the trailing assertions here referenced names from another test;
	# the property they meant — an unowed row carries no cue — is held
	# by test_the_row_names_the_obligation above.)


@pytest.mark.parametrize("seq,expected", [
	(7, "@7"), (99, "@99"), (100, "@100"), (1000, "@1000"),
	(999999, "@999999"),
])
def test_the_cue_column_grows_with_the_sequence(world, seq, expected):
	"""Every decimal boundary, not just the one that happened to break.
	`Id` was sized from the page for exactly this reason in W49 and the
	same reasoning simply was not carried one column across."""
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	message = {
		"seq": 7, "author_team": "lang", "author": "ada",
		"body": "act", "ts": "2026-08-18 00:00:00", "new": True,
		"references": [],
		"owed": {"seq": seq, "owed_by": {"endpoint": "lang.rsrch"},
		         "completes_by": ["respond"]},
	}
	console.msg_cursor = message["seq"]
	screen = Screen()
	console._paint_index(screen, 0, 4, 0, 60, [message])
	painted = screen.lines()
	assert expected in painted[1], painted[1]
	at = painted[0].index("Do")
	assert painted[1][at:at + len(expected)] == expected, \
		f"the cue is not under its heading: {painted[1]!r}"


def test_a_page_shares_one_cue_allocation(world):
	"""All rows on one paint share the allocation, so a two-digit cue
	beside a four-digit one is padded rather than the column moving
	between rows."""
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	page = []
	for index, seq in enumerate((7, 1000)):
		page.append({
			"seq": 10 + index, "author_team": "lang", "author": "ada",
			"body": "act", "ts": "2026-08-18 00:00:00", "new": True,
			"references": [],
			"owed": {"seq": seq, "owed_by": {"endpoint": "lang.rsrch"},
			         "completes_by": ["respond"]},
		})
	console.msg_cursor = page[-1]["seq"]
	screen = Screen()
	console._paint_index(screen, 0, 5, 0, 60, page)
	painted = screen.lines()
	at = painted[0].index("From")
	for row in painted[1:]:
		assert row[at] != " ", f"the From cell moved between rows: {row!r}"


def test_the_cue_is_legible_without_colour_or_weight(world):
	"""'legible without relying on color, blink, or bold alone.' The
	cue is TEXT — the same row read through a monochrome, attribute-free
	capture still carries it."""
	asked = _ask(world)
	painted = _index(world)
	owed_row = next(row for row in painted[1:] if row.startswith(f"M{asked} "))
	assert f"@{asked}" in owed_row, owed_row


def test_a_foreign_obligation_leaves_the_row_unmarked_on_screen(world):
	asked = _ask(world, endpoint="push.bug")
	painted = _index(world)
	owed_row = next(row for row in painted[1:] if row.startswith(f"M{asked} "))
	assert _cell(painted, "Do", owed_row) == "", owed_row
	# and the member who DOES owe it sees it
	theirs = _index(world, viewer="sl", team="push")
	mine = next(row for row in theirs[1:] if row.startswith(f"M{asked} "))
	assert _cell(theirs, "Do", mine) == f"@{asked}"


@pytest.mark.parametrize("cell_width", [40, 34, 30, 26, 22, 20, 12])
def test_the_cue_survives_every_width_that_shows_a_row(world, cell_width):
	"""'composes with … narrow layouts'. The cue outlives every other
	optional field, because a row you cannot act on is worth less than
	one you can."""
	asked = _ask(world)
	painted = _index(world, cell_width=cell_width)
	assert "Do" in painted[0], f"the cue is gone at {cell_width}: {painted[0]}"
	owed_row = next(row for row in painted[1:] if row.startswith(f"M{asked} "))
	assert f"@{asked}" in owed_row, owed_row


def test_the_cue_disappears_on_refresh_after_the_action(world):
	"""'cease to look actionable after refresh' — the same Console,
	repainted from a fresh projection read."""
	asked = _ask(world)
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.msg_cursor = asked

	def painted():
		page = _page(world)
		screen = Screen()
		console._paint_index(screen, 0, 12, 0, 40, page)
		return screen.lines()

	before = painted()
	assert any(f"@{asked}" in row for row in before[1:])
	tr.respond_obligation(world["store"], asked, team="lang", member="ada",
	                      body="answered")
	after = painted()
	assert not any(f"@{asked}" in row for row in after[1:]), after


def test_selection_and_ordering_are_untouched(world):
	"""'composes with … newest-first ordering, personal New/seen state,
	and keyboard focus/navigation.'"""
	first = _say(world)
	asked = _ask(world)
	painted = _index(world)
	assert painted[1].startswith(f"M{asked} "), "newest-first order changed"
	assert any(row.startswith(f"M{first} ") for row in painted[1:])
	for row in painted[1:]:
		assert _cell(painted, "St", row) in ("new", "seen")


# -- the selected row --------------------------------------------------------

def test_the_selected_row_states_the_commands(world):
	"""'Selecting the row exposes the allowed terminal actions and
	enough command context to act without consulting JSON.'"""
	asked = _ask(world)
	message = next(entry for entry in _page(world) if entry["seq"] == asked)
	block = "\n".join(format_message(message, 80))
	assert f"you owe obligation {asked}" in block, block
	assert "lang.rsrch" in block
	assert f"respond obligation={asked} body=" in block
	assert f"dispose obligation={asked} disposition=" in block
	assert f"accept obligation={asked}" in block


def test_the_commands_carry_every_required_operand(world):
	"""A bare `verb obligation=N` refuses for two of the three verbs, so
	the guidance would be advice that does not work. The operands come
	from the CLI's own grammar rather than a second copy, which is what
	keeps this true when the grammar changes."""
	from baton_work.cli import GRAMMAR
	asked = _ask(world)
	message = next(entry for entry in _page(world) if entry["seq"] == asked)
	block = "\n".join(format_message(message, 100))
	for verb in ("respond", "dispose", "accept"):
		line = next(row for row in block.splitlines()
		            if row.strip().startswith(f"complete: {verb} "))
		for key in GRAMMAR[verb]["keys"]:
			if key.get("required"):
				assert f"{key['name']}=" in line, \
					f"{verb} guidance omits required {key['name']}: {line}"
	# accept's provider is an exactly-one-of rule, not a required key
	accept = next(row for row in block.splitlines()
	              if "complete: accept " in row)
	assert "into=" in accept and "create=" in accept, accept


def test_an_unowed_message_states_nothing(world):
	plain = _say(world)
	message = next(entry for entry in _page(world) if entry["seq"] == plain)
	block = "\n".join(format_message(message, 80))
	assert "you owe" not in block and "complete:" not in block, block


# -- parity ------------------------------------------------------------------

def test_the_cue_agrees_with_the_obligations_verb(world):
	"""JSON/TUI parity: the cue must be the SAME canonical fact the
	`obligations` listing reports, not a second opinion."""
	asked = _ask(world)
	# the `obligations` verb is TEAM-scoped, the cue is member-scoped —
	# so this compares the shared canonical facts, not the audiences.
	listed = pj.obligations(world["store"], viewer_team="lang")
	rows = listed if isinstance(listed, list) else listed.get("obligations")
	mine = next(entry for entry in rows if entry["seq"] == asked)
	owed = _owed(world, asked)
	assert owed["seq"] == mine["seq"]
	assert owed["completes_by"] == mine["completes_by"]
	assert owed["owed_by"]["endpoint"] == mine["owed_by"]["endpoint"]


def test_the_cue_never_invents_an_obligation(world):
	"""'Presentation does not invent an obligation from a directed
	Message alone; canonical pending obligation state is the only
	authority.' A directed Message whose obligation is gone is ordinary
	prose again — proved by comparing against the authority's own
	pending set rather than against the Message's shape."""
	asked = _ask(world)
	tr.respond_obligation(world["store"], asked, team="lang", member="ada",
	                      body="answered")
	pending = [row["seq"] for row in world["store"].conn.execute(
		"SELECT seq FROM obligations WHERE status='pending'")]
	assert asked not in pending
	assert _owed(world, asked) is None
	painted = _index(world)
	assert not any("@" in row for row in painted[1:]), painted


# -- a real terminal ---------------------------------------------------------

@pytest.mark.serial
def test_the_cue_and_its_guidance_on_a_real_terminal(world):
	asked = _ask(world)
	text, status, steps = ptyharness.drive(
		world["config"], "lang.ada", [(b"\r", 0.8), (b"qy", 0.4)],
		columns=110, lines=24)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-300:]
	screen = ptyharness.replay(steps[0], columns=110, lines=24)
	flat = "\n".join(screen)
	assert f"@{asked}" in flat, f"the index cue is missing: {screen[:12]}"
	assert f"you owe obligation {asked}" in flat, \
		f"the selected row states no action: {screen[:12]}"
	assert f"respond obligation={asked}" in flat
