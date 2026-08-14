"""WF-01 — one-team straight-through report (WORKFLOW-TESTS.md).

The smallest complete workflow and the vocabulary baseline: report → pass
with planned Next → evidence → consuming return → terminal close.

WS-1 extension (authorized): public classification and the explicit
research → active → review phases, including review → active rework, while
proving a pass moves the baton WITHOUT touching phase — and that transition
authority follows the baton to the new Current route's handlers.
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
	work = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	               "--title", "parser drops recovery state",
	               "--origin", "external-report",
	               "--body", "reported with a minimal repro",
	               viewer="lang.ada")["work_id"]
	checkpoint = flow.ok("detail", work, viewer="lang.ada")
	assert checkpoint["status"] == "open"
	assert checkpoint["origin"] == "external-report"
	assert checkpoint["classification"] == "unknown", \
		"classification arrived null instead of canonical unknown"
	assert checkpoint["phase"] == "queued"
	assert checkpoint["current"] == {"endpoint": "lang.rsrch",
	                                 "route": "intake", "role": "rsrch",
	                                 "handlers": ["ada"]}
	assert checkpoint["next"] is None

	# WS-1: research classifies the report and moves into research phase —
	# two EXPLICIT audited operations by the Current route's handler.
	flow.ok("classify", work, "--as", "confirmed-defect", viewer="lang.ada")
	flow.ok("phase", work, "--to", "research", viewer="lang.ada")
	checkpoint = flow.ok("detail", work, viewer="lang.ada")
	assert checkpoint["classification"] == "confirmed-defect"
	assert checkpoint["phase"] == "research"
	assert checkpoint["origin"] == "external-report", \
		"classification changed origin"

	# 2. research passes to implementation with planned Next lang.rev.
	passed = flow.ok("post", work, "--body", "confirmed; implement",
	                 "--pass-to", "lang.impl", "--set-next", "lang.rev",
	                 viewer="lang.ada")
	assert passed["kind"] == "pass"
	checkpoint = flow.ok("detail", work, viewer="lang.ada")
	assert checkpoint["current"]["endpoint"] == "lang.impl"
	assert checkpoint["current"]["handlers"] == ["grace"]
	assert checkpoint["next"]["endpoint"] == "lang.rev", \
		"the planned return is not visible while unconsumed"
	assert checkpoint["origin"] == "external-report"
	assert checkpoint["phase"] == "research", \
		"the pass silently rewrote operational phase"
	# Transition authority FOLLOWED the baton: ada (no longer a Current
	# handler) is refused; grace moves the work into active.
	error = flow.refuse("phase", work, "--to", "active", viewer="lang.ada")
	assert "never grant" in error
	flow.ok("phase", work, "--to", "active", viewer="lang.grace")

	# 3. implementation posts evidence, then passes to the PLANNED review —
	# which consumes Next and audits as `return`.
	flow.ok("post", work, "--body", "fix at rev 4f2c; tests attached",
	        viewer="lang.grace")
	returned = flow.ok("post", work, "--body", "done, please verify",
	                   "--pass-to", "lang.rev", viewer="lang.grace")
	assert returned["kind"] == "return"
	checkpoint = flow.ok("detail", work, viewer="lang.grace")
	assert checkpoint["current"]["endpoint"] == "lang.rev"
	assert checkpoint["next"] is None, "the consumed Next is still set"
	assert checkpoint["phase"] == "active", \
		"the return silently rewrote operational phase"

	# 4. review — including one honest review → active → review REWORK
	# cycle: ordinary open phases move freely, and every step is audited.
	flow.ok("phase", work, "--to", "review", viewer="lang.ada")
	flow.ok("phase", work, "--to", "active", viewer="lang.ada")
	flow.ok("phase", work, "--to", "review", viewer="lang.ada")

	# Review records verification and closes terminally.
	flow.ok("close", work, "--disposition", "fixed and verified",
	        viewer="lang.ada")
	checkpoint = flow.ok("detail", work, viewer="lang.ada")
	assert checkpoint["status"] == "closed"
	assert checkpoint["origin"] == "external-report", \
		"the terminal close changed immutable origin"

	# The trail: ordered, and every handoff carries its resolution snapshot.
	events = assert_final_invariants(flow, "lang.ada", [work])
	assert [event["kind"] for event in events] == \
		["accept_config", "create_work", "classify", "set_phase", "pass",
		 "set_phase", "post_message", "return", "set_phase", "set_phase",
		 "set_phase", "close_work"]
	classified = events[2]
	assert (classified["payload"]["from"],
	        classified["payload"]["to"]) == ("unknown", "confirmed-defect")
	assert classified["payload"]["resolution"]["handlers"] == ["ada"]
	phase_trail = [(event["payload"]["from"], event["payload"]["to"])
	               for event in events if event["kind"] == "set_phase"]
	assert phase_trail == [("queued", "research"), ("research", "active"),
	                       ("active", "review"), ("review", "active"),
	                       ("active", "review")]
	created, handoff = events[1], events[4]
	consumed, closing = events[7], events[11]
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
	assert closing["payload"]["disposition"] == "fixed and verified"
	assert "endpoint" not in closing["payload"]
	assert "recipient" not in closing["payload"]
