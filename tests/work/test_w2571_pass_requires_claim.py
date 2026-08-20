"""W2571: a pass is the CURRENT CLAIMANT'S handoff.

`work/records/2026/08/finding-recursive-target-graph/findings/
finding-active-work-claim/findings/finding-pass-requires-current-claim/`.

The live evidence is W1568. It was rerouted to `baton.impl` through the
`impl2` alternate, which resolves to `baton.gemini`. Gemini read the
implementation, ran `just test-v11`, reported runtime state `working`,
and then committed `pass work=W1568 to=baton.bug` — on route-handler
authority alone, having never issued `claim`. The Work's event journal
contains no Gemini claim, and the Work was unclaimed throughout. An
agent completed an entire assignment lifecycle without ever becoming
Handler, so canonical state said nobody had worked on it while the
runtime log and the filesystem said otherwise.

That was not a missing guard. W171 R1 corrected the DIFFERENT case of a
route peer passing underneath somebody else's active claim, and
deliberately preserved the older unclaimed-pass authority. This record
supersedes that half: route eligibility says who MAY claim, and was
never a licence to hand on Work one is not doing. Handing something on
means having held it.

Two operations, two authorities, and they do not overlap: `pass` is the
claimant's handoff on the claimant's authority; `reroute` moves
unclaimed Work on the OWNING TEAM's. Nobody fakes a claim to redirect a
queue.
"""

from __future__ import annotations

import hashlib
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


def document():
	"""Two handlers on one route, plus an alternate — the exact shape of
	the live incident, where `impl2` resolved to a second agent that
	could act on Work the primary was not holding."""
	base = fx.config_document(
		{"lang": {"members": {"ada": ["dev"], "gem": ["dev"]},
		          "kinds": ["bug", "rev"]},
		 "push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]}})
	lang = base["teams"]["lang"]
	lang["routes"] = {"main": {"role": "dev", "handlers": ["ada", "gem"]},
	                  "alt": {"role": "dev", "handlers": ["gem"]}}
	lang["kinds"]["bug"] = {"display": "Bug", "route": "main",
	                        "alternates": ["alt"]}
	lang["kinds"]["rev"] = {"display": "Rev", "route": "main"}
	return base


@pytest.fixture()
def world(tmp_path):
	config_path = os.path.join(str(tmp_path), "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		_json.dump(document(), handle, indent=2, sort_keys=True)
	database = lc.init_from_config(config_path,
	                               participant="lang.ada")["database"]
	store = bw.Authority(database)
	yield {"store": store, "config": config_path, "database": database}
	store.close()


def make(world, title="the assigned work"):
	return tr.create_work(world["store"], team="lang", kind="bug",
	                      title=title, origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")["work_id"]


def row(world, work):
	return dict(world["store"].conn.execute(
		"SELECT * FROM work WHERE id=?", (work,)).fetchone())


def digest(world):
	world["store"].conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
	with open(world["database"], "rb") as handle:
		return hashlib.sha256(handle.read()).hexdigest()


# -- the ruling --------------------------------------------------------------

def test_an_eligible_handler_cannot_pass_work_it_has_not_claimed(world):
	"""The defect itself. `ada` is the resolved handler of this Work's
	route and could do everything else with it — and still may not hand
	it on, because there is nothing to hand on."""
	work = make(world)
	assert row(world, work)["handler_team"] is None
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="reviewed and handing on")


def test_the_refusal_names_the_claim_and_the_alternative(world):
	"""A refusal that does not say what to do instead teaches nothing.
	Both routes out are named: claim it if you are executing it, or
	reroute it if you are moving a queue."""
	work = make(world)
	with pytest.raises(bw.WorkError) as refused:
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="on you now")
	message = str(refused.value)
	assert "claim it first" in message, message
	assert "reroute" in message, message


def test_the_claimant_passes_exactly_as_before(world):
	"""The positive half, unchanged: claim, then hand on — one atomic
	act that moves the route, releases the claim, and records its
	evidence."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	passed = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="ada", to="lang.rev",
	                      comment="reviewed and handing on")
	assert passed["kind"] == "pass"
	assert passed["destination_phase"] == "queued"
	after = row(world, work)
	assert after["handler_team"] is None, "the pass kept the claim"
	assert (after["route_team"], after["route_kind"]) == ("lang", "rev")
	event = next(entry for entry in world["store"].events()
	             if entry["seq"] == passed["seq"])
	assert event["payload"]["comment"] == "reviewed and handing on"


def test_a_route_peer_still_cannot_pass_underneath_a_claimant(world):
	"""W171 R1's half of the rule is untouched, and the two refusals stay
	distinguishable: this one names the recorded executor, the unclaimed
	one names the missing claim. Both say the same thing from opposite
	sides — the actor releasing the claim must be the actor holding it."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	assert "gem" in pj.detail(world["store"], work, viewer_team="lang",
	                          viewer_member="gem")["route"]["handlers"], \
		"the peer is not eligible, so this proves nothing about peers"
	with pytest.raises(bw.WorkError, match="actively claimed by lang.ada"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="gem",
		             to="lang.rev", comment="mine now")
	assert row(world, work)["handler_member"] == "ada"


def test_reroute_also_refuses_underneath_a_claimant(world):
	"""The escape hatch is not one: a peer cannot route around the claim
	either, so `reroute` is for work NOBODY holds and nothing else."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	with pytest.raises(bw.WorkError, match="claimed by lang.ada"):
		tr.reroute_work(world["store"], work, actor_team="lang",
		                actor="gem", to="lang.bug", route="alt",
		                reason="taking it")


def test_a_second_handler_of_the_same_route_is_refused_while_unclaimed(
		world):
	"""The live incident's exact shape: the Work sits on the `alt` route
	whose handler is `gem`, gem is genuinely eligible, and gem still
	cannot pass it without claiming."""
	work = make(world)
	tr.reroute_work(world["store"], work, actor_team="lang", actor="ada",
	                to="lang.bug", route="alt",
	                reason="offered to the backup route")
	assert pj.detail(world["store"], work, viewer_team="lang",
	                 viewer_member="gem")["route"]["handlers"] == ["gem"]
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="gem",
		             to="lang.rev", comment="reviewed; handing back")
	tr.claim_work(world["store"], work, actor_team="lang", actor="gem")
	passed = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="gem", to="lang.rev",
	                      comment="reviewed; handing back")
	assert passed["kind"] == "pass"


def test_route_eligibility_is_checked_before_the_claim(world):
	"""Two independent gates, in the order that answers the more
	fundamental question first: somebody who is not a handler at all
	learns that, rather than being told to claim Work they could never
	claim."""
	work = make(world)
	with pytest.raises(bw.WorkError, match="not a resolved handler"):
		tr.pass_work(world["store"], work, actor_team="push", actor="sl",
		             to="lang.rev", comment="not mine")


# -- the refusal is side-effect-free ----------------------------------------

def test_the_refusal_changes_no_authority_byte(world):
	"""Atomicity at the strongest available resolution: the database
	file itself is identical after the refusal."""
	work = make(world)
	before = digest(world)
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="on you now")
	assert digest(world) == before, "the refused pass wrote a byte"


def test_the_refusal_moves_no_work_state_event_or_episode(world):
	"""Every axis the acceptance boundary names, compared field by field
	rather than by spot-check — route, phase, handler, next, episode and
	the event journal all hold still."""
	work = make(world)
	before_row = row(world, work)
	before_events = world["store"].events()
	before_seq = world["store"].last_seq()
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="on you now",
		             set_next="lang.bug")
	assert row(world, work) == before_row
	assert world["store"].events() == before_events
	assert world["store"].last_seq() == before_seq


def test_the_refusal_moves_no_message_or_personal_count(world):
	"""A pass is threadless (W171), and so is its refusal."""
	work = make(world)
	before = {
		"messages": world["store"].conn.execute(
			"SELECT COUNT(*) AS n FROM messages").fetchone()["n"],
		"obligations": world["store"].conn.execute(
			"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"],
		"new": {key: value for key, value in pj.new_count(
			world["store"], work, viewer_team="lang",
			viewer_member="gem").items() if key != "snapshot_seq"},
	}
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="on you now")
	assert {
		"messages": world["store"].conn.execute(
			"SELECT COUNT(*) AS n FROM messages").fetchone()["n"],
		"obligations": world["store"].conn.execute(
			"SELECT COUNT(*) AS n FROM obligations").fetchone()["n"],
		"new": {key: value for key, value in pj.new_count(
			world["store"], work, viewer_team="lang",
			viewer_member="gem").items() if key != "snapshot_seq"},
	} == before


def test_the_refusal_does_not_consume_the_operation_id(world):
	"""WS-5's rule holds for this refusal like every other: an identity
	spent on something that did not commit would make the honest retry
	refuse as a conflict, and the operator would have to invent a new id
	to do the thing they always meant."""
	work = make(world)
	with pytest.raises(bw.WorkError, match="is unclaimed"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="on you now", op_id="hand-1")
	assert world["store"].conn.execute(
		"SELECT COUNT(*) AS n FROM operations").fetchone()["n"] == 0, \
		"the refusal consumed the operation identity"
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	corrected = tr.pass_work(world["store"], work, actor_team="lang",
	                         actor="ada", to="lang.rev",
	                         comment="on you now", op_id="hand-1")
	assert corrected["operation"] == {"id": "hand-1",
	                                  "state": "committed"}


def test_the_committed_retry_still_replays_after_the_claim_is_gone(world):
	"""The pass releases the claim, so an exact retry necessarily arrives
	at UNCLAIMED Work. It must still replay: WS-5 answers a committed
	identity inside the write transaction, before the claim gate runs,
	so a retry is a read of what happened and never a second act."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	first = tr.pass_work(world["store"], work, actor_team="lang",
	                     actor="ada", to="lang.rev", comment="over",
	                     op_id="hand-2")
	assert row(world, work)["handler_team"] is None
	before = digest(world)
	again = tr.pass_work(world["store"], work, actor_team="lang",
	                     actor="ada", to="lang.rev", comment="over",
	                     op_id="hand-2")
	assert again["seq"] == first["seq"]
	assert again["operation"]["state"] == "replayed"
	assert digest(world) == before, "the replay wrote a byte"


# -- unclaimable work names the operation that can move it -------------------

@pytest.mark.parametrize("phase", ["block", "parked"])
def test_unclaimable_work_is_refused_and_pointed_at_reroute(world, phase):
	"""Discovered while implementing: blocked and parked Work is
	unclaimed AND unclaimable — a gate arriving releases the claimant,
	and neither phase can be claimed — so "claim it first" would be an
	instruction nobody can follow. The refusal names the phase and the
	one operation that CAN move it."""
	work = make(world)
	if phase == "block":
		tr.add_dependency(world["store"], work, make(world, "the gate"),
		                  actor_team="lang", actor="ada",
		                  rationale="waits on it")
	else:
		tr.set_phase(world["store"], work, actor_team="lang", actor="ada",
		             phase="parked", reason="deferred deliberately")
	assert row(world, work)["phase"] == phase
	with pytest.raises(bw.WorkError,
	                   match=f"unclaimed and {phase}") as refused:
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="over")
	assert "reroute" in str(refused.value)
	with pytest.raises(bw.WorkError, match="cannot be claimed"):
		tr.claim_work(world["store"], work, actor_team="lang", actor="ada")


def test_a_gate_arriving_on_claimed_work_ends_its_passability(world):
	"""The two rules meeting, in one sequence. The claimant could pass
	it a moment ago; the gate releases the claim, and now nobody can —
	which is correct, because nobody is executing gated Work."""
	work = make(world)
	tr.claim_work(world["store"], work, actor_team="lang", actor="ada")
	tr.add_dependency(world["store"], work, make(world, "late gate"),
	                  actor_team="lang", actor="ada", rationale="late")
	assert row(world, work)["handler_team"] is None, \
		"the late gate did not release the claimant"
	with pytest.raises(bw.WorkError, match="unclaimed and block"):
		tr.pass_work(world["store"], work, actor_team="lang", actor="ada",
		             to="lang.rev", comment="over")


# -- reroute remains the operation for unclaimed Work ------------------------

def test_reroute_still_moves_unclaimed_work_on_owning_team_authority(world):
	"""The other half of the ruling: nothing is lost, only relocated.
	`sl` is not a lang handler and could never pass this Work; `ada`
	moves it as a member of the owning team, without claiming."""
	work = make(world)
	moved = tr.reroute_work(world["store"], work, actor_team="lang",
	                        actor="ada", to="lang.bug", route="alt",
	                        reason="the default route's runner is idle")
	assert moved["route"] == "alt"
	assert row(world, work)["handler_team"] is None, \
		"the reroute invented a claim"
	with pytest.raises(bw.WorkError, match="owned by lang"):
		tr.reroute_work(world["store"], work, actor_team="push",
		                actor="sl", to="lang.rev", reason="not mine")


def test_the_two_operations_stay_distinguishable_in_the_journal(world):
	"""A reroute is not a pass wearing a different hat: different event
	kind, different authority, and a `reason` rather than a handoff
	`comment`."""
	work = make(world)
	rerouted = tr.reroute_work(world["store"], work, actor_team="lang",
	                           actor="ada", to="lang.bug", route="alt",
	                           reason="offered to the backup route")
	tr.claim_work(world["store"], work, actor_team="lang", actor="gem")
	passed = tr.pass_work(world["store"], work, actor_team="lang",
	                      actor="gem", to="lang.rev", comment="handing on")
	events = {entry["seq"]: entry for entry in world["store"].events()}
	assert events[rerouted["seq"]]["kind"] == "reroute"
	assert events[rerouted["seq"]]["payload"]["reason"] == \
		"offered to the backup route"
	assert "comment" not in events[rerouted["seq"]]["payload"]
	assert events[passed["seq"]]["kind"] == "pass"
	assert events[passed["seq"]]["payload"]["comment"] == "handing on"
	assert "reason" not in events[passed["seq"]]["payload"]


def test_nobody_fakes_a_claim_to_redirect_a_queue(world):
	"""The temptation the ruling closes off, stated as a test: claiming
	in order to immediately pass Work you are not executing is possible
	— Baton cannot read intent — but it is NOT required, and the journal
	tells the two apart. A reroute leaves no claim event at all."""
	work = make(world)
	tr.reroute_work(world["store"], work, actor_team="lang", actor="ada",
	                to="lang.bug", route="alt", reason="not taking it")
	kinds = [entry["kind"] for entry in world["store"].events()
	         if entry["payload"].get("work") == work]
	assert "claim" not in kinds, \
		"moving a queue required somebody to pretend to execute it"


# -- the whole lifecycle, through the public CLI -----------------------------

def test_the_assignment_lifecycle_cannot_complete_without_the_claim(world):
	"""The live incident replayed end to end, through the same public
	surface an agent uses.

	The old behaviour let an agent read the Work, run the gate, and hand
	it on with the journal recording no claim — `handler: null` from
	beginning to end. Now the lifecycle has exactly one shape: claim,
	execute, pass. The journal proves it by containing a claim for every
	transfer."""
	from baton_work import cli as work_cli
	import contextlib
	import io

	def run(*argv, viewer="lang.gem"):
		out, err = io.StringIO(), io.StringIO()
		with contextlib.redirect_stdout(out), \
				contextlib.redirect_stderr(err):
			code = work_cli.main(["--config", world["config"],
			                      "--participant", viewer] + list(argv))
		if code != 0:
			return code, _json.loads(err.getvalue())["error"]
		return code, _json.loads(out.getvalue())["result"]

	work = make(world)
	world["store"].conn.commit()
	code, error = run("reroute", f"work={work}", "to=lang.bug",
	                  "route=alt", "reason=offered to the backup route",
	                  viewer="lang.ada")
	assert code == 0, error
	# gem reviews it — and the handoff refuses, exactly as W1568's
	# should have.
	code, error = run("pass", f"work={work}", "to=lang.rev",
	                  "comment=reviewed; gate is green")
	assert code == 1
	assert "is unclaimed" in error, error
	code, claimed = run("claim", f"work={work}")
	assert code == 0, claimed
	assert claimed["claimant"] == "lang.gem"
	code, passed = run("pass", f"work={work}", "to=lang.rev",
	                   "comment=reviewed; gate is green")
	assert code == 0, passed
	code, events = run("work-events", f"work={work}", viewer="lang.ada")
	assert code == 0, events
	kinds = [entry["kind"] for entry in events["events"]]
	assert kinds.count("claim") == 1, kinds
	assert kinds.index("claim") < kinds.index("pass"), \
		"the journal records a transfer by somebody who never held it"
