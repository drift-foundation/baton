"""W93 slice 3: the participant runtime lease.

`work/records/2026/08/finding-agent-runtime-state/`. `baton.tuner` held
W22 while its Codex turn sat on a command-approval prompt. Baton showed
`active` with a Handler, because that is all Baton had: Phase is the
Work's scheduler state and Handler is who holds the claim, and neither
can say the held turn is waiting on a human. The evidence existed only
in a dispatcher log.

This slice is the authority half — the lease, its transitions, its
refusals, and the read projections. The adapters that publish onto it
and the Jobs/Teams/Inbox rendering are later slices, so what these tests
hold is the contract those slices will lean on:

- a runner publishes about ITSELF, on a lease it holds, and a superseded
  incarnation never overwrites its replacement;
- the stored vocabulary is closed, and `offline`/`unknown` are DERIVED
  from silence at read time rather than published;
- silence is never diagnosed — a quiet runner is `unknown`, never
  `failed` and never `stuck`;
- provenance separates what was reported from what was concluded;
- and none of it is workflow authority: no runtime write moves a claim,
  a phase, a route or anything else on the Work table.
"""

from __future__ import annotations

NEXT_TAB = ord("]")   # W1151: `]` switches tabs; Tab moves panes
import hashlib
import json as _json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                        # noqa: E402
from baton_work import authority as au                         # noqa: E402
from baton_work import cli as _cli                              # noqa: E402
from baton_work import projection as pj                         # noqa: E402
from baton_work import transitions as tr                        # noqa: E402
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


def make_work(world, title="the held work"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")


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


def work_snapshot(world):
	"""Everything a runtime report must never touch."""
	return [dict(row) for row in
	        world["store"].conn.execute("SELECT * FROM work")]


# -- the schema --------------------------------------------------------------

def test_the_fresh_authority_carries_the_runtime_tables(world):
	"""The finding rules this a FRESH schema: schema 22 had nowhere to
	put a participant's runtime state, and no live migration is part of
	this Work."""
	# W2938 added `member_pickup` at 25; W415 added
	# `approval_incidents` at 26.
	assert au.SCHEMA_VERSION == 26
	names = {row["name"] for row in world["store"].conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table'")}
	assert {"runtime_leases", "runtime_events"} <= names


# -- publishing --------------------------------------------------------------

def test_a_fresh_lease_reports_idle_with_its_configured_facts(world):
	start(world, provider="OpenAI", model="gpt-5.6",
	      session="019ff3f9-4b0e-7c1a", action_owner="lang.grace")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "idle", "a started runner is not unknown"
	assert state["provenance"] == "reported"
	assert state["adapter"] == "codex" and state["provider"] == "OpenAI"
	assert state["model"] == "gpt-5.6"
	assert state["session"] == "019ff3f9-4b0e-7c1a", \
		"the record must keep the session locator in full"
	assert state["action_owner"] == "lang.grace"


def test_the_adapter_is_never_inferred_from_the_participant_name(world):
	"""Decision 9: `baton.claude` may be driven by any conforming
	adapter, and guessing from an identity is how a roster starts
	lying."""
	start(world, member="ada", adapter="acp", provider="Anthropic")
	assert runtime(world)["lang.ada"]["runtime"]["adapter"] == "acp"
	with pytest.raises(bw.WorkError):
		tr.runtime_start(world["store"], actor_team="lang", actor="grace",
		                 incarnation="run-x", adapter="")


def test_the_motivating_incident_is_visible_end_to_end(world):
	"""working -> waiting-input(approval) -> working -> idle, exactly
	the sequence the finding says an operator should have seen."""
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	start(world)
	report(world, state="working", work=born["work_id"], episode=2)
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "working"
	report(world, state="waiting-input", cause="approval",
	       detail="command approval required", work=born["work_id"])
	held = runtime(world)["lang.ada"]
	assert held["runtime"]["state"] == "waiting-input"
	assert held["runtime"]["cause"] == "approval"
	assert held["runtime"]["detail"] == "command approval required"
	# the Work is STILL claimed and active — the report explained the
	# claim, it did not change it
	assert [entry["work"] for entry in held["handled_work"]] == \
		[born["work_id"]]
	report(world, state="working", work=born["work_id"])
	report(world, state="idle")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "idle"
	assert [row["state"] for row in pj.runtime_history(
		world["store"], participant="lang.ada")["rows"]] == \
		["idle", "working", "waiting-input", "working", "idle"]


def test_the_closed_category_is_cause_not_reason(world):
	"""Across this grammar `reason=` is durable human prose an operator
	may author in an editor, and that name/behaviour pairing is enforced
	repository-wide. A closed machine category published by an adapter
	takes its own name rather than making one word mean two things."""
	spec = {key["name"]: key
	        for key in _cli.GRAMMAR["runtime-state"]["keys"]}
	assert "reason" not in spec and "cause" in spec, spec
	assert not spec["cause"].get("prose"), \
		"a closed vocabulary must never open an editor"
	assert not any(key.get("prose")
	               for key in _cli.GRAMMAR["runtime-state"]["keys"]), \
		"an adapter-published field is not editor-authored prose"


def test_waiting_input_must_name_what_it_waits_on(world):
	start(world)
	with pytest.raises(bw.WorkError, match="waiting-input requires"):
		report(world, state="waiting-input")
	report(world, state="waiting-input", cause="approval")


def test_the_stored_vocabulary_is_closed(world):
	start(world)
	for refused in ("stuck", "offline", "unknown", "busy", ""):
		with pytest.raises(bw.WorkError, match="not one of"):
			report(world, state=refused)
	for accepted in tr.RUNTIME_STATES:
		report(world, state=accepted,
		       cause="approval" if accepted == "waiting-input" else None)


def test_a_cause_outside_the_closed_categories_refuses(world):
	start(world)
	with pytest.raises(bw.WorkError, match="not one of"):
		report(world, state="failed", cause="because it broke")


def test_a_runtime_detail_is_a_sentence_and_not_a_log(world):
	start(world)
	with pytest.raises(bw.WorkError, match="the limit is"):
		report(world, state="failed", cause="internal",
		       detail="x" * 401)


# -- the lease ---------------------------------------------------------------

def test_a_superseded_runner_never_overwrites_its_replacement(world):
	"""Decision 6, and the whole reason the incarnation exists."""
	start(world, incarnation="run-1")
	report(world, incarnation="run-1", state="working")
	start(world, incarnation="run-2", adapter="acp",
	      rationale="the codex runner exited; relaunched on acp")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "idle"
	with pytest.raises(bw.WorkError, match="superseded runner"):
		report(world, incarnation="run-1", state="failed")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "idle", \
		"the stale write changed the live state anyway"
	assert runtime(world)["lang.ada"]["runtime"]["incarnation"] == "run-2"


def test_publishing_without_a_lease_refuses(world):
	with pytest.raises(bw.WorkError, match="no runtime lease"):
		report(world, member="grace", incarnation="ghost")


def test_a_replacement_keeps_both_timelines_in_the_journal(world):
	start(world, incarnation="run-1")
	report(world, incarnation="run-1", state="working")
	start(world, incarnation="run-2",
	      rationale="runner died mid-turn; relaunched")
	report(world, incarnation="run-2", state="failed", cause="provider")
	rows = pj.runtime_history(world["store"],
	                          participant="lang.ada")["rows"]
	assert [(row["incarnation"], row["state"]) for row in rows] == [
		("run-1", "idle"), ("run-1", "working"),
		("run-2", "idle"), ("run-2", "failed")], rows


def test_an_ended_lease_is_terminal_for_that_incarnation(world):
	start(world)
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1", cause="internal")
	with pytest.raises(bw.WorkError, match="ended at"):
		report(world, state="working")


# -- bounded freshness (review R1) -------------------------------------------

def test_a_lease_is_always_bounded_even_when_nobody_supplies_one(world):
	"""Review R1: an optional deadline let a runner that omitted the
	operand report `working` forever, after its process was gone. Every
	current runtime fact carries freshness or it is not a fact."""
	at("2026-08-19T10:00:00Z")
	start(world)
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["expires_at"] is not None, state
	assert state["expires_at"] > "2026-08-19T10:00:00Z"
	at("2026-08-19T23:59:00Z")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "unknown", \
		"an unbounded lease survived the day"


def test_a_lease_born_expired_refuses(world):
	at("2026-08-19T10:00:00Z")
	with pytest.raises(bw.WorkError, match="not later than now"):
		start(world, expires_at="2026-08-19T09:00:00Z")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "offline"


def test_every_explicit_report_renews_the_deadline(world):
	"""Freshness a live report cannot refresh is not freshness."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	at("2026-08-19T10:04:00Z")
	report(world, state="working")
	assert runtime(world)["lang.ada"]["runtime"]["expires_at"] > \
		"2026-08-19T10:05:00Z", "the report kept the old deadline"
	at("2026-08-19T10:06:00Z")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "working", \
		"a renewed lease expired on its retired deadline"


def test_a_report_after_the_deadline_renews_rather_than_staying_unknown(world):
	"""Coming back from a long silence is what a slow tool call looks
	like. Refusing the report would strand a runner that is
	demonstrably alive; keeping the old deadline would report `unknown`
	about a participant that just spoke."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	at("2026-08-19T10:30:00Z")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "unknown"
	result = report(world, state="working")
	assert result["renewed_after_expiry"] is True, result
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "working" and state["stale"] is False
	assert state["last_contact"] == "2026-08-19T10:30:00Z"


# -- one launch identity (review R2) -----------------------------------------

def test_restarting_the_same_incarnation_refuses(world):
	"""Review R2: it reset a live runner to `idle`, bypassing the
	terminal gate the other two verbs go through."""
	start(world, incarnation="run-1")
	report(world, incarnation="run-1", state="working")
	before = _runtime_rows(world)
	with pytest.raises(bw.WorkError, match="one launch"):
		start(world, incarnation="run-1", rationale="same launch again")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "working", \
		"the refused start reset a live runner"
	assert _runtime_rows(world) == before, \
		"a refused start wrote to the lease or the journal"


def test_resurrecting_an_ended_incarnation_refuses(world):
	start(world, incarnation="run-1")
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1", cause="internal")
	before = _runtime_rows(world)
	with pytest.raises(bw.WorkError, match="ended"):
		start(world, incarnation="run-1", rationale="bring it back")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "offline"
	assert _runtime_rows(world) == before, \
		"a refused start wrote to the lease or the journal"


def test_reusing_a_superseded_incarnation_refuses(world):
	"""One incarnation names one launch for its entire journal lifetime,
	not merely while it occupies the current-row projection. Once run-2
	supersedes run-1, presenting run-1 again must not resurrect the old
	launch identity and displace run-2."""
	start(world, incarnation="run-1")
	start(world, incarnation="run-2", rationale="replace run-1")
	before = _runtime_rows(world)
	with pytest.raises(bw.WorkError, match="one launch"):
		start(world, incarnation="run-1", rationale="old runner returned")
	assert runtime(world)["lang.ada"]["runtime"]["incarnation"] == \
		"run-2"
	assert _runtime_rows(world) == before, \
		"a refused historical resurrection wrote lease or journal state"


def test_the_one_launch_guard_reads_committed_state(world):
	"""Review R4 also asks that the refusal stay atomic with concurrent
	starts. The guard runs inside the write transaction and consults
	the journal there, so a second connection that never saw the first
	call still refuses — it is reading committed state under the lock,
	not a value cached before it.

	Two connections rather than two threads: the property under test is
	WHERE the check reads from, and a second connection proves that
	without making the suite depend on thread timing."""
	other = bw.Authority(world["database"])
	try:
		start(world, incarnation="run-1")
		tr.runtime_start(other, actor_team="lang", actor="ada",
		                 incarnation="run-2",
		                 adapter="acp", rationale="replacing run-1")
		# the first connection never observed run-2 being written
		with pytest.raises(bw.WorkError, match="one launch"):
			start(world, incarnation="run-2",
			      rationale="racing the replacement")
		with pytest.raises(bw.WorkError, match="one launch"):
			start(world, incarnation="run-1",
			      rationale="the superseded runner returning")
		assert runtime(world)["lang.ada"]["runtime"]["incarnation"] == \
			"run-2"
	finally:
		other.close()


def test_an_exact_retry_is_op_ids_job_and_not_a_restart(world):
	"""The replay path is where 'the same call twice' belongs; the
	incarnation is not a retry token."""
	first = tr.runtime_start(world["store"], actor_team="lang",
	                         actor="ada", incarnation="run-1",
	                         adapter="codex", op_id="launch-1")
	again = tr.runtime_start(world["store"], actor_team="lang",
	                         actor="ada", incarnation="run-1",
	                         adapter="codex", op_id="launch-1")
	assert again["operation"]["state"] == "replayed", again
	assert first["seq"] == again["seq"]


# -- reasoned replacement (review R3) ----------------------------------------

def test_replacing_a_lease_requires_a_rationale(world):
	start(world, incarnation="run-1")
	with pytest.raises(bw.WorkError, match="needs rationale"):
		start(world, incarnation="run-2")
	assert runtime(world)["lang.ada"]["runtime"]["incarnation"] == "run-1"


def test_a_first_start_needs_no_rationale(world):
	"""There is nothing to explain about a runner simply arriving."""
	start(world, incarnation="run-1")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "idle"


def test_the_journal_alone_names_the_superseded_launch_and_why(world):
	"""Review R3: `runtime-history` showed two timelines and no
	statement that one superseded the other, or why."""
	start(world, incarnation="run-1")
	report(world, incarnation="run-1", state="working")
	start(world, incarnation="run-2", adapter="acp",
	      rationale="codex session died; relaunched through acp")
	rows = pj.runtime_history(world["store"],
	                          participant="lang.ada")["rows"]
	replacement = next(row for row in rows
	                   if row["incarnation"] == "run-2")
	assert replacement["supersedes"] == "run-1", replacement
	assert replacement["detail"] == \
		"codex session died; relaunched through acp"
	# and a first start claims to supersede nothing
	first = next(row for row in rows if row["incarnation"] == "run-1")
	assert first["supersedes"] is None
	# an ordinary transition is not a replacement either
	moved = next(row for row in rows
	             if row["incarnation"] == "run-1"
	             and row["state"] == "working")
	assert moved["supersedes"] is None


def _runtime_rows(world):
	store = world["store"]
	return ([dict(row) for row in
	         store.conn.execute("SELECT * FROM runtime_leases")],
	        [dict(row) for row in
	         store.conn.execute("SELECT * FROM runtime_events")])


# -- derived state -----------------------------------------------------------

def test_silence_past_the_deadline_is_unknown_and_never_failed(world):
	"""'A lease expiry yields unknown or offline, never failed or
	stuck.' Baton cannot tell a wedged process from a long tool call."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	report(world, state="working")
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "working"
	at("2026-08-19T10:06:00Z")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "unknown", state
	assert state["provenance"] == "derived"
	assert state["stale"] is True
	assert "working" in state["note"], \
		"the last reported state is not recoverable from the note"
	assert state["state"] not in ("failed", "stuck")


def test_expiry_writes_nothing(world):
	"""Reads are pure: the deadline passing must not mutate a byte."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	report(world, state="working")
	at("2026-08-19T10:06:00Z")
	before = _digest(world["database"])
	assert runtime(world)["lang.ada"]["runtime"]["state"] == "unknown"
	assert _digest(world["database"]) == before, \
		"deriving expiry wrote to the authority"


def test_a_participant_that_never_started_is_offline_by_derivation(world):
	state = runtime(world)["lang.grace"]["runtime"]
	assert state["state"] == "offline"
	assert state["provenance"] == "derived"
	assert state["incarnation"] is None


def test_an_explicit_exit_is_offline_by_report(world):
	"""'This runner said goodbye' and 'this lease went quiet' are
	different operational facts and get different provenance."""
	start(world)
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1", cause="internal",
	               detail="turn finished")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "offline"
	assert state["provenance"] == "reported"
	assert state["cause"] == "internal"
	assert "exited" in state["note"]


# -- it is not workflow authority --------------------------------------------

@pytest.mark.parametrize("act", ["start", "state", "end"])
def test_no_runtime_write_touches_the_work_table(world, act):
	"""Decision 7. Runtime diagnostics never auto-release, transfer,
	block, close or reassign Work — recovery stays an explicit act."""
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	if act != "start":
		start(world)
	before = work_snapshot(world)
	if act == "start":
		start(world)
	elif act == "state":
		report(world, state="failed", cause="provider",
		       work=born["work_id"])
	else:
		tr.runtime_end(world["store"], actor_team="lang", actor="ada",
		               incarnation="run-1", cause="transport")
	assert work_snapshot(world) == before, \
		f"runtime-{act} mutated the Work table"


def test_a_runner_correlation_never_becomes_a_claim(world):
	"""The runner names the Work it BELIEVES it is serving. The Work
	table decides who holds it, and the disagreement is shown."""
	born = make_work(world)
	start(world)
	report(world, state="working", work=born["work_id"])
	row = runtime(world)["lang.ada"]
	assert row["runtime"]["work"] == born["work_id"]
	assert row["handled_work"] == [], \
		"the correlation claimed the Work"
	detail = pj.detail(world["store"], born["work_id"],
	                   viewer_team="lang", viewer_member="ada")
	assert detail["handler"] is None and detail["phase"] == "queued"


def test_a_terminal_work_leaves_its_runner_alone(world):
	"""'A terminal Work whose former runner is still alive' — closing
	Work is not a statement about anybody's process."""
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	start(world)
	report(world, state="working", work=born["work_id"])
	tr.close_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada", outcome="satisfying", rationale="done")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "working", \
		"closing Work rewrote its runner's state"
	assert state["work"] == born["work_id"]


# -- the roster and the interfaces -------------------------------------------

def test_the_roster_carries_the_same_canonical_state(world):
	"""Teams must not derive runtime a second way — one helper, one
	answer, or the two surfaces disagree in front of an operator."""
	start(world, provider="OpenAI", session="019ff3f9")
	report(world, state="waiting-input", cause="approval")
	roster = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	member = next(entry for team in roster["teams"]
	              for entry in team["members"]
	              if entry["participant"] == "lang.ada")
	assert member["runtime"] == \
		runtime(world)["lang.ada"]["runtime"]


def test_the_agents_own_report_stays_separately_visible(world):
	"""The poke answer is an ON-DEMAND agent report, not a live runner
	state; the revalidation note requires both to remain distinct."""
	seq = tr.poke(world["store"], actor_team="lang", actor="grace",
	              target="lang.ada", request="status?")["poke"]
	tr.answer_poke(world["store"], seq, actor_team="lang", actor="ada",
	               state="working", explanation="mid-way")
	start(world)
	report(world, state="waiting-input", cause="approval")
	roster = pj.teams(world["store"], viewer_team="lang",
	                  viewer_member="ada")
	member = next(entry for team in roster["teams"]
	              for entry in team["members"]
	              if entry["participant"] == "lang.ada")
	assert member["runtime"]["state"] == "waiting-input"
	assert member["last_answer"]["state"] == "working", \
		"the runner state overwrote the agent's own answer"


def test_the_verbs_are_reachable_and_carry_no_workflow_authority(world):
	for verb in ("runtime-start", "runtime-state", "runtime-end",
	             "runtime", "runtime-history"):
		assert verb in _cli.GRAMMAR
	for verb in ("runtime-start", "runtime-state", "runtime-end"):
		assert verb in _cli.MUTATIONS, \
			f"{verb} writes, so a console must refresh after it"
	for verb in ("runtime", "runtime-history"):
		assert verb not in _cli.MUTATIONS


def test_the_grammar_offers_exactly_the_transition_vocabularies(world):
	spec = {key["name"]: key
	        for key in _cli.GRAMMAR["runtime-state"]["keys"]}
	assert spec["state"]["values"] == tr.RUNTIME_STATES
	assert spec["cause"]["values"] == tr.RUNTIME_CAUSES
	assert "offline" not in spec["state"]["values"]
	assert "unknown" not in spec["state"]["values"]


def test_the_cli_publishes_and_reads_one_runtime_state(world, capsys):
	code = _cli.main(["--config", world["config"], "--participant",
	                  "lang.ada", "runtime-start", "incarnation=run-9",
	                  "adapter=acp", "session=72a241a9-full-locator"])
	assert code == 0
	capsys.readouterr()
	code = _cli.main(["--config", world["config"], "--participant",
	                  "lang.ada", "runtime-state", "incarnation=run-9",
	                  "state=waiting-input", "cause=approval",
	                  "detail=command approval required"])
	assert code == 0
	capsys.readouterr()
	code = _cli.main(["--config", world["config"], "--participant",
	                  "lang.grace", "runtime"])
	assert code == 0
	result = _json.loads(capsys.readouterr().out)["result"]
	ada = next(row for row in result["participants"]
	           if row["participant"] == "lang.ada")
	assert ada["runtime"]["state"] == "waiting-input"
	assert ada["runtime"]["cause"] == "approval"
	assert ada["runtime"]["session"] == "72a241a9-full-locator", \
		"JSON must carry the session locator in full"


def test_a_runner_publishes_only_about_itself(world, capsys):
	"""The acting participant is the subject, so no participant can
	narrate another's runtime and no capability question arises."""
	spec = {key["name"]
	        for key in _cli.GRAMMAR["runtime-start"]["keys"]}
	assert "target" not in spec and "participant" not in spec, spec
	start(world, member="ada")
	report(world, member="ada", state="working")
	assert runtime(world)["lang.grace"]["runtime"]["state"] == "offline"


def _digest(database):
	blob = b""
	for suffix in ("", "-wal"):
		try:
			with open(database + suffix, "rb") as handle:
				blob += handle.read()
		except FileNotFoundError:
			pass
	return hashlib.sha256(blob).hexdigest()


# -- slice 5: the three surfaces ---------------------------------------------
#
# Jobs, Teams and Inbox all read the ONE canonical runtime projection.
# None of them infers a runner's state from Work Phase or from Handler,
# which is the whole point: those two say the Work is being executed and
# by whom, and neither can say the held turn is sitting on a prompt.

def _console(world, member="ada"):
	from baton_work.tui.app import Console
	return Console(world["store"], "lang", member,
	               config_path=world["config"])


class _Screen:
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


def _painted(view, height=26, width=150):
	screen = _Screen(height, width)
	view.render(screen)
	return screen.lines()


def _held(world, member="ada"):
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor=member)
	return born["work_id"]


def test_the_work_row_carries_its_handlers_runner_state(world):
	work = _held(world)
	start(world, session="01a01552-9d3e", action_owner="lang.grace")
	report(world, state="waiting-input", cause="approval",
	       detail="command approval required", work=work)
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["agent"]["state"] == "waiting-input"
	assert row["agent"]["cause"] == "approval"
	assert row["agent"]["provenance"] == "reported"
	# and it is the same object the roster and the runtime projection
	# report, so no surface can disagree with another
	assert row["agent"] == runtime(world)["lang.ada"]["runtime"]


def test_unclaimed_work_has_no_runner_to_describe(world):
	"""`-` because nobody holds it — a different fact from a runner
	nobody can see, which reads `off` or `unkn`."""
	from baton_work.tui.app import agent_cell
	born = make_work(world)
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == born["work_id"])
	assert row["agent"] is None
	assert agent_cell(row["agent"]) == "-"


def test_a_claimed_work_whose_runner_never_published_says_so(world):
	work = _held(world)
	from baton_work.tui.app import agent_cell
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["agent"]["state"] == "offline"
	assert row["agent"]["provenance"] == "derived"
	assert agent_cell(row["agent"]) == "off"


def test_the_jobs_table_paints_the_runner_state_beside_handler(world):
	"""The finding's own example: Handler says who is executing and the
	column beside it says what their runner is doing.

	W137 renamed that column `Run`. The header was the one thing about
	it that was wrong — it said `Agent` while every cell held a runtime
	STATE, and `Handler` already named the participant. The values, the
	projection field and the placement are unchanged."""
	work = _held(world)
	start(world)
	report(world, state="waiting-input", cause="approval", work=work)
	lines = _painted(_console(world))
	header = next(line for line in lines if "Handler" in line)
	assert "Run" in header, header
	assert "Agent" not in header, \
		"the superseded header survived beside the new one"
	assert header.index("Handler") < header.index("Run")
	row = next(line for line in lines
	           if line.startswith(work.rsplit("-", 1)[1] + " "))
	assert "lang.ada" in row and "input" in row, row


def test_the_agent_cell_is_never_inferred_from_phase_or_handler(world):
	"""A claimed, active Work with a runner reporting `idle` shows
	`idle`. Phase says the Work is being executed; only the runner says
	whether anything is happening."""
	from baton_work.tui.app import agent_cell
	work = _held(world)
	start(world)
	report(world, state="idle")
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["phase"] == "active" and row["handler"] is not None
	assert agent_cell(row["agent"]) == "idle"


def test_teams_members_show_the_ruled_columns(world):
	work = _held(world)
	start(world, provider="OpenAI", model="gpt-5.6",
	      session="01a01552-9d3e-77bb-a2c1")
	report(world, state="working", work=work)
	view = _console(world)
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	lines = _painted(view)
	header = next(line for line in lines if "Session" in line)
	for column in ("Role", "Agent", "State", "Work", "Session", "Since"):
		assert column in header, header
	row = next(line for line in lines if line.startswith("lang.ada"))
	assert "codex" in row, row
	assert "work" in row, row
	assert work.rsplit("-", 1)[1] in row, row


def test_an_identical_renewal_updates_contact_not_state_since(world):
	"""Periodic lease renewal says the runner is still contactable; it
	does not claim that an unchanged state began again."""
	at("2026-08-19T10:00:00Z")
	start(world)
	report(world, state="working", work=None)
	initial = runtime(world)["lang.ada"]["runtime"]
	at("2026-08-19T10:01:00Z")
	report(world, state="working", work=None)
	renewed = runtime(world)["lang.ada"]["runtime"]
	assert renewed["since"] == initial["since"]
	assert renewed["last_contact"] == "2026-08-19T10:01:00Z"


def test_derived_unknown_begins_at_the_lease_deadline(world):
	"""The projected state changes to unknown when the lease expires,
	not when its last reported state began."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	report(world, state="working",
	       expires_at="2026-08-19T10:05:00Z")
	at("2026-08-19T10:06:00Z")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["state"] == "unknown"
	assert state["since"] == "2026-08-19T10:05:00Z"


def test_teams_since_is_elapsed_mmss_not_an_absolute_timestamp(monkeypatch):
	from baton_work.tui import app as tui
	monkeypatch.setattr(tui._time, "time", lambda: 65)
	row = {"roles": ["dev"], "handled_work": [], "runtime": {
		"adapter": "codex", "state": "working", "session": "s1",
		"since": "1970-01-01T00:00:00Z"}}
	assert tui.Console._team_cells(row)["Since"] == "01:05"


def test_member_details_expose_the_full_session_and_provenance(world):
	"""The compact table abbreviates the locator; the record never
	does, and the detail block is where an operator reads it."""
	work = _held(world)
	start(world, provider="OpenAI", model="gpt-5.6",
	      session="01a01552-9d3e-77bb-a2c1-and-longer",
	      action_owner="lang.grace")
	report(world, state="waiting-input", cause="approval",
	       detail="command approval required", work=work)
	view = _console(world)
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	lines = _painted(view, height=40)
	assert any("01a01552-9d3e-77bb-a2c1-and-longer" in line
	           for line in lines), lines
	# W184 made member detail a key/value table, so each of these is
	# its own discoverable row instead of a packed sentence. The facts
	# asserted are the same ones.
	assert any("State" in line and "waiting-input (reported)" in line
	           for line in lines), lines
	assert any("Cause" in line and "approval" in line
	           for line in lines), lines
	assert any("Provider" in line and "OpenAI" in line
	           for line in lines), lines
	assert any("Model" in line and "gpt-5.6" in line
	           for line in lines), lines
	assert any("interactive answers owed by lang.grace" in line
	           for line in lines), lines


def test_a_member_with_no_lease_says_so_rather_than_looking_fine(world):
	view = _console(world, member="grace")
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	# W184: the same fact, as the `Lease` row of the detail table.
	assert any("Lease" in line and "never published runtime state" in line
	           for line in _painted(view)), _painted(view)


def test_waiting_input_reaches_the_owners_inbox_only(world):
	"""'Inbox contains only runtime states that require the viewer to
	act.' The owner is named on the lease and never guessed."""
	work = _held(world)
	start(world, action_owner="lang.grace")
	report(world, state="waiting-input", cause="approval",
	       detail="command approval required", work=work)
	owner = pj.inbox(world["store"], viewer_team="lang",
	                 viewer_member="grace")
	row = next(entry for entry in owner["rows"]
	           if entry["kind"] == "runtime")
	assert row["owed"] is True
	assert row["selector"] == "lang.ada"
	assert row["work"] == work
	assert "approval" in row["summary"]
	assert owner["owed_action"] is True
	# and nobody else is told to do anything about it
	mine = pj.inbox(world["store"], viewer_team="lang",
	                viewer_member="ada")
	assert not [entry for entry in mine["rows"]
	            if entry["kind"] == "runtime"]


def test_ordinary_transitions_are_not_inbox_noise(world):
	"""'Ordinary working and idle transitions do not create
	notification noise.'"""
	work = _held(world)
	start(world, action_owner="lang.grace")
	for state in ("working", "idle", "retrying"):
		report(world, state=state, work=work,
		       cause="transport" if state == "retrying" else None)
		rows = pj.inbox(world["store"], viewer_team="lang",
		                viewer_member="grace")["rows"]
		assert not [entry for entry in rows
		            if entry["kind"] == "runtime"], state


def test_a_waiting_runner_with_no_owner_creates_no_obligation(world):
	"""'With no action owner it remains visible in Teams and the Jobs
	Agent cell but creates no guessed team-wide obligation.'"""
	work = _held(world)
	start(world)
	report(world, state="waiting-input", cause="approval", work=work)
	for member in ("ada", "grace"):
		rows = pj.inbox(world["store"], viewer_team="lang",
		                viewer_member=member)["rows"]
		assert not [entry for entry in rows
		            if entry["kind"] == "runtime"], member
	# still visible where it belongs
	row = next(entry for entry in pj.tree(
		world["store"], None, viewer_team="lang",
		viewer_member="ada")["rows"] if entry["id"] == work)
	assert row["agent"]["state"] == "waiting-input"


def test_the_inbox_row_says_baton_cannot_answer_it(world):
	"""The runner is waiting on a person in its own session, so the row
	must not advertise an action the operator cannot take here."""
	work = _held(world)
	start(world, action_owner="lang.grace")
	report(world, state="waiting-input", cause="approval", work=work)
	view = _console(world, member="grace")
	while view.tab != "inbox":
		view.handle(NEXT_TAB)
	lines = _painted(view)
	row = next(line for line in lines if line.startswith("lang.ada"))
	assert "attend" in row, row
	assert any("Baton has no verb that answers it" in line
	           for line in lines), lines


def test_the_runtime_row_leaves_when_the_runner_moves_on(world):
	work = _held(world)
	start(world, action_owner="lang.grace")
	report(world, state="waiting-input", cause="approval", work=work)
	assert pj.inbox(world["store"], viewer_team="lang",
	                viewer_member="grace")["owed"] >= 1
	report(world, state="working", work=work)
	rows = pj.inbox(world["store"], viewer_team="lang",
	                viewer_member="grace")["rows"]
	assert not [entry for entry in rows if entry["kind"] == "runtime"]


def test_an_expired_waiting_lease_stops_being_actionable(world):
	"""A stale lease is `unknown`, and an operator is not asked to
	attend a prompt nobody can prove is still there."""
	at("2026-08-19T10:00:00Z")
	work = _held(world)
	start(world, action_owner="lang.grace",
	      expires_at="2026-08-19T10:05:00Z")
	report(world, state="waiting-input", cause="approval", work=work,
	       expires_at="2026-08-19T10:05:00Z")
	assert pj.inbox(world["store"], viewer_team="lang",
	                viewer_member="grace")["owed"] >= 1
	at("2026-08-19T10:06:00Z")
	rows = pj.inbox(world["store"], viewer_team="lang",
	                viewer_member="grace")["rows"]
	assert not [entry for entry in rows if entry["kind"] == "runtime"]


def test_a_changed_correlation_starts_a_new_interval(world):
	"""R15's other half: a renewal must not restart the clock, but a
	change in what is DISPLAYED beside the state must. Otherwise a
	runner that moved to a different Work would keep the age of the one
	it left."""
	at("2026-08-19T10:00:00Z")
	first = make_work(world, "the first")
	second = make_work(world, "the second")
	start(world)
	report(world, state="working", work=first["work_id"])
	began = runtime(world)["lang.ada"]["runtime"]["since"]
	at("2026-08-19T10:01:00Z")
	report(world, state="working", work=first["work_id"])
	assert runtime(world)["lang.ada"]["runtime"]["since"] == began, \
		"an identical renewal restarted the state clock"
	at("2026-08-19T10:02:00Z")
	report(world, state="working", work=second["work_id"])
	assert runtime(world)["lang.ada"]["runtime"]["since"] == \
		"2026-08-19T10:02:00Z", \
		"moving to different Work kept the previous interval"
	at("2026-08-19T10:03:00Z")
	report(world, state="waiting-input", cause="approval",
	       work=second["work_id"])
	assert runtime(world)["lang.ada"]["runtime"]["since"] == \
		"2026-08-19T10:03:00Z"


def test_the_reported_interval_survives_in_the_derived_note(world):
	"""Projecting `since` at the deadline must not lose when the last
	reported state actually began — an incident is reconstructed from
	that, and the journal keeps it too."""
	at("2026-08-19T10:00:00Z")
	start(world, expires_at="2026-08-19T10:05:00Z")
	report(world, state="working", expires_at="2026-08-19T10:05:00Z")
	at("2026-08-19T10:30:00Z")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["since"] == "2026-08-19T10:05:00Z"
	assert "10:00:00" in state["note"], state["note"]
	assert state["last_contact"] == "2026-08-19T10:00:00Z"


def test_the_teams_row_and_the_details_answer_different_questions(world):
	"""`Since` is elapsed time in the state; the absolute instants live
	in the detail block, which is where an operator reads them."""
	at("2026-08-19T10:00:00Z")
	work = _held(world)
	start(world, session="01a01552")
	report(world, state="working", work=work)
	view = _console(world)
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	lines = _painted(view, height=40)
	row = next(line for line in lines if line.startswith("lang.ada"))
	# The elapsed vocabulary, not an instant: MM:SS, or ∞ past the
	# hundred-minute overflow — which is what a frozen authority clock
	# against a live console clock produces here, and is itself the
	# ruled spelling.
	cell = row.split()[-1]
	assert cell == "∞" or (len(cell) == 5 and cell[2] == ":"), row
	assert "2026-08-19T10:00" not in row, \
		"the compact row spent its cells on an absolute instant"
	assert any(line.strip().startswith("Since")
	           and "2026-08-19T10:00:00" in line
	           for line in lines), lines


# -- slice 6: the safe operational inventory ---------------------------------

def facts(world, member="ada", incarnation="run-1", source="reported",
          observed_at=None, answers=None, op_id=None, **supplied):
	return tr.runtime_facts(world["store"], actor_team="lang",
	                        actor=member, incarnation=incarnation,
	                        source=source, observed_at=observed_at,
	                        answers=answers, op_id=op_id, facts=supplied)


def pending_refresh(world, member="ada"):
	"""The generation an adapter would read and answer."""
	return next(
		(action for action in pj.participant_actions(
			world["store"], viewer_team="lang",
			viewer_member=member)["actions"]
		 if action["kind"] == "runtime_refresh"), None)


def inventory(world, member="ada"):
	return {entry["key"]: entry
	        for entry in runtime(world)[f"lang.{member}"]["runtime"]
	        ["facts"]}


def test_the_inventory_locates_a_session_without_a_vendor_command(world):
	"""'Members exposes enough runner metadata that an operator does not
	need a vendor-specific thread-listing command merely to identify the
	active session.'"""
	start(world, session="01a01552-9d3e")
	facts(world, source="configured",
	      dispatcher="local/driftquery", readiness="/run/baton.sock",
	      workdir="/home/op/src/baton", log="/var/log/bridge.log",
	      version="codex-event-bridge 1.4.0", service="pid 42199")
	held = inventory(world)
	assert set(held) == {"dispatcher", "readiness", "workdir", "log",
	                     "version", "service"}
	assert held["log"]["value"] == "/var/log/bridge.log"
	assert all(entry["source"] == "configured"
	           for entry in held.values())


def test_every_fact_carries_its_own_source_and_instant(world):
	"""They age separately, so they are reported separately: a locator
	read at launch is not as current as a version observed since."""
	at("2026-08-19T10:00:00Z")
	start(world)
	facts(world, source="configured", workdir="/home/op/src/baton")
	at("2026-08-19T10:05:00Z")
	facts(world, source="reported", version="acp 2.0.1")
	held = inventory(world)
	assert held["workdir"]["observed_at"] == "2026-08-19T10:00:00Z"
	assert held["workdir"]["source"] == "configured"
	assert held["version"]["observed_at"] == "2026-08-19T10:05:00Z"
	assert held["version"]["source"] == "reported"


def test_a_secret_shaped_value_is_refused_rather_than_stored(world):
	"""The adapter scrubs too, and that is not a reason to trust it:
	this is durable state, so the boundary belongs where the durability
	is — and a refusal tells the publisher it has a bug."""
	start(world)
	for value in ("Bearer abcdefghijklmnopqrst",
	              "api_key=sk-01234567890123456789",
	              "https://user:hunter2@api.example.com/v1",
	              "authorization: something"):
		with pytest.raises(bw.WorkError, match="credential"):
			facts(world, log=value)
	assert inventory(world) == {}, "a refused fact was stored anyway"


def test_a_signed_locator_cannot_smuggle_a_credential(world):
	"""A closed key set does not make an allowed locator's VALUE safe.

	Signed log/readiness URLs are realistic deployment inputs, and their
	signature is a credential even though it is not labelled token/password.
	The durable boundary must refuse it rather than preserving it forever.
	"""
	start(world)
	value = ("https://logs.example.test/view?X-Amz-Signature="
	         "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
	with pytest.raises(bw.WorkError, match="credential"):
		facts(world, log=value)
	assert inventory(world) == {}, "a signed locator was stored anyway"


def test_an_oauth_fragment_cannot_smuggle_a_credential(world):
	"""URI fragments can carry bearer tokens just as queries can."""
	start(world)
	value = ("https://client.example.test/callback#access_token="
	         "0123456789abcdef0123456789abcdef")
	with pytest.raises(bw.WorkError, match="credential"):
		facts(world, readiness=value)
	assert inventory(world) == {}, "an OAuth fragment was stored anyway"


def test_the_key_set_is_closed_so_a_secret_has_nowhere_to_go(world):
	start(world)
	for key in ("environment", "prompt", "argv", "config"):
		with pytest.raises(bw.WorkError, match="closed set"):
			tr.runtime_facts(world["store"], actor_team="lang",
			                 actor="ada", incarnation="run-1",
			                 facts={key: "x"})


def test_an_empty_publication_refuses(world):
	start(world)
	with pytest.raises(bw.WorkError, match="at least one"):
		facts(world)


def test_facts_belong_to_one_incarnation(world):
	"""A replacement's inventory never masquerades as its
	predecessor's."""
	start(world, incarnation="run-1")
	facts(world, incarnation="run-1", version="1.0.0")
	start(world, incarnation="run-2", rationale="relaunched")
	assert inventory(world) == {}, \
		"the replacement inherited the previous launch's inventory"
	facts(world, incarnation="run-2", version="2.0.0")
	assert inventory(world)["version"]["value"] == "2.0.0"


def test_a_superseded_runner_cannot_publish_facts(world):
	start(world, incarnation="run-1")
	start(world, incarnation="run-2", rationale="relaunched")
	with pytest.raises(bw.WorkError, match="superseded runner"):
		facts(world, incarnation="run-1", version="1.0.0")


def test_publishing_facts_never_touches_the_work_table(world):
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	start(world)
	before = work_snapshot(world)
	facts(world, version="1.0.0")
	assert work_snapshot(world) == before


# -- the on-demand refresh ---------------------------------------------------

def test_a_refresh_asks_the_adapter_and_runs_nothing(world):
	"""The cheap half of the live-versus-requested split: it records
	that an operator wants fresh facts. Nothing executes, no model is
	woken, and no Work moves."""
	start(world)
	born = make_work(world)
	before = work_snapshot(world)
	at("2026-08-19T11:00:00Z")
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["refresh_requested"] == "2026-08-19T11:00:00Z"
	assert state["state"] == "idle", "the ask changed the runner's state"
	assert work_snapshot(world) == before
	assert born["work_id"]


def test_publishing_the_inventory_answers_the_ask(world):
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"]
	asked = pending_refresh(world)
	answer = facts(world, version="1.4.1",
	               answers=asked["generation"])
	assert answer["answered"] is True
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"] \
		is None


def test_a_publication_that_answers_nothing_acknowledges_nothing(world):
	"""R25: an adapter that never saw the question has not answered it,
	however new its facts are. Startup inventories are exactly this."""
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	answer = facts(world, version="1.4.1")
	assert answer["answered"] is False
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"]


def test_answering_a_superseded_generation_leaves_the_current_one(world):
	"""A late answer to a question the operator already replaced is not
	an error — but it is not an answer to the standing one either."""
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	stale = pending_refresh(world)["generation"]
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	current = pending_refresh(world)["generation"]
	assert current > stale
	assert facts(world, version="1.4.1",
	             answers=stale)["answered"] is False
	assert pending_refresh(world)["generation"] == current
	assert facts(world, version="1.4.2",
	             answers=current)["answered"] is True
	assert pending_refresh(world) is None


def test_a_generation_is_a_positive_sequence(world):
	start(world)
	with pytest.raises(bw.WorkError, match="positive generation"):
		facts(world, version="1.4.1", answers=0)


def test_a_refresh_needs_an_adapter_to_hear_it(world):
	with pytest.raises(bw.WorkError, match="no live runtime lease"):
		tr.runtime_refresh(world["store"], actor_team="lang",
		                   actor="ada", target="lang.grace")
	start(world)
	tr.runtime_end(world["store"], actor_team="lang", actor="ada",
	               incarnation="run-1")
	with pytest.raises(bw.WorkError, match="no live runtime lease"):
		tr.runtime_refresh(world["store"], actor_team="lang",
		                   actor="grace", target="lang.ada")


def test_asking_is_not_workflow_authority(world):
	"""'Any configured member may ask' — a diagnostic request grants
	nothing and moves nothing."""
	born = make_work(world)
	tr.claim_work(world["store"], born["work_id"], actor_team="lang",
	              actor="ada")
	start(world)
	before = work_snapshot(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	assert work_snapshot(world) == before
	detail = pj.detail(world["store"], born["work_id"],
	                   viewer_team="lang", viewer_member="grace")
	assert "runtime_refresh" not in detail["available_transitions"]


def test_member_details_show_the_inventory_with_its_provenance(world):
	start(world, session="01a01552")
	facts(world, source="configured", workdir="/home/op/src/baton",
	      log="/var/log/bridge.log")
	view = _console(world)
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	lines = _painted(view, height=40)
	assert any("Workdir" in line and "/home/op/src/baton" in line
	           and "configured" in line for line in lines), lines
	assert any("Log" in line and "/var/log/bridge.log" in line
	           for line in lines), lines


def test_the_details_disclose_an_outstanding_refresh(world):
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	view = _console(world)
	while view.tab != "teams":
		view.handle(NEXT_TAB)
	assert any(line.strip().startswith("Refresh") and "asked at" in line
	           for line in _painted(view, height=40)), \
		_painted(view, height=40)


def test_the_ordinary_reads_stay_cheap(world):
	"""'Keep provider-specific or expensive inspection off the ordinary
	Jobs/Teams reads.' The inventory is stored state, so a Teams read
	costs one more query per member and never a provider call."""
	start(world)
	facts(world, version="1.4.0")
	calls = []
	real = world["store"].conn

	class Counting:
		def __init__(self, wrapped):
			self._wrapped = wrapped

		def execute(self, sql, *args, **kwargs):
			calls.append(sql)
			return self._wrapped.execute(sql, *args, **kwargs)

		def __getattr__(self, name):
			return getattr(self._wrapped, name)

	world["store"].conn = Counting(real)
	try:
		pj.teams(world["store"], viewer_team="lang",
		         viewer_member="ada")
	finally:
		world["store"].conn = real
	assert not any("poke" in sql and "provider" in sql for sql in calls)
	assert any("runtime_facts" in sql for sql in calls)


def test_the_refresh_request_is_offered_to_the_adapter_that_polls(world):
	"""R18: the request reaches an adapter through the ONE projection a
	bridge already polls, declares that it wakes no model, and is
	level-triggered — offered while it stands, gone when answered."""
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	actions = pj.participant_actions(
		world["store"], viewer_team="lang",
		viewer_member="ada")["actions"]
	entry = next(action for action in actions
	             if action["kind"] == "runtime_refresh")
	assert entry["incarnation"] == "run-1"
	assert entry["wakes_model"] is False
	assert entry["action_key"] == \
		f"runtime-refresh:run-1:{entry['generation']}"
	# level-triggered: still offered on the next poll
	again = pj.participant_actions(world["store"], viewer_team="lang",
	                               viewer_member="ada")["actions"]
	assert any(action["kind"] == "runtime_refresh" for action in again)
	facts(world, version="1.4.1", answers=entry["generation"])
	after = pj.participant_actions(world["store"], viewer_team="lang",
	                               viewer_member="ada")["actions"]
	assert not [action for action in after
	            if action["kind"] == "runtime_refresh"]


def test_a_newer_request_survives_an_older_publication(world):
	"""The race the review names: a fact publication already in flight
	must not silently answer a refresh asked after it was queued."""
	at("2026-08-19T10:00:00Z")
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	at("2026-08-19T10:05:00Z")
	# the operator asks again — a newer request replaces the old one
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	state = runtime(world)["lang.ada"]["runtime"]
	assert state["refresh_requested"] == "2026-08-19T10:05:00Z"
	asked = pending_refresh(world)
	assert asked["action_key"] == \
		f"runtime-refresh:run-1:{asked['generation']}"
	assert asked["generation"] == state["refresh_generation"]
	# the key carries the request GENERATION, so an adapter that
	# answered the first one has not answered this one
	facts(world, version="1.4.1", answers=asked["generation"])
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"] \
		is None


def test_a_fact_observed_before_a_newer_refresh_does_not_clear_it(world):
	"""An in-flight publication is old by when it was OBSERVED, not by
	when its queued authority write happens to commit."""
	at("2026-08-19T10:00:00Z")
	start(world)
	at("2026-08-19T10:01:00Z")
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	at("2026-08-19T10:05:00Z")
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	# Collected after the first ask but before the second, then held in
	# the publisher queue until after the second ask committed.
	facts(world, observed_at="2026-08-19T10:02:00Z", version="1.4.1")
	assert runtime(world)["lang.ada"]["runtime"]["refresh_requested"] \
		== "2026-08-19T10:05:00Z"


def test_two_same_second_refreshes_have_distinct_action_identities(world):
	"""Whole-second timestamps cannot identify ordered requests.

	A second request may race an answer to the first inside one second;
	the level-triggered consumer must still see a new action identity.
	"""
	at("2026-08-19T10:00:00Z")
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada", op_id="first-refresh")
	first = next(action["action_key"] for action in pj.participant_actions(
		world["store"], viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "runtime_refresh")
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada", op_id="second-refresh")
	second = next(action["action_key"] for action in pj.participant_actions(
		world["store"], viewer_team="lang", viewer_member="ada")["actions"]
		if action["kind"] == "runtime_refresh")
	assert second != first, "the newer request reused the delivered action key"


def test_the_refresh_signal_never_reaches_the_operator_inbox(world):
	"""It is addressed to a machine. Putting it in front of a human
	would be asking them to do the adapter's job."""
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	for member in ("ada", "grace"):
		rows = pj.inbox(world["store"], viewer_team="lang",
		                viewer_member=member)["rows"]
		assert not [row for row in rows
		            if row["kind"] == "runtime_refresh"], member


def test_the_observation_instant_is_the_adapters_not_the_commits(world):
	"""R20: these writes queue and retry, so commit time can make an old
	observation look newer than it is."""
	at("2026-08-19T10:00:00Z")
	start(world)
	at("2026-08-19T10:09:00Z")
	facts(world, observed_at="2026-08-19T10:02:00Z", version="1.4.0")
	held = inventory(world)
	assert held["version"]["observed_at"] == "2026-08-19T10:02:00Z"
	assert held["version"]["age_seconds"] == 420


def test_an_observation_instant_is_bounded_on_both_sides(world):
	at("2026-08-19T10:00:00Z")
	start(world)
	at("2026-08-19T10:05:00Z")
	with pytest.raises(bw.WorkError, match="later than now"):
		facts(world, observed_at="2026-08-19T11:00:00Z", version="x")
	with pytest.raises(bw.WorkError, match="precedes this lease"):
		facts(world, observed_at="2026-08-19T09:00:00Z", version="x")
	assert inventory(world) == {}


def test_no_fact_is_called_stale_merely_for_being_older_than_now(world):
	"""R20: a boolean true of every fact the moment after it is written
	says nothing. The age is exposed; a verdict needs a ruled threshold
	that does not exist yet."""
	start(world)
	facts(world, version="1.4.0")
	entry = inventory(world)["version"]
	assert "stale" not in entry, entry
	assert entry["age_seconds"] >= 0


def test_an_exact_retry_replays_the_generation_it_minted(world):
	"""R25: effectively-once, at whole-second resolution. A retry that
	could not tell the clock had not moved must not mint a second
	request, and must be told which generation its first attempt got."""
	at("2026-08-19T10:00:00Z")
	start(world)
	first = tr.runtime_refresh(world["store"], actor_team="lang",
	                           actor="grace", target="lang.ada",
	                           op_id="ask-once")
	again = tr.runtime_refresh(world["store"], actor_team="lang",
	                           actor="grace", target="lang.ada",
	                           op_id="ask-once")
	assert again["generation"] == first["generation"]
	assert again["seq"] == first["seq"], "a retry minted a second ask"


def test_a_distinct_operation_mints_a_new_generation_in_the_same_second(world):
	at("2026-08-19T10:00:00Z")
	start(world)
	first = tr.runtime_refresh(world["store"], actor_team="lang",
	                           actor="grace", target="lang.ada",
	                           op_id="ask-one")
	second = tr.runtime_refresh(world["store"], actor_team="lang",
	                            actor="grace", target="lang.ada",
	                            op_id="ask-two")
	assert second["generation"] > first["generation"]
	assert second["requested_at"] == first["requested_at"], \
		"this test is only meaningful inside one second"


def test_an_answer_retried_after_a_newer_ask_stays_answered(world):
	"""The publication committed once; a retry of the SAME operation
	replays that result rather than re-deciding it against a request
	the adapter has still never seen."""
	start(world)
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	answered = pending_refresh(world)["generation"]
	first = facts(world, version="1.4.1", answers=answered,
	              op_id="answer-once")
	assert first["answered"] is True
	tr.runtime_refresh(world["store"], actor_team="lang", actor="grace",
	                   target="lang.ada")
	replay = facts(world, version="1.4.1", answers=answered,
	               op_id="answer-once")
	assert replay["answered"] is True and replay["seq"] == first["seq"]
	# and the newer ask is untouched by that replay
	assert pending_refresh(world)["generation"] > answered
