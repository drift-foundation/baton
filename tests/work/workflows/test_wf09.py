"""WF-09 — restart and concurrent completion safety (WORKFLOW-TESTS.md).

A shortened WF-04 where every act is already a fresh process, with two truly
concurrent race checkpoints:

- respond and dispose race on ONE obligation (same authorized handler, two
  sessions) — exactly one commits, the loser gets a structured refusal;
- pass races terminal close — under the WS-1 ownership rule EXACTLY ONE
  commits in either serialization: close first leaves the pass refusing on
  the closed work; pass first moves Current, so the racing close by the
  former handler refuses on ownership (authority followed the baton
  mid-race) and the NEW handler closes deliberately afterwards.

Around every refusal: no partial rows, no sequence hole. The final
checkpoint reconstructs everything from `--config` alone.

Omitted (WORKFLOW-COVERAGE.md, WS-5): client operation ids and
effectively-once retry — claimed by the plan, not exposed by the CLI, and
needing their own ruling first.

Defect found by this workflow (workflow-to-regression rule): race 1 exposed
respond AND dispose both committing against one obligation — every
terminal-competition check ran only before the write lock. Extracted
regressions: the four `test_wf09_*` tests in `test_transitions.py`; fix:
in-lock rechecks across create/post/close/block/respond/dispose, with
the close event's `was_current` recorded from the row at commit.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_dense_audit, document, standard_teams  # noqa: E402


def _outcomes(flow, procs):
	finished = [flow.finish(proc) for proc in procs]
	winners = [out for code, out, _err in finished if code == 0]
	losers = [err for code, _out, err in finished if code != 0]
	return winners, losers


def test_wf09_restart_and_races(flow):
	flow.init(document(standard_teams()))

	push1 = flow.ok("create", "team=push", "kind=bug",
	                "title=checkout fails",
	                "origin=external-report", "classification=suspected-defect", "body=500 at checkout",
	                viewer="push.sl")["work_id"]
	asked = flow.post(push1, "body=lang: yours?",
	                "request=lang.bug", viewer="push.sl")
	lang42 = flow.ok("create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect", "body=accepted",
	                 viewer="lang.ada")["work_id"]
	flow.ok("block", f"work={push1}", f"on={lang42}", viewer="push.sl")

	# RACE 1: respond and dispose compete for the ONE pending obligation.
	seq = str(asked["seq"])
	procs = [flow.spawn("respond", f"obligation={seq}", "body=ours; tracked",
	                    viewer="lang.ada"),
	         flow.spawn("dispose", f"obligation={seq}",
	                    "disposition=not ours after all", viewer="lang.ada")]
	winners, losers = _outcomes(flow, procs)
	assert len(winners) == 1, "both terminal obligation actions committed"
	assert len(losers) == 1
	assert "already" in json.loads(losers[0])["error"], \
		"the loser did not receive a structured refusal"
	assert flow.ok("obligations", viewer="lang.ada") == []
	events = assert_dense_audit(flow, "lang.ada")
	terminal = [event for event in events
	            if event["kind"] in ("respond", "dispose")]
	assert len(terminal) == 1, "the losing action still left rows"

	# RACE 2: a pass and a terminal close compete for LANG-42.
	lang_thread = flow.born(lang42, "lang.ada")
	procs = [flow.spawn("say", f"thread={lang_thread}", "body=handing to build",
	                    f"on={lang42}",
	                    "pass-to=lang.impl", "phase=active", viewer="lang.ada"),
	         flow.spawn("close", f"work={lang42}",
	                    "rationale=fixed and verified", "outcome=satisfying", viewer="lang.ada")]
	winners, losers = _outcomes(flow, procs)
	events = assert_dense_audit(flow, "lang.ada")
	race_kinds = [event["kind"] for event in events
	              if event["kind"] in ("pass", "close_work")]
	assert len(winners) == 1 and len(losers) == 1, \
		"the ownership rule admits exactly one racing terminal action"
	assert json.loads(losers[0])["error"], \
		"the loser did not receive a structured refusal"
	if race_kinds == ["pass"]:
		# The pass serialized first: Current moved, the racing close lost
		# on OWNERSHIP, and closure is now the new handler's deliberate
		# act — authority followed the baton even mid-race.
		flow.ok("close", f"work={lang42}", "rationale=fixed and verified", "outcome=satisfying",
		        viewer="lang.grace")
	else:
		assert race_kinds == ["close_work"], \
			"a merged or duplicated race state committed"
	closed = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	assert closed["status"] == "closed"
	assert closed["current"] is None and closed["next"] is None

	# The consumer resumed either way — its blocker closed.
	assert flow.ok("detail", f"work={push1}", viewer="push.sl")["ready"] is True
	flow.ok("close", f"work={push1}", "rationale=verified upstream", "outcome=satisfying",
	        viewer="push.sl")

	# RESTART RECONSTRUCTION: a fresh process rebuilds every projection
	# from --config alone; process memory contributed nothing.
	events = assert_dense_audit(flow, "push.sl")
	for work, viewer in ((push1, "push.sl"), (lang42, "lang.ada")):
		rebuilt = flow.ok("detail", f"work={work}", viewer=viewer)
		assert rebuilt["status"] == "closed"
		assert rebuilt["current"] is None and rebuilt["next"] is None
	assert flow.ok("obligations", viewer="lang.ada") == []
	assert flow.ok("home", viewer="push.sl")["rows"][0]["status"] == "closed"
	born = flow.ok("work-threads", f"work={push1}",
	               viewer="push.sl")["rows"][0]["id"]
	trail = flow.ok("thread", f"thread={born}", viewer="push.sl")["messages"]
	assert [msg["seq"] for msg in trail] == \
		sorted(msg["seq"] for msg in trail)
