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

from baton_work.authority import Authority, WorkError


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
# promotion, no second priority axis. Containment is not here either —
# an open child does gate its parent's readiness, but "holds another
# agent" is a claim about a dependency somebody declared, and the
# containment half is an open acceptance question in `FINDING.md`.
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
		snapshot_seq = store.last_seq()
	finally:
		# A read transaction, rolled back: purity intact, and rows,
		# summary and snapshot_seq all describe ONE database snapshot —
		# a writer committing mid-read changes none of them (R3).
		store.conn.execute("ROLLBACK")
	return {"summary": summary, "rows": views,
	        "filter": active,
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
		snapshot_seq = store.last_seq()
	return {"rows": rows, "summary": summary, "filter": active,
	        "snapshot_seq": snapshot_seq}


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
		        "route": _endpoint_struct(store, other["route_team"],
		                                  other["route_kind"]),
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
	"pass", "return", "create_trial", "report", "assess",
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
			"work.route_team, work.route_kind "
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
			"owed_by": _endpoint_struct(store, row["route_team"],
			                            row["route_kind"]),
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

		def resolve(team, kind):
			key = (team, kind)
			if key not in memo:
				memo[key] = _endpoint_struct(store, team, kind)
			return memo[key]

		for row in store.conn.execute(
				"SELECT seq, work, message_seq, team, kind, flavor, "
				"trial, thread, status FROM obligations "
				"WHERE team=? AND status='pending' ORDER BY seq",
				(viewer_team,)):
			owed = resolve(row["team"], row["kind"])
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
				"work.route_team, work.route_kind "
				"FROM trials JOIN work ON work.id = trials.work "
				"WHERE trials.status='open' "
				"AND trials.review_at IS NOT NULL "
				"AND trials.review_at <= ? AND work.route_team=? "
				"ORDER BY trials.review_at, trials.work",
				(now, viewer_team)):
			responsible = resolve(row["route_team"],
			                      row["route_kind"])
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
				route = resolve(row["route_team"],
				                row["route_kind"])
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
		window = participant_actions(store, viewer_team=viewer_team,
		                             viewer_member=viewer_member,
		                             now=store.clock())
		if window["actions"]:
			return {"actionable": window["actions"],
			        "timed_out": False,
			        "snapshot_seq": window["snapshot_seq"]}
		remaining = wall_deadline - _time.monotonic()
		if remaining <= 0:
			return {"actionable": [], "timed_out": True,
			        "snapshot_seq": window["snapshot_seq"]}
		_time.sleep(min(0.05, remaining))


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
		                            row["route_kind"])
		handler = resolved is not None and \
			viewer_member in resolved["handlers"]
	available = []
	if row["status"] == "open":
		# W3: priority is OWNING-team authority, independent of the
		# Route, claimant, phase, and readiness — advertised to
		# every configured owning-team member while the Work is open.
		if viewer_team == row["team"]:
			available.append("prioritize")
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
		if handler and row["handler_team"] is not None:
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
