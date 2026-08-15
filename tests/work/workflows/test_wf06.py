"""WF-06 — recursive release with children and external blockers
(WORKFLOW-TESTS.md).

Containment and dependency COMPOSED: a release root with one locally-worked
child and one externally-blocked child; the root's readiness is the
conjunction of both, closure refuses by naming open children, and personal
New decomposes exactly with VISIBLE overlap across a discussion labelled to
both children (WS-4 Slice A). (The former reopen leg is superseded by WS-2
immutable closure; WS2-WF-06 owns that story.)

Omitted (WORKFLOW-COVERAGE.md, WS-4): multiply-related discussion
deduplication — needs first-class discussions.

Defect found by this workflow (workflow-to-regression rule): the cycle-
refusal checkpoint exposed that the PACKAGED artifact exited 0 on every
refusal — zipapp's __main__ discards the target's return value. Extracted
regression: `test_packaged.test_a_refusal_exits_nonzero_through_the_archive`;
fix: the archive targets `cli:entry`, which owns the exit status.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_final_invariants,                # noqa: E402
                      assert_refusal_changes_nothing, document,
                      standard_teams)


def test_wf06_recursive_release(flow):
	flow.init(document(standard_teams()))

	# 1. The release root and its two children.
	root = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	               "--title", "release 1.2.0", "--origin", "self-initiated",
	               "--body", "the milestone gate", viewer="lang.ada")["work_id"]
	local = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                "--title", "fix recovery table", "--origin",
	                "decomposition", "--body", "local leg",
	                "--parent", root, viewer="lang.ada")["work_id"]
	blocked = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                  "--title", "needs the CI image", "--origin",
	                  "decomposition", "--body", "externally blocked leg",
	                  "--parent", root, viewer="lang.ada")["work_id"]

	# WS-4 Slice A: one discussion labelled to BOTH children (created
	# while they are open — live context) exercises ancestor dedup later.
	shared = flow.ok("discuss", "--body", "release readiness sweep",
	                 "--label", local, "--label", blocked,
	                 viewer="lang.ada")["discussion"]
	flow.ok("say", shared, "--body", "both legs affected",
	        viewer="lang.ada")

	# 2. One child runs WF-01 locally; the other waits on an external
	# provider work (WF-04 pattern).
	flow.post(local, "--body", "build it", "--pass-to", "lang.impl",
	        "--set-next", "lang.rev", viewer="lang.ada")
	external = flow.ok("create", "--team", "mdb", "--kind", "build",
	                   "--title", "CI image rebuild", "--origin",
	                   "external-report", "--body", "lang needs the image",
	                   viewer="mdb.mo")["work_id"]
	flow.ok("block", blocked, "--on", external, viewer="lang.ada")

	# A union-graph cycle is refused through the public CLI — and the
	# refusal changes not one authority byte.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "block", external, "--on", root,
		as_viewer="mdb.mo")
	assert "closes a loop" in error

	# 3. Closing the root while children are open refuses AND NAMES them.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", root, "--rationale", "shipped", "--outcome", "satisfying")
	assert local in error and blocked in error, \
		"the refusal does not name the open children"

	# 4. Readiness is the CONJUNCTION: the local child alone is not enough.
	returned = flow.post(local, "--body", "done", "--pass-to",
	                   "lang.rev", viewer="lang.grace")
	assert returned["kind"] == "return"
	flow.ok("close", local, "--rationale", "fixed and verified", "--outcome", "satisfying",
	        viewer="lang.ada")
	assert flow.ok("detail", root, viewer="lang.ada")["ready"] is False, \
		"the root became ready with an externally blocked child open"
	flow.ok("close", external, "--rationale", "image rebuilt", "--outcome", "satisfying",
	        viewer="mdb.mo")
	assert flow.ok("detail", blocked, viewer="lang.ada")["ready"] is True
	flow.ok("close", blocked, "--rationale", "unblocked and done", "--outcome", "satisfying",
	        viewer="lang.ada")
	assert flow.ok("detail", root, viewer="lang.ada")["ready"] is True

	# 5. Ancestor deduplication, made VISIBLE: each child counts the
	# shared discussion truthfully, the root counts each message once,
	# and the exact identity total = own + sum(children) - overlap holds.
	view = flow.ok("thread", shared, viewer="lang.grace")
	assert {entry["work"] for entry in view["labels"]} == {local, blocked}
	breakdown = flow.ok("new", root, viewer="lang.grace")
	assert breakdown["overlap"] >= 2, \
		"the shared discussion's dedup is invisible"
	assert breakdown["total"] == breakdown["own"] + \
		sum(entry["new"] for entry in breakdown["children"]) - \
		breakdown["overlap"]
	assert breakdown["total"] > 0
	# Reading the shared discussion ONCE clears it under both children.
	flow.ok("mark-seen", shared, "--up-to", str(view["last_seq"]),
	        viewer="lang.grace")
	cleared = flow.ok("new", root, viewer="lang.grace")
	assert cleared["overlap"] == 0
	assert cleared["total"] == cleared["own"] + \
		sum(entry["new"] for entry in cleared["children"])
	# The breadcrumb drill is deterministic from any position.
	trail = flow.ok("breadcrumb", blocked, viewer="lang.ada")
	assert [entry["id"] for entry in trail] == [root, blocked]

	flow.ok("close", root, "--rationale", "1.2.0 shipped", "--outcome", "satisfying",
	        viewer="lang.ada")
	assert_final_invariants(flow, "lang.ada",
	                        [root, local, blocked, external])
