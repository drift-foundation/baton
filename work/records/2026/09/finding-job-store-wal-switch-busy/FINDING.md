# JobStore WAL switching can escape raw contention

Work: W101661

Discovery context: W101621

## 2026-09-06 — recursive discovery and confirmation

**Observed.** Review of W101621 found the same unconditional post-commit WAL
statement at `baton_v12/job_manager/store.py:471`. It sits in
`JobStore._initialize` after the complete schema, schema version and immutable
Authority binding have committed.

**Confirmed.** `/tmp/w101621-job-store-probe.py` deterministically pauses the
public `JobStore.open` immediately after that commit, lets a real second SQLite
connection acquire `BEGIN IMMEDIATE`, and releases the opener into
`PRAGMA journal_mode = WAL`. Current source raises
`sqlite3.OperationalError: database is locked` with
`sqlite_errorcode == 5` and `sqlite_errorname == SQLITE_BUSY`. The resulting
database is already a complete, correctly Authority-bound Job store; only the
optional persistent journal-mode request was denied.

**Confirmed cause.** The configured busy timeout does not guarantee waiting
for a journal-mode switch. `JobStore.open` closes its connection on the raw
failure, but its caller receives an implementation exception for transient
contention after the durable initialization succeeded. Existing owned stores
take `_adopt`, which validates/migrates and enables foreign keys but does not
request WAL again, so a tolerated first-open race needs an explicit later-open
retry boundary rather than a permanent downgrade by accident.

**Confirmed contract interaction.** Ownership includes the store kind, schema
version and immutable Authority UUID. No persistent PRAGMA may run before all
three are proved or atomically installed. WAL is a concurrency property, not a
schema or identity member. As in the Worker Manager, only SQLite's structured
BUSY/LOCKED primary result codes identify contention; free-form text must not
select tolerance and non-contention storage failures retain their identity.

## Recommended correction boundary

**Proposed.** Move the WAL request out of the initialization-only tail and run
it after either fresh initialization or `_adopt` has completely established
store and Authority ownership. Tolerate only structured SQLITE_BUSY or
SQLITE_LOCKED and return the usable store in the retained mode. A later open
requests WAL again after ownership, allowing transient contention to heal.

**Proposed path set.** Limit production changes to
`v12/python/src/baton_v12/job_manager/store.py`. Add focused tests only to
`v12/python/tests/job_manager/test_store.py`, plus an additive registry entry
only if current discovery does not already include that module. Do not change
the Worker Manager or integration store under W101661.

## Required regressions

1. Drive public `JobStore.open` deterministically through committed schema and
   Authority binding into a real competing writer at the WAL statement. A
   BUSY answer returns a usable, correctly bound store with no raw exception.
2. Release the competitor and prove a later normal open requests WAL again and
   obtains it.
3. Cover the structured LOCKED edge directly if it cannot be produced portably
   with two SQLite connections.
4. Drive a non-contention `sqlite3.OperationalError` at the optional request
   and prove it remains raw and the connection is closed.
5. Preserve byte-stable refusal for the Worker Manager store, a foreign store,
   the wrong schema version and the wrong Authority UUID. None may receive a
   persistent mode request before refusal.
6. Preserve migrations and their stale-reader/Authority-binding races. The WAL
   change is outside their transactions and must not widen migration authority
   or alter schema bytes.

## Acceptance boundary

The correction is complete when transient BUSY/LOCKED at an owned JobStore's
optional WAL request cannot turn a successful initialization or adoption into
a raw public-open failure, while Authority binding, migration atomicity,
ownership-before-mutation, later WAL retry, connection cleanup and raw
non-contention failures remain independently proved.

This is distinct from W101621 because the stores have separate schema and
identity owners. Their correction may use the same shape, but neither Work
authorizes opportunistic edits to the other.

## Research verification

- `PYTHONPATH=src python3 /tmp/w101621-job-store-probe.py` reproduces
  `sqlite3.OperationalError` with code 5 / SQLITE_BUSY through public
  `JobStore.open`.
- `PYTHONPATH=src python3 -m unittest tests.job_manager.test_store -v` passes
  all 42 existing focused cases, confirming the deterministic probe adds a
  missing contention boundary rather than explaining a standing focused-test
  failure.

## 2026-09-06 — owner decision

**Accepted.** `JobStore.open` owns the WAL policy so callers do not repeat or
remember it. After initialization or adoption has proved the store kind,
schema and immutable Authority binding, every successful open requests WAL.
An already-WAL store makes this effectively a no-op; a structured SQLITE_BUSY
or SQLITE_LOCKED leaves the valid store open in its current journal mode, and
a later open requests WAL again. The open does not synchronously retry an
optional concurrency optimization.

Only structured BUSY/LOCKED primary codes are tolerated. Other SQLite failures
retain their original identity, and foreign, incompatible or differently
bound stores are refused before any persistent journal-mode request. The
production and test scope above is approved unchanged and remains separate
from W101621's ControlStore correction.

## 2026-09-06 — independent implementation review

`review-2026-09-06T13-27-45Z.md` signs off the bounded implementation with no
findings. The WAL request occurs after either complete ownership path,
structured BUSY/LOCKED is tolerated, every other failure preserves identity
and handle cleanup, later opens retry promotion, and unowned, incompatible or
differently Authority-bound stores see no persistent PRAGMA. The five
existing-test additions are within the explicitly accepted scope and weaken no
earlier assertion. Focused class, store-module and Job Manager gates pass 5/5,
47/47 and 338/338; the original deterministic public-open probe now returns a
usable store under contention.

No immutable proposal digest was supplied, so this is a bounded semantic and
working-tree-diff sign-off rather than approval of digest-bound integration
bytes.
