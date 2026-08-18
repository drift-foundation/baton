# Plan

1. [done] Inventory the phase/handler/readiness transition matrix and every
   consumer of research/review/route-derived destination phases.
2. [done] Enforce the closed scheduler-state invariant in the authority and
   migration-free fresh schema; remove role-to-phase mapping.
3. [done] Rename claimant-valued `current` to `handler`, then update pass,
   claim, release, waiting/dependency wake, park, close, retry, race, Events,
   filters, and readiness behavior atomically. Route and Next remain endpoint
   values; history remains in Events.
4. [done] Update CLI/JSON, TUI, ACP/Codex readiness consumers, workflow
   stories, and `EFFECTIVE-BATON.md`.
5. [done] Prove all role handoffs, claim exclusivity, gate wakeups, terminal
   null, contradiction refusals, packaged parity, and fresh-authority startup.
6. [done] Run focused tests and `just test-v11`, then return for independent
   review before the next authority cutover.

**Independent review — 2026-08-18:** changes requested. The implementation
does not yet preserve the scheduler invariant when a gate is added to
unclaimed queued Work, when gated parked Work is resumed, or when one of
multiple live wait conditions is satisfied. Readiness-consumer tests and the
operator documentation also disagree with projection 9. See the newest
append-only review for the complete gate.

**Independent review round 2 — 2026-08-18:** the authority and readiness
corrections are accepted and the full gate is green. Changes remain requested
only for direct semantic contradictions in the active operator guide and
executable-spec prose. The pre-existing condition-bound waiting exit rule is
affirmed; it is not changed by W38. See
`review-2026-08-18T06-29-08Z.md`.

**Independent review round 3 — 2026-08-18:** accepted. The final semantic
documentation and executable-spec guards are clean; 53 focused tests pass
independently and K's complete gate reports 1105 parallel + 13 serial + 38
ACP passing. W38 may close satisfying.
