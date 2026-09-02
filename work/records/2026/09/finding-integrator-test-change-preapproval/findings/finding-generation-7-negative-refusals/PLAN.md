# Plan

1. [blocked on W72003] Wait for accepted generation 7 and a fresh healthy
   `baton.merge` runtime.
2. [pending operator preparation] Revalidate both exact targets and prepare two
   separate immutable candidates against the recorded base: Case A only the
   scheduled read-only path; Case B only the explicitly unauthorized writable
   path.
3. [pending independent review] Bind and enumerate each candidate separately,
   confirming Case A is otherwise admissible and Case B is intentionally
   outside scope.
4. [pending Case A] Require owner-write refusal before mutation, with unchanged
   target/all-path hashes and modes and no prompt or repair attempt.
5. [pending Case B] Require scheduled-scope refusal before mutation while
   type/base/owner-write facts pass, again with unchanged hashes and modes.
6. [pending assessment] Retain both runtime/refusal records and close satisfying
   only if the two fail-closed causes are independently demonstrated.
