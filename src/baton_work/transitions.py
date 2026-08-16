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
STAGE_PHASES = {"rsrch": "research", "research": "research",
                "impl": "active", "implementation": "active",
                "rview": "review", "review": "review"}

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
OUTCOMES = ("satisfying", "non-satisfying", "rejected", "cancelled")
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
			_touch_work(conn, row["id"])
			_emit(conn, "wake", actor,
			      {"work": row["id"], "from": "waiting", "to": "queued",
			       "condition": {"type": row["wait_type"],
			                     "obligation": row["wait_obligation"]}})


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
		if ready == 0:
			# finding-active-work-claim R3: a late-arriving gate keeps
			# the honest work stage but INVALIDATES execution — the
			# claimant is released atomically, and the causing event's
			# payload keeps the released claimant as recoverable
			# evidence.
			live = conn.execute(
				"SELECT active_team, active_member FROM work WHERE id=?",
				(work_id,)).fetchone()
			if live["active_team"] is not None:
				if payload is not None:
					payload.setdefault("released_claims", []).append(
						{"work": work_id,
						 "claimant": f"{live['active_team']}."
						             f"{live['active_member']}"})
				conn.execute(
					"UPDATE work SET active_team=NULL, "
					"active_member=NULL WHERE id=?", (work_id,))
		_touch_work(conn, work_id)





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

_BINDING_PATH = _ws6_re.compile(
	r"^work/records/[0-9]{4}/(0[1-9]|1[0-2])/"
	r"[A-Za-z0-9][A-Za-z0-9._-]*$")
_WORK_ID = _ws6_re.compile(r"^[0-9a-f]{8}-W[0-9]+$")


def _validate_binding_path(path: str) -> str:
	"""M4: the canonical permanent-record locator is exactly
	`work/records/YYYY/MM/<stable-record>` — literal prefix, four-digit
	year, month 01-12, ONE safe record component. Validation is pure
	syntax; nothing is probed."""
	_validate_ref_path(path, "binding")
	if not _BINDING_PATH.match(path):
		raise WorkError(
			f"binding path {path!r} is not the canonical permanent "
			f"record shape work/records/YYYY/MM/<stable-record>")
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
                op_id: str | None = None, refs=()) -> dict:
	"""A Work and its first message, atomically — creation must be cheap or
	mandatory Work scope becomes authoring ceremony (confirmed behavior).

	`author` is `member` within `team`. The new Work's `Current` is
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
	# creation. The current handler may reclassify later; activation
	# never requires a redundant classify step.
	if classification is None or classification == "unknown":
		raise WorkError(
			"work creation requires a concrete classification; "
			"'unknown' (or omitting it) refuses — choose one of "
			f"{tuple(c for c in CLASSIFICATIONS if c != 'unknown')}; "
			"the current handler may reclassify later")
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
			"follow_up_of, created_seq, last_change_seq, last_changed_at) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)",
			(work_id, team, title, origin, classification, phase, OPEN,
			 parent, team, kind, follow_up_of, seq, seq, clock_ms_now()))
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
	evidence becomes follow-up Work). No current and no next endpoint
	afterwards, and the ancestor gate recomputes: closure rolls UP through
	recomputation, never down through force. Every terminal close names
	exactly one of `satisfying`, `non-satisfying`, `rejected`, or
	`cancelled` and records a non-empty rationale — terminal decisions
	are durable review evidence, never reconstructed from thread
	prose. Cancellation is ordinary accelerated close under the same
	Current-only authority: no cascade, no child bypass. A duplicate is a
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
	           "was_current_team": row["current_team"],
	           "was_current_kind": row["current_kind"]}

	def mutate(conn, seq):
		# WF-09 race 2: status and children rechecked inside the lock — a
		# competing close or late create can commit between the optimistic
		# checks above and this transaction.
		live = conn.execute(
			"SELECT status, parent, classification, current_team, "
			"current_kind FROM work WHERE id=?", (work_id,)).fetchone()
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
				"basis": rationale,
			}
		conn.execute(
			"UPDATE rounds SET status='closed', ended_seq=? "
			"WHERE work=? AND status='open'", (seq, work_id))
		conn.execute(
			"UPDATE work SET status=?, ready=0, outcome=?, rationale=?, "
			"duplicate_of=?, "
			"current_team=NULL, current_kind=NULL, next_team=NULL, "
			"next_kind=NULL, active_team=NULL, active_member=NULL, "
			"closed_seq=? WHERE id=?",
			(CLOSED, outcome, rationale, duplicate_of, seq, work_id))
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
		# WS-1: this close may have shut the LAST gate some waiting work
		# recorded — the wake commits atomically with it, or not at all.
		_sweep_wakes(conn, f"{actor_team}.{actor}")

	return store._write("close_work", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    references=refs)


# -- finding-active-work-claim: the atomic phase-orthogonal claim ------------

def claim_work(store: Authority, work_id: str, *, actor_team: str,
               actor: str, op_id: str | None = None, refs=()) -> dict:
	"""THE atomic active-work claim: records WHO is executing without
	touching phase (orthogonal ruling). One eligible handler of the live
	Current endpoint acquires open, ready, non-waiting/non-parked Work —
	every condition rechecked inside the write transaction, so an earlier
	`ready` observation is advisory and a competing claim fails closed
	naming the recorded claimant. Release happens only through the ruled
	transitions (pass, entering waiting/parked, terminal close)."""
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
			"SELECT status, phase, active_team, active_member "
			"FROM work WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; terminal "
			                f"work cannot be claimed")
		if live["phase"] in ("waiting", "parked"):
			raise WorkError(f"{work_id} is {live['phase']}; waiting and "
			                f"parked work cannot be claimed")
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "claim")
		gates = _open_gates(conn, work_id)
		if gates:
			raise WorkError(
				f"{work_id} has {gates} unmet dependency/child gate(s); "
				f"blocked work cannot be claimed — readiness is decided "
				f"here, in the write transaction")
		if live["active_team"] is not None:
			raise WorkError(
				f"{work_id} is already claimed by "
				f"{live['active_team']}.{live['active_member']}; "
				f"conflicting claim attempts fail closed (an exact "
				f"retry replays through its operation id)")
		payload["claimant"] = f"{actor_team}.{actor}"
		conn.execute(
			"UPDATE work SET active_team=?, active_member=? WHERE id=?",
			(actor_team, actor, work_id))
		_touch_work(conn, work_id)

	def finish(result):
		# The committed claimant rides the replayable result — an agent
		# retrying reads WHO holds the claim without a second call.
		result["claimant"] = payload["claimant"]

	return store._write("claim", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


def release_claim(store: Authority, work_id: str, *, actor_team: str,
                  actor: str, expect: str, reason: str,
                  op_id: str | None = None, refs=()) -> dict:
	"""Explicit claimant recovery (ruled): one honest operation for
	self-release AND forced recovery. Authority is the live Current
	endpoint's resolved handlers; --expect is a mandatory compare-and-swap
	against the exact recorded claimant, decided inside the write
	transaction; --reason is durable evidence. A successful release clears
	ONLY the claimant — phase, Current, Next, readiness, dependencies,
	waiting and discussion state are untouched."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	if not isinstance(reason, str) or not reason.strip():
		raise WorkError("a release records its non-empty durable reason — "
		                "self-release and forced recovery both explain "
		                "why the work became unclaimed")
	reason = reason.strip()
	if not isinstance(expect, str) or expect.count(".") != 1 or \
			not all(expect.split(".")):
		raise WorkError(f"--expect {expect!r} is not team.member shaped; "
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
			"SELECT status, active_team, active_member FROM work "
			"WHERE id=?", (work_id,)).fetchone()
		if live["status"] != OPEN:
			raise WorkError(f"{work_id} is {live['status']}; terminal "
			                f"work carries no claim to release")
		payload["resolution"] = _handler_gate(conn, work_id, actor_team,
		                                      actor, "release")
		if live["active_team"] is None:
			raise WorkError(f"{work_id} is unclaimed; there is no "
			                f"execution claim to release")
		recorded = f"{live['active_team']}.{live['active_member']}"
		if recorded != expect:
			raise WorkError(
				f"{work_id} is claimed by {recorded}, not {expect}; "
				f"the compare-and-swap refuses — recovery never "
				f"guesses whose execution it is interrupting")
		payload["released_claimant"] = recorded
		conn.execute(
			"UPDATE work SET active_team=NULL, active_member=NULL "
			"WHERE id=?", (work_id,))
		_touch_work(conn, work_id)

	def finish(result):
		result["released_claimant"] = payload["released_claimant"]

	return store._write("release", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation, finish=finish,
	                    references=refs)


# -- WS-1: public classification and operational phase -----------------------

def classify(store: Authority, work_id: str, *, actor_team: str, actor: str,
             classification: str, op_id: str | None = None, refs=()) -> dict:
	"""An explicit, audited classification change by a currently resolved
	handler of the Work's Current route. Canonical values only — compact
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
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "set_phase", op_id,
	                       {"work": work_id, "phase": phase,
	                        "reason": reason, "wait": wait, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
		# finding-active-work-claim ("orthogonal" ruling): phase answers
		# WHAT stage is happening; the claimant answers WHO executes.
		# Ordinary phase changes never touch the claim — but ENTERING
		# waiting or parked is a ruled release.
		if phase in ("waiting", "parked"):
			live_claim = conn.execute(
				"SELECT active_team, active_member FROM work WHERE id=?",
				(work_id,)).fetchone()
			if live_claim["active_team"] is not None:
				payload["released_claimant"] = (
					f"{live_claim['active_team']}."
					f"{live_claim['active_member']}")
				conn.execute(
					"UPDATE work SET active_team=NULL, "
					"active_member=NULL WHERE id=?", (work_id,))
		conn.execute(
			"UPDATE work SET phase=?, wait_type=?, wait_obligation=? "
			"WHERE id=?", (phase, wait_type, wait_obligation, work_id))
		_touch_work(conn, work_id)

	return store._write("set_phase", f"{actor_team}.{actor}", payload,
	                    mutate, operation=operation,
	                    references=refs)


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
                 review_at: str | None = None,
                 op_id: str | None = None, refs=()) -> dict:
	"""One verification round for one EXACT candidate, with an exact
	selected set of verifier routes (each an @ verification obligation —
	actionable for testing WITHOUT clearing anyone's dependency, granting
	no mutation authority, and never a wake condition).

	Publishing a different candidate is a NEW round: any open round is
	superseded and its pending assignments are withdrawn with route
	notification — replies stay pinned to the exact candidate they tested
	and never carry forward silently."""
	_member(store, actor_team, actor)
	if isinstance(assign, str):
		assign = [assign]
	assign = list(assign or [])
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "create_round",
	                       op_id, {"work": work_id,
	                               "candidate": candidate,
	                               "assign": assign,
	                               "review_at": review_at, "refs": refs})
	if isinstance(operation, dict):
		return operation
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

	def finish(result):
		result["round"] = mutate.round_number
		result["assignments"] = [entry["obligation"]
		                         for entry in payload["assignments"]]

	return store._write("create_round", f"{actor_team}.{actor}",
	                    payload, mutate, operation=operation,
	                    finish=finish, references=refs)


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
           observation: str, evidence: str,
           op_id: str | None = None, refs=()) -> dict:
	"""The verifier's IMMUTABLE raw observation: exactly passed, failed, or
	unable, with evidence, pinned to its assignment/round/candidate. It
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


def abandon_round(store: Authority, work_id: str, round_number: int, *,
                  actor_team: str, actor: str, reason: str,
                  op_id: str | None = None, refs=()) -> dict:
	"""End a round WITHOUT closing the work: pending assignments are
	withdrawn with route notification, candidate and report history stay
	immutable, and no provider or consumer lifecycle state changes."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "abandon_round",
	                       op_id, {"work": work_id, "round": round_number,
	                               "reason": reason, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
	                    payload, mutate, operation=operation,
	                    references=refs)


def extend_round(store: Authority, work_id: str, round_number: int, *,
                 actor_team: str, actor: str, review_at: str,
                 op_id: str | None = None, refs=()) -> dict:
	"""Extend the SAME candidate's testing window: an explicit audited
	reviewer decision — never a hidden timer reset. All reports and pending
	assignments are retained; the deadline generation advances so due-ness
	is per-generation; repeated extensions are visible history. May also
	give a deadline to a round created without one."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "extend_round",
	                       op_id, {"work": work_id, "round": round_number,
	                               "review_at": review_at, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
                   actor_team: str, actor: str,
                   op_id: str | None = None, refs=()) -> dict:
	"""`work_id` blocked_by `blocker_id` — the ONLY thing that gates
	readiness across records (labels are inert, by clarification). Cross-team
	on purpose; that is the convergence model."""
	_member(store, actor_team, actor)
	refs = _parse_refs(store, refs)
	operation = _operation(store, actor_team, actor, "add_dependency",
	                       op_id, {"work": work_id, "on": blocker_id, "refs": refs})
	if isinstance(operation, dict):
		return operation
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
		_recompute_ready(conn, work_id, payload)

	return store._write("add_dependency", f"{actor_team}.{actor}",
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
		_sweep_wakes(conn, f"{team}.{member}")

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
		_sweep_wakes(conn, f"{team}.{member}")

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
	this one narrow atomic authority over the requesting Work. `--into`
	adds same-team + open checks on the provider Work; its Current is
	recorded as evidence, not a second gate. `--create --parent` alone
	adds the separate live parent-Current handler gate.
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
				"current_kind, ready, created_seq, last_change_seq, "
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
		_sweep_wakes(conn, f"{actor_team}.{actor}")
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
	carrying operator acts against. An explicit `--on` must name a
	current label (the thread carries its operating context) and that
	Work must itself be open and authorized. An omitted `--on` resolves
	only when exactly ONE label is eligible for this operation — zero or
	several refuse. Returns (work_id, authorization_snapshot)."""
	labels = [row["work"] for row in conn.execute(
		"SELECT work FROM thread_labels WHERE thread=? "
		"ORDER BY added_seq, work", (thread_id,))]
	if on is not None:
		if on not in labels:
			raise WorkError(
				f"--on {on} is not among {thread_id}'s current "
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
			f"{operation} with no --on resolves only when exactly one "
			f"labelled work is eligible; {thread_id} has "
			f"{len(eligible)} — select the target with --on")
	return eligible[0]


def post_thread(store: Authority, thread_id: str, *,
                    author_team: str, author: str, body: str,
                    include=(), request: str | None = None,
                    pass_to: str | None = None,
                    pass_phase: str | None = None,
                    set_next: str | None = None,
                    on: str | None = None,
                    op_id: str | None = None, refs=()) -> dict:
	"""THE public posting surface (Slice B): one message into one
	thread, optionally carrying this operation's tags.

	`+` (include) stays the ONLY fan-out: expanded against live
	endpoints, the exact expansion recorded with the publication, each
	reached team joining monotonic participation once — and no
	obligation, Current, Next, readiness, phase, edge, or Work authority
	changes. `@` (request) and `=>` (pass, optionally planting a planned
	Next) affect exactly one currently labelled, eligible open Work:
	`--on` selects it; omitted, it resolves only at eligible-cardinality
	one, and the resolution is recorded and echoed. A plain message
	requires live context — at least one labelled open Work — rechecked
	inside the committing transaction."""
	_member(store, author_team, author)
	if isinstance(include, str):
		include = [part for part in include.split(",") if part]
	include = list(include or [])
	refs = _parse_refs(store, refs)
	protected = _operation(store, author_team, author, "post", op_id,
	                       {"thread": thread_id, "body": body,
	                        "include": include, "request": request,
	                        "pass_to": pass_to,
	                        # W108 R1: the destination phase is typed
	                        # semantic input — a retry with a DIFFERENT
	                        # phase is a different operation and must
	                        # refuse, never replay the first choice.
	                        "pass_phase": pass_phase,
	                        "set_next": set_next,
	                        "on": on, "refs": refs})
	if isinstance(protected, dict):
		return protected
	_thread(store, thread_id)
	if not isinstance(body, str) or not body:
		raise WorkError("a message body must be non-empty")
	if request is not None and pass_to is not None:
		raise WorkError("one message carries one operation: @ requests a "
		                "response, => passes the baton; asking both at "
		                "once makes the obligation ambiguous")
	if set_next is not None and pass_to is None:
		raise WorkError("a planned Next is set by a pass; there is "
		                "nothing to return from otherwise")
	carrying = request is not None or pass_to is not None
	if on is not None and not carrying:
		raise WorkError("--on selects the work a carrying operator acts "
		                "against; this message carries none")
	if include:
		# Optimistic early refusal only; the recorded expansion is redone
		# inside the write transaction (C4 review R1).
		_expand_include(store, include)
	requested = _one_endpoint(store, request, "@ request") \
		if request else None
	passed = _one_endpoint(store, pass_to, "=> pass") if pass_to else None
	# finding-active-work-claim ("Current and phase move together"): a
	# pass atomically records the DESTINATION phase. Explicit values are
	# the honest source; waiting/parked stay explicit handler decisions
	# and are never a pass destination.
	if pass_phase is not None:
		if pass_to is None:
			raise WorkError("a destination phase rides a pass; there is "
			                "no pass here")
		if pass_phase not in ("queued", "research", "active", "review"):
			raise WorkError(
				f"destination phase {pass_phase!r} is not one of "
				f"('queued', 'research', 'active', 'review'); waiting "
				f"and parked are explicit handler decisions with their "
				f"ruled conditions, never a pass destination")
	planned = _one_endpoint(store, set_next, "planned Next") \
		if set_next else None
	operation = "@ request" if request is not None else "=> pass"

	event_kind = "post_message"
	consumes_next = False
	selected = None
	if carrying:
		# Optimistic selection — decides the event kind; the selection
		# that COMMITS is re-derived in-lock and must agree.
		selected, _authorization = _select_target(
			store.conn, thread_id, author_team, author, operation, on)
		if passed is not None:
			row = _work(store, selected)
			if (row["current_team"], row["current_kind"]) == passed:
				raise WorkError(f"{selected} is already at "
				                f"{passed[0]}.{passed[1]}; a pass moves "
				                f"the baton")
			if (row["next_team"], row["next_kind"]) == passed:
				event_kind, consumes_next = "return", True
			else:
				event_kind = "pass"
		else:
			event_kind = "request"
	elif not _live_context(store.conn, thread_id):
		raise WorkError(
			f"{thread_id} has no labelled open work; closed context "
			f"is readable history — create or label open follow-up work "
			f"to continue (live-context ruling)")

	payload = {"thread": thread_id,
	           "body_bytes": len(body.encode("utf-8")),
	           "include": [], "request": request, "pass": pass_to,
	           "set_next": set_next, "on": on,
	           "consumed_next": consumes_next}

	def mutate(conn, seq):
		_member_active(conn, author_team, author)
		if carrying:
			# The committing selection: still labelled, open, authorized —
			# and when --on was omitted, STILL exactly one eligible work
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
			if passed is not None:
				live = conn.execute(
					"SELECT current_team, current_kind, next_team, "
					"next_kind FROM work WHERE id=?",
					(work_id,)).fetchone()
				if (live["current_team"], live["current_kind"]) == passed:
					raise WorkError(f"{work_id} is already at "
					                f"{passed[0]}.{passed[1]}; a pass "
					                f"moves the baton")
				if (((live["next_team"], live["next_kind"]) == passed)
						!= consumes_next):
					raise WorkError(
						f"{work_id}'s planned Next changed while this "
						f"pass was being prepared; it lost a concurrent "
						f"race — retry against the current state")
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
		if passed is not None:
			work_id = payload["work"]
			payload["pass_resolution"] = resolve_endpoint(
				conn, passed[0], passed[1], "=> pass")
			if planned is not None:
				payload["next_resolution"] = resolve_endpoint(
					conn, planned[0], planned[1], "planned Next")
			if consumes_next:
				# The consumed plan clears — but a NEW plan stated on
				# this same return commits with it (discovered at the
				# W108 trial handoff: the old code silently dropped a
				# planted --set-next on a consuming return).
				conn.execute(
					"UPDATE work SET current_team=?, current_kind=?, "
					"next_team=?, next_kind=? WHERE id=?",
					(passed[0], passed[1],
					 planned[0] if planned else None,
					 planned[1] if planned else None, work_id))
			else:
				# An unconsumed planned Next stays VISIBLY set unless
				# this pass plants a new one — never silently cleared.
				conn.execute(
					"UPDATE work SET current_team=?, current_kind=?, "
					"next_team=COALESCE(?, next_team), "
					"next_kind=COALESCE(?, next_kind) WHERE id=?",
					(passed[0], passed[1],
					 planned[0] if planned else None,
					 planned[1] if planned else None, work_id))
			# finding-active-work-claim ("Current and phase move
			# together"): the pass atomically records the destination
			# phase — explicit when stated, derived from the
			# destination route's STAGE role otherwise, refused when
			# neither names a stage. It never carries the sender's
			# phase, never substitutes queued, and never derives
			# waiting from readiness. The sender's claim is released;
			# the recipient claims explicitly.
			if pass_phase is not None:
				destination_phase = pass_phase
			else:
				role = payload["pass_resolution"].get("role")
				destination_phase = STAGE_PHASES.get(role)
				if destination_phase is None:
					raise WorkError(
						f"the destination role {role!r} names no work "
						f"stage; state the destination phase "
						f"explicitly — a pass records the honest "
						f"destination phase, never the sender's and "
						f"never a generic queued")
			payload["destination_phase"] = destination_phase
			conn.execute(
				"UPDATE work SET active_team=NULL, active_member=NULL, "
				"phase=?, wait_type=NULL, wait_obligation=NULL "
				"WHERE id=?", (destination_phase, work_id))
			_touch_work(conn, work_id)
			touched_teams.add(passed[0])
		for team in sorted(touched_teams):
			_join_thread(conn, thread_id, team, seq)

	def finish(result):
		result["included"] = [entry["endpoint"]
		                      for entry in payload["include"]]
		if carrying:
			result["work"] = payload["work"]

	return store._write(event_kind, f"{author_team}.{author}",
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
	thread message as the effective contract (pinned ruling). Only
	the resolved Current handler of OPEN Work commits it; transfer of
	Current transfers this authority. The promoted message must live in
	a thread currently carrying this open Work's label. The write is
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
		                "thread message; name it with --message")
	if expected_revision is None or not isinstance(expected_revision, int) \
			or expected_revision < 0:
		raise WorkError("a revision names the expected prior revision "
		                "explicitly (--expect); concurrent and stale "
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
		# The one revision authority: the LIVE resolved Current handler,
		# in the lock, snapshot recorded (resolution facts).
		payload["authorization"] = _handler_gate(
			conn, work_id, actor_team, actor, "revise")
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
	LIVE resolved Current handler of OPEN work only (transfer of Current
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
		                "(--root, --path)")
	from baton_work.config import validate_root_id
	validate_root_id(root, "binding root")
	_validate_binding_path(path)
	if expected_revision is None or \
			not isinstance(expected_revision, int) or \
			expected_revision < 0:
		raise WorkError("a binding change names the expected prior "
		                "revision explicitly (--expect); stale or "
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
