# Plan

1. Protocol 10: document and retain deterministic `(created_ts, id)` ordering;
   no schema change for 1.2.0.
2. Protocol 11: design the shared publication sequence and its message/notice/
   multi-recipient semantics.
3. Implement the schema and query changes with migration/fresh-authority tests.
4. Add concurrency, rollback, restart, GC and ordering regressions.

