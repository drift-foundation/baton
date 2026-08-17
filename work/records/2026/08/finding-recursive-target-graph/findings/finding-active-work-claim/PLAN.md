# Plan

**Status — 2026-08-16:** confirmed fresh-schema release requirement discovered
during W92. It must gate the fresh v11 authority/release candidate.

1. Define the active-claim state and claimant identity in the authority, plus
   the exact queued/active/waiting/parked/pass/close/recovery transition
   matrix.
2. Require one concrete classification at Work creation; omission and
   `unknown` refuse in the fresh schema, while the current handler may
   reclassify later.
3. Add one atomic eligible-handler claim operation with effectively-once retry
   and a deterministic competing-handler refusal.
4. Project the active participant through canonical JSON and the TUI.
5. Update agent workflow policy: no execution begins until the active claim
   succeeds.
6. Cover missing/unknown submission classification, later reclassification,
   two-handler races, retries, pass-and-reclaim, waiting/parking, recovery,
   terminal release, stale clients, and JSON/TUI parity.
7. Make active acquisition atomically require `ready=true`; cover an existing
   blocker, an unresolved child, and a dependency/claim race. Passing releases
   the claimant and projects `queued` when ready or `waiting` when blocked;
   the recipient remains unclaimed until an explicit successful acquisition.
8. Keep claimant identity orthogonal to phase. Cover a claimed review-phase
   Work alongside an independently claimed implementation Work, prove one
   claimant per Work under races, and prove claiming does not rewrite phase.
   Remove or supersede any queued-to-active implementation assumption.
9. Make pass change Current and destination phase atomically. Cover
   implementer-to-reviewer (`phase=review`), reviewer-to-implementer, blocked
   review Work retaining `review` while refusing claim, sender-claim release,
   recipient non-claim, retry, and concurrent phase/pass attempts. Do not
   derive waiting from dependency readiness or carry the sender's old phase.

**Review status — 2026-08-16 10:08Z:** changes requested in
`review-2026-08-16T10-08-11Z.md`. Before sign-off, include the explicit
destination phase in protected pass retry identity and expose `claim` through
canonical `available_transitions` with positive/negative CLI and projection
coverage.

**Review status — 2026-08-16 10:13Z:** round 4 cleared the 10:08 requests.
Final acceptance remains blocked by the pinned but unimplemented explicit
claim recovery/release transition and by missing waiting-release coverage;
see `review-2026-08-16T10-13-10Z.md`. Recovery authority requires Slawomir's
ruling before implementation.

10. Implement the confirmed `release WORK --expect team.member --reason TEXT`
    transition: live Current-handler authority, exact-claimant compare-and-swap,
    mandatory durable rationale, claimant-only mutation, effectively-once retry,
    canonical discovery, CLI/JSON proof, and positive/negative/race coverage.
    Add the missing direct waiting-entry release and audit-payload test.

**Decision status — 2026-08-16 10:15Z:** recovery authority and syntax are
approved and pinned in `FINDING.md`; item 10 is cleared for implementation.

**Signed off — 2026-08-16 10:19Z:** all ten items are implemented and reviewed
clean; see `review-2026-08-16T10-19-38Z.md`. Reviewer verification is 28
focused tests green with a clean diff check; K reports the full v11 gate at
632 parallel plus 3 serial tests green.

## Follow-up — route-derived handoff phase

1. Remove `phase=` from the public `pass` grammar, transition API, protected
   operation identity, help, examples, parity surface, and packaged client.
2. Derive the destination phase only from the destination route's live stage
   role under the write lock. Add approver-to-review mapping and refuse any
   destination role without a canonical stage.
3. Prove implementation, research, reviewer, and approver route handoffs;
   reject explicit `phase=`, unmapped roles, stale config, retries, and route
   races without mutation.
4. Update workflows so a handoff names only `to=`, while same-route stage
   changes continue through the separate authorized phase transition.
5. Re-run the full v11 gate and independently review before the messaging
   cutover closes.
