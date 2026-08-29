# Plan

1. Revalidate `reconcile_runtime`, adapter list/observe contracts, and engine-state normalization.
2. [approved 2026-08-27] Pin the exact-identity, unique-candidate observation
   seam and its fail-closed `running`/`quiescent`/`absent`/`uncertain` state
   model. Keep retry, removal, output, release, and reassignment policy in
   W6636.
3. Implement observation-backed reconciliation without absorbing W6636 restart or orphan policy.
4. Add running, exited, absent, duplicate, mismatch, observation-failure, and real-engine regressions.
5. Run focused and full v12 verification, then request independent review.

## 2026-08-27 — implementation

- [done] 1. Revalidated `reconcile_runtime`, the adapter's list/observe
  contracts and engine-state normalization. Found a blocker first: the axis had
  no transition to `quiescent` from `not-started` or `start-requested`, so the
  truthful answer was unrepresentable.
- [done] 2. The seam is pinned: exact identity, unique candidate, `adapter.observe`
  on that candidate, and `running`/`quiescent`/`absent`/`uncertain` kept as four
  distinct answers through the manager.
- [done] 3. Implemented without absorbing restart or orphan policy. The
  observation is recorded on every reconciliation rather than inside the
  effectively-once attachment — which is where my first version put it, and
  where the defect survived inside its own fix.
- [done] 4. Running, exited, absent, duplicate, mismatch, observation-failure
  and real-engine regressions; the lifecycle diagnostic converted to a positive
  production-seam proof.
- [done] 5. Focused and full v12 verification; returned for independent review.

### For review

- [judgement] The transition-map change adds two discoveries and removes
  nothing. If that reads as lifecycle policy rather than observation, it belongs
  to W6636.

## 2026-08-28 — independent review changes requested

- [required] When listing returns no candidate but the attempt or current start
  supplies one exact runtime identity, observe that identity and preserve the
  adapter's `absent` versus `uncertain` answer. Retain uncertainty only when no
  exact identity exists or the exact observation is inconclusive.
- [required] Normalize observation exceptions and malformed/unknown answers to
  a durable `uncertain` observation instead of leaving a stale `running` axis;
  replace the inverted lifecycle assertion with one that proves running is not
  retained.
- [required] Replace W26294's real-engine evidence that depends on W26291's
  retired environment transport. Exercise the live fixed launch-document path
  once available, or use a bounded observation-only container whose lifecycle
  does not assert the superseded worker launch contract.
- [cleanup] Supply `observed` on every `runtime.attached` construction or
  remove the unreachable same-runtime fallback.
- [verify] Extend the mutation measurement for zero-listing positive absence
  and observation-failure-to-uncertain, rerun focused tests, and return for
  independent review.

## 2026-08-28 — review corrections applied

- [done] [P0] Zero listing over a known identity observes it. The identity
  comes from the durable attachment, or from `minted` when nothing is attached
  yet; only a reconciliation naming no runtime stays unable to ask.
- [done] [P0] Every failed, malformed or unrecognised observation is a durable
  `uncertain` rather than a propagated refusal, with the exact reason carried
  on an optional `why`.
- [done] Both inverted real-engine cases corrected:
  `test_a_runtime_removed_underneath_the_manager_is_observed_absent` now
  requires the absence its subject actually produces, and the never-running
  case asserts the durable `uncertain` instead of `not quiescent`, which stale
  `running` satisfied.
- [done] [P1] Resolved by W26291 landing: no W26294 evidence uses the retired
  environment transport.
- [done] [P2] `_attach`'s same-runtime recovery return supplies `observed`.
- [done] Inventory: the two absorbed boundary owners registered in `NO_PROBE`
  with their reason, so this Work adds nothing to the accepted failure set.
- [done] The record-and-return step extracted to one owner, `_settled`. The
  correction's second caller had duplicated it, and the mutation harness
  noticed as an anchor matching twice before a reader would have.
- [done] Four mutations added for the two new rules; **13 of 13 caught**.
- [done] Gates: `test_attempts` 92, parallel 1568 with the accepted six
  `test_boundary_inventory` failures, serial 105/0 on a real daemon.

## 2026-08-28 — independent re-review changes requested

- [verified] Zero listing over a known identity now preserves positive absence;
  failed observation durably becomes uncertain. Focused 92/92 and the corrected
  P0 reproduction pass.
- [required] Rebuild the outward `runtime.attached` answer from the stable
  attached identity and the current observation after effectively-once replay.
  Include the current `why` exactly for an inconclusive observation and remove
  a replayed reason for a conclusive one.
- [required] Add both two-pass regressions (`running` to `uncertain` and
  `uncertain` to `running`) plus a mutation restoring the stale merge. See
  `review-2026-08-28T10-09-59Z.md`.

## 2026-08-28 — implementation of the re-reviewed correction

- [done] P1. `_settled` composes the outward `runtime.attached` from the stable
  attachment identity plus the current observation, with `why` riding exactly
  when the answered state is inconclusive. A cancellation from `_attach` passes
  through untouched.
- [done] Regressions: `test_a_later_inconclusive_observation_carries_its_own_reason`,
  `test_a_later_conclusive_observation_drops_the_stale_reason`,
  `test_the_fixed_identity_survives_every_later_observation` and
  `test_the_recorded_attachment_keeps_the_reason_it_was_made_with`, plus
  `evidence/w26294-corrected-replay.py` beside the reviewer's own file.
- [done] Five mutations added, including the one the review named — restoring
  the merge — and the two half-rebuild directions on either side of it.
- [next review] Independent verification, unchanged.

## 2026-08-28 — final independent review

- [signed off] The outward attachment is rebuilt from stable identity plus the
  current observation. Both replay directions and a four-pass state sequence
  preserve exact current `why` semantics and durable-axis agreement.
- [verified] Focused 96/96, both corrected reproduction sets, and targeted
  diff hygiene pass. See `review-2026-08-28T11-18-50Z.md`.
