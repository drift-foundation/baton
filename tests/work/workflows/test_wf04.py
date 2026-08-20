"""WF-04 — one consumer, one provider fix (WORKFLOW-TESTS.md).

The canonical cross-team happy path, extended as the draft asks: obligation
and dependency edge asserted as DISTINCT records, only the edge gating
readiness, C4 structured endpoints at every checkpoint, drill-through from
both sides, a provider close addressed to nobody, and an independent
consumer verification and close.

WS-1 extension (authorized): the provider's classification/phase legs, and
the consumer parking itself behind its recorded gate — dependency-backed
`blocked` whose atomic `wake` rides the very transaction that closes the
provider work.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_wf04_one_consumer_one_provider(flow):
	flow.init(document(standard_teams()))

	# 1. Push reports and asks Lang; Push retains Current.
	push1 = flow.ok("create", "team=push", "kind=bug",
	                "title=checkout fails after parser update",
	                "origin=external-report", "classification=suspected-defect",
	                "body=500 at checkout, trace attached",
	                viewer="push.sl")["work_id"]
	asked = flow.post(push1, "body=parser recovery bug?",
	                "request=lang.bug", "wait=false", viewer="push.sl")

	# 2. Lang accepts intake: provider work, explicit edge, response with
	# the provider id. Obligation and edge are DISTINCT records.
	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery drops state",
	                 "origin=external-report", "classification=suspected-defect",
	                 "body=accepted from push's report",
	                 viewer="lang.ada")["work_id"]
	flow.ok("block", f"work={push1}", f"on={lang42}",
	        "rationale=compiler defect gates push", viewer="push.sl")
	flow.ok("respond", f"obligation={asked["seq"]}",
	        f"body=ours; tracked as {lang42}", viewer="lang.ada")

	# The obligation is gone; the edge remains — ONLY the edge gates.
	assert flow.ok("obligations", viewer="lang.ada") == []
	blocked = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert blocked["ready"] is False
	assert blocked["open_blockers"] == 1
	assert blocked["route"] == {"endpoint": "push.bug", "route": "main",
	                              "role": "dev", "handlers": ["sl"]}, \
		"intake moved the consumer's Current"

	# WS-1: with the edge recorded, the consumer chooses honest BLOCK —
	# dependency-backed, refused if there were nothing to wait for.
	blocked = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert blocked["phase"] == "block"
	# W78: the structured gate names WHAT holds the Work and since when.
	assert blocked["gate"]["kind"] == "work"
	assert blocked["gate"]["selector"].startswith("W")
	assert blocked["gate"]["started_at"] is not None
	assert flow.ok("summary", viewer="push.sl") == \
		{"team": "push", "open": 1, "parked": 0, "blocked": 1, "due": 0}

	# The link is traversable from EITHER side.
	assert [entry["id"] for entry in
	        flow.ok("links", f"work={push1}", viewer="push.sl")["blocked_by"]] == \
		[lang42]
	assert [entry["id"] for entry in
	        flow.ok("links", f"work={lang42}", viewer="lang.ada")["blocks"]] == [push1]

	# 3. Lang classifies the accepted intake and works the phases HONESTLY:
	# each an explicit audited transition beside its pass — and every pass
	# releases the claimant and re-phases by readiness (pinned matrix).
	flow.ok("classify", f"work={lang42}", "as=confirmed-defect",
	        viewer="lang.ada")

	# W2571: every pass below is its claimant's handoff, so each leg
	# picks the Work up before handing it on.
	flow.ok("claim", f"work={lang42}", viewer="lang.ada")
	flow.ok("pass", f"work={lang42}", "to=lang.rev", "comment=analysis: recovery table clobbered",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={lang42}",
	               viewer="lang.ada")["phase"] == "queued", \
		"the pass did not record its destination phase atomically"

	flow.ok("claim", f"work={lang42}", viewer="lang.ada")
	flow.ok("pass", f"work={lang42}", "to=lang.impl", "set-next=lang.rev",
	        "comment=approach approved; build it", viewer="lang.ada")
	midway = flow.ok("detail", f"work={lang42}", viewer="lang.grace")
	assert midway["route"] == {"endpoint": "lang.impl", "route": "build",
	                             "role": "impl", "handlers": ["grace"]}
	assert midway["next"]["endpoint"] == "lang.rev"
	assert midway["phase"] == "queued", \
		"the pass did not record its destination phase atomically"
	flow.ok("claim", f"work={lang42}", viewer="lang.grace")

	returned = flow.ok("pass", f"work={lang42}", "to=lang.rev",
	                   "comment=fixed; tests attached",
	                   viewer="lang.grace")
	assert returned["kind"] == "return"
	assert flow.ok("detail", f"work={lang42}",
	               viewer="lang.ada")["phase"] == "queued", \
		"the return did not record its destination phase (and release)"
	phase_trail = [(event["payload"]["from"], event["payload"]["to"])
	               for event in flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "set_phase" and
	               event["payload"]["work"] == lang42]
	# W38: handoffs record their destination in the pass event, and the
	# scheduler axis has no role-shaped stages to move between, so an
	# ordinary story emits no set_phase acts at all.
	assert phase_trail == [], \
		"handoff states ride their pass events, not separate set_phase acts"

	# 4. Reviewer closes fixed-and-verified — addressed to NOBODY.
	flow.ok("close", f"work={lang42}", "rationale=fixed and verified", "outcome=satisfying",
	        viewer="lang.ada")

	# 5. PUSH-1 became ready because its BLOCKER changed state — and its
	# recorded wake condition was satisfied by THAT SAME transaction: one
	# atomic `wake`, phase back to queued, nothing owed to memory.
	resumed = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert resumed["ready"] is True
	assert resumed["open_blockers"] == 0
	assert resumed["phase"] == "queued", "the satisfied waiter did not wake"
	assert resumed["gate"] is None
	events_now = flow.ok("events", viewer="push.sl")
	wakes = [event for event in events_now if event["kind"] == "wake"]
	closes = [event for event in events_now
	          if event["kind"] == "close_work" and
	          event["payload"]["work"] == lang42]
	assert len(wakes) == 1, "the wake was lost or duplicated"
	assert wakes[0]["seq"] == closes[0]["seq"] + 1, \
		"the wake did not commit atomically with the provider close"
	assert flow.ok("summary", viewer="push.sl")["blocked"] == 0
	assert resumed["route"]["endpoint"] == "push.bug", \
		"the provider close moved the consumer's Current"
	flow.post(push1, "body=verified on staging",
	        viewer="push.sl")
	flow.ok("close", f"work={push1}", "rationale=verified fixed upstream", "outcome=satisfying",
	        viewer="push.sl")

	events = assert_final_invariants(flow, "push.sl", [push1, lang42])
	provider_close = next(event for event in events
	                      if event["kind"] == "close_work" and
	                      event["payload"]["work"] == lang42)
	assert "endpoint" not in provider_close["payload"]
	assert "recipient" not in provider_close["payload"]
	# Every handoff snapshot on the provider trail is complete and gen-1.
	for event in events:
		for key in ("resolution", "pass_resolution", "next_resolution",
		            "request_resolution"):
			snapshot = event["payload"].get(key)
			if snapshot is not None:
				assert snapshot["handlers"] and snapshot["generation"] == 1
