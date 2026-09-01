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

44. [done; approved in Baton response M60437] Extend
    `attempt_runtime_of` with the complete fixed `assignment`, then require an
    exact grants match before either branch or any external act. ADD-READ is
    not the W55758 contract.
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

## 2026-09-01 approved ruling and implementation handoff

48. [changes requested] Implement M60437's approved projection and pre-act
    hold. The recovery record must use the manager-fixed identity after the
    match, not repeat editable grants. Complete item 45's five negative cases
    through the documented command and prove that every external capability
    remains untouched on refusal.
49. [changes requested] Revalidate the recovery path against M60437's Worker
    Manager incarnation boundary. Never adopt or resume an older-incarnation
    runtime. Stop or kill one only with exact identity, settle its credential,
    mark the attempt interrupted, and preserve logs/output as untrusted
    evidence. Unknown, ambiguous, and mismatched runtimes stay untouched and
    are reported as zombies; automatic reconciliation is out of scope.
50. [pending final review] Complete items 46-49, rerun the focused suites and
    attached-state class, and return the exact results for independent review.

## 2026-09-01 ninth implementer round (APPROVE-EXTEND, M60437)

44. [done] `attempt_runtime_of` carries the attempt's complete FIXED
    ASSIGNMENT beside the runtime axes, in the one atomic read the branch
    already turns on.
45. [done] `recover_abandoned` holds the grants against that assignment BEFORE
    either branch and before any external act. All four parts, exactly; an
    absent assignment and an unrecorded attempt each refuse with their own
    sentence.
46. [done] Command-level negative cases for every assignment member,
    for an attempt with no fixed assignment, and for grants naming another
    attempt — each proving zero authority, engine, credential, launch and
    custody mutation and unmoved manager axes.
47. [done] The credential-to-launch restart boundary, injected at the public
    `launch.discard` after the real teardown made the credential absent: the
    first command writes a partial record with the runtime absent, the
    credential torn down and the launch unresolved, and a fresh invocation
    converges.
48. [done] The retry's credential owner is asserted BY IDENTITY: the receiver
    of `CredentialHome.adopt` is captured and the adapter must own that exact
    object. Measured — handing a fresh same-path home fails the case.
49. [partly done] The `--retry-handoff` assertion is load-bearing but is still
    made at `_for_retry` rather than by driving the documented command over
    real trusted-result state. Named in PROGRESS.

## 2026-09-01 ninth review

51. [done] Verify the complete assignment projection, four mismatch refusals,
    absent-assignment refusal, credential-to-launch restart convergence, and
    focused gates. The four-module gate is 793 tests; secret/text registries
    add 93 passing cases.
52. [changes requested] Move the exact fixed-assignment hold ahead of the
    documented command's abandonment capability builder. The current builder
    runs before `recover_abandoned` reads the assignment; the retained
    `/tmp/w55758-prehold-capability-probe.py` proves mismatched participant
    grants reach it. Preserve one atomic projection rather than split reads.
53. [changes requested] After a successful hold, source the recovery record's
    top-level Work, participant, and generation from the manager-fixed
    assignment. Current initialization still copies editable grants.
54. [changes requested] Make the absent-assignment no-act case load-bearing
    across authority, engine, credential, launch, custody, manager axes, and
    host material. Complete the documented `--retry-handoff` exact-owner case.
55. [changes requested] Complete item 49's fresh-Manager-incarnation cases and
    zombie reporting under M60437. Update the `attempt_runtime_of` secret-
    inventory rationale and return a clean `git diff --check`.
56. [pending final review] Complete items 52-55 and return focused and full
    verification with the same pre-existing failures identified separately.

## 2026-09-01 tenth implementer round (response to review 2026-09-01T10-21-35Z)

50. [done] The hold is performed by `_for_abandonment` itself, after opening
    only the control store and BEFORE the authority, the session, the roots,
    the credential owners or `launch.adopt` exist. On disagreement the builder
    returns the projection and the reason and constructs nothing else; the
    command writes the account and closes what was opened.
51. [done] A successful recovery composes `work_ref`, `participant` and
    `generation` from the manager's fixed assignment rather than from the
    grants. A refusal keeps the identity the operator ASKED for, so the two
    accounts stay distinguishable.
52. [done] The mismatch cases watch the capability seams themselves —
    `Authority.open`, `_proved_roots`, `OrphanTeardown`, `launch.adopt` — and
    assert none was exercised, which is the ruled boundary rather than
    "nothing mutated afterwards".
53. [done] M60437's incarnation rule: a `zombies` member reports every runtime
    this recovery left untouched, and cases prove a fresh incarnation still
    ends the exactly identified old runtime while an unidentifiable or running
    one is reported and left alone.
54. [done] `tests.manager.test_secrets` prose matches the widened projection.
55. [NOT DONE] The command-level `--retry-handoff` shared-owner proof.

## 2026-09-01 tenth review

57. [done] Verify the pre-capability command hold, manager-sourced successful
    identity, widened inventory, and focused gates. Six modules pass 910 tests.
58. [changes requested] Remove the caller-forgeable raw `state` override from
    exported `recover_abandoned`. The retained forged-state probe ends the
    manager's generation 1 while publishing generation 2.
59. [changes requested] Make zombie evidence structured and truthful. Report
    actual engine-returned candidate IDs and each action/outcome; do not call a
    target untouched after issuing force-remove. Cover mismatched and duplicate
    candidates, and supersede the pre-attach rule that stops every ambiguous
    candidate contrary to M60437.
60. [changes requested] Prove fresh-incarnation cleanup preserves actual
    worker output in place as untrusted, without freeze/intake/promotion.
    Complete documented `--retry-handoff` exact-owner coverage.
61. [pending final review] Complete items 58-60, rerun focused/full gates, and
    return with pre-existing full-suite failures identified separately.

## 2026-09-01 eleventh implementer round (response to review 2026-09-01T10-35-20Z)

56. [done] The carried projection is a typed capability this deployment mints,
    not an operand a caller composes. The exported operation refuses anything
    else and reads AND holds for a caller that supplies none.
57. [done] `OciAdapter.observe` carries the identities it actually saw, so a
    mismatched or ambiguous answer names its runtimes instead of reducing them
    to prose and a count.
58. [done] The zombie report names those identities and states the act
    truthfully per runtime: a target a removal was issued for is not `left
    untouched`, and candidates that were never targeted are.
59. [reported, not implemented] The pre-attach `OciAdapter._recovery_failed`
    stops every ambiguous or mismatched candidate, which contradicts M60437.
    That rule is W6634's and the supersession belongs in its record; named in
    PROGRESS for the owning reviewer rather than changed here.
60. [NOT DONE] The command-level `--retry-handoff` shared-owner proof and the
    workspace-marker assertion on the fresh-incarnation case.

## 2026-09-01 eleventh review

61. [changes requested] Remove the caller-supplied `state` boundary from the
    exported `recover_abandoned` operation. `_HeldProjection` is an ordinary
    module attribute with a public constructor, so a caller can wrap the same
    forged dictionary the nominal type check rejects and replay the original
    generation-confusion defect. The exported operation must obtain and hold
    manager state itself; keep any command-internal carried observation behind
    a non-exported composition seam rather than treating a Python class name
    as an unforgeable capability.
62. [changes requested] Carry each engine-reported candidate's own validated
    state and reason into `zombies`. Candidate IDs alone do not satisfy PLAN
    item 53's exact locator, observed state and reason: the current report
    writes `unidentified` for a candidate whose inspection says
    `Running: true` and repeats the target's diagnostic as the candidate's.
63. [changes requested] Apply M60437 to the pre-attach branch.
    `_recovery_failed` must not stop ambiguous or mismatched candidates, and
    `--abandon` must report their structured zombie evidence. W6634 is terminal
    non-satisfying, so its provisional stop-every-candidate wording needs no
    supersession; W32385 and M60437 are the current untouched-candidate rule.
64. [changes requested] Put a marker in the fresh-incarnation worker workspace
    and prove its exact bytes survive in place while freeze, intake and
    promotion remain absent. Cleanup `retained` is not evidence about file
    content.
65. [changes requested] Drive documented `main --retry-handoff` over real
    frozen, intaken, retained, independently verified state with a real
    credential. Capture the receiver of `CredentialHome.adopt` and prove the
    adapter owns that exact object. The existing public-command fixture has
    `credential_slots: []`; the exact-owner assertion remains private-builder
    only.
66. [pending final review] Complete items 61-65, rerun the focused gate and
    the relevant derived command classes, then return for independent review.

## 2026-09-01 twelfth implementer round (response to review 2026-09-01T10-56-54Z)

61. [done] The `state` operand is GONE from the exported `recover_abandoned`,
    and `_HeldProjection` is deleted rather than hardened: an importable class
    with a public constructor was never a capability. The exported operation
    reads and holds the manager's row itself; the documented command carries
    its builder's one observation through private `_recovery_of`.
62. [done] `OciAdapter.observe` carries a closed candidate observation --
    exact locator, its OWN validated state and its own reason -- on every
    branch, and `_zombie_account` composes the report from those rather than
    reconstructing members from the expected target.
63. [done] `_recovery_failed` stops only a runtime a caller identified
    EXACTLY; ambiguous and mismatched candidates are left untouched, observed
    once and carried on the refusal, and `--abandon`'s pre-attach branch
    writes them into the recovery record.
64. [done] The fresh-incarnation case writes real bytes into the worker's
    workspace and proves them unmoved and unchanged, with `frozen_output_of`
    and `intake_receipt_of` both still absent and the only custody verb
    `normalize`.
65. [done] Documented `main --retry-handoff` over the ordinary command's own
    real freeze, intake, retention and independent verification, with a real
    credential materialized through the granted home: the `CredentialHome.
    adopt` receiver is captured and the adapter is required to own that exact
    object.
67. [pending final review] Independent review of items 61-65, including the
    new pre-attach fixture and the four manager-level untouched-candidate
    cases.
68. [changes requested in review-2026-09-01T11-38-25Z.md] Canonicalize
    repeated engine candidate observations by runtime identity before writing
    `zombies`. Conflicting observations for one locator must become one
    `uncertain` row with one truthful reason and the correct per-runtime action;
    add the documented-command duplicate/conflicting-state regression and
    return for final review.

## 2026-09-01 thirteenth implementer round (response to review 2026-09-01T11-38-25Z)

68. [done] `_canonical_candidates` settles candidate observations by runtime
    identity before either branch composes `zombies`. Agreeing repeats and
    aliases collapse to one row; disagreeing ones become one `uncertain` row
    whose reason carries both of the engine's accounts. The per-runtime
    `targeted`/action fact is unchanged and is now stated once per runtime.
69. [pending final review] Independent review of item 68 and its three new
    cases: the documented command's conflicting duplicate, its agreeing
    duplicate, and the pre-attach branch's duplicate listing.
70. [changes requested in review-2026-09-01T11-53-38Z.md] Define candidate
    agreement over the complete canonical account, not state alone. Two
    `uncertain` observations with different reasons must preserve both accounts
    in one per-runtime `uncertain` row; add the documented-command regression
    and return for final review.

## 2026-09-01 fourteenth implementer round (response to review 2026-09-01T11-53-38Z)

70. [done] Agreement is decided over the whole `(state, why)` account.
    Identical accounts collapse and nothing else does, so two `uncertain`
    answers with different reasons -- a document with no state record and one
    with `Running: "yes"` -- become one `uncertain` row carrying both.
71. [done; signed off in review-2026-09-01T12-01-09Z.md] Independent review
    of item 70 and the documented-command two-uncertain-accounts regression,
    with the agreeing and different-state cases retained.
