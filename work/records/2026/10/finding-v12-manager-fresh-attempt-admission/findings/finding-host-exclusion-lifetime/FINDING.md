# W359719 — host identity and exclusion lifetime

## 2026-10-23 — bounded decomposition from W358969

**Confirmed:** parent review `../../review-2026-10-23T22-41-20Z.md` R13/R14 and
`../../evidence/review-359705/PROBE.json` show overlapping guard users lose
exclusion on the first user's exit and an unrelated empty control store can be
accepted as this instance's host. CLI expected=taken.control checks a supplied
path against itself. Existing DESIGN REC-7 and DB-3–5 require real ownership.

**Outcome:** positive instance/host identity and exclusion throughout every active
admission lifetime, with no release of a serving owner's guard. Keep missing or
unknown runtime/resource facts fail-closed; legitimate never-launched behavior
requires positive owning evidence. No general ownership framework is selected.

**Acceptance:** overlapping admission lifetimes, different Job identities, first
user exiting before second, both ordinary/error exits, borrowed external serving
guard, same-process and separate-process contention all preserve exclusion or
refuse safely. Preserve fork/cache behavior. Wrong independent control-store
selection refuses before trusting absence or performing effects, including real
CLI wiring and direct-manager composition. Right-instance positive retry and
unknown-token/runtime refusals remain covered. Tests use real disposable owner
APIs with deterministic controlled execution, no live models or engine operation.

**Serial dependency:** do not start implementation until W359718 is independently
accepted. Consume its exact pinned cumulative candidate, preserving all accepted
submission changes. Parent candidate-359603 is historical baseline only after
that handoff. Parent W358969 owns joined acceptance; W325959 remains gated.

**Ownership:** claimed baton.impl author owns this child's new isolated cumulative
candidate, test changes and PROGRESS; baton.rvpc owns FINDING/PLAN/review/evidence.
Preserve parent and sibling candidates. Necessary product/test paths are chosen
by the implementer, recorded with exact digests, and edited serially. No canonical
product import, deployment or Git mutation selected.

## 2026-10-23 — dependency accepted, execution released

W359718 closed satisfying at event359899 after independent review of cumulative
candidate359821 manifest9f06dbe3. Exact source and signoff are pinned in PLAN.
Canonical wake359900 and detail readback confirm this child ready; reviewer
claim359901 prepares its implementation handoff. R13/R14 remain present in the
unchanged host code inherited by that candidate. No new scope/spec decision is
needed. Preserve the accepted submission behavior while correcting this bounded
host identity/lifetime outcome; no separate general ownership project is selected.

## 2026-10-24 — recovered preparation claim360416

**Observed operational finding:** reading this child's `PROGRESS.md` returned
ENOENT. No implementation handoff or candidate is recorded for this child;
the absent author record supplies no implementation evidence. The receiving
implementer must create its attributable PROGRESS when execution starts.
Reviewer has not created or impersonated that author account.

**Confirmed:** owner recovery event360406 released interrupted claim359901;
claim360416 succeeded under baton.rvpc. The accepted predecessor manifest still
hashes to the exact value pinned in PLAN. Its `InstanceOwnership.held` still
uses separate read/acquire and releases the first acquirer's guard on exit;
its CLI still constructs `HostExclusion(control, expected=taken.control)`.
Thus R13/R14 remain the actionable correction. This preparation performed no
tests or product edits and makes no new acceptance claim. Existing independent
probe evidence remains applicable to the unchanged host implementation.

## 2026-10-24 — first candidate independent review, claim360558

**Confirmed:** candidate-360435 improves sequential borrowing and CLI path
validation but retains concurrent guard-loss and direct-manager wrong-host
admission. Review `review-2026-10-24T00-41-56Z.md` records R16/R17 and exact
candidate digest. `evidence/review-360558/PROBE.json` preserves both independent
reproductions and 113 passing focused cases. Missing identity is not accepted
as an exception to the selected positive host-evidence requirement merely
because test doubles omit it. No new specification change is selected.

**Resolved operational finding:** the implementing claimant created PROGRESS.md;
it was read successfully on this review. Return the same bounded host correction
to implementation; parent joined acceptance remains outstanding.

## 2026-10-24 — owner composition still incomplete, claim360740

**Confirmed:** candidate360582 closes the precise borrower-registration and
missing-identity cases from R16/R17, but independent real-owner probes reproduce
cross-instance JobStore admission (R18), loss of a serving guard acquired during
a borrow (R19), and inherited-mutex deadlock on actual fork (R20). Exact candidate,
evidence, limits and verification are in `review-2026-10-24T01-09-18Z.md`.
The accepted outcome already requires real instance identity, serving-owner
lifetime preservation and fork behavior; no expanded specification is selected.
Continue the same bounded correction through implementation and independent
review, preserving accepted submission behavior and the parent acceptance gate.

## 2026-10-24 — final-release transition race, claim360896

**Confirmed:** candidate360765 passes150 independent focused cases, including
the selected R18–R20 regressions. R21 remains: final release leaves its mutex
before retiring the cached guard, so a new holder receives the descriptor just
before it closes. The independent controlled interleaving also observes a spawned
process acquire the same instance during the new lifetime. Exact evidence and
candidate are pinned in `review-2026-10-24T01-31-06Z.md`. Return this single
transition correction to implementation within the existing accepted scope.

## 2026-10-24 — bounded host slice accepted, claim360981

**Confirmed:** candidate360912 manifest164546f94cc88854271d623a149835e1283e76a4f8d9049bdc68a402656ab13f
resolves R21 and passes159 independent focused cases. The new holder waits for
full retirement, receives a fresh live guard and excludes a spawned contender
until release. Exact review `review-2026-10-24T01-43-39Z.md` accepts this child's
selected host outcome and records evidence/limits. Close satisfying to release
parent W358969 for joined acceptance of these cumulative bytes. Parent delivery,
human Git checkpoint and W325959's gate remain outstanding; no import or live
execution is selected by this acceptance.
