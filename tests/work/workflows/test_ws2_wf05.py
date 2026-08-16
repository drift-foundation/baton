"""WS2-WF-05 — a non-satisfying close returns the decision to consumers
(WORKFLOW-TESTS.md WS-2 battery).

Either terminal provider outcome ends the gate; a non-satisfying result is
visible and actionable at every consumer without ever reading as a fix —
and each consumer decides its own next move independently.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_ws2_wf05_non_satisfying_close(flow):
	flow.init(document(standard_teams()))

	# 1. Push and Web wait only on LANG-42; MariaDB waits on LANG-42 AND
	# BUILD-7.
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--classification", "suspected-defect", "--body", "three consumers",
	                 viewer="lang.ada")["work_id"]
	build7 = flow.ok("create", "--team", "mdb", "--kind", "build",
	                 "--title", "CI image", "--origin", "self-initiated", "--classification", "suspected-defect",
	                 "--body", "unrelated gate", viewer="mdb.mo")["work_id"]
	consumers = {}
	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		# Born 'limitation' so the explicit classify below records a real
		# change (creation now requires a concrete value, fresh schema).
		work = flow.ok("create", "--team", team, "--kind", "bug",
		               "--title", f"{team} report", "--origin",
		               "external-report", "--classification", "limitation", "--body", "blocked on lang",
		               viewer=f"{team}.{member}")["work_id"]
		flow.ok("classify", work, "--as", "suspected-defect",
		        viewer=f"{team}.{member}")
		flow.ok("block", work, "--on", lang42, viewer=f"{team}.{member}")
		consumers[team] = work
	flow.ok("block", consumers["mdb"], "--on", build7, viewer="mdb.mo")
	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		flow.ok("phase", consumers[team], "--to", "waiting",
		        "--wait-on-gates", viewer=f"{team}.{member}")

	# 2. Lang closes LANG-42 with explicit non-satisfying and rationale.
	flow.ok("close", lang42, "--rationale",
	        "cannot reproduce against current parser; insufficient evidence",
	        "--outcome", "non-satisfying", viewer="lang.ada")

	# 3. Push and Web become queued; MariaDB remains waiting; all three
	# retain Current and classification.
	for team, member, phase in (("push", "sl", "queued"),
	                            ("web", "wren", "queued"),
	                            ("mdb", "mo", "waiting")):
		checkpoint = flow.ok("detail", consumers[team],
		                     viewer=f"{team}.{member}")
		assert checkpoint["phase"] == phase, f"{team} phase wrong"
		assert checkpoint["status"] == "open"
		assert checkpoint["classification"] == "suspected-defect"
		assert checkpoint["current"]["endpoint"] == f"{team}.bug", \
			"the provider result moved a consumer's Current"

		# 4. The non-satisfying result is VISIBLE where the dependency
		# points — and nothing anywhere claims a fix.
		links = flow.ok("links", consumers[team],
		                viewer=f"{team}.{member}")
		provider_side = next(entry for entry in links["blocked_by"]
		                     if entry["id"] == lang42)
		assert provider_side["outcome"] == "non-satisfying"
		assert provider_side["status"] == "closed"

	closing = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")
	assert closing["payload"]["outcome"] == "non-satisfying"
	assert "fixed" not in closing["payload"]["rationale"]
	assert "recipient" not in closing["payload"], \
		"the provider close addressed a single return recipient"

	# 5. Each consumer independently chooses its ending.
	flow.post(consumers["push"], "--body",
	        "workaround: pin the previous parser", viewer="push.sl")
	flow.ok("close", consumers["push"], "--rationale",
	        "workaround shipped; upstream declined", "--outcome",
	        "non-satisfying", viewer="push.sl")
	flow.post(consumers["web"], "--body",
	        "gathering the minimized repro lang asked for",
	        viewer="web.wren")
	flow.ok("close", build7, "--rationale", "image rebuilt",
	        "--outcome", "satisfying", viewer="mdb.mo")
	assert flow.ok("detail", consumers["mdb"],
	               viewer="mdb.mo")["phase"] == "queued", \
		"the LAST gate closing did not queue the multi-gate waiter"

	assert_final_invariants(flow, "lang.ada",
	                        [lang42, build7, *consumers.values()])
