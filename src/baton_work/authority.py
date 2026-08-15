"""The v11 Work authority: schema, publication sequence, identity registry.

Gate A step A1. Three properties live here and everything later leans on them:

THE SEQUENCE IS ALLOCATED INSIDE THE WRITE TRANSACTION. Every mutation calls
`_append` within the same `BEGIN IMMEDIATE` that commits its rows, and the
sequence is a persisted counter incremented there — so two committed events can
never share a number, a crash between allocate and commit leaves no gap that a
reader can observe as a row, and a restart continues above everything that ever
committed. This is the total order that pagination, audit and readiness
recomputation stand on; protocol 10's `(created_ts, id)` tie is the defect it
replaces (`work/finding-same-second-ordering/`).

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
import time
import unicodedata

SCHEMA_VERSION = 11
PROTOCOL_VERSION = 11

HANDLE_MAX_CELLS = 6

# Characters a handle may never contain, whatever their width: the tag
# operators and separators the grammar reserves (`#`, `+`, `@`, `=>`, `*`,
# `.`, `,`), and anything that reads as structure.
_RESERVED = set("#+@=>*.,:/\\\"'`|&;<>()[]{}!?~^$%")


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
	classification TEXT NOT NULL DEFAULT 'unknown',
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
	closed_seq     INTEGER
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
	round        INTEGER,
	observation  TEXT,
	evidence     TEXT,
	accepted_into TEXT REFERENCES work(id),
	discussion   TEXT REFERENCES discussions(id),
	status       TEXT NOT NULL DEFAULT 'pending',
	resolved_seq INTEGER
) STRICT;
CREATE TABLE rounds (
	work        TEXT NOT NULL REFERENCES work(id),
	round       INTEGER NOT NULL,
	candidate   TEXT NOT NULL,
	status      TEXT NOT NULL DEFAULT 'open',
	review_at   TEXT,
	deadline_generation INTEGER NOT NULL DEFAULT 0,
	created_ts  TEXT NOT NULL,
	created_seq INTEGER NOT NULL,
	ended_seq   INTEGER,
	PRIMARY KEY (work, round)
) STRICT;
CREATE TABLE assessments (
	seq         INTEGER PRIMARY KEY,
	obligation  INTEGER NOT NULL,
	assessment  TEXT NOT NULL,
	rationale   TEXT NOT NULL,
	actor       TEXT NOT NULL
) STRICT;
CREATE TABLE discussions (
	id          TEXT PRIMARY KEY,
	created_seq INTEGER NOT NULL,
	created_ts  TEXT NOT NULL
) STRICT;
CREATE TABLE discussion_labels (
	discussion TEXT NOT NULL REFERENCES discussions(id),
	work       TEXT NOT NULL REFERENCES work(id),
	added_seq  INTEGER NOT NULL,
	PRIMARY KEY (discussion, work)
) STRICT;
CREATE TABLE discussion_participants (
	discussion TEXT NOT NULL REFERENCES discussions(id),
	team       TEXT NOT NULL REFERENCES teams(handle),
	added_seq  INTEGER NOT NULL,
	PRIMARY KEY (discussion, team)
) STRICT;
CREATE TABLE revisions (
	seq         INTEGER PRIMARY KEY,
	work        TEXT NOT NULL REFERENCES work(id),
	revision    INTEGER NOT NULL,
	prior       INTEGER NOT NULL,
	discussion  TEXT NOT NULL REFERENCES discussions(id),
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
	discussion TEXT NOT NULL REFERENCES discussions(id),
	seq        INTEGER NOT NULL,
	PRIMARY KEY (team, member, discussion)
) STRICT;
CREATE TABLE messages (
	seq         INTEGER PRIMARY KEY,
	discussion  TEXT NOT NULL REFERENCES discussions(id),
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

	def _write(self, event_kind: str, actor: str, payload: dict,
	           mutate) -> dict:
		"""One mutation: BEGIN IMMEDIATE, allocate seq, apply, commit.

		`mutate(conn, seq)` performs the step's own writes. The sequence
		allocation and the event row live in the SAME transaction, which is
		the whole property: an event number exists if and only if its
		mutation committed.
		"""
		try:
			self.conn.execute("BEGIN IMMEDIATE")
			seq = self.conn.execute(
				"UPDATE sequence SET value = value + 1 WHERE id = 1 "
				"RETURNING value").fetchone()["value"]
			mutate(self.conn, seq)
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
		return {"seq": seq, "kind": event_kind}

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
			out.append(entry)
		return out
