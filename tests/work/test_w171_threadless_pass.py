"""W171 (finding-pass-is-work-event): pass is a THREADLESS Work event.

The acceptance pins from the finding, verbatim intent: the CLI/TUI
command surface accepts the mandatory `work= to= comment=` shape with
no `thread=` (and refuses the old coupling as an unknown operand); the
pass event projects the exact comment and complete transition
metadata; atomic claim release, Current/phase transfer, retry replay,
stale/unauthorized refusal and destination readiness keep their
guarantees; and passing leaves every discussion-message and personal
cursor/count projection unchanged — proven on Work carrying several
Threads, through the ordinary implementation-to-review handoff and the
approval-to-review consuming return.
"""

from __future__ import annotations

import contextlib
import io
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import cli as work_cli                        # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	document = fx.config_document(
		{"lang": {"members": {"ada": ["impl"],
		                              "grace": ["impl"]},
		          "kinds": ["bug"]},
		 "rev": {"members": {"bee": ["rview"]},
		         "kinds": ["bug"]}})
	# A real shared route is required to prove that route eligibility does
	# not let one handler transfer underneath another handler's active claim.
	document["teams"]["lang"]["routes"]["main"]["handlers"] = \
		["ada", "grace"]
	config = os.path.join(str(tmp_path), "baton.json")
	with open(config, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config, participant="lang.ada")
	database = result["database"]
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def run(world, *argv, viewer="lang.ada"):
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", viewer] + list(argv))
	return code, out.getvalue(), err.getvalue()


def ok(world, *argv, viewer="lang.ada"):
	code, out, err = run(world, *argv, viewer=viewer)
	assert code == 0, err
	return _json.loads(out)["result"]


def refusal(world, *argv, viewer="lang.ada"):
	code, _out, err = run(world, *argv, viewer=viewer)
	assert code == 1
	return _json.loads(err)["error"]


def make(world, title="carried"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")


def test_thread_is_an_unknown_pass_operand(world):
	"""The old coupling cannot silently survive: `thread=` refuses as
	an unknown key, and the same act without it commits."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	error = refusal(world, "pass", f"work={work}", "to=rev.bug",
	                f"thread={thread}", "comment=old dialect")
	assert "unknown key 'thread'" in error
	detail = ok(world, "detail", f"work={work}")
	assert detail["route"]["endpoint"] == "lang.bug", \
		"the refused old dialect moved the baton"
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "comment=new dialect")
	assert passed["kind"] == "pass" and passed["work"] == work


def test_the_event_is_the_complete_authoritative_record(world):
	"""The pass event owns the handoff evidence: exact comment plus the
	full transition metadata — and no thread."""
	work = make(world)["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "set-next=lang.bug",
	            "comment=exact evidence, verbatim")
	event = [entry for entry in world["store"].events()
	         if entry["seq"] == passed["seq"]][0]
	payload = event["payload"]
	assert payload["comment"] == "exact evidence, verbatim"
	assert payload["work"] == work
	assert payload["pass_resolution"]["endpoint"] == "rev.bug"
	assert payload["destination_phase"] == "queued"
	assert payload["set_next"] == "lang.bug"
	assert payload["consumed_next"] is False
	assert payload["authorization"]["endpoint"] == "lang.bug", \
		"the audited authorization snapshot is missing"
	assert "thread" not in payload, \
		"the threadless event still names a thread"
	assert passed["to"] == "rev.bug"
	assert passed["destination_phase"] == "queued"


def test_a_pass_moves_no_message_cursor_or_count(world):
	"""Work carrying SEVERAL threads: the pass changes the Work row and
	the journal — and not one message, cursor, or personal count."""
	store = world["store"]
	born = make(world)
	work = born["work_id"]
	tr.create_thread(store, actor_team="lang", actor="ada",
	                 body="second venue", labels=[work],
	                 subject="side discussion")
	tr.post_thread(store, born["thread"], author_team="lang",
	               author="ada", body="first venue detail")
	threads = [row["id"] for row in ok(world, "work-threads",
	                                   f"work={work}")["rows"]]
	assert len(threads) >= 2, "the rig needs several threads"

	def snapshot():
		return {
			"messages": store.conn.execute(
				"SELECT COUNT(*) AS n FROM messages").fetchone()["n"],
			"cursors": store.conn.execute(
				"SELECT * FROM seen ORDER BY 1, 2, 3").fetchall(),
			"obligations": store.conn.execute(
				"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"],
			"pages": {thread: ok(world, "thread", f"thread={thread}")
			          ["messages"] for thread in threads},
			# snapshot_seq legitimately advances with the pass event;
			# every COUNT must hold still.
			"new": {viewer: {key: value for key, value in pj.new_count(
				store, work, viewer_team=viewer.split(".")[0],
				viewer_member=viewer.split(".")[1]).items()
				if key != "snapshot_seq"}
				for viewer in ("lang.ada", "lang.grace", "rev.bee")},
		}

	before = snapshot()
	detail_before = ok(world, "detail", f"work={work}")
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "comment=silent on every message surface")
	after = snapshot()
	assert after["messages"] == before["messages"], \
		"the pass created a message"
	assert after["cursors"] == before["cursors"], \
		"the pass moved a personal cursor"
	assert after["obligations"] == before["obligations"]
	assert after["pages"] == before["pages"], \
		"a thread page changed under a threadless pass"
	assert after["new"] == before["new"], \
		"a personal New count changed under a threadless pass"
	detail = ok(world, "detail", f"work={work}")
	assert detail["message_count"] == detail_before["message_count"]
	assert detail["route"]["endpoint"] == "rev.bug", \
		"the immutability held but the baton did not move"
	assert passed["kind"] == "pass"


def test_the_handoff_and_the_consuming_return(world):
	"""The ordinary implementation-to-review handoff wakes the
	destination through Work readiness; the approval-to-review return
	consumes the planned Next — claim released both ways."""
	store = world["store"]
	work = make(world)["work_id"]
	tr.claim_work(store, work, actor_team="lang", actor="ada")
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "set-next=lang.bug",
	            "comment=please review")
	assert passed["kind"] == "pass"
	detail = ok(world, "detail", f"work={work}")
	assert detail["handler"] is None, "the handoff kept the claim"
	assert detail["phase"] == "queued"
	woken = pj.wait_actionable(store, viewer_team="rev",
	                           viewer_member="bee", timeout_seconds=0)
	assert any(action["kind"] == "work" and action["work"] == work
	           for action in woken["actionable"]), \
		"the destination was not woken through Work readiness"
	returned = ok(world, "pass", f"work={work}", "to=lang.bug",
	              "comment=approved",
	              viewer="rev.bee")
	assert returned["kind"] == "return", \
		"the consuming pass is not audited as a return"
	assert returned["consumed_next"] is True
	detail = ok(world, "detail", f"work={work}")
	assert detail["route"]["endpoint"] == "lang.bug"
	assert detail["next"] is None


def test_stale_and_unauthorized_refusals_hold(world):
	work = make(world)["work_id"]
	assert "not a resolved handler" in refusal(
		world, "pass", f"work={work}", "to=rev.bug",
		"comment=not mine", viewer="rev.bee")
	assert "already at" in refusal(
		world, "pass", f"work={work}", "to=lang.bug",
		"comment=nowhere to go")
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert "terminal work never moves" in refusal(
		world, "pass", f"work={work}", "to=rev.bug", "comment=late")


def test_another_route_handler_cannot_pass_the_claimants_work(world):
	"""The active claim is execution ownership, not merely route membership.

	A second eligible handler must use the explicit recovery protocol; pass
	must never let them transfer Work underneath the recorded claimant and
	silently clear that claim.
	"""
	work = make(world)["work_id"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	before = ok(world, "detail", f"work={work}")
	error = refusal(world, "pass", f"work={work}", "to=rev.bug",
	                "comment=steal the handoff", viewer="lang.grace")
	assert "claim" in error and "lang.ada" in error, error
	after = ok(world, "detail", f"work={work}")
	for field in ("route", "phase", "next", "handler", "status"):
		assert after[field] == before[field], \
			f"the losing non-claimant changed {field}"
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "comment=claimant handoff", viewer="lang.ada")
	assert passed["kind"] == "pass"
