"""WF-08 — handler reassignment while work is live (WORKFLOW-TESTS.md).

The C4 history-versus-current acceptance scenario through the PUBLIC surface:
route `intake` resolves to ada under generation 1; a generation-2 acceptance
reassigns it to grace. History and the obligation row keep generation 1 and
ada immutably; the live projections resolve the same stable endpoint to
grace; grace's own operations then record generation 2. Fully executable —
step 5's "responds/passes" is exercised as a pass, which records a
resolution snapshot.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_wf08_reassignment_of_live_work(flow):
	flow.init(document(standard_teams()))

	# 1. Generation 1: an obligation and a provider Current both resolving
	# through intake → rsrch → ada.
	push1 = flow.ok("create", "--team", "push", "--kind", "bug",
	                "--title", "checkout fails", "--origin",
	                "external-report", "--body", "500 at checkout",
	                viewer="push.sl")["work_id"]
	asked = flow.ok("post", push1, "--body", "lang: yours?",
	                "--request", "lang.bug", viewer="push.sl")
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--body", "accepted",
	                 viewer="lang.ada")["work_id"]
	first = flow.ok("obligations", viewer="lang.ada")[0]
	assert first["owed_by"]["handlers"] == ["ada"]

	# 2. Generation 2 reassigns the SAME live route to grace — the only
	# reassignment path is config acceptance, done through the public CLI.
	with open(flow.config_path) as handle:
		config = json.load(handle)
	config["generation"] = 2
	config["teams"]["lang"]["routes"]["intake"]["handlers"] = ["grace"]
	flow.write_config(config)
	accepted = flow.ok("regen", viewer="lang.ada")
	assert accepted["generation"] == 2

	# 3. HISTORY still names generation 1 and ada — nothing was rewritten.
	events = flow.ok("events", viewer="lang.ada")
	request_event = next(event for event in events
	                     if event["kind"] == "request")
	assert request_event["payload"]["request_resolution"] == {
		"endpoint": "lang.bug", "route": "intake", "role": "rsrch",
		"handlers": ["ada"], "generation": 1}
	create_event = next(event for event in events
	                    if event["kind"] == "create_work" and
	                    event["payload"]["team"] == "lang")
	assert create_event["payload"]["resolution"]["handlers"] == ["ada"]

	# 4. The LIVE projections resolve the stable endpoints to grace now:
	# the obligation is owed by the ENDPOINT, not the person.
	relisted = flow.ok("obligations", viewer="lang.grace")[0]
	assert relisted["owed_by"] == {"endpoint": "lang.bug",
	                               "route": "intake", "role": "rsrch",
	                               "handlers": ["grace"]}
	assert flow.ok("detail", lang42,
	               viewer="lang.grace")["current"]["handlers"] == ["grace"]

	# 5. Grace acts under generation 2; the NEW event records generation 2
	# and nothing rewrites the earlier operations.
	flow.ok("respond", str(asked["seq"]), "--body",
	        "taking over; tracked", viewer="lang.grace")
	passed = flow.ok("post", lang42, "--body", "researching",
	                 "--pass-to", "lang.impl", viewer="lang.grace")
	events = flow.ok("events", viewer="lang.grace")
	pass_event = next(event for event in events
	                  if event["seq"] == passed["seq"])
	assert pass_event["payload"]["pass_resolution"]["generation"] == 2
	again = next(event for event in events if event["kind"] == "request")
	assert again["payload"]["request_resolution"]["handlers"] == ["ada"], \
		"the generation-2 activity rewrote a generation-1 snapshot"

	flow.ok("close", lang42, "--disposition", "handed through cleanly",
	        viewer="lang.grace")
	flow.ok("close", push1, "--disposition", "answered", viewer="push.sl")
	assert_final_invariants(flow, "lang.grace", [push1, lang42])
