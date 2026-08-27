"""The canonical read model — Gate A step A5.

ONE projection, two renderers. Everything the TUI will draw (Gate B) and
everything the JSON surface returns (A6) comes from here, so the two cannot
disagree without one of them bypassing this module — which the boundary test
forbids.

EVERY FUNCTION IS PURE. Nothing here writes, and the acceptance test proves
it the blunt way: the authority file's hash is identical before and after a
full sweep by every configured member. Readiness, `New`, and obligations are
READ from state the transitions maintain; the projection never recomputes
authority state, because a reader that "fixes" state on the way past is a
writer wearing a costume.

PER-VIEWER, NEVER ACCESS-RESTRICTED. `New` and the obligation set depend on
who is asking; the graph itself does not (open-graph ruling — deliberate
drill-through may expose linked reports and fan-in). The team boundary
appears in exactly one place: `New` aggregates over containment only and
counts only works the viewer's team participates in, because attention is
noise control, not a wall.
"""

from __future__ import annotations

import contextlib
import json as _json
import re

from baton_work.authority import (Authority, PICKUP_OVERDUE_DEFAULT,
                                  WorkError, dispatch_row, live_claim_rows)
# W24755 third review [P1]: the CLOSED VOCABULARIES, imported rather than
# restated. A renderer-only copy of "the four phases" would be a second
# opinion about the authority's own axis, and the two would agree until
# somebody added a fifth.
#
# NAMES ONLY, NEVER THE MODULE. `from baton_work import transitions` would put
# every mutation in this module's namespace, and this is the read side --
# `test_the_read_side_never_commits` is a source-text check and would not
# notice. `test_the_read_side_imports_only_vocabulary_from_transitions` holds
# this import to closed tuples of text, so the narrowing is a rule rather than
# a habit.
from baton_work.transitions import (CLASSIFICATIONS, CLOSED, OPEN, ORIGINS,
                                    OUTCOMES, PHASES, PRIORITIES)


class Snapshotted(list):
	"""A list read inside ONE database snapshot, carrying the sequence
	that snapshot observed — the envelope's consistency token can then
	name exactly the state the rows came from, never a later commit."""

	snapshot_seq: int = 0


@contextlib.contextmanager
def _read_snapshot(store: Authority):
	"""One pure read transaction (BEGIN … ROLLBACK), reentrant: a caller
	already holding a snapshot keeps it — nested reads join it instead of
	failing, so every canonical response derives its rows, its derived
	predicates, and its token from one database state (WS-2 R46)."""
	if store.conn.in_transaction:
		yield
		return
	store.conn.execute("BEGIN")
	try:
		yield
	finally:
		store.conn.execute("ROLLBACK")


def _work(store: Authority, work_id: str) -> dict:
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work_id,)).fetchone()
	if row is None:
		raise WorkError(f"no work {work_id!r}")
	return dict(row)


def _selected_route(row) -> str | None:
	"""The route explicitly chosen for one Work row, if any.

	A sqlite3.Row raises on an absent column rather than returning None,
	and several projections build rows from narrower SELECTs, so the
	access is guarded here once instead of at each call site."""
	try:
		return row["route_selected"]
	except (IndexError, KeyError):
		return None


def _endpoint_struct(store: Authority, team, kind,
                     selected: str | None = None) -> dict | None:
	"""Structured endpoint data, resolved against the CURRENTLY accepted
	configuration at read time (projection 2.0). History keeps the snapshot
	recorded at event time; this is the live view. An endpoint the current
	generation no longer resolves is shown explicitly unresolved — route,
	role and handlers None/empty — never silently dropped and never a bare
	string.

	W230: `selected` is the route explicitly chosen for one Work. It
	replaces the kind's default and is THE only route projected for that
	Work — the finding's rule, and the reason the choice is durable: a
	row that showed the default while the Work was actually routed
	elsewhere would send the operator to the wrong agent. A selection
	the accepted configuration no longer offers reports unresolved,
	exactly as any other stale endpoint does."""
	if not team or not kind:
		return None
	row = store.conn.execute(
		"SELECT route, retired FROM kinds WHERE team=? AND handle=?",
		(team, kind)).fetchone()
	structured = {"endpoint": f"{team}.{kind}", "route": None,
	              "role": None, "handlers": []}
	if row is None or row["retired"] or row["route"] is None:
		return structured
	handle = row["route"]
	if selected is not None and selected != handle:
		offered = [entry["route"] for entry in store.conn.execute(
			"SELECT route FROM kind_alternates WHERE team=? AND kind=?",
			(team, kind))]
		if selected not in offered:
			return structured
		handle = selected
	route = store.conn.execute(
		"SELECT role FROM routes WHERE team=? AND handle=? AND removed=0",
		(team, handle)).fetchone()
	if route is None:
		return structured
	structured["route"] = handle
	structured["role"] = route["role"]
	structured["handlers"] = [entry["member"] for entry in store.conn.execute(
		"SELECT member FROM route_handlers WHERE team=? AND route=? "
		"ORDER BY member", (team, handle))]
	return structured


def _message_count(store: Authority, work_id: str) -> int:
	"""W36 `Msg`, W179 DIRECT scope: total DISTINCT messages across the
	threads labelled DIRECTLY to this Work — exactly the conversation
	entering the Work exposes. Descendants report their own counters;
	hidden closed children never inflate a visible parent. Conversation
	volume, not unread; seen and answers never decrease it."""
	return store.conn.execute(
		"SELECT COUNT(DISTINCT messages.seq) AS n FROM messages "
		"JOIN thread_labels ON thread_labels.thread = messages.thread "
		"WHERE thread_labels.work = ?",
		(work_id,)).fetchone()["n"]


def _my_pending(store: Authority, work_id: str, viewer_team: str,
                viewer_member: str) -> int:
	"""W36 `My`: unresolved directed @ obligations in the same
	recursive scope for which THIS participant is an eligible handler
	under the CURRENTLY accepted route resolution — never inclusions,
	never another member's load, never ownership. A shared route
	obligation leaves every handler's count on any resolution;
	terminal withdrawal removes it likewise. W179: the scope is the
	Work's DIRECTLY labelled threads — the same visible scope as Msg
	and New; a thread deliberately reused by several Works contributes
	to each direct view."""
	count = 0
	eligible: dict = {}
	# EVERY pending directed flavor the participant can discharge
	# counts (R1): response (respond/dispose/accept) AND verification
	# (report) — each keeps its own completion transition; withdrawal
	# clears either.
	# Thread-borne obligations (@ requests) count through the direct
	# thread labels; thread-less directed obligations (verification
	# assignments) belong to their own Work directly — neither is ever
	# aggregated from descendants.
	for entry in store.conn.execute(
			"SELECT DISTINCT obligations.seq, obligations.team, "
			"obligations.kind FROM obligations "
			"LEFT JOIN thread_labels "
			"ON thread_labels.thread = obligations.thread "
			"WHERE obligations.status='pending' AND "
			"(thread_labels.work = ? OR (obligations.thread IS NULL "
			"AND obligations.work = ?))", (work_id, work_id)):
		key = (entry["team"], entry["kind"])
		if key not in eligible:
			resolved = _endpoint_struct(store, entry["team"],
			                            entry["kind"])
			eligible[key] = (entry["team"] == viewer_team and
			                 resolved is not None and
			                 viewer_member in resolved["handlers"])
		if eligible[key]:
			count += 1
	return count


# W5 (ruled): the ONE closed filter vocabulary over existing canonical
# Work facts — deterministic field order, AND composition, at most one
# value per field. No comma syntax, negation, comparison, or OR
# language; compact TUI display spellings are refused as input.
# W245: `route` and `current` are DIFFERENT questions and both are
# filterable. route=me means "I am eligible to claim this"; handler=me
# means "I hold the claim". Conflating them is what this finding fixes.
FILTER_FIELDS = ("team", "status", "phase", "route", "handler", "category",
                 "ready", "new", "priority")


def normalize_filter(store: Authority, active, viewer_team: str):
	"""Validate and canonically order a filter mapping. Field
	vocabulary is enforced by the shared grammar; this boundary adds
	the store-dependent refusals — an unknown team handle and an
	unresolvable route endpoint refuse BEFORE any plausible partial
	view is produced. Returns the ordered {field: value} dict, or None
	for an empty filter."""
	if not active:
		return None
	unknown = set(active) - set(FILTER_FIELDS)
	if unknown:
		raise WorkError(f"unknown filter field "
		                f"{sorted(unknown)[0]!r}; filters cover "
		                f"{', '.join(FILTER_FIELDS)}")
	if "team" in active:
		if not store.conn.execute(
				"SELECT 1 FROM teams WHERE handle=?",
				(active["team"],)).fetchone():
			raise WorkError(f"filter team={active['team']!r} is not a "
			                f"configured team")
	if "route" in active and active["route"] != "me":
		team, dot, kind = active["route"].partition(".")
		known = dot and store.conn.execute(
			"SELECT 1 FROM kinds WHERE team=? AND handle=?",
			(team, kind)).fetchone()
		if not known:
			raise WorkError(
				f"filter route={active['route']!r} is neither a "
				f"configured TEAM.KIND endpoint nor me")
	if "handler" in active and active["handler"] != "me":
		# W245: current is a PARTICIPANT, so an endpoint spelling here
		# is the exact stale-consumer mistake this finding removes —
		# refuse it by name rather than silently matching nothing.
		team, dot, member = active["handler"].partition(".")
		# W245 R1: EVER known, not currently live. A later accepted
		# generation may retire a member while the claim they hold is
		# preserved by ruling — so the authority can truthfully project
		# `current.participant = "lang.bee"` while `bee` is removed. A
		# `removed=0` gate here made that retained Current impossible to
		# query, which is the one state the filter most needs to reach.
		known = dot and store.conn.execute(
			"SELECT 1 FROM members WHERE team=? AND handle=?",
			(team, member)).fetchone()
		if not known:
			endpoint = dot and store.conn.execute(
				"SELECT 1 FROM kinds WHERE team=? AND handle=?",
				(team, member)).fetchone()
			if endpoint:
				raise WorkError(
					f"filter handler={active['handler']!r} is a TEAM.KIND "
					f"endpoint; the handler is the exact claiming "
					f"PARTICIPANT — filter eligibility with route= "
					f"instead")
			raise WorkError(
				f"filter handler={active['handler']!r} is neither a "
				f"configured TEAM.MEMBER participant nor me")
	return {field: active[field] for field in FILTER_FIELDS
	        if field in active}


def _filter_matches(row: dict, active: dict, viewer_team: str,
                    viewer_member: str) -> bool:
	"""One row against the normalized filter — canonical projected
	values only (`route=me` = the viewer is one of the endpoint's
	resolved handlers; `handler=me` = the viewer HOLDS the claim;
	`new=true` = the viewer's personal New count is nonzero)."""
	for field, value in active.items():
		if field == "team" and row["team"] != value:
			return False
		if field == "status" and row["status"] != value:
			return False
		if field == "phase" and row["phase"] != value:
			return False
		if field == "route":
			route = row["route"]
			if value == "me":
				if not (route
				        and route["endpoint"].split(".", 1)[0] == viewer_team
				        and viewer_member in (route.get("handlers") or ())):
					return False
			elif not route or route["endpoint"] != value:
				return False
		if field == "handler":
			# W245/W38: the EXACT claimant, so unclaimed Work matches
			# nothing here however eligible the viewer may be.
			handler = row["handler"]
			if value == "me":
				if not (handler and handler["team"] == viewer_team
				        and handler["member"] == viewer_member):
					return False
			elif not handler or handler["participant"] != value:
				return False
		if field == "category" and row["classification"] != value:
			return False
		if field == "ready" and bool(row["ready"]) != (value == "true"):
			return False
		if field == "new" and (row["new"] > 0) != (value == "true"):
			return False
		if field == "priority" and row["priority"] != value:
			return False
	return True


def _gate_struct(store: Authority, row) -> dict | None:
	"""W78: the ONE displayed gate holding this Work, or None.

	`kind` is `work` or `message`. A Work gate carries the blocking
	Work's canonical id and its local `W…` selector; a Message gate
	carries the source Message seq, its `M…` selector, and the pending
	obligation's identity, state and resolved endpoint — the facts Work
	detail needs without a second lookup.

	`started_at` is the instant THIS gate became the one holding the
	Work. It is the only legitimate origin for a blocked row's timer:
	`handoff_at`, `last_changed_at` and the edge's creation time each
	describe something else, and substituting one of them is exactly the
	unexplained clock this Work removes."""
	if row["gate_kind"] is None:
		return None
	gate = {"kind": row["gate_kind"],
	        "started_at": row["gate_started_at"],
	        "started_seq": row["gate_seq"],
	        "work": None, "selector": None, "message": None,
	        "obligation": None}
	if row["gate_kind"] == "work":
		gate["work"] = row["gate_work"]
		gate["selector"] = row["gate_work"].rsplit("-", 1)[1]
		return gate
	found = store.conn.execute(
		"SELECT seq, message_seq, status, team, kind, flavor "
		"FROM obligations WHERE seq=?",
		(row["gate_obligation"],)).fetchone()
	if found is None:
		return gate
	gate["message"] = found["message_seq"]
	gate["selector"] = f"M{found['message_seq']}"
	gate["obligation"] = {"seq": found["seq"],
	                      "status": found["status"],
	                      "flavor": found["flavor"],
	                      "endpoint": f"{found['team']}.{found['kind']}"}
	return gate


# W7 (finding-blocker-effective-priority), first-cut ruling 2026-08-18:
# THE one blocker predicate, written once and shared by every ordering
# surface and by the published row fact, so a bridge and a human can
# never be told a different next Work.
#
# A Work BLOCKS when it is open, ready, unclaimed, and at least one OPEN
# Work waits on it through a live dependency edge. Every clause earns
# its place:
#
# - `ready`, unclaimed, and neither blocked nor parked, because the
#   ruling scopes the preference to Work that can actually be picked up
#   now. Sorting a claimed, gated, or deliberately parked blocker forward
#   would advertise something nobody may take — the "never preempted or
#   made claimable" boundary — and it is the same eligibility test
#   `participant_actions` already applies to unclaimed Work, so the two
#   surfaces cannot disagree about who is a candidate.
# - the CONSUMER must be open. A satisfied, closed, or removed edge
#   stops counting the instant it stops holding anybody — no automatic
#   operation rewrites anything, the predicate simply stops being true.
# - the consumer need NOT be claimed. The stall this Work exists to fix
#   was an unclaimed Work sitting behind a ready blocker; requiring a
#   claimant would make the preference flicker every time a consumer was
#   claimed or released, which is the opposite of the stable ordering the
#   ruling asks for.
#
# Deliberately NOT here, because the ruling pins a BINARY preference:
# no transitive walk, no fan-out weight, no count, no cross-pool
# promotion, no second priority axis. Containment is not here either,
# and W1477 settled the acceptance question this comment used to leave
# open: an open child does NOT gate its parent's readiness, so a parent
# holds up nobody by having one. "Holds another agent" is a claim about
# a dependency somebody declared, and only dependencies make it.
_BLOCKING_PREDICATE = (
	"work.status='open' AND work.ready=1 AND work.handler_team IS NULL "
	"AND work.phase NOT IN ('block', 'parked') "
	"AND EXISTS (SELECT 1 FROM edges JOIN work AS blocked "
	"ON blocked.id = edges.work "
	"WHERE edges.blocker = work.id AND blocked.status='open')")

# The canonical Work ordering. Explicit priority is the PRIMARY pool and
# is never rewritten or inherited (rule 1); the blocker preference orders
# only WITHIN one pool (rule 2); stable creation order is the final
# tie-break (rule 4). Every human Work list and the participant readiness
# projection sort by exactly this, which is rule 5.
WORK_ORDER = ("ORDER BY CASE priority WHEN 'high' THEN 0 "
              "WHEN 'normal' THEN 1 ELSE 2 END, "
              f"CASE WHEN {_BLOCKING_PREDICATE} THEN 0 ELSE 1 END, "
              "created_seq")


def _blocking(row: dict, open_dependents: int) -> bool:
	"""The same predicate as `_BLOCKING_PREDICATE`, decided from facts a
	row already carries rather than by asking the database twice.

	`open_dependents` is exactly the EXISTS clause counted, and the row
	supplies the rest, so there is no second definition to drift."""
	return bool(open_dependents) and row["status"] == "open" \
		and bool(row["ready"]) and row["handler_team"] is None \
		and row["phase"] not in ("block", "parked")


def _first_open_blockers(store: Authority, work_ids) -> dict:
	"""W39 R1 (no-N+1): the deterministic first-open-blocker selectors
	for a WHOLE window in one batch — growing the visible tree never
	grows selector reads. Oldest open blocker per consumer, read in the
	caller's snapshot; consumers with no open blocker are absent."""
	work_ids = list(work_ids)
	if not work_ids:
		return {}
	marks = ",".join("?" * len(work_ids))
	first = {}
	for hit in store.conn.execute(
			f"SELECT edges.work AS consumer, work.id AS blocker "
			f"FROM edges JOIN work ON work.id = edges.blocker "
			f"WHERE work.status='open' AND edges.work IN ({marks}) "
			f"ORDER BY edges.work, work.created_seq",
			tuple(work_ids)):
		if hit["consumer"] not in first:
			first[hit["consumer"]] = hit["blocker"].rsplit("-", 1)[1]
	return first


def _handoffs(store: Authority, work_ids) -> dict:
	"""W226: the committed HANDOFF instant per Work — the newest
	pass/return event's transaction time, batched for a whole window in
	one statement (the W39 no-N+1 boundary), straight from the
	append-only journal. Responsibility begins at this instant, before
	any member claims. {work_id: ts}; absent for never-passed Work."""
	work_ids = list(work_ids)
	if not work_ids:
		return {}
	marks = ",".join("?" * len(work_ids))
	return {hit["consumer"]: hit["handed"]
	        for hit in store.conn.execute(
		f"WITH last_pass AS ("
		f"  SELECT json_extract(payload, '$.work') AS w, "
		f"         MAX(seq) AS s FROM events "
		f"  WHERE kind IN ('pass', 'return') "
		f"  AND json_extract(payload, '$.work') IN ({marks}) "
		f"  GROUP BY 1) "
		f"SELECT lp.w AS consumer, pe.ts AS handed "
		f"FROM last_pass lp JOIN events pe ON pe.seq = lp.s",
		work_ids)}


# W226's structured pickup threshold remains protocol-visible even though
# W65 removed every elapsed-time alert glyph: six minutes without pickup
# after a committed, currently claimable handoff is OVERDUE. No timeout
# mutates workflow authority.
PICKUP_OVERDUE_SECONDS = 360


def _pickup_state(handler_team, handoff_at, now_iso, status="open",
                  ready=True, phase=None):
	"""The structured pickup/claim state (W226): 'claimed' while an
	active claimant exists, 'pending'/'overdue' for an unclaimed
	committed handoff, None for unclaimed never-passed Work — and
	None on TERMINAL Work (R2): a pickup obligation cannot exist on
	closed Work, while handoff_at remains as history. Derived at
	snapshot time from recorded instants — never display glyphs.

	W65: 'overdue' asserts that somebody OWES a pickup, so it may only
	describe Work a pickup is actually possible on. The live defect was
	W2 reporting overdue while dependency-blocked: adding its blockers
	had correctly released the reviewer's claim, and the projection
	then went on aging the old handoff even though the authority made
	a new claim impossible. Blocked and parked Work stays
	'pending' — honestly unclaimed, with readiness/wait/phase as the
	separate structured facts that explain why it is not claimable."""
	if status == "closed":
		return None
	if handler_team is not None:
		return "claimed"
	if handoff_at is None:
		return None
	if not ready or phase in ("block", "parked"):
		return "pending"
	import datetime as _dt
	handed = _dt.datetime.fromisoformat(
		handoff_at.replace("Z", "+00:00").replace(" ", "T"))
	now = _dt.datetime.fromisoformat(
		now_iso.replace("Z", "+00:00").replace(" ", "T"))
	elapsed = max(0, int((now - handed).total_seconds()))
	return "overdue" if elapsed >= PICKUP_OVERDUE_SECONDS else "pending"


def _claimed_ats(store: Authority, work_ids) -> dict:
	"""W33+W47: the committed CURRENT-claim timestamp AND the latest
	qualifying heartbeat for a whole window in ONE batched statement
	(no per-row read, W39's boundary) — straight from the append-only
	journal, never last_changed_at. The heartbeat is scoped to the
	CURRENT claim epoch: the newest claim event per Work, then the
	newest claim/heartbeat event at or after it whose payload names
	that same exact claimant — a beat from an earlier claim can never
	make a later re-claim look healthy. Returns
	{work_id: (claimed_ts, heartbeat_ts)}; meaningful only for rows
	whose active claimant exists (the caller guards)."""
	work_ids = list(work_ids)
	if not work_ids:
		return {}
	marks = ",".join("?" * len(work_ids))
	return {hit["consumer"]: (hit["claimed"], hit["beat"])
	        for hit in store.conn.execute(
		f"WITH last_claim AS ("
		f"  SELECT json_extract(payload, '$.work') AS w, "
		f"         MAX(seq) AS s FROM events WHERE kind='claim' "
		f"  AND json_extract(payload, '$.work') IN ({marks}) "
		f"  GROUP BY 1) "
		f"SELECT lc.w AS consumer, ce.ts AS claimed, "
		f"  (SELECT hb.ts FROM events hb "
		f"   WHERE hb.kind IN ('claim', 'heartbeat') "
		f"   AND json_extract(hb.payload, '$.work') = lc.w "
		f"   AND hb.seq >= lc.s "
		f"   AND json_extract(hb.payload, '$.claimant') "
		f"       = json_extract(ce.payload, '$.claimant') "
		f"   ORDER BY hb.seq DESC LIMIT 1) AS beat "
		f"FROM last_claim lc JOIN events ce ON ce.seq = lc.s",
		tuple(work_ids))}


def _row_view(store: Authority, row: dict, viewer_team: str,
              viewer_member: str, first_blockers: dict | None = None,
              claimed_ats: dict | None = None,
              handoffs: dict | None = None,
              now: str | None = None) -> dict:
	"""One Work as a projection row: stable ids and structured values, no
	preformatted display strings (parity ruling)."""
	counts = store.conn.execute(
		"SELECT COUNT(*) AS total, "
		"SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed "
		"FROM work WHERE parent=?", (row["id"],)).fetchone()
	# W47 R2: the claim/heartbeat pair resolves EXACTLY once per row —
	# window callers pass one batched map; a single-row caller batches
	# its one id here, once, never per field.
	if row["handler_team"] is None:
		claim_fact = (None, None)
	else:
		if claimed_ats is None:
			claimed_ats = _claimed_ats(store, [row["id"]])
		claim_fact = claimed_ats.get(row["id"], (None, None))
	# W226: the committed handoff instant and the structured pickup
	# state resolve once per row from the batched journal map, against
	# ONE sampled instant per window (R1) — rows inside one snapshot
	# can never disagree at the six-minute boundary.
	if handoffs is None:
		handoffs = _handoffs(store, [row["id"]])
	if now is None:
		now = store.clock()
	handoff_at = handoffs.get(row["id"])
	pickup = _pickup_state(row["handler_team"], handoff_at, now,
	                       row["status"], ready=bool(row["ready"]),
	                       phase=row["phase"])
	open_dependents = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work "
		"ON work.id = edges.work "
		"WHERE edges.blocker=? AND work.status='open'",
		(row["id"],)).fetchone()["n"]
	return {
		"id": row["id"],
		# W4: the generated authority-local short selector — derived
		# from the canonical id's permanent sequence, never invented,
		# never reused; a convenience spelling, not a second identity.
		"local_id": row["id"].rsplit("-", 1)[1],
		"title": row["title"],
		"team": row["team"],
		"origin": row["origin"],
		"classification": row["classification"],
		# W77: phase applies only while Work is OPEN — closed Work
		# projects null ("not applicable", never omitted); the stored
		# last-phase value and audit history stay untouched.
		"phase": row["phase"] if row["status"] == "open" else None,
		# W78 (finding-unclaimed-work-cue): ONE structured current gate
		# replaces `waiting_on`. That field named the wake CONDITION but
		# never which gate was actually holding the Work or since when,
		# so a client had to combine it with `first_open_blocker` and
		# journal timestamps to explain a blocked row's clock — and
		# could not explain it at all when the displayed gate changed
		# inside `block`. Every field here is committed by the
		# authority; nothing is reconstructed and no client parses a
		# `W…`/`M…` presentation string to recover it.
		"gate": _gate_struct(store, row),
		"status": row["status"],
		"ready": bool(row["ready"]),
		"outcome": row["outcome"],
		"rationale": row["rationale"],
		"duplicate_of": row["duplicate_of"],
		"follow_up_of": row["follow_up_of"],
		# W245 (finding-current-is-claimant): ROUTE is eligibility, and
		# it is the only thing authorization resolves from.
		# W230: the Work's OWN route — its explicit selection when it has
		# one, the kind's default otherwise.
		"route": _endpoint_struct(store, row["route_team"],
		                          row["route_kind"],
		                          _selected_route(row)),
		"next": _endpoint_struct(store, row["next_team"], row["next_kind"]),
		"progress": {"children": counts["total"] or 0,
		             "closed": counts["closed"] or 0},
		# W71 (ruled): the ambiguous `dep` is REPLACED by two explicit
		# live graph fields — open work THIS row still waits on, and
		# open work depending on it (the provider's live load). The
		# journal retains every edge act.
		"open_blockers": store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges JOIN work "
			"ON work.id = edges.blocker "
			"WHERE edges.work=? AND work.status='open'",
			(row["id"],)).fetchone()["n"],
		# W39: the deterministic first OPEN blocker's local selector —
		# oldest by permanent creation order, from the same snapshot.
		# Window projections pass the ONE batched map (R1: no per-row
		# selector read); a single-row view batches its one id. None
		# when nothing open blocks this row; satisfied historical
		# edges leave the live cue and stay in the audit ledger.
		"first_open_blocker": (first_blockers if first_blockers
		                       is not None else _first_open_blockers(
		                           store, [row["id"]])).get(row["id"]),
		"open_dependents": open_dependents,
		# W7: this row is holding somebody up and can be picked up right
		# now, so it sorts ahead of free-standing Work in its own
		# explicit-priority pool. Published as a canonical BOOLEAN
		# because the ruled preference is binary — a client reads this
		# fact rather than inferring a boost from a TUI glyph, and
		# `links.blocks` already names exactly whom it is holding.
		"blocking": _blocking(row, open_dependents),
		# W179: the plain cell is the DIRECT count — the viewer's unseen
		# messages in threads labelled directly to this row, the scope
		# entering the row exposes. The recursive union stays available
		# only through the explicitly named subtree breakdown.
		"new": new_count(store, row["id"], viewer_team=viewer_team,
		                 viewer_member=viewer_member)["own"],
		# Schema 15: the team-local ordering signal (W10) and the row's
		# stable change identity (W84 groundwork) — canonical values,
		# never client-derived. Their TUI presentation is W10/W84 work.
		"priority": row["priority"],
		"last_changed_at": row["last_changed_at"],
		"last_change_seq": row["last_change_seq"],
		# finding-active-work-claim: the atomic claimant, projected so
		# nobody infers the active worker from route membership.
		# W245: this IS Current — the exact participant executing the
		# Work, NULL while unclaimed. A routed handoff awaiting pickup
		# therefore no longer reads as somebody working, which is the
		# live-trial failure this finding names. No `active` alias is
		# kept: two names for one fact preserved the ambiguity.
		"handler": None if row["handler_team"] is None else
			{"team": row["handler_team"], "member": row["handler_member"],
			 "participant": f"{row['handler_team']}.{row['handler_member']}"},
		# W93 slice 5: what the HANDLER's runner is doing, beside the
		# claim rather than inside it. Phase says the Work is being
		# executed and Handler says by whom; neither can say that the
		# held turn is sitting on an approval prompt, which is the
		# incident this finding is named for.
		#
		# Null while UNCLAIMED — an absent runner state and "nobody has
		# taken this" are different facts, and only the second one is
		# true of unclaimed Work. It is the same `_runtime_view` the
		# roster and the runtime projection use, so no surface can
		# disagree with another about a participant's runner, and none
		# of them infers it from Phase or Handler.
		"agent": None if row["handler_team"] is None else _runtime_view(
			store, row["handler_team"], row["handler_member"],
			now or store.clock()),
		# W33: when a current claimant exists, the timestamp its claim
		# landed (the newest claim event) — canonical fact only; the
		# changing age display is client-derived. Null while unclaimed,
		# after release, and on terminal rows. W47 adds heartbeat_at:
		# the latest qualifying beat of the CURRENT claim epoch (the
		# claim itself is the initial beat). W65 removed display alarms
		# derived from silence; the instant remains a structured diagnostic.
		"claimed_at": claim_fact[0],
		"heartbeat_at": claim_fact[1],
		# W226: responsibility begins at the committed handoff — the
		# instant the newest pass/return to the route endpoint
		# committed (null for never-passed Work) — and the pickup
		# state is STRUCTURED: claimed | pending | overdue | null.
		# Glyphs are TUI presentation; agents read these facts.
		"handoff_at": handoff_at,
		"pickup": pickup,
		# W36/W179: conversation VOLUME and the viewer's directed load —
		# DIRECT visible scope (the threads entering this row exposes),
		# overlap-safe, seen-independent, purely derived.
		"message_count": _message_count(store, row["id"]),
		"my_pending_obligations": _my_pending(
			store, row["id"], viewer_team, viewer_member),
	}


def home(store: Authority, *, viewer_team: str, viewer_member: str,
         work_filter=None) -> dict:
	"""The viewer's default top-level view: the team SUMMARY and the table
	of root Work owned by their team — ONE projection, one snapshot, so the
	always-visible parked count can never disagree with the rows beside it
	(WS-1 review R3). Linked external records deliberately do NOT appear in
	the rows (noise boundary); they are one `links` call away (open graph)."""
	store.conn.execute("BEGIN")
	try:
		rows = store.conn.execute(
			"SELECT * FROM work WHERE parent IS NULL AND team=? "
			+ WORK_ORDER, (viewer_team,)).fetchall()
		ids = [row["id"] for row in rows]
		first = _first_open_blockers(store, ids)
		claimed = _claimed_ats(store, ids)
		handed = _handoffs(store, ids)
		window_now = store.clock()
		views = [_row_view(store, dict(row), viewer_team, viewer_member,
		                   first_blockers=first, claimed_ats=claimed,
		                   handoffs=handed, now=window_now)
		         for row in rows]
		# W5: filtering happens INSIDE the canonical snapshot, after
		# the row facts are projected — JSON and the TUI consume the
		# same selected rows and the same normalized disclosure. The
		# team summary stays deliberately GLOBAL.
		active = normalize_filter(store, work_filter, viewer_team)
		if active:
			views = [dict(view, filter_match=True) for view in views
			         if _filter_matches(view, active, viewer_team,
			                            viewer_member)]
		summary = team_summary(store, viewer_team=viewer_team,
		                       now=store.clock())
		# W4615: the deployment-global dispatch state, from the SAME
		# read snapshot as the rows and the summary. An operator who
		# sees `PAUSED` beside a board full of queued Work is reading
		# one instant, not two.
		dispatch = dispatch_view(store)
		snapshot_seq = store.last_seq()
	finally:
		# A read transaction, rolled back: purity intact, and rows,
		# summary and snapshot_seq all describe ONE database snapshot —
		# a writer committing mid-read changes none of them (R3).
		store.conn.execute("ROLLBACK")
	return {"summary": summary, "rows": views,
	        "filter": active,
	        "dispatch": dispatch,
	        "snapshot_seq": snapshot_seq}


def search(store: Authority, query, *, viewer_team: str,
           viewer_member: str, work_filter=None, after: int = 0,
           limit: int = 100) -> dict:
	"""W6: the canonical read-only Work search — every Work OWNED by
	the viewer's team (nested Work beyond any window included; the
	team-noise boundary holds, cross-team navigation stays explicit
	links). Matching is deliberately small and predictable: case-folded
	substring on the title; case-insensitive exact/prefix on the
	canonical and authority-local identifiers. No message bodies,
	thread subjects, routes, categories, or dossier content. The
	active Work filter narrows with the same normalized AND semantics
	as home/tree; results ride stable creation order behind an
	explicit `next_after` continuation cursor (never an identity);
	everything reads from ONE snapshot and writes nothing."""
	query = (query or "").strip()
	if not query:
		raise WorkError("search needs a non-empty query=")
	if not isinstance(limit, int) or limit < 1 or limit > 500:
		raise WorkError("search limit= takes 1..500")
	folded = query.casefold()
	store.conn.execute("BEGIN")
	try:
		active = normalize_filter(store, work_filter, viewer_team)
		candidates = []
		for row in store.conn.execute(
				"SELECT * FROM work WHERE team=? ORDER BY created_seq",
				(viewer_team,)):
			title_hit = folded in row["title"].casefold()
			canonical = row["id"].casefold()
			local = canonical.rsplit("-", 1)[1]
			id_hit = canonical.startswith(folded) or 				local.startswith(folded)
			if title_hit or id_hit:
				candidates.append(dict(row))
		ids = [row["id"] for row in candidates]
		first = _first_open_blockers(store, ids)
		claimed = _claimed_ats(store, ids)
		handed = _handoffs(store, ids)
		window_now = store.clock()
		views = []
		for row in candidates:
			view = _row_view(store, row, viewer_team, viewer_member,
			                 first_blockers=first, claimed_ats=claimed,
			                 handoffs=handed, now=window_now)
			if active and not _filter_matches(view, active,
			                                  viewer_team,
			                                  viewer_member):
				continue
			if active:
				view = dict(view, filter_match=True)
			views.append((row["created_seq"], view))
		window = [entry for entry in views if entry[0] > after]
		page = window[:limit]
		next_after = page[-1][0] if len(window) > limit else None
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"query": query, "rows": [view for _seq, view in page],
	        "filter": active, "next_after": next_after,
	        "snapshot_seq": snapshot_seq}


def breadcrumb(store: Authority, work_id: str) -> list[dict]:
	"""Root-first ancestry as stable ids — the drill path, reconstructible
	from any position."""
	trail, cursor = [], work_id
	while cursor is not None:
		row = _work(store, cursor)
		trail.append({"id": row["id"], "title": row["title"]})
		cursor = row["parent"]
	return list(reversed(trail))


def children(store: Authority, work_id: str, *, viewer_team: str,
             viewer_member: str) -> list[dict]:
	# W71 R3: every row's multiple internal reads happen inside ONE read
	# snapshot — a writer committing between them cannot mix two states.
	with _read_snapshot(store):
		_work(store, work_id)
		rows = store.conn.execute(
			"SELECT * FROM work WHERE parent=? " + WORK_ORDER,
			(work_id,)).fetchall()
		ids = [row["id"] for row in rows]
		first = _first_open_blockers(store, ids)
		claimed = _claimed_ats(store, ids)
		handed = _handoffs(store, ids)
		window_now = store.clock()
		return [_row_view(store, dict(row), viewer_team, viewer_member,
		                  first_blockers=first, claimed_ats=claimed,
		                  handoffs=handed, now=window_now)
		        for row in rows]


def _children_outside(store: Authority, work_ids, inside: set) -> set:
	"""W155: which of these rows contain Work the window does not show?

	Asked of the window ACTUALLY RETURNED rather than of a depth number,
	so it stays true when the cap moves and covers the case W154 ruled
	on: a filter that removed a row's children must not also remove the
	fact that they exist.

	ONE batched statement for the whole window (the W39 R1 boundary):
	growing the visible tree never grows the number of reads."""
	work_ids = list(work_ids)
	if not work_ids:
		return set()
	marks = ",".join("?" * len(work_ids))
	return {row["parent"] for row in store.conn.execute(
		f"SELECT DISTINCT parent FROM work WHERE parent IN ({marks}) "
		f"AND id NOT IN ({marks})", tuple(work_ids) + tuple(inside))}


def tree(store: Authority, root: str | None = None, *, viewer_team: str,
         viewer_member: str, work_filter=None) -> dict:
	"""W71 R3: THE canonical bounded tree window the navigation contract
	paints — the team's roots (or one supplied re-root), their children and
	their grandchildren, the team summary, and the snapshot token, all
	derived under ONE read transaction. JSON and the TUI consume this same
	result; neither composes it from separate reads, so a writer committing
	mid-read can never produce a mixed tree.

	W155 supersedes W71's two-level visual cap with THREE levels. Two
	levels hid a common shape: a root's child waiting with no Handler
	while its own child was open and claimed, giving the operator no
	visible reason to re-root. Containment semantics are untouched — one
	parent, depth means containment and nothing else.

	Each row carries `deeper`: this row has children that this window
	does NOT contain. At the cap that is the fourth level and beyond,
	which is the case W155 names; it is also true of any row whose
	children a filter removed, because W154's ruling is that filters must
	never silently remove the fact that a visible Work has hidden
	children. Defining it against the window ACTUALLY RETURNED covers
	both without the client knowing how deep the cap is."""
	with _read_snapshot(store):
		if root is None:
			# W3: root siblings rank high, normal, low, then the stable
			# created_seq tie-break — and each child sibling group
			# below orders identically WITHOUT leaving its parent.
			bases = [dict(row) for row in store.conn.execute(
				"SELECT * FROM work WHERE parent IS NULL AND team=? "
				+ WORK_ORDER, (viewer_team,))]
		else:
			bases = [_work(store, root)]
		# W39 R1: gather the WHOLE window first, then one batched
		# blocker-selector read for all of it — row construction never
		# issues a per-row selector query.
		# W3: sibling groups order identically at every level WITHOUT
		# leaving their parent.
		order = WORK_ORDER

		def children_by_parent(parent_ids):
			"""One ordered statement for a WHOLE level, grouped by
			parent in memory.

			W155 R1: asking per parent added one statement for every
			visible row at the level above — on every two-second TUI
			refresh. The window's cost is now bounded by the number of
			LEVELS, which is what the W39 R1 no-N+1 boundary means and
			what makes a third level affordable at all."""
			parent_ids = list(parent_ids)
			if not parent_ids:
				return {}
			marks = ",".join("?" * len(parent_ids))
			grouped = {}
			for row in store.conn.execute(
					f"SELECT * FROM work WHERE parent IN ({marks}) {order}",
					tuple(parent_ids)):
				grouped.setdefault(row["parent"], []).append(dict(row))
			return grouped

		# W155: three levels, two statements. The cap lives here, in the
		# one place that builds the window, so JSON and the TUI cannot
		# disagree about how deep it goes.
		children = children_by_parent([base["id"] for base in bases])
		grandchildren = children_by_parent(
			[child["id"] for base in bases
			 for child in children.get(base["id"], ())])
		window = []
		for base in bases:
			window.append((base, 0))
			for child in children.get(base["id"], ()):
				window.append((child, 1))
				for grandchild in grandchildren.get(child["id"], ()):
					window.append((grandchild, 2))
		ids = [entry["id"] for entry, _depth in window]
		first = _first_open_blockers(store, ids)
		claimed = _claimed_ats(store, ids)
		handed = _handoffs(store, ids)
		window_now = store.clock()
		rows = [dict(_row_view(store, entry, viewer_team,
		                       viewer_member, first_blockers=first,
		                       claimed_ats=claimed, handoffs=handed,
		                       now=window_now),
		             depth=depth)
		        for entry, depth in window]
		# W5 (approved containment rule): within each bounded
		# parent/child group — a matching parent keeps only its
		# matching children; a NONmatching parent is retained as
		# structural context (filter_match: false) when at least one
		# child matches; a group with no match disappears whole.
		# Filtering never promotes a child, changes depth, or reorders.
		active = normalize_filter(store, work_filter, viewer_team)
		# W6814: the hidden active claims, and the containment path from each
		# up to a row of this window. Derived here, before the filter decides
		# what is kept, because a hidden claim that MATCHES has to retain its
		# bounded ancestors as structural context -- exactly as an ordinarily
		# visible matching descendant does. Review [P1]: leaving `rows` empty
		# and anchoring to the requested root gave the renderer no visible
		# ancestor to group under and returned an anchor that was not the
		# nearest RETURNED ancestor.
		painted = {row["id"] for row in rows}
		within = {base["id"] for base in bases}
		parents, rank, seen_under = {}, {}, {}
		for entry in store.conn.execute(
				"SELECT * FROM work WHERE team=? " + WORK_ORDER,
				(viewer_team,)):
			parents[entry["id"]] = entry["parent"]
			# The sibling's place in its parent's group, from the SAME
			# canonical order the window uses -- so a containment path built
			# from these orders exactly as the tree does.
			at = seen_under.setdefault(entry["parent"], 0)
			rank[entry["id"]] = (at,)
			seen_under[entry["parent"]] = at + 1
		hidden = _hidden_claims(store, viewer_team, painted, within, parents,
		                        WORK_ORDER)
		trail_rows = {}
		if hidden:
			# One batched read for ALL trail endpoints, the same no-N+1
			# boundary the window keeps -- and the SAME sampled `now`, so a
			# trail's claim facts are derived at the moment the rows were.
			endpoints = [claim["id"] for claim, _chain in hidden]
			trail_first = _first_open_blockers(store, endpoints)
			trail_claimed = _claimed_ats(store, endpoints)
			trail_handed = _handoffs(store, endpoints)
			trail_rows = {
				claim["id"]: _row_view(store, claim, viewer_team,
				                       viewer_member,
				                       first_blockers=trail_first,
				                       claimed_ats=trail_claimed,
				                       handoffs=trail_handed,
				                       now=window_now)
				for claim, _chain in hidden}
		matched_hidden = [
			(claim, chain) for claim, chain in hidden
			if not active or _filter_matches(trail_rows[claim["id"]], active,
			                                 viewer_team, viewer_member)]
		if active:
			# W155: the same W5 containment rule over three levels
			# instead of two. A row is kept when it matches, or when a
			# DESCENDANT inside this window matches — in which case it
			# is structural context (`filter_match: false`) so the
			# matching row keeps its place in the containment it lives
			# in. Filtering never promotes a row, changes its depth, or
			# reorders siblings.
			matches = [_filter_matches(row, active, viewer_team,
			                           viewer_member) for row in rows]
			keep = list(matches)
			# one backward pass: a kept row keeps its nearest shallower
			# ancestor, which then keeps its own, so context propagates
			# all the way up without a second scan per level.
			for index in range(len(rows) - 1, -1, -1):
				if not keep[index]:
					continue
				depth = rows[index]["depth"]
				for above in range(index - 1, -1, -1):
					if rows[above]["depth"] < depth:
						keep[above] = True
						depth = rows[above]["depth"]
						if depth == 0:
							break
			# W6814 [P1]: a hidden MATCHING claim keeps its bounded ancestors
			# too. The ruling says the containment a match lives in is
			# preserved whether the match is inside the window or below it,
			# and without this the filtered screen is empty about a handler
			# who is holding something.
			position = {row["id"]: index for index, row in enumerate(rows)}
			for _claim, chain in matched_hidden:
				for ancestor in chain:
					if ancestor in position:
						keep[position[ancestor]] = True
			rows = [dict(row, filter_match=matches[index])
			        for index, row in enumerate(rows) if keep[index]]
		# W155: `deeper` is decided LAST, against the rows this call
		# actually returns. Deciding it before the filter would answer a
		# question nobody asked — whether children exist outside the
		# unfiltered window — and would let a filter silently remove the
		# fact that a visible row has hidden children, which is exactly
		# what W154 ruled against.
		returned = {row["id"] for row in rows}
		deeper = _children_outside(store, returned, returned)
		rows = [dict(row, deeper=row["id"] in deeper) for row in rows]
		summary = _summary_in_snapshot(store, viewer_team, store.clock())
		# W6814: the trails, anchored to the rows this call ACTUALLY
		# returns and ordered by full containment.
		returned = {row["id"]: index for index, row in enumerate(rows)}
		trails = []
		for claim, chain in matched_hidden:
			anchor, hops = None, 0
			for ancestor in chain:
				if ancestor in returned:
					anchor = ancestor
					break
				hops += 1
			if anchor is None:
				continue
			trails.append({"anchor": anchor, "hidden_depth": hops + 1,
			               "work": trail_rows[claim["id"]],
			               "_path": _containment_path(claim["id"], parents,
			                                          rank)})
		# THE FULL CONTAINMENT ORDER, not the endpoints' own. Review [P1]:
		# ordering by each claim's global sibling rank let two claims under
		# different hidden branches of one anchor leapfrog their branch order.
		# The key is the whole root-to-endpoint path, so a branch orders as a
		# branch and its endpoints order inside it.
		trails.sort(key=lambda trail: (returned.get(trail["anchor"], 0),
		                               trail["_path"]))
		trails = [{name: value for name, value in trail.items()
		           if name != "_path"} for trail in trails]
		snapshot_seq = store.last_seq()
	return {"rows": rows, "summary": summary, "filter": active,
	        "active_trails": trails, "snapshot_seq": snapshot_seq}


def _hidden_claims(store, viewer_team, painted, within, parents, order):
	"""Every actively claimed Work this window HIDES, with its ancestry.

	W6814. The window is three containment levels; a Work claimed below that is
	invisible, so an operator sees a roll-up with no Handler and no reason to
	re-root while somebody is working underneath it.

	ACTIVITY IS A CLAIM. Nothing here infers it from messages or timers.

	ONE TRAIL PER HIDDEN CLAIM, EVEN WHEN THE CLAIMED WORK HAS CHILDREN
	(approved ruling): reporting only containment leaves would hide a handler
	holding a roll-up, and handlers working at the same time are exactly who
	this field exists to surface.

	Returns `(row, chain)` where the chain runs from the claim's parent upward,
	so the caller can find the nearest RETURNED ancestor after filtering.
	"""
	held = [dict(row) for row in store.conn.execute(
		"SELECT * FROM work WHERE team=? AND status='open' "
		"AND phase='active' AND handler_team IS NOT NULL " + order,
		(viewer_team,))]
	found = []
	for claim in held:
		if claim["id"] in painted:
			# ORDINARILY VISIBLE ROWS ARE NEVER DUPLICATED. The trail is for
			# what the window hides.
			continue
		chain, at, seen = [], parents.get(claim["id"]), {claim["id"]}
		inside = False
		while at is not None and at not in seen:
			seen.add(at)
			chain.append(at)
			if at in within:
				inside = True
				break
			at = parents.get(at)
		if inside:
			found.append((claim, chain))
	return found


def _containment_path(work_id, parents, rank):
	"""The root-to-this sibling-order path, for ordering a set of claims by
	the containment they live in rather than by their own priority."""
	path, at, seen = [], work_id, set()
	while at is not None and at not in seen:
		seen.add(at)
		path.append(rank.get(at, (0,)))
		at = parents.get(at)
	return tuple(reversed(path))


# W4996: the ONE bounded dependency neighborhood, read under one snapshot.
#
# `work/records/2026/08/finding-ascii-dependency-neighborhood/`, contract
# approved 2026-08-22 without amendment.
#
# WHY THIS EXISTS RATHER THAN A CLIENT-SIDE CRAWL. `links` is a one-hop
# public response and is not itself wrapped in `_read_snapshot`. A console
# calling it recursively would be unbounded in fan-out AND could combine
# different authority states if a writer committed between hops — so the
# drawn graph would be of a database that never existed at any instant.
# One bounded read here answers both.
#
# WHAT IT DOES NOT CHANGE. The dependency semantics are exactly `links`':
# `blocked_by` is EVERY recorded upstream edge, including one whose blocker
# is closed, and `blocks` is only the LIVE downstream consumers. That
# asymmetry is ruled, and a presentation read is not the place to redefine
# it — a renderer that quietly widened it would be inventing edge lifetime.
DEPENDENCY_DEPTH_MIN = 1
DEPENDENCY_DEPTH_MAX = 3
# Neighbours admitted per expanded branch before an overflow token stands
# in for the rest. One page; Enter on the token admits one more.
DEPENDENCY_BRANCH_PAGE = 4
# The adversarial bound. A neighbourhood is a view, not an export: past
# this many rendered occurrences the graph says so and stops, with the
# exact direct counts it did not draw.
DEPENDENCY_OCCURRENCE_CAP = 200


class GraphInvalid(WorkError):
	"""The projection refuses to describe a graph it cannot describe.

	A cycle, a missing endpoint, or an edge whose named endpoint disagrees
	with the row it points at is not something to drop quietly: the caller
	would then draw a smaller graph that looks complete. It fails VISIBLY,
	naming the exact edge."""


def dependency_neighborhood(store: Authority, work_id: str, *,
                            depth: int = DEPENDENCY_DEPTH_MIN,
                            expanded=None) -> dict:
	"""Blockers upstream and dependents downstream of one center.

	`expanded` maps an exact `"<work>|<side>"` branch key to how many
	neighbours that branch has been paged to; a branch not named there
	admits `DEPENDENCY_BRANCH_PAGE`. Paging is per branch on purpose — an
	operator expanding one dense blocker set has not asked to expand every
	other one.

	Expansion is DIRECTIONAL and does not turn corners. Upstream follows
	`blocked_by` recursively and downstream follows `blocks` recursively;
	neither walks from an upstream node into that node's other consumers,
	because those are a different Work's neighbourhood and are reached by
	recentering. A graph that turned corners would grow to the component
	and stop being about the center at all."""
	if not isinstance(depth, int) or isinstance(depth, bool) \
			or not DEPENDENCY_DEPTH_MIN <= depth <= DEPENDENCY_DEPTH_MAX:
		raise WorkError(
			f"dependency depth {depth!r} is outside "
			f"{DEPENDENCY_DEPTH_MIN}..{DEPENDENCY_DEPTH_MAX}")
	expanded = dict(expanded or {})
	nested = store.conn.in_transaction
	with _read_snapshot(store):
		center = _work(store, work_id)
		nodes: dict[str, dict] = {}
		edges: list[dict] = []
		seen_edges: set[tuple[str, str]] = set()
		omitted: dict[str, int] = {}
		frontier: dict[str, int] = {}
		# `fetched` and `walked` are per-RUN memos, not caches across
		# calls: a neighbourhood is one bounded read of one snapshot.
		state = {"occurrences": 1, "capped": False,
		         "fetched": {}, "walked": {}}
		nodes[center["id"]] = _graph_node(store, center)
		for side in ("upstream", "downstream"):
			_expand_dependency(store, center["id"], side, depth, expanded,
			                   nodes, edges, seen_edges, omitted, frontier,
			                   state, (center["id"],))
		# The ancestry-independent boundary, over what was actually
		# admitted. The walk's own path check cannot see a cycle the branch
		# memo answered for; this can, because it asks about the drawn graph
		# rather than about the order it was drawn in.
		_refuse_cycles(edges)
		result = {
			"center": center["id"],
			"depth": depth,
			"depth_min": DEPENDENCY_DEPTH_MIN,
			"depth_max": DEPENDENCY_DEPTH_MAX,
			"branch_page": DEPENDENCY_BRANCH_PAGE,
			"nodes": nodes,
			# Directed, and named for what the edge MEANS: the blocker
			# blocks the work. A renderer never has to decide direction.
			"edges": edges,
			# Exact DIRECT counts, per branch key. Never a guess at what
			# lies beyond them — an invented total is worse than a bound.
			"omitted": omitted,
			# What the DEPTH bound cut off, per branch key — a different
			# absence from `omitted`, opened by a different key. Never a
			# guess: it is an exact direct count of edges this view did
			# not walk.
			"frontier": frontier,
			"occurrences": state["occurrences"],
			"occurrence_cap": DEPENDENCY_OCCURRENCE_CAP,
			"capped": state["capped"],
			"expanded": expanded,
		}
		if not nested:
			result["snapshot_seq"] = store.last_seq()
	return result


def branch_key(work_id: str, side: str) -> str:
	"""The exact `(node, side)` identity a page and an overflow token share."""
	if side not in ("upstream", "downstream"):
		raise WorkError(f"dependency side {side!r} is neither upstream nor "
		                f"downstream")
	return f"{work_id}|{side}"


def _graph_node(store: Authority, row) -> dict:
	"""The bounded summary a node token draws from. Deliberately small: a
	graph is about relationships, and every extra field is width the
	selector and the label need first."""
	row = dict(row)
	return {"id": row["id"],
	        "local_id": row["id"].rsplit("-", 1)[1],
	        "title": row["title"],
	        "team": row["team"],
	        "status": row["status"],
	        "outcome": row["outcome"],
	        "phase": row["phase"] if row["status"] == "open" else None}


def _dependency_edges(store: Authority, work_id: str, side: str, limit: int):
	"""One BOUNDED hop, in the canonical direction, in stable edge order.

	Returns `(edges, total)`: at most `limit` rows, and the exact direct
	count so the omission can be reported without having seen it.

	W4996 review [P2]: this returned every direct edge as a Python list and
	the caller sliced it afterwards, so a center with adversarial fan-out
	allocated memory proportional to the WHOLE fan-out while the response
	claimed to be a bounded view. A count plus an ordered limited page gives
	the same exact number without materializing the rest.

	The two sides are NOT symmetric and that is ruled: upstream keeps every
	recorded edge including a satisfied one, downstream keeps only live
	consumers."""
	limit = max(0, int(limit))
	if side == "upstream":
		total = store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges WHERE work=?",
			(work_id,)).fetchone()["n"]
		rows = store.conn.execute(
			"SELECT blocker FROM edges WHERE work=? ORDER BY created_seq "
			"LIMIT ?", (work_id, limit))
		return [(row["blocker"], work_id) for row in rows], total
	total = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work ON work.id = edges.work "
		"WHERE edges.blocker=? AND work.status='open'",
		(work_id,)).fetchone()["n"]
	rows = store.conn.execute(
		"SELECT edges.work FROM edges JOIN work ON work.id = edges.work "
		"WHERE edges.blocker=? AND work.status='open' "
		"ORDER BY edges.created_seq LIMIT ?", (work_id, limit))
	return [(work_id, row["work"]) for row in rows], total


def _refuse_cycles(edges: list[dict]) -> None:
	"""A bounded cycle check over the ADMITTED edges, after the walk.

	W4996 re-review [P1]: `state["walked"]` answers "do this branch's
	descendants need expanding again", and that is a sound question — but
	cycle closure is a property of the ANCESTRY, which the memo does not
	carry. A node first reached where its edge is ordinary, then reached
	again with the other end of that edge among its ancestors, got a memo hit
	and returned before the path check ran. Every edge of the cycle was drawn
	and the response called itself valid.

	The path-local check STAYS: it refuses at the moment of recursion, before
	the walk can spend the view's budget descending into a loop, and it is
	what makes the walk terminate at all. This is the boundary that does not
	depend on which path arrived first — the graph as RENDERED either
	contains a cycle or it does not, and that is decidable from the edges
	alone.

	Iterative, and bounded by the occurrence cap that already bounds `edges`,
	so a damaged store cannot exhaust the interpreter's stack on the way to
	being reported. The refusal names the exact closing edge, because "this
	graph has a cycle" sends an operator looking through the whole
	neighbourhood for it.

	A cycle whose closing edge was NOT admitted — cut by the cap or a branch
	page — is deliberately not reported here: the drawn graph really is
	acyclic, and inventing a refusal about an edge the response does not
	contain would be a different kind of lie."""
	following: dict[str, list[str]] = {}
	for edge in edges:
		following.setdefault(edge["blocker"], []).append(edge["work"])
	OPEN, DONE = 1, 2
	state: dict[str, int] = {}
	for start in list(following):
		if state.get(start):
			continue
		# (node, iterator over its consumers). `ancestry` is the current
		# DFS stack as a set, so a back edge is one hop's membership test.
		stack = [(start, iter(following.get(start, ())))]
		state[start] = OPEN
		ancestry = {start}
		while stack:
			node, following_it = stack[-1]
			far = next(following_it, None)
			if far is None:
				stack.pop()
				ancestry.discard(node)
				state[node] = DONE
				continue
			if far in ancestry:
				raise GraphInvalid(
					f"dependency cycle: {node} --blocks--> {far} closes a "
					f"loop through {' -> '.join(entry for entry, _ in stack)}"
					f"; the graph refuses rather than drawing it")
			if state.get(far) == DONE:
				continue
			state[far] = OPEN
			ancestry.add(far)
			stack.append((far, iter(following.get(far, ()))))


def _expand_dependency(store, work_id, side, remaining, expanded, nodes,
                       edges, seen_edges, omitted, frontier, state, path):
	"""One directional hop, then recursion, with every bound applied here.

	`path` is the ancestry of THIS expansion, so a cycle is detected as an
	edge back into it rather than by a global visited set — a node reached
	by two different valid paths is ordinary in a DAG and must still be
	drawn.

	W4996 re-review [P1]: a DAG path is not another occurrence of a
	canonical edge. Two valid paths to one node re-expanded that node's
	identical branch: `seen_edges` suppressed the duplicate ROWS, but the
	occurrence count and the recursion ran anyway, so the second traversal
	spent the cap on edges already rendered and then overwrote the branch's
	COMPLETE result with an omission for dependents that were on screen. A
	bound that describes something other than the rendered graph is worse
	than no bound.

	Two memos close it, and they are deliberately not one global visited
	set — the review is right that a blanket node cut is not equivalent,
	because a Work legitimately appears on several edges:

	  `state["fetched"]`  the direct page already read for a `(work, side)`
	                      branch, reused rather than re-queried. This is
	                      what keeps a re-visit from recording a smaller,
	                      false omission when less room remains.
	  `state["walked"]`   the greatest `remaining` depth this branch has
	                      already been expanded with. A LATER SHORTER PATH
	                      carries more depth and is allowed through; one
	                      that can see no further is not.

	Path-local cycle detection is untouched."""
	if remaining <= 0:
		# A BRANCH ALREADY EXPANDED IN THIS RESPONSE IS NOT A FRONTIER,
		# whichever path arrived first.
		#
		# W4996 re-review [P2]: clearing the entry when a later path expands
		# a branch fixed only ONE traversal order. With the shortcut older,
		# the branch is expanded first and a later, longer path reaches it at
		# remaining zero — and recorded a frontier for edges already drawn.
		# Disclosure cannot depend on the order the edges happen to have
		# been created in, so it asks the same memo the expansion sets.
		if branch_key(work_id, side) in state["walked"]:
			return
		# THE DEPTH FRONTIER, and the reason it is reported separately from
		# a dense branch page. Two different things are missing from this
		# view and they are opened by different keys: a branch page is
		# widened with Enter, and the depth bound is lifted with `+`. One
		# token for both would make the key that opens it a guess.
		#
		# The exact direct count comes from the same bounded reader with a
		# limit of zero — a COUNT and no rows — so naming what the bound cut
		# off costs one indexed count per frontier branch and materializes
		# nothing.
		_, beyond = _dependency_edges(store, work_id, side, 0)
		if beyond:
			frontier[branch_key(work_id, side)] = beyond
		return
	key = branch_key(work_id, side)
	# A branch already expanded at least this deep has nothing more to give.
	# Strictly greater, so a shorter path reaching it later still expands.
	if state["walked"].get(key, 0) >= remaining:
		return
	state["walked"][key] = remaining
	_expand_branch(store, work_id, side, remaining, expanded, nodes, edges,
	               seen_edges, omitted, frontier, state, path, key)


def _expand_branch(store, work_id, side, remaining, expanded, nodes, edges,
                   seen_edges, omitted, frontier, state, path, key):
	"""The expansion itself, once the memo has admitted it.

	Split from the guard so that "this branch was actually expanded" is an
	observable event rather than an internal early return. The memo has no
	visible result — the same response comes back either way — so a
	regression watches this instead of asserting an outcome that cannot
	change."""
	# THIS BRANCH IS BEING EXPANDED, so it is no longer a depth frontier.
	#
	# W4996 console review [P2]: `frontier[key]` is recorded the moment a
	# visit runs out of depth, and a LATER SHORTER PATH may legitimately
	# reach the same branch with depth to spare and draw its edges. Nothing
	# cleared the earlier entry, so the graph claimed a direct dependent was
	# hidden by depth while drawing that exact edge — a bound describing
	# something other than what is on screen, which is the same defect class
	# as the shared-branch omissions.
	frontier.pop(key, None)
	page = int(expanded.get(key, DEPENDENCY_BRANCH_PAGE))
	if key in state["fetched"]:
		admitted = state["fetched"][key]
	else:
		# W4996 re-review [P2]: the SQL row limit is bounded by BOTH bounds,
		# not just the requested page. Fetching `page` rows and letting the
		# loop below stop at the occurrence cap left an expanded branch
		# materializing as much as the whole direct fan-out — the
		# count-plus-LIMIT change had moved the unbounded read one caller up
		# rather than removing it. The exact total still comes from the
		# COUNT, so the omission is disclosed without having seen the rows.
		room = max(0, DEPENDENCY_OCCURRENCE_CAP - state["occurrences"])
		admitted, total = _dependency_edges(store, work_id, side,
		                                    min(page, room))
		state["fetched"][key] = admitted
		if total > len(admitted):
			omitted[key] = total - len(admitted)
			# WHICH bound stopped it is the difference between "there is
			# more on this branch, press Enter" and "this view is full",
			# and the loop below can no longer discover the second for a
			# branch the SQL limit already trimmed.
			#
			# Re-review [P2]: `room <= page`, not `room <`. When they TIE
			# the branch was page-truncated and allowance-truncated at once
			# — the view ends at exactly the cap with an edge omitted, and
			# no later branch can admit an occurrence. Calling that ordinary
			# paging would hide that the view is full.
			if room <= page:
				state["capped"] = True
	for blocker, work in admitted:
		far = work if side == "downstream" else blocker
		drawn = (blocker, work) in seen_edges
		# CAP ADMISSION IS DECIDED FIRST, for an edge not already drawn.
		#
		# W4996 re-review [P1]: the path guard ran before this, so an edge
		# the cap was about to omit could still raise. An earlier sibling's
		# descendants can exhaust the allowance between the fetch and this
		# iteration, and the round-5 rule is that a cycle whose closing edge
		# the view never admitted is NOT reported — the graph actually
		# returned is acyclic, and refusing over an edge the response does
		# not contain is the same lie in the other direction.
		#
		# So an edge with no occurrence left is disclosed and not inspected:
		# not for a cycle, and not by recursing through it.
		if not drawn and state["occurrences"] >= DEPENDENCY_OCCURRENCE_CAP:
			# The cap is honest: the branch records what it did not draw,
			# and the response says the view cap was reached. Silence here
			# would make a truncated graph look complete.
			state["capped"] = True
			omitted[key] = (omitted.get(key, 0)
			                + (len(admitted)
			                   - admitted.index((blocker, work))))
			return
		# The edge WILL be in the response — either it is about to enter it,
		# or it is already part of the admitted graph — so the fast guard
		# applies and refuses before the walk descends into the loop.
		if far in path:
			raise GraphInvalid(
				f"dependency cycle: {blocker} --blocks--> {work} closes a "
				f"loop through {' -> '.join(path)}; the graph refuses "
				f"rather than recursing")
		if not drawn:
			row = store.conn.execute(
				"SELECT * FROM work WHERE id=?", (far,)).fetchone()
			if row is None:
				raise GraphInvalid(
					f"dependency edge {blocker} --blocks--> {work} names "
					f"{far}, which the authority does not hold; the graph "
					f"refuses rather than dropping the edge")
			if far not in nodes:
				nodes[far] = _graph_node(store, row)
			seen_edges.add((blocker, work))
			edges.append({"blocker": blocker, "work": work, "side": side})
			# ONE OCCURRENCE PER RENDERED EDGE. Counting a re-walk would
			# spend the view's budget on rows nobody sees twice.
			state["occurrences"] += 1
		_expand_dependency(store, far, side, remaining - 1, expanded, nodes,
		                   edges, seen_edges, omitted, frontier, state,
		                   (*path, far))


def links(store: Authority, work_id: str) -> dict:
	"""Typed edges with the far row's summary — the deliberate cross-team
	traversal the open-graph ruling requires, INCLUDING the provider-side
	fan-in (`blocks`): consumers discover one another here on purpose."""
	row = _work(store, work_id)

	def far(other_id: str) -> dict:
		other = _work(store, other_id)
		return {"id": other["id"], "title": other["title"],
		        "team": other["team"], "status": other["status"],
		        "outcome": other["outcome"],
		        # W30/W128: the far row's route is the OTHER Work's own
		        # route — its explicit selection when it has one. This
		        # resolution dropped the selection, so `links` reported
		        # the default while `detail` reported the alternate, and
		        # the two views disagreed about which agent a neighbour
		        # is offered to. W128's acceptance boundary requires the
		        # direct and linked views to agree, which is why it is
		        # corrected here; W30 is the record that named it first.
		        "route": _endpoint_struct(store, other["route_team"],
		                                  other["route_kind"],
		                                  _selected_route(other)),
		        "handler": None if other["handler_team"] is None else
		            {"team": other["handler_team"],
		             "member": other["handler_member"],
		             "participant": f"{other['handler_team']}."
		                            f"{other['handler_member']}"}}

	return {
		"id": work_id,
		"parent": far(row["parent"]) if row["parent"] else None,
		"contains": [far(child["id"]) for child in store.conn.execute(
			"SELECT id FROM work WHERE parent=? ORDER BY created_seq",
			(work_id,))],
		"blocked_by": [
			{**far(edge["blocker"]),
			 "via_obligation": edge["via_obligation"]}
			for edge in store.conn.execute(
				"SELECT blocker, via_obligation FROM edges WHERE work=? "
				"ORDER BY created_seq", (work_id,))],
		# The DEP drill: only the LIVE dependent set (ruled) — closed
		# consumers leave the drill; the audit retains their edges.
		"blocks": [
			{**far(edge["work"]),
			 "via_obligation": edge["via_obligation"]}
			for edge in store.conn.execute(
				"SELECT edges.work, edges.via_obligation FROM edges "
				"JOIN work ON work.id = edges.work "
				"WHERE edges.blocker=? AND work.status='open' "
				"ORDER BY edges.created_seq", (work_id,))],
		# WS-2: follow-up context is NAVIGABLE from both sides and gates
		# nothing — the relationship preserves closed history.
		# Terminal-outcome slice: the non-gating duplicate relation is
		# NAVIGABLE both ways — the duplicate names its canonical
		# survivor; the survivor lists what was folded into it.
		"duplicate_of": far(row["duplicate_of"])
		if row["duplicate_of"] else None,
		"duplicates": [far(entry["id"]) for entry in store.conn.execute(
			"SELECT id FROM work WHERE duplicate_of=? ORDER BY "
			"created_seq", (work_id,))],
		"follow_up_of": far(row["follow_up_of"])
		if row["follow_up_of"] else None,
		"follow_ups": [far(entry["id"]) for entry in store.conn.execute(
			"SELECT id FROM work WHERE follow_up_of=? ORDER BY created_seq",
			(work_id,))],
	}


MAX_PAGE = 500


def _page_bounds(after, limit) -> tuple[int, int]:
	"""R63: pagination is a CONTRACT — non-negative cursor, bounded
	positive limit, explicit continuation state on every page."""
	if not isinstance(after, int) or after < 0:
		raise WorkError("the pagination cursor is a non-negative integer")
	if not isinstance(limit, int) or limit < 1 or limit > MAX_PAGE:
		raise WorkError(f"the page limit is between 1 and {MAX_PAGE}")
	return after, limit


def completes_by(flavor: str) -> list:
	"""The declared terminal verbs for one obligation flavor.

	W228: stated ONCE. The same expression existed in two projections
	already and the Message cue would have been a third copy — three
	places to disagree about what an agent is allowed to do. Agents read
	this; they never probe by trying verbs."""
	return (["respond", "dispose", "accept"] if flavor == "response"
	        else ["report"])


def _owed_on_messages(store: Authority, thread_id: str, seqs,
                      viewer_team: str, viewer_member: str) -> dict:
	"""W228: the viewer's PENDING obligations, keyed by the Message that
	created each one.

	Viewer-relative in the same way every other actionable fact is: an
	obligation is owed by whoever its endpoint currently resolves, so
	another member's obligation does not mark this viewer's row. The
	presentation never infers one from a directed Message — a Message
	with a resolved obligation is ordinary prose again, and only
	canonical pending state says otherwise.

	One batched statement for the page (the W39 R1 boundary): the cue
	must not cost a read per Message row."""
	seqs = list(seqs)
	if not seqs:
		return {}
	marks = ",".join("?" * len(seqs))
	owed = {}
	for row in store.conn.execute(
			f"SELECT seq, message_seq, work, team, kind, flavor "
			f"FROM obligations WHERE status='pending' AND thread=? "
			f"AND message_seq IN ({marks}) ORDER BY seq",
			(thread_id, *seqs)):
		endpoint = _endpoint_struct(store, row["team"], row["kind"])
		if not endpoint or viewer_member not in (endpoint["handlers"] or ()):
			continue
		if endpoint["endpoint"].split(".", 1)[0] != viewer_team:
			continue
		owed.setdefault(row["message_seq"], {
			"seq": row["seq"], "work": row["work"],
			"flavor": row["flavor"],
			"owed_by": endpoint,
			"completes_by": completes_by(row["flavor"]),
		})
	return owed


def thread(store: Authority, thread_id: str, *, viewer_team: str,
           viewer_member: str, after: int = 0, limit: int = 500,
           before: int | None = None, newest: bool = False) -> dict:
	"""One thread, one snapshot: labels (with each Work's team and
	status), monotonic participants, the viewer's New, and a
	deterministically paginated message window with its token. Every
	supplied limit goes through the contract unchanged — no invalid
	request is a secret alias for the maximum (R68).

	W76: pagination runs in EITHER direction, always bounded to one
	page. `after` walks forward from a cursor as it always has;
	`newest=True` returns the last page of the thread, and `before=N`
	the page immediately older than sequence N. A newest-first client
	must never load an unbounded thread, nor walk every page forward,
	merely to reach the tail. Both directions return the page in
	CANONICAL ASCENDING order — display order is the client's business
	— and both carry their own continuation token: `next_after` for
	older-to-newer, `next_before` for newer-to-older."""
	after, limit = _page_bounds(after, limit)
	if before is not None and (not isinstance(before, int) or before < 0):
		raise WorkError("the pagination cursor is a non-negative integer")
	store.conn.execute("BEGIN")
	try:
		row = store.conn.execute(
			"SELECT * FROM threads WHERE id=?",
			(thread_id,)).fetchone()
		if row is None:
			raise WorkError(f"no thread {thread_id!r}")
		# Total tie-break order: (added_seq, identity) — several initial
		# labels or expanded participants may share one sequence (R63).
		labels = [dict(entry) for entry in store.conn.execute(
			"SELECT thread_labels.work AS work, work.team AS team, "
			"work.status AS status FROM thread_labels JOIN work "
			"ON work.id = thread_labels.work "
			"WHERE thread_labels.thread=? "
			"ORDER BY thread_labels.added_seq, "
			"thread_labels.work", (thread_id,))]
		participants = [entry["team"] for entry in store.conn.execute(
			"SELECT team FROM thread_participants WHERE thread=? "
			"ORDER BY added_seq, team", (thread_id,))]
		if newest or before is not None:
			# ONE bounded query from the newer end, reading at most one
			# row BEYOND the page. W76 R1: a full page is not proof that
			# another row exists, and `next_before` is a promise the TUI
			# acts on — an exact-limit Thread that advertised `n` opened
			# an empty page. The extra row is the proof; it is discarded
			# from the payload, which stays exactly `limit` long and in
			# canonical ascending order.
			if before is None:
				rows = store.conn.execute(
					"SELECT seq, author_team, author, body, ts FROM "
					"messages WHERE thread=? ORDER BY seq DESC LIMIT ?",
					(thread_id, limit + 1))
			else:
				rows = store.conn.execute(
					"SELECT seq, author_team, author, body, ts FROM "
					"messages WHERE thread=? AND seq < ? "
					"ORDER BY seq DESC LIMIT ?",
					(thread_id, before, limit + 1))
			descending = [dict(entry) for entry in rows]
			older_exists = len(descending) > limit
			newer_exists = False
			messages = descending[:limit][::-1]
		else:
			older_exists = False
			# W130: the FORWARD direction gets the same proof row the
			# reverse one has. Returning exactly `limit` rows never
			# proved another page existed, so an exact-limit final page
			# advertised a cursor whose follow-up was empty. The extra
			# row is the PROOF and is trimmed from the payload; `after`
			# stays exclusive and the order stays ascending.
			forward = [dict(entry) for entry in store.conn.execute(
				"SELECT seq, author_team, author, body, ts FROM messages "
				"WHERE thread=? AND seq > ? ORDER BY seq LIMIT ?",
				(thread_id, after, limit + 1))]
			newer_exists = len(forward) > limit
			messages = forward[:limit]
		for message in messages:
			message["references"] = [dict(ref) for ref in
			                         store.conn.execute(
				"SELECT ordinal, kind, work, binding_revision, root, "
				"path FROM act_references WHERE seq=? ORDER BY ordinal",
				(message["seq"],))]
		cursor = store.conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND "
			"thread=?",
			(viewer_team, viewer_member, thread_id)).fetchone()
		floor = cursor["seq"] if cursor else 0
		# W8 (additive): each message carries the viewer's personal
		# new-state — computed HERE against the seen cursor, so the
		# renderer formats it and never derives it.
		for message in messages:
			message["new"] = message["seq"] > floor
		# W228: the viewer's own pending obligation, on the exact
		# Message that created it. `oblig:1` in the header and a bold
		# Work row are aggregates — they say something is owed
		# somewhere, which is not the same as being able to act.
		owed = _owed_on_messages(store, thread_id,
		                         [message["seq"] for message in messages],
		                         viewer_team, viewer_member)
		for message in messages:
			message["owed"] = owed.get(message["seq"])
		unread = store.conn.execute(
			"SELECT COUNT(*) AS n FROM messages WHERE thread=? AND "
			"seq>?", (thread_id, floor)).fetchone()["n"]
		# W29: the WHOLE-thread message count, read inside the same
		# snapshot as `unread` so the pair can never disagree. The
		# loaded page is one bounded window, so a client that counted
		# `messages` would report the page and call it the thread —
		# which is exactly the defect. Clients are not asked to infer
		# it from page length, sequence numbers, or cursor presence,
		# because none of those can express it.
		total = store.conn.execute(
			"SELECT COUNT(*) AS n FROM messages WHERE thread=?",
			(thread_id,)).fetchone()["n"]
		last = store.conn.execute(
			"SELECT MAX(seq) AS m FROM messages WHERE thread=?",
			(thread_id,)).fetchone()["m"]
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	# W7: the authority-local short selector alongside canonical
	# identity — the spelling every Thread-valued command accepts.
	return {"id": thread_id,
	        "local_id": thread_id.rsplit("-", 1)[1],
	        "subject": row["subject"],
	        "labels": labels,
	        "participants": participants, "messages": messages,
	        # W130: only when the proof row showed another page exists.
	        "next_after": messages[-1]["seq"] if newer_exists else None,
	        # W76: the older-direction continuation — set ONLY when the
	        # probe row proved an older page exists, so following it can
	        # never open an empty one.
	        "next_before": messages[0]["seq"] if older_exists else None,
	        "new": unread, "total": total,
	        "last_seq": last, "snapshot_seq": snapshot_seq}


# W123 (finding-work-events-tab): the Work Events play-by-play.
#
# Association is an EXPLICIT per-kind contract, never a heuristic search
# for a Work-shaped string inside arbitrary JSON — a rationale that
# happens to quote an id must not manufacture an event on that Work.
#
# `subject` events name their Work in `payload.work`. Creation is the one
# exception: the created id is the act's RESULT, not its input, so the
# Work's own `created_seq` is the join. Dependency and acceptance acts
# genuinely affect TWO Works and attach to both with direction-specific
# roles, from the SAME authoritative event — the finding's "storage is
# not duplicated".
_EVENT_SUBJECT_KINDS = (
	"close_work", "claim", "release", "heartbeat", "set_phase",
	"prioritize", "classify", "bind_work", "revise_work", "wake",
	# W128: the owning team's route correction is a Work event, so it
	# belongs in the Work's own play-by-play beside `pass` — an
	# operator asking why this Work moved must find the answer here.
	"pass", "return", "reroute", "create_trial", "report", "assess",
	"abandon_trial", "extend_trial", "request", "respond", "dispose",
	"label", "unlabel",
)
# Pure conversation and personal cursor movement stay in Messages, by
# ruling: `post_message`, `mark_seen`, `create_thread`. Workflow-bearing
# message acts are their own kinds above and remain discoverable here
# without duplicating any message body. `accept_config` is instance-wide,
# not Work-scoped.
_EVENT_PAIR_KINDS = {
	# kind: (consumer key, other key, consumer role, other role)
	"add_dependency": ("work", "blocker", "consumer", "blocker"),
	"remove_dependency": ("work", "blocker", "consumer", "blocker"),
	"accept": ("work", "provider", "consumer", "provider"),
}
# Events that END an open claim interval for the Work they name.
_CLAIM_END_KINDS = ("release", "pass", "return", "close_work")


def _event_roles(kind: str, payload: dict, work_id: str,
                 context: dict) -> list[str]:
	"""Why this event belongs to this Work — the typed relationship, so a
	reader never has to infer it from the payload shape."""
	roles = []
	pair = _EVENT_PAIR_KINDS.get(kind)
	if pair:
		consumer_key, other_key, consumer_role, other_role = pair
		if payload.get(consumer_key) == work_id:
			roles.append(consumer_role)
		if payload.get(other_key) == work_id:
			roles.append(other_role)
	elif kind == "create_work":
		# Creation attaches to the created Work AND, when present, to
		# its parent and closed predecessor. Which one is being viewed
		# decides the role — the created Work is the subject; the other
		# two are named by the payload.
		if payload.get("parent") == work_id:
			roles.append("parent")
		if payload.get("follow_up_of") == work_id:
			roles.append("predecessor")
		if not roles:
			roles.append("subject")
	elif payload.get("work") == work_id:
		roles.append("subject")
	if kind == "close_work" and payload.get("duplicate_of") == work_id:
		roles.append("duplicate_target")
	# W123 R4: `accept` may create its provider beneath a parent. The
	# parent is a typed relation on the provider's Work ROW, not a key
	# in the accept payload, so it is resolved before we get here.
	if kind == "accept" and context.get("provider_parent"):
		roles.append("parent")
	return roles or ["subject"]


def _event_related(kind: str, payload: dict, work_id: str,
                   context: dict) -> list[dict]:
	"""The OTHER explicitly affected Works and their roles. Direction is
	preserved: `unblock work=W2 on=W76` reads, from W2, that it no longer
	waits on W76, and from W76 that it no longer blocks W2."""
	related = []

	def add(other, role):
		if other and other != work_id:
			related.append({"work": other, "role": role})

	pair = _EVENT_PAIR_KINDS.get(kind)
	if pair:
		consumer_key, other_key, consumer_role, other_role = pair
		if payload.get(consumer_key) == work_id:
			add(payload.get(other_key), other_role)
		else:
			add(payload.get(consumer_key), consumer_role)
		# W123 R4: seen from the PARENT of an accept-created provider,
		# the interesting other Work is that provider.
		if context.get("provider_parent"):
			add(context["provider_parent"], "provider")
	elif kind == "create_work":
		add(payload.get("parent"), "parent")
		add(payload.get("follow_up_of"), "predecessor")
		# W123 R1: the created Work's identity is the Work ROW whose
		# created_seq is this event — the act's result, never a payload
		# key. A parent or predecessor reading its child's birth has to
		# be told WHICH child.
		add(context.get("created"), "subject")
	elif kind == "close_work":
		# Direction matters here too. The closed Work points AT its
		# survivor; the survivor is pointed at BY the duplicate.
		if payload.get("duplicate_of") == work_id:
			add(payload.get("work"), "duplicate")
		else:
			add(payload.get("duplicate_of"), "duplicate_target")
	return related


def _claim_intervals(store: Authority, work_id: str,
                     now_iso: str) -> dict:
	"""The work-time play-by-play, keyed by the STARTING claim event.

	A `claim` opens an interval; the first later event that releases it
	closes it — an explicit release, a pass/return, a terminal close,
	entry into block or parked, or a gate that invalidated the claim
	(recorded typed in `released_claims`, never guessed). Heartbeats are
	liveness evidence INSIDE the interval and never restart it or
	fabricate work time.

	W123 R3: an OPEN interval carries its ongoing elapsed time, measured
	from the read's own instant. `started_at` stays fixed and a
	heartbeat still changes nothing — the duration grows because time
	passed, not because anything was recorded."""
	import datetime as _dt

	def instant(value):
		return _dt.datetime.fromisoformat(
			value.replace("Z", "+00:00").replace(" ", "T"))

	intervals, open_claim = {}, None
	for row in store.conn.execute(
			"SELECT seq, kind, actor, payload, ts FROM events "
			"ORDER BY seq"):
		payload = _json.loads(row["payload"])
		names_work = payload.get("work") == work_id
		released = any(entry.get("work") == work_id for entry
		               in (payload.get("released_claims") or ()))
		if row["kind"] == "claim" and names_work:
			open_claim = {"claim_seq": row["seq"],
			              "claimant": payload.get("claimant"),
			              "started_at": row["ts"], "end_seq": None,
			              "end_kind": None, "ended_at": None,
			              "elapsed_seconds": None}
			intervals[row["seq"]] = open_claim
			continue
		if open_claim is None:
			continue
		ends = released or (names_work and (
			row["kind"] in _CLAIM_END_KINDS
			or (row["kind"] == "set_phase"
			    and payload.get("to") in ("block", "parked"))))
		if ends:
			open_claim["end_seq"] = row["seq"]
			open_claim["end_kind"] = row["kind"]
			open_claim["ended_at"] = row["ts"]
			open_claim["elapsed_seconds"] = max(0, int(
				(instant(row["ts"])
				 - instant(open_claim["started_at"])).total_seconds()))
			open_claim = None
	if open_claim is not None:
		open_claim["elapsed_seconds"] = max(0, int(
			(instant(now_iso)
			 - instant(open_claim["started_at"])).total_seconds()))
	return intervals


def _phase_intervals(store: Authority, work_id: str,
                     now_iso: str) -> dict:
	"""W47: the scheduler history, keyed by the event that ENTERED each
	phase.

	Replayed from the append-only ledger's `phase_now` records, which
	every phase-changing transition writes — so this reconstructs
	nothing and re-decides nothing. An episode ends at the next event
	that records a different phase for this Work; terminal closure
	records `None` and ends the last one without opening another.

	Heartbeats never appear here, because they never record a phase.
	That is the property by construction rather than by exclusion list:
	an event that does not change the phase writes no `phase_now`, so
	it cannot split an episode.

	An OPEN episode carries its elapsed time measured from the read's
	own instant, exactly as claim intervals do; a completed one is
	fixed forever."""
	import datetime as _dt

	def instant(value):
		return _dt.datetime.fromisoformat(
			value.replace("Z", "+00:00").replace(" ", "T"))

	intervals, current = {}, None
	for row in store.conn.execute(
			"SELECT seq, kind, payload, ts FROM events ORDER BY seq"):
		payload = _json.loads(row["payload"])
		entries = [entry for entry in (payload.get("phase_now") or ())
		           if entry.get("work") == work_id]
		if not entries:
			continue
		phase = entries[-1]["phase"]
		if current is not None:
			if current["phase"] == phase:
				# the same phase recorded again is not a new episode
				continue
			current["end_seq"] = row["seq"]
			current["end_kind"] = row["kind"]
			current["ended_at"] = row["ts"]
			current["open"] = False
			current["elapsed_seconds"] = max(0, int(
				(instant(row["ts"])
				 - instant(current["started_at"])).total_seconds()))
		current = None
		if phase is None:
			continue
		current = {"phase": phase, "start_seq": row["seq"],
		           "started_at": row["ts"], "end_seq": None,
		           "end_kind": None, "ended_at": None,
		           "elapsed_seconds": None, "open": True}
		intervals[row["seq"]] = current
	if current is not None:
		current["elapsed_seconds"] = max(0, int(
			(instant(now_iso)
			 - instant(current["started_at"])).total_seconds()))
	return intervals


def work_events(store: Authority, work_id: str, *, after: int = 0,
                limit: int = 200, before: int | None = None,
                newest: bool = False) -> dict:
	"""W123: one Work's append-only operational journal.

	The global `events` read is not enough: it is not Work-relative, does
	not say WHY an event belongs to a Work, and offers no claim
	intervals. This returns each underlying event ONCE, keeping its real
	authoritative sequence, and adds `roles`, `related`, the act's own
	references, and — on claim boundaries — the structured interval.

	Paging mirrors `thread` exactly (W76): `after` walks forward,
	`newest=True` opens the last page, `before=N` the page older than N.
	Both directions read one PROOF row beyond the page, so an exactly
	full final page never advertises a continuation that opens empty.
	The payload is always canonical ascending; display order is the
	client's business."""
	after, limit = _page_bounds(after, limit)
	if before is not None and (not isinstance(before, int) or before < 0):
		raise WorkError("the pagination cursor is a non-negative integer")
	store.conn.execute("BEGIN")
	try:
		row = store.conn.execute(
			"SELECT id, created_seq, title FROM work WHERE id=?",
			(work_id,)).fetchone()
		if row is None:
			raise WorkError(f"no work {work_id!r}")
		# The explicit association predicate, expressed once. Creation
		# joins on the Work's own created_seq; subject kinds on
		# payload.work; the two-sided kinds on either end.
		subject_marks = ",".join("?" * len(_EVENT_SUBJECT_KINDS))
		pair_marks = ",".join("?" * len(_EVENT_PAIR_KINDS))
		where = (
			f"(seq = ? "
			f" OR (kind = 'create_work' "
			f"     AND (json_extract(payload, '$.parent') = ? "
			f"          OR json_extract(payload, '$.follow_up_of') "
			f"             = ?)) "
			# W123 R2: the surviving Work must see WHICH Work was closed
			# as its duplicate. That is a typed terminal relation, and
			# without this clause the survivor's journal never mentioned
			# the act at all.
			f" OR (kind = 'close_work' "
			f"     AND json_extract(payload, '$.duplicate_of') = ?) "
			# W123 R4: an accept-created provider is placed beneath a
			# parent whose link lives on the provider's Work ROW, not in
			# the accept payload. The parent receives the same
			# authoritative event.
			f" OR (kind = 'accept' "
			f"     AND json_extract(payload, '$.provider') IN "
			f"         (SELECT id FROM work WHERE parent = ? "
			f"          AND created_seq = events.seq)) "
			f" OR (kind IN ({subject_marks}) "
			f"     AND json_extract(payload, '$.work') = ?) "
			f" OR (kind IN ({pair_marks}) "
			f"     AND (json_extract(payload, '$.work') = ? "
			f"          OR json_extract(payload, '$.blocker') = ? "
			f"          OR json_extract(payload, '$.provider') = ?)))")
		binds = ([row["created_seq"], work_id, work_id, work_id, work_id]
		         + list(_EVENT_SUBJECT_KINDS)
		         + [work_id] + list(_EVENT_PAIR_KINDS)
		         + [work_id, work_id, work_id])
		if newest or before is not None:
			clause = "" if before is None else " AND seq < ?"
			tail = [] if before is None else [before]
			rows = store.conn.execute(
				f"SELECT seq, kind, actor, payload, ts FROM events "
				f"WHERE {where}{clause} ORDER BY seq DESC LIMIT ?",
				binds + tail + [limit + 1]).fetchall()
			older_exists = len(rows) > limit
			rows = rows[:limit][::-1]
		else:
			rows = store.conn.execute(
				f"SELECT seq, kind, actor, payload, ts FROM events "
				f"WHERE {where} AND seq > ? ORDER BY seq LIMIT ?",
				binds + [after, limit + 1]).fetchall()
			older_exists = False
			more_forward = len(rows) > limit
			rows = rows[:limit]
		intervals = _claim_intervals(store, work_id, store.clock())
		phases = _phase_intervals(store, work_id, store.clock())
		# W123 R1/R4: two typed relations live on the Work ROW rather
		# than in a payload — the identity a creation produced, and the
		# parent an accept-created provider was placed beneath. Resolve
		# them for this page in ONE query each, so association stays a
		# declared relation and never a guess at payload shape.
		creation_seqs = [entry["seq"] for entry in rows
		                 if entry["kind"] == "create_work"]
		created_by_seq = {}
		if creation_seqs:
			marks = ",".join("?" * len(creation_seqs))
			created_by_seq = {
				found["created_seq"]: found["id"] for found in
				store.conn.execute(
					f"SELECT id, created_seq FROM work "
					f"WHERE created_seq IN ({marks})", creation_seqs)}
		provider_parents, provider_created = {}, {}
		accept_providers = [_json.loads(entry["payload"]).get("provider")
		                    for entry in rows
		                    if entry["kind"] == "accept"]
		accept_providers = [one for one in accept_providers if one]
		if accept_providers:
			marks = ",".join("?" * len(accept_providers))
			found_rows = list(store.conn.execute(
				f"SELECT id, parent, created_seq FROM work "
				f"WHERE id IN ({marks})", accept_providers))
			provider_parents = {r["id"]: r["parent"] for r in found_rows}
			provider_created = {r["id"]: r["created_seq"]
			                    for r in found_rows}
		entries = []
		for entry in rows:
			payload = _json.loads(entry["payload"])
			provider = payload.get("provider")
			# Only an accept that CREATED its provider places it beneath
			# a parent. `accept into=existing` creates nothing, so it
			# must not reach that provider's pre-existing parent — the
			# relation is real, but this act did not make it.
			created_here = created_by_seq.get(entry["seq"])
			context = {
				"created": created_here,
				"provider_parent": provider
				if (provider is not None
				    and provider_parents.get(provider) == work_id
				    and provider_created.get(provider) == entry["seq"])
				else None,
			}
			item = {"seq": entry["seq"], "kind": entry["kind"],
			        "actor": entry["actor"], "ts": entry["ts"],
			        "payload": payload,
			        "roles": _event_roles(entry["kind"], payload,
			                              work_id, context),
			        "related": _event_related(entry["kind"], payload,
			                                  work_id, context),
			        "references": [dict(ref) for ref in
			                       store.conn.execute(
					"SELECT ordinal, kind, work, binding_revision, "
					"root, path FROM act_references WHERE seq=? "
					"ORDER BY ordinal", (entry["seq"],))]}
			# The interval rides BOTH of its boundary events, so the
			# same facts are reachable from either end.
			if entry["seq"] in intervals:
				item["claim_interval"] = intervals[entry["seq"]]
			else:
				for interval in intervals.values():
					if interval["end_seq"] == entry["seq"]:
						item["claim_interval"] = interval
						break
			# W47: the phase interval rides its ENTRY event only. The
			# index shows one row per episode, so attaching it to the
			# closing boundary too — as claim intervals deliberately
			# do — would print the same episode twice.
			if entry["seq"] in phases:
				item["phase_interval"] = phases[entry["seq"]]
			entries.append(item)
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"work": work_id,
	        "local_id": work_id.rsplit("-", 1)[1],
	        "title": row["title"],
	        "events": entries,
	        "next_after": entries[-1]["seq"]
	        if (not (newest or before is not None) and more_forward)
	        else None,
	        "next_before": entries[0]["seq"] if older_exists else None,
	        "snapshot_seq": snapshot_seq}


def threads_for(store: Authority, *, viewer_team: str,
                    viewer_member: str, after: int = 0,
                    limit: int = 100) -> dict:
	"""The participating-thread attention surface (WS-4 R56): every
	thread the viewer's team has joined — via its own labels, +,
	incoming @, or incoming => — with the member's personal New from the
	same per-thread cursors, in one snapshot. Pages cursor by the
	PARTICIPATION's added_seq (R67): a team joining old context after a
	cursor has advanced must remain discoverable by the next incremental
	read — the relation's birth orders the page, never the thread's."""
	after, limit = _page_bounds(after, limit)
	store.conn.execute("BEGIN")
	try:
		rows = []
		for entry in store.conn.execute(
				"SELECT thread_participants.thread AS thread, "
				"thread_participants.added_seq AS added_seq "
				"FROM thread_participants "
				"WHERE thread_participants.team=? "
				"AND thread_participants.added_seq > ? "
				"ORDER BY thread_participants.added_seq, "
				"thread_participants.thread "
				"LIMIT ?", (viewer_team, after, limit)):
			cursor = store.conn.execute(
				"SELECT seq FROM seen WHERE team=? AND member=? AND "
				"thread=?",
				(viewer_team, viewer_member,
				 entry["thread"])).fetchone()
			floor = cursor["seq"] if cursor else 0
			unread = store.conn.execute(
				"SELECT COUNT(*) AS n FROM messages WHERE thread=? "
				"AND seq>?",
				(entry["thread"], floor)).fetchone()["n"]
			last = store.conn.execute(
				"SELECT MAX(seq) AS m FROM messages WHERE thread=?",
				(entry["thread"],)).fetchone()["m"]
			born = store.conn.execute(
				"SELECT subject, created_seq FROM threads WHERE id=?",
				(entry["thread"],)).fetchone()
			rows.append({"id": entry["thread"],
			             "local_id": entry["thread"].rsplit("-", 1)[1],
			             "subject": born["subject"], "new": unread,
			             "last_seq": last,
			             "created_seq": born["created_seq"],
			             "added_seq": entry["added_seq"]})
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"rows": rows,
	        "next_after": rows[-1]["added_seq"]
	        if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def work_threads(store: Authority, work_id: str, *, viewer_team: str,
                     viewer_member: str, after: int = 0,
                     limit: int = 100) -> dict:
	"""The paged Work-to-thread direction (R63): every thread
	labelled to this Work, one snapshot, with explicit continuation — an
	agent never fetches an unbounded detail to navigate. Pages cursor by
	the LABEL's added_seq (R67): old context gaining this Work's label
	after a cursor has advanced must remain discoverable — the relation's
	birth orders the page, never the thread's."""
	after, limit = _page_bounds(after, limit)
	store.conn.execute("BEGIN")
	try:
		_work(store, work_id)
		rows = []
		for entry in store.conn.execute(
				"SELECT threads.id AS id, "
				"threads.subject AS subject, "
				"threads.created_seq AS created_seq, "
				"thread_labels.added_seq AS added_seq "
				"FROM thread_labels JOIN threads "
				"ON threads.id = thread_labels.thread "
				"WHERE thread_labels.work=? "
				"AND thread_labels.added_seq > ? "
				"ORDER BY thread_labels.added_seq, threads.id "
				"LIMIT ?", (work_id, after, limit)):
			cursor = store.conn.execute(
				"SELECT seq FROM seen WHERE team=? AND member=? AND "
				"thread=?",
				(viewer_team, viewer_member, entry["id"])).fetchone()
			floor = cursor["seq"] if cursor else 0
			# The thread's stable ORDINAL within the Work's set (label
			# order) — the compact T{n} selector renders it, never
			# derives it client-side across pages.
			ordinal = store.conn.execute(
				"SELECT COUNT(*) AS n FROM thread_labels "
				"JOIN threads ON threads.id = thread_labels.thread "
				"WHERE thread_labels.work=? AND "
				"(thread_labels.added_seq < ? OR "
				"(thread_labels.added_seq = ? AND threads.id <= ?))",
				(work_id, entry["added_seq"], entry["added_seq"],
				 entry["id"])).fetchone()["n"]
			rows.append({
				"id": entry["id"],
				# W7: the accepted local selector spelling; the
				# label-order ordinal below remains a pagination
				# fact (R63), never an identifier.
				"local_id": entry["id"].rsplit("-", 1)[1],
				"subject": entry["subject"],
				"ordinal": ordinal,
				"created_seq": entry["created_seq"],
				"added_seq": entry["added_seq"],
				"last_seq": store.conn.execute(
					"SELECT MAX(seq) AS m FROM messages WHERE "
					"thread=?", (entry["id"],)).fetchone()["m"],
				"new": store.conn.execute(
					"SELECT COUNT(*) AS n FROM messages WHERE "
					"thread=? AND seq>?",
					(entry["id"], floor)).fetchone()["n"],
			})
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"work": work_id, "rows": rows,
	        "next_after": rows[-1]["added_seq"]
	        if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def _descendants(store: Authority, work_id: str) -> list[str]:
	out, stack = [work_id], [work_id]
	while stack:
		node = stack.pop()
		for row in store.conn.execute(
				"SELECT id FROM work WHERE parent=?", (node,)):
			out.append(row["id"])
			stack.append(row["id"])
	return out


def _unseen_set(store: Authority, works, viewer_team: str,
                viewer_member: str) -> set:
	"""Distinct unseen message seqs across every thread labelled to
	any of `works`, against the member's per-thread cursors — each
	message counted once however many labels reach it."""
	seqs = set()
	marks = ",".join("?" for _ in works)
	for row in store.conn.execute(
			f"SELECT DISTINCT thread FROM thread_labels "
			f"WHERE work IN ({marks})", list(works)):
		cursor = store.conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND "
			"thread=?",
			(viewer_team, viewer_member, row["thread"])).fetchone()
		floor = cursor["seq"] if cursor else 0
		for message in store.conn.execute(
				"SELECT seq FROM messages WHERE thread=? AND seq>?",
				(row["thread"], floor)):
			seqs.add(message["seq"])
	return seqs


def new_count(store: Authority, work_id: str, *, viewer_team: str,
              viewer_member: str) -> dict:
	"""Member-relative `New` over labelled threads and containment
	(WS-4 R57): distinct messages counted once, with the deduplication
	made VISIBLE — subtree_total = own + sum(children.new) - overlap.
	`own` is the direct labels (W179: exactly the plain `new` cell);
	each child's count is its truthful subtree total; `overlap` is the
	raw-sum excess over the distinct union, keeping "jump to the unread
	child" honest under multiply-labelled threads. W179: the union is
	NAMED subtree_total — no client may project it into a plain New/
	Msg/My cell. (The WS-1 team-participation gate is superseded per the
	red-team note RT9: the counter is member-relative by the pinned
	ruling; the noise boundary lives in home-table scoping.)"""
	with _read_snapshot(store):
		_work(store, work_id)
		own_set = _unseen_set(store, [work_id], viewer_team,
		                      viewer_member)
		children = []
		child_sum = 0
		for row in store.conn.execute(
				"SELECT id FROM work WHERE parent=? ORDER BY created_seq",
				(work_id,)):
			child_set = _unseen_set(store,
			                        _descendants(store, row["id"]),
			                        viewer_team, viewer_member)
			children.append({"id": row["id"], "new": len(child_set)})
			child_sum += len(child_set)
		total_set = _unseen_set(store, _descendants(store, work_id),
		                        viewer_team, viewer_member)
		snapshot_seq = store.last_seq()
	return {"id": work_id, "own": len(own_set), "children": children,
	        "overlap": len(own_set) + child_sum - len(total_set),
	        "subtree_total": len(total_set), "snapshot_seq": snapshot_seq}


def bindings(store: Authority, work_id: str, *, after: int = 0,
             limit: int = 100) -> dict:
	"""WS-6: the paged pure read over a Work's append-only binding
	history — non-negative cursor on the monotonic revision, bounded
	positive limit, explicit continuation, one snapshot."""
	after, limit = _page_bounds(after, limit)
	store.conn.execute("BEGIN")
	try:
		_work(store, work_id)
		rows = [dict(entry) for entry in store.conn.execute(
			"SELECT revision, prior, root, path, git_provenance, "
			"actor, rationale, seq, created_ts FROM bindings "
			"WHERE work=? AND revision > ? ORDER BY revision LIMIT ?",
			(work_id, after, limit))]
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"work": work_id, "rows": rows,
	        "next_after": rows[-1]["revision"]
	        if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def operation_log(store: Authority, participant: str, *,
                  after: int = 0, limit: int = 100) -> dict:
	"""WS-5: the pure paged listing of ONE'S OWN operation records —
	bookkeeping (identity, fingerprint, event provenance when any,
	timestamp), ordered by the history's own dense `recorded` cursor;
	results replay through the mutation path, never through this
	listing."""
	after, limit = _page_bounds(after, limit)
	store.conn.execute("BEGIN")
	try:
		rows = [dict(entry) for entry in store.conn.execute(
			"SELECT recorded, op_id, fingerprint, seq, created_ts "
			"FROM operations WHERE participant=? AND recorded > ? "
			"ORDER BY recorded LIMIT ?", (participant, after, limit))]
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"participant": participant, "rows": rows,
	        "next_after": rows[-1]["recorded"]
	        if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def revisions(store: Authority, work_id: str, *, after: int = 0,
              limit: int = 100) -> dict:
	"""The paged pure read over a Work's ordered immutable revision
	history (R75): non-negative cursor on the monotonic revision number,
	bounded positive limit, explicit continuation, one snapshot."""
	after, limit = _page_bounds(after, limit)
	store.conn.execute("BEGIN")
	try:
		_work(store, work_id)
		rows = [dict(entry) for entry in store.conn.execute(
			"SELECT seq, revision, prior, thread, message_seq, "
			"actor, rationale, content, created_ts FROM revisions "
			"WHERE work=? AND revision > ? ORDER BY revision LIMIT ?",
			(work_id, after, limit))]
		snapshot_seq = store.last_seq()
	finally:
		store.conn.execute("ROLLBACK")
	return {"work": work_id, "rows": rows,
	        "next_after": rows[-1]["revision"]
	        if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def _poke_state(row, now: str) -> str:
	"""The one place a poke's state is decided, so `wait`, `pokes`, and
	every refusal agree.

	`timed-out` is DERIVED and is deliberately not a stored status. A
	stored one would have to be written by somebody, and nothing in this
	authority watches a clock — introducing the first background expiry
	for a conversational primitive would be the largest change in this
	feature and the least justified. So the row keeps saying `pending`
	past its deadline and every reader calls it what it is."""
	if row["status"] != "pending":
		return row["status"]
	if row["expires_at"] is not None and row["expires_at"] <= now:
		return "timed-out"
	return "pending"


def _work_state(store: Authority, work_id: str) -> dict:
	"""The CANONICAL facts about one Work, for reporting beside an
	agent's claim about it rather than instead of it."""
	row = store.conn.execute(
		"SELECT id, title, status, phase, handler_team, handler_member "
		"FROM work WHERE id=?", (work_id,)).fetchone()
	if row is None:
		return {"work": work_id, "exists": False}
	handler = None if row["handler_team"] is None \
		else f"{row['handler_team']}.{row['handler_member']}"
	return {"work": row["id"], "exists": True, "title": row["title"],
	        "status": row["status"],
	        "phase": None if row["status"] != "open" else row["phase"],
	        "handler": handler}


def pokes(store: Authority, *, viewer_team: str, viewer_member: str,
          asker: str | None = None, target: str | None = None,
          after: int = 0, limit: int = 100,
          now: str | None = None) -> dict:
	"""W5: the ONE vendor-neutral place to retrieve a poke and its
	answer, whatever runner family answered it.

	Every poke in the authority is readable. A poke is operational
	conversation with no Work attached and no confidentiality claim, and
	the operator's whole reason for the primitive is being able to ask
	"what is that participant doing" from one place — a per-viewer
	filter would put the answer somewhere the operator has to guess at.
	`asker=`/`target=` narrow it; paging is the ordinary ascending
	`after`/`limit` this surface uses everywhere else.

	Each row reports the AGENT's answer and the AUTHORITY's canonical
	state as two separate facts. `answer.claimed_work` is what the agent
	said it believes it is handling, each entry carrying the canonical
	status/phase/handler of that Work; `canonical.handled_work` is what
	the authority says the target actually holds right now. When those
	disagree, the disagreement is the report — collapsing them would
	hide exactly the case somebody poked to find."""
	if now is None:
		now = store.clock()
	rows = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		clauses = ["seq > ?"]
		params: list = [int(after)]
		if asker is not None:
			team, _dot, member = str(asker).partition(".")
			clauses.append("asker_team=? AND asker=?")
			params.extend([team, member])
		if target is not None:
			team, _dot, member = str(target).partition(".")
			clauses.append("target_team=? AND target=?")
			params.extend([team, member])
		params.append(int(limit))
		for row in store.conn.execute(
				"SELECT * FROM pokes WHERE " + " AND ".join(clauses)
				+ " ORDER BY seq LIMIT ?", params):
			target_participant = f"{row['target_team']}.{row['target']}"
			entry = {
				"poke": row["seq"],
				"asker": f"{row['asker_team']}.{row['asker']}",
				"target": target_participant,
				"request": row["request"],
				"expires_at": row["expires_at"],
				"asked_at": row["created_ts"],
				"state": _poke_state(row, now),
				"resolved_seq": row["resolved_seq"],
				"resolved_at": row["resolved_ts"],
				"answer": None,
				# What the AUTHORITY says the target is executing, read
				# fresh at this snapshot and owed by nobody's report.
				"canonical": {"handled_work": [
					_work_state(store, held["id"]) for held in
					store.conn.execute(
						"SELECT id FROM work WHERE status='open' AND "
						"handler_team=? AND handler_member=? "
						"ORDER BY created_seq",
						(row["target_team"], row["target"]))]},
			}
			answer = store.conn.execute(
				"SELECT * FROM poke_answers WHERE poke=?",
				(row["seq"],)).fetchone()
			if answer is not None:
				entry["answer"] = {
					"seq": answer["seq"],
					"at": answer["created_ts"],
					"state": answer["state"],
					"explanation": answer["explanation"],
					# Layer 1: what the RUNNER could observe. Each field
					# is a closed vocabulary whose `unknown` member means
					# "this adapter cannot see it", never "it is fine".
					"runner": {
						"provider": answer["provider"],
						"model": answer["model"],
						"session_state": answer["session_state"],
						"auth_state": answer["auth_state"],
						"limit_state": answer["limit_state"],
						"retry_at": answer["retry_at"]},
					# Layer 2, advisory: null is UNKNOWN, never zero.
					"telemetry": {
						"context_limit": answer["context_limit"],
						"context_used": answer["context_used"],
						"context_remaining": answer["context_remaining"]},
					"claimed_work": [
						_work_state(store, named["work"]) for named in
						store.conn.execute(
							"SELECT work FROM poke_answer_work "
							"WHERE poke=? ORDER BY ordinal",
							(row["seq"],))],
				}
			rows.append(entry)
	return {"pokes": rows, "snapshot_seq": snapshot_seq}


def obligations(store: Authority, *, viewer_team: str,
                now: str | None = None) -> list[dict]:
	"""The team's ACTIONABLE set — separate from unseen counts by ruling:
	`@` enters this projection, `+` never does. R43: every LIVE due trial
	the team currently answers for appears as one structured derived entry
	per deadline generation — the alarm's LOCATOR: work, trial, candidate,
	deadline, generation, and the live responsible endpoint. Purely
	derived; it follows accepted Route changes and disappears on
	extension, abandonment, supersession, or close."""
	if now is None:
		now = store.clock()
	out = Snapshotted()
	with _read_snapshot(store):
		out.snapshot_seq = store.last_seq()
		_collect_actionable(store, viewer_team, now, out)
	return out


def _collect_actionable(store: Authority, viewer_team: str, now: str,
                        out) -> None:
	for row in store.conn.execute(
			"SELECT seq, work, message_seq, team, kind, flavor, trial, "
			"thread, status FROM obligations WHERE team=? AND "
			"status='pending' ORDER BY seq", (viewer_team,)):
		entry = dict(row)
		# The declared completion verbs — the eligible handlers are
		# exactly owed_by.handlers; agents read, they do not probe.
		entry["completes_by"] = completes_by(row["flavor"])
		entry["owed_by"] = _endpoint_struct(store, row["team"], row["kind"])
		out.append(entry)
	for row in store.conn.execute(
			"SELECT trials.work, trials.trial, trials.candidate, "
			"trials.review_at, trials.deadline_generation, "
			"work.route_team, work.route_kind, work.route_selected "
			"FROM trials JOIN work ON work.id = trials.work "
			"WHERE trials.status='open' AND trials.review_at IS NOT NULL "
			"AND trials.review_at <= ? AND work.route_team=? "
			"ORDER BY trials.review_at, trials.work",
			(now, viewer_team)):
		out.append({
			"flavor": "due_trial",
			"work": row["work"], "trial": row["trial"],
			"candidate": row["candidate"],
			"review_at": row["review_at"],
			"deadline_generation": row["deadline_generation"],
			"owed_by": _endpoint_struct(
				store, row["route_team"], row["route_kind"],
				_selected_route(dict(row))),
		})


def _trial_view(store: Authority, row, now: str | None = None) -> dict:
	"""One verification trial, both axes visible: the raw observation and
	the reviewer's effective assessment are shown side by side so receipt
	progress (`reported/assigned`) is never mistaken for support. The
	counters are internally consistent by construction — one query, one
	snapshot (the caller holds the read transaction)."""
	assignments = []
	assigned = reported = withdrawn = pending = 0
	for entry in store.conn.execute(
			"SELECT * FROM obligations WHERE work=? AND trial=? "
			"AND flavor='verification' ORDER BY seq",
			(row["work"], row["trial"])):
		assigned += 1
		if entry["status"] == "reported":
			reported += 1
		elif entry["status"] == "withdrawn":
			withdrawn += 1
		else:
			pending += 1
		acts = [dict(act) for act in store.conn.execute(
			"SELECT seq, assessment, rationale, actor FROM assessments "
			"WHERE obligation=? ORDER BY seq", (entry["seq"],))]
		assignments.append({
			"obligation": entry["seq"],
			"endpoint": f"{entry['team']}.{entry['kind']}",
			"route": entry["route"], "role": entry["role"],
			"state": entry["status"],
			"observation": entry["observation"],
			"evidence": entry["evidence"],
			"effective_assessment": acts[-1] if acts else None,
			"assessments": acts,
		})
	# Due-ness is DERIVED, level-triggered, and per deadline generation:
	# a pure function of the stored instant and the clock — no scheduler,
	# no timer audit row, idempotent across reads and restarts.
	if now is None:
		now = store.clock()
	due = (row["status"] == "open" and row["review_at"] is not None
	       and now >= row["review_at"])
	return {"trial": row["trial"], "candidate": row["candidate"],
	        "status": row["status"],
	        "review_at": row["review_at"],
	        "deadline_generation": row["deadline_generation"],
	        "due": due,
	        "assigned": assigned, "reported": reported,
	        "pending": pending, "withdrawn": withdrawn,
	        "progress": f"{reported}/{assigned}",
	        "assignments": assignments}


def participant_actions(store: Authority, *, viewer_team: str,
                        viewer_member: str, now: str | None = None) -> dict:
	"""W136: THE one participant-relative action projection — the facts
	that may WAKE this exact member, owned here and consumed unchanged
	by JSON, `wait`, and the TUI's personal counters. No new message
	operator exists: the existing rules decide everything.

	- routed Work (`=>`/pass): an open, ready, unclaimed,
	  non-blocked/parked Work is actionable for every member the
	  live Route endpoint resolves; after the atomic claim it stays
	  actionable for the exact claimant alone (rediscoverable after a
	  restart, whatever its readiness drifts to). W49: the action
	  identity is the ASSIGNMENT EPISODE — Work id, its
	  `episode_seq`, and the accepted configuration generation.
	  Claiming never manufactures a second wake (a claim does not
	  mint), but a pass away and back BETWEEN two polls does, which
	  Work identity alone could not express.
	- `@` obligations: actionable exactly for members the obligation's
	  owed endpoint currently resolves; identity = the obligation seq.
	  Rerouting changes eligibility without rewriting history.
	- due verification trials: actionable exactly for members the
	  Work's live Route endpoint resolves; identity includes work,
	  trial, and deadline generation, so an extension retires the old
	  alarm and a later due generation is new.
	- W5 conversational pokes: actionable for the EXACT participant
	  asked, and for nobody else — a poke names one configured
	  `team.member`, never a route, so no endpoint resolution enters
	  here at all. Identity = the poke seq, which is the creating
	  event's sequence and never changes, so redelivery is inherently
	  idempotent for a consumer keying on `action_key`. A poke wakes a
	  participant that has no actionable Work at all, which is the
	  whole point of it, and it carries no workflow authority: it
	  appears here and changes nothing else.
	- `+`, plain posts, and personal New are attention, never wakeups.

	Deterministic order: obligations (seq), due trials (review_at,
	work), Work actions (W7's canonical explicit-priority pool, then
	the ready-unclaimed blocker preference within it, then creation
	order), then pokes (seq). Pokes come
	LAST deliberately — a conversational question never displaces the
	workflow a participant is being woken for. One read snapshot; no
	write of any kind."""
	if now is None:
		now = store.clock()
	actions = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		# W136 R4: the wait path re-derives this projection on a tight
		# poll — each DISTINCT endpoint resolves exactly once per
		# snapshot, so the read cost never grows with the number of
		# actions sharing one endpoint.
		memo: dict = {}

		def owes(team, kind, selected: str | None = None):
			key = (team, kind, selected)
			if key not in memo:
				memo[key] = _endpoint_struct(store, team, kind, selected)
			return memo[key]

		for row in store.conn.execute(
				"SELECT seq, work, message_seq, team, kind, flavor, "
				"trial, thread, status FROM obligations "
				"WHERE team=? AND status='pending' ORDER BY seq",
				(viewer_team,)):
			owed = owes(row["team"], row["kind"])
			if not owed or viewer_member not in (owed["handlers"]
			                                     or ()):
				continue
			entry = dict(row)
			entry["kind_name"] = row["kind"]
			entry["kind"] = "obligation"
			entry["action_key"] = f"obligation:{row['seq']}"
			entry["completes_by"] = completes_by(row["flavor"])
			entry["owed_by"] = owed
			actions.append(entry)
		for row in store.conn.execute(
				"SELECT trials.work, trials.trial, trials.candidate, "
				"trials.review_at, trials.deadline_generation, "
				"work.route_team, work.route_kind, work.route_selected "
				"FROM trials JOIN work ON work.id = trials.work "
				"WHERE trials.status='open' "
				"AND trials.review_at IS NOT NULL "
				"AND trials.review_at <= ? AND work.route_team=? "
				"ORDER BY trials.review_at, trials.work",
				(now, viewer_team)):
			responsible = owes(row["route_team"],
			                     row["route_kind"],
			                     _selected_route(dict(row)))
			if not responsible or viewer_member not in 					(responsible["handlers"] or ()):
				continue
			actions.append({
				"kind": "due_trial", "flavor": "due_trial",
				"action_key": (f"trial:{row['work']}:{row['trial']}"
				               f":{row['deadline_generation']}"),
				"work": row["work"], "trial": row["trial"],
				"candidate": row["candidate"],
				"review_at": row["review_at"],
				"deadline_generation": row["deadline_generation"],
				"responsible": responsible})
		# W49: endpoint eligibility is GENERATION-relative, so the
		# accepted configuration generation is part of the action
		# identity. A participant removed from a route and restored
		# between two polls would otherwise stay suppressed under an
		# episode key that never changed. A config acceptance is rare and
		# conservatively redelivers otherwise-unchanged actionable Work —
		# an honest new resolution episode, not a false wake.
		generation_row = store.conn.execute(
			"SELECT value FROM meta WHERE key='accepted_generation'"
		).fetchone()
		generation = int(generation_row["value"]) if generation_row else 0
		# W7: THE SAME canonical ordering the human Work lists use, so
		# an agent asking "what next" and an operator reading the board
		# are told the same next Work — which is the ruling's rule 5 and
		# the reason the order fragment is shared rather than repeated.
		# Eligibility is unchanged: this reorders the wake set and
		# admits nothing to it.
		for row in store.conn.execute(
				"SELECT * FROM work WHERE status='open' " + WORK_ORDER):
			if row["handler_team"] is not None:
				if (row["handler_team"], row["handler_member"]) != 						(viewer_team, viewer_member):
					continue
			else:
				if not row["ready"] or 						row["phase"] in ("block", "parked"):
					continue
				if row["route_team"] != viewer_team:
					continue
				route = owes(row["route_team"],
				             row["route_kind"],
				             _selected_route(dict(row)))
				if not route or viewer_member not in 						(route["handlers"] or ()):
					continue
			actions.append({
				"kind": "work",
				# W49: an EPISODE LOCATOR, not Work identity. The Work id
				# stays in its own structured field — consumers never
				# parse this key to recover it. Handing Work away and
				# back between two polls changes the episode, so the
				# return is delivered even though no consumer ever
				# observed the key absent.
				"action_key": (f"work:{row['id']}:{row['episode_seq']}"
				               f":g{generation}"),
				"work": row["id"],
				"episode_seq": row["episode_seq"],
				"config_generation": generation,
				"local_id": row["id"].rsplit("-", 1)[1],
				"title": row["title"],
				"phase": row["phase"],
				"claimed": row["handler_team"] is not None})
		# W93 review R18: an outstanding refresh REQUEST is actionable
		# for the exact participant whose adapter is being asked — the
		# only way a level-triggered signal reaches a bridge that
		# already polls this projection and nothing else. It is
		# deliberately not a wake for the model: the adapter answers it
		# from facts it is holding, which is why `poke` remains the
		# separate path for what only the agent can say.
		#
		# Level-triggered by construction: the row is offered while
		# `refresh_at` stands and disappears when a publication clears
		# it, so a lost delivery is simply re-offered on the next poll.
		for row in store.conn.execute(
				"SELECT incarnation, refresh_at, refresh_seq FROM "
				"runtime_leases WHERE team=? AND member=? AND "
				"refresh_at IS NOT NULL AND ended_ts IS NULL",
				(viewer_team, viewer_member)):
			actions.append({
				"kind": "runtime_refresh",
				# W93 R25: the GENERATION identifies the request.
				# Canonical instants are whole seconds, so two asks
				# inside one second shared a key and the second was
				# suppressed as already delivered — the instant stays
				# beside it as what an operator reads, never as
				# identity.
				"action_key": f"runtime-refresh:{row['incarnation']}"
				              f":{row['refresh_seq']}",
				"incarnation": row["incarnation"],
				"generation": row["refresh_seq"],
				"requested_at": row["refresh_at"],
				# The adapter answers this itself. Stated in the entry
				# so a consumer cannot mistake it for work to forward.
				"wakes_model": False})
		# W5: expiry is DERIVED here and nowhere else. Nothing schedules
		# a transition when `expires_at` arrives — this read simply
		# stops offering the poke, which is what "removed from
		# actionable delivery" means. The row keeps saying `pending`
		# and every read of it, here and in `pokes`, agrees that it is
		# `timed-out`.
		for row in store.conn.execute(
				"SELECT seq, asker_team, asker, request, expires_at, "
				"created_ts FROM pokes WHERE status='pending' AND "
				"target_team=? AND target=? AND (expires_at IS NULL OR "
				"expires_at > ?) ORDER BY seq",
				(viewer_team, viewer_member, now)):
			actions.append({
				"kind": "poke",
				"action_key": f"poke:{row['seq']}",
				"poke": row["seq"],
				"asker": f"{row['asker_team']}.{row['asker']}",
				"request": row["request"],
				"expires_at": row["expires_at"],
				"asked_at": row["created_ts"]})
	return {"actions": actions, "snapshot_seq": snapshot_seq}


def _seen_floor(store: Authority, thread: str, viewer_team: str,
                viewer_member: str) -> int:
	"""This participant's personal cursor in one thread — the ONE seen
	mechanism the authority has, read here rather than reinvented."""
	row = store.conn.execute(
		"SELECT seq FROM seen WHERE team=? AND member=? AND thread=?",
		(viewer_team, viewer_member, thread)).fetchone()
	return row["seq"] if row else 0


def inbox(store: Authority, *, viewer_team: str, viewer_member: str,
          now: str | None = None) -> dict:
	"""W25: the participant-relative ACTION and ATTENTION surface.

	Two axes, and they are never collapsed into one. OWED rows are the
	things this participant is the blocker for, and they are EXACTLY
	`participant_actions` — the one derivation `wait` consumes — so a
	console and a runner reading the same identity can never disagree
	about who owes what. Re-deriving "owed" here would be a second
	opinion, and W39 is the finding that says what a second endpoint
	resolution costs. ATTENTION rows are unseen discussion in threads
	this participant's team has joined: they invite reading and oblige
	nothing.

	SEEN is reported only where the authority actually knows it. A
	thread carries a per-participant cursor, so an attention row — and
	any owed row born from a message — is seen exactly when that cursor
	has passed the message. A poke and a due trial have no message and
	no cursor, so they report `seen: false` until they resolve.
	Presentation inventing a cursor for them would be a UI deciding a
	fact the authority does not hold.

	`owed_action` is therefore INDEPENDENT of seen state, which is the
	ruled point: reading the message that asked you something does not
	stop you being the person who owes the answer."""
	if now is None:
		now = store.clock()
	rows: list[dict] = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		for action in participant_actions(
				store, viewer_team=viewer_team,
				viewer_member=viewer_member, now=now)["actions"]:
			# Actionable WORK is not an Inbox row. Jobs is the Work
			# surface and it shows the same rows with their tree,
			# phase, route and claim; repeating them here would put one
			# queue in two tabs and make "how much do I owe" a number
			# nobody could act on. The Inbox is what is owed BESIDE the
			# Work queue — and `wait` still returns both, because a
			# runner has one attention span and no tabs.
			if action["kind"] == "work":
				continue
			# W93 review R18: a refresh request is addressed to this
			# participant's ADAPTER, not to the human reading their
			# Inbox. It rides the wake projection because that is the
			# one thing a bridge already polls; putting it in front of
			# an operator would be asking them to do a machine's job.
			if action["kind"] == "runtime_refresh":
				continue
			rows.append(_inbox_owed(store, action, viewer_team,
			                        viewer_member))
		# W93 slice 5: a runtime state the VIEWER must act on. The lease
		# names its action owner explicitly — the finding forbids
		# guessing one — so a `waiting-input` runner with no configured
		# owner stays visible in Teams and the Jobs `Agent` cell and
		# creates no obligation here. Ordinary `working` and `idle`
		# transitions are not Inbox rows at all: an operator does not
		# need notifying that an agent is working.
		for lease in store.conn.execute(
				"SELECT * FROM runtime_leases WHERE state='waiting-input' "
				"AND ended_ts IS NULL AND action_owner=? "
				"AND expires_at > ? ORDER BY changed_seq",
				(f"{viewer_team}.{viewer_member}", now)):
			participant = f"{lease['team']}.{lease['member']}"
			rows.append({
				"kind": "runtime", "owed": True, "seen": False,
				"action_key": f"runtime:{participant}:"
				              f"{lease['incarnation']}",
				"selector": participant,
				"summary": f"{participant} is waiting on "
				           f"{lease['cause']}"
				           + (f": {lease['detail']}" if lease["detail"]
				              else ""),
				"unseen_count": 0,
				"thread": None, "message": None,
				"work": lease["work"], "poke": None,
				"obligation": None, "trial": None,
				# The runner is waiting on a human, not on Baton: the
				# answer happens in that session, and the state clears
				# when the adapter reports what happened next.
				"completes_by": []})
		# W415: durable managed-turn incidents. These are the OTHER
		# half of the pair above, and the difference is the whole
		# finding: the `waiting-input` row is live state and vanishes
		# the moment the runner returns to `idle`, which is exactly
		# what erased the evidence three times running. An incident is
		# what FAILED and still needs somebody — it survives the
		# transition back to idle, a managed-stack restart, a console
		# refresh, and marking discussion seen. Only its action owner's
		# explicit dismissal removes it.
		#
		# No `Approve` completes it. The corrective action is to repair
		# the deployment/rule mismatch or reroute the Work, and
		# offering an approval here would rebuild the interactive path
		# one console away from the dispatcher that refuses it.
		for row in store.conn.execute(
				"SELECT * FROM approval_incidents WHERE action_owner=? "
				"AND dismissed_ts IS NULL ORDER BY opened_seq",
				(f"{viewer_team}.{viewer_member}",)):
			participant = f"{row['team']}.{row['member']}"
			repeated = (f" ({row['occurrences']}x, latest "
			            f"{row['latest_ts']})"
			            if row["occurrences"] > 1 else "")
			summary = (f"{participant} could not complete a managed "
			           f"{row['category']} operation: {row['cause']}"
			           + (f" — {row['detail']}" if row["detail"] else "")
			           + repeated)
			rows.append({
				"kind": "incident", "owed": True, "seen": False,
				"action_key": f"incident:{row['id']}",
				"selector": f"I{row['id']}",
				"summary": summary,
				"unseen_count": 0,
				"thread": None, "message": None,
				"work": row["work"], "poke": None,
				"obligation": None, "trial": None,
				"incident": row["id"],
				"occurrences": row["occurrences"],
				"category": row["category"],
				"cause": row["cause"],
				"participant": participant,
				"episode": row["episode"],
				# The Work is NOT claimed by anybody and stays that
				# way: an incident correlates with the assignment it
				# interrupted and decides nothing about it.
				"completes_by": [f"dismiss incident={row['id']}"]})
		# Attention: the participating-thread surface, personal cursors
		# and all. A thread with nothing unseen is not an Inbox row —
		# the Inbox is what is waiting, not an archive of everything
		# the team has ever joined.
		for entry in store.conn.execute(
				"SELECT thread, added_seq FROM thread_participants "
				"WHERE team=? ORDER BY added_seq, thread",
				(viewer_team,)):
			floor = _seen_floor(store, entry["thread"], viewer_team,
			                    viewer_member)
			unseen = store.conn.execute(
				"SELECT COUNT(*) AS n, MAX(seq) AS last FROM messages "
				"WHERE thread=? AND seq>?",
				(entry["thread"], floor)).fetchone()
			if not unseen["n"]:
				continue
			born = store.conn.execute(
				"SELECT subject FROM threads WHERE id=?",
				(entry["thread"],)).fetchone()
			labelled = store.conn.execute(
				"SELECT work FROM thread_labels WHERE thread=? "
				"ORDER BY added_seq LIMIT 1",
				(entry["thread"],)).fetchone()
			rows.append({
				"kind": "message", "owed": False, "seen": False,
				"action_key": None,
				"selector": f"M{unseen['last']}",
				"summary": born["subject"],
				"unseen_count": unseen["n"],
				"thread": entry["thread"], "message": unseen["last"],
				"work": labelled["work"] if labelled else None,
				"poke": None, "obligation": None, "trial": None,
				"completes_by": []})
	owed = [row for row in rows if row["owed"]]
	return {"rows": rows, "total": len(rows),
	        "unseen": len([row for row in rows if not row["seen"]]),
	        "owed": len(owed),
	        # The tab is bold on THIS, never on `unseen`: seen state must
	        # not be able to hide that the viewer is the blocker.
	        "owed_action": bool(owed),
	        "snapshot_seq": snapshot_seq}


def incidents(store: Authority, *, viewer_team: str, viewer_member: str,
              include_dismissed: bool = False) -> dict:
	"""W415: the durable managed-turn incident surface.

	Open incidents first, then dismissed history when asked for. The
	dismissed rows are kept and readable because "this was dismissed,
	and then it happened again" is the sequence that tells an operator
	their fix did not hold — a projection that only showed open rows
	would make a recurring problem look like a series of unrelated
	first occurrences."""
	rows = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		query = ("SELECT * FROM approval_incidents"
		         + ("" if include_dismissed
		            else " WHERE dismissed_ts IS NULL")
		         + " ORDER BY opened_seq")
		for row in store.conn.execute(query):
			rows.append({
				"incident": row["id"],
				"participant": f"{row['team']}.{row['member']}",
				"incarnation": row["incarnation"],
				"adapter": row["adapter"],
				"session": row["session"],
				"action_owner": row["action_owner"],
				"mine": row["action_owner"] == f"{viewer_team}."
				                               f"{viewer_member}",
				"cause": row["cause"],
				"category": row["category"],
				"detail": row["detail"],
				"work": row["work"],
				"episode": row["episode"],
				"action_key": row["action_key"],
				"occurrences": row["occurrences"],
				"first_ts": row["first_ts"],
				"latest_ts": row["latest_ts"],
				"open": row["dismissed_ts"] is None,
				"dismissed_ts": row["dismissed_ts"],
				"dismissed_by": row["dismissed_by"],
				"dismissal_note": row["dismissal_note"]})
	mine_open = [row for row in rows if row["open"] and row["mine"]]
	return {"rows": rows, "total": len(rows),
	        "open": len([row for row in rows if row["open"]]),
	        "mine": len(mine_open),
	        "owed_action": bool(mine_open),
	        "snapshot_seq": snapshot_seq}


def _inbox_owed(store: Authority, action: dict, viewer_team: str,
                viewer_member: str) -> dict:
	"""One actionable entry as an Inbox row — typed, with the canonical
	context an operator navigates to and the verbs that satisfy it, so
	no id is ever copied out of raw JSON."""
	row = {"kind": action["kind"], "owed": True, "seen": False,
	       "action_key": action["action_key"], "work": None,
	       "thread": None, "message": None, "poke": None,
	       "obligation": None, "trial": None, "unseen_count": 0,
	       "completes_by": action.get("completes_by") or []}
	if action["kind"] == "poke":
		row.update({"selector": f"P{action['poke']}",
		            "poke": action["poke"],
		            "summary": f"{action['asker']}: "
		                       f"{action['request']}",
		            "completes_by": ["poke-answer"]})
		return row
	if action["kind"] == "due_trial":
		row.update({"selector": f"{_local(action['work'])} "
		                        f"trial {action['trial']}",
		            "work": action["work"], "trial": action["trial"],
		            "summary": f"candidate {action['candidate']} is due "
		                       f"for review",
		            "completes_by": ["assess", "extend", "abandon"]})
		return row
	# An obligation IS born from a message, so it is the one owed kind
	# whose seen state the authority can answer.
	row.update({"selector": f"@{action['seq']}",
	            "obligation": action["seq"], "work": action["work"],
	            "thread": action["thread"],
	            "message": action["message_seq"],
	            "summary": f"{action['owed_by']['endpoint']} owes "
	                       f"{action['flavor']}"})
	if action["thread"]:
		row["seen"] = _seen_floor(store, action["thread"], viewer_team,
		                          viewer_member) >= action["message_seq"]
	return row


def _local(work_id: str) -> str:
	return work_id.rsplit("-", 1)[1]


def _runtime_view(store: Authority, team: str, member: str,
                  now: str) -> dict:
	"""W93: what this participant's RUNNER is doing, or the honest
	absence of that fact.

	Three provenances, and they are never blurred. `reported` is an
	explicit transition the adapter published. `derived` is what a read
	concludes from silence — a lease past its deadline is `unknown`, and
	one that never opened is `offline`. `configured` would be a fact
	from `baton.json` and no runtime field has one yet.

	Silence is never diagnosed. A quiet runner is `unknown`, never
	`failed` and never `stuck`: Baton cannot tell a wedged process from a
	long tool call, and a projection that guessed would send an operator
	to kill a healthy turn. Expiry writes NOTHING — this read simply
	stops reporting the last state as current, exactly as a timed-out
	poke stops being offered."""
	row = store.conn.execute(
		"SELECT * FROM runtime_leases WHERE team=? AND member=?",
		(team, member)).fetchone()
	if row is None:
		return {"state": "offline", "provenance": "derived",
		        "refresh_requested": None, "facts": [],
		        "cause": None, "detail": None, "adapter": None,
		        "provider": None, "model": None, "session": None,
		        "incarnation": None, "work": None, "episode": None,
		        "action_owner": None, "since": None,
		        "last_contact": None, "expires_at": None,
		        "stale": False,
		        "note": "no runner has ever opened a lease here"}
	view = {"adapter": row["adapter"], "provider": row["provider"],
	        "refresh_requested": row["refresh_at"],
	        "refresh_generation": row["refresh_seq"],
	        "model": row["model"], "session": row["session"],
	        "incarnation": row["incarnation"], "work": row["work"],
	        "episode": row["episode"],
	        "action_owner": row["action_owner"],
	        "since": row["changed_ts"],
	        "last_contact": row["last_contact"],
	        "expires_at": row["expires_at"], "note": None}
	view["facts"] = _runtime_facts(store, team, member,
	                               row["incarnation"], now)
	if row["ended_ts"] is not None:
		# An explicit goodbye. `reported`, because somebody said it.
		view.update({"state": "offline", "provenance": "reported",
		             "cause": row["ended_cause"],
		             "detail": row["detail"], "stale": False,
		             "note": f"runner exited at {row['ended_ts']}"})
		return view
	# The deadline is NOT NULL by schema, so this is the only question
	# a read has to ask: has it passed?
	expired = row["expires_at"] <= now
	if expired:
		# W93 review R15: the DISPLAYED state is `unknown`, and it began
		# when the deadline passed — not when the last reported
		# transition happened. `since` is the age of what a reader is
		# being shown; the reported instant that preceded it is in the
		# note and in the journal.
		view.update({"state": "unknown", "provenance": "derived",
		             "cause": None, "detail": None, "stale": True,
		             "since": row["expires_at"],
		             "note": f"lease deadline {row['expires_at']} "
		                     f"passed; the last reported state was "
		                     f"{row['state']} since {row['changed_ts']}"})
		return view
	view.update({"state": row["state"], "provenance": "reported",
	             "cause": row["cause"], "detail": row["detail"],
	             "stale": False})
	return view


def _elapsed_seconds(instant: str, now: str) -> int:
	"""Whole seconds between two canonical instants, clamped at zero —
	the age a reader needs, computed once here rather than by every
	surface that shows it."""
	import datetime as _dt

	def moment(value):
		return _dt.datetime.fromisoformat(
			value.replace("Z", "+00:00").replace(" ", "T")).timestamp()

	try:
		return max(0, int(moment(now) - moment(instant)))
	except ValueError:
		return 0


def _runtime_facts(store: Authority, team: str, member: str,
                   incarnation, now: str) -> list[dict]:
	"""W93 slice 6: this runner's safe operational inventory, each fact
	with its own SOURCE and the instant it was observed.

	They age separately on purpose. A dispatcher target read from the
	deployment document at launch and a working directory observed at
	the same moment are not equally current a day later, and a refresh
	may update one and not the other — so a reader is shown which is
	which rather than being asked to assume, and a stale fact stays
	visibly stale rather than looking live."""
	if incarnation is None:
		return []
	# W93 review R20: the instant and nothing else. A `stale` boolean
	# derived from "older than now" is true of every fact the moment
	# after it is written and therefore says nothing; a meaningful one
	# needs a ruled per-field expiry that does not exist yet. The age is
	# exposed and the reader — or a later ruling — decides what is old.
	return [{"key": row["key"].replace("_", "-"), "value": row["value"],
	         "source": row["source"], "observed_at": row["observed_ts"],
	         "age_seconds": _elapsed_seconds(row["observed_ts"], now)}
	        for row in store.conn.execute(
		"SELECT key, value, source, observed_ts FROM runtime_facts "
		"WHERE team=? AND member=? AND incarnation=? ORDER BY key",
		(team, member, incarnation))]


def runtime(store: Authority, *, viewer_team: str, viewer_member: str,
            now: str | None = None) -> dict:
	"""Every configured participant's runtime state, in one snapshot.

	Beside each one, the CANONICAL Work facts: what the authority says
	that participant holds. The runner's own `work` correlation rides
	separately and the two are never merged — a runner reporting it is
	serving Work nobody has claimed, or a claim held by a runner that
	says it is idle, is exactly the disagreement an operator opened this
	to find."""
	if now is None:
		now = store.clock()
	rows = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		for member in store.conn.execute(
				"SELECT team, handle FROM members WHERE removed=0 "
				"ORDER BY team, handle"):
			state = _runtime_view(store, member["team"],
			                      member["handle"], now)
			held = [_work_state(store, row["id"]) for row in
			        store.conn.execute(
				"SELECT id FROM work WHERE status='open' AND "
				"handler_team=? AND handler_member=? ORDER BY "
				"created_seq", (member["team"], member["handle"]))]
			rows.append({
				"participant": f"{member['team']}.{member['handle']}",
				"team": member["team"], "member": member["handle"],
				"runtime": state, "handled_work": held,
				"mine": (member["team"], member["handle"])
				        == (viewer_team, viewer_member)})
	return {"participants": rows, "snapshot_seq": snapshot_seq}


def runtime_history(store: Authority, *, participant: str,
                    after: int = 0, limit: int = 100) -> dict:
	"""One participant's append-only runtime journal.

	The lease row is a projection aid that is overwritten in place; this
	is what an incident is reconstructed from, and it keeps each
	incarnation's timeline separate so a replacement does not swallow the
	runner it replaced."""
	after, limit = _page_bounds(after, limit)
	team, _dot, member = str(participant).partition(".")
	with _read_snapshot(store):
		rows = [dict(row) for row in store.conn.execute(
			"SELECT * FROM runtime_events WHERE team=? AND member=? "
			"AND seq > ? ORDER BY seq LIMIT ?",
			(team, member, after, limit))]
		snapshot_seq = store.last_seq()
	return {"participant": participant, "rows": rows,
	        "next_after": rows[-1]["seq"] if len(rows) == limit else None,
	        "snapshot_seq": snapshot_seq}


def teams(store: Authority, *, viewer_team: str,
          viewer_member: str) -> dict:
	"""W25: the operational ROSTER — who is configured, what each of
	them may take, and what the authority says they are doing.

	Two kinds of fact ride every member row and they never merge.
	WORKFLOW facts — roles, route coverage, the Work this member is
	holding right now — come from the accepted configuration and the
	Work table.

	RUNNER facts have TWO sources and they are deliberately separate.
	`runtime` is the participant's runtime lease (W93): what its adapter
	OBSERVED — state, adapter family, provider, model, the live session
	locator, freshness and provenance. `last_answer` is that
	participant's own most recent poke answer: what the AGENT said about
	itself when asked, including the auth and limit facts only it can
	see, and the Work it believes it is handling. The two can disagree,
	and that disagreement is a fact worth showing rather than one to
	reconcile.

	Nothing here reads a process table, a socket, a console session or a
	file to guess whether somebody is alive: a member whose adapter has
	published nothing reports an unopened lease, and one who has never
	answered a poke reports `last_answer: null`. Both mean UNKNOWN and
	neither means "fine".

	Removed teams and members are absent. A roster is the set of people
	who can be given work now; retired configuration is history, and
	`events` is where history lives."""
	roster = []
	with _read_snapshot(store):
		snapshot_seq = store.last_seq()
		now = store.clock()
		# W2938 review P1: ONE read of the accepted policy, inside the
		# same snapshot the member states are derived in. Reading it
		# before the snapshot and again for the response let a
		# concurrent acceptance publish states derived with threshold A
		# beside a response claiming its threshold was B — which
		# contradicts both this feature's one-accepted-value contract
		# and the projection's own one-snapshot rule.
		threshold = pickup_threshold(store)
		for team in store.conn.execute(
				"SELECT handle, display FROM teams WHERE removed=0 "
				"ORDER BY handle"):
			members = [
				_roster_member(store, team["handle"], row,
				               now=now, threshold=threshold)
				for row in store.conn.execute(
					"SELECT handle, display FROM members WHERE team=? "
					"AND removed=0 ORDER BY handle",
					(team["handle"],))]
			roster.append({"team": team["handle"],
			               "display": team["display"],
			               "mine": team["handle"] == viewer_team,
			               "members": members})
	return {"teams": roster, "viewer": f"{viewer_team}.{viewer_member}",
	        # W2938: the ACCEPTED policy value rides the read, so a JSON
	        # client never parses TUI wording and never recomputes
	        # `pending` versus `overdue` against a local guess.
	        "pickup_overdue_seconds": threshold,
	        "snapshot_seq": snapshot_seq}


def _instant(value):
	import datetime as _dt
	return _dt.datetime.fromisoformat(
		value.replace("Z", "+00:00").replace(" ", "T"))


def pickup_threshold(store: Authority) -> int:
	"""The ACCEPTED claim-pickup threshold in seconds (W2938).

	Fails closed. Initialization and configuration acceptance always
	store a validated positive value — including the 360-second default
	when the document omits the field — so a missing, malformed, zero or
	negative one does not mean "the operator did not choose": it means
	the authority is invalid. Returning the compiled default there would
	have this reader INVENT policy in exactly the place the contract
	says the accepted value is the only source of truth, and every
	client would then consume a number no acceptance ever agreed to.

	The defaulting lives at acceptance, where omission legitimately
	means 360 (W2938 review P2)."""
	value = store.meta().get("pickup_overdue_seconds")
	if value is None:
		raise WorkError(
			"this authority records no accepted pickup threshold; "
			"every acceptance stores one, so its absence means the "
			"meta table is invalid rather than that a deployment "
			"declined to choose")
	try:
		seconds = int(value)
	except (TypeError, ValueError):
		seconds = None
	if seconds is None or seconds < 1:
		raise WorkError(
			f"the accepted pickup threshold is {value!r}; acceptance "
			f"validates it POSITIVE, so this authority's meta table is "
			f"invalid — a client must not fall back to a local guess")
	return seconds


def member_pickup(store: Authority, team: str, member: str,
                  now_iso: str, threshold: int) -> dict:
	"""One participant's pickup obligation (W2938).

	`state` is None when nothing is owed — busy, no actionable Work, or
	not eligible — `pending` inside the accepted threshold and `overdue`
	at or beyond it. Derived from the canonical open interval at READ
	time; the read performs no write and no timeout.

	`next_work` is the FIRST actionable Work in the same canonical order
	`wait` offers, as a suggested next claim. It is diagnostic: the
	obligation belongs to the participant, and that Work does not own
	it. One idle participant owes one pickup however deep the queue."""
	row = store.conn.execute(
		"SELECT started_seq, started_at FROM member_pickup "
		"WHERE team=? AND member=?", (team, member)).fetchone()
	if row is None:
		return {"state": None, "since": None, "elapsed_seconds": None,
		        "next_work": None}
	elapsed = max(0, int((_instant(now_iso)
	                      - _instant(row["started_at"])).total_seconds()))
	return {"state": "overdue" if elapsed >= threshold else "pending",
	        "since": row["started_at"],
	        "elapsed_seconds": elapsed,
	        "next_work": _first_actionable(store, team, member)}


def _first_actionable(store: Authority, team: str, member: str):
	"""The canonical first actionable Work for one member, in the same
	order `wait` offers — so the suggestion and the wake agree."""
	for row in store.conn.execute(
			"SELECT * FROM work WHERE status='open' AND handler_team IS "
			"NULL AND ready=1 AND phase NOT IN ('block','parked') "
			"AND route_team=? " + WORK_ORDER, (team,)):
		resolution = _endpoint_struct(store, row["route_team"],
		                              row["route_kind"],
		                              _selected_route(dict(row)))
		if resolution is None:
			continue
		if member in (resolution["handlers"] or ()):
			return {"work": row["id"],
			        "local_id": row["id"].rsplit("-", 1)[1],
			        "title": row["title"]}
	return None


def _roster_member(store: Authority, team: str, row, *, now=None,
                   threshold: int | None = None) -> dict:
	"""One roster row. `routes` is COVERAGE — the routes this member
	handles, each with its role and the endpoints that reach it,
	including the alternates W230 added, because "which work can land on
	this person" is the question a roster exists to answer."""
	member = row["handle"]
	routes = []
	for entry in store.conn.execute(
			"SELECT route_handlers.route AS route, routes.role AS role "
			"FROM route_handlers JOIN routes "
			"ON routes.team = route_handlers.team "
			"AND routes.handle = route_handlers.route "
			"WHERE route_handlers.team=? AND route_handlers.member=? "
			"AND routes.removed=0 ORDER BY route_handlers.route",
			(team, member)):
		endpoints = [f"{team}.{kind['handle']}" for kind in
		             store.conn.execute(
			"SELECT handle FROM kinds WHERE team=? AND retired=0 "
			"AND route=? ORDER BY handle", (team, entry["route"]))]
		endpoints += [f"{team}.{kind['kind']}" for kind in
		              store.conn.execute(
			"SELECT kind_alternates.kind AS kind FROM kind_alternates "
			"JOIN kinds ON kinds.team = kind_alternates.team "
			"AND kinds.handle = kind_alternates.kind "
			"WHERE kind_alternates.team=? AND kind_alternates.route=? "
			"AND kinds.retired=0 ORDER BY kind_alternates.kind",
			(team, entry["route"]))]
		routes.append({"route": entry["route"], "role": entry["role"],
		               "endpoints": sorted(set(endpoints))})
	answered = store.conn.execute(
		"SELECT poke_answers.*, pokes.seq AS poke_seq, "
		"pokes.request AS request FROM poke_answers "
		"JOIN pokes ON pokes.seq = poke_answers.poke "
		"WHERE pokes.target_team=? AND pokes.target=? "
		"ORDER BY poke_answers.seq DESC LIMIT 1",
		(team, member)).fetchone()
	return {
		"team": team, "member": member,
		"participant": f"{team}.{member}",
		"display": row["display"],
		# W93: the RUNNER's state, from the one helper Jobs and the
		# runtime projection also use — Teams never derives it a second
		# way. It sits beside `last_answer`, which is the agent's own
		# on-demand report and a different kind of evidence entirely.
		"runtime": _runtime_view(store, team, member, store.clock()),
		# W2938: the participant's ONE pickup obligation. A member is
		# never overdue for N Jobs; the state, its start, the elapsed
		# time and a diagnostic first actionable Work all describe one
		# interval that a claim of ANY eligible Work clears.
		"pickup": member_pickup(
			store, team, member,
			now if now is not None else store.clock(),
			threshold if threshold is not None
			else pickup_threshold(store)),
		"roles": [entry["role"] for entry in store.conn.execute(
			"SELECT role FROM member_roles WHERE team=? AND member=? "
			"ORDER BY role", (team, member))],
		"routes": routes,
		# CANONICAL activity: what this member holds, from the Work
		# table — never what a poke answer claimed. `pokes` is where
		# the agent's own claim is reported beside this.
		"handled_work": [_work_state(store, held["id"]) for held in
		                 store.conn.execute(
			"SELECT id FROM work WHERE status='open' AND "
			"handler_team=? AND handler_member=? ORDER BY created_seq",
			(team, member))],
		"last_answer": None if answered is None else {
			"poke": answered["poke_seq"],
			"request": answered["request"],
			"at": answered["created_ts"],
			"state": answered["state"],
			"explanation": answered["explanation"],
			"runner": {"provider": answered["provider"],
			           "model": answered["model"],
			           "session_state": answered["session_state"],
			           "auth_state": answered["auth_state"],
			           "limit_state": answered["limit_state"],
			           "retry_at": answered["retry_at"]},
			"telemetry": {
				"context_limit": answered["context_limit"],
				"context_used": answered["context_used"],
				"context_remaining": answered["context_remaining"]}},
	}


# W321 (finding-readiness-poll-interval): the idle cadence of the
# blocking readiness surface. Every configured participant runs its own
# bridge and its own `wait`, and at the previous 50 ms an idle
# deployment re-derived the participant-action projection about twenty
# times a second PER MEMBER — real database and CPU work to discover,
# over and over, that nothing had happened.
#
# This is agent coordination, not a control loop: pickup and execution
# happen on seconds-to-minutes timescales, so a second of latency is
# invisible where twenty reads a second are not. Fixed, not
# configurable — the ruling is one operating default for now, and a
# knob would invite tuning a number nobody has evidence about.
#
# It is a FLOOR on responsiveness, never on the caller's deadline: the
# sleep is always bounded by the remaining timeout, so `timeout=0` is
# still one pure read and a sub-second timeout still returns at the
# instant it asked for.
READINESS_POLL_SECONDS = 1.0


# W4615: the ONE bounded projection of deployment-global dispatch state.
#
# Read by home, status, `wait` and the TUI so the four cannot disagree
# about the same instant. Reading it requires nothing: the ruling grants
# `dispatch` for CHANGING the mode and leaves status readable by every
# accepted participant, because a participant that cannot tell why it is
# not being woken has to guess.
DISPATCH_BLOCKER_LIMIT = 20


def dispatch_view(store: Authority, *, limit: int = DISPATCH_BLOCKER_LIMIT) -> dict:
	"""Mode, control generation, boundary, actor, instant, and the exact
	claims still preventing `paused`.

	The blockers are DERIVED from live assignments rather than read from
	a stored snapshot, and they are bounded with EXPLICIT truncation: a
	silently cut list reads as "these are all of them", which for an
	operator waiting to restart is the one wrong answer.

	Runtime state is deliberately absent from the decision. A blocker
	whose runner is failed or unreachable is still a canonical claim and
	still prevents pause; letting adapter telemetry retire it would let
	a participant's own report decide the deployment's lifecycle."""
	# W4615 review [P2]: ONE snapshot, because the mode and the blockers are
	# one fact. Read as two independent SELECTs, a final pass committing
	# between them returned `draining` with zero blocking claims — a state
	# the authority never held, since that same commit made it `paused`.
	# `_read_snapshot` is reentrant, so a caller already holding one (`wait`,
	# `home`) joins it rather than opening a second.
	with _read_snapshot(store):
		return _dispatch_in_snapshot(store, limit)


def _dispatch_in_snapshot(store: Authority, limit: int) -> dict:
	row = dispatch_row(store.conn)
	blockers = []
	total = 0
	if row["mode"] == "draining":
		live = live_claim_rows(store.conn)
		total = len(live)
		for entry in live[:limit]:
			blockers.append({
				"work": entry["id"],
				"team": entry["team"],
				"handler": f"{entry['handler_team']}."
				           f"{entry['handler_member']}",
				"episode_seq": entry["episode_seq"],
				"title": entry["title"],
			})
	return {
		"mode": row["mode"],
		"generation": row["generation"],
		"boundary_seq": row["boundary_seq"],
		"actor": (f"{row['actor_team']}.{row['actor_member']}"
		          if row["actor_team"] else None),
		"transitioned_ts": row["transitioned_ts"],
		"blocking_claims": total,
		"blockers": blockers,
		"blockers_truncated": total > len(blockers),
	}


# The order WITHIN one authority instant. `drain_requested` and
# `pause_reached` share a sequence when the finishing round was already
# empty, and newest-first means the pause reads above the drain that caused
# it. Written out rather than left to the storage order, which is not an
# order at all.
_DISPATCH_EVENT_RANK = {"drain_requested": 0, "resumed": 0, "pause_reached": 1}


def dispatch_history(store: Authority, *, limit: int = 50,
                     before: int | None = None) -> dict:
	"""The global control journal, newest first, in whole INSTANTS.

	W4615 review [P2]: this ordered by `seq` alone, limited ROWS, and
	resumed with `seq < next_before`. An empty drain writes two events at one
	sequence, so a page size that bisected that pair made the second event
	unreachable — the audit journal was complete only when a caller happened
	to choose a page size that did not cut through an instant.

	`limit` therefore counts INSTANTS and every event at a boundary sequence
	is returned together. An authority instant is indivisible here for the
	same reason it is indivisible in the writer: the last assignment-ending
	act and the pause it caused are one commit, and a reader that saw one
	without the other would be reading a state that never existed."""
	limit = max(1, int(limit))
	# The sequences this page covers, chosen before any row is fetched, so a
	# multi-event instant is never split by the row limit.
	seq_sql = "SELECT DISTINCT seq FROM dispatch_events"
	seq_params: list = []
	if before is not None:
		seq_sql += " WHERE seq < ?"
		seq_params.append(int(before))
	seq_sql += " ORDER BY seq DESC LIMIT ?"
	seq_params.append(limit + 1)
	sequences = [row["seq"] for row in store.conn.execute(seq_sql, seq_params)]
	more = len(sequences) > limit
	sequences = sequences[:limit]
	if not sequences:
		return {"events": [], "next_before": None, "truncated": False}
	placeholders = ",".join("?" for _ in sequences)
	rows = [dict(row) for row in store.conn.execute(
		"SELECT seq, kind, mode, generation, boundary_seq, actor_team, "
		"actor_member, live_claims, reason, ts FROM dispatch_events "
		f"WHERE seq IN ({placeholders})", sequences)]
	rows.sort(key=lambda row: (-row["seq"],
	                           -_DISPATCH_EVENT_RANK.get(row["kind"], 0)))
	for row in rows:
		team, member = row.pop("actor_team"), row.pop("actor_member")
		row["actor"] = f"{team}.{member}" if team else None
	return {"events": rows,
	        # The cursor names the LAST INSTANT returned, and the next page
	        # starts strictly below it — so no event at that sequence is
	        # skipped, because every one of them was already returned.
	        "next_before": sequences[-1] if more else None,
	        "truncated": more}


def wait_actionable(store: Authority, *, viewer_team: str,
                    viewer_member: str,
                    timeout_seconds: float) -> dict:
	"""R44 + W136: the smallest READ-ONLY wait surface, now
	PARTICIPANT-relative. Returns immediately when this member's action
	projection is non-empty; otherwise blocks no later than the nearest
	live deadline (the poll re-derives the pure projection, so
	extensions, closes, claims, passes, reroutes, and competing
	messages are seen as they commit) or the caller's timeout. Creates
	no claim, timer row, audit act, or any other authority mutation."""
	import time as _time
	wall_deadline = _time.monotonic() + max(0.0, float(timeout_seconds))
	while True:
		# W4615 review [P2]: the action set and the dispatch state are
		# derived under ONE outer reentrant snapshot, so the answer describes
		# one authority instant. Two snapshots could report a participant's
		# finishing Work beside a mode that had already moved past it.
		with _read_snapshot(store):
			window = participant_actions(store, viewer_team=viewer_team,
			                             viewer_member=viewer_member,
			                             now=store.clock())
			dispatch = dispatch_view(store)
		# W4615: the MANAGED delivery boundary is where dispatch filters,
		# and `participant_actions` stays untouched.
		#
		# That projection is shared with the TUI Inbox and the operator's
		# personal counters. Filtering it globally would hide a
		# participant's obligations and pokes from the human reading the
		# console, which drain has no business doing — drain suppresses
		# model WAKES, not visibility. So the filter lives here, on the
		# one surface a managed bridge polls.
		actions = _dispatchable(window["actions"], dispatch["mode"])
		if actions:
			return {"actionable": actions,
			        "timed_out": False,
			        "snapshot_seq": window["snapshot_seq"],
			        "dispatch": dispatch}
		if dispatch["mode"] != "running":
			# An explicit answer, immediately. A managed client that
			# blocked for its full timeout here would learn "nothing for
			# you" and could not tell a paused deployment from an idle
			# one — and an empty actionable set read as ordinary idleness
			# is exactly how a drained stack looks like a broken one.
			# Both bridges already back off after a non-timeout result
			# that forwards nothing, so this does not spin.
			return {"actionable": [], "timed_out": False,
			        "snapshot_seq": window["snapshot_seq"],
			        "dispatch": dispatch}
		remaining = wall_deadline - _time.monotonic()
		if remaining <= 0:
			return {"actionable": [], "timed_out": True,
			        "snapshot_seq": window["snapshot_seq"],
			        "dispatch": dispatch}
		_time.sleep(min(READINESS_POLL_SECONDS, remaining))


def _dispatchable(actions, mode: str) -> list:
	"""Which actions may still wake a managed model in this mode.

	`running`   — every action, unchanged.
	`draining`  — only Work this exact participant ALREADY holds, so the
	              finishing round can finish, plus adapter-only refresh.
	`paused`    — adapter-only refresh, and nothing that spends a turn.

	Unclaimed Work disappears from managed delivery even for an eligible
	handler, which is what retires an offer a bridge forwarded just
	before the boundary: both bridges revalidate the exact action key
	with `timeout=0` immediately before starting a turn, so the offer is
	dropped there rather than becoming a claim the transaction would
	refuse anyway.

	Obligations, trials and pokes are not model wakes during a drain
	either. They stay visible to the human in Inbox and home — this
	filters delivery, never the board."""
	if mode == "running":
		return list(actions)
	keep = []
	for action in actions:
		if action.get("kind") == "runtime_refresh":
			# Adapter-only: it starts no model turn, and an operator
			# inspecting a drained stack still needs fresh machine facts.
			keep.append(action)
			continue
		if mode == "draining" and action.get("kind") == "work" \
				and action.get("claimed") is True:
			# `claimed` here already means "claimed BY THIS VIEWER":
			# `participant_actions` skips Work whose Handler is anybody
			# else, so this needs no second identity test and must not
			# invent one that could disagree with that rule.
			keep.append(action)
	return keep


def team_summary(store: Authority, *, viewer_team: str,
                 now: str | None = None) -> dict:
	"""WS-1 ruling: parked work stays in the operators' faces. The team's
	always-visible counts — the TUI renders the same numbers in its summary
	line, and parity holds the two surfaces equal. R46: rows, the due
	predicate, and the token come from one read snapshot."""
	# The due count is ALWAYS visible, like parked (WS-2 group 3): open
	# trials whose review_at has arrived, on work this team currently
	# answers for — derived at read time from the same clock.
	if now is None:
		now = store.clock()
	nested = store.conn.in_transaction
	with _read_snapshot(store):
		summary = _summary_in_snapshot(store, viewer_team, now)
		if not nested:
			summary["snapshot_seq"] = store.last_seq()
	return summary


def _summary_in_snapshot(store: Authority, viewer_team: str,
                         now: str) -> dict:
	def count(clause: str, *params) -> int:
		return store.conn.execute(
			"SELECT COUNT(*) AS n FROM work WHERE team=? AND status='open' "
			+ clause, (viewer_team, *params)).fetchone()["n"]
	due = store.conn.execute(
		"SELECT COUNT(*) AS n FROM trials JOIN work "
		"ON work.id = trials.work "
		"WHERE trials.status='open' AND trials.review_at IS NOT NULL "
		"AND trials.review_at <= ? AND work.route_team=?",
		(now, viewer_team)).fetchone()["n"]
	return {"team": viewer_team,
	        "open": count(""),
	        "parked": count("AND phase='parked'"),
	        # W78: the counter follows the phase it counts.
	        "blocked": count("AND phase='block'"),
	        "due": due}


def detail(store: Authority, work_id: str, *, viewer_team: str,
           viewer_member: str) -> dict:
	"""Everything about one Work, plus the transitions available to this
	viewer — DECLARED, so no client infers workflow effects from punctuation
	or discovers by trying (parity ruling)."""
	store.conn.execute("BEGIN")
	try:
		return _detail_in_snapshot(store, work_id,
		                           viewer_team=viewer_team,
		                           viewer_member=viewer_member)
	finally:
		# One pure read snapshot (WS-2 R2, following `home`): the DEP
		# counter, the live drill, and snapshot_seq can never disagree
		# about the same instant; nothing is written and the transaction
		# is rolled back.
		store.conn.execute("ROLLBACK")


def _detail_in_snapshot(store: Authority, work_id: str, *, viewer_team: str,
                        viewer_member: str) -> dict:
	row = _work(store, work_id)
	view = _row_view(store, row, viewer_team, viewer_member)
	view["snapshot_seq"] = store.last_seq()
	# W4303: the live ASSIGNMENT EPISODE, because `release` now
	# compare-and-swaps it and an operand nothing publishes cannot be
	# supplied. The claimant reads its own episode off the readiness
	# action it was woken by, but the recovery operator is deliberately
	# NOT a route handler and never sees that projection — the whole
	# point of the capability — so without this the one participant who
	# can recover an orphaned claim could not name the claim.
	#
	# It stays on `detail` rather than every Work row: this is a
	# recovery operand, not a board fact, and the lists are already the
	# place where an extra per-row field costs the most.
	view["episode_seq"] = row["episode_seq"]
	# One sampled instant for the WHOLE response (R42): due flags in
	# every trial agree with each other and with the snapshot.
	now = store.clock()
	view["trials"] = [_trial_view(store, entry, now)
	                  for entry in store.conn.execute(
		"SELECT * FROM trials WHERE work=? ORDER BY trial", (work_id,))]
	# WS-4 R54: the work's THREAD SET — distinct summaries with
	# stable ids, last-message seq, and the viewer's New, deterministic
	# order, never merged into one false timeline.
	# R67: the preview shares the relation order (label added_seq, id)
	# with `work_threads`, and truncation is EXPLICIT — the count and
	# the continuation cursor say a 51st thread exists; silence never
	# does.
	view["threads"] = []
	view["thread_count"] = store.conn.execute(
		"SELECT COUNT(*) AS n FROM thread_labels WHERE work=?",
		(work_id,)).fetchone()["n"]
	for entry in store.conn.execute(
			"SELECT thread_labels.thread AS id, "
			"threads.subject AS subject, "
			"thread_labels.added_seq AS added_seq "
			"FROM thread_labels JOIN threads "
			"ON threads.id = thread_labels.thread "
			"WHERE thread_labels.work=? "
			"ORDER BY thread_labels.added_seq, threads.id "
			"LIMIT 50", (work_id,)):
		cursor = store.conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND "
			"thread=?",
			(viewer_team, viewer_member, entry["id"])).fetchone()
		floor = cursor["seq"] if cursor else 0
		view["threads"].append({
			"id": entry["id"],
			"subject": entry["subject"],
			"added_seq": entry["added_seq"],
			"last_seq": store.conn.execute(
				"SELECT MAX(seq) AS m FROM messages WHERE thread=?",
				(entry["id"],)).fetchone()["m"],
			"new": store.conn.execute(
				"SELECT COUNT(*) AS n FROM messages WHERE thread=? "
				"AND seq>?", (entry["id"], floor)).fetchone()["n"],
		})
	view["threads_truncated"] = \
		view["thread_count"] > len(view["threads"])
	view["threads_next_after"] = \
		view["threads"][-1]["added_seq"] \
		if view["threads_truncated"] else None
	# WS-6: exactly ONE effective dossier binding, returned directly,
	# plus a BOUNDED ordered history preview with count, truncation, and
	# a continuation cursor handing off to the paged `bindings` read.
	view["binding_count"] = store.conn.execute(
		"SELECT COUNT(*) AS n FROM bindings WHERE work=?",
		(work_id,)).fetchone()["n"]
	view["binding"] = None
	effective_binding = store.conn.execute(
		"SELECT revision, prior, root, path, git_provenance, actor, "
		"rationale, seq, created_ts FROM bindings WHERE work=? "
		"ORDER BY revision DESC LIMIT 1", (work_id,)).fetchone()
	if effective_binding is not None:
		view["binding"] = dict(effective_binding)
	view["bindings"] = [dict(entry) for entry in store.conn.execute(
		"SELECT revision, prior, root, path, git_provenance, actor, "
		"rationale, seq, created_ts FROM bindings WHERE work=? "
		"ORDER BY revision LIMIT 50", (work_id,))]
	view["bindings_truncated"] = \
		view["binding_count"] > len(view["bindings"])
	view["bindings_next_after"] = \
		view["bindings"][-1]["revision"] \
		if view["bindings_truncated"] else None

	# Work-revision slice: exactly ONE effective revision, returned
	# DIRECTLY, plus a BOUNDED ordered history preview (R75: every
	# canonical list is bounded and paged) — count, truncation, and a
	# continuation cursor that hands off to the pure `revisions` read
	# without a gap or repeat.
	view["revision_count"] = store.conn.execute(
		"SELECT COUNT(*) AS n FROM revisions WHERE work=?",
		(work_id,)).fetchone()["n"]
	view["revision"] = None
	effective = store.conn.execute(
		"SELECT seq, revision, prior, thread, message_seq, actor, "
		"rationale, content, created_ts FROM revisions WHERE work=? "
		"ORDER BY revision DESC LIMIT 1", (work_id,)).fetchone()
	if effective is not None:
		view["revision"] = dict(effective)
	view["revisions"] = [dict(entry) for entry in store.conn.execute(
		"SELECT seq, revision, prior, thread, message_seq, actor, "
		"rationale, content, created_ts FROM revisions WHERE work=? "
		"ORDER BY revision LIMIT 50", (work_id,))]
	view["revisions_truncated"] = \
		view["revision_count"] > len(view["revisions"])
	view["revisions_next_after"] = \
		view["revisions"][-1]["revision"] \
		if view["revisions_truncated"] else None

	# WS-3 R49: the work's obligations as PUBLIC structured state — an
	# agent reads "obligation N is accepted into W" here, in the same
	# snapshot, without SQL or audit mining.
	view["obligations"] = [
		{"seq": row["seq"], "endpoint": f"{row['team']}.{row['kind']}",
		 "flavor": row["flavor"], "status": row["status"],
		 "accepted_into": row["accepted_into"],
		 "thread": row["thread"],
		 "resolved_seq": row["resolved_seq"]}
		for row in store.conn.execute(
			"SELECT * FROM obligations WHERE work=? ORDER BY seq",
			(work_id,))]
	view["breadcrumb"] = breadcrumb(store, work_id)
	view["links"] = links(store, work_id)
	view["new_breakdown"] = new_count(store, work_id,
	                                  viewer_team=viewer_team,
	                                  viewer_member=viewer_member)
	open_children = view["progress"]["children"] - view["progress"]["closed"]
	# The R1 authority matrix, mirrored: availability is computed from the
	# SAME live route/handler rule the authority enforces — an agent reads
	# what it may do; it never discovers by attempting. Ownership-gated
	# operations belong to the viewer only when they currently resolve as
	# a handler; every configured member keeps contribution and their own
	# seen state. CLOSED work offers nothing: closure is immutable (WS-2);
	# follow-up creation is an operation on NEW work.
	handler = False
	if row["route_team"] is not None and viewer_team == row["route_team"]:
		resolved = _endpoint_struct(store, row["route_team"],
		                            row["route_kind"],
		                            _selected_route(row))
		handler = resolved is not None and \
			viewer_member in resolved["handlers"]
	available = []
	if row["status"] == "open":
		# W3: priority is OWNING-team authority, independent of the
		# Route, claimant, phase, and readiness — advertised to
		# every configured owning-team member while the Work is open.
		if viewer_team == row["team"]:
			available.append("prioritize")
			# W128: correcting where UNCLAIMED Work is offered is
			# owning-team authority, not route eligibility — the whole
			# point being that an operator routing around a runner
			# cannot be made to depend on that runner. It disappears
			# the moment somebody claims, because claimed Work is never
			# rerouted underneath its handler.
			if row["handler_team"] is None:
				available.append("reroute")
		# R69: no Work-addressed posting/seen operation exists after the
		# Slice B bridge removal — contribution and seen state are
		# thread-addressed (say/mark-seen against a thread id),
		# so no Work alias is advertised here. An agent reads what it
		# may do; a stale advertisement is discovery-by-attempt.
		if handler:
			available += ["request", "pass", "add_dependency",
			              "create_child", "classify", "create_trial"]
			if store.conn.execute(
					"SELECT 1 FROM edges e JOIN work b ON b.id=e.blocker "
					"WHERE e.work=? AND b.status='open' LIMIT 1",
					(work_id,)).fetchone():
				available.append("remove_dependency")
			if store.conn.execute(
					"SELECT 1 FROM trials WHERE work=? AND status='open'",
					(work_id,)).fetchone():
				available += ["abandon_trial", "extend_trial"]
			if row["phase"] != "block":
				# block leaves only through its gate-bound wake.
				available.append("set_phase")
		# Only open CHILDREN prevent closure — an open blocker gates
		# readiness, never an honest terminal close (same rule as the
		# writer; agents read this instead of discovering it).
		if handler and open_children == 0:
			available.append("close")
		# W108 R2: the atomic claim is advertised exactly when the
		# writer would grant it — resolved Route handler, open,
		# ready, not blocked/parked, unclaimed. The writer stays the
		# final authority; this is discovery, not a promise.
		if handler and row["ready"] and \
				row["phase"] not in ("block", "parked") and \
				row["handler_team"] is None:
			available.append("claim")
		# Recovery mirror: a resolved Route handler may release
		# whoever holds the claim (self-release included); advertised
		# only while a claimant exists. Writer stays final.
		#
		# W4303: and so may an owning-team member holding the `recover`
		# capability. That branch exists precisely for the case where
		# the Route's only handler is the participant whose managed turn
		# died holding the claim — so leaving it undiscoverable would
		# hide recovery from the one operator who can perform it, and
		# discovery-by-attempt is what this projection exists to avoid.
		if row["handler_team"] is not None and (
				handler or (viewer_team == row["team"] and
				            store.conn.execute(
					            "SELECT 1 FROM member_capabilities "
					            "WHERE team=? AND member=? AND "
					            "capability='recover'",
					            (viewer_team, viewer_member)).fetchone()
				            is not None)):
			available.append("release")
		# W47 R1: the heartbeat is advertised EXACTLY for the recorded
		# active claimant — stricter than the route-handler test; no
		# teammate, other team, unclaimed, or closed row ever offers
		# it (closure offers nothing at all above).
		if row["handler_team"] == viewer_team and \
				row["handler_member"] == viewer_member:
			available.append("heartbeat")
	view["available_transitions"] = sorted(available)
	# W71: open_blockers is the ROW's own field (one computation, one
	# meaning) — the former detail-local recompute is gone.
	return view


# -- W24755: the portable Work-graph export -----------------------------------
#
# THE COMPLETE CURRENT GRAPH, IN ONE SNAPSHOT. Every existing projection here
# answers a bounded operator question: `tree` is team-scoped and three
# containment levels deep, `dependency_neighborhood` is dependency-only and
# capped at 200 rendered occurrences, and `links` carries all four families but
# ONE HOP AT A TIME under an independent snapshot per call. An exporter
# assembled from repeated `links` reads would therefore be stitched from
# different database states, which is precisely the thing this Work exists to
# refuse: a graph nobody can say the moment of.
#
# So this is a NEW read over the canonical relation sources rather than a crawl
# over the public views. It reads every Work row and every current dependency
# row in a constant number of ordered statements inside ONE `_read_snapshot`,
# derives the other three families from those same Work rows, validates, samples
# the snapshot sequence inside the same transaction, and rolls back.

GRAPH_STATUSES = ("all", "open", "closed")
# The one closure this export performs, spelled once. A scope naming any other
# would be describing a graph this projection does not build.
GRAPH_CLOSURE = "incident-endpoints"
GRAPH_SCOPE_MEMBERS = ("team", "status", "changed_from", "changed_until",
                       "closure")
GRAPH_COUNT_MEMBERS = ("selected_nodes", "context_nodes", "nodes", "edges")

# The four families, and the rank that orders them when two edges share a
# sequence. Fixed here rather than at the renderer, because the ORDER is part
# of the projection's determinism promise and a second copy would be a second
# opinion about it.
GRAPH_RELATIONS = ("dependency", "containment", "follow-up", "duplicate")
_RELATION_RANK = {name: rank for rank, name in enumerate(GRAPH_RELATIONS)}
_RELATION_PREDICATE = {"dependency": "blocks", "containment": "contains",
                       "follow-up": "followed_by", "duplicate": "duplicate_of"}

# Every member of a graph node, fixed. A node is graph IDENTITY plus current
# node state: Route, Handler, message counts, attention and dossier facts are
# deliberately absent, because an export that carried them would be a second
# `detail` that happens to have edges, and every one of them is a per-viewer or
# per-moment fact that would break the byte-determinism this format promises.
GRAPH_NODE_MEMBERS = ("id", "local_id", "team", "title", "origin",
                      "classification", "priority", "status", "phase",
                      "outcome", "created_seq", "last_changed_at", "selected")
GRAPH_EDGE_MEMBERS = ("relation", "predicate", "source", "target",
                      "relation_seq", "via_obligation")

# THE TYPE AND THE NULLABLE DOMAIN OF EVERY FIXED MEMBER. Second review [P1]:
# presence was proved and types were not, so a malformed structured input
# reached code that gave it meaning anyway -- `selected="false"` is TRUTHY and
# rendered as selected, and a non-text title escaped as `AttributeError` from
# `.encode()` rather than as a Baton refusal naming the member.
#
# THE WHOLE SCHEMA, not the two values that happened to be found. A pair of
# one-off guards would leave every other member in the same state and would
# have to be extended by whoever next notices one.
#
# `type(value) is expected` rather than `isinstance`, because `bool` is a
# subclass of `int`: `created_seq=True` would otherwise pass as an integer, and
# a sequence that is a boolean is exactly the kind of nonsense this exists to
# refuse.
# THE CLOSED DOMAIN OF EVERY MEMBER THAT HAS ONE. Third review [P1] named
# `status`, `phase` and `outcome`; this covers `origin`, `classification` and
# `priority` too, because they are closed in exactly the same way and validating
# only the three that were found would be the same mistake the second review
# already corrected -- a guard extended one member at a time by whoever next
# notices one.
#
# `team` is deliberately absent: its domain is the accepted configuration, which
# is a STORE fact, and the renderer is pure. The projection admits the team
# inside its own snapshot instead.
_MEMBER_VOCABULARIES = {
	"status": (OPEN, CLOSED),
	"phase": PHASES,
	"outcome": OUTCOMES,
	"origin": ORIGINS,
	"classification": CLASSIFICATIONS,
	"priority": PRIORITIES,
}

_MEMBER_TYPES = {
	"id": (str, False), "local_id": (str, False), "team": (str, False),
	"title": (str, False), "origin": (str, False),
	"classification": (str, False), "priority": (str, False),
	"status": (str, False), "phase": (str, True), "outcome": (str, True),
	"created_seq": (int, False), "last_changed_at": (str, False),
	"selected": (bool, False),
	"relation": (str, False), "predicate": (str, False),
	"source": (str, False), "target": (str, False),
	"relation_seq": (int, False), "via_obligation": (int, True),
}


def _export_members(document, members, what) -> dict:
	"""Every fixed member present, of its fixed type, and null only where the
	contract allows it."""
	if not isinstance(document, dict):
		raise WorkError(f"{what} is a document; this is {document!r}")
	missing = [name for name in members if name not in document]
	if missing:
		raise WorkError(f"{what} needs {', '.join(missing)}")
	for name in members:
		wanted, nullable = _MEMBER_TYPES[name]
		value = document[name]
		if value is None:
			if nullable:
				continue
			raise WorkError(
				f"{what} carries {name}=null; that member is always present")
		if type(value) is not wanted:
			raise WorkError(
				f"{what} carries {name}={value!r}, which is "
				f"{type(value).__name__} and not {wanted.__name__}")
		allowed = _MEMBER_VOCABULARIES.get(name)
		if allowed is not None and value not in allowed:
			raise WorkError(
				f"{what} carries {name}={value!r}, which is not one of "
				f"{', '.join(allowed)}")
	return document


# THE PUBLIC GRAMMAR, WRITTEN OUT. Review [P1]: this delegated its grammar to
# `datetime.fromisoformat`, whose accepted language is a SUPERSET of RFC 3339 --
# `2026-01-01 00:00:00Z`, `2026-W01-1T00:00:00Z` and `20260101T000000Z` were all
# accepted and silently normalized. The approved contract says timezone-bearing
# RFC 3339 and nothing else, and "whatever this Python happens to parse" is not
# a contract a client can be held to or a future Python will keep.
#
# `date-time = full-date "T" full-time`, with the separator and the zone
# designator case-insensitive per §5.6, an optional fractional second, and an
# offset that is `Z` or `(+|-)HH:MM`. The offset is REQUIRED here: RFC 3339
# permits `-00:00` to mean an unknown local offset, and a range whose meaning
# depended on the reader's zone would answer two different questions on two
# machines.
_RFC3339 = re.compile(
	r"^(?P<whole>\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2})"
	r"(\.(?P<fraction>\d+))?"
	r"(?P<offset>[Zz]|[+-]\d{2}:\d{2})$")


def _rfc3339_upper(value: str) -> str:
	"""The separator and the zone designator, upper-cased. See §5.6."""
	spelled = value[:10] + value[10].upper() + value[11:]
	return spelled[:-1] + spelled[-1].upper()


def _rfc3339_fraction(digits: str | None) -> str:
	"""The canonical fractional second: trailing zeros gone, nothing else.

	`.1` and `.10` are one instant and canonicalize alike; `.0000001` keeps
	every significant digit. The empty result means a whole second.
	"""
	return (digits or "").rstrip("0")


def _export_instant(value, what: str) -> str:
	"""One timezone-bearing RFC 3339 instant, normalized to UTC.

	THE GRAMMAR IS CHECKED BEFORE THE VALUE IS PARSED, so a spelling outside
	the contract refuses as a spelling rather than being accepted and quietly
	turned into some other instant.

	The parse still runs afterwards, because a string can match the shape and
	name no moment -- month 13, or the 30th of February -- and a regex has no
	opinion about that.
	"""
	import datetime
	if not isinstance(value, str) or not value:
		raise WorkError(f"{what} is one RFC 3339 instant")
	if not _RFC3339.match(value):
		raise WorkError(
			f"{what}={value!r} is not an RFC 3339 instant; the grammar is "
			f"YYYY-MM-DDThh:mm:ss[.sss](Z|+hh:mm|-hh:mm), and the offset is "
			f"required because a naive instant is a different moment on every "
			f"machine that reads it")
	# THE CASE IS NORMALIZED BEFORE THE PARSE, and it belongs here rather than
	# in the grammar. RFC 3339 §5.6 makes both `T` and `Z` case-insensitive, so
	# `2026-08-27t00:00:00z` IS the contract -- and `fromisoformat` rejects the
	# lower-case `z`. Without this the accepted grammar and the parser would
	# disagree about a legal spelling, and the operator would be told an
	# instant "names no moment" when it names one perfectly well.
	#
	# MEASURED, AND ONLY HALF OF IT IS LOAD-BEARING TODAY: this CPython's
	# `fromisoformat` already accepts a lower-case `t`, so removing that half
	# alone changes nothing observable. Both halves are still done in one
	# operation, because the two letters are one rule in §5.6 and a
	# normalization that handled one of them would be a rule half-applied --
	# but the asymmetry is stated here rather than left for the next reader to
	# rediscover, and the case that covers this covers the `z`.
	spelled = _rfc3339_upper(value)
	found = _RFC3339.match(spelled)
	fraction = _rfc3339_fraction(found.group("fraction"))
	# THE FRACTION IS CARRIED SEPARATELY FROM `datetime`, and second review
	# [P1] is why. RFC 3339 permits arbitrarily many fractional digits;
	# `datetime` holds only microseconds and TRUNCATES the rest without
	# complaint, so `...00.0000001Z` and `...00.0000009Z` both became
	# `...00.000000Z`. Those are different instants and therefore different
	# half-open bounds: the export silently answered a question the operator
	# did not ask, and two distinct approved scopes became indistinguishable
	# in the JSON and in the DOT metadata.
	#
	# `datetime` is still what validates the calendar and rolls the offset to
	# UTC -- a regex has no opinion about February 30th, and an offset shift
	# can move the date. It is simply not allowed to own the fraction. That is
	# sound because RFC 3339 offsets are whole minutes, so shifting to UTC
	# cannot change the sub-second part.
	try:
		moment = datetime.datetime.fromisoformat(
			found.group("whole") + found.group("offset"))
	except ValueError:
		raise WorkError(
			f"{what}={value!r} has the shape of an RFC 3339 instant and names "
			f"no moment") from None
	whole = moment.astimezone(datetime.timezone.utc).isoformat(
		timespec="seconds").replace("+00:00", "")
	return whole + (f".{fraction}" if fraction else "") + "Z"


def _export_ordering(canonical: str) -> tuple:
	"""A key that compares two canonical instants CHRONOLOGICALLY.

	The canonical text cannot be compared as a string, and the reason is worth
	stating because it is not obvious: the fraction is variable-length, so
	`...00:00:00Z` and `...00:00:00.0000001Z` compare on `Z` against `0` and
	the whole second sorts AFTER the instant a tenth of a microsecond later.
	Fixed-width padding is not available either, because the fraction has no
	bound.

	So the two parts are compared separately. The whole second is fixed-width
	text, where lexicographic and chronological agree. The fraction is compared
	as its canonical digits, which is numerically correct once trailing zeros
	are gone: equal values have equal digits, and where they differ the first
	differing digit decides -- including when one is a prefix of the other,
	since the longer one then carries a significant digit the shorter does not.
	"""
	whole, _, rest = canonical.partition(".")
	if not rest:
		return (canonical[:-1], "")
	return (whole, rest[:-1])


def _export_scope(team, status, changed_from, changed_until):
	"""The validated scope, decided from the OPERANDS ALONE.

	Nothing here touches the store, so an export that cannot be answered
	refuses before a transaction is opened and before a byte is composed.

	Review [P2]: the configured-team check used to live here, which meant one
	authority read that admits the export happened at a DIFFERENT instant from
	the rows it admits. It is now `_export_configured_team`, called inside the
	snapshot -- so a configuration change cannot land between the two and leave
	a graph admitted under a team that no longer exists.

	THIS FUNCTION PARSES; `_export_scope_document` RULES. Fourth review [P1]
	gave the scope a document validator, and for one round this held a second
	copy of the same interval and status rules -- two statements of one rule,
	which is the thing three earlier rounds corrected elsewhere. What is left
	here is the only operand-specific work there is: turning whatever legal
	spelling the operator typed into the canonical instant the document
	carries. Every rule about the result is stated once, downstream.
	"""
	since = (None if changed_from is None
	         else _export_instant(changed_from, "changed-from"))
	until = (None if changed_until is None
	         else _export_instant(changed_until, "changed-until"))
	scope = {"team": team, "status": status,
	         "changed_from": since, "changed_until": until,
	         "closure": GRAPH_CLOSURE}
	_export_scope_document(scope)
	return scope


def _export_configured_team(store: Authority, team) -> None:
	"""The one store-dependent scope refusal, read inside the snapshot."""
	if team is not None and not store.conn.execute(
			"SELECT 1 FROM teams WHERE handle=?", (team,)).fetchone():
		raise WorkError(f"team={team!r} is not a configured team")


def _export_node(row, *, selected: bool) -> dict:
	"""One EXPORT node, every member fixed and derived from the row alone.

	`_export_*` rather than `_graph_*`, and the prefix is a correction rather
	than a preference: this file already had a `_graph_node` for the bounded
	dependency NEIGHBOURHOOD, and appending a second definition of that name
	silently replaced it -- so every neighbourhood case failed with a
	TypeError while W24755's own suite passed. A module-scope name is a shared
	resource; the export's helpers now say which graph they belong to.
	"""
	return {"id": row["id"],
	        "local_id": row["id"].rsplit("-", 1)[1],
	        "team": row["team"],
	        "title": row["title"],
	        "origin": row["origin"],
	        "classification": row["classification"],
	        "priority": row["priority"],
	        "status": row["status"],
	        # Terminal Work holds no phase and open Work holds no outcome.
	        # `phase` is NOT NULL in the store and keeps its last value
	        # forever, so a row closed while blocked still reads 'block'
	        # there; the projection derives the terminal null from `status`,
	        # exactly as `_row_view` and `_graph_node` already do.
	        "phase": row["phase"] if row["status"] == "open" else None,
	        "outcome": row["outcome"] if row["status"] != "open" else None,
	        "created_seq": row["created_seq"],
	        "last_changed_at": row["last_changed_at"],
	        "selected": selected}


def _export_edge(relation, source, target, relation_seq,
                via_obligation=None) -> dict:
	return {"relation": relation,
	        "predicate": _RELATION_PREDICATE[relation],
	        "source": source, "target": target,
	        "relation_seq": relation_seq,
	        "via_obligation": via_obligation}


def _export_selects(row, scope, bounds) -> bool:
	"""Whether one Work row is SELECTED by the scope operands.

	Selection is about the operands only. Whether a row is nevertheless
	present as context is decided later, by the edges -- keeping the two
	apart is what makes `selected` a fact about the query rather than a fact
	about the traversal.
	"""
	if scope["team"] is not None and row["team"] != scope["team"]:
		return False
	if scope["status"] != "all" and row["status"] != scope["status"]:
		return False
	if scope["changed_from"] is not None:
		# CANONICAL AGAINST CANONICAL, and by ORDERING KEY rather than by text
		# -- see `_export_ordering` for why the text of two canonical instants
		# cannot be compared directly.
		moment = _export_ordering(_export_instant(row["last_changed_at"],
		                                          "a stored last_changed_at"))
		if not (bounds[0] <= moment < bounds[1]):
			return False
	return True


def _export_node_state(node) -> None:
	"""status, phase and outcome are ONE state, not three fields.

	Fourth review [P1]: each was proved to be in its own closed vocabulary and
	nothing proved they belonged together, so an open node with a terminal
	outcome, or a closed one still carrying a phase, rendered as an
	authoritative-looking document. Every value in those four combinations is
	individually legal; only the whole state is wrong.

	The schema couples them: `phase` is null exactly for terminal Work and
	`outcome` is null exactly for open Work, which is the same rule
	`_export_node` applies when it builds one.
	"""
	terminal = node["status"] != OPEN
	if terminal and node["phase"] is not None:
		raise WorkError(
			f"{node['id']} is {node['status']} and carries "
			f"phase={node['phase']!r}; terminal Work holds no scheduler phase")
	if not terminal and node["phase"] is None:
		raise WorkError(
			f"{node['id']} is open and carries phase=null; open Work is "
			f"always in one scheduler phase")
	if terminal and node["outcome"] is None:
		raise WorkError(
			f"{node['id']} is {node['status']} and carries outcome=null; "
			f"every terminal close records exactly one outcome")
	if not terminal and node["outcome"] is not None:
		raise WorkError(
			f"{node['id']} is open and carries outcome={node['outcome']!r}; "
			f"an outcome is what closing records")


def _export_edge_provenance(edge) -> None:
	"""`via_obligation` is dependency provenance and null everywhere else.

	Fourth review [P1]: the type rule allowed a nullable integer on every
	relation, so a containment edge could name an obligation it cannot have
	come from -- a plausible-looking claim about how a relation was created.
	"""
	if edge["relation"] != "dependency" and edge["via_obligation"] is not None:
		raise WorkError(
			f"the {edge['relation']} relation from {edge['source']} to "
			f"{edge['target']} carries via_obligation="
			f"{edge['via_obligation']!r}; only a dependency is created through "
			f"an obligation")


def _export_scope_document(scope) -> None:
	"""The scope AS A DOCUMENT -- its shape, its closed values, its interval.

	Distinct from `_export_scope`, which validates the OPERANDS a caller typed
	before a transaction is opened. This owns the document a structured caller
	may hand the renderer directly, and both end at the same rules: the bounds
	are RFC 3339, they arrive together, and the interval is half-open and
	non-empty.
	"""
	if not isinstance(scope, dict):
		raise WorkError(f"a Work-graph scope is a document; this is {scope!r}")
	unknown = sorted(set(scope) - set(GRAPH_SCOPE_MEMBERS))
	if unknown:
		raise WorkError(
			f"a Work-graph scope carries {', '.join(unknown)}, which is not "
			f"part of it; the scope is exactly "
			f"{', '.join(GRAPH_SCOPE_MEMBERS)}")
	missing = [name for name in GRAPH_SCOPE_MEMBERS if name not in scope]
	if missing:
		raise WorkError(f"a Work-graph scope needs {', '.join(missing)}")
	for name in ("team", "changed_from", "changed_until"):
		if scope[name] is not None and type(scope[name]) is not str:
			raise WorkError(
				f"a Work-graph scope carries {name}={scope[name]!r}, which is "
				f"neither text nor null")
	if scope["status"] not in GRAPH_STATUSES:
		raise WorkError(
			f"a Work-graph scope carries status={scope['status']!r}; the "
			f"three are {', '.join(GRAPH_STATUSES)}")
	if scope["closure"] != GRAPH_CLOSURE:
		raise WorkError(
			f"a Work-graph scope carries closure={scope['closure']!r}; this "
			f"export performs exactly {GRAPH_CLOSURE}")
	supplied = [name for name in ("changed_from", "changed_until")
	            if scope[name] is not None]
	if scope["status"] == "all" and len(supplied) != 2:
		raise WorkError(
			"a Work-graph scope with status=all names both changed_from and "
			"changed_until; the complete graph is bounded by an explicit "
			"interval")
	if len(supplied) == 1:
		raise WorkError(
			f"a Work-graph scope names {supplied[0]} alone; changed_from and "
			f"changed_until are supplied together or not at all")
	if supplied:
		since = _export_instant(scope["changed_from"], "changed_from")
		until = _export_instant(scope["changed_until"], "changed_until")
		# THE BOUND IS THE CANONICAL INSTANT, not merely a legal spelling of
		# it. Fifth review [P1], and I decided this the other way one round
		# ago on purpose: I judged that requiring canonical form would be
		# unkind to a structured caller, and validated "parses as RFC 3339"
		# instead. That was wrong, and by an argument I had already made
		# myself -- two rounds earlier I added the range to the DOT graph
		# attributes precisely so two different scopes could not produce
		# identical bytes. One scope producing DIFFERENT bytes is the same
		# promise broken from the other side.
		#
		# `2026-01-01T01:00:00+01:00` and `2026-01-01T00:00:00Z` are one
		# approved lower bound, and a document may spell it exactly one way.
		# The OPERAND path is untouched and still accepts every legal
		# spelling: it normalizes before building the scope, so the rule it
		# reaches here is already satisfied.
		for name, canonical in (("changed_from", since),
		                        ("changed_until", until)):
			if scope[name] != canonical:
				raise WorkError(
					f"a Work-graph scope carries {name}={scope[name]!r}, "
					f"which is the instant {canonical} spelled another way; a "
					f"structured scope carries the canonical UTC form so one "
					f"scope has one document")
		if _export_ordering(since) >= _export_ordering(until):
			raise WorkError(
				f"a Work-graph scope names changed_from={since} which is not "
				f"before changed_until={until}; the interval is half-open and "
				f"cannot be empty or reversed")


def _export_counts(counts, nodes, edges) -> None:
	"""Every count PROVED from the arrays beside it.

	Fourth review [P1]: `counts` was a required member nothing checked, so a
	document could announce two nodes and carry one. A count that is not
	derived is a second, unverifiable description of the same data -- and the
	one a reader is most likely to trust, because it is cheap to read.
	"""
	if not isinstance(counts, dict):
		raise WorkError(f"Work-graph counts are a document; this is {counts!r}")
	if sorted(counts) != sorted(GRAPH_COUNT_MEMBERS):
		raise WorkError(
			f"Work-graph counts are exactly {', '.join(GRAPH_COUNT_MEMBERS)}; "
			f"these are {', '.join(sorted(counts)) or 'none'}")
	selected = len([one for one in nodes if one.get("selected")])
	derived = {"selected_nodes": selected,
	           "context_nodes": len(nodes) - selected,
	           "nodes": len(nodes), "edges": len(edges)}
	for name in GRAPH_COUNT_MEMBERS:
		if type(counts[name]) is not int:
			raise WorkError(
				f"Work-graph counts carry {name}={counts[name]!r}, which is "
				f"not an integer")
		if counts[name] != derived[name]:
			raise WorkError(
				f"Work-graph counts say {name}={counts[name]} and the arrays "
				f"hold {derived[name]}; a count that is not derived is a "
				f"second description of the same data")


def validate_work_graph(result) -> dict:
	"""Refuse the whole export rather than omit an offending row, and answer
	the `id -> node` mapping the caller can then render from.

	COMPLETE-OR-REFUSE. There is no fallback that drops an invalid edge,
	because an export missing one relation is indistinguishable from a graph
	that never had it -- and this format exists to be trusted about exactly
	that.

	PUBLIC, AND CALLED BY BOTH BOUNDARIES. Review [P1]: this was private to the
	projection, so `dot.render_work_graph_dot` -- whose own docstring promises
	it owns its input because something other than this projection may call it
	-- emitted complete-looking DOT for a duplicate edge, a dangling endpoint
	or a forged predicate. A promise the code did not keep is worse than no
	promise, because a reader stops checking.

	ONE ENFORCEMENT, NOT TWO COPIES OF THE RULES. The renderer calls this
	rather than restating it; two statements of one rule agree until they
	don't.

	TAKES THE NODES AS A SEQUENCE, deliberately. A caller that had already
	built a mapping would have silently collapsed two nodes sharing an id
	before this could object -- and an export naming one Work twice is exactly
	as broken as one naming an endpoint it never described.

	TAKES THE WHOLE RESULT, and fourth review [P1] is why. It owned nodes and
	edges while `scope` and `counts` -- both required members, both reaching
	the DOT graph attributes -- were merely present. "The whole input
	validated" was a claim about two of its four parts.
	"""
	if not isinstance(result, dict):
		raise WorkError(f"a Work-graph result is a document; this is "
		                f"{result!r}")
	for name in ("scope", "counts", "nodes", "edges"):
		if name not in result:
			raise WorkError(f"a Work-graph result needs {name}")
	for name in ("nodes", "edges"):
		if not isinstance(result[name], list):
			raise WorkError(f"Work-graph {name} are a list; this is "
			                f"{result[name]!r}")
	nodes, edges = result["nodes"], result["edges"]
	_export_scope_document(result["scope"])
	taken: dict = {}
	for node in nodes:
		_export_members(node, GRAPH_NODE_MEMBERS, "a Work-graph node")
		_export_node_state(node)
		if node["id"] in taken:
			raise WorkError(
				f"the Work-graph describes {node['id']} twice; one Work is "
				f"one node")
		taken[node["id"]] = node
	nodes = taken
	seen = set()
	for edge in edges:
		_export_members(edge, GRAPH_EDGE_MEMBERS, "a Work-graph edge")
		_export_edge_provenance(edge)
		if edge["relation"] not in _RELATION_RANK:
			raise WorkError(
				f"{edge['relation']!r} is not a Work-graph relation; the four "
				f"are {', '.join(GRAPH_RELATIONS)}")
		if edge["predicate"] != _RELATION_PREDICATE[edge["relation"]]:
			raise WorkError(
				f"the {edge['relation']} relation from {edge['source']} to "
				f"{edge['target']} spells its predicate "
				f"{edge['predicate']!r}; it is "
				f"{_RELATION_PREDICATE[edge['relation']]!r}")
		for side in ("source", "target"):
			if edge[side] not in nodes:
				raise WorkError(
					f"the {edge['relation']} relation from {edge['source']} "
					f"to {edge['target']} names {edge[side]}, which is not in "
					f"the exported graph; an edge with a missing endpoint "
					f"would render as a node this export never described")
		key = (edge["relation"], edge["source"], edge["target"])
		if key in seen:
			raise WorkError(
				f"the {edge['relation']} relation from {edge['source']} to "
				f"{edge['target']} appears twice; one typed relation between "
				f"one pair is one edge")
		seen.add(key)
	# LAST, because it is the only rule that reads both arrays at once.
	_export_counts(result["counts"], result["nodes"], result["edges"])
	return nodes


def work_graph(store: Authority, *, team: str | None = None,
               status: str = "open", changed_from: str | None = None,
               changed_until: str | None = None) -> dict:
	"""The complete current Work graph, in one snapshot, as structured data.

	FOUR RELATION FAMILIES, EACH WITH A FIXED SEMANTIC DIRECTION:

	    dependency   blocker      -> consumer   `blocks`
	    containment  parent       -> child      `contains`
	    follow-up    predecessor  -> successor  `followed_by`
	    duplicate    rejected     -> survivor   `duplicate_of`

	THIS IS THE CURRENT GRAPH, NOT RELATIONSHIP HISTORY. A dependency that was
	removed is absent; a current `edges` row is present even where the `links`
	drill deliberately hides a closed consumer, because the drill answers "who
	is still waiting on me" and this answers "what does the graph contain".

	SCOPE SELECTS, THEN CLOSES OVER INCIDENT ENDPOINTS ONLY. Every typed edge
	touching a selected node is included, and the far endpoint of such an edge
	joins the export as `selected: false` context. Context does NOT expand: an
	edge incident only to context nodes is not followed. That keeps every
	selected node's direct adjacency complete, never emits a dangling edge, and
	stops one closed predecessor from pulling an unbounded history chain into
	an open-only export.

	NO PAGINATION, NO DEPTH, NO TRUNCATION MEMBER. Bounding this would produce
	a partial graph indistinguishable from a complete one.
	"""
	scope = _export_scope(team, status, changed_from, changed_until)
	with _read_snapshot(store):
		_export_configured_team(store, team)
		# STATEMENT 1 of 2: every Work row, once, in canonical order. The
		# whole graph is derived from this list and the dependency rows
		# below; there is no per-node follow-up read, which is what keeps the
		# statement count constant rather than proportional to the graph.
		rows = {row["id"]: dict(row) for row in store.conn.execute(
			"SELECT id, team, title, origin, classification, priority, "
			"status, phase, outcome, parent, follow_up_of, duplicate_of, "
			"created_seq, closed_seq, last_changed_at "
			"FROM work ORDER BY created_seq, id")}
		# STATEMENT 2 of 2: every CURRENT dependency row.
		dependencies = [dict(row) for row in store.conn.execute(
			"SELECT work, blocker, via_obligation, created_seq FROM edges "
			"ORDER BY created_seq, blocker, work")]

		bounds = (None if scope["changed_from"] is None else
		          (_export_ordering(scope["changed_from"]),
		           _export_ordering(scope["changed_until"])))
		selected = {work_id for work_id, row in rows.items()
		            if _export_selects(row, scope, bounds)}

		# Every typed edge in the authority, built once from the rows already
		# read. Whether it appears in the export is decided afterwards by
		# incidence, so the selection rule is in one place instead of being
		# repeated four times with four chances to differ.
		candidates = [
			_export_edge("dependency", edge["blocker"], edge["work"],
			            edge["created_seq"], edge["via_obligation"])
			for edge in dependencies]
		for work_id, row in rows.items():
			# The relation sequence is the moment the relation came into
			# being, and each is checked in PROGRESS.md against the column
			# that carries it: `parent` and `follow_up_of` are written at
			# creation and never updated, and `duplicate_of` is written by
			# the same close that sets `closed_seq`.
			if row["parent"] is not None:
				candidates.append(_export_edge(
					"containment", row["parent"], work_id,
					row["created_seq"]))
			if row["follow_up_of"] is not None:
				candidates.append(_export_edge(
					"follow-up", row["follow_up_of"], work_id,
					row["created_seq"]))
			if row["duplicate_of"] is not None:
				candidates.append(_export_edge(
					"duplicate", work_id, row["duplicate_of"],
					row["closed_seq"]))

		edges = [edge for edge in candidates
		         if edge["source"] in selected or edge["target"] in selected]
		context = {edge[side] for edge in edges for side in
		           ("source", "target")} - selected

		nodes = {work_id: _export_node(rows[work_id],
		                              selected=work_id in selected)
		         for work_id in selected | context}
		# ORDERED LAST, ONCE. Nodes by `(created_seq, id)`; edges by
		# `(relation_seq, relation_rank, source, target)`. Both are total
		# orders over values the store guarantees, so two unchanged snapshots
		# produce the same arrays and therefore the same bytes.
		ordered_nodes = sorted(nodes.values(),
		                       key=lambda one: (one["created_seq"], one["id"]))
		ordered_edges = sorted(
			edges, key=lambda one: (one["relation_seq"],
			                        _RELATION_RANK[one["relation"]],
			                        one["source"], one["target"]))
		# SAMPLED INSIDE THE SAME TRANSACTION. A sequence read after the
		# rollback would describe a state these rows may not have come from,
		# which is the defect that makes repeated `links` calls unusable as
		# an export.
		snapshot_seq = store.last_seq()
	# THE PROJECTION IS HELD TO ITS OWN OUTPUT by the same function the
	# renderer uses. Building a result and validating a result are two
	# different things, and a producer exempt from the rules its consumer
	# enforces is how the two come to disagree.
	answered = {"scope": scope,
	            "counts": {"selected_nodes": len(selected),
	                       "context_nodes": len(context),
	                       "nodes": len(ordered_nodes),
	                       "edges": len(ordered_edges)},
	            "nodes": ordered_nodes,
	            "edges": ordered_edges}
	validate_work_graph(answered)
	return {**answered, "snapshot_seq": snapshot_seq}
