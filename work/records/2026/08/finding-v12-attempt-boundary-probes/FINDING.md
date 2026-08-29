# Derive adopted-attempt probes in the Worker Manager boundary inventory

## Discovery and ownership

Discovered during independent review of W16823. Ledger Work W35557 is bound to
this record. This is an independent, pre-existing test-infrastructure gap
rather than a defect in W16823's principal-context implementation:
`column_probes()` derives corruption probes for `offers` and `operations`, but
not for `attempts`.

## Finding

**Observed:** when the boundary-inventory completeness checks run as isolated
parallel shards, they report adopted attempt columns that are owned by
`attempts.py:_attempts` but have no corruption probe. Before W16823 the family
already contained `attempts.input_digest` and
`attempts.runtime_attempt_id`; W16823 made the same omission visible for
`attempts.assignment_principal` and `attempts.assignment_scope`.

**Confirmed:** production reads all attempt rows through
`boundaries.row(..., schema.ATTEMPT_COLUMNS)`, and W16823's focused tests prove
the new context is copied and used in runtime labels. The missing coverage is
therefore in the inventory's per-column destructive probes, not in the
production row owner.

**Confirmed:** treating only the two W16823 columns as special cases would
leave the same table-family omission in place. The correction should derive
attempt probes from `schema.ATTEMPT_COLUMNS`, with explicit exclusions only
where SQLite's STRICT type or lookup identity makes a meaningful corruption
probe impossible.

## Acceptance

- The boundary inventory derives one non-vacuous corruption probe for every
  probeable adopted attempt column it owns.
- Count/lookup exclusions are explicit, justified, and checked as live owned
  entries.
- The four currently reported attempt-column omissions disappear without
  weakening the completeness or arrival guards.
- The boundary-inventory module and its isolated parallel shards agree.

## 2026-08-29 — implemented and independently reviewed

**Confirmed:** the attempt family contains three adoption sites, and the prior
coverage had drifted in both directions: four live entries were missing from
`attempts.py:_attempts`, while seven declarations for
`output.py:_attempt_of` no longer named entries the inventory attributes to
that site. `attempt_probes()` now derives every live probeable member from
`schema.ATTEMPT_COLUMNS`, intersects it with the independently discovered
receiving-entry universe, and drives each site through its own public module
operation. The old hand-written attempt lists are gone.

**Confirmed exclusions:** the current family owns 17 entries, declares 15
probes, and exempts exactly two live owned entries. SQLite STRICT owns
`assignment_generation`'s count shape before adoption; corrupting
`runtime_attempt_id` makes the row unfindable because every adoption query uses
that identity as its lookup key. Both exemptions remain in `NO_PROBE`, whose
liveness/ownership guard passes.

**Independent verification:** no expected attempt probe is missing and no
attempt probe is stale. All 15 generated probes were rerun individually and
each reached the named `a persisted attempt` integrity boundary. The retained
whole-module and isolated-shard evidence agrees on the same five unrelated
inventory failures and contains no attempt-family failure. W35557 satisfies
its bounded test-infrastructure correction.
