# A damaged attachment blocks the recipient's queue

Folder: `work/finding-damaged-attachment-queue/`
Status: **complete — both phases implemented, reviewed over two rounds, and
accepted for commit.** No live action outstanding. Test counts and hashes in
the phase-results sections are the historical record at each stage; the
current tree is tool 2.0.0 / protocol 7.
Raised by: the implementer on 2026-08-07, closing out
`work/finding-wait-notice-wakeup/`.
Contract decided by Slawomir: **skip and continue, plus an explicit audited
recovery path** (`contract_decision`, claim `403a641986b56746297e4d44d5169682`).
Separate tool defect; not a widening of the approved wait/notice patch.

While this finding is under review, its documents travel as **message
bodies**, never as hash-pinned attachments. Publishing a pinned attachment of
a document still being edited is what caused the outage in the first place.

## Problem

`Store.claim` selects the single oldest pending message for a recipient, calls
`verify_attachment`, and has **no fallthrough** to the next message
(`baton_v6.py:1066`). A stale attachment pin raises `EXIT_DAMAGE` (6), and
`wait_for_message` re-raises anything that is not `EXIT_NONE`.

One message whose pinned file changed after publication therefore makes
**every plain `wait` and `claim` by that recipient fail immediately and
permanently** — including for valid messages published behind it. The queue is
blocked from the head.

The damaged message also cannot be disposed of. Reproduced end to end in a
throwaway instance rather than inferred from the code:

| Attempt | Result |
| --- | --- |
| `claim` (plain) | exit 6 |
| `claim --message-id <damaged>` | exit 6 — `verify_attachment` runs regardless of how the message was selected |
| `close` | impossible; requires a claim that cannot be created |
| `gc` | no effect; collects only *transient* terminal metadata, these are durable |
| `recover-claim` | requires an active claim; none can exist |
| `doctor` | correctly reports it, `ok: false` — visible but not fixable |

So the message is **undeliverable and undisposable**: permanently `pending`,
permanently blocking, with no participant-level recovery path.

## Live impact at time of filing

`baton.reviewer` had two damaged messages at the head of its queue, so the
plain `wait` invocation every role brief instructs agents to run was bricked
for that participant. Three publications are affected:

- `da19ba84c2503ae9d7c4354609097550` — already terminal, still keeps `doctor` unhealthy
- `b1894f68fa4885cbe2e749d977afac7f` — pending
- `9cff508bcf03ef05a42f02e83a6609f3` — pending

## Cause, and the practice it changes

The implementer attached `FINDING.md` and `EVIDENCE.md` and then kept editing
those files as review progressed, invalidating three publications. The
attachment contract worked exactly as designed and failed closed; the mistake
was operational.

**Attachments pin at publication.** A document under revision must be sent as
a `--body` — copied into the store, immune to later edits — and attached only
once final.

That habit change is necessary but not sufficient: the present design turns a
routine authoring mistake into an unrecoverable queue outage. The tool
contract has to change too.

## Accepted contract

**Skip and continue**, with an explicit audited recovery path. Specifically:

- A plain `claim` skips attachment-damaged candidates and selects the oldest
  healthy, deliverable message in deterministic `(created_ts, id)` order.
- `wait` inherits this and can receive healthy messages published behind
  damaged entries.
- With only damaged messages pending, `wait` stays live without busy spinning
  and can still receive a later healthy publication.
- `claim --message-id <damaged>` continues to fail closed and creates no claim.
- Skipping never erases, repairs, claims, closes, or otherwise mutates the
  damaged message.
- Skipped damage is visible through `doctor` and through a machine-readable
  `scan`, without changing successful claim or wait delivery shapes.
- Healthy directed delivery keeps its existing `{"claim": …, "message": …}`
  shape.

**No claim is created for unverifiable content.** A claim currently means
Baton verified the selected message sufficiently to deliver it; turning damage
into a special disposable claim would weaken that guarantee for every
consumer. This is why the disposable-claim alternative was rejected.

## Delivery plan — two phases, and why

The urgent half and the schema half have very different costs, and folding
them together would delay the urgent half behind a coordinated outage.

### Phase 1 — restore queue liveness. Protocol 6, no migration.

Skip-and-continue plus the `scan` damage view require **no schema change**.
They ship on protocol 6 as a tool minor bump, with no migration and no
maintenance gate, and they immediately unblock `baton.reviewer` and any other
participant in the same state.

This is a strict subset of the accepted contract and is required regardless of
how phase 2 is designed.

### Phase 2 — audited recovery and instance health. Protocol 7, migration required.

The recovery verb needs two things the protocol-6 schema cannot express:

1. **A terminal damaged disposition.** `messages.state` is
   `CHECK(state IN ('pending','claimed','completed','closed','expired'))`.
   A damaged message must reach a terminal state that does not pretend its
   content was delivered, so a new `quarantined` state is required. (`expired`
   exists and is unused, but reusing it would misdescribe the disposition.)
2. **An audit record.** Recovery must record the original pinned attachment
   identity, the observed failure, the reason, actor, and timestamp. No
   existing table can hold that: `recoveries` requires a `claim_id` foreign key
   to a claim that cannot exist, `ceremonies` has a closed `kind` CHECK,
   and `transitions` has no reason or pin columns.

`_validate_schema` compares `sqlite_master` SQL text exactly and requires
`PRAGMA user_version == PROTOCOL_VERSION`, so either change is a protocol bump
to 7.

**The consequence Slawomir needs to weigh:** migrating the live instance to
protocol 7 requires `maintenance-enter`, which gates **every participant in
the deployment** — `lang`, `lang_testing`, `build`, `mariadb`, `net_tls`,
`dq`, `web`, `workflows`, `pushcoin` and `baton` alike, not just this project.
It is a suite-wide coordinated outage. It also means writing the first
migration in this tool's history: `migrate_instance` is currently a stub that
audits the attempt and then refuses, and `messages` cannot be `ALTER`ed to
change a CHECK, so the migration is a guarded table rebuild with the
claims/dispositions/responds_to foreign keys and every trigger reconstructed.

Both phases shipped; see the results sections below. Slawomir authorized
phase 2 immediately rather than deferring it, so the two landed together.

## Phase 2 design, as proposed at the time

New table:

    quarantines(quarantine_id PK, message_id UNIQUE REFERENCES messages(id),
                participant, actor, seed, reason, prior_state,
                attach_root_id, attach_path, attach_sha256, attach_size,
                attach_generation, failure, created_ts)

`UNIQUE(message_id)` gives idempotence structurally. The message's own
`attach_*` columns are left intact, so the evidence of what was originally
published is never destroyed — the quarantine row records it a second time
alongside the observed failure.

Verb `quarantine-attachment <message-id> --reason …`, requiring the `recovery`
capability as `recover-claim` does. It confirms the target actually fails
`verify_attachment`, refuses healthy/unknown/ineligible targets, and:

- if the message is `pending`, sets `state='quarantined'` with `completed_ts`
  (the existing `CHECK((state IN ('pending','claimed')) = (completed_ts IS
  NULL))` accommodates this without modification);
- if the message is already terminal — the `da19ba84…` case — leaves its state
  alone and records the quarantine row as an acknowledgement, which is what
  restores instance health.

Exact retry returns `already_committed`; a mismatched reason fails closed,
matching the existing `_verify_retry` idiom. `doctor` then separates
unresolved damage (a problem) from acknowledged damage (a warning).

## Regression coverage required

Slawomir's list, annotated by phase.

| # | Coverage | Phase |
| --- | --- | --- |
| 1 | damaged oldest then healthy — plain `claim` delivers the healthy one | 1 |
| 2 | `wait` with damaged pending receives a healthy message published later | 1 |
| 3 | damaged-only waiting does not exit, busy-spin, or create claims | 1 |
| 4 | explicit claim of a damaged message still fails closed | 1 |
| 5 | skipped messages remain pending and visible before recovery | 1 |
| 6 | recovery of an exact damaged pending message is atomic and audited | 2 |
| 7 | recovery refuses a healthy message | 2 |
| 8 | retry after committed recovery is idempotent | 2 |
| 9 | concurrent claim/recovery races preserve valid state | 2 |
| 10 | recovery of a stale attachment on an already-terminal message | 2 |
| 11 | after recovering all three stale publications, live `doctor` is healthy | 2 |
| 12 | healthy claim and reply/close semantics unchanged | 1 and 2 |
| 13 | polling and event-driven `wait` parity | 1 |
| 14 | distribution contains no Drift-specific assumptions | 1 and 2 |

## Phase 1 results — implemented

Tool **1.1.0**, protocol **6** (unchanged), no migration, no maintenance gate.

Changes in `baton_v6.py`:

- `Store._first_deliverable` — oldest pending message whose attachment still
  verifies, in `(created_ts, id)` order, plus a skipped count. `Store.claim`
  uses it for the unnamed case; an explicitly named `message_id` still calls
  `verify_attachment` directly and fails closed.
- Exhausting the queue with damage present raises `EXIT_NONE` (never
  `EXIT_DAMAGE`) with a diagnostic naming the skipped count — `EXIT_NONE` is
  what keeps a waiter alive to receive a later healthy publication.
- `Store.scan` gained a `damaged` array: the pending entries `claim` skips,
  each with its pinned attachment tuple and the observed failure. Damaged
  entries also remain in `pending`, because they are pending — `damaged` is a
  second lens on the same rows, not a separate queue.
- `verify_attachment` now classifies **any** failure to re-resolve a
  previously pinned attachment as `EXIT_DAMAGE`. A deleted or newly unreadable
  file previously raised a validation error, so it would have been re-raised
  instead of skipped — the same blocking outage through a different door. The
  reclassification is sound because the attachment resolved cleanly at
  publication, so a later resolve failure is by definition post-publication
  damage. Publication-time validation is untouched.

`wait` required no change: it inherits skipping through `claim`, and the
`EXIT_NONE` mapping keeps it live and non-spinning.

### Two baseline tests were modified — disclosed deliberately

This is the first time in this work that pre-existing tests changed, so it
should not pass unremarked:

- `TestAttachments::test_post_publication_mutation_fails_at_claim`
- `TestRootBindingGenerations::test_binding_generation_mismatch_is_damage`

Both asserted that a *plain* `claim` raises `EXIT_DAMAGE`, which is precisely
the behavior Slawomir's contract replaces. Neither was weakened. The property
each protected — tampered or wrongly bound content is never delivered — is now
asserted on **both** paths: the explicit target still fails closed with the
original diagnostic and regex, and the plain claim is additionally asserted to
report nothing deliverable, leave the message `pending`, and create no claim.
Each test is strictly stronger than before.

### Verification

- **292 passed, 0 failed** (280 before this phase, plus 12 new).
- Regression-first: the 12 new tests were written before the implementation;
  10 failed and 2 passed (the two parity pins that must hold either way).
- Live instance, read-only via the rebuilt 1.1.0 binary: `scan --participant
  baton.reviewer` reports `pending: 2, damaged: 2`, naming both stale pins and
  their failures. Nothing was mutated.

## Phase 2 results — implemented

Authorized by Slawomir as the preferred upgrade window. Tool **2.0.0**,
protocol **7**. `RUNBOOK.md` carries the migration procedure and its rehearsal.

**Schema (protocol 7):**

- `messages.state` gains `quarantined`; `trg_msg_edge` gains the
  `pending → quarantined` edge, and `trg_msg_completed_ts_guard` accepts the
  timestamp that comes with it. The existing
  `CHECK((state IN ('pending','claimed')) = (completed_ts IS NULL))` needed no
  change.
- New `quarantines` table, `UNIQUE(message_id)` so idempotence is structural,
  recording prior state, the full original pin, the observed failure, actor,
  seed, reason and timestamp. Insert requires verb `quarantine`; update and
  delete are refused outright — it is permanent audit.
- `trg_meta_frozen` narrowed: `protocol` moved out of the unconditionally
  immutable set into a new `trg_meta_protocol_guard` that permits it under
  verb `migrate` only. Without this a migration could not move the protocol
  without disarming a guard, and disarming guards to migrate is how audit
  trails get laundered.
- Ledger: `(message, pending, quarantined)` under verb `quarantine`.

**`quarantine-attachment <message-id> --reason …`** requires the `recovery`
capability. It verifies outside the write lock that the target genuinely
fails, refuses healthy / unknown / bodyless / claimed-in-flight targets, and
either moves a `pending` message to terminal `quarantined` or, for an
already-terminal message, records the acknowledgement without rewriting
history. Exact retry returns `already_committed`; a different reason fails
closed.

**`doctor`** now separates unresolved damage (a problem) from acknowledged
damage (a warning), and lists `quarantined`. Without that split, instance
health would be permanently unreachable once any pin legitimately went stale.

**Migration** validates the source against protocol 6's own frozen schema
first and refuses anything else, then rebuilds `messages` (SQLite cannot alter
a CHECK, and `ALTER … RENAME` would rewrite the stored SQL with quoting that
exact-text validation rejects), restores rows, rebuilds indexes and triggers,
adds the v7 objects, and accepts the generation+1 config in the same
transaction. It **ends by running the full protocol-7 `_validate_schema`
before committing** — that self-check is the real safety property, and it
immediately caught a genuine bug during development: `DROP TABLE` takes the
table's indexes as well as its triggers, and the first draft rebuilt only the
triggers.

### Verification

- **309 passed, 0 failed** (292 before this phase, plus 17 new).
- Rehearsed end-to-end on a byte copy of the live instance: 51 messages
  preserved, state counts identical, the same three problems and nothing new,
  then `doctor` `ok: true` after recovery. Full table in `RUNBOOK.md`.
- Slawomir's regression items 6–11 are covered, plus rollback-to-intact-v6,
  capability, generation-bump, altered-source-schema and unknown-protocol
  refusals.

### Assets and a consequence I caused

`example-baton.json` and `config-schema.json` move to `protocol_version: 7`,
and `bin/baton` is rebuilt.

Because the repository's `bin/baton` is the deployed executable, taking it to
protocol 7 **broke every team's access to the still-protocol-6 live
instance** — config validation rejects `protocol_version: 6` before anything
else runs. A protocol-6 executable is staged at
`/home/sl/src/baton-protocol6/bin/baton` and the runbook directs all
live-instance work there until the migration completes. The phase-1 executable
(1.1.0) was never committed and no longer exists as an artifact, so the
fallback is the committed 1.0.0, which predates skip-and-continue. Consequence:
the reviewer must keep using `claim --message-id` until migration, which is why
handoff ids continue to be reported to Slawomir.

## Review round 1 — eight items, all addressed

Reviewer reproduced four defects with adversarial tests; all four now pass,
kept as a separate check rather than absorbed. Suite: **322 passed, 0 failed**.

| # | Item | Resolution |
| --- | --- | --- |
| 1 | Quarantine must run under the gate | Ceremony `quarantine`: authorized under a plain maintenance gate, refused during `moving`/`moved` inside the transaction. Ordinary writes stay gated. |
| 2 | WAL-unsafe backup/restore | `snapshot` verb reusing `checkpoint_drain` + the move ceremony's hash-verified fsynced no-clobber publish, then opens and validates the copy. `migrate --snapshot-dir` takes it automatically. |
| 3 | Retry depended on the file staying damaged | `_committed_quarantine` resolves retry identity before any file is read, comparing the full `(participant, actor, seed, reason)` tuple; in-transaction repeat preserved for races. |
| 4 | Quarantine row broke `gc` | Quarantine-referenced messages are retained anchors alongside recovery-referenced ones. |
| 5 | `quarantined` reachable under any verb | `trg_msg_edge` requires `verb = 'quarantine'` on the edge. `doctor` gained bidirectional coherence checks (record exists, pin matches, prior/current state agree, exactly one `quarantine` ledger edge). |
| 6 | Protocol briefly unguarded | Narrowed guard installed **before** the blanket guard is dropped; also constrained to a one-step advance. Fault seam proves both guards live at the seam and exact v6 restoration on rollback. |
| 7 | Drain was only a runbook precondition | Enforced inside the migration transaction; refuses with `EXIT_RACE` naming the count and first claim. |
| 8 | Fallback executable unpinned | Both executables' artifact/source/protocol-doc hashes and `--version` strings recorded in `RUNBOOK.md`. |

### Two second-order defects the rehearsal found, which reasoning had not

**`close` and `reply` are themselves gated.** So claims cannot be drained
*after* entering maintenance. The previous runbook told the operator to verify
no active claims and then gate — with no way to resolve one if found short of
dropping the gate. Order corrected to drain → gate → stage config → migrate →
quarantine → verify → reopen. This is also what makes item 7 load-bearing
rather than belt-and-braces: the in-transaction check is the only thing
closing the drain-to-gate window, and it fired for real on a copy of the live
instance carrying two active claims.

**The pre-migration snapshot was not restorable.** Taken after the
generation-3 config is staged, it captured a protocol-6 database paired with
the protocol-7 config — openable by neither executable. A rollback artifact
that cannot roll back is worse than none, because it invites false confidence.

Fixed by having `migrate --snapshot-dir` write a **reconstructed generation-2
protocol-6 config** beside the old database. The reconstruction is proved, not
assumed: setting `generation` and `protocol_version` back must reproduce the
accepted `config_sha256`, or the migration refuses. That single mechanism also
enforces the "diff is exactly two fields" property, pointing at `regen` for
anything else. `validate_config` and `_check_meta` gained a scoped
prior-protocol allowance so a pre-migration instance and its snapshot can be
opened; the generation+1 rule now applies only to non-readonly migrate opens,
since a read-only one is an inspection.

Verified: the snapshot reopens under the protocol-6 executable as protocol 6,
generation 2, 55 messages, after its WAL siblings are removed.

## Migration architecture: availability is the invariant

**Channel availability outranks preservation of pending or historical
messages.** Porting old state is optional and off the critical path — in most
incidents nobody needs it, and once communication works actors re-send what
matters.

The default and primary migration shape is therefore: retire the old mailbox
intact, stand up a **verified empty** instance on the target protocol at the
canonical path, reconnect immediately, and treat any port as a separate
optional recovery operation performed only on demonstrated need. This is
`RUNBOOK.md`. The in-place procedure is `RUNBOOK-offline-migration.md` and is
never used on a live deployment.

Established by Slawomir after this deployment could not coordinate for over
**ten hours** during an in-place cutover. The in-place machinery still ships
and remains useful when applied to a *copy*, where it costs no availability.

I designed this migration in-place, which maximizes continuity and minimizes
moving parts. What I underweighted is that it makes the whole deployment's
coordination unavailable for the entire duration — **including the review of
the migration itself**. That is not hypothetical: this cutover stalled
awaiting review, every team stayed blocked, and the channel they needed in
order to unblock it was the channel that was blocked. Pending messages are
cheap to re-send; a jammed coordination channel is expensive precisely because
working around it requires the channel.

The in-place machinery is not wasted — it is the correct procedure for
migrating a *copy*, which is what the offline port in step 4 is, and what
repairing the retired authority now is. Applied off the live path it carries
no availability cost.

## Live-instance authority — resolved by the mailbox reset

**No live action is outstanding.** The three damaged records were never
altered on the live authority, and they are no longer on it: the blocked
protocol-6 mailbox was retired on 2026-08-07 and replaced with a fresh
protocol-7 instance, which reports `doctor ok: true`. The records live only in
the retired archive.

They were therefore never repaired, and the recovery commands drafted for them
were never run. That is the correct outcome — the reset removed the urgency
that made repair worth a maintenance window at all.

Not done, and deliberately: the stale pins were not reconstructed. Hand-
reverting a file to satisfy a pin forges the evidence the pin exists to
protect. No raw SQL, and no use of `regen` to erase audit history.
