"""THE fixture — one scripted authority state every Gate A/B suite shares.

Same-fixture parity is a pinned ruling: the TUI and JSON suites must drive
THIS state, not private lookalikes that agree today and drift tomorrow. The
scenario is the finding's own: a Lang epic with children, three consumer
teams converged on it, tags of every kind, obligations in every state, and
seen cursors at known positions.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import transitions as tr                      # noqa: E402


def build(path: str) -> dict:
	"""Returns the cast of ids the assertions use."""
	store = bw.Authority.init(path)
	for team, members in (("lang", ["ada", "grace"]), ("push", ["sl"]),
	                      ("web", ["wren"]), ("mdb", ["mo"])):
		store.register_team(team, team.title())
		for member in members:
			store.register_member(team, member, member.title())
	for team in ("lang", "push", "web", "mdb"):
		store.register_kind(team, "bug", "Bug intake")
	store.register_kind("lang", "rsrch", "Research")
	store.register_kind("lang", "impl", "Implementation")
	store.register_kind("lang", "rev", "Review")

	cast = {}
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

	# Tags in every shape: a broadcast include, one answered request, one
	# pending request, and a pass that plants a planned return.
	tr.post_message(store, cast["lang42"], author_team="lang", author="ada",
	                body="tracking the converged reports", include="*.bug")
	pending = tr.post_message(store, cast["lang42"], author_team="lang",
	                          author="ada", body="can push retest?",
	                          request="push.bug")
	cast["pending_obligation"] = pending["seq"]
	answered = tr.post_message(store, cast["lang42"], author_team="lang",
	                           author="ada", body="web: still crashing?",
	                           request="web.bug")
	tr.respond_obligation(store, answered["seq"], team="web", member="wren",
	                      body="yes, trace attached")
	tr.post_message(store, cast["step_fix"], author_team="lang", author="ada",
	                body="take it", pass_to="lang.impl", set_next="lang.rev")

	# One member has read part of the epic; everyone else is behind.
	tr.mark_seen(store, cast["lang42"], team="lang", member="ada",
	             up_to_seq=store.last_seq())
	cast["last_seq"] = store.last_seq()
	store.close()
	return cast
