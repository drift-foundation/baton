"""WF-13 — portable dossier authority across PushCoin and Drift
(WORKFLOW-TESTS.md, WS-6 Slice A).

Strict config declares roots without host paths; a Work may be born
bound; only Current attaches or corrects a binding under CAS; ordered
typed references ride the acts, pin the committed binding revision, and
survive root retirement by revision; canonical reads never need a
resolver or a filesystem; closure freezes binding history without
moving anything.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document)
from ws2cast import verification_teams                        # noqa: E402

ROOTS = {"pushcoin": {"display": "PushCoin monorepo"},
         "drift": {"display": "Drift checkout"},
         "baton": {"display": "Baton repository"}}


def test_wf13_portable_dossier_authority(flow):
	flow.init(document(verification_teams(), roots=dict(ROOTS)))

	# 1. PUSH-1 is BORN bound: work, first message, and binding
	# revision 1 in one transaction.
	push_born = flow.ok(
		"create", "--team", "push", "--kind", "bug",
		"--title", "checkout fails", "--origin", "external-report", "--classification", "suspected-defect",
		"--body", "500 at checkout",
		"--binding", "pushcoin:work/records/2026/08/finding-push-1",
		viewer="push.sl")
	push1, push_thread = push_born["work_id"], push_born["thread"]
	detail = flow.ok("detail", push1, viewer="push.sl")
	assert detail["binding"]["revision"] == 1
	assert detail["binding"]["root"] == "pushcoin"
	assert detail["binding"]["path"] == \
		"work/records/2026/08/finding-push-1"

	# 2. LANG-42 is created unbound; requester and former handler cannot
	# attach; Current attaches revision 1 with expected prior 0.
	lang_born = flow.ok("create", "--team", "lang", "--kind", "rsrch",
	                    "--title", "parser recovery", "--origin",
	                    "external-report", "--classification", "suspected-defect", "--body", "provider",
	                    viewer="lang.ada")
	lang42 = lang_born["work_id"]
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "bind", lang42, "--root", "drift", "--path",
		"work/records/2026/08/finding-lang-42", "--expect", "0",
		"--rationale", "requester cannot attach")
	assert "never grant" in error
	flow.ok("bind", lang42, "--root", "drift", "--path",
	        "work/records/2026/08/finding-lang-42", "--expect", "0",
	        "--rationale", "the handler attaches the record",
	        viewer="lang.ada")

	# 3. Push publishes a report with a PUSH-1 dossier-relative
	# reproduction and requests @lang.bug; Lang accepts into LANG-42
	# with explicit compound placement; Lang then posts a
	# LANG-42-relative proof plus an independent baton: reference —
	# citing LANG-42 in Push's thread needs NO label (M2).
	reported = flow.ok("--ref", f"{push1}:repro/checkout-500.sh",
	                   "say", push_thread, "--body",
	                   "repro attached; lang: yours?",
	                   "--request", "lang.rsrch", viewer="push.sl")
	assert [ref["kind"] for ref in
	        flow.ok("thread", push_thread,
	                viewer="push.sl")["messages"][-1]["references"]] == \
		["dossier"]
	accepted = flow.ok("--ref", "baton:docs/EFFECTIVE-BATON.md",
	                   "--answer-ref", f"{lang42}:proof/parser-state.md",
	                   "accept", str(reported["seq"]), "--body",
	                   "ours; tracked with the proof attached",
	                   "--into", lang42, viewer="lang.ada")
	events = flow.ok("events", viewer="lang.ada")
	accept_event = next(entry for entry in events
	                    if entry["seq"] == accepted["seq"])
	assert [ref["kind"] for ref in accept_event["references"]] == \
		["independent"]
	answer_event = next(entry for entry in events
	                    if entry["seq"] == accepted["seq"] + 1)
	assert [(ref["kind"], ref["work"], ref["binding_revision"])
	        for ref in answer_event["references"]] == \
		[("dossier", lang42, 1)], \
		"the answer placement was guessed or dropped"

	# 4. Correct LANG-42's locator under CAS: the old proof stays
	# anchored to revision 1; a new proof names revision 2; a raced
	# same-prior correction refuses; transfer moves the authority.
	flow.ok("bind", lang42, "--root", "drift", "--path",
	        "work/records/2026/08/finding-lang-42-parser",
	        "--expect", "1", "--rationale", "record renamed at triage",
	        viewer="lang.ada")
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "bind", lang42, "--root", "drift", "--path",
		"work/records/2026/08/finding-elsewhere", "--expect", "1",
		"--rationale", "stale prior")
	assert "is at revision" in error
	fresh_proof = flow.ok("--ref", f"{lang42}:proof/round-two.md",
	                      "say", push_thread, "--body",
	                      "updated proof under the corrected record",
	                      viewer="lang.ada")
	assert next(entry for entry in
	            flow.ok("events", viewer="lang.ada")
	            if entry["seq"] == fresh_proof["seq"])[
	            "references"][0]["binding_revision"] == 2
	assert answer_event["references"][0]["binding_revision"] == 1, \
		"the old proof was reinterpreted by the correction"
	flow.ok("say", flow.born(lang42, "lang.ada"), "--body",
	        "handing to push", "--on", lang42, "--pass-to", "push.bug", "--phase", "queued",
	        viewer="lang.ada")
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "bind", lang42, "--root", "drift", "--path",
		"work/records/2026/08/finding-after-transfer", "--expect", "2",
		"--rationale", "former handler")
	assert "never grant" in error

	# 5. Root retirement: drift leaves the catalog; independent drift
	# references refuse; the committed dossier citations stay; a new
	# binding revision needs a live root.
	config = document(verification_teams(), roots=dict(ROOTS),
	                  generation=2)
	del config["roots"]["drift"]
	flow.write_config(config)
	flow.ok("regen", viewer="lang.ada")
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "--ref", "drift:docs/late.md", "say",
		push_thread, "--body", "late evidence")
	assert "not a live configured root" in error
	still = flow.ok("--ref", f"{lang42}:proof/round-two.md", "say",
	                push_thread, "--body", "the citation still anchors",
	                viewer="push.sl")
	assert next(entry for entry in
	            flow.ok("events", viewer="push.sl")
	            if entry["seq"] == still["seq"])[
	            "references"][0]["root"] == "drift"
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "bind", lang42, "--root", "drift", "--path",
		"work/records/2026/08/finding-still-drift", "--expect", "2",
		"--rationale", "retired root")
	assert "not a live configured root" in error

	# 6. No resolver, no filesystem: every canonical read repeats with
	# portable locators only; the refusal matrix stays byte-pure.
	for argv in (("detail", lang42), ("bindings", lang42),
	             ("thread", push_thread), ("events",)):
		view = flow.ok(*argv, viewer="push.sl")
		assert view is not None
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "--ref", "pushcoin:x.md", "detail", lang42)
	assert "pure read" in error

	# 7. Close LANG-42 without Git provenance: PUSH-1 unblocks via its
	# edge; binding history freezes; a lightweight unbound work closes
	# with no placeholder binding.
	flow.ok("close", lang42, "--rationale",
	        "delivered under the corrected record", "--outcome",
	        "satisfying", viewer="push.sl")
	assert flow.ok("detail", push1, viewer="push.sl")["ready"] is True
	error = assert_refusal_changes_nothing(
		flow, "push.sl", "bind", lang42, "--root", "pushcoin",
		"--path", "work/records/2026/08/finding-postmortem",
		"--expect", "2", "--rationale", "post-terminal")
	assert "freezes its binding" in error
	light = flow.ok("create", "--team", "push", "--kind", "bug",
	                "--title", "lightweight", "--origin",
	                "self-initiated", "--classification", "suspected-defect", "--body", "no dossier",
	                viewer="push.sl")["work_id"]
	flow.ok("close", light, "--rationale", "quick fix, no record",
	        "--outcome", "satisfying", viewer="push.sl")
	assert flow.ok("detail", light,
	               viewer="push.sl")["binding"] is None

	# 8. WS-5 retries and races: a protected reference-bearing post
	# retries exactly; a spawned same-prior binding race admits one.
	prot = flow.ok("--op-id", "cite-1", "--ref",
	               f"{push1}:repro/checkout-500.sh", "say", push_thread,
	               "--body", "protected citation", viewer="push.sl")
	again = flow.ok("--op-id", "cite-1", "--ref",
	                f"{push1}:repro/checkout-500.sh", "say", push_thread,
	                "--body", "protected citation", viewer="push.sl")
	assert again["operation"]["state"] == "replayed"
	assert again["seq"] == prot["seq"]
	procs = [flow.spawn("bind", push1, "--root", "pushcoin", "--path",
	                    f"work/records/2026/08/finding-push-1-r{index}",
	                    "--expect", "1", "--rationale", "race",
	                    viewer="push.sl") for index in range(2)]
	finished = [flow.finish(proc) for proc in procs]
	winners = [out for code, out, _err in finished if code == 0]
	losers = [err for code, _out, err in finished if code != 0]
	assert len(winners) == 1 and len(losers) == 1
	assert json.loads(losers[0])["error"]
	assert flow.ok("detail", push1,
	               viewer="push.sl")["binding"]["revision"] == 2

	assert_dense_audit(flow, "lang.ada")
