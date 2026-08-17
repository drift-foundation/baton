"""The v11 Work authority: schema, publication sequence, identity registry.

Gate A step A1. Three properties live here and everything later leans on them:

THE SEQUENCE IS ALLOCATED INSIDE THE WRITE TRANSACTION. Every mutation calls
`_append` within the same `BEGIN IMMEDIATE` that commits its rows, and the
sequence is a persisted counter incremented there — so two committed events can
never share a number, a crash between allocate and commit leaves no gap that a
reader can observe as a row, and a restart continues above everything that ever
committed. This is the total order that pagination, audit and readiness
recomputation stand on; protocol 10's `(created_ts, id)` tie is the defect it
replaces (`work/records/2026/08/finding-same-second-ordering/`).

IDENTITY IS VALIDATED AT REGISTRATION, NEVER AT RENDER. A canonical handle is
at most six terminal display cells (wcwidth semantics, computed here in
stdlib), and the display name is arbitrary. A handle that would lie about its
width — zero-width characters, combining marks, controls — is refused with the
measured cell count, because a width rule enforced at draw time is a rule the
first narrow terminal breaks (ruling: short canonical handles + display
names, 2026-08-14).

READS ARE PURE. Nothing in this module writes outside `_write`; the projection
layer above never calls `_write` at all. The authority's bytes are identical
before and after any sequence of reads by any viewer — rulings 3+4, tested as
a file-hash sweep.
"""

from __future__ import annotations

import json
import os
import sqlite3
import unicodedata
import time
import unicodedata

# Schema 16 (W202): the candidate-verification object is a TRIAL —
# table `trials`, column `trial`, obligations.trial — created by the
# `try` command. Fresh-authority evolution: no alias, no migration.
SCHEMA_VERSION = 17
PROTOCOL_VERSION = 11

HANDLE_MAX_CELLS = 6

# Characters a handle may never contain, whatever their width: the tag
# operators and separators the grammar reserves (`#`, `+`, `@`, `=>`, `*`,
# `.`, `,`), and anything that reads as structure.
_RESERVED = set("#+@=>*.,:/\\\"'`|&;<>()[]{}!?~^$%")


def validate_op_id(op_id) -> None:
	"""WS-5 R82: the ONE operation-id grammar, shared by every entry —
	1-128 bytes of UTF-8 with no whitespace and no control characters of
	ANY kind (all Unicode category C: C0, DEL, C1, format, surrogate,
	unassigned), exactly as advertised."""
	if not isinstance(op_id, str) or not op_id or \
			len(op_id.encode("utf-8")) > 128 or \
			any(ch.isspace() or
			    unicodedata.category(ch).startswith("C")
			    for ch in op_id):
		raise WorkError("an operation id is 1-128 bytes of UTF-8 with "
		                "no whitespace or control characters")


class WorkError(Exception):
	"""A refusal a human (or an agent) should read, rather than a traceback."""


def cell_width(text: str) -> int:
	"""Terminal display cells, wcwidth semantics, stdlib only.

	East-Asian Wide and Fullwidth are two cells; combining marks are zero;
	everything printable else is one. Control characters have no width a
	terminal agrees on, so they are reported as -1 and the caller refuses
	them rather than guessing.
	"""
	cells = 0
	for char in text:
		if unicodedata.category(char) in ("Cc", "Cf"):
			return -1
		if unicodedata.combining(char):
			continue
		cells += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
	return cells


def validate_handle(handle: str, what: str) -> str:
	"""The canonical-handle grammar, refused with the measurement.

	Six display cells, at least one, no reserved or structural characters,
	no whitespace, and NO zero-width content at all: a handle whose visual
	width disagrees with its content is exactly the trick the width rule
	exists to keep out of identity.
	"""
	if not isinstance(handle, str) or not handle:
		raise WorkError(f"{what} handle must be a non-empty string")
	for char in handle:
		if char.isspace():
			raise WorkError(f"{what} handle {handle!r} contains whitespace")
		if char in _RESERVED:
			raise WorkError(
				f"{what} handle {handle!r} contains {char!r}, which the tag "
				f"grammar reserves")
		if unicodedata.combining(char) or unicodedata.category(char) == "Cf":
			raise WorkError(
				f"{what} handle {handle!r} contains a zero-width character; "
				f"a handle's visual width must equal its content")
	cells = cell_width(handle)
	if cells < 0:
		raise WorkError(f"{what} handle {handle!r} contains a control character")
	if cells > HANDLE_MAX_CELLS:
		raise WorkError(
			f"{what} handle {handle!r} is {cells} display cells; the limit is "
			f"{HANDLE_MAX_CELLS}. Shorten the canonical handle and put the "
			f"long form in the display name.")
	return handle


def _utc_now() -> str:
	return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def clock_ms_now() -> str:
	"""The module-level millisecond clock helpers share: the injected
	BATON_WORK_NOW instant when present (deterministic subprocess stories),
	real UTC milliseconds otherwise."""
	return os.environ.get("BATON_WORK_NOW") or _utc_now_ms()


def _utc_now_ms() -> str:
	"""Millisecond-precision UTC instant (schema 15, W84 groundwork): the
	Work-recency cue divides real elapsed time, which second resolution
	cannot express. Still ISO-8601 and lexicographically ordered."""
	now = time.time()
	whole = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now))
	return f"{whole}.{int((now % 1) * 1000):03d}Z"


_SCHEMA = """
CREATE TABLE meta (
	key   TEXT PRIMARY KEY,
	value TEXT NOT NULL
) STRICT;
CREATE TABLE sequence (
	id    INTEGER PRIMARY KEY CHECK (id = 1),
	value INTEGER NOT NULL
) STRICT;
CREATE TABLE teams (
	handle  TEXT PRIMARY KEY,
	display TEXT NOT NULL,
	removed INTEGER NOT NULL DEFAULT 0
) STRICT;
CREATE TABLE members (
	team    TEXT NOT NULL REFERENCES teams(handle),
	handle  TEXT NOT NULL,
	display TEXT NOT NULL,
	removed INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (team, handle)
) STRICT;
CREATE TABLE roles (
	team    TEXT NOT NULL,
	handle  TEXT NOT NULL,
	display TEXT NOT NULL,
	removed INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (team, handle)
) STRICT;
CREATE TABLE routes (
	team    TEXT NOT NULL,
	handle  TEXT NOT NULL,
	role    TEXT NOT NULL,
	removed INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (team, handle)
) STRICT;
CREATE TABLE route_handlers (
	team    TEXT NOT NULL,
	route   TEXT NOT NULL,
	member  TEXT NOT NULL,
	PRIMARY KEY (team, route, member)
) STRICT;
CREATE TABLE member_roles (
	team    TEXT NOT NULL,
	member  TEXT NOT NULL,
	role    TEXT NOT NULL,
	PRIMARY KEY (team, member, role)
) STRICT;
CREATE TABLE member_capabilities (
	team       TEXT NOT NULL,
	member     TEXT NOT NULL,
	capability TEXT NOT NULL,
	PRIMARY KEY (team, member, capability)
) STRICT;
CREATE TABLE kinds (
	team    TEXT NOT NULL REFERENCES teams(handle),
	handle  TEXT NOT NULL,
	display TEXT NOT NULL,
	route   TEXT,
	retired INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (team, handle)
) STRICT;
CREATE TABLE events (
	seq     INTEGER PRIMARY KEY,
	kind    TEXT NOT NULL,
	actor   TEXT NOT NULL,
	payload TEXT NOT NULL,
	ts      TEXT NOT NULL
) STRICT;
CREATE TABLE work (
	id             TEXT PRIMARY KEY,
	team           TEXT NOT NULL REFERENCES teams(handle),
	title          TEXT NOT NULL,
	origin         TEXT NOT NULL,
	classification TEXT NOT NULL,
	phase          TEXT NOT NULL DEFAULT 'queued',
	wait_type       TEXT,
	wait_obligation INTEGER,
	status         TEXT NOT NULL DEFAULT 'open',
	parent         TEXT REFERENCES work(id),
	current_team   TEXT,
	current_kind   TEXT,
	next_team      TEXT,
	next_kind      TEXT,
	ready          INTEGER NOT NULL DEFAULT 0,
	outcome        TEXT,
	rationale      TEXT,
	duplicate_of   TEXT REFERENCES work(id),
	follow_up_of   TEXT REFERENCES work(id),
	created_seq    INTEGER NOT NULL,
	closed_seq     INTEGER,
	priority       TEXT NOT NULL DEFAULT 'normal'
		CHECK (priority IN ('high', 'normal', 'low')),
	last_changed_at TEXT NOT NULL,
	last_change_seq INTEGER NOT NULL,
	-- finding-active-work-claim: `active` is an authority-backed atomic
	-- participant claim, not only a descriptive phase. The claimant
	-- identity lives here; the claim/release transition matrix is that
	-- finding's own gated implementation (blocks W92's release).
	active_team    TEXT,
	active_member  TEXT,
	-- W49 (finding-acp-same-key-redelivery-loss): the ASSIGNMENT EPISODE.
	-- Deliberately NOT last_change_seq, which every visible edit touches:
	-- a claim, a heartbeat, an ordinary phase move, a priority or
	-- classification revision would each redeliver work nobody reassigned
	-- — including prompting a claimant again immediately after their own
	-- claim. This mints only when the Work BECOMES NEWLY ACTIONABLE for
	-- whoever its Current resolves: creation, pass/return, explicit claim
	-- release, a false-to-true readiness flip, a condition wake, and a
	-- parked-to-queued resume. Consumers key delivery on it, so a Work
	-- handed away and handed back BETWEEN two polls is a new episode even
	-- though no observer ever saw it absent.
	episode_seq    INTEGER NOT NULL DEFAULT 0
) STRICT;
CREATE TABLE edges (
	work        TEXT NOT NULL REFERENCES work(id),
	blocker     TEXT NOT NULL REFERENCES work(id),
	via_obligation INTEGER REFERENCES obligations(seq),
	created_seq INTEGER NOT NULL,
	PRIMARY KEY (work, blocker)
) STRICT;
CREATE TABLE obligations (
	seq          INTEGER PRIMARY KEY,
	work         TEXT NOT NULL REFERENCES work(id),
	message_seq  INTEGER NOT NULL,
	team         TEXT NOT NULL,
	kind         TEXT NOT NULL,
	route        TEXT,
	role         TEXT,
	handlers     TEXT,
	generation   INTEGER,
	flavor       TEXT NOT NULL DEFAULT 'response',
	trial        INTEGER,
	observation  TEXT,
	evidence     TEXT,
	accepted_into TEXT REFERENCES work(id),
	thread   TEXT REFERENCES threads(id),
	status       TEXT NOT NULL DEFAULT 'pending',
	resolved_seq INTEGER
) STRICT;
CREATE TABLE trials (
	work        TEXT NOT NULL REFERENCES work(id),
	trial       INTEGER NOT NULL,
	candidate   TEXT NOT NULL,
	status      TEXT NOT NULL DEFAULT 'open',
	review_at   TEXT,
	deadline_generation INTEGER NOT NULL DEFAULT 0,
	created_ts  TEXT NOT NULL,
	created_seq INTEGER NOT NULL,
	ended_seq   INTEGER,
	PRIMARY KEY (work, trial)
) STRICT;
CREATE TABLE assessments (
	seq         INTEGER PRIMARY KEY,
	obligation  INTEGER NOT NULL,
	assessment  TEXT NOT NULL,
	rationale   TEXT NOT NULL,
	actor       TEXT NOT NULL
) STRICT;
CREATE TABLE threads (
	id          TEXT PRIMARY KEY,
	subject     TEXT NOT NULL,
	created_seq INTEGER NOT NULL,
	created_ts  TEXT NOT NULL
) STRICT;
CREATE TABLE thread_labels (
	thread TEXT NOT NULL REFERENCES threads(id),
	work       TEXT NOT NULL REFERENCES work(id),
	added_seq  INTEGER NOT NULL,
	PRIMARY KEY (thread, work)
) STRICT;
CREATE TABLE thread_participants (
	thread TEXT NOT NULL REFERENCES threads(id),
	team       TEXT NOT NULL REFERENCES teams(handle),
	added_seq  INTEGER NOT NULL,
	PRIMARY KEY (thread, team)
) STRICT;
CREATE TABLE roots (
	root       TEXT PRIMARY KEY,
	display    TEXT NOT NULL,
	removed    INTEGER NOT NULL DEFAULT 0
) STRICT;
CREATE TABLE bindings (
	work            TEXT    NOT NULL REFERENCES work(id),
	revision        INTEGER NOT NULL,
	prior           INTEGER NOT NULL,
	root            TEXT    NOT NULL REFERENCES roots(root),
	path            TEXT    NOT NULL,
	git_provenance  TEXT,
	actor           TEXT    NOT NULL,
	rationale       TEXT,
	seq             INTEGER NOT NULL,
	created_ts      TEXT    NOT NULL,
	UNIQUE (work, revision)
) STRICT;
CREATE TABLE act_references (
	seq              INTEGER NOT NULL,
	ordinal          INTEGER NOT NULL,
	kind             TEXT    NOT NULL,
	work             TEXT    REFERENCES work(id),
	binding_revision INTEGER,
	root             TEXT    NOT NULL REFERENCES roots(root),
	path             TEXT    NOT NULL,
	PRIMARY KEY (seq, ordinal)
) STRICT;
CREATE TABLE operations (
	recorded    INTEGER NOT NULL UNIQUE,
	participant TEXT    NOT NULL,
	op_id       TEXT    NOT NULL,
	fingerprint TEXT    NOT NULL,
	seq         INTEGER,
	result      TEXT    NOT NULL,
	created_ts  TEXT    NOT NULL,
	PRIMARY KEY (participant, op_id)
) STRICT;
CREATE TABLE revisions (
	seq         INTEGER PRIMARY KEY,
	work        TEXT NOT NULL REFERENCES work(id),
	revision    INTEGER NOT NULL,
	prior       INTEGER NOT NULL,
	thread  TEXT NOT NULL REFERENCES threads(id),
	message_seq INTEGER NOT NULL,
	actor       TEXT NOT NULL,
	rationale   TEXT NOT NULL,
	content     TEXT NOT NULL,
	created_ts  TEXT NOT NULL,
	UNIQUE (work, revision)
) STRICT;
CREATE TABLE seen (
	team       TEXT NOT NULL,
	member     TEXT NOT NULL,
	thread TEXT NOT NULL REFERENCES threads(id),
	seq        INTEGER NOT NULL,
	PRIMARY KEY (team, member, thread)
) STRICT;
CREATE TABLE messages (
	seq         INTEGER PRIMARY KEY,
	thread  TEXT NOT NULL REFERENCES threads(id),
	author_team TEXT NOT NULL,
	author      TEXT NOT NULL,
	body        TEXT NOT NULL,
	ts          TEXT NOT NULL
) STRICT;
"""


class Authority:
	"""One open v11 Work authority. The ONLY writer in the package."""

	def __init__(self, path: str):
		if not os.path.isfile(path):
			raise WorkError(f"{path} is not an initialized Work authority; "
			                f"run init first")
		self.path = path
		# WS-2 group 3: due-ness is a PURE function of stored review_at and
		# this clock. Production reads UTC wall time; tests may inject a
		# fixed instant (directly, or via BATON_WORK_NOW for subprocess
		# stories) so before/at/after boundaries are deterministic. UTC
		# ISO-8601 strings compare lexicographically, so no display
		# timezone can alter stored ordering.
		self.clock = (lambda: os.environ["BATON_WORK_NOW"]) \
			if os.environ.get("BATON_WORK_NOW") else _utc_now
		# The millisecond clock honours the same injected instant so
		# subprocess stories stay deterministic.
		self.clock_ms = clock_ms_now
		self.conn = sqlite3.connect(path, timeout=60.0)
		self.conn.row_factory = sqlite3.Row
		self.conn.execute("PRAGMA foreign_keys = ON")
		row = self.conn.execute(
			"SELECT value FROM meta WHERE key='schema_version'").fetchone()
		if row is None or int(row["value"]) != SCHEMA_VERSION:
			raise WorkError(
				f"{path} is schema version "
				f"{None if row is None else row['value']}; this build reads "
				f"{SCHEMA_VERSION} and does not guess across versions")

	# -- lifecycle ----------------------------------------------------------

	@classmethod
	def init(cls, path: str) -> "Authority":
		"""Create an empty authority. Refuses to overwrite anything."""
		if os.path.lexists(path):
			raise WorkError(f"{path} already exists; an authority is created "
			                f"once and never re-initialized in place")
		directory = os.path.dirname(os.path.abspath(path))
		os.makedirs(directory, exist_ok=True)
		conn = sqlite3.connect(path)
		try:
			conn.execute("PRAGMA journal_mode = WAL")
			conn.executescript(_SCHEMA)
			authority_uuid = os.urandom(16).hex()
			conn.execute("INSERT INTO sequence (id, value) VALUES (1, 0)")
			conn.executemany(
				"INSERT INTO meta (key, value) VALUES (?, ?)",
				[("schema_version", str(SCHEMA_VERSION)),
				 ("protocol_version", str(PROTOCOL_VERSION)),
				 ("authority_uuid", authority_uuid),
				 ("created_ts", _utc_now())])
			conn.commit()
		finally:
			conn.close()
		# NO handshake file. WORK.json is superseded by ruling: the identity
		# lives in `baton.json` (instance.authority_uuid) and this database
		# stores the same uuid plus the accepted digest/generation. Open
		# validates those facts directly; a third document would be a second
		# place for the truth to disagree with itself.
		return cls(path)

	def close(self) -> None:
		self.conn.close()

	def __enter__(self) -> "Authority":
		return self

	def __exit__(self, *_exc) -> None:
		self.close()

	# -- the one write path -------------------------------------------------

	def _commit_references(self, conn, seq: int, references) -> None:
		"""WS-6: ordered typed asset references commit WITH their act —
		same transaction, keyed by the act's event sequence. Independent
		references require a LIVE configured root; dossier references
		require the named Work to be BOUND and pin the effective binding
		revision under the committing state (a citation of an existing
		immutable revision stays valid after its root retires). Only
		protocol facts are validated — nothing is stat'ed, opened, or
		probed."""
		for ordinal, ref in enumerate(references, start=1):
			if ref["kind"] == "independent":
				live = conn.execute(
					"SELECT removed FROM roots WHERE root=?",
					(ref["root"],)).fetchone()
				if live is None or live["removed"]:
					raise WorkError(
						f"root {ref['root']!r} is not a live configured "
						f"root; an independent reference lands on the "
						f"accepted catalog")
				conn.execute(
					"INSERT INTO act_references (seq, ordinal, kind, "
					"work, binding_revision, root, path) "
					"VALUES (?, ?, 'independent', NULL, NULL, ?, ?)",
					(seq, ordinal, ref["root"], ref["path"]))
			else:
				binding = conn.execute(
					"SELECT revision, root FROM bindings WHERE work=? "
					"ORDER BY revision DESC LIMIT 1",
					(ref["work"],)).fetchone()
				if binding is None:
					raise WorkError(
						f"{ref['work']} has no dossier binding to "
						f"anchor; bind it first or use an independent "
						f"ROOT:PATH reference")
				conn.execute(
					"INSERT INTO act_references (seq, ordinal, kind, "
					"work, binding_revision, root, path) "
					"VALUES (?, ?, 'dossier', ?, ?, ?, ?)",
					(seq, ordinal, ref["work"], binding["revision"],
					 binding["root"], ref["path"]))

	def _op_identity(self, conn, participant: str) -> None:
		"""WS-5 R84: the identity gate read on the SAME connection and
		transaction as the replay lookup — gate and lookup are one
		coherent observation, so an accepted removal can never slip
		between them and disclose a stored result to a now-removed
		identity."""
		team, _dot, member = str(participant).partition(".")
		if conn.execute(
				"SELECT 1 FROM members WHERE team=? AND handle=? AND "
				"removed=0", (team, member)).fetchone() is None:
			raise WorkError(f"{participant} is not a registered member "
			                f"of the currently accepted configuration")

	def _op_replay(self, conn, participant: str, op_id: str,
	               fingerprint: str):
		"""WS-5 lookup: the stored result for an EXACT retry (state
		rewritten to `replayed` on the way out), None when unrecorded,
		and a closed refusal for conflicting reuse — an operation
		identity names one semantic request forever."""
		row = conn.execute(
			"SELECT fingerprint, result FROM operations WHERE "
			"participant=? AND op_id=?", (participant, op_id)).fetchone()
		if row is None:
			return None
		if row["fingerprint"] != fingerprint:
			raise WorkError(
				f"op-id {op_id!r} was already used by {participant} "
				f"for a different request; conflicting reuse refuses "
				f"without mutation")
		out = json.loads(row["result"])
		out["operation"] = dict(out["operation"], state="replayed")
		return out

	def _op_record(self, conn, participant: str, op_id: str,
	               fingerprint: str, seq, result: dict) -> None:
		"""The operation record commits WITH its effect (or alone for a
		successful protected no-op, seq NULL): identity, fingerprint,
		provenance, and the complete replayable result, ordered by the
		history's own dense `recorded` cursor."""
		recorded = conn.execute(
			"SELECT COALESCE(MAX(recorded), 0) + 1 AS next "
			"FROM operations").fetchone()["next"]
		conn.execute(
			"INSERT INTO operations (recorded, participant, op_id, "
			"fingerprint, seq, result, created_ts) "
			"VALUES (?, ?, ?, ?, ?, ?, ?)",
			(recorded, participant, op_id, fingerprint, seq,
			 json.dumps(result, sort_keys=True), _utc_now()))

	def record_noop(self, operation, result: dict) -> dict:
		"""WS-5 R76: a SUCCESSFUL protected no-op consumes its identity —
		one transaction holding ONLY the operation record (seq NULL, no
		domain event, no sequence allocation); refusals never reach
		here. Returns the result carrying its committed operation
		shape."""
		participant, op_id, fingerprint = operation
		try:
			self.conn.execute("BEGIN IMMEDIATE")
			self._op_identity(self.conn, participant)
			replay = self._op_replay(self.conn, participant, op_id,
			                         fingerprint)
			if replay is not None:
				self.conn.execute("ROLLBACK")
				return replay
			result = dict(result)
			result["operation"] = {"id": op_id, "state": "committed"}
			self._op_record(self.conn, participant, op_id, fingerprint,
			                None, result)
			self.conn.execute("COMMIT")
		except BaseException:
			try:
				self.conn.execute("ROLLBACK")
			except sqlite3.Error:
				pass
			raise
		return result

	def _write(self, event_kind: str, actor: str, payload: dict,
	           mutate, operation=None, finish=None,
	           references=None) -> dict:
		"""One mutation: BEGIN IMMEDIATE, allocate seq, apply, commit.

		`mutate(conn, seq)` performs the step's own writes. The sequence
		allocation and the event row live in the SAME transaction, which is
		the whole property: an event number exists if and only if its
		mutation committed.

		WS-5: with `operation=(participant, op_id, fingerprint)` the
		in-lock lookup replays a concurrently committed exact retry (or
		refuses conflicting reuse), and on success the operation record —
		identity, fingerprint, event provenance, and the COMPLETE
		replayable result (decorations applied by `finish(result)` inside
		the transaction) — commits atomically with the effect."""
		try:
			self.conn.execute("BEGIN IMMEDIATE")
			if operation is not None:
				# Fresh generation-1 bootstrap: the members rows commit
				# in THIS transaction, so no accepted generation exists
				# to gate against — the proposed-document validation
				# governs (R81); every later operation gates here.
				if self.conn.execute(
						"SELECT 1 FROM members LIMIT 1").fetchone() \
						is not None:
					self._op_identity(self.conn, operation[0])
				replay = self._op_replay(self.conn, *operation)
				if replay is not None:
					self.conn.execute("ROLLBACK")
					return replay
			seq = self.conn.execute(
				"UPDATE sequence SET value = value + 1 WHERE id = 1 "
				"RETURNING value").fetchone()["value"]
			mutate(self.conn, seq)
			if references:
				self._commit_references(self.conn, seq, references)
			result = {"seq": seq, "kind": event_kind}
			if finish is not None:
				finish(result)
			if operation is not None:
				participant, op_id, fingerprint = operation
				result["operation"] = {"id": op_id, "state": "committed"}
				self._op_record(self.conn, participant, op_id,
				                fingerprint, seq, result)
			else:
				result["operation"] = None
			self.conn.execute(
				"INSERT INTO events (seq, kind, actor, payload, ts) "
				"VALUES (?, ?, ?, ?, ?)",
				(seq, event_kind, actor,
				 json.dumps(payload, sort_keys=True), _utc_now()))
			self.conn.execute("COMMIT")
		except BaseException as failure:
			try:
				self.conn.execute("ROLLBACK")
			except sqlite3.Error:
				pass
			if isinstance(failure, sqlite3.IntegrityError):
				# THE RACE LOSER'S PATH. Pre-validation passed in two
				# writers; the constraint refused the second inside the
				# transaction. That is an ordinary refusal, not a defect,
				# and it must read like one — a raw IntegrityError traceback
				# would teach callers to catch sqlite3 errors, which only
				# this module may know exist.
				raise WorkError(
					f"{event_kind} lost a concurrent race: "
					f"{failure}") from None
			raise
		return result

	# -- identity registration (A1) ----------------------------------------

	def register_team(self, handle: str, display: str,
	                  *, actor: str = "config") -> dict:
		validate_handle(handle, "team")
		if not isinstance(display, str) or not display:
			raise WorkError("a team display name must be a non-empty string")
		if self.conn.execute("SELECT 1 FROM teams WHERE handle=?",
		                     (handle,)).fetchone():
			raise WorkError(f"team {handle!r} is already registered; handles "
			                f"are identities and are never reused or replaced")

		def mutate(conn, _seq):
			conn.execute("INSERT INTO teams (handle, display) VALUES (?, ?)",
			             (handle, display))
		return self._write("register_team", actor,
		                   {"team": handle, "display": display}, mutate)

	def register_member(self, team: str, handle: str, display: str,
	                    *, actor: str = "config") -> dict:
		validate_handle(handle, "member")
		self._team(team)
		if not isinstance(display, str) or not display:
			raise WorkError("a member display name must be a non-empty string")
		if self.conn.execute("SELECT 1 FROM members WHERE team=? AND handle=?",
		                     (team, handle)).fetchone():
			raise WorkError(f"member {team}.{handle} is already registered")

		def mutate(conn, _seq):
			conn.execute(
				"INSERT INTO members (team, handle, display) VALUES (?, ?, ?)",
				(team, handle, display))
		return self._write("register_member", actor,
		                   {"team": team, "member": handle,
		                    "display": display}, mutate)

	def register_kind(self, team: str, handle: str, display: str,
	                  *, actor: str = "config") -> dict:
		validate_handle(handle, "kind")
		self._team(team)
		if not isinstance(display, str) or not display:
			raise WorkError("a kind display name must be a non-empty string")
		if self.conn.execute("SELECT 1 FROM kinds WHERE team=? AND handle=?",
		                     (team, handle)).fetchone():
			raise WorkError(
				f"kind {team}.{handle} is already registered. Retired kinds "
				f"keep their name forever — reuse would make old records lie.")

		def mutate(conn, _seq):
			conn.execute(
				"INSERT INTO kinds (team, handle, display) VALUES (?, ?, ?)",
				(team, handle, display))
		return self._write("register_kind", actor,
		                   {"team": team, "kind": handle,
		                    "display": display}, mutate)

	def retire_kind(self, team: str, handle: str,
	                *, actor: str = "config") -> dict:
		"""Retired, never deleted: the name stays taken and old records stay
		true; new obligations to it refuse at tag time (A4)."""
		row = self.conn.execute(
			"SELECT retired FROM kinds WHERE team=? AND handle=?",
			(team, handle)).fetchone()
		if row is None:
			raise WorkError(f"kind {team}.{handle} is not registered")
		if row["retired"]:
			raise WorkError(f"kind {team}.{handle} is already retired")

		def mutate(conn, _seq):
			conn.execute("UPDATE kinds SET retired=1 WHERE team=? AND handle=?",
			             (team, handle))
		return self._write("retire_kind", actor,
		                   {"team": team, "kind": handle}, mutate)

	# -- pure reads ---------------------------------------------------------

	def _team(self, handle: str) -> sqlite3.Row:
		row = self.conn.execute("SELECT * FROM teams WHERE handle=?",
		                        (handle,)).fetchone()
		if row is None:
			raise WorkError(f"team {handle!r} is not registered")
		return row

	def meta(self) -> dict:
		return {row["key"]: row["value"]
		        for row in self.conn.execute("SELECT key, value FROM meta")}

	def last_seq(self) -> int:
		return self.conn.execute(
			"SELECT value FROM sequence WHERE id=1").fetchone()["value"]

	def events(self, *, after: int = 0, limit: int = 1000) -> list[dict]:
		"""The audit trail, ascending by sequence. Pure."""
		out = []
		for row in self.conn.execute(
				"SELECT seq, kind, actor, payload, ts FROM events "
				"WHERE seq > ? ORDER BY seq LIMIT ?", (after, limit)):
			entry = dict(row)
			entry["payload"] = json.loads(entry["payload"])
			entry["references"] = [dict(ref) for ref in self.conn.execute(
				"SELECT ordinal, kind, work, binding_revision, root, "
				"path FROM act_references WHERE seq=? ORDER BY ordinal",
				(row["seq"],))]
			out.append(entry)
		return out
