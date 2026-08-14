"""A4: tags, obligations, seen cursors, planned Next.

Cardinality is the law under test: `+` is the only fan-out; `@` and `=>` name
exactly one resolved endpoint. The planned-`Next` pair — set on pass, consumed
on the audited return, never silently cleared — carries its own break-sweep.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402


import fixtures as fx


@pytest.fixture
def store(tmp_path):
	spec = {"lang": {"members": {"ada": ["dev"]},
	                 "kinds": ["bug", "rsrch", "impl", "rev"]},
	        "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	        "web": {"members": {"wren": ["dev"]}, "kinds": ["bug"]}}
	with fx.open_instance(str(tmp_path), spec) as authority:
		yield authority


@pytest.fixture
def work(store):
	return tr.create_work(store, team="lang", kind="rsrch",
	                      title="parser recovery", origin="external-report",
	                      author="ada", body="the report")["work_id"]


def _row(store, work_id):
	return store.conn.execute("SELECT * FROM work WHERE id=?",
	                          (work_id,)).fetchone()


# -- include (+) -------------------------------------------------------------

def test_include_expands_wildcards_and_records_the_expansion(store, work):
	result = tr.post_message(store, work, author_team="lang", author="ada",
	                         body="fyi", include="*.bug")
	assert result["included"] == ["lang.bug", "push.bug", "web.bug"]
	event = store.events(after=result["seq"] - 1, limit=1)[0]
	recorded = event["payload"]["include"]
	assert [entry["endpoint"] for entry in recorded] == \
		["lang.bug", "push.bug", "web.bug"], \
		"the exact expansion is not recorded with the publication"
	# C4: each expansion entry is a FULL resolution snapshot.
	for entry in recorded:
		assert set(entry) == {"endpoint", "route", "role", "handlers",
		                      "generation"}, entry
		assert entry["generation"] == 1 and entry["handlers"]
	teams = {row["team"] for row in store.conn.execute(
		"SELECT team FROM work_participants WHERE work=?", (work,))}
	assert teams == {"lang", "push", "web"}


def test_include_of_everything_reaches_every_live_endpoint_once(store, work):
	result = tr.post_message(store, work, author_team="lang", author="ada",
	                         body="shutdown notice", include="*.*")
	assert sorted(result["included"]) == result["included"]
	assert len(result["included"]) == len(set(result["included"]))
	assert "lang.rsrch" in result["included"]


def test_a_selector_that_lands_nowhere_is_refused_at_tag_time(store, work):
	with pytest.raises(bw.WorkError, match="matches no live endpoint"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="void", include="ghost.bug")


# -- request (@) -------------------------------------------------------------

def test_request_creates_one_obligation_and_current_stays(store, work):
	before = _row(store, work)
	result = tr.post_message(store, work, author_team="lang", author="ada",
	                         body="please confirm the driver hang",
	                         request="push.bug")
	after = _row(store, work)
	assert (after["current_team"], after["current_kind"]) == \
		(before["current_team"], before["current_kind"]), \
		"@ moved the baton; it must not"
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (result["seq"],)).fetchone()
	assert (obligation["team"], obligation["kind"],
	        obligation["status"]) == ("push", "bug", "pending")


@pytest.mark.parametrize("target", ["*.bug", "push.*", "*.*",
                                    "push.bug,web.bug"])
def test_request_refuses_every_fan_out_shape(store, work, target):
	with pytest.raises(bw.WorkError, match="exactly one endpoint"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="x", request=target)
	assert store.conn.execute(
		"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"] == 0


def test_respond_discharges_the_obligation_with_the_answer(store, work):
	seq = tr.post_message(store, work, author_team="lang", author="ada",
	                      body="confirm?", request="push.bug")["seq"]
	with pytest.raises(bw.WorkError, match="cannot discharge"):
		tr.respond_obligation(store, seq, team="web", member="wren",
		                      body="not ours")
	result = tr.respond_obligation(store, seq, team="push", member="sl",
	                               body="confirmed, trace attached")
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (seq,)).fetchone()
	assert obligation["status"] == "responded"
	assert obligation["resolved_seq"] == result["seq"]
	with pytest.raises(bw.WorkError, match="already responded"):
		tr.respond_obligation(store, seq, team="push", member="sl", body="again")


def test_dispose_is_the_no_action_answer_with_words(store, work):
	seq = tr.post_message(store, work, author_team="lang", author="ada",
	                      body="fyi?", request="push.bug")["seq"]
	tr.dispose_obligation(store, seq, team="push", member="sl",
	                      disposition="no action: known limitation")
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (seq,)).fetchone()
	assert obligation["status"] == "disposed"


def test_request_and_pass_in_one_message_is_ambiguous_and_refused(store, work):
	with pytest.raises(bw.WorkError, match="one operation"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="x", request="push.bug", pass_to="lang.impl")


# -- pass (=>) and planned Next ----------------------------------------------

def test_pass_moves_the_one_current(store, work):
	tr.post_message(store, work, author_team="lang", author="ada",
	                body="confirmed defect", pass_to="lang.impl")
	row = _row(store, work)
	assert (row["current_team"], row["current_kind"]) == ("lang", "impl")


def test_pass_with_next_sets_it_and_the_return_consumes_it(store, work):
	"""The canonical flow with the planned return: impl gets the baton with
	Next = lang.rev; the pass BACK to lang.rev is audited as `return` and
	clears Next."""
	tr.post_message(store, work, author_team="lang", author="ada",
	                body="implement this", pass_to="lang.impl",
	                set_next="lang.rev")
	row = _row(store, work)
	assert (row["next_team"], row["next_kind"]) == ("lang", "rev")

	result = tr.post_message(store, work, author_team="lang", author="ada",
	                         body="implementation complete",
	                         pass_to="lang.rev")
	assert result["kind"] == "return", \
		"the consuming pass is not audited as a return"
	row = _row(store, work)
	assert (row["current_team"], row["current_kind"]) == ("lang", "rev")
	assert row["next_team"] is None and row["next_kind"] is None
	event = store.events(after=result["seq"] - 1, limit=1)[0]
	assert event["kind"] == "return"
	assert event["payload"]["consumed_next"] is True


def test_a_pass_elsewhere_leaves_the_planned_next_visibly_set(store, work):
	tr.post_message(store, work, author_team="lang", author="ada",
	                body="implement", pass_to="lang.impl",
	                set_next="lang.rev")
	result = tr.post_message(store, work, author_team="lang", author="ada",
	                         body="actually needs research first",
	                         pass_to="lang.rsrch")
	assert result["kind"] == "pass", "a detour is not a return"
	row = _row(store, work)
	assert (row["next_team"], row["next_kind"]) == ("lang", "rev"), \
		"the detour silently cleared the planned Next"


def test_next_requires_a_pass_and_pass_refuses_fan_out(store, work):
	with pytest.raises(bw.WorkError, match="set by a pass"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="x", set_next="lang.rev")
	with pytest.raises(bw.WorkError, match="exactly one endpoint"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="x", pass_to="*.*")
	with pytest.raises(bw.WorkError, match="already at"):
		tr.post_message(store, work, author_team="lang", author="ada",
		                body="x", pass_to="lang.rsrch")


# -- participation and visibility -------------------------------------------

def test_any_configured_member_may_contribute_and_becomes_participant(
		store, work):
	"""R1 matrix (superseding the old barrier): open browsing carries the
	right to chip in — a configured member posts without invitation, and
	their team becomes a durable participant in the SAME transaction."""
	result = tr.post_message(store, work, author_team="push", author="sl",
	                         body="drive-by evidence, gladly given")
	assert result["kind"] == "post_message"
	assert store.conn.execute(
		"SELECT 1 FROM work_participants WHERE work=? AND team='push'",
		(work,)).fetchone(), \
		"the contribution did not record durable participation"


# -- mark_seen ---------------------------------------------------------------

def test_mark_seen_is_the_only_writer_and_is_monotonic(store, work):
	seq = tr.post_message(store, work, author_team="lang", author="ada",
	                      body="one")["seq"]
	result = tr.mark_seen(store, work, team="lang", member="ada",
	                      up_to_seq=seq)
	assert result["advanced"] is True and result["cursor"] == seq
	backwards = tr.mark_seen(store, work, team="lang", member="ada",
	                         up_to_seq=seq - 1)
	assert backwards["advanced"] is False and backwards["cursor"] == seq, \
		"the cursor moved backwards"
	again = tr.mark_seen(store, work, team="lang", member="ada",
	                     up_to_seq=seq)
	assert again["advanced"] is False, "an idempotent mark advanced"
	cursors = store.conn.execute(
		"SELECT seq FROM seen WHERE team='lang' AND member='ada' AND work=?",
		(work,)).fetchall()
	assert [row["seq"] for row in cursors] == [seq]


def test_seen_state_is_per_member_never_shared(store, work):
	tr.post_message(store, work, author_team="lang", author="ada",
	                body="invite web", include="web.bug")
	seq = store.last_seq()
	tr.mark_seen(store, work, team="lang", member="ada", up_to_seq=seq)
	web_cursor = store.conn.execute(
		"SELECT seq FROM seen WHERE team='web' AND member='wren' AND work=?",
		(work,)).fetchone()
	assert web_cursor is None, "one member's mark moved another's cursor"
