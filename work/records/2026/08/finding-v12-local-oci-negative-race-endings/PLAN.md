# Plan: local OCI negative and race endings

## Complete — independent review claim168683

review-2026-09-14T11-10-46Z.md accepts the exact changed test candidate and the composed
parent matrix. W32576/W32577/W32648/W32649 are all closed satisfying. Prior
accepted child crossings and verification remain applicable; the parent now
asserts deadline cleanup and refusal of successor reuse before settlement.
No selected parent source/test/verification step remains. Canonical closure168717
records satisfying outcome; detail at168719 confirms closed status and no claim.
W3 and W33755 retain independent completion requirements.

Current evidence: review-audit-168683.json. Author fresh engine results remain
attributed reports; no new reviewer engine run or broad-suite pass is claimed.
W168703 separately owns the20 unregistered modules and preservation of explicitly
gated execution. Do not bypass the guard or register supervised engine tests
blindly. No new dependency is installed for this separate limitation.

All historical incomplete provider/order/deadline statements below are superseded
by this final review; their decision history is retained.

## Historical plan and implementation reports


1. Revalidate W6636's final one-container, provider and cleanup contracts.
2. Add offer-expiry and post-create non-duplication real-engine regressions.
3. Drive `plan-rejected`, `unsupported-version`, and deadline through the
   shared terminal cleanup crossing.
4. Verify exact engine absence, provider endings, durable state and lane reuse
   ordering under retry.
5. Run focused Docker and manager gates and return for independent review.

## 2026-08-28 — implementer round

- [done] 1. W6636's final contracts revalidated on the tree.
- [done] 2. Offer-expiry and post-create non-duplication composed.
- [partial] 3. `plan-rejected` drives the shared terminal cleanup crossing.
  `unsupported-version` is a handshake refusal rather than a runtime
  disposition and the deadline belongs to interrogation; both are reported
  rather than invented. See `PROGRESS.md`.
- [done] 4. Exact engine absence, provider endings and durable state verified
  at each ending, including a cleanup held open by an unresolved root while
  the container is really gone.
- [done] 5. Focused Docker and full manager gates run; returned for review.

## 2026-08-28 — independent review disposition

- [verified partial] Offer expiry blocks execution, `plan-rejected` reaches
  real cleanup, and an unresolved provider prevents early settlement.
- [required, P1] Inject a real post-create engine failure and prove exact
  attachment, no duplicate on retry, and convergence through cleanup.
- [required, P1] Compose typed `unsupported-version` handshake refusal and an
  explicitly owned runtime deadline into the attempt cleanup crossing, or
  create bound gating Work for those missing seams.
- [required, P1] Attempt the actual lane/replacement reuse boundary before and
  after settlement rather than inferring it from `cleanup=pending`.
- [required, P2] Distinguish manager-side launch-root materialization from
  runtime delivery in the acceptance and regression.

## 2026-08-28 — correction re-review

- [accepted] A real post-create fault now attaches the exact created runtime,
  refuses duplicate retry, and enters the existing cleanup path.
- [required] Complete that failed-start path through manager-owned intake or
  equivalent custody authorization, exact destruction, positive absence,
  provider settlement, and clean retry; fixture teardown is not convergence.
- [accepted] Expiry now explicitly permits manager-side materialization while
  proving no runtime received that delivery.
- [required] Replace the same-terminal-attempt double refusal with an actual
  new-attempt/lane consumer after cleanup; only the pre-settlement act refuses.
- [decomposed as W32576, child provider] Implement typed unsupported-version
  cleanup in `findings/finding-v12-handshake-refusal-runtime-cleanup/`.
- [decomposed as W32577, decision plus child provider] Rule and implement
  runtime-deadline cleanup in
  `findings/finding-v12-runtime-deadline-cleanup/`.

## 2026-08-28 — second correction re-review

- [required as W32648, child provider] Replace manually written worker `unable` and
  fabricated output with a manager-owned post-create start-failure ending and
  ruled no-envelope custody/cleanup path in
  `findings/finding-v12-post-create-start-failure-cleanup/`.
- [required as W32649, child provider] Add the missing cross-attempt lane/capacity owner
  and prove pre-settlement refusal plus one post-settlement winner in
  `findings/finding-v12-cross-attempt-lane-capacity/`.
- [sequencing required] W32649's impl Route installs a dependency on W16823
  before implementation so the lane consumes canonical principal/scope context
  rather than endpoint spelling.

## 2026-09-14 - providers landed; the two deferred items are closed out

- [done] The successor/lane ordering is now ENFORCED rather than witnessed.
  W32649's cross-attempt lane owner exists, so the case attempts a real
  successor attempt BEFORE the predecessor's ending is proved, asserts the
  exact predecessor refusal, asserts nothing was created, and only then lets
  the settled predecessor hand the lane over to one winner.
- [done] The runtime deadline takes the same cleanup crossing, asserted in the
  ORDINARY serial registry beside `plan-rejected`: observation alone touches
  nothing, then fence, exact removal, positive absence, both provider
  teardowns, settlement, lane release and a replaying proof.
- [revalidated, not duplicated] `unsupported-version` is proved on a real
  daemon by W32576's `test_refused_session_engine`, which sits in the same
  serial registry on the same fixture. Ran it rather than copying it.
- [reported] `tools/parallel_test.py` will not start in this tree: twenty
  modules owned by other in-flight Works are unregistered and its guard
  refuses. Focused module, fixture neighbour and all four child seams were run
  instead; registering those modules belongs to the Works that own them.

All four mandatory children are closed `satisfying`. Returned for independent
review rather than closed.
