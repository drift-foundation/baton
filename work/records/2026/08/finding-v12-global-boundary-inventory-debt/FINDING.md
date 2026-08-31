# Complete the global v12 receiving-boundary inventory

Work: W48697
Origin: W43977 independent review, message M48312

## Finding

W43977's custody-specific inventory work exposed a wider existing baseline:
131 unowned receiving entries and 57 missing probes across ten modules. Making
W43977 repair all of them would turn one bounded custody child into an
unresearched global program and delay the current vertical slice.

The debt is nevertheless real and must not disappear when W43977's acceptance
is narrowed. `worker_entry` is already owned by W39666. This record owns the
remaining modules:

- `workspaces`
- `documents`
- `oci`
- `handshake`
- `lanes`
- `attempts`
- `authority_port`
- `intake`
- `sessions`

## 2026-08-30 — approver ruling

W43977 may close on a complete custody/declaration slice rather than waiting
for the entire shared inventory module to become green. The global debt is
preserved here as deferred v12 hardening. Before implementation, this umbrella
must be decomposed by module so each owner reads and proves its own crossings;
no participant registers guessed ownership merely to make an aggregate count
green.

The baseline counts are discovery evidence, not frozen acceptance totals. A
fresh rescan at implementation start establishes the then-current module-local
entries and probes, while this record preserves why that rescan is required.

## Acceptance boundary

- Every listed module is represented by a separately claimable child before
  implementation begins.
- Each child inventories its current caller-controlled crossings, establishes
  one real owner per entry and provides one independently driven refusal or
  corruption witness per `(entry,label)` pair.
- W39666 remains the owner of `worker_entry`; this umbrella neither duplicates
  nor silently absorbs it.
- Aggregate verification becomes green without weakening existing assertions
  or inventing ownership for unread code.

## Fresh bounded rescan — 2026-08-31 (W54802)

**Observed.** W54182 made the probe driver bounded without changing its
semantics. On that corrected driver, the focused command
`PYTHONPATH=src python3 -m unittest
tests.manager.test_boundary_inventory.EveryProbeProvesItArrived` completes in
about 2.1 seconds. All 549 declared probes reach their named boundary. Catalog
completeness still reports 46 owned `(entry, label)` pairs with no probe and 3
probes with no attributed owner. Exact grouped output is preserved in
`evidence/w54802-probe-rescan-2026-08-31.txt`.

**Confirmed ownership.** W54802 is not a second implementation owner. Its
module set is the one this record already owns: `workspaces`, `oci`,
`handshake`, `lanes`, `attempts`, `intake`, and `sessions` are present in the
fresh mismatch; `worker_entry` remains W39666's separately scheduled scope.
W54802 was therefore closed as a duplicate of W48697 after contributing this
rescan. This record stays parked under the 2026-08-30 ruling; new counts do not
silently start the hardening campaign.

**Confirmed diagnosis boundary.** The 46/3 display is not one homogeneous
probe-table omission, and implementation must not add all displayed keys
literally:

- Thirty-seven displayed missing pairs are direct live gaps in the current
  catalog: 14 adopted profile/retention/session/workspace-record pairs, 19
  caller operands across abandonment, OCI, worker entry and workspaces, and 4
  members of the new abandoned-runtime destroy observation.
- Eight displayed `intake.py:_destroyed*` pairs are malformed projections of
  `_provider_ending`. The source iterates `credentials`/`launch` and builds the
  boundary label with an f-string; the scanner drops the loop variable,
  reports `a  teardown ending`, and collapses the provider subdocument onto
  the whole `adapter.destroy*` answer. The real two provider subdocuments and
  their lifecycle members must be spelled and inventoried explicitly; adding
  probes for the collapsed empty-label keys would certify an entry that does
  not exist at runtime.
- The displayed `attempts.py:request_runtime_start adapter.target` pair is
  likewise a lossy projection through `_plan_agrees`: `getattr(adapter,
  "mounts")`, the per-mount document, and the later source/target/writable
  reads collapse onto the adapter root while the real `a declared runtime
  mount` owner becomes an orphan. Correct the attribution first; then probe
  the final mount entries rather than the current synthetic key.
- Two retained-profile probes (`wire_protocol`, `client_capabilities`) are
  valid but appear ownerless because `_through_helpers` propagates injected
  and caller origins but omits its existing adopted `read:` origin. The
  certified row already returns the `profiles.body` origin; member reads in
  `_negotiated_against` need to preserve that original adoption site.
- The persisted-lane probe is valid but appears ownerless because
  `_returned_origins` records `_adopted(row)` as generic `caller:row`; the
  later `held = _adopted(held)` overwrites the contextual
  `read:lanes.py:_occupy_lane|runtime_lanes` origin. An identity-style helper
  return must substitute the call argument's live origin rather than its own
  parameter placeholder.

**Observed interaction.** The adjacent bounded
`EveryReceivingEntryHasOneOwner` class currently reports 133 unowned entries,
34 orphan boundary calls and two untracked persisted column names. Those are
the broader W48697 baseline, not additional W54802 scope. The four attribution
faults above explain several rows in both views, so the module-local children
must fix discovery first, take a fresh module-local inventory, and only then
freeze their probe lists. The historical 46/3 counts remain discovery evidence,
not acceptance totals.
