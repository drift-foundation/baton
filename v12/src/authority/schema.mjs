// The disposable v12 authority's durable schema.
//
// This is a SELF-CONTAINED store. It is not the v11 authority, it is not
// a migration of one, and nothing here opens `work.sqlite3` or imports
// `src/baton_work/`. `SPEC.md` §5 calls for an additive superset of the
// v11 Work row; this is that superset built fresh, so the v11 columns it
// keeps (route, phase, status, handler) carry the meanings v11 gives
// them and the v12 columns beside them are new.
//
// What the AUTHORITY owns is fixed by §3 and the table list is the whole
// argument: Work state, the per-Work contract selector, the generation
// counter, the live assignment, fenced generations, the one typed gate,
// assignment-ending and contract events, gate evidence, proposal and
// workflow receipts, and the operation journal. Offers, runtime attempts,
// quarantined output and runtime observations are the Worker Manager
// control store's and are deliberately absent — an authority that also
// stored them would be answering questions it is not authoritative for.

export const SCHEMA_VERSION = 1;

export const SCHEMA = `
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
-- Concurrent writers WAIT for the write lock rather than failing with
-- SQLITE_BUSY. A competing claim must lose by being refused inside the
-- transaction, which is a decision; losing by not getting a transaction at
-- all is an error, and the two are not interchangeable.
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS meta (
	key   TEXT PRIMARY KEY,
	value TEXT NOT NULL
);

-- Deployment policy. These are configured facts shared by every Work:
-- which contracts a certified runtime profile can execute, which
-- contract transitions are permitted at all, and the pinned isolation
-- and retention clauses §10.8/§10.9 refer to.
CREATE TABLE IF NOT EXISTS certified_contract (
	contract     TEXT PRIMARY KEY,
	profile      TEXT NOT NULL,
	certified_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contract_transition (
	from_contract TEXT NOT NULL,
	to_contract   TEXT NOT NULL,
	PRIMARY KEY (from_contract, to_contract)
);

CREATE TABLE IF NOT EXISTS policy (
	key   TEXT PRIMARY KEY,
	value TEXT NOT NULL
);

-- One row per Work. phase is the closed scheduler axis and is NULL
-- exactly when the Work is terminal; gate is the ONE typed gate v11
-- already displays, never a second axis (§10.7).
CREATE TABLE IF NOT EXISTS work (
	work_id            TEXT PRIMARY KEY,
	route              TEXT NOT NULL,
	status             TEXT NOT NULL,
	phase              TEXT,
	outcome            TEXT,
	rationale          TEXT,
	handler            TEXT,
	contract           TEXT NOT NULL,
	generation_counter INTEGER NOT NULL DEFAULT 0,
	live_generation    INTEGER,
	gate               TEXT,
	created_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS route_handler (
	route       TEXT NOT NULL,
	participant TEXT NOT NULL,
	PRIMARY KEY (route, participant)
);

-- Configured capabilities. §7 names a distinct actor for the receipt
-- transitions -- verifier, rview, approv, trusted integrator -- and an
-- authorized actor holding the close capability. Review 2026-08-22 [P1]:
-- without this, one consumer could publish a candidate, self-verify it,
-- self-review it, self-approve it, integrate it into the canonical target
-- and close the Work, because the receipts stored dispositions and no actor
-- at all.
--
-- A deployment MAY grant one participant several of these: §10.12 says the
-- four receipts stay distinct even when configuration permits one
-- participant to hold more than one role. What it may not do is leave the
-- question unasked, which is what an actorless receipt does.
CREATE TABLE IF NOT EXISTS capability (
	participant TEXT NOT NULL,
	capability  TEXT NOT NULL,
	granted_at  TEXT NOT NULL,
	PRIMARY KEY (participant, capability)
);

-- Fenced generations are retained forever with their cause: §10.1 says
-- the counter is never decremented or reused, and the fence is how a
-- late act by an ended generation is refused rather than ignored.
CREATE TABLE IF NOT EXISTS fenced_generation (
	work_id    TEXT NOT NULL,
	generation INTEGER NOT NULL,
	cause      TEXT NOT NULL,
	reason     TEXT,
	fenced_at  TEXT NOT NULL,
	PRIMARY KEY (work_id, generation),
	FOREIGN KEY (work_id) REFERENCES work (work_id)
);

-- Deployment-wide capacity (§10.2). The participant is the key BECAUSE
-- one participant holds at most one live claim across the whole
-- deployment; making this per Work is the bug the table shape forbids.
CREATE TABLE IF NOT EXISTS claim_slot (
	participant TEXT PRIMARY KEY,
	work_id     TEXT NOT NULL,
	generation  INTEGER,
	taken_at    TEXT NOT NULL
);

-- The operation journal. An identity is durably in exactly one of four
-- states; UNSUBMITTED is the absence of a row (§4).
CREATE TABLE IF NOT EXISTS operation (
	operation_id TEXT PRIMARY KEY,
	signature    TEXT NOT NULL,
	state        TEXT NOT NULL CHECK (state IN ('committed', 'refused', 'retired')),
	result       TEXT,
	detail       TEXT,
	recorded_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignment_event (
	seq         INTEGER PRIMARY KEY AUTOINCREMENT,
	work_id     TEXT NOT NULL,
	participant TEXT NOT NULL,
	generation  INTEGER,
	cause       TEXT NOT NULL,
	fenced      INTEGER NOT NULL,
	reason      TEXT,
	gate        TEXT,
	phase       TEXT,
	at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contract_event (
	seq           INTEGER PRIMARY KEY AUTOINCREMENT,
	work_id       TEXT NOT NULL,
	from_contract TEXT NOT NULL,
	to_contract   TEXT NOT NULL,
	participant   TEXT NOT NULL,
	generation    INTEGER,
	rationale     TEXT NOT NULL,
	at            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_evidence (
	seq      INTEGER PRIMARY KEY AUTOINCREMENT,
	work_id  TEXT NOT NULL,
	gate     TEXT NOT NULL,
	evidence TEXT NOT NULL,
	at       TEXT NOT NULL
);

-- Canonical activity carried out under an exact assignment. Unique on
-- the assignment plus the caller's key, so a retry is the same row.
CREATE TABLE IF NOT EXISTS activity (
	seq         INTEGER PRIMARY KEY AUTOINCREMENT,
	work_id     TEXT NOT NULL,
	participant TEXT NOT NULL,
	generation  INTEGER,
	action_key  TEXT NOT NULL,
	at          TEXT NOT NULL
);

-- IFNULL, not a plain UNIQUE: SQLite treats NULLs as distinct in a unique
-- index, so a v11 assignment (which mints no generation) would insert the
-- same activity twice and the idempotency key would silently stop working.
CREATE UNIQUE INDEX IF NOT EXISTS activity_key
	ON activity (work_id, participant, IFNULL(generation, -1), action_key);

-- The immutable candidate.
--
-- §10.11 requires the receipt to bind the exact assignment AND the input,
-- policy, output, candidate-tree and target digests; §4 adds the frozen
-- result identity and its content digest. Review 2026-08-22 [P1]: one
-- undifferentiated digest column bound none of that, so a proposal could
-- not say what it was built FROM. Every digest is required and every one
-- rides the publish operation signature, because later bytes are a new
-- proposal rather than an edit to this one.
CREATE TABLE IF NOT EXISTS proposal (
	proposal_id      TEXT PRIMARY KEY,
	work_id          TEXT NOT NULL,
	participant      TEXT NOT NULL,
	generation       INTEGER,
	result_id        TEXT NOT NULL,
	result_digest    TEXT NOT NULL,
	candidate_digest TEXT NOT NULL,
	input_digest     TEXT NOT NULL,
	policy_digest    TEXT NOT NULL,
	target           TEXT NOT NULL,
	published_at     TEXT NOT NULL
);

-- The four separately attributable IMMUTABLE receipts (§10.12).
--
-- Rows rather than columns on the proposal, because each carries its own
-- identity, its own actor, and the candidate digest and target revision it
-- was written against. A receipt that was only a disposition string could
-- not say who attributed it or what they saw.
--
-- kind is UNIQUE per proposal: that is the immutability rule, enforced by
-- the index rather than by a check somebody can forget.
CREATE TABLE IF NOT EXISTS receipt (
	receipt_id        TEXT PRIMARY KEY,
	kind              TEXT NOT NULL CHECK (kind IN
	                    ('verification', 'review', 'approval', 'integration')),
	proposal_id       TEXT NOT NULL,
	actor             TEXT NOT NULL,
	disposition       TEXT NOT NULL,
	candidate_digest  TEXT NOT NULL,
	target            TEXT NOT NULL,
	policy_generation INTEGER,
	recorded_at       TEXT NOT NULL,
	FOREIGN KEY (proposal_id) REFERENCES proposal (proposal_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS receipt_one_per_kind
	ON receipt (proposal_id, kind);

-- A refused integration is journalled ONCE beside the proposal and never
-- rewrites a committed receipt (§7, review P1b).
CREATE TABLE IF NOT EXISTS integration_attempt (
	seq         INTEGER PRIMARY KEY AUTOINCREMENT,
	proposal_id TEXT NOT NULL,
	actor       TEXT NOT NULL,
	reason      TEXT NOT NULL,
	target      TEXT NOT NULL,
	at          TEXT NOT NULL
);
`;
