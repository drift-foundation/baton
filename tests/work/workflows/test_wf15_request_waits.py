"""WF-15 — a directed request blocks by default, through the PUBLIC CLI.

W159's focused tests exercise the transition API. This proves the same
contract through the JSON CLI in both the source and packaged lanes,
because the defect it removes is one an operator hits: asking another
endpoint for input you cannot proceed without, while your own Work goes
on advertising itself as active and claimed.

The retired shape was two commands — publish, then suspend — with a
window between them where an interruption left the workflow lying.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, team  # noqa: E402


def _teams() -> dict:
	return {
		"push": team(
			"Pushcoin",
			{"sl": {"display": "Slawomir", "roles": ["impl"],
			        "capabilities": ["config"]}},
			{"impl": {"display": "Implementation"}},
			{"main": {"role": "impl", "handlers": ["sl"]}},
			{"bug": {"display": "Bug", "route": "main"}}),
		"drift": team(
			"Drift",
			{"ada": {"display": "Ada", "roles": ["impl"]}},
			{"impl": {"display": "Implementation"}},
			{"main": {"role": "impl", "handlers": ["ada"]}},
			{"bug": {"display": "Bug", "route": "main"}}),
	}


def test_wf15_a_directed_request_waits_by_default(flow):
	flow.init(document(_teams()))

	# 1. A claimed consumer asks another endpoint for input.
	born = flow.ok("create", "team=push", "kind=bug",
	               "title=checkout fails", "origin=external-report",
	               "classification=suspected-defect",
	               "body=500 at checkout", viewer="push.sl")
	work, thread = born["work_id"], born["thread"]
	flow.ok("claim", f"work={work}", viewer="push.sl")
	before = flow.ok("detail", f"work={work}", viewer="push.sl")
	assert before["current"] == {"team": "push", "member": "sl",
	                   "participant": "push.sl"}
	last_before = before["snapshot_seq"] if "snapshot_seq" in before \
		else max(e["seq"] for e in flow.ok("events", viewer="push.sl"))

	# 2. ONE act, with wait= omitted — the ruled default.
	asked = flow.ok("say", f"thread={thread}", "body=drift: is this yours?",
	                "request=drift.bug", f"on={work}", viewer="push.sl")
	# W159 R5: the immediate JSON result says WHICH form committed, so
	# an operator never has to read Events back to find out.
	assert asked["wait"] is True, asked

	# 3. It published, created the obligation, entered the exact wait and
	#    released the claim — in ONE sequence, without moving Current.
	assert asked["seq"] == last_before + 1, \
		f"the blocking request consumed more than one sequence: " \
		f"{last_before} -> {asked['seq']}"
	after = flow.ok("detail", f"work={work}", viewer="push.sl")
	assert after["phase"] == "waiting"
	assert after["waiting_on"] == {"type": "obligation",
	                               "obligation": asked["seq"]}
	assert after["current"] is None, "the blocking ask kept the claim"
	assert after["route"]["endpoint"] == before["route"]["endpoint"], \
		"asking for input transferred ownership"
	assert after["ready"] is False or after["phase"] == "waiting"

	# 4. The obligation is real and actionable for the asked endpoint.
	owed = flow.ok("obligations", viewer="drift.ada")
	assert [entry["seq"] for entry in owed] == [asked["seq"]]
	assert owed[0]["completes_by"] == ["respond", "dispose", "accept"]

	# 5. The Events journal carries the effective choice and the
	#    released claimant — facts, not glyphs.
	events = flow.ok("work-events", f"work={work}", "newest=true",
	                 viewer="push.sl")["events"]
	entry = next(e for e in events if e["seq"] == asked["seq"])
	assert entry["kind"] == "request"
	assert entry["payload"]["wait"] is True
	assert entry["payload"]["released_claimant"] == "push.sl"

	# 6. Answering wakes the exact waiter, once.
	flow.ok("respond", f"obligation={asked['seq']}",
	        "body=ours; picking it up", viewer="drift.ada")
	woken = flow.ok("detail", f"work={work}", viewer="push.sl")
	assert woken["phase"] == "queued", "the exact waiter slept on"
	assert woken["waiting_on"] is None
	wakes = [e for e in flow.ok("events", viewer="push.sl")
	         if e["kind"] == "wake"
	         and e["payload"]["work"] == work]
	assert len(wakes) == 1, f"the waiter woke {len(wakes)} times"
	assert_final_invariants(flow, "push.sl", [work])


def test_wf15_wait_false_is_the_asynchronous_contrast(flow):
	"""The deliberate override: still one obligation, but the consumer
	keeps its claim and its stage and carries on."""
	flow.init(document(_teams()))
	born = flow.ok("create", "team=push", "kind=bug",
	               "title=needs input but not blocked",
	               "origin=external-report",
	               "classification=suspected-defect",
	               "body=continuing meanwhile", viewer="push.sl")
	work, thread = born["work_id"], born["thread"]
	flow.ok("claim", f"work={work}", viewer="push.sl")
	before = flow.ok("detail", f"work={work}", viewer="push.sl")

	asked = flow.ok("say", f"thread={thread}", "body=drift: when you can",
	                "request=drift.bug", f"on={work}", "wait=false",
	                viewer="push.sl")
	assert asked["wait"] is False, asked
	# a plain message alongside it invents no choice
	plain = flow.ok("say", f"thread={thread}", "body=for context",
	                viewer="push.sl")
	assert "wait" not in plain, plain

	after = flow.ok("detail", f"work={work}", viewer="push.sl")
	assert after["phase"] == before["phase"], "wait=false changed the stage"
	assert after["current"] == before["current"], "wait=false released the claim"
	assert after["waiting_on"] is None
	assert [entry["seq"] for entry in flow.ok("obligations",
	                                          viewer="drift.ada")] == \
		[asked["seq"]], "the asynchronous form created no obligation"
	events = flow.ok("work-events", f"work={work}", "newest=true",
	                 viewer="push.sl")["events"]
	entry = next(e for e in events if e["seq"] == asked["seq"])
	assert entry["payload"]["wait"] is False
	assert_final_invariants(flow, "push.sl", [work])


def test_wf15_the_blocking_form_refuses_what_it_cannot_suspend(flow):
	"""Public refusals, changing nothing: an unclaimed Work has no
	execution to suspend, and `wait=` is meaningless without a request."""
	flow.init(document(_teams()))
	born = flow.ok("create", "team=push", "kind=bug", "title=unclaimed",
	               "origin=external-report",
	               "classification=suspected-defect", "body=b",
	               viewer="push.sl")
	work, thread = born["work_id"], born["thread"]

	error = flow.refuse("say", f"thread={thread}", "body=drift: yours?",
	                    "request=drift.bug", f"on={work}",
	                    viewer="push.sl")
	assert "unclaimed" in error, error
	assert flow.ok("detail", f"work={work}",
	               viewer="push.sl")["phase"] != "waiting"

	error = flow.refuse("say", f"thread={thread}", "body=plain",
	                    "wait=true", viewer="push.sl")
	assert "requires request=" in error or \
		"carries no request" in error, error

	error = flow.refuse("say", f"thread={thread}", "body=x",
	                    "request=drift.bug", f"on={work}", "wait=maybe",
	                    viewer="push.sl")
	assert "true, false" in error or "true or false" in error, error
	assert_final_invariants(flow, "push.sl", [work])
