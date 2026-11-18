# G3 — replay of a committed token act after REVOCATION: refuse or answer? (decision packet)

K, under owner claim E384905, no claim held. Returned per M385095's decision boundary: a concrete
specification ambiguity, with exact behaviour and options, BEFORE a new rule is implemented. Nothing is
implemented: `tokens.py` is byte-identical to owner checkpoint 2e330649.

## The two ids and what they encode (tested facts)

- `tests.job_manager.test_native_stop_restart.NativeStopRestart.test_reopened_store_preserves_deadline_and_generation_without_revival`
  reserves the workspace token for an attempt's start, advances the clock past the native deadline, sweeps
  with the ENGINE UNAVAILABLE (the sweep revokes the generation and holds -- the sibling test
  `test_unavailable_engine_holds_across_restart_then_retries_exact_runtime` passes and pins exactly that),
  reopens the store as a restarted manager, and calls `govern.reserve(store, row, operation=<the same
  start operation>)` again. It expects the SAME reservation back (same `expires_at`, same `generation`,
  "without revival") and asserts no new start follows.
- `tests.job_manager.test_serving_renewal.ServingPermission.test_expiry_is_not_revival_or_reuse_and_unknown_cessation_holds`
  acquires, lets the lane tick past expiry with the engine unavailable (revoked, not returned), then calls
  `self.acquire()` again -- the same `reserve` for the same start operation -- and expects the replayed
  token with the original `expires_at`, then that a competitor's acquire and a renew both refuse.

Both fail today with `ContractRefusal refused/already-terminal`: "resource-token.launch for generation 1
of 'workspace:…' is refused: that generation has been REVOKED, so its entitlement is withdrawn; only a
manager settlement holding positive cessation evidence may act on it now", raised from
`workspaces.reserve -> tokens.journal_launch -> _acting_record -> _owning`. The same symptom is in the
B0 baseline (29 Oct).

## Where the product stands (tested facts)

- `tokens.acquire` REPLAYS the same-operation/same-operands acquisition after revocation (its own replay
  logic runs first; DB-7 "same ID / same operands replays; changed operands refuse"). Inside `reserve`,
  the retry therefore gets past `acquire` and is refused one line later by `journal_launch`.
- `tokens._acting_record` (launch, bind, renewal, activation) re-proves ownership through `_owning`
  BEFORE it consults `control.replay`, and `_owning` refuses a FENCED generation (stopped-execution
  settlement, W375444) and a REVOKED generation (W275774: "a revocation stops acting and does not stop
  settling") alike.
- Measured on 2026-11-18 (then reverted): moving `control.replay` ahead of `_owning` in
  `_acting_record` makes BOTH G3 ids pass (`g3-two-ids-after.log`, 2 OK) and BREAKS three accepted
  stopped-settlement witnesses (`g3-token-modules.log`):
  `test_stopped_settlement.StoppedSettlement.test_fence_wins_over_preflighted_renewal_replay`,
  `…test_post_fence_observation_holds_and_all_acting_paths_refuse`, and
  `test_stopped_settlement_joined.JoinedSettlement.test_joined_fence_rejects_acting_operations`.
  So the accepted W375444 rule is: after a settlement FENCE, even a replay of an acting operation
  refuses. No accepted text says the same for REVOCATION; the two G3 tests say the opposite for it, and
  `acquire` already behaves the opposite way.

## The question

After a generation is REVOKED (overdue, engine unavailable, resource still held), does an exact
same-operation replay of an already-committed acting record (the start's `launch`, a binding, a
renewal) ANSWER the committed record, or REFUSE like a new act?

A replay commits nothing: readers still see `revoked`, `effects_permitted` stays False, no new
generation, deadline or binding comes into existence, and a changed-operand retry still collides. The
difference is only what a restarted manager re-running its own committed start sees.

## Options

1. Revocation replays, fence refuses (recommended if the owner agrees it is DB-7 applied, not a new
   rule). In `_acting_record`: check the settlement fence first (refuse, as W375444 pins), then
   `control.replay` (answer a committed record as it was), then `_owning`'s revocation/owner/returned/
   expiry checks for a NEW act only. Both G3 ids pass; the three fence witnesses keep passing (fence
   checked first); `acquire` and `journal_launch` agree inside `reserve`. Cost: ~10 lines in tokens.py plus
   a witness that a NEW launch/bind/renewal after revocation still refuses and a replayed one answers
   without reviving. Risk: `_owning`'s docstring sentence "a revocation stops acting" would need the
   clarification "a replay is not an act".
2. Keep refusing; align the two G3 tests. A restarted manager must observe the revocation and not
   re-reserve; `reserve` would need to refuse consistently (today `acquire` replays and `journal_launch`
   refuses, two answers for one retry) -- so this option also touches `reserve`/`acquire` to refuse
   first, or accepts the inconsistency. Cost: two test rewrites plus a small `reserve` change. Risk: a
   manager resumed after a deadline sweep cannot re-read the start it already committed through the
   governance path and must learn the revocation some other way (token_of).
3. Localize to `reserve` (workspaces): if the generation is revoked, answer the recorded token without
   calling `journal_launch`. Cost: small. Risk: special-cases one caller; `bind_container`/renewal
   replays after revocation still refuse, so the replay rule stays inconsistent across acts.

The sweep's revoke-on-unavailable itself is NOT in question: the passing sibling test pins it and no G3
id contests it.

## Evidence

`g3-two-ids-after.log` (under the reverted reorder: 2 OK), `g3-token-modules.log` (same reorder: 3
fence witnesses FAIL, everything else OK), `g3-two-ids-after-revert.log` (product restored: the two ids
fail with the original refusal), `source-g3.json`. `tokens.py` hash equals the 2e330649 checkpoint.
