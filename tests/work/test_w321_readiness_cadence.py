"""W321: the readiness wait idles at one second, not fifty milliseconds.

`work/records/2026/08/finding-readiness-poll-interval/`. Every
configured participant runs its own readiness bridge and its own
`baton wait timeout=60`. At a 50 ms empty-read cadence an idle
deployment re-derived the whole participant-action projection about
twenty times a second PER MEMBER — real SQLite and CPU work spent
discovering, over and over, that nothing had happened.

Agent pickup and execution happen on seconds-to-minutes timescales, so
one second of extra latency is invisible where twenty reads a second
are not.

These tests pin the cadence WITHOUT sleeping in wall time: the clock
and the sleep are both replaced, so a five-second wait costs
microseconds and the assertions are on the durations actually
requested. The one property that cannot be faked — that the caller's
deadline still wins — is checked at both ends of it.
"""

from __future__ import annotations

import os
import sys
import time as _real_time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402


@pytest.fixture()
def world(tmp_path):
	_config, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield store
	store.close()


@pytest.fixture()
def fake_clock(monkeypatch):
	"""A monotonic clock the sleep advances, and nothing else.

	The suite must not spend a second to prove a one-second cadence, so
	the wait's own two time calls are replaced and the DURATIONS IT
	ASKED FOR become the evidence."""
	# Starting at zero on purpose: a float clock parked at a large
	# value cannot represent a sub-nanosecond remainder, so a residual
	# left by `deadline - now` would never advance it and this fake —
	# not the code under test — would spin. A real monotonic clock
	# advances on its own and has no such problem.
	state = {"now": 0.0, "slept": []}

	def monotonic():
		return state["now"]

	def sleep(seconds):
		state["slept"].append(seconds)
		state["now"] += max(seconds, 1e-9)
		if len(state["slept"]) > 5_000:
			raise AssertionError("the wait did not terminate")

	monkeypatch.setattr(_real_time, "monotonic", monotonic)
	monkeypatch.setattr(_real_time, "sleep", sleep)
	return state


@pytest.fixture()
def reads(monkeypatch):
	"""How many times the projection was actually derived."""
	counted = []
	original = pj.participant_actions

	def counting(*args, **kwargs):
		counted.append(1)
		return original(*args, **kwargs)

	monkeypatch.setattr(pj, "participant_actions", counting)
	return counted


def wait(store, seconds, member="ada"):
	return pj.wait_actionable(store, viewer_team="lang",
	                          viewer_member=member,
	                          timeout_seconds=seconds)


def make_work(store, title="parser recovery"):
	return tr.create_work(store, team="lang", kind="bug", title=title,
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


# -- the ruled cadence -------------------------------------------------------

def test_the_cadence_is_one_second(world):
	assert pj.READINESS_POLL_SECONDS == 1.0


def test_an_idle_wait_polls_once_a_second(world, fake_clock, reads):
	"""The finding's own arithmetic: about one read per second after
	the first, rather than twenty."""
	result = wait(world, 5.0)
	assert result["timed_out"] is True and result["actionable"] == []
	assert fake_clock["slept"] == [1.0, 1.0, 1.0, 1.0, 1.0], \
		fake_clock["slept"]
	# one read to start, then one per interval — six, not a hundred
	assert len(reads) == 6, len(reads)


def test_a_minute_long_wait_costs_a_minute_of_reads_not_twelve_hundred(
		world, fake_clock, reads):
	"""The deployed shape: `wait timeout=60`, per participant."""
	wait(world, 60.0)
	assert len(reads) == 61, len(reads)
	assert sum(fake_clock["slept"]) == pytest.approx(60.0)


# -- the caller's deadline still wins ----------------------------------------

def test_timeout_zero_is_still_one_pure_read(world, fake_clock, reads):
	result = wait(world, 0)
	assert result["timed_out"] is True
	assert fake_clock["slept"] == [], "a zero timeout slept"
	assert len(reads) == 1


@pytest.mark.parametrize("timeout", [0.01, 0.05, 0.25, 0.999])
def test_a_sub_second_timeout_returns_at_its_own_deadline(
		world, fake_clock, reads, timeout):
	"""The cadence is a floor on POLLING, never on the caller's
	deadline: a wait asked for 10 ms sleeps 10 ms, not a second."""
	result = wait(world, timeout)
	assert result["timed_out"] is True
	assert fake_clock["slept"] == [timeout], fake_clock["slept"]
	assert len(reads) == 2


def test_a_partial_final_interval_is_bounded_by_the_remainder(
		world, fake_clock):
	wait(world, 2.5)
	assert fake_clock["slept"] == [1.0, 1.0, 0.5], fake_clock["slept"]


def test_no_sleep_ever_exceeds_the_interval_or_the_remainder(
		world, fake_clock):
	for timeout in (0.3, 1.0, 1.7, 3.0, 4.25):
		fake_clock["slept"].clear()
		wait(world, timeout)
		assert sum(fake_clock["slept"]) == pytest.approx(timeout), timeout
		for nap in fake_clock["slept"]:
			assert 0 < nap <= pj.READINESS_POLL_SECONDS, (timeout, nap)


# -- what a wait still sees --------------------------------------------------

def test_an_action_already_present_returns_without_sleeping(
		world, fake_clock, reads):
	make_work(world)
	result = wait(world, 60.0)
	assert result["timed_out"] is False
	assert result["actionable"], result
	assert fake_clock["slept"] == [], "a ready wait slept anyway"
	assert len(reads) == 1


def test_an_action_committed_meanwhile_is_seen_within_one_interval(
		world, fake_clock, reads, monkeypatch):
	"""The acceptance boundary's latency claim, asserted in intervals
	rather than in wall time: the Work commits while the wait is
	asleep, and the very next read returns it."""
	original = pj.participant_actions
	born = {}

	def commit_then_read(*args, **kwargs):
		# committed DURING the first sleep, from the wait's point of
		# view: the second read is the first one that can see it
		if len(reads) == 1 and not born:
			born["work"] = make_work(world)["work_id"]
		return original(*args, **kwargs)

	monkeypatch.setattr(pj, "participant_actions", commit_then_read)
	result = wait(world, 60.0)
	assert result["timed_out"] is False
	assert fake_clock["slept"] == [1.0], fake_clock["slept"]
	assert result["actionable"][0]["work"] == born["work"]


def test_the_action_contents_are_the_projections_own(world, fake_clock):
	"""Nothing about derivation changed — the wait returns what
	`participant_actions` returns, key for key."""
	work = make_work(world)["work_id"]
	waited = wait(world, 5.0)["actionable"]
	direct = pj.participant_actions(world, viewer_team="lang",
	                                viewer_member="ada")["actions"]
	assert waited == direct
	assert waited[0]["work"] == work


def test_the_wait_is_still_read_only(world, fake_clock):
	before = world.last_seq()
	rows = [dict(row) for row in
	        world.conn.execute("SELECT * FROM work ORDER BY id")]
	wait(world, 3.0)
	assert world.last_seq() == before, "an empty wait wrote something"
	assert [dict(row) for row in
	        world.conn.execute("SELECT * FROM work ORDER BY id")] == rows


def test_the_wait_stays_participant_relative(world, fake_clock):
	"""`grace` shares the team; the route resolves to `ada`, so the
	cadence change must not have widened who sees what."""
	make_work(world)
	assert wait(world, 2.0, member="ada")["timed_out"] is False
	assert wait(world, 2.0, member="grace")["timed_out"] is True


# -- the cost this Work removed ----------------------------------------------

def test_the_old_cadence_would_have_read_twenty_times_a_second(
		world, fake_clock, reads, monkeypatch):
	"""The measurement the finding rests on, kept as a live comparison
	rather than a number in prose: at the previous 50 ms the same idle
	minute cost twelve hundred projection derivations."""
	monkeypatch.setattr(pj, "READINESS_POLL_SECONDS", 0.05)
	wait(world, 60.0)
	# a range rather than an exact count: the last interval of a
	# float-accumulated minute may leave a sliver, and the point here is
	# the ORDER OF MAGNITUDE the finding measured.
	assert 1_195 <= len(reads) <= 1_210, len(reads)
	assert len(reads) / 61 > 19, "the comparison stopped being a comparison"


def test_the_operating_guide_states_the_cadence_and_its_bound():
	"""An agent reading the guide must not be surprised by a second of
	latency, and must not read the interval as a floor on its own
	deadline."""
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "EFFECTIVE-BATON.md").read_text(
		encoding="utf-8")
	prose = " ".join(body.split())
	assert "once a second" in prose, "the cadence is undocumented"
	assert "never extends your deadline" in prose
	assert "`timeout=0` is a single read" in prose
