# Plan

1. [done 2026-08-21] Revalidate the parent rulings against current v11 authority and
   accepted `v12/` proof behavior; separate confirmed facts from proposed v12
   contract.
2. [done 2026-08-21] Specify durable identities, authority-owned claim generation, and
   the non-overlapping Work, offer, assignment, runtime, output, proposal, and
   disposition state records.
3. [done 2026-08-21] Produce the complete transition and reconciliation tables,
   including idempotent retry and ambiguous-result settlement.
4. [done 2026-08-21] State safety and liveness invariants with explicit counterexample
   traces for stale, competing, restarted, cancelled, and uncertain workers.
5. [done 2026-08-21] Add executable model tests for the approved scenarios without
   changing application or runtime behavior.
6. [done 2026-08-21] Independently review the specification and tests, then return the
   design gate for approval before any runtime implementation.

   Reviewed by `baton.claude` in `review-2026-08-21T16-20-35Z.md`. Every
   Confirmed tree claim re-derived and upheld; 13/13 model scenarios
   re-ran green. Five findings, none invalidating the contract's
   direction. Two of them (P1a fenced-vs-one-slot-capacity, P2a the
   narrowed `active` guarantee) change what open approval 1 is deciding
   and must be read before it is ruled. P2b records that open approval 4
   — the only recommendation contradicting current v11 — has no
   executable scenario.

7. [done 2026-08-21] Implementer follow-up on the contract and evidence, owned by
   `baton.claude`: replace the retained-Handler cancellation cross-product with
   assignment end plus a typed runtime gate and policy-controlled output
   retention; make token expiry the acceptance boundary; add authoritative
   per-Work contract progression and its unavailable-runtime gate; preserve
   unclaimed closure while enforcing exact identity for live-assignment close;
   route the four disposition gates through operation replay so a retry cannot
   rewrite a committed receipt (P1b); scope offer uniqueness per Work, share
   the durable control store in successor tests (P3), check participant
   capacity before offer and claim, and add all ruled close scenarios (P2b).
   Correct the stale parent close statement and re-run the model.

   Landed by `baton.claude`. `SPEC.md` is version `1-ruled` with a §0 change
   table mapping each ruling and review finding to the sections it moved.
   Cancellation now ends the assignment and installs a typed
   `runtime-quiescence` gate; token expiry is the acceptance boundary with a
   separate settlement timeout that never revives the token; a per-Work typed
   contract selector advances atomically with assignment end and gates on
   `contract-runtime:` when no certified profile exists; unclaimed close is
   preserved while a close ending a live assignment requires the exact
   identity. Capacity is a precondition of offer issue and claim; the four
   workflow receipts are immutable and replay-only; offer uniqueness is
   per Work over one shared control store. Evidence: 13 -> 27 scenarios, all
   passing. P2a is dissolved by ruling 1 rather than superseded, and the
   stale parent close statement was already corrected in the parent record.

8. [done 2026-08-21] Approver rulings at `baton.ops` on the four open
   decisions in `FINDING.md`, then approve or revise the contract before any
   runtime implementation. Ruling 1 rejects the fenced/active retained-Handler
   cross-product: end the assignment and free the participant slot while a
   typed `runtime-quiescence` gate prevents replacement until destruction or
   certified-isolation evidence satisfies it. Ruling 2 makes token expiry the
   worker's offer-acceptance deadline; a timely durable acceptance fixes one
   later exact claim reconciliation. Ruling 3 replaces global drained
   activation with an atomic per-Work contract transition that ends the old
   assignment and blocks on a typed runtime gate when the selected contract
   has no certified environment. Ruling 4 preserves authorized unclaimed
   closure and requires exact assignment comparison only when close ends a
   live assignment.

9. [done 2026-08-21; signed off after five rounds] `baton.codex` runs a focused independent re-review after item 7.
   Confirm every ruling is reflected without competing live text, every
   evidence defect is corrected, and the executable scenarios cover the
   revised transition contract. Close W151 only after that review is clean.

   The focused review confirms the four ruled transition shapes and all 27
   supplied scenarios, then adds seven red cases. An accepted offer can time
   out after its fixed authority claim already committed, hiding a live
   assignment from restart recovery. Exact cancellation retry regresses a
   destroyed runtime; failed integration retry duplicates its journal act;
   frozen output is mutable; and end, contract-transition, and close replay
   signatures omit their durable reasons. The later contract-conditional
   generation ruling is also not explicitly marked as a scoped supersession of
   the earlier unqualified parent/child text. See
   `review-2026-08-21T21-06-44Z.md`.

   Final review signed off in `review-2026-08-21T21-52-09Z.md` after items
   10-13 corrected every red boundary. All 54 scenarios pass; no application,
   protocol, runtime, schema, or dependency change is part of this Work.

10. [done 2026-08-21] Implementer response to the focused review, owned by
    `baton.claude`. The settlement timeout now resolves the fixed claim
    operation before it may expire an offer — a committed claim is recorded
    `claimed`, only a positively uncommitted one expires, and an unanswerable
    lookup leaves the offer accepted rather than defaulting to expired.
    Manager-owned mutations carry their own control-store operation records,
    runtime observations never regress from a terminal `destroyed`, frozen
    output is immutable, a refusal that wrote something durable replays that
    refusal instead of repeating it, and `end`, `advance_contract` and `close`
    bind their reason/rationale in the replay signature. The parent
    "Assignment-generation identity" ruling now carries a dated scoped
    supersession, mirrored in this record's decision summary and acknowledged
    in `SPEC.md` §1. Evidence: 27 -> 38 scenarios, all passing, every
    correction mutation-checked. Detail in `PROGRESS.md`, focused-review
    response.

11. [done 2026-08-21] Correct the round-2 effectively-once boundaries, then
    return for focused review. A read-only absent claim result must not permit
    offer terminalization while that fixed operation can still commit;
    terminal claim refusal/retirement must be durable against stale retry.
    Intake and cleanup must carry the manager operation identities already
    required by `SPEC.md` section 7, including replay of cleanup's
    state-writing refusal. Four additive scenarios are red. See
    `review-2026-08-21T21-27-27Z.md`.

    Landed by `baton.claude`. Settlement is now ONE authority act that finds
    the committed claim or RETIRES the fixed identity, and retirement answers
    every later and stale submitter regardless of the operands it asks with;
    the manager retires that identity in the same breath as writing
    `claim-refused`, so no terminal control row can coexist with a claim that
    might still commit. Intake carries its own disposition operation identity,
    and cleanup's `blocked-on-intake` refusal is durable to its own operation
    while a distinct cleanup operation may re-evaluate the moved boundary.
    Evidence: 38 -> 45 scenarios, all passing, every correction
    mutation-checked. One of the implementer's own earlier scenarios asserted
    the overturned cleanup behaviour and was corrected rather than the
    reviewer's; it is flagged in `PROGRESS.md`.

12. [done 2026-08-21] Correct the round-3 settlement boundaries, then return for final
    focused review. Persist and enforce a claim-settlement deadline distinct
    from the bearer acceptance expiry, so an immediate timeout cannot retire a
    newly accepted offer. Make commit-or-retire validate the fixed claim's
    complete operation signature before accepting a committed result or
    retiring an unsubmitted identity; a pre-existing operation with different
    operands must fail closed without being rebound or overwritten. Two
    additive scenarios are red. See
    `review-2026-08-21T21-40-39Z.md`.

    Landed by `baton.claude`. Acceptance now records a claim-settlement
    deadline of its own, derived from a deployment settlement window rather
    than from the bearer expiry, and retirement requires reaching it —
    while reconciling a claim that already committed does not, because
    learning an outcome is not declaring one. `settle_operation` takes the
    fixed claim signature: a committed or durably refused record under that
    id with different operands is a collision that refuses and changes
    neither record, and a retirement binds the operands it settled so the
    journal says which operation died. Evidence: 45 -> 51 scenarios, all
    passing, every correction mutation-checked. Three of the implementer's
    own earlier scenarios exercised the timeout in the instant of acceptance
    and now reach the deadline first; what they assert is unchanged and the
    edit is flagged in `PROGRESS.md`.

13. [done 2026-08-21] Correct the remaining restart boundary, then return for final
    focused review. Authority retirement must durably bind the offer's
    terminal disposition as well as the fixed claim operands and reason, so a
    crash before the control-store CAS cannot let a later entry path relabel
    `settlement-expired` as `claim-refused` or vice versa. Every retry path
    finding that retirement must replay its one terminal disposition. One
    additive crash scenario is red. See
    `review-2026-08-21T21-48-06Z.md`.

    Landed by `baton.claude`. `settle_operation` takes the disposition its
    caller's path would terminalize as and records it WITH the retirement,
    beside the operands and reason; `_terminalize` then applies the bound
    disposition of any retirement it finds rather than its own caller's, so a
    crash between the two stores cannot let a retry path relabel the outcome
    in either direction. Evidence: 51 -> 54 scenarios, all passing, every
    correction mutation-checked. One of the implementer's own scenarios read
    the retirement's free-form reason and now reads the richer record; the
    edit is flagged in `PROGRESS.md`.
14. [amended 2026-08-22, W4487] The decline token contradiction between this
    contract and frozen worker-control 1.0 was ruled by `baton.slaw`: the
    non-secret decline envelope is kept and §7's "exact unspent token"
    requirement for DECLINE is explicitly superseded. §1 carries the dated
    supersession with the old row quoted, §6 and §7 carry the replacement, and
    the evidence gained seven decline scenarios (54 -> 61). Acceptance is
    unchanged. Reviewed under W4487;
    `work/records/2026/08/finding-worker-control-decline-token-conflict/`.
