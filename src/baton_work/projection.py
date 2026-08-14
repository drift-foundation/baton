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

from baton_work.authority import Authority, WorkError


def _work(store: Authority, work_id: str) -> dict:
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work_id,)).fetchone()
	if row is None:
		raise WorkError(f"no work {work_id!r}")
	return dict(row)


def _endpoint_str(team, kind) -> str | None:
	return f"{team}.{kind}" if team and kind else None


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
		"status": row["status"],
		"ready": bool(row["ready"]),
		"current": _endpoint_str(row["current_team"], row["current_kind"]),
		"next": _endpoint_str(row["next_team"], row["next_kind"]),
		"progress": {"children": counts["total"] or 0,
		             "closed": counts["closed"] or 0},
		"new": new_count(store, row["id"], viewer_team=viewer_team,
		                 viewer_member=viewer_member)["total"],
	}


def home(store: Authority, *, viewer_team: str, viewer_member: str) -> list[dict]:
	"""The viewer's default top-level table: root Work owned by their team.

	Linked external records deliberately do NOT appear here (noise boundary);
	they are one `links` call away (open graph)."""
	rows = store.conn.execute(
		"SELECT * FROM work WHERE parent IS NULL AND team=? "
		"ORDER BY created_seq", (viewer_team,)).fetchall()
	return [_row_view(store, dict(row), viewer_team, viewer_member)
	        for row in rows]


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
		        "current": _endpoint_str(other["current_team"],
		                                 other["current_kind"])}

	return {
		"id": work_id,
		"parent": far(row["parent"]) if row["parent"] else None,
		"contains": [far(child["id"]) for child in store.conn.execute(
			"SELECT id FROM work WHERE parent=? ORDER BY created_seq",
			(work_id,))],
		"blocked_by": [far(edge["blocker"]) for edge in store.conn.execute(
			"SELECT blocker FROM edges WHERE work=? ORDER BY created_seq",
			(work_id,))],
		"blocks": [far(edge["work"]) for edge in store.conn.execute(
			"SELECT work FROM edges WHERE blocker=? ORDER BY created_seq",
			(work_id,))],
	}


def discussion(store: Authority, work_id: str, *, after: int = 0,
               limit: int = 1000) -> list[dict]:
	"""The work's timeline, ascending by the publication sequence — which is
	the pagination cursor, because it is the total order (A1)."""
	_work(store, work_id)
	return [dict(row) for row in store.conn.execute(
		"SELECT seq, author_team, author, body, ts FROM messages "
		"WHERE work=? AND seq > ? ORDER BY seq LIMIT ?",
		(work_id, after, limit))]


def new_count(store: Authority, work_id: str, *, viewer_team: str,
              viewer_member: str) -> dict:
	"""Per-member `New`, DECOMPOSABLE: own count plus one entry per child, so
	'jump to the unread child' can exist later without recomputing the tree
	(required correction 5 of the TUI review, now pinned by test).

	Aggregation is over containment only and counts only works the viewer's
	team participates in — the team boundary as noise control. The viewer's
	own cursor for each work is the only cursor consulted (`seen state is
	per member`, ruled)."""
	_work(store, work_id)

	def own(target: str) -> int:
		participates = store.conn.execute(
			"SELECT 1 FROM work_participants WHERE work=? AND team=?",
			(target, viewer_team)).fetchone()
		if participates is None:
			return 0
		cursor_row = store.conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND work=?",
			(viewer_team, viewer_member, target)).fetchone()
		cursor = cursor_row["seq"] if cursor_row else 0
		return store.conn.execute(
			"SELECT COUNT(*) AS n FROM messages WHERE work=? AND seq > ?",
			(target, cursor)).fetchone()["n"]

	child_rows = store.conn.execute(
		"SELECT id FROM work WHERE parent=? ORDER BY created_seq",
		(work_id,)).fetchall()
	per_child = [{"id": child["id"],
	              "new": new_count(store, child["id"],
	                               viewer_team=viewer_team,
	                               viewer_member=viewer_member)["total"]}
	             for child in child_rows]
	own_new = own(work_id)
	return {"id": work_id, "own": own_new,
	        "children": per_child,
	        "total": own_new + sum(entry["new"] for entry in per_child)}


def obligations(store: Authority, *, viewer_team: str) -> list[dict]:
	"""The team's ACTIONABLE set — separate from unseen counts by ruling:
	`@` enters this projection, `+` never does."""
	return [dict(row) for row in store.conn.execute(
		"SELECT seq, work, message_seq, team, kind, status FROM obligations "
		"WHERE team=? AND status='pending' ORDER BY seq", (viewer_team,))]


def detail(store: Authority, work_id: str, *, viewer_team: str,
           viewer_member: str) -> dict:
	"""Everything about one Work, plus the transitions available to this
	viewer — DECLARED, so no client infers workflow effects from punctuation
	or discovers by trying (parity ruling)."""
	row = _work(store, work_id)
	view = _row_view(store, row, viewer_team, viewer_member)
	view["breadcrumb"] = breadcrumb(store, work_id)
	view["links"] = links(store, work_id)
	view["new_breakdown"] = new_count(store, work_id,
	                                  viewer_team=viewer_team,
	                                  viewer_member=viewer_member)
	participates = store.conn.execute(
		"SELECT 1 FROM work_participants WHERE work=? AND team=?",
		(work_id, viewer_team)).fetchone() is not None
	open_children = view["progress"]["children"] - view["progress"]["closed"]
	open_blockers = store.conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work ON work.id=edges.blocker "
		"WHERE edges.work=? AND work.status='open'", (work_id,)).fetchone()["n"]
	available = []
	if row["status"] == "open":
		if participates:
			available += ["post_message", "request", "pass", "add_dependency",
			              "mark_seen"]
		if open_children == 0 and open_blockers == 0 and participates:
			available.append("close")
	elif participates:
		available.append("reopen")
	view["available_transitions"] = sorted(available)
	view["open_blockers"] = open_blockers
	return view
