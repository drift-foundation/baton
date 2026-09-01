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
16. [resolved by items 18-20; re-review found the narrower exact-wake gap in
    item 21] Refuse a configured action owner equal to the runner participant,
    and reconcile an existing recoverable fence's authority before any later
    prompt is delivered.

## 2026-09-01 third implementer round (response to review 2026-09-01T04-30-00Z)

18. [done] Authority identity is a PRE-delivery fence. `AcpSettlement.admits`
    compares the fence's recorded authority with the `authority_uuid` the
    envelope validator already proved, and the loop consults it whenever a
    marker exists — before revalidation and before any prompt. A matching
    exact claim still takes W11910's recoverable redelivery; a changed or
    unnamed authority retains the WHOLE envelope and drops the fence's
    verification without re-minting it.
19. [done] `runtime.actionOwner` equal to the runner participant is refused at
    startup, before role loading, the runtime lease and the first wait. It is
    the same self-addressed deadlock the ruling rules out, reached by spelling
    the runner instead of inferring it.
20. [done] Three new regressions — a single bridge across an A-to-B authority
    change proving only the A prompt is spent, an unnamed authority as drift,
    and a startup-order case for the self-owner. Five mutations of the two new
    guards, all caught. 122 ACP tests (from 119) and 430 in
    `tools/codex-event-bridge/`.

## 2026-09-01 third review

21. [changes requested in review-2026-09-01T05-03-30Z.md] Do not treat a
    matching `authority_uuid` as admission for every action in the envelope.
    While a claim-settlement marker exists, admit only the exact unspent
    recovery wake covered by the approved refinement. Reconcile and retain a
    same-authority successor claim or any neighboring action before a turn is
    spent, and preserve one incident for the original Work/episode fence.
22. [pending] Add the same-authority successor and same-envelope neighboring
    wake regressions, re-run the ACP and sibling settlement gates, and return
    for independent review.

## 2026-09-01 fourth implementer round (response to review 2026-09-01T05-03-30Z)

21. [done] `AcpSettlement.permits(action)` is a PER-ACTION gate beside the
    per-envelope authority one. Only the exact unspent recovery wake — same
    Work, same assignment episode, same action key, compared against the
    fence's recorded OFFER — takes W11910's redelivery path. Anything else
    reconciles the recorded claim first and is retained unless that read
    proves the slot released, so a successor is recorded before a turn is
    spent.
22. [done] Six new regressions, including the review's two probes end to end
    with the one-incident assertion, and a case proving a retained later wake
    is delivered once the exact claim is reconciled.
23. [done; approved in Baton response M59062] The existing
    `non-Work actions beside a deferred Work keep their own delivery rule`
    prompt-count expectation is superseded from two to one after the claimed
    recovery wake strands settlement. The retained poke is delivered after
    canonical claim release.
24. [done] Eight mutations of the new gate, all caught after two tests were
    made load-bearing. 127 ACP tests (from 122) and 430 in
    `tools/codex-event-bridge/`.
25. [done] Record the approval and complete final sign-off. No further code
    change was required after the 2026-09-01T05:17:42Z conditional review.
