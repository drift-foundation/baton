"""WS2-WF-01 — one candidate, one verifier, satisfying close
(WORKFLOW-TESTS.md WS-2 battery).

The minimal staged-verification story: publish, assign, report, assess,
close — with the provider gate open and the consumer blocked throughout the
trial, and each act changing exactly what its ruling says and nothing more.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document        # noqa: E402
from ws2cast import verification_teams                        # noqa: E402


def test_ws2_wf01_one_verifier_satisfying(flow):
	flow.init(document(verification_teams()))

	# 1. Push owns PUSH-1, waiting on provider Work LANG-42.
	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=provider",
	                 viewer="lang.ada")["work_id"]
	push1 = flow.ok("create", "team=push", "kind=bug",
	                "title=checkout fails",
	                "origin=external-report", "classification=suspected-defect", "body=blocked",
	                viewer="push.sl")["work_id"]
	flow.ok("block", f"work={push1}", f"on={lang42}",
	        "rationale=compiler defect gates push", viewer="push.sl")

	# 2. Lang's Current reviewer publishes candidate driftc-A, trial 1,
	# one exact assignment to @push.verify.
	created = flow.ok("try", f"work={lang42}", "candidate=driftc-A",
	                  "assign=push.verify", viewer="lang.ada")
	assignment = str(created["assignments"][0])

	# 3. LANG-42 open, PUSH-1 blocked, the assignment actionable for the
	# live Push verifier, the trial 0/1.
	checkpoint = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	assert checkpoint["status"] == "open"
	staged = checkpoint["trials"][0]
	assert staged["progress"] == "0/1" and staged["status"] == "open"
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["ready"] is False
	actionable = flow.ok("obligations", viewer="push.sl")
	assert len(actionable) == 1 and \
		actionable[0]["flavor"] == "verification"

	# 4. Push reports passed with evidence: the immutable raw report, 1/1,
	# no dependency or Work transition, no automatic assessment.
	flow.ok("report", f"obligation={assignment}", "observation=passed",
	        "evidence=staging clean for 48h", viewer="push.sl")
	checkpoint = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	staged = checkpoint["trials"][0]
	assert staged["progress"] == "1/1"
	entry = staged["assignments"][0]
	assert entry["observation"] == "passed"
	assert entry["effective_assessment"] is None, \
		"the report arrived pre-assessed"
	assert checkpoint["status"] == "open", "a report closed the provider"
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["phase"] == \
		"waiting", "a report transitioned the consumer"

	# 5. Lang records accepted with rationale — a separate audit act that
	# still changes no workflow state.
	flow.ok("assess", f"obligation={assignment}", "as=accepted",
	        "rationale=clean run on the exact candidate",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["status"] == "open"
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["phase"] == "waiting"

	# 6. Lang closes LANG-42 satisfying, naming the trial and rationale;
	# PUSH-1 wakes because this was its LAST gate — Current,
	# classification, and open status unchanged.
	flow.ok("close", f"work={lang42}",
	        "rationale=trial 1 accepted evidence; shipping driftc-A",
	        "outcome=satisfying", viewer="lang.ada")
	resumed = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert resumed["phase"] == "queued" and resumed["ready"] is True
	assert resumed["status"] == "open"
	assert resumed["route"]["endpoint"] == "push.bug"
	closing = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")
	summary = closing["payload"]["trial_summary"]
	assert summary["candidate"] == "driftc-A"
	assert summary["progress"] == "1/1"
	assert summary["observations"]["passed"] == 1

	# 7. Push independently verifies its own Work and closes it.
	flow.post(push1, "body=confirmed on production",
	        viewer="push.sl")
	flow.ok("close", f"work={push1}", "rationale=verified fixed upstream",
	        "outcome=satisfying", viewer="push.sl")
	assert_final_invariants(flow, "lang.ada", [lang42, push1])
