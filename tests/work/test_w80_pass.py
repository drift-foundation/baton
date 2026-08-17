"""W80: the explicit `pass` verb — transfer gets its own canonical
surface.

`pass work= to= comment=` (W171, finding-pass-is-work-event; phase input
superseded by W73):
ONE indivisible THREADLESS Work event — the comment is durable handoff
evidence stored with the authoritative pass event itself, Current and
the route-derived destination phase transfer, any planned `set-next=`
records, and the
sender's active claim releases. No Thread is involved and no Message
exists: a pass moves no cursor and no Message/My/New/obligation count.
A refusal leaves everything unchanged. Plain `say` remains discussion
with the `@ request=` operator.
"""

from __future__ import annotations

import contextlib
import hashlib
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
from baton_work import transitions as tr                      # noqa: E402
from baton_work.tui.app import assist_text                    # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["impl"],
		                                     "grace": ["impl"]},
		                         "kinds": ["bug"]},
		                "rev": {"members": {"bee": ["rview"]},
		                        "kinds": ["bug"]}})
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


def make(world):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title="carried", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")


def test_pass_is_one_indivisible_transfer(world):
	"""The canonical surface: evidence appended, Current + derived
	phase + planned Next recorded, the sender's claim released — one
	act, one audited event."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	before = ok(world, "thread", f"thread={thread}")
	passed = ok(world, "pass", f"work={work}", "to=rev.bug",
	            "set-next=lang.bug",
	            "comment=please verify")
	assert passed["kind"] == "pass"
	assert passed["work"] == work
	assert passed["destination_phase"] == "review"
	detail = ok(world, "detail", f"work={work}")
	assert detail["current"]["endpoint"] == "rev.bug"
	assert detail["phase"] == "review"
	assert detail["next"]["endpoint"] == "lang.bug"
	assert detail["active"] is None, "the pass kept the sender's claim"
	page = ok(world, "thread", f"thread={thread}")
	assert page["messages"] == before["messages"], \
		"a threadless pass manufactured a discussion message"
	event = [e for e in world["store"].events() if e["seq"] == passed["seq"]][0]
	assert event["payload"]["comment"] == "please verify", \
		"the handoff evidence is not in the authoritative pass event"


def test_the_destination_phase_derives_from_the_stage_role(world):
	"""The destination route's stage role decides the phase — rview
	lands review and impl lands active — exactly the W73 rule."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	ok(world, "pass", f"work={work}", "to=rev.bug",
	   "comment=over to review")
	assert ok(world, "detail", f"work={work}")["phase"] == "review"
	ok(world, "pass", f"work={work}", "to=lang.bug",
	   "comment=back to build",
	   viewer="rev.bee")
	assert ok(world, "detail", f"work={work}")["phase"] == "active"


def test_a_refused_pass_changes_nothing(world):
	"""Refusal atomicity: a bad destination leaves the thread, the
	workflow facts, and the authority bytes exactly as they were."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	before_detail = ok(world, "detail", f"work={work}")
	before_page = ok(world, "thread", f"thread={thread}")
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		before = hashlib.sha256(handle.read()).hexdigest()
	error = refusal(world, "pass", f"work={work}", "to=ghost.bug",
	                "comment=nowhere")
	assert "ghost" in error
	after_detail = ok(world, "detail", f"work={work}")
	for field in ("current", "phase", "next", "active", "status"):
		assert after_detail[field] == before_detail[field], field
	after_page = ok(world, "thread", f"thread={thread}")
	assert len(after_page["messages"]) == len(before_page["messages"]), \
		"a refused pass left its evidence behind"
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		assert hashlib.sha256(handle.read()).hexdigest() == before


def test_authorization_and_retry(world):
	"""Only a resolved Current handler passes; an exact op-id retry
	replays the one committed transfer."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	error = refusal(world, "pass", f"work={work}", "to=rev.bug",
	                "comment=not mine",
	                viewer="rev.bee")
	assert "rev.bee" in error
	first = ok(world, "pass", f"work={work}", "to=rev.bug",
	           "comment=handing over", "op-id=xfer-1")
	again = ok(world, "pass", f"work={work}", "to=rev.bug",
	           "comment=handing over", "op-id=xfer-1")
	assert again["operation"]["state"] == "replayed"
	assert again["seq"] == first["seq"]
	events = [e for e in world["store"].events()
	          if e["kind"] in ("pass", "return")
	          and e["payload"].get("work") == work]
	assert len(events) == 1, "the retry duplicated the transfer event"
	page = ok(world, "thread", f"thread={thread}")
	assert all(m["body"] != "handing over" for m in page["messages"]), \
		"the pass left a discussion message behind"


def test_say_is_discussion_only_now(world):
	"""`say` keeps body/include/request/on — the transfer keys are
	unknown there; on= binds to request=; the @ operator still works."""
	born = make(world)
	work, thread = born["work_id"], born["thread"]
	assert "unknown key 'pass-to'" in refusal(
		world, "say", f"thread={thread}", "body=x", "pass-to=rev.bug")
	assert "unknown key 'set-next'" in refusal(
		world, "say", f"thread={thread}", "body=x",
		"set-next=rev.bug")
	assert "requires request=" in refusal(
		world, "say", f"thread={thread}", "body=x", f"on={work}")
	asked = ok(world, "say", f"thread={thread}", "body=push: confirm?",
	           "request=rev.bug", f"on={work}")
	assert asked["kind"] == "request"
	obligations = ok(world, "obligations", viewer="rev.bee")
	assert obligations, "the preserved @ operator raised no obligation"


def test_the_assist_teaches_the_new_dialect(world):
	"""The shared analyzer offers pass's form and never resurrects the
	retired say keys."""
	hint = assist_text("pass ")
	for name in ("work=", "to=", "comment="):
		assert name in hint.split("optional:")[0], (name, hint)
	assert "thread=" not in hint, "the assist resurrected the thread coupling"
	# W73: the route decides the phase, so the assist must not offer the
	# operand either — a suggestion the parser refuses is worse than
	# silence.
	assert "phase=" not in hint, "the assist offered the retired phase key"
	assert "set-next=" in hint
	say_hint = assist_text("say thread=T1 body=b ")
	assert "pass-to=" not in say_hint and "set-next=" not in say_hint
	# and typing the retired key gets the parser's own diagnostic, not
	# a value list for an operand that no longer exists
	assert assist_text("pass work=W1 to=lang.bug phase=") == \
		"unknown key 'phase'"
