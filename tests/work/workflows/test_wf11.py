"""WF-11 — assigned Work revisions preserve accountable scope
(WORKFLOW-TESTS.md).

A requester proposes complete contracts in the labelled thread but
cannot revise assigned Work directly; the Route handler promotes each
durable message as an append-only, compare-and-swap revision; transfer
of Current transfers the authority; new independently accountable
results become child Work; terminal history is immutable. JSON exposes
one effective revision and the ordered history with complete
self-contained content — no thread replay, no fixed contract
fields, no template machinery.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document)
from ws2cast import verification_teams                        # noqa: E402


def test_wf11_work_revisions(flow):
	flow.init(document(verification_teams()))

	# 1. Open Work its handler CLAIMS (W288: the contract is promoted by
	# whoever is executing it, not by anyone the route makes eligible),
	# and its labelled thread; a requester posts a COMPLETE proposed
	# contract; the claimant promotes it as revision 1 naming expected
	# revision 0 and a rationale.
	born = flow.ok("create", "team=lang", "kind=rsrch",
	               "title=parser recovery",
	               "origin=external-report", "classification=suspected-defect", "body=initial statement",
	               viewer="lang.ada")
	work, thread = born["work_id"], born["thread"]
	flow.ok("claim", f"work={work}", viewer="lang.ada")
	proposed = flow.ok("say", f"thread={thread}",
	                   "body=complete contract v1: recover the parser "
	                   "without dropping state; acceptance: replay "
	                   "suite green", viewer="push.sl")["seq"]
	promoted = flow.ok("revise", f"work={work}", f"message={proposed}",
	                   "expect=0",
	                   "rationale=agreed at intake", viewer="lang.ada")
	assert promoted["revision"] == 1
	detail = flow.ok("detail", f"work={work}", viewer="lang.ada")
	effective = detail["revision"]
	assert effective["revision"] == 1 and effective["prior"] == 0
	assert effective["thread"] == thread
	assert effective["message_seq"] == proposed
	assert effective["actor"] == "lang.ada"
	assert effective["rationale"] == "agreed at intake"
	assert effective["content"].startswith("complete contract v1"), \
		"the effective contract is not readable without the thread"

	# 2. The requester posts a replacement but CANNOT revise directly;
	# the claimant evaluates and promotes revision 2, preserving
	# identity, dependencies, phase, route, and revision 1.
	replacement = flow.ok("say", f"thread={thread}",
	                      "body=complete contract v2: also preserve the "
	                      "recovery trace", viewer="push.sl")["seq"]
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "revise", f"work={work}", f"message={replacement}",
		"expect=1", "rationale=requester's own edit")
	assert "never grant" in error, \
		"the requester revised the assigned work directly"
	flow.ok("revise", f"work={work}", f"message={replacement}",
	        "expect=1", "rationale=handler accepts the refinement",
	        viewer="lang.ada")
	detail = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert detail["revision"]["revision"] == 2
	assert [entry["revision"] for entry in detail["revisions"]] == [1, 2]
	assert detail["revisions"][0]["content"].startswith(
		"complete contract v1"), "revision 1 was not preserved"
	assert detail["status"] == "open" and \
		detail["route"]["endpoint"] == "lang.rsrch"

	# The refusal matrix on the live fixture: missing message, foreign
	# provenance, empty rationale, wrong expectation — JSON refusals,
	# nothing changed.
	foreign = flow.ok("create", "team=lang", "kind=impl",
	                  "title=elsewhere",
	                  "origin=self-initiated", "classification=suspected-defect", "body=other",
	                  viewer="lang.ada")
	outside = flow.ok("say", f"thread={foreign["thread"]}",
	                  "body=written outside the work's context",
	                  viewer="lang.ada")["seq"]
	for argv, needle in (
			(("revise", f"work={work}", "expect=2", "rationale=x"),
			 "missing required message="),
			(("revise", f"work={work}", f"message={outside}",
			  "expect=2", "rationale=x"), "does not carry"),
			(("revise", f"work={work}", f"message={replacement}",
			  "expect=2", "rationale=  "), "rationale"),
			(("revise", f"work={work}", f"message={replacement}",
			  "rationale=x"), "missing required expect="),
			(("revise", f"work={work}", f"message={replacement}",
			  "expect=0", "rationale=x"), "is at revision")):
		error = assert_refusal_changes_nothing(flow, "lang.ada", *argv)
		assert needle in error, f"{argv} refused with {error!r}"

	# 3. Two Current-authored promotions both name expected revision 2:
	# exactly one becomes revision 3; the stale writer refuses without
	# mutation or sequence consumption, across restart and retry.
	left = flow.ok("say", f"thread={thread}", "body=complete contract v3-A",
	               viewer="lang.ada")["seq"]
	right = flow.ok("say", f"thread={thread}", "body=complete contract v3-B",
	                viewer="lang.ada")["seq"]
	procs = [flow.spawn("revise", f"work={work}", f"message={left}",
	                    "expect=2", "rationale=race left",
	                    viewer="lang.ada"),
	         flow.spawn("revise", f"work={work}", f"message={right}",
	                    "expect=2", "rationale=race right",
	                    viewer="lang.ada")]
	finished = [flow.finish(proc) for proc in procs]
	winners = [out for code, out, _err in finished if code == 0]
	losers = [err for code, _out, err in finished if code != 0]
	assert len(winners) == 1 and len(losers) == 1, \
		"the CAS race admitted both writers"
	assert json.loads(losers[0])["error"]
	detail = flow.ok("detail", f"work={work}", viewer="lang.ada")
	assert detail["revision"]["revision"] == 3
	assert [entry["revision"] for entry in detail["revisions"]] == \
		[1, 2, 3]
	assert_dense_audit(flow, "lang.ada")
	# The retry boundary: replaying the stale command (a fresh process —
	# a restart by construction) refuses again without mutation.
	stale = left if detail["revision"]["message_seq"] == right else right
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "revise", f"work={work}", f"message={stale}",
		"expect=2", "rationale=verbatim retry")
	assert "is at revision" in error

	# 4. Transfer the route: the prior handler loses the authority, and
	# W288 makes the transfer take two steps — the pass moves
	# eligibility and CLEARS current, so the incoming handler holds the
	# authority only once it actually claims.
	flow.ok("pass", f"work={work}", "to=push.bug", "comment=handing the contract to push", viewer="lang.ada")
	next_contract = flow.ok("say", f"thread={thread}",
	                        "body=complete contract v4: push owns delivery",
	                        viewer="push.sl")["seq"]
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "revise", f"work={work}",
		f"message={next_contract}", "expect=3",
		"rationale=former handler")
	assert "never grant" in error, \
		"the former handler kept revision authority after the transfer"
	# eligible now, but nobody is executing it yet
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "revise", f"work={work}",
		f"message={next_contract}", "expect=3",
		"rationale=eligible but unclaimed")
	assert "is unclaimed" in error, \
		"a routed but unclaimed Work accepted a contract promotion"
	flow.ok("claim", f"work={work}", viewer="push.sl")
	flow.ok("revise", f"work={work}", f"message={next_contract}",
	        "expect=3", "rationale=the new handler commits",
	        viewer="push.sl")
	assert flow.ok("detail", f"work={work}",
	               viewer="push.sl")["revision"]["actor"] == "push.sl"

	# 5. A newly requested independent proof is CHILD Work, not a hidden
	# revision; the parent closes only after the child concludes.
	child = flow.ok("create", "team=push", "kind=bug",
	                "title=independent replay proof",
	                "origin=decomposition", "classification=suspected-defect", "body=own accountable result",
	                f"parent={work}", viewer="push.sl")["work_id"]
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "close", f"work={work}", "rationale=premature",
		"outcome=satisfying")
	assert child in error
	flow.ok("close", f"work={child}",
	        "rationale=proof delivered and reviewed on its own record",
	        "outcome=satisfying", viewer="push.sl")

	# 6. Terminal history is immutable: no later promotion is accepted,
	# and the committed revisions survive the close untouched.
	flow.ok("close", f"work={work}", "rationale=delivered under contract v4",
	        "outcome=satisfying", viewer="push.sl")
	late = flow.ok("say", f"thread={foreign["thread"]}",
	               "body=post-terminal wish", viewer="lang.ada")["seq"]
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "revise", f"work={work}", f"message={late}",
		"expect=4", "rationale=too late")
	assert "terminal work is immutable" in error
	closed = flow.ok("detail", f"work={work}", viewer="push.sl")
	assert [entry["revision"] for entry in closed["revisions"]] == \
		[1, 2, 3, 4]
	assert closed["revision_count"] == 4
	assert closed["revisions_truncated"] is False
	assert closed["revisions_next_after"] is None
	assert closed["revision"]["content"].startswith(
		"complete contract v4"), \
		"closure disturbed the committed revision history"

	# R75: the paged pure continuation joins the history without a gap
	# or repeat — pages of 2 over 4 revisions, explicit None at the end,
	# and the bounds refuse rather than clamp.
	walked, after = [], 0
	while True:
		page = flow.ok("revisions", f"work={work}", f"after={after}",
		               "limit=2", viewer="push.sl")
		walked += [entry["revision"] for entry in page["rows"]]
		if page["next_after"] is None:
			break
		after = page["next_after"]
	assert walked == [1, 2, 3, 4], \
		"the revision pages skipped or repeated"
	for argv in (("revisions", f"work={work}", "after=-1"),
	             ("revisions", f"work={work}", "limit=0"),
	             ("revisions", f"work={work}", "limit=501")):
		error = assert_refusal_changes_nothing(flow, "push.sl", *argv)
		assert "pagination cursor" in error or "page limit" in error

	assert_dense_audit(flow, "lang.ada")
