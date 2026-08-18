"""WF-07 — announcement without a notice object (WORKFLOW-TESTS.md).

There is no broadcast authority object: an announcement is an ordinary
message with `+*.*`. Attention reaches every member exactly once, creates no
obligation, moves no Current, and only an explicit personal mark-seen changes
anyone's New. Fan-out cardinality stays with `+` alone — wildcard or comma
`@`/`=>` refuse. Fully executable; no omitted steps.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                    # noqa: E402
                      assert_refusal_changes_nothing, document,
                      standard_teams)

EVERYONE = ("lang.ada", "lang.grace", "push.sl", "web.wren", "mdb.mo",
            "ops.bat")


def test_wf07_announcement(flow):
	flow.init(document(standard_teams()))

	# 1. Operations opens its Work and publishes one ordinary message +*.*.
	born = flow.ok("create", "team=ops", "kind=ops",
	               "title=maintenance window saturday",
	               "origin=self-initiated", "classification=suspected-defect",
	               "body=authority migration 02:00-03:00 UTC",
	               viewer="ops.bat")
	ops1, thread_id = born["work_id"], born["thread"]
	announced = flow.post(ops1,
	                    "body=all teams: expect a short outage",
	                    "include=*.*", viewer="ops.bat")

	# 2. Every member's attention is raised EXACTLY ONCE — a member handling
	# several endpoints (ada routes rsrch, impl and rev) still counts each
	# message once, not once per matched endpoint.
	for member in EVERYONE:
		assert flow.ok("new", f"work={ops1}", viewer=member)["own"] == 2, \
			f"{member} did not see the announcement exactly once"

	# 3. No obligation anywhere, and Current never moved.
	for team_viewer in ("lang.ada", "push.sl", "web.wren", "mdb.mo",
	                    "ops.bat"):
		assert flow.ok("obligations", viewer=team_viewer) == []
	assert flow.ok("detail", f"work={ops1}",
	               viewer="ops.bat")["route"]["endpoint"] == "ops.ops"

	# 4. One member marks seen; ONLY that member's New changes.
	up_to = flow.ok("thread", f"thread={thread_id}", viewer="web.wren")["last_seq"]
	flow.ok("mark-seen", f"thread={thread_id}", f"up-to={up_to}",
	        viewer="web.wren")
	assert flow.ok("new", f"work={ops1}", viewer="web.wren")["subtree_total"] == 0
	for member in ("lang.ada", "push.sl", "mdb.mo"):
		assert flow.ok("new", f"work={ops1}", viewer=member)["subtree_total"] > 0, \
			"one member's mark-seen changed another member's New"

	# 5. Expanding or multi-destination @ and => REFUSE — and the refusal
	# changes nothing.
	for token in ("request=lang.*", "request=*.bug",
	              "request=lang.bug,web.bug"):
		error = assert_refusal_changes_nothing(
			flow, "ops.bat", "say", f"thread={thread_id}", "body=x",
			token)
		assert "exactly one" in error
	# W80: the => operator lives on the explicit pass verb now — the
	# same expanding/multi-destination refusals, changing nothing.
	for destination in ("to=*.rev", "to=lang.rev,push.rev"):
		error = assert_refusal_changes_nothing(
			flow, "ops.bat", "pass", f"work={ops1}", destination,
			"comment=x")
		assert "exactly one" in error

	# R71: a `+` selector that lands nowhere refuses — wildcard shapes
	# included — and the refusal changes nothing.
	for selector in ("ghost.*", "*.ghost", "ops.ops,ghost.*"):
		error = assert_refusal_changes_nothing(
			flow, "ops.bat", "say", f"thread={thread_id}", "body=void",
			f"include={selector}")
		assert "matches no live endpoint" in error

	# The EXACT expansion is audited with the publication: every live
	# (team, kind) endpoint, deduplicated, fully resolved.
	events = assert_dense_audit(flow, "ops.bat")
	published = next(event for event in events
	                 if event["seq"] == announced["seq"])
	expansion = [entry["endpoint"] for entry in
	             published["payload"]["include"]]
	assert expansion == sorted(expansion) and \
		len(expansion) == len(set(expansion))
	assert set(expansion) == {
		"lang.bug", "lang.rsrch", "lang.impl", "lang.rev",
		"push.bug", "push.rev", "web.bug", "mdb.bug", "mdb.build",
		"ops.ops"}
	for entry in published["payload"]["include"]:
		assert entry["handlers"] and entry["generation"] == 1

	# And there is NO notice surface: the CLI knows no such verb, and the
	# unknown verb changes no authority byte.
	before = flow.ok("events", viewer="ops.bat")
	proc = flow.raw("notice", "body=x", viewer="ops.bat")
	assert proc.returncode != 0
	assert flow.ok("events", viewer="ops.bat") == before
