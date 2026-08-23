// The Worker Manager's OWN durable control store schema.
//
// W2929. This is not the authority and it is not a migration of one: the
// authority owns Work state, generations, gates, claim outcomes and the
// workflow receipts, and this store owns the facts a manager is
// authoritative for — which offers it issued, which runtime attempts it
// made, what its adapters observed, and how its own operations settled.
//
// THE SPLIT IS THE POINT. `SPEC.md` §3 of W151 says a manager-local or
// sidecar identity is non-conforming: a manager that stored a claim or a
// generation would be a second authority, and two authorities disagreeing
// is not a bug that can be fixed afterwards. So there is no `claim` here,
// no generation counter and no Work phase — only the fixed claim OPERATION
// identity the authority settles, recorded so a restart can go and ask.
//
// WHAT MAY NEVER BE HERE. Bearer tokens, credentials, raw provider
// approval payloads, and the authority's configuration or store locator.
// Only verifier and body digests, redacted diagnostics, and identities.
// A regression walks every column of every table asserting the bearer is
// absent, because "we do not write it" is a property of code and this is a
// property of the file.

// VERSION HISTORY, one line each, because an incompatible binary refuses on
// this number and the reason it moved is what tells a reader whether their
// store is behind:
//
//   2: the assignment bindings item 3's review required — the generation a
//      claim actually produced, on the offer, and the full four-part
//      assignment on the attempt. A manager that stored three of four
//      fields could not compare the fourth.
//   3: one claimed offer per runtime attempt, as a UNIQUE INDEX. The
//      allocator already behaved; the store did not say so.
//   4: the frozen output — the immutable result record and its artifact
//      references.
//   5: the RETAINED MANIFESTS. A digest is not a record: the freeze review
//      found that neither the input declaration nor the sealed result
//      survived the call that produced it.
//   6: the TRUSTED INTAKE DECISION, with its retention separate from it.
//   7: the intake decision BOUND TO THE MATERIAL it decided. A locator is
//      where something is; it is not which immutable result was judged.
//   8: the CERTIFIED PROFILE BYTES, and the agent sessions opened under
//      them. A profile digest cannot be read for the policy it pins.
//   9: AT MOST ONE OPEN SESSION PER POSTURE, as a partial unique index.
//      Freshness and concurrency are two rules and were tested as one.
//  10: TURNS, with the manager deadline every one of them has and the
//      dispositions its outcome permits.
//  11: the turn's own CANONICAL DOCUMENT, retained beside the summary. A
//      row that cannot represent the frozen record is not the record.
export const SCHEMA_VERSION = 11;

export const SCHEMA = `
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
-- Concurrent managers WAIT for the write lock rather than failing with
-- SQLITE_BUSY. The one-offer-per-Work rule must be decided by a refusal
-- INSIDE a transaction; losing by not getting a transaction at all is an
-- error, and the two are not interchangeable.
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS meta (
	key   TEXT PRIMARY KEY,
	value TEXT NOT NULL
) STRICT;

-- The certified profiles this manager may act under. A profile is
-- certified by DIGEST: "the runtime profile we agreed on" is a byte
-- identity, not a name, or a later edit to a file would silently
-- recertify itself.
CREATE TABLE IF NOT EXISTS profiles (
	kind        TEXT NOT NULL CHECK (kind IN ('runtime', 'agent-session')),
	name        TEXT NOT NULL,
	digest      TEXT NOT NULL,
	-- THE CERTIFIED BYTES, for a kind this manager certifies from a document
	-- rather than from a digest somebody hands it. A digest cannot be read
	-- for the per-posture policy a session must pin, which is the same
	-- lesson the freeze review taught about results: a digest is not a
	-- record. Null for a runtime profile, whose document W2930 owns.
	body        TEXT,
	certified_at TEXT NOT NULL,
	withdrawn_at TEXT,
	PRIMARY KEY (kind, name)
) STRICT;

-- ONE AGENT SESSION per (attempt, posture, epoch).
--
-- Consent and execution NEVER share an epoch or a connection, and an epoch is
-- FRESH every time: the manager never resumes, forks or promotes one, so the
-- key is a fact rather than a convention. The reference labels evidence; it
-- is never an assignment identity and it authorizes nothing.
CREATE TABLE IF NOT EXISTS agent_sessions (
	runtime_attempt_id TEXT NOT NULL REFERENCES attempts(runtime_attempt_id),
	posture            TEXT NOT NULL
	                   CHECK (posture IN ('consent', 'execution')),
	session_epoch      INTEGER NOT NULL CHECK (session_epoch >= 1),
	profile_digest     TEXT NOT NULL,
	-- the per-posture policy this session pinned, by digest of the exact
	-- policy object the certified profile carries for this posture
	pinned_policy      TEXT NOT NULL,
	work_id            TEXT NOT NULL,
	authority_uuid     TEXT NOT NULL,
	-- exactly null for a consent session, which exists before any claim, and
	-- exactly the assignment for an execution one
	participant        TEXT,
	generation         INTEGER,
	provider_session_id TEXT,
	state              TEXT NOT NULL,
	opened_at          TEXT NOT NULL,
	PRIMARY KEY (runtime_attempt_id, posture, session_epoch)
) STRICT;

-- AT MOST ONE OPEN SESSION PER POSTURE, across every manager process.
--
-- Review [P1]: freshness and concurrency are two rules and the first version
-- tested them as one — allocating MAX+1 and inserting unconditionally, so a
-- posture could hold three simultaneously open epochs. A partial unique index
-- rather than a read-then-write check, because two managers racing on
-- separate connections both pass any read and only the database can refuse
-- the second.
--
-- 'closed' is the only state that frees the posture. 'unknown' deliberately
-- does NOT: transport ambiguity is where a second session would be most
-- tempting and least safe, and re-identification after it is a gate this
-- slice has not built.
--
-- (Plain quotes, not backticks: this whole schema is a JS template literal
-- and a backticked word terminates it. THIRD occurrence in this file.)
CREATE UNIQUE INDEX IF NOT EXISTS agent_sessions_one_open_per_posture
	ON agent_sessions (runtime_attempt_id, posture)
	WHERE state <> 'closed';

-- ONE TURN, inside one session epoch.
--
-- EVERY TURN HAS A MANAGER DEADLINE, so the column is NOT NULL: a turn whose
-- deadline is optional is a turn that can wait forever, and 'timeout' is one
-- of the two honest outcomes precisely because the deadline is always there.
--
-- 'permitted' is DERIVED from the outcome and stored so a later reader sees
-- the gate that was applied rather than re-deriving one from a table that may
-- have moved. The turn outcome GATES the worker disposition and never
-- chooses it.
CREATE TABLE IF NOT EXISTS turns (
	turn_id            TEXT PRIMARY KEY,
	runtime_attempt_id TEXT NOT NULL REFERENCES attempts(runtime_attempt_id),
	posture            TEXT NOT NULL,
	session_epoch      INTEGER NOT NULL,
	prompt_digest      TEXT NOT NULL,
	started_at         TEXT NOT NULL,
	deadline_at        TEXT NOT NULL,
	ended_at           TEXT NOT NULL,
	outcome            TEXT NOT NULL,
	-- the exact provider observation the outcome was derived from; 'none' is
	-- how a timeout or a lost transport says it has nothing
	terminal_kind      TEXT NOT NULL,
	terminal_value     TEXT,
	conclusive         INTEGER NOT NULL,
	permitted          TEXT NOT NULL,
	event_count        INTEGER NOT NULL DEFAULT 0,
	late_event_count   INTEGER NOT NULL DEFAULT 0,
	dropped_event_count INTEGER NOT NULL DEFAULT 0,
	dropped_event_bytes INTEGER NOT NULL DEFAULT 0,
	-- THE EVIDENCE THAT SELECTED THE OUTCOME, beside the outcome. A durable
	-- 'policy-failed' whose failure list vanished is not the record that
	-- outcome came from, and a reader should not have to open the sealed
	-- document to ask which violation ended the turn.
	policy_failures    TEXT NOT NULL DEFAULT '[]',
	-- the sealed frozen turnRecord, RFC 8785 canonical. The columns above
	-- are the queryable summary; this is the record. A summary that cannot
	-- represent policy failures, evidence, diagnostics or the seal is not
	-- what was accepted, and reproducing what was accepted is the point.
	body               TEXT NOT NULL,
	document_digest    TEXT NOT NULL,
	recorded_at        TEXT NOT NULL,
	FOREIGN KEY (runtime_attempt_id, posture, session_epoch)
		REFERENCES agent_sessions (runtime_attempt_id, posture, session_epoch)
) STRICT;

-- One offer. The verifier is stored; the bearer never is.
CREATE TABLE IF NOT EXISTS offers (
	offer_id           TEXT PRIMARY KEY,
	work_id            TEXT NOT NULL,
	authority_uuid     TEXT NOT NULL,
	participant        TEXT NOT NULL,
	runtime_attempt_id TEXT NOT NULL,
	incarnation        TEXT NOT NULL,
	-- advisory evidence only: the readiness episode this offer answered.
	-- It is NOT the assignment episode and grants nothing.
	readiness_episode  INTEGER,
	input_digest       TEXT NOT NULL,
	policy_digest      TEXT NOT NULL,
	profile_digest     TEXT NOT NULL,
	-- "sha256:<hex over the bearer's own UTF-8 bytes>" — W151 §7's ONE
	-- derivation, pinned by the W4487 re-review. Never the bearer.
	verifier           TEXT NOT NULL,
	verifier_spent     INTEGER NOT NULL DEFAULT 0,
	issued_at          TEXT NOT NULL,
	expires_at         TEXT NOT NULL,
	-- W151's exact offer vocabulary. 'issued' and 'accepted' are the two
	-- NONTERMINAL states, which is what the partial index below counts.
	state              TEXT NOT NULL CHECK (state IN (
		'issued', 'accepted', 'claimed', 'declined', 'expired',
		'settlement-expired', 'claim-refused', 'abandoned-after-restart')),
	-- the durable decision record: its prose is an operand of the
	-- operation signature, so it is stored beside the state it caused
	decision_reason    TEXT,
	decided_at         TEXT,
	-- acceptance's separate facts. The intent is immutable once written,
	-- and the settlement deadline is a DIFFERENT deadline from expiry.
	intent_digest      TEXT,
	accepted_at        TEXT,
	settle_by          TEXT,
	claim_operation_id TEXT,
	claim_signature    TEXT,
	-- the generation the claim COMMITTED, recorded when it settled. It is
	-- what an attempt's activation compares against: a live assignment
	-- somewhere in the authority is not proof that THIS offer claimed it.
	claim_generation   INTEGER
) STRICT;

-- ONE OFFER PER RUNTIME ATTEMPT, at the database boundary.
--
-- Review [P1]: activation asks for THIS attempt's claim, and that question
-- has no honest answer if two claimed rows can share an attempt identity —
-- 'SELECT ... LIMIT 1' would merely pick one by unspecified row order. I
-- argued this was unwitnessable by construction; the construction was a
-- property of the ALLOCATOR, not of the store, and the store is what
-- activation reads. An invariant only the writer maintains is not an
-- invariant.
CREATE UNIQUE INDEX IF NOT EXISTS offers_one_per_attempt
	ON offers (runtime_attempt_id);

-- AT MOST ONE nonterminal offer per Work, across every manager process.
-- A partial unique index rather than a check in code: two managers racing
-- on separate connections both pass any read-then-write check, and only
-- the database can refuse the second.
CREATE UNIQUE INDEX IF NOT EXISTS offers_one_live_per_work
	ON offers (authority_uuid, work_id)
	WHERE state IN ('issued', 'accepted');

-- One runtime attempt. The ten orthogonal axes of the runtime-attempt
-- manifest are columns rather than a JSON blob, so a regression can ask
-- the database whether an axis regressed.
CREATE TABLE IF NOT EXISTS attempts (
	runtime_attempt_id TEXT PRIMARY KEY,
	work_id            TEXT,
	authority_uuid     TEXT,
	-- the exact live assignment this attempt belongs to, once there is
	-- one. Null before activation: an attempt exists from the offer.
	-- ALL FOUR FIELDS, because an assignment is a four-part identity and
	-- comparing three of them is comparing a different thing.
	assignment_generation INTEGER,
	assignment_participant TEXT,
	adapter_name       TEXT NOT NULL,
	adapter_digest     TEXT NOT NULL,
	profile_digest     TEXT NOT NULL,
	input_digest       TEXT,
	policy_digest      TEXT,
	image_digest       TEXT,
	toolchain_digest   TEXT,
	-- opaque and adapter-minted; it carries no authority
	runtime_id         TEXT,
	observation_seq    INTEGER NOT NULL DEFAULT 0,
	consent_runtime    TEXT NOT NULL DEFAULT 'not-started',
	execution_runtime  TEXT NOT NULL DEFAULT 'not-started',
	output             TEXT NOT NULL DEFAULT 'open',
	worker_disposition TEXT NOT NULL DEFAULT 'none',
	proposal           TEXT NOT NULL DEFAULT 'none',
	verification       TEXT NOT NULL DEFAULT 'none',
	technical_review   TEXT NOT NULL DEFAULT 'none',
	approval           TEXT NOT NULL DEFAULT 'none',
	integration        TEXT NOT NULL DEFAULT 'none',
	cleanup            TEXT NOT NULL DEFAULT 'pending',
	created_at         TEXT NOT NULL,
	observed_at        TEXT
) STRICT;

-- The MANAGER's own operation journal, separate from the authority's.
-- §4.2: success at one boundary does not imply success at the other, and
-- reconciliation queries both exact records.
CREATE TABLE IF NOT EXISTS operations (
	operation_id TEXT PRIMARY KEY,
	kind         TEXT NOT NULL,
	signature    TEXT NOT NULL,
	state        TEXT NOT NULL
	             CHECK (state IN ('committed', 'refused')),
	-- byte-stable: an exact retry returns THIS, not a recomputation that
	-- might differ in member order
	result       TEXT,
	-- Review 2026-08-22 [P1]: this held only a MESSAGE, and replay then
	-- rebuilt every durable refusal as 'refused.precondition'. A durable
	-- 'policy.retention' came back with a different portable meaning and a
	-- different retry policy — the decision ran once, but the retry was not
	-- a replay of the same refusal. The whole sealed outcome is stored, so
	-- the first answer is REPRODUCED rather than re-derived.
	refusal      TEXT,
	settled_at   TEXT NOT NULL
) STRICT;

-- THE TRUSTED INTAKE DECISION.
--
-- Not one of the frozen axes, on purpose: the ten axes are the MANAGER's own
-- observations, and this is somebody else's decision that the manager merely
-- records. Nothing here reaches the authority.
--
-- RETENTION IS NOT ACCEPTANCE (SPEC 6.4). Whether intake wanted the material
-- and where the material went are two facts, so they are two columns; a
-- rejected draft that is retained under policy is an ordinary outcome and
-- collapsing them would make it unsayable.
--
-- The assignment is stored with the decision because a decision read under a
-- different generation is a decision about something else.
CREATE TABLE IF NOT EXISTS intake (
	runtime_attempt_id TEXT PRIMARY KEY
	                   REFERENCES attempts(runtime_attempt_id),
	-- WHICH MATERIAL WAS JUDGED. Review [P1]: the decision stored only a
	-- locator, so a restart could not prove which immutable result it
	-- concerned, and an attempt with no sealed output at all could be
	-- accepted or rejected. A locator is where something is.
	result_digest      TEXT NOT NULL REFERENCES manifests(digest),
	disposition        TEXT NOT NULL
	                   CHECK (disposition IN ('accepted', 'rejected')),
	retention          TEXT NOT NULL
	                   CHECK (retention IN ('retained', 'quarantined')),
	locator            TEXT NOT NULL,
	retain_until       TEXT,
	reason             TEXT,
	work_id            TEXT NOT NULL,
	authority_uuid     TEXT NOT NULL,
	participant        TEXT NOT NULL,
	generation         INTEGER NOT NULL,
	decided_at         TEXT NOT NULL
) STRICT;

-- Adapter observations, keyed by their FULL source scope.
--
-- Review 2026-08-22 [P1]: the key was '(runtime_attempt_id, source_seq)',
-- and the frozen contract scopes 'source_seq' to one adapter INCARNATION.
-- So an adapter restart — a valid new incarnation whose sequence begins
-- again at 1 — collided with the previous incarnation's sequence 1, and the
-- required restart path became indistinguishable from a conflicting
-- duplicate before any monotonic logic ran.
--
-- The source identity and the manager's own ordering are two different
-- facts and are stored as two: this key answers "have I seen THIS
-- observation", and 'manager_seq' carries the per-attempt monotonicity that
-- axis logic enforces separately.
CREATE TABLE IF NOT EXISTS observations (
	runtime_attempt_id TEXT NOT NULL REFERENCES attempts(runtime_attempt_id),
	incarnation        TEXT NOT NULL,
	source_seq         INTEGER NOT NULL,
	runtime_id         TEXT,
	-- the immutable digest of what was observed, which is what makes
	-- "the same observation again" answerable
	observation_digest TEXT NOT NULL,
	manager_seq        INTEGER NOT NULL,
	observed_at        TEXT NOT NULL,
	PRIMARY KEY (runtime_attempt_id, incarnation, source_seq)
) STRICT;
-- The manager's own sequence is unique PER ATTEMPT regardless of which
-- incarnation produced the observation: it is this manager's ordering, not
-- the adapter's.
CREATE UNIQUE INDEX IF NOT EXISTS observations_manager_seq
	ON observations (runtime_attempt_id, manager_seq);

-- THE FROZEN OUTPUT. Store surface item 7: an immutable freeze/result
-- record, its artifact references and their exact digests.
--
-- One row per attempt, and the PRIMARY KEY says so at the database
-- boundary. The manager operation journal decides replay-versus-collision
-- for the product path; this is what a store written some other way still
-- cannot violate.
-- THE RETAINED MANIFESTS, keyed by the digest that identifies them.
--
-- Review [P1]: the store held 'attempt.input_digest' and
-- 'outputs.manifest_digest' and not one byte of either document. Freeze
-- could not compare a sealed result against the output DECLARATIONS the
-- input manifest names, and intake, publication and restart were left with
-- a number and nothing to replay. Retention is idempotent by construction
-- because the key is computed from the bytes.
CREATE TABLE IF NOT EXISTS manifests (
	digest      TEXT PRIMARY KEY,
	schema      TEXT NOT NULL,
	-- RFC 8785 canonical bytes, so what comes back out is what went in
	body        TEXT NOT NULL,
	retained_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS outputs (
	runtime_attempt_id  TEXT PRIMARY KEY
	                    REFERENCES attempts(runtime_attempt_id),
	result_id           TEXT NOT NULL,
	-- the disposition the RESULT declares, which freeze already compared
	-- against the recorded worker_disposition axis
	disposition         TEXT NOT NULL,
	-- the sealed manifest digest this manager RECOMPUTED, not the one the
	-- document declared about itself
	-- the retained result manifest, by the digest this manager recomputed
	manifest_digest     TEXT NOT NULL REFERENCES manifests(digest),
	freeze_operation_id TEXT NOT NULL,
	frozen_at           TEXT NOT NULL
) STRICT;

-- The artifact REFERENCES, one row per declared output. Whether the bytes
-- match is a collection-time fact W2930 owns; that the reference is well
-- formed, digested and free of credentials is decided before it lands here.
CREATE TABLE IF NOT EXISTS output_artifacts (
	runtime_attempt_id TEXT NOT NULL REFERENCES outputs(runtime_attempt_id),
	output_name        TEXT NOT NULL,
	artifact_id        TEXT NOT NULL,
	media_type         TEXT NOT NULL,
	bytes              INTEGER NOT NULL,
	content_digest     TEXT NOT NULL,
	locator            TEXT NOT NULL,
	PRIMARY KEY (runtime_attempt_id, output_name)
) STRICT;
`;
