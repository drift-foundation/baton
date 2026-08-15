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
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--body", "three consumers",
	                 viewer="lang.ada")["work_id"]
	consumers = {}
	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		work = flow.ok("create", "--team", team, "--kind", "bug",
		               "--title", f"{team} report", "--origin",
		               "external-report", "--body", "blocked on lang",
		               viewer=f"{team}.{member}")["work_id"]
		flow.ok("block", work, "--on", lang42, viewer=f"{team}.{member}")
		flow.ok("phase", work, "--to", "waiting", "--wait-on-gates",
		        viewer=f"{team}.{member}")
		consumers[team] = work
	flow.ok("close", lang42, "--disposition", "fixed and verified",
	        "--outcome", "satisfying", viewer="lang.ada")
	events = flow.ok("events", viewer="lang.ada")
	wakes = [event for event in events if event["kind"] == "wake"]
	assert len(wakes) == 3, "the satisfying close did not wake every waiter"
	for team in consumers:
		assert flow.ok("detail", consumers[team],
		               viewer="lang.ada")["phase"] == "queued"

	# 2. A later Push test contradicts the result. Every public attempt to
	# reopen or mutate LANG-42 refuses without changing bytes, sequence, or
	# dependents.
	proc = flow.raw("reopen", lang42, "--reason", "regressed",
	                viewer="lang.ada")
	assert proc.returncode != 0, "a reopen verb still exists"
	for argv in (("post", lang42, "--body", "late evidence"),
	             ("classify", lang42, "--as", "duplicate"),
	             ("phase", lang42, "--to", "queued"),
	             ("close", lang42, "--disposition", "again",
	              "--outcome", "satisfying"),
	             ("block", lang42, "--on", consumers["push"])):
		assert_refusal_changes_nothing(flow, "lang.ada", *argv)
	# New blockers may target only OPEN work — the contradiction cannot
	# silently re-block anyone through the closed record.
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "block", consumers["push"], "--on", lang42)
	assert "only open Work" in error

	# 3. Lang creates LANG-57 as the follow-up; the relationship is
	# navigable and non-gating.
	lang57 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "recovery regression", "--origin",
	                 "external-report", "--body", "push contradicts",
	                 "--follow-up-of", lang42,
	                 viewer="lang.ada")["work_id"]
	fresh = flow.ok("detail", lang57, viewer="lang.ada")
	assert fresh["follow_up_of"] == lang42
	assert fresh["ready"] is True, "the follow-up relationship gated"
	graph = flow.ok("links", lang57, viewer="lang.ada")
	assert graph["follow_up_of"]["id"] == lang42
	assert graph["follow_up_of"]["outcome"] == "satisfying"
	assert [entry["id"] for entry in
	        flow.ok("links", lang42, viewer="lang.ada")["follow_ups"]] == \
		[lang57]

	# 4. Push gains its OWN new edge; Web and MariaDB are not re-blocked.
	flow.ok("block", consumers["push"], "--on", lang57, viewer="push.sl")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is False
	for team, member in (("web", "wren"), ("mdb", "mo")):
		untouched = flow.ok("detail", consumers[team],
		                    viewer=f"{team}.{member}")
		assert untouched["ready"] is True and \
			untouched["open_blockers"] == 0, \
			f"{team} was silently re-blocked"

	# 5. Web later proves affected and adds its own explicit edge; closing
	# LANG-57 fans out only across the NEW edges. Old history unchanged.
	flow.ok("block", consumers["web"], "--on", lang57, viewer="web.wren")
	before = [event for event in flow.ok("events", viewer="lang.ada")
	          if event["payload"].get("work") == lang42 or
	          event["kind"] == "close_work" and
	          event["payload"]["work"] == lang42]
	flow.ok("close", lang57, "--disposition", "regression fixed",
	        "--outcome", "satisfying", viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is True
	assert flow.ok("detail", consumers["web"],
	               viewer="web.wren")["ready"] is True
	after = [event for event in flow.ok("events", viewer="lang.ada")
	         if event["payload"].get("work") == lang42 or
	         event["kind"] == "close_work" and
	         event["payload"]["work"] == lang42]
	assert after == before, "the follow-up's close rewrote LANG-42 history"

	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		flow.ok("close", consumers[team], "--disposition", "verified",
		        "--outcome", "satisfying", viewer=f"{team}.{member}")
	assert_final_invariants(flow, "lang.ada",
	                        [lang42, lang57, *consumers.values()])
