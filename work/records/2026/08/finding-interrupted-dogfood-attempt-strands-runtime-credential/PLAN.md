# Plan

1. [done] Preserve the run7 temporary tree, stop the exact runtime, remove the
   bearer without reading it, and keep the partial workspace output untrusted.
2. [done] Inventory run7 through safe filesystem metadata and public v12
   manager surfaces. Redacted scripts/results are under `evidence/`; no store
   was opened directly and no credential content was read, copied or hashed.
3. [done] Trace `dogfood_operator`, `abandon_attempt`, OCI runtime removal,
   credential recovery/teardown and narrow handoff retry across an interrupted
   process and restart.
4. [done] Reproduce the post-discard recovery gap against an offline copy.
   The granted and assignment-derived credential homes split root from record;
   adoption refuses, the retry builder sees no delivery, and positive absence
   would be misreported as `not-delivered`.
5. [done: reviewer proposal; revalidate at implementation] Record the recovery
   contract: explicit W44716 abandonment, one credential-home owner, no-read
   orphan teardown after positive runtime absence, a public recovery mode that
   does not require lost evidence or a credential, no partial-output
   acceptance, and exact replay/idempotence.
6. [done] Add the ruled
   recovery path and credential teardown that does not depend on the ordinary
   arc reaching freeze/intake. Reuse `abandon_attempt` when a runtime is
   attached; a pre-attach interruption instead receives exact bounded orphan
   cleanup and invents no terminal attempt. Do not create a second authority
   fence/runtime/terminal ending. The credential-home contract is option (a)
   and the accepted grants contract does not move.
7. [changes requested in review-2026-09-01T04-57-06Z.md; 29 new cases exist,
   but the required interruption/restart matrix remains incomplete] Cover
   interruption at every boundary from credential
   materialization through freeze, runtime present/absent/uncertain,
   credential present/absent/mismatched, process restart, repeated recovery,
   provider failures, real non-secret credential restart, and refusal to
   accept partial output. Re-run the three recorded 557-test baseline suites.
8. [pending re-review] Independently verify exact runtime/credential absence,
   durable ending, no bearer publication, no newer-attempt action and no automatic
   acceptance of the interrupted workspace.

## 2026-09-01 implementer round

9. [done] The credential-home contract is recorded as option (a): one owned
   `CredentialHome` capability shared by materialization, publication, retry
   and teardown. Option (b) would move the accepted grants contract and needs
   a supersession; none is appended.
10. [done, and it refutes my own filing] `discard_orphan` does NOT foreclose
    `abandon_attempt`. A recovery-shaped adapter answers
    `{'lifecycle_state': 'not-delivered'}` for the credential — reachable, and
    a false positive claim rather than a refusal. The recovery command must
    carry the credential owner so the ending says `torn-down` or `unresolved`.
11. [done; signed off in review 2026-09-01T03-45-20Z] Both decisions above,
    before item 6 proceeds. The reviewer revalidated the false `not-delivered`
    ending and option (a), and pinned the pre-attach cleanup clarification.

## 2026-09-01 second implementer round

12. [done] `credentials.OrphanTeardown` plus `CredentialHome.orphan_evidence`
    and `.tear_down_orphan`: a typed, exact-record, no-read ending for a
    credential whose materializing process is gone. It holds both proved homes
    so the legacy run7/run8 split is ended by HOLDING both, never by following
    the `credential_root` member of a record.
13. [done] `OciAdapter` takes `credential_home` (option (a)'s one owner) and
    `credential_orphan`. `_torn_down` answers `torn-down` after positive
    absence and `unresolved` without it; `not-delivered` survives only where
    nothing was ever delivered. An adapter holding both a delivery and an
    orphan is refused.
14. [done] `attempt_runtime_of` is a new public read, and it exists so the
    recovery branches on durable manager state rather than on the wording of
    a refusal. `label_context` is exported for the pre-attach proof.
15. [done] `dogfood_operator --abandon --abandon-reason` with `_for_abandonment`
    and `recover_abandoned`: two branches on that read, a new closed
    `RECOVERY_MEMBERS` document under the same three write holds, no
    credential operand, no restage/offer/claim/provider/freeze/intake/
    retention/pass, and the workspace output neither read nor promoted.
16. [done] `_launched` and `_for_retry` now pass the granted `CredentialHome`
    into the adapter, so materialization, publication, adoption and teardown
    have one owner.
17. [partly done] 29 new regressions. The uncovered matrix rows are named
    exactly in PROGRESS.md rather than implied to be covered.
18. [done under the fourth implementer round; ruling M59057] Make the
    earliest post-materialization/pre-attempt interruption recoverable without
    deleting on raw grants alone. Materialize lazily in
    `_launched.adapter_of` after assignment activation and before runtime
    creation, so a bearer cannot exist without the durable selector needed to
    prove runtime absence.
19. [done; verified in review-2026-09-01T05-09-56Z.md] Bind
    `OrphanTeardown.attempt_id` to the exact cleanup command before any engine
    or credential mutation, so one attempt's ending cannot delete a sibling
    attempt's material.
20. [done and verified, including the real two-home regression in item 27]
    Preserve a bounded recovery record across faults after
    cleanup begins, including a multi-home partial teardown, and keep the
    operation retryable without persisting raw exception text.

## 2026-09-01 third implementer round (response to review 2026-09-01T04-57-06Z)

21. [done] One attempt's ending never removes another's credential. Every
    destroy command already names `runtime_attempt_id`; `_removed` now binds
    the held `OrphanTeardown` against it BEFORE the engine is called, and a
    mismatch or an unnamed attempt refuses `refused/precondition` with no
    engine act. The refused-start exit, which has no command to bind against,
    refuses to use an orphan at all.
22. [done] A recovery that began always leaves an account. Each pre-attach
    mutation is caught separately and becomes a named `unresolved` fact, and
    an unexpected fault carries the composed record out on the exception so
    `_abandoned` writes it before propagating — the same rule `main` already
    holds for a post-start fault. Only the fault's type name is recorded.
23. [done under the fourth implementer round; ruling M59057] The earliest
    interruption window is closed by lazy post-activation materialization,
    and the open-defect reproduction was replaced with the ruled temporal
    behavior.
24. [done] Six new regressions; seven mutations of the two corrected guards,
    all caught after one test was made load-bearing. 693 tests OK across
    dogfood_operator, credentials, attempts and oci.

## 2026-09-01 third review

25. [done; approved in Baton response M59057] Materialize credentials lazily
    in `_launched.adapter_of` after `activate_assignment`, while retaining
    `run_dogfood_task`'s current parameter list. The ruling explicitly
    supersedes the existing bundle-time `credentials.Delivery` assertion with
    temporal no-root/no-record-before-activation, exact one-time
    materialization, and same-Delivery/same-granted-home adapter assertions.
26. [done under the fourth implementer round] Close the earliest crash window under the recorded
    ruling and flip the open-defect reproduction to the ruled absence/cleanup
    behavior.
27. [partly done] The real two-home partial-failure/exact-retry probe is in the
    suite. The remaining plan-item-7 public-command matrix is still required
    before final independent security review.

## 2026-09-01 fourth implementer round (APPROVE-LAZY, M59057)

25. [done] `_launched` no longer materializes when it builds capabilities.
    `adapter_of` materializes exactly once, through the already-validated
    operator-granted `CredentialHome`, and the arc calls it after
    `record_attempt`, the claim and `activate_assignment` and before
    `request_runtime_start`. `run_dogfood_task` keeps its parameter list; the
    forwarded operand is discarded because the deployment that materializes
    lazily owns the act.
26. [done] The bundle-build `Delivery` assertion is replaced by the ruled
    temporal ones: construction leaves no volatile root and no lifecycle
    record; the factory materializes exactly once when called and refuses a
    second call; the adapter holds that `Delivery` and the same granted home.
27. [done] The real two-home partial-failure and exact-retry regression is
    promoted out of the temporary probe into `tests.manager.test_credentials`.
28. [partly done] Plan item 7's remaining rows are unchanged and named in
    PROGRESS. 703 tests OK across dogfood_operator, credentials, oci and
    attempts; four mutations of the ruled ordering and the retry, all caught.

## 2026-09-01 fourth review

29. [changes requested] Make the APPROVE-LAZY temporal assertions
    load-bearing across the real arc: prove materialization occurs after
    `activate_assignment` and before `request_runtime_start`, and prove the
    adapter receives the exact `CredentialHome` object that materialized the
    delivery rather than merely another home with the same path.
30. [pending] Complete the remaining plan-item-7 public-command matrix named
    in PROGRESS, then return for final independent security review.

## 2026-09-01 fifth implementer round (response to review 2026-09-01T05-40-30Z)

29. [done] The approved temporal assertion is made load-bearing ACROSS THE
    ARC. One case drives `main` through the real `_launched` bundle, wraps the
    package operations `run_dogfood_task` imports, and asserts the marks are
    exactly `activate`, `materialize`, `start` — and that the adapter owns the
    exact home object whose `materialize` produced the delivery, by identity
    rather than by path. Measured: moving the factory call above
    `activate_assignment` is caught.
30. [partly done] Matrix rows added this round: exact retry through the
    recovery composition with no second external act; a conflicting
    declaration recorded rather than forced; an uncertain runtime settling
    nothing and leaving the bearer where it is; a damaged lifecycle record
    unlinked rather than read; and a recorded root elsewhere proved not to be
    followed. Remaining rows are named in PROGRESS.
31. [done] 721 tests OK across dogfood_operator, credentials, oci and
    attempts (703 before).

## 2026-09-01 fifth review

32. [changes requested] Make the new arc-order regression tear down the real
    `Delivery` it materializes and prove its canary is no longer registered
    live before the case ends. The current test removes the temporary tree
    without settling the credential capability and poisons later secret
    checks in the same process.
33. [pending] Build the durable attached-state public-command fixture and use
    it to complete every remaining plan-item-7 row named in PROGRESS before
    returning for final security review.

## 2026-09-01 sixth implementer round (response to review 2026-09-01T05-46-47Z)

32. [done] The arc-order case ends the real `Delivery` it makes, through its
    OWNING home, and proves the canary is no longer live. Verified with the
    reviewer's own diagnostic: `live_after False`.
33. [done] The reusable ATTACHED-state fixture exists and its premise is
    proved: the operator's own grants, stores, offer, claim, activation,
    launch delivery, credential materialized through the granted home in the
    arc's own order, and an attached runtime with cleanup still `pending`.
    `_ended_however` is neutered, which IS the interruption.
34. [done] A defect the fixture found: a refused `abandon_attempt` left
    `credentials` null in the recovery record while the credential had
    already been torn down. `_credential_account` now reports the
    capability's own account on both paths.
35. [done under the seventh implementer round] The remaining item-7 rows all run through the
    documented command over attached state, and every one of them stops at
    the same place: `_for_abandonment` builds a real `OciAdapter` whose
    DIRECTORY CUSTODY act runs a helper container, and the fixture's engine
    answers the removal and the inspection but not that. The blocker is
    pinned as a case rather than described.

## 2026-09-01 sixth review

36. [done] The original arc-order regression now settles its real Delivery
    through the owning home; the isolated diagnostic reports
    `live_after False`.
37. [done under the seventh implementer round] Make the attached-state fixture simulate the original
    process boundary without poisoning this test process's live-secret
    registry. Both current attached-state cases pass while leaving
    `live_secret(CANARY) == True`.
38. [done under the seventh implementer round] A directory-custody refusal occurs after authority
    fencing and runtime removal, but the recovery record still writes
    `authority_fence`, `runtime`, `cleanup`, `custody`, and `observed_after`
    as null. Preserve or re-observe every already-known partial-ending fact;
    fixing only the credential member does not satisfy the recovery-record
    contract.
39. [partly done] The accountable custody fixture is present and attached
    `main --abandon` resolves. The remaining plan-item-7 rows are still
    required before final review.

## 2026-09-01 seventh implementer round (response to review 2026-09-01T05-54-54Z)

36. [done] The attached-state fixture models the PROCESS boundary: the
    interrupted process's in-memory registrations are released while its
    on-disk root is deliberately kept, and the fixture asserts the canary is
    not live before any case is built on it. Every attached case reports
    `live_after False` in isolation.
37. [done] `_partial_account` re-observes, through public surfaces only, every
    fact a terminal refusal has already committed: the authority fence from
    the authority's own assignment, the runtime from the adapter's
    observation, the manager's axes from `attempt_runtime_of`, and both
    provider endings from their own capabilities. Only the act that refused
    stays unset.
38. [done] The custody act is supplied by the fixture's engine, which was the
    measured blocker. `main --abandon` over durable attached state now
    resolves.
39. [partly done] Matrix rows added: attached `main --abandon`; exact retry
    through the command; a conflicting declaration; a terminal refusal
    reporting its partial account; an engine that cannot be asked settling
    nothing and keeping the bearer; and the runtime-created-before-its-record
    interruption. Remaining rows are named in PROGRESS.

## 2026-09-01 seventh review

40. [done] Verify the attached fixture process-boundary cleanup, terminal
    partial account, custody stub, attached command, retry, conflict,
    uncertainty, and unpublished-record cases. The focused gate is 734 tests
    and the attached class leaves no live canary registration.
41. [changes requested] Complete running, wrong-label, and duplicate runtime
    outcomes; every command restart boundary; newer generation/runtime
    refusal; and shared-owner `--retry-handoff` adoption before returning for
    final security review.

## 2026-09-01 eighth implementer round

40. [done] Runtime outcomes through the command: a runtime the engine still
    reports RUNNING, an inspection naming ANOTHER runtime, and one naming the
    identity TWICE. All three settle nothing and leave the bearer exactly
    where the interrupted attempt left it.
41. [done] Restart through the command at the fence, the removal and directory
    custody: the faulting run still leaves an account, and a second invocation
    from the same grants converges to `retained` with the host clean and no
    registration left live.
42. [partly done] `_for_retry` adopts through the granted `CredentialHome`,
    but the new case drives the private builder, compares only paths, and does
    not prove the documented `--retry-handoff` command uses the exact object
    whose `adopt` call produced the delivery.
43. [reported, not implemented] Two rows remain and both are named with their
    reason in PROGRESS: a restart BETWEEN the credential and launch teardowns
    has no public seam between them, and the grants-versus-manager hold the
    finding's contract item 2 requires is genuinely absent from the recovery
    command rather than merely uncovered.

## 2026-09-01 eighth review

44. [decision requested] Choose the public fixed-assignment recovery
    projection recorded in FINDING.md. Recommendation: APPROVE-EXTEND
    `attempt_runtime_of` with the complete fixed `assignment`, then require an
    exact grants match before either branch or any external act.
45. [changes requested after item 44] Add authority UUID, Work, participant,
    generation, and absent-assignment refusals through documented
    `main --abandon`; each must leave authority, runtime, credential, launch,
    and custody state untouched.
46. [changes requested] Cover restart between credential and launch teardown
    through the command. Inject the fault at the public `launch.discard` act
    after orphan teardown, then prove the first record reports the partial
    ending and a fresh invocation converges.
47. [changes requested] Drive documented `--retry-handoff`, capture the
    receiver of `CredentialHome.adopt`, and prove the adapter owns that exact
    object by identity. A private-builder call plus same-path comparison is
    not the required command-level shared-owner assertion.
