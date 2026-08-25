"""The manager control store's own schema, and the marker that says whose it is.

W4 cut B (PLAN item 4bc). Ported from the frozen Node `schema.mjs` by
obligation, carrying only the tables this cut needs: the metadata that
establishes ownership, and the manager's own operation journal. The state tables
-- offers, attempts, sessions, turns, events, intake, outputs -- arrive with the
cuts that give them meaning, because a table nothing writes is a claim about a
design rather than part of one.

THE STORE KIND IS THE POINT OF THE MARKER. This distribution ships an assignment
authority whose first schema version is also small, and three other SQLite files
sit beside it. "Version 1" is true of all of them, so a store that could only say
its version could be adopted by the wrong reader; the KIND is what makes the
question answerable, and it is checked before the version so a caller is told
their store is the wrong PRODUCT rather than sent to fix the wrong thing.

§4.2: THE MANAGER'S JOURNAL IS NOT THE AUTHORITY'S. Success at one boundary does
not imply success at the other, and reconciliation queries both exact records. So
this file describes a store the authority cannot open and does not share a
connection, transaction or schema with.
"""

from .boundaries import Column

__all__ = ["STORE_KIND", "SCHEMA_VERSION", "SCHEMA", "TABLES",
           "OFFER_COLUMNS", "OPERATION_COLUMNS", "OFFER_STATES",
           "OPERATION_STATES", "ATTEMPT_COLUMNS", "OBSERVATION_COLUMNS",
           "POSTURES", "SESSION_STATES", "SLOT_OCCUPANCY",
           "AGENT_SESSION_COLUMNS", "POSTURE_SLOT_COLUMNS"]

STORE_KIND = "baton.v12.python.worker-manager"

# Six. One; two, when the journal row invariant changed what a row is allowed
# to BE; three, when cut C added the offers table; four, because that table's
# all-five-or-none invariant is now ENFORCED rather than documented; five, when
# cut D added the attempt and its observations; six, when W6592's composition
# added the certified agent-session profile and its bytes. A store written under an earlier
# shape cannot hold what this build enforces, and keeping the number would let
# this build adopt one -- the "does not guess across versions" rule applied to my
# own changes rather than to somebody else's.
# Seven, because W6627 added the agent session and the posture slot it holds.
SCHEMA_VERSION = 7

TABLES = ("meta", "operations", "offers", "attempts", "observations",
          "profiles", "agent_sessions", "posture_slots")

# THE TWO POSTURES, and they are a third vocabulary rather than a subdivision
# of either axis below. `posture` says WHICH CONTAINER this is; the runtime
# axis says whether that container is up; the session state says whether the
# agent inside it can be prompted. W6627's revalidation: collapsing any two of
# the three is the two-live-sources-of-truth defect, and the reason to name
# them in one file is so a reader meets all three at once.
POSTURES = ("consent", "execution")

# The nine of frozen agent-session 1.0 `$defs.sessionState`, in the schema's
# own order. Taken as a vocabulary here because the DDL's CHECK and the adopted
# row's contract are the same statement in two languages; what may FOLLOW what
# is a different question and lives with the rule, in `sessions.py`.
SESSION_STATES = ("not-started", "initializing", "ready", "prompting",
                  "turn-ended", "cancel-requested", "agent-quiescent",
                  "unknown", "closed")

# POSTURE OCCUPANCY -- a MANAGER-OWNED axis, and deliberately not a projection
# of the nine above.
#
# Tying the two together is what made `closed` the only way to free a posture,
# and `closed` asserts a terminal fact was observed for every turn the epoch
# started. A session that died before it initialized has no such facts, so
# recovering capacity would have meant inventing knowledge. These three say
# only whether the posture may be used again, which nobody has to observe a
# provider to know.
SLOT_OCCUPANCY = ("available", "occupied", "recovery-required")

SCHEMA = """
CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT;

-- The MANAGER's own operation journal.
--
-- `signature` is the FULL effective signature of the operation and not its id:
-- §4.2 makes reusing an id with different operands `refused.operation-collision`
-- and changes nothing. Storing the signature is what lets that be decided from
-- the record rather than from the caller's account of it.
--
-- `result` is BYTE-STABLE. An exact retry returns these bytes' value, not a
-- recomputation that might differ in member order -- a result rebuilt from
-- current state would be a fresh answer wearing the first one's identity.
--
-- `refusal` holds the WHOLE SEALED OUTCOME rather than a message. The frozen
-- host stored only prose and replay then rebuilt every durable refusal as
-- `refused.precondition`, so a durable `policy.retention` came back with a
-- different portable meaning and a different retry policy. The decision ran
-- once; the retry was not a replay of the same refusal.
-- ONE SEALED OUTCOME PER ROW, enforced by the store rather than by whoever
-- writes it. Review [P2]: `state` was constrained and its payload columns were
-- not, so the table accepted a committed row with no result, a committed row
-- carrying a refusal, a refused row with no refusal, and a refused row carrying
-- a result. `_record` writes coherent rows -- and every action receives the same
-- connection, and later cuts add more writers. A durable store should reject
-- impossible state rather than leave replay to fail later or to reinterpret it.
--
-- JSON `null` is stored as the TEXT "null", so it stays distinct from SQL NULL:
-- "the committed result was null" and "there is no result" are different facts
-- here for the same reason `replay` answers presence separately from value.
CREATE TABLE operations (
    operation_id TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    signature    TEXT NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('committed', 'refused')),
    result       TEXT,
    refusal      TEXT,
    settled_at   TEXT NOT NULL,
    CHECK ((state = 'committed' AND result IS NOT NULL AND refusal IS NULL)
        OR (state = 'refused'   AND result IS NULL     AND refusal IS NOT NULL))
) STRICT;

-- THE OFFER: where a manager spends a bearer and takes a claim on somebody's
-- behalf. Every column here exists to answer one question after a crash -- what
-- actually happened?
--
-- `verifier` is stored and the BEARER NEVER IS. The bearer exists only in the
-- process that minted it; the store holds what proves possession of it, which
-- is why a replayed issue cannot answer with a usable secret and refuses
-- instead.
--
-- `intent_digest`, `claim_operation_id` and `claim_signature` are frozen at
-- ACCEPTANCE and never rewritten. The claim operation id is DERIVED from the
-- intent rather than minted, which is what makes a lost result settleable: the
-- next incarnation must be able to name the exact operation this one submitted
-- without having seen it submitted.
--
-- `incarnation` is which manager issued it. Several managers coordinate through
-- one store, so abandoning an offer merely because THIS process did not mint its
-- bearer would let one live manager destroy another's work.
CREATE TABLE offers (
    offer_id           TEXT PRIMARY KEY,
    work_id            TEXT NOT NULL,
    authority_uuid     TEXT NOT NULL,
    participant        TEXT NOT NULL,
    runtime_attempt_id TEXT NOT NULL,
    incarnation        TEXT NOT NULL,
    input_digest       TEXT NOT NULL,
    policy_digest      TEXT NOT NULL,
    profile_digest     TEXT NOT NULL,
    verifier           TEXT NOT NULL,
    verifier_spent     INTEGER NOT NULL DEFAULT 0
                       CHECK (verifier_spent IN (0, 1)),
    issued_at          TEXT NOT NULL,
    expires_at         TEXT NOT NULL,
    state              TEXT NOT NULL CHECK (state IN (
                           'issued', 'accepted', 'declined', 'expired',
                           'abandoned-after-restart', 'claimed',
                           'claim-refused', 'settlement-expired')),
    intent_digest      TEXT,
    accepted_at        TEXT,
    settle_by          TEXT,
    claim_operation_id TEXT,
    claim_signature    TEXT,
    claim_generation   INTEGER,
    decision_reason    TEXT,
    decided_at         TEXT,
    -- ACCEPTANCE FREEZES ALL FIVE OR NONE, and this is the CHECK that says so.
    --
    -- Review [P2]: the comment claimed all five and the constraint mentioned
    -- three, and it constrained only `issued` -- so the table accepted an
    -- `accepted` row with the five fields absent AND an `issued` row already
    -- carrying `accepted_at` and `settle_by`. A row that named a claim operation
    -- without the signature to settle it would be an identity nobody can retire,
    -- which is the shape the frozen host was corrected for; a row that carried
    -- acceptance fields without being accepted is the same thing arriving early.
    --
    -- The states divide cleanly: the ones a row can reach WITHOUT acceptance
    -- carry none of the five, and the ones only acceptance can lead to carry all
    -- five.
    CHECK (
        (state IN ('issued', 'declined', 'expired', 'abandoned-after-restart')
         AND intent_digest IS NULL AND accepted_at IS NULL
         AND settle_by IS NULL AND claim_operation_id IS NULL
         AND claim_signature IS NULL)
     OR (state IN ('accepted', 'claimed', 'claim-refused',
                   'settlement-expired')
         AND intent_digest IS NOT NULL AND accepted_at IS NOT NULL
         AND settle_by IS NOT NULL AND claim_operation_id IS NOT NULL
         AND claim_signature IS NOT NULL))
) STRICT;

-- ONE LIVE OFFER PER WORK. A partial index, because terminal offers are history
-- and history does not hold a slot.
CREATE UNIQUE INDEX offers_one_live_per_work
    ON offers (work_id) WHERE state IN ('issued', 'accepted');

-- THE RUNTIME ATTEMPT: what an accepted offer named, and where it got to.
--
-- The four assignment columns are NULL until activation FIXES them, and
-- activation fixes all four in one compare-and-swap -- §4 says an identity is
-- never three quarters of one, and a row that carried a Work and a generation
-- without the participant and the authority would be exactly that.
--
-- Every axis column is its own vocabulary with its own CHECK. What may FOLLOW
-- what is the transition map's, in `attempts.py`: a vocabulary lists what an
-- axis may say, and only a transition map says what may follow what.
CREATE TABLE attempts (
    runtime_attempt_id     TEXT PRIMARY KEY,
    adapter_name           TEXT NOT NULL,
    adapter_digest         TEXT NOT NULL,
    profile_digest         TEXT NOT NULL,
    input_digest           TEXT,
    policy_digest          TEXT,
    image_digest           TEXT,
    toolchain_digest       TEXT,
    created_at             TEXT NOT NULL,
    -- ACTIVATION FIXES ALL FOUR OR NONE.
    work_id                TEXT,
    authority_uuid         TEXT,
    assignment_participant TEXT,
    assignment_generation  INTEGER,
    runtime_id             TEXT,
    observation_seq        INTEGER NOT NULL DEFAULT 0,
    observed_at            TEXT,
    consent_runtime        TEXT NOT NULL DEFAULT 'not-started' CHECK (
        consent_runtime IN ('not-started', 'running', 'quiescent',
                            'uncertain', 'destroyed')),
    execution_runtime      TEXT NOT NULL DEFAULT 'not-started' CHECK (
        execution_runtime IN ('not-started', 'start-requested', 'running',
                              'cancel-requested', 'stopping', 'quiescent',
                              'uncertain', 'destroyed')),
    output                 TEXT NOT NULL DEFAULT 'open' CHECK (
        output IN ('open', 'freeze-requested', 'frozen', 'invalid', 'sealed',
                   'discarded')),
    worker_disposition     TEXT NOT NULL DEFAULT 'none' CHECK (
        worker_disposition IN ('none', 'completed', 'unable', 'plan-rejected',
                               'cancelled')),
    proposal               TEXT NOT NULL DEFAULT 'none' CHECK (
        proposal IN ('none', 'publish-requested', 'published', 'superseded')),
    verification           TEXT NOT NULL DEFAULT 'none' CHECK (
        verification IN ('none', 'passed', 'failed', 'unable')),
    technical_review       TEXT NOT NULL DEFAULT 'none' CHECK (
        technical_review IN ('none', 'accepted', 'changes-requested',
                             'rejected')),
    approval               TEXT NOT NULL DEFAULT 'none' CHECK (
        approval IN ('none', 'approved', 'denied')),
    integration            TEXT NOT NULL DEFAULT 'none' CHECK (
        integration IN ('none', 'integrated', 'failed')),
    cleanup                TEXT NOT NULL DEFAULT 'pending' CHECK (
        cleanup IN ('pending', 'blocked-on-intake', 'complete', 'retained',
                    'failed')),
    CHECK (
        (work_id IS NULL AND authority_uuid IS NULL
         AND assignment_participant IS NULL AND assignment_generation IS NULL)
     OR (work_id IS NOT NULL AND authority_uuid IS NOT NULL
         AND assignment_participant IS NOT NULL
         AND assignment_generation IS NOT NULL))
) STRICT;

-- ONE ATTEMPT PER CLAIMED OFFER. The offers table names its attempt, and two
-- claimed offers naming one attempt would make "which of these is this
-- attempt's claim" a question with no answer a manager may guess at.
CREATE UNIQUE INDEX offers_one_claim_per_attempt
    ON offers (runtime_attempt_id) WHERE state = 'claimed';

-- WHAT WAS OBSERVED, and BY WHOM under WHICH source identity.
--
-- `(runtime_attempt_id, incarnation, source_seq)` is the durable identity of an
-- observation: an exact duplicate replays, and a DIFFERENT observation reusing
-- that identity refuses. That is what makes "the same observation again"
-- answerable at all, and it is a fact about the identity rather than about
-- where the axis happens to be today.
CREATE TABLE observations (
    runtime_attempt_id TEXT NOT NULL,
    incarnation        TEXT NOT NULL,
    source_seq         INTEGER NOT NULL,
    runtime_id         TEXT,
    observation_digest TEXT NOT NULL,
    manager_seq        INTEGER NOT NULL,
    observed_at        TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, incarnation, source_seq)
) STRICT;

CREATE UNIQUE INDEX observations_manager_order
    ON observations (runtime_attempt_id, manager_seq);

-- THE CERTIFIED AGENT-SESSION PROFILE, and its BYTES rather than its digest
-- alone.
--
-- W6592: `certify_profile` recorded that a digest was certified and nothing
-- ever saw the document that digest named -- so a manager could act under a
-- profile whose contents no code in this distribution had read. A session must
-- pin the per-posture policy a profile carries, and a digest cannot be read for
-- it.
--
-- `withdrawn_at` is a column rather than a delete because withdrawing a
-- certification and never having certified one are different facts, and a row
-- that vanishes cannot tell them apart after the event.
--
-- (kind, name) is the identity and `digest` is not: recertifying the same
-- profile id under new bytes is one profile changing, not two profiles. The
-- digest is what a handshake names, so it is indexed for that lookup.
CREATE TABLE profiles (
    kind         TEXT NOT NULL,
    name         TEXT NOT NULL,
    digest       TEXT NOT NULL,
    body         TEXT NOT NULL,
    certified_at TEXT NOT NULL,
    withdrawn_at TEXT,
    PRIMARY KEY (kind, name)
) STRICT;

CREATE INDEX profiles_by_digest ON profiles (kind, digest);

-- ONE AGENT SESSION, in one posture, at one epoch.
--
-- W6627. The manager never resumes, forks or promotes a session, so the epoch
-- is always the next one for this (attempt, posture) and the primary key says
-- a given one exists at most once. Consent and execution count separately,
-- because they never share a connection either.
--
-- THE POSTURE BINDING IS A CHECK rather than a comment. Frozen agent-session
-- 1.0 makes `assignment_ref` exactly null for a consent session -- which
-- exists before any claim -- and exactly an assignment for an execution one.
-- A store that could hold a consent session carrying somebody's generation
-- would be a store in which the separation the two postures exist for is a
-- convention.
--
-- `provider_session_id` is NULL until the provider names one, and it is the
-- FOURTH component of the §3.1 reference that labels evidence. It is nullable
-- and it is still bound on every observation: a report naming provider session
-- B must not move the row held for A.
--
-- `state` defaults to `not-started` and no writer may set it here to anything
-- else: the axis is what moves it, through the one boundary that knows which
-- successors §7.3 permits.
CREATE TABLE agent_sessions (
    runtime_attempt_id  TEXT NOT NULL,
    posture             TEXT NOT NULL CHECK (
        posture IN ('consent', 'execution')),
    session_epoch       INTEGER NOT NULL CHECK (session_epoch >= 1),
    profile_digest      TEXT NOT NULL,
    pinned_policy       TEXT NOT NULL,
    work_id             TEXT NOT NULL,
    authority_uuid      TEXT NOT NULL,
    participant         TEXT,
    generation          INTEGER,
    provider_session_id TEXT,
    state               TEXT NOT NULL DEFAULT 'not-started' CHECK (
        state IN ('not-started', 'initializing', 'ready', 'prompting',
                  'turn-ended', 'cancel-requested', 'agent-quiescent',
                  'unknown', 'closed')),
    opened_at           TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, posture, session_epoch),
    CHECK (
        (posture = 'consent'   AND participant IS NULL
                               AND generation IS NULL)
     OR (posture = 'execution' AND participant IS NOT NULL
                               AND generation IS NOT NULL))
) STRICT;

-- THE POSTURE SLOT: may this posture be used, and by which epoch.
--
-- W6627, and it is a separate table because it is a separate axis. Occupancy
-- is taken by a compare-and-set against `available` INSIDE the transaction
-- that writes the session row, so the database decides concurrency rather than
-- a read: an occupied posture with no session, or a session holding no
-- posture, would each be a stranding of their own.
--
-- `session_epoch` names WHICH epoch the slot is about, so evidence about one
-- epoch can never move or free the epoch that replaced it. It stays after a
-- release, because "available, and epoch 3 was the last to hold it" is a fact
-- a reader wants; only a posture nobody has ever used has none.
CREATE TABLE posture_slots (
    runtime_attempt_id TEXT NOT NULL,
    posture            TEXT NOT NULL CHECK (
        posture IN ('consent', 'execution')),
    occupancy          TEXT NOT NULL CHECK (
        occupancy IN ('available', 'occupied', 'recovery-required')),
    session_epoch      INTEGER CHECK (
        session_epoch IS NULL OR session_epoch >= 1),
    reason             TEXT,
    changed_at         TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, posture),
    -- A slot that is HELD names its holder. Only a posture nobody has used is
    -- allowed to name nobody, and that is exactly the `available` row the
    -- first occupancy creates.
    CHECK (occupancy = 'available' OR session_epoch IS NOT NULL)
) STRICT;
"""


# -- what a persisted row must BE when it is read back ------------------------
#
# PLAN 4bz names the store a receiving trust domain, and until this round it had
# no owner at all: `SELECT *` produced a dict that was handed on as trusted
# internal data. A persisted `settle_by` of `not-an-instant` was therefore
# COMPARED against the current instant and the claim continued as though the
# deadline were valid.
#
# THE CONTRACT LIVES BESIDE THE DDL because it is the same statement twice, in
# the two vocabularies each end can enforce. The CHECK constraint binds what THIS
# build writes; an adopted row is by definition one some other process wrote, and
# the two are different facts however identical the text. Keeping them adjacent
# is what makes a drift between them visible to a reader.
#
# NOT A RE-STATEMENT OF THE ROW INVARIANTS. The all-five-or-none CHECK is a
# relationship BETWEEN columns and stays in SQL, where the store enforces it on
# every writer including a future one. These say what each column IS.

OFFER_STATES = ("issued", "accepted", "declined", "expired",
                "abandoned-after-restart", "claimed", "claim-refused",
                "settlement-expired")

OPERATION_STATES = ("committed", "refused")

OFFER_COLUMNS = {
    "offer_id": Column("identity"),
    "work_id": Column("identity"),
    "authority_uuid": Column("text"),
    "participant": Column("text"),
    "runtime_attempt_id": Column("text"),
    "incarnation": Column("text"),
    "input_digest": Column("text"),
    "policy_digest": Column("text"),
    "profile_digest": Column("text"),
    "verifier": Column("text"),
    "verifier_spent": Column("flag"),
    "issued_at": Column("instant"),
    "expires_at": Column("instant"),
    "state": Column("text", allowed=OFFER_STATES),
    # The five acceptance freezes, and the three a decision writes. Nullable
    # here because the STATE decides whether they are present, and that
    # relationship is the SQL CHECK's to enforce rather than this table's.
    "intent_digest": Column("text", nullable=True),
    "accepted_at": Column("instant", nullable=True),
    "settle_by": Column("instant", nullable=True),
    "claim_operation_id": Column("text", nullable=True),
    "claim_signature": Column("text", nullable=True),
    "claim_generation": Column("count", nullable=True),
    "decision_reason": Column("text", nullable=True),
    "decided_at": Column("instant", nullable=True),
}

OPERATION_COLUMNS = {
    "operation_id": Column("identity"),
    "kind": Column("text"),
    "signature": Column("text"),
    "state": Column("text", allowed=OPERATION_STATES),
    # PROVED TO DECODE where the row is read, and handed back as the bytes that
    # were stored. Replay is byte-stable, so the value a retry receives is
    # derived from these exact bytes rather than from a re-encoding -- and a
    # result that no longer decodes is caught at the read instead of in the one
    # function whose whole job is handing a retry the first answer.
    "result": Column("json", nullable=True),
    # AND WHAT IT MEANS, at the read. A sealed refusal IS the closed portable
    # pair, and replay reproduces it rather than rebuilding one -- so the whole
    # document, its field types and the §9 pairing are proved here, which is
    # what lets the replay path use it as an owned value instead of adopting
    # the same bytes a second time.
    "refusal": Column("refusal", nullable=True),
    "settled_at": Column("instant"),
}


ATTEMPT_AXES = ("consent_runtime", "execution_runtime", "output",
                "worker_disposition", "proposal", "verification",
                "technical_review", "approval", "integration", "cleanup")

ATTEMPT_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "adapter_name": Column("text"),
    "adapter_digest": Column("text"),
    "profile_digest": Column("text"),
    "input_digest": Column("text", nullable=True),
    "policy_digest": Column("text", nullable=True),
    "image_digest": Column("text", nullable=True),
    "toolchain_digest": Column("text", nullable=True),
    "created_at": Column("instant"),
    # The four activation fixes, together or not at all -- the relationship is
    # the SQL CHECK's, and what each one IS is this table's.
    "work_id": Column("identity", nullable=True),
    "authority_uuid": Column("text", nullable=True),
    "assignment_participant": Column("text", nullable=True),
    "assignment_generation": Column("count", nullable=True),
    "runtime_id": Column("text", nullable=True),
    "observation_seq": Column("count"),
    "observed_at": Column("instant", nullable=True),
}

# The axis columns, added by the same vocabulary the DDL constrains. Written
# from one source rather than twice: a vocabulary spelled out in two places is
# two vocabularies that agree until they do not.
for _axis, _values in {
        "consent_runtime": ("not-started", "running", "quiescent", "uncertain",
                            "destroyed"),
        "execution_runtime": ("not-started", "start-requested", "running",
                              "cancel-requested", "stopping", "quiescent",
                              "uncertain", "destroyed"),
        "output": ("open", "freeze-requested", "frozen", "invalid", "sealed",
                   "discarded"),
        "worker_disposition": ("none", "completed", "unable", "plan-rejected",
                               "cancelled"),
        "proposal": ("none", "publish-requested", "published", "superseded"),
        "verification": ("none", "passed", "failed", "unable"),
        "technical_review": ("none", "accepted", "changes-requested",
                             "rejected"),
        "approval": ("none", "approved", "denied"),
        "integration": ("none", "integrated", "failed"),
        "cleanup": ("pending", "blocked-on-intake", "complete", "retained",
                    "failed"),
}.items():
    ATTEMPT_COLUMNS[_axis] = Column("text", allowed=_values)

OBSERVATION_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "incarnation": Column("text"),
    "source_seq": Column("count"),
    "runtime_id": Column("text", nullable=True),
    "observation_digest": Column("text"),
    "manager_seq": Column("count"),
    "observed_at": Column("instant"),
}

# W6627. The posture/assignment relationship is a relationship BETWEEN columns
# and stays in SQL, where the store enforces it on every writer; these say what
# each column IS when this build reads a row somebody else wrote.
AGENT_SESSION_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "posture": Column("text", allowed=POSTURES),
    "session_epoch": Column("count"),
    "profile_digest": Column("text"),
    "pinned_policy": Column("text"),
    "work_id": Column("identity"),
    "authority_uuid": Column("text"),
    "participant": Column("text", nullable=True),
    "generation": Column("count", nullable=True),
    "provider_session_id": Column("text", nullable=True),
    "state": Column("text", allowed=SESSION_STATES),
    "opened_at": Column("instant"),
}

POSTURE_SLOT_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "posture": Column("text", allowed=POSTURES),
    "occupancy": Column("text", allowed=SLOT_OCCUPANCY),
    "session_epoch": Column("count", nullable=True),
    "reason": Column("text", nullable=True),
    "changed_at": Column("instant"),
}
