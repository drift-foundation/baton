"""WS3-WF-01 — PushCoin→Drift: the first external report, accepted
atomically (WS3-DESIGN.md D4).

One commit: the provider Work exists (established AT the acceptance, R48),
the consumer is gated with provenance, the obligation reads accepted→id,
and the rationale answers into the consumer's thread. The waiting
consumer wakes on its named obligation while the new gate holds readiness
false (R47).
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
			{"sl": {"display": "Slawomir", "roles": ["dev"],
			        "capabilities": ["config"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["sl"]}},
			{"bug": {"display": "Bug", "route": "main"}}),
		"drift": team(
			"Drift",
			{"ada": {"display": "Ada", "roles": ["dev"]},
			 "grace": {"display": "Grace", "roles": ["dev"]}},
			{"dev": {"display": "Developer"}},
			{"main": {"role": "dev", "handlers": ["ada"]}},
			{"bug": {"display": "Bug", "route": "main"},
			 "rsrch": {"display": "Research", "route": "main"}}),
	}


def test_ws3_wf01_first_report_accepted_atomically(flow):
	flow.init(document(_teams()))

	# Push reports and asks Drift, then waits on exactly that question.
	born = flow.ok("create", "team=push", "kind=bug",
	               "title=checkout fails",
	               "origin=external-report", "classification=suspected-defect", "body=500 at checkout",
	               viewer="push.sl")
	push1, thread_id = born["work_id"], born["thread"]
	# W159: ONE act. The claim is what the blocking form suspends, and
	# the request itself enters the exact-obligation wait and releases
	# it — the retired two-command `say` then `phase to=waiting` is
	# exactly the race this Work removed.
	flow.ok("claim", f"work={push1}", viewer="push.sl")
	asked = flow.post(push1, "body=drift: yours?",
	                "request=drift.bug", viewer="push.sl")
	waiting = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert waiting["phase"] == "waiting", waiting["phase"]
	assert waiting["waiting_on"] == {"type": "obligation",
	                                 "obligation": asked["seq"]}
	assert waiting["current"] is None, "the blocking ask kept the claim"
	assert waiting["route"]["endpoint"] == "push.bug", \
		"asking for input moved Current"

	# The actionable entry DECLARES acceptance to the owed route.
	actionable = flow.ok("obligations", viewer="drift.ada")
	assert actionable[0]["completes_by"] == ["respond", "dispose", "accept"]

	# A non-handler holds no grant; the refusal changes nothing.
	error = flow.refuse("accept", f"obligation={asked["seq"]}", "body=not mine",
	                    "create=true", "kind=rsrch", "classification=suspected-defect", "title=x",
	                    viewer="drift.grace")
	assert "ownership" in error

	# THE atomic acceptance.
	result = flow.ok("accept", f"obligation={asked["seq"]}",
	                 "body=ours; tracking as a parser regression",
	                 "create=true", "kind=rsrch",
	                 "classification=suspected-defect",
	                 "title=parser recovery", viewer="drift.ada")
	drift1 = result["provider"]
	assert result["created"] is True
	assert result["edge"] == {
		"work": push1,
		"blocker": drift1,
		"via_obligation": asked["seq"],
	}

	# The consumer: woken on its named obligation, gated by the new edge,
	# provenance visible, rationale in its thread.
	consumer = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert consumer["phase"] == "queued", "the obligation waiter slept on"
	assert consumer["ready"] is False, "the new gate did not hold"
	assert consumer["links"]["blocked_by"][0]["id"] == drift1
	assert consumer["links"]["blocked_by"][0]["via_obligation"] == \
		asked["seq"]
	accepted = next(entry for entry in consumer["obligations"]
	                if entry["seq"] == asked["seq"])
	assert accepted["status"] == "accepted"
	assert accepted["accepted_into"] == drift1
	tail = flow.ok("thread", f"thread={thread_id}",
	               viewer="push.sl")["messages"][-1]
	assert tail["body"].startswith("ours; tracking")
	assert flow.ok("obligations", viewer="drift.ada") == []

	# The provider: born at the acceptance, noise-scoped to drift's home.
	provider = flow.ok("detail", f"work={drift1}", viewer="drift.ada")
	assert provider["open_dependents"] == 1
	assert provider["origin"] == "external-report"
	assert [row["id"] for row in
	        flow.ok("home", viewer="drift.ada")["rows"]] == [drift1]
	assert flow.ok("home", viewer="push.sl")["rows"][0]["id"] == push1, \
		"the provider record leaked into the consumer's default table"

	# Terminal fanout: closing DRIFT-1 ends the gate and wakes push.
	flow.ok("close", f"work={drift1}", "rationale=fixed and verified",
	        "outcome=satisfying", viewer="drift.ada")
	resumed = flow.ok("detail", f"work={push1}", viewer="push.sl")
	assert resumed["ready"] is True
	assert resumed["links"]["blocked_by"][0]["outcome"] == "satisfying"
	flow.ok("close", f"work={push1}", "rationale=verified upstream",
	        "outcome=satisfying", viewer="push.sl")
	assert_final_invariants(flow, "drift.ada", [push1, drift1])
