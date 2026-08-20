"""W36: canonical Msg/My — conversation volume and the viewer's directed
load (same-schema iteration).

`message_count` is the total DISTINCT messages in the row's DIRECT
visible scope (W179: exactly the threads labelled directly to the Work;
descendants report their own; overlap-safe; seen-independent; answers
only grow it).
`my_pending_obligations` counts unresolved directed @ obligations where
THIS participant is an eligible handler under the CURRENTLY accepted
route resolution; shared resolutions and terminal withdrawal clear it for
every handler. Reading is pure. The TUI alone combines them compactly.
"""

from __future__ import annotations

import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug", "rsrch"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	store = bw.Authority(database)
	yield store, config_path
	store.close()


def _row(store, work_id, viewer_team="lang", viewer_member="ada"):
	return pj.detail(store, work_id, viewer_team=viewer_team,
	                 viewer_member=viewer_member)


def test_message_count_is_direct_distinct_and_seen_independent(world):
	store, _config = world
	parent = tr.create_work(store, team="lang", kind="bug",
	                        title="parent scope",
	                        origin="external-report", classification="suspected-defect", author="ada",
	                        body="parent opener")
	left = tr.create_work(store, team="lang", kind="bug",
	                      title="left child", origin="decomposition", classification="suspected-defect",
	                      author="ada", body="left opener",
	                      parent=parent["work_id"])
	right = tr.create_work(store, team="lang", kind="bug",
	                       title="right child", origin="decomposition", classification="suspected-defect",
	                       author="ada", body="right opener",
	                       parent=parent["work_id"])
	# One thread labelled to BOTH children: its messages must count
	# ONCE for the parent (overlap-safe) though reachable twice.
	shared = tr.create_thread(
		store, actor_team="lang", actor="ada", body="spans both",
		labels=[left["work_id"], right["work_id"]],
		subject="the shared conversation")

	# W179 DIRECT scope: the parent counts ONLY its own opener; each
	# child counts its opener plus the shared thread — which counts
	# for BOTH children (visible reuse), never for the parent.
	assert _row(store, parent["work_id"])["message_count"] == 1
	assert _row(store, left["work_id"])["message_count"] == 2
	assert _row(store, right["work_id"])["message_count"] == 2

	tr.post_thread(store, shared["thread"], author_team="lang",
	               author="ada", body="one more in the shared thread")
	assert _row(store, parent["work_id"])["message_count"] == 1, \
		"a descendant conversation inflated the parent's direct Msg"
	assert _row(store, left["work_id"])["message_count"] == 3
	assert _row(store, right["work_id"])["message_count"] == 3

	# Seen-independence: marking everything seen changes nothing.
	tr.seen_thread(store, shared["thread"], team="lang", member="ada",
	               up_to_seq=store.last_seq())
	assert _row(store, left["work_id"])["message_count"] == 3
	assert _row(store, left["work_id"])["new"] != 3, \
		"New and Msg collapsed into one meaning"


def test_my_counts_only_my_eligible_pending_obligations(world):
	store, _config = world
	# sl's push-owned epic: as its Route handler he requests
	# lang.bug (handled by ada per the fixture route); grace is NOT an
	# eligible handler of that route, and a + inclusion counts for
	# nobody.
	epic = tr.create_work(store, team="push", kind="bug",
	                      title="the epic", origin="external-report", classification="suspected-defect",
	                      author="sl", body="opener")
	consumer = tr.create_work(store, team="push", kind="bug",
	                          title="consumer",
	                          origin="external-report", classification="suspected-defect", author="sl",
	                          body="consumer opener")
	tr.post_thread(store, consumer["thread"], author_team="push",
	               author="sl", body="lang: please confirm",
	               include="lang.bug")
	request = tr.post_thread(store, epic["thread"], author_team="push",
	                         author="sl", body="confirm the defect?",
	                         request="lang.bug", wait=False, on=epic["work_id"])

	ada = _row(store, epic["work_id"], viewer_member="ada")
	grace = _row(store, epic["work_id"], viewer_member="grace")
	assert ada["my_pending_obligations"] == 1
	assert grace["my_pending_obligations"] == 0, \
		"a non-handler acquired another member's load"
	# The include (+) never counts for anyone.
	assert _row(store, consumer["work_id"], viewer_team="push",
	            viewer_member="sl")["my_pending_obligations"] == 0

	# The ANSWER grows Msg and clears My for every eligible handler.
	before_msg = ada["message_count"]
	tr.respond_obligation(store, request["seq"], team="lang",
	                      member="ada", body="confirmed, tracked")
	after = _row(store, epic["work_id"], viewer_member="ada")
	assert after["my_pending_obligations"] == 0
	assert after["message_count"] == before_msg + 1, \
		"the answer did not grow the conversation volume"


def test_terminal_withdrawal_clears_my(world):
	store, _config = world
	epic = tr.create_work(store, team="push", kind="bug",
	                      title="withdrawn epic",
	                      origin="external-report", classification="suspected-defect", author="sl",
	                      body="opener")
	tr.post_thread(store, epic["thread"], author_team="push",
	               author="sl", body="please retest",
	               request="lang.bug", wait=False, on=epic["work_id"])
	assert _row(store, epic["work_id"])["my_pending_obligations"] == 1
	tr.close_work(store, epic["work_id"], actor_team="push",
	              actor="sl", rationale="obsolete", outcome="cancelled")
	assert _row(store, epic["work_id"])["my_pending_obligations"] == 0, \
		"terminal withdrawal left the obligation in My"


def test_eligibility_follows_the_currently_accepted_routes(world):
	"""Re-routing the handling member under an accepted generation-2
	configuration moves the SAME pending obligation from one member's
	My to the other's — eligibility is live, not a creation snapshot."""
	store, config_path = world
	epic = tr.create_work(store, team="push", kind="bug",
	                      title="rerouted epic",
	                      origin="external-report", classification="suspected-defect", author="sl",
	                      body="opener")
	tr.post_thread(store, epic["thread"], author_team="push",
	               author="sl", body="confirm?", request="lang.bug", wait=False,
	               on=epic["work_id"])
	assert _row(store, epic["work_id"],
	            viewer_member="ada")["my_pending_obligations"] == 1
	assert _row(store, epic["work_id"],
	            viewer_member="grace")["my_pending_obligations"] == 0

	document = _json.load(open(config_path))
	document["generation"] = 2
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["grace"]
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	lc.accept_config(config_path, actor="lang.ada")

	assert _row(store, epic["work_id"],
	            viewer_member="ada")["my_pending_obligations"] == 0, \
		"the re-routed member kept the load"
	assert _row(store, epic["work_id"],
	            viewer_member="grace")["my_pending_obligations"] == 1, \
		"the new handler did not acquire the load"


def test_reading_is_pure_and_counts_survive_reopen(world, tmp_path):
	store, config_path = world
	epic = tr.create_work(store, team="push", kind="bug",
	                      title="pure epic", origin="external-report", classification="suspected-defect",
	                      author="sl", body="opener")
	tr.post_thread(store, epic["thread"], author_team="push",
	               author="sl", body="request", request="lang.bug", wait=False,
	               on=epic["work_id"])
	before = store.events()
	first = _row(store, epic["work_id"])
	assert store.events() == before, "reading Msg/My mutated the audit"

	database = store.path
	fresh = bw.Authority(database)
	again = _row(fresh, epic["work_id"])
	fresh.close()
	assert (again["message_count"], again["my_pending_obligations"]) == \
		(first["message_count"], first["my_pending_obligations"]), \
		"a rebuild/reopen changed the derived counts"


def test_verification_assignments_count_in_my(world):
	"""R1: a candidate-trial @ verification assignment is directed load
	for its eligible handler until reported or withdrawn — never for a
	non-handler."""
	store, _config = world
	epic = tr.create_work(store, team="lang", kind="rsrch",
	                      title="verified epic",
	                      origin="external-report", classification="suspected-defect", author="ada",
	                      body="opener")
	created = tr.create_trial(store, epic["work_id"], actor_team="lang",
	                          actor="ada", candidate="build-A",
	                          assign=["push.bug"])
	assert _row(store, epic["work_id"], viewer_team="push",
	            viewer_member="sl")["my_pending_obligations"] == 1, \
		"the assigned verifier owes nothing?"
	assert _row(store, epic["work_id"], viewer_team="lang",
	            viewer_member="grace")["my_pending_obligations"] == 0, \
		"a non-handler acquired verification load"

	tr.report(store, created["assignments"][0], team="push", member="sl",
	          observation="passed", evidence="green run")
	assert _row(store, epic["work_id"], viewer_team="push",
	            viewer_member="sl")["my_pending_obligations"] == 0, \
		"the report did not clear the verification load"

	# Withdrawal clears likewise: a second trial, then abandonment.
	second = tr.create_trial(store, epic["work_id"], actor_team="lang",
	                         actor="ada", candidate="build-B",
	                         assign=["push.bug"])
	assert _row(store, epic["work_id"], viewer_team="push",
	            viewer_member="sl")["my_pending_obligations"] == 1
	tr.abandon_trial(store, epic["work_id"], second["trial"],
	                 actor_team="lang", actor="ada",
	                 reason="candidate replaced")
	assert _row(store, epic["work_id"], viewer_team="push",
	            viewer_member="sl")["my_pending_obligations"] == 0, \
		"withdrawal left the verification load pending"


def test_the_msg_my_column_drops_whole_at_narrow_widths(world):
	"""R2: the responsive budget keeps or omits Msg/My as a UNIT — the
	retained identity and workflow columns keep their widths."""
	from baton_work.tui import app
	wide = next(width for width in range(120, 40, -1)
	            if any(name == "MSG/MY"
	                   for name, _w in app.visible_columns(width)))
	narrow = next(width for width in range(wide, 30, -1)
	              if not any(name == "MSG/MY"
	                         for name, _w in app.visible_columns(width)))
	kept = dict(app.visible_columns(narrow))
	assert "MSG/MY" not in kept
	# W73 retired ST; W2938 retired NEW from this list and added no
	# replacement, so HANDLER is what the retained-width property is
	# asked about now.
	for name in ("HANDLER",):
		assert kept[name] == dict(app.COLUMNS)[name], \
			f"{name} shrank to make room instead of a whole-column drop"
	present = dict(app.visible_columns(wide))
	assert present["MSG/MY"] == dict(app.COLUMNS)["MSG/MY"]
	assert app.layout_fits(narrow), \
		"the narrow layout does not actually fit its terminal"
