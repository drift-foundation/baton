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


def _row_view(store: Authority, row: dict, viewer_team: str,
              viewer_member: str) -> dict:
	"""One Work as a projection row: stable ids and structured values, no
	preformatted display strings (parity ruling)."""
	counts = store.conn.execute(
		"SELECT COUNT(*) AS total, "
		"SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed "
		"FROM work WHERE parent=?", (row["id"],)).fetchone()
	return {
		"id": row["id"],
		"title": row["title"],
		"team": row["team"],
		"origin": row["origin"],
		"classification": row["classification"],
		"phase": row["phase"],
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
		# WS-2 (ruled): DEP is the count of OPEN work currently depending
		# on this one — the provider's live load, not a historical total;
		# the journal retains every edge act.
		"dep": store.conn.execute(
			"SELECT COUNT(*) AS n FROM edges JOIN work "
			"ON work.id = edges.work "
			"WHERE edges.blocker=? AND work.status='open'",
			(row["id"],)).fetchone()["n"],
		"new": new_count(store, row["id"], viewer_team=viewer_team,
		                 viewer_member=viewer_member)["total"],
	}


def home(store: Authority, *, viewer_team: str, viewer_member: str) -> dict:
	"""The viewer's default top-level view: the team SUMMARY and the table
	of root Work owned by their team — ONE projection, one snapshot, so the
	always-visible parked count can never disagree with the rows beside it
	(WS-1 review R3). Linked external records deliberately do NOT appear in
	the rows (noise boundary); they are one `links` call away (open graph)."""
	store.conn.execute("BEGIN")
	try:
		rows = store.conn.execute(
			"SELECT * FROM work WHERE parent IS NULL AND team=? "
			"ORDER BY created_seq", (viewer_team,)).fetchall()
		views = [_row_view(store, dict(row), viewer_team, viewer_member)
		         for row in rows]
		summary = team_summary(store, viewer_team=viewer_team,
		                       now=store.clock())
		snapshot_seq = store.last_seq()
	finally:
		# A read transaction, rolled back: purity intact, and rows,
		# summary and snapshot_seq all describe ONE database snapshot —
		# a writer committing mid-read changes none of them (R3).
		store.conn.execute("ROLLBACK")
	return {"summary": summary, "rows": views,
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
	_work(store, work_id)
	rows = store.conn.execute(
		"SELECT * FROM work WHERE parent=? ORDER BY created_seq",
		(work_id,)).fetchall()
	return [_row_view(store, dict(row), viewer_team, viewer_member)
	        for row in rows]


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
	return {"id": thread_id, "subject": row["subject"],
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
	made VISIBLE — total = own + sum(children.new) - overlap. `own` is
	the direct labels; each child's count is its truthful subtree total;
	`overlap` is the raw-sum excess over the distinct union, keeping
	"jump to the unread child" honest under multiply-labelled
	threads. (The WS-1 team-participation gate is superseded per the
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
	        "total": len(total_set), "snapshot_seq": snapshot_seq}


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
	`@` enters this projection, `+` never does. R43: every LIVE due round
	the team currently answers for appears as one structured derived entry
	per deadline generation — the alarm's LOCATOR: work, round, candidate,
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
			"SELECT seq, work, message_seq, team, kind, flavor, round, "
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
			"SELECT rounds.work, rounds.round, rounds.candidate, "
			"rounds.review_at, rounds.deadline_generation, "
			"work.current_team, work.current_kind "
			"FROM rounds JOIN work ON work.id = rounds.work "
			"WHERE rounds.status='open' AND rounds.review_at IS NOT NULL "
			"AND rounds.review_at <= ? AND work.current_team=? "
			"ORDER BY rounds.review_at, rounds.work",
			(now, viewer_team)):
		out.append({
			"flavor": "due_round",
			"work": row["work"], "round": row["round"],
			"candidate": row["candidate"],
			"review_at": row["review_at"],
			"deadline_generation": row["deadline_generation"],
			"owed_by": _endpoint_struct(store, row["current_team"],
			                            row["current_kind"]),
		})


def _round_view(store: Authority, row, now: str | None = None) -> dict:
	"""One verification round, both axes visible: the raw observation and
	the reviewer's effective assessment are shown side by side so receipt
	progress (`reported/assigned`) is never mistaken for support. The
	counters are internally consistent by construction — one query, one
	snapshot (the caller holds the read transaction)."""
	assignments = []
	assigned = reported = withdrawn = pending = 0
	for entry in store.conn.execute(
			"SELECT * FROM obligations WHERE work=? AND round=? "
			"AND flavor='verification' ORDER BY seq",
			(row["work"], row["round"])):
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
	return {"round": row["round"], "candidate": row["candidate"],
	        "status": row["status"],
	        "review_at": row["review_at"],
	        "deadline_generation": row["deadline_generation"],
	        "due": due,
	        "assigned": assigned, "reported": reported,
	        "pending": pending, "withdrawn": withdrawn,
	        "progress": f"{reported}/{assigned}",
	        "assignments": assignments}


def wait_actionable(store: Authority, *, viewer_team: str,
                    timeout_seconds: float) -> dict:
	"""R44: the smallest READ-ONLY wait surface. Returns immediately when
	the team's actionable projection is non-empty; otherwise blocks no
	later than the nearest live deadline (the poll re-derives the pure
	projection, so extensions, closes, abandonments, and competing
	messages are seen as they commit) or the caller's timeout. Creates no
	claim, timer row, audit act, or any other authority mutation."""
	import time as _time
	wall_deadline = _time.monotonic() + max(0.0, float(timeout_seconds))
	while True:
		entries = obligations(store, viewer_team=viewer_team,
		                      now=store.clock())
		if entries:
			return {"actionable": entries, "timed_out": False,
			        "snapshot_seq": entries.snapshot_seq}
		remaining = wall_deadline - _time.monotonic()
		if remaining <= 0:
			return {"actionable": [], "timed_out": True,
			        "snapshot_seq": entries.snapshot_seq}
		_time.sleep(min(0.05, remaining))


def team_summary(store: Authority, *, viewer_team: str,
                 now: str | None = None) -> dict:
	"""WS-1 ruling: parked work stays in the operators' faces. The team's
	always-visible counts — the TUI renders the same numbers in its summary
	line, and parity holds the two surfaces equal. R46: rows, the due
	predicate, and the token come from one read snapshot."""
	# The due count is ALWAYS visible, like parked (WS-2 group 3): open
	# rounds whose review_at has arrived, on work this team currently
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
		"SELECT COUNT(*) AS n FROM rounds JOIN work "
		"ON work.id = rounds.work "
		"WHERE rounds.status='open' AND rounds.review_at IS NOT NULL "
		"AND rounds.review_at <= ? AND work.current_team=?",
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
	# every round agree with each other and with the snapshot.
	now = store.clock()
	view["rounds"] = [_round_view(store, entry, now)
	                  for entry in store.conn.execute(
		"SELECT * FROM rounds WHERE work=? ORDER BY round", (work_id,))]
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
	open_blockers = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work ON work.id=edges.blocker "
		"WHERE edges.work=? AND work.status='open'", (work_id,)).fetchone()["n"]
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
		# R69: no Work-addressed posting/seen operation exists after the
		# Slice B bridge removal — contribution and seen state are
		# thread-addressed (say/mark-seen against a thread id),
		# so no Work alias is advertised here. An agent reads what it
		# may do; a stale advertisement is discovery-by-attempt.
		if handler:
			available += ["request", "pass", "add_dependency",
			              "create_child", "classify", "create_round"]
			if store.conn.execute(
					"SELECT 1 FROM rounds WHERE work=? AND status='open'",
					(work_id,)).fetchone():
				available += ["abandon_round", "extend_round"]
			if row["phase"] != "waiting":
				# waiting leaves only through its condition-bound wake.
				available.append("set_phase")
		# Only open CHILDREN prevent closure — an open blocker gates
		# readiness, never an honest terminal close (same rule as the
		# writer; agents read this instead of discovering it).
		if handler and open_children == 0:
			available.append("close")
	view["available_transitions"] = sorted(available)
	view["open_blockers"] = open_blockers
	return view
