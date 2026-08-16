"""WS2-WF-07 — shared provider, selected verifier subset
(WORKFLOW-TESTS.md WS-2 battery).

Five consumers depend on LANG-42, but the reviewer selects only Push and
Web for staged verification: the round total is two, not five; outside
contributions stay readable evidence without touching the counter; and the
eventual explicit provider outcome fans out through all five edges while
the round's reports remain exactly the selected teams' evidence.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_final_invariants, document, team)  # noqa: E402


def _teams() -> dict:
	consumers = {}
	for name, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo"),
	                     ("infra", "ivy"), ("docs", "dot")):
		consumers[name] = team(
			name.title(),
			{member: {"display": member.title(), "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": [member]}},
			{"bug": {"display": "Bug", "route": "main"},
			 "verify": {"display": "Verify", "route": "main"}})
	consumers["lang"] = team(
		"Lang",
		{"ada": {"display": "Ada", "roles": ["dev"],
		         "capabilities": ["config"]},
		 "grace": {"display": "Grace", "roles": ["dev"]}},
		{"dev": {"display": "Developer"}},
		{"main": {"role": "dev", "handlers": ["ada"]}},
		{"rsrch": {"display": "Research", "route": "main"}})
	return consumers


MEMBERS = {"push": "sl", "web": "wren", "mdb": "mo",
           "infra": "ivy", "docs": "dot"}


def test_ws2_wf07_selected_verifier_subset(flow):
	flow.init(document(_teams()))

	# 1. Five consumer Works depend on LANG-42.
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--classification", "suspected-defect", "--body", "five consumers",
	                 viewer="lang.ada")["work_id"]
	consumers = {}
	for name, member in MEMBERS.items():
		work = flow.ok("create", "--team", name, "--kind", "bug",
		               "--title", f"{name} report", "--origin",
		               "external-report", "--classification", "suspected-defect", "--body", "blocked",
		               viewer=f"{name}.{member}")["work_id"]
		flow.ok("block", work, "--on", lang42, viewer=f"{name}.{member}")
		consumers[name] = work
	assert flow.ok("detail", lang42, viewer="lang.ada")["open_dependents"] == 5

	# 2. Lang selects ONLY Push and Web: the round total is two, not five,
	# and only the exact selected route handlers hold assignments.
	created = flow.ok("round", lang42, "--candidate", "driftc-A",
	                  "--assign", "push.verify", "--assign", "web.verify",
	                  viewer="lang.ada")
	checkpoint = flow.ok("detail", lang42, viewer="lang.ada")
	staged = checkpoint["rounds"][0]
	assert staged["assigned"] == 2 and staged["progress"] == "0/2"
	assert len(flow.ok("obligations", viewer="push.sl")) == 1
	assert len(flow.ok("obligations", viewer="web.wren")) == 1
	assert flow.ok("obligations", viewer="mdb.mo") == [], \
		"an unselected team received an actionable assignment"

	# 3. Contributions from other configured participants remain readable
	# evidence but never complete an assignment or touch the counter.
	flow.post(lang42, "--body",
	        "mdb here: our nightly run also looks clean on driftc-A",
	        viewer="mdb.mo")
	error = flow.refuse("report", str(created["assignments"][0]),
	                    "--observation", "passed", "--evidence", "n/a",
	                    viewer="mdb.mo")
	assert "ownership" in error
	assert flow.ok("detail", lang42,
	               viewer="lang.ada")["rounds"][0]["progress"] == "0/2"

	# The selected teams report; the reviewer adjudicates.
	flow.ok("report", str(created["assignments"][0]),
	        "--observation", "passed", "--evidence", "staging clean",
	        viewer="push.sl")
	flow.ok("report", str(created["assignments"][1]),
	        "--observation", "passed", "--evidence", "render farm clean",
	        viewer="web.wren")
	for assignment in created["assignments"]:
		flow.ok("assess", str(assignment), "--as", "accepted",
		        "--rationale", "relevant clean run", viewer="lang.ada")

	# 4. The reviewer closes on the selected evidence; the explicit outcome
	# fans out through ALL FIVE edges, while the round keeps exactly the
	# two selected teams' reports.
	flow.ok("close", lang42, "--rationale",
	        "verified by the selected subset", "--outcome", "satisfying",
	        viewer="lang.ada")
	for name, member in MEMBERS.items():
		resumed = flow.ok("detail", consumers[name],
		                  viewer=f"{name}.{member}")
		assert resumed["ready"] is True
		links = flow.ok("links", consumers[name],
		                viewer=f"{name}.{member}")
		assert links["blocked_by"][0]["outcome"] == "satisfying"
	final = flow.ok("detail", lang42, viewer="lang.ada")["rounds"][0]
	assert final["progress"] == "2/2" and final["assigned"] == 2, \
		"the fan-out inflated the round beyond the selected subset"

	for name, member in MEMBERS.items():
		flow.ok("close", consumers[name], "--rationale", "verified",
		        "--outcome", "satisfying", viewer=f"{name}.{member}")
	assert_final_invariants(flow, "lang.ada",
	                        [lang42, *consumers.values()])
