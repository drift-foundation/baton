# Plan

1. [done] Capture the exact W2907 claim/turn-failure/runtime contradiction and
   its effect on W2928/W2929.
2. [done] Trace the failure boundary, restart ordering, incident reuse, and
   release authorization/fencing gaps to exact symbols and regression suites.
3. [done 2026-08-22; obligation 4379] Add the narrow accepted-config `recover`
   capability for non-handler recovery and require `episode=` on every release,
   including self-release, with exact `(work, episode, claimant)` CAS and
   authorization-branch journaling.
3a. [done reviewer verification 2026-08-22] The managed full bridge gate ran
    cleanly, including the socket-bearing `runtime_publisher.test.mjs` cases:
    290 passed. Broad direct `node` execution was not authorized. Dismissing
    I5 remains the configured action owner's separate incident act.
3b. [done 2026-08-22; operational stopgap] Forbid readiness-launched Codex
    contexts from requesting escalation or destructively cleaning optional
    temporary evidence. Preserve and report the path instead. Recorded after
    W2907 repeated the same approval quarantine immediately after restart.
4. [done 2026-08-22] Implement shared failed-turn settlement in both completion
    orderings, durable incident/fence recovery, claimed-first managed delivery,
    and exact `(work, episode, claimant)` release compare-and-swap under the
    ruled authority.
5. [done 2026-08-22] Verify failure-before-claim, failure-after-claim, canonical-read
   failure, restart/crash windows, claimed-before-unclaimed ordering, duplicate
   completion/recovery, same-participant newer-claim fencing, authorization
   negatives, and queued-wake redelivery.
6. [changes requested 2026-08-22] Independent review found that a failed turn
   first observed in the reconnect resume snapshot bypasses `#settleTurn`:
   `#reconcileTarget` clears `activeTurn` and drains while the canonical claim
   survives. Route the resume-discovered terminal path through settlement and
   keep a late duplicate completion idempotent. Reviewer regression and exact
   result: `evidence/review-reconnect-terminal-gap-2026-08-22.txt`.
6b. [done 2026-08-22] Corrected: `#settleTurn` now runs at every point this
    dispatcher first observes a delivered turn has ended, not only where a
    completion NOTIFICATION arrives. Besides the reported resume path, three
    more sites were found and corrected — an ambiguous `turn/start` resolved
    on resume as already ended, the same resolved by `#drain` through
    `#reconcileAmbiguous`, and an accepted turn ABSENT from an idle thread.
    The absent-turn boundary is preserved: the turn is not replayed. Seven new
    regressions, each call site independently mutation-checked. 279 Node,
    2850 + 52 pytest, 55 ACP, 161 v12.
    Evidence: `evidence/correction-reconnect-2026-08-22.txt`.
6a. [changes requested 2026-08-22] Independent re-review found a concurrent
    idempotence gap: reconnect settlement and a late `turn/completed` can both
    pass the `incidentFiled` check before either publication returns, filing
    two occurrences for one failed turn. Serialize/share publication per
    orphan fence while preserving retry after a false/failed publication.
    Reviewer regression and exact result:
    `evidence/review-concurrent-settlement-2026-08-22.txt`.
6c. [done 2026-08-22] Corrected the concurrent incident-publication race.
    Two halves, each independently mutation-checked: a second observer JOINS
    the in-flight publication rather than starting a second one, and the
    in-flight handle is dropped unless the acknowledgement made it durable so
    a refused or failed publication stays retryable. Found while correcting
    and also fixed: a rejecting runner took the whole settlement path down
    with it, so the incident was neither filed nor retried — a throw is now a
    failed publication rather than a failed settlement. Both the sequential
    and concurrent regressions are retained, plus two new retryability cases.
    288 Node (the suite is fully green for the first time since this Work
    opened), 2883 + 52 pytest, 55 ACP, 186 v12.
    Evidence: `evidence/correction-concurrent-2026-08-22.txt`.
6d. [changes requested 2026-08-22] Independent re-review found that a late
    successful publication for cleared orphan A calls acknowledgement through
    mutable `state.orphan`, so it can mark successor orphan B filed even when
    B's own publication returns false. Bind acknowledgement to the exact
    published orphan and update the live marker only if it is still current.
    Reviewer regression and exact result:
    `evidence/review-successor-ack-race-2026-08-22.txt`.
6e. [done 2026-08-22] Corrected: `#acknowledgeOrphanIncident` takes the EXACT
    orphan whose publication returned; the in-memory flag is set on that
    captured object and the DURABLE marker is written only while
    `state.orphan` is still that object. Each half independently
    mutation-checked, and the durable half needed a regression of its own —
    the reviewer's case witnesses only the in-memory flag, so removing the
    guard left the suite green. 290 Node, 52 serial pytest; the two
    non-serial pytest failures are W4996's reviewer-added cases against a
    different module and were deliberately not touched from here.
    Evidence: `evidence/correction-successor-ack-2026-08-22.txt`.
6f. [signed off 2026-08-22] Independent re-review confirmed the exact-object
    acknowledgement and durable identity guard. The two successor regressions,
    every earlier settlement/concurrency/retry regression, and the focused
    release-recovery suite pass. Review:
    `review-2026-08-22T17-16-24Z.md`.
6g. [revalidated 2026-08-22] The signed-off state re-measured against a tree
    that had moved: bridge 297/297 (290 at sign-off; the seven extra are
    W2845's), focused release recovery 20/20. W4615's drain and this Work's
    `release_claim` were read together and compose correctly — drain refuses
    claim ADMISSION only, while a drain's blockers are derived from live
    assignments, so an orphaned claim blocks a drain forever and this Work's
    `recover` release is what clears it. That is a new argument for item 8.
7. [decided 2026-08-22] Do not add automatic release/retry. The shipped
   default is fence + durable incident + explicit operator recovery. Any
   automatic policy is separately ruled future Work, not an unfinished part
   of W4303.
8. [approved; next-deployment action] Grant `recover` to `baton.slaw` in the
   next deployment's `baton.json` and accept the generation. Do not attempt
   the grant through deployed `c529b28`, which predates this implementation.
   Verify the accepted authority exposes the recovery-capable operator before
   closing W4303 satisfying.
9. [approved operator action] Dismiss historical incident I5. Its quarantined
   context has been replaced; dismissal acknowledges the incident and does
   not mutate Work or replace plan item 8.
