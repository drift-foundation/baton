# Plan

**Status — 2026-08-20:** approved for a narrow no-schema v11 correction. The
earlier same-participant takeover design is superseded and deferred to v12.
W415 no longer blocks this independent team-member recovery rule.

1. [done] Revalidate how managed Codex sessions, foreground sessions,
   participant identities, runtime incarnations, and canonical claims interact.
2. [done] Supersede same-participant takeover machinery for v11. Permit any
   configured owning-team member—but no cross-team participant—to release an
   exact recorded Handler with a durable reason.
3. [pending] Change only the `release` authorization gate; preserve its atomic
   compare-and-swap, derived landing phase, episode minting, event evidence,
   and effectively-once behavior. Add no schema or TUI change.
4. [pending] Cover self-release, owning-team forced recovery, cross-team
   refusal, wrong expected Handler, unclaimed/terminal refusal, and existing
   landing behavior. Document stop/quiesce before forced recovery and run the
   focused gate.
5. [pending] Independently review before deployment.
