# Plan

1. [done] Identify all callers and the listener-after-start ordering.
2. [done 2026-08-19] Add a deterministic regression where completion precedes the
   waiter's registration.
3. [done 2026-08-19] Implement bounded completion retention in `CodexClient` and cover
   normal, early, unrelated, duplicate, cleanup, and disconnect cases.
4. [done 2026-08-19] Run focused Codex bridge tests and the full v11 gate.
5. [in review 2026-08-19] Obtain independent review.

Implementation follows W424 because both edit the Codex bootstrap/client
surface; the dependency is code-ownership serialization, not product
semantics.

