# Plan

1. [research complete 2026-09-06] Confirm the broad-sweep failure at the exact
   `ControlStore._initialize` WAL statement and drive it deterministically
   through public `ControlStore.open`. Separate a committed valid schema from
   the optional mode-switch failure and record the SQLite primary result code.
2. [implemented 2026-09-06] Request WAL
   only after fresh initialization or adoption has established ownership;
   tolerate only structured SQLITE_BUSY/SQLITE_LOCKED; preserve raw
   non-contention storage faults; and retry the request on later ordinary
   opens. Limit production scope to
   `v12/python/src/baton_v12/worker_manager/store.py`.
3. [implemented 2026-09-06] Add deterministic cases to
   `v12/python/tests/manager/test_store.py` for BUSY success with a real
   competing writer, later WAL promotion, the LOCKED classifier edge, raw
   non-contention propagation with connection cleanup, and no persistent
   request before foreign/incompatible-store refusal. These are additive
   regressions; do not weaken existing assertions or replace the synchronized
   multi-opener case.
4. [implemented 2026-09-06] Create the required `PROGRESS.md` at
   implementation start, then implement the bounded post-ownership WAL helper
   without changing schema, operation identity, journal semantics, public
   return shapes or other stores. Revalidate against the current tree at
   implementation start.
5. [independent review complete 2026-09-06; bounded sign-off with no findings;
   broader gate has recorded baseline blockers] Run
   the focused manager store tests, the manager source suite and the broad v12
   gate. Independently review the exact production/test diff and all changed
   existing-test expectations before any integration handoff. The new focused
   class passes 5/5 and the complete store module passes 57/57. Manager-wide
   discovery ran 2,433 tests but is red on 17 unavailable-Docker prerequisite
   errors and five boundary-inventory failures outside this Work's paths; see
   PROGRESS.md for the retained result. The bounded review is retained in
   `review-2026-09-06T13-03-25Z.md`; no immutable proposal digest was supplied.

The sibling unconditional WAL switch in
`v12/python/src/baton_v12/job_manager/store.py` is excluded. It receives a
separate tracked disposition rather than broadening W101621.
