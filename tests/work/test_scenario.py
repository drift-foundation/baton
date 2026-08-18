"""A7: the gate scenario, end to end, through `baton-work` AS A SUBPROCESS.

Every step is a real process invocation of the CLI module — the same entry
the installed artifact will expose — not an in-process call. The final
assertion is the ordered audit trail by sequence number, which is what makes
this a scenario rather than eight independent tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src")


def _run(path, *argv, viewer=None, expect_ok=True):
	command = [sys.executable, "-m", "baton_work.cli",
	           "--config", path]
	if viewer:
		command += ["--participant", viewer]
	command += list(argv)
	proc = subprocess.run(command, capture_output=True, text=True,
	                      timeout=120,
	                      env={**os.environ, "PYTHONPATH": SRC})
	if expect_ok:
		assert proc.returncode == 0, proc.stderr or proc.stdout
		return json.loads(proc.stdout)
	assert proc.returncode == 1, proc.stdout
	return json.loads(proc.stderr)


def test_the_gate_scenario_end_to_end(tmp_path):
	import fixtures as fx
	path, _db = fx.build_instance(str(tmp_path))

	# 1. web creates WEB-1 with its first message, atomically.
	born = _run(path, "create", "team=web", "kind=bug",
	            "title=render crash", "origin=external-report", "classification=suspected-defect",
	            "body=tab dies on load",
	            viewer="web.wren")["result"]
	web1, thread = born["work_id"], born["thread"]

	# 2. include +lang.rsrch — attention, no obligation.
	_run(path, "say", f"thread={thread}", "body=lang may want to see this",
	     "include=lang.rsrch", viewer="web.wren")
	assert _run(path, "obligations", viewer="lang.ada")["result"] == []

	# 3. request @lang.rsrch — one obligation; WEB-1's Current unchanged.
	# The single labelled work is the eligible target; --on may be omitted.
	requested = _run(path, "say", f"thread={thread}",
	                 "body=is this your parser bug?",
	                 "request=lang.rsrch", "wait=false", viewer="web.wren")["result"]
	pending = _run(path, "obligations", viewer="lang.ada")["result"]
	assert [entry["seq"] for entry in pending] == [requested["seq"]]
	assert _run(path, "detail", f"work={web1}",
	            viewer="web.wren")["result"]["route"]["endpoint"] == \
		"web.bug"

	# 4. lang creates LANG-42, relates WEB-1 blocked_by LANG-42, responds.
	lang_born = _run(path, "create", "team=lang", "kind=rsrch",
	                 "title=parser recovery",
	                 "origin=external-report", "classification=suspected-defect",
	                 "body=deduplicating consumer reports",
	                 viewer="lang.ada")["result"]
	lang42, lang_thread = lang_born["work_id"], lang_born["thread"]
	_run(path, "block", f"work={web1}", f"on={lang42}",
	     "rationale=compiler fix required", viewer="web.wren")
	assert _run(path, "detail", f"work={web1}",
	            viewer="web.wren")["result"]["ready"] is False
	_run(path, "respond", f"obligation={requested["seq"]}",
	     "body=yes - tracked as our parser recovery work",
	     viewer="lang.ada")
	assert _run(path, "obligations", viewer="lang.ada")["result"] == []

	# 5. pass with planned Next, then the consuming return.
	passed = _run(path, "pass", f"work={lang42}", "to=lang.impl",
	              "set-next=lang.rev",
	              "comment=confirmed, implement",
	              viewer="lang.ada")["result"]
	assert passed["kind"] == "pass"
	detail = _run(path, "detail", f"work={lang42}", viewer="lang.ada")["result"]
	assert detail["route"]["endpoint"] == "lang.impl"
	assert detail["next"]["endpoint"] == "lang.rev"
	returned = _run(path, "pass", f"work={lang42}", "to=lang.rev",
	                "comment=implementation complete",
	                viewer="lang.ada")["result"]
	assert returned["kind"] == "return"
	detail = _run(path, "detail", f"work={lang42}", viewer="lang.ada")["result"]
	assert detail["route"]["endpoint"] == "lang.rev"
	assert detail["next"] is None

	# 6. terminal close unblocks WEB-1, level-triggered.
	_run(path, "close", f"work={lang42}", "rationale=fixed and verified", "outcome=satisfying",
	     viewer="lang.ada")
	after = _run(path, "detail", f"work={web1}", viewer="web.wren")["result"]
	assert after["ready"] is True, "the dependent did not unblock"
	assert after["open_blockers"] == 0

	# The ordered audit trail: every step, one event, dense sequence.
	events = _run(path, "events", viewer="lang.ada")["result"]
	kinds = [event["kind"] for event in events]
	# W38 R1: the gated dependent now sits in `waiting`, so closing the
	# last blocker emits the wake that makes it actionable again.
	assert kinds[-7:] == ["create_work", "add_dependency", "respond",
	                      "pass", "return", "close_work", "wake"]
	seqs = [event["seq"] for event in events]
	assert seqs == list(range(1, len(seqs) + 1)), "the trail has a hole"
	# ...and the return step is the one that consumed the planned Next.
	consuming = [event for event in events if event["kind"] == "return"]
	assert len(consuming) == 1
	assert consuming[0]["payload"]["consumed_next"] is True


def test_the_scenario_refuses_out_of_order_acts(tmp_path):
	"""The same commands out of order refuse rather than half-apply: a close
	over an open CHILD (the ruled refusal), and a respond by the wrong team.

	Deliberately NOT tested as a refusal: closing over an open BLOCKER. The
	rulings refuse closure only over open required descendants; a consumer
	may honestly close (reject, duplicate, defer) while its provider
	dependency is open — the disposition is where that honesty lives. The
	first version of this test invented the stricter rule and the code
	correctly refused to have it."""
	import fixtures as fx
	path, _db = fx.build_instance(str(tmp_path))
	born = _run(path, "create", "team=web", "kind=bug",
	            "title=crash", "origin=external-report", "classification=suspected-defect",
	            "body=b", viewer="web.wren")["result"]
	web1, thread = born["work_id"], born["thread"]
	child = _run(path, "create", "team=web", "kind=bug",
	             "title=narrow the repro", "origin=decomposition", "classification=suspected-defect",
	             "body=b", f"parent={web1}",
	             viewer="web.wren")["result"]["work_id"]

	error = _run(path, "close", f"work={web1}", "rationale=premature", "outcome=satisfying",
	             viewer="web.wren", expect_ok=False)
	assert child in error["error"], "the refusal does not name the open child"

	requested = _run(path, "say", f"thread={thread}", "body=your bug?",
	                 "request=lang.bug", "wait=false", viewer="web.wren")["result"]
	error = _run(path, "respond", f"obligation={requested["seq"]}", "body=not mine",
	             viewer="web.wren", expect_ok=False)
	assert "cannot discharge" in error["error"]
