"""W2645: a reroute corrects WHERE, and never resumes a parked Work.

`work/records/2026/08/finding-reroute-unparks-deferred-work/`.
`reroute_work` re-derived its phase through `_unclaimed_state`, which
answers exactly `block` or `queued`. `parked` is not among them, so
correcting where a deliberately deferred Work was offered silently made
it runnable again — and the reason somebody recorded for deferring it
survived only in the earlier `set_phase` event.

The operation's own comment already argued the other way: the phase "is
re-derived only because a route change can change nothing about
readiness — it is asserted, not moved." For `queued` and `block` that
holds. `parked` is not a readiness fact at all; it is a decision.

The 2026-08-20 ruling: Route and scheduler phase answer separate
questions, so correcting one must not change the other. A parked reroute
keeps the phase and the reason, moves the Route, and starts the episode
that offers the Work to its corrected route when somebody explicitly
resumes it. Only `parked -> queued` resumes.

This is the same carve-out `_recompute_ready` already makes for the same
reason — a gate arriving underneath a park does not revoke the park
either (`finding-active-work-claim` R2) — which is why a parked Work may
hold open gates, and why the park wins over the gate derivation here.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402

PARK_REASON = "deferred to the next cycle"


def document():
	"""One team, two endpoints and an alternate route to a DIFFERENT
	member — enough for a reroute to genuinely move the offer."""
	base = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rev"]}})
	team = base["teams"]["lang"]
	team["routes"]["main"] = {"role": "dev", "handlers": ["ada"]}
	team["routes"]["alt"] = {"role": "dev", "handlers": ["grace"]}
	team["kinds"]["bug"] = {"display": "Bug", "route": "main",
	                        "alternates": ["alt"]}
	team["kinds"]["rev"] = {"display": "Rev", "route": "alt"}
	return base


@pytest.fixture()
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document(), handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def make(world, title="the deferred work"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="self-initiated",
	                      classification="design-choice", author="ada",
	                      body="the opener")["work_id"]


def park(world, work, reason=PARK_REASON):
	return tr.set_phase(world["store"], work, actor_team="lang",
	                    actor="ada", phase="parked", reason=reason)


def reroute(world, work, to="lang.rev", route=None,
            reason="offered at the wrong endpoint"):
	return tr.reroute_work(world["store"], work, actor_team="lang",
	                       actor="ada", to=to, route=route, reason=reason)


def row(world, work):
	return dict(world["store"].conn.execute(
		"SELECT * FROM work WHERE id=?", (work,)).fetchone())


def event(world, seq):
	return next(entry for entry in world["store"].events()
	            if entry["seq"] == seq)


def actionable(world, member):
	return [action["work"] for action in pj.wait_actionable(
		world["store"], viewer_team="lang", viewer_member=member,
		timeout_seconds=0)["actionable"] if action["kind"] == "work"]


# -- acceptance 1: the park survives the correction --------------------------

def test_a_parked_work_is_still_parked_after_a_reroute(world):
	"""The defect, directly: correcting where it is offered used to
	decide that it may run."""
	work = make(world)
	park(world, work)
	moved = reroute(world, work)
	assert moved["phase"] == "parked"
	assert row(world, work)["phase"] == "parked", \
		"the reroute resumed a deliberately deferred Work"


def test_the_route_really_moved_while_the_phase_held(world):
	"""Both halves at once — a fix that preserved the phase by refusing
	to move anything would pass the test above and defeat the point."""
	work = make(world)
	park(world, work)
	before = row(world, work)
	moved = reroute(world, work)
	after = row(world, work)
	assert (before["route_team"], before["route_kind"]) == ("lang", "bug")
	assert (after["route_team"], after["route_kind"]) == ("lang", "rev")
	assert moved["to"] == "lang.rev"
	assert after["phase"] == "parked"


def test_the_alternate_route_form_preserves_it_too(world):
	"""The other shape of the same correction: same endpoint, different
	route. It moves the offer to a different member and must not resume
	the Work either."""
	work = make(world)
	park(world, work)
	moved = reroute(world, work, to="lang.bug", route="alt")
	assert moved["route"] == "alt"
	assert moved["phase"] == "parked"
	assert row(world, work)["phase"] == "parked"


def test_the_recorded_park_reason_is_untouched(world):
	"""The reason is the whole content of a park — parked Work has no
	wake condition, so the why is all a later reader gets. It lives in
	the `set_phase` event, and nothing after the reroute may supersede
	or restate it."""
	work = make(world)
	parked = park(world, work)
	reroute(world, work)
	assert event(world, parked["seq"])["payload"]["reason"] == PARK_REASON
	later = [entry for entry in world["store"].events()
	         if entry["seq"] > parked["seq"]
	         and entry["payload"].get("work") == work]
	assert [entry["kind"] for entry in later] == ["reroute"]
	assert later[0]["payload"]["reason"] == "offered at the wrong endpoint", \
		"the reroute's own reason was confused with the park's"


def test_the_park_still_leaves_only_through_the_explicit_resume(world):
	"""What the ruling protects. After the correction the Work is still
	deferred, and the ONE transition that resumes it still does —
	offering it, now, at the corrected route."""
	work = make(world)
	park(world, work)
	reroute(world, work)
	tr.set_phase(world["store"], work, actor_team="lang", actor="grace",
	             phase="queued", reason="the cycle came round")
	after = row(world, work)
	assert after["phase"] == "queued"
	assert (after["route_team"], after["route_kind"]) == ("lang", "rev")
	assert work in actionable(world, "grace"), \
		"the resumed Work was not offered at its corrected route"


def test_the_reroute_wakes_nobody(world):
	"""Acceptance 1's other clause. A parked row is not actionable, so
	the episode the reroute mints offers the Work to nobody until the
	explicit resume — neither the old handler nor the new one."""
	work = make(world)
	park(world, work)
	reroute(world, work)
	assert actionable(world, "ada") == []
	assert actionable(world, "grace") == []


def test_the_episode_still_starts_for_the_corrected_route(world):
	"""The ruling asks for the episode explicitly: the correction is a
	real handoff of responsibility for a future resume, even though
	nothing is actionable yet."""
	work = make(world)
	park(world, work)
	before = row(world, work)["episode_seq"]
	moved = reroute(world, work)
	assert row(world, work)["episode_seq"] != before
	assert row(world, work)["episode_seq"] == moved["seq"]


def test_a_parked_work_holding_a_gate_stays_parked(world):
	"""The precedence question the carve-out settles. A gate arriving
	underneath a park does not revoke the park
	(`finding-active-work-claim` R2), so a parked Work CAN hold open
	gates — and the reroute must not let the gate derivation speak for
	the phase either."""
	work = make(world)
	park(world, work)
	tr.add_dependency(world["store"], work, make(world, "the gate"),
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	assert row(world, work)["phase"] == "parked", \
		"the gate revoked the park before this test could run"
	assert row(world, work)["ready"] == 0
	moved = reroute(world, work)
	assert moved["phase"] == "parked"
	assert row(world, work)["phase"] == "parked"


# -- acceptance 2: nothing else changed --------------------------------------

def test_a_queued_reroute_still_derives_queued(world):
	work = make(world)
	assert row(world, work)["phase"] == "queued"
	assert reroute(world, work)["phase"] == "queued"
	assert row(world, work)["phase"] == "queued"


def test_a_gated_reroute_still_derives_block(world):
	"""The case W2571's restatements depend on: with `pass` requiring
	the claim, this is the only operation that moves gated Work, and it
	must keep landing `block` with the row gated."""
	work = make(world)
	tr.add_dependency(world["store"], work, make(world, "the gate"),
	                  actor_team="lang", actor="ada",
	                  rationale="waits on it")
	assert row(world, work)["phase"] == "block"
	moved = reroute(world, work)
	assert moved["phase"] == "block"
	assert row(world, work)["phase"] == "block"
	assert row(world, work)["gate_kind"] == "work", \
		"the reroute lost the recorded wake condition"


def test_a_queued_reroute_still_offers_the_work_at_its_new_route(world):
	"""The contrast that gives the parked case its meaning: an unparked
	correction DOES wake the destination."""
	work = make(world)
	reroute(world, work)
	assert work in actionable(world, "grace")


def test_reroute_still_refuses_the_things_it_always_refused(world):
	"""A parked Work is not a licence to skip the operation's own
	guards: a no-op correction and a claimed Work still refuse."""
	work = make(world)
	park(world, work)
	with pytest.raises(bw.WorkError, match="already at"):
		reroute(world, work, to="lang.bug")
	assert row(world, work)["phase"] == "parked"


# -- acceptance 3: the event agrees with the row -----------------------------

@pytest.mark.parametrize("phase", ["parked", "queued", "block"])
def test_the_event_payload_agrees_with_the_committed_row(world, phase):
	"""The defect was visible in the payload too — it recorded `queued`
	for a row it had just written. Asserted for every phase, because
	agreement is the property, not one value."""
	work = make(world)
	if phase == "parked":
		park(world, work)
	elif phase == "block":
		tr.add_dependency(world["store"], work, make(world, "the gate"),
		                  actor_team="lang", actor="ada",
		                  rationale="waits on it")
	moved = reroute(world, work)
	payload = event(world, moved["seq"])["payload"]
	committed = row(world, work)["phase"]
	assert committed == phase
	assert payload["phase"] == committed
	assert moved["phase"] == committed
	assert [entry for entry in payload["phase_now"]
	        if entry["work"] == work] == [{"work": work, "phase": committed}]


def test_the_preserved_park_is_one_continuing_interval(world):
	"""`phase_now` records the phase on every phase-carrying event, and
	the projection replays those into intervals. Recording `parked`
	again must therefore READ as the same park continuing — not as the
	park ending and an identical one beginning, which is what a reader
	looking for "when was this deferred" would be misled by."""
	work = make(world)
	park(world, work)
	reroute(world, work)
	intervals = [entry for entry in pj._phase_intervals(
		world["store"], work, world["store"].clock()).values()
		if entry["phase"] == "parked"]
	assert len(intervals) == 1, intervals
	assert intervals[0]["open"] is True
