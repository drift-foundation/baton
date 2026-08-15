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
		               "roles": {role: {"display": role.title()}
		                         for role in roles},
		               "routes": routes, "kinds": kinds}
	return {"config_version": 1, "protocol_version": 11, "generation": 1,
	        "instance": {"name": "fixture", "authority_uuid": uuid,
	                     "database": "work.sqlite3"},
	        "teams": teams}


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
		origin="external-report", author="ada",
		body="crash reported from three consumers")["work_id"]
	cast["step_confirm"] = tr.create_work(
		store, team="lang", kind="rsrch", title="confirm the defect",
		origin="decomposition", author="ada", body="repro first",
		parent=cast["lang42"])["work_id"]
	cast["step_fix"] = tr.create_work(
		store, team="lang", kind="rsrch", title="implement the fix",
		origin="decomposition", author="ada", body="after confirmation",
		parent=cast["lang42"])["work_id"]

	cast["pushcoin"] = tr.create_work(
		store, team="push", kind="bug", title="checkout fails",
		origin="external-report", author="sl", body="500 at checkout")["work_id"]
	cast["web"] = tr.create_work(
		store, team="web", kind="bug", title="render crash",
		origin="external-report", author="wren", body="tab dies")["work_id"]
	cast["mdb"] = tr.create_work(
		store, team="mdb", kind="bug", title="driver hang",
		origin="external-report", author="mo", body="hangs on insert")["work_id"]

	tr.add_dependency(store, cast["pushcoin"], cast["lang42"],
	                  actor_team="push", actor="sl")
	tr.add_dependency(store, cast["web"], cast["lang42"],
	                  actor_team="web", actor="wren")
	tr.add_dependency(store, cast["mdb"], cast["lang42"],
	                  actor_team="mdb", actor="mo")

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
	"""The discussion born with the Work (shares its created_seq) — a
	TEST-ONLY derivation; the public surface addresses discussions
	directly."""
	return store.conn.execute(
		"SELECT discussions.id AS id FROM discussions JOIN work "
		"ON work.created_seq = discussions.created_seq WHERE work.id=?",
		(work_id,)).fetchone()["id"]


def post(store, work_id: str, **kw):
	"""TEST-ONLY adapter for WS-1-era call sites: post into the Work's
	born discussion, selecting the Work explicitly for carrying
	operators. Public callers use `post_discussion` directly."""
	from baton_work import transitions as _tr
	if kw.get("request") or kw.get("pass_to"):
		kw.setdefault("on", work_id)
	return _tr.post_discussion(store, born(store, work_id), **kw)


def mark_all_seen(store, work_id: str, *, team: str, member: str,
                  up_to_seq: int):
	"""TEST-ONLY: advance the member's cursor on every discussion
	currently labelled to the Work (the old bridge reading), via the
	public per-discussion transition."""
	from baton_work import transitions as _tr
	result = None
	for row in store.conn.execute(
			"SELECT DISTINCT discussion FROM discussion_labels "
			"WHERE work=?", (work_id,)):
		result = _tr.seen_discussion(store, row["discussion"], team=team,
		                             member=member, up_to_seq=up_to_seq)
	return result
