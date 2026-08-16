"""WS2-WF-08 — abandon a round without closing Work
(WORKFLOW-TESTS.md WS-2 battery).

The reviewer ends a round while the provider Work stays open: the counter
freezes at `1/3` with two visible withdrawals and route notifications, the
candidate and its report stay immutable, no lifecycle state moves anywhere,
late responses to withdrawn assignments refuse, and a later candidate needs
a new round with new assignments.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                    # noqa: E402
                      assert_refusal_changes_nothing, document, team)


def _teams() -> dict:
	spec = {}
	for name, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		spec[name] = team(
			name.title(),
			{member: {"display": member.title(), "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": [member]}},
			{"verify": {"display": "Verify", "route": "main"}})
	spec["lang"] = team(
		"Lang",
		{"ada": {"display": "Ada", "roles": ["dev"],
		         "capabilities": ["config"]},
		 "grace": {"display": "Grace", "roles": ["dev"]}},
		{"dev": {"display": "Developer"}},
		{"main": {"role": "dev", "handlers": ["ada"]}},
		{"rsrch": {"display": "Research", "route": "main"}})
	return spec


def test_ws2_wf08_abandon_without_closing(flow):
	flow.init(document(_teams()))

	# 1. One reported and two pending assignments.
	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=candidate testing",
	                 viewer="lang.ada")["work_id"]
	created = flow.ok("round", f"work={lang42}", "candidate=driftc-A",
	                  "assign=push.verify", "assign=web.verify",
	                  "assign=mdb.verify", viewer="lang.ada")
	flow.ok("report", f"obligation={created["assignments"][0]}",
	        "observation=passed", "evidence=staging clean",
	        viewer="push.sl")

	# 2. The reviewer abandons the round; LANG-42 stays open.
	before = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	flow.ok("abandon", f"work={lang42}", "round=1",
	        "reason=strategy pivot: candidate line retired",
	        viewer="lang.ada")

	# 3. 1/3, two withdrawals, route notifications, immutable candidate and
	# report history, and NO provider/consumer lifecycle change.
	after = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	view = after["rounds"][0]
	assert view["status"] == "abandoned"
	assert view["progress"] == "1/3"
	assert view["withdrawn"] == 2 and view["pending"] == 0
	assert view["candidate"] == "driftc-A"
	reported = next(entry for entry in view["assignments"]
	                if entry["state"] == "reported")
	assert reported["observation"] == "passed"
	assert (after["status"], after["phase"], after["current"]) == \
		(before["status"], before["phase"], before["current"]), \
		"abandoning a round moved the provider's lifecycle"
	events = flow.ok("events", viewer="lang.ada")
	notified = [event["payload"]["endpoint"] for event in events
	            if event["kind"] == "withdraw"]
	assert sorted(notified) == ["mdb.verify", "web.verify"], \
		"withdrawal notifications missed a route"
	for team_viewer in ("web.wren", "mdb.mo"):
		assert flow.ok("obligations", viewer=team_viewer) == [], \
			"an abandoned round left an assignment actionable"

	# 4. Late responses to withdrawn assignments refuse — and change no
	# byte. A later candidate requires a NEW round and NEW assignments.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "report", f"obligation={created["assignments"][1]}",
		"observation=passed", "evidence=too late",
		as_viewer="web.wren")
	assert "already withdrawn" in error
	replacement = flow.ok("round", f"work={lang42}", "candidate=driftc-B",
	                      "assign=web.verify", viewer="lang.ada")
	assert replacement["round"] == 2
	fresh = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][1]
	assert fresh["progress"] == "0/1", \
		"round 1 evidence leaked into the replacement round"
	assert len(flow.ok("obligations", viewer="web.wren")) == 1

	assert_dense_audit(flow, "lang.ada")
