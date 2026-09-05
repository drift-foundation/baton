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
           "AGENT_SESSION_COLUMNS", "POSTURE_SLOT_COLUMNS",
           "RUNTIME_LANE_COLUMNS",
           "OUTPUT_STATUSES", "OUTPUT_TYPES", "DISPOSITIONS",
           "CLAIM_CONTEXT",
           "MANIFEST_COLUMNS", "OUTPUT_COLUMNS", "OUTPUT_ARTIFACT_COLUMNS",
           "INTERROGATION_KINDS", "INTERROGATION_OUTCOMES",
           "INTERROGATION_COLUMNS",
           # W6629. Every other table's column contract and closed vocabulary
           # is declared here, and intake's four were reachable only as module
           # attributes -- which is a different promise from the one this list
           # makes. Nothing failed because of it, and that is the observation
           # worth keeping: this module has no gate comparing what it defines
           # to what it declares, so the omission was invisible.
           "CUSTODY", "RETENTION_DISPOSITIONS", "INTAKE_COLUMNS",
           "INTAKE_ARTIFACT_COLUMNS", "RETENTION_COLUMNS"]

STORE_KIND = "baton.v12.python.worker-manager"

# Six. One; two, when the journal row invariant changed what a row is allowed
# to BE; three, when cut C added the offers table; four, because that table's
# all-five-or-none invariant is now ENFORCED rather than documented; five, when
# cut D added the attempt and its observations; six, when W6592's composition
# added the certified agent-session profile and its bytes. A store written under an earlier
# shape cannot hold what this build enforces, and keeping the number would let
# this build adopt one -- the "does not guess across versions" rule applied to my
# own changes rather than to somebody else's.
# Seven, because W6627 added the agent session and the posture slot it holds;
# eight, because W6628 added the retained manifests a declaration is compared
# against and the frozen result those declarations answer; nine, because
# W6627's confirmed interrogation split needs a durable lifecycle of its own.
# Eleven, because W6629 added the intake receipt, the artifacts this manager
# took custody of, and the retention decisions cleanup is authorized by.
# TWELVE, because W16823 persists the AUTHORIZATION CONTEXT the authority's
# closed claim result now carries: the exact claim event, and the principal,
# effective scope, role, grant provenance and policy generation the claim was
# authorized under. A schema-11 store holds a claimed offer and an activated
# attempt with NO context and no way to supply one -- the decision it was
# taken under is at the authority, keyed by an event identity this build would
# have to guess. Approver ruling M35002 keeps this a clean initialization
# boundary rather than a migration.
# THIRTEEN, because W32649 adds the RUNTIME LANE: one capacity identity that
# spans a predecessor and a successor attempt, keyed by the assignment's
# authority, Work, canonical principal and effective scope rather than by an
# attempt id that changes with every attempt. A schema-12 store holds no lane
# at all, so a manager reading one would believe every lane free -- and the
# state this exists to prevent is precisely two executions over one
# assignment's material.
# FOURTEEN, because W61599 adds the DEFAULT LIVENESS PROJECTION: how many bytes
# of a worker's native session stream this manager has OBSERVED, and the
# manager's own receipt instant for the latest of them. A schema-13 store has
# nowhere to put either, so a manager reading one could only answer "unknown"
# for every attempt -- and the whole point of the projection is that an
# operator can tell a wedged worker from a working one without opening its
# container. The two columns are diagnostic and carry no content: M61707 keeps
# them out of every decision, so nothing that was authorized under schema 13 is
# authorized differently under 14.
#
# 15 ADDS THE NOMINATED SOURCE'S OBJECT IDENTITY (W71917). Two nullable
# diagnostic-shaped columns that one gate reads: a restarted manager compares
# the source it re-nominates against the object an earlier incarnation proved,
# and refuses a directory replaced while it was down. Nothing authorized under
# 14 is authorized differently under 15; what changes is that one refusal
# survives a restart instead of being forgotten with the process.
#
# 16 ADDS THE WRITABLE WORKSPACE'S OBJECT IDENTITY (W71917), and it is a
# separate version rather than an amendment to 15 because a 15 store cannot
# answer the question. 15 pinned the nominated SOURCE and left the workspace
# with only its pathname, so a real directory created at that pathname was
# adopted with nothing to compare it against -- and the workspace is the root
# an assignment's answer is collected out of. The two new columns are the
# same shape and the same non-content rule as 15's, and the table's CHECK ties
# all four together so no row can hold one root's object and not the other's.
# Nothing authorized under 15 is authorized differently under 16; what changes
# is that the second refusal survives a restart too.
#
# THERE IS NO MIGRATION, and that is this store's standing contract rather than
# an omission here: `ControlStore` refuses a database at another schema because
# it "does not guess across versions". This finding's rollout boundary already
# requires fresh Job and control stores for production acceptance.
SCHEMA_VERSION = 16

TABLES = ("meta", "operations", "offers", "attempts", "observations",
          "profiles", "agent_sessions", "posture_slots", "manifests",
          "outputs", "output_artifacts", "interrogations", "intakes",
          "intake_artifacts", "retentions", "runtime_lanes")

# THE TWO OPERATOR INTERROGATIONS, and they are two because v11's `poke`
# conflated two facts: whether the adapter and session can be OBSERVED now,
# and whether a model has accepted and answered a new conversational request.
#
#   probe    an immediate control-plane observation. It requires and consumes
#            no model turn.
#   inquire  a conversational request to the agent. The acknowledgement and
#            the eventual answer are two separate facts.
INTERROGATION_KINDS = ("probe", "inquire")

# WHAT MAY FOLLOW WHAT, per kind. Two tables rather than one plus conditionals,
# for the reason the runtime axes are two: a probe is never queued and an
# inquire is never merely observed, and one merged table would admit both.
#
# `timed-out` IS NOT TERMINAL, and that is the ruling rather than an oversight.
# A timeout is an OBSERVATION -- it says the manager stopped waiting, not that
# the work stopped or that anybody may discard it -- so a model that answers
# afterwards is answering, and the axis has to be able to say so. An axis that
# made `timed-out` terminal would turn the manager's patience into a decision
# about somebody else's turn.
INTERROGATION_OUTCOMES = {
    "probe": {
        "requested": ("observed", "timed-out", "adapter-unreachable",
                      "runtime-absent"),
        "timed-out": ("observed",),
        "observed": (), "adapter-unreachable": (), "runtime-absent": (),
    },
    "inquire": {
        "requested": ("queued", "delivered", "timed-out",
                      "adapter-unreachable", "runtime-absent"),
        "queued": ("delivered", "answered", "timed-out",
                   "adapter-unreachable", "runtime-absent"),
        "delivered": ("answered", "timed-out", "adapter-unreachable",
                      "runtime-absent"),
        "timed-out": ("answered",),
        "answered": (), "adapter-unreachable": (), "runtime-absent": (),
    },
}

_INTERROGATION_STATES = tuple(sorted(
    {state for moves in INTERROGATION_OUTCOMES.values() for state in moves}))

# W6628, from the frozen `artifactOutput`. TWO STATUSES, and `missing-optional`
# is one of them: an output the assignment declared as not required and which
# did not appear is REPORTED, with a null manifest and a null artifact. It is
# not silence and it is not an error, and a receiver that treated it as nothing
# to record would lose the fact that the worker was asked and answered.
OUTPUT_STATUSES = ("present", "missing-optional")

OUTPUT_TYPES = ("git-change-proposal", "directory-result", "record-output")

# The frozen `resultManifest.disposition`. The same four the
# `worker_disposition` axis carries beyond `none` -- and they are compared
# against that axis rather than accepted from the result, because a proof the
# caller writes is not a proof.
DISPOSITIONS = ("completed", "unable", "plan-rejected", "cancelled")

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

# WHAT INTAKE DID WITH THE MATERIAL, and it is two answers rather than one.
#
# W6628 pinned the reason in the module that hands intake its work: the
# liveness read before a freeze "is inside the write and is still only a read",
# so the window cannot be zero, and "material from an assignment that ended
# anyway is QUARANTINED AT INTAKE rather than trusted here". Intake is
# therefore the boundary that decides custody, and refusing would be the wrong
# answer -- the bytes exist, somebody produced them, and losing them because
# their assignment ended is how evidence disappears.
CUSTODY = ("accepted", "quarantined")

# THE FROZEN CONTRACT'S OWN retention vocabulary, from `outputRetainBody`. It
# is the operation's answer and never this manager's invention: a disposition
# arrives on the command and is recorded.
RETENTION_DISPOSITIONS = ("retain", "quarantine", "discard-after-intake")

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
    -- W16823: WHAT THIS OFFER FROZE ABOUT THE WORK IT WAS ISSUED AGAINST.
    --
    -- The authority-owned effective scope and the route, taken from the same
    -- projection the issue decision was made on. NOT NULL because every offer
    -- is issued from a projection and there is no path that has one without
    -- them. They exist so the claim decision can be HELD to them: a claim
    -- authorized in another scope, or as another route, is not the claim this
    -- offer promised, and without the frozen pair "relationally inconsistent"
    -- would be a phrase rather than a refusal.
    work_scope         TEXT NOT NULL,
    work_route         TEXT NOT NULL,
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
    -- W16823: THE AUTHORIZATION CONTEXT THE CLAIM WAS TAKEN UNDER.
    --
    -- The endpoint is NOT among them, deliberately. It is already this row's
    -- `participant`, and a second column holding the same fact is a second
    -- place for it to be wrong; the port PROVES the decision's endpoint is
    -- that participant instead, which is the relation rather than a copy.
    --
    -- `claim_event_seq` is the authority's exact immutable act identity,
    -- under a name of this table's own: the authority's document member is
    -- `claim_event`, and one name meaning both a wire member and a column is
    -- one the inventory's flat column scan cannot tell apart. It is
    -- what makes the rest of these attributable: a v11 assignment mints no
    -- generation, so `(work, participant, generation)` is not unique across
    -- two claims through one endpoint, and without this the manager could not
    -- say WHICH claim the context beside it belongs to.
    claim_event_seq        INTEGER,
    claim_principal        TEXT,
    claim_scope            TEXT,
    claim_role             TEXT,
    claim_grant            TEXT,
    claim_policy_generation INTEGER,
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
         AND claim_signature IS NOT NULL)),
    -- W16823: A CLAIMED OFFER CARRIES ITS WHOLE CONTEXT, AND NO OTHER STATE
    -- CARRIES ANY OF IT.
    --
    -- The same all-or-none reasoning the acceptance fields are under, for the
    -- same reason: a row naming the principal but not the scope it was
    -- authorized in would be an authorization nobody can reconstruct, and a
    -- refused or expired settlement authorized nothing at all -- context on
    -- one of those would be evidence of a claim that never committed.
    CHECK (
        (state = 'claimed'
         AND claim_event_seq IS NOT NULL
         AND claim_principal IS NOT NULL
         AND claim_scope IS NOT NULL AND claim_role IS NOT NULL
         AND claim_grant IS NOT NULL
         AND claim_policy_generation IS NOT NULL)
     OR (state <> 'claimed'
         AND claim_event_seq IS NULL AND claim_principal IS NULL
         AND claim_scope IS NULL AND claim_role IS NULL
         AND claim_grant IS NULL AND claim_policy_generation IS NULL))
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
    -- W16823: ...AND THE CONTEXT ARRIVES WITH THEM, from the claimed offer
    -- this attempt belongs to. Fixed by the same act, so it is in the same
    -- all-or-none CHECK below: an attempt that knows which generation it is
    -- fenced to but not which principal it runs for is exactly the conflation
    -- W16793 found, arriving one row later.
    assignment_claim_event_seq INTEGER,
    assignment_principal    TEXT,
    assignment_scope        TEXT,
    assignment_role         TEXT,
    assignment_grant        TEXT,
    assignment_policy_generation INTEGER,
    runtime_id             TEXT,
    observation_seq        INTEGER NOT NULL DEFAULT 0,
    observed_at            TEXT,
    -- W61599, approver ruling M61707: THE DEFAULT LIVENESS PROJECTION, and it
    -- is deliberately two numbers and no content. `activity_bytes` counts the
    -- bytes of the worker's native session stream this manager has OBSERVED;
    -- `activity_at` is the MANAGER's receipt instant for the latest of them,
    -- because a provider timestamp would be the child's account of its own
    -- liveness. Neither renews a claim, clears a gate, extends a deadline or
    -- authorizes recovery -- they are a cue to look, and the axes above remain
    -- the only thing anything decides on.
    --
    -- TOGETHER OR NOT AT ALL, for the reason the assignment columns are: a
    -- count with no instant is an unreadable age and an instant with no count
    -- is freshness about nothing.
    activity_bytes         INTEGER,
    activity_at            TEXT,
    -- W71917: THE NOMINATED SOURCE'S OBJECT IDENTITY, AND NOTHING ABOUT ITS
    -- CONTENTS.
    --
    -- The device and inode this manager itself observed when it nominated the
    -- source directory. Recording them is what lets a SECOND INCARNATION
    -- refuse a source that was replaced while the manager was down: within one
    -- incarnation the composed boundary holds these in memory and the adoption
    -- gate compares against them, and across a restart there was previously
    -- nothing to compare against, so a directory unlinked and recreated at the
    -- same path was re-nominated and accepted.
    --
    -- THIS IS NOT A CONTENT IDENTITY and the distinction is pinned in the
    -- finding. It costs no walk, no read, no hash and no enumeration; it is
    -- the manager remembering which OBJECT a path named, which it already
    -- looked at. What is inside the tree remains something this manager never
    -- measures, and a worker that needs to know which revision it received
    -- still verifies that itself against its own declared base.
    --
    -- TOGETHER OR NOT AT ALL, like the pairs above: half an object identity
    -- compares against nothing.
    source_device          INTEGER,
    source_inode           INTEGER,
    -- W71917 THIRD REVIEW [P1]: THE WRITABLE ROOT IS AN OBJECT TOO.
    --
    -- The pair above made a replaced SOURCE visible across a restart while the
    -- workspace still had only a pathname, so a real directory created at that
    -- pathname was adopted without anything comparing it against the one this
    -- manager took custody of. That is the half a worker's answer is collected
    -- out of, and the acceptance clause names both.
    --
    -- The same non-content rule applies: this manager observed which OBJECT
    -- its own `assignment_workspace` answered, and recording it costs no walk
    -- and no read.
    workspace_device       INTEGER,
    workspace_inode        INTEGER,
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
    -- MONOTONIC AND NON-NEGATIVE IS THE WRITER'S RULE; that a count and an
    -- instant travel together is the TABLE's, because no writer can be trusted
    -- to keep two columns' relationship on its own.
    CHECK ((activity_bytes IS NULL AND activity_at IS NULL)
        OR (activity_bytes IS NOT NULL AND activity_bytes >= 0
            AND activity_at IS NOT NULL)),
    -- W71917: HALF AN OBJECT IDENTITY COMPARES AGAINST NOTHING, so the pair
    -- travels together for the reason the pair above does -- and non-negative,
    -- because a device or inode number is not a signed quantity and a writer
    -- that put one there would be recording something it did not read.
    CHECK ((source_device IS NULL AND source_inode IS NULL)
        OR (source_device IS NOT NULL AND source_device >= 0
            AND source_inode IS NOT NULL AND source_inode >= 0)),
    -- AND THE FOUR TRAVEL TOGETHER, not two pairs that may disagree about
    -- whether this attempt has an identity: the boundary proves both roots in
    -- one act, so a row holding one object and not the other is a row no
    -- writer here can produce.
    CHECK ((workspace_device IS NULL AND workspace_inode IS NULL
            AND source_device IS NULL)
        OR (workspace_device IS NOT NULL AND workspace_device >= 0
            AND workspace_inode IS NOT NULL AND workspace_inode >= 0
            AND source_device IS NOT NULL)),
    CHECK (
        (work_id IS NULL AND authority_uuid IS NULL
         AND assignment_participant IS NULL AND assignment_generation IS NULL
         AND assignment_claim_event_seq IS NULL
         AND assignment_principal IS NULL
         AND assignment_scope IS NULL AND assignment_role IS NULL
         AND assignment_grant IS NULL
         AND assignment_policy_generation IS NULL)
     OR (work_id IS NOT NULL AND authority_uuid IS NOT NULL
         AND assignment_participant IS NOT NULL
         AND assignment_generation IS NOT NULL
         AND assignment_claim_event_seq IS NOT NULL
         AND assignment_principal IS NOT NULL
         AND assignment_scope IS NOT NULL AND assignment_role IS NOT NULL
         AND assignment_grant IS NOT NULL
         AND assignment_policy_generation IS NOT NULL))
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
-- W32649: THE RUNTIME LANE. One row means one lane is HELD; no row means it is
-- free. There is no `available` state, because a lane nobody has taken and a
-- lane that has been given back are the same fact and two spellings of it
-- would be two things to keep true.
--
-- THE PRIMARY KEY IS THE COMPARE-AND-SWAP. `lane_id` is derived from the four
-- identity parts, so two managers racing one successor compute the same key
-- and actually contend; `INSERT` is the acquisition and SQLite decides the
-- winner. A read-then-write would have a window, and this has none.
--
-- THE FOUR PARTS ARE STORED BESIDE THE DERIVED NAME rather than only hashed
-- into it. A digest cannot be read back, and the acceptance requires a
-- projection that explains the current holder and the blocking predecessor --
-- which needs the Work and the principal in a form an operator can see.
CREATE TABLE runtime_lanes (
    lane_id         TEXT PRIMARY KEY,
    authority_uuid  TEXT NOT NULL,
    work_id         TEXT NOT NULL,
    principal       TEXT NOT NULL,
    effective_scope TEXT NOT NULL,
    -- WHO holds it. A lane row without a holder would be capacity nobody can
    -- attribute, which is the shape the posture slot was corrected for.
    holder          TEXT NOT NULL,
    reason          TEXT NOT NULL,
    occupied_at     TEXT NOT NULL
) STRICT;

-- The predecessor interlock reads by Work rather than by lane, so it gets its
-- own index: a successor's start asks this on every attempt.
CREATE INDEX runtime_lanes_by_work
    ON runtime_lanes (authority_uuid, work_id);

-- ONE LANE PER ATTEMPT. An attempt holding two lanes would mean it belonged to
-- two assignments, and choosing between them is a question with no answer.
CREATE UNIQUE INDEX runtime_lanes_one_per_holder
    ON runtime_lanes (holder);

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

-- THE RETAINED MANIFESTS. W6628.
--
-- A DIGEST IS NOT A RECORD. The store held `attempts.input_digest` and would
-- have held a result's manifest digest, and not one byte of either document --
-- so a freeze could not compare a sealed result against the OUTPUT
-- DECLARATIONS the input manifest names, because it never saw them, and any
-- later reader was left with a number and nothing to inspect.
--
-- ONE TABLE SERVES BOTH, because both are the same fact: a validated document
-- this manager is holding, keyed by the digest that identifies it. The key
-- being the digest is what makes retention idempotent by construction and what
-- stops a stored body from drifting from its key -- the key is computed from
-- the bytes.
CREATE TABLE manifests (
    digest      TEXT PRIMARY KEY,
    schema      TEXT NOT NULL,
    body        TEXT NOT NULL,
    retained_at TEXT NOT NULL
) STRICT;

-- ONE FROZEN RESULT PER ATTEMPT.
--
-- The primary key is the attempt and not the result id: an attempt freezes
-- once, and the record operation is fixed per attempt so changed bytes under
-- the same identity REFUSE rather than committing a second result. A table
-- that could hold two would make "which of these is this attempt result" a
-- question with no answer a manager may guess at.
--
-- `manifest_digest` is the RECOMPUTED one, so the number stored beside the
-- result is derived from the bytes rather than lifted from a member the
-- document filled in about itself, and it names the retained row those bytes
-- are in.
CREATE TABLE outputs (
    runtime_attempt_id  TEXT PRIMARY KEY,
    result_id           TEXT NOT NULL,
    disposition         TEXT NOT NULL CHECK (
        disposition IN ('completed', 'unable', 'plan-rejected', 'cancelled')),
    manifest_digest     TEXT NOT NULL,
    freeze_operation_id TEXT NOT NULL,
    frozen_at           TEXT NOT NULL
) STRICT;

-- THE ARTIFACT REFERENCES a frozen result binds, one row per PRESENT output.
--
-- A `missing-optional` output has no artifact and gets no row here; the answer
-- it gave is in the retained result document, which is where every output --
-- present or missing -- is preserved whole. This table is the indexed half,
-- not the record.
CREATE TABLE output_artifacts (
    runtime_attempt_id TEXT NOT NULL,
    output_name        TEXT NOT NULL,
    artifact_id        TEXT NOT NULL,
    media_type         TEXT NOT NULL,
    bytes              INTEGER NOT NULL CHECK (bytes >= 0),
    content_digest     TEXT NOT NULL,
    locator            TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, output_name)
) STRICT;

-- THE INTAKE RECEIPT: this manager's own record that it has taken custody.
--
-- `runtime_attempt_id` IS THE PRIMARY KEY, so "this attempt was intaken once"
-- is the table's invariant rather than a convention, and the receipt digest
-- `runtimeDestroyBody.intake_receipt_digest` carries is derived from the
-- document rather than stored beside an unrelated one.
--
-- THE RECEIPT IS THE MANAGER'S DOCUMENT, and that is why its shape is written
-- down here. The frozen contract names `intake_receipt_digest` and states no
-- shape for what it digests -- exactly as it names ten `*_policy_digest`
-- fields and states the shape of none of them. The difference is direction: a
-- policy is CONSUMED, so this manager binds it by digest and never interprets
-- it; a receipt is PRODUCED here, so the producer owns its shape.
CREATE TABLE intakes (
    runtime_attempt_id  TEXT PRIMARY KEY,
    receipt_digest      TEXT NOT NULL,
    result_id           TEXT NOT NULL,
    manifest_digest     TEXT NOT NULL,
    custody             TEXT NOT NULL CHECK (
        custody IN ('accepted', 'quarantined')),
    why                 TEXT NOT NULL,
    recoverable         INTEGER NOT NULL CHECK (recoverable IN (0, 1)),
    collect_operation_id TEXT NOT NULL,
    intake_operation_id TEXT NOT NULL,
    sealed_at           TEXT NOT NULL
) STRICT;

-- WHAT THIS MANAGER NOW HOLDS, one row per artifact taken into custody.
--
-- Deliberately NOT a copy of `output_artifacts`: that table records what the
-- frozen result DECLARED and where the worker left it, and this one records
-- what intake proved it received and where the manager put it. Conflating them
-- would make "the manager holds this" indistinguishable from "the worker said
-- this existed", which is the whole difference intake makes.
CREATE TABLE intake_artifacts (
    runtime_attempt_id TEXT NOT NULL,
    artifact_id        TEXT NOT NULL,
    content_digest     TEXT NOT NULL,
    bytes              INTEGER NOT NULL CHECK (bytes >= 0),
    custody_locator    TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, artifact_id)
) STRICT;

-- THE RETENTION DECISION, one row per artifact, under the policy that decided
-- it -- BY DIGEST.
--
-- The policy document's shape is stated nowhere in the frozen contract and is
-- not needed here. What cleanup authorization requires is that the digest the
-- destroy command carries is the SAME one every retention decision was made
-- under, and identity is a question a digest answers exactly.
CREATE TABLE retentions (
    runtime_attempt_id      TEXT NOT NULL,
    artifact_id             TEXT NOT NULL,
    disposition             TEXT NOT NULL CHECK (
        disposition IN ('retain', 'quarantine', 'discard-after-intake')),
    retention_policy_digest TEXT NOT NULL,
    retain_operation_id     TEXT NOT NULL,
    decided_at              TEXT NOT NULL,
    PRIMARY KEY (runtime_attempt_id, artifact_id)
) STRICT;

-- THE OPERATOR INTERROGATION, journalled as its own durable lifecycle.
--
-- W6627's confirmed split. The row binds all four things an interrogation is
-- ABOUT and none of them is a caller's account of itself: the exact assignment
-- generation, the posture-specific session, the effectively-once operation
-- identity, and the manager-observed deadline.
--
-- `operation_id` IS THE PRIMARY KEY, so effectively-once is the table's rather
-- than a convention. A second request under one identity is a collision the
-- store refuses, and a retry replays the row it already has.
--
-- `deadline_at` is the MANAGER's, not the adapter's. Timeout is an observation
-- this manager makes about its own waiting; nothing in the worker is asked to
-- agree with it, and nothing about it cancels anything.
--
-- `answer` is null until a conversational answer arrives and stays null for a
-- probe, which has no model turn to answer with. `published_at` is separate
-- from `settled_at` because journalling an answer and publishing it into
-- Baton are two acts, and a committed Baton request is never proof that the
-- adapter or the model saw anything.
CREATE TABLE interrogations (
    operation_id           TEXT PRIMARY KEY,
    kind                   TEXT NOT NULL CHECK (
        kind IN ('probe', 'inquire')),
    runtime_attempt_id     TEXT NOT NULL,
    posture                TEXT NOT NULL CHECK (
        posture IN ('consent', 'execution')),
    session_epoch          INTEGER NOT NULL CHECK (session_epoch >= 1),
    authority_uuid         TEXT NOT NULL,
    work_id                TEXT NOT NULL,
    assignment_participant TEXT NOT NULL,
    assignment_generation  INTEGER NOT NULL,
    requested_at           TEXT NOT NULL,
    deadline_at            TEXT NOT NULL,
    -- ALL SEVEN, and `observed` is the probe's own terminal one. A CHECK
    -- that named six would refuse the very outcome a probe exists to record.
    outcome                TEXT NOT NULL CHECK (
        outcome IN ('requested', 'queued', 'delivered', 'answered',
                    'observed', 'timed-out', 'adapter-unreachable',
                    'runtime-absent')),
    settled_at             TEXT,
    answer                 TEXT,
    published_at           TEXT,
    -- THE PROBE'S READING, DURABLE. Re-review [P1]: this column did not
    -- exist, so the observation reached the caller of a FRESH probe and was
    -- gone from every replay, lookup, list and restart -- an `observed`
    -- outcome with nothing observed in it, which is the whole content of the
    -- operation missing from the only copy that survives.
    observation            TEXT,
    -- AN ANSWER BELONGS TO AN INQUIRE. A probe consumes no model turn, so a
    -- probe row carrying a conversational answer would be a row claiming
    -- something the operation cannot produce.
    CHECK (answer IS NULL OR kind = 'inquire'),
    -- AND PUBLICATION FOLLOWS AN ANSWER. Publishing what nobody answered
    -- would put a manager-authored sentence into Baton wearing a model's
    -- provenance.
    CHECK (published_at IS NULL OR answer IS NOT NULL),
    -- AN OBSERVATION BELONGS TO AN OBSERVED PROBE, both ways round. A row
    -- carrying a reading on any other outcome would be reporting something
    -- nobody looked at, and an `observed` probe without one is the defect
    -- this column was added for, recorded as a rule rather than as a habit.
    CHECK (observation IS NULL
           OR (kind = 'probe' AND outcome = 'observed')),
    CHECK (NOT (kind = 'probe' AND outcome = 'observed')
           OR observation IS NOT NULL)
) STRICT;

CREATE INDEX interrogations_by_session
    ON interrogations (runtime_attempt_id, posture, session_epoch);
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
    "work_scope": Column("text"),
    "work_route": Column("text"),
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
    # W16823's context. Nullable HERE because the STATE decides whether they
    # are present, exactly as the acceptance five are -- the relationship is
    # the SQL CHECK's and what each one IS is this table's.
    "claim_event_seq": Column("count", nullable=True),
    "claim_principal": Column("text", nullable=True),
    "claim_scope": Column("text", nullable=True),
    "claim_role": Column("text", nullable=True),
    "claim_grant": Column("text", nullable=True),
    "claim_policy_generation": Column("count", nullable=True),
    "decision_reason": Column("text", nullable=True),
    "decided_at": Column("instant", nullable=True),
}

# W16823: THE AUTHORIZATION CONTEXT, AS ONE TABLE.
#
# Each entry is (the offer's column, the attempt's column, the member of the
# composed context). Three spellings of one fact are three places for it to
# drift, so they are written down together and every writer and copier reads
# this rather than repeating them.
#
# `claim_event_seq` is this build's name for the authority's `claim_event`
# wire member. They are deliberately different: one is a column and one is a
# document member, and the frozen `assignmentManifest` already calls the same
# fact `claim_event_seq` -- so this is the vocabulary's own spelling rather
# than an invented one.
CLAIM_CONTEXT = (
    ("claim_event_seq", "assignment_claim_event_seq", "claim_event_seq"),
    ("claim_principal", "assignment_principal", "principal"),
    ("claim_scope", "assignment_scope", "effective_scope"),
    ("claim_role", "assignment_role", "role"),
    ("claim_grant", "assignment_grant", "grant"),
    ("claim_policy_generation", "assignment_policy_generation",
     "policy_generation"))

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
    "assignment_claim_event_seq": Column("count", nullable=True),
    "assignment_principal": Column("text", nullable=True),
    "assignment_scope": Column("text", nullable=True),
    "assignment_role": Column("text", nullable=True),
    "assignment_grant": Column("text", nullable=True),
    "assignment_policy_generation": Column("count", nullable=True),
    "runtime_id": Column("text", nullable=True),
    "observation_seq": Column("count"),
    "observed_at": Column("instant", nullable=True),
    # W61599: the liveness projection, absent until something is observed.
    "activity_bytes": Column("count", nullable=True),
    "activity_at": Column("instant", nullable=True),
    # W71917: the nominated source's object identity. `count` because both are
    # whole non-negative numbers this manager read from the filesystem, and
    # nullable because an attempt has neither until its boundary is composed.
    "source_device": Column("count", nullable=True),
    "source_inode": Column("count", nullable=True),
    "workspace_device": Column("count", nullable=True),
    "workspace_inode": Column("count", nullable=True),
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

RUNTIME_LANE_COLUMNS = {
    "lane_id": Column("identity"),
    "authority_uuid": Column("text"),
    "work_id": Column("identity"),
    "principal": Column("text"),
    "effective_scope": Column("text"),
    "holder": Column("identity"),
    "reason": Column("text"),
    "occupied_at": Column("instant"),
}

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

# W6628. `body` is proved to DECODE at the read: a retained document that no
# longer parses is caught where the row is adopted rather than by the caller
# that was about to compare declarations against it.
MANIFEST_COLUMNS = {
    "digest": Column("identity"),
    "schema": Column("text"),
    "body": Column("json"),
    "retained_at": Column("instant"),
}

OUTPUT_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "result_id": Column("identity"),
    "disposition": Column("text", allowed=DISPOSITIONS),
    "manifest_digest": Column("text"),
    "freeze_operation_id": Column("identity"),
    "frozen_at": Column("instant"),
}

INTERROGATION_COLUMNS = {
    "operation_id": Column("identity"),
    "kind": Column("text", allowed=INTERROGATION_KINDS),
    "runtime_attempt_id": Column("identity"),
    "posture": Column("text", allowed=POSTURES),
    "session_epoch": Column("count"),
    "authority_uuid": Column("text"),
    "work_id": Column("identity"),
    "assignment_participant": Column("text"),
    "assignment_generation": Column("count"),
    "requested_at": Column("instant"),
    "deadline_at": Column("instant"),
    "outcome": Column("text", allowed=_INTERROGATION_STATES),
    "settled_at": Column("instant", nullable=True),
    "answer": Column("json", nullable=True),
    "published_at": Column("instant", nullable=True),
    "observation": Column("json", nullable=True),
}

INTAKE_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "receipt_digest": Column("text"),
    "result_id": Column("identity"),
    "manifest_digest": Column("text"),
    "custody": Column("text", allowed=CUSTODY),
    "why": Column("text"),
    "recoverable": Column("flag"),
    "collect_operation_id": Column("identity"),
    "intake_operation_id": Column("identity"),
    "sealed_at": Column("instant"),
}

INTAKE_ARTIFACT_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "artifact_id": Column("identity"),
    "content_digest": Column("text"),
    "bytes": Column("count"),
    "custody_locator": Column("text"),
}

RETENTION_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "artifact_id": Column("identity"),
    "disposition": Column("text", allowed=RETENTION_DISPOSITIONS),
    "retention_policy_digest": Column("text"),
    "retain_operation_id": Column("identity"),
    "decided_at": Column("instant"),
}

OUTPUT_ARTIFACT_COLUMNS = {
    "runtime_attempt_id": Column("identity"),
    "output_name": Column("identity"),
    "artifact_id": Column("identity"),
    "media_type": Column("text"),
    "bytes": Column("count"),
    "content_digest": Column("text"),
    "locator": Column("text"),
}
