"""WF-03 — provider rejects or requests more evidence (WORKFLOW-TESTS.md).

Route intake is not an automatic pipeline: a `@` request may end in an honest
rejection that creates NO provider work, NO dependency edge, and NO false
`fixed` — and the consumer decides its own ending independently.

Omitted (WORKFLOW-COVERAGE.md, WS-2): the exact disposition enums and the
effect of a non-satisfying provider outcome on a consumer dependency need a
ruling before the full branch matrix becomes executable. This gate covers the
executable spine; "request more evidence" is modeled as a contribution
message while the obligation stays pending.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import assert_final_invariants, document, standard_teams  # noqa: E402


def test_wf03_provider_rejects_honestly(flow):
	flow.init(document(standard_teams()))

	# 1. The consumer reports locally and asks Lang, retaining its Current.
	web1 = flow.ok("create", "--team", "web", "--kind", "bug",
	               "--title", "render crash on nested tables",
	               "--origin", "external-report",
	               "--body", "crashes with the attached DOM",
	               viewer="web.wren")["work_id"]
	requested = flow.ok("post", web1, "--body", "looks like a lang defect?",
	                    "--request", "lang.bug", viewer="web.wren")
	assert flow.ok("detail", web1,
	               viewer="web.wren")["current"]["endpoint"] == "web.bug"

	# 2. Lang requests more evidence — a contribution, not a resolution;
	# the obligation stays actionable the whole time.
	flow.ok("post", web1, "--body", "need the minimized repro, please",
	        viewer="lang.ada")
	pending = flow.ok("obligations", viewer="lang.ada")
	assert len(pending) == 1 and pending[0]["status"] == "pending"
	flow.ok("post", web1, "--body", "minimized repro attached",
	        viewer="web.wren")

	# 3. Lang explicitly REJECTS with an honest reason.
	flow.ok("dispose", str(requested["seq"]),
	        "--disposition", "not a lang defect: the DOM is malformed "
	        "before the parser sees it", viewer="lang.ada")
	assert flow.ok("obligations", viewer="lang.ada") == []

	# The rejection created NOTHING on the provider side.
	assert flow.ok("home", viewer="lang.ada")["rows"] == [], \
		"a rejection created provider work"
	links = flow.ok("links", web1, viewer="web.wren")
	assert links["blocked_by"] == [], "a rejection created a dependency edge"

	# The consumer decides independently — and its terminal state never
	# claims a fix that did not happen.
	flow.ok("close", web1, "--disposition",
	        "workaround shipped: sanitize the DOM before render",
	        viewer="web.wren")
	closed = flow.ok("detail", web1, viewer="web.wren")
	assert closed["status"] == "closed"

	events = assert_final_invariants(flow, "web.wren", [web1])
	dispositions = [event["payload"].get("disposition")
	                for event in events
	                if event["kind"] in ("dispose", "close_work")]
	assert len(dispositions) == 2, "the dispose or close left no audit"
	assert all("fixed" not in text for text in dispositions), \
		"a rejection path recorded a fix claim"
