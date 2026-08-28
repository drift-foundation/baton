"""W2938: claim pickup is a PARTICIPANT obligation, not a Work property.

`work/records/2026/08/finding-claim-overdue-cue/`. W2780 was passed to
`baton.codex` and became ready, unclaimed Work. The authority projected
the handoff correctly and the readiness bridge forwarded the episode,
but the reviewer did not act, and nothing said so.

The first implementation put a `Claim` cue on the Job and was rejected
for it: a Job is queued and unclaimed, and is not the entity that owes
a claim. The AGENT with free capacity owes pickup. Showing it per-Job
would turn one idle participant into N duplicate overdue rows and pin a
member-level failure onto Work records.

So the ruled model is one obligation per participant:

- one-slot capacity — a participant holds exactly ONE active claim, and
  a second is refused. Without a defined capacity unit "free capacity"
  is unanswerable and the cue would be dishonest;
- one interval — an idle participant with a nonempty actionable pool
  owes exactly one pickup, however deep the queue;
- canonical — the interval start is stored, so it survives a client or
  runner restart, and `pending`/`overdue` is derived at READ time with
  no timeout event and no workflow mutation;
- and the persistent signal on Jobs is `[Teams*]`, never a Work row.
"""

from __future__ import annotations

import curses
import json as _json
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import lifecycle as lc                         # noqa: E402
from baton_work import projection as pj                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
from baton_work.authority import PICKUP_OVERDUE_DEFAULT        # noqa: E402
from baton_work.tui import app                                 # noqa: E402
from baton_work.tui.app import Console                         # noqa: E402
import fixtures as fx                                          # noqa: E402


def build(directory, members=("ada", "bee"), threshold=None):
	document = fx.crew_document("lang", list(members), kinds=("bug", "rev"))
	if threshold is not None:
		document["instance"]["pickup_overdue_seconds"] = threshold
	config_path = os.path.join(directory, "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	return config_path, database


@pytest.fixture()
def world(tmp_path):
	config_path, database = build(str(tmp_path))
	store = bw.Authority(database)
	yield {"config": config_path, "database": database, "store": store}
	store.close()


def make(world, title="actionable"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")["work_id"]


def pickup(world, member="ada", threshold=None):
	store = world["store"]
	return pj.member_pickup(
		store, "lang", member, store.clock(),
		pj.pickup_threshold(store) if threshold is None else threshold)


def intervals(world):
	"""The canonical open intervals, by participant."""
	return {row["member"] for row in world["store"].conn.execute(
		"SELECT member FROM member_pickup WHERE team='lang'")}


# -- one-slot capacity, which makes free capacity knowable -------------------

def test_a_participant_holds_one_claim_at_a_time(world):
	"""The capacity unit the ruling requires before anything else. It is
	not a presentation rule: without it, "at least one eligible member
	has free capacity" cannot be answered."""
	first, second = make(world, "first"), make(world, "second")
	tr.claim_work(world["store"], first, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="ONE active claim"):
		tr.claim_work(world["store"], second, actor_team="lang",
		              actor="ada")


def test_the_refusal_names_the_work_already_held_and_the_ways_out(world):
	first, second = make(world, "first"), make(world, "second")
	tr.claim_work(world["store"], first, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError) as refused:
		tr.claim_work(world["store"], second, actor_team="lang",
		              actor="ada")
	message = str(refused.value)
	assert first in message, message
	for way in ("finish", "pass", "release"):
		assert way in message, message


def test_the_slot_frees_on_every_releasing_transition(world):
	"""Finish it, hand it on, or let it go — each frees the slot."""
	store = world["store"]
	for release in ("close", "pass", "release"):
		work = make(world, release)
		tr.claim_work(store, work, actor_team="lang", actor="ada")
		if release == "close":
			tr.close_work(store, work, actor_team="lang", actor="ada",
			              rationale="done", outcome="satisfying")
		elif release == "pass":
			tr.pass_work(store, work, actor_team="lang", actor="ada",
			             to="lang.rev", comment="over")
		else:
			tr.release_claim(store, work, actor_team="lang", actor="ada",
			                 expect="lang.ada", episode=fx.episode_of(store, work),
			                 reason="letting go")
		another = make(world, f"after {release}")
		tr.claim_work(store, another, actor_team="lang", actor="ada")
		tr.release_claim(store, another, actor_team="lang", actor="ada",
		                 expect="lang.ada", episode=fx.episode_of(store, another),
		                 reason="cycling")


def test_a_second_participant_is_unaffected(world):
	"""The slot is per participant, not per route."""
	first, second = make(world, "first"), make(world, "second")
	tr.claim_work(world["store"], first, actor_team="lang", actor="ada")
	tr.claim_work(world["store"], second, actor_team="lang", actor="bee")


# -- one obligation per participant ------------------------------------------

def test_an_idle_participant_with_no_work_owes_nothing(world):
	assert intervals(world) == set()
	assert pickup(world)["state"] is None


def test_ten_jobs_make_one_obligation_not_ten(world):
	"""The ruling's headline, and the reason the cue is not on Jobs."""
	for index in range(10):
		make(world, f"job {index}")
	assert intervals(world) == {"ada", "bee"}
	assert pickup(world)["state"] == "pending"
	assert world["store"].conn.execute(
		"SELECT COUNT(*) AS n FROM member_pickup "
		"WHERE team='lang' AND member='ada'").fetchone()["n"] == 1


def test_the_interval_does_not_reset_while_the_pool_stays_nonempty(world):
	"""Adding, removing, reprioritizing or reordering Work while the
	pool remains continuously nonempty neither multiplies nor resets
	it — including a competing handler claiming one offered Work."""
	first = make(world, "first")
	started = world["store"].conn.execute(
		"SELECT started_seq FROM member_pickup WHERE member='ada'"
	).fetchone()["started_seq"]
	make(world, "second")
	tr.prioritize(world["store"], first, actor_team="lang", actor="ada",
	              priority="high")
	tr.claim_work(world["store"], first, actor_team="lang", actor="bee")
	after = world["store"].conn.execute(
		"SELECT started_seq FROM member_pickup WHERE member='ada'"
	).fetchone()["started_seq"]
	assert after == started, \
		"the interval restarted while the actionable pool never emptied"


def test_a_busy_participant_owes_no_pickup(world):
	work = make(world)
	make(world, "another")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert "ada" not in intervals(world)
	assert pickup(world)["state"] is None
	assert pickup(world, "bee")["state"] == "pending", \
		"one member going busy cleared another member's obligation"


def test_claiming_any_eligible_job_clears_the_one_obligation(world):
	"""Not the 'right' Job — ANY of them. The obligation is to start
	work, and the remaining queue is ordinary backlog."""
	make(world, "first")
	second = make(world, "second")
	make(world, "third")
	tr.claim_work(world["store"], second, actor_team="lang", actor="ada")
	assert pickup(world)["state"] is None


def test_becoming_idle_again_starts_a_new_interval(world):
	"""Elapsed time from the earlier busy period never resumes."""
	work = make(world)
	make(world, "still waiting to be taken")
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.release_claim(world["store"], work, actor_team="lang", actor="ada",
	                 expect="lang.ada",
	                 episode=fx.episode_of(world["store"], work),
	                 reason="handing back")
	fresh = pickup(world)
	assert fresh["state"] == "pending"
	assert fresh["elapsed_seconds"] == 0, \
		"the new interval resumed the old elapsed time"


def test_an_emptied_pool_clears_the_obligation(world):
	work = make(world)
	assert "ada" in intervals(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="bee")
	assert intervals(world) == set(), \
		"a member with nothing actionable still owed a pickup"


# -- what is NOT in the actionable pool --------------------------------------

@pytest.mark.parametrize("state", ["block", "parked"])
def test_unclaimable_work_is_not_an_actionable_pool(world, state):
	"""A pool the participant could not claim from is not a missed
	pickup — the same honesty the Work-level cue needed, at the level
	the obligation actually lives."""
	work = make(world)
	if state == "block":
		tr.add_dependency(world["store"], work, make(world, "the gate"),
		                  actor_team="lang", actor="ada",
		                  rationale="waits on it")
		# the gate row itself is actionable, so remove it from the pool
		tr.claim_work(world["store"], world["store"].conn.execute(
			"SELECT id FROM work WHERE title='the gate'"
		).fetchone()["id"], actor_team="lang", actor="bee")
	else:
		tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
		             phase="parked", reason="deferred")
	assert "ada" not in intervals(world), state


def test_terminal_work_is_not_an_actionable_pool(world):
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              rationale="done", outcome="satisfying")
	assert intervals(world) == set()


def test_losing_route_eligibility_clears_the_obligation(tmp_path):
	"""Configured eligibility decides it, so a regeneration that takes
	the route away takes the obligation with it."""
	config_path, database = build(str(tmp_path))
	store = bw.Authority(database)
	try:
		tr.create_work(store, team="lang", kind="bug", title="offered",
		               origin="external-report",
		               classification="suspected-defect",
		               author="ada", body="b")
		assert {row["member"] for row in store.conn.execute(
			"SELECT member FROM member_pickup")} == {"ada", "bee"}
	finally:
		store.close()
	document = _json.loads(open(config_path, encoding="utf-8").read())
	document["teams"]["lang"]["routes"]["main"]["handlers"] = ["ada"]
	document["generation"] = 2
	open(config_path, "w", encoding="utf-8").write(_json.dumps(document))
	lc.accept_config(config_path, actor="lang.ada")
	store = bw.Authority(database)
	try:
		assert {row["member"] for row in store.conn.execute(
			"SELECT member FROM member_pickup")} == {"ada"}, \
			"a member the route no longer reaches still owed a pickup"
	finally:
		store.close()


# -- the shared route races through the atomic claim -------------------------

def test_every_idle_eligible_member_evaluates_its_own_interval(world):
	make(world, "one offered Work")
	assert intervals(world) == {"ada", "bee"}
	assert pickup(world, "ada")["state"] == "pending"
	assert pickup(world, "bee")["state"] == "pending"


def test_the_winner_of_the_race_removes_it_from_the_others_pool(world):
	"""The cue never bypasses the atomic claim: after one member wins,
	every other member's pool and cue are recomputed from canonical
	state."""
	work = make(world, "one offered Work")
	tr.claim_work(world["store"], work, actor_team="lang", actor="bee")
	assert pickup(world, "bee")["state"] is None, "the winner is busy"
	assert pickup(world, "ada")["state"] is None, \
		"the loser still owed a pickup for Work somebody else took"


# -- pending versus overdue, and the accepted threshold ----------------------

def test_the_default_threshold_is_the_documented_one(world):
	assert PICKUP_OVERDUE_DEFAULT == 360
	assert pj.pickup_threshold(world["store"]) == 360


def test_inside_the_threshold_is_pending_and_beyond_it_is_overdue(world):
	make(world)
	assert pickup(world, threshold=10_000)["state"] == "pending"
	assert pickup(world, threshold=0)["state"] == "overdue"


def test_a_deployment_may_configure_the_threshold(tmp_path):
	config_path, database = build(str(tmp_path), threshold=1)
	store = bw.Authority(database)
	try:
		assert pj.pickup_threshold(store) == 1
		tr.create_work(store, team="lang", kind="bug", title="offered",
		               origin="external-report",
		               classification="suspected-defect",
		               author="ada", body="b")
		time.sleep(1.2)
		state = pj.member_pickup(store, "lang", "ada", store.clock(), 1)
		assert state["state"] == "overdue"
		assert state["elapsed_seconds"] >= 1
	finally:
		store.close()


def test_a_non_positive_threshold_refuses_at_acceptance(tmp_path):
	"""Zero or negative would make every idle participant permanently
	overdue, so it refuses where every other configuration error does."""
	for bad in (0, -1):
		directory = tmp_path / f"bad{bad}"
		directory.mkdir()
		document = fx.crew_document("lang", ["ada"])
		document["instance"]["pickup_overdue_seconds"] = bad
		path = str(directory / "baton.json")
		open(path, "w", encoding="utf-8").write(_json.dumps(document))
		with pytest.raises(bw.WorkError, match="POSITIVE"):
			lc.init_from_config(path, participant="lang.ada")


def test_a_missing_accepted_threshold_fails_closed(world):
	"""Review P2: every acceptance stores a validated positive value,
	including the 360-second default when the document omits it. So a
	missing one does not mean "nobody chose" — it means the meta table
	is invalid, and a reader that quietly substituted the compiled
	default would INVENT policy in the one place the contract says the
	accepted value is the only source of truth."""
	world["store"].conn.execute(
		"DELETE FROM meta WHERE key='pickup_overdue_seconds'")
	with pytest.raises(bw.WorkError, match="no accepted pickup threshold"):
		pj.pickup_threshold(world["store"])
	with pytest.raises(bw.WorkError):
		pj.teams(world["store"], viewer_team="lang", viewer_member="ada")


@pytest.mark.parametrize("corrupt", ["0", "-5", "", "later", "3.5"])
def test_an_invalid_accepted_threshold_fails_closed(world, corrupt):
	"""The same rule for a value acceptance could never have written."""
	world["store"].conn.execute(
		"UPDATE meta SET value=? WHERE key='pickup_overdue_seconds'",
		(corrupt,))
	with pytest.raises(bw.WorkError, match="acceptance validates it"):
		pj.pickup_threshold(world["store"])


def test_the_default_still_lives_at_acceptance(tmp_path):
	"""Failing closed at READ must not remove the legitimate omission:
	a document that says nothing still accepts 360."""
	config_path, database = build(str(tmp_path))
	document = _json.loads(open(config_path, encoding="utf-8").read())
	assert "pickup_overdue_seconds" not in document["instance"]
	store = bw.Authority(database)
	try:
		assert store.meta()["pickup_overdue_seconds"] == "360"
		assert pj.pickup_threshold(store) == 360
	finally:
		store.close()


def test_the_roster_reads_one_policy_per_snapshot(world, monkeypatch):
	"""Review P1: the published policy and every member state are ONE
	snapshot. Reading the threshold before the roster and again for the
	response let a concurrent acceptance publish states derived with one
	value beside a response announcing another."""
	make(world)
	reads = []

	real = pj.pickup_threshold

	def counted(store):
		reads.append(None)
		return real(store)

	monkeypatch.setattr(pj, "pickup_threshold", counted)
	result = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	assert len(reads) == 1, \
		"one roster response read the accepted policy twice"
	assert result["pickup_overdue_seconds"] == 360


def test_reading_an_overdue_member_mutates_nothing(world):
	"""Passage of time derives the state; it performs no timeout event
	and no workflow mutation."""
	make(world)
	before = world["store"].last_seq()
	assert pickup(world, threshold=0)["state"] == "overdue"
	assert world["store"].last_seq() == before


def test_the_interval_survives_reopening_the_authority(world):
	"""Canonical, not a client timer: a runner restart does not reset
	somebody's pickup clock."""
	make(world)
	started = world["store"].conn.execute(
		"SELECT started_at FROM member_pickup WHERE member='ada'"
	).fetchone()["started_at"]
	world["store"].close()
	world["store"] = bw.Authority(world["database"])
	assert world["store"].conn.execute(
		"SELECT started_at FROM member_pickup WHERE member='ada'"
	).fetchone()["started_at"] == started


# -- the JSON contract -------------------------------------------------------

def test_the_roster_publishes_the_state_and_the_accepted_policy(world):
	"""Clients read structured fields and never TUI wording, so the
	value they compare against rides the same read."""
	make(world)
	roster = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	assert roster["pickup_overdue_seconds"] == 360
	member = next(entry for team in roster["teams"]
	              for entry in team["members"]
	              if entry["member"] == "ada")
	assert member["pickup"]["state"] == "pending"
	assert member["pickup"]["since"] is not None
	assert member["pickup"]["elapsed_seconds"] >= 0
	assert member["pickup"]["next_work"]["title"] == "actionable"


def test_the_suggested_work_is_diagnostic_and_not_an_owner(world):
	"""It names the canonical FIRST actionable Work as a next claim.
	The obligation is the participant's: claiming any eligible Work
	clears it, and the remaining queue is not overdue."""
	first = make(world, "first")
	make(world, "second")
	assert pickup(world)["next_work"]["work"] == first
	tr.claim_work(world["store"], first, actor_team="lang", actor="bee")
	assert pickup(world)["next_work"]["title"] == "second", \
		"the suggestion did not follow the pool"


# -- the console -------------------------------------------------------------

class Screen:
	def __init__(self, height=24, width=110):
		self.height = height
		self.width = width
		self.rows = {}
		self.calls = []

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}
		self.calls = []

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "").ljust(x)
		text = str(text)[:n]
		self.rows[y] = row[:x] + text + row[x + len(text):]
		self.calls.append((str(text), rest[0] if rest else 0))

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def console(world, member="ada"):
	store = bw.Authority(world["database"])
	view = Console(store, "lang", member, config_path=world["config"])
	while view.tab != "teams":
		view.handle(ord("]"))
	return view


def test_the_teams_table_carries_a_pickup_column(world):
	make(world)
	view = console(world)
	screen = Screen()
	view.render(screen)
	header = next(line for line in screen.lines() if "Participant" in line)
	assert "Pickup" in header, header
	row = next(line for line in screen.lines()
	           if line.startswith("lang.ada "))
	assert "pend" in row, row
	view.store.close()


def test_an_overdue_member_row_is_bold_and_stars_the_tab(tmp_path):
	"""The star sends the operator to Teams; the bold row is how they
	find who, without reading every Pickup cell."""
	config_path, database = build(str(tmp_path), threshold=1)
	store = bw.Authority(database)
	tr.create_work(store, team="lang", kind="bug", title="offered",
	               origin="external-report",
	               classification="suspected-defect", author="ada",
	               body="b")
	time.sleep(1.2)
	try:
		view = Console(store, "lang", "ada", config_path=config_path)
		while view.tab != "teams":
			view.handle(ord("]"))
		assert view.teams_need_attention()
		assert "[Teams *]" in view.top_tabs(), view.top_tabs()
		screen = Screen()
		view.render(screen)
		bold = {text.strip() for text, attr in screen.calls
		        if attr & curses.A_BOLD}
		assert any(text.startswith("lang.bee") for text in bold), bold
		row = next(line for line in screen.lines()
		           if line.startswith("lang.ada "))
		assert "late" in row, row
	finally:
		store.close()


def test_pending_alone_never_stars_the_tab(world):
	"""'Pending alone does not add the star.' A grace period nobody has
	missed yet is not attention."""
	make(world)
	view = console(world)
	assert not view.teams_need_attention()
	assert "[Teams]" in view.top_tabs(), view.top_tabs()
	view.store.close()


def test_no_participant_owing_anything_stars_nothing(world):
	view = console(world)
	assert "[Teams]" in view.top_tabs()
	view.store.close()


def test_member_detail_spells_the_obligation_out(world):
	make(world, "the suggested one")
	view = console(world)
	rows = view.team_rows()
	block = "\n".join(view._team_detail(
		next(row for row in rows if row["member"] == "ada"), 110))
	assert "Claim pickup" in block, block
	assert "pending" in block
	assert "Suggested next claim" in block
	assert "the suggested one" in block
	view.store.close()


def test_member_detail_says_nothing_when_nothing_is_owed(world):
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	view = console(world)
	rows = view.team_rows()
	block = "\n".join(view._team_detail(
		next(row for row in rows if row["member"] == "ada"), 110))
	assert "Claim pickup" not in block, \
		"a busy member grew an empty pickup section"
	view.store.close()


def test_no_job_row_or_work_detail_carries_the_cue(world):
	"""The ownership supersession, asserted where it was broken: the
	obligation never annotates a Work."""
	make(world)
	store = bw.Authority(world["database"])
	try:
		view = Console(store, "lang", "ada", config_path=world["config"])
		screen = Screen()
		view.render(screen)
		painted = "\n".join(screen.lines())
		header = next(line for line in screen.lines() if "Title" in line)
		for absent in ("Claim", "Pickup", "New"):
			assert absent not in header, header
		assert "pend" not in painted and "overdue" not in painted
		detail = pj.detail(store, view.rows()[0]["id"], viewer_team="lang",
		                   viewer_member="ada")
		assert "claim " not in view._detail_header(detail)
	finally:
		store.close()


# -- widths ------------------------------------------------------------------

def test_pickup_outlives_every_column_but_state_and_identity():
	order = list(app.TEAM_DROP_ORDER)
	for lower in ("Session", "Role", "Since", "Work", "Agent"):
		assert order.index(lower) < order.index("Pickup"), lower


@pytest.mark.parametrize("width", [140, 110, 90, 70, 50])
def test_the_pickup_cell_is_drawn_whole_or_not_at_all(world, width):
	make(world)
	view = console(world)
	screen = Screen(width=width)
	view.render(screen)
	for line in screen.lines():
		if line.startswith("lang.ada "):
			assert "pen" not in line or "pend" in line, (width, line)
	view.store.close()


# -- the deployed product ----------------------------------------------------

@pytest.mark.serial
def test_the_packaged_console_shows_the_participant_cue(tmp_path_factory):
	"""What an operator launches, on a real terminal."""
	import pty as _pty
	if not hasattr(_pty, "fork"):
		pytest.skip("no pty support")
	import ptyharness
	repo = os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__))))
	target = os.path.join(str(tmp_path_factory.mktemp("w2938dist")),
	                      "baton-r1")
	done = subprocess.run(
		[sys.executable, os.path.join(repo, "tools", "deploy_work.py"),
		 target], capture_output=True, text=True, timeout=180)
	assert done.returncode == 0, done.stderr
	executable = _json.loads(done.stdout)["executable"]
	env = {key: value for key, value in os.environ.items()
	       if key != "PYTHONPATH"}
	home = str(tmp_path_factory.mktemp("w2938home"))
	run = subprocess.run([executable, "init", f"directory={home}"],
	                     capture_output=True, text=True, timeout=120,
	                     env=env)
	assert run.returncode == 0, run.stderr
	config_path = os.path.join(home, "baton.json")
	document = _json.loads(open(config_path, encoding="utf-8").read())
	crew = fx.crew_document("lang", ["ada", "bee"])
	document["teams"] = crew["teams"]
	document["instance"]["pickup_overdue_seconds"] = 1
	open(config_path, "w", encoding="utf-8").write(
		_json.dumps(document, indent=2, sort_keys=True))
	run = subprocess.run([executable, "--participant", "lang.ada",
	                      "activate", f"directory={home}"],
	                     capture_output=True, text=True, timeout=120,
	                     env=env)
	assert run.returncode == 0, run.stderr
	run = subprocess.run(
		[executable, "--config", config_path, "--participant", "lang.ada",
		 "create", "team=lang", "kind=bug", "title=nobody took it",
		 "origin=external-report", "classification=suspected-defect",
		 "body=b"], capture_output=True, text=True, timeout=120, env=env)
	assert run.returncode == 0, run.stderr
	time.sleep(1.2)
	text, status, steps = ptyharness.drive(
		config_path, "lang.ada",
		[(b"", 0.7), (b"]", 0.7), (b"qy", 0.4)],
		columns=120, lines=20, command=[sys.executable, executable])
	jobs, teams = (ptyharness.replay(step, columns=120, lines=20)
	               for step in steps[:2])   # settle on Jobs, then `]`
	# W26328: the Jobs label carries the actionable count. The
	# subject here is the `*` on Teams, which is unchanged — a count
	# on a NEIGHBOURING label is not the pickup cue multiplying.
	assert jobs[0].startswith("[Jobs 1]  [Teams *]"), jobs[0]
	assert any("Title" in line for line in jobs), jobs[:6]
	# The TABLE, not the footer — `c claim` is the key hint and has
	# always been there. What must not appear is a column or a cell.
	header = next(line for line in jobs if "Title" in line)
	for absent in ("Claim", "Pickup", "New"):
		assert absent not in header, header
	assert not any(word in line for line in jobs
	               if line.startswith("W")
	               for word in ("pend", "late", "overdue")), jobs[:8]
	assert any("Pickup" in line for line in teams), teams[:6]
	assert any(line.startswith("lang.ada") and "late" in line
	           for line in teams), teams[:8]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, text[-400:]
