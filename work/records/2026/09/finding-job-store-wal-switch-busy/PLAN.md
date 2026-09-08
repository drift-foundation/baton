# Plan

1. [research complete 2026-09-06] Drive the unconditional JobStore WAL request
   through public `JobStore.open` under deterministic post-commit contention.
   Confirm the schema and Authority binding commit precede the SQLITE_BUSY
   result and record the separation from W101621.
2. [implemented 2026-09-06] Apply a bounded post-ownership WAL request for
   both initialization and adoption. Tolerate only structured
   SQLITE_BUSY/SQLITE_LOCKED, preserve raw non-contention storage faults, and
   retry on later opens. Limit production scope to
   `v12/python/src/baton_v12/job_manager/store.py`.
3. [implemented 2026-09-06] Add deterministic cases in
   `v12/python/tests/job_manager/test_store.py` for BUSY success with a real
   competitor, later WAL promotion, the LOCKED classifier edge,
   non-contention propagation plus handle cleanup, and refusal-before-PRAGMA
   across foreign/product/schema/Authority mismatches. The test changes are
   additive and do not weaken existing expectations.
4. [implemented 2026-09-06] Create the required `PROGRESS.md` at
   implementation start, then implement without changing schema, migrations,
   Authority identity, journal semantics, public return shapes, the Worker
   Manager store or the integration store. Revalidate these boundaries
   against the current tree before editing.
5. [independent review complete 2026-09-06; bounded sign-off with no findings;
   broad concurrent-tree blockers recorded] Run the focused Job store module,
   Job Manager source suite and broad v12 gate. Independently review exact
   production/test paths and every changed existing-test expectation before
   integration. The focused class passes 5/5, the complete Job store module
   passes 47/47, and all Job Manager source tests pass 338/338. The broad
   runner completed its 3,996-test pure phase with seven failures outside this
   Work's paths and therefore did not enter the serial phase; see PROGRESS.md.
   The bounded review is retained in `review-2026-09-06T13-27-45Z.md`; no
   immutable proposal digest was supplied.
