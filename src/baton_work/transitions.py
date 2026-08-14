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
# WS-1 ruling: classification is NEVER null — `unknown` is the canonical
# default, a value like any other, and clients must not read meaning into
# absence.
CLASSIFICATIONS = ("unknown", "suspected-defect", "confirmed-defect",
                   "limitation", "duplicate", "design-choice", "rejection")
# WS-1 ruling: the operational phase enum, canonical protocol values only.
# Compact TUI renderings (queue/rsrch/wait/actve/rview/park) are
# PRESENTATION vocabulary and are never accepted as mutation values.
PHASES = ("queued", "research", "waiting", "active", "review", "parked")
# Phases a creation may choose directly. `waiting` needs a recorded wake
# condition and `parked` needs a reason — both enter only through their
# explicit transitions, or a creation could mint the loose end the ruling
# forbids.
CREATION_PHASES = ("queued", "research", "active", "review")
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


def resolve_endpoint(conn, team: str, kind: str, what: str) -> dict:
	"""One endpoint, resolved through the ACCEPTED route to its role and
	handlers, with the configuration generation stamped — C4's snapshot.

	Runs on the transaction's own connection when recording history (the
	fourth appearance of validate-inside-the-lock: a regen committing between
	a pre-read and the write would otherwise stamp a stale resolution), and
	on the read connection when the projection resolves for display.
	Refuses partial resolution: an endpoint whose kind has no live route is
	an error, never a bare string in history."""
	row = conn.execute(
		"SELECT route, retired FROM kinds WHERE team=? AND handle=?",
		(team, kind)).fetchone()
	if row is None:
		raise WorkError(f"{what}: {team}.{kind} is not a configured endpoint")
	if row["retired"]:
		raise WorkError(f"{what}: {team}.{kind} is retired; a retired "
		                f"endpoint takes no new work")
	if row["route"] is None:
		raise WorkError(f"{what}: {team}.{kind} has no route in the accepted "
		                f"configuration; endpoint history is never recorded "
		                f"partly resolved")
	route_row = conn.execute(
		"SELECT role FROM routes WHERE team=? AND handle=? AND removed=0",
		(team, row["route"])).fetchone()
	if route_row is None:
		raise WorkError(f"{what}: {team}.{kind} routes through "
		                f"{row['route']!r}, which is not live")
	handlers = [entry["member"] for entry in conn.execute(
		"SELECT member FROM route_handlers WHERE team=? AND route=? "
		"ORDER BY member", (team, row["route"]))]
	generation = conn.execute(
		"SELECT value FROM meta WHERE key='accepted_generation'").fetchone()
	return {"endpoint": f"{team}.{kind}", "route": row["route"],
	        "role": route_row["role"], "handlers": handlers,
	        "generation": int(generation["value"]) if generation else 0}


def _emit(conn, kind: str, actor: str, payload: dict) -> int:
	"""One ADDITIONAL audit event inside an already-open write transaction —
	the mechanism behind the atomic `wake`: the seq is allocated from the
	same counter, so density holds and the event exists iff the transaction
	that satisfied the condition committed."""
	import json as _json
	import time as _time
	seq = conn.execute(
		"UPDATE sequence SET value = value + 1 WHERE id = 1 "
		"RETURNING value").fetchone()["value"]
	conn.execute(
		"INSERT INTO events (seq, kind, actor, payload, ts) "
		"VALUES (?, ?, ?, ?, ?)",
		(seq, kind, actor, _json.dumps(payload, sort_keys=True),
		 _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())))
	return seq


def _open_gates(conn, work_id: str) -> int:
	"""The aggregate wake condition's inputs: open required children plus
	open explicit blockers."""
	children = conn.execute(
		"SELECT COUNT(*) AS n FROM work WHERE parent=? AND status=?",
		(work_id, OPEN)).fetchone()["n"]
	blockers = conn.execute(
		"SELECT COUNT(*) AS n FROM edges JOIN work ON work.id=edges.blocker "
		"WHERE edges.work=? AND work.status=?",
		(work_id, OPEN)).fetchone()["n"]
	return children + blockers


def _sweep_wakes(conn, actor: str) -> None:
	"""Level-triggered wake: every OPEN waiting Work whose recorded
	condition is now satisfied atomically becomes `queued`, with one `wake`
	event in the SAME transaction that satisfied it. Runs at the end of
	every transaction that can close a gate or complete an obligation
	(close, respond, dispose — and reopen, which can only re-satisfy a
	stale condition, never un-record one). A racing retry finds the phase
	already `queued` and wakes nothing twice."""
	for row in conn.execute(
			"SELECT id, wait_type, wait_obligation FROM work "
			"WHERE status=? AND phase='waiting'", (OPEN,)).fetchall():
		satisfied = False
		if row["wait_type"] == "gates":
			satisfied = _open_gates(conn, row["id"]) == 0
		elif row["wait_type"] == "obligation":
			pending = conn.execute(
				"SELECT status FROM obligations WHERE seq=?",
				(row["wait_obligation"],)).fetchone()
			satisfied = pending is not None and \
				pending["status"] != "pending"
		if satisfied:
			conn.execute(
				"UPDATE work SET phase='queued', wait_type=NULL, "
				"wait_obligation=NULL WHERE id=?", (row["id"],))
			_emit(conn, "wake", actor,
			      {"work": row["id"], "from": "waiting", "to": "queued",
			       "condition": {"type": row["wait_type"],
			                     "obligation": row["wait_obligation"]}})


def _obligation_gate(conn, obligation, actor_team: str, actor: str,
                     what: str) -> dict:
	"""R1 matrix: answering or disposing one exact @ obligation belongs to
	a currently resolved handler of the route the obligation names — and
	grants no other mutation authority. Live resolution, in the lock."""
	resolution = resolve_endpoint(conn, obligation["team"],
	                              obligation["kind"], what)
	if actor_team != obligation["team"] or \
			actor not in resolution["handlers"]:
		raise WorkError(
			f"{what}: {actor_team}.{actor} is not a resolved handler of "
			f"{resolution['endpoint']} (handlers {resolution['handlers']}); "
			f"participation never substitutes for ownership")
	return resolution


def _handler_gate(conn, work_id: str, actor_team: str, actor: str,
                  what: str) -> dict:
	"""WS-1 direct transition authority, checked IN THE LOCK: the actor
	must be a currently resolved handler of the Work's Current route under
	the accepted generation at commit. Returns the resolution snapshot for
	the audit payload. `@` respondents and other teams get an explicit
	refusal — input never grants mutation authority."""
	row = conn.execute(
		"SELECT current_team, current_kind FROM work WHERE id=?",
		(work_id,)).fetchone()
	if row["current_team"] is None or row["current_kind"] is None:
		raise WorkError(f"{what}: {work_id} has no Current endpoint")
	resolution = resolve_endpoint(conn, row["current_team"],
	                              row["current_kind"], what)
	if actor_team != row["current_team"] or \
			actor not in resolution["handlers"]:
		raise WorkError(
			f"{what}: {actor_team}.{actor} is not a resolved handler of "
			f"{resolution['endpoint']} (route {resolution['route']!r}, "
			f"handlers {resolution['handlers']}); contribution and @ input "
			f"never grant workflow mutation authority")
	return resolution


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
                classification: str | None = None,
                phase: str | None = None) -> dict:
	"""A Work and its first message, atomically — creation must be cheap or
	mandatory Work scope becomes authoring ceremony (confirmed behavior).

	`author` is `member` within `team`. The new Work's `Current` is
	`team.kind`, resolved and validated now, at creation."""
	if not isinstance(title, str) or not title.strip():
		raise WorkError("a work title must be non-empty")
	if origin not in ORIGINS:
		raise WorkError(f"origin {origin!r} is not one of {ORIGINS}; origin "
		                f"is immutable history and is not free text")
	classification = "unknown" if classification is None else classification
	if classification not in CLASSIFICATIONS:
		raise WorkError(f"classification {classification!r} is not one of "
		                f"{CLASSIFICATIONS}")
	phase = "queued" if phase is None else phase
	if phase not in PHASES:
		raise WorkError(f"phase {phase!r} is not one of {PHASES}; compact "
		                f"display values are presentation only and are not "
		                f"accepted as mutation values")
	if phase not in CREATION_PHASES:
		raise WorkError(
			f"a work is not created {phase!r}: waiting needs a recorded "
			f"wake condition and parking needs a reason — use the explicit "
			f"phase transition after creation")
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
	payload = {"team": team, "kind": kind, "title": title,
	           "origin": origin, "parent": parent,
	           "classification": classification, "phase": phase}

	def mutate(conn, seq):
		work_id = f"{prefix}-W{seq}"
		# In-lock recheck (WF-09 class): the parent must still be open at
		# commit — a closed work does not grow children through a race.
		if parent is not None:
			live_parent = conn.execute(
				"SELECT status FROM work WHERE id=?", (parent,)).fetchone()
			if live_parent["status"] != OPEN:
				raise WorkError(
					f"parent {parent} is {live_parent['status']}; a closed "
					f"work does not grow new children — reopen it first, "
					f"visibly")
			# R1 matrix: attaching child Work is a workflow decision of the
			# PARENT's Current handler; root creation stays with the team.
			payload["authorization"] = _handler_gate(
				conn, parent, team, author, "attach child")
		payload["resolution"] = resolve_endpoint(conn, team, kind, "create")
		conn.execute(
			"INSERT INTO work (id, team, title, origin, classification, "
			"phase, status, parent, current_team, current_kind, ready, "
			"created_seq) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
			(work_id, team, title, origin, classification, phase, OPEN,
			 parent, team, kind, seq))
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
	                      payload, mutate)
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

	# The endpoint being cleared is RECORDED in the close event, because it
	# is what reopen restores: the live row forgets it deliberately, and
	# history is where cleared facts live. Its value is filled in by mutate,
	# from the row AS COMMITTED — a pass can land between the pre-read and
	# this lock, and reopen must restore the endpoint that was really live.
	payload = {"work": work_id, "disposition": disposition,
	           "was_current_team": row["current_team"],
	           "was_current_kind": row["current_kind"]}

	def mutate(conn, seq):
		# WF-09 race 2: status and children rechecked inside the lock — a
		# competing close, reopen-of-a-child, or late create can commit
		# between the optimistic checks above and this transaction.
		live = conn.execute(
			"SELECT status, parent, current_team, current_kind "
			"FROM work WHERE id=?", (work_id,)).fetchone()
		if live["status"] == CLOSED:
			raise WorkError(f"{work_id} is already closed")
		still_open = conn.execute(
			"SELECT id FROM work WHERE parent=? AND status=?",
			(work_id, OPEN)).fetchall()
		if still_open:
			raise WorkError(
				f"{work_id} has open children "
				f"({', '.join(child['id'] for child in still_open)}); root "
				f"closure while required descendants remain open is refused")
		# WS-1 review R1: terminal close is a workflow-state decision, so
		# the same one ownership rule applies — a currently resolved
		# handler of the Current route, in the lock, snapshot recorded.
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "close")
		payload["was_current_team"] = live["current_team"]
		payload["was_current_kind"] = live["current_kind"]
		conn.execute(
			"UPDATE work SET status=?, ready=0, current_team=NULL, "
			"current_kind=NULL, next_team=NULL, next_kind=NULL, closed_seq=? "
			"WHERE id=?", (CLOSED, seq, work_id))
		if live["parent"] is not None:
			_recompute_ready(conn, live["parent"])
		# THE FAN-OUT, level-triggered: every dependent recomputes from its
		# own current blocker set. No message is addressed to anyone; a
		# dependent with other open blockers simply stays unready.
		for dependent in conn.execute(
				"SELECT work FROM edges WHERE blocker=?", (work_id,)):
			_recompute_ready(conn, dependent["work"])
		# WS-1: this close may have shut the LAST gate some waiting work
		# recorded — the wake commits atomically with it, or not at all.
		_sweep_wakes(conn, f"{actor_team}.{actor}")

	return store._write("close_work", f"{actor_team}.{actor}",
	                    payload, mutate)


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
		# In-lock recheck (WF-09 class), COMPLETE: everything the reopen
		# depends on is re-read from the transaction connection — the
		# status (a competing reopen), the parent's status (a parent may
		# close after the optimistic ancestry check; an open child beneath
		# a terminal parent is the state the gate exists to prevent), and
		# the LATEST close event (a whole reopen/pass/close cycle can
		# commit while this reopen waits for its lock, and restoring from
		# the obsolete event resurrects a superseded endpoint).
		live = conn.execute("SELECT status, parent FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != CLOSED:
			raise WorkError(f"{work_id} is not closed")
		if live["parent"] is not None:
			live_parent = conn.execute(
				"SELECT status FROM work WHERE id=?",
				(live["parent"],)).fetchone()
			if live_parent["status"] == CLOSED:
				raise WorkError(
					f"parent {live['parent']} is closed; reopen the "
					f"ancestry first so the gate reopens visibly top-down")
		latest = conn.execute(
			"SELECT payload FROM events WHERE kind='close_work' "
			"AND json_extract(payload, '$.work') = ? "
			"ORDER BY seq DESC LIMIT 1", (work_id,)).fetchone()
		if latest is None:
			raise WorkError(
				f"{work_id} is closed but has no close event; the "
				f"authority is inconsistent and reopening would guess")
		committed = _json.loads(latest["payload"])
		restore_team = committed.get("was_current_team") or row["team"]
		restore_kind = committed.get("was_current_kind")
		if restore_kind is None:
			raise WorkError(
				f"{work_id}'s close event records no prior endpoint; "
				f"reopening would leave open work with nobody responsible")
		# R1 matrix: reopen restores Current, so it belongs to whoever
		# currently resolves as that Current's handler.
		resolution = resolve_endpoint(conn, restore_team, restore_kind,
		                              "reopen")
		if actor_team != restore_team or \
				actor not in resolution["handlers"]:
			raise WorkError(
				f"reopen: {actor_team}.{actor} is not a resolved handler "
				f"of {resolution['endpoint']} (handlers "
				f"{resolution['handlers']}), the Current this reopen "
				f"restores; participation never substitutes for ownership")
		payload["authorization"] = resolution
		conn.execute(
			"UPDATE work SET status=?, closed_seq=NULL, current_team=?, "
			"current_kind=? WHERE id=?",
			(OPEN, restore_team, restore_kind, work_id))
		_recompute_ready(conn, work_id)
		if live["parent"] is not None:
			_recompute_ready(conn, live["parent"])
		# Reopen is the same recomputation in the other direction: every
		# dependent that became ready when this closed becomes blocked again
		# because its INPUTS changed — there is no retraction walk to get
		# wrong, which is the entire argument for level-triggering.
		for dependent in conn.execute(
				"SELECT work FROM edges WHERE blocker=?", (work_id,)):
			_recompute_ready(conn, dependent["work"])
		# WS-1: reopening cannot un-record a wake condition, but the
		# reopened work itself may have been waiting on gates that all
		# closed while it was closed — the sweep keeps no false waiting.
		_sweep_wakes(conn, f"{actor_team}.{actor}")

	payload = {"work": work_id, "reason": reason}
	return store._write("reopen_work", f"{actor_team}.{actor}",
	                    payload, mutate)


# -- WS-1: public classification and operational phase -----------------------

def classify(store: Authority, work_id: str, *, actor_team: str, actor: str,
             classification: str) -> dict:
	"""An explicit, audited classification change by a currently resolved
	handler of the Work's Current route. Canonical values only — compact
	display vocabulary is never a mutation value. Origin is untouched."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if classification not in CLASSIFICATIONS:
		raise WorkError(f"classification {classification!r} is not one of "
		                f"{CLASSIFICATIONS}; compact display values are "
		                f"presentation only")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"refuses classification changes — reopen it first, "
		                f"visibly")

	payload = {"work": work_id, "from": row["classification"],
	           "to": classification}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, classification FROM work WHERE id=?",
			(work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"refuses classification changes — reopen it "
			                f"first, visibly")
		if live["classification"] == classification:
			raise WorkError(f"{work_id} is already classified "
			                f"{classification!r}")
		payload["from"] = live["classification"]
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "classify")
		conn.execute("UPDATE work SET classification=? WHERE id=?",
		             (classification, work_id))

	return store._write("classify", f"{actor_team}.{actor}", payload, mutate)


def set_phase(store: Authority, work_id: str, *, actor_team: str, actor: str,
              phase: str, reason: str | None = None,
              wait: str | int | None = None) -> dict:
	"""An explicit, audited operational-phase change by a currently
	resolved handler of the Current route.

	The special rules, exactly as ruled: `parked` needs a non-empty reason,
	keeps its one accountable Current, and leaves ONLY through explicit
	parked→queued; `waiting` records exactly one typed wake condition
	(`wait="gates"` for the aggregate required-Work gate, or an obligation
	seq for one exact pending `@`), refuses an already-satisfied condition,
	and leaves ONLY through the condition-bound audited wake; closed work
	refuses. Everything else moves freely between ordinary open phases —
	review/rework cycles included. A pass never changes phase."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if phase not in PHASES:
		raise WorkError(f"phase {phase!r} is not one of {PHASES}; compact "
		                f"display values are presentation only and are not "
		                f"accepted as mutation values")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"refuses phase changes")
	if phase == "parked":
		if not isinstance(reason, str) or not reason.strip():
			raise WorkError(
				"parking requires a reason: parked work has NO wake "
				"condition and can sit forever, so the why must be on "
				"the record")
	if phase == "waiting":
		if wait is None:
			raise WorkError(
				"waiting requires a recorded wake condition: "
				"wait='gates' for the aggregate required-Work gate, or "
				"the seq of one exact pending @ obligation")
		if wait != "gates" and not isinstance(wait, int):
			raise WorkError(f"wait condition {wait!r} is neither 'gates' "
			                f"nor an obligation seq")
	elif wait is not None:
		raise WorkError(f"a wake condition belongs to 'waiting' only, "
		                f"not {phase!r}")

	payload = {"work": work_id, "from": row["phase"], "to": phase,
	           "reason": reason}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, phase FROM work WHERE id=?",
			(work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"refuses phase changes")
		if live["phase"] == phase:
			raise WorkError(f"{work_id} is already {phase}")
		if live["phase"] == "parked" and phase != "queued":
			raise WorkError(
				f"{work_id} is parked; parked work resumes only through "
				f"the explicit parked→queued transition, deliberately")
		if live["phase"] == "waiting":
			raise WorkError(
				f"{work_id} is waiting on its recorded condition; waiting "
				f"leaves only through the condition-bound audited wake")
		payload["from"] = live["phase"]
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "set_phase")
		wait_type, wait_obligation = None, None
		if phase == "waiting":
			if wait == "gates":
				if _open_gates(conn, work_id) == 0:
					raise WorkError(
						f"{work_id} has no open required child or blocker; "
						f"an already-satisfied wait condition is refused "
						f"rather than creating a loose end")
				wait_type = "gates"
			else:
				obligation = conn.execute(
					"SELECT work, status FROM obligations WHERE seq=?",
					(wait,)).fetchone()
				if obligation is None:
					raise WorkError(f"no obligation {wait}")
				if obligation["work"] != work_id:
					raise WorkError(
						f"obligation {wait} belongs to "
						f"{obligation['work']}; a work waits on its OWN "
						f"outstanding @ request")
				if obligation["status"] != "pending":
					raise WorkError(
						f"obligation {wait} is already "
						f"{obligation['status']}; an already-satisfied "
						f"wait condition is refused rather than creating "
						f"a loose end")
				wait_type, wait_obligation = "obligation", wait
		payload["wait"] = None if wait_type is None else \
			{"type": wait_type, "obligation": wait_obligation}
		conn.execute(
			"UPDATE work SET phase=?, wait_type=?, wait_obligation=? "
			"WHERE id=?", (phase, wait_type, wait_obligation, work_id))

	return store._write("set_phase", f"{actor_team}.{actor}", payload, mutate)


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

	payload = {"work": work_id, "blocker": blocker_id,
	           "blocker_status": blocker["status"]}

	def mutate(conn, seq):
		# In-lock recheck (WF-09 class): the closed-takes-no-blockers and
		# duplicate checks above are optimistic; they hold only if rechecked
		# under the same lock as the cycle walk below.
		live = conn.execute("SELECT status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"takes no new blockers — reopen it first, "
			                f"visibly")
		# R1 matrix: changing a Work's dependencies belongs to its Current
		# handler.
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "add_dependency")
		if conn.execute("SELECT 1 FROM edges WHERE work=? AND blocker=?",
		                (work_id, blocker_id)).fetchone():
			raise WorkError(f"{work_id} is already blocked by {blocker_id}")
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
	                    payload, mutate)


# -- A4: tags, obligations, seen, planned Next -------------------------------

def _expand_selectors(conn, selectors) -> list[tuple[str, str]]:
	"""`+` expansion: comma-lists and wildcards, over LIVE endpoints only,
	deduplicated, deterministic. The exact expansion is recorded with the
	publication (ruled), so the sender and agents can see who was reached.

	Takes a CONNECTION, not the store: wildcard membership is itself endpoint
	resolution (C4 review R1), so the authoritative expansion runs inside the
	write transaction, against the same accepted generation that stamps the
	snapshots. Any earlier expansion is an optimistic pre-read only."""
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
		rows = conn.execute(
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


def _expand_include(store: Authority, selectors) -> list[tuple[str, str]]:
	"""The OPTIMISTIC pre-lock expansion: same parse, same refusals, run
	before the write path is entered so a malformed or landing-nowhere
	selector never opens a transaction. Its membership result is advisory —
	the expansion that gets recorded is redone inside the write transaction
	by `_expand_selectors(conn, ...)`, under the generation that commits."""
	return _expand_selectors(store.conn, selectors)


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
	if not isinstance(body, str) or not body:
		raise WorkError("a message body must be non-empty")
	if request is not None and pass_to is not None:
		raise WorkError("one message carries one operation: @ requests a "
		                "response, => passes the baton; asking both at once "
		                "makes the obligation ambiguous")
	if set_next is not None and pass_to is None:
		raise WorkError("a planned Next is set by a pass; there is nothing "
		                "to return from otherwise")

	if include:
		# Optimistic early refusal only; the recorded expansion is redone
		# inside the write transaction (C4 review R1).
		_expand_include(store, include)
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
		# WF-09 race 2: everything decided from the pre-lock row is
		# revalidated HERE. A message must not land on a work that closed
		# underneath it, and a pass whose already-at / consumes-Next
		# decision no longer matches the live row lost a race — it refuses
		# rather than committing a mislabeled or resurrecting transition.
		live = conn.execute(
			"SELECT status, current_team, current_kind, next_team, "
			"next_kind FROM work WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; discussion on "
			                f"closed work reopens it first, visibly")
		if passed is not None:
			# WS-1 review R1: delegation is ownership transfer, and ONLY a
			# currently resolved handler of the Current route may pass the
			# baton on. Participation — including having answered an @ —
			# never authorizes acting as Current. The snapshot is recorded.
			payload["authorization"] = _handler_gate(
				conn, work_id, author_team, author, "=> pass")
			if (live["current_team"], live["current_kind"]) == passed:
				raise WorkError(f"{work_id} is already at "
				                f"{passed[0]}.{passed[1]}; a pass moves "
				                f"the baton")
			if (((live["next_team"], live["next_kind"]) == passed)
					!= consumes_next):
				raise WorkError(
					f"{work_id}'s planned Next changed while this pass was "
					f"being prepared; it lost a concurrent race — retry "
					f"against the current state")
		conn.execute(
			"INSERT INTO messages (seq, work, author_team, author, body, ts) "
			"VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, work_id, author_team, author, body))
		# C4: EVERY endpoint this operation touches is resolved here, inside
		# the transaction, and the snapshots land in the committed payload —
		# never partly resolved, never bare. That includes the WILDCARD
		# MEMBERSHIP itself (review R1): the selectors are re-expanded from
		# this connection, so the recorded set and its snapshots describe
		# the same accepted generation — the one that commits.
		included = _expand_selectors(conn, include) if include else []
		payload["include"] = [
			resolve_endpoint(conn, team, kind, "+ include")
			for team, kind in included]
		# R1 re-review: contribution has NO participation barrier — any
		# configured member may chip in on open Work, and their team is
		# recorded as a participant in THIS transaction so New and
		# accounting have a durable basis. Ownership stays where it is.
		touched_teams = {team for team, _kind in included}
		touched_teams.add(author_team)
		if requested is not None:
			# R1 matrix: creating an @ obligation is a workflow decision of
			# the Work's Current handler.
			payload["authorization"] = _handler_gate(
				conn, work_id, author_team, author, "@ request")
			resolution = resolve_endpoint(conn, requested[0], requested[1],
			                              "@ request")
			payload["request_resolution"] = resolution
			import json as _json
			conn.execute(
				"INSERT INTO obligations (seq, work, message_seq, team, "
				"kind, route, role, handlers, generation) "
				"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
				(seq, work_id, seq, requested[0], requested[1],
				 resolution["route"], resolution["role"],
				 _json.dumps(resolution["handlers"]),
				 resolution["generation"]))
			touched_teams.add(requested[0])
		if passed is not None:
			payload["pass_resolution"] = resolve_endpoint(
				conn, passed[0], passed[1], "=> pass")
			if planned is not None:
				payload["next_resolution"] = resolve_endpoint(
					conn, planned[0], planned[1], "planned Next")
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
	           "include": [],
	           "request": request, "pass": pass_to,
	           "set_next": set_next, "consumed_next": consumes_next}
	result = store._write(event_kind, f"{author_team}.{author}",
	                      payload, mutate)
	result["included"] = [entry["endpoint"] for entry in payload["include"]]
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

	payload = {"obligation": obligation_seq, "work": obligation["work"]}

	def mutate(conn, seq):
		# WF-09 race 1: the pending check above is optimistic — a competing
		# terminal action can commit between it and this lock. The check
		# that counts runs HERE (validate-inside-the-lock).
		live = conn.execute("SELECT status FROM obligations WHERE seq=?",
		                    (obligation_seq,)).fetchone()
		if live["status"] != "pending":
			raise WorkError(f"obligation {obligation_seq} is already "
			                f"{live['status']}")
		payload["authorization"] = _obligation_gate(
			conn, obligation, team, member, "respond")
		conn.execute(
			"INSERT INTO messages (seq, work, author_team, author, body, ts) "
			"VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, obligation["work"], team, member, body))
		conn.execute(
			"UPDATE obligations SET status='responded', resolved_seq=? "
			"WHERE seq=?", (seq, obligation_seq))
		# WS-1: completing an obligation may be the recorded wake condition.
		_sweep_wakes(conn, f"{team}.{member}")

	return store._write("respond", f"{team}.{member}", payload, mutate)


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

	payload = {"obligation": obligation_seq, "work": obligation["work"],
	           "disposition": disposition}

	def mutate(conn, seq):
		# WF-09 race 1, the other competitor: same in-lock recheck.
		live = conn.execute("SELECT status FROM obligations WHERE seq=?",
		                    (obligation_seq,)).fetchone()
		if live["status"] != "pending":
			raise WorkError(f"obligation {obligation_seq} is already "
			                f"{live['status']}")
		payload["authorization"] = _obligation_gate(
			conn, obligation, team, member, "dispose")
		conn.execute(
			"UPDATE obligations SET status='disposed', resolved_seq=? "
			"WHERE seq=?", (seq, obligation_seq))
		# WS-1: completion by disposal satisfies the condition the same way.
		_sweep_wakes(conn, f"{team}.{member}")

	return store._write("dispose", f"{team}.{member}", payload, mutate)


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
