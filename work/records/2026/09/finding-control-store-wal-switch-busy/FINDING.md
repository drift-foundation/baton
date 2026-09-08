# ControlStore WAL switching can escape raw contention

Work: W101621

## 2026-09-06 — discovery and independent confirmation

**Observed.** The 562-shard v12 source sweep retained at
`/tmp/w101490-sweep.txt` failed
`OwnershipBeforeAdoption.test_concurrent_first_openers_adopt_one_initialized_store`.
One synchronized first opener escaped
`sqlite3.OperationalError: database is locked` from
`baton_v12/worker_manager/store.py:419`, the post-commit
`PRAGMA journal_mode = WAL`. The same focused test ordinarily passes, so its
four-way barrier exposes the race without deterministically choosing which
opener holds the file when the WAL request runs.

**Confirmed.** `/tmp/w101621-repro.py` deterministically pauses the public
`ControlStore.open` immediately after its schema transaction commits, lets a
second SQLite connection take `BEGIN IMMEDIATE`, and then releases the opener
into the WAL request. Current source raises the same raw exception with
`sqlite_errorcode == 5` and `sqlite_errorname == SQLITE_BUSY`. The schema is
already fully committed and owned at this point; only the optional persistent
journal-mode request failed.

**Confirmed cause.** `ControlStore._initialize` correctly decides an empty
database under `BEGIN IMMEDIATE`, creates the complete schema atomically and
commits it. It then executes `PRAGMA journal_mode = WAL` outside the
transaction. Changing journal mode needs stronger file access than an ordinary
write transaction, and this PRAGMA can return BUSY without waiting through the
configured busy handler. `ControlStore.open` correctly closes the connection
on every exception, but re-raises this storage exception unchanged. The caller
therefore receives a raw implementation exception even though initialization
succeeded and the resulting control store is valid in its existing journal
mode.

**Confirmed contract interaction.** WAL is a concurrency property, not a
schema or identity requirement. The control store's ownership rule remains
empty-or-ours; a foreign or incompatible non-empty database must still be
refused before any persistent PRAGMA changes it. Manager contention policy is
also already explicit: identify only SQLite BUSY/LOCKED from the structured
primary result code and preserve raw non-contention storage failures. Free-form
exception text must not choose the retry/tolerance policy.

**Confirmed adjacent defect, outside W101621.**
`baton_v12/job_manager/store.py:471` has the same post-commit unconditional WAL
statement in `JobStore._initialize`. `/tmp/w101621-job-store-probe.py` drives
the same public-open interleaving and receives SQLITE_BUSY after the schema and
Authority binding commit. It is tracked separately as W101661. This record does
not authorize changing that separately owned store.

## Recommended correction boundary

**Proposed.** Make the WAL switch a post-ownership request shared by both the
fresh-initialize and existing-store adoption paths. A transient BUSY or LOCKED
answer should leave the open successful in the mode SQLite actually retained.
Later opens of the now-owned store should request WAL again, so one transient
race does not make rollback-journal mode permanent. Do not issue the request
before `_adopt` has proved store kind and schema version.

**Proposed.** Classify tolerance by `sqlite_errorcode & 0xff` and accept only
`SQLITE_BUSY` or `SQLITE_LOCKED`, matching the manager's settled contention
boundary. Preserve raw constraint, schema, disk and other non-contention
storage faults. Reading back `PRAGMA journal_mode` after a tolerated answer may
be an internal verification aid, but no new public return value or schema field
is required for this correction.

**Proposed path set.** Limit production changes to
`v12/python/src/baton_v12/worker_manager/store.py`. Add focused cases only in
`v12/python/tests/manager/test_store.py`, plus the additive manager registry
entry only if the chosen test class is not already discovered by the current
registry. Do not change the integration or Job store in this Work.

## Required regressions

1. Deterministically drive `ControlStore.open` through a committed fresh schema
   and a structured SQLITE_BUSY at its WAL request. It returns a usable store,
   the competing writer remains real, and no raw exception escapes.
2. After the competing writer releases, a later ordinary open retries the WAL
   request and obtains WAL. This proves the optional failure did not become a
   permanent silent downgrade.
3. Drive SQLITE_LOCKED or an equivalent structured-code fixture through the
   same local classifier if the actual connection arrangement cannot produce
   it portably.
4. Drive a non-contention `sqlite3.OperationalError` at the same statement and
   prove it still escapes unchanged and the handle is closed.
5. Preserve the foreign/incompatible-store byte-stability cases: no WAL request
   occurs before ownership is established.
6. Keep the existing concurrent-first-openers case and focused manager store
   suite green; the deterministic regression complements rather than replaces
   that scheduler-sensitive coverage.

## Acceptance boundary

The correction is complete when an owned, valid ControlStore can survive
BUSY/LOCKED on its optional WAL request without exposing a raw constructor
failure, while non-contention failures, ownership-before-mutation, atomic schema
creation, connection cleanup and later WAL retry remain independently proved.

No workaround is recommended. Retrying `ControlStore.open` in a caller after a
raw exception would hide a defect in the public storage boundary and would not
make the failure taxonomy portable.

## 2026-09-06 — owner decision

**Accepted.** `ControlStore.open` owns the WAL policy so no caller has to
remember it. After either initialization or adoption proves ownership, every
successful open requests WAL. An already-WAL store makes this effectively a
no-op; a structured SQLITE_BUSY or SQLITE_LOCKED leaves the valid store open
in its current journal mode, and a later open requests WAL again. The open
does not synchronously retry an optional concurrency optimization.

Only the structured BUSY/LOCKED primary codes are tolerated. Other SQLite
failures retain their original identity, and a foreign or incompatible store
is refused before any persistent journal-mode request. The production and test
scope above is approved unchanged; the sibling JobStore defect remains
separate.

## 2026-09-06 — independent implementation review

`review-2026-09-06T13-03-25Z.md` signs off the bounded implementation with no
findings. The WAL request occurs after either ownership path, structured
BUSY/LOCKED is tolerated, every other failure preserves identity and handle
cleanup, later opens retry promotion, and foreign/incompatible stores see no
persistent PRAGMA. The five existing-test additions are within the explicitly
accepted scope and weaken no earlier assertion. Focused class and store-module
gates pass 5/5 and 57/57; the original deterministic public-open probe now
returns a usable store in `delete` mode under contention.

No immutable proposal digest was supplied, so this is a bounded semantic and
working-tree-diff sign-off rather than approval of digest-bound integration
bytes. W101661 remains the separate JobStore correction.
