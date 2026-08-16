"""WS2-WF-04 — failed candidate and a replacement round
(WORKFLOW-TESTS.md WS-2 battery).

The pinned order (R66): research, active, candidate A, review, failed
feedback, active rework, candidate B, review, successful feedback, explicit
close. An accepted failure resumes work only through the reviewer's EXPLICIT
transition; the replacement candidate is a new round whose counter starts
empty; and only the eventual explicit close ends the provider gate. The
audited event ORDER — phase acts interleaved with round creation, reports and
assessments — is asserted, not merely the phase subsequence.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document        # noqa: E402
from ws2cast import verification_teams                        # noqa: E402


def test_ws2_wf04_failed_candidate_replacement(flow):
	flow.init(document(verification_teams()))

	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=provider",
	                 viewer="lang.ada")["work_id"]
	push1 = flow.ok("create", "team=push", "kind=bug",
	                "title=checkout fails",
	                "origin=external-report", "classification=suspected-defect", "body=blocked",
	                viewer="push.sl")["work_id"]
	flow.ok("block", f"work={push1}", f"on={lang42}", viewer="push.sl")

	# 1. Research first, then the EXPLICIT move to active — candidate
	# driftc-A is cut from active work, not from research.
	flow.ok("phase", f"work={lang42}", "to=research", viewer="lang.ada")
	flow.ok("phase", f"work={lang42}", "to=active", viewer="lang.ada")
	first = flow.ok("round", f"work={lang42}", "candidate=driftc-A",
	                "assign=push.verify", "assign=web.verify",
	                viewer="lang.ada")

	# 2. The candidate is STAGED for review before any feedback exists; the
	# failed report and its acceptance land while the Work is IN review —
	# and neither transitions anything.
	flow.ok("phase", f"work={lang42}", "to=review", viewer="lang.ada")
	flow.ok("report", f"obligation={first["assignments"][0]}",
	        "observation=failed", "evidence=checkout still 500s",
	        viewer="push.sl")
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["phase"] == \
		"review", "a raw report transitioned the provider's phase"
	flow.ok("assess", f"obligation={first["assignments"][0]}", "as=accepted",
	        "rationale=genuine regression in the candidate",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["phase"] == \
		"review", "an assessment transitioned the provider's phase"

	# 3. LANG-42 is still open and the dependency still unsatisfied.
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["status"] == "open"
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["ready"] is False

	# 4. Lang EXPLICITLY resumes rework — the cyclic open-phase model:
	# review -> active is the reviewer's decision, never the feedback's.
	flow.ok("phase", f"work={lang42}", "to=active", viewer="lang.ada")

	# 5. Different candidate driftc-B: round 2, its counter starts empty —
	# candidate identity is immutable inside round 1, and round 1's report
	# does not carry forward.
	second = flow.ok("round", f"work={lang42}", "candidate=driftc-B",
	                 "assign=push.verify", viewer="lang.ada")
	assert second["round"] == 2
	rounds = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"]
	old, fresh = rounds[0], rounds[1]
	assert old["candidate"] == "driftc-A" and \
		fresh["candidate"] == "driftc-B"
	assert fresh["progress"] == "0/1", "round 1 evidence carried forward"

	# 6. The pending round-1 assignment (web) was explicitly withdrawn and
	# notified; both rounds remain ordered audit evidence.
	assert old["status"] == "superseded"
	assert old["progress"] == "1/2" and old["withdrawn"] == 1
	withdrawals = [event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "withdraw"]
	assert [event["payload"]["endpoint"] for event in withdrawals] == \
		["web.verify"]

	# 7. The replacement is staged for review; the successful feedback
	# lands while IN review, transitions nothing, and only the EXPLICIT
	# close ends the provider gate.
	flow.ok("phase", f"work={lang42}", "to=review", viewer="lang.ada")
	flow.ok("report", f"obligation={second["assignments"][0]}",
	        "observation=passed", "evidence=checkout clean",
	        viewer="push.sl")
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["phase"] == \
		"review", "a passing report transitioned the provider's phase"
	flow.ok("assess", f"obligation={second["assignments"][0]}", "as=accepted",
	        "rationale=fix verified on the replacement",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={lang42}", viewer="lang.ada")["phase"] == \
		"review", "an assessment transitioned the provider's phase"
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["ready"] is False, \
		"a report or assessment ended the provider gate"
	flow.ok("close", f"work={lang42}",
	        "rationale=driftc-B verified by the affected consumer",
	        "outcome=satisfying", viewer="lang.ada")
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["ready"] is True

	# 8. The audited ORDER, not just the phase subsequence: phase acts
	# interleave with round creation, reports and assessments exactly as
	# the story ran — dense seqs guarantee nothing hides between them.
	story = [(event["kind"], event["payload"]) for event in
	         flow.ok("events", viewer="lang.ada")
	         if event["payload"].get("work") == lang42 and
	         event["kind"] in ("set_phase", "create_round", "report",
	                           "assess", "withdraw", "close_work")]
	trail = [(kind,
	          f"{payload['from']}->{payload['to']}"
	          if kind == "set_phase" else
	          payload.get("candidate") or payload.get("assessment") or
	          payload.get("endpoint") or "")
	         for kind, payload in story]
	assert trail == [
		("set_phase", "queued->research"),
		("set_phase", "research->active"),
		("create_round", "driftc-A"),
		("set_phase", "active->review"),
		("report", "driftc-A"),
		("assess", "accepted"),
		("set_phase", "review->active"),
		("create_round", "driftc-B"),
		("withdraw", "web.verify"),
		("set_phase", "active->review"),
		("report", "driftc-B"),
		("assess", "accepted"),
		("close_work", ""),
	], "the audited interleaving is not the pinned story order"
	seqs = [event["seq"] for event in flow.ok("events", viewer="lang.ada")]
	assert seqs == sorted(seqs)
	summary = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")["payload"][
	               "round_summary"]
	assert summary["candidate"] == "driftc-B", \
		"the close audited the superseded round instead of the concluded one"

	flow.ok("close", f"work={push1}", "rationale=verified upstream",
	        "outcome=satisfying", viewer="push.sl")
	assert_final_invariants(flow, "lang.ada", [lang42, push1])
