"""WS-2 group 3: derived due, audited extension, close evidence, reviewer
discretion, and the atomic/race/restart matrix rows.

Due-ness is a pure function of the stored `review_at`, the injected clock,
and the deadline generation: no scheduler, no timer audit row, no read
mutation — idempotent across reads and restarts. Every branch out of a due
trial is an explicit audited reviewer decision; elapsed time and feedback
never choose one automatically.
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
import fixtures as fx                                         # noqa: E402

T0 = "2026-08-15T10:00:00Z"
T1 = "2026-08-15T12:00:00Z"
T2 = "2026-08-15T18:00:00Z"


@pytest.fixture
def world(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
	                 "kinds": ["bug", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["verify"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["verify"]},
	        "mdb": {"members": {"mo": ["dev"]}, "kinds": ["verify"]}}
	_config, database = fx.build_instance(str(tmp_path), spec)
	store = bw.Authority(database)
	store.clock = lambda: store.now
	store.now = T0
	yield store
	store.close()


def _provider(store):
	return tr.create_work(store, team="lang", kind="bug", title="LANG-42",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="provider")["work_id"]


def _round_view(store, work, number=1):
	detail = pj.detail(store, work, viewer_team="lang", viewer_member="ada")
	return next(entry for entry in detail["trials"]
	            if entry["trial"] == number)


# -- derived due -------------------------------------------------------------

def test_due_is_derived_deterministic_and_idempotent(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	view = _round_view(store, work)
	assert view["due"] is False and view["review_at"] == T1
	assert view["deadline_generation"] == 1
	assert pj.team_summary(store, viewer_team="lang")["due"] == 0
	# The boundary is exact: at T, due.
	store.now = T1
	assert _round_view(store, work)["due"] is True
	assert pj.team_summary(store, viewer_team="lang")["due"] == 1
	# Idempotent across reads AND restart — same generation, same answer,
	# no event row anywhere (no scheduler, no notification mutation).
	assert _round_view(store, work)["due"] is True
	fresh = bw.Authority(store.path)
	fresh.clock = lambda: T1
	assert pj.detail(fresh, work, viewer_team="lang",
	                 viewer_member="ada")["trials"][0]["due"] is True
	fresh.close()
	assert all(event["kind"] != "due"
	           for event in store.events()), "a timer wrote an audit row"
	# Due is visible to the RESPONSIBLE team only.
	assert pj.team_summary(store, viewer_team="push")["due"] == 0


def test_a_deadline_born_expired_refuses(world):
	store = world
	work = _provider(store)
	with pytest.raises(bw.WorkError, match="loose end"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=["push.verify"],
		                review_at=T0)


@pytest.mark.parametrize("bad", [
	"not-a-utc-instant",
	"2027-02-30T12:00:00Z",
	"2026-08-15T13:00:00+01:00",
])
def test_review_at_refuses_noncanonical_or_invalid_instants(world, bad):
	store = world
	work = _provider(store)
	with pytest.raises(bw.WorkError):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=["push.verify"],
		                review_at=bad)


def test_a_round_rechecks_deadline_after_entering_the_write(world):
	"""A deadline can pass after optimistic validation but before the write
	lock; a trial must not commit already due."""
	store = world
	work = _provider(store)
	moments = iter((T0, T2))
	store.clock = lambda: next(moments)
	with pytest.raises(bw.WorkError, match="not later than now|expired"):
		tr.create_trial(store, work, actor_team="lang", actor="ada",
		                candidate="driftc-A", assign=["push.verify"],
		                review_at=T1)
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM trials").fetchone()["n"] == 0


def test_due_trial_is_in_the_responsible_routes_actionable_projection(world):
	"""The summary count is an alarm, not a locator: the confirmed mapping
	requires the due trial itself in the responsible route's actionable list."""
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	assert pj.obligations(store, viewer_team="lang") == []
	store.now = T1
	actionable = pj.obligations(store, viewer_team="lang")
	assert any(entry.get("work") == work and entry.get("trial") == 1
	           for entry in actionable), \
		"due count has no actionable record identifying what needs review"


def test_actionable_projection_is_one_database_snapshot(world, monkeypatch):
	"""The response and its derived due locator describe one authority
	snapshot. A close between their queries may yield wholly before or wholly
	after, never an already-withdrawn response without its same-snapshot due
	trial."""
	store = world
	store.conn.execute("PRAGMA journal_mode=WAL")
	work = _provider(store)
	fx.post(store, work, author_team="lang", author="ada",
	                body="review this", request="lang.rev")
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	store.now = T1
	original = pj._endpoint_struct
	interleaved = False

	def close_between_queries(reader, team, kind, selected=None):
		nonlocal interleaved
		if not interleaved:
			interleaved = True
			with bw.Authority(store.path) as writer:
				writer.clock = store.clock
				tr.close_work(writer, work, actor_team="lang", actor="ada",
				              rationale="interleaving proof",
				              outcome="satisfying")
		return original(reader, team, kind, selected)

	monkeypatch.setattr(pj, "_endpoint_struct", close_between_queries)
	flavors = [entry["flavor"] for entry in
	           pj.obligations(store, viewer_team="lang", now=T1)]
	assert flavors in ([], ["response", "due_trial"]), \
		f"actionable response tore across the close: {flavors!r}"


def test_due_never_transitions_anything(world):
	"""Reaching review_at changes NO workflow state: work, phase, Current,
	candidate, dependencies, and assignments are byte-identical."""
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	before = store.events()
	store.now = T2
	assert _round_view(store, work)["due"] is True
	assert store.events() == before, "due-ness mutated the authority"
	row = store.conn.execute("SELECT status, phase FROM work WHERE id=?",
	                         (work,)).fetchone()
	assert row["status"] == "open" and row["phase"] == "queued"
	assert pj.obligations(store, viewer_team="push")[0]["status"] == \
		"pending"


# -- the audited extension ---------------------------------------------------

def test_extension_is_audited_retains_evidence_and_advances_generation(
		world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify"],
	                          review_at=T1)
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="passed", evidence="clean")
	# Not-forward refusal while the deadline is still ahead of the clock.
	with pytest.raises(bw.WorkError, match="moves forward"):
		tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
		                review_at=T1)
	store.now = T1
	assert _round_view(store, work)["due"] is True
	with pytest.raises(bw.WorkError, match="never grant"):
		tr.extend_trial(store, work, 1, actor_team="lang", actor="grace",
		                review_at=T2)
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at=T2)
	view = _round_view(store, work)
	assert view["due"] is False, "the extension did not clear due"
	assert view["deadline_generation"] == 2
	assert view["review_at"] == T2
	assert view["progress"] == "1/2" and view["pending"] == 1, \
		"the extension lost reports or pending assignments"
	act = next(event for event in store.events()
	           if event["kind"] == "extend_trial")
	assert act["payload"]["candidate"] == "driftc-A"
	assert (act["payload"]["from_review_at"],
	        act["payload"]["to_review_at"]) == (T1, T2)
	assert act["payload"]["deadline_generation"] == 2
	# Repeated extensions are VISIBLE history, not a hidden timer reset.
	store.now = T2
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at="2026-08-16T00:00:00Z")
	assert len([e for e in store.events()
	            if e["kind"] == "extend_trial"]) == 2


def test_extension_gives_a_deadline_to_an_undated_round(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"])
	assert _round_view(store, work)["review_at"] is None
	assert _round_view(store, work)["deadline_generation"] == 0
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at=T1)
	view = _round_view(store, work)
	assert view["review_at"] == T1 and view["deadline_generation"] == 1


def test_extension_rechecks_deadline_after_entering_the_write(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"])
	_interleave(store, lambda: setattr(store, "now", T2))
	with pytest.raises(bw.WorkError, match="not later than now|expired"):
		tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
		                review_at=T1)
	view = _round_view(store, work)
	assert view["review_at"] is None and view["deadline_generation"] == 0


# -- reviewer discretion and the close evidence ------------------------------

def test_silence_may_inform_the_reviewer_but_never_impersonates_a_report(
		world):
	"""Closing at 0/N on elapsed exposure is a HUMAN decision the audit
	records honestly: zero reports, the exposure window, the withdrawn
	pending set — no feedback fabricated anywhere."""
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A",
	                assign=["push.verify", "web.verify", "mdb.verify"],
	                review_at=T1)
	store.now = T2
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="wide exposure, zero negative reports",
	              outcome="satisfying")
	closing = next(event for event in store.events()
	               if event["kind"] == "close_work")
	summary = closing["payload"]["trial_summary"]
	assert summary["progress"] == "0/3"
	assert summary["observations"] == {"passed": 0, "failed": 0,
	                                   "unable": 0}
	assert sorted(summary["withdrawn_pending"]) == \
		["mdb.verify", "push.verify", "web.verify"]
	assert summary["candidate"] == "driftc-A"
	assert (summary["created_ts"], summary["closed_ts"]) == (T0, T2), \
		"the elapsed exposure window is not recorded"
	assert summary["basis"] == "wide exposure, zero negative reports"
	view = _round_view(store, work)
	assert view["status"] == "closed" and view["progress"] == "0/3"
	assert view["withdrawn"] == 3


def test_the_close_evidence_counts_receipt_not_support(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify",
	                                  "mdb.verify"])
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="passed", evidence="clean")
	tr.report(store, created["assignments"][1], team="web", member="wren",
	          observation="failed", evidence="crash")
	tr.assess(store, created["assignments"][1], actor_team="lang",
	          actor="ada", assessment="rejected",
	          rationale="consumer config error")
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="one confirmation; the failure was invalid",
	              outcome="satisfying")
	summary = next(event for event in store.events()
	               if event["kind"] == "close_work")["payload"][
	               "trial_summary"]
	assert summary["progress"] == "2/3", \
		"a rejected failure stopped counting as received"
	assert summary["observations"] == {"passed": 1, "failed": 1,
	                                   "unable": 0}
	assert summary["withdrawn_pending"] == ["mdb.verify"]


# -- races, atomicity, restart ----------------------------------------------

def _interleave(store, competing):
	original = store._write

	def wrapped(kind, actor, payload, mutate, **kw):
		store._write = original
		competing()
		return original(kind, actor, payload, mutate, **kw)

	store._write = wrapped


def test_the_extension_versus_close_race_serializes(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.close_work(
		other, work, actor_team="lang", actor="ada",
		rationale="closed first", outcome="non-satisfying"))
	with pytest.raises(bw.WorkError, match="only an open trial"):
		tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
		                review_at=T2)
	assert _round_view(store, work)["status"] == "closed"
	other.close()


def test_the_report_versus_abandon_race_serializes(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.abandon_trial(
		other, work, 1, actor_team="lang", actor="ada",
		reason="abandoned mid-flight"))
	with pytest.raises(bw.WorkError, match="already withdrawn"):
		tr.report(store, created["assignments"][0], team="push",
		          member="sl", observation="passed", evidence="racing")
	view = _round_view(store, work)
	assert view["status"] == "abandoned" and view["withdrawn"] == 1
	other.close()


def test_the_assessment_versus_close_race_serializes(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="failed", evidence="crash")
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.close_work(
		other, work, actor_team="lang", actor="ada",
		rationale="closed first", outcome="non-satisfying"))
	with pytest.raises(bw.WorkError, match="closed"):
		tr.assess(store, created["assignments"][0], actor_team="lang",
		          actor="ada", assessment="accepted", rationale="racing")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM assessments").fetchone()["n"] == 0
	other.close()


def test_the_new_round_versus_abandon_race_serializes(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"])
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.create_trial(
		other, work, actor_team="lang", actor="ada",
		candidate="driftc-B", assign=["web.verify"]))
	with pytest.raises(bw.WorkError, match="already superseded"):
		tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
		                 reason="racing abandon")
	assert _round_view(store, work, 1)["status"] == "superseded"
	assert _round_view(store, work, 2)["status"] == "open"
	other.close()


def test_the_atomic_close_rolls_back_whole_at_every_boundary(world):
	"""Fault injection: explode at each successive write statement inside
	the closing transaction. Every fault leaves the authority byte-for-byte
	at the pre-close state — dense sequence, open work, open trial, pending
	assignments, waiting consumer — or the close commits whole."""
	store = world
	work = _provider(store)
	consumer = tr.create_work(store, team="push", kind="verify",
	                          title="PUSH-1", origin="external-report", classification="suspected-defect",
	                          author="sl", body="blocked")["work_id"]
	tr.add_dependency(store, consumer, work, actor_team="push", actor="sl", rationale="test dependency")
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A",
	                assign=["push.verify", "web.verify"], review_at=T1)
	store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	import hashlib
	baseline = hashlib.sha256(open(store.path, "rb").read()).hexdigest()
	baseline_events = store.events()

	statement = {"n": 0, "limit": 0}
	real_conn = store.conn

	class ExplodingConn:
		def execute(self, sql, *args):
			if sql.strip().upper().startswith(
					("UPDATE", "INSERT", "DELETE")):
				statement["n"] += 1
				if statement["n"] > statement["limit"]:
					raise Exception("injected fault")
			return real_conn.execute(sql, *args)

		def __getattr__(self, name):
			return getattr(real_conn, name)

	boundary = 0
	while True:
		boundary += 1
		statement["n"], statement["limit"] = 0, boundary
		store.conn = ExplodingConn()
		try:
			tr.close_work(store, work, actor_team="lang", actor="ada",
			              rationale="atomic", outcome="satisfying")
			store.conn = real_conn
			break  # committed whole with no fault reached
		except Exception as failure:
			store.conn = real_conn
			if isinstance(failure, bw.WorkError) and \
					"injected" not in str(failure):
				raise
			store.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
			now = hashlib.sha256(
				open(store.path, "rb").read()).hexdigest()
			assert now == baseline, \
				f"fault at write {boundary} left partial state"
			assert store.events() == baseline_events
		assert boundary < 50, "the close never completed"
	# The completed close is WHOLE: outcome, trial, withdrawals, wake.
	assert _round_view(store, work)["status"] == "closed"
	assert _round_view(store, work)["withdrawn"] == 2
	row = store.conn.execute("SELECT phase FROM work WHERE id=?",
	                         (consumer,)).fetchone()
	assert row["phase"] == "queued", "the consumer wake was lost"


def test_restart_reconstructs_the_complete_round_state(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify", "web.verify"],
	                          review_at=T1)
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="failed", evidence="crash")
	tr.assess(store, created["assignments"][0], actor_team="lang",
	          actor="ada", assessment="rejected", rationale="bad config")
	tr.assess(store, created["assignments"][0], actor_team="lang",
	          actor="ada", assessment="accepted", rationale="reproduced")
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at=T2)
	before = pj.detail(store, work, viewer_team="lang",
	                   viewer_member="ada")["trials"]

	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	after = pj.detail(fresh, work, viewer_team="lang",
	                  viewer_member="ada")["trials"]
	fresh.close()
	assert after == before, "restart lost trial state"
	entry = after[0]["assignments"][0]
	assert entry["observation"] == "failed"
	assert [a["assessment"] for a in entry["assessments"]] == \
		["rejected", "accepted"]
	assert after[0]["review_at"] == T2
	assert after[0]["deadline_generation"] == 2


# -- R44: the read-only deadline-aware wait ----------------------------------

def test_wait_returns_immediately_when_actionable(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	store.now = T1
	result = pj.wait_actionable(store, viewer_team="lang",
	                            viewer_member="ada",
	                            timeout_seconds=0.01)
	assert result["timed_out"] is False
	assert result["actionable"][0]["flavor"] == "due_trial"
	# The verifier's pending assignment is equally immediate.
	result = pj.wait_actionable(store, viewer_team="push",
	                            viewer_member="sl",
	                            timeout_seconds=0.01)
	assert result["timed_out"] is False
	assert result["actionable"][0]["flavor"] == "verification"


def test_wait_times_out_quietly_before_the_deadline(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	before = store.events()
	# W136: the wait is participant-relative; grace resolves nothing,
	# so the pure deadline mechanics stay observable without the
	# provider Work itself waking its handler.
	result = pj.wait_actionable(store, viewer_team="lang",
	                            viewer_member="grace",
	                            timeout_seconds=0.15)
	assert result["actionable"] == [] and result["timed_out"] is True
	assert result["snapshot_seq"] == store.last_seq(), \
		"the wait's token does not name the state it observed"
	assert store.events() == before, "the wait mutated the authority"


def test_wait_wakes_when_the_deadline_arrives(world, monkeypatch):
	import time as _time
	# W321 raised the idle readiness cadence from 50 ms to one second.
	# What this case is about is that the wait WAKES on the deadline
	# rather than sleeping through it — not how long an idle poll
	# lasts, which `test_w321_readiness_cadence` owns and pins without
	# spending wall time. Polling faster here keeps the subject and
	# keeps the gate honest about the seconds it spends.
	monkeypatch.setattr(pj, "READINESS_POLL_SECONDS", 0.05)
	store = world
	work = _provider(store)
	# W136: neutralize the routed-Work wake (a push-owned gate blocks
	# the provider) so the DEADLINE is the only thing that can wake ada.
	gate = tr.create_work(store, team="push", kind="verify",
	                      title="gate", origin="external-report",
	                      classification="suspected-defect",
	                      author="sl", body="g")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	start = _time.monotonic()
	store.clock = lambda: T1 if _time.monotonic() - start > 0.15 else T0
	result = pj.wait_actionable(store, viewer_team="lang",
	                            viewer_member="ada",
	                            timeout_seconds=5.0)
	assert result["timed_out"] is False
	assert result["actionable"][0]["work"] == work
	assert _time.monotonic() - start < 4.0, \
		"the wait slept past the deadline it should wake at"


def test_wait_sees_a_competing_message_commit(world, monkeypatch):
	import threading
	# W321: same reason as the deadline case above — the subject is
	# that a commit from another connection is SEEN, not the interval
	# it is seen within.
	monkeypatch.setattr(pj, "READINESS_POLL_SECONDS", 0.05)
	store = world
	work = _provider(store)
	gate = tr.create_work(store, team="push", kind="verify",
	                      title="gate", origin="external-report",
	                      classification="suspected-defect",
	                      author="sl", body="g")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")

	def late_request():
		import time as _time
		_time.sleep(0.15)
		other = bw.Authority(store.path)
		other.clock = lambda: T0
		fx.post(other, work, author_team="lang", author="ada",
		                body="lang: self-check?", request="lang.rev")
		other.close()

	thread = threading.Thread(target=late_request)
	thread.start()
	try:
		result = pj.wait_actionable(store, viewer_team="lang",
		                            viewer_member="ada",
		                            timeout_seconds=5.0)
	finally:
		thread.join()
	assert result["timed_out"] is False
	assert result["actionable"][0]["flavor"] == "response"


def test_wait_reflects_extension_close_abandon_and_restart(world):
	store = world
	work = _provider(store)
	gate = tr.create_work(store, team="push", kind="verify",
	                      title="gate", origin="external-report",
	                      classification="suspected-defect",
	                      author="sl", body="g")["work_id"]
	tr.add_dependency(store, work, gate, actor_team="lang",
	                  actor="ada", rationale="test dependency")
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	store.now = T1
	# Extension clears the due entry: the wait times out again.
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at=T2)
	assert pj.wait_actionable(store, viewer_team="lang",
	                          viewer_member="ada",
	                          timeout_seconds=0.05)["timed_out"] is True
	# Restart sees the same derived state.
	fresh = bw.Authority(store.path)
	fresh.clock = store.clock
	store.now = T2
	woken = pj.wait_actionable(fresh, viewer_team="lang",
	                           viewer_member="ada",
	                           timeout_seconds=0.05)
	fresh.close()
	assert woken["timed_out"] is False
	# Abandon removes the trial; close removes the work: quiet either way.
	tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
	                 reason="enough")
	assert pj.wait_actionable(store, viewer_team="lang",
	                          viewer_member="ada",
	                          timeout_seconds=0.05)["timed_out"] is True
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert pj.wait_actionable(store, viewer_team="lang",
	                          viewer_member="ada",
	                          timeout_seconds=0.05)["timed_out"] is True


# -- R45: both orders of every race, two reports, and the retry boundary -----

def test_the_extension_versus_close_race_extension_first(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"],
	                review_at=T1)
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.extend_trial(
		other, work, 1, actor_team="lang", actor="ada", review_at=T2))
	# The close after a committed extension is LEGAL: both acts commit,
	# and the concluded trial records the extended window.
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="closing after the extension",
	              outcome="satisfying")
	kinds = [event["kind"] for event in store.events()]
	assert kinds.count("extend_trial") == 1
	assert kinds.count("close_work") == 1
	summary = next(event for event in store.events()
	               if event["kind"] == "close_work")["payload"][
	               "trial_summary"]
	assert summary["review_at"] == T2
	assert summary["deadline_generation"] == 2
	other.close()


def test_the_report_versus_abandon_race_report_first(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.report(
		other, created["assignments"][0], team="push", member="sl",
		observation="passed", evidence="landed first"))
	# The abandon after a committed report is LEGAL: it withdraws nothing
	# (nothing is pending) and the report is retained, not duplicated.
	tr.abandon_trial(store, work, 1, actor_team="lang", actor="ada",
	                 reason="abandoning after the report")
	view = _round_view(store, work)
	assert view["status"] == "abandoned"
	assert view["progress"] == "1/1" and view["withdrawn"] == 0
	assert [event["kind"] for event in store.events()].count("report") == 1
	other.close()


def test_the_assessment_versus_close_race_assessment_first(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="failed", evidence="crash")
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.assess(
		other, created["assignments"][0], actor_team="lang", actor="ada",
		assessment="accepted", rationale="landed first"))
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="closing after the assessment",
	              outcome="non-satisfying")
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM assessments").fetchone()["n"] == 1
	entry = _round_view(store, work)["assignments"][0]
	assert entry["effective_assessment"]["assessment"] == "accepted"
	other.close()


def test_the_new_round_versus_abandon_race_abandon_first(world):
	store = world
	work = _provider(store)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-A", assign=["push.verify"])
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.abandon_trial(
		other, work, 1, actor_team="lang", actor="ada",
		reason="abandoned first"))
	# The new trial after a committed abandon is LEGAL: trial 1 stays
	# abandoned (never re-labeled superseded) and its single withdrawal is
	# not duplicated by the supersession sweep.
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="driftc-B", assign=["web.verify"])
	assert _round_view(store, work, 1)["status"] == "abandoned"
	assert _round_view(store, work, 2)["status"] == "open"
	withdrawals = [event for event in store.events()
	               if event["kind"] == "withdraw"]
	assert len(withdrawals) == 1, "the race duplicated a withdrawal"
	other.close()


def test_two_reports_race_exactly_one_commits(world):
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"])
	other = bw.Authority(store.path)
	other.clock = lambda: store.now
	_interleave(store, lambda: tr.report(
		other, created["assignments"][0], team="push", member="sl",
		observation="passed", evidence="the first session's run"))
	with pytest.raises(bw.WorkError, match="already reported"):
		tr.report(store, created["assignments"][0], team="push",
		          member="sl", observation="failed",
		          evidence="the second session's run")
	entry = _round_view(store, work)["assignments"][0]
	assert entry["observation"] == "passed"
	assert entry["evidence"] == "the first session's run", \
		"the losing report overwrote the committed evidence"
	assert [event["kind"] for event in store.events()].count("report") == 1
	other.close()


def test_retry_without_operation_ids_refuses_and_never_duplicates(world):
	"""The PUBLIC retry limitation, stated and tested: v11 has no client
	operation identifiers, so an at-most-once retry of a completed mutation
	is NOT idempotent-by-replay — the supported boundary is a structured
	refusal with zero duplicate effects. A caller that cannot tell whether
	its first attempt committed must READ before retrying."""
	store = world
	work = _provider(store)
	created = tr.create_trial(store, work, actor_team="lang", actor="ada",
	                          candidate="driftc-A",
	                          assign=["push.verify"], review_at=T1)
	assignment = created["assignments"][0]
	tr.report(store, assignment, team="push", member="sl",
	          observation="passed", evidence="clean")
	with pytest.raises(bw.WorkError, match="already reported"):
		tr.report(store, assignment, team="push", member="sl",
		          observation="passed", evidence="clean")
	tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
	                review_at=T2)
	with pytest.raises(bw.WorkError, match="moves forward"):
		tr.extend_trial(store, work, 1, actor_team="lang", actor="ada",
		                review_at=T2)
	tr.close_work(store, work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	with pytest.raises(bw.WorkError, match="already closed"):
		tr.close_work(store, work, actor_team="lang", actor="ada",
		              rationale="done", outcome="satisfying")
	kinds = [event["kind"] for event in store.events()]
	assert kinds.count("report") == 1
	assert kinds.count("extend_trial") == 1
	assert kinds.count("close_work") == 1


def test_obligations_envelope_token_names_its_snapshot(world, monkeypatch):
	"""R46: the consistency token comes from INSIDE the read snapshot — a
	writer committing during the read cannot relabel the old rows with a
	newer sequence."""
	store = world
	store.conn.execute("PRAGMA journal_mode=WAL")
	work = _provider(store)
	fx.post(store, work, author_team="lang", author="ada",
	                body="review this", request="lang.rev")
	seq_before = store.last_seq()
	original = pj._endpoint_struct
	interleaved = False

	def close_between_queries(reader, team, kind, selected=None):
		nonlocal interleaved
		if not interleaved:
			interleaved = True
			with bw.Authority(store.path) as writer:
				writer.clock = store.clock
				tr.close_work(writer, work, actor_team="lang",
				              actor="ada", rationale="interleaved",
				              outcome="satisfying")
		return original(reader, team, kind, selected)

	monkeypatch.setattr(pj, "_endpoint_struct", close_between_queries)
	rows = pj.obligations(store, viewer_team="lang", now=T0)
	monkeypatch.setattr(pj, "_endpoint_struct", original)
	assert [entry["flavor"] for entry in rows] == ["response"], \
		"expected the wholly-before view"
	assert rows.snapshot_seq == seq_before, \
		"the token names a state later than the payload"
	assert store.last_seq() > seq_before, "the interleave never committed"


def test_summary_counts_share_one_database_snapshot(world):
	"""R46: the summary's counts and its token come from one snapshot — a
	parked-work commit between two count statements cannot produce a
	half-updated summary."""
	store = world
	store.conn.execute("PRAGMA journal_mode=WAL")
	work = _provider(store)
	real_conn = store.conn
	state = {"selects": 0, "raced": False}

	def park_via_other_session():
		other = bw.Authority(store.path)
		other.clock = store.clock
		tr.set_phase(other, work, actor_team="lang", actor="ada",
		             phase="parked", reason="interleaving proof")
		other.close()

	class RacingConn:
		def execute(self, sql, *args):
			if sql.strip().upper().startswith("SELECT") and \
					"COUNT" in sql.upper():
				state["selects"] += 1
				if state["selects"] == 2 and not state["raced"]:
					state["raced"] = True
					park_via_other_session()
			return real_conn.execute(sql, *args)

		def __getattr__(self, name):
			return getattr(real_conn, name)

	store.conn = RacingConn()
	try:
		summary = pj.team_summary(store, viewer_team="lang")
	finally:
		store.conn = real_conn
	assert state["raced"], "the interleave never fired"
	assert summary["open"] == 1 and summary["parked"] == 0, \
		f"the summary tore across the commit: {summary!r}"
	assert summary["snapshot_seq"] < store.last_seq(), \
		"the token names the post-commit state for pre-commit counts"
