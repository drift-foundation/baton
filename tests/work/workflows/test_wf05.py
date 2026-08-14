"""WF-05 — three consumers converge on one provider Work (WORKFLOW-TESTS.md).

The central cross-team dependency-web acceptance: N:1 convergence with exact
fan-in, the second-blocker conjunction, level-triggered close → reopen →
re-close with no inverse-path bookkeeping, and the noise boundary — default
tables stay local while deliberate link traversal opens the graph.

Omitted (WORKFLOW-COVERAGE.md, WS-4): the label-versus-edge proof — no label
surface exists yet, so "labels never gate" cannot be stated positively.
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
	consumers = {}
	for team, member, title in (
			("push", "sl", "checkout fails"),
			("web", "wren", "render crash"),
			("mdb", "mo", "driver hang")):
		work = flow.ok("create", "--team", team, "--kind", "bug",
		               "--title", title, "--origin", "external-report",
		               "--body", f"local report: {title}",
		               viewer=f"{team}.{member}")["work_id"]
		flow.ok("post", work, "--body", "suspect the lang parser",
		        viewer=f"{team}.{member}")
		flow.ok("post", work, "--body", "lang: is this yours?",
		        "--request", "lang.bug", viewer=f"{team}.{member}")
		consumers[team] = work

	# 2. Lang relates all three to ONE provider record and each consumer
	# records an explicit dependency edge.
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery drops state",
	                 "--origin", "external-report",
	                 "--body", "three converged reports",
	                 viewer="lang.ada")["work_id"]
	for obligation in flow.ok("obligations", viewer="lang.ada"):
		flow.ok("respond", str(obligation["seq"]),
		        "--body", f"ours; tracked as {lang42}", viewer="lang.ada")
	flow.ok("block", consumers["push"], "--on", lang42, viewer="push.sl")
	flow.ok("block", consumers["web"], "--on", lang42, viewer="web.wren")
	flow.ok("block", consumers["mdb"], "--on", lang42, viewer="mdb.mo")

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
	flow.ok("close", lang42, "--disposition", "fixed and verified",
	        viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is True
	assert flow.ok("detail", consumers["web"],
	               viewer="web.wren")["ready"] is True
	mdb_view = flow.ok("detail", consumers["mdb"], viewer="mdb.mo")
	assert mdb_view["ready"] is False and mdb_view["open_blockers"] == 1, \
		"a dependent with a second open blocker became ready"

	# 6. Reopen re-blocks every still-open dependent; re-close recomputes
	# again — level-triggered both ways, no inverse path.
	flow.ok("reopen", lang42, "--reason", "fix regressed on fuzzing",
	        viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is False
	assert flow.ok("detail", consumers["web"],
	               viewer="web.wren")["ready"] is False
	assert flow.ok("detail", consumers["mdb"],
	               viewer="mdb.mo")["open_blockers"] == 2
	flow.ok("close", lang42, "--disposition", "re-fixed, fuzz clean",
	        viewer="lang.ada")
	assert flow.ok("detail", consumers["push"],
	               viewer="push.sl")["ready"] is True
	flow.ok("close", build7, "--disposition", "image rebuilt",
	        viewer="mdb.mo")
	assert flow.ok("detail", consumers["mdb"],
	               viewer="mdb.mo")["ready"] is True

	assert_final_invariants(flow, "lang.ada",
	                        [lang42, build7, *consumers.values()])
