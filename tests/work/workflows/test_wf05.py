"""WF-05 — three consumers converge on one provider Work (WORKFLOW-TESTS.md).

The central cross-team dependency-web acceptance under the Slice B grammar:
each consumer asks `@lang.bug` IN its own discussion, Lang ACCEPTS each into
ONE provider record — every originating discussion atomically gains the
`#LANG-42` label and the rationale answer — N:1 convergence with exact
fan-in, the second-blocker conjunction, level-triggered closure, the noise
boundary, and the label-versus-edge proof FINALLY landed: removing a label
changes no readiness, DEP, or closure fanout; the gate is the edge alone.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_wf05_three_consumers_converge(flow):
	flow.init(document(standard_teams()))

	# 1. Three independent local reports, each with its own discussion and
	# an exact request through @lang.bug.
	consumers, threads = {}, {}
	for team, member, title in (
			("push", "sl", "checkout fails"),
			("web", "wren", "render crash"),
			("mdb", "mo", "driver hang")):
		born = flow.ok("create", "--team", team, "--kind", "bug",
		               "--title", title, "--origin", "external-report",
		               "--body", f"local report: {title}",
		               viewer=f"{team}.{member}")
		work, thread = born["work_id"], born["discussion"]
		flow.ok("say", thread, "--body", "suspect the lang parser",
		        viewer=f"{team}.{member}")
		# The one labelled work is the eligible target — @ rides the
		# discussion with the selection resolved and recorded.
		flow.ok("say", thread, "--body", "lang: is this yours?",
		        "--request", "lang.bug", viewer=f"{team}.{member}")
		consumers[team], threads[team] = work, thread

	# 2. Lang relates all three to ONE provider record: each acceptance
	# atomically commits the edge with provenance, the rationale answered
	# into the ORIGINATING discussion, and that discussion's #LANG-42
	# label (audited added|existing).
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery drops state",
	                 "--origin", "external-report",
	                 "--body", "three converged reports",
	                 viewer="lang.ada")["work_id"]
	for obligation in flow.ok("obligations", viewer="lang.ada"):
		accepted = flow.ok("accept", str(obligation["seq"]),
		                   "--body", f"ours; tracked as {lang42}",
		                   "--into", lang42, viewer="lang.ada")
		assert accepted["edge"]["via_obligation"] == obligation["seq"]
	for team, member in (("push", "sl"), ("web", "wren"), ("mdb", "mo")):
		view = flow.ok("thread", threads[team],
		               viewer=f"{team}.{member}")
		assert {entry["work"] for entry in view["labels"]} == 			{consumers[team], lang42}, 			"the acceptance did not label the originating discussion"
		assert view["messages"][-1]["body"].startswith("ours; tracked"), 			"the rationale did not return to the originating discussion"
		assert "lang" in view["participants"], 			"the acceptance left no durable participation"
	assert flow.ok("detail", lang42, viewer="lang.ada")["dep"] == 3

	# The label-versus-edge proof (pinned since the finding): Lang
	# removes its OWN label from Push's discussion — readiness, DEP, and
	# the eventual closure fanout do not move; the gate is the edge.
	flow.ok("unlabel", threads["push"], "--work", lang42,
	        viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is False, 		"removing an inert label changed readiness"
	assert flow.ok("detail", lang42, viewer="lang.ada")["dep"] == 3, 		"removing an inert label changed DEP"

	# 3. Provider view shows fan-in THREE; default tables stay noise-scoped;
	# deliberate traversal opens the graph (not a security boundary).
	fan_in = flow.ok("links", lang42, viewer="lang.ada")["blocks"]
	assert [entry["id"] for entry in fan_in] == \
		[consumers["push"], consumers["web"], consumers["mdb"]]
	push_home = flow.ok("home", viewer="push.sl")
	assert [row["id"] for row in push_home["rows"]] == \
		[consumers["push"]], "another team's record entered a default table"
	assert push_home["summary"]["team"] == "push"
	via_traversal = flow.ok("links", consumers["push"],
	                        viewer="push.sl")["blocked_by"][0]["id"]
	assert via_traversal == lang42
	others = [entry["id"] for entry in
	          flow.ok("links", via_traversal, viewer="push.sl")["blocks"]]
	assert consumers["web"] in others and consumers["mdb"] in others, \
		"deliberate open-graph traversal hid the other consumers"

	# 4. MariaDB also waits on an unrelated local blocker.
	build7 = flow.ok("create", "--team", "mdb", "--kind", "build",
	                 "--title", "CI image rebuild", "--origin",
	                 "self-initiated", "--body", "blocks the driver fix",
	                 viewer="mdb.mo")["work_id"]
	flow.ok("block", consumers["mdb"], "--on", build7, viewer="mdb.mo")

	# 5. Closing LANG-42 unblocks Push and Web INDEPENDENTLY; MariaDB stays
	# blocked by BUILD-7 (multiple-blocker conjunction).
	flow.ok("close", lang42, "--rationale", "fixed and verified", "--outcome", "satisfying",
	        viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is True
	assert flow.ok("detail", consumers["web"],
	               viewer="web.wren")["ready"] is True
	mdb_view = flow.ok("detail", consumers["mdb"], viewer="mdb.mo")
	assert mdb_view["ready"] is False and mdb_view["open_blockers"] == 1, \
		"a dependent with a second open blocker became ready"

	# 6. The second blocker clears independently — level-triggered, no
	# inverse path. (The former reopen leg is superseded by WS-2 immutable
	# closure; WS2-WF-06 owns the contradiction story.)
	flow.ok("close", build7, "--rationale", "image rebuilt", "--outcome", "satisfying",
	        viewer="mdb.mo")
	assert flow.ok("detail", consumers["mdb"],
	               viewer="mdb.mo")["ready"] is True

	assert_final_invariants(flow, "lang.ada",
	                        [lang42, build7, *consumers.values()])
