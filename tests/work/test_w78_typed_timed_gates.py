"""W78: blocked Work names what holds it, and times that.

Two unclaimed rows in the same phase ran different clocks. W4 had a
historical `handoff_at` so its Held advanced; W5 had none so it showed
`-`. Nothing visible on either row explained the difference, and no
client could invent the missing origin: the authority had never
committed one.

The fix is one `block` phase with a typed, timed, displayed GATE. `Wait`
names it — `W…` for a Work, `M…` for the source Message of a directed
obligation — and Held measures that gate's episode. Every advancing
clock is now explainable from the row it sits on: `Handler` names active
execution, `Wait` names blocked execution, and everything else shows no
clock at all.

The episode is the delicate part. It starts when the DISPLAYED gate
becomes the one holding the Work and it must not restart for anything
else: not a second blocker arriving behind the first, not a heartbeat,
not a refresh, not an unrelated message.
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
from baton_work.tui.app import blocker_cue, held_field        # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"], "bee": ["dev"]},
		                        "kinds": ["bug", "rsrch"]}})
	store = bw.Authority(database)
	yield {"store": store, "config": config_path}
	store.close()


def _make(world, title="w", parent=None):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b", parent=parent)["work_id"]


def _row(world, work):
	return pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="ada")


def _gate(world, work):
	return _row(world, work)["gate"]


def _thread(world, work):
	return pj.work_threads(world["store"], work, viewer_team="lang",
	                       viewer_member="ada")["rows"][0]["id"]


def _epoch(value):
	import datetime as _dt
	return _dt.datetime.fromisoformat(
		value.replace("Z", "+00:00").replace(" ", "T")).timestamp()


# -- the acceptance boundary, clause by clause -----------------------------

def test_a_first_dependency_blocks_and_releases_without_a_clock(world):
	"""'A queued or active Work acquiring its first dependency enters
	`block`, releases any claimant atomically, displays `W…`' — and,
	W12 superseding this Work's own ruling, does NOT start Held.

	Everything the gate episode is for survives the change; only the
	Handler column stops borrowing it."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert _row(world, work)["phase"] == "active"
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="needs it first")
	row = _row(world, work)
	assert row["phase"] == "block"
	assert row["handler"] is None, "the late gate did not release the claim"
	gate = row["gate"]
	assert gate["kind"] == "work" and gate["work"] == blocker
	assert gate["selector"] == blocker.rsplit("-", 1)[1]
	assert gate["started_at"] is not None, \
		"the episode start is the evidence and must survive W12"
	# W12: the released claim is precisely why there is no Held. The row
	# has no Handler, so 45 seconds later it still shows nothing.
	assert held_field(row, _epoch(gate["started_at"]) + 45) == "-"


def test_a_non_displayed_dependency_does_not_reset_the_episode(world):
	"""'Adding a non-displayed dependency does not reset the displayed
	gate episode.' This is the whole reason the episode is committed
	rather than derived: a second blocker is not a new wait."""
	work = _make(world, "consumer")
	first, second = _make(world, "first"), _make(world, "second")
	tr.add_dependency(world["store"], work, first, actor_team="lang",
	                  actor="ada", rationale="a")
	before = _gate(world, work)
	tr.add_dependency(world["store"], work, second, actor_team="lang",
	                  actor="ada", rationale="b")
	after = _gate(world, work)
	assert after == before, \
		f"a second blocker restarted the episode: {before} -> {after}"
	assert after["work"] == first, "the displayed gate moved"


def test_closing_the_displayed_gate_selects_the_next_and_resets(world):
	"""'Closing or removing the displayed dependency selects the next
	blocker and resets Held even though phase remains `block`.'"""
	work = _make(world, "consumer")
	first, second = _make(world, "first"), _make(world, "second")
	for blocker in (first, second):
		tr.add_dependency(world["store"], work, blocker, actor_team="lang",
		                  actor="ada", rationale="r")
	before = _gate(world, work)
	tr.close_work(world["store"], first, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	after = _row(world, work)
	assert after["phase"] == "block", "the Work woke on a partial gate"
	assert after["gate"]["work"] == second, "the next blocker is not displayed"
	assert after["gate"]["started_seq"] > before["started_seq"], \
		"the new gate reused the old episode's start"


def test_removing_the_displayed_gate_selects_the_next_and_resets(world):
	"""The same clause through the correction path rather than a close:
	an edge authoritatively removed is not a satisfied gate, and both
	have to move the episode."""
	work = _make(world, "consumer")
	first, second = _make(world, "first"), _make(world, "second")
	for blocker in (first, second):
		tr.add_dependency(world["store"], work, blocker, actor_team="lang",
		                  actor="ada", rationale="r")
	before = _gate(world, work)
	tr.remove_dependency(world["store"], work, first, actor_team="lang",
	                     actor="ada", rationale="the edge was mistaken")
	after = _gate(world, work)
	assert after["work"] == second
	assert after["started_seq"] > before["started_seq"]


def test_clearing_the_last_gate_queues_the_work_and_stops_the_clock(world):
	"""'clearing the last one queues the Work and stops Held.'"""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	tr.close_work(world["store"], blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	row = _row(world, work)
	assert row["phase"] == "queued" and row["gate"] is None
	assert held_field(row, _epoch(row["last_changed_at"]) + 60) == "-"


def test_a_blocking_request_enters_a_message_gate_at_publication(world):
	"""'A blocking directed request enters `block M…` at publication.'"""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada",
	                       body="advise before I continue",
	                       request="lang.rsrch", on=work)["seq"]
	row = _row(world, work)
	assert row["phase"] == "block" and row["handler"] is None
	gate = row["gate"]
	assert gate["kind"] == "message"
	assert gate["message"] == asked and gate["selector"] == f"M{asked}"
	assert gate["obligation"]["seq"] == asked
	assert gate["obligation"]["status"] == "pending"
	assert gate["obligation"]["endpoint"] == "lang.rsrch"
	assert gate["started_at"] is not None


def test_answering_retargets_to_a_work_gate_with_a_new_episode(world):
	"""'Its response or disposition either queues the Work or retargets
	it to `block W…` with a new episode start.'"""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="acquired independently")
	before = _gate(world, work)
	assert before["kind"] == "message", \
		"a blocker behind the obligation captured the cue"
	tr.respond_obligation(world["store"], asked, team="lang", member="ada",
	                      body="here is the advice")
	after = _row(world, work)
	assert after["phase"] == "block", \
		"answering released Work another gate still holds"
	assert after["gate"]["kind"] == "work" and after["gate"]["work"] == blocker
	assert after["gate"]["started_seq"] > before["started_seq"]


def test_answering_the_only_gate_queues_the_work(world):
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.respond_obligation(world["store"], asked, team="lang", member="ada",
	                      body="answered")
	row = _row(world, work)
	assert row["phase"] == "queued" and row["gate"] is None


def test_a_disposal_moves_the_gate_like_a_response(world):
	"""Disposition is the other way an obligation completes, and the
	ruling names both."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.dispose_obligation(world["store"], asked, team="lang", member="ada",
	                      disposition="no longer needed")
	row = _row(world, work)
	assert row["phase"] == "queued" and row["gate"] is None


@pytest.mark.parametrize("act", ["heartbeat", "message", "priority",
                                 "classification", "refresh"])
def test_unrelated_events_do_not_reset_the_episode(world, act):
	"""'Refresh, heartbeat, priority/category edits, ordinary Messages,
	and other unrelated events do not reset the gate episode.'

	Parametrized so a future act that quietly touches the row fails on
	its own line rather than hiding inside a compound test.

	The cases differ in how load-bearing they are, which is worth
	knowing: `priority` and `classification` DO stamp the Work row, so
	they are the ones that catch a retarget wired into the row-change
	path. `message` and `heartbeat` never touch this row at all — they
	are guards against a future change that starts touching it, not
	proofs about today's code."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	before = _gate(world, work)
	store = world["store"]
	if act == "heartbeat":
		# a heartbeat needs a claimant, and blocked Work has none — the
		# closest reachable unrelated act is a beat on OTHER Work in the
		# same authority, which must not disturb this row either.
		other = _make(world, "other")
		tr.claim_work(store, other, actor_team="lang", actor="ada")
		tr.heartbeat(store, other, actor_team="lang", actor="ada")
	elif act == "message":
		tr.post_thread(store, _thread(world, work), author_team="lang",
		               author="ada", body="ordinary discussion")
	elif act == "priority":
		tr.prioritize(store, work, actor_team="lang", actor="ada",
		              priority="high")
	elif act == "classification":
		tr.classify(store, work, actor_team="lang", actor="ada",
		            classification="confirmed-defect")
	after = _gate(world, work)
	assert after == before, \
		f"{act} restarted the gate episode: {before} -> {after}"


def test_claim_and_the_non_timing_states(world):
	"""'Claim starts active Held from `claimed_at`; release/pass without
	a gate, queued, parked, unclaimed handoff, and terminal states
	render `-`.'"""
	work = _make(world)
	queued = _row(world, work)
	assert held_field(queued, _epoch(queued["last_changed_at"]) + 90) == "-"

	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	claimed = _row(world, work)
	assert held_field(claimed, _epoch(claimed["claimed_at"]) + 30) == "00:30"

	tr.release_claim(world["store"], work, actor_team="lang", actor="ada",
	                 expect="lang.ada", reason="handing it back")
	released = _row(world, work)
	assert released["phase"] == "queued"
	assert held_field(released, _epoch(released["last_changed_at"]) + 30) == "-"

	fx.hand_off(world["store"], work, actor_team="lang", actor="ada",
	             to="lang.rsrch", comment="over to you")
	passed = _row(world, work)
	assert passed["handoff_at"] is not None, "the handoff is still history"
	assert held_field(passed, _epoch(passed["handoff_at"]) + 30) == "-", \
		"an unclaimed handoff started a clock the row cannot explain"

	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="parked", reason="deferred")
	parked = _row(world, work)
	assert held_field(parked, _epoch(parked["last_changed_at"]) + 90) == "-"

	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="queued", reason="resumed")
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	closed = _row(world, work)
	assert closed["phase"] is None and closed["gate"] is None
	assert held_field(closed, _epoch(closed["last_changed_at"]) + 90) == "-"


def test_closing_blocked_work_clears_its_terminal_gate(world):
	"""A terminal Work has no scheduler phase or live gate, even when its
	blocker remains open. Closing the consumer is explicitly allowed; its
	former dependency remains journal history rather than a terminal Wait cue."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="needed while open")
	assert _row(world, work)["gate"]["work"] == blocker

	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              outcome="non-satisfying", rationale="cancelled independently")
	closed = _row(world, work)
	assert closed["phase"] is None
	stored = world["store"].conn.execute(
		"SELECT gate_kind, gate_work, gate_obligation, gate_started_at, gate_seq "
		"FROM work WHERE id=?", (work,)).fetchone()
	assert all(value is None for value in stored), \
		"terminal authority row retained a live scheduler gate episode"
	assert closed["gate"] is None, \
		"terminal Work retained a live scheduler gate"
	assert blocker_cue(closed) == "", \
		"terminal Work still rendered a Wait cause"
	assert held_field(closed, _epoch(closed["last_changed_at"]) + 90) == "-"


# -- the defect this Work exists to remove ---------------------------------

def test_two_unclaimed_rows_no_longer_run_unexplained_clocks(world):
	"""The reopened observation, exactly: W4 and W5 are both unclaimed
	and visibly equivalent, but one ran a clock and the other did not,
	because one carried a historical handoff. Now a running clock always
	has a visible cause on its own row."""
	handed, fresh = _make(world, "handed"), _make(world, "fresh")
	fx.hand_off(world["store"], handed, actor_team="lang", actor="ada",
	             to="lang.rsrch", comment="over")
	rows = [_row(world, handed), _row(world, fresh)]
	now = _epoch(rows[0]["last_changed_at"]) + 600
	assert [held_field(row, now) for row in rows] == ["-", "-"], \
		"two equivalent unclaimed rows still disagree about their clocks"
	# W12 extends the same reasoning one row further. Blocking `fresh`
	# gives it a visible cause in `Wait`, and it STILL runs no clock —
	# because a cause is not a Handler, and Held measures a Handler.
	blocker = _make(world, "blocker")
	tr.add_dependency(world["store"], fresh, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	blocked = _row(world, fresh)
	assert blocked["handler"] is None
	assert held_field(blocked, now) == "-", \
		"a blocked row runs a clock nobody is spending"
	assert blocker_cue(blocked), \
		"the gate must still name what the row is waiting on"


def test_every_row_with_a_clock_names_its_cause(world):
	"""The invariant behind the finding, stated once and then NARROWED
	by W12: a visible timer implies a visible Handler. `Wait` explains
	why a row cannot move, which is a different question from who is
	holding it, and only the second one is Held."""
	store = world["store"]
	subjects = []
	# W2938 one-slot capacity: the row that merely passes THROUGH a
	# claim is built before the one that stays claimed, so ada's single
	# slot serves both. Ordering only — every subject below is the same
	# subject it always was.
	subjects.append(_make(world, "queued"))
	blocked = _make(world, "blocked")
	tr.add_dependency(store, blocked, _make(world, "gate"),
	                  actor_team="lang", actor="ada", rationale="r")
	asked_work = _make(world, "asked")
	tr.claim_work(store, asked_work, actor_team="lang", actor="ada")
	tr.post_thread(store, _thread(world, asked_work), author_team="lang",
	               author="ada", body="advise", request="lang.rsrch",
	               on=asked_work)
	subjects.append(asked_work)
	subjects.append(blocked)
	claimed = _make(world, "claimed")
	tr.claim_work(store, claimed, actor_team="lang", actor="ada")
	subjects.append(claimed)
	parked = _make(world, "parked")
	tr.set_phase(store, parked, actor_team="lang", actor="ada",
	             phase="parked", reason="deferred")
	subjects.append(parked)

	now = _epoch(_row(world, subjects[0])["last_changed_at"]) + 300
	for work in subjects:
		row = _row(world, work)
		running = held_field(row, now) != "-"
		explained = row["handler"] is not None
		assert running == explained, \
			(f"{row['local_id']} phase={row['phase']} runs={running} "
			 f"handler={row['handler']} wait={blocker_cue(row)!r}")


# -- the cue -----------------------------------------------------------------

def test_the_cue_names_a_work_gate_with_the_remaining_count(world):
	work = _make(world, "consumer")
	first = _make(world, "first")
	tr.add_dependency(world["store"], work, first, actor_team="lang",
	                  actor="ada", rationale="r")
	assert blocker_cue(_row(world, work)) == first.rsplit("-", 1)[1]
	for name in ("second", "third"):
		tr.add_dependency(world["store"], work, _make(world, name),
		                  actor_team="lang", actor="ada", rationale="r")
	assert blocker_cue(_row(world, work)) == \
		f"{first.rsplit('-', 1)[1]}+2"


def test_the_cue_names_a_message_gate_without_a_count(world):
	"""`+N` counts additional open WORK blockers. Beside a Message gate
	it would suggest the two were commensurable, so it is absent."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	assert blocker_cue(_row(world, work)) == f"M{asked}"


def test_an_unblocked_row_has_no_cue(world):
	work = _make(world)
	assert blocker_cue(_row(world, work)) == ""
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert blocker_cue(_row(world, work)) == ""


def test_a_non_blocking_obligation_never_captures_the_cue(world):
	"""`request wait=false` creates a pending obligation that never
	suspended the Work. If the gate were rediscovered from the
	obligations table rather than read from the committed episode, that
	obligation would capture the cue the moment something else blocked
	the Work — naming a Message that is not holding it, and timing an
	episode that never started."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada",
	                       body="advise when you can", request="lang.rsrch",
	                       on=work, wait=False)["seq"]
	assert _row(world, work)["phase"] == "queued", \
		"wait=false blocked the Work"
	assert _gate(world, work) is None

	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	gate = _gate(world, work)
	assert gate["kind"] == "work" and gate["work"] == blocker, \
		f"a non-blocking obligation captured the cue: {gate}"
	assert blocker_cue(_row(world, work)) == blocker.rsplit("-", 1)[1]

	# and answering it changes nothing about what holds the Work
	before = _gate(world, work)
	tr.respond_obligation(world["store"], asked, team="lang", member="ada",
	                      body="advice")
	assert _gate(world, work) == before, \
		"answering an unrelated obligation moved the gate episode"


def test_a_non_blocking_obligation_does_not_outlive_its_own_wake(world):
	"""The mirror case: a Work blocked by a real Message gate, with a
	SECOND non-blocking obligation opened afterwards. Clearing the
	blocking one must queue the Work, not silently adopt the other."""
	work = _make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	blocking = tr.post_thread(world["store"], _thread(world, work),
	                          author_team="lang", author="ada",
	                          body="advise before I continue",
	                          request="lang.rsrch", on=work)["seq"]
	assert _gate(world, work)["obligation"]["seq"] == blocking
	tr.post_thread(world["store"], _thread(world, work), author_team="lang",
	               author="ada", body="and this one whenever",
	               request="lang.rsrch", on=work, wait=False)
	assert _gate(world, work)["obligation"]["seq"] == blocking, \
		"a later non-blocking obligation stole the cue"
	tr.respond_obligation(world["store"], blocking, team="lang",
	                      member="ada", body="answered")
	row = _row(world, work)
	assert row["phase"] == "queued" and row["gate"] is None, \
		"the Work stayed blocked on an obligation that never blocked it"


# -- a child is NOT a gate ---------------------------------------------------

def test_an_open_child_holds_its_parent_back_from_nothing(world):
	"""W1477 supersedes W78's extension of the selection rule.

	The pinned rule is 'the oldest open BLOCKER by permanent creation
	order'. W78 also searched open children, reasoning that a
	child-gated parent would otherwise sit blocked with an empty `Wait`
	cell — the unexplained timer W78 existed to remove. W1477 removed
	the premise instead: containment never gated execution, so the
	parent is not blocked, and there is no unexplained row to explain.

	The `Wait` cell is empty here because nothing is waiting."""
	parent = _make(world, "epic")
	_child = _make(world, "part one", parent=parent)
	row = _row(world, parent)
	assert row["phase"] == "queued", "an open child blocked its parent"
	assert row["gate"] is None, "a child was displayed as a gate"
	assert blocker_cue(row) == ""
	# No gate episode means no clock to run, which W12 already required
	# of the child-gated parent this case used to build.
	assert held_field(row, _epoch(row["last_changed_at"]) + 20) == "-"


def test_opening_and_closing_children_never_moves_the_parent_gate(world):
	"""Containment traffic is invisible to the scheduler in both
	directions: the second child does not queue behind the first, and
	closing one does not retarget a gate the parent never had."""
	parent = _make(world, "epic")
	first = _make(world, "part one", parent=parent)
	_second = _make(world, "part two", parent=parent)
	assert _gate(world, parent) is None
	tr.close_work(world["store"], first, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	assert _gate(world, parent) is None, \
		"closing a child started a gate episode on its parent"
	assert _row(world, parent)["phase"] == "queued"


def test_the_oldest_open_blocker_wins_and_children_never_enter(world):
	"""One order over blockers by permanent creation sequence. W1477
	narrowed this from 'across children and blockers': a child cannot
	outrank or succeed a blocker, because it is not a candidate at
	all."""
	older = _make(world, "older blocker")
	parent = _make(world, "epic")
	_child = _make(world, "younger child", parent=parent)
	younger = _make(world, "younger blocker")
	for blocker in (older, younger):
		tr.add_dependency(world["store"], parent, blocker,
		                  actor_team="lang", actor="ada", rationale="r")
	assert _gate(world, parent)["work"] == older, \
		"a younger blocker outranked an older one"
	tr.close_work(world["store"], older, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	assert _gate(world, parent)["work"] == younger
	tr.close_work(world["store"], younger, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	# The child is still open, and the parent is gate-free and runnable.
	assert _gate(world, parent) is None, \
		"the child inherited the cleared blocker's gate"
	assert _row(world, parent)["phase"] == "queued"


# -- the ledger stays honest -------------------------------------------------

def test_a_gate_change_inside_block_is_not_a_phase_transition(world):
	"""'The implementation must keep phase-event playback honest: a gate
	change within `block` is a new gate episode but not a fabricated
	phase transition.'"""
	work = _make(world, "consumer")
	first, second = _make(world, "first"), _make(world, "second")
	for blocker in (first, second):
		tr.add_dependency(world["store"], work, blocker, actor_team="lang",
		                  actor="ada", rationale="r")
	before = [entry for entry in
	          pj.work_events(world["store"], work)["events"]
	          if entry.get("phase_interval")]
	tr.close_work(world["store"], first, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	after = [entry for entry in
	         pj.work_events(world["store"], work)["events"]
	         if entry.get("phase_interval")]
	assert len(after) == len(before), \
		"the gate change fabricated a phase transition"
	assert after[-1]["phase_interval"]["phase"] == "block"
	assert after[-1]["phase_interval"]["open"] is True, \
		"the block episode was closed and reopened by a gate change"


def test_a_message_to_work_retarget_records_its_gate_boundary(world):
	"""The response event is the authoritative instant at which M... stops
	holding the Work and W... becomes the displayed gate. The row alone only
	describes the latest episode; without `gate_now` on this event, the prior
	episode boundary disappears as soon as the gate changes again."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="acquired independently")
	answered = tr.respond_obligation(world["store"], asked, team="lang",
	                                 member="ada", body="answered")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == answered["seq"])
	assert event["payload"]["gate_now"] == [
		{"work": work, "kind": "work", "gate_work": blocker,
		 "obligation": None}], event["payload"].get("gate_now")
	assert "phase_now" not in event["payload"], \
		"the same-phase gate retarget fabricated a phase transition"


def test_the_wake_names_the_gate_that_cleared(world):
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	tr.close_work(world["store"], blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	wake = next(event for event in world["store"].events()
	            if event["kind"] == "wake")
	assert wake["payload"]["cleared_gate"] == {
		"kind": "work", "work": blocker, "obligation": None}
	assert wake["payload"]["gate_now"] == [
		{"work": work, "kind": None, "gate_work": None, "obligation": None}]


def test_the_phase_and_the_gate_never_disagree(world):
	"""The structural invariant: `block` iff a gate is displayed. Driven
	through every path that moves either one."""
	store = world["store"]

	def agrees(work, note):
		row = _row(world, work)
		blocked = row["phase"] == "block"
		gated = row["gate"] is not None
		assert blocked == gated, \
			f"{note}: phase={row['phase']!r} gate={row['gate']!r}"

	work = _make(world, "subject")
	agrees(work, "born")
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	agrees(work, "claimed")
	asked = tr.post_thread(store, _thread(world, work), author_team="lang",
	                       author="ada", body="advise", request="lang.rsrch",
	                       on=work)["seq"]
	agrees(work, "blocking request")
	blocker = _make(world, "blocker")
	tr.add_dependency(store, work, blocker, actor_team="lang", actor="ada",
	                  rationale="r")
	agrees(work, "blocker behind the obligation")
	tr.respond_obligation(store, asked, team="lang", member="ada", body="ok")
	agrees(work, "obligation answered")
	tr.close_work(store, blocker, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	agrees(work, "blocker closed")
	child = _make(world, "child", parent=work)
	agrees(work, "child created")
	tr.close_work(store, child, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	agrees(work, "child closed")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="parked", reason="deferred")
	agrees(work, "parked")
	tr.set_phase(store, work, actor_team="lang", actor="ada",
	             phase="queued", reason="resumed")
	agrees(work, "resumed")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done")
	agrees(work, "closed")

	# and closed while BLOCKED, which the queued close above does not
	# reach: the phase column is NOT NULL and keeps its last value, so
	# a terminal row can retain a gate the projection still reports.
	second, blocker = _make(world, "second"), _make(world, "still open")
	tr.add_dependency(store, second, blocker, actor_team="lang",
	                  actor="ada", rationale="needed while open")
	agrees(second, "blocked")
	tr.close_work(store, second, actor_team="lang", actor="ada",
	              outcome="non-satisfying", rationale="cancelled")
	agrees(second, "closed while blocked")


def test_a_parked_work_under_a_gate_shows_no_clock(world):
	"""Parking is an explicit deferral and is deliberately excluded from
	the gate sweep, so a parked row shows neither a gate nor a timer
	even while something would otherwise hold it."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="parked", reason="deferred first")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="r")
	row = _row(world, work)
	assert row["phase"] == "parked"
	assert row["gate"] is None and blocker_cue(row) == ""
	assert held_field(row, _epoch(row["last_changed_at"]) + 300) == "-"
	# and leaving the park reveals the gate, starting its episode then
	tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
	             phase="queued", reason="resumed")
	resumed = _row(world, work)
	assert resumed["phase"] == "block"
	assert resumed["gate"]["work"] == blocker


def test_the_terminal_close_records_the_gate_episode_boundary(world):
	"""'Clear the gate episode atomically in terminal close and preserve
	the event evidence for that episode boundary.'

	The clearing has its own test; this is the evidence half, which
	nothing else checks. Without it the row would go quiet correctly
	while the ledger lost the fact that an episode ended — and the
	replay reconstructs nothing, so an unrecorded boundary is absent
	forever rather than derivable later."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="needed while open")
	before = _gate(world, work)
	assert before["kind"] == "work"
	closed = tr.close_work(world["store"], work, actor_team="lang",
	                       actor="ada", outcome="non-satisfying",
	                       rationale="cancelled independently")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == closed["seq"])
	assert event["payload"]["gate_now"] == [
		{"work": work, "kind": None, "gate_work": None,
		 "obligation": None}], event["payload"].get("gate_now")
	# and the phase episode boundary is still recorded beside it — the
	# two axes end together but are recorded separately, because a gate
	# change inside `block` is not a phase transition.
	assert event["payload"]["phase_now"] == [
		{"work": work, "phase": None}]


def test_a_close_with_no_gate_records_no_gate_boundary(world):
	"""The guard on the other side: a Work closing while it holds no
	gate has no episode to end, and inventing one would put a boundary
	in the ledger for an episode that never existed."""
	work = _make(world, "ungated")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert _gate(world, work) is None
	closed = tr.close_work(world["store"], work, actor_team="lang",
	                       actor="ada", outcome="satisfying",
	                       rationale="done")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == closed["seq"])
	assert "gate_now" not in event["payload"], \
		"a Work with no gate recorded a gate episode boundary anyway"
	assert event["payload"]["phase_now"] == [{"work": work, "phase": None}]


def test_a_disposal_retarget_records_its_gate_boundary_too(world):
	"""'for both response and disposition.' Disposal is the other way an
	obligation completes, and a boundary recorded for one and not the
	other would be a hole shaped exactly like the one just closed."""
	work, blocker = _make(world, "consumer"), _make(world, "blocker")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	tr.add_dependency(world["store"], work, blocker, actor_team="lang",
	                  actor="ada", rationale="acquired independently")
	disposed = tr.dispose_obligation(world["store"], asked, team="lang",
	                                 member="ada",
	                                 disposition="no longer needed")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == disposed["seq"])
	assert event["payload"]["gate_now"] == [
		{"work": work, "kind": "work", "gate_work": blocker,
		 "obligation": None}], event["payload"].get("gate_now")
	assert "phase_now" not in event["payload"], \
		"the same-phase gate retarget fabricated a phase transition"


def test_the_final_gate_clear_records_exactly_one_boundary(world):
	"""'prove that final-gate clear still records exactly one honest
	boundary (the existing wake event) rather than duplicating or
	fabricating one.'

	This is the risk the retarget repair introduces. Now that the sweep
	receives the causing operation's payload, the clearing path could
	just as easily write the boundary TWICE — once onto the response and
	once inline on the wake — leaving a replay that sees an episode end
	at two different sequences."""
	work = _make(world, "consumer")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	answered = tr.respond_obligation(world["store"], asked, team="lang",
	                                 member="ada", body="answered")
	recorded = [(entry["seq"], entry["kind"])
	            for entry in world["store"].events()
	            if entry["seq"] >= answered["seq"]
	            and any(record["work"] == work for record
	                    in (entry["payload"].get("gate_now") or ()))]
	assert len(recorded) == 1, \
		f"the final clear recorded {len(recorded)} boundaries: {recorded}"
	assert recorded[0][1] == "wake", \
		f"the boundary is not on the wake event: {recorded}"
	# the wake is the honest place for it: this is the transition that
	# DID make the Work actionable again, unlike the same-phase retarget.
	wake = next(entry for entry in world["store"].events()
	            if entry["seq"] == recorded[0][0])
	assert wake["payload"]["phase_now"] == [{"work": work, "phase": "queued"}]
	assert wake["payload"]["cleared_gate"]["obligation"] == asked


def test_a_dispose_that_clears_the_last_gate_also_records_one_boundary(world):
	work = _make(world, "consumer")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	asked = tr.post_thread(world["store"], _thread(world, work),
	                       author_team="lang", author="ada", body="advise",
	                       request="lang.rsrch", on=work)["seq"]
	disposed = tr.dispose_obligation(world["store"], asked, team="lang",
	                                 member="ada", disposition="withdrawn")
	recorded = [entry["kind"] for entry in world["store"].events()
	            if entry["seq"] >= disposed["seq"]
	            and any(record["work"] == work for record
	                    in (entry["payload"].get("gate_now") or ()))]
	assert recorded == ["wake"], recorded
