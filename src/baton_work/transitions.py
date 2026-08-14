"""Work transitions: create, close, reopen — Gate A step A2.

Every transition is one authority write transaction, and READINESS IS
LEVEL-TRIGGERED: nothing here walks a graph forwarding an event. A transition
recomputes the readiness of exactly the rows whose inputs it changed, from
their CURRENT state — so replay is idempotent, a crash re-runs harmlessly, and
reopen is the same code path as close rather than an inverse that must be kept
in sync (ruling: level-triggered readiness; the plan's A3 break-sweep exists
to keep it this way).

IDS ARE QUALIFIED. A Work id embeds the authority uuid's prefix, so a
reference retained in protocol-10 history can never silently resolve to a
record in this fresh authority (plan §6).
"""

from __future__ import annotations

import sqlite3

from baton_work.authority import Authority, WorkError

# The confirmed intake example's vocabulary. Additive growth is expected;
# renames are not.
ORIGINS = ("external-report", "self-initiated", "decomposition")
CLASSIFICATIONS = ("suspected-defect", "confirmed-defect", "limitation",
                   "duplicate", "design-choice", "rejection")
OPEN, CLOSED = "open", "closed"


def _work(store: Authority, work_id: str) -> sqlite3.Row:
	row = store.conn.execute("SELECT * FROM work WHERE id=?",
	                         (work_id,)).fetchone()
	if row is None:
		raise WorkError(f"no work {work_id!r}")
	return row


def _endpoint(store: Authority, team: str, kind: str, what: str) -> None:
	"""An endpoint names a LIVE kind. Refused at use time, with retirement
	distinguished from absence: a retired kind is a name that existed, and
	saying so beats making the caller wonder about a typo."""
	row = store.conn.execute(
		"SELECT retired FROM kinds WHERE team=? AND handle=?",
		(team, kind)).fetchone()
	if row is None:
		raise WorkError(f"{what}: {team}.{kind} is not a registered endpoint")
	if row["retired"]:
		raise WorkError(f"{what}: {team}.{kind} is retired; a retired "
		                f"endpoint takes no new work")


def _member(store: Authority, team: str, member: str) -> None:
	if store.conn.execute("SELECT 1 FROM members WHERE team=? AND handle=?",
	                      (team, member)).fetchone() is None:
		raise WorkError(f"{team}.{member} is not a registered member")


def _recompute_ready(conn, work_id: str) -> None:
	"""Readiness from CURRENT state: open, and no open children.

	(A3 adds open blockers to the conjunction.) This is the single place
	readiness is computed, called by whichever transition changed an input —
	never by a reader, because reads are pure."""
	row = conn.execute("SELECT status FROM work WHERE id=?",
	                   (work_id,)).fetchone()
	if row is None:
		return
	open_children = conn.execute(
		"SELECT COUNT(*) AS n FROM work WHERE parent=? AND status=?",
		(work_id, OPEN)).fetchone()["n"]
	open_blockers = conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work ON work.id = edges.blocker "
		"WHERE edges.work=? AND work.status=?",
		(work_id, OPEN)).fetchone()["n"]
	ready = 1 if (row["status"] == OPEN and open_children == 0
	              and open_blockers == 0) else 0
	conn.execute("UPDATE work SET ready=? WHERE id=?", (ready, work_id))


def create_work(store: Authority, *, team: str, kind: str, title: str,
                origin: str, author: str, body: str,
                parent: str | None = None,
                classification: str | None = None) -> dict:
	"""A Work and its first message, atomically — creation must be cheap or
	mandatory Work scope becomes authoring ceremony (confirmed behavior).

	`author` is `member` within `team`. The new Work's `Current` is
	`team.kind`, resolved and validated now, at creation."""
	if not isinstance(title, str) or not title.strip():
		raise WorkError("a work title must be non-empty")
	if origin not in ORIGINS:
		raise WorkError(f"origin {origin!r} is not one of {ORIGINS}; origin "
		                f"is immutable history and is not free text")
	if classification is not None and classification not in CLASSIFICATIONS:
		raise WorkError(f"classification {classification!r} is not one of "
		                f"{CLASSIFICATIONS}")
	if not isinstance(body, str) or not body:
		raise WorkError("the first message body must be non-empty")
	store._team(team)
	_endpoint(store, team, kind, "create")
	_member(store, team, author)
	if parent is not None:
		parent_row = _work(store, parent)
		if parent_row["status"] != OPEN:
			raise WorkError(f"parent {parent} is {parent_row['status']}; a "
			                f"closed work does not grow new children — reopen "
			                f"it first, visibly")

	prefix = store.meta()["authority_uuid"][:8]

	def mutate(conn, seq):
		work_id = f"{prefix}-W{seq}"
		conn.execute(
			"INSERT INTO work (id, team, title, origin, classification, "
			"status, parent, current_team, current_kind, ready, created_seq) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
			(work_id, team, title, origin, classification, OPEN, parent,
			 team, kind, seq))
		conn.execute(
			"INSERT INTO messages (seq, work, author_team, author, body, ts) "
			"VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, work_id, team, author, body))
		conn.execute(
			"INSERT INTO work_participants (work, team, added_seq) "
			"VALUES (?, ?, ?)", (work_id, team, seq))
		_recompute_ready(conn, work_id)
		if parent is not None:
			_recompute_ready(conn, parent)
		mutate.work_id = work_id

	result = store._write("create_work", f"{team}.{author}",
	                      {"team": team, "kind": kind, "title": title,
	                       "origin": origin, "parent": parent}, mutate)
	result["work_id"] = mutate.work_id
	return result


def close_work(store: Authority, work_id: str, *, actor_team: str,
               actor: str, disposition: str) -> dict:
	"""Terminal close: no current and no next endpoint afterwards, and the
	ancestor gate recomputes. Refused while required descendants are open —
	closure rolls UP through recomputation, never down through force."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if row["status"] == CLOSED:
		raise WorkError(f"{work_id} is already closed")
	if not isinstance(disposition, str) or not disposition.strip():
		raise WorkError("a terminal close records a disposition")
	open_children = store.conn.execute(
		"SELECT id FROM work WHERE parent=? AND status=?",
		(work_id, OPEN)).fetchall()
	if open_children:
		raise WorkError(
			f"{work_id} has open children "
			f"({', '.join(child['id'] for child in open_children)}); root "
			f"closure while required descendants remain open is refused")

	def mutate(conn, seq):
		conn.execute(
			"UPDATE work SET status=?, ready=0, current_team=NULL, "
			"current_kind=NULL, next_team=NULL, next_kind=NULL, closed_seq=? "
			"WHERE id=?", (CLOSED, seq, work_id))
		if row["parent"] is not None:
			_recompute_ready(conn, row["parent"])
		# THE FAN-OUT, level-triggered: every dependent recomputes from its
		# own current blocker set. No message is addressed to anyone; a
		# dependent with other open blockers simply stays unready.
		for dependent in conn.execute(
				"SELECT work FROM edges WHERE blocker=?", (work_id,)):
			_recompute_ready(conn, dependent["work"])

	# The endpoint being cleared is RECORDED in the close event, because it
	# is what reopen restores: the live row forgets it deliberately, and
	# history is where cleared facts live.
	return store._write("close_work", f"{actor_team}.{actor}",
	                    {"work": work_id, "disposition": disposition,
	                     "was_current_team": row["current_team"],
	                     "was_current_kind": row["current_kind"]}, mutate)


def reopen_work(store: Authority, work_id: str, *, actor_team: str,
                actor: str, reason: str) -> dict:
	"""Reopen is close's mirror THROUGH THE SAME RECOMPUTATION: the ancestor
	gate visibly reopens because its readiness inputs changed, not because a
	special inverse path went looking for it."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if row["status"] != CLOSED:
		raise WorkError(f"{work_id} is not closed")
	if not isinstance(reason, str) or not reason.strip():
		raise WorkError("reopening records a reason")
	if row["parent"] is not None:
		parent_row = _work(store, row["parent"])
		if parent_row["status"] == CLOSED:
			raise WorkError(
				f"parent {row['parent']} is closed; reopen the ancestry "
				f"first so the gate reopens visibly top-down")

	# The endpoint to restore comes from the CLOSE EVENT, not from the live
	# row — close cleared the row on purpose, and restoring from it would
	# restore NULL and reopen the work with nobody responsible, which is the
	# one state the finding forbids ("no open work may be left without a
	# responsible endpoint").
	closing = store.conn.execute(
		"SELECT payload FROM events WHERE kind='close_work' "
		"AND json_extract(payload, '$.work') = ? "
		"ORDER BY seq DESC LIMIT 1", (work_id,)).fetchone()
	if closing is None:
		raise WorkError(f"{work_id} is closed but has no close event; the "
		                f"authority is inconsistent and reopening would guess")
	import json as _json
	was = _json.loads(closing["payload"])
	restore_team = was.get("was_current_team") or row["team"]
	restore_kind = was.get("was_current_kind")
	if restore_kind is None:
		raise WorkError(
			f"{work_id}'s close event records no prior endpoint; reopening "
			f"would leave open work with nobody responsible")

	def mutate(conn, seq):
		conn.execute(
			"UPDATE work SET status=?, closed_seq=NULL, current_team=?, "
			"current_kind=? WHERE id=?",
			(OPEN, restore_team, restore_kind, work_id))
		_recompute_ready(conn, work_id)
		if row["parent"] is not None:
			_recompute_ready(conn, row["parent"])
		# Reopen is the same recomputation in the other direction: every
		# dependent that became ready when this closed becomes blocked again
		# because its INPUTS changed — there is no retraction walk to get
		# wrong, which is the entire argument for level-triggering.
		for dependent in conn.execute(
				"SELECT work FROM edges WHERE blocker=?", (work_id,)):
			_recompute_ready(conn, dependent["work"])

	return store._write("reopen_work", f"{actor_team}.{actor}",
	                    {"work": work_id, "reason": reason}, mutate)


def _would_cycle(conn, work_id: str, blocker_id: str) -> list[str] | None:
	"""Does `blocker` already wait on `work`, through the UNION graph?

	"Waits on" is one relation with two sources: a parent waits on its
	children (containment), and a work waits on its blockers (dependency).
	A cycle in the union deadlocks even when each graph alone is acyclic —
	so the walk follows both, and it runs INSIDE the write transaction,
	because two concurrent inserts can each be acyclic alone and cyclic
	together, and the IMMEDIATE lock is what serializes them."""
	stack, seen = [(blocker_id, [blocker_id])], set()
	while stack:
		node, path = stack.pop()
		if node == work_id:
			return path
		if node in seen:
			continue
		seen.add(node)
		for child in conn.execute("SELECT id FROM work WHERE parent=?",
		                          (node,)):
			stack.append((child["id"], path + [child["id"]]))
		for edge in conn.execute("SELECT blocker FROM edges WHERE work=?",
		                         (node,)):
			stack.append((edge["blocker"], path + [edge["blocker"]]))
	return None


def add_dependency(store: Authority, work_id: str, blocker_id: str, *,
                   actor_team: str, actor: str) -> dict:
	"""`work_id` blocked_by `blocker_id` — the ONLY thing that gates
	readiness across records (labels are inert, by clarification). Cross-team
	on purpose; that is the convergence model."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	blocker = _work(store, blocker_id)
	if work_id == blocker_id:
		raise WorkError(f"{work_id} cannot block itself")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work takes "
		                f"no new blockers — reopen it first, visibly")
	if store.conn.execute("SELECT 1 FROM edges WHERE work=? AND blocker=?",
	                      (work_id, blocker_id)).fetchone():
		raise WorkError(f"{work_id} is already blocked by {blocker_id}")

	def mutate(conn, seq):
		path = _would_cycle(conn, work_id, blocker_id)
		if path is not None:
			raise WorkError(
				f"blocking {work_id} on {blocker_id} closes a loop through "
				f"{' -> '.join(path)}; a required-edge cycle is everyone "
				f"waiting forever, and it is refused at insertion")
		conn.execute(
			"INSERT INTO edges (work, blocker, created_seq) VALUES (?, ?, ?)",
			(work_id, blocker_id, seq))
		_recompute_ready(conn, work_id)

	return store._write("add_dependency", f"{actor_team}.{actor}",
	                    {"work": work_id, "blocker": blocker_id,
	                     "blocker_status": blocker["status"]}, mutate)


# -- A4: tags, obligations, seen, planned Next -------------------------------

def _expand_include(store: Authority, selectors) -> list[tuple[str, str]]:
	"""`+` expansion: comma-lists and wildcards, over LIVE endpoints only,
	deduplicated, deterministic. The exact expansion is recorded with the
	publication (ruled), so the sender and agents can see who was reached."""
	if isinstance(selectors, str):
		selectors = [part for part in selectors.split(",") if part]
	endpoints: list[tuple[str, str]] = []
	seen_pairs = set()
	for selector in selectors:
		team_part, dot, kind_part = selector.partition(".")
		if not dot:
			raise WorkError(f"include selector {selector!r} is not "
			                f"team.kind shaped")
		clauses, params = ["retired = 0"], []
		if team_part != "*":
			clauses.append("team = ?"); params.append(team_part)
		if kind_part != "*":
			clauses.append("handle = ?"); params.append(kind_part)
		rows = store.conn.execute(
			"SELECT team, handle FROM kinds WHERE " + " AND ".join(clauses) +
			" ORDER BY team, handle", params).fetchall()
		if not rows and team_part != "*" and kind_part != "*":
			raise WorkError(f"include selector {selector!r} matches no live "
			                f"endpoint; a tag that lands nowhere is refused "
			                f"at tag time, not discovered later")
		for row in rows:
			pair = (row["team"], row["handle"])
			if pair not in seen_pairs:
				seen_pairs.add(pair)
				endpoints.append(pair)
	return endpoints


def _one_endpoint(store: Authority, endpoint: str, what: str) -> tuple[str, str]:
	"""`@` and `=>` name EXACTLY ONE resolved destination (cardinality
	ruling): no wildcard, no comma, and it must resolve to a live kind."""
	if "," in endpoint or "*" in endpoint:
		raise WorkError(
			f"{what} names exactly one endpoint; {endpoint!r} fans out, and "
			f"only + may do that. A bulk operation must create separate "
			f"single-destination obligations, visibly.")
	team, dot, kind = endpoint.partition(".")
	if not dot or not team or not kind:
		raise WorkError(f"{what} target {endpoint!r} is not team.kind shaped")
	_endpoint(store, team, kind, what)
	return team, kind


def post_message(store: Authority, work_id: str, *, author_team: str,
                 author: str, body: str, include=(),
                 request: str | None = None,
                 pass_to: str | None = None,
                 set_next: str | None = None) -> dict:
	"""One discussion message, carrying this operation's tags.

	`include` is the only fan-out; `request` (`@`) creates one obligation and
	the Work stays with its Current; `pass_to` (`=>`) moves the one Current —
	and when it names the stored planned Next, it CONSUMES it and audits as
	`return`. Setting `set_next` requires `pass_to`: a planned return is a
	property of a pass, not a free-floating edit."""
	_member(store, author_team, author)
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; discussion on closed "
		                f"work reopens it first, visibly")
	if store.conn.execute(
			"SELECT 1 FROM work_participants WHERE work=? AND team=?",
			(work_id, author_team)).fetchone() is None:
		raise WorkError(f"{author_team} does not participate in {work_id}")
	if not isinstance(body, str) or not body:
		raise WorkError("a message body must be non-empty")
	if request is not None and pass_to is not None:
		raise WorkError("one message carries one operation: @ requests a "
		                "response, => passes the baton; asking both at once "
		                "makes the obligation ambiguous")
	if set_next is not None and pass_to is None:
		raise WorkError("a planned Next is set by a pass; there is nothing "
		                "to return from otherwise")

	included = _expand_include(store, include) if include else []
	requested = _one_endpoint(store, request, "@ request") if request else None
	passed = _one_endpoint(store, pass_to, "=> pass") if pass_to else None
	planned = _one_endpoint(store, set_next, "planned Next") if set_next else None

	event_kind = "post_message"
	consumes_next = False
	if passed is not None:
		if (row["current_team"], row["current_kind"]) == passed:
			raise WorkError(f"{work_id} is already at "
			                f"{passed[0]}.{passed[1]}; a pass moves the baton")
		if (row["next_team"], row["next_kind"]) == passed:
			event_kind, consumes_next = "return", True
		else:
			# The audit trail distinguishes all three: a message, a pass,
			# and the consuming return. An agent reading events must never
			# have to re-derive which was which from the payload.
			event_kind = "pass"
	elif requested is not None:
		event_kind = "request"

	def mutate(conn, seq):
		conn.execute(
			"INSERT INTO messages (seq, work, author_team, author, body, ts) "
			"VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, work_id, author_team, author, body))
		touched_teams = {team for team, _kind in included}
		if requested is not None:
			conn.execute(
				"INSERT INTO obligations (seq, work, message_seq, team, kind) "
				"VALUES (?, ?, ?, ?, ?)",
				(seq, work_id, seq, requested[0], requested[1]))
			touched_teams.add(requested[0])
		if passed is not None:
			if consumes_next:
				conn.execute(
					"UPDATE work SET current_team=?, current_kind=?, "
					"next_team=NULL, next_kind=NULL WHERE id=?",
					(passed[0], passed[1], work_id))
			else:
				# An unconsumed planned Next stays VISIBLY set unless this
				# pass plants a new one — it is never silently cleared.
				conn.execute(
					"UPDATE work SET current_team=?, current_kind=?, "
					"next_team=COALESCE(?, next_team), "
					"next_kind=COALESCE(?, next_kind) WHERE id=?",
					(passed[0], passed[1],
					 planned[0] if planned else None,
					 planned[1] if planned else None, work_id))
			touched_teams.add(passed[0])
		for team in sorted(touched_teams):
			conn.execute(
				"INSERT OR IGNORE INTO work_participants "
				"(work, team, added_seq) VALUES (?, ?, ?)",
				(work_id, team, seq))

	payload = {"work": work_id, "body_bytes": len(body.encode("utf-8")),
	           "include": [f"{team}.{kind}" for team, kind in included],
	           "request": request, "pass": pass_to,
	           "set_next": set_next, "consumed_next": consumes_next}
	result = store._write(event_kind, f"{author_team}.{author}",
	                      payload, mutate)
	result["included"] = payload["include"]
	return result


def respond_obligation(store: Authority, obligation_seq: int, *,
                       team: str, member: str, body: str) -> dict:
	"""The obligated endpoint's team answers; the obligation resolves with
	the response message in one transaction."""
	_member(store, team, member)
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (obligation_seq,)).fetchone()
	if obligation is None:
		raise WorkError(f"no obligation {obligation_seq}")
	if obligation["status"] != "pending":
		raise WorkError(f"obligation {obligation_seq} is already "
		                f"{obligation['status']}")
	if obligation["team"] != team:
		raise WorkError(f"obligation {obligation_seq} belongs to "
		                f"{obligation['team']}.{obligation['kind']}; "
		                f"{team} cannot discharge it")
	if not isinstance(body, str) or not body:
		raise WorkError("a response body must be non-empty")

	def mutate(conn, seq):
		conn.execute(
			"INSERT INTO messages (seq, work, author_team, author, body, ts) "
			"VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, obligation["work"], team, member, body))
		conn.execute(
			"UPDATE obligations SET status='responded', resolved_seq=? "
			"WHERE seq=?", (seq, obligation_seq))

	return store._write("respond", f"{team}.{member}",
	                    {"obligation": obligation_seq,
	                     "work": obligation["work"]}, mutate)


def dispose_obligation(store: Authority, obligation_seq: int, *,
                       team: str, member: str, disposition: str) -> dict:
	"""No response is owed after all — said explicitly, with a reason, by the
	obligated team. Route policy may classify status as no-action (ruled)."""
	_member(store, team, member)
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (obligation_seq,)).fetchone()
	if obligation is None:
		raise WorkError(f"no obligation {obligation_seq}")
	if obligation["status"] != "pending":
		raise WorkError(f"obligation {obligation_seq} is already "
		                f"{obligation['status']}")
	if obligation["team"] != team:
		raise WorkError(f"obligation {obligation_seq} belongs to "
		                f"{obligation['team']}.{obligation['kind']}")
	if not isinstance(disposition, str) or not disposition.strip():
		raise WorkError("a disposition needs words")

	def mutate(conn, seq):
		conn.execute(
			"UPDATE obligations SET status='disposed', resolved_seq=? "
			"WHERE seq=?", (seq, obligation_seq))

	return store._write("dispose", f"{team}.{member}",
	                    {"obligation": obligation_seq,
	                     "work": obligation["work"],
	                     "disposition": disposition}, mutate)


def mark_seen(store: Authority, work_id: str, *, team: str, member: str,
              up_to_seq: int) -> dict:
	"""THE ONLY WRITER of the seen cursor (pinned ruling 4). Idempotent and
	monotonic: marking backwards is a no-op reported as such, because a
	cursor that can move backwards makes `New` count things twice."""
	_member(store, team, member)
	_work(store, work_id)
	if not isinstance(up_to_seq, int) or up_to_seq < 0:
		raise WorkError("mark_seen takes a non-negative sequence number")
	current = store.conn.execute(
		"SELECT seq FROM seen WHERE team=? AND member=? AND work=?",
		(team, member, work_id)).fetchone()
	if current is not None and current["seq"] >= up_to_seq:
		return {"seq": None, "kind": "mark_seen", "advanced": False,
		        "cursor": current["seq"]}

	def mutate(conn, seq):
		conn.execute(
			"INSERT INTO seen (team, member, work, seq) VALUES (?, ?, ?, ?) "
			"ON CONFLICT (team, member, work) DO UPDATE SET seq=excluded.seq",
			(team, member, work_id, up_to_seq))

	result = store._write("mark_seen", f"{team}.{member}",
	                      {"work": work_id, "up_to": up_to_seq}, mutate)
	result["advanced"] = True
	result["cursor"] = up_to_seq
	return result
