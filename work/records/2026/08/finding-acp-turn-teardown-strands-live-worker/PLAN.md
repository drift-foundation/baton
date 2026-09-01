# Plan

1. [done] Record W51487 episode 55530, the contradictory runtime projection,
   surviving run7 process and missing terminal evidence.
2. [done] The operator stopped the exact run7 container while preserving
   `/tmp/w51487/run7/`, proved it exited, and released only W51487 episode
   55530. The authority queued a fresh assignment episode 55726.
3. [done] Trace the ACP bridge delivery-completion and process-domain teardown
   paths against the prior W4303 managed-turn settlement contract. The
   reviewer findings record the missing read, reusable durable-store boundary,
   ordering, restart/race requirements, and external-runtime limit.
4. [done, with one flagged refinement] Add a participant-scoped durable ACP settlement owner.
   Restore it before wait/idle, reconcile every ended ACP turn through a
   canonical `wait timeout=0`, publish `idle` only after a released answer,
   and otherwise publish `failed` and file/retry one sticky incident. Apply
   item 8's approved scheduling split rather than blanket readiness retention.
   Preserve the independent W28681 process-domain fence.
5. [done] Require configured
   `runtime.actionOwner` for every managed ACP bridge governed by this
   settlement contract. Refuse startup before runtime-lease publication or
   the first wait when it is absent or unresolved; never infer the owner from
   the runner participant, session, Route, or runtime telemetry.
6. [done] Cover no-claim and exact/secondary/unreadable outcomes,
   successful and failed prompts, marker restart/corruption/recovery,
   publication concurrency and retry, later readiness retention, a newer
   episode, detached runtime survival, composed process-domain failure, and
   absence of automatic runtime kill, credential action, claim release or
   partial-output acceptance. Re-run the full ACP suite and focused sibling
   W4303 settlement suite.
7. [done] Confirm no automatic acceptance, runtime kill or claim release was
   introduced without an explicit policy.

## 2026-09-01 implementer round

8. [done; the ruling is pinned in FINDING.md and the ledger obligation for
   M58475 was resolved by response M58545] Preserve
   W11910's
   redelivery of an exact claimed-Work recovery prompt that failed before
   returning. A prompt that returned is presented and is not replayed solely
   because its exact claim survives. Both paths withhold `idle`, publish
   `failed`, and owe the incident. Secondary, held, unreadable, and
   authority-drifted states remain stranded and retain readiness.
9. [resolved 2026-09-01] Item 6's regression matrix is written: 30 focused
   W55705 cases, and the suite moved from 89 to 119.

## 2026-09-01 second implementer round (response to review 2026-09-01T03-41-20Z)

10. [done] A stranded settlement now BREAKS the action loop on both the
    returned and the failed path, so a fence taken mid-envelope retains every
    remaining action instead of letting the next one start a turn.
11. [done] Fence IDENTITY is preserved through the read. The recoverable retry
    no longer clears the fence before comparing authority; an opaque answer
    keeps the existing fence rather than minting a second one for the same
    stranded claim; a genuine successor mints its own unfiled incident; and a
    late acknowledgement is applied only to the fence that asked for it.
    Incident publication is serialized.
12. [done] A restored marker is fenced until one canonical read compares its
    recorded authority, whatever its correlation. Drift, a missing authority
    and an unreadable answer all keep it fenced and adopt nothing.
13. [done] Marker persistence is load-bearing: an uncommitted marker or
    acknowledgement strands the lane instead of looking durable, and a delete
    nobody could confirm keeps the fence on both the settle and the reconcile
    path.
14. [done] A defect the matrix found on its own: `reconcile` classified the
    canonical read against the fence's OCCUPANT, so a `secondary` fence read
    its own occupant back as `claimed` and re-admitted delivery into a slot
    that never freed. The fence now records the delivered OFFER separately and
    asks about that.
15. [done] 119 ACP tests (from 89) and the sibling gates: 430 in
    `tools/codex-event-bridge/`, including its 54-case W4303 settlement suite.
    Fifteen mutations of the corrected guards, all caught; three started as
    misses and the TESTS were corrected.
16. [changes requested in review-2026-09-01T04-30-00Z.md] Refuse a configured
    action owner equal to the runner participant, and reconcile an existing
    recoverable fence's authority before any later prompt is delivered.
