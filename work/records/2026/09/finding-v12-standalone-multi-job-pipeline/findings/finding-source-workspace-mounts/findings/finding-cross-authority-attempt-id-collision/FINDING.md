# Cross-authority attempt identifiers collide

## Finding

**Observed 2026-09-04.** A fresh standalone v12 Job Manager authority tried to
start the first episode of a stage whose local stage name matched an earlier
retained trial. Both authorities derived the same offer and attempt
identifiers. OCI reconciliation found the retained container and correctly
refused to adopt it because its immutable `authority_uuid` label named the
earlier authority.

The fresh authority was `e0cccafbe81ae8072de8e24b45091283`; the retained
container named `26050b09a89ab20c0a0e631723fce6c0`. Both produced attempt
`attempt-1851504c0486e885c0d71be5f9b73e09c1352b4b11c9e7a5e97e904dc71ec76e`.
The fresh manager committed a `policy/denied` runtime-start failure, recorded
the execution runtime as uncertain, and did not dispatch a provider turn.

**Confirmed.**
`v12/python/src/baton_v12/job_manager/episodes.py::identities` derives the
offer/attempt seed only from `stage_id` and `episode`. Those values are local
to one Job store and are not globally unique. Independent authorities can
therefore derive the same OCI identity without sharing any Work, store, or
assignment.

The adapter's authority-label check behaved correctly and must remain
fail-closed. The defect is the identity namespace supplied to the adapter,
not reconciliation's refusal to adopt a container owned by another authority.

## Decision boundary

Offer and attempt identities must include the owning authority namespace in
their canonical derivation. The change must preserve deterministic retry
within one authority, keep offer and attempt identities derived from the same
assignment episode, and make otherwise identical stage/episode pairs differ
across authorities.

The derivation input must be an explicit stable authority identity, not a
database path, process incarnation, hostname, current time, random retry
value, or other deployment-local surrogate. Existing fail-closed runtime
label validation remains unchanged.

## Required evidence

- A positive vector proving stable replay within one authority.
- A cross-authority vector proving distinct identifiers for identical local
  stage and episode values.
- Focused Job Manager and OCI regressions proving the correct old-authority
  container is refused and a fresh-authority attempt can start independently.
- Review of every call site so no caller silently omits or invents the
  authority namespace.

## Reviewer research — 2026-09-04

**Observed.** The current function reproduces the collision without an OCI
engine. For stage `job-a/implementation`, episode 1, both example authorities
produce
`offer-ad83af8ebc99ab662c58acd8bedb8273c8680fda7e0e546f7b9bc43b01b8513b`
and the corresponding `attempt-...` value. A canonical seed containing
`authority_uuid`, `stage_id`, and `episode` produced distinct digests for the
two authorities and replayed byte-for-byte for the same authority.

**Confirmed.** There are exactly two production derivation call sites, both in
`v12/python/src/baton_v12/job_manager/episodes.py`: `open_first` and
`open_next`. The former runs inside `submit`, before a deployment operations
factory exists; the latter runs from the persisted Job store during
replacement. Passing the namespace only through
`tools.single_worker.operations_from` is therefore too late for episode 1 and
would leave the two episode-opening paths deriving identities from different
inputs.

**Confirmed.** `JobStore` currently persists only `store_kind` and
`schema_version` in `meta`. `tools/job_manager.py::_job_store` accepts only the
path, process incarnation, and clock. The production factory later opens an
Authority with the configured expected UUID, but currently executes
`del job_store`; it neither proves that the Job store belongs to that
Authority nor supplies an identity namespace to it. `submit` and read-only
`status` intentionally construct no Authority capability, so the namespace
must be explicit store-opening data rather than discovered by reaching into an
Authority database.

**Confirmed.** The existing safety check is correct and separate from the
derivation defect. `OciAdapter.list` selects candidates only by
`runtime_attempt_id`, owns every returned `baton.v12.*` label, and compares the
complete returned label set with the requested assignment. In particular,
`tests/manager/test_oci.py::test_every_label_that_contradicts_the_request_is_refused`
already proves that a returned candidate carrying another `authority_uuid` is
denied. That comparison must not be weakened or replaced by extra engine-side
filters.

**Confirmed.** Episode identity is persisted evidence, not a value readers
recompute. The schema-1-to-2 migration deliberately copies prior offer and
attempt strings so existing Worker Manager journal keys and Job receipts are
not orphaned. The namespace correction has the same compatibility obligation:
it changes identities only when a new episode row is opened.

**Observed baseline.** Before any correction,
`python3 -m unittest discover -s tests/job_manager -t .` with `PYTHONPATH=src`
passes 246 tests, and `tests.tools.test_single_worker` with
`PYTHONPATH=src:.:../worker` passes 71 tests.

## Proposed implementation boundary

**Proposed.** Bind each Job store to one explicit Authority UUID and persist
that binding in `meta`. `JobStore.open` should require the UUID, validate it
against the existing 32-lowercase-hex authority rule before touching a path,
expose the accepted value as `store.authority_uuid`, and refuse a later open
that supplies a different UUID without changing the database. Reuse the
existing authority UUID vocabulary rather than introducing a second looser
spelling in the Job Manager.

This is a store binding, not a shared transaction or a capability. The
Authority, Worker Manager control, and Job stores remain separate files and
owners. `submit` and `status` learn only the stable public identity required to
open their Job store; neither receives an Authority session, store path, or
mutation surface.

**Proposed.** Bump the Job-store schema and make schema-1 and schema-2 adoption
atomically pin the explicitly supplied Authority UUID while preserving every
existing episode, receipt, and operation byte. A failed migration must roll
back the UUID and version stamp together. A new store writes kind, version,
and UUID in its initialization transaction.

**Proposed.** Change the canonical derivation to hash
`{"authority_uuid": ..., "stage_id": ..., "episode": ...}` and keep the
existing `offer-<digest>` / `attempt-<digest>` spelling. Both `open_first` and
`open_next` obtain the namespace from the already-open `JobStore`; no caller
may default, infer, or separately cache it. Existing episode rows are always
read unchanged.

**Proposed.** Add a required `--authority-uuid` Job Manager operand and pass it
to every `JobStore.open` for `submit`, `status`, and `serve`. Update the
documented production invocations. In
`tools.single_worker.operations_from`, compare `job_store.authority_uuid` with
the validated production configuration UUID before configuring the control
store, certifying a profile, allocating storage, or opening the Authority. A
mismatch is a fail-closed deployment error with no partial control-store
configuration.

## Migration and rollout boundary

**Confirmed.** Migration must not rename a live legacy offer or attempt. An
already-recorded unnamespaced episode can still meet a retained container from
another Authority and must continue to fail closed. Merely stopping that
container does not erase the fresh manager's durable start-failure record or
turn the legacy attempt into a namespaced one.

**Proposed.** Production acceptance should therefore use fresh Job and Worker
Manager control stores under the corrected build (or another explicitly
scheduled recovery that creates a new episode); it must not claim that opening
an old store repairs existing episode identities. Retained old containers are
safe negative controls and operator cleanup, not migration inputs.

## Regression boundary

The bounded candidate should prove all of the following:

- malformed, missing, and uppercase Authority UUIDs refuse before a Job-store
  path is created or changed;
- a new store persists its UUID, a same-UUID/process-restart open succeeds,
  and a different-UUID open refuses byte-for-byte untouched;
- direct schema-1 and schema-2 migrations pin the supplied UUID atomically,
  preserve every prior episode identity and receipt, and use the namespace
  only for an episode opened after migration;
- the same `(authority_uuid, stage_id, episode)` deterministically replays,
  changing only the process incarnation changes nothing, and changing only
  `authority_uuid` changes both offer and attempt identities;
- first and replacement episode creation use the same namespace rule, retain
  the bounded worker `opaqueId` grammar, and keep offer and attempt suffixes on
  the same digest;
- the Job Manager CLI requires and threads the UUID for all three commands,
  while read-only status still holds no Authority capability;
- the production factory refuses a Job-store/config UUID mismatch before any
  durable control-store side effect;
- OCI reconciliation still refuses a same-attempt candidate labelled for the
  old Authority before `run`, while a correctly namespaced fresh attempt does
  not select the old attempt and can reach exactly one `run`;
- all existing Job Manager, production-composition, and focused OCI tests
  remain green.

## Historical coordination

W83781 was created after the live W71917 bootstrap exposed the collision. Its
first review turn refused because this bound dossier had not yet been created;
this record restores the missing durable specification before another
handoff.

## Correction decisions — 2026-09-04 — W83781, review pass 1

Independent review `review-2026-09-04T09-07-42Z.md` accepted the boundary and
returned one P0, two P1s and two P2s.

### The migration decides under its own lock

**This corrects the implementation, not the recorded boundary.** `_adopt` read
the schema version before `_migrate` asked for a write lock, and `_migrate`
acted on that pre-lock value. Two openers could therefore both observe schema
2: the first migrated and recorded its Authority, and the second acquired the
lock still believing the store was at 2, ran the step again and rebound. The
winner's episodes stayed in the winner's namespace while every future episode
would have been derived in the loser's — the cross-authority split this
binding exists to prevent, produced by the binding's own migration.

The version is now re-read under the lock and everything derives from that
read. A waiter that finds the store already at the current schema commits
nothing and returns; `_bound` is what then decides whether that opener may use
the store at all. The stamp is a plain `INSERT` rather than `INSERT OR
REPLACE`, because replacement semantics are wrong for a value that is
immutable once written: if a row is somehow already there, the primary key
refuses and the transaction rolls back, which is the correct answer to
"somebody else got here first".

### The store's own evidence is owned before it is compared

`_bound` read the persisted UUID as storable text and compared it. Text is not
an Authority, so a corrupt schema-3 row was reported as a valid store
belonging to a different Authority — sending an operator to look for an
Authority that does not exist — when what it actually was is this store's own
evidence being malformed. The persisted value now goes through the same rule
as the supplied one, so a corrupt row is `integrity/schema`.

### Two vectors that were promised and not exercised

The rollback this record requires was implemented and only its success path
was covered; it is now driven through the public `JobStore.open` boundary with
a failure raised from the final in-transaction validation — the one moment at
which both the schema-3 stamp and the binding are readable on the migration
connection and the COMMIT has not run — proving the prior version retained, no
binding surviving, every identity and receipt unchanged, and the store still
migratable afterwards. Where the failure is raised is the whole vector: an
injection before either value is written cannot distinguish this
implementation from one that stamps outside the transaction, which is what the
second review measured.

The OCI positive vector asserted that a fresh namespaced attempt reaches a
start and never called `start`. It now drives one through an engine that
retains the other Authority's container and honours the attempt-id selector,
and asserts exactly one `run`. Being handed an engine that is still holding
somebody else's runtime is what makes the answer mean anything; an empty
engine would have proved nothing about selection.

## Rebase decisions — 2026-09-04 — W83781 onto the integrated W85500

The signed-off candidate declared base `389cdd4`. The operator ordered W83781
behind W85500, W85500 was integrated, and the approved correction is being
rebased onto the result rather than imported over a stale base. Seven of the
seventeen source paths moved underneath it. Three decisions came out of that
and are pinned here because a later reader finding only the merge would have
no way to tell them from drift.

### The observation-only status surface keeps no binding comparison

`tools.single_worker._Observation` did not exist when this correction was
approved. It is W85500's read-only exchange reader, and it accepts a Job store
and deliberately does not read it. That stays true, and the reason is now
measurable rather than provisional.

`JobStore.open` requires the Authority operand and refuses a store bound to
another Authority without touching it, so a store's binding is already proved
against what the operator named before any factory sees it. What
`operations_from` compares is a different question — the deployment
CONFIGURATION's Authority against the store's — and it compares it because
every line after it writes. The observation surface only reads. A
configuration naming another Authority reaches another Authority's launch
home, where this store's namespaced attempt identities do not exist, so the
answer is `exchange: null` rather than a stranger's terminal.

**This supersedes the ordering sentence in that class's comment, and not its
decision.** That comment said the check stays out because W83781 is ordered
behind W85500 and a candidate there must not depend on it. That reason has
expired; the decision has not. Adding a refusal to a read-only surface is a
design change and needs its own pinned ruling and independent review, so it is
explicitly NOT taken in a rebase. The comment now carries both the original
reasoning and its supersession.

### The CLI operand is threaded through the invocations W85500 added

`--authority-uuid` is required on all three commands. W85500 added status
invocations to `tests/job_manager/test_tool.py` and
`tests/tools/test_single_worker.py`, and a documented `status --observe`
example to `DEPLOYMENT.md`, all of which were written when no such operand
existed. The three-way merge carried them across untouched because neither
side edited the other's lines — a clean textual merge that produced five
failing cases and one documented invocation this build refuses.

They are threaded, not weakened: each keeps every assertion it had. PLAN item
5 already schedules both test files as the explicit authority to adjust CLI
operands in them.

### The documented `--observe` example names an Authority

`DEPLOYMENT.md` gains both sections in full: W85500's three-freshnesses
account of `status`, and this Work's account of the Authority a Job store
belongs to. They are independent additions to the same chapter and neither is
a substitute for the other. The `status --observe` example inside the first
one carries `--authority-uuid`, because a documented invocation that this
build refuses is worse than no example.
