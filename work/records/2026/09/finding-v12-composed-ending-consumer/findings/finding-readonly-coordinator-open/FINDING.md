# Read coordinator evidence without initializing or writing

W126887, parent W122060. Owner M126833 approved the exact two-path coordinator
half of `../../READ-ONLY-OPENING-ALLOCATION-2026-09-09.md`, additive tests only,
baton.impl returning baton.bug. Pinned by reviewer under parent claim126878.

Confirmed baseline: IntegrationStore.open creates an absent store, initializes
an empty schema and requests persistent WAL mode. The existing public entry,
lease and history readers require an already opened store. Its snapshot method
does not supply an opening capability. Source/public evidence and limitations:
`../../review-2026-09-09T09-31-41Z.md` and
`../../evidence/consumer-126729/FINDING.md`; reuse them without a live-store read.

Pinned API: `IntegrationStore.open_readonly(path, *, incarnation, clock)` returns
the existing public coordinator reading/snapshot/close interface backed by a
non-writing connection. Validate the supplied configuration without introducing
a serving act. The coordinator stays target-keyed; no Authority UUID is added.
Any equivalent within-scope API clarification is recorded before implementation,
not silently changed; no further owner approval is needed for that detail.

Revalidate the accepted allocation's full existing-store/owner/schema binding,
no-persistent-change and coherent committed/WAL-read requirements. Reuse the
owner's adoption checks against the actual returned connection. No initializers,
migrations, write locks, persistent journal settings, checkpoints, permission
changes, private consumer constructors, main-file copies or immutable-live-file
assumptions. Refuse unavailable safe reads visibly, preserving files and naming
any sidecar/filesystem limit. Mutation through the resulting public handle must
refuse before writes/external effects; normal serving behavior stays unchanged.

W122060's ordinary serving path already has its coordinator and continues
independently. This provider and sibling W126880 are separately acceptable owner
capabilities for its final read-only join, not terminal handoff implementations.

## 2026-09-09 — independent review127025, changes requested

Confirmed: partial WAL sidecars permit persistent artifact creation, and a
non-database file escapes as raw sqlite3.DatabaseError. Exact diagnosis, scope,
evidence and limits are in `review-2026-09-09T10-10-57Z.md`. This supersedes the
implementation's claim that its opener changes nothing and contains unavailable
reads at the public refusal boundary. The approved API/allocation remains;
W122060's dependency stays open. The local shutdown probe is inconclusive and
is explicitly not represented as an independently reproduced race.

## 2026-09-09 — review127103, corrections verified; shutdown residual confirmed

`review-2026-09-09T10-22-03Z.md` verifies the partial-sidecar and malformed-file
corrections, superseding those two fixed-state findings. Its separate-process
probe now confirms artifact creation during serving shutdown, superseding the
earlier inconclusive race status. Refusal occurs after creation and does not
meet the strict rule. Apply the owner disposition requested at127088 through
the sibling OPENING-BOUNDARY-DECISION-2026-09-09.md; no contract amendment or
independent provider acceptance is implied. W122060 remains gated.

## 2026-09-09 — owner M128249/M128251 explicitly amends sidecar effects

Owner M128251 applies M128249's exception to this independently allocated
provider: permit SQLite-managed WAL/SHM creation and maintenance during mode=ro
opening, including refused opens. This supersedes owner126833's blanket
no-persistent-sidecar rule and the pending-disposition status above. The current
terms are pinned in ../../READ-ONLY-OPENING-ALLOCATION-2026-09-09.md. Preserve
database contents and committed evidence, coherent committed reads, schema
validation, mutation refusal and unchanged serving behavior. No database
creation, schema change, checkpoint, application cleanup, permission change or
write-capable fallback.

Only sidecar-effect expectations may change in tests/integration/test_coordinator.py;
all other assertions remain. PLAN schedules the conversion before edits under
reviewer claim128270. Both existing paths remain reserved to this Work, and
review127103 candidate bytes still matched immediately before this handoff.
Independent review remains required; reconcile and carry all prior verification
usage without resetting the20s budget. No new mechanism or planning Job.

## 2026-09-09 — independently accepted, review128347

`review-2026-09-09T14-06-23Z.md` accepts candidate128308 under the explicit
owner128249/128251 amendment, superseding the pending acceptance status. Full
accepted bytes are in evidence/accepted-128347. Independent19 controls and the
separate-process committed read pass with database preservation. Charged usage
is16.106s/20s with the original carry-in evidence limitation retained. W122060
can now join both independently accepted public openers within its own scope.
