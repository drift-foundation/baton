"""W415: durable managed-turn approval incidents.

`work/records/2026/08/finding-managed-turn-approval-incidents/`.

The motivating incident, three times in under an hour: a managed
reviewer turn asked for interactive command approval, the dispatcher
correctly denied it, published `waiting-input(approval)`, ended the turn
and returned the runner to `idle`. Every step was right. The net effect
was that the failure ERASED ITS OWN EVIDENCE — the lease moved on, the
Inbox row went with it, the Work stayed unclaimed, and the only
surviving explanation was in a background rollout nobody reads.

So live runtime state and durable incidents are separate facts and this
is the contract that keeps them separate:

- an incident SURVIVES what live state does not: the return to `idle`,
  a new incarnation, a managed-stack restart, and marking discussion
  seen;
- repeated reports for the same participant, episode and cause COALESCE
  into one open incident that counts, because three identical failures
  are one problem an operator fixes once — but the count is retained,
  because "this has happened three times" is what says the first fix
  did not hold;
- a new episode, or a recurrence AFTER dismissal, opens a NEW incident:
  a dismissed problem must never reappear inside a row the operator has
  already answered;
- dismissal is the action owner's, authoritative, journaled, and
  mutates NO Work;
- there is no approve, anywhere;
- and no command body, credential or environment value is ever stored —
  what travels is a closed safe category.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import cli as _cli                              # noqa: E402
from baton_work import projection as pj                         # noqa: E402
from baton_work import transitions as tr                        # noqa: E402
from baton_work.authority import WorkError                      # noqa: E402
import fixtures as fx                                           # noqa: E402


@pytest.fixture()
def world(tmp_path):
	config_path, database = fx.build_instance(
		str(tmp_path),
		{"lang": {"members": {"ada": ["dev"], "grace": ["dev"]},
		          "kinds": ["bug"]}})
	store = bw.Authority(database)
	store.clock = lambda: (os.environ.get("BATON_WORK_NOW")
	                       or bw.authority._utc_now())
	yield {"store": store, "config": config_path, "database": database}
	store.close()


@pytest.fixture(autouse=True)
def _unfrozen():
	yield
	os.environ.pop("BATON_WORK_NOW", None)


def make_work(world, title="the review nobody picked up"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


def launch(world, member="ada", incarnation="run-1", owner="lang.grace",
           **extra):
	return tr.runtime_start(world["store"], actor_team="lang",
	                        actor=member, incarnation=incarnation,
	                        adapter="codex", action_owner=owner, **extra)


def file_incident(world, member="ada", incarnation="run-1",
                  cause="approval", category="baton-cli", **extra):
	return tr.incident_report(world["store"], actor_team="lang",
	                          actor=member, incarnation=incarnation,
	                          cause=cause, category=category, **extra)


def inbox(world, member="grace"):
	return pj.inbox(world["store"], viewer_team="lang",
	                viewer_member=member)


def incident_rows(world, member="grace"):
	return [row for row in inbox(world, member)["rows"]
	        if row["kind"] == "incident"]


def work_snapshot(world):
	"""Everything an incident must never touch."""
	return [dict(row) for row in
	        world["store"].conn.execute("SELECT * FROM work")]


# -- the schema --------------------------------------------------------------

def test_the_fresh_authority_carries_the_incident_table(world):
	names = {row["name"] for row in world["store"].conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table'")}
	assert "approval_incidents" in names


# -- filing ------------------------------------------------------------------

def test_an_incident_records_the_safe_correlation(world):
	work = make_work(world)["work_id"]
	launch(world)
	result = file_incident(
		world, detail="the turn invoked the Baton CLI through a login shell",
		work=work, episode=4, action_key="work:x:4:g1")
	assert result["incident"] == 1
	assert result["coalesced"] is False
	assert result["occurrences"] == 1
	assert result["action_owner"] == "lang.grace"

	view = pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")
	assert view["open"] == 1 and view["mine"] == 1
	assert view["owed_action"] is True
	row = view["rows"][0]
	assert row["participant"] == "lang.ada"
	assert row["work"] == work and row["episode"] == 4
	assert row["action_key"] == "work:x:4:g1"
	assert row["category"] == "baton-cli" and row["cause"] == "approval"
	assert row["adapter"] == "codex"


def test_the_closed_vocabularies_are_enforced(world):
	launch(world)
	with pytest.raises(WorkError, match="is not one of"):
		file_incident(world, cause="whatever")
	# The SAFE category is closed precisely so a command body can never
	# be smuggled through it as free text.
	with pytest.raises(WorkError, match="command body is deliberately "
	                                    "never stored"):
		file_incident(world, category="rm -rf /home/sl/src")


def test_an_ownerless_runner_cannot_file_a_loose_end(world):
	# The finding forbids guessing an owner. A runner with none cannot
	# file an incident at all, and the refusal says why.
	tr.runtime_start(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", adapter="codex")
	with pytest.raises(WorkError, match="no configured action owner"):
		file_incident(world)


def test_the_owner_is_the_lease_s_and_cannot_be_chosen_by_the_reporter(world):
	"""Review round 1 of W415: the verb used to accept `action-owner=`,
	so any configured participant could plant a sticky owed action in
	any other member's Inbox through a report that carries no such
	authority. The owner now comes from the live lease and nowhere
	else."""
	launch(world, owner="lang.grace")
	assert file_incident(world)["action_owner"] == "lang.grace"
	# The operand is gone from the transition and from the grammar.
	with pytest.raises(TypeError):
		tr.incident_report(world["store"], actor_team="lang", actor="ada",
		                   incarnation="run-1", cause="approval",
		                   category="baton-cli", action_owner="lang.ada")
	assert "action-owner" not in [
		key["name"] for key in _cli.GRAMMAR["incident"]["keys"]]


# -- coalescing --------------------------------------------------------------

def test_repeated_reports_coalesce_and_count(world):
	work = make_work(world)["work_id"]
	launch(world)
	for _ in range(3):
		result = file_incident(world, work=work, episode=4)
	assert result["incident"] == 1
	assert result["coalesced"] is True
	assert result["occurrences"] == 3
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 1
	# The count is what tells an operator the first repair did not hold.
	assert incident_rows(world)[0]["occurrences"] == 3
	assert "3x" in incident_rows(world)[0]["summary"]


def test_a_new_episode_is_a_new_incident(world):
	work = make_work(world)["work_id"]
	launch(world)
	first = file_incident(world, work=work, episode=4)
	second = file_incident(world, work=work, episode=5)
	assert second["incident"] != first["incident"]
	assert second["coalesced"] is False
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 2


def test_a_different_cause_does_not_coalesce_but_a_category_does(world):
	"""The confirmed key is participant + Work episode + CAUSE. Category
	is evidence carried on the row, so a second report that classifies
	the same failure differently joins the incident rather than
	competing with it."""
	launch(world)
	file_incident(world)
	file_incident(world, category="shell")
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 1
	file_incident(world, cause="credential")
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 2


# -- what an incident SURVIVES -----------------------------------------------

def test_the_incident_outlives_the_runner_returning_to_idle(world):
	"""THE defect. The `waiting-input` row is live state and correctly
	disappears; the incident is the other question and does not."""
	work = make_work(world)["work_id"]
	launch(world)
	tr.runtime_state(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", state="waiting-input",
	                 cause="approval", detail="denied", work=work)
	file_incident(world, work=work, episode=4)

	live = [row for row in inbox(world)["rows"] if row["kind"] == "runtime"]
	assert len(live) == 1, "the transient row should be present while waiting"
	assert len(incident_rows(world)) == 1

	tr.runtime_state(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", state="idle")
	after = inbox(world)
	assert not [row for row in after["rows"] if row["kind"] == "runtime"], \
		"live state is supposed to move on"
	assert len(incident_rows(world)) == 1, \
		"the incident must not move on with it"
	assert after["owed_action"] is True


def test_the_incident_outlives_a_managed_stack_restart(world):
	launch(world)
	file_incident(world)
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1")
	# A whole new launch: new incarnation, new lease, same open incident.
	launch(world, incarnation="run-2", rationale="managed stack restarted")
	assert len(incident_rows(world)) == 1
	assert inbox(world)["owed_action"] is True


def test_marking_discussion_seen_does_not_clear_an_incident(world):
	work = make_work(world)
	launch(world)
	file_incident(world, work=work["work_id"], episode=4)
	tr.seen_thread(world["store"], work["thread"], team="lang",
	               member="grace", up_to_seq=work["seq"])
	assert len(incident_rows(world)) == 1
	assert inbox(world)["owed_action"] is True


# -- the Inbox row ------------------------------------------------------------

def test_the_inbox_row_is_owed_and_offers_no_approval(world):
	work = make_work(world)["work_id"]
	launch(world)
	file_incident(world, work=work, episode=4)
	row = incident_rows(world)[0]
	assert row["owed"] is True
	assert row["work"] == work
	assert row["completes_by"] == ["dismiss incident=1"]
	# There is no approve anywhere on this surface: the corrective
	# action is to repair the mismatch or reroute the Work.
	assert not any("approve" in verb for verb in row["completes_by"])
	assert "approve" not in row["summary"].lower()


def test_the_incident_is_only_in_its_action_owners_inbox(world):
	launch(world)
	file_incident(world)
	assert len(incident_rows(world, "grace")) == 1
	assert incident_rows(world, "ada") == []
	assert inbox(world, "ada")["owed_action"] is False


# -- dismissal ---------------------------------------------------------------

def test_only_the_action_owner_dismisses(world):
	launch(world)
	file_incident(world)
	with pytest.raises(WorkError, match="is owed by lang.grace"):
		tr.incident_dismiss(world["store"], actor_team="lang",
		                    actor="ada", incident=1)
	assert len(incident_rows(world)) == 1


def test_dismissal_is_authoritative_and_journaled(world):
	launch(world)
	file_incident(world)
	result = tr.incident_dismiss(
		world["store"], actor_team="lang", actor="grace", incident=1,
		note="repaired the deployment rule")
	assert result["incident"] == 1
	assert result["dismissed_by"] == "lang.grace"
	assert incident_rows(world) == []
	assert inbox(world)["owed_action"] is False

	history = pj.incidents(world["store"], viewer_team="lang",
	                       viewer_member="grace", include_dismissed=True)
	assert history["open"] == 0 and history["total"] == 1
	row = history["rows"][0]
	assert row["open"] is False
	assert row["dismissed_by"] == "lang.grace"
	assert row["dismissal_note"] == "repaired the deployment rule"
	assert row["dismissed_ts"]


def test_dismissing_twice_is_not_a_transition(world):
	launch(world)
	file_incident(world)
	tr.incident_dismiss(world["store"], actor_team="lang", actor="grace",
	                    incident=1)
	with pytest.raises(WorkError, match="already dismissed"):
		tr.incident_dismiss(world["store"], actor_team="lang",
		                    actor="grace", incident=1)


def test_dismissing_an_unknown_incident_refuses(world):
	with pytest.raises(WorkError, match="there is no incident 99"):
		tr.incident_dismiss(world["store"], actor_team="lang",
		                    actor="grace", incident=99)


def test_a_recurrence_after_dismissal_opens_a_new_incident(world):
	"""A dismissed problem must never reappear inside a row the
	operator has already answered."""
	work = make_work(world)["work_id"]
	launch(world)
	first = file_incident(world, work=work, episode=4)
	tr.incident_dismiss(world["store"], actor_team="lang", actor="grace",
	                    incident=first["incident"], note="thought I fixed it")
	again = file_incident(world, work=work, episode=4)
	assert again["incident"] != first["incident"]
	assert again["coalesced"] is False
	assert again["occurrences"] == 1
	assert len(incident_rows(world)) == 1


def test_dismissal_mutates_no_work(world):
	"""The ruled boundary: saying "I have seen this" is a statement
	about the incident, never about the assignment it interrupted."""
	work = make_work(world)["work_id"]
	launch(world)
	file_incident(world, work=work, episode=4)
	before = work_snapshot(world)
	tr.incident_dismiss(world["store"], actor_team="lang", actor="grace",
	                    incident=1, note="rerouted it by hand")
	assert work_snapshot(world) == before
	detail = pj.detail(world["store"], work, viewer_team="lang",
	                   viewer_member="grace")
	assert detail["phase"] == "queued"
	assert detail["handler"] is None
	assert detail["status"] == "open"


def test_filing_an_incident_mutates_no_work(world):
	work = make_work(world)["work_id"]
	launch(world)
	before = work_snapshot(world)
	file_incident(world, work=work, episode=4)
	assert work_snapshot(world) == before


# -- secret-safe rendering ---------------------------------------------------

def test_no_command_body_can_reach_the_record(world):
	"""What is stored is a CATEGORY and a short adapter-authored
	detail. The category is closed, so the one field that would
	otherwise be a natural place to paste a command cannot take one."""
	launch(world)
	with pytest.raises(WorkError):
		file_incident(world,
		              category="/bin/bash -lc 'baton --config x claim'")
	# `detail` is length-bounded prose like every other adapter-authored
	# field, and the schema has no column for a command, argv, an
	# environment or a payload at all.
	columns = {row["name"] for row in world["store"].conn.execute(
		"PRAGMA table_info(approval_incidents)")}
	for forbidden in ("command", "argv", "env", "environment", "payload",
	                  "credential", "token", "body"):
		assert forbidden not in columns
	with pytest.raises(WorkError, match="the limit is 400"):
		file_incident(world, detail="x" * 401)


def test_the_projection_exposes_no_unsafe_field(world):
	launch(world)
	file_incident(world, detail="a short safe explanation")
	row = pj.incidents(world["store"], viewer_team="lang",
	                   viewer_member="grace")["rows"][0]
	assert set(row) == {
		"incident", "participant", "incarnation", "adapter", "session",
		"action_owner", "mine", "cause", "category", "detail", "work",
		"episode", "action_key", "occurrences", "first_ts", "latest_ts",
		"open", "dismissed_ts", "dismissed_by", "dismissal_note"}


# -- retry ------------------------------------------------------------------

def test_an_exact_retry_replays_rather_than_filing_twice(world):
	launch(world)
	first = file_incident(world, op_id="deny-1")
	second = file_incident(world, op_id="deny-1")
	assert second["incident"] == first["incident"]
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 1
	# Without the identity it is a genuine second observation, and
	# coalescing — not the retry machinery — is what keeps it to one row.
	third = file_incident(world)
	assert third["coalesced"] is True
	assert third["occurrences"] == 2


def test_a_dismissal_retry_replays(world):
	launch(world)
	file_incident(world)
	first = tr.incident_dismiss(world["store"], actor_team="lang",
	                            actor="grace", incident=1,
	                            op_id="dismiss-1")
	second = tr.incident_dismiss(world["store"], actor_team="lang",
	                             actor="grace", incident=1,
	                             op_id="dismiss-1")
	assert first["incident"] == second["incident"] == 1


# -- the console surface -----------------------------------------------------

def test_the_inbox_cells_say_dismiss_and_never_approve():
	"""W228's ruling applied here: an actionable row must be legible
	without colour or weight, so `Do` is the action in WORDS."""
	from baton_work.tui.app import Console
	row = {"kind": "incident", "owed": True, "seen": False,
	       "selector": "I1", "work": "aaa-W415", "summary": "it failed",
	       "occurrences": 1}
	cells = Console._inbox_cells(row)
	assert cells["Do"] == "dismiss"
	assert cells["Type"] == "incident"
	# There is no approve on this surface, by ruling.
	assert "approve" not in " ".join(cells.values()).lower()


def test_the_inbox_detail_states_the_boundary(world):
	from baton_work.tui.app import Console
	work = make_work(world)["work_id"]
	launch(world)
	for _ in range(2):
		file_incident(world, work=work, episode=4)
	row = incident_rows(world)[0]
	console = Console.__new__(Console)
	text = " ".join(Console._inbox_detail(console, row, 78))
	# What an operator must be able to read without leaving the row.
	assert "lang.ada" in text and "baton-cli" in text
	assert "2 times" in text, text
	assert "not claimed" in text.lower() or "NOT claimed" in text
	assert "dismiss" in text
	assert "reroute" in text
	# The ruled absence.
	assert "approve" not in text.replace("no approve", "").lower()


def test_the_inbox_tab_carries_the_owed_marker(world):
	"""W167: `[Inbox*]` attracts attention while the incident is open,
	and stops when it is dismissed — not when anything is read."""
	launch(world)
	file_incident(world)
	assert inbox(world)["owed_action"] is True
	tr.incident_dismiss(world["store"], actor_team="lang", actor="grace",
	                    incident=1)
	assert inbox(world)["owed_action"] is False


# -- W415 review round 1: identity, staleness, and restart coalescing --------

def test_a_restart_increments_the_incident_rather_than_opening_a_rival(world):
	"""THE P2. The key used to include the incarnation, so a managed
	stack restart opened a SECOND incident for the same still-unclaimed
	episode. A problem that survives a restart is the same problem,
	harder — and the count is what says so."""
	work = make_work(world)["work_id"]
	launch(world, incarnation="run-1")
	file_incident(world, incarnation="run-1", work=work, episode=4)
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1")
	launch(world, incarnation="run-2", rationale="managed stack restarted")
	result = file_incident(world, incarnation="run-2", work=work, episode=4)

	assert result["coalesced"] is True
	assert result["occurrences"] == 2
	view = pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")
	assert view["open"] == 1
	# The incarnation and session advance to where it is happening now:
	# evidence, not identity.
	assert view["rows"][0]["incarnation"] == "run-2"


def test_a_superseded_runner_cannot_file_at_all(world):
	"""Every other runtime write gates the supplied incarnation. This one
	did not, so a replaced publisher could file with its stale
	incarnation while borrowing the live runner's adapter, session and
	owner — making the superseded runner authoritative over the one that
	replaced it."""
	launch(world, incarnation="run-1")
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1")
	launch(world, incarnation="run-2", rationale="replacement")
	with pytest.raises(WorkError):
		file_incident(world, incarnation="run-1")
	assert pj.incidents(world["store"], viewer_team="lang",
	                    viewer_member="grace")["open"] == 0
	# The live one files normally.
	assert file_incident(world, incarnation="run-2")["occurrences"] == 1


def test_a_runner_with_no_lease_at_all_cannot_file(world):
	with pytest.raises(WorkError):
		file_incident(world, incarnation="never-started")


def test_a_coalescing_report_moves_the_incident_to_the_current_owner(world):
	"""Review round 2 asked for an explicit ruling. The owner MOVES.

	`action_owner` is a configuration fact about who answers for this
	runner. If a redeployment changed it, an incident still owed to the
	former participant is owed to nobody who can act — the exact
	invisibility this Work exists to remove."""
	launch(world, incarnation="run-1", owner="lang.grace")
	file_incident(world, incarnation="run-1")
	assert len(incident_rows(world, "grace")) == 1

	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1")
	launch(world, incarnation="run-2", owner="lang.ada",
	       rationale="redeployed with a different action owner")
	result = file_incident(world, incarnation="run-2")

	assert result["coalesced"] is True
	assert result["action_owner"] == "lang.ada"
	# One incident, now owed to whoever currently answers for the runner.
	assert incident_rows(world, "grace") == []
	assert len(incident_rows(world, "ada")) == 1
	assert inbox(world, "ada")["owed_action"] is True
	assert inbox(world, "grace")["owed_action"] is False
