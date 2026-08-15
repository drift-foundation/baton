"""Work transitions: create, close, classify, phase — Gate A step A2.

Every transition is one authority write transaction, and READINESS IS
LEVEL-TRIGGERED: nothing here walks a graph forwarding an event. A transition
recomputes the readiness of exactly the rows whose inputs it changed, from
their CURRENT state — so replay is idempotent and a crash re-runs harmlessly
(ruling: level-triggered readiness; the plan's A3 break-sweep exists to keep
it this way). Closure is IMMUTABLE (WS-2): there is no reopen; later
evidence becomes follow-up Work.

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
# WS-2 ruling: every terminal close records exactly one of these.
OUTCOMES = ("satisfying", "non-satisfying")
# WS-2 verification vocabulary (ruled): the verifier's raw observation and
# the provider reviewer's separate assessment — two immutable axes.
OBSERVATIONS = ("passed", "failed", "unable")
ASSESSMENTS = ("accepted", "rejected", "inconclusive")
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
	if store.conn.execute(
			"SELECT 1 FROM members WHERE team=? AND handle=? AND removed=0",
			(team, member)).fetchone() is None:
		raise WorkError(f"{team}.{member} is not a registered member")


def _member_active(conn, team: str, member: str) -> None:
	"""R65: the COMMITTING transaction revalidates that the actor is a
	currently configured member — a config acceptance removing them
	between the optimistic check and the lock must win."""
	if conn.execute(
			"SELECT 1 FROM members WHERE team=? AND handle=? AND removed=0",
			(team, member)).fetchone() is None:
		raise WorkError(f"{team}.{member} is not a member of the "
		                f"currently accepted configuration")


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
	(close, respond, dispose). A racing retry finds the phase
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


def _born(conn, work_id: str) -> str:
	"""The discussion born with a Work — found derivably (it shares the
	Work's created_seq), NOT a stored primary relation (WS-4 R54). The
	internal Slice-A bridge routes Work-addressed message writes here;
	Slice B removes the bridge."""
	row = conn.execute(
		"SELECT discussions.id AS id FROM discussions JOIN work "
		"ON work.created_seq = discussions.created_seq WHERE work.id=?",
		(work_id,)).fetchone()
	if row is None:
		raise WorkError(f"{work_id} has no born discussion; the "
		                f"authority is inconsistent")
	return row["id"]


def _live_context(conn, discussion_id: str) -> bool:
	"""The pinned live-context boundary: at least one currently labelled
	OPEN Work."""
	return conn.execute(
		"SELECT 1 FROM discussion_labels JOIN work "
		"ON work.id = discussion_labels.work "
		"WHERE discussion_labels.discussion=? AND work.status='open'",
		(discussion_id,)).fetchone() is not None


def _join_discussion(conn, discussion_id: str, team: str, seq: int) -> None:
	"""Monotonic discussion-team participation (WS-4 R56): once added, a
	team stays; nothing in this slice removes it."""
	conn.execute(
		"INSERT OR IGNORE INTO discussion_participants "
		"(discussion, team, added_seq) VALUES (?, ?, ?)",
		(discussion_id, team, seq))


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
                phase: str | None = None,
                follow_up_of: str | None = None) -> dict:
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
	if follow_up_of is not None:
		predecessor = _work(store, follow_up_of)
		if predecessor["status"] != CLOSED:
			raise WorkError(
				f"{follow_up_of} is still open; follow_up_of preserves "
				f"the context of TERMINALLY CLOSED work — an open "
				f"predecessor is ordinary relation, not a follow-up")
	if parent is not None:
		parent_row = _work(store, parent)
		if parent_row["status"] != OPEN:
			raise WorkError(f"parent {parent} is {parent_row['status']}; a "
			                f"closed work does not grow new children; create "
			                f"follow-up work instead")

	prefix = store.meta()["authority_uuid"][:8]
	payload = {"team": team, "kind": kind, "title": title,
	           "origin": origin, "parent": parent,
	           "classification": classification, "phase": phase,
	           "follow_up_of": follow_up_of}

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
					f"work does not grow new children; create follow-up "
					f"work instead")
			# R1 matrix: attaching child Work is a workflow decision of the
			# PARENT's Current handler; root creation stays with the team.
			payload["authorization"] = _handler_gate(
				conn, parent, team, author, "attach child")
		payload["resolution"] = resolve_endpoint(conn, team, kind, "create")
		if follow_up_of is not None:
			live_predecessor = conn.execute(
				"SELECT status FROM work WHERE id=?",
				(follow_up_of,)).fetchone()
			if live_predecessor["status"] != CLOSED:
				raise WorkError(
					f"{follow_up_of} is still open; follow_up_of "
					f"preserves the context of TERMINALLY CLOSED work")
		conn.execute(
			"INSERT INTO work (id, team, title, origin, classification, "
			"phase, status, parent, current_team, current_kind, ready, "
			"follow_up_of, created_seq) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
			(work_id, team, title, origin, classification, phase, OPEN,
			 parent, team, kind, follow_up_of, seq))
		discussion_id = f"{prefix}-D{seq}"
		conn.execute(
			"INSERT INTO discussions (id, created_seq, created_ts) "
			"VALUES (?, ?, ?)", (discussion_id, seq, store.clock()))
		conn.execute(
			"INSERT INTO discussion_labels (discussion, work, added_seq) "
			"VALUES (?, ?, ?)", (discussion_id, work_id, seq))
		_join_discussion(conn, discussion_id, team, seq)
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, discussion_id, team, author, body))
		_recompute_ready(conn, work_id)
		if parent is not None:
			_recompute_ready(conn, parent)
		mutate.work_id = work_id
		mutate.discussion_id = discussion_id

	result = store._write("create_work", f"{team}.{author}",
	                      payload, mutate)
	result["discussion"] = mutate.discussion_id
	result["work_id"] = mutate.work_id
	return result


def close_work(store: Authority, work_id: str, *, actor_team: str,
               actor: str, disposition: str,
               outcome: str | None = None) -> dict:
	"""Terminal close: IMMUTABLE (WS-2 ruling — there is no reopen; later
	evidence becomes follow-up Work). No current and no next endpoint
	afterwards, and the ancestor gate recomputes: closure rolls UP through
	recomputation, never down through force. Every terminal close names
	exactly `satisfying` or `non-satisfying` — universal, independent of
	graph shape; clients never infer the result from prose."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if row["status"] == CLOSED:
		raise WorkError(f"{work_id} is already closed")
	if not isinstance(disposition, str) or not disposition.strip():
		raise WorkError("a terminal close records a disposition")
	if outcome not in OUTCOMES:
		raise WorkError(
			f"a terminal close names exactly one outcome of {OUTCOMES}; "
			f"got {outcome!r} — the result is never inferred from "
			f"classification or disposition prose")
	open_children = store.conn.execute(
		"SELECT id FROM work WHERE parent=? AND status=?",
		(work_id, OPEN)).fetchall()
	if open_children:
		raise WorkError(
			f"{work_id} has open children "
			f"({', '.join(child['id'] for child in open_children)}); root "
			f"closure while required descendants remain open is refused")

	# The endpoint being cleared is RECORDED in the close event, because it
	# the live row forgets deliberately, and history is where cleared
	# facts live. Its value is filled in by mutate, from the row AS
	# COMMITTED — a pass can land between the pre-read and this lock.
	payload = {"work": work_id, "disposition": disposition,
	           "outcome": outcome,
	           "was_current_team": row["current_team"],
	           "was_current_kind": row["current_kind"]}

	def mutate(conn, seq):
		# WF-09 race 2: status and children rechecked inside the lock — a
		# competing close or late create can commit between the optimistic
		# checks above and this transaction.
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
		# WS-2 group 2: rounds end with their work — no assignment stays
		# actionable. Group 3: the close AUDITS the concluded round's
		# evidence basis — candidate, receipt fraction, raw observation
		# summary, elapsed exposure, and the pending assignments about to
		# be withdrawn — recording the basis of the judgment without
		# fabricating feedback.
		concluding = conn.execute(
			"SELECT * FROM rounds WHERE work=? AND status='open'",
			(work_id,)).fetchone()
		if concluding is not None:
			tally = {"passed": 0, "failed": 0, "unable": 0}
			assigned = reported = 0
			still_pending = []
			for entry in conn.execute(
					"SELECT team, kind, status, observation FROM "
					"obligations WHERE work=? AND round=? "
					"AND flavor='verification'",
					(work_id, concluding["round"])):
				assigned += 1
				if entry["status"] == "reported":
					reported += 1
					tally[entry["observation"]] += 1
				elif entry["status"] == "pending":
					still_pending.append(
						f"{entry['team']}.{entry['kind']}")
			payload["round_summary"] = {
				"round": concluding["round"],
				"candidate": concluding["candidate"],
				"progress": f"{reported}/{assigned}",
				"observations": tally,
				"review_at": concluding["review_at"],
				"deadline_generation":
					concluding["deadline_generation"],
				"created_ts": concluding["created_ts"],
				"closed_ts": store.clock(),
				"withdrawn_pending": still_pending,
				"basis": disposition,
			}
		conn.execute(
			"UPDATE rounds SET status='closed', ended_seq=? "
			"WHERE work=? AND status='open'", (seq, work_id))
		conn.execute(
			"UPDATE work SET status=?, ready=0, outcome=?, "
			"current_team=NULL, current_kind=NULL, next_team=NULL, "
			"next_kind=NULL, closed_seq=? WHERE id=?",
			(CLOSED, outcome, seq, work_id))
		# WS-2 group-1 correction (ruled): terminal close atomically
		# WITHDRAWS every pending exact @ obligation this work carries —
		# classic requests and verification assignments alike — so closed
		# history can never gain a late answer. Each withdrawal points at
		# its own audited withdraw event.
		_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
		                  "the carrying work closed")
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
		                f"refuses classification changes; closure is terminal")

	payload = {"work": work_id, "from": row["classification"],
	           "to": classification}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, classification FROM work WHERE id=?",
			(work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"refuses classification changes; closure is terminal")
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
					"SELECT work, status, flavor FROM obligations "
					"WHERE seq=?", (wait,)).fetchone()
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
				if obligation["flavor"] != "response":
					raise WorkError(
						f"obligation {wait} is a verification "
						f"assignment; feedback never transitions Work, so "
						f"it cannot be a wake condition (WS-2 ruling)")
				wait_type, wait_obligation = "obligation", wait
		payload["wait"] = None if wait_type is None else \
			{"type": wait_type, "obligation": wait_obligation}
		conn.execute(
			"UPDATE work SET phase=?, wait_type=?, wait_obligation=? "
			"WHERE id=?", (phase, wait_type, wait_obligation, work_id))

	return store._write("set_phase", f"{actor_team}.{actor}", payload, mutate)


# -- WS-2 group 2: candidate verification rounds ------------------------------

def _canonical_instant(value, what: str) -> str:
	"""R41: a deadline is a REAL canonical UTC instant in exactly the
	supported representation (YYYY-MM-DDTHH:MM:SSZ) — not merely a nonblank
	string. Anything else refuses before any write path opens, so the
	database's lexicographic ordering stays a true time ordering."""
	import datetime as _datetime
	if not isinstance(value, str):
		raise WorkError(f"{what} must be a canonical UTC instant string")
	try:
		parsed = _datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
	except ValueError:
		raise WorkError(
			f"{what} {value!r} is not a canonical UTC instant "
			f"(YYYY-MM-DDTHH:MM:SSZ)") from None
	if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
		raise WorkError(
			f"{what} {value!r} does not round-trip canonically; refusing "
			f"an instant that would lie about its ordering")
	return value


def _round(store: Authority, work_id: str, round_number: int):
	row = store.conn.execute(
		"SELECT * FROM rounds WHERE work=? AND round=?",
		(work_id, round_number)).fetchone()
	if row is None:
		raise WorkError(f"{work_id} has no round {round_number}")
	return row


def create_round(store: Authority, work_id: str, *, actor_team: str,
                 actor: str, candidate: str, assign,
                 review_at: str | None = None) -> dict:
	"""One verification round for one EXACT candidate, with an exact
	selected set of verifier routes (each an @ verification obligation —
	actionable for testing WITHOUT clearing anyone's dependency, granting
	no mutation authority, and never a wake condition).

	Publishing a different candidate is a NEW round: any open round is
	superseded and its pending assignments are withdrawn with route
	notification — replies stay pinned to the exact candidate they tested
	and never carry forward silently."""
	_member(store, actor_team, actor)
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"takes no verification rounds")
	if not isinstance(candidate, str) or not candidate.strip():
		raise WorkError("a round names its exact candidate/artifact; "
		                "candidate identity is required and immutable")
	if isinstance(assign, str):
		assign = [assign]
	if not assign:
		raise WorkError("a round selects at least one exact verifier route")
	selected = []
	for endpoint in assign:
		pair = _one_endpoint(store, endpoint, "verification assignment")
		if pair in selected:
			raise WorkError(
				f"verification assignment {endpoint!r} is selected twice; "
				f"one round creates at most one obligation per endpoint")
		selected.append(pair)

	if review_at is not None:
		_canonical_instant(review_at, "review_at")
		if review_at <= store.clock():
			raise WorkError(
				f"review_at {review_at!r} is not later than now "
				f"({store.clock()}); a deadline born expired is a loose "
				f"end")
	payload = {"work": work_id, "candidate": candidate,
	           "review_at": review_at,
	           "selected": [f"{team}.{kind}" for team, kind in selected]}

	def mutate(conn, seq):
		import json as _json
		live = conn.execute("SELECT status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"takes no verification rounds")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "create round")
		previous = conn.execute(
			"SELECT round FROM rounds WHERE work=? AND status='open'",
			(work_id,)).fetchone()
		if previous is not None:
			conn.execute(
				"UPDATE rounds SET status='superseded', ended_seq=? "
				"WHERE work=? AND round=?",
				(seq, work_id, previous["round"]))
			_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
			                  "superseded by a new candidate round",
			                  round_number=previous["round"])
			payload["supersedes"] = previous["round"]
		# R42: ONE transaction-local instant — the deadline is rechecked
		# against it inside the committing write (it may have passed since
		# the optimistic check), and it becomes the round's created_ts.
		now = store.clock()
		if review_at is not None and review_at <= now:
			raise WorkError(
				f"review_at {review_at!r} is not later than now ({now}); "
				f"a deadline born expired is a loose end")
		number = (conn.execute(
			"SELECT COALESCE(MAX(round), 0) AS n FROM rounds WHERE work=?",
			(work_id,)).fetchone()["n"]) + 1
		conn.execute(
			"INSERT INTO rounds (work, round, candidate, status, "
			"review_at, deadline_generation, created_ts, created_seq) "
			"VALUES (?, ?, ?, 'open', ?, ?, ?, ?)",
			(work_id, number, candidate, review_at,
			 1 if review_at else 0, now, seq))
		payload["round"] = number
		payload["assignments"] = []
		for team, kind in selected:
			resolution = resolve_endpoint(conn, team, kind,
			                              "verification assignment")
			assignment_seq = _emit(
				conn, "assign", f"{actor_team}.{actor}",
				{"work": work_id, "round": number,
				 "candidate": candidate, "resolution": resolution})
			conn.execute(
				"INSERT INTO obligations (seq, work, message_seq, team, "
				"kind, route, role, handlers, generation, flavor, round) "
				"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'verification', ?)",
				(assignment_seq, work_id, seq, team, kind,
				 resolution["route"], resolution["role"],
				 _json.dumps(resolution["handlers"]),
				 resolution["generation"], number))
			payload["assignments"].append(
				{"obligation": assignment_seq, "resolution": resolution})
		mutate.round_number = number

	result = store._write("create_round", f"{actor_team}.{actor}",
	                      payload, mutate)
	result["round"] = mutate.round_number
	result["assignments"] = [entry["obligation"]
	                         for entry in payload["assignments"]]
	return result


def _withdraw_pending(conn, work_id: str, actor: str, reason: str,
                      round_number=None) -> None:
	"""Withdraw pending obligations (optionally one round's) with the
	audited per-obligation notification — shared by close, supersession,
	and abandon. Withdrawal never fabricates feedback."""
	import json as _json
	clause = "work=? AND status='pending'"
	params = [work_id]
	if round_number is not None:
		clause += " AND round=?"
		params.append(round_number)
	for obligation in conn.execute(
			f"SELECT seq, team, kind, route, role, handlers, generation "
			f"FROM obligations WHERE {clause}", params).fetchall():
		withdraw_seq = _emit(
			conn, "withdraw", actor,
			{"work": work_id, "obligation": obligation["seq"],
			 "endpoint": f"{obligation['team']}.{obligation['kind']}",
			 "route": obligation["route"], "role": obligation["role"],
			 "handlers": _json.loads(obligation["handlers"])
			 if obligation["handlers"] else [],
			 "generation": obligation["generation"], "reason": reason})
		conn.execute(
			"UPDATE obligations SET status='withdrawn', resolved_seq=? "
			"WHERE seq=?", (withdraw_seq, obligation["seq"]))


def report(store: Authority, obligation_seq: int, *, team: str, member: str,
           observation: str, evidence: str) -> dict:
	"""The verifier's IMMUTABLE raw observation: exactly passed, failed, or
	unable, with evidence, pinned to its assignment/round/candidate. It
	never votes, transitions, satisfies, wakes, or closes anything."""
	_member(store, team, member)
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (obligation_seq,)).fetchone()
	if obligation is None:
		raise WorkError(f"no obligation {obligation_seq}")
	if obligation["flavor"] != "verification":
		raise WorkError(f"obligation {obligation_seq} is a classic @ "
		                f"request; it completes by respond or dispose")
	if observation not in OBSERVATIONS:
		raise WorkError(f"a report observes exactly one of {OBSERVATIONS}; "
		                f"got {observation!r}")
	if not isinstance(evidence, str) or not evidence.strip():
		raise WorkError("a report attaches its evidence")
	if obligation["status"] != "pending":
		raise WorkError(f"assignment {obligation_seq} is already "
		                f"{obligation['status']}")

	pinned = _round(store, obligation["work"], obligation["round"])
	payload = {"work": obligation["work"], "obligation": obligation_seq,
	           "round": obligation["round"],
	           "candidate": pinned["candidate"],
	           "observation": observation, "evidence": evidence}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status FROM obligations WHERE seq=?",
			(obligation_seq,)).fetchone()
		if live["status"] != "pending":
			raise WorkError(f"assignment {obligation_seq} is already "
			                f"{live['status']}")
		payload["authorization"] = _obligation_gate(
			conn, obligation, team, member, "report")
		conn.execute(
			"UPDATE obligations SET status='reported', observation=?, "
			"evidence=?, resolved_seq=? WHERE seq=?",
			(observation, evidence, seq, obligation_seq))

	return store._write("report", f"{team}.{member}", payload, mutate)


def assess(store: Authority, obligation_seq: int, *, actor_team: str,
           actor: str, assessment: str, rationale: str) -> dict:
	"""The provider reviewer's SEPARATE immutable judgment of a report:
	accepted, rejected, or inconclusive, with rationale. It never rewrites
	the raw observation; a changed mind is a new superseding act."""
	_member(store, actor_team, actor)
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (obligation_seq,)).fetchone()
	if obligation is None:
		raise WorkError(f"no obligation {obligation_seq}")
	if obligation["flavor"] != "verification":
		raise WorkError(f"obligation {obligation_seq} is a classic @ "
		                f"request; there is no report to assess")
	if assessment not in ASSESSMENTS:
		raise WorkError(f"an assessment is exactly one of {ASSESSMENTS}; "
		                f"got {assessment!r}")
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("an assessment records its rationale")
	row = _work(store, obligation["work"])
	if row["status"] != OPEN:
		raise WorkError(f"{obligation['work']} is {row['status']}; a "
		                f"closed work refuses assessment")

	payload = {"work": obligation["work"], "obligation": obligation_seq,
	           "assessment": assessment, "rationale": rationale}

	def mutate(conn, seq):
		prior = conn.execute(
			"SELECT seq FROM assessments WHERE obligation=? "
			"ORDER BY seq DESC LIMIT 1", (obligation_seq,)).fetchone()
		payload["supersedes"] = prior["seq"] if prior else None
		live_work = conn.execute(
			"SELECT status FROM work WHERE id=?",
			(obligation["work"],)).fetchone()
		if live_work["status"] != OPEN:
			raise WorkError(f"{obligation['work']} is "
			                f"{live_work['status']}; a closed work refuses "
			                f"assessment")
		live = conn.execute(
			"SELECT status FROM obligations WHERE seq=?",
			(obligation_seq,)).fetchone()
		if live["status"] != "reported":
			raise WorkError(
				f"assignment {obligation_seq} is {live['status']}; only a "
				f"returned report is assessed — assessment never invents "
				f"feedback")
		payload["authorization"] = _handler_gate(
			conn, obligation["work"], actor_team, actor, "assess")
		conn.execute(
			"INSERT INTO assessments (seq, obligation, assessment, "
			"rationale, actor) VALUES (?, ?, ?, ?, ?)",
			(seq, obligation_seq, assessment, rationale,
			 f"{actor_team}.{actor}"))

	return store._write("assess", f"{actor_team}.{actor}", payload, mutate)


def abandon_round(store: Authority, work_id: str, round_number: int, *,
                  actor_team: str, actor: str, reason: str) -> dict:
	"""End a round WITHOUT closing the work: pending assignments are
	withdrawn with route notification, candidate and report history stay
	immutable, and no provider or consumer lifecycle state changes."""
	_member(store, actor_team, actor)
	_work(store, work_id)
	existing = _round(store, work_id, round_number)
	if existing["status"] != "open":
		raise WorkError(f"round {round_number} of {work_id} is already "
		                f"{existing['status']}")
	if not isinstance(reason, str) or not reason.strip():
		raise WorkError("abandoning a round records a reason")

	payload = {"work": work_id, "round": round_number, "reason": reason}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status FROM rounds WHERE work=? AND round=?",
			(work_id, round_number)).fetchone()
		if live["status"] != "open":
			raise WorkError(f"round {round_number} of {work_id} is "
			                f"already {live['status']}")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "abandon round")
		conn.execute(
			"UPDATE rounds SET status='abandoned', ended_seq=? "
			"WHERE work=? AND round=?", (seq, work_id, round_number))
		_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
		                  reason, round_number=round_number)

	return store._write("abandon_round", f"{actor_team}.{actor}",
	                    payload, mutate)


def extend_round(store: Authority, work_id: str, round_number: int, *,
                 actor_team: str, actor: str, review_at: str) -> dict:
	"""Extend the SAME candidate's testing window: an explicit audited
	reviewer decision — never a hidden timer reset. All reports and pending
	assignments are retained; the deadline generation advances so due-ness
	is per-generation; repeated extensions are visible history. May also
	give a deadline to a round created without one."""
	_member(store, actor_team, actor)
	_work(store, work_id)
	existing = _round(store, work_id, round_number)
	if existing["status"] != "open":
		raise WorkError(f"round {round_number} of {work_id} is "
		                f"{existing['status']}; only an open round's window "
		                f"extends")
	if not isinstance(review_at, str) or not review_at.strip():
		raise WorkError("an extension names the new review_at instant")
	_canonical_instant(review_at, "review_at")
	if review_at <= store.clock():
		raise WorkError(
			f"review_at {review_at!r} is not later than now "
			f"({store.clock()}); a deadline born expired is a loose end")
	if existing["review_at"] is not None and \
			review_at <= existing["review_at"]:
		raise WorkError(
			f"review_at {review_at!r} does not extend the current window "
			f"({existing['review_at']}); an extension moves forward")

	payload = {"work": work_id, "round": round_number,
	           "candidate": existing["candidate"],
	           "from_review_at": existing["review_at"],
	           "to_review_at": review_at}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, review_at, deadline_generation FROM rounds "
			"WHERE work=? AND round=?", (work_id, round_number)).fetchone()
		if live["status"] != "open":
			raise WorkError(f"round {round_number} of {work_id} is "
			                f"{live['status']}; only an open round's "
			                f"window extends")
		if live["review_at"] is not None and \
				review_at <= live["review_at"]:
			raise WorkError(
				f"review_at {review_at!r} does not extend the current "
				f"window ({live['review_at']}); an extension moves forward")
		# R42: the deadline is rechecked against a transaction-local
		# instant inside the committing write.
		now = store.clock()
		if review_at <= now:
			raise WorkError(
				f"review_at {review_at!r} is not later than now ({now}); "
				f"a deadline born expired is a loose end")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "extend round")
		payload["deadline_generation"] = live["deadline_generation"] + 1
		conn.execute(
			"UPDATE rounds SET review_at=?, deadline_generation=? "
			"WHERE work=? AND round=?",
			(review_at, live["deadline_generation"] + 1, work_id,
			 round_number))

	return store._write("extend_round", f"{actor_team}.{actor}",
	                    payload, mutate)


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
	if blocker["status"] != OPEN:
		raise WorkError(
			f"{blocker_id} is {blocker['status']}; a dependency on finished "
			f"work gates nothing — depend on follow-up Work instead "
			f"(WS-2 ruling: new blockers target only open Work)")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work takes "
		                f"no new blockers; closure is terminal")
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
			                f"takes no new blockers; closure is terminal")
		# R1 matrix: changing a Work's dependencies belongs to its Current
		# handler.
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "add_dependency")
		if conn.execute("SELECT 1 FROM edges WHERE work=? AND blocker=?",
		                (work_id, blocker_id)).fetchone():
			raise WorkError(f"{work_id} is already blocked by {blocker_id}")
		live_blocker = conn.execute(
			"SELECT status FROM work WHERE id=?", (blocker_id,)).fetchone()
		if live_blocker["status"] != OPEN:
			raise WorkError(
				f"{blocker_id} is {live_blocker['status']}; a dependency "
				f"on finished work gates nothing — depend on follow-up "
				f"Work instead (WS-2 ruling: new blockers target only "
				f"open Work)")
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
		raise WorkError(f"{work_id} is {row['status']}; closed work is "
		                f"immutable history — new evidence belongs in "
		                f"follow-up work")
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
			                f"closed work is immutable history; new evidence "
			                f"belongs in follow-up work")
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
		born = _born(conn, work_id)
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, born, author_team, author, body))
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
			_join_discussion(conn, born, team, seq)

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
	if obligation["flavor"] != "response":
		raise WorkError(f"obligation {obligation_seq} is a verification "
		                f"assignment; it completes only by report or "
		                f"withdrawal")
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
		born = _born(conn, obligation["work"])
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, born, team, member, body))
		_join_discussion(conn, born, team, seq)
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
	if obligation["flavor"] != "response":
		raise WorkError(f"obligation {obligation_seq} is a verification "
		                f"assignment; it completes only by report or "
		                f"withdrawal")
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


def accept_obligation(store: Authority, obligation_seq: int, *,
                      actor_team: str, actor: str, body: str,
                      into: str | None = None,
                      create: dict | None = None) -> dict:
	"""WS-3: THE atomic provider acceptance. One transaction commits — or
	refuses whole — the obligation's terminal `accepted` state naming the
	provider Work, the rationale answered into the consumer's discussion,
	the provenance-carrying dependency edge, readiness recomputation, the
	exact-obligation wake (R47: the waiter wakes because its named
	condition completed; the new gate keeps it unready; gates-waiters do
	not wake), and — in the create form — the provider Work itself, whose
	creation IS the primary accept act (R48: history establishes the
	provider no later than the acceptance that names it).

	Authority (ruled): the pending exact @ grants its LIVE route handler
	this one narrow atomic authority over the requesting Work. `--into`
	adds same-team + open checks on the provider Work; its Current is
	recorded as evidence, not a second gate. `--create --parent` alone
	adds the separate live parent-Current handler gate.
	"""
	_member(store, actor_team, actor)
	obligation = store.conn.execute(
		"SELECT * FROM obligations WHERE seq=?", (obligation_seq,)).fetchone()
	if obligation is None:
		raise WorkError(f"no obligation {obligation_seq}")
	if obligation["flavor"] != "response":
		raise WorkError(f"obligation {obligation_seq} is a verification "
		                f"assignment; acceptance answers @ requests only")
	if obligation["status"] != "pending":
		raise WorkError(f"obligation {obligation_seq} is already "
		                f"{obligation['status']}")
	if not isinstance(body, str) or not body:
		raise WorkError("an acceptance records its rationale")
	if (into is None) == (create is None):
		raise WorkError("acceptance names exactly one provider: an "
		                "existing work (--into) or a new one (--create)")
	consumer_id = obligation["work"]
	provider_team = obligation["team"]

	if into is not None:
		provider_row = _work(store, into)
		if provider_row["team"] != provider_team:
			raise WorkError(
				f"{into} belongs to {provider_row['team']}; the "
				f"obligation was addressed to {provider_team}, and "
				f"acceptance may only gate on that team's work")
		if provider_row["status"] != OPEN:
			raise WorkError(f"{into} is {provider_row['status']}; a "
			                f"dependency on finished work gates nothing")
	else:
		kind = create.get("kind")
		title = create.get("title")
		classification = create.get("classification")
		classification = "unknown" if classification is None \
			else classification
		phase = create.get("phase")
		phase = "queued" if phase is None else phase
		parent = create.get("parent")
		create = dict(create, classification=classification, phase=phase)
		if not isinstance(title, str) or not title.strip():
			raise WorkError("a work title must be non-empty")
		_endpoint(store, provider_team, kind, "accept --create")
		if classification not in CLASSIFICATIONS:
			raise WorkError(f"classification {classification!r} is not "
			                f"one of {CLASSIFICATIONS}")
		if phase not in PHASES:
			raise WorkError(f"phase {phase!r} is not one of {PHASES}; "
			                f"compact display values are presentation "
			                f"only")
		if phase not in CREATION_PHASES:
			raise WorkError(
				f"a work is not created {phase!r}: waiting needs a "
				f"recorded wake condition and parking needs a reason")
		if parent is not None:
			parent_row = _work(store, parent)
			if parent_row["status"] != OPEN:
				raise WorkError(
					f"parent {parent} is {parent_row['status']}; a "
					f"closed work does not grow new children")

	prefix = store.meta()["authority_uuid"][:8]
	payload = {"obligation": obligation_seq, "work": consumer_id,
	           "provider": into, "created": create is not None,
	           "body_bytes": len(body.encode("utf-8"))}

	def mutate(conn, seq):
		import json as _json
		live = conn.execute("SELECT * FROM obligations WHERE seq=?",
		                    (obligation_seq,)).fetchone()
		if live["status"] != "pending":
			raise WorkError(f"obligation {obligation_seq} is already "
			                f"{live['status']}")
		# The ruled narrow grant: the LIVE route handler of the exact
		# pending request, in the lock, snapshot recorded.
		payload["authorization"] = _obligation_gate(
			conn, obligation, actor_team, actor, "accept")

		if into is not None:
			provider_id = into
			live_provider = conn.execute(
				"SELECT * FROM work WHERE id=?", (into,)).fetchone()
			if live_provider["status"] != OPEN:
				raise WorkError(f"{into} is {live_provider['status']}; a "
				                f"dependency on finished work gates "
				                f"nothing")
			# Provider Current: recorded EVIDENCE, never a gate — shown
			# explicitly unresolved rather than refusing (disposition 2).
			try:
				payload["provider_current"] = resolve_endpoint(
					conn, live_provider["current_team"],
					live_provider["current_kind"], "accept evidence")
			except WorkError:
				payload["provider_current"] = {
					"endpoint":
					f"{live_provider['current_team']}."
					f"{live_provider['current_kind']}",
					"route": None, "role": None, "handlers": [],
					"generation": None}
		else:
			# R48: the provider Work's creation IS this primary act — it
			# exists at the acceptance's own sequence, never after it.
			provider_id = f"{prefix}-W{seq}"
			kind = create["kind"]
			resolution = resolve_endpoint(conn, provider_team, kind,
			                              "accept --create")
			payload["resolution"] = resolution
			parent = create.get("parent")
			if parent is not None:
				live_parent = conn.execute(
					"SELECT status FROM work WHERE id=?",
					(parent,)).fetchone()
				if live_parent["status"] != OPEN:
					raise WorkError(
						f"parent {parent} is {live_parent['status']}; a "
						f"closed work does not grow new children")
				# Disposition 5: the SEPARATE parent-Current handler gate.
				payload["parent_authorization"] = _handler_gate(
					conn, parent, actor_team, actor,
					"accept --create --parent")
			conn.execute(
				"INSERT INTO work (id, team, title, origin, "
				"classification, phase, status, parent, current_team, "
				"current_kind, ready, created_seq) "
				"VALUES (?, ?, ?, 'external-report', ?, ?, ?, ?, ?, ?, "
				"0, ?)",
				(provider_id, provider_team, create["title"],
				 create["classification"], create["phase"], OPEN, parent,
				 provider_team, kind, seq))
			provider_discussion = f"{prefix}-D{seq}"
			conn.execute(
				"INSERT INTO discussions (id, created_seq, created_ts) "
				"VALUES (?, ?, ?)",
				(provider_discussion, seq, store.clock()))
			conn.execute(
				"INSERT INTO discussion_labels (discussion, work, "
				"added_seq) VALUES (?, ?, ?)",
				(provider_discussion, provider_id, seq))
			_join_discussion(conn, provider_discussion, provider_team, seq)
			conn.execute(
				"INSERT INTO messages (seq, discussion, author_team, "
				"author, body, ts) VALUES (?, ?, ?, ?, ?, "
				"datetime('now'))",
				(seq, provider_discussion, actor_team, actor, body))
			_recompute_ready(conn, provider_id)
			if parent is not None:
				_recompute_ready(conn, parent)
		payload["provider"] = provider_id

		# The dependency edge, with the existing in-lock protections and
		# the WS-3 provenance.
		if consumer_id == provider_id:
			raise WorkError(f"{consumer_id} cannot block itself")
		if conn.execute(
				"SELECT 1 FROM edges WHERE work=? AND blocker=?",
				(consumer_id, provider_id)).fetchone():
			raise WorkError(f"{consumer_id} is already blocked by "
			                f"{provider_id}")
		live_consumer = conn.execute(
			"SELECT status FROM work WHERE id=?",
			(consumer_id,)).fetchone()
		if live_consumer["status"] != OPEN:
			raise WorkError(f"{consumer_id} is {live_consumer['status']}; "
			                f"a closed work takes no new blockers")
		path = _would_cycle(conn, consumer_id, provider_id)
		if path is not None:
			raise WorkError(
				f"blocking {consumer_id} on {provider_id} closes a loop "
				f"through {' -> '.join(path)}; a required-edge cycle is "
				f"everyone waiting forever")
		conn.execute(
			"INSERT INTO edges (work, blocker, via_obligation, "
			"created_seq) VALUES (?, ?, ?, ?)",
			(consumer_id, provider_id, obligation_seq, seq))

		# The obligation reaches its ruled terminal state, addressed to
		# THIS act and naming the provider it accepted into.
		conn.execute(
			"UPDATE obligations SET status='accepted', resolved_seq=?, "
			"accepted_into=? WHERE seq=?",
			(seq, provider_id, obligation_seq))

		# The rationale lands in the CONSUMER's discussion as its own
		# ordered, audited act (R48: distinct and later in the same
		# transaction).
		message_seq = _emit(
			conn, "post_message", f"{actor_team}.{actor}",
			{"work": consumer_id,
			 "body_bytes": len(body.encode("utf-8")),
			 "via_accept": seq, "include": [], "request": None,
			 "pass": None, "set_next": None, "consumed_next": False})
		consumer_born = _born(conn, consumer_id)
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(message_seq, consumer_born, actor_team, actor, body))
		_join_discussion(conn, consumer_born, actor_team, message_seq)

		_recompute_ready(conn, consumer_id)
		# R47: the exact-obligation waiter wakes (its named condition
		# completed) with readiness kept false by the new gate; a
		# gates-waiter gained a gate and does not wake.
		_sweep_wakes(conn, f"{actor_team}.{actor}")
		mutate.provider_id = provider_id

	result = store._write("accept", f"{actor_team}.{actor}", payload, mutate)
	result["provider"] = mutate.provider_id
	result["obligation"] = obligation_seq
	result["work"] = consumer_id
	result["created"] = create is not None
	result["edge"] = {"work": consumer_id,
	                  "blocker": mutate.provider_id,
	                  "via_obligation": obligation_seq}
	return result


def mark_seen(store: Authority, work_id: str, *, team: str, member: str,
              up_to_seq: int) -> dict:
	"""THE ONLY WRITER of seen cursors (pinned ruling 4) — Work-addressed
	BRIDGE form (Slice A internal; Slice B removes it): advances the
	member's cursor on EVERY discussion currently labelled to the Work,
	monotonically, so "New drops to zero" stays true under per-discussion
	cursors. The canonical public form is `seen_discussion`."""
	_member(store, team, member)
	_work(store, work_id)
	if not isinstance(up_to_seq, int) or up_to_seq < 0:
		raise WorkError("mark_seen takes a non-negative sequence number")
	if up_to_seq > store.last_seq():
		raise WorkError(
			f"cursor {up_to_seq} is beyond the observed authority "
			f"sequence ({store.last_seq()}); a mark names what was read, "
			f"never the future")
	labelled = [row["discussion"] for row in store.conn.execute(
		"SELECT discussion FROM discussion_labels WHERE work=?",
		(work_id,))]
	advanced_any = False
	floor = 0
	for discussion in labelled:
		current = store.conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND "
			"discussion=?", (team, member, discussion)).fetchone()
		if current is not None:
			floor = max(floor, current["seq"])
		if current is None or current["seq"] < up_to_seq:
			advanced_any = True
	if not advanced_any:
		return {"seq": None, "kind": "mark_seen", "advanced": False,
		        "cursor": floor}

	def mutate(conn, seq):
		_member_active(conn, team, member)
		advanced = False
		for discussion in labelled:
			current = conn.execute(
				"SELECT seq FROM seen WHERE team=? AND member=? AND "
				"discussion=?", (team, member, discussion)).fetchone()
			if current is None or current["seq"] < up_to_seq:
				advanced = True
			conn.execute(
				"INSERT INTO seen (team, member, discussion, seq) "
				"VALUES (?, ?, ?, ?) "
				"ON CONFLICT(team, member, discussion) DO UPDATE SET "
				"seq = MAX(seq, excluded.seq)",
				(team, member, discussion, up_to_seq))
		if not advanced:
			raise _NoAdvance(up_to_seq)

	try:
		result = store._write("mark_seen", f"{team}.{member}",
		                      {"work": work_id, "discussions": labelled,
		                       "up_to": up_to_seq}, mutate)
	except _NoAdvance:
		return {"seq": None, "kind": "mark_seen", "advanced": False,
		        "cursor": floor}
	result["advanced"] = True
	result["cursor"] = up_to_seq
	return result


def _discussion(store: Authority, discussion_id: str):
	row = store.conn.execute("SELECT * FROM discussions WHERE id=?",
	                         (discussion_id,)).fetchone()
	if row is None:
		raise WorkError(f"no discussion {discussion_id!r}")
	return row


class _NoAdvance(Exception):
	"""A losing or idempotent mark: NOT an audit act (R62)."""

	def __init__(self, cursor: int):
		self.cursor = cursor


def seen_discussion(store: Authority, discussion_id: str, *, team: str,
                    member: str, up_to_seq: int) -> dict:
	"""The canonical per-discussion cursor advance: monotonic,
	idempotent, bounded by the OBSERVED authority sequence (a future
	cursor would hide messages that do not exist yet), revalidated inside
	the committing transaction, and truthful — a losing lower mark
	returns the committed cursor with NO audit act (R62)."""
	_member(store, team, member)
	_discussion(store, discussion_id)
	if not isinstance(up_to_seq, int) or up_to_seq < 0:
		raise WorkError("seen takes a non-negative sequence number")
	if up_to_seq > store.last_seq():
		raise WorkError(
			f"cursor {up_to_seq} is beyond the observed authority "
			f"sequence ({store.last_seq()}); a mark names what was read, "
			f"never the future")

	def mutate(conn, seq):
		_member_active(conn, team, member)
		current = conn.execute(
			"SELECT seq FROM seen WHERE team=? AND member=? AND "
			"discussion=?", (team, member, discussion_id)).fetchone()
		if current is not None and current["seq"] >= up_to_seq:
			raise _NoAdvance(current["seq"])
		conn.execute(
			"INSERT INTO seen (team, member, discussion, seq) "
			"VALUES (?, ?, ?, ?) "
			"ON CONFLICT(team, member, discussion) DO UPDATE SET "
			"seq = excluded.seq",
			(team, member, discussion_id, up_to_seq))

	try:
		result = store._write("mark_seen", f"{team}.{member}",
		                      {"discussion": discussion_id,
		                       "up_to": up_to_seq}, mutate)
	except _NoAdvance as losing:
		return {"seq": None, "kind": "mark_seen", "advanced": False,
		        "cursor": losing.cursor}
	result["advanced"] = True
	result["cursor"] = up_to_seq
	return result


def _label_gate(store, work_row, actor_team: str, actor: str) -> None:
	"""WS-4 D1: a `#WORK` label is applied or removed by a configured
	member of the Work's OWNING team — context is cheap inside the team,
	and outsiders cannot inject noise into another team's New."""
	del store, actor
	if actor_team != work_row["team"]:
		raise WorkError(
			"#" + work_row["id"] + " may be labelled only by "
			f"{work_row['team']} members; a member cannot decorate "
			f"another team's work merely by knowing its id")


def create_discussion(store: Authority, *, actor_team: str, actor: str,
                      body: str, labels) -> dict:
	"""A discussion is born labelled and speaking: at least one authorized
	`#WORK` label (each to the actor's own team's Work, at least one of
	them OPEN — the live-context ruling) and its first message, in one
	transaction."""
	_member(store, actor_team, actor)
	if not isinstance(body, str) or not body:
		raise WorkError("a discussion is born with its first message")
	if isinstance(labels, str):
		labels = [labels]
	labels = list(labels or [])
	if not labels:
		raise WorkError("a discussion is born with at least one "
		                "authorized #WORK label (live-context ruling)")
	if len(set(labels)) != len(labels):
		raise WorkError("a label is applied once")
	rows = []
	for work_id in labels:
		row = _work(store, work_id)
		_label_gate(store, row, actor_team, actor)
		rows.append(row)
	if not any(row["status"] == OPEN for row in rows):
		raise WorkError(
			"a new message requires at least one labelled OPEN work; "
			"create or label open follow-up work first "
			"(live-context ruling)")

	prefix = store.meta()["authority_uuid"][:8]
	payload = {"labels": list(labels),
	           "body_bytes": len(body.encode("utf-8"))}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		discussion_id = f"{prefix}-D{seq}"
		live_open = False
		for work_id in labels:
			live = conn.execute(
				"SELECT status, team FROM work WHERE id=?",
				(work_id,)).fetchone()
			if live["team"] != actor_team:
				raise WorkError(
					"#" + work_id + " may be labelled only by "
					f"{live['team']} members")
			live_open = live_open or live["status"] == OPEN
		if not live_open:
			raise WorkError(
				"a new message requires at least one labelled OPEN "
				"work (live-context ruling)")
		conn.execute(
			"INSERT INTO discussions (id, created_seq, created_ts) "
			"VALUES (?, ?, ?)", (discussion_id, seq, store.clock()))
		for work_id in labels:
			conn.execute(
				"INSERT INTO discussion_labels (discussion, work, "
				"added_seq) VALUES (?, ?, ?)",
				(discussion_id, work_id, seq))
		_join_discussion(conn, discussion_id, actor_team, seq)
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, discussion_id, actor_team, actor, body))
		payload["discussion"] = discussion_id
		mutate.discussion_id = discussion_id

	result = store._write("create_discussion", f"{actor_team}.{actor}",
	                      payload, mutate)
	result["discussion"] = mutate.discussion_id
	return result


def label_discussion(store: Authority, discussion_id: str, work_id: str, *,
                     actor_team: str, actor: str) -> dict:
	"""Apply an INERT `#WORK` label: reusable context, never a gate. May
	name terminal Work. Authorized by the Work's owning team (D1)."""
	_member(store, actor_team, actor)
	_discussion(store, discussion_id)
	row = _work(store, work_id)
	_label_gate(store, row, actor_team, actor)
	if store.conn.execute(
			"SELECT 1 FROM discussion_labels WHERE discussion=? AND "
			"work=?", (discussion_id, work_id)).fetchone():
		raise WorkError(f"{discussion_id} already carries #" + work_id)

	payload = {"discussion": discussion_id, "work": work_id,
	           "work_team": row["team"]}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		if conn.execute(
				"SELECT 1 FROM discussion_labels WHERE discussion=? AND "
				"work=?", (discussion_id, work_id)).fetchone():
			raise WorkError(f"{discussion_id} already carries #" + work_id)
		live = conn.execute("SELECT team, status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if actor_team != live["team"]:
			raise WorkError(
				"#" + work_id + " may be labelled only by "
				f"{live['team']} members")
		# R65: the audit describes the COMMITTING state, not an
		# optimistic diagnostic.
		payload["work_status"] = live["status"]
		conn.execute(
			"INSERT INTO discussion_labels (discussion, work, added_seq) "
			"VALUES (?, ?, ?)", (discussion_id, work_id, seq))
		_join_discussion(conn, discussion_id, actor_team, seq)

	return store._write("label", f"{actor_team}.{actor}", payload, mutate)


def unlabel_discussion(store: Authority, discussion_id: str, work_id: str,
                       *, actor_team: str, actor: str) -> dict:
	"""Remove a label under the same D1 authority. Removing the FINAL
	label refuses — a discussion always keeps explicit Work scope (the
	live-context ruling). The audit act is the history; the row goes."""
	_member(store, actor_team, actor)
	_discussion(store, discussion_id)
	row = _work(store, work_id)
	_label_gate(store, row, actor_team, actor)
	if store.conn.execute(
			"SELECT 1 FROM discussion_labels WHERE discussion=? AND "
			"work=?", (discussion_id, work_id)).fetchone() is None:
		raise WorkError(f"{discussion_id} does not carry #" + work_id)

	payload = {"discussion": discussion_id, "work": work_id}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		if conn.execute(
				"SELECT 1 FROM discussion_labels WHERE discussion=? AND "
				"work=?", (discussion_id, work_id)).fetchone() is None:
			raise WorkError(f"{discussion_id} does not carry #" + work_id)
		remaining = conn.execute(
			"SELECT COUNT(*) AS n FROM discussion_labels WHERE "
			"discussion=?", (discussion_id,)).fetchone()["n"]
		if remaining <= 1:
			raise WorkError(
				"#" + work_id + f" is {discussion_id}'s final label; a "
				f"discussion always keeps explicit work scope "
				f"(live-context ruling)")
		conn.execute(
			"DELETE FROM discussion_labels WHERE discussion=? AND work=?",
			(discussion_id, work_id))

	return store._write("unlabel", f"{actor_team}.{actor}", payload, mutate)


def post_discussion(store: Authority, discussion_id: str, *,
                    author_team: str, author: str, body: str) -> dict:
	"""A plain message into a discussion — open to every configured
	member, requiring live context (at least one labelled OPEN Work,
	rechecked in-lock). The author's team joins the participation set
	monotonically. Carrying operators remain Slice B."""
	_member(store, author_team, author)
	_discussion(store, discussion_id)
	if not isinstance(body, str) or not body:
		raise WorkError("a message body must be non-empty")
	if not _live_context(store.conn, discussion_id):
		raise WorkError(
			f"{discussion_id} has no labelled open work; closed context "
			f"is readable history — create or label open follow-up work "
			f"to continue (live-context ruling)")

	payload = {"discussion": discussion_id,
	           "body_bytes": len(body.encode("utf-8"))}

	def mutate(conn, seq):
		_member_active(conn, author_team, author)
		if not _live_context(conn, discussion_id):
			raise WorkError(
				f"{discussion_id} has no labelled open work; closed "
				f"context is readable history (live-context ruling)")
		conn.execute(
			"INSERT INTO messages (seq, discussion, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, discussion_id, author_team, author, body))
		_join_discussion(conn, discussion_id, author_team, seq)

	return store._write("post_message", f"{author_team}.{author}",
	                    payload, mutate)
