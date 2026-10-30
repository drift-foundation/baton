# S1 correction — real profile witnesses for the two restoration entries (2026-10-30)

Author: K (interactive copilot `baton.prompt`), owner-held arrangement B; owner
claim E384905 (`baton.slaw`) read back before editing. Answers
`review-2026-10-30T08-20-12Z.md` P2. HEAD `84f66f43`. One file edited:
`v12/python/tests/manager/test_boundary_inventory.py` (digest in
CANDIDATE-SHA256.txt). No product change; no Git mutation, engine, live model,
full-suite run or other agent.

## The defect the review proved

STATED_OWNERS credits `_profile` for the `profile` operand of
`review_cycles.restore_abandoned_correction` and
`review_cycles.settle_restoration_execution`. The blanket WITNESSES mapping sent
both to `StatedRules.test_review_cycle_stated_owners`, which runs the base
`ReviewCycles` class only; the restoration cases live in the subclass
`AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint`, so the witness passed
while calling neither entry (reviewer's spies: zero calls).

## The correction

- `StatedRules._restoration_world`: composes the subclass's own world through
  its accepted operations (`setUp`, `abandoned()`: line, round one, verdict,
  second writer, production start, `abandon_attempt`, gate discharge) and
  registers its cleanups on the witness.
- `StatedRules._spoiled_profiles`: the lifecycle suite's `Profile` double with
  one thing wrong at a time -- `name = None`, then each required capability
  replaced by non-callable text -- and the exact `_profile` label each must
  meet (`a checkpoint profile name`, `a checkpoint profile's <method>
  capability`).
- `StatedRules._profile_owner_witness`: for each spoiled profile, the public
  entry is called with every OTHER operand valid (the fixture's `restore()` /
  `settled()` operands, including the accountable launcher/cessation pair) and
  must refuse with `ContractRefusal` carrying that label. Then, with
  `review_cycles._profile` patched to a pass-through, the SAME call must no
  longer be refused by that label: it goes through or fails later and
  differently. That is the bypass detection the review asked for -- the witness
  distinguishes "the intended check refused" from "something refused".
- `test_restore_abandoned_correction_profile_owner`: first restores the line
  end to end with the sound profile (the world is valid; `_profile` is step
  one, before the replay, so the spoiled calls still meet it), then the three
  spoiled profiles (`name`, `validate`, `restore_checkpoint`).
- `test_settle_restoration_execution_profile_owner`: the sound profile is
  refused, if at all, for something other than the profile (no interrupted
  episode exists to settle), then the two spoiled profiles (`name`,
  `validate`). The check is reached after `_requested_pair` and the
  cessation/launcher capability rule and before any store read, so the world's
  state cannot pre-empt it.
- WITNESSES: the two entries now map to these methods explicitly, after the
  blanket mapping; the STATED_OWNERS comment names them. The key set is
  unchanged (`EveryStatedOwnerHasAWitness` still holds WITNESSES == STATED_OWNERS).

## Verification (measured)

- `just test-one …StatedRules.test_restore_abandoned_correction_profile_owner
  …StatedRules.test_settle_restoration_execution_profile_owner
  …EveryStatedOwnerHasAWitness` → 3 OK, 0.038 s (focused-witnesses.log).
- `just test-one tests.manager.test_boundary_inventory.StatedRules
  tests.manager.test_boundary_inventory.EveryStatedOwnerHasAWitness` → 114 OK,
  3.33 s (stated-rules-class.log): no regression in the stated-owner class.
- The reviewer's spy reproduction, pointed at the new witnesses
  (`reproduce-witness-reaches-entries.py`, log beside it): with both entries
  wrapped under both names and `_profile` wrapped, each witness passes with
  `restore_abandoned_correction` called 7 times (1 sound + 3 refused + 3
  bypassed) and `settle_restoration_execution` 5 times (1 + 2 + 2); the other
  entry 0; `_profile` reached 10 and 9 times (the extra calls are the world's
  own `create_line`/`freeze_checkpoint`). The inverse of the review's finding.
- The scans group was not rerun: the change adds two methods and remaps two
  WITNESSES values; the aggregate inventory tests it could affect are
  `EveryStatedOwnerHasAWitness` (run) and the ownership totals (unchanged keys).

Not changed, still open: the 47 missing probe pairs, the nine pre-existing
unmatched declarations (both lists to be carried forward in S4), other
inventory debt, B3-B5.
