"""WS2-WF-02 — three mixed reports and reviewer adjudication
(WORKFLOW-TESTS.md WS-2 battery).

Receipt is not support: `2/3` can mean one confirmation, one rejected
failure, and one pending — the projection shows both axes so nobody
mistakes the fraction for votes, and no count, observation, or assessment
ever chooses the reviewer's branch automatically.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_dense_audit, document             # noqa: E402
from ws2cast import verification_teams                        # noqa: E402


def test_ws2_wf02_mixed_reports_and_adjudication(flow):
	flow.init(document(verification_teams()))

	# 1. Round 1 selects exact routes in Push, Web, and MariaDB: three
	# independent assignments, 0/3.
	lang42 = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                 "--title", "parser recovery", "--origin",
	                 "external-report", "--body", "provider",
	                 viewer="lang.ada")["work_id"]
	created = flow.ok("round", lang42, "--candidate", "driftc-A",
	                  "--assign", "push.verify", "--assign", "web.verify",
	                  "--assign", "mdb.verify", viewer="lang.ada")
	push_a, web_a, mdb_a = [str(seq) for seq in created["assignments"]]
	assert flow.ok("detail", lang42,
	               viewer="lang.ada")["rounds"][0]["progress"] == "0/3"

	# 2. Push reports passed; Lang accepts. 1/3.
	flow.ok("report", push_a, "--observation", "passed",
	        "--evidence", "staging clean", viewer="push.sl")
	flow.ok("assess", push_a, "--as", "accepted",
	        "--rationale", "clean run", viewer="lang.ada")
	assert flow.ok("detail", lang42,
	               viewer="lang.ada")["rounds"][0]["progress"] == "1/3"

	# 3. Web reports failed; Lang REJECTS the report as a consumer
	# configuration error. The projection says failed/rejected with both
	# rationales — and reads 2/3, never two approvals.
	flow.ok("report", web_a, "--observation", "failed",
	        "--evidence", "render farm crash", viewer="web.wren")
	flow.ok("assess", web_a, "--as", "rejected",
	        "--rationale", "web's farm runs an unsupported libc",
	        viewer="lang.ada")
	staged = flow.ok("detail", lang42, viewer="lang.ada")["rounds"][0]
	assert staged["progress"] == "2/3"
	web_entry = next(entry for entry in staged["assignments"]
	                 if entry["endpoint"] == "web.verify")
	assert web_entry["observation"] == "failed"
	assert web_entry["effective_assessment"]["assessment"] == "rejected"
	assert web_entry["effective_assessment"]["rationale"] == \
		"web's farm runs an unsupported libc"

	# 4. MariaDB reports unable; Lang leaves it inconclusive. 3/3, all
	# three raw reports immutable.
	flow.ok("report", mdb_a, "--observation", "unable",
	        "--evidence", "no repro environment this week",
	        viewer="mdb.mo")
	flow.ok("assess", mdb_a, "--as", "inconclusive",
	        "--rationale", "no signal either way", viewer="lang.ada")
	staged = flow.ok("detail", lang42, viewer="lang.ada")["rounds"][0]
	assert staged["progress"] == "3/3"
	assert [entry["observation"] for entry in staged["assignments"]] == \
		["passed", "failed", "unable"]

	# 5. No count, observation, or assessment chose a branch: the work sat
	# untouched through all of it, and the reviewer may explicitly
	# continue work instead of closing.
	checkpoint = flow.ok("detail", lang42, viewer="lang.ada")
	assert checkpoint["status"] == "open"
	assert checkpoint["phase"] == "queued"
	flow.ok("phase", lang42, "--to", "active", viewer="lang.ada")

	# 6. Lang supersedes its Web assessment with a new accepted act; the
	# prior assessment and the raw failed report remain in history.
	flow.ok("assess", web_a, "--as", "accepted",
	        "--rationale", "reproduced on a supported libc after all",
	        viewer="lang.ada")
	staged = flow.ok("detail", lang42, viewer="lang.ada")["rounds"][0]
	web_entry = next(entry for entry in staged["assignments"]
	                 if entry["endpoint"] == "web.verify")
	assert web_entry["observation"] == "failed", \
		"supersession rewrote the raw report"
	assert web_entry["effective_assessment"]["assessment"] == "accepted"
	assert [act["assessment"] for act in web_entry["assessments"]] == \
		["rejected", "accepted"]
	supersession = [event for event in
	                flow.ok("events", viewer="lang.ada")
	                if event["kind"] == "assess"][-1]
	assert supersession["payload"]["supersedes"] is not None

	assert_dense_audit(flow, "lang.ada")
