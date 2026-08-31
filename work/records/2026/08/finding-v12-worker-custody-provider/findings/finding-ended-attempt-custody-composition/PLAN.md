# Plan

1. [done] Revalidate the enrichment's observations and the existing ending's
   order against the current tree. All three hold; recorded in `FINDING.md`.
2. [done] Pin the decisions the wiring rests on: the `directory_custody` noun,
   the per-(attempt, root, verb) identity, and the accountable-success
   precondition.
3. [done: approver ruling 2026-08-30] Option (b) is accepted: normalize and
   account for both writable roots on failed-start and refused-session
   endings, retain both roots in place, and let the later explicit retention
   cleanup own removal. Normalization restores manager group access and does
   not trust, freeze, admit or delete M33800's retained bytes.
4. [done: approver ruling 2026-08-30] The result root is mandatory and is
   manager-derived as `workspace/result-<attempt-id>`. Attempt allocation
   creates it before runtime start; cleanup never creates it and refuses a
   contradictory absence. Logs may exist even when `output.json` declares no
   accepted output artifacts.
5. [next] Implement the production wiring, the durable receipt, and the
   regression matrix the enrichment and latest review list.

## Why no production code changed this round

`intake.py` is the manager's ending core and the change is a new durable
outcome inside a frozen axis. Wiring it against an applicability reading the
approver's own ruling bears on would be exactly the kind of decision
`AGENTS.md` says to pin and revalidate first — and this record would rather
carry an unanswered question than an implementation built on a guess.

## 2026-08-30 — the ruling, and what it unblocks

3. [RULED — option (b), confirmed with a recorded caveat] All three endings
   normalize both writable roots and account for each outcome. Ordinary
   cleanup then removes; failed-start and refused-session retain both roots in
   place and remove neither. `FINDING.md` records why the reasoning holds, and
   records that normalize MUTATES retained mode bits — the one cost the
   research did not weigh, with the alternative (normalize at the point of
   removal) named so a later reader knows it was considered.
4. [RULED] The authoritative result locator is the mandatory
   `workspace/result-<attempt-id>` created at attempt allocation. Custody
   derives it from manager-owned identity and never creates a missing root.
5. [NOT STARTED] The production wiring, the durable `directory_custody`
   receipt, and the regression matrix.

## 2026-08-30 — locator re-review

1. [accepted slice] Allocation establishes and custody derives the same
   mandatory `workspace/result-<attempt-id>` locator; custody creates nothing
   and refuses missing/link contradictions. The retired-path reviewer fixture
   is updated under the implementer's explicit request.
2. [required P0, unchanged] Implement the signed per-root
   `directory-custody.normalize` receipt, replay-read adoption, terminal
   cleanup binding and explicit typed call seam from
   `review-2026-08-30T11-32-34Z.md`.
3. [required] Compose all three ruled endings and the complete
   unresolved/crash/restart/replay/signature-collision regression matrix before
   W43975 can close.

## 2026-08-30 — durable receipt re-review

1. [accepted slice] Accountable per-root receipts, exact replay-read adoption,
   signature binding and the typed adapter seam are present in isolation.
2. [required P0] Derive the operation ID only from attempt, root and verb.
   Keep custodian image and configured workspace store in the signature so a
   retarget hits the existing operation and refuses with `operation-collision`.
3. [required P0, unchanged] Wire both receipts into all three endings, bind
   terminal cleanup to their adopted results, perform the single ordinary
   removal, and complete the crash/restart/replay matrix.
4. [regression] The seven-module aggregate runs 716 tests: the prior 715 pass
   (one skipped) and the new changed-store collision witness is the sole
   failure.

## 2026-08-30 — operation-identity correction re-review

1. [accepted] The operation ID is now only attempt/root/verb; workspace store
   and custodian image remain signature inputs, and both replay adoption and
   normalization use the same derivation.
2. [verified] The focused 112 custody tests and seven-module 716-test aggregate
   pass (one aggregate skip), including the changed-store collision witness.
3. [required P0, unchanged] Complete the all-three-ending production wiring,
   receipt-bound terminal result, ordinary removal and full
   crash/restart/replay/collision matrix before W43975 can close.

## 2026-08-30 — ending-composition re-review

1. [accepted slice] All four current endings reach result-then-workspace
   normalization; terminal settlement replay-reads and carries both receipts;
   recordless endings retain their homes.
2. [required P0] Correct ordinary removal ownership. Whole-home
   `discard_workspace` deletes retained/quarantined custody and unrelated
   credential roots. Preserve every kept locator and sibling provider domain;
   this observed contradiction supersedes the earlier literal
   `discard_workspace(storage, attempt_id)` helper choice. The invariant of
   one contained attempt-owned removal remains; deleting the complete shared
   home does not satisfy it.
3. [required P0] Preflight the typed custody capability and signed custodian
   image before runtime/provider destruction on every path that can require
   normalization.
4. [required P0] Add the complete all-ending crash/restart/replay/collision
   matrix, including each receipt boundary, removal-before-terminal-commit,
   exact replay after absence and terminal receipt binding.
5. [regressions] The 820-test focused aggregate has two failures and one skip;
   the prior 818 pass. The failures prove retained-locator deletion and
   destructive work before the missing-custody refusal. The disclosed Docker
   sibling-credential failure is the same over-broad removal scope.

## 2026-08-30 — selective-removal re-review

1. [confirmed] Selective execution-root removal preserves retained custody and
   provider siblings; all four endings preflight custody before destruction.
2. [required P0] Apply allocation's exact no-link, own-canonical-directory
   proof at the destructive home and root identities before thaw/traversal.
   Containment inside the store does not authorize following a sibling alias.
3. [required P0, unchanged] Complete the composed all-ending
   crash/restart/replay/signature-collision matrix and assert both adopted
   receipts in every terminal result.
4. [regression] 854 focused tests: the prior 853 pass; the new sibling-home
   alias witness fails because assignment-1 cleanup deletes assignment-2's
   workspace sentinel.

## 2026-08-30 — corrected removal ownership (supersedes point 5's literal call)

1. [superseded] `discard_workspace(storage, attempt_id)` as the ordinary
   removal. It deletes the whole attempt home, including retained custody
   locators and another manager domain's credential state.
2. [decided] Ordinary cleanup removes ONLY `inputs` and `workspace` — the two
   roots this attempt's workspace ending owns — and preserves `custody`,
   `credentials` and `credential-state`.
3. [decided] The custody seam and its image identity are proved at ending
   ENTRY, before any destructive work, beside the destroy capability.
4. [open] The three-ending crash/restart/replay/collision matrix.

## 2026-08-30 — destructive-identity re-review

1. [confirmed] A static symlinked attempt home is refused; the prior sibling
   witness passes.
2. [required P0] Prove the home and every present execution root before thaw
   or any removal. The current sequential loop deletes `inputs` before
   discovering an invalid `workspace`.
3. [required P0] Hold each proved root identity through destructive traversal.
   Reopening its pathname after `_proved_own` follows a replacement alias into
   a sibling attempt.
4. [accepted slice] Per-root receipt interruption, restart, exact replay and
   custodian collision are covered; abandonment covers the corresponding
   ending-level composition.
5. [required P0, unchanged] Complete interruption/restart/receipt-binding and
   exact-replay coverage for ordinary cleanup and the other two recordless
   endings, including removal-before-terminal-commit and retry after roots are
   absent.
6. [regressions] 865 focused tests: 862 pass, one skips and the two new
   destructive-boundary witnesses fail.

## 2026-08-30 — descriptor-relative removal re-review

1. [confirmed] The complete home/root set is opened no-follow before thaw or
   deletion, so an invalid second root leaves the first untouched.
2. [confirmed] Recursive removal is descriptor-relative and the final name is
   checked against the held inode; replacement preserves the sibling and
   produces a typed refusal.
3. [review fixture adapted] The replacement injection moved from retired
   `_remove` to the final name-use seam; its survival and refusal assertions
   are unchanged.
4. [required P0, unchanged] Complete interruption/restart/collision, both-
   receipt terminal binding and exact replay at ordinary, failed-start and
   refused-session public endings. Include ordinary removal-before-commit and
   retry after execution roots are absent.
5. [verified] 866 focused tests pass (1 skipped); Docker gates are unavailable
   to this managed reviewer.

## 2026-08-30 — all-ending composition signoff

1. [done] Ordinary, failed-start and refused-session public endings now cover
   interruption/resume, changed-custodian collision, both-receipt terminal
   binding, exact replay and their distinct remove/retain behavior.
2. [done] Ordinary removal-before-terminal-commit retry is proved from the
   faithful crash state: both receipts committed, execution roots absent and
   cleanup still pending; no absent root is normalized again.
3. [done] All recorded W43975 acceptance items are satisfied. Independent
   non-Docker aggregate: 930 tests pass (1 skipped); Docker remains unavailable
   to the managed reviewer and its implementer run is durably reported.
