"""WF-10 — every terminal outcome is explicit and reviewable
(WORKFLOW-TESTS.md).

Four sibling fixtures, each carrying an open dependent, a planned Next, a
pending carried `@`, and a pending verification assignment before its
Current handler closes it: `satisfying`, `non-satisfying`, `rejected`
(plus the duplicate rejection with its explicit `duplicate_of` link), and
`cancelled` (proposer-versus-Current authority and the open-child
refusal). One close transaction dismantles the machine identically for
all four; the refusal matrix and the close races leave exactly one
compatible terminal history.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document)
from ws2cast import verification_teams                        # noqa: E402


def _rig(flow, tag):
	"""The full-featured provider each outcome must dismantle."""
	born = flow.ok("create", "team=lang", "kind=rsrch",
	               f"title=provider {tag}",
	               "origin=external-report", "classification=suspected-defect", f"body={tag}", viewer="lang.ada")
	work, thread = born["work_id"], born["thread"]
	dependent = flow.ok("create", "team=push", "kind=bug",
	                    f"title=consumer {tag}",
	                    "origin=external-report", "classification=suspected-defect", "body=waits",
	                    viewer="push.sl")["work_id"]
	flow.ok("block", f"work={dependent}", f"on={work}", viewer="push.sl")
	gated = flow.ok("create", "team=web", "kind=bug",
	                f"title=gated {tag}",
	                "origin=external-report", "classification=suspected-defect", "body=two gates",
	                viewer="web.wren")["work_id"]
	extra = flow.ok("create", "team=mdb", "kind=bug",
	                f"title=extra {tag}",
	                "origin=external-report", "classification=suspected-defect", "body=second gate",
	                viewer="mdb.mo")["work_id"]
	flow.ok("block", f"work={gated}", f"on={work}", viewer="web.wren")
	flow.ok("block", f"work={gated}", f"on={extra}", viewer="web.wren")
	flow.ok("pass", f"work={work}", "to=lang.impl", "phase=active",
	        "set-next=lang.rsrch", f"thread={thread}",
	        "comment=onward", viewer="lang.ada")
	asked = flow.ok("say", f"thread={thread}", "body=push: confirm",
	                "request=push.bug", f"on={work}",
	                viewer="lang.ada")["seq"]
	assigned = flow.ok("round", f"work={work}", f"candidate=cand-{tag}",
	                   "assign=push.verify",
	                   viewer="lang.ada")["assignments"][0]
	return {"work": work, "thread": thread, "dependent": dependent,
	        "gated": gated, "asked": asked, "assigned": assigned,
	        "tag": tag}


def _assert_dismantled(flow, rig, outcome, rationale):
	"""One close transaction: Current and Next cleared, pending
	obligations and assignments withdrawn, the dependency gate ended,
	only last-gate dependents unblocked, exact actor/outcome/rationale
	audited, terminal Work immutable."""
	detail = flow.ok("detail", f"work={rig["work"]}", viewer="lang.ada")
	assert detail["status"] == "closed" and detail["outcome"] == outcome
	assert detail["rationale"] == rationale
	assert detail["current"] is None and detail["next"] is None, \
		"the close did not clear Current and the planned Next"
	states = {entry["seq"]: entry["status"]
	          for entry in detail["obligations"]}
	assert states[rig["asked"]] == "withdrawn"
	assert states[rig["assigned"]] == "withdrawn"
	assert flow.ok("detail", f"work={rig["dependent"]}",
	               viewer="push.sl")["ready"] is True, \
		"the last-gate dependent did not unblock"
	gated = flow.ok("detail", f"work={rig["gated"]}", viewer="web.wren")
	assert gated["ready"] is False and gated["open_blockers"] == 1, \
		"a dependent with another live gate became ready"
	closing = next(event for event in flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work" and
	               event["payload"]["work"] == rig["work"])
	assert closing["actor"] == "lang.ada"
	assert closing["payload"]["outcome"] == outcome
	assert closing["payload"]["rationale"] == rationale
	assert closing["payload"]["round_summary"]["candidate"] == \
		f"cand-{rig['tag']}"
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", f"work={rig["work"]}", "rationale=again",
		f"outcome={outcome}")
	assert "already closed" in error


def test_wf10_terminal_outcomes(flow):
	flow.init(document(verification_teams()))

	# 1. Accepted work concluded and met its contract.
	first = _rig(flow, "one")
	flow.ok("close", f"work={first["work"]}",
	        "rationale=contract met: recovery verified by the affected consumer",
	        "outcome=satisfying", viewer="lang.ada")
	_assert_dismantled(flow, first, "satisfying",
	                   "contract met: recovery verified by the affected "
	                   "consumer")

	# 2. Attempted and evaluated, but the contract was not met.
	second = _rig(flow, "two")
	flow.ok("close", f"work={second["work"]}",
	        "rationale=three candidates failed the memory ceiling; stopping here",
	        "outcome=non-satisfying", viewer="lang.ada")
	_assert_dismantled(flow, second, "non-satisfying",
	                   "three candidates failed the memory ceiling; "
	                   "stopping here")

	# 3. Intake declined with an honest reason — no link required.
	third = _rig(flow, "three")
	flow.ok("close", f"work={third["work"]}",
	        "rationale=not reproducible on any supported build",
	        "outcome=rejected", viewer="lang.ada")
	_assert_dismantled(flow, third, "rejected",
	                   "not reproducible on any supported build")

	# 3b. The duplicate rejection: classification says duplicate, so free
	# text alone REFUSES; the explicit non-gating duplicate_of commits
	# and both link directions are navigable.
	canonical = _rig(flow, "canon")
	dupe = _rig(flow, "dupe")
	flow.ok("classify", f"work={dupe["work"]}", "as=duplicate",
	        viewer="lang.ada")
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", f"work={dupe["work"]}",
		"rationale=same defect as the canonical", "outcome=rejected")
	assert "free text alone" in error
	flow.ok("close", f"work={dupe["work"]}",
	        "rationale=same defect as the canonical", "outcome=rejected",
	        f"duplicate-of={canonical["work"]}", viewer="lang.ada")
	_assert_dismantled(flow, dupe, "rejected",
	                   "same defect as the canonical")
	links = flow.ok("links", f"work={dupe["work"]}", viewer="lang.ada")
	assert links["duplicate_of"]["id"] == canonical["work"]
	assert [entry["id"] for entry in
	        flow.ok("links", f"work={canonical["work"]}",
	                viewer="lang.ada")["duplicates"]] == [dupe["work"]]
	survivor = flow.ok("detail", f"work={canonical["work"]}", viewer="lang.ada")
	assert survivor["status"] == "open", \
		"the non-gating duplicate link touched the survivor"

	# 4. Cancellation: proposed in the labelled thread, committed
	# only by Current — the proposer cannot close around it.
	fourth = _rig(flow, "four")
	flow.ok("say", f"thread={fourth["thread"]}",
	        "body=propose we cancel: the feature was descoped",
	        viewer="push.sl")
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "close", f"work={fourth["work"]}",
		"rationale=descoped", "outcome=cancelled")
	assert "never grant" in error, \
		"a thread participant closed around Current"
	flow.ok("close", f"work={fourth["work"]}",
	        "rationale=descoped for this cycle; follow-up will reopen the question",
	        "outcome=cancelled", viewer="lang.ada")
	_assert_dismantled(flow, fourth, "cancelled",
	                   "descoped for this cycle; follow-up will reopen "
	                   "the question")

	# 4b. An open child prevents cancellation until that child is
	# independently concluded by its own Current — never a cascade.
	parent = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=cancellable parent",
	                 "origin=self-initiated", "classification=suspected-defect", "body=p",
	                 viewer="lang.ada")["work_id"]
	child = flow.ok("create", "team=lang", "kind=impl",
	                "title=living child",
	                "origin=decomposition", "classification=suspected-defect", "body=c", f"parent={parent}",
	                viewer="lang.ada")["work_id"]
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", f"work={parent}", "rationale=unwanted",
		"outcome=cancelled")
	assert child in error
	assert flow.ok("detail", f"work={child}",
	               viewer="lang.ada")["status"] == "open", \
		"a refused cancellation cascaded into the child"
	flow.ok("close", f"work={child}", "rationale=concluded on its own merits",
	        "outcome=satisfying", viewer="lang.ada")
	flow.ok("close", f"work={parent}", "rationale=unwanted after the descope",
	        "outcome=cancelled", viewer="lang.ada")

	# 5. The refusal matrix: empty rationale, unknown outcome, outsider
	# close, and the incompatible link — each refuses changing nothing.
	fifth = _rig(flow, "five")
	for argv, needle in (
			(("close", f"work={fifth["work"]}", "rationale=  ",
			  "outcome=satisfying"), "rationale"),
			(("close", f"work={fifth["work"]}", "rationale=x",
			  "outcome=done"), "outcome= takes one of"),
			(("close", f"work={fifth["work"]}", "rationale=x",
			  "outcome=satisfying",
			  f"duplicate-of={fourth["work"]}"), "requires outcome=rejected"),
			(("close", f"work={fifth["work"]}", "rationale=x",
			  "outcome=rejected",
			  f"duplicate-of={fifth["work"]}"), "duplicate of itself")):
		error = assert_refusal_changes_nothing(flow, "lang.ada", *argv)
		assert needle in error, f"{argv} refused with {error!r}"
	error = assert_refusal_changes_nothing(
		flow, "web.wren", "close", f"work={fifth["work"]}", "rationale=mine",
		"outcome=satisfying")
	assert "never grant" in error
	# R73: OMITTING --rationale or --outcome stays inside the JSON
	# exit-one agent contract — a structured refusal, no mutation.
	for argv, needle in (
			(("close", f"work={fifth["work"]}", "outcome=satisfying"),
			 "rationale"),
			(("close", f"work={fifth["work"]}", "rationale=words"),
			 "outcome")):
		error = assert_refusal_changes_nothing(flow, "lang.ada", *argv)
		assert needle in error, \
			f"omission {argv} escaped the JSON contract: {error!r}"
	# R74: a duplicate target must itself be canonical — a chain through
	# the already-folded record refuses, naming the survivor.
	chained = _rig(flow, "chained")
	flow.ok("classify", f"work={chained["work"]}", "as=duplicate",
	        viewer="lang.ada")
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", f"work={chained["work"]}",
		"rationale=folding into a fold", "outcome=rejected",
		f"duplicate-of={dupe["work"]}")
	assert "canonical survivor" in error
	flow.ok("close", f"work={chained["work"]}",
	        "rationale=folded into the true canonical", "outcome=rejected",
	        f"duplicate-of={canonical["work"]}", viewer="lang.ada")
	assert [entry["id"] for entry in
	        flow.ok("links", f"work={canonical["work"]}",
	                viewer="lang.ada")["duplicates"]] == \
		[dupe["work"], chained["work"]]

	# 6. Races: close against respond, report, pass, and a competing
	# close — every serialization leaves exactly ONE compatible terminal
	# history, proven from the audit order itself.
	def race(rig, other_argv, other_viewer):
		procs = [flow.spawn("close", f"work={rig["work"]}",
		                    "rationale=racing close", "outcome=satisfying",
		                    viewer="lang.ada"),
		         flow.spawn(*other_argv, viewer=other_viewer)]
		finished = [flow.finish(proc) for proc in procs]
		losers = [err for code, _out, err in finished if code != 0]
		for err in losers:
			assert json.loads(err)["error"], \
				"a racing loser got no structured refusal"
		events = assert_dense_audit(flow, "lang.ada")
		closes = [event for event in events
		          if event["kind"] == "close_work" and
		          event["payload"]["work"] == rig["work"]]
		assert len(closes) == 1, "the race admitted a second close"
		return events

	# close vs respond: whichever serialized second either refused or
	# left the obligation in its own terminal state.
	rig = _rig(flow, "race-respond")
	events = race(rig, ("respond", f"obligation={rig["asked"]}",
	                    "body=confirmed"), "push.sl")
	state = next(entry["status"] for entry in
	             flow.ok("detail", f"work={rig["work"]}",
	                     viewer="lang.ada")["obligations"]
	             if entry["seq"] == rig["asked"])
	responded = any(event["kind"] == "respond" and
	                event["payload"]["obligation"] == rig["asked"]
	                for event in events)
	assert state == ("responded" if responded else "withdrawn"), \
		"the obligation's terminal state contradicts the audit order"

	# close vs report: a report that serialized first is counted in the
	# close's audited round summary.
	rig = _rig(flow, "race-report")
	events = race(rig, ("report", f"obligation={rig["assigned"]}",
	                    "observation=passed", "evidence=ok"),
	              "push.sl")
	closing = next(event for event in events
	               if event["kind"] == "close_work" and
	               event["payload"]["work"] == rig["work"])
	reported = any(event["kind"] == "report" and
	               event["payload"]["obligation"] == rig["assigned"]
	               for event in events)
	assert closing["payload"]["round_summary"]["progress"] == \
		("1/1" if reported else "0/1")

	# close vs pass: the close that lost the serialization refused; a
	# close that won recorded the Current AS COMMITTED.
	rig = _rig(flow, "race-pass")
	events = race(rig, ("pass", f"work={rig["work"]}",
	                    "to=lang.rsrch", "phase=research",
	                    f"thread={rig["thread"]}", "comment=detour"),
	              "lang.ada")
	closing = next(event for event in events
	               if event["kind"] == "close_work" and
	               event["payload"]["work"] == rig["work"])
	passed = [event for event in events
	          if event["kind"] in ("pass", "return") and
	          event["payload"].get("work") == rig["work"] and
	          event["seq"] < closing["seq"]]
	expected = "rsrch" if passed and \
		passed[-1]["payload"]["pass"] == "lang.rsrch" else "impl"
	assert closing["payload"]["was_current_kind"] == expected, \
		"the close audited a Current the commit no longer had"

	# close vs close: exactly one terminal act, one refusal.
	rig = _rig(flow, "race-close")
	procs = [flow.spawn("close", f"work={rig["work"]}", "rationale=first",
	                    "outcome=satisfying", viewer="lang.ada"),
	         flow.spawn("close", f"work={rig["work"]}", "rationale=second",
	                    "outcome=cancelled", viewer="lang.ada")]
	finished = [flow.finish(proc) for proc in procs]
	winners = [out for code, out, _err in finished if code == 0]
	losers = [err for code, _out, err in finished if code != 0]
	assert len(winners) == 1 and len(losers) == 1
	assert "already closed" in json.loads(losers[0])["error"]

	assert_dense_audit(flow, "lang.ada")
