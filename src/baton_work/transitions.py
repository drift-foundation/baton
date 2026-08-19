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

import hashlib as _op_hashlib
import json as _op_json

from baton_work.authority import (Authority, WorkError,
                                  clock_ms_now, validate_op_id)

# The confirmed intake example's vocabulary. Additive growth is expected;
# renames are not.
ORIGINS = ("external-report", "self-initiated", "decomposition")
# WS-1 ruling: classification is NEVER null — `unknown` is the canonical
# default, a value like any other, and clients must not read meaning into
# absence.
# finding-active-work-claim: role handles that NAME a work stage derive a
# pass's destination phase; anything else needs the phase stated in the
# pass itself. Closed map — derivation never guesses.
# W73: the ONE stage-role vocabulary a route transfer derives its
# destination phase from. A handoff never produces `queued` — the baton
# arriving IS the work starting at the destination's stage — and an
# unmapped role refuses rather than guessing, because a wrong phase is
# a false operational view that survives in the projection.
CLASSIFICATIONS = ("unknown", "suspected-defect", "confirmed-defect",
                   "limitation", "duplicate", "design-choice", "rejection")
# W38 (finding-phase-is-scheduler-state): Phase is a closed SCHEDULER
# axis and nothing else. It answers "can this run, and is it running" —
# never what KIND of work it is, which is the Route's role, and never who
# is doing it, which is the Handler.
#
# The authority previously mapped a destination role onto a phase, so an
# implementation handoff read `active` before anybody picked it up and a
# review handoff read `review`. Three Works sitting in `active` with one
# real claimant between them is what exposed it: the word active meant
# "routed to implementers", not "somebody is working on this".
#
#   queued   open, runnable, unclaimed
#   active   open and CLAIMED — active iff Handler is non-null
#   block    open, unclaimed, held by ONE displayed unsatisfied gate
#   parked   open, unclaimed, deliberately deferred with no wake condition
#   (terminal work has no phase at all: null in JSON, `-` in the TUI)
#
# W78 (finding-unclaimed-work-cue) renamed `waiting` to `block` and gave
# it a typed, timed cause. One phase covers every unsatisfied gate
# whether the gate is another Work or a directed Message obligation;
# splitting them into two phases would have hidden that both are the
# same scheduler condition — this Work cannot advance — while the
# interesting difference (what would unblock it) belongs in the gate,
# not the phase. The gate is displayed beside the row and its episode
# start is what the Held timer measures, so every advancing clock is
# explainable from the row it sits on.
#
# Compact TUI renderings are PRESENTATION and are never accepted as
# mutation values.
PHASES = ("queued", "active", "block", "parked")
# W38: a creation is open, unclaimed and ungated, so `queued` is the only
# state it can honestly land in. `active` would need a claimant, `block`
# a live gate, and `parked` a reason — none of which a creation
# has. The operand is therefore gone from `create` rather than accepting
# exactly one value.
CREATION_PHASES = ("queued",)
# WS-2 ruling: every terminal close records exactly one of these.
OUTCOMES = ("satisfying", "non-satisfying", "rejected", "cancelled")
# W3 (ruled): exactly three team-local priority tiers — deliberately no
# urgent, numeric, or finer grading; extra levels destroy the signal.
PRIORITIES = ("high", "normal", "low")
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


# W4 (ruled): the two accepted Work spellings — the canonical qualified
# id and the exact authority-local `W<positive-sequence>` selector. Like
# a short Git object name, the selector is a CONVENIENCE over canonical
# identity, never a second identity: generated from the permanent Work
# sequence, unique and never reused within an authority.
import re as _sel_re
_LOCAL_SELECTOR = _sel_re.compile(r"^W[1-9][0-9]*$")
_CANONICAL_WORK = _sel_re.compile(r"^[0-9a-f]{8}-W[1-9][0-9]*$")


def resolve_work_selector(store: Authority, value) -> str:
	"""THE one strict Work-selector resolver, scoped to the ONE
	authority this client explicitly opened. `W<seq>` qualifies against
	that authority; a canonical id must already belong to it (a foreign
	id refuses by name). Anything else — malformed, empty, partial —
	refuses without guessing: never from title, cursor position,
	creation order, or a match that could name more than one object.
	The resolver fixes IDENTITY only; existence is judged by the
	lookup that follows, so a well-formed absent selector still gets
	the honest `no work` refusal."""
	prefix = store.meta()["authority_uuid"][:8]
	if isinstance(value, str) and _LOCAL_SELECTOR.match(value):
		return f"{prefix}-{value}"
	if isinstance(value, str) and _CANONICAL_WORK.match(value):
		if not value.startswith(prefix + "-"):
			raise WorkError(
				f"{value!r} names a different authority; this client "
				f"is bound to {prefix} and never resolves across "
				f"instances")
		return value
	raise WorkError(
		f"{value!r} is not a Work selector; use the authority-local "
		f"W<sequence> (for example W11) or the canonical "
		f"<authority>-W<sequence> id")


# W7 (finding-local-thread-selectors): the SAME two-spelling contract
# for Threads. The TUI presents Threads with the local `T<sequence>`
# label; a stable identifier presented as the way to name a Thread is
# accepted wherever a command asks for one.
_LOCAL_THREAD = _sel_re.compile(r"^T[1-9][0-9]*$")
_CANONICAL_THREAD = _sel_re.compile(r"^[0-9a-f]{8}-T[1-9][0-9]*$")


def resolve_thread_selector(store: Authority, value) -> str:
	"""THE one strict Thread-selector resolver — the exact discipline of
	`resolve_work_selector`, scoped to the ONE authority this client
	explicitly opened. `T<seq>` qualifies against that authority; a
	canonical id must already belong to it (a foreign id refuses by
	name). Anything else refuses without guessing — never from subject,
	cursor position, or creation order. The resolver fixes IDENTITY
	only; a well-formed absent selector still gets the honest
	`no thread` refusal from the lookup that follows."""
	prefix = store.meta()["authority_uuid"][:8]
	if isinstance(value, str) and _LOCAL_THREAD.match(value):
		return f"{prefix}-{value}"
	if isinstance(value, str) and _CANONICAL_THREAD.match(value):
		if not value.startswith(prefix + "-"):
			raise WorkError(
				f"{value!r} names a different authority; this client "
				f"is bound to {prefix} and never resolves across "
				f"instances")
		return value
	raise WorkError(
		f"{value!r} is not a Thread selector; use the authority-local "
		f"T<sequence> (for example T2) or the canonical "
		f"<authority>-T<sequence> id")


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


def selectable_routes(conn, team: str, kind: str) -> list:
	"""W230: every route this endpoint may be sent to — the default
	first, then its configured alternates in handle order.

	The default leads deliberately: it is not one candidate among
	equals. An omitted selection resolves to it, and nothing ever picks
	an alternate on the operator's behalf."""
	row = conn.execute(
		"SELECT route FROM kinds WHERE team=? AND handle=?",
		(team, kind)).fetchone()
	if row is None or row["route"] is None:
		return []
	alternates = [entry["route"] for entry in conn.execute(
		"SELECT route FROM kind_alternates WHERE team=? AND kind=? "
		"ORDER BY route", (team, kind))]
	return [row["route"]] + [route for route in alternates
	                         if route != row["route"]]


def resolve_endpoint(conn, team: str, kind: str, what: str,
                     selected: str | None = None) -> dict:
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
	# W230: an explicitly selected route replaces the default for THIS
	# Work, and only if the accepted configuration offers it. An
	# unconfigured or since-removed selection refuses rather than
	# silently falling back — a quiet fallback would send Work to a
	# different agent than the operator chose, which is the one thing
	# an explicit selection exists to prevent.
	route = row["route"]
	if selected is not None and selected != route:
		offered = selectable_routes(conn, team, kind)
		if selected not in offered:
			raise WorkError(
				f"{what}: {team}.{kind} does not offer route "
				f"{selected!r}; the accepted configuration offers "
				f"{offered}")
		route = selected
	route_row = conn.execute(
		"SELECT role FROM routes WHERE team=? AND handle=? AND removed=0",
		(team, route)).fetchone()
	if route_row is None:
		raise WorkError(f"{what}: {team}.{kind} routes through "
		                f"{route!r}, which is not live")
	handlers = [entry["member"] for entry in conn.execute(
		"SELECT member FROM route_handlers WHERE team=? AND route=? "
		"ORDER BY member", (team, route))]
	generation = conn.execute(
		"SELECT value FROM meta WHERE key='accepted_generation'").fetchone()
	return {"endpoint": f"{team}.{kind}", "route": route,
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


def _displayed_gate(conn, work_id: str, current) -> tuple | None:
	"""W78: WHICH single gate is holding this Work, or None if none is.

	Returns `(kind, work, obligation)` — exactly one of the last two is
	set — and returns `current` UNCHANGED whenever the gate it names is
	still the one holding the Work. That is what makes the episode
	stable: the answer only differs when the displayed gate genuinely
	differs.

	A blocking directed obligation outranks Work gates while it is
	pending, because the Work was suspended BY that request and
	answering it is the act that moves the Work. It is identified by the
	STORED gate rather than rediscovered, because a Work may carry
	pending obligations that never blocked it — `request wait=false`
	creates exactly that — and those must not capture the cue.

	The Work gate is the oldest open gate by permanent creation order.
	Two kinds count, because both are what `_open_gates` counts: an open
	required CHILD and an open explicit BLOCKER. The pinned selection
	rule names the oldest open blocker, which is the case it was written
	for; extending the same order over children is the only way a
	child-gated Work can name what holds it. The alternative — a `block`
	row with an empty Wait cell and a running clock — is precisely the
	unexplained timer this Work exists to remove, so leaving children
	out would have reintroduced the defect in a new place."""
	if current is not None and current[0] == "message" \
			and current[2] is not None:
		live = conn.execute(
			"SELECT status FROM obligations WHERE seq=?",
			(current[2],)).fetchone()
		if live is not None and live["status"] == "pending":
			return current
	gate = conn.execute(
		"SELECT id, created_seq FROM work WHERE parent=? AND status=? "
		"UNION "
		"SELECT work.id, work.created_seq FROM edges JOIN work "
		"ON work.id=edges.blocker WHERE edges.work=? AND work.status=? "
		"ORDER BY created_seq LIMIT 1",
		(work_id, OPEN, work_id, OPEN)).fetchone()
	if gate is not None:
		return ("work", gate["id"], None)
	return None


def _gate_now(payload, work_id: str, gate) -> None:
	"""W78: record a displayed-gate EPISODE boundary on this event.

	Mirrors `_phase_now` and is deliberately SEPARATE from it, because a
	gate change inside `block` is a new gate episode and not a phase
	transition: recording it as one would fabricate a phase change that
	never happened, and the Events playback would show the Work leaving
	and re-entering a phase it never left.

	A LIST whose entries name their Work, for the same reason
	`phase_now` is one: a single event can retarget more than one."""
	if payload is not None:
		payload.setdefault("gate_now", []).append(
			{"work": work_id,
			 "kind": None if gate is None else gate[0],
			 "gate_work": None if gate is None else gate[1],
			 "obligation": None if gate is None else gate[2]})


def _write_gate(conn, work_id: str, payload, gate) -> None:
	"""Commit one displayed-gate episode, stamping its start."""
	if gate is None:
		conn.execute(
			"UPDATE work SET gate_kind=NULL, gate_work=NULL, "
			"gate_obligation=NULL, gate_started_at=NULL, gate_seq=NULL "
			"WHERE id=?", (work_id,))
	else:
		seq = conn.execute(
			"SELECT value FROM sequence WHERE id=1").fetchone()["value"]
		conn.execute(
			"UPDATE work SET gate_kind=?, gate_work=?, gate_obligation=?, "
			"gate_started_at=?, gate_seq=? WHERE id=?",
			(*gate, clock_ms_now(), seq, work_id))
	# A new gate episode IS a visible row change, so it stamps the row's
	# change identity like every other one.
	_touch_work(conn, work_id)
	_gate_now(payload, work_id, gate)


def _retarget_gate(conn, work_id: str, payload) -> None:
	"""W78: keep the stored gate episode equal to the displayed gate.

	Called by every transaction that can change what holds a Work —
	adding or removing a dependency, closing a blocker or a child,
	creating a child, answering or disposing an obligation, and every
	readiness recomputation.

	The episode start moves ONLY when the displayed gate actually
	changes. That is the whole point: adding a second blocker behind the
	displayed one, a heartbeat, a priority edit or a refresh leave the
	clock alone, and a client never has to guess a start instant the
	authority did not commit."""
	row = conn.execute(
		"SELECT phase, gate_kind, gate_work, gate_obligation "
		"FROM work WHERE id=?", (work_id,)).fetchone()
	if row is None:
		return
	current = (row["gate_kind"], row["gate_work"], row["gate_obligation"])
	if row["gate_kind"] is None:
		current = None
	if row["phase"] != "block":
		gate = None
	else:
		gate = _displayed_gate(conn, work_id, current)
		if gate is None:
			# Still `block`, nothing left holding it: this Work is about
			# to be woken by the sweep at the end of this very
			# transaction. Leave the episode alone so the wake can name
			# the gate that CLEARED and end the episode itself. Clearing
			# it here would erase that evidence one statement before it
			# is needed, and would also, for an instant, describe a
			# blocked Work as blocked by nothing.
			return
	if gate == current:
		return
	_write_gate(conn, work_id, payload, gate)


def _enter_message_gate(conn, work_id: str, payload, obligation: int) -> None:
	"""W78: a blocking directed request establishes its own gate.

	The obligation that suspends the Work is known only here, so this is
	the one gate the authority sets explicitly rather than deriving."""
	_write_gate(conn, work_id, payload, ("message", None, obligation))


def _phase_now(payload, work_id: str, phase: str | None) -> None:
	"""W47: record the scheduler phase the Work is in AFTER this event.

	One key on every phase-changing event, so the ledger states the
	transition rather than leaving a reader to infer it from five
	differently-named payload fields (`to`, `destination_phase`,
	`phase`, `from_phase`, and the wake's own pair). The projection
	replays these to build phase intervals; nothing recomputes the
	authority's decision.

	A LIST, and each entry names its Work, because one event can move
	more than one: creating a child gates its parent, so the child's
	`create_work` event is where the PARENT enters `block`. A bare
	phase string would attribute that to the wrong Work.

	`None` means the Work has no phase at all, which is true of exactly
	one transition: terminal close."""
	if payload is not None:
		payload.setdefault("phase_now", []).append(
			{"work": work_id, "phase": phase})


def _unclaimed_state(conn, work_id: str) -> str:
	"""W38: the scheduler phase of OPEN, UNCLAIMED Work — `block` when a
	gate is unsatisfied, `queued` when it can run.

	Every claimant-releasing transition derives its state here rather
	than carrying one in, so `pass`, `release`, recovery and readiness
	changes cannot disagree about the same committed gate state.

	W78: this used to return a `wait_type` beside the phase, because
	`waiting` without a recorded condition is unwakeable. The condition
	now lives in the displayed-gate episode, which every caller commits
	through `_retarget_gate` in the same transaction — so the phase and
	the thing holding it can no longer be written apart."""
	return "block" if _open_gates(conn, work_id) else "queued"


def _sweep_wakes(conn, actor: str, payload=None) -> None:
	"""Level-triggered wake: every OPEN blocked Work whose displayed gate
	is now satisfied atomically becomes `queued`, with one `wake` event in
	the SAME transaction that satisfied it. Runs at the end of every
	transaction that can close a gate or complete an obligation (close,
	respond, dispose). A racing retry finds the phase already `queued`
	and wakes nothing twice."""
	for row in conn.execute(
			"SELECT id, gate_kind, gate_work, gate_obligation FROM work "
			"WHERE status=? AND phase='block'", (OPEN,)).fetchall():
		current = (row["gate_kind"], row["gate_work"],
		           row["gate_obligation"])
		if row["gate_kind"] is None:
			current = None
		if row["gate_kind"] == "message":
			pending = conn.execute(
				"SELECT status FROM obligations WHERE seq=?",
				(row["gate_obligation"],)).fetchone()
			satisfied = pending is not None and \
				pending["status"] != "pending"
		else:
			# A Work gate is satisfied only when the AGGREGATE is: the
			# displayed blocker closing does not release Work that other
			# gates still hold.
			satisfied = _open_gates(conn, row["id"]) == 0
		if satisfied and _open_gates(conn, row["id"]):
			# W38 R3: the recorded condition is satisfied, but the
			# SCHEDULER condition is not. Work can wait on a directed
			# obligation and independently acquire a dependency;
			# answering the obligation does not make it runnable.
			# Retarget to whatever is still holding it, stay blocked,
			# and mint NOTHING — nothing became actionable, so waking a
			# handler here would be a false alarm.
			#
			# W78: the retarget is a real, timed episode. Deliberately
			# no `wake` EVENT: one whose from and to are both `block`
			# would put a false actionability signal in the journal,
			# since nothing became actionable.
			#
			# But the episode boundary itself IS recorded, on the event
			# that caused it — the response, disposal or close being
			# committed right now. The row alone describes only the
			# LATEST episode, so without this the boundary would vanish
			# the moment the gate changed again; and the replay
			# reconstructs nothing, so an unrecorded boundary is absent
			# forever rather than derivable later. `_gate_now` is
			# separate from `_phase_now` precisely so this can be said
			# without fabricating a phase transition that never
			# happened.
			_retarget_gate(conn, row["id"], payload)
			_touch_work(conn, row["id"])
			continue
		if satisfied:
			conn.execute(
				"UPDATE work SET phase='queued' WHERE id=?", (row["id"],))
			_write_gate(conn, row["id"], None, None)
			_touch_work(conn, row["id"])
			# W49: the condition wake returns the Work to its Route
			# endpoint's queue — newly actionable, so a new episode.
			_mint_episode(conn, row["id"])
			_emit(conn, "wake", actor,
			      {"work": row["id"], "from": "block", "to": "queued",
			       "phase_now": [{"work": row["id"],
			                      "phase": "queued"}],
			       "gate_now": [{"work": row["id"], "kind": None,
			                     "gate_work": None, "obligation": None}],
			       # W78: the gate that CLEARED, named for what it is.
			       # `gate_now` beside it is the episode boundary (the
			       # Work now has no gate at all); calling this one
			       # `gate` would have read as the current one.
			       "cleared_gate": {
				       "kind": current[0] if current else None,
				       "work": current[1] if current else None,
				       "obligation": current[2] if current else None}})


def _touch_work(conn, work_id: str) -> None:
	"""Schema 15 (W84 groundwork): every direct Work-row mutation stamps
	the row's stable change identity — the committing event's sequence and
	one millisecond-precision instant. Clients derive age from these
	canonical values; they never reconstruct recency from the event ledger.
	The set of INDIRECT acts that count as Work recency is W84's own ruling
	and is deliberately not guessed here."""
	seq = conn.execute(
		"SELECT value FROM sequence WHERE id=1").fetchone()["value"]
	conn.execute(
		"UPDATE work SET last_change_seq=?, last_changed_at=? WHERE id=?",
		(seq, clock_ms_now(), work_id))


def _mint_episode(conn, work_id: str) -> None:
	"""W49: start a NEW assignment episode for this Work.

	The neighbouring `_touch_work` stamps every visible edit; this stamps
	only the ones that make the Work newly actionable for whoever its
	Route resolves — creation, pass/return, explicit claim release, a
	false-to-true readiness flip, a condition wake, and a parked-to-queued
	resume. Claim, heartbeat, ordinary phase moves, priority,
	classification and descriptive edits deliberately do NOT mint: an
	episode is "you have been handed this", not "something about this
	changed".

	The value is the committing event's sequence, so it is authority-
	derived and every independent client agrees on it across restarts —
	never a local poll counter, which two consumers could not reconcile."""
	seq = conn.execute(
		"SELECT value FROM sequence WHERE id=1").fetchone()["value"]
	conn.execute("UPDATE work SET episode_seq=? WHERE id=?", (seq, work_id))


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
	must be a currently resolved handler of the Work's Route under
	the accepted generation at commit. Returns the resolution snapshot for
	the audit payload. `@` respondents and other teams get an explicit
	refusal — input never grants mutation authority."""
	row = conn.execute(
		"SELECT route_team, route_kind, route_selected FROM work "
		"WHERE id=?", (work_id,)).fetchone()
	if row["route_team"] is None or row["route_kind"] is None:
		raise WorkError(f"{what}: {work_id} has no Route endpoint")
	# W230: through the Work's OWN route, which is its explicit
	# selection when it has one. Resolving the endpoint's default here
	# would authorize the default's handlers and refuse the agent
	# actually holding the Work — a Work sent to an alternate could
	# never be passed back, and the selection would strand it.
	resolution = resolve_endpoint(conn, row["route_team"],
	                              row["route_kind"], what,
	                              selected=row["route_selected"])
	if actor_team != row["route_team"] or \
			actor not in resolution["handlers"]:
		raise WorkError(
			f"{what}: {actor_team}.{actor} is not a resolved handler of "
			f"{resolution['endpoint']} (route {resolution['route']!r}, "
			f"handlers {resolution['handlers']}); contribution and @ input "
			f"never grant workflow mutation authority")
	return resolution


def _live_context(conn, thread_id: str) -> bool:
	"""The pinned live-context boundary: at least one currently labelled
	OPEN Work."""
	return conn.execute(
		"SELECT 1 FROM thread_labels JOIN work "
		"ON work.id = thread_labels.work "
		"WHERE thread_labels.thread=? AND work.status='open'",
		(thread_id,)).fetchone() is not None


def _join_thread(conn, thread_id: str, team: str, seq: int) -> None:
	"""Monotonic thread-team participation (WS-4 R56): once added, a
	team stays; nothing in this slice removes it."""
	conn.execute(
		"INSERT OR IGNORE INTO thread_participants "
		"(thread, team, added_seq) VALUES (?, ?, ?)",
		(thread_id, team, seq))


def _recompute_ready(conn, work_id: str, payload=None) -> None:
	"""Readiness from CURRENT state: open, and no open children.

	(A3 adds open blockers to the conjunction.) This is the single place
	readiness is computed, called by whichever transition changed an input —
	never by a reader, because reads are pure."""
	row = conn.execute("SELECT status, ready FROM work WHERE id=?",
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
	if ready != row["ready"]:
		# A readiness flip is a visible row change; a same-value recompute
		# is not and must not disturb the change identity (schema 15).
		conn.execute("UPDATE work SET ready=? WHERE id=?", (ready, work_id))
		if ready == 1:
			# W49: false-to-true readiness is the unblock wake — the last
			# child closed, or the last blocker did. Nobody passed this
			# Work, but it just became actionable for its Route, which
			# is exactly what an episode names. The reverse flip is not
			# an episode: it REMOVES actionability.
			_mint_episode(conn, work_id)
		if ready == 0:
			# finding-active-work-claim R3: a late-arriving gate
			# INVALIDATES execution — the claimant is released
			# atomically, and the causing event's payload keeps the
			# released claimant as recoverable evidence.
			#
			# W38 R1: the scheduler state moves whenever READINESS
			# changes, not only when a claimant happens to be released.
			# `queued` means RUNNABLE, so a gate arriving on unclaimed
			# queued Work has to move it too — otherwise the row sits
			# queued with ready=false and no recorded condition, which
			# contradicts the definition and cannot wake.
			#
			# `parked` is deliberately excluded: it is an explicit
			# deferral, and a gate appearing underneath it does not
			# revoke that decision. Leaving the park reveals whatever
			# the gates then say (R2).
			live = conn.execute(
				"SELECT phase, handler_team, handler_member "
				"FROM work WHERE id=?", (work_id,)).fetchone()
			if live["handler_team"] is not None:
				if payload is not None:
					payload.setdefault("released_claims", []).append(
						{"work": work_id,
						 "claimant": f"{live['handler_team']}."
						             f"{live['handler_member']}",
						 "from_phase": live["phase"]})
					_phase_now(payload, work_id, "block")
				conn.execute(
					"UPDATE work SET handler_team=NULL, "
					"handler_member=NULL, phase='block' WHERE id=?",
					(work_id,))
			elif live["phase"] == "queued":
				if payload is not None:
					_phase_now(payload, work_id, "block")
				conn.execute(
					"UPDATE work SET phase='block' WHERE id=?",
					(work_id,))
		_touch_work(conn, work_id)
	# W78: OUTSIDE the readiness flip, deliberately. The case the ruling
	# names — the displayed blocker closes while another gate remains —
	# does not flip readiness at all: the Work was blocked before and is
	# blocked after. Retargeting only on a flip would leave that row
	# showing a closed gate and a clock measuring an episode that ended,
	# which is the same unexplained timer in a new place. A recompute
	# that changes nothing writes nothing, so this is free.
	_retarget_gate(conn, work_id, payload)





def _validate_ref_path(path: str, what: str) -> str:
	"""WS-6 containment SYNTAX only (never a stat): a normalized
	relative POSIX path — no absolute, backslash, empty/dot/dotdot
	component, control character, or edge whitespace."""
	if not isinstance(path, str) or not path:
		raise WorkError(f"{what}: a reference path is a non-empty "
		                f"relative POSIX path")
	if path != path.strip():
		raise WorkError(f"{what}: a reference path carries no edge "
		                f"whitespace")
	if path.startswith("/") or "\\" in path or \
			any(ord(ch) < 32 or ord(ch) == 127 for ch in path):
		raise WorkError(f"{what}: {path!r} is not a contained relative "
		                f"POSIX path")
	for component in path.split("/"):
		if component in ("", ".", ".."):
			raise WorkError(
				f"{what}: {path!r} contains an empty, '.', or '..' "
				f"component; escapes are refused at the syntax boundary")
	return path


import re as _ws6_re

# W309: the canonical permanent-record shapes — a top-level record OR
# a causally tied child under the repository's ruled layout
# `<record>/findings/<child>`, at most TWO child levels deep
# (AGENTS.md: deeper children are promoted to top level, never bound).
_BINDING_COMPONENT = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_BINDING_PATH = _ws6_re.compile(
	r"^work/records/[0-9]{4}/(0[1-9]|1[0-2])/"
	+ _BINDING_COMPONENT
	+ r"(?:/findings/" + _BINDING_COMPONENT + r"){0,2}$")
_WORK_ID = _ws6_re.compile(r"^[0-9a-f]{8}-W[0-9]+$")


def _validate_binding_path(path: str) -> str:
	"""M4 + W309: the canonical permanent-record locator — literal
	prefix, four-digit year, month 01-12, then a safe record component
	optionally followed by the repository's ruled child layout: up to
	TWO `/findings/<child>` levels. Absolute paths, traversal, empty
	or edge components, other separators, and deeper nesting refuse.
	Validation is pure syntax; nothing is probed."""
	_validate_ref_path(path, "binding")
	if not _BINDING_PATH.match(path):
		raise WorkError(
			f"binding path {path!r} is not a canonical permanent "
			f"record shape: work/records/YYYY/MM/<stable-record>"
			f"[/findings/<child>[/findings/<grandchild>]]")
	return path


def _parse_ref_tokens(refs, what: str = "reference"):
	"""The ONE typed-reference grammar (R89): pure token parsing and
	containment syntax shared by every mutation family, the
	configuration family included — no store access, no disclosure.
	Each token is either `ROOT_ID:relative/path` (independent; v10 root
	grammar) or `WORK-ID:relative/path` (dossier-relative; the two
	grammars cannot collide)."""
	from baton_work.config import validate_root_id
	parsed = []
	for token in refs or ():
		if not isinstance(token, str) or ":" not in token:
			raise WorkError(
				f"{what} {token!r} is not LEFT:relative/path shaped")
		left, _colon, path = token.partition(":")
		_validate_ref_path(path, what)
		if _WORK_ID.match(left):
			parsed.append({"kind": "dossier", "work": left,
			               "path": path})
		else:
			validate_root_id(left, what)
			parsed.append({"kind": "independent", "root": left,
			               "path": path})
	return parsed


def _peek_refs(store, parsed, what: str = "reference"):
	"""The optimistic semantic peek — early legible refusals; the
	committing transaction revalidates everything. Callers that must
	respect the identity information boundary run this only AFTER their
	identity gate."""
	for ref in parsed:
		if ref["kind"] == "independent":
			row = store.conn.execute(
				"SELECT removed FROM roots WHERE root=?",
				(ref["root"],)).fetchone()
			if row is None or row["removed"]:
				raise WorkError(
					f"root {ref['root']!r} is not a live configured "
					f"root; an independent reference lands on the "
					f"accepted catalog")
		else:
			_work(store, ref["work"])
			if store.conn.execute(
					"SELECT 1 FROM bindings WHERE work=?",
					(ref["work"],)).fetchone() is None:
				raise WorkError(
					f"{ref['work']} has no dossier binding to anchor; "
					f"bind it first or use an independent ROOT:PATH "
					f"reference")
	return parsed


def _parse_refs(store, refs, what: str = "reference"):
	"""Grammar plus optimistic peek — the ordinary-mutation entry."""
	return _peek_refs(store, _parse_ref_tokens(refs, what), what)


def _operation(store, actor_team, actor, name, op_id, typed_input):
	"""WS-5 entry: the identity gate, the id grammar, the canonical
	semantic fingerprint over the TYPED input (never shell spelling or
	dynamic resolution output), and the optimistic peek for a committed
	exact retry. Returns None (unprotected call), a REPLAY result dict
	(exact retry — return it verbatim), or the (participant, op_id,
	fingerprint) tuple carried into the committing transaction."""
	if op_id is None:
		return None
	validate_op_id(op_id)
	participant = f"{actor_team}.{actor}"
	fingerprint = _op_hashlib.sha256(_op_json.dumps(
		{"operation": name, "actor": participant, "input": typed_input},
		sort_keys=True, separators=(",", ":"),
		default=list).encode("utf-8")).hexdigest()
	# R84: lookup and identity gate are ONE observation — a single read
	# transaction whose snapshot starts at the lookup, with the gate
	# read against that same state. An accepted removal committing
	# before the lookup refuses; one committing after leaves a replay
	# that was valid when observed.
	store.conn.execute("BEGIN")
	try:
		# R84/R85: gate and lookup are ONE observation, and the identity
		# gate is also the INFORMATION boundary — whatever the lookup
		# concludes (replay or conflict), the current-identity check
		# against the same transaction state speaks first, so a removed
		# participant learns nothing about its old id.
		try:
			replay = store._op_replay(store.conn, participant, op_id,
			                          fingerprint)
		except WorkError:
			store._op_identity(store.conn, participant)
			raise
		store._op_identity(store.conn, participant)
	finally:
		store.conn.execute("ROLLBACK")
	if replay is not None:
		return replay
	return (participant, op_id, fingerprint)


def create_work(store: Authority, *, team: str, kind: str, title: str,
                origin: str, author: str, body: str,
                parent: str | None = None,
                classification: str | None = None,
                phase: str | None = None,
                follow_up_of: str | None = None,
                binding: str | None = None,
                op_id: str | None = None, refs=(), priority: str | None = None) -> dict:
	"""A Work and its first message, atomically — creation must be cheap or
	mandatory Work scope becomes authoring ceremony (confirmed behavior).

	`author` is `member` within `team`. The new Work's `route` is
	`team.kind`, resolved and validated now, at creation."""
	if not isinstance(title, str) or not title.strip():
		raise WorkError("a work title must be non-empty")
	# W31 rev3 (R2, approved): Work titles and Thread subjects share
	# ONE normalized contract — non-empty, single line, at most 80
	# UTF-8 bytes. The normalized title is stored as BOTH the Work
	# title and the born Thread subject, and participates in the
	# effectively-once lookup below. No silent truncation.
	title = validate_subject(title, "work title")
	if origin not in ORIGINS:
		raise WorkError(f"origin {origin!r} is not one of {ORIGINS}; origin "
		                f"is immutable history and is not free text")
	# finding-active-work-claim clarification (fresh schema, 2026-08-16;
	# reviewed under review-2026-08-16T09-27-05Z): the SUBMITTER chooses
	# a concrete classification — omission and 'unknown' refuse at
	# creation. The Route handler may reclassify later; activation
	# never requires a redundant classify step.
	if classification is None or classification == "unknown":
		raise WorkError(
			"work creation requires a concrete classification; "
			"'unknown' (or omitting it) refuses — choose one of "
			f"{tuple(c for c in CLASSIFICATIONS if c != 'unknown')}; "
			"the Route handler may reclassify later")
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
			f"a work is not created {phase!r}: active needs a claimant, "
			f"block needs a live gate, and parking needs "
			f"a reason — a creation has none of those, so it lands queued "
			f"and moves on its own transitions")
	if not isinstance(body, str) or not body:
		raise WorkError("the first message body must be non-empty")
	store._team(team)
	_endpoint(store, team, kind, "create")
	_member(store, team, author)
	binding_root = binding_path = None
	if binding is not None:
		if not isinstance(binding, str) or ":" not in binding:
			raise WorkError("a creation binding is ROOT_ID:work/records/"
			                "YYYY/MM/<stable-record>")
		binding_root, _colon, binding_path = binding.partition(":")
		from baton_work.config import validate_root_id
		validate_root_id(binding_root, "binding root")
		_validate_binding_path(binding_path)
		live = store.conn.execute(
			"SELECT removed FROM roots WHERE root=?",
			(binding_root,)).fetchone()
		if live is None or live["removed"]:
			raise WorkError(f"root {binding_root!r} is not a live "
			                f"configured root; a new binding lands on "
			                f"the accepted catalog")
	refs = _parse_refs(store, refs)
	operation = _operation(store, team, author, "create_work", op_id,
	                       {"team": team, "kind": kind, "title": title,
	                        "origin": origin, "body": body,
	                        "parent": parent,
	                        "classification": classification,
	                        "phase": phase,
	                        "follow_up_of": follow_up_of,
	                        "binding": binding, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
	# W3: priority may be recorded atomically at birth; omission is the
	# natural normal default, never a distinct state.
	if priority is None:
		priority = "normal"
	if priority not in PRIORITIES:
		raise WorkError(f"priority {priority!r} is not one of "
		                f"{PRIORITIES}")
	payload = {"team": team, "kind": kind, "title": title,
	           "origin": origin, "parent": parent,
	           "classification": classification, "phase": phase,
	           "priority": priority,
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
			# PARENT's Route handler; root creation stays with the team.
			payload["authorization"] = _handler_gate(
				conn, parent, team, author, "attach child")
		payload["resolution"] = resolve_endpoint(conn, team, kind, "create")
		# W47: creation opens the Work's first scheduler episode.
		_phase_now(payload, work_id, phase)
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
			"phase, status, parent, route_team, route_kind, ready, "
			"priority, "
			"follow_up_of, created_seq, last_change_seq, last_changed_at) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)",
			(work_id, team, title, origin, classification, phase, OPEN,
			 parent, team, kind, priority, follow_up_of, seq, seq,
			 clock_ms_now()))
		# W49: creation is the first assignment episode.
		_mint_episode(conn, work_id)
		thread_id = f"{prefix}-T{seq}"
		# The born Thread's subject is the Work's title — the one
		# conversation a creation opens is ABOUT that Work.
		conn.execute(
			"INSERT INTO threads (id, subject, created_seq, created_ts) "
			"VALUES (?, ?, ?, ?)", (thread_id, title, seq,
			                        store.clock()))
		conn.execute(
			"INSERT INTO thread_labels (thread, work, added_seq) "
			"VALUES (?, ?, ?)", (thread_id, work_id, seq))
		_join_thread(conn, thread_id, team, seq)
		conn.execute(
			"INSERT INTO messages (seq, thread, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, thread_id, team, author, body))
		if binding_root is not None:
			live_root = conn.execute(
				"SELECT removed FROM roots WHERE root=?",
				(binding_root,)).fetchone()
			if live_root is None or live_root["removed"]:
				raise WorkError(
					f"root {binding_root!r} is not a live configured "
					f"root; a new binding lands on the accepted catalog")
			conn.execute(
				"INSERT INTO bindings (work, revision, prior, root, "
				"path, git_provenance, actor, rationale, seq, "
				"created_ts) VALUES (?, 1, 0, ?, ?, NULL, ?, NULL, ?, "
				"?)",
				(work_id, binding_root, binding_path,
				 f"{team}.{author}", seq, store.clock()))
			payload["binding"] = {"root": binding_root,
			                      "path": binding_path, "revision": 1}
		_recompute_ready(conn, work_id, payload)
		if parent is not None:
			_recompute_ready(conn, parent, payload)
		mutate.work_id = work_id
		mutate.thread_id = thread_id

	def finish(result):
		result["thread"] = mutate.thread_id
		result["work_id"] = mutate.work_id

	return store._write("create_work", f"{team}.{author}",
	                    payload, mutate, operation=operation,
	                    finish=finish, references=refs)


def close_work(store: Authority, work_id: str, *, actor_team: str,
               actor: str, rationale: str | None = None,
               outcome: str | None = None,
               duplicate_of: str | None = None,
               op_id: str | None = None, refs=()) -> dict:
	"""Terminal close: IMMUTABLE (WS-2 ruling — there is no reopen; later
	evidence becomes follow-up Work). No route and no next endpoint
	afterwards, and the ancestor gate recomputes: closure rolls UP through
	recomputation, never down through force. Every terminal close names
	exactly one of `satisfying`, `non-satisfying`, `rejected`, or
	`cancelled` and records a non-empty rationale — terminal decisions
	are durable review evidence, never reconstructed from thread
	prose. Cancellation is ordinary accelerated close under the same
	Route-only authority: no cascade, no child bypass. A duplicate is a
	`rejected` close whose structured reason names the surviving Work
	through the explicit non-gating `duplicate_of` relation; free text
	alone is insufficient."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "close_work", op_id,
	                       {"work": work_id, "rationale": rationale,
	                        "outcome": outcome,
	                        "duplicate_of": duplicate_of, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if row["status"] == CLOSED:
		raise WorkError(f"{work_id} is already closed")
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("a terminal close records its rationale; every "
		                "outcome requires one")
	if outcome not in OUTCOMES:
		raise WorkError(
			f"a terminal close names exactly one outcome of {OUTCOMES}; "
			f"got {outcome!r} — the result is never inferred from "
			f"classification or rationale prose")
	if duplicate_of is not None:
		if outcome != "rejected":
			raise WorkError(
				f"duplicate_of marks a duplicate REJECTION; a "
				f"{outcome!r} close cannot carry it")
		if duplicate_of == work_id:
			raise WorkError(f"{work_id} cannot be a duplicate of itself")
		target = _work(store, duplicate_of)
		if target["duplicate_of"] is not None:
			raise WorkError(
				f"{duplicate_of} is itself a duplicate of "
				f"{target['duplicate_of']}; name the canonical survivor "
				f"directly — chains have no surviving record")
	if row["classification"] == "duplicate" and outcome == "rejected" \
			and duplicate_of is None:
		raise WorkError(
			"a duplicate rejection names the surviving canonical work "
			"through duplicate_of; free text alone is insufficient")
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
	payload = {"work": work_id, "rationale": rationale,
	           "outcome": outcome, "duplicate_of": duplicate_of,
	           "was_route_team": row["route_team"],
	           "was_route_kind": row["route_kind"]}

	def mutate(conn, seq):
		# WF-09 race 2: status and children rechecked inside the lock — a
		# competing close or late create can commit between the optimistic
		# checks above and this transaction.
		live = conn.execute(
			"SELECT status, parent, classification, route_team, "
			"route_kind FROM work WHERE id=?", (work_id,)).fetchone()
		if live["status"] == CLOSED:
			raise WorkError(f"{work_id} is already closed")
		# The duplicate-link discipline is rechecked against the
		# COMMITTING classification — a classify landing between the
		# pre-read and this lock must not smuggle a linkless duplicate.
		if live["classification"] == "duplicate" and \
				outcome == "rejected" and duplicate_of is None:
			raise WorkError(
				"a duplicate rejection names the surviving canonical "
				"work through duplicate_of; free text alone is "
				"insufficient")
		if duplicate_of is not None:
			target = conn.execute(
				"SELECT status, duplicate_of FROM work WHERE id=?",
				(duplicate_of,)).fetchone()
			if target is None:
				raise WorkError(f"no work {duplicate_of!r}")
			# R74 in-lock: a racing close may have just made the target
			# a duplicate itself — a chain or mutual cycle would leave
			# no canonical survivor. Closed canonical targets stay
			# valid; duplicate targets never are.
			if target["duplicate_of"] is not None:
				raise WorkError(
					f"{duplicate_of} is itself a duplicate of "
					f"{target['duplicate_of']}; name the canonical "
					f"survivor directly — chains have no surviving "
					f"record")
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
		# handler of the Route, in the lock, snapshot recorded.
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "close")
		payload["was_route_team"] = live["route_team"]
		payload["was_route_kind"] = live["route_kind"]
		# WS-2 group 2: trials end with their work — no assignment stays
		# actionable. Group 3: the close AUDITS the concluded trial's
		# evidence basis — candidate, receipt fraction, raw observation
		# summary, elapsed exposure, and the pending assignments about to
		# be withdrawn — recording the basis of the judgment without
		# fabricating feedback.
		concluding = conn.execute(
			"SELECT * FROM trials WHERE work=? AND status='open'",
			(work_id,)).fetchone()
		if concluding is not None:
			tally = {"passed": 0, "failed": 0, "unable": 0}
			assigned = reported = 0
			still_pending = []
			for entry in conn.execute(
					"SELECT team, kind, status, observation FROM "
					"obligations WHERE work=? AND trial=? "
					"AND flavor='verification'",
					(work_id, concluding["trial"])):
				assigned += 1
				if entry["status"] == "reported":
					reported += 1
					tally[entry["observation"]] += 1
				elif entry["status"] == "pending":
					still_pending.append(
						f"{entry['team']}.{entry['kind']}")
			payload["trial_summary"] = {
				"trial": concluding["trial"],
				"candidate": concluding["candidate"],
				"progress": f"{reported}/{assigned}",
				"observations": tally,
				"review_at": concluding["review_at"],
				"deadline_generation":
					concluding["deadline_generation"],
				"created_ts": concluding["created_ts"],
				"closed_ts": store.clock(),
				"withdrawn_pending": still_pending,
				"basis": rationale,
			}
		conn.execute(
			"UPDATE trials SET status='closed', ended_seq=? "
			"WHERE work=? AND status='open'", (seq, work_id))
		# W47: terminal closure ends the open episode and opens none —
		# a closed Work has no phase at all.
		_phase_now(payload, work_id, None)
		conn.execute(
			"UPDATE work SET status=?, ready=0, outcome=?, rationale=?, "
			"duplicate_of=?, "
			"route_team=NULL, route_kind=NULL, next_team=NULL, "
			"next_kind=NULL, handler_team=NULL, handler_member=NULL, "
			"closed_seq=? WHERE id=?",
			(CLOSED, outcome, rationale, duplicate_of, seq, work_id))
		# W78: and it ends the GATE episode with it. Closing blocked
		# Work is explicitly allowed — a consumer can be cancelled while
		# its blocker stays open — and the `phase` column keeps its last
		# value because it is NOT NULL, so without this the terminal row
		# would keep a live gate: a closed Work painting a `Wait` cause
		# and a running Held clock, which is the exact invariant this
		# Work exists to establish. The edge itself remains journal
		# history; what ends is the scheduler episode.
		if conn.execute("SELECT gate_kind FROM work WHERE id=?",
		                (work_id,)).fetchone()["gate_kind"] is not None:
			_write_gate(conn, work_id, payload, None)
		_touch_work(conn, work_id)
		# WS-2 group-1 correction (ruled): terminal close atomically
		# WITHDRAWS every pending exact @ obligation this work carries —
		# classic requests and verification assignments alike — so closed
		# history can never gain a late answer. Each withdrawal points at
		# its own audited withdraw event.
		_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
		                  "the carrying work closed")
		if live["parent"] is not None:
			_recompute_ready(conn, live["parent"], payload)
		# THE FAN-OUT, level-triggered: every dependent recomputes from its
		# own current blocker set. No message is addressed to anyone; a
		# dependent with other open blockers simply stays unready.
		for dependent in conn.execute(
				"SELECT work FROM edges WHERE blocker=?", (work_id,)):
			_recompute_ready(conn, dependent["work"], payload)
		# WS-1: this close may have shut the LAST gate some blocked work
		# recorded — the wake commits atomically with it, or not at all.
		_sweep_wakes(conn, f"{actor_team}.{actor}", payload)

	return store._write("close_work", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


# -- finding-active-work-claim: the atomic phase-orthogonal claim ------------

def claim_work(store: Authority, work_id: str, *, actor_team: str,
               actor: str, op_id: str | None = None, refs=()) -> dict:
	"""THE atomic claim: records WHO is executing, and with it the
	scheduler state that fact implies.

	One eligible handler of the live Route endpoint acquires open,
	runnable, unclaimed Work — every condition rechecked inside the write
	transaction, so an earlier `ready` observation is advisory and a
	competing claim fails closed naming the recorded claimant.

	W38: the claim is what makes Work `active`, because active means
	somebody is doing it. Phase and Handler move together here and in
	every releasing transition, so the invariant `active iff Handler` has
	no window in which it is false."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "claim", op_id,
	                       {"work": work_id, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_work(store, work_id)
	payload = {"work": work_id}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, phase, handler_team, handler_member "
			"FROM work WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; terminal "
			                f"work cannot be claimed")
		if live["phase"] in ("block", "parked"):
			raise WorkError(f"{work_id} is {live['phase']}; blocked and "
			                f"parked work cannot be claimed")
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "claim")
		gates = _open_gates(conn, work_id)
		if gates:
			raise WorkError(
				f"{work_id} has {gates} unmet dependency/child gate(s); "
				f"blocked work cannot be claimed — readiness is decided "
				f"here, in the write transaction")
		if live["handler_team"] is not None:
			raise WorkError(
				f"{work_id} is already claimed by "
				f"{live['handler_team']}.{live['handler_member']}; "
				f"conflicting claim attempts fail closed (an exact "
				f"retry replays through its operation id)")
		payload["claimant"] = f"{actor_team}.{actor}"
		payload["from_phase"] = live["phase"]
		payload["phase"] = "active"
		_phase_now(payload, work_id, "active")
		conn.execute(
			"UPDATE work SET handler_team=?, handler_member=?, "
			"phase='active' WHERE id=?", (actor_team, actor, work_id))
		_touch_work(conn, work_id)

	def finish(result):
		# The committed claimant rides the replayable result — an agent
		# retrying reads WHO holds the claim without a second call.
		result["claimant"] = payload["claimant"]
		result["phase"] = payload["phase"]

	return store._write("claim", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


def release_claim(store: Authority, work_id: str, *, actor_team: str,
                  actor: str, expect: str, reason: str,
                  op_id: str | None = None, refs=()) -> dict:
	"""Explicit claimant recovery (ruled): one honest operation for
	self-release AND forced recovery. Authority is the live Route
	endpoint's resolved handlers; expect= is a mandatory compare-and-swap
	against the exact recorded claimant, decided inside the write
	transaction; reason= is durable evidence. A successful release clears
	ONLY the claimant — phase, Route, Next, readiness, dependencies,
	gate and discussion state are untouched."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	if not isinstance(reason, str) or not reason.strip():
		raise WorkError("a release records its non-empty durable reason — "
		                "self-release and forced recovery both explain "
		                "why the work became unclaimed")
	reason = reason.strip()
	if not isinstance(expect, str) or expect.count(".") != 1 or \
			not all(expect.split(".")):
		raise WorkError(f"expect= {expect!r} is not team.member shaped; "
		                f"recovery never guesses whose execution it is "
		                f"interrupting")
	operation = _operation(store, actor_team, actor, "release", op_id,
	                       {"work": work_id, "expect": expect,
	                        "reason": reason, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_work(store, work_id)
	payload = {"work": work_id, "expect": expect, "reason": reason}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, handler_team, handler_member FROM work "
			"WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; terminal "
			                f"work carries no claim to release")
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "release")
		if live["handler_team"] is None:
			raise WorkError(f"{work_id} is unclaimed; there is no "
			                f"execution claim to release")
		recorded = f"{live['handler_team']}.{live['handler_member']}"
		if recorded != expect:
			raise WorkError(
				f"{work_id} is claimed by {recorded}, not {expect}; "
				f"the compare-and-swap refuses — recovery never "
				f"guesses whose execution it is interrupting")
		payload["released_claimant"] = recorded
		landing = _unclaimed_state(conn, work_id)
		_phase_now(payload, work_id, landing)
		conn.execute(
			# W38: releasing the claim ends `active`, and the state it
			# lands in is derived from the committed gates rather than
			# carried in — so a release that races a new blocker cannot
			# leave runnable-looking Work that nothing can claim.
			"UPDATE work SET handler_team=NULL, handler_member=NULL, "
			"phase=? WHERE id=?", (landing, work_id))
		# W78: landing in `block` names the gate that holds it and
		# starts that gate's episode in the same transaction.
		_retarget_gate(conn, work_id, payload)
		_touch_work(conn, work_id)
		# W49: the Work becomes available to its Route endpoint again.
		# Every eligible handler — including the released claimant, who
		# may legitimately re-take it — needs a fresh wake.
		_mint_episode(conn, work_id)

	def finish(result):
		result["released_claimant"] = payload["released_claimant"]

	return store._write("release", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


# -- WS-1: public classification and operational phase -----------------------

def heartbeat(store: Authority, work_id: str, *, actor_team: str,
              actor: str, op_id: str | None = None, refs=()) -> dict:
	"""W47: the deliberate claimant liveness beat — an audited generic
	event, never an automatic assertion of client presence. Authorized
	STRICTER than route membership: only the exact recorded active
	claimant commits it, rechecked inside the committing transaction
	(a release/pass/close winning the race refuses the beat without an
	event). The beat deliberately avoids `_touch_work`: it is not a
	semantic Work change — no reorder, no change identity, no phase,
	no message, no claim-age reset. Exact op-id retries replay."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "heartbeat", op_id,
	                       {"work": work_id, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	claimant = f"{actor_team}.{actor}"
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"has no claim to keep alive")
	if row["handler_team"] is None:
		raise WorkError(f"{work_id} is unclaimed; a heartbeat asserts "
		                f"the CURRENT claim and nothing else")
	recorded = f"{row['handler_team']}.{row['handler_member']}"
	if recorded != claimant:
		raise WorkError(
			f"{work_id} is claimed by {recorded}; only the exact "
			f"current claimant heartbeats — route membership never "
			f"suffices")

	payload = {"work": work_id, "claimant": claimant}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, handler_team, handler_member FROM work "
			"WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed "
			                f"work has no claim to keep alive")
		if live["handler_team"] is None or \
				f"{live['handler_team']}.{live['handler_member']}" \
				!= claimant:
			raise WorkError(
				f"{work_id} is no longer claimed by {claimant}; the "
				f"racing transition won and the beat records nothing")
		# Deliberately NO _touch_work and no row update: the audited
		# event is the whole record.

	return store._write("heartbeat", claimant, payload, mutate,
	                    operation=operation, references=refs)


def prioritize(store: Authority, work_id: str, *, actor_team: str,
               actor: str, priority: str, op_id: str | None = None,
               refs=()) -> dict:
	"""W3: the audited, effectively-once priority revision. Priority is
	OWNING-team authority: any configured member of the Work's owning
	team may revise it, independent of the Route, claimant,
	phase, and readiness — and members of other teams may discuss
	urgency in a Thread but never reprioritize here. An ordering signal
	only: readiness, dependencies, Route/Next, phase, status, and
	closure are untouched. Closed Work refuses; a same-value change
	refuses (an exact op-id retry replays)."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "prioritize", op_id,
	                       {"work": work_id, "priority": priority,
	                        "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if priority not in PRIORITIES:
		raise WorkError(f"priority {priority!r} is not one of "
		                f"{PRIORITIES}")

	if actor_team != row["team"]:
		raise WorkError(
			f"{work_id} belongs to team {row['team']!r}; priority is "
			f"owning-team authority — other teams discuss urgency in "
			f"a Thread, they do not reprioritize")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"refuses priority changes; closure is terminal")

	payload = {"work": work_id, "from": row["priority"], "to": priority}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, priority FROM work WHERE id=?",
			(work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed "
			                f"work refuses priority changes; closure "
			                f"is terminal")
		if live["priority"] == priority:
			raise WorkError(f"{work_id} is already {priority} priority")
		payload["from"] = live["priority"]
		conn.execute("UPDATE work SET priority=? WHERE id=?",
		             (priority, work_id))
		_touch_work(conn, work_id)

	return store._write("prioritize", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, references=refs)


def classify(store: Authority, work_id: str, *, actor_team: str, actor: str,
             classification: str, op_id: str | None = None, refs=()) -> dict:
	"""An explicit, audited classification change by a currently resolved
	handler of the Work's Route. Canonical values only — compact
	display vocabulary is never a mutation value. Origin is untouched."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "classify", op_id,
	                       {"work": work_id,
	                        "classification": classification, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
		_touch_work(conn, work_id)

	return store._write("classify", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


def set_phase(store: Authority, work_id: str, *, actor_team: str, actor: str,
              phase: str, reason: str | None = None,
              wait: str | int | None = None,
              op_id: str | None = None, refs=()) -> dict:
	"""An explicit, audited operational-phase change by a currently
	resolved handler of the Route.

	The special rules, exactly as ruled: `parked` needs a non-empty reason,
	keeps its one accountable Route, and leaves ONLY through explicit
	parked→queued; `block` records exactly one typed gate
	(`wait="gates"` for the aggregate required-Work gate, or an obligation
	seq for one exact pending `@`), refuses an already-satisfied condition,
	and leaves ONLY through the condition-bound audited wake; closed work
	refuses.

	W38: `active` is NOT reachable here. It means somebody is executing
	the Work, which is a fact only `claim` can establish, so asking for it
	refuses and names the claim instead. The remaining moves are the
	genuine scheduler decisions: defer it, gate it, or make it runnable
	again."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "set_phase", op_id,
	                       {"work": work_id, "phase": phase,
	                        "reason": reason, "wait": wait, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if phase == "active":
		raise WorkError(
			"active is not a phase you set: it means a participant is "
			"executing the Work, which only `claim` establishes — claim "
			"it, or move it to queued, block, or parked")
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
	if phase == "block":
		if wait is None:
			raise WorkError(
				"block requires a recorded gate: wait='gates' for the "
				"aggregate required-Work gate, or the seq of one exact "
				"pending @ obligation")
		if wait != "gates" and not isinstance(wait, int):
			raise WorkError(f"wait condition {wait!r} is neither 'gates' "
			                f"nor an obligation seq")
	elif wait is not None:
		raise WorkError(f"a gate belongs to 'block' only, "
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
		if live["phase"] == "block":
			raise WorkError(
				f"{work_id} is blocked on its displayed gate; block "
				f"leaves only through the gate-bound audited wake")
		payload["from"] = live["phase"]
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "set_phase")
		wait_type, wait_obligation = None, None
		if phase == "block":
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
		# W38: every phase this verb can reach is an UNCLAIMED state, so
		# each one releases. Previously only block and parked did,
		# because queued/research/active/review were all claimable
		# stages; with the role-shaped phases gone, `queued` means
		# runnable and unclaimed just as literally as the other two.
		if phase in ("queued", "block", "parked"):
			live_claim = conn.execute(
				"SELECT handler_team, handler_member FROM work WHERE id=?",
				(work_id,)).fetchone()
			if live_claim["handler_team"] is not None:
				payload["released_claimant"] = (
					f"{live_claim['handler_team']}."
					f"{live_claim['handler_member']}")
				conn.execute(
					"UPDATE work SET handler_team=NULL, "
					"handler_member=NULL WHERE id=?", (work_id,))
		# W38 R2: leaving a deliberate park does not make open gates
		# vanish. Asking for `queued` asks to RESUME, and what that
		# reveals is whatever the committed gates say — queued when
		# runnable, blocked on those gates when not. Writing queued
		# verbatim would commit runnable-looking Work that nothing can
		# claim, which is the same contradiction R1 closes on the
		# readiness side.
		committed = phase
		if phase == "queued":
			committed = _unclaimed_state(conn, work_id)
			payload["to"] = committed
		_phase_now(payload, work_id, committed)
		conn.execute("UPDATE work SET phase=? WHERE id=?",
		             (committed, work_id))
		# W78: an explicit `block wait=<obligation>` names its own gate;
		# every other landing derives the displayed gate from what is
		# actually open. Both go through the one episode writer, so the
		# phase and the thing holding it are committed together.
		if committed == "block" and wait_obligation is not None:
			_enter_message_gate(conn, work_id, payload, wait_obligation)
		else:
			_retarget_gate(conn, work_id, payload)
		_touch_work(conn, work_id)
		# W49: ONLY the parked→queued resume mints. Entering block or
		# parked REMOVES actionability rather than granting it, and a
		# release into queued mints through `release` itself.
		if payload["from"] == "parked" and phase == "queued":
			_mint_episode(conn, work_id)

	return store._write("set_phase", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


# -- WS-2 group 2: candidate verification trials ------------------------------

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


def _trial(store: Authority, work_id: str, trial_number: int):
	row = store.conn.execute(
		"SELECT * FROM trials WHERE work=? AND trial=?",
		(work_id, trial_number)).fetchone()
	if row is None:
		raise WorkError(f"{work_id} has no trial {trial_number}")
	return row


def create_trial(store: Authority, work_id: str, *, actor_team: str,
                 actor: str, candidate: str, assign,
                 review_at: str | None = None,
                 op_id: str | None = None, refs=()) -> dict:
	"""One verification trial for one EXACT candidate, with an exact
	selected set of verifier routes (each an @ verification obligation —
	actionable for testing WITHOUT clearing anyone's dependency, granting
	no mutation authority, and never a wake condition).

	Publishing a different candidate is a NEW trial: any open trial is
	superseded and its pending assignments are withdrawn with route
	notification — replies stay pinned to the exact candidate they tested
	and never carry forward silently."""
	_member(store, actor_team, actor)
	if isinstance(assign, str):
		assign = [assign]
	assign = list(assign or [])
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "create_trial",
	                       op_id, {"work": work_id,
	                               "candidate": candidate,
	                               "assign": assign,
	                               "review_at": review_at, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a closed work "
		                f"takes no verification trials")
	if not isinstance(candidate, str) or not candidate.strip():
		raise WorkError("a trial names its exact candidate/artifact; "
		                "candidate identity is required and immutable")
	if isinstance(assign, str):
		assign = [assign]
	if not assign:
		raise WorkError("a trial selects at least one exact verifier route")
	selected = []
	for endpoint in assign:
		pair = _one_endpoint(store, endpoint, "verification assignment")
		if pair in selected:
			raise WorkError(
				f"verification assignment {endpoint!r} is selected twice; "
				f"one trial creates at most one obligation per endpoint")
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
			                f"takes no verification trials")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "try")
		previous = conn.execute(
			"SELECT trial FROM trials WHERE work=? AND status='open'",
			(work_id,)).fetchone()
		if previous is not None:
			conn.execute(
				"UPDATE trials SET status='superseded', ended_seq=? "
				"WHERE work=? AND trial=?",
				(seq, work_id, previous["trial"]))
			_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
			                  "superseded by a new candidate trial",
			                  trial_number=previous["trial"])
			payload["supersedes"] = previous["trial"]
		# R42: ONE transaction-local instant — the deadline is rechecked
		# against it inside the committing write (it may have passed since
		# the optimistic check), and it becomes the trial's created_ts.
		now = store.clock()
		if review_at is not None and review_at <= now:
			raise WorkError(
				f"review_at {review_at!r} is not later than now ({now}); "
				f"a deadline born expired is a loose end")
		number = (conn.execute(
			"SELECT COALESCE(MAX(trial), 0) AS n FROM trials WHERE work=?",
			(work_id,)).fetchone()["n"]) + 1
		conn.execute(
			"INSERT INTO trials (work, trial, candidate, status, "
			"review_at, deadline_generation, created_ts, created_seq) "
			"VALUES (?, ?, ?, 'open', ?, ?, ?, ?)",
			(work_id, number, candidate, review_at,
			 1 if review_at else 0, now, seq))
		payload["trial"] = number
		payload["assignments"] = []
		for team, kind in selected:
			resolution = resolve_endpoint(conn, team, kind,
			                              "verification assignment")
			assignment_seq = _emit(
				conn, "assign", f"{actor_team}.{actor}",
				{"work": work_id, "trial": number,
				 "candidate": candidate, "resolution": resolution})
			conn.execute(
				"INSERT INTO obligations (seq, work, message_seq, team, "
				"kind, route, role, handlers, generation, flavor, trial) "
				"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'verification', ?)",
				(assignment_seq, work_id, seq, team, kind,
				 resolution["route"], resolution["role"],
				 _json.dumps(resolution["handlers"]),
				 resolution["generation"], number))
			payload["assignments"].append(
				{"obligation": assignment_seq, "resolution": resolution})
		mutate.trial_number = number

	def finish(result):
		result["trial"] = mutate.trial_number
		result["assignments"] = [entry["obligation"]
		                         for entry in payload["assignments"]]

	return store._write("create_trial", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    finish=finish, references=refs)


def _withdraw_pending(conn, work_id: str, actor: str, reason: str,
                      trial_number=None) -> None:
	"""Withdraw pending obligations (optionally one trial's) with the
	audited per-obligation notification — shared by close, supersession,
	and abandon. Withdrawal never fabricates feedback."""
	import json as _json
	clause = "work=? AND status='pending'"
	params = [work_id]
	if trial_number is not None:
		clause += " AND trial=?"
		params.append(trial_number)
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
           observation: str, evidence: str,
           op_id: str | None = None, refs=()) -> dict:
	"""The verifier's IMMUTABLE raw observation: exactly passed, failed, or
	unable, with evidence, pinned to its assignment/trial/candidate. It
	never votes, transitions, satisfies, wakes, or closes anything."""
	_member(store, team, member)
	refs = _parse_refs(store, refs)
	operation = _operation(store, team, member, "report", op_id,
	                       {"obligation": obligation_seq,
	                        "observation": observation,
	                        "evidence": evidence, "refs": refs})
	if isinstance(operation, dict):
		return operation
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

	pinned = _trial(store, obligation["work"], obligation["trial"])
	payload = {"work": obligation["work"], "obligation": obligation_seq,
	           "trial": obligation["trial"],
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

	return store._write("report", f"{team}.{member}", payload, mutate,
	                    operation=operation,
	                    references=refs)


def assess(store: Authority, obligation_seq: int, *, actor_team: str,
           actor: str, assessment: str, rationale: str,
           op_id: str | None = None, refs=()) -> dict:
	"""The provider reviewer's SEPARATE immutable judgment of a report:
	accepted, rejected, or inconclusive, with rationale. It never rewrites
	the raw observation; a changed mind is a new superseding act."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "assess", op_id,
	                       {"obligation": obligation_seq,
	                        "assessment": assessment,
	                        "rationale": rationale, "refs": refs})
	if isinstance(operation, dict):
		return operation
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

	return store._write("assess", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


def abandon_trial(store: Authority, work_id: str, trial_number: int, *,
                  actor_team: str, actor: str, reason: str,
                  op_id: str | None = None, refs=()) -> dict:
	"""End a trial WITHOUT closing the work: pending assignments are
	withdrawn with route notification, candidate and report history stay
	immutable, and no provider or consumer lifecycle state changes."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "abandon_trial",
	                       op_id, {"work": work_id, "trial": trial_number,
	                               "reason": reason, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_work(store, work_id)
	existing = _trial(store, work_id, trial_number)
	if existing["status"] != "open":
		raise WorkError(f"trial {trial_number} of {work_id} is already "
		                f"{existing['status']}")
	if not isinstance(reason, str) or not reason.strip():
		raise WorkError("abandoning a trial records a reason")

	payload = {"work": work_id, "trial": trial_number, "reason": reason}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status FROM trials WHERE work=? AND trial=?",
			(work_id, trial_number)).fetchone()
		if live["status"] != "open":
			raise WorkError(f"trial {trial_number} of {work_id} is "
			                f"already {live['status']}")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "abandon trial")
		conn.execute(
			"UPDATE trials SET status='abandoned', ended_seq=? "
			"WHERE work=? AND trial=?", (seq, work_id, trial_number))
		_withdraw_pending(conn, work_id, f"{actor_team}.{actor}",
		                  reason, trial_number=trial_number)

	return store._write("abandon_trial", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


def extend_trial(store: Authority, work_id: str, trial_number: int, *,
                 actor_team: str, actor: str, review_at: str,
                 op_id: str | None = None, refs=()) -> dict:
	"""Extend the SAME candidate's testing window: an explicit audited
	reviewer decision — never a hidden timer reset. All reports and pending
	assignments are retained; the deadline generation advances so due-ness
	is per-generation; repeated extensions are visible history. May also
	give a deadline to a trial created without one."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "extend_trial",
	                       op_id, {"work": work_id, "trial": trial_number,
	                               "review_at": review_at, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_work(store, work_id)
	existing = _trial(store, work_id, trial_number)
	if existing["status"] != "open":
		raise WorkError(f"trial {trial_number} of {work_id} is "
		                f"{existing['status']}; only an open trial's window "
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

	payload = {"work": work_id, "trial": trial_number,
	           "candidate": existing["candidate"],
	           "from_review_at": existing["review_at"],
	           "to_review_at": review_at}

	def mutate(conn, seq):
		live = conn.execute(
			"SELECT status, review_at, deadline_generation FROM trials "
			"WHERE work=? AND trial=?", (work_id, trial_number)).fetchone()
		if live["status"] != "open":
			raise WorkError(f"trial {trial_number} of {work_id} is "
			                f"{live['status']}; only an open trial's "
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
			conn, work_id, actor_team, actor, "extend trial")
		payload["deadline_generation"] = live["deadline_generation"] + 1
		conn.execute(
			"UPDATE trials SET review_at=?, deadline_generation=? "
			"WHERE work=? AND trial=?",
			(review_at, live["deadline_generation"] + 1, work_id,
			 trial_number))

	return store._write("extend_trial", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


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
                   actor_team: str, actor: str, rationale: str,
                   op_id: str | None = None, refs=()) -> dict:
	"""`work_id` blocked_by `blocker_id` — the ONLY thing that gates
	readiness across records (labels are inert, by clarification). Cross-team
	on purpose; that is the convergence model."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "add_dependency",
	                       op_id, {"work": work_id, "on": blocker_id,
	                               "rationale": rationale, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	blocker = _work(store, blocker_id)
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("block records why the dependency is required; "
		                "rationale cannot be empty")
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
	           "blocker_status": blocker["status"],
	           "rationale": rationale}

	def mutate(conn, seq):
		# In-lock recheck (WF-09 class): the closed-takes-no-blockers and
		# duplicate checks above are optimistic; they hold only if rechecked
		# under the same lock as the cycle walk below.
		live = conn.execute("SELECT status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a closed work "
			                f"takes no new blockers; closure is terminal")
		# R1 matrix: changing a Work's dependencies belongs to its Route
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
				f"blocked forever, and it is refused at insertion")
		conn.execute(
			"INSERT INTO edges (work, blocker, created_seq) VALUES (?, ?, ?)",
			(work_id, blocker_id, seq))
		_recompute_ready(conn, work_id, payload)

	return store._write("add_dependency", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


def remove_dependency(store: Authority, work_id: str, blocker_id: str, *,
                      actor_team: str, actor: str, rationale: str,
                      op_id: str | None = None, refs=()) -> dict:
	"""Correct one mistaken LIVE dependency without falsifying either Work.

	The current graph table loses the edge; the immutable add/remove events
	preserve how the mistake arose and why it was corrected. Finished edges are
	history, not live gates, and cannot be rewritten through this operation.
	"""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "remove_dependency",
	                       op_id, {"work": work_id, "on": blocker_id,
	                               "rationale": rationale, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	blocker = _work(store, blocker_id)
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("unblock records why the live dependency was wrong; "
		                "rationale cannot be empty")
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; a terminal Work has "
		                f"no live dependency to correct")
	if blocker["status"] != OPEN:
		raise WorkError(f"{blocker_id} is {blocker['status']}; its edge is "
		                f"historical, not a live dependency")
	edge = store.conn.execute(
		"SELECT created_seq FROM edges WHERE work=? AND blocker=?",
		(work_id, blocker_id)).fetchone()
	if edge is None:
		raise WorkError(f"{work_id} has no live dependency on {blocker_id}")

	payload = {"work": work_id, "blocker": blocker_id,
	           "rationale": rationale, "created_seq": edge["created_seq"]}

	def mutate(conn, seq):
		live = conn.execute("SELECT status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; a terminal Work "
			                f"has no live dependency to correct")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "remove_dependency")
		live_blocker = conn.execute(
			"SELECT status FROM work WHERE id=?", (blocker_id,)).fetchone()
		if live_blocker["status"] != OPEN:
			raise WorkError(f"{blocker_id} is {live_blocker['status']}; its "
			                f"edge is historical, not a live dependency")
		live_edge = conn.execute(
			"SELECT created_seq FROM edges WHERE work=? AND blocker=?",
			(work_id, blocker_id)).fetchone()
		if live_edge is None:
			raise WorkError(
				f"{work_id} has no live dependency on {blocker_id}")
		payload["created_seq"] = live_edge["created_seq"]
		conn.execute("DELETE FROM edges WHERE work=? AND blocker=?",
		             (work_id, blocker_id))
		_recompute_ready(conn, work_id, payload)
		# Removing the final live gate satisfies the same recorded
		# `block` Work gate as closing that gate. Recompute marks
		# readiness; the level-triggered sweep performs the audited phase
		# release in THIS correction transaction rather than stranding the
		# Work until some unrelated later writer happens to sweep it.
		_sweep_wakes(conn, f"{actor_team}.{actor}", payload)

	return store._write("remove_dependency", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


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
		# R71: EVERY individual selector must land somewhere, wildcard
		# shapes included — a `ghost.*` publishing to nobody would be a
		# silent no-op include, especially misleading when a config race
		# removes the last match between the optimistic expansion and
		# the committing generation.
		if not rows:
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


def respond_obligation(store: Authority, obligation_seq: int, *,
                       team: str, member: str, body: str,
                       op_id: str | None = None, refs=()) -> dict:
	"""The obligated endpoint's team answers; the obligation resolves with
	the response message in one transaction."""
	_member(store, team, member)
	refs = _parse_refs(store, refs)
	operation = _operation(store, team, member, "respond", op_id,
	                       {"obligation": obligation_seq, "body": body, "refs": refs})
	if isinstance(operation, dict):
		return operation
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

	payload = {"obligation": obligation_seq, "work": obligation["work"],
	           "thread": obligation["thread"]}

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
		# R59: the answer returns to the thread the @ was raised in —
		# the obligation names it; participation persists independently
		# after the obligation terminates.
		conn.execute(
			"INSERT INTO messages (seq, thread, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, obligation["thread"], team, member, body))
		_join_thread(conn, obligation["thread"], team, seq)
		conn.execute(
			"UPDATE obligations SET status='responded', resolved_seq=? "
			"WHERE seq=?", (seq, obligation_seq))
		# WS-1: completing an obligation may be the recorded wake condition.
		_sweep_wakes(conn, f"{team}.{member}", payload)

	return store._write("respond", f"{team}.{member}", payload, mutate,
	                    operation=operation,
	                    references=refs)


def dispose_obligation(store: Authority, obligation_seq: int, *,
                       team: str, member: str, disposition: str,
                       op_id: str | None = None, refs=()) -> dict:
	"""No response is owed after all — said explicitly, with a reason, by the
	obligated team. Route policy may classify status as no-action (ruled)."""
	_member(store, team, member)
	refs = _parse_refs(store, refs)
	operation = _operation(store, team, member, "dispose", op_id,
	                       {"obligation": obligation_seq,
	                        "disposition": disposition, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
	           "thread": obligation["thread"],
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
		_sweep_wakes(conn, f"{team}.{member}", payload)

	return store._write("dispose", f"{team}.{member}", payload, mutate,
	                    operation=operation,
	                    references=refs)


def accept_obligation(store: Authority, obligation_seq: int, *,
                      actor_team: str, actor: str, body: str,
                      into: str | None = None,
                      create: dict | None = None,
                      op_id: str | None = None, refs=(),
                      answer_refs=()) -> dict:
	"""WS-3: THE atomic provider acceptance. One transaction commits — or
	refuses whole — the obligation's terminal `accepted` state naming the
	provider Work, the rationale answered into the consumer's thread,
	the provenance-carrying dependency edge, readiness recomputation, the
	exact-obligation wake (R47: the waiter wakes because its named
	condition completed; the new gate keeps it unready; gates-waiters do
	not wake), and — in the create form — the provider Work itself, whose
	creation IS the primary accept act (R48: history establishes the
	provider no later than the acceptance that names it).

	Authority (ruled): the pending exact @ grants its LIVE route handler
	this one narrow atomic authority over the requesting Work. `into=`
	adds same-team + open checks on the provider Work; its Route is
	recorded as evidence, not a second gate. `create=true parent=` alone
	adds the separate live parent-Route handler gate.
	"""
	_member(store, actor_team, actor)
	if create is not None:
		create = {"kind": create.get("kind"),
		          "title": create.get("title"),
		          "classification": create.get("classification"),
		          "phase": create.get("phase"),
		          "parent": create.get("parent")}
		# W31 rev3 (R2): the created provider's title shares the
		# unified subject contract, normalized BEFORE the operation
		# lookup so the fingerprint sees the one canonical value.
		if isinstance(create["title"], str) and create["title"].strip():
			create = dict(create,
			              title=validate_subject(create["title"],
			                                     "work title"))
	refs = _parse_refs(store, refs)
	answer_refs = _parse_refs(store, answer_refs, "answer reference")
	operation = _operation(store, actor_team, actor, "accept", op_id,
	                       {"obligation": obligation_seq, "body": body,
	                        "into": into, "create": create, "refs": refs,
	                        "answer_refs": answer_refs})
	if isinstance(operation, dict):
		return operation
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
		                "existing work (into=) or a new one (create=true)")
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
		# The same fresh-schema rule as direct creation: the submitting
		# side chooses; 'unknown' and omission refuse.
		if classification is None or classification == "unknown":
			raise WorkError(
				"work creation requires a concrete classification; "
				"'unknown' (or omitting it) refuses")
		phase = create.get("phase")
		phase = "queued" if phase is None else phase
		parent = create.get("parent")
		create = dict(create, classification=classification, phase=phase)
		if not isinstance(title, str) or not title.strip():
			raise WorkError("a work title must be non-empty")
		_endpoint(store, provider_team, kind, "accept create=true")
		if classification not in CLASSIFICATIONS:
			raise WorkError(f"classification {classification!r} is not "
			                f"one of {CLASSIFICATIONS}")
		if phase not in PHASES:
			raise WorkError(f"phase {phase!r} is not one of {PHASES}; "
			                f"compact display values are presentation "
			                f"only")
		if phase not in CREATION_PHASES:
			raise WorkError(
				f"a work is not created {phase!r}: block needs a live "
				f"gate and parking needs a reason")
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
			# Provider Route: recorded EVIDENCE, never a gate — shown
			# explicitly unresolved rather than refusing (disposition 2).
			try:
				payload["provider_route"] = resolve_endpoint(
					conn, live_provider["route_team"],
					live_provider["route_kind"], "accept evidence")
			except WorkError:
				payload["provider_route"] = {
					"endpoint":
					f"{live_provider['route_team']}."
					f"{live_provider['route_kind']}",
					"route": None, "role": None, "handlers": [],
					"generation": None}
		else:
			# R48: the provider Work's creation IS this primary act — it
			# exists at the acceptance's own sequence, never after it.
			provider_id = f"{prefix}-W{seq}"
			kind = create["kind"]
			resolution = resolve_endpoint(conn, provider_team, kind,
			                              "accept create=true")
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
				# Disposition 5: the SEPARATE parent-Route handler gate.
				payload["parent_authorization"] = _handler_gate(
					conn, parent, actor_team, actor,
					"accept create=true parent=")
			conn.execute(
				"INSERT INTO work (id, team, title, origin, "
				"classification, phase, status, parent, route_team, "
				"route_kind, ready, created_seq, last_change_seq, "
				"last_changed_at) "
				"VALUES (?, ?, ?, 'external-report', ?, ?, ?, ?, ?, ?, "
				"0, ?, ?, ?)",
				(provider_id, provider_team, create["title"],
				 create["classification"], create["phase"], OPEN, parent,
				 provider_team, kind, seq, seq, clock_ms_now()))
			provider_thread = f"{prefix}-T{seq}"
			conn.execute(
				"INSERT INTO threads (id, subject, created_seq, "
				"created_ts) VALUES (?, ?, ?, ?)",
				(provider_thread, create["title"], seq,
				 store.clock()))
			conn.execute(
				"INSERT INTO thread_labels (thread, work, "
				"added_seq) VALUES (?, ?, ?)",
				(provider_thread, provider_id, seq))
			_join_thread(conn, provider_thread, provider_team, seq)
			conn.execute(
				"INSERT INTO messages (seq, thread, author_team, "
				"author, body, ts) VALUES (?, ?, ?, ?, ?, "
				"datetime('now'))",
				(seq, provider_thread, actor_team, actor, body))
			# W47: `accept create=` is the SECOND Work-creation path,
			# and the ledger has to say so. Without this the provider is
			# born with no recorded phase at all, so its scheduler
			# history is empty from birth — the replay reconstructs
			# nothing, by design, so an unrecorded entry is simply
			# absent forever. `_recompute_ready` below may append a
			# second entry for this same Work in this same event (a gate
			# present at birth moves it straight to block); the replay
			# takes the last entry per event, which is that later truth.
			_phase_now(payload, provider_id, create["phase"])
			_recompute_ready(conn, provider_id, payload)
			if parent is not None:
				_recompute_ready(conn, parent, payload)
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
				f"everyone blocked forever")
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

		# D5/R59: the ORIGINATING thread — where the @ was raised —
		# atomically gains the provider Work's label, collision-safely: a
		# pre-existing label is success audited as `existing`, otherwise
		# this transaction audits `added`. The label is inert context;
		# the GATE remains exclusively the explicit edge above.
		originating = obligation["thread"]
		if conn.execute(
				"SELECT 1 FROM thread_labels WHERE thread=? AND "
				"work=?", (originating, provider_id)).fetchone():
			payload["provider_label"] = "existing"
		else:
			conn.execute(
				"INSERT INTO thread_labels (thread, work, "
				"added_seq) VALUES (?, ?, ?)",
				(originating, provider_id, seq))
			payload["provider_label"] = "added"
		payload["thread"] = originating

		# The rationale returns to that originating thread as its own
		# ordered, audited act (R48: distinct and later in the same
		# transaction).
		message_seq = _emit(
			conn, "post_message", f"{actor_team}.{actor}",
			{"thread": originating, "work": consumer_id,
			 "body_bytes": len(body.encode("utf-8")),
			 "via_accept": seq, "include": [], "request": None,
			 "pass": None, "set_next": None, "consumed_next": False})
		conn.execute(
			"INSERT INTO messages (seq, thread, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(message_seq, originating, actor_team, actor, body))
		if answer_refs:
			# Explicit compound placement (M1): these ride the emitted
			# ANSWER message's own act, never guessed onto the accept.
			store._commit_references(conn, message_seq, answer_refs)
		_join_thread(conn, originating, actor_team, message_seq)

		_recompute_ready(conn, consumer_id, payload)
		# R47: the exact-obligation waiter wakes (its named condition
		# completed) with readiness kept false by the new gate; a
		# gates-waiter gained a gate and does not wake.
		_sweep_wakes(conn, f"{actor_team}.{actor}", payload)
		mutate.provider_id = provider_id

	def finish(result):
		result["provider"] = mutate.provider_id
		result["obligation"] = obligation_seq
		result["work"] = consumer_id
		result["created"] = create is not None
		result["edge"] = {"work": consumer_id,
		                  "blocker": mutate.provider_id,
		                  "via_obligation": obligation_seq}

	return store._write("accept", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


def _thread(store: Authority, thread_id: str):
	row = store.conn.execute("SELECT * FROM threads WHERE id=?",
	                         (thread_id,)).fetchone()
	if row is None:
		raise WorkError(f"no thread {thread_id!r}")
	return row


class _NoAdvance(Exception):
	"""A losing or idempotent mark: NOT an audit act (R62)."""

	def __init__(self, cursor: int):
		self.cursor = cursor


def seen_thread(store: Authority, thread_id: str, *, team: str,
                    member: str, up_to_seq: int,
                    op_id: str | None = None, refs=()) -> dict:
	"""The canonical per-thread cursor advance: monotonic,
	idempotent, bounded by the OBSERVED authority sequence (a future
	cursor would hide messages that do not exist yet), revalidated inside
	the committing transaction, and truthful — a losing lower mark
	returns the committed cursor with NO audit act (R62). WS-5 R76: a
	SUCCESSFUL protected no-op still CONSUMES its operation id — the
	record commits alone (seq NULL, no domain event) so an exact retry
	replays THIS invocation's result even after the cursor advances;
	refusals alone leave the id unconsumed."""
	_member(store, team, member)
	refs = _parse_refs(store, refs)
	operation = _operation(store, team, member, "mark_seen", op_id,
	                       {"thread": thread_id,
	                        "up_to_seq": up_to_seq, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_thread(store, thread_id)
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
			"thread=?", (team, member, thread_id)).fetchone()
		if current is not None and current["seq"] >= up_to_seq:
			raise _NoAdvance(current["seq"])
		conn.execute(
			"INSERT INTO seen (team, member, thread, seq) "
			"VALUES (?, ?, ?, ?) "
			"ON CONFLICT(team, member, thread) DO UPDATE SET "
			"seq = excluded.seq",
			(team, member, thread_id, up_to_seq))

	def finish(result):
		result["advanced"] = True
		result["cursor"] = up_to_seq

	try:
		return store._write("mark_seen", f"{team}.{member}",
		                    {"thread": thread_id,
		                     "up_to": up_to_seq}, mutate,
		                    operation=operation, finish=finish,
	                    references=refs)
	except _NoAdvance as losing:
		if refs:
			raise WorkError(
				"a reference-bearing mark that commits no act refuses "
				"whole; nothing was committed to carry the evidence")
		noop = {"seq": None, "kind": "mark_seen", "advanced": False,
		        "cursor": losing.cursor}
		if operation is not None:
			return store.record_noop(operation, noop)
		noop["operation"] = None
		return noop


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


def validate_subject(subject, what: str = "thread") -> str:
	"""A Thread's REQUIRED concise subject: non-empty, one line, at most
	80 UTF-8 bytes — the space-constrained console renders it whole."""
	if not isinstance(subject, str) or not subject.strip():
		raise WorkError(f"a {what} requires a concise non-empty subject")
	subject = subject.strip()
	if "\n" in subject or "\r" in subject:
		raise WorkError(f"a {what} subject is a single line")
	if len(subject.encode("utf-8")) > 80:
		raise WorkError(f"a {what} subject is at most 80 UTF-8 bytes; "
		                f"got {len(subject.encode('utf-8'))} — details "
		                f"belong in the message body")
	return subject


def create_thread(store: Authority, *, actor_team: str, actor: str,
                      body: str, labels, subject: str,
                      op_id: str | None = None, refs=()) -> dict:
	"""A thread is born labelled and speaking: at least one authorized
	`#WORK` label (each to the actor's own team's Work, at least one of
	them OPEN — the live-context ruling) and its first message, in one
	transaction."""
	_member(store, actor_team, actor)
	if isinstance(labels, str):
		labels = [labels]
	labels = list(labels or [])
	# R1 (W31 review): the subject is validated/normalized BEFORE the
	# operation lookup and joins the typed fingerprint — an identical
	# retry replays; a changed subject under the same op-id refuses.
	subject = validate_subject(subject)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor,
	                       "create_thread", op_id,
	                       {"body": body, "labels": labels,
	                        "subject": subject, "refs": refs})
	if isinstance(operation, dict):
		return operation
	if not isinstance(body, str) or not body:
		raise WorkError("a thread is born with its first message")
	if not labels:
		raise WorkError("a thread is born with at least one "
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
	payload = {"labels": list(labels), "subject": subject,
	           "body_bytes": len(body.encode("utf-8"))}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		thread_id = f"{prefix}-T{seq}"
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
			"INSERT INTO threads (id, subject, created_seq, "
			"created_ts) VALUES (?, ?, ?, ?)",
			(thread_id, subject, seq, store.clock()))
		for work_id in labels:
			conn.execute(
				"INSERT INTO thread_labels (thread, work, "
				"added_seq) VALUES (?, ?, ?)",
				(thread_id, work_id, seq))
		_join_thread(conn, thread_id, actor_team, seq)
		conn.execute(
			"INSERT INTO messages (seq, thread, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, thread_id, actor_team, actor, body))
		payload["thread"] = thread_id
		mutate.thread_id = thread_id

	def finish(result):
		result["thread"] = mutate.thread_id

	return store._write("create_thread", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    finish=finish, references=refs)


def label_thread(store: Authority, thread_id: str, work_id: str, *,
                     actor_team: str, actor: str, op_id: str | None = None, refs=()) -> dict:
	"""Apply an INERT `#WORK` label: reusable context, never a gate. May
	name terminal Work. Authorized by the Work's owning team (D1)."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "label", op_id,
	                       {"thread": thread_id,
	                        "work": work_id, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_thread(store, thread_id)
	row = _work(store, work_id)
	_label_gate(store, row, actor_team, actor)
	if store.conn.execute(
			"SELECT 1 FROM thread_labels WHERE thread=? AND "
			"work=?", (thread_id, work_id)).fetchone():
		raise WorkError(f"{thread_id} already carries #" + work_id)

	payload = {"thread": thread_id, "work": work_id,
	           "work_team": row["team"]}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		if conn.execute(
				"SELECT 1 FROM thread_labels WHERE thread=? AND "
				"work=?", (thread_id, work_id)).fetchone():
			raise WorkError(f"{thread_id} already carries #" + work_id)
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
			"INSERT INTO thread_labels (thread, work, added_seq) "
			"VALUES (?, ?, ?)", (thread_id, work_id, seq))
		_join_thread(conn, thread_id, actor_team, seq)

	return store._write("label", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


def unlabel_thread(store: Authority, thread_id: str, work_id: str,
                       *, actor_team: str, actor: str, op_id: str | None = None, refs=()) -> dict:
	"""Remove a label under the same D1 authority. Removing the FINAL
	label refuses — a thread always keeps explicit Work scope (the
	live-context ruling). The audit act is the history; the row goes."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "unlabel", op_id,
	                       {"thread": thread_id,
	                        "work": work_id, "refs": refs})
	if isinstance(operation, dict):
		return operation
	_thread(store, thread_id)
	row = _work(store, work_id)
	_label_gate(store, row, actor_team, actor)
	if store.conn.execute(
			"SELECT 1 FROM thread_labels WHERE thread=? AND "
			"work=?", (thread_id, work_id)).fetchone() is None:
		raise WorkError(f"{thread_id} does not carry #" + work_id)

	payload = {"thread": thread_id, "work": work_id}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		if conn.execute(
				"SELECT 1 FROM thread_labels WHERE thread=? AND "
				"work=?", (thread_id, work_id)).fetchone() is None:
			raise WorkError(f"{thread_id} does not carry #" + work_id)
		remaining = conn.execute(
			"SELECT COUNT(*) AS n FROM thread_labels WHERE "
			"thread=?", (thread_id,)).fetchone()["n"]
		if remaining <= 1:
			raise WorkError(
				"#" + work_id + f" is {thread_id}'s final label; a "
				f"thread always keeps explicit work scope "
				f"(live-context ruling)")
		conn.execute(
			"DELETE FROM thread_labels WHERE thread=? AND work=?",
			(thread_id, work_id))

	return store._write("unlabel", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


def _select_target(conn, thread_id: str, actor_team: str, actor: str,
                   operation: str, on: str | None):
	"""D2/R55/D9: the ONE currently labelled, eligible, OPEN Work a
	carrying operator acts against. An explicit `on=` must name a
	current label (the thread carries its operating context) and that
	Work must itself be open and authorized. An omitted `on=` resolves
	only when exactly ONE label is eligible for this operation — zero or
	several refuse. Returns (work_id, authorization_snapshot)."""
	labels = [row["work"] for row in conn.execute(
		"SELECT work FROM thread_labels WHERE thread=? "
		"ORDER BY added_seq, work", (thread_id,))]
	if on is not None:
		if on not in labels:
			raise WorkError(
				f"on={on} is not among {thread_id}'s current "
				f"labels; the thread carries its operating context")
		candidates = [on]
	else:
		candidates = labels
	eligible = []
	for work_id in candidates:
		row = conn.execute("SELECT status FROM work WHERE id=?",
		                   (work_id,)).fetchone()
		if row["status"] != OPEN:
			continue
		try:
			authorization = _handler_gate(conn, work_id, actor_team,
			                              actor, operation)
		except WorkError:
			continue
		eligible.append((work_id, authorization))
	if on is not None:
		if not eligible:
			# The explicit selection failed one of its own gates — name
			# the exact refusal, not a cardinality complaint.
			row = conn.execute("SELECT status FROM work WHERE id=?",
			                   (on,)).fetchone()
			if row["status"] != OPEN:
				raise WorkError(
					f"{on} is {row['status']}; closed work refuses "
					f"carrying activity — commentary stays welcome, but "
					f"{operation} needs open work")
			_handler_gate(conn, on, actor_team, actor, operation)
		return eligible[0]
	if len(eligible) != 1:
		raise WorkError(
			f"{operation} with no on= resolves only when exactly one "
			f"labelled work is eligible; {thread_id} has "
			f"{len(eligible)} — select the target with on=")
	return eligible[0]


def post_thread(store: Authority, thread_id: str, *,
                    author_team: str, author: str, body: str,
                    include=(), request: str | None = None,
                    on: str | None = None, wait: bool | None = None,
                    op_id: str | None = None, refs=()) -> dict:
	"""THE public posting surface (Slice B): one message into one
	thread, optionally carrying this operation's tags.

	`+` (include) stays the ONLY fan-out: expanded against live
	endpoints, the exact expansion recorded with the publication, each
	reached team joining monotonic participation once — and no
	obligation, Route, Next, readiness, phase, edge, or Work authority
	changes. `@` (request) affects exactly one currently labelled,
	eligible open Work: `on=` selects it; omitted, it resolves only at
	eligible-cardinality one, and the resolution is recorded and echoed.
	A plain message requires live context — at least one labelled open
	Work — rechecked inside the committing transaction. The Work baton
	NEVER moves through a message: pass is its own threadless Work
	event (W171, finding-pass-is-work-event).

	W159: a directed request WAITS BY DEFAULT. Asking another endpoint
	for input while your own Work stays active and claimed advertises
	progress that cannot happen, and doing it as two commands leaves a
	window where an interruption strands the Work in a lie. So the
	blocking form is ONE transaction: publish, create the obligation,
	enter the exact-obligation wait, release the claim. `wait=false` is
	the deliberate asynchronous override; `include=` remains the way to
	give someone context they owe nothing for. the Route does NOT move —
	the request is input owed to the requesting Work's Route, not a
	transfer."""
	_member(store, author_team, author)
	if isinstance(include, str):
		include = [part for part in include.split(",") if part]
	include = list(include or [])
	refs = _parse_refs(store, refs)
	carrying = request is not None
	if wait is not None and not isinstance(wait, bool):
		raise WorkError("wait= is true or false")
	# W159 R1: the CONDITIONAL GRAMMAR is validated BEFORE the replay
	# lookup. For a plain post the effective wait collapses to false
	# whether `wait` was absent or explicitly supplied, so an invalid
	# `wait=` retry of a valid plain post would otherwise fingerprint
	# identically and REPLAY instead of refusing — an invalid spelling
	# accepted because its meaning happened to be unreachable.
	# Omitted-versus-explicit-true equivalence still holds for an actual
	# request, which is the equivalence the ruling asks for.
	if wait is not None and not carrying:
		raise WorkError("wait= says whether a directed request blocks "
		                "the work it acts on; this message carries no "
		                "request=")
	# The EFFECTIVE value, which is what evidence and retry identity
	# use: omitted and explicit true are the same operation.
	blocking = bool(carrying and (True if wait is None else wait))
	protected = _operation(store, author_team, author, "post", op_id,
	                       {"thread": thread_id, "body": body,
	                        "include": include, "request": request,
	                        "on": on,
	                        # W159: the EFFECTIVE boolean, so an exact
	                        # retry may spell the default explicitly
	                        # while flipping it fails closed.
	                        "wait": blocking,
	                        "refs": refs})
	if isinstance(protected, dict):
		return protected
	_thread(store, thread_id)
	if not isinstance(body, str) or not body:
		raise WorkError("a message body must be non-empty")
	if on is not None and not carrying:
		raise WorkError("on= selects the work a carrying operator acts "
		                "against; this message carries none")
	if include:
		# Optimistic early refusal only; the recorded expansion is redone
		# inside the write transaction (C4 review R1).
		_expand_include(store, include)
	requested = _one_endpoint(store, request, "@ request") \
		if request else None
	operation = "@ request"

	event_kind = "post_message"
	selected = None
	if carrying:
		# Optimistic selection — the selection that COMMITS is
		# re-derived in-lock and must agree.
		selected, _authorization = _select_target(
			store.conn, thread_id, author_team, author, operation, on)
		event_kind = "request"
	elif not _live_context(store.conn, thread_id):
		raise WorkError(
			f"{thread_id} has no labelled open work; closed context "
			f"is readable history — create or label open follow-up work "
			f"to continue (live-context ruling)")

	payload = {"thread": thread_id,
	           "body_bytes": len(body.encode("utf-8")),
	           "include": [], "request": request, "on": on,
	           "wait": blocking if carrying else None}

	def mutate(conn, seq):
		_member_active(conn, author_team, author)
		if carrying:
			# The committing selection: still labelled, open, authorized —
			# and when on= was omitted, STILL exactly one eligible work
			# under the state that commits. A different resolution than
			# the one that decided this act's kind lost a race — refuse,
			# never commit a mislabeled transition.
			work_id, authorization = _select_target(
				conn, thread_id, author_team, author, operation, on)
			if work_id != selected:
				raise WorkError(
					f"{thread_id}'s eligible context changed while "
					f"this {operation} was being prepared; it lost a "
					f"concurrent race — retry against the current state")
			payload["work"] = work_id
			payload["on_resolved"] = on is None
			payload["authorization"] = authorization
		else:
			payload["work"] = None
			if not _live_context(conn, thread_id):
				raise WorkError(
					f"{thread_id} has no labelled open work; closed "
					f"context is readable history (live-context ruling)")
		conn.execute(
			"INSERT INTO messages (seq, thread, author_team, author, "
			"body, ts) VALUES (?, ?, ?, ?, ?, datetime('now'))",
			(seq, thread_id, author_team, author, body))
		# C4: every endpoint this operation touches is resolved HERE,
		# inside the transaction — including the wildcard membership
		# itself (review R1), so the recorded set and its snapshots
		# describe the accepted generation that commits.
		included = _expand_selectors(conn, include) if include else []
		payload["include"] = [
			resolve_endpoint(conn, team, kind, "+ include")
			for team, kind in included]
		touched_teams = {team for team, _kind in included}
		touched_teams.add(author_team)
		if requested is not None:
			resolution = resolve_endpoint(conn, requested[0],
			                              requested[1], "@ request")
			payload["request_resolution"] = resolution
			import json as _json
			conn.execute(
				"INSERT INTO obligations (seq, work, message_seq, team, "
				"kind, route, role, handlers, generation, thread) "
				"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
				(seq, payload["work"], seq, requested[0], requested[1],
				 resolution["route"], resolution["role"],
				 _json.dumps(resolution["handlers"]),
				 resolution["generation"], thread_id))
			touched_teams.add(requested[0])
			if blocking:
				# W159, all inside the ONE transaction that published
				# the message and created the obligation above.
				#
				# The blocking form is a WORKFLOW act, so it needs more
				# than the carrying authorization `_select_target`
				# already applied: only the participant actually
				# EXECUTING the Work may suspend it. A handler who
				# holds no claim, or somebody else's claim, would
				# otherwise be able to park work out from under its
				# executor.
				# Entering block or parked already releases the
				# claim, so the claim check below subsumes any phase
				# test: a suspended Work is necessarily unclaimed and
				# refuses there. Phase is read for the evidence only.
				live = conn.execute(
					"SELECT phase, handler_team, handler_member "
					"FROM work WHERE id=?",
					(payload["work"],)).fetchone()
				if live["handler_team"] is None:
					raise WorkError(
						f"a blocking request suspends {payload['work']}, "
						f"which is unclaimed; claim it first or send the "
						f"request with wait=false")
				if (live["handler_team"], live["handler_member"]) != \
						(author_team, author):
					raise WorkError(
						f"{payload['work']} is claimed by "
						f"{live['handler_team']}.{live['handler_member']}; "
						f"a blocking request suspends the work its own "
						f"executor is doing, never somebody else's")
				payload["released_claimant"] = \
					f"{live['handler_team']}.{live['handler_member']}"
				payload["from_phase"] = live["phase"]
				# W47: this transaction moves the phase itself — it goes
				# through neither `set_phase` nor `release_claim` — so
				# this event must carry the boundary. `from_phase` above
				# is evidence about the claim it released, not the
				# scheduler axis; without the record below the replay
				# leaves the claim's `active` episode open while the
				# Work is in fact blocked on its obligation, which is
				# the false actionability signal W38 ruled against.
				_phase_now(payload, payload["work"], "block")
				# Enter the exact-obligation gate and release the
				# claim. the Route is deliberately untouched: the answer
				# is owed TO the requesting Work's Route, not
				# instead of it.
				conn.execute(
					"UPDATE work SET phase='block', "
					"handler_team=NULL, handler_member=NULL WHERE id=?",
					(payload["work"],))
				# W78: `block M<seq>` at PUBLICATION, timed from here.
				# This is the one gate the authority sets explicitly
				# rather than deriving, because the obligation that
				# suspends the Work is known only at this point — a
				# Work may carry other pending obligations that never
				# blocked it, and those must not capture the cue.
				_enter_message_gate(conn, payload["work"], payload, seq)
				_touch_work(conn, payload["work"])
		for team in sorted(touched_teams):
			_join_thread(conn, thread_id, team, seq)

	def finish(result):
		result["included"] = [entry["endpoint"]
		                      for entry in payload["include"]]
		if carrying:
			result["work"] = payload["work"]
			# W159 R5: the immediate result reports WHICH semantic form
			# committed. Both forms otherwise returned the same shape,
			# so an operator had to read Events back to learn whether
			# their Work was now suspended — inference from omission,
			# which the acceptance boundary names separately from the
			# Events evidence. A plain message invents no choice: it
			# has no request to wait on, so the key is simply absent.
			result["wait"] = blocking

	return store._write(event_kind, f"{author_team}.{author}",
	                    payload, mutate, operation=protected,
	                    finish=finish, references=refs)


def _default_route(conn, team: str, kind: str) -> str | None:
	row = conn.execute("SELECT route FROM kinds WHERE team=? AND handle=?",
	                   (team, kind)).fetchone()
	return row["route"] if row else None


def _current_route(conn, row) -> str | None:
	"""The route a Work is on NOW: its explicit selection, or the
	endpoint's default when it has none."""
	try:
		selected = row["route_selected"]
	except (IndexError, KeyError):
		selected = None
	return selected or _default_route(conn, row["route_team"],
	                                  row["route_kind"])


def pass_work(store: Authority, work_id: str, *, actor_team: str,
              actor: str, to: str,
              comment: str, set_next: str | None = None,
              route: str | None = None,
              op_id: str | None = None, refs=()) -> dict:
	"""W171 (finding-pass-is-work-event): pass is an authoritative
	WORK transition, not a discussion message. One atomic act moves
	the Route to exactly one destination endpoint, records the honest
	destination phase, releases the sender's claim, applies any planned
	Next, and stores `comment` as durable handoff evidence in the pass
	event itself. No Thread is involved: a pass creates no Message,
	advances no cursor, and changes no Message/My/New/obligation count —
	conversation stays explicit and separate through say."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	# W73: the destination phase is no longer typed input, so it is no
	# longer part of the operation identity — the route decides it, and
	# a retry naming the same destination is the same operation.
	protected = _operation(store, actor_team, actor, "pass_work", op_id,
	                       {"work": work_id, "to": to,
	                        "comment": comment, "route": route,
	                        "set_next": set_next, "refs": refs})
	if isinstance(protected, dict):
		return protected
	if not isinstance(comment, str) or not comment.strip():
		raise WorkError("a pass records its handoff evidence; state "
		                "comment=")
	passed = _one_endpoint(store, to, "pass")
	planned = _one_endpoint(store, set_next, "planned Next") \
		if set_next else None
	# Optimistic pre-read — decides this act's event kind; everything
	# is re-derived under the state that COMMITS.
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(f"{work_id} is {row['status']}; the baton of "
		                f"terminal work never moves")
	# W230: "already there" is now about the ROUTE, not only the visible
	# endpoint. Selecting an alternate is a pass to the same endpoint
	# that genuinely moves the baton — to a different agent — and it is
	# the operation this Work exists for. Comparing endpoints alone
	# would have refused exactly the reroute the finding requires, so
	# the comparison includes which route the Work is on now.
	if (row["route_team"], row["route_kind"]) == passed \
			and _current_route(store.conn, row) == (
				route or _default_route(store.conn, *passed)):
		raise WorkError(f"{work_id} is already at "
		                f"{passed[0]}.{passed[1]} on route "
		                f"{_current_route(store.conn, row)!r}; a pass "
		                f"moves the baton")
	consumes_next = (row["next_team"], row["next_kind"]) == passed
	event_kind = "return" if consumes_next else "pass"

	payload = {"work": work_id, "comment": comment,
	           "set_next": set_next, "consumed_next": consumes_next}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		live = conn.execute(
			"SELECT status, route_team, route_kind, route_selected, "
			"next_team, next_kind, handler_team, handler_member FROM work "
			"WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; the baton "
			                f"of terminal work never moves")
		# WS-1 in the lock: only the resolved Route handler transfers.
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "pass")
		# W171 R1: the active claim is EXECUTION ownership, not route
		# membership — a second eligible handler must use the explicit
		# recovery protocol, never transfer underneath the recorded
		# claimant. Only the claimant's own pass releases the claim.
		if live["handler_team"] is not None and \
				(live["handler_team"], live["handler_member"]) != \
				(actor_team, actor):
			raise WorkError(
				f"{work_id} is actively claimed by "
				f"{live['handler_team']}.{live['handler_member']}; route "
				f"eligibility never moves work underneath its recorded "
				f"executor — recover or release the claim explicitly "
				f"first")
		# W230: the authoritative half of the same comparison — route
		# included, so selecting an alternate on the same visible
		# endpoint is a real move. Committed under the lock, because a
		# regen between the pre-read and here could change which route
		# is the default.
		if (live["route_team"], live["route_kind"]) == passed \
				and _current_route(conn, live) == (
					route or _default_route(conn, *passed)):
			raise WorkError(f"{work_id} is already at "
			                f"{passed[0]}.{passed[1]} on route "
			                f"{_current_route(conn, live)!r}; a pass "
			                f"moves the baton")
		if (((live["next_team"], live["next_kind"]) == passed)
				!= consumes_next):
			raise WorkError(
				f"{work_id}'s planned Next changed while this pass "
				f"was being prepared; it lost a concurrent race — "
				f"retry against the current state")
		# W230: an explicitly selected route travels with the handoff.
		# It is resolved INSIDE the lock like every other endpoint fact,
		# so a regen removing the alternate between the operator's
		# choice and the commit refuses rather than routing elsewhere.
		payload["pass_resolution"] = resolve_endpoint(
			conn, passed[0], passed[1], "pass", selected=route)
		payload["route_selected"] = route
		if planned is not None:
			payload["next_resolution"] = resolve_endpoint(
				conn, planned[0], planned[1], "planned Next")
		if consumes_next:
			# The consumed plan clears — but a NEW plan stated on this
			# same return commits with it (W108 trial handoff ruling).
			conn.execute(
				"UPDATE work SET route_team=?, route_kind=?, "
				"route_selected=?, next_team=?, next_kind=? WHERE id=?",
				(passed[0], passed[1], route,
				 planned[0] if planned else None,
				 planned[1] if planned else None, work_id))
		else:
			# An unconsumed planned Next stays VISIBLY set unless this
			# pass plants a new one — never silently cleared.
			conn.execute(
				"UPDATE work SET route_team=?, route_kind=?, "
				"route_selected=?, "
				"next_team=COALESCE(?, next_team), "
				"next_kind=COALESCE(?, next_kind) WHERE id=?",
				(passed[0], passed[1], route,
				 planned[0] if planned else None,
				 planned[1] if planned else None, work_id))
		# W73: the DESTINATION ROUTE decides the phase, never the
		# caller. W49 was handed to baton.impl with phase=queued and
		# then actively worked, so the projection showed a claimed Work
		# sitting in `queued` — exclusive, but an operationally false
		# view that would misdirect scheduling as more agents share a
		# route. Deriving it under the same lock that moves the Route
		# makes that state unrepresentable through the public handoff.
		# An unmapped role refuses rather than guessing; a route
		# transfer never produces `queued`; same-route stage changes
		# remain the separately authorized `set_phase`.
		# W38 supersedes W73's role-to-phase derivation. A handoff
		# hands over RESPONSIBILITY, not activity: the recipient is not
		# working on it until they claim, so the destination phase is
		# the scheduler state of unclaimed Work — queued when runnable,
		# blocked when a gate is unsatisfied. The destination ROLE says
		# implementation or review, and it says so through the Route.
		destination_phase = _unclaimed_state(conn, work_id)
		payload["destination_phase"] = destination_phase
		_phase_now(payload, work_id, destination_phase)
		conn.execute(
			"UPDATE work SET handler_team=NULL, handler_member=NULL, "
			"phase=? WHERE id=?", (destination_phase, work_id))
		_retarget_gate(conn, work_id, payload)
		_touch_work(conn, work_id)
		# W49: a pass/return hands the Work to a new Route and
		# releases the sender's claim — the canonical new episode. The
		# recipient must be woken even if a previous episode of the SAME
		# Work was delivered to them and never observed as absent.
		_mint_episode(conn, work_id)

	def finish(result):
		result["work"] = work_id
		result["to"] = payload["pass_resolution"]["endpoint"]
		result["destination_phase"] = payload["destination_phase"]
		result["consumed_next"] = consumes_next

	return store._write(event_kind, f"{actor_team}.{actor}",
	                    payload, mutate, operation=protected,
	                    finish=finish, references=refs)


def _current_revision(conn, work_id: str) -> int:
	row = conn.execute(
		"SELECT MAX(revision) AS top FROM revisions WHERE work=?",
		(work_id,)).fetchone()
	return row["top"] or 0


def revise_work(store: Authority, work_id: str, *, actor_team: str,
                actor: str, message_seq: int | None = None,
                expected_revision: int | None = None,
                rationale: str | None = None,
                op_id: str | None = None, refs=()) -> dict:
	"""Append-only Work contract revision: PROMOTES one complete durable
	thread message as the effective contract (pinned ruling). Only the
	EXACT CURRENT CLAIMANT of OPEN Work commits it, and they must still
	be eligible through the live Route (W288): route eligibility alone
	let one handler rewrite assigned scope underneath another handler
	who was executing it, defeating the claim's single-executor
	boundary. Unclaimed Work refuses — discussion stays open for
	proposals, and promotion waits for somebody to be accountable for
	it. The promoted message must live in a thread currently carrying
	this open Work's label. The write is
	compare-and-swap on the expected prior revision — a concurrent or
	stale writer refuses whole without consuming a sequence — and every
	decision is rechecked inside the committing transaction. The stored
	content is the message's complete rendered bytes, self-contained:
	no fixed contract fields, no template machinery."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "revise_work",
	                       op_id, {"work": work_id,
	                               "message_seq": message_seq,
	                               "expected_revision": expected_revision,
	                               "rationale": rationale, "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(
			f"{work_id} is {row['status']}; terminal work is immutable "
			f"and continues through follow-up work, never a "
			f"post-terminal revision")
	if message_seq is None or not isinstance(message_seq, int):
		raise WorkError("a revision promotes exactly one durable "
		                "thread message; name it with message=")
	if expected_revision is None or not isinstance(expected_revision, int) \
			or expected_revision < 0:
		raise WorkError("a revision names the expected prior revision "
		                "explicitly (expect=); concurrent and stale "
		                "edits must fail, never overwrite")
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("a revision records its rationale")
	message = store.conn.execute(
		"SELECT seq, thread, author_team, author, body FROM messages "
		"WHERE seq=?", (message_seq,)).fetchone()
	if message is None:
		raise WorkError(f"no thread message {message_seq}")
	if store.conn.execute(
			"SELECT 1 FROM thread_labels WHERE thread=? AND "
			"work=?", (message["thread"], work_id)).fetchone() is None:
		raise WorkError(
			f"message {message_seq} lives in {message['thread']}, "
			f"which does not carry #" + work_id + "; a promoted "
			f"contract keeps the work's own thread provenance")
	current = _current_revision(store.conn, work_id)
	if expected_revision != current:
		raise WorkError(
			f"{work_id} is at revision {current}, not "
			f"{expected_revision}; the edit is stale — re-read and "
			f"retry against the current state")

	payload = {"work": work_id, "revision": expected_revision + 1,
	           "prior": expected_revision,
	           "thread": message["thread"],
	           "message_seq": message_seq, "rationale": rationale}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		live = conn.execute("SELECT status FROM work WHERE id=?",
		                    (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(
				f"{work_id} is {live['status']}; terminal work is "
				f"immutable and never revised")
		# The one revision authority: the LIVE resolved Route handler
		# who is ALSO the exact current claimant — both checked in the
		# lock, snapshot recorded (resolution facts).
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "revise")
		# W288: route eligibility says who MAY claim; it never says who
		# is executing. Deciding this here, under the same lock as the
		# compare-and-swap below, is what makes a claim released or
		# passed mid-revision fail closed rather than racing.
		claim = conn.execute(
			"SELECT handler_team, handler_member FROM work WHERE id=?",
			(work_id,)).fetchone()
		if claim["handler_team"] is None:
			raise WorkError(
				f"revise: {work_id} is unclaimed; the Work contract is "
				f"promoted by the participant executing it — claim it "
				f"first, or keep proposing in the thread")
		if (claim["handler_team"], claim["handler_member"]) != \
				(actor_team, actor):
			raise WorkError(
				f"revise: {work_id} is claimed by "
				f"{claim['handler_team']}.{claim['handler_member']}; "
				f"a route peer may propose in the thread but never "
				f"rewrites assigned scope underneath its executor")
		payload["authorization"]["claimant"] = f"{actor_team}.{actor}"
		if conn.execute(
				"SELECT 1 FROM thread_labels WHERE thread=? "
				"AND work=?",
				(message["thread"], work_id)).fetchone() is None:
			raise WorkError(
				f"message {message_seq} lost its #" + work_id +
				" provenance while this revision was being prepared; "
				f"it lost a concurrent race — retry against the "
				f"current state")
		# CAS, decided under the state that COMMITS: a concurrent
		# promotion that landed first makes this writer stale.
		live_revision = _current_revision(conn, work_id)
		if expected_revision != live_revision:
			raise WorkError(
				f"{work_id} is at revision {live_revision}, not "
				f"{expected_revision}; the edit lost a concurrent "
				f"race — re-read and retry against the current state")
		conn.execute(
			"INSERT INTO revisions (seq, work, revision, prior, "
			"thread, message_seq, actor, rationale, content, "
			"created_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			(seq, work_id, expected_revision + 1, expected_revision,
			 message["thread"], message_seq,
			 f"{actor_team}.{actor}", rationale, message["body"],
			 store.clock()))

	def finish(result):
		result["revision"] = expected_revision + 1
		result["work"] = work_id

	return store._write("revise_work", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    finish=finish, references=refs)


def bind_work(store: Authority, work_id: str, *, actor_team: str,
              actor: str, root: str | None = None,
              path: str | None = None,
              expected_revision: int | None = None,
              rationale: str | None = None,
              git_provenance: str | None = None,
              op_id: str | None = None, refs=()) -> dict:
	"""WS-6: attach or correct a Work's canonical dossier binding —
	append-only, compare-and-swap on the expected prior revision, by the
	LIVE resolved Route handler of OPEN work only (transfer of the Route
	transfers this authority; creation-time binding belongs to
	create_work). Every post-creation change records a non-empty
	rationale. New revisions require a LIVE configured root and the M4
	canonical locator shape; committed history survives root retirement
	and freezes at terminal close. Ordinary lifecycle never calls this;
	correction exists for an erroneous locator or additive provenance."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "bind_work", op_id,
	                       {"work": work_id, "root": root, "path": path,
	                        "expected_revision": expected_revision,
	                        "rationale": rationale,
	                        "git_provenance": git_provenance,
	                        "refs": refs})
	if isinstance(operation, dict):
		return operation
	row = _work(store, work_id)
	if row["status"] != OPEN:
		raise WorkError(
			f"{work_id} is {row['status']}; terminal work freezes its "
			f"binding history — a later problem is explicit follow-up "
			f"work, never a locator rewrite")
	if root is None or path is None:
		raise WorkError("a binding names its root and canonical path "
		                "(root=, path=)")
	from baton_work.config import validate_root_id
	validate_root_id(root, "binding root")
	_validate_binding_path(path)
	if expected_revision is None or \
			not isinstance(expected_revision, int) or \
			expected_revision < 0:
		raise WorkError("a binding change names the expected prior "
		                "revision explicitly (expect=); stale or "
		                "concurrent edits refuse, never overwrite")
	if not isinstance(rationale, str) or not rationale.strip():
		raise WorkError("every post-creation binding change records its "
		                "rationale")
	live = store.conn.execute(
		"SELECT removed FROM roots WHERE root=?", (root,)).fetchone()
	if live is None or live["removed"]:
		raise WorkError(f"root {root!r} is not a live configured root; "
		                f"a new binding lands on the accepted catalog")
	current = store.conn.execute(
		"SELECT COALESCE(MAX(revision), 0) AS top FROM bindings "
		"WHERE work=?", (work_id,)).fetchone()["top"]
	if expected_revision != current:
		raise WorkError(
			f"{work_id}'s binding is at revision {current}, not "
			f"{expected_revision}; the change is stale — re-read and "
			f"retry against the current state")

	payload = {"work": work_id, "revision": expected_revision + 1,
	           "prior": expected_revision, "root": root, "path": path,
	           "git_provenance": git_provenance, "rationale": rationale}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		live_work = conn.execute("SELECT status FROM work WHERE id=?",
		                         (work_id,)).fetchone()
		if live_work["status"] != OPEN:
			raise WorkError(
				f"{work_id} is {live_work['status']}; terminal work "
				f"freezes its binding history")
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "bind")
		live_root = conn.execute(
			"SELECT removed FROM roots WHERE root=?", (root,)).fetchone()
		if live_root is None or live_root["removed"]:
			raise WorkError(
				f"root {root!r} is not a live configured root; a new "
				f"binding lands on the accepted catalog")
		live_revision = conn.execute(
			"SELECT COALESCE(MAX(revision), 0) AS top FROM bindings "
			"WHERE work=?", (work_id,)).fetchone()["top"]
		if expected_revision != live_revision:
			raise WorkError(
				f"{work_id}'s binding is at revision {live_revision}, "
				f"not {expected_revision}; the change lost a concurrent "
				f"race — re-read and retry against the current state")
		conn.execute(
			"INSERT INTO bindings (work, revision, prior, root, path, "
			"git_provenance, actor, rationale, seq, created_ts) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			(work_id, expected_revision + 1, expected_revision, root,
			 path, git_provenance, f"{actor_team}.{actor}", rationale,
			 seq, store.clock()))

	def finish(result):
		result["work"] = work_id
		result["revision"] = expected_revision + 1

	return store._write("bind_work", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


# -- W5: the conversational poke ---------------------------------------------
#
# An operator (or any participant) sees an apparently idle or stalled
# agent and needs to ask the live session what is happening. The three
# verbs below are OPERATIONAL CONVERSATION and carry no workflow
# authority whatsoever: nothing here claims, releases, passes,
# reprioritizes, re-phases, blocks, closes, or makes any Work
# actionable, and no code path below writes to `work`, `obligations`,
# `edges`, `messages` or `threads`. Creating a Work dependency or a
# directed obligation merely to wake an agent falsifies the coordination
# record, which is the defect this primitive removes.

# The friendly default. The wording is deliberately ordinary: a poke is
# a lightweight request for status between collaborators, never an
# alarm, escalation, accusation or automated health verdict, and the
# text an agent actually receives must not imply otherwise.
DEFAULT_POKE_REQUEST = "what's up?"

# The agent's own answer about itself.
POKE_STATES = ("idle", "working", "waiting", "needs-help")
# Layer 1 — runner/provider diagnostics, capability-based. `unknown` is
# a first-class member of each vocabulary, not a fallback: an adapter
# that cannot observe a fact says so rather than guessing, and a reader
# can tell "the runner reports authentication is fine" apart from "the
# runner cannot see authentication at all".
POKE_SESSION_STATES = ("unknown", "live", "starting", "stopped", "failed")
POKE_AUTH_STATES = ("unknown", "ok", "expired", "failed")
POKE_LIMIT_STATES = ("unknown", "ok", "rate-limited", "overloaded")


def _participant_pair(value, what: str) -> tuple[str, str]:
	team, dot, member = str(value).partition(".")
	if not dot or not team or not member:
		raise WorkError(f"{what} {value!r} is not team.member shaped; a "
		                f"poke names exactly one configured participant, "
		                f"never a route or a wildcard")
	return team, member


def _poke_text(value, what: str, default: str | None = None) -> str:
	if value is None:
		if default is None:
			raise WorkError(f"{what} is required")
		return default
	if not isinstance(value, str) or not value.strip():
		raise WorkError(f"{what} must be a non-empty string")
	if "\0" in value:
		raise WorkError(f"{what} must not contain a NUL")
	return value


def _poke_choice(value, allowed, what: str) -> str:
	if value is None:
		return allowed[0]
	if value not in allowed:
		raise WorkError(f"{what} {value!r} is not one of "
		                f"{', '.join(allowed)}")
	return value


def _poke_count(value, what: str):
	"""An advisory telemetry scalar: a non-negative integer, or None
	meaning UNKNOWN. Never a zero standing in for a fact nobody has."""
	if value is None:
		return None
	if not isinstance(value, int) or isinstance(value, bool) or value < 0:
		raise WorkError(f"{what} must be a non-negative integer, or be "
		                f"omitted entirely to report it as unknown")
	return value


def _live_poke(store: Authority, conn, poke_seq, now: str):
	"""The poke row, refusing every state that is already terminal —
	including the DERIVED one.

	Expiry is not a stored status and nothing is watching the clock, so
	`pending` in the row and `pending` in fact are different questions.
	A poke past its `expires_at` reads as `timed-out` everywhere, and
	the ruling is that a timed-out poke can never later be answered; if
	that check lived only in the read path, an answer arriving after the
	deadline would quietly resurrect it."""
	row = conn.execute(
		"SELECT * FROM pokes WHERE seq=?", (poke_seq,)).fetchone()
	if row is None:
		raise WorkError(f"poke {poke_seq} does not exist")
	if row["status"] != "pending":
		raise WorkError(f"poke {poke_seq} is already {row['status']}; a "
		                f"poke is answered, cancelled or superseded once "
		                f"and its record is not rewritten")
	if row["expires_at"] is not None and row["expires_at"] <= now:
		raise WorkError(
			f"poke {poke_seq} timed out at {row['expires_at']} (now "
			f"{now}); a timed-out poke is terminal and cannot be "
			f"answered or cancelled")
	return row


def poke(store: Authority, *, actor_team: str, actor: str, target: str,
         request: str | None = None, expires_at: str | None = None,
         op_id: str | None = None, refs=()) -> dict:
	"""Ask exactly one configured participant what is going on.

	AUTHORIZATION is deliberately open: any configured participant may
	poke any other, including ITSELF. Poke carries no workflow
	authority, so the route-eligibility gate that protects mutations has
	nothing to protect here — and requiring a capability would make the
	friendly question harder to ask than the acts that actually change
	state, which inverts the risk. The record names the asker, so misuse
	is visible rather than prevented by refusal. Self-poke is the
	end-to-end diagnostic "does my own wake-up bus work?" and exercises
	the same persistent path another asker would use.

	DEDUPLICATION keeps the NEWEST pending poke per (asker, target).
	A deliberate re-ask supersedes that asker's earlier pending poke:
	only the newer one stays actionable, its text is the current
	question, and its optional `expires_at` starts the new wait window.
	This is what a rate limit is actually for here — one asker cannot
	pile up pokes — achieved without measuring time or adding the
	authority's first background timer. The superseded row remains
	operational history and is never rewritten or deleted. Different
	askers keep their own independent pending pokes to one target,
	because they are different people asking.

	An exact `op-id` retry replays its committed result and therefore
	does NOT renew expiry: a retry is the same question, not a new one.
	"""
	_member(store, actor_team, actor)
	target_team, target_member = _participant_pair(target, "poke target")
	_member(store, target_team, target_member)
	request = _poke_text(request, "poke request", DEFAULT_POKE_REQUEST)
	if expires_at is not None:
		_canonical_instant(expires_at, "expires_at")
		if expires_at <= store.clock():
			raise WorkError(
				f"expires_at {expires_at!r} is not later than now "
				f"({store.clock()}); a poke that has already timed out "
				f"would never be delivered")
	operation = _operation(store, actor_team, actor, "poke", op_id,
	                       {"target": f"{target_team}.{target_member}",
	                        "request": request,
	                        "expires_at": expires_at, "refs": refs})
	if isinstance(operation, dict):
		return operation
	refs = _parse_refs(store, refs)
	asker = f"{actor_team}.{actor}"
	payload = {"asker": asker,
	           "target": f"{target_team}.{target_member}",
	           "request": request, "expires_at": expires_at}
	superseded: list = []

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		_member_active(conn, target_team, target_member)
		now = store.clock()
		# Only rows that are pending IN FACT are superseded. One already
		# past its deadline reads as `timed-out`, and overwriting that
		# derived terminal state with `superseded` would rewrite history
		# the operator has already been shown.
		for row in conn.execute(
				"SELECT seq FROM pokes WHERE status='pending' AND "
				"asker_team=? AND asker=? AND target_team=? AND "
				"target=? AND (expires_at IS NULL OR expires_at > ?) "
				"ORDER BY seq",
				(actor_team, actor, target_team, target_member, now)):
			superseded.append(row["seq"])
		if superseded:
			conn.executemany(
				"UPDATE pokes SET status='superseded', resolved_seq=?, "
				"resolved_ts=? WHERE seq=?",
				[(seq, now, older) for older in superseded])
		conn.execute(
			"INSERT INTO pokes (seq, asker_team, asker, target_team, "
			"target, request, expires_at, status, created_ts) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
			(seq, actor_team, actor, target_team, target_member,
			 request, expires_at, now))

	def finish(result):
		result["poke"] = result["seq"]
		result["target"] = f"{target_team}.{target_member}"
		result["superseded"] = list(superseded)

	return store._write("poke", asker, payload, mutate,
	                    operation=operation, finish=finish,
	                    references=refs)


def answer_poke(store: Authority, poke_seq: int, *, actor_team: str,
                actor: str, state: str, explanation: str, work=(),
                provider: str | None = None, model: str | None = None,
                session_state: str | None = None,
                auth_state: str | None = None,
                limit_state: str | None = None,
                retry_at: str | None = None,
                context_limit=None, context_used=None,
                context_remaining=None,
                op_id: str | None = None, refs=()) -> dict:
	"""The one terminal response, from the EXACT participant that was
	asked.

	Two independently observable layers land here together. The
	runner/provider diagnostics can explain why the model itself could
	not answer — a provider rate limiter, an expired credential, a dead
	session — and the agent status is what the model said when it could.
	Both are capability-based and advisory: what an adapter cannot
	observe stays the explicit `unknown` member of its vocabulary, or
	is omitted and stored NULL. Nothing is guessed and nothing opaque is
	accepted, so no credential or unrestricted vendor payload has a
	column to arrive in.

	`work` is what the AGENT believes it is handling. It is recorded as
	the agent's claim, and the projection reports canonical Work state
	beside it rather than instead of it — a disagreement between the two
	is the single most useful thing a poke can surface, and collapsing
	them would hide exactly the case the operator poked to find. Naming
	a Work that does not exist is a malformed answer and refuses; naming
	one somebody else holds is a disagreement and is recorded.

	This verb mutates no Work of any kind. Answering never claims,
	releases, or makes anything actionable — an agent that discovers
	actionable Work while answering reports the discovery and then acts
	on it through the ordinary protocol, under the ordinary
	eligibility, gate, and compare-and-swap checks."""
	_member(store, actor_team, actor)
	if not isinstance(poke_seq, int) or isinstance(poke_seq, bool) or \
			poke_seq < 1:
		raise WorkError("a poke is answered by its positive sequence")
	state = _poke_text(state, "poke state")
	if state not in POKE_STATES:
		raise WorkError(f"poke state {state!r} is not one of "
		                f"{', '.join(POKE_STATES)}")
	explanation = _poke_text(explanation, "poke explanation")
	provider = _poke_text(provider, "provider", "unknown")
	model = _poke_text(model, "model", "unknown")
	session_state = _poke_choice(session_state, POKE_SESSION_STATES,
	                             "session_state")
	auth_state = _poke_choice(auth_state, POKE_AUTH_STATES, "auth_state")
	limit_state = _poke_choice(limit_state, POKE_LIMIT_STATES,
	                           "limit_state")
	if retry_at is not None:
		_canonical_instant(retry_at, "retry_at")
	context_limit = _poke_count(context_limit, "context_limit")
	context_used = _poke_count(context_used, "context_used")
	context_remaining = _poke_count(context_remaining, "context_remaining")
	named = []
	for entry in work or ():
		work_id = _poke_text(entry, "answered work id")
		if work_id in named:
			raise WorkError(f"answered work {work_id} is named twice; a "
			                f"claim is a set, not a tally")
		_work(store, work_id)
		named.append(work_id)
	operation = _operation(store, actor_team, actor, "answer_poke", op_id,
	                       {"poke": poke_seq, "state": state,
	                        "explanation": explanation, "work": named,
	                        "provider": provider, "model": model,
	                        "session_state": session_state,
	                        "auth_state": auth_state,
	                        "limit_state": limit_state,
	                        "retry_at": retry_at,
	                        "context_limit": context_limit,
	                        "context_used": context_used,
	                        "context_remaining": context_remaining,
	                        "refs": refs})
	if isinstance(operation, dict):
		return operation
	refs = _parse_refs(store, refs)
	answerer = f"{actor_team}.{actor}"
	now = store.clock()
	row = _live_poke(store, store.conn, poke_seq, now)
	if (row["target_team"], row["target"]) != (actor_team, actor):
		raise WorkError(
			f"poke {poke_seq} asked "
			f"{row['target_team']}.{row['target']}, not {answerer}; "
			f"only the exact participant that was asked answers")
	payload = {"poke": poke_seq, "answerer": answerer, "state": state,
	           "work": named}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		now_in_lock = store.clock()
		live = _live_poke(store, conn, poke_seq, now_in_lock)
		if (live["target_team"], live["target"]) != (actor_team, actor):
			raise WorkError(
				f"poke {poke_seq} is no longer addressed to {answerer}")
		conn.execute(
			"INSERT INTO poke_answers (poke, seq, state, explanation, "
			"provider, model, session_state, auth_state, limit_state, "
			"retry_at, context_limit, context_used, context_remaining, "
			"created_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
			"?, ?)",
			(poke_seq, seq, state, explanation, provider, model,
			 session_state, auth_state, limit_state, retry_at,
			 context_limit, context_used, context_remaining,
			 now_in_lock))
		for ordinal, work_id in enumerate(named, start=1):
			conn.execute(
				"INSERT INTO poke_answer_work (poke, ordinal, work) "
				"VALUES (?, ?, ?)", (poke_seq, ordinal, work_id))
		conn.execute(
			"UPDATE pokes SET status='answered', resolved_seq=?, "
			"resolved_ts=? WHERE seq=?",
			(seq, now_in_lock, poke_seq))

	def finish(result):
		result["poke"] = poke_seq
		result["state"] = state

	return store._write("poke_answer", answerer, payload, mutate,
	                    operation=operation, finish=finish,
	                    references=refs)


def cancel_poke(store: Authority, poke_seq: int, *, actor_team: str,
                actor: str, reason: str | None = None,
                op_id: str | None = None, refs=()) -> dict:
	"""Withdraw an unanswered poke.

	The ASKER owns the question and may take it back; a holder of the
	`config` capability may clear one aimed at a participant that will
	never return. Both are recorded with the actor and the reason, so
	"why did this poke vanish" stays answerable. Cancelling an
	already-terminal poke — answered, cancelled, superseded, or timed
	out — refuses by name rather than rewriting history."""
	_member(store, actor_team, actor)
	if not isinstance(poke_seq, int) or isinstance(poke_seq, bool) or \
			poke_seq < 1:
		raise WorkError("a poke is cancelled by its positive sequence")
	if reason is not None:
		reason = _poke_text(reason, "cancellation reason")
	operation = _operation(store, actor_team, actor, "cancel_poke", op_id,
	                       {"poke": poke_seq, "reason": reason,
	                        "refs": refs})
	if isinstance(operation, dict):
		return operation
	refs = _parse_refs(store, refs)
	canceller = f"{actor_team}.{actor}"
	row = _live_poke(store, store.conn, poke_seq, store.clock())
	authorized = (row["asker_team"], row["asker"]) == (actor_team, actor)
	if not authorized:
		authorized = store.conn.execute(
			"SELECT 1 FROM member_capabilities WHERE team=? AND "
			"member=? AND capability='config'",
			(actor_team, actor)).fetchone() is not None
	if not authorized:
		raise WorkError(
			f"poke {poke_seq} was asked by "
			f"{row['asker_team']}.{row['asker']}; only that asker or a "
			f"holder of the config capability withdraws it")
	payload = {"poke": poke_seq, "canceller": canceller, "reason": reason}

	def mutate(conn, seq):
		_member_active(conn, actor_team, actor)
		now = store.clock()
		live = _live_poke(store, conn, poke_seq, now)
		if (live["asker_team"], live["asker"]) != (actor_team, actor) \
				and conn.execute(
					"SELECT 1 FROM member_capabilities WHERE team=? AND "
					"member=? AND capability='config'",
					(actor_team, actor)).fetchone() is None:
			raise WorkError(
				f"poke {poke_seq} is not {canceller}'s to withdraw")
		conn.execute(
			"UPDATE pokes SET status='cancelled', resolved_seq=?, "
			"resolved_ts=? WHERE seq=?", (seq, now, poke_seq))

	def finish(result):
		result["poke"] = poke_seq

	return store._write("poke_cancel", canceller, payload, mutate,
	                    operation=operation, finish=finish,
	                    references=refs)
