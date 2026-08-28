# Plan — keep readiness armed until claim

1. [done] Capture the live W6630/W6632/W6633/W10265 stall and identify the
   prompt/event-delivery acknowledgement that suppresses unchanged actionable
   keys.
2. [done] Pin the confirmed v11 level-triggered invariant and the bounded ACP
   plus Codex correction surface.
3. [done] Revalidate current `wait` projection ordering, claimed-action
   shape, ACP delivery memory, Codex producer memory, dispatcher retention,
   and cross-Work fencing before implementation.
4. [done] Add failing focused regressions for one-at-a-time unclaimed Work
   admission, a busy participant, a successful no-claim turn, bounded retry,
   claim acknowledgement, claimed-Work restart recovery, stale withdrawal,
   and restart-independent redelivery in both adapter families. Replace the
   current ACP three-unclaimed-turn assertion and split the Codex persistent-
   key assertion into unclaimed-offer and claimed-acknowledgement cases.
5. [done] Replace delivery-as-acknowledgement with retained per-Work offer
   state: defer all unclaimed Work while another claim is live, admit only the
   canonical unclaimed head while the slot is free, acknowledge only from
   canonical `claimed:true`, and retry an unchanged no-claim offer through a
   bounded policy.
6. [done] Extend the Codex dispatcher boundary so an exact v11 event id is
   retained for its complete queued/starting/ambiguous/active lifetime and a
   producer retry cannot queue the same offer behind itself. Release the local
   identity after withdrawal or terminal no-claim settlement without changing
   canonical Work.
7. [done] Preserve existing non-Work delivery semantics and verify runtime
   state remains honest while an offer is retained rather than executing.
8. [done] Update ACP and Codex bridge documentation and remove or supersede
   tests/comments that call indefinite delivered-key suppression
   level-triggered. Clarify that `--once` proves transport delivery, not claim
   acknowledgement.
9. [done except the live smoke] Run focused ACP/Codex bridge suites, the v11
   test gates, policy checks, and a live smoke where one participant finishes
   Work A and receives already-pending Work B without a restart. Include a
   corrected-runner smoke where one unchanged no-claim action is retried after
   environment repair.
10. [pending] Obtain independent review, deploy the v11 correction, and verify
   the live overdue implementation queue advances without a recovery restart.

**Status 2026-08-25 (implementer).** Items 1-8 are complete and item 9 is
complete except its live smoke, which needs the item-10 deploy and is therefore
not this role's to run. See `PROGRESS.md` for what shipped, the four
clarifications recorded in `FINDING.md`, the two replaced assertions, and the
gate results. Item 10 is the reviewer's and the operator's; the Work is passed
back for independent review rather than closed.


## Review correction — 2026-08-25

`review-2026-08-25T22-04-16Z.md` requested changes on two [P1] gaps. Both are
corrected; PLAN items 5, 6 and 8 are amended by this section rather than
restated.

11. [done 2026-08-25] **A first-seen-CLAIMED Work carries its own status.**
    `recovering` is cleared only by its own successful delivery, so a claim can
    no longer acknowledge a recovery wake that never reached the runner.
    `claimed:true` still acknowledges `pending` and `presented`.
12. [done 2026-08-25] **The claim-slot gate is at the drain, not at
    `enqueue`.** Refusing a second unclaimed Work at the socket broke three
    W99 retention cases, which the same review protects; the pre-turn
    revalidation now answers `over` / `deferred` / `live` from one canonical
    read, and a deferred delivery is HELD at the queue head and re-asked every
    `claimSlotRetryMs` (new config key, default 15s). A claimed Work's own
    recovery delivery is never deferred.
13. [done 2026-08-25] **The cross producer/dispatcher regression exists.**
    `tools/codex-event-bridge/test/claim_slot.test.mjs`, plus the
    failed-then-repaired claimed-recovery pair in the ACP suite. Both were
    measured to fail without the correction.
14. [done 2026-08-25] Documentation corrected: one unclaimed Work per POLL is
    the producer's rule, the claim slot is the dispatcher's, and a failed
    recovery wake stays eligible. ACP 64/64, Codex 382/382.
15. [next] Independent re-review, then the item-10 deploy and the live smoke,
    which remain the reviewer's and the operator's.

## Independent re-review correction — 2026-08-26

16. [pending] Derive the Codex dispatch verdict from the exact matching action
    in the current canonical projection, not the queued event's stale
    `claimed` bit: current claimed Work is its own live recovery, current
    unclaimed Work may be deferred by the occupied claim slot, and non-Work
    actions keep their existing delivery semantics.
17. [pending] Give ACP's immediate pre-turn authority read distinct `over`,
    `deferred`, and `live` outcomes. Retain an exact live Work offer on
    `deferred`; do not prompt it and do not mark it withdrawn or presented.
18. [pending] Make the three additive regressions pass, rerun both bridge
    suites and policy gates, then return for independent review. Deploy and
    live smoke remain blocked on that sign-off.


## Second review correction — 2026-08-26

`review-2026-08-26T01-28-35Z.md` requested changes on two [P1] gaps in the
claim-slot gate the previous correction added. Both are corrected.

16. [done 2026-08-26] **The current matching entry decides, not the event.**
    The Codex gate read `claimed` off the queued event and had no kind test,
    so a Work claimed while it waited was deferred behind its own claim and a
    non-Work obligation was swallowed. The canonical read already returns the
    exact matching action with its kind and current claimed state; that is
    what the verdict is derived from now.
17. [done 2026-08-26] **ACP derives the same three-way verdict.** Exact-key
    membership could not say "still good, waiting on another claim", so a
    claim acquired between the outer poll and the pre-turn read still spent a
    turn. `episodeVerdict` answers `over`/`deferred`/`live` from one envelope,
    and a deferred offer is retained with no prompt, no withdrawal and no
    presentation.
18. [done 2026-08-26] Three existing boolean injections moved to the verdict
    vocabulary, so the seam has one vocabulary rather than two. No assertion
    changed.
19. [done 2026-08-26] ACP 66/66, Codex 396 with one failure that belongs to
    W12229 and was measured to reproduce with this Work's change reverted to
    HEAD. Both corrections measured to fail without them.
20. [next] Independent re-review, then the item-10 deploy and the live smoke,
    which remain the reviewer's and the operator's.

## Third review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T02-42-43Z.md`.

21. [next P1] Give Codex pre-turn revalidation a distinct retain/retry outcome
    for an execution failure, invalid JSON, or a malformed canonical envelope.
    Keep the exact queued event and in-flight identity, spend no model turn,
    and retry the canonical read with bounded delay.
22. [next] Revise the W1224 assertions that describe starting a turn after a
    failed/malformed read as “retaining” the event. This is explicit,
    case-specific confirmation: those expectations predate and conflict with
    the confirmed claim-slot rule. Preserve ordinary non-Baton event behavior.
23. [next] Keep the additive cross-boundary regression, add malformed-envelope
    coverage at the same boundary, rerun both bridge suites and policy gates,
    and return for independent review. Deploy and live smoke remain blocked on
    sign-off.


## Third review correction — 2026-08-26

`review-2026-08-26T02-42-43Z.md`'s one [P1] is corrected.

21. [done 2026-08-26] **A fourth verdict, `uncertain`.** A failed Baton
    invocation, unreadable JSON, or an envelope with no actionable set all
    answer it rather than being mapped onto `live`. The read has two jobs
    since the claim-slot correction and a read that failed does neither.
22. [done 2026-08-26] **The drain holds an uncertain event exactly as it holds
    a deferred one**: at the queue head, with its v11 in-flight identity not
    released, no turn spent, and a bounded re-read on the same cadence.
    `actionDeferred` carries `reason: "unreadable"` so an operator can tell an
    occupied slot from an unreachable authority.
23. [done 2026-08-26] **Two existing assertions revised under the review's
    explicit confirmation.** Both established retention by requiring a turn to
    start; retention is asserted where it lives now — the event is still
    queued — and no turn is spent. Neither was weakened.
24. [done 2026-08-26] One added case: an unreadable authority is re-asked and
    delivers once it answers, because retention that never retries is a queue
    nobody drains. All four measured to fail without the correction.
25. [done 2026-08-26] Codex **403/403**, ACP **67/67** — both Node suites
    fully green.
26. [next] Independent re-review, then the item-10 deploy and the live smoke,
    which remain the reviewer's and the operator's.

## Fourth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T03-43-47Z.md`.

27. [next P1] Validate the canonical revalidation envelope and the actionable
    entry fields used to derive `over` / `deferred` / `uncertain` / `live`.
    Any contradictory or unreadable structure is `uncertain`, not non-Work
    `live`; retain the exact event and spend no turn.
28. [next] Make the additive malformed-matching-action regression pass,
    preserve the 31 other focused cases, rerun both bridge suites and policy
    gates, and return for independent review. Deploy and live smoke remain
    blocked on sign-off.


27. [done 2026-08-26] **`#revalidate` applies `validateEnvelope` before any
    field of the reply is consumed**, against the participant the read named.
    Any validation failure returns `uncertain` on the existing bounded path;
    the old `Array.isArray` check is subsumed by the contract.
28. [done 2026-08-26] **An entry carrying the exact key under a kind this
    build does not know is `uncertain`, not `over`** — in the Codex
    dispatcher and in the ACP `episodeVerdict`, which had the same defect and
    was not named by the review.
29. [done 2026-08-26] **Four suites' authority fixtures are canonical
    envelopes**, not abbreviations of one: `claim_slot`, `stale_episode`,
    `cross_work_fence`, `failed_turn_settlement`. The deliberately unreadable
    fixtures are unchanged and still reach the uncertain path.
30. [done 2026-08-26] The review's additive regression is kept exactly as
    written and passes. Codex focused 32 -> 36 and ACP 67 -> 69; every added
    case measured to fail without the correction, and both sources restored
    byte for byte.
31. [done 2026-08-26] Codex **408/408**, ACP **69/69**, no trailing
    whitespace. Evidence in
    `evidence/gate-after-fourth-review-correction-2026-08-26.txt`.
32. [next] Independent re-review. Item 9's live smoke and item 10's deploy
    remain the operator's.

## Fifth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T04-38-41Z.md`.

33. [next P1] Require every known Work action in `validateEnvelope` to carry
    a Boolean `claimed` verdict. Missing and wrong-typed values are both an
    unreadable envelope, so pre-turn revalidation retains the exact event as
    `uncertain` and spends no turn.
34. [next] Revise the existing bare-Work validator assertion that permits an
    absent `claimed` field. This is explicit case-specific confirmation: the
    field became required when W11910 made it a scheduling input. Keep the
    additive missing-neighbor claim-slot regression.
35. [next] Rerun the focused dispatcher case and both bridge suites, then
    return for independent review. Item 9's live smoke and item 10's deploy
    remain blocked on sign-off and operator action.

## Sixth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T07-46-13Z.md`.

36. [next P1] A deferred unclaimed Work at the Codex dispatcher queue head
    must remain retained without blocking a later obligation, due trial or poke
    for the same participant. Revalidate the later readiness action and let it
    pass the Work-only gate; do not let another unclaimed Work or a generic
    event bypass the retained head.
37. [next] Keep the additive queue-order regression, preserving B's queue and
    in-flight identity after the obligation passes. Preserve claimed-recovery
    promotion, ambiguous/active retention, W99 quarantine and ACP behavior.
38. [next] Rerun `claim_slot` and both bridge suites, then return for
    independent review. Expected Codex result: 410/410; expected ACP result:
    70/70. Deploy and the live smoke remain blocked on sign-off.

## Sixth correction outcome and seventh review correction — 2026-08-26

36. [done 2026-08-26] Deferred Work B remains at the queue head while a later
    canonical `live` action may pass the Work-only claim-slot gate.
37. [done 2026-08-26] Positive obligation and claimed-recovery cases pass;
    another unclaimed Work and a generic non-readiness event do not bypass B.
38. [done 2026-08-26] Codex baseline is **413/413**. The ACP suite is
    concurrently changing under W14828 and is not a clean W11910 gate in this
    review snapshot.
39. [next P1] Reconcile ambiguity for the exact passing candidate whose
    `turn/start` was attempted behind deferred B. Do not assume an ambiguous
    delivery is `state.queue[0]`, and do not replay it before client-message-id
    reconciliation decides whether the turn was created.
40. [next] Keep the additive ambiguous-obligation regression and preserve B's
    queue position and in-flight identity after the obligation is bound.
    Preserve all sixth-correction pass/refusal cases and W99/W4303 settlement.
41. [next] Rerun `claim_slot` and the full Codex suite after correction. Rerun
    ACP once concurrent W14828 assertions settle, then return for independent
    review. Deploy and live smoke remain blocked on sign-off.

## Eighth review outcome — 2026-08-26

42. [done 2026-08-26] Both reconciliation paths now follow the exact
    ambiguous candidate rather than assuming queue position.
43. [done 2026-08-26] The reviewer added a terminating disconnect regression
    for the ordinary-drain half that the seventh correction left unmeasured.
    It passes in the current tree and fails when only that selection is
    reverted in an isolated copy.
44. [done 2026-08-26] Focused claim-slot **44/44**, complete Codex bridge
    **417/417**, ACP bridge **77/77**, and `git diff --check` clean.
45. [next operator] Deploy the signed-off v11 correction and run item 9's live
    smokes: held Work A releasing already-pending Work B without restart, and
    an unchanged no-claim action retrying after runner repair.

## Tuner deployment audit — 2026-08-27

46. [done] Revalidate the signed bridge source, current immutable release, and live process inventory. Source gates are Codex 420/420 and ACP 77/77; every active bridge process predates final sign-off, the ACP runtime still comes from byte-different `14aecfb`, and no new immutable release exists.
47. [next approver/operator] Select a clean reviewed commit containing W11910, publish it through the official immutable v11 deploy path, update the live deployment's explicit paths and accepted launcher instructions as required, and perform the drain/cutover/restart under approver authority. Do not deploy the current dirty checkout wholesale.
48. [pending after cutover] Run and record both live smokes from item 45, then close only if the unchanged readiness levels advance without a recovery restart.
