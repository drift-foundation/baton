# Plan

1. [done] Wait for accepted generation 7 and a fresh healthy
   `baton.merge` runtime.
2. [done] Revalidate both exact targets and prepare two
   separate immutable candidates against the recorded base: Case A only the
   scheduled read-only path; Case B only the explicitly unauthorized writable
   path.
3. [done 2026-09-03] Bound and enumerated each candidate in separate append-only
   reviews. Case A is otherwise admissible under its exact scheduled authority;
   Case B is byte-reviewed but remains intentionally outside scope. See
   `review-2026-09-03T00-25-32Z.md` and
   `review-2026-09-03T00-25-35Z.md`.
4. [done] Require owner-write refusal before mutation, with unchanged
   target/all-path hashes and modes and no prompt or repair attempt.
5. [done] Require scheduled-scope refusal before mutation while
   type/base/owner-write facts pass, again with unchanged hashes and modes.
6. [done] Retain both runtime/refusal records and close satisfying
   only if the two fail-closed causes are independently demonstrated.
