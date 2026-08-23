"""WF-06 — recursive release with children and external blockers
(WORKFLOW-TESTS.md).

Containment and dependency COMPOSED, and — since W1477 — kept apart: a
release root with one locally-worked child and one externally-blocked
child. The root stays runnable and claimable throughout while its children
are open, its CLOSURE refuses by naming them, only the externally blocked
child's own readiness is a dependency conjunction, and personal New
decomposes exactly with VISIBLE overlap across a thread labelled to both
children (WS-4 Slice A). (The former reopen leg is superseded by WS-2
immutable closure; WS2-WF-06 owns that story.)

Omitted (WORKFLOW-COVERAGE.md, WS-4): multiply-related thread
deduplication — needs first-class threads.

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
	root = flow.ok("create", "team=lang", "kind=rsrch",
	               "title=release 1.2.0", "origin=self-initiated", "classification=suspected-defect",
	               "body=the milestone gate", viewer="lang.ada")["work_id"]
	local = flow.ok("create", "team=lang", "kind=rsrch",
	                "title=fix recovery table",
	                "origin=decomposition", "classification=suspected-defect", "body=local leg",
	                f"parent={root}", viewer="lang.ada")["work_id"]
	blocked = flow.ok("create", "team=lang", "kind=rsrch",
	                  "title=needs the CI image",
	                  "origin=decomposition", "classification=suspected-defect", "body=externally blocked leg",
	                  f"parent={root}", viewer="lang.ada")["work_id"]

	# WS-4 Slice A: one thread labelled to BOTH children (created
	# while they are open — live context) exercises ancestor dedup later.
	shared = flow.ok("start-thread", "subject=trial subject", "body=release readiness sweep",
	                 f"label={local}", f"label={blocked}",
	                 viewer="lang.ada")["thread"]
	flow.ok("say", f"thread={shared}", "body=both legs affected",
	        viewer="lang.ada")

	# 2. One child runs WF-01 locally; the other waits on an external
	# provider work (WF-04 pattern).
	# W2571: the handoff is ada's, so ada holds it first.
	flow.ok("claim", f"work={local}", viewer="lang.ada")
	flow.ok("pass", f"work={local}", "to=lang.impl", "set-next=lang.rev",
	        "comment=build it", viewer="lang.ada")
	external = flow.ok("create", "team=mdb", "kind=build",
	                   "title=CI image rebuild",
	                   "origin=external-report", "classification=suspected-defect", "body=lang needs the image",
	                   viewer="mdb.mo")["work_id"]
	flow.ok("block", f"work={blocked}", f"on={external}",
	        "rationale=external provider required", viewer="lang.ada")

	# A union-graph cycle is refused through the public CLI — and the
	# refusal changes not one authority byte.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "block", f"work={external}", f"on={root}",
		"rationale=would cycle",
		as_viewer="mdb.mo")
	assert "closes a loop" in error

	# 3. Closing the root while children are open refuses AND NAMES them
	# — containment's one real gate, and it is a CLOSURE gate.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", f"work={root}", "rationale=shipped", "outcome=satisfying")
	assert local in error and blocked in error, \
		"the refusal does not name the open children"

	# W1477: and the root is runnable the whole time. This step used to
	# assert the opposite — that the root's readiness was a conjunction
	# over its children, so decomposing a release suspended the release.
	# Somebody coordinates the milestone WHILE its legs run; that is
	# what a milestone is.
	root_view = flow.ok("detail", f"work={root}", viewer="lang.ada")
	assert root_view["ready"] is True, \
		"open children unmade the root's readiness"
	assert root_view["phase"] == "queued" and root_view["gate"] is None
	flow.ok("claim", f"work={root}", viewer="lang.ada")
	held = flow.ok("detail", f"work={root}", viewer="lang.ada")
	assert held["phase"] == "active"
	flow.ok("release", f"work={root}", "expect=lang.ada",
	        f"episode={held['episode_seq']}",
	        "reason=back to the legs", viewer="lang.ada")

	# 4. The DEPENDENCY conjunction is the externally blocked child's
	# own, and it is untouched.
	flow.ok("claim", f"work={local}", viewer="lang.grace")
	returned = flow.ok("pass", f"work={local}", "to=lang.rev",
	                   "comment=done", viewer="lang.grace")
	assert returned["kind"] == "return"
	flow.ok("close", f"work={local}", "rationale=fixed and verified", "outcome=satisfying",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={blocked}", viewer="lang.ada")["ready"] is False, \
		"the externally blocked child ran without its provider"
	flow.ok("close", f"work={external}", "rationale=image rebuilt", "outcome=satisfying",
	        viewer="mdb.mo")
	assert flow.ok("detail", f"work={blocked}", viewer="lang.ada")["ready"] is True
	flow.ok("close", f"work={blocked}", "rationale=unblocked and done", "outcome=satisfying",
	        viewer="lang.ada")
	assert flow.ok("detail", f"work={root}", viewer="lang.ada")["ready"] is True

	# 5. Ancestor deduplication, made VISIBLE: each child counts the
	# shared thread truthfully, the root counts each message once,
	# and the exact identity total = own + sum(children) - overlap holds.
	view = flow.ok("thread", f"thread={shared}", viewer="lang.grace")
	assert {entry["work"] for entry in view["labels"]} == {local, blocked}
	breakdown = flow.ok("new", f"work={root}", viewer="lang.grace")
	assert breakdown["overlap"] >= 2, \
		"the shared thread's dedup is invisible"
	assert breakdown["subtree_total"] == breakdown["own"] + \
		sum(entry["new"] for entry in breakdown["children"]) - \
		breakdown["overlap"]
	assert breakdown["subtree_total"] > 0
	# Reading the shared thread ONCE clears it under both children.
	flow.ok("mark-seen", f"thread={shared}", f"up-to={view["last_seq"]}",
	        viewer="lang.grace")
	cleared = flow.ok("new", f"work={root}", viewer="lang.grace")
	assert cleared["overlap"] == 0
	assert cleared["subtree_total"] == cleared["own"] + \
		sum(entry["new"] for entry in cleared["children"])
	# The breadcrumb drill is deterministic from any position.
	trail = flow.ok("breadcrumb", f"work={blocked}", viewer="lang.ada")
	assert [entry["id"] for entry in trail] == [root, blocked]

	flow.ok("close", f"work={root}", "rationale=1.2.0 shipped", "outcome=satisfying",
	        viewer="lang.ada")
	assert_final_invariants(flow, "lang.ada",
	                        [root, local, blocked, external])
