"""WS2-WF-04 — failed candidate and a replacement round
(WORKFLOW-TESTS.md WS-2 battery).

An accepted failure resumes work only through the reviewer's EXPLICIT
transition; the replacement candidate is a new round whose counter starts
empty; and only the eventual explicit close ends the provider gate.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document        # noqa: E402
from ws2cast import verification_teams                        # noqa: E402


def test_ws2_wf04_failed_candidate_replacement(flow):
	flow.init(document(verification_teams()))

	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--body", "provider",
	                 viewer="lang.ada")["work_id"]
	push1 = flow.ok("create", "--team", "push", "--kind", "bug",
	                "--title", "checkout fails", "--origin",
	                "external-report", "--body", "blocked",
	                viewer="push.sl")["work_id"]
	flow.ok("block", push1, "--on", lang42, viewer="push.sl")

	# 1. Candidate driftc-A; Push reports failed; Lang ACCEPTS the failure
	# as relevant evidence.
	first = flow.ok("round", lang42, "--candidate", "driftc-A",
	                "--assign", "push.verify", "--assign", "web.verify",
	                viewer="lang.ada")
	flow.ok("report", str(first["assignments"][0]),
	        "--observation", "failed", "--evidence", "checkout still 500s",
	        viewer="push.sl")
	flow.ok("assess", str(first["assignments"][0]), "--as", "accepted",
	        "--rationale", "genuine regression in the candidate",
	        viewer="lang.ada")

	# 2. LANG-42 is still open and the dependency still unsatisfied.
	assert flow.ok("detail", lang42, viewer="lang.ada")["status"] == "open"
	assert flow.ok("detail", push1, viewer="push.sl")["ready"] is False

	# 3. Lang EXPLICITLY returns to implementation — the report itself
	# caused no transition.
	assert flow.ok("detail", lang42, viewer="lang.ada")["phase"] == \
		"queued", "the accepted failure transitioned the provider"
	flow.ok("phase", lang42, "--to", "active", viewer="lang.ada")

	# 4. Different candidate driftc-B: round 2, its counter starts empty —
	# candidate identity is immutable inside round 1, and round 1's report
	# does not carry forward.
	second = flow.ok("round", lang42, "--candidate", "driftc-B",
	                 "--assign", "push.verify", viewer="lang.ada")
	assert second["round"] == 2
	rounds = flow.ok("detail", lang42, viewer="lang.ada")["rounds"]
	old, fresh = rounds[0], rounds[1]
	assert old["candidate"] == "driftc-A" and \
		fresh["candidate"] == "driftc-B"
	assert fresh["progress"] == "0/1", "round 1 evidence carried forward"

	# 5. The pending round-1 assignment (web) was explicitly withdrawn and
	# notified; both rounds remain ordered audit evidence.
	assert old["status"] == "superseded"
	assert old["progress"] == "1/2" and old["withdrawn"] == 1
	withdrawals = [event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "withdraw"]
	assert [event["payload"]["endpoint"] for event in withdrawals] == \
		["web.verify"]

	# 6. Round 2 completes; only THIS explicit close ends the provider
	# gate.
	flow.ok("report", str(second["assignments"][0]),
	        "--observation", "passed", "--evidence", "checkout clean",
	        viewer="push.sl")
	flow.ok("assess", str(second["assignments"][0]), "--as", "accepted",
	        "--rationale", "fix verified on the replacement",
	        viewer="lang.ada")
	assert flow.ok("detail", push1, viewer="push.sl")["ready"] is False, \
		"a report or assessment ended the provider gate"
	flow.ok("close", lang42, "--disposition",
	        "driftc-B verified by the affected consumer",
	        "--outcome", "satisfying", viewer="lang.ada")
	assert flow.ok("detail", push1, viewer="push.sl")["ready"] is True
	summary = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")["payload"][
	               "round_summary"]
	assert summary["candidate"] == "driftc-B", \
		"the close audited the superseded round instead of the concluded one"

	flow.ok("close", push1, "--disposition", "verified upstream",
	        "--outcome", "satisfying", viewer="push.sl")
	assert_final_invariants(flow, "lang.ada", [lang42, push1])
