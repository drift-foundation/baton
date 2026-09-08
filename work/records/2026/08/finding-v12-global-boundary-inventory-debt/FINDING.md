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

## 2026-09-08 — W115824 twelve-check disposition

**Observed under W115824 claim115826, not an activation of this Work.** The
fresh focused inventory reports 61 missing probe pairs, 11 orphan probe pairs,
185 unowned entries, 55 unattributed boundary calls and two missing column
names `operation_id`/`settled_at`. Exact lists and source hashes are retained at
`baton:work/records/2026/09/finding-v12-unresolved-suite-checks/evidence/`.
The eight catalog/inventory checks took 3.516s; no whole suite was rerun.

Complete proposed scanner, writer-key fixture, and module-child assignments
are in that record's `review-2026-09-08T03-46-00Z.md`, B1–B3. A 0.606s
diagnostic confirms the writer probe queries an old key after corrupting it;
the real reader correctly rejects a malformed returned identity. Discovery
also drops the existing adopted interrogation origin before `_view` reads
its columns. Preserve completeness and non-vacuity assertions.

**Proposed coverage extension requiring owner disposition:** credentials
(already raised by M54844), exchange, launch, review_cycles, source_boundary,
interrogation, custody and posture_slots join the original census. W39666 is
now closed satisfying; a remaining worker_entry orphan after scanner repair
needs a bounded follow-up in that separate lineage. This diagnosis neither
duplicates W48697 nor silently changes its parked ruling. Module children must
still exist before implementation. Their accepted scopes must enumerate any
existing helper, fixture, stimulus or expected-label changes.

## 2026-09-08 — owner assigns the current repair program to tuner

Slawomir explicitly requested that tuner address the twelve unresolved suite
checks, allowing decomposition. The old parked deferral and the pending-owner
posture above are superseded for this repair program. W48697 remains the sole
inventory owner and is assigned to baton.tune; W115981 tracks the whole-suite
remediation as a follow-up of completed diagnosis W115824.

Schedule B1 scanner helpers and independent fragment witnesses, B2's exact
writer-key returned-row corruption fixture, then B3 module-local coverage as
enumerated in work/records/2026/09/finding-v12-unresolved-suite-checks/
review-2026-09-08T03-46-00Z.md. The exact B1/B2 existing helper and fixture
changes are authorized by this bounded repair assignment. Recompute the census
after scanner corrections; preserve all completeness and refusal assertions.
Coverage includes the original module list plus the review's credentials,
exchange, launch, review_cycles, source_boundary, interrogation, custody and
posture_slots inputs. Create bounded children before implementation, with
serial ownership of test_boundary_inventory.py. Enumerate and justify any
surviving orphan-probe stimulus/label changes in its child plan before editing.
The separate worker_entry lineage remains separate if a genuine delta survives.
Runtime source is read-only unless a demonstrated defect obtains its own scope.

## 2026-09-08 B3 planning decision — claim116930

Both B1 and B2 are independently accepted; read their final dispositions.
Use the retained1365entry/183unowned/72orphan B1 census and the4 remaining
probe-reachability failures from B2. Before module implementation, create
bounded records for all17 approved modules, preserving serial ownership and
independent assessment. The separate worker-entry follow-up retains its own
lineage. The newly exposed output-fixture failure gets a proposal-only scope
until an explicit bounded disposition authorizes its existing-test mutation.

The retained B1 census did not enumerate the post-scanner expected/declared
probe-pair difference. New planning question: what exact missing/orphan probe
pairs now accompany each module census? Budget10s for one catalog-only
projection, calling existing expected/all_probes without executing probes,
plus source hashes and retained evidence audit. Do not repeat original3,
original6/7, scanner controls or the ordinary suite. Pin exact rows as planning
inputs, never as guessed owners or mandatory probe registrations.

A dedicated plan-review Work will gate the serial module sequence before
implementation. Its review evaluates bounded scopes, existing stimulus/label
changes, special lineage and scope gaps; the inventory umbrella retains all
aggregate/final gates. No implementation is performed under this planning claim.

## 2026-09-08 concrete module decomposition — claim116930

Created21 bound Work records: plan-review W116952; declaration-accounting
proposal W116962;17 approved module scopes; output proposal W117024; and
worker-entry follow-up W117026 of W39666 with its own top-level dossier.
MODULE-SCOPES.md and evidence/planning-116930/work-index.json retain every
exact Work/dossier mapping. Serial dependencies preserve one shared-file
writer through independent acceptance. Planning/authority prerequisites are
explicit, not inferred from a census count.

Catalog-only projection1.931s within10s found817expected and715declared pairs,
153missing and51orphan. No probe or test suite ran. scope-audit.json proves
exact assignment of all retained183unowned,72orphan calls,153missing pairs,
51orphan pairs and4failed stimuli to module inputs. No row was silently
subtracted, treated as accepted ownership or assigned a fabricated witness.

The declaration-accounting and output records are proposal-only pending
concrete bounded dispositions. The worker-entry result keeps separate lineage.
Accepted proposal completion alone cannot satisfy its underlying correction:
retain or create implementation Work before considering inventory complete.
This planning result is ready for independent assessment; source remains
unchanged on accepted B2 candidate3973301e... .

## 2026-09-08 — exact declaration proposal, baton.tuner W116962 claim117120

W116952 independently accepted the planning partition and required a separate actual implementation gate for proposal results. W116962 prepared an unapplied candidate830496b44569e7a88c29771577d616f94b52bcd3066c48f6fa338aab24a30d04 with source-call identities and actual entry claims, preserving the live3973301e... baseline. See findings/finding-declaration-accounting-proposal/PROPOSAL.md and evidence/research.json there. Eleven controls pass in both the standalone model and candidate; the candidate aggregate still fails on77 residual rows. It resolves13 symbolic rows, exposes18 previously hidden rows, retains4 symbolic rows, and preserves1365 entries and existing owner triples.

Created W117174, bound to findings/finding-declaration-accounting-implementation/, as the actual implementation result after independent review and explicit bounded existing-test disposition. Lanes/module execution now also waits for that result. The new Work is conditional and grants no current assertion-edit authority. Its accepted implementation must revalidate exact module input deltas; the earlier planning packet remains historical evidence. This research does not complete B3 or W48697 and does not silently waive any original check.
