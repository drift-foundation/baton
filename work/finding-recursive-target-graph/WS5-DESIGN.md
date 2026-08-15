# WS-5 design — effectively-once mutation retry

Author: `baton.implementer`
Date: 2026-08-15
Responding to: `8c5407d126d2e264f032973fdfb01991` (design/challenge only)
No source, schema, CLI, test, migration, deployment, TUI, or PROGRESS
edits made.

## 1. Inventory: every public mutating operation and its retry posture today

Committed via `Authority._write` (one SQLite transaction each: BEGIN
IMMEDIATE, dense seq allocation, mutate, event insert, COMMIT):

- **Work family** — `create_work` (create), `close_work` (close),
  `classify`, `set_phase` (phase, incl. waiting/parked and the atomic
  wake), `add_dependency` (block), `revise_work` (revise).
- **Discussion family** — `create_discussion` (discuss),
  `post_discussion` (say; event kind `post_message`/`request`/`pass`/
  `return` decided by operators), `label_discussion` (label),
  `unlabel_discussion` (unlabel), `seen_discussion` (mark-seen; the
  losing/idempotent mark returns WITHOUT an audit act by design).
- **Obligation family** — `respond_obligation` (respond),
  `dispose_obligation` (dispose), `accept_obligation` (accept; may
  create the provider Work and emit the answer message in the same
  transaction).
- **Verification family** — `create_round` (round), `report`, `assess`,
  `abandon_round` (abandon), `extend_round` (extend).
- **Configuration family** (lifecycle path, its own bound transaction):
  `init_from_config` (init; generation 1 — creates the schema and seeds
  the accepted topology) and `accept_config` (regen; generation N+1
  under the config capability).

Pure reads and waits (NO operation identity now or ever, unchanged):
home, obligations, summary, detail, children, links, breadcrumb, new,
thread, discussions, work-discussions, revisions, events, and the
read-only `wait` (it polls the pure projection and mutates nothing).

Current retry posture, stated since WS-2 and soaked since A8: every
transition is atomic and crash-safe, and duplicate COMMITS are
structurally refused where the domain allows it (double close, double
respond, CAS revisions, UNIQUE constraints), but a mutation whose
RESPONSE was lost is unrecoverable except by reading state first — the
documented "read before retry" limitation. Two calls of an
intentionally repeatable operation (say, post) are two effects. WS-5
replaces exactly this.

## 2. Operation identity: grammar, scope, and the optional-id guarantee (P1, P2)

- **Grammar.** A client-supplied opaque string, `--op-id VALUE`:
  1–128 bytes UTF-8, at least one byte, no whitespace or control
  characters; anything else refuses pre-write with the usual JSON
  refusal. No server-side generation, no format inference — a UUID is
  the recommended convention, never a requirement. The id is an
  IDENTITY, not a fingerprint: its bytes carry no meaning.
- **Collision scope (P1).** Uniqueness is per PARTICIPANT:
  the record key is `(participant, op_id)` where participant is the
  validated `team.member` acting identity. Two members reusing the
  same UUID never interfere; one member reusing their own id for a
  different request is the conflict the design refuses. Global scope
  is rejected: it would let one member's id choice make another
  member's honest retry refuse, and it discloses cross-member timing.
- **Mandatory versus convenience (P2 — recommendation: optional,
  honest).** `--op-id` is accepted by EVERY public mutation and
  required by none. With an id: effectively-once — the committed
  result is recoverable and a second effect is impossible. Without an
  id: the guarantee is exactly today's, and the CLI says so in the
  verb help — at-most-once per invocation, lost responses recovered by
  reading state ("read before retry"). Rationale: mandatory ids would
  break every human one-off invocation and add ceremony to operations
  that are already structurally idempotent; an honest two-tier
  guarantee keeps the strong path available wherever it matters.
  - Agent CLI: agents SHOULD generate one id per intended mutation and
    retain it until the result is durably recorded; the JSON envelope
    makes the guarantee visible (§6).
  - Human CLI: optional; the refusal/replay messages are designed to
    read correctly either way.
  - Bounded TUI: its only mutation is the discussion-scoped seen mark,
    which is monotonic and idempotent by construction (a repeat is a
    no-op WITHOUT an audit act). The TUI therefore supplies no id and
    loses nothing. Stated explicitly rather than silently assumed.

## 3. The semantic request fingerprint (P3)

Reusing an id must fail closed unless the request is THE SAME REQUEST.
"Same" is semantic, not textual:

- **Definition.** `fingerprint = sha256(canonical_json(record))` where
  `record = {"operation": <transition name>, "actor": "team.member",
  "input": <typed keyword arguments exactly as validated>}`.
  `canonical_json` is sorted-keys, compact separators, UTF-8 — the
  digest discipline already used for config acceptance.
- **Typed input, not spelling.** The fingerprint is computed AFTER
  argument parsing and normalization but BEFORE any dynamic
  resolution: flag order, shell quoting, and CLI-versus-library entry
  do not change it; `--limit 7` as int 7 is one value however spelled.
- **Not resolution output.** Dynamic facts the authority derives —
  an omitted `--on`'s resolved Work, `+` selector expansion, route
  handler resolution, allocated ids/seqs — are EXCLUDED. `on=None` and
  `on="X-W1"` are different requests; `include="*.bug"` fingerprints
  as the literal selector, never its expansion. Consequence, stated
  honestly: an exact retry of an omitted-`--on` request replays the
  ORIGINAL committed resolution even if a fresh resolution would now
  pick differently — that is precisely the effectively-once contract.
- Exact retry: same `(participant, op_id)`, equal fingerprint →
  return the stored committed result, no second effect, no sequence.
  Conflicting reuse: same key, different fingerprint → closed refusal
  naming the collision ("op-id X was already used for a different
  request"), no mutation, no sequence.

## 4. Storage and the one-transaction algorithm (P4)

Schema v12, one new append-only table:

    CREATE TABLE operations (
        recorded    INTEGER NOT NULL UNIQUE,  -- the operation history's
                                              -- OWN dense total cursor
                                              -- (R79): allocated per
                                              -- authority in the same
                                              -- transaction; never the
                                              -- event sequence
        participant TEXT    NOT NULL,
        op_id       TEXT    NOT NULL,
        fingerprint TEXT    NOT NULL,
        seq         INTEGER,               -- committed event seq; NULL
                                           -- for a successful NO-OP
                                           -- (R76: no invented event)
        result      TEXT    NOT NULL,      -- canonical replayable JSON
        created_ts  TEXT    NOT NULL,
        PRIMARY KEY (participant, op_id)
    ) STRICT;

`recorded` exists because `seq` cannot order this history: successful
no-op rows have no domain event (R76), so the domain sequence is
partial over operations. `recorded` is dense over ALL recorded
operations — effectful and no-op alike — allocated monotonically
inside the recording transaction, giving the listing a total,
gap-free, deterministic cursor independent of event sequencing.

Algorithm, inside the SAME `_write` transaction as the mutation and
its event (never a second transaction):

1. **Pre-write lookup** (optimistic, on the read connection): if
   `(participant, op_id)` exists — equal fingerprint → return the
   stored result as a replay (pure read, no transaction, no seq);
   different fingerprint → refuse. This handles the common retry
   without taking the write lock at all.
2. **In-lock recheck** (first statement of mutate, same conn): repeat
   the lookup. A concurrent identical attempt that committed between
   step 1 and the lock is detected HERE and the transaction abandons
   into a replay of the stored result — refuse-into-replay, not a
   second effect. A concurrent conflicting attempt refuses closed.
3. **Record with the effect**: after the domain mutate succeeds and
   the result is fully assembled, insert the operations row in the
   same transaction, then the event, then COMMIT. The PRIMARY KEY is
   the last-resort backstop: two simultaneous identical attempts
   serialize on BEGIN IMMEDIATE, so the loser always sees the
   winner's row at step 2; a PK violation surviving to step 3 is a
   defect, surfaced loudly, never silently swallowed.
4. **Refusal before commit records NOTHING** (recommended, P5): an id
   only ever names a COMMITTED effect. A validation refusal leaves no
   operations row, so a corrected attempt may REUSE the same id — the
   id names the caller's intent, and the intent has not happened yet.
   The alternative (poisoning the id on refusal) would force clients
   to mint ids per attempt, reintroducing the very ambiguity WS-5
   removes. Fault-injected crashes behave identically: no partial
   operations row can exist because it commits with the effect or not
   at all.

Implementation shape (for the released slice, not begun): `_write`
gains an optional `operation=(participant, op_id, fingerprint)` and the
result-assembly that today happens AFTER `_write` returns (accept's
provider fields, create's ids, post's included list) moves inside the
transaction via a finalize step, so the STORED result is byte-identical
to the returned one.

**Successful no-ops consume the id (R76).** A SUCCESSFUL invocation
that commits no domain effect — notably the no-advance/losing
`seen_discussion` mark, which by design returns without an audit act —
is still a success the caller may lose the response to. With an op-id
it therefore COMMITS a transaction containing ONLY its operations row
(`seq NULL`, the no-op result stored verbatim) and no event: dense
event sequencing is untouched because sequences are allocated with
events, never with operation rows. The id is consumed; an exact retry
replays the STORED no-op result even if the cursor has since advanced
— the result names what THAT invocation did, not the current state —
and conflicting reuse refuses exactly as for effectful operations.
Without an id, the no-op remains free and unrecorded as today. A
REFUSAL still records nothing: refusals are failures, no-ops are
successes, and only successes consume identity.

## 5. Retry lookup versus validation, later state, and identity (P6)

Ordering: **participant identity gate first, then retry lookup, then
ordinary validation.**

- The configuration boundary stays absolute: `--participant` must name
  a member of the CURRENTLY accepted generation before any output —
  replay included. A member removed by a later generation cannot
  retrieve their old results through the mutation surface (their
  teammates read the audit instead). Recommended (P6a) because one
  identity rule everywhere beats a replay-only carve-out through the
  config boundary.
- Retry lookup precedes domain validation: a committed operation
  replays its stored result even though the Work has since closed, the
  handler was reassigned, the label was removed, or the phase moved —
  the ORIGINAL commit was valid at its sequence, and the replay is a
  read of that fact, not a new act. Handler reassignment therefore
  never turns a lost response into a permanently unrecoverable one.
- Disclosure stays coherent: the stored result is returned only to the
  SAME participant key that committed it. No cross-participant lookup
  exists, so the operations table adds no new visibility surface
  beyond what the actor already received once.
- Restart: the operations table is ordinary durable state; a fresh
  `Authority` on the same file replays identically. Nothing lives in
  memory.

## 6. Result envelope, retention, audit, and pagination (P7, P8)

- **Envelope (revised per R78).** A bare boolean cannot distinguish a
  PROTECTED fresh commit from an UNPROTECTED id-less call, so every
  mutation result (and its stored copy) carries an explicit
  `"operation"` field with exactly three shapes:
  - `"operation": null` — no op-id was supplied; the call ran in the
    weaker tier and is NOT replayable (read before retry applies);
  - `"operation": {"id": <op_id>, "state": "committed"}` — a fresh
    protected success, effectful or no-op alike (a no-op's own result
    body already says so, e.g. `advanced: false`), now replayable;
  - `"operation": {"id": <op_id>, "state": "replayed"}` — an exact
    retry returning the STORED result with its ORIGINAL seq (or the
    stored no-op shape with no seq).
  init and regen results carry the same three shapes. The stored copy
  records `state: "committed"`; the replay path rewrites only the
  state field on the way out, so the domain payload stays
  byte-identical. Replays consume no sequence and write no byte
  (purity hash-sweep material). Projection version bumps minor:
  2.1 → 2.2 (additive field). The earlier `already_committed` boolean
  proposal is WITHDRAWN in favor of this single explicit field.
- **Retention (P8 — recommendation: permanent).** Operations rows are
  append-only history, small (a hash, an id, one JSON result), and the
  guarantee they carry should not silently expire — a bounded TTL
  would turn "effectively once" into "effectively once, recently".
  GC/archival can be a later explicit product decision alongside any
  event-journal compaction; WS-5 ships none.
- **Audit projection (revised per R79).** A pure paged read of ONE'S
  OWN operation records — the CLI verb pages on the history's OWN
  dense `recorded` cursor, never the domain `seq` (which is NULL for
  no-op rows and therefore cannot totally order this list):
  `operation-log --after RECORDED --limit N` → rows (recorded, op_id,
  fingerprint, seq-or-null, created_ts; results replay through the
  mutation path, the listing is bookkeeping) under the shared
  `_page_bounds` contract (non-negative cursor, limit 1..500,
  explicit `next_after` = last `recorded`, one snapshot). Dense event
  sequencing is untouched: replays emit no event; fresh commits emit
  exactly one as today.
- **init/regen (P9, revised per R77).** `accept_config` accepts
  `--op-id` with the fingerprint over the actor plus the proposed
  document's canonical digest (already computed today); the operations
  row commits in the acceptance transaction under the validated
  acting participant.
  `init` is today participant-LESS and refuses an existing destination
  before any lookup could run — so "init with an op-id" needs a real
  identity rule, not hand-waving (R77). RECOMMENDED (P9a): init gains
  a required `--participant` naming a member of the PROPOSED
  generation-1 document, validated against that document before any
  filesystem effect; the operations row commits under that identity in
  the same transaction that creates the schema and seeds the topology.
  On an EXISTING initialized authority the identity gate comes FIRST
  and is explicit (R81): `--participant` is validated against that
  authority's CURRENTLY ACCEPTED generation — the uniform config
  boundary, exactly as for every other operation — before any lookup
  runs; an identity the current generation does not know refuses
  there, learning nothing. Only then does the safe lookup run against
  that authority's operations table: exact `(participant, op_id)` +
  equal fingerprint (over the canonical digest of the proposed
  document) → replay the stored init result; same key, different
  fingerprint → closed conflict refusal; no record, or no id supplied
  → refuse "already initialized" exactly as today. The
  proposed-document validation of the participant applies only on the
  FRESH-init path, where no accepted generation exists yet. The
  lookup only READS the existing store and discloses a result only to
  the identity that committed it. Alternative (P9b):
  exclude init from WS-5 and state that the first operation of every
  authority carries only the weaker tier — returned as a real product
  choice rather than silently assumed.

## 7. WF-09 expanded on paper: the WS-5 battery (source + packaged)

WF-09 grows (or gains a sibling WF-12, reviewer's choice — recommend a
sibling so WF-09's accepted race narrative stays stable) into:

1. **Lost response, exact retry**: commit a `say --request` with an
   op-id through the CLI, discard the response, retry verbatim —
   one obligation, one event; the first result carries
   `operation: {id, state: "committed"}` and the replay the SAME
   domain payload with `operation: {id, state: "replayed"}` and the
   original seq (R80: the withdrawn boolean appears nowhere).
2. **Same-id same-request race**: two spawned identical invocations —
   exactly one effect; both exits report the SAME result, one fresh
   and one replay; audit dense with one event.
3. **Same-id conflicting request / conflicting actor**: same id with a
   different body refuses closed without mutation; the same id VALUE
   under a different participant is independent (scope proof).
4. **Refusal then correction**: a refused attempt (unknown outcome,
   say) followed by a corrected attempt under the SAME id commits; the
   id was not poisoned.
5. **Crash at every boundary**: fault injection through a
   full-featured operation (accept --create with an op-id) — no
   partial operations row, no false success, corrected retry commits.
6. **Restart**: replay after closing and reopening the authority.
7. **Later-state replay**: commit a pass with an id, close the Work,
   retry the pass — the stored result replays although a fresh pass
   would refuse; then a FRESH pass (new id) refuses on the closed
   Work.
8. **Config-generation race**: handler reassignment landing mid-flight
   (both orders) — the fresh attempt refuses or commits under the
   committing generation exactly as today; the committed one replays
   after the reassignment.
9. **Every mutation family**: a table-driven sweep giving each family
   one exact-retry and one conflicting-reuse case (Work, discussion,
   seen, obligation, verification, revision, config).
10. **No-op identity consumption (R76)**: an op-id-bearing losing mark
    consumes its id (operations row, no event, dense audit unchanged);
    its exact retry replays `advanced: false` VERBATIM after another
    mark has advanced the cursor; conflicting reuse of the consumed id
    refuses.
11. **Init identity (R77, if P9a rules)**: init with `--participant` +
    op-id; lost response; exact re-init replays the original result
    against the existing authority; a different document under the
    same id refuses conflict; id-less re-init refuses "already
    initialized".

Focused regressions (named for the slice): grammar/scope refusals;
fingerprint spelling-invariance and resolution-exclusion; the
three-step lookup algorithm races (`_interleave` both orders);
replay purity (hash sweep); envelope shape; operations listing
pagination bounds; retention (no GC path exists); init/regen ids.
Break-sweeps: drop the in-lock recheck (race regression bites), store
the result outside the transaction (crash sweep bites), fingerprint
over the resolved `--on` instead of the typed input (later-state
regression bites), poison-on-refusal (correction regression bites),
global scope (cross-participant independence bites).

## 8. Unresolved product choices returned for ruling

- **P1 scope** — per-participant `(participant, op_id)` uniqueness.
  RECOMMEND as specified; alternative global scope rejected above.
- **P2 mandatory vs optional** — RECOMMEND optional-with-honest-tiers;
  alternative: mandatory for mutations invoked with `--participant`
  agents cannot be distinguished from humans, so mandatory means
  mandatory for everyone.
- **P5 refusal non-poisoning** — RECOMMEND refusals record nothing and
  ids survive for corrected attempts; alternative (record refusals)
  rejected as id-per-attempt ceremony.
- **P6a removed-member replay** — RECOMMEND the uniform config
  identity boundary (no replay for removed identities); alternative: a
  replay-only carve-out.
- **P8 retention** — RECOMMEND permanent, GC deferred to an explicit
  later ruling; alternative: bounded TTL with a stated expiry in the
  envelope.
- **P9 init coverage (revised per R77)** — RECOMMEND P9a: init gains
  a required `--participant` validated against the proposed
  generation-1 document, records its operation under that identity in
  the initializing transaction, and an op-id-bearing re-init performs
  the safe exact/conflict lookup against the existing authority.
  Alternative P9b: exclude init and state the first operation carries
  only the weaker tier. This is a REAL surface change (init grows a
  required flag) and needs Slawomir's explicit choice.
- **P11 no-op identity (R76)** — RECOMMEND: every SUCCESSFUL op-id
  invocation consumes the id and stores its replayable result, no-ops
  included, committing an operations row with NO domain event;
  refusals alone leave the id unconsumed. Alternative (id-less no-ops
  stay unrecorded when an id WAS supplied) is withdrawn as the R76
  contradiction.
- **P12 envelope (R78)** — RECOMMEND the three-shape `operation`
  field (`null` / `committed` / `replayed`) on every mutation result
  incl. init/regen and no-ops; `already_committed` is withdrawn.
- **P10 battery placement** — RECOMMEND a new WF-12 battery beside
  WF-09 rather than rewriting the accepted WF-09 text.
- **No contradiction found** with the chronological rulings: dense
  sequencing, pure reads, the R73 JSON-refusal contract, R63/R75
  pagination, and the identity boundary all compose with the design
  above. The one behavioral supersession is intentional and pinned by
  the WS-5 ruling itself: the "read before retry" limitation stops
  being documented as a limitation and becomes the stated weaker tier
  of id-less calls.

Stopping here for reviewer and Slawomir rulings; no implementation
begun, no later phase touched.

## Post-review corrections (R76–R78, first design review)

- **R76** — successful no-op invocations bearing an op-id CONSUME the
  identity: an operations row (seq NULL, stored no-op result) commits
  with no domain event; exact retries replay the stored result verbatim
  even after later cursor advances; refusals alone leave an id
  unconsumed. §4 and the battery updated; new P11.
- **R77** — init identity made explicit instead of assumed: P9a
  (recommended) adds a required generation-1-validated `--participant`
  to init, records the operation in the initializing transaction, and
  defines the safe exact/conflict lookup against an EXISTING authority
  before the "already initialized" refusal; P9b (exclusion) returned as
  the honest alternative. §6 updated; battery case 11 added.
- **R78** — the boolean envelope is withdrawn for the explicit
  three-shape `operation` field distinguishing unprotected, fresh
  protected, and replayed results across every mutation, no-op, and
  init/regen shape. §6 updated; new P12.

## Post-review corrections (R79–R81, second design review)

- **R79** — the operations table gains its own dense `recorded`
  cursor (allocated in the recording transaction, total over
  effectful AND no-op rows); the listing verb (`operation-log`) pages
  on `recorded`, never the partial domain `seq`. §4 and §6 updated.
- **R80** — battery case 1 rewritten to assert the
  `committed`/`replayed` operation shapes; the withdrawn
  `already_committed` boolean appears nowhere.
- **R81** — on an existing authority, init's `--participant` is
  validated against the CURRENTLY accepted generation before the
  replay lookup (uniform identity boundary, no disclosure to unknown
  identities); the proposed-document validation applies only to the
  fresh-init path. §6/P9a updated.
