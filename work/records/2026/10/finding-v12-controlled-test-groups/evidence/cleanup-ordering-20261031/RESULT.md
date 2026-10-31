# Frozen-home removal ordering (M384981) -- K, copilot under owner claim E384905

Assignment: T384870 seq 384981 (coordinator), from W384944 review
2026-10-31T02:51:05Z and its independent reproduction
(`findings/finding-b4-docker-readiness/evidence/input-delivery-20261031/independent.log`:
three `test_input_delivery` cleanup cases error with
`PermissionError: [Errno 13] Permission denied: 'inputs'` at
`workspaces._removed_through_handles`).

## Defect (confirmed in source)

`_removed_through_handles` admits every directory first, then walks the admitted
handles deepest-first: thaw the handle, remove its members, then
`os.rmdir(name, dir_fd=parent)`. A child's entry is removed FROM THE PARENT, and a
delivery freezes every directory of the home (0o555), so at that point the parent
is still frozen -- its own thaw comes on its own, later turn. The first nested
`rmdir` fails with EACCES and the home is left half-emptied and still frozen.

## Correction (workspaces.diff; product only, one call added)

Before the child's `rmdir`, thaw the parent handle (`_thaw_handle(parent, what)`).
The parent is an admitted handle of the same tree, so nothing outside the tree
being removed changes mode; the parent's own pass repeats the same `fchmod`,
which is idempotent. Preserved: full admission (device + mount-table checks over
every directory) before any destructive effect; retained-handle, `O_NOFOLLOW`
relative operations only (no name resolved from the root twice); the
worker-owned refusal; identity re-proof of the home against the pinned ownership
record and the parent's entry before and after; every handle closed.

## Verification

- `regression-before-4989ce76.log`: the new regression
  (`test_workspaces.CleanupTouchesOnlyWhatWasCreated.test_a_home_whose_every_directory_is_frozen_is_removed_deepest_first`:
  home, inputs, workspace and two nested directories all 0o555, a frozen sibling
  beside it) run in a scratch snapshot whose `workspaces.py` is the committed
  4989ce76 bytes: `PermissionError: Permission denied: 'deeper'`, errors=1.
- `regression-after.log`: the same regression plus the three input-delivery
  cleanup cases on the corrected tree: 13 run, OK.
- `focused-1.log`: `test_input_delivery` non-engine classes (TheInputRootIsFrozenAndNotOnlyItsFiles,
  TheRootsOwnENTRYIsFrozenToo, TheRuledTrustModel -- the three cleanup cases, the
  refusal/retry/outside-storage/stale-entry cases -- TheWholeDeliveryIsFrozenAndNotOnlyTheRoot,
  TheModeIsEstablishedRatherThanRequested), the whole `test_workspaces` and
  `test_custody` modules, `test_dependencies`, and the inventory's StatedRules and
  refusal-table witness: 424 run, OK (this run also covers the custody `math`
  import removal below).
- Scans group after both fixes: parent `evidence/stage-c-2026-10-30/scans-group-run-4.log`.

Also in this candidate (same digests, `CANDIDATE-SHA256.txt`): `custody._finite_seconds`
decides finiteness without importing `math` -- scans run 3 (`scans-group-run-3.log`)
failed `test_dependencies...test_the_manager_imports_only_the_ruled_validator`
(`'math' not found in {...}`) on the M384941 allowance correction; the rule was kept
and the import removed (`value != value` is the NaN test, equality with the two
infinities the rest).

Paths touched for this assignment: `workspaces.py` (K's exclusive path) and
`tests/manager/test_workspaces.py` (one added test; reported here as an additional
edit path -- not allocated to codexpc). No Docker, no engine, no build, no shared
fixture edit, no assertion weakened; codexpc's isolated snapshot was not touched.
