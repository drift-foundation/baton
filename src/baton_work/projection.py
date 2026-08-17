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


def _endpoint_struct(store: Authority, team, kind) -> dict | None:
	"""Structured endpoint data, resolved against the CURRENTLY accepted
	configuration at read time (projection 2.0). History keeps the snapshot
	recorded at event time; this is the live view. An endpoint the current
	generation no longer resolves is shown explicitly unresolved — route,
	role and handlers None/empty — never silently dropped and never a bare
	string."""
	if not team or not kind:
		return None
	row = store.conn.execute(
		"SELECT route, retired FROM kinds WHERE team=? AND handle=?",
		(team, kind)).fetchone()
	structured = {"endpoint": f"{team}.{kind}", "route": None,
	              "role": None, "handlers": []}
	if row is None or row["retired"] or row["route"] is None:
		return structured
	route = store.conn.execute(
		"SELECT role FROM routes WHERE team=? AND handle=? AND removed=0",
		(team, row["route"])).fetchone()
	if route is None:
		return structured
	structured["route"] = row["route"]
	structured["role"] = route["role"]
	structured["handlers"] = [entry["member"] for entry in store.conn.execute(
		"SELECT member FROM route_handlers WHERE team=? AND route=? "
		"ORDER BY member", (team, row["route"]))]
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
FILTER_FIELDS = ("team", "status", "phase", "current", "category",
                 "ready", "new", "priority")


def normalize_filter(store: Authority, active, viewer_team: str):
	"""Validate and canonically order a filter mapping. Field
	vocabulary is enforced by the shared grammar; this boundary adds
	the store-dependent refusals — an unknown team handle and an
	unresolvable current endpoint refuse BEFORE any plausible partial
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
	if "current" in active and active["current"] != "me":
		team, dot, kind = active["current"].partition(".")
		known = dot and store.conn.execute(
			"SELECT 1 FROM kinds WHERE team=? AND handle=?",
			(team, kind)).fetchone()
		if not known:
			raise WorkError(
				f"filter current={active['current']!r} is neither a "
				f"configured TEAM.KIND endpoint nor me")
	return {field: active[field] for field in FILTER_FIELDS
	        if field in active}


def _filter_matches(row: dict, active: dict, viewer_team: str,
                    viewer_member: str) -> bool:
	"""One row against the normalized filter — canonical projected
	values only (`current=me` = the viewer is one of the endpoint's
	resolved handlers; `new=true` = the viewer's personal New count is
	nonzero)."""
	for field, value in active.items():
		if field == "team" and row["team"] != value:
			return False
		if field == "status" and row["status"] != value:
			return False
		if field == "phase" and row["phase"] != value:
			return False
		if field == "current":
			current = row["current"]
			if value == "me":
				if not (current
				        and current["endpoint"].split(".", 1)[0]
				        == viewer_team
				        and viewer_member
				        in (current.get("handlers") or ())):
					return False
			elif not current or current["endpoint"] != value:
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


def _pickup_state(active_team, handoff_at, now_iso, status="open",
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
	a new claim impossible. Blocked, waiting and parked Work stays
	'pending' — honestly unclaimed, with readiness/wait/phase as the
	separate structured facts that explain why it is not claimable."""
	if status == "closed":
		return None
	if active_team is not None:
		return "claimed"
	if handoff_at is None:
		return None
	if not ready or phase in ("waiting", "parked"):
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
	if row["active_team"] is None:
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
	pickup = _pickup_state(row["active_team"], handoff_at, now,
	                       row["status"], ready=bool(row["ready"]),
	                       phase=row["phase"])
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
		"waiting_on": None if row["wait_type"] is None else
			{"type": row["wait_type"],
			 "obligation": row["wait_obligation"]},
		"status": row["status"],
		"ready": bool(row["ready"]),
		"outcome": row["outcome"],
		"rationale": row["rationale"],
		"duplicate_of": row["duplicate_of"],
		"follow_up_of": row["follow_up_of"],
		"current": _endpoint_struct(store, row["current_team"],
		                            row["current_kind"]),
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
		"open_dependents": store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges JOIN work "
			"ON work.id = edges.work "
			"WHERE edges.blocker=? AND work.status='open'",
			(row["id"],)).fetchone()["n"],
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
		# nobody infers the active worker from route membership. Null
		# until the gated claim operation exists and succeeds.
		"active": None if row["active_team"] is None else
			{"team": row["active_team"], "member": row["active_member"]},
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
		# instant the newest pass/return to the current endpoint
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
			"ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_seq", (viewer_team,)).fetchall()
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
			"SELECT * FROM work WHERE parent=? "
			"ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_seq",
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


def tree(store: Authority, root: str | None = None, *, viewer_team: str,
         viewer_member: str, work_filter=None) -> dict:
	"""W71 R3: THE canonical bounded tree window the navigation contract
	paints — the team's roots (or one supplied re-root) each followed by its
	immediate children (depth 1), the team summary, and the snapshot token,
	all derived under ONE read transaction. JSON and the TUI consume this
	same result; neither composes it from separate reads, so a writer
	committing mid-read can never produce a mixed tree."""
	with _read_snapshot(store):
		if root is None:
			# W3: root siblings rank high, normal, low, then the stable
			# created_seq tie-break — and each child sibling group
			# below orders identically WITHOUT leaving its parent.
			bases = [dict(row) for row in store.conn.execute(
				"SELECT * FROM work WHERE parent IS NULL AND team=? "
				"ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_seq", (viewer_team,))]
		else:
			bases = [_work(store, root)]
		# W39 R1: gather the WHOLE window first, then one batched
		# blocker-selector read for all of it — row construction never
		# issues a per-row selector query.
		window = []
		for base in bases:
			window.append((base, 0))
			for child in store.conn.execute(
					"SELECT * FROM work WHERE parent=? "
					"ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_seq", (base["id"],)).fetchall():
				window.append((dict(child), 1))
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
			def keep(parent, children):
				parent_match = _filter_matches(parent, active,
				                               viewer_team,
				                               viewer_member)
				matched = [child for child in children
				           if _filter_matches(child, active,
				                              viewer_team,
				                              viewer_member)]
				if parent_match or matched:
					yield dict(parent, filter_match=parent_match)
					for child in matched:
						yield dict(child, filter_match=True)

			filtered = []
			index = 0
			while index < len(rows):
				parent = rows[index]
				index += 1
				children = []
				while index < len(rows) and rows[index]["depth"]:
					children.append(rows[index])
					index += 1
				filtered.extend(keep(parent, children))
			rows = filtered
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
		        "current": _endpoint_struct(store, other["current_team"],
		                                    other["current_kind"])}

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


def thread(store: Authority, thread_id: str, *, viewer_team: str,
           viewer_member: str, after: int = 0, limit: int = 500) -> dict:
	"""One thread, one snapshot: labels (with each Work's team and
	status), monotonic participants, the viewer's New, and a
	deterministically paginated message window with its token. Every
	supplied limit goes through the contract unchanged — no invalid
	request is a secret alias for the maximum (R68)."""
	after, limit = _page_bounds(after, limit)
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
		messages = [dict(entry) for entry in store.conn.execute(
			"SELECT seq, author_team, author, body, ts FROM messages "
			"WHERE thread=? AND seq > ? ORDER BY seq LIMIT ?",
			(thread_id, after, limit))]
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
		unread = store.conn.execute(
			"SELECT COUNT(*) AS n FROM messages WHERE thread=? AND "
			"seq>?", (thread_id, floor)).fetchone()["n"]
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
	        "next_after": messages[-1]["seq"]
	        if len(messages) == limit else None,
	        "new": unread, "last_seq": last, "snapshot_seq": snapshot_seq}


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


def obligations(store: Authority, *, viewer_team: str,
                now: str | None = None) -> list[dict]:
	"""The team's ACTIONABLE set — separate from unseen counts by ruling:
	`@` enters this projection, `+` never does. R43: every LIVE due trial
	the team currently answers for appears as one structured derived entry
	per deadline generation — the alarm's LOCATOR: work, trial, candidate,
	deadline, generation, and the live responsible endpoint. Purely
	derived; it follows accepted Current/route changes and disappears on
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
		entry["completes_by"] = (["respond", "dispose", "accept"]
		                         if row["flavor"] == "response"
		                         else ["report"])
		entry["owed_by"] = _endpoint_struct(store, row["team"], row["kind"])
		out.append(entry)
	for row in store.conn.execute(
			"SELECT trials.work, trials.trial, trials.candidate, "
			"trials.review_at, trials.deadline_generation, "
			"work.current_team, work.current_kind "
			"FROM trials JOIN work ON work.id = trials.work "
			"WHERE trials.status='open' AND trials.review_at IS NOT NULL "
			"AND trials.review_at <= ? AND work.current_team=? "
			"ORDER BY trials.review_at, trials.work",
			(now, viewer_team)):
		out.append({
			"flavor": "due_trial",
			"work": row["work"], "trial": row["trial"],
			"candidate": row["candidate"],
			"review_at": row["review_at"],
			"deadline_generation": row["deadline_generation"],
			"owed_by": _endpoint_struct(store, row["current_team"],
			                            row["current_kind"]),
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
	  non-waiting/parked Work is actionable for every member the
	  live Current endpoint resolves; after the atomic claim it stays
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
	  Work's live Current endpoint resolves; identity includes work,
	  trial, and deadline generation, so an extension retires the old
	  alarm and a later due generation is new.
	- `+`, plain posts, and personal New are attention, never wakeups.

	Deterministic order: obligations (seq), due trials (review_at,
	work), then Work actions (creation order). One read snapshot; no
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
			entry["completes_by"] = (["respond", "dispose", "accept"]
			                         if row["flavor"] == "response"
			                         else ["report"])
			entry["owed_by"] = owed
			actions.append(entry)
		for row in store.conn.execute(
				"SELECT trials.work, trials.trial, trials.candidate, "
				"trials.review_at, trials.deadline_generation, "
				"work.current_team, work.current_kind "
				"FROM trials JOIN work ON work.id = trials.work "
				"WHERE trials.status='open' "
				"AND trials.review_at IS NOT NULL "
				"AND trials.review_at <= ? AND work.current_team=? "
				"ORDER BY trials.review_at, trials.work",
				(now, viewer_team)):
			responsible = resolve(row["current_team"],
			                      row["current_kind"])
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
		for row in store.conn.execute(
				"SELECT * FROM work WHERE status='open' "
				"ORDER BY created_seq"):
			if row["active_team"] is not None:
				if (row["active_team"], row["active_member"]) != 						(viewer_team, viewer_member):
					continue
			else:
				if not row["ready"] or 						row["phase"] in ("waiting", "parked"):
					continue
				if row["current_team"] != viewer_team:
					continue
				current = resolve(row["current_team"],
				                  row["current_kind"])
				if not current or viewer_member not in 						(current["handlers"] or ()):
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
				"claimed": row["active_team"] is not None})
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
		"AND trials.review_at <= ? AND work.current_team=?",
		(now, viewer_team)).fetchone()["n"]
	return {"team": viewer_team,
	        "open": count(""),
	        "parked": count("AND phase='parked'"),
	        "waiting": count("AND phase='waiting'"),
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
	if row["current_team"] is not None and viewer_team == row["current_team"]:
		resolved = _endpoint_struct(store, row["current_team"],
		                            row["current_kind"])
		handler = resolved is not None and \
			viewer_member in resolved["handlers"]
	available = []
	if row["status"] == "open":
		# W3: priority is OWNING-team authority, independent of the
		# Current route, claimant, phase, and readiness — advertised to
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
					"SELECT 1 FROM trials WHERE work=? AND status='open'",
					(work_id,)).fetchone():
				available += ["abandon_trial", "extend_trial"]
			if row["phase"] != "waiting":
				# waiting leaves only through its condition-bound wake.
				available.append("set_phase")
		# Only open CHILDREN prevent closure — an open blocker gates
		# readiness, never an honest terminal close (same rule as the
		# writer; agents read this instead of discovering it).
		if handler and open_children == 0:
			available.append("close")
		# W108 R2: the atomic claim is advertised exactly when the
		# writer would grant it — resolved Current handler, open,
		# ready, not waiting/parked, unclaimed. The writer stays the
		# final authority; this is discovery, not a promise.
		if handler and row["ready"] and \
				row["phase"] not in ("waiting", "parked") and \
				row["active_team"] is None:
			available.append("claim")
		# Recovery mirror: a resolved Current handler may release
		# whoever holds the claim (self-release included); advertised
		# only while a claimant exists. Writer stays final.
		if handler and row["active_team"] is not None:
			available.append("release")
		# W47 R1: the heartbeat is advertised EXACTLY for the recorded
		# active claimant — stricter than the route-handler test; no
		# teammate, other team, unclaimed, or closed row ever offers
		# it (closure offers nothing at all above).
		if row["active_team"] == viewer_team and \
				row["active_member"] == viewer_member:
			available.append("heartbeat")
	view["available_transitions"] = sorted(available)
	# W71: open_blockers is the ROW's own field (one computation, one
	# meaning) — the former detail-local recompute is gone.
	return view
