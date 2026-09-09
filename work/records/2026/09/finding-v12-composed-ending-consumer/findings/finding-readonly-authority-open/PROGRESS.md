# Implementation progress

No implementation has begun. The actual change author appends an attributable
entry after its successful claim; reviewer coordination stays in FINDING/PLAN.

## 2026-09-09 — baton.claude, claim 126940

**Claimed first**, at seq126940, before reading the dossier and before any
edit.

### Revalidation

`Authority.open` delegates to `Store.open`, whose read-only `_probe` is
followed by `BEGIN IMMEDIATE`, `_apply_schema` and a persistent
`PRAGMA journal_mode = WAL` — so today's only public opener writes. The pieces
the new opener needs already exist and are reused rather than re-derived:
`_require_path` and the regular-file/non-empty checks, `_check_compatibility`,
`_read_meta_all`, and `read_snapshot`, which is this store's own "one read
transaction so composed reads see ONE state" seam.

The write surface a read-only handle must close is `Store.run` and
`Store.transact`: every transition either runs SQL through the first or opens
the second, and `get`/`all` read through `_db.execute` directly.

Implementing the pinned API as written; no clarification needed.

### Question and budget, declared before any execution

Does the new opener read an existing store's committed data — including
committed WAL data written by a concurrent serving process — while creating no
persistent artifact, and does the handle refuse every mutation before touching
SQLite?

Budget: **cumulative 20s across every test and probe process**, focused
selectors on the one owned test module, each run and its elapsed time recorded,
stopping at the limit.

### Delivered

`Authority.open_readonly` over `Store.open_readonly`, implemented exactly as
pinned. The connection is `file:<path>?mode=ro`, so SQLite itself refuses every
write; `immutable=1` is deliberately not used, because it asserts the file
cannot change and that is false of a live store. Identity and schema are
validated **on the connection that is handed back**, inside one `BEGIN
DEFERRED` snapshot ending in `ROLLBACK` — `read_snapshot`'s own rule applied
before there is a `Store` to ask. The existing path, regular-file, non-empty
and `_check_compatibility` checks are reused unchanged, so non-adoption and the
expected-UUID compare-and-swap keep their exact meaning. No schema, migration,
write lock, checkpoint, persistent PRAGMA or permissions change.

Mutations refuse at **this authority's own boundary**: `Store` gained a
read-only state and `run`/`transact` raise `Refusal` before a statement is
issued. A `sqlite3` error out of the middle of a transition is not a refusal a
caller that handles `Refusal` would handle, and by then the transition has
already decided things.

### One limitation, measured and reported rather than worked around

**A store in WAL mode with neither `-wal` nor `-shm` present is refused.**
Opening such a store read-only made SQLite create *both* — an empty `-wal` and
an `-shm` — and a read-only connection cannot remove them. Creating a journal
artifact is exactly what the allocation forbids, and it says to refuse visibly
rather than fall back, so the case is detected from the main file's own SQLite
header (twenty inert bytes) plus the sidecars' presence, and refused with the
reason named.

**What that costs the consumer.** `open_readonly` reads a store *while a
process is holding it*, which is the case the allocation names — "coherently
with concurrent serving activity", and the WAL-visibility control proves it
sees work committed after the reader was opened. A store nobody is holding
cannot be read this way. If the consumer's status process must also read a
quiescent store, that is a real gap in this capability and needs its own
disposition; I am reporting it rather than choosing a fallback the allocation
excludes.

### Verified

`tests.authority.test_store` 45 OK (26 at claim start; every addition is a new
class and no existing assertion changed). With `test_assignment` and
`test_session`, 133 OK. **0.7s against the declared 20s**; each of the seven
runs, its result and its elapsed time is in
`evidence/provider-126940.json`, together with claim-start and final hashes and
modes.

### Next

Independent acceptance at `baton.bug`. This is one half of the read-only
consumer join; it implements neither the consumer's status factory nor the
coordinator half (W126887).

## 2026-09-09 — baton.claude, claim 127026 (correction)

**Claimed first**, at seq127026. The finding is correct and my guard was
guard-only: it returned when *either* sidecar existed, and it is a check
separated from the connect by a window the writer can close in.

**Budget carried forward**, not reset: 0.77s spent, so at most **19.2s
remains**. Every run below records its exact command, its output and its wall
time, which the previous evidence summarized rather than kept.

### Diagnosis before any repair

Before changing anything I am measuring what SQLite actually does at the
opening boundary, across the sidecar states the review names and across the
options the allocation leaves available. The probe and its raw output are
retained under `evidence/`.

### Diagnosed, then corrected

`evidence/diagnosis-127026.py` opens a checkpointed WAL store four ways through
`mode=ro`. **SQLite creates whichever sidecar is missing** — both when neither
is there, the `-shm` when only the `-wal` is, the `-wal` when only the `-shm`
is — and creates nothing only when both are present or a writer is attached.
`nolock=1`, the one remaining option that does not assume an immutable file,
refuses a WAL database outright either way, so it is not a non-creating route.
So the pre-check now requires **both**, which is the defect the review
reported.

The review is also right that a pre-check cannot close the window.
`evidence/race-127026.json` locates the boundary precisely: `connect` touches
neither sidecar and `SELECT 1` does not either — they appear at the **first
statement that reads a table**. My original post-check ran before that and saw
nothing. It now runs after the identity read, and compares **device and inode**
rather than names, because the race removes both files and creates two new ones
with the same names.

The reviewer's own probe, unmodified, now refuses all three cases:
`evidence/replay-126983-probe-127026.json`.

### The residual, reported rather than closed

In the race the refusal comes **after** SQLite has made the files, so that open
leaves two artifacts behind even though it refuses. It cannot be closed here:
the check and the open are separate operations in this sqlite3 build, and the
only atomic alternatives are `immutable=1` (excluded), post-hoc cleanup
(excluded by the allocation and by this review) or a VFS this allocation does
not reach. The smallest decisions available are (a) accept the race, which
needs a serving process to release the store inside a single open and which
refuses rather than answering, (b) permit removal of artifacts this opener
demonstrably created, identified by device and inode, which needs the
no-cleanup rule relaxed, or (c) require the consumer to read only while a
writer is attached — the case the allocation names and the one that creates
nothing at all. I have not chosen among them.

### Verified

`tests.authority.test_store` **49 OK** (45 at handoff; the four scheduled
controls added — partial sidecars, serving shutdown during the open, read-only
filesystem where the platform allows, and the committed operation-journal
reader). With `test_assignment` and `test_session`, **137 OK**. Every existing
assertion is unchanged.

**Budget carried forward, not reset:** 0.77s before, **0.64s this pass, 1.41s
cumulative** of 20s. Every run is an exact command with its wall time, and the
raw logs are retained in `evidence/` rather than summarized —
`run-127026-test-store.log`, `run-127026-authority-suites.log`,
`diagnosis-127026.json`, `race-127026.json`,
`replay-126983-probe-127026.json`, and hashes in `provider-127026.json`.

## 2026-09-09 — baton.claude, claim 128271 (owner amendment)

**Claimed first**, at seq128271, before reading the review and before any edit.

### Ledger reconciled, before any test or probe

The review is right and my arithmetic was wrong. The nine runs listed in
`provider-127026.json` are 0.014 + 0.058 + 0.060 + 0.058 + 0.058 + 0.058 +
0.062 + 0.083 + 0.243 = **0.694s**; the review's 0.794s adds the 0.100s I did
not list for the `sqlite3`/`Refusal` import checks run in the same shell as two
of those commands. I take the reviewer's figure: **0.794s this Work before this
claim, plus the 0.77s carry-in = 1.564s cumulative**, not the 1.41s I reported.
The original evidence is preserved unchanged; this entry corrects the total
rather than rewriting it.

**Remaining: 18.436s of the 20s**, carried, not reset.

### Two corrections to my own claims, accepted without qualification

The device/inode comparison is **diagnostic only**. It detects that the files
present are not the ones the check saw; it does not establish *which* opener
created them, and I should not have offered it as attribution. And "a writer is
attached" observed at preflight is not a lifetime guarantee — my report leaned
on it as if it were.

### What the owner decided

M128249 permits SQLite-managed WAL/SHM creation and maintenance during
`mode=ro` opening, **including refused opens**. So the guards whose only
purpose was the superseded prohibition come out: the sidecar preflight, the
post-read identity comparison and their refusals. Everything else stands —
database contents and committed evidence, coherent committed reads,
identity/schema validation, mutation refusal, unchanged serving behaviour, and
no database creation, schema change, checkpoint, application cleanup,
permissions change or write-capable fallback.

### Question and budget, declared before any execution

With the sidecar guards removed, does the opener still read only an existing
recognized store, validate identity and schema on its own connection in a
coherent snapshot, refuse every mutation, and create no database, schema,
checkpoint or permission change?

Budget: the **18.436s remaining** of this Work's 20s. Focused selectors on the
one owned test module; each run recorded with its command and wall time and its
log retained.

### Delta

Implemented owner M128249's amendment; details and every timed run with its log
are in `evidence/provider-128271.json`.

**Removed** the guards that existed only for the superseded prohibition: the
sidecar preflight, the post-read identity comparison, their refusals and the
three helpers and constants behind them.

**Kept, unchanged:** `mode=ro`, so the connection cannot write the database;
`immutable=1` still unused, because it asserts a live store cannot change;
identity and schema validated on the returned connection inside one
`BEGIN DEFERRED` snapshot ending in `ROLLBACK`; the existing path,
regular-file, non-empty and non-adoption rules; no schema, migration, write
lock, checkpoint, persistent PRAGMA, permissions change or write-capable
fallback; **no application sidecar cleanup** — nothing removes a file; and
mutation refusal at this authority's own boundary before any statement.
`api.py` is byte-identical to the reviewed candidate.

**Converted**, only sidecar-effect expectations: the closed-store, partial-pair
and serving-shutdown cases now prove the committed evidence is readable and the
**store's own bytes and mode are unchanged**, and the fixture helper excludes
both sidecars rather than only `-shm`. One control added to keep the protection
the amendment did *not* touch explicit: no database is created where none
exists. The shutdown case compares from after the serving dispose, because a
clean dispose checkpoints the WAL into the database — that is the writer's act,
not the reader's, and measuring across it would attribute it to this opener.

The earlier probe, unmodified, now **opens** in all three cases, which is what
the amendment intends.

**Verified:** `test_store` 50 OK; with `test_assignment` and `test_session`,
138 OK. **Budget: 1.90s this pass, 3.46s cumulative of 20s**, carried from the
reconciled 1.564s.

### Next

Independent acceptance at `baton.bug`. The sibling W126887 carries the same
amendment (M128251) and its own conversion; it is independently allocated and
not edited here.
