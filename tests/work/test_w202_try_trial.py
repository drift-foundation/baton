"""W202 (finding-try-trial-vocabulary): `try` creates a trial; the
obsolete `round` surface is GONE without alias.

The suite pins the acceptance's vocabulary coherence: the creation
command is `try`, the durable object projects as `trials`/`trial`
with `due_trial` wakes and `trial:` action keys, and the old `round`
command refuses as unknown rather than surviving as an alias.
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
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["impl"]},
		                         "kinds": ["bug"]},
		                "push": {"members": {"sl": ["rview"]},
		                         "kinds": ["verify"]}})
	store = bw.Authority(database)
	yield {"config": config, "database": database, "store": store}
	store.close()


def run(world, *argv, viewer="lang.ada"):
	out, err = io.StringIO(), io.StringIO()
	with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
		code = work_cli.main(["--config", world["config"],
		                      "--participant", viewer] + list(argv))
	return code, out.getvalue(), err.getvalue()


def make(world):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title="candidate work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="born")["work_id"]


def test_the_obsolete_round_command_refuses_as_unknown(world):
	work = make(world)
	code, _out, err = run(world, "round", f"work={work}",
	                      "candidate=build-1", "assign=push.verify")
	assert code == 1
	assert "unknown command 'round'" in err, err
	assert "alias" not in err.lower()
	# and nothing was created by the refused spelling
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")
	assert detail["trials"] == []


def test_try_creates_a_trial_with_coherent_vocabulary(world):
	work = make(world)
	code, out, err = run(world, "try", f"work={work}",
	                     "candidate=build-17", "assign=push.verify")
	assert code == 0, err
	result = _json.loads(out)["result"]
	assert result["kind"] == "create_trial"
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="ada")
	trials = detail["trials"]
	assert len(trials) == 1
	assert trials[0]["trial"] == 1
	assert trials[0]["candidate"] == "build-17"
	# No mixed surface: the detail projection carries no round key.
	assert "rounds" not in detail
	assert "round" not in trials[0]
	# The audited event speaks trial vocabulary.
	newest = [event for event in world["store"].events()
	          if event["kind"] == "create_trial"]
	assert newest and newest[-1]["payload"]["work"] == work


def test_due_wakes_use_the_trial_kind_and_key(world):
	store = world["store"]
	work = make(world)
	tr.create_trial(store, work, actor_team="lang", actor="ada",
	                candidate="build-17", assign=["push.verify"],
	                review_at="2099-01-01T00:00:00Z")
	store.clock = lambda: "2099-01-02T00:00:00Z"   # the deadline arrived
	# Due responsibility lies with the Work's CURRENT route handlers.
	woken = pj.wait_actionable(store, viewer_team="lang",
	                           viewer_member="ada", timeout_seconds=0)
	due = [action for action in woken["actionable"]
	       if action["kind"] == "due_trial"]
	assert due, "no due_trial wake for the responsible route"
	assert due[0]["action_key"].startswith(f"trial:{work}:1:")
	assert due[0]["trial"] == 1
	assert "round" not in due[0]
