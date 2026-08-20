"""W47: aligned Event rows, and the scheduler history behind them.

The index concatenated `E<seq>`, an unbounded kind, a time and an actor
into one string, so every field after the first started at a different
cell and no column could be scanned. And `work-events` projected claim
intervals but nothing about the queued/active/block/parked episodes
that make up the Work's scheduler history.

The intervals are replayed from the ledger's own `phase_now` records,
which every phase-changing transition writes. Nothing here re-derives an
authority decision, and an event that changes no phase writes no record
— which is why a heartbeat cannot split an episode by construction
rather than by being listed as an exception.
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
from baton_work.tui.app import Console, duration_cell         # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		                        "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


def _make(world, title="w"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]


def _episodes(world, work):
	"""(phase, end_kind, open) per episode, oldest first."""
	events = pj.work_events(world["store"], work)["events"]
	return [(entry["phase_interval"]["phase"],
	         entry["phase_interval"]["end_kind"],
	         entry["phase_interval"]["open"])
	        for entry in events if entry.get("phase_interval")]


# -- the boundary matrix ---------------------------------------------------

def test_creation_opens_the_first_episode(world):
	work = _make(world)
	assert _episodes(world, work) == [("queued", None, True)]


def test_claim_ends_queued_and_opens_active(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert _episodes(world, work) == [("queued", "claim", False),
	                                  ("active", None, True)]


def test_release_ends_active_and_opens_queued(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.release_claim(world["store"], work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="stepping away")
	assert _episodes(world, work)[-2:] == [("active", "release", False),
	                                       ("queued", None, True)]


def test_a_pass_ends_and_reopens(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rsrch", comment="over")
	assert _episodes(world, work)[-2:] == [("active", "pass", False),
	                                       ("queued", None, True)]


def test_a_blocking_request_ends_active_and_opens_waiting(world):
	"""A directed request is also a phase-changing claim release.

	It does not go through ``set_phase`` or ``release_claim``; the request
	transaction moves the Work itself, so that event must carry the phase
	boundary rather than leaving the projection to infer it.
	"""
	work = _make(world)
	thread = pj.work_threads(world["store"], work, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.post_thread(world["store"], thread, author_team="lang", author="ada",
	               body="research this before I continue",
	               request="lang.rsrch", on=work)
	assert _episodes(world, work)[-2:] == [
		("active", "request", False), ("block", None, True)]


def test_an_explicit_park_and_resume_are_two_episodes(world):
	work = _make(world)
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="parked", reason="later")
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="queued")
	assert _episodes(world, work) == [("queued", "set_phase", False),
	                                  ("parked", "set_phase", False),
	                                  ("queued", None, True)]


def test_a_gate_ends_the_episode_and_opens_waiting(world):
	work = _make(world)
	blocker = _make(world, "gate")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	assert _episodes(world, work)[-1] == ("block", None, True)


def test_the_wake_ends_waiting_and_opens_queued(world):
	work = _make(world)
	blocker = _make(world, "gate")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="gate")
	tr.close_work(world["store"], blocker, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert _episodes(world, work)[-2:] == [("block", "wake", False),
	                                       ("queued", None, True)]


def test_an_accept_created_provider_opens_its_first_episode(world):
	"""The accept-create compound act is a second Work creation path."""
	consumer = _make(world, "consumer")
	thread = pj.work_threads(world["store"], consumer, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	asked = tr.post_thread(
		world["store"], thread, author_team="lang", author="ada",
		body="track this separately", request="lang.rsrch", on=consumer,
		wait=False)["seq"]
	accepted = tr.accept_obligation(
		world["store"], asked, actor_team="lang", actor="ada",
		body="accepted as provider", create={
			"kind": "rsrch", "classification": "suspected-defect",
			"title": "provider"})
	assert _episodes(world, accepted["provider"]) == [
		("queued", None, True)]


def test_terminal_close_ends_the_last_episode_and_opens_none(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	episodes = _episodes(world, work)
	assert episodes[-1] == ("active", "close_work", False)
	assert not any(open_ for _phase, _kind, open_ in episodes), \
		"a closed Work still has an open episode"


def test_a_heartbeat_never_splits_an_episode(world):
	"""By construction: a heartbeat records no phase, so it cannot end
	one. Asserted anyway, because it is the property the finding
	names."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	before = _episodes(world, work)
	tr.heartbeat(world["store"], work, actor_team="lang", actor="ada")
	tr.heartbeat(world["store"], work, actor_team="lang", actor="ada")
	assert _episodes(world, work) == before
	events = pj.work_events(world["store"], work)["events"]
	beats = [entry for entry in events if entry["kind"] == "heartbeat"]
	assert beats and not any(entry.get("phase_interval") for entry in beats)


def test_an_episode_appears_exactly_once_in_the_index(world):
	"""The interval rides its ENTRY event only. Claim intervals ride
	both boundaries deliberately; doing that here would print the same
	episode twice."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	# The close matters: for phase intervals the ending event is USUALLY
	# also the next episode's start, so a both-boundary attachment is
	# only reachable at terminal closure — the one event that ends an
	# episode without opening another. Without this the check passes
	# against an implementation that shows the episode twice.
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	events = pj.work_events(world["store"], work)["events"]
	starts = [entry["phase_interval"]["start_seq"]
	          for entry in events if entry.get("phase_interval")]
	assert len(starts) == len(set(starts))
	for entry in events:
		interval = entry.get("phase_interval")
		if interval:
			assert interval["start_seq"] == entry["seq"], \
				"an interval rode an event that did not enter it"


def test_a_completed_episode_never_changes(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	first = pj.work_events(world["store"], work)["events"][0]
	again = pj.work_events(world["store"], work)["events"][0]
	assert first["phase_interval"] == again["phase_interval"]
	assert first["phase_interval"]["open"] is False


def test_an_open_episode_carries_elapsed_seconds(world):
	work = _make(world)
	events = pj.work_events(world["store"], work)["events"]
	interval = events[0]["phase_interval"]
	assert interval["open"] is True
	assert isinstance(interval["elapsed_seconds"], int)
	assert interval["elapsed_seconds"] >= 0


def test_the_projection_carries_no_glyph_or_formatted_timer(world):
	"""JSON owns structured seconds and timestamps; the scale is the
	client's."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	for entry in pj.work_events(world["store"], work)["events"]:
		interval = entry.get("phase_interval")
		if not interval:
			continue
		blob = repr(interval)
		assert "∞" not in blob and ":" not in str(
			interval["elapsed_seconds"])
		assert set(interval) == {
			"phase", "start_seq", "started_at", "end_seq", "end_kind",
			"ended_at", "elapsed_seconds", "open"}


# -- the shared scale ------------------------------------------------------

@pytest.mark.parametrize("seconds,rendered", [
	(None, "-"), (0, "00:00"), (59, "00:59"), (60, "01:00"),
	(5999, "99:59"), (6000, "∞"), (60 * 60 * 24, "∞"),
])
def test_the_duration_cell_reuses_the_held_scale(seconds, rendered):
	assert duration_cell(seconds) == rendered


def test_a_negative_interval_clamps_to_zero(world):
	"""A clock correction must not render a negative timer."""
	assert duration_cell(-5) == "00:00"


# -- the fixed columns -----------------------------------------------------

def _console(world, work):
	console = Console(world["store"], "lang", "ada",
	                  config_path=world["config"])
	console.detail_work = work
	console.mode = "detail"
	console.detail_tab = "events"
	return console


class Screen:
	def __init__(self):
		self.calls = []

	def addnstr(self, y, x, text, *rest):
		self.calls.append((y, x, str(text)))

	def lines(self):
		return [text for _y, _x, text in self.calls]


def _index_rows(world, work, width=110, height=24):
	console = _console(world, work)
	screen = Screen()
	console._render_detail(screen, height, width)
	return [text for text in screen.lines()
	        if text.startswith("EVENT") or text.startswith("E")]


def test_every_row_starts_its_fields_at_the_same_cell(world):
	"""The defect: an unbounded kind moved every later field."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="parked", reason="a much longer event kind test")
	rows = _index_rows(world, work)
	assert len(rows) >= 3, rows
	header, body = rows[0], rows[1:]
	for name in ("KIND", "ACTOR", "TIME", "PHASE", "FOR"):
		start = header.index(name)
		for row in body:
			assert len(row) > start, (name, row)
			# the cell at that offset belongs to that column: it is
			# either content or the padding that keeps it aligned
			assert row[start - 1] == " ", (name, row)


def test_the_phase_and_duration_cells_ride_the_entry_row(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	rows = _index_rows(world, work)
	body = rows[1:]
	assert any("actve" in row for row in body), body
	assert any("queue" in row for row in body), body
	# and a row with no episode says so rather than borrowing one
	tr.heartbeat(world["store"], work, actor_team="lang", actor="ada")
	beat = [row for row in _index_rows(world, work)[1:]
	        if "heartbeat" in row]
	assert beat and beat[0].rstrip().endswith("-"), beat


def test_a_narrow_pane_drops_whole_columns_from_the_right(world):
	"""An entire lower-priority column disappears; the surviving ones
	keep their offsets, because truncating one would move the rest."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	wide = _index_rows(world, work, width=110)
	# narrower than the full column set, so a column must actually go
	narrow = _index_rows(world, work, width=38)
	assert wide and narrow
	assert "FOR" in wide[0] and "FOR" not in narrow[0], narrow[0]
	assert wide[0].index("KIND") == narrow[0].index("KIND"), \
		"a surviving column moved when a lower-priority one was dropped"
	assert len(narrow[0].rstrip()) < len(wide[0].rstrip())


def test_the_highest_priority_columns_survive_the_narrowest_pane(world):
	work = _make(world)
	rows = _index_rows(world, work, width=30)
	assert rows and rows[0].startswith("EVENT")


# -- the invariant behind the two defects above ----------------------------

def _recorded_phase(world, work):
	"""The phase the LEDGER says this Work is in: the last `phase_now`
	record naming it, replayed from the beginning."""
	import json as _json
	phase, seen = None, False
	for row in world["store"].conn.execute(
			"SELECT payload FROM events ORDER BY seq"):
		for entry in (_json.loads(row["payload"]).get("phase_now") or ()):
			if entry.get("work") == work:
				phase, seen = entry["phase"], True
	return phase if seen else "<never recorded>"


def _live_phase(world, work):
	"""The phase the AUTHORITY reports — not the raw row.

	`work.phase` is NOT NULL, so a closed Work's row keeps whatever
	phase it last held; the projection derives the terminal null from
	the status, and that is what every reader sees. Comparing the raw
	column here would fail on every close for a reason no operator can
	observe."""
	return pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")["phase"]


def _agrees(world, work):
	"""The invariant, per Work: what the ledger records and what the row
	holds are the same phase.

	This is the property both W47 defects violated. Each was a
	transition that moved the phase in its own statement — `accept
	create=` and a blocking `request` — and so reached neither
	`set_phase` nor `release_claim`, where the recording lived. The
	replay reconstructs nothing by design, so an unrecorded move is not
	recoverable later: it is absent forever."""
	recorded, live = _recorded_phase(world, work), _live_phase(world, work)
	assert recorded == live, \
		f"{work}: the ledger records {recorded!r}, the row holds {live!r}"


def test_the_ledger_and_the_row_agree_across_every_transition(world):
	"""One scenario driving every phase-moving path there is, checking
	the invariant after each. A future transition that moves the phase
	without recording it fails here whether or not anyone remembers to
	write a test for it."""
	store = world["store"]
	work = _make(world, "subject")
	_agrees(world, work)

	# claim -> active
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	_agrees(world, work)

	# a blocking request -> waiting on an exact obligation
	thread = pj.work_threads(store, work, viewer_team="lang",
	                         viewer_member="ada")["rows"][0]["id"]
	asked = tr.post_thread(store, thread, author_team="lang", author="ada",
	                       body="answer before I continue",
	                       request="lang.rsrch", on=work)["seq"]
	_agrees(world, work)

	# accept create= : the provider is born here, and the consumer moves
	accepted = tr.accept_obligation(
		store, asked, actor_team="lang", actor="ada", body="taken",
		create={"kind": "rsrch", "classification": "suspected-defect",
		        "title": "provider"})
	provider = accepted["provider"]
	_agrees(world, work)
	_agrees(world, provider)

	# the provider runs and closes; closing it wakes the consumer
	tr.claim_work(store, provider, actor_team="lang", actor="ada")
	_agrees(world, provider)
	tr.close_work(store, provider, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="answered")
	_agrees(world, provider)
	_agrees(world, work)

	# park and resume
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	_agrees(world, work)
	tr.set_phase(store, work, phase="parked", actor_team="lang",
	             actor="ada", reason="waiting on the operator")
	_agrees(world, work)
	tr.set_phase(store, work, phase="queued", actor_team="lang",
	             actor="ada", reason="resumed")
	_agrees(world, work)

	# a child gates its parent, and closing the child releases it
	child = tr.create_work(store, team="lang", kind="bug", title="child",
	                       origin="external-report",
	                       classification="suspected-defect", author="ada",
	                       body="b", parent=work)["work_id"]
	_agrees(world, work)
	_agrees(world, child)
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	_agrees(world, child)
	_agrees(world, work)

	# and the terminal close records no phase at all
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	assert _recorded_phase(world, work) is None
	assert _live_phase(world, work) is None


def test_a_dependency_edge_moves_the_ledger_with_the_row(world):
	"""`block`/`unblock` gate a Work from outside its own thread — a
	third path to `waiting` that neither defect covered."""
	store = world["store"]
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="needs the blocker first")
	_agrees(world, work)
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	_agrees(world, blocker)
	_agrees(world, work)


def test_a_pass_moves_the_ledger_with_the_row(world):
	"""`pass` derives the destination phase from the Route, in its own
	threadless event."""
	store = world["store"]
	work = _make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	_agrees(world, work)
	tr.pass_work(store, work, actor_team="lang", actor="ada",
	             to="lang.rsrch", comment="over to you")
	_agrees(world, work)
