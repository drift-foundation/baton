"""The integration coordinator's own relations.

W71878, under the owner ruling of 2026-09-05: integration ordering and
exclusion belong to a TARGET-GLOBAL store whose transaction domain is
independent of every Authority-bound `JobStore`.

WHY THIS IS NOT A JOB-STORE TABLE, which is the whole reason this file exists.
W83781 binds each Job store immutably to one Authority UUID and refuses an open
under another. A live-target unique index there is therefore unique only WITHIN
one Authority -- so two Authorities configured for one canonical target would
each hold their own store, grant their own lease, and import into one working
tree. This record's identity model requires them to contend on ONE lock. Only a
store outside every Authority's binding can enforce that.

SO THIS STORE IS KEYED BY THE TARGET AND BY NOTHING ELSE. It records no
Authority binding of its own, because binding it to one would reintroduce the
defect one layer down. What is Authority-specific -- the Work, the proposal,
the receipts, the checkpoint, the reviewed path scope -- travels INSIDE an
immutable entry as evidence, namespaced by the Authority it came from.
"""

from ..contracts import ContractRefusal
from ..worker_manager.boundaries import Column

__all__ = ["ENTRY_COLUMNS", "ENTRY_STATES", "LEASE_COLUMNS", "LEASE_STATES",
           "MIGRATIONS", "OPERATION_COLUMNS", "SCHEMA", "SCHEMA_VERSION",
           "STORE_KIND", "TABLES", "TARGET_COLUMNS", "TARGET_STATES",
           "check_authority"]


def check_authority(value, *, what):
    """The Authority UUID rule, REUSED and answered in this leaf's vocabulary.

    Review of 2026-09-06 [P1]: an entry's `authority_uuid` was owned as generic
    non-empty text, so `not-an-authority` was accepted and returned by a store
    whose entries the contract calls Authority-NAMESPACED. A namespace nothing
    validates is a label.

    The shape of the fix is `job_manager.schema.check_authority`'s, for its
    reasons rather than by imitation. The RULE must be the Authority package's
    own -- a third spelling of "32 lowercase hex" living here is exactly the
    drift that stays invisible until two components disagree about one
    identity. The REFUSAL a caller of this package catches must be this
    package's, because everything else here raises `ContractRefusal`.

    So the predicate is imported and only the exception type is translated.
    `check_authority_uuid` opens no store, holds no session and grants nothing:
    it is a rule, and importing a rule is not importing an Authority -- which
    matters more here than anywhere, since this store's whole purpose is to
    stand outside every Authority binding.

    THIS PROVES SYNTAX AND NOTHING ELSE. It is not evidence that the Authority
    exists, that it is reachable, or that it may speak for this candidate;
    that is PLAN item 4's admission, above this seam.
    """
    from ..authority.errors import Refusal
    from ..authority.identity import check_authority_uuid

    try:
        return check_authority_uuid(value, what=what)
    except Refusal as refused:
        raise ContractRefusal("integrity", "schema", str(refused)) from None

STORE_KIND = "baton.v12.python.integration-coordinator"

# FOUR. Two was `operations.seq` arriving; three was the candidate account
# losing the two members W101491 found unprovable; four is
# `proposal_manifest_digest` -- which W101714's own review found in the same
# state -- becoming the accepted publish operation's `result_id` and
# `result_digest`. Versions 1 to 3 are shapes this record's unaccepted candidate
# carried and nothing else ever held, so there is no deployed store to carry
# forward and no migration is invented; a database at another version is refused
# rather than guessed across, which is the rule every other store in this
# distribution is under. The version moves with the shape because two different
# shapes under one version number is exactly the drift a version exists to
# prevent.
# FIVE ADDS THE INTEGRATION RESULT (W131409 replacement slice P,
# INTEGRATION-CONTRACT-v1 section 3). An eligible submission and an integration
# RESULT are two immutable objects, not one row in two states: the submission
# is the producer's original candidate on its original base, and the result is
# that submission reconciled with one exact target snapshot, with its own
# content, its own evidence and its own derived Authority proposal. A schema-4
# store has no relation those facts could live in and no way to tell a direct
# import from a reconciled one after the fact, so the standing fresh-store
# boundary applies exactly as it did at four: a database at another version is
# refused rather than guessed across, and no migration is invented.
SCHEMA_VERSION = 5

TABLES = ("meta", "operations", "targets", "entries", "leases",
          "integration_results")

# WHAT A RESULT IS FOR, as states rather than prose.
#
# `preparing` is a committed intent whose profile effects may not have
# happened yet -- it is NOT a completed operation. `prepared` holds proved
# content and nothing more: no test has run against it and nobody has reviewed
# it. `awaiting-evidence` and `authorized` separate "content exists" from
# "somebody independently verified, reviewed and approved THESE bytes", which
# is the distinction the whole design turns on. `published` names a derived
# Authority proposal. `imported` is terminal success. `held` carries its reason
# and takes nothing: a conflict, a missing object, an unproved source or a
# target that moved all stop here with their evidence intact.
#
# `blocked` IS WHERE A COMBINED FAILURE LIVES. Review 2026-09-10T05:41:11Z
# [R1]: a failing combined observation used to refuse before anything was
# stored, so the row stayed `prepared` with no observations at all and the
# failed execution had no custody -- the opposite of section 4's "the combined
# failure stays visible". It is a settled outcome with its content, its
# retained observations and its reason, and it cannot be authorized.
RESULT_STATES = ("preparing", "prepared", "awaiting-evidence", "authorized",
                 "published", "held", "blocked", "imported")

# WHAT AN ENTRY IS FOR, as states rather than prose.
#
# `queued` is eligible and unleased; `leased` is being integrated right now;
# `integrated` is terminal success. The two refusals are NOT one state, and the
# targeted review of 2026-09-05 is why: an ordinary policy, scope or target
# failure before mutation terminally refuses THAT immutable entry and the queue
# moves on, while an integrity, digest or ambiguous-custody failure is a
# statement about the TARGET and must not be retried past.
ENTRY_STATES = ("queued", "leased", "integrated", "refused", "held")

# A lease is live or it is over. `released` ended cleanly; `abandoned` was
# ended by an explicit recovery that proved the prior holder can no longer
# mutate. Nothing expires on its own -- see `leases` below.
LEASE_STATES = ("live", "released", "abandoned")

# A target is open for business or it is blocked pending explicit repair. There
# is no "degraded": a target whose last import left an account this build
# cannot reconcile is one nothing may be imported into until somebody says so.
TARGET_STATES = ("open", "blocked")

SCHEMA = """
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
) STRICT;

-- THE JOURNAL, AND `seq` IS THE ORDER THE ACTS COMMITTED IN.
--
-- Seventh review of 2026-09-06 [P0]: rank and fence are GENERATED inside their
-- transactions, so no signed request can contain them. The only witnesses were
-- the recorded result and the materialized row, and rewriting both left them
-- agreeing about a durable order that never happened -- entry 1 moved behind
-- entry 2 and selection followed.
--
-- `seq` is the third witness and it is a different KIND of one: it is not a
-- value about the decision, it is the position the act holds among every act
-- this store ever committed. It is allocated as MAX+1 in the recording
-- transaction and is dense from one, so the ranks a target's enqueues
-- allocated, the fences its grants burned, and which entry each grant could
-- have selected are all DERIVABLE from the order rather than believed from the
-- values. An UPDATE to a result or an entry row cannot reach it.
--
-- WHAT IT IS NOT. There is no durable secret in this deployment (§13 forbids
-- one), so nothing here is unforgeable: a writer who also rewrites `seq` can
-- present a self-consistent alternative history, and this seam cannot tell
-- that from the real one. What the column buys is that the two-surface rewrite
-- the review demonstrated now contradicts a third surface that neither of them
-- touches, and that a deleted act leaves a hole in a dense sequence.
CREATE TABLE operations (
  seq INTEGER NOT NULL UNIQUE CHECK (seq >= 1),
  operation_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  signature TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('committed', 'refused')),
  result TEXT,
  refusal TEXT,
  settled_at TEXT NOT NULL,
  CHECK ((state = 'committed' AND refusal IS NULL)
         OR (state = 'refused' AND result IS NULL AND refusal IS NOT NULL))
) STRICT;

-- THE TARGET, AND ITS KEY IS CONFIGURATION'S.
--
-- `canonical_target_id` is supplied by trusted target configuration and is
-- never derived from a line, Authority, Work, proposal, checkpoint or the
-- mutable target revision. Deriving it from any of those is how one target
-- acquires two locks.
--
-- `fence` is the monotonic lease generation for this target. It only ever
-- increases, and it increases in the same transaction that grants a lease, so
-- a fence value read at any moment names at most one grant that ever existed.
--
-- `blocked_account` IS THE BLOCK'S SUBJECT AND IS NOT DECORATION. The review of
-- 2026-09-06 found a block that named any of the target's entries while some
-- OTHER entry held the live lease -- so the recovery that followed abandoned
-- the real holder's grant and left its entry `leased` while an unrelated entry
-- was `held`. A blocked target now records the exact entry, lease, fence and
-- holder that were live when it blocked, and the recovery cross-checks that
-- one account rather than re-deriving it.
CREATE TABLE targets (
  canonical_target_id TEXT PRIMARY KEY,
  document TEXT NOT NULL,
  digest TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('open', 'blocked')),
  fence INTEGER NOT NULL CHECK (fence >= 0),
  blocked_reason TEXT,
  blocked_account TEXT,
  activated_at TEXT NOT NULL,
  CHECK ((state = 'open' AND blocked_reason IS NULL
          AND blocked_account IS NULL)
         OR (state = 'blocked' AND blocked_reason IS NOT NULL
             AND blocked_account IS NOT NULL))
) STRICT;

-- AN IMMUTABLE ENTRY, AUTHORITY-NAMESPACED.
--
-- Everything from `authority_uuid` through `scope_digest` is evidence copied
-- at enqueue and never rewritten: the entry is a statement about one candidate
-- at one instant, and a queue whose entries could be edited would be a queue
-- whose order meant nothing.
--
-- THESE COLUMNS ARE THE ACCOUNT, and there is no second copy of it. The first
-- shape stored all seventeen operands AGAIN as one `eligibility` document, and
-- the review of 2026-09-06 changed one column and watched the reader hand back
-- a row and a document that disagreed about the same candidate without
-- refusing. Validating the two against each other on every read was the
-- narrower fix, and removing the second owner is the one this codebase's own
-- rule asks for -- it makes the disagreement unrepresentable, not caught.
-- The account is reassembled from these columns at the read, which is lossless
-- because the document is closed over exactly these members.
--
-- AND NOTHING HERE NAMES A VERSION CONTROL SYSTEM. The owner clarified on
-- 2026-09-06 that the coordinator, Job Manager, Worker Manager and protocol are
-- VCS-NEUTRAL: core Baton mechanically owns serialized admission, the live
-- fenced grant, exclusive target write access, quiescence and durable
-- settlement, and it neither parses nor validates commits, refs, branches,
-- trees, ancestry or merges. `base_object`, `head_object`, `tree_object` and
-- `transport_ref` were Git operands sitting in core schema, and they are gone.
--
-- WHAT REPLACED THEM IS ONE PROFILE NAME. The first correction wrote a
-- three-member binding -- kind, version and an account digest -- and
-- W101491's admission leaf then found that two of the three had no producer
-- at all. `profile_kind` is what survived, and it is the accepted checkpoint
-- evidence's own `profile` member (`source_profiles.PROFILES`: `generic` or
-- `git`). The profile-shaped account that name belongs to is bound by
-- `checkpoint_digest`, which `review_cycles.freeze` computes as the digest of
-- that evidence, so the coordinator refuses a changed account without ever
-- knowing what one is -- and without a second column holding the same digest.
--
-- EVERY MEMBER HAS AN ACCEPTED PRODUCER, which is this account's rule and is
-- driven rather than asserted. `result_id` and `result_digest` are here
-- because `proposal_manifest_digest` was not: that name lives only in the
-- frozen worker-control JSON schema and in this coordinator, while the
-- Authority `publish` operation and its `proposal` row carry the frozen
-- result's identity and content digest.
--
-- THE DIGEST FAMILIES SIT SIDE BY SIDE AND ARE NEVER EQUATED.
-- `checkpoint_digest` is W71918's `digest(checkpoint_evidence)`;
-- `candidate_digest` and `result_digest` are Authority's, over different
-- things. The targeted review of 2026-09-05 ruled that requiring them equal
-- merely to manufacture a cross-binding would silently reinterpret one of
-- them, so each is retained under its own name and the CORRESPONDING operands
-- are what must agree.
CREATE TABLE entries (
  entry_id TEXT PRIMARY KEY,
  canonical_target_id TEXT NOT NULL REFERENCES targets(canonical_target_id),
  rank INTEGER NOT NULL CHECK (rank >= 1),
  authority_uuid TEXT NOT NULL,
  work_id TEXT NOT NULL,
  assignment_generation INTEGER NOT NULL CHECK (assignment_generation >= 1),
  line_id TEXT NOT NULL,
  checkpoint_id TEXT NOT NULL,
  verdict_id TEXT NOT NULL,
  checkpoint_digest TEXT NOT NULL,
  proposal_id TEXT NOT NULL,
  candidate_digest TEXT NOT NULL,
  result_id TEXT NOT NULL,
  result_digest TEXT NOT NULL,
  profile_kind TEXT NOT NULL,
  expected_target_revision TEXT NOT NULL,
  path_set_digest TEXT NOT NULL,
  scope_digest TEXT NOT NULL,
  state TEXT NOT NULL CHECK (
    state IN ('queued', 'leased', 'integrated', 'refused', 'held')),
  enqueued_at TEXT NOT NULL,
  settled_at TEXT,
  settlement TEXT,
  -- ORDER IS PER TARGET AND IS ALLOCATED IN THE ENQUEUE TRANSACTION, so two
  -- concurrent enqueues cannot receive one rank and selection never has to
  -- break a tie by row order or wall clock.
  UNIQUE (canonical_target_id, rank),
  -- ONE ENTRY PER CANDIDATE PER TARGET. A second enqueue of the same accepted
  -- checkpoint is a replay, not a second place in the queue.
  UNIQUE (canonical_target_id, authority_uuid, checkpoint_id),
  CHECK ((state IN ('queued', 'leased') AND settled_at IS NULL
          AND settlement IS NULL)
         OR (state IN ('integrated', 'refused', 'held')
             AND settled_at IS NOT NULL AND settlement IS NOT NULL))
) STRICT;

-- ONE LIVE LEASE PER TARGET, DECIDED IN THE STORE.
--
-- The partial index below is the exclusion itself rather than a check some
-- caller performs: two grants racing for one target contend on it inside their
-- write transactions, and the loser refuses.
--
-- NOTHING EXPIRES. There is no timeout column and that is deliberate: a
-- holder's silence is not evidence that it has stopped, and W71917's campaign
-- already recorded what happens when absence is read as absence of work.
-- Ending somebody else's lease is the explicit `abandoned` recovery, which
-- must prove the prior holder can no longer mutate.
CREATE TABLE leases (
  lease_id TEXT PRIMARY KEY,
  canonical_target_id TEXT NOT NULL REFERENCES targets(canonical_target_id),
  entry_id TEXT NOT NULL REFERENCES entries(entry_id),
  integrator_participant TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  fence INTEGER NOT NULL CHECK (fence >= 1),
  state TEXT NOT NULL CHECK (state IN ('live', 'released', 'abandoned')),
  granted_at TEXT NOT NULL,
  ended_at TEXT,
  ending TEXT,
  UNIQUE (canonical_target_id, fence),
  CHECK ((state = 'live' AND ended_at IS NULL AND ending IS NULL)
         OR (state IN ('released', 'abandoned') AND ended_at IS NOT NULL
             AND ending IS NOT NULL))
) STRICT;

CREATE UNIQUE INDEX leases_one_live_per_target
  ON leases (canonical_target_id) WHERE state = 'live';

CREATE INDEX entries_queued_by_rank
  ON entries (canonical_target_id, rank) WHERE state = 'queued';

-- W131409 slice P: ONE PREPARED INTEGRATION RESULT.
--
-- It names the ORIGINAL submission it was reconciled from and never rewrites
-- it: the producer's line, checkpoint, verdict, proposal, frozen result and
-- base all appear here as immutable references. What belongs to the RESULT is
-- the prepared content, the target snapshot it was prepared onto, its OWN
-- verification/review/approval evidence and its OWN derived Authority
-- proposal. A checkpoint alone never reaches this table.
CREATE TABLE integration_results (
  result_id TEXT PRIMARY KEY,
  operation_id TEXT NOT NULL,
  canonical_target_id TEXT NOT NULL REFERENCES targets(canonical_target_id),
  authority_uuid TEXT NOT NULL,
  work_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  line_id TEXT NOT NULL,
  source_checkpoint_id TEXT NOT NULL,
  source_verdict_id TEXT NOT NULL,
  source_proposal_id TEXT NOT NULL,
  source_result_id TEXT NOT NULL,
  source_result_digest TEXT NOT NULL,
  source_checkpoint_digest TEXT NOT NULL,
  source_base TEXT NOT NULL,
  source_candidate TEXT NOT NULL,
  integration_attempt_id TEXT NOT NULL,
  integration_assignment TEXT NOT NULL,
  workspace TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  profile_version INTEGER NOT NULL CHECK (profile_version >= 1),
  target_revision TEXT NOT NULL,
  target_source TEXT NOT NULL,
  target_reference TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN
    ('preparing', 'prepared', 'awaiting-evidence', 'authorized', 'published',
     'held', 'blocked', 'imported')),
  reason TEXT,
  prepared TEXT,
  content_digest TEXT,
  evidence TEXT,
  causal_observations TEXT,
  observed_by TEXT,
  policy_generation INTEGER CHECK (policy_generation IS NULL
                                   OR policy_generation >= 1),
  derived_proposal_id TEXT,
  derived_result_id TEXT,
  derived_result_digest TEXT,
  entry_id TEXT REFERENCES entries(entry_id),
  recorded_at TEXT NOT NULL,
  -- A REASON BELONGS TO A STOPPED RECORD AND TO NOTHING ELSE, and prepared
  -- content is absent until there is some: an account of something that has
  -- not happened is not one. `blocked` carries BOTH -- content that exists and
  -- the reason it may not proceed.
  CHECK ((state IN ('held', 'blocked') AND reason IS NOT NULL)
      OR (state NOT IN ('held', 'blocked') AND reason IS NULL)),
  CHECK ((state IN ('preparing', 'held') AND prepared IS NULL
          AND content_digest IS NULL)
      OR (state NOT IN ('preparing', 'held') AND prepared IS NOT NULL
          AND content_digest IS NOT NULL)),
  -- THE CAUSAL OBSERVATIONS ARE RETAINED WHETHER OR NOT THEY PASSED. Review
  -- 2026-09-10T05:41:11Z [R1]: a failing combined observation used to refuse
  -- before anything was stored, leaving the failed execution with no custody
  -- at all. They commit with the observation act, and `blocked` is a state
  -- that HAS them, names who produced them, and can never be authorized.
  CHECK ((state IN ('awaiting-evidence', 'blocked', 'authorized', 'published',
                    'imported')
          AND causal_observations IS NOT NULL AND observed_by IS NOT NULL)
      OR (state NOT IN ('awaiting-evidence', 'blocked', 'authorized',
                        'published', 'imported')
          AND causal_observations IS NULL AND observed_by IS NULL)),
  -- AUTHORIZATION IS EVIDENCE-BOUND, and an authorized result binds the policy
  -- generation it was authorized under. A result cannot be authorized,
  -- published or imported without its own independent verification, review and
  -- approval recorded here.
  CHECK ((state IN ('authorized', 'published', 'imported')
          AND evidence IS NOT NULL AND policy_generation IS NOT NULL)
      OR (state NOT IN ('authorized', 'published', 'imported')
          AND evidence IS NULL AND policy_generation IS NULL)),
  -- AND A PUBLISHED RESULT NAMES ITS OWN DERIVED PROPOSAL, never the
  -- producer's.
  CHECK ((state IN ('published', 'imported')
          AND derived_proposal_id IS NOT NULL
          AND derived_result_id IS NOT NULL
          AND derived_result_digest IS NOT NULL)
      OR (state NOT IN ('published', 'imported')
          AND derived_proposal_id IS NULL
          AND derived_result_id IS NULL
          AND derived_result_digest IS NULL)),
  -- AN IMPORTED RESULT NAMES THE ENTRY IT WAS IMPORTED THROUGH. Review [P1]
  -- reached `imported` with no entry at all; terminal linkage is section 3's
  -- own requirement and is now structural.
  CHECK ((state = 'imported' AND entry_id IS NOT NULL)
      OR (state != 'imported')),
  -- ONE LIVE RESULT PER SUBMISSION PER TARGET SNAPSHOT. A later target advance
  -- needs a NEW result from the same submission; it never mutates this one.
  UNIQUE (canonical_target_id, source_proposal_id, target_revision)
) STRICT;

-- Selection reads by target and state; recovery reads by the submission.
CREATE INDEX results_by_target_state
  ON integration_results (canonical_target_id, state);
CREATE INDEX results_by_submission
  ON integration_results (authority_uuid, work_id, source_proposal_id);
"""

MIGRATIONS = {}

# THE JOURNAL IS EVIDENCE, SO IT IS ADOPTED LIKE ANY OTHER ROW. The review of
# 2026-09-06T03:22 made the operation record the durable history the
# materialized rows are proved against; a record used as evidence is persisted
# input, and persisted input this build did not write in this process is owned
# where it is read like everything else here.
OPERATION_COLUMNS = {
    "seq": Column("count"),
    "operation_id": Column("identity"),
    "kind": Column("text"),
    "signature": Column("json"),
    "state": Column("text", allowed=("committed", "refused")),
    "result": Column("json", nullable=True),
    "refusal": Column("refusal", nullable=True),
    "settled_at": Column("instant"),
}

TARGET_COLUMNS = {
    "canonical_target_id": Column("identity"),
    "document": Column("json"),
    "digest": Column("text"),
    "state": Column("text", allowed=TARGET_STATES),
    "fence": Column("count"),
    "blocked_reason": Column("text", nullable=True),
    "blocked_account": Column("json", nullable=True),
    "activated_at": Column("instant"),
}

ENTRY_COLUMNS = {
    "entry_id": Column("identity"),
    "canonical_target_id": Column("identity"),
    "rank": Column("count"),
    "authority_uuid": Column("text"),
    "work_id": Column("identity"),
    "assignment_generation": Column("count"),
    "line_id": Column("identity"),
    "checkpoint_id": Column("identity"),
    "verdict_id": Column("identity"),
    "checkpoint_digest": Column("text"),
    "proposal_id": Column("identity"),
    "candidate_digest": Column("text"),
    "result_id": Column("identity"),
    "result_digest": Column("text"),
    "profile_kind": Column("text"),
    "expected_target_revision": Column("text"),
    "path_set_digest": Column("text"),
    "scope_digest": Column("text"),
    "state": Column("text", allowed=ENTRY_STATES),
    "enqueued_at": Column("instant"),
    "settled_at": Column("instant", nullable=True),
    "settlement": Column("json", nullable=True),
}

RESULT_COLUMNS = {
    "result_id": Column("identity"), "operation_id": Column("text"),
    "canonical_target_id": Column("identity"),
    # -- the ORIGINAL submission, named and never rewritten -------------------
    "authority_uuid": Column("text"), "work_id": Column("identity"),
    "job_id": Column("identity"), "line_id": Column("identity"),
    "source_checkpoint_id": Column("identity"),
    "source_verdict_id": Column("identity"),
    "source_proposal_id": Column("identity"),
    "source_result_id": Column("identity"),
    "source_result_digest": Column("text"),
    "source_checkpoint_digest": Column("text"),
    "source_base": Column("text"), "source_candidate": Column("text"),
    # -- the integration role's own fixed assignment and workspace ------------
    "integration_attempt_id": Column("identity"),
    "integration_assignment": Column("json", members=("work_ref",
                                                      "participant",
                                                      "generation")),
    "workspace": Column("json", members=("path", "device", "inode")),
    "profile_name": Column("text"), "profile_version": Column("count"),
    # -- the pinned target snapshot this result was prepared onto -------------
    "target_revision": Column("text"),
    "target_source": Column("json", members=("path", "device", "inode")),
    "target_reference": Column("text"),
    # -- the prepared content --------------------------------------------------
    "state": Column("text", allowed=RESULT_STATES),
    "reason": Column("text", nullable=True),
    "prepared": Column("json", nullable=True,
                       members=("profile", "version", "base", "head", "tree",
                                "reference", "content")),
    "content_digest": Column("text", nullable=True),
    # -- the result's OWN independent evidence, never the producer's ----------
    "evidence": Column("json", nullable=True),
    "causal_observations": Column("json", nullable=True),
    "observed_by": Column("text", nullable=True),
    "policy_generation": Column("count", nullable=True),
    # -- the derived Authority proposal ---------------------------------------
    "derived_proposal_id": Column("identity", nullable=True),
    "derived_result_id": Column("identity", nullable=True),
    "derived_result_digest": Column("text", nullable=True),
    "entry_id": Column("identity", nullable=True),
    "recorded_at": Column("instant"),
}

LEASE_COLUMNS = {
    "lease_id": Column("identity"),
    "canonical_target_id": Column("identity"),
    "entry_id": Column("identity"),
    "integrator_participant": Column("text"),
    "attempt_id": Column("identity"),
    "fence": Column("count"),
    "state": Column("text", allowed=LEASE_STATES),
    "granted_at": Column("instant"),
    "ended_at": Column("instant", nullable=True),
    "ending": Column("json", nullable=True),
}
