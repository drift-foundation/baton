"""WF-12 — effectively-once mutation retry (WORKFLOW-TESTS.md, WS-5).

The client operation identity through the real CLI/JSON surface, source
and packaged alike: a lost response recovers its one committed result;
identical racing attempts yield one effect; conflicting reuse and
cross-participant independence behave per the ruling; refusals never
poison an id; committed operations replay across later state and config
generations; every mutation family participates; protected no-ops
consume their identity; init and regen are covered end to end.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wfdriver import (assert_dense_audit,                     # noqa: E402
                      assert_refusal_changes_nothing, document)
from ws2cast import verification_teams                        # noqa: E402


def test_wf12_effectively_once_retry(flow):
	flow.init(document(verification_teams()))

	born = flow.ok("create", "team=lang", "kind=rsrch",
	               "title=retry provider",
	               "origin=external-report", "classification=suspected-defect", "body=root",
	               viewer="lang.ada")
	work, thread = born["work_id"], born["thread"]
	assert born["operation"] is None, \
		"an unprotected call did not carry the null operation shape"

	# 1. Lost response, exact retry: one obligation, one event, the
	# replay carries the committed/replayed shapes and the original seq.
	first = flow.ok("say", "op-id=ask-1", f"thread={thread}",
	                "body=push: confirm", "request=push.bug", "wait=false",
	                viewer="lang.ada")
	assert first["operation"] == {"id": "ask-1", "state": "committed"}
	events_before = flow.ok("events", viewer="lang.ada")
	retry = flow.ok("say", "op-id=ask-1", f"thread={thread}",
	                "body=push: confirm", "request=push.bug", "wait=false",
	                viewer="lang.ada")
	assert retry["operation"] == {"id": "ask-1", "state": "replayed"}
	assert retry["seq"] == first["seq"]
	assert {key: value for key, value in retry.items()
	        if key != "operation"} == \
		{key: value for key, value in first.items()
		 if key != "operation"}
	assert flow.ok("events", viewer="lang.ada") == events_before, \
		"a replay consumed a sequence or wrote an event"
	pending = flow.ok("obligations", viewer="push.sl")
	assert [entry["seq"] for entry in pending] == [first["seq"]], \
		"the retry raised a second obligation"

	# 2. Same-id same-request race: exactly one effect; both exits
	# succeed; one committed, one replayed.
	procs = [flow.spawn("say", "op-id=race-1", f"thread={thread}",
	                    "body=raced once", viewer="lang.ada")
	         for _ in range(2)]
	finished = [flow.finish(proc) for proc in procs]
	assert all(code == 0 for code, _out, _err in finished), \
		"an identical racing attempt failed instead of replaying"
	results = [json.loads(out)["result"] for _code, out, _err in finished]
	states = sorted(entry["operation"]["state"] for entry in results)
	assert states == ["committed", "replayed"]
	assert results[0]["seq"] == results[1]["seq"]
	events = assert_dense_audit(flow, "lang.ada")
	assert len([event for event in events
	            if event["payload"].get("body_bytes") ==
	            len(b"raced once")]) == 1, "the race admitted two posts"

	# 3. Conflicting reuse refuses; the same id VALUE under another
	# participant is independent (per-participant scope).
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "say", "op-id=race-1", f"thread={thread}",
		"body=different meaning")
	assert "different request" in error
	independent = flow.ok("say", "op-id=race-1", f"thread={thread}",
	                      "body=push's own act", viewer="push.sl")
	assert independent["operation"]["state"] == "committed", \
		"one participant's id blocked another's"

	# 4. Refusal then correction under the SAME id: the refusal did not
	# consume the identity.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "close", "op-id=close-1", f"work={work}",
		"rationale=x", "outcome=done")
	assert "outcome= takes one of" in error
	# (corrected close comes later in step 6 under the same id)

	# 5. A pure read refuses an operation identity.
	error = assert_refusal_changes_nothing(
		flow, "lang.ada", "detail", "op-id=read-1", f"work={work}")
	assert "pure read" in error

	# 6. Later-state replay across config generations: pass the baton
	# with an id, reassign handlers by regen, close; the committed pass
	# STILL replays; a fresh identical request under a new id refuses.
	passed = flow.ok("pass", "op-id=pass-1", f"work={work}",
	                 "to=lang.impl", "comment=onward", viewer="lang.ada")
	config = document(verification_teams())
	config["generation"] = 2
	# the Work sits on lang.impl, whose route is `build` (W73 gave the
	# provider real per-stage routes so a handoff can derive its phase)
	config["teams"]["lang"]["routes"]["build"]["handlers"] = ["grace"]
	flow.write_config(config)
	regen = flow.ok("regen", "op-id=regen-1", viewer="lang.ada")
	assert regen["operation"]["state"] == "committed"
	regen_again = flow.ok("regen", "op-id=regen-1",
	                      viewer="lang.ada")
	assert regen_again["operation"]["state"] == "replayed", \
		"the protected regeneration did not replay"
	closed = flow.ok("close", "op-id=close-1", f"work={work}",
	                 "rationale=delivered", "outcome=satisfying",
	                 viewer="lang.grace")
	assert closed["operation"]["state"] == "committed"
	replayed_pass = flow.ok("pass", "op-id=pass-1", f"work={work}",
	                        "to=lang.impl", "comment=onward",
	                        viewer="lang.ada")
	assert replayed_pass["operation"]["state"] == "replayed"
	assert replayed_pass["seq"] == passed["seq"], \
		"the committed pass stopped replaying after regen and close"
	error = assert_refusal_changes_nothing(
		flow, "lang.grace", "pass", "op-id=pass-2", f"work={work}",
		"to=lang.impl", "comment=onward")
	assert "terminal work never moves" in error

	# 7. A protected successful no-op consumes its id without an event
	# and replays verbatim after the cursor advances.
	side = flow.ok("create", "team=push", "kind=bug",
	               "title=push local",
	               "origin=self-initiated", "classification=suspected-defect", "body=local",
	               viewer="push.sl")
	top = flow.ok("thread", f"thread={side["thread"]}",
	              viewer="push.sl")["last_seq"]
	flow.ok("mark-seen", f"thread={side["thread"]}", f"up-to={top}",
	        viewer="push.sl")
	events_before = flow.ok("events", viewer="push.sl")
	noop = flow.ok("mark-seen", "op-id=mark-1", f"thread={side["thread"]}",
	               f"up-to={top}", viewer="push.sl")
	assert noop["advanced"] is False
	assert noop["operation"] == {"id": "mark-1", "state": "committed"}
	assert flow.ok("events", viewer="push.sl") == events_before, \
		"a successful no-op invented a domain event"
	flow.ok("say", f"thread={side["thread"]}", "body=later",
	        viewer="push.sl")
	later = flow.ok("thread", f"thread={side["thread"]}",
	                viewer="push.sl")["last_seq"]
	flow.ok("mark-seen", f"thread={side["thread"]}", f"up-to={later}",
	        viewer="push.sl")
	replayed_noop = flow.ok("mark-seen", "op-id=mark-1",
	                        f"thread={side['thread']}", f"up-to={top}",
	                        viewer="push.sl")
	assert replayed_noop["operation"]["state"] == "replayed"
	assert replayed_noop["advanced"] is False and \
		replayed_noop["cursor"] == top, \
		"the no-op replay did not return THAT invocation's result"

	# 8. Every mutation family: one exact retry each — the second call
	# replays the first's committed seq.
	fam = flow.ok("create", "team=push", "kind=bug",
	              "title=family", "origin=self-initiated", "classification=suspected-defect",
	              "body=family", viewer="push.sl")
	# W288: the revise family below promotes a contract, which is the
	# claimant's act — so this fixture Work is claimed.
	flow.ok("claim", f"work={fam["work_id"]}", viewer="push.sl")
	# W38: every settable phase is an UNCLAIMED state, so the phase
	# family would release that claim out from under revise. It gets
	# its own Work; the families are independent by design.
	phased = flow.ok("create", "team=push", "kind=bug",
	                 "title=phased", "origin=self-initiated",
	                 "classification=suspected-defect",
	                 "body=phased", viewer="push.sl")
	for label, argv, viewer in (
			("create", ("create", "team=push", "kind=bug",
			            "title=twin", "origin=self-initiated", "classification=suspected-defect",
			            "body=twin"), "push.sl"),
			("discuss", ("start-thread", "subject=trial subject", "body=ctx",
			             f"label={fam["work_id"]}"), "push.sl"),
			("label", ("label", f"thread={side["thread"]}",
			           f"work={fam["work_id"]}"), "push.sl"),
			("classify", ("classify", f"work={fam["work_id"]}",
			              "as=confirmed-defect"), "push.sl"),
			("phase", ("phase", f"work={phased["work_id"]}",
			           "to=parked", "reason=family"), "push.sl"),
			("try", ("try", f"work={fam["work_id"]}", "candidate=c1",
			           "assign=web.verify"), "push.sl"),
			("revise", ("revise", f"work={fam["work_id"]}",
			            f"message={fam['seq']}", "expect=0",
			            "rationale=contract"), "push.sl")):
		first = flow.ok(*argv, f"op-id=fam-{label}", viewer=viewer)
		again = flow.ok(*argv, f"op-id=fam-{label}", viewer=viewer)
		assert again["operation"]["state"] == "replayed", label
		assert again["seq"] == first["seq"], \
			f"{label} retry performed a second effect"

	assert_dense_audit(flow, "lang.ada")


def test_wf12_protected_init_and_reinit(flow):
	"""Init end to end: the named proposed-document participant, the
	committed operation, the exact replay against the existing
	authority, the conflicting-document refusal, and the id-less
	refusal."""
	config = document(verification_teams())
	flow.write_config(config)
	import os as _os
	home = _os.path.dirname(flow.config_path)
	first = flow.ok("activate", "op-id=init-1", f"directory={home}",
	                viewer="lang.ada")
	assert first["operation"] == {"id": "init-1", "state": "committed"}
	assert first["generation"] == 1
	again = flow.ok("activate", "op-id=init-1", f"directory={home}",
	                viewer="lang.ada")
	assert again["operation"]["state"] == "replayed"
	assert again["database"] == first["database"], \
		"the protected re-init did not recover the committed binding"
	# An identity the accepted generation does not know learns nothing.
	error = flow.refuse("activate", "op-id=init-1", f"directory={home}",
	                    viewer="ghost.gone")
	assert "not a registered member" in error
	# A different document under the same identity is a conflict.
	edited = document(verification_teams())
	edited["instance"]["name"] = "edited"
	flow.write_config(edited)
	error = flow.refuse("activate", "op-id=init-1", f"directory={home}",
	                    viewer="lang.ada")
	assert "different request" in error
	# Id-less re-init keeps today's honest refusal.
	flow.write_config(config)
	error = flow.refuse("activate", f"directory={home}", viewer="lang.ada")
	assert "already exists" in error
