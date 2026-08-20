"""WS2-WF-06 — immutable close, later contradiction, selective follow-up
(WORKFLOW-TESTS.md WS-2 battery).

Closure is an externally observable terminal fact. A later contradiction
cannot retract it: every mutation attempt refuses without changing a byte,
and the live continuation is follow-up Work with NEW explicit edges for
exactly the consumers it affects — prior consumers are never silently
re-blocked.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_final_invariants,                # noqa: E402
                      assert_refusal_changes_nothing, document,
                      standard_teams)


def test_ws2_wf06_immutable_close_and_follow_up(flow):
	flow.init(document(standard_teams()))

	# 1. LANG-42 satisfies three waiting consumers and closes; record the
	# resulting wakes and states.
	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=three consumers",
	                 viewer="lang.ada")["work_id"]
	consumers = {}
	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		work = flow.ok("create", f"team={team}", "kind=bug",
		               f"title={team} report",
		               "origin=external-report", "classification=suspected-defect", "body=blocked on lang",
		               viewer=f"{team}.{member}")["work_id"]
		# W38 R1: the block itself commits the `block` phase on its
		# gates — a separate phase act would refuse as redundant.
		flow.ok("block", f"work={work}", f"on={lang42}",
		        "rationale=shared provider required", viewer=f"{team}.{member}")
		consumers[team] = work
	flow.ok("close", f"work={lang42}", "rationale=fixed and verified",
	        "outcome=satisfying", viewer="lang.ada")
	events = flow.ok("events", viewer="lang.ada")
	wakes = [event for event in events if event["kind"] == "wake"]
	assert len(wakes) == 3, "the satisfying close did not wake every waiter"
	for team in consumers:
		assert flow.ok("detail", f"work={consumers[team]}",
		               viewer="lang.ada")["phase"] == "queued"

	# 2. A later Push test contradicts the result. Every public attempt to
	# reopen or mutate LANG-42 refuses without changing bytes, sequence, or
	# dependents.
	proc = flow.raw("reopen", lang42, "reason=regressed",
	                viewer="lang.ada")
	assert proc.returncode != 0, "a reopen verb still exists"
	for argv in (("say", f"thread={flow.born(lang42, 'lang.ada')}",
	              "body=late evidence"),
	             ("classify", f"work={lang42}", "as=duplicate"),
	             ("phase", f"work={lang42}", "to=parked", "reason=w38"),
	             ("close", f"work={lang42}", "rationale=again",
	              "outcome=satisfying"),
	             ("block", f"work={lang42}", f"on={consumers['push']}",
	              "rationale=would cycle")):
		assert_refusal_changes_nothing(flow, "lang.ada", *argv)
	# New blockers may target only OPEN work — the contradiction cannot
	# silently re-block anyone through the closed record.
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "block", f"work={consumers["push"]}", f"on={lang42}",
		"rationale=duplicate gate")
	assert "only open Work" in error

	# 3. Lang creates LANG-57 as the follow-up; the relationship is
	# navigable and non-gating.
	lang57 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=recovery regression",
	                 "origin=external-report", "classification=suspected-defect", "body=push contradicts",
	                 f"follow-up-of={lang42}",
	                 viewer="lang.ada")["work_id"]
	fresh = flow.ok("detail", f"work={lang57}", viewer="lang.ada")
	assert fresh["follow_up_of"] == lang42
	assert fresh["ready"] is True, "the follow-up relationship gated"
	graph = flow.ok("links", f"work={lang57}", viewer="lang.ada")
	assert graph["follow_up_of"]["id"] == lang42
	assert graph["follow_up_of"]["outcome"] == "satisfying"
	assert [entry["id"] for entry in
	        flow.ok("links", f"work={lang42}", viewer="lang.ada")["follow_ups"]] == \
		[lang57]

	# 4. Push gains its OWN new edge; Web and MariaDB are not re-blocked.
	flow.ok("block", f"work={consumers["push"]}", f"on={lang57}",
	        "rationale=follow-up provider required", viewer="push.sl")
	assert flow.ok("detail", f"work={consumers["push"]}",
	               viewer="push.sl")["ready"] is False
	for team, member in (("web", "wren"), ("mdb", "mo")):
		untouched = flow.ok("detail", f"work={consumers[team]}",
		                    viewer=f"{team}.{member}")
		assert untouched["ready"] is True and \
			untouched["open_blockers"] == 0, \
			f"{team} was silently re-blocked"

	# 5. Web later proves affected and adds its own explicit edge; closing
	# LANG-57 fans out only across the NEW edges. Old history unchanged.
	flow.ok("block", f"work={consumers["web"]}", f"on={lang57}",
	        "rationale=follow-up provider required", viewer="web.wren")
	before = [event for event in flow.ok("events", viewer="lang.ada")
	          if event["payload"].get("work") == lang42 or
	          event["kind"] == "close_work" and
	          event["payload"]["work"] == lang42]
	flow.ok("close", f"work={lang57}", "rationale=regression fixed",
	        "outcome=satisfying", viewer="lang.ada")
	assert flow.ok("detail", f"work={consumers["push"]}",
	               viewer="push.sl")["ready"] is True
	assert flow.ok("detail", f"work={consumers["web"]}",
	               viewer="web.wren")["ready"] is True
	after = [event for event in flow.ok("events", viewer="lang.ada")
	         if event["payload"].get("work") == lang42 or
	         event["kind"] == "close_work" and
	         event["payload"]["work"] == lang42]
	assert after == before, "the follow-up's close rewrote LANG-42 history"

	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		flow.ok("close", f"work={consumers[team]}", "rationale=verified",
		        "outcome=satisfying", viewer=f"{team}.{member}")
	assert_final_invariants(flow, "lang.ada",
	                        [lang42, lang57, *consumers.values()])
