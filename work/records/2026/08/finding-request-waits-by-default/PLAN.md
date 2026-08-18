# Plan

**Status — 2026-08-17:** implemented and returned for re-review after the
round-one corrections.

1. [done] Revalidate the confirmed contract against the current `say`,
   obligation, exact-wait wake, claim-release, operation-replay,
   projection, command-assist, and TUI paths.
2. [done] Add `wait=` to the strict `say` grammar, default it effectively
   to true only for `request=`, and refuse it without a request —
   validated BEFORE the replay lookup (R1).
3. [done] Implement the default blocking request as one authority
   transaction covering Message, obligation, exact wait, and claim
   release; retain the non-blocking `wait=false` form.
4. [done] Project the effective Boolean and resulting workflow state in
   canonical JSON, Events, CLI help, command assistance, and the TUI —
   including the IMMEDIATE `say` result, so the committed form is
   readable without a second Events read (R5).
5. [done] Focused positive, negative, retry, concurrency,
   failure-injection, wake, JSON/TUI parity, and packaged workflow
   tests.
6. [done] Focused gate and `just test-v11` on all available cores.
