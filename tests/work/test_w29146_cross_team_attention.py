"""W29146: a Teams star must lead to the participant that caused it.

`work/records/2026/08/finding-teams-attention-cross-team-findability/`.

THE DEFECT. `[Teams *]` is deployment-global by W2938's ruling -- it appears
when ANY configured participant is claim-overdue -- and `Console.team_rows()`
dropped every non-viewer team in its default mode. So a star could be caused
by a participant the destination view refused to show. The Jobs search could
not find the Work either: W6 scopes search to the viewer's owning team and the
header said only `search: QUERY`, which reads global. What the operator was
left looking at was their own bold row, which is an IDENTITY cue and never the
reason for the star.

THE BOUNDED CORRECTION, from rulings that already exist rather than a new
policy. The star stays deployment-global (W2938); ordinary Work search stays
team-scoped (W6) and now SAYS so; and the already-projected
`pickup.next_work` becomes an explicit cross-team link, which is the
cross-team navigation mechanism W6's own finding names. V12 principal
aggregation stays separate Work: v11 must not guess that two `*.slaw`
spellings are one human.
"""

from __future__ import annotations

import curses
import json as _json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import jsonapi                                 # noqa: E402
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402


HOME = "baton"
AWAY = "pc"
FAR = "web"


def document(threshold=1):
	"""Three teams, each with its own route and its own members.

	DISJOINT ON PURPOSE. The whole finding is about attention that belongs
	to a team the viewer is not in, so a shared route would not reproduce
	it -- the offender has to be somewhere the default roster drops.
	"""
	base = fx.config_document({
		HOME: {"members": {"claude": ["impl"], "codex": ["impl"]},
		       "kinds": ["bug"]},
		AWAY: {"members": {"slaw": ["ops"]}, "kinds": ["bug"]},
		FAR: {"members": {"wren": ["ops"]}, "kinds": ["bug"]},
	})
	base["instance"]["pickup_overdue_seconds"] = threshold
	return base


def build(directory, threshold=1):
	place = os.path.join(directory, "baton.json")
	with open(place, "w", encoding="utf-8") as handle:
		_json.dump(document(threshold), handle, indent=2, sort_keys=True)
	database = lc.init_from_config(
		place, participant=f"{HOME}.claude")["database"]
	return place, database


def offer(store, team, title="needs picking up"):
	"""One open, ready, queued, unclaimed Work on that team's route."""
	return tr.create_work(store, team=team, kind="bug", title=title,
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author=_author(team), body="the opener")["work_id"]


def _author(team):
	return {HOME: "claude", AWAY: "slaw", FAR: "wren"}[team]


@pytest.fixture()
def world(tmp_path):
	place, database = build(str(tmp_path))
	store = bw.Authority(database)
	yield {"config": place, "database": database, "store": store}
	store.close()


def console(world, member="claude"):
	return Console(world["store"], HOME, member,
	               config_path=world["config"])


def overdue_elsewhere(world, team=AWAY):
	"""One overdue participant in `team`, and none in the viewer's own."""
	work = offer(world["store"], team)
	time.sleep(1.2)
	return work


def teams_view(world, member="claude"):
	"""A console with the Teams tab OPENED the way an operator opens it,
	because the entry focus is part of what is under test."""
	view = console(world, member)
	while view.tab != "teams":
		view.handle(ord("]"))
	return view


class Screen:
	"""The painted surface, with attributes kept: bold is a fact here."""

	def __init__(self, height=32, width=120):
		self.height, self.width = height, width
		self.rows, self.calls = {}, []

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows, self.calls = {}, []

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "").ljust(x)
		text = str(text)[:n]
		self.rows[y] = row[:x] + text + row[x + len(text):]
		self.calls.append((text, rest[0] if rest else 0))

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def painted(view, height=32, width=120):
	screen = Screen(height, width)
	view.render(screen)
	return screen


def participants(view):
	return [row["participant"] for row in view.team_rows()]


# -- 1: the star, and the roster it sends the operator to --------------------

def test_a_foreign_overdue_member_stars_the_tab(world):
	"""The star is correct and always was: `teams_need_attention` scans
	every configured team through the same cached roster."""
	overdue_elsewhere(world)
	view = console(world)
	assert view.teams_need_attention()
	assert "[Teams *]" in view.top_tabs(), view.top_tabs()
	assert pj.member_pickup(
		world["store"], AWAY, "slaw", world["store"].clock(),
		pj.pickup_threshold(world["store"]))["state"] == "overdue"


def test_the_default_roster_shows_the_foreign_overdue_row(world):
	"""THE DEFECT. Own team plus the exception, and nothing else from the
	other teams."""
	overdue_elsewhere(world)
	view = teams_view(world)
	seen = participants(view)
	assert f"{AWAY}.slaw" in seen, seen
	# Every own-team member is still there...
	assert {f"{HOME}.claude", f"{HOME}.codex"} <= set(seen), seen
	# ...and the third team, which owes nothing, stays hidden.
	assert not any(one.startswith(f"{FAR}.") for one in seen), seen


def test_the_scope_line_says_why_a_stranger_is_there(world):
	"""A line reading `own team` above a foreign row is the same defect one
	layer down: the operator sees a stranger and is told nothing."""
	overdue_elsewhere(world)
	view = teams_view(world)
	line = next(one for one in painted(view).lines() if one.startswith("teams —"))
	assert "own team + 1 overdue elsewhere" in line, line


def test_no_overdue_anywhere_keeps_the_plain_own_team_scope(world):
	"""The exception is an exception. With nothing overdue the view and its
	scope line are exactly what they were."""
	view = teams_view(world)
	seen = participants(view)
	assert all(one.startswith(f"{HOME}.") for one in seen), seen
	line = next(one for one in painted(view).lines() if one.startswith("teams —"))
	assert line.rstrip().endswith("own team"), line


# -- 2: entry focus lands on a cause -----------------------------------------

def test_opening_a_starred_teams_focuses_the_overdue_member(world):
	"""The marker promises actionable attention; the destination now opens
	on one named cause rather than on the viewer's own row."""
	overdue_elsewhere(world)
	view = teams_view(world)
	assert view._team_selected()["participant"] == f"{AWAY}.slaw"


def test_the_focused_row_shows_its_pickup_and_suggested_work(world):
	"""Focus without the reason would be a cursor, not an answer."""
	work = overdue_elsewhere(world)
	view = teams_view(world)
	body = "\n".join(painted(view).lines())
	assert f"{AWAY}.slaw" in body
	assert "overdue" in body, body
	assert work.rsplit("-", 1)[1] in body, body


def test_an_unstarred_entry_moves_no_cursor(world):
	"""There is no attention to lead anyone to, so inventing a selection
	would be answering a question nobody asked."""
	view = console(world)
	view.team_member = f"{HOME}.codex"
	while view.tab != "teams":
		view.handle(ord("]"))
	assert view._team_selected()["participant"] == f"{HOME}.codex"


def test_an_own_team_cause_is_focused_before_a_foreign_one(world):
	"""The star is deployment-global and own team sorts first, so an
	own-team cause is the one an operator should be looking at."""
	offer(world["store"], HOME)
	offer(world["store"], AWAY)
	time.sleep(1.2)
	view = teams_view(world)
	assert view._team_selected()["participant"].startswith(f"{HOME}.")


# -- 3: one star never conceals a second cause -------------------------------

def test_two_foreign_teams_overdue_are_both_visible(world):
	overdue_elsewhere(world, AWAY)
	offer(world["store"], FAR)
	time.sleep(1.2)
	view = teams_view(world)
	seen = participants(view)
	assert f"{AWAY}.slaw" in seen and f"{FAR}.wren" in seen, seen
	line = next(one for one in painted(view).lines() if one.startswith("teams —"))
	assert "2 overdue elsewhere" in line, line


def test_the_second_cause_is_reachable_by_ordinary_movement(world):
	"""Deterministic focus is only half of it; the other rows have to be
	walkable or the second cause is visible and unusable."""
	overdue_elsewhere(world, AWAY)
	offer(world["store"], FAR)
	time.sleep(1.2)
	view = teams_view(world)
	walked = {view._team_selected()["participant"]}
	for _step in range(len(view.team_rows())):
		view.handle(ord("j"))
		walked.add(view._team_selected()["participant"])
	assert {f"{AWAY}.slaw", f"{FAR}.wren"} <= walked, walked


# -- 4: `t` still browses every team -----------------------------------------

def test_t_exposes_every_team_and_toggles_back(world):
	overdue_elsewhere(world)
	view = teams_view(world)
	view.handle(ord("t"))
	everyone = participants(view)
	assert any(one.startswith(f"{FAR}.") for one in everyone), everyone
	line = next(one for one in painted(view).lines() if one.startswith("teams —"))
	assert "every team" in line, line
	view.handle(ord("t"))
	back = participants(view)
	assert f"{AWAY}.slaw" in back and not any(
		one.startswith(f"{FAR}.") for one in back), back


def test_toggling_back_keeps_a_still_visible_selection(world):
	"""The exception row survives the round trip, so the operator is not
	dropped somewhere else for having looked."""
	overdue_elsewhere(world)
	view = teams_view(world)
	view.team_member = f"{AWAY}.slaw"
	view.handle(ord("t"))
	view.handle(ord("t"))
	assert view._team_selected()["participant"] == f"{AWAY}.slaw"


# -- 5: pending is not attention ---------------------------------------------

def test_a_pending_foreign_pickup_creates_neither_star_nor_row(world, tmp_path):
	"""'A grace period nobody has missed yet is not attention.' The
	exception exists for exactly what the marker promises and no more."""
	slow = tmp_path / "slow"
	slow.mkdir()
	place, database = build(str(slow), threshold=10_000)
	store = bw.Authority(database)
	try:
		offer(store, AWAY)
		view = Console(store, HOME, "claude", config_path=place)
		assert not view.teams_need_attention()
		assert "[Teams]" in view.top_tabs(), view.top_tabs()
		assert not any(one.startswith(f"{AWAY}.")
		               for one in participants(view))
	finally:
		store.close()


# -- 6: identity bold and overdue bold stay separate -------------------------

def test_the_viewer_row_is_bold_without_being_the_cause(world):
	"""The finding's own confusion: the operator reads their own bold row
	as the reason for a star it did not cause."""
	overdue_elsewhere(world)
	view = teams_view(world)
	screen = painted(view)
	bold = {text.strip() for text, attr in screen.calls
	        if attr & curses.A_BOLD}
	assert any(text.startswith(f"{HOME}.claude") for text in bold), bold
	mine = next(one for one in screen.lines()
	            if one.startswith(f"{HOME}.claude "))
	# Bold, and owing nothing -- which is what makes it an identity cue.
	assert "late" not in mine, mine
	theirs = next(one for one in screen.lines()
	              if one.startswith(f"{AWAY}.slaw "))
	assert "late" in theirs, theirs


# -- 7: the explicit suggested-Work link -------------------------------------

def test_enter_opens_the_foreign_suggested_work(world):
	work = overdue_elsewhere(world)
	view = teams_view(world)
	view.handle(curses.KEY_ENTER)
	assert view.tab == "jobs"
	assert view.detail_work == work, view.detail_work

def test_back_returns_to_the_same_teams_selection(world):
	overdue_elsewhere(world)
	view = teams_view(world)
	chosen = view._team_selected()["participant"]
	view.handle(curses.KEY_ENTER)
	view.handle(27)
	assert view.tab == "teams"
	assert view._team_selected()["participant"] == chosen


def test_a_member_with_no_suggestion_advertises_no_enter(world):
	"""A key that does nothing is worse than an absent one: the operator
	learns the wrong thing about the row."""
	view = teams_view(world)
	view.team_member = f"{HOME}.codex"
	footer = [one for one in painted(view).lines() if "j/k select" in one]
	assert footer and "Enter open suggested Work" not in footer[0], footer
	view.handle(curses.KEY_ENTER)
	assert view.tab == "teams"
	assert "no suggested Work" in view.status, view.status


def test_the_footer_offers_enter_when_there_is_a_suggestion(world):
	overdue_elsewhere(world)
	view = teams_view(world)
	footer = [one for one in painted(view).lines() if "j/k select" in one]
	assert footer and "Enter open suggested Work" in footer[0], footer


# -- 8: the exception clears with the pickup ---------------------------------

def test_claiming_the_suggested_work_clears_star_row_and_focus(world):
	"""Under the existing pickup rules, claiming makes the participant
	busy. The marker, the exception row and the focus all derive from the
	same refreshed snapshot, so they move together."""
	work = overdue_elsewhere(world)
	view = teams_view(world)
	assert view._team_selected()["participant"] == f"{AWAY}.slaw"
	tr.claim_work(world["store"], work, actor_team=AWAY, actor="slaw")
	view.tick()
	assert not view.teams_need_attention()
	assert "[Teams]" in view.top_tabs(), view.top_tabs()
	assert f"{AWAY}.slaw" not in participants(view)


def test_a_vanished_exception_falls_back_to_the_viewers_own_row(world):
	"""No stale hidden participant stays selected. The fallback is the
	viewer's own participant, which is the one row this operator can always
	be shown."""
	work = overdue_elsewhere(world)
	view = teams_view(world)
	# ACTUALLY SELECTED, cursor and all. Setting `team_member` alone left
	# `team_cursor` at 0, where the old `min(cursor, len - 1)` fallback
	# happened to answer the same row -- so the mutation that restores it
	# stayed UNSEEN and this case proved nothing about the fallback. The
	# operator this is written for is LOOKING at the exception row, which
	# means the cursor is on it.
	assert view._team_selected()["participant"] == f"{AWAY}.slaw"
	assert view.team_cursor == len(view.team_rows()) - 1
	tr.claim_work(world["store"], work, actor_team=AWAY, actor="slaw")
	view.tick()
	assert view._team_selected()["participant"] == f"{HOME}.claude"
	assert view.team_cursor == 0


def test_another_actionable_work_keeps_the_participant_and_updates_it(world):
	"""'If another actionable Work keeps the pool nonempty, the participant
	and its updated suggestion remain.'"""
	first = overdue_elsewhere(world)
	second = offer(world["store"], AWAY, "the next one")
	view = teams_view(world)
	tr.reroute_work(world["store"], first, actor_team=AWAY, actor="slaw",
	                to=f"{FAR}.bug", reason="handed over")
	view.tick()
	assert f"{AWAY}.slaw" in participants(view)
	row = next(one for one in view.team_rows()
	           if one["participant"] == f"{AWAY}.slaw")
	assert row["pickup"]["next_work"]["work"] == second, row["pickup"]


def test_closing_the_last_suggested_work_clears_the_exception(world):
	work = overdue_elsewhere(world)
	view = teams_view(world)
	tr.claim_work(world["store"], work, actor_team=AWAY, actor="slaw")
	tr.close_work(world["store"], work, actor_team=AWAY, actor="slaw",
	              outcome="satisfying", rationale="done")
	view.tick()
	assert not view.teams_need_attention()
	assert f"{AWAY}.slaw" not in participants(view)


# -- 9: search states its scope ----------------------------------------------

def test_the_search_result_names_the_team_it_searched(world):
	"""Published rather than left to caller knowledge, because the caller
	that most needs it is the one that did not know to ask."""
	overdue_elsewhere(world)
	answer = pj.search(world["store"], "needs", viewer_team=HOME,
	                   viewer_member="claude")
	assert answer["team"] == HOME
	assert answer["rows"] == [], answer["rows"]


def test_the_foreign_work_is_still_not_searchable_and_says_which_team(world):
	"""W6's team-noise boundary HOLDS. This correction makes the scope
	visible; it does not widen the search, because the cross-team route is
	the explicit link in Teams."""
	work = overdue_elsewhere(world)
	answer = pj.search(world["store"], work, viewer_team=HOME,
	                   viewer_member="claude")
	assert answer["rows"] == []
	assert answer["team"] == HOME
	# And the same query inside the owning team does find it, so the empty
	# answer above is about SCOPE rather than about matching.
	theirs = pj.search(world["store"], work, viewer_team=AWAY,
	                   viewer_member="slaw")
	assert [row["id"] for row in theirs["rows"]] == [work]


def test_the_console_renders_the_scope_the_authority_answered(world):
	"""READ, NOT ASSUMED, which is the whole defect one level up.

	The console asks with its own team, so `window["team"]` and
	`self.team` are equal in every ordinary run -- and a console that
	assumed the scope would pass every case that could not tell them
	apart. Measured: the mutation replacing the read with the assumption
	stayed UNSEEN until this case made the authority answer something
	else, which is the only way to prove the header is reporting rather
	than restating.
	"""
	view = console(world)
	real = pj.search

	def answering_elsewhere(*args, **kwargs):
		return {**real(*args, **kwargs), "team": "somewhere-else"}

	pj.search = answering_elsewhere
	try:
		view.search_input = "zzz"
		view.handle(10)
		body = "\n".join(painted(view).lines())
	finally:
		pj.search = real
	assert "search (team somewhere-else):" in body, body
	assert "in team somewhere-else" in body, body


def test_the_console_header_and_empty_copy_name_the_team(world):
	view = console(world)
	view.search_input = "zzz"
	view.handle(10)
	body = "\n".join(painted(view).lines())
	assert f"search (team {HOME}):" in body, body
	assert f"in team {HOME}" in body, body


# -- 10: the published contract ----------------------------------------------

def test_the_projection_minor_advances_for_the_additive_field(world):
	"""Additive: a consumer that ignores `team` reads what it read before,
	and the MINOR moves because a consumer that wants it must know the
	surface exists."""
	assert jsonapi.PROJECTION_VERSION == "12.8"
	envelope = jsonapi.envelope(
		world["store"], participant=f"{HOME}.claude",
		result=pj.search(world["store"], "needs", viewer_team=HOME,
		                 viewer_member="claude"))
	assert envelope["projection_version"] == "12.8"
	assert envelope["result"]["team"] == HOME


def test_a_narrow_terminal_still_paints_the_exception_row(world):
	"""The exception is not a wide-terminal luxury: the operator most
	likely to be lost is the one who cannot see every column."""
	overdue_elsewhere(world)
	view = teams_view(world)
	body = "\n".join(painted(view, height=24, width=60).lines())
	assert f"{AWAY}.slaw" in body, body


def test_the_star_and_the_rows_come_from_one_snapshot(world):
	"""One cached read feeds the marker, the roster and the focus, so they
	cannot describe two authority states."""
	overdue_elsewhere(world)
	view = teams_view(world)
	reads = []
	real = pj.teams

	def counting(*args, **kwargs):
		reads.append(1)
		return real(*args, **kwargs)

	pj.teams = counting
	try:
		view.teams_need_attention()
		view.team_rows()
		view.team_exceptions()
		view._team_scope()
	finally:
		pj.teams = real
	assert reads == [], "the roster was re-read outside the cache"
