# V12 canonical dossiers are a flat set

## Finding

The repository currently mirrors some Baton Work containment in dossier
directories such as `.../finding-parent/findings/finding-child/`. That makes a
mutable scheduler relationship look like permanent filesystem identity.
Reparenting, promotion, campaign regrouping, or folding a Job then either
leaves the path describing stale structure or demands a move that breaks the
canonical-path guarantee.

## Confirmed direction — 2026-08-29

V12 treats canonical dossier content as a set. Every dossier has one stable,
flat canonical record location independent of its current Work relationships.
Containment, dependency, campaign membership, follow-up, promotion, folding,
routing, and scheduling belong exclusively to the Baton authority and its
projections. No directory segment carries any of those semantics.

This supersedes the v12 direction that treated dossier-path flattening or
promotion as merely an indexing concern while retaining bounded canonical
directory nesting. It does not rewrite or move existing v11-era canonical
records: those paths remain immutable historical locators. The v12
materializer adopts the flat model for records created under the new contract.

Human navigation is recovered through Baton tree/graph/search views and, if
useful, generated disposable indexes. Such views are never authority and never
change a dossier's canonical identity. A dossier may retain internal files and
directories such as `FINDING.md`, `PLAN.md`, `PROGRESS.md`, `evidence/`, and
append-only reviews; "flat" applies to relationships between dossiers, not to
the contents of one dossier.

The exact collision-resistant record-name grammar is an implementation detail
still to be selected. It must be stable and must not encode mutable Work
relations.

## Acceptance boundary

- New v12 dossiers receive stable canonical locations in one record set.
- Reparenting or changing any Baton relationship never changes that location.
- No v12 scheduler or authorization decision is inferred from a path.
- Baton projections can reconstruct all Work relations without filesystem
  ancestry.
- Existing canonical records are not bulk-moved to simulate adoption.
- Generated navigation indexes are replaceable and non-authoritative.


## 2026-10-18 — minimal coordination-pilot provider selected

Owner M321677 on W321608 explicitly reuses W39435 ownership for minimal stable
dossier binding/retention. Reviewer claim321708 read events through321708 and
T39435 through39435. Child W321688 owns this bounded provider at
`baton:work/records/2026/10/finding-v12-pilot-dossier-binding/`. This supersedes
parked scheduling only for the selected child; broader audit/navigation and
relationship coverage are preserved and must be reconciled before parent closure.
No historical locator moves, bulk migration or live deployment is selected.

W321689 consumes the child's binding contract serially for owner disposition;
W321690 consumes both for a deterministic joined packet. Slawomir owns production
backup/restore and Git; implementer prepares disposable rehearsal, reviewer checks
exact recovery identity/evidence. Existing Work remains in v11. Reviewer owns
parent findings/plan; child implementer owns its isolated candidate and PROGRESS.

## 2026-10-18T15:55Z — child acceptance reconciled; broader scope stays parked

Confirmed under baton.rvpc claim323943: W321688 closed satisfying at E323936.
Its exact independent review is
`baton:work/records/2026/10/finding-v12-pilot-dossier-binding/review-2026-10-18T09-42-00Z.md`;
owner closure records integration and human commit
`433b09d6963ca9789700849b640e242e772b9867`, all twelve accepted hashes and 102 focused passes.
The child's integration evidence and current PLAN preserve that provenance.

This supersedes the parent checkpoint saying it awaits child delivery. It does
not supersede the original broader acceptance or the explicit selection of only
the minimal provider. The accepted provider supplies stable one-to-one flat
locator binding, readback, collision/rebinding refusal, evidence resolution and
bounded retained-instance recovery. The grammar is now implemented: at most 96
characters, lowercase letters/digits/single hyphens with an eight-hex suffix.
The earlier statement that grammar remains unselected is superseded for this
provider. Caller-supplied suffix syntax does not itself prove random allocation.

Review reconciliation is in `review-2026-10-18T15-55-24Z.md`. Broader allocation,
relationship mutation/projection coverage and navigation remain unaccepted and
parked, as selected before the pilot. In particular, the test named
`test_ROUTING_changes_do_not_rename_the_record` adds route handlers; it does not
reroute the bound Work. Its name is not proof of reparenting, promotion, folding
or dependency changes. This limits the parent roll-up, not the already accepted
minimal child contract.

Decomposition assessment: the selected provider was already independently
implemented/reviewed as W321688. No second executable slice is selected by this
wake. On resumption, first audit materialization/relationship consumers against
OBS-4, then split concrete independent gaps with actual dependency edges; W39435
retains joined acceptance. Do not enlarge the active W321689 implementation or
duplicate W321690's joined pilot rehearsal. Reviewer owns only this parent
FINDING/PLAN and append-only review; no product or child PROGRESS edits occur.
Future product implementation follows the isolated-v12-Job standing default.


## 2026-10-29 — delivery-plan reconciliation W383239

Broad flat-dossier migration remains deferred beyond v12 under the existing release classification. Minimal native pilot binding was already accepted; it is not an outstanding preparation gate. Preserve permanent dossiers and existing identities. No storage migration or v12-only execution prerequisite is selected.

Current PLAN supersedes prior scheduling; the entire prior PLAN is preserved byte-for-byte in PLAN-HISTORY-W383239.md. No source, tests, specification, acceptance result or claim ownership changed by this record update.
