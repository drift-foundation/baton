"""The v12 Python authority's durable schema.

This is a SELF-CONTAINED store.  It is not the v11 authority, it is not the
Node v12 authority, it is not the Worker Manager control store, and it is not a
migration of any of them.  Nothing here opens `work.sqlite3` or imports
`src/baton_work/`.

What the AUTHORITY owns is fixed by §3 and the table list is the whole
argument: Work state, the per-Work contract selector, the generation counter,
the live assignment, fenced generations, the one typed gate, assignment-ending
and contract events, gate evidence, proposal and workflow receipts, and the
operation journal.  Offers, runtime attempts, quarantined output and runtime
observations are the Worker Manager control store's and are deliberately
absent -- an authority that also stored them would be answering questions it is
not authoritative for.

THE STORE KIND IS WHY THIS SCHEMA IS NOT ENOUGH ON ITS OWN.  The frozen Node
authority also calls its first schema version `1`, and both are SQLite files
holding a table called `meta`.  A version number alone therefore cannot tell
"my store, version 1" from "somebody else's store, version 1", and the failure
mode is not an error -- it is silent adoption.  So every store this module
creates records WHOSE it is before it records how old it is, and the open path
checks the kind first.
"""

__all__ = ["STORE_KIND", "SCHEMA_VERSION", "SCHEMA", "META_STORE_KIND",
           "META_SCHEMA_VERSION", "META_AUTHORITY_UUID"]

# The marker that makes this store recognizably ours.  It names the host, the
# product and the role, because "v12" alone would still be ambiguous between
# the Node authority, this one and the manager's control store.
STORE_KIND = "baton.v12.python.authority"

# W16821 raised this from 1 to 2.  Schema 2 SEPARATES the principal from the
# endpoint address, gives Work an authority-owned effective scope, keys claim
# capacity by principal, and records the authorization decision beside the acts
# it authorized.  A schema-1 store holds none of those facts and nothing in it
# could supply them: approver ruling M33752 makes this a CLEAN INITIALIZATION
# BOUNDARY for disposable proof stores rather than a migration, and
# `store._check_compatibility` refuses the older file read-only and tells the
# operator to initialize a fresh one.
# W29400 raised this from 2 to 3 for the Work-label model: the live set, its
# append-only mutation evidence, and the inverse index the exact filters read.
# Approver ruling M33752 makes each version a CLEAN INITIALIZATION BOUNDARY for
# these disposable proof stores, so this is a version bump and not a migration
# -- which is the schema disposition W29400's own record says must be derived
# at implementation time rather than decided by its decomposition.
# W16823 raised this from 3 to 4, and NO TABLE CHANGED -- which is the whole
# reason the bump has to be argued rather than derived from a diff.  `claim`
# now answers a CLOSED RESULT: the unchanged four-part assignment, the exact
# immutable claim event, and the decision the claim was authorized under.  The
# operation journal retains a committed result whole and replays it byte for
# byte, so a schema-3 journal can hold the OLD BARE ASSIGNMENT and this build
# would hand it to a manager reading it as the new closed document -- a missing
# `decision` discovered at a member lookup rather than at the open.  Versioning
# the RESULT CONTRACT is exactly what the version is for; approver ruling
# M35002 allocates 4 as the cumulative shape after W29400's 3, and no later
# Work may lower or independently reuse it.
#
# W29400, approver ruling M35127: FIVE is the cumulative clean-initialization
# boundary after W16823's 4, and it is allocated ONCE -- here, with the
# creation pipeline it is the boundary for. A Work-label store written under 4
# has no attributable creation act and no `work-create` decision to join a
# create-time label event to, so a build that required them could not adopt
# one; the version is what says so instead of a member lookup discovering it.
#
# The disposition is clean initialization rather than migration, on M33752's
# still-current rule for this disposable proof store: 5 is not reused, not
# lowered, and not reached by upgrading a 4.
SCHEMA_VERSION = 5

META_STORE_KIND = "store_kind"
META_SCHEMA_VERSION = "schema_version"
META_AUTHORITY_UUID = "authority_uuid"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT;

-- Deployment policy.  These are configured facts shared by every Work: which
-- contracts a certified runtime profile can execute, which contract
-- transitions are permitted at all, and the pinned isolation and retention
-- clauses §10.8/§10.9 refer to.
CREATE TABLE IF NOT EXISTS certified_contract (
    contract     TEXT PRIMARY KEY,
    profile      TEXT NOT NULL,
    certified_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS contract_transition (
    from_contract TEXT NOT NULL,
    to_contract   TEXT NOT NULL,
    PRIMARY KEY (from_contract, to_contract)
) STRICT;

CREATE TABLE IF NOT EXISTS policy (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT;

-- The configuration generation every authorization decision is taken under
-- (§5 of the correction boundary).  ONE ROW, enforced by the primary key
-- check: a table that could hold two generations would have no answer to
-- "which one is current".
--
-- Kept OUT of `policy`, which `set_policy` lets a deployment write freely: a
-- generation a caller could set is a generation a caller could rewind, and an
-- act's recorded provenance would then name a configuration that never
-- existed.
CREATE TABLE IF NOT EXISTS policy_generation (
    one        INTEGER PRIMARY KEY CHECK (one = 1),
    generation INTEGER NOT NULL CHECK (generation >= 1),
    bumped_at  TEXT NOT NULL
) STRICT;

-- W16821.  THE CANONICAL GLOBAL IDENTITY an act is attributed to, separate
-- from the endpoint address it was performed through.
--
-- Two tables rather than a column on `route_handler`, because the mapping is
-- MANY endpoints to ONE principal and that is the whole point: two spellings
-- of one person received two claim slots, and one spelling could not say which
-- scope and which grant authorized an act.
CREATE TABLE IF NOT EXISTS principal (
    principal_id  TEXT PRIMARY KEY,
    registered_at TEXT NOT NULL
) STRICT;

-- The deployment mapping.  The AUTHORITY owns it: a caller names an endpoint
-- and never a principal, so no operand anywhere can choose or widen the
-- identity an act is attributed to.
CREATE TABLE IF NOT EXISTS endpoint (
    participant  TEXT PRIMARY KEY,
    principal_id TEXT NOT NULL,
    bound_at     TEXT NOT NULL,
    FOREIGN KEY (principal_id) REFERENCES principal (principal_id)
) STRICT;

-- One row per Work.  phase is the closed scheduler axis and is NULL exactly
-- when the Work is terminal; gate is the ONE typed gate v11 already displays,
-- never a second axis (§10.7).
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
    -- W16821 item 2.  The effective scope this Work's authorizations are
    -- decided in.  NOT NULL and supplied at creation through the trusted
    -- bootstrap: the correction boundary forbids deriving it from route,
    -- repository or participant spelling, and a nullable column would be a
    -- standing invitation to derive it later "just for the rows that are
    -- missing it".
    scope              TEXT NOT NULL,
    created_at         TEXT NOT NULL
) STRICT;

-- W29400: THE LIVE LABEL SET.  One row per Work per canonical label, so the
-- set is the table rather than a parsed column, and `(work_id, label)` is the
-- uniqueness the contract calls set semantics.
--
-- NO ORDER COLUMN.  A set has no order; the projection sorts, which is what
-- makes two Works with the same labels project identically however they were
-- supplied.
CREATE TABLE IF NOT EXISTS work_label (
    work_id  TEXT NOT NULL,
    label    TEXT NOT NULL,
    added_at TEXT NOT NULL,
    PRIMARY KEY (work_id, label),
    FOREIGN KEY (work_id) REFERENCES work (work_id)
) STRICT;

-- THE INVERSE, because the filters ask "which Work carries this label" and the
-- primary key only answers the other direction.  An exact-membership predicate
-- over a missing index is a scan that gets slower as the deployment grows,
-- and this feature exists to be filtered by.
CREATE INDEX IF NOT EXISTS work_label_by_label
    ON work_label (label, work_id);

-- APPEND-ONLY MUTATION EVIDENCE.  Every EFFECTIVE addition and removal, in
-- order.  A convergent no-op writes nothing here: the contract says adding a
-- present label returns `changed:false` and fabricates no event, because an
-- event that records nothing having happened makes the history unable to say
-- what did.
--
-- The AUTHORIZATION EVIDENCE is not repeated in these columns.  W16821 owns
-- one decision shape in `authorization_decision`, keyed by the act, and this
-- journal names its act rather than carrying a second provisional spelling of
-- endpoint, principal, scope, grant and policy generation -- which is what the
-- parent record asks for in terms.
CREATE TABLE IF NOT EXISTS work_label_event (
    seq     INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id TEXT NOT NULL,
    label   TEXT NOT NULL,
    action  TEXT NOT NULL CHECK (action IN ('added', 'removed')),
    act_id  TEXT NOT NULL,
    at      TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS route_handler (
    route       TEXT NOT NULL,
    participant TEXT NOT NULL,
    PRIMARY KEY (route, participant)
) STRICT;

-- Configured capabilities.  §7 names a distinct actor for the receipt
-- transitions -- verifier, rview, approv, trusted integrator -- and an
-- authorized actor holding the close capability.  Without this, one consumer
-- could publish a candidate, self-verify it, self-review it, self-approve it,
-- integrate it into the canonical target and close the Work, because the
-- receipts stored dispositions and no actor at all.
--
-- A deployment MAY grant one participant several of these: §10.12 says the four
-- receipts stay distinct even when configuration permits one participant to
-- hold more than one role.  What it may not do is leave the question unasked,
-- which is what an actorless receipt does.
--
-- W16821: THE GRANTEE IS THE PRINCIPAL, not an endpoint address.  A grant held
-- by a spelling is a grant a second spelling of the same person does not have,
-- and the deployment could not say so.
--
-- `provenance` admits the whole vocabulary the M6 resolver will need --
-- `direct`, `inherited`, `masked` -- because a durable column that could not
-- hold an inherited grant would have to be migrated to gain one.  What this
-- cut may WRITE is only `direct`, and that restriction lives in the code where
-- a case can remove it and see the suite fail; a CHECK naming one value would
-- have made "the shape admits inheritance" false.
CREATE TABLE IF NOT EXISTS capability (
    principal_id TEXT NOT NULL,
    capability   TEXT NOT NULL,
    scope        TEXT NOT NULL,
    provenance   TEXT NOT NULL CHECK (provenance IN
                   ('direct', 'inherited', 'masked')),
    granted_at   TEXT NOT NULL,
    PRIMARY KEY (principal_id, capability, scope),
    FOREIGN KEY (principal_id) REFERENCES principal (principal_id)
) STRICT;

-- Fenced generations are retained forever with their cause: §10.1 says the
-- counter is never decremented or reused, and the fence is how a late act by an
-- ended generation is refused rather than ignored.
CREATE TABLE IF NOT EXISTS fenced_generation (
    work_id    TEXT NOT NULL,
    generation INTEGER NOT NULL,
    cause      TEXT NOT NULL,
    reason     TEXT,
    fenced_at  TEXT NOT NULL,
    PRIMARY KEY (work_id, generation),
    FOREIGN KEY (work_id) REFERENCES work (work_id)
) STRICT;

-- Deployment-wide capacity (§10.2).  Making this per Work is the bug the table
-- shape forbids -- and W16821 corrects WHOSE capacity it is.
--
-- THE PRINCIPAL IS THE KEY.  One principal holds at most one live claim across
-- the whole deployment, across every endpoint address it acts through.  Keyed
-- by participant, two spellings of one person received two slots, which is a
-- capacity limit that the person it limits can opt out of by being addressed
-- differently.
--
-- The endpoint is kept BESIDE it, not dropped: the Handler, the fence and the
-- assignment identity are all still endpoint-addressed, and a slot that could
-- not say which address took it could not release the right one.
CREATE TABLE IF NOT EXISTS claim_slot (
    principal_id TEXT PRIMARY KEY,
    participant  TEXT NOT NULL,
    work_id      TEXT NOT NULL,
    generation   INTEGER,
    taken_at     TEXT NOT NULL,
    FOREIGN KEY (principal_id) REFERENCES principal (principal_id)
) STRICT;

-- The operation journal.  An identity is durably in exactly one of four states;
-- UNSUBMITTED is the absence of a row (§4).
CREATE TABLE IF NOT EXISTS operation (
    operation_id TEXT PRIMARY KEY,
    signature    TEXT NOT NULL,
    state        TEXT NOT NULL CHECK (state IN ('committed', 'refused', 'retired')),
    result       TEXT,
    detail       TEXT,
    recorded_at  TEXT NOT NULL
) STRICT;

-- W16821 item 5: THE AUTHORIZATION DECISION, IN ONE TABLE.
--
-- The first cut of this correction put four nullable columns on
-- `assignment_event` and three more on `receipt`, and review found what that
-- shape costs: `close` writes neither row, so an authorized close persisted no
-- decision at all, and every act that gained a door would have needed its own
-- copy of the same four columns.  One table, one shape, one writer.
--
-- IMMUTABLE BY ITS PRIMARY KEY.  A decision is what the authority answered at
-- the instant it authorized one act; a second write for the same act would be
-- a second answer to a question that was already decided.
--
-- `act` and `act_id` name the exact act rather than the Work: a claim is keyed
-- by the assignment event it authorized, a close by its Work, each receipt by
-- its own identity, and a durably journalled refused integration attempt by
-- its own row.  Keying a claim by Work would collide the moment a released
-- Work was claimed again.
--
-- ASSIGNMENT-DERIVED ACTS ARE NOT LISTED HERE and that is deliberate: an
-- activity, a contract event and a proposal are carried out UNDER an
-- assignment that was already authorized, so the decision they were performed
-- under is the claim's.  They join to it through the full exact assignment
-- identity rather than copying it, because two copies of one fact are two
-- things that can disagree.
CREATE TABLE IF NOT EXISTS authorization_decision (
    act               TEXT NOT NULL,
    act_id            TEXT NOT NULL,
    endpoint          TEXT NOT NULL,
    principal_id      TEXT NOT NULL,
    effective_scope   TEXT NOT NULL,
    role              TEXT NOT NULL,
    grant_provenance  TEXT NOT NULL CHECK (grant_provenance IN
                        ('direct', 'inherited', 'masked')),
    policy_generation INTEGER NOT NULL,
    decided_at        TEXT NOT NULL,
    PRIMARY KEY (act, act_id),
    FOREIGN KEY (principal_id) REFERENCES principal (principal_id)
) STRICT;

CREATE TABLE IF NOT EXISTS assignment_event (
    seq               INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id           TEXT NOT NULL,
    participant       TEXT NOT NULL,
    generation        INTEGER,
    cause             TEXT NOT NULL,
    fenced            INTEGER NOT NULL,
    reason            TEXT,
    gate              TEXT,
    phase             TEXT,
    at                TEXT NOT NULL
);

-- `claim_seq` IS THE EXACT CLAIM THIS ACT WAS CARRIED OUT UNDER.
--
-- W16821 re-review [P0]: the projection joined back to a claim by
-- `(work_id, participant, generation)` and took the newest match.  That tuple
-- distinguishes v12 claims because they mint generations -- and a v11
-- assignment has NO generation, so releasing and reclaiming through the same
-- endpoint produced two distinct claim acts with identical join fields.  The
-- second claim then became the apparent authorization of the FIRST act's
-- history, without that act or its decision row being touched.
--
-- A nullable tuple, an instant and a newest-row ordering are not an identity.
-- The assignment event's own `seq` is, and it is captured at the moment of the
-- act rather than searched for afterwards.
CREATE TABLE IF NOT EXISTS contract_event (
    seq           INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id       TEXT NOT NULL,
    from_contract TEXT NOT NULL,
    to_contract   TEXT NOT NULL,
    participant   TEXT NOT NULL,
    generation    INTEGER,
    claim_seq     INTEGER NOT NULL,
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

-- Canonical activity carried out under an exact assignment.  Unique on the
-- assignment plus the caller's key, so a retry is the same row.
CREATE TABLE IF NOT EXISTS activity (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id     TEXT NOT NULL,
    participant TEXT NOT NULL,
    generation  INTEGER,
    claim_seq   INTEGER NOT NULL,
    action_key  TEXT NOT NULL,
    at          TEXT NOT NULL
);

-- IFNULL, not a plain UNIQUE: SQLite treats NULLs as distinct in a unique
-- index, so a v11 assignment (which mints no generation) would insert the same
-- activity twice and the idempotency key would silently stop working.
CREATE UNIQUE INDEX IF NOT EXISTS activity_key
    ON activity (work_id, participant, IFNULL(generation, -1), action_key);

-- The immutable candidate.
--
-- §10.11 requires the receipt to bind the exact assignment AND the input,
-- policy, output, candidate-tree and target digests; §4 adds the frozen result
-- identity and its content digest.  One undifferentiated digest column bound
-- none of that, so a proposal could not say what it was built FROM.  Every
-- digest is required and every one rides the publish operation signature,
-- because later bytes are a new proposal rather than an edit to this one.
CREATE TABLE IF NOT EXISTS proposal (
    proposal_id      TEXT PRIMARY KEY,
    work_id          TEXT NOT NULL,
    participant      TEXT NOT NULL,
    generation       INTEGER,
    claim_seq        INTEGER NOT NULL,
    result_id        TEXT NOT NULL,
    result_digest    TEXT NOT NULL,
    candidate_digest TEXT NOT NULL,
    input_digest     TEXT NOT NULL,
    policy_digest    TEXT NOT NULL,
    target           TEXT NOT NULL,
    published_at     TEXT NOT NULL
) STRICT;

-- The four separately attributable IMMUTABLE receipts (§10.12).
--
-- Rows rather than columns on the proposal, because each carries its own
-- identity, its own actor, and the candidate digest and target revision it was
-- written against.  A receipt that was only a disposition string could not say
-- who attributed it or what they saw.
--
-- kind is UNIQUE per proposal: that is the immutability rule, enforced by the
-- index rather than by a check somebody can forget.
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
    -- W16821: `actor` stays and is the ENDPOINT that wrote this receipt --
    -- §10.12's separate attributability is about addresses a deployment
    -- configures.  Which principal that address resolved to, in which scope
    -- and by which grant is the DECISION, and it lives in
    -- `authorization_decision` keyed by this receipt's own identity rather
    -- than in three more columns here.
    recorded_at       TEXT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES proposal (proposal_id)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS receipt_one_per_kind
    ON receipt (proposal_id, kind);

-- A refused integration is journalled ONCE beside the proposal and never
-- rewrites a committed receipt (§7).
-- W16821 review [P0]: a refused integration attempt is a DURABLE, separately
-- attributable act -- it journals an authorized actor and its operation
-- identity commits -- so it carries the decision that authorized it like any
-- other.  `attempt_id` is what the decision is keyed by; the autoincrement
-- `seq` is an ordering and is not an identity a second table can name
-- stably.
CREATE TABLE IF NOT EXISTS integration_attempt (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id  TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    actor       TEXT NOT NULL,
    reason      TEXT NOT NULL,
    target      TEXT NOT NULL,
    at          TEXT NOT NULL
);
"""
