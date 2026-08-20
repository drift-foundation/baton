"""WF-01 — one-team straight-through report (WORKFLOW-TESTS.md).

The smallest complete workflow and the vocabulary baseline: report → pass
with planned Next → evidence → consuming return → terminal close.

WS-1 extension (authorized): public classification and the explicit
research → active → review phases, including review → active rework, while
proving a pass moves the baton WITHOUT touching phase — and that transition
authority follows the baton to the new Route's handlers.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_final_invariants, document,     # noqa: E402
                      standard_teams)


def test_wf01_straight_through_report(flow):
	flow.init(document(standard_teams()))

	# 1. lang.ada creates the report at lang.rsrch, immutable origin.
	work = flow.ok("create", "team=lang", "kind=rsrch",
	               "title=parser drops recovery state",
	               "origin=external-report", "classification=suspected-defect",
	               "body=reported with a minimal repro",
	               viewer="lang.ada")["work_id"]
	checkpoint = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert checkpoint["status"] == "open"
	assert checkpoint["origin"] == "external-report"
	assert checkpoint["classification"] == "suspected-defect", \
		"the submitted concrete classification did not arrive"
	assert checkpoint["phase"] == "queued"
	assert checkpoint["route"] == {"endpoint": "lang.rsrch",
	                                 "route": "intake", "role": "rsrch",
	                                 "handlers": ["ada"]}
	assert checkpoint["next"] is None

	# WS-1: research classifies the report and moves into research phase —
	# two EXPLICIT audited operations by the Route's handler.
	flow.ok("classify", f"work={work}", "as=confirmed-defect", viewer="lang.ada")
	flow.ok("phase", f"work={work}", "to=parked", "reason=deferring", viewer="lang.ada")
	checkpoint = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert checkpoint["classification"] == "confirmed-defect"
	assert checkpoint["phase"] == "parked"
	assert checkpoint["origin"] == "external-report", \
		"classification changed origin"

	# 2. research passes to implementation with planned Next lang.rev.
	# W2571: a pass is the current claimant's handoff, so ada picks the
	# Work up before handing it on — and a PARKED Work cannot be claimed
	# at all, so the deliberate deferral above is lifted first. The two
	# refusals are asserted rather than merely avoided: they are the
	# contract this step now teaches.
	error = flow.refuse("pass", f"work={work}", "to=lang.impl",
	                    "comment=confirmed; implement", viewer="lang.ada")
	assert "unclaimed and parked" in error, error
	flow.ok("phase", f"work={work}", "to=queued",
	        "reason=resuming", viewer="lang.ada")
	error = flow.refuse("pass", f"work={work}", "to=lang.impl",
	                    "comment=confirmed; implement", viewer="lang.ada")
	assert "is unclaimed" in error, error
	flow.ok("claim", f"work={work}", viewer="lang.ada")
	passed = flow.ok("pass", f"work={work}", "to=lang.impl",
	                 "set-next=lang.rev",
	                 "comment=confirmed; implement", viewer="lang.ada")
	assert passed["kind"] == "pass"
	checkpoint = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert checkpoint["route"]["endpoint"] == "lang.impl"
	assert checkpoint["route"]["handlers"] == ["grace"]
	assert checkpoint["next"]["endpoint"] == "lang.rev", \
		"the planned return is not visible while unconsumed"
	assert checkpoint["origin"] == "external-report"
	assert checkpoint["phase"] == "queued", \
		"the pass did not record its destination phase atomically"
	# Transition authority FOLLOWED the baton: ada (no longer a Route
	# handler) is refused; grace CLAIMS the work, and W38 makes that
	# claim the thing that turns it active.
	error = flow.refuse("phase", f"work={work}", "to=parked",
	                    "reason=not mine", viewer="lang.ada")
	assert "never grant" in error
	flow.ok("claim", f"work={work}", viewer="lang.grace")

	# 3. implementation posts evidence, then passes to the PLANNED review —
	# which consumes Next and audits as `return`.
	flow.post(work, "body=fix at rev 4f2c; tests attached",
	        viewer="lang.grace")
	returned = flow.ok("pass", f"work={work}", "to=lang.rev",
	                   "comment=done, please verify",
	                   viewer="lang.grace")
	assert returned["kind"] == "return"
	checkpoint = flow.ok("detail", f"work={work}", viewer="lang.grace")
	assert checkpoint["route"]["endpoint"] == "lang.rev"
	assert checkpoint["next"] is None, "the consumed Next is still set"
	assert checkpoint["phase"] == "queued", \
		"the return did not record its destination phase (and release)"

	# 4. one honest review → active → review REWORK cycle: ordinary open
	# phases move freely and never touch the claim.
	flow.ok("claim", f"work={work}", viewer="lang.ada")
	flow.ok("phase", f"work={work}", "to=queued", viewer="lang.ada")

	# Review records verification and closes terminally.
	flow.ok("close", f"work={work}", "rationale=fixed and verified", "outcome=satisfying",
	        viewer="lang.ada")
	checkpoint = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert checkpoint["status"] == "closed"
	assert checkpoint["origin"] == "external-report", \
		"the terminal close changed immutable origin"

	# The trail: ordered, and every handoff carries its resolution snapshot.
	events = assert_final_invariants(flow, "lang.ada", [work])
	# W2571 adds two acts to this story, both of them the point: the
	# resume that makes the parked Work claimable, and ada's own claim
	# before handing it on.
	assert [event["kind"] for event in events] == \
		["accept_config", "create_work", "classify", "set_phase",
		 "set_phase", "claim", "pass", "claim", "post_message", "return",
		 "claim", "set_phase", "close_work"]
	classified = events[2]
	assert (classified["payload"]["from"],
	        classified["payload"]["to"]) == ("suspected-defect", "confirmed-defect")
	assert classified["payload"]["resolution"]["handlers"] == ["ada"]
	phase_trail = [(event["payload"]["from"], event["payload"]["to"])
	               for event in events if event["kind"] == "set_phase"]
	# W38: the park, W2571's resume that makes it claimable again, and
	# the release the reviewer's own queued move performs after
	# claiming.
	assert phase_trail == [("queued", "parked"), ("parked", "queued"),
	                       ("active", "queued")]
	created, handoff = events[1], events[6]
	consumed, closing = events[9], events[12]
	assert created["payload"]["resolution"] == {
		"endpoint": "lang.rsrch", "route": "intake", "role": "rsrch",
		"handlers": ["ada"], "generation": 1}
	assert handoff["payload"]["pass_resolution"]["endpoint"] == "lang.impl"
	assert handoff["payload"]["pass_resolution"]["handlers"] == ["grace"]
	assert handoff["payload"]["next_resolution"]["endpoint"] == "lang.rev"
	assert consumed["payload"]["pass_resolution"] == {
		"endpoint": "lang.rev", "route": "review", "role": "rev",
		"handlers": ["ada"], "generation": 1}
	assert consumed["payload"]["consumed_next"] is True
	# The terminal close names a disposition and NO recipient of any kind.
	assert closing["payload"]["rationale"] == "fixed and verified"
	assert "endpoint" not in closing["payload"]
	assert "recipient" not in closing["payload"]
