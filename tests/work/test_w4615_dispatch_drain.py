"""W4615: deployment-global managed dispatch drain.

`work/records/2026/08/finding-managed-stack-drain/`.

The incident this exists for: an operator waiting to restart after "the
current item" can repeatedly miss the gap, because the moment one handler
relinquishes a claim readiness offers another eligible Work to somebody
else. Drain draws a deterministic boundary instead — claims live at that
instant finish, nothing later is admitted, and the deployment reaches
`paused` when the last one ends.

Drain is LIFECYCLE state, not a Work phase and not an instruction to an
agent. Nothing about any Work changes when the deployment drains.
"""

from __future__ import annotations

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures                                               # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))), "src"))

import json as _json                                          # noqa: E402

import baton_work as bw                                       # noqa: E402
from baton_work import cli                                    # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
from baton_work.authority import WorkError                    # noqa: E402
from baton_work.config import CAPABILITIES                    # noqa: E402


@pytest.fixture()
def world(tmp_path):
	cast = fixtures.build(str(tmp_path / "work.sqlite3"))
	store = bw.Authority(str(tmp_path / "work.sqlite3"))
	# The ruling grants `dispatch` in the ACCEPTED CONFIGURATION. The
	# fixture's document predates the capability, so the grant is written
	# directly here — every case below still exercises the authority's own
	# transactional check against that grant.
	store.conn.execute(
		"INSERT INTO member_capabilities (team, member, capability) "
		"VALUES ('lang', 'ada', 'dispatch')")
	store.conn.commit()
	yield {"store": store, "cast": cast}
	store.close()


def _dispatch(store):
	return pj.dispatch_view(store)


# -- the capability ----------------------------------------------------------

def test_dispatch_is_a_capability_of_its_own(world):
	"""Ruled 2026-08-22: not a Route, not a held role, not the runtime
	action owner, not `recover`, and not `config`."""
	assert "dispatch" in CAPABILITIES
	store = world["store"]
	# `grace` holds no capability at all.
	with pytest.raises(WorkError, match="does not hold the `dispatch`"):
		tr.drain_dispatch(store, actor_team="lang", actor="grace")
	# And neither `config` nor `recover` implies it: `sl` holds `config`
	# in the fixture document.
	store.conn.execute(
		"INSERT INTO member_capabilities (team, member, capability) "
		"VALUES ('lang', 'grace', 'recover')")
	store.conn.commit()
	with pytest.raises(WorkError, match="does not hold the `dispatch`"):
		tr.drain_dispatch(store, actor_team="lang", actor="grace")
	with pytest.raises(WorkError, match="does not hold the `dispatch`"):
		tr.resume_dispatch(store, actor_team="lang", actor="grace")


def test_the_capability_is_checked_in_the_write_transaction(world):
	"""A revoked grant takes effect against the next act, not against the
	next process. Stale memory never preserves authority."""
	store = world["store"]
	store.conn.execute(
		"DELETE FROM member_capabilities WHERE member='ada' "
		"AND capability='dispatch'")
	store.conn.commit()
	with pytest.raises(WorkError, match="does not hold the `dispatch`"):
		tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert _dispatch(store)["mode"] == "running"


# -- the boundary ------------------------------------------------------------

def test_a_fresh_authority_dispatches(world):
	state = _dispatch(world["store"])
	assert state["mode"] == "running"
	assert state["generation"] == 1
	assert state["blockers"] == [] and state["blocking_claims"] == 0


def test_draining_with_nothing_live_pauses_in_the_same_commit(world):
	"""The empty finishing round needs no second act — and must not have
	one, or a reader between them would see `draining` with nothing to
	drain."""
	store = world["store"]
	result = tr.drain_dispatch(store, actor_team="lang", actor="ada",
	                           reason="maintenance")
	assert result["mode"] == "paused"
	assert result["live_claims"] == 0
	state = _dispatch(store)
	assert (state["mode"], state["generation"]) == ("paused", 2)
	kinds = [(row["kind"], row["seq"])
	         for row in pj.dispatch_history(store)["events"]]
	assert [kind for kind, _seq in kinds] == ["pause_reached",
	                                          "drain_requested"]
	# ONE authority instant, recorded as two typed control acts.
	assert kinds[0][1] == kinds[1][1]


def test_no_claim_is_admitted_after_the_boundary(world):
	store, cast = world["store"], world["cast"]
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	with pytest.raises(WorkError, match="managed dispatch is paused"):
		tr.claim_work(store, cast["step_fix"], actor_team="lang",
		              actor="ada")
	# The Work is untouched: drain is lifecycle state, not a Work phase.
	row = store.conn.execute(
		"SELECT phase, handler_team FROM work WHERE id=?",
		(cast["step_fix"],)).fetchone()
	assert row["phase"] == "queued" and row["handler_team"] is None


def test_a_claim_live_at_the_boundary_finishes_normally(world):
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	result = tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert result["mode"] == "draining"
	assert result["live_claims"] == 1
	state = _dispatch(store)
	assert state["blocking_claims"] == 1
	assert state["blockers"][0]["work"] == work
	assert state["blockers"][0]["handler"] == "lang.ada"
	assert state["blockers"][0]["episode_seq"] == fixtures.episode_of(
		store, work)
	# The claimant may still end it, and the ending act reaches paused.
	tr.pass_work(store, work, to="lang.rev", actor_team="lang", actor="ada",
	             comment="handing the finished item on")
	assert _dispatch(store)["mode"] == "paused"


def test_a_pass_may_make_work_ready_without_waking_or_claiming_it(world):
	"""The destination Route is not woken while drain is in effect, and
	nobody there can claim it either."""
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	tr.pass_work(store, work, to="lang.rev", actor_team="lang", actor="ada",
	             comment="ready for review, but not now")
	assert _dispatch(store)["mode"] == "paused"
	woken = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="ada", timeout_seconds=0)
	assert [action for action in woken["actionable"]
	        if action["kind"] == "work"] == []
	with pytest.raises(WorkError, match="managed dispatch is paused"):
		tr.claim_work(store, work, actor_team="lang", actor="ada")


def test_every_handler_clearing_path_can_reach_paused(world):
	"""Not just pass/release/close. `_settle_dispatch` runs at the ONE
	writer boundary precisely because Handler removal is not confined to
	a short list of verbs — a check copied into three of them would
	strand a drain after a legitimate final release."""
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert _dispatch(store)["mode"] == "draining"
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 episode=fixtures.episode_of(store, work),
	                 reason="operator recovery during maintenance")
	assert _dispatch(store)["mode"] == "paused"


def test_a_second_drain_does_not_move_the_boundary(world):
	store = world["store"]
	tr.claim_work(store, world["cast"]["step_fix"], actor_team="lang",
	              actor="ada")
	first = tr.drain_dispatch(store, actor_team="lang", actor="ada")
	with pytest.raises(WorkError, match="already draining"):
		tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert _dispatch(store)["boundary_seq"] == first["boundary_seq"]


def test_an_exact_retry_replays_and_a_conflicting_one_refuses(world):
	store = world["store"]
	first = tr.drain_dispatch(store, actor_team="lang", actor="ada",
	                          reason="maintenance", op_id="drain-1")
	replay = tr.drain_dispatch(store, actor_team="lang", actor="ada",
	                           reason="maintenance", op_id="drain-1")
	assert replay["seq"] == first["seq"]
	assert _dispatch(store)["generation"] == first["generation"]
	with pytest.raises(WorkError):
		tr.drain_dispatch(store, actor_team="lang", actor="ada",
		                  reason="a different reason", op_id="drain-1")


def test_a_claim_racing_drain_is_in_the_round_or_refused_never_after(world):
	"""The property the whole design rests on, proven on TWO connections
	rather than argued.

	Both acts serialize through `BEGIN IMMEDIATE` on the same database,
	so whichever commits second sees the first. There is no third
	outcome — a claim is either inside the boundary set or refused — and
	that is exactly what a projection-level filter could not give,
	because a claim already in flight when drain committed never reads a
	projection again."""
	store, cast = world["store"], world["cast"]
	other = bw.Authority(store.path)
	try:
		for work, drain_first in ((cast["step_fix"], True),
		                          (cast["step_confirm"], False)):
			if drain_first:
				tr.drain_dispatch(store, actor_team="lang", actor="ada")
				with pytest.raises(WorkError, match="managed dispatch is"):
					tr.claim_work(other, work, actor_team="lang",
					              actor="ada")
				assert _dispatch(store)["blocking_claims"] == 0
				tr.resume_dispatch(store, actor_team="lang", actor="ada")
			else:
				tr.claim_work(other, work, actor_team="lang", actor="ada")
				result = tr.drain_dispatch(store, actor_team="lang",
				                           actor="ada")
				assert result["mode"] == "draining"
				assert [row["work"] for row
				        in _dispatch(store)["blockers"]] == [work]
				tr.release_claim(
					other, work, actor_team="lang", actor="ada",
					expect="lang.ada",
					episode=fixtures.episode_of(other, work),
					reason="ending the finishing round")
				assert _dispatch(store)["mode"] == "paused"
				tr.resume_dispatch(store, actor_team="lang", actor="ada")
	finally:
		other.close()


def test_the_boundary_sequence_is_the_drain_mutation_itself(world):
	""""After the boundary" is decided by the same monotonic counter that
	orders every other act, not by a wall clock."""
	store = world["store"]
	result = tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert result["boundary_seq"] == result["seq"]
	assert _dispatch(store)["boundary_seq"] == result["seq"]


# -- resume ------------------------------------------------------------------

def test_resume_is_explicit_audited_and_advances_the_generation(world):
	store, cast = world["store"], world["cast"]
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	before = _dispatch(store)
	result = tr.resume_dispatch(store, actor_team="lang", actor="ada",
	                            reason="maintenance complete")
	assert result["mode"] == "running"
	assert result["generation"] == before["generation"] + 1
	assert _dispatch(store)["actor"] == "lang.ada"
	journal = pj.dispatch_history(store)["events"]
	assert journal[0]["kind"] == "resumed"
	assert journal[0]["reason"] == "maintenance complete"
	# And claims are admitted again.
	tr.claim_work(store, cast["step_fix"], actor_team="lang", actor="ada")


def test_resuming_a_running_deployment_refuses(world):
	with pytest.raises(WorkError, match="already running"):
		tr.resume_dispatch(world["store"], actor_team="lang", actor="ada")


def test_the_control_journal_is_traversable_one_instant_at_a_time(world):
	"""W4615 review [P2]. An empty drain writes TWO events at one authority
	sequence, and the cursor was a sequence with a strict `<` resume — so a
	page size that bisected that pair made the second event unreachable. The
	journal was complete only for callers who happened to choose a page size
	that did not cut through an instant.

	`limit` counts INSTANTS now, and every event at a boundary sequence is
	returned together: an authority instant is indivisible for the reader
	because it is indivisible in the writer."""
	store = world["store"]
	tr.drain_dispatch(store, actor_team="lang", actor="ada")     # + pause
	tr.resume_dispatch(store, actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")     # + pause
	complete = [(row["seq"], row["kind"])
	            for row in pj.dispatch_history(store)["events"]]
	assert len(complete) == 5, complete
	# Newest first, and DETERMINISTIC inside one instant: the pause reads
	# above the drain that caused it.
	for index in range(len(complete) - 1):
		assert complete[index][0] >= complete[index + 1][0]
	shared = [seq for seq, _kind in complete
	          if [entry[0] for entry in complete].count(seq) > 1]
	assert shared, "no instant carried two events, so this proves nothing"
	pair = [kind for seq, kind in complete if seq == shared[0]]
	assert pair == ["pause_reached", "drain_requested"], pair
	# Traversed one INSTANT at a time, every event appears exactly once.
	seen = []
	before = None
	while True:
		page = pj.dispatch_history(store, limit=1, before=before)
		seen.extend((row["seq"], row["kind"]) for row in page["events"])
		if page["next_before"] is None:
			break
		before = page["next_before"]
	assert seen == complete, seen


def test_the_dispatch_view_reads_ONE_authority_snapshot(world, monkeypatch):
	"""W4615 review [P2]. The mode and the blockers were two independent
	SELECTs, so a final pass committing between them returned `draining` with
	zero blocking claims — a tuple the authority never held, because that
	same commit made it `paused`.

	The interleaving is deterministic here: a second connection commits the
	release while the reader is inside its snapshot."""
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	other = bw.Authority(store.path)
	released = []

	# INTERPOSED between the two reads, from a second connection: the
	# blocker query is where the writer is let in. Without one snapshot the
	# mode was read before the commit and the blockers after it.
	original = pj.live_claim_rows

	def interposing(conn, **kwargs):
		if not released:
			released.append(True)
			tr.release_claim(other, work, actor_team="lang", actor="ada",
			                 expect="lang.ada",
			                 episode=fixtures.episode_of(other, work),
			                 reason="the finishing round ends mid-read")
		return original(conn, **kwargs)

	try:
		monkeypatch.setattr(pj, "live_claim_rows", interposing)
		view = pj.dispatch_view(store)
		assert released, "the writer never interposed; this proves nothing"
		assert not (view["mode"] == "draining"
		            and view["blocking_claims"] == 0), \
			f"the view reported draining with nothing left to drain: {view}"
		assert (view["mode"], view["blocking_claims"]) == ("draining", 1), view
	finally:
		monkeypatch.undo()
		other.close()
	# And afterwards the canonical answer is the settled one.
	assert pj.dispatch_view(store)["mode"] == "paused"


def test_wait_derives_its_actions_and_dispatch_from_one_instant(world):
	store, cast = world["store"], world["cast"]
	tr.claim_work(store, cast["step_fix"], actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	answer = pj.wait_actionable(store, viewer_team="lang",
	                            viewer_member="ada", timeout_seconds=0)
	# The finishing Work and the mode that explains why it is the ONLY one
	# come from the same snapshot; a split read could report one without the
	# other.
	assert answer["dispatch"]["mode"] == "draining"
	assert [action["work"] for action in answer["actionable"]
	        if action["kind"] == "work"] == [cast["step_fix"]]
	assert answer["dispatch"]["blocking_claims"] == 1
	assert answer["snapshot_seq"] >= answer["dispatch"]["boundary_seq"]


def test_automatic_pause_uses_the_AUTHORITY_clock(world, monkeypatch):
	"""W4615 review [P2]. `_settle_dispatch` called the private wall clock,
	so under an injected instant the two same-sequence events disagreed —
	the drain at the injected time, the pause at the host's — and the
	singleton inherited the wrong one."""
	import os
	store, cast = world["store"], world["cast"]
	instant = "2099-01-02T03:04:05Z"
	monkeypatch.setenv("BATON_WORK_NOW", instant)
	injected = bw.Authority(store.path)
	try:
		# The EMPTY drain: both events are written at one sequence.
		tr.drain_dispatch(injected, actor_team="lang", actor="ada")
		events = pj.dispatch_history(injected)["events"]
		assert {row["ts"] for row in events} == {instant}, events
		assert pj.dispatch_view(injected)["transitioned_ts"] == instant
		# And a LATER final release, which settles from a different act.
		tr.resume_dispatch(injected, actor_team="lang", actor="ada")
		work = cast["step_fix"]
		tr.claim_work(injected, work, actor_team="lang", actor="ada")
		tr.drain_dispatch(injected, actor_team="lang", actor="ada")
		tr.release_claim(injected, work, actor_team="lang", actor="ada",
		                 expect="lang.ada",
		                 episode=fixtures.episode_of(injected, work),
		                 reason="ending the finishing round")
		view = pj.dispatch_view(injected)
		assert view["mode"] == "paused"
		assert view["transitioned_ts"] == instant
		assert {row["ts"] for row in pj.dispatch_history(injected)["events"]} \
			== {instant}
	finally:
		injected.close()
		os.environ.pop("BATON_WORK_NOW", None)


def test_one_drain_instant_samples_the_authority_clock_once(world):
	"""A same-sequence drain/pause pair is one authority instant, not merely
	two reads from the same clock source. A ticking injected clock exposes the
	difference that the fixed-environment regression cannot."""
	store = world["store"]
	instants = iter(["2099-01-02T03:04:05Z", "2099-01-02T03:04:06Z"])
	store.clock = lambda: next(instants)
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	events = pj.dispatch_history(store)["events"]
	assert {row["kind"] for row in events} == {
		"drain_requested", "pause_reached"}
	assert {row["seq"] for row in events} == {events[0]["seq"]}
	assert {row["ts"] for row in events} == {"2099-01-02T03:04:05Z"}, \
		"one authority instant sampled its injected clock twice"
	assert pj.dispatch_view(store)["transitioned_ts"] == \
		"2099-01-02T03:04:05Z"


def test_a_later_final_release_carries_ITS_act_instant(world):
	"""The other half of the same invariant, and the one a fixed clock
	cannot see. When the finishing round ends at a LATER act, the pause
	belongs to that act — so `pause_reached` and the singleton carry the
	RELEASE's instant, not the drain's, and the two events correctly differ
	because they are two authority instants rather than one."""
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	# Every write takes exactly one sample, so a ticking clock also counts
	# the samples: three writes, three instants, in order.
	instants = iter(["2099-01-02T03:04:05Z", "2099-01-02T03:04:06Z",
	                 "2099-01-02T03:04:07Z", "2099-01-02T03:04:08Z"])
	store.clock = lambda: next(instants)
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	tr.release_claim(store, work, actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 episode=fixtures.episode_of(store, work),
	                 reason="ending the finishing round")
	events = {row["kind"]: row for row in pj.dispatch_history(store)["events"]}
	assert events["drain_requested"]["ts"] == "2099-01-02T03:04:05Z"
	# The release is the SECOND write, so the settlement it completes is
	# stamped with the release's own sample — not a third reading taken
	# inside it, and not the drain's.
	assert events["pause_reached"]["ts"] == "2099-01-02T03:04:06Z"
	assert events["pause_reached"]["seq"] > events["drain_requested"]["seq"]
	view = pj.dispatch_view(store)
	assert view["mode"] == "paused"
	assert view["transitioned_ts"] == "2099-01-02T03:04:06Z"


def test_the_sampled_instant_does_not_outlive_its_write(world):
	"""Pinning an instant for the duration of a write is only safe if it is
	cleared however that write ends. A leaked instant would be read by the
	NEXT act as its own — the same defect with a longer window — and a write
	that RAISED would leak it most easily."""
	store, cast = world["store"], world["cast"]
	instants = iter(["2099-01-02T03:04:05Z", "2099-01-02T03:04:06Z",
	                 "2099-01-02T03:04:07Z"])
	store.clock = lambda: next(instants)
	# A refused mutation: draining twice. It samples, then raises.
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError):
		tr.drain_dispatch(store, actor_team="lang", actor="ada")
	# Outside a write there is no act to timestamp, and `instant()` says so
	# rather than quietly answering with a fresh reading.
	with pytest.raises(bw.WorkError) as refusal:
		store.instant()
	assert "write in progress" in str(refusal.value)
	# The next act gets its OWN instant, which is the third sample — the
	# refused write consumed the second and kept none of it.
	tr.resume_dispatch(store, actor_team="lang", actor="ada")
	assert pj.dispatch_view(store)["transitioned_ts"] == \
		"2099-01-02T03:04:07Z"


# -- what a managed client is told -------------------------------------------

def test_managed_delivery_is_filtered_and_the_board_is_not(world):
	"""Drain suppresses model WAKES, never visibility. The operator's
	Inbox and personal projection keep every obligation and poke."""
	store, cast = world["store"], world["cast"]
	# ada resolves three routed Work rows before anything is claimed.
	before = [action["work"] for action in pj.participant_actions(
		store, viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "work"]
	assert len(before) > 1
	tr.claim_work(store, cast["step_fix"], actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	# MANAGED delivery gives her only the one she is finishing.
	mine = pj.wait_actionable(store, viewer_team="lang",
	                          viewer_member="ada", timeout_seconds=0)
	assert [action["work"] for action in mine["actionable"]
	        if action["kind"] == "work"] == [cast["step_fix"]]
	assert mine["dispatch"]["mode"] == "draining"
	# The UNFILTERED participant projection still shows her the rest, so
	# the Inbox and the personal counters are unchanged by a lifecycle
	# state. Drain suppresses model wakes, never visibility.
	board = [action["work"] for action in pj.participant_actions(
		store, viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "work"]
	assert board == before, \
		"the human board lost rows to a lifecycle state"
	# And a participant with nothing to finish is told so IMMEDIATELY,
	# with the reason attached, rather than blocking out its timeout and
	# reading as ordinary idleness.
	quiet = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="grace", timeout_seconds=5)
	assert quiet["actionable"] == []
	assert quiet["timed_out"] is False, \
		"a drained deployment must not look like an idle one"
	assert quiet["dispatch"]["mode"] == "draining"


def test_paused_delivers_nothing_that_spends_a_turn(world):
	store = world["store"]
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	assert _dispatch(store)["mode"] == "paused"
	for member in ("ada", "grace"):
		answer = pj.wait_actionable(store, viewer_team="lang",
		                            viewer_member=member, timeout_seconds=0)
		assert [action for action in answer["actionable"]
		        if action["kind"] != "runtime_refresh"] == []
		assert answer["dispatch"]["mode"] == "paused"


def test_home_and_wait_agree_about_one_instant(world):
	store = world["store"]
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	board = pj.home(store, viewer_team="lang", viewer_member="ada")
	answer = pj.wait_actionable(store, viewer_team="lang",
	                            viewer_member="ada", timeout_seconds=0)
	assert board["dispatch"]["mode"] == answer["dispatch"]["mode"]
	assert board["dispatch"]["generation"] == \
		answer["dispatch"]["generation"]


def test_blocker_truncation_is_explicit(world):
	"""A silently cut list reads as "these are all of them", which for an
	operator waiting to restart is the one wrong answer."""
	store, cast = world["store"], world["cast"]
	tr.claim_work(store, cast["step_fix"], actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	full = pj.dispatch_view(store)
	assert full["blockers_truncated"] is False
	bounded = pj.dispatch_view(store, limit=0)
	assert bounded["blocking_claims"] == 1
	assert bounded["blockers"] == []
	assert bounded["blockers_truncated"] is True


# -- restart -----------------------------------------------------------------

@pytest.mark.parametrize("finish", [False, True])
def test_restart_reconstructs_the_mode_from_the_authority(world, finish):
	"""Process memory decides nothing: reopening the same database is
	the whole recovery path."""
	store, cast = world["store"], world["cast"]
	if not finish:
		tr.claim_work(store, cast["step_fix"], actor_team="lang",
		              actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	expected = pj.dispatch_view(store)
	path = store.path
	store.close()
	reopened = bw.Authority(path)
	try:
		after = pj.dispatch_view(reopened)
		assert after["mode"] == expected["mode"]
		assert after["generation"] == expected["generation"]
		assert after["boundary_seq"] == expected["boundary_seq"]
		assert after["blocking_claims"] == expected["blocking_claims"]
		if not finish:
			with pytest.raises(WorkError, match="managed dispatch is"):
				tr.claim_work(reopened, cast["lang42"], actor_team="lang",
				              actor="ada")
	finally:
		reopened.close()
	world["store"] = bw.Authority(path)


def test_a_failed_runtime_never_retires_a_canonical_blocker(world):
	"""Adapter telemetry is not lifecycle authority. A blocker whose
	runner is failed still prevents pause, exactly as one whose runner is
	healthy does."""
	store, cast = world["store"], world["cast"]
	work = cast["step_fix"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	tr.runtime_start(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", adapter="acp")
	tr.runtime_state(store, actor_team="lang", actor="ada",
	                 incarnation="run-1", state="failed", cause="internal")
	state = _dispatch(store)
	assert state["mode"] == "draining"
	assert [row["work"] for row in state["blockers"]] == [work]


# -- the public grammar ------------------------------------------------------

def _run(capsys, config, *argv, participant="lang.ada", expect_ok=True):
	code = cli.main(["--config", config, "--participant", participant]
	                + list(argv))
	captured = capsys.readouterr()
	if expect_ok:
		assert code == 0, captured.err
		return _json.loads(captured.out)
	assert code == 1, captured.out
	return _json.loads(captured.err)


def test_the_public_grammar_carries_drain_status_and_resume(world, capsys):
	"""The whole control surface through the key=value grammar an
	operator and an agent actually drive."""
	config = world["cast"]["config_path"]
	state = _run(capsys, config, "dispatch")["result"]
	assert state["mode"] == "running"
	drained = _run(capsys, config, "drain", "reason=host maintenance")
	assert drained["result"]["mode"] == "paused"
	# Status is readable by a participant holding NO capability at all:
	# the ruling makes changing the mode privileged and reading it not,
	# because a participant that cannot tell why it is not being woken
	# has to guess.
	seen = _run(capsys, config, "dispatch", participant="lang.grace")
	assert seen["result"]["mode"] == "paused"
	assert seen["projection_version"] == "12.7"
	refused = _run(capsys, config, "resume", participant="lang.grace",
	               expect_ok=False)
	assert "does not hold the `dispatch`" in refused["error"]
	journal = _run(capsys, config, "dispatch", "history=true")["result"]
	assert [row["kind"] for row in journal["events"]] == [
		"pause_reached", "drain_requested"]
	assert journal["events"][1]["reason"] == "host maintenance"
	assert journal["events"][1]["actor"] == "lang.ada"
	resumed = _run(capsys, config, "resume")["result"]
	assert resumed["mode"] == "running"


# -- the lifecycle manager ---------------------------------------------------
#
# `tools/infra.py` learns drain, resume and dispatch status at manifest
# version 2, through ONE explicitly named control triple. It never reaches
# into the authority itself — a second writer would be a second authority —
# and it never infers the identity from a service's argv, which is the
# configuration ambiguity this manager exists to prevent.

CONTROLLER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))), "tools", "infra.py")


def _manifest(mailbox, control=None, version=1):
	import json
	document = {"version": version, "services": [
		{"name": "quiet", "command": ["/bin/sleep", "3600"]}]}
	if control is not None:
		document["control"] = control
	os.makedirs(mailbox, exist_ok=True)
	with open(os.path.join(mailbox, "infra.json"), "w",
	          encoding="utf-8") as handle:
		json.dump(document, handle, indent=2)
		handle.write("\n")
	return mailbox


def _infra(command, mailbox, *extra):
	import subprocess
	return subprocess.run(
		[sys.executable, CONTROLLER, command, str(mailbox), *extra],
		capture_output=True, text=True, timeout=60)


def _canonical_binary(tmp_path):
	"""A canonical Baton entry point for the manifest to NAME.

	The lifecycle manager runs whatever binary the control triple names,
	with `--config`, `--participant` and the operands appended. This shim
	is that binary, running the CLI from source — so these cases test
	the manager's own contract (build the argv, read the JSON, refuse on
	an error document) without needing a packaged artifact, and without
	the manager ever touching the authority itself."""
	repo = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	path = tmp_path / "baton-shim"
	path.write_text(
		"#!/bin/sh\n"
		f"exec {sys.executable} -c "
		f"'import sys; sys.path.insert(0, \"{repo}/src\"); "
		f"from baton_work.cli import main; sys.exit(main())' \"$@\"\n",
		encoding="utf-8")
	os.chmod(path, 0o755)
	return str(path)


def test_a_version_1_manifest_has_no_dispatch_control(world, tmp_path):
	"""Version 1 stays loadable and simply cannot drain: the manager
	refuses with an actionable message rather than guessing an identity
	out of a service's argv."""
	mailbox = _manifest(str(tmp_path / "v1"))
	done = _infra("drain", mailbox)
	assert done.returncode == 2
	assert "version 1 and names no control identity" in done.stderr
	# And `stop` is untouched at version 1 — the immediate stop must keep
	# working when the authority cannot be reached at all.
	assert _infra("stop", mailbox).returncode == 0


def test_manifest_version_2_requires_the_explicit_control_triple(tmp_path):
	mailbox = _manifest(str(tmp_path / "v2-bare"), version=2)
	done = _infra("status", mailbox)
	assert done.returncode == 2
	assert "manifest.control is required at version 2" in done.stderr
	mailbox = _manifest(str(tmp_path / "v2-relative"), version=2,
	                    control={"binary": "baton", "config": "/tmp/x.json",
	                             "participant": "lang.ada"})
	assert _infra("status", mailbox).returncode == 2
	mailbox = _manifest(str(tmp_path / "v2-participant"), version=2,
	                    control={"binary": "/bin/true",
	                             "config": "/tmp/x.json",
	                             "participant": "not-a-participant"})
	done = _infra("status", mailbox)
	assert done.returncode == 2
	assert "control.participant must be team.member" in done.stderr


def test_the_manager_drains_and_resumes_through_the_named_identity(world,
                                                                  tmp_path):
	"""And status is reported even with every service stopped: the mode
	lives in the authority, so "the stack is down" and "the deployment is
	paused" are different facts an operator must be able to tell apart
	before starting anything."""
	import json
	store, cast = world["store"], world["cast"]
	mailbox = _manifest(str(tmp_path / "v2-live"), version=2, control={
		"binary": _canonical_binary(tmp_path),
		"config": cast["config_path"],
		"participant": "lang.ada"})
	seen = json.loads(_infra("dispatch", mailbox).stdout)
	assert seen["dispatch"]["mode"] == "running"
	done = _infra("drain", mailbox, "--reason", "host maintenance")
	assert done.returncode == 0, done.stderr
	assert json.loads(done.stdout)["dispatch"]["mode"] == "paused"
	assert _dispatch(store)["mode"] == "paused"
	done = _infra("resume", mailbox, "--reason", "done")
	assert done.returncode == 0, done.stderr
	assert _dispatch(store)["mode"] == "running"
	journal = pj.dispatch_history(store)["events"]
	assert journal[0]["reason"] == "done"
	assert journal[0]["actor"] == "lang.ada"


def test_the_manager_refuses_when_the_named_participant_may_not(world,
                                                               tmp_path):
	"""The manager names WHO to ask as; the authority decides whether
	they may. A manifest naming a participant without the capability is
	refused by the authority, and the refusal reaches the operator."""
	store, cast = world["store"], world["cast"]
	mailbox = _manifest(str(tmp_path / "v2-unauth"), version=2, control={
		"binary": _canonical_binary(tmp_path),
		"config": cast["config_path"],
		"participant": "lang.grace"})
	done = _infra("drain", mailbox)
	assert done.returncode == 2
	assert "does not hold the `dispatch`" in done.stderr
	assert _dispatch(store)["mode"] == "running"


def test_graceful_stop_refuses_before_signalling_anything(world, tmp_path):
	"""The whole point: it reads the canonical state and refuses BEFORE
	touching a service, so a refused graceful stop leaves the deployment
	exactly as it found it."""
	store, cast = world["store"], world["cast"]
	mailbox = _manifest(str(tmp_path / "v2"), version=2, control={
		"binary": _canonical_binary(tmp_path),
		"config": cast["config_path"],
		"participant": "lang.ada"})
	tr.claim_work(store, cast["step_fix"], actor_team="lang", actor="ada")
	tr.drain_dispatch(store, actor_team="lang", actor="ada")
	done = _infra("stop-drained", mailbox)
	assert done.returncode == 2
	assert "not paused" in done.stderr and "Nothing was signalled" in done.stderr
	# End the finishing round; now it is allowed.
	tr.release_claim(store, cast["step_fix"], actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 episode=fixtures.episode_of(store, cast["step_fix"]),
	                 reason="maintenance")
	assert _dispatch(store)["mode"] == "paused"
	assert _infra("stop-drained", mailbox).returncode == 0
	# Start never resumes: a deployment paused for maintenance that began
	# dispatching because its services came back would be the opposite of
	# a boundary.
	assert _dispatch(store)["mode"] == "paused"
