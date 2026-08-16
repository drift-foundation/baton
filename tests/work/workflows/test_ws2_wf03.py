"""WS2-WF-03 — due review, silence, extension, and withdrawal
(WORKFLOW-TESTS.md WS-2 battery).

Due-ness is derived, deterministic, idempotent across restart, and decides
nothing: reaching T changes no state, extension is an audited act that
advances the deadline generation while keeping every report and pending
assignment, and silence may inform the reviewer's close — at `1/3` or even
`0/N` — but can never impersonate a report.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import document                                 # noqa: E402
from ws2cast import verification_teams                        # noqa: E402

T0 = "2026-08-15T10:00:00Z"
T1 = "2026-08-15T12:00:00Z"
T2 = "2026-08-15T18:00:00Z"


def _provider(flow):
	return flow.ok("create", "team=lang", "kind=rsrch",
	               "title=parser recovery",
	               "origin=external-report", "classification=suspected-defect", "body=provider",
	               viewer="lang.ada")["work_id"]


def test_ws2_wf03_due_extension_withdrawal(flow):
	flow.now = T0
	flow.init(document(verification_teams()))

	# 1. A three-route round with review_at=T1: 0/3, zero withdrawn, not
	# due before T.
	lang42 = _provider(flow)
	created = flow.ok("round", f"work={lang42}", "candidate=driftc-A",
	                  "assign=push.verify", "assign=web.verify",
	                  "assign=mdb.verify", f"review-at={T1}",
	                  viewer="lang.ada")
	staged = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert (staged["progress"], staged["withdrawn"], staged["due"]) == \
		("0/3", 0, False)
	assert flow.ok("summary", viewer="lang.ada")["due"] == 0
	# The read-only wait times out quietly before the deadline...
	# (W136: the wait is participant-relative — grace resolves nothing,
	# so ada's routed-Work wake does not mask the deadline mechanics.)
	early = flow.ok("wait", "timeout=0.15", viewer="lang.grace")
	assert early == {"actionable": [], "timed_out": True}

	# 2. At T, the round is due for exactly the responsible provider
	# endpoint — and NOTHING transitioned.
	flow.now = T1
	staged = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert staged["due"] is True
	assert staged["deadline_generation"] == 1
	assert flow.ok("summary", viewer="lang.ada")["due"] == 1
	assert flow.ok("summary", viewer="push.sl")["due"] == 0
	# ...and returns the due round's LOCATOR the moment it is actionable.
	woken = flow.ok("wait", "timeout=0.15", viewer="lang.ada")
	assert woken["timed_out"] is False
	located = next(entry for entry in woken["actionable"]
	               if entry.get("flavor") == "due_round")
	assert (located["work"], located["round"],
	        located["candidate"]) == (lang42, 1, "driftc-A")
	checkpoint = flow.ok("detail", f"work={lang42}", viewer="lang.ada")
	assert checkpoint["status"] == "open" and \
		checkpoint["phase"] == "queued"
	assert len(flow.ok("obligations", viewer="push.sl")) == 1

	# 3. Restart and reread after T (every CLI act IS a fresh process):
	# still due, same generation, no duplicate notification, no automatic
	# decision.
	again = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert again["due"] is True and again["deadline_generation"] == 1
	events = flow.ok("events", viewer="lang.ada")
	assert all(event["kind"] not in ("due", "notify")
	           for event in events), "a timer wrote an audit row"

	# 4. The reviewer extends the SAME candidate to T2: an audit act; due
	# clears; reports and pending assignments are retained.
	flow.ok("report", f"obligation={created["assignments"][0]}",
	        "observation=passed", "evidence=clean",
	        viewer="push.sl")
	flow.ok("extend", f"work={lang42}", "round=1", f"review-at={T2}",
	        viewer="lang.ada")
	staged = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert staged["due"] is False
	assert staged["deadline_generation"] == 2
	assert staged["progress"] == "1/3" and staged["pending"] == 2
	assert flow.ok("summary", viewer="lang.ada")["due"] == 0
	extension = next(event for event in
	                 flow.ok("events", viewer="lang.ada")
	                 if event["kind"] == "extend_round")
	assert (extension["payload"]["from_review_at"],
	        extension["payload"]["to_review_at"]) == (T1, T2)

	# 5-6. The reviewer closes satisfying BEFORE T2 on the received report
	# plus elapsed exposure: final progress 1/3, both pending assignments
	# withdrawn and their routes notified, neither presented as feedback.
	flow.ok("close", f"work={lang42}",
	        "rationale=one clean report and broad exposure since T0",
	        "outcome=satisfying", viewer="lang.ada")
	final = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert final["progress"] == "1/3"
	assert final["withdrawn"] == 2 and final["pending"] == 0
	withdrawals = [event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "withdraw"]
	assert sorted(event["payload"]["endpoint"]
	              for event in withdrawals) == \
		["mdb.verify", "web.verify"]
	summary = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")["payload"][
	               "round_summary"]
	assert summary["progress"] == "1/3"
	assert summary["observations"] == {"passed": 1, "failed": 0,
	                                   "unable": 0}
	assert sorted(summary["withdrawn_pending"]) == \
		["mdb.verify", "web.verify"]
	assert (summary["created_ts"], summary["closed_ts"]) == (T0, T1)


def test_ws2_wf03_the_zero_report_close_branch(flow):
	"""7. Silence may inform a human decision but can never impersonate a
	report: a 0/3 close records zero observations, the full exposure
	window, and three visible withdrawals."""
	flow.now = T0
	flow.init(document(verification_teams()))
	lang42 = _provider(flow)
	flow.ok("round", f"work={lang42}", "candidate=driftc-A",
	        "assign=push.verify", "assign=web.verify",
	        "assign=mdb.verify", f"review-at={T1}",
	        viewer="lang.ada")
	flow.now = T2
	flow.ok("close", f"work={lang42}",
	        "rationale=long exposure, zero negative reports anywhere",
	        "outcome=satisfying", viewer="lang.ada")
	summary = next(event for event in
	               flow.ok("events", viewer="lang.ada")
	               if event["kind"] == "close_work")["payload"][
	               "round_summary"]
	assert summary["progress"] == "0/3"
	assert summary["observations"] == {"passed": 0, "failed": 0,
	                                   "unable": 0}
	assert len(summary["withdrawn_pending"]) == 3
	assert (summary["created_ts"], summary["closed_ts"]) == (T0, T2)
	final = flow.ok("detail", f"work={lang42}", viewer="lang.ada")["rounds"][0]
	assert final["progress"] == "0/3" and final["withdrawn"] == 3
