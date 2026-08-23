"""THE fixture — one scripted authority state every Gate A/B suite shares.

CONFIG-BASED since C3: the instance is declared in a generation-1
`baton.json` and initialized through the bound lifecycle, exactly as
production will be — the fixture stopped using the registration API when the
CLI stopped offering it. Work/message/tag state is then driven through the
internal transitions, which C3 does not change.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402

UUID = "fe" * 16

TEAMS = {
	"lang": {"members": {"ada": ["rsrch", "impl", "rev"],
	                     "grace": ["impl"]},
	         "kinds": ["bug", "rsrch", "impl", "rev"]},
	"push": {"members": {"sl": ["dev"]}, "kinds": ["bug"]},
	"web":  {"members": {"wren": ["dev"]}, "kinds": ["bug"]},
	"mdb":  {"members": {"mo": ["dev"]}, "kinds": ["bug"]},
}


def config_document(spec_teams=None, uuid: str = UUID) -> dict:
	teams = {}
	for team, spec in (spec_teams or TEAMS).items():
		roles = sorted({role for held in spec["members"].values()
		                for role in held})
		participants = {member: {"display": member.title(),
		                         "roles": held,
		                         **({"capabilities": ["config"]}
		                            if member in ("ada", "sl", "wren", "mo",
		                                          "slaw")
		                            else {})}
		                for member, held in spec["members"].items()}
		default_role = roles[0]
		routes = {"main": {"role": default_role,
		                   "handlers": [next(
		                       member for member, held
		                       in spec["members"].items()
		                       if default_role in held)]}}
		kinds = {kind: {"display": kind.title(), "route": "main"}
		         for kind in spec["kinds"]}
		teams[team] = {"display": team.title(), "participants": participants,
		               # W101: every declared role carries durable
		               # operating instructions, so the fixture supplies
		               # them too — a config without them is refused at
		               # acceptance, which is the point.
		               "roles": {role: {
			               "display": role.title(),
			               "instructions": (
				               f"You are the {role} for {team}. Read this "
				               f"repository's policy and the operating "
				               f"guide before your first assignment, then "
				               f"act only on Work routed to you.")}
		                         for role in roles},
		               "routes": routes, "kinds": kinds}
	return {"config_version": 1, "protocol_version": 11, "generation": 1,
	        "instance": {"name": "fixture", "authority_uuid": uuid,
	                     "database": "work.sqlite3"},
	        "teams": teams}


def episode_of(store, work_id: str) -> int:
	"""TEST-ONLY: the Work's live assignment episode.

	W4303 made `episode=` a mandatory compare-and-swap operand on every
	release, so a suite that releases a claim has to name the episode
	that claim was offered under. Reading it here keeps the suites
	asserting what release DOES rather than restating how episodes are
	minted at every call site."""
	return store.conn.execute(
		"SELECT episode_seq FROM work WHERE id=?",
		(work_id,)).fetchone()["episode_seq"]


def first_participant(config_path: str) -> str:
	"""TEST-ONLY: the first config-capable member of the document (or the
	first member at all) — init's required committing identity."""
	document = json.loads(open(config_path).read())
	fallback = None
	for team, spec in document["teams"].items():
		for member, entry in spec["participants"].items():
			if fallback is None:
				fallback = f"{team}.{member}"
			if "config" in entry.get("capabilities", []):
				return f"{team}.{member}"
	return fallback


def build_instance(directory: str, spec_teams=None) -> tuple[str, str]:
	"""Write the config and initialize; returns (config_path, db_path)."""
	config_path = os.path.join(directory, "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(config_document(spec_teams), handle, indent=2,
		          sort_keys=True)
		handle.write("\n")
	result = lc.init_from_config(config_path,
	                             participant=first_participant(config_path))
	return config_path, result["database"]


def open_instance(directory: str, spec_teams=None):
	"""Init from a spec and hand back the open internal Authority — the
	config-based replacement for the retired registration fixtures."""
	_config, database = build_instance(directory, spec_teams)
	return bw.Authority(database)


def build(path: str) -> dict:
	"""Legacy entry: `path` names the desired work.sqlite3; the config is
	written beside it. Returns the cast plus `config_path`."""
	directory = os.path.dirname(os.path.abspath(path))
	config_path, database = build_instance(directory)
	assert database == os.path.abspath(path), \
		f"callers must name the fixed sibling: {database} != {path}"
	store = bw.Authority(database)

	cast = {"config_path": config_path}
	cast["lang42"] = tr.create_work(
		store, team="lang", kind="rsrch", title="parser recovery",
		origin="external-report", classification="suspected-defect", author="ada",
		body="crash reported from three consumers")["work_id"]
	cast["step_confirm"] = tr.create_work(
		store, team="lang", kind="rsrch", title="confirm the defect",
		origin="decomposition", classification="suspected-defect", author="ada", body="repro first",
		parent=cast["lang42"])["work_id"]
	cast["step_fix"] = tr.create_work(
		store, team="lang", kind="rsrch", title="implement the fix",
		origin="decomposition", classification="suspected-defect", author="ada", body="after confirmation",
		parent=cast["lang42"])["work_id"]

	cast["pushcoin"] = tr.create_work(
		store, team="push", kind="bug", title="checkout fails",
		origin="external-report", classification="suspected-defect", author="sl", body="500 at checkout")["work_id"]
	cast["web"] = tr.create_work(
		store, team="web", kind="bug", title="render crash",
		origin="external-report", classification="suspected-defect", author="wren", body="tab dies")["work_id"]
	cast["mdb"] = tr.create_work(
		store, team="mdb", kind="bug", title="driver hang",
		origin="external-report", classification="suspected-defect", author="mo", body="hangs on insert")["work_id"]

	tr.add_dependency(store, cast["pushcoin"], cast["lang42"],
	                  actor_team="push", actor="sl", rationale="test dependency")
	tr.add_dependency(store, cast["web"], cast["lang42"],
	                  actor_team="web", actor="wren", rationale="test dependency")
	tr.add_dependency(store, cast["mdb"], cast["lang42"],
	                  actor_team="mdb", actor="mo", rationale="test dependency")

	post(store, cast["lang42"], author_team="lang", author="ada",
	     body="tracking the converged reports", include="*.bug")
	pending = post(store, cast["lang42"], author_team="lang",
	               author="ada", body="can push retest?",
	               request="push.bug")
	cast["pending_obligation"] = pending["seq"]
	answered = post(store, cast["lang42"], author_team="lang",
	                author="ada", body="web: still crashing?",
	                request="web.bug")
	tr.respond_obligation(store, answered["seq"], team="web", member="wren",
	                      body="yes, trace attached")
	post(store, cast["step_fix"], author_team="lang", author="ada",
	     body="take it", pass_to="lang.impl", set_next="lang.rev")

	mark_all_seen(store, cast["lang42"], team="lang", member="ada",
	              up_to_seq=store.last_seq())
	cast["last_seq"] = store.last_seq()
	store.close()
	return cast


def born(store, work_id: str) -> str:
	"""The thread born with the Work (shares its created_seq) — a
	TEST-ONLY derivation; the public surface addresses threads
	directly."""
	return store.conn.execute(
		"SELECT threads.id AS id FROM threads JOIN work "
		"ON work.created_seq = threads.created_seq WHERE work.id=?",
		(work_id,)).fetchone()["id"]


def crew_document(team: str, members, kinds=("bug",), uuid: str = UUID):
	"""A config whose ROUTE resolves to every named member.

	W2938 gave a participant one-slot capacity, so a test that needs
	several rows claimed AT ONCE needs several claimants — the default
	spec resolves a route to one member, which is right for almost
	everything and wrong for exactly that shape. Building the crew here
	keeps those tests asking their real question (a batched read across
	many claimed rows) instead of asking it of one row."""
	base = config_document({team: {"members": {name: ["dev"]
	                                           for name in members},
	                               "kinds": list(kinds)}}, uuid=uuid)
	spec = base["teams"][team]
	spec["routes"] = {"main": {"role": "dev", "handlers": list(members)}}
	spec["kinds"] = {kind: {"display": kind.title(), "route": "main"}
	                 for kind in kinds}
	return base


def build_crew(directory: str, team: str, members, kinds=("bug",)):
	"""`crew_document` written and initialized; returns (config, db)."""
	from baton_work import lifecycle as _lc
	config_path = os.path.join(directory, "baton.json")
	with open(config_path, "w", encoding="utf-8") as handle:
		json.dump(crew_document(team, members, kinds), handle, indent=2,
		          sort_keys=True)
		handle.write("\n")
	result = _lc.init_from_config(
		config_path, participant=f"{team}.{list(members)[0]}")
	return config_path, result["database"]


def hand_off(store, work_id: str, *, actor_team: str, actor: str,
             to: str, comment: str = "handoff", claim: bool = True, **kw):
	"""TEST-ONLY: the W2571 handoff — claim it, then pass it.

	`pass` requires the actor to be the Work's current claimant, because
	handing something on means having held it
	(`finding-recursive-target-graph/findings/finding-active-work-claim/
	findings/finding-pass-requires-current-claim`, 2026-08-20). Suites
	written before that rule call `pass_work` on freshly created Work to
	MOVE it somewhere, as setup for the property they actually assert —
	route selection, phase derivation, projection columns, episodes.

	This states the claim those call sites always implied, in one place
	that says why, instead of scattering the same two lines through
	every suite that merely needed the Work somewhere else. It claims
	only when the Work is UNCLAIMED, so an explicit claim in the test
	stays the one that matters.

	`claim=False` suppresses it for the two shapes where acquiring
	anything would be wrong: an operation-id RETRY, which must change
	nothing at all, and a replay against Work that has since closed.

	Tests ABOUT pass authority — who may pass, and what an unclaimed or
	underneath-a-claimant pass does — call `transitions.pass_work`
	directly and never come through here. Routing them through a helper
	that quietly claims first is exactly how a regression for this
	defect would stop being able to fail."""
	if claim and _unclaimed(store, work_id):
		_transitions().claim_work(store, work_id, actor_team=actor_team,
		                          actor=actor)
	return _transitions().pass_work(store, work_id, actor_team=actor_team,
	                                actor=actor, to=to, comment=comment,
	                                **kw)


def _transitions():
	from baton_work import transitions as _tr
	return _tr


def _unclaimed(store, work_id: str) -> bool:
	"""TEST-ONLY: whether the Work currently records no Handler."""
	row = store.conn.execute(
		"SELECT handler_team FROM work WHERE id=?", (work_id,)).fetchone()
	return row is not None and row["handler_team"] is None


def post(store, work_id: str, **kw):
	"""TEST-ONLY adapter for WS-1-era call sites: post into the Work's
	born thread, selecting the Work explicitly for carrying
	operators. Public callers use `post_thread` directly. A pass_to=
	call site rides the W171 THREADLESS pass event (the old body
	becomes the handoff comment); everything else stays a message."""
	from baton_work import transitions as _tr
	if "pass_phase" in kw:
		# W73: the destination route decides the phase. A test that
		# still states one is asserting a contract that no longer
		# exists, and silently ignoring it would let the assertion pass
		# for the wrong reason.
		raise AssertionError(
			"pass_phase= is retired (W73): the destination route "
			"decides the handoff phase — route the destination kind at "
			"a stage role instead")
	if kw.get("pass_to"):
		# W2571: a pass is the CURRENT CLAIMANT'S handoff, so there is
		# nothing to hand on until the author holds the claim. Every
		# call site here predates that rule and meant "this author hands
		# the Work on" — which now includes holding it — so the claim is
		# stated explicitly rather than left to a contract that has
		# since changed under them. Exactly the shape of the `wait=False`
		# note below, for exactly the same reason.
		#
		# Only when UNCLAIMED, and never behind `claim=False`: a test
		# about the claim gate itself, or about an operation-id retry
		# whose second call must change nothing, states that and does
		# its own setup. The W2571 suite calls `pass_work` directly and
		# never comes through here at all.
		if kw.get("claim", True) and _unclaimed(store, work_id):
			_tr.claim_work(store, work_id, actor_team=kw["author_team"],
			               actor=kw["author"])
		return _tr.pass_work(
			store, work_id, actor_team=kw["author_team"],
			actor=kw["author"], to=kw["pass_to"],
			comment=kw.get("body") or "handoff",
			set_next=kw.get("set_next"), op_id=kw.get("op_id"),
			refs=kw.get("refs", ()))
	if kw.get("request"):
		kw.setdefault("on", work_id)
		# W159: a directed request now WAITS by default, which suspends
		# the selected Work and requires the caller to hold its claim.
		# Every call site here predates that rule and meant the
		# ASYNCHRONOUS ask — they exercise obligation mechanics, not the
		# blocking form — so the historical intent is stated explicitly
		# rather than left to a default that has since changed under
		# them. A caller that means the blocking form passes wait=True,
		# and W159's own tests call `post_thread` directly.
		kw.setdefault("wait", False)
	return _tr.post_thread(store, born(store, work_id), **kw)


def mark_all_seen(store, work_id: str, *, team: str, member: str,
                  up_to_seq: int):
	"""TEST-ONLY: advance the member's cursor on every thread
	currently labelled to the Work (the old bridge reading), via the
	public per-thread transition."""
	from baton_work import transitions as _tr
	result = None
	for row in store.conn.execute(
			"SELECT DISTINCT thread FROM thread_labels "
			"WHERE work=?", (work_id,)):
		result = _tr.seen_thread(store, row["thread"], team=team,
		                             member=member, up_to_seq=up_to_seq)
	return result
