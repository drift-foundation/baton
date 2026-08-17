"""W47: the claimant heartbeat and the informational stall alert.

`heartbeat work=Wn` (finding-work-claim-heartbeat, same-schema journal
ruling): a deliberate audited beat by the EXACT current claimant — the
claim event is the initial beat; the committing transaction rechecks
open status and the exact claimant so a racing release/pass/close
refuses the beat without an event. Projection resolves the latest
qualifying beat of the CURRENT claim epoch for the whole window in one
batched read and exposes `heartbeat_at`; clients derive the fixed
six-minute alert (`12:04!` vs `12:04 `) from that fact and a local
clock. Informational only: a stale beat never releases, transfers,
rephases, or admits a second claimant, and the beat itself never
touches change identity, order, phase, messages, New, claim Age, or
the phase-change blink.
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import io
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import (STALL_AFTER_SECONDS, Console,  # noqa: E402
                                held_field)


def field(claimed, beat, now):
	"""The W47-era three-argument spelling over the W226 row field."""
	return held_field({"claimed_at": claimed, "heartbeat_at": beat}, now)
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"],
		                                     "grace": ["dev"]},
		                         "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def make(world, title="w"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")["work_id"]


def row_of(world, work_id):
	return pj.detail(world["store"], work_id, viewer_team="lang",
	                 viewer_member="ada")


def stamp(ts):
	return _dt.datetime.fromisoformat(
		ts.replace("Z", "+00:00")).timestamp()


def test_the_claim_is_the_initial_beat_and_beats_advance_it(world):
	"""heartbeat_at starts as the claim timestamp, advances with each
	accepted beat, never resets claimed_at, and lands one audited
	event naming the exact claimant."""
	store = world["store"]
	work = make(world)
	assert row_of(world, work)["heartbeat_at"] is None
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	claimed = row_of(world, work)
	assert claimed["heartbeat_at"] == claimed["claimed_at"], \
		"the claim is not the initial beat"
	result = tr.heartbeat(store, work, actor_team="lang", actor="ada")
	event = store.conn.execute(
		"SELECT kind, payload FROM events WHERE seq=?",
		(result["seq"],)).fetchone()
	assert event["kind"] == "heartbeat"
	assert _json.loads(event["payload"]) == {"work": work,
	                                         "claimant": "lang.ada"}
	after = row_of(world, work)
	assert stamp(after["heartbeat_at"]) >= stamp(after["claimed_at"])
	assert after["claimed_at"] == claimed["claimed_at"], \
		"a beat reset the claim age"


def test_only_the_exact_claimant_beats(world):
	"""Stricter than route membership: an unclaimed row, a different
	member (even a configured teammate), and a closed row all refuse —
	and a refused beat records no event."""
	store = world["store"]
	work = make(world)
	before = store.conn.execute(
		"SELECT COUNT(*) AS n FROM events").fetchone()["n"]
	with pytest.raises(bw.WorkError, match="unclaimed"):
		tr.heartbeat(store, work, actor_team="lang", actor="ada")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="only the exact current "
	                                       "claimant"):
		tr.heartbeat(store, work, actor_team="lang", actor="grace")
	done = make(world, title="done")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="no claim to keep alive"):
		tr.heartbeat(store, done, actor_team="lang", actor="ada")
	# release wins the race: the beat refuses without an event
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="pause")
	events_now = store.conn.execute(
		"SELECT COUNT(*) AS n FROM events").fetchone()["n"]
	with pytest.raises(bw.WorkError, match="unclaimed"):
		tr.heartbeat(store, work, actor_team="lang", actor="ada")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM events").fetchone()["n"] \
		== events_now, "a refused beat left an event behind"


def test_beats_have_no_semantic_side_effects(world):
	"""No change identity, no reorder, no phase, no message, no New,
	no phase-change blink — the beat is liveness evidence only."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	console.rows()                          # cold blink baseline
	before = row_of(world, work)
	result = tr.heartbeat(store, work, actor_team="lang", actor="ada")
	assert result["operation"] is None
	after = row_of(world, work)
	for field in ("last_change_seq", "last_changed_at", "phase",
	              "status", "current", "next", "ready", "new",
	              "message_count", "priority", "claimed_at"):
		assert after[field] == before[field], field
	console.schedule_refresh()
	console.rows()
	assert console.phase_blink == {}, \
		"a heartbeat armed the phase-change blink"


def test_the_beat_is_epoch_scoped(world):
	"""A beat from an earlier claim never makes a later re-claim look
	healthy: after release + re-claim, heartbeat_at is the NEW claim's
	timestamp, not the old beat."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	old_beat = row_of(world, work)["heartbeat_at"]
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="cycling")
	assert row_of(world, work)["heartbeat_at"] is None
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	fresh = row_of(world, work)
	assert fresh["heartbeat_at"] == fresh["claimed_at"]
	assert stamp(fresh["heartbeat_at"]) >= stamp(old_beat), \
		"the epoch went backwards"
	# and the new epoch's own beat advances it
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	assert stamp(row_of(world, work)["heartbeat_at"]) >= \
		stamp(fresh["heartbeat_at"])


def test_the_window_resolves_in_one_batched_read(world):
	"""The W39/W33 no-N+1 boundary holds: a full tree resolves claim
	AND heartbeat facts in at most one journal statement."""
	store = world["store"]
	for index in range(5):
		work = make(world, title=f"row {index}")
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		tr.heartbeat(store, work, actor_team="lang", actor="ada")
	statements = []
	store.conn.set_trace_callback(statements.append)
	try:
		pj.tree(store, viewer_team="lang", viewer_member="ada")
	finally:
		store.conn.set_trace_callback(None)
	journal_reads = [statement for statement in statements
	                 if "heartbeat" in statement
	                 or "kind='claim'" in statement]
	assert len(journal_reads) <= 1, \
		f"claim/heartbeat projection ran {len(journal_reads)} reads"


def test_replay_and_cli_surface(world):
	"""`heartbeat work=Wn` rides the public grammar with W4 selectors
	and WS-5 replay; the replayed beat commits exactly once."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")

	def run(*argv):
		out, err = io.StringIO(), io.StringIO()
		with contextlib.redirect_stdout(out), \
				contextlib.redirect_stderr(err):
			code = work_cli.main(["--config", world["config"],
			                      "--participant", "lang.ada"]
			                     + list(argv))
		return code, out.getvalue(), err.getvalue()

	short = work.rsplit("-", 1)[1]
	code, out, _err = run("heartbeat", f"work={short}",
	                      "op-id=beat-1")
	assert code == 0
	first = _json.loads(out)["result"]
	code, out, _err = run("heartbeat", f"work={short}",
	                      "op-id=beat-1")
	assert code == 0
	again = _json.loads(out)["result"]
	assert again["operation"]["state"] == "replayed"
	assert again["seq"] == first["seq"]
	beats = store.conn.execute(
		"SELECT COUNT(*) AS n FROM events WHERE kind='heartbeat'"
	).fetchone()["n"]
	assert beats == 1, "the replay duplicated the beat"
	code, _out, err = run("heartbeat", "work=w1")
	assert code == 1 and "is not a Work selector" in err


def test_the_alert_thresholds_and_display(world):
	"""The six-cell field: trailing space while healthy, `!` at six
	silent minutes, cleared by a beat, `-` unclaimed, clock corrections
	clamp healthy; claim Age itself keeps counting."""
	base = "2026-08-16T12:00:00Z"
	origin = stamp(base)
	assert field(None, None, origin) == "-"
	assert field(base, base, origin) == "00:00 "
	just_before = origin + STALL_AFTER_SECONDS - 1
	assert field(base, base, just_before).endswith(" ")
	at_boundary = origin + STALL_AFTER_SECONDS
	assert field(base, base, at_boundary) == "00:06!"
	# a fresh beat clears the alert while the claim age keeps counting
	fresh_beat = "2026-08-16T12:06:00Z"
	assert field(base, fresh_beat, at_boundary) == "00:06 "
	# missing beat falls back to the claim (the initial beat)
	assert field(base, None, at_boundary) == "00:06!"
	# clock correction clamps healthy
	future_beat = "2026-08-16T13:00:00Z"
	assert field(base, future_beat, at_boundary).endswith(" ")
	assert all(len(field(base, base, origin + n)) <= 6
	           for n in (0, 3600, 3600 * 100))


def test_stale_is_informational_never_a_lease(world):
	"""Six silent minutes render `!` and change NOTHING else: the
	claim holds, another claim fails closed naming the claimant, and
	the claimant's own late beat clears the alert."""
	store = world["store"]
	work = make(world, title="long runner")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	row = row_of(world, work)
	late = stamp(row["heartbeat_at"]) + STALL_AFTER_SECONDS + 30
	stale_cell = field(row["claimed_at"], row["heartbeat_at"],
	                       late)
	assert stale_cell.endswith("!")
	assert row["active"] == {"team": "lang", "member": "ada"}, \
		"staleness altered the claim"
	with pytest.raises(bw.WorkError,
	                   match="resolved handler|claimed by"):
		tr.claim_work(store, work, actor_team="lang", actor="grace")
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	fresh = row_of(world, work)
	now = stamp(fresh["heartbeat_at"]) + 1
	assert field(fresh["claimed_at"], fresh["heartbeat_at"],
	                 now).endswith(" "), \
		"the successful beat did not clear the alert"


def test_the_stale_suffix_paints_and_narrow_omits_whole(world):
	"""The painted cell carries the suffix; the Age field still omits
	as ONE whole responsive column; a beat never reorders the row."""
	store = world["store"]
	first = make(world, title="steady")
	second = make(world, title="beating")
	tr.claim_work(store, second, actor_team="lang", actor="ada")
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])
	order_before = [row["id"] for row in console.rows()]

	class Screen:
		def __init__(self):
			self.texts = []

		def addnstr(self, _y, _x, text, *_rest):
			self.texts.append(str(text))

	screen = Screen()
	console._render_table(screen, 24, 110, console.rows())
	beating = next(text for text in screen.texts if "beating" in text)
	assert beating.rstrip().endswith(":00") or \
		beating.rstrip().endswith(":01"), beating
	tr.heartbeat(store, second, actor_team="lang", actor="ada")
	console.schedule_refresh()
	assert [row["id"] for row in console.rows()] == order_before, \
		"a heartbeat reordered the window"
	from baton_work.tui.app import DROP_ORDER
	assert "HELD" in DROP_ORDER


# -- round 2 -----------------------------------------------------------------

def test_discovery_advertises_heartbeat_to_the_exact_claimant(world):
	"""R1: available_transitions offers heartbeat exactly for the
	recorded active claimant — never a teammate, another team's
	viewer, an unclaimed row, or a closed row."""
	store = world["store"]
	work = make(world)
	assert "heartbeat" not in row_of(world, work)[
		"available_transitions"], "an unclaimed row offered a beat"
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	assert "heartbeat" in row_of(world, work)["available_transitions"]
	teammate = pj.detail(store, work, viewer_team="lang",
	                     viewer_member="grace")
	assert "heartbeat" not in teammate["available_transitions"], \
		"a non-claimant teammate was offered the beat"
	done = make(world, title="finished")
	tr.claim_work(store, done, actor_team="lang", actor="ada")
	tr.close_work(store, done, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	closed = row_of(world, done)
	assert closed["available_transitions"] == [], \
		"closure stopped being immutable"


def test_a_non_claimant_handler_is_not_offered_the_beat(tmp_path):
	"""R1's sharp edge: with TWO resolved handlers, the beat is
	advertised to the winner alone — the losing handler keeps release
	but never heartbeat (stricter than handlership)."""
	import json as __json
	from baton_work import lifecycle as lc
	document = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		          "kinds": ["bug"]}})
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "bee"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		__json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	try:
		work = tr.create_work(store, team="lang", kind="bug",
		                      title="shared", origin="external-report",
		                      classification="suspected-defect",
		                      author="ada", body="b")["work_id"]
		tr.claim_work(store, work, actor_team="lang", actor="bee")
		winner = pj.detail(store, work, viewer_team="lang",
		                   viewer_member="bee")
		assert "heartbeat" in winner["available_transitions"]
		loser = pj.detail(store, work, viewer_team="lang",
		                  viewer_member="ada")
		assert "release" in loser["available_transitions"]
		assert "heartbeat" not in loser["available_transitions"], \
			"a non-claimant RESOLVED HANDLER was offered the beat"
	finally:
		store.close()


def test_detail_resolves_the_claim_pair_in_one_read(world):
	"""R2: a single detail read runs the claim/heartbeat journal
	statement at most once — the pair resolves once per row, never
	once per field."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	statements = []
	store.conn.set_trace_callback(statements.append)
	try:
		view = pj.detail(store, work, viewer_team="lang",
		                 viewer_member="ada")
	finally:
		store.conn.set_trace_callback(None)
	journal_reads = [statement for statement in statements
	                 if "kind='claim'" in statement]
	assert len(journal_reads) <= 1, \
		f"one detail ran the journal lookup {len(journal_reads)} times"
	assert view["heartbeat_at"] is not None


def test_the_projection_identifies_the_heartbeat_shape(world):
	"""R3: the additive minor advanced — the envelope announces the
	first projection carrying heartbeat evidence, and a same-major
	demand still succeeds."""
	from baton_work import jsonapi
	# Heartbeat evidence entered at 4.2 and remains part of every later
	# shape; W179's honest-breaking major moved the projection to 5.0
	# (no alias), so the CURRENT same-major demand is 5.x and a stale
	# 4.x demand refuses.
	assert jsonapi.PROJECTION_VERSION == "6.2"
	jsonapi.require_version("6.0")
	with pytest.raises(bw.WorkError, match="not compatible"):
		jsonapi.require_version("4.2")


def test_the_two_writer_race_resolves_fail_closed(world):
	"""R4: an INTERLEAVED competitor, not a sequential one. When the
	release commits first (inside the beat's own write window), the
	beat refuses with no event and no burned operation id; when the
	beat commits first, its event stays history while the release
	clears the live projection — and close, another automatic release
	path, clears it the same way."""
	store = world["store"]
	work = make(world)
	tr.claim_work(store, work, actor_team="lang", actor="ada")

	# release wins: interleave it into the beat's write path
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		tr.release_claim(store, work, actor_team="lang", actor="ada",
		                 expect="lang.ada", reason="raced away")
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped
	events_before = store.conn.execute(
		"SELECT COUNT(*) AS n FROM events").fetchone()["n"]
	with pytest.raises(bw.WorkError, match="no longer claimed"):
		tr.heartbeat(store, work, actor_team="lang", actor="ada",
		             op_id="raced-beat")
	store._write = original
	heartbeats = store.conn.execute(
		"SELECT COUNT(*) AS n FROM events WHERE kind='heartbeat'"
	).fetchone()["n"]
	assert heartbeats == 0, "the losing beat left an event"
	# the operation id was NOT burned: the same id commits fresh after
	# a re-claim
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	result = tr.heartbeat(store, work, actor_team="lang", actor="ada",
	                      op_id="raced-beat")
	assert result["operation"]["state"] == "committed", \
		"the refused race burned the operation id"

	# beat wins: the event is history; release clears the live output
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="pause")
	assert row_of(world, work)["heartbeat_at"] is None, \
		"a released claim kept live heartbeat output"
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM events WHERE kind='heartbeat'"
	).fetchone()["n"] == 1, "history lost the committed beat"
	# close — another automatic clearing path — behaves identically
	other = make(world, title="closing")
	tr.claim_work(store, other, actor_team="lang", actor="ada")
	tr.heartbeat(store, other, actor_team="lang", actor="ada")
	tr.close_work(store, other, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert row_of(world, other)["heartbeat_at"] is None


def test_the_stale_suffix_actually_paints(world, monkeypatch):
	"""R5: the painted table cell itself flips from the reserved blank
	to `!` as the paint clock crosses six silent minutes, and back
	after a successful beat."""
	from baton_work.tui import app as tui_app
	store = world["store"]
	work = make(world, title="stalling")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	claimed = stamp(row_of(world, work)["claimed_at"])
	console = Console(store, "lang", "ada",
	                  config_path=world["config"])

	class Screen:
		def __init__(self):
			self.texts = []

		def addnstr(self, _y, _x, text, *_rest):
			self.texts.append(str(text))

	def cell_at(now):
		monkeypatch.setattr(tui_app._time, "time", lambda: now)
		screen = Screen()
		console._render_table(screen, 24, 110, console.rows())
		return next(text for text in screen.texts
		            if "stalling" in text)

	healthy = cell_at(claimed + STALL_AFTER_SECONDS - 1)
	assert "!" not in healthy, healthy
	stale = cell_at(claimed + STALL_AFTER_SECONDS)
	assert stale.rstrip().endswith("!"), \
		f"the table never painted the stall alert: {stale!r}"
	# the claimant's beat clears the painted alert immediately
	tr.heartbeat(store, work, actor_team="lang", actor="ada")
	console.schedule_refresh()
	beat_ts = stamp(row_of(world, work)["heartbeat_at"])
	recovered = cell_at(beat_ts + 1)
	assert "!" not in recovered, recovered
