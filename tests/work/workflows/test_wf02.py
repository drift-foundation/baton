"""WF-02 — request information without transferring Work (WORKFLOW-TESTS.md).

Pins the difference between `+`, `@`, and `=>` by asserting FOUR distinct
states side by side at every checkpoint: visibility (participation),
attention (personal New), obligation (the actionable set), and ownership
(Current). Fully executable; no omitted steps.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_wf02_request_without_transfer(flow):
	flow.init(document(standard_teams()))

	# 1. push.sl owns PUSH-1 at push.rev.
	born = flow.ok("create", "team=push", "kind=rev",
	               "title=audit the retry path",
	               "origin=self-initiated", "classification=suspected-defect",
	               "body=sweeping the checkout retries",
	               viewer="push.sl")
	push1, thread_id = born["work_id"], born["thread"]

	# 2. `+lang.bug` raises Lang attention — and NOTHING else.
	flow.post(push1, "body=lang folks may find this relevant",
	        "include=lang.bug", viewer="push.sl")
	assert flow.ok("new", f"work={push1}", viewer="lang.ada")["total"] > 0, \
		"+ raised no attention for the included team"
	assert flow.ok("new", f"work={push1}", viewer="lang.grace")["total"] > 0
	assert flow.ok("obligations", viewer="lang.ada") == [], \
		"+ created an obligation"
	checkpoint = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert checkpoint["current"]["endpoint"] == "push.rev", \
		"+ moved Current"

	# 3. `@lang.bug` creates EXACTLY ONE obligation; ownership still push.
	requested = flow.post(push1, "body=is this yours?",
	                    "request=lang.bug", viewer="push.sl")
	assert requested["kind"] == "request"
	actionable = flow.ok("obligations", viewer="lang.ada")
	assert len(actionable) == 1
	assert actionable[0]["work"] == push1
	assert actionable[0]["owed_by"] == {"endpoint": "lang.bug",
	                                    "route": "intake", "role": "rsrch",
	                                    "handlers": ["ada"]}
	assert flow.ok("detail", f"work={push1}",
	               viewer="push.sl")["current"]["endpoint"] == "push.rev"

	# 4. A non-handler Lang member reads and contributes; the contribution
	# does not silently discharge or take over the obligation.
	flow.post(push1, "body=seen similar in the parser",
	        viewer="lang.grace")
	still = flow.ok("obligations", viewer="lang.grace")
	assert len(still) == 1 and still[0]["status"] == "pending", \
		"a mere contribution discharged the obligation"

	# Seen cursors are PERSONAL: ada catches up, grace's New is untouched.
	up_to = flow.ok("thread", f"thread={thread_id}", viewer="lang.ada")["last_seq"]
	flow.ok("mark-seen", f"thread={thread_id}", f"up-to={up_to}",
	        viewer="lang.ada")
	assert flow.ok("new", f"work={push1}", viewer="lang.ada")["total"] == 0
	assert flow.ok("new", f"work={push1}", viewer="lang.grace")["total"] > 0, \
		"one member's mark-seen moved another member's cursor"

	# 5. Lang EXPLICITLY responds; the obligation leaves the actionable set.
	flow.ok("respond", f"obligation={requested["seq"]}",
	        "body=ours; tracked in the parser epic", viewer="lang.ada")
	assert flow.ok("obligations", viewer="lang.ada") == []

	# Push continues and closes its OWN work — ownership never moved.
	flow.ok("close", f"work={push1}", "rationale=audit complete", "outcome=satisfying",
	        viewer="push.sl")
	events = assert_final_invariants(flow, "push.sl", [push1])
	assert [event["kind"] for event in events] == \
		["accept_config", "create_work", "post_message", "request",
		 "post_message", "mark_seen", "respond", "close_work"]
