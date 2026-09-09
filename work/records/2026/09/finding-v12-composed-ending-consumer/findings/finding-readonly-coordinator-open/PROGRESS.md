# Implementation progress

No implementation has begun. The actual change author appends an attributable
entry after its successful claim; reviewer coordination stays in FINDING/PLAN.

## 2026-09-09 — baton.claude, claim 126986

**Claimed first**, at seq126986, before reading the dossier and before any
edit.

### Revalidation

`IntegrationStore.open` connects read-write, `_initialize`s an absent or empty
store under `BEGIN IMMEDIATE`, and then asks for persistent WAL through
`_concurrent` — so today's only opener creates and writes. The pieces to reuse
are `_objects`, `_adopt` (the ownership decision, which refuses a foreign or
unexpected-metadata store untouched), `snapshot` (this store's own coherent
read transaction) and `_now`. The write boundary a read-only handle must close
is `transact`; `_record` is reached only from inside it and there is no public
`run`.

Implementing the pinned API as written; no clarification needed. The store
stays target-keyed and acquires no Authority identity.

### Question and budget, declared before any execution

Does the new opener read an existing coordinator's committed entry, lease and
history data — including data a concurrent serving coordinator commits after it
opened — while creating nothing and changing no byte, and does the handle
refuse every transition before it writes?

Budget: **cumulative 20s across every test and probe process**, focused
selectors on the one owned test module, each run and its elapsed time recorded,
stopping at the limit.

### Delivered

`IntegrationStore.open_readonly(path, *, incarnation, clock)`, exactly as
pinned. The connection is `file:<path>?mode=ro`, so SQLite itself refuses every
write; `immutable=1` is deliberately not used, because it asserts the file
cannot change and that is false of a coordinator two Authorities may be
contending for. The ownership decision is `_adopt`'s — made on the connection
that is handed back, inside this store's own `snapshot` — so a foreign store,
one carrying metadata this build does not own, and one at another schema
version are each refused untouched. No initialization, migration, write lock,
checkpoint, persistent PRAGMA or permissions change; `_now` is proved at the
open exactly as `open` proves it. The store stays target-keyed and acquires no
Authority identity.

**The one place its answer differs from `open`'s** is an empty database:
`open` initializes it and this refuses it, which is the reason this opener
exists.

Transitions refuse at this coordinator's own boundary — `transact` raises
`refused/capability` before the operands are owned, before the transaction and
before anything external. `_record` is reached only from inside it and there is
no public `run`.

### The same limitation the Authority half reports

A coordinator in WAL mode with **neither `-wal` nor `-shm` present is
refused**, with the reason named: opening it read-only makes SQLite create
both, and a read-only connection cannot remove them. So this reads a
coordinator *while a process is holding it* — the case the allocation names,
and the control proves the reader sees entries committed after it opened — but
not a quiescent one. Reported for the consumer's disposition rather than
resolved by a fallback the allocation excludes.

### Verified

`tests.integration.test_coordinator` 207 OK (195 at claim start; every addition
is a new class and no existing assertion changed), and `test_driver` 109 OK
over the same store. The controls use the **public** entry, target, lease and
live-grant readers, including the composed possession proof this store's
snapshot exists for. **7.2s against the declared 20s**; every run, its result
and its elapsed time is in `evidence/provider-126986.json` with claim-start and
final hashes and modes.

### Next

Independent acceptance at `baton.bug`. This is the coordinator half; it
implements neither the consumer's status factory nor the terminal handoff, and
invents no dependency on the Authority sibling W126880.

## 2026-09-09 — baton.claude, claim 127073 (correction)

**Claimed first**, at seq127073. Both findings are correct.

**Budget carried forward, not reset**: 7.2s spent, so at most **12.8s
remains**. Every run below is an exact command with its wall time and its raw
log retained in `evidence/`, which the previous evidence summarized.

### The diagnosis this correction stands on

The sibling W126880 measured the actual SQLite opening boundary at claim127026
(`../finding-readonly-authority-open/evidence/diagnosis-127026.json`, sqlite
3.46.1): through `mode=ro`, SQLite creates whichever of `-wal` and `-shm` is
missing and creates nothing only when BOTH are present or a writer is attached;
`nolock=1` refuses a WAL database outright either way. A second measurement
(`race-127026.json`) located where they are actually attached: not at `connect`
and not at `SELECT 1`, but at the first statement that reads a table.

**That sibling correction is itself unaccepted** — returned at seq127067 — so
what is reused here is the measurement, not an accepted artifact, and both
halves should be judged together.

### Question and budget, declared before any execution

Do partial sidecars refuse without completing the pair, does a store SQLite
cannot read refuse in this coordinator's own taxonomy, and does neither leave a
file behind?

### Delta

Both findings corrected; details, controls and every timed run with its raw log
are in `evidence/provider-127073.json`.

**[P1]** The pre-check permitted a WAL store when *either* sidecar existed, so
SQLite created the other and the open succeeded on an artifact it had just
made. Both are now required, and the same fact is read again **after the first
statement that reads a table** — the measured point where SQLite actually
attaches them — comparing **device and inode**, because names cannot see a pair
that was removed and recreated. An artifact the race produces is reported and
left: removing it is the post-hoc cleanup the allocation and both reviews
exclude, and it would race another opener's own file.

**[P2]** `_objects` is the first statement to touch the schema and its
`sqlite3.DatabaseError` escaped a public opener. It is now translated at its
owning boundary into this coordinator's `refused/precondition`, with the handle
closed and the file preserved — and only SQLite's own failures are translated,
which a `MemoryError` control drives.

Also added, as scheduled: another-schema-version (over a store this build
*owns*, since `_adopt` refuses on kind before version), read-only filesystem
where the platform allows, and a committed-history control that shows
`entries_of` agreeing its rows with the journal — emptying that journal makes
the same read refuse.

The reviewer's probe, unmodified, now refuses all four cases and creates
nothing: `evidence/replay-127025-probe-127073.json`.

**Residual, same as the Authority half's:** in the race the refusal follows
creation, so that open can leave sidecars behind even though it refuses. It
cannot be closed here, and the same three smallest decisions apply — accept the
race, permit removal of artifacts identified by device and inode, or require
the consumer to read only while a process holds the store. Not mine to choose.

`test_coordinator` **213 OK** (195 at claim start), `test_driver` 109 OK; every
existing assertion unchanged. **Budget carried, not reset: 4.3s this pass,
11.5s cumulative of 20s**, each command timed and its log retained.

## 2026-09-09 — baton.claude, claim 128308 (owner amendment)

**Claimed first**, at seq128308, before reading the review and before any edit.

### Ledger reconciled, before any test or probe

The reviewer measured my correction runs at **4.296s**, consistent with the
4.3s I reported. The **7.2s carry-in stands but remains subject to the evidence
limitation** recorded in review-2026-09-09T10-10-57Z.md — it was reported as
grouped, rounded summaries without raw logs, and that cannot be reconstructed
now. So: **11.5s cumulative of 20s, about 8.5s remaining**, carried and not
reset, with that caveat named rather than dropped.

### One claim withdrawn

`provider-127073.json` said the reviewer's probe replay showed
`serving-close-after-guard` refusing at the **post-check**. The reviewer is
right that that fixture refuses at the absent-sidecar **preflight**; my reading
of which guard fired was unsupported by it. Their separate-process harness is
what actually reproduces the shutdown sequence.

### What the owner decided

M128251 applies M128249 here: SQLite-managed WAL/SHM creation and maintenance
during `mode=ro` opening is permitted, **including refused opens**. So the
sidecar-presence and identity guards and their refusals come out. Everything
else stands — the public `ContractRefusal` correction for an unreadable store,
coherent snapshots, ownership/schema/history validation, mutation refusal,
database contents and committed evidence, and no initialization, checkpoint,
application cleanup or write-capable fallback.

### Question and budget, declared before any execution

With the sidecar guards removed, does the opener still read only an existing
recognized coordinator, refuse a foreign, empty, wrong-version or unreadable
one untouched, refuse every transition, and initialize nothing?

Budget: the **~8.5s remaining** of this Work's 20s, each run recorded with its
command and wall time and its log retained.

### What changed

`src/baton_v12/integration/store.py` — the sidecar guards are gone:
`_sidecars_present`, `_sidecar_identities`, `_is_write_ahead_log`,
`_require_nothing_was_created`, `_SIDECARS`/`_HEADER_BYTES`/`_HEADER_WAL`, the
write-ahead-log preflight in `_connect_readonly`, and the pre-connect snapshot
and post-read check in `open_readonly`. Each existed only for the prohibition
the amendment supersedes. Everything else is untouched: the [P2]
`ContractRefusal` translation of `sqlite3.Error` at the first schema read, the
single coherent snapshot around identity/objects/`_adopt`, the absent, empty,
foreign, unowned and wrong-version refusals that leave the file as found,
`mode=ro`, mutation refusal, and no initialization, checkpoint, cleanup or
write-capable fallback.

`tests/integration/test_coordinator.py` — the two scheduled cases converted.
`..._is_refused_with_the_sidecar_limit_named` becomes
`test_a_store_nobody_holds_reads_its_committed_evidence`, which is the case
this Work exists for: a status process reading a coordinator after an ordinary
serving shutdown, when there is no serving process left to ask.
`..._is_refused_and_completed_by_nothing` becomes
`..._reads_the_same_committed_evidence` over the same `-wal`-only and
`-shm`-only states. Both still assert the store's own bytes and mode are
unchanged, and the shutdown case measures `before` AFTER the close, because a
clean shutdown checkpoints the write-ahead log into the database — the
writer's act, not the reader's. Added
`test_no_coordinator_is_created_where_none_exists` so the protection the
amendment did NOT touch stays explicit beside the conversions.

The baseline run is the evidence that nothing else conflicted: with the guards
out and no test edited, exactly those two cases failed and the other sixteen
passed.

### The reviewer's residual, answered

Their separate-process harness proved a serving exit between the reader's
preflight and its connection made SQLite recreate both sidecars before the
opener refused. Replayed unchanged against this candidate it reports
`opened: true` — the sequence they proved was a refusal now reads. That is what
the amendment intends; nothing in this code decides whether SQLite may make
those files, and nothing removes them.

### Runs

18 tests / 3 failures (0.197s) → 19 / OK (0.204s) → 214 coordinator OK (1.540s)
→ 109 driver OK (2.173s) → probe replay (0.164s) → shutdown replay (0.328s).
**4.606s this pass, 16.106s cumulative of 20s, ~3.9s left.** Commands, raw logs
and hashes are in `evidence/provider-128308.json`.

Passing back to `baton.bug` unaccepted, mirroring the Authority half at
seq128301. Both halves carry the same owner amendment and should be judged
against it together.
