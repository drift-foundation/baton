"""W92: schema 16 carries the selected persisted-state groundwork.

The fresh-authority cutover ships the parked persisted state that schema 14
could not hold: required team-local Work `priority` (W10) and the stable
change identity `last_change_seq` + millisecond `last_changed_at` (W84).
Their TUI presentation remains W10/W84 feature work; W78 project metadata is
deliberately ABSENT because its persisted shape is still an open design
question in its finding.
"""

from __future__ import annotations

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import authority as au                        # noqa: E402
from baton_work import projection as pj                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures as fx                                         # noqa: E402


@pytest.fixture()
def store(tmp_path):
	_config, database = fx.build_instance(
		str(tmp_path), {"lang": {"members": {"ada": ["dev"]},
		                         "kinds": ["bug"]}})
	with bw.Authority(database) as authority:
		yield authority


def test_the_fresh_authority_is_schema_17(store):
	assert store.meta()["schema_version"] == "17"


def test_created_work_defaults_to_normal_priority(store):
	created = tr.create_work(store, team="lang", kind="bug", title="born",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	row = store.conn.execute("SELECT priority FROM work WHERE id=?",
	                         (created["work_id"],)).fetchone()
	assert row["priority"] == "normal"


def test_the_priority_domain_is_closed_at_the_schema(store):
	created = tr.create_work(store, team="lang", kind="bug", title="hard",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	import sqlite3
	with pytest.raises(sqlite3.IntegrityError):
		store.conn.execute("UPDATE work SET priority='urgent' WHERE id=?",
		                   (created["work_id"],))


def test_birth_stamps_the_change_identity(store):
	created = tr.create_work(store, team="lang", kind="bug", title="stamp",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	row = store.conn.execute(
		"SELECT created_seq, last_change_seq, last_changed_at "
		"FROM work WHERE id=?", (created["work_id"],)).fetchone()
	assert row["last_change_seq"] == row["created_seq"]
	assert row["last_changed_at"]


def test_a_direct_row_mutation_advances_the_change_identity(store):
	created = tr.create_work(store, team="lang", kind="bug", title="moved",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	moved = tr.set_phase(store, created["work_id"], actor_team="lang",
	                     actor="ada", phase="active", reason="starting")
	row = store.conn.execute(
		"SELECT last_change_seq FROM work WHERE id=?",
		(created["work_id"],)).fetchone()
	assert row["last_change_seq"] == moved["seq"], \
		"the change identity does not name the mutating event"


def test_an_unrelated_act_leaves_the_change_identity_alone(store):
	created = tr.create_work(store, team="lang", kind="bug", title="quiet",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	before = store.conn.execute(
		"SELECT last_change_seq, last_changed_at FROM work WHERE id=?",
		(created["work_id"],)).fetchone()
	# Conversation continues without touching the Work row: the set of
	# indirect acts that count as recency is W84's own ruling, not guessed.
	tr.post_thread(store, created["thread"], author_team="lang",
	               author="ada", body="talk is not a row change")
	after = store.conn.execute(
		"SELECT last_change_seq, last_changed_at FROM work WHERE id=?",
		(created["work_id"],)).fetchone()
	assert tuple(after) == tuple(before)


def test_the_row_projection_exposes_the_new_canonical_values(store):
	created = tr.create_work(store, team="lang", kind="bug", title="seen",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	view = pj.detail(store, created["work_id"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["priority"] == "normal"
	assert view["last_change_seq"] == view["snapshot_seq"] or \
		view["last_change_seq"] <= view["snapshot_seq"]
	assert view["last_changed_at"]


def test_the_millisecond_clock_is_iso_with_milliseconds():
	stamp = au._utc_now_ms()
	assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z",
	                    stamp), stamp


def test_the_active_claim_state_is_present_and_unclaimed(store):
	"""finding-active-work-claim: the fresh schema carries the atomic
	claimant identity; it projects null until the gated claim operation
	exists and succeeds — never inferred from route membership."""
	created = tr.create_work(store, team="lang", kind="bug", title="claim",
	                         origin="external-report", classification="suspected-defect", author="ada",
	                         body="b")
	row = store.conn.execute(
		"SELECT active_team, active_member FROM work WHERE id=?",
		(created["work_id"],)).fetchone()
	assert (row["active_team"], row["active_member"]) == (None, None)
	view = pj.detail(store, created["work_id"], viewer_team="lang",
	                 viewer_member="ada")
	assert view["active"] is None


def test_creation_requires_a_concrete_classification(store):
	"""finding-active-work-claim clarification: the submitter chooses —
	omission and 'unknown' refuse at creation; the handler may still
	reclassify later (including back to unknown, an ordinary value)."""
	with pytest.raises(bw.WorkError, match="concrete classification"):
		tr.create_work(store, team="lang", kind="bug", title="lazy",
		               origin="external-report", author="ada", body="b")
	with pytest.raises(bw.WorkError, match="concrete classification"):
		tr.create_work(store, team="lang", kind="bug", title="lazy",
		               origin="external-report", author="ada", body="b",
		               classification="unknown")
	created = tr.create_work(store, team="lang", kind="bug", title="chosen",
	                         origin="external-report", author="ada",
	                         body="b", classification="suspected-defect")
	tr.classify(store, created["work_id"], actor_team="lang", actor="ada",
	            classification="unknown")
	row = store.conn.execute("SELECT classification FROM work WHERE id=?",
	                         (created["work_id"],)).fetchone()
	assert row["classification"] == "unknown", \
		"later reclassification is the handler's ordinary authority"
