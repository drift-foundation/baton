"""W93 slice 7: the end-to-end scenario matrix.

`work/records/2026/08/finding-agent-runtime-state/`. Slices 3-6 built
the lease, the adapters that publish onto it, the Jobs/Teams/Inbox
rendering and the safe operational inventory, and each was tested at
its own seam. This file is the finding's ACCEPTANCE list walked whole:
one scenario per named situation, from the adapter's report to what an
operator actually sees, so a regression that only shows up when the
pieces are composed has somewhere to fail.

The list is the finding's, verbatim in intent: approval wait and
recovery, slow silent work, disconnect and reconnect, stale-runner
replacement, provider rate limiting, no Handler, a terminal Work whose
former runner is still alive, stale diagnostic data, and a launcher
configuration that carries secrets.

What every scenario holds in common, because it is the finding's first
decision: none of this is workflow authority. The Work table is
snapshotted around each one and must come back unchanged.
"""

from __future__ import annotations

NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import projection as pj                         # noqa: E402
from baton_work import transitions as tr                        # noqa: E402
from baton_work import cli as _cli                              # noqa: E402
from baton_work.tui.app import Console, agent_cell              # noqa: E402
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


def at(instant):
	os.environ["BATON_WORK_NOW"] = instant


def held(world, member="ada", title="the held work"):
	born = tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor=member)
	return born["work_id"]


def start(world, member="ada", incarnation="run-1", adapter="codex",
          **extra):
	return tr.runtime_start(world["store"], actor_team="lang",
	                        actor=member, incarnation=incarnation,
	                        adapter=adapter, **extra)


def report(world, member="ada", incarnation="run-1", state="working",
           **extra):
	return tr.runtime_state(world["store"], actor_team="lang",
	                        actor=member, incarnation=incarnation,
	                        state=state, **extra)


def runtime(world, member="ada"):
	view = pj.runtime(world["store"], viewer_team="lang",
	                  viewer_member=member)
	return {row["participant"]: row for row in view["participants"]}


def jobs_cell(world, work, viewer="ada"):
	"""What the Jobs `Agent` column paints for this Work."""
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member=viewer)["rows"] if entry["id"] == work)
	return agent_cell(row["agent"])


def inbox_runtime(world, viewer):
	return [row for row in pj.inbox(
		world["store"], viewer_team="lang",
		viewer_member=viewer)["rows"] if row["kind"] == "runtime"]


def work_rows(world):
	return [dict(row) for row in
	        world["store"].conn.execute(
		        "SELECT * FROM work ORDER BY id")]


class _Screen:
	"""The same fake the slice-5 TUI tests paint onto: `addnstr` is the
	one call the Console makes."""

	def __init__(self, height=26, width=150):
		self.rows = {}
		self.height = height
		self.width = width

	def getmaxyx(self):
		return self.height, self.width

	def erase(self):
		self.rows = {}

	def refresh(self):
		pass

	def move(self, *_args):
		pass

	def addnstr(self, y, x, text, n, *rest):
		row = self.rows.get(y, "")
		text = str(text)[:n]
		row = row.ljust(x)
		self.rows[y] = row[:x] + text + row[x + len(text):]

	def lines(self):
		return [self.rows.get(key, "")
		        for key in range(max(self.rows) + 1)] if self.rows else []


def painted(world, member="ada", tab=None, height=40):
	# W184 made Teams member detail a key/value table, which is taller
	# than the prose block it replaced. These scenarios read its lower
	# sections, so they paint a screen tall enough to hold it — the
	# short-terminal behaviour is W184's own test's subject.
	view = Console(world["store"], "lang", member,
	               config_path=world["config"])
	while tab is not None and view.tab != tab:
		view.handle(NEXT_TAB)
	screen = _Screen(height=height)
	view.render(screen)
	return screen.lines()


@pytest.fixture(autouse=True)
def _work_table_is_never_touched(world):
	"""Decision 1, enforced around every scenario in this file rather
	than remembered in each: runtime state never moves workflow."""
	yield
	before = world.get("_work_before")
	if before is not None:
		assert work_rows(world) == before, \
			"a runtime scenario changed the Work table"


def freeze_work(world):
	world["_work_before"] = work_rows(world)


# -- 1. approval wait and recovery -------------------------------------------

def test_an_approval_wait_is_visible_and_recovers(world):
	"""THE motivating incident, walked whole.

	W22 was `active` with a Handler while its turn sat on a command
	approval, and the only evidence was a dispatcher log line. Every
	step below is what an operator now sees without opening one — and
	the recovery is part of the scenario, because a surface that lights
	up and never goes out is its own kind of lie.
	"""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world, session="01a01552-9d3e-77bb-a2c1",
	      action_owner="lang.grace")
	report(world, state="working", work=work)
	freeze_work(world)
	assert jobs_cell(world, work) == "work"
	assert inbox_runtime(world, "grace") == []

	# the turn hits an approval prompt
	at("2026-08-19T10:02:00Z")
	report(world, state="waiting-input", cause="approval",
	       detail="command approval required", work=work)
	assert jobs_cell(world, work) == "input"
	owed = inbox_runtime(world, "grace")
	assert len(owed) == 1 and owed[0]["owed"] is True
	assert owed[0]["selector"] == "lang.ada"
	# Baton did not answer it, and says so where the operator reads it
	assert any("waiting-input" in line for line in
	           painted(world, tab="teams"))

	# the operator approves in the provider's own UI; the adapter
	# observes the turn resume. No Work message, no claim, no baton.
	at("2026-08-19T10:03:00Z")
	report(world, state="working", work=work)
	assert jobs_cell(world, work) == "work"
	assert inbox_runtime(world, "grace") == [], \
		"the answered request stayed in the owner's Inbox"
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "working" and live["cause"] is None
	# and the whole sequence survives in the journal, which is the
	# other half of the incident: the operator could not reconstruct it
	history = pj.runtime_history(world["store"],
	                             participant="lang.ada")["rows"]
	assert [entry["state"] for entry in history] == \
		["idle", "working", "waiting-input", "working"]


# -- 2. slow silent work ------------------------------------------------------

def test_a_long_turn_that_says_nothing_new_stays_working(world):
	"""A turn can run for an hour without a single transition. The
	lease renewal is what keeps it honest — and a renewal is contact,
	not a new state, so `Since` still answers "how long has it been
	working" rather than "how long since it last spoke"."""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world)
	report(world, state="working", work=work)
	freeze_work(world)
	entered = runtime(world)["lang.ada"]["runtime"]["since"]

	for minute in ("10:04", "10:08", "10:12"):
		at(f"2026-08-19T{minute}:00Z")
		report(world, state="working", work=work)

	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "working", "a quiet turn was reclassified"
	assert live["provenance"] == "reported"
	assert live["since"] == entered, \
		"a renewal restarted the state clock"
	assert live["last_contact"] == "2026-08-19T10:12:00Z"
	assert jobs_cell(world, work) == "work"


def test_a_runner_that_stops_renewing_becomes_unknown_not_stuck(world):
	"""Decision 4's boundary. Silence past the deadline is `unknown`,
	derived, dated from the deadline — never `failed`, never `stuck`,
	and never a guess about why."""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world)
	report(world, state="working", work=work)
	freeze_work(world)
	at("2026-08-19T10:06:00Z")
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "unknown"
	assert live["provenance"] == "derived"
	assert live["since"] == live["expires_at"], \
		"the derived state is dated from the deadline it crossed"
	assert live["cause"] is None, "silence was diagnosed"
	assert jobs_cell(world, work) == "unkn"


# -- 3. disconnect and reconnect ---------------------------------------------

def test_a_transport_drop_reads_as_retrying_and_then_recovers(world):
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world)
	report(world, state="working", work=work)
	freeze_work(world)
	at("2026-08-19T10:01:00Z")
	report(world, state="retrying", cause="transport",
	       detail="the dispatcher lost its Codex connection", work=work)
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "retrying" and live["cause"] == "transport"
	assert jobs_cell(world, work) == "retry"
	# a reconnecting runner is not an operator's problem to answer
	assert inbox_runtime(world, "grace") == []
	assert inbox_runtime(world, "ada") == []
	at("2026-08-19T10:01:30Z")
	report(world, state="working", work=work)
	assert jobs_cell(world, work) == "work"


# -- 4. stale-runner replacement ---------------------------------------------

def test_a_replaced_runner_cannot_repaint_the_screen(world):
	"""Decision 6. The old process may still be alive and still be
	publishing; its writes fail closed rather than restoring a state
	its replacement has moved past."""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world, incarnation="run-1")
	report(world, incarnation="run-1", state="working", work=work)
	freeze_work(world)
	at("2026-08-19T10:05:00Z")
	start(world, incarnation="run-2",
	      rationale="the dispatcher restarted after a crash")
	report(world, incarnation="run-2", state="idle")
	with pytest.raises(bw.WorkError, match="superseded"):
		report(world, incarnation="run-1", state="working", work=work)
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["incarnation"] == "run-2" and live["state"] == "idle"
	assert jobs_cell(world, work) == "idle"
	# both launches survive in the journal, and the replacement says why
	history = pj.runtime_history(world["store"],
	                             participant="lang.ada")["rows"]
	assert {entry["incarnation"] for entry in history} == {"run-1", "run-2"}
	assert any("restarted after a crash" in (entry["detail"] or "")
	           for entry in history)


# -- 5. provider rate limiting -----------------------------------------------

def test_a_rate_limit_is_retrying_with_a_reset_an_operator_can_read(world):
	"""A throttled runner is not a broken one. The category is `limit`,
	the reset instant is an inventory fact rather than a state field,
	and nobody is asked to do anything about it."""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world, action_owner="lang.grace")
	report(world, state="working", work=work)
	freeze_work(world)
	at("2026-08-19T10:01:00Z")
	report(world, state="retrying", cause="limit",
	       detail="provider rate limit; retrying", work=work)
	tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", source="reported",
	                 facts={"retry-at": "2026-08-19T10:06:00Z"})
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "retrying" and live["cause"] == "limit"
	assert jobs_cell(world, work) == "retry"
	held_facts = {entry["key"]: entry for entry in live["facts"]}
	assert held_facts["retry-at"]["value"] == "2026-08-19T10:06:00Z"
	# `limit` is not actionable by a human: nothing lands in an Inbox
	assert inbox_runtime(world, "grace") == []


# -- 6. no Handler ------------------------------------------------------------

def test_unclaimed_work_reports_no_runner_at_all(world):
	"""`-` is "nobody is executing this", which is a different fact
	from "somebody is, and their runner is dark"."""
	born = tr.create_work(world["store"], team="lang", kind="bug",
	                      title="nobody's yet", origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="b")
	work = born["work_id"]
	# a live runner exists — it simply holds nothing
	start(world)
	report(world, state="idle")
	freeze_work(world)
	assert jobs_cell(world, work) == "-"
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["agent"] is None
	# and the runner is still visible where runners are listed
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "idle"


# -- 7. a terminal Work whose former runner is still alive --------------------

def test_closing_the_work_leaves_its_runner_running(world):
	"""Decision 7 from the other side: workflow does not command the
	runtime either. A closed Work does not end a lease, and a runner
	that is still up is still reported."""
	at("2026-08-19T10:00:00Z")
	work = held(world)
	start(world, session="01a01552-9d3e")
	report(world, state="working", work=work)
	tr.close_work(world["store"], work, actor_team="lang", actor="ada",
	              outcome="satisfying", rationale="done and verified")
	freeze_work(world)
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["state"] == "working", "closing Work ended a lease"
	assert live["work"] == work, \
		"the runner's own correlation is its report, not the Work's"
	# the Work is terminal, so it has no Agent cell to paint
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["agent"] is None
	# the disagreement is SHOWN rather than reconciled by a write
	assert row["handler"] is None
	assert any("lang.ada" in line for line in painted(world, tab="teams"))


# -- 8. stale diagnostic data -------------------------------------------------

def test_an_old_fact_reads_as_old_rather_than_as_live(world):
	"""Decision 10's last line. A last-known answer is never presented
	as live: every fact carries where it came from and how old it is,
	and the answer to "is this still true" is the operator's."""
	at("2026-08-19T10:00:00Z")
	start(world)
	tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", source="configured",
	                 facts={"workdir": "/home/op/src/baton",
	                        "version": "codex-event-bridge 1.4.0"})
	freeze_work(world)
	at("2026-08-19T10:30:00Z")
	report(world, state="working")
	live = runtime(world)["lang.ada"]["runtime"]
	inventory = {entry["key"]: entry for entry in live["facts"]}
	assert inventory["workdir"]["source"] == "configured"
	assert inventory["workdir"]["observed_at"] == "2026-08-19T10:00:00Z"
	assert inventory["workdir"]["age_seconds"] == 1800
	# the STATE is fresh and the FACTS are half an hour old; a single
	# freshness for the member would have hidden exactly that
	assert live["provenance"] == "reported"
	assert live["last_contact"] == "2026-08-19T10:30:00Z"
	detail = painted(world, tab="teams")
	assert any("/home/op/src/baton" in line for line in detail), detail
	assert any("configured" in line for line in detail), detail


def test_a_refresh_says_it_was_asked_until_the_adapter_answers(world):
	"""The other half of freshness: an operator can tell "nobody has
	asked for newer facts" from "somebody asked and the adapter has not
	answered yet"."""
	at("2026-08-19T10:00:00Z")
	start(world)
	tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", source="configured",
	                 facts={"version": "1.4.0"})
	freeze_work(world)
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"] \
		is None
	at("2026-08-19T10:30:00Z")
	asked = tr.runtime_refresh(world["store"], actor_team="lang",
	                           actor="grace", target="lang.ada")
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["refresh_requested"] == "2026-08-19T10:30:00Z"
	assert live["refresh_generation"] == asked["generation"]
	# the adapter answers it — no model turn is involved anywhere here
	tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", source="configured",
	                 answers=asked["generation"],
	                 facts={"version": "1.4.1"})
	live = runtime(world)["lang.ada"]["runtime"]
	assert live["refresh_requested"] is None
	inventory = {entry["key"]: entry for entry in live["facts"]}
	assert inventory["version"]["value"] == "1.4.1"


# -- 9. a launcher configuration that carries secrets -------------------------

SECRET_BEARING = {
	# the shapes a real launcher configuration actually contains
	"log": "https://logs.example.test/tail?X-Amz-Signature=" + "a" * 64,
	"readiness": "https://gw.example.test/cb#access_token=" + "b" * 32,
	"service": "codex-event-bridge --header 'Authorization: Bearer "
	           + "c" * 40 + "'",
	"dispatcher": "https://user:hunter2@dispatch.example.test/target",
	"version": "build sk-" + "d" * 20,
}


@pytest.mark.parametrize("key", sorted(SECRET_BEARING))
def test_a_launcher_secret_is_refused_rather_than_stored(world, key):
	"""Decision 10's boundary, one shape at a time. The inventory is
	locators and versions; a credential is refused at the door rather
	than stored and redacted by a later reader who may not run."""
	start(world)
	freeze_work(world)
	with pytest.raises(bw.WorkError, match="credential"):
		tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
		                 incarnation="run-1",
		                 facts={key: SECRET_BEARING[key]})
	assert runtime(world)["lang.ada"]["runtime"]["facts"] == [], \
		"a refused publication left something behind"


def test_a_secret_bearing_launcher_still_publishes_its_safe_facts(world):
	"""Refusing the credential must not cost the operator the
	inventory: the safe half of the same deployment publishes."""
	start(world)
	freeze_work(world)
	tr.runtime_facts(world["store"], actor_team="lang", actor="ada",
	                 incarnation="run-1", source="configured",
	                 facts={"workdir": "/home/op/src/baton",
	                        "log": "/var/log/codex-event-bridge.log",
	                        "readiness": "/run/baton/events.sock"})
	inventory = {entry["key"]: entry["value"] for entry in
	             runtime(world)["lang.ada"]["runtime"]["facts"]}
	assert inventory == {"workdir": "/home/op/src/baton",
	                     "log": "/var/log/codex-event-bridge.log",
	                     "readiness": "/run/baton/events.sock"}
	# and nothing anywhere on the member surface carries a secret
	blob = "\n".join(painted(world, tab="teams"))
	for secret in ("hunter2", "Bearer", "X-Amz-Signature", "access_token"):
		assert secret not in blob, secret


# -- the operator reference is tied to the grammar ---------------------------

def test_the_operator_reference_names_every_runtime_verb():
	"""Slice 7 owes `docs/BATON-WORK.md` a runtime command reference.
	The verb list is asked of the GRAMMAR rather than restated here, so
	a runtime verb added later fails this on the day it ships instead
	of on the day an operator cannot find it."""
	import pathlib
	from baton_work import cli as _cli
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	verbs = {name for name in _cli.GRAMMAR
	         if name == "runtime" or name.startswith("runtime-")}
	assert verbs, "the grammar has no runtime verbs at all"
	for verb in sorted(verbs):
		assert verb in body, \
			f"the operator reference never names {verb!r}"


def test_the_operator_reference_documents_runtime_state_reconnect_operands():
	"""The manual command surface must include the operands that make a
	reconnect and an explicit lease deadline operable. Merely mentioning
	`session=` on runtime-start does not teach an operator how the live lease
	is updated after that session changes."""
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	state_help = body.split("runtime-state", 1)[1].split("runtime-end", 1)[0]
	for operand in ("session=", "expires-at="):
		assert operand in state_help, \
			f"the runtime-state reference omits {operand!r}"


def _runtime_section():
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	section = body[body.index("### Agent runtime state"):]
	tail = section.find("\n### ", 1)
	return section if tail < 0 else section[:tail]


def _verb_block(section, verb):
	"""The command lines that belong to ONE verb.

	Per-verb rather than per-section on purpose: `session=` is spelled
	on `runtime-start`, so a section-wide search would call it
	documented while `runtime-state` — the verb a reconnect actually
	uses — never mentioned it. That is exactly the omission R28 found.
	"""
	verbs = {name for name in _cli.GRAMMAR
	         if name == "runtime" or name.startswith("runtime-")}
	block, grabbing = [], False
	for line in section.splitlines():
		if not line.startswith("    "):
			grabbing = False
			continue
		named = verbs.intersection(line.split())
		if verb in named:
			grabbing, _ = True, block.append(line)
		elif named:
			grabbing = False
		elif grabbing:
			block.append(line)
	return "\n".join(block)


def test_the_operator_reference_names_every_runtime_operand():
	"""R28 generalized. The omission was not a typo — the reference was
	written from what the section was ABOUT rather than from what the
	grammar accepts, which is how `session=` and `expires-at=` fell out
	of `runtime-state` while the same section promised reconnect and
	freshness. The operand list is therefore asked of the grammar, per
	verb, so the next operand added to any runtime verb fails here."""
	section = _runtime_section()
	missing = []
	for verb, spec in _cli.GRAMMAR.items():
		if verb != "runtime" and not verb.startswith("runtime-"):
			continue
		block = _verb_block(section, verb)
		for key in spec.get("keys", ()):
			name = key["name"]
			# a fact KEY is documented in the inventory prose rather
			# than in the command line, which spells them `KEY=VALUE`
			if f"{name}=" in block or f"`{name}`" in section:
				continue
			missing.append(f"{verb} {name}")
	assert not missing, f"undocumented runtime operands: {missing}"


def test_the_operator_reference_teaches_the_state_vocabulary():
	"""The states and the closed cause categories are the two closed
	sets an operator meets in this surface, and reading one of them off
	a JSON field is not documentation."""
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	for state in tr.RUNTIME_STATES + ("offline", "unknown"):
		assert f"`{state}`" in body, f"the reference never names {state}"
	for cause in tr.RUNTIME_CAUSES:
		assert f"`{cause}`" in body, f"the reference never names {cause}"
	for key in tr.RUNTIME_FACTS:
		assert f"`{key}`" in body, f"the inventory key {key} is undocumented"


def test_the_operator_reference_keeps_refresh_and_poke_apart():
	"""They are the two halves of decision 11 and confusing them is how
	a diagnostic becomes a model turn."""
	import pathlib
	repo = pathlib.Path(__file__).resolve().parents[2]
	body = (repo / "docs" / "BATON-WORK.md").read_text(encoding="utf-8")
	# Prose wraps, so the phrases are matched against the section with
	# its whitespace collapsed rather than against its line breaks.
	section = " ".join(
		body[body.index("### Agent runtime state"):].split())
	assert "never wakes the model" in section
	assert "only the agent itself can answer" in section
